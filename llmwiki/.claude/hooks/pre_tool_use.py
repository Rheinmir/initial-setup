#!/usr/bin/env python3
"""L1/PreToolUse: chặn trước khi tool chạy. Exit 2 = block, stderr được đưa lại cho Claude.

Mỗi cú chặn cũng là một failure ĐÃ gán nhãn sẵn (taxonomy `spec-violation` = "ignored an
explicit rule") → ghi thẳng vào flywheel ledger. Tất định, 0 token, fail-open: capture không
còn chờ ai nhớ gõ `flywheel record`."""
import sys

import json
import os
import subprocess

from hooklib import find_validators, project_dir, read_payload, resolve_tool, run_validator

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def record_bite(root: str, rule: str, tool: str, target: str, err: str) -> None:
    """Rule cắn → 1 dòng ledger CỦA DỰ ÁN ĐÓ. Fail-open tuyệt đối: không thấy engine → no-op.
    resolve_tool = repo-local → global (~/.claude/harness): downstream chỉ có engine global,
    tự nối root/harness/scripts sẽ trượt và capture chết im (bắt được ở fresh-install)."""
    try:
        engine = resolve_tool(root, "harness/scripts/flywheel.py")
        if not engine:
            return
        sys.path.insert(0, os.path.dirname(engine))
        import flywheel
        flywheel.record(root, flywheel.KINDS["failure"], "spec-violation",
                        f"{rule} chặn {tool} {target}".strip(),
                        detail=(err or "").strip()[:300] or None)
    except Exception:
        pass


def run_local(root: str, event: dict, tool: str, target: str) -> None:
    """Chạy rule RIÊNG của dự án (harness-local/run.py) SONG SONG framework. Block (exit 2) nếu vi phạm.
    Fail-open: dự án không có harness-local/ hoặc lỗi → no-op (không đụng framework)."""
    runner = os.path.join(root, "harness-local", "run.py")
    if not os.path.isfile(runner):
        return
    try:
        r = subprocess.run([sys.executable, runner, "hook"], input=json.dumps(event),
                           capture_output=True, text=True, timeout=25)
    except Exception:
        return  # fail-open tuyệt đối
    if r.returncode == 2:
        err = r.stderr.strip()
        record_bite(root, "harness-local", tool, target, err)
        print(err, file=sys.stderr)
        sys.exit(2)


def main() -> None:
    payload = read_payload()
    tool = payload.get("tool_name", "")
    ti = payload.get("tool_input") or {}
    vdir = find_validators(project_dir(payload))
    if vdir is None:
        sys.exit(0)  # không tìm thấy validators → fail-open, còn L2 đỡ

    if tool in WRITE_TOOLS:
        event = {
            "action": "write",
            "file_path": ti.get("file_path", ""),
            "content": ti.get("content") or ti.get("new_string") or "",
        }
        checks = ["no_write_raw.py", "folder_structure.py", "patterns_guard.py"]
    elif tool == "Bash":
        event = {"action": "bash", "command": ti.get("command", "")}
        checks = ["no_write_raw.py", "patterns_guard.py"]
    else:
        sys.exit(0)

    root = project_dir(payload)
    target = event.get("file_path") or event.get("command", "")[:80]
    for name in checks:
        rc, err = run_validator(name, event, vdir)
        if rc == 2:
            record_bite(root, name[:-3] if name.endswith(".py") else name, tool, target, err)
            print(err, file=sys.stderr)
            sys.exit(2)
    run_local(root, event, tool, target)  # rule RIÊNG của dự án (harness-local) — sau framework
    sys.exit(0)


if __name__ == "__main__":
    main()
