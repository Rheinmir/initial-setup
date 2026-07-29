---
type: issue
kind: architecture
title: "Dây chuyền sản xuất app khép kín kiểu Ralph: BR-kỹ → slice frames gắn-chặt-code → mỗi frame là loop có harness + monitor"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P1
tags: [issue, ralph, agent-loop, br, production-line, loop-runner, monitor, architecture]
timestamp: 2026-07-03
id: 030726-ralph-br-frame-production-line
source_session: "phiên frontier-gap-scan — user đề xuất dây chuyền Ralph + harness overstack"
---

# Issue: Dây chuyền sản xuất ứng dụng khép kín (Ralph BR→frame→loop) chạy trên harness overstack

## Vấn đề (một câu)
Xây một dây chuyền khép kín biến một **BR (bản yêu cầu) soạn cực kỹ** thành sản phẩm: BR được slice thành nhiều **frame nhỏ gắn chặt code** (nội dung + scope), mỗi frame chạy như một **loop có kỷ luật** (loop-harness + model), cộng thêm **monitor** — để "sản phẩm có vấn đề ⇔ BR có vấn đề", và mọi lỗi truy ngược được về đúng frame để sửa.

## Bối cảnh & bằng chứng
- Ý tưởng của user: (1) soạn BR kỹ tới mức mọi vấn đề sản phẩm đều quy về BR; (2) có great-BR rồi thì **slice thành nhiều frame nhỏ**; (3) frame **liên kết chặt với code** cả nội dung lẫn scope → lỗi ở đâu tìm đúng frame đó sửa. Ba phần này Ralph **đã làm được**.
- Phần CÒN THIẾU (việc của issue này): **monitor** + biến mỗi frame thành **agent làm việc có kỷ luật** bằng cách áp **loop-harness + model**. *harness ở đây chính là framework overstack của chúng ta* — đó là điểm ghép.
- Liên quan overstack: frontier-gap-scan (trục self-evolving-skills + observability), `loop-runner` (propose→verify→revise + termination guards), `propose`/`safe-change` (scope-guard), `wikieval`/`medic` (gate), `Workflow` journal (nguyên liệu monitor).

## Phạm vi
- Thiết kế dây chuyền: BR-authoring → slicer → frame-registry (map frame↔code) → per-frame loop (loop-runner) → monitor/observability.
- Đụng: `loop-runner`, `propose`, `Workflow`, ledger/wiki, và issue anh em [[030726-observability-runtime]] (monitor dùng chung).

## Không thuộc phạm vi
- Không thay Ralph nguyên bản; ta MƯỢN ý tưởng BR→frame và bọc bằng harness overstack.
- Không tự-merge output frame không qua gate (giữ người-trong-vòng-lặp).
- Không làm autonomous vô hạn — mọi loop phải có termination guard (loop-runner).

## Hướng gợi ý (không bắt buộc)
1. **BR-authoring**: chuẩn BR có acceptance-criteria kiểm-chứng-được (Ralph nhấn: spec testable là điều kiện để loop biết "xong"). Có thể là 1 skill `/br` hoặc mở rộng `propose`.
2. **Slicer**: cắt BR thành frame nhỏ, mỗi frame = {mục tiêu, scope code, acceptance-test}. Frame lưu như file (travel-được), có id gắn vào code (comment/anchor) để truy ngược.
3. **Per-frame loop = loop-runner**: mỗi frame chạy propose→verify(acceptance-test)→revise, termination bằng max_iter/no-progress. harness overstack = lớp kỷ luật.
4. **Monitor**: dùng `Workflow` journal + view timeline (issue [[030726-observability-runtime]]) để thấy frame nào đang loop/kẹt/fail, truy ngược lỗi→frame→BR.
5. **Khép kín**: lỗi runtime → map về frame (registry) → sửa frame → loop lại chỉ frame đó, không build lại toàn bộ.

## Tiêu chí HOÀN THÀNH
- 1 BR mẫu → slice ≥3 frame → mỗi frame chạy loop-runner tới khi acceptance-test xanh.
- Có registry frame↔code truy ngược được: cho 1 "lỗi", chỉ ra đúng frame + BR-clause.
- Monitor hiển thị trạng thái từng frame (đang chạy/kẹt/xong) từ journal.

## Assign & lý do
- @Rheinmir chủ; Claude dispatch (thiết kế + đụng nhiều skill lõi). Mở `/fdk`. P1 — đây là capability nền, ghép trực tiếp thế mạnh harness của overstack.

## Repo/paper tham khảo
- `snarktank/ralph` — Ralph gốc: loop chạy tới khi hết PRD item; có PRD skill sinh BR chi tiết (khớp "BR-kỹ → frame").
- `ghuntley/how-to-ralph-wiggum` + ghuntley.com/ralph, ghuntley.com/loop — phương pháp "everything is a ralph loop" (Geoffrey Huntley).
- `frankbria/ralph-claude-code` — bản Ralph cho Claude Code (intelligent exit detection — tham chiếu termination guard).
- `mikeyobrien/ralph-orchestrator` — bản cải tiến có orchestration (tham chiếu monitor/multi-frame).
- `vercel-labs/ralph-loop-agent` — "Continuous Autonomy for the AI SDK".
- `PageAI-Pro/ralph-loop` — long-running loop qua task-list.

## Origin
Raise bởi phiên frontier-gap-scan 2026-07-03 — user đề xuất dây chuyền Ralph + ghép harness overstack. Bằng chứng: WebSearch Ralph repos; frontier-gap-scan; [[030726-observability-runtime]].
