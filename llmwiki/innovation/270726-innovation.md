---
title: "Overstack vs thế giới — 27/07/2026"
status: living
tags: [innovation, frontier, comparison, gap-analysis]
timestamp: 2026-07-27
id: innovation-270726
---

# Overstack vs thế giới — rà soát 27/07/2026

Tiếp nối [[innovation-240726]] (3 ngày trước), chạy đúng runbook `fdk/wiki/concepts/frontier-gap-scan.md` — 5 WebSearch cố định theo 5 trục, đối chiếu `fdk/CAPABILITIES.md` (84 skill · 18 rule · 19 fdk-tool · **63** harness-script — tăng 1 script so với kỳ trước) và ledger `llmwiki/wiki/sources/ISSUES.md` (GH#9–13 vẫn `needs-triage`/`open`, chưa ai nhận).

Trước khi quét, đã kiểm tra `~/.claude/skills/last30days/` — v3.3.2 cài sẵn, không cần cài lại. Skill này tối ưu cho tín hiệu mạng xã hội tiêu dùng (Reddit/X/TikTok), không khớp chủ đề kỹ thuật của bản rà này nên vẫn dùng WebSearch trực tiếp, đúng phương pháp 2 kỳ trước.

## Bảng đối chiếu — cột CŨ (overstack đang có) và MỚI (thế giới, tính đến 27/07)

| Trục | 🔵 CŨ — Overstack đang có | 🟢 MỚI — Thế giới (đến 27/07) | Verdict | Nên claim thêm |
|---|---|---|---|---|
| **Harness / model nền** | `medic`, `loop-runner`, 18 rule cắn cứng; orca dùng 1 model cấu hình sẵn cho toàn phiên | Claude Opus 5 lên mặc định + **per-subagent model/effort field** (mỗi subagent tự chọn model/effort khác nhau trong cùng 1 phiên), VS Code 1.128 thêm multi-chat trong 1 session (so-sánh song song, branch từ 1 turn cũ) | Thua nhẹ (mới) | overstack chưa có khái niệm "1 subagent = 1 model/effort riêng" — Agent tool đã có tham số `model`/`effort` per-call nhưng orca-workflow của user chưa khai thác chọn effort khác nhau theo độ khó từng subtask. Đáng thử nghiệm, chưa cần raise issue riêng |
| **Orchestration scale (GH#12, đang Chớm)** | `orca` orchestration đa-agent, `/orchestration` cho DAG/blocking-ask, quy mô nhỏ | Thị trường 2026 đã phân tầng rõ 3 tier theo số agent (3-10 / 10-50 / 50+): tier thấp có tên cụ thể — Conductor, Vibe Kanban, Gastown, Claude Squad, Antigravity, Cursor Background Agents. Alibaba công bố "Agent Native Cloud" (18/07) với AgentTeams + sandbox riêng cho hạ tầng orchestration | Thua (không đổi, giờ có bản đồ thị trường rõ hơn) | GH#12 giờ có việc cụ thể để làm: xác định orca đang ở tier nào (rõ ràng là tier thấp, 3-10 agent) và có nên tham khảo pattern của 1 trong 6 tool cùng tier (VD Claude Squad — cùng dùng Claude Code làm nền) thay vì tự nghĩ lại từ đầu |
| **Self-evolving skills / harness (GH#10, đang Thua)** | `failure-flywheel` — weakness-mining thủ công, người-trong-vòng-lặp | **Self-Harness** (arXiv 2606.09498) làm gần đúng những gì `failure-flywheel` đang làm nhưng TỰ ĐỘNG hết vòng: mining execution trace → cluster lỗi theo pattern → tự sinh sửa harness. Có SỐ ĐO: +14.5% trung bình (ALFWorld/GAIA/SWE-bench Verified) từ riêng harness-evolution, +4.7% nữa nếu co-evolve cả model. NHƯNG: Terminal-Bench 2.1 cho thấy auto harness-evolution KHÔNG nhất quán thắng test-time-scaling đơn giản, generalize kém | Thua, nhưng bằng chứng vẫn 2 chiều (giống kỳ trước) | Tín hiệu mạnh nhất kỳ này: `failure-flywheel` đã đúng Ý TƯỞNG (weakness-mining → guardrail) mà Self-Harness paper mô tả — khác biệt chỉ là **mức tự động hoá** (paper: agent tự cluster+tự sửa; overstack: người đọc log rồi tự viết rule). Có thể claim rõ hơn: "failure-flywheel là bản người-trong-vòng-lặp của kiến trúc Self-Harness", và cân nhắc tự-động-hoá bước cluster (không phải bước apply — giữ người duyệt rule) làm bước kế tiếp nếu build GH#10 |
| **Memory (GH#9 — ĐÍNH CHÍNH: đã CLOSED/COMPLETED 03/07, không phải "open" như bảng kỳ trước chép nhầm)** | `llmwiki` (semantic+procedural) + `mem-rank.py`/`harness/mem-rank.config.yaml` — ADD/UPDATE/DELETE + eviction policy (write-policy thật) + TEMPORAL qua `ts`+`supersedes` chain = đã 4/4 tầng, tự-test PASS. Gap con còn lại: `relevance.scorer=embedding` chưa calib (`verified: false`, đã cách ly adapt-later, KHÔNG phải gap mới) | Gartner gọi 2026 là **"Year of Context"** — tách rõ 2 kỷ luật: *context engineering* (chọn/xếp/nén — mỗi lượt) vs *memory engineering* (write-policy, tầng lưu trữ, retrieval, bảo trì — xuyên phiên) | Ngang (đã đóng, kỳ trước 2 bản liền chép nhầm "Thua" từ template cũ — xem sửa lỗi bên dưới) | Không claim mới cho GH#9 — issue đã đóng đúng, có bằng chứng code thật (`mem-rank.py`). Khung context-vs-memory-engineering mới chỉ giúp MÔ TẢ chính xác hơn cái đã có (mem-rank = memory-engineering, wiki-room/ingest = context-engineering), không mở gap. Việc thật cần làm: sửa `ISSUES.md` + không chép lại "Thua" ở bản rà tới |
| **Skill security / supply-chain (GH#13 — ĐÍNH CHÍNH: đã CLOSED/COMPLETED 04/07, ledger vừa sửa lại đúng)** | `orca-sec-scans` (Trivy), `/skill-provenance` (sha256), `egress-guard.py` (chặn net-egress + MCP-injection-pattern, đã build + self-test) — 84 skill **private**, không kéo marketplace mở | 🔴 **CVE-2026-25253** — CVE ĐẦU TIÊN cấp cho agentic-AI skill runtime (RCE OpenClaw, 27/01/2026). Mitiga Labs (07/2026) trình diễn skill "hợp pháp trông thấy" âm thầm **exfiltrate toàn bộ codebase** — vector cụ thể chưa nêu ở các kỳ trước, đúng lớp mà `egress-guard.py` được thiết kế để bắt (network egress không nằm trong allow-list) | Ngang có-cơ-chế, nhưng **cơ chế đang tắt** — cần khác kỳ trước | `egress-guard.py` ĐÃ có detection (self-test PASS) nhưng `harness/egress-guard.config.yaml` hiện `mode: warn` + `allow_domains: []` (`verified: false`) — tức chỉ cảnh báo, KHÔNG chặn thật. Vector exfiltrate-qua-skill mới của Mitiga không đòi cơ chế mới, đòi **calib allow-list thật rồi lật `mode: block`** — đây là việc làm được ngay, không cần issue mới |
| **Deterministic orchestration / dynamic workflows** | `/orca-workflow`, Agent tool dùng ~1000-agent cap, pipeline/parallel | Claude Code bản thân đã "mở rộng dynamic workflows và nested subagents" (chính nền tảng overstack build trên), thêm filesystem isolation controls, session-resume mạnh hơn cho phiên dài | Ngang/Hơn (được kế thừa miễn phí) | Không cần claim — đây là nâng cấp của chính hạ tầng Claude Code mà Workflow tool overstack dùng đã tự hưởng lợi. Chỉ cần xác nhận orca-workflow không giả định hành vi cũ (VD filesystem isolation mới có thể đổi cách Agent isolation:'worktree' hoạt động) |
| **Eval / observability runtime (GH#11)** | `wikieval`, `medic eval`, `trace-grader` — tĩnh/CI | Không có phát hiện đảo chiều mới trong đợt quét này | Thua (không đổi) | Giữ nguyên đề xuất GH#11 |
| **Enterprise control-plane** *(ngoài phạm vi)* | Không có — framework single-operator | Không có tin mới nổi bật hơn kỳ trước (agent-memory-2026-07-22 đã ghi nhận 24/07) | Không áp dụng | Giữ nguyên: không đuổi theo, khác phân khúc |

## Tín hiệu đáng chú ý nhất kỳ này — khác gì với 24/07

**1. `failure-flywheel` hoá ra đã đi đúng kiến trúc Self-Harness — chỉ thiếu tự động hoá, không thiếu ý tưởng.** Đây là phát hiện tích cực nhất 3 kỳ gần đây: paper mô tả đúng 2 bước overstack đã làm tay (weakness-mining, cluster theo pattern). Khoảng cách thật là "ai bấm nút sinh rule" (người vs agent), không phải "có làm hay không". Điều này hạ nhẹ mức độ nghiêm trọng của GH#10 so với cách đọc trước đây ("overstack viết tay, thế giới tự động" nghe xa hơn thực tế).

**2. Supply-chain có một vector MỚI cụ thể: exfiltrate-codebase-qua-skill (Mitiga, 07/2026) + CVE đầu tiên cho agentic skill runtime.** Khác câu chuyện "1200 skill độc hại" đã biết — đây là bài test kỹ thuật cụ thể có thể tự chạy trên chính 84 skill của overstack (skill nào vừa đọc file-tree rộng vừa có network call). Đáng làm ngay trong `/orca-sec-scans`, không cần chờ raise issue mới vì công cụ đã tồn tại, chỉ thiếu 1 luật audit.

**3. Orchestration scale giờ có bản đồ thị trường theo tên cụ thể (Conductor, Vibe Kanban, Gastown, Claude Squad...), không còn mơ hồ "thế giới làm quy mô lớn hơn".** GH#12 có thể tham khảo trực tiếp 1 tool cùng tier (Claude Squad, cùng nền Claude Code) thay vì tự thiết kế lại.

**4. Đính chính quan trọng: GH#9 (memory) và GH#13 (supply-chain) thật ra đã CLOSED/COMPLETED từ 03–04/07, KHÔNG "open" như 2 bản rà trước (230726, 240726) chép.** Kiểm tra trực tiếp `gh issue view` mới phát hiện — `ISSUES.md` ledger local bị lệch so với GitHub thật (không sync sau khi đóng), và bản rà 24/07 kế thừa nhầm "Thua" từ template kỳ #2 mà không đối chiếu lại. Đã sửa `ISSUES.md` (status `open`→`done`) trong lần rà này; từ kỳ sau PHẢI chạy `gh issue view <n> --json state` trước khi chép verdict cũ, không suy diễn từ ledger local.

## Nên claim thêm gì — tóm tắt ưu tiên

1. **GH#13 (supply-chain, đã closed, KHÔNG mở lại):** cơ chế đã có (`egress-guard.py`, self-test PASS) nhưng đang `mode: warn` + `allow_domains: []` (`verified: false`) — chỉ cảnh báo, không chặn thật. Vector exfiltrate-qua-skill mới của Mitiga là lý do cụ thể để **calib allow-list thật rồi lật sang `mode: block`** — việc làm được ngay trong `harness/egress-guard.config.yaml`, không cần rule/issue mới.
2. **GH#10 (self-evolving skill, vẫn open):** đổi khung mô tả — `failure-flywheel` là **bản người-trong-vòng-lặp của kiến trúc Self-Harness**, không phải "chưa có gì". Nếu build tiếp, chỉ cần tự động hoá bước cluster-trace, giữ người duyệt ở bước apply-rule.
3. **GH#12 (orchestration scale, vẫn open):** tham khảo cụ thể Claude Squad (cùng nền Claude Code, cùng tier 3-10 agent) khi thiết kế mở rộng orca, thay vì chỉ ghi "thế giới làm lớn hơn" chung chung.
4. **GH#9 (memory, đã closed, KHÔNG mở lại):** không có claim mới — `mem-rank.py` đã 4/4 tầng + write-policy (ADD/UPDATE/DELETE/eviction) + temporal (`supersedes`). Gap con duy nhất (`scorer: embedding` chưa calib) đã tự cách ly trong `mem-rank.config.yaml`, không phải phát hiện mới.
5. **Không claim gì cho** deterministic-orchestration/dynamic-workflows và enterprise-control-plane — cả hai đã ghi nhận đủ ở kỳ trước hoặc là nâng cấp kế thừa miễn phí từ nền tảng.
6. **Cân nhắc thử nghiệm** per-subagent effort khác nhau theo độ khó việc trong `orca-workflow` (Agent tool đã hỗ trợ tham số, chưa được khai thác chủ động) — không phải gap khẩn, chỉ là cơ hội chưa dùng hết công cụ sẵn có.

## Nguồn

- [Claude Code Changelog (July 2026)](https://www.gradually.ai/en/changelogs/claude-code/)
- [Claude Developer Platform Updates by Anthropic — July 2026](https://releasebot.io/updates/anthropic/claude-developer-platform)
- [Claude AI Gets Yet Another Boost in VS Code 1.128](https://visualstudiomagazine.com/articles/2026/07/08/claude-ai-gets-yet-another-boost-in-vs-code-1-128.aspx)
- [Context vs. Memory Engineering in Agentic AI Systems](https://machinelearningmastery.com/context-vs-memory-engineering-in-agentic-ai-systems/)
- [The State of AI Agent Memory in 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- [Self-Harness: Harnesses That Improve Themselves (arXiv 2606.09498)](https://arxiv.org/html/2606.09498v1)
- [Harness Engineering for Self-Improvement — Lil'Log](https://lilianweng.github.io/posts/2026-07-04-harness/)
- [Harness Evolution for LLM Agents (Terminal-Bench 2.1 critique)](https://www.emergentmind.com/papers/2607.12227)
- [Skill Issues: Supply Chain Attack Vectors in an AI Agent Skills Marketplace — Orca Security](https://orca.security/resources/blog/ai-agent-skill-supply-chain-security/)
- [AI Agent Supply Chain Risk: Silent Codebase Exfiltration via Skills — Mitiga](https://www.mitiga.io/blog/ai-agent-supply-chain-risk-silent-codebase-exfiltration-via-skills)
- [OpenClaw's Skill Marketplace and the Emerging AI Supply Chain Threat — Unit42](https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/)
- [Microsoft at Black Hat USA 2026: Defending trust in the age of AI and supply chain attacks](https://www.microsoft.com/en-us/security/blog/2026/07/17/microsoft-at-black-hat-usa-2026-defending-trust-in-the-age-of-ai-and-supply-chain-attacks/)
- [The Code Agent Orchestra — Addy Osmani](https://addyosmani.com/blog/code-agent-orchestra/)
- [Best AI Coding Agents in 2026, Ranked — MightyBot](https://mightybot.ai/blog/coding-ai-agents-for-accelerating-engineering-workflows/)
