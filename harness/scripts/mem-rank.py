#!/usr/bin/env python3
"""mem-rank — a small agent-memory layer: ADD/UPDATE/DELETE/NOOP ops + RANKED retrieval that

See llmwiki/wiki/concepts/log-model.md for how this differs from events.jsonl/scratch-log/
touches/provenance-log — each answers ONE narrow question, none coordinate with the others.
returns the few relevant memories instead of dumping full context (2026 agent-memory trend).

The harness already has the wiki (curated knowledge) + .claude/memory (flat facts). This adds
the missing piece: a queryable store you write to by code and retrieve top-k from by relevance.

  add "<text>" [--kind k] [--id ID]   append/replace a memory (ADD/UPDATE).
  episode "<did>" [--files a,b] [--outcome o] [--session s] [--supersedes ID] [--id ID]
                                      record a structured SESSION EPISODE (kind=episode) — the
                                      EPISODIC memory layer (what a past session did), retrievable.
  delete ID                           remove a memory (DELETE).
  export                              dump store as JSONL to stdout (memory portability).
  export-okf [--out DIR] [--kind K]   write each memory as an OKF v0.1 .md (type + ## Origin).
  import <file.jsonl>                 load JSONL, dedupe by id (local store wins).
  retrieve "<query>" [--k N]          top-N memories by relevance (NOOP if nothing relevant).
  --kind-filter K                     with retrieve: only rank memories of kind K (e.g. episode).
  --report                            list stored memories + count.
  --self-test                         deterministic add->retrieve ranking in a temp store.

TEMPORAL: every record carries `ts` (ISO time). UPDATE (same id) or `episode --supersedes ID`
records a `supersedes` link so you can answer "which fact was true when" — the store keeps the
newer record and points back at what it replaced.

The ONE adapter = harness/mem-rank.config.yaml (relevance.scorer, embedding_model, eviction;
flagged verified=false). The token-overlap ranker + store + ops are deterministic, built now.
The embedding scorer is the quarantined unknown; absent => token-overlap.
"""
import json
import os
import math
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import bnal_config

_FALLBACK = {"verified": False, "relevance": {"scorer": "token-overlap", "embedding_model": None},
             "eviction": {"policy": "score", "max_entries": 500}}


def _store_file(root: Path) -> Path:
    return root / "harness" / "metrics" / "memory.jsonl"


def _config_file(root: Path) -> Path:
    return root / "harness" / "mem-rank.config.yaml"


def _ensure_gitignored(root: Path) -> None:
    try:
        (root / "harness" / "metrics").mkdir(parents=True, exist_ok=True)
        gi = root / ".gitignore"
        cur = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
        if "harness/metrics/memory.jsonl" not in cur:
            with open(gi, "a", encoding="utf-8") as f:
                f.write("\n# mem-rank local memory store\nharness/metrics/memory.jsonl\n")
    except Exception:
        pass


def load_config(root: Path) -> dict:
    cfg = bnal_config.load(root, "mem-rank", _FALLBACK)
    return cfg


def _read(root: Path):
    try:
        lines = _store_file(root).read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out = []
    for ln in lines:
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def _write_all(root: Path, mems) -> None:
    try:
        _ensure_gitignored(root)
        with open(_store_file(root), "w", encoding="utf-8") as f:
            for m in mems:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _next_id(mems):
    n = 0
    for m in mems:
        try:
            n = max(n, int(str(m.get("id", "0")).lstrip("m") or 0))
        except Exception:
            pass
    return f"m{n + 1}"


