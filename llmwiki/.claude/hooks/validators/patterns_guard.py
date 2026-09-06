#!/usr/bin/env python3
"""R14 patterns-protected: kho pattern tham chiếu (llmwiki/patterns/) chỉ được sửa KHI user cho phép.

"raw/ nhưng thấp hơn một bậc": raw/ = không bao giờ ghi (R1); patterns/ = chỉ ghi khi user
mở khoá (đặt env LLMWIKI_PATTERNS_UNLOCK=1). Vô tình (agent tự ý) Write/Edit/bash-ghi vào
protected_dir → CHẶN. Có unlock → cho qua. Fail-safe: thà chặn nhầm còn hơn sửa nhầm kho tham chiếu.

Contract (mọi validator):
  - stdin JSON : {"action":"write"|"bash","file_path":"...","command":"..."}
  - argv files : patterns_guard.py path1 path2 ...
  - exit 0 = pass · exit 2 = chặn (lý do ra stderr) · lỗi bất ngờ → fail-open (exit 0)

Adapter (build-now-adapt-later): harness/pattern-library.config.yaml (protected_dir, unlock_env;
flagged verified=false). Fallback nếu vắng config: llmwiki/patterns + LLMWIKI_PATTERNS_UNLOCK.
"""
import json
import os
import re
import sys

_DEFAULTS = {"protected_dir": "llmwiki/patterns", "unlock_env": "LLMWIKI_PATTERNS_UNLOCK"}


def _load_cfg():
    cfg = dict(_DEFAULTS)
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    for cand in (os.path.join(root, "harness", "pattern-library.config.yaml"),
                 os.path.join(os.path.dirname(__file__), "..", "pattern-library.config.yaml")):
        try:
            import yaml
            data = yaml.safe_load(open(cand, encoding="utf-8"))
            if isinstance(data, dict):
                for k in ("protected_dir", "unlock_env"):
                    if data.get(k):
                        cfg[k] = data[k]
                break
        except Exception:
            continue
    return cfg


def _unlocked(cfg) -> bool:
    return str(os.environ.get(cfg["unlock_env"], "")).strip() in ("1", "true", "yes", "on")


def _in_protected(path: str, protected_dir: str) -> bool:
    # `\.?`: dự án downstream cài vào .llmwiki/ (layout dot) — protected_dir mặc định là
    # "llmwiki/patterns" nên thiếu nó thì ".llmwiki/patterns/x" trượt và R14 chết (GH#112 audit).
    return bool(re.search(r"(^|/)\.?" + re.escape(protected_dir) + r"/", (path or "").replace("\\", "/")))


def main() -> None:
    cfg = _load_cfg()
    pdir = cfg["protected_dir"]
    unlocked = _unlocked(cfg)

    def fail(what: str) -> None:
        env = cfg["unlock_env"]
        print(f"[R14 patterns-protected] {what} — kho pattern '{pdir}/' chỉ sửa khi user cho phép. "
              f"Mở khoá: đặt env {env}=1 rồi thử lại (đừng tự ý sửa kho tham chiếu).", file=sys.stderr)
        sys.exit(2)

    args = sys.argv[1:]
    if args:  # file mode (pre-commit / CLI)
        if not unlocked:
            for p in args:
                if _in_protected(p, pdir):
                    fail(f"Chặn ghi vào kho pattern: {p}")
        sys.exit(0)

    try:
        ev = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # payload hỏng → fail-open
    if unlocked:
        sys.exit(0)  # user đã cho phép

    action = ev.get("action", "")
    if action == "write":
        if _in_protected(ev.get("file_path", ""), pdir):
            fail(f"Chặn ghi vào kho pattern: {ev.get('file_path')}")
    elif action == "bash":
        cmd = ev.get("command", "") or ""
        seg = pdir.split("/")[-1] + "/"          # vd 'patterns/'
        if seg in cmd and re.search(
                r"(?:>>?|\btee\b(?:\s+-a)?|\btouch\b|\bsed\s+-i\S*|\b(?:cp|mv|rsync)\b)[^|;&]*" + re.escape(pdir),
                cmd):
            fail(f"Chặn lệnh bash ghi vào kho pattern: {cmd[:120]}")
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # fail-open tuyệt đối
