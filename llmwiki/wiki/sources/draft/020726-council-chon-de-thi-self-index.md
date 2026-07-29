---
type: draft
title: "020726-council-chọn-đề-thi — dựng app mẫu ngoài mẫu + harass test 8 loại vector, để council tự chọn đề thi (chống ludic fallacy)"
status: superseded  # T-260702-02 superseded — phần còn lại là GH#81
tags: [council, self-index, wiki-core, relations, eval, harass, dogfood, output-report]
timestamp: 2026-07-02
relations:
  - {rel: derives-from, to: 020726-wiki-core-relations}
  - {rel: derives-from, to: 010726-query-retrieval-eval}
  - {rel: touches, path: fdk/tools/build-wiki-graph.py}
  - {rel: touches, path: fdk/tools/wiki-relations.py}
  - {rel: touches, path: harness/scripts/retrieval-eval.py}
  - {rel: touches, path: harness/scripts/council.py}
---

# 020726-council-chọn-đề-thi — app mẫu ngoài mẫu + harass 8 loại vector

**Type:** draft
**Status:** superseded (→ GH#81)
**Tags:** council, self-index, wiki-core, relations, eval, harass, output-report
**Proposed:** 2026-07-02
**Task:** T-260702-02

## What
Dựng một **app mẫu MỚI, ngoài mẫu** (không phải wiki của chính framework), onboard nó, rồi **harass/stress test** để kiểm chứng framework **tự áp dụng đúng cả 8 loại vector quan hệ** trong hệ tự-hành của wiki — với điểm mới cốt lõi: **để COUNCIL tự chọn đề thi** (chọn app mẫu + bộ harass), thay vì người tự chọn.

## Context (force-query)
Query wiki trước khi draft (R7-f). Các neo liên quan:

- **[[wiki-core-relations]]** (`concepts/wiki-core-relations.md`, shipped 2026-07-02) — wiki đã lên "lõi tri thức có quan hệ": schema quan hệ có kiểu, ledger flock (G1 8-process pass), stale-propagation cap=1 (G2, 9.8ms/ghi), `/wiki-room` (G3), và render `wiki-graph-{fdk,llmwiki}.html` (13ms). **Đây chính là "hệ tự-hành" cần test.** Engine (`fdk/tools/build-wiki-graph.py`) hiện hỗ trợ **8 loại vector**: `derives-from, depends-on, implements, supersedes, touches, contradicts, imports, wikilink`.
- **[[010726-query-retrieval-eval]]** (`draft/orca/010726-query-retrieval-eval.md`, promoted) — đã có khung eval **truy-hồi bằng số** (recall@k + token, baseline-diff) và scorer `harness/scripts/retrieval-eval.py`. Bản này **tái dùng** khung đó, mở rộng sang **relation-recall** (quan hệ đúng-kiểu có được engine tự sinh không).
- **Council seed42** (`llmwiki/html/council/council-report-008-seed42.html`) — hội đồng vừa kết luận: bộ bằng chứng robustness hiện tại **tự chọn đề thi (ludic fallacy)**, test trên chính wiki của framework, chỉ chứng minh ROBUST chứ không ANTI-FRAGILE; bằng chứng còn thiếu = **adversary/ứng viên NGOÀI MẪU**. Proposal này là câu trả lời trực tiếp cho lời phê đó.

**Vì sao "council chọn đề thi":** nếu người dựng app + chọn harass thì lại rơi vào đúng cái bẫy council chê (đề thi do người ra, hệ chỉ mạnh trước cú người đã tưởng tượng nổi). Cho council (nhiều persona đối-trọng, blind peer-rank) chọn app mẫu + bộ harass → đề thi **không do một người chọn**, sát tinh thần adversary bên-thứ-ba.

## Impact — file/hành vi có thể ảnh hưởng
| Vùng | Ảnh hưởng |
|------|-----------|
| `harness/scripts/council.py` | dùng lại (không sửa engine) — chạy 1 council mới để chọn đề thi |
| `harness/scripts/retrieval-eval.py` | **mở rộng** thêm chế độ `--relations` (relation-recall@k) — rủi ro chạm scorer hiện có |
| `fdk/tools/build-wiki-graph.py` / `wiki-relations.py` | **chỉ đọc/gọi**, không sửa — nếu harass lộ bug thì mới đụng (safe-change) |
| wiki chính (`llmwiki/wiki/`) | app mẫu onboard vào **thư mục/wiki tách riêng** (sandbox), KHÔNG trộn vào wiki framework → không nhiễm bẩn graph thật |
| Không có code sản phẩm nào khác bị đụng | app mẫu là project throwaway, cô lập |

## Plan
- [x] **T1 — Council chọn đề thi.** ✅ Đã chạy `/council` seed 42, roster case-risk 5 ghế (taleb, ilya, munger, kahneman, aurelius). Winner **seat-3/Munger** (mean 1.33). Đề thi được chốt ở mục [T1 Output](#t1-output--đề-thi-được-chốt) dưới. Report: `llmwiki/html/council/council-report-010-seed42.html`, transcript: `scratchpad/council-dethi/run/`.
- [x] **T2 — Dựng app mẫu ngoài mẫu.** ✅ `scratchpad/council-app/generate.py` (re-runnable = bản bàn giao standalone) dựng 42 file TS plugin-host, gieo đủ 10 đòn, ground-truth niêm phong (hash `854c5b2a…`/`49bea26b…`) tại `plugin-host/ground-truth/`.
- [x] **T3 — Onboard + để engine tự-index.** ✅ `adapter.py` onboard app→wiki-shape rồi gọi ENGINE THẬT (`build-wiki-graph.py` scan+enrich_code). KHÔNG gắn tay. Ra 14 node / 11 cạnh thô → `plugin-host/engine-edges.json`.
- [x] **T4 — Harass/stress test 8 loại vector.** ✅ Chấm mù bằng `score.py` (seal verified). **Kết quả thật:** core edge **P=0.889 R=0.8 F1=0.842**, hallucination 0.125, negative PASS. Chi tiết per-capability ở mục [T3/T4 Kết quả](#t3t4--kết-quả-engine-thật).
- [x] **T5 — Đo bằng số + distill.** ✅ Report HTML `llmwiki/html/030726-self-index-benchmark-report.html`; 3 defect đẩy `/failure-flywheel` (coverage-gap ×2, hallucination ×1); cập nhật concept [[wiki-core-relations]] (mục "Kiểm chứng NGOÀI-MẪU"). Scorer `plugin-host/score.py` **áp cơ chế benchmark chuẩn ngành** (từ `/last30days` 2026-07-03: ContextBench gold-context P/R/F1, Unified-KG-Benchmark hallucination/omission-rate per-triple, negative-control, held-out fixed-seed + hash-seal, LLM-judge-calibrate). Verdict gate: `F1≥0.7 AND negative=PASS AND hallucination≤0.15`. Đã kiểm chứng bằng engine-output giả (tốt→PASS 1.0; xấu-bịa-cạnh→FAIL). Còn: chạy engine THẬT (`build-wiki-graph.py`) qua adapter map→schema (T3/T4), rồi xuất report HTML + distill wiki.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 Council chọn đề thi | Claude (orchestrator + subagent seats) | Suy luận đối-trọng + blind peer-rank là việc reasoning-heavy, cần Claude | pending |
| T2 Dựng app mẫu | OpenCode (big-pickle / DeepSeek) | Scaffold code+docs cơ học theo spec đã chốt — rẻ, không cần Claude | pending |
| T3 Onboard + auto-index | Claude | Cần quan sát engine tự sinh quan hệ đúng/sai, phán đoán khi lệch | pending |
| T4 Harass 8 vector | Claude (thiết kế harass) + OpenCode (chạy ca cơ học) | Thiết kế adversary cần Claude; chạy batch ca rẻ giao OpenCode | pending |
| T5 Eval + distill | Claude | Mở rộng scorer + đối chiếu council + distill wiki = substance | pending |

**Sequence diagram:** [020726-council-chon-de-thi-seq.html](../../../html/020726-council-chon-de-thi-seq.html)

## T1 Output — Đề thi được chốt
Council (blind peer-rank, chống ludic fallacy) đã ra đề. Winner Munger (TS plugin-host), graft điểm mạnh á quân (Aurelius — pass/fail nhị phân + đòn âm tính) và hạng 3 (Kahneman — ca để-trống frontmatter đo suy-ngầm).

**App mẫu:** monorepo **TypeScript "plugin-host" ~150 file** — `packages/core/` (alias `@core/*`, DI container, barrel `index.ts`), `packages/plugins/*` (frontmatter + code, có `import(name)` động), `packages/host/`, `docs/` (có `[[wikilink]]`), `ground-truth/` **niêm phong** (engine không đọc khi chấm).

**10 đòn harass** (vector · ca đuôi · PASS/FAIL):
1. `imports` alias-vs-runtime — động phải ghi "unresolved", không bịa đích
2. `imports` barrel giả cạnh — không fan-out 12 cạnh sau barrel
3. `wikilink` treo + đồng danh — dangling flag + cảnh báo nhập nhằng
4. `derives-from` chu trình A→B→C→A — giữ 3 cạnh + cờ chu trình, không treo
5. `supersedes` rename lan truyền — cạnh đúng + `touches` lan đúng 4 file
6. `contradicts` bất đối xứng — không tự đối-xứng-hóa
7. `implements` corrupt-YAML — quarantine file lỗi, graph còn lại vẫn dựng
8. `touches` lan truyền im lặng — chạm đúng phụ thuộc trực tiếp, không bùng nổ
9. **âm tính** (chống bịa cạnh) — hai file trùng tên hàm, engine sinh ZERO cạnh
10. `depends-on` để-trống (đo GIỚI HẠN suy-ngầm — FAIL không trừ điểm lõi)

**Chấm:** recall (cạnh-đúng/cạnh-vàng) × precision (phạt bịa cạnh); đòn âm tính nhị phân; đòn để-trống chấm riêng "bảng giới hạn". **Chống ludic fallacy:** ground-truth niêm phong + băm hash TRƯỚC khi engine chạy, chấm mù bằng script.

**Lưu ý năng lực engine (bất biến):** chỉ TỰ SINH `touches/imports/wikilink`; 5 loại còn lại ĐỌC từ frontmatter → mỗi loại có ca khai-tường-minh (đo đọc-đúng = PASS chính) + tùy chọn ca để-trống (đo giới hạn).

## T3/T4 — Kết quả engine thật
Chạy `build-wiki-graph.py` (scan+enrich_code) trên app mẫu, chấm mù. **Đây là graph-BUILDER chạy đơn lẻ** — full self-index còn dùng hook auto-touches + validator rel_integrity + code-graph MCP (chưa exercise ở run này, đã ghi rõ trong `engine-edges.json._meta`).

**Số thật (subset semantic-relation):** precision 0.889 · recall 0.8 · **F1 0.842** · hallucination 0.125 · negative-control PASS.

**Chia theo năng lực (mới là bức tranh thật, verdict-gate ẩn mất):**
- ✅ **MẠNH — đọc quan hệ khai tường minh:** derives-from ×3 (đòn 4), supersedes (5), contradicts **không tự đối-xứng-hóa** (6), implements cache + **không bịa implements cho file YAML hỏng** (7), depends-on khai tường minh (10-declared). Đọc đúng 5/5 loại frontmatter.
- ❌ **MÙ code TypeScript:** `imports` chỉ parse `.py` (ast) → 0 cạnh import TS (đòn 1,2 chỉ pass phần "không bịa"). `touches` chỉ từ ledger/frontmatter → 0 (đòn 8 không có gì để chấm).
- ❌ **Thiếu cờ toàn vẹn trong graph-builder:** không cờ chu trình (đòn 4 mất 1 check), không quarantine YAML hỏng (đòn 7 mất 1 check).
- ❌ **Không strip code-fence:** trích `[[NotALink]]` từ trong khối code → 1 false-positive (đòn 3, chính là hallucination 0.125).

**Kết luận đối chiếu council seed42:** khẳng định đúng lời phê — engine **robust ở mặt nó được thiết kế** (đọc quan hệ khai báo, không bịa cạnh negative, không đối-xứng-hóa contradicts) nhưng **giòn ở đuôi ngoài-mẫu**: mù code TS, thiếu cờ toàn vẹn, lẫn link trong code-fence. Không có cái nào "mạnh lên nhờ stress" → **robust, chưa anti-fragile** — đúng như dự báo. Đây là bằng chứng NGOÀI MẪU mà council đòi.

**Nợ để T5 hoàn tất:** report HTML + đưa 3 defect (import-TS-blind, cycle/quarantine-flag, code-fence-strip) vào [[failure-flywheel]] + cập nhật [[wiki-core-relations]].

## Success (tiêu chí kiểm chứng được)
1. Council **chốt được đề thi** (app + harass set) qua transcript blind peer-rank — người KHÔNG chọn đề.
2. App mẫu onboard xong, engine **tự sinh ≥6/8 loại vector** mà không gắn tay; mỗi loại có ≥1 cạnh trong `wiki-graph`.
3. Harass đo được **relation-recall@k bằng số** + baseline, phát hiện được ≥1 ca đuôi (link treo/chu trình/rename) engine xử lý ra sao (đỏ→xanh hoặc lộ bug ghi lại).
4. Report HTML đối chiếu tường minh: kết quả ngoài-mẫu **xác nhận hay bác** lời council "chỉ robust, chưa anti-fragile".
5. Kết quả distill về wiki (concept mới hoặc cập nhật [[wiki-core-relations]]).

## Render brief (cho T2/T4 nếu dispatch cheaper CLI)
- T1: steps `[add] chạy council → [legacy] council.py math → [add] chốt đề thi vào draft`; prose: council nhiều persona blind-rank chọn app+harass, chống ludic fallacy.
- T2: steps `[add] sinh code có import chéo → [add] sinh docs/ADR → [block] cô lập sandbox không trộn wiki thật`.
- T3: steps `[legacy] onboard/reindex → [add] hook+build-wiki-graph tự sinh edges → [block] không gắn quan hệ tay`.
- T4: steps `[add] mỗi loại vector 1 assertion → [block] ca đuôi: link treo/chu trình/rename/corrupt → [add] đo recall + fail-open`.
- T5: steps `[add] retrieval-eval --relations → [add] report HTML → [legacy] đối chiếu council seed42 → [add] distill wiki`.

## Origin
- **Draft:** `wiki/sources/draft/020726-council-chon-de-thi-self-index.md`
- **Commit:** _(verify-before-commit điền)_
- **Date promoted:** _(verify-before-commit điền)_
