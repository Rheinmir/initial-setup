---
title: "Overstack vs thế giới — 05/08/2026"
status: living
tags: [innovation, frontier, comparison, gap-analysis]
timestamp: 2026-08-05
id: innovation-050826
---

# Overstack vs thế giới — rà soát 05/08/2026

Tiếp nối [[innovation-040826]] (1 ngày trước). Trước khi quét, phát hiện `last30days` cài **thiếu**: chỉ có `SKILL.md` (127K), không có thư mục `scripts/` chứa engine Python — lệnh gọi ra "No such file". Đã sửa bằng cách clone repo nguồn (`github.com/mvanhorn/last30days-skill`) và copy trọn bộ `scripts/` + `references/` + `agents/` + `SKILL.md` bản mới nhất (v3.18.4, thay cho bản cũ v3.3.2 đang cài) vào `~/.claude/skills/last30days/`. `--diagnose` xác nhận sau khi sửa: 6 nguồn sống (Reddit, YouTube, Hacker News, Polymarket, GitHub, grounding — X/Twitter vẫn thiếu vì chưa đăng nhập cookie trình duyệt). Đối chiếu `fdk/CAPABILITIES.md`: vẫn **84 skill · 18 rule · 19 fdk-tool · 63 harness-script** — không đổi 7 kỳ liên tiếp (27/07 → 05/08).

Kỳ này chạy engine `last30days` với 1 plan 3-subquery (skill marketplace/self-evolving, orchestration, memory) — thu về 51 evidence item (GitHub 18, HN 24, Reddit 8, YouTube 1) — cộng 3 WebSearch bổ sung: (1) theo dõi tiếp trục AGENTS.md từ 040826, (2) self-evolving skills — bám GH#10, (3) trạng thái Agent Teams — bám GH#12. Kết quả: trục **cross-agent portability** mà 040826 gắn nhãn "trục mới, 4 tín hiệu hội tụ, còn early" nay đã có bằng chứng mạnh hơn hẳn — không còn là trào lưu, mà là chuẩn được một foundation trung lập tiếp quản với số liệu đo được cụ thể. Ngoài ra phát hiện 2 dự án GitHub mới trong 30 ngày (`OpenLore`, `Codeman`) chạm trực tiếp vào GH#11 (observability/guardrails) và một khoảng trống chưa từng ghi nhận (mission-control dashboard cho nhiều CLI agent cùng lúc).

## Bảng đối chiếu — cột CŨ (overstack đang có) và MỚI (thế giới, tính đến 05/08)

