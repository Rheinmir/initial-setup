---
type: issue
kind: feature-gap
title: "Distill Zero-Mem: thêm nhánh entity-graph (NER+PageRank) bổ sung cho mem-rank hiện tại"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, memory, retrieval, mem-rank, zero-mem, frontier-gap]
timestamp: 2026-08-05
id: 050826-distill-zero-mem-graph-branch
source_session: "phiên đọc bài Zero-Mem (PolyU Hong Kong) 05/08/2026, đối chiếu với mem-rank.py hiện có"
---

# Issue: Distill Zero-Mem — thêm nhánh đồ thị thực thể cho tầng nhớ episodic

## Vấn đề (một câu)
Zero-Mem (PolyU Hong Kong) chứng minh trí nhớ agent đạt độ chính xác cao nhất (F1 59.15 trên LoCoMo, hơn GAM — đối thủ mạnh nhất — hơn 5 điểm) với chi phí vận hành bằng 0 token nhờ hai nhánh truy hồi bổ sung nhau (đồ thị thực thể + cây thời gian phân tầng) và bỏ 1 trong 2 nhánh thì điểm rơi mạnh; `mem-rank.py` hiện tại của overstack đã đạt tinh thần "0-token retrieval" (token-overlap ranker, LLM không tham gia build/route/retrieve) nhưng **chỉ có nhánh temporal** (supersedes-link), **thiếu hẳn nhánh quan hệ-thực-thể** — nên các câu hỏi kiểu "ai/cái gì từng xuất hiện cùng nhau" không có đường trả lời tất định.

## Bối cảnh & bằng chứng
- Nguồn: bài Zero-Mem, nhóm nghiên cứu Đại học Bách khoa Hong Kong (PolyU), benchmark LoCoMo (hội thoại dài nhiều phiên). Số đo: F1 trung bình **59.15** (cao nhất trong các hệ so sánh, GAM đứng nhì với 53.75); chi phí vận hành **0 token** so với GAM tốn **28,570,674 token**; tổng thời gian vận hành trí nhớ **334.77s** (~0.22s/truy vấn), nhanh hơn 57.6% hệ nhanh nhất trước đó. LLM chỉ được gọi đúng **một lần** — lúc đọc bằng chứng đã lọc để trả lời câu hỏi cuối cùng; toàn bộ build/route/retrieve/repair đều bằng quy tắc (NER kiểu spaCy + PageRank cho nhánh quan hệ; turn→window→episode cho nhánh thời gian). Ablation: bỏ 1 trong 2 nhánh → điểm rơi mạnh, cả hai đều cần thiết.
- Mã nguồn Zero-Mem **chưa công bố** (đang chờ qua peer review) — không có repo để đối chiếu trực tiếp, chỉ có kiến trúc mô tả trong bài. Đã kiểm `gh search repos` trên GitHub: repo chính chủ tồn tại tại `TheMoon0815/Zero-mem` (tạo 2026-07-30, 10 sao) nhưng chỉ có README placeholder ("After peer review, the code and implementation details will be released") — chưa có code để đối chiếu.
- Đã grep toàn repo (`llmwiki`, `skills`, `scratchpad`) tìm "zero-mem"/"zeromem"/"locomo" — không có hit thật, chỉ false-positive khớp rời "zero"/"mem" (vd `design-taste-frontend`, macrostructure `18-portfolio-grid`). Chưa từng absorb Zero-Mem vào overstack.
- Tiền lệ trực tiếp: **[[030726-memory-episodic-vector]]** (đã `done` 2026-07-04, archived tại `llmwiki/wiki/sources/draft/archive/analysis/030726-memory-episodic-vector.md`) — issue đó đưa llmwiki từ ~1.5/4 lên 4/4 tầng nhớ (working/episodic/semantic/procedural), sinh ra `harness/scripts/mem-rank.py` + `harness/mem-rank.config.yaml` + skill `record-episode`. Cơ chế hiện tại (đọc trực tiếp từ code, không suy đoán):
  - `retrieve()` xếp hạng bằng `_overlap()` (token-overlap tất định) hoặc `_embed()`/`_cosine()` nếu config bật embedding adapter (mặc định `verified: false`) — **đây chính là dạng "0-token retrieval" mà Zero-Mem cổ vũ, overstack đã có sẵn tinh thần này**.
  - Tầng temporal: mọi record có `ts`; `episode --supersedes ID` ghi link trỏ ngược — trả lời được "điều gì đúng lúc nào", tương đương ý tưởng cây thời gian của Zero-Mem nhưng **phẳng** (list record + supersede-link), không phải cây phân tầng turn→window→episode.
  - **Không có nhánh quan hệ-thực-thể nào** — không NER, không đồ thị "ai xuất hiện cùng ai", không PageRank. Mọi truy vấn quan hệ ("người này liên quan tới việc kia thế nào") phải đi qua token-overlap phẳng, dễ nhầm giữa các phiên/thực-thể có từ khoá giống nhau — đúng lỗ hổng "flat search dễ nhầm phiên na ná nhau" mà bài Zero-Mem nêu là nhược điểm của hướng "giữ nguyên dữ liệu thô rồi tìm kiếm phẳng".
