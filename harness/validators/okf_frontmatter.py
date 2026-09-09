#!/usr/bin/env python3
"""R9 okf-frontmatter: mọi file nội dung wiki phải tuân Open Knowledge Format (OKF) v0.1.

OKF v0.1 (Google Cloud, 2026-06-12): mỗi concept là một file Markdown có YAML frontmatter
parse được, bắt buộc đúng một trường `type` không rỗng. Bên đọc PHẢI dung thứ khóa lạ →
validator này CHỈ kiểm: (1) có khối frontmatter `---…---` parse được, (2) có `type` không rỗng.

Contract (giống các validator khác — xem harness/recipe.md):
  - stdin JSON : {"action":"write","file_path":...,"content":...}
                 nếu không có "content" thì đọc file từ disk (PostToolUse — file đã ghi xong).
  - argv files : okf_frontmatter.py path1 path2 ...
  - exit 0 = pass, exit 2 = vi phạm (lý do ghi ra stderr).
"""
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Reserved filenames (R5 allow-root + cấu trúc/chỉ mục) — miễn yêu cầu OKF concept.
SKIP_BASENAMES = {"README.md", "_template.md", "index.md", "log.md", "decisions.md", "active-context.md"}
CONTENT_DIRS = ("concepts/", "entities/", "sources/", "draft/", "architecture/", "tours/")
WIKI_REL_RE = re.compile(r"(?:^|/)wiki/(.+)$")
FRONTMATTER_RE = re.compile(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", re.DOTALL)
# Fallback khi không có pyyaml: bắt dòng `type: <non-empty>` trong khối frontmatter.
TYPE_LINE_RE = re.compile(r"^type[ \t]*:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE)


def is_wiki_content_file(path: str) -> bool:
    p = (path or "").replace("\\", "/")
    if not p.endswith(".md"):
        return False
    m = WIKI_REL_RE.search(p)
    if not m:
        return False
    rel = m.group(1)
    if Path(rel).name in SKIP_BASENAMES or "archive" in Path(rel).parts:
        return False   # archive/ = nháp đông cứng (tidy dời vào) — không soi lại lịch sử
    return rel.startswith(CONTENT_DIRS)


def fail(path: str, reason: str) -> None:
    print(f"[R9 okf-frontmatter] {path} {reason}", file=sys.stderr)
    sys.exit(2)


def check(path, content):
    if not is_wiki_content_file(path):
        return
    if content is None:
        try:
            content = Path(path).read_text(encoding="utf-8")
        except OSError:
            return

    m = FRONTMATTER_RE.match(content)
    if not m:
        fail(path, "thieu YAML frontmatter '---…---' o dau file (OKF v0.1 yeu cau).")
    block = m.group(1)

    if yaml is not None:
        try:
            data = yaml.safe_load(block)
        except yaml.YAMLError as e:
            fail(path, f"frontmatter khong parse duoc YAML: {str(e).splitlines()[0]}")
        if not isinstance(data, dict):
            fail(path, "frontmatter khong phai mapping YAML (key: value).")
        tval = data.get("type")
        if tval is None or (isinstance(tval, str) and not tval.strip()):
            fail(path, "frontmatter thieu truong 'type' khong rong (truong DUY NHAT bat buoc cua OKF).")
    else:
        if not TYPE_LINE_RE.search(block):
            fail(path, "frontmatter thieu truong 'type' khong rong (OKF) — [pyyaml khong co, dung kiem regex].")


def main() -> None:
    args = sys.argv[1:]
    if args:
        for p in args:
            check(p, None)
        sys.exit(0)
    try:
        ev = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if ev.get("action") == "write":
        check(ev.get("file_path", ""), ev.get("content") or None)
    sys.exit(0)


if __name__ == "__main__":
    main()
