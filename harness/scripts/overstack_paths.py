#!/usr/bin/env python3
"""overstack_paths — MỘT nguồn chân lý cho câu "thư mục overstack nằm đâu trong dự án này".

Bối cảnh (đề xuất 040926-downstream-dot-layout): installer từng đặt `llmwiki/` và `harness/`
TRẦN ở gốc dự án đích, trong khi `.claude/` `.cursor/` `.kiro/` đều đã ẩn. Hệ quả: cổng thiết
kế (hallmark, impeccable, linter bên thứ ba) quét `**/*.html` của dự án sản phẩm là vớ phải
`llmwiki/html/overstack.html` 530KB rồi chấm nó như UI sản phẩm.

Chuẩn MỚI là `.llmwiki/` và `.harness/`. Nhưng đo được 79 file / 261 chỗ dựng đường dẫn lúc
chạy — đổi tên cứng hết một lượt là big-bang, sót một chỗ là bản cài cũ gãy câm. Nên theo thang
Meadows ta đổi LUỒNG THÔNG TIN thay vì sửa 261 tham số: mọi nơi hỏi cùng một hàm, hàm chấp cả
hai layout. File chưa kịp sửa vẫn chạy → migrate không còn là sự kiện một-lần-ăn-cả.

Thứ tự tìm là HỢP ĐỒNG, không phải chi tiết: **chuẩn mới trước, chuẩn cũ sau**. Dự án đã migrate
thì không bao giờ chạm nhánh cũ; dự án chưa migrate vẫn chạy y nguyên.

Dùng:
    from overstack_paths import wiki_dir, overstack_dir, harness_dir, needs_migration
"""
from __future__ import annotations

import pathlib

# Chuẩn mới đứng trước. Đổi thứ tự ở đây là đổi hành vi của toàn hệ — đừng sửa lẻ nơi khác.
OVERSTACK_DIRS = (".llmwiki", "llmwiki")
HARNESS_DIRS = (".harness", "harness")
# Trong repo framework, wiki của CHÍNH framework nằm ở fdk/wiki — luôn thắng.
FRAMEWORK_WIKI = "fdk/wiki"


def _first_dir(root, names, suffix=""):
    r = pathlib.Path(root)
    for n in names:
        c = r / n / suffix if suffix else r / n
        if c.is_dir():
            return c
    return None


def is_framework_repo(root) -> bool:
    """Repo framework tự nhận diện bằng fdk/wiki — KHÔNG bao giờ được migrate chính nó."""
    return (pathlib.Path(root) / FRAMEWORK_WIKI).is_dir()


def overstack_dir(root):
    """Thư mục overstack của dự án (.llmwiki ưu tiên, llmwiki để tương thích ngược)."""
    return _first_dir(root, OVERSTACK_DIRS)


def harness_dir(root):
    return _first_dir(root, HARNESS_DIRS)


def wiki_dir(root):
    """Thư mục wiki nội dung. Repo framework: fdk/wiki thắng trước (wiki của chính framework)."""
    r = pathlib.Path(root)
    fw = r / FRAMEWORK_WIKI
    if fw.is_dir():
        return fw
    d = _first_dir(root, OVERSTACK_DIRS, "wiki")
    if d:
        return d
    return r / "wiki" if (r / "wiki").is_dir() else None


def needs_migration(root) -> list:
    """Thư mục còn RƠI RỚT ở chuẩn cũ (có bản trần, chưa có bản dấu chấm).

    Trả list cặp (cũ, mới). Rỗng = đã đúng chuẩn hoặc là repo framework → bỏ qua.
    Đây là câu hỏi mà installer hỏi trước khi seed; giữ ở đây để installer và tool
    kiểm tra không bao giờ lệch định nghĩa."""
    r = pathlib.Path(root)
    if is_framework_repo(root):
        return []
    out = []
    for new, old in (OVERSTACK_DIRS, HARNESS_DIRS):
        if (r / old).is_dir() and not (r / new).is_dir():
            out.append((old, new))
    return out


# ── Cổng tất định phải đọc GIT, không đọc ĐĨA ─────────────────────────────────────
# Đo 2026-09-08: ba cổng cho kết quả khác nhau tuỳ máy đang có file local nào —
# build-overstack-docs --check (docs "cũ" vì wiki có 24 file chưa track), wiki-graph
# (394 node ở clone chính, 311 ở clone sạch), task_lifecycle (đỏ vì 13 file trong
# draft/archive/ bị .gitignore trỏ task đã xoá). Cùng một gốc: quét đĩa bằng rglob.
# Một hàm, ba nơi hỏi. Không có git → None, caller quét đĩa như cũ (fail-open).
_TRACKED_CACHE: dict = {}


