---
type: draft
title: mattpocock-absorb
status: proposed
tags: [skills, wayfinder, issue-tracker, context-load, mattpocock]
timestamp: 2026-07-15
task: T-260715-01
---

# 150726-mattpocock-absorb

**Status:** proposed

## What
Hấp thụ trọn bộ phần tốt của `mattpocock/skills` ("Skills for Real Engineers", 39 skill) vào overstack theo ba trục: **cắt context load** (76/76 skill của ta đang model-invoked, tốn ~7.400 token mỗi lượt mọi phiên), **thêm tầng điều phối cho ledger issue** (nhãn `ready-for-agent`, cạnh chặn, claim — ba thứ ta không có gì tương đương dù chạy fan-out nhiều agent), và **thêm một năng lực mới `/wayfinder`** cho việc quá lớn với một phiên agent.

## Context
Đã query wiki + đọc nguồn ngoài trước khi soạn (force-query, R7-f):

- `ADR-003 (skill-as-single-source-of-truth)` — hành vi skill định nghĩa ở `skills/<tên>/SKILL.md`; mirror sinh bằng `sync-skill.sh`.
- `ADR-005 (logger-and-capabilities-travel-downstream)` + `[[ADR-017-global-shared-engine-repo-data-travel]]` — engine ở global, dữ liệu đi theo repo. Ledger issue nằm phía **dữ liệu**, nên mọi thay đổi schema phải travel được.
- `ADR-015 (boris-archetypes-into-template)` — persona theo archetype khi dispatch. Nhãn `ready-for-agent` ăn khớp trục này: nó nói *việc nào* giao máy được, archetype nói *giao cho vai nào*.
- `skills/raise-issue/SKILL.md` + `llmwiki/wiki/sources/ISSUES.md` — ledger local là nguồn chân lý, tracker remote là mirror. Bảng hiện có đúng 7 cột: `id · kind · tiêu đề · status · assignee · entry · tracker`. **Không có** `blocked_by`, không có nhãn agent-readiness, không có giao thức claim.
- SPEC `140726-propose-plan-split-superpowers` và `140726-spec-kit-traceability` (đã giao) — bộ ba SPEC/PLAN/HTML, R7 hai nhánh, R18 truy vết `FR-xxx`. Đề xuất này **xây tiếp**, không xây lại.
- Nguồn ngoài: `scratchpad/mattpocock-skills/` — đọc `skills/productivity/writing-great-skills/SKILL.md`, `skills/engineering/wayfinder/SKILL.md`, `skills/engineering/to-tickets/SKILL.md`, `skills/engineering/triage/SKILL.md`, `skills/engineering/setup-matt-pocock-skills/{SKILL.md,issue-tracker-github.md,triage-labels.md}`, `skills/productivity/grilling/SKILL.md`.

**Ba kết luận đo được, không phải cảm tính:**

1. **Context load.** 76/76 skill của ta là model-invoked; `disable-model-invocation` xuất hiện **0 lần**. Tổng description ≈ **29.848 ký tự ≈ 7.462 token**, nằm trong context **mọi lượt, mọi phiên**, kể cả phiên không đụng tới skill nào. Mattpocock tắt **24/39** skill: skill chỉ-gọi-tay không trả context load nào, đổi lại người dùng phải nhớ tên — và cái đó chữa bằng **router skill** (ta đã có `/find-skills` + `CAPABILITIES.md`).

2. **Điều phối issue.** Họ có ba thứ ta không có: nhãn **`ready-for-agent` / `ready-for-human`** (việc nào agent được tự lấy chạy AFK), **cạnh chặn** giữa issue (→ tính được **frontier** = mở ∧ không-bị-chặn ∧ chưa-ai-nhận), và **claim = assign, là thao tác ghi ĐẦU TIÊN** của phiên (chống hai agent ôm cùng một việc). Ta fan-out nhiều agent mà thiếu cả ba — đây là trục ta yếu nhất.

3. **Wayfinder.** `/propose` giả định hình dạng công việc **đã biết**. Wayfinder dành cho lúc **chưa biết**: dựng bản đồ **quyết định** (không phải lát cắt build), có **fog of war** (biết là sẽ tới nhưng chưa đặt được câu hỏi sắc), **out of scope**, **frontier**, và luật *mỗi phiên chỉ giải một ticket*.

