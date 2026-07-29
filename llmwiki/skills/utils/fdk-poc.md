---
name: fdk-poc
description: >-
  POC luồng /br: tạo PROJECT THẬT trong Orca (orca-cli) → CURL cài overstack từ REMOTE (đường
  người mới) → nạp context bằng cách copy tài liệu THẬT sang llmwiki/raw/ → chạy /br TỪ ĐẦU, ghi
  lại TỪNG BƯỚC THẬT (rc + log) rồi render trang visualize để người xem ĐỌC LOG + CHẤM từng bước.
  Luật cốt lõi: tool KHÔNG BAO GIỜ BỊA BƯỚC — mọi bước hoặc do tool chạy thật, hoặc do agent chạy
  thật rồi `record`. Có `probe` để soi một /br project có sẵn bằng tool thật (frame-lint/pytest/
  line-status/checkpoint). KHÁC /fdk-uat (test nhanh xanh-đỏ "người mới curl về chạy không"):
  fdk-poc nhắm CHỨC NĂNG THỰC TẾ chạy ra sao. Gọi khi user nói "fdk-poc", "poc luồng", "chạy thử
  project mới", "visualize luồng br chạy", "/fdk-poc".
---

# Skill: fdk-poc — POC luồng /br chạy THẬT + visualize

## When to use
- Muốn THẤY một luồng ĐẦY ĐỦ chạy thật trên một project MỚI (không phải nghe kể).
- Chứng năng lực mới **tới tay người dùng** qua đường remote + chạy được trên tài liệu thật.
- KHÔNG dùng để: test nhanh xanh/đỏ (đó là `/fdk-uat`) hay chạy sản phẩm thật (đó là `/br`).

## MỤC TIÊU THẬT (user chốt 17/07/26) — POC để XEM, không để THAM GIA
> "tôi muốn xem prompt được inject **từ từ** để biết **bước nào BẮT BUỘC** khi làm việc với /br,
> để biết **những lệnh nào tôi phải nhớ** — chứ nhớ all thì không nhớ nổi."

Ba hệ quả **bắt buộc**:
1. **KHÔNG-NGƯỜI-GÁC.** POC **cấm dừng chờ user trả lời**. Field `missing`/`conflict` → `/br auto`
   (registry defaults) + `--lens-fill` tự điền, đóng dấu `verified: false`; ghi lại bằng
   `record --asks "<bản thật sẽ hỏi gì ở đây>"`. User **vào trả lời = POC đã sai mục tiêu**.
2. **Hiện prompt inject TỪ TỪ.** Mỗi bước phải in được cái nó bơm vào model
   (`br-revise.py --print` cho `/br run` — xem mục "LUỒNG INJECT GÌ" dưới).
3. **Trả lời "phải nhớ mấy lệnh".** `record --must` đánh dấu bước **user THỰC SỰ phải gõ**;
   `render` in KPI **LỆNH PHẢI NHỚ** + `N/M bước user gõ` — phần còn lại tool tự fire.
   Mục tiêu con số: **≈1 hub** (`/br`) — khớp bài học discoverability.

## LÁI TỪNG LƯỢT — không bắn 1 prompt rồi thả (bài học 17/07/26)
> User: *"có mỗi 1 prompt làm tôi chả hình dung được là làm việc cùng ntn? phải kiểu hỏi đáp chứ —
> vấn đề chính là việc bạn không theo dõi session đấy."*

Một **mega-prompt fire-and-forget** hỏng cả 3 mục tiêu: không thấy prompt inject **từ từ**,
không thấy **cách cộng tác**, và coordinator **không giám sát gì**. Bắt buộc:
- **`drive_step(proj, handle, text, …)`** = `terminal send --enter` → `terminal wait --for tui-idle`
  → `terminal read` → `record`. MỘT bước một lượt; coordinator TRẢ LỜI khi agent hỏi.
  User **ngồi xem** hội thoại, không phải người trả lời.
- **Handle, không phải title:** selector đúng là `term_…` (`terminal list --json` → `.handle`).
  Dùng `--terminal "title:…"` → `terminal_handle_stale`, coordinator mù hoàn toàn.

