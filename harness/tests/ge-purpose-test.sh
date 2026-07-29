#!/usr/bin/env bash
# ge-purpose-test.sh — TT8: từng thay đổi T1–T7 có làm ĐÚNG VIỆC NÓ SINH RA ĐỂ LÀM không.
#
# Khác mọi self-test đang có: self-test chứng minh "code chạy đúng như đã viết"; script này
# hỏi vế còn lại — "viết như thế có đạt mục đích không". Mỗi khối mở đầu bằng MỘT CÂU MỤC ĐÍCH
# viết thành lời, rồi tấn công nó bằng ca đối kháng (PDF §VII.2 xếp adversarial case ngang gold
# set). Khi một assert đỏ, cái vỡ là MỤC ĐÍCH ghi ở đầu khối, không phải một hàm nào đó.
#
# Mỗi khối có ít nhất một CONTROL — ca phải xanh/đỏ ngược lại — để một cài đặt luôn-từ-chối
# hoặc luôn-chấp-nhận không thể ăn điểm toàn khối.
#
# Sandbox tuyệt đối: mọi thứ ghi vào mktemp -d, dọn bằng trap. Repo thật chỉ được ĐỌC —
# không test nào tạo refs/hub/*, không test nào ghi harness/metrics/ của repo dev.
set -uo pipefail

SRC="${1:?usage: ge-purpose-test.sh <repo-root>}"
SRC=$(cd "$SRC" && pwd)
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
cd "$TMP"   # mọi đường dẫn tương đối lỡ tay đều rơi vào sandbox, không vào repo thật

LOOP="$SRC/harness/scripts/loop-runner.py"
HUB="$SRC/harness/scripts/hub.py"
GROUND="$SRC/harness/scripts/grounding-check.py"
GRAPH="$SRC/harness/scripts/wiki-graph.py"
BUDGET="$SRC/harness/scripts/token-budget.py"
PROV="$SRC/harness/scripts/provenance-log.py"

mkgit() {  # mkgit <dir> — repo dùng-một-lần có một commit mồi
  git init -q "$1"
  git -C "$1" config user.email purpose@test.local
  git -C "$1" config user.name "purpose test"
  git -C "$1" config commit.gpgsign false
  echo seed > "$1/out.txt"
  git -C "$1" add -A
  git -C "$1" commit -qm seed
}

# ───────────────────────────────────────────────────────────────────────────
hdr "T1 mục đích: 'giữ cái TỐT NHẤT, không phải cái CUỐI CÙNG' — metric nhiễu"
# Điểm đi theo dãy 5 → 9 → 3 → 4: đỉnh nằm ở GIỮA. Một vòng lặp chỉ "chạy đúng" mà không
# ratchet sẽ để lại workspace mang điểm 4 (cái cuối); ratchet đúng phải để lại điểm 9.
# Bộ đếm nằm NGOÀI repo (`$TMP/i`) — để trong repo thì `git reset --hard` của chính ratchet
# quay ngược nó và dãy điểm không bao giờ chạy hết.
mkgit "$TMP/w1"
cat > "$TMP/noisy.py" <<PY
import pathlib
c = pathlib.Path("$TMP/i")
i = int(c.read_text()) if c.is_file() else 0
c.write_text(str(i + 1))
s = [5, 9, 3, 4][i % 4]
pathlib.Path("$TMP/w1/out.txt").write_text(str(s) + "\n")
print(s)
PY
python3 "$LOOP" run --verify 'false' --metric-cmd "python3 $TMP/noisy.py" \
  --direction max --max-iter 3 --no-improve-k 0 --no-progress-k 0 \
  --log "$TMP/noisy.json" --cwd "$TMP/w1" >/dev/null 2>&1

