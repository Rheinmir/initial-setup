#!/usr/bin/env bash
# ge-travel-test.sh — thay đổi mới có TỚI TAY người dùng mới không.
#
# Bài học repo (harness/downstream-contract.yaml): "xanh trong repo" ≠ "đúng ở downstream".
# Installer hardcode danh sách file, nên một engine dev xong, self-test xanh hết, vẫn có thể
# KHÔNG BAO GIỜ được ship. T4 (grounding-check.py) và T7 (hub.py + hub.config.yaml) là hai file
# MỚI của nhánh graph-engineering — chúng phải đi qua được cả hai đường cài thật.
#
# Khoá 5 bất biến:
#   (a) đường per-project: cài vào dự án TRỐNG thì engine mới có mặt trong harness/scripts/;
#   (b) đường NGƯỜI MỚI (travel-policy v4 = global-shared): engine + config tới ~/.claude/harness,
#       và HAI CHIỀU — thứ khai framework_only phải VẮNG khỏi global;
#   (c) travel-policy.yaml khớp installer THẬT, và cổng gác nó phải CẮN được (negative control
#       hai chiều: bịa drift ở phía policy và ở phía installer, cả hai phải đỏ);
#   (d) TỒN TẠI ≠ DÙNG ĐƯỢC — engine phải CHẠY ở downstream (bắt lớp lỗi "copy file, thiếu
#       phụ thuộc anh em"), chạy cả bản per-project lẫn bản global;
#   (e) cổng sẵn có (fresh-install-smoke --local, probe required của /fdk) không đỏ vì engine mới.
#
# HAI CHỖ LỆCH so với PLAN (làm theo CODE THẬT):
#   1. Config (*.yaml) KHÔNG travel theo đường per-project — installer chỉ copy harness/scripts/*.py,
#      policy.yaml, recipe.md, version.json. Đó là thiết kế v4 (engine dùng chung ở global), không
#      phải hồi quy của graph-engineering, nên assert config đặt ở đường GLOBAL.
#   2. travel-policy.yaml KHÔNG liệt kê đủ file (43/65 script được khai tên) — "hub.py không có
#      tên trong policy" là tính chất repo-wide sẵn có, không phải lỗi do T4/T7 gây ra. Assert
#      theo kiểu đó là bịa luật, nên chỗ này kiểm CỔNG có cắn hay không thay vì kiểm danh sách.
#
# SANDBOX: mọi thứ ghi vào mktemp -d. Đường global cũng bị nhốt bằng HOME=$TMP/home — test này
# KHÔNG được phép sửa ~/.claude/harness thật của máy đang chạy (installer --global ghi theo $HOME).
# CLAUDE_SKILLS_DIR/AGENTS_SKILLS_DIR vẫn trỏ HOME thật để assert "skill reachable" còn nói thật.
set -uo pipefail

SRC="${1:?usage: ge-travel-test.sh <repo-root>}"
SRC="$(cd "$SRC" && pwd)"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
REAL_HOME="$HOME"
NEW="$TMP/newproj"
GH="$TMP/home/.claude/harness"

# Engine mà nhánh graph-engineering đụng tới. hub.py (T7) + grounding-check.py (T4) là file MỚI;
# ba cái còn lại bị T1/T2/T5/T6 sửa — cả năm đều phải tới tay người dùng.
ENGINES="grounding-check.py hub.py token-budget.py provenance-log.py wiki-graph.py"
# Config đi CÙNG engine đọc nó. Thiếu config ⇒ engine chạy bằng fail-soft default, không phải
# giá trị đã hiệu chỉnh — im lặng sai còn tệ hơn gãy to.
CONFIGS="hub.config.yaml token-budget.config.yaml loop-runner.config.yaml"

hdr "(a) install per-project vào dự án TRỐNG"
mkdir -p "$NEW"
git init -q "$NEW"
if bash "$SRC/harness/scripts/install-harness.sh" "$NEW" >"$TMP/install.log" 2>&1; then
  ok "install-harness.sh <dự án trống> exit 0"
else
  bad "install per-project" "exit≠0 — xem $TMP/install.log (đã xoá khi test kết thúc)"
fi
for f in $ENGINES; do
  [ -f "$NEW/harness/scripts/$f" ] \
    && ok "per-project: $f tới dự án mới" \
    || bad "per-project: $f" "installer KHÔNG copy — người mới cài xong sẽ thiếu"
done

hdr "(b) đường NGƯỜI MỚI (travel-policy v4 = global-shared, engine ở ~/.claude/harness)"
if env HOME="$TMP/home" bash "$SRC/harness/scripts/install-harness.sh" --global >"$TMP/global.log" 2>&1; then
  ok "install-harness.sh --global exit 0 (nhốt trong HOME sandbox)"
else
  bad "install --global" "exit≠0 — xem $TMP/global.log"
fi
for f in $ENGINES; do
  [ -f "$GH/harness/scripts/$f" ] \
    && ok "global: $f tới ~/.claude/harness" \
    || bad "global: $f" "engine KHÔNG tới global — skill gọi nó sẽ gãy ở MỌI dự án"
done
for c in $CONFIGS; do
  [ -f "$GH/harness/$c" ] \
    && ok "global: $c đi cùng engine" \
    || bad "global: $c" "thiếu config ⇒ engine chạy với default lạ, không phải giá trị đã hiệu chỉnh"
