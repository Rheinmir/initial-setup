---
type: issue
kind: tech-debt
title: "pre-commit (17-rule fire-drill) chạy >2 phút khi commit — dễ timeout, ngắt giữa chừng làm hỏng index"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, tech-debt, harness, pre-commit, backstop, ci]
timestamp: 2026-07-04
id: 040726-precommit-slow-fragile-on-commit
source_session: "phiên orca-fdk issue-16 (2026-07-04) — commit A+B+C kích hoạt pre-commit và bị timeout"
---

# Issue: pre-commit chậm + giòn khi bị ngắt

## Vấn đề (một câu)
Hook `pre-commit` (bộ fire-drill 17 rule) chạy quá 2 phút cho một lần `git commit` thường, nên dễ bị timeout; và khi bị kill giữa chừng, cơ chế stash-patch của pre-commit để lại **index hỏng** (hàng trăm "deletion" ảo dù file vẫn còn trên đĩa) + cất các thay đổi chưa-staged vào một patch chưa kịp trả lại — người dùng phải khôi phục thủ công.

## Bối cảnh & bằng chứng
- Phiên 2026-07-04, khi commit nhóm A+B+C của issue-16: `git commit` treo, pre-commit in `Stashing unstaged files to ~/.cache/pre-commit/patch1783099903-61068`, chạy qua hàng loạt rule (R2/R5/R7/R9/R3/L4/R13/meta-drift…) rồi bị cắt ở mốc 2 phút.
- Hậu quả: `git status` báo **621 "D" (deletion) staged** trong khi mọi file vẫn tồn tại trên đĩa → index bị pre-commit reset dở dang. Thay đổi unstaged (gồm cả sửa `skills/ship/SKILL.md`) bị lùi về bản HEAD trong working tree, nằm trong patch cache chưa trả lại.
- Khôi phục thủ công đã làm được: backup patch → `git reset` (index về HEAD, không đụng file) → `git apply` patch → về nguyên trạng, không mất dữ liệu. Nhưng đây là bẫy dễ mất việc nếu người dùng không biết patch nằm ở `~/.cache/pre-commit/`.
- Workaround đã dùng để commit tiếp: `git commit --no-verify` sau khi `medic --ci` đã xanh (gate tương đương) + CI remote (L3) chạy lại trên PR. PR #17 merge xanh bằng đường này.
- Liên quan: `[[harness-enforcement-floor]]` (3 tầng L1 hook / L2 pre-commit / L3 CI), skill `[[medic]]` (probe `backstop` nhắc cài pre-commit). Nghịch lý: backstop L2 vừa là thứ được khuyến khích bật, vừa là thứ đang gây timeout + rủi ro hỏng cây.

## Phạm vi
- Cấu hình `.pre-commit-config.yaml` + các hook script `harness/scripts/harness-doctor.py` (fire-drill) và các validator được gọi trong pre-commit. Cách pre-commit chạy (toàn bộ bộ rule mỗi commit thay vì chỉ file đổi). Universal (mọi repo cài harness đều dính).

## Không thuộc phạm vi
- Không bỏ backstop L2 (giá trị chặn-lúc-commit vẫn cần).
- Không đụng gate CI L3 (harness.yml) — nó là tầng khác, đang chạy nhanh (<15s/job).

## Hướng gợi ý (không bắt buộc)
1. **Chỉ chạy trên file đổi**: cấu hình pre-commit dùng danh sách file staged (mặc định của framework pre-commit) thay vì fire-drill toàn bộ 17 rule mỗi lần — fire-drill đầy đủ để dành cho `medic`/CI.
2. **Tách "kiểm nhanh" (pre-commit) khỏi "chứng minh đầy đủ" (medic/CI)**: pre-commit chỉ chạy validator content trên file đổi (giây), bộ fire-drill BAD/GOOD 17-rule chuyển hẳn sang `medic --ci` + CI.
3. **Atomic/khôi-phục-được**: nếu vẫn giữ hook nặng, thêm cơ chế tự phục hồi (trap EXIT khôi phục patch) hoặc tài liệu rõ đường cứu `~/.cache/pre-commit/patch*`.
4. **Bump timeout** cho lệnh commit trong quy trình agent (skill `ship` ghi rõ commit có thể mất vài phút) — giải pháp tạm, không sửa gốc.

## Tiêu chí HOÀN THÀNH
- `git commit` một thay đổi thường xong dưới ~15 giây (không chạy fire-drill toàn bộ mỗi commit).
- Bị ngắt giữa chừng KHÔNG để lại index hỏng (hoặc có đường tự phục hồi được ghi rõ).
- Bộ fire-drill 17-rule vẫn được chạy đủ ở `medic --ci` + CI (không mất độ phủ).

## Assign & lý do
- @Rheinmir chủ; Claude dispatch (đụng cấu hình harness + validator). Mở `/fdk`. P2 — đã có workaround `--no-verify` + medic xanh nên không chặn việc, nhưng là bẫy mất-việc cho người dùng khác.

## Origin
Raise bởi phiên orca-fdk issue-16 (2026-07-04). Bằng chứng: log pre-commit `patch1783099903-61068`; `git status` 621 D ảo; khôi phục bằng reset+apply; PR #17 merge qua `--no-verify`.

## Kết quả (2026-07-04 — done)
- Đo lại: bộ 25 hook chạy mỗi commit trước đây → nay **12 hook nhanh** theo file-đổi; `pre-commit run` = **0.16s** (trước >2 phút). DoD #1 ✓ (<15s).
- Dời TRỌN fire-drill nặng (arch-scan · index-sync · wiki-health · harness-lint · duplicate-basename · 2 ADR test · decision-adr-gate-test · adr-delete-guard · capabilities · adapt-registry · harness-local-check) sang CI job "repo health" (đã có sẵn) — **không mất phủ**. `policy-converters-drift` chưa có ở CI → thêm mới vào harness.yml.
- Cửa sổ interrupt còn sub-second ⇒ gần như loại index-hỏng-khi-kill (DoD #2); thêm đường cứu `~/.cache/pre-commit/patch*` vào comment config.
- Căn cứ ADR: concept [[harness-enforcement-floor]] — "CI là sàn thật, pre-commit chỉ chặn-sớm"; đổi này đưa L2 về đúng vai.