read -r BEST NKEPT SEQ <<<"$(python3 - "$TMP/noisy.json" <<'PY'
import json, sys
its = json.load(open(sys.argv[1]))["iterations"]
loop = [i for i in its if i.get("ratchet") != "baseline"]
kept = [i for i in loop if i.get("ratchet") == "kept"]
best = max((i.get("score") or 0) for i in kept) if kept else -1
seq = ",".join(f"{i.get('score')}:{i.get('ratchet')}" for i in loop)
print(best, len(kept), seq or "-")
PY
)"
[ "$BEST" = "9.0" ] \
  && ok "đỉnh 9 (ở GIỮA dãy) được giữ — không trôi theo điểm cuối" \
  || bad "T1 mục đích" "kept cao nhất = $BEST, đáng lẽ 9.0 · dãy = $SEQ"
[ "$NKEPT" = "1" ] \
  && ok "đúng 1 vòng được keep; hai vòng tệ hơn (3, 4) đều reverted" \
  || bad "T1 mục đích" "có $NKEPT vòng kept, đáng lẽ 1 · dãy = $SEQ"
# Bằng chứng SỜ ĐƯỢC: thứ còn lại trên đĩa sau cả vòng lặp là bản tốt nhất, không phải bản cuối.
LEFT=$(tr -d '[:space:]' < "$TMP/w1/out.txt")
[ "$LEFT" = "9" ] \
  && ok "workspace còn lại mang điểm 9 (bản tốt nhất), không phải 4 (bản cuối)" \
  || bad "T1 mục đích" "workspace còn lại mang điểm $LEFT — ratchet không revert bản tệ"
HEAD1=$(git -C "$TMP/w1" rev-parse HEAD)
KEEPSHA=$(python3 -c "import json;print(json.load(open('$TMP/noisy.json'))['ratchet']['last_kept_commit'])")
[ "$HEAD1" = "$KEEPSHA" ] \
  && ok "HEAD đậu đúng commit của vòng tốt nhất" \
  || bad "T1 mục đích" "HEAD=$HEAD1 ≠ last_kept_commit=$KEEPSHA"

# ───────────────────────────────────────────────────────────────────────────
hdr "T7 mục đích: 'THẤT BẠI VẪN TRA CỨU ĐƯỢC' — sống sót qua git gc --prune=now"
# Ca đắt giá nhất của TT8. Một thí nghiệm BỎ ĐI rời khỏi mọi nhánh; nếu git dọn rác nuốt mất
# nó thì lời hứa "hub giữ lineage của cái đã bỏ" là rỗng. Có CONTROL: một commit anh em KHÔNG
# được push lên hub phải thật sự CHẾT sau cùng một lần gc — nếu nó cũng sống thì assert trên
# chẳng chứng minh được gì (gc chỉ đang nương tay).
mkgit "$TMP/w2"
echo tried > "$TMP/w2/tried.txt"; git -C "$TMP/w2" add -A; git -C "$TMP/w2" commit -qm tried
KEPT_SHA=$(git -C "$TMP/w2" rev-parse HEAD)
python3 "$HUB" push --agent purpose --hypothesis "ý bỏ đi: cache theo path" \
  --metric 0.1 --status discarded --root "$TMP/w2" >/dev/null
echo ctrl > "$TMP/w2/ctrl.txt"; git -C "$TMP/w2" add -A; git -C "$TMP/w2" commit -qm ctrl
CTRL_SHA=$(git -C "$TMP/w2" rev-parse HEAD)

git -C "$TMP/w2" reset -q --hard HEAD~2            # cả hai commit rời khỏi mọi nhánh
git -C "$TMP/w2" reflog expire --expire=now --all  # cắt luôn phao cứu sinh reflog
git -C "$TMP/w2" gc --prune=now --quiet >/dev/null 2>&1

if git -C "$TMP/w2" cat-file -e "$KEPT_SHA" 2>/dev/null; then
  ok "commit đã bỏ VẪN sống sau gc --prune=now — ref hub neo object lại"
else
  bad "T7 mục đích" "gc nuốt mất thí nghiệm đã bỏ ⇒ hub không giữ được lineage"
