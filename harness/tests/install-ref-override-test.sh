#!/usr/bin/env bash
# install-ref-override-test — cổng nghiệm thu KHÔNG được mù với chính bản đang nghiệm thu.
#
# Bất-biến: nguồn clone của install-harness.sh phải ĐI THEO ref mà người cài đang trỏ tới.
# Trước rào này, 4 lệnh clone đều hardcode `-b orca`: UAT canary override REPO_RAW/SKILLS_REF
# vẫn bị kéo hook+engine từ nhánh CHÍNH → canary chấm bản CŨ rồi báo kết quả cho bản MỚI.
# Mù với: llmwiki/.claude/hooks/**, harness/scripts/**, harness/validators/**, fdk/tools/**.
# Đã cháy thật 2026-07-17 (UAT auto-capture: hook global 2121B, record_bite=0 dù canary có).
#
# Usage: bash harness/tests/install-ref-override-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
IH="$ROOT/harness/scripts/install-harness.sh"
fail=0
ok()  { printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
bad() { printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

ref() { env -u HARNESS_REF -u REPO_RAW "$@" bash "$IH" --print-ref 2>/dev/null; }

# 1. Không ai trỏ gì → nhánh chính (người dùng bình thường không đổi hành vi).
r=$(ref); [ "$r" = "orca" ] && ok "mặc định = orca (người cài bình thường không đổi)" \
                            || bad "mặc định phải là orca, ra '$r'"

# 2. REPO_RAW trỏ canary → ref ĐI THEO canary. Đây là ca đã cháy.
r=$(ref REPO_RAW="https://raw.githubusercontent.com/Rheinmir/setup/uat-260717-2105")
[ "$r" = "uat-260717-2105" ] && ok "REPO_RAW canary → ref đi theo" \
                             || bad "canary ref sai: kỳ vọng 'uat-260717-2105', ra '$r'"

# 2b. Ref CÓ dấu "/" vẫn được trích đúng (không cắt cụt) — NHƯNG đó chỉ là chuyện
#     truyền biến. Đo được 2026-09-08: `npx skills add <owner>/<repo>#<ref-có-/>` resolve
#     đúng ref rồi CHẾT IM LẶNG ở bước discovery (curl: (3) URL rejected), cài 0 skill,
#     trong khi install.sh vẫn báo "3 trụ ✓" → bài UAT canary thành ảo giác.
#     Nên test này chỉ được kết luận "ref đi theo", TUYỆT ĐỐI không được đọc thành
#     "ref có / dùng được". Đặt tên canary không dấu / — xem skills/fdk-uat/SKILL.md.
r=$(ref REPO_RAW="https://raw.githubusercontent.com/Rheinmir/setup/uat/260717-2105")
[ "$r" = "uat/260717-2105" ] && ok "ref có dấu / được trích nguyên vẹn (CHỈ là truyền biến, KHÔNG chứng minh cài được skill)" \
                             || bad "ref có / bị cắt: ra '$r'"

# 3. HARNESS_REF ép tay thắng suy diễn.
r=$(env HARNESS_REF=my-branch bash "$IH" --print-ref 2>/dev/null)
[ "$r" = "my-branch" ] && ok "HARNESS_REF ép tay thắng REPO_RAW" \
                       || bad "HARNESS_REF phải thắng, ra '$r'"

# 4. REPO_RAW lạ host (không phải raw.githubusercontent) → không đoán bừa, về mặc định.
r=$(ref REPO_RAW="https://example.com/whatever")
[ "$r" = "orca" ] && ok "REPO_RAW lạ host → không đoán bừa, về orca" \
                  || bad "host lạ phải fallback orca, ra '$r'"

# 5. Rào chống tái phát: không còn lệnh clone nào ghim cứng tên nhánh.
n=$(grep -cE '^[^#]*git clone .*-b +(orca|main|master)\b' "$IH" 2>/dev/null || true)
[ "${n:-0}" -eq 0 ] && ok "không còn clone hardcode tên nhánh trong install-harness.sh" \
                    || bad "$n lệnh clone còn ghim cứng tên nhánh → canary sẽ lại chấm nhầm bản"

if [ "$fail" -eq 0 ]; then
  printf '\n\033[1m═══ install-ref-override: \033[1;32mPASS\033[0m\033[0m\n'; exit 0
fi
printf '\n\033[1m═══ install-ref-override: \033[1;31m%d VI PHẠM\033[0m\033[0m\n' "$fail"; exit 1
