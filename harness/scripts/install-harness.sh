#!/usr/bin/env bash
# install-harness.sh — cài llmwiki harness stack (L0–L4) vào project.
# Idempotent. Tự detect 2 trường hợp:
#   NEW     : chưa có llmwiki/  → cài đủ, bật chặn ngay
#   MIGRATE : đã có llmwiki/    → cài + baseline audit, chỉ bật chặn khi hết nợ
#
# Usage:
#   bash harness/scripts/install-harness.sh [project_root]   # per-project (mặc định)
#   bash harness/scripts/install-harness.sh --global         # global: hooks vào ~/.claude (mọi project llmwiki trên máy)
#
# GLOBAL mode: copy hooks+validators vào ~/.claude/harness/hooks/, đăng ký 4 hooks
# vào ~/.claude/settings.json với shell guard `[ -d "$CLAUDE_PROJECT_DIR/llmwiki" ]`
# — project không có llmwiki chỉ tốn ~1ms/tool-call, không python, không audit,
# không false-positive (raw/ của data project, wiki/ của project ngoài).
# Global KHÔNG thay thế per-project cho team: teammate clone repo chỉ được bảo vệ
# khi harness/ + .claude/settings.json được commit vào repo (mode per-project).
# Global cũng KHÔNG cài pre-commit (L2) và không chạy baseline audit.
#
# Nguồn file: ưu tiên bundle cạnh script; thiếu thì clone $HARNESS_REPO@$HARNESS_REF
# (cả hai suy từ REPO_RAW nếu có — fork nào cũng cài được, xem khối 0).
set -euo pipefail

# ---------- Flag scan (tách --self-heal khỏi positional) ----------
# --self-heal: sau audit, installer TỰ backfill nợ (Origin+index+OKF) trong 1 process
# rồi re-audit 1 lần — gộp vòng lặp 3-reinstall của agent thành 1 lệnh bash.
SELF_HEAL=0
NO_CLONE=0
ALL_SUBREPOS=0
PRINT_REF=0
ARGS=()
for a in "$@"; do
  case "$a" in
    --self-heal)    SELF_HEAL=1 ;;
    --no-clone)     NO_CLONE=1 ;;
    --all-subrepos) ALL_SUBREPOS=1 ;;
    --print-ref)    PRINT_REF=1 ;;   # in ref nguồn rồi thoát — để test được mà không clone thật
    *) ARGS+=("$a") ;;
  esac
done
set -- ${ARGS[@]+"${ARGS[@]}"}   # bash 3.2-safe khi mảng rỗng + set -u

if [ "${1:-}" = "--global" ]; then ROOT="$HOME"; else ROOT="$(cd "${1:-.}" && pwd)"; fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE="$(cd "$SCRIPT_DIR/../.." && pwd)"   # repo chứa harness/ + llmwiki/
TMP_CLONE=""

log()  { printf '\033[1;32m[harness]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[harness]\033[0m %s\n' "$*"; }

cleanup() { [ -n "${TMP_CLONE:-}" ] && rm -rf "${TMP_CLONE:-}" || true; [ -n "${TMP_SYNC:-}" ] && rm -rf "${TMP_SYNC:-}" || true; }
trap cleanup EXIT

# ---------- 0. Xác định nguồn ----------
# REF nguồn để clone. Mặc định nhánh chính; nhưng UAT canary cài từ raw của MỘT NHÁNH KHÁC,
# và trước đây 4 chỗ clone đều hardcode -b orca → hook/engine LUÔN lấy từ nhánh chính, tức
# canary MÙ với mọi thay đổi trong llmwiki/.claude/hooks, harness/scripts, harness/validators,
# fdk/tools. Cổng nghiệm thu chấm nhầm bản cũ mà vẫn xanh. Suy REF từ REPO_RAW (canary đã trỏ
# sẵn) nên không đẻ thêm biến người dùng phải nhớ; HARNESS_REF để ép tay khi cần.
HARNESS_REF="${HARNESS_REF:-}"
if [ -z "$HARNESS_REF" ] && [ -n "${REPO_RAW:-}" ]; then
  case "$REPO_RAW" in
    https://raw.githubusercontent.com/*/*/*)
      _r="${REPO_RAW#https://raw.githubusercontent.com/}"   # <owner>/<repo>/<ref...>
      _r="${_r#*/}"; _r="${_r#*/}"                          # <ref...> (giữ được ref có dấu /)
      [ -n "$_r" ] && HARNESS_REF="$_r"
      ;;
  esac
fi
HARNESS_REF="${HARNESS_REF:-orca}"

# REPO nguồn — cùng lớp lỗi với REF ở trên, phát hiện muộn hơn một vòng (UAT canary 2026-07-30).
# Lần trước sửa REF nhưng vẫn hardcode `rheinmir/setup` ở 6 chỗ clone, nên canary chạy từ một
# FORK suy đúng ref rồi lại clone repo GỐC ở ref đó → nhánh không tồn tại → cài global fail →
# mọi năng lực mới không tới tay, mà cổng local vẫn xanh vì nó cài từ working-tree. Suy owner/repo
# từ REPO_RAW y hệt cách suy ref, nên fork nào cũng UAT được mà không phải nhớ thêm biến;
# HARNESS_REPO để ép tay.
HARNESS_REPO="${HARNESS_REPO:-}"
if [ -z "$HARNESS_REPO" ] && [ -n "${REPO_RAW:-}" ]; then
  case "$REPO_RAW" in
    https://raw.githubusercontent.com/*/*/*)
      _s="${REPO_RAW#https://raw.githubusercontent.com/}"   # <owner>/<repo>/<ref...>
      _own="${_s%%/*}"; _s="${_s#*/}"; _rep="${_s%%/*}"
      [ -n "$_own" ] && [ -n "$_rep" ] && HARNESS_REPO="$_own/$_rep"
      ;;
  esac
