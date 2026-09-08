---
name: dym-diagram-design
disable-model-invocation: true
domains: [diagram, frontend]
source: cathrynlavery/diagram-design
description: "diagram-design (cathrynlavery/diagram-design) — workflow đã kiểm chứng. Gõ /dym-diagram-design <slug>. slugs: install-and-verify · brand-onboarding-and-profiles · authoring-in-chat · import-extractors-shell · import-export-slash-commands · selfcheck-and-your-ci · contributor-gates"
---

# Skill: dym-diagram-design — hub workflow cho diagram-design

## When to use
- User gõ `/dym-diagram-design` (không tham số → bảng slug) hoặc `/dym-diagram-design <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
   | `install-and-verify` | Cài đặt và chứng minh nó chạy |
   | `brand-onboarding-and-profiles` | Onboard brand và quản lý profile khách hàng |
   | `authoring-in-chat` | Vẽ sơ đồ bằng chat (không có CLI cho việc này) |
   | `import-extractors-shell` | Hai extractor chạy trong terminal (draw.io và Mermaid) |
   | `import-export-slash-commands` | Slash command: import và export (gõ trong chat) |
   | `selfcheck-and-your-ci` | Tự kiểm output và khoá nó bằng CI của BẠN |
   | `contributor-gates` | Nhánh người đóng góp: cổng kiểm và luật release |

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../dym-diagram-design-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/diagram-design/skills/dym-diagram-design-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-diagram-design-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
