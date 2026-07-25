#!/usr/bin/env bash
# Khoá: Graph.build_graph() nạp cạnh "touches" (wiki→code, 2 nguồn: backtick thân bài
# + frontmatter khai tay) vào touches_in — suy tất định, KHÔNG đổi hành vi touches_targets().
set -uo pipefail

SRC="${1:?usage: wikigraph-touches-in-test.sh <repo-root>}"
WG="$SRC/harness/scripts/wiki-graph.py"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/repo/llmwiki/wiki/concepts" "$TMP/repo/real"
echo "hello" > "$TMP/repo/real/exists.py"
echo "hello" > "$TMP/repo/real/fm-only.py"
cat > "$TMP/repo/llmwiki/wiki/concepts/demo.md" <<'EOF'
---
type: concept
relations:
  - {rel: touches, path: real/fm-only.py}
---
# Demo
Liên quan `real/exists.py` và `real/missing.py`.
EOF

hdr "(a) touches_in nạp cạnh từ backtick thân bài, path phải tồn tại trên đĩa"
OUT=$(python3 - "$WG" "$TMP/repo/llmwiki/wiki" <<'PY'
import importlib.util, sys, pathlib
spec = importlib.util.spec_from_file_location("_wg", pathlib.Path(sys.argv[1]))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
g = m.build_graph(pathlib.Path(sys.argv[2]))
print("exists:", sorted(m.code_touched_by(g, "real/exists.py")))
print("missing:", sorted(m.code_touched_by(g, "real/missing.py")))
print("fmonly:", sorted(m.code_touched_by(g, "real/fm-only.py")))
print("never:", sorted(m.code_touched_by(g, "real/never-mentioned.py")))
PY
)
echo "$OUT" | grep -q "exists: \['concepts/demo.md'\]" \
  && ok "backtick + path tồn tại → có cạnh touches" \
  || bad "cạnh backtick" "kỳ vọng exists: ['concepts/demo.md'], nhận: $OUT"
echo "$OUT" | grep -q "missing: \[\]" \
  && ok "backtick nhưng path KHÔNG tồn tại → 0 cạnh" \
  || bad "path không tồn tại" "kỳ vọng missing: [], nhận: $OUT"

hdr "(b) touches_in nạp cạnh từ frontmatter khai tay (nguồn thứ 2)"
echo "$OUT" | grep -q "fmonly: \['concepts/demo.md'\]" \
  && ok "frontmatter {rel: touches, path: ...} → có cạnh touches dù KHÔNG có backtick trùng" \
  || bad "cạnh frontmatter" "kỳ vọng fmonly: ['concepts/demo.md'], nhận: $OUT"

hdr "(c) code_touched_by() trả rỗng cho path chưa từng được nhắc ở đâu cả"
echo "$OUT" | grep -q "never: \[\]" \
  && ok "path chưa từng touches → set rỗng" \
  || bad "rỗng đúng nghĩa" "kỳ vọng never: [], nhận: $OUT"

hdr "(d) is_touchable_path() đúng phạm vi đuôi file của CODE_PATH_RE"
OUT2=$(python3 - "$WG" <<'PY'
import importlib.util, sys, pathlib
spec = importlib.util.spec_from_file_location("_wg", pathlib.Path(sys.argv[1]))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m.is_touchable_path("harness/scripts/wiki-graph.py"))
print(m.is_touchable_path("llmwiki/wiki/concepts/demo.md"))
PY
)
[ "$(echo "$OUT2" | sed -n 1p)" = "True" ] && [ "$(echo "$OUT2" | sed -n 2p)" = "False" ] \
  && ok ".py trong phạm vi, .md ngoài phạm vi (đúng TOUCHABLE_EXTS)" \
  || bad "is_touchable_path" "nhận: $OUT2"

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 1
