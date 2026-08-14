#!/usr/bin/env python3
"""build-skill-search — BM25 lexical search index + CLI for the Orca skills.

Pure-stdlib, offline, no-LLM. Reads every ``skills/<name>/SKILL.md``, tokenizes
the frontmatter ``name`` + ``description`` (plus any ``## Trigger phrases`` body
section), builds an inverted index with per-doc lengths, and emits
``fdk/skills.search.json``. Name tokens are boosted x3 and trigger tokens x2 so
that "find by roughly-the-name" queries rank the right skill first.

The same index powers three consumers with identical BM25 math:
  - this script's ``find-skill`` verb (terminal / agent use),
  - the emitted ``fdk/skills.search.json`` (external consumers),
  - an optional ``<script id="skillsearch">`` injected into the cheatsheet so its
    search box returns *ranked* results instead of a substring filter.

Usage:
    python3 fdk/tools/build-skill-search.py                        # build → fdk/skills.search.json
    python3 fdk/tools/build-skill-search.py --inject [HTML]        # build, then embed search into the cheatsheet
    python3 fdk/tools/build-skill-search.py find-skill "<query>"   # print top-k ranked skills (default k=5)
    python3 fdk/tools/build-skill-search.py find-skill "<query>" -k 10

Injection mirrors build-cheatsheet.py exactly: escape ``</`` → ``<\\/`` so skill
text can't break the <script> tag, regex-remove any prior block (idempotent),
and insert before the page's first plain ``<script>``. Default = JSON only.
"""
import argparse
import glob
import json
import math
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve_skills_dir(root):
    """Repo gốc: skills/ nằm cạnh fdk/. Global harness home (~/.claude/harness/,
    cài bởi install-harness.sh --global) mirror fdk/tools nhưng KHÔNG có skills/
    riêng — skill thật nằm ở ~/.claude/skills/ (cài qua `npx skills add --global`),
    tức dirname(root)/skills. Fallback chỉ kích khi candidate trong-repo rỗng, nên
    không đổi hành vi khi chạy trong repo gốc (GH#87)."""
    candidate = os.path.join(root, "skills")
    if glob.glob(os.path.join(candidate, "*", "SKILL.md")):
        return candidate
    if os.path.basename(root) == "harness":
        alt = os.path.join(os.path.dirname(root), "skills")
        if os.path.isdir(alt):
            return alt
    return candidate


SKILLS_DIR = _resolve_skills_dir(ROOT)
OUT_JSON = os.path.join(ROOT, "fdk", "skills.search.json")

K1, B = 1.5, 0.3  # BM25 knobs. b is below the 0.75 default on purpose: skill
# "documents" are metadata blurbs whose length varies wildly (one line vs a huge
# folded description), so strong length-normalization wrongly rewards the shortest
# blurbs. b=0.3 keeps some normalization without that short-doc bias.
NAME_BOOST, TRIG_BOOST = 3, 2  # field weighting via term-frequency inflation

# Stopword set (EN + a few VI) — keeps low-signal glue words out of both the index
# and the query. Includes generic action verbs/pronouns (make/create/want/need/...)
# that phrase a request ("make a docs website") but carry no skill-topic signal and,
# being rare in skill text, otherwise get a misleadingly high IDF.
STOP = set((
    "a an and or of to in on for with is are be as by at from this that it its the "
    "your you our we i not no so if then than via use used using when where what how "
    "make makes making create creates creating want wants need needs get got do does "
    "please can could would should my me let "
    "và là các cho của một với khi nếu thì để được không có ở"
).split())

TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)  # letters/digits (Unicode), splits on - _ etc.


def tokenize(text):
    """Lowercase, Unicode-aware tokenizer; drops stopwords and 1-char tokens."""
    return [t for t in TOKEN_RE.findall(text.lower()) if len(t) > 1 and t not in STOP]


