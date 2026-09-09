---
type: draft
title: "Absorb HÒA TAN 6 nguồn GitHub — nâng qc-code, orca-sec-scans, mem-rank, design-foundation, orca-issue"
status: proposed
tags: [absorb, adapt-modes, dissolve, qc-code, orca-sec-scans, mem-rank, design-foundation]
timestamp: 2026-07-17
task: T-260717-02
---

# 170726-absorb-six-sources

**Type:** draft
**Status:** proposed
**Tags:** absorb, adapt-modes, dissolve
**Proposed:** 2026-07-17

## What

Absorb 6 nguồn GitHub theo kiểu **HÒA TAN** (distill bản chất, viết lại thành của framework — không vendor bytes, không thêm dependency): nâng 5 bề mặt có sẵn của overstack thay vì thêm skill mới.

## Context

Query wiki trước khi draft (theo R7-f):

- [[adapt-modes]] — taxonomy 3 kiểu absorb. User đã chốt **HÒA TAN** cho cả đợt: chép cái **Ý** rồi tự viết lại, sở hữu thứ mình hiểu; ghi `adapt_mode` vào provenance. Khác NHÚNG (chép bytes, nuôi hộ) và KÉO NGOÀI (pin + audit, engine ở ngoài).
- Tiền lệ chuẩn: vụ hallmark 2026-07-15 ([[design-foundation]]) — clone vào `scratchpad/`, distill qua `/propose` → gate → task, để lại cổng tất định (`frontend-antipattern.py` wired vào medic), đóng `p-23`. Đợt này đi đúng đường đó.
- [[ADR-003-skill-as-single-source-of-truth]] — sửa hành vi skill chỉ sửa **canonical** `skills/<tên>/SKILL.md`, mirror `llmwiki/skills/` đồng bộ qua `sync-template`; parity có CI gác (`skills-sync.yml`).
- Tiền lệ superpowers: `140726-propose-plan-split-superpowers` — đã absorb tỷ lệ spec:plan 1:8 vào chính `/propose`. Nghĩa là trong 14 skill của obra/superpowers, phần lớn đã có tương đương overstack; đợt này chỉ lấy phần **thật sự thiếu**.
- Trạng thái skill đích (đọc trong phiên): `/qc-code` = review 4 mục chấm điểm + test tái hiện `qc-*` chạy tất định; `/orca-sec-scans` = Trivy tĩnh + kiểm chứng động giả định dev; `mem-rank` = episodic store + pluggable embedding (commit `0a1958c`); sàn design = hallmark 6 discipline + slop-test.

## Global constraints

Chép nguyên văn từ wiki/ADR/policy — mọi task ngầm mang theo:

- **ADR-003:** "Toàn bộ hành vi [skill] sống trong [canonical]. Sửa hành vi chỉ sửa file này; mirror và bản remote được đồng bộ qua `sync-template`, không chép tay." Đích sửa là `skills/<tên>/SKILL.md` (canonical), sau đó sync mirror `llmwiki/skills/`.
- **Parity CI:** `skills-sync.yml` chặn drift 2 cây skill — commit thiếu sync là đỏ.
- **R15:** cấm AI-attribution trong commit message (chặn cứng ở commit-msg hook).
- **adapt-modes:** "Ghi `adapt_mode` vào `provenance` cho mỗi skill ngoài để về sau biết nó thuộc kiểu nào" — mỗi phần hòa tan ghi `adapt_mode: dissolve` + nguồn + ngày vào mục Origin của skill đích (và `fdk/skills.provenance.json` nếu có entry).
- **Ponytail/CLAUDE.md mục 2:** không phình — tổng diff mỗi skill đích ≤ ~80 dòng; distill là NÉN, không phải chép.
- **Cổng trước push:** `medic --ci` xanh; wiki entry chỉ tạo SAU khi code commit (luật "Wiki entries are only created AFTER code is committed").
- **Prose rule (feedback 2026-06-27):** phần thêm vào SKILL.md người đọc được — câu hoàn chỉnh, không caveman.

## Non-goals

