---
type: draft
title: unknown-ledger
status: proposed
tags: [propose, unknown, default, debt, traceability]
timestamp: 2026-07-15
task: T-260715-03
r7_meta: true
---

# 150726-unknown-ledger

**Status:** proposed

## What
Biến việc "model tự điền default để bù gap khi user chưa trả lời" từ một **ghi-vết lặng** (chỉ một tag `(default)` trong `## Assumptions`) thành một **sổ nợ unknown có thật, truy được, trả được**. Ba phần: interview dạng chọn-đáp-án **luôn có thêm một lựa chọn "điền trước, tìm hiểu sau" (fill-first-find-out-later)**; mỗi unknown bị hoãn được ghi vào file `.md` tiền tố `unknown-` trong `llmwiki/wiki/draft/unknown/` kèm **đầy đủ metadata + truy ngược được SPEC/PLAN gốc**; và một luồng **trả nợ**: khi có thông tin thật thì điền vào nguồn + đóng unknown, có audit trail.

## Context
Đã query wiki + đọc trạng thái trước khi soạn (force-query, R7-f):

- SPEC `150726-mattpocock-absorb` + `140726-spec-kit-traceability` (đã giao) — `/propose` hiện có ba tầng: **fact** (tra, không hỏi) · **decision rủi ro thấp** → `(default)` (tự điền, ghi `## Assumptions`) · **decision rủi ro cao** → `[CẦN LÀM RÕ]` (chặn cổng duyệt, R7-n).
- **Khoảng hở đang có:** khi user (hoặc model có phép) hạ một `[CẦN LÀM RÕ]` xuống `(default)` "một cách có chủ ý", thứ ghi-vết duy nhất là cái tag trong `## Assumptions`. Không có sổ, không truy được, không có luồng trả nợ. Một `(default)` rủi ro cao được điền để không chặn việc rồi **chìm vào quên lãng** — đúng cái "silent" mà cả hệ này sinh ra để chống.
- `harness/scripts/frontier.py`, `design-variety.py`, `skill-health.py` — mẫu engine tất định 0-token đọc file wiki, travel qua global harness. Sổ unknown dùng đúng khuôn này.
- R5 folder-structure: `draft` là subdir hợp lệ → `wiki/draft/unknown/` (lồng) qua được. R9 (frontmatter+type) và R2 (`## Origin`) áp cho `wiki/draft/**` → mỗi file unknown **bắt buộc** có metadata + Origin, đúng yêu cầu "đầy đủ metadata truy vết". R3 (index-sync) → file unknown phải vào `index.md`.
- R7 scope gồm `wiki/draft/**`: file unknown KHÔNG có `## Plan` nên tự miễn R7 (không phải proposal). Đã kiểm.
- `[[skill-craft]]` — sổ unknown là reference travel-được, tool đọc; áp progressive disclosure.

**Kết luận:** đây không phải cơ chế mới cạnh tranh `(default)`/`[CẦN LÀM RÕ]`. Nó là **tầng thứ ba** đóng khoảng hở giữa hai cái đó: một `(default)` mà ta *biết là rủi ro và sẽ phải kiểm lại* thì thay vì im lặng, ghi thành nợ có sổ. "Fill-first" giữ việc chạy (không chặn); "find-out-later" giữ nợ không chìm.

## Global constraints
- **ADR-003:** hành vi `/propose` định nghĩa ở `skills/propose/SKILL.md` (canonical); mirror + bản cài sinh bằng `sync-skill.sh`.
- **Không đẻ rule id mới:** nếu cần cưỡng chế, mở rộng validator có sẵn. Rule đổi thì cả hai `policy.yaml` sửa giống hệt + bite-test hai tầng.
- **Engine tất định phải TỚI ĐƯỢC downstream** (bài học `p-26`): `unknown-ledger.py` ở global harness, verify travel bằng UAT.
- **Sổ unknown là file wiki hợp lệ:** frontmatter + `type` + `## Origin` (R9/R2), có trong `index.md` (R3). Một file MỘT nguồn (gom mọi unknown của một SPEC), không một-file-một-unknown (chống phình index).
- **Truy vết hai chiều bắt buộc:** dòng `(default)` trong SPEC trỏ tới file unknown + U-id; file unknown trỏ ngược SPEC + FR-id + task-id.
- **Không ghi công AI** (R15). **Trước push:** `medic --ci` xanh + repo-health local + `/fdk-uat` hai pha PASS (sentinel grep-verify).

