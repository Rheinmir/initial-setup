---
type: draft
title: Gộp gitignored-check trùng lặp trong okf-check.py về canonical index_sync
status: proposed
tags: [flywheel, spec-violation, harness, dedupe]
timestamp: 2026-07-17
task: T-260717-01
---

# 170726-gitignored-dedupe

**Status:** proposed

## What
Chốt rule từ 3 failure `spec-violation` đã ghi trong flywheel (đều là scanner từng thiếu bước "skip file gitignored"): thay vì để mỗi scanner tự cài lại logic `git check-ignore`, trỏ `okf-check.py` về đúng 1 implementation canonical đã có sẵn (`harness/validators/index_sync.py:gitignored()`), dùng lại pattern `_load()` dynamic-import mà `audit.py` đã dùng.

## Context
Không có concept/ADR nào trong wiki nói về scanner/gitignored (đã query `concepts/`, `sources/adr/`, `decisions.md` — rỗng). Grounding lấy trực tiếp từ code đang chạy:
- `harness/validators/index_sync.py:gitignored(rel, wiki)` — canonical, wiki-relative, cache theo path, fail-open khi `git` lỗi.
- `harness/scripts/audit.py` đã đúng pattern: dynamic-load canonical qua `_load(VALIDATORS / "index_sync.py", "_indexsync")` rồi gọi `index_mod.gitignored(f, wiki)` — không tự định nghĩa lại.
- `harness/scripts/okf-check.py:35-43` tự định nghĩa **bản copy riêng** `gitignored(path)` (absolute-path, không cache) — thêm ở commit `fcdd61d7` (2026-06-28) cùng ngày ghi nhận failure "R9 scanner okf-check.py content_files khong skip gitignored (latent)".
- `harness/poc-vendor-neutral/bin/harness-events.py:55-63` cũng tự định nghĩa bản copy riêng `_gitignored(path, cwd)` — nhưng file này thuộc **PoC vendor-neutral** (xem `harness/poc-vendor-neutral/README.md`: "1 lõi, nhiều dây cắm", cài bằng `curl | bash` độc lập vào project khác, không có `harness/scripts/` đi kèm) → **không thể** import cross-directory từ `harness/scripts/lib/` mà không phá ranh giới tự-chứa.
- `harness/scripts/harness-lint.py` đã có sẵn **meta-guard** `WIKI_TREE_SCANNERS` (regex `check-ignore|gitignored`) quét MỌI scanner để bắt trường hợp thiếu guard này — đây chính là cơ chế đã bắt được cả 3 failure và khiến chúng được vá trong ngày. Cơ chế phòng-ngừa hệ thống **đã tồn tại và đã chứng minh hoạt động**; phần còn thiếu chỉ là dọn trùng lặp *nội bộ* trong `harness/scripts/`.

## Global constraints
Chép nguyên văn từ `llmwiki/CLAUDE.md`:
- "Surgical changes. Chỉ chạm cái buộc phải chạm. Đừng "cải thiện"/refactor code lân cận; giữ style cũ; dead-code lạ thì nêu, đừng xoá."
- "Bug = root cause, không vá triệu chứng. Grep mọi caller, sửa 1 lần ở hàm chung — fix root-cause thường diff NHỎ HƠN vá từng caller."
- Trước push: `medic --ci` phải xanh (gate `ship`).

## Non-goals
- KHÔNG đụng `harness/poc-vendor-neutral/bin/harness-events.py` — bản `_gitignored()` tự chứa ở đó là **chủ ý** (ranh giới cài-đặt vendor-neutral), không phải lỗi trùng lặp cần dọn.
- KHÔNG đụng `wiki-graph.py` / `wiki-health.py` (`local_only_stem()`) — đây là một hàm khác (kiểm theo *stem* qua 3 đường dẫn ứng viên), trùng lặp verbatim giữa 2 file nhưng **không nằm trong 3 failure đã ghi nhận**; nêu ra như ghi chú follow-up, không tự mở rộng phạm vi propose này.
- KHÔNG đổi logic/regex meta-guard trong `harness-lint.py` (`WIKI_TREE_SCANNERS`) — nó đang hoạt động đúng, giữ nguyên.
- KHÔNG tạo file `lib/` mới — dùng lại `_load()` pattern đã có, canonical đã có sẵn.

## Approaches
**A. Không làm gì** — dựa hoàn toàn vào meta-guard `harness-lint.py` đã có để bắt scanner thiếu guard trong tương lai. Đã chứng minh hoạt động (bắt + vá cả 3 failure trong ngày). Nhược điểm: `okf-check.py` vẫn giữ 1 bản định nghĩa riêng cho đúng ngữ nghĩa canonical đã có — hai implementation có thể lệch hành vi âm thầm (khác cache, khác exception handling) mà meta-guard không phát hiện được (nó chỉ soi marker string, không soi tương đương hành vi).

**B. (Chọn) Trỏ `okf-check.py` về canonical** — xoá `gitignored(path)` cục bộ (dòng 35-43), dynamic-load `index_sync.py` giống hệt `audit.py`, gọi `index_mod.gitignored(rel, wiki)` (tính `rel` từ `p.relative_to(wiki).as_posix()` ngay trong `content_files()`). Diff nhỏ nhất, không file mới, dùng lại pattern đã có trong chính codebase này (ladder bậc 2).

**C. Tạo `harness/scripts/lib/gitcheck.py` dùng chung cho MỌI scanner kể cả `harness-events.py`** — bị loại: phá ranh giới tự-chứa của PoC vendor-neutral (xem Context) — `harness-events.py` được cài độc lập vào project khác qua curl, không có `harness/scripts/` đi kèm.

