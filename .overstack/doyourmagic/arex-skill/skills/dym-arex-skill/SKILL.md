---
name: dym-arex-skill
disable-model-invocation: true
domains: [skill-authoring, agent]
source: VectorSpaceLab/AREX-Skill
description: "arex-skill (VectorSpaceLab/AREX-Skill) — workflow đã kiểm chứng. Gõ /dym-arex-skill <slug>. slugs: cai-dat-disco · cai-thu-vien-skill · chay-viec-researcher · xuat-skill-sang-agent-khac · creator-tao-repo-skill · creator-paper-to-skills · tich-hop-ci · lenh-chat-trong-tui · contributor-phat-trien-cli · contributor-dong-gop-skill"
---

# Skill: dym-arex-skill — hub workflow cho arex-skill

## When to use
- User gõ `/dym-arex-skill` (không tham số → bảng slug) hoặc `/dym-arex-skill <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
   | `cai-dat-disco` | Cài `disco` CLI |
   | `cai-thu-vien-skill` | Cài & bảo trì thư viện AREX-Skill |
   | `chay-viec-researcher` | Chạy việc nghiên cứu ở Researcher mode (shell) |
   | `xuat-skill-sang-agent-khac` | Xuất repo skill sang Claude Code / Codex / agent khác |
   | `creator-tao-repo-skill` | Creator: tạo / verify / refresh / extend một repo skill |
   | `creator-paper-to-skills` | Creator: paper → skill tái lập được (Distiller) |
   | `tich-hop-ci` | Ghim & gác thư viện skill trong CI của **dự án bạn** |
   | `lenh-chat-trong-tui` | Lệnh chat trong TUI (KHÔNG phải lệnh shell) |
   | `contributor-phat-trien-cli` | Contributor: sửa chính DisCo CLI |
   | `contributor-dong-gop-skill` | Contributor: đóng góp / refresh một repo skill vào thư viện |

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../dym-arex-skill-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/arex-skill/skills/dym-arex-skill-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-arex-skill-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
