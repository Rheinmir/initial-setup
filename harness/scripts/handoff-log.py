#!/usr/bin/env python3
"""handoff-log — sổ BÀN GIAO giữa các node, đi theo git.

Lỗ nó bịt (đo 2026-09-04): state bàn giao đang bay — run · message · inbox · reply · task DAG —
sống trong runtime Orca, KHÔNG có bản nào phía repo. Quét `harness/metrics/` cho
`orchestr|run|inbox|message` ra 0 file. Hệ quả đo được:

  · Đổi máy / Orca restart là mất chuỗi. Phiên sau đọc được "đã xong chưa" (dispatch-verify)
    nhưng không dựng lại được "đang bàn giao tới đâu, node nào đang cầm gì".
  · Không probe nào kiểm state đang bay: 9/12 file state có cổng chứng minh còn đúng,
    state orchestration có 0 — vì nó nằm ngoài tầm với của medic.

Ta ĐÃ có hậu kiểm chắc (dispatch-verify đối chiếu lời hứa với đĩa, orca-dispatch dùng sentinel
`__ORCA_DONE__<id>:$?`, trace-grader chấm đường đi). Nhưng hậu kiểm chỉ nói "không xong" —
không nói "đứt ở đâu, đang cầm gì". Sổ này giữ đúng khúc giữa đó.

BỐ CỤC BÁM ORCA, KHÔNG TỰ CHẾ. Đọc từ OBJECT THẬT (`run-list --json`, `inbox --json`):
  run:     id · objective · coordinator_handle · coordinator_pane_key · consumer_generation
           · created_at · updated_at
  message: id · run_id · sequence · created_at · delivered_at · read · from_handle
           · to_handle · sender_pane_key · subject · body · type · priority · thread_id
           · payload · delivery_contract   (+ cờ gửi: task_id · dispatch_id · outcome
           · files_modified · report_path · phase · retry_request)
Sổ dùng ĐÚNG những tên đó, cộng hai trường neo vào code-state (`git_sha`, `branch`) — cùng
quy ước `agent-trace.jsonl` đã dùng. Không đặt tên mới cho thứ Orca đã đặt tên.

Vì sao append-only JSONL chứ không phải một file trạng-thái-hiện-tại: bàn giao là CHUỖI
SỰ KIỆN. Một file "trạng thái hiện tại" trả lời được "đang ở đâu" nhưng mất "đã đi qua đâu",
mà câu thứ hai mới là câu người ta hỏi khi một mắt xích đứt.

CLI:
  handoff-log.py record --run <id> --from <h> --to <h> --subject <s> [--task-id …] […]
  handoff-log.py sync                 # kéo message từ runtime Orca vào sổ (dedupe theo id)
  handoff-log.py show --run <id>      # dựng lại chuỗi bàn giao của một run
  handoff-log.py runs                 # các run có trong sổ + mốc cuối
  handoff-log.py --check              # probe: sổ có nói dối không (files_modified/report_path)
  handoff-log.py --self-test

Exit: 0 sạch · 1 sổ khai sai (probe đỏ) · 2 lỗi cách dùng.
Fail-open khi GHI (không bao giờ làm gãy phiên), fail-closed khi KIỂM.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_REL = "harness/metrics/handoff-log.jsonl"

# Tên trường lấy NGUYÊN của Orca — đổi ở đây là lệch khỏi runtime, đừng đổi tuỳ tiện.
# Bản đầu lấy danh sách này từ `send --help` (tức các CỜ GỬI) nên mất `created_at`,
# `sequence`, `delivered_at` — những trường chỉ có trên OBJECT trả về. Hậu quả đã đo:
# chuỗi bàn giao dựng lại theo thứ tự SYNC chứ không theo thứ tự THẬT. Nay lấy từ object.
ORCA_FIELDS = ("id", "run_id", "sequence", "created_at", "delivered_at", "read",
               "from_handle", "to_handle", "sender_pane_key", "subject", "body", "type",
               "priority", "thread_id", "payload", "delivery_contract",
               "task_id", "dispatch_id", "outcome",
               "files_modified", "report_path", "phase", "retry_request")
# Khoá sắp xếp chuỗi: `sequence` là khoá thứ tự CỦA CHÍNH ORCA — tin nó trước, rồi mới tới
# thời điểm tạo, cuối cùng mới tới lúc ta ghi sổ (chỉ đúng cho mốc do ta tự record).
def _order_key(r: dict):
    seq = r.get("sequence")
    return (0, seq) if isinstance(seq, int) else (1, r.get("created_at") or r.get("ts") or "")
# Hai trường của ta: neo mốc bàn giao vào trạng thái code lúc đó.
LOCAL_FIELDS = ("ts", "git_sha", "branch")
OUTCOMES = ("succeeded", "failed", "in_flight")


def log_path(root: Path = ROOT) -> Path:
    return root / LOG_REL


def _git(root: Path, *args) -> str:
    try:
        r = subprocess.run(["git", "-C", str(root), *args],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def read_rows(root: Path = ROOT) -> list:
    p = log_path(root)
    if not p.is_file():
        return []
    out = []
    for line in p.open(encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue          # dòng hỏng không được làm chết cả sổ
    return out


def append(row: dict, root: Path = ROOT) -> bool:
    """Ghi một mốc. Fail-open: lỗi ghi KHÔNG bao giờ làm gãy phiên đang chạy."""
    try:
        row.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
        row.setdefault("git_sha", _git(root, "rev-parse", "--short", "HEAD"))
        row.setdefault("branch", _git(root, "rev-parse", "--abbrev-ref", "HEAD"))
        p = log_path(root)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return True
    except Exception:  # noqa: BLE001
        return False


def sync_from_orca(root: Path = ROOT) -> tuple:
    """Kéo message từ runtime Orca vào sổ, dedupe theo `id`.

    Đây là cây cầu một chiều runtime → repo. KHÔNG đẩy ngược: runtime là nguồn chân lý của
    việc đang chạy, sổ là bản sao đi-theo-git để phiên sau (hoặc máy khác) dựng lại chuỗi.
    """
    have = {r.get("id") for r in read_rows(root) if r.get("id")}
    try:
        r = subprocess.run(["orca", "orchestration", "inbox", "--json"],
                           capture_output=True, text=True, timeout=30)
        msgs = (json.loads(r.stdout).get("result") or {}).get("messages") or []
    except Exception as e:  # noqa: BLE001
        return 0, f"BỎ QUA: không đọc được runtime Orca ({str(e)[:60]})"
    n = 0
    for m in msgs:
        if m.get("id") in have:
            continue
        append({k: m[k] for k in ORCA_FIELDS if k in m} | {"source": "orca-inbox"}, root)
        n += 1
    return n, f"đồng bộ {n} mốc mới ({len(msgs)} message trong inbox)"


def check(root: Path = ROOT) -> list:
    """Probe: sổ có NÓI DỐI không.

    Cùng nguyên lý claim-receipts và neo `data-src`: đã KHAI thì phải đúng. Một mốc khai
    `files_modified` hoặc `report_path` mà đường dẫn không tồn tại nghĩa là chuỗi bàn giao
    đang kể một câu chuyện không kiểm chứng được — tệ hơn không ghi gì.
    Không khai thì không bị hỏi (fail-closed có phạm vi).
    """
    problems = []
    for r in read_rows(root):
        rid = r.get("id") or r.get("ts") or "?"
        oc = r.get("outcome")
        if oc and oc not in OUTCOMES:
            problems.append(f"{rid}: outcome lạ {oc!r} (hợp lệ: {', '.join(OUTCOMES)})")
        fm = r.get("files_modified") or ""
        files = [x.strip() for x in (fm.split(",") if isinstance(fm, str) else fm) if x and x.strip()]
        for f in files:
            if not (root / f).exists():
                problems.append(f"{rid}: khai sửa `{f}` nhưng file KHÔNG tồn tại")
        rp = r.get("report_path")
        if rp and not (root / rp).exists() and not Path(rp).exists():
            problems.append(f"{rid}: report_path `{rp}` không resolve")
    return problems


def show_run(run_id: str, root: Path = ROOT) -> list:
    rows = [r for r in read_rows(root) if r.get("run_id") == run_id]
    return sorted(rows, key=_order_key)


def runs_summary(root: Path = ROOT) -> dict:
    agg: dict = {}
    for r in read_rows(root):
        rid = r.get("run_id") or "(không run_id)"
        a = agg.setdefault(rid, {"n": 0, "last_ts": "", "last_phase": "", "outcomes": set()})
        a["n"] += 1
        when = r.get("created_at") or r.get("ts") or ""
        if when >= a["last_ts"]:
            a["last_ts"] = when
            a["last_phase"] = r.get("phase") or r.get("subject") or ""
        if r.get("outcome"):
            a["outcomes"].add(r["outcome"])
    return agg


def self_test() -> int:
    import tempfile
    ok = True

    def ck(label, cond):
        nonlocal ok
        print(f"  {'✓' if cond else '✗'} {label}")
        ok = ok and cond

    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "harness" / "metrics").mkdir(parents=True)
        (root / "thuc-te-co-that.py").write_text("x", encoding="utf-8")

        append({"id": "m1", "run_id": "run_x", "from_handle": "a", "to_handle": "b",
                "subject": "giao việc", "phase": "dispatch", "outcome": "in_flight"}, root)
        append({"id": "m2", "run_id": "run_x", "from_handle": "b", "to_handle": "a",
                "subject": "xong", "phase": "worker_done", "outcome": "succeeded",
                "files_modified": "thuc-te-co-that.py"}, root)
        ck("ghi rồi đọc lại được 2 mốc", len(read_rows(root)) == 2)
        ck("dựng lại được chuỗi theo run_id", [r["id"] for r in show_run("run_x", root)] == ["m1", "m2"])
        ck("mốc tự neo git_sha + branch", all("git_sha" in r and "branch" in r for r in read_rows(root)))
        ck("sổ khai đúng → probe SẠCH", check(root) == [])

        # Khai sửa một file KHÔNG tồn tại → probe phải bắt. Đây là lý do sổ này là STATE
        # chứ không phải log: có người kiểm nó.
        append({"id": "m3", "run_id": "run_x", "subject": "khai láo",
                "files_modified": "khong-he-co-file-nay.py"}, root)
        ck("khai sửa file KHÔNG tồn tại → probe ĐỎ",
           any("KHÔNG tồn tại" in p for p in check(root)))
        append({"id": "m4", "run_id": "run_x", "subject": "outcome lạ", "outcome": "maybe"}, root)
        ck("outcome ngoài từ điển → probe ĐỎ", any("outcome lạ" in p for p in check(root)))
        # Sổ append-only sẽ gặp dòng hỏng (ghi đứt giữa chừng, hai tiến trình cùng ghi).
        # Một dòng hỏng KHÔNG được làm mất 4 mốc còn lại.
        with log_path(root).open("a", encoding="utf-8") as f:
            f.write("{dòng hỏng không phải JSON\n")
        ck("dòng JSON hỏng bị bỏ qua, 4 mốc còn lại vẫn đọc được",
           len(read_rows(root)) == 4)

    print("self-test: PASS" if ok else "self-test: FAIL")
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="sổ bàn giao giữa các node, đi theo git")
    ap.add_argument("cmd", nargs="?", choices=["record", "sync", "show", "runs"])
    ap.add_argument("--root", default=str(ROOT))
    for f in ORCA_FIELDS:
        ap.add_argument(f"--{f.replace('_', '-')}")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    root = Path(a.root).resolve()

    if a.check:
        problems = check(root)
        if problems:
            print(f"  \033[1;31m✗\033[0m sổ bàn giao khai SAI ({len(problems)}):")
            for p in problems[:12]:
                print(f"      {p}")
            sys.exit(1)
        print(f"  \033[1;32m✓\033[0m {len(read_rows(root))} mốc bàn giao, mọi khai báo đều resolve")
        sys.exit(0)

    if a.cmd == "record":
        row = {f: getattr(a, f) for f in ORCA_FIELDS if getattr(a, f, None)}
        if not row.get("run_id"):
            print("record: cần --run-id", file=sys.stderr)
            sys.exit(2)
        ok = append(row, root)
        print(("✓ ghi mốc " if ok else "· bỏ qua (ghi lỗi, fail-open) ") + str(row.get("id") or row.get("subject", ""))[:60])
        sys.exit(0)

    if a.cmd == "sync":
        n, msg = sync_from_orca(root)
        print(f"  {msg}")
        sys.exit(0)

    if a.cmd == "show":
        if not a.run_id:
            print("show: cần --run-id", file=sys.stderr)
            sys.exit(2)
        rows = show_run(a.run_id, root)
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            sys.exit(0)
        print(f"  chuỗi bàn giao của {a.run_id} — {len(rows)} mốc")
        for r in rows:
            print(f"    {(r.get('created_at') or r.get('ts') or '')[:19]}  {str(r.get('from_handle',''))[:14]:<14} → "
                  f"{str(r.get('to_handle',''))[:14]:<14} [{r.get('phase') or r.get('type') or '-'}] "
                  f"{r.get('outcome') or ''} {str(r.get('subject',''))[:44]}")
        sys.exit(0)

    agg = runs_summary(root)
    if not agg:
        print("  sổ bàn giao trống — chạy `handoff-log.py sync` để kéo từ runtime Orca")
        sys.exit(0)
    print(f"  {len(agg)} run trong sổ:")
    for rid, v in sorted(agg.items(), key=lambda x: x[1]["last_ts"], reverse=True):
        print(f"    {rid:<22} {v['n']:>3} mốc · cuối {v['last_ts'][:19]} · "
              f"{','.join(sorted(v['outcomes'])) or 'in_flight'} · {v['last_phase'][:40]}")
    sys.exit(0)


if __name__ == "__main__":
    main()
