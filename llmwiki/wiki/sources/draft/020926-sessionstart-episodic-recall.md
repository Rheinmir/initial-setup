---
type: draft
title: "020926-sessionstart-episodic-recall — nudge tất định 1-2 dòng ở SessionStart, không auto-inject"
status: proposed
tags: [memory, retrieval, session-start, mem-rank, episodic, opt-in, output-report]
timestamp: 2026-09-02
task: T-260902-01
relations:
  - {rel: derives-from, to: log-model}
  - {rel: touches, path: llmwiki/.claude/hooks/session_start.py}
  - {rel: touches, path: harness/scripts/mem-rank.py}
  - {rel: related-to, to: 050826-distill-zero-mem-graph-branch}
---

# 020926-sessionstart-episodic-recall

**Status:** proposed · **Proposed:** 2026-09-02 · **Task:** T-260902-01

## Context
Phiên hội thoại vừa xác nhận bằng grep thật (không phải suy đoán): `session_start.py::orient()` (dòng 110-157) — hook duy nhất chạy đầu MỌI phiên — chỉ in một dòng NHẮC "project có wiki/code-index/CAPABILITIES, đi query đi", **không tự đọc nội dung nào**. Recall thật (đọc lại phiên cũ) chỉ xảy ra khi agent chủ động gõ `/query`, `/record-episode`, hay `/wiki-room` — grep xác nhận không hook nào khác gọi `mem-rank.py retrieve`. Đây là quyết định thiết kế có chủ ý (`fdk/wiki/sources/adr/ADR-004-framework-dev-context-opt-in.md` + `fdk/wiki/sources/adr/ADR-009-session-orientation-autoindex-forcequery.md`): không auto-bơm ký ức vào mọi phiên, tránh nặng/nhiễu — cùng logic vừa áp dụng khi tách `/graph-mode` ra khỏi CLAUDE.md (commit `41ed323`, phiên này).

Nghiên cứu `/last30days "AI agent memory across sessions"` (phiên này, raw lưu tại `~/Documents/Last30Days/ai-agent-memory-across-sessions-raw-v3.md`) xác nhận bằng chứng ngoài: selective/opt-in retrieval đo được rẻ hơn auto-inject-toàn-bộ tới 20 lần (Memori paper, arXiv 2603.19935: 1,294 token/response chọn-lọc so với 26,031 token/response full-context) — đúng hướng ADR-004/009 đã chọn, không phải hướng MCP "auto context injection" (Claude Session Continuity MCP) mà một số server 2026 đang làm.

