---
type: draft
title: "Pha 1 — nguyên thuỷ 'biết khi nào agent xong', gốc của 78% task không bao giờ được giao"
status: proposed
tags: [orchestration, orca, herdr, dispatch, feedback-loop, medic, meadows, adapt-hoa-tan]
timestamp: 2026-07-20
task: T-260720-01
---

# 200726-orchestration-loop-closure

**Status:** proposed (bản 2 — viết lại sau khi user phản biện và bằng chứng bác chẩn đoán bản 1)
**Proposed:** 2026-07-20
**Task:** `T-260720-01`
**Sequence diagram:** [200726-orchestration-loop-closure-seq.html](../../../html/200726-orchestration-loop-closure-seq.html)

## Request (một câu)

Dựng orchestrator điều phối các **main agent** (phiên/CLI khác vendor, tách bias ở tầng vật lý) qua Orca; user phản biện rằng thực tế `orca-workflow` **không giao việc** mà toàn tự làm, và yêu cầu **so code Orca với herdr trước khi làm bất cứ gì mang tính thiên kiến**.

## Context

### Bản 1 sai ở đâu — ghi lại để không lặp

Bản 1 của proposal này khẳng định *"orca-workflow đã phủ ~80% yêu cầu"*. **Sai.** Tôi đọc SKILL thấy nó *mô tả* dispatch rồi kết luận nó *đang* dispatch — nhầm **tài liệu** với **hành vi**. User phản biện; đo lại thì user đúng.

| Đo trên 59 task orchestration (runtime Orca, 2026-07-20) | |
|---|---|
| Thực sự có bản ghi dispatch | **13 (22%)** |
| **Chưa bao giờ dispatch** (`dispatch: null`) | **46 (78%)** |
| `completed` mà chưa từng dispatch | **31** |
| 14 task `ready`+`blocked` treo | **100% chưa từng dispatch** |

`orca orchestration` đang được dùng như **sổ ghi việc**, không phải cơ chế giao việc.

### Nhưng nguyên nhân KHÔNG phải "Orca không dispatch được"

Thử thật, dispatch cho **opencode** (deepseek-v4-flash-free) qua `orca terminal create --command`:

```
> build · deepseek-v4-flash-free
4
```

**Giao việc cho vendor khác chạy tốt.** Cái hỏng nằm ở chỗ khác — cùng lượt đó:

```
orca terminal wait --for tui-idle --timeout-ms 90000  →  ok:false, code:"timeout"
orca terminal read                                    →  status: "running"
```

Việc xong trong vài giây, shell đã về prompt, mà `wait` **timeout sau 90 giây**, còn `status` vẫn `running` — vì thứ đang chạy là **shell**, không phải agent.

**Chuỗi nhân quả (có bằng chứng từng mắt xích):** dispatch được → **nhưng không biết lúc nào xong** → giám sát một dispatch thành cực hình → coordinator bỏ cuộc, làm inline → **78% task không bao giờ được giao** → 17 task mồ côi.

⇒ Chẩn đoán bản 1 (*"vòng không đóng"*) là **nông**. Vòng không đóng vì nó **chưa bao giờ được bắt đầu**, và nó không được bắt đầu vì **không quan sát được lúc kết thúc**.

### So Orca ↔ herdr (đã clone và đọc code, không đoán)

`herdr` — `github.com/ogulcancelik/herdr`, Rust, ~233k LOC, **AGPL-3.0**, "agent multiplexer sống trong terminal".

| | Orca | herdr |
|---|---|---|
| Cô lập vật lý | **worktree (git-level)** — mạnh hơn | pane/process; worktree tuỳ chọn |
| Biết pane chạy agent nào | ✗ không có trường `agent` | ✓ `agent` |
| Biết agent đang làm gì | ✗ chỉ `lastOutputAt` + `tui-idle` (đã timeout ở test) | ✓ `agent_status`: working·blocked·**done** |
| "kết quả đã xem chưa" | ✗ | ✓ phân biệt `idle` vs `done` |
| Task DAG · deps · decision gate | **✓ mạnh** | ✗ (chỉ `wait`) |
| Đóng vòng dựa vào | worker **tự nguyện** gửi `worker_done` | **quan sát** từ pane, worker khỏi hợp tác |
| Ràng buộc chạy | cần app + runtime | 1 binary, ssh/detach |