def _now_iso(ts=None):
    if ts:
        return ts
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def add(root, text, kind=None, mid=None, meta=None, ts=None, supersedes=None):
    """ADD (new id) or UPDATE (existing id). Evicts per policy if over cap.

    TEMPORAL: stamps `ts`. If `mid` names an existing record (UPDATE) or `supersedes` is given,
    the new record links `supersedes` to the id it replaced — the append-only history signal."""
    root = Path(root)
    cfg = load_config(root)
    mems = _read(root)
    rid = mid or _next_id(mems)
    replaced = next((m for m in mems if m.get("id") == rid), None)
    # OKF v0.1 dùng từ khoá `type`; store này vốn dùng `kind`. Ghi CẢ HAI: `type` để mọi thứ
    # đọc wiki (validator R9, okf-check, bên thứ ba) hiểu được record memory mà không cần
    # bộ chuyển; `kind` giữ nguyên cho code cũ. OKF cho phép khoá lạ nên thêm là hợp lệ.
    rec = {"id": rid, "text": (text or "").strip(), "kind": kind or "note",
           "type": kind or "note", "ts": _now_iso(ts)}
    sup = supersedes or (replaced.get("id") if replaced else None)
    if sup:
        rec["supersedes"] = sup
    if meta:
        for key, val in meta.items():
            if val not in (None, "", [], {}):
                rec[key] = val
    mems = [m for m in mems if m.get("id") != rec["id"]]   # UPDATE = replace same id
    mems.append(rec)
    mems = _evict(mems, cfg)
    _write_all(root, mems)
    return rec


def episode(root, did, files=None, outcome=None, session=None, ts=None, supersedes=None, mid=None, parent=None):
    """Record a SESSION EPISODE — the episodic memory layer. Composes a retrievable `text` from
    the structured fields (so token-overlap retrieval works) and keeps the fields as metadata."""
    files = files or []
    if isinstance(files, str):
        files = [f.strip() for f in files.split(",") if f.strip()]
    parts = [(did or "").strip()]
    if files:
        parts.append("files: " + ", ".join(files))
    if outcome:
        parts.append("outcome: " + outcome.strip())
    text = ". ".join(p for p in parts if p)
    # parent = phiên NGAY TRƯỚC trong cùng repo (episode gần nhất khác session). Đây là thứ
    # biến một đống episode rời thành một CHUỖI đọc được: bàn giao (session-continue) hay chỉ
    # là mở phiên mới thì cha vẫn đúng, không cần state riêng. "auto" → tự suy lúc ghi.
    if parent == "auto":
        parent = last_session(root, exclude=session)
    meta = {"did": (did or "").strip(), "files": files, "outcome": outcome,
            "session": session, "parent": parent}
    return add(root, text, kind="episode", mid=mid, meta=meta, ts=ts, supersedes=supersedes)


def last_session(root, exclude=None):
    """Session của episode gần nhất (bỏ qua chính phiên đang ghi). None nếu chưa có."""
    for m in reversed(_read(Path(root))):
        if m.get("kind") != "episode":
            continue
        sid = m.get("session")            # add() phẳng hoá meta lên top-level, không lồng "meta"
        if sid and sid != exclude:
            return sid
    return None


def chain(root, session=None, limit=20):
    """Chuỗi phiên nối tiếp: đi ngược parent từ `session` (mặc định: phiên mới nhất).

    Đây là cái MAP mà từng episode rời rạc không cho được — "phiên này tiếp phiên nào, đã làm
    gì, chạm file nào" đọc một mạch, không phải ghép tay từ nhiều sổ.
    """
    eps = [m for m in _read(Path(root)) if m.get("kind") == "episode"]
    by_sess = {}
    for m in eps:                                   # episode mới nhất của mỗi phiên thắng
        sid = m.get("session")
        if sid:
            by_sess[sid] = m
    cur = session or last_session(root)
    out, seen = [], set()
    while cur and cur not in seen and len(out) < limit:
        seen.add(cur)
        m = by_sess.get(cur)
        if not m:
            break
        out.append(m)
        cur = m.get("parent")
    return out


