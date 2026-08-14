---
type: draft
title: "Migration: code là source of truth — 3 lớp artifact, quan hệ suy ra được, merge = regen"
status: proposed
tags: [architecture, source-of-truth, derived, merge, ledger, migration]
timestamp: 2026-07-21
task: T-260721-02
---

# Migration: code là source of truth — 3 lớp artifact + merge protocol regen

**Status:** proposed

Yêu cầu gốc, một câu: chuyển framework sang kiến trúc mà source code là nguồn sự thật duy nhất, mọi quan hệ đều suy ra được và máy kiểm được, để khi merge hai nhánh thì có căn cứ so sánh A-B tự động thay vì tự tay hoà giải văn bản.

**Sequence diagram:** [210726-code-as-truth-migration-seq.html](../../../html/210726-code-as-truth-migration-seq.html)

## Context

Đề xuất này không du nhập một kiến trúc lạ — nó **hoàn tất một chuyển động đã đi được nửa đường** trong chính repo này, và wiki đã ghi đủ bằng chứng cho cả hai vế.

Vế bệnh: bài viết nguồn (goonnguyen.substack — Revenue-Driven Development; phần áp dụng được là chẩn đoán SDD) mô tả một dự án chết vì 135 file plan cộng hơn 40 ADR mâu thuẫn, khiến LLM grep trúng spec chết và tin nó — "distractor interference". Bệnh đó đã xảy ra **đo được** ở đây: node `p-41` trong cây vấn đề ghi lại việc agent đọc `harness/travel-policy.yaml` ba lần trong một phiên và cả ba lần coi nó là sự thật, trong khi installer mới là hành vi; `p-10` ghi 15 draft tồn chưa ai chưng lọc; `p-42` ghi CAPABILITIES.md là bản kiểm kê sinh từ `os.listdir` (bài toán TỒN TẠI) chứ không phải bản đồ sinh từ quan hệ; và 7/83 skill rơi khỏi mind map tự sinh vì `LOOP_GROUPS` trong `fdk/tools/build-overstack-docs.py` là một dict viết tay đã lệch khỏi taxonomy mà `llmwiki/CLAUDE.md` tự khai ("wiki-loop" — code không biết loop này tồn tại).

Vế nền đã có: commit `bc39047` chuyển `touches` từ khai tay trong frontmatter (đóng băng ở 21 cạnh suốt 18 ngày) sang tự suy từ path trong nội dung — ra 283 cạnh; commit `713775b` chuyển `log.md` sang render bằng code từ `events.jsonl`; bước 0 phiên 2026-07-20 hạ `travel-policy.yaml` từ vai "sự thật" xuống vai "mô tả" — hành vi nằm trong `STRIP_TIER3` của installer, còn `harness/validators/travel_policy_sync.py` gác hai chiều cho văn bản khớp code; khuôn `--check` drift đã chạy thật ở `build-capabilities.py --check` và cổng docs của medic. `ADR-003` (skill-as-single-source-of-truth) đã chốt đúng nguyên tắc này cho riêng tầng skill. [[graph-model]] chốt kiến trúc đồ thị quan hệ; [[adapt-modes]] và [[skill-craft]] là hai concept sẽ đứng ở lớp AUTHORED vì chúng chứa phán đoán người, không suy được từ code.

Điểm nghẽn cần cổng duyệt: `travel-policy.yaml` Tầng 2 hiện khai nguyên văn *"llmwiki/wiki/** — tri thức (nguồn chân lý)"* — mâu thuẫn trực diện với đích đến. Lời giải của đề xuất: wiki **giữ WHY** (ADR, origin, feedback, bài học — thứ code không chứa được), **mất quyền giữ WHAT/quan-hệ** (mọi inventory, map, index, danh sách phải sinh từ code). Một điều phải nói rõ vì trung thực: luận điểm merge A-B là của user, **không có trong bài viết nguồn** — và nó là phần mạnh nhất của cả ý tưởng, vì nó biến "code là sự thật" từ khẩu hiệu thành một cơ chế kiểm được tại đúng chỗ đau nhất (merge nhiều phiên song song — memory `framework-multi-session-dev` đã ghi nhận drift kiểu này là thường trực).

## Global constraints

Chép nguyên văn từ nguồn có thẩm quyền, áp cho mọi task bên dưới.

