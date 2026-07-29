---
type: draft
title: "Query L0→L1: eval truy-hồi + telemetry + tool có-lọc (land chung, cap 30 golden)"
status: promoted
tags: [query, retrieval, eval, telemetry, wikieval, council, output-report]
proposed: 2026-07-01
id: 010726-query-retrieval-eval
---

# 010726-query-retrieval-eval

**Type:** draft · **Status:** proposed · **Proposed:** 2026-07-01

## What
Nâng hệ thống query/lưu-trữ của overstack từ **L0** (skill `query` chỉ là prose dặn model tự tìm tự đọc, không code, không đo) lên **L1** (query thành tool có-lọc thật), NHƯNG bắt đầu bằng **cảm biến**: một bộ eval truy-hồi tối thiểu + telemetry land *cùng ngày* với tool, để mọi cải tiến sau này chứng minh được bằng số. Không đi L2 (hook prefetch-inject). Quyết định thứ tự này do council 5 ghế chốt (Karpathy thắng mean-rank 1.33; transcript ở `scratchpad/council-query/run/`).

## Problem
Chẩn đoán đã xác minh bằng code (không phải phỏng đoán):

1. **`query` ở L0 — không có retrieval.** `skills/query/` chỉ có đúng 1 file `SKILL.md` (~2.5KB prose), 0 dòng code, 0 index/FTS/embedding. Skill dặn model *"Identify relevant pages. Read each relevant page in full."* — model tự Read cả trang, tiêu bằng chính context window của nó. Không có bước lọc-rồi-trả-payload nào chạy.
2. **Không có telemetry.** Gọi `orca-workflow` không ghi dòng nào xác nhận query có thực sự chạy. `user_prompt_submit.py` chỉ inject directive nhắc 3 trụ, không log việc query. Model có thể bỏ qua bước query mà không ai biết.
3. **Không có eval truy-hồi.** `wikieval` chỉ đo ĐÚNG NỘI DUNG (assert `contains:Origin` trên output nạp sẵn qua `--outputs`), KHÔNG đo TRUY HỒI (recall@k: query có tìm ra đúng trang không; token: tốn bao nhiêu). Golden cho sẵn cả `input` lẫn `expected` nên nó chấm câu-trả-lời-có-sẵn, không chạy pipeline query thật.

So sánh: engram ở **L1** — MCP tool `mem_search` chạy FTS5 SQL thật, lọc rồi trả preview 300-ký-tự, 3 tầng `search → get → timeline`. Overstack còn dưới cả engram. Nhưng KHÔNG nuốt SQLite: ràng buộc triết lý transparent + git + markdown (council trước đã loại "wholesale-thay-wiki" 3.89).

## Proposed Solution
Ba mảnh, land **chung một đợt** (kỷ luật cốt lõi — xem Risks):

### Mảnh 1 — Telemetry query (cảm biến, ~30 dòng)
Script `harness/scripts/query-log.py` ghi mỗi lần query một dòng JSONL vào `harness/metrics/query-log.jsonl`: `{ts, question, pages_hit:[slug], tokens_est, tier_reached}`. Skill `query` thêm một dòng gọi script này ở cuối. 0 dependency, 0 service, chạy local.

### Mảnh 2 — Eval truy-hồi tối thiểu (thước đo, ~100-150 dòng, cap 30 golden)
- Goldens ở `llmwiki/wiki/sources/evals/retrieval/*.md`: mỗi file frontmatter `question:` + `expected_pages: [slug1, slug2]` (**một TẬP trang chấp nhận được**, không phải một trang — chống brittle).
- Scorer `harness/scripts/retrieval-eval.py`: nhận `--outputs` (danh sách trang mà query pipeline trả về cho mỗi câu hỏi) → tính **recall@k** (có trang kỳ vọng nào trong top-k không) + tổng token, so với baseline `harness/metrics/retrieval-baseline.json`. Tái dùng khung cascade + baseline-diff của `wikieval.py` (không viết lại engine).
- **Hard-cap 30 golden**, dogfood từ câu hỏi thật trong `wiki/log.md`. Vượt 1 ngày công → ship mỏng, đừng nới.

### Mảnh 3 — Query L0→L1: tool có-lọc 3 tầng (0 dependency)
Viết lại `llmwiki/skills/wiki-loop/query.md` (canonical) + mirror thành pipeline 3 tầng, dùng đồ đã có:
- **Tầng 1 (quét, KHÔNG mở file):** `ripgrep` trên `wiki/index.md` + heading các trang → trả **danh sách slug + 1 dòng snippet**. code-graph MCP cho câu hỏi về code.
- **Tầng 2 (khoan):** chỉ `Read` full những trang được chọn ở tầng 1.
- **Tầng 3 (bối cảnh):** lần theo `[[wikilinks]]` của trang đã đọc (tương đương `timeline/related` của engram).
Đo baseline L0 **đúng 1 lần** để lấy sàn, rồi land L1 và đo lại trên cùng bộ golden.

**Loại khỏi phạm vi — L2 (hook prefetch-inject):** cả hội đồng loại. Hook chạy trước khi model suy nghĩ → phải đoán mù cần trang nào + trả thuế token mọi lượt + ép content lên model dù không hỏi (rủi ro đuôi đầu độc context, "mùi wholesale"). Không làm.

## Scope
- **In scope:** telemetry script; eval truy-hồi + ≤30 golden + baseline; viết lại `query.md` (canonical+mirror) thành 3 tầng; đo L0 sàn rồi L1.
- **Out of scope:** L2 hook inject; SQLite/FTS/embedding; đổi `wikieval` hiện có; đụng engram; >30 golden.

