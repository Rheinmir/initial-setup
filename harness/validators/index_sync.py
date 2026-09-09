#!/usr/bin/env python3
"""R3 index-sync: wiki/index.md phải liệt kê đúng tập file wiki tồn tại.

Contract: `index_sync.py --wiki-dir path/to/wiki` (CLI/pre-commit/Stop hook)
          hoặc stdin JSON {"action":"stop","wiki_dir":"..."}.
Exit 0 = khớp, exit 2 = lệch (liệt kê thiếu/thừa trên stderr).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

SKIP_BASENAMES = {"README.md", "_template.md"}
_IGN_CACHE: dict[str, bool] = {}


def gitignored(rel: str, wiki: Path) -> bool:
    """True nếu (wiki/rel) bị .gitignore loại — drafts/html local-only cố ý (xem ADR/.gitignore).

    Hoạt động cả trên FRESH CLONE (file vắng mặt nhưng .gitignore tracked → khớp pattern),
    nên index_sync nhất quán giữa máy tác giả và clone sạch: file gitignored được BỎ QUA cả
    hai chiều (không bắt buộc có row, mà row trỏ tới nó cũng không bị coi là 'thừa').
    Fail-open: git lỗi/không có → coi như KHÔNG ignore.

    `git check-ignore` cần chạy VỚI CWD nằm trong working tree để tìm .gitignore — nếu tiến
    trình gọi (hook/agent) có cwd trôi ra ngoài repo, lệnh fail-open sai thành "không ignore"
    dù path đúng, gây báo THUA giả cho draft/archive local-only. Ép cwd=wiki_abs (luôn nằm
    trong repo, không phụ thuộc cwd kế thừa từ caller) — VÀ resolve `full` thành absolute
    trước khi truyền cho git, vì nếu `wiki` tới dưới dạng relative (--wiki-dir fdk/wiki) thì
    `full` cũng relative; đổi cwd mà không resolve full sẽ khiến full bị nối đôi theo cwd mới
    (fdk/wiki/fdk/wiki/...) và check sai theo hướng ngược lại.
    """
    wiki_abs = wiki.resolve()
    full = (wiki_abs / rel).as_posix()
    if full not in _IGN_CACHE:
        try:
            r = subprocess.run(["git", "check-ignore", "-q", full], cwd=str(wiki_abs),
                                capture_output=True, timeout=5)
            _IGN_CACHE[full] = (r.returncode == 0)
        except Exception:
            _IGN_CACHE[full] = False
    return _IGN_CACHE[full]
_TRACKED_CACHE = {}


def tracked(wiki: Path):  # -> set[str] | None (3.9 không có union operator)
    """Tập path (rel theo wiki) mà git ĐANG theo dõi — kể cả mới `git add` (đọc index, không HEAD).

    Lý do tồn tại: file có trên đĩa nhưng CHƯA add và KHÔNG bị ignore thì fresh clone không
    thấy — index.md trỏ tới nó sẽ đỏ trên CI mà xanh ở máy tác giả. Đó đúng là lỗ mà docstring
    của gitignored() nói là phải bịt: "nhất quán giữa máy tác giả và clone sạch".
    Fail-open: git lỗi/không có → None, caller giữ nguyên hành vi cũ. RỖNG cũng coi như
    None: sandbox `git init` mới toanh (harness/tests/*.sh copy cây rồi init, không add)
    có 0 file tracked — ở đó "chưa add" KHÔNG đồng nghĩa "clone sạch không thấy", và áp
    luật untracked sẽ báo THỪA toàn bộ index.
    """
    key = str(wiki.resolve())
    if key not in _TRACKED_CACHE:
        try:
            r = subprocess.run(["git", "ls-files", "-z", "--cached", "."], cwd=key,
                               capture_output=True, timeout=10)
            got = ({p for p in r.stdout.decode().split("\0") if p}
                   if r.returncode == 0 else None)
            _TRACKED_CACHE[key] = got or None
        except Exception:
            _TRACKED_CACHE[key] = None
    return _TRACKED_CACHE[key]


CONTENT_DIRS = ("concepts", "entities", "sources", "draft", "architecture", "tours")
LINK_RE = re.compile(r"\]\(([^)#\s]+\.md)\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


def content_files(wiki: Path) -> set[str]:
    """Tập file wiki 'tính vào index' — ĐÃ loại file gitignored (drafts/html/archive local-only):
    chúng không bắt buộc index và nhất quán local ↔ fresh clone. An-toàn-mặc-định: caller (main,
    audit, indexed_files) khỏi tự lọc lại 'exist' → không tái lặp drift bỏ-quên-lọc gitignored."""
    out = set()
    trk = tracked(wiki)
    for d in CONTENT_DIRS:
        base = wiki / d
        if not base.is_dir():
            continue
        for f in base.rglob("*.md"):
            rel = f.relative_to(wiki).as_posix()
            if f.name in SKIP_BASENAMES or gitignored(rel, wiki):
                continue
            if trk is not None and rel not in trk:
                continue   # chưa `git add` → fresh clone không có → coi như vắng mặt
            out.add(rel)
    return out


def indexed_files(wiki: Path) -> set[str]:
    idx = wiki / "index.md"
    if not idx.is_file():
        return set()
    text = idx.read_text(encoding="utf-8")
    refs = {m.lstrip("./") for m in LINK_RE.findall(text)}
    # wikilink trong index: [[name]] → khớp theo basename không đuôi
    names = {m.strip() for m in WIKILINK_RE.findall(text)}
    if names:
        for f in content_files(wiki):
            if Path(f).stem in names:
                refs.add(f)
    return refs


IDX_AUTO_START = "<!-- index:auto:start -->"
IDX_AUTO_END = "<!-- index:auto:end -->"


def _row(wiki: Path, rel: str) -> str:
    """1 dòng index cho file wiki (type từ frontmatter, summary = dòng # đầu)."""
    stem = Path(rel).stem
    typ, summ = "auto", ""
    try:
        t = (wiki / rel).read_text(encoding="utf-8")
        m = re.search(r"^type:\s*(\w+)", t, re.M)
        if m:
            typ = m.group(1)
        h = re.search(r"^#\s+(.+)$", t, re.M)
        if h:
            summ = h.group(1).strip()[:80]
    except Exception:
        pass
    return f"| [{stem}]({rel}) | {typ} | {summ} |"


def fix(wiki: Path, missing) -> int:
    """Self-healing: thêm dòng cho file thiếu vào block auto của index.md. Giữ nguyên phần người viết."""
    idx = wiki / "index.md"
    if not idx.is_file() or not missing:
        return 0
    rows = [_row(wiki, m) for m in missing]
    block = IDX_AUTO_START + "\n" + "\n".join(rows) + "\n" + IDX_AUTO_END
    text = idx.read_text(encoding="utf-8")
    if IDX_AUTO_START in text and IDX_AUTO_END in text:
        pre = text.split(IDX_AUTO_START)[0]
        post = text.split(IDX_AUTO_END, 1)[1]
        # gộp với dòng auto cũ
        old = text.split(IDX_AUTO_START, 1)[1].split(IDX_AUTO_END, 1)[0]
        existing = [ln for ln in old.splitlines() if ln.strip().startswith("|")]
        block = IDX_AUTO_START + "\n" + "\n".join(existing + rows) + "\n" + IDX_AUTO_END
        new = pre.rstrip() + "\n" + block + post
    else:
        new = text.rstrip() + "\n\n" + block + "\n"
    idx.write_text(new, encoding="utf-8")
    return len(rows)


def main() -> None:
    wiki_dir = None
    args = sys.argv[1:]
    if "--wiki-dir" in args:
        wiki_dir = args[args.index("--wiki-dir") + 1]
    elif not sys.stdin.isatty():
        try:
            ev = json.load(sys.stdin)
            wiki_dir = ev.get("wiki_dir")
        except Exception:
            pass
    if not wiki_dir:
        print("usage: index_sync.py --wiki-dir <path>", file=sys.stderr)
        sys.exit(0)

    wiki = Path(wiki_dir)
    if not wiki.is_dir():
        sys.exit(0)

    # content_files() đã loại file gitignored (local-only, an-toàn-mặc-định) — khỏi lọc 'exist' lại.
    # Chiều 'stale' vẫn phải lọc: 'indexed' lấy từ index.md có thể trỏ tới file gitignored.
    exist = content_files(wiki)
    indexed = indexed_files(wiki)
    missing = sorted(exist - indexed)                                   # có file (tracked), index chưa ghi
    stale = sorted(f for f in (indexed - exist) if not gitignored(f, wiki))  # row trỏ file tracked không tồn tại

    if "--fix" in sys.argv[1:]:
        n = fix(wiki, missing)
        print(f"[R3 index-sync --fix] đã auto-thêm {n} dòng vào index.md (block auto); còn stale: {len(stale)}")
        sys.exit(0)

    if missing or stale:
        lines = ["[R3 index-sync] wiki/index.md lech voi thuc te:"]
        lines += [f"  THIEU trong index: {f}" for f in missing]
        lines += [f"  THUA trong index (file khong ton tai): {f}" for f in stale]
        lines.append("  → Cap nhat wiki/index.md cho khop roi tiep tuc.")
        print("\n".join(lines), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
