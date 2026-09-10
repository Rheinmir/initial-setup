---
name: dym-agent-desktop-route
disable-model-invocation: true
description: "Chọn đúng công cụ cho một việc 'điều khiển máy': agent-desktop vs orca computer vs claude-in-chrome vs playwright-verify vs browser-use REPL. Gọi khi phân vân dùng cái nào, hoặc khi một cái vừa thất bại và cần đường lui."
---

# dym-agent-desktop-route

## When to use
- Sắp làm một việc chạm UI ngoài trình duyệt và không chắc gọi tool nào.
- Một tool vừa thất bại (mù AX, chặn localhost, ref chết) và cần đường lui có lý do.

## Steps

1. **Trả lời hai câu, ra ngay đáp án**: mục tiêu nằm TRONG trình duyệt hay ngoài? Máy đang
   chạy macOS hay không?

| việc | công cụ | vì sao |
|---|---|---|
| Trang web / web app, cần điều khiển DOM | `/playwright-verify` | rẻ nhất, selector ổn định, chạy được `file://` và `localhost` |
| Trang web nhiều bước, giữ session | `/playwright-verify` mode CDP, hoặc `/dym-browser-use repl` | tab và cookie sống giữa các lượt |
| Trang web trong Chrome thật của user | `claude-in-chrome` | dùng đúng profile/đăng nhập của user; **chặn localhost và `file://`** |
| App desktop macOS **native** (System Settings, Finder, Numbers, Notes) | **agent-desktop** | ref bền, skeleton, actionability, mã lỗi rẽ nhánh được |
| App desktop trên Linux/Windows | `orca computer` | agent-desktop chỉ hỗ trợ darwin |
| UI của chính app Orca, worktree/terminal Orca | `orca-cli` / `orca computer` | cùng runtime, không cần thêm binary |
| App Electron chưa bật AX (Teams, một số Slack build) | `launch --cdp` + client CDP | **cả hai tool AX đều mù** ở ranh giới "Web content" |

2. **Nếu chọn agent-desktop** → `/dym-agent-desktop install` rồi `/dym-agent-desktop drive`.
3. **Nếu cần biên lai** → `/dym-agent-desktop session`.

## So sánh đã ĐO (2026-09-09, macOS 24.6 arm64, agent-desktop 0.8.5)

| trục | `orca computer` | `agent-desktop` |
|---|---|---|
| Nền tảng | macOS + Linux (`orca-ide`) | **darwin only** (`SUPPORTED_PLATFORMS = ['darwin']`; crate windows/linux 76 dòng stub) |
| Chi phí cài | 0 — đi kèm app Orca | +3.0M binary + 498K helper qua npm |
| Định danh phần tử | element-index, **sống trong một lượt trả về**, tài liệu của chính nó ghi "short-lived, go stale" | `@<snapshot_id>:eN`, refmap ghi xuống đĩa → **resolve được ở tiến trình khác, vài phút sau** |
| Ref chết | không có mã lỗi riêng — index sai trỏ nhầm phần tử | `STALE_REF` / `SNAPSHOT_NOT_FOUND` + `recovery.strategy` |
| Cửa sổ nhập nhằng | **tự chọn một cửa sổ, không báo** (Teams 2 cửa sổ → trả w-9249) | `AMBIGUOUS_TARGET` + liệt kê đủ ứng viên |
| Chi phí token, app dày | System Settings: treeText **3313 ký tự** / 117 dòng, một phát cả cây | full `-i --compact` **24185 B** / 168 ref; skeleton **4630 B** / 27 ref rồi drill |
| Bề mặt lệnh | ~15 lệnh | 55 lệnh chạy được / 59 tên (surfaces, notifications, clipboard, wait, batch, session, trace) |
| Headless | không khai — thao tác đi đường vật lý | **mặc định headless**, `--headed` mới cướp focus/di chuột |
| Bằng chứng | không có | trace JSONL + `trace export` ra HTML |
| Nhiều agent | không có khái niệm | session dùng chung + `AGENT_DESKTOP_AGENT_ID` + lease con trỏ |

## Rules
- **Đừng đọc "agent-desktop rẻ token hơn" từ bảng trên.** Ở độ sâu đầy đủ nó ĐẮT hơn
  `orca computer` khoảng 5 lần mỗi phần tử (JSON vs treeText thụt lề). Cái nó tiết kiệm là
  **số lượt** — skeleton + drill + ref không chết, nên bớt vòng snapshot lại từ đầu.
- Việc **một lượt, một app thưa, đọc rồi thôi** → `orca computer` vẫn thắng: 0 cài, 1 lệnh.
- Việc **nhiều bước, có mutation, cần verify và cần biên lai** → agent-desktop thắng rõ.
- Không có tool nào ở đây thay được nhau về nền tảng: Linux thì agent-desktop là số 0.
- Web thì đừng dùng cả hai — AX của trình duyệt là con đường dài nhất tới một cái nút.
