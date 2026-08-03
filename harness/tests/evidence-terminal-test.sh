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

printf '\n%d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