Thứ **ta hơn họ**, giữ nguyên không đánh đổi: ledger local travel-được (họ tracker-first, mất mạng là mù), cưỡng chế tất định bằng validator/hook (skill của họ thuần văn xuôi — chính README của họ nói đó là chủ ý), và problem-tree.

## Global constraints
- **ADR-003:** hành vi skill chỉ định nghĩa tại `skills/<tên>/SKILL.md` (canonical); mirror + bản cài sinh bằng `bash fdk/tools/sync-skill.sh <tên>` — cấm `cp` tay.
- **Skill được skill khác gọi thì PHẢI giữ model-invoked.** `orca-workflow` gọi `/query`, `/propose`, `/plan`; `/propose` bàn giao `/plan`. Tắt model-invocation cho nhóm này là cắt đứt chuỗi gọi.
- **Không đẻ rule id mới:** mở rộng R7/R18 tại `harness/validators/proposal_complete.py`. Rule nào đổi thì **cả hai** `harness/policy.yaml` và `harness/poc-vendor-neutral/policy.yaml` sửa giống hệt (gate `policy-converters-drift`).
- **Luật mới phải TỚI ĐƯỢC downstream** (bài học `p-26`): check chỉ sống trong validator Python thì dự án curl-cài không nhận. Rule mới/đổi phải có bite-test ở **cả hai** tầng (`build_rN` trong `harness-doctor` + case trong `test-broad.sh`).
- **Ledger là nguồn chân lý, tracker remote là mirror** — mọi cột mới phải sống được khi **không có mạng và không có tracker**.
- **Tương thích ngược:** 12 issue đang mở trong `ISSUES.md` không được vỡ; cột mới có giá trị mặc định.
- **Không ghi công AI** trong commit/PR/wiki (R15).
- **Trước push:** `medic --ci` xanh + trọn job `repo health` local + **`/fdk-uat` hai pha PASS** (canary trước merge, main-URL smoke sau merge, có chờ sentinel CDN).

## Non-goals
- **Không** bê hệ triage 5-trạng-thái đầy đủ của họ (`/triage` với verify-claim, redundancy-scan, `.out-of-scope/`). Ta đã có `/orca-issue` (repro-first) và `/raise-issue`. Chỉ lấy **từ vựng nhãn** + ba cơ chế điều phối.
- **Không** bê `/tdd`, `/implement`, `/code-review`, `/research`, `/diagnosing-bugs`, `/prototype` — trùng với cái đã có.
- **Không** đổi tracker thành nguồn chân lý. Ledger local vẫn là gốc.
- **Không** xoá skill nào. Cắt context load bằng cách **tắt model-invocation**, không bằng cách bỏ năng lực.

## Approaches
**(A) Chỉ làm phần cắt context load.** Rẻ nhất, hiệu quả tức thì (~7.4k token/lượt). Nhưng bỏ mất đúng hai thứ mattpocock mạnh nhất, và trục điều phối vẫn hở.

**(B) Làm tất, mỗi thứ một SPEC riêng (5 vòng propose→gate→plan).** Sạch nhất về quy trình, nhưng năm lần gate cho năm thứ dùng chung một hạ tầng (skill + validator + ledger) là nghi lễ thừa; các thay đổi đan vào nhau (nhãn `ready-for-agent` vô nghĩa nếu không có claim).

**(C) — chọn.** Một SPEC, mười task, thi hành **tuần tự** theo đúng thứ tự phụ thuộc: sửa hợp đồng skill trước (T1–T2), rồi lens + cắt tải (T3–T5), rồi tầng điều phối ledger (T6–T7), rồi năng lực mới đứng trên nó (T8 — `/wayfinder` **dùng** cạnh chặn và claim của T7), rồi cổng giao-đúng-việc (T9 — **dùng** nhãn của T6), cuối cùng là cổng phát hành (T10). Một gate, một PLAN, một lần UAT.

## Plan

