#!/usr/bin/env python3
"""unknown-ledger — sổ nợ 'fill-first, find-out-later' (tất định, 0-token).

Đóng khoảng hở giữa `(default)` (điền im lặng) và `[CẦN LÀM RÕ]` (chặn cổng):
một unknown đã fill-default để KHÔNG chặn việc, nhưng ghi thành nợ CÓ SỔ, truy được,
trả được. Nhớ-còn-unknown-nào là việc của MÁY đọc sổ, không nhờ model nhớ.

Sổ = file `.md` một-nguồn-một-file ở llmwiki/wiki/draft/unknown/unknown-<source>.md
(frontmatter type/source_task/source_spec/status + mục ## U-NN). BÁO CÁO, KHÔNG CHẶN —
fill-first nghĩa là cố ý không chặn.

Dùng:
  unknown-ledger.py --list                         # mọi unknown mở, gom theo nguồn, cũ nhất trước
  unknown-ledger.py --add --file unknown-x.md --fr FR-003 --source <spec> --task T-... \\
                    --q "..." --default "..." --verify "..." --risk "..." --date YYYY-MM-DD
  unknown-ledger.py --resolve --file unknown-x.md --id U-01 --value "..." --fixed "..." --date YYYY-MM-DD
  unknown-ledger.py --trace --file unknown-x.md --id U-01     # đường truy ngược SPEC/FR/task
  unknown-ledger.py --self-test
  unknown-ledger.py --json
"""
import argparse
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Chuẩn mới `.llmwiki` trước, `llmwiki` để tương thích ngược (xem overstack_paths.py).
DIR = next((ROOT / n / "wiki" / "draft" / "unknown" for n in (".llmwiki", "llmwiki")
            if (ROOT / n).is_dir()), ROOT / "llmwiki" / "wiki" / "draft" / "unknown")
U_RE = re.compile(r"^##\s+(U-\d+)\s+—\s+(.*)$", re.M)
FIELD_RE = {
    "trace": re.compile(r"^-\s+\*\*Trace:\*\*\s*(.*)$", re.M),
    "default": re.compile(r"^-\s+\*\*Đã fill \(default\):\*\*\s*(.*)$", re.M),
    "verify": re.compile(r"^-\s+\*\*Cần verify:\*\*\s*(.*)$", re.M),
    "risk": re.compile(r"^-\s+\*\*Rủi ro nếu default sai:\*\*\s*(.*)$", re.M),
    "status": re.compile(r"^-\s+\*\*Status:\*\*\s*(.*)$", re.M),
    "resolved": re.compile(r"^-\s+\*\*Resolved:\*\*\s*(.*)$", re.M),
}


def _fm(text, key):
    m = re.search(rf"^{key}:\s*(.*)$", text, re.M)
    return m.group(1).strip().strip('"') if m else ""


def parse_file(path):
    """Trả {source_spec, source_task, status, units:[{id,q,trace,default,verify,risk,status,resolved}]}."""
    t = Path(path).read_text(encoding="utf-8", errors="ignore")
    blocks = list(U_RE.finditer(t))
    units = []
    for i, m in enumerate(blocks):
        end = blocks[i + 1].start() if i + 1 < len(blocks) else len(t)
        body = t[m.end():end]
        u = {"id": m.group(1), "q": m.group(2).strip()}
        for k, rx in FIELD_RE.items():
            fm = rx.search(body)
            u[k] = fm.group(1).strip() if fm else ""
        units.append(u)
    return {"file": Path(path).name, "source_spec": _fm(t, "source_spec"),
            "source_task": _fm(t, "source_task"), "status": _fm(t, "status"), "units": units}


def all_files():
    return sorted(p for p in glob.glob(str(DIR / "*.md")) if Path(p).name != "_template.md")


def open_units():
    out = []
    for f in all_files():
        d = parse_file(f)
        for u in d["units"]:
            st = u.get("status", "").lower()
            if "resolved" not in st:
                out.append({**u, "_file": d["file"], "_spec": d["source_spec"], "_task": d["source_task"]})
    return out


def next_id(path):
    d = parse_file(path)
    nums = [int(u["id"].split("-")[1]) for u in d["units"]]
    return f"U-{(max(nums) + 1) if nums else 1:02d}"


def add(args):
    path = DIR / args.file
    if not path.is_file():
        print(f"unknown-ledger: chưa có {path} — tạo từ _template.md trước.", file=sys.stderr)
        sys.exit(1)
    uid = next_id(path)
    block = (f"\n## {uid} — {args.q}\n"
             f"- **Trace:** {args.fr} · SPEC `{args.source}` · task `{args.task}`\n"
             f"- **Đã fill (default):** {args.default}\n"
             f"- **Cần verify:** {args.verify}\n"
             f"- **Rủi ro nếu default sai:** {args.risk}\n"
             f"- **Status:** open\n"
             f"- **Resolved:** _(chưa)_\n")
    # chèn TRƯỚC section '## Origin' nếu có, không thì append
    t = path.read_text(encoding="utf-8")
    idx = t.find("\n## Origin")
    t = (t[:idx] + block + t[idx:]) if idx >= 0 else (t.rstrip() + "\n" + block)
    path.write_text(t, encoding="utf-8")
    print(f"✓ {args.file} += {uid}. Dán vào SPEC: (default, find-out-later → [[{path.stem}]] {uid})")


