---
title: "Overstack vs thế giới — 29/07/2026"
status: living
tags: [innovation, frontier, comparison, gap-analysis]
timestamp: 2026-07-29
id: innovation-290726
---

# Overstack vs thế giới — rà soát 29/07/2026

Tiếp nối [[innovation-280726]] (1 ngày trước), chạy đúng runbook `fdk/wiki/concepts/frontier-gap-scan.md` — 5 WebSearch cố định theo 5 trục, đối chiếu `fdk/CAPABILITIES.md` (84 skill · 18 rule · 19 fdk-tool · 63 harness-script — không đổi so với kỳ trước) và ledger `llmwiki/wiki/sources/ISSUES.md` (GH#9 và GH#13 vẫn `done`, GH#10/#11/#12 vẫn `open`/`needs-triage`, chưa có issue nào tên "credential" trong ledger).

**Khác kỳ trước:** lần này chạy thẳng engine `last30days` qua Bash (bỏ qua modal wizard vì `SETUP_COMPLETE=true` đã có sẵn từ kỳ 28/07) thay vì đi lại toàn bộ luồng cài đặt. Gặp 1 trục trặc môi trường: `python3` mặc định trên máy là 3.9.6 (< yêu cầu 3.12+ của engine v3), phải chuyển sang `python3.13` (đã có sẵn, không cần cài mới) — ghi lại để lần sau không mất thời gian dò lại. Chạy `--auto-resolve --quick` (bỏ qua wizard tương tác đầy đủ vì WebSearch đã chạy độc lập song song) cho chủ đề `AI coding agent framework harness self-improving skills`: 10 mục (6 Hacker News, 4 Reddit), quality 3/5 nguồn lõi (thiếu X/Twitter, YouTube). Xác nhận lại đúng nhận định 2 kỳ trước — tín hiệu hẹp nhưng lần này có 2 mục dùng được trực tiếp cho bảng dưới (Observal, "Most self-improving AI agents don't improve"), khác các kỳ trước hầu như chỉ vớt được 1 mục hoặc toàn meme.

## Bảng đối chiếu — cột CŨ (overstack đang có) và MỚI (thế giới, tính đến 29/07)

| Trục | 🔵 CŨ — Overstack đang có | 🟢 MỚI — Thế giới (đến 29/07) | Verdict | Nên claim thêm |
|---|---|---|---|---|
| **Credential isolation cho agent (GH#9-13 chưa có issue riêng — trục nêu lần đầu 28/07)** | `egress-guard.py` chặn NETWORK EGRESS ngoài allow-list (wired PreToolUse, GH#13 done) — agent vẫn CÓ thể đọc thẳng biến môi trường/`.env` chứa credential thật nếu tool đọc được | **Leo thang mạnh so với 28/07** (khi đó chỉ có 1 tín hiệu — Show HN OneCLI): giờ có cả một THỊ TRƯỜNG đặt tên "credential brokering" — **1Password Credential Broker** (private beta từ 15/06/2026, GA cuối 2026), **Infisical Agent Vault** (OSS, HTTP proxy+vault cho Claude Code/OpenClaw/Hermes), SANS Institute đặt tên vấn đề là "confused deputy" (agent giữ credential nhiều dịch vụ cộng dồn thành blast-radius không service-account nào được thiết kế để có), và 1 sự cố thật đã xảy ra: **campaign TeamPCP (03/2026) đã compromise LiteLLM** (AI gateway proxy hàng nghìn doanh nghiệp dùng để route LLM request) | **Thua, và khoảng cách đang NỚI RỘNG chứ không hẹp lại** | Đây không còn là 1 ý tưởng lẻ (OneCLI) mà là category đã có ≥3 sản phẩm cụ thể (1Password, Infisical, credential-gateway) + 1 sự cố thật xác nhận rủi ro. Đủ chín để `/raise-issue` ngay kỳ này thay vì "cân nhắc" như 28/07: agent chạy Bash trong `orca-workflow` hiện đọc thẳng được `.env`/biến môi trường (RTK, SCRAPECREATORS_API_KEY,...) — `egress-guard.py` chỉ chặn NƠI ĐI, không chặn việc CẦM secret. Việc cụ thể: khảo sát pattern Infisical Agent Vault (OSS, gần nhất với quy mô overstack) trước khi tự thiết kế, không cần chờ thêm bằng chứng |
| **Observability runtime (GH#11, vẫn `open`/`needs-triage`)** | `wikieval`, `medic eval`, `trace-grader` — tĩnh/CI, không có tracing lúc chạy | Tên cụ thể mới xuất hiện qua `last30days` (Show HN, 22 điểm, 21/07/2026): **Observal — "OSS Cross-Harness self hosted registry and analytics for AI Agents"** (`github.com/Observal/Observal`) — đúng object GH#11 đang thiếu (registry+analytics tự-host, đa-harness) | Thua, nhưng lần đầu có 1 REPO CỤ THỂ để tham chiếu thay vì chỉ tên hãng lớn (Galileo/future-agi) | GH#11 không đổi hướng, nhưng nên thêm `Observal` vào phần tham khảo của issue — là OSS, tự-host, quy mô gần overstack hơn Galileo Agent Control (SaaS doanh nghiệp), đáng xem trước khi tự thiết kế lược đồ registry/analytics |
| **Self-improving harness (GH#10, vẫn `open`)** | `failure-flywheel` — weakness-mining thủ công, người-trong-vòng-lặp | Số đo Terminal-Bench 2.0 không đổi so với 28/07 (Self-Harness +33% đến +60%), nhưng `last30days` vớt thêm 1 tín hiệu HOÀI NGHI đáng cân bằng: bài "**Most 'self-improving' AI agents don't improve**" (Substack, loadbearingtech) lập luận phần lớn triển khai "self-improving" thực chất KHÔNG cải thiện — thiếu verifier độc lập đáng tin nên vòng lặp tự-khen | Thua (chưa đổi hướng ưu tiên), nhưng thêm 1 RỦI RO THIẾT KẾ cần né | Không đổi kết luận GH#10 (đi đúng kiến trúc, thiếu tự động hoá cluster). NHƯNG khi tự động hoá bước cluster của `failure-flywheel`, tránh đúng bẫy bài báo nêu: đừng để chính LLM vừa sinh sửa vừa tự chấm sửa đó tốt — cần verifier tách biệt (giống bước "Proposal Validation" của Self-Harness), không tự-khen |
| **Skill supply-chain (GH#13 — đã `done`)** | `skill-provenance.py` hash sha256 toàn-byte + `egress-guard.py` chặn egress runtime | Không có tin đảo chiều mới so với 28/07 (GuardFall, Claude Code Action bị đầu độc, bypass scanner hàng loạt vẫn là tin gần nhất) | Ngang (đã đóng, miễn nhiễm cấu trúc với bypass padding — ghi nhận từ 28/07, không đổi) | Không claim mới — giữ nguyên như 28/07 |
| **Orchestration scale (GH#12, vẫn `open`)** | `orca` đa-agent, `Workflow` tool, quy mô 3-10 agent | Không quét lại trục này kỳ này (đã có 2 tên tham chiếu từ 27/07: Google ADK 2.0 graph-execution, Microsoft MAF) | Không đổi — cần tái-kiểm kỳ sau | Không claim mới kỳ này |
| **Memory (GH#9 — đã `done`)** | `mem-rank.py` 4/4 tầng + write-policy + temporal (`supersedes`) | Reddit post vớt qua `last30days` (r/MervinPraison, "Self-Learning AI Agents: Model, Harness, and Context Layers") mô tả kiến trúc: route bài học vào harness+context (KHÔNG phải model weight), phân loại semantic/episodic/procedural, scope theo user/team/app — **đúng khung 4 tầng overstack đã có** | Ngang (xác nhận, không lệch hướng) | Không claim mới — tín hiệu này CỦNG CỐ hướng đã chọn (GH#9 done), không mở gap |
| **Nền tảng Claude Code/Anthropic (hạ tầng, không phải gap cạnh tranh)** | `orca-workflow`/`Agent` tool đứng trên Claude Code hiện tại | 2 thay đổi API mới công bố 07/2026: `agent-memory-2026-07-22` beta header (memory listing trả thứ tự ổn định, cursor chặt hơn); MCP spec `2026-07-28` (stateless core, OAuth/OIDC mạnh hơn) | Cần xác minh (thay đổi hạ tầng, không phải thắng/thua) | Chỉ ghi nhận — nếu overstack có tích hợp MCP tuỳ biến hoặc gọi memory API trực tiếp, kiểm 1 dòng xem có phụ thuộc behavior cũ không. Không cần raise issue nếu không đụng tới các API này |

## Tín hiệu đáng chú ý nhất kỳ này — khác gì với 28/07

**1. Credential-gateway không còn là 1 ý tưởng lẻ (OneCLI) — đã thành category có thị trường thật, đủ chín để raise issue ngay, không cần chờ thêm.** 28/07 chỉ có 1 Show HN 109 điểm. Hôm nay tìm thấy: 1Password (private beta từ 1 công ty lớn, tín hiệu "đủ nghiêm túc để hãng lớn đầu tư"), Infisical Agent Vault (OSS, tham chiếu gần quy mô nhất), và quan trọng nhất — **1 sự cố supply-chain THẬT đã xảy ra** (TeamPCP compromise LiteLLM, 03/2026) chứng minh rủi ro không phải giả thuyết. Đây là điểm khác biệt định tính: hôm qua là "nên cân nhắc xem xét", hôm nay là "có bằng chứng đủ để hành động".

**2. `last30days` chạy engine thật lần đầu cho trục này (28/07 chỉ vớt được 1 mục qua ScrapeCreators/HN, hôm nay 10 mục) và trả về đúng 1 repo tham chiếu cụ thể cho GH#11 (Observal) — khác các kỳ trước chỉ có tên hãng SaaS lớn không cùng quy mô.** Xác nhận lại: công cụ này vẫn cho tín hiệu mỏng với chủ đề B2B hẹp (3/5 nguồn lõi, thiếu X/YouTube — không có XAI_API_KEY/yt-dlp trên máy này), nhưng KHÁC 2 kỳ trước ở chỗ tỷ lệ hữu ích cao hơn hẳn (2/10 mục dùng được thay vì 1/10).

**3. Phát hiện 1 rủi ro thiết kế cho chính GH#10 (self-evolving skill) từ bài phê bình "Most self-improving AI agents don't improve":** khi tự động hoá bước cluster của `failure-flywheel`, cần verifier TÁCH BIỆT khỏi vòng sinh-sửa, tránh vòng lặp tự-khen không có cơ sở — bài học áp dụng trực tiếp vào lúc thiết kế, không phải lúc chấm điểm sau.

**4. Trục Memory (GH#9, đã đóng) được CỦNG CỐ thêm bởi 1 bài kiến trúc độc lập mô tả đúng khung 4 tầng overstack đã chọn — không mở gap mới, chỉ xác nhận hướng cũ đúng.**

**5. Gỡ 1 trục trặc môi trường cho lần chạy `last30days` sau: máy này cần `python3.13` (không phải `python3` mặc định 3.9.6) để chạy engine v3 — ghi lại tránh dò lại từ đầu.**

## Nên claim thêm gì — tóm tắt ưu tiên

1. **Credential-gateway/broker cho agent — nâng cấp từ "cân nhắc" (28/07) lên "nên `/raise-issue` ngay":** bằng chứng đã đủ (3 sản phẩm cụ thể + 1 sự cố thật TeamPCP/LiteLLM). Việc cụ thể: khảo sát Infisical Agent Vault (OSS, HTTP proxy+vault) trước khi tự thiết kế lớp bổ sung cho `egress-guard.py` — bổ sung, không thay thế (egress-guard = "đi đâu", credential-gateway = "cầm gì").
2. **GH#11 (observability, vẫn open):** thêm `Observal` (github.com/Observal/Observal) làm tham chiếu OSS gần quy mô overstack hơn Galileo/future-agi khi thiết kế registry+analytics.
3. **GH#10 (self-evolving skill, vẫn open):** khi tự động hoá bước cluster của `failure-flywheel`, thiết kế verifier tách biệt khỏi vòng sinh-sửa — né đúng bẫy "tự-khen không cơ sở" mà bài phê bình nêu.
4. **GH#12 (orchestration scale) và GH#9 (memory, đã đóng):** không claim mới kỳ này — GH#12 chưa quét lại, GH#9 chỉ được củng cố thêm không đổi hướng.
5. **Hạ tầng Claude Code (agent-memory-2026-07-22, MCP 2026-07-28):** chỉ ghi nhận, kiểm nhanh nếu overstack có tích hợp trực tiếp các API này — không phải gap cạnh tranh.

## Nguồn

- [Claude AI Gets Yet Another Boost in VS Code 1.128](https://visualstudiomagazine.com/articles/2026/07/08/claude-ai-gets-yet-another-boost-in-vs-code-1-128.aspx)
- [Claude Code Changelog (July 2026)](https://www.gradually.ai/en/changelogs/claude-code/)
- [Claude Developer Platform Updates by Anthropic — July 2026](https://releasebot.io/updates/anthropic/claude-developer-platform)
- [Claude Code Updates by Anthropic — July 2026](https://releasebot.io/updates/anthropic/claude-code)
- [Codex and Claude Code in July 2026: Agent Controls Are the Feature](https://www.developersdigest.tech/blog/codex-claude-code-july-agent-controls)
- [AI Agent Memory 2026: Progress Benchmark Report Evaluations](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- [Context Engineering: Complete 2026 Field Guide](https://www.taskade.com/blog/context-engineering)
- [Are We Ready For An Agent-Native Memory System? (arXiv 2606.24775)](https://arxiv.org/pdf/2606.24775)
- [Self-Harness: AI Agents That Autonomously Improve Their Own Framework](https://explainx.ai/blog/self-harness-agents-improve-themselves-arxiv-2026)
- [AutoAgent: Self-Improving AI Agents Explained (2026)](https://decodethefuture.org/en/autoagent-self-improving-ai-agents-meta-harness/)
- [SIA: Self Improving AI with Harness & Weight Updates (arXiv 2605.27276)](https://arxiv.org/abs/2605.27276)
- [Researchers introduce Self-Harness — VentureBeat](https://venturebeat.com/orchestration/researchers-introduce-self-harness-a-framework-that-lets-ai-agents-rewrite-their-own-rules-boosting-performance-up-to-60)
- [We Spent 20 Years Securing the Supply Chain. AI Agents Just Reset the Clock to Zero](https://www.secureworld.io/industry-news/securing-software-supply-chain-ai-agents)
- [Microsoft at Black Hat USA 2026: Defending trust in the age of AI and supply chain attacks](https://www.microsoft.com/en-us/security/blog/2026/07/17/microsoft-at-black-hat-usa-2026-defending-trust-in-the-age-of-ai-and-supply-chain-attacks/)
- [Skill Issues: Supply Chain Attack Vectors in an AI Agent Skills Marketplace — Orca Security](https://orca.security/resources/blog/ai-agent-skill-supply-chain-security/)
- [OpenClaw's Skill Marketplace and the Emerging AI Supply Chain Threat — Unit42](https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/)
- [Your AI Agent Is an Easily Confused Deputy: Why Cloud Security Needs a Credential Broker — SANS Institute](https://www.sans.org/blog/your-ai-agent-easily-confused-deputy-why-cloud-security-needs-credential-broker)
- [Introducing 1Password Credential Broker](https://1password.com/blog/introducing-1password-credential-broker)
- [1Password debuts Credential Broker to release secrets only when needed — SiliconANGLE](https://siliconangle.com/2026/06/15/1password-debuts-credential-broker-release-secrets-needed/)
- [Credential Brokering for AI Agents, Explained — Infisical](https://infisical.com/blog/credential-brokering-for-ai-agents)
- [GitHub - Infisical/agent-vault](https://github.com/Infisical/agent-vault)
- [Put a Credential Boundary Between AI Coding Agents and Secrets](https://vibesecadvisory.com/blog/credential-boundary-ai-coding-agents/)
- [Show HN: Stele – A self-maintaining knowledge graph for AI coding agents](https://stele-ai.dev/) (via `/last30days`, Hacker News)
- [Show HN: OSS Cross-Harness self hosted registry and analytics for AI Agents (Observal)](https://github.com/Observal/Observal) (via `/last30days`, Hacker News)
- [Most "self-improving" AI agents don't improve](https://loadbearingtech.substack.com/p/self-improving-agent-loops-verifier) (via `/last30days`, Hacker News)
- [Self-Learning AI Agents: Model, Harness, and Context Layers for Compounding Products](https://www.reddit.com/r/MervinPraison/comments/1url0dp/selflearning_ai_agents_model_harness_and_context/) (via `/last30days`, Reddit)
