---
type: draft
title: "PLAN thi hành — br proactive fill (T-260714-01)"
status: approved-spec
tags: [br, plan, proactive, defaults, spec-kit, issue-15]
timestamp: 2026-07-14
task: T-260714-01
---

# 140726-br-proactive-fill-PLAN

**SPEC nguồn:** [[140726-br-proactive-fill]] (gate `gate_f5cfd004e73b` approved).
**Phát hiện khảo sát trước PLAN:** ATG mảnh 1 ĐÃ implement từ GH#75 (`depends_on` trong slice/frame-template, topo order + blocked + `affected` trong `br-queue.py`, DAG-cycle check trong `frame-lint.py`, `waiting_on` trong `build-line-status.py`) → **FR-006 chuyển thành verify-only, không code mới**. `br/memos` không tồn tại ở worktree này → project mẫu là `br/payroll`.

## Global constraints (chép nguyên văn từ SPEC — mọi task ngầm mang theo)

- ADR-004: `--proactive` là flag của lệnh user gọi chủ động; KHÔNG watcher/daemon/hook trên `raw/`.
- Kỷ luật fill: mọi giá trị máy điền mang `filled_by` + `verified: false`, hiện trong bảng "Giả định đang gánh"; không trộn với câu trả lời thật của user.
- Carve-out KHÔNG auto-fill: xác thực/phân quyền · lưu trữ dữ liệu · tiền · pháp lý · trust boundary — luôn thành câu hỏi thật. Trần 5 câu, chọn Impact × Uncertainty.
- Frame schema v0: không schema mới; sửa validator phải qua selftest của chính tool.
- R15 không AI-attribution trong commit · prose đầy đủ cho file người đọc · máy chỉ có `python3`.
- Tool mới BẮT BUỘC có `selftest` subcommand (pattern mọi tool `fdk/tools/br-*.py`).

## Task 1 — Registry mặc định (FR-004)

**Files:**
- `skills/br/assets/defaults.yaml` (MỚI — registry framework-level, travel cùng skill)

**Interfaces:**
- Produces: YAML `{schema_version: 0, carveout: [{field, reason}], defaults: [{field, source: loop-26|spec-kit, refs: [A2,…], value, note}]}`
- Consumes: bảng 26 điều kiện `llmwiki/html/140726-br-dieu-kien-day-chuyen.html` (A1–A9/B1–B7/C1–C9+) + convention spec-kit (constitution: test-first, simplicity, no-implementation-details-in-spec; spec template: given-when-then, edge cases, priority).

**Steps:**
1. Soạn `carveout:` = `S2.2` (vai trò & quyền), `S7.2` (bảo mật & phân quyền), `S6.1`/`S6.2` (trust boundary — hệ ngoài), `S8.3` (tiền/ngân sách). Mỗi entry có `reason`.
2. Soạn `defaults:` chỉ những field có default loop-level THẬT (không bịa số đo domain):
   - `S7.5` ← A1/A2/A9 (design-template, vibe Neumorphism, dark/light toggle + localStorage + chống FOUC)
   - `S10.1` ← C1/C8/C9 (acceptance test máy-chạy-được, test-first đỏ→xanh, người viết test, nghiệm thu ground-truth)
   - `S10.2` ← C9 (ground-truth lấy từ dữ liệu bàn giao thật, không fixture bịa)
   - `S1.4`/`S9.1` ← spec-kit constitution (simplicity/YAGNI: mọi thứ không có clause là out-of-scope)
   - `S3.3` ← spec-kit (mỗi flow liệt kê edge case + luồng lỗi)
   - `S4.3` ← spec-kit (ưu tiên must/should/could)
   - `S7.1` ← default khung có điều kiện (UI <2s, job nền <5phút — ghi rõ trong note đây là ngưỡng khung phải được user xác nhận)
3. Kiểm: `python3 -c "import yaml; d=yaml.safe_load(open('skills/br/assets/defaults.yaml')); assert d['schema_version']==0 and d['carveout'] and d['defaults']"` → không lỗi.

## Task 2 — Tool tất định `br-fill.py` (FR-001, FR-002, FR-003 nửa máy, FR-005 nửa máy)

**Files:**
- `fdk/tools/br-fill.py` (MỚI)

**Interfaces:**
- Consumes: `skills/br/assets/spec-template.md` (danh sách field required — parse dòng `- \`S\d+\.\d+\` (required|optional)`), `br/spec-filled.md` (parse block `### S\d+\.\d+` + dòng `status: …`), registry Task 1 (+ override `br/defaults.yaml` nếu có — project thắng), `br/BR.clauses.json`.
- Produces:
  - `fill`: stdout markdown block đề xuất điền (mỗi mục `## S*.*` + `filled_by: default:<ref>|spec-kit:<ref>` + `verified: false` + value) + phần "CÂU HỎI THẬT" (carve-out + không-default); `--json` ra máy đọc.
  - `check-contract`: exit 0 khi mọi required field S1–S10 (status ≠ missing/conflict trong spec-filled) có ≥1 clause khai `fields:` chứa nó trong `BR.clauses.json`; exit 2 + in tên field khi thủng.
  - `selftest`: fixtures inline, exit 0/2.