def resolve(args):
    path = DIR / args.file
    d = parse_file(path)
    if not any(u["id"] == args.id for u in d["units"]):
        print(f"unknown-ledger: không thấy {args.id} trong {args.file}", file=sys.stderr)
        sys.exit(1)
    t = path.read_text(encoding="utf-8")
    # trong block của U-id: đổi Status → resolved, điền Resolved
    pat = re.compile(rf"(##\s+{re.escape(args.id)}\s+—.*?)(?=^##\s|\Z)", re.M | re.S)
    m = pat.search(t)
    blk = m.group(1)
    blk2 = re.sub(r"(- \*\*Status:\*\*).*", r"\1 resolved", blk)
    blk2 = re.sub(r"(- \*\*Resolved:\*\*).*",
                  rf"\1 {args.value} · fix: {args.fixed} · {args.date}", blk2)
    t = t[:m.start()] + blk2 + t[m.end():]
    path.write_text(t, encoding="utf-8")
    print(f"✓ {args.file} {args.id} → resolved (audit giữ cả giá trị-đã-fill).")


def trace(args):
    d = parse_file(DIR / args.file)
    for u in d["units"]:
        if u["id"] == args.id:
            print(f"{u['id']} — {u['q']}")
            print(f"  ↳ {u['trace']}")
            print(f"  spec: {d['source_spec']} · task: {d['source_task']} · status: {u['status']}")
            return
    print(f"không thấy {args.id}", file=sys.stderr); sys.exit(1)


def report(as_json=False):
    units = open_units()
    if as_json:
        print(json.dumps({"open": len(units), "units": units}, ensure_ascii=False, indent=2))
        return 0
    from collections import Counter
    by_spec = Counter(u["_spec"] or u["_file"] for u in units)
    print(f"unknown-ledger · {len(units)} unknown MỞ (fill-first, chờ verify) — báo cáo, KHÔNG chặn")
    for u in units:
        print(f"  {u['_file']} {u['id']}: {u['q'][:56]}")
    if by_spec:
        top = by_spec.most_common(1)[0]
        print(f"  nguồn nhiều nợ nhất: {top[0]} ({top[1]})")
    if not units:
        print("  (không còn nợ unknown mở)")
    return 0


def self_test():
    import tempfile
    d = tempfile.mkdtemp()
    global DIR
    old = DIR
    DIR = Path(d)
    try:
        f = DIR / "unknown-x.md"
        f.write_text("---\ntype: unknown-ledger\nsource_spec: wiki/sources/draft/x.md\n"
                     "source_task: T-1\nstatus: open\n---\n# x\n\n## Origin\n- s\n", encoding="utf-8")
        class A: pass
        a = A(); a.file = "unknown-x.md"; a.fr = "FR-001"; a.source = "wiki/sources/draft/x.md"
        a.task = "T-1"; a.q = "auth?"; a.default = "email/pass"; a.verify = "hỏi user"
        a.risk = "sai cơ chế"; a.date = "2026-07-15"
        add(a)
        assert len(open_units()) == 1, "add phải tạo 1 unknown mở"
        r = A(); r.file = "unknown-x.md"; r.id = "U-01"; r.value = "OAuth"; r.fixed = "spec x"; r.date = "2026-07-16"
        resolve(r)
        assert len(open_units()) == 0, "resolve phải đóng unknown"
        # audit: giá trị-đã-fill (email/pass) vẫn còn trong file
        assert "email/pass" in f.read_text(encoding="utf-8"), "phải giữ audit giá trị-đã-fill"
        print("self-test: PASS")
        return 0
    except AssertionError as e:
        print(f"self-test: FAIL — {e}"); return 1
    finally:
        DIR = old


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--add", action="store_true")
    ap.add_argument("--resolve", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--file"); ap.add_argument("--id"); ap.add_argument("--fr", default="")
    ap.add_argument("--source", default=""); ap.add_argument("--task", default="")
    ap.add_argument("--q", default=""); ap.add_argument("--default", default="")
    ap.add_argument("--verify", default=""); ap.add_argument("--risk", default="")
    ap.add_argument("--value", default=""); ap.add_argument("--fixed", default=""); ap.add_argument("--date", default="")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if a.add:
        add(a); sys.exit(0)
    if a.resolve:
        resolve(a); sys.exit(0)
    if a.trace:
        trace(a); sys.exit(0)
    sys.exit(report(as_json=a.json))


if __name__ == "__main__":
    main()