fi
HARNESS_REPO="${HARNESS_REPO:-rheinmir/setup}"
[ "$PRINT_REF" = "1" ] && { echo "$HARNESS_REF"; exit 0; }

src_ok() { [ -d "$1/harness/validators" ] && [ -d "$1/llmwiki/.claude/hooks" ]; }
SRC="$BUNDLE"
if ! src_ok "$SRC"; then
  if [ "$NO_CLONE" = "1" ]; then
    warn "Bundle nguồn thiếu và --no-clone bật → fast-fail (không treo mạng). Cung cấp bundle rồi chạy lại."
    exit 1
  fi
  log "Bundle cạnh script thiếu file nguồn → clone template $HARNESS_REPO@$HARNESS_REF"
  TMP_CLONE="$(mktemp -d /tmp/llmwiki-harness-src.XXXXXX)"
  git clone --depth 1 -b "$HARNESS_REF" git@github.com:"$HARNESS_REPO".git "$TMP_CLONE" >/dev/null 2>&1 \
    || git clone --depth 1 -b "$HARNESS_REF" https://github.com/"$HARNESS_REPO".git "$TMP_CLONE" >/dev/null 2>&1
  SRC="$TMP_CLONE"
  src_ok "$SRC" || { warn "Template repo chưa có harness/ — sync template trước"; exit 1; }
fi

# ---------- 0.4. --all-subrepos: R12 v3 (C) — nhân gate2 (pre-push) ra mọi subrepo harnessed ----------
if [ "$ALL_SUBREPOS" = "1" ]; then
  LIST="$SRC/harness/poc-vendor-neutral/bin/list-subrepos.py"
  [ -f "$LIST" ] || { warn "thiếu list-subrepos.py — không quét được"; exit 1; }
  log "R12 v3: quét subrepo trong workspace $ROOT (gate2 = pre-push)"
  n=0; ok=0
  while IFS=$'\t' read -r path kind; do
    [ -n "$path" ] || continue
    n=$((n+1))
    GATEPATH="$path/harness/poc-vendor-neutral/bin/pull-gate.sh"
    if [ "$kind" != "target" ] || [ ! -f "$GATEPATH" ]; then
      warn "  skip $(basename "$path") ($kind — không có pull-gate.sh): gate2 cần harnessed repo"; continue
    fi
    if [ -d "$path/.git/hooks" ]; then
      cat > "$path/.git/hooks/pre-push" <<'PP'
#!/usr/bin/env bash
# harness R12 (C) gate2 — pull-before-push. Bypass khẩn: git push --no-verify
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
GATE="$ROOT/harness/poc-vendor-neutral/bin/pull-gate.sh"
[ -x "$GATE" ] || { echo "pre-push: thiếu pull-gate.sh — fail-open"; exit 0; }
exec "$GATE" gate2
PP
      chmod +x "$path/.git/hooks/pre-push"
      ok=$((ok+1)); log "  ✓ pre-push (gate2) → $(basename "$path")"
    else
      warn "  skip $(basename "$path") — không thấy .git/hooks (worktree/submodule?)"
    fi
  done < <(python3 "$LIST" "$ROOT" 2>/dev/null)
  log "--all-subrepos: gate2 cài cho $ok/$n subrepo target. Xong."
  exit 0
fi