## Non-goals
- **Không** bỏ hay đổi nghĩa `(default)` / `[CẦN LÀM RÕ]`. Tầng thứ ba đứng giữa, không thay hai cái kia.
- **Không** biến sổ unknown thành issue tracker thứ hai. Nó chỉ theo dõi *unknown-đã-fill-chờ-verify*, khác `/raise-issue` (feature-gap/tech-debt) và `[CẦN LÀM RÕ]` (chặn cổng).
- **Không** tự động "tìm hiểu" giùm — find-out-later là hành động có chủ ý của user/agent sau, skill chỉ ghi nợ và cung cấp luồng trả.
- **Không** chặn cổng duyệt vì có unknown mở. Fill-first nghĩa là *không chặn* — chặn thì mất điểm. Chỉ **báo cáo** số nợ để nó không chìm.

## Approaches
**(A) Chỉ thêm tag `(default, find-out-later)` vào Assumptions, không đẻ sổ.** Rẻ nhất. Nhưng vẫn không truy được, không có luồng trả nợ — đúng khoảng hở đang than.

**(B) Nhét unknown vào ledger issue chung (`ISSUES.md`).** Tái dùng hạ tầng. Nhưng trộn unknown-chờ-verify với issue-feature-gap làm cả hai khó đọc; unknown gắn chặt một SPEC cụ thể, cần truy vết per-FR mà ledger issue không có.

**(C) — chọn.** Sổ riêng `wiki/draft/unknown/unknown-<nguồn>.md` (một file một SPEC, gom mọi unknown của nó), metadata + truy vết hai chiều, engine tất định `unknown-ledger.py` để list/add/resolve, interview thêm lựa chọn "fill-first-find-out-later", và một bước báo-cáo (không chặn) để nợ hiện ra. Đắt hơn (A) đúng một file format + một script + một mục skill, nhưng đó là toàn bộ khoản chênh, và nó đóng trọn khoảng hở.

## Plan

- [ ] **T1 — `/propose`: lựa chọn thứ ba "fill-first, find-out-later".** Thêm vào mục fact/decision của propose: khi interview dạng chọn-đáp-án, **luôn có một đáp án cuối** — *"Điền mặc định bây giờ, tìm hiểu sau (ghi nợ unknown)"*. Chọn nó → model điền một default hợp lý NGAY (việc không bị chặn), **và** ghi unknown vào sổ. Áp cho cả trường hợp hạ `[CẦN LÀM RÕ]` → thay vì hạ xuống `(default)` im lặng, hạ xuống `(default, find-out-later → [[unknown-<slug>]] U-NN)` có sổ. Dòng trong `## Assumptions` mang tag đó + link file unknown.

- [ ] **T2 — Format sổ unknown + folder `wiki/draft/unknown/`.** Một file một SPEC nguồn: `unknown-<source-slug>.md`, frontmatter (`type: unknown-ledger`, `source_task`, `source_spec`, `status: open|partial|resolved`, `timestamp`) + `## Origin`. Thân là danh sách `## U-01`, `## U-02`… mỗi mục: **Trace** (FR-id · SPEC path · task-id) · **Đã fill (default)** (giá trị model tự chọn) · **Cần verify** (thông tin thật phải lấy để trả nợ) · **Rủi ro nếu default sai** · **Status** (open/resolved) · **Resolved** (giá trị đúng + fix ở đâu + ngày — điền khi trả nợ). Template `wiki/draft/unknown/_template.md`.

- [ ] **T3 — Engine tất định `harness/scripts/unknown-ledger.py` (0-token).** `--list` (mọi unknown mở, gom theo nguồn, cũ nhất trước) · `--add --source <spec> --task <T-id> --fr <FR-id> --q "<câu hỏi>" --default "<giá trị>" --verify "<cần lấy gì>" --risk "<...>"` (append một U-NN, tự đánh số) · `--resolve <file> <U-id> --value "<giá trị thật>" --fixed "<sửa ở đâu>" --date <YYYY-MM-DD>` (đánh dấu resolved + audit) · `--trace <U-id>` (in đường truy ngược SPEC/FR/task) · `--json`. Self-test BAD/GOOD.

