---
type: draft
title: "Archetype tester (/test) — vai thứ 6: senior tester thiết kế kịch bản + code test từ SPEC"
status: proposed
tags: [archetype, tester, persona, dispatch, qc]
timestamp: 2026-07-18
task: T-260718-02
---

# 180726-archetype-tester

**Type:** draft
**Status:** proposed
**Tags:** archetype, tester, persona
**Proposed:** 2026-07-18

## What

Thêm archetype thứ 6 **`tester` (`/test`)** vào hệ 5 vai Cherny: persona senior-tester thiết kế **kịch bản test neo FR/SC** + **code test chạy được** (tên `qc-*` để rơi vào lưới `qc-regression` tất định) — lấp lỗ "muốn góc nhìn tester phải tự viết prompt trong đầu".

## Context

- Yêu cầu user 2026-07-18: "cần góc nhìn senior tester agent để tạo artifact test case (kịch bản + code test) — gọi ntn trong hạ tầng?" → tra: 5 archetype (`archetype.py --list`: prototyper/builder/sweeper/grower/maintainer, ADR-015) **không có tester**; `/qc-code` là REVIEW-driven (test từ bug trong diff), không phải DESIGN-driven (test từ yêu cầu).
- Khuôn sẵn có: `llmwiki/personas/<vai>.md` + entry trong `harness/scripts/archetype.py` (`--get /<kw>` in CLI gợi ý + preamble để inject vào dispatch) — orca-workflow cổng 2 dùng đúng cơ chế này.
- Chuỗi tận dụng: SPEC có id `FR-xxx/SC-xxx` (R7) làm nguồn kịch bản; test đặt tên `qc-*` được `qc-regression.py --run` gom chạy tất định (0-token) ở verify-before-commit — persona chỉ cần SINH đúng format, lưới hứng đã có.
- Luật mới capproof (T-260718-01): năng lực mới vào PHẢI kèm bằng chứng sống, không thì medic đỏ.

## Global constraints

- **ADR-015 (archetype):** persona là PREAMBLE inject vào task dispatch; CLI-nào-hợp-vai là adapter `harness/archetypes.config.yaml` (`verified:false`) — thêm vai mới theo đúng khuôn, không đổi cơ chế.
- **ADR-003:** sửa canonical, sync mirror; parity CI gác.
- **capproof ratchet:** năng lực mới phải có proof — persona/archetype mới phải được test sẵn có của archetype.py hoặc test mới nhắc tên.
- **Ponytail:** ≤ ~100 dòng diff tổng; không skill mới (90 giữ nguyên); R15 no-AI-attribution; medic --ci xanh trước push.

## Non-goals

- **KHÔNG** thêm skill `/tester` riêng — archetype + persona là đủ bề mặt; gọi qua dispatch hoặc nói "lấy vai tester".
- **KHÔNG** đụng `/qc-code` (review-driven, giữ nguyên vai) — tester là DESIGN-driven, hai chiều bổ nhau.
- **KHÔNG** tự chạy test framework nặng — persona sinh artifact; việc CHẠY là của runner dự án + qc-regression.

## Approaches

| Phương án | Bản chất | Tradeoff |
|---|---|---|
| **A. Archetype thứ 6 (chọn)** | persona .md + entry archetype.py, khuôn 5 vai sẵn | (+) rẻ, cắm thẳng orca-workflow cổng 2, không phình skill. (−) discovery kém hơn skill (phải biết `/test` hoặc nói "vai tester") — chữa bằng dòng trigger trong CAPABILITIES (tự sinh). |
| B. Skill `/tester` riêng | SKILL.md đầy đủ, model tự route | (+) discovery tốt. (−) 90→91, trùng ranh giới với qc-code ở tầng route (skill-resolve phải thêm golden chống nhầm), nặng hơn nhu cầu. |
| C. Chỉ ghi prompt mẫu vào wiki | 0 code | (+) 0 diff. (−) đúng cái đang muốn thoát: tri thức nằm trong doc, không phải hạ tầng gọi được. |

Chọn **A** — user đã gật hướng này khi duyệt đề xuất miệng 2026-07-18.

## Plan

