---
type: draft
title: hallmark-design-foundation
status: proposed
tags: [design, slop-test, frontend, default-fill, hallmark]
timestamp: 2026-07-15
task: T-260715-02
r7_meta: true
---

# 150726-hallmark-design-foundation

**Status:** proposed

## What
Hấp thụ `Nutlope/hallmark` (design skill của Together AI, "từ chối trông giống AI-generated") thành **nền design chung** của overstack — đúng thứ `p-23` đang mở đòi hỏi. Ba việc: cài hallmark làm **chuẩn mặc định khi dựng UI**, nâng cổng tất định `frontend-antipattern.py` (hiện ~5 check) bằng các cổng slop-test grep được của hallmark để **mọi HTML ta tự sinh phải vượt qua**, và nối catalog macrostructure/theme của hallmark vào `/propose` làm **nguồn fill mặc định** khi brief của user không nói rõ lựa chọn thiết kế.

## Context
Đã query wiki + đọc nguồn ngoài trước khi soạn (force-query, R7-f):

- `p-23` trong `fdk-problem-tree.html` (**đang mở, scope rỗng**): "~8 skill design mỗi cái tự mang luật, không nền chung; HTML do framework tự sinh (report/docs/council/tree) không bị soi cùng chuẩn." Đây chính là bài toán hallmark giải.
- `fdk/tools/frontend-antipattern.py` — cổng tất định đã có, wired vào `medic` (probe `p_frontend`), nhưng **chỉ ~5 check** (98 dòng). Hallmark có **57 cổng slop-test**. Ta có khung, thiếu nội dung.
- `llmwiki/wiki/sources/draft/060726-design-standard-ai-elite-PLAN.md` — một PLAN cũ về design-standard + ai-slop-lint, **vẫn nằm draft chưa thi hành** (orphan). Đề xuất này thay thế nó bằng một nền có thật, battle-tested.
- 14 skill design đang có (`design-taste-frontend`, `high-end-visual-design`, `docs-site-macos`, `gpt-taste`, `minimalist-ui`, `industrial-brutalist-ui`, `brandkit`, `redesign-existing-projects`, `imagegen-*`, `stitch-design-taste`, `tour-guide*`). Rủi ro trùng lặp cao — phải hoà giải, không đẻ cái thứ 15 cạnh tranh.
- `[[skill-craft]]` (vừa thêm) — hallmark 558 dòng + ~100 file reference là một skill khổng lồ; áp progressive disclosure: SKILL.md là step, catalog là external reference nạp khi cần.
- SPEC `150726-mattpocock-absorb` (đã giao) — `/propose` giờ có trục fact/decision + tag `(default)`. Fill-default của đề xuất này **cắm thẳng vào đó**: lựa chọn thiết kế user không nói = decision rủi ro thấp → fill từ catalog hallmark + tag `(default)`.
- Nguồn ngoài: `scratchpad/hallmark/` (clone `Nutlope/hallmark`) — `skills/hallmark/SKILL.md`, `references/slop-test.md` (57 cổng + pre-emit critique 6 trục), `references/anti-patterns.md` (Critical/Major), `references/macrostructures/` (21 macrostructure), `references/genres/` (4 genre).

**Kết luận từ đối chiếu:** hallmark không phải "skill design thứ 15". Nó là thứ 14 skill kia đang thiếu — một **nền kỷ luật chung** (6 discipline + 57 cổng) mà mọi output UI phải đứng trên. 6 discipline đáng chép nguyên: pre-emit self-critique (chấm 1–5 trên 6 trục trước khi xuất), honest-copy (không bịa số liệu — khớp anti-fabrication ta đã có), locked tokens (mọi màu/font qua biến có tên), no re-drawn chrome (cấm vẽ fake browser bar — đúng thứ ta hay làm trong seq.html), mobile 4 width, no italic header. Đây là những thứ *grep được* → đưa xuống cổng tất định.

