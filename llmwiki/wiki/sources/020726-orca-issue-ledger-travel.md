---
type: draft
title: "orca-issue loop + problem-tree travel (p-02, p-04)"
status: implemented
tags: [propose, orca-issue, problem-tree, distribution, systems-thinking]
timestamp: 2026-07-02
id: 020726-orca-issue-ledger-travel
---

# 020726-orca-issue-ledger-travel
**Status:** implemented
**Task:** T-260702-01
**Sequence diagram:** [020726-orca-issue-ledger-travel-seq.html](../../html/020726-orca-issue-ledger-travel-seq.html)

## Context

Query wiki trước khi draft (R7-f):

- **`ADR-004`** (`fdk/wiki/sources/adr/ADR-004-framework-dev-context-opt-in.md`): context nội-bộ-framework là opt-in qua /fdk, KHÔNG auto-bơm và KHÔNG distribute — đây chính là lý do p-04 tồn tại: quy tắc problem-tree đang nằm trong fdk nên không travel theo dự án. Lời giải phải cưỡi trên trụ ĐƯỢC distribute (skill loop trong `llmwiki/skills/`, hook harness) chứ không được nhét thêm context framework vào mọi phiên.
- **`ADR-005`** (logger-and-capabilities-travel-downstream): tiền lệ đúng cho "thứ gì cần travel thì đi cùng harness/hooks khi bootstrap" — R17 flush trong `session_end.py` đã tự travel theo cơ chế này.
- **Skill hiện có** (LOOP_MAP trong `llmwiki/CLAUDE.md`): `failure-flywheel` (gom lỗi lặp → rule), `loop-runner` (vòng fix có guard), `trace-grader` (chấm đường đi), `safe-change`/`verify-before-commit` (đường ray sửa code) — orca-issue KHÔNG làm lại các mảnh này, chỉ điều phối chúng theo thứ tự issue-specific. `orca-workflow` là entry point chính user gọi hằng ngày.
- **Ledger problem-tree** (`llmwiki/html/fdk-problem-tree.html`, rule R16/R17 vừa thêm, skill fdk § Problem-tree): p-02 và p-04 là hai node đỏ 0/3 đang chờ chính proposal này.
- **Eval 020726** (`sources/draft/020726-eval-report.md`): khuyến cáo KHÔNG gắn nghĩa vụ ledger vào verify-before-commit (no-op tốn token ở mọi commit dự án thường) — gắn vào nhánh framework của orca-workflow + hook tất định.

## Restate

Một câu: tạo skill điều phối `orca-issue` (vòng xử lý sự cố: bắt buộc tái hiện được lỗi trước khi sửa, sửa xong phải chứng minh đỏ→xanh, và đúc kết kép về wiki + failure-flywheel), đồng thời làm cho convention problem-tree đi theo MỌI dự án cài overstack (không chỉ máy có fdk).

## Impact — file/module bị chạm

| # | File | Thay đổi |
|---|------|----------|
| 1 | `skills/orca-issue/SKILL.md` (MỚI) + mirror `llmwiki/skills/orchestrate/orca-issue.md` | skill điều phối mới |
| 2 | `llmwiki/CLAUDE.md` + `llmwiki/AGENT.md` (bảng LOOP_MAP) | thêm hàng orca-issue |
| 3 | `fdk/CAPABILITIES.md` | regenerate bằng build-capabilities.py |
| 4 | `skills/orca-workflow/SKILL.md` + mirror | thêm 2 đoạn ngắn: (a) nhánh "issue → gọi orca-issue", (b) convention problem-tree project-local |
| 5 | `harness/poc-vendor-neutral/bootstrap.sh` hoặc `install.sh` | seed `llmwiki/html/problem-tree.html` template rỗng khi cài dự án mới |
| 6 | `llmwiki/.claude/hooks/session_end.py` | generalize path: ưu tiên `fdk-problem-tree.html` (repo framework), fallback `problem-tree.html` (downstream) |
| 7 | `llmwiki/wiki/concepts/problem-tree.md` (MỚI) | concept wiki — trụ llmwiki cho p-03/p-05 |

## Side effects — có thể vỡ gì

- **orca-workflow phình**: thêm 2 đoạn phải NGẮN (≤10 dòng mỗi đoạn) — skill này mọi dự án nạp, phình là tăng token mọi phiên. Guard: đếm dòng trước/sau.
- **session_end.py chạy ở downstream không có tree** → đã fail-open (`if not tree.is_file(): return`), thêm fallback tên file thứ hai không đổi hành vi cũ.
- **bootstrap seed file** có thể ghi đè tree đang có ở dự án cũ → guard `[ -f ... ] ||` chỉ seed khi chưa tồn tại.
- **R16 validator** hiện chỉ khớp `llmwiki/html/` — downstream giữ nguyên layout llmwiki nên không cần đổi glob.
- orca-issue là skill MỚI — không caller cũ nào vỡ. "No existing behaviour removed."

## Plan

