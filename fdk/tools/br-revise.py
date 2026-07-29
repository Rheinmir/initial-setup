#!/usr/bin/env python3
"""br-revise — the LLM revise ADAPTER for /br run (GH#15, build-now-adapt-later).

The loop-runner's revise step is the ONE quarantined unknown. This adapter makes it
concrete: it reads the frame + the prompt TEMPLATE (skills/br/assets/revise-prompt.md),
fills the placeholders with the frame's data + the last verify output, and calls
`claude -p` with BOUNDED tools (no free Bash, no network). The frame's scope is still
enforced deterministically by loop-runner's diff-jail / test-hash guards — the prompt is
only a first, soft layer (council 5/5: prompt is NOT the safety layer).

WHAT'S DETERMINISTIC (built + selftested here):
  • loading the frame, loading the template, rendering {{placeholders}} → the exact prompt.
  • `--print` emits that prompt without calling any model (inspect/debug/edit loop).
QUARANTINED (verified:false): the actual `claude -p` invocation. Edit the PROMPT by editing
`skills/br/assets/revise-prompt.md`; edit WHICH tools are allowed via --allowed-tools.

Usage (loop-runner calls this as its --revise cmd):
  br-revise.py --frame br/frames/<id>.md --verify "<cmd>" --verify-output <file> [--cwd DIR]
               [--template skills/br/assets/revise-prompt.md] [--print] [--allowed-tools "Edit,Write,Read,Grep,Glob"]
  br-revise.py selftest       # deterministic template-render checks (no model call)

`--print` writes the composed prompt to stdout and exits 0 (no model). Without it, the
adapter pipes the prompt to `claude -p` (exit follows the CLI).
"""
import argparse
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

_FL = Path(__file__).with_name("frame-lint.py")
_spec = importlib.util.spec_from_file_location("frame_lint", _FL)
_frame_lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frame_lint)
parse_frontmatter = _frame_lint.parse_frontmatter

DEFAULT_TEMPLATE = Path(__file__).resolve().parents[2] / "skills" / "br" / "assets" / "revise-prompt.md"
DEFAULT_TOOLS = "Edit,Write,Read,Grep,Glob"  # bounded: no free Bash, no network


def _fmt_list(v):
    if isinstance(v, list):
        return ", ".join(str(x) for x in v)
    return str(v if v is not None else "")


def render_prompt(frame_fm, verify_cmd, verify_output, template_text):
    """Deterministically fill the template. Same inputs → same prompt (byte-identical)."""
    values = {
        "frame_id": str(frame_fm.get("frame_id", "")),
        "muc_tieu": str(frame_fm.get("muc_tieu", "")),
        "scope_code": _fmt_list(frame_fm.get("scope_code")),
        "scope_test": _fmt_list(frame_fm.get("scope_test")),
        "clause_ids": _fmt_list(frame_fm.get("clause_ids")),
        "verify_cmd": str(verify_cmd or ""),
        "verify_output": str(verify_output or "(chưa có output)"),
    }
    # drop the leading guidance block (everything above the first '---' separator line)
    body = template_text
    if "\n---\n" in body:
        body = body.split("\n---\n", 1)[1]
    out = body
    for k, v in values.items():
        out = out.replace("{{" + k + "}}", v)
    return out.strip() + "\n"


def load_frame(path):
    return parse_frontmatter(Path(path).read_text(encoding="utf-8"))


def build_and_maybe_call(frame_path, verify_cmd, verify_output_path, template_path,
                         cwd, do_print, allowed_tools, prompts_path="br/prompts.md"):
    fm = load_frame(frame_path)
    # HIGHEST priority: the user's hand-edited SỔ PROMPT (br/prompts.md, section ## <frame_id>).
    # A hand edit there always wins over queue/prompt_file/default template.
    template_text = None
    if prompts_path:
        pp = Path(cwd) / prompts_path if not Path(prompts_path).is_absolute() else Path(prompts_path)
        if pp.exists():
            try:
                _bp = importlib.util.spec_from_file_location(
                    "br_prompts", Path(__file__).with_name("br-prompts.py"))
                _bpm = importlib.util.module_from_spec(_bp)
                _bp.loader.exec_module(_bpm)
                sec = _bpm.get_section(pp, str(fm.get("frame_id", "")))
                if sec:
                    template_text = sec  # section IS the full prompt body (no guidance block to strip)
            except Exception:
                template_text = None
    if template_text is None:
        template_text = Path(template_path).read_text(encoding="utf-8")
    verify_output = ""
    if verify_output_path and Path(verify_output_path).exists():
        verify_output = Path(verify_output_path).read_text(encoding="utf-8")[-4000:]
    prompt = render_prompt(fm, verify_cmd, verify_output, template_text)
    if do_print:
        sys.stdout.write(prompt)
        return 0
    # QUARANTINED boundary: the real model call. Bounded tools; runs in the worktree cwd.
    cmd = ["claude", "-p", "--allowedTools", allowed_tools]
    try:
        proc = subprocess.run(cmd, input=prompt, text=True, cwd=cwd)
        return proc.returncode
    except FileNotFoundError:
        print("[br-revise] `claude` CLI not found — adapter is verified:false. "
              "Use --print to inspect the prompt, or install the CLI to wire revise.",
              file=sys.stderr)
        return 127


