#!/usr/bin/env bash
# Khoá: lint.md có bước diễn giải cờ recall-gap (khác cờ code-drift/stale đã có).
set -uo pipefail
SRC="${1:?usage: lint-recall-gap-doc-test.sh <repo-root>}"
LINT="$SRC/llmwiki/skills/wiki-loop/lint.md"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

hdr "(a) lint.md có bước 0c diễn giải recall-gap"
grep -q "0c\." "$LINT" && grep -q "recall-gap" "$LINT" \
  && ok "bước 0c tồn tại, nhắc đúng tên cờ recall-gap" \
  || bad "bước 0c" "grep '0c\.' hoặc 'recall-gap' không ra trong $LINT"

hdr "(b) nội dung nêu rõ KHÔNG tự động sửa (đúng Non-goals SPEC)"
grep -q "KHÔNG tự động" "$LINT" \
  && ok "có câu nói rõ không tự sửa/tự chèn — người/agent tự quyết" \
  || bad "non-goal" "thiếu câu khẳng định không tự động sửa trong $LINT"

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 1
