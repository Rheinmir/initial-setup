#!/usr/bin/env python3
"""provenance-log — sổ sự kiện artifact-level, git-tracked, hash-chain THEO TỪNG writer_id.

Khác events.jsonl/scratch-log.jsonl/memory.jsonl/touches — xem llmwiki/wiki/concepts/log-model.md
để biết ranh giới. Sổ này CHỈ ghi sự kiện Ý NGHĨA artifact-level (code.change/docs.change/
decision.confirm/task.milestone), KHÔNG phải mọi tool-call. Adapter DUY NHẤT — mọi nơi khác
PHẢI gọi qua 3 hàm append_event/read_events/correlate, không chạm thẳng file (FR-007, chừa
slot migrate sang broker thật sau này chỉ bằng cách viết lại nội dung file này).

CLI:
    provenance-log.py record-changed [--root DIR]     # phân loại + ghi mọi file đổi (git status)
    provenance-log.py confirm-emit --id ID [--note TEXT] [--root DIR]  # T3 dùng nội bộ
    provenance-log.py --self-test
"""
from __future__ import annotations

import hashlib
import json
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

EVENTS_PATH_REL = "harness/metrics/provenance-log.jsonl"

# Đồng bộ tay với llmwiki/.claude/hooks/stop.py::_CODE_RE — hai file khác thư mục (hooks/ vs
# harness/scripts/), import chéo phức tạp hơn giá trị mang lại cho 1 regex; đổi 1 bên thì đổi
# luôn bên kia (cùng pattern đã chấp nhận ở medic.py's PROBE_MECH_MAP).
_CODE_RE = re.compile(r"\.(py|js|jsx|ts|tsx|mjs|cjs|go|rs|java|rb|php|c|h|cpp|cc|sh)$")


def _events_path(root) -> Path:
    return Path(root) / EVENTS_PATH_REL


def _canon(body: dict) -> str:
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _chain_hash(prev_h: str, body: dict) -> str:
    """Tái dùng nguyên thuật toán code-logger.py::_chain_hash (FR-003)."""
    return hashlib.sha256((str(prev_h) + "\n" + _canon(body)).encode("utf-8")).hexdigest()


def _last_hash_for_writer(path: Path, writer_id: str) -> str:
    """h của dòng CUỐI CÙNG thuộc writer_id này. 'genesis' nếu writer chưa ghi dòng nào."""
    last = None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rec = json.loads(ln)
                except Exception:
                    continue
                if rec.get("writer_id") == writer_id:
                    last = rec
    except FileNotFoundError:
        return "genesis"
    return (last.get("h") or "genesis") if last else "genesis"


def _writer_id() -> str:
    """<vendor>::<session_id>::<hostname> (FR-002) — không đăng ký tập trung (Assumptions).

    2026-07-24 (/fable5): biến MÔI TRƯỜNG THẬT của Claude Code là `CLAUDE_CODE_SESSION_ID`
    (xác nhận qua `env` thật trong hook context) — bản đầu đoán nhầm `CLAUDE_SESSION_ID`
    (không tồn tại), nên mọi event thật đều rơi vào 'unknown-session', vô hiệu hoá đúng phần
    FR-002 hứa phân biệt writer theo session. Self-test không bắt được vì nó tự set writer_id
    tay, không đi qua nhánh env thật này — bài học: test phải phủ CẢ đường lấy giá trị mặc định,
    không chỉ đường override tường minh."""
    import os
    session = (os.environ.get("CLAUDE_CODE_SESSION_ID")
               or os.environ.get("CLAUDE_SESSION_ID")
               or os.environ.get("SESSION_ID")
               or "unknown-session")
    vendor = os.environ.get("PROVENANCE_VENDOR", "claude-code")
    return f"{vendor}::{session}::{socket.gethostname()}"


def _git_sha(root) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=5)
        sha = out.stdout.strip()
        return sha if sha else "unknown"
    except Exception:
        return "unknown"


