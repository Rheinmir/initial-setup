---
type: draft
title: spec-kit-traceability
status: proposed
tags: [propose, plan, spec-kit, traceability, fdk-uat]
timestamp: 2026-07-14
task: T-260714-02
---

# 140726-spec-kit-traceability

**Status:** proposed

## What
Hấp thụ ba thứ tốt nhất của `github/spec-kit` vào `/propose` + `/plan` — **id ổn định cho từng yêu cầu** (`FR-xxx` / `SC-xxx`) để truy vết được SPEC→PLAN→task, **cặp tag `(default)` / `[CẦN LÀM RÕ]`** phân biệt lời user với phỏng đoán của model, và **tiêu chí thành công đo được, không dính công nghệ** — đồng thời sửa một lỗi thiết kế trong `/fdk-uat`: cho nó test đường remote thật qua **nhánh canary** thay vì bắt nhánh chính mang bản chưa nghiệm thu.

## Context
Đã query wiki + đọc nguồn ngoài trước khi soạn (force-query, R7-f):

- `ADR-003 (skill-as-single-source-of-truth)` — hành vi propose/plan chỉ định nghĩa ở `skills/<tên>/SKILL.md`; mirror sinh bằng `sync-skill.sh`.
- SPEC `140726-propose-plan-split-superpowers` (đã giao, commit `36cf02e`) — vừa dựng bộ ba SPEC/PLAN/HTML, R7 hai nhánh, R18 travel downstream. Đề xuất này **xây tiếp trên đó**, không xây lại.
- `skills/plan/SKILL.md` § Self-review mục 1 ("phủ SPEC — lướt từng yêu cầu, chỉ ra được task nào thực hiện nó") — hiện là **lời hứa của model**, không có gì cưỡng chế. Đây chính là chỗ đề xuất này biến thành cổng.
- `skills/br/SKILL.md` — `/br compile` đã sinh **`clause_id`** cho từng điều khoản BR. Khái niệm "id ổn định để truy vết" **đã tồn tại trong framework**, chỉ chưa có ở đường `/propose` nhẹ.
- `CLAUDE.md` § carve-out — "không lười ở: validation tại trust boundary, error-handling chống mất data, security, a11y, và bất cứ thứ gì user yêu cầu rõ". Đây là nền lý luận cho marker `[CẦN LÀM RÕ]`.
- Nguồn ngoài: `scratchpad/spec-kit/` (clone `github/spec-kit`) — đọc `templates/spec-template.md`, `templates/plan-template.md`, `templates/constitution-template.md`, `templates/commands/{clarify,analyze}.md`.

**Kết luận từ đối chiếu:** spec-kit đã làm đúng cái user mô tả — `## Assumptions` của họ định nghĩa nguyên văn là *"reasonable defaults chosen when the feature description did not specify certain details"*, và `/clarify` là opt-in, trần 5 câu. Nhưng họ có thêm một lớp ta chưa có: **`[NEEDS CLARIFICATION: ...]`** — nhóm trường mà model **từ chối đoán** (ví dụ ngay trong template của họ: cơ chế auth, thời hạn lưu dữ liệu). Autofill mà không có lớp này thì `(default)` thành cái máy hợp thức hoá phỏng đoán ở đúng chỗ nguy hiểm nhất.

## Global constraints
- **ADR-003:** sửa hành vi ở `skills/<tên>/SKILL.md` (canonical); mirror + bản cài sinh bằng `bash fdk/tools/sync-skill.sh <tên>` — cấm `cp` tay.
- **Không đẻ rule id mới:** mở rộng R7 (SPEC) và R18 (PLAN) tại `harness/validators/proposal_complete.py`. Rule nào đổi thì **cả hai** `harness/policy.yaml` và `harness/poc-vendor-neutral/policy.yaml` phải sửa giống hệt (gate `policy-converters-drift`).
- **Luật mới phải TỚI ĐƯỢC downstream:** check nào chỉ sống trong validator Python thì downstream (chạy engine khai báo) không nhận. Bài học `p-26` — mọi luật mới phải tự hỏi "nó cắn được ở dự án curl-cài không?".
- **Rule mới/đổi phải có bite-test** ở cả hai tầng: `build_rN` trong `harness-doctor` và case trong `test-broad.sh`.
- **Tương thích ngược:** SPEC/PLAN cũ (đã `implemented`/`done`) không được đỏ lên.
- **Không ghi công AI** trong commit/PR/wiki (R15).
- **Trước push:** `medic --ci` xanh + trọn job `repo health` local + **`/fdk-uat` PASS** (nhánh canary).

