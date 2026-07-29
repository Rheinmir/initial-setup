---
type: draft
title: Nghiệm thu output dây chuyền /br — app Payroll (council 3 ghế + harass)
status: proposed
tags: [br, nghiem-thu, council, evaluation, payroll, output]
timestamp: 2026-07-12
---

# 120726-nghiem-thu-output
**Status:** proposed · **App chạy:** http://localhost:8770/ · **Ngày:** 2026-07-12

Đánh giá thành phẩm dây chuyền `/br` = app Payroll (31 frame). Nguồn: council 3 ghế (output · DX · kiến trúc) + harness-doctor harass + nghiệm thu trực tiếp.

## Harass (harness-doctor)
**17/17 rail cắn** — mọi luật gác active. 1 advisory hạ tầng: pre-commit chưa cài trong `.git/hooks` (python vs python3).

## Council — chairman synthesis

### Điểm mạnh (thật, có bằng chứng)
- **30/30 test module PASS**; UI `app/p28_ui.py` nối THẬT engine (p03/p06/p07/p12/p22/p25/p26/p27/p29/p30), không mock. Số lấy từ `payroll_master`/`cong_tho` thật.
- Tab "Công thức lương" là sandbox chạy-thử trace theo dependency từ `p30.compute`, nguồn Excel ghi rõ — hiếm ở tier demo. Import CSV có validate, theme persist, stdlib-only.
- **Bộ gác code-enforced thật:** verify=exit-code + test-hash fail-closed + FLAKY re-run (chặn 3 kiểu gian lận green); diff-jail + FINAL SCOPE SWEEP → `changed_files ⊆ scope_code` bất kể loop dừng cách nào; R6 + manifest-từ-chối-khi-collision → spine sai không bao giờ sinh ra.

### Điểm yếu (chặn "production")
1. **Contract từng lệch app thật** (`/cham-cong` vs `/bang-cong`) — **ĐÃ FIX phiên này**: `ui-layout.yaml` reconcile về 11 route thật, contract regenerate 0 lệch.
2. **Khúc rủi ro nhất (#40 map-not-territory) CHƯA build:** T2 assemble diff ground-truth, T4 localizer, T5 adversarial, T6/T7 — vẫn `pending`. Hiện chỉ có spine (T1) + R8 + R9. `app/pipeline.py` raise `NotImplementedError` (chặn bởi ground-truth Excel).
3. **Gác ở mức FILE, không mức SYMBOL** dù doc hứa "symbol→frame". Localizer T4 cần granularity symbol mà lint chưa có.
4. **R9 assumption-gate mỏng** (fail-open, opt-in `--ship`, chỉ đọc block có cấu trúc). **Diff-jail fail-OPEN khi không có git.**
5. **Che-tiền không auth thật:** role lấy từ `?role=` query — bỏ param là thấy hết. Không phải access-control production.
6. **Rác cây:** `serve.py` là stub chết (entrypoint thật `_run_app.py`), `frame-p08-*.failed.patch` còn sót.

### DX (người kế nhiệm) — xem [[120726-pipeline-friction]]
Trung bình-khó: gác chắc + docs payroll tốt, nhưng thiếu quickstart happy-path, hub lệnh thống nhất, glossary, `br doctor`; 8+ tool gạch-nối + `--root .` dễ sai.

## Verdict nghiệm thu
**ĐẠT-CÓ-ĐIỀU-KIỆN.** App chạy thật, engine+test+UI vượt mức demo, bộ gác là thật. CHƯA "production" vì: pipeline lắp ráp p99 còn NotImplementedError (thiếu ground-truth Excel), gác mức file chưa mức symbol, che-tiền chưa auth, còn rác cây.

## Việc tiếp (ưu tiên, từ council)
1. **G2 `/br reverse`** (nuốt G1) — phép nghịch đang thiếu thật, linchpin cho clone/onboard→pipeline.
2. Build T2 assemble khi có **ground-truth Excel** (mở khoá p99 + T4 localizer).
3. Nâng gác lên mức symbol; vá diff-jail fail-open-khi-no-git; R9 thành cổng cứng hơn.
4. DX: `br/QUICKSTART.md` + glossary + `br doctor`; dọn serve.py stub + .failed.patch.
5. G3 `/modularize`: council chấm nửa-YAGNI (memos-specific) → **defer/bỏ**.

## Origin
Council 3 ghế + harness-doctor + nghiệm thu trực tiếp app :8770, phiên 2026-07-12.
