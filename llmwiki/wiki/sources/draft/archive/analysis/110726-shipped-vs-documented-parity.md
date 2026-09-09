---
type: issue
kind: tech-debt
title: "Parity ship: tài liệu hứa N năng lực nhưng installer chỉ giao M — không cổng nào bắt"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, capabilities, parity, skills, fresh-install, npx]
timestamp: 2026-07-11
id: 110726-shipped-vs-documented-parity
source_session: test fresh-install-gate.md → phát hiện npx giao 67/74 skill trong im lặng
---

# Issue: số năng lực TÀI LIỆU HỨA ≠ số năng lực THẬT SỰ GIAO

## Vấn đề (một câu)
`overstack.html` và `CAPABILITIES.md` đều đọc từ ĐĨA nên cùng báo 74 skill, trong khi `npx skills add --all` chỉ thật sự giao 67 — ba nguồn soi lẫn nhau và cùng sai so với thứ tới tay người dùng; không cổng nào so "hứa" với "giao".

## Bối cảnh & bằng chứng
- Đo 2026-07-11: `overstack.html` = **74 skill** · `fdk/CAPABILITIES.md` = **74 skill** · `npx skills add … --all` = **"Installed 67 skills"**.
- 7 skill không bao giờ tới tay ai: `web-crawl`, `web-clone`, `harness-tour`, `harness-update`, `health-check`, `trace-grader`, `uat-nonit-testcase`.
- Nguyên nhân *lần này*: frontmatter YAML hỏng (`description:` inline chứa `": "` chưa quote → `ScannerError`) → CLI `skills` bỏ qua **không in lỗi**. Đã sửa + đã gác bằng probe `capsurface` (parse YAML thật) — xem [[110726-eval-blinding-grader-context]] họ hàng về "cổng phải tự chạy".
- **Nhưng đó mới là gác NGUYÊN NHÂN, chưa gác HỆ QUẢ.** Nguyên nhân khác vẫn có thể làm lệch mà im lặng: skill không đăng ký trong `.claude-plugin/marketplace.json`, CLI đổi luật validate, tarball lỗi, network fail giữa chừng…
- Người dùng đọc tài liệu thấy `/web-crawl`, gõ vào thì không có gì — đây là mất uy tín trực tiếp, không phải nợ kỹ thuật trừu tượng.

## Phạm vi
- `harness/scripts/fresh-install-smoke.sh` (mode `--remote` vốn ĐÃ chạy npx thật — chỗ đặt tự nhiên).
- `harness/downstream-contract.yaml` (khai điều kiện parity).
- Universal.

## Không thuộc phạm vi
- Không sửa CLI `skills` (bên thứ ba).
- Không đưa parity vào gate `--local` (offline, không chạy npx được) — đây là acceptance của `--remote`.

## Hướng gợi ý
- Sau khi `--remote` chạy `npx`, bắt số `Installed N skills` và so với số skill trên đĩa (trừ ngoại lệ cố ý như `fdk` theo ADR-004). Lệch → ĐỎ, in ra **tên** skill bị rớt, không chỉ con số.

## Tiêu chí HOÀN THÀNH
- `fresh-install-smoke --remote` ĐỎ khi có skill trên đĩa không tới được global; in đúng tên skill rớt.
- Negative-test: bẻ hỏng 1 skill → cổng đỏ đúng tên đó.

## Assign & lý do
- @Rheinmir / Claude / `/fdk`: đụng cổng ship, cần người giữ harness quyết mức chặn.

## Origin
Raised bởi `/raise-issue` (phiên 2026-07-11) khi test đầy đủ theo `fdk/docs/fresh-install-gate.md`: phát hiện tài liệu hứa 74 mà installer giao 67. Bằng chứng: output `npx skills add`, `fdk/CAPABILITIES.md`, `llmwiki/html/overstack.html` tại commit `0723450`.
