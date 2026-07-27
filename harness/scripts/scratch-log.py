#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scratch-log — BỘ NHỚ THỨ CẤP tầng THÔ + DISTILL (proposal 030726-secondary-memory).

Xem llmwiki/wiki/concepts/log-model.md để biết sổ này khác gì events.jsonl/mem-rank/
touches/provenance-log — mỗi sổ trả lời một câu hỏi hẹp, KHÔNG phối hợp với nhau.

Bắt SỬA VỤN + CONTEXT VỤN (không chỉ proposal chính thức) để KHÔNG MẤT gì + truy được ở phiên sau.
File-first, visualizable, KHÔNG RAG. Chỉ stdlib.

Khác events.jsonl (code-logger, GITIGNORED local): scratch-log.jsonl được TRACK trong git
→ history bất biến = lưới an toàn "không mất" (council-024, Taleb+Munger). Judgment "đáng nhớ"
để ở lúc ĐỌC/distill, không lúc ghi. `why` OPTIONAL — không ép agent.

CLI:
  scratch-log.py note "<vì sao / context vụn>" [--file PATH] [--session ID] [--action edit]
        → append 1 entry vào harness/metrics/scratch-log.jsonl (append-only)
  scratch-log.py distill [--session ID] [--date YYYY-MM-DD]
        → gom scratch-log + wiki-ledger theo phiên → sources/DDMMYY-session-provenance.md
           (distill KHÔNG xoá thô, chỉ trỏ về)
  scratch-log.py show [--session ID] [-n 20]   → in các entry gần nhất (đọc bằng mắt)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    # Ưu tiên cwd: Stop-hook chạy engine (có thể ở GLOBAL ~/.claude/harness) với cwd=project root
    # → data/ledger ghi đúng project downstream, không phải thư mục engine global.
    cwd = Path.cwd()
    if (cwd / "llmwiki").is_dir() or (cwd / ".git").is_dir():
        return cwd
    p = Path(__file__).resolve()
    for up in p.parents:
        if (up / "llmwiki").is_dir() or (up / ".git").is_dir():
            return up
    return cwd


ROOT = repo_root()
LOG = ROOT / "harness" / "metrics" / "scratch-log.jsonl"
LEDGER = ROOT / "llmwiki" / "wiki" / "ledger.jsonl"


def _now_iso():
    # tránh Date.now non-determinism trong test — dùng mtime-free stamp qua env nếu có, else để trống
    import os
    return os.environ.get("SCRATCH_TS", "")


def note(args):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": args.ts or _now_iso(), "session": args.session or "",
           "action": args.action, "file": args.file or "", "why": args.why}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"scratch: ghi 1 entry (session={rec['session'] or '?'}, file={rec['file'] or '-'})")
    return 0


def _read(path):
    if not path.exists():
        return []
    out = []
    for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except ValueError:
                pass
    return out


def show(args):
    rows = _read(LOG)
    if args.session:
        rows = [r for r in rows if r.get("session") == args.session]
    for r in rows[-args.n:]:
        why = (r.get("why") or "").strip()
        print(f"  [{r.get('session','?')[:8]}] {r.get('action','')} {r.get('file','-')}"
              + (f"  ← {why}" if why else ""))
    print(f"({len(rows)} entry" + (f", session {args.session[:8]}" if args.session else "") + ")")
    return 0


def _git(root, *argv):
    """Chạy git, trả stdout đã strip (rỗng nếu lỗi/thiếu git). Fail-open."""
    try:
        p = subprocess.run(["git", "-C", str(root), *argv],
                           capture_output=True, text=True, timeout=8)
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:
        return ""