## Plan
- [ ] T1: `okf-check.py` — xoá hàm `gitignored(path)` cục bộ (dòng 35-43); thêm `_load()` dynamic-import `harness/validators/index_sync.py` (copy pattern từ `audit.py`); trong `content_files()`, tính `rel = p.relative_to(wiki).as_posix()` và gọi `index_mod.gitignored(rel, wiki)` thay cho `gitignored(p)`.

## Requirements (FR)
- **FR-001**: `okf-check.py` PHẢI dùng đúng 1 nguồn logic gitignored-check (canonical `index_sync.gitignored`), không giữ định nghĩa cục bộ riêng cho cùng ngữ nghĩa.
- **FR-002**: Hành vi `content_files()` (tập file bị loại vì gitignored) PHẢI giữ nguyên y hệt trước/sau refactor.
- **FR-003**: `harness-events.py` PHẢI giữ nguyên bản `_gitignored()` tự chứa — không import cross-directory từ `harness/scripts/`.

## Success criteria (SC)
- **SC-001**: Chạy `okf-check.py --check` trên cùng tập input đã từng gây false-positive (file trong `sources/draft/` bị gitignore) trước và sau refactor → kết quả giống hệt nhau, không hồi quy.
- **SC-002**: `harness-lint.py --scanners` (bao phủ R3+R9, 5 scanner) chạy xanh sau refactor.
- **SC-003**: Grep `def gitignored` trong `harness/scripts/` chỉ còn 0 kết quả cục bộ ở `okf-check.py` (đã xoá) — người đọc code không còn thấy 2 định nghĩa khác nhau cho cùng 1 ngữ nghĩa wiki-relative-gitignored.

## Assumptions
- (default) Giữ nguyên `harness-events.py` — không refactor, vì ranh giới vendor-neutral (xem Non-goals). Rủi ro thấp: nếu sau này 2 bản lệch hành vi, meta-guard `harness-lint.py` vẫn bắt được thiếu-marker, chỉ không bắt được lệch-hành-vi-tinh-vi — chấp nhận được vì đây là code phòng-vệ (fail-open), lệch tối đa là báo thiếu 1 lần rồi tự vá như 3 lần trước.
- (default) Không đụng `wiki-graph.py`/`wiki-health.py` — ngoài phạm vi 3 failure gốc, để dành cho một `/propose` riêng nếu ai đó muốn dọn tiếp.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| T1 | Claude | Refactor 1 file, ~10 dòng, cần đọc hiểu pattern `_load()` sẵn có trong `audit.py` trước khi áp dụng — không đáng dispatch sang CLI rẻ hơn cho một thay đổi nhỏ, có ngữ cảnh. | pending |

**Sequence diagram:** [170726-gitignored-dedupe-seq.html](../../../html/170726-gitignored-dedupe-seq.html)

## Render brief
### T1 — Trỏ okf-check.py về canonical index_sync.gitignored
1. (legacy) `okf-check.py` tự định nghĩa `gitignored(path)` — bản copy riêng, absolute-path, không cache.
2. (legacy) `audit.py` đã đúng: `_load(VALIDATORS / "index_sync.py", "_indexsync")` rồi gọi `index_mod.gitignored(f, wiki)`.
3. (add) `okf-check.py` xoá bản cục bộ, copy y hệt pattern `_load()` của `audit.py`, gọi `index_mod.gitignored(rel, wiki)` trong `content_files()`.
4. (block) Không đụng `harness-events.py` — ranh giới vendor-neutral, xem Non-goals; đây là nhánh CỐ Ý dừng lại, không phải thiếu sót.

Prose: Ba lần liên tiếp, một scanner khác nhau quên bước "bỏ qua file gitignored" — mỗi lần được vá tại chỗ, mỗi lần bằng một bản copy logic riêng. `harness-lint.py` đã có sẵn cơ chế bắt-thiếu (meta-guard quét marker `check-ignore|gitignored`) nên rủi ro "quên hẳn" cho tương lai đã được chặn — cái còn lại chỉ là 2 bản implementation cùng ngữ nghĩa (wiki-relative gitignored-check) tồn tại song song trong `harness/scripts/`, một canonical (`index_sync.py`, đã có `audit.py` dùng đúng cách) và một bản riêng ở `okf-check.py`. Refactor duy nhất trong SPEC này là trỏ `okf-check.py` về bản canonical bằng đúng pattern `_load()` mà `audit.py` đã chứng minh hoạt động — không file mới, không thay đổi hành vi, chỉ xoá một nguồn trùng lặp. `harness-events.py` bị loại khỏi phạm vi vì nó là phần lõi của một PoC "vendor-neutral" được cài độc lập bằng `curl | bash` vào các project khác — ràng buộc tự-chứa (self-contained) của nó là chủ ý kiến trúc, không phải nợ kỹ thuật.

## Self-review
1. **Phủ yêu cầu** — cả 3 failure gốc đã được đối chiếu: 2 cái (audit.py, okf-check.py) đã dùng/được trỏ về canonical; harness-events.py (cái thứ 3) được xử lý bằng quyết định KHÔNG đụng, có lý do rõ (Non-goals), không phải bỏ sót.
2. **Quét placeholder** — đã đọc lại toàn bộ Plan/FR/SC, mỗi mục đều là câu khẳng định cụ thể, không có mục nào mơ hồ.
3. **Nhất quán tên-kiểu** — dùng thống nhất `gitignored`/`index_mod`/`_load` đúng tên đã tồn tại trong `audit.py`, không đặt tên mới.

## Origin
- **Draft:** `wiki/sources/draft/170726-gitignored-dedupe.md`
- **Nguồn:** flywheel `spec-violation` (3 failure, ngưỡng 3) — `llmwiki/wiki/sources/draft/290626-failure-spec-violation.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