- `llmwiki/CLAUDE.md`, 5-Why: "**Tìm HỘI TỤ trước khi sửa.** Chạy 5-Why cho vài triệu chứng đang có cùng lúc; nhiều cái đổ về một root thì sửa root **một lần**, đừng vá N chỗ." — năm triệu chứng (p-41, p-10, p-42, LOOP_GROUPS lệch, merge conflict file sinh) đổ về một root: sự thật bị CẤT vào văn bản thay vì SUY từ code.
- `llmwiki/CLAUDE.md`, cái thang: "**Hiểu bài trước, leo thang sau.**… bậc rẻ nhất là xoá." — migration này chủ yếu là XOÁ quyền-làm-sự-thật của văn bản, không phải xây tầng mới.
- `ADR-003` (skill-as-single-source-of-truth): một skill chỉ có một bản canonical, mirror sinh ra bằng code (`sync-skills.py`) — đề xuất này nhân nguyên tắc đó ra toàn bộ artifact.
- `ADR-004`: thứ auto-fire mọi phiên chỉ phục vụ dự án hiện tại; mọi cơ chế mới trong đề xuất này đều chạy ở gate/generator, không thêm hook auto-bơm.
- Fail-open tuyệt đối ở tầng hook; fail-CLOSED ở tầng gate commit/CI (khuôn đã có: R7, medic --ci).
- Luật prose (CLAUDE.md 2026-06-27): tài liệu người đọc viết văn xuôi đầy đủ — lớp AUTHORED không được caveman-hoá.
- Repo cấm AI-attribution trong commit (R15).

## Non-goals

- **Không xoá wiki.** Wiki là nơi duy nhất giữ WHY — quyết định, nguồn gốc, bài học, feedback. Bài viết nguồn giữ ~5 file vì tác giả không có validator; ta có 14 validator + medic nên giữ được nhiều file authored hơn mà không mục.
- **Không adopt phần "revenue"** của bài viết — framework không có tín hiệu doanh thu; analog đã có là telemetry `skill-usage.py`.
- **Không rewrite engine nào** (build-wiki-graph, mem-rank, code-graph…) — chỉ đổi *nguồn* chúng đọc và *vai trò* output của chúng.
- **Không đổi cấu trúc thư mục wiki** (concepts/entities/sources/draft) — R5 giữ nguyên.
- **Không gitignore các HTML sinh mà downstream-contract đòi tồn tại** (`overstack.html` nằm trong `must_exist` của fresh-install-smoke) — xem Approaches B vì sao bác.
- **Không làm trong đợt này:** incremental cho build-wiki-graph (p-45 đã vá bằng debounce, thuật toán để riêng), và mọi việc thuộc draft `210726-codegraph-external-pull` (đang chờ duyệt riêng).

## Approaches

**Phương án A — 3 lớp artifact + derived-vẫn-commit + merge-bằng-regen (chọn).** Mọi artifact được khai vào đúng một trong ba lớp: **AUTHORED** (người viết, giữ WHY — ADR, concept, origin, feedback, SKILL.md); **DERIVED** (code sinh từ zero được — mọi map/index/inventory/HTML/log-block; vẫn commit để người xem mở trực tiếp và downstream-contract không gãy, nhưng mỗi cái bắt buộc có generator + `--check` exit 2 khi drift); **STATE** (máy-local, gitignore — metrics, cache, debounce). Merge protocol: file DERIVED không bao giờ hoà giải tay — lấy phía nào cũng được, regen từ code đã merge, chạy validator suite; diff của derived trước/sau regen chính là bản so sánh A-B ngữ nghĩa. Ưu: khớp mọi tiền lệ đang chạy (`--check`, travel_policy_sync, sync-skills), không phá hợp đồng downstream, chi phí chủ yếu là *phân loại + bịt chỗ thiếu check* chứ không xây mới. Nhược: derived commit vào git vẫn tạo noise diff — chấp nhận, vì gate bảo đảm noise đó luôn tái tạo được.

**Phương án B — gitignore toàn bộ DERIVED.** Sạch nhất về lý thuyết (git chỉ còn code + WHY), merge không bao giờ đụng file sinh. Bác vì ba lẽ: `overstack.html`/`wiki-graph.html` là thứ user mở xem hằng ngày qua `file://` — bắt chạy generator trước khi xem là hạ usability (kim chỉ nam UX: usage > performance); fresh-install-smoke khai `must_exist: llmwiki/html/overstack.html` ở downstream — gitignore là gãy hợp đồng nghiệm thu; và lịch sử render cũng là dữ liệu (đối chiếu "trang này từng nói gì").

**Phương án C — giữ nguyên, thêm kỷ luật viết tài liệu.** Chi phí bằng không. Bác: đây là bậc thấp nhất thang Meadows ("dặn agent nhớ"), và đã chứng minh không giữ được — `touches` khai tay đóng băng 18 ngày ngay cả khi có quy ước rõ ràng; `p-41` xảy ra với chính agent đã đọc quy ước.

