---
name: dym-impeccable
disable-model-invocation: true
domains: [frontend, design-audit]
source: pbakaus/impeccable
description: "impeccable (pbakaus/impeccable) — workflow đã kiểm chứng. Gõ /dym-impeccable <slug>. slugs: install-into-your-project · detect-cli-scan · tune-detector-ignores · ci-integration · chat-commands · contributor-build-and-test · browser-extension-build"
---

# Skill: dym-impeccable — hub workflow cho impeccable

## When to use
- User gõ `/dym-impeccable` (không tham số → bảng slug) hoặc `/dym-impeccable <slug>`; hoặc `/dym` định tuyến tới đây theo domain.
- Hub chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích |
   |---|---|
   | `install-into-your-project` | Cài Impeccable vào dự án của bạn |
   | `detect-cli-scan` | Quét anti-pattern bằng CLI |
   | `tune-detector-ignores` | Dập false positive: ignore của detector |
   | `ci-integration` | Cắm detector vào CI của dự án bạn |
   | `chat-commands` | 23 lệnh `/impeccable` (chỉ gõ trong CHAT) |
   | `contributor-build-and-test` | Đóng góp: build và test chính Impeccable |
   | `browser-extension-build` | Build extension trình duyệt |

2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `../dym-impeccable-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/impeccable/skills/dym-impeccable-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-impeccable-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

## Rules
- Mỗi sub-skill tự chứa; hub không nhồi cả bundle vào context.
- `workflows.md` cạnh bundle là chỉ mục + bảng kiểm chứng, không phải nguồn lệnh.