**Steps:**
1. Viết parser 3 nguồn (template/filled/registry) — hàm thuần, không model, không network.
2. `cmd_fill`: field required mà `status: missing|conflict` → phân loại: (a) `field in carveout` → nhóm CÂU HỎI THẬT (không bao giờ đề xuất giá trị — FR-002); (b) có trong defaults (override > asset) → đề xuất điền kèm `filled_by`/`verified: false` (FR-001); (c) còn lại → nhóm CÂU HỎI THẬT. In cảnh báo nếu nhóm câu hỏi > 5: "chọn 5 theo Impact × Uncertainty, phần còn lại lens-fill" (FR-003 — máy đưa danh sách, model/người chọn).
3. `cmd_check_contract`: đọc spec-template required list + spec-filled statuses + BR.clauses.json; clause được khai thêm khoá `fields: ["S4.2", …]`; required field không được clause nào claim → liệt kê + exit 2 (FR-005).
4. `cmd_selftest`: fixture spec-filled 4 field (1 filled, 1 missing-có-default, 1 missing-carveout, 1 missing-trần) + registry mini + clauses mini; assert: carve-out KHÔNG nằm trong đề xuất; default có `verified: false`; check-contract fail khi bỏ claim 1 field và pass khi đủ.
5. Chạy: `python3 fdk/tools/br-fill.py selftest` → `✓ selftest pass`.

## Task 3 — Wire vào skill `/br` (FR-001, FR-003, FR-005 nửa quy trình)

**Files:**
- `skills/br/SKILL.md` (SỬA — Mode 1 + Mode 2)
- `llmwiki/skills/dev-loop/br.md` (mirror — parity canonical↔mirror)

**Interfaces:**
- Consumes: br-fill.py (Task 2), defaults.yaml (Task 1).
- Produces: Mode 1 thêm nhánh `--proactive`; Mode 2 thêm bước ghi `fields:` per clause + gate `check-contract`.

**Steps:**
1. Mode 1, sau bước gap-diff (bước 3), thêm bước 3b: "`--proactive`: chạy `python3 fdk/tools/br-fill.py fill --root .` → dán block đề xuất vào `NNN-answers.md` (giữ nguyên `filled_by`/`verified: false`); nhóm CÂU HỎI THẬT chọn ≤5 câu theo Impact × Uncertainty đưa vào questions.html; phần còn lại lens-fill như cũ. Carve-out KHÔNG BAO GIỜ nhận giá trị máy."
2. Mode 2, bước 3: BR.clauses.json mỗi clause ghi thêm `fields: [S*.*]` (field nó hiện thực); thêm bước 4: "`python3 fdk/tools/br-fill.py check-contract --root .` — ĐỎ là compile FAIL, sửa BR cho tới khi mọi required field có clause đối ứng"; bảng "Giả định đang gánh" nhóm theo nguồn `default / spec-kit / lens`.
3. Đồng bộ mirror `llmwiki/skills/dev-loop/br.md` (chép các đoạn sửa — giữ parity).

## Task 4 — Verify ATG mảnh 1 (FR-006 — verify-only)

**Files:** không sửa file nào.

**Steps:**
1. `python3 fdk/tools/frame-lint.py selftest` → pass (gồm case DAG cycle).
2. `python3 fdk/tools/frame-lint.py check br/frames --root br/payroll` → xanh trên 16 frame payroll.
3. `python3 fdk/tools/build-line-status.py build --root br/payroll` → line-status.json có khoá `depends_on`/`waiting_on`.
4. Ghi kết quả 3 lệnh vào output report — FR-006 đạt bằng bằng chứng, không code mới.

## Task 5 — Chạy thật trên br/payroll + register (SC-001…SC-004)

**Files:**
- `br/payroll/br/` (artifacts chạy thử — không sửa code app payroll)
- `llmwiki/wiki/draft/orca/140726-br-proactive-fill-report.md` (output report)

**Steps:**
1. Baseline: đếm câu hỏi interview hiện có của payroll (`grep -c '^## S' br/payroll/br/interview/*-answers.md` — kỳ vọng 12 theo điều kiện B2).
2. Chạy `python3 fdk/tools/br-fill.py fill --root br/payroll --json` → đếm: số field đề xuất điền (default/spec-kit) vs số CÂU HỎI THẬT. SC-001 đạt khi câu hỏi thật ≤5 sau khi máy điền.
3. Đối chứng carve-out: trong JSON output, assert không field nào thuộc carveout có đề xuất giá trị (SC-004).
4. `check-contract` trên payroll: kỳ vọng FAIL (BR.clauses.json cũ chưa khai `fields`) → đúng thiết kế back-compat: gate chỉ ăn compile MỚI; ghi rõ vào report.
5. Register: `python3 fdk/tools/build-capabilities.py` + `python3 fdk/tools/medic.py --ci` xanh → commit theo R15, cập nhật ledger GH#15 + index/log wiki.

## Truy vết FR → Task

| FR | Task |
|----|------|
| FR-001 | Task 2 (cmd_fill) + Task 3 (Mode 1) |
| FR-002 | Task 1 (carveout) + Task 2 (phân loại a) |
| FR-003 | Task 2 (cảnh báo >5) + Task 3 (chọn Impact × Uncertainty) |
| FR-004 | Task 1 (registry versioned) + Task 2 (đọc override) |
| FR-005 | Task 2 (check-contract) + Task 3 (Mode 2 gate) |
| FR-006 | Task 4 (verify-only — đã có từ GH#75) |

## Origin
- PLAN mở rộng từ [[140726-br-proactive-fill]] sau gate approve; khảo sát code thật phiên 2026-07-14 (skills/br/SKILL.md, fdk/tools/frame-lint.py, br-queue.py, build-line-status.py, br/payroll).
