---
name: orca-onboard
description: "Parallel codebase onboarding — distilled understand-anything pipeline (scan + git history + batch analyze + layers/tour, no plugin), then domain enrichment (Claude), wiki + HTML via opencode+DeepSeek Flash v4."
requires:
  - name: docs-site-macos
    source: rheinmir/setup@orca
    install: "npx skills add rheinmir/setup@orca --skill docs-site-macos --global -y"
---

# orca-onboard

> 🧭 Dispatch backend — chọn agent/model rẻ, chạy nhiều worker song song, cú pháp opencode/orchestration → xem **orca-dispatch-reference** (nguồn chân lý duy nhất, đừng nhân bản syntax ở đây).

Onboard codebase via distilled understand-anything pipeline (graph + git history, no plugin), then domain enrichment + wiki + HTML.

## Triggers
- "onboard codebase", "analyze codebase", "knowledge graph", "guided tour"

## Options
- `--full` — Delete `.understand-anything/` and rebuild
- `--update` — Incremental: re-analyze only changed files since last run
- `--language <lang>` — Output language (vi, en, zh, ...)
- `--skip-wiki` — Skip wiki generation
- `<path>` — Target directory (default: `.`)

## Progress
```
[Phase 1/4] Graph generation (scan + git history + batch analyze + layers/tour)...
[Phase 2/4] Domain enrichment (Claude)...
[Phase 3/4] Wiki generation (opencode + DeepSeek Flash v4)...
[Phase 4/4] HTML docs (opencode + DeepSeek Flash v4)...
```

---

## ⚠️ HARD RULES

⛔ **DO NOT run Phase 0.5 or Phases 1–4 until Phase 0 completes.**

**Strict order — no reversal:**
1. **Phase 0** → complete, verify `llmwiki/` exists ✅
2. **Phase 0.5 (Gate)** → create draft file FIRST, then ask user
3. **Phases 1–4** → execute, update status after EACH phase immediately

- `llmwiki/` missing → bootstrap in Phase 0, NEVER defer
- Bootstrap fail → STOP completely, report error
- After EACH phase → update draft status NOW, never at end

---

## Dispatch Rules

```
TASK TYPE          → AGENT               → MODEL
──────────────────────────────────────────────────────
Scan + git history → bash/python direct  → (no LLM)
Batch file analyze → python static parse → (no LLM — PRIMARY; opencode chỉ enrich)
Merge + validate   → python inline       → (no LLM)
Layers / tour      → Claude main thread  → Sonnet (never dispatch out)
Domain reasoning   → Claude main thread  → Sonnet (never dispatch out)
Wiki / HTML render → opencode            → opencode/deepseek-v4-flash-free
```

**Reasoning tasks MUST stay in Claude main thread. NO reasoning to opencode/agy.**
**opencode + DeepSeek: template fill, wiki render, HTML only.**

---

## Agent Binaries

| Agent | Binary | Default model | Check |
|-------|--------|--------------|-------|
| Antigravity | `agy` | Claude (Sonnet/Opus) | `agy --version` |
| OpenCode | `opencode` | Configurable | `opencode --version` |
| Kiro | `kiro-cli` | — | `kiro-cli --version` |

> **Không cần plugin Understand-Anything.** Phase 1 dùng phương pháp đã distill từ Understand-Anything (scan → batch analyze → merge → layers → tour → validate) viết thẳng trong skill này — chạy bằng bash/python + opencode prompt thuần + Claude main thread. Không cài thêm gì vào agy/opencode.

**OpenCode with DeepSeek Flash v4:**
```bash
opencode run "$SPEC" --model opencode/deepseek-v4-flash-free < /dev/null \
# Fallback if flag unsupported:
echo "$SPEC" | opencode --model opencode/deepseek-v4-flash-free
# Last resort: Claude main thread
```

---

## Status Update Helper

```bash
update_phase_status() {
  local keyword="$1"
  local status="$2"
  [ -z "$DRAFT_FILE" ] && echo "[WARN] DRAFT_FILE unset" && return 0
  local f=$(echo "$DRAFT_FILE" | tr '\\' '/')
  [ ! -f "$f" ] && echo "[WARN] DRAFT_FILE not found: $f" && return 0
  perl -i -pe "s/(\Q$keyword\E.*?)\| (?:pending|in-progress|done)/\$1| $status/g if /\Q$keyword\E/" "$f" \
    || sed -i "s/\(.*$(echo "$keyword" | sed 's/[^^]/[&]/g').*\)| [a-z-]*/\1| $status/" "$f" \
    || echo "[WARN] status update failed for: $keyword"
}
```

---

## Phase 0 — Pre-flight & Setup

```bash
# --- 1. Dependency check (agy optional — Phase 1 dùng distilled pipeline, không cần agy) ---
MISSING=()
opencode --version >/dev/null 2>&1  || MISSING+=("opencode")
ls ~/.agents/skills/docs-site-macos/SKILL.md >/dev/null 2>&1 || MISSING+=("docs-site-macos skill")

if [ ${#MISSING[@]} -gt 0 ]; then
  echo "❌ Missing dependencies:"
  for dep in "${MISSING[@]}"; do echo "   - $dep"; done
  echo ""
  echo "docs-site-macos: npx skills add rheinmir/setup@orca --skill docs-site-macos --global -y"
  exit 1
fi

# --- 2. Resume Mode check & Project Root resolution ---
if [[ "$1" == @* ]]; then
  DRAFT_FILE="${1#@}"
  DRAFT_FILE=$(echo "$DRAFT_FILE" | tr '\\' '/')
  RESUME_MODE=true
  PROJECT_ROOT=$(grep "Project root:" "$DRAFT_FILE" | grep -oP '(?<=`)[^`]+(?=`)' | head -1)
  PROJECT_ROOT=$(echo "$PROJECT_ROOT" | tr '\\' '/')
else
  RESUME_MODE=false
  PROJECT_ROOT=${1:-.}
  PROJECT_ROOT=$(echo "$PROJECT_ROOT" | tr '\\' '/')
fi

test -d "$PROJECT_ROOT" || { echo "❌ Project root directory not found: $PROJECT_ROOT"; exit 1; }

