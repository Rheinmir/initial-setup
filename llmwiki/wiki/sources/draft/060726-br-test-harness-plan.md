---
type: draft
title: "br-test-harness-plan — plan test/harass moi vấn đề dây chuyền /br (GH#15)"
status: proposed
tags: [ralph, br, testing, harass, council, issue-15]
timestamp: 2026-07-06
---

# 060726-br-test-harness-plan

**Status:** proposed
**Council:** report 033 (Feynman/senior-tester · Linus · Socrates · 3 judge chấm kín · đồng thuận tuyệt đối C>B>A, winner Feynman mean-rank 1.0). `llmwiki/html/council/council-report-033-seed42.html`.

## What
Kế hoạch test/harass ĐẦY ĐỦ để moi ra vấn đề của dây chuyền sản xuất code /br — biến harass ad-hoc thành **scaffolding thường trực**, với ưu tiên theo council: rủi ro số 1 là **false-GREEN qua oracle verify không-hermetic** (hỏng ÂM THẦM, cộng dồn), không phải false-RED (hỏng nhìn-thấy, an toàn).

## Đã harass + đã fix (bằng chứng thực tế, không lý thuyết)
Chạy 5 dự án × 30 frame (~150 frame-run) với revise xấu đủ kiểu (ok/multi2/wrong/flail/noop/greedy/tamper/crash/syntax/delete/unicode) + cổng bad-frame (orphan/overlap/nomatch/greentest/brakes) + resume. **3 bug thật phát hiện & vá, mỗi vá kèm regression selftest:**
1. **Stale `.pyc` → false verdict (nghiêm trọng)**: loop rewrite file + rerun test nhiều lần/giây → Python tái dùng bytecode cache theo mtime → verify chấm CODE CŨ (false-RED lộ ra ở multi2; false-GREEN về lý thuyết). Fix: verify/revise chạy với `PYTHONDONTWRITEBYTECODE=1` + `PYTHONHASHSEED=0` (loop-runner + frame-lint). Selftest `stale-pyc guard`.
2. **Tree bẩn cộng dồn ở quy mô**: 1 frame kẹt để diff dở → chặn oan 27 frame sau. Fix: lưu `.failed.patch` + revert scope + bookkeeping commit (br-run/br-queue).
3. **FLAKY / false-GREEN "SUCCESS nhưng không sửa code nào"**: verify flaky fluke xanh vòng 1 → SUCCESS với `changed_files=[]`. Fix (đúng đề xuất council về hermeticity): **guard 7 CONFIRM** — SUCCESS phải xanh LẠI K lần (br-run mặc định `--confirm 2`); lệch → verdict `FLAKY` (exit 7) fail-closed. Selftest `FLAKY_CONFIRM`.

## GAP council chỉ ra — ĐÃ KIỂM CHỨNG, phần lớn đã được bịt (sửa lại độ nghiêm trọng)
Council (winner) cho rằng test-hash chỉ băm file test LITERAL nên LLM có thể làm test xanh qua file test IMPORT bắc cầu (conftest/fixture/sitecustomize/plugin) → false-GREEN. **Đã test trực tiếp**: dựng test import `conftest_val.py` (ngoài scope), cho revise tamper nó thành trivially-true. Kết quả: **diff-jail revert ngay** (mọi file ngoài `scope_code` bị revert mỗi vòng, không chỉ file test) → test vẫn đỏ → verdict `NO_PROGRESS`, KHÔNG false-green. → **Với mối đe doạ TRONG-LOOP (LLM revise), gap này đã được diff-jail bịt** — test-hash chỉ là lớp 2 chuyên cho `scope_test`.
- CÒN LẠI (defence-in-depth, thấp hơn council tưởng): threat NGOÀI loop — frame-author (người/slicer) tự viết test tự-thoả-mãn import file đã-đúng-sẵn. Nhưng **frame-lint R3 (test phải ĐỎ trước khi build) đã bắt** ca này ở slice. → test-hash-transitive chỉ là hardening thừa, KHÔNG phải lỗ hổng mở. Phát hiện phụ: 3 lớp (R3 test-first + diff-jail blanket-revert + CONFIRM) phủ chồng lên nhau khá kín false-green — council thiếu tầm nhìn diff-jail nên đánh giá cao hơn thực tế.

## Plan — scaffolding test THƯỜNG TRỰC (thứ tự ưu tiên council)
1. **Oracle hermeticity & false-green (TẦNG 1 — CI mọi push, fail-closed):**
   - test-hash bao import-closure (đóng GAP trên).
   - **test-independence check**: chạy `acceptance_test` của frame X trên cây CHƯA có sửa của X → phải ĐỎ; xanh = test tự-thoả-mãn, quarantine frame.
   - **hermeticity double-run**: chạy cùng verify môi trường sạch vs bẩn (có/không `.pyc`, `PYTHONHASHSEED` khác, đảo thứ tự test) → verdict phải GIỐNG; phân kỳ = non-hermetic → không commit. (CONFIRM guard là bản rẻ đã có; mở rộng thành probe chuyên.)
   - "SUCCESS + `changed_files` rỗng" = SUSPECT (frame hợp lệ PHẢI đổi scope để đỏ→xanh).
