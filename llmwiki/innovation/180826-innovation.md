---
title: "Overstack vs thế giới — 18/08/2026: sandbox cách ly, agent teams, receipt xác minh"
status: living
tags: [innovation, frontier, comparison, gap-analysis, last30days]
timestamp: 2026-08-18
id: innovation-180826
---

# Overstack vs thế giới — rà soát 18/08/2026

Tiếp nối [[innovation-170826]] (17/08, quét chủ đề chung lần trước: risk-score trước-khi-hỏi, skill supply-chain atomic-install, agent trust, RAG-vs-context-window, LangGraph, SKILL.md open-standard, license/SPDX). Kỳ này chạy 3 truy vấn `last30days` mới, tránh trùng chủ đề đã quét: (1) "AI agent context window compaction memory management", (2) "AI coding agent subagent orchestration parallel workflow", (3) "AI agent skill marketplace discovery trust verification". Nguồn thật = GitHub/Hacker News/Reddit/YouTube (không có API key social nên X/TikTok thiếu, YouTube fallback đôi khi lẫn video cũ hơn 30 ngày). Đối chiếu với `fdk/CAPABILITIES.md` (skill/tool đang có) và `llmwiki/wiki/sources/ISSUES.md` (GH#12, GH#71, GH#72, GH#102 vẫn đang mở, xác nhận qua grep trực tiếp) để tránh claim trùng.

## Bảng đối chiếu

| Trục | 🔵 Overstack đang có | 🟢 Ý tưởng mới thế giới (30 ngày qua) | Verdict |
|---|---|---|---|
| **Sandbox cách ly cho hành động agent** | `orca-cli` worktree isolation (cô lập theo file/nhánh git) + `EnterWorktree`; Bash tool có cờ `dangerouslyDisableSandbox` nhưng không có lớp container dùng-1-lần mặc định cho lệnh rủi ro | Docker chính thức ra mắt *"Docker Sandboxes — Disposable, isolated sandboxes for AI agents"* (HN, 693 điểm/396 bình luận, 2026-08-10); song song, *"Never Trust Your AI Agent's Own Sandbox"* (HN, 2026-08-12) cảnh báo: sandbox phải do BÊN NGOÀI agent dựng và xác minh, không dựa vào agent tự khai báo | **Thua — gap mới.** Worktree cô lập file/git, không cô lập process/network/filesystem toàn hệ như container; nguyên tắc "không tin sandbox agent tự dựng" đáng đưa vào trước khi bật `dangerouslyDisableSandbox` |
| **Multi-agent fan-out có cấu trúc (pipeline/parallel)** | `Workflow` tool: `pipeline()`/`parallel()`, gom theo `phase()`, budget-aware scaling, cache-resume theo `runId` | *"Claude Code Dynamic Workflows Clearly Explained"* (Nate Herk, 107k views, 2026-05-30) mô tả CHÍNH XÁC cùng cơ chế: 41 agent Haiku chấm điểm song song → 1 agent Opus tổng hợp, chạy vì "agents are working in parallel" | **Ngang/đi trước.** Đây là tính năng native cùng hãng mà video mô tả trùng khớp cơ chế `Workflow` đang dùng — không phải gap, là xác nhận hướng đầu tư đúng, không cần đổi |
| **Multi-agent "đội" ngang hàng thấy nhau real-time** | `orchestration` skill: coordinator dispatch task-DAG, blocking ask/reply, worker báo về coordinator (mô hình hub-and-spoke một chiều) | *"Claude Code's Agent Teams Are Insane"* (Cole Medin, 148k views, 2026-02-09): tính năng Agent Teams của Anthropic — nhiều instance Claude Code cùng thấy nhau, làm việc song song thật (ví dụ 16 agent cùng viết một C compiler, có lead agent + backend/frontend/db agent riêng) | **Cần kiểm tra — chưa xác định.** Chưa rõ `orchestration` skill có mô phỏng được peer-visibility (agent thấy tiến độ agent khác trực tiếp) hay chỉ coordinator-dispatch một chiều; cần xác nhận trước khi kết luận đây là gap thật hay đã tương đương |
| **Chứng nhận verify ĐÃ THẬT chạy (chống agent tự khai láo)** | GH#71 (eval-blinding), GH#72 (anti-fabrication số đo bịa), GH#102 (behavioral-integrity mô tả≠hành-vi) đang mở; `medic`/`verify-before-commit` chạy gate thật nhưng không phát hành receipt độc lập kiểm được sau này | *"ProofRun — a local verification receipt for AI coding agents"* (HN, 2026-08-16, tín hiệu còn mỏng — 5 điểm) — ý tưởng: mỗi lần agent tự nhận "đã verify", sinh một receipt tất định (hash lệnh+output+timestamp) để audit sau này không phải tin lời agent | **Thua nhẹ — củng cố ưu tiên GH#71/72/102.** Không phải gap mới về bài toán (3 issue đã mở đúng hướng), nhưng ProofRun gợi ý CƠ CHẾ cụ thể (receipt hash tất định) mà 3 issue kia chưa có thiết kế chi tiết |

## Nên claim thêm (ưu tiên theo effort, thấp→cao)

1. **Receipt tất định cho mỗi lần chạy gate** (rẻ nhất — không hạ tầng mới, chỉ thêm bước ghi hash sau khi `medic`/`verify-before-commit` chạy xong: hash(lệnh + output + timestamp) vào file audit-log). Đây là input thiết kế cụ thể cho GH#71/GH#72/GH#102, không phải issue mới.
2. **Nguyên tắc "không tin sandbox agent tự dựng"** — trước khi agent tự đề xuất bật `dangerouslyDisableSandbox`, cân nhắc yêu cầu xác nhận từ layer NGOÀI agent (người, hoặc policy tất định), không chỉ dựa vào agent tự báo "tôi đang chạy an toàn."
3. **Container/disposable sandbox cho lệnh Bash rủi ro** (effort vừa — có thể là tuỳ chọn dùng Docker khi lệnh không thể chạy trực tiếp an toàn trên máy user, thay vì chỉ hỏi-người).
4. **Làm rõ orchestration skill: coordinator-dispatch hay peer-visibility** (effort cao nhất — cần đọc kỹ `skills/orchestrate/orchestration.md` và có thể thử nghiệm thật trước khi kết luận có nên raise issue GH mới về "agent teams ngang hàng" hay không).

Không raise GH issue tự động trong phiên này — theo `/raise-issue`, đây là hành động công khai cần user xác nhận trước. 4 mục trên sẵn sàng làm input nếu user muốn mở.

## Nguồn
- HN: "Docker Sandboxes – Disposable, isolated sandboxes for AI agents" — https://www.docker.com/products/docker-sandboxes/ (2026-08-10, 693pts/396cmt)
- HN: "Never Trust Your AI Agent's Own Sandbox" — https://badshah.io/blog/never-trust-your-ai-agents-sandbox/ (2026-08-12)
- HN: "ProofRun – a local verification receipt for AI coding agents" — https://github.com/yebiguo/ProofRun (2026-08-16, 5pts)
- YouTube (Nate Herk | AI Automation): "Claude Code Dynamic Workflows Clearly Explained" — https://www.youtube.com/watch?v=jZgcWCzxh1I (2026-05-30, 107,961 views)
- YouTube (Cole Medin): "Claude Code's Agent Teams Are Insane" — https://www.youtube.com/watch?v=-1K_ZWDKpU0 (2026-02-09, 148,352 views)
- YouTube (Burke Holland): "After This Video, You'll Actually Understand Agent Orchestration" — https://www.youtube.com/watch?v=-BhfcPseWFQ (2026-02-10, 144,615 views)
- YouTube (Claude): "Context Management in Claude Code" — https://www.youtube.com/watch?v=eW3oTyfeWZ0 (2026-05-18)
- Đối chiếu nội bộ: `fdk/CAPABILITIES.md`, `llmwiki/wiki/sources/ISSUES.md` (GH#12, GH#71, GH#72, GH#102 — xác nhận vẫn `open` qua grep trực tiếp), `skills/orchestrate/orchestration.md`

## Origin
Kích hoạt bởi yêu cầu trực tiếp của user (phiên 2026-08-18): "cài last30days repo nếu chưa có" + "đánh giá những gì repo của chúng ta làm được so với các ý tưởng mới trên thế giới ... ra 1 file /llmwiki/innovation/ddmmyy-innovation.md, so sánh phải có dạng cột trực quan cái cũ mới cái mới". `last30days` đã cài sẵn tại `skills/last30days/scripts/last30days.py` (không cần cài mới) — xác nhận bằng `find`; chỉ cần Python 3.12+ (`/opt/homebrew/bin/python3.13`, python3 mặc định máy là 3.9.6 không đủ, kiểm chứng lại giống phiên 17/08). Chạy engine trực tiếp (không dùng `--plan`) vì cả 3 chủ đề đều là khái niệm chung (concept), không phải named-entity, nên bỏ qua bước resolve X-handle/GitHub-user theo đúng luật skip của chính SKILL.md. Không có API key social (`SCRAPECREATORS_API_KEY`/`XAI_API_KEY`/...) nên nguồn thật giới hạn ở Reddit/HackerNews/GitHub/YouTube.
