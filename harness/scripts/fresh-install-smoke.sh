#!/usr/bin/env bash
# fresh-install-smoke.sh — chứng minh một NGƯỜI MỚI curl-cài overstack vào dự án
# TRỐNG là có ngay 3 trụ + orchestration-ready. Chạy trong thư mục CÔ LẬP (mktemp,
# ngoài repo dev) rồi tự dọn. Đây là cổng required của push-qua-/fdk (medic probe).
#
#   fresh-install-smoke.sh            # --local: cài từ working-tree qua file:// (OFFLINE,
#                                     #   tất định) — bản dùng làm CỔNG pre-push.
#   fresh-install-smoke.sh --remote   # cài THẬT bằng curl github raw (đúng đường người mới,
#                                     #   gồm npx skills). Bản ACCEPTANCE, chạy tay/hậu-push.
#   fresh-install-smoke.sh --keep     # không xoá thư mục cô lập (để soi).
#   fresh-install-smoke.sh --self-test  # tự kiểm cấu trúc script (không cài gì).
#
# CEILING (ponytail): cổng headless KHÔNG spin được model LLM + Orca runtime, nên
# "/orchestration chạy được" được kiểm ở mức TẤT ĐỊNH: (a) skills orchestration cài
# đủ + reachable, (b) harness cắn thật trên dự án mới, (c) PING runtime nếu máy đang
# bật Orca — vắng thì SKIP có in ra (không nuốt lặng). Live-run LLM là acceptance tay.
set -uo pipefail

# repo root = 2 cấp trên script (harness/scripts/ -> repo)
SELF="${BASH_SOURCE[0]:-$0}"
ROOT="$(CDPATH= cd -- "$(dirname -- "$SELF")/../.." && pwd)"
MODE="local"; KEEP=0
for a in "$@"; do case "$a" in
  --remote) MODE="remote";;
  --local)  MODE="local";;
  --keep)   KEEP=1;;
  --self-test) MODE="selftest";;
  *) echo "cờ lạ: $a" >&2; exit 64;;
esac; done

G=$'\033[1;32m'; R=$'\033[1;31m'; Y=$'\033[1;33m'; B=$'\033[1;36m'; X=$'\033[0m'
ok(){   printf '  %s✓%s %s\n' "$G" "$X" "$*"; }
bad(){  printf '  %s✗%s %s\n' "$R" "$X" "$*"; FAILED=1; }
skip(){ printf '  %s·%s %s\n' "$B" "$X" "$*"; }
FAILED=0

# ── --self-test: cấu trúc, không cài ──────────────────────────────────────────
if [ "$MODE" = "selftest" ]; then
  echo "${B}fresh-install-smoke --self-test${X}"
  [ -f "$ROOT/harness/poc-vendor-neutral/bootstrap.sh" ] && ok "bootstrap.sh có mặt" || bad "thiếu bootstrap.sh"
  bash -n "$SELF" && ok "script tự-parse sạch" || bad "script lỗi cú pháp"
  # isolation-guard là hàm thuần: thư mục trong repo phải bị chặn
  case "$ROOT/x" in "$ROOT"*) ok "isolation-guard: nhận diện path trong repo";; *) bad "guard sai";; esac
  [ "$FAILED" = 0 ] && { echo "${G}▉ self-test OK${X}"; exit 0; } || { echo "${R}▉ self-test FAIL${X}"; exit 1; }
fi

# ── thư mục CÔ LẬP ngoài repo dev ─────────────────────────────────────────────
TARGET="$(mktemp -d "${TMPDIR:-/tmp}/overstack-fresh.XXXXXX")"
case "$TARGET" in
  "$ROOT"*) echo "${R}FATAL: mktemp rơi TRONG repo dev ($TARGET) — hỏng cô lập${X}" >&2; exit 3;;
esac
cleanup(){ [ "$KEEP" = 1 ] && echo "giữ: $TARGET" || rm -rf "$TARGET"; }
trap cleanup EXIT
echo "${B}fresh-install-smoke${X} — mode=$MODE  ·  cô lập tại $TARGET"

# ── cài như người mới ─────────────────────────────────────────────────────────
( cd "$TARGET" && git init -q )  # bootstrap cần 1 git repo để cắm pre-commit
if [ "$MODE" = "remote" ]; then
  echo "→ curl github raw (đường người-mới thật, gồm npx skills)"
  ( cd "$TARGET" && curl -fsSL "https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh" | bash ) >/dev/null 2>&1
