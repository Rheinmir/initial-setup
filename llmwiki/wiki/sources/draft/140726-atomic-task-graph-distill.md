---
type: issue
kind: feature-gap
title: "Distill Atomic Task Graph (arXiv 2607.01942): plan = DAG atomic task, sửa cục bộ subgraph thay vì replan cả plan, tái dùng subgraph"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, feature-gap, planning, dag, br, loop-runner, distill, paper]
timestamp: 2026-07-14
id: 140726-atomic-task-graph-distill
source_session: "phiên 2026-07-14 — user gửi arXiv 2607.01942, yêu cầu raise issue distill"
---

# Issue: Distill Atomic Task Graph thành năng lực planning cho overstack

## Vấn đề (một câu)
Dây chuyền `/br` hiện cắt BR thành **danh sách frame phẳng** chạy tuần tự, nên khi một frame hỏng ta không có cách nào biết frame nào *thật sự* là nguồn lỗi và phải sửa lại từ đầu chuỗi; paper Atomic Task Graph đưa ra một cấu trúc plan (DAG các tác vụ nguyên tử) cho phép chạy song song nhánh độc lập, khoanh vùng lỗi về đúng subgraph gây ra nó, và tái dùng subgraph đã tính — cả ba đều là thứ overstack đang thiếu.

## Bối cảnh & bằng chứng

**Paper**: *Atomic Task Graph: A Unified Framework for Agentic Planning and Execution* — Yue Zhang, Sihan Chen, Ziwen Huang, Hanyun Cui, Kangye Ji, Zhi Wang. arXiv 2607.01942, nộp 02/07/2026. PDF đã tải: `tool-results/webfetch-1784003450973-dj3js2.pdf` (phiên này).

Bốn cơ chế cốt lõi của ATG:

1. **Plan là DAG, node là tác vụ nguyên tử.** Một node được coi là "atomic" khi không thể chia nhỏ thêm mà vẫn còn thực thi được bởi agent — trên thực tế thường tương ứng với đúng một tool-call / một API call. Cạnh của đồ thị mã hoá quan hệ phụ thuộc. Đồ thị này là *tường minh*, nên phụ thuộc lộ ra cho cả người lẫn máy thấy, thay vì nằm ẩn trong chain-of-thought.
2. **Planning bằng phân rã đệ quy.** Mục tiêu cấp cao được chẻ đệ quy xuống các subtask nhỏ dần cho tới khi chạm đáy nguyên tử, thay vì bắt model đẻ ra một plan phẳng trong một lượt.
3. **Execution song song theo topological scheduler.** Các nhánh không phụ thuộc nhau chạy đồng thời; scheduler chỉ tôn trọng cạnh phụ thuộc. Đây là nguồn của phần "hiệu quả thực thi" trong kết quả.
4. **Error localization + localized repair.** Khi chạy hỏng, hệ định vị *thành phần subgraph nào* gây ra lỗi và chỉ tính lại vùng bị ảnh hưởng, thay vì replan toàn bộ. Cộng thêm **subgraph reuse**: các subgraph đã tính được cache và dùng lại giữa các lần plan, kể cả chuyển sang bài toán tương tự.

**Kết quả**: cải thiện nhất quán cả success rate lẫn hiệu quả thực thi trên WebShop, Mind2Web, ALFWorld, ScienceWorld; thắng baseline chain-of-thought và tree-of-thought **với backbone chỉ 7B–8B** — tức lợi ích đến từ *cấu trúc plan*, không phải từ model to hơn. Đây chính là điểm đáng distill: overstack không kiểm soát model, nhưng kiểm soát được cấu trúc plan.

**Limitations tác giả tự nêu** (phải mang nguyên vào khi absorb, đừng giấu): môi trường biến động mạnh; đồ thị rất lớn thì overhead scheduling ăn hết lợi; tool trả kết quả non-deterministic thì đồ thị mất tính chắc chắn.