def tracked_set(root) -> "set[str] | None":
    """Đường dẫn (posix, tương đối root) mà git đang track — gồm cả file mới `git add`.

    None khi không phải repo git / thiếu git: caller phải coi như "mọi file đều hợp lệ"
    chứ không được coi là "không file nào hợp lệ"."""
    import subprocess
    key = str(pathlib.Path(root).resolve())
    if key in _TRACKED_CACHE:
        return _TRACKED_CACHE[key]
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=key, capture_output=True,
                             text=True, timeout=15)
        val = set(x for x in out.stdout.split("\0") if x) if out.returncode == 0 else None
    except Exception:
        val = None
    _TRACKED_CACHE[key] = val
    return val


def is_tracked(root, path) -> bool:
    """True nếu git track `path` — hoặc nếu không có git để hỏi (fail-open)."""
    ts = tracked_set(root)
    if ts is None:
        return True
    try:
        rel = pathlib.Path(path).resolve().relative_to(pathlib.Path(root).resolve()).as_posix()
    except ValueError:
        return False
    return rel in ts


def self_test() -> int:
    import shutil
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp())
    ok = True

    def ck(label, cond):
        nonlocal ok
        print(f"  {'✓' if cond else '✗'} {label}")
        ok = ok and cond

    try:
        # 1. Dự án chuẩn CŨ: vẫn phân giải được (tương thích ngược là bắt buộc)
        old = tmp / "old"
        (old / "llmwiki" / "wiki").mkdir(parents=True)
        (old / "harness").mkdir()
        ck("layout CŨ vẫn phân giải được (không gãy bản cài cũ)",
           wiki_dir(old) == old / "llmwiki" / "wiki")
        ck("layout CŨ bị báo là CẦN migrate (cả 2 thư mục)",
           sorted(needs_migration(old)) == [("harness", ".harness"), ("llmwiki", ".llmwiki")])

        # 2. Dự án chuẩn MỚI: bỏ qua, không đề nghị migrate gì
        new = tmp / "new"
        (new / ".llmwiki" / "wiki").mkdir(parents=True)
        (new / ".harness").mkdir()
        ck("layout MỚI phân giải đúng", wiki_dir(new) == new / ".llmwiki" / "wiki")
        ck("layout MỚI → không migrate (idempotent, chạy lại vẫn im)", needs_migration(new) == [])

        # 3. Cả hai cùng tồn tại (migrate dở dang): chuẩn mới THẮNG
        both = tmp / "both"
        (both / ".llmwiki" / "wiki").mkdir(parents=True)
        (both / "llmwiki" / "wiki").mkdir(parents=True)
        ck("có cả hai → chuẩn MỚI thắng", wiki_dir(both) == both / ".llmwiki" / "wiki")

        # 4. Repo framework: KHÔNG BAO GIỜ tự migrate, và fdk/wiki thắng
        fw = tmp / "fw"
        (fw / "fdk" / "wiki").mkdir(parents=True)
        (fw / "llmwiki" / "wiki").mkdir(parents=True)
        ck("repo framework → fdk/wiki thắng", wiki_dir(fw) == fw / "fdk" / "wiki")
        ck("repo framework → KHÔNG BAO GIỜ migrate chính nó", needs_migration(fw) == [])

        # 5. tracked_set: cổng đọc GIT chứ không đọc ĐĨA
        import subprocess
        g = tmp / "g"; g.mkdir()
        run = lambda *a: subprocess.run(["git", "-C", str(g), *a], capture_output=True, text=True)
        run("init", "-q"); run("config", "user.email", "t@t"); run("config", "user.name", "t")
        (g / "a.md").write_text("a"); (g / "ign.md").write_text("i"); (g / "new.md").write_text("n")
        (g / ".gitignore").write_text("ign.md\n")
        run("add", "a.md", ".gitignore"); run("commit", "-q", "-m", "init")
        (g / "staged.md").write_text("s"); run("add", "staged.md")
        _TRACKED_CACHE.clear()
        ck("file đã commit → tracked", is_tracked(g, g / "a.md"))
        ck("file vừa git add (chưa commit) → tracked (người viết draft chỉ cần add)",
           is_tracked(g, g / "staged.md"))
        ck("file untracked → KHÔNG", not is_tracked(g, g / "new.md"))
        ck("file bị .gitignore → KHÔNG (đúng ca task_lifecycle đỏ 13 file archive)",
           not is_tracked(g, g / "ign.md"))
        ck("ngoài root → KHÔNG", not is_tracked(g, tmp / "old" / "x.md"))
        nog = tmp / "nogit"; nog.mkdir(); (nog / "x.md").write_text("x")
        ck("không có git → None, is_tracked fail-open = True",
           tracked_set(nog) is None and is_tracked(nog, nog / "x.md"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("self-test: PASS" if ok else "self-test: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    print(f"overstack : {overstack_dir(root)}")
    print(f"wiki      : {wiki_dir(root)}")
    print(f"harness   : {harness_dir(root)}")
    mig = needs_migration(root)
    print(f"migrate   : {mig or 'không cần (đã đúng chuẩn hoặc repo framework)'}")