else
  echo "→ file:// từ working-tree (offline, tất định) — harness + llmwiki, bỏ npx skills"
  ( cd "$TARGET" && HARNESS_BASE="file://$ROOT/harness/poc-vendor-neutral" \
      bash "$ROOT/harness/poc-vendor-neutral/bootstrap.sh" --with-wiki ) >/dev/null 2>&1
fi
[ $? -eq 0 ] && ok "install exit 0" || bad "install exit≠0"

# ── PARITY HỨA↔GIAO (GH#77) — CHẠY Ở MỌI MODE, KỂ CẢ --local ────────────────────────────
# overstack.html + CAPABILITIES.md đều đọc từ ĐĨA nên luôn đồng thuận với nhau — và cùng SAI so
# với thứ npx thật sự giao. Đo 2026-07-11: doc hứa 74 skill, installer giao 67; 7 skill bị CLI
# nuốt im lặng (frontmatter YAML hỏng). User đọc doc thấy /web-crawl, gõ vào thì không có gì.
# capsurface gác NGUYÊN NHÂN (YAML hỏng); đây gác HỆ QUẢ — bất kể nguyên nhân gì.
#
# PHẢI ở ngoài nhánh remote: cổng required (medic → probe freshinstall) chạy --local. Nhét parity
# vào riêng --remote = guard phải-nhớ-gọi-tay = guard không tồn tại (đúng bệnh mà cả cổng này sinh
# ra để chống). Kiểm này KHÔNG cần mạng — chỉ so skill trên đĩa với skill đã tới global.
echo "${Y}parity hứa↔giao:${X}"
SK_DIR="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
if [ -d "$SK_DIR" ]; then
  dropped=""
  for sk in "$ROOT"/skills/*/SKILL.md; do
    n="$(basename "$(dirname "$sk")")"
    [ "$n" = "fdk" ] && continue                      # cố ý không ship xuống user (ADR-004)
    [ -d "$SK_DIR/$n" ] || dropped="$dropped $n"
  done
  if [ -z "$dropped" ]; then
    ok "mọi skill trên đĩa đều tới được người dùng (hứa == giao)"
  else
    bad "SKILL RỚT — doc hứa nhưng user KHÔNG nhận được:$dropped"
    bad "  → soi nguyên nhân: python3 harness/scripts/capability-stamp.py --check"
    bad "  → giao lại:        npx skills add . --global --all"
  fi
else
  skip "chưa cài skill global ($SK_DIR) — bỏ qua parity (fail-open, không chặn máy mới)"
fi

# ── (C) 3 trụ có mặt trên dự án mới ──────────────────────────────────────────
echo "${Y}3 trụ:${X}"
[ -f "$TARGET/.harness/poc-vendor-neutral/policy.yaml" ] && ok "harness (policy.yaml)"       || bad "thiếu harness/policy.yaml"
[ -f "$TARGET/.claude/settings.json" ]                  && ok "wiring (.claude/settings.json)" || bad "thiếu .claude wiring"
[ -f "$TARGET/.pre-commit-config.yaml" ]                && ok "pre-commit wired"             || bad "thiếu pre-commit"
[ -f "$TARGET/.llmwiki/wiki/index.md" ]                  && ok "llmwiki (wiki/index.md)"      || bad "thiếu llmwiki seed"

# ── (D) harness CẮN THẬT trên dự án mới (không chỉ file có mặt) ───────────────
echo "${Y}harness cắn:${X}"
if [ -f "$TARGET/.harness/poc-vendor-neutral/test-broad.sh" ]; then
  if ( cd "$TARGET" && bash .harness/poc-vendor-neutral/test-broad.sh ) >/dev/null 2>&1; then
    ok "test-broad.sh xanh (validator GOOD-pass/BAD-block)"
  else
    bad "test-broad.sh ĐỎ — guardrail không cắn đúng trên fresh install"
  fi
else
  bad "thiếu test-broad.sh"
fi

# ── (E) HỢP ĐỒNG DOWNSTREAM — tính năng dev ở fdk có THẬT SỰ tới downstream không ────────
# Nguồn chân lý: harness/downstream-contract.yaml. "Xanh trong repo" ≠ "đúng ở downstream":
# installer hardcode file-list, nên một tính năng mới có thể không bao giờ được ship.
CONTRACT="$ROOT/harness/downstream-contract.yaml"
# đọc các mục dạng "  - <giá trị>" nằm dưới một khoá cho trước (bash thuần, không cần pyyaml)
contract_list(){ sed -n "/^$1:/,/^[a-z_]*:/p" "$CONTRACT" 2>/dev/null | sed -n 's/^[[:space:]]*-[[:space:]]*//p'; }
if [ -f "$CONTRACT" ]; then
  echo "${Y}hợp đồng downstream:${X}"
  for f in $(contract_list must_exist); do
    [ -e "$TARGET/$f" ] && ok "must_exist: $f" || bad "must_exist THIẾU downstream: $f  (installer chưa ship → sửa install.sh/bootstrap.sh)"
  done
  while IFS= read -r cmd; do
    [ -z "$cmd" ] && continue
    if ( cd "$TARGET" && eval "$cmd" ) >/dev/null 2>&1; then ok "must_bite: $cmd"
    else bad "must_bite ĐỎ downstream: $cmd"; fi
  done <<< "$(contract_list must_bite)"
  # ENGINE GLOBAL: tool của skill sống ở global harness home (KHÔNG per-project — U10 xoá bản
  # per-project có chủ đích). install.sh cài global ở chế độ FAIL-OPEN → bước đó hỏng thì project
  # "cài thành công" nhưng rỗng ruột engine. Đây là chỗ gate phải gác.
  GH_HOME="${OVERSTACK_HARNESS_HOME:-$HOME/.claude/harness}"
  for e in $(contract_list must_reach_global_engines); do
    [ -e "$GH_HOME/$e" ] && ok "engine global: $e" \
      || bad "engine global THIẾU: $e  (global harness rỗng → skill gãy; sửa: bash harness/scripts/install-harness.sh --global)"
  done

  # rule parity: mọi R\d+ của policy REPO phải có trong policy DOWNSTREAM
  if grep -q '^rule_parity:[[:space:]]*true' "$CONTRACT"; then
    RP="$ROOT/harness/poc-vendor-neutral/policy.yaml"; DP="$TARGET/harness/poc-vendor-neutral/policy.yaml"
    if [ -f "$RP" ] && [ -f "$DP" ]; then
      missing=""
      for r in $(grep -oE 'id:[[:space:]]*R[0-9]+' "$RP" | grep -oE 'R[0-9]+' | sort -u); do
        grep -qE "id:[[:space:]]*$r\b" "$DP" || missing="$missing $r"
      done
      [ -z "$missing" ] && ok "rule_parity: mọi rule repo đều tới downstream" \
        || bad "rule_parity ĐỨT — rule có ở fdk nhưng KHÔNG tới downstream:$missing"
    fi
  fi