# ── Self-test: deterministic template render (no model) ─────────────────────
def selftest():
    ok = True
    tmpl = ("# guidance\n> edit me\n\n---\n\n"
            "Frame {{frame_id}} muc_tieu={{muc_tieu}} clauses={{clause_ids}}\n"
            "scope_code={{scope_code}} scope_test={{scope_test}}\n"
            "verify={{verify_cmd}}\nOUT:\n{{verify_output}}\n")
    fm = {"frame_id": "f1", "muc_tieu": "lam X", "clause_ids": ["S4.1", "S4.2"],
          "scope_code": ["src/**"], "scope_test": ["tests/**"]}
    p = render_prompt(fm, "pytest -q", "AssertionError: boom", tmpl)

    checks = [
        ("guidance block dropped", "# guidance" not in p and "edit me" not in p),
        ("frame_id filled", "Frame f1 " in p),
        ("muc_tieu filled", "muc_tieu=lam X" in p),
        ("clause list joined", "clauses=S4.1, S4.2" in p),
        ("scope_code filled", "scope_code=src/**" in p),
        ("scope_test filled", "scope_test=tests/**" in p),
        ("verify cmd filled", "verify=pytest -q" in p),
        ("verify output filled", "AssertionError: boom" in p),
        ("no leftover placeholder", "{{" not in p),
        ("deterministic", render_prompt(fm, "pytest -q", "AssertionError: boom", tmpl) == p),
    ]
    # missing verify output → placeholder text
    p2 = render_prompt(fm, "pytest -q", "", tmpl)
    checks.append(("empty verify → placeholder", "(chưa có output)" in p2))
    # --print path via the default template file (must exist + render)
    with tempfile.TemporaryDirectory() as td:
        fpath = Path(td) / "frame.md"
        fpath.write_text("---\nschema_version: 0\nframe_id: fT\ncreated_by: human\n"
                         "parent_br: BR.md\nclause_ids: [S1.1]\nparent_br_hash: x\n"
                         'muc_tieu: "muc tieu that"\nscope_code: ["src/**"]\n'
                         'scope_test: ["tests/**"]\nacceptance_test: "true"\n---\n# fT\n')
        vout = Path(td) / "v.txt"; vout.write_text("boom-real")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = build_and_maybe_call(str(fpath), "true", str(vout), str(DEFAULT_TEMPLATE),
                                      td, True, DEFAULT_TOOLS)
        out = buf.getvalue()
        checks.append(("--print uses real template + frame", rc == 0 and "fT" in out and "boom-real" in out
                       and "{{" not in out))
        # SỔ PROMPT wins: a hand-edited br/prompts.md section overrides the template
        (Path(td) / "br").mkdir()
        (Path(td) / "br" / "prompts.md").write_text(
            "# sổ\n\n## fT\n\nPROMPT TAY CỦA USER cho {{muc_tieu}} — out: {{verify_output}}\n",
            encoding="utf-8")
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            rc2 = build_and_maybe_call(str(fpath), "true", str(vout), str(DEFAULT_TEMPLATE),
                                       td, True, DEFAULT_TOOLS, "br/prompts.md")
        out2 = buf2.getvalue()
        checks.append(("sổ prompt (sửa tay) THẮNG template", rc2 == 0 and "PROMPT TAY CỦA USER" in out2
                       and "muc tieu that" in out2 and "boom-real" in out2 and "Bạn là một agent" not in out2))

    print("br-revise self-test — deterministic prompt render (no model)\n" + "-" * 58)
    for name, good in checks:
        ok = ok and good
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
    print("-" * 58)
    print(f"  RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="br-revise.py", description="LLM revise adapter for /br run (prompt from an editable template).")
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="render the prompt and call claude -p (default)")
    r.add_argument("--frame", required=True)
    r.add_argument("--verify", default="")
    r.add_argument("--verify-output", default=None, help="file with the last verify output")
    r.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    r.add_argument("--cwd", default=".")
    r.add_argument("--print", dest="do_print", action="store_true", help="print the composed prompt, do NOT call the model")
    r.add_argument("--allowed-tools", default=DEFAULT_TOOLS)
    r.add_argument("--prompts", default="br/prompts.md", help="sổ prompt tổng (section ## <frame_id> thắng mọi nguồn khác); '' để tắt")
    r.set_defaults(func=lambda a: build_and_maybe_call(a.frame, a.verify, a.verify_output,
                                                       a.template, a.cwd, a.do_print, a.allowed_tools,
                                                       a.prompts))
    s = sub.add_parser("selftest", help="deterministic template-render checks (no model)")
    s.set_defaults(func=lambda a: selftest())
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        build_parser().parse_args(["--help"])
        return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