Kiểm công bằng cho Orca: đã soi cả `terminal list` (12 trường: handle · ptyId · worktreeId · branch · title · connected · `lastOutputAt` · preview…) và `worktree ps` (`workspaceStatus` mức workspace) — **không nơi nào có `agent_status`**.

**Hai thứ bổ sung nhau, không thay thế nhau.** Orca mạnh ở *sở hữu & kế hoạch*; herdr mạnh ở đúng nguyên thuỷ ta thiếu: *quan sát trạng thái agent mà không cần agent hợp tác*.

### Mode adapt đã chốt: HÒA TAN

User chốt **HÒA TAN** (lấy ý tưởng), không **KÉO NGOÀI** (cài herdr làm hạ tầng): lấy insight "quan sát thay vì tin worker tự khai" nhưng cài bằng đồ Orca sẵn có. Tránh thêm 233k LOC hạ tầng và ràng buộc AGPL-3.0 nếu sau này phát hành. Xem [[adapt-modes]].

**Đã có, KHÔNG dẫm (pre-flight #3):** `skills/orca-workflow` (propose→gate→dispatch, cổng HITL/AFK, watchdog) · `skills/orca-dispatch-reference` (SoT syntax) · `harness/scripts/dispatch-verify.py` (đóng vòng *proposal ↔ đĩa* — vòng KHÁC) · `harness/council.personas.yaml` (6 archetype) · ADR-015-boris-archetypes-into-template · ADR-003-skill-as-single-source-of-truth · ADR-004-framework-dev-context-opt-in (all 3 ở `fdk/wiki/sources/adr/`).

## Global constraints

- **Hook fail-open; CLI/CI thì lỗi bất ngờ phải nổi (exit ≠ 0)** — docstring `wiki-sync.py`.
- **Mọi file wiki phải có `## Origin`**; chỉ nằm trong `concepts/ entities/ sources/ draft/ architecture/ tours/` (R5); **luôn cập nhật `index.md` + append `log.md`**.
- **R3 index-sync khớp ĐĨA** — thừa hay thiếu dòng index đều đỏ.
- **Skill canonical `skills/` ↔ mirror `llmwiki/skills/` byte-identical**, qua `sync-skills`; `medic` gác parity.
- **Commit CẤM mọi AI-attribution** — R15, ADR-016-no-ai-attribution-in-commits (`fdk/wiki/sources/adr/ADR-016-no-ai-attribution-in-commits.md`).
- **`medic --ci` xanh trước push**; trước push chạy trọn step `repo health` của `.github/workflows/harness.yml` tại local (L2 ≠ L4).
- **`orca orchestration` là RPC tới runtime đang chạy** — runtime tắt là trạng thái BÌNH THƯỜNG, không phải lỗi.
- **herdr là AGPL-3.0** — không sao chép code herdr vào repo này; chỉ lấy ý tưởng (HÒA TAN).
- **Beneficiary (ADR-004):** phiên `/fdk`, được đánh giá chính framework; SC vẫn nói bằng thứ người dùng nhận được.

## Non-goals

- **KHÔNG cài herdr làm hạ tầng** trong pha này (mode đã chốt là HÒA TAN).
- **KHÔNG chép code herdr** — AGPL-3.0.
- **KHÔNG dựng orchestrator tự chủ** — Pha 2, chỉ mở khi Pha 1 xanh.
- **KHÔNG viết lại `orca-workflow`** — chỉ thêm nguyên thuỷ còn thiếu và sửa chỗ nó bảo dùng `terminal wait --for tui-idle`.
- **KHÔNG tự động đóng/xoá task** — tool chỉ báo cáo; đóng là hành động có chủ ý.
- **KHÔNG đụng `dispatch-verify.py`** — vòng khác, đang chạy tốt.

## Approaches

### A — Sentinel trong lệnh dispatch, poll `terminal read` ✅ CHỌN

Dispatch bọc lệnh thành `<cmd>; echo __ORCA_DONE__<id>:$?`, rồi poll `orca terminal read` tìm sentinel để biết **xong thật** + lấy exit code.

- Ưu: chạy với **mọi vendor CLI** (claude · opencode · agy · copilot) vì không cần CLI đó biết gì về Orca; dùng nguyên thuỷ Orca đã có; ~30 dòng; lấy được cả exit code nên phân biệt xong-đúng với xong-lỗi.
- Nhược: sentinel nằm trong output nên về lý thuyết có thể trùng chuỗi — xử bằng id ngẫu-nhiên-theo-task; và nó đo *lệnh kết thúc*, không đo *agent nghĩ xong* (với agent chạy một-phát `run` thì hai thứ trùng nhau).

### B — KÉO NGOÀI: cài herdr, dùng `agent_status` gốc

- Ưu: primitive xịn nhất, phân biệt cả `blocked` lẫn `done`-chưa-xem.
- Nhược: thêm hạ tầng 233k LOC; phải test lồng Orca↔herdr (chưa ai làm); **AGPL-3.0**; và nó giải bài toán lớn hơn bài ta đang có. **Loại ở pha này** — user đã chốt HÒA TAN.

### C — Sửa `tui-idle` của Orca

- Ưu: sửa đúng gốc thượng nguồn.
- Nhược: Orca là app đóng, không sửa được từ đây. **Loại.**

**Chốt A** vì nó là bậc thang rẻ nhất còn đứng vững: lấy đúng *insight* của herdr (quan sát, đừng tin lời tự khai) mà không nuốt cả *hạ tầng* của herdr.

## Requirements (FR)

- **FR-001**: Hệ thống PHẢI xác định được một lệnh dispatch đã kết thúc hay chưa, **không phụ thuộc agent được giao có hợp tác báo cáo hay không**.
- **FR-002**: Việc phát hiện kết thúc PHẢI phân biệt được **xong-thành-công** và **xong-lỗi** (exit code).
- **FR-003**: Cơ chế PHẢI chạy với ít nhất hai vendor CLI khác nhau, chứng minh bằng lượt chạy thật.
- **FR-004**: Hệ thống PHẢI liệt kê được task chưa kết thúc kèm tuổi và phân loại, trong đó **chưa-từng-dispatch là một nhóm riêng** (hiện chiếm 78%).
- **FR-005**: Đối soát PHẢI tất định, **0 token**, và coi "runtime Orca không chạy" là bình thường (không làm đỏ cổng).
- **FR-006**: Tool PHẢI KHÔNG tự đóng/xoá/đổi trạng thái bất kỳ task nào — chỉ báo cáo.
- **FR-007**: 17 task đang treo PHẢI được triage xong, mỗi task có kết luận kèm lý do truy được.

## Plan

- [ ] **T1 — `orca-dispatch.py`: nguyên thuỷ "xong thật".** Bọc lệnh bằng sentinel `__ORCA_DONE__<id>:$?`, tạo terminal qua `orca terminal create --command`, poll `orca terminal read` cho tới khi thấy sentinel hoặc hết hạn. Trả `{done, exit_code, output, waited_ms}`. `--self-test` tất định trên fixture (không cần runtime). Fail-open khi thiếu `orca`. *(FR-001, FR-002, FR-005)*
- [ ] **T2 — Chứng end-to-end trên 2 vendor.** Dùng T1 dispatch một việc nhỏ cho **opencode** và **agy**, ghi bằng chứng (exit code + thời gian chờ thật) vào `harness/metrics/dispatch-proof.json`. Đây là thứ bác bỏ hoặc xác nhận "Orca không giao việc được". *(FR-003)*
- [ ] **T3 — `orca-reconcile.py` + probe `medic`.** Liệt kê task chưa kết thúc theo tuổi, nhóm chính là **chưa-từng-dispatch** (đọc `dispatch-show`), rồi cắm probe thứ 15 vào `medic` ở mức **warn**; runtime tắt → **skip**. Chỉ báo cáo. *(FR-004, FR-005, FR-006)*
- [ ] **T4 — Triage 17 task treo.** Mỗi task: đóng / mở lại / xoá kèm lý do, ghi bản đối soát vào wiki draft; task thiếu bối cảnh thì **giữ**, không xoá. *(FR-007)*

## Success criteria (SC)

- **SC-001**: Người điều phối **giao được việc cho CLI khác rồi biết chắc lúc nó xong**, thay vì ngồi đoán hoặc bỏ cuộc làm tay. *(Bằng chứng: `dispatch-proof.json` có 2 vendor, exit code đúng, thời gian chờ khớp thực tế.)*
- **SC-002**: Việc giao cho agent **không còn im lặng thất bại** — xong-lỗi phân biệt được với xong-đúng. *(Bằng chứng: một lượt dispatch lệnh sai trả `exit_code ≠ 0`.)*
- **SC-003**: Người điều phối **biết ngay mình đang nợ bao nhiêu việc chưa giao**, thay vì phát hiện sau hai tháng. *(Bằng chứng: `medic` in số task treo + nhóm chưa-từng-dispatch.)*
- **SC-004**: Cổng sức khoẻ **không đỏ chỉ vì người dùng không mở Orca**. *(Bằng chứng: tắt runtime → probe skip, `medic --ci` xanh.)*
- **SC-005**: **Không việc đang chạy nào bị tool đóng nhầm** — tool không có quyền đổi state. *(Bằng chứng: grep mã nguồn không có `task-update`/`reset`.)*
- **SC-006**: Sau T4, **số task mồ côi về 0**, mỗi task đóng đều truy được lý do. *(Bằng chứng: bản đối soát + `task-list` chạy lại.)*

## Assumptions

- Sentinel dạng `__ORCA_DONE__<id>:$?` với `<id>` sinh theo task `(default)` — id riêng mỗi lượt để output của chính agent không vô tình trùng.
- Poll `terminal read` mỗi **2 giây** `(default)` — đủ nhanh để không trễ cảm nhận, đủ thưa để không quấy runtime.
- Ngưỡng "treo" mặc định **7 ngày** `(default)`; task `blocked` tính là chưa kết thúc `(default)`.
- Probe medic mức **warn** chứ không **fail** `(default)` — nợ điều phối không phải hỏng hệ; đỏ vì nợ sẽ bị học cách phớt lờ (bài học "cảnh báo bị nhờn", T-260719-02).
- Với agent chạy chế độ một-phát (`opencode run`, `agy -p`), "lệnh kết thúc" trùng với "agent xong" `(default, find-out-later)` — agent chạy chế độ TUI tương tác thì KHÔNG trùng; nếu sau này cần supervise agent TUI thì phải quay lại cân nhắc phương án B.
- 17 task treo phần lớn là rác lịch sử của thí nghiệm cũ `(default)` — T4 xác nhận hoặc bác.

Không mục nào rơi vào nhóm bắt buộc `[CẦN LÀM RÕ]`: pha này không chạm auth, dữ liệu người dùng, tiền, pháp lý, hay ranh giới tin cậy.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 — `orca-dispatch.py` sentinel | CLAUDE | Nguyên thuỷ lõi; fail-open và bóc exit code phải đúng ở mọi nhánh | pending |
| T2 — chứng end-to-end 2 vendor | CLAUDE | Phải phán bằng chứng thật/giả, và chính nó là bài bác claim của tôi | pending |
| T3 — reconcile + probe medic | OPENCODE big-pickle | Cơ khí: đọc JSON, phân nhóm, thêm probe theo khuôn 14 probe đã có | pending |
| T4 — triage 17 task | CLAUDE | Mỗi task đòi đọc bối cảnh rồi mới quyết — đúng định nghĩa HITL, không giao headless được | pending |

## Render brief

**T1** — Bên: coordinator · `orca-dispatch.py` · `orca terminal create` · agent vendor khác · `orca terminal read`. Bước: (1 legacy) `terminal create --command` đã chạy được agent vendor khác; (2 block) `terminal wait --for tui-idle` TIMEOUT 90s dù việc xong vài giây, `status` vẫn `running` vì đó là shell; (3 add) bọc lệnh: `<cmd>; echo __ORCA_DONE__<id>:$?`; (4 add) poll `terminal read` mỗi 2s tìm sentinel; (5 add) thấy sentinel → trả `{done, exit_code, waited_ms}`; (6 add) không cần agent hợp tác — chạy với mọi vendor; (7 block) thiếu `orca` → fail-open, không gãy phiên. *Prose:* insight của herdr (quan sát thay vì tin tự khai) cài bằng đồ Orca; vì sao không nuốt 233k LOC AGPL.

**T2** — Bên: T1 · opencode · agy · `dispatch-proof.json`. Bước: (1 add) dispatch việc nhỏ cho opencode, ghi exit code + waited_ms thật; (2 add) lặp với agy — vendor thứ hai; (3 add) một lượt cố tình lệnh sai để chứng minh exit code ≠ 0 bắt được; (4 add) ghi bằng chứng ra metrics; (5 block) vendor nào không cài → ghi "skipped, chưa cài", KHÔNG bịa kết quả. *Prose:* đây là bài bác chính claim sai của bản 1; chuẩn bằng chứng phải là lượt chạy thật, không phải mô tả tài liệu.

**T3** — Bên: `medic --ci` · probe `orchestration` · `orca-reconcile.py` · `task-list`/`dispatch-show`. Bước: (1 legacy) medic đã chạy 14 probe, đã thành thói quen trước commit; (2 add) reconcile đọc `task-list` + `dispatch-show` từng task; (3 add) phân nhóm — **chưa-từng-dispatch** (78%) tách riêng khỏi dispatch-rồi-treo; (4 add) probe thứ 15 báo WARN kèm số + tuổi lớn nhất; (5 add) runtime tắt → SKIP, medic vẫn xanh; (6 block) KHÔNG mức fail, KHÔNG quyền đổi state. *Prose:* vì sao nhóm "chưa từng dispatch" mới là nhóm đáng báo; vì sao warn chứ không fail.

**T4** — Bên: người điều phối · reconcile · 17 task · `dispatch-show` · bản đối soát. Bước: (1 add) chạy reconcile lấy 17 task; (2 add) đọc spec + dispatch-show từng cái; (3 add) quyết đóng/mở lại/xoá kèm lý do; (4 add) ghi bản đối soát vào wiki; (5 add) `task-list` chạy lại — mồ côi về 0; (6 block) thiếu bối cảnh → GIỮ, ghi "giữ, thiếu bối cảnh", không xoá thứ mình không hiểu. *Prose:* chứng minh vòng ĐÓNG ĐƯỢC chứ không chỉ ĐO ĐƯỢC; điều kiện mở Pha 2.

## Self-review

**1. Phủ yêu cầu.** Yêu cầu lần này có 3 phần: (a) *phản biện "orca-workflow toàn tự làm"* — phủ ở `## Context`, đo được 78% chưa từng dispatch, xác nhận user đúng và ghi rõ bản 1 sai ở đâu; (b) *so code Orca với herdr trước khi làm gì thiên kiến* — phủ bằng bảng so sau khi clone và đọc `SKILL.md`/`README.md` của herdr, cộng kiểm công bằng cho Orca (soi `terminal list` + `worktree ps` để không kết luận vội là Orca thiếu); (c) *rồi mới quyết* — mode HÒA TAN do user chốt, ghi ở `## Context` và là lý do loại phương án B. Mỗi phần về đúng một chỗ.

**2. Quét placeholder.** Rà toàn văn theo danh sách cấm R7-g: không còn chỗ bỏ ngỏ bằng từ hoãn-binh, không lời hứa xử-lý-chung-chung, không task nào mô tả bằng cách trỏ sang task khác. Một chỗ chưa chốt khai tường minh bằng `(default, find-out-later)` — giả định "lệnh kết thúc = agent xong" chỉ đúng với chế độ một-phát.

**3. Nhất quán tên-kiểu.** Rà tên lặp: `orca-dispatch.py` (T1) và `orca-reconcile.py` (T3) là **hai file khác nhau**, không lẫn; sentinel viết thống nhất `__ORCA_DONE__<id>:$?`; nhóm gọi thống nhất là **chưa-từng-dispatch** (không lẫn "never-dispatched" trong văn tiếng Việt); ngưỡng **7 ngày** và mức **warn** thống nhất giữa Plan và Assumptions; **HÒA TAN** viết hoa nhất quán theo [[adapt-modes]].

**Một chỉnh sửa tại chỗ trong self-review:** bản nháp lần này ban đầu gộp T1 và T2 làm một task. Đã tách, vì T2 là **bằng chứng bác claim sai của chính tôi** — gộp nó vào task xây dựng sẽ khiến nó dễ bị coi là thủ tục và bỏ qua, đúng cái đã xảy ra ở bản 1.

## Origin
- **Draft:** `wiki/sources/draft/200726-orchestration-loop-closure.md` (bản 2 — thay thế bản 1 cùng tên)
- **Source:** phiên `/fdk` 2026-07-20; user phản biện "orca-workflow toàn tự làm" + cung cấp `github.com/ogulcancelik/herdr`. Bằng chứng: đo 59 task orchestration (78% chưa dispatch), dispatch thật opencode thành công nhưng `terminal wait --for tui-idle` timeout 90s, clone + đọc herdr `SKILL.md`/`README.md`
- **Problem-tree:** `p-36` (vòng không đóng — chẩn đoán đã được thay bằng gốc sâu hơn), `p-37`, `p-38`
- **Task:** `T-260720-01`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
