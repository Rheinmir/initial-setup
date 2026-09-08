---
name: dym-lieflat-charts
disable-model-invocation: true
domains: [chart, report]
source: git@github.com:larashero3-dotcom/lieflat-charts.git
description: "lieflat-charts (git@github.com:larashero3-dotcom/lieflat-charts.git) — workflow đã kiểm chứng. Gõ /dym-lieflat-charts <slug>. slugs: install · chart-request · report-request · browse-templates · contributor-checks · ci-example"
---

# Skill: dym-lieflat-charts — hub workflow cho lieflat-charts

## When to use
- User gõ `/dym-lieflat-charts` (không tham số → bảng slug) hoặc `/dym-lieflat-charts <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
   | `install` | Cài lieflat-charts vào agent |
   | `chart-request` | Xin biểu đồ (chế độ mặc định) |
   | `report-request` | Xin báo cáo nguyên trang (R01–R12) |
   | `browse-templates` | Xem tận mắt kho template |
   | `contributor-checks` | Hai gate khi bạn sửa chính repo |
   | `ci-example` | CI tối thiểu cho fork của bạn |

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../dym-lieflat-charts-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/lieflat-charts/skills/dym-lieflat-charts-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-lieflat-charts-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