- **KHÔNG thêm skill mới nào** — 90 skill hiện có là đủ bề mặt; mọi thứ hòa vào skill/tool có sẵn.
- **KHÔNG vendor** 21.000+ dòng per-language guides của awesome-skills/code-review-skill — chỉ distill *phương pháp* (severity labels, 4-phase). Cần guide ngôn ngữ cụ thể thì đó là một vòng KÉO NGOÀI sau, có sổ.
- **KHÔNG cài** claude-mem / gstack / superpowers làm dependency runtime — zero external dep là định nghĩa của HÒA TAN.
- **KHÔNG đổi sàn** hallmark — frontend-design (nếu có phần hay) vào như *flavour/checkpoint trên sàn*, không thay 6 discipline.
- **KHÔNG absorb** 12 skill superpowers còn lại (đã có tương đương: writing-plans→/plan, verification→verify-before-commit, worktrees→orca-cli, TDD→ponytail one-check…).

## Approaches

| Phương án | Bản chất | Tradeoff |
|---|---|---|
| **A. HÒA TAN (chọn)** | Distill ý → viết lại vào 5 bề mặt có sẵn | (+) 0 dep, gác tất định được, không phình số skill. (−) Tự maintain, không có update từ upstream — chấp nhận vì phần lấy là *checklist/phương pháp* (ít đổi), không phải engine. |
| B. NHÚNG-SỞ-HỮU | Vendor 6 skill nguyên bytes vào `skills/` | (+) Giữ nguyên bản, nhanh. (−) 90→96 skill trùng chức năng (qc-code vs code-review-skill cùng làm review), +LICENSE ngoại, nuôi hộ bytes không hiểu — đúng cái bảng quyết định adapt-modes khuyên tránh khi "bản chất nhỏ". |
| C. KÉO NGOÀI | Pin 6 repo + provenance, cài global khi cần | (+) Có update upstream. (−) 6 dependency mạng cho thứ chỉ là checklist tĩnh; overstack đã có bề mặt tương đương nên pin thêm là thừa. |

Chọn **A** — do user chốt trực tiếp ở gate câu hỏi (2026-07-17), khớp bảng quyết định adapt-modes: "bản chất nhỏ, muốn gác tất định, 0 dep ngoài → HÒA TAN".

## Plan

- [ ] **T1 — gstack review + awesome-skills → `/qc-code`:** distill 13 nhóm check lỗi của `garrytan/gstack` skill `review` (5 CRITICAL: SQL & data safety, race condition, LLM output trust boundary, shell injection, enum completeness · 8 INFORMATIONAL: async/sync mixing, field-name safety, LLM prompt, type coercion, view/frontend, time window, completeness gaps, CI/CD) thành bảng tra trong mục **logic + security** của `skills/qc-code/SKILL.md`; kèm nhãn severity (blocking · important · nit · suggestion) distill từ `awesome-skills/code-review-skill`. Mỗi finding của qc-code từ nay gắn 1 nhóm + 1 severity.
- [ ] **T2 — everything-claude-code security-review → `/orca-sec-scans`:** distill bảng **trigger-conditions** (khi thêm auth / nhận input người dùng / đụng secret / mở endpoint / tính năng thanh toán → bắt buộc chạy scan) + các nhóm lỗ hổng thành mục mới trong `skills/orca-sec-scans/SKILL.md`, nối vào phần "kiểm chứng động giả định dev" sẵn có.
- [ ] **T3 — anthropics/skills frontend-design → design-foundation:** verify skill tồn tại (Assumption A-1); đọc SKILL.md của nó, đối chiếu từng luật với sàn hallmark 6 discipline; phần **chưa có** trong sàn → thêm như checkpoint/flavour vào `skills/hallmark/` references + cập nhật concept [[design-foundation]]; phần trùng → bỏ, ghi rõ "đã có" trong Origin.
- [ ] **T4 — claude-mem → mem-rank export/import:** claude-mem không public cơ chế export (chỉ cloud sync cmem.ai) → tự thiết kế: `mem-rank.py export > memories.jsonl` / `mem-rank.py import memories.jsonl` (dedupe theo id, append-only), để memory di chuyển máy↔máy bằng file — chép **Ý** "memory phải portable, sync-on-write", không chép code. Kèm self-test round-trip.
- [ ] **T5 — superpowers → qc-code + orca-issue:** distill `receiving-code-review` (nguyên tắc: **verify claim của reviewer bằng cách chạy/đọc code trước khi sửa theo**, không blind-comply) thành mục "Nhận review" trong `skills/qc-code/SKILL.md`; distill khung `systematic-debugging` (phase-based: đọc lỗi nguyên văn → tái hiện → cô lập → root-cause, cấm shotgun-fix) đối chiếu vòng repro-first của `skills/orca-issue/SKILL.md` — chỉ thêm phần vòng hiện tại chưa nói.
- [ ] **T6 — provenance + sync + verify:** ghi `adapt_mode: dissolve` + nguồn + ngày vào Origin từng skill đích; chạy `sync-template` đồng bộ mirror; `medic --ci`; commit qua `verify-before-commit`.