def export_okf(root, outdir, kind_filter="episode") -> int:
    """Xuất store thành file .md ĐÚNG CHUẨN OKF v0.1 — mỗi memory một file, frontmatter YAML có
    `type` không rỗng + section `## Origin`, nên bỏ vào cây wiki là qua được R9/R2 mà không phải
    sửa gì. Đây là cầu nối "memory (máy ghi) → wiki (người đọc/kiểm)", trước đây phải chép tay.
    """
    root, out = Path(root), Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for m in _read(root):
        if kind_filter and m.get("kind") != kind_filter:
            continue
        mid = m.get("id") or f"mem-{n}"
        fm = ["---", f'type: {m.get("type") or m.get("kind") or "note"}',
              f'title: "{(m.get("did") or m.get("text") or mid).splitlines()[0][:90].replace(chr(34), chr(39))}"',
              f'id: {mid}', f'timestamp: {(m.get("ts") or "")[:10]}',
              "tags: [memory, episode]"]
        for k in ("session", "parent", "supersedes"):
            if m.get(k):
                fm.append(f"{k}: {m[k]}")
        if m.get("files"):
            fm.append("files: [" + ", ".join(m["files"]) + "]")
        fm.append("---")
        body = [f"\n# {(m.get('did') or mid)}\n", (m.get("text") or "").strip(), "",
                "## Origin", f"- **Source:** `harness/metrics/memory.jsonl` (mem-rank, id `{mid}`)",
                f"- **Session:** {m.get('session') or '(không rõ)'}"
                + (f" · tiếp nối `{m['parent']}`" if m.get("parent") else ""),
                f"- **Date:** {(m.get('ts') or '')[:10]}", ""]
        (out / f"{mid}.md").write_text("\n".join(fm + body), encoding="utf-8")
        n += 1
    return n


def delete(root, mid) -> int:
    root = Path(root)
    mems = _read(root)
    kept = [m for m in mems if m.get("id") != mid]
    _write_all(root, kept)
    return len(mems) - len(kept)


def export_all(root) -> int:
    """Dump toàn bộ store ra stdout dạng JSONL — memory di chuyển máy bằng file.
    (Ý từ claude-mem "memory phải portable"; code là của mình, format là store sẵn có.)"""
    mems = _read(Path(root))
    for m in mems:
        print(json.dumps(m, ensure_ascii=False))
    return len(mems)


def import_file(root, path):
    """Nạp JSONL vào store, dedupe theo id (bản trong store thắng — không ghi đè bản local)."""
    root = Path(root)
    have = {m.get("id") for m in _read(root)}
    added, skipped = [], 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            skipped += 1
            continue
        if not isinstance(rec, dict) or not rec.get("id") or rec["id"] in have:
            skipped += 1
            continue
        have.add(rec["id"])
        added.append(rec)
    if added:
        _write_all(root, _read(root) + added)
    return len(added), skipped


def _toks(s):
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def _overlap(query, text):
    q, t = _toks(query), _toks(text)
    if not q or not t:
        return 0.0
    return len(q & t) / len(q | t)            # Jaccard — deterministic


def _embed(text, cmd):
    """Pluggable embedder: writes `text` to the command's stdin, expects a JSON float
    array on stdout. Returns list[float] or None on any failure (caller falls back).
    `cmd` is any backend — ollama wrapper, Voyage/OpenAI script, local model — so no
    embedding dependency is baked into the framework."""
    try:
        p = subprocess.run(cmd, shell=True, input=(text or ""),
                           capture_output=True, text=True, timeout=30)
        vec = json.loads(p.stdout)
        if isinstance(vec, list) and vec and all(isinstance(x, (int, float)) for x in vec):
            return [float(x) for x in vec]
    except Exception:
        pass
    return None


