#!/usr/bin/env bash
# patterns-guard-test — R14 patterns-protected: kho pattern llmwiki/patterns/ chỉ sửa khi user
# cho phép (env LLMWIKI_PATTERNS_UNLOCK=1). "raw/ nhưng thấp hơn một bậc": agent không tự ý sửa.
#
# Usage: bash harness/tests/patterns-guard-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
V="$ROOT/harness/validators/patterns_guard.py"
pass=0; fail=0
ok(){  printf '  \033[1;32m✓\033[0m %s\n' "$1"; pass=$((pass+1)); }
bad(){ printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }
ev(){ printf '{"action":"write","file_path":"%s","content":"x"}' "$1"; }
bev(){ printf '{"action":"bash","command":"%s"}' "$1"; }

[ -f "$V" ] || { bad "thiếu patterns_guard.py"; printf '\n1 FAIL\n'; exit 1; }
unset LLMWIKI_PATTERNS_UNLOCK

ev   "llmwiki/patterns/frontend.md" | python3 "$V" >/dev/null 2>&1; [ $? -eq 2 ] && ok "CHẶN write vào patterns/ (không unlock)" || bad "không chặn write patterns/"
ev   "llmwiki/patterns/frontend.md" | LLMWIKI_PATTERNS_UNLOCK=1 python3 "$V" >/dev/null 2>&1; [ $? -eq 0 ] && ok "CHO write khi unlock=1 (user cho phép)" || bad "chặn nhầm khi unlock"
ev   "llmwiki/wiki/concepts/x.md"   | python3 "$V" >/dev/null 2>&1; [ $? -eq 0 ] && ok "CHO write file KHÁC (wiki) — chỉ gác patterns/" || bad "chặn nhầm file ngoài patterns/"
ev   ".llmwiki/patterns/frontend.md" | python3 "$V" >/dev/null 2>&1; [ $? -eq 2 ] && ok "CHẶN write vào .llmwiki/patterns/ (layout dot, GH#112)" || bad "không chặn write .llmwiki/patterns/"
ev   "src/llmwiki/patterns-old/x.md" | python3 "$V" >/dev/null 2>&1; [ $? -eq 0 ] && ok "CHO 'patterns-old/' (không phải kho pattern)" || bad "chặn nhầm patterns-old/"
bev  "echo hi > llmwiki/patterns/loops.md" | python3 "$V" >/dev/null 2>&1; [ $? -eq 2 ] && ok "CHẶN bash redirect vào patterns/" || bad "không chặn bash ghi patterns/"
bev  "cat llmwiki/patterns/loops.md"       | python3 "$V" >/dev/null 2>&1; [ $? -eq 0 ] && ok "CHO bash ĐỌC patterns/ (cat)" || bad "chặn nhầm đọc patterns/"
python3 "$V" "llmwiki/patterns/pm.md" >/dev/null 2>&1; [ $? -eq 2 ] && ok "CHẶN argv file-mode (pre-commit) vào patterns/" || bad "không chặn file-mode"
LLMWIKI_PATTERNS_UNLOCK=1 python3 "$V" "llmwiki/patterns/pm.md" >/dev/null 2>&1; [ $? -eq 0 ] && ok "CHO file-mode khi unlock" || bad "chặn nhầm file-mode unlock"

printf '\n\033[1m═══ TỔNG: %d test — \033[1;32m%d PASS\033[0m / \033[1;31m%d FAIL\033[0m\033[0m\n' "$((pass+fail))" "$pass" "$fail"
[ "$fail" -eq 0 ]
