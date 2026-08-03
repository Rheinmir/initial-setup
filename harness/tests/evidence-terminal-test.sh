#!/usr/bin/env bash
# evidence-terminal-test.sh — R19: chuoi ket luan phai cham dut o chung cu XEM DUOC.
# Fixture XANH lay tu chuoi that phien 03/08 (OpenClaude tu dung agent). Bon fixture DO phu
# bon hinh dang bi cam. Ba ca cuoi gac CONG TAC theo khuon ge-killswitch-test.sh.
set -uo pipefail

SRC="${1:?usage: evidence-terminal-test.sh <repo-root>}"
SRC="$(cd "$SRC" && pwd)"
V="$SRC/harness/validators/evidence_terminal.py"
PASS=0; FAIL=0; N=0
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }

chain() { # chain <file> <noi-dung-yaml>
  { printf '# fixture\n\n```evidence-chain\n'; printf '%s\n' "$2"; printf '```\n'; } > "$1"
}
# O che do advisory rc luon 0; tin hieu THAT nam o stderr co dong [R19 evidence-terminal] hay khong.
flags() { python3 "$V" --check "$1" --root "$SRC" 2>&1 >/dev/null \
            | grep -c '\[R19 evidence-terminal\]' || true; }

XANH="$TMP/xanh.md"
chain "$XANH" '- id: C1
  claim: "agent tu dung giua viec"
  kind: inference
  because: [C2]
- id: C2
  claim: "luot bi cat boi refusal chen san, khong do model sinh"
  kind: inference
  because: [E1]
- id: E1
  claim: "11 luot refusal tong usage 0 token, 297 luot thuong trung vi 50477"
  kind: observed
  evidence:
    ref: "harness/policy.yaml"'
[ "$(flags "$XANH")" = "0" ] \
  && ok "fixture XANH: chuoi cham chung cu → khong bi bat" \
  || bad "fixture XANH" "bi bat nham"

NAMES=("ket thuc bang suy luan" "chuoi vong tron" "web thieu link/trich" "parametric don doc")
BODIES=(
'- id: C1
  claim: "a"
  kind: inference
  because: [C2]
- id: C2
  claim: "b"
  kind: inference
  because: []'
'- id: C1
  claim: "a"
  kind: inference
  because: [C2]
- id: C2
  claim: "b"
  kind: inference
  because: [C1]'
'- id: C1
  claim: "a"
  kind: inference
  because: [W1]
- id: W1
  claim: "b"
  kind: web
  evidence:
    url: "https://example.org/a"
    accessed: "2026-08-03"'
'- id: C1
  claim: "a"
  kind: inference
  because: [P1]
- id: P1
  claim: "b"
  kind: parametric
  evidence:
    origin: "RFC 6749 muc 4.1"
    unverified: true'
)
for i in "${!NAMES[@]}"; do
  f="$TMP/do-$i.md"; chain "$f" "${BODIES[$i]}"
  [ "$(flags "$f")" -ge 1 ] \
    && ok "fixture DO: ${NAMES[$i]} → bi bat" \
    || bad "fixture DO: ${NAMES[$i]}" "LOT — validator khong bat"
done

# ── ngoai le r19_meta: tai lieu DAY chinh dinh dang nay phai duoc mien ──
# Do 2026-08-03 truoc khi lat strict: 2/2 file co khoi trong corpus deu la tai lieu day dinh dang,
# ref trong vi du CO Y khong ton tai. Khong co ngoai le nay thi strict chan chinh docs cua luat.
META="$TMP/meta.md"
{ printf -- '---\ntype: concept\nr19_meta: true\n---\n\n```evidence-chain\n';
  printf -- '- id: C1\n  claim: "a"\n  kind: inference\n  because: [C2]\n';
  printf -- '- id: C2\n  claim: "b"\n  kind: inference\n  because: []\n';
  printf '```\n'; } > "$META"
