---
type: draft
title: "ralph-monitor — step 4 dây chuyền: nhìn thấy dây chuyền đang chạy/kẹt/xong (/br status)"
status: proposed
tags: [ralph, monitor, observability, issue-15, issue-11]
timestamp: 2026-07-05
---

# 050726-ralph-monitor

**Status:** proposed
**Issue:** GH#15 step 4/4 · đồng thời là thin-slice của GH#11 (observability). Council 028 đã chốt: #11-full KHÔNG chặn dây chuyền; Monitor v0 chỉ cần khi scale nhiều frame.
**Bản review cho người:** `llmwiki/html/050726-ralph-monitor.html` (Sequence diagram trong đó).

## What
Cho user NHÌN THẤY trạng thái dây chuyền không phải mò từng file: mỗi frame đang ở đâu (pending / running / green / stalled / killed / merged), truy ngược lỗi→frame→clause→(assumed?) bằng một trang HTML tất định sinh từ dữ liệu ĐÃ CÓ — không thêm sổ cái mới, không daemon, không auto-fire (ADR-004; tránh Goodhart theo lesson p-17).

## Nguồn dữ liệu (tất cả ĐÃ tồn tại sau step 1–3 — monitor chỉ là LỚP ĐỌC)
| Nguồn | Cho biết |
|-------|----------|
| `br/frames/*.md` frontmatter (`outcome`, `run_log_ref`) + `br/frames/index.md` | trạng thái từng frame, map frame↔clause↔scope |
| run-log JSON của loop-runner (`iterations`, `termination`, guard events) | run gần nhất: bao nhiêu iter, dừng vì gì, diff-jail/test-hash có kích hoạt không |
| `br/BR.md` (clause provenance) + bảng "Giả định đang gánh" | clause nào lens-assumed — điểm ngờ đầu tiên khi lỗi |
| git (`baseline_ref`, nhánh worktree run) | diff đã merge hay còn treo |

## Sản phẩm
1. **`fdk/tools/build-line-status.py`** (stdlib-only, tất định — cùng họ build-overstack-docs):
   - Đọc 4 nguồn trên → `br/line-status.json` (máy đọc) + `llmwiki/html/line-status.html` (người xem).
   - Trang HTML: (a) hàng KPI (frames tổng/green/stalled/killed · % clause assumed còn gánh), (b) bảng frame — mỗi hàng: frame_id, trạng thái màu, clause_ids, termination reason + số iter run cuối, link run-log, (c) khối truy ngược: gõ/chọn 1 file hoặc 1 frame → hiện chuỗi file→frame→clause→provenance, clause assumed tô cam, (d) timeline đơn giản các run theo thời gian từ run-log timestamps. Offline, không CDN, giải nghĩa thuật ngữ, R16 full-path, dark-mode.
   - `--check`: HTML trên đĩa khớp dữ liệu nguồn (chống drift tay, như mọi generator khác).
   - **Trạng thái suy TẤT ĐỊNH** từ dữ liệu, không LLM: có run_log + termination SUCCESS + chưa merge → `green-pending-review`; NO_PROGRESS/TIMEOUT → `stalled`; KILL condition → `killed`; merged (baseline_ref là ancestor của HEAD nhánh chính) → `merged`.
2. **`/br status`** (mode cuối của hub): chạy generator rồi in đường dẫn HTML + tóm tắt 3 dòng ra terminal; cờ `--open` mở browser.

## Plan (đợt 4 — sau khi đợt 3 có run-log thật đầu tiên)
1. Chốt schema `line-status.json` (versioned) từ run-log + frame frontmatter THẬT của đợt 3 (không thiết kế chay — dữ liệu thật quyết định field).
2. Viết `build-line-status.py` + `--check` + fixture selftest (1 bộ frame/run-log giả lập đủ 5 trạng thái).
3. Thêm mode `status` vào skill `/br`; register + CAPABILITIES.
4. Chạy trên dữ liệu thật đợt 3; nếu GH#11 cần rộng hơn (trace ngoài dây chuyền Ralph) → raise phần đó về #11, KHÔNG phình tool này.
5. medic --ci + ledger #15 + problem-tree p-22 (khi cả 4 step xong → cập nhật status/scope).

**DoD đợt 4:** sau ≥1 run thật, `/br status` ra trang HTML đúng trạng thái mọi frame + truy ngược 1 lỗi giả định đủ chuỗi file→frame→clause→assumed; `--check` gate được drift; selftest 5 trạng thái xanh.

**Không thuộc phạm vi:** daemon/watcher realtime; metric chấm điểm agent (đó là trace-grader/#4); dashboard đa-BR (chỉ 1 BR active đợt này); mọi thứ #11-full (OTel export…) — chỉ raise issue, không làm ở đây.

## Rủi ro
- **Goodhart** (đo cái dễ đo rồi tối ưu nhầm): monitor v0 CHỈ hiển thị trạng thái + truy ngược, KHÔNG chấm điểm, không xếp hạng frame/agent (lesson p-17 + council 030726 về metric).
- **Drift HTML sửa tay:** `--check` cùng cơ chế các generator hiện có; sửa gì cũng qua generator.
- **Thiết kế schema trước dữ liệu thật:** đã né bằng Plan bước 1 (chốt schema SAU run thật đợt 3).

## Agent Task Assignment
- Claude (phiên /fdk, nhánh issue-15): bước 1–5 sau khi user duyệt qua /propose (depends_on: đợt 3 có run-log thật).
- User: duyệt proposal; dùng thử `/br status` và phản hồi cái CẦN THẤY mà trang chưa hiện.

Sequence diagram: xem `llmwiki/html/050726-ralph-monitor.html` (section "Sequence — một lần /br status").

## Origin
Phiên planning GH#15 2026-07-05 (issue-15-br-k). Nguồn: council 028 (Monitor v0 đủ, #11 không chặn), lesson p-17 (đừng phình sổ cái — thêm lớp đọc trên dữ liệu sẵn), [[050726-ralph-loop-gate]], [[030726-observability-runtime]].