fi
if git -C "$TMP/w2" cat-file -e "$CTRL_SHA" 2>/dev/null; then
  bad "T7 control" "commit KHÔNG có ref hub cũng sống ⇒ gc đang nương tay, assert trên vô nghĩa"
else
  ok "control: commit không được hub neo thì CHẾT thật ⇒ chính ref hub là thứ cứu"
fi
NOTE=$(git -C "$TMP/w2" notes --ref=refs/notes/hub show "$KEPT_SHA" 2>/dev/null)
if printf '%s' "$NOTE" | python3 -c "
import json, sys
n = json.load(sys.stdin)
sys.exit(0 if n.get('status') == 'discarded' and 'cache theo path' in n.get('hypothesis', '') else 1)
" 2>/dev/null; then
  ok "notes sau gc còn đọc được cả giả thuyết lẫn status=discarded"
else
  bad "T7 mục đích" "metadata thí nghiệm mất sau gc — tra cứu được commit mà không biết nó là gì"
fi
python3 "$HUB" log --root "$TMP/w2" 2>/dev/null | grep -q "ý bỏ đi" \
  && ok "hub log sau gc vẫn liệt kê thí nghiệm đã bỏ" \
  || bad "T7 mục đích" "hub log không còn thấy node sau gc"

# ───────────────────────────────────────────────────────────────────────────
hdr "T4 mục đích: '\"nhìn ổn\" LÀ schema-invalid' — thử các biến thể lách"
# Verdict không có cấu trúc thì không phải feedback. Mỗi dòng dưới là một cách khác nhau để
# tỏ ra có cấu trúc mà thực chất rỗng; tất cả phải bị chặn bằng exit 2.
LEAKS=(
  '"LGTM"'
  '{"decision":"approve","claim":"  ","reason":"r"}'
  '{"decision":"revise","claim":"c","reason":"r","required_evidence":["  "]}'
  '{"decision":"ok","claim":"c","reason":"r"}'
  '["decision","approve"]'
  '{"decision":"revise","claim":"c","reason":"r","required_evidence":[]}'
)
for v in "${LEAKS[@]}"; do
  printf '%s' "$v" | python3 "$GROUND" --check - >/dev/null 2>&1
  if [ $? -eq 2 ]; then ok "chặn được biến thể lách: $v"
  else bad "T4 mục đích" "lọt biến thể lách (exit≠2): $v"; fi
done
# CONTROL — không có nó thì một validator luôn-từ-chối cũng ăn trọn khối trên.
printf '%s' '{"decision":"revise","claim":"paginate() sót phần tử cuối","reason":"off-by-one","required_evidence":["test qc-off-by-one ĐỎ"]}' \
  | python3 "$GROUND" --check - >/dev/null 2>&1
[ $? -eq 0 ] \
  && ok "control: verdict CÓ cấu trúc thật vẫn đi qua (không phải cổng chặn-tất-cả)" \
  || bad "T4 control" "verdict hợp lệ cũng bị chặn ⇒ cổng vô dụng, ai cũng sẽ tắt nó"

# ───────────────────────────────────────────────────────────────────────────
hdr "T2 mục đích: 'TRÍCH DẪN ĐƯỢC' — eid phải ổn định để câu trích còn giá trị"
# Một eid đổi theo lần dựng, theo đường dẫn, hay theo số trang trong wiki thì mọi câu trả lời
# có trích dẫn đều thối ngay hôm sau. Ba ca: dựng lại, đổi thư mục, và thêm một trang KHÔNG
# liên quan (bắt cài đặt đánh số cạnh theo chỉ mục thay vì theo nội dung).
mkwiki() {
  mkdir -p "$1/concepts"
  printf '%s\n' '# A' '' 'xem [[b]]' > "$1/concepts/a.md"
  printf '%s\n' '---' 'type: concept' 'relations:' '  - {rel: supports, to: a}' '---' '' '# B' \
    > "$1/concepts/b.md"
}
mkwiki "$TMP/wiki1"
mkwiki "$TMP/wiki2"
printf '%s\n' '# Z' '' 'trang la [[a]]' > "$TMP/wiki2/concepts/z.md"
cite_eid() { python3 "$GRAPH" cite a --wiki-dir "$1" | awk '$3=="->" && $4=="concepts/b.md" {print $1}'; }
E1=$(cite_eid "$TMP/wiki1")
E1B=$(cite_eid "$TMP/wiki1")
E2=$(cite_eid "$TMP/wiki2")
[ -n "$E1" ] && [ "$E1" = "$E1B" ] \
  && ok "eid ổn định giữa 2 lần dựng lại cùng wiki ($E1)" \
  || bad "T2 mục đích" "eid đổi giữa 2 lần dựng ($E1 vs $E1B) ⇒ trích dẫn vô nghĩa"