[ "$(flags "$META")" = "0" ] \
  && ok "r19_meta: tai lieu day dinh dang duoc mien, khong bi bat" \
  || bad "r19_meta" "tai lieu meta van bi bat → strict se chan chinh docs cua luat"

NOMETA="$TMP/nometa.md"
{ printf -- '---\ntype: concept\n---\n\n```evidence-chain\n';
  printf -- '- id: C1\n  claim: "a"\n  kind: inference\n  because: [C2]\n';
  printf -- '- id: C2\n  claim: "b"\n  kind: inference\n  because: []\n';
  printf '```\n'; } > "$NOMETA"
[ "$(flags "$NOMETA")" -ge 1 ] \
  && ok "khong khai r19_meta thi VAN bi bat (ngoai le khong bi lam dung)" \
  || bad "r19_meta khong khai" "mien nham — ngoai le dang mo qua rong"

# ── cong tac 3 tang (khuon ge-killswitch-test.sh: cong tac co THAT + de duoc config) ──
DO0="$TMP/do-0.md"

out=$(python3 "$V" --check "$DO0" --root "$SRC" --no-evidence-chain 2>&1 >/dev/null)
{ [ "$(printf '%s' "$out" | grep -c 'DANG TAT')" -ge 1 ] \
  && [ "$(printf '%s' "$out" | grep -c "la 'C2' khong phai diem cuoi")" = "0" ]; } \
  && ok "cong tac: co --no-evidence-chain tat luat + VAN bao dang tat" \
  || bad "cong tac co CLI" "khong tat, hoac tat im lang"

out=$(OVERSTACK_EVIDENCE_TERMINAL=0 python3 "$V" --check "$DO0" --root "$SRC" 2>&1 >/dev/null)
[ "$(printf '%s' "$out" | grep -c 'OVERSTACK_EVIDENCE_TERMINAL')" -ge 1 ] \
  && ok "cong tac: env tat luat + bao dung TANG da tat" \
  || bad "cong tac env" "khong tat hoac khong noi ro tang"

[ "$(flags "$DO0")" -ge 1 ] \
  && ok "cong tac co THAT: khong tat thi luat van bat (khong phai khoa trang tri)" \
  || bad "cong tac co that" "luat khong bat ke ca khi dang bat"

# ── ban DEPLOY tier-2 phai suy dung goc repo ──
# Do 2026-08-03: ROOT = parents[2] dung cho ban canonical harness/validators/, nhung installer con
# copy validator sang llmwiki/.claude/hooks/validators/. O do parents[2] tro ra llmwiki/.claude ->
# khong thay config -> roi ve fallback advisory -> LUAT TU TAT o ban deploy ma khong ai biet.
# Dung lop loi da ghi trong [[decision-anchoring]]: suy root theo VI TRI BAN DANG CHAY.
DEPLOY="$SRC/llmwiki/.claude/hooks/validators/evidence_terminal.py"
if [ -f "$DEPLOY" ]; then
  got=$(python3 -c "
import sys; sys.path.insert(0, '$SRC/llmwiki/.claude/hooks/validators')
import evidence_terminal as e
print(e.load_cfg(e.ROOT_DEFAULT).get('strictness'), e.ROOT_DEFAULT)" 2>/dev/null)
  want=$(python3 -c "
import sys; sys.path.insert(0, '$SRC/harness/validators')
import evidence_terminal as e
print(e.load_cfg(e.ROOT_DEFAULT).get('strictness'), e.ROOT_DEFAULT)" 2>/dev/null)
  [ -n "$got" ] && [ "$got" = "$want" ] \
    && ok "ban deploy tier-2 suy dung goc repo + doc dung config nhu ban canonical" \
    || bad "ban deploy tier-2" "deploy='$got' vs canonical='$want' — luat co the tu tat o ban deploy"
else
  printf '  \033[1;33mSKIP\033[0m  ban deploy tier-2 chua co (chua chay install-harness)\n'
fi

printf '\n%d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