def parse_frontmatter(text):
    """Minimal YAML-frontmatter reader (name/description only need apply).

    Handles single-line values, quoted values, and ``>``/``|`` block scalars.
    Top-level keys start at column 0; indented lines continue the previous value.
    """
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}
    data, key, buf = {}, None, []
    keyre = re.compile(r"^([A-Za-z0-9_-]+):\s?(.*)$")

    def flush():
        if key is not None:
            data[key] = "\n".join(buf).strip()

    for ln in lines[1:end]:
        m = keyre.match(ln)
        if m and not ln.startswith((" ", "\t")):
            flush()
            key, rest = m.group(1), m.group(2).strip()
            buf = [] if rest in (">", "|", ">-", "|-", ">+", "|+", "") else [rest.strip("\"'")]
        elif key is not None:
            buf.append(ln.strip())
    flush()
    return data


def trigger_section(text):
    """Return the text under a ``## Trigger phrases`` heading, if present."""
    out, grab = [], False
    for ln in text.splitlines():
        if re.match(r"^#{2,}\s", ln):
            grab = bool(re.match(r"^#{2,}\s*trigger phrases\s*$", ln, re.I))
            continue
        if grab:
            if not ln.strip():
                break
            out.append(ln)
    return " ".join(out)


def load_skills(skills_dir):
    """Read all SKILL.md, deduped by frontmatter name; returns ordered docs.

    Each doc = {'n': name, 'd': short-desc, 'tokens': boosted token bag}.
    A name seen twice (e.g. docs-site-macos + docs-site-macos-skill) is merged
    so the index has exactly one entry per skill — matching the cheatsheet's
    clickable `KNOWN` set, which is keyed by skill name.
    """
    merged = {}
    for path in sorted(glob.glob(os.path.join(skills_dir, "*", "SKILL.md"))):
        text = open(path, encoding="utf-8").read()
        fm = parse_frontmatter(text)
        name = fm.get("name") or os.path.basename(os.path.dirname(path))
        desc = re.sub(r"\s+", " ", fm.get("description", "")).strip()
        trig = trigger_section(text)
        tokens = tokenize(name) * NAME_BOOST + tokenize(trig) * TRIG_BOOST + tokenize(desc)
        if name in merged:
            merged[name]["tokens"].extend(tokens)
            if len(desc) > len(merged[name]["d"]):
                merged[name]["d"] = desc
        else:
            merged[name] = {"n": name, "d": desc, "tokens": tokens}
    if not merged:
        sys.exit(f"No SKILL.md found under {skills_dir}")
    docs = [merged[n] for n in sorted(merged)]
    for d in docs:  # truncate display description; matching already used full text
        d["d"] = (d["d"][:157] + "…") if len(d["d"]) > 158 else d["d"]
    return docs


def build_index(skills_dir=SKILLS_DIR):
    """Build the BM25 inverted index (deterministic, sorted)."""
    docs = load_skills(skills_dir)
    lengths, post = [], {}
    for i, d in enumerate(docs):
        tf = {}
        for t in d["tokens"]:
            tf[t] = tf.get(t, 0) + 1
        lengths.append(len(d["tokens"]))
        for t, c in tf.items():
            post.setdefault(t, []).append([i, c])
    post = {t: sorted(post[t]) for t in sorted(post)}
    avgdl = (sum(lengths) / len(lengths)) if lengths else 0.0
    return {
        "v": 1, "k1": K1, "b": B, "N": len(docs), "avgdl": round(avgdl, 4),
        "docs": [{"n": d["n"], "d": d["d"]} for d in docs],
        "len": lengths, "post": post, "stop": sorted(STOP),
    }


def score_query(index, query, k=5):
    """Rank docs for a query using the same BM25 the JS uses."""
    k1, b, N, avg = index["k1"], index["b"], index["N"], index["avgdl"] or 1.0
    post, length, docs = index["post"], index["len"], index["docs"]
    scores = {}
    for t in tokenize(query):
        pl = post.get(t)
        if not pl:
            continue
        df = len(pl)
        idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
        for docid, tf in pl:
            den = tf + k1 * (1 - b + b * length[docid] / avg)
            scores[docid] = scores.get(docid, 0.0) + idf * tf * (k1 + 1) / den
    ranked = sorted(scores.items(), key=lambda x: -x[1])[:k]
    return [(docs[i]["n"], s, docs[i]["d"]) for i, s in ranked]


