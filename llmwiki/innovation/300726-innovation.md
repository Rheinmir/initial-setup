---
title: "Overstack vs thế giới — 30/07/2026"
status: living
tags: [innovation, frontier, comparison, gap-analysis]
timestamp: 2026-07-30
id: innovation-300726
---

# Overstack vs thế giới — rà soát 30/07/2026

Tiếp nối [[innovation-290726]] (1 ngày trước), chạy runbook `fdk/wiki/concepts/frontier-gap-scan.md` — 5 WebSearch cố định theo 5 trục, đối chiếu `fdk/CAPABILITIES.md` (vẫn 84 skill · 18 rule · 19 fdk-tool · 63 harness-script — không đổi so với 3 kỳ liên tiếp) và ledger `llmwiki/wiki/sources/ISSUES.md` (GH#9 và GH#13 vẫn `done`, GH#10/#11/#12 vẫn `open`/`needs-triage`).

**Khác kỳ trước:** kỳ này bỏ qua engine `last30days` (kỳ 29/07 chỉ vớt được 2/10 mục dùng được, quality 3/5 nguồn lõi vì thiếu X/YouTube trên máy này) và chạy thẳng 5 WebSearch theo đúng runbook — nhanh hơn, không vướng lại vụ Python 3.9.6 vs 3.13 đã ghi nhận kỳ trước. `last30days` đã xác nhận **đã cài, `SETUP_COMPLETE=true`**, không cần cài lại — chỉ không phải công cụ tối ưu cho quét diện rộng 5-trục kỳ này.

## Bảng đối chiếu — cột CŨ (overstack đang có) và MỚI (thế giới, tính đến 30/07)

| Trục | 🔵 CŨ — Overstack đang có | 🟢 MỚI — Thế giới (đến 30/07) | Verdict | Nên claim thêm |
|---|---|---|---|---|
| **Filesystem/credential isolation cho agent (nêu 28-29/07, chưa raise issue)** | `egress-guard.py` chặn NETWORK EGRESS ngoài allow-list (PreToolUse, GH#13 done) — không chặn việc agent CẦM/đọc secret trong biến môi trường hay filesystem | **Claude Code (nền tảng đang chạy overstack) vừa tự thêm "new filesystem isolation controls"** trong bản cập nhật 07/2026 (cùng đợt với `--max-budget-usd` và subagent không tự spawn nested subagent) — đây là tín hiệu khác hẳn 1Password/Infisical: chính NỀN TẢNG bên dưới bắt đầu che phần này, không phải bên thứ ba | **Có thể đã một phần Ngang** (cần xác minh, chưa phải Thua rõ như 2 kỳ trước) | Rung thang thấp nhất trước khi tự xây: kiểm 1 dòng xem "filesystem isolation controls" của Claude Code 07/2026 có che được ca agent đọc thẳng `.env`/biến môi trường không — nếu che được, `/raise-issue` credential-gateway kỳ 29/07 đề xuất có thể ĐỔI THÀNH "cấu hình đúng tính năng native" thay vì tự viết credential-broker; nếu KHÔNG che (chỉ cô lập filesystem path, không phải env var), giữ nguyên đề xuất raise issue của kỳ 29/07 |
| **Orchestration scale (GH#12, vẫn `open`, chưa quét lại từ 27/07)** | `orca` đa-agent, `Workflow` tool, quy mô thực tế 3-10 agent song song, chưa có cơ chế index/summary riêng cho agent-card | **Kỹ thuật cụ thể mới xuất hiện: "two-phase agent discovery"** — pha 1 chỉ nạp SUMMARY nhẹ của mọi agent đã đăng ký để model chọn agent liên quan, pha 2 mới nạp FULL agent-card cho agent đã chọn — giải đúng vấn đề "Planner không thể reason trên hàng trăm agent-card đầy đủ cùng lúc" mà DAG Plan&Execute (LangGraph/MS Agent Framework/Google ADK) đang dùng | Thua ở kỹ thuật cụ thể (chưa có tương đương), nhưng khoảng cách hẹp vì overstack mới cần 3-10 agent chứ chưa tới quy mô hàng trăm | Khi `Workflow` tool hoặc `orca-cli` scale quá ~15-20 agent song song, thêm 1 bước index nhẹ (tên + 1 dòng mô tả mỗi agent) TRƯỚC khi giao việc, thay vì nạp full prompt/context của mọi agent ngay từ đầu — tránh nợ kỹ thuật trước khi thật sự cần |
| **Self-improving harness (GH#10, vẫn `open`)** | `failure-flywheel` — weakness-mining thủ công, người-trong-vòng-lặp, cluster lỗi bằng tay | Lil'Log (Lilian Weng, tác giả uy tín cao trong ngành) xuất bản "Harness Engineering for Self-Improvement" (04/07/2026) — hợp thức hoá đúng hướng overstack đã chọn ở cấp học thuật cao nhất. Thêm 1 kỹ thuật cụ thể: **DemoEvolve** (arXiv 2605.24539) — dùng DEMONSTRATION (ví dụ cụ thể) để dẫn dắt tiến hoá harness khi tín hiệu phản hồi (reward) quá thưa, thay vì chỉ dựa reward thưa thớt | Ngang về hướng đi (được hợp thức hoá thêm), Thua về tự-động-hoá bước cluster (không đổi so với kỳ trước) | Khi tự động hoá bước cluster lỗi của `failure-flywheel` (việc GH#10 còn thiếu), dùng đúng ý tưởng DemoEvolve: nuôi cluster bằng các CA SỬA THẬT đã từng chạy (demonstration) làm neo, thay vì chỉ đếm tần suất lỗi giống nhau — giải quyết đúng ca lỗi hiếm/thưa mà đếm tần suất bỏ sót |
| **Skill/MCP supply-chain (GH#13 — đã `done`, nhưng có nguy cơ hạ tầng MỚI)** | `skill-provenance.py` hash sha256 toàn-byte + `egress-guard.py` — bảo vệ tầng SKILL cài vào overstack | Kỳ này lộ rủi ro ở tầng THẤP HƠN skill: **CVE-2026-25253** (RCE trong OpenClaw skill runtime, bị khai thác bởi chiến dịch ClawHavoc — 1.200+ skill độc chèn credential-stealer AMOS) và **lỗ hổng kiến trúc trong chính MCP SDK của Anthropic** (OX Security, ước tính 200.000 server + 150 triệu lượt tải, ≥10 CVE mức Critical) — đây KHÔNG phải lỗ hổng ở skill cài vào mà ở chính giao thức/SDK overstack đang dùng làm nền | Không áp dụng Ngang/Thua (đây là rủi ro tầng hạ-tầng, không phải gap năng lực cạnh tranh) | Chỉ cần xác minh 1 dòng: overstack có gọi trực tiếp MCP SDK của Anthropic ở đường nào (kết nối MCP server ngoài) không, và nếu có, phiên bản SDK đang dùng có nằm trong khoảng bị OX Security nêu không — không cần raise issue nếu chỉ dùng qua Claude Code (bản vá do Anthropic chịu trách nhiệm), raise nếu overstack tự nhúng MCP client/server riêng |
| **Memory (GH#9 — đã `done`)** | `mem-rank.py` 4/4 tầng + write-policy + temporal (`supersedes`) | Xác nhận thêm lần 2 liên tiếp (sau tín hiệu Reddit kỳ 29/07): thế giới giờ chuẩn hoá "memory engineering" thành 4 chiến lược — WRITE / SELECT / COMPRESS / ISOLATE — đúng khung 4 tầng overstack đã chọn, không có kỹ thuật mới lệch hướng | Ngang (xác nhận lần 2, không lệch hướng) | Không claim mới — hướng đã chọn tiếp tục được củng cố, không mở gap |

## Tín hiệu đáng chú ý nhất kỳ này — khác gì với 29/07

**1. Chính nền tảng Claude Code vừa thêm "filesystem isolation controls" (07/2026) — có thể đã che một phần đúng lỗ hổng mà kỳ 29/07 định `/raise-issue` (credential-gateway).** Đây là tín hiệu quan trọng nhất kỳ này vì nó đổi bản chất đề xuất: từ "tự xây thêm lớp" (rung thang cao — viết code mới) sang khả năng "chỉ cần bật/cấu hình đúng tính năng native đã có" (rung thang thấp hơn theo đúng nguyên tắc ponytail — dùng cái nền tảng đã cho trước khi tự viết). Việc TRƯỚC KHI raise issue: xác minh phạm vi thật của tính năng này (chặn đọc path filesystem, hay chặn cả đọc biến môi trường/`.env`?) — chưa xác minh được nên verdict để "có thể đã một phần Ngang" thay vì kết luận chắc.

**2. GH#12 (orchestration scale) được quét lại lần đầu sau 3 kỳ đứng yên (27/07 → 30/07) và tìm ra 1 kỹ thuật cụ thể, nhỏ, áp dụng được ngay khi cần: two-phase agent discovery.** Khác các kỳ trước chỉ có tên framework (LangGraph, MS Agent Framework) mà không có kỹ thuật cụ thể để tham chiếu.

**3. GH#13 (đã đóng) không mở lại, nhưng lộ 1 rủi ro tầng SÂU HƠN skill — chính MCP SDK của Anthropic có lỗ hổng kiến trúc (OX Security).** Đây là điểm khác về LOẠI rủi ro: không phải "skill lạ cài vào overstack" (đã có `skill-provenance` chặn) mà là "giao thức nền overstack đứng trên" — nằm ngoài phạm vi GH#13 nhưng đáng ghi nhận vì quy mô ảnh hưởng công bố (200k server).

**4. GH#10 (self-evolving) được củng cố ở tầng học thuật (Lil'Log) và có thêm 1 kỹ thuật cụ thể cho đúng phần overstack còn thiếu (tự động hoá cluster) — DemoEvolve.**

**5. GH#9 (memory, đã đóng) được xác nhận lần 2 liên tiếp — không mở gap, chỉ củng cố hướng đã chọn.**

## Nên claim thêm gì — tóm tắt ưu tiên

1. **Xác minh phạm vi "filesystem isolation controls" của Claude Code 07/2026 trước khi làm gì khác với đề xuất credential-gateway của kỳ 29/07.** Đây là việc rẻ nhất và ưu tiên cao nhất kỳ này — nếu tính năng native đã che đúng ca lo ngại (agent đọc `.env`/biến môi trường), khỏi cần tự xây credential-broker; nếu không che, giữ nguyên đề xuất `/raise-issue` credential-gateway (đã đủ bằng chứng từ 29/07: 1Password + Infisical + sự cố TeamPCP/LiteLLM).
2. **GH#12 (orchestration scale):** ghi nhận kỹ thuật "two-phase agent discovery" làm tham chiếu cho lúc `Workflow`/`orca-cli` cần scale quá ~15-20 agent song song — chưa cần làm ngay vì quy mô hiện tại (3-10 agent) chưa chạm ngưỡng.
3. **GH#10 (self-evolving, vẫn open):** khi tự động hoá bước cluster của `failure-flywheel`, tham khảo DemoEvolve — dùng ca sửa thật làm demonstration-anchor cho lỗi hiếm/thưa, kết hợp với verifier tách biệt đã nêu ở kỳ 29/07.
4. **Kiểm 1 dòng dependency MCP SDK:** overstack có tự nhúng MCP client/server riêng ngoài Claude Code không — nếu không, bỏ qua rủi ro OX Security (Anthropic tự vá); nếu có, cần theo dõi version.
5. **GH#9 (memory, đã đóng):** không claim mới — chỉ xác nhận hướng cũ đúng lần 2.

## Nguồn

- [Claude AI Gets Yet Another Boost in VS Code 1.128](https://visualstudiomagazine.com/articles/2026/07/08/claude-ai-gets-yet-another-boost-in-vs-code-1-128.aspx)
- [Claude Code Changelog (July 2026)](https://www.gradually.ai/en/changelogs/claude-code/)
- [Claude Updates by Anthropic — July 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude)
- [Claude Code Updates by Anthropic — July 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude-code)
- [Claude Developer Platform Updates by Anthropic — July 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude-developer-platform)
- [Codex and Claude Code in July 2026: Agent Controls Are the Feature](https://www.developersdigest.tech/blog/codex-claude-code-july-agent-controls)
- [Context vs. Memory Engineering in Agentic AI Systems](https://machinelearningmastery.com/context-vs-memory-engineering-in-agentic-ai-systems/)
- [AI Agent Memory 2026: Progress Benchmark Report Evaluations](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- [Context Engineering: Complete 2026 Field Guide](https://www.taskade.com/blog/context-engineering)
- [The 6 Best AI Agent Memory Frameworks You Should Try in 2026](https://machinelearningmastery.com/the-6-best-ai-agent-memory-frameworks-you-should-try-in-2026/)
- [Context Engineering: A Practical Guide for AI Agents (2026) — Sourcegraph](https://sourcegraph.com/blog/context-engineering)
- [Are We Ready For An Agent-Native Memory System? (arXiv 2606.24775)](https://arxiv.org/pdf/2606.24775)
- [Harness Engineering for Self-Improvement — Lil'Log (Lilian Weng)](https://lilianweng.github.io/posts/2026-07-04-harness/)
- [Self-Harness: AI Agents That Autonomously Improve Their Own Framework](https://explainx.ai/blog/self-harness-agents-improve-themselves-arxiv-2026)
- [GitHub - ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering)
- [AutoAgent: Self-Improving AI Agents Explained (2026)](https://decodethefuture.org/en/autoagent-self-improving-ai-agents-meta-harness/)
- [DemoEvolve: Overcoming Sparse Feedback in Agentic Harness Evolution with Demonstrations (arXiv 2605.24539)](https://arxiv.org/pdf/2605.24539)
- [How self-improving harnesses are rewriting the agent engineering playbook — TechTalks](https://bdtechtalks.com/2026/07/13/ai-agents-self-improving-harness/)
- [SIA: Self Improving AI with Harness & Weight Updates (arXiv 2605.27276)](https://arxiv.org/abs/2605.27276)
- [Formal Analysis and Supply Chain Security for Agentic AI Skills (arXiv 2603.00195)](https://arxiv.org/html/2603.00195v1)
- [Skill Issues: How We Discovered Supply Chain Attack Vectors in an AI Agent Skills Marketplace — Orca Security](https://orca.security/resources/blog/ai-agent-skill-supply-chain-security/)
- [OpenClaw's Skill Marketplace and the Emerging AI Supply Chain Threat — Unit42](https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/)
- [When AI Becomes the Attack Surface: Emerging Supply Chain Risks in Skills Marketplaces — Unite.AI](https://www.unite.ai/ai-agent-skills-supply-chain-security-vulnerabilities/)
- [We Spent 20 Years Securing the Supply Chain. AI Agents Just Reset the Clock to Zero](https://www.secureworld.io/industry-news/securing-software-supply-chain-ai-agents)
- [How AI agents upend software supply chain security — ReversingLabs](https://www.reversinglabs.com/blog/how-ai-agents-upend-sscs)
- [AI Agent Security Risks 2026: MCP, OpenClaw & Supply Chain](https://blog.cyberdesserts.com/ai-agent-security-risks/)
- [Multi-Agent Orchestration: 5 Patterns That Work in 2026](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work)
- [How to Orchestrate Multi-Agent AI Systems at Scale in 2026 — Atlan](https://atlan.com/know/multi-agent-system-orchestration/)
- [Autonomous Event-Driven Multi-Agent Orchestration for Enterprise AI at Scale (arXiv 2606.20058)](https://arxiv.org/pdf/2606.20058)
- [AI Agent Orchestration in 2026: Enterprise Guide to Multi-Agent Systems](https://viston.tech/ai-agent-orchestration-in-2026-moving-from-pilots-to-enterprise-wide-execution/)