### Theo dõi THẬT = đọc TRANSCRIPT, không scrape TUI
`orca terminal read` chỉ trả **màn hình TUI đã vẽ lại** (`❯ Crunched for 18s`) — KHÔNG có hội thoại.
Nguồn thật là transcript Claude Code:
```
~/.claude/projects/<path-slug>/<session-id>.jsonl     # mỗi dòng 1 record; type=user|assistant
```
Đọc nó mới thấy đúng câu hỏi/câu trả lời (vd phiên payroll-poc: 757 record · 456 lượt).
**Kết luận "đã theo dõi" mà chỉ nhìn tail TUI là tự lừa.**

### BẪY LỚN: workspace giữ SNAPSHOT ĐÔNG CỨNG — sửa repo KHÔNG tới agent
Ca thật 17/07/26 (agent chặn coordinator **2 lần**, cả 2 lần agent ĐÚNG):
- `curl bootstrap` cài **bản `fdk/tools/*` RIÊNG vào workspace** (payroll-poc: `fdk-poc.py` 38.110B @09:33).
- Coordinator sửa repo (`42.676B @10:43`, +`--must/--asks`) rồi bảo agent *"tool NAY ĐÃ CÓ"* → **SAI**:
  agent grep bản CỦA NÓ → `0 matches` → **từ chối chạy trên tiền đề sai**.
- Cùng lớp lỗi với `install.sh` hardcode `#orca`: **thứ đã cài KHÔNG tự tươi**.

**Luật:** trước khi bảo agent dùng flag/tool mới → **đồng bộ bản trong workspace TRƯỚC**
(`cp` từ repo, hoặc curl lại), rồi **để agent tự verify** (`--help`/grep), rồi mới ra lệnh.
Coordinator khẳng định "tool đã có" mà không kiểm bản-trong-workspace = tiền đề sai.

### Prompt nhắc flag mà tool CHƯA CÓ ⇒ agent đúng khi từ chối
Ca thật: prompt bảo `record --must/--asks` nhưng agent spawn TRƯỚC commit thêm 2 flag đó.
Agent `--help`/grep source, thấy không có, **từ chối chế flag giả** và báo lại — hành vi ĐÚNG.
⇒ Luật: **spawn agent SAU khi tool đã có đủ flag prompt nhắc tới**; agent gặp lệch phải báo,
không được bịa. (Cũng là lý do `ms=0`: prompt không ép đo giờ → agent không tự chế số.)

## Luật CỐT LÕI (rút từ lần fail 16/07/26)
**Tool KHÔNG BAO GIỜ BỊA BƯỚC.** Bản đầu tự scaffold artifact giả trong `/tmp` rồi vẽ timeline →
user không thấy project đâu, không có luồng thật ⇒ POC vô giá trị (đúng luật "bằng chứng > lời").
Nay mọi bước trong trace đến từ MỘT trong hai nguồn:
- lệnh tool NÀY thực sự chạy (`new`, `probe`), hoặc
- bước agent THỰC SỰ chạy rồi `record` lại (kèm `rc` + log thật).

## Luồng ĐÚNG (user chốt 16/07/26)
```
1) orca repo add + orca WORKTREE create → WORKSPACE hiện ở panel Orca
2) CURL cài overstack từ REMOTE          → đường NGƯỜI MỚI, chứng năng lực travel được
3) nạp CONTEXT: copy tài liệu THẬT       → <workspace>/llmwiki/raw/
4) chạy /br TỪ ĐẦU (interview → auto → compile → slice → run → qc → status)
```

### Bẫy 1 — `repo add` KHÔNG đủ (bài học 17/07/26)
`orca repo add` chỉ đăng ký repo (hiện ở `orca repo list`). Panel **Workspaces** liệt kê **worktree**
→ thiếu `orca worktree create` thì **user KHÔNG THẤY project** ⇒ POC fail. Layout khớp Orca:
repo ở `~/orca/<name>/<name>`, workspace ở `~/orca/workspaces/<name>/<wt>`.

