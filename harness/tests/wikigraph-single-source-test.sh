#!/usr/bin/env bash
# Khoá: CHỈ MỘT nguồn chân lý cho "cái gì link tới cái gì".
#
# Bối cảnh: hai công cụ trả lời cùng câu hỏi đó bằng hai regex độc lập, không chia sẻ
# dòng code nào — harness/scripts/wiki-graph.py (query cho agent) và
# fdk/tools/build-wiki-graph.py (vẽ cho người). Đo 2026-07-20: LỆCH THẬT 208 vs 164 cạnh,
# và mỗi bên sai một kiểu khác nhau nên không thể chọn bừa một bên làm chuẩn:
#   · wiki-graph.py không bỏ code-fence → [[...]] trong ví dụ code thành cạnh thật
#   · build-wiki-graph.py bỏ code-fence đúng nhưng giữ nguyên [[trang#anchor]] →
#     sinh cạnh trỏ tới một trang không tồn tại
set -uo pipefail

SRC="${1:?usage: wikigraph-single-source-test.sh <repo-root>}"
cd "$SRC"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

WG="$SRC/harness/scripts/wiki-graph.py"
BG="$SRC/fdk/tools/build-wiki-graph.py"

hdr "(a) hàm dùng chung xử đúng cả hai lớp lỗi"
OUT=$(python3 - "$WG" <<'PY'
import importlib.util, sys, pathlib
s = importlib.util.spec_from_file_location("_wg", pathlib.Path(sys.argv[1]))
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
demo = "body [[alpha]] [[beta#muc]] [[gamma|nhan]]\n```\n[[trong-code]]\n```\n`[[inline]]`"
print(",".join(m.wikilink_targets(demo)))
PY
)
[ "$OUT" = "alpha,beta,gamma" ] \
  && ok "cắt #anchor, cắt |alias, BỎ [[...]] trong code-fence và inline-code" \
  || bad "trích wikilink" "kỳ vọng 'alpha,beta,gamma', nhận '$OUT'"

hdr "(b) chỉ MỘT nơi định nghĩa phép trích"
grep -q "def wikilink_targets" "$WG" \
  && ok "wiki-graph.py giữ hàm chuẩn wikilink_targets()" \
  || bad "hàm chuẩn" "wiki-graph.py không còn định nghĩa wikilink_targets"
grep -q "wikilink_targets" "$BG" \
  && ok "build-wiki-graph.py GỌI hàm chuẩn (không tự chế lại)" \
  || bad "dùng chung" "build-wiki-graph.py không tham chiếu wikilink_targets — đã tách đôi trở lại"

hdr "(c) fail-open: thiếu harness thì vẫn vẽ được"
grep -q "_wg = None" "$BG" \
  && ok "nạp hỏng → rơi về regex local, không gãy" \
  || bad "fail-open" "không thấy nhánh dự phòng khi không nạp được wiki-graph.py"

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 1
