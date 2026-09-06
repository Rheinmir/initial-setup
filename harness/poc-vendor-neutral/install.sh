#!/usr/bin/env bash
# install.sh — cài PoC vendor-neutral harness vào 1 dự án bằng MỘT lệnh (luồng B0–B4).
#
# Usage:
#   bash install.sh [project_root] [--vendor claude,opencode,cursor,codex,kiro] [--no-verify]
#
#   project_root  thư mục dự án đích (mặc định: thư mục hiện tại)
#   --vendor      ép danh sách vendor; bỏ qua → tự DÒ (.claude/ · opencode.json · .cursor/ · .kiro/ · .codex)
#   --no-verify   bỏ bước chạy demo.sh + test-broad.sh
#
# Idempotent. CI + pre-commit luôn cài (sàn đảm bảo); adapter chỉ cài cho vendor có mặt.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # nguồn = poc-vendor-neutral/
ROOT="."; VENDORS=""; VERIFY=1; CLEAN=0; WITH_SKILLS=0; WITH_WIKI=0
# GH_HOME phải định nghĩa ở TOP LEVEL: trước đây nó chỉ được gán trong nhánh
# `if [ "$WITH_WIKI" = 1 ]`, nhưng dòng BC="$GH_HOME/hooks/build-capabilities.py" ở dưới lại
# nằm NGOÀI nhánh đó — nên cài KHÔNG kèm --with-wiki là `set -u` giết script ngay
# ("GH_HOME: unbound variable"). Đo 2026-08-06 khi cài vào CoopCons: crash sau bước B4.
GH_HOME="${OVERSTACK_HARNESS_HOME:-$HOME/.claude/harness}"
while [ $# -gt 0 ]; do
  case "$1" in
    --vendor) VENDORS="${2:-}"; shift 2;;
    --no-verify) VERIFY=0; shift;;
    --clean) CLEAN=1; shift;;
    --with-skills) WITH_SKILLS=1; shift;;
    --with-wiki) WITH_WIKI=1; shift;;
    --full) WITH_SKILLS=1; WITH_WIKI=1; shift;;   # đủ 3 trụ: harness + skills + llmwiki
    -*) echo "tham số lạ: $1" >&2; exit 1;;
    *) ROOT="$1"; shift;;
  esac
done
ROOT="$(cd "$ROOT" && pwd)"
log(){ printf '\033[1;32m[install]\033[0m %s\n' "$*"; }
warn(){ printf '\033[1;33m[install]\033[0m %s\n' "$*"; }
has(){ case ",$VENDORS," in *",$1,"*) return 0;; *) return 1;; esac; }