done
# CHIỀU NGƯỢC: tầng 3 khai "chỉ chạy ở repo framework" thì phải VẮNG. Glob *.py của installer copy
# tất tay rồi mới gỡ theo STRIP_TIER3 — nếu ai đó xoá dòng gỡ, tầng 3 thành hư cấu mà không ai biết.
for f in fdk-gate.py harness-doctor.py sync-skills.py; do
  [ ! -f "$GH/harness/scripts/$f" ] \
    && ok "global: $f VẮNG đúng như khai framework_only" \
    || bad "framework_only rò rỉ: $f" "tool chỉ-dev vẫn xuống global — tầng 3 thành hư cấu"
done

hdr "(c) travel-policy.yaml là hợp đồng sống, và cổng gác nó phải CẮN được"
if python3 "$SRC/harness/validators/travel_policy_sync.py" --root "$SRC" >"$TMP/tps.log" 2>&1; then
  ok "travel-policy khớp install-harness.sh (2 chiều: leaked + missing + STRIP drift)"
else
  bad "travel-policy drift" "policy lệch installer: $(tr '\n' ' ' < "$TMP/tps.log" | cut -c1-160)"
fi
# NEGATIVE CONTROL — cổng luôn-xanh và cổng không-tồn-tại là một thứ. Bịa drift trên BẢN SAO trong
# sandbox (repo thật không bị chạm) rồi đòi validator phải exit 2. Hai chiều, vì hai chiều hỏng theo
# hai kiểu khác nhau: sửa policy mà quên installer, và ngược lại.
tamper_dir() {  # tamper_dir <đích> — dựng bản sao đủ để validator chạy
  mkdir -p "$1/harness/scripts"
  cp "$SRC/harness/scripts/install-harness.sh" "$1/harness/scripts/install-harness.sh"
  cp "$SRC/harness/travel-policy.yaml" "$1/harness/travel-policy.yaml"
}
# chiều 1: policy khai thêm một mục framework_only mà installer KHÔNG gỡ khỏi global
tamper_dir "$TMP/t1"
python3 - "$TMP/t1/harness/travel-policy.yaml" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
p.write_text(t.replace("framework_only:\n",
                       'framework_only:\n  harness/scripts/hub.py:  "bịa để thử cổng"\n', 1),
             encoding="utf-8")
PY
python3 "$SRC/harness/validators/travel_policy_sync.py" --root "$TMP/t1" >/dev/null 2>&1
[ $? -eq 2 ] \
  && ok "negative control: policy khai thêm tầng-3 mà installer không gỡ → validator exit 2" \
  || bad "cổng travel-policy câm (phía policy)" "sửa policy lệch installer mà validator vẫn xanh"
# chiều 2: installer thôi ship một engine ĐANG được policy khai global_shared (nhét vào STRIP_TIER3)
tamper_dir "$TMP/t2"
python3 - "$TMP/t2/harness/scripts/install-harness.sh" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
p.write_text(t.replace('STRIP_TIER3="\n',
                       'STRIP_TIER3="\nharness/scripts/wiki-graph.py\n', 1),
             encoding="utf-8")
PY
python3 "$SRC/harness/validators/travel_policy_sync.py" --root "$TMP/t2" >/dev/null 2>&1
[ $? -eq 2 ] \
  && ok "negative control: installer ngừng ship engine đã khai global → validator exit 2" \
  || bad "cổng travel-policy câm (phía installer)" "engine biến mất khỏi global mà validator vẫn xanh"

hdr "(d) TỒN TẠI ≠ DÙNG ĐƯỢC — engine phải chạy THẬT ở downstream"
for f in grounding-check.py hub.py; do
  if ( cd "$NEW" && python3 "harness/scripts/$f" --self-test ) >/dev/null 2>&1; then
    ok "per-project: $f --self-test PASS ngay tại dự án mới"
  else
    bad "per-project chạy: $f" "self-test đỏ ở downstream — copy được file nhưng thiếu phụ thuộc anh em"
  fi
done
for f in grounding-check.py hub.py; do
  if ( cd "$NEW" && python3 "$GH/harness/scripts/$f" --self-test ) >/dev/null 2>&1; then
    ok "global: $f --self-test PASS khi chạy trên dự án downstream"
  else
    bad "global chạy: $f" "bản global đỏ — engine dùng chung hỏng thì MỌI dự án hỏng"
  fi
done

hdr "(e) cổng sẵn có không đỏ vì engine mới (fresh-install-smoke --local)"
# Check này cố ý đọc GLOBAL SKILLS THẬT của máy đang chạy (CLAUDE_SKILLS_DIR trỏ REAL_HOME) —
# đúng cho máy dev đã cài skill qua /fdk-uat, nhưng CI runner sạch (vd GitHub Actions) không có
# global install nào để "không đỏ vì engine mới" — tiền đề của check không áp dụng, không phải
# hồi quy thật. Skip rõ ràng thay vì fail khi máy chưa có global skill nào.
if [ ! -d "$REAL_HOME/.claude/skills" ] || [ -z "$(ls -A "$REAL_HOME/.claude/skills" 2>/dev/null)" ]; then
  ok "fresh-install-smoke --local SKIP (máy chưa có global skill install để bảo vệ — vd CI runner sạch)"
elif env HOME="$TMP/home2" \
       CLAUDE_SKILLS_DIR="$REAL_HOME/.claude/skills" \
       AGENTS_SKILLS_DIR="$REAL_HOME/.agents/skills" \
       bash "$SRC/harness/scripts/fresh-install-smoke.sh" --local >"$TMP/smoke.log" 2>&1; then
  ok "fresh-install-smoke --local vẫn XANH (3 trụ + hợp đồng downstream + rule parity)"
else
  bad "fresh-install-smoke" "đỏ: $(grep -E '✗' "$TMP/smoke.log" | head -3 | tr '\n' ' ' | cut -c1-200)"
fi

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
