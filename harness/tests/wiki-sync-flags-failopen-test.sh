#!/usr/bin/env bash
# T1 — cờ code-drift phải tới được ĐƯỜNG ĐỌC (/query), và không bao giờ làm gãy nó.
# Khoá 2 chiều: (a) trang có cờ → CẢNH BÁO hiện ra (không im lặng trả tri thức cũ);
#               (b) mọi trạng thái hỏng của stale.json → exit 0, không output rác (fail-open).
set -uo pipefail

SRC="${1:?usage: wiki-sync-flags-failopen-test.sh <repo-root>}"
cd "$SRC"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

SYNC="$SRC/harness/scripts/wiki-sync.py"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
W="$TMP/wiki"; mkdir -p "$W/concepts"
echo "noop" > "$W/concepts/alpha.md"

run() { python3 "$SYNC" --wiki-dir "$W" --flags-for "$1" 2>&1; }
rc()  { python3 "$SYNC" --wiki-dir "$W" --flags-for "$1" >/dev/null 2>&1; echo $?; }

hdr "(a) cờ tới được đường đọc"
cat > "$W/stale.json" <<'JSON'
{"concepts/alpha.md": {"by": "harness/scripts/foo.py", "action": "code-drift",
 "ts": "2026-07-19T10:00:00", "session": null}}
JSON
out="$(run 'alpha')"
case "$out" in *"CẢNH BÁO DRIFT"*) ok "trang có cờ → cảnh báo (khớp theo slug)";;
  *) bad "trang có cờ → cảnh báo" "không thấy cảnh báo, out=<$out>";; esac
case "$(run 'concepts/alpha.md')" in *"CẢNH BÁO DRIFT"*) ok "khớp theo relpath đầy đủ";;
  *) bad "khớp theo relpath" "không khớp";; esac
case "$(run 'alpha')" in *"foo.py"*) ok "cảnh báo nêu file code gây drift";;
  *) bad "cảnh báo nêu nguyên nhân" "thiếu tên file trong output";; esac
out="$(run 'beta')"
[ -z "$out" ] && ok "trang KHÔNG có cờ → im lặng (không cảnh báo giả)" \
              || bad "trang sạch phải im" "out=<$out>"

hdr "(b) fail-open — đường đọc không bao giờ gãy"
[ "$(rc 'alpha')" = 0 ] && ok "ca thường → exit 0" || bad "ca thường exit 0" "rc=$(rc 'alpha')"
echo '{ this is not json' > "$W/stale.json"
[ "$(rc 'alpha')" = 0 ] && ok "stale.json HỎNG → exit 0" || bad "json hỏng" "rc≠0"
[ -z "$(run 'alpha')" ] && ok "stale.json hỏng → không nôn rác ra câu trả lời" \
                       || bad "json hỏng phải im" "có output"
echo '["mảng chứ không phải object"]' > "$W/stale.json"
[ "$(rc 'alpha')" = 0 ] && ok "stale.json sai KIỂU → exit 0" || bad "sai kiểu" "rc≠0"
rm -f "$W/stale.json"
[ "$(rc 'alpha')" = 0 ] && ok "stale.json THIẾU → exit 0" || bad "thiếu file" "rc≠0"
[ "$(python3 "$SYNC" --wiki-dir "$TMP/khong-ton-tai" --flags-for 'alpha' >/dev/null 2>&1; echo $?)" = 0 ] \
  && ok "wiki-dir KHÔNG tồn tại → exit 0" || bad "wiki-dir thiếu" "rc≠0"
[ "$(rc '')" = 0 ] && ok "danh sách trang RỖNG → exit 0" || bad "pages rỗng" "rc≠0"

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 1