# --- 3. Update Mode check ---
UPDATE_MODE=false
for arg in "$@"; do
  [ "$arg" = "--update" ] && UPDATE_MODE=true
done

if [ "$UPDATE_MODE" = "true" ]; then
  [ ! -f "$PROJECT_ROOT/.understand-anything/knowledge-graph.json" ] \
    && echo "❌ --update requires existing graph. Run without --update first." && exit 1
  [ ! -f "$PROJECT_ROOT/.understand-anything/meta.json" ] \
    && echo "❌ --update requires meta.json. Run without --update first." && exit 1
  echo "[update] Incremental mode — reading changed files from meta.json"
  
  CHANGED_FILES=$(python3 -c "
import json, sys
meta = json.load(open('$PROJECT_ROOT/.understand-anything/meta.json'))
changed = meta.get('changedFiles', meta.get('changed', []))
print('\n'.join(changed))
" 2>/dev/null || echo "")

  if [ -z "$CHANGED_FILES" ]; then
    echo "[update] no changedFiles in meta.json — falling back to full rebuild"
    UPDATE_MODE=false
  else
    echo "[update] Changed files:"; echo "$CHANGED_FILES"
  fi
fi

# --- 4. Bootstrap llmwiki + harness if missing ---
# Harness có 2 mode: GLOBAL (~/.claude/harness + hooks trong ~/.claude/settings.json,
# bảo vệ mọi project llmwiki trên máy này) và PER-PROJECT (harness/ commit vào repo,
# bảo vệ teammate). Global đủ cho máy dev cá nhân — chỉ WARN per-project khi cả 2 thiếu.
GLOBAL_HARNESS=false
[ -f "$HOME/.claude/harness/hooks/pre_tool_use.py" ] \
  && grep -q 'harness/hooks/pre_tool_use.py' "$HOME/.claude/settings.json" 2>/dev/null \
  && GLOBAL_HARNESS=true
echo "[harness] global=$GLOBAL_HARNESS project=$([ -d "$PROJECT_ROOT/harness" ] && echo yes || echo no)"

if [ ! -d "$PROJECT_ROOT/llmwiki" ] || { [ "$GLOBAL_HARNESS" = "false" ] && [ ! -d "$PROJECT_ROOT/harness" ]; }; then
  echo "[orca-onboard] bootstrapping llmwiki + harness..."
  git clone https://github.com/rheinmir/setup.git /tmp/orca-llmwiki-bootstrap --depth 1 -b orca -q
  [ ! -d "$PROJECT_ROOT/llmwiki" ] && cp -r /tmp/orca-llmwiki-bootstrap/llmwiki "$PROJECT_ROOT/llmwiki"
  if [ "$GLOBAL_HARNESS" = "false" ] && [ ! -d "$PROJECT_ROOT/harness" ]; then
    bash /tmp/orca-llmwiki-bootstrap/harness/scripts/install-harness.sh "$PROJECT_ROOT" \
      && echo "[orca-onboard] harness installed OK" \
      || echo "[WARN] harness install failed/denied — user chạy 1 trong 2: 'install-harness.sh .' (per-project, cho team) hoặc 'install-harness.sh --global' (cả máy, khuyên dùng cho máy dev)"
  fi
  rm -rf /tmp/orca-llmwiki-bootstrap
  echo "[orca-onboard] bootstrap done"
fi

# --- 5. Create dirs ---
mkdir -p $PROJECT_ROOT/.orca-onboard/{intermediate,tmp}
mkdir -p $PROJECT_ROOT/llmwiki/wiki/draft/{cave,uiux,orca}

# --- 6. File count & availability check ---
git rev-parse HEAD 2>/dev/null > $PROJECT_ROOT/.orca-onboard/tmp/commit.txt
git ls-files > $PROJECT_ROOT/.orca-onboard/tmp/files.txt 2>/dev/null \
  || find $PROJECT_ROOT -type f \
       ! -path "*/.orca-onboard/*" ! -path "*/llmwiki/*" ! -path "*/.git/*" \
     > $PROJECT_ROOT/.orca-onboard/tmp/files.txt
FILE_COUNT=$(wc -l < $PROJECT_ROOT/.orca-onboard/tmp/files.txt | tr -d ' ')

# Probe agent availability
AGY_OK=$(agy --version 2>/dev/null && echo "✅ usable" || echo "❌ not found")
OC_OK=$(opencode --version 2>/dev/null && echo "✅ usable" || echo "❌ not found")
KIRO_OK=$(kiro-cli --version 2>/dev/null && echo "✅ usable" || echo "❌ not found")

echo "[pre-flight] $FILE_COUNT files | agy=$AGY_OK | opencode=$OC_OK"

# Parse statuses if in resume mode
parse_status() {
  local keyword="$1"
  awk '/## Agent Task Assignment/{p=1} p && /^## [^A]/{p=0} p' "$DRAFT_FILE" \
    | grep "$keyword" | grep -oE 'pending|in-progress|done' | head -1
}

if [ "$RESUME_MODE" = true ]; then
  PHASE1_STATUS=$(parse_status "Phase 1 —")
  PHASE2_STATUS=$(parse_status "Phase 2 —")
  PHASE3_STATUS=$(parse_status "Phase 3 —")
  PHASE4_STATUS=$(parse_status "Phase 4 —")
  echo "[Resume] P1=$PHASE1_STATUS P2=$PHASE2_STATUS P3=$PHASE3_STATUS P4=$PHASE4_STATUS"
fi
```

---

## Phase 0.5 — Gate

**Required: create draft file FIRST, then ask user. Never reverse this order.**

```bash
DATE=$(date +%d%m%y)
PROJECT_SLUG=$(basename "$PROJECT_ROOT" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
DRAFT_FILE="$PROJECT_ROOT/llmwiki/wiki/draft/orca/${DATE}-onboard-${PROJECT_SLUG}.md"

# Graph = distilled pipeline (no plugin): scan/history bash → batch opencode → layers/tour Claude
OC_AVAIL=$(opencode --version 2>/dev/null && echo "yes" || echo "no")
if [ "$OC_AVAIL" = "yes" ]; then
  AGENT_GRAPH="distilled pipeline: bash + opencode (batch) + Claude (layers/tour)"
else
  AGENT_GRAPH="distilled pipeline: bash + Claude main thread (opencode unavailable)"
fi

cat > "$DRAFT_FILE" << EOF
---
type: draft
title: ${DATE}-onboard-${PROJECT_SLUG}
status: proposed
tags: [orca-onboard, output-report]
timestamp: $(date +%Y-%m-%d)
---

# ${DATE}-onboard-${PROJECT_SLUG}

**Status:** proposed

## Agent CLI Availability
| Agent | Binary | Status |
|-------|--------|--------|
| Antigravity | \`agy\` | $AGY_OK |
| OpenCode | \`opencode\` | $OC_OK |
| Kiro | \`kiro-cli\` | $KIRO_OK |

## Agent Task Assignment
| Task | Agent | Model | Status |
|------|-------|-------|--------|
| Phase 1 — Graph generation ($FILE_COUNT files) | $AGENT_GRAPH | DeepSeek Flash v4 + Sonnet | pending |
| Phase 2 — Domain enrichment | Claude main thread | Sonnet | pending |
| Phase 3 — Wiki generation | opencode | DeepSeek Flash v4 | pending |
| Phase 4 — HTML docs | opencode | DeepSeek Flash v4 | pending |

## What
Onboard \`$PROJECT_ROOT\` — understand-anything graph, domain enrichment, wiki, HTML.

## Output
- \`.understand-anything/knowledge-graph.json\` (tree-sitter + Louvain)
- \`.understand-anything/ONBOARDING.md\` (~20k tokens distilled)
- \`.orca-onboard/intermediate/domain-graph.json\`
- \`llmwiki/wiki/\` (index, concepts, entities, architecture, tours)
- \`llmwiki/html/onboarding-${PROJECT_SLUG}.html\`
- \`llmwiki/html/wiki-graph.html\` (vector quan hệ concept↔code — STEP C)

## Files
| File | Action |
|------|--------|
| \`.understand-anything/knowledge-graph.json\` | created by Phase 1 pipeline |
| \`.understand-anything/ONBOARDING.md\` | created by Phase 1 pipeline |
| \`.orca-onboard/intermediate/domain-graph.json\` | created by Claude |
| \`llmwiki/wiki/index.md\` | created/modified |
| \`llmwiki/wiki/concepts/architecture.md\` | created |
| \`llmwiki/wiki/concepts/*.md\` | created |
| \`llmwiki/wiki/entities/*.md\` | created |
| \`llmwiki/wiki/concepts/onboarding-tour.md\` | created |
| \`llmwiki/html/onboarding-${PROJECT_SLUG}.html\` | created |
| \`llmwiki/html/wiki-graph.html\` | created by STEP C (vector) |

## Notes
- Invoked via: \`/orca-onboard\` skill
- Project root: \`$PROJECT_ROOT\`
- Files tracked: $FILE_COUNT
- Reasoning phases in Claude main thread — NOT dispatched to cheap models
- Mechanical phases: opencode + DeepSeek Flash v4

## Cost Estimate
| Phase | Agent | Est. tokens | Est. cost |
|-------|-------|-------------|-----------|
| Phase 1 (graph) | bash + opencode batches + Claude layers/tour | ~1.5M (DeepSeek) + ~50k (Sonnet) | ~\$0.50 |
| Phase 2 (domain) | Claude Sonnet | ~50k | ~\$0.50 |
| Phase 3 (wiki) | DeepSeek Flash | ~100k | ~\$0.02 |
| Phase 4 (HTML) | DeepSeek Flash | ~50k | ~\$0.01 |

## Origin
- **Draft:** \`wiki/draft/orca/${DATE}-onboard-${PROJECT_SLUG}.md\`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
EOF

# Update wiki index + log
echo "| [${DATE}-onboard-${PROJECT_SLUG}](draft/orca/${DATE}-onboard-${PROJECT_SLUG}.md) | draft | $(date +%Y-%m-%d) |" >> "$PROJECT_ROOT/llmwiki/wiki/index.md"
echo "## $(date +%Y-%m-%d) — orca-onboard — onboard-${PROJECT_SLUG}" >> "$PROJECT_ROOT/llmwiki/wiki/log.md"

echo "DRAFT_FILE=$DRAFT_FILE"

# --- Terminal dispatch board (REQUIRED — must print in terminal BEFORE the gate question) ---
P1_NOTE="(distilled pipeline: 1.1-1.2 bash, 1.3 opencode batches, 1.4/1.6 python, 1.5 Claude)"

echo ""
echo "==================== ORCA-ONBOARD DISPATCH BOARD ===================="
echo " Project : $PROJECT_SLUG"
echo " Files   : $FILE_COUNT"
echo " Draft   : $DRAFT_FILE"
echo "----------------------------------------------------------------------"
printf " %-7s %-22s %-24s %-20s %s\n" "PHASE" "TASK" "AGENT" "MODEL" "EST.COST"
printf " %-7s %-22s %-24s %-20s %s\n" "1" "Graph generation" "bash+opencode+Claude" "DeepSeek+Sonnet" "~\$0.50"
printf " %-7s %-22s %-24s %-20s %s\n" "2" "Domain enrichment" "Claude main thread" "Sonnet" "~\$0.50"
printf " %-7s %-22s %-24s %-20s %s\n" "3" "Wiki generation" "opencode" "DeepSeek Flash v4" "~\$0.02"
printf " %-7s %-22s %-24s %-20s %s\n" "4" "HTML docs" "opencode" "DeepSeek Flash v4" "~\$0.01"
[ -n "$P1_NOTE" ] && echo " Phase 1 $P1_NOTE"
echo "======================================================================"

# --- Print propose file path + content (REQUIRED — user reviews this before approving) ---
echo ""
echo "PROPOSE FILE: $DRAFT_FILE"
echo "----------------------------------------------------------------------"
cat "$DRAFT_FILE"
```

⛔ The dispatch board AND the propose file content above MUST be printed via bash (visible in terminal) — restating them only in chat or only in the draft file is NOT sufficient. The user gates orchestration based on this board + propose. The draft's Agent Task Assignment rows must match the board (e.g. if Phase 1 is rerouted to opencode for >100 files, the draft must say opencode, not agy).

Ask for confirmation before continuing.

---

## Phase 1 — Graph Generation (distilled understand-anything — KHÔNG cần plugin)

**Pipeline:** scan (bash) → git history (bash) → batch analyze (opencode + DeepSeek) → merge (python) → layers + tour (Claude main thread) → validate + save (python + Claude). Phương pháp distill từ Understand-Anything; mọi prompt/schema nằm ngay dưới đây — không dispatch `/understand`, không cài plugin.

**Required output:**
- `.understand-anything/knowledge-graph.json` (nodes, edges, layers, tour)
- `.understand-anything/ONBOARDING.md` (~20k tokens distilled)
- `.understand-anything/meta.json`

**Skip check:** `RESUME_MODE=true` + `PHASE1_STATUS=done` → skip to Phase 2.

**Decision table:**

| Graph exists | Flag | Action |
|-------------|------|--------|
| No | (none) | full pipeline |
| Yes | (none) | skip Phase 1, use existing graph |
| Yes | `--update` | re-analyze only `git diff <meta.gitCommitHash>..HEAD --name-only` files, merge into existing graph |
| Yes | `--full` | delete `.understand-anything/`, full pipeline |

### 1.1 SCAN (bash — no LLM)

```bash
mkdir -p "$PROJECT_ROOT/.understand-anything" "$PROJECT_ROOT/.orca-onboard/tmp"
git -C "$PROJECT_ROOT" ls-files > "$PROJECT_ROOT/.orca-onboard/tmp/files.txt"
# Loại file nhị phân/lock/vendor; phân loại theo extension: code/config/docs/infra/data/script
# Đọc context: README (3000 chars đầu), manifest (package.json/pyproject.toml/Cargo.toml/go.mod), dir tree 2 cấp
# Detect entry point: src/index.ts, main.py, app.py, main.go, src/main.rs, cmd/*/main.go, manage.py, __main__.py...
```

### 1.2 GIT HISTORY (bash — no LLM)

Tín hiệu lịch sử git làm giàu graph — thứ phân tích tĩnh không có:

```bash
# Churn — file nóng (hay sửa nhất, 365 ngày)
git -C "$PROJECT_ROOT" log --since="365 days ago" --name-only --pretty=format: \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -40 > "$PROJECT_ROOT/.orca-onboard/tmp/churn.txt"
# Recent — file vừa đổi (30 ngày)
git -C "$PROJECT_ROOT" log --since="30 days ago" --name-only --pretty=format: | grep -v '^$' | sort -u \
  > "$PROJECT_ROOT/.orca-onboard/tmp/recent.txt"
# Commit subjects gần nhất — chủ đề đang phát triển
git -C "$PROJECT_ROOT" log --since="90 days ago" --pretty=format:'%s' | head -50 \
  > "$PROJECT_ROOT/.orca-onboard/tmp/recent-subjects.txt"
# Co-change — python đọc `git log --name-only` theo commit, đếm cặp file đổi cùng nhau, ngưỡng ≥3
```

Áp dụng: top churn → tag node `hot`; trong recent.txt → tag `recent`; cặp co-change ≥3 → edge `related` (weight 0.5); tour + ONBOARDING ưu tiên file `hot`; recent-subjects cho mục "What's being worked on".

### 1.3 ANALYZE — PRIMARY: static parse (0 token) · opencode chỉ để enrich

**Mặc định dùng python static parse** (bài học run 120626-zca-bridge — vừa rẻ vừa deterministic):
regex `import/export ... from` + `require()` → resolve relative path → edges `imports`;
`test/**.test.ts` → `tested_by`; summary = comment đầu file / danh sách exports / heading md;
type theo extension (file/config/document). Imports là việc mechanical — LLM không chính xác hơn regex.
Chỉ dispatch opencode khi cần summary giàu ngữ nghĩa hơn cho file phức tạp (optional enrichment):

Chia file list thành batch ~25 file (file liên quan cùng batch: Dockerfile+compose, migrations, CI configs, docs). Mỗi batch dispatch:

```bash
opencode run "$BATCH_SPEC" --model opencode/deepseek-v4-flash-free < /dev/null
# ⚠ KHÔNG thêm --dangerously-skip-permissions: Claude Code auto-mode classifier sẽ DENY lệnh dispatch.
# opencode treo chờ permission / bị chặn → dùng STATIC PARSE fallback bên dưới (ưu tiên mặc định).
```

`BATCH_SPEC` (inject đủ context — DeepSeek không tự đọc gì ngoài danh sách được giao):

> Analyze these files in project <name> (<description>, languages: <langs>). For EACH file produce GraphNode `{id, type, name, filePath, summary (1-2 câu), tags[]}` and GraphEdges `{source, target, type, weight}` for imports/calls/configures/documents visible in file content. Read each listed file. Write ONLY valid JSON `{"nodes":[...], "edges":[...]}` to `.orca-onboard/tmp/batch-<i>.json`. ID convention: `file:<relpath>`, `config:<relpath>`, `document:<relpath>`. Files: <list kèm line counts>

Tối đa 5 batch song song. Batch fail → retry 1 lần → fail nữa thì bỏ qua, ghi PHASE_WARNINGS (partial graph > no graph). opencode unavailable → Claude main thread tự analyze batch.

### 1.4 MERGE + NORMALIZE (python inline — no LLM)

Claude viết script `.orca-onboard/tmp/merge.py` (logic distill từ merge-batch-graphs.py của Understand-Anything): đọc mọi `batch-*.json` → gộp nodes/edges → chuẩn hoá ID prefix (bỏ double-prefix, thêm prefix thiếu) → dedupe node theo id (giữ bản cuối), edge theo (source,target,type) → drop edge dangling (log stderr) → thêm edges `related` từ co-change (1.2) → ghi `assembled-graph.json`.

### 1.5 LAYERS + TOUR (Claude main thread — REASONING, không dispatch)

Từ assembled-graph + dir tree + README:
- **Layers:** `[{id: "layer:<kebab>", name, description, nodeIds[]}]` — mỗi file-level node thuộc ĐÚNG MỘT layer; cấu trúc thư mục là bằng chứng mạnh nhất.
- **Tour:** 5-15 bước `[{order, title, description, nodeIds[]}]` — bước 1 luôn là project overview (README), theo entry point, ưu tiên file `hot`; kể cùng câu chuyện README kể nhưng qua code thật.

### 1.6 VALIDATE + SAVE (python + Claude)

Validate deterministic (script): không duplicate node ID, không dangling edge, mọi file node trong đúng 1 layer, tour nodeIds tồn tại, đếm orphan. Sửa tự động được thì sửa (drop dangling, fill default), còn lại ghi warning — partial graph vẫn save.

Ghi:
- `knowledge-graph.json`: `{version, project: {name, languages, frameworks, description, analyzedAt, gitCommitHash}, nodes, edges, layers, tour}`
- `meta.json`: `{lastAnalyzedAt, gitCommitHash, analyzedFiles}`
- `ONBOARDING.md` (Claude distill, ~20k tokens): overview, layers + mô tả, key flows, hot files + lý do (churn), "What's being worked on" (recent-subjects), tour narrative, stats.

Cuối: xoá `batch-*.json`, báo summary (files analyzed, nodes/edges by type, layers, tour steps, warnings).

### Schema (distill từ Understand-Anything)

- **Node types:** `file, function, class, module, concept, config, document, service, table, endpoint, pipeline, schema, resource` — ID: `<type>:<relpath>[:<name>]`
- **Edge types chính:** imports, exports, contains, inherits, implements, calls, reads_from, writes_to, depends_on, tested_by, configures, related, documents, deploys, triggers, routes, defines_schema
- **Weights:** contains 1.0 · inherits/implements 0.9 · calls/exports 0.8 · imports 0.7 · depends_on/configures 0.6 · còn lại 0.5

```bash
# Gate cuối Phase 1
[ ! -f "$PROJECT_ROOT/.understand-anything/knowledge-graph.json" ] \
  && echo "❌ Phase 1 FAIL: knowledge-graph.json missing" && exit 1
[ ! -f "$PROJECT_ROOT/.understand-anything/ONBOARDING.md" ] \
  && echo "❌ Phase 1 FAIL: ONBOARDING.md missing" && exit 1
echo "✅ Phase 1 done"
# update_phase_status "Phase 1 —" "done"
```

### 1.7 CODE-GRAPH MCP INDEX (optional — chỉ khi server `code-graph` có trong mcpServers)

Tầng truy vấn quan hệ code **chính xác theo line** bổ sung cho graph distill ở trên: `search_symbols`, `get_callers/callees` cho impact-check tức thì. Server `code-graph` (`~/.claude.json → mcpServers`) ghi 1 db SQLite mỗi repo tại `<repo>/.graph-agent/index.db`.

**Khi nào chạy:** project có submodule/repo code thật (Go/TS/Py…) **và code-graph THẬT SỰ dùng được** — kiểm bằng `python3 harness/scripts/dep-health.py --json` và đòi `status == "ok"`, ĐỪNG chỉ xem nó có được khai báo trong `~/.claude.json` hay không. Khai báo trong config ≠ server sống: DB 0 byte, DB thiếu bảng `symbols`, hay server đã chết đều vẫn "đang khai báo" (bài học 2026-07-20 — code-graph hỏng nhiều tuần mà mọi phiên vẫn bị lùa vào nó). `degraded`/`absent` thì bỏ qua bước này.

```bash
# 1. Index từng repo code (auto-detect root từ .git/go.mod/package.json).
#    Gọi MCP tool reindex_repo(<abs path repo>, force=true) cho MỖI repo code.
#    Lưu ý: code có thể nằm ở SUBDIR của submodule (vd <sub>/<svc>/go.mod chứ không phải <sub>/).
#    → trỏ vào thư mục chứa go.mod/package.json, không phải submodule root rỗng.
# 2. reindex_repo tự thêm repo vào registry ~/.graph-agent/repos.txt
#    → server --watch re-watch sau restart (durability).
# 3. Verify: get_stats() phải thấy symbols thật (>0), không phải stub.
echo "[1.7] code-graph: gọi reindex_repo cho mỗi repo code có manifest"
```

**Durability harness:** hook SessionStart `code_graph_keeper.py` (cài kèm install-harness.sh) tự re-register repo nếu rớt registry + cảnh báo repo chưa index. Fail-open, **no-op nếu project không dùng code-graph** — điều kiện là có `.graph-agent/index.db` **dùng được** (mở được + có bảng `symbols`/`files`), không phải chỉ có file: DB rỗng từng khiến keeper ghi nhầm registry và dập tắt luôn cảnh báo "chưa index". KHÔNG reindex per-edit (watcher đã lo, debounce 2s). Sau đó ghi 1 wiki concept page `concepts/code-graph-nav.md` (cách dùng tool + ví dụ caller trace) để team biết dùng.

> Freshness sau đó tự động: edit file → watcher reindex ~2s. Không cần reindex tay trừ khi clone mới hoặc đổi hàng loạt lúc server tắt.

---

## Phase 2 — Domain Enrichment

**Agent:** Claude main thread (no dispatch) | **Model:** Sonnet

> **READ FIRST** (in order, before writing anything):
> 1. `.understand-anything/ONBOARDING.md` — full read (~20k tokens)
> 2. `.understand-anything/knowledge-graph.json` — read `layers` array + `entry-point` tagged nodes ONLY (⛔ NOT full file — context overflow)
> 3. If `UPDATE_MODE=true`: read existing `.orca-onboard/intermediate/domain-graph.json` (merge, don't overwrite)

**DO:**
1. From entry points → identify HTTP endpoints / CLI commands / events / cron jobs
2. Reverse-engineer: entry point → flow (process) → steps (actions @ file:line)
3. Build `domain → flow → step` hierarchy
4. Write `.orca-onboard/intermediate/domain-graph.json`

**Domain graph schema:**
```json
{
  "domains": [
    {
      "id": "domain:order-management",
      "name": "Order Management",
      "flows": [
        {
          "id": "flow:create-order",
          "name": "Create Order",
          "steps": [
            { "order": 0.1, "id": "step:validate-input", "file": "src/orders/validator.ts", "line": 42 },
            { "order": 0.2, "id": "step:check-inventory", "file": "src/inventory/checker.ts", "line": 15 }
          ]
        }
      ]
    }
  ]
}
```

**Output:** `.orca-onboard/intermediate/domain-graph.json`

**Skip check:** `RESUME_MODE=true` + `PHASE2_STATUS=done` → skip to Phase 3.

```bash
if [ "$RESUME_MODE" != "true" ] || [ "$PHASE2_STATUS" != "done" ]; then
  update_phase_status "Phase 2 —" "in-progress"
  # Claude main thread — no dispatch
  if [ "$UPDATE_MODE" = "true" ] && [ -n "$CHANGED_FILES" ]; then
    echo "[Phase 2] Update mode: re-enrich domain steps for changed files only"
    # Read existing domain-graph.json
    # Filter steps with filePath in CHANGED_FILES
    # Re-analyze those steps from ONBOARDING.md
    # Merge back into domain-graph.json (keep unchanged steps)
  else
    echo "[Phase 2] Full domain enrichment from ONBOARDING.md"
    # Read ONBOARDING.md + layers from knowledge-graph.json, write new domain-graph.json
  fi
  update_phase_status "Phase 2 —" "done"
fi
```

---

## Phase 3 — Wiki Generation

**Agent:** opencode | **Model:** `opencode/deepseek-v4-flash-free`

> **READ FIRST** (inject into SPEC before dispatch — DeepSeek won't read files unless injected):
> 1. `.understand-anything/ONBOARDING.md` — full read
> 2. `.orca-onboard/intermediate/domain-graph.json` — full read
> 3. If `UPDATE_MODE=true`: grep `llmwiki/wiki/` for refs to `CHANGED_FILES` → identify stale pages
> - ⛔ DO NOT read `.understand-anything/knowledge-graph.json` — too large, context overflow

**DO:** Fill wiki templates from distilled content. No reasoning — mechanical template fill.

**Output structure:**
```
llmwiki/wiki/
├── index.md
├── concepts/          ← architecture.md, message-sync/flows, onboarding-tour.md (R5: KHÔNG tạo folder architecture/ hay tours/ — validator folder_structure chặn)
└── entities/          ← domain entities + project-structure.md
# Mọi trang PHẢI có '## Origin' (R2) và row trong index.md (R3)
```

**Skip check:** `RESUME_MODE=true` + `PHASE3_STATUS=done` → skip to Phase 4.

```bash
if [ "$RESUME_MODE" != "true" ] || [ "$PHASE3_STATUS" != "done" ]; then
  update_phase_status "Phase 3 —" "in-progress"

  if [ "$UPDATE_MODE" = "true" ] && [ -n "$CHANGED_FILES" ]; then
    STALE_PAGES=$(grep -rl "$CHANGED_FILES" "$PROJECT_ROOT/llmwiki/wiki/" 2>/dev/null | tr '\n' ' ')
    if [ -n "$STALE_PAGES" ]; then
      echo "[Phase 3] Stale wiki pages: $STALE_PAGES"
      SPEC="Update these wiki pages based on changes in ONBOARDING.md: $STALE_PAGES
Changed source files: $CHANGED_FILES
Do NOT regenerate unchanged pages. Preserve existing content in unchanged pages."
    else
      echo "[Phase 3] No stale wiki pages — skipping"
      update_phase_status "Phase 3 —" "done"
    fi
  else
    SPEC="Generate wiki pages from .understand-anything/ONBOARDING.md and .orca-onboard/intermediate/domain-graph.json.
Create: llmwiki/wiki/index.md, llmwiki/wiki/concepts/*.md (architecture.md + flow pages + onboarding-tour.md),
llmwiki/wiki/entities/*.md (domain entities + project-structure.md).
R5: chỉ được ghi vào concepts/ hoặc entities/. R2: mọi trang có '## Origin'. R3: cập nhật index.md.
Use wikilink format [[page-name]]. Do NOT read knowledge-graph.json directly."
  fi

  opencode run "$SPEC" --model opencode/deepseek-v4-flash-free < /dev/null \
    || echo "[WARN] opencode unavailable — Claude main thread fallback for wiki"

  update_phase_status "Phase 3 —" "done"
fi
```

---

## Phase 4 — HTML Docs (skeleton v2 + JSON island)

**Agent:** assemble JSON = opencode (mechanical) / Claude fallback · **fill skeleton = python (no LLM)**

**Cách hoạt động (KHÁC bản cũ — chống sơ sài + đứt UX):** KHÔNG để model sinh HTML thô
(DeepSeek tự chế CSS/JS → mất "gương", ấn không ăn, output 173–816 dòng không ổn định).
Thay vào đó: model CHỈ phát **một object JSON** theo schema; UI do **skeleton v2 frozen**
(`assets/docs-site-skeleton.html`, đã áp đúng design-system `/docs-site-macos`) render.
Skeleton = nav 5 tab CỐ ĐỊNH (Overview/Architecture/Guided Tour/Modules/Docker) + sidebar
fixed + collapse + scroll-spy + tour master-detail + draggable diagram; **Modules/Docker tự
ẩn khi mono**. Nội dung con (layer/tour/module/docker) DATA-DRIVEN từ JSON.

> **READ FIRST** (nguồn GIÀU — inject vào SPEC; DeepSeek không tự đọc file):
> 1. `.understand-anything/ONBOARDING.md` — full (overview, hot files, flows, tour narrative)
> 2. `.orca-onboard/intermediate/domain-graph.json` — domain→flow→step (tour + lifecycle)
> 3. `knowledge-graph.json` **chỉ** `layers` + `tour` + node entry-point (⛔ KHÔNG full — overflow)
> ⛔ KHÔNG dùng wiki md mỏng làm nguồn chính (đó là lý do bản cũ sơ sài).

**Skip check:** `RESUME_MODE=true` + `PHASE4_STATUS=done` → skip.

```bash
if [ "$RESUME_MODE" != "true" ] || [ "$PHASE4_STATUS" != "done" ]; then
  update_phase_status "Phase 4 —" "in-progress"

  # --- locate skeleton v2 ---
  SKELETON=$(ls ~/.agents/skills/orca-onboard/assets/docs-site-skeleton.html \
                ~/.claude/skills/orca-onboard/assets/docs-site-skeleton.html \
                "$PROJECT_ROOT/skills/orca-onboard/assets/docs-site-skeleton.html" 2>/dev/null | head -1)
  [ -z "$SKELETON" ] && echo "❌ Phase 4: skeleton v2 not found" && exit 1

  # --- detect Docker (multi-service → tab Docker; mono → docker:null, Modules:[]) ---
  DKFILE=$(ls "$PROJECT_ROOT"/docker-compose.y*ml "$PROJECT_ROOT"/compose.y*ml 2>/dev/null | head -1)
  N_SVC=0; [ -n "$DKFILE" ] && N_SVC=$(grep -cE '^  [a-zA-Z0-9_-]+:' "$DKFILE" 2>/dev/null || echo 0)
  echo "[Phase 4] skeleton=$SKELETON | compose=$DKFILE | services=$N_SVC"

  # --- STEP A: assemble ONBOARD_JSON (model emit JSON ONLY → file) ---
  JSON_OUT="$PROJECT_ROOT/.orca-onboard/tmp/onboard.json"
  SPEC="Đọc .understand-anything/ONBOARDING.md + .orca-onboard/intermediate/domain-graph.json.
Phát ra MỘT object JSON (KHÔNG markdown, KHÔNG giải thích) theo ĐÚNG schema trong header của
$SKELETON, ghi vào $JSON_OUT. Yêu cầu chất lượng:
- project: name/subtitle/about thật; stack[] + versions[] từ manifest; stats[] (files, services, layers, tour steps).
- architecture.layers[] = layers thật; architecture.diagram.nodes[] (toạ độ trong ~760×rộng, rect≥70×30) + edges[] theo luồng.
- tour[] 5–15 bước, MỖI bước GIÀU: role(1-2 câu), file+line THẬT, in[]/out[], hot(churn), narr — KHÔNG 1–2 dòng.
- modules[] = mỗi container/image (đọc $DKFILE): name,img,meta(port/env/volume),life[[read|proc|write,desc]],arch. Repo mono ($N_SVC≤1) → modules:[].
- docker = {strategy, cmd[[text,c|p|]], table[[svc,img,cmd/port,deps]], order[]} nếu có compose; mono → docker:null."
  opencode run "$SPEC" --model opencode/deepseek-v4-flash-free < /dev/null 2>/dev/null \
    || echo "[Phase 4] opencode unavailable — Claude main thread tự assemble $JSON_OUT theo schema skeleton"
  # Nếu opencode treo/trống → Claude main thread đọc 2 nguồn trên, tự viết $JSON_OUT (reasoning OK ở đây).

  # --- STEP B: fill skeleton (python, no LLM) — thay {{TITLE}} + {{ONBOARD_JSON}} ---
  OUT="$PROJECT_ROOT/llmwiki/html/onboarding-${PROJECT_SLUG}.html"
  mkdir -p "$PROJECT_ROOT/llmwiki/html"
  python3 - "$SKELETON" "$JSON_OUT" "$OUT" <<'PY'
import json,sys,html
sk=open(sys.argv[1]).read(); data=json.load(open(sys.argv[2]))
name=(data.get("project") or {}).get("name","Project")
out=sk.replace("{{TITLE}}",html.escape(name)).replace("{{ONBOARD_JSON}}",json.dumps(data,ensure_ascii=False))
assert "{{ONBOARD_JSON}}" not in out and "{{TITLE}}" not in out, "token chưa thay hết"
open(sys.argv[3],"w").write(out); print("✅ filled →",sys.argv[3],len(out),"bytes")
PY

  ls "$OUT" && echo "✅ Phase 4 done" || echo "❌ Phase 4 FAIL: HTML not found"
  update_phase_status "Phase 4 —" "done"
fi
```

> **Fallback:** opencode chết/treo → Claude main thread tự đọc `ONBOARDING.md` +
> `domain-graph.json`, viết `$JSON_OUT` theo schema (đây là assemble dữ liệu, OK ở Claude),
> rồi chạy STEP B. KHÔNG bao giờ tự viết HTML thô — luôn qua skeleton v2.

**STEP C — vẽ vector `wiki-graph.html` (wiki vừa sinh ở Phase 3 → giờ CÓ concept để vẽ):**

Onboard đẻ wiki nhưng KHÔNG tự vẽ vector quan hệ — vẽ NGAY tại đây để dự án code-only kết thúc
onboard là có luôn vector (đúng nút thắt: `build-wiki-graph.py` đọc `llmwiki/wiki/*.md` + code, không
đọc thẳng code để đẻ concept). Fail-open, không chặn onboard.

```bash
# engine: repo-local → global (cùng thứ tự hook Stop resolve)
WG=$(ls "$PROJECT_ROOT/fdk/tools/build-wiki-graph.py" \
        "$HOME/.claude/harness/fdk/tools/build-wiki-graph.py" 2>/dev/null | head -1)
if [ -n "$WG" ] && [ -d "$PROJECT_ROOT/llmwiki/wiki" ]; then
  ALSO=""; [ -d "$PROJECT_ROOT/fdk/wiki" ] && ALSO="--also fdk/wiki"
  ( cd "$PROJECT_ROOT" && python3 "$WG" llmwiki/wiki $ALSO --code-root . ) \
    && echo "✅ vector: llmwiki/html/wiki-graph.html (concept↔code)" \
    || echo "⚠️ wiki-graph vẽ lỗi — không chặn onboard (Stop hook sẽ vẽ khi wiki/code đổi)"
else
  echo "⚠️ bỏ vẽ vector — thiếu engine build-wiki-graph.py (cài harness global) hoặc chưa có llmwiki/wiki"
fi
```

**After completion:**
```bash
lsof -ti :8765 >/dev/null 2>&1 || nohup npx serve -p 8765 > /tmp/serve.log 2>&1 &
echo "→ http://localhost:8765/llmwiki/html/onboarding-${PROJECT_SLUG}.html"
```

---

## Rules

- **READ BEFORE ACT** — each phase reads all inputs in `READ FIRST` block before any action. Never ask user about something already in a file.
- **NO full `knowledge-graph.json` reads after Phase 1** — use `ONBOARDING.md` instead
- Real file paths only — never fabricate
- Domain graph: only reference real file:line, verify against code
- Wiki: wikilink format `[[page-name]]`
- Tour: 5-15 steps, start with project overview
- Reasoning tasks (domain, architecture): Claude main thread only

## Errors

- Phase 1 batch fail (opencode) → retry 1 lần, fail nữa → Claude main thread tự analyze batch đó; ghi PHASE_WARNINGS
- Phase 1 fail (no graph) → kiểm tra batch-*.json có tồn tại không; merge script lỗi → đọc stderr, sửa, chạy lại
- Phase 2 domain empty → no HTTP/CLI/event entry points found; write empty domains array
- Phase 3 fail → check opencode model config; fallback Claude main thread
- Phase 4 fail → fallback: invoke docs-site-macos skill directly in Claude

---

## Output Report

After all phases complete, write propose draft to wiki.

**1. Filename:** `DDMMYY-<ten>.md` — today's date + 2-4 kebab-case summary words

**2. Write** `llmwiki/wiki/draft/orca/DDMMYY-<ten>.md`:

```
---
type: draft
title: DDMMYY-<ten>
status: proposed
tags: [orca-onboard, output-report]
timestamp: YYYY-MM-DD
---

# DDMMYY-<ten>

**Status:** proposed

## Agent Task Assignment
| Task | Agent | Model | Status |
|------|-------|-------|--------|
| Phase 1 — Graph generation | agy /understand | Claude (agy) | done |
| Phase 2 — Domain enrichment | Claude main | Sonnet | done |
| Phase 3 — Wiki generation | opencode | DeepSeek Flash v4 | done |
| Phase 4 — HTML docs | opencode | DeepSeek Flash v4 | done |

## What
<One sentence>

## Output
<Key artefacts>

## Files
| File | Action |
|------|--------|
| `.understand-anything/knowledge-graph.json` | created |
| `llmwiki/wiki/index.md` | created/modified |
| `llmwiki/html/onboarding-<slug>.html` | created |

## Notes
- Invoked via: `/orca-onboard` skill

## Origin
- **Draft:** `wiki/draft/orca/DDMMYY-<ten>.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
```

**3. Update wiki index & log:**
- `llmwiki/wiki/index.md` — append: `| [DDMMYY-<ten>](draft/orca/DDMMYY-<ten>.md) | draft | YYYY-MM-DD |`
- `llmwiki/wiki/log.md` — append: `## YYYY-MM-DD — orca-onboard — <ten>`

**4. Update statuses & sync push — REQUIRED:**
- Update Status column in draft file to reflect actual run
- Clone `rheinmir/setup` branch `orca`, copy updated SKILL.md, push:
  ```bash
  git clone git@github.com:rheinmir/setup.git /tmp/rheinmir-setup-sync -b orca --depth 1
  cp ~/.agents/skills/orca-onboard/SKILL.md /tmp/rheinmir-setup-sync/skills/orca-onboard/SKILL.md
  cd /tmp/rheinmir-setup-sync
  git add .
  git commit -m "skill: orca-onboard — wrap understand-anything, DeepSeek mechanical dispatch"
  git push origin orca
  rm -rf /tmp/rheinmir-setup-sync
  ```

> Skip Output Report only if skill produced zero artefacts and zero decisions.

---

## Output Report

After all phases complete, write propose draft to wiki.

**1. Filename:** `DDMMYY-<ten>.md` — today's date + 2-4 kebab-case summary words

**2. Write** `llmwiki/wiki/draft/orca/DDMMYY-<ten>.md`:

```
---
type: draft
status: proposed
tags: [orca-onboard, output-report]
proposed: YYYY-MM-DD
---
# DDMMYY-<ten>

## Agent Task Assignment
| Task | Agent | Model | Status |
|------|-------|-------|--------|
| Phase 1 — Graph generation | agy /understand | Claude (agy) | done |
| Phase 2 — Domain enrichment | Claude main | Sonnet | done |
| Phase 3 — Wiki generation | opencode | DeepSeek Flash v4 | done |
| Phase 4 — HTML docs | opencode | DeepSeek Flash v4 | done |

## What
<One sentence>

## Output
<Key artefacts>

## Files
| File | Action |
|------|--------|
| `.understand-anything/knowledge-graph.json` | created |
| `llmwiki/wiki/index.md` | created/modified |
| `llmwiki/html/onboarding-<slug>.html` | created |

## Notes
- Invoked via: `/orca-onboard` skill

## Origin
- **Draft:** `wiki/draft/orca/DDMMYY-<ten>.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
```

**3. Update wiki index & log:**
- `llmwiki/wiki/index.md` — append: `| [DDMMYY-<ten>](draft/orca/DDMMYY-<ten>.md) | draft | YYYY-MM-DD |`
- `llmwiki/wiki/log.md` — append: `## YYYY-MM-DD — orca-onboard — <ten>`

**4. Update statuses & sync push — REQUIRED:**
- Update Status column in draft file to reflect actual run
- Clone `rheinmir/setup` branch `orca`, copy updated SKILL.md, push:
  ```bash
  git clone git@github.com:rheinmir/setup.git /tmp/rheinmir-setup-sync -b orca --depth 1
  cp ~/.agents/skills/orca-onboard/SKILL.md /tmp/rheinmir-setup-sync/skills/orca-onboard/SKILL.md
  cd /tmp/rheinmir-setup-sync
  git add .
  git commit -m "skill: orca-onboard — wrap understand-anything, DeepSeek mechanical dispatch"
  git push origin orca
  rm -rf /tmp/rheinmir-setup-sync
  ```

> Skip Output Report only if skill produced zero artefacts and zero decisions.
