---
type: draft
title: "Capability-proof map — checklist năng lực TỰ SOI (mỗi dòng có bằng chứng sống) + TỰ CỘNG (sinh từ đĩa)"
status: proposed
tags: [capabilities, proof, medic, ratchet, missing-verification]
timestamp: 2026-07-18
task: T-260718-01
---

# 180726-capability-proof-map

**Type:** draft
**Status:** proposed
**Tags:** capabilities, proof, medic
**Proposed:** 2026-07-18

## What

Nâng checklist năng lực từ "liệt kê CÓ MẶT" thành "chứng minh CÒN SỐNG": mỗi capability trong CAPABILITIES.md mang một cột **Proof** trỏ tới bằng chứng chạy được; capability không có bằng chứng bị bêu ở mục **UNPROVEN**; medic probe mới `capproof` gác theo kiểu **ratchet** — nợ cũ không đỏ, nợ MỚI đỏ ngay. **Kèm chiều ngược** (bổ sung tại gate 18/07): các **cách giải CŨ** trong `mechanisms.yaml`/overstack.html cũng đi qua cùng resolver (giải cũ còn sống không?) và bản đồ proof được **đảo chiều** để bêu **ứng viên TRÙNG LẶP** — hai cơ chế cùng giải một việc (ca sống: HAI sổ unknown song song — skill `unknown` ghi `~/.claude/unknowns/` vs `unknown-ledger.py` ghi `llmwiki/wiki/draft/unknown/`).

## Context

- **Động cơ trực tiếp — lớp lỗi `missing-verification` lặp 3 lần trong 2 ngày** (đã ghi flywheel ledger 2026-07-18): auto-capture không tới downstream (engine global thiếu), `frontend-design-delta.md` mồ côi (hallmark không load), fire-drill chưa wire vào CI downstream. Cả ba cùng một hình dạng: **năng lực có mặt trên đĩa nhưng không có đường runtime đi qua, và không cơ chế nào thấy**. Flywheel ngưỡng 3 — lớp này vừa chạm ngưỡng, đề xuất rule là đúng nhịp create→label→fix của nó.
- `fdk/CAPABILITIES.md` — sinh bằng code từ đĩa (`build-capabilities.py`), CI gác khớp ([[ADR-005-logger-and-capabilities-travel-downstream]]): phần "TỰ CỘNG" đã có sẵn, chỉ thiếu chiều "TỰ SOI".
- medic probe `coverage` đã chứng 18/18 **rule** có bite-test (harness-doctor `build_rN`) — mô hình proof-per-capability đã tồn tại cho rule; đề xuất này mở rộng đúng mô hình đó sang **skill + script**.
- `skill-health.py` — đo HÌNH DẠNG skill (dài, negation, sprawl), không đo sống/chết; không dẫm.
- [[adapt-modes]] + tiền lệ absorb 170726: mọi absorb phải kèm đường runtime — capproof là bản tất định hoá của bài học đó.

## Global constraints

- **ADR-005:** `build-capabilities.py` travel downstream (deploy cạnh hooks, chạy với `--root`); sửa nó phải giữ tương thích downstream — downstream KHÔNG có `harness/tests/` nên proof-resolver phải fail-open thành "không đo được ở downstream", không đỏ oan.
- **Khuôn medic:** probe mới theo đúng khuôn 12 probe sẵn có trong `fdk/tools/medic.py` (tên ngắn, tags, chỉ chẩn đoán không sửa, `--ci` exit 1); medic tự báo nếu probe mới quên hàng rào.
- **Hook 0-token:** toàn bộ resolver + probe là code thuần, 0 LLM (nguyên tắc hook-0-token của overstack).
- **Ponytail:** không đẻ script mới nếu nhét được vào `build-capabilities.py` sẵn có; diff tối thiểu; ratchet baseline là MỘT file JSON.
- **R15:** cấm AI-attribution trong commit; **medic --ci xanh trước push**.

## Non-goals

