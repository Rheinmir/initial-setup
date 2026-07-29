---
type: draft
title: br-assembly-provenance-isolation — vá #40 ở tầng /br + giữ truy vết bug→frame→clause sau agent tổng
status: proposed
tags: [br, ralph, issue-15, issue-40, provenance, assembly, traceback, isolation, map-territory]
timestamp: 2026-07-11
task: T-260711-01
---

# 110726-br-assembly-provenance-isolation

**Status:** proposed
**Issue:** GH#40 (map-not-territory) hạ xuống tầng thi công của GH#15 (/br pipeline).
**Sequence diagram**: [110726-br-assembly-provenance-isolation-seq.html](../../../html/110726-br-assembly-provenance-isolation-seq.html) — 5 sequence diagram + diễn giải đầy đủ, một sơ đồ mỗi task.

## What
Vá lỗ hổng #40 ở tầng /br bằng 5 cơ chế — provenance manifest, frame LẮP-RÁP chạy trên data thật diff ground-truth, assumption-gate, localizer+re-dispatch, và paraphrase/adversarial trong loop-runner — sao cho khi có "agent tổng" nối các component lại, **chuỗi truy vết bug→component→frame→clause vẫn nguyên và mọi fix vẫn cô lập đúng scope frame chủ, không lan sang phần khác.**

## Context
- **GH#40 [[050726-map-not-territory-fable5-unknowns]]** (`llmwiki/wiki/sources/draft/050726-map-not-territory-fable5-unknowns.md`): model mạnh lấp mơ hồ tự tin → lỗi lan nhiều file, lộ muộn; cần "tìm unknowns trước khi prompt" (paraphrase-plan gate), audit map khi đổi model, và ô "Giả định đang gánh" nhân rộng thành khối chuẩn. Chẩn đoán phiên này: dây chuyền /br **tối ưu "xanh theo bản đồ" không phải "đúng với lãnh thổ"** — bản đồ (BR.md + tiêu chí frame) vẽ một lần lúc slice rồi không đo lại; 30 hàm thuần pass cô lập nhưng không ai ráp ra sản phẩm diff được với Excel bàn giao.
- **Bản thiết kế ralph pipeline** (`llmwiki/wiki/sources/draft/050726-ralph-interview-pipeline.md`) đã tuyên bố vòng phản hồi khép kín Meadows: *"lỗi sản phẩm → truy `clause_id` → provenance = lens-assumed → tự sinh câu hỏi interview vòng sau"* — nhưng E7/E8/E9 (FRAME/RUN-LOG/MONITOR) đánh dấu **"đợt sau"** và chưa thi công. Nỗi lo của user chính là cái "đợt sau" chưa có.
- **Đã có sẵn (không làm lại):** mỗi frame `frame_id → clause_ids → parent_br_hash` + `scope_code` globs; `run.json` ghi `changed_files/scope_clean/out_of_scope_files`; commit per-frame; `fdk/tools/frame-lint.py` + `build-line-status.py` (đã dựng traceback lỗi→frame→clause); loop-runner 6 phanh + `scope_globs/protect_globs`. Liên quan: [[safe-change]], [[impact-check]], [[build-now-adapt-later]] (assumed = adapter boundary).

## Prior art — loop-engineering (cobusgreyling/loop-engineering)
Repo "loop engineering" (inspired Addy Osmani + Boris Cherny) chốt luận điểm: đòn bẩy nằm ở *thiết kế loop tự prompt agent*, không phải viết prompt lẻ. So với /br: phần **maker/checker split** (implementer chạy code, verifier gate bằng test), **worktree cô lập**, và **memory/state ngoài hội thoại** thì /br đã có tương đương và sâu hơn — provenance manifest (T1) là "loop-sync có xương sống" chứ không chỉ STATE.md phẳng; `scope_clean` bất biến máy-kiểm (T4) mạnh hơn worktree vật lý. Hai ý của họ /br CHƯA có và đáng absorb:

- **Phased rollout L1→L2→L3** (report-only → assisted fix → unattended). Frame mới — nhất là `assemble` (T2) — nên mặc định chạy ở bậc thấp nhất chỉ *diff + report*, không tự sửa; chỉ khi frame chủ ổn định mới cho T4 re-dispatch tự sửa. Đây là "chạy L1 một tuần trước khi tự động hoá" hạ xuống mức từng-frame.
- **loop-cost — ước token TRƯỚC khi chạy** (theo pattern × cadence × số ca sinh). T5 mới có budget guard *bị động*; thêm ước-lượng-trước để quyết `probe: on/off` và số vòng adversarial có căn cứ, thay vì chặn sau khi đã tiêu.