def auto(args):
    """Chốt 2 (council-030, fail-closed MỀM): nếu phiên có SỬA thật (git dirty hoặc vừa commit)
    mà scratch-log CHƯA có `why` thủ công nào cho phiên → TỰ trích một `why` từ git
    (subject commit gần nhất + file đổi nhiều nhất) rồi append 1 note. Đường tự-động vì thế
    KHÔNG BAO GIỜ rỗng why ở đuôi (agent lười/quên). KHÔNG đè lên why thủ công — tôn trọng con người.
    Fail-open tuyệt đối: thiếu git / không mutation → không ghi gì, trả 0."""
    sess = args.session
    have = [r for r in _read(LOG)
            if (not sess or r.get("session") == sess) and (r.get("why") or "").strip()]
    if have:
        return 0  # phiên đã có why thủ công → không đụng
    root = args.root or str(ROOT)
    dirty = _git(root, "status", "--porcelain")
    subject = _git(root, "log", "-1", "--format=%s")
    changed = [ln[3:] for ln in dirty.splitlines() if len(ln) > 3]
    if not dirty and not subject:
        return 0  # không mutation, không lịch sử → không bịa why
    top = changed[0] if changed else ""
    why = f"auto: {subject or '(chưa commit)'} — trích từ git ({len(changed)} file dirty); agent chưa ghi why thủ công"
    rec = {"ts": args.ts or _now_iso(), "session": sess or "",
           "action": "auto", "file": top, "why": why}
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"scratch-auto: điền why từ git (session={rec['session'][:8] or '?'}, {len(changed)} file dirty)")
    return 0


def distill(args):
    """Gom scratch-log + wiki-ledger cho MỘT phiên → session-provenance.md (tầng distill).
    KHÔNG xoá thô — chỉ trỏ về file scratch-log.jsonl."""
    sess = args.session
    scratch = [r for r in _read(LOG) if not sess or r.get("session") == sess]
    ledger = [r for r in _read(LEDGER) if not sess or (r.get("session") or "").startswith((sess or "")[:8])]
    if not sess and scratch:
        sess = scratch[-1].get("session", "")
    whys = [r for r in scratch if (r.get("why") or "").strip()]
    files = sorted({r.get("file") for r in scratch if r.get("file")} |
                   {r.get("target") for r in ledger if r.get("target")})
    date = args.date or "unknown"
    ddmmyy = date  # DDMMYY khớp convention framework (030726)
    if len(date) == 10 and date[4] == "-":     # YYYY-MM-DD → DDMMYY
        ddmmyy = date[8:10] + date[5:7] + date[2:4]
    out = ROOT / "llmwiki" / "wiki" / "sources" / f"{ddmmyy}-session-provenance.md"
    lines = [
        "---", "type: source",
        f'title: "session-provenance {sess[:8]} (auto-distill scratch-log)"',
        "status: shipped", "tags: [session-provenance, secondary-memory, auto-distill]",
        f'timestamp: {date}', f'session: {sess}', "---", "",
        f"# session-provenance {sess[:8]} — auto-distill",
        "",
        f"**Nguồn thô (KHÔNG xoá):** `harness/metrics/scratch-log.jsonl` · `llmwiki/wiki/ledger.jsonl` (session {sess[:8]}).",
        "",
        "## Vì sao (context vụn — distill từ scratch-log)",
    ]
    if whys:
        for r in whys:
            lines.append(f"- {r.get('why').strip()}" + (f"  _(file: `{r.get('file')}`)_" if r.get('file') else ""))
    else:
        lines.append("- _(chưa có annotate `why` — agent chưa ghi lý do vụn nào phiên này)_")
    lines += ["", "## File chạm trong phiên", ""]
    for fp in files[:60]:
        lines.append(f"- `{fp}`")
    lines += ["", "## Origin", f"- **Session:** `{sess}`",
              "- **Generated by:** scratch-log.py distill (auto, tầng 2 bộ nhớ thứ cấp)", ""]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"distill: {len(whys)} why + {len(files)} file → {out.relative_to(ROOT)} (thô giữ nguyên)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("note")
    n.add_argument("why")
    n.add_argument("--file", default="")
    n.add_argument("--session", default="")
    n.add_argument("--action", default="note")
    n.add_argument("--ts", default="")
    s = sub.add_parser("show")
    s.add_argument("--session", default="")
    s.add_argument("-n", type=int, default=20)
    d = sub.add_parser("distill")
    d.add_argument("--session", default="")
    d.add_argument("--date", default="")
    au = sub.add_parser("auto")
    au.add_argument("--session", default="")
    au.add_argument("--root", default="")
    au.add_argument("--ts", default="")
    a = ap.parse_args()
    return {"note": note, "show": show, "distill": distill, "auto": auto}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
