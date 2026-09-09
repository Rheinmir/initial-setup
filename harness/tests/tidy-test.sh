#!/usr/bin/env bash
# tidy-test.sh — chứng minh tidy.py đúng ngưỡng + không giết draft sống + git-aware archive (D1/D2).
# Sandbox: git repo tạm, không đụng repo thật.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TIDY="$HERE/../scripts/tidy.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
pass=0
assert() { if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "  ✓ $1"; else echo "  ✗ $1 (mong '$2', được '$3')"; exit 1; fi; }

cd "$TMP"; git init -q -b main; git config user.email t@t; git config user.name t
D=llmwiki/wiki/sources/draft; H=llmwiki/html
mkdir -p "$D/sub" "$H" llmwiki/wiki/concepts
printf -- '---\ntype: draft\n---\n# idx\n' > llmwiki/wiki/index.md
mk() { printf -- '---\ntype: draft\nstatus: %s\n---\n# %s\nnội dung\n' "$2" "$1" > "$D/$1.md"; }
for i in 1 2 3 4 5 6 7 8 9; do mk "010126-live-$i" proposed; done
mk 010126-old-done done                       # 10 file gốc
mk sub/010126-in-subdir proposed              # thư mục con — KHÔNG tính
printf -- '---\ntype: draft\n---\n# nostatus\n' > "$D/010126-nostatus-PLAN.md"; rm "$D/010126-nostatus-PLAN.md"
git add -A; git -c core.hooksPath=/dev/null commit -qm init

echo "[1] ngưỡng: 10 file gốc (+1 trong sub) → exit 0"
set +e; python3 "$TIDY" check --root . >/dev/null; rc=$?; set -e
assert "10 file, sub không tính → exit 0" 0 "$rc"

mk 010126-eleventh proposed
set +e; python3 "$TIDY" check --root . >/dev/null; rc=$?; set -e
assert "11 file → exit 3" 3 "$rc"
set +e; j=$(python3 "$TIDY" check --root . --json); set -e
n=$(echo "$j" | python3 -c 'import json,sys;print(json.load(sys.stdin)["draft_top"])')
assert "--json draft_top=11" 11 "$n"

echo "[2] D2: draft proposed ngày cũ KHÔNG bị archive; status done → archive"
out=$(python3 "$TIDY" plan --root .)
assert "old-done → ARCHIVE OUTDATED" 1 "$(echo "$out" | grep -c 'old-done.md.*OUTDATED — status done')"
assert "9 live proposed → TREO, không archive" 0 "$(echo "$out" | grep 'live-' | grep -c ARCHIVE || true)"
assert "kết đếm archive = 1" 1 "$(echo "$out" | grep -oE 'archive [0-9]+' | awk '{print $2}')"

echo "[2b] seq html được draft SỐNG (stem khác) link tới → KEEP; seq không ai nhắc → archive"
printf '<html>seq</html>' > "$H/010126-feat-seq.html"; printf '<html>seq</html>' > "$H/010126-orphan-seq.html"
printf -- '---\ntype: draft\nstatus: proposed\n---\n# feat fe\n**Sequence diagram**: [seq](../../../html/010126-feat-seq.html)\n' > "$D/010126-feat-fe.md"
out=$(python3 "$TIDY" plan --root .)
assert "feat-seq (draft feat-fe link) → KEEP" 1 "$(echo "$out" | grep 'feat-seq.html' | grep -c 'còn sống')"
assert "orphan-seq → ARCHIVE" 1 "$(echo "$out" | grep 'orphan-seq.html' | grep -c 'mồ côi')"
rm "$H/010126-orphan-seq.html" "$D/010126-feat-fe.md" "$H/010126-feat-seq.html"

echo "[2c] PLAN không thấy SPEC → KEEP; PLAN status done → archive"
printf -- '---\ntype: draft\n---\n# plan\n### Task 1\n' > "$D/010126-lonely-PLAN.md"
printf -- '---\ntype: draft\nstatus: done\n---\n# plan\n' > "$D/010126-finished-PLAN.md"
out=$(python3 "$TIDY" plan --root .)
assert "lonely-PLAN → giữ" 1 "$(echo "$out" | grep 'lonely-PLAN' | grep -c 'giữ')"
assert "finished-PLAN → OUTDATED" 1 "$(echo "$out" | grep 'finished-PLAN' | grep -c 'OUTDATED')"
rm "$D/010126-lonely-PLAN.md" "$D/010126-finished-PLAN.md"

echo "[3] D1: đích gitignored + file tracked → KHÔNG dời (bảo vệ khỏi xoá khỏi repo)"
echo "llmwiki/wiki/sources/draft/archive/" > .gitignore; git add .gitignore; git -c core.hooksPath=/dev/null commit -qm ign
python3 "$TIDY" apply --root . >/dev/null
assert "old-done vẫn ở chỗ cũ" 1 "$([ -f "$D/010126-old-done.md" ] && echo 1 || echo 0)"

echo "[4] D1: đích không ignore → git mv, git thấy RENAME không DELETE"
: > .gitignore; git add .gitignore; git -c core.hooksPath=/dev/null commit -qm unign
python3 "$TIDY" apply --root . >/dev/null
assert "file nằm trong archive/analysis/" 1 "$([ -f "$D/archive/analysis/010126-old-done.md" ] && echo 1 || echo 0)"
st=$(git status --porcelain | grep old-done | cut -c1-2 | tr -d ' ')
assert "git status = R (rename), không D" R "$st"
assert "archive/INDEX.md có dòng" 1 "$(grep -c old-done "$H/archive/INDEX.md")"

echo "[5] check sau apply: 10 file → exit 0 (vòng khép)"
set +e; python3 "$TIDY" check --root . >/dev/null; rc=$?; set -e
assert "sau archive còn 10 → exit 0" 0 "$rc"

echo "PASS $pass/$pass"
