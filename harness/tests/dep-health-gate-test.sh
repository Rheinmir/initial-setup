#!/usr/bin/env bash
# Chặn hồi quy lớp lỗi "TỒN TẠI ≠ DÙNG ĐƯỢC".
#
# Bối cảnh: orientation từng quảng cáo code-graph dựa trên `.is_file()` của index.db.
# DB 0 byte / thiếu schema / server chết đều lọt, nên framework lùa MỌI phiên vào một
# tool hỏng suốt nhiều tuần (đo được: 37 tool-call so với 14 của grep).
#
# Khoá 3 bất biến:
#   (a) probe phân biệt được DB rỗng với DB có schema;
#   (b) cổng quảng cáo trong session_start ĐI QUA probe, không phải qua .is_file();
#   (c) fail-CLOSED — không thăm dò được thì KHÔNG quảng cáo (thà thiếu gợi ý còn hơn
#       lùa agent vào tool chết).
set -uo pipefail

SRC="${1:?usage: dep-health-gate-test.sh <repo-root>}"
cd "$SRC"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

PROBE="$SRC/harness/scripts/dep-health.py"
HOOK="$SRC/llmwiki/.claude/hooks/session_start.py"

hdr "(a) probe phân biệt được hỏng với lành"
if python3 "$PROBE" --self-test >/dev/null 2>&1; then
  ok "dep-health --self-test xanh"
else
  bad "dep-health --self-test" "self-test đỏ"
fi
[ "$(python3 "$PROBE" --json >/dev/null 2>&1; echo $?)" = 0 ] \
  && ok "--json luôn exit 0 (fail-open, không gãy phiên gọi)" \
  || bad "--json exit 0" "rc≠0"

hdr "(b) cổng quảng cáo đi qua PROBE, không qua .is_file()"
if grep -q "dep-health.py" "$HOOK"; then
  ok "session_start gọi dep-health để quyết định quảng cáo"
else
  bad "session_start gọi probe" "không thấy dep-health.py trong hook — cổng có thể đã bị hạ về kiểm file"
fi
# Bất biến thật: has_cg KHÔNG được gán từ một phép kiểm file.
if grep -nE '^\s*has_cg\s*=.*(is_file|exists)\(\)' "$HOOK" >/dev/null 2>&1; then
  bad "has_cg không gán từ kiểm file" "có dòng gán has_cg từ is_file()/exists() — đúng anti-pattern cũ"
else
  ok "has_cg KHÔNG gán từ is_file()/exists()"
fi

hdr "(c) fail-CLOSED khi không thăm dò được"
if grep -q 'has_cg = False  # không thăm dò được' "$HOOK"; then
  ok "probe lỗi → has_cg=False (KHÔNG quảng cáo)"
else
  bad "fail-closed" "không thấy nhánh đặt has_cg=False khi probe lỗi"
fi

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 1
