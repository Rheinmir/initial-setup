#!/usr/bin/env bash
# downstream-firedrill-test — CI downstream phải TỰ chứng rule gốc còn cắn, và chứng ĐÚNG CÁCH.
#
# Bối cảnh: harness-doctor (fire-drill bắt dark-rail) trước đây không wire xuống downstream →
# guardrail của framework có thể mục ruỗng mà CI downstream không kêu. Nay wire vào job validate.
# NHƯNG có một cái bẫy tất phải chặn: chạy fire-drill từ GLOBAL (~/.claude/harness) báo dark-rail
# GIẢ (global thiếu hooks/pre-commit của repo → side-effect rail R4/R8/R10/R17 = missing). Phải
# chạy từ CHECKOUT ĐẦY ĐỦ ($RUNNER_TEMP/harness-src mà CI đã clone) → 18/18 thật.
#
# Hai nửa:
#   1. step harness-doctor CÓ trong out/ci/harness.yml (đã ship xuống)
#   2. nó chạy từ harness-src (full repo), KHÔNG từ $HOME/.claude (global) → không đỏ giả
#
# Usage: bash harness/tests/downstream-firedrill-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
CI="$ROOT/harness/poc-vendor-neutral/out/ci/harness.yml"
GEN="$ROOT/harness/poc-vendor-neutral/gen-converters.py"
fail=0
ok()  { printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
bad() { printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

# out/ là build-artifact (gitignored) — install SINH nó tại chỗ rồi mới copy CI. Fresh
# checkout chưa có out/ → regen trước khi soi (idempotent, đúng như install.sh làm).
( cd "$ROOT/harness/poc-vendor-neutral" && python3 gen-converters.py >/dev/null 2>&1 ) \
  || bad "gen-converters.py chạy lỗi — không sinh được out/ci/harness.yml"
[ -f "$CI" ] || bad "không thấy out/ci/harness.yml sau regen"

# 1. fire-drill có mặt trong CI downstream đã sinh
grep -q 'harness-doctor.py" --ci' "$CI" 2>/dev/null \
  && ok "out/ci/harness.yml có step harness-doctor --ci (fire-drill đã ship xuống)" \
  || bad "CI downstream KHÔNG chạy fire-drill → dark rail của framework không nổi đỏ tại downstream"

# 2. chạy từ full checkout, KHÔNG từ global (bẫy đỏ-giả)
grep -q 'RUNNER_TEMP/harness-src/harness/scripts/harness-doctor.py" --ci' "$CI" 2>/dev/null \
  && ok "fire-drill chạy từ harness-src (full repo) → 18/18 thật" \
  || bad "fire-drill KHÔNG trỏ harness-src — nếu chạy từ global sẽ báo dark-rail GIẢ (R4/R8/R10/R17 missing)"

if grep -q 'HOME/.claude/harness/harness/scripts/harness-doctor.py" --ci' "$CI" 2>/dev/null; then
  bad "fire-drill trỏ \$HOME/.claude (global) — global thiếu hooks repo → CI đỏ giả mỗi PR"
else
  ok "fire-drill KHÔNG trỏ global (tránh đỏ-giả)"
fi

# 3. generator là nguồn — sửa output tay sẽ bị regen đè; đảm bảo generator cũng mang step
grep -q 'harness-doctor.py" --ci' "$GEN" 2>/dev/null \
  && ok "gen-converters.py (nguồn) mang step → regen không mất" \
  || bad "step chỉ có ở output, không ở generator → lần regen kế sẽ xoá mất"

# 4. harness-local fire-drill (phủ rule RIÊNG) cũng ship xuống — ENGINE luôn-mới, fail-open nếu vắng
grep -q 'harness-src/harness-local/run.py" firedrill' "$CI" 2>/dev/null \
  && ok "CI dùng ENGINE từ harness-src (run.py repo có thể bản cũ → mode lạ degrade về check ÂM THẦM)" \
  || bad "CI KHÔNG dùng engine harness-src → run.py cũ của repo sẽ degrade firedrill thành check"
grep -q 'HARNESS_LOCAL_DIR="\$PWD/harness-local"' "$CI" 2>/dev/null \
  && ok "engine trỏ HARNESS_LOCAL_DIR vào rules của repo (engine theo framework, rules theo dự án)" \
  || bad "thiếu HARNESS_LOCAL_DIR → engine soi nhầm rules của harness-src thay vì của repo"
grep -q '\[ -d harness-local \] ||' "$CI" 2>/dev/null \
  && ok "harness-local firedrill fail-open (vắng harness-local → skip, không đỏ)" \
  || bad "harness-local firedrill KHÔNG fail-open → dự án không có harness-local sẽ đỏ oan"

# 5. logic firedrill THẬT cắn: rule chết + rule thiếu fixtures đều phải FAIL (dùng run.py sống)
RUN="$ROOT/harness-local/run.py"
if [ -f "$RUN" ]; then
  SB="$(mktemp -d)"; LR="$SB/harness-local"; mkdir -p "$LR/validators"; cp "$RUN" "$LR/run.py"
  # rule sống + đủ fixtures → firedrill xanh
  printf 'import json,sys\ntry: ev=json.load(sys.stdin)\nexcept: sys.exit(0)\nif "TODO" in (ev.get("content") or ""): sys.exit(2)\nsys.exit(0)\n' > "$LR/validators/v.py"
  printf 'rules:\n  - id: P1\n    name: t\n    validator: harness-local/validators/v.py\n    fixtures:\n      bad:  { content: "TODO" }\n      good: { content: "ok" }\n' > "$LR/policy.yaml"
  python3 "$LR/run.py" firedrill >/dev/null 2>&1 && ok "firedrill: rule sống+fixtures → xanh" || bad "firedrill chặn nhầm rule sống"
  # rule chết (validator không chặn) → firedrill ĐỎ
  printf 'import sys; sys.exit(0)\n' > "$LR/validators/v.py"
  python3 "$LR/run.py" firedrill >/dev/null 2>&1; [ $? -eq 2 ] && ok "firedrill: rule CHẾT → đỏ (bắt dark rail rule riêng)" || bad "firedrill KHÔNG bắt rule chết"
  # rule thiếu fixtures → firedrill ĐỎ (blind-spot không im lặng)
  printf 'rules:\n  - id: P1\n    name: t\n    validator: harness-local/validators/v.py\n' > "$LR/policy.yaml"
  python3 "$LR/run.py" firedrill >/dev/null 2>&1; [ $? -eq 2 ] && ok "firedrill: thiếu fixtures → đỏ (không im lặng blind-spot)" || bad "firedrill bỏ qua rule thiếu fixtures"
  # HARNESS_LOCAL_DIR: engine ở NGOÀI thư mục rules vẫn soi đúng rules (chính cảnh CI harness-src)
  printf 'import json,sys\ntry: ev=json.load(sys.stdin)\nexcept: sys.exit(0)\nif "TODO" in (ev.get("content") or ""): sys.exit(2)\nsys.exit(0)\n' > "$LR/validators/v.py"
  printf 'rules:\n  - id: P1\n    name: t\n    validator: harness-local/validators/v.py\n    fixtures:\n      bad:  { content: "TODO" }\n      good: { content: "ok" }\n' > "$LR/policy.yaml"
  cp "$LR/run.py" "$SB/engine-elsewhere.py"
  HARNESS_LOCAL_DIR="$LR" python3 "$SB/engine-elsewhere.py" firedrill >/dev/null 2>&1 \
    && ok "HARNESS_LOCAL_DIR: engine ngoài thư mục vẫn soi đúng rules (cảnh CI engine-mới)" \
    || bad "HARNESS_LOCAL_DIR không hoạt động → CI engine harness-src soi nhầm/không thấy rules"
  rm -rf "$SB"
fi

if [ "$fail" -eq 0 ]; then
  printf '\n\033[1m═══ downstream-firedrill: \033[1;32mPASS\033[0m\033[0m\n'; exit 0
fi
printf '\n\033[1m═══ downstream-firedrill: \033[1;31m%d VI PHẠM\033[0m\033[0m\n' "$fail"; exit 1
