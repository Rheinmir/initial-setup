# Operation Log

## 2026-09-02 — maintenance — vá R3 index-sync + soi duplicate-basename (fdk-gate drift)

`python3 harness/validators/index_sync.py --wiki-dir llmwiki/wiki` báo 18 file thiếu khỏi `wiki/index.md` (8 `sources/*-session-provenance.md` từ 24/07 đến 13/08, 10 `sources/draft/*.md`). Đọc từng file thật (không suy đoán tên/ngày) rồi thêm đúng 18 dòng vào bảng, theo house-style sẵn có: 8 dòng session-provenance khớp khuôn `Auto-distill scratch-log phiên <hash> ngày DD/MM...` (5 dòng `(stub) — chỉ chạm ...` vì chỉ đụng `gitignore`/`entities/repowise.md`, 1 dòng có nội dung thật vì phiên đó soạn draft BIV); 6 dòng `draft` + 4 dòng `issue` khớp khuôn "SPEC ..."/"Issue: ..." đã dùng cho các `sources/draft/*` khác. Validator giờ exit 0.

Soi `python3 harness/validators/duplicate_basename.py --wiki-dir llmwiki/wiki`: `200826-docs-site-macos-mermaid-sidebar-fix.md` trùng basename ở `draft/unknown/` và `sources/draft/`. Diff hai file: **KHÔNG phải bản sao** — `sources/draft/` là SPEC (`type: draft`), `draft/unknown/` là unknown-ledger (`type: unknown-ledger`, khai `source_spec:` trỏ ngược về chính SPEC đó), nội dung hoàn toàn khác nhau. Đối chiếu 2 file unknown-ledger khác cùng thư mục (`unknown-context-hygiene.md`, `unknown-frontend-design.md`) lộ ra quy ước đặt tên: file trong `draft/unknown/` phải mang tiền tố `unknown-<slug>.md`, không được trùng basename với SPEC nguồn — file `200826-...` phá quy ước đó (thiếu tiền tố `unknown-`) nên mới đụng basename. Không xoá/gộp file nào — nội dung khác nhau thật, cần người quyết hướng sửa (nhiều khả năng: đổi tên `draft/unknown/200826-docs-site-macos-mermaid-sidebar-fix.md` → `draft/unknown/unknown-docs-site-macos-mermaid-sidebar-fix.md`), báo lại thay vì tự đoán. `duplicate_basename.py` vẫn đỏ, cố ý để nguyên.

## 2026-09-02 — propose — sessionstart-episodic-recall

Câu hỏi "phần nào đảm bảo agent phiên mới không quên phiên cũ" (phiên này) → grep thật xác nhận: KHÔNG có gì tự động, `session_start.py::orient()` chỉ nhắc chung "đi query đi". Chạy `/last30days "AI agent memory across sessions"` lấy bằng chứng ngoài (Mem0/Zep/Letta, MCP session-continuity servers, Memori paper: selective retrieval rẻ hơn ~20 lần so với auto-inject).

`/propose` T-260902-01: `020926-sessionstart-episodic-recall.md` + companion HTML — 3 approach (A: nudge tất định 1-2 dòng qua lệnh mới `mem-rank.py recent`, KHUYẾN NGHỊ · B: auto-inject đầy đủ kiểu MCP, loại · C: giữ nguyên hiện trạng, loại), chọn A. Không trùng GH#101 (`050826-distill-zero-mem-graph-branch` — cải thiện CHẤT LƯỢNG ranking, trục khác). 2 task: T1 thêm subcommand `recent` vào `mem-rank.py` (tất định, sort theo `ts`, không ranking); T2 wire `episodic_recall()` vào `session_start.py` đúng khuôn fail-open có sẵn. R7 gate xanh. Đang chờ duyệt — chưa code.

## 2026-09-03 — docs-site-macos — memory-retrieval-improvement-summary

Đáp ứng docs-gate R10 (5 prompt thiếu tài liệu). Sinh `llmwiki/html/030926-memory-retrieval-improvement-summary.html` — 3 section (Phát hiện gốc / Nghiên cứu /last30days / Quyết định /propose), mind map 4 nhánh 10 lá, diagram-box kéo-thả cho mỗi section, theme toggle + sidebar collapse. Audit Playwright thật (không chỉ đọc code): 0 lỗi console, round-trip `.nav-close`/`.nav-toggle` đúng, control đổi `data-theme` nằm trong `.theme-row`, cấu trúc 3 section = 3 diagram-box = 3 nav-link khớp. `npm install playwright` chạy nhầm ở gốc repo lúc đầu (lệnh `cd` scratchpad thất bại âm thầm) — phát hiện ngay, dọn sạch, chuyển đúng vào scratchpad trước khi tiếp tục.

