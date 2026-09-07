#!/usr/bin/env python3
"""okf-scan — quét MỌI nguồn OKF (wiki + memory store) theo tag/type, trả về mục liên quan,
và ĐỂ LẠI BIÊN LAI để biết việc quét có thật sự chạy — rồi đối chiếu transcript xem agent
có MỞ những mục đó không.

Vì sao cần: recall/orient chỉ *in gợi ý* vào context. Không có gì chứng minh (a) việc quét đã
chạy, (b) agent có đọc thứ được trả về hay chỉ lướt qua. "Agent bảo là đã đọc wiki" không phải
bằng chứng. Ở đây cả hai vế đều tất định, 0 token:

  query "<từ khoá>" [--tags a,b] [--type t] [--k N] [--session S] [--json]
        Quét frontmatter OKF (`type`, `tags`, `title`, `id`) của mọi file .md trong các cây wiki
        + mọi record trong harness/metrics/memory.jsonl (đã mang `type`), xếp hạng theo tag khớp
        rồi token-overlap, in top-k. GHI biên lai {ts, session, query, scanned, returned}.

  verify --session S --transcript P [--json]
        Đọc transcript của phiên, xem mục nào trong `returned` thật sự xuất hiện ở đầu vào
        tool (Read/Grep/…): cập nhật biên lai `opened` + `coverage`. Đây là chỗ duy nhất
        phân biệt "đã trả về" với "đã đọc".

  receipts [--session S] [--json]      xem biên lai
  --check --session S                  exit 2 nếu phiên KHÔNG có biên lai quét nào (gate)
  --self-test

Biên lai: harness/metrics/context-receipts.jsonl (gitignore như các sổ khác).
Fail-open: mọi lỗi hạ tầng → im lặng, exit 0. Đây là công cụ đo, không được phá phiên.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    import overstack_paths
except Exception:
    overstack_paths = None

RECEIPTS = "harness/metrics/context-receipts.jsonl"
MEMORY = "harness/metrics/memory.jsonl"
WIKI_CANDS = ("fdk/wiki", ".llmwiki/wiki", "llmwiki/wiki", "wiki")
FM = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.S)
_WORD = re.compile(r"[a-z0-9à-ỹ]+", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _toks(s: str) -> set:
    return {w.lower() for w in _WORD.findall(s or "") if len(w) > 2}


def _frontmatter(text: str) -> dict:
    """Đọc frontmatter OKF không cần pyyaml — chỉ cần scalar + list phẳng (đủ cho type/tags/title)."""
    m = FM.match(text or "")
    if not m:
        return {}
    out = {}
    for ln in m.group(1).splitlines():
        if ":" not in ln or ln.lstrip().startswith("#") or ln.startswith(" "):
            continue
        k, v = ln.split(":", 1)
        k, v = k.strip(), v.strip().strip("'\"")
        if not k or not v:
            continue
        if v.startswith("[") and v.endswith("]"):
            out[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        else:
            out[k] = v
    return out


def wiki_dirs(root: Path) -> list:
    return [root / c for c in WIKI_CANDS if (root / c).is_dir()]


def collect(root: Path) -> list:
    """Mọi mục OKF: file .md có frontmatter trong các cây wiki + record trong memory store."""
    items = []
    for wd in wiki_dirs(root):
        for p in wd.rglob("*.md"):
            try:
                fm = _frontmatter(p.read_text(encoding="utf-8", errors="ignore")[:2000])
            except Exception:
                continue
            if not fm.get("type"):
                continue                     # OKF v0.1: không có `type` thì không phải mục OKF
            tags = fm.get("tags") or []
            items.append({"source": "wiki", "path": str(p.relative_to(root)),
                          "type": fm["type"], "title": fm.get("title") or p.stem,
                          "tags": tags if isinstance(tags, list) else [str(tags)], "id": fm.get("id") or p.stem})
    try:
        for ln in (root / MEMORY).read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            m = json.loads(ln)
            if not m.get("type"):
                continue
            items.append({"source": "memory", "path": f"{MEMORY}#{m.get('id')}",
                          "type": m["type"], "title": (m.get("did") or m.get("text") or "")[:90],
                          "tags": ["memory", m["type"]] + ([m["session"]] if m.get("session") else []),
                          "id": m.get("id")})
    except Exception:
        pass
    return items


def rank(items: list, query: str, tags=None, type_filter=None, k: int = 5) -> list:
    """Tag khớp thắng token-overlap: tag là thứ người/máy khai CHỦ ĐÍCH, chính xác hơn đoán từ chữ."""
    want_tags = {t.strip().lower() for t in (tags or []) if t.strip()}
    q = _toks(query)
    out = []
    for it in items:
        if type_filter and it["type"] != type_filter:
            continue
        it_tags = {str(t).lower() for t in it.get("tags") or []}
        tag_hit = len(want_tags & it_tags)
        if want_tags and not tag_hit:
            continue
        hay = _toks(" ".join([it.get("title") or "", it.get("path") or "", " ".join(it_tags)]))
        overlap = len(q & hay) / len(q | hay) if (q and hay) else 0.0
        score = tag_hit * 10 + overlap
        if score > 0:
            out.append((score, it))
    out.sort(key=lambda x: (-x[0], x[1]["path"]))
    return [dict(it, score=round(sc, 4)) for sc, it in out[:k]]


def _receipts_file(root: Path) -> Path:
    p = root / RECEIPTS
    p.parent.mkdir(parents=True, exist_ok=True)
    try:                                     # sổ local, không vào git — cùng quy ước các sổ khác
        gi = root / ".gitignore"
        cur = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
        if RECEIPTS not in cur:
            with open(gi, "a", encoding="utf-8") as f:
                f.write(f"\n# okf-scan context receipts\n{RECEIPTS}\n")
    except Exception:
        pass
    return p


def write_receipt(root: Path, rec: dict) -> None:
    try:
        with open(_receipts_file(root), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_receipts(root: Path, session=None) -> list:
    out = []
    try:
        for ln in (root / RECEIPTS).read_text(encoding="utf-8").splitlines():
            if not ln.strip():
                continue
            r = json.loads(ln)
            if session and r.get("session") != session:
                continue
            out.append(r)
    except Exception:
        pass
    return out


def query(root: Path, q: str, tags=None, type_filter=None, k=5, session=None) -> dict:
    items = collect(root)
    hits = rank(items, q, tags, type_filter, k)
    rec = {"ts": _now(), "session": session or "", "query": q,
           "tags": tags or [], "scanned": len(items),
           "returned": [h["path"] for h in hits], "hits": hits}
    write_receipt(root, rec)
    return rec


def verify(root: Path, session: str, transcript: str) -> dict:
    """Mục đã TRẢ VỀ nào thật sự xuất hiện trong đầu vào tool của phiên (agent đã mở/đọc)?

    Nguồn duy nhất trung thực là transcript của provider: nó ghi tool_use với tham số thật.
    So khớp bằng basename + đường dẫn tương đối để không phụ thuộc agent gõ tuyệt đối hay không.
    """
    returned = []
    for r in read_receipts(root, session):
        returned += r.get("returned") or []
    returned = sorted(set(returned))
    blob = ""
    try:
        blob = Path(transcript).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        pass
    opened = [p for p in returned if p and (p in blob or Path(p).name in blob)]
    cov = round(len(opened) / len(returned), 3) if returned else 0.0
    rec = {"ts": _now(), "session": session, "kind": "verify", "returned": returned,
           "opened": opened, "coverage": cov}
    write_receipt(root, rec)
    return rec


def self_test() -> int:
    ok = True

    def chk(c, m):
        nonlocal ok
        print(("  \033[1;32m✓\033[0m " if c else "  \033[1;31m✗\033[0m ") + m)
        ok = ok and bool(c)

    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        wd = root / ".llmwiki" / "wiki" / "concepts"
        wd.mkdir(parents=True)
        (wd / "harness-rules.md").write_text(
            "---\ntype: concept\ntitle: \"luật harness R1-R19\"\ntags: [harness, rules, gate]\nid: harness-rules\n---\n\n# x\n## Origin\n- a\n",
            encoding="utf-8")
        (wd / "design-taste.md").write_text(
            "---\ntype: concept\ntitle: \"gu thiết kế UI\"\ntags: [design, ui]\nid: design-taste\n---\n\n# y\n## Origin\n- b\n",
            encoding="utf-8")
        (wd / "no-frontmatter.md").write_text("# không phải OKF\n", encoding="utf-8")
        (root / "harness" / "metrics").mkdir(parents=True)
        (root / MEMORY).write_text(json.dumps(
            {"id": "ep1", "kind": "episode", "type": "episode", "did": "vá hook harness",
             "session": "sessA", "ts": "2026-09-07T00:00:00"}) + "\n", encoding="utf-8")

        items = collect(root)
        chk(len(items) == 3, f"collect: 2 wiki OKF + 1 memory, bỏ file thiếu frontmatter ({len(items)})")

        r = query(root, "luật harness", session="sessX")
        chk(r["scanned"] == 3 and r["returned"] and "harness-rules" in r["returned"][0],
            f"query xếp đúng mục liên quan nhất ({r['returned'][:1]})")

        r2 = query(root, "bất kỳ", tags=["design"], session="sessX")
        chk(len(r2["returned"]) == 1 and "design-taste" in r2["returned"][0],
            "lọc theo tag: chỉ trả mục mang tag đó")

        r3 = query(root, "vá hook", type_filter="episode", session="sessX")
        chk(len(r3["returned"]) == 1 and "memory.jsonl" in r3["returned"][0],
            "lọc theo type: memory store cũng là nguồn OKF")

        rs = read_receipts(root, "sessX")
        chk(len(rs) == 3 and all(x.get("scanned") == 3 for x in rs),
            f"biên lai ghi đủ mỗi lượt quét ({len(rs)})")
        chk(read_receipts(root, "khac") == [], "lọc biên lai theo phiên")

        tr = root / "t.jsonl"
        tr.write_text('{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read",'
                      '"input":{"file_path":"/x/.llmwiki/wiki/concepts/harness-rules.md"}}]}}\n', encoding="utf-8")
        v = verify(root, "sessX", str(tr))
        chk(len(v["opened"]) == 1 and 0 < v["coverage"] < 1,
            f"verify: đếm ĐÚNG mục agent thật sự mở ({v['opened']}, coverage {v['coverage']})")

        v2 = verify(root, "sessX", str(root / "khong-co.jsonl"))
        chk(v2["opened"] == [] and v2["coverage"] == 0.0, "transcript thiếu → coverage 0, không nổ")

        chk(check(root, "sessX") == 0 and check(root, "sessRong") == 2,
            "check: phiên có biên lai → 0, phiên chưa quét gì → 2")
        chk(RECEIPTS in (root / ".gitignore").read_text(encoding="utf-8"), "sổ biên lai tự vào .gitignore")

    print("okf-scan self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 2


def check(root: Path, session: str) -> int:
    return 0 if read_receipts(root, session) else 2


def _opt(args, flag, default=None):
    if flag in args:
        i = args.index(flag)
        return args[i + 1] if i + 1 < len(args) else default
    return default


def main() -> None:
    args = sys.argv[1:]
    if "--self-test" in args:
        sys.exit(self_test())
    root = Path(_opt(args, "--root") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    sess = _opt(args, "--session", "")
    try:
        if args and args[0] == "query":
            tags = [t for t in (_opt(args, "--tags") or "").split(",") if t.strip()]
            rec = query(root, args[1] if len(args) > 1 else "", tags,
                        _opt(args, "--type"), int(_opt(args, "--k") or 5), sess)
            if "--json" in args:
                print(json.dumps(rec, ensure_ascii=False, indent=1)); return
            if not rec["hits"]:
                print(f"okf-scan: quét {rec['scanned']} mục OKF — không có mục nào khớp"); return
            print(f"okf-scan: quét {rec['scanned']} mục OKF → {len(rec['hits'])} liên quan"
                  + (f" (tag: {', '.join(tags)})" if tags else ""))
            for h in rec["hits"]:
                print(f"  · {h['path']}  [{h['type']}] {h['title'][:60]}"
                      + (f"  tags: {', '.join(map(str, h['tags'][:4]))}" if h.get("tags") else ""))
            return
        if args and args[0] == "verify":
            rec = verify(root, sess, _opt(args, "--transcript", "") or "")
            if "--json" in args:
                print(json.dumps(rec, ensure_ascii=False, indent=1)); return
            print(f"okf-scan verify {sess[:8]}: trả về {len(rec['returned'])} mục · "
                  f"agent MỞ {len(rec['opened'])} · coverage {rec['coverage']:.0%}")
            for p in rec["opened"]:
                print(f"  ✓ đã mở: {p}")
            for p in [x for x in rec["returned"] if x not in rec["opened"]]:
                print(f"  · chưa mở: {p}")
            return
        if args and args[0] == "receipts":
            rs = read_receipts(root, sess or None)
            if "--json" in args:
                print(json.dumps(rs, ensure_ascii=False, indent=1)); return
            if not rs:
                print("okf-scan: chưa có biên lai nào"); return
            for r in rs:
                if r.get("kind") == "verify":
                    print(f"  {r['ts'][:16]}  {r.get('session', '')[:8]}  VERIFY  "
                          f"mở {len(r.get('opened') or [])}/{len(r.get('returned') or [])} "
                          f"({r.get('coverage', 0):.0%})")
                else:
                    print(f"  {r['ts'][:16]}  {r.get('session', '')[:8]}  quét {r.get('scanned', 0)} "
                          f"→ {len(r.get('returned') or [])}  «{(r.get('query') or '')[:40]}»")
            return
        if "--check" in args:
            rc = check(root, sess)
            print(f"okf-scan: phiên {sess[:8] or '?'} "
                  + ("CÓ biên lai quét context" if rc == 0 else "CHƯA quét context lần nào"))
            sys.exit(rc)
    except SystemExit:
        raise
    except Exception as e:
        print(f"okf-scan: lỗi hạ tầng, bỏ qua (fail-open): {e}", file=sys.stderr); sys.exit(0)
    print(__doc__)


if __name__ == "__main__":
    main()
