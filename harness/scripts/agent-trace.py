#!/usr/bin/env python3
"""agent-trace — sổ KIỂM CHỨNG: agent nào đã quyết định gì, dựa bằng chứng nào, kiểm lại bằng lệnh gì.

Câu hỏi sổ này trả lời (đúng MỘT câu, theo convention `llmwiki/wiki/concepts/log-model.md`):

    "Agent — chính hay phụ — đã làm/quyết định gì trong phiên X, và tôi kiểm lại thế nào?"

KHÔNG sổ nào có sẵn trả lời được: `events.jsonl` ghi tool-call nhưng không có LÝ DO và bị
gitignore; `scratch-log` là ngữ cảnh vụn tự nguyện; `provenance-log` là artifact-level;
`memory.jsonl` là truy hồi ngữ nghĩa. Sổ này hẹp hơn tất cả: chỉ QUYẾT ĐỊNH + BẰNG CHỨNG +
CÁCH KIỂM LẠI.

── GIỚI HẠN PHẢI BIẾT TRƯỚC KHI TIN SỔ NÀY ──────────────────────────────────────────────
"Suy nghĩ" của agent **không log được**. Đo thật 2026-07-31 trên transcript Claude Code:
main 186 khối `thinking`, subagent ge-t7 34 khối — **nội dung RỖNG hết**, runtime không ghi
chuỗi suy luận ra đĩa. Nên sổ này KHÔNG hứa "lưu suy nghĩ". Nó lưu ba thứ có thật:

    1. HÀNH ĐỘNG   — agent chạy lệnh gì, sửa file nào  (từ tool_use trong transcript)
    2. LỜI NÓI RA  — agent giải thích quyết định thế nào (từ text block)
    3. QUYẾT ĐỊNH  — agent chủ động khai, kèm bằng chứng + lệnh kiểm lại (`note`)

Mục 3 là thứ đáng tin nhất, vì nó mang `verify` chạy lại được — không phải lời tự khai suông.
Mục 1-2 chưng cất từ transcript, giữ CON TRỎ (file + số dòng) chứ không nhân bản 15 MB.

── VÌ SAO KHÔNG NHÂN BẢN TRANSCRIPT ─────────────────────────────────────────────────────
Transcript đã có sẵn và đầy đủ hơn mọi bản sao. Vấn đề của nó là (a) nằm ngoài repo nên
không travel, (b) 15 MB / 2409 dòng nên không ai kiểm bằng mắt, (c) phân tán — 13 subagent
của một phiên nằm ở 13 slug khác nhau. Sổ này giải đúng ba cái đó: mỏng, trong repo, có index.

CLI:
    agent-trace.py on|off|status              bật/tắt (mặc định TẮT — không bật thì không ghi gì)
    agent-trace.py note --what W --why Y [--evidence E]... [--verify CMD] [--agent A]
    agent-trace.py collect [--session S] [--all]   chưng cất transcript → trace (cần bật)
    agent-trace.py show [--session S] [--agent A] [--limit N]
    agent-trace.py verify [--id N | --all]    CHẠY LẠI lệnh verify để kiểm chứng
    agent-trace.py --self-test
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TRACE_REL = "harness/metrics/agent-trace.jsonl"
CONFIG_REL = "harness/agent-trace.config.yaml"
TRANSCRIPT_HOME = Path.home() / ".claude" / "projects"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _trace_path(root: Path) -> Path:
    return root / TRACE_REL


def _git(root: Path, *args) -> str:
    try:
        p = subprocess.run(["git", "-C", str(root), *args],
                           capture_output=True, text=True, timeout=10)
        return p.stdout.strip()
    except Exception:
        return ""


def enabled(root: Path) -> bool:
    """Công tắc. Mặc định TẮT: một sổ ghi lén là sổ không ai tin, và cũng là rủi ro riêng tư."""
    cfg = root / CONFIG_REL
    if not cfg.exists():
        return False
    try:
        for line in cfg.read_text(encoding="utf-8").splitlines():
            s = line.split("#")[0].strip()
            if s.startswith("enabled:"):
                return s.split(":", 1)[1].strip().lower() in ("true", "yes", "1", "on")
    except Exception:
        pass
    return False


def set_enabled(root: Path, on: bool) -> None:
    cfg = root / CONFIG_REL
    cfg.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "# agent-trace.config.yaml — công tắc sổ kiểm chứng agent.\n"
        "#\n"
        "# TẮT là mặc định có chủ ý: sổ ghi lén thì không ai tin, và transcript agent có thể\n"
        "# chứa đường dẫn/nội dung riêng tư. Bật khi bạn CẦN kiểm chứng lại một phiên.\n"
        "#\n"
        "#   python3 harness/scripts/agent-trace.py on     # bật\n"
        "#   python3 harness/scripts/agent-trace.py off    # tắt\n"
        "\n"
        f"enabled: {'true' if on else 'false'}\n"
        "\n"
        "# Chỉ chưng cất transcript của project nào (khớp tiền tố slug trong ~/.claude/projects).\n"
        "# Để trống = tự suy từ tên thư mục repo, nên worktree con (…-ge-t1) cũng được gom.\n"
        "slug_prefix: \"\"\n"
    )
    cfg.write_text(body, encoding="utf-8")


def append(root: Path, rec: dict) -> bool:
    """Ghi một record. Fail-open: sổ kiểm chứng không bao giờ được phá việc chính."""
    try:
        if not enabled(root):
            return False
        p = _trace_path(root)
        p.parent.mkdir(parents=True, exist_ok=True)
        rec.setdefault("ts", _now())
        rec.setdefault("git_sha", _git(root, "rev-parse", "HEAD")[:12])
        rec.setdefault("branch", _git(root, "rev-parse", "--abbrev-ref", "HEAD"))
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def read(root: Path) -> list:
    out = []
    p = _trace_path(root)
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


# ── chưng cất transcript ────────────────────────────────────────────────────────────────
def _slugs(root: Path, prefix: str = "") -> list:
    """Mọi slug transcript thuộc project này — GỒM worktree con của subagent.

    Một phiên dispatch 13 agent đẻ ra 13 slug riêng (…-setup-ge-t1, …-ge-tt8). Bỏ sót chúng
    là bỏ sót đúng phần việc mình muốn kiểm: agent phụ làm gì khi không ai nhìn.
    """
    if not TRANSCRIPT_HOME.exists():
        return []
    key = prefix or root.name
    return sorted(d for d in TRANSCRIPT_HOME.iterdir()
                  if d.is_dir() and key.lower() in d.name.lower())


def distill_file(path: Path, max_text: int = 400) -> list:
    """Một transcript → danh sách sự kiện kiểm chứng được, KÈM con trỏ dòng về file gốc."""
    events = []
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("type") != "assistant":
                    continue
                msg = d.get("message") or {}
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "tool_use":
                        inp = b.get("input") or {}
                        # giữ mô tả + lệnh: đủ để biết agent LÀM gì mà không nuốt cả payload
                        events.append({
                            "kind": "action", "tool": b.get("name"),
                            "desc": str(inp.get("description") or "")[:160],
                            "cmd": str(inp.get("command") or inp.get("file_path") or "")[:300],
                            "ts": d.get("timestamp"), "src_line": lineno,
                        })
                    elif b.get("type") == "text":
                        t = (b.get("text") or "").strip()
                        if len(t) > 40:      # bỏ câu ngắn vô nghĩa ("xong", "ok")
                            events.append({"kind": "said", "text": t[:max_text],
                                           "ts": d.get("timestamp"), "src_line": lineno})
    except Exception:
        pass
    return events


def collect(root: Path, session: str = None, all_sessions: bool = False) -> tuple:
    """Quét transcript → ghi trace. Trả (số record, số transcript đã đọc)."""
    if not enabled(root):
        return -1, 0
    prefix = ""
    cfg = root / CONFIG_REL
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            s = line.split("#")[0].strip()
            if s.startswith("slug_prefix:"):
                prefix = s.split(":", 1)[1].strip().strip('"\'')
    n_rec = n_file = 0
    for slug in _slugs(root, prefix):
        files = sorted(slug.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not all_sessions:
            files = files[:1]                      # phiên mới nhất mỗi slug
        for f in files:
            sid = f.stem
            if session and session not in sid:
                continue
            evs = distill_file(f)
            if not evs:
                continue
            n_file += 1
            acts = [e for e in evs if e["kind"] == "action"]
            said = [e for e in evs if e["kind"] == "said"]
            append(root, {
                "type": "session-trace",
                "agent": slug.name.split("-")[-1] if "-ge-" in slug.name else "main",
                "session": sid[:8],
                "slug": slug.name,
                "transcript": str(f),              # CON TRỎ: kiểm sâu thì mở file này
                "actions": len(acts),
                "tools": sorted({a["tool"] for a in acts if a.get("tool")}),
                "first_ts": evs[0].get("ts"), "last_ts": evs[-1].get("ts"),
                # giữ 12 hành động + 6 lời nói đầu-cuối: đủ dựng lại mạch, không nuốt cả file
                "sample_actions": acts[:6] + acts[-6:] if len(acts) > 12 else acts,
                "sample_said": said[:3] + said[-3:] if len(said) > 6 else said,
            })
            n_rec += 1
    return n_rec, n_file


# ── kiểm chứng ──────────────────────────────────────────────────────────────────────────
def verify(root: Path, idx=None, run_all=False) -> int:
    """CHẠY LẠI lệnh `verify` của record — đây là điểm khác biệt với mọi sổ tự-khai khác."""
    recs = [r for r in read(root) if r.get("verify")]
    if not recs:
        print("[agent-trace] không record nào có lệnh verify — chưa có gì kiểm lại được")
        return 0
    targets = recs if run_all else ([recs[idx]] if idx is not None and -len(recs) <= idx < len(recs) else recs[-1:])
    bad = 0
    for r in targets:
        cmd = r["verify"]
        try:
            p = subprocess.run(cmd, shell=True, cwd=str(root),
                               capture_output=True, text=True, timeout=120)
            ok = p.returncode == 0
        except Exception as e:
            ok, p = False, type("x", (), {"returncode": -1, "stdout": "", "stderr": str(e)})()
        mark = "✅" if ok else "❌"
        print(f"  {mark} [{r.get('ts','')}] {str(r.get('what'))[:60]}")
        print(f"      $ {cmd}")
        if not ok:
            bad += 1
            tail = (p.stderr or p.stdout or "").strip().splitlines()[-2:]
            for t in tail:
                print(f"      {t[:150]}")
    print(f"\n  {len(targets) - bad}/{len(targets)} verify còn đúng")
    return 2 if bad else 0


def show(root: Path, session=None, agent=None, limit=20) -> None:
    recs = read(root)
    if session:
        recs = [r for r in recs if session in str(r.get("session", ""))]
    if agent:
        recs = [r for r in recs if agent == r.get("agent")]
    if not recs:
        print("[agent-trace] sổ rỗng (chưa bật? chạy: agent-trace.py on)")
        return
    print(f"agent-trace — {len(recs)} record  (hiện {min(limit, len(recs))} mới nhất)\n")
    for r in recs[-limit:]:
        if r.get("type") == "session-trace":
            print(f"  [{r.get('ts','')[:19]}] agent={r.get('agent'):<6} session={r.get('session')} "
                  f"· {r.get('actions')} hành động · tools: {', '.join(r.get('tools') or [])[:60]}")
            print(f"      transcript: {r.get('transcript')}")
        else:
            print(f"  [{r.get('ts','')[:19]}] agent={r.get('agent','?'):<6} QUYẾT ĐỊNH: {r.get('what')}")
            if r.get("why"):
                print(f"      vì: {r['why']}")
            for e in (r.get("evidence") or []):
                print(f"      bằng chứng: {e}")
            if r.get("verify"):
                print(f"      kiểm lại:   $ {r['verify']}")


def self_test() -> int:
    import tempfile
    fails = []

    def ck(name, cond):
        print(f"  [{'OK ' if cond else 'FAIL'}] {name}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        subprocess.run(["git", "init", "-q", td], capture_output=True)
        ck("mặc định TẮT (không config thì không ghi)", enabled(root) is False)
        ck("tắt thì append KHÔNG ghi gì", append(root, {"what": "x"}) is False
           and not _trace_path(root).exists())
        set_enabled(root, True)
        ck("bật được qua config", enabled(root) is True)
        ok = append(root, {"type": "decision", "what": "chọn A",
                           "evidence": ["a.py:1"], "verify": "true"})
        ck("bật rồi thì ghi được", ok and _trace_path(root).exists())
        recs = read(root)
        ck("đọc lại đúng 1 record", len(recs) == 1 and recs[0]["what"] == "chọn A")
        ck("record tự gắn ts + git_sha", bool(recs[0].get("ts")) and "git_sha" in recs[0])
        append(root, {"type": "decision", "what": "lệnh hỏng", "verify": "exit 3"})
        rc_bad = verify(root, run_all=True)
        ck("verify BẮT được lệnh hỏng (exit 2)", rc_bad == 2)
        set_enabled(root, False)
        ck("tắt lại thì ngừng ghi", append(root, {"what": "y"}) is False and len(read(root)) == 2)

        # distill trên transcript giả — khoá cấu trúc parse
        fake = root / "t.jsonl"
        fake.write_text("\n".join([
            json.dumps({"type": "assistant", "timestamp": "T1", "message": {"content": [
                {"type": "tool_use", "name": "Bash",
                 "input": {"command": "ls -la", "description": "liệt kê"}}]}}),
            json.dumps({"type": "assistant", "timestamp": "T2", "message": {"content": [
                {"type": "text", "text": "Tôi chọn cách A vì cách B làm hỏng backward-compat."}]}}),
            json.dumps({"type": "assistant", "timestamp": "T3", "message": {"content": [
                {"type": "thinking", "thinking": ""}]}}),
        ]), encoding="utf-8")
        evs = distill_file(fake)
        ck("distill bắt được hành động", any(e["kind"] == "action" and e["tool"] == "Bash" for e in evs))
        ck("distill bắt được lời giải thích", any(e["kind"] == "said" for e in evs))
        ck("distill giữ con trỏ dòng", all("src_line" in e for e in evs))
        ck("thinking rỗng KHÔNG thành record giả", not any(e.get("kind") == "thinking" for e in evs))

    print("\nSELF-TEST: " + ("ALL PASS" if not fails else f"{len(fails)} FAIL"))
    return 0 if not fails else 1


def _opt(args, flag, many=False):
    vals = []
    for i, a in enumerate(args):
        if a == flag and i + 1 < len(args):
            vals.append(args[i + 1])
    if many:
        return vals
    return vals[0] if vals else None


def main() -> None:
    args = sys.argv[1:]
    root = Path(_opt(args, "--root") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())

    if "--self-test" in args:
        sys.exit(self_test())
    cmd = args[0] if args else "status"

    if cmd == "on":
        set_enabled(root, True)
        print(f"[agent-trace] BẬT — ghi vào {TRACE_REL}\n"
              f"  chưng cất phiên đang có: python3 harness/scripts/agent-trace.py collect --all"); return
    if cmd == "off":
        set_enabled(root, False)
        print("[agent-trace] TẮT — không ghi thêm; dữ liệu cũ giữ nguyên"); return
    if cmd == "status":
        on = enabled(root)
        recs = read(root)
        print(f"[agent-trace] {'BẬT' if on else 'TẮT'} · {len(recs)} record · sổ: {TRACE_REL}")
        if not on:
            print("  bật: python3 harness/scripts/agent-trace.py on")
        return
    if cmd == "note":
        what = _opt(args, "--what")
        if not what:
            print("usage: agent-trace.py note --what W [--why Y] [--evidence E]... [--verify CMD] [--agent A]",
                  file=sys.stderr); sys.exit(2)
        ok = append(root, {"type": "decision", "what": what, "why": _opt(args, "--why"),
                           "evidence": _opt(args, "--evidence", many=True),
                           "verify": _opt(args, "--verify"),
                           "agent": _opt(args, "--agent") or "main"})
        print("[agent-trace] ghi xong" if ok else "[agent-trace] ĐANG TẮT — không ghi (bật: agent-trace.py on)")
        return
    if cmd == "collect":
        n, nf = collect(root, _opt(args, "--session"), "--all" in args)
        if n < 0:
            print("[agent-trace] ĐANG TẮT — bật trước: agent-trace.py on"); return
        print(f"[agent-trace] chưng cất {n} phiên từ {nf} transcript"); return
    if cmd == "show":
        lim = _opt(args, "--limit")
        show(root, _opt(args, "--session"), _opt(args, "--agent"), int(lim) if lim else 20); return
    if cmd == "verify":
        i = _opt(args, "--id")
        sys.exit(verify(root, int(i) if i else None, "--all" in args))

    print(__doc__.split("CLI:")[-1].strip())


if __name__ == "__main__":
    main()
