---
type: draft
title: Điểm bất tiện của dây chuyền /br — cho người sẽ làm việc với nó
status: proposed
tags: [br, dx, onboarding, friction, pipeline]
timestamp: 2026-07-12
---

# 120726-pipeline-friction
**Status:** proposed · gom từ council-DX + quan sát thực tế phiên 2026-07-12.

Danh sách bất tiện THẬT khi làm việc với dây chuyền `/br`, kèm cách giảm. Dành cho người kế nhiệm — đọc trước khi nhảy vào.

## Top friction (theo mức cản trở)
1. **Lệnh dài + phải `--root .` đúng cwd.** `python3 fdk/tools/br-run.py run br/frames/<f>.md --root .` — sai thư mục / quên `--root` là hỏng. *Giảm:* thêm quickstart 5 dòng + alias `br` một-từ.
2. **Số "mode" không nhất quán.** CLAUDE.md/skill nói 5 mode; thực có thêm `/br find`, `/br assemble`, `/br sync`, `/br contract` → người mới không biết còn bao nhiêu lệnh. *Giảm:* MỘT bảng mode đánh số dứt khoát (hiện đã 7 mode trong br.md — cập nhật description skill cho khớp).
3. **`/br` không phải slash thật — mọi thao tác là `python3 fdk/tools/*.py` tay.** "User chỉ mô tả phạm vi" là lý tưởng; runbook bên dưới toàn lệnh thủ công. *Giảm:* quickstart happy-path copy-paste (interview→compile→slice→run→status).
4. **8+ tool tên gạch-nối** (`br-run`, `br-contract`, `frame-lint`, `loop-cost`, `br-queue`, `br-revise`, `br-find`, `br-prompts`, `br-sync`) lẫn trong ~30 file `fdk/tools/`, không import được như module (dấu `-`). *Giảm:* bảng "việc → tool" ngay đầu skill hub.
5. **Rối khái niệm:** frame vs clause vs component vs slice vs "giả định đang gánh" vs ground-truth; 3 nguồn chân lý; 2 loại "chưa chắc". *Giảm:* glossary tập trung + link `CODEBASE-MAP.md` từ skill hub (hiện chỉ nằm ở `br/payroll/docs/`, project khác không có).
6. **Rào chắn dày ngày đầu:** R1–R9, 6 phanh, tier-gate `--ack-tier`, `--ship`, `--worktree`, `loop-cost`. Tốt nhưng nặng. *Giảm:* tách "cần biết ngày 1" (5 lệnh) khỏi "cơ chế gác" (đọc sau).

## Thiếu onboarding
- Không có `br/QUICKSTART.md` (happy-path 5 lệnh).
- Description skill `br` ghi "5 mode", bỏ sót `find`/`assemble`/`sync`/`contract` — index không khớp thực tế.
- `CODEBASE-MAP.md` (bản đồ tốt nhất cho người mới) chỉ có cho `br/payroll`, không link từ hub; project khác thiếu bản tương đương.
- Không có glossary tập trung.
- Không có `br doctor` (kiểm "đã cài đúng chưa") — selftest có per-tool nhưng rời rạc.

## Bất tiện hạ tầng (từ harness-doctor)
- **pre-commit chưa cài trong `.git/hooks`** — shim gọi `python` nhưng máy chỉ có `python3` trên PATH. L2 git backstop không active. *Giảm:* `pre-commit install` với python3 trên PATH, hoặc symlink.
- Nhiều lệnh phải `cd br/payroll` trước; chạy từ gốc repo hay báo "no such file or directory".

## Đề xuất hành động (ưu tiên)
1. Viết `br/QUICKSTART.md` + cập nhật description skill cho đủ 7 mode.
2. Thêm glossary + link CODEBASE-MAP từ skill hub.
3. `br doctor` gom selftest mọi tool + kiểm cwd/PATH.

## Origin
Council-DX (ghế 2) + harness-doctor + quan sát phiên 2026-07-12 (nghiệm thu app payroll).