## 2026-09-04 — lint — drift-catchup

Neo wiki đứng yên từ 2026-07-20 (`b226621183`), 159 commit / 336 file sau đó → `wiki-sync --check` bung 157 cờ `code-drift`. Không sửa rộng: phân loại trước, 108 cờ rơi vào `sources/`+`draft/` và 37 cờ vào `archive/` — đều là bản ghi theo thời điểm (progression), không đụng. Còn 12 trang LIVE (`concepts/` + `entities/`), rà từng trang bằng `claim-receipts.py --check`.

Kết quả: đúng **1** drift thật — `concepts/problem-tree.md` còn trỏ proposal ở `sources/draft/020726-orca-issue-ledger-travel.md` trong khi file đã được promote lên `sources/`. Contradiction → sửa đè 1 câu. 11 trang còn lại kiểm từng cờ đều KHÔNG phải drift: ref nằm trong khối ví dụ có rào (`a.txt`, `openclaude-usage.json`), đường dẫn repo ngoài (`mattpocock/skills`), câu văn đã tự phân biệt tên file framework vs downstream, hoặc số đo lịch sử ("migrate 82 trang" 2026-07-02).

Đóng kèm 3 drift hạ tầng: regen `overstack.html` (medic `✗ docs` → 0 fail 0 warn 16 ok); khôi phục `llmwiki/commands/serve` bị xoá nhầm ở 1474a88 (hash `e1846847abcedbea` khớp đúng byte template global → xác nhận xoá nhầm chứ không phải retire); ghi lại `.harness-stamp` 1.3.54 → 1.3.65 đúng cách installer làm.

Maintainer duyệt sửa nốt heuristic. Đo ngược "file nào sinh nhiều cờ nhất" cho ra thủ phạm thật, khác giả thuyết ban đầu: không phải việc dữ liệu đổi, mà là needle **basename** trong `map_suspects` — `log.py` khớp 64/240 trang, `scratch-log.jsonl` 58, `ledger.jsonl` 56, `SKILL.md` 42 (tên có ở 85 chỗ trong repo), `serve` 30 (từ tiếng Anh). Sửa: (1) không quét `sources/draft/archive/` + `sources/handover/` — bản ghi lịch sử /lint cấm sửa; (2) basename chỉ làm needle khi có đuôi VÀ khớp ≤ 8 trang. Đo lại đúng neo cũ: **159 → 115 cờ**; 2 cờ LIVE bị gỡ đúng là 2 false positive đã rà tay. Test 8 → 10 assertion, kèm bite-test.

<!-- log:auto:start -->

### 🤖 Log tự-động (code-logger, không do agent ghi)

