---
name: dym-scientific-agent-skills
disable-model-invocation: true
domains: [science, research]
source: K-Dense-AI/scientific-agent-skills
description: "scientific-agent-skills (K-Dense-AI/scientific-agent-skills) — workflow đã kiểm chứng. Gõ /dym-scientific-agent-skills <slug>. slugs: cai-dat-skills · tham-dinh-truoc-khi-cai · dung-skill-trong-agent · chay-script-bundled-tu-shell · pin-va-cap-nhat · gate-trong-ci-cua-ban · dong-gop-them-sua-skill · dong-gop-validate-test-scan"
---

# Skill: dym-scientific-agent-skills — hub workflow cho scientific-agent-skills

## When to use
- User gõ `/dym-scientific-agent-skills` (không tham số → bảng slug) hoặc `/dym-scientific-agent-skills <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
   | `cai-dat-skills` | Cài Scientific Agent Skills vào agent của bạn |
   | `tham-dinh-truoc-khi-cai` | Thẩm định một skill TRƯỚC khi cài |
   | `dung-skill-trong-agent` | Dùng skill trong agent (CHỈ prompt, không phải lệnh shell) |
   | `chay-script-bundled-tu-shell` | Chạy script bundled thẳng từ shell (không cần agent) |
   | `pin-va-cap-nhat` | Ghim version, cập nhật, gỡ bỏ |
   | `gate-trong-ci-cua-ban` | Đưa skill vào CI của DỰ ÁN BẠN |
   | `dong-gop-them-sua-skill` | Đóng góp: thêm hoặc sửa một skill |
   | `dong-gop-validate-test-scan` | Đóng góp: validate, test, scan |

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../dym-scientific-agent-skills-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/scientific-agent-skills/skills/dym-scientific-agent-skills-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-scientific-agent-skills-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