**Vì sao đúng lúc với overstack** — ba chỗ ăn khớp trực tiếp:
- `/br slice` (xem [[050726-ralph-slice-frames]]): BR → frames hiện là *danh sách*, phụ thuộc giữa frame không được mã hoá. ATG nói: chính chỗ đó phải là DAG.
- `loop-runner`: retry hiện ở mức *iteration* — hỏng thì lặp lại cả vòng. ATG nói: retry đúng ra phải ở mức *subgraph hỏng*.
- `checkpoint-trace`: đã có rollback về mốc bất kỳ, nhưng rollback là "lùi thời gian", chưa phải "khoanh vùng nguyên nhân". Hai thứ bù nhau chứ không thay nhau.
- Khác và bù cho [[030726-orchestration-scale]] (GH#12): GH#12 lo *quy mô* chạy (hàng trăm subagent, verify, resume). Issue này lo *cấu trúc của plan* (DAG, sửa cục bộ, tái dùng). Không trùng; nếu làm cả hai thì DAG của issue này là thứ GH#12 đem đi scale.

## Phạm vi
- `br` (đặc biệt mode `slice` và `run`), `loop-runner`, và điểm nối sang `checkpoint-trace`.
- Universal (framework overstack), không phải local một dự án.
- Bước đầu bắt buộc: quyết định **kiểu absorb** theo taxonomy đã chốt — HÒA TAN (nhét cơ chế vào skill sẵn có) / KÉO NGOÀI (gọi ra công cụ ngoài) / NHÚNG-SỞ-HỮU (viết một skill mới của mình). Đọc paper rồi chọn *trước*, đừng vừa code vừa chọn.

## Không thuộc phạm vi
- Không tái hiện lại benchmark của paper (WebShop/Mind2Web/ALFWorld/ScienceWorld) — chúng ta không chạy agent benchmark, và con số của họ không chuyển sang domain của ta được.
- Không xây một engine đồ thị đa dụng. Nếu chỉ cần một trường `depends_on` trong frontmatter frame là đủ để có DAG, thì đó chính là câu trả lời — leo thang lên engine chỉ khi đo được là nó không đủ.
- Không đụng vào `orca` orchestration hiện có trong phạm vi issue này.

## Hướng gợi ý (không bắt buộc)
Ba mảnh, độc lập nhau, có thể lấy từng mảnh:
1. **DAG hoá frame** — cho `/br slice` sinh thêm `depends_on: [frame-id, ...]` cho mỗi frame; `/br status` vẽ đồ thị thay vì danh sách. Đây là mảnh rẻ nhất và mở khoá hai mảnh còn lại.
2. **Localized repair** — khi một frame fail, đi ngược cạnh phụ thuộc để tìm frame-nguồn thay vì rerun từ đầu; chỉ chạy lại subgraph bị ảnh hưởng.
3. **Subgraph reuse** — cache frame đã xanh theo hash của (clause + code touched); frame nào không đổi input thì bỏ qua, giống caching build.

Mảnh 1 gần như chắc chắn đáng làm. Mảnh 2 và 3 phải cân với limitations của chính paper (overhead scheduling, non-determinism) — với quy mô frame của ta (chục frame, không phải nghìn node) có khi mảnh 3 là YAGNI.

## Tiêu chí HOÀN THÀNH
- Có một quyết định absorb được ghi lại (HÒA TAN / KÉO NGOÀI / NHÚNG-SỞ-HỮU) kèm lý do, dưới dạng ADR hoặc concept trong wiki.
- `/br slice` sinh ra được frame có quan hệ phụ thuộc tường minh, và `/br status` đọc được quan hệ đó.
- Chứng minh được bằng một ca thật: một frame fail giữa chuỗi, hệ chỉ chạy lại đúng subgraph bị ảnh hưởng chứ không chạy lại toàn bộ — kèm log đối chứng số frame chạy lại trước/sau.
- Limitations của paper được ghi thẳng vào skill (không chỉ trong issue này), để người dùng sau biết khi nào cơ chế này *không* nên bật.

## Assign & lý do
@Rheinmir chủ; Claude dispatch; mở bằng `/fdk` vì đây là sửa chính framework (skill `br`/`loop-runner`). P2 — không chặn việc gì đang chạy, nhưng đánh trúng điểm đau đã thấy trong dây chuyền BR hiện tại (frame fail thì phải chạy lại nhiều hơn mức cần).

## Origin
Raise bởi phiên 2026-07-14 khi user gửi `https://arxiv.org/pdf/2607.01942` và yêu cầu raise issue distill. Bằng chứng: abstract + toàn văn PDF của arXiv 2607.01942 (đã fetch trong phiên); đối chiếu với [[050726-ralph-slice-frames]] và [[030726-orchestration-scale]] trong ledger.
