---
name: orca-issue
description: Vòng xử lý SỰ CỐ first-class — dùng khi có bug, lỗi runtime, hành vi sai, "approve treo", regression, incident production. Điều phối triage → repro-first gate (chưa tái hiện được thì CHƯA được sửa) → khoanh vùng (code-graph/impact-check/bisect) → fix qua safe-change với bằng chứng đỏ→xanh → distill kép (wiki incident + failure-flywheel + problem-tree). KHÔNG dùng cho tính năng mới (đó là propose/orca-workflow).
---

# Skill: orca-issue — vòng xử lý sự cố

Khác vòng làm-tính-năng ở hai chốt cứng: **không tái hiện được thì không sửa**, và **không đỏ→xanh thì không đóng**. Skill này điều phối đồ nghề đã có (impact-check, safe-change, verify-before-commit, failure-flywheel) — không làm lại chúng.

## When to use
- Bug, lỗi runtime, regression, hành vi sai so với mong đợi, incident production.
- User nói: "lỗi rồi", "bị bug", "chạy sai", "hôm qua còn chạy", "trace lỗi này", "/orca-issue".
- KHÔNG dùng khi: yêu cầu tính năng/thay đổi mới → `propose` / `orca-workflow`.

## Steps — 5 chốt tuần tự, không nhảy cóc

1. **Triage** — chép lại triệu chứng bằng 1–2 câu (cái gì sai, thấy ở đâu, từ bao giờ); thu log/screenshot/bối cảnh; phân mức (chặn việc / khó chịu / thẩm mỹ). Chưa rõ triệu chứng → hỏi user, đừng đoán.
2. **Repro-first GATE (chốt cứng #1)** — viết script/test tái hiện lỗi, chạy ra kết quả **ĐỎ** (fail) và lưu lại làm bằng chứng (file test hoặc script + output). **Chưa có repro đỏ thì DỪNG ở đây** — không bàn nguyên nhân, không sửa. Lỗi không tái hiện được (flaky/heisenbug) → ghi rõ điều kiện đã thử, hạ xuống chế độ giám sát (thêm log/probe), không sửa mò.
3. **Khoanh vùng** — dùng đồ nghề định vị thay vì grep mù: code-graph (`get_callers`/`get_symbol_context`), `impact-check` để map ai phụ thuộc vùng nghi vấn, `git bisect`/`git log` khi nghi regression theo thời gian. Kết quả: 1 câu "root cause nằm ở X vì Y".
4. **Fix red→green (chốt cứng #2)** — sửa qua `safe-change` (code dùng chung thì map caller trước), surgical đúng vùng đã khoanh. Chạy lại repro ở bước 2: phải chuyển **ĐỎ → XANH**; chạy thêm test/verify sẵn có của dự án; chốt bằng `verify-before-commit`. Repro còn đỏ = chưa xong, quay lại bước 3 — không được "chắc là được rồi".
5. **Distill kép** — sau khi commit: (a) trang wiki incident vào `llmwiki/wiki/sources/` (triệu chứng, root cause, fix, kèm `## Origin` trỏ commit + repro); (b) record vào `failure-flywheel` để lỗi lặp đủ ngưỡng tự đề xuất rule/skill; (c) dự án có problem-tree (`llmwiki/html/problem-tree.html` hoặc `fdk-problem-tree.html`) → thêm/flip node tương ứng.

## Rules
- **Không repro, không sửa** — mọi fix phải truy được về một bằng chứng đỏ đã lưu. Fix không có repro là fix mò, bị trả lại.
- **Không xanh, không đóng** — lời agent không phải bằng chứng; chỉ repro chuyển xanh + verify pass mới được đóng.
- **Surgical** — chỉ chạm vùng đã khoanh ở bước 3; thấy code lân cận "muốn dọn" thì ghi chú, không dọn trong vòng sự cố.
- **Distill là bắt buộc, không phải lịch sự** — vòng chưa xong khi chưa ghi wiki + flywheel; đây là cách lỗi hôm nay thành rào chắn ngày mai.
- Sự cố nặng cần nhiều người/agent → escalate sang `orca-workflow` để dispatch, nhưng các chốt 2 và 4 vẫn giữ nguyên.
- **Đọc thông báo lỗi NGUYÊN VĂN trước khi đoán** (superpowers systematic-debugging) — error message + stack trace là dữ kiện rẻ nhất; triage mà chưa trích nguyên văn lỗi là đang đoán.
- **Một hypothesis một lần** — mỗi vòng chỉ đổi MỘT thứ rồi chạy lại repro; đổi nhiều thứ cùng lúc (shotgun-fix) thì xanh cũng không biết vì sao xanh.
- **3 fix liên tiếp thất bại → dừng, nghi ngờ TẦM kiến trúc** — không thử fix thứ 4 cùng cỡ; quay lại bước 3 với giả thuyết to hơn (sai tầng, sai component, sai giả định nền).

## Origin
- **Absorb 2026-07-17 (adapt_mode: dissolve, T-260717-02):** 3 chốt cuối (đọc lỗi nguyên văn · một hypothesis một lần · 3-fail-nghi-kiến-trúc) distill từ `obra/superpowers` (`systematic-debugging` — Iron Law + Four Phases). Các chốt trùng vòng sẵn có (repro-first, root-cause, red→green) KHÔNG absorb lại. Clone sẵn trong scratchpad/superpowers.