def _cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if not na or not nb:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def retrieve(root, query, k=5, kind_filter=None, cfg=None):
    """Top-k by relevance. NOOP (empty) if nothing relevant — don't return noise.
    `kind_filter` restricts ranking to one memory kind (e.g. 'episode' for episodic recall).
    Scorer picked from config: 'embedding' (cosine over `relevance.embedder_cmd`, SEMANTIC —
    catches paraphrase/synonym) else 'token-overlap' (Jaccard, lexical, zero-dep default).
    Embedding path degrades to token-overlap if the backend is unset or unreachable."""
    root = Path(root)
    if cfg is None:
        cfg = load_config(root)
    mems = _read(root)
    if kind_filter:
        mems = [m for m in mems if m.get("kind") == kind_filter]
    rel = cfg.get("relevance", {}) or {}
    cmd = rel.get("embedder_cmd")
    use_embed = rel.get("scorer") == "embedding" and bool(cmd)
    qv = _embed(query, cmd) if use_embed else None
    if use_embed and qv is None:
        sys.stderr.write("mem-rank: embedder_cmd unreachable — falling back to token-overlap\n")
        use_embed = False
    if use_embed:
        thr = float(rel.get("min_score", 0.25))       # cosine>0 for unrelated too — need a floor
        scored = []
        for m in mems:
            mv = _embed(m.get("text", ""), cmd)
            s = _cosine(qv, mv) if mv else 0.0
            if s >= thr:
                scored.append((m, s))
    else:
        scored = [(m, _overlap(query, m.get("text", ""))) for m in mems]
        scored = [(m, s) for m, s in scored if s > 0]
    scored.sort(key=lambda ms: (-ms[1], ms[0].get("id", "")))
    return scored[:max(1, int(k))]


def _evict(mems, cfg):
    cap = int(cfg.get("eviction", {}).get("max_entries", 500))
    policy = cfg.get("eviction", {}).get("policy", "score")
    if len(mems) <= cap or policy == "none":
        return mems
    if policy == "lru":
        return mems[-cap:]                    # keep most-recent
    return mems[-cap:]                         # 'score' w/o query at write-time => recency fallback


def report(root) -> str:
    mems = _read(Path(root))
    out = [f"MemRank — {len(mems)} memories"]
    for m in mems:
        out.append(f"  {m.get('id'):<5} [{m.get('kind','')}] {m.get('text','')[:70]}")
    return "\n".join(out)