# ── JS embedded into the cheatsheet by --inject. ~30-line BM25 + a results panel.
# `__INDEX__` is replaced with the index JSON; the whole inner string then gets the
# same `</` → `<\/` escape build-cheatsheet uses, so no skill text can close the tag.
SKILLSEARCH_JS = r"""
(function(){
  var IDX=__INDEX__;
  var k1=IDX.k1,b=IDX.b,N=IDX.N,avg=IDX.avgdl||1,post=IDX.post,len=IDX.len,docs=IDX.docs;
  var STOP={};(IDX.stop||[]).forEach(function(w){STOP[w]=1;});  // same stopwords as the CLI
  function tok(s){var m=(s||"").toLowerCase().match(/[^\W_]+/g)||[],o=[],i;for(i=0;i<m.length;i++)if(m[i].length>1&&!STOP[m[i]])o.push(m[i]);return o;}
  function rank(q){
    var qs=tok(q),sc={},i,j,t,pl,df,idf,d,tf,den;
    for(i=0;i<qs.length;i++){t=qs[i];pl=post[t];if(!pl)continue;df=pl.length;idf=Math.log(1+(N-df+0.5)/(df+0.5));
      for(j=0;j<pl.length;j++){d=pl[j][0];tf=pl[j][1];den=tf+k1*(1-b+b*len[d]/avg);sc[d]=(sc[d]||0)+idf*tf*(k1+1)/den;}}
    var out=[];for(d in sc)out.push([+d,sc[d]]);out.sort(function(a,b){return b[1]-a[1];});return out;
  }
  var q=document.getElementById("q");if(!q)return;
  var panel=document.createElement("div");panel.id="ssresults";
  panel.style.cssText="position:fixed;z-index:50;max-width:480px;background:rgba(255,255,255,.96);backdrop-filter:blur(12px);border:1px solid rgba(0,0,0,.12);border-radius:12px;box-shadow:0 12px 40px rgba(0,0,0,.18);overflow:hidden;display:none;font:13px system-ui,-apple-system,sans-serif";
  document.body.appendChild(panel);
  function place(){var r=q.getBoundingClientRect();panel.style.top=(r.bottom+6)+"px";panel.style.left=Math.max(8,r.right-480)+"px";panel.style.width=Math.min(480,window.innerWidth-16)+"px";}
  function show(){
    var v=q.value.trim();if(!v){panel.style.display="none";return;}
    var r=rank(v).slice(0,8);if(!r.length){panel.style.display="none";return;}
    panel.innerHTML=r.map(function(x){var dc=docs[x[0]];
      return '<div class="ssrow" data-n="'+dc.n+'" style="padding:8px 12px;cursor:pointer;border-bottom:1px solid rgba(0,0,0,.06)"><b style="color:#0a84ff">'+dc.n+'</b> <span style="color:#667">'+(dc.d||"")+'</span></div>';
    }).join("");place();panel.style.display="block";
  }
  q.addEventListener("input",show);q.addEventListener("focus",show);
  panel.addEventListener("mouseover",function(e){var r=e.target.closest(".ssrow");if(r)r.style.background="rgba(10,132,255,.08)";});
  panel.addEventListener("mouseout",function(e){var r=e.target.closest(".ssrow");if(r)r.style.background="";});
  panel.addEventListener("click",function(e){var r=e.target.closest(".ssrow");if(r&&typeof openSkill==="function"){openSkill(r.dataset.n,true);panel.style.display="none";}});
  document.addEventListener("click",function(e){if(e.target!==q&&!panel.contains(e.target))panel.style.display="none";});
})();
"""


def write_json(index, out=OUT_JSON):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    return out


