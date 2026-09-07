---
name: dym-setup
disable-model-invocation: true
description: "overstack (rheinmir/setup) — workflow đã kiểm chứng. Gõ /dym-setup <slug>. slugs: install · guardrail-cli · agent-workflow · ci · maintain · contributor"
---

# Skill: dym-setup — hub workflow cho overstack

## When to use
- User gõ `/dym-setup` (không tham số → bảng slug) hoặc `/dym-setup <slug>`.
- Đây là hub: context chỉ tốn dòng description; thân workflow con chỉ đọc khi được gọi.

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng, không đọc file nào.

   | slug | mục đích | nhánh |
   |---|---|---|
   | `install` | cài/gỡ overstack, cờ thật, ghi gì vào $HOME, xác nhận rào cắn | tiêu thụ |
   | `guardrail-cli` | validator từ shell: 3 mode, 19 luật, mã thoát 0/1/2 | tiêu thụ |
   | `agent-workflow` | vòng /propose → /plan → /verify-before-commit → /ship (lệnh chat) | tiêu thụ |
   | `ci` | GitHub Actions tối giản cho dự án tiêu thụ + pre-commit | tiêu thụ |
   | `maintain` | nâng bản, migrate, rc 0/3/4/1, tool nào chạy được ở downstream | tiêu thụ |
   | `contributor` | sửa chính overstack: fdk-gate, medic, UAT canary, ship | đóng góp |

2. Đọc ĐÚNG MỘT file `doyourmagic/setup/skills/dym-setup-<slug>/SKILL.md` (đường tương đối từ gốc dự án) rồi làm theo `## Steps` và `## Rules` của nó. Không đọc file con khác.
3. Slug lạ → in bảng ở bước 1, dừng.

## Rules
- Chỉ đọc file con được gọi; không nạp cả bundle.
- Lệnh chat (`/x`) chỉ gõ trong chat; lệnh shell chỉ gõ trong terminal — file con đã tách sẵn.
