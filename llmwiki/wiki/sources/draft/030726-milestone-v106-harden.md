---
type: draft
title: "030726-milestone-v106 — hardening (medic 17/17 + framework-touch hook) + query-implement"
status: proposed
tags: [milestone, v1.0.6, medic, fdk-hardening, query, retrieval, output-report]
timestamp: 2026-07-03
relations:
  - {rel: derives-from, to: 030726-eval-report}
  - {rel: touches, path: harness/scripts/harness-doctor.py}
  - {rel: touches, path: fdk/tools/medic.py}
  - {rel: touches, path: harness/scripts/trace-grader.py}
---

# 030726-milestone-v106 — hardening + query-implement

**Type:** draft · **Status:** proposed · **Proposed:** 2026-07-03 · **Task:** T-260703-02

## What
Milestone v1.0.6: hiện thực các NỢ đã ghi ở v1.0.5 — biến 2 verdict council + issue #4 thành code: (1) medic thành cổng tự-cắn đủ phủ (17/17) + gương-soi-cuối-phiên; (2) hiện thực query-verdict (đừng ép query, đo thiệt-hại-thật, hạ /query, code-graph rẻ, retrieval tự-surface).

## Context (force-query — nợ từ v1.0.5)
- **[[030726-eval-report]]** + council `council-report-020-seed42.html` (winner Lão Tử): đòn bẩy = **medic gương-soi-cuối-phiên khi đụng framework**; giữ 2 cổng tự-cắn **A1** (generator-only + probe) + **A7** (medic 5/17→17/17, hấp thụ A3 sync-direction-check); A2/A6 thành phụ lục /fdk. Bằng chứng cấp thiết: release v1.0.5 vừa lộ **dark rail R7-f** (validator thiếu check `## Context`) mà medic 5/17 KHÔNG bắt — chỉ commit-gate bắt.
- Council `council-report-022-seed42.html` (query): query-rate là **vanity/Goodhart**; đo **reinvent-rate + cross-break-rate + harm-when-missing**; tách 3 lớp — wiki-content (giữ), code-graph/quan-hệ-phi-cục-bộ (giữ+đầu tư, cho **entrypoint rẻ 1-lệnh**), /query-skill (**hạ xuống optional**); retrieval **tự-surface** thay vì ép gọi.
- **Issue #4** (github) — logger có đủ thông tin cho trace-grading 5 phiên cũ không (tiền-đề cho đo reinvent/cross-break qua [[trace-grader]]).

## Impact
| Vùng | Ảnh hưởng |
|------|-----------|
| `harness/scripts/harness-doctor.py` | mở `build_rN` 5→17 (rủi ro chạm fire-drill) |
| `fdk/tools/medic.py` | thêm probe artifact-khớp-generator (A1) |
| `llmwiki/.claude/hooks/` | hook mới framework-touch-detector + pre-edit cross-break (opt-in, default nhẹ) |
| `harness/scripts/trace-grader.py` + logger | đo reinvent/cross-break từ session log |
| skill `/query` | hạ mô tả xuống optional (không xoá) |

## Plan
- [x] **T1 — medic coverage 5/17 → 17/17.** ✅ (commit ef12c4a) — fire-drill tổng quát hoá theo KIND: block/block-argv/-dir/-commitmsg/-poc/-git/side-effect/wiring. Mở `harness-doctor build_rN` 4 tầng: content-validator mở rộng (R11/R13/R14/R16 + validator lẻ), hook_event (R3/R4/R8/R10/R17 feed synthetic-event), process_gate (R12/R15 temp-git BAD-state), documentary (R6 presence). Hấp thụ **A3 sync-direction-check** (so bản đang-cắn 2 chiều trước sync).
- [x] **T2 — hook framework-touch-detector → medic-cuối-phiên.** ✅ — `stop.py::framework_medic_mirror`: chỉ repo framework (có `fdk/tools/medic.py`) + git-status thật chạm `fdk/|harness/|skills/|llmwiki/` → tự chạy `medic --ci` cuối lượt. Khoẻ (kể cả warn) → 1 dòng khẽ báo; FAIL thật (exit≠0) → **chặn dừng (exit 2)** in chỗ hở để sửa sớm (guard `stop_hook_active` chống lặp). Fail-open tuyệt đối.
- [ ] **T3 — A1 generator-only probe.** medic probe: artifact có generator (overstack/capabilities/skill-whiteboard…) mà bị sửa tay (hash lệch nguồn sinh) → cảnh báo.
- [ ] **T4 — code-graph entrypoint rẻ + hạ /query.** Một lệnh `graph <symbol>` → callers/callees/derives phi-cục-bộ ngay terminal (không skill 3 tầng). Sửa mô tả `/query` xuống optional-shortcut.
- [ ] **T5 — retrieval tự-surface.** Hook pre-edit: nếu code-graph phát hiện file sắp sửa có quan hệ phi-cục-bộ agent chưa chạm → chèn cảnh báo cross-break (bảo hiểm không cần yêu cầu).
- [ ] **T7 — auto session-provenance.** Stop-hook ghi `sources/DDMMYY-session-provenance.md` cuối phiên: session-id → chức năng sinh (từ ledger+events) → context (council/proposal đã dùng) → commit. Để session MỚI query được 'chức năng này từ phiên nào, vì sao' (chỗ hở user chỉ 2026-07-03). events.jsonl bổ sung field `session`.
- [ ] **T6 — đo thiệt-hại-thật (không query-rate).** Rà issue #4 (logger đủ chưa) → thêm mục **reinvent-rate + cross-break-rate** vào `/orca-eval` (dùng trace-grader); retro-test mẫu 31% "mù". BỎ đo query-rate.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do | Status |
|------|-------------|-------|--------|
| T1 medic 17/17 | Claude | fixture BAD/GOOD + synthetic hook/git = reasoning-heavy | pending |
| T2 framework-touch hook | Claude | logic phạm-vi + tránh theater | pending |
| T3 generator-probe | Claude | hash/fingerprint artifact | pending |
| T4 code-graph entrypoint | Claude | tái dùng code-graph + hạ /query | pending |
| T5 retrieval tự-surface | Claude | hook pre-edit + graph query | pending |
| T6 đo reinvent/cross-break | Claude | rà logger (issue #4) + wire orca-eval/trace-grader | pending |

**Sequence diagram:** [030726-milestone-v106-harden-seq.html](../../../html/030726-milestone-v106-harden-seq.html)

## Success
1. `medic` phủ **17/17 rule** có bite-test; thêm rule mới thiếu test → medic tự FAIL. (bug R7-f kiểu vừa rồi bị bắt SỚM, không phải ở commit-gate).
2. Phiên đụng framework tự chạy medic cuối (gương-soi); phiên project thường KHÔNG.
3. `graph <symbol>` chạy 1 lệnh trả quan-hệ phi-cục-bộ; `/query` đã hạ mô tả.
4. `/orca-eval` báo **reinvent-rate + cross-break** (không query-rate); issue #4 có kết luận logger.
5. Không thêm phụ thuộc phần mềm ngoài; medic-gate không thành theater (chỉ đụng-framework).

## Origin
- **Draft:** `wiki/sources/draft/030726-milestone-v106-harden.md`
- **Commit:** _(verify-before-commit điền)_
- **Date promoted:** _(verify-before-commit điền)_
