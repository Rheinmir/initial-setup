---
name: dym-cti-expert
disable-model-invocation: true
domains: [security, threat-intel]
source: 7onez/cti-expert
description: "cti-expert (7onez/cti-expert) — workflow đã kiểm chứng. Gõ /dym-cti-expert <slug>. slugs: install-and-register · api-keys-and-capabilities · investigate-in-claude-code · cli-dispatcher · case-pipeline-and-kb · reports-and-iocs · safety-gates · ci-monitoring · contributor-develop-and-gate"
---

# Skill: dym-cti-expert — hub workflow cho cti-expert

## When to use
- User gõ `/dym-cti-expert` (không tham số → bảng slug) hoặc `/dym-cti-expert <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
   | `install-and-register` | Cài đặt & đăng ký với Claude Code |
   | `api-keys-and-capabilities` | API key, năng lực keyless, và sổ chi phí |
   | `investigate-in-claude-code` | Điều tra bằng lệnh chat (CHỈ trong Claude Code) |
   | `cli-dispatcher` | Dispatcher CLI: `intel.py` (CHỈ trong terminal) |
   | `case-pipeline-and-kb` | Chạy một case: pipeline, cluster, KB |
   | `reports-and-iocs` | Bàn giao: báo cáo HTML, bundle IOC/STIX, DOCX, bản đã che |
   | `safety-gates` | Rào an toàn: cái gì bị CHẶN, cái gì HỎI, cái gì im lặng |
   | `ci-monitoring` | Chạy cti-expert trong CI của **dự án bạn** |
   | `contributor-develop-and-gate` | Nhánh đóng góp: sửa chính cti-expert |

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../dym-cti-expert-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/cti-expert/skills/dym-cti-expert-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-cti-expert-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
