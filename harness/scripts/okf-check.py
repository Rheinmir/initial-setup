#!/usr/bin/env python3
"""OKF v0.1 compliance check + migrate cho cây wiki.

Hai chế độ (dùng chung logic với validator R9 okf_frontmatter.py):
  --check    : quét wiki, báo file nào chưa OKF. exit 0 = sạch, 3 = có file cần migrate.
  --migrate  : convert pseudo-frontmatter dạng bold (**Type:** …) -> YAML frontmatter.
               Chỉ THÊM frontmatter + bỏ các dòng bold đã hấp thụ; KHÔNG đụng body/## Origin.
               Idempotent: file đã có '---' frontmatter -> bỏ qua.

OKF v0.1 (Google Cloud, 2026-06-12): mỗi concept là 1 file Markdown có YAML frontmatter
parse được, bắt buộc đúng 1 trường `type` không rỗng; bên đọc dung thứ khóa lạ.

Dùng bởi: skill health-check (--check), sync-template & harness-update (--migrate).
"""
import argparse
import importlib.util
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

HERE = Path(__file__).resolve().parent          # harness/scripts
VALIDATORS = HERE.parent / "validators"

SKIP_BASENAMES = {"README.md", "_template.md", "index.md", "log.md", "decisions.md", "active-context.md"}
CONTENT_DIRS = ("concepts", "entities", "sources", "draft", "architecture", "tours")
FRONTMATTER_RE = re.compile(r"^---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", re.DOTALL)
BOLD_RE = re.compile(r"^\*\*([A-Za-z][\w ]*?):?\*\*[ \t]*:?[ \t]*(.*?)[ \t]*$")
H1_RE = re.compile(r"^#\s+(.*?)\s*$")

# Suy ra type mặc định từ thư mục khi bold không khai Type.
DIR_TYPE = {"concepts": "concept", "entities": "entity", "draft": "draft", "sources": "source"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def content_files(wiki: Path):
    """File wiki để check/migrate OKF — ĐÃ loại file gitignored (local-only): an-toàn-mặc-định,
    caller (audit, sync-template) khỏi tự lọc → không flag/migrate file archive/draft cố ý local.
    gitignored() dùng CANONICAL index_sync.py (pattern _load() như audit.py) — trước đây tự cài
    lại logic git check-ignore riêng, 3 scanner từng thiếu bước này cùng lúc (failure-flywheel
    170726, 3 ca spec-violation); giờ 1 implementation duy nhất, sửa 1 chỗ là mọi caller ăn theo."""
    index_mod = _load(VALIDATORS / "index_sync.py", "_indexsync")
    out = []
    for p in wiki.rglob("*.md"):
        if p.name in SKIP_BASENAMES:
            continue
        rel = p.relative_to(wiki).parts
        if rel and rel[0] in CONTENT_DIRS and not index_mod.gitignored(p.relative_to(wiki).as_posix(), wiki):
            out.append(p)
    return sorted(out)


def has_okf_frontmatter(text: str) -> bool:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return False
    block = m.group(1)
    if yaml is not None:
        try:
            d = yaml.safe_load(block)
        except yaml.YAMLError:
            return False
        return isinstance(d, dict) and bool(str(d.get("type", "")).strip())
    return bool(re.search(r"^type[ \t]*:[ \t]*\S", block, re.MULTILINE))


def infer_type(path: Path, wiki: Path) -> str:
    parts = path.relative_to(wiki).parts
    for seg in parts:
        if seg in DIR_TYPE:
            return DIR_TYPE[seg]
    return "concept"


def migrate_text(text: str, path: Path, wiki: Path):
    """Trả (new_text, changed). Convert bold header -> YAML frontmatter."""
    if has_okf_frontmatter(text):
        return text, False
    lines = text.splitlines()
    i = 0
    # bỏ qua dòng trống đầu
    while i < len(lines) and not lines[i].strip():
        i += 1
    title = None
    if i < len(lines):
        m = H1_RE.match(lines[i])
        if m:
            title = m.group(1)
            i += 1
    # gom các dòng bold metadata ngay sau H1
    meta = {}
    consumed_to = i
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            consumed_to = i
            continue
        bm = BOLD_RE.match(ln)
        if not bm:
            break
        meta[bm.group(1).strip().lower()] = bm.group(2).strip()
        i += 1
        consumed_to = i
    # body còn lại
    body_lines = lines[consumed_to:]

    typ = meta.get("type") or infer_type(path, wiki)
    fm = ["---", f"type: {typ}"]
    if title:
        fm.append(f"title: {title}")
    if meta.get("status"):
        fm.append(f"status: {meta['status']}")
    if meta.get("tags"):
        tags = [t.strip() for t in re.split(r"[,;]", meta["tags"]) if t.strip()]
        if tags:
            fm.append("tags: [" + ", ".join(tags) + "]")
    if meta.get("resource") or meta.get("origin"):
        fm.append(f"resource: {meta.get('resource') or meta.get('origin')}")
    ts = meta.get("timestamp") or meta.get("proposed") or meta.get("date")
    if ts:
        fm.append(f"timestamp: {ts}")
    fm.append("---")
    fm.append("")
    if title:
        fm.append(f"# {title}")
    # giữ Status trong body cho draft (R7 đọc **Status:**)
    if typ == "draft" and meta.get("status"):
        fm.append("")
        fm.append(f"**Status:** {meta['status']}")
    # đúng 1 dòng trống ngăn cách header với body
    body = list(body_lines)
    while body and not body[0].strip():
        body.pop(0)
    out = fm + ([""] + body if body else [])
    new = "\n".join(out)
    if not new.endswith("\n"):
        new += "\n"
    return new, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--wiki-dir", default=None)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true")
    g.add_argument("--migrate", action="store_true")
    args = ap.parse_args()

    wiki = Path(args.wiki_dir) if args.wiki_dir else Path(args.root) / "llmwiki" / "wiki"
    if not wiki.is_dir():
        print(f"[okf-check] khong tim thay wiki dir: {wiki}", file=sys.stderr)
        sys.exit(1)

    files = content_files(wiki)
    bad = [p for p in files if not has_okf_frontmatter(p.read_text(encoding="utf-8"))]

    if args.migrate:
        if not bad:
            print(f"[okf-check] OKF-clean ({len(files)} file) — khong co gi de migrate.")
            sys.exit(0)
        changed = 0
        for p in bad:
            new, ch = migrate_text(p.read_text(encoding="utf-8"), p, wiki)
            if ch:
                p.write_text(new, encoding="utf-8")
                changed += 1
                print(f"  ✎ migrated  {p.relative_to(wiki)}")
        print(f"[okf-check] migrate xong: {changed}/{len(bad)} file -> YAML frontmatter (OKF v0.1).")
        sys.exit(0)

    # default = --check
    print(f"[okf-check] OKF v0.1 — wiki: {wiki}")
    print(f"  content files : {len(files)}")
    print(f"  OKF-compliant : {len(files) - len(bad)}/{len(files)}")
    if bad:
        print(f"  ⚠ chua dat chuan ({len(bad)}):")
        for p in bad:
            print(f"      - {p.relative_to(wiki)}")
        print("  -> chay: python3 harness/scripts/okf-check.py --migrate")
        sys.exit(3)
    print("  ✓ DAT CHUAN OKF v0.1 (3/3 tieu chi)")
    sys.exit(0)


if __name__ == "__main__":
    main()
