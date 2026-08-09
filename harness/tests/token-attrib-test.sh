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

# --agents: tach chi phi LUONG CHINH vs AGENT CON. Agent con chay o transcript RIENG nen moi
# bang do phien-chinh deu bo sot. Do that 15 du an: Claude Code 0,7-31%, OpenClaude 47-69%.
# Dung HOME GIA: --agents tra ~/.claude/projects/<slug-cua-cwd>, khong phai thu muc cwd.
FAKE="$TMP/home"; WORK="$TMP/work"; mkdir -p "$WORK"
# pwd -P: macOS resolve /var -> /private/var, ma script dung Path.resolve(). Tinh slug tu duong
# dan DA RESOLVE, neu khong test se tro nham thu muc va bao "khong ra bang" mot cach oan uong.
WORKP="$(cd "$WORK" && pwd -P)"
SLUG="-$(printf '%s' "${WORKP#/}" | tr '/' '-')"
SUBD="$FAKE/.claude/projects/$SLUG/subagents"; mkdir -p "$SUBD"
python3 - "$FAKE/.claude/projects/$SLUG" <<'PY2'
import json, sys, pathlib
d = pathlib.Path(sys.argv[1])
def w(p, out, cr):
    p.write_text(json.dumps({"type": "assistant", "message": {"usage":
        {"output_tokens": out, "cache_read_input_tokens": cr}}}) + "\n")
w(d / "main.jsonl", 100, 1000)
w(d / "subagents" / "a1.jsonl", 200, 2000)
PY2
out=$(cd "$WORK" && HOME="$FAKE" python3 "$T" --agents 2>&1)

printf '%s' "$out" | grep -q "LUỒNG CHÍNH" \
  && ok "--agents in duoc bang main vs subagent" \
  || bad "--agents" "khong ra bang"

# trong so: main out=100,cr=1000 -> 100*5 + 1000*0.1 = 600. Cong tho 4 so se ra 1100 -> sai.
printf '%s' "$out" | grep -q "600" \
  && ok "trong so chi phi dung (output x5, cache_read x0.1)" \
  || bad "trong so" "khong thay 600 — cong tho 4 con so la so sai"

# agent con o day dat hon main (200*5+2000*0.1=1200 vs 600) -> phai canh bao >40%
printf '%s' "$out" | grep -q "agent con nuot\|agent con nuốt" \
  && ok "canh bao khi agent con nuot >40% chi phi" \
  || bad "canh bao agent con" "khong canh bao du chiem 67%"

printf '\n%d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
