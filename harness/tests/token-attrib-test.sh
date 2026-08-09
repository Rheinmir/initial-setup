#!/usr/bin/env bash
# token-attrib-test.sh — quy trach nhiem token theo TUNG NGUON BOM phai dung va phai TAT DINH.
#
# Cai de sai nhat khong phai phep cong, ma la KHUECH DAI: mot khoi bom vao luot N ton
# `token × so_luot_con_lai`, khong phai `token`. Do that tren phien 1.305 luot: skill_listing
# 10.784 token bom 13 lan thanh 11,75 TRIEU token·luot. Bang dem thuong ghi 10 nghin — lech
# ba bac do lon va lai nguoi doc toi uu nham cho.
set -uo pipefail

SRC="${1:?usage: token-attrib-test.sh <repo-root>}"
SRC="$(cd "$SRC" && pwd)"
T="$SRC/harness/scripts/token-attrib.py"
PASS=0; FAIL=0; N=0
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }

[ -f "$T" ] || { echo "khong tim thay $T"; exit 1; }

python3 "$T" --self-test >/dev/null 2>&1 \
  && ok "self-test tat dinh PASS" \
  || bad "self-test" "that bai"

# fixture: 1 khoi bom o dau + 3 luot assistant -> khuech dai phai = tok × 3
python3 - "$TMP/t.jsonl" <<'PY'
import json, sys
rows = [
  {"type":"attachment","attachment":{"type":"nested_memory","displayPath":"llmwiki/CLAUDE.md",
                                     "content":"z"*4000}},
  {"type":"assistant","message":{"usage":{"cache_read_input_tokens":100}}},
  {"type":"assistant","message":{"usage":{"cache_read_input_tokens":100}}},
  {"type":"assistant","message":{"usage":{"cache_read_input_tokens":100}}},
]
open(sys.argv[1],"w").write("\n".join(json.dumps(r) for r in rows))
PY

out=$(python3 "$T" --transcript "$TMP/t.jsonl" --json 2>/dev/null)
amp=$(printf '%s' "$out" | python3 -c "
import json,sys
d=json.load(sys.stdin); s=d['sources']
k=[x for x in s if 'nested_memory' in x]
print(s[k[0]]['amp'] if k else -1)")
tok=$(printf '%s' "$out" | python3 -c "
import json,sys
d=json.load(sys.stdin); s=d['sources']
k=[x for x in s if 'nested_memory' in x]
print(s[k[0]]['tok'] if k else -1)")

[ "$tok" = "1000" ] \
  && ok "dem token dung (4000 ky tu / 4 = 1000)" \
  || bad "dem token" "got tok=$tok, want 1000"

[ "$amp" = "3000" ] \
  && ok "KHUECH DAI dung: tok × 3 luot con lai = 3000" \
  || bad "khuech dai" "got amp=$amp, want 3000 (neu = 1000 la quen nhan so luot)"

# nhan dien dung nguon nested_memory (nguon nang nhat), khong roi vao '(chua dat ten)'
printf '%s' "$out" | grep -q "nested_memory" \
  && ok "gan nhan dung nguon nested_memory (CLAUDE.md bom lai)" \
  || bad "gan nhan" "khong nhan ra attachment nested_memory"

# transcript khong doc duoc -> rc=3, KHONG duoc tra 0 (cong se hieu nham 'da do va sach')
python3 "$T" --transcript /khong/ton/tai.jsonl >/dev/null 2>&1
[ "$?" = "3" ] \
  && ok "transcript thieu → rc=3, khong gia bo da do" \
  || bad "ma thoat" "rc khac 3"

# hai lan chay tren cung fixture phai ra y het nhau (tat dinh, khong LLM)
a=$(python3 "$T" --transcript "$TMP/t.jsonl" --json 2>/dev/null | shasum -a1 | cut -c1-12)
b=$(python3 "$T" --transcript "$TMP/t.jsonl" --json 2>/dev/null | shasum -a1 | cut -c1-12)
[ "$a" = "$b" ] && [ -n "$a" ] \
  && ok "tat dinh: hai lan chay cho ket qua giong het" \
  || bad "tat dinh" "$a vs $b"

printf '\n%d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
