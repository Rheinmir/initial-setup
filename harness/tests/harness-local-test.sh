#!/usr/bin/env bash
# harness-local-test — cơ chế rule RIÊNG của dự án (harness-local/) chạy SONG SONG framework
# R1–R13 mà KHÔNG giẫm chân. Sandbox MỌI case có thể fail/đụng độ:
#   A namespace guard (R-collision / sai format / trùng id)   B hook write-time (block/pass)
#   C files commit-time (block/pass)   D đụng độ runtime (_-skip · crash fail-open · empty no-op)
#   E sống chung framework (sync-safe ngoài manifest · framework chạy TRƯỚC, project không tắt được)
#
# Usage: bash harness/tests/harness-local-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
RUN="$ROOT/harness-local/run.py"
pass=0; fail=0
ok(){  printf '  \033[1;32m✓\033[0m %s\n' "$1"; pass=$((pass+1)); }
bad(){ printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }
hdr(){ printf '\n\033[1m%s\033[0m\n' "$1"; }

[ -f "$RUN" ] || { bad "thiếu harness-local/run.py"; printf '\n%d FAIL\n' 1; exit 1; }

# Sandbox: bản sao run.py + validators/policy tạm (run.py định vị validators theo __file__ của nó).
# 'repo root' của sandbox = $SB; harness-local = $SB/harness-local (mirror layout thật).
SB="$(mktemp -d)"; R="$SB/harness-local"; VDIR="$R/validators"; POL="$R/policy.yaml"
mkdir -p "$VDIR"; cp "$RUN" "$R/run.py"

# validator P-mẫu: chặn "TODO" — hỗ trợ CẢ hook (stdin JSON) lẫn files (argv) như contract.
cat > "$VDIR/no_todo.py" <<'PY'
import json, sys
args = [a for a in sys.argv[1:] if not a.startswith("-")]
if args:  # files mode (pre-commit/CI)
    hit = [a for a in args if "TODO" in open(a, encoding="utf-8", errors="replace").read()]
    if hit: print("TODO", file=sys.stderr); sys.exit(2)
    sys.exit(0)
try: ev = json.load(sys.stdin)            # hook mode
except Exception: sys.exit(0)
if ev.get("action") == "write" and "TODO" in (ev.get("content") or ""):
    print("TODO", file=sys.stderr); sys.exit(2)
sys.exit(0)
PY

hdr "A — namespace guard (id P<n> ≠ R<n>; đúng format; không trùng)"
printf 'rules:\n  - id: R99\n    name: x\n' > "$POL"
python3 "$R/run.py" check >/dev/null 2>&1; [ $? -eq 2 ] && ok "CHẶN id R99 (đụng namespace framework R<n>)" || bad "không chặn R-collision"
printf 'rules:\n  - id: X1\n    name: x\n' > "$POL"
python3 "$R/run.py" check >/dev/null 2>&1; [ $? -eq 2 ] && ok "CHẶN id sai format (X1)" || bad "không chặn sai format"
printf 'rules:\n  - id: P1\n    name: a\n  - id: P1\n    name: b\n' > "$POL"
python3 "$R/run.py" check >/dev/null 2>&1; [ $? -eq 2 ] && ok "CHẶN trùng id P1" || bad "không chặn trùng id"
printf 'rules:\n  - id: P1\n    name: no-todo\n    validator: harness-local/validators/no_todo.py\n' > "$POL"
python3 "$R/run.py" check >/dev/null 2>&1; [ $? -eq 0 ] && ok "CHO qua P1 hợp lệ + validator compile" || bad "chặn nhầm P-hợp-lệ"

hdr "B — hook write-time: chặn vi phạm, cho qua sạch"
printf '%s' '{"action":"write","file_path":"x.md","content":"TODO: vá"}' | python3 "$R/run.py" hook >/dev/null 2>&1; [ $? -eq 2 ] && ok "CHẶN write có TODO" || bad "không chặn ở hook"
printf '%s' '{"action":"write","file_path":"x.md","content":"sach"}'     | python3 "$R/run.py" hook >/dev/null 2>&1; [ $? -eq 0 ] && ok "CHO qua write sạch" || bad "chặn nhầm bản sạch"

hdr "C — files commit-time (pre-commit/CI): chặn file có TODO"
echo "TODO: x" > "$SB/f.txt"; python3 "$R/run.py" files "$SB/f.txt" >/dev/null 2>&1; [ $? -eq 2 ] && ok "CHẶN file TODO" || bad "không chặn ở files"
echo "ok"      > "$SB/g.txt"; python3 "$R/run.py" files "$SB/g.txt" >/dev/null 2>&1; [ $? -eq 0 ] && ok "CHO qua file sạch" || bad "chặn nhầm file sạch"

hdr "D — đụng độ runtime: _-skip · crash fail-open · empty no-op"
cat > "$VDIR/_always_block.py" <<'PY'
import sys; print("KHONG-DUOC-CHAY", file=sys.stderr); sys.exit(2)
PY
printf '%s' '{"action":"write","file_path":"x.md","content":"sach"}' | python3 "$R/run.py" hook >/dev/null 2>&1; [ $? -eq 0 ] && ok "validator _-prefix BỊ BỎ QUA (mẫu/helper không chạy)" || bad "_validator vẫn chạy (sai)"
cat > "$VDIR/crasher.py" <<'PY'
raise SystemExit(undefined_name)   # NameError → exit≠2
PY
printf '%s' '{"action":"write","file_path":"x.md","content":"sach"}' | python3 "$R/run.py" hook >/dev/null 2>&1; [ $? -eq 0 ] && ok "validator CRASH → fail-open (không gãy phiên/commit)" || bad "crash làm gãy (sai)"
rm -f "$VDIR/crasher.py" "$VDIR/no_todo.py" "$VDIR/_always_block.py"
printf '%s' '{"action":"write","file_path":"x.md","content":"TODO"}' | python3 "$R/run.py" hook >/dev/null 2>&1; [ $? -eq 0 ] && ok "0 validator → no-op (dự án không cài rule vẫn chạy như thường)" || bad "no-op sai"
rm -rf "$SB"

hdr "E — sống chung framework: sync-safe + framework chạy TRƯỚC (precedence)"
MAN="$ROOT/.template-manifest.json"
if [ -f "$MAN" ]; then
  grep -q 'harness-local' "$MAN" && bad "harness-local NẰM trong manifest → sync-template sẽ đè rule dự án!" || ok "harness-local NGOÀI manifest → sync-template/framework-update không đụng"
else
  ok "manifest vắng (bản lẻ) — harness-local vốn không được khai → sync-safe"
fi
PTU="$ROOT/llmwiki/.claude/hooks/pre_tool_use.py"
fl=$(grep -n 'for name in checks' "$PTU" 2>/dev/null | head -1 | cut -d: -f1)
# neo vào LỜI GỌI trong main (thụt 4 space), không phải dòng `def` — đừng pin cách viết tham số
rl=$(grep -n '^    run_local(' "$PTU" 2>/dev/null | head -1 | cut -d: -f1)
{ [ -n "$fl" ] && [ -n "$rl" ] && [ "$rl" -gt "$fl" ]; } && ok "pre_tool_use: framework checks TRƯỚC, harness-local SAU → project KHÔNG tắt được rule framework" || bad "thứ tự precedence sai/thiếu"

printf '\n\033[1m═══ TỔNG: %d test — \033[1;32m%d PASS\033[0m / \033[1;31m%d FAIL\033[0m\033[0m\n' "$((pass+fail))" "$pass" "$fail"
[ "$fail" -eq 0 ]