## Non-goals
- **Không** thêm `constitution.md`. Ta đã có `CLAUDE.md` (cái thang) + `## Global constraints` trong SPEC. File thứ tư là nợ.
- **Không** bê pipeline 9 lệnh của spec-kit (`specify/clarify/plan/tasks/analyze/checklist/implement/constitution/converge`), không bê `extensions.yml`, không bê branch-per-feature.
- **Không** thêm `/clarify` riêng — `/br interview` đã phủ. Chỉ mượn **trần 5 câu, ưu tiên Impact × Uncertainty**.
- Không đụng dispatch / persona / archetype.

## Approaches
**(A) Bê nguyên bộ template spec-kit** (User Stories P1/P2/P3, Edge Cases, Key Entities, Checklist, `/analyze`). Đầy đủ nhất, nhưng SPEC phình gấp mấy lần và ta vừa mất công dựng cổng để SPEC *đọc được*. Tự mâu thuẫn với chính lý do tách SPEC/PLAN hôm nay.

**(B) Chỉ lấy id `FR-xxx` + cổng truy vết**, bỏ phần tag. Rẻ nhất, và là món giá trị nhất. Nhưng bỏ mất đúng thứ user hỏi (`(default)`), và để hở lớp "model đoán thầm chỗ nguy hiểm".

**(C) — chọn.** Lấy ba món: id + truy vết (biến self-review thành cổng grep được), cặp `(default)` / `[CẦN LÀM RÕ]`, và tiêu chí thành công đo-được-không-dính-công-nghệ. Bỏ constitution, bỏ pipeline, bỏ `/clarify`. Kèm sửa `/fdk-uat` sang nhánh canary. Đắt hơn (B) đúng hai check validator và một mục trong hai skill.

## Plan

- [ ] **T1 — SPEC mang id + tag (`skills/propose/SKILL.md`).** Yêu cầu trong SPEC được đánh id ổn định: `FR-001`, `FR-002`… (Functional Requirement) và `SC-001`, `SC-002`… (Success Criterion). Thêm `## Assumptions` — nơi liệt kê mọi trường model **tự điền vì user không nói**, mỗi dòng gắn tag **`(default)`**. Và marker **`[CẦN LÀM RÕ: <câu hỏi>]`** cho nhóm model **KHÔNG được đoán thầm**: cơ chế xác thực/phân quyền, thời hạn & phạm vi lưu dữ liệu, tiền/thanh toán, thứ có hệ quả pháp lý, và bất cứ ranh giới tin cậy nào (khớp carve-out `CLAUDE.md`). Mặc định là **autofill + tag**, KHÔNG hỏi — chỉ leo lên `[CẦN LÀM RÕ]` khi rơi vào nhóm nguy hiểm đó.

- [ ] **T2 — `SC-xxx` phải ĐO ĐƯỢC và KHÔNG dính công nghệ (`skills/propose/SKILL.md`).** "User hoàn tất tạo tài khoản dưới 2 phút" / "chịu 1000 người đồng thời" — chứ không phải "chạy lệnh X ra exit 0" (đó là đo *cái máy*, không đo *người dùng nhận được gì*). Cách kiểm ở tầng máy vẫn ghi, nhưng ghi như **bằng chứng** của `SC-xxx`, không thay thế nó.

- [ ] **T3 — PLAN khai mình thoả id nào (`skills/plan/SKILL.md`).** Mỗi `### Task N` thêm dòng `**Thoả:** FR-001, FR-003` — task này thực hiện những yêu cầu nào của SPEC. Đây là thứ biến câu "phủ hết SPEC" trong Self-review từ lời hứa thành dữ liệu grep được.

