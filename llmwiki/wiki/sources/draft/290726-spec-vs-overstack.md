---
type: draft
title: 290726-spec-vs-overstack
status: proposed
tags: [docs-site-macos, gap-analysis, output-report]
timestamp: 2026-07-29
---

# 290726-spec-vs-overstack

**Status:** proposed

## What

Đối chiếu overstack (hệ hiện tại, commit `9032ae4`) với `graph-engineering-implementation-spec.md` v0.1 (306 dòng, user cung cấp trong `~/Downloads/`), rồi sinh trang HTML so sánh `llmwiki/html/290726-spec-vs-overstack.html`.

Đối chiếu 67 mục trên tám trục: 5 mặt phẳng kiến trúc · 9 loại node · 11 loại cạnh · 4 bất biến ghi · 7 cấu phần §4 · 13 hạng mục budget/rails · 10 hạng mục eval · 8 điều kiện nghiệm thu §10.

## Kết quả đối chiếu

| Phán quyết | Số mục | Tỷ lệ |
|---|---:|---:|
| ✅ Có đủ | 15 | 22% |
| 🟡 Một phần | 36 | 54% |
| 🔴 Thiếu hẳn | 15 | 22% |
| ◆ Khác thiết kế (cố ý) | 1 | 1% |

**Kết luận chính:** spec mô tả một *platform* (FastAPI, Postgres, S3, Docker worker, service commit-DAG); overstack là một *lớp khung không hạ tầng* (git, file markdown, hook vendor, Python thuần, cài bằng một dòng curl). Hai hệ theo đuổi cùng bất biến truy vết của spec §1.4 nhưng dựng trên hai nền khác nhau — nên phần lớn nhóm "một phần" là *chọn nền khác*, không phải *làm dở*.

**15 chỗ thiếu quy về ba nguyên nhân gốc:**

1. **Không có ratchet theo điểm số** (§4.1). `harness/scripts/loop-runner.py` có đủ guard tất định (`max_iter`, `budget_seconds`, `no_progress_k` bằng state-hash, `escalate_after_iter`) và có reflexion, nhưng VERIFY là exit-code pass/fail chứ không phải metric cải thiện; `grep 'git reset'` trong file này ra **0** kết quả — không có revert, không có bản ghi `Trial{commit, score, status}`. Vòng lặp *dừng đúng lúc* nhưng chưa *giữ cái tốt hơn và vứt cái tệ hơn*.
2. **Cạnh đồ thị vô danh, không có edge ID** (§4.5). `[[wikilink]]` chiếm đa số cạnh và không mang type — kéo theo 5/11 loại cạnh của spec là thiếu, node `Claim` không tồn tại, và mắt xích thứ năm của bài nghiệm thu §10 (trích dẫn đường đi kèm edge ID) không đạt.
3. **Không có dịch vụ commit-DAG** (§4.6). Có `provenance-log.py` (hash-chain theo `writer_id`, git-tracked, `merge=union`) và git, nhưng không có `children / leaves / lineage / diff`, và quan trọng hơn: không giữ nhiều lineage thí nghiệm sống song song — overstack vẫn làm việc tuyến tính trên nhánh `orca`.

**Mặt overstack mạnh hơn spec** (bảy điều spec không nhắc tới, phần lớn sinh từ trả giá thật): chặn TRƯỚC hành động ở PreToolUse với 0 token · fire-drill `medic.py` chứng minh luật *còn* cắn · nguyên tắc "tồn tại ≠ dùng được" trong `dep-health.py` · chống drift ba bản của một skill · docs sinh từ đĩa kèm `capproof` đòi bằng chứng cho từng năng lực quảng cáo · `claim-receipts.py` chặn ảo giác trích dẫn trước commit · hạ tầng bằng không.

## Output

- `llmwiki/html/290726-spec-vs-overstack.html` — 94 KB, 7 section, self-contained (0 request ngoài), có hai sơ đồ SVG kéo-thả và master-detail cho 7 cấu phần §4
- `.orca-onboard/tmp/build_spec_compare.py` — generator, tái dùng design shell của `build_source_map.py`

## Files
| File | Action |
|------|--------|
| `llmwiki/html/290726-spec-vs-overstack.html` | created |
| `llmwiki/html/290726-pdf-gap-overstack.html` | created — trang riêng cho đối chiếu PDF gốc (4 gốc thiếu, TABLE I/VI, world model, build path) |
| `.orca-onboard/tmp/build_spec_compare.py` | created |
| `.orca-onboard/tmp/build_pdf_gap.py` | created |
| `.orca-onboard/tmp/build_source_map.py` | modified — bọc phần ghi file vào `main()` + guard `__name__` để import lại được mà không có side-effect |
| `llmwiki/wiki/index.md` | modified |
| `llmwiki/wiki/log.md` | modified |

## Việc nên làm (xếp theo giá trị trên công)

**P1 — rẻ, mở khoá nhiều thứ**
1. Edge ID ổn định cho `wiki-graph.py` / `build-wiki-graph.py`, và bắt câu trả lời trích edge ID → mở khoá mắt xích 5 của §10.
2. Thêm type cho cạnh wiki (supports / contradicts / supersedes / depends-on) — thay đổi rẻ nhất, tác động lớn nhất.
3. Ratchet theo điểm số cho `loop-runner.py`: nhận metric + chiều, revert bằng `git reset`, ghi `Trial`.

