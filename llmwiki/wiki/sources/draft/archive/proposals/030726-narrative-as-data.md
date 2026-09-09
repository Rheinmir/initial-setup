---
type: draft
title: "narrative-as-data + medic narrative-drift probe (council-025)"
status: implemented  # ship v1.0.6 (narrative-as-data + code-state)
tags: [overstack-docs, narrative-drift, medic, anti-drift, council-025]
timestamp: 2026-07-03
task: T-260703-04
relations:
  - {rel: derives-from, to: council-report-025}
  - {rel: touches, path: fdk/tools/build-overstack-docs.py}
  - {rel: touches, path: fdk/tools/medic.py}
  - {rel: implements, to: ADR-001-policy-as-source-of-truth}
---

# 030726-narrative-as-data — biến narrative overstack thành DATA + medic gác drift

**Type:** draft · **Status:** implemented (ship v1.0.6) · **Proposed:** 2026-07-03 · **Task:** T-260703-04

## What
Đóng lỗ hổng council-025 phát hiện: `overstack.html` **tự-render đúng nhưng chưa tự-đúng** — số liệu (DATA) sinh từ đĩa nên khớp, nhưng phần **narrative** (list `MECHANISMS` + tab "Tự bảo trì") là **prose viết tay** đóng băng, drift âm thầm mà `medic docs-probe` (chỉ so `html == generator-output`) không bao giờ bắt được. Giải: rút narrative cơ-chế-phòng-thủ khỏi prose tay → **derive từ một manifest máy-đọc**; thêm **medic probe `narrative`** cắn khi cơ-chế phòng-thủ LIVE vắng khỏi trang (bắt sớm y như R7-f).

## Context (force-query — wiki đã đọc trước khi draft)
- **`ADR-001-policy-as-source-of-truth`** — nguyên tắc *một nguồn chân lý, derive-không-duplicate*. `MECHANISMS` hardcode trong `build-overstack-docs.py` **vi phạm trực tiếp**: nó là bản CHÉP TAY của trạng thái hệ, không phải suy ra từ nguồn. Đây là gốc-rễ của drift.
- **[fdk](../../../../skills/fdk/SKILL.md)** (concept, mục Rules) — "**Đếm số luôn LIVE; không hardcode (anti-drift)**". Số đếm skill/rule đã tuân (generator đếm đĩa); nhưng *danh sách cơ-chế* thì chưa — cùng một luật, chưa áp cho narrative.
- **[[feature-catalog]]** — concept "vì sao" mà overstack.html render; là ứng viên nguồn narrative nhưng hiện không có tầng máy-đọc cho *defense-line*.
- **council-report-025-seed42.html** — verdict: consensus Taleb+Munger (iatrogenics: tài liệu sai mang nhãn "đáng tin" nguy hiểm hơn không có; medic kiểm *tính trung thành bản sao*, không kiểm *tính trung thực bản gốc*). Đòn bẩy hội tụ: **narrative → DATA + probe cắn**. Aurelius (ranh giới): phần *ý-nghĩa/giọng-văn* CHẤP NHẬN cần người — đừng hứa tự-động cái không tự-động được; tối thiểu **đổi nhãn** "sinh từ đĩa nên luôn khớp".
- Tiền lệ [[030726-milestone-v106-harden]] **T3 generator-only probe** — proposal này là hiện-thực-hoá + mở rộng T3 (từ "artifact khác generator" sang "narrative thiếu cơ-chế LIVE").
- Bằng chứng cấp thiết (đo phiên này): `MECHANISMS` list thiếu **medic**, **gương-soi T2**, **bộ nhớ thứ cấp** — 3 tuyến phòng thủ lớn nhất phiên này; tab "Tự bảo trì" vẫn chỉ kể `/harness-update` + `/health-check`.
- **council-advisory 030726 (mở rộng self-narration)** — roster Rams·Taleb·Feynman: "overstack tự tường thuật TRẠNG THÁI CODE" **NÊN** làm (là VIEW ghép state máy-đọc sẵn có, không phải prose tay mới) NHƯNG buộc **hợp đồng cứng** — xem mục "Tự tường thuật" dưới. Đây là lý do sinh **T5**.