## Affected
| File / Symbol | How it changes |
|---------------|---------------|
| `fdk/tools/frame-lint.py` | thêm 2 luật: (a) sinh/kiểm `_manifest.json`; (b) frame kind `assemble` KHÔNG được liệt kê component file trong `scope_code` |
| `br/payroll/br/frames/_manifest.json` | **mới** — map `symbol/file → frame_id → clause_ids` (spine truy vết); sinh từ frontmatter |
| `br/payroll/br/frames/frame-p99-lap-rap.md` | **mới** — frame kind `assemble`: import p01–p30, chạy trên dataset bàn giao, xuất phiếu lương, diff ground-truth |
| `skills/br/SKILL.md` + `frame-template.md` | thêm `kind: frame\|assemble`, khối `assumptions:` bền, mode `/br assemble` |
| loop-runner (`loop-runner` skill) | thêm paraphrase-plan gate (trước) + new-case adversarial (sau green); localizer khi assemble diff fail |
| `fdk/tools/build-line-status.py` | render cột assumption + trạng thái assemble + đường localizer bug→component→frame |

## Side-effects có thể vỡ
- **Frame cũ (p01–p30):** không đổi frontmatter cũ → thêm field `kind` mặc định `frame`, `assumptions: []`. frame-lint đọc thiếu field phải fail-open (frame cũ vẫn lint xanh).
- **loop-runner hiện chạy được:** paraphrase gate + adversarial phải OPT-IN theo frame (`probe: on`), mặc định off để 30 frame cũ không đột ngột đổi hành vi.
- **Manifest lệch:** nếu manifest sinh sai, traceback trỏ nhầm frame → fix lan. Chống bằng: manifest sinh THUẦN từ frontmatter (không tay), frame-lint kiểm mọi `scope_code` glob có đúng 1 frame chủ (không chồng scope → không mơ hồ chủ sở hữu).

## Plan
- [ ] **T1 — Provenance manifest** `_manifest.json`: `file/symbol → frame_id → clause_ids`, sinh thuần từ frontmatter bởi frame-lint; kiểm 1-file-1-chủ (scope không chồng). Đây là xương sống của mọi truy vết.
- [ ] **T2 — Frame kind `assemble` (p99-lap-rap)**: scope CHỈ gồm `app/pipeline.py` + output sản phẩm; frame-lint CẤM nó liệt kê file component. Import p01–p30, chạy trên data bàn giao thật, xuất phiếu lương, diff ground-truth từ Excel.
- [ ] **T3 — Assumption-gate**: frame-lint + build-line-status quét `assumptions`/`verified:false`; ship/assemble CHẶN "done" khi còn assumed trên đường giao hàng → "Giả định đang gánh" từ thụ động thành cổng cứng.
- [ ] **T4 — Localizer + re-dispatch (bảo chứng cô lập)**: assemble diff fail → localizer bisect trace component → tra manifest ra frame chủ → rút ca lỗi end-to-end xuống unit test của đúng component → mở LẠI chỉ frame đó với `scope_globs` gốc. Agent tổng CHỈ lắp+khoanh vùng, frame-lint assert `changed_files` của assemble ⊄ component globs.
- [ ] **T5 — paraphrase-plan gate + new-case adversarial** (opt-in) trong loop-runner: trước run diễn giải frame vs clause; sau green spawn probe sinh ca mới từ data thật cố phá.
- [ ] **T6 — Phased rollout L1→L2→L3** (absorb loop-engineering): thêm field frame `rollout: L1|L2|L3`; frame mới + `assemble` mặc định `L1` (chỉ diff+report, không tự sửa). T4 re-dispatch tự sửa chỉ bật ở `L2`+. build-line-status hiện bậc rollout mỗi frame.
- [ ] **T7 — loop-cost estimate** (absorb loop-engineering): trước khi bật probe (T5) hoặc chạy assemble trên roster thật, ước token theo (số component × số ca sinh × vòng adversarial) để quyết `probe: on/off`; gắn vào budget guard của loop-runner thay vì chỉ chặn sau khi tiêu.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 provenance manifest | CLAUDE | logic parse frontmatter + bất biến 1-chủ, là spine — sai là lan, cần cẩn trọng | pending |
| T2 frame assemble | CLAUDE | kiến trúc cô lập (cấm chạm component) + diff ground-truth, quyết định thiết kế | pending |
| T3 assumption-gate | CLAUDE | cổng chặn ship, correctness-critical, không giao rẻ | pending |
| T4 localizer + re-dispatch | CLAUDE | trọng tâm nỗi lo user, phần khó nhất (bisect trace → frame → reduce case) | pending |
| T5 paraphrase + adversarial | CLAUDE | prompt-engineering tinh, chạm loop-runner đang hoạt động | pending |

*Tất cả một agent (CLAUDE): năm task khớp nhau chặt (cùng chạm frame-lint + loop-runner + manifest), tuần tự phụ thuộc (T4 cần T1 manifest; T2 cần T1), rủi ro lan cao → không phân mảnh sang CLI rẻ.*

