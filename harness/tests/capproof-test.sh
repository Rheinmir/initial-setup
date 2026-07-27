#!/usr/bin/env bash
# capproof-test — gate bắt "năng lực có mặt mà không chứng được còn sống" PHẢI tự chứng nó chạy.
# 4 chiều: nợ MỚI → đỏ · TỤT → đỏ · nợ tồn trong baseline → xanh · sandbox không đụng đồ thật.
# Bối cảnh: lớp missing-verification lặp 3 lần (auto-capture/delta/fire-drill) → capproof sinh ra
# để bắt nó; test này là fire-drill của chính capproof — gate nói dối tệ hơn không có gate.
set -u
ROOT="$(cd "${1:-.}" && pwd)"
BC="$ROOT/fdk/tools/build-capabilities.py"
fail=0
ok(){ printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
bad(){ printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

j(){ python3 "$BC" --root "$1" --capproof-json; }

# Sandbox = repo tối thiểu đủ cho resolver: skills/ + harness/tests + policy + scripts + fdk/tools
SB="$(mktemp -d)"
mkdir -p "$SB/skills/proven-sk" "$SB/skills/orphan-sk" "$SB/harness/tests" \
         "$SB/harness/scripts" "$SB/fdk/tools" "$SB/harness/metrics" "$SB/harness/poc-vendor-neutral"
# proven-sk THAM CHIẾU engine thật (để không rơi vào miễn trừ tier-7 no-engine khi test bị xoá
# ở bước "tụt" bên dưới) — proof của nó đến từ tier-3 (tên khớp file trong harness/tests/),
# KHÔNG phải từ chính dòng python3 này (engine đó thật ra không cần tồn tại cho tier 3).
printf -- '---\nname: proven-sk\ndescription: co test\n---\ndung: python3 harness/scripts/proven-sk-engine.py\n' > "$SB/skills/proven-sk/SKILL.md"
# orphan-sk THAM CHIẾU 1 engine giả (không tồn tại) — đại diện "skill CÓ code nhưng chưa có
# test", phân biệt với skill thuần-prompt (miễn trừ N/A, tier 7) — nếu bỏ dòng python3 này,
# orphan-sk sẽ rơi vào miễn trừ và test dưới đây sai oan.
printf -- '---\nname: orphan-sk\ndescription: khong co gi\n---\ndung: python3 harness/scripts/khong-ton-tai.py\n' > "$SB/skills/orphan-sk/SKILL.md"
printf 'echo proven-sk duoc test o day\n' > "$SB/harness/tests/proven-sk-test.sh"
# pure-prompt-sk: KHÔNG tham chiếu engine .py nào — skill thuần thẩm mỹ/hướng dẫn (root-cause
# 2026-07-18: 34/38 skill-unproven thật rơi đúng dạng này — brandkit/caveman-*/gpt-taste…).
mkdir -p "$SB/skills/pure-prompt-sk"
printf -- '---\nname: pure-prompt-sk\ndescription: mot skill thuan huong dan, khong dung engine nao\n---\n' > "$SB/skills/pure-prompt-sk/SKILL.md"
printf 'rules: []\n' > "$SB/harness/poc-vendor-neutral/policy.yaml"

# 1. resolver phân loại đúng: proven-sk có proof (tests), orphan-sk UNPROVEN
u=$(j "$SB" | python3 -c "import sys,json;print(','.join(json.load(sys.stdin)['unproven']))")
echo "$u" | grep -q "skill:orphan-sk" && ok "orphan-sk (có engine, chưa test) bị bêu UNPROVEN" || bad "orphan-sk lọt lưới ($u)"
echo "$u" | grep -q "skill:proven-sk" && bad "proven-sk bị bêu OAN" || ok "proven-sk được nhận proof (tests)"
echo "$u" | grep -q "skill:pure-prompt-sk" && bad "pure-prompt-sk (0 engine) bị bêu OAN — root-cause chưa fix" \
                                            || ok "pure-prompt-sk (0 engine) MIỄN TRỪ đúng (tier 7, không phải nợ giả)"

# 1b. shim os.execv mỏng → resolve qua proof của TARGET (tier 8), không đòi shim tự có test riêng
printf 'def self_test():\n    return 0\n' > "$SB/harness/scripts/fake-target.py"
printf -- '--self-test' >> "$SB/harness/scripts/fake-target.py"
printf 'import os, sys\n_T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fake-target.py")\nos.execv(sys.executable, [sys.executable, _T, *sys.argv[1:]])\n' > "$SB/harness/scripts/fake-shim.py"
u_shim=$(j "$SB" | python3 -c "import sys,json;print(','.join(json.load(sys.stdin)['unproven']))")
echo "$u_shim" | grep -q "script:fake-shim.py" && bad "shim mỏng bị bêu OAN — tier shim-delegate chưa hoạt động" \
                                                || ok "shim os.execv mỏng resolve qua proof của target (tier 8)"

# 2. baseline chốt nợ → logic ratchet XANH (nợ tồn không đỏ)
python3 "$BC" --root "$SB" --write-capproof-baseline >/dev/null
u2=$(j "$SB" | python3 -c "
import sys,json
cp=json.load(sys.stdin); base=json.load(open('$SB/harness/metrics/capproof-baseline.json'))
known=set(base['proven'])|set(base['unproven'])
new=[k for k in cp['unproven'] if k not in known]
dem=[k for k in cp['unproven'] if k in set(base['proven'])]
print('RED' if (new or dem) else 'GREEN')")
[ "$u2" = "GREEN" ] && ok "nợ tồn trong baseline → XANH (ratchet đúng chiều)" || bad "nợ tồn làm đỏ ($u2)"

# 3. thêm capability MỚI không proof → đỏ
mkdir -p "$SB/skills/new-orphan"; printf -- '---\nname: new-orphan\ndescription: x\n---\ndung: python3 harness/scripts/khong-ton-tai-2.py\n' > "$SB/skills/new-orphan/SKILL.md"
u3=$(j "$SB" | python3 -c "
import sys,json
cp=json.load(sys.stdin); base=json.load(open('$SB/harness/metrics/capproof-baseline.json'))
known=set(base['proven'])|set(base['unproven'])
print('RED' if [k for k in cp['unproven'] if k not in known] else 'GREEN')")
[ "$u3" = "RED" ] && ok "năng lực MỚI không proof → ĐỎ" || bad "nợ mới lọt ($u3)"

# 4. xoá proof của cái đã-proven → đỏ (TỤT)
rm "$SB/harness/tests/proven-sk-test.sh"
u4=$(j "$SB" | python3 -c "
import sys,json
cp=json.load(sys.stdin); base=json.load(open('$SB/harness/metrics/capproof-baseline.json'))
print('RED' if [k for k in cp['unproven'] if k in set(base['proven'])] else 'GREEN')")
[ "$u4" = "RED" ] && ok "proof bị xoá → ĐỎ (bắt tụt)" || bad "tụt không bị bắt ($u4)"

# 5. baseline THẬT của repo không bị đụng
git -C "$ROOT" diff --quiet -- harness/metrics/capproof-baseline.json 2>/dev/null \
  && ok "baseline thật nguyên vẹn" || bad "test đã đụng baseline thật!"
rm -rf "$SB"
[ "$fail" -eq 0 ] && { printf '\n\033[1m═══ capproof-test: \033[1;32mPASS\033[0m\033[0m\n'; exit 0; }
printf '\n\033[1m═══ capproof-test: \033[1;31m%d VI PHẠM\033[0m\033[0m\n' "$fail"; exit 1
