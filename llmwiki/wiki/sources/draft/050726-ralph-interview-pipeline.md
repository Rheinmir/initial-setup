---
type: draft
title: ralph-interview-pipeline — bản đồ entity dây chuyền + step Interview (GH#15)
status: proposed
tags: [ralph, br, interview, pipeline, production-line, issue-15]
timestamp: 2026-07-05
---

# 050726-ralph-interview-pipeline

**Status:** proposed
**Issue:** GH#15 · kế thừa council 028 (go thin-slice) + council 031/032 (plan loop v1 đạt-có-điều-kiện, 6 sửa bắt buộc).
**Bản review cho người:** `llmwiki/html/050726-ralph-interview-pipeline.html` (Sequence diagram + entity map nằm trong đó).

## What
Vẽ trọn bản đồ entity nghiệp vụ của dây chuyền Ralph (bước gì → bước gì) và thi công BƯỚC ĐẦU TIÊN: **Interview** — từ tài liệu thô của user (`raw/`) + một bộ specs chuẩn tham chiếu, sinh bộ câu hỏi hỏi-bù-phần-thiếu (HTML xem theo section + MD có cấu trúc để điền), cho phép lens chuyên gia điền thay mục user không chắc (đánh dấu assumed, fail-fast).

## Entity map (9 entity, thứ tự dây chuyền)

| # | Entity | Vật chứa (file) | Sinh bởi | Ghi chú |
|---|--------|-----------------|----------|---------|
| E1 | RAW — tài liệu thô | `llmwiki/raw/` (đã có convention; agent KHÔNG ghi) | user vứt vào | mọi định dạng, không cấu trúc |
| E2 | SPEC TEMPLATE — bộ specs chuẩn mọi project | `br/spec-template.md` (versioned, `schema_version`) | thi công đợt này | 10 section S1–S10, mỗi field có id |
| E3 | SPEC-FILLED (partial) | `br/spec-filled.md` | agent extract từ E1 map vào E2 | mỗi field ghi provenance `raw:<file>` |
| E4 | QUESTIONNAIRE — bộ câu hỏi hỏi bù | `br/interview/NNN-questions.html` (xem) + `NNN-answers.md` (điền) | gap-diff E2−E3 | chỉ hỏi phần THIẾU/mâu thuẫn |
| E5 | ANSWERS | chính `NNN-answers.md` sau khi điền | user điền HOẶC lens-fill | lens-fill đánh dấu `filled_by: lens-<tên>` + `verified: false` |
| E6 | BR — bản yêu cầu compile | `br/BR.md` | compile E3+E5 | mỗi clause có `clause_id` + provenance `raw\|user\|lens-assumed` |
| E7 | FRAME | `br/frames/frame-NNN.md` | slice từ E6 (schema v0 council 031/032) | đợt sau |
| E8 | RUN-LOG + GATE | loop-runner run-log JSON + medic + người duyệt | loop v1 (đã council) | đợt sau |
| E9 | MONITOR | timeline từ journal (GH#11) | đợt sau | |

**Flow:** E1 →(extract)→ E3 →(gap-diff với E2)→ E4 →(user điền / lens-fill)→ E5 →(compile)→ E6 →(slice)→ E7 →(loop)→ E8 →(quan sát)→ E9.
**Feedback loop khép kín (Meadows):** lỗi sản phẩm → truy `clause_id` → clause provenance = `lens-assumed` → tự sinh câu hỏi interview vòng sau (assumption sai thành câu hỏi thật, không thành bug lặp).

## Spec template — 10 section chuẩn (S1–S10)
S1 Tầm nhìn & bài toán · S2 Người dùng & vai trò · S3 Luồng nghiệp vụ chính · S4 Chức năng (feature + acceptance từng cái) · S5 Dữ liệu (entity/field) · S6 Tích hợp ngoài · S7 Non-functional (hiệu năng/bảo mật/quyền) · S8 Ràng buộc (tech/hạn/ngân sách) · S9 Out-of-scope · S10 Acceptance tests tổng (kiểm-chứng-được — điều kiện để frame slice được).
Mỗi field: `id` (vd `S4.2`), `required: yes/no`, `status: filled|missing|conflict|assumed`.

## Bộ slash — HUB MỘT TÊN: `/br`
Theo nguyên tắc hub 1-tên (user chỉ mô tả phạm vi, không nhớ lệnh con). Gõ được bằng cơ bắp: `br`.
- `/br interview` — bước này (đợt 1): đọc raw/ → extract → gap-diff → sinh questions.html + answers.md; flag tuỳ chọn "lens-fill các mục tôi không chắc".
- `/br compile` — E5→E6 (đợt 1, phần cuối).
- `/br slice` · `/br run <frame>` · `/br status` — đợt sau (mapping sang loop v1 + monitor).

## Plan (đợt 1 — chỉ Interview, thin-slice)
1. **spec-template**: viết `br/spec-template.md` (S1–S10, field-id, schema_version: 0).
2. **skill `/br`** (mode interview): scaffold bằng `new-skill`; Steps: (a) quét `llmwiki/raw/` (chỉ đọc), (b) extract → `br/spec-filled.md` với provenance từng field, (c) gap-diff → sinh `br/interview/001-questions.html` (theo section, giải nghĩa thuật ngữ, R16 full-path) + `001-answers.md` (block điền theo field-id), (d) nếu user bật lens-fill: bốc lens qua `council.py roster --case product`, điền các mục user đánh dấu "không chắc", mỗi mục ghi `filled_by` + `verified: false`, (e) STOP chờ user điền/duyệt.
3. **`/br compile`**: đọc answers.md đã điền → `br/BR.md` với clause_id + provenance; mục `assumed` gom vào bảng "Giả định đang gánh" đầu BR (fail-fast: thấy ngay đang cược gì).
4. **Chạy thử trên 1 project mẫu thật** (chọn khi thi công — repo có sẵn tài liệu thô), demo lens-fill 1 section.
5. Register skill (mirror + LOOP_MAP + bảng AGENT/CLAUDE + CAPABILITIES) + medic --ci + cập nhật ledger #15 + problem-tree p-22.

**DoD đợt 1:** từ 1 folder raw thật → ra questionnaire HTML + answers MD đúng cấu trúc; lens-fill hoạt động và bị đánh dấu assumed; compile ra BR.md có clause_id + bảng giả định; toàn bộ file-first, không hook auto-fire (ADR-004).

**Không thuộc phạm vi đợt 1:** slicer tự động, loop chạy frame (đợt 2 — theo plan v1 council 031/032 với 6 sửa bắt buộc), monitor HTML (#11).

## Rủi ro
- **Lens-fill = xanh giả cấp specs** (tương tự rủi ro Taleb ở cấp code): mọi mục lens điền BẮT BUỘC `verified: false` + hiện trong bảng "Giả định đang gánh"; không bao giờ trộn lẫn với câu trả lời thật của user.
- Spec template phình → interview dài lê thê: required-field giữ tối thiểu, phần còn lại optional; câu hỏi CHỈ sinh cho field missing/conflict.

## Agent Task Assignment
- Claude (phiên /fdk, nhánh `Rheinmir/issue-15-br-k`): thi công đợt 1 (bước 1–5 ở Plan) sau khi user duyệt proposal này qua `/propose`.
- User: duyệt proposal; cung cấp/chọn project mẫu có raw docs; điền answers hoặc bật lens-fill.

Sequence diagram: xem `llmwiki/html/050726-ralph-interview-pipeline.html` (section "Sequence — một vòng interview").

## Origin
Phiên planning GH#15 2026-07-04→05 (nhánh issue-15-br-k): council 031/032 chốt loop v1; user chỉ đạo tiếp: vẽ entity business + thiết kế step Interview (raw-folder → specs chuẩn → hỏi bù → HTML preview + MD điền → lens-fill fail-fast → bộ slash). Liên quan: [[030726-ralph-br-frame-production-line]] · GH#15 · council-report-032.
