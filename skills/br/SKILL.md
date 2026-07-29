---
name: br
description: >-
  Hub MỘT TÊN cho dây chuyền sản xuất kiểu Ralph (GH#15): biến tài liệu thô của
  user thành sản phẩm qua 5 mode — `/br interview` (đọc folder raw/ → đối chiếu bộ
  specs chuẩn S1–S10 → sinh bộ câu hỏi hỏi-bù dạng HTML xem trước + MD điền, cho
  phép lens chuyên gia điền thay mục chưa chắc), `/br compile` (answers → BR.md có
  clause_id + bảng "Giả định đang gánh"), `/br slice` (BR → frames nhỏ gắn chặt code,
  gác bằng frame-lint), `/br run <frame>` (mỗi frame chạy loop-runner có 6 phanh +
  dry-run + người gác · sau frame xanh TỰ chạy QC tất định 0-token), `/br qc` (audit
  senior 4-mục: /qc-code soi code + /qc-uiux soi UI/UX qua engine visual-qa), `/br status`
  (trang line-status.html tất định: frame nào chạy/kẹt/xong + truy ngược lỗi→frame→clause).
  Gọi khi user nói "br", "interview", "phỏng vấn yêu cầu", "soạn BR", "slice frame",
  "chạy frame", "qc frame", "audit ui mockup", "trạng thái dây chuyền", "ralph pipeline",
  hoặc invoke /br. User chỉ mô tả PHẠM VI, không cần nhớ lệnh con.
---

# Skill: br — dây chuyền sản xuất Ralph (BR-kỹ → frames → loop có harness)

> Hub 1-tên: user mô tả *phạm vi* (interview / compile / slice / run / status), KHÔNG
> phải nhớ nhiều lệnh. Nền tảng: council 028 (thin-slice, người-trong-vòng-lặp) +
> council 031/032 (loop v1 với 6 điều kiện bắt buộc — winner Taleb mean-rank 1.0).

## When to use
- User có tài liệu yêu cầu (thô/không cấu trúc) và muốn biến thành sản phẩm có kỷ luật.
- User nói: interview / phỏng vấn yêu cầu / soạn BR / slice frame / chạy frame / trạng thái dây chuyền / ralph.

## Đồ nghề tất định (đã build + selftest — KHÔNG viết lại)
| Tool | Việc | selftest |
|------|------|----------|
| `skills/br/assets/spec-template.md` | bộ specs chuẩn S1–S10 (khung tham chiếu mọi project) | — |
| `skills/br/assets/frame-template.md` | template TẤT ĐỊNH cho mọi frame (frontmatter + 4 section body người-đọc-hiểu) | — |
| `skills/br/assets/design-template.md` | template thiết kế tái dùng (khung Google design-doc + design system nạp từ `/high-end-visual-design`) → copy thành `br/DESIGN.md` | — |
| `fdk/tools/frame-lint.py` | gác frame 7 luật (schema · scope · test-first · freshness · DAG · exclusive-scope · **content**) | `frame-lint.py selftest` |
| `harness/scripts/loop-runner.py` | loop 6 phanh (max_iter·budget·no_progress·escalate·**diff-jail**·**test-hash**) | `loop-runner.py selftest` |
| `fdk/tools/build-line-status.py` | monitor tất định (frame·run-log·BR → json+html, `--check`) | `build-line-status.py selftest` |

Runtime artifacts sống ở `br/` tại gốc project (không phải trong skill): `br/spec-filled.md`,
`br/interview/NNN-{questions.html,answers.md}`, `br/BR.md`, `br/BR.clauses.json`, `br/frames/*.md`,
`br/frames/index.md`, `br/frames/<id>.run.json`, `br/line-status.{json,html}`.

## Mode 1 — `/br interview`
1. Đọc TẤT CẢ file trong `llmwiki/raw/` (chỉ đọc — luật cấm ghi raw/). Nếu trống → hỏi user bỏ tài liệu vào.
2. Đối chiếu bộ specs chuẩn `skills/br/assets/spec-template.md`: bóc thông tin từ raw map vào từng field S1–S10 → ghi `br/spec-filled.md`. MỖI field ghi `status` (`filled|missing|conflict|assumed`) + `provenance` (`raw:<file>`).
3. Gap-diff: field `missing`/`conflict` → sinh bộ câu hỏi. **Mỗi field là MỘT spec rõ (rigor /orca-workflow):** câu hỏi nêu field LÀM GÌ + "trả lời thế nào là ĐỦ" (tiêu chí chấp nhận của field), không hỏi mơ hồ. Ghi 2 file (cùng số thứ tự NNN):
   - `br/interview/NNN-questions.html` — xem theo section, có giải nghĩa thuật ngữ + tiêu chí-đủ mỗi field, in full-path (R16), dark-mode. CHỈ hỏi phần thiếu.
   - `br/interview/NNN-answers.md` — block điền theo field-id (vd `## S4.2` … khoảng trống), để user gõ câu trả lời.
3b. **`--proactive` (T-260714-01, gọi tắt `/br auto`)** — user muốn máy điền phần thiếu thay vì hỏi hết: chạy `python3 fdk/tools/br-fill.py fill --root .` (tất định, không model). Tool tra registry defaults (`skills/br/assets/defaults.yaml` — bảng 26 điều kiện loop + convention github/spec-kit; project override `br/defaults.yaml` thắng khi trùng field) và in 2 nhóm:
   - **ĐỀ XUẤT MÁY ĐIỀN** → dán vào `NNN-answers.md`, GIỮ NGUYÊN `filled_by: <source>:<refs>` + `verified: false` từng mục (kỷ luật lens-fill áp cho mọi tầng máy điền).
   - **CÂU HỎI THẬT** (field carve-out — auth/quyền, trust boundary, tiền — và field không có default): chọn **≤5 câu** theo Impact × Uncertainty (carve-out đã xếp trước, chiếm suất hỏi trước) đưa vào questions.html; phần vượt trần thì lens-fill (bước 5). Carve-out KHÔNG BAO GIỜ nhận giá trị máy — kể cả registry có entry, kể cả lens.
4. **STOP** — báo user mở HTML xem + điền answers.md.
5. Nếu user bật `--lens-fill` (hoặc nói "cho chuyên gia điền mục chưa chắc"): bốc lens bằng `python3 harness/scripts/council.py roster --case product --json`, điền các field `missing` mà user đánh dấu "không chắc" → mỗi field đóng dấu `filled_by: lens:<tên>` + `verified: false`. KHÔNG trộn với câu trả lời thật của user.

## Mode 2 — `/br compile`
1. Đọc `br/spec-filled.md` + `br/interview/*-answers.md` đã điền.
2. Sinh `br/BR.md`: mỗi điều khoản có `clause_id` (kế thừa field-id, vd `S4.2`) + provenance (`raw|user|lens:<tên>`). Đầu file là bảng **"Giả định đang gánh"** liệt kê mọi clause `lens`/`assumed` (fail-fast: nhìn một phát biết đang cược gì).
   - **Sản phẩm có UI (S7.5)**: chốt một clause NFR (vd `N01 giao-diện`) TRỎ tới `br/DESIGN.md`, KHÔNG chép luật design vào BR. Đồng thời copy `skills/br/assets/design-template.md` → `br/DESIGN.md` và điền §1/§2/§4/§6/§7 cho sản phẩm (giữ nguyên §3/§5 kế thừa). BR = *phải có theme/design*; DESIGN.md = *design trông ra sao*.
3. Sinh `br/BR.clauses.json`: `{clause_id: {provenance, assumed: bool, fields: ["S4.2", …]}}` — `fields` khai field spec S1–S10 mà clause hiện thực (khoá của checksum hợp đồng); monitor (`/br status`) đọc file này để tô cam clause assumed. Bảng "Giả định đang gánh" **nhóm theo nguồn fill** (`default` / `spec-kit` / `lens`) để người duyệt thấy đang cược gì từ đâu.
4. **Gate checksum hợp đồng (vá G1 — council c9dc13d):** `python3 fdk/tools/br-fill.py check-contract --root .` — mọi required field S1–S10 phải có clause đối ứng; ĐỎ là compile FAIL, sửa BR cho tới khi xanh, không có chuyện "compile xong mà hợp đồng thủng".

## Mode 3 — `/br slice`
1. Đọc `br/BR.md`. ĐỀ XUẤT danh sách lát cắt: mỗi lát = {clause_ids, scope_code dự kiến (≤3 file), scope_test, acceptance_test, **depends_on**}. **STOP cho user duyệt/sửa/gộp/tách TỪNG lát** (người-trong-vòng-lặp — chốt chặn lỗi tương quan slicer). Lô đầu ≤ 3–5 frame.
   - **`depends_on` là bắt buộc nghĩ, không bắt buộc có** (GH#75, distill Atomic Task Graph): dây chuyền là ĐỒ THỊ chứ không phải danh sách. Frame B khai `depends_on: [frame-A]` khi B *không thể xanh* nếu A chưa xanh (B gọi API/store/schema A dựng). Không dựa ai → `depends_on: []`. Khai đúng thì được ba thứ miễn phí ở mode 4: thứ tự chạy tự đúng, frame đỏ tự chặn nhánh dưới, và sửa một frame chỉ phải chạy lại đúng nhánh của nó. Khai bừa (nối cho "có vẻ hợp lý") thì mất song song và tạo chờ giả — chỉ nối khi có phụ thuộc THẬT.
2. Ghi `br/frames/frame-NNN-<slug>.md` **THEO TEMPLATE `skills/br/assets/frame-template.md`** (schema v0 + 5 section body bắt buộc: Nghiệp vụ · Input/Output · **Spec (FR/SC)** · Tiêu chí nghiệm thu · Ngoài phạm vi — viết cho NGƯỜI VỀ SAU đọc-hiểu, frame-lint R7 gác cứng: frame_id phải có slug nghiệp vụ, muc_tieu không được generic, mỗi frame có FR-id/SC-id rõ, section không được rỗng) + `parent_br_hash = sha256(br/BR.md)`.
3. Sinh registry `br/frames/index.md` (bảng frame_id · clause_ids · scope_code · status · run_log_ref) từ frontmatter các frame.
4. Gác: `python3 fdk/tools/frame-lint.py check br/frames --root . ` — xanh hết mới coi là slice xong (gồm R6 exclusive-scope: 2 frame không được giẫm cùng file).
5. `python3 fdk/tools/br-prompts.py sync` — bổ sung mục prompt cho các frame mới vào sổ `br/prompts.md` (user sửa tay được ngay).

## Mode 4 — `/br run <frame>`
**Cách gọi tất định (đã wire — mặc định IN-PLACE, MỘT cây làm việc duy nhất):**
```
python3 fdk/tools/br-run.py run br/frames/<frame>.md --root .
# xem prompt sẽ gửi mà không chạy: thêm --print-prompt
# chạy cả hàng đợi resumable: python3 fdk/tools/br-queue.py run --queue br/queue.yaml
# sửa 1 frame → chạy lại ĐÚNG nhánh của nó, không cả dây chuyền:
#   python3 fdk/tools/br-queue.py affected <frame_id> --queue br/queue.yaml --reset
#   python3 fdk/tools/br-queue.py run --queue br/queue.yaml
# cần cô lập thư mục thật sự (hiếm): thêm --worktree
```

**Queue chạy theo ĐỒ THỊ, không theo thứ tự gõ tay** (GH#75 — distill Atomic Task Graph, arXiv 2607.01942):
- **Topo order**: `br-queue` đọc `depends_on` của từng frame và tự sắp thứ tự (không phụ thuộc thì giữ nguyên thứ tự khai — queue cũ chạy y như trước).
- **Frame đỏ CHẶN cả nhánh dưới nó** (`status: blocked`, ghi `blocked_by`): input của nhánh đó đã hỏng, chạy tiếp chỉ tốn lượt model cho một cái chắc chắn fail. Nhánh KHÔNG liên quan vẫn chạy bình thường — một frame hỏng không còn đứng chặn cả dây chuyền.
- **Sửa cục bộ (`affected`)**: sửa một frame → chỉ frame đó + nhánh dưới nó về `pending`, mọi frame xanh khác giữ nguyên. Đây là chỗ trả tiền: trước đây một frame hỏng giữa chuỗi buộc chạy lại nhiều hơn mức cần.
- **KHÔNG làm subgraph-reuse cache** (paper có, ta bỏ có chủ ý): `status: done` đã bỏ qua frame xanh rồi; thêm cache theo hash ở quy mô vài chục frame chỉ đẻ bug stale. Giới hạn của chính paper cũng áp ở đây — lợi ích còn nguyên khi đồ thị nhỏ và acceptance_test tất định; graph rất lớn hoặc test/tool trả kết quả bấp bênh thì lịch chạy này mất tác dụng.
`br-run.py` tự: (0) **TIER-GATE** — frame khai `tier: compensable|irreversible` trong frontmatter (effect không-đảo: gọi API ngoài/gửi mail/ghi DB) bị CHẶN cho tới khi người chạy lại với `--ack-tier` (SHEPHERD gate-before-materialize), (1) frame-lint, (2) kiểm working-tree sạch, (3) chạy loop-runner **NGAY TRONG cây hiện tại** với revise **đã trỏ tới `fdk/tools/br-revise.py`** (render `skills/br/assets/revise-prompt.md` → `claude -p` tools bó hẹp), (4) frame xanh → commit vào nhánh hiện tại, message gắn frame_id (mốc revert/blame), (5) in tóm tắt 1 dòng, (6) ghi `run_log_ref` vào frame, (7) **ghi mốc vào SỔ TRACE** `.checkpoints.jsonl` (checkpoint-trace/SHEPHERD — record trỏ commit sẵn, không double-commit) → xem cả dây chuyền: `python3 fdk/tools/checkpoint.py list`; **rollback cả pipeline về frame bất kỳ theo TÊN**: `checkpoint.py rollback <frame_id>` (giữ lịch sử, cảnh báo effect tier không-đảo sau mốc).
**Vì sao in-place là mặc định (feedback user 05/07):** N frame = N worktree = N folder ma không ai lục; luồng người thường là *bật app lên xem*, sửa phải hiện ngay trong cây đang chạy app. **Kiểm soát không-phạm-scope nằm ở HARNESS** (diff-jail revert mỗi vòng + FINAL SCOPE SWEEP + test-hash + scope_clean + R6 exclusive-scope), không nằm ở cô lập thư mục. Không ưng kết quả → `git revert <commit frame>`.

Bước thủ công tương đương (nếu cần tinh chỉnh tay):
1. `frame-lint check` frame đó xanh. Kiểm **working-tree SẠCH** (`git status --porcelain` rỗng) — bẩn thì từ chối.
2. Tạo **git worktree riêng** từ `baseline_ref` của frame (jail filesystem — frame đầu KHÔNG đụng harness/hook/CI).
3. Chạy loop — commit per-frame VÀO WORKTREE BRANCH (không phải main); người vẫn merge tay:
   ```
   python3 harness/scripts/loop-runner.py run \
     --verify "<acceptance_test>" --revise "<adapter claude -p>" \
     --state "<scope_code>" --scope "<scope_code>" --protect "<scope_test>" \
     --baseline "<baseline_ref>" --commit-on-success \
     --commit-message "frame(<frame_id>): <muc_tieu> [<clause_ids>]" \
     --max-iter <g> --budget-seconds <g> --no-progress-k <g> --escalate-after <g> \
     --log br/frames/<id>.run.json --cwd <worktree>
   ```
   Adapter revise = `claude -p` với tools bó hẹp (`--allowedTools Edit,Write,Read,Grep,Glob` — KHÔNG Bash tự do, không network), prompt dựng từ `muc_tieu` + `scope_code` + output verify fail gần nhất.
   **Truy vết frame→code (điều kiện tiên quyết — chắc frame tạo code nào + không phạm scope):**
   - Run-log ghi `changed_files` = file THẬT frame đã đổi (≠ scope dự định); `scope_clean`=true khi mọi file ⊆ `scope_code`; `attempted_out_of_scope` = file frame ĐỊNH ghi ngoài scope nhưng đã bị revert.
   - **FINAL SCOPE SWEEP**: mọi lần loop dừng (kể cả PROTECT_VIOLATION), loop-runner revert sạch mọi file ngoài `scope_code` → worktree LUÔN scope-clean, `changed_files` LUÔN ⊆ `scope_code`. Kiểm soát hoàn toàn, không chỉ dựa lời dặn prompt.
   - `--commit-on-success` chỉ commit khi verdict=SUCCESS VÀ scope_clean; message gắn `frame_id` → `git blame` truy đúng frame. `--baseline` = commit gốc để tính diff (thường HEAD của worktree lúc bắt đầu).

### Prompt & queue (chạy nhiều frame, resume được)
- **📒 SỔ PROMPT TỔNG (nguồn ƯU TIÊN #1, user sửa tay không cần model)**: `br/prompts.md` — MỘT file, mỗi frame một mục `## <frame_id>`. Mở ra, tìm frame, sửa/THÊM nội dung thoải mái (placeholder `{{...}}` giữ nguyên để máy điền lúc chạy). `python3 fdk/tools/br-prompts.py sync` tự thêm mục cho frame mới, KHÔNG BAO GIỜ đè mục đã sửa tay (chạy sau mỗi `/br slice`); `list`/`get <frame_id>` để tra. Thứ tự ưu tiên khi run: **sổ prompt > queue inline > prompt_file > template mặc định**.
- **Template gốc (seed cho sổ)**: `skills/br/assets/revise-prompt.md`. Adapter `fdk/tools/br-revise.py` render nguồn thắng cuộc → gọi `claude -p` (tools bó hẹp). Xem prompt sẽ gửi: `br-revise.py run --frame <f> --verify "<cmd>" --print`.
- **File QUEUE** (`br/queue.yaml`, mẫu `skills/br/assets/queue.example.yaml`): DANH SÁCH frame để chạy tuần tự; mỗi mục hoặc `prompt_file:` (trỏ file template) HOẶC `prompt:` (ghi text trực tiếp, vẫn hỗ trợ placeholder). Driver `fdk/tools/br-queue.py run --queue br/queue.yaml` chạy từng mục, ghi `status` back sau MỖI mục → **chạy lại queue = bỏ qua `done`, chạy tiếp** (resume). `--dry-run` xem mỗi mục dùng prompt nào; `list` xem trạng thái.
- Adapter `claude -p` là ranh giới `verified:false` (BNAL) — template + queue + render đều tất định + selftest (`br-revise.py selftest`, `br-queue.py selftest`).
4. **Điều kiện KILL viết TRƯỚC** (via negativa): vd diff-jail cắn ≥2 lần / test-hash cắn 1 lần → vứt cả run, không cứu, không nâng phanh.
5. Loop dừng → in **tóm tắt MỘT DÒNG** (verdict · số vòng · diffstat · lệnh verify cuối) + chạy `python3 fdk/tools/medic.py --ci`. **STOP** — người đọc diff trong worktree, tự quyết merge/chạy-tiếp/vứt.
6. Điền `run_log_ref` + `outcome` vào frame + registry. Ghi lesson (kể cả điều KHÔNG xảy ra — phanh nào chưa từng cắn).

## Mode 4b — `/br find <file-hoặc-từ-khoá>` — trỏ vào chỗ lỗi, ra frame/prompt phụ trách
Luồng người thường: bật app → thấy lỗi → trỏ vào khúc đó:
```
python3 fdk/tools/br-find.py "src/auth/login.py"     # theo file
python3 fdk/tools/br-find.py "đăng nhập"              # theo từ khoá / clause
```
In ra: frame phụ trách (khớp theo file THẬT đã đổi > scope_code > từ khoá) · điều khoản BR · **prompt nằm ở đâu** (inline trong queue.yaml / prompt_file / template mặc định) · lệnh chạy lại ĐÚNG frame đó sau khi sửa prompt. Hoạt động được vì R6 exclusive-scope (frame-lint) ép mỗi file chỉ thuộc MỘT frame.

## Mode 4c — `/br qc [frame]` — audit senior QC (LLM 4-mục) trên mockup/frame
Sau khi có mockup/frame xanh, chạy CẶP MẮT SENIOR (đắt=LLM, gọi tay — phần rẻ tất định đã tự chạy sau mỗi `/br run`):
- **Code:** gọi `/qc-code` (Skill tool → `qc-code`) soi diff frame — 4 mục security/performance/naming/logic + sinh test tái hiện `qc-*`.
- **UI/UX:** gọi `/qc-uiux` (Skill tool → `qc-uiux`) audit mockup — 4 mục a11y/hierarchy/consistency/antipattern; phần đo được (contrast/tap-target/overlap/misalign/missing-label) chạy qua engine visual-qa headless:
  ```
  node skills/visual-qa/assets/route-shots.mjs <base-url-mockup> --audit
  ```
- Verdict CẦN SỬA → sửa trước khi chốt frame. **Advisory** — verdict LLM là ý kiến; số đo engine + test `qc-*` mới gác cứng (đã tự chạy ở `/br run` và `verify-before-commit` bước 3b). Không có frame chỉ định → audit các route mockup hiện có.

## Mode 5 — `/br status`
1. `python3 fdk/tools/build-line-status.py build --root .` → `br/line-status.json` + `llmwiki/html/line-status.html`.
2. In tóm tắt 3 dòng (tổng quan trạng thái · frame đáng chú ý nhất · đường dẫn HTML). Trang cho truy ngược lỗi→frame→clause; clause assumed tô cam → quay `/br interview` vòng sau nếu lỗi rơi vào assumed.

## Mode 6 — `/br sync` (frame ↔ GitHub sub-issue)
Distill `automazeio/ccpm`: mỗi frame → một GitHub sub-issue để team thấy tiến độ + hand-off. KHÔNG làm lại provenance (clause_id/manifest đã sâu hơn ccpm); chỉ lớp đồng bộ mỏng trên `gh`.
1. `python3 fdk/tools/br-sync.py sync br/frames --root . --repo <owner/repo> --dry-run` — LUÔN dry-run trước (không gọi gh, không ghi mapping).
2. Bỏ `--dry-run` khi chắc → tạo sub-issue cho frame chưa map, ghi `br/frames/issue-mapping.json`. Idempotent. `--epic` tạo epic-issue. `status`/`selftest` có sẵn.
3. Tạo issue là hành động ra-ngoài repo → xác nhận trước khi bỏ `--dry-run`.

## Mode 7 — `/br contract` (UI Contract chốt thực hiện, md+html)
Tách trục CODE (frame) khỏi trục HIỂN THỊ (screen/route). Chuẩn mọi dự án:
1. Frame khai `ui_role: none|screen|panel|widget|form|action` + `ui_screen` (frame-template) + section "## UI hoạt động ra sao".
2. `br/ui-layout.yaml`: `nav_style` + `screens[]` (id·title·**route thật**·frames[]). Sửa file này gom màn KHÔNG đụng frame.
3. `python3 fdk/tools/br-contract.py build br/frames --layout br/ui-layout.yaml --root .` → `br/UI-CONTRACT.md` + `.html`. Bảng frame·làm gì·ui_role·màn·route·clause·acceptance + đếm frame/màn/route + cảnh báo lệch. `selftest` có sẵn.

## Stream UI thống nhất + Spec rõ ràng (distill hallmark + orca-workflow)
Hai lỗ hổng của dây chuyền nhiều-frame, vá bằng hai cơ chế distill:

**A. UI/UX thống nhất XUYÊN FRAME (distill `hallmark`).** Mỗi frame chạy độc lập qua loop-runner → dễ mỗi frame một kiểu, mockup chắp vá. Cơ chế hallmark: **`br/DESIGN.md` = HỆ TOKEN KHOÁ**, đọc trước và đè mọi lựa chọn; **luật ĐẢO NGƯỢC** — frame phải GIỐNG nhau (chia sẻ hệ), không đa dạng hoá; **locked-token** — mọi màu/font/spacing trỏ token có tên (`var(--…)`), CẤM inline. Áp vào /br:
- `/br compile` copy `design-template.md`→`br/DESIGN.md` với bảng token §4 + §4.1 (token khoá) là NGUỒN CHÂN LÝ.
- Frame UI ở `## UI hoạt động ra sao` chỉ dùng token DESIGN.md; thêm giá trị mới = thêm token vào DESIGN.md rồi trỏ, không tự chế tại frame.
- Drift token bị `/qc-uiux` (consistency) + engine visual-qa bắt → "stream" chạy bằng gate tất định, không bằng lời dặn. Kết quả: frame-01 và frame-09 trông như MỘT sản phẩm.

**B. Mọi frame + màn interview cần SPEC rõ (học `/orca-workflow`).** Propose sinh FR/SC id-bền + acceptance; /br mang rigor đó xuống mọi mắt xích:
- **Frame:** frame-template có section `## Spec (FR/SC)` (frame-lint R7 gác cứng) — mỗi frame khai FR-id (hệ thống PHẢI…) + SC-id (đo NGƯỜI), acceptance_test là bằng chứng của SC, mỗi dòng nghiệm thu truy về một FR. Frame thiếu FR/SC rõ = chưa xong, y như interview thiếu field.
- **Interview:** mỗi field S1–S10 hỏi ra phải là MỘT spec rõ — câu hỏi nêu field làm gì + tiêu chí "trả lời thế nào là ĐỦ" (không hỏi mơ hồ). Field còn `missing/assumed` = spec chưa đủ, hiện ở bảng "Giả định đang gánh" để không trôi.

## Vòng THIẾT KẾ cho frame UI (skill `/design-twice`) — chạy TRƯỚC khi code

**Bắt buộc với mọi frame `ui_role≠none`:** trước khi viết một dòng code UI, chạy `/design-twice`
để có **2–3 phương án KHÁC NHAU TẬN GỐC**, so sánh, chọn 1, rồi ghi mục `## Thiết kế (design-twice)`
vào chính frame (3 phương án + phương án chọn + lý do + ý ghép từ bản thua).

- **Vì sao:** ý đầu tiên là ý *dễ nghĩ nhất*, không phải ý *tốt nhất*. Không có phương án để so thì
  agent chỉ biết **vá** phương án duy nhất — mỗi vòng vá đẻ một lỗi mới (theme Lume: 5 vòng vá).
- **Tín hiệu phải quay lại vòng thiết kế:** đang **vá lần thứ 2 cho cùng một chỗ**, hoặc user chê
  "xấu/bựa/không ưng" mà không chỉ ra lỗi cụ thể ⇒ **hình dạng sai**, vá thêm chỉ tốn công.
- Frame UI **thiếu mục `## Thiết kế (design-twice)` = chưa xong** (R7 content coi là thiếu nội dung).
- Thiết kế xong mới tới `## UI hoạt động ra sao` → code → gate `/visual-qa` bên dưới.

## Vòng tự-kiểm THỊ GIÁC cho frame UI (skill `/visual-qa`)
**Nguyên tắc (không phải luật re-check riêng):** sửa UI = edit spec + code CỦA FRAME đó rồi
`/br run` lại. Muốn "chạy lại frame là tự re-verify UI" thì **`acceptance_test` của frame UI
phải CHÍNH LÀ visual-qa** — test hit vào UI, không phải unit-test cạnh bên. Đây là điểm đòn bẩy
cao: không cần dặn agent "nhớ kiểm lại", vì loop verify của chính frame đã ôm luôn cái kiểm UI.
- Frame `ui_role≠none` đặt: `acceptance_test: "node skills/visual-qa/assets/route-shots.mjs --base <url> --route <route> --assert --user <u> --pass <p> --out <dir>"` → exit 1 nếu route không 200/rỗng → frame ĐỎ tới khi UI render đúng. `/br run` lại sau mỗi sửa = tự re-verify.
- Sau green, agent `Read` ảnh (skill `/visual-qa`) → `FINDINGS.md` (route·mức·cách sửa) → mỗi finding là một sửa spec+code của frame → `/br run` lại. Bắt lỗi theme/brand/empty-state unit-test không thấy; dùng khi extension MCP lỗi localhost.
- **Cấm sửa UI tay ngoài `/br run`** (nợ p28 05/07): sửa tay = mất gate + không re-verify. Mọi sửa UI phải qua frame.

## Rail — công tắc harness của dây chuyền (`/br rail on|off|skip`)
"On the rails" = đang trong tầm gác. **MẶC ĐỊNH ON — auto-on cả phiên khi dùng /br.**
- `python3 fdk/tools/br-rail.py status --root .` → trạng thái + **LUÔN nhắc bật/tắt được**.
- `on` (gác đủ) · `off` (tắt gate MỀM tới khi bật lại) · `skip` (bỏ gate mềm ĐÚNG 1 lần rồi tự bật lại + cảnh báo).
- **AN TOÀN (bất biến):** off/skip CHỈ tắt **gate mềm** — R7 content · visual-qa UI · assumption-gate. **PHANH CỨNG** (diff-jail · test-hash · scope-clean) + cấu trúc R1–R6 + hook bảo mật KHÔNG BAO GIỜ tắt qua đây.
- **Wiring:** đầu `/br run`, đọc `br-rail.py consume` → nếu off/skip thì gọi `frame-lint … --soft-off` (bỏ R7+assumption), loop-runner phanh cứng vẫn nguyên; IN trạng thái Rail + dòng nhắc mỗi lần chạy.

## Bằng chứng > lời (luật kiểm UI — feedback 2026-07-13)
Kiểm UI/thị giác chỉ hợp lệ khi có **FILE ẢNH thật + `MANIFEST.json`** liệt kê route→ảnh→bytes (skill `/visual-qa`). **Không có file = CHƯA TỪNG LÀM = fail**, bất kể model nói gì. Sau khi sửa UI phải chụp LẠI + đọc lại trước khi green. Cấm "cho pass" bằng suy luận. (Cũng là luật /fdk.)

## Rules
- **Người là cổng cuối** — KHÔNG tự commit/merge output frame; dry-run + người duyệt (council 028).
- **Phanh bất khả xâm phạm** — không bao giờ nâng max_iter hay tắt guard "để nó xong". Thừa phanh rẻ hơn thiếu phanh (council 031/032).
- **Prompt-dặn KHÔNG phải lớp an toàn** — scope-jail/test-hash là code tất định (loop-runner guard 5/6), không phải lời dặn trong prompt (council 5/5 ghế).
- **Lens-fill luôn `verified: false`** — không trộn với câu trả lời thật; luôn hiện ở bảng "Giả định đang gánh".
- **Slicer người-trong-vòng-lặp** ở đợt đầu — chưa full-auto (lỗi slicer là lỗi tương quan, blast-radius = toàn BR).
- **File-first, on-demand** — mọi artifact là file travel-được; skill gọi tay, KHÔNG hook auto-fire (ADR-004).
- HTML sinh ra cho người xem phải giải nghĩa thuật ngữ + in full-path (R16).
