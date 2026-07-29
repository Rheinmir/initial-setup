---
type: draft
title: "ralph-slice-frames — step 2 dây chuyền: BR → frames gắn chặt code (/br slice)"
status: proposed
tags: [ralph, br, slicer, frames, issue-15]
timestamp: 2026-07-05
---

# 050726-ralph-slice-frames

**Status:** proposed
**Issue:** GH#15 · step 2/4 dây chuyền (sau [[050726-ralph-interview-pipeline]]). Kế thừa council 031/032: frame schema đã chốt trường; rủi ro đuôi số 1 của slicer = cắt sai HÀNG LOẠT theo khuôn hệ thống (Taleb, council 028).
**Bản review cho người:** `llmwiki/html/050726-ralph-slice-frames.html` (Sequence diagram trong đó).

## What
Biến BR (đã compile từ interview, mỗi clause có `clause_id`) thành các **frame nhỏ gắn chặt code** — mỗi frame = {mục tiêu, scope code, acceptance-test} — kèm **registry truy ngược** lỗi→frame→clause. Đợt 1: slicer là **người-trong-vòng-lặp** (agent ĐỀ XUẤT lát cắt, người duyệt TỪNG frame), chưa auto — vì lỗi slicer là lỗi tương quan (mọi frame hỏng cùng kiểu).

## Frame schema v0 (chốt từ council 031/032 — KHÔNG thêm trường "phòng xa")
File `br/frames/frame-NNN-<slug>.md`, frontmatter:
- `schema_version: 0` (quan trọng nhất — cho phép schema thiếu, chừa cửa đổi)
- `frame_id`, `created_by: human|slicer`
- `parent_br` + `clause_ids: []` + `parent_br_hash` (BR đổi sau khi slice → frame mồ côi PHÁT HIỆN ĐƯỢC bằng so hash)
- `muc_tieu` (1 câu), `scope_code: []` (glob file được GHI — ≤3 file đợt đầu)
- `scope_test: []` (glob test — TÁCH RIÊNG, adapter loop KHÔNG được ghi; chống xanh-giả)
- `depends_on: []` (frame_id — DAG, không chu trình)
- `env/setup_cmd` (điều kiện trước khi chạy test), `acceptance_test` (shell cmd, exit-0 = đạt)
- `baseline_ref` (commit điểm quay về), `run_log_ref` + `outcome` (điền sau khi loop chạy)
- `guards: {max_iter, budget_seconds, no_progress_k, escalate_after_iter}`

## Registry truy ngược
`br/frames/index.md` — bảng: frame_id · clause_ids · scope_code · status · run_log_ref. Cho 1 "lỗi" (file/hành vi), tra ngược: file khớp scope_code của frame nào → frame → clause → nếu clause `lens-assumed` → câu hỏi interview vòng sau (khép vòng với step 1).

## frame-lint — validator tất định (chống lỗi tương quan TRƯỚC khi loop chạy)
`fdk/tools/frame-lint.py` (stdlib-only, exit≠0 khi fail):
1. Schema đủ trường bắt buộc + `schema_version` hợp lệ.
2. `scope_code` giao `scope_test` phải rỗng; glob không khớp file nào → FAIL; scope KHÔNG được chứa `harness/**`, `.github/**`, hook (frame không được sửa bộ phanh — council 032 mục 3).
3. `acceptance_test` chạy được và đang ĐỎ (test-first: frame chưa làm thì test phải fail — đỏ sẵn nghĩa là test có thật, không phải xanh giả từ đầu).
4. `parent_br_hash` khớp hash BR hiện tại (bắt frame mồ côi).
5. DAG `depends_on` không chu trình.

## Plan (đợt 2 — sau khi đợt 1 Interview merge)
1. Viết `frame-lint.py` + selftest fixture BAD/GOOD từng luật (5 luật trên).
2. Mở rộng skill `/br` mode `slice`: đọc `br/BR.md`, đề xuất danh sách lát cắt (mỗi lát: clause_ids + scope dự kiến + test dự kiến) → **STOP cho người duyệt/sửa từng lát** → ghi frame files + registry.
3. Sinh registry `br/frames/index.md` tự động từ frontmatter các frame (generator nhỏ, chống drift tay).
4. Chạy thử: BR mẫu từ đợt 1 → slice ≥3 frame → frame-lint xanh cả 3 → demo truy ngược 1 "lỗi" giả định về đúng frame + clause.
5. Register + medic --ci + ledger #15 + problem-tree p-22.

**DoD đợt 2:** ≥3 frame hợp lệ qua frame-lint từ BR thật; registry truy ngược hoạt động (1 lỗi giả định → đúng frame → đúng clause); mọi frame người đã duyệt tay; chưa có frame nào chạy loop (đó là đợt 3).

**Không thuộc phạm vi:** slicer full-auto (chỉ sau khi ≥1 BR đi trọn dây chuyền và lesson cho thấy đề xuất lát cắt ổn định); frame sửa harness/hook/CI (cấm cứng trong frame-lint).

## Rủi ro
- **Lỗi tương quan slicer** (blast-radius = toàn BR): chốt chặn = người duyệt TỪNG frame + frame-lint bắt khuôn sai trước khi loop tốn tiền; lô đầu tối đa 3-5 frame.
- **Frame mồ côi khi BR đổi**: `parent_br_hash` + frame-lint luật 4 bắt tất định.
- **Test đỏ giả** (test fail vì env thiếu chứ không phải vì feature chưa làm): `setup_cmd` phải chạy trước khi kiểm luật 3; lint phân biệt exit-code test-fail với crash.

## Agent Task Assignment
- Claude (phiên /fdk, nhánh issue-15): thi công bước 1–5 sau khi user duyệt qua /propose (và sau khi đợt 1 Interview xong — depends_on cứng).
- User: duyệt từng lát cắt ở bước 2; chọn để nguyên/gộp/tách.

Sequence diagram: xem `llmwiki/html/050726-ralph-slice-frames.html` (section "Sequence — một vòng slice").

## Origin
Phiên planning GH#15 2026-07-05 (issue-15-br-k), tiếp mẫu step-1 Interview của user. Nguồn: council-report-032 (frame schema + 6 điều kiện), council-report-028 (rủi ro tương quan slicer), [[030726-ralph-br-frame-production-line]].
