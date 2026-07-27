---
type: draft
title: "Bản đối soát 17 task orchestration treo — verdict, bằng chứng, độ chắc"
status: proposed
tags: [orchestration, orca, triage, reconcile, dispatch]
timestamp: 2026-07-20
task: T-260720-01
---

# 200726-orchestration-triage

**Status:** ĐÃ XÁC MINH quy thuộc — user xác nhận nhóm B **không liên quan dự án này** (2026-07-20)
**Task:** `T-260720-01` (T4)
**Công cụ:** `harness/scripts/orca-reconcile.py`

## Vì sao bản này tồn tại

Đo ngày 2026-07-20: 59 task orchestration, **17 chưa kết thúc**, cũ nhất **59 ngày**. Trong đó **14 task chưa bao giờ được dispatch** (`dispatch: null`) — không phải worker chết, mà **chưa ai giao**.

Gốc đã tìm ra và đã vá ở T1: coordinator không biết lúc nào worker xong (`orca terminal wait --for tui-idle` timeout 90 giây trên việc xong sau 9 giây), nên bỏ cuộc và tự làm inline. Nay `orca-dispatch.py` phát hiện kết thúc trong ~9s trên 2 vendor, nên lựa chọn "mở lại" mới thực sự có nghĩa.

## Nguyên tắc triage

Chép từ chính proposal T-260720-01, nhánh amber bước 6 của T4: **không bao giờ xoá một thứ mình không hiểu.** Task nào tôi không kiểm chứng được thì để **GIỮ**, ghi rõ thiếu bối cảnh, chứ không đoán.

## Nhóm A — đóng được, có bằng chứng cứng (3 task)

Đây là các task mà **việc đã hoàn thành ở nơi khác**, task chỉ còn là vỏ rỗng chưa ai đóng.

| Task | Tuổi | Việc | Bằng chứng đã xong | Verdict |
|---|---|---|---|---|
| `task_7a605c4ff70f` | 18d | query-retrieval-eval: telemetry + eval + L1 3-tầng | `[[query-retrieval-eval]]` ghi `status: implemented`, commit `632e29c`; `harness/scripts/retrieval-eval.py` + `query-log.py` + `query-proxy.py` đều tồn tại và chạy (`--self-test` OK, `hit@5 30/30`) | **ĐÓNG** — đã ship |
| `task_878c40ce717b` | 2d | Capability-proof map — T-260718-01 | `medic capproof` → **199/199 proven · nợ tồn 0** | **ĐÓNG** — đã ship |
| `task_9aae1bbea821` | 2d | Archetype tester T-260718-02 | `llmwiki/personas/tester.md` tồn tại (3.1K, có `keyword`), đã nằm trong roster `council.personas.yaml` từ T-260719-02 | **ĐÓNG** — đã ship |

## Phát hiện then chốt: sổ task của Orca là RUNTIME-GLOBAL

Đây mới là lý do các task lạ xuất hiện. Guide của chính Orca ghi thẳng: *"Orchestration messages and tasks are runtime-global."* Đo được **18 terminal thuộc nhiều dự án khác nhau cùng ghi vào MỘT sổ**, nên `task-list` chạy ở repo `setup` trả về cả việc của `bonbon-ai`, HRIS/payroll, DMS Coteccons.

Hệ quả nghiêm trọng hơn báo cáo nhiễu: **một orchestrator chạy ở dự án A nhìn thấy và claim được task của dự án B** — phá đúng mục tiêu "tách bias ở tầng vật lý" (cô lập được worktree và CLI, nhưng sổ việc thì dùng chung).

Đã vá ở `orca-reconcile.py` (2026-07-20): `--stamp` đóng dấu repo root lúc TẠO task (chính xác vĩnh viễn, còn đúng khi terminal đã chết — thực đo 0/17 terminal cũ còn sống), `--scope current|all` khi ĐỌC. Quy tắc fail-safe: chỉ loại task **chứng minh được** thuộc dự án khác; `unknown` thì giữ, vì thà hiện một task không phải của mình còn hơn giấu một task là của mình.

## Nhóm B — thuộc DỰ ÁN KHÁC (11 task) — user đã xác nhận không liên quan

Các task này trỏ vào repo/đường dẫn ngoài repo framework này. Tôi **không** đọc được trạng thái thật của chúng từ đây, nên **không phán**.

