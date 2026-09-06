#!/usr/bin/env bash
# stop-hook-all-wikis-test — GH#76: Stop-hook auto-index + R3 phải soi MỌI wiki (fdk/wiki + llmwiki/wiki),
# không chỉ cái find_wiki_dir() trả về đầu tiên. Kịch bản thật: distill() ghi vào llmwiki/wiki/sources/,
# R3 (harness-events) soi llmwiki/wiki, nhưng auto-index cũ chỉ chữa fdk/wiki → agent vá tay mỗi phiên.
# Test gọi thẳng stop.main() với medic-mirror/regen/secondary_memory được vô hiệu (chỉ soi khối wiki).
# Usage: bash harness/tests/stop-hook-all-wikis-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
cp -R "$ROOT/llmwiki" "$TMP/llmwiki"; cp -R "$ROOT/fdk" "$TMP/fdk"; cp -R "$ROOT/harness" "$TMP/harness"
# .gitignore đi kèm: R3 git-aware bỏ qua draft/archive + html bị ignore — thiếu nó thì báo "thừa" giả
cp "$ROOT/.gitignore" "$TMP/.gitignore"
git -C "$TMP" -c init.defaultBranch=main init -q
printf -- '---\ntype: concept\ntitle: zz\n---\n# zz\n## Origin\nGH#76\n' > "$TMP/llmwiki/wiki/concepts/zz-gh76.md"
printf -- '---\ntype: concept\ntitle: yy\n---\n# yy\n## Origin\nGH#76\n' > "$TMP/fdk/wiki/concepts/yy-gh76.md"
python3 - "$TMP" <<'PY'
import importlib.util, io, os, sys, pathlib
root = sys.argv[1]; os.environ["CLAUDE_PROJECT_DIR"] = root
hooks = pathlib.Path(root) / "llmwiki" / ".claude" / "hooks"; sys.path.insert(0, str(hooks))
spec = importlib.util.spec_from_file_location("stop", hooks / "stop.py"); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for name in ("secondary_memory", "regen_docs"):
    setattr(m, name, lambda *a, **k: None)
m.framework_medic_mirror = lambda r: 0
m.wiki_changed = lambda r: True
# không assert all_wiki_dirs() tồn tại — test đo HÀNH VI, để bản stop.py cũ cũng đi tới assertion thật
if hasattr(m, "all_wiki_dirs"):
    assert len(m.all_wiki_dirs(root)) == 2, [str(p) for p in m.all_wiki_dirs(root)]
def run():
    sys.stdin = io.StringIO('{"session_id":"t"}')
    try: m.main()
    except SystemExit as e: return e.code
    return 0
idx_l = pathlib.Path(root, "llmwiki/wiki/index.md"); idx_f = pathlib.Path(root, "fdk/wiki/index.md")
rc = run()
assert "zz-gh76" in idx_l.read_text(encoding="utf-8"), "llmwiki/wiki KHÔNG được auto-index (bug GH#76 còn)"
assert "yy-gh76" in idx_f.read_text(encoding="utf-8"), "fdk/wiki không được auto-index"
assert rc == 0, f"stop exit {rc} sau khi đã tự chữa index"
n1 = idx_l.read_text(encoding="utf-8").count("zz-gh76"); run()
assert idx_l.read_text(encoding="utf-8").count("zz-gh76") == n1, "chạy 2 lần nhân đôi dòng index"
print("  \033[1;32m✓\033[0m auto-index chạy trên CẢ fdk/wiki lẫn llmwiki/wiki, exit 0, không nhân đôi (GH#76)")
PY
rc=$?; [ $rc -eq 0 ] && printf '\n\033[1m═══ stop-hook-all-wikis: \033[1;32mPASS\033[0m\033[0m\n' || printf '\n\033[1m═══ stop-hook-all-wikis: \033[1;31mFAIL\033[0m\033[0m\n'; exit $rc
