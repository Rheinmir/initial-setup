#!/usr/bin/env python3
"""unknown — ledger cho UNKNOWN (chỗ mơ hồ làm 'think' rối) của một project bất kỳ.

KHÔNG phụ thuộc /br hay llmwiki — dùng cho MỌI project. Ledger là jsonl per-project,
keyed theo đường dẫn project, nằm ở `~/.claude/unknowns/<slug>.jsonl` (cạnh tầng memory,
để đi ké vòng chống-quên của memory — xem skill `/unknown`).

Vòng đời entry: open → clarified → resolved. Promote (cố ý) sang memory (pattern lặp)
hoặc wiki (quyết định dự án) khi đáng thành tri-thức.

DETERMINISTIC (build + selftest): add/list/resolve/promote/status trên jsonl. Không gọi model
(phần phỏng vấn làm rõ do skill/agent làm, tool chỉ giữ sổ).

Usage:
  unknown.py add "<mô tả unknown>" [--why "vì sao rối"] [--root .]
  unknown.py list [--all] [--root .]          # mặc định chỉ 'open'
  unknown.py resolve <id> --answer "<câu trả lời>" [--root .]
  unknown.py promote <id> --to memory|wiki [--root .]
  unknown.py status [--root .]                # đếm open + dòng chống-quên
  unknown.py selftest
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path


def _slug(root):
    return os.path.realpath(root).strip("/").replace("/", "-") or "root"


def _store(root):
    d = Path(os.path.expanduser("~/.claude/unknowns"))
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{_slug(root)}.jsonl"


def _load(root):
    p = _store(root)
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _save(root, rows):
    _store(root).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def _now():
    # Date.now bị cấm trong workflow nhưng đây là CLI thường — dùng time.time an toàn.
    return int(time.time())


def add(root, text, why, _ts=None):
    rows = _load(root)
    nid = (max([r["id"] for r in rows], default=0) + 1)
    rows.append({"id": nid, "text": text, "why": why or "", "status": "open",
                 "answer": "", "created": _ts if _ts is not None else _now(), "promoted": ""})
    _save(root, rows)
    return nid


def resolve(root, nid, answer):
    rows = _load(root)
    hit = next((r for r in rows if r["id"] == nid), None)
    if not hit:
        return False
    hit["status"] = "resolved"
    hit["answer"] = answer
    hit["resolved_at"] = _now()
    _save(root, rows)
    return True


def promote(root, nid, target):
    rows = _load(root)
    hit = next((r for r in rows if r["id"] == nid), None)
    if not hit:
        return False
    hit["promoted"] = target  # 'memory' | 'wiki' — agent ghi file đích, tool đánh dấu
    _save(root, rows)
    return True


def open_rows(root):
    return [r for r in _load(root) if r["status"] == "open"]


_SENT = "<!-- unknown-sync -->"


def sync_memory(root, mem_path):
    """Tự viết/gỡ MỘT dòng pointer 'còn N unknown' trong MEMORY.md (chống-quên đi ké recall
    memory). Idempotent: luôn xoá dòng managed cũ (theo sentinel) rồi thêm lại nếu còn open →
    không bao giờ trùng, tự biến mất khi giải hết. Trả số open."""
    n = len(open_rows(root))
    p = Path(mem_path)
    lines = p.read_text(encoding="utf-8").splitlines() if p.exists() else []
    lines = [ln for ln in lines if _SENT not in ln]          # gỡ dòng managed cũ
    if n:
        lines.append(f"- ⚠ {n} unknown chưa giải cho project này — `/unknown list` {_SENT}")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return n


def _autosync(root, mem):
    if mem:
        sync_memory(root, mem)
        print(f"  ↺ MEMORY.md đồng bộ: {mem}")


def cmd_add(root, text, why, mem):
    nid = add(root, text, why)
    print(f"  unknown #{nid} đã ghi (open) → {_store(root)}")
    print(f"  ⚠ còn {len(open_rows(root))} unknown OPEN — `/unknown list`")
    _autosync(root, mem)
    return 0


def cmd_sync(root, mem):
    n = sync_memory(root, mem)
    print(f"  MEMORY.md sync: {n} unknown open → {mem}" + (" (đã gỡ dòng — hết open)" if n == 0 else ""))
    return 0


def cmd_list(root, show_all):
    rows = _load(root) if show_all else open_rows(root)
    if not rows:
        print("  (không có unknown" + ("" if show_all else " open") + ")")
        return 0
    for r in rows:
        mark = {"open": "○", "clarified": "◐", "resolved": "●"}.get(r["status"], "?")
        line = f"  {mark} #{r['id']} [{r['status']}] {r['text']}"
        if r.get("promoted"):
            line += f"  → promoted:{r['promoted']}"
        print(line)
        if r.get("why"):
            print(f"       vì: {r['why']}")
        if r.get("answer"):
            print(f"       ✓ {r['answer']}")
    return 0


def cmd_resolve(root, nid, answer, mem):
    ok = resolve(root, nid, answer)
    print(f"  unknown #{nid} → resolved" if ok else f"  không thấy #{nid}")
    print(f"  còn {len(open_rows(root))} open")
    _autosync(root, mem)
    return 0 if ok else 1


def cmd_promote(root, nid, target):
    ok = promote(root, nid, target)
    if ok:
        print(f"  unknown #{nid} đánh dấu promoted:{target}. "
              f"→ agent GHI file đích: {'memory/<slug>.md + MEMORY.md pointer' if target=='memory' else 'wiki decision/ADR draft'}")
    else:
        print(f"  không thấy #{nid}")
    return 0 if ok else 1


def cmd_status(root):
    op = open_rows(root)
    print(f"  unknown ledger: {_store(root)}")
    print(f"  OPEN: {len(op)} · tổng: {len(_load(root))}")
    if op:
        print(f"  ⚠ CHỐNG-QUÊN: dán dòng này vào MEMORY.md để mỗi phiên thấy —")
        print(f"    \"- ⚠ {len(op)} unknown chưa giải cho project này — `/unknown list`\"")
    return 0


def selftest():
    import tempfile
    ok = True

    def chk(c, m):
        nonlocal ok
        if not c:
            ok = False
            print("  [FAIL]", m)

    with tempfile.TemporaryDirectory() as td:
        # cô lập HOME để không đụng ledger thật
        old = os.environ.get("HOME")
        os.environ["HOME"] = td
        try:
            root = td + "/proj"
            os.makedirs(root, exist_ok=True)
            chk(open_rows(root) == [], "ledger mới phải rỗng")
            i1 = add(root, "spec UI mơ hồ", "không rõ theme", _ts=100)
            i2 = add(root, "lưu ở đâu", "chưa rõ scope")
            chk(i1 == 1 and i2 == 2, f"id tăng dần: {i1},{i2}")
            chk(len(open_rows(root)) == 2, "2 open")
            chk(resolve(root, 1, "neumorphism"), "resolve #1")
            chk(len(open_rows(root)) == 1, "còn 1 open sau resolve")
            chk(not resolve(root, 99, "x"), "resolve id lạ = False")
            chk(promote(root, 1, "memory"), "promote #1")
            chk(next(r for r in _load(root) if r["id"] == 1)["promoted"] == "memory", "đánh dấu promoted")
            # bền qua load lại
            chk([r["text"] for r in _load(root)] == ["spec UI mơ hồ", "lưu ở đâu"], "persist đúng thứ tự")
            # slug per-project khác nhau
            chk(_slug("/a/b") != _slug("/a/c"), "slug phân biệt project")
            # sync_memory: idempotent + tự gỡ khi hết open
            mem = td + "/MEMORY.md"
            Path(mem).write_text("# Memory Index\n- [x](x.md) — cũ\n", encoding="utf-8")
            sync_memory(root, mem); sync_memory(root, mem)  # gọi 2 lần
            body = Path(mem).read_text()
            chk(body.count(_SENT) == 1, "sync idempotent — đúng 1 dòng managed")
            chk("1 unknown chưa giải" in body, f"đếm open đúng (còn #2 open): {body!r}")
            chk("- [x](x.md) — cũ" in body, "không đụng dòng memory sẵn có")
            resolve(root, 2, "xong"); sync_memory(root, mem)
            chk(_SENT not in Path(mem).read_text(), "hết open → tự gỡ dòng managed")
        finally:
            if old is not None:
                os.environ["HOME"] = old
    print("unknown self-test:", "ALL PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="unknown.py", description="Ledger unknown per-project (universal).")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("text"); a.add_argument("--why", default=""); a.add_argument("--root", default="."); a.add_argument("--memory", default="")
    a.set_defaults(func=lambda x: cmd_add(x.root, x.text, x.why, x.memory))
    li = sub.add_parser("list"); li.add_argument("--all", action="store_true"); li.add_argument("--root", default=".")
    li.set_defaults(func=lambda x: cmd_list(x.root, x.all))
    r = sub.add_parser("resolve"); r.add_argument("id", type=int); r.add_argument("--answer", required=True); r.add_argument("--root", default="."); r.add_argument("--memory", default="")
    r.set_defaults(func=lambda x: cmd_resolve(x.root, x.id, x.answer, x.memory))
    sm = sub.add_parser("sync-memory"); sm.add_argument("--memory", required=True); sm.add_argument("--root", default=".")
    sm.set_defaults(func=lambda x: cmd_sync(x.root, x.memory))
    pr = sub.add_parser("promote"); pr.add_argument("id", type=int); pr.add_argument("--to", required=True, choices=["memory", "wiki"]); pr.add_argument("--root", default=".")
    pr.set_defaults(func=lambda x: cmd_promote(x.root, x.id, x.to))
    st = sub.add_parser("status"); st.add_argument("--root", default="."); st.set_defaults(func=lambda x: cmd_status(x.root))
    t = sub.add_parser("selftest"); t.set_defaults(func=lambda x: selftest())
    return p


if __name__ == "__main__":
    _a = build_parser().parse_args()
    sys.exit(_a.func(_a))
