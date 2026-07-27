#!/usr/bin/env bash
# engines-smoke-test — CHẠY THẬT từng engine chưa có proof (26 nợ capproof 2026-07-18),
# mỗi cái execute với input thật trong sandbox/read-only, assert exit-code + output thật.
# KHÔNG phải danh sách tên cho resolver ăn: tên chỉ xuất hiện vì lệnh thật được chạy ở đây.
# Phủ: mech:harness-lint, mech:medic-mirror, skill:docs-curate, skill:ovs-notes,
#      script: adapt-registry.py arch-scan.py dispatch-verify.py embed-ollama.py embed-voyage.py
#              harness-lint.py ovs-notes.py query-log.py query-proxy.py skill-health.py
#              skill-registry.py sync-skills.py sync-template.py wiki-health.py
#      tool:   artifacts.py build-cheatsheet.py build-docs-index.py build-health-dashboard.py
#              build-skill-search.py docs-curate.py whiteboard-skill-map.py wiki-relations.py
set -u
ROOT="$(cd "${1:-.}" && pwd)"
fail=0
ok(){ printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
bad(){ printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }
SB="$(mktemp -d)"
trap 'rm -rf "$SB"' EXIT

# clone_tool DEST file... — chép engine vào sandbox GIỮ NGUYÊN vị trí tương-đối, vì các tool
# fdk/tools/* tự tìm repo-root bằng Path(__file__).parents[2] → sandbox thành "repo" của nó.
clone_tool(){ local d="$1"; shift; local f; for f in "$@"; do
  mkdir -p "$d/$(dirname "$f")"; cp "$ROOT/$f" "$d/$f"; done; }

# ── fixtures dùng chung ────────────────────────────────────────────────────────
mkdir -p "$SB/skills/smoke-sk" "$SB/wiki"
printf -- '---\nname: smoke-sk\ndescription: skill fixture cho smoke harness\n---\n\n## Trigger phrases\nsmoke harness fixture\n' > "$SB/skills/smoke-sk/SKILL.md"
mkdir -p "$SB/wiki/concepts"   # wiki-health chỉ đếm trang trong CONTENT_DIRS
printf -- '# index\n- [[page-a]]\n' > "$SB/wiki/index.md"
printf -- '# page a\nnoi dung page a smoke\n' > "$SB/wiki/concepts/page-a.md"
printf -- '# orphan b\nkhong ai link toi\n' > "$SB/wiki/concepts/orphan-b.md"

# ── 1. wiki-health.py: chạy trên wiki fixture; orphan thật phải làm --fail-on orphans đỏ ──
out=$(python3 "$ROOT/harness/scripts/wiki-health.py" --wiki-dir "$SB/wiki" 2>&1); rc=$?
[ $rc -eq 0 ] && ok "wiki-health.py chạy sạch trên fixture (rc=0)" || bad "wiki-health.py rc=$rc: $out"
out=$(python3 "$ROOT/harness/scripts/wiki-health.py" --wiki-dir "$SB/wiki" --fail-on orphans 2>&1); rc=$?
[ $rc -ne 0 ] && ok "wiki-health.py --fail-on orphans ĐỎ khi có orphan thật" || bad "wiki-health.py không bắt orphan-b"

# ── 2. query-proxy.py: L0 trên wiki thật (read-only), out về sandbox ──
out=$(python3 "$ROOT/harness/scripts/query-proxy.py" --mode L0 --out "$SB/qp.json" 2>&1); rc=$?
if [ $rc -eq 0 ] && python3 -c "import json;json.load(open('$SB/qp.json'))" 2>/dev/null; then
  ok "query-proxy.py --mode L0 sinh output JSON hợp lệ"
else bad "query-proxy.py rc=$rc: $out"; fi

# ── 3. skill-health.py: JSON trên skills fixture ──
out=$(python3 "$ROOT/harness/scripts/skill-health.py" --skills-dir "$SB/skills" --json 2>&1); rc=$?
if [ $rc -eq 0 ] && echo "$out" | python3 -c "import sys,json;d=json.load(sys.stdin);assert 'smoke-sk' in json.dumps(d)" 2>/dev/null; then
  ok "skill-health.py --json thấy smoke-sk trong fixture"
else bad "skill-health.py rc=$rc: $(echo "$out" | head -2)"; fi

# ── 4. query-log.py: --record ghi JSONL thật vào sandbox root ──
python3 "$ROOT/harness/scripts/query-log.py" --root "$SB" --record --question "smoke-question" >/dev/null 2>&1
grep -q "smoke-question" "$SB/harness/metrics/query-log.jsonl" 2>/dev/null \
  && ok "query-log.py --record ghi được dòng JSONL" || bad "query-log.py không ghi harness/metrics/query-log.jsonl"

# ── 5. adapt-registry.py: report thật trên repo (read-only) ──
out=$(python3 "$ROOT/harness/scripts/adapt-registry.py" --root "$ROOT" --report 2>&1); rc=$?
[ $rc -eq 0 ] && [ -n "$out" ] && ok "adapt-registry.py --report chạy được trên repo thật" \
  || bad "adapt-registry.py rc=$rc: $(echo "$out" | head -2)"

# ── 6. arch-scan.py: file fixture sạch → rc 0 ──
printf 'tai lieu binh thuong, khong xung dot luat.\n' > "$SB/doc.md"
out=$(python3 "$ROOT/harness/scripts/arch-scan.py" --root "$SB" "$SB/doc.md" 2>&1); rc=$?
[ $rc -eq 0 ] && ok "arch-scan.py sạch trên fixture (rc=0)" || bad "arch-scan.py rc=$rc: $out"

# ── 7. dispatch-verify.py: --scan sandbox rỗng → rc 0 + thông điệp đúng ──
mkdir -p "$SB/dv/.git"
out=$(python3 "$ROOT/harness/scripts/dispatch-verify.py" --root "$SB/dv" --scan 2>&1); rc=$?
[ $rc -eq 0 ] && echo "$out" | grep -q "khong co draft" \
  && ok "dispatch-verify.py --scan báo đúng 'không có draft' (rc=0)" || bad "dispatch-verify.py rc=$rc: $(echo "$out" | head -3)"

# ── 8. embed-voyage.py: fail-path là HỢP ĐỒNG mem-rank dựa vào — key vắng → stderr + rc≠0 ──
out=$(env -u VOYAGE_API_KEY python3 "$ROOT/harness/scripts/embed-voyage.py" "text" 2>&1); rc=$?
[ $rc -ne 0 ] && echo "$out" | grep -q "VOYAGE_API_KEY unset" \
  && ok "embed-voyage.py fail-loud đúng hợp đồng khi key vắng" || bad "embed-voyage.py rc=$rc out=$out"

# ── 9. embed-ollama.py: host chết → rc≠0, stdout im lặng (mem-rank fallback dựa vào) ──
out=$(OLLAMA_HOST="http://127.0.0.1:9" python3 "$ROOT/harness/scripts/embed-ollama.py" "text" 2>/dev/null); rc=$?
[ $rc -ne 0 ] && [ -z "$out" ] && ok "embed-ollama.py fail im lặng + rc≠0 khi host chết" \
  || bad "embed-ollama.py rc=$rc stdout='$out'"

# ── 10. sync-template.py: remote URL rác → thông báo + rc 2 (fail-path tất định, 0 network) ──
mkdir -p "$SB/st"
printf '{"remote":"notaurl","includes":[]}\n' > "$SB/st/.template-manifest.json"
out=$(python3 "$ROOT/harness/scripts/sync-template.py" --root "$SB/st" --dry-run 2>&1); rc=$?
[ $rc -eq 2 ] && echo "$out" | grep -q "parse" \
  && ok "sync-template.py từ chối remote không parse được (rc=2)" || bad "sync-template.py rc=$rc: $out"

# ── 11. sync-skills.py: sinh mirror thật → --check xanh → phá mirror → --check đỏ ──
T="$SB/ss"; clone_tool "$T" harness/scripts/sync-skills.py
mkdir -p "$T/skills/smoke-sk"; cp "$SB/skills/smoke-sk/SKILL.md" "$T/skills/smoke-sk/"
python3 "$T/harness/scripts/sync-skills.py" >/dev/null 2>&1
python3 "$T/harness/scripts/sync-skills.py" --check >/dev/null 2>&1; rc=$?
[ $rc -eq 0 ] && ok "sync-skills.py sinh mirror rồi --check xanh" || bad "sync-skills.py --check đỏ ngay sau sinh (rc=$rc)"
find "$T/llmwiki/skills" -name '*.md' | head -1 | xargs -I{} sh -c 'echo drift >> {}'
python3 "$T/harness/scripts/sync-skills.py" --check >/dev/null 2>&1; rc=$?
[ $rc -ne 0 ] && ok "sync-skills.py --check ĐỎ khi mirror bị phá (fire-drill)" || bad "sync-skills.py --check không bắt drift"

# ── 12. skill-registry.py: report thật trên repo (read-only) ──
out=$(python3 "$ROOT/harness/scripts/skill-registry.py" 2>&1); rc=$?
[ $rc -eq 0 ] && [ -n "$out" ] && ok "skill-registry.py report chạy được trên repo thật" \
  || bad "skill-registry.py rc=$rc: $(echo "$out" | head -2)"

# ── 13. harness-lint.py (mech:harness-lint): --check thật trên repo — đỏ là drift THẬT ──
out=$(python3 "$ROOT/harness/scripts/harness-lint.py" --check 2>&1); rc=$?
[ $rc -eq 0 ] && ok "harness-lint.py --check xanh trên repo (mech harness-lint sống)" \
  || bad "harness-lint.py --check rc=$rc: $(echo "$out" | tail -3)"

# ── 14. ovs-notes.py (skill:ovs-notes): --here đọc git tag local, offline-ok.
#     Repo có tag → phải in nhãn nguồn + tag; checkout shallow (CI không tag) →
#     vẫn phải rc=0 + nhãn nguồn "chưa có release" (hợp đồng NHÃN NGUỒN bắt buộc). ──
out=$(cd "$ROOT" && python3 harness/scripts/ovs-notes.py --here 2>&1); rc=$?
if [ -n "$(git -C "$ROOT" tag 2>/dev/null | head -1)" ]; then
  [ $rc -eq 0 ] && echo "$out" | grep -q "nguồn" && echo "$out" | grep -qE 'v[0-9]+\.[0-9]+' \
    && ok "ovs-notes.py --here in release notes có nhãn nguồn + tag" || bad "ovs-notes.py rc=$rc: $(echo "$out" | head -2)"
else
  [ $rc -eq 0 ] && echo "$out" | grep -qE 'nguồn|chưa có release' \
    && ok "ovs-notes.py --here (repo không tag) vẫn rc=0 + nhãn nguồn" || bad "ovs-notes.py rc=$rc: $(echo "$out" | head -2)"
fi

# ── 15. artifacts.py: --report trong sandbox → MANIFEST.json thật ──
T="$SB/art"; clone_tool "$T" fdk/tools/artifacts.py fdk/tools/artifacts.config.yaml
mkdir -p "$T/llmwiki/html" "$T/llmwiki/wiki/sources/draft" "$T/llmwiki/wiki/draft/orca"
printf '<html><title>smoke</title></html>\n' > "$T/llmwiki/html/180726-smoke.html"
out=$(python3 "$T/fdk/tools/artifacts.py" --report 2>&1); rc=$?
if [ $rc -eq 0 ] && python3 -c "import json;json.load(open('$T/fdk/MANIFEST.json'))" 2>/dev/null; then
  ok "artifacts.py --report sinh MANIFEST.json hợp lệ"
else bad "artifacts.py rc=$rc: $(echo "$out" | head -2)"; fi

# ── 16. build-cheatsheet.py: nhồi skilldata vào trang fixture ──
printf '<html><body><p>cheat</p><script>void 0;</script></body></html>\n' > "$SB/cheat.html"
out=$(python3 "$ROOT/fdk/tools/build-cheatsheet.py" "$SB/cheat.html" "$SB/skills" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q 'id="skilldata"' "$SB/cheat.html" && grep -q 'smoke-sk' "$SB/cheat.html" \
  && ok "build-cheatsheet.py nhồi block skilldata chứa smoke-sk" || bad "build-cheatsheet.py rc=$rc: $out"

# ── 17. build-docs-index.py: sandbox-repo → sinh index.html ──
T="$SB/bdi"; clone_tool "$T" fdk/tools/build-docs-index.py
mkdir -p "$T/llmwiki/html"
printf '<html><head><title>Smoke Doc</title></head><body>x</body></html>\n' > "$T/llmwiki/html/180726-smoke-doc.html"
out=$(python3 "$T/fdk/tools/build-docs-index.py" 2>&1); rc=$?
[ $rc -eq 0 ] && grep -q "Smoke Doc" "$T/llmwiki/html/index.html" 2>/dev/null \
  && ok "build-docs-index.py sinh index.html có tiêu đề fixture" || bad "build-docs-index.py rc=$rc: $(echo "$out" | head -2)"

# ── 18. build-health-dashboard.py: sandbox-repo → sinh dashboard HTML ──
T="$SB/bhd"; clone_tool "$T" fdk/tools/build-health-dashboard.py
mkdir -p "$T/llmwiki/html" "$T/skills/smoke-sk"; cp "$SB/skills/smoke-sk/SKILL.md" "$T/skills/smoke-sk/"
out=$(python3 "$T/fdk/tools/build-health-dashboard.py" 2>&1); rc=$?
[ $rc -eq 0 ] && [ -s "$T/llmwiki/html/280626-health-dashboard.html" ] \
  && ok "build-health-dashboard.py sinh dashboard trong sandbox" || bad "build-health-dashboard.py rc=$rc: $(echo "$out" | head -2)"

# ── 19. build-skill-search.py: build index BM25 rồi find-skill ra đúng skill ──
T="$SB/bss"; clone_tool "$T" fdk/tools/build-skill-search.py
mkdir -p "$T/skills/smoke-sk" "$T/fdk"; cp "$SB/skills/smoke-sk/SKILL.md" "$T/skills/smoke-sk/"
out=$(python3 "$T/fdk/tools/build-skill-search.py" build 2>&1); rc=$?
[ $rc -eq 0 ] && [ -s "$T/fdk/skills.search.json" ] && ok "build-skill-search.py build sinh index" \
  || bad "build-skill-search.py build rc=$rc: $out"
out=$(python3 "$T/fdk/tools/build-skill-search.py" find-skill "smoke harness" 2>&1)
echo "$out" | grep -q "smoke-sk" && ok "build-skill-search.py find-skill xếp hạng ra smoke-sk" \
  || bad "build-skill-search.py find-skill không thấy smoke-sk: $out"

# ── 20. whiteboard-skill-map.py: sandbox-repo (kèm 3 engine nó import) → sinh đồ thị ──
T="$SB/wsm"; clone_tool "$T" fdk/tools/whiteboard-skill-map.py fdk/tools/build-wiki-graph.py \
  fdk/tools/build-overstack-docs.py harness/scripts/sync-skills.py
mkdir -p "$T/llmwiki/html" "$T/skills/smoke-sk"; cp "$SB/skills/smoke-sk/SKILL.md" "$T/skills/smoke-sk/"
out=$(python3 "$T/fdk/tools/whiteboard-skill-map.py" --static 2>&1); rc=$?
[ $rc -eq 0 ] && [ -s "$T/llmwiki/html/skill-whiteboard.html" ] \
  && ok "whiteboard-skill-map.py --static sinh bản đồ skill trong sandbox" \
  || bad "whiteboard-skill-map.py rc=$rc: $(echo "$out" | head -3)"

# ── 21. wiki-relations.py: --dry-run KHÔNG được đụng file (hợp đồng dry-run) ──
sum_before=$(cat "$SB/wiki/concepts/page-a.md")
out=$(python3 "$ROOT/fdk/tools/wiki-relations.py" "$SB/wiki" --dry-run 2>&1); rc=$?
sum_after=$(cat "$SB/wiki/concepts/page-a.md")
[ $rc -eq 0 ] && [ "$sum_before" = "$sum_after" ] \
  && ok "wiki-relations.py --dry-run chạy sạch, không sửa file" || bad "wiki-relations.py rc=$rc hoặc dry-run có side-effect"

# ── 22. docs-curate.py (skill:docs-curate): plan trong sandbox-repo → phân loại thật ──
T="$SB/dc"; clone_tool "$T" fdk/tools/docs-curate.py
mkdir -p "$T/llmwiki/html" "$T/llmwiki/wiki/sources/draft" "$T/harness/metrics"
printf '<html><title>a</title></html>\n' > "$T/llmwiki/html/180726-smoke.html"
printf -- '---\ntitle: draft smoke\n---\nnoi dung\n' > "$T/llmwiki/wiki/sources/draft/180726-smoke.md"
out=$(python3 "$T/fdk/tools/docs-curate.py" plan 2>&1); rc=$?
[ $rc -eq 0 ] && echo "$out" | grep -q "plan" && ok "docs-curate.py plan phân loại kho fixture (rc=0)" \
  || bad "docs-curate.py rc=$rc: $(echo "$out" | head -3)"

# ── 23. stop.py (mech:medic-mirror): payload ngoài framework → fail-open rc 0 ──
out=$(printf '{"session_id":"smoke","transcript_path":"%s/nope.jsonl","cwd":"%s"}' "$SB" "$SB" \
      | python3 "$ROOT/llmwiki/.claude/hooks/stop.py" 2>&1); rc=$?
[ $rc -eq 0 ] && ok "stop.py (medic-mirror) fail-open rc=0 với payload sandbox" \
  || bad "stop.py rc=$rc: $(echo "$out" | head -2)"

echo
if [ $fail -eq 0 ]; then echo "engines-smoke-test: PASS (23 nhóm assert)"; else
  echo "engines-smoke-test: FAIL ($fail assert đỏ)"; exit 1; fi