## Requirements (FR)

- **FR-001**: `/qc-code` PHẢI liệt kê 13 nhóm check lỗi (5 CRITICAL + 8 INFORMATIONAL) và mỗi finding PHẢI gắn đúng 1 nhóm.
- **FR-002**: `/qc-code` PHẢI gắn severity (blocking · important · nit · suggestion) cho mỗi finding, có định nghĩa từng mức trong SKILL.md.
- **FR-003**: `/orca-sec-scans` PHẢI có bảng trigger-conditions nêu rõ hành vi code nào bắt buộc kích hoạt scan.
- **FR-004**: `mem-rank.py` PHẢI có `export`/`import` round-trip qua JSONL, dedupe theo id, kèm self-test tất định.
- **FR-005**: sàn design PHẢI được đối chiếu với frontend-design; mọi luật thêm vào PHẢI là luật sàn chưa có (không trùng).
- **FR-006**: `/qc-code` PHẢI có mục "Nhận review" (verify trước khi sửa); `/orca-issue` PHẢI được đối chiếu với systematic-debugging.
- **FR-007**: mỗi phần absorb PHẢI ghi `adapt_mode: dissolve` + nguồn (repo, path, ngày) trong Origin của skill đích.

## Success criteria (SC)

- **SC-001**: Một diff chứa lỗi mẫu thuộc nhóm CRITICAL (ví dụ race condition khi 2 request cùng ghi) được `/qc-code` **gọi đúng tên nhóm lỗi + severity** trong một lần chạy — người đọc report biết ngay lỗi thuộc lớp nào mà không cần mở nguồn ngoài.
- **SC-002**: Dev chuyển sang máy mới, chạy 2 lệnh (`export` ở máy cũ, `import` ở máy mới), hỏi "phiên trước làm gì" và nhận lại đúng episode cũ — memory không còn bị giam trong một máy.
- **SC-003**: Người viết code đọc mục trigger-conditions của `/orca-sec-scans` tự trả lời được "thay đổi này có bắt buộc scan không" trong dưới một phút.
- **SC-004**: Trang UI sinh sau đợt absorb vẫn qua slop-test hiện có; không xuất hiện cổng trùng lặp nào (medic không báo thêm probe mới trùng).

## Assumptions

- **A-1** `(default, find-out-later → [[unknown-frontend-design]] U-01)`: skill `frontend-design` tồn tại trong `anthropics/skills` — WebFetch chưa xác nhận được (trang không render danh sách); T3 verify đầu tiên, không có thì T3 rút còn "đối chiếu với tài liệu design chính thống khác hoặc bỏ, ghi sổ".
- **A-2** `(default)`: phần lấy từ superpowers = `receiving-code-review` + `systematic-debugging` — user chỉ nói "superpower"; 12 skill còn lại đã có tương đương overstack (căn cứ scan `scratchpad/superpowers/skills/` + tiền lệ 140726).
- **A-3** `(default)`: claude-mem không có export CLI documented (chỉ cloud sync) → format JSONL tự thiết kế, không tương thích ngược với SQLite/Chroma của claude-mem.
- **A-4** `(default)`: `everything-claude-code` = fork `WorldFlowAI/everything-claude-code` (có đúng path `skills/security-review/SKILL.md`).
- **A-5** `(default)`: "23 quy trình check lỗi" của gstack = checklist 13 nhóm trong skill `review` (user đã xác nhận phạm vi "chỉ skill review"; số 23 là số tool của cả stack, không phải số check).

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 qc-code ← gstack + awesome-skills | Claude Code | Distill = đọc hiểu + nén + viết lại, cần phán đoán trùng/thiếu — không phải boilerplate | done |
| T2 orca-sec-scans ← security-review | Claude Code | Như T1; đích là skill security, sai một dòng là sai lớp gác | done |
| T3 design-foundation ← frontend-design | Claude Code | Có bước verify nguồn + đối chiếu sàn — cần judgment | done |
| T4 mem-rank export/import | Claude Code | Code logic + self-test, đụng store episodic dùng chung | done |
| T5 qc-code + orca-issue ← superpowers | Claude Code | Distill đối chiếu 2 skill đích | done |
| T6 provenance + sync + verify | Claude Code | Chuỗi gate tất định, chạy tại chỗ | done |