## Requirements (FR)

**FR-001**: Hệ thống PHẢI có một sổ phân lớp artifact duy nhất (artifact-ledger) khai mọi đường dẫn tracked vào đúng một lớp AUTHORED / DERIVED / STATE, và một validator gác hai điều: file tracked mới phải thuộc một lớp, và file DERIVED phải trỏ được tới generator của nó.

**FR-002**: Mọi artifact lớp DERIVED PHẢI regen được từ zero bằng một lệnh, và PHẢI có chế độ `--check` exit 2 khi bản trên đĩa lệch bản sinh lại; các `--check` này PHẢI được medic gọi (khuôn cổng docs hiện có).

**FR-003**: Quan hệ giữa các thực thể (skill↔loop, trang↔code, trang↔trang, tool↔tool) CHỈ được suy từ nguồn — path trong nội dung, wikilink trong văn bản, import/call trong code, frontmatter tại chính thực thể — KHÔNG được khai thành danh sách quan hệ ở file thứ ba. `fdk/tools/wiki-relations.py` (dập quan hệ vào frontmatter) PHẢI bị khai tử theo đúng kế hoạch bàn giao 2026-07-20 bước 4.

**FR-004**: `LOOP_GROUPS` PHẢI chuyển từ dict viết tay trong `build-overstack-docs.py` sang suy từ frontmatter của từng `SKILL.md` (một trường `loop:` + `group:` tại nguồn); taxonomy "wiki-loop" mà `llmwiki/CLAUDE.md` khai PHẢI trở thành giá trị hợp lệ của trường đó, để tài liệu và code đọc cùng một nguồn và 7 skill hiện lọt lưới có chỗ đứng.

**FR-005**: `CAPABILITIES.md` PHẢI sinh từ đồ thị quan hệ thay vì `os.listdir`, theo đúng ba tính chất bắt buộc đã ghi trong bàn giao: suy ra đừng cất · khai cả cái CHẾT (0 node/0 caller) · khai cả cái KHÔNG travel; quan hệ `supersedes` là phán đoán người thì ở lại lớp AUTHORED.

**FR-006**: PHẢI có merge protocol thành văn + một script kiểm được: khi merge, file DERIVED lấy phía nào cũng được, sau merge chạy regen toàn bộ + validator suite; script PHẢI xuất bản diff derived trước/sau làm bản so sánh A-B. Protocol PHẢI được thử trên một merge thật giữa hai nhánh có thay đổi song song trước khi tuyên bố xong.

**FR-007**: `/lint` PHẢI báo draft ở `sources/draft/` quá hạn tuổi (mặc định 14 ngày) chưa promote/archive — trả nợ `p-10`; báo cáo, không chặn.

**FR-008**: Dòng khai Tầng 2 trong `travel-policy.yaml` PHẢI đổi từ "tri thức (nguồn chân lý)" thành khai đúng vai mới: wiki là nguồn chân lý **của WHY**; WHAT/quan-hệ do code sinh. Một câu, nhưng là câu định vị cả kiến trúc — đổi kèm chú thích trỏ về SPEC này.

## Success criteria (SC)

**SC-001**: Người merge hai nhánh có thay đổi song song không phải tự tay hoà giải bất kỳ file sinh nào — toàn bộ conflict còn lại nằm ở code và văn bản WHY. Bằng chứng: một merge thật theo FR-006 hoàn tất mà không có thao tác sửa tay trong file DERIVED.

**SC-002**: Bất kỳ ai (người hoặc agent) hỏi "file X là sự thật hay mô tả, ai sinh ra nó?" đều trả lời được bằng một lệnh tra sổ — không còn ca "đọc ba lần tin nhầm ba lần" như p-41. Bằng chứng: tra ledger ra lớp + generator cho 100% file tracked.

**SC-003**: Thêm một skill mới chỉ phải viết đúng MỘT file (`skills/<tên>/SKILL.md`) — mirror, mind map, CAPABILITIES, search index tự cập nhật qua generator. Baseline hôm nay: ≥4 chỗ phải sửa tay (mirror cp, LOOP_GROUPS, đăng ký bảng CLAUDE.md, capabilities), và đã đo được hậu quả là 7 skill lọt lưới.

**SC-004**: Người đọc wiki phân biệt được ngay WHY với WHAT: mọi trang inventory/map hiển thị rõ "sinh bởi <generator>, đừng sửa tay"; số văn bản "mô tả trùng vai hành vi" kiểu travel-policy-cũ về 0.

