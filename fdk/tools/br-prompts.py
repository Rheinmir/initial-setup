#!/usr/bin/env python3
"""br-prompts — SỔ PROMPT tổng: one human-editable file for EVERY frame's prompt.

The user asked for a single, visually structured file they can open, find a frame's
prompt by hand, and EDIT/ADD content WITHOUT going through a model. That file is
`br/prompts.md`:

    # SỔ PROMPT — dây chuyền Ralph
    ## frame-001-login
    <toàn bộ prompt của frame này — sửa/thêm thoải mái, placeholder {{...}} được giữ>
    ## frame-002-validate
    ...

Resolution order at run time (br-revise): br/prompts.md section > queue inline >
queue prompt_file > default template. So a hand edit here ALWAYS wins.

`sync` adds a section for every frame that doesn't have one (seeded from the default
template body, placeholders intact) and NEVER touches sections that already exist —
hand edits are sacred. Orphan sections (no matching frame) are reported, not deleted.

Usage:
  br-prompts.py sync  [--root .] [--frames br/frames] [--prompts br/prompts.md]
  br-prompts.py list  [--prompts br/prompts.md]
  br-prompts.py get <frame_id> [--prompts br/prompts.md]
  br-prompts.py selftest
"""
import argparse
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
_FL = _HERE.with_name("frame-lint.py")
_spec = importlib.util.spec_from_file_location("frame_lint", _FL)
_frame_lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frame_lint)
parse_frontmatter = _frame_lint.parse_frontmatter

DEFAULT_TEMPLATE = _REPO / "skills" / "br" / "assets" / "revise-prompt.md"

HEADER = """# 📒 SỔ PROMPT — dây chuyền Ralph (br/prompts.md)

> MỘT file cho TẤT CẢ prompt. Mỗi frame một mục `## <frame_id>` — mở ra, tìm frame,
> SỬA / THÊM nội dung bằng tay, không cần qua model. Khi chạy (`/br run`), bản ở đây
> được ƯU TIÊN CAO NHẤT (trên queue inline / prompt_file / template mặc định).
> Placeholder được phép: {{muc_tieu}} {{scope_code}} {{scope_test}} {{clause_ids}}
> {{verify_cmd}} {{verify_output}} — máy điền lúc chạy.
> `br-prompts.py sync` chỉ THÊM mục cho frame mới, KHÔNG BAO GIỜ đè mục đã có.
"""

_SECTION_RE = re.compile(r"^## +(\S+) *$", re.M)


def parse_sections(text):
    """Return {frame_id: body} from the prompts file."""
    out = {}
    matches = list(_SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1)] = text[m.end():end].strip("\n")
    return out


def get_section(prompts_path, frame_id):
    p = Path(prompts_path)
    if not p.exists():
        return None
    body = parse_sections(p.read_text(encoding="utf-8")).get(frame_id)
    return body if body and body.strip() else None


def _default_body():
    t = DEFAULT_TEMPLATE.read_text(encoding="utf-8")
    body = t.split("\n---\n", 1)[1].strip() if "\n---\n" in t else t.strip()
    # demote template's `## ` headings → `### ` so the ONLY `## ` lines in the sổ are
    # frame sections (một mức heading = một frame; mắt quét là thấy).
    return body.replace("\n## ", "\n### ")


def sync(root=".", frames_dir="br/frames", prompts_path="br/prompts.md", out=print):
    root = Path(root)
    fdir = root / frames_dir if not Path(frames_dir).is_absolute() else Path(frames_dir)
    ppath = root / prompts_path if not Path(prompts_path).is_absolute() else Path(prompts_path)
    frames = []
    if fdir.is_dir():
        for f in sorted(fdir.glob("*.md")):
            if f.name == "index.md":
                continue
            try:
                fm = parse_frontmatter(f.read_text(encoding="utf-8"))
                frames.append((fm.get("frame_id"), fm.get("muc_tieu", "")))
            except (ValueError, OSError):
                continue
    existing_text = ppath.read_text(encoding="utf-8") if ppath.exists() else ""
    existing = parse_sections(existing_text)
    body_tmpl = _default_body()

    added = []
    parts = [existing_text.rstrip() if existing_text.strip() else HEADER.rstrip()]
    for fid, muc in frames:
        if not fid or fid in existing:
            continue
        parts.append(f"\n\n## {fid}\n\n<!-- mục tiêu: {muc} — sửa/thêm nội dung dưới đây tuỳ ý -->\n\n{body_tmpl}")
        added.append(fid)
    orphans = [k for k in existing if k not in {f for f, _ in frames}]
    if added:
        ppath.parent.mkdir(parents=True, exist_ok=True)
        ppath.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    out(f"[br-prompts] {ppath}: +{len(added)} mục mới {added or ''} · giữ nguyên {len(existing)} mục đã có"
        + (f" · ⚠ mồ côi (không có frame): {orphans}" if orphans else ""))
    return 0


