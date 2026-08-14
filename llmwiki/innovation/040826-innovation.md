---
title: "Overstack vs thế giới — 04/08/2026"
status: living
tags: [innovation, frontier, comparison, gap-analysis]
timestamp: 2026-08-04
id: innovation-040826
---

# Overstack vs thế giới — rà soát 04/08/2026

Tiếp nối [[innovation-030826]] (1 ngày trước). Trước khi quét, xác nhận lại `last30days`: `SETUP_COMPLETE=true` đã có sẵn (không mất cài đặt lần nữa như sự cố 03/08), nhưng máy chỉ có Python 3.9.6 làm mặc định — dùng `python3.14` (đã có sẵn trên máy) làm interpreter thay vì cài lại gì. `--diagnose` xác nhận 5 nguồn sống: Reddit, YouTube, Hacker News, Polymarket, GitHub (X/Twitter vẫn thiếu vì chưa đăng nhập cookie trình duyệt). Đối chiếu `fdk/CAPABILITIES.md`: vẫn **84 skill · 18 rule · 19 fdk-tool · 63 harness-script** — không đổi 6 kỳ liên tiếp (27/07 → 04/08). Ledger `ISSUES.md`: GH#9 và GH#13 vẫn `done`, GH#10/GH#11/GH#12 vẫn `open`/`needs-triage` — không có tín hiệu mới đủ mạnh để quét lại GH#10 (self-evolving skills) hay GH#11 (observability runtime) kỳ này, nên hai trục đó **không** xuất hiện trong bảng dưới (tránh bịa dữ liệu khi không có bằng chứng mới).

Kỳ này chạy `last30days` với 1 plan 3-subquery tập trung vào chủ đề Claude Code subagent/skills/memory + so sánh Cursor/Codex CLI/Cline/Aider + multi-agent orchestration mới, cộng 2 WebSearch bổ sung (changelog Claude Code 08/2026, và tổng quan xu hướng agent-coding-tool 2026). Kết quả nổi lên một trục **hoàn toàn mới, chưa từng được theo dõi trong `ISSUES.md`**: cộng đồng đang hội tụ về một lớp "adapter phổ quát" để một cấu hình/skill chạy được xuyên nhiều coding agent (Claude Code, Cursor, Codex, Aider, Cline, Windsurf...), điều mà overstack hiện chưa có gì tương đương.

## Bảng đối chiếu — cột CŨ (overstack đang có) và MỚI (thế giới, tính đến 04/08)