- [ ] **T1 — `/propose`: luật ba tầng fact / decision-thấp / decision-cao.** Mattpocock (`/grilling`) có một câu làm sắc thêm thứ ta build hôm qua: *"nếu một **fact** tra được bằng cách khám phá môi trường thì tra, đừng hỏi; còn **decision** thì là của tôi"*. Ghép với cặp `(default)` / `[CẦN LÀM RÕ]` thành ba tầng dứt khoát: **fact → TRA, tuyệt đối không hỏi** (đọc file, chạy lệnh, grep — hỏi user một thứ mà `git remote -v` trả lời được là lãng phí lượt của họ) · **decision rủi ro thấp → tự điền + gắn `(default)`** · **decision rủi ro cao → `[CẦN LÀM RÕ]`**. Thêm luật **một câu hỏi một lượt** (hỏi chùm là làm người ta hoang mang) và **luôn kèm phương án khuyến nghị** để user gật một tiếng là xong.

- [ ] **T2 — `/plan`: tracer bullet + expand–contract.** Task hiện là "đơn vị nhỏ nhất có test cycle riêng", nhưng không buộc là **lát cắt DỌC chạy được đầu-cuối**. Đổi: mỗi task là một **tracer bullet** — một lát mỏng xuyên hết các tầng, tự nó chạy được và chứng minh được. **Ngoại lệ có tên: wide refactor** — thay đổi cơ học mà **blast radius** trải khắp codebase (đổi tên một cột, đổi kiểu một symbol dùng chung) thì không lát dọc nào xanh được. Sequence bằng **expand → migrate theo lô (chia lô theo blast radius: per-package, per-directory; mỗi lô một task, bị chặn bởi expand) → contract** (xoá dạng cũ, bị chặn bởi mọi lô migrate). CI xanh từng lô vì dạng cũ vẫn còn.

- [ ] **T3 — Chưng cất `writing-great-skills` thành concept của ta.** Viết `llmwiki/wiki/concepts/skill-craft.md` — bộ từ vựng để soi mọi skill: **predictability** là đức tính gốc (agent đi cùng một *quy trình* mỗi lần chạy, không phải ra cùng một *output*) · **context load ↔ cognitive load** (hai loại phí; mỗi lần chia skill là tiêu một trong hai) · **information hierarchy** (in-skill step → in-skill reference → external reference) + **progressive disclosure** · **completion criterion** phải *kiểm được* và *vét cạn*, không thì agent mắc **premature completion** · **leading word** (một từ đã nằm trong pretraining — *fog of war*, *tracer bullet*, *red* — neo cả một vùng hành vi bằng vài token; ta đang viết ba câu để tả thứ một từ đúng làm được) · năm **failure mode**: **duplication**, **sediment**, **sprawl**, **no-op**, **negation**. `/new-skill` trỏ tới concept này bằng context pointer.

- [ ] **T4 — Cắt context load: tắt model-invocation cho nhóm chỉ-gọi-tay.** Đo trước: 76 skill, ~7.462 token description mỗi lượt. Phân ba nhóm: **(a) PHẢI giữ model-invoked** — skill được skill khác gọi (`query`, `propose`, `plan`, `verify-before-commit`, `impact-check`, `safe-change`) hoặc cần model tự bắt được ngữ cảnh (`orca-issue`, `caveman`, `docs-site-macos`…); **(b) chỉ-gọi-tay → `disable-model-invocation: true`** — `fdk`, `fdk-uat`, `harness-tour`, `harness-update`, `health-check`, `sync-template`, `frontier-scan`, `council`, `orca-eval`, `snapshot-push`, `ovs-notes`, `caveman-help`, `caveman-stats`, `skill-provenance`… ; **(c) mơ hồ → giữ nguyên**, ghi lý do. Đo lại sau, ghi **số thật** vào wiki. `description` của nhóm (b) rút thành một dòng người-đọc (bỏ danh sách trigger — không ai đọc nó nữa).

- [ ] **T5 — `/lint` thêm bước skill-health tất định (0 token).** Một script đếm bằng code, không nhờ model nhớ: tổng token description (cảnh báo khi vượt ngưỡng) · skill nào **thiếu completion criterion** ở các bước · skill nào **nặng negation** (đếm tỉ lệ câu cấm trên câu khẳng định) · skill nào **sprawl** (vượt N dòng mà không có progressive disclosure) · skill nào **duplication** (cùng một luật xuất hiện ở skill + policy + workflow). In ra danh sách xếp hạng, **báo cáo — không chặn** (đây là chất lượng, không phải an toàn).