def self_test() -> int:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "harness").mkdir()
        _config_file(root).write_text("verified: false\neviction:\n  max_entries: 2\n  policy: lru\n", encoding="utf-8")
        add(root, "deploy the web app with docker compose", "ops")
        add(root, "fix the flaky retry test in CI", "test")
        hits = retrieve(root, "docker deploy", k=2)
        top_ok = hits and "docker" in hits[0][0]["text"]
        none_ok = retrieve(root, "completely unrelated zebra", k=2) == []   # NOOP
        add(root, "third memory triggers eviction (cap 2)", "note")          # cap=2 evicts oldest
        evict_ok = len(_read(root)) == 2
    # ── episodic + temporal slice (own store, no eviction) ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "harness").mkdir()
        _config_file(root).write_text("verified: false\neviction:\n  policy: none\n", encoding="utf-8")
        e1 = episode(root, "wired episodic retrieval into query skill",
                     files=["skills/query/SKILL.md"], outcome="query surfaces episodes", session="s1", mid="ep1")
        ep_stamped = bool(e1.get("ts")) and e1.get("kind") == "episode" and e1.get("files") == ["skills/query/SKILL.md"]
        ep_hits = retrieve(root, "how did query get episodic retrieval", k=3, kind_filter="episode")
        ep_hit_ok = bool(ep_hits) and ep_hits[0][0]["id"] == "ep1"
        add(root, "a plain note that must NOT show under episode filter", "note")
        filter_ok = [m for m, _ in retrieve(root, "note", k=5, kind_filter="episode")] == []
        # temporal supersede: newer episode replaces ep1, links back
        e2 = episode(root, "revised episodic recall to filter by kind", mid="ep1", supersedes="ep1")
        temporal_ok = e2.get("supersedes") == "ep1" and len(_read(root)) == 2  # ep1 replaced, note kept
        ep_ok = ep_stamped and ep_hit_ok and filter_ok and temporal_ok
    # ── embedding scorer slice: the REAL cosine path via a deterministic pluggable embedder ──
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "harness").mkdir()
        emb = root / "fake_embed.py"              # 26-dim letter-frequency embedder (deterministic)
        emb.write_text("import sys,json\nt=sys.stdin.read().lower()\n"
                       "print(json.dumps([float(t.count(chr(97+i))) for i in range(26)]))\n",
                       encoding="utf-8")
        cmd = f"{sys.executable} {emb}"
        _config_file(root).write_text(
            "verified: true\nrelevance:\n  scorer: embedding\n"
            f"  embedder_cmd: {json.dumps(cmd)}\n  min_score: 0.5\neviction:\n  policy: none\n",
            encoding="utf-8")
        cfg = load_config(root)
        add(root, "deploy the service to production", "ops")
        add(root, "xyzzy qwkk", "note")
        hits = retrieve(root, "production deployment of the service", k=2, cfg=cfg)
        embed_top_ok = bool(hits) and "deploy" in hits[0][0]["text"]
        # backend unreachable => graceful fallback to token-overlap, still returns lexical hit
        bad = dict(cfg); bad["relevance"] = {"scorer": "embedding", "embedder_cmd": "false", "min_score": 0.5}
        fb = retrieve(root, "deploy production", k=2, cfg=bad)
        fallback_ok = bool(fb) and "deploy" in fb[0][0]["text"]
        embed_ok = embed_top_ok and fallback_ok
    # ── export/import round-trip (portability máy↔máy) ──
    with tempfile.TemporaryDirectory() as d2:
        src, dst = Path(d2) / "src", Path(d2) / "dst"
        src.mkdir(); dst.mkdir()
        add(src, "portable fact", mid="port1")
        dump = "\n".join(json.dumps(m, ensure_ascii=False) for m in _read(src))
        f = Path(d2) / "mem.jsonl"; f.write_text(dump, encoding="utf-8")
        n1, _ = import_file(dst, str(f))
        n2, _ = import_file(dst, str(f))          # import lần 2 phải skip hết (dedupe)
        roundtrip_ok = n1 == 1 and n2 == 0 and _read(dst)[0]["id"] == "port1"
    # CHUỖI PHIÊN: parent="auto" phải bắt đúng phiên trước; chain() đi ngược đủ 3 mắt, không lặp.
    with tempfile.TemporaryDirectory() as d3:
        r3 = Path(d3); (r3 / "harness").mkdir()
        _config_file(r3).write_text("verified: false\n", encoding="utf-8")
        episode(r3, "phiên A: dựng validator", files=["a.py"], session="sessA", parent="auto")
        episode(r3, "phiên B: vá hook", files=["b.py"], session="sessB", parent="auto")
        episode(r3, "phiên C: viết test", files=["c.py"], session="sessC", parent="auto")
        ch = chain(r3)
        sids = [m.get("session") for m in ch]
        parents = [m.get("parent") for m in ch]
        chain_ok = sids == ["sessC", "sessB", "sessA"] and parents == ["sessB", "sessA", None]
        # phiên ghi 2 episode: không tự trỏ chính mình (parent bỏ qua session hiện tại)
        episode(r3, "phiên C: thêm ca", files=["c2.py"], session="sessC", parent="auto")
        self_ok = chain(r3)[0].get("parent") == "sessB"
        # chain từ một phiên GIỮA chuỗi
        mid_ok = [m.get("session") for m in chain(r3, "sessB")] == ["sessB", "sessA"]
        chain_ok = chain_ok and self_ok and mid_ok

        # OKF: file xuất ra phải qua ĐÚNG validator R9 đang gác wiki, không tự chấm mình.
        okdir = r3 / "okf"
        n_okf = export_okf(r3, okdir)
        v = Path(__file__).resolve().parents[1] / "validators" / "okf_frontmatter.py"
        files = sorted(str(f) for f in okdir.glob("*.md"))
        rc_okf = subprocess.run([sys.executable, str(v), *files], capture_output=True).returncode if v.exists() else 0
        first = Path(files[0]).read_text(encoding="utf-8") if files else ""
        okf_ok = n_okf == 4 and rc_okf == 0 and "## Origin" in first and "type: episode" in first

    ok = (bool(top_ok) and none_ok and evict_ok and ep_ok and embed_ok and roundtrip_ok
          and chain_ok and okf_ok)
    print("mem-rank self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _opt(args, flag):
    if flag in args:
        i = args.index(flag)
        val = args[i + 1] if len(args) > i + 1 else None
        del args[i:i + 2]
        return val
    return None


def main() -> None:
    args = sys.argv[1:]
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    r = _opt(args, "--root")
    if r:
        root = Path(r)
    kind = _opt(args, "--kind")
    mid = _opt(args, "--id")
    files = _opt(args, "--files")
    outcome = _opt(args, "--outcome")
    session = _opt(args, "--session")
    supersedes = _opt(args, "--supersedes")
    kind_filter = _opt(args, "--kind-filter")
    k = _opt(args, "--k") or 5
    if "--self-test" in args:
        sys.exit(self_test())
    if "--report" in args:
        print(report(root)); return
    if args and args[0] == "add":
        if len(args) < 2:
            print('usage: mem-rank.py add "<text>" [--kind k]', file=sys.stderr); sys.exit(2)
        rec = add(root, args[1], kind, mid, supersedes=supersedes)
        print(f"added {rec['id']}: {rec['text'][:60]}"); return
    if args and args[0] == "episode":
        if len(args) < 2:
            print('usage: mem-rank.py episode "<did>" [--files a,b] [--outcome o] [--session s] [--parent S|auto] [--supersedes ID]',
                  file=sys.stderr); sys.exit(2)
        rec = episode(root, args[1], files=files, outcome=outcome, session=session, parent=_opt(args, "--parent"),
                      supersedes=supersedes, mid=mid)
        sup = f" (supersedes {rec['supersedes']})" if rec.get("supersedes") else ""
        print(f"episode {rec['id']} @ {rec['ts']}{sup}: {rec['text'][:60]}"); return
    if args and args[0] == "export-okf":
        d = _opt(args, "--out") or "llmwiki/wiki/sources/memory"
        n = export_okf(root, root / d if not str(d).startswith("/") else d,
                       kind_filter=_opt(args, "--kind") or "episode")
        print(f"export-okf: {n} file .md (OKF v0.1) → {d}"); return
    if args and args[0] == "chain":
        rows = chain(root, args[1] if len(args) > 1 and not args[1].startswith("-") else None)
        if "--json" in args:
            print(json.dumps(rows, ensure_ascii=False, indent=1)); return
        if not rows:
            print("mem-rank: chưa có episode nào — chuỗi rỗng"); return
        print(f"CHUỖI PHIÊN ({len(rows)}, mới → cũ)")
        for i, m in enumerate(rows):
            mt = m
            arrow = "└─" if i == len(rows) - 1 else "├─"
            print(f"  {arrow} {(mt.get('session') or '?')[:8]}  {m.get('ts', '')[:16]}  {mt.get('did', '')[:70]}")
            for f in (mt.get("files") or [])[:4]:
                print(f"  {'  ' if i == len(rows) - 1 else '│ '}    · {f}")
        return
    if args and args[0] == "delete":
        if len(args) < 2:
            print("usage: mem-rank.py delete ID", file=sys.stderr); sys.exit(2)
        n = delete(root, args[1]); print(f"deleted {n}"); return
    if args and args[0] == "export":
        export_all(root); return
    if args and args[0] == "import":
        if len(args) < 2:
            print("usage: mem-rank.py import <file.jsonl>", file=sys.stderr); sys.exit(2)
        n, sk = import_file(root, args[1])
        print(f"imported {n}, skipped {sk}"); return
    if args and args[0] == "retrieve":
        if len(args) < 2:
            print('usage: mem-rank.py retrieve "<query>" [--k N] [--kind-filter K]', file=sys.stderr); sys.exit(2)
        hits = retrieve(root, args[1], k, kind_filter=kind_filter)
        if not hits:
            print("(NOOP — no relevant memory)"); return
        for m, s in hits:
            tag = f"[{m.get('kind','')}] " if m.get("kind") else ""
            print(f"  {s:.2f}  {m.get('id')}  {tag}{m.get('text','')[:70]}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