## Implementation Plan
Mỗi bước verify độc lập:
1. **Telemetry** — viết `query-log.py`; chạy tay 1 query giả, xác nhận 1 dòng JSONL đúng schema. *(verify: `cat query-log.jsonl`)*
2. **Golden + scorer** — tạo 20-30 golden từ `wiki/log.md`; viết `retrieval-eval.py` tái dùng khung `wikieval.py`; self-test: mỗi golden tự thoả `expected_pages` của chính nó. *(verify: `retrieval-eval.py --self-test` exit 0)*
3. **Baseline L0** — chạy pipeline L0 hiện tại trên bộ golden **1 lần**, ghi `retrieval-baseline.json` (recall@k + token sàn). *(verify: file baseline tồn tại, có số)*
4. **Query L1** — viết lại `query.md` canonical+mirror 3 tầng; chạy lại eval; so recall@k + token với baseline. *(verify: recall không giảm, token/query giảm so L0)*
5. **Chốt kỷ luật** — đảm bảo mảnh 2+4 land chung commit/đợt (không tách để tránh "đo hơi nước").

## Render brief
- **Diagram (data-driven):** thang 3 mức L0→L1→L2 (node: L0 prose·đỏ / L1 tool-lọc·xanh / L2 inject·xám-gạch-chéo-loại), cạnh mỗi mức gắn nhãn chi phí + "đo được?". Bên dưới: sơ đồ 3 tầng query (index.md+rg → Read → wikilinks) với mũi tên thu hẹp dần (progressive disclosure).
- **Prose mỗi task:** đoạn văn cho từng mảnh 1/2/3 giải thích *tại sao thứ tự này* (đo trước để chứng minh) + bảng Risk→Mitigation. Người đọc là người review kiến trúc → prose đầy đủ, không caveman.

## Risks & Mitigations
Bốn case xấu, **mỗi case có chốt chặn cụ thể** (đây là phần user hỏi "có phương án xử lý chưa" — có):

| # | Case xấu | Nguồn | Chốt chặn |
|---|----------|-------|-----------|
| 1 | **Mạ vàng eval** — 30 golden phình 300, tuần tuning threshold, không ship tool → tê liệt phân tích | Munger/Taleb | **Hard-cap 30 golden** dogfood từ câu hỏi thật; quá 1 ngày công → ship mỏng, cấm nới. Ghi thẳng cap vào scorer (từ chối >30). |
| 2 | **Đo hơi nước** — baseline đo L0 vốn không tất định (model tự Read tuỳ hứng) → recall dao động, số nhiễu, tham chiếu yếu | Linus (đúng ở đây) | Đo L0 **đúng 1 lần** lấy sàn, KHÔNG đầu tư ổn định hoá số L0; **land L1 sát ngay** (mảnh 2+4 chung đợt) — chính là lý do Karpathy thắng chứ không phải "đo trước" thuần. |
| 3 | **Telemetry nói dối** — query agentic; model bỏ skill tự Read thẳng → log hiện "không query" dù việc vẫn xảy ra → đếm hụt/quy sai | — | Chấp nhận telemetry đo **tool-usage** (đường query được-gọi), không phải mọi retrieval; ghi rõ giới hạn này trong log schema. Tuỳ chọn sau: biến query thành đường sanctioned duy nhất. |
| 4 | **Golden brittle** — recall@k so với **một** trang kỳ vọng → retrieval tốt tìm trang khác cũng đúng lại bị chấm "trượt" | — | `expected_pages` là **một TẬP** trang chấp nhận được, không phải 1. Scorer tính recall trên tập. |

**Rủi ro gốc không phải kỹ thuật mà là kỷ luật** (vượt phạm vi / đo thứ chưa tất định). Cả hai chặn bằng một luật ghi vào proposal: **eval land cùng ngày với L1, cap 30 golden.**

## Verification
- `retrieval-eval.py --self-test` exit 0 (mỗi golden thoả expected của chính nó — tất định, không model).
- Baseline L0 ghi được số recall@k + token.
- Sau L1: **recall@k không giảm** so baseline VÀ **token/query giảm** (mục tiêu chính của progressive disclosure). Nếu recall giảm → dừng, không promote.
- Telemetry: chạy 1 query thật → đúng 1 dòng JSONL hợp schema.
- `query.md` canonical và mirror byte-identical (parity check).

## Chi phí (tóm)
~1 buổi–1 ngày công, **0 dependency, 0 chi phí runtime** (eval chạy offline/CI, telemetry 1 dòng log). Cái đắt duy nhất: hoãn tool "đẹp" ~1 ngày — đã cân nhắc và chấp nhận (council chốt: đo trước để cải tiến chứng minh được).

## Origin
- **Draft:** `wiki/draft/orca/010726-query-retrieval-eval.md`
- **Nguồn quyết định:** council 5 ghế (Karpathy/Linus/Taleb/Meadows/Munger), transcript `scratchpad/council-query/run/council.transcript.md` — winner Karpathy mean-rank 1.33, dissent Linus (var 3.56, "ship tool trước").
- **Chẩn đoán:** Explore engram `/tmp/engram` (cơ chế L1 3-tầng) + xác minh code overstack (query prose, hook không inject, wikieval đo nội-dung).
- **Commit:** `632e29c` — feat(query): nâng L0→L1 có đo
- **Date promoted:** 2026-07-01 → `fdk/wiki/concepts/query-retrieval-eval.md`
```
