#!/usr/bin/env python3
"""R16 report-show-path: HTML report/visualization phải tự khai đường dẫn của mình.

File HTML dưới llmwiki/html/ (trừ archive/, assets/) phải chứa đường dẫn tuyệt đối
của chính nó trong nội dung (footer/titlebar) — người xem biết file nằm đâu để mở lại/sửa.
Nguồn: feedback user 020726 ("file đâu để coi path là gì") + rule skill fdk.

Contract: stdin JSON {"action":"write","file_path":...} hoặc argv files. Exit 0/2.
"""
import json
import re
import sys
from pathlib import Path

SKIP_PARTS = {"archive", "assets"}


ARCHIFY_RE = re.compile(r"\barchify \d+\.\d+")


def is_report_html(path: str) -> bool:
    p = (path or "").replace("\\", "/")
    if not p.endswith(".html"):
        return False
    if "llmwiki/html/" not in p:
        return False
    rel = p.split("llmwiki/html/", 1)[1]
    return not any(part in SKIP_PARTS for part in Path(rel).parts[:-1])


def check(path: str) -> None:
    if not is_report_html(path):
        return
    try:
        content = Path(path).read_text(encoding="utf-8")
    except OSError:
        return
    if ARCHIFY_RE.search(content) and "<svg" in content:
        return  # artifact archify (viewer tự chứa, không có footer) — cùng cách miễn như R7 (080926)
    abs_path = str(Path(path).resolve())
    rel_path = repo_relative(abs_path)
    # #131: artifact đã commit ghi đường TƯƠNG ĐỐI từ gốc repo (đường tuyệt đối drift theo máy).
    # R16 chỉ cần người xem biết file nằm đâu — cả hai dạng đều trả lời được.
    if abs_path not in content and (not rel_path or rel_path not in content):
        print(
            f"[R16 report-show-path] {path} khong chua duong dan cua chinh no "
            f"(tuyet doi {abs_path} hoac tuong doi tu goc repo {rel_path or '?'}) — them footer/titlebar dang "
            f"<code>{rel_path or abs_path}</code> de nguoi xem biet file nam dau (rule skill fdk, feedback 020726; #131 chon tuong doi).",
            file=sys.stderr,
        )
        sys.exit(2)


def repo_relative(abs_path: str):
    """Đường từ gốc repo ('llmwiki/html/x.html'); None nếu không nằm trong repo git nào."""
    p = Path(abs_path)
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists():
            return p.relative_to(parent).as_posix()
    return None


def self_test():
    import tempfile
    d = Path(tempfile.mkdtemp()); (d / ".git").mkdir(); (d / "llmwiki" / "html").mkdir(parents=True)
    f = d / "llmwiki" / "html" / "r.html"
    f.write_text("<footer><code>llmwiki/html/r.html</code></footer>")
    assert repo_relative(str(f)) == "llmwiki/html/r.html"
    check(str(f))  # tương đối → qua (không exit)
    f.write_text(f"<footer><code>{f.resolve()}</code></footer>"); check(str(f))  # tuyệt đối → qua
    f.write_text("<p>no path</p>")
    try:
        check(str(f)); raise AssertionError("phai chan file khong co path")
    except SystemExit as e:
        assert e.code == 2
    f.write_text("<html>archify 2.17.0 <svg></svg></html>"); check(str(f))  # archify → miễn
    print("report_show_path --self-test: 4/4 ok")


def main() -> None:
    if sys.argv[1:] == ["--self-test"]:
        self_test(); return
    args = sys.argv[1:]
    if args:
        for p in args:
            check(p)
        sys.exit(0)
    try:
        ev = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if ev.get("action") == "write":
        check(ev.get("file_path", ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
