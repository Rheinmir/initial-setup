#!/usr/bin/env bash
# scope-config-test — GH#49: .overstack.yaml (wiki_dir + code_root) là scope TƯỜNG MINH, và MỌI hook
# đọc cùng một nguồn (hooklib.scope_config): find_wiki_dir() + stop.all_wiki_dirs() tôn trọng wiki_dir
# khai báo (relocate được), thiếu file → hành vi cũ y nguyên, file hỏng → không chặn.
# Usage: bash harness/tests/scope-config-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
python3 - "$ROOT" <<'PY'
import importlib.util, os, pathlib, sys, tempfile
root = sys.argv[1]; hooks = pathlib.Path(root, "llmwiki/.claude/hooks"); sys.path.insert(0, str(hooks))
def load(name):
    spec = importlib.util.spec_from_file_location(name, hooks / f"{name}.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
hl = load("hooklib"); stop = load("stop")
ok = 0
def check(cond, msg):
    global ok
    print(("  \033[1;32m✓\033[0m " if cond else "  \033[1;31m✗\033[0m ") + msg); ok += 0 if cond else 1
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); (t / "llmwiki/wiki").mkdir(parents=True); (t / "docs/kb").mkdir(parents=True)
    # 1. thiếu file → mặc định cũ
    c = hl.scope_config(str(t)); check(c == {"wiki_dir": None, "code_root": None}, "thiếu .overstack.yaml → không khoá nào (mặc định cũ)")
    check(hl.find_wiki_dir(str(t)) == t / "llmwiki/wiki", "find_wiki_dir mặc định = llmwiki/wiki")
    # 2. khai wiki_dir + code_root → relocate
    (t / ".overstack.yaml").write_text("# scope\nwiki_dir: docs/kb   # relocate\ncode_root: 'src'\n", encoding="utf-8")
    c = hl.scope_config(str(t)); check(c == {"wiki_dir": "docs/kb", "code_root": "src"}, f"parse 2 khoá (bỏ comment, bỏ quote): {c}")
    check(hl.find_wiki_dir(str(t)) == t / "docs/kb", "find_wiki_dir tôn trọng wiki_dir khai báo")
    check(stop.all_wiki_dirs(str(t))[0] == t / "docs/kb" and (t / "llmwiki/wiki") in stop.all_wiki_dirs(str(t)), "stop.all_wiki_dirs: wiki khai báo đứng đầu, wiki ngầm định vẫn được soi")
    check(stop._scope_config(str(t)) == ("docs/kb", "src"), "stop._scope_config dùng chung nguồn hooklib")
    # 3. wiki_dir khai nhưng KHÔNG tồn tại → rơi về ứng viên cũ, không vỡ
    (t / ".overstack.yaml").write_text("wiki_dir: nowhere\n", encoding="utf-8")
    check(hl.find_wiki_dir(str(t)) == t / "llmwiki/wiki", "wiki_dir khai sai đường → fallback ứng viên cũ")
    # 4. file hỏng → không exception
    (t / ".overstack.yaml").write_bytes(b"\xff\xfe:::")
    try: hl.scope_config(str(t)); check(True, "config hỏng → fail-open")
    except Exception as e: check(False, f"config hỏng ném exception: {e}")
sys.exit(1 if ok else 0)
PY
rc=$?; [ $rc -eq 0 ] && printf '\n\033[1m═══ scope-config: \033[1;32mPASS\033[0m\033[0m\n' || printf '\n\033[1m═══ scope-config: \033[1;31mFAIL\033[0m\033[0m\n'; exit $rc
