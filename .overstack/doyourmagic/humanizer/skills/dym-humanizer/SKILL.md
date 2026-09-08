---
name: dym-humanizer
disable-model-invocation: true
domains: [writing, copy]
source: blader/humanizer
description: "humanizer (blader/humanizer) — workflow đã kiểm chứng. Gõ /dym-humanizer <slug>. slugs: install-shell · install-claude-plugin · humanize-pasted-text · humanize-files-and-embedded · tune-false-positives · contributor-validate-and-release"
---

# Skill: dym-humanizer — hub workflow cho humanizer

## When to use
- User gõ `/dym-humanizer` (không tham số → bảng slug) hoặc `/dym-humanizer <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
   | `install-shell` | Cài Humanizer bằng shell (Skills CLI / copy tay) |
   | `install-claude-plugin` | Cài Humanizer làm plugin Claude Code (lệnh chat) |
   | `humanize-pasted-text` | Chữa văn bản dán trực tiếp (chế độ mặc định) |
   | `humanize-files-and-embedded` | Chữa file trên đĩa, và nhúng vào việc khác (chế độ file / embedded) |
   | `tune-false-positives` | Chặn sửa quá tay: false positive và chi tiết người cần giữ |
   | `contributor-validate-and-release` | Sửa chính Humanizer: bộ kiểm và luật phát hành (contributor) |

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../dym-humanizer-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/humanizer/skills/dym-humanizer-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-humanizer-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
