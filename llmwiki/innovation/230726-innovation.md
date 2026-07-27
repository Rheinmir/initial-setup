---
title: "Overstack vs thế giới — 23/07/2026"
status: living
tags: [innovation, frontier, comparison, gap-analysis]
timestamp: 2026-07-23
id: innovation-230726
---

# Overstack vs thế giới — rà soát 23/07/2026

Đối chiếu năng lực hiện tại của overstack (84 skill · 18 rule · 19 fdk-tool · 62 harness-script, tính từ `fdk/CAPABILITIES.md`) với các ý tưởng mới nhất trong mảng agent-framework/harness/skill trong khoảng 30 ngày qua. Đây là bản tiếp nối của chuỗi frontier-scan (`llmwiki/html/overstack-vs-world-30d.html`, lần cuối cập nhật 12/07/2026) — khoảng cách 11 ngày kể từ lần rà trước. Phương pháp: 5 WebSearch bám đúng 5 trục cố định của runbook `fdk/wiki/concepts/frontier-gap-scan.md`, đối chiếu với `fdk/CAPABILITIES.md` và ledger issue (`llmwiki/wiki/sources/ISSUES.md`, GH#9–13 vẫn đang mở).

## Bảng đối chiếu — cột CŨ (đã có) và MỚI (thế giới vừa xuất hiện)

| Trục | 🔵 Overstack — CŨ (đã có) | 🟢 Thế giới — MỚI (30 ngày qua) | Verdict | Nên claim thêm |
|---|---|---|---|---|
| **Harness / rule chặn** | 18 rule cắn cứng (R1–R18), `medic` làm cổng sức khoẻ cuối, `loop-runner` propose→verify→revise, `safe-change`/`impact-check` trước khi sửa code dùng chung | Anthropic tiếp tục đẩy hướng "harness architecture" — Managed Agents thêm **Outcomes** (rubric-graded, grader riêng biệt tự đẩy agent sửa tới khi đạt) | Ngang/Hơn | Có thể tự nhận diện với "Outcomes" pattern: `loop-runner` đã có vòng verify-revise, chỉ thiếu **rubric tường minh + grader tách biệt khỏi agent sinh** — khai rõ điểm này khi mô tả `loop-runner` để so sánh 1-1 được với thế giới |
| **Orchestration / đa-agent** | `orca` orchestration, `council` (blind peer-rank), `Workflow` (pipeline/parallel/barrier), agent teams quy mô vài–vài chục | Anthropic Managed Agents public-beta **multi-agent orchestration** (lead agent giao việc cho specialist agent, context/tool/model riêng) + **Dreaming** (research preview — agent tự "gạn lọc bài học" xuyên nhiều phiên, không cần người tổng hợp) | Chớm | "Dreaming" là ý tưởng MỚI overstack CHƯA có tương đương — `record-episode`/`failure-flywheel` vẫn cần người gọi tay, chưa có vòng tự-consolidate xuyên phiên chạy nền |
| **Memory** | `llmwiki` (semantic + procedural), `auto-memory` (MEMORY.md) — 1.5/4 tầng, không vector/episodic/temporal | MAGMA (multi-graph, tách episodic-subgraph, LoCoMo judge-score cao nhất tính đến đầu 2026) củng cố thêm cho hướng temporal-graph (Zep/Graphiti) đã ghi nhận kỳ trước — xu hướng ổn định, không có framework nào lật kèo | Thua (không đổi) | Vẫn đúng đề xuất kỳ trước: thêm tầng episodic + vector cho `llmwiki`. Không có phát hiện mới bắt buộc đổi hướng — GH#9 giữ nguyên |
| **Self-evolving skills** | `new-skill` scaffold thủ công + `failure-flywheel` (đề xuất rule khi lỗi lặp) + `fdk` — vẫn người-trong-vòng-lặp | CoEvoSkills (bản cập nhật 2026): "vượt qua skill do người curate chỉ sau 5 vòng tiến hoá" trên SkillsBench, có Verifier tách biệt (Surrogate Verifier) khỏi Generator — **ngược lại phát hiện thận trọng của SkillsBench gốc** ("skill tự sinh không đem lợi ích trung bình") mà báo cáo kỳ trước (GH#10) đã dùng làm lý do "chưa vội" | Thua | Tín hiệu ĐẢO CHIỀU đáng chú ý: risk "tự sinh skill không lợi" đang co lại KHI có verifier tách biệt độc lập. Nên nới ưu tiên GH#10 lên — nếu build vòng CoEvoSkills nội bộ, bắt buộc verifier KHÔNG dùng chung model/context với generator (đúng thiết kế đã ghi trong scan trước, giờ có thêm bằng chứng ủng hộ) |
| **Eval / observability runtime** | `wikieval`, `medic eval`, `trace-grader` — eval tĩnh/CI, chưa có tracing/simulation runtime | "Complete trace visibility is table stakes in 2026"; guardrail runtime chặn output không an toàn <200ms (Galileo); eval liên tục chạy song song offline (golden-set) + online (traffic thật) | Thua (không đổi) | Vẫn đúng đề xuất kỳ trước: tối thiểu ghi transcript có cấu trúc (đã có `journal.jsonl` của Workflow) → 1 view HTML timeline. GH#11 giữ nguyên |
| **Skill security / supply-chain** | `orca-sec-scans` (Trivy), `skill-provenance` (sha256), 84 skill **private** — không kéo marketplace mở | 🔴 **LEO THANG mạnh trong 30 ngày qua**: GuardFall (lỗi shell-injection ảnh hưởng >500k deployment mã nguồn mở), 1.184 skill độc hại xác nhận trên ClawHub (tăng từ ~900/4.500 kỳ trước), RCE qua **poisoned repository config file** trong Claude Code, poisoning cả GitHub Action của Claude Code; JFrog×Anthropic vừa ra governance layer chính thức cho MCP/skill supply-chain | Chớm → cần nâng cảnh giác | Việc "private, không kéo marketplace" đã đúng, giờ càng đúng hơn — NÊN CLAIM rõ ràng đây là lợi thế phòng thủ chủ động, không phải tình cờ. Nhưng đe doạ MỚI là **poisoned repo config** (khác hẳn "skill độc hại từ marketplace") — cần tự hỏi: config/hook nội bộ (`.claude/settings.json`, hooks) của overstack có được ký/kiểm toàn vẹn không? Đây là câu hỏi CHƯA có trong GH#13, nên bổ sung |
| **Knowledge / context engineering** | `llmwiki` có Origin/ADR/concept/entity, `wiki-room` nạp on-demand, pipeline `ingest` | Không có phát hiện mới đảo chiều kỳ này — hướng "skill/wiki = institutional-knowledge primitive" tiếp tục là dòng chính, overstack đã trưởng thành hơn phần lớn repo public | Ngang/Hơn (không đổi) | Giữ nguyên positioning, không cần claim thêm |
| **Quy mô & phân phối** | 84 skill (tăng từ 71 tại baseline 03/07), template pull nội bộ, `marketplace.json` riêng | Marketplace mở tiếp tục phình (ClawHub, Skills.sh, SkillsMP) nhưng đi kèm chính là nguồn của làn sóng tấn công supply-chain nói trên | Thua (về lượng, nhưng giờ có thêm lý do CHỦ ĐỘNG không đuổi theo lượng) | Không nên chạy theo số lượng marketplace mở — nên claim "quy mô private + provenance-audited" như một CHIẾN LƯỢC BẢO MẬT, không phải hạn chế tạm thời |

## Hai tín hiệu mới nhất — chưa từng xuất hiện ở 2 kỳ scan trước

**1. "Dreaming" (Anthropic Managed Agents, research preview).** Agent tự gạn lọc bài học xuyên nhiều phiên chạy nền, không cần người gọi tay tổng hợp lại. Đây là điểm overstack chưa có tương đương thật: `record-episode` và `failure-flywheel` đều đúng ý tưởng (đúc kết bài học từ phiên) nhưng đều CẦN người/skill gọi chủ động sau khi phiên kết thúc — không có vòng nền tự-consolidate. Nên ghi nhận đây là một trục MỚI cần theo dõi, chưa vội raise issue vì Dreaming còn ở research preview (chưa production), nhưng đáng đưa vào lần scan kế tiếp để xem có ổn định thành pattern hay không.

**2. Leo thang supply-chain trong đúng hệ sinh thái Claude Code.** Khác các kỳ trước (đe doạ chủ yếu ở marketplace ngoài như ClawHub), lần này xuất hiện 2 vector áp sát trực tiếp overstack hơn: poisoning GitHub Action của Claude Code, và RCE qua poisoned repository config file. Vì overstack cũng dùng hook (`llmwiki/.claude/hooks/`) và cấu hình `.claude/settings.json`, đây là câu hỏi tự-vấn cụ thể chưa có trong GH#13 hiện tại: cấu hình/hook nội bộ có được kiểm toàn vẹn (checksum/provenance) như skill đã có qua `/skill-provenance` không?

## Nên claim thêm gì — tóm tắt ưu tiên

1. **Claim rõ ràng, không đợi hỏi**: "84 skill private + `/skill-provenance` (sha256) + không kéo marketplace mở" là một lựa chọn bảo mật chủ động, đúng lúc thế giới vừa xác nhận 1.184 skill độc hại trên 1 marketplace duy nhất. Đây là điểm bán hàng (positioning) nên nói to hơn, không chỉ nằm im trong ISSUES.md.
2. **Mở rộng phạm vi GH#13** (skill-resolve + supply-chain) để bao thêm câu hỏi "hook/config nội bộ có được kiểm toàn vẹn không" — hiện GH#13 chỉ nói skill, chưa nói tới hook/settings.json.
3. **Theo dõi tiếp CoEvoSkills** — bằng chứng mới nghiêng về ủng hộ self-evolving CÓ verifier tách biệt. Không đổi kế hoạch GH#10 (vẫn giữ người duyệt cuối), nhưng độ tin cậy của hướng "để agent tự sinh skill, miễn có verifier độc lập" đã tăng — đáng nhắc lại trong lần chạy /fdk kế tiếp nhận việc GH#10.
4. **Đưa "Dreaming" vào radar** — chưa raise issue (còn research preview), nhưng ghi vào lần scan kế để so sánh có ổn định thành pattern production hay không trước khi đầu tư.
5. **Memory / Observability (GH#9, GH#11) — không đổi**, giữ nguyên đề xuất kỳ trước, không có phát hiện nào đảo chiều ưu tiên.

## Nguồn

- [AI Agent Memory 2026: Vector, Graph, Episodic Update](https://www.digitalapplied.com/blog/ai-agent-memory-vector-graph-episodic-2026)
- [State of AI Agent Memory 2026 — Mem0](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- [Implicit Graph, Explicit Retrieval — arXiv 2601.03417](https://arxiv.org/pdf/2601.03417)
- [Beyond Dialogue Time: Temporal Semantic Memory — arXiv 2601.07468](https://arxiv.org/pdf/2601.07468)
- [CoEvoSkills: Self-Evolving Agent Skills via Co-Evolutionary Verification — arXiv 2604.01687](https://arxiv.org/html/2604.01687)
- [SkillForge: Forging Domain-Specific Self-Evolving Agent Skills — arXiv 2604.08618](https://arxiv.org/html/2604.08618v1)
- [Agent Skill Evaluation and Evolution: Frameworks and Benchmarks — arXiv 2606.11435](https://arxiv.org/html/2606.11435v1)
- [AI Agent Observability 2026: Tracing & Monitoring Stack](https://www.digitalapplied.com/blog/ai-agent-observability-2026-tracing-monitoring-stack-guide)
- [8 Best AI Agent Guardrails Solutions in 2026 — Galileo](https://galileo.ai/blog/best-ai-agent-guardrails-solutions)
- [Top AI Coding Agent security resources — July 2026 — Adversa AI](https://adversa.ai/blog/top-ai-coding-agent-security-resources-july-2026/)
- [When Your AI Coding Plugin Starts Picking Your Dependencies — SentinelOne](https://www.sentinelone.com/blog/marketplace-skills-and-dependency-hijack-in-claude-code/)
- [JFrog and Anthropic Bring Enterprise-Grade Software Supply Chain Governance to Claude Code](https://www.businesswire.com/news/home/20260610800676/en/JFrog-and-Anthropic-Bring-Enterprise-Grade-Software-Supply-Chain-Governance-and-Security-to-Claude-Code)
- [Code with Claude 2026: 5 New Agent Features Anthropic Just Shipped — MindStudio](https://www.mindstudio.ai/blog/code-with-claude-2026-new-agent-features)
- [Claude Managed Agents: Dreaming, Outcomes, and Multi-Agent Orchestration — Developers Digest](https://www.developersdigest.tech/blog/claude-managed-agents-dreaming-outcomes-multi-agent)
- [Effective harnesses for long-running agents — Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

## Origin

Tạo theo yêu cầu trực tiếp của user (phiên 23/07/2026): "đánh giá những gì repo của chúng ta làm được so với các ý tưởng mới trên thế giới". Dựng trên baseline có sẵn của chuỗi frontier-scan (`llmwiki/html/overstack-vs-world-30d.html`, scan #1–#3, 03/07–12/07/2026) và ledger `llmwiki/wiki/sources/ISSUES.md` (GH#9–13). Khác `/frontier-scan` ở chỗ: đây là bản chụp một lần theo yêu cầu, đặt tại `llmwiki/innovation/` (không phải `llmwiki/wiki/`), KHÔNG tự raise/cập nhật issue — việc đó vẫn thuộc về skill `/frontier-scan` khi được gọi.
