#!/usr/bin/env python3
"""br-find — "trỏ vào khúc lỗi → ra frame/prompt phụ trách" (GH#15).

The normal-person flow: run the app, spot a bug, point at it — a FILE PATH
(src/auth/login.py) or a KEYWORD (đăng nhập / login / S4.1) — and this tool answers:
which FRAME owns that spot, which BR clause it came from, WHERE its prompt lives
(queue inline / prompt_file / default template), and the exact command to re-run just
that frame after you edit the prompt. Works because every frame's scope is exclusive
(frame-lint + diff-jail enforce it), so one file → one owning frame.

Matching (deterministic, in priority order):
  1. changed_files in the frame's run-log  (files the frame ACTUALLY touched)
  2. scope_code globs                      (declared ownership)
  3. keyword in muc_tieu / clause_ids / frame_id

Usage:
  br-find.py <path-or-keyword> [--root .] [--frames br/frames] [--queue br/queue.yaml]
  br-find.py selftest
"""
import argparse
import fnmatch
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
_FL = _HERE.with_name("frame-lint.py")
_spec = importlib.util.spec_from_file_location("frame_lint", _FL)
_frame_lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frame_lint)
parse_frontmatter = _frame_lint.parse_frontmatter

DEFAULT_TEMPLATE = "skills/br/assets/revise-prompt.md"


def load_frames(root, frames_dir):
    out = []
    d = Path(root) / frames_dir if not Path(frames_dir).is_absolute() else Path(frames_dir)
    if not d.is_dir():
        return out
    for f in sorted(d.glob("*.md")):
        if f.name == "index.md":
            continue
        try:
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        runlog = {}
        ref = fm.get("run_log_ref")
        if ref:
            p = Path(root) / ref
            if p.exists():
                try:
                    runlog = json.loads(p.read_text(encoding="utf-8"))
                except (ValueError, OSError):
                    runlog = {}
        out.append({"file": str(f), "fm": fm, "runlog": runlog})
    return out


def prompt_source(frame_id, frame_file, root, queue_path):
    """Where does this frame's prompt live? SỔ PROMPT (hand-edited) > queue inline >
    queue prompt_file > default template."""
    pb = Path(root) / "br" / "prompts.md"
    if pb.exists():
        try:
            _bp = importlib.util.spec_from_file_location("br_prompts", _HERE.with_name("br-prompts.py"))
            _bpm = importlib.util.module_from_spec(_bp)
            _bp.loader.exec_module(_bpm)
            if _bpm.get_section(pb, frame_id):
                return ("SỔ PROMPT (sửa tay được, thắng mọi nguồn)", f"{pb} — mục `## {frame_id}`")
        except Exception:
            pass
    qp = Path(root) / queue_path if not Path(queue_path).is_absolute() else Path(queue_path)
    if yaml is not None and qp.exists():
        try:
            entries = yaml.safe_load(qp.read_text(encoding="utf-8")) or []
            for i, e in enumerate(entries):
                if not isinstance(e, dict):
                    continue
                ef = str(e.get("frame", ""))
                if frame_id in ef or ef.endswith(Path(frame_file).name):
                    if str(e.get("prompt") or "").strip():
                        return ("inline trong queue", f"{qp} (mục #{i} — sửa field `prompt:` ngay tại đó)")
                    if e.get("prompt_file"):
                        return ("prompt_file", str(e["prompt_file"]))
                    break
        except Exception:
            pass
    return ("template mặc định", DEFAULT_TEMPLATE)


def match(frames, query):
    """Return (frame_entry, how) hits, best-first, deduped."""
    q = query.strip()
    ql = q.lower()
    hits = []
    for fr in frames:
        fm, runlog = fr["fm"], fr["runlog"]
        changed = runlog.get("changed_files") or []
        # 1. actual changed file
        if any(q == c or q in c for c in changed):
            hits.append((fr, f"file THẬT frame đã đổi ({q})", 0))
            continue
        # 2. declared scope glob
        if any(fnmatch.fnmatch(q, g) for g in (fm.get("scope_code") or [])):
            hits.append((fr, f"khớp scope_code {fm.get('scope_code')}", 1))
            continue
        # 3. keyword
        hay = " ".join([str(fm.get("frame_id", "")), str(fm.get("muc_tieu", "")),
                        " ".join(str(c) for c in fm.get("clause_ids") or [])]).lower()
        if ql and ql in hay:
            hits.append((fr, f"khớp từ khoá trong mục tiêu/clause", 2))
    hits.sort(key=lambda h: h[2])
    return [(fr, how) for fr, how, _ in hits]