else
  skip "chưa có downstream-contract.yaml — bỏ qua kiểm hợp đồng"
fi

# ── (F) orchestration-ready: skill reachable ─────────────────────────────────
echo "${Y}orchestration-ready:${X}"
SK="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
for s in $(contract_list must_reach_skills 2>/dev/null || echo "orca-dispatch-reference"); do
  if [ -e "$SK/$s" ] || [ -e "$SK/$s/SKILL.md" ]; then ok "skill '$s' reachable"
  else bad "skill '$s' THIẾU global ($SK) — cài: npx skills add rheinmir/setup#orca --global --all"; fi
done

# ── (F) runtime ping — env-dependent, SKIP-không-fail (ceiling) ──────────────
if command -v orca >/dev/null 2>&1 || command -v orca-ide >/dev/null 2>&1; then
  OC="$(command -v orca || command -v orca-ide)"
  if "$OC" status --json 2>/dev/null | grep -q '"ok"[[:space:]]*:[[:space:]]*true'; then
    ok "orca runtime UP — /orchestration live-able (ceiling: LLM run vẫn là acceptance tay)"
  else
    skip "orca CLI có nhưng runtime chưa bật — /orchestration cần bật runtime (không fail cổng)"
  fi
else
  skip "orca CLI vắng (headless/CI) — bỏ qua ping runtime, KHÔNG fail (ceiling)"
fi

echo
if [ "$FAILED" = 0 ]; then echo "${G}▉ FRESH-INSTALL PASS${X} — người mới curl-cài là có 3 trụ + orchestration-ready"; exit 0
else echo "${R}▉ FRESH-INSTALL FAIL${X} — đường cài người-mới hỏng, đừng push"; exit 2; fi
