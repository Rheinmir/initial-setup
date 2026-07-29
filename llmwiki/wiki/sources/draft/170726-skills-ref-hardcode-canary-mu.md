---
type: issue
kind: tech-debt
title: "install.sh hardcode `skills add rheinmir/setup#orca` — skill nhánh canary không tới tay user, /fdk-uat pha-1 mù"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, tech-debt, install, skills, fdk-uat, canary]
timestamp: 2026-07-17
id: 170726-skills-ref-hardcode-canary-mu
source_session: "chạy /fdk-poc THẬT trên project mới payroll-poc (17/07/26) — curl bootstrap với HARNESS_BASE trỏ nhánh canary"
---

# Issue: install.sh hardcode nhánh skill → canary không kiểm được

## Vấn đề (một câu)
`harness/poc-vendor-neutral/install.sh:230` hardcode `npx -y skills add rheinmir/setup#orca --global --all` và **không có `SKILLS_REF` để override**, nên `HARNESS_BASE` trỏ nhánh canary được nhưng **skill luôn kéo từ `orca`** — skill mới của nhánh canary không bao giờ tới tay user qua đường cài chuẩn cho tới khi merge.

## Bối cảnh & bằng chứng
Phát hiện khi chạy `/fdk-poc` THẬT: tạo project mới `payroll-poc` trong Orca rồi `curl bootstrap` với
`HARNESS_BASE=https://raw.githubusercontent.com/Rheinmir/setup/Rheinmir/issue-15-br-k/harness/poc-vendor-neutral`.

Kết quả: **harness** tới từ nhánh canary (đúng), nhưng log install in ra:
```
+ cài bộ skill llmwiki (global, qua npx skills)
  npx -y skills add rheinmir/setup#orca --global --all      ← REF HARDCODE
```
⇒ skill về từ `orca`, KHÔNG phải nhánh đang test. Suýt kết luận nhầm "skill mới đã travel qua remote" —
kiểm lại mới thấy `/fdk-poc` + `/qc-uiux` có ở global **chỉ vì copy tay**, không phải do remote.

Đây đúng lớp lỗi mà `fdk-uat` sinh ra để bắt — skill `fdk-uat` nói rõ phải override **cả ba** biến
(`HARNESS_BASE` + `REPO_RAW` + `SKILLS_REF`), nhưng `SKILLS_REF` **chưa tồn tại trong install.sh**.
Hệ quả: **pha-1 (canary, trước merge) của `/fdk-uat` mù** với lớp lỗi "docs hứa mà user không nhận
được" (GH#77) — đúng thứ nó được thiết kế để chặn.

Liên quan: `[[150726-qc-code-skill]]` (skill mới cần travel), `[[050726-reachability-sweep-skill-tools]]` (GH#54 — skill trỏ tool không ship, cùng họ "publish ≠ tới tay").

## Repro
1. Project trống mới, `curl -fsSL "<canary>/bootstrap.sh" | HARNESS_BASE="<canary>" bash`
2. `ls ~/.agents/skills/` → **không có** skill mới của nhánh canary.
3. `grep -n 'skills add' harness/poc-vendor-neutral/install.sh` → thấy `#orca` cứng.

## Phạm vi
- `harness/poc-vendor-neutral/install.sh` (khối `WITH_SKILLS`).
- Universal: mọi lần cài downstream + mọi lần chạy `/fdk-uat` pha canary.

## Không thuộc phạm vi
- Không đụng `REPO_RAW`/`HARNESS_BASE` (đã override được).
- Không đổi cách `npx skills` hoạt động.
- Không tự merge skill canary vào `orca`.

## Hướng gợi ý
```sh
SKILLS_REF="${SKILLS_REF:-orca}"
SKILLS_PKG="rheinmir/setup#${SKILLS_REF}"
npx -y skills add "$SKILLS_PKG" --global --all
```
+ log ra ref đang dùng để người chạy thấy ngay skill về từ nhánh nào.

## Tiêu chí HOÀN THÀNH
- `SKILLS_REF=<nhánh> curl … | bash` → `~/.agents/skills/` có skill CHỈ tồn tại ở nhánh đó.
- Không set `SKILLS_REF` → vẫn về `orca` (không đổi hành vi mặc định).
- Log in ra ref đang dùng.
- `/fdk-uat` pha-1 override được cả 3 biến như skill nó mô tả.

## Assign & lý do
`@Rheinmir` · Claude · `/fdk` — sửa lõi install của framework, cần chạy `/fdk-uat` để tự kiểm.
**Ghi chú:** fix đã có sẵn trong nhánh `Rheinmir/issue-15-br-k` (PR #78) — issue này để ledger/tracker không trôi và để lần sau truy được vì sao đổi.

## Origin
- Raise bởi phiên chạy `/fdk-poc` thật trên `payroll-poc` (17/07/26).
- Bằng chứng: log `curl bootstrap` in `rheinmir/setup#orca`; `install.sh:230`; skill `fdk-uat` (mục HAI PHA) đòi `SKILLS_REF` mà install không có.