2. **Property/invariant test (Hypothesis, stateful) trên 7 phanh (TẦNG 1):** mọi chuỗi revise ngẫu nhiên → diff cuối ⊆ scope · mutation file-test ⇒ fail-closed · chỉ commit khi verify xanh trên CODE HIỆN TẠI · loop luôn dừng · revise stateless (xáo thứ tự vòng không đổi kết quả).
3. **Mutation testing trên chính loop-runner (ai gác người gác):** đột biến code từng phanh → phải có ≥1 test đỏ. Nguyên tắc: mỗi test kèm câu hỏi "test này có thể xanh trong khi hệ đã hỏng không?" — có ⇒ vô dụng.
4. **Adapter `claude -p` THẬT (TẦNG 2 — nightly, gated, KHÔNG chặn):** cassette record/replay 200–500 phiên thật → replay tất định; fault-injection (truncated/empty/rác-quanh-diff/timeout/exit≠0) → khẳng định 7 phanh bắt, không false-GREEN. Lật `verified:true` khi smoke đạt.
5. **Fuzz filesystem/scope (TẦNG 2):** path dấu-cách/unicode/symlink-thoát-scope/`../`, glob rộng `app/**` → diff-jail phải giữ.
6. **Chaos & scale (TẦNG 3 — weekly):** kill `-9` GIỮA loop → resume idempotency (commit-hash đúng frame_id, không double-run/skip); scale 100–500 frame (đo hiệu năng + R6 pairwise O(n²)).
7. **Golden/characterization:** cùng input → verdict + HTML line-status byte-for-byte; đóng băng golden bắt regression im lặng.
8. **Kỷ luật thường trực:** mỗi bug fix = 1 regression test vĩnh viễn (đã áp: pyc, FLAKY). Promote harness harass (`harass_gen.py`/`harass_run.py` đang ở scratchpad) vào `fdk/tools/` hoặc `tests/`.

## Tail-risk (Q3 — cả 3 ghế hội tụ)
Giả định load-bearing: **verify là hàm TẤT ĐỊNH, hermetic, chỉ phụ thuộc code-in-scope + test đã commit**. `.pyc` đã chứng minh nó mong manh. Nếu sai → mọi phanh lý luận trên tín hiệu nhiễu, hệ hội tụ tới xanh giả rồi commit gắn frame_id → lỗi lan có chữ ký "đã kiểm chứng". Test chính nó = "máy-đo-niềm-tin": chạy cùng frame chưa đổi N≥50 lần trên cây bất động, entropy verdict phải = 0; bơm phi-tất-định có kiểm soát và hỏi phanh nào PHÁT HIỆN.

## Plan (thi công, thứ tự — đã cập nhật theo bằng chứng)
1. **test-independence check + "empty-diff SUCCESS = suspect"** (TẦNG 1, rẻ, giá trị cao) — không cần test-hash-transitive (đã bịt bởi diff-jail).
2. Promote harass harness (`harass_gen.py`/`harass_run.py`) vào repo + property test (Hypothesis) 7 phanh.
3. Mutation test loop-runner; wire CI 3 tầng (fast fail-closed / nightly cassette+fuzz / weekly chaos+scale).
4. Cassette real-adapter `claude -p` → fault-injection → lật `verified:true`.
5. (tuỳ chọn hardening) test-hash-transitive — chỉ khi mở threat-model ra ngoài loop.

## Agent Task Assignment
- Claude (phiên /fdk, nhánh issue-15): thi công theo thứ tự Plan sau khi user duyệt. Bước 1 (đóng GAP hermeticity) là ưu tiên tuyệt đối — false-GREEN là rủi ro âm thầm.
- User: duyệt proposal; quyết mức đầu tư CI (tầng nào bắt buộc chặn push).

Sequence diagram: xem `llmwiki/html/council/council-report-033-seed42.html` (blind-vote + dashboard) — mô tả luồng council → plan.

## Origin
Phiên GH#15 2026-07-06 (issue-15-br-k): user chỉ đạo harass-test 5 dự án × 30 frame, fix dần không thoả hiệp, thêm góc nhìn senior tester + council ra /propose plan test. Nguồn: council-report-033 (đồng thuận C>B>A) · harass runs (~150 frame-run) · 3 bug fixed + regression selftests. Liên quan: [[050726-ralph-pipeline-build]] · [[050726-ralph-loop-gate]].
