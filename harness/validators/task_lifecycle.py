#!/usr/bin/env python3
"""task-lifecycle: Trụ 3 (Task Tracking) ép bằng CODE, không chỉ lời dặn trong skill.

GỐC: propose mint ID bền `T-YYMMDD-NN` + ghi state vào harness/metrics/tasks.json, các skill
(orca-workflow/verify-before-commit) chuyển proposed→approved→dispatched→done. Trước đây không
gì CHẶN khi agent né một bước hay trỏ task lạ → "STRONG nhưng soft". Validator này biến nó thành
chốt cứng ở fdk-gate.

Kiểm 2 bất biến (đọc tasks.json + frontmatter draft — KHÔNG đụng hash-chain Trụ 5):
  A. Lifecycle path  — mỗi task: history là chuỗi LIỀN MẠCH TIẾN từ `proposed`, mỗi bước +1 đúng
                       thứ tự proposed→approved→dispatched→done (không nhảy cóc, không lùi, không
                       trùng, không state lạ); và field `state` == state cuối của history.
                       → bắt: sửa lùi, fabricate, và né gate (proposed→done thẳng).
  B. No dangling ref — mọi draft wiki có `task: T-…` ở frontmatter phải trỏ task CÓ THẬT trong store.

Fail-OPEN đúng chỗ: không có tasks.json (feature chưa cài / install cũ) → exit 0, không vỡ.
CÓ tasks.json thì siết cứng: vi phạm → exit 2 (gate đỏ), lý do ra stderr.

Contract (giống validator khác — xem harness/recipe.md):
  - argv : task_lifecycle.py [--root DIR]   (mặc định root = ".")
  - exit 0 = pass, exit 2 = vi phạm.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ORDER = ["proposed", "approved", "dispatched", "done"]
IDX = {s: i for i, s in enumerate(ORDER)}

FRONTMATTER_RE = re.compile(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", re.DOTALL)
TASK_LINE_RE = re.compile(r"^task[ \t]*:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE)
TASK_ID_RE = re.compile(r"^T-\d{6}-\d{2,}$")


def _check_lifecycle(tasks: dict) -> list:
    """Bất biến A — mỗi task có history liền mạch tiến + state khớp đuôi."""
    errs = []
    for tid, t in tasks.items():
        hist = t.get("history") or []
        if not hist:
            errs.append(f"{tid}: history rỗng (mọi task phải có ít nhất 'proposed')")
            continue
        states = [h.get("state") for h in hist]
        # 'superseded' = terminal hợp lệ từ BẤT KỲ điểm nào của chuỗi (task bị thay thế
        # bởi task/issue khác — ngữ nghĩa docs-curate JOIN); phần trước nó vẫn phải liền mạch.
        chain = states[:-1] if states and states[-1] == "superseded" else states
        if not chain:
            errs.append(f"{tid}: 'superseded' phải đứng sau ít nhất 'proposed'")
            continue
        unknown = [s for s in chain if s not in IDX]
        if unknown:
            errs.append(f"{tid}: state lạ {unknown} (chỉ cho {ORDER} + terminal 'superseded')")
            continue
        idxs = [IDX[s] for s in chain]
        # phải là 0,1,2,…,k liền mạch tiến (bắt: lùi, nhảy cóc/né gate, trùng)
        if idxs != list(range(len(idxs))):
            errs.append(
                f"{tid}: lifecycle '{'→'.join(states)}' không liền-mạch-tiến "
                f"(phải đi đúng {'→'.join(ORDER[:len(idxs)])} không nhảy/lùi/trùng)"
            )
            continue
        # field state phải khớp đuôi history (bắt: store bị sửa state mà quên history)
        if t.get("state") != states[-1]:
            errs.append(f"{tid}: state='{t.get('state')}' lệch đuôi history '{states[-1]}'")
    return errs


def _check_refs(root: Path, tasks: dict) -> list:
    """Bất biến B — mọi `task:` ở frontmatter draft phải trỏ task có thật."""
    errs = []
    wiki = root / "llmwiki" / "wiki"
    if not wiki.is_dir():
        return errs
    for md in wiki.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except Exception:
            continue
        m = FRONTMATTER_RE.match(text)
        if not m:
            continue
        tm = TASK_LINE_RE.search(m.group(1))
        if not tm:
            continue
        ref = tm.group(1).strip().strip("\"'")
        if not TASK_ID_RE.match(ref):
            errs.append(f"{md.relative_to(root)}: task '{ref}' sai dạng (cần T-YYMMDD-NN)")
        elif ref not in tasks:
            errs.append(f"{md.relative_to(root)}: trỏ task lạ '{ref}' (không có trong tasks.json)")
    return errs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    store = root / "harness" / "metrics" / "tasks.json"
    if not store.is_file():
        print("[task-lifecycle] ✓ không có tasks.json (feature chưa dùng) — bỏ qua.")
        sys.exit(0)
    try:
        tasks = json.loads(store.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"[task-lifecycle] tasks.json hỏng, không parse được: {e}\n")
        sys.exit(2)
    if not isinstance(tasks, dict) or not tasks:
        print("[task-lifecycle] ✓ tasks.json rỗng — bỏ qua.")
        sys.exit(0)

    errs = _check_lifecycle(tasks) + _check_refs(root, tasks)
    if errs:
        sys.stderr.write("[task-lifecycle] LỆCH state-machine Trụ 3:\n")
        for e in errs:
            sys.stderr.write(f"  ✗ {e}\n")
        sys.stderr.write("  → sửa tasks.json / draft cho đúng vòng đời, hoặc dùng code-logger task để chuyển state.\n")
        sys.exit(2)
    print(f"[task-lifecycle] ✓ {len(tasks)} task đi đúng state-machine + không ref lạ.")
    sys.exit(0)


if __name__ == "__main__":
    main()
