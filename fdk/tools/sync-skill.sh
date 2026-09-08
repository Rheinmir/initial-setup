#!/usr/bin/env bash
# sync-skill.sh <tên-skill> [...] — đồng bộ 1 skill từ bản canonical ra 2 bản còn lại:
#   canonical : skills/<tên>/SKILL.md            (nguồn sự thật)
#   mirror    : llmwiki/skills/<loop>/<tên>.md   (tự dò loop dir đang có)
#   installed : ~/.claude/skills/<tên>/SKILL.md  (bản máy user, phiên nào cũng đọc)
# Sinh ra từ eval 020726: sync tay bằng cp lặp 3 lần/phiên → drift khi quên (finding #2).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

[ $# -ge 1 ] || { echo "usage: sync-skill.sh <tên-skill> [...]"; exit 2; }

fail=0
for name in "$@"; do
  src="skills/$name/SKILL.md"
  if [ ! -f "$src" ]; then echo "✗ $name: thiếu canonical $src"; fail=1; continue; fi

  mirror=$(ls llmwiki/skills/*/"$name".md 2>/dev/null | head -1 || true)
  if [ -n "$mirror" ]; then
    cp "$src" "$mirror" && echo "✓ $name → $mirror"
  else
    echo "⚠ $name: chưa có mirror trong llmwiki/skills/*/ — đăng ký bằng new-skill.py trước"
  fi

  inst="$HOME/.claude/skills/$name/SKILL.md"
  mkdir -p "$(dirname "$inst")"
  cp "$src" "$inst" && echo "✓ $name → $inst"
  # skill có scripts/ references/ assets/ → bản cài phải mang theo, không thì SKILL.md trỏ vào hư không (prd-grade-fe 080926)
  for sub in scripts references assets; do
    [ -d "skills/$name/$sub" ] && rsync -a --delete "skills/$name/$sub/" "$HOME/.claude/skills/$name/$sub/" && echo "✓ $name/$sub → ~/.claude/skills/$name/$sub"
  done

  # verify parity — sync mà không kiểm là vòng phản hồi cụt
  [ -z "$mirror" ] || diff -q "$src" "$mirror" >/dev/null
  diff -q "$src" "$inst" >/dev/null

  # Sổ checksum phải đi cùng nhịp với nội dung. Sửa SKILL.md rồi quên `record` thì
  # CI đỏ ở bước skill-provenance, mà cổng đó lại chạy MUỘN (chỉ trên CI, không phải
  # pre-commit) nên người sửa biết rất trễ. Đã dính hai lần trong một phiên (08/09:
  # skill `diagram`, rồi `fdk-uat`) — vá tay lần hai là sai quy trình, nên ghim vào
  # đây: đã sync là sổ tự cập nhật, không phải nhớ.
  if [ -f fdk/tools/skill-provenance.py ]; then
    python3 fdk/tools/skill-provenance.py record "$name" --source local-authored >/dev/null 2>&1 \
      && echo "✓ $name → sổ checksum (skill-provenance)" \
      || echo "⚠ $name: không cập nhật được sổ checksum — chạy tay: python3 fdk/tools/skill-provenance.py record $name --source local-authored"
  fi
done
exit $fail
