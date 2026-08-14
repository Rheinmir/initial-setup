#!/usr/bin/env bash
# bootstrap-fork.sh — cài overstack từ MỘT FORK, một dòng, không đụng repo gốc.
#
# Vì sao có file này: `bootstrap.sh` gọi `install.sh`, mà `install.sh` mặc định kéo mọi thứ
# từ repo gốc + nhánh chính. Muốn cài từ fork thì phải nhớ và trỏ ĐÚNG BỐN biến
# (HARNESS_BASE · REPO_RAW · SKILLS_REF · HARNESS_REPO) — nhớ tay thì sai một cái là bản cài
# lặng lẽ trộn hai nguồn, và cổng nghiệm thu vẫn xanh vì nó chấm nhầm bản cũ. File này gói
# cả bốn lại: gõ một dòng, không phải nhớ gì.
#
# Cài (một dòng, thay <owner>/<repo>/<ref> cho fork của bạn):
#   curl -fsSL https://raw.githubusercontent.com/dragonwar000/setup/graph-engineering/harness/poc-vendor-neutral/bootstrap-fork.sh | bash
#
# Đổi nguồn mà không sửa file — mọi biến đều override được:
#   ... | FORK_OWNER=ai-do FORK_REPO=setup FORK_REF=main bash
#   ... | bash -s -- --harness-only        # cờ của bootstrap.sh vẫn dùng nguyên
#
# Kiểm nguồn trước khi cài (không tải gì, chỉ in ra rồi thoát):
#   ... | bash -s -- --print-source
set -euo pipefail

# Mặc định trỏ fork dragonwar000 nhánh graph-engineering. Sửa 3 dòng này để có bản riêng
# cho fork khác, hoặc truyền biến môi trường như trên.
FORK_OWNER="${FORK_OWNER:-dragonwar000}"
FORK_REPO="${FORK_REPO:-setup}"
FORK_REF="${FORK_REF:-graph-engineering}"

RAW="https://raw.githubusercontent.com/$FORK_OWNER/$FORK_REPO/$FORK_REF"

say(){ printf '\033[1;36m[bootstrap-fork]\033[0m %s\n' "$*"; }
die(){ printf '\033[1;31m[bootstrap-fork]\033[0m %s\n' "$*" >&2; exit 1; }

for a in "$@"; do
  case "$a" in
    --print-source)
      printf 'owner=%s repo=%s ref=%s\nraw=%s\n' "$FORK_OWNER" "$FORK_REPO" "$FORK_REF" "$RAW"
      exit 0 ;;
  esac
done

say "nguồn: $FORK_OWNER/$FORK_REPO@$FORK_REF"

# Kiểm nguồn SỐNG trước khi cài. Không có bước này thì ref sai / fork private sẽ biểu hiện
# thành "cài xong mà thiếu file", khó truy hơn nhiều so với một lỗi 404 nói thẳng.
for probe in harness/poc-vendor-neutral/bootstrap.sh harness/scripts/install-harness.sh; do
  code=$(curl -fsS -o /dev/null -w '%{http_code}' "$RAW/$probe" 2>/dev/null || echo 000)
  [ "$code" = "200" ] || die "không đọc được $probe từ $FORK_OWNER/$FORK_REPO@$FORK_REF (HTTP $code).
  Kiểm: fork có tồn tại? ref '$FORK_REF' đã push chưa? repo có phải private không?"
done
say "nguồn sống ✓ (bootstrap.sh + install-harness.sh)"

# Bốn biến — thiếu bất kỳ cái nào là cài trộn nguồn:
#   HARNESS_BASE  nơi install.sh lấy lõi vendor-neutral
#   REPO_RAW      gốc raw để kéo file lẻ; install-harness.sh SUY ref VÀ owner/repo từ đây
#   SKILLS_REF    nguồn skill cho `npx skills` — thiếu thì cài skill của nhánh chính
#   HARNESS_REPO  repo để clone khi bundle thiếu — thiếu thì clone repo GỐC ở ref của fork,
#                 và nếu ref đó chỉ tồn tại trên fork thì bước cài global fail lặng lẽ
curl -fsSL "$RAW/harness/poc-vendor-neutral/bootstrap.sh" \
  | HARNESS_BASE="$RAW/harness/poc-vendor-neutral" \
    REPO_RAW="$RAW" \
    SKILLS_REF="$FORK_OWNER/$FORK_REPO#$FORK_REF" \
    HARNESS_REPO="$FORK_OWNER/$FORK_REPO" \
    bash -s -- "$@"

say "xong — nguồn dùng: $FORK_OWNER/$FORK_REPO@$FORK_REF"
say "kiểm nhanh: ls harness/ · cat CAPABILITIES.md · /hooks (trong Claude Code)"