- [ ] **T4 — CỔNG TRUY VẾT + cổng unknown (`harness/validators/proposal_complete.py`).** Nhánh SPEC thêm **(n)**: SPEC còn `[CẦN LÀM RÕ: ...]` chưa được trả lời thì **chặn ở cổng duyệt** — user phải trả lời hoặc chuyển nó thành `(default)` có chủ ý. Nhánh PLAN thêm **(o)**: đọc SPEC anh em (cùng stem, bỏ hậu tố `-PLAN`), gom mọi `FR-xxx`, và **mọi id phải xuất hiện ở ≥1 dòng `**Thoả:**`** — thiếu một cái là chặn, in ra đúng id bị bỏ rơi. Không tìm thấy SPEC anh em → fail-open (PLAN đứng một mình vẫn hợp lệ).

- [ ] **T5 — luật mới phải TỚI downstream (`harness/policy.yaml` + `harness/poc-vendor-neutral/policy.yaml`).** Bản khai báo diễn tả được phần "contains": SPEC có `[CẦN LÀM RÕ` → chặn (dùng cơ chế forbid nếu engine hỗ trợ, không thì ghi rõ TRẦN). Phần truy vết per-id chỉ validator Python làm được → khai trần trong `note:`, đúng cách R18 đã làm. Bite-test cả hai tầng.

- [ ] **T6a — tham số hoá ref cài skill (`harness/poc-vendor-neutral/install.sh:249`).** Hiện `npx -y skills add rheinmir/setup#orca --global --all` **hardcode `#orca`, không có đường override** — trong khi `HARNESS_BASE` (bootstrap.sh:17) và `REPO_RAW` (install.sh:169) thì có. Hệ quả: cài từ một nhánh khác vẫn kéo **skill của `orca`**. Đổi thành `SKILLS_REF="${SKILLS_REF:-rheinmir/setup#orca}"`. Không có bước này thì toàn bộ T6b là ảo giác — nó sẽ test bản cũ mà báo là đã nghiệm thu bản mới.

- [ ] **T6b — `/fdk-uat` thành HAI PHA (`skills/fdk-uat/SKILL.md`).** Canary và main-URL kiểm hai thứ khác nhau, không cái nào thay được cái nào.
  - **Pha 1 — canary, TRƯỚC merge:** đẩy lên nhánh tạm `uat/<yymmdd-HHMM>` → dựng dự án trống → `curl` bootstrap từ raw của **chính nhánh đó**, truyền `HARNESS_BASE` + `REPO_RAW` + `SKILLS_REF` trỏ về canary → UAT đầy đủ (3 trụ · harness cắn · **năng lực mới cắn thật** · orchestration-ready). PASS mới merge vào nhánh chính. FAIL thì xoá nhánh canary — nhánh chính **chưa hề bị bẩn**. Đây là thứ giữ được SC-004.
  - **Pha 2 — main-URL smoke, NGAY SAU merge:** chạy **đúng lệnh người mới gõ** — `curl .../<nhánh chính>/bootstrap.sh | bash`, **không override một biến nào**. Chỉ pha này mới kiểm được các giá trị **mặc định**, mà mặc định chính là chỗ chứa chuỗi nhánh hardcode. Rút gọn: 3 trụ + `test-broad` + skill mới reachable (~1 phút). FAIL → `revert` ngay.
  - Giữ `revert` / `reset --force-with-lease` làm đường lùi. Cửa sổ rủi ro của nhánh chính thu từ "cả bài UAT" xuống "một lần smoke ~1 phút".

- [ ] **T7 — trần 5 câu cho interview (`skills/br/SKILL.md`).** Mượn đúng một chi tiết của `/clarify`: interview tối đa **5 câu**, chọn theo (Impact × Uncertainty), ưu tiên nhóm chưa rõ có tác động cao (an ninh, dữ liệu) trước. Interview không giới hạn là interview user bỏ giữa chừng.

