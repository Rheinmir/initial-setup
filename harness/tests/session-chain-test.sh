#!/usr/bin/env bash
# session-chain-test — tầng episodic phải là một CHUỖI ĐỌC ĐƯỢC, và phải QUAY LẠI được prompt.
# Trước bản này: Stop-hook ghi episode nhưng không ai đọc (mem-rank retrieve/chain không có caller
# runtime), và episode không có parent nên chỉ là một đống rời. Test khoá cả hai chiều: ghi có
# parent (chain đúng thứ tự) + SessionStart in chuỗi đó ra context.
# Usage: bash harness/tests/session-chain-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
bash -c "cd '$ROOT/harness/scripts' && python3 mem-rank.py --self-test" >/tmp/mc.log 2>&1 || { cat /tmp/mc.log; exit 1; }
echo "  ✓ mem-rank self-test (gồm ca chuỗi parent) PASS"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/.llmwiki/wiki" "$TMP/harness/metrics" "$TMP/.claude"
cp -R "$ROOT/llmwiki/.claude/hooks" "$TMP/.claude/hooks"; cp -R "$ROOT/harness/scripts" "$TMP/harness/scripts"
cp "$ROOT/.template-manifest.json" "$TMP/" 2>/dev/null || echo '{}' > "$TMP/.template-manifest.json"
printf 'verified: false\n' > "$TMP/harness/mem-rank.config.yaml"
git -C "$TMP" -c init.defaultBranch=main init -q
ep(){ (cd "$TMP/harness/scripts" && python3 mem-rank.py episode "$1" --files "$2" --session "$3" --parent auto --root "$TMP") >/dev/null 2>&1; }
ep "dựng validator R20" "harness/validators/r20.py" sessA
ep "vá hook global"     "llmwiki/.claude/hooks/stop.py" sessB
ep "viết test chuỗi"    "harness/tests/session-chain-test.sh" sessC
CH="$(cd "$TMP/harness/scripts" && python3 mem-rank.py chain --root "$TMP")"
echo "$CH" | grep -q "sessC" && echo "$CH" | grep -q "sessA" && echo "  ✓ chain in đủ 3 mắt" || { echo "  ✗ chain thiếu mắt"; echo "$CH"; exit 1; }
[ "$(echo "$CH" | grep -c '─ sess')" = 3 ] && echo "  ✓ không lặp / không dư" || { echo "  ✗ số mắt sai"; echo "$CH"; exit 1; }
echo "$CH" | head -3 | grep -q "sessC" && echo "  ✓ thứ tự mới → cũ" || { echo "  ✗ thứ tự sai"; exit 1; }
OUT="$(printf '{"cwd":"%s"}' "$TMP" | CLAUDE_PROJECT_DIR="$TMP" python3 "$TMP/.claude/hooks/session_start.py" 2>/dev/null)"
echo "$OUT" | grep -q "\[recall\]" && echo "  ✓ SessionStart bơm chuỗi vào context" || { echo "  ✗ SessionStart không in recall"; echo "$OUT" | head -5; exit 1; }
echo "$OUT" | grep -q "viết test chuỗi" && echo "  ✓ recall nêu việc phiên gần nhất" || { echo "  ✗ recall thiếu nội dung"; exit 1; }
echo "$OUT" | grep -q "nguồn đúng" && echo "  ✓ recall tự khai 'là NHẮC, không phải sự thật'" || { echo "  ✗ thiếu cảnh báo untrusted"; exit 1; }
rm -f "$TMP/harness/metrics/memory.jsonl"
OUT2="$(printf '{"cwd":"%s"}' "$TMP" | CLAUDE_PROJECT_DIR="$TMP" python3 "$TMP/.claude/hooks/session_start.py" 2>/dev/null)"
echo "$OUT2" | grep -q "\[recall\]" && { echo "  ✗ store rỗng vẫn in recall"; exit 1; } || echo "  ✓ store rỗng → im lặng (không nhiễu)"
# OKF: memory xuất ra .md phải qua ĐÚNG validator R9 đang gác wiki (không tự chấm mình)
(cd "$TMP/harness/scripts" && python3 mem-rank.py episode "ghi lại" --session sessD --parent auto --root "$TMP") >/dev/null 2>&1
(cd "$TMP/harness/scripts" && python3 mem-rank.py export-okf --out "$TMP/okf" --root "$TMP") >/dev/null 2>&1
N=$(ls "$TMP/okf"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$N" -ge 1 ] && echo "  ✓ export-okf sinh $N file .md" || { echo "  ✗ export-okf không sinh file"; exit 1; }
python3 "$ROOT/harness/validators/okf_frontmatter.py" "$TMP"/okf/*.md >/dev/null 2>&1 \
  && echo "  ✓ file xuất ra qua validator R9 (OKF v0.1) thật" || { echo "  ✗ file xuất ra KHÔNG qua R9"; exit 1; }
grep -q "## Origin" "$TMP"/okf/*.md && echo "  ✓ có ## Origin (qua R2 nếu bỏ vào wiki)" || { echo "  ✗ thiếu ## Origin"; exit 1; }
# BIÊN LAI: SessionStart phải để lại bằng chứng đã quét OKF; Stop verify đối chiếu transcript.
mkdir -p "$TMP/.llmwiki/wiki/concepts"
printf -- '---\ntype: concept\ntitle: "luật harness"\ntags: [harness, rules]\nid: hr\n---\n\n# x\n## Origin\n- a\n' > "$TMP/.llmwiki/wiki/concepts/harness-rules.md"
printf '{"cwd":"%s","session_id":"sessC"}' "$TMP" | CLAUDE_PROJECT_DIR="$TMP" python3 "$TMP/.claude/hooks/session_start.py" >/tmp/ss2.out 2>/dev/null
R=$(cd "$TMP/harness/scripts" && python3 okf-scan.py receipts --session sessC --root "$TMP")
echo "$R" | grep -q "quét" && echo "  ✓ SessionStart để lại BIÊN LAI quét OKF" || { echo "  ✗ không có biên lai cho ĐÚNG phiên"; echo "$R"; exit 1; }
(cd "$TMP/harness/scripts" && python3 okf-scan.py --check --session sessC --root "$TMP") >/dev/null 2>&1 \
  && echo "  ✓ --check: phiên có quét → 0" || { echo "  ✗ --check sai"; exit 1; }
(cd "$TMP/harness/scripts" && python3 okf-scan.py --check --session sessKhac --root "$TMP") >/dev/null 2>&1 \
  && { echo "  ✗ phiên chưa quét vẫn báo 0"; exit 1; } || echo "  ✓ --check: phiên chưa quét → 2 (gate dùng được)"
# transcript giả lập agent MỞ đúng mục mà biên lai đã trả về (lấy từ chính biên lai, không đoán)
P=$(cd "$TMP/harness/scripts" && python3 okf-scan.py receipts --session sessC --root "$TMP" --json \
    | python3 -c "import sys,json;rs=json.load(sys.stdin);print(next((x for r in rs for x in (r.get('returned') or [])), ''))")
[ -n "$P" ] && echo "  ✓ biên lai có mục trả về: $P" || { echo "  ✗ biên lai không trả về mục nào"; exit 1; }
printf '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"%s"}}]}}\n' "$P" > "$TMP/tr.jsonl"
V=$(cd "$TMP/harness/scripts" && python3 okf-scan.py verify --session sessC --transcript "$TMP/tr.jsonl" --root "$TMP")
printf '{"type":"assistant","message":{"content":[{"type":"text","text":"không mở gì"}]}}\n' > "$TMP/tr0.jsonl"
V0=$(cd "$TMP/harness/scripts" && python3 okf-scan.py verify --session sessC --transcript "$TMP/tr0.jsonl" --root "$TMP")
echo "$V0" | grep -q "coverage 0%" && echo "  ✓ agent KHÔNG mở gì → coverage 0% (không tự khen)" || { echo "  ✗ coverage sai khi không mở"; echo "$V0"; exit 1; }
echo "$V" | grep -q "coverage 100%" && echo "  ✓ verify đếm ĐÚNG mục agent thật sự mở (coverage 100%)" || { echo "  ✗ verify không đếm được"; echo "$V"; exit 1; }
printf '\n\033[1m═══ session-chain: \033[1;32mPASS\033[0m\033[0m\n'