`harness/scripts/mem-rank.py` đã có sẵn tầng episodic (`episode`/`retrieve --kind-filter episode`), tất định, 0-LLM (`_overlap()` token-overlap; embedding chỉ bật khi config `verified: true`) — hạ tầng đã đủ, chỉ thiếu READ tự động ở đúng một điểm: đầu phiên. `[[050826-distill-zero-mem-graph-branch]]` (GH#101, open) là issue KHÁC — cải thiện CHẤT LƯỢNG ranking (thêm nhánh entity-graph/NER), không đụng tới việc `retrieve()` có được TỰ GỌI hay không. Hai trục độc lập, không trùng phạm vi.

## Global constraints
- ADR-004 (nguyên văn, `llmwiki/CLAUDE.md`): "thứ gì auto-fire/tự-bơm context vào MỌI phiên (hook SessionStart/UserPromptSubmit, dòng auto-load) chỉ được phục vụ *dự án hiện tại*; context *nội-bộ-framework* (FDK, inventory, runbook sửa rule) phải **opt-in** qua skill gọi chủ động."
- Mọi hàm mới trong `session_start.py` phải **fail-open tuyệt đối** — quy ước lặp lại ở docstring MỌI hàm hiện có trong file (`harness_integrity`, `wiki_drift`, `orient`, `wikigraph_reminder`): thiếu file / JSON hỏng / lỗi bất kỳ → im lặng, không bao giờ làm gãy phiên.
- `mem-rank.py` docstring (nguyên văn): "The token-overlap ranker + store + ops are deterministic, built now. The embedding scorer is the quarantined unknown" — giữ đúng tinh thần 0-LLM, không đổi.

## Non-goals
- KHÔNG xây nhánh entity-graph/NER cho `retrieve()` — đó là phạm vi `[[050826-distill-zero-mem-graph-branch]]` (GH#101), issue riêng đã mở, không trùng.
- KHÔNG auto-inject toàn bộ nội dung episode/wiki vào context — chỉ 1-2 dòng tóm tắt.
- KHÔNG đổi thuật toán ranking hiện có của `retrieve()`.
- KHÔNG thay wiki làm nguồn chân lý — nudge chỉ trỏ về, không thay thế `/query`.
- KHÔNG thêm cờ cấu hình mới (`.env`, config yaml) — tái dùng đúng pattern "im lặng khi thiếu file" đã có ở mọi hàm khác trong `session_start.py`.

## Approaches

**A — Nudge tất định 1-2 dòng tại SessionStart, đọc episode gần nhất qua lệnh MỚI `mem-rank.py recent` (KHUYẾN NGHỊ).**
`mem-rank.py` thêm subcommand `recent --k N --kind episode` — trả về N record MỚI NHẤT theo `ts` (sort thời gian thuần, KHÔNG cần query text vì đầu phiên chưa có chủ đề để rank theo relevance). `session_start.py` gọi lệnh này, in tối đa 2 dòng ("phiên trước: {did}, chạm {N} file") + gợi ý `/query`/`/wiki-room` nếu muốn sâu hơn. Chi phí: 1 subprocess tất định + ≤200 ký tự stdout. Đúng tinh thần ADR-004 (không auto-bơm nội-bộ-framework) vì đây là project-relevant, giống `orient()`/`wiki_drift()` đã làm.
*Tradeoff:* thêm 1 lệnh mới vào `mem-rank.py` (diện tích code nhỏ, ~15 dòng), và nudge dựa trên "gần nhất theo thời gian" chứ chưa phải "liên quan nhất theo ngữ nghĩa" (đó là việc của `retrieve()` khi agent chủ động hỏi).

**B — Auto-inject đầy đủ nội dung phiên trước (kiểu MCP "Claude Session Continuity", auto context injection).**
Session mới tự động nạp toàn bộ episode + file-touch gần nhất vào context. *Bị loại:* ngược hẳn ADR-004/009 (đã chốt "không auto-bơm mọi phiên"), và chính nghiên cứu `/last30days` vừa chạy đo được auto-inject tốn gấp ~20 lần token so với retrieval chọn lọc (Memori paper) — đây là hướng đã bị cộng đồng 2026 khuyến cáo tránh, không phải hướng nên đi.

**C — Giữ nguyên hiện trạng (chỉ `orient()` nhắc chung "có wiki, đi query đi").**
*Bị loại:* không đóng được khoảng trống thật mà phiên hội thoại này phát hiện — agent phiên mới vẫn "lơ ngơ" y hệt vấn đề gốc của ADR-009 nếu không chủ động gõ lệnh; một dòng nhắc chung chung không đủ, cần nudge có NỘI DUNG cụ thể (dù ngắn).

**Chọn: A.** Rẻ nhất, tất định, không đụng ADR-004, không trùng GH#101, đóng đúng khoảng trống đã xác nhận bằng grep.

## Plan
- [ ] **T1** — `harness/scripts/mem-rank.py`: thêm subcommand `recent --k N (default 1) --kind K (default episode)` — đọc store, lọc theo `kind`, sort theo `ts` giảm dần, trả N record đầu (JSON hoặc text tuỳ `--json`). Tất định, không gọi `_embed()`/`_overlap()` (không cần ranking, chỉ cần mới-nhất). Self-test: thêm case vào `--self-test` hiện có — add 3 episode, `recent --k 1` phải trả đúng episode có `ts` lớn nhất.
- [ ] **T2** — `llmwiki/.claude/hooks/session_start.py`: thêm hàm `episodic_recall(root)` theo đúng khuôn `wiki_drift()`/`wikigraph_reminder()` (try/except bọc toàn bộ, fail-open tuyệt đối) — gọi `mem-rank.py recent --k 1 --kind episode --json`, nếu có kết quả thì in `"🧵 [recall] Phiên trước: {did} (chạm {N} file) — /query hoặc /wiki-room để đào sâu."`, nếu không có store/episode nào thì im lặng. Gọi hàm này trong `main()` cùng nhóm với `wiki_drift`/`wikigraph_reminder` (trước early-exit template-manifest, để downstream cũng nhận).

## Requirements (FR)
- **FR-001**: Hệ thống PHẢI in một nudge ngắn (≤2 dòng, ≤200 ký tự) ở đầu mỗi phiên tóm tắt episode gần nhất, khi `harness/metrics/memory.jsonl` của project hiện tại có ít nhất 1 record kind=episode.
- **FR-002**: `episodic_recall()` PHẢI fail-open tuyệt đối — thiếu file/JSON hỏng/subprocess lỗi/timeout → im lặng, exit 0, không raise ra ngoài.
- **FR-003**: Nudge KHÔNG được chứa toàn văn nội dung episode — chỉ `did` (tóm tắt 1 câu đã có sẵn trong record) + số file chạm, không dump `files`/`outcome` đầy đủ.
- **FR-004**: `mem-rank.py recent` PHẢI tất định — sort theo `ts` thuần, không gọi LLM, không network, không phụ thuộc `_embed()`.

## Success criteria (SC)
- **SC-001**: Ghi 1 episode giả bằng `mem-rank.py episode "..."`, mở phiên Claude Code mới trong project đó, hỏi ngay "phiên trước làm gì" mà KHÔNG gõ lệnh nào trước — agent trả lời đúng chủ đề (`did`) chỉ từ nudge đã hiện, không cần tool-call thêm. (Bằng chứng: SessionStart output có dòng `🧵 [recall]`.)
- **SC-002**: Chi phí thêm mỗi phiên đo bằng `wc -c` trên dòng nudge ≤ 200 ký tự — giữ đúng khác biệt với Approach B (auto-inject).
- **SC-003**: Project KHÔNG có `memory.jsonl` (chưa từng dùng mem-rank) → không có dòng nào thêm vào SessionStart output, không lỗi, không cảnh báo thừa.

## Assumptions
- **(default)** K=1 episode gần nhất hiển thị mặc định — giữ nudge ngắn nhất; nâng K nếu sau này thấy 1 dòng chưa đủ, không cần đợi hỏi trước vì đây là tham số vô hại, dễ đổi.
- **(default)** Không thêm cờ bật/tắt riêng trong `.env`/config — tái dùng đúng cơ chế "im lặng khi thiếu dữ liệu" mọi hàm khác trong `session_start.py` đã dùng (project chưa có `memory.jsonl` = tự động không hiện, không cần cờ).
- **(default)** `recent` không lọc theo project — vì `memory.jsonl` vốn đã là file per-project (`harness/metrics/`, không phải global), nên mọi record trong đó mặc định thuộc đúng project hiện tại.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 | CLAUDE | Sửa engine lõi (`mem-rank.py`, ranking/store logic) — cần hiểu đúng contract `_read()`/`_write_all()`/kind-filter đã có, rủi ro cao nếu giao CLI rẻ đọc nhầm store format | pending |
| T2 | CLAUDE | Wire vào hook `session_start.py` — phải khớp đúng khuôn fail-open + gọi đúng chỗ trong `main()`, cùng lớp rủi ro với T1 (đụng hook chạy MỌI phiên) | pending |

**Sequence diagram**: [020926-sessionstart-episodic-recall-seq.html](../../../html/020926-sessionstart-episodic-recall-seq.html)

## Self-review
1. **Phủ yêu cầu** — "cải thiện truy hồi dữ liệu, chọn hướng nào" → cả 2 task (T1 lệnh đọc mới, T2 wire vào SessionStart) cùng trả lời đúng 1 yêu cầu: đóng khoảng trống "agent phiên mới không tự nhớ". Không có yêu cầu nào bị bỏ sót.
2. **Quét placeholder** — đã rà toàn draft, không còn cụm bỏ-lửng kiểu "để sau"/"chưa nghĩ tới"/"giống task trước" nào; mọi mục đều có giá trị cụ thể.
3. **Nhất quán tên-kiểu** — `episodic_recall()`, `mem-rank.py recent`, nudge prefix `🧵 [recall]` dùng thống nhất giữa Plan/FR/SC/HTML companion.

## Notes
- [[log-model]] — bản đồ 5 sổ độc lập; `mem-rank.py` là sổ "phiên trước đã làm gì" (episodic), đề xuất này chỉ thêm READ tự động, không thêm sổ mới.
- [[050826-distill-zero-mem-graph-branch]] — GH#101, cải thiện CHẤT LƯỢNG ranking (entity-graph), trục khác, không trùng phạm vi với đề xuất này.
- ADR liên quan: `ADR-004-framework-dev-context-opt-in`, `ADR-009-session-orientation-autoindex-forcequery` (cả hai ở `fdk/wiki/sources/adr/`).

## Origin
- **Draft:** `wiki/sources/draft/020926-sessionstart-episodic-recall.md`
- **Nguồn:** phiên hội thoại 2026-09-02 — câu hỏi "phần nào trong src code đảm bảo agent phiên mới không quên phiên cũ" → xác nhận bằng grep thật là KHÔNG có; `/last30days "AI agent memory across sessions"` cùng phiên cho bằng chứng ngoài (Memori paper, MCP session-continuity servers) để chọn hướng A thay vì B.
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