# ─── Chuẩn thư mục: ẩn sau dấu chấm (đề xuất 040926-downstream-dot-layout) ───
# Framework nằm TRẦN ở gốc dự án đích khiến cổng thiết kế của dự án (hallmark,
# impeccable, linter bên thứ ba) quét **/*.html là vớ phải llmwiki/html/overstack.html
# 530KB rồi chấm nó như UI sản phẩm. Mọi thứ khác installer đặt (.claude .cursor .kiro)
# vốn đã ẩn; hai thư mục này bị bỏ sót.
#
# Migrate TỰ ĐỘNG, idempotent: đúng chuẩn rồi thì im lặng bỏ qua; còn rơi rớt ở ngoài
# thì dọn vào. Repo framework (nhận diện bằng fdk/wiki) KHÔNG BAO GIỜ tự migrate.
migrate_dot_layout(){
  [ -d "$ROOT/fdk/wiki" ] && { log "  · repo framework (có fdk/wiki) → KHÔNG migrate layout"; return 0; }
  local moved=0 old new
  for pair in "llmwiki:.llmwiki" "harness:.harness"; do
    old="${pair%%:*}"; new="${pair##*:}"
    [ -d "$ROOT/$old" ] || continue                 # không có bản cũ → bỏ qua
    if [ -d "$ROOT/$new" ]; then
      warn "  có CẢ HAI $old/ và $new/ — không tự gộp, dọn tay rồi chạy lại"
      continue
    fi
    if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1 \
       && [ -n "$(git -C "$ROOT" ls-files -- "$old" 2>/dev/null | head -1)" ]; then
      git -C "$ROOT" mv "$old" "$new" 2>/dev/null || mv "$ROOT/$old" "$ROOT/$new"
    else
      mv "$ROOT/$old" "$ROOT/$new"
    fi
    log "  ✓ migrate $old/ → $new/"
    moved=1
  done
  [ "$moved" = 1 ] || { log "  · layout đã đúng chuẩn (.llmwiki/.harness) → bỏ qua"; return 0; }
  # Viết lại con trỏ. Chỉ đụng ĐÚNG chuỗi đường dẫn, không format lại file.
  for f in .claude/settings.json .claude/settings.local.json .pre-commit-config.yaml \
           .cursor/hooks.json .codex/hooks.json .gitignore; do
    [ -f "$ROOT/$f" ] || continue
    if python3 - "$ROOT/$f" <<'PYEOF'
import re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
# Chỉ thay khi 'llmwiki/' hoặc 'harness/' đứng ở đầu path hoặc sau / hoặc sau " ' = : (
n = re.sub(r'(?<![\w.-])(llmwiki|harness)/', lambda m: "." + m.group(1) + "/", s)
if n != s:
    open(p, "w", encoding="utf-8").write(n)
    sys.exit(0)
sys.exit(1)
PYEOF
    then log "    · cập nhật con trỏ trong $f"; fi
  done
  for g in "$ROOT"/.grok/hooks/*.json; do
    [ -f "$g" ] && python3 -c "
import re,sys;p=sys.argv[1];s=open(p,encoding='utf-8').read()
n=re.sub(r'(?<![\w.-])(llmwiki|harness)/', lambda m: '.'+m.group(1)+'/', s)
s!=n and open(p,'w',encoding='utf-8').write(n)" "$g" 2>/dev/null
  done
  # GH#106 gốc thật: vòng .grok ở trên là lệnh CUỐI của hàm — không có .grok/ thì `[ -f ]` trả 1,
  # hàm trả 1, `set -e` giết script NGAY SAU khi migrate (trước B0). Mọi dự án được migrate đều
  # bị bỏ dở: con trỏ đã đổi sang .harness/ mà .harness/ chưa có gì → pre-commit đỏ mọi commit.
  return 0
}
migrate_dot_layout

# Sau migrate mới chốt DEST: nó phải trỏ vào layout ĐANG dùng, không đoán.
OVERSTACK_DIR="llmwiki"; [ -d "$ROOT/.llmwiki" ] && OVERSTACK_DIR=".llmwiki"
HARNESS_DIR="harness";   [ -d "$ROOT/.harness" ] && HARNESS_DIR=".harness"
[ -d "$ROOT/fdk/wiki" ] || { OVERSTACK_DIR=".llmwiki"; HARNESS_DIR=".harness"; }
DEST="$ROOT/$HARNESS_DIR/poc-vendor-neutral"; OUT="$DEST/out"

# --clean: gỡ bản cũ trước khi cài (cài mới sạch). Cần uninstall.sh cạnh script.
if [ "$CLEAN" = 1 ] && [ -f "$SRC/uninstall.sh" ]; then
  log "--clean → gỡ bản cũ trước"
  bash "$SRC/uninstall.sh" "$ROOT" || warn "uninstall gặp lỗi, vẫn cài tiếp"
fi

# ── B0. Copy lõi vào dự án ──
log "B0 · copy lõi → $DEST"
mkdir -p "$DEST/bin"
if [ "$(cd "$SRC" && pwd -P)" != "$(cd "$DEST" && pwd -P)" ]; then
  cp "$SRC/policy.yaml" "$SRC/gen-converters.py" "$SRC/demo.sh" "$SRC/test-broad.sh" "$DEST/"
  cp "$SRC/bin/"*.py "$DEST/bin/"
  for f in install.sh uninstall.sh bootstrap.sh README.md DOCS.md; do [ -f "$SRC/$f" ] && cp "$SRC/$f" "$DEST/"; done
else
  log "  · lõi đã ở đúng chỗ (SRC=DEST), bỏ qua copy"
fi
printf 'out/\n' > "$DEST/.gitignore"
chmod +x "$DEST/bin/"*.py "$DEST/gen-converters.py" "$DEST"/*.sh 2>/dev/null || true
python3 -c 'import yaml' 2>/dev/null || { warn "thiếu pyyaml → thử pip install"; pip3 install --quiet pyyaml 2>/dev/null || warn "không cài được pyyaml — lõi sẽ fail-open tới khi có pyyaml"; }

# ── B1. Dò vendor ──
if [ -z "$VENDORS" ]; then
  det=""
  [ -d "$ROOT/.claude" ] && det="${det}claude,"
  { [ -f "$ROOT/opencode.json" ] || [ -d "$ROOT/.opencode" ]; } && det="${det}opencode,"
  [ -d "$ROOT/.openclaude" ] && det="${det}openclaude,"
  [ -d "$ROOT/.cursor" ] && det="${det}cursor,"
  { [ -f "$ROOT/AGENTS.md" ] || [ -d "$ROOT/.codex" ]; } && det="${det}codex,"
  [ -d "$ROOT/.kiro" ] && det="${det}kiro,"
  VENDORS="${det%,}"
  # harness chạy TRONG Claude Code → nếu không dò ra vendor nào, mặc định Claude
  # (tạo .claude/settings.json để wire PreToolUse hook, kể cả project chưa có .claude/)
  [ -z "$VENDORS" ] && VENDORS="claude"
fi
log "B1 · vendor: $VENDORS"

# ── B2. Sinh wiring từ policy ──
log "B2 · gen-converters → out/"
( cd "$DEST" && OVERSTACK_HARNESS_DIR="$HARNESS_DIR" python3 gen-converters.py >/dev/null )

# ── B3. Cắm wiring ──
log "B3 · cắm wiring"
# CI (sàn, luôn cài)
mkdir -p "$ROOT/.github/workflows"
cp "$OUT/ci/harness.yml" "$ROOT/.github/workflows/harness.yml"
log "  ✓ CI       → .github/workflows/harness.yml"
# pre-commit (sàn)
PC="$ROOT/.pre-commit-config.yaml"
if [ ! -f "$PC" ]; then
  # heredoc KHÔNG quote để $HARNESS_DIR nở ra — hardcode "harness/" ở đây làm pre-commit
  # đỏ với "can't open file" trên mọi commit chạm .md ở dự án layout dot (GH#111).
  cat > "$PC" <<YML
repos:
  - repo: local
    hooks:
      - id: llmwiki-harness
        name: llmwiki harness validator (layer=repo)
        entry: python3 $HARNESS_DIR/poc-vendor-neutral/bin/llmwiki-validate.py files
        language: system
        files: '\.md$'
YML
  log "  ✓ pre-commit → .pre-commit-config.yaml (tạo mới)"
elif grep -q 'llmwiki-harness' "$PC"; then
  log "  · pre-commit → đã có hook llmwiki-harness, bỏ qua"
else
  warn "  pre-commit đã tồn tại → thêm tay khối repo:local id=llmwiki-harness (xem out/pre-commit-snippet.yaml)"
fi
if [ ! -d "$ROOT/fdk/wiki" ]; then
  # GH#106 (downstream, mọi lần chạy): pre-commit của dự án có thể còn hook trỏ harness/scripts|validators
  # (bản GH#51 từng copy engine vào repo; migrate dot-layout lại đổi tiền tố thành .harness/). U10 gỡ
  # thư mục đó nên MỌI commit đỏ "can't open file" — kể cả commit không dính wiki.
  # Trỏ lại về bản global; thiếu file thì bỏ qua (exit 0), không khoá người dùng. Idempotent.
  PCF="$ROOT/.pre-commit-config.yaml"
  if [ -f "$PCF" ] && grep -qE 'python3 "?\.?harness/(scripts|validators)/' "$PCF"; then
    python3 - "$PCF" "$ROOT" <<'PYEOF'
import os, re, sys
pc, root = sys.argv[1], sys.argv[2]
s = open(pc, encoding="utf-8").read()
def sub(m):
    rel = m.group(2)                                   # harness/scripts/x.py
    if os.path.exists(os.path.join(root, m.group(1) + rel)):
        return m.group(0)                              # còn file → giữ nguyên
    return ('bash -c \'f="$HOME/.claude/harness/%s"; [ -f "$f" ] && exec python3 "$f" "$@" || exit 0\' --' % rel)
n = re.sub(r'python3 "?(\.?)(harness/(?:scripts|validators)/[^\s"]+)"?', sub, s)
if n != s:
    open(pc, "w", encoding="utf-8").write(n)
    print("  \033[1;32m✓\033[0m pre-commit: hook trỏ engine đã gỡ → dùng bản global, thiếu thì bỏ qua (GH#106)")
PYEOF
  fi
fi
# Claude / OpenClaude (merge hooks vào settings.json — cùng schema hook + cùng $CLAUDE_PROJECT_DIR,
# OpenClaude là fork của Claude Code; chỉ khác path project-settings: .openclaude/ thay vì .claude/)
merge_claude_hooks(){
  python3 - "$ROOT" "$OUT/claude/settings.snippet.json" "$1" <<'PY'
import json,os,sys,shutil
root,snip,subdir=sys.argv[1],sys.argv[2],sys.argv[3]
sp=os.path.join(root,subdir,'settings.json')
os.makedirs(os.path.dirname(sp),exist_ok=True)
cur=json.load(open(sp,encoding='utf-8')) if os.path.exists(sp) else {}
if os.path.exists(sp): shutil.copy(sp, sp+'.bak')
add=json.load(open(snip,encoding='utf-8'))
MARK='harness/poc-vendor-neutral/bin/'
cur.setdefault('hooks',{})
# 1) GỠ mọi hook harness cũ trước (idempotent kể cả khi đổi format lệnh → không trùng);
#    giữ nguyên hook KHÁC của user trong cùng event.
for ev,defs in list(cur['hooks'].items()):
    nd=[]
    for d in defs:
        d['hooks']=[h for h in (d.get('hooks') or []) if MARK not in (h.get('command') or '')]
        if d.get('hooks'): nd.append(d)
    if nd: cur['hooks'][ev]=nd
    else: cur['hooks'].pop(ev,None)
# 2) THÊM hook harness mới (đúng 1 bản, đã fail-open)
for ev,entries in add.get('hooks',{}).items():
    cur['hooks'].setdefault(ev,[]).extend(entries)
json.dump(cur,open(sp,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print(f'  \033[1;32m✓\033[0m {subdir:<9}→ {subdir}/settings.json (merged, backup .bak)')
PY
}
if has claude; then merge_claude_hooks .claude; fi
if has openclaude; then merge_claude_hooks .openclaude; fi
# opencode (permission.edit native — merge tự động)
if has opencode; then
  python3 - "$ROOT" "$OUT/opencode/opencode.json" <<'PY'
import json,os,sys,shutil
root,snip=sys.argv[1],sys.argv[2]
op=os.path.join(root,'opencode.json')
cur=json.load(open(op,encoding='utf-8')) if os.path.exists(op) else {}
if os.path.exists(op): shutil.copy(op,op+'.bak')
add=json.load(open(snip,encoding='utf-8'))
perm=cur.get('permission')
if not isinstance(perm,dict): perm={}
edit=perm.get('edit')
if not isinstance(edit,dict): edit={}
for k,v in add.get('permission',{}).get('edit',{}).items():
    if k=='*': edit.setdefault(k,v)     # giữ default của user nếu đã có
    else: edit[k]=v                      # luôn áp glob deny của harness
perm['edit']=edit; cur['permission']=perm
cur.setdefault('$schema', add.get('$schema','https://opencode.ai/config.json'))
json.dump(cur,open(op,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('  \033[1;32m✓\033[0m opencode → opencode.json (merged permission.edit, backup .bak)')
PY
fi
# advisory (nhắc — dựa CI là chính)
if has cursor; then mkdir -p "$ROOT/.cursor/rules"; cp "$OUT/cursor/.cursor/rules/harness.mdc" "$ROOT/.cursor/rules/"; log "  ✓ Cursor   → .cursor/rules/harness.mdc (advisory)"; fi
if has kiro;   then mkdir -p "$ROOT/.kiro/steering"; cp "$OUT/kiro/.kiro/steering/harness.md" "$ROOT/.kiro/steering/"; log "  ✓ Kiro     → .kiro/steering/harness.md (advisory)"; fi
if has codex;  then warn "  Codex → thêm nội dung out/codex/AGENTS.snippet.md vào AGENTS.md (advisory)"; fi

# ── B4. Verify ──
if [ "$VERIFY" = 1 ]; then
  log "B4 · verify"
  if bash "$DEST/demo.sh" >/dev/null 2>&1; then log "  ✓ demo.sh (13)"; else warn "  demo.sh FAIL — kiểm pyyaml"; fi
  if bash "$DEST/test-broad.sh" >/dev/null 2>&1; then log "  ✓ test-broad.sh (80)"; else warn "  test-broad.sh FAIL"; fi
fi

# ── (tùy chọn) trụ 3: seed khung llmwiki (nhanh, idempotent — không đè file có sẵn) ──
if [ "$WITH_WIKI" = 1 ]; then
  log "+ seed khung llmwiki"
  mkdir -p "$ROOT/$OVERSTACK_DIR/raw" "$ROOT/$OVERSTACK_DIR/wiki/concepts" "$ROOT/$OVERSTACK_DIR/wiki/entities" "$ROOT/$OVERSTACK_DIR/wiki/sources/adr" "$ROOT/$OVERSTACK_DIR/wiki/sources/draft"
  [ -f "$ROOT/$OVERSTACK_DIR/wiki/index.md" ] || printf '# Wiki index\n\n| File | Type | Date |\n|---|---|---|\n' > "$ROOT/$OVERSTACK_DIR/wiki/index.md"
  [ -f "$ROOT/$OVERSTACK_DIR/wiki/log.md" ]   || printf '# Log\n' > "$ROOT/$OVERSTACK_DIR/wiki/log.md"
  log "  ✓ $OVERSTACK_DIR/ (wiki/{concepts,entities,sources/draft} · raw/ · index.md · log.md)"
  # tài liệu hướng dẫn overstack — TRAVEL cùng khung xương (luôn refresh bản mới nhất)
  if command -v curl >/dev/null 2>&1; then
    REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/Rheinmir/setup/orca}"
    mkdir -p "$ROOT/$OVERSTACK_DIR/html"
    if curl -fsSL "$REPO_RAW/llmwiki/html/overstack.html" -o "$ROOT/$OVERSTACK_DIR/html/overstack.html" 2>/dev/null; then
      log "  ✓ $OVERSTACK_DIR/html/overstack.html (tài liệu overstack — mở bằng trình duyệt)"
    else
      warn "  overstack.html chưa tải được (mạng?) → lấy tay: $REPO_RAW/llmwiki/html/overstack.html"
    fi
    # foundation.yaml — nguồn mục "Nền tảng" (GH#6): seed CHỈ khi chưa có, không đè bản đã điền
    if [ ! -f "$ROOT/$HARNESS_DIR/foundation.yaml" ]; then
      mkdir -p "$ROOT/$HARNESS_DIR"
      if curl -fsSL "$REPO_RAW/harness/templates/foundation-template.yaml" -o "$ROOT/$HARNESS_DIR/foundation.yaml" 2>/dev/null; then
        log "  ✓ $HARNESS_DIR/foundation.yaml (nguồn mục Nền tảng — điền rồi regen overstack.html; medic probe foundation gác drift)"
      else
        warn "  foundation-template chưa tải được (mạng?) — điền tay: $REPO_RAW/harness/templates/foundation-template.yaml"
      fi
    fi
    # sổ cây vấn đề (problem-tree) — seed CHỈ khi chưa có, không bao giờ ghi đè sổ đang dùng
    if [ ! -f "$ROOT/$OVERSTACK_DIR/html/problem-tree.html" ] && [ ! -f "$ROOT/$OVERSTACK_DIR/html/fdk-problem-tree.html" ]; then
      if curl -fsSL "$REPO_RAW/harness/templates/problem-tree-template.html" -o "$ROOT/$OVERSTACK_DIR/html/problem-tree.html" 2>/dev/null; then
        log "  ✓ $OVERSTACK_DIR/html/problem-tree.html (sổ cây vấn đề — hook R17 tự xả sổ khi phiên kết thúc)"
      else
        warn "  problem-tree template chưa tải được (mạng?) — hook R17 sẽ fail-open tới khi có sổ"
      fi
    fi
    # v4 ĐẢO GH#51 (council-038, GH#63 Phase 2): engine KHÔNG travel vào repo nữa — GLOBAL-SHARED
    # ~/.claude/harness là source-of-truth (U10). Repo chỉ giữ llmwiki (data) + .harness-stamp.
    # Hooks fire từ GLOBAL ~/.claude/settings.json (install-harness --global wire, guard theo stamp).
    # 1) đảm bảo global harness có mặt VÀ KHÔNG CŨ.
    #    Trước đây chỉ cài khi VẮNG → re-curl bootstrap không bao giờ refresh global → global kẹt
    #    ở bản cũ mãi mãi. Hệ quả dây chuyền: stamp dự án == global (cùng bản cũ) → hook
    #    harness-integrity thấy bằng nhau → im lặng → DỰ ÁN KHÔNG BAO GIỜ BIẾT CÓ NĂNG LỰC MỚI,
    #    dù framework đã bump. Đây là mắt xích đứt duy nhất của chuỗi "model biết mình có gì mới".
    #    Nay: vắng HOẶC version remote khác version đang cài → cài lại (idempotent).
    GH_CUR=""; GH_NEW=""
    [ -f "$GH_HOME/version.json" ] && GH_CUR="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('template_version',''))" "$GH_HOME/version.json" 2>/dev/null || echo "")"
    if [ -f "$SRC/../version.json" ]; then
      GH_NEW="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('template_version',''))" "$SRC/../version.json" 2>/dev/null || echo "")"
    else
      VJ="$(mktemp)"
      curl -fsSL "$REPO_RAW/harness/version.json" -o "$VJ" 2>/dev/null \
        && GH_NEW="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('template_version',''))" "$VJ" 2>/dev/null || echo "")"
      rm -f "$VJ"
    fi
    if [ ! -f "$GH_HOME/version.json" ] || { [ -n "$GH_NEW" ] && [ "$GH_CUR" != "$GH_NEW" ]; }; then
      if [ -f "$GH_HOME/version.json" ]; then
        log "  global harness CŨ (v${GH_CUR:-?} → v$GH_NEW) → cập nhật install-harness.sh --global"
      else
        log "  global harness chưa có ($GH_HOME) → cài install-harness.sh --global"
      fi
      IH="$SRC/../scripts/install-harness.sh"
      if [ ! -f "$IH" ]; then
        IH="$(mktemp)"
        curl -fsSL "$REPO_RAW/harness/scripts/install-harness.sh" -o "$IH" 2>/dev/null || IH=""
      fi
      if [ -n "$IH" ] && [ -f "$IH" ]; then
        bash "$IH" --global || warn "  cài global lỗi — chạy tay: install-harness.sh --global (fail-open, không chặn install)"
      else
        warn "  không tải được install-harness.sh (mạng?) — cài tay: $REPO_RAW/harness/scripts/install-harness.sh --global"
      fi
    fi
    # 2) stamp — hợp đồng travel "repo này được gác bản vX" (session_start so với global → warn skew, U11)
    TV="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('template_version','0'))" "$GH_HOME/version.json" 2>/dev/null || echo 0)"
    printf '{"schema": 1, "guarded_by": "%s"}\n' "${TV:-0}" > "$ROOT/$OVERSTACK_DIR/.harness-stamp"
    log "  ✓ llmwiki/.harness-stamp (guarded_by: ${TV:-0})"
    # 3) U10: gỡ engine bản GH#51 từng copy vào repo (fdk/tools, harness/scripts) — global thay thế.
    #    KHÔNG đụng repo framework (nhận diện: có fdk/wiki — framework_only, downstream không có).
    if [ ! -d "$ROOT/fdk/wiki" ]; then
      for d in fdk/tools harness/scripts; do
        if [ -d "$ROOT/$d" ]; then rm -rf "$ROOT/${d:?}" && log "  ✓ gỡ $d khỏi repo (engine dùng bản global — U10)"; fi
      done
      rmdir "$ROOT/fdk" 2>/dev/null || true
    fi
  fi
fi

# ── (tùy chọn) cài skill llmwiki (GLOBAL — khác phạm vi với harness theo-project) ──
if [ "$WITH_SKILLS" = 1 ]; then
  # Ref cài skill. Mặc định GIỮ NGUYÊN `#orca` — đây là đường cài của mọi người dùng thật.
  # Mở override để test được một nhánh khác (canary UAT): không có nó thì cài-từ-nhánh-X vẫn
  # kéo skill của `orca` → bài UAT chấm bản CŨ rồi báo PASS cho bản MỚI. Cổng nói dối mà vẫn
  # xanh còn tệ hơn không có cổng. HARNESS_BASE / REPO_RAW đã override được; dòng này thì chưa.
  SKILLS_REF="${SKILLS_REF:-rheinmir/setup#orca}"
  log "+ cài bộ skill llmwiki (global, qua npx skills — ref: $SKILLS_REF)"
  if command -v npx >/dev/null; then
    npx -y skills add "$SKILLS_REF" --global --all 2>&1 | tail -4 | sed 's/^/    /' \
      || warn "  cài skill lỗi — chạy tay: npx skills add $SKILLS_REF --global --all"
  else
    warn "  không có npx — cài skill tay: npx skills add $SKILLS_REF --global --all"
  fi

  # OpenClaude quét THƯ MỤC SKILL RIÊNG: ~/.openclaude/skills. `npx skills add --global` chỉ
  # ghi vào ~/.claude/skills, nên máy có cả hai CLI thì openclaude thấy 0 skill — gõ
  # /orca-onboard không resolve, agent tự chế lại việc đã có sẵn. Đo 2026-08-06: 87 skill ở
  # ~/.claude/skills, thư mục ~/.openclaude/skills KHÔNG tồn tại; bundle openclaude grep ra
  # 10 hit ".openclaude/skills" và 0 hit ".claude/skills".
  # Symlink thay vì copy: MỘT nguồn chân lý, cài/gỡ skill một lần là cả hai CLI thấy ngay.
  if command -v openclaude >/dev/null 2>&1; then
    OC_SKILLS="$HOME/.openclaude/skills"
    if [ -L "$OC_SKILLS" ]; then
      log "  ✓ OpenClaude skills → đã trỏ sẵn ($(readlink "$OC_SKILLS"))"
    elif [ -e "$OC_SKILLS" ]; then
      warn "  OpenClaude đã có thư mục skill RIÊNG (không phải symlink) — giữ nguyên, không đè"
    elif [ -d "$HOME/.claude/skills" ]; then
      mkdir -p "$HOME/.openclaude"
      ln -s "$HOME/.claude/skills" "$OC_SKILLS" \
        && log "  ✓ OpenClaude skills → symlink ~/.claude/skills (cả hai CLI dùng chung)" \
        || warn "  không tạo được symlink ~/.openclaude/skills — openclaude sẽ thấy 0 skill"
    fi
  fi
fi

# ── BẢN ĐỒ NĂNG LỰC CHO MODEL (ADR-005) — mắt xích cuối, đừng bỏ ──────────────────────
# Hook orientation (session_start.py) nói với agent "dự án này có CAPABILITIES.md — bản đồ
# skill/tool đang có". Nhưng nếu KHÔNG AI SINH file đó, hook chẳng có gì để khoe và agent vào
# dự án KHÔNG BIẾT mình có đồ nghề gì → cài xong mà model vẫn mù. Sinh ngay tại đây, từ skill
# global + policy vừa cài. fail-open: bản harness cũ chưa có tool này thì bỏ qua, không chặn.
BC="$GH_HOME/hooks/build-capabilities.py"
if [ -f "$BC" ]; then
  if python3 "$BC" --root "$ROOT" >/dev/null 2>&1; then
    log "  ✓ CAPABILITIES.md (bản đồ đồ nghề — agent đọc để biết dự án này CÓ GÌ)"
  else
    warn "  không sinh được CAPABILITIES.md — chạy tay: python3 $BC --root ."
  fi
fi

echo ""
# ── Trần chi phí (spec §5): hỏi NGƯỜI DÙNG thay vì ship số đoán rồi bật chặn ──────────
# Mọi trần trong token-budget.config.yaml đều gắn `# ASSUMPTION (not verified)`. Bật chặn
# trên số đoán thì hoặc chặn nhầm việc thật, hoặc treo quá cao nên không bao giờ cắn — cả
# hai đều tệ hơn không có trần vì tạo cảm giác an toàn giả. Bước này gợi ý theo workload
# THẬT đo được trên máy, và chỉ bật `mode: block` khi người dùng tự chọn.
# `--if-tty`: không có terminal (CI, curl|bash trong script) thì im lặng giữ mặc định,
# TUYỆT ĐỐI không treo chờ nhập.
TB="$ROOT/$HARNESS_DIR/scripts/token-budget.py"
[ -f "$TB" ] || TB="$HOME/.claude/harness/harness/scripts/token-budget.py"
if [ -f "$TB" ]; then
  python3 "$TB" configure --if-tty --root "$ROOT" </dev/null 2>/dev/null || true
fi

log    "═══════════ TRẠNG THÁI 3 TRỤ ═══════════"
log    "  1. Harness  ✓ cài/cập nhật   (per-project: hook validate + CI + R1–R10)"
if [ "$WITH_SKILLS" = 1 ]; then
  log  "  2. Skills   ✓ cài/cập nhật   (GLOBAL ~/.claude/skills, qua npx)"
else
  warn "  2. Skills   — BỎ QUA         → thêm cờ --with-skills (hoặc --full)"
fi
if [ "$WITH_WIKI" = 1 ]; then
  log  "  3. llmwiki  ✓ seed khung     ($OVERSTACK_DIR/wiki + raw + index/log)"
else
  warn "  3. llmwiki  — BỎ QUA         → thêm cờ --with-wiki (hoặc --full)"
fi
if [ "$WITH_SKILLS" = 0 ] || [ "$WITH_WIKI" = 0 ]; then
  warn "  ► Muốn CẢ 3 trụ trong 1 lệnh: chạy lại với  --full"
fi
log    "═════════════════════════════════════════"
echo "   • Claude: mở session mới (hoặc /hooks reload) để hook có hiệu lực."
echo "   • CI chạy khi push lên GitHub. Sửa luật: harness/poc-vendor-neutral/policy.yaml → chạy lại install.sh (hoặc gen-converters.py)."