[ "$E1" = "$E2" ] \
  && ok "eid không đổi khi wiki ở thư mục khác và có thêm trang lạ" \
  || bad "T2 mục đích" "eid phụ thuộc đường dẫn/số trang ($E1 vs $E2) ⇒ trích cũ chết sau mỗi lần thêm trang"
python3 "$GRAPH" edge "$E1" --wiki-dir "$TMP/wiki2" 2>/dev/null | python3 -c "
import json, sys
e = json.load(sys.stdin)
sys.exit(0 if (e.get('from'), e.get('to')) == ('concepts/a.md', 'concepts/b.md') else 1)
" \
  && ok "eid tra ngược ra đúng cạnh a→b (trích dẫn resolve được, không phải chuỗi trang trí)" \
  || bad "T2 mục đích" "eid không resolve ngược ⇒ bằng chứng mức cạnh là giả"
# CONTROL — eid phải PHÂN BIỆT được cạnh, nếu không thì "ổn định" chỉ là một hằng số.
ESUP=$(python3 "$GRAPH" cite a --wiki-dir "$TMP/wiki1" | awk '$5=="(supports)" {print $1}')
[ -n "$ESUP" ] && [ "$ESUP" != "$E1" ] \
  && ok "control: cạnh khác (b→a supports) có eid khác — eid định danh thật, không phải hằng" \
  || bad "T2 control" "hai cạnh khác nhau dùng chung eid ⇒ trích dẫn không phân biệt được"

# ───────────────────────────────────────────────────────────────────────────
hdr "T5 mục đích: 'TRẦN PHẢI CHẶN ĐƯỢC, không chỉ cảnh báo' — công tắc có hiệu lực thật"
mkcfg() {  # mkcfg <dir> <mode> <verified>
  mkdir -p "$1/harness"
  printf '%s\n' "verified: $3" "mode: $2" 'budgets:' '  per_session_tokens: 100' \
    'rates:' '  default: {input: 0.003, output: 0.015}' > "$1/harness/token-budget.config.yaml"
  python3 "$BUDGET" record s1 --in 500 --out 500 --root "$1" >/dev/null 2>&1
}
mkcfg "$TMP/b_block" block true
python3 "$BUDGET" check s1 --root "$TMP/b_block" >/dev/null 2>&1
[ $? -eq 2 ] \
  && ok "mode:block + verified:true, vượt trần → exit 2 (CHẶN thật)" \
  || bad "T5 mục đích" "vượt trần ở mode block mà không exit 2 ⇒ trần chỉ là trang trí"
mkcfg "$TMP/b_warn" warn true
python3 "$BUDGET" check s1 --root "$TMP/b_warn" >/dev/null 2>&1
[ $? -eq 0 ] \
  && ok "mode:warn, vượt trần → exit 0 (công tắc có hai trạng thái khác nhau thật)" \
  || bad "T5 mục đích" "mode warn cũng chặn ⇒ không ai dám bật engine này"
mkcfg "$TMP/b_unver" block false
python3 "$BUDGET" check s1 --root "$TMP/b_unver" >/dev/null 2>&1
[ $? -eq 0 ] \
  && ok "mode:block nhưng verified:false → exit 0 (trần CHƯA hiệu chỉnh không được giết phiên)" \
  || bad "T5 mục đích" "trần chưa verified đã chặn ⇒ con số đoán mò cầm quyền sinh sát"