- [ ] **T6 — Ledger issue: hợp đồng tracker (adapter) + 5 nhãn.** Hiện `/raise-issue` nhét thẳng `gh`/`glab`/`tea` vào ruột skill. Đổi sang mô hình adapter của họ: một **file hợp đồng theo repo** — `llmwiki/wiki/sources/issue-tracker.md` — khai tracker của repo này là gì và **các thao tác được diễn đạt thế nào** (tạo · đọc · gán nhãn · đóng · liệt kê · thêm cạnh chặn · claim). Skill chỉ nói *"publish to the issue tracker"*; hợp đồng nói *cách làm ở repo này*. Mặc định: **local-markdown** (ledger — luôn chạy được, không cần mạng); có `git remote` GitHub → đề xuất mirror `gh`. Kèm **5 nhãn chuẩn**: `needs-triage`, `needs-info`, **`ready-for-agent`**, **`ready-for-human`**, `wontfix` — thêm cột `labels` vào `ISSUES.md`, mặc định `needs-triage`.

- [ ] **T7 — Cạnh chặn + frontier + claim.** Thêm hai cột vào `ISSUES.md`: **`blocked_by`** (danh sách id, rỗng = không bị chặn) và **`claim`** (ai đang giữ + timestamp; rỗng = chưa ai nhận). Viết `harness/scripts/frontier.py` — tất định, 0 token: đọc ledger, in ra **frontier** = issue *open* ∧ *mọi blocker đã đóng* ∧ *chưa ai claim* ∧ nhãn `ready-for-agent` (lọc riêng được `ready-for-human`). Giao thức **claim là thao tác GHI ĐẦU TIÊN** của một phiên nhận việc, trước mọi thứ khác — đây là thứ chống hai agent song song ôm cùng một issue, và ta đang fan-out mà không có nó. Mirror lên GitHub thì dùng dependency native + assignee (theo hợp đồng T6).

- [ ] **T8 — Skill mới `/wayfinder`.** Cho việc **quá lớn với một phiên agent và còn mù mờ** — trước cả khi có SPEC. Dựng một **bản đồ** (một issue gốc trong ledger, nhãn `wayfinder:map`) với các **ticket quyết định** là con của nó — mỗi ticket là *một câu hỏi mà lời giải là một quyết định*, không phải một lát cắt build. Bốn kiểu ticket: `research` (AFK, tra tài liệu) · `prototype` (HITL, làm bản thô để phản ứng) · `grilling` (HITL, hỏi từng câu) · `task` (việc tay phải xong thì mới quyết được). Thân bản đồ có **Destination** (đích, cố định scope) · **Decisions so far** (chỉ mục, một dòng mỗi ticket đã đóng) · **Not yet specified** (fog of war — biết là sẽ tới nhưng chưa đặt được câu hỏi sắc; test phân biệt: *"đặt được câu hỏi cho chính xác chưa"*, KHÔNG phải *"trả lời được chưa"*) · **Out of scope** (bị loại, không bao giờ tốt nghiệp). Luật cứng: **mỗi phiên chỉ giải MỘT ticket** (trừ research), và **claim trước khi làm** (dùng T7). `/wayfinder` là skill **chỉ-gọi-tay** (`disable-model-invocation: true`) — đúng lens T3.

