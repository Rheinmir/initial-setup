#!/usr/bin/env bash
# session-continue-test — trần token-budget phải THI HÀNH được: hook UserPromptSubmit chặn prompt khi
# phiên vượt/sắp vượt, ghi file bàn giao kiểu Orca, đánh dấu để không mở phiên thứ hai; dưới trần → im.
# Chạy self-test tất định + tích hợp hook trên repo tạm (OVERSTACK_HANDOVER_DRY_RUN=1: không mở terminal).
# Usage: bash harness/tests/session-continue-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
python3 "$ROOT/harness/scripts/session-continue.py" --self-test >/tmp/sc-self.log 2>&1 || { cat /tmp/sc-self.log; exit 1; }
echo "  ✓ self-test tất định PASS"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/llmwiki/wiki" "$TMP/harness/metrics" "$TMP/.claude"
cp -R "$ROOT/llmwiki/.claude/hooks" "$TMP/.claude/hooks"; cp -R "$ROOT/harness/scripts" "$TMP/harness/scripts"
cp "$ROOT/harness/token-budget.config.yaml" "$TMP/harness/"
# cap model calls thấp để phiên s-over vượt theo trigger MẶC ĐỊNH (per_task_usd không kích hoạt — subscription)
sed -i.bak "s/^  per_session_model_calls: 500/  per_session_model_calls: 10/" "$TMP/harness/token-budget.config.yaml" && rm -f "$TMP/harness/token-budget.config.yaml.bak"
git -C "$TMP" -c init.defaultBranch=main init -q
# phiên "s-over": 12 lượt > cap 10 (và $6 — không kích hoạt vì per_task_usd không trong triggers mặc định)
printf '{"s-over":{"session":"s-over","turns":12,"tokens":{"input_tokens":100,"output_tokens":100},"cost_usd":6.0},"s-ok":{"session":"s-ok","turns":2,"tokens":{"input_tokens":50,"output_tokens":50},"cost_usd":0.1}}' > "$TMP/harness/metrics/cost-by-session.json"
printf '{"type":"user","message":{"content":"sửa nốt validator"}}\n' > "$TMP/t.jsonl"
run_hook(){ printf '{"session_id":"%s","transcript_path":"%s","prompt":"%s","cwd":"%s"}' "$1" "$TMP/t.jsonl" "$2" "$TMP" \
  | CLAUDE_PROJECT_DIR="$TMP" OVERSTACK_HANDOVER_DRY_RUN=1 python3 "$TMP/.claude/hooks/user_prompt_submit.py" >/tmp/sc-out 2>/tmp/sc-err; echo $?; }
rc=$(run_hook s-ok "làm việc A"); [ "$rc" = 0 ] && echo "  ✓ dưới trần → prompt đi tiếp (rc=0)" || { echo "  ✗ dưới trần bị chặn rc=$rc"; cat /tmp/sc-err; exit 1; }
rc=$(run_hook s-over "prompt bị chặn X")
[ "$rc" = 2 ] && echo "  ✓ vượt trần → chặn prompt (rc=2)" || { echo "  ✗ vượt trần nhưng rc=$rc"; cat /tmp/sc-err; exit 1; }
grep -q '"decision": "block"' /tmp/sc-out && echo "  ✓ stdout có JSON decision:block (OpenClaude)" || { echo "  ✗ thiếu JSON block"; exit 1; }
grep -q "session-continue" /tmp/sc-err && echo "  ✓ stderr nêu lý do + nơi bàn giao (Claude Code)" || { echo "  ✗ stderr trống"; exit 1; }
HF=$(ls "$TMP"/llmwiki/handover/*-s-over-continue.md 2>/dev/null | head -1)
[ -n "$HF" ] && echo "  ✓ file bàn giao: $(basename "$HF")" || { echo "  ✗ không có file bàn giao"; ls -R "$TMP/llmwiki"; exit 1; }
for k in "prompt bị chặn X" "Chỉ dẫn cho phiên này" "dữ liệu lịch sử" "git status"; do grep -q "$k" "$HF" && echo "  ✓ bàn giao có: $k" || { echo "  ✗ bàn giao thiếu: $k"; exit 1; }; done
rc=$(run_hook s-over "prompt thứ hai"); n=$(ls "$TMP"/llmwiki/handover/*-continue.md | wc -l | tr -d ' ')
[ "$rc" = 2 ] && [ "$n" = 1 ] && echo "  ✓ prompt kế cùng phiên: vẫn chặn, KHÔNG mở phiên/ghi file thứ hai" || { echo "  ✗ lặp: rc=$rc files=$n"; exit 1; }
printf '\n\033[1m═══ session-continue: \033[1;32mPASS\033[0m\033[0m\n'
