#!/usr/bin/env bash
# anti-idle-stop-test.sh — Stop hook phai CHAN dung khi provider cat luot bang refusal RONG.
#
# Boi canh (do 2026-08-06, phien CoopCons 59f19d72): mot so provider chen san cau
# "I'm sorry, but I cannot assist with that request." voi usage = 0 o MOI truong, trong khi
# luot binh thuong cung phien co trung vi 40.773 token. Refusal do ket thuc luot -> agent dung
# im cho nguoi go "continue" (do duoc 9 lan go tay, cach nhau 25-115 phut).
#
# Ranh gioi AN TOAN cua luat nay la `usage == 0`: refusal THAT cua model luon ton output token,
# nen ta khong bao gio de len mot loi tu choi co ly do.
set -uo pipefail

SRC="${1:?usage: anti-idle-stop-test.sh <repo-root>}"
SRC="$(cd "$SRC" && pwd)"
HOOK="$SRC/llmwiki/.claude/hooks/stop.py"
PASS=0; FAIL=0; N=0
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }

[ -f "$HOOK" ] || { echo "khong tim thay $HOOK"; exit 1; }

run_case() { # run_case <ten-file> -> in "True"/"False"
  python3 - "$SRC" "$1" <<'PY'
import sys
sys.path.insert(0, sys.argv[1] + "/llmwiki/.claude/hooks")
import stop
print(stop.provider_stall(sys.argv[2]))
PY
}

mk() { # mk <file> <text> <usage-json>
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys
path, text, usage = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
rows = [
  {"type": "assistant", "message": {"content": [{"type": "text", "text": "viec truoc do"}],
                                    "usage": {"input_tokens": 900, "output_tokens": 120}}},
  {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
  {"type": "assistant", "message": {"content": [{"type": "text", "text": text}], "usage": usage}},
]
with open(path, "w", encoding="utf-8") as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
PY
}

REF="I'm sorry, but I cannot assist with that request."

mk "$TMP/stall.jsonl" "$REF" '{"input_tokens":0,"output_tokens":0,"cache_read_input_tokens":0}'
[ "$(run_case "$TMP/stall.jsonl")" = "True" ] \
  && ok "refusal RONG (usage=0) → nhan dien la nhieu ha tang" \
  || bad "refusal rong" "khong nhan dien → agent van dung im"

# Ranh gioi quan trong nhat: refusal THAT (co token) KHONG duoc ep chay tiep.
mk "$TMP/real.jsonl" "$REF" '{"input_tokens":1200,"output_tokens":18}'
[ "$(run_case "$TMP/real.jsonl")" = "False" ] \
  && ok "refusal THAT (co token) → KHONG de len loi tu choi co ly do" \
  || bad "refusal that" "de len tu choi that — nguy hiem hon van de goc"

mk "$TMP/normal.jsonl" "Da xong viec, day la ket qua." '{"input_tokens":5000,"output_tokens":300}'
[ "$(run_case "$TMP/normal.jsonl")" = "False" ] \
  && ok "luot binh thuong → khong chan dung" \
  || bad "luot binh thuong" "chan nham luot hop le"

[ "$(run_case /khong/ton/tai.jsonl)" = "False" ] \
  && ok "fail-open: transcript khong doc duoc → khong chan" \
  || bad "fail-open" "ha tang loi ma van chan → pha phien"

[ "$(run_case "")" = "False" ] \
  && ok "fail-open: khong co transcript_path → khong chan" \
  || bad "fail-open rong" "chan khi khong co du lieu"

# Guard chong lap vo han phai con nguyen trong main().
grep -q 'payload.get("stop_hook_active")' "$HOOK" \
  && ok "guard stop_hook_active con nguyen (khong lap vo han)" \
  || bad "guard stop_hook_active" "MAT guard → block lap vo han"

printf '\n%d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
