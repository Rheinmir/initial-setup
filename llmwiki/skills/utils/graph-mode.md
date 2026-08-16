---
name: graph-mode
description: Bật luật chứng cứ evidence-chain (R19) cho phần CHAT — bắt buộc mọi chuỗi lập luận chấm dứt ở chứng cứ xem được (observed/tool-record/graph-edge/web/parametric/absence), khác fable5 (kỷ luật suy luận chung, không ràng buộc trích dẫn). Dùng khi user nói 'graph-mode', 'bật graph mode', 'evidence mode', hoặc invoke /graph-mode. Nặng token (buộc trích dẫn/mở file nhiều hơn mỗi câu trả lời) nên KHÔNG auto-bơm mỗi phiên — chỉ bật khi gọi tay. Once invoked it stays active for the rest of the session (toggle off with 'tắt graph mode' / 'graph-mode off' / 'normal mode').
---

# Skill: graph-mode

Luật chứng cứ của R19 (evidence-terminal) áp cho phần CHAT, chuyển ra khỏi
`llmwiki/CLAUDE.md`/`llmwiki/AGENT.md` (trước đây auto-bơm mọi phiên — nặng token vì
buộc trích dẫn/mở file nhiều hơn mỗi câu trả lời). Validator máy (`evidence_terminal.py`)
trên tài liệu có khối ```evidence-chain KHÔNG phụ thuộc skill này — luôn chạy qua
`harness/policy.yaml` bất kể graph-mode bật hay tắt. Skill này chỉ bật/tắt kỷ luật
CHAT (không validator nào với tới), là phần không tự-gate được nên cần cân nhắc chi phí
trước khi bật.

## When to use
- User nói "graph-mode", "bật graph mode", "evidence mode", "chế độ chứng cứ", hoặc gõ `/graph-mode`.
- Việc cần độ tin cậy cao trên kết luận sẽ dùng để QUYẾT ĐỊNH (audit, nghiệm thu, viết ADR/PLAN, chẩn đoán bug lan rộng nhiều file) — nơi một kết luận sai giá đắt hơn vài lượt tool call thêm.
- KHÔNG dùng cho việc thường ngày (sửa 1 file, trả lời câu hỏi đơn giản, việc reversible) — bật tràn lan làm mọi câu trả lời dài và tốn hơn không cần thiết.

## Bật (persistence)
ACTIVE MỌI câu trả lời kể từ lúc gọi cho tới khi tắt. Không tự trôi lại kiểu trả lời
suông sau nhiều lượt. **Tắt bằng:** "tắt graph mode" / "graph-mode off" / "normal mode".
Mặc định: **tắt** (không tự bật đầu phiên).

Khi bật, mọi chuỗi lập luận trong CHAT phải chấm dứt ở chứng cứ mở ra xem được, không
phải một lập luận nữa. Chuỗi `A vì B vì chứng cứ C` là xong; chuỗi `A vì B vì C` mà C
lại là suy luận thì CHƯA xong — phải khai tiếp C dựa trên cái gì, cho tới khi chạm đáy.

Sáu loại được tính là điểm cuối:
- `observed` — đường dẫn `file:line` mở ra được, hoặc lệnh chạy lại được kèm output.
- `tool-record` — id một mục trong provenance-log / events.jsonl / ledger.
- `graph-edge` — eid một cạnh trong wiki graph.
- `web` — dữ liệu tìm trên mạng: phải kèm **link tới ĐÚNG CHỖ tìm được** (không phải
  trang chủ), ngày truy cập, và trích nguyên văn đoạn đã dựa vào.
- `parametric` — kiến thức từ **training của model**: phải tự khai đúng là loại này,
  **chỉ rõ nó ở đâu ra** (tên chuẩn, tài liệu, tác giả), và nói rõ là chưa kiểm chứng.
  KHÔNG được là điểm cuối duy nhất của một kết luận dùng để quyết định — phải nâng lên
  `web`/`observed` hoặc đi kèm loại khác.
- `absence` — chính lệnh/truy vấn đã chạy để tìm, kèm output rỗng của nó.

Không kết luận bằng "rõ ràng là", "ai cũng biết", hay bằng cách trỏ ngược về một mục
lập luận khác trong cùng câu trả lời. Chi tiết cơ chế: [[evidence-terminal-chain]].

## Rules
- Đây là kỷ luật CHAT không có validator nào bắt được — nếu tắt, không ai chặn; nếu
  bật, phải tự tuân thủ nghiêm vì không có cổng nào cứu.
- Không đè lên luật R19 machine-gate cho tài liệu `evidence-chain` (`applies_to: [write]`
  trong `harness/policy.yaml`) — luật đó độc lập, luôn chạy bất kể skill này.
- Touch only what the task requires — no opportunistic changes.
