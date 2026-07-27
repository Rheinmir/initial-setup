#!/usr/bin/env bash
# flywheel-autocapture-test — capture KHÔNG được phụ thuộc vào việc ai đó NHỚ gõ lệnh.
#
# Bất-biến: mỗi cú rule cắn ở PreToolUse phải tự đẻ đúng 1 dòng `spec-violation` vào
# harness/metrics/failures.jsonl — 0 token, không LLM, không người. Trước rào này ledger
# đứng im 2 tuần trong khi rule vẫn cắn hằng ngày: tín hiệu có, chỉ là không ai ghi.
#
# Hai nửa đều phải đúng:
#   1. rule VẪN cắn (rc=2) — capture không được nuốt mất cú chặn
#   2. ledger mọc thêm dòng, category = spec-violation, summary chỉ đúng validator
# Và nửa thứ ba: hook fail-open — repo không có harness/scripts thì vẫn chặn, chỉ là không ghi.
#
# Usage: bash harness/tests/flywheel-autocapture-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
HOOK="$ROOT/llmwiki/.claude/hooks/pre_tool_use.py"
fail=0
ok()  { printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
bad() { printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

# Sandbox: repo thật chỉ cho MƯỢN validators + scripts, ledger đẻ ra trong tmp.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/llmwiki/raw" "$TMP/harness"
cp -R "$ROOT/harness/scripts" "$TMP/harness/scripts"
cp -R "$ROOT/llmwiki/.claude" "$TMP/llmwiki/.claude"
cp "$ROOT/harness/failure-flywheel.config.yaml" "$TMP/harness/" 2>/dev/null

bite() {  # $1 = root chạy hook; in ra rc. OVERSTACK_HARNESS_HOME kế thừa từ caller.
  printf '{"session_id":"autocapture-test","cwd":"%s","tool_name":"Write","tool_input":{"file_path":"%s/llmwiki/raw/blocked.md","content":"x"}}' "$1" "$1" \
    | CLAUDE_PROJECT_DIR="$1" python3 "$TMP/llmwiki/.claude/hooks/pre_tool_use.py" >/dev/null 2>&1
  echo $?
}

LEDGER="$TMP/harness/metrics/failures.jsonl"
before=0; [ -f "$LEDGER" ] && before=$(wc -l < "$LEDGER")
rc=$(bite "$TMP")
after=0; [ -f "$LEDGER" ] && after=$(wc -l < "$LEDGER")

[ "$rc" = "2" ] && ok "rule vẫn cắn (rc=2) — capture không nuốt mất cú chặn" \
                || bad "rule KHÔNG cắn nữa (rc=$rc) — capture đã phá mất hàng rào"

[ "$after" -eq $((before+1)) ] && ok "ledger tự mọc đúng 1 dòng (không cần ai gõ record)" \
                               || bad "ledger $before→$after, kỳ vọng +1 — auto-capture đứt"

if [ -f "$LEDGER" ]; then
  last="$(tail -1 "$LEDGER")"
  printf '%s' "$last" | grep -q '"category": "spec-violation"' \
    && ok "gán nhãn spec-violation (bucket có sẵn, không đẻ taxonomy mới)" \
    || bad "category sai — kỳ vọng spec-violation: $last"
  printf '%s' "$last" | grep -q 'no_write_raw' \
    && ok "summary chỉ đúng validator đã cắn (truy được rule nào hay bắt)" \
    || bad "summary không nêu validator: $last"
fi

# ── Ca DOWNSTREAM THẬT: dự án KHÔNG có harness/scripts, engine nằm GLOBAL (~/.claude/harness).
# Đây là hình dạng của mọi máy người dùng — bản đầu tự nối root/harness/scripts nên trượt và
# capture chết IM LẶNG (rule vẫn cắn nên không ai biết). fresh-install bắt được; rào này giữ.
DOWN="$(mktemp -d)"; GLOB="$(mktemp -d)"
mkdir -p "$DOWN/llmwiki/raw" "$GLOB/harness/scripts"
cp -R "$ROOT/llmwiki/.claude" "$DOWN/llmwiki/.claude"
cp "$ROOT/harness/scripts/"*.py "$GLOB/harness/scripts/" 2>/dev/null
rc2=$(OVERSTACK_HARNESS_HOME="$GLOB" bite "$DOWN")
dl="$DOWN/harness/metrics/failures.jsonl"
[ "$rc2" = "2" ] && ok "downstream (engine global): rule vẫn cắn" \
                 || bad "downstream: rule KHÔNG cắn (rc=$rc2)"
{ [ -f "$dl" ] && grep -q 'no_write_raw' "$dl"; } \
  && ok "downstream ghi được ledger qua engine GLOBAL → auto-capture tới tay người dùng thật" \
  || bad "downstream KHÔNG ghi ledger — capture chết im ở đúng nơi người dùng chạy (regression cũ)"
rm -rf "$DOWN" "$GLOB"

# Không engine đâu cả → vẫn phải chặn, chỉ mất phần ghi (fail-open không được kéo sập hàng rào).
BARE="$(mktemp -d)"; mkdir -p "$BARE/llmwiki/raw"
cp -R "$ROOT/llmwiki/.claude" "$BARE/llmwiki/.claude"
rc3=$(OVERSTACK_HARNESS_HOME="$BARE/nope" bite "$BARE")
rm -rf "$BARE"
[ "$rc3" = "2" ] && ok "fail-open: không có engine nào vẫn chặn (chỉ mất phần ghi)" \
                 || bad "thiếu engine làm hook gãy (rc=$rc3) — fail-open đứt"

if [ "$fail" -eq 0 ]; then
  printf '\n\033[1m═══ flywheel-autocapture: \033[1;32mPASS\033[0m\033[0m\n'; exit 0
fi
printf '\n\033[1m═══ flywheel-autocapture: \033[1;31m%d VI PHẠM\033[0m\033[0m\n' "$fail"; exit 1
