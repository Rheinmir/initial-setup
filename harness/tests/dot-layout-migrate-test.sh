#!/usr/bin/env bash
# dot-layout-migrate-test.sh — chứng minh migrate layout ẩn chạy đúng (6 assertion).
# Sandbox trong $TMPDIR, không đụng repo thật.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
INSTALL="$HERE/../poc-vendor-neutral/install.sh"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
pass=0
ck(){ if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "  ✓ $1"; else echo "  ✗ $1 (mong '$2', được '$3')"; exit 1; fi; }

# Trích ĐÚNG hàm migrate từ installer thật — test không được nhân bản logic.
extract(){ sed -n '/^migrate_dot_layout(){/,/^}/p' "$INSTALL"; }

run_migrate(){ # run_migrate <root>
  ROOT="$1"
  eval "log(){ :; }; warn(){ :; }"
  eval "$(extract)"
  migrate_dot_layout
}

# 1. Dự án chuẩn CŨ → dọn vào dấu chấm
P="$TMP/old"; mkdir -p "$P/llmwiki/wiki/concepts" "$P/harness/scripts" "$P/src"
echo "noi dung" > "$P/llmwiki/wiki/concepts/a.md"
mkdir -p "$P/.claude"
printf '{"hooks":{"SessionStart":[{"command":"python3 \\"$CLAUDE_PROJECT_DIR/llmwiki/.claude/hooks/session_start.py\\""}]}}\n' > "$P/.claude/settings.json"
printf 'llmwiki/html/*.png\n' > "$P/.gitignore"
( run_migrate "$P" ) >/dev/null 2>&1
ck "llmwiki/ được dọn vào .llmwiki/" "yes" "$([ -d "$P/.llmwiki" ] && [ ! -d "$P/llmwiki" ] && echo yes || echo no)"
ck "harness/ được dọn vào .harness/"  "yes" "$([ -d "$P/.harness" ] && [ ! -d "$P/harness" ] && echo yes || echo no)"
ck "nội dung không mất" "noi dung" "$(cat "$P/.llmwiki/wiki/concepts/a.md")"
ck "con trỏ hook được viết lại" "yes" \
   "$(grep -q '\.llmwiki/\.claude/hooks' "$P/.claude/settings.json" && echo yes || echo no)"
ck "gitignore được viết lại" "yes" \
   "$(grep -q '^\.llmwiki/html/' "$P/.gitignore" && echo yes || echo no)"

# 2. Chạy LẦN HAI trên cùng dự án → không đổi gì (idempotent)
before="$(cd "$P" && find . -maxdepth 2 | sort | md5)"
( run_migrate "$P" ) >/dev/null 2>&1
ck "chạy lại lần hai → im lặng, không đổi gì (idempotent)" "$before" "$(cd "$P" && find . -maxdepth 2 | sort | md5)"

# 3. Repo framework (có fdk/wiki) → KHÔNG BAO GIỜ tự migrate
F="$TMP/fw"; mkdir -p "$F/fdk/wiki" "$F/llmwiki/wiki" "$F/harness"
( run_migrate "$F" ) >/dev/null 2>&1
ck "repo framework giữ nguyên llmwiki/ (không tự migrate)" "yes" \
   "$([ -d "$F/llmwiki" ] && [ ! -d "$F/.llmwiki" ] && echo yes || echo no)"

echo "dot-layout-migrate-test: $pass/7 assertion XANH"
