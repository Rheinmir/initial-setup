---
name: dym-nuwa-skill
disable-model-invocation: true
domains: [skill-authoring, agent]
source: alchaincyf/nuwa-skill
description: "nuwa-skill (alchaincyf/nuwa-skill) — workflow đã kiểm chứng. Gõ /dym-nuwa-skill <slug>. slugs: install · distill-a-person · diagnose-then-distill · use-and-update-persona · helper-scripts-cli · fidelity-scorecard · publish-and-get-listed · contributor-repo-itself"
---

# Skill: dym-nuwa-skill — hub workflow cho nuwa-skill

## When to use
- User gõ `/dym-nuwa-skill` (không tham số → bảng slug) hoặc `/dym-nuwa-skill <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
   | `install` | Cài nüwa (女娲) vào runtime của bạn |
   | `distill-a-person` | Chắt lọc một nhân vật (đường trực tiếp, chat-only) |
   | `diagnose-then-distill` | Chưa biết chắt lọc ai: đường chẩn đoán (chat-only) |
   | `use-and-update-persona` | Dùng và cập nhật một persona skill (chat-only) |
   | `helper-scripts-cli` | Bốn script phụ trợ chạy trong terminal |
   | `fidelity-scorecard` | Chấm bảo chân (Fidelity Scorecard) cho skill vừa làm ra |
   | `publish-and-get-listed` | Phát hành skill của bạn và xin thu vào COMMUNITY.md |
   | `contributor-repo-itself` | Đóng góp vào chính repo nüwa (contributor track) |

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../dym-nuwa-skill-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/nuwa-skill/skills/dym-nuwa-skill-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-nuwa-skill-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