## Global constraints
- **ADR-003:** hành vi skill định nghĩa ở `skills/<tên>/SKILL.md` (canonical); mirror + bản cài sinh bằng `sync-skill.sh`.
- **Provenance ngoài:** hallmark là skill bên thứ ba (LICENSE riêng) → cài qua `/skill-provenance` (ghi nguồn + sha256, audit supply-chain). KHÔNG sửa nội dung skill gốc; điều chỉnh của ta sống ở file riêng.
- **Cổng tất định phải TỚI ĐƯỢC downstream** (bài học `p-26`): nâng `frontend-antipattern.py` là engine ở global harness — verify nó travel. Rule mới/đổi có bite-test hai tầng nếu chạm policy.
- **Không phá 14 skill design đang có** — hallmark là nền chúng đứng trên, không phải cái thay thế. Skill taste hiện thành "flavour"; hallmark cấp discipline floor.
- **Cổng slop áp đúng phạm vi:** cổng UNIVERSAL grep được (gradient text, font Inter/system làm display, pure #000/#fff, italic header, fake chrome) áp cho MỌI HTML ta sinh. Cổng genre/structural (cần một brief thật) KHÔNG áp cho artifact kỹ thuật (seq.html, report) — chúng có R11 glass riêng.
- **Không ghi công AI** trong commit/PR/wiki (R15).
- **Trước push:** `medic --ci` xanh + repo-health local + `/fdk-uat` hai pha PASS (có chờ sentinel CDN grep-verify).

## Non-goals
- **Không** xoá hay gộp 14 skill design hiện có. Hoà giải bằng một dòng "đứng trên nền hallmark", không refactor chúng.
- **Không** bê cả 57 cổng vào `frontend-antipattern.py` — nhiều cổng cần phán đoán thị giác (hierarchy, restraint, variety), không grep được. Chỉ lấy nhóm cơ học.
- **Không** ép artifact kỹ thuật (seq.html, report, dashboard) theo macrostructure/theme của hallmark — chúng là máy-đọc/tham-chiếu, có chuẩn glass riêng (R11). Chỉ áp nhóm cổng universal.
- **Không** đổi `docs-site-macos` thành hallmark. Nó là một theme cụ thể của TA cho artifact nội bộ; hallmark là nền cho UI sản-phẩm giao user.

## Approaches
**(A) Cài hallmark như một skill design nữa, để nguyên.** Rẻ nhất. Nhưng bỏ lỡ đúng giá trị user hỏi ("chuẩn mặc định và tối thiểu") — nó thành cái thứ 15, và p-23 vẫn mở.

**(B) Viết lại nền design của riêng ta lấy cảm hứng hallmark.** Kiểm soát tối đa. Nhưng dựng lại 57 cổng + 21 macrostructure + 4 genre là hàng tháng, và ta sẽ có một bản kém hơn bản đã battle-tested. Tự mâu thuẫn với ladder chống over-engineering.

**(C) — chọn.** Cài hallmark nguyên bản (provenance) làm **nền**, rồi chưng cất phần *grep được* của slop-test vào cổng tất định `frontend-antipattern.py` để cưỡng chế trên chính HTML ta sinh, và nối catalog vào `/propose` làm nguồn fill-default. Đây là bậc "đổi cấu trúc" của Meadows: một nền chung + một cổng cưỡng chế thay cho 14 skill mỗi cái tự mang luật. Đóng p-23.

## Plan

- [ ] **T1 — Cài hallmark làm nền (provenance).** `/skill-provenance` ghi nguồn `Nutlope/hallmark` + sha256, rồi cài `skills/hallmark/` (SKILL.md + toàn bộ `references/`) vào canonical + mirror. Model-invoked (dựng UI là việc model bắt được ngữ cảnh — "làm cho tôi một landing page"). KHÔNG sửa nội dung gốc.

- [ ] **T2 — Hoà giải với 14 skill design đang có.** Thêm một câu vào mỗi skill taste (hoặc một concept `design-foundation` mà chúng trỏ tới): *"đứng trên nền hallmark — 6 discipline + slop-test là sàn; skill này thêm flavour lên trên, không thay sàn."* Bảng skill nói rõ hallmark là **default/foundation**, các skill kia là style cụ thể. Đóng đúng phần "8 skill mỗi cái tự mang luật" của p-23.

- [ ] **T3 — Nâng cổng tất định `frontend-antipattern.py` bằng slop-test grep được.** Thêm các cổng cơ học: gradient text (`background-clip:text` + gradient), font Inter/Roboto/Poppins/system làm display, pure `#000`/`#fff` làm base, italic header (`<h*>` chứa `<em>`/`font-style:italic`), fake browser chrome (URL pill + traffic-light dots vẽ tay), card-in-card, thick side-stripe border, số liệu bịa (regex `+NN%`, `Nx faster`, `trusted by N+` không có nguồn — khớp anti-fabrication ta đã có). Áp cho MỌI `*.html` ta sinh. **Báo cáo** ở artifact kỹ thuật, **có thể chặn** ở UI sản phẩm. Wired sẵn vào `medic` probe `p_frontend`.

- [ ] **T4 — Bite-test cổng slop.** Fixture BAD (HTML có gradient text + Inter + #000 + italic header) → bị bắt; fixture GOOD → sạch. Thêm vào self-test của `frontend-antipattern.py` (`--self-test`) và một case vào repo-health. Chứng minh cổng CẮN, không phải đồ trang trí.

- [ ] **T5 — Nối fill-default vào `/propose`.** Thêm vào mục "fact/decision" của propose: lựa chọn thiết kế mà user KHÔNG nói (macrostructure, theme, type-pairing, màu anchor) là **decision rủi ro thấp** → không hỏi, fill từ catalog hallmark (`references/macrostructures/`, `references/genres/`), gắn tag `(default)` và ghi tên macrostructure/theme đã chọn vào `## Assumptions`. User đổi được. Đây là "nguồn tham chiếu để fill unknown" user yêu cầu, cắm vào đúng hệ `(default)` đã có.

- [ ] **T6 — Áp cổng lên chính artifact của ta (dogfood).** Chạy cổng nâng cấp lên `llmwiki/html/*.html` ta đã sinh (seq, report, overstack). Sửa vi phạm UNIVERSAL nào lộ ra (nếu có fake chrome / gradient text / italic header). Đây là bằng chứng "HTML tự sinh bị soi cùng chuẩn" — phần còn lại của p-23.

- [ ] **T8 — Bộ nhớ thiết kế TRAVEL-ĐƯỢC (`.hallmark/log.json`) → cổng Variety xuyên workflow.** Đây là cấu trúc data duy nhất của hallmark travel được, và là thứ đưa slop-test ra khỏi phạm-vi-một-lần thành cưỡng-chế-xuyên-phiên. Adopt một file bộ nhớ build (đi theo repo, nguồn chân lý cục bộ): mỗi HTML ta sinh stamp `{date, macrostructure, theme, theme_axes, nav, footer, brief}`. Cổng Variety (đã có trong slop-test gate 8 + trục F) đọc log này → trang mới PHẢI khác **cấu trúc** trang trước (structural distance, không phải colour-swap). Nối vào ledger/stamp ta đã có thay vì đẻ store mới. **Bằng chứng phải đối mặt:** mọi `*-seq.html` ta sinh hiện dùng CÙNG một glass template — theo trục Variety chúng là slop (colour-swap của cùng một fingerprint). Task này vừa cấp cơ chế phát hiện, vừa buộc ta thừa nhận và (ít nhất) đa dạng hoá dần các template artifact.

- [ ] **T7 — Register + cổng + UAT.** `sync-skill.sh hallmark`; regen `CAPABILITIES.md` + `overstack.html`; `capability-stamp --update`; append `wiki/index.md` + `log.md`; cập nhật p-23 (solved theo độ phủ) + node mới; `medic --ci` + repo-health local; `/fdk-uat` hai pha (canary → main-URL smoke, sentinel grep-verify).

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| T1 — cài hallmark (provenance) | Claude | Cài skill ngoài + provenance, nhiều file, phải đúng | pending |
| T2 — hoà giải 14 skill design | Claude | Phán đoán "flavour vs foundation", nuance | pending |
| T3 — nâng frontend-antipattern.py | Claude | Cổng tất định, regex sai là bắt nhầm/sót | pending |
| T4 — bite-test cổng slop | OpenCode `big-pickle` (fallback Claude) | Cơ học: viết fixture BAD/GOOD + assert. Watchdog 60–90s | pending |
| T5 — fill-default vào /propose | Claude | Hợp đồng skill trung tâm | pending |
| T6 — dogfood cổng lên artifact ta | Claude | Đọc-hiểu vi phạm, sửa đúng chỗ | pending |
| T8 — bộ nhớ thiết kế travel-được (Variety) | Claude | Chạm ledger/stamp (nguồn chân lý) + đối mặt slop chính artifact ta | pending |
| T7 — register + cổng + UAT | OpenCode `big-pickle` (fallback Claude) | Cơ học: script có sẵn + UAT. Watchdog 60–90s | pending |

**Sequence diagram:** [150726-hallmark-design-foundation-seq.html](../../../html/150726-hallmark-design-foundation-seq.html)

## Requirements (FR)
- **FR-001**: Hallmark PHẢI được cài làm nền design, qua `/skill-provenance` (nguồn + sha256), không sửa nội dung gốc.
- **FR-002**: 14 skill design hiện có PHẢI được hoà giải thành "flavour trên nền hallmark", không cái nào bị xoá hay cạnh tranh với nền.
- **FR-003**: `frontend-antipattern.py` PHẢI mang các cổng slop-test grep được (gradient text, font AI-default làm display, pure đen/trắng, italic header, fake chrome, card-in-card, số liệu bịa).
- **FR-004**: Cổng slop PHẢI có bite-test (BAD bị bắt, GOOD sạch) và wired vào medic + repo-health.
- **FR-005**: `/propose` PHẢI fill lựa chọn thiết kế user không nói từ catalog hallmark, tag `(default)`, ghi vào `## Assumptions`.
- **FR-006**: Cổng UNIVERSAL PHẢI áp cho mọi HTML ta sinh; cổng genre/structural KHÔNG áp cho artifact kỹ thuật.
- **FR-007**: Chính artifact HTML của ta (seq/report/overstack) PHẢI được soi bằng cổng nâng cấp, vi phạm universal PHẢI được sửa.
- **FR-008**: PHẢI có một bộ nhớ thiết kế **travel-được** (theo repo) stamp mỗi HTML sinh ra, để cổng Variety đọc và chặn trang mới lặp cấu trúc trang trước — xuyên workflow, xuyên phiên, không nhờ model nhớ.

## Success criteria (SC)
- **SC-001**: Một trang UI mới dựng qua overstack **không mang năm dấu hiệu AI dễ nhận nhất** (gradient tím, Inter khắp nơi, 3-cột-icon-tile, hero centred-100vh, italic header) — cổng bắt được nếu có.
- **SC-002**: Người dùng dựng UI mà **không nói gì về thiết kế** vẫn nhận một trang có macrostructure + theme chọn *hợp brief*, không phải template mặc định — và thấy rõ trong `## Assumptions` cái gì máy chọn.
- **SC-003**: HTML do chính framework sinh (report, seq, overstack) **bị soi cùng một chuẩn** với UI giao user — p-23 đóng.
- **SC-004**: Người viết một skill design mới **được chỉ tới nền chung** thay vì tự bịa luật — 14 skill thôi mỗi cái một kiểu.
- **SC-006**: Hai trang ta sinh cho hai brief khác nhau **khác nhau về CẤU TRÚC**, không phải colour-swap của cùng một template — cổng Variety đọc bộ nhớ travel-được và bắt nếu lặp.
- **SC-005**: Cổng slop **cắn được ở dự án curl-cài** (frontend-antipattern travel xuống global harness) — chứng minh bằng `/fdk-uat`.

## Assumptions
Trường user không nói, model tự điền — mọi dòng `(default)`, sửa được:
- Hallmark cài **model-invoked** `(default)` — dựng UI là việc model bắt được ngữ cảnh; khác nhóm framework-dev vừa tắt.
- Cổng slop **báo-cáo ở artifact kỹ thuật, có-thể-chặn ở UI sản phẩm** `(default)` — seq.html có glass riêng (R11), ép nó theo hallmark là sai chỗ.
- Chỉ lấy **nhóm cổng grep được** vào frontend-antipattern.py `(default)`; nhóm cần phán đoán thị giác để nguyên trong SKILL.md hallmark (model chạy lúc dựng UI).
- Fill-default lấy từ `references/macrostructures/` + `references/genres/` `(default)` — đó là catalog cấu trúc + genre, đúng tầng "lựa chọn mặc định".
- Giữ `docs-site-macos` làm theme artifact nội bộ, **không** thay bằng hallmark `(default)`.

Không mục nào rơi `[CẦN LÀM RÕ]`: thay đổi nội-bộ framework, không chạm auth/dữ-liệu/tiền/pháp-lý.

## Risks
- **Nâng cổng bắt nhầm chính artifact ta** — seq.html của ta CÓ dùng gradient (nền glass) và có thể có cấu trúc hallmark ghét. Giảm thiểu: tách cổng universal (áp mọi nơi) khỏi cổng genre (chỉ UI sản phẩm); gradient *nền* khác gradient *text* — chỉ cấm text. T6 dogfood để lộ nhầm sớm.
- **57 cổng → regex mong manh.** Giảm thiểu: chỉ lấy nhóm cơ học rõ ràng, mỗi cổng một bite-test; cổng nào regex không chắc thì để nguyên trong SKILL.md cho model, không đưa xuống tất định.
- **Hallmark 558 dòng + 100 file làm phình repo + context.** Giảm thiểu: model-invoked nhưng reference nạp on-demand (progressive disclosure — chỉ SKILL.md vào context, catalog nạp khi cần). Đo context load sau, ghi số thật.
- **Provenance skill ngoài đổi ở upstream.** Giảm thiểu: `/skill-provenance` ghi sha256; drift phát hiện được. Không auto-update.

## Self-review
- **Phủ yêu cầu:** FR-001→T1 · FR-002→T2 · FR-003→T3 · FR-004→T4 · FR-005→T5 · FR-006→T3 (phạm vi) · FR-007→T6 · FR-008→T8. T7 là cổng. Không FR nào không có task.
- **Placeholder:** không còn mục bỏ trống.
- **Nhất quán tên:** skill là `hallmark`; cổng là `frontend-antipattern.py`; nền khái niệm gọi "6 discipline + slop-test"; catalog là `references/macrostructures/` + `references/genres/`; đóng `p-23`.

## Notes
- Nguồn ngoài: `scratchpad/hallmark/` (clone `Nutlope/hallmark`, Together AI). 20 theme · 4 verb · 57 cổng slop-test · pre-emit critique 6 trục.
- Đóng `p-23`; thay thế orphan `060726-design-standard-ai-elite-PLAN`.
- Xây tiếp trên [[150726-mattpocock-absorb]] (tag `(default)` + fact/decision) và [[skill-craft]].

## Origin
- **Draft:** `wiki/sources/draft/150726-hallmark-design-foundation.md`
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
