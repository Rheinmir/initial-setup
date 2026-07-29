---
name: checkpoint-trace
description: >-
  Cỗ máy thời gian cho một lượt chạy agent trên codebase — distill từ SHEPHERD
  ("Reversible Agentic Execution Traces", arxiv 2605.10913). Mô hình mỗi bước agent =
  một CHECKPOINT trong một trace kiểu git, để ROLL BACK cây code về BẤT KỲ trạng thái
  trước đó (mọi state luôn reachable, lịch sử không bị xoá), CỘNG phân loại mỗi effect
  theo 3 "tier khả-đảo": reversible (ghi file — tự roll-back được) · compensable
  (side-effect cần handler bù, vd ghi DB) · irreversible (model call/email/API ngoài —
  chỉ audit, không undo được → phải gate trước khi materialize). Gọi khi user nói
  "roll back về trạng thái bất kỳ", "checkpoint codebase", "undo cả lượt chạy agent",
  "reversible trace", "shepherd", "time machine cho codebase", hoặc invoke /checkpoint-trace.
  KHÁC /br run (commit per-frame) và loop-runner (revert per-iteration): đây là rollback
  TOÀN LƯỢT về bất kỳ mốc + kỷ luật tier khả-đảo.
---

# Skill: checkpoint-trace — reversible trace cho codebase (distill từ SHEPHERD)

## Ý tưởng gốc (SHEPHERD, arxiv 2605.10913)
SHEPHERD coi một lượt chạy agent là một **persistent branching commit graph**: mỗi effect =
một commit có kiểu; `fork`/`merge`/`discard` = tạo/gộp/bỏ nhánh; **mọi state quá khứ luôn
reachable & replayable** (điều hướng graph về bất kỳ hash → khôi phục byte-identical). Mỗi
effect mang một **reversibility tier** quyết định hợp đồng rollback. Work về dạng **held
proposal** (fork chạy cô lập → observe → merge hoặc discard; discard → parent byte-identical).

Ta không có substrate Python của SHEPHERD — **substrate của ta là GIT**. Skill này áp ĐÚNG
3 ý cốt lõi lên git, bằng tool tất định `fdk/tools/checkpoint.py`.

## When to use
- Chạy một lượt agent/pipeline nhiều bước và muốn **quay về bất kỳ mốc** nếu đi sai (không chỉ undo bước cuối).
- Có effect **không-đảo-được** (gửi email, gọi API tính phí, ghi DB) cần **gate trước khi để nó landing**.
- Muốn một **audit trace** tự-mô-tả: mỗi bước làm gì, tier gì, hash nào.

## Đồ nghề (đã build + selftest)
`fdk/tools/checkpoint.py` — `selftest` 7 check. Sổ trace tự-mô-tả ở `.checkpoints.jsonl` (append-only, đi cùng commit).

## Đã WIRE vào /br run (cách dùng chính — không cần gọi tay)
Mỗi `br-run.py run` (in-place) TỰ: tier-gate frame khai `tier:` không-đảo (chặn tới khi
`--ack-tier`) + `record` một mốc vào `.checkpoints.jsonl` trỏ commit frame (không double-commit).
→ `checkpoint.py list` = timeline cả dây chuyền · `checkpoint.py rollback <frame_id>` = quay
cả pipeline về frame bất kỳ theo TÊN. Gọi tay các verb dưới chỉ khi chạy NGOÀI dây chuyền /br.

## Steps
1. **Trước mỗi bước có rủi ro**, phân loại effect và GATE nếu cần:
   ```
   python3 fdk/tools/checkpoint.py tier-gate irreversible   # exit 4 → DỪNG, hỏi người
   ```
   reversible → exit 0 (cho chạy) · compensable → exit 3 (cần handler bù) · irreversible → exit 4 (cần người).
2. **Sau mỗi bước hoàn tất**, đóng checkpoint vào trace (ghi tier + mô tả effect):
   ```
   python3 fdk/tools/checkpoint.py save --label "sửa auth" --tier reversible --effect "app/auth.py"
   python3 fdk/tools/checkpoint.py save --label "gửi mail xác nhận" --tier irreversible --effect "email khách"
   ```
3. **Xem trace bất cứ lúc nào**:
   ```
   python3 fdk/tools/checkpoint.py list      # seq · tier (⚠ irreversible) · hash · label/effect
   ```
4. **Roll back về BẤT KỲ mốc** (theo seq hoặc hash-prefix) — cây code khôi phục, **lịch sử GIỮ nguyên**:
   ```
   python3 fdk/tools/checkpoint.py rollback 3        # hoặc: rollback a1b2c3d
   ```
   Tool CẢNH BÁO nếu có checkpoint SAU mốc đích mang tier compensable/irreversible — effect đó ĐÃ
   materialize, roll code KHÔNG undo được: compensable → chạy handler bù; irreversible → xử tay.

## Rules
- **Trace CHỈ TĂNG, mọi state reachable** (nguyên tắc SHEPHERD): rollback KHÔNG xoá lịch sử — nó khôi phục cây rồi ghi CHÍNH hành động rollback thành một step mới. Không `reset --hard` phá commit.
- **Gate TRƯỚC khi materialize effect không-đảo**: `tier-gate` là cổng người-gác cho model-call/email/API ngoài — đừng để chúng landing rồi mới hối. "Rollback code không undo được email đã gửi."
- **Mỗi effect khai đúng tier** — khai sai (gọi API mà ghi `reversible`) làm hỏng bảo đảm rollback. Khi nghi ngờ, khai tier CAO hơn (fail-safe).
- **Bổ trợ, không thay** `/br run` (commit per-frame trong dây chuyền) và `loop-runner` (revert per-iteration). Dùng checkpoint-trace cho rollback TOÀN LƯỢT + kỷ luật tier.
- **Self-contained**: chỉ cần git + `checkpoint.py`. Sổ `.checkpoints.jsonl` travel cùng repo.
- Ghi công nguồn: distill từ SHEPHERD (arxiv 2605.10913 · shepherd-agents.ai) — KHÔNG chép code, chỉ mượn mô hình reversible-trace + reversibility-tier áp lên git.
