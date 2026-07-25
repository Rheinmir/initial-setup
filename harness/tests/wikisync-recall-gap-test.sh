#!/usr/bin/env bash
# Khoá: wiki-sync --check phát cờ "recall-gap" khi code đổi mà 0 trang nào touches,
# TÁCH khỏi cờ "stale"/code-drift hiện có (action khác nhau, cùng stale.json).
set -uo pipefail

SRC="${1:?usage: wikisync-recall-gap-test.sh <repo-root>}"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
REPO="$TMP/repo"
mkdir -p "$REPO/llmwiki/wiki/concepts" "$REPO/harness/scripts" "$REPO/code"
cp "$SRC/harness/scripts/wiki-graph.py" "$REPO/harness/scripts/wiki-graph.py"
cp "$SRC/harness/scripts/wiki-sync.py"  "$REPO/harness/scripts/wiki-sync.py"

cd "$REPO"
git init -q
git config user.email t@t.com
git config user.name t

echo "print(1)" > code/touched.py
echo "print(2)" > code/orphan.py
cat > llmwiki/wiki/concepts/demo.md <<'EOF'
---
type: concept
---
# Demo
Liên quan `code/touched.py`.
EOF
git add -A && git commit -q -m init

python3 harness/scripts/wiki-sync.py --root "$REPO" --mark-synced >/dev/null

echo "print(3)" >> code/touched.py
echo "print(4)" >> code/orphan.py
git add -A

hdr "(a) recall-gap chỉ cờ file KHÔNG được touches, KHÔNG cờ file có touches"
python3 harness/scripts/wiki-sync.py --root "$REPO" --check >/dev/null 2>&1
STALE="$REPO/llmwiki/wiki/stale.json"
python3 - "$STALE" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("code/orphan.py", {}).get("action") == "recall-gap", d
assert d.get("code/touched.py", {}).get("action") != "recall-gap", d
PY
if [ $? -eq 0 ]; then
  ok "orphan.py bị cờ recall-gap, touched.py không"
else
  bad "recall-gap" "xem stale.json: $(cat "$STALE" 2>/dev/null || echo '(không tồn tại)')"
fi

hdr "(b) --json phơi mục recall_gaps"
python3 harness/scripts/wiki-sync.py --root "$REPO" --json --check > "$TMP/out.json" 2>/dev/null
python3 - "$TMP/out.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
assert "recall_gaps" in d, d
assert "code/orphan.py" in d["recall_gaps"], d
PY
if [ $? -eq 0 ]; then
  ok "--json có khoá recall_gaps chứa code/orphan.py"
else
  bad "--json recall_gaps" "xem: $(cat "$TMP/out.json" 2>/dev/null)"
fi

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 1