| Trục | 🔵 CŨ — Overstack đang có | 🟢 MỚI — Thế giới (đến 05/08) | Verdict | Nên claim thêm |
|---|---|---|---|---|
| **Cross-agent portability (leo thang từ 040826)** | Skill overstack (`SKILL.md`, `/<tên>`, hook harness) viết riêng cho Claude Code, không có lớp tương thích Cursor/Codex/Aider/Cline | AGENTS.md — ra mắt bởi OpenAI 08/2025, đã chuyển giao cho **Agentic AI Foundation (AAIF) thuộc Linux Foundation** cuối 2025 cùng MCP (Anthropic) và Goose (Block); tính đến 05/2026 AAIF có **170+ tổ chức thành viên**, AGENTS.md được **60.000+ repo** áp dụng. Song song có định dạng **SKILL.md** — một thư mục portable (SKILL.md + script/reference/asset tuỳ chọn) chạy được trên Claude Code, Codex, Copilot và các agent tương thích khác; 6/8 agent phổ biến nay đọc SKILL.md trực tiếp — điều 6 tháng trước chưa đúng. Một nghiên cứu (Gloaguen et al. 2026, 138 repo thật) đo được: AGENTS.md viết tay nâng tỷ lệ hoàn thành task ~4% và **giảm 35–55% bug do agent sinh ra** | **Thua rõ — không còn là trào lưu để "theo dõi", mà là chuẩn có tổ chức trung lập đứng sau + số liệu đo được cụ thể (không phải overstack tự đo)** | Cấp bách hơn 040826 đánh giá: (1) sinh 1 `AGENTS.md` tối giản từ `fdk/CAPABILITIES.md` (đã sinh-bằng-code sẵn, chỉ thêm bước export ánh xạ) — bậc rẻ nhất của cái thang; (2) đáng giá hơn nữa: vì overstack "skill" đã gần giống hình dạng SKILL.md (thư mục + SKILL.md + script), xét khoảng cách thực giữa 2 định dạng — có thể chỉ cần một shim mỏng, không phải viết lại |
| **Self-evolving skills (GH#10, `open`, quét lại sau im lặng ở 040826)** | `failure-flywheel`: capture-by-code → count deterministic → khi 1 category vượt ngưỡng, sinh STUB draft và **DỪNG chờ người duyệt** (`--draft` không bao giờ tự ghi rule) — vòng tạo/sửa skill vẫn cần người ở bước "distill" | Cụm 5+ paper 2026 mô tả vòng tự-tiến-hoá **không có người ở giữa**: `SkillOpt` (chiến lược tối ưu skill tự động), `MUSE-Autoskill` (tạo→nhớ→quản lý→đánh giá skill hoàn toàn tự động), `SkillForge` (skill tự-tiến-hoá theo domain cho support kỹ thuật), `Skill-MAS` (tiến hoá meta-skill cho multi-agent system), `FederatedSkill`. OpenAI đã phát hành **Self-Evolving Agents Cookbook chính thức** (11/2025) — hướng dẫn tự-chẩn-đoán lỗi agent, đo feedback, dựng vòng self-healing | **Thua — đúng gap đã ghi nhận ở GH#10, nay có bằng chứng world dày hơn hẳn (paper + cookbook chính thức từ OpenAI, không còn là ý tưởng lẻ)** | Overstack đã có ĐÚNG nửa đầu vòng lặp (capture + count + taxonomy, tất định, 0-token) — cái thiếu là nửa sau: "distill" hiện toàn thủ công qua `/propose`. Rẻ nhất: đọc cách `MUSE-Autoskill` tách 4 giai đoạn (creation/memory/management/evaluation) — có thể chỉ cần thêm bước "eval tự động cho stub trước khi tới người duyệt" chứ không phải xây cả vòng auto-merge (giữ nguyên chốt chặn người duyệt cuối — đây là chủ ý, không phải thiếu sót, ghi ở GH#10) |
| **Deterministic local-first memory + guardrails cho coding agent (nhánh cụ thể của GH#11)** | `llmwiki` mem-rank (episodic + temporal, [[framework-multi-session-dev]]) chạy local-first, nhưng KHÔNG có khái niệm "guardrail" tường minh gắn kèm memory — guardrail hiện nằm rải ở harness rule (18 rule), tách rời khỏi tầng nhớ | `OpenLore` (Show HN, 29/07, github.com/clay-good/OpenLore) — dự án mới đóng khung memory VÀ guardrail là MỘT tầng: "deterministic, local-first memory and guardrails for AI coding agents" | **Chớm — overstack có cả 2 mảnh (memory tất định + rule harness) nhưng tách rời, chưa hợp nhất thành 1 tầng như OpenLore đóng khung** | Không cần xây mới — chỉ đáng đọc kỹ cách OpenLore mô tả ranh giới "memory ⟷ guardrail" để xem có khoảng trống thật (vd rule bị vi phạm do agent quên context) mà hợp nhất 2 tầng sẽ vá được, hay chỉ là cách đóng gói khác của cùng 2 thứ overstack đã có |
| **Mission-control dashboard cho NHIỀU CLI agent cùng lúc (trục MỚI, chưa có issue theo dõi, khác GH#8)** | Không có UI persistent theo dõi nhiều agent chạy song song; `orca-cli`/`Workflow` là điều phối qua terminal/tool-call, không có dashboard web sống. GH#8 (`skill-usage-dashboard`, open) gần nhưng khác: đó là báo cáo tần suất dùng skill, không phải màn hình theo dõi agent đang chạy | `Codeman` (r/selfhosted, 03/08, 176 điểm/43 comment, 500+ sao/14 contributor/1.500 commit) — "self-hosted mission control" chạy nhiều AI coding CLI (OpenCode, Claude Code, Codex, Gemini) trong session **bền (persistent)**, theo dõi qua 1 dashboard | **Chớm — trục mới, chưa có issue; KHÁC GH#8 nên không tính là cùng gap** | Thấp — quan sát thêm, chưa raise issue (1 tín hiệu, chưa hội tụ). Nếu Orca hoặc `orca-cli` sau này thêm khả năng xem nhiều session terminal cùng lúc trên 1 màn, đối chiếu lại xem có trùng lặp Codeman hay không trước khi tự xây |

## Tín hiệu đáng chú ý nhất kỳ này — khác gì với 04/08

**1. Trục cross-agent portability đã đổi hạng nghiêm trọng.** 040826 gọi đây là "4 tín hiệu độc lập hội tụ, đáng theo dõi". Hôm nay bằng chứng khác hẳn về chất: không phải 4 dự án cộng đồng nữa, mà là một **chuẩn đã có tổ chức trung lập (Linux Foundation's AAIF) đứng sau, cùng hàng với MCP của chính Anthropic**, với số đo định lượng cụ thể (60.000+ repo, +4% task success, -35–55% bug). Đây không còn là câu hỏi "có nên theo dõi không" mà là "khi nào bắt đầu", vì khoảng cách sẽ ngày càng khó bù nếu để lâu.

**2. GH#10 (self-evolving skills) im lặng ở 040826 nay có tín hiệu mới đáng kể** — không phải 1 dự án lẻ mà một cụm 5 paper học thuật cùng chủ đề trong 30 ngày, cộng cookbook chính thức từ OpenAI. Đáng để `/fdk` nhận việc "đọc kỹ MUSE-Autoskill, xem có phần nào ghép được vào `failure-flywheel` mà không phá chốt chặn người duyệt" — không phải xây lại từ đầu.

**3. Hai dự án GitHub cùng chạm domain overstack đã có sẵn (nhưng KHÔNG tạo gap mới):** `Stele` (self-maintaining knowledge graph cho coding agent, HN 22/07) và `MindFlock` (agent song song mỗi cái 1 git worktree riêng, HN 29/07) — cả hai đều là thứ overstack **đã có**: `wiki-graph.py`/code-graph MCP cho vế đầu, `Workflow` tool's `isolation: 'worktree'` + `orca-cli` worktree cho vế sau. Ghi nhận ở đây để tránh sau này tưởng nhầm là thiếu, không đưa vào bảng vì không phải gap.

**4. Agent Teams (GH#12) — xác nhận KHÔNG đổi so với 040826.** WebSearch riêng cho trục này xác nhận: ra mắt research-preview từ Claude Code v2.1.32 (05/02/2026), tính đến 05/08/2026 **vẫn chưa GA** (một issue GitHub 08/2026 còn báo bug "Agent Teams unavailable... despite flag bật"). Đúng như 040826 đánh giá — chưa cần hành động, chỉ tiếp tục theo dõi thời điểm bật mặc định.

## Nên claim thêm gì — tóm tắt ưu tiên

1. **Cấp bách nhất, nâng hạng so với hôm qua: cross-agent portability.** Bậc rẻ nhất của cái thang — sinh `AGENTS.md` tối giản từ `fdk/CAPABILITIES.md` (đã sinh-bằng-code) — vẫn còn nguyên giá trị, nhưng nay có thêm lý do làm sớm: chuẩn đã có tổ chức trung lập đứng sau nên rủi ro "trào lưu chết yểu" thấp hơn hẳn 040826. Bậc thứ hai đáng xét: so hình dạng skill hiện tại của overstack với SKILL.md chuẩn — nếu gần, một shim mỏng có thể đủ thay vì viết lại.
2. **GH#10 (self-evolving skills):** đọc `MUSE-Autoskill` + cookbook OpenAI, tìm phần "eval tự động cho stub trước người duyệt" có ghép được vào `failure-flywheel` không — giữ nguyên chốt chặn người duyệt cuối (chủ ý thiết kế, không phải thiếu sót).
3. **GH#11 (observability/guardrails), nhánh cụ thể mới:** đọc cách `OpenLore` hợp nhất "memory + guardrail" thành 1 tầng — kiểm xem overstack có khoảng trống thật (rule bị vi phạm do agent quên context) hay chỉ là cách đóng gói khác của 2 thứ đã có.
4. **Trục mới, chưa raise issue (1 tín hiệu, chưa hội tụ):** mission-control dashboard nhiều-CLI-agent kiểu Codeman — quan sát thêm, không hành động ngay.
5. **Không cần việc mới — chỉ ghi nhận đã có:** self-maintaining knowledge graph (Stele ≈ wiki-graph.py/code-graph) và parallel-agent-per-worktree (MindFlock ≈ `Workflow` isolation:'worktree') — tránh xây trùng nếu sau này ai hỏi.
6. **GH#12 (Agent Teams):** không đổi, tiếp tục theo dõi thụ động tới khi GA.

## Nguồn

- `python3.14 ~/.claude/skills/last30days/scripts/last30days.py` (v3.18.4, chạy 05/08/2026, plan 3-subquery: skill-marketplace/self-evolving, orchestration, memory) — Reddit 8 thread, YouTube 1 video, HN 24 story, GitHub 18 item (51 evidence item tổng)
- [Codeman: self-hosted mission control for AI coding agents](https://www.reddit.com/r/selfhosted/comments/1vebymy/codeman_selfhosted_mission_control_for_ai_coding/) — r/selfhosted, 176 điểm
- [Agent teams: named agent definitions and multi-agent orchestration (plank)](https://github.com/aovestdipaperino/plank/issues/19)
- [Show HN: MindFlock – Parallel AI coding agents, each in its own Git worktree](https://github.com/MindFlock/MindFlock)
- [OpenLore: Deterministic, local-first memory and guardrails for AI coding agents](https://github.com/clay-good/OpenLore)
- [Show HN: Stele – A self-maintaining knowledge graph for AI coding agents](https://stele-ai.dev/)
- [LobeHub — Your AI Team, Autonomous & 24/7 | 80K+ Github Stars](https://www.youtube.com/watch?v=qpnZcSJSoWo)
- [AGENTS.md Spec (2026): Recommended Sections + AGENTS.md vs CLAUDE.md vs .cursorrules](https://www.morphllm.com/agents-md-guide)
- [What Is the Agent Skills Open Standard?](https://www.agensi.io/learn/agent-skills-open-standard)
- [Cross-Agent Skills: Portability in 2026 — MCP.Directory](https://mcp.directory/blog/cross-agent-skills-cursor-codex-cline-antigravity-gemini-mastra-portability)
- [Top AI Agent Standards to Know in 2026 — Agentailor](https://blog.agentailor.com/posts/top-ai-agent-standards-2026)
- [Self-Evolving AI Agents: How Memory and Skills Work — Geeky Gadgets](https://www.geeky-gadgets.com/self-evolving-ai-agents-explained/)
- [May 2026 SkillOpt: Executive Strategy for Self-Evolving Agent Skills (arXiv)](https://arxiv.org/pdf/2605.23904)
- [MUSE-Autoskill: Self-Evolving Agents via Skill Creation, Memory, Management, and Evaluation (arXiv)](https://arxiv.org/html/2605.27366v1)
- [SkillForge: Forging Domain-Specific, Self-Evolving Agent Skills in Cloud Technical Support (arXiv)](https://arxiv.org/pdf/2604.08618)
- [[BUG] Agent Teams unavailable in Claude Code on the web despite CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1](https://github.com/anthropics/claude-code/issues/56449)

## Origin
Nối tiếp [[innovation-040826]]. Kích hoạt bởi yêu cầu "cài last30days repo nếu chưa có + đánh giá repo so với ý tưởng mới trên thế giới" (phiên 05/08/2026). Phát hiện phụ: cài `last30days` trước đó bị thiếu `scripts/` (chỉ có SKILL.md) — đã bù bằng cách clone `mvanhorn/last30days-skill` lên bản mới nhất (v3.18.4) và copy đè vào `~/.claude/skills/last30days/`.
