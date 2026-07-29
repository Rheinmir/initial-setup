---
name: unknown
description: >-
  Bắt + làm rõ + lưu UNKNOWN (chỗ mơ hồ làm reasoning/"think" rối) cho MỌI project
  (không cần /br hay llmwiki). Khi gọi: tự PHỎNG VẤN user làm rõ những unknown của phiên
  đang khiến think confused, ghi vào ledger jsonl per-project (`~/.claude/unknowns/<slug>.jsonl`),
  surface qua MEMORY.md mỗi phiên để KHÔNG QUÊN, promote CỐ Ý sang memory (pattern lặp) hoặc
  wiki (quyết định) khi đáng thành tri-thức. Trigger: "unknown", "chỗ này mơ hồ", "làm rõ cái
  chưa chắc", "ghi lại unknown", "think bị rối / confused", "phỏng vấn làm rõ", "/unknown".
---

# Skill: unknown — bắt · làm rõ · lưu · chống-quên các UNKNOWN

> Meadows: một unknown mơ hồ không được bắt → reasoning đoán bừa → sai lan. Chống-quên phải
> là VÒNG PHẢN HỒI chủ động, không phải file thụ động: unknown open đi ké recall của memory
> (MEMORY.md nạp mỗi phiên) nên mỗi phiên mới ĐỀU THẤY. Universal — mọi project, không /br/wiki.

## When to use
- Đang có chỗ mơ hồ/ambiguous làm reasoning rối, hoặc user chỉ ra "cái này chưa rõ".
- Muốn ghi lại unknown để phiên sau không quên + làm rõ dần.
- Trước khi làm việc nguy hiểm/ambiguous (tắt phanh, xoá, ra-ngoài) — bắt unknown + hỏi trước
  (khớp nguyên tắc "unknown thì hỏi kỹ trước khi thực hiện").

## Steps
1. **Bắt (capture):** liệt kê các unknown của phiên đang làm think rối → mỗi cái:
   `python3 fdk/tools/unknown.py add "<mô tả>" --why "<vì sao rối>"`.
2. **Phỏng vấn làm rõ:** với mỗi unknown OPEN, hỏi user bằng câu hỏi CỤ THỂ (dùng
   `AskUserQuestion` — option rõ ràng + nhược/lợi nếu là quyết định). KHÔNG đoán thay user.
3. **Ghi câu trả lời:** `unknown.py resolve <id> --answer "<chốt>"` → status resolved.
4. **Chống-quên (TẤT ĐỊNH — không dán tay):** truyền `--memory <path MEMORY.md>` cho `add`/
   `resolve`, hoặc chạy `unknown.py sync-memory --memory <path>` → tool TỰ viết/gỡ idempotent
   một dòng managed `⚠ N unknown chưa giải — /unknown list <!-- unknown-sync -->` trong MEMORY.md
   (nạp mỗi phiên). Còn open thì dòng ở đó; giải hết thì tool tự gỡ. Không trùng dòng, không đụng
   memory khác. Project KHÔNG có auto-memory thì bỏ `--memory`, dựa `/unknown list` tay.
5. **Promote (cố ý, chỉ cái đáng):** `unknown.py promote <id> --to memory|wiki` → rồi agent
   GHI file đích: `memory` = `memory/<slug>.md` + pointer MEMORY.md (pattern lặp) · `wiki` =
   wiki decision/ADR draft (quyết định dự án, chỉ khi project có llmwiki). Cái không đáng để
   nguyên `resolved` trong ledger.
6. `unknown.py status` / `list [--all]` để xem.

## Rules
- **Universal — KHÔNG phụ thuộc /br/llmwiki.** Ledger ở `~/.claude/unknowns/<slug-project>.jsonl` (keyed theo đường dẫn project), không đụng repo user, không cần pipeline.
- **Không đoán thay user cho unknown thật.** Unknown = chỗ CHƯA CHẮC; skill phải HỎI (AskUserQuestion), rồi mới ghi resolved. Đoán bừa rồi ghi = phản tác dụng.
- **Chống-quên là bắt buộc, không optional.** Còn open mà không surface qua MEMORY.md = sẽ quên = vô dụng. Bước 4 không được bỏ.
- **Promote có chọn lọc.** Đừng promote mọi unknown → loãng memory/wiki. Chỉ pattern-lặp (→memory) hoặc quyết-định-bền (→wiki).
- **Không dẫm:** khác `raise-issue` (issue để dev khác làm) + `failure-flywheel` (lỗi lặp → rule) — `unknown` là *chỗ mơ hồ chưa được làm rõ trong phiên*, vòng đời riêng (open→clarified→resolved→promote).
