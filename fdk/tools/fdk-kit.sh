#!/usr/bin/env bash
# fdk-kit.sh — mang BỘ FDK (đồ nghề phát triển overstack) về BẤT KỲ project nào, để bạn
# distill/sửa một skill rồi submit PR vào overstack remote — KHÔNG cần đang đứng trong repo overstack.
#
# Vì sao tồn tại: fdk-gate + fdk/tools KHÔNG travel xuống dự án downstream (cố ý — ADR-004).
# Nên khi đang dev dở một dự án khác mà muốn chưng cất một skill và adapt vào remote, gọi
# `/fdk` → nó dùng script này để:
#   (1) PULL   — clone overstack vào sandbox .overstack/kit/ (có fdk-gate, skills/, new-skill…)
#   (2) CHECK  — chạy fdk-gate trong kit (đủ 15 bước mới hợp lệ)
#   (3) SUBMIT — gate xanh → commit lên branch → push → TỰ mở PR vào nhánh base
#
# Usage:
#   bash fdk-kit.sh pull                      # clone/cập-nhật .overstack/kit/ (tự gitignore)
#   bash fdk-kit.sh check                     # fdk-gate trong kit (hoặc repo nếu đang ở overstack)
#   bash fdk-kit.sh submit <branch> "<msg>"   # gate → commit → push → gh pr create
#
# Lần đầu (kit chưa có) chạy thẳng từ remote, không cần file local:
#   bash <(curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/fdk/tools/fdk-kit.sh) pull
set -euo pipefail

REMOTE="${OVERSTACK_REMOTE:-https://github.com/Rheinmir/setup.git}"
BASE="${OVERSTACK_BASE:-orca}"
KIT="${FDK_KIT_DIR:-.overstack/kit}"

in_repo()  { [ -f "harness/scripts/fdk-gate.py" ] && [ -d "fdk/tools" ]; }   # đang đứng trong overstack?
kit_dir()  { if in_repo; then echo "."; else echo "$KIT"; fi; }
log()      { printf '\033[1;36m[fdk-kit]\033[0m %s\n' "$*"; }

case "${1:-help}" in
  pull)
    if in_repo; then log "đang ở repo overstack — kit có sẵn, khỏi pull."; exit 0; fi
    if [ -d "$KIT/.git" ]; then
      log "cập nhật kit ở $KIT"
      git -C "$KIT" fetch --depth 1 origin "$BASE" && git -C "$KIT" reset --hard "origin/$BASE"
    else
      log "clone overstack → $KIT (sandbox dev framework, KHÔNG đụng dự án của bạn)"
      git clone --depth 1 -b "$BASE" "$REMOTE" "$KIT"
    fi
    # đừng commit kit clone vào dự án của bạn
    grep -qxF "$KIT/" .gitignore 2>/dev/null || echo "$KIT/" >> .gitignore 2>/dev/null || true
    log "sẵn sàng. Distill skill TRONG $KIT: scaffold bằng \`cd $KIT && python3 fdk/tools/new-skill.py <tên>\`,"
    log "viết SKILL.md, register, rồi \`bash $KIT/fdk/tools/fdk-kit.sh check\` và \`… submit <branch> \"<msg>\"\`."
    ;;

  check)
    d="$(kit_dir)"
    [ -d "$d" ] && [ -f "$d/harness/scripts/fdk-gate.py" ] || { log "chưa có kit — chạy: fdk-kit pull"; exit 1; }
    ( cd "$d" && python3 harness/scripts/fdk-gate.py )
    ;;

  submit)
    branch="${2:?cần <branch> (vd: skill/my-new-skill)}"
    msg="${3:?cần \"<commit message>\"}"
    d="$(kit_dir)"
    [ -d "$d" ] && [ -f "$d/harness/scripts/fdk-gate.py" ] || { log "chưa có kit — chạy: fdk-kit pull"; exit 1; }
    ( cd "$d"
      log "fdk-gate trước khi submit (đủ bước mới cho push)…"
      python3 harness/scripts/fdk-gate.py
      git checkout -b "$branch" 2>/dev/null || git checkout "$branch"
      git add -A
      if git diff --cached --quiet; then
        log "không có thay đổi mới để commit — bỏ qua commit."
      else
        git commit -m "$msg"
      fi
      git push -u origin "$branch"
      if command -v gh >/dev/null 2>&1; then
        gh pr create --base "$BASE" --head "$branch" --title "$msg" --fill \
          && log "PR đã mở vào $BASE." \
          || log "push xong nhưng tạo PR lỗi (có thể PR đã tồn tại) — kiểm tra trên GitHub."
      else
        log "gh chưa cài — đã push branch '$branch'. Mở PR thủ công: $REMOTE (base: $BASE)."
      fi
    )
    ;;

  *)
    echo "fdk-kit: pull | check | submit <branch> \"<msg>\""
    echo "  pull    — clone/cập-nhật .overstack/kit/ (đồ nghề dev overstack)"
    echo "  check   — fdk-gate trong kit"
    echo "  submit  — gate → commit → push → tự mở PR"
    ;;
esac