def find_html():
    cands = sorted(glob.glob(os.path.join(ROOT, "llmwiki", "html", "*skills-cheatsheet.html")))
    if not cands:
        sys.exit("No *skills-cheatsheet.html in llmwiki/html/ — pass the path with --html.")
    return cands[-1]


def inject(index, html_path):
    """Embed/replace the <script id="skillsearch"> block (idempotent)."""
    payload = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    inner = SKILLSEARCH_JS.replace("__INDEX__", payload).replace("</", "<\\/")
    block = '<script id="skillsearch">' + inner + "</script>"

    html = open(html_path, encoding="utf-8").read()
    html = re.sub(r'<script id="skillsearch"[^>]*>.*?</script>\n?', "", html, flags=re.S)
    idx = html.find("<script>")
    if idx == -1:
        sys.exit("Target HTML has no main <script> to insert before.")
    html = html[:idx] + block + "\n" + html[idx:]
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path


def cmd_build(a):
    index = build_index(a.skills)
    out = write_json(index, a.out)
    print(f"✓ indexed {index['N']} skills · {len(index['post'])} terms · "
          f"avgdl {index['avgdl']:.1f} → {os.path.relpath(out, ROOT)} "
          f"({os.path.getsize(out)//1024} KB)")
    if a.inject:
        html = a.html or find_html()
        inject(index, html)
        print(f"✓ injected <script id=\"skillsearch\"> → {os.path.relpath(html, ROOT)}")


def cmd_find(a):
    if not a.query:
        sys.exit('find-skill needs a query, e.g.  find-skill "render markdown to html"')
    index = build_index(a.skills)
    hits = score_query(index, a.query, a.topk)
    print(f'\n  query: "{a.query}"   (top {a.topk} of {index["N"]} skills)\n')
    if not hits:
        print("  no lexical matches.\n")
        return
    width = max(len(n) for n, _, _ in hits)
    for rank, (name, score, desc) in enumerate(hits, 1):
        snippet = (desc[:64] + "…") if len(desc) > 65 else desc
        print(f"  {rank}. {score:6.2f}  {name.ljust(width)}  {snippet}")
    print()


def self_test():
    # GH#87: fallback global-harness-home phải trúng khi repo-candidate rỗng, và
    # KHÔNG kích khi repo-candidate đã có skill (tránh phá hành vi trong repo gốc).
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        claude_home = os.path.join(td, ".claude")
        harness = os.path.join(claude_home, "harness")
        os.makedirs(os.path.join(harness, "skills"))  # rỗng — mô phỏng global home
        real_skill = os.path.join(claude_home, "skills", "demo-skill")
        os.makedirs(real_skill)
        with open(os.path.join(real_skill, "SKILL.md"), "w") as f:
            f.write("---\nname: demo-skill\n---\n")
        assert _resolve_skills_dir(harness) == os.path.join(claude_home, "skills")
        repo = os.path.join(td, "some-repo")
        assert _resolve_skills_dir(repo) == os.path.join(repo, "skills")
    print("✓ self-test passed")


def main():
    p = argparse.ArgumentParser(description="BM25 skill search: build index + find-skill CLI.")
    p.add_argument("cmd", nargs="?", default="build", choices=["build", "find-skill"],
                   help="build (default) or find-skill")
    p.add_argument("query", nargs="?", help="query string (find-skill)")
    p.add_argument("-k", "--topk", type=int, default=5, help="number of results (find-skill)")
    p.add_argument("--inject", action="store_true", help="also embed search into the cheatsheet")
    p.add_argument("--html", help="cheatsheet path (default: auto-detect)")
    p.add_argument("--skills", default=SKILLS_DIR, help="skills dir")
    p.add_argument("--out", default=OUT_JSON, help="output JSON path")
    p.add_argument("--self-test", action="store_true", help="kiểm bất biến nội bộ")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    (cmd_find if a.cmd == "find-skill" else cmd_build)(a)


if __name__ == "__main__":
    main()