- **KHÔNG chấm chất lượng** proof (test tốt hay dở) — chỉ chấm CÓ/KHÔNG có đường bằng chứng chạy được. Chất lượng là việc của review/qc-code.
- **KHÔNG ép trả nợ tồn cũ ngay** — ratchet chỉ chặn nợ MỚI và coverage TỤT; núi đỏ ngày đầu là cách giết một cái gate (bài học calibration của gstack redaction: "a gate that cries wolf gets ignored").
- **KHÔNG gác LLM-skill-behavior** (skill có "chạy đúng ý" không là việc của eval golden/trace-grader) — capproof chỉ gác TỒN TẠI của đường bằng chứng.
- **KHÔNG đổi format các mục sẵn có** của CAPABILITIES.md (agent/downstream đang parse nó).
- **KHÔNG tự dedupe / tự xoá cơ chế cũ** — TRÙNG-ỨNG-VIÊN là báo cáo cho người quyết; mỗi vụ dedupe thật là một vòng `/propose` riêng (tiền lệ `170726-gitignored-dedupe`). Máy phát hiện, người phán.

## Approaches

| Phương án | Bản chất | Tradeoff |
|---|---|---|
| **A. Proof-resolver trong build-capabilities + medic probe ratchet (chọn)** | Map tất định capability→bằng chứng lúc sinh CAPABILITIES; probe so baseline | (+) Tự cộng theo đúng chỗ đang tự cộng, 0 script mới, downstream-aware sẵn. (−) Heuristic map theo tên/marker có thể sót proof đặt tên lạ → có ô UNPROVEN oan; chữa bằng marker khai tay `proof:` trong frontmatter skill. |
| B. Registry proof khai tay (YAML riêng: capability → test) | Người khai từng dòng | (+) Chính xác tuyệt đối. (−) Chính là thứ đề bài cấm: PHẢI NHỚ cập nhật — registry sẽ mục như mọi registry tay; lớp lỗi này sinh ra từ "quên wire" thì giải pháp không được dựa vào "nhớ khai". |
| C. Chạy THẬT mọi proof mỗi lần build (không chỉ resolve đường dẫn) | Execute toàn bộ test khi sinh CAPABILITIES | (+) Bằng chứng mạnh nhất. (−) build-capabilities đang chạy trong SessionStart hook và downstream — chạy cả bộ test ở đó là phá ngân sách hook; việc CHẠY đã có chỗ riêng (medic/CI); capproof chỉ cần chứng đường dẫn tồn tại + việc chạy giao cho gate sẵn có. |

Chọn **A**: tự-cộng thật (derive từ đĩa, không nhớ gì), chi phí 0 ở runtime hook, sai sót heuristic có đường chữa tường minh (`proof:` frontmatter).

## Plan

- [ ] **T1 — Proof-resolver + cột Proof + mục UNPROVEN trong `build-capabilities.py`:** với mỗi capability, tìm bằng chứng theo thứ tự tất định: (1) frontmatter `proof:` khai tay trong SKILL.md (đường chữa heuristic-sót) → (2) rule `R<n>` → `harness-doctor build_r<n>` (tái dùng map của probe coverage) → (3) tên capability xuất hiện trong `harness/tests/*.sh|*.py` → (4) engine nó bọc có `--self-test` (skill nào wrap script nào lấy từ dòng `python3 harness/scripts/<x>.py` trong SKILL.md) → (5) golden eval nhắc tên (`wiki/sources/evals/**`) → (6) medic probe tags. Không khớp gì → UNPROVEN. CAPABILITIES.md thêm ký hiệu proof gọn cạnh mỗi dòng + mục `## UNPROVEN` cuối file liệt kê nợ kèm gợi ý "thêm proof kiểu nào rẻ nhất".
- [ ] **T2 — medic probe `capproof` (ratchet):** đọc kết quả resolver, so `harness/metrics/capproof-baseline.json`: FAIL khi (a) một capability MỚI (không có trong baseline) vào mà UNPROVEN, hoặc (b) capability đã-proven TỤT thành UNPROVEN (proof bị xoá/đổi tên). Nợ tồn trong baseline: chỉ in đếm, không đỏ. `--update-baseline` để chốt nợ có chủ ý (giống capability-stamp). Downstream: probe skip có nhãn (không có harness/tests → "không đo được", không đỏ).
- [ ] **T3 — Guard test `capproof-test.sh`:** fire-drill chính cơ chế: (a) thêm capability giả không proof → probe phải ĐỎ (nợ mới); (b) xoá proof của capability đã-proven → probe phải ĐỎ (tụt); (c) nợ tồn cũ trong baseline → probe XANH (ratchet đúng chiều); (d) sandbox không đụng baseline thật. Nối vào CI framework + medic tự báo nếu probe quên hàng rào.
- [ ] **T4 — Giải-cũ-còn-sống + ứng-viên-trùng (chiều ngược của map):** (a) mỗi mục trong `harness/mechanisms.yaml` đi qua CÙNG resolver của T1 — `live_probe` nâng từ "path tồn tại" lên "có đường bằng chứng chạy được"; cơ-chế cũ mất bằng chứng hiện trong cùng mục UNPROVEN (không đẻ report riêng); (b) đảo chiều bản đồ proof→capability: một proof artifact bị ≥2 capability/cơ-chế cùng trỏ, HOẶC hai mục có desc/tên trùng token cao (n-gram overlap, ngưỡng tất định) → ghi vào mục `## TRÙNG-ỨNG-VIÊN` của CAPABILITIES.md — **chỉ báo, không tự dedupe**; dedupe đi vòng `/propose` riêng theo tiền lệ `170726-gitignored-dedupe`. Ca thử số 1 phải bắt được: hai sổ unknown song song.