## Tự tường thuật (self-narration) — nguyên tắc chung + mở rộng code-state
Tính năng cốt lõi proposal này KHÔNG chỉ là "sửa list cơ-chế" mà là một **cơ chế tổng quát**: *overstack tự tường thuật về chính nó, và mỗi mệnh đề tường thuật cột vào một live-probe*. Manifest cơ-chế (T1-T4) là **ứng dụng đầu tiên**; **T5** áp cùng máy móc cho *trạng thái code hiện thời*. Hợp đồng cứng (council-advisory, bất khả thương lượng):
1. **Một câu = một probe = một dòng code truy được.** Không probe → không câu (Taleb: cấm "prose mồ côi").
2. **Hai lớp tách vật lý** (Feynman): **FACT** (có badge nguồn + lệnh sinh + timestamp, tái tạo byte-cho-byte) vs **OPINION** (diễn giải người, dán nhãn rõ, không trộn màu).
3. **Mặc định ĐỎ/UNKNOWN, không xanh-mặc-định** (Taleb via-negativa): im lặng/đỏ khi không đo được, đừng suy diễn lành.
4. **Chỉ FACT nhị-phân/đếm-được từ nguồn máy-đọc** (Rams): medic verdict, số symbol/module/edge (code-graph), file chạm gần nhất (ledger+events), git HEAD/branch/dirty, coverage/test NẾU có runner thật. **CẤM** câu suy-luận "code sạch/tốt/ổn định" ở tầng FACT — đó là opinion. Dòng-chảy trôi (list symbol dài, git diff thô, memory-map) là **tra cứu**, không trưng bày.
5. **Reproducibility-probe** (Feynman) + **staleness-probe** (Taleb): render 2 lần → diff tầng FACT phải byte-identical (khác = fail); FACT cũ hơn git HEAD → tự bôi đỏ.

## Impact — file/hành vi bị chạm
| Vùng | Ảnh hưởng |
|------|-----------|
| `harness/mechanisms.yaml` (MỚI) | manifest máy-đọc: mọi cơ-chế/tuyến-phòng-thủ overstack có ở đây (nguồn chân lý) |
| `fdk/tools/build-overstack-docs.py` | `MECHANISMS` (hằng-số tay, ~12 dòng) + tab `maintain` **derive từ manifest**; bỏ prose-list cứng |
| `fdk/tools/medic.py` | thêm probe `narrative` (3 tầng: có-mặt-trên-trang · LIVE-tồn-tại · canary skill-phòng-thủ-vắng-manifest) |
| `llmwiki/html/overstack.html` | regen: list cơ-chế + tab Tự-bảo-trì đầy đủ (medic/gương-soi/bộ-nhớ); nhãn "sinh từ đĩa" đổi cho trung thực |
| medic coverage/probe count | +1 probe; docs-probe cũ (render-khớp) GIỮ nguyên — probe mới bổ sung, không thay |

## Điều CÓ THỂ vỡ (side-effect)
- **Regen overstack.html thay đổi nội dung** → nếu manifest thiếu một mục cũ, mục đó biến mất khỏi trang. Chống: T1 backfill ĐỦ 12 cơ-chế cũ + 3 mới, so số dòng trước/sau.
- **medic probe mới quá gắt** → mọi phiên chưa regen sẽ FAIL. Chống: probe chỉ FAIL khi manifest-entry LIVE mà **vắng trang** (drift thật); đổi giọng/thứ tự prose KHÔNG kích hoạt.
- **Manifest thành nguồn drift MỚI** (ai đó thêm tuyến phòng thủ mà quên ghi manifest) → tầng canary (warn) quét skill mô-tả "gác/health/phòng thủ/drift/self-heal" mà vắng manifest, biến im-lặng thành tiếng-ồn (Taleb).

## Manifest — nguồn chân lý ở đâu? (tradeoff, không tự chọn thầm)
- **(A) `harness/mechanisms.yaml` tập trung** _(đề xuất)_ — một file liệt kê mọi cơ-chế: `{id, name, kind: rule|hook|skill|tool, desc, live_probe: path/skill-name}`. Ưu: một nguồn, đúng ADR-001, dễ probe cả 2 chiều. Nhược: một nơi phải nhớ cập nhật (nhưng canary đỡ).
- **(B) frontmatter `defense-line:` rải trong SKILL.md + yaml cho hook** — Ưu: co-locate với skill. Nhược: cơ-chế phi-skill (hook/rule) vẫn cần yaml → **hai** nguồn; probe phức tạp hơn. → chọn (A) cho gọn + đúng nguyên tắc một-nguồn.