**SC-005**: Số draft tồn quá hạn giảm từ 15 hiện tại về ≤3 trong vòng bốn tuần sau khi FR-007 chạy, và không tích tụ trở lại (đo bằng chính báo cáo /lint qua các tuần).

## Plan

- [ ] **T1 — Artifact-ledger + validator phân lớp.** Thiết kế sổ (một file YAML/JSON tại `harness/`), phân loại toàn bộ file tracked hiện có, viết validator gác file mới + DERIVED-phải-có-generator. Verify: validator chạy trên repo hiện tại ra 0 file không lớp; cố tình thêm 1 file lạ → exit 2.
- [ ] **T2 — Bịt lỗ `--check`.** Rà mọi DERIVED trong ledger, cái nào thiếu `--check` thì thêm theo khuôn `build-capabilities.py --check`; nối tất cả vào medic. Verify: medic --ci đếm đủ số check mới; sửa tay 1 file derived → medic đỏ.
- [ ] **T3 — LOOP_GROUPS → frontmatter.** Điền `loop:`/`group:` vào 83 SKILL.md (giá trị lấy từ dict hiện có + xếp 7 skill lọt lưới, trong đó 5 skill nhận `loop: wiki-loop`); sửa `build-overstack-docs.py` đọc frontmatter, xoá dict; sync-skills lo mirror. Verify: mind map render đủ 83/83, cảnh báo "chưa phân nhóm" biến mất, diff taxonomy trước/sau = 0 cho 76 skill cũ.
- [ ] **T4 — CAPABILITIES sinh từ graph (trả p-42).** Sửa `build-capabilities.py` đọc từ wiki-graph/code-graph: thêm cột quan-hệ (cái gì gọi cái gì, cái gì travel, cái gì chết). Verify: ba tính chất bắt buộc hiện diện trong output; mục "dead" bắt được ít nhất các ca đã biết (graph.db gốc repo, wiki-graph-static.html — nếu còn).
- [ ] **T5 — Merge protocol + script + thử thật.** Viết `harness/scripts/merge-regen.sh` (checkout union → regen ledger-DERIVED → validator suite → xuất diff A-B); tài liệu hoá trong CONTRIBUTING; chạy thử trên hai nhánh thật có sửa song song. Verify: merge thử hoàn tất không sửa tay file DERIVED nào; diff A-B đọc được.
- [ ] **T6 — Draft-age vào /lint (trả p-10).** Thêm phép đếm tuổi draft vào lint, ngưỡng 14 ngày, báo không chặn. Verify: chạy lint hôm nay phải bêu đúng các draft từ 02/07.
- [ ] **T7 — Đổi vai wiki trong travel-policy + CLAUDE.md.** Sửa dòng Tầng 2 theo FR-008; cập nhật đoạn taxonomy trong `llmwiki/CLAUDE.md` trỏ về frontmatter làm nguồn. Verify: `travel_policy_sync.py` vẫn xanh; grep "nguồn chân lý" chỉ còn ở ngữ cảnh WHY.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| T1 | Claude | Thiết kế phân loại là quyết định kiến trúc — xếp nhầm lớp một file là sai dây chuyền mọi gate sau nó | pending |
| T2 | OpenCode (rẻ) | Chép khuôn `--check` đã có, medic tự bắt nếu chép sai — lưới an toàn tất định đỡ sẵn | pending |
| T3 | OpenCode (rẻ) phần điền 83 frontmatter (bảng giá trị cho sẵn từ dict cũ) · Claude phần sửa generator | Điền frontmatter là cơ học có bảng tra; sửa generator dùng chung cần đọc hiểu luồng render | pending |
| T4 | Claude | Trả p-42 đúng cảnh báo bàn giao: "bản đồ tự tin và sai còn tệ hơn không có bản đồ" — cần phán đoán quan hệ nào kiểm được | pending |
| T5 | Claude | Merge protocol là điểm ăn tiền của cả SPEC, sai thì mất niềm tin vào toàn bộ kiến trúc | pending |
| T6 | OpenCode (rẻ) | Đếm mtime + ngưỡng, lint đã có khung báo cáo | pending |
| T7 | Claude | Một câu nhưng định vị kiến trúc; kèm nghĩa vụ giữ travel_policy_sync xanh | pending |

## Assumptions

