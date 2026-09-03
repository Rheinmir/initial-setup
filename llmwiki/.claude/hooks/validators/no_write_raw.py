#!/usr/bin/env python3
"""R1 no-write-raw: agent không được ghi vào raw/.

Contract (mọi validator đều theo contract này — xem harness/recipe.md):
  - stdin JSON : {"action": "write"|"bash", "file_path": "...", "command": "..."}
  - argv files : no_write_raw.py path1 path2 ...
  - exit 0 = pass, exit 2 = vi phạm (lý do ghi ra stderr)
"""
import json
import re
import sys

RAW_PATH = re.compile(r"(^|/)raw/")
# Bash: redirect/tee/touch/sed -i theo sau bởi path bắt đầu bằng raw/ (hoặc .../raw/)
BASH_WRITE_TO_RAW = re.compile(
    r"(?:>>?|\btee\b(?:\s+-a)?|\btouch\b|\bsed\s+-i\S*)\s+['\"]?(?:\S*/)?raw/"
)
# cp/mv/rsync: chỉ chặn khi ĐÍCH (token cuối trước ; | & hoặc hết lệnh) nằm trong raw/
BASH_COPY_DEST_RAW = re.compile(
    r"\b(?:cp|mv|rsync)\b[^|;&]*\s['\"]?(?:\S*/)?raw/\S*['\"]?\s*(?:$|[|;&])"
)


def fail(reason: str) -> None:
    print(f"[R1 no-write-raw] {reason} — raw/ la inbox cua con nguoi, agent chi duoc doc.", file=sys.stderr)
    sys.exit(2)


def check_path(path: str) -> None:
    if RAW_PATH.search((path or "").replace("\\", "/")):
        fail(f"Chan ghi file vao raw/: {path}")


def main() -> None:
    args = sys.argv[1:]
    if args:  # file mode (pre-commit / CLI)
        for p in args:
            check_path(p)
        sys.exit(0)

    try:
        ev = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # payload hỏng → fail-open, L2 vẫn đỡ

    action = ev.get("action", "")
    if action == "write":
        check_path(ev.get("file_path", ""))
    elif action == "bash":
        cmd = ev.get("command", "") or ""
        if "raw/" in cmd and (BASH_WRITE_TO_RAW.search(cmd) or BASH_COPY_DEST_RAW.search(cmd)):
            fail(f"Chan lenh bash ghi vao raw/: {cmd[:120]}")
    sys.exit(0)


if __name__ == "__main__":
    main()
