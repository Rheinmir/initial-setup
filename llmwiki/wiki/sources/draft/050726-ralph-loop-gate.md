---
type: draft
title: "ralph-loop-gate — step 3 dây chuyền: mỗi frame là loop có kỷ luật + cổng người gác (/br run)"
status: proposed
tags: [ralph, loop-runner, gate, dry-run, issue-15]
timestamp: 2026-07-05
---

# 050726-ralph-loop-gate

**Status:** proposed
**Issue:** GH#15 · step 3/4 (sau [[050726-ralph-slice-frames]]). Đây là phần council 031/032 đã phán quyết "ĐẠT CÓ ĐIỀU KIỆN" với **6 sửa bắt buộc** — proposal này chi tiết hoá thành việc thi công.
**Bản review cho người:** `llmwiki/html/050726-ralph-loop-gate.html` (Sequence diagram trong đó).

## What
Chạy MỖI frame như một agent-loop có kỷ luật: propose → verify(acceptance_test, tất định) → revise (adapter LLM), bọc bởi `loop-runner.py` (đã có, 4 guard) + **2 guard MỚI** (diff-jail, test-hash) — dry-run KHÔNG tự commit, người là cổng cuối. Thin-slice: ĐÚNG MỘT frame đầu tiên.

## 6 điều kiện council (bắt buộc, không thương lượng)
1. **Chống xanh-giả:** hash mọi file khớp `scope_test` TRƯỚC loop; sau MỖI iteration hash lại — lệch → dừng FAIL-CLOSED (adapter đã đụng test).
2. **Diff-jail:** sau mỗi iteration `git diff --name-only` so glob `scope_code` ∪ `scope_test`; file ngoài scope → `git checkout --` file đó (revert phần tràn) + iteration tính vào `no_progress`.
3. **Jail mức OS:** loop chạy trong **git worktree riêng** (không phải worktree người đang làm); adapter `claude -p` quyền tối thiểu (`--allowedTools Edit,Write,Read,Grep,Glob` — không Bash tự do, không network); scope không đụng harness/hook/CI (frame-lint đã chặn từ step 2).
4. **Điều kiện KILL viết trước** (via negativa), trong config từng run: vd "diff-jail kích hoạt ≥2 lần", "test-hash lệch 1 lần", "TIMEOUT + diff > 200 dòng" → dừng vứt cả run, không cứu.
5. **Working-tree SẠCH** trước khi loop (check tất định, dirty → từ chối chạy).
6. **Cắt thừa:** không monitor HTML trong step này; gate chỉ `medic --ci` (wikieval bỏ khỏi thin-slice).

## Kiến trúc thi công
- **`loop-runner.py` thêm 2 guard** (cùng hạng 4 guard cũ, tất định, có selftest):
  - `--scope "<glob,glob>"` → diff-jail (điều kiện 2). Không truyền = guard tắt (tương thích ngược).
  - `--protect "<glob,glob>"` → test-hash fail-closed (điều kiện 1).
  - Selftest thêm 2 kịch bản: adapter-stub cố ghi ngoài scope → bị revert + no_progress; stub sửa file protect → FAIL-CLOSED. (Tổng selftest 5→7.)
- **Revise adapter** (`harness/loop-runner.config.yaml`, vẫn là MỘT file quarantine): lệnh `claude -p` với prompt dựng từ frame (mục tiêu + scope_code + output verify lần fail gần nhất), tools bó hẹp như điều kiện 3.
- **Orchestrator `/br run <frame>`** (mode mới của skill `/br`): (a) frame-lint xanh, (b) tạo worktree riêng từ `baseline_ref`, (c) check sạch, (d) chạy loop-runner với guard từ frontmatter frame, (e) loop dừng → viết **tóm tắt MỘT DÒNG** (termination reason · số iter · diffstat · lệnh verify cuối — ý Rams) + chạy `medic --ci`, (f) STOP — người đọc diff trong worktree, tự quyết commit/merge/vứt, (g) điền `run_log_ref` + `outcome` vào frame + registry.
- **Lesson (reflexion):** ghi vào episodic page cả điều KHÔNG xảy ra (loop có thử phá scope không, guard nào chưa từng kích hoạt — ý Lão Tử).

## Plan (đợt 3 — sau khi đợt 2 Slice merge)
1. Thêm 2 guard + 2 selftest vào `loop-runner.py` (surgical — không đổi 4 guard cũ; impact-check caller trước).
2. Viết revise-adapter `claude -p` trong `loop-runner.config.yaml` (quarantine, `verified: false`).
3. Mở rộng skill `/br` mode `run` theo orchestrator trên (gồm bảng điều kiện KILL mặc định, override được per-frame).
4. Chạy thật ĐÚNG MỘT frame (frame-001 từ đợt 2): mục tiêu là quan sát loop vỡ kiểu gì, không phải diff xanh. Chạy thêm 1 lần CỐ TÌNH phá (adapter stub ghi ngoài scope) để chứng minh diff-jail cắn trên đường thật, không chỉ selftest.
5. Ghi lesson + outcome vào frame/registry/ledger #15/problem-tree; flip `verified: true` cho adapter nếu chạy thật đạt.

**DoD đợt 3:** 1 frame chạy trọn loop trong worktree riêng → SUCCESS hoặc guard dừng ĐÚNG lý do; diff nằm trọn trong scope; 2 guard mới có selftest xanh + 1 lần cắn thật được demo; người duyệt với tóm tắt một-dòng + run-log; KHÔNG có commit nào do máy tự tạo.

**Không thuộc phạm vi:** chạy nhiều frame song song; auto-merge; monitor HTML (step 4); tự nâng max_iter khi fail (cấm — guard là bất khả xâm phạm).

## Rủi ro
- **Adapter lách qua khe** (sửa file ngoài scope rồi revert kịp trước check? — không: check chạy sau MỖI iteration, revert tất định; sửa test? — test-hash fail-closed).
- **`claude -p` chạy lệnh phụ ngoài dự kiến:** tools bó hẹp không Bash; worktree riêng giới hạn thiệt hại filesystem; điều kiện KILL dừng sớm.
- **Guard giết oan run sắp xong** (max_iter chạm khi test gần xanh): chấp nhận — theo council, thừa phanh rẻ hơn thiếu phanh; người xem run-log tự quyết chạy tiếp tay.

## Agent Task Assignment
- Claude (phiên /fdk, nhánh issue-15): bước 1–5 sau khi user duyệt qua /propose (depends_on: đợt 2).
- User: duyệt proposal; bấm nút sau mỗi run; quyết merge/vứt diff.

Sequence diagram: xem `llmwiki/html/050726-ralph-loop-gate.html` (section "Sequence — một run").

## Origin
Phiên planning GH#15 2026-07-05 (issue-15-br-k). Nguồn: council-report-031/032 (phán quyết + 6 điều kiện — winner Taleb mean-rank 1.0), skill `loop-runner` hiện có, [[050726-ralph-slice-frames]], [[030726-ralph-br-frame-production-line]].