- [ ] **T8 — register + parity + cổng.** `sync-skill.sh` cho propose/plan/fdk-uat/br; regen `CAPABILITIES.md` + `overstack.html`; `capability-stamp --update`; append `wiki/index.md` + `log.md`; node vào `fdk-problem-tree.html`; `medic --ci` + repo-health local; **`/fdk-uat` canary PASS** rồi mới push.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| T1 — SPEC id + tag | Claude | Hợp đồng skill trung tâm, chạm định nghĩa "cái gì được đoán / cái gì không" | pending |
| T2 — SC đo được | Claude | Cùng file với T1, làm liền tay | pending |
| T3 — PLAN khai `**Thoả:**` | Claude | Hợp đồng skill | pending |
| T4 — cổng truy vết + unknown | Claude | Validator fail-closed, sai regex là chặn nhầm cả repo | pending |
| T5 — policy ×2 + travel downstream | Claude | Có gate drift trên CI; bài học p-26 | pending |
| T6a — tham số hoá `SKILLS_REF` | Claude | Chạm đường cài của mọi người dùng — sai một dòng là hỏng install | pending |
| T6b — /fdk-uat hai pha | Claude | Chạm quy trình push/remote — không giao model rẻ | pending |
| T7 — trần 5 câu interview | OpenCode `big-pickle` (fallback Claude) | Cơ học: thêm một mục vào SKILL.md có sẵn. Watchdog 60–90s | pending |
| T8 — register + parity + cổng | OpenCode `big-pickle` (fallback Claude) | Cơ học thuần: chạy script có sẵn, append index/log | pending |

**Sequence diagram:** [140726-spec-kit-traceability-seq.html](../../../html/140726-spec-kit-traceability-seq.html)

## Requirements (FR)
- **FR-001**: SPEC PHẢI đánh id ổn định `FR-xxx` cho từng yêu cầu chức năng và `SC-xxx` cho từng tiêu chí thành công.
- **FR-002**: SPEC PHẢI có `## Assumptions`, mỗi dòng model tự điền gắn tag `(default)`.
- **FR-003**: Model PHẢI leo lên marker `[CẦN LÀM RÕ: ...]` thay vì đoán thầm, khi trường rơi vào nhóm: xác thực/phân quyền · lưu trữ & thời hạn dữ liệu · tiền/thanh toán · hệ quả pháp lý · ranh giới tin cậy.
- **FR-004**: Mỗi `### Task` trong PLAN PHẢI khai `**Thoả:** FR-xxx[, FR-yyy]`.
- **FR-005**: R7 PHẢI chặn SPEC còn `[CẦN LÀM RÕ]` chưa trả lời tại cổng duyệt.
- **FR-006**: R18 PHẢI chặn PLAN bỏ sót bất kỳ `FR-xxx` nào của SPEC anh em, và in ra id bị bỏ rơi.
- **FR-007**: `/fdk-uat` PHẢI test được đường remote thật **mà không** đẩy bản chưa nghiệm thu lên nhánh chính.
- **FR-008**: Interview (`/br`) PHẢI có trần 5 câu, ưu tiên theo Impact × Uncertainty.
- **FR-009**: `install.sh` PHẢI cho phép override ref cài skill (`SKILLS_REF`) — không thì cài-từ-nhánh-khác vẫn kéo skill của nhánh chính, và mọi bài test trên nhánh tạm đều là ảo giác.
- **FR-010**: `/fdk-uat` PHẢI có pha kiểm **đúng lệnh mặc định người mới gõ** (không override biến nào) — canary không thay thế được, vì canary chạy với ref khác và biến override, nên mù với chính các giá trị mặc định.

## Success criteria (SC)
- **SC-001**: Một người viết PLAN bỏ sót một yêu cầu của SPEC thì **bị chặn ngay lúc ghi file**, kèm tên id bị bỏ — không phải phát hiện lúc review hay lúc agent giao hàng thiếu.
- **SC-002**: Người duyệt SPEC **phân biệt được bằng mắt** đâu là điều mình nói, đâu là điều model tự điền — mọi dòng model điền đều mang tag `(default)`.
- **SC-003**: Không có quyết định thuộc nhóm nguy hiểm (auth, lưu dữ liệu, tiền, pháp lý) nào lọt qua cổng duyệt dưới dạng phỏng đoán im lặng.
- **SC-004**: Nhánh chính (`orca`) **không có khoảng thời gian nào** mang commit chưa qua UAT.
- **SC-005**: Luật mới cắn được ở một dự án cài overstack bằng `curl` — chứng minh bằng `/fdk-uat` PASS, không phải bằng lời.