- [x] **T1 — Skill `orca-issue`**: scaffold bằng `fdk/tools/new-skill.py orca-issue`; SKILL.md gồm 5 gate tuần tự: (1) triage & mô tả triệu chứng, (2) **repro-first gate** — phải có script/test tái hiện fail (commit làm bằng chứng) mới được bàn fix, (3) khoanh vùng bằng code-graph/`impact-check`/git bisect, (4) fix qua `safe-change` → repro chuyển đỏ→xanh (verify tất định) → `verify-before-commit`, (5) **distill kép**: trang wiki incident (có `## Origin`) + record `failure-flywheel` + node problem-tree.
- [x] **T2 — Register orca-issue**: mirror + LOOP_MAP (CLAUDE.md/AGENT.md) + regenerate CAPABILITIES; sync bằng `fdk/tools/sync-skill.sh`.
- [x] **T3 — orca-workflow nối 2 đoạn**: (a) đầu vào là *sự cố* (bug/lỗi runtime) → route sang `orca-issue` thay vì propose; (b) convention problem-tree: dự án có `llmwiki/` thì ledger nằm ở `llmwiki/html/problem-tree.html`, cập nhật khi phát hiện/giải vấn đề quy trình.
- [x] **T4 — Travel kit**: seed template problem-tree rỗng trong bootstrap/install (guard không ghi đè); generalize `session_end.py` fallback `problem-tree.html`; test lại 3 ca flush trong sandbox.
- [x] **T5 — Trụ llmwiki**: viết `concepts/problem-tree.md` (concept + cách đọc màu/scope + trigger R16/R17); index + log; flip ledger: p-02 → solved (scope theo thực tế sau merge), p-04 → solved, p-03/p-05 → 3/3 nếu concept wiki đủ.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 skill orca-issue | Claude (session này) | thiết kế gate/logic — việc substance, cần hiểu cả hệ | done |
| T2 register + sync | Claude (session này) | đụng LOOP_MAP/CAPABILITIES — cần chính xác, rẻ vì đã có tool | done |
| T3 orca-workflow 2 đoạn | Claude (session này) | skill mọi dự án nạp — sửa phải surgical, đếm dòng | done |
| T4 travel kit (bash+py) | OpenCode `big-pickle` | mechanical: sed/copy + test sandbox có sẵn kịch bản 3 ca | done |
| T5 concept wiki + ledger flip | OpenCode `big-pickle` | render từ nội dung đã chốt trong draft này — việc chép có khuôn | done |

## Success criteria

1. `/orca-issue` xuất hiện trong CAPABILITIES + LOOP_MAP; gọi thử với 1 bug giả → skill chặn ở gate 2 khi chưa có repro (kiểm chứng được).
2. Repo mới cài bằng bootstrap có sẵn `llmwiki/html/problem-tree.html` + hook flush hoạt động (sandbox test 3 ca pass).
3. Sửa dự án downstream KHÔNG cần biết fdk vẫn được nhắc ledger qua orca-workflow — đọc SKILL.md orca-workflow thấy convention.
4. Ledger: p-02, p-04 hết đỏ; p-03, p-05 đạt 3/3 xanh lá (lần đầu có node xanh thứ hai sau p-01).
5. orca-workflow tăng ≤ 20 dòng tổng.

## Render brief

- **T1**: participants User, orca-issue, repro-script, code-graph, safe-change, wiki+flywheel. Steps: User báo bug (legacy) → orca-issue mở triage (add) → GATE repro: chưa có script fail → BLOCK quay lại yêu cầu repro (block) → repro đỏ commit (add) → khoanh vùng code-graph (add) → fix qua safe-change (add) → repro xanh + verify (add) → distill kép wiki + flywheel + ledger (add). Prose: vòng đời sự cố với hai chốt cứng — không repro không sửa, không xanh không đóng; đúc kết kép để lỗi lặp tự sinh guardrail.
- **T2**: participants new-skill.py, SKILL.md, mirror, LOOP_MAP, CAPABILITIES. Steps: scaffold (add) → viết SKILL (add) → sync-skill.sh (add) → build-capabilities (add) → kiểm parity (add). Prose: đăng ký đủ 4 bề mặt để router tìm thấy skill; sync bằng tool mới, không cp tay.
- **T3**: participants User, orca-workflow, orca-issue, problem-tree. Steps: User mô tả việc (legacy) → orca-workflow phân loại: feature → propose (legacy); sự cố → route orca-issue (add) → cuối vòng: chạm vấn đề quy trình → nhắc cập nhật problem-tree project-local (add). Prose: entry point hằng ngày biết rẽ nhánh; convention ledger nằm ở skill được distribute nên travel theo dự án — trả lời trực diện p-04.
- **T4**: participants bootstrap.sh, project mới, session_end.py, problem-tree.html. Steps: cài overstack (legacy) → seed template nếu chưa có (add) → phiên làm việc chạm framework surface (legacy) → SessionEnd flush: tree fdk? → fallback problem-tree.html (add) → stub pending ghi bằng code (add); tree không tồn tại → fail-open bỏ qua (block). Prose: đích "tắt app bình thường thì cây vẫn đúng chỗ" giờ đúng ở CẢ dự án downstream.
- **T5**: participants concepts/problem-tree.md, index, log, ledger. Steps: viết concept (add) → index+log (add) → flip p-02/p-04, nâng p-03/p-05 (add) → R16 kiểm HTML có path (legacy). Prose: trụ tri thức khép vòng — phiên sau query wiki là hiểu ledger không cần đọc code.

## Origin
- **Draft:** `wiki/sources/draft/020726-orca-issue-ledger-travel.md`
- **Nguồn vấn đề:** ledger `llmwiki/html/fdk-problem-tree.html` node p-02, p-04 (session 020726) + eval `020726-eval-report.md`
- **Commit:** 49d2361 — feat(harness+skills): problem-tree ledger đủ 3 trụ + vòng orca-issue (T-260702-01)
- **Date promoted:** 2026-07-02