### Bẫy 2 — `curl` KHÔNG mang skill của nhánh canary
`install.sh:230` **hardcode** `npx -y skills add rheinmir/setup#orca --global --all` — KHÔNG có
`SKILLS_REF` override. Nên: **harness** tới từ `--ref` bạn chọn, nhưng **skill LUÔN tới từ nhánh `orca`**.
⇒ Skill MỚI ở nhánh canary **chưa tới tay user** qua đường remote cho tới khi merge vào `orca`.
Đây đúng lớp lỗi *"hardcode tên nhánh"* mà `/fdk-uat` pha-2 sinh ra để bắt. POC ghi cảnh báo này
vào log bước curl thay vì im lặng giả xanh.
```bash
# bước 1–3 (tool chạy thật, ghi 3 bước vào trace)
python3 fdk/tools/fdk-poc.py new --raw "<dir tài liệu>" [--name <proj>] [--ref <nhánh>] [--dest ~/orca/workspaces]

# bước 4: agent chạy /br THẬT, ghi lại từng bước
python3 fdk/tools/fdk-poc.py record --project <p> --cmd "/br interview" --rc 0 --log-file <out> --llm \
        --sentinel "br/spec-filled.md:provenance"

# render trang visualize từ trace THẬT
python3 fdk/tools/fdk-poc.py render --project <p>

# soi một /br project CÓ SẴN bằng tool thật (không scaffold)
python3 fdk/tools/fdk-poc.py probe --project br/payroll [--fresh]
```
`--ref` trỏ nhánh remote cho `curl` (mặc định `orca`; canary thì đưa tên nhánh — `bootstrap.sh` nhận
`HARNESS_BASE`). `--skip-curl` CHỈ dùng khi offline/self-test — bỏ nó là bỏ mất phần chứng minh.

## LUỒNG INJECT GÌ ở mỗi bước (câu hỏi user 17/07/26: "muốn coi 1 luồng phải inject những gì")
Không phải "đồ đi bùa" — mỗi bước có **input xác định** và **artifact ra**, xem được bằng lệnh thật:

| Bước | INJECT vào | RA | Xem bằng |
|---|---|---|---|
| `/br interview` | `llmwiki/raw/*` (tài liệu THẬT) + `skills/br/assets/spec-template.md` (khung S1–S10) | `br/spec-filled.md` — mỗi field có `status` + `provenance: raw:<file>` | đọc file |
| `/br auto` | `skills/br/assets/defaults.yaml` (registry) + `br/defaults.yaml` (project override THẮNG) | điền field `missing` + in **câu hỏi thật** cho field không có default | `br-fill.py fill --root .` |
| `/br compile` | spec-filled + answers | `br/BR.md` (clause_id + bảng "Giả định đang gánh") · `BR.clauses.json` · `br/DESIGN.md` (token KHOÁ) | đọc file |
| `/br slice` | BR.md + `frame-template.md` | frames: `scope_code` (≤3 file) · `scope_test` · `acceptance_test` · `## Spec (FR/SC)` | `frame-lint check` (7 luật) |
| **`/br run`** | **xem dưới** ↓ | code trong scope + `<frame>.run.json` + commit gắn frame_id | **`br-revise.py … --print`** |
| `/br qc` | diff + route mockup | verdict 4 mục + test `qc-*` | `/qc-code` · `/qc-uiux` |
| `/br status` | frames + run-log + BR | `line-status.html` (truy ngược lỗi→frame→clause) | mở HTML |

### `/br run` — chỗ inject QUAN TRỌNG NHẤT (xem được, không phải tin lời)
`fdk/tools/br-revise.py` render prompt rồi gọi `claude -p`. **Placeholder được inject:**
`{{frame_id}}` · `{{clause_ids}}` · `{{muc_tieu}}` · `{{scope_code}}` · `{{scope_test}}` · `{{verify_cmd}}` · `{{verify_output}}`

- **Nguồn prompt, thứ tự ưu tiên:** `br/prompts.md` (**SỔ PROMPT TỔNG — user sửa tay, không cần model**) > queue inline > `prompt_file` > template mặc định `skills/br/assets/revise-prompt.md`.
- **`{{verify_output}}`** = output ĐỎ của vòng trước → **feedback loop thật** (vòng sau biết vì sao fail).
- **Tools bó hẹp:** `--allowedTools Edit,Write,Read,Grep,Glob` — KHÔNG Bash tự do, KHÔNG network.
- **XEM ĐÚNG PROMPT SẼ GỬI, không tốn model:**
  ```
  python3 fdk/tools/br-revise.py run --frame <frame.md> --verify "<cmd>" --print
  ```
  In ra: bối cảnh frame · lệnh nghiệm thu · output đỏ gần nhất · **LUẬT BẤT KHẢ XÂM PHẠM** (chỉ sửa `scope_code`, cấm đụng `scope_test` → test-hash, cấm lệnh phụ/mạng, sửa tối thiểu).