- Ngưỡng tuổi draft 14 ngày — **(default)**: đủ dài cho một draft đang chờ duyệt thật, đủ ngắn để không thành bãi 135-plans; chỉnh bằng config lint nếu nhịp làm việc khác.
- DERIVED vẫn commit vào git (không gitignore) — **(default)**, lý do đầy đủ ở Approaches A/B; nếu về sau noise diff thành vấn đề thật thì mở lại bằng số đo, không mở lại bằng cảm giác.
- Trường frontmatter đặt tên `loop:` và `group:` — **(default)**: khớp từ vựng LOOP_GROUPS hiện có để migration là phép chép, không phải phép dịch.
- Migration chạy TUẦN TỰ T1→T2→(T3,T4,T6 song song)→T5→T7 — **(default)**: ledger phải có trước thì check mới biết gác cái gì; merge protocol thử sau khi các generator đã đọc nguồn mới; T7 chốt hạ cuối cùng khi mọi thứ đã đúng vai.
- Không cần cổng CẦN-LÀM-RÕ nào: đề xuất không chạm auth/tiền/dữ-liệu-người-dùng/ranh-giới-tin-cậy — mọi quyết định còn lại đều rủi ro thấp và đã khai `(default)` bên trên.

## Render brief

Mỗi task một diagram; participant chung: `AUTHORED (người)`, `CODE (nguồn)`, `GENERATOR`, `DERIVED (sinh)`, `GATE (validator/medic)`.

- **T1**: [add] người khai ledger 3 lớp → [add] validator đọc ledger → [legacy] git tracked files → [block] file mới không lớp bị exit 2. Prose: sổ một chỗ, mọi gate sau tra sổ này.
- **T2**: [legacy] generator có sẵn → [add] bổ sung `--check` cho DERIVED thiếu → [add] medic gọi đủ bộ → [block] derived bị sửa tay → medic đỏ.
- **T3**: [add] 83 SKILL.md nhận `loop:`/`group:` → [legacy] sync-skills mirror → [add] build-overstack-docs đọc frontmatter, dict viết tay bị xoá → [block] skill thiếu trường → cảnh báo generator.
- **T4**: [legacy] os.listdir bị thay → [add] build-capabilities đọc graph → [add] output khai cả cái chết + cái không travel → [block] quan hệ không kiểm được (supersedes) ở lại AUTHORED.
- **T5**: [add] merge-regen.sh: union code → regen toàn bộ DERIVED → validator suite → [add] xuất diff A-B → [block] hoà giải tay file DERIVED = sai quy trình.
- **T6**: [legacy] /lint → [add] đếm tuổi draft, ngưỡng 14 ngày → [block] không chặn, chỉ bêu — quyết promote/archive là của người.
- **T7**: [legacy] travel-policy Tầng 2 "nguồn chân lý" → [add] đổi thành "nguồn chân lý của WHY" → [legacy] travel_policy_sync gác tiếp → [block] mô-tả-trùng-vai-hành-vi không còn được phép tồn tại.

## Self-review

**Phủ yêu cầu.** Ba vế của yêu cầu gốc — code là sự thật (T1/T2/T7), quan hệ rõ ràng suy được (T3/T4, FR-003), merge so sánh A-B hoặc thuần cộng thêm (T5, và SC-003 chính là vế "cộng thêm": thêm skill = một file, không đụng file chung) — mỗi vế về đúng task, không vế nào rơi. Năm triệu chứng nêu trong Context đều có FR trả nợ tương ứng.

**Quét chỗ bỏ ngỏ.** Không còn ô trống chờ đoán; giá trị chưa chắc duy nhất (ngưỡng 14 ngày, tên trường frontmatter, thứ tự chạy) đều nằm trong Assumptions có tag và có lý do.

**Nhất quán tên-kiểu.** Ba lớp gọi thống nhất AUTHORED/DERIVED/STATE toàn văn bản; "regen" dùng cho hành vi sinh lại, "--check" cho chế độ so drift, "merge protocol" cho quy trình T5 — không đặt tên thứ hai cho cùng một thứ. Số liệu (21→283, 15 draft, 7 skill, 83 skill) khớp với Context và các phần dưới.

## Origin
- **Source:** phiên 2026-07-21 — user đọc bài RDD (goonnguyen.substack), yêu cầu "lên plan chuyển dự án sang kiến trúc mới, src code là src of truth có ràng buộc bằng quan hệ rõ ràng"; đối chiếu với chuỗi đo 2026-07-20/21 (capability-map, cây vấn đề, bàn giao graph-foundation).
- **Concept nền:** [[graph-model]] · [[adapt-modes]] · [[skill-craft]] · `ADR-003` · `ADR-004` · bàn giao `200726-graph-foundation-handoff` (bước 4, 5)
- **Task:** `T-260721-02`
