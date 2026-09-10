---
name: dym-agent-desktop
disable-model-invocation: true
domains: [computer-use, desktop, macos]
source: https://github.com/lahfir/agent-desktop
description: "agent-desktop — CLI Rust điều khiển app desktop qua accessibility tree (macOS-only, 55 lệnh, ref bền giữa các tiến trình). Gõ /dym-agent-desktop <slug> — slugs: install · drive · session · route."
---

# dym-agent-desktop

Bundle sinh từ `/doyourmagic git@github.com:lahfir/agent-desktop.git` (chạy thật 2026-09-09,
bản 0.8.5 trên macOS 24.6 arm64).

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi dừng.
2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại rồi đọc ĐÚNG MỘT file:
   (1) `.claude/skills/dym-agent-desktop-<slug>/SKILL.md`
   (2) `.overstack/doyourmagic/agent-desktop/skills/dym-agent-desktop-<slug>/SKILL.md`
   (3) `doyourmagic-bundles/agent-desktop/skills/dym-agent-desktop-<slug>/SKILL.md`
   Làm theo Steps/Rules của file đó; không đọc file con khác; không thấy cả 3 → nói rõ, dừng.

| slug | mục đích |
|---|---|
| `install` | cài binary có pin scope, kiểm quyền TCC, xác minh chạy được — làm trước mọi thứ |
| `drive` | vòng quan sát-hành động: skeleton → drill → act → verify; hệ ref và bảng lỗi |
| `session` | session/trace/multi-agent cursor — sinh bằng chứng JSONL+HTML cho `/br qc`, `/fdk-poc` |
| `route` | chọn công cụ: agent-desktop vs `orca computer` vs claude-in-chrome vs playwright-verify |

## Rules
- macOS-only trên thực tế: `npm/scripts/postinstall.js` khai `SUPPORTED_PLATFORMS = ['darwin']`;
  crate `windows`/`linux` mỗi cái 76 dòng stub. Linux/Windows → dùng `orca computer`.
- Tool tự mang doc: `agent-desktop skills get desktop --full` in nguyên SKILL + 5 file
  references từ binary. ĐỪNG chép lại doc của nó vào repo ta — sẽ drift theo version.