| Trục | 🔵 CŨ — Overstack đang có | 🟢 MỚI — Thế giới (đến 04/08) | Verdict | Nên claim thêm |
|---|---|---|---|---|
| **Cross-agent portability (trục MỚI — chưa có issue theo dõi)** | Skill overstack (`SKILL.md`, `/<tên>`, hook harness) viết riêng cho Claude Code — không có lớp tương thích để chạy trên Cursor/Codex/Aider/Cline; muốn dùng framework ở CLI khác phải viết lại từ đầu | Bốn tín hiệu độc lập cùng hướng trong 30 ngày qua: **TierDecay** (score 38, GitHub) — công cụ gán role→model, vừa mở rộng thành 7 adapter (Claude Code native, chuẩn phổ quát `AGENTS.md` cho Codex/Cursor/OpenCode/Copilot/Zed, Gemini CLI, Aider, **thêm Cline, Goose, Windsurf**); một PR "cross-AI session handoff protocol" (score 37) ràng cùng một ngữ cảnh repo-canonical (`/AI`) cho 8 hệ (Codex/AGENTS, Claude Code, Gemini CLI, Copilot, Cursor, Windsurf, Cline, Roo Code); **headroom** (score 32) — wrapper hợp nhất ngữ cảnh cho 15+ coding agent; **EGC** (score 31) — chia sẻ memory + skills + context sống giữa Cursor, Claude Code, Copilot, Aider và 20+ tool. `AGENTS.md` đang nổi lên như chuẩn de-facto trung gian | **Thua rõ — trục mới, chưa có gì tương đương** | Thấp nhất trước khi tự xây (đúng nguyên tắc cái thang): xét khả năng sinh một file `AGENTS.md` TỐI GIẢN từ `fdk/CAPABILITIES.md` (đã sinh-bằng-code, luôn-mới) — không viết lại core skill, chỉ thêm 1 bước export ánh xạ danh sách skill/rule sang định dạng chuẩn phổ quát, để framework mở được đối tượng dùng ở CLI khác mà không phải port từng skill |
| **Orchestration scale (GH#12, `open`, quét lại lần 4 sau 27/07→31/07→03/08)** | `orca`/`Workflow` tool: coordinator pattern, pipeline/parallel, 3-10 agent song song; ghi nhận từ 30/07: "subagent không tự spawn nested subagent" từng là giới hạn nền tảng | Đúng nền tảng Claude Code (nơi overstack chạy trên) vừa đổi 2 điều liên quan trực tiếp: (1) **subagent giờ chạy nền mặc định + tự spawn nested subagent tới độ sâu 3** (trước là 1) — giới hạn ghi nhận 30/07 **không còn đúng**; (2) ra mắt **Agent Teams** — orchestrator đa-agent tích hợp sẵn, một session "team lead" điều phối qua **shared task list**, mỗi "teammate" chạy context window riêng — đang **thử nghiệm, tắt mặc định** | **Constraint cũ (không nested-spawn) đã lỗi thời — cần rà lại giả định trong code/docs**; pattern orchestration của overstack (coordinator + task dispatch) khá gần với Agent Teams native, nhưng Agent Teams còn tắt mặc định nên chưa phải áp lực cấp bách | (1) Rà `Workflow`/`orca-cli`/wiki xem còn chỗ nào giả định "subagent không tự spawn" — nếu depth-3 mở khả năng mới (vd fan-out lồng nhau sâu hơn trong `pipeline()`), cân nhắc tận dụng thay vì chỉ ghi nhận thụ động. (2) Khi Anthropic bật Agent Teams mặc định, so lại 1 lần cụ thể: "team lead + shared task list" của họ có phần nào trùng `orchestration`/`orca-workflow` không — tránh trùng 2 hệ điều phối chồng lên nhau trên cùng nền tảng |
| **Model-routing theo tác vụ (xác nhận vị trí, không phải gap)** | `Workflow` tool đã có `opts.model` override PER-AGENT-CALL — mỗi bước trong pipeline/parallel có thể chỉ định model riêng (model đắt để lên kế hoạch, model rẻ để thực thi song song) | Xu hướng "software dev đang chuyển từ viết code sang điều phối agent viết code" đi kèm khuyến nghị cụ thể: **gán model theo từng tác vụ thay vì chọn 1 model cho cả pipeline** — model đắt lập kế hoạch, model rẻ thực thi song song | **Ngang — overstack đã có cơ chế đúng hướng này** (không cần claim thêm, chỉ xác nhận) | Không cần việc mới. Ghi nhận để lần sau nếu ai hỏi "overstack có hỗ trợ multi-model routing không" thì trả lời có, qua `Workflow`'s `opts.model`/`opts.effort` — tránh xây trùng |

## Tín hiệu đáng chú ý nhất kỳ này — khác gì với 03/08

**1. Một trục hoàn toàn mới xuất hiện, không nằm trong 5 trục `ISSUES.md` đang theo dõi: cross-agent portability qua `AGENTS.md`.** Đây là phát hiện quan trọng nhất kỳ này. Bốn dự án độc lập (TierDecay, cross-AI handoff PR, headroom, EGC) cùng hội tụ về một điểm trong 30 ngày qua — không phải một tín hiệu đơn lẻ dễ nhiễu. Overstack hiện là framework Claude-Code-only; nếu `AGENTS.md` tiếp tục trở thành chuẩn trung gian thực sự (không chỉ trào lưu ngắn hạn), đây sẽ là khoảng cách rộng dần nếu không theo dõi.

**2. Constraint nền tảng ghi nhận từ 30/07 ("subagent không tự spawn nested subagent") đã bị chính Claude Code lật ngược trong bản cập nhật 08/2026** — giờ mặc định chạy nền + nested tới độ sâu 3. Đây là loại thay đổi cần rà lại giả định cũ trong code/docs overstack, không chỉ ghi nhận rồi bỏ qua.

**3. Agent Teams (team-lead + shared task list) là tín hiệu native-catch-up rõ nhất từ trước đến nay cho GH#12** — gần với đúng pattern `orchestration`/`orca-workflow` đã chọn, nhưng còn tắt mặc định nên chưa cần hành động ngay, chỉ cần theo dõi thời điểm bật mặc định.

**4. Model-routing theo tác vụ — kỳ đầu tiên xác nhận overstack KHÔNG có gap ở trục này** nhờ `opts.model`/`opts.effort` đã có sẵn trong `Workflow` tool; đáng ghi lại để tránh sau này tưởng nhầm là thiếu.

## Nên claim thêm gì — tóm tắt ưu tiên

1. **Trục mới ưu tiên cao nhất: cross-agent portability.** Xét khả năng sinh 1 file `AGENTS.md` tối giản từ `fdk/CAPABILITIES.md` (đã sinh-bằng-code sẵn) — bước rẻ, không đụng core skill, chỉ export ánh xạ. Cân nhắc `/raise-issue` nếu quét lại kỳ sau vẫn thấy tín hiệu hội tụ (2+ dự án độc lập nữa) thay vì hành động ngay từ 1 kỳ quan sát.
2. **GH#12 (orchestration scale):** rà lại mọi chỗ trong code/docs còn giả định "subagent không tự spawn" — giả định này đã lỗi thời kể từ bản cập nhật nested-depth-3 của Claude Code 08/2026.
3. **GH#12 (theo dõi thụ động):** khi Agent Teams (team-lead + shared task list) của Anthropic chuyển từ thử nghiệm sang mặc định, so lại với `orchestration`/`orca-workflow` một lần cụ thể để tránh 2 hệ điều phối chồng nhau.
4. **Không cần việc mới:** model-routing theo tác vụ đã có (`opts.model`/`opts.effort`) — chỉ cần nhớ để trả lời đúng khi so sánh với thế giới, không phải xây thêm.
5. **GH#9, GH#13 (đã đóng), GH#10, GH#11:** không quét lại kỳ này — không đủ bằng chứng mới trong phạm vi 3 truy vấn đã chạy để cập nhật.

## Nguồn

- `python3.14 ~/.claude/skills/last30days/scripts/last30days.py "AI coding agent frameworks and multi-agent orchestration" --plan <3-subquery>` (v3.18.4, chạy 04/08/2026) — Reddit 14 threads, YouTube 1 video, HN 7 stories, GitHub 8 items
- [Adapters wanted: bring TierDecay to your AI coding CLI](https://github.com/alebgl77/tierdecay/issues/1)
- [Add cross-AI session handoff protocol](https://github.com/ingolf-lohmann/qik-vrt/pull/12)
- [Expand beyond Claude Code: support other agents' transcripts (headroom)](https://github.com/manavgup/context-analyzer/issues/80)
- [feat: remove AI coding agent config files before arXiv submission](https://github.com/google-research/arxiv-latex-cleaner/pull/130)
- [AI Agent Radar 日报 · 2026-07-25 (EGC)](https://github.com/apiiskan/ai-agent-radar/issues/6)
- [Claude Code Changelog (August 2026) — gradually.ai](https://www.gradually.ai/en/changelogs/claude-code/)
- [Code with Claude 2026: 5 New Agent Features Anthropic Just Shipped — MindStudio](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)
- [Multi-agent orchestration for Claude Code in 2026 — Shipyard](https://shipyard.build/blog/claude-code-multi-agent/)
- [Claude Code Agent Teams, Subagents, and MCP: The 2026 Playbook — Developers Digest](https://www.developersdigest.tech/blog/claude-code-agent-teams-subagents-2026)
- [Claude Code subagents: the 2026 production playbook — Totalum](https://www.totalum.app/blog/claude-code-subagents-totalum)
- [Agentic Coding Tools Compared (2026): Claude Code vs Cursor vs Codex vs Aider — Requesty](https://www.requesty.ai/blog/agentic-coding-tools-compared-2026-claude-code-cursor-codex-aider)
- [AI Coding Agents 2026: The State of Play — CLI, IDE, and Cloud Agents Compared — niteagent](https://niteagent.com/blog/2026-05-21-ai-coding-agents-state-of-play/)