# ---------- 0.5. GLOBAL mode ----------
if [ "${1:-}" = "--global" ]; then
  GH="$HOME/.claude/harness"
  mkdir -p "$GH/hooks/validators"
  cp "$SRC/llmwiki/.claude/hooks/"*.py "$GH/hooks/"
  cp "$SRC/harness/validators/"*.py "$GH/hooks/validators/"
  cp "$SRC/harness/scripts/health-check.py" "$GH/hooks/health-check.py"   # session_start.py tìm cạnh hooks
  # logger + capability-map XUỐNG CÙNG PROJECT (ADR-005): hooklib gọi code-logger cạnh hooks;
  # build-capabilities tự nhận bối cảnh downstream (global skills + rule đã cài).
  cp "$SRC/harness/scripts/code-logger.py" "$GH/hooks/code-logger.py"
  cp "$SRC/fdk/tools/build-capabilities.py" "$GH/hooks/build-capabilities.py"
  log "GLOBAL: hooks + validators + health-check + code-logger + build-capabilities → $GH/hooks/"

  # GLOBAL-SHARED engine + tools (council-036 · travel-policy v2 tầng global_shared): mirror cấu trúc
  # repo (fdk/tools, harness/scripts, harness/validators) để hooklib.resolve_tool + find_validators
  # tìm được engine ở ~/.claude/harness/<rel>. Mọi project được gác dùng CHUNG — cài 1 lần, update 1 chỗ,
  # KHÔNG copy vào từng repo. code_imports.py đi cùng build-wiki-graph.py (copy nguyên thư mục).
  mkdir -p "$GH/fdk/tools" "$GH/harness/scripts" "$GH/harness/validators" "$GH/llmwiki/personas"
  cp "$SRC/fdk/tools/"*.py         "$GH/fdk/tools/"        2>/dev/null || true
  cp "$SRC/harness/scripts/"*.py   "$GH/harness/scripts/"  2>/dev/null || true
  # personas travel theo engine (archetype.py --get đọc posture; UAT canary 260718 bắt preamble rỗng)
  cp "$SRC/llmwiki/personas/"*.md  "$GH/llmwiki/personas/" 2>/dev/null || true
  cp "$SRC/harness/validators/"*.py "$GH/harness/validators/" 2>/dev/null || true
  cp "$SRC/harness/"*.yaml         "$GH/harness/"          2>/dev/null || true
  # config đi CÙNG script đọc nó (mem-rank.py ⇄ mem-rank.config.yaml) — glob *.py bên trên bỏ sót,
  # script global đọc config repo-local là đường dẫn tới "chạy được ở máy này, chết ở máy khác".
  cp "$SRC/harness/scripts/"*.yaml  "$GH/harness/scripts/"  2>/dev/null || true
  cp "$SRC/harness/version.json"   "$GH/version.json"      2>/dev/null || true
  # Phase 1 v4 (council-038): poc-vendor-neutral (RÀO CHẮN R1-R17: bin/llmwiki-validate.py, policy.yaml,
  # gen-converters) → global. CI downstream (Phase 3) sẽ curl bootstrap → cài poc global → validate từ global;
  # pre-commit downstream trỏ ~/.claude/harness/... . Mirror cấu trúc để llmwiki-validate.py đọc policy.yaml cạnh nó.
  if [ -d "$SRC/harness/poc-vendor-neutral" ]; then
    mkdir -p "$GH/harness/poc-vendor-neutral"
    cp -R "$SRC/harness/poc-vendor-neutral/." "$GH/harness/poc-vendor-neutral/" 2>/dev/null || true
    log "GLOBAL-SHARED rào chắn: poc-vendor-neutral (validate + policy + converters) → $GH/harness/poc-vendor-neutral/"
  fi
  # TẦNG 3 (travel-policy.yaml framework_only) KHÔNG được ở lại global: các glob *.py bên trên copy
  # tất tay, nên gỡ lại đúng danh sách đã khai. Installer TIÊU THỤ policy — policy hết là văn bản mô tả
  # (đo 2026-07-20: 18/18 mục tầng 3 vẫn đi xuống global, tầng 3 khi đó là hư cấu).
  # Gác hai chiều bằng harness/validators/travel_policy_sync.py.
  # Danh sách nằm NGAY ĐÂY, không đọc travel-policy.yaml lúc chạy: script này được copy đi khắp nơi
  # (bundle, clone remote, bản đã cài trong repo target) nên mọi đường dẫn tới policy đều có thể trỏ
  # vào bản CŨ. Đo 2026-07-20: đọc policy runtime làm fresh-install-smoke đỏ vì script working-tree
  # gặp policy remote còn xếp medic.py ở tầng 3 → xoá medic khỏi global; mà smoke là cổng chặn push
  # ⇒ deadlock chỉ-xanh-sau-khi-push. Hằng số đi cùng script thì không bao giờ lệch pha với script.
  # Đồng bộ với travel-policy.yaml framework_only do harness/validators/travel_policy_sync.py gác.
  STRIP_TIER3="