Tất cả về Claude vì cả 6 task là distill/analysis — đúng bảng chi phí ("Architectural decisions → Claude"); không có task search/boilerplate nào đáng đẩy CLI rẻ. Render HTML của SPEC này: Claude render trực tiếp (standalone render, ADR-003 cho phép; không dispatch vì độ tin headless ~1/5 không đáng cho 1 file).

**Sequence diagram:** [170726-absorb-six-sources-seq.html](../../../html/170726-absorb-six-sources-seq.html)

## Render brief

- **T1** · steps: [legacy] qc-code 4 mục hiện có → [add] bảng 13 nhóm + severity vào mục logic/security → [add] finding gắn nhóm+severity → [block] KHÔNG vendor per-language guides (non-goal).
- **T2** · steps: [legacy] orca-sec-scans Trivy + kiểm chứng động → [add] bảng trigger-conditions → [block] không thêm tool scan mới.
- **T3** · steps: [add] verify frontend-design tồn tại (A-1) → [legacy] sàn hallmark 6 discipline → [add] checkpoint thiếu vào references → [block] không đổi sàn.
- **T4** · steps: [legacy] mem-rank episodic store → [add] export JSONL → [add] import dedupe-by-id → [add] self-test round-trip → [block] không dep claude-mem.
- **T5** · steps: [legacy] qc-code / orca-issue repro-first → [add] mục "Nhận review" (verify claim trước khi sửa) → [add] đối chiếu systematic-debugging → [block] 12 skill superpowers còn lại không absorb.
- **T6** · steps: [add] Origin + adapt_mode: dissolve từng đích → [add] sync-template mirror → [legacy] medic --ci + verify-before-commit.

## Self-review

1. **Phủ yêu cầu:** 6 nguồn user nêu → T1 (gstack + awesome-skills, gộp vì cùng đích qc-code), T2 (security-review), T3 (frontend-design), T4 (claude-mem), T5 (superpowers) — đủ 6, không nguồn nào rơi; T6 là nghĩa vụ provenance từ adapt-modes.
2. **Quét placeholder:** không còn token trì hoãn nào trong draft; A-1 là unknown có sổ (U-01), không phải placeholder trốn.
3. **Nhất quán tên-kiểu:** thống nhất "13 nhóm check" (không dùng "23 quy trình" — số 23 là số tool gstack, đã ghi A-5); severity 4 mức viết thống nhất blocking · important · nit · suggestion; đích luôn ghi canonical `skills/<tên>/SKILL.md`.

## Notes

- Invoked via: `/orca-workflow` → `/propose`
- Nguồn xác định: `obra/superpowers` (clone sẵn `scratchpad/superpowers`) · `anthropics/skills` · `awesome-skills/code-review-skill` · `WorldFlowAI/everything-claude-code` · `thedotmack/claude-mem` · `garrytan/gstack`.

## Origin

- **Draft:** `wiki/sources/draft/170726-absorb-six-sources.md`
- **Nguồn quyết định:** user args `/orca-workflow` 2026-07-17 + 3 câu trả lời gate (claude-mem = import/export MEMORY; gstack = chỉ skill review; kiểu = HÒA TAN).
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
