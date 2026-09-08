---
name: dym-archify
disable-model-invocation: true
domains: [diagram, architecture]
source: tt-a1i/archify
description: "archify (tt-a1i/archify) — workflow đã kiểm chứng. Gõ /dym-archify <slug>. slugs: install-and-verify · agent-chat-authoring · cli-authoring-loop · repository-evidence · visual-check-and-preview · compare-architecture-delta · migrate-workflow-v2 · ci-diagram-gate · contributor-build-and-test"
---

# Skill: dym-archify — hub workflow cho archify

## When to use
- User gõ `/dym-archify` (không tham số → bảng slug) hoặc `/dym-archify <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
   | `install-and-verify` | Cài Archify vào agent harness và chứng minh nó chạy |
   | `agent-chat-authoring` | Soạn sơ đồ từ khung chat của agent |
   | `cli-authoring-loop` | Vòng lặp soạn sơ đồ bằng CLI trong terminal |
   | `repository-evidence` | Sơ đồ architecture gắn bằng chứng mã nguồn thật |
   | `visual-check-and-preview` | Bằng chứng trình duyệt thật và vòng preview trực tiếp |
   | `compare-architecture-delta` | So sánh hai bản architecture (Architecture Delta) |
   | `migrate-workflow-v2` | Nâng nguồn workflow từ `schema_version: 1` lên `2` |
   | `ci-diagram-gate` | Chốt cổng CI cho sơ đồ trong dự án của bạn |
   | `contributor-build-and-test` | Nhánh người đóng góp: build, test, và luật của repo |

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../dym-archify-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/archify/skills/dym-archify-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-archify-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
