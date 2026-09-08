#!/usr/bin/env python3
"""Static parse: build nodes + edges from repo files. No LLM."""
import json, os, re, sys, subprocess
from collections import defaultdict, Counter

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
T = os.path.join(ROOT, ".overstack", "onboard", "tmp")

SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc", ".lock", ".woff", ".woff2", ".zip"}
CODE_EXT = {".py", ".sh", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs"}
CONF_EXT = {".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".jsonl"}
DOC_EXT = {".md", ".mdx", ".txt", ".rst"}

files = [l.strip() for l in open(os.path.join(T, "files.txt")) if l.strip()]
files = [f for f in files if os.path.splitext(f)[1].lower() not in SKIP_EXT]
fileset = set(files)

# ---------- churn / recent ----------
churn = {}
for line in open(os.path.join(T, "churn.txt")):
    p = line.strip().split(None, 1)
    if len(p) == 2:
        churn[p[1]] = int(p[0])
recent = {l.strip() for l in open(os.path.join(T, "recent.txt")) if l.strip()}

def ntype(path):
    e = os.path.splitext(path)[1].lower()
    if e in CODE_EXT: return "file"
    if e in CONF_EXT: return "config"
    if e in DOC_EXT: return "document"
    if e in (".html",): return "document"
    return "file"

def nid(path):
    t = ntype(path)
    return f"{t}:{path}"

def read(path, limit=200000):
    try:
        with open(os.path.join(ROOT, path), "r", encoding="utf-8", errors="replace") as f:
            return f.read(limit)
    except Exception:
        return ""

# ---------- summary extraction ----------
def summarize(path, text):
    e = os.path.splitext(path)[1].lower()
    lines = text.split("\n")
    if e == ".md":
        # frontmatter description / first heading + first prose line
        head, prose = "", ""
        i = 0
        if lines and lines[0].strip() == "---":
            for j in range(1, min(len(lines), 40)):
                if lines[j].strip() == "---":
                    i = j + 1
                    break
                m = re.match(r"\s*(description|title|summary)\s*:\s*(.+)", lines[j])
                if m and not head:
                    head = m.group(2).strip().strip('"\'')
        for l in lines[i:i + 80]:
            s = l.strip()
            if not s or s.startswith(("---", "|", "```", "<!--")): continue
            if s.startswith("#") and not head:
                head = s.lstrip("#").strip(); continue
            if not s.startswith(("#", ">", "-", "*", "[")) and len(s) > 25 and not prose:
                prose = s; break
            if s.startswith(">") and not prose and len(s) > 25:
                prose = s.lstrip("> ").strip(); break
        out = " — ".join(x for x in (head, prose) if x)
        return out[:300] or os.path.basename(path)
    if e == ".py":
        m = re.search(r'^\s*(?:#!.*\n)?(?:# -\*-.*\n)?(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', text, re.S)
        if m: return " ".join(m.group(1).split())[:300]
        cm = [l.lstrip("# ").strip() for l in lines[:12] if l.startswith("#") and not l.startswith("#!")]
        if cm: return " ".join(cm)[:300]
    if e == ".sh":
        cm = [l.lstrip("# ").strip() for l in lines[:15] if l.startswith("#") and not l.startswith("#!")]
        if cm: return " ".join(cm)[:300]
    if e in (".json", ".jsonl"):
        try:
            d = json.loads(text)
            if isinstance(d, dict):
                for k in ("description", "name", "title"):
                    if k in d and isinstance(d[k], str): return d[k][:300]
                return "keys: " + ", ".join(list(d.keys())[:10])
        except Exception:
            pass
    if e in (".yaml", ".yml"):
        cm = [l.lstrip("# ").strip() for l in lines[:10] if l.startswith("#")]
        if cm: return " ".join(cm)[:300]
        keys = [l.split(":")[0] for l in lines[:60] if re.match(r"^[a-zA-Z_][\w-]*:", l)]
        if keys: return "top keys: " + ", ".join(keys[:10])
    if e == ".html":
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        if m: return " ".join(m.group(1).split())[:300]
    return os.path.basename(path)

# ---------- edge resolution helpers ----------
basename_idx = defaultdict(list)
for f in files:
    basename_idx[os.path.basename(f)].append(f)

def resolve(cand, frm):
    """Resolve a referenced path string to a tracked file."""
    if not cand: return None
    cand = cand.strip().strip('"\'`')
    cand = cand.split("#")[0].split("?")[0]
    if not cand or cand.startswith(("http://", "https://", "mailto:")): return None
    cand = cand.replace("$PROJECT_ROOT/", "").replace("./", "", 1) if cand.startswith("./") else cand
    tries = []
    d = os.path.dirname(frm)
    tries.append(os.path.normpath(os.path.join(d, cand)))
    tries.append(os.path.normpath(cand.lstrip("/")))
    for t in tries:
        if t in fileset: return t
    b = os.path.basename(cand)
    if b in basename_idx and len(basename_idx[b]) == 1:
        return basename_idx[b][0]
    return None

nodes, edges = {}, {}

def add_edge(s, t, typ, w):
    if s == t: return
    k = (s, t, typ)
    if k not in edges:
        edges[k] = {"source": s, "target": t, "type": typ, "weight": w}

WEIGHT = {"contains": 1.0, "inherits": 0.9, "implements": 0.9, "calls": 0.8, "exports": 0.8,
          "imports": 0.7, "depends_on": 0.6, "configures": 0.6, "documents": 0.5,
          "tested_by": 0.5, "related": 0.5, "triggers": 0.5, "deploys": 0.5}

# python module map: dotted module -> file
pymod = {}
for f in files:
    if f.endswith(".py"):
        mod = f[:-3].replace("/", ".")
        pymod[mod] = f
        pymod[os.path.basename(f)[:-3]] = pymod.get(os.path.basename(f)[:-3], f)

RE_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
RE_WIKILINK = re.compile(r"\[\[([^\]|#]+)")
RE_PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)
RE_PATHLIKE = re.compile(r"[\w./-]*\b(?:harness|fdk|skills|llmwiki|scripts|hooks|tools)/[\w./-]+\.(?:py|sh|yaml|yml|json|md|html)")
RE_SH_SRC = re.compile(r"(?:^|\s)(?:source|\.|bash|sh|python3?)\s+([\"']?[\w$./{}-]+\.(?:sh|py))", re.M)

stats = Counter()
for f in files:
    text = read(f)
    t = ntype(f)
    node = {
        "id": nid(f), "type": t, "name": os.path.basename(f), "filePath": f,
        "summary": summarize(f, text), "tags": [],
    }
    if f in churn and churn[f] >= 14: node["tags"].append("hot")
    if f in recent: node["tags"].append("recent")
    if churn.get(f): node["churn"] = churn[f]
    node["lines"] = text.count("\n") + 1
    nodes[node["id"]] = node
    stats[t] += 1

    e = os.path.splitext(f)[1].lower()
    # --- python imports ---
    if e == ".py":
        for m in RE_PY_IMPORT.finditer(text):
            mod = m.group(1) or m.group(2)
            tgt = pymod.get(mod) or pymod.get(mod.split(".")[0])
            if tgt and tgt != f:
                add_edge(nid(f), nid(tgt), "imports", WEIGHT["imports"])
    # --- shell sourcing / invoking scripts ---
    if e == ".sh" or e == ".py":
        for m in RE_SH_SRC.finditer(text):
            tgt = resolve(m.group(1), f)
            if tgt and tgt != f:
                add_edge(nid(f), nid(tgt), "calls", WEIGHT["calls"])
    # --- markdown links + path mentions ---
    if e in (".md", ".mdx"):
        for m in RE_MD_LINK.finditer(text):
            tgt = resolve(m.group(1), f)
            if tgt and tgt != f:
                add_edge(nid(f), nid(tgt), "documents", WEIGHT["documents"])
    # --- generic path mentions in any text file (scripts referencing configs etc.) ---
    if e in (".sh", ".py", ".yaml", ".yml", ".json", ".md", ".html"):
        for m in RE_PATHLIKE.finditer(text):
            tgt = resolve(m.group(0), f)
            if tgt and tgt != f:
                typ = "documents" if e in (".md", ".mdx") else ("configures" if e in (".yaml", ".yml", ".json") else "depends_on")
                add_edge(nid(f), nid(tgt), typ, WEIGHT[typ])

# --- tests ---
for f in files:
    b = os.path.basename(f)
    if b.startswith("test_") or b.endswith("_test.py") or "/tests/" in f or "/test/" in f:
        nodes[nid(f)]["tags"].append("test")
        stem = b.replace("test_", "").replace("_test", "")
        for cand in basename_idx.get(stem, []):
            if cand != f:
                add_edge(nid(cand), nid(f), "tested_by", WEIGHT["tested_by"])

# ---------- co-change edges ----------
raw = subprocess.run(["git", "-C", ROOT, "log", "--since=365 days ago", "--name-only",
                      "--pretty=format:@@%H"], capture_output=True, text=True).stdout
pairs = Counter()
cur = []
for line in raw.split("\n"):
    if line.startswith("@@"):
        if 1 < len(cur) <= 12:
            cs = sorted(set(x for x in cur if x in fileset))
            for i in range(len(cs)):
                for j in range(i + 1, len(cs)):
                    pairs[(cs[i], cs[j])] += 1
        cur = []
    elif line.strip():
        cur.append(line.strip())
cochange = 0
for (a, b), c in pairs.items():
    if c >= 4:
        add_edge(nid(a), nid(b), "related", WEIGHT["related"])
        cochange += 1

out = {"nodes": list(nodes.values()), "edges": list(edges.values())}
json.dump(out, open(os.path.join(T, "assembled-graph.json"), "w"), ensure_ascii=False, indent=1)

et = Counter(e["type"] for e in out["edges"])
print(f"nodes={len(out['nodes'])} edges={len(out['edges'])} cochange={cochange}")
print("node types:", dict(stats))
print("edge types:", dict(et))
orphans = len([n for n in out["nodes"] if not any(e["source"] == n["id"] or e["target"] == n["id"] for e in out["edges"])])
print("orphans:", orphans)
