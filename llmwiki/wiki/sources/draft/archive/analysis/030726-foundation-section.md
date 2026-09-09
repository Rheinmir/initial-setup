---
type: issue
kind: foundation
title: "Mọi wiki thiếu mục Foundation — bài toán · vì sao tồn tại · vì sao chọn công nghệ"
status: done
assignee: phiên /fdk kế (framework-dev)
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, foundation, wiki-template, overstack, onboarding]
timestamp: 2026-07-03
id: 030726-foundation-section
source_session: "Phiên 2026-07-03 hỏi vai trò YAML vs Python → council-026 phát hiện gap nền tảng"
---

# Issue: Foundation section phổ quát cho mọi wiki

## Vấn đề (một câu)
Mọi wiki dựng bằng overstack (kể cả `overstack.html`) thiếu một mục **Foundation** trả lời ba câu gốc — *dự án giải quyết bài toán gì, vì sao nó tồn tại, vì sao chọn các công nghệ này* — nên tri-thức "vì sao" nằm rải rác trong ADR/commit/đầu người thay vì một chỗ người mới đọc đầu tiên.

## Bối cảnh & bằng chứng
- Phát sinh khi user hỏi "file YAML đóng vai trò gì, khác Python chỗ nào". Câu trả lời đúng tồn tại (policy-as-data, ADR-001) nhưng **không có chỗ canonical** để một dev mới đọc — phải hỏi mới ra.
- Council-026 (blind peer-rank, 5 lăng kính) hội tụ: executor giỏi giải thích *đã-chọn-gì* nhưng thiếu tầng *vì-sao-nền-tảng*. Report: `llmwiki/html/council/council-report-026-seed42.html`.
- Báo cáo minh hoạ vấn đề: `llmwiki/html/030726-yaml-vs-python.html` — đây chính là loại nội dung lẽ ra thuộc mục Foundation nhưng đang là report rời.
- Liên quan: `[[ADR-001]]` (policy-as-source-of-truth), `[[ADR-004]]` (framework-dev context opt-in — Foundation phải travel qua trụ được distribute, không nhét context mọi phiên).
- Đây KHÔNG riêng overstack: bất kỳ dự án nào cài llmwiki đều cần Foundation của CHÍNH nó.

## Phạm vi
- **Universal**: một section/template Foundation chuẩn, seed khi bootstrap dự án mới (như problem-tree travel-kit ở `[[020726-orca-issue-ledger-travel]]`).
- Chạm: generator `fdk/tools/build-overstack-docs.py` (thêm tab/section Foundation derive từ nguồn khai báo), template wiki (`concepts/` hoặc `architecture/`), install/bootstrap seed.
- Nguồn Foundation nên là **dữ liệu khai báo** (giống mechanisms.yaml) để overstack.html *derive* chứ không chép tay — tránh drift.

## Không thuộc phạm vi
- Không viết lại nội dung ADR đã có — chỉ tổng hợp/liên kết vào một mặt Foundation.
- Không đụng logic enforcement/validator.
- Không làm cho dự án ngoài (chỉ template + overstack của repo này trước).

## Hướng gợi ý (không bắt buộc)
- File nguồn khai báo `foundation.yaml` (problem / why-exists / tech-choices[{tech, role, why, alternatives-rejected}]) → generator render tab "Nền tảng" trong overstack.html + trang wiki.
- Mỗi tech-choice link tới ADR/report/council làm bằng chứng (vd YAML→ADR-001+council-026).
- Bootstrap seed `foundation.yaml` rỗng-có-placeholder khi cài dự án mới.

## Tiêu chí HOÀN THÀNH
1. `overstack.html` có mục Foundation trả lời đủ 3 câu gốc, **derive** từ nguồn khai báo (sửa nguồn → trang đổi, không chép tay).
2. Có template Foundation seed được khi bootstrap dự án mới.
3. Ít nhất 2 tech-choice (vd YAML, Python) có `why` + `alternatives-rejected` + link bằng chứng.
4. medic/harness-doctor có probe: nếu `foundation.yaml` khai một mục mà trang vắng → cắn (giống narrative-as-data).

## Assign & lý do
- **assignee**: phiên `/fdk` kế — đây là framework-dev (đụng generator + template + bootstrap), đúng cửa ADR-004.
- **dispatch Claude**: việc substance, cần hiểu cả hệ (derive-not-copy, travel-kit, probe).
- **entry /fdk**: mở bằng front-door framework-dev, không phải propose feature dự án thường.

## Kết quả (2026-07-04)
Đã thực hiện theo `[[030726-foundation-section-PLAN]]` (fable lên plan, opus triển khai):
- `harness/foundation.yaml` — nguồn khai báo thật (problem / why-exists / 2 tech-choice YAML+Python, mỗi mục có why + alternatives-rejected + evidence-link tồn tại).
- `harness/templates/foundation-template.yaml` — bản seed placeholder cho dự án mới.
- `fdk/tools/build-overstack-docs.py` — `load_foundation()` + tab "01 · Nền tảng" DERIVE từ manifest (không chép tay); regen `llmwiki/html/overstack.html`.
- `fdk/tools/medic.py` — probe `p_foundation` (drift + "manifest nói dối" + warn khi toàn TODO); đăng ký vào `PROBES`.
- Seed không-đè trong `install-harness.sh` + `poc-vendor-neutral/install.sh`.
- Verify: medic 0 fail; 2 mutation test (drift/nói-dối → fail) + placeholder (→ warn) đạt. Đủ 4 tiêu chí HOÀN THÀNH.

## Origin
Raise bởi skill `/raise-issue` trong phiên 2026-07-03. Nguồn: câu hỏi user về vai trò YAML/Python → council-026 (`llmwiki/html/council/council-report-026-seed42.html`) phát hiện gap nền tảng; báo cáo minh hoạ `llmwiki/html/030726-yaml-vs-python.html`. Chưa thực hiện — cố ý defer cho phiên /fdk kế.
