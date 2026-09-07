#!/usr/bin/env bash
# self-report-test — hệ phải TỰ CHẤM được từ sổ và chỉ ồn khi đáng ồn.
# Khoá bốn thứ dễ hỏng: (1) chấm đúng theo ngưỡng, (2) hook chỉ nổ đúng mốc N lượt,
# (3) raise có dedupe/cooldown/trần (không spam repo mẹ), (4) issue KHÔNG lộ nội dung file.
# Usage: bash harness/tests/self-report-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
python3 "$ROOT/harness/scripts/self-report.py" --self-test >/tmp/sr.log 2>&1 || { cat /tmp/sr.log; exit 1; }
echo "  ✓ self-test tất định PASS (ngưỡng, cooldown, trần, riêng tư)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/.llmwiki/wiki" "$TMP/harness/metrics" "$TMP/.claude/audit"
cp -R "$ROOT/llmwiki/.claude/hooks" "$TMP/.claude/hooks"; cp -R "$ROOT/harness/scripts" "$TMP/harness/scripts"
cp "$ROOT/harness/self-report.config.yaml" "$TMP/harness/"
cp "$ROOT/.template-manifest.json" "$TMP/" 2>/dev/null || echo '{}' > "$TMP/.template-manifest.json"
git -C "$TMP" -c init.defaultBranch=main init -q
# 6 phiên có số đo, 0 biên lai quét → finding 'high' recall-never-ran
python3 - "$TMP" <<'PY'
import json,sys,pathlib
r=pathlib.Path(sys.argv[1])
(r/"harness/metrics/cost-by-session.json").write_text(json.dumps({
  f"s{i}": {"session": f"s{i}", "turns": 20, "tokens": {"input_tokens": 100, "output_tokens": 50},
            "cost_usd": 0.4, "last_ts": f"2026-09-0{i+1}T00:00:00Z"} for i in range(6)}))
PY
R="$(cd "$TMP" && python3 harness/scripts/self-report.py --report --root "$TMP")"
echo "$R" | grep -q "recall-never-ran\|Không phiên nào để lại biên lai" && echo "  ✓ chấm ra vấn đề thật từ sổ" || { echo "  ✗ không chấm ra"; echo "$R"; exit 1; }
(cd "$TMP" && python3 harness/scripts/self-report.py --check --root "$TMP") >/dev/null 2>&1 \
  && { echo "  ✗ --check không cắn khi có finding high"; exit 1; } || echo "  ✓ --check exit 2 khi có finding high (gate dùng được)"
[ -s "$TMP/harness/metrics/self-report.jsonl" ] && echo "  ✓ ghi lịch sử self-report.jsonl (đo được xu hướng)" || { echo "  ✗ không ghi lịch sử"; exit 1; }
# raise ở chế độ dry-run: chỉ đề xuất, KHÔNG gọi mạng, tôn trọng trần
D="$(cd "$TMP" && python3 harness/scripts/self-report.py --raise --dry-run --json --root "$TMP")"
N=$(echo "$D" | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('raised') or []))")
[ "$N" -le 2 ] && echo "  ✓ dry-run đề xuất tối đa 2 (trần max_per_run)" || { echo "  ✗ vượt trần: $N"; exit 1; }
echo "$D" | grep -q '"action": "raised"' && { echo "  ✗ dry-run vẫn gọi tạo issue thật"; exit 1; } || echo "  ✓ dry-run KHÔNG tạo issue thật"
# hook: chưa tới mốc thì im, tới mốc N thì nói
hook(){ printf '{"cwd":"%s","session_id":"sr","prompt":"x"}' "$TMP" | CLAUDE_PROJECT_DIR="$TMP" \
        OVERSTACK_SELF_REPORT_EVERY="$1" LLMWIKI_DOCS_GATE_EVERY=0 python3 "$TMP/.claude/hooks/user_prompt_submit.py" 2>/dev/null; }
rm -f "$TMP/.claude/audit/.self-report.json"
O1="$(hook 3)"; O2="$(hook 3)"
echo "$O1$O2" | grep -q "self-report" && { echo "  ✗ nổ trước mốc"; exit 1; } || echo "  ✓ lượt 1-2 (mốc 3): im lặng"
O3="$(hook 3)"
echo "$O3" | grep -q "self-report" && echo "  ✓ đúng lượt thứ 3: bơm báo cáo vào context" || { echo "  ✗ tới mốc mà không báo"; echo "$O3"; exit 1; }
echo "$O3" | grep -q "additionalContext" && echo "  ✓ đi qua đường additionalContext (không phá prompt)" || { echo "  ✗ sai giao thức hook"; exit 1; }
# riêng tư: body issue không được chứa nội dung file của dự án
printf 'BÍ MẬT NỘI BỘ KHÔNG ĐƯỢC RÒ\n' > "$TMP/.llmwiki/wiki/secret.md"
B="$(cd "$TMP" && python3 harness/scripts/self-report.py --raise --dry-run --json --root "$TMP")"
echo "$B" | grep -q "BÍ MẬT NỘI BỘ" && { echo "  ✗ body issue rò nội dung file"; exit 1; } || echo "  ✓ body issue không rò nội dung file dự án"
printf '\n\033[1m═══ self-report: \033[1;32mPASS\033[0m\033[0m\n'
