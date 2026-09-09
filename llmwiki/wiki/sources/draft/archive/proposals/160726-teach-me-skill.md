---
type: draft
title: teach-me-skill
status: proposed
tags: [skill, teaching, explanation, debugger, diagram]
timestamp: 2026-07-16
task: T-260716-01
---

# 160726-teach-me-skill

**Status:** proposed

## What
Thêm skill `/teach-me` — giải thích MỘT thứ (một file, một hàm, một tính năng, một hệ thống) theo cấu trúc cố định: **cách chạy ở cấp HỆ THỐNG** (+ sơ đồ) · **cách chạy ở cấp CODE** (+ sơ đồ) · bộ ba **vấn đề giải quyết / workflow / nội dung chi tiết (OS · cơ chế · vai trò)** · **tóm tắt luồng** (+ sơ đồ). Điểm phân biệt: skill **được phép và nên DRIVE runtime thật** — chạy code với instrumentation, đặt breakpoint/dùng debugger, quan sát state thật — thay vì suy đoán từ đọc tĩnh, khi câu hỏi là "nó chạy thế nào".

## Context
Đã query wiki + pre-flight `/fdk` trước khi soạn (force-query, R7-f):

- **Không dẫm skill cũ** (pre-flight #3): chưa có skill teach/explain. Lân cận: `/onboard-codebase` (phân tích sâu, GHI wiki — nặng), `/join-project` (orient nhanh read-only cả dự án), `/cursor-animated-sites` + `/docs-site-macos` (dựng HTML walkthrough/glass). Không cái nào là "giải thích MỘT thứ ở 2 cấp + sơ đồ + grounded bằng runtime". `/teach-me` khác: **phạm vi hẹp (một thứ), sâu, có sơ đồ, và chứng bằng chạy thật**.
- Built-in `/verify` + `/run` — triết lý "chứng bằng cách DRIVE, không đọc-rồi-đoán". `/teach-me` mượn đúng triết lý đó cho phần "nó chạy thế nào": khi có thể, chạy code + instrument + quan sát, không suy diễn.
- `/docs-site-macos` — dùng SVG/glass, KHÔNG mermaid. Nên sơ đồ có hai đường: mermaid inline (nhanh, trong chat) hoặc HTML explainer glass (giữ lại/chia sẻ).
- `[[skill-craft]]` — `/teach-me` model-invoked (giải thích là việc model bắt ngữ cảnh); mỗi bước có completion criterion; tránh negation.
- `CLAUDE.md` § surgical — instrument để hiểu runtime PHẢI dọn sạch sau (không để lại print/breakpoint rác).

**Kết luận:** giá trị cốt lõi không phải "một explainer đẹp" (đã có docs-site-macos) mà là **giải thích được chứng bằng runtime thật**. Một lời giải thích "hàm này chắc trả về X" khác hẳn "tôi đã chạy với đầu vào Y, đặt breakpoint ở dòng Z, quan sát state là W". Cái sau là dữ kiện; cái trước là phỏng đoán. Đây đúng carve-out `/verify`.

## Global constraints
- **ADR-003:** hành vi `/teach-me` định nghĩa ở `skills/teach-me/SKILL.md` (canonical); mirror + bản cài sinh bằng `sync-skill.sh`.
- **Instrument để hiểu → DỌN SẠCH sau** (surgical, CLAUDE.md): print/log/breakpoint tạm thêm vào để quan sát runtime phải gỡ hết trước khi kết thúc — không để lại rác trong code người dùng.
- **Grounded, không bịa:** phần "nó chạy thế nào" ưu tiên chạy thật; nếu KHÔNG chạy được (thiếu môi trường, cần prod) → nói rõ "giải thích tĩnh, chưa chứng bằng chạy" và ghi nợ `[[150726-unknown-ledger]]` nếu một khẳng định phụ thuộc thứ chưa quan sát.
- **Không ghi công AI** (R15). **Trước push:** `medic --ci` xanh + repo-health local + `/fdk-uat` hai pha PASS (sentinel grep-verify).

## Non-goals
- **Không** thay `/onboard-codebase` (phân tích cả dự án → wiki) hay `/join-project` (orient cả dự án). `/teach-me` phạm vi MỘT thứ, không ghi wiki.
- **Không** đẻ một trình debugger mới — dùng công cụ có sẵn (pdb/debugpy · `node --inspect`/console.trace · print/log tạm) và built-in `/run`,`/verify` để drive.
- **Không** ép luôn ra file HTML — mặc định giải thích trong chat + mermaid; HTML explainer chỉ khi user muốn giữ/chia sẻ.

## Approaches
**(A) Explainer thuần tĩnh (đọc code → giải thích).** Nhanh, không cần chạy. Nhưng "nó chạy thế nào" thành phỏng đoán — đúng thứ user muốn tránh khi nhắc "breakpoint/debugger".

**(B) — chọn.** Cấu trúc giải thích cố định (2 cấp + triad + flow), và phần runtime **grounded bằng chạy thật** khi có thể: instrument tạm, breakpoint, quan sát, rồi dọn. Sơ đồ hai đường: mermaid inline (mặc định) / HTML glass (opt-in). Đây là "explainer" + "verify" gộp — giá trị nằm ở chỗ chứng bằng runtime, không chỉ vẽ đẹp.

## Plan

- [ ] **T1 — Skill `/teach-me`: cấu trúc giải thích + grounded runtime.** `skills/teach-me/SKILL.md`. Đầu vào: user chỉ một thứ (file/hàm/tính năng/hệ thống). Output bốn phần cố định:
  1. **Cấp HỆ THỐNG — nó chạy thế nào** + sơ đồ: các thành phần, ai gọi ai, dữ liệu đi đâu, ranh giới process/service/OS.
  2. **Cấp CODE — nó chạy thế nào** + sơ đồ: hàm/đường thực thi cụ thể, state đổi ra sao, nhánh nào chạy.
  3. **Bộ ba:** **vấn đề giải quyết** (vì sao tồn tại) · **workflow** (các bước dùng/chạy) · **nội dung chi tiết** (OS liên quan · cơ chế · vai trò từng phần).
  4. **Tóm tắt luồng** + sơ đồ: một hình một câu chuyện đầu-cuối.
  Mỗi phần "nó chạy thế nào" **ưu tiên DRIVE runtime**: chạy với đầu vào cụ thể, thêm instrument tạm / đặt breakpoint (pdb/debugpy · `node --inspect` · print/log), quan sát state THẬT, rồi **dọn sạch instrument**. Không chạy được → nói rõ "giải thích tĩnh", không giả vờ đã chứng.

- [ ] **T2 — Sơ đồ hai đường (mermaid mặc định / HTML glass opt-in).** Sơ đồ mặc định = khối ```mermaid``` inline (flowchart/sequence) — nhanh, đọc-được-dạng-text, render ở surface hỗ trợ. User muốn giữ/chia sẻ → render một **HTML explainer** theo `/docs-site-macos` (glass, toggle sáng/tối, full-path) với sơ đồ SVG. Ghi rõ trong skill khi nào dùng đường nào.

- [ ] **T3 — Register + cổng + UAT.** `new-skill.py teach-me` (4 chỗ curated); `sync-skill.sh`; regen `CAPABILITIES.md` + `overstack.html`; `capability-stamp --update`; append index/log; node problem-tree; `medic --ci` + repo-health local; `/fdk-uat` hai pha (canary → main-URL smoke, sentinel grep-verify). Smoke: gọi thử `/teach-me` trên một hàm nhỏ có thật (vd `frontier.py`) — kiểm nó ra đủ bốn phần và có chạy thật.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| T1 — skill teach-me + grounded runtime | Claude | Văn bản định nghĩa cách giải thích + drive runtime; nuance cao | pending |
| T2 — sơ đồ hai đường | Claude | Quyết định mermaid/HTML, nối docs-site-macos | pending |
| T3 — register + cổng + UAT | OpenCode `big-pickle` (fallback Claude) | Cơ học: new-skill.py + UAT. Watchdog 60–90s | pending |

**Sequence diagram:** [160726-teach-me-skill-seq.html](../../../html/160726-teach-me-skill-seq.html)

## Requirements (FR)
- **FR-001**: `/teach-me` PHẢI ra bốn phần: cấp hệ thống (+sơ đồ) · cấp code (+sơ đồ) · bộ ba (vấn đề/workflow/chi tiết os·cơ chế·vai trò) · tóm tắt luồng (+sơ đồ).
- **FR-002**: Phần "nó chạy thế nào" PHẢI ưu tiên DRIVE runtime thật (chạy + instrument/breakpoint + quan sát) khi có thể, không suy đoán tĩnh.
- **FR-003**: Instrument tạm (print/log/breakpoint) PHẢI được DỌN SẠCH sau khi quan sát — không để rác trong code.
- **FR-004**: Không drive được → PHẢI nói rõ "giải thích tĩnh, chưa chứng bằng chạy", không giả vờ đã chứng.
- **FR-005**: Sơ đồ mặc định = mermaid inline; HTML explainer (docs-site-macos glass) là opt-in khi user muốn giữ/chia sẻ.
- **FR-006**: `/teach-me` PHẢI biết mình được dùng công cụ debugger/breakpoint có sẵn (pdb/debugpy, node --inspect, print/log) + built-in /run,/verify.

## Success criteria (SC)
- **SC-001**: User chỉ một hàm/hệ thống và nhận về bốn phần đầy đủ trong một lần — không phải hỏi lại từng phần.
- **SC-002**: Câu "nó chạy thế nào" được chứng bằng **một lần chạy thật có quan sát** (đầu vào X → state Y ở dòng Z), không phải "chắc là".
- **SC-003**: Sau khi teach xong, code người dùng **sạch như trước** — mọi instrument tạm đã gỡ.
- **SC-004**: `/teach-me` **tới tay ở dự án curl-cài** — chứng bằng `/fdk-uat`.

## Assumptions
Trường user không nói, model tự điền — mọi dòng `(default)`, sửa được:
- Sơ đồ mặc định = **mermaid inline** trong chat `(default)` — nhanh, không đẻ file mỗi lần; HTML glass chỉ khi user muốn giữ.
- `teach-me` model-invoked `(default)` — giải thích là việc model bắt ngữ cảnh, khác nhóm framework-dev đã tắt.
- Loop = `dev-loop` `(default)` — cùng nhóm dev.
- Phạm vi mặc định = **thứ user chỉ đích danh** `(default)`; không có thì hỏi "giải thích cái gì" (một câu, kèm gợi ý từ context).
- "Debugger" trong môi trường Claude Code = instrument + pdb/debugpy/node-inspect + /run/verify `(default)` — không có trình step-debugger GUI; drive bằng công cụ dòng lệnh.

Không mục nào rơi `[CẦN LÀM RÕ]`: thay đổi nội-bộ framework, không chạm auth/dữ-liệu-người-dùng/tiền/pháp-lý.

## Risks
- **Instrument quên dọn → rác trong code.** Giảm thiểu: FR-003 + skill bắt bước cuối "gỡ mọi instrument tạm", và nhắc chạy `git diff` xác nhận code sạch trước khi kết thúc.
- **Không chạy được nhưng vẫn nói như đã chứng.** Giảm thiểu: FR-004 buộc khai "giải thích tĩnh"; ghi nợ unknown nếu khẳng định phụ thuộc runtime chưa thấy.
- **Trùng /onboard-codebase / /join-project.** Giảm thiểu: ranh giới rõ — teach-me = MỘT thứ, sâu, có sơ đồ + chạy thật, không ghi wiki; onboard/join = cả dự án.
- **Sơ đồ mermaid không render ở terminal.** Giảm thiểu: mermaid đọc-được-dạng-text (nhãn rõ); user muốn hình thật → HTML glass opt-in.

## Self-review
- **Phủ yêu cầu:** FR-001→T1 · FR-002→T1 · FR-003→T1 · FR-004→T1 · FR-005→T2 · FR-006→T1. T3 là cổng. Không FR nào không có task.
- **Placeholder:** không còn mục bỏ trống.
- **Nhất quán tên:** skill `teach-me`; bốn phần (hệ thống/code/bộ-ba/tóm-tắt); sơ đồ mermaid-default/HTML-opt-in; grounded-runtime. Dùng đúng như vậy trong code.

## Notes
- Điểm phân biệt so với mọi explainer: grounded bằng runtime thật (mượn triết lý /verify). "Dùng breakpoint/debugger" = instrument + pdb/node-inspect + /run/verify trong môi trường Claude Code.
- [[skill-craft]] · [[150726-unknown-ledger]] (khai nợ khi giải thích tĩnh có khẳng định chưa chứng).

## Origin
- **Draft:** `wiki/sources/draft/160726-teach-me-skill.md`
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