- [ ] **T9 — Giao ĐÚNG LOẠI việc cho đúng phiên (cổng HITL/AFK + kiểu việc trong brief).** Bảng chi phí hiện chỉ trả lời *"model nào làm rẻ nhất"* — nó chưa bao giờ hỏi *"việc này có làm được không cần người không"*. Đó chính là gốc của con số giao-hàng ~1/5: ta dispatch những việc **bản chất là HITL** cho CLI headless **không hỏi lại được**, nên nó **đoán thay người dùng** rồi im lặng. Dựng phép chọn hai chiều, đúng thứ tự:
  1. **Cổng HITL/AFK — chạy TRƯỚC mọi thứ.** Việc cần một người sống trả lời (quyết định thiết kế, đánh đổi, thứ chỉ người dùng biết, truy cập bên ngoài, kiểm thủ công) → nhãn **`ready-for-human`**, **KHÔNG dispatch**. Chỉ việc AFK mới được `ready-for-agent`. Luật cứng, chép từ bản gốc: *một agent grilling mà tự trả lời câu hỏi của chính mình là đã phá vỡ điều này*.
  2. **Kiểu việc → archetype → CLI.** Gắn `kind` cho mỗi task: `research` (AFK — lôi ra một *fact* từ tài liệu/môi trường) · `prototype` (HITL — làm bản thô để người ta có cái phản ứng) · `grilling` (HITL — hỏi từng câu) · `build` (AFK — thi hành theo brief) · `sweep` (AFK — dọn cơ học). Map sang archetype đã có (ADR-015): Prototyper / Builder / Sweeper / Grower / Maintainer → persona preamble → CLI theo bảng chi phí. Bảng chi phí **không đổi**, nó chỉ tụt xuống thành bước cuối thay vì bước đầu.
  3. **Brief KHAI kiểu việc ở dòng đầu.** `dispatch --inject` mở đầu bằng một câu nói thẳng phiên này là phiên gì — *"anh đang giải một QUYẾT ĐỊNH, không phải đi build"* — vì kiểu việc quyết định **hình dạng của phiên**, không chỉ chọn model. Một agent biết mình đang làm gì hành xử khác hẳn một agent nhận một cục mô tả.

- [ ] **T10 — Register + cổng + UAT.** `sync-skill.sh` cho mọi skill đã sửa; regen `CAPABILITIES.md` + `overstack.html`; `capability-stamp --update`; append `wiki/index.md` + `log.md`; node vào `fdk-problem-tree.html`; `medic --ci` + trọn repo-health local; **`/fdk-uat` hai pha** (canary → main-URL smoke có chờ sentinel CDN). Đo lại và **ghi số thật** context load trước/sau.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|------------|--------|
| T1 — /propose 3 tầng fact/decision | Claude | Hợp đồng skill trung tâm, nuance cao | pending |
| T2 — /plan tracer bullet + expand–contract | Claude | Hợp đồng skill; expand–contract sai là vỡ CI hàng loạt | pending |
| T3 — concept skill-craft | Claude | Văn bản định nghĩa chất lượng của mọi skill — không giao model rẻ | pending |
| T4 — tắt model-invocation 76 skill | Claude | Phán đoán "skill nào được skill khác gọi" — sai một cái là đứt chuỗi gọi | pending |
| T5 — /lint bước skill-health | OpenCode `big-pickle` (fallback Claude) | Script đếm tất định, tiêu chí đã khai rõ ở T3. Watchdog 60–90s | pending |
| T6 — hợp đồng tracker + 5 nhãn | Claude | Chạm ledger (nguồn chân lý) + hợp đồng downstream | pending |
| T7 — cạnh chặn + frontier + claim | Claude | Giao thức chống đụng độ đa-agent — sai là mất việc của nhau | pending |
| T8 — skill /wayfinder | Claude | Năng lực mới, đứng trên T7 | pending |
| T9 — cổng HITL/AFK + kiểu việc trong brief | Claude | Chạm luồng dispatch đang chạy; sai cổng là lại giao việc HITL cho máy | pending |
| T10 — register + cổng + UAT | OpenCode `big-pickle` (fallback Claude) | Cơ học: chạy script có sẵn, append index/log. Watchdog 60–90s | pending |

**Sequence diagram:** [150726-mattpocock-absorb-seq.html](../../../html/150726-mattpocock-absorb-seq.html)