## Requirements (FR)

- **FR-001**: Mỗi capability trong CAPABILITIES.md PHẢI mang trạng thái proof (proven-kèm-đường-dẫn hoặc UNPROVEN) sinh tất định từ đĩa, 0 LLM.
- **FR-002**: SKILL.md PHẢI khai được `proof:` trong frontmatter để chỉ định bằng chứng khi heuristic không tìm ra.
- **FR-003**: medic probe `capproof` PHẢI đỏ khi capability MỚI vào không có proof, đỏ khi capability đã-proven tụt thành UNPROVEN, và KHÔNG đỏ vì nợ tồn cũ đã chốt trong baseline.
- **FR-004**: Ở downstream (không có `harness/tests/`), resolver PHẢI degrade có nhãn ("không đo được ở downstream"), không báo đỏ oan.
- **FR-005**: Cơ chế PHẢI có fire-drill riêng (guard test) chứng nó còn cắn cả hai chiều đỏ/xanh.
- **FR-006**: Mọi cơ-chế trong `mechanisms.yaml` PHẢI đi qua cùng resolver — `live_probe` được nâng từ "path tồn tại" lên "có đường bằng chứng chạy được"; cơ-chế mất bằng chứng hiện trong mục UNPROVEN chung.
- **FR-007**: Bản đồ proof PHẢI đảo chiều được: proof bị ≥2 mục cùng trỏ hoặc desc trùng token cao → mục `## TRÙNG-ỨNG-VIÊN` (chỉ báo, không tự dedupe); ca hai-sổ-unknown PHẢI bị bắt trong lần chạy đầu.

## Success criteria (SC)

- **SC-001**: Người mở CAPABILITIES.md trả lời được "năng lực X có bằng chứng còn sống không, bằng chứng nằm đâu" trong dưới 30 giây — không phải đi hỏi ai.
- **SC-002**: Người thêm một skill/tool mới mà quên kèm cổng gác BIẾT NGAY trong lần chạy medic/CI đầu tiên — lớp lỗi "delta mồ côi" không thể lặp lần thứ 4 mà không ai thấy.
- **SC-003**: Đội không bị chôn dưới núi đỏ ngày bật gate: nợ tồn cũ hiển thị như con số theo dõi được, chỉ nợ mới chặn — gate giữ được uy tín thay vì bị tắt.
- **SC-004**: Sáu tháng sau, nhìn đường giảm của con số UNPROVEN trong baseline biết được framework đang trả nợ hay đang tích nợ.
- **SC-005**: Người bảo trì mở CAPABILITIES.md thấy được "cách giải cũ nào đã chết hoặc bị cái mới trùng đè" mà không phải tự nhớ lịch sử framework — mục TRÙNG-ỨNG-VIÊN nêu thẳng cặp nghi trùng để đưa ra quyết định dedupe/giữ.

## Assumptions

