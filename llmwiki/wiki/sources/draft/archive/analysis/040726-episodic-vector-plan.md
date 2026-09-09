---
type: draft
status: proposed
title: "Kế hoạch issue#9 — episodic + vector-retrieval + temporal (4/4 tầng nhớ)"
id: 040726-episodic-vector-plan
tags: [draft, memory, retrieval, episodic, issue-9]
timestamp: 2026-07-04
---

# Draft: đạt 4/4 tầng nhớ cho llmwiki (issue #9)

## TL;DR
Nền tảng **vector-retrieval đã có** (`mem-rank.py` — store + retrieve top-k, embedding adapter đã
quarantine). Việc còn lại KHÔNG phải dựng lại, mà là **nối dây**: (1) ghi *episodic* (phiên trước
làm gì) vào store, (2) cho `query` truy hồi ngữ nghĩa từ store chứ không chỉ `[[wikilink]]`,
(3) gắn *temporal* (ts + supersede), (4) 1 golden episodic đo hit@k, cắm vào eval hồi quy.
Giữ nguyên: wiki là nguồn chân lý, vector chỉ là lớp truy hồi phụ, tất cả local/travel-được.

## Trạng thái 4 tầng
| Tầng | Hiện | Sau kế hoạch |
|---|---|---|
| working (context) | có | có |
| semantic (wiki) | có (term-scan + link) | + truy hồi ngữ nghĩa qua mem-rank |
| procedural (skills) | có | có |
| **episodic (phiên)** | **thiếu** | **có — session episode ghi + hồi được** |
| temporal | thiếu | ts + supersede-link trên episode |

## Các bước (surgical, không đụng nguồn chân lý wiki)
1. **Episodic recording** — skill/CLI mỏng `record-episode`: ghi bản tóm tắt phiên có cấu trúc
   `{id, ts, session, did, files, outcome}` vào mem-rank store với `kind=episode`. On-demand
   (KHÔNG auto-hook — ADR-004). Nguồn dữ liệu tận dụng: `ledger.jsonl` + `log.md` sẵn có.
2. **Wire semantic vào `query`** — thêm 1 bước ở Tầng-1: gọi `mem-rank retrieve "<câu hỏi>"`
   để nổi các episode/memory liên quan CẠNH kết quả term-scan wiki. Không thay term-scan, chỉ bổ sung.
3. **Temporal** — episode mang `ts`; UPDATE cùng `id` = supersede (giữ link `supersedes` để trả
   lời "điều này đúng ở thời điểm nào"). Tận dụng UPDATE-by-id sẵn có của mem-rank.
4. **Golden episodic + eval** — thêm ≥1 golden episodic đo **hit@k** truy hồi ngữ nghĩa; chạy
   qua mem-rank (tất định, token-overlap fallback — không cần model), cắm vào `retrieval-eval`/
   `wikieval` để CI cắn hồi quy. Tôn trọng HARD-CAP 30 golden.

## Không thuộc phạm vi
- Không thay wiki bằng vector-DB. Không kéo managed cloud. Không wire embedding model thật
  (giữ nguyên adapter `verified:false` — token-overlap đủ cho golden tất định).

## Tiêu chí HOÀN THÀNH (từ ledger #9)
- `query` trả kết quả ngữ nghĩa (không chỉ exact-link) trên ≥1 golden episodic.
- 1 golden hit@k truy hồi ngữ nghĩa cắm vào eval hồi quy.

## Origin
- Raise: ledger `030726-memory-episodic-vector.md` (issue GH#9), frontier-gap-scan 03/07/2026.
- Draft phiên 2026-07-04 qua /fdk.