def find(query, root=".", frames_dir="br/frames", queue_path="br/queue.yaml", out=print):
    frames = load_frames(root, frames_dir)
    if not frames:
        out(f"[br-find] không có frame nào dưới {frames_dir} — chạy /br slice trước.")
        return 2
    hits = match(frames, query)
    if not hits:
        out(f"[br-find] không frame nào khớp: {query!r}")
        out("  gợi ý: thử đường dẫn file (src/...), tên frame, hoặc từ trong mục tiêu.")
        return 1
    for fr, how in hits:
        fm = fr["fm"]
        fid = fm.get("frame_id")
        kind, where = prompt_source(fid, fr["file"], root, queue_path)
        out(f"\n🎯 {fid}   (khớp vì: {how})")
        out(f"   mục tiêu   : {fm.get('muc_tieu')}")
        out(f"   điều khoản : {', '.join(str(c) for c in fm.get('clause_ids') or [])}   → BR: {fm.get('parent_br')}")
        out(f"   scope      : {', '.join(fm.get('scope_code') or [])}   (test: {', '.join(fm.get('scope_test') or [])})")
        v = fr["runlog"].get("verdict")
        if v:
            out(f"   run cuối   : {v} · file đổi: {', '.join(fr['runlog'].get('changed_files') or []) or '(không)'} · commit {str(fr['runlog'].get('commit'))[:8] if fr['runlog'].get('commit') else '—'}")
        out(f"   📝 PROMPT  : {kind} → {where}")
        out(f"   ▶ sửa prompt xong, chạy lại đúng frame này:")
        out(f"       python3 fdk/tools/br-run.py run {fr['file']} --root {root}")
    return 0


# ── Self-test ────────────────────────────────────────────────────────────────
def selftest():
    ok = True
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "br" / "frames").mkdir(parents=True)
        def frame(fid, muc, scope, run=None):
            body = ("---\nschema_version: 0\nframe_id: %s\ncreated_by: human\nparent_br: br/BR.md\n"
                    "clause_ids: [S4.1]\nparent_br_hash: x\nmuc_tieu: \"%s\"\nscope_code: [\"%s\"]\n"
                    "scope_test: [\"tests/**\"]\nacceptance_test: \"true\"\n" % (fid, muc, scope))
            if run:
                body += f"run_log_ref: {run}\n"
            (root / "br" / "frames" / f"{fid}.md").write_text(body + "---\n", encoding="utf-8")
        frame("frame-login", "man hinh dang nhap", "src/auth/**", run="br/l.run.json")
        (root / "br" / "l.run.json").write_text(json.dumps(
            {"verdict": "SUCCESS", "changed_files": ["src/auth/login.py"], "commit": "abc12345"}))
        frame("frame-report", "xuat bao cao thang", "src/report/**")
        (root / "br" / "queue.yaml").write_text(
            "- frame: br/frames/frame-login.md\n  prompt: |\n    inline x\n  status: done\n"
            "- frame: br/frames/frame-report.md\n  prompt_file: prompts/report.md\n  status: pending\n",
            encoding="utf-8")

        lines = []
        cap = lambda s="": lines.append(str(s))
        # 1) point at an ACTUAL changed file → frame-login, prompt = inline in queue
        find("src/auth/login.py", root=str(root), out=cap)
        t = "\n".join(lines)
        c1 = "frame-login" in t and "file THẬT" in t and "inline trong queue" in t
        # 2) point at a file only covered by declared scope → frame-report, prompt_file
        lines.clear(); find("src/report/monthly.py", root=str(root), out=cap)
        t = "\n".join(lines)
        c2 = "frame-report" in t and "scope_code" in t and "prompts/report.md" in t
        # 3) keyword in Vietnamese goal text
        lines.clear(); find("bao cao", root=str(root), out=cap)
        c3 = "frame-report" in "\n".join(lines)
        # 4) no match → helpful exit 1
        lines.clear(); rc = find("khong-ton-tai.py", root=str(root), out=cap)
        c4 = rc == 1 and "không frame nào khớp" in "\n".join(lines)
        # 5) re-run command printed
        lines.clear(); find("src/auth/login.py", root=str(root), out=cap)
        c5 = "br-run.py run" in "\n".join(lines)
        # 6) SỔ PROMPT wins over queue when a hand-edited section exists
        (root / "br" / "prompts.md").write_text("# sổ\n\n## frame-login\n\nprompt tay\n", encoding="utf-8")
        lines.clear(); find("src/auth/login.py", root=str(root), out=cap)
        c6 = "SỔ PROMPT" in "\n".join(lines)

    print("br-find self-test — point-at-bug → frame/prompt lookup\n" + "-" * 56)
    for name, good in [("changed-file hit → frame + inline prompt", c1),
                       ("scope-glob hit → frame + prompt_file", c2),
                       ("keyword hit (mục tiêu tiếng Việt)", c3),
                       ("no-match → rc 1 + gợi ý", c4),
                       ("re-run command included", c5),
                       ("SỔ PROMPT thắng queue khi có mục sửa tay", c6)]:
        ok = ok and good
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
    print("-" * 56)
    print(f"  RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="br-find.py", description="Point at a bug (file/keyword) → owning frame + its prompt.")
    p.add_argument("query", nargs="?", help="file path hoặc từ khoá (vd: src/auth/login.py · 'đăng nhập' · S4.1)")
    p.add_argument("--root", default=".")
    p.add_argument("--frames", default="br/frames")
    p.add_argument("--queue", default="br/queue.yaml")
    p.add_argument("--selftest", action="store_true")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.selftest or args.query == "selftest":
        return selftest()
    if not args.query:
        build_parser().print_help()
        return 2
    return find(args.query, args.root, args.frames, args.queue)


if __name__ == "__main__":
    sys.exit(main())