**P2 — vừa sức**
4. Bốn hạn mức còn thiếu vào `token-budget.py`: model calls, sub-agents, concurrent workers, graph writes.
5. Hợp đồng review có schema — reviewer phải trả `{criterion_id, location, defect, severity}`, "nhìn ổn" thành không hợp lệ (`/qc-code`, `council.py`).
6. Soft-delete cho trang wiki; plan JSON + validator DAG song song với PLAN.md trong `spec-gate.py`.

**P3 — cân nhắc, có thể ĐỪNG**
7. Commit-DAG hub: chỉ đáng làm nếu thật sự cần giữ nhiều lineage sống song song — hiện chưa thấy đau.
8. Pipeline extraction/resolution bằng LLM: chính spec §8 khuyên **đừng** xây KG khi quan hệ cố định và đơn giản. Đồ thị wikilink 0-token có thể đã là điểm dừng đúng.

## Rủi ro spec nêu mà overstack chưa phòng bị

- Lỗi tương quan giữa worker song song — spec bắt sóng kiểm chứng phải khác prompt/bằng chứng/vai; overstack dispatch nhiều agent nhưng không ép điều này.
- Phân mảnh làm hỏng việc cần mạch liền (kiến trúc, refactor xoắn nhau) — chưa có luật cấm fan-out loại này.
- Nổ chi phí swarm — `token-budget.py` mới cap theo session, chưa cap theo swarm.

## Notes

- Invoked via: `/docs-site-macos`, nối tiếp phiên `/orca-onboard`
- Mọi tên file trên trang đã đọc thật trên đĩa (`harness/scripts/`, `fdk/tools/`, `harness/policy.yaml`, `harness/metrics/`) — không suy đoán từ tên
- Phán quyết `🔴` cho §4.1 revert dựa trên bằng chứng đếm được: `grep -nE 'git reset|revert|score|Trial' harness/scripts/loop-runner.py` trả về rỗng
- Kiểm chứng render: mở thật trong Chrome, console sạch, 0 request ngoài, master-detail và sơ đồ kéo-thả chạy
- Sửa một lỗi trong lúc làm: tiêu đề block trong master-detail bị `html.escape()` nên thẻ `<code>` hiện literal — bỏ escape cho phần header do chính generator soạn
- `llmwiki/html/*.html` bị gitignore; `git add -f` nếu muốn commit
- Xem tại `http://localhost:8766/llmwiki/html/290726-spec-vs-overstack.html`

## Đối chiếu bổ sung với PDF gốc (2026-07-29, cùng ngày)

Đọc thêm `~/Downloads/Graph-Engineering-Athropic-Karpathy-Loop.pdf` (11 trang) — tài liệu GỐC mà spec md derive ra. ~80% trùng; **không lật kết luận nào ở trên**. Phần PDF có mà spec md lược bỏ lộ thêm:

**Gốc thiếu thứ 4 — graph chưa tham gia runtime.** TABLE I của PDF gán graph một vai trò trong TỪNG workflow pattern lúc chạy: gate signal (Prompt Chaining), classifier input (Routing), shared surface (Parallelization), shared memory (Orch-Workers), grounding layer (Eval-Optimizer). overstack có graph nhưng chỉ để xem/lint/vẽ — không workflow nào đọc-ghi nó lúc chạy. DOCS-graph, chưa phải RUNTIME-graph.

**Hai món rẻ ăn ngay (PDF cho luôn format):**
1. Grounding feedback có cấu trúc: evaluator trả `{decision, claim, reason, required_evidence[]}` thay vì văn xuôi — cụ thể hoá mục P2 "review schema" ở trên.
2. Message board cho giả thuyết đã bỏ (§III.E "failed experiment still contains useful evidence") — `failure-flywheel` gom lớp lỗi ở tầng meta rồi, nhưng agent không đọc được giả thuyết đã bỏ của agent khác lúc chạy.

**TABLE VI Production Checklist (10 hàng):** ✅ objective, provenance (R2 mạnh hơn PDF — chặn lúc Write), monitoring · 🟡 metric, reversibility, budget, recovery · 🔴 tool schema typed, artifact contract · — resolution policy (không áp).

**"Persistent world model" (§V) — mặt overstack mạnh nhất theo PDF, 7/9 tick:** problem-tree R17, orca-handover, /ingest, ADR + decision-anchoring liveness, provenance-log hash-chain, AGENT↔CLAUDE parity, recovery 🟡, contradiction tracking 🟡 (thủ công qua /lint), temporal facts 🔴 (wiki không có valid-time).

**14-step default (Appendix):** thiếu đúng các bước graph — 2, 3, 7, 8, 13.

**Vị trí trên build path TABLE II:** ~Week 2 (multi-agent) + mảnh Month 1 (persistence qua wiki); chưa đạt exit Month 1 "cross-session queries answered with cited edges" vì thiếu edge ID.

**PDF tự phanh (§VIII.C, TABLE IV, §IX.E):** đừng dựng KG khi quan hệ cố định/đơn giản; việc mạch liền giảm chất lượng khi fan-out — overstack đang tuân thủ hai cảnh báo này một cách vô tình, củng cố phán quyết P3 "có thể ĐỪNG" ở trên.

## Origin
- **Spec nguồn:** `~/Downloads/graph-engineering-implementation-spec.md` v0.1 (draft, 306 dòng), do user cung cấp
- **PDF gốc:** `~/Downloads/Graph-Engineering-Athropic-Karpathy-Loop.pdf` (11 trang, independently compiled July 2026)
- **Hệ đối chiếu:** overstack tại commit `9032ae42fbe1e74115bf852decd12c6ca57d467e`, nhánh `orca`
- **Draft:** `wiki/sources/draft/290726-spec-vs-overstack.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