| Task | Tuổi | Việc | Vì sao không phán được |
|---|---|---|---|
| `task_29467f85b9d0` | 59d | email-viewer fallback khi `.eml` thiếu headers | Dự án email-viewer, ngoài repo này |
| `task_ef85de290c68` | 59d | BRAINSTORM B — email viewer, góc security | Cùng dự án trên; là task brainstorm, có thể đã hết nghĩa |
| `task_22fd20341a37` | 59d | FIX DOCX/XLSX Office Online Viewer | Cùng dự án trên |
| `task_dae8d64881a7` | 25d | Proposal: HRIS Adapter (ACL) | Dự án HRIS, cần người biết tình trạng adapter hiện tại |
| `task_fad15be6c94c` | 25d | Proposal: hris-explorer-v2 (3 kênh SQL/Portal/API) | Trạng thái `blocked`; dep là gì thì chỉ người trong dự án biết |
| `task_9342bdf70008` | 24d | Proposal: DMS Sync Adapter — poller 12 module | Dự án DMS |
| `task_69a4c9809b77` | 14d | Regen wiki-graph project **1-webservice** | 5 task cùng lô, trỏ project scratchpad/UAT — cần xác nhận các project đó còn tồn tại không |
| `task_b1ea535d5e4d` | 14d | Regen wiki-graph project **2-datapipeline** | như trên |
| `task_4df5ddaefbc4` | 14d | Regen wiki-graph project **3-cli-toolkit** | như trên |
| `task_428bb3355096` | 14d | Regen wiki-graph project **4-polyglot** | như trên |
| `task_e3bb0e8c2118` | 14d | Regen wiki-graph project **5-knowledgebase** | như trên |

**User xác nhận 2026-07-20: nhóm này không liên quan dự án của chúng ta.** Gợi ý cũ giữ lại làm ghi chú: 5 task regen wiki-graph là một lô sinh cùng ngày cho các project mẫu; nếu các project đó là sân UAT tạm thì cả lô đóng được một lượt. 3 task email-viewer đã 59 ngày — nếu tính năng đó đã ship hoặc dự án đã dừng thì đóng. Cần user xác nhận.

## Nhóm C — `failed`, là thí nghiệm cũ (3 task)

| Task | Tuổi | Việc | Nhận định | Verdict đề xuất |
|---|---|---|---|---|
| `task_daa12a904cde` | 17d | TEST end-to-end wiki-core traceability trong worktree clone biệt lập | Task **thí nghiệm** cố ý, không phải việc sản phẩm | **ĐÓNG** (thí nghiệm đã kết thúc) |
| `task_7f8949c6ddcf` | 15d | todo CLI: thêm lệnh `done <id>` / `rm` | Repo `todo.py` là sân thử dispatch, không phải sản phẩm | **ĐÓNG** (sân thử) |
| `task_02e26def5541` | 15d | Review diff của task todo.py trên | Cặp với task trên | **ĐÓNG** (sân thử) |

Ba task này `failed` gần như chắc chắn vì **worker được giao nhưng coordinator không nhận được tín hiệu xong** — đúng lỗi mà T1 vừa vá. Chúng là bằng chứng lịch sử của chính bug đó, nên đề xuất đóng kèm ghi chú thay vì xoá.

## Tổng kết verdict

| Nhóm | Số | Verdict |
|---|---|---|
| A — bằng chứng cứng đã ship | 3 | **ĐÓNG** |
| C — thí nghiệm `failed` | 3 | **ĐÓNG** kèm ghi chú |
| B — dự án khác | 11 | **GIỮ** — chờ user xác nhận, không đoán |

Nếu user xác nhận nhóm B, số task mồ côi về **0** và SC-006 đạt → mở được Pha 2.

## Lệnh áp dụng (chưa chạy)

```bash
# nhóm A + C — chỉ chạy sau khi user duyệt
for t in task_7a605c4ff70f task_878c40ce717b task_9aae1bbea821 \
         task_daa12a904cde task_7f8949c6ddcf task_02e26def5541; do
  orca orchestration task-update --task "$t" --status completed
done
```

## Origin
- **Source:** T4 của proposal `[[200726-orchestration-loop-closure]]`; dữ liệu từ `harness/scripts/orca-reconcile.py --json` chạy 2026-07-20 trên runtime Orca
- **Bằng chứng liên quan:** `harness/metrics/dispatch-proof.json` (T1/T2 — 2 vendor + nhánh lỗi)
- **Task:** `T-260720-01`
- **Commit:** _(filled by verify-before-commit)_