## Requirements (FR)
- **FR-001**: `/propose` PHẢI phân ba tầng: **fact** → tra bằng công cụ, không hỏi · **decision rủi ro thấp** → tự điền + tag `(default)` · **decision rủi ro cao** → `[CẦN LÀM RÕ]`.
- **FR-002**: Khi có hỏi, PHẢI hỏi **một câu một lượt**, kèm **phương án khuyến nghị**.
- **FR-003**: Mỗi `### Task` trong PLAN PHẢI là một **tracer bullet** — lát cắt dọc chạy được đầu-cuối.
- **FR-004**: PLAN PHẢI có đường riêng cho **wide refactor**: expand → migrate theo lô → contract, mỗi lô một task với cạnh chặn.
- **FR-005**: Repo PHẢI có concept `skill-craft` làm nguồn chân lý cho việc viết/soi skill, và `/new-skill` PHẢI trỏ tới nó.
- **FR-006**: Skill **chỉ-gọi-tay** PHẢI khai `disable-model-invocation: true`; skill được skill khác gọi PHẢI giữ model-invoked.
- **FR-007**: `/lint` PHẢI có bước skill-health **tất định** (0 token): token description, thiếu completion criterion, nặng negation, sprawl, duplication — **báo cáo, không chặn**.
- **FR-008**: Thao tác trên issue tracker PHẢI đi qua **một file hợp đồng theo repo**; skill KHÔNG được hardcode `gh`/`glab`/`tea` trong thân.
- **FR-009**: Ledger PHẢI mang **5 nhãn** chuẩn, trong đó `ready-for-agent` / `ready-for-human` phân biệt việc giao máy được với việc cần người.
- **FR-010**: Ledger PHẢI mang **cạnh chặn** (`blocked_by`) và **claim**; PHẢI có lệnh tất định in ra **frontier** = open ∧ không-bị-chặn ∧ chưa-claim.
- **FR-011**: Claim PHẢI là thao tác **ghi đầu tiên** của một phiên nhận việc — trước mọi công việc khác.
- **FR-012**: PHẢI có skill `/wayfinder` cho việc quá lớn một phiên: bản đồ quyết định + fog of war + out-of-scope + frontier + luật một-ticket-một-phiên.
- **FR-013**: Mọi luật/nhãn/cột mới PHẢI sống được **không mạng, không tracker remote** (ledger local là nguồn chân lý).
- **FR-014**: Việc bản chất **HITL** PHẢI bị chặn khỏi dispatch (nhãn `ready-for-human`); chỉ việc **AFK** mới được giao agent.
- **FR-015**: Mỗi task PHẢI khai **kiểu việc** (`research`/`prototype`/`grilling`/`build`/`sweep`), và kiểu việc PHẢI quyết định archetype + persona trước khi bảng chi phí chọn CLI.
- **FR-016**: Brief bơm cho agent PHẢI **khai kiểu việc ở dòng đầu** — phiên nhận phải biết nó là phiên kiểu gì.

## Success criteria (SC)
- **SC-001**: Người dùng mở một phiên mới **không tốn ~7.4k token** cho các skill họ chưa bao giờ gọi bằng tay — số đo trước/sau ghi vào wiki, không phải ước lượng.
- **SC-002**: Hai agent chạy song song **không bao giờ ôm cùng một issue** — vì claim là thao tác ghi đầu tiên, và frontier loại issue đã bị claim.
- **SC-003**: Người điều phối nhìn ledger là **biết ngay việc nào giao máy được** mà không phải đọc từng issue.
- **SC-004**: Với một ý tưởng lớn còn mù mờ, người dùng có một **bản đồ đọc được** thay vì một SPEC bịa ra từ phỏng đoán — và mỗi phiên sau đó chỉ cần giải một quyết định.
- **SC-005**: Một người viết skill mới **được chỉ ra chỗ dở của nó bằng máy** (sprawl, negation, thiếu completion criterion) thay vì chờ ai đó đọc và góp ý.
- **SC-006**: Refactor diện rộng **không còn làm CI đỏ hàng loạt** — vì kế hoạch buộc đi đường expand→migrate→contract.
- **SC-007**: Một việc mà **chỉ người mới quyết được** thì **không bao giờ** rơi vào tay một CLI headless để nó đoán thay — cổng HITL chặn từ trước khi dispatch.

## Assumptions
Trường user không nói, model tự điền — mọi dòng là `(default)`, sửa được:
- Nhãn giữ **nguyên tiếng Anh** (`ready-for-agent`…) thay vì Việt hoá `(default)` — chúng là *label string* của tracker, phải khớp GitHub khi mirror.
- Cột mới thêm vào **bảng markdown `ISSUES.md`** hiện có, không đẻ schema JSON mới `(default)` — bảng đang chạy, người đọc được bằng mắt, đúng tinh thần file-first.
- `frontier.py` đặt ở `harness/scripts/` `(default)` — cùng chỗ với các engine tất định khác, travel qua global harness.
- Bản đồ wayfinder là **một issue trong ledger** (nhãn `wayfinder:map`), ticket là issue con `(default)` — tái dùng hạ tầng T6/T7 thay vì đẻ store mới.
- Ngưỡng cảnh báo của skill-health: description > 400 ký tự, SKILL.md > 200 dòng `(default)` — chọn theo phân bố hiện tại, chỉnh được sau khi có số liệu thật.
- `/lint` skill-health **báo cáo, không chặn** `(default)` — đây là chất lượng, không phải an toàn; chặn sẽ làm người ta ghét cổng.