### Ra mockup CHẠY ĐƯỢC ở staging + sửa AGILE (không phải đồ trình diễn)
- **Frame UI phải có `acceptance_test` HIT UI thật** (visual-qa `route-shots.mjs --assert`), không phải unit-test cạnh bên ⇒ frame ĐỎ tới khi route render đúng; chạy lại `/br run` = **tự re-verify UI**.
- **IN-PLACE là mặc định** (feedback 05/07): sửa hiện ngay trong cây đang chạy app → *bật app lên xem liền*. Không đẻ N worktree ma.
- **Vòng agile thật:** thấy lỗi trên app → `/br find <file|từ khoá>` → ra **frame phụ trách + prompt nằm ở đâu** → sửa `br/prompts.md` (tay, 0 token) → `/br run` lại ĐÚNG frame đó (`br-queue.py affected <id>` chỉ chạy lại nhánh của nó).
- **CẤM sửa UI tay ngoài `/br run`** (nợ p28) — sửa tay = mất gate + không re-verify.
- **Không ưng kết quả:** `git revert <commit frame>` (mỗi frame 1 commit gắn `frame_id`) hoặc `checkpoint.py rollback <frame_id>`.

## "Không tất định từ raw thì TRỎ thế nào?"
`/br auto` (`br-fill.py fill`) **không** tất định-từ-raw: nó cần `br/spec-filled.md` có trước, mà file
đó do **LLM đọc .docx** sinh ra. Cơ chế trỏ nằm ở **provenance per-field**:
- mỗi field S1–S10 mang `status: filled|missing|conflict|assumed` + `provenance: raw:<file>|user|lens:<tên>`
  ⇒ field nào cũng **trỏ ngược về đúng tài liệu nguồn** → bước LLM vẫn audit được.
- `br-fill.py fill` chỉ điền field `missing` từ registry defaults (`skills/br/assets/defaults.yaml`,
  project override `br/defaults.yaml` thắng) — phần này TẤT ĐỊNH.
- mọi thứ `assumed` nổi lên bảng **"Giả định đang gánh"** trong BR.md → nhìn một phát biết đang cược gì.
POC vì thế ghi bước interview là `--llm` + log thật + sentinel `br/spec-filled.md:provenance`.

## Đọc kết quả
- **bước THẬT đã chạy** + **sentinel PASS** → luồng thật tạo đủ artifact (không phải khai).
- **LOG mỗi bước** (`rc` + output) → người xem tự chấm, không tin lời model.
- **bước LLM (cam)** là biến; **tất định (tím)** là chi phí harness.

## Rules
- **KHÔNG bịa bước** — không có log thật thì không vào trace.
- **Curl từ remote là bắt buộc** cho POC đầy đủ — cài từ working-tree/`file://` KHÔNG chứng minh năng lực travel (bài học fdk-uat / GH#77).
- **Không khoe "skill tới qua remote" khi chưa kiểm** — `install.sh` hardcode `#orca`; skill có mặt ở global có thể do copy tay. Kiểm nguồn trước khi tuyên bố (bài học 17/07/26).
- **Project phải hiện ở panel Workspaces** (worktree), không chỉ `repo list`.
- **Bước LLM đánh dấu trung thực** (`--llm`), không giả vờ tất định.
- **Project phải THẤY ĐƯỢC** (orca repo add) — POC mà user không mở được project thì fail.
- HTML self-contained + in full-path (R16).

## Related
- `fdk/tools/fdk-poc.py` — new · record · render · probe.
- `~/.claude/skills/fdk-uat` — test nhanh đường remote (xanh/đỏ), tầng TRÊN medic.
- `skills/br/SKILL.md` — vòng đời được demo · `fdk/tools/br-fill.py` — engine `/br auto`.
