---
type: issue
kind: tech-debt
title: "2/3 deny-rule chặn raw/ là NO-OP — Write()/MultiEdit() không khớp file-permission check, spam cảnh báo mọi phiên"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, tech-debt, harness, permissions, rule-khong-can]
timestamp: 2026-07-17
id: 170726-deny-rule-raw-no-op
source_session: "đọc log phiên agent trong workspace payroll-poc khi chạy /fdk-poc (17/07/26)"
---

# Issue: 2/3 luật chặn `raw/` không cắn

## Vấn đề (một câu)
`install-harness.sh` ship 3 deny-rule cho `raw/` nhưng **chỉ `Edit(path)` khớp** file-permission check của Claude Code — `Write(...)` không khớp và `MultiEdit` không phải tool có thật ⇒ **2/3 luật là no-op**, đồng thời **spam 3 dòng cảnh báo ở mọi phiên**.

## Bối cảnh & bằng chứng
Bắt được khi ĐỌC LOG phiên agent trong workspace `payroll-poc`. Claude Code in ra ngay khi khởi động:
```
Permission deny rule "MultiEdit(./llmwiki/raw/**)" matches no known tool — check for typos.
Permission deny rule (~/.claude/settings.json): Write(./llmwiki/raw/**) is not matched by file
  permission checks — only Edit(path) rules are. Use Edit(./llmwiki/raw/**) instead
  (Edit rules cover all file-editing tools).
Permission deny rule (~/.claude/settings.json): MultiEdit(./llmwiki/raw/**) is not matched by ...
```
Nguồn ship:
- `harness/scripts/install-harness.sh:158` (global) — `for d in ["Write(./llmwiki/raw/**)", "Edit(...)", "MultiEdit(...)"]`
- `harness/scripts/install-harness.sh:316` (per-project) — `deny = [f"Write(./{prefix}raw/**)", f"Edit(...)", f"MultiEdit(...)"]`

**Đây là "rule không cắn"** — đúng thứ framework này ghét nhất. Luật `NEVER write to raw/` (AGENT.md/CLAUDE.md)
ở tầng permission chỉ còn **1/3 chân**. May là còn hook `llmwiki-validate.py` (PreToolUse) gác thật, nên
raw/ vẫn được bảo vệ — nhưng đó là may, không phải thiết kế: nếu ai gỡ hook thì tưởng vẫn còn 3 lớp.

Điểm đau thêm: 3 dòng cảnh báo hiện ở **mọi phiên của mọi project đã cài harness** → nhiễu, và người
đọc quen mắt sẽ bỏ qua cả cảnh báo thật.

Đáng chú ý: `fdk-gate` **19/20 vẫn xanh** — vì gate kiểm **REPO**, không kiểm **cái ĐÃ CÀI**.
Cùng khoảng trống mà `/fdk-uat` sinh ra để lấp. Liên quan: `[[040726-precommit-slow-fragile-on-commit]]`
(harness-enforcement-floor: CI là sàn thật).

## Repro
1. Mở bất kỳ phiên `claude` nào trong project đã cài harness (hoặc có `~/.claude/settings.json` do install-harness ghi).
2. 3 dòng cảnh báo hiện ngay khi khởi động.
3. `python3 -c "import json;print(json.load(open('$HOME/.claude/settings.json'))['permissions']['deny'])"` → thấy cả 3 rule.

## Phạm vi
- `harness/scripts/install-harness.sh` — 2 chỗ (`:158` global, `:316` per-project).
- Universal: mọi máy/project đã cài harness.

## Không thuộc phạm vi
- Không gỡ hook `llmwiki-validate.py` (nó là lớp gác THẬT, giữ nguyên).
- Không đổi luật nghiệp vụ "NEVER write to raw/".
- Không dọn `~/.claude/settings.json` đã có sẵn trên máy người dùng (chỉ sửa cái ship ra từ nay).

## Hướng gợi ý
Giữ đúng một rule khớp thật:
```python
for d in ["Edit(./llmwiki/raw/**)"]:      # Edit-rule đã phủ MỌI tool sửa file
```
(và tương tự ở khối per-project). Kèm comment giải thích vì sao bỏ 2 cái kia, để lần sau không ai "thêm lại cho chắc".

## Tiêu chí HOÀN THÀNH
- Cài mới → `~/.claude/settings.json` chỉ có `Edit(./llmwiki/raw/**)`.
- Mở phiên claude → **0 dòng cảnh báo** permission.
- Thử `Write` vào `llmwiki/raw/x.md` → vẫn bị chặn (hook + Edit-rule).

## Assign & lý do
`@Rheinmir` · Claude · `/fdk` — sửa lõi install, cần verify bằng phiên thật (mở claude xem còn cảnh báo không).
**Ghi chú:** fix đã có sẵn trong nhánh `Rheinmir/issue-15-br-k` (PR #78).

## Origin
- Raise bởi phiên chạy `/fdk-poc` thật trên `payroll-poc` (17/07/26) — cảnh báo lộ ra khi `orca terminal read` phiên agent.
- Bằng chứng: log phiên (3 dòng verbatim ở trên); `install-harness.sh:158,316`.