Không mục nào rơi vào nhóm `[CẦN LÀM RÕ]`: thay đổi thuần nội-bộ framework, không chạm xác thực, dữ liệu người dùng, tiền, hay ranh giới tin cậy.

## Risks
- **Tắt model-invocation nhầm một skill đang được skill khác gọi** → đứt chuỗi `orca-workflow → query/propose/plan`. Giảm thiểu: grep mọi lời gọi chéo (`Skill tool → `, `/<tên>`) **trước** khi tắt; T4 liệt kê nhóm (a) trước, tắt nhóm (b) sau; smoke-test một vòng `/orca-workflow` sau khi tắt.
- **Người dùng "mất" skill** vì nó không còn tự nhảy ra. Giảm thiểu: đó chính là **cognitive load** mà lens đã cảnh báo — chữa bằng router (`/find-skills`, `CAPABILITIES.md`), và `description` nhóm (b) vẫn nằm trong `CAPABILITIES.md` để tra.
- **Cột mới làm vỡ `ISSUES.md`** với 12 issue đang mở. Giảm thiểu: cột mới có mặc định (`blocked_by` rỗng, `claim` rỗng, `labels: needs-triage`); parser đọc thiếu cột thì fail-open.
- **Claim là quy ước, không phải khoá.** Hai phiên vẫn có thể ghi đè nhau trong khe hẹp. Giảm thiểu: claim ghi kèm timestamp + tên phiên; ai claim sau thấy claim trước thì nhường. Đây là **trần cố ý** — khoá thật cần một dịch vụ, và ta chọn file-first.
- **`/wayfinder` phình thành một hệ quản lý dự án.** Giảm thiểu: nó **chỉ lập kế hoạch**, không thi hành (luật "plan, don't do" của bản gốc); khi thấy muốn nhảy vào làm, đó là tín hiệu đã tới mép bản đồ và phải bàn giao sang `/propose`.

## Self-review
- **Phủ yêu cầu:** FR-001→T1 · FR-002→T1 · FR-003→T2 · FR-004→T2 · FR-005→T3 · FR-006→T4 · FR-007→T5 · FR-008→T6 · FR-009→T6 · FR-010→T7 · FR-011→T7 · FR-012→T8 · FR-013→T6+T7 · FR-014→T9 · FR-015→T9 · FR-016→T9. T10 là cổng. Không FR nào không có task.
- **Placeholder:** không còn mục nào bỏ trống hay hẹn "sau".
- **Nhất quán tên:** nhãn là `ready-for-agent` / `ready-for-human` (không `agent-ready`); cột ledger là `blocked_by` và `claim`; script là `harness/scripts/frontier.py`; concept là `llmwiki/wiki/concepts/skill-craft.md`; hợp đồng là `llmwiki/wiki/sources/issue-tracker.md`; skill mới là `wayfinder`. Dùng đúng như vậy trong code.

## Notes
- Nguồn ngoài: `scratchpad/mattpocock-skills/` (clone `mattpocock/skills`, 39 skill). Chủ ý thiết kế của họ, ghi trong README: *"Spec-Kit và BMAD cố giúp bằng cách sở hữu quy trình — nhưng làm vậy là lấy mất quyền kiểm soát của bạn"*. Ta đi hướng ngược lại (cưỡng chế tất định), nên chỉ lấy **từ vựng và cơ chế**, không lấy triết lý.
- Xây tiếp trên [[140726-propose-plan-split-superpowers]] và [[140726-spec-kit-traceability]].
- ADR-003 (skill-as-single-source-of-truth) · ADR-005 (logger-and-capabilities-travel-downstream) · ADR-015 (boris-archetypes-into-template)

## Origin
- **Draft:** `wiki/sources/draft/150726-mattpocock-absorb.md`
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