def list_cmd(prompts_path, out=print):
    p = Path(prompts_path)
    if not p.exists():
        out(f"[br-prompts] chưa có {prompts_path} — chạy `br-prompts.py sync` để tạo.")
        return 1
    secs = parse_sections(p.read_text(encoding="utf-8"))
    for fid, body in secs.items():
        first = next((ln for ln in body.splitlines() if ln.strip() and not ln.strip().startswith("<!--")), "")
        out(f"  ## {fid}  ({len(body)} ký tự)  {first[:60]}")
    return 0


def get_cmd(prompts_path, frame_id, out=print):
    body = get_section(prompts_path, frame_id)
    if body is None:
        out(f"[br-prompts] không có mục `## {frame_id}` trong {prompts_path}")
        return 1
    out(body)
    return 0


# ── Self-test ────────────────────────────────────────────────────────────────
def selftest():
    ok = True
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "br" / "frames").mkdir(parents=True)
        def frame(fid, muc):
            (root / "br" / "frames" / f"{fid}.md").write_text(
                "---\nschema_version: 0\nframe_id: %s\ncreated_by: human\nparent_br: BR.md\n"
                "clause_ids: [S1.1]\nparent_br_hash: x\nmuc_tieu: \"%s\"\nscope_code: [\"src/**\"]\n"
                "scope_test: [\"tests/**\"]\nacceptance_test: \"true\"\n---\n" % (fid, muc), encoding="utf-8")
        frame("frame-a", "viec a"); frame("frame-b", "viec b")
        msgs = []
        sync(root=str(root), out=msgs.append)
        pfile = root / "br" / "prompts.md"
        t1 = pfile.read_text(encoding="utf-8")
        c1 = "## frame-a" in t1 and "## frame-b" in t1 and "SỔ PROMPT" in t1
        # user hand-edits frame-a's prompt
        t_edit = t1.replace("Bạn là một agent sửa code", "NỘI DUNG USER TỰ THÊM: ưu tiên hiệu năng.\n\nBạn là một agent sửa code", 1)
        pfile.write_text(t_edit, encoding="utf-8")
        # new frame appears → sync again: adds frame-c, PRESERVES the hand edit
        frame("frame-c", "viec c")
        sync(root=str(root), out=msgs.append)
        t2 = pfile.read_text(encoding="utf-8")
        c2 = "## frame-c" in t2
        c3 = "NỘI DUNG USER TỰ THÊM" in t2                    # hand edit survived
        c4 = t2.count("## frame-a") == 1                       # no duplicate section
        # get returns the edited body
        body = get_section(pfile, "frame-a")
        c5 = body is not None and "NỘI DUNG USER TỰ THÊM" in body
        # orphan detection: remove frame-b file → sync reports orphan, keeps section
        (root / "br" / "frames" / "frame-b.md").unlink()
        msgs.clear(); sync(root=str(root), out=msgs.append)
        c6 = "mồ côi" in msgs[0] and "frame-b" in msgs[0] and "## frame-b" in pfile.read_text(encoding="utf-8")

    print("br-prompts self-test — sổ prompt tổng, sửa tay an toàn\n" + "-" * 56)
    for name, good in [("sync tạo đủ section + header", c1),
                       ("sync lần 2 thêm frame mới", c2),
                       ("SỬA TAY được GIỮ NGUYÊN qua sync", c3),
                       ("không nhân đôi section", c4),
                       ("get trả đúng bản đã sửa tay", c5),
                       ("mồ côi: báo, không xoá", c6)]:
        ok = ok and good
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
    print("-" * 56)
    print(f"  RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="br-prompts.py", description="Sổ prompt tổng — một file, user tự sửa tay, máy tôn trọng.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sync", help="thêm section cho frame mới (không đè mục đã có)")
    s.add_argument("--root", default="."); s.add_argument("--frames", default="br/frames")
    s.add_argument("--prompts", default="br/prompts.md")
    s.set_defaults(func=lambda a: sync(a.root, a.frames, a.prompts))
    l = sub.add_parser("list", help="liệt kê các mục prompt")
    l.add_argument("--prompts", default="br/prompts.md")
    l.set_defaults(func=lambda a: list_cmd(a.prompts))
    g = sub.add_parser("get", help="in prompt của một frame")
    g.add_argument("frame_id"); g.add_argument("--prompts", default="br/prompts.md")
    g.set_defaults(func=lambda a: get_cmd(a.prompts, a.frame_id))
    t = sub.add_parser("selftest")
    t.set_defaults(func=lambda a: selftest())
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