def append_event(root, topic: str, **fields) -> None:
    """Fail-open TUYỆT ĐỐI (FR-008) — never raise, never block caller."""
    try:
        root = Path(root)
        path = _events_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        writer_id = fields.pop("writer_id", None) or _writer_id()
        rec = {
            "writer_id": writer_id,
            "topic": topic,
            "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "git_sha": _git_sha(root),
        }
        rec.update({k: v for k, v in fields.items() if v is not None})
        with open(path, "a", encoding="utf-8") as f:
            try:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX)
            except Exception:
                pass
            rec["prev"] = _last_hash_for_writer(path, writer_id)
            rec["h"] = _chain_hash(rec["prev"], rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_events(root, writer_id: str = None, topic: str = None, ref: str = None) -> list:
    path = _events_path(root)
    out = []
    if not path.is_file():
        return out
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = json.loads(ln)
            except Exception:
                continue
            if writer_id and rec.get("writer_id") != writer_id:
                continue
            if topic and rec.get("topic") != topic:
                continue
            if ref and rec.get("ref") != ref:
                continue
            out.append(rec)
    return out


def _parse_ts(ts_utc: str) -> datetime:
    return datetime.strptime(ts_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def correlate(event_a: dict, event_b: dict, threshold_s: int = 600) -> dict:
    """FR-005: CHỈ temporal-proximity — 'hai sự kiện có cùng phiên/mạch công việc không'.
    KHÔNG phân tích nội dung/path để suy quan hệ ngữ nghĩa — đó là việc của
    wiki-graph.py::touches_targets (content-based, đã giải xong, xem log-model.md).
    related=True/False khi tín hiệu RÕ; related=None ('cần agent phán đoán') khi mơ hồ —
    caller (agent) tự dùng tool-use schema {is_related, confidence, reasoning} để quyết tiếp."""
    ts_a, ts_b = _parse_ts(event_a["ts_utc"]), _parse_ts(event_b["ts_utc"])
    delta = abs((ts_a - ts_b).total_seconds())
    same_writer = event_a.get("writer_id") == event_b.get("writer_id")
    same_task = bool(event_a.get("task_id")) and event_a.get("task_id") == event_b.get("task_id")
    if same_writer and delta <= threshold_s:
        return {"related": True, "reason": f"cùng writer_id, cách nhau {int(delta)}s <= ngưỡng {threshold_s}s"}
    if not same_writer and not same_task:
        return {"related": False, "reason": "khác writer_id, khác task_id — không có tín hiệu liên quan"}
    return {"related": None,
            "reason": "cần agent phán đoán — tín hiệu thời gian không đủ rõ ràng (tool-use schema {is_related, confidence, reasoning})",
            "delta_s": delta, "same_writer": same_writer, "same_task": same_task}


def classify_topic(path: str):
    """'docs.change' CHỈ khi path nằm trong llmwiki/wiki/ (wiki thật) VÀ đuôi .md — theo PREFIX,
    không theo đuôi file (SKILL.md/README.md/*-PLAN.md không phải wiki dù cùng đuôi .md).
    'code.change' nếu khớp _CODE_RE và KHÔNG phải wiki. None nếu không thuộc loại nào."""
    p = path.replace("\\", "/").lstrip("./")
    if p.startswith("llmwiki/wiki/") and p.endswith(".md"):
        return "docs.change"
    # _CODE_RE (mượn từ stop.py) cố ý KHÔNG chứa .md (stop.py xử lý .md riêng cho wiki-content
    # check). Ở đây .md NGOÀI llmwiki/wiki/ (SKILL.md/README.md/*-PLAN.md) vẫn phải phân loại —
    # chúng là cấu hình/lệnh cho agent, gần "code" hơn "wiki quyết định", nên rơi vào code.change.
    if _CODE_RE.search(p) or p.endswith(".md"):
        return "code.change"
    return None


def _changed_paths(root) -> list:
    out = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                          capture_output=True, text=True, timeout=8).stdout
    paths = []
    for ln in out.splitlines():
        if len(ln) < 4:
            continue
        p = ln[3:].strip()
        if " -> " in p:  # rename: lấy path MỚI
            p = p.split(" -> ", 1)[1]
        paths.append(p.strip('"'))
    return paths


def record_changed(root) -> int:
    n = 0
    for p in _changed_paths(root):
        topic = classify_topic(p)
        if topic:
            append_event(root, topic, path=p)
            n += 1
    return n


def ck(name, cond, fails):
    print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
    if not cond:
        fails.append(name)


def self_test() -> int:
    import shutil as sh
    import subprocess as sp
    import tempfile

    fails = []

    # --- Task 1: append_event/read_events, hash-chain theo writer ---
    td = Path(tempfile.mkdtemp())
    (td / "harness" / "metrics").mkdir(parents=True)
    sp.run(["git", "init", "-q"], cwd=td)
    sp.run(["git", "config", "user.email", "t@t.t"], cwd=td)
    sp.run(["git", "config", "user.name", "t"], cwd=td)
    (td / "f.txt").write_text("x")
    sp.run(["git", "add", "-A"], cwd=td)
    sp.run(["git", "commit", "-q", "-m", "init"], cwd=td)

    append_event(td, "code.change", writer_id="w1", path="f.txt")
    events = read_events(td, writer_id="w1")
    ck("append_event ghi đúng 1 dòng, đọc lại được", len(events) == 1, fails)
    ck("event mang ts_utc dạng ISO8601 kết thúc 'Z'", events[0]["ts_utc"].endswith("Z"), fails)
    ck("event mang git_sha thật (không phải 'unknown')", len(events[0]["git_sha"]) == 40, fails)
    ck("mắt xích đầu tiên của writer -> prev='genesis'", events[0]["prev"] == "genesis", fails)

    append_event(td, "code.change", writer_id="w1", path="g.txt")
    e2 = read_events(td, writer_id="w1")
    ck("mắt xích thứ 2 cùng writer -> prev = h của mắt xích 1", e2[1]["prev"] == e2[0]["h"], fails)

    append_event(td, "code.change", writer_id="w2", path="h.txt")
    e_w2 = read_events(td, writer_id="w2")
    ck("writer KHÁC -> chuỗi riêng, prev='genesis' (không lẫn với w1)", e_w2[0]["prev"] == "genesis", fails)

    # SC-005: fail-open thật khi ghi lỗi
    bad_root = Path("/proc/nonexistent-root-xyz")
    try:
        append_event(bad_root, "code.change", writer_id="w1", path="x")
        ck("SC-005: ghi vào root hỏng không raise (fail-open thật)", True, fails)
    except Exception as e:
        ck(f"SC-005: fail-open THẤT BẠI — lộ exception {type(e).__name__}", False, fails)

    # --- Task 2: SC-001 — merge=union thật trên sandbox git 2 branch ---
    td2 = Path(tempfile.mkdtemp())
    sp.run(["git", "init", "-q"], cwd=td2)
    sp.run(["git", "config", "user.email", "t@t.t"], cwd=td2)
    sp.run(["git", "config", "user.name", "t"], cwd=td2)
    (td2 / ".gitattributes").write_text(f"{EVENTS_PATH_REL} merge=union\n")
    (td2 / "harness" / "metrics").mkdir(parents=True)
    (td2 / EVENTS_PATH_REL).write_text("")
    sp.run(["git", "add", "-A"], cwd=td2)
    sp.run(["git", "commit", "-q", "-m", "init"], cwd=td2)

    sp.run(["git", "checkout", "-q", "-b", "branch-a"], cwd=td2)
    append_event(td2, "code.change", writer_id="session-a", path="a.py")
    sp.run(["git", "add", "-A"], cwd=td2)
    sp.run(["git", "commit", "-q", "-m", "event a"], cwd=td2)

    sp.run(["git", "checkout", "-q", "-"], cwd=td2)
    append_event(td2, "code.change", writer_id="session-b", path="b.py")
    sp.run(["git", "add", "-A"], cwd=td2)
    sp.run(["git", "commit", "-q", "-m", "event b"], cwd=td2)

    merge_out = sp.run(["git", "merge", "branch-a", "--no-edit"], cwd=td2, capture_output=True, text=True)
    ck("SC-001: git merge không lỗi", merge_out.returncode == 0, fails)
    merged = read_events(td2)
    ck("SC-001: merge xong ĐỦ 2 sự kiện của cả 2 nhánh, không mất dòng",
       len(merged) == 2 and {e["writer_id"] for e in merged} == {"session-a", "session-b"}, fails)

    # --- Task 4: FR-005/SC-003 — correlate() CHỈ temporal, không suy nội dung ---
    ea = {"writer_id": "w1", "ts_utc": "2026-07-22T01:00:00Z"}
    eb_close = {"writer_id": "w1", "ts_utc": "2026-07-22T01:05:00Z"}
    eb_far_diff_writer = {"writer_id": "w2", "ts_utc": "2026-07-22T10:00:00Z"}
    eb_ambiguous = {"writer_id": "w2", "ts_utc": "2026-07-22T01:03:00Z", "task_id": "T-1"}
    ea_task = {**ea, "task_id": "T-1"}

    r1 = correlate(ea, eb_close)
    ck("SC-003: cùng writer, trong ngưỡng 10' -> related=True", r1["related"] is True, fails)

    r2 = correlate(ea, eb_far_diff_writer)
    ck("SC-003: khác writer, khác task, cách xa -> related=False (không đề xuất sai)",
       r2["related"] is False, fails)

    r3 = correlate(ea_task, eb_ambiguous)
    ck("FR-005: khác writer nhưng cùng task_id, ngoài ngưỡng -> None (cần agent phán đoán)",
       r3["related"] is None and "agent" in r3["reason"], fails)

    # --- Task 5: FR-001 — classify_topic() theo PATH PREFIX, không theo đuôi file ---
    ck("wiki thật (llmwiki/wiki/*.md) -> docs.change",
       classify_topic("llmwiki/wiki/concepts/decision-anchoring.md") == "docs.change", fails)
    ck("SKILL.md KHÔNG phải wiki (dù cùng đuôi .md) -> code.change, không phải docs.change",
       classify_topic("skills/fdk-uat/SKILL.md") == "code.change", fails)
    ck("README.md ở gốc repo -> code.change (không thuộc llmwiki/wiki/)",
       classify_topic("README.md") == "code.change", fails)
    ck("file .py bất kỳ -> code.change", classify_topic("harness/scripts/foo.py") == "code.change", fails)
    ck("file .json (không khớp _CODE_RE, không phải wiki) -> None (không ghi)",
       classify_topic("harness/metrics/tasks.json") is None, fails)

    # --- /fable5 2026-07-24: _writer_id() PHẢI đọc đúng biến môi trường THẬT của Claude Code
    # (CLAUDE_CODE_SESSION_ID), không phải qua writer_id override tay như mọi case trên — bài
    # học: bản đầu đoán nhầm tên biến, self-test không bắt được vì luôn override thủ công. ---
    import os as _os_env
    _saved = _os_env.environ.get("CLAUDE_CODE_SESSION_ID")
    _os_env.environ["CLAUDE_CODE_SESSION_ID"] = "test-session-xyz"
    try:
        wid = _writer_id()
        ck("_writer_id() đọc đúng CLAUDE_CODE_SESSION_ID (không rơi về 'unknown-session')",
           "test-session-xyz" in wid, fails)
    finally:
        if _saved is None:
            _os_env.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        else:
            _os_env.environ["CLAUDE_CODE_SESSION_ID"] = _saved

    sh.rmtree(td, ignore_errors=True)
    sh.rmtree(td2, ignore_errors=True)

    print(f"\nSELF-TEST: {'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


def main():
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="provenance-log — artifact event ledger")
    sub = ap.add_subparsers(dest="cmd")
    p_rc = sub.add_parser("record-changed")
    p_rc.add_argument("--root", default=".")
    p_confirm = sub.add_parser("confirm-emit")
    p_confirm.add_argument("--id", required=True)
    p_confirm.add_argument("--note", default=None)
    p_confirm.add_argument("--root", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if args.cmd == "confirm-emit":
        append_event(Path(args.root), "decision.confirm", ref=args.id, note=args.note)
        sys.exit(0)
    if args.cmd == "record-changed":
        n = record_changed(Path(args.root))
        print(f"· ghi {n} sự kiện")
        sys.exit(0)
    ap.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