## Milestones (thứ tự code — gộp 7 task thành 3 sóng)
7 task ở trên là *đơn vị thiết kế* (mỗi cái 1 sequence diagram); khi **thi công** gộp thành 3 mốc theo phụ thuộc, mỗi mốc là 1 diff chạy-được-và-test-được trước khi sang mốc sau. Đây là bước *dispatch* của orca-workflow (doc này = propose; gate = hook R7 vừa chạy; dispatch = 3 sóng dưới):
- **Mốc A — Spine (T1).** `_manifest.json` sinh thuần từ frontmatter + frame-lint assert 1-file-1-chủ. Nền của mọi truy vết; không phụ thuộc gì. Test: 2 frame cùng claim 1 file → lint đỏ.
- **Mốc B — Assemble + gate (T2 + T3).** Frame kind `assemble` chạy data thật diff ground-truth; assumption-gate chặn "done" khi còn assumed. Cả hai cần manifest của Mốc A.
- **Mốc C — Loop controls (T4 + T5 + T6 + T7).** Localizer+re-dispatch (cô lập fix), paraphrase/adversarial, phased rollout L1→L2→L3, loop-cost. Nhóm này là họ điều-khiển-loop → đóng gói song song thành **bộ skill `loop-*` mới** (loop-cost, loop-rollout, loop-localize) bọc quanh loop-runner, KHÔNG đổi tên skill cũ.

## Success (kiểm-chứng-được)
1. `_manifest.json` sinh bằng code, frame-lint fail nếu 2 frame cùng claim 1 file (kiểm 1-chủ).
2. `/br assemble` chạy p01–p30 trên data bàn giao → xuất phiếu lương; diff ground-truth = 0 dòng lệch HOẶC báo đúng bộ dòng lệch.
3. Cố sửa 1 component TRONG frame assemble → frame-lint CHẶN (assert scope). Đưa cùng lỗi qua localizer → nó trỏ đúng `frame-pNN` + clause, mở lại chỉ frame đó, `run.json.scope_clean=true`, `out_of_scope_files=[]`.
4. Frame còn `assumed` trên đường ship → assumption-gate chặn "done", build-line-status hiện đỏ assumption.
5. 30 frame cũ lint + chạy XANH không đổi hành vi (fail-open field mới; probe opt-in off).

## Render brief
- **T1:** slicer/frame-lint → đọc frontmatter mọi frame → sinh `_manifest.json` → kiểm 1-chủ (block nếu chồng). Steps: [add] parse frontmatter, [add] build map file→frame→clause, [block] 2 frame cùng file → fail, [legacy] build-line-status đọc manifest. Prose: manifest là bản đồ chủ-sở-hữu; mọi truy vết sau này tra nó thay vì đoán theo tên.
- **T2:** frame-lint kiểm kind=assemble → cấm component trong scope → assemble import p01–p30 → chạy data thật → diff ground-truth. Steps: [block] scope chứa component file → fail, [add] import components read-only, [add] run trên dataset bàn giao, [add] diff vs Excel ground-truth, [legacy] xuất phiếu lương. Prose: assemble là NGƯỜI LẮP không phải thợ sửa; nó chỉ được tạo lớp composition mỏng của riêng nó.
- **T3:** frame/ship → quét assumptions → còn assumed trên đường ship → chặn. Steps: [add] scan assumptions+verified:false, [block] assumed trên ship-path → CHẶN done, [add] escalate thành câu hỏi interview vòng sau. Prose: biến "Giả định đang gánh" thụ động thành cổng cứng, nối đúng vòng Meadows đã thiết kế.
- **T4:** assemble diff fail → localizer bisect trace → manifest → frame chủ → reduce ca xuống unit test → mở lại chỉ frame đó. Steps: [block] diff fail, [add] bisect component traces, [add] tra manifest ra frame+clause, [add] reduce end-to-end case → unit test component, [add] re-open chỉ frame đó scope gốc, [block] assemble tự sửa component → frame-lint chặn. Prose: câu trả lời trực tiếp nỗi lo — cô lập được bảo chứng vì agent tổng bị cấm sửa component; nó chỉ phát hiện + đẩy lỗi xuống đúng chủ.
- **T5:** trước run paraphrase frame vs clause → diff sớm; sau green spawn adversarial case-gen từ data thật. Steps: [add] paraphrase plan vs clause diff, [legacy] verify test green, [add] adversarial probe sinh ca mới từ data thật, [block] ca mới đỏ → quay lại revise. Prose: chuyển xanh-theo-spec thành xanh-theo-thực-tế; bắt lệch map/territory trước và sau khi chạy.

## Origin
Raise từ phiên 2026-07-11: user hỏi "chạy frame ra output nhàm thay vì sản phẩm production-tier — hổng ở đâu như #40", rồi lo agent tổng làm mất truy vết + fix lan scope. Chẩn đoán 5 lỗ hổng + đối chiếu overstack đã-có/thiếu ở transcript; propose này là bản thi công.