- [ ] **T4 — Luồng TRẢ NỢ (find-out-later → fix).** Ghi vào `/propose` (hoặc một mục riêng): khi có thông tin thật cho một unknown — (1) điền giá trị đúng vào **SPEC/PLAN nguồn** (thay dòng `(default, find-out-later)`); (2) `unknown-ledger.py --resolve` đóng U-NN với giá trị + chỗ đã fix + ngày; (3) nếu unknown đó đã đẻ ra code sai (default sai đã thi hành) → mở `/orca-issue` hoặc `/raise-issue` để sửa code, link ngược U-id. Audit trail: file unknown giữ cả giá trị-đã-fill lẫn giá trị-đúng, không xoá lịch sử.

- [ ] **T5 — Nợ HIỆN RA, không chìm (báo-cáo, không chặn).** `/lint` thêm một bước (hoặc `medic` một probe): `unknown-ledger.py --list` in số unknown mở + cái cũ nhất + SPEC nào nhiều nợ nhất. **Báo cáo, KHÔNG chặn** — fill-first là cố ý không chặn; chặn ở đây là phản bội chính cơ chế. Mục đích chỉ để nợ không rot: người duyệt/định kỳ thấy "còn N unknown chờ verify, cái cũ nhất 12 ngày".

- [ ] **T6 — Register + cổng + UAT.** `sync-skill.sh propose`; regen `CAPABILITIES.md` + `overstack.html`; `capability-stamp --update`; append `wiki/index.md` + `log.md`; node problem-tree; `medic --ci` + repo-health local; `/fdk-uat` hai pha (canary → main-URL smoke, sentinel grep-verify).

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| T1 — /propose lựa chọn thứ ba | Claude | Hợp đồng skill trung tâm, nuance cao | pending |
| T2 — format sổ unknown + folder | Claude | Chạm wiki (nguồn chân lý) + rule R9/R2/R3 | pending |
| T3 — unknown-ledger.py | Claude | Engine tất định, parse/audit sai là mất truy vết | pending |
| T4 — luồng trả nợ | Claude | Hợp đồng skill, nối /orca-issue | pending |
| T5 — nợ hiện ra (lint/medic) | OpenCode `big-pickle` (fallback Claude) | Cơ học: thêm một bước gọi script có sẵn. Watchdog 60–90s | pending |
| T6 — register + cổng + UAT | OpenCode `big-pickle` (fallback Claude) | Cơ học: script có sẵn + UAT. Watchdog 60–90s | pending |

**Sequence diagram:** [150726-unknown-ledger-seq.html](../../../html/150726-unknown-ledger-seq.html)

## Requirements (FR)
- **FR-001**: Interview dạng chọn-đáp-án của `/propose` PHẢI luôn có một đáp án cuối "điền mặc định bây giờ, tìm hiểu sau (ghi nợ unknown)".
- **FR-002**: Chọn "fill-first-find-out-later" PHẢI điền một default NGAY (không chặn việc) VÀ ghi unknown vào sổ.
- **FR-003**: Mỗi unknown bị hoãn PHẢI được ghi vào `llmwiki/wiki/draft/unknown/unknown-<nguồn>.md` với metadata đầy đủ (frontmatter type/source_task/source_spec/status + Origin).
- **FR-004**: Mỗi unknown PHẢI truy ngược được SPEC/PLAN gốc + FR-id + task-id; và dòng `(default)` trong SPEC PHẢI trỏ tới file unknown + U-id (hai chiều).
- **FR-005**: PHẢI có engine tất định `unknown-ledger.py` để list / add / resolve / trace, 0-token.
- **FR-006**: PHẢI có luồng TRẢ NỢ: có thông tin thật → điền vào nguồn + `--resolve` đóng unknown với giá trị đúng + chỗ fix + ngày, giữ audit trail.
- **FR-007**: Nợ unknown mở PHẢI hiện ra ở một bước báo-cáo (lint/medic), **báo cáo không chặn**.