## Plan
- [x] **T1 — `harness/mechanisms.yaml`.** Manifest máy-đọc mọi tuyến phòng thủ/cơ-chế runtime: 12 mục cũ (orientation, auto-index, force-query, code-index, code-logger, health-check, wiki→fdk, harness-lint, harness-doctor, fdk-gate, harness-local, docs-gate) + **3 mục mới** (medic, gương-soi-T2, bộ-nhớ-thứ-cấp). Mỗi mục có `live_probe` (đường dẫn file / tên skill) để verify tồn-tại-thật.
- [x] **T2 — build-overstack-docs.py derive từ manifest.** `MECHANISMS` + nội dung tab `maintain` đọc `mechanisms.yaml` thay hằng-số tay. Giữ nguyên phần *ý-nghĩa* (giọng/ẩn-dụ) là prose người-viết NHƯNG danh-sách-năng-lực thì derive. Đổi nhãn "sinh từ đĩa nên luôn khớp" → "số liệu khớp đĩa · danh sách cơ-chế gác bằng probe narrative".
- [x] **T3 — medic probe `narrative`.** 3 tầng: (a) **fail** nếu một entry manifest LIVE (live_probe tồn tại) mà **vắng** trong `overstack.html`; (b) **fail** nếu entry manifest có `live_probe` **không tồn tại** (manifest nói dối); (c) **warn** canary: skill có mô-tả chứa "gác/health/phòng-thủ/drift/self-heal/gương" mà **vắng** manifest. Đăng ký vào PROBES + coverage.
- [x] **T4 — regen + nhãn trung thực + backfill trang.** Chạy build-overstack-docs → overstack.html có đủ medic/gương-soi/bộ-nhớ; khối prose *chỉ-người-viết* (không auto-verify) gắn chú thích rõ; verify medic `narrative` xanh + `--ci` xanh.
- [x] **T5 — code-state self-narration (Phase 2, hợp đồng cứng council-advisory).** Một section MỚI trong overstack.html "Trạng thái hiện thời" tường thuật **chỉ FACT probe-được**: medic verdict (probe nào cắn), số symbol/module/edge từ code-graph, N file chạm gần nhất (ledger+events), git HEAD/branch/dirty, coverage NẾU có. Mỗi dòng có **badge nguồn + lệnh sinh** (lớp FACT); tách khỏi lớp OPINION (dán nhãn). Thêm **reproducibility-probe** (render 2 lần diff FACT byte-identical) + **staleness-probe** (FACT cũ hơn git HEAD → đỏ) vào medic. Scope-cứng: KHÔNG câu "khoẻ/tốt", KHÔNG dòng-chảy trôi.

## Success (kiểm chứng được)
1. `overstack.html` tab "Tự bảo trì" + list cơ-chế **liệt kê medic, gương-soi T2, bộ-nhớ-thứ-cấp** (grep thấy).
2. Xoá thử 1 dòng cơ-chế khỏi trang (hoặc thêm mục manifest LIVE mới) → `medic narrative` **FAIL** (drift bị bắt sớm, không phải ở commit-gate).
3. Đặt `live_probe` sai (trỏ file không tồn tại) → probe FAIL "manifest nói dối" — manifest tự-gác, không thành drift-surface mới.
4. Nhãn "sinh từ đĩa nên luôn khớp" đã đổi; không còn hứa tự-động-hoá phần cần người.
5. `medic --ci` xanh, docs-probe cũ vẫn xanh, coverage không tụt.
6. **(T5)** section "Trạng thái hiện thời": mỗi dòng FACT có badge nguồn + lệnh; render 2 lần diff FACT byte-identical; sửa 1 file rồi không regen → staleness-probe đỏ; KHÔNG có câu "khoẻ/tốt" ở lớp FACT.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| T1 manifest mechanisms.yaml | Claude | thiết kế schema + backfill chính xác 15 cơ-chế, hiểu ngữ nghĩa từng tuyến | pending |
| T2 generator derive | Claude | sửa generator dùng-chung (impact overstack), tách derive vs prose-người | pending |
| T3 medic probe narrative | Claude | logic 3 tầng + canary heuristic = reasoning-heavy, gần code medic | pending |
| T4 regen + nhãn + verify | Claude | phán đoán nhãn trung thực + đối chiếu trước/sau, chạy gate | pending |
| T5 code-state self-narration | Claude | ghép nhiều nguồn máy-đọc + probe reproducibility/staleness, phân lớp FACT/OPINION = reasoning-heavy | pending |

_(Tất cả Claude: chuỗi việc framework reasoning-heavy, chạm generator + medic dùng-chung, không tách rời an toàn cho CLI rẻ; HTML proposal này Claude render trực tiếp.)_

**Sequence diagram:** [030726-narrative-as-data-seq.html](../../../html/030726-narrative-as-data-seq.html)

## Origin
- **Draft:** `wiki/sources/draft/030726-narrative-as-data.md`
- **Commit:** _(verify-before-commit điền)_
- **Date promoted:** _(verify-before-commit điền)_