## Assumptions
Những trường user không nói, model tự điền — mọi dòng dưới đây là `(default)`, sửa được:
- Hậu tố id dùng `FR-` / `SC-` như spec-kit, không Việt hoá thành `YC-`/`TC-` `(default)` — giữ nguyên để đối chiếu với nguồn ngoài dễ hơn.
- Marker viết tiếng Việt `[CẦN LÀM RÕ: ...]` thay vì `[NEEDS CLARIFICATION]` `(default)` — repo này viết tài liệu người-đọc bằng tiếng Việt.
- Nhánh canary đặt tên `uat/<yymmdd-HHMM>` và **xoá sau khi xong** dù pass hay fail `(default)`.
- Cổng truy vết chỉ đối chiếu `FR-xxx`, **không** ép `SC-xxx` phải map vào task `(default)` — tiêu chí thành công là kết quả của cả bộ, không của một task lẻ.
- PLAN không tìm thấy SPEC anh em → **fail-open** (không chặn) `(default)` — PLAN đứng một mình vẫn là trường hợp hợp lệ.

Không có mục nào rơi vào nhóm `[CẦN LÀM RÕ]`: thay đổi này thuần nội-bộ framework, không chạm xác thực, dữ liệu người dùng, tiền, hay ranh giới tin cậy.

## Risks
- **Cổng truy vết (o) chặn nhầm khi SPEC dùng id trong văn xuôi.** Ví dụ câu "FR-003 nói rằng…" trong phần Risks cũng bị bắt là một yêu cầu. Giảm thiểu: chỉ quét id trong section `## Requirements (FR)`, không quét cả file.
- **PLAN cũ không có `**Thoả:**` sẽ đỏ.** Chỉ ảnh hưởng PLAN còn `proposed`; repo hiện có 2 file `-PLAN.md` cũ — phải kiểm và vá hoặc để chúng ở trạng thái đã xong.
- **`(default)` bị lạm dụng** — model gắn tag rồi coi như xong, người duyệt lướt qua vì "trông như đã xong". Đây đúng là lý do FR-003 tồn tại; nếu vẫn xảy ra thì phải siết bằng cách bắt `## Assumptions` xuất hiện trong phần tóm tắt gửi kèm cổng duyệt.
- **Canary là ẢO GIÁC nếu quên T6a.** `install.sh:249` hardcode `rheinmir/setup#orca` → cài từ nhánh tạm vẫn kéo skill của nhánh chính. Không tham số hoá thì UAT sẽ chấm bản CŨ và báo PASS. Đây là rủi ro nguy hiểm nhất trong đề xuất, vì nó làm cổng **nói dối mà vẫn xanh**.
- **Nhánh canary rác** nếu phiên chết giữa chừng. Giảm thiểu: `/fdk-uat` xoá nhánh ở cả nhánh pass lẫn fail, và bước 0 liệt kê nhánh `uat/*` còn sót để dọn.

## Self-review
- **Phủ yêu cầu:** FR-001→T1 · FR-002→T1 · FR-003→T1 · FR-004→T3 · FR-005→T4 · FR-006→T4 · FR-007→T6b · FR-008→T7 · FR-009→T6a · FR-010→T6b. T2 phục vụ SC-002/SC-003 (chất lượng tiêu chí), T5 phục vụ SC-005 (travel downstream), T8 là cổng. Không FR nào không có task.
- **Placeholder:** không còn mục nào bỏ trống hay hẹn "sau".
- **Nhất quán tên:** id là `FR-xxx`/`SC-xxx` (không `REQ-`); tag là `(default)`; marker là `[CẦN LÀM RÕ: ...]`; dòng khai trong PLAN là `**Thoả:**`; nhánh tạm là `uat/<yymmdd-HHMM>`. Dùng thống nhất xuyên suốt SPEC này và phải dùng đúng như vậy trong code.

## Notes
- Nguồn ngoài: `scratchpad/spec-kit/` (clone `github/spec-kit`) — `templates/spec-template.md` (§ Assumptions, § `[NEEDS CLARIFICATION]`), `templates/commands/clarify.md` (trần 5 câu, Impact × Uncertainty), `templates/commands/analyze.md` (đối chiếu chéo spec↔plan↔tasks).
- Xây tiếp trên `[[140726-propose-plan-split-superpowers]]` (commit `36cf02e`, `c5efc57`).

## Origin
- **Draft:** `wiki/sources/draft/140726-spec-kit-traceability.md`
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