- [ ] **T1 — Persona `llmwiki/personas/tester.md` + entry archetype:** viết persona theo khuôn 5 file sẵn có (đọc `builder.md` làm mẫu): senior tester 10 năm, phiên THIẾT KẾ TEST không sửa code; giao 2 artifact — kịch bản test neo từng `FR-xxx/SC-xxx` (happy · negative · biên · race, map 13 nhóm lỗi của qc-code làm bản đồ soi) + code test chạy bằng runner sẵn có của dự án, tên `qc-<slug>`, PHẢI đỏ đúng chỗ nghi (cấm test xanh sẵn); ranh giới với /qc-code ghi rõ. Entry `archetype.py`: keyword `/test`, cli `claude` (design cần phán đoán), phase `verify design-first`, tools `qc-code, wikieval`.
- [ ] **T2 — Proof + đồng bộ:** test sẵn có của archetype (nếu có) mở rộng đếm 6 vai, không có thì thêm assert vào test nhắc `archetype.py`; chạy `archetype.py --get /test` in đúng persona; sync mirror; capproof phải nhận `mech/persona` mới không nợ thêm; medic --ci xanh; commit.

## Requirements (FR)

- **FR-001**: `archetype.py --get /test` PHẢI in CLI gợi ý + preamble persona tester (đúng cơ chế 5 vai sẵn có).
- **FR-002**: Persona PHẢI yêu cầu artifact kịch bản neo id FR/SC và code test tên `qc-*` đỏ-trước — khớp lưới qc-regression.
- **FR-003**: Năng lực mới PHẢI proven trong capproof (test nhắc tên hoặc self-test), không thêm dòng nợ ratchet.

## Success criteria (SC)

- **SC-001**: Người cần góc nhìn tester gọi được bằng MỘT từ khoá (`/test` khi dispatch, hoặc "lấy vai tester") thay vì tự soạn prompt — tri thức nằm trong hạ tầng, không trong đầu.
- **SC-002**: Artifact test sinh ra truy ngược được từng kịch bản về đúng FR/SC của SPEC — người duyệt biết yêu cầu nào chưa có test trong một lần nhìn.
- **SC-003**: Test code sinh ra tự rơi vào lưới chạy tất định của dự án (qc-regression) — không cần ai nhớ chạy tay.

## Assumptions

- **A-1** `(default)`: cli cho vai tester = `claude` (thiết kế test cần phán đoán, không phải boilerplate) — đổi được trong `archetypes.config.yaml` (adapter verified:false).
- **A-2** `(default)`: keyword `/test` — nếu đụng lệnh có sẵn nào thì fallback `/tester` (kiểm lúc PLAN).

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 persona + entry | Claude Code | Persona là văn bản hành vi — cần phán đoán ranh giới với qc-code | done |
| T2 proof + sync | Claude Code | Chuỗi gate tất định tại chỗ | done |

**Sequence diagram:** [180726-archetype-tester-seq.html](../../../html/180726-archetype-tester-seq.html)

## Render brief

- **T1** · steps: [legacy] 5 persona + archetype.py sẵn có → [add] tester.md theo khuôn (FR/SC-neo, qc-*, đỏ-trước, 13-nhóm làm bản đồ) → [add] entry /test cli=claude → [block] không đụng qc-code, không skill mới.
- **T2** · steps: [add] test đếm 6 vai / nhắc archetype.py → [add] --get /test chạy thật → [legacy] sync mirror + capproof + medic → [block] không thêm nợ ratchet.

## Self-review

1. **Phủ yêu cầu:** "góc nhìn senior tester tạo kịch bản + code test, gọi được trong hạ tầng" → T1 (persona + keyword) + T2 (proof); đủ.
2. **Quét placeholder:** không còn token trì hoãn.
3. **Nhất quán tên:** vai `tester`, keyword `/test` (fallback `/tester` khai A-2), file `llmwiki/personas/tester.md`, tên test `qc-*` thống nhất xuyên draft.

## Notes

- Invoked via: `/propose` (user gật đề xuất miệng 2026-07-18).

## Origin

- **Draft:** `wiki/sources/draft/180726-archetype-tester.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