- **A-1** `(default)`: thứ tự heuristic proof-resolver như T1 (6 tầng, khai-tay thắng suy-diễn) — đủ cho ≥80% capability hiện có; phần sót có đường `proof:` chữa, không cần hoàn hảo ngày đầu.
- **A-2** `(default)`: ratchet đặt ở medic probe (chạy cả local + CI qua `medic --ci`) thay vì thêm job CI riêng — theo khuôn "medic là tuyến phòng thủ cuối" sẵn có.
- **A-3** `(default)`: baseline chốt nợ tồn tại thời điểm bật gate; trả nợ tồn cũ là các vòng riêng sau (mỗi lần trả chạy `--update-baseline` ghi vết).
- **A-4** `(default)`: "capability" đợt này = skill (90) + rule (18) + script/tool trong `harness/scripts/` + `fdk/tools/` + cơ-chế trong `mechanisms.yaml` (~20); KHÔNG gồm pattern/persona/wiki-page (chúng là nội dung, không phải năng lực chạy được).
- **A-5** `(default)`: heuristic trùng = (cùng proof artifact) HOẶC (desc n-gram overlap vượt ngưỡng tất định, chốt ở PLAN sau khi đo thử trên dữ liệu thật) — cả hai chỉ sinh ỨNG VIÊN, ngưỡng chỉnh được, false-positive chấp nhận được vì đầu ra là report người đọc, không phải gate chặn.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 proof-resolver + CAPABILITIES | Claude Code | Sửa engine dùng chung travel downstream (ADR-005) — cần phán đoán tương thích | done |
| T2 medic probe capproof | Claude Code | Đụng tuyến phòng thủ cuối, khuôn probe + ratchet logic | done |
| T3 guard test fire-drill | Claude Code | Test canh chính cơ chế gác — sai một chiều là gate nói dối | done |
| T4 giải-cũ + trùng-ứng-viên | Claude Code | Đảo chiều map + nâng narrative probe — đụng manifest cơ-chế dùng chung | done |

Cả 3 về Claude: engine dùng chung + gate logic, không có phần boilerplate độc lập đáng đẩy CLI rẻ. Render HTML: Claude render trực tiếp (standalone, ADR-003 cho phép).

**Sequence diagram:** [180726-capability-proof-map-seq.html](../../../html/180726-capability-proof-map-seq.html)

## Render brief

- **T1** · steps: [legacy] build-capabilities sinh list từ đĩa (tự cộng sẵn có) → [add] resolver 6 tầng tìm proof mỗi capability → [add] cột proof + mục UNPROVEN → [block] không chấm chất lượng test, không chạy test lúc build.
- **T2** · steps: [legacy] medic 12 probe → [add] probe capproof đọc resolver, so baseline ratchet → [add] đỏ khi nợ MỚI hoặc TỤT; nợ cũ chỉ đếm → [block] downstream skip có nhãn, không đỏ oan.
- **T3** · steps: [add] sandbox capability giả không proof → probe đỏ → [add] xoá proof item đã-proven → probe đỏ → [add] nợ cũ trong baseline → probe xanh → [block] không đụng baseline thật của repo.
- **T4** · steps: [legacy] mechanisms.yaml + narrative probe (path-tồn-tại) → [add] live_probe qua cùng resolver, cơ-chế mất bằng chứng vào UNPROVEN chung → [add] đảo chiều map + n-gram desc → mục TRÙNG-ỨNG-VIÊN, ca thử = hai sổ unknown → [block] chỉ báo, không tự dedupe.

## Self-review

1. **Phủ yêu cầu:** "tự soi" → T1 (trạng thái proof) + T2 (gate); "tự cộng" → T1 nằm trong build-capabilities vốn derive từ đĩa; "scale tới giai đoạn hiện tại" → A-4 phủ 90 skill + 18 rule + scripts, ratchet cho nợ tồn; "giải cũ còn hoạt động không / có duplicate không" (bổ sung tại gate 18/07) → T4 (FR-006/FR-007). Đủ, không yêu cầu nào rơi.
2. **Quét placeholder:** không còn token trì hoãn; mọi heuristic nêu đủ 6 tầng cụ thể.
3. **Nhất quán tên:** probe tên `capproof` thống nhất T2/T3/FR-003; baseline `harness/metrics/capproof-baseline.json` thống nhất T2/A-3; frontmatter key `proof:` thống nhất T1/FR-002/A-1.

## Notes

- Invoked via: `/propose` (yêu cầu user 2026-07-18: "checklist năng lực kiểm tra tự soi được và tự cộng lên, scale như giai đoạn bây giờ").

## Origin

- **Draft:** `wiki/sources/draft/180726-capability-proof-map.md`
- **Nguồn quyết định:** 3 ca `missing-verification` trong flywheel ledger (17-18/07) + recon `build-capabilities.py`/`skill-health.py`/`medic --list` trong phiên.
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
