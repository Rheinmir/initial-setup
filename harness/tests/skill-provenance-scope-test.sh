#!/usr/bin/env bash
# skill-provenance-scope-test — gap #4 (senior-lens 2026-07-18): skill NGOÀI chạy full-permission
# sau khi cài, không ai re-verify theo nhịp. medic probe `provenance` gác — nhưng phải gác ĐÚNG PHẠM
# VI: hard-fail khi skill external-pull bị sửa lén sau khi pin (tamper thật), KHÔNG hard-fail khi
# skill local-authored đổi (dev churn hàng ngày — mọi phiên sửa SKILL.md). Sai phạm vi = "gate cries
# wolf" (đỏ vĩnh viễn vì churn bình thường) HOẶC mù (bỏ sót tamper thật) — cả hai đều làm gate vô dụng.
set -u
ROOT="$(cd "${1:-.}" && pwd)"
SP="$ROOT/fdk/tools/skill-provenance.py"
fail=0
ok(){ printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
bad(){ printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

# 1. --json phân biệt được external-pull vs local-authored (điều kiện tiên quyết để scope đúng)
python3 "$SP" check --json 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
has_ext = any(r.get('adapt_mode') == 'external-pull' for r in d['rows'])
has_local = any(r.get('adapt_mode') != 'external-pull' for r in d['rows'])
sys.exit(0 if has_ext and has_local else 1)
" && ok "--json phân biệt được external-pull và local-authored" \
  || bad "--json thiếu 1 trong 2 loại — không thể scope đúng"

# 2. Sandbox: tamper 1 skill GIẢ external-pull → probe phải ĐỎ, không đụng repo thật
SB="$(mktemp -d)"
mkdir -p "$SB/skills/fake-ext" "$SB/skills/fake-local" "$SB/harness/metrics" "$SB/fdk"
printf -- '---\nname: fake-ext\ndescription: x\n---\nbody v1\n' > "$SB/skills/fake-ext/SKILL.md"
printf -- '---\nname: fake-local\ndescription: x\n---\nbody v1\n' > "$SB/skills/fake-local/SKILL.md"
cp "$ROOT/fdk/tools/skill-provenance.py" "$SB/sp.py"
sed -i.bak "s|REPO = Path(__file__).resolve().parents\[2\]|REPO = Path('$SB')|" "$SB/sp.py" 2>/dev/null || \
  sed -i "s|REPO = Path(__file__).resolve().parents\[2\]|REPO = Path('$SB')|" "$SB/sp.py"
python3 "$SB/sp.py" record fake-ext --source "https://example.com/fake-ext"
python3 "$SB/sp.py" record fake-local --source local-authored
[ -f "$SB/fdk/skills.provenance.json" ] || bad "setup hỏng: record không ghi được store (sandbox thiếu dir?)"
# adapt_mode không được ghi bởi `record` (tool hiện tại) — set tay để mô phỏng entry external-pull thật
python3 -c "
import json
p = '$SB/fdk/skills.provenance.json'
d = json.load(open(p))
d['skills']['fake-ext']['adapt_mode'] = 'external-pull'
json.dump(d, open(p, 'w'))
"

judge() {  # in RED|GREEN theo đúng logic scoped của medic p_provenance
  python3 "$SB/sp.py" check --json 2>/dev/null | python3 -c "
import sys, json
rows = json.load(sys.stdin)['rows']
bad = [r for r in rows if r.get('adapt_mode') == 'external-pull' and r['status'] == 'MODIFIED']
print('RED' if bad else 'GREEN')"
}

[ "$(judge)" = "GREEN" ] && ok "trạng thái sạch ban đầu → GREEN" || bad "sai ngay từ đầu (setup lỗi)"

echo 'body v2 — sua len' > /tmp/_tamper_local; cat "$SB/skills/fake-local/SKILL.md" /tmp/_tamper_local > /tmp/_x && mv /tmp/_x "$SB/skills/fake-local/SKILL.md"
[ "$(judge)" = "GREEN" ] && ok "local-authored đổi (dev churn) → vẫn GREEN, không cries-wolf" \
                         || bad "local churn làm đỏ oan — gate sẽ bị tắt vì nhiễu"

cat "$SB/skills/fake-ext/SKILL.md" /tmp/_tamper_local > /tmp/_x && mv /tmp/_x "$SB/skills/fake-ext/SKILL.md"
[ "$(judge)" = "RED" ] && ok "external-pull bị sửa lén sau khi pin → RED (tamper thật bị bắt)" \
                       || bad "tamper skill NGOÀI không bị bắt — lỗ supply-chain vẫn mở"
rm -f /tmp/_tamper_local
rm -rf "$SB"

# 3. Repo thật không bị đụng (probe chỉ đọc, self-test không side-effect)
git -C "$ROOT" status --porcelain -- skills/ 2>/dev/null | grep -q . \
  && bad "test làm bẩn skills/ của repo thật!" || ok "repo thật (skills/) nguyên vẹn sau test"

[ "$fail" -eq 0 ] && { printf '\n\033[1m═══ skill-provenance-scope: \033[1;32mPASS\033[0m\033[0m\n'; exit 0; }
printf '\n\033[1m═══ skill-provenance-scope: \033[1;31m%d VI PHẠM\033[0m\033[0m\n' "$fail"; exit 1
