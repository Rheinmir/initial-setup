---
type: draft
title: qc-code-skill
status: proposed
tags: [skill, code-review, qc, test-generation, orca-workflow]
timestamp: 2026-07-15
task: T-260715-04
---

# 150726-qc-code-skill

**Status:** proposed

## What
Thêm skill `/qc-code` — review code theo phong cách **senior 10 năm kinh nghiệm**, bốn mục (security · performance · naming · logic), mỗi mục cho **điểm/10 + lỗi nặng nhất + cách sửa**, và một **kết luận: PASS sang bước kế hay CẦN SỬA**. Với mục logic, mỗi bug tìm được **sinh một test-case tái hiện lỗi**; các test đó auto-chạy khi code đổi qua một **hook tất định (chỉ chạy test, không gọi LLM)**, và `/qc-code` là một bước tùy chọn trong `/orca-workflow` trước commit.

## Context
Đã query wiki + pre-flight `/fdk` + đọc yêu cầu trước khi soạn (force-query, R7-f):

- **Không dẫm skill cũ** (pre-flight #3): repo chưa có skill `qc`/`review`. Built-in Claude Code có `/code-review`, `/simplify`, `/security-review`; của ta có `/orca-sec-scans` (Trivy **static** — vuln/misconfig/secret) và `/medic` (cổng sức khoẻ framework). `/qc-code` khác: **review-bằng-phán-đoán-senior** có chấm điểm + verdict + sinh test tái hiện — bổ sung cho Trivy (tĩnh) và cho `/code-review` (không có format 4-mục-chấm-điểm-verdict).
- SPEC `150726-unknown-ledger` + `150726-mattpocock-absorb` (đã giao) — `/propose` có trục fact/decision + `(default)`/`[CẦN LÀM RÕ]`/`fill-first`. Quyết định "nối vào đâu" của skill này đã được **hỏi và chốt** (option 3, xem `## Approaches`), không đoán.
- `/orca-workflow` bước 7 = `verify-before-commit` chạy trước mỗi commit. `/qc-code` cắm vào TRƯỚC bước đó (tùy chọn).
- Hook `PostToolUse` (llmwiki/.claude/hooks/post_tool_use.py) fire trên Edit/Write — nguyên tắc overstack: **hook phải tất định, 0-token** (không gọi LLM). Đây là ràng buộc cứng quyết định thiết kế.
- `[[skill-craft]]` — `/qc-code` model-invoked (review code là việc model bắt ngữ cảnh); completion criterion mỗi bước; tránh negation.

**Kết luận từ đối chiếu:** phần đắt (LLM phán đoán 4 mục) và phần rẻ (test tất định tái hiện lỗi) phải **tách**. LLM review = gọi tay / bước workflow; test tự-sinh = auto-chạy qua hook tất định. Chạy LLM review trên mọi lần Edit là đắt, ồn, và phá nguyên tắc hook-0-token. Đây là bậc "đổi cấu trúc" của Meadows: không tự động-hoá cái đắt, tự động-hoá cái rẻ.

## Global constraints
- **ADR-003:** hành vi `/qc-code` định nghĩa ở `skills/qc-code/SKILL.md` (canonical); mirror + bản cài sinh bằng `sync-skill.sh`.
- **Hook phải TẤT ĐỊNH, 0-token** — hook auto-chạy test tuyệt đối KHÔNG gọi LLM. LLM review chỉ chạy khi user gọi `/qc-code` hoặc ở bước workflow tùy chọn.
- **Verdict là advisory, không chặn cứng bằng LLM** — LLM chấm điểm/verdict để user QUYẾT, không phải cổng tất định. Cổng tất định (chặn) chỉ là các test tái hiện (đỏ→xanh) — đó mới là thứ máy gác được.
- **Test tự-sinh phải chạy được độc lập** — mỗi test là một file chạy bằng runner có sẵn của dự án (pytest/vitest/…), tự phát hiện; không đẻ framework test mới.
- **Engine hook tất định phải TỚI ĐƯỢC downstream** (bài học `p-26`) — verify travel bằng UAT.
- **Không ghi công AI** (R15). **Trước push:** `medic --ci` xanh + repo-health local + `/fdk-uat` hai pha PASS (sentinel grep-verify).

## Non-goals
- **Không** thay `/code-review` built-in hay `/orca-sec-scans`. `/qc-code` là format senior-4-mục-chấm-điểm, bổ sung.
- **Không** hook LLM vào Edit/Write — quá đắt, ồn, phá nguyên tắc hook-0-token. (Đã hỏi user, chốt option 3.)
- **Không** để verdict LLM chặn commit — verdict là để người quyết; chỉ test tất định mới gác cứng.
- **Không** review toàn codebase mặc định — mặc định là **diff hiện tại** (đã chốt), chỉ định file khi cần.

## Approaches
Câu hỏi "nối vào đâu" đã được **hỏi user và chốt**:

**(1) Chỉ workflow-step + gọi tay.** Test tự-sinh chỉ là file test thường, chạy qua cổng có sẵn (verify-before-commit/CI). Không hook mới. Đơn giản nhưng một bug đã tái hiện chỉ được bắt lúc commit, không phải ngay khi sửa.

**(2) Auto-hook LLM mọi Edit.** Tự động hoàn toàn nhưng đắt (một LLM call mỗi edit), chậm, ồn, phá nguyên tắc hook-0-token. **Loại.**

**(3) — user CHỌN.** LLM review = gọi tay + bước workflow tùy chọn. Hook tất định (0-token) auto-chạy **các test tái hiện mà qc-code đã sinh** khi code đổi — bug đã có test thì lần sửa sau chạm vùng đó là bắn liền, không đợi commit. Tách đúng: cái đắt thủ công, cái rẻ tự động. Phạm vi review mặc định = **diff hiện tại** (đã chốt).

## Plan

- [ ] **T1 — Skill `/qc-code` (bốn mục senior + verdict).** `skills/qc-code/SKILL.md`. Persona senior 10 năm. Bốn mục, mỗi mục **điểm/10 + lỗi nặng nhất + cách sửa**:
  - **security** — SQL injection · XSS · lộ API key/secrets · validate input · phân quyền.
  - **performance** — query N+1 · vòng lặp lồng vô ích · memory leak âm thầm; **chỉ ra 3 điểm chậm nhất + cách tối ưu**.
  - **naming & readability** — tên có nói đúng việc nó làm · convention nhất quán; **trả về bảng `tên cũ → tên mới + lý do`**.
  - **logic & bug** — edge case (null/rỗng/số âm/overflow) · off-by-one · race condition; mỗi bug **viết một test-case tái hiện**.
  Kết luận: **PASS sang bước kế** hoặc **CẦN SỬA** (liệt kê phải sửa gì trước khi pass). Phạm vi mặc định: **diff hiện tại** (`git diff` từ base/branch), chỉ định file khi cần.

- [ ] **T2 — Test tái hiện: sinh file + nơi đặt.** Mục logic của T1, mỗi bug → một test-case đỏ (tái hiện lỗi). Đặt vào thư mục test chuẩn của dự án (tự phát hiện: `tests/` · `__tests__/` · `*_test.py` · `*.spec.ts`…), đặt tên `qc-<slug-bug>` để phân biệt test do qc-code sinh. Mỗi test tự-chạy bằng runner có sẵn (pytest/vitest/jest). File test là deliverable tất định — nó gác cứng, khác verdict LLM (advisory).

- [ ] **T3 — Engine tất định `harness/scripts/qc-regression.py` (0-token).** Chạy đúng các test `qc-*` đã sinh, báo đỏ/xanh. `--list` (liệt kê test qc-* + trạng thái) · `--run` (chạy, exit 1 nếu có đỏ) · `--json`. Tự phát hiện runner. Đây là thứ hook gọi — KHÔNG gọi LLM. Self-test.

- [ ] **T4 — Auto-hook khi code đổi (chỉ test, tất định).** Nối `qc-regression.py --run` vào một điểm auto khi code đổi — **PostToolUse (Edit/Write mã nguồn) chạy nhẹ** hoặc gộp vào `verify-before-commit`. Chọn điểm rẻ nhất không làm chậm mỗi edit: mặc định chạy ở **verify-before-commit** (trước commit) + tùy chọn bật PostToolUse cho ai muốn phản hồi tức thì. Hook chỉ chạy test `qc-*` (nhanh), KHÔNG toàn bộ suite mỗi edit. Fail-open nếu không có test qc-* nào.

- [ ] **T5 — Cắm `/qc-code` vào `/orca-workflow` (tùy chọn, trước verify).** Thêm một bước tùy chọn ở `/orca-workflow`: trước `verify-before-commit`, có thể gọi `/qc-code` review diff → nếu verdict CẦN SỬA thì sửa trước khi commit. Là **tùy chọn** (user bật), không bắt buộc — verdict LLM không chặn cứng.

- [ ] **T6 — Register + cổng + UAT.** `new-skill.py qc-code` (4 chỗ curated); `sync-skill.sh`; regen `CAPABILITIES.md` + `overstack.html`; `capability-stamp --update`; append index/log; node problem-tree; `medic --ci` + repo-health local; `/fdk-uat` hai pha (canary → main-URL smoke, sentinel grep-verify).

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| T1 — skill qc-code 4 mục | Claude | Văn bản định nghĩa chất lượng review — không giao model rẻ | pending |
| T2 — sinh test tái hiện | Claude | Nuance: đặt test đúng chỗ, đúng runner của dự án | pending |
| T3 — qc-regression.py | Claude | Engine tất định, tự-phát-hiện runner sai là chạy hụt | pending |
| T4 — auto-hook (chỉ test) | Claude | Chạm hook — rủi ro; phải giữ 0-token + không chậm mỗi edit | pending |
| T5 — cắm vào orca-workflow | Claude | Chạm luồng workflow đang chạy | pending |
| T6 — register + cổng + UAT | OpenCode `big-pickle` (fallback Claude) | Cơ học: new-skill.py + script + UAT. Watchdog 60–90s | pending |

**Sequence diagram:** [150726-qc-code-skill-seq.html](../../../html/150726-qc-code-skill-seq.html)

## Requirements (FR)
- **FR-001**: `/qc-code` PHẢI review bốn mục (security/performance/naming/logic), mỗi mục điểm/10 + lỗi nặng nhất + cách sửa, và một kết luận PASS/CẦN SỬA.
- **FR-002**: Mục performance PHẢI chỉ ra 3 điểm chậm nhất + cách tối ưu; mục naming PHẢI trả bảng `tên cũ → mới + lý do`.
- **FR-003**: Mục logic PHẢI sinh một test-case tái hiện cho mỗi bug tìm được.
- **FR-004**: Test tái hiện PHẢI đặt vào thư mục test chuẩn của dự án (tự phát hiện), tên `qc-*`, chạy bằng runner có sẵn.
- **FR-005**: PHẢI có engine tất định `qc-regression.py` chạy các test `qc-*` (0-token, không LLM).
- **FR-006**: Test `qc-*` PHẢI auto-chạy khi code đổi qua hook/verify tất định — KHÔNG bao giờ gọi LLM trong hook.
- **FR-007**: `/qc-code` PHẢI là một bước TÙY CHỌN trong `/orca-workflow` trước `verify-before-commit`.
- **FR-008**: Verdict LLM là advisory (người quyết); chỉ test tất định (đỏ→xanh) mới gác cứng.

## Success criteria (SC)
- **SC-001**: Một người dán code vào `/qc-code` nhận về bốn mục chấm điểm + lỗi nặng nhất mỗi mục + verdict — trong một lần, không phải hỏi lại.
- **SC-002**: Một bug logic được tìm ra để lại một **test đỏ tái hiện** — lần sửa sau làm nó xanh là bằng chứng đã fix, và nếu bug quay lại thì test đỏ lại (không âm thầm tái phát).
- **SC-003**: Test `qc-*` **auto-chạy khi code đổi** mà **không tốn một LLM call nào** — hook giữ 0-token.
- **SC-004**: Chi phí không nổ: LLM review chỉ chạy khi gọi tay/workflow, không phải mỗi edit.
- **SC-005**: `/qc-code` + `qc-regression.py` **tới tay ở dự án curl-cài** — chứng minh bằng `/fdk-uat`.

## Assumptions
Trường user không nói, model tự điền — mọi dòng `(default)`, sửa được:
- Điểm auto-hook mặc định = **verify-before-commit** (trước commit), PostToolUse chỉ là tùy chọn bật `(default)` — rẻ nhất không làm chậm mỗi edit; user muốn phản hồi tức thì thì bật PostToolUse.
- Hook chỉ chạy **test `qc-*`** (không toàn suite mỗi edit) `(default)` — giữ nhanh; toàn suite vẫn chạy ở verify/CI.
- `qc-code` model-invoked `(default)` — review code là việc model bắt ngữ cảnh, khác nhóm framework-dev vừa tắt.
- Verdict LLM **không chặn commit** `(default)` — người quyết; chặn cứng chỉ dành cho test tất định.
- Loop skill = `dev-loop` `(default)` — cùng nhóm với propose/verify/impact-check.

Không mục nào rơi `[CẦN LÀM RÕ]`: thay đổi nội-bộ framework, không chạm auth/dữ-liệu-người-dùng/tiền/pháp-lý. (Quyết định lớn "nối vào đâu" đã HỎI và chốt option 3, không đoán.)

## Risks
- **Hook làm chậm mỗi edit.** Giảm thiểu: mặc định auto-chạy ở verify-before-commit (không phải mỗi Edit); PostToolUse chỉ tùy chọn, và chỉ chạy test `qc-*` (nhỏ), fail-open nếu không có.
- **Verdict LLM bị hiểu nhầm là cổng cứng.** Giảm thiểu: skill nói rõ verdict = advisory; chặn cứng chỉ là test đỏ. Tránh cho user tưởng "qc-code PASS = an toàn tuyệt đối".
- **Test tự-sinh đặt sai chỗ / sai runner.** Giảm thiểu: tự phát hiện thư mục test + runner của dự án; không có thì báo rõ và để test cạnh file nguồn, không đoán bừa cấu trúc.
- **Trùng /code-review built-in.** Giảm thiểu: ranh giới rõ — /code-review = review tổng quát Claude; /qc-code = format senior-4-mục-chấm-điểm-verdict + sinh test. Nêu trong description.

## Self-review
- **Phủ yêu cầu:** FR-001→T1 · FR-002→T1 · FR-003→T1+T2 · FR-004→T2 · FR-005→T3 · FR-006→T4 · FR-007→T5 · FR-008→T1+T4. T6 là cổng. Không FR nào không có task.
- **Placeholder:** không còn mục bỏ trống.
- **Nhất quán tên:** skill `qc-code`; engine `harness/scripts/qc-regression.py`; test prefix `qc-*`; verdict `PASS`/`CẦN SỬA`; bốn mục security/performance/naming/logic. Dùng đúng như vậy trong code.

## Notes
- Quyết định "nối vào đâu" đã hỏi user (2026-07-15) → option 3 (LLM thủ công/workflow, test tự-sinh auto-hook tất định), phạm vi diff hiện tại. Dogfood đúng hệ fact/decision + hỏi-kèm-khuyến-nghị vừa dựng.
- [[skill-craft]] · [[150726-unknown-ledger]] (nếu review có unknown thì ghi nợ).

## Origin
- **Draft:** `wiki/sources/draft/150726-qc-code-skill.md`
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