fdk/tools/build-overstack-docs.py
fdk/tools/build-cheatsheet.py
fdk/tools/build-docs-index.py
fdk/tools/build-health-dashboard.py
fdk/tools/whiteboard-skill-map.py
fdk/tools/new-skill.py
harness/scripts/harness-lint.py
harness/scripts/harness-doctor.py
harness/scripts/fdk-gate.py
harness/scripts/sync-skills.py
harness/scripts/skill-registry.py
harness/scripts/bnal-selftest.py
harness/scripts/adapt-registry.py
harness/scripts/arch-scan.py
harness/scripts/audit.py
harness/scripts/dispatch-verify.py
"
  n=0
  for rel in $STRIP_TIER3; do
    if [ -f "$GH/$rel" ]; then rm -f "$GH/$rel"; n=$((n+1)); fi
  done
  log "GLOBAL: gỡ $n tool framework_only khỏi $GH — tầng 3 chỉ chạy ở repo framework"
  log "GLOBAL-SHARED engine: fdk/tools + harness/scripts + validators + *.yaml + version.json → $GH/ (mọi project dùng chung)"

  SETTINGS="$HOME/.claude/settings.json"
  [ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak.$(date +%s)" || echo '{}' > "$SETTINGS"
  python3 - << 'PYEOF'
import json, os
path = os.path.expanduser("~/.claude/settings.json")
cur = json.load(open(path))
HOOKS_DIR = '$HOME/.claude/harness/hooks'
def cmd(script):
    # if-guard (KHÔNG dùng `&& ... || true` — nó nuốt exit 2, mất khả năng chặn)
    # v4 (GH#63 Phase 2): gate theo .harness-stamp (hợp đồng install ghi ra, travel theo git)
    # thay vì [ -d llmwiki ] — repo chưa curl-bootstrap thì hook global KHÔNG fire (opt-in tường minh).
    return f'if [ -f "${{CLAUDE_PROJECT_DIR:-.}}/llmwiki/.harness-stamp" ]; then python3 "{HOOKS_DIR}/{script}"; fi'
# dọn entry harness-global đời cũ (guard [ -d llmwiki ] hoặc format khác) trước khi thêm bản mới —
# idempotent qua các lần đổi format, không để hook fire đôi; hook KHÁC của user giữ nguyên.
def _is_stale(c):
    return HOOKS_DIR in (c or "") and '/llmwiki/.harness-stamp" ]' not in (c or "")
tpl = {
    "PreToolUse":  [{"matcher": "Write|Edit|MultiEdit|NotebookEdit|Bash", "script": "pre_tool_use.py"},
                    {"matcher": "Bash", "script": "orca_guard.py"}],
    "PostToolUse": {"matcher": "Write|Edit|MultiEdit", "script": "post_tool_use.py"},
    "Stop":        {"matcher": None, "script": "stop.py"},
    "SessionEnd":  {"matcher": None, "script": "session_end.py"},
    "SessionStart": [{"matcher": None, "script": "session_start.py"},
                     {"matcher": None, "script": "code_graph_keeper.py"}],
    "UserPromptSubmit": {"matcher": None, "script": "user_prompt_submit.py"},
}
cur.setdefault("permissions", {}).setdefault("deny", [])
for d in ["Write(./llmwiki/raw/**)", "Edit(./llmwiki/raw/**)", "MultiEdit(./llmwiki/raw/**)"]:
    if d not in cur["permissions"]["deny"]:
        cur["permissions"]["deny"].append(d)
cur.setdefault("hooks", {})
for event, defs in list(cur["hooks"].items()):
    nd = []
    for d in defs:
        d["hooks"] = [h for h in (d.get("hooks") or []) if not _is_stale(h.get("command"))]
        if d.get("hooks"):
            nd.append(d)
    if nd:
        cur["hooks"][event] = nd
    else:
        cur["hooks"].pop(event, None)
for event, spec in tpl.items():
    defs = cur["hooks"].setdefault(event, [])
    for s in (spec if isinstance(spec, list) else [spec]):
        existing = {h.get("command") for d in defs for h in (d.get("hooks") or [])}
        c = cmd(s["script"])
        if c not in existing:
            entry = {"hooks": [{"type": "command", "command": c, "timeout": 30}]}
            if s["matcher"]:
                entry["matcher"] = s["matcher"]
            defs.append(entry)
json.dump(cur, open(path, "w"), indent=2, ensure_ascii=False)
print("[harness] GLOBAL: settings.json merged (backup .bak.*)")
PYEOF

  python3 -c "import json; json.load(open(\"$SETTINGS\"))" || { warn "settings.json hỏng — khôi phục từ backup!"; exit 1; }
  # Smoke: validator phải chặn được
  RC=0; echo '{"action":"write","file_path":"llmwiki/raw/x.md"}' | python3 "$GH/hooks/validators/no_write_raw.py" 2>/dev/null || RC=$?
  [ "$RC" = "2" ] && log "GLOBAL smoke OK: no_write_raw chặn đúng (rc=2)" || { warn "GLOBAL smoke FAIL (rc=$RC)"; exit 4; }
  log "GLOBAL HOÀN TẤT — restart session hoặc mở /hooks để reload. Per-project vẫn cần cho team (commit harness/ vào repo)."
  exit 0
fi

# ---------- 1. Detect mode ----------
if [ -d "$ROOT/llmwiki" ]; then MODE="migrate"; else MODE="new"; fi
SAME_BUNDLE=0; [ "$SRC" = "$ROOT" ] && SAME_BUNDLE=1
log "Project: $ROOT — mode: $MODE$([ $SAME_BUNDLE = 1 ] && echo ' (project chính là bundle — merge missing từ remote)')"

# ---------- 2. Khung llmwiki (mode new) ----------
if [ "$MODE" = "new" ]; then
  mkdir -p "$ROOT/llmwiki/wiki"/{concepts,entities,sources/adr,sources/draft,draft/orca} \
           "$ROOT/llmwiki"/{raw,html,skills}
  touch "$ROOT/llmwiki/raw/.gitkeep"
  [ -f "$ROOT/llmwiki/wiki/index.md" ] || printf '# Wiki Index\n\n| File | Type | Summary |\n|------|------|---------|\n' > "$ROOT/llmwiki/wiki/index.md"
  [ -f "$ROOT/llmwiki/wiki/log.md" ]   || printf '# Operation Log\n' > "$ROOT/llmwiki/wiki/log.md"
fi

# ---------- 3. L0 + validators + scripts + evals (vendor-neutral core) ----------
if [ "$SAME_BUNDLE" = "0" ]; then
  mkdir -p "$ROOT/harness"
  cp -R "$SRC/harness/validators" "$ROOT/harness/" 2>/dev/null || true
  mkdir -p "$ROOT/harness/scripts" "$ROOT/harness/evals"
  cp "$SRC/harness/policy.yaml"               "$ROOT/harness/policy.yaml"
  cp "$SRC/harness/recipe.md"                 "$ROOT/harness/recipe.md"
  cp "$SRC/harness/scripts/"*.py              "$ROOT/harness/scripts/" 2>/dev/null || true
  [ -f "$ROOT/harness/version.json" ] || cp "$SRC/harness/version.json" "$ROOT/harness/version.json" 2>/dev/null || true
  cp "$SRC/harness/scripts/install-harness.sh" "$ROOT/harness/scripts/install-harness.sh" 2>/dev/null || true
  [ -f "$ROOT/harness/evals/promptfooconfig.yaml" ] || cp "$SRC/harness/evals/promptfooconfig.yaml" "$ROOT/harness/evals/promptfooconfig.yaml"
else
  # SAME_BUNDLE=1 — pull all harness files from remote (overwrite local)
  if [ "$NO_CLONE" != "1" ]; then
    TMP_SYNC="$(mktemp -d /tmp/llmwiki-harness-sync.XXXXXX)"
    if git clone --depth 1 -b "$HARNESS_REF" git@github.com:"$HARNESS_REPO".git "$TMP_SYNC" >/dev/null 2>&1 \
        || git clone --depth 1 -b "$HARNESS_REF" https://github.com/"$HARNESS_REPO".git "$TMP_SYNC" >/dev/null 2>&1; then
      mkdir -p "$ROOT/harness/validators" "$ROOT/harness/scripts" "$ROOT/harness/evals" "$ROOT/harness/tests"
      cp -R "$TMP_SYNC/harness/validators/"*    "$ROOT/harness/validators/" 2>/dev/null || true
      cp    "$TMP_SYNC/harness/policy.yaml"      "$ROOT/harness/policy.yaml" 2>/dev/null || true
      cp    "$TMP_SYNC/harness/recipe.md"        "$ROOT/harness/recipe.md" 2>/dev/null || true
      cp    "$TMP_SYNC/harness/harness.md"       "$ROOT/harness/harness.md" 2>/dev/null || true
      cp    "$TMP_SYNC/harness/scripts/"*        "$ROOT/harness/scripts/" 2>/dev/null || true
      cp    "$TMP_SYNC/harness/tests/"*          "$ROOT/harness/tests/" 2>/dev/null || true
      cp    "$TMP_SYNC/harness/version.json"     "$ROOT/harness/version.json" 2>/dev/null || true
      cp    "$TMP_SYNC/harness/evals/"*          "$ROOT/harness/evals/" 2>/dev/null || true
      log "SAME_BUNDLE: pull all harness files from remote (overwrite)"
    else
      warn "Không thể clone remote template — harness files có thể thiếu"
      rm -rf "$TMP_SYNC" 2>/dev/null || true; unset TMP_SYNC
    fi
  fi
fi
log "L0 policy + validators + wiki-health + evals: OK"

# ---------- 4. L1 adapter Claude Code ----------
mkdir -p "$ROOT/llmwiki/.claude/hooks/validators"
if [ "$SAME_BUNDLE" = "0" ]; then
  cp "$SRC/llmwiki/.claude/hooks/"*.py "$ROOT/llmwiki/.claude/hooks/"
else
  # SAME_BUNDLE: hooks already pulled in TMP_SYNC from step 3; clone if step 3 skipped
  if [ "$NO_CLONE" != "1" ] && [ ! -d "${TMP_SYNC:-}" ]; then
    TMP_SYNC="$(mktemp -d /tmp/llmwiki-harness-sync.XXXXXX)"
    git clone --depth 1 -b "$HARNESS_REF" git@github.com:"$HARNESS_REPO".git "$TMP_SYNC" >/dev/null 2>&1 \
      || git clone --depth 1 -b "$HARNESS_REF" https://github.com/"$HARNESS_REPO".git "$TMP_SYNC" >/dev/null 2>&1 || true
  fi
  if [ -d "${TMP_SYNC:-}" ]; then
    cp "$TMP_SYNC/llmwiki/.claude/hooks/"*.py "$ROOT/llmwiki/.claude/hooks/" 2>/dev/null || true
  fi
fi
# copy validators vào cạnh hooks để llmwiki deploy standalone vẫn chạy (resolution tier 2)
cp "$ROOT/harness/validators/"*.py "$ROOT/llmwiki/.claude/hooks/validators/" 2>/dev/null || true
# harness-local/ — scaffold rule RIÊNG của dự án (chỉ tạo nếu CHƯA có; project-owned, sync-template KHÔNG đụng)
if [ ! -d "$ROOT/harness-local" ] && [ -d "$SRC/harness-local" ]; then
  mkdir -p "$ROOT/harness-local/validators"
  cp "$SRC/harness-local/run.py" "$SRC/harness-local/README.md" "$ROOT/harness-local/" 2>/dev/null || true
  cp "$SRC/harness-local/policy.yaml" "$ROOT/harness-local/policy.yaml" 2>/dev/null || true
  cp "$SRC/harness-local/validators/_template.py" "$ROOT/harness-local/validators/" 2>/dev/null || true
  printf '\033[1;32m[harness]\033[0m %s\n' "harness-local/ — scaffold rule riêng dự án (P-namespace; sync-template không đụng)"
fi
# foundation.yaml — nguồn mục "Nền tảng" (GH#6): SEED từ template CHỈ khi chưa có, KHÔNG đè bản dự án đã điền
[ -f "$ROOT/harness/foundation.yaml" ] || cp "$SRC/harness/templates/foundation-template.yaml" "$ROOT/harness/foundation.yaml" 2>/dev/null \
  || cp "${TMP_SYNC:-/nonexistent}/harness/templates/foundation-template.yaml" "$ROOT/harness/foundation.yaml" 2>/dev/null || true

# overstack docs user — TRAVEL cùng install (Phase D): trang tài liệu chính thức về cho dự án
mkdir -p "$ROOT/llmwiki/html"
cp "$SRC/llmwiki/html/overstack.html" "$ROOT/llmwiki/html/overstack.html" 2>/dev/null \
  || cp "${TMP_SYNC:-/nonexistent}/llmwiki/html/overstack.html" "$ROOT/llmwiki/html/overstack.html" 2>/dev/null || true
printf '# runtime data — khong commit\naudit/\n' > "$ROOT/llmwiki/.claude/.gitignore"

SETTINGS="$ROOT/llmwiki/.claude/settings.json"
if [ -f "$SETTINGS" ]; then
  cp "$SETTINGS" "$SETTINGS.bak.$(date +%s)"
  python3 - "$SETTINGS" "$SRC/llmwiki/.claude/settings.json" <<'PY'
import json, sys
cur = json.load(open(sys.argv[1])); tpl = json.load(open(sys.argv[2]))
# merge: deny rules (union), hooks (thêm event còn thiếu — không đè hook user tự thêm)
cur.setdefault("permissions", {}).setdefault("deny", [])
for d in tpl.get("permissions", {}).get("deny", []):
    if d not in cur["permissions"]["deny"]:
        cur["permissions"]["deny"].append(d)
cur.setdefault("hooks", {})
for event, defs in tpl.get("hooks", {}).items():
    cur_defs = cur["hooks"].setdefault(event, [])
    # so sánh trên command THÔ — json.dumps escape quote nên substring-check sẽ luôn miss
    existing_cmds = {h.get("command") for d in cur_defs for h in (d.get("hooks") or [])}
    for d in defs:  # append hook harness nếu event đã có hook user — không đè
        cmd = (d.get("hooks") or [{}])[0].get("command", "")
        if cmd and cmd not in existing_cmds:
            cur_defs.append(d)
json.dump(cur, open(sys.argv[1], "w"), indent=2, ensure_ascii=False)
PY
  log "settings.json: MERGE (backup .bak.*)"
else
  cp "$SRC/llmwiki/.claude/settings.json" "$SETTINGS"
  log "settings.json: cài mới"
fi

# ---------- 4b. Settings ở ROOT — session mở tại root mới load hooks ----------
# (llmwiki/.claude/settings.json chỉ tác dụng khi session mở ngay tại llmwiki/)
ROOT_SETTINGS="$ROOT/.claude/settings.json"
mkdir -p "$ROOT/.claude"
[ -f "$ROOT_SETTINGS" ] && cp "$ROOT_SETTINGS" "$ROOT_SETTINGS.bak.$(date +%s)"
python3 - "$ROOT_SETTINGS" <<'PY'
import json, os, sys
path = sys.argv[1]
prefix = "llmwiki/"
hooks_dir = '$CLAUDE_PROJECT_DIR/llmwiki/.claude/hooks'
deny = [f"Write(./{prefix}raw/**)", f"Edit(./{prefix}raw/**)", f"MultiEdit(./{prefix}raw/**)"]
def h(script, matcher=None):
    d = {"hooks": [{"type": "command", "command": f'python3 "{hooks_dir}/{script}"'}]}
    if matcher: d["matcher"] = matcher
    return d
tpl = {"permissions": {"deny": deny}, "env": {"OVERSTACK_WIKIGRAPH": "1"}, "hooks": {
    "PreToolUse":  [h("pre_tool_use.py",  "Write|Edit|MultiEdit|NotebookEdit|Bash"), h("orca_guard.py", "Bash")],
    "PostToolUse": [h("post_tool_use.py", "Write|Edit|MultiEdit")],
    "Stop":        [h("stop.py")],
    "SessionEnd":  [h("session_end.py")],
    "SessionStart":[h("session_start.py"), h("code_graph_keeper.py")],
    "UserPromptSubmit":[h("user_prompt_submit.py")],
}}
cur = {}
if os.path.exists(path):
    try: cur = json.load(open(path))
    except Exception: cur = {}
cur.setdefault("permissions", {}).setdefault("deny", [])
for d in tpl["permissions"]["deny"]:
    if d not in cur["permissions"]["deny"]:
        cur["permissions"]["deny"].append(d)
# env: bật auto-draw wiki-graph.html downstream (opt-in Taleb) — setdefault không đè giá trị user đã đặt
cur.setdefault("env", {}).setdefault("OVERSTACK_WIKIGRAPH", "1")
cur.setdefault("hooks", {})
for event, defs in tpl["hooks"].items():
    cur_defs = cur["hooks"].setdefault(event, [])
    existing_cmds = {h.get("command") for d in cur_defs for h in (d.get("hooks") or [])}
    for d in defs:
        cmd = d["hooks"][0]["command"]
        if cmd not in existing_cmds:
            cur_defs.append(d)
json.dump(cur, open(path, "w"), indent=2, ensure_ascii=False)
PY
grep -q "audit/" "$ROOT/.claude/.gitignore" 2>/dev/null || printf 'audit/\nsettings.json.bak.*\n' >> "$ROOT/.claude/.gitignore"
log "settings.json ở ROOT: OK (session mở tại root sẽ load hooks)"

# ---------- 4c. Seed-once wiki-graph.html: artifact vector TỒN TẠI ngay, khỏi chờ Stop có diff ----------
# Diệt pain "cài xong không thấy vector": Stop hook chỉ regen khi git-status có diff ở wiki/ hay code →
# project vừa cài ngồi im thì vector KHÔNG bao giờ xuất hiện. Seed 1 lần NẾU wiki đã có nội dung; project
# code-only (wiki rỗng) → bỏ qua, để orca-onboard đẻ wiki rồi tự vẽ (STEP C của skill). Fail-open: seed lỗi
# KHÔNG chặn install (tách `|| true` khỏi set -e). Engine: repo-local → global (cùng thứ tự hook resolve).
WG_SEED=""
[ -f "$ROOT/fdk/tools/build-wiki-graph.py" ] && WG_SEED="$ROOT/fdk/tools/build-wiki-graph.py"
[ -z "$WG_SEED" ] && [ -f "$HOME/.claude/harness/fdk/tools/build-wiki-graph.py" ] && WG_SEED="$HOME/.claude/harness/fdk/tools/build-wiki-graph.py"
if [ -n "$WG_SEED" ] && [ -d "$ROOT/llmwiki/wiki" ] \
   && [ -n "$(find "$ROOT/llmwiki/wiki" -name '*.md' ! -name index.md ! -name log.md -print -quit 2>/dev/null)" ]; then
  ALSO_SEED=""; [ -d "$ROOT/fdk/wiki" ] && ALSO_SEED="--also fdk/wiki"
  if ( cd "$ROOT" && python3 "$WG_SEED" llmwiki/wiki $ALSO_SEED --code-root . >/dev/null 2>&1 ); then
    log "wiki-graph.html: seed-once OK (vector vẽ ngay, khỏi chờ Stop có diff)"
  else
    warn "wiki-graph.html: seed-once lỗi — bỏ qua (không chặn install; Stop sẽ vẽ khi wiki/code đổi)"
  fi
else
  log "wiki-graph.html: bỏ seed-once (wiki chưa có nội dung — orca-onboard sẽ đẻ wiki rồi tự vẽ)"
fi

# ---------- 5. L2 pre-commit ----------
if [ ! -f "$ROOT/.pre-commit-config.yaml" ]; then
  cp "$SRC/.pre-commit-config.yaml" "$ROOT/.pre-commit-config.yaml"
  log "L2 .pre-commit-config.yaml: cài mới (kiểm tra prefix path nếu wiki không nằm ở llmwiki/wiki)"
else
  warn "L2 .pre-commit-config.yaml đã tồn tại — không đè; merge tay nếu cần (mẫu: $SRC/.pre-commit-config.yaml)"
fi
# [ -e ] chứ không phải [ -d ]: trong git worktree, .git là FILE trỏ về gitdir chính
if command -v pre-commit >/dev/null 2>&1 && [ -e "$ROOT/.git" ]; then
  # idempotent: hook đã trỏ pre-commit rồi thì khỏi install lại (re-run nhanh hơn)
  HOOK="$ROOT/.git/hooks/pre-commit"
  if [ -f "$HOOK" ] && grep -q "pre-commit" "$HOOK" 2>/dev/null; then
    log "pre-commit: đã cài (skip)"
  else
    (cd "$ROOT" && pre-commit install >/dev/null) && log "pre-commit install: OK"
  fi
  # R12 gate2: pull-before-push — version-controlled qua .pre-commit-config (stage pre-push)
  (cd "$ROOT" && pre-commit install --hook-type pre-push >/dev/null 2>&1) && log "pre-commit pre-push (R12 gate2): OK"
  # R15 no-ai-attribution: commit message không ghi công AI (stage commit-msg)
  (cd "$ROOT" && pre-commit install --hook-type commit-msg >/dev/null 2>&1) && log "pre-commit commit-msg (R15 no-ai-attribution): OK"
else
  warn "pre-commit chưa cài hoặc không phải git repo → chạy sau: pipx install pre-commit && pre-commit install"
fi

# ---------- 6. Baseline audit (quan trọng với migrate) ----------
WIKI="$ROOT/llmwiki/wiki"
mkdir -p "$ROOT/harness/metrics"
DEBT=0
log "Baseline audit..."
CONTENT_FILES=$(find "$WIKI"/concepts "$WIKI"/entities "$WIKI"/sources "$WIKI"/draft -name '*.md' \
  ! -name 'README.md' ! -name '_template.md' 2>/dev/null || true)
if [ -n "$CONTENT_FILES" ]; then
  # shellcheck disable=SC2086
  python3 "$ROOT/harness/validators/origin_required.py" $CONTENT_FILES || DEBT=1
fi
python3 "$ROOT/harness/validators/index_sync.py" --wiki-dir "$WIKI" || DEBT=1
python3 "$ROOT/harness/scripts/wiki-health.py" --wiki-dir "$WIKI" \
  --csv "$ROOT/harness/metrics/wiki-health.csv" > "$ROOT/harness/metrics/baseline-$(date +%F).json" || true
log "Báo cáo baseline: harness/metrics/baseline-$(date +%F).json"

# 6b. Pattern-sync health: sinh version.json nếu thiếu, rồi báo cáo (không chặn)
if [ -f "$ROOT/.template-manifest.json" ] && [ -f "$ROOT/harness/scripts/health-check.py" ]; then
  [ -f "$ROOT/harness/version.json" ] \
    || python3 "$ROOT/harness/scripts/health-check.py" --root "$ROOT" --update >/dev/null 2>&1 || true
  python3 "$ROOT/harness/scripts/health-check.py" --root "$ROOT" --branch orca || true
fi

# ---------- 6c. Self-heal (chỉ khi --self-heal) — installer tự trả nợ trong 1 process ----------
# Trigger dựa trên audit.py (gồm cả OKF), KHÔNG chỉ DEBT của mục 6 (origin+index).
# Nhờ vậy nợ OKF-only cũng được bắt. Backfill là THÊM, không sửa/xóa nội dung cũ.
if [ "$SELF_HEAL" = "1" ] && [ -f "$ROOT/harness/scripts/audit.py" ]; then
  if ! python3 "$ROOT/harness/scripts/audit.py" --wiki-dir "$WIKI" --root "$ROOT" >/dev/null 2>&1; then
    log "Self-heal: phát hiện nợ (Origin/index/OKF) → tự backfill trong 1 process..."
    python3 "$ROOT/harness/scripts/audit.py" --wiki-dir "$WIKI" --root "$ROOT" --fix || true
  fi
  if python3 "$ROOT/harness/scripts/audit.py" --wiki-dir "$WIKI" --root "$ROOT" >/dev/null 2>&1; then
    DEBT=0; log "Self-heal: wiki sạch (Origin + index + OKF) sau backfill."
  else
    DEBT=1; warn "Self-heal: còn nợ KHÔNG tự sửa được (cần user quyết):"
    python3 "$ROOT/harness/scripts/audit.py" --wiki-dir "$WIKI" --root "$ROOT" || true
  fi
fi

# ---------- 7. Kết luận ----------
{
  printf '\n## %s — install-harness — mode=%s\n' "$(date +%F)" "$MODE"
  printf -- '- Cài harness L0–L4 (validators, hooks, pre-commit, wiki-health, health-check, evals)\n'
  [ "$DEBT" = "1" ] && printf -- '- ⚠ CÓ NỢ wiki (thiếu Origin / index lệch) — backfill trước khi tin Stop hook\n'
} >> "$WIKI/log.md" 2>/dev/null || true

echo
if [ "$DEBT" = "1" ]; then
  warn "MIGRATE CÓ NỢ: sửa các vi phạm in phía trên TRƯỚC, rồi chạy lại script để xác nhận sạch."
  warn "Hooks đã cài nhưng phiên đụng wiki sẽ bị Stop hook nhắc cho tới khi index/Origin sạch."
  exit 3
fi
log "HOÀN TẤT — harness sạch. Tự kiểm hàng rào:"

# ---------- 8. Auto-smoke: 3 rule phải CHẶN được (exit 2 = PASS) ----------
V="$ROOT/harness/validators"
smoke() { # smoke <label> <validator> <json> — exit 2 là KỲ VỌNG, không để errexit giết
  local out rc=0
  out=$(printf '%s' "$3" | python3 "$V/$2" 2>&1) || rc=$?
  if [ "$rc" = "2" ]; then printf '  ⛔ %-38s → BỊ CHẶN ✓\n' "$1"
  else printf '  ✗ %-38s → KHÔNG CHẶN (rc=%s) — KIỂM TRA LẠI!\n' "$1" "$rc"; SMOKE_FAIL=1; fi
}
SMOKE_FAIL=0
echo "── Harness tự kiểm ─────────────────────────────────────"
smoke "Thử ghi llmwiki/raw/x.md (R1)"        no_write_raw.py     '{"action":"write","file_path":"llmwiki/raw/x.md"}'
smoke "Thử wiki file thiếu ## Origin (R2)"   origin_required.py  '{"action":"write","file_path":"llmwiki/wiki/concepts/x.md","content":"# x"}'
smoke "Thử file lạc wiki/ root (R5)"         folder_structure.py '{"action":"write","file_path":"llmwiki/wiki/rogue.md"}'
echo "────────────────────────────────────────────────────────"
if [ "$SMOKE_FAIL" = "0" ]; then
  log "Hệ thống đang cắn. Xem nó cắn trong PHIÊN THẬT: gọi skill /harness-tour (3 phút)"
  log "Hoặc xem máy diễn đủ 5 cảnh: bash harness/scripts/tour.sh"
else
  warn "Có rule không chặn được — kiểm tra python3 + harness/validators/"
  exit 4
fi