| Thời điểm | Event | Chi tiết |
|---|---|---|
| 2026-08-20 16:47:31 | `file.write` | llmwiki/html/200826-session-summary-mermaid-sidebar.html · tool=Edit · session=72190e1c · actor=agent · prev=f20318dcc7a |
| 2026-08-20 16:50:41 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=1e42b1ad9b45f8023466b49014316f5e05df |
| 2026-08-20 16:50:41 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=2aedc924b9e0561933ebbe966def9820d88f |
| 2026-08-20 16:51:03 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=d37df70991273fabc0aa0299b63201c58501 |
| 2026-08-20 16:51:03 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=86219564e5016e70436f872b88e3065c285c |
| 2026-08-20 16:52:41 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=69bd47f08ef961c5a2c8b000edfaba003d66 |
| 2026-08-20 16:52:41 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=975ce6988d22b8f1b1c3621ce28988518e77 |
| 2026-08-20 16:54:14 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=eeb667ae76a3850a867bfd2400f7a676853d |
| 2026-08-20 16:54:14 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=a20acaeee733ab4535b7a9aef47735673ead |
| 2026-08-20 16:55:42 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=2 · human=['llmwiki/skills/utils/docs-site-macos.md', 'llmwiki/wiki/log.md'] · pre |
| 2026-08-25 16:42:01 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=dba79064 · actor=agent · prev=9d362ca0ce329e89707e841212e8b27eafc0 |
| 2026-08-25 16:42:01 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=dba79064 · actor=agent · prev=6a1c107e3bf8fb4ff782902f9c25da3c7f4b |
| 2026-08-25 16:42:15 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=dba79064 · actor=agent · prev=edf5b193ac2a43a8b35cd754c491d61bb61f |
| 2026-08-25 16:42:15 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=dba79064 · actor=agent · prev=78c5e8d0375375dc10af170c80cef6c92fc9 |
| 2026-08-25 16:42:33 | `file.write` | skills/docs-site-macos/vendor/README.md · tool=Edit · session=dba79064 · actor=agent · prev=a10b05672245277682f2f521703f |
| 2026-08-25 16:42:33 | `file.write` | skills/docs-site-macos/vendor/README.md · tool=Edit · session=dba79064 · actor=agent · prev=e0e12c389be97732aa470b3d340d |
| 2026-08-25 16:44:33 | `commit.reconcile` |  · actor=system · agent_n=2 · human_n=1 · human=['llmwiki/skills/utils/docs-site-macos.md'] · prev=a90e42b1c8c934ab010ea |
| 2026-09-02 22:23:18 | `task.new` |  · task=T-260902-01 · title=SessionStart episodic recall nudge · state=proposed · actor=agent · prev=b4fbfdc098a5e1db2cd |
| 2026-09-02 22:25:01 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Write · session=dba79064 · actor=agent · prev=1 |
| 2026-09-02 22:25:01 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Write · session=dba79064 · actor=agent · prev=2 |
| 2026-09-02 22:25:09 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Edit · session=dba79064 · actor=agent · prev=aa |
| 2026-09-02 22:25:09 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Edit · session=dba79064 · actor=agent · prev=4a |
| 2026-09-02 22:25:13 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Edit · session=dba79064 · actor=agent · prev=ee |
| 2026-09-02 22:25:13 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Edit · session=dba79064 · actor=agent · prev=bc |
| 2026-09-02 22:26:15 | `file.write` | llmwiki/html/020926-sessionstart-episodic-recall-seq.html · tool=Write · session=dba79064 · actor=agent · prev=4a08f8b28 |
| 2026-09-02 22:26:15 | `file.write` | llmwiki/html/020926-sessionstart-episodic-recall-seq.html · tool=Write · session=dba79064 · actor=agent · prev=54fa86bbb |
| 2026-09-02 22:26:31 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=dba79064 · actor=agent · prev=c4422a6186a7bcc87d8810238fb8c2bb85f924e9329974 |
| 2026-09-02 22:26:31 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=dba79064 · actor=agent · prev=ff038a986a0e63e9595a01ad865570f8ce539b17c7c1d9 |
| 2026-09-02 22:26:49 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=d32daf24fa115e707af8c2d38061c8cfb1b5c3057f338c1a |
| 2026-09-02 22:26:49 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=f6c7d5cdc48e63a13aeb026f3102e1c81921df1e4228f6c0 |
| 2026-09-03 20:15:40 | `file.write` | llmwiki/html/030926-memory-retrieval-improvement-summary.html · tool=Write · session=dba79064 · actor=agent · prev=55a5d |
| 2026-09-03 20:15:40 | `file.write` | llmwiki/html/030926-memory-retrieval-improvement-summary.html · tool=Write · session=dba79064 · actor=agent · prev=d2fcf |
| 2026-09-03 20:17:30 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=dba79064 · actor=agent · prev=c065e6312d6230dd552d37fd235f2c7aa78d01c40f0819 |
| 2026-09-03 20:17:30 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=dba79064 · actor=agent · prev=e93ca9b3fd848b64b13af9be67bf1207e0700c619a0ee3 |
| 2026-09-03 20:17:38 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=8b33279b91cf3035e7559fa08ee87adb345c628d76c5b575 |
| 2026-09-03 20:17:38 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=a90b22aff1ec5fb7d215fa43c82428f61078fac478f9b2fc |
| 2026-09-04 09:11:37 | `file.write` | harness/scripts/wiki-sync.py · tool=Edit · session=3e970e77 · actor=agent · prev=01e00cc7e1eba30d0aab65482e0c796dd732cfc |
| 2026-09-04 09:11:37 | `file.write` | harness/scripts/wiki-sync.py · tool=Edit · session=3e970e77 · actor=agent · prev=99341691ce6394f752acb8a141f296bf0e8411b |
| 2026-09-04 09:11:53 | `file.write` | harness/scripts/wiki-sync.py · tool=Edit · session=3e970e77 · actor=agent · prev=f91c12fbf75fbedeaa09215e5c006fc439b4e77 |
| 2026-09-04 09:11:53 | `file.write` | harness/scripts/wiki-sync.py · tool=Edit · session=3e970e77 · actor=agent · prev=60c00ca6158856fc2de0ccba12fa11f8b5d4af1 |

<!-- log:auto:end -->