## Success criteria (SC)
- **SC-001**: Một unknown user bảo "cứ điền, tính sau" **không bao giờ chìm** — nó nằm trong sổ, `--list` in ra được, và người duyệt thấy còn bao nhiêu nợ.
- **SC-002**: Sáu tháng sau, nhìn một dòng `(default)` trong SPEC là **truy ngược được** unknown gốc, biết model đã đoán gì và cần verify gì.
- **SC-003**: Khi có thông tin thật, trả nợ là **một luồng rõ** (điền nguồn + resolve + link code-fix nếu cần), không phải đi tìm lại xem đã đoán gì ở đâu.
- **SC-004**: Việc **không bị chặn** bởi unknown — fill-first giữ dòng chảy; hệ chỉ nhắc, không cản.
- **SC-005**: Sổ unknown **cắn/đọc được ở dự án curl-cài** (engine travel qua global harness) — chứng minh bằng `/fdk-uat`.

## Assumptions
Trường user không nói, model tự điền — mọi dòng `(default)`, sửa được:
- Folder dùng đúng path user nêu: `llmwiki/wiki/draft/unknown/` `(default)` — không đổi thành `sources/draft/unknown/` cho khớp SPEC/PLAN, vì user chỉ định rõ.
- Một file MỘT nguồn (gom unknown của một SPEC) `(default)` — chống phình `index.md` (R3), và truy vết per-SPEC gọn hơn một-file-một-unknown.
- Id unknown là `U-01`, `U-02`… trong phạm vi một file `(default)` — ngắn, đọc được, không cần global-unique vì đã có source_spec định danh file.
- `unknown-ledger.py` đặt `harness/scripts/` `(default)` — cùng chỗ frontier/skill-health/design-variety, travel qua global harness.
- Bước báo-cáo gắn vào `/lint` `(default)` — cùng chỗ skill-health (8b); không đẻ probe medic riêng để giữ medic gọn.

Không mục nào rơi `[CẦN LÀM RÕ]`: thay đổi nội-bộ framework, không chạm auth/dữ-liệu-người-dùng/tiền/pháp-lý.

## Risks
- **Sổ unknown thành bãi rác nếu không ai trả nợ.** Giảm thiểu: T5 làm nợ hiện ra (số + tuổi cái cũ nhất); và trả nợ là một luồng rẻ (T4). Nhưng bản chất đây là nợ *cố ý* — hiện ra là đủ, ép trả là phản cơ chế.
- **File unknown làm phình `index.md` (R3).** Giảm thiểu: một file một nguồn, không một-file-một-unknown. Số SPEC có unknown thường ít.
- **Truy vết hai chiều lệch** (SPEC trỏ U-01 nhưng file đổi số). Giảm thiểu: `unknown-ledger.py --add` tự đánh số và in ra U-id để dán vào SPEC; `--trace` kiểm được link còn đúng không.
- **Lẫn với `[CẦN LÀM RÕ]`.** Giảm thiểu: ranh giới rõ trong skill — `[CẦN LÀM RÕ]` = *chặn cổng, chưa được điền* (nhóm nguy hiểm); `(default, find-out-later)` = *đã điền để chạy, ghi nợ để verify sau* (rủi ro vừa, có chủ ý hoãn). Hai trạng thái khác nhau của cùng một trục.

## Self-review
- **Phủ yêu cầu:** FR-001→T1 · FR-002→T1 · FR-003→T2 · FR-004→T2+T3 · FR-005→T3 · FR-006→T4 · FR-007→T5. T6 là cổng. Không FR nào không có task.
- **Placeholder:** không còn mục bỏ trống.
- **Nhất quán tên:** folder `wiki/draft/unknown/`; file `unknown-<nguồn>.md`; `type: unknown-ledger`; id `U-NN`; tag SPEC `(default, find-out-later → [[unknown-<slug>]] U-NN)`; engine `harness/scripts/unknown-ledger.py`. Dùng đúng như vậy trong code.

## Notes
- Đóng khoảng hở giữa `(default)` và `[CẦN LÀM RÕ]` do [[140726-spec-kit-traceability]] và [[150726-mattpocock-absorb]] tạo ra.
- Truy vết dùng lại `FR-id` (spec-kit) + `T-id` (code-logger) đã có.

## Origin
- **Draft:** `wiki/sources/draft/150726-unknown-ledger.md`
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
