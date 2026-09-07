#!/usr/bin/env python3
"""L1/UserPromptSubmit: R10 docs-gate — harness quản lý nhịp TÀI LIỆU + ĐÁNH GIÁ.

Cứ mỗi N prompt (mặc định 5), soi N request gần nhất xem 2 trụ có đang được duy trì:
  • TÀI LIỆU — đã dùng `/docs-site-macos` hoặc `/orca-workflow` chưa?
  • ĐÁNH GIÁ/eval — đã đụng `wikieval` / `trace-grader` / `council` chưa?
Trụ nào THIẾU → inject directive vào context prompt đó: hỏi user có muốn bổ sung
trụ đó cho N prompt vừa rồi không (docs → skill `docs-site-macos`; eval → skill
`wikieval`). Cả hai đang được duy trì → im lặng (mục tiêu đã đạt).

Fail-open tuyệt đối: lỗi gì cũng exit 0, không bao giờ chặn prompt của user.
Đếm bằng state file (.claude/audit/.docs-gate.json) — bằng máy, không nhờ model nhớ.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from hooklib import audit, find_wiki_dir, project_dir, read_payload, resolve_tool

EVERY = int(os.environ.get("LLMWIKI_DOCS_GATE_EVERY", "5") or "5")
REPORT_EVERY = int(os.environ.get("OVERSTACK_SELF_REPORT_EVERY", "50") or "50")   # tự chấm hệ mỗi N lượt
DOCS_TOKENS = ("docs-site-macos", "orca-workflow")           # trụ TÀI LIỆU đang được duy trì?
EVAL_TOKENS = ("wikieval", "trace-grader", "council")        # trụ ĐÁNH GIÁ/eval có được đụng tới?


def load_count(state: Path, sid: str) -> int:
    try:
        data = json.loads(state.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    return int(data.get(sid, 0)) if isinstance(data, dict) else 0


def save_count(state: Path, sid: str, n: int) -> None:
    try:
        data = json.loads(state.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    data[sid] = n
    state.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def last_user_texts(transcript_path: str, k: int):
    """Lấy text của k user-message gần nhất từ transcript jsonl."""
    texts = []
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return texts
    for line in lines:
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("type") != "user":
            continue
        msg = rec.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        texts.append(json.dumps(content, ensure_ascii=False) if content is not None else "")
    return texts[-k:]


def emit(msg: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": msg,
    }}, ensure_ascii=False))


def build_gate(n: int, every: int, need_docs: bool, need_eval: bool) -> str:
    miss = ([] if not need_docs else ["**tài liệu**"]) + ([] if not need_eval else ["**đánh giá/eval**"])
    lines = [
        f"⟳ [docs-gate R10] Đã {n} prompt; {every} request gần nhất thiếu: {', '.join(miss)} → trụ này đang tụt lại.",
        "HÀNH ĐỘNG (harness yêu cầu — HỎI user TRƯỚC khi chạy nặng):",
    ]
    step = 1
    if need_docs:
        lines.append(
            f"{step}. Hỏi user: \"Có muốn bổ sung TÀI LIỆU cho {every} prompt vừa rồi không?\" → nếu ĐỒNG Ý, "
            "dispatch doc-agent dùng skill `docs-site-macos` (CLI: opencode → agy → claude; subagent không "
            "gọi được opencode → `/orchestration` dispatch opencode chạy skill `docs-site-macos`)."
        )
        step += 1
    if need_eval:
        lines.append(
            f"{step}. Hỏi user: \"Có muốn bổ sung ĐÁNH GIÁ/eval cho {every} prompt vừa rồi không?\" → nếu ĐỒNG Ý, "
            "dùng skill `wikieval` (eval hồi quy từ wiki goldens) thêm/chạy case cho phần vừa làm; nếu là output "
            "của agent thì chấm bằng `trace-grader`/`council`."
        )
        step += 1
    lines.append(f"{step}. Nếu TỪ CHỐI → bỏ qua, không hỏi lại cho tới mốc prompt kế tiếp.")
    return "\n".join(lines)


def main() -> None:
    payload = read_payload()
    audit(payload, "UserPromptSubmit")

    root = Path(project_dir(payload))
    if find_wiki_dir(str(root)) is None:
        sys.exit(0)  # không phải project llmwiki → bỏ qua

    sid = payload.get("session_id") or "default"

    # Trần token-budget → "continue in new session" TỰ ĐỘNG (session-continue.py). Chạy TRƯỚC docs-gate:
    # vượt/sắp vượt trần thì prompt này bị chặn, bàn giao đã ghi + phiên mới đã mở — tiếp ở đó.
    # Trước đây `check` của token-budget không hook nào gọi → mode:block là một chữ trong file.
    sc = resolve_tool(str(root), "harness/scripts/session-continue.py")
    if sc:
        try:
            p = subprocess.run([sys.executable, sc, "run", sid, "--root", str(root),
                                "--transcript", payload.get("transcript_path", "") or "",
                                "--prompt", payload.get("prompt", "") or ""],
                               cwd=str(root), capture_output=True, text=True, timeout=150)
            if p.returncode == 2:
                sys.stdout.write(p.stdout)      # OpenClaude: {"decision":"block"} · Claude Code: exit 2 + stderr
                sys.stderr.write(p.stderr)
                sys.exit(2)
        except SystemExit:
            raise
        except Exception:
            pass                                # fail-open: cơ chế bảo vệ phiên không được phá phiên

    # ── Tự chấm hệ mỗi N lượt (mặc định 50) — self-report đọc CÁC SỔ ĐÃ CÓ, 0 token.
    # Phần CHẤM chạy đồng bộ (local, nhanh); phần RAISE ISSUE về repo mẹ chạy NỀN (Popen tách
    # phiên) vì nó gọi mạng qua `gh` — không được để prompt của user đứng chờ GitHub.
    try:
        n_rep = load_count(root / ".claude" / "audit" / ".self-report.json", sid) + 1
        save_count(root / ".claude" / "audit" / ".self-report.json", sid, n_rep)
        sr = resolve_tool(str(root), "harness/scripts/self-report.py")
        if sr and REPORT_EVERY > 0 and n_rep % REPORT_EVERY == 0:
            p = subprocess.run([sys.executable, sr, "--root", str(root), "--json"],
                               capture_output=True, text=True, timeout=90)
            data = json.loads(p.stdout or "{}")
            fs = data.get("findings") or []
            if fs:
                head = "\n".join(f"  [{f['severity']}] {f['title']} — {f['evidence']}" for f in fs[:3])
                emit(f"[self-report] Đã {n_rep} lượt. Hệ tự chấm từ số đo trong sổ và thấy "
                     f"{len(fs)} vấn đề:\n{head}\n  Sửa: xem `python3 harness/scripts/self-report.py --report`. "
                     f"Vấn đề mức high/medium sẽ được raise về repo mẹ (dedupe + cooldown 7 ngày).")
                subprocess.Popen([sys.executable, sr, "--root", str(root), "--raise"],
                                 cwd=str(root), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
                sys.exit(0)      # đã nói phần quan trọng nhất lượt này; đừng chồng thêm docs-gate
    except SystemExit:
        raise
    except Exception:
        pass                     # fail-open: cơ chế tự chấm không được phá prompt

    state = root / ".claude" / "audit" / ".docs-gate.json"
    state.parent.mkdir(parents=True, exist_ok=True)

    n = load_count(state, sid) + 1
    save_count(state, sid, n)
    if EVERY <= 0 or n % EVERY != 0:
        sys.exit(0)

    # Mốc N prompt: soi N request gần nhất (transcript) + prompt hiện tại.
    window = last_user_texts(payload.get("transcript_path", ""), EVERY)
    window.append(payload.get("prompt", "") or "")
    blob = "\n".join(window).lower()
    need_docs = not any(t in blob for t in DOCS_TOKENS)
    need_eval = not any(t in blob for t in EVAL_TOKENS)
    if not need_docs and not need_eval:
        sys.exit(0)  # cả tài liệu lẫn đánh giá đang được duy trì → im lặng

    emit(build_gate(n, EVERY, need_docs, need_eval))
    sys.exit(0)


if __name__ == "__main__":
    main()