- Liên quan: `llmwiki/wiki/concepts/log-model.md` (nếu tồn tại) giải thích mem-rank khác gì với `events.jsonl`/`scratch-log`/`provenance-log` — mỗi sổ trả lời một câu hỏi hẹp; đồ thị thực thể sẽ là một góc truy hồi mới, không thay các sổ đó.

## Phạm vi
- `harness/scripts/mem-rank.py` + `harness/mem-rank.config.yaml`: thêm một hàm truy hồi thứ hai (nhánh quan hệ-thực-thể) chạy song song với `retrieve()` hiện có, không thay thế.
- Skill `record-episode` / `query` / `wiki-room`: nơi quyết định khi nào ưu tiên nhánh quan hệ vs nhánh thời gian (tương đương "pipeline cố định tự đọc câu hỏi để chọn ưu tiên" của Zero-Mem) — cần một quy tắc chọn nhánh bằng code, không LLM.
- Universal: mọi dự án dùng `llmwiki`/`mem-rank`, vì đây là hạ tầng chung của framework.

## Không thuộc phạm vi
- Không thay `mem-rank.py`/wiki bằng vector-DB hay dịch vụ managed cloud (đã chốt ở issue tiền lệ `030726-memory-episodic-vector`, giữ nguyên).
- Không port mã nguồn Zero-Mem — **mã nguồn chưa công bố**, đây là distill KIẾN TRÚC (2 nhánh bổ sung + fusion tất định), không phải fork/clone.
- Không đổi cây thời gian hiện tại (`ts` + `supersedes`) trừ khi phase graph chứng minh cần tái cấu trúc thành turn→window→episode thật sự.
- Không tự động NER lên toàn bộ `llmwiki/wiki/` — chỉ áp cho tầng episodic mới (memory.jsonl), tránh scope-creep sang wiki chính.

## Hướng gợi ý (không bắt buộc)
- Bước nhỏ trước: NER tất định rẻ (regex/heuristic tên riêng, hoặc `spaCy` nếu đã có sẵn dependency — kiểm trước khi thêm mới, theo ladder ponytail) trên field `text`/`did` của mỗi record `mem-rank`, dựng đồ thị đồng-xuất-hiện (co-occurrence) đơn giản trước khi nhảy thẳng lên PageRank.
- PageRank: dùng thẳng thuật toán chuẩn (không cần thư viện ngoài nếu đồ thị nhỏ — vài chục dòng networkx-free đủ dùng, hoặc `networkx` nếu đã là dependency sẵn có).
- Fusion rule: câu hỏi có tên riêng/thực-thể lặp → ưu tiên nhánh graph; câu hỏi có mốc thời gian ("phiên trước", "hôm qua") → ưu tiên nhánh temporal hiện có; mặc định chạy cả hai rồi hợp bằng union có dedupe (giống cách Zero-Mem "ghép lại, bổ sung mắt xích liên quan, lọc mâu thuẫn" — toàn bằng quy tắc).
- Golden eval: thêm 1 case vào `wikieval`/`episodic-baseline.json` đo hit@k cho câu hỏi QUAN HỆ (không chỉ semantic phẳng như golden hiện có), verify nhánh graph thực sự nâng độ chính xác chứ không chỉ thêm chi phí.

## Tiêu chí HOÀN THÀNH
- `mem-rank.py` có một lệnh/hàm truy hồi mới chạy nhánh entity-graph, 0 lời gọi LLM (giống `retrieve()` hiện tại), có `--self-test` tất định.
- Có ≥1 golden case dạng quan hệ-thực-thể trong `wikieval` mà nhánh graph trả đúng còn token-overlap phẳng trả sai/kém hơn — chứng minh nhánh mới CÓ GIÁ TRỊ, không phải thêm cho có.
- `medic`/gate hiện tại vẫn xanh sau khi thêm (không phá `p_eval`).

## Assign & lý do
@Rheinmir chủ; dispatch Claude (đụng retrieval + skill framework, cần bối cảnh wiki/mem-rank sẵn có). Mở bằng `/fdk` vì sửa chính framework overstack, không phải dự án downstream.

## Origin
Raise bởi phiên đọc bài Zero-Mem (PolyU Hong Kong) 2026-08-05. Grep xác nhận repo chưa có Zero-Mem/LoCoMo. Đối chiếu trực tiếp với `harness/scripts/mem-rank.py` (đọc code, không suy đoán) và issue tiền lệ [[030726-memory-episodic-vector]] để tránh trùng và để định vị chính xác cái ĐÃ có (temporal + 0-token retrieval) vs cái THIẾU (entity-graph, PageRank, hierarchical time tree).