python3 "$BUDGET" record s2 --in 1 --out 1 --root "$TMP/b_block" >/dev/null 2>&1
python3 "$BUDGET" check s2 --root "$TMP/b_block" >/dev/null 2>&1
[ $? -eq 0 ] \
  && ok "control: phiên DƯỚI trần đi qua bình thường (không phải cổng chặn-tất-cả)" \
  || bad "T5 control" "phiên dưới trần cũng bị chặn"

# ───────────────────────────────────────────────────────────────────────────
hdr "T6 mục đích: 'AGENT SAU HỌC ĐƯỢC TỪ VIỆC AGENT TRƯỚC ĐÃ BỎ' (PDF §III.E)"
# Đọc bằng MỘT TIẾN TRÌNH RIÊNG, không chia sẻ bộ nhớ với bên ghi — đúng cảnh agent sau đọc
# sổ của agent trước. sleep 1 vì ts_utc chỉ tới giây; không tách giây thì phép sắp xếp
# mới-trước không kiểm được (và test sẽ xanh nhầm).
mkdir -p "$TMP/prov"
CLAUDE_CODE_SESSION_ID=w1 python3 "$PROV" post-hypothesis --root "$TMP/prov" \
  --text "gia thuyet A: giu lai" >/dev/null 2>&1
sleep 1
CLAUDE_CODE_SESSION_ID=w1 python3 "$PROV" post-hypothesis --root "$TMP/prov" --discarded \
  --text "gia thuyet B: da bo" --ref "llmwiki/wiki/draft/b.md" >/dev/null 2>&1
sleep 1
CLAUDE_CODE_SESSION_ID=w2 python3 "$PROV" post-hypothesis --root "$TMP/prov" --discarded \
  --text "gia thuyet C: da bo" --ref "llmwiki/wiki/draft/c.md" >/dev/null 2>&1

DISC=$(python3 "$PROV" read-hypotheses --discarded-only --root "$TMP/prov" 2>/dev/null)
[ "$(printf '%s\n' "$DISC" | grep -c 'da bo')" = "2" ] \
  && ok "tiến trình khác đọc được đủ 2 ý ĐÃ BỎ của 2 writer khác nhau" \
  || bad "T6 mục đích" "không đọc đủ ý đã bỏ: $DISC"
printf '%s\n' "$DISC" | grep -q 'giu lai' \
  && bad "T6 mục đích" "--discarded-only rò cả ý CÒN GIỮ ⇒ bộ lọc không có tác dụng" \
  || ok "--discarded-only lọc đúng: ý còn giữ KHÔNG lọt vào sổ ý đã bỏ"
[ "$(printf '%s\n' "$DISC" | head -1 | grep -c 'gia thuyet C')" = "1" ] \
  && ok "thứ tự mới-trước: ý bỏ gần nhất (C) đứng đầu" \
  || bad "T6 mục đích" "không phải mới-trước — agent sau đọc phải ý cũ nhất trước"
printf '%s\n' "$DISC" | grep -q 'llmwiki/wiki/draft/c.md' \
  && ok "mỗi ý đã bỏ mang theo --ref ⇒ lần ngược được về bối cảnh, không chỉ một dòng chữ" \
  || bad "T6 mục đích" "mất ref ⇒ agent sau biết 'ý này bỏ' mà không lần được vì sao"
ALL=$(python3 "$PROV" read-hypotheses --root "$TMP/prov" 2>/dev/null)
printf '%s\n' "$ALL" | grep -q 'giu lai' \
  && ok "control: đọc KHÔNG --discarded-only thấy đủ cả ý còn giữ (bộ lọc thật sự lọc)" \
  || bad "T6 control" "đọc đầy đủ cũng không thấy ý còn giữ ⇒ sổ mất dữ liệu"

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
