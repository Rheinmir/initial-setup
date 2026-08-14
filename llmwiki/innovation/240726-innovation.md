---
title: "Overstack vs thế giới — 24/07/2026"
status: living
tags: [innovation, frontier, comparison, gap-analysis]
timestamp: 2026-07-24
id: innovation-240726
---

# Overstack vs thế giới — rà soát 24/07/2026

Bản tiếp nối trực tiếp của [[innovation-230726]] (hôm qua), chạy lại đúng runbook `fdk/wiki/concepts/frontier-gap-scan.md` — 5 WebSearch cố định theo 5 trục, đối chiếu `fdk/CAPABILITIES.md` (vẫn 84 skill · 18 rule · 19 fdk-tool · 62 harness-script, không đổi số so với hôm qua) và ledger `llmwiki/wiki/sources/ISSUES.md` (GH#9–13 vẫn `needs-triage`, chưa ai nhận). Khoảng cách chỉ 1 ngày nhưng ba nguồn có dấu thời gian rất mới (22/07, 21/07, 17/07) nên vẫn có tín hiệu thật đáng ghi, không phải lặp lại suông.

Trước khi chạy nghiên cứu, đã kiểm tra và xác nhận skill `/last30days` (v3.3.2, nguồn `mvanhorn/last30days-skill`) đã cài sẵn tại `~/.claude/skills/last30days/` — không cần cài lại. Skill này tối ưu cho tín hiệu mạng xã hội tiêu dùng (Reddit/X/TikTok về người/sản phẩm), không khớp với chủ đề kỹ thuật (framework/paper/blog kỹ sư) của bản rà này, nên bản rà vẫn dùng WebSearch trực tiếp theo đúng runbook đã có, giống hệt phương pháp hôm qua.

## Bảng đối chiếu — cột CŨ (đã có) và MỚI (thế giới vừa xuất hiện, 24/07)

| Trục | 🔵 Overstack — CŨ (đã có) | 🟢 Thế giới — MỚI (tính đến 24/07) | Verdict | Nên claim thêm |
|---|---|---|---|---|
| **Harness / orchestration nền tảng** | 18 rule cắn cứng, `medic` cổng sức khoẻ, `loop-runner` propose→verify→revise, `orca` orchestration đa-agent | Claude Developer Platform thêm `agent-memory-2026-07-22` (beta, ra 2 ngày trước bản rà này): thứ tự memory-listing ổn định phía server + phân trang `depth`/`path_prefix`/`cursor`; Managed Agents thêm model-effort setting, webhook phủ rộng hơn (event/memory-store), session seeding, event delta cho thread stream | Ngang (không đổi hướng) | Không cần claim mới — đây là Anthropic siết chặt API nội bộ của chính họ, không phải mô hình mới overstack cần bắt kịp |
| **Enterprise deployment / control-plane** *(trục mới, chưa từng chấm trước đây)* | overstack không có khái niệm này — là framework dev cá nhân/nhóm nhỏ, không multi-tenant | Anthropic ra "Claude apps gateway" (Bedrock + Google Cloud): control-plane tự host cho Claude Code — SSO doanh nghiệp, policy tập trung, RBAC, cost-tracking theo user, spend cap | Không áp dụng (khác phân khúc) | KHÔNG nên đuổi theo — ghi nhận đây là sản phẩm cho tổ chức lớn nhiều dev dùng chung ngân sách API, ngoài phạm vi mục tiêu hiện tại của overstack (single-operator, private). Chỉ đáng quay lại nếu overstack có ngày mở multi-user |
| **Memory** | `llmwiki` (semantic+procedural), `auto-memory` (MEMORY.md) — 1.5/4 tầng | Không đảo chiều: memory tiếp tục là "production engineering discipline" chuẩn hoá (Phil Schmid/Google DeepMind gọi context engineering là "kỹ năng AI định hình của 2026"); hạ tầng đã phủ 21 framework, 20 vector store, 3 mô hình hosting | Thua (không đổi) | Giữ nguyên đề xuất GH#9 (episodic+vector). Không có phát hiện mới bắt buộc đổi hướng |
| **Self-evolving skills** | `new-skill` scaffold thủ công + `failure-flywheel` — người-trong-vòng-lặp | Ba hướng nghiên cứu MỚI xuất hiện đúng tuần này: **MetaSkill-Evolve** (arXiv 2607.05297, tự-cải-tiến đệ quy 2 tầng thời gian) và **SkillAudit** (arXiv, kiểm-tiến-hoá-skill KHÔNG cần ground-truth, dùng paired-trajectory auditing thay vì verifier tách biệt) — hướng ngược lại phần nào so với CoEvoSkills (verifier tách biệt) mà bản rà hôm qua vừa ghi nhận. Đồng thời có bài phản biện phương pháp luận: "Rethinking the Evaluation of Harness Evolution for Agents" (HuggingFace papers, chỉ ra các benchmark harness-evolution hiện tại tự kiểm trên chính public benchmark đã dùng để tìm cấu hình — nguy cơ overfit) | Thua, nhưng CẨN TRỌNG hơn hôm qua | Tín hiệu quan trọng nhất kỳ này: bằng chứng ủng hộ "cần verifier tách biệt" (hôm qua) và "không cần verifier, dùng audit theo cặp trajectory" (SkillAudit, hôm nay) đang RA CÙNG LÚC — nghĩa là cộng đồng chưa hội tụ về MỘT kiến trúc đúng. Bài phản biện benchmark càng củng cố lý do "chưa vội" của GH#10 — nên hạ nhẹ lại mức ưu tiên vừa nâng hôm qua, chờ hội tụ rõ hơn trước khi build |
| **Self-improving qua "Dreaming"** | `record-episode`/`failure-flywheel` — cần người gọi tay, không có vòng nền tự-consolidate | **Dreaming đã có case study thật, không còn chỉ là research preview trừu tượng**: Harvey (legal AI) tăng ~6x tỷ lệ hoàn thành task sau khi bật Dreaming; Wisedocs cắt 50% thời gian review tài liệu nhờ Outcomes (rubric + grader tách biệt) | Chớm → nâng mức tin cậy | Khác biệt so với hôm qua ("chưa vội vì còn preview"): giờ có SỐ ĐO THẬT từ khách hàng doanh nghiệp. Đáng đưa vào radar ưu tiên cao hơn — nếu build thử một vòng "tự-consolidate nền" cho `record-episode`/`failure-flywheel`, đây là bằng chứng ROI cụ thể để trích dẫn khi đề xuất |
| **Skill security / supply-chain** | `orca-sec-scans` (Trivy), `/skill-provenance` (sha256), 84 skill **private**, không kéo marketplace mở | 🔴 **Đã có TÊN CHIẾN DỊCH cụ thể**: "ClawHavoc" — hơn 1.200 skill độc hại cài vào marketplace OpenClaw, phát tán credential-stealer AMOS. Phân tích quy mô lớn: 42.447 skill được rà, **26,1% có ít nhất 1 lỗ hổng bảo mật**. Unit42 (Palo Alto) ra báo cáo riêng về đúng rủi ro này. Giữa tháng 7 xuất hiện khuyến nghị ngành mới: coi AI agent là "principal hạng nhất" — cần identity có vòng đời, RBAC theo-task, tool-binding, JIT-elevation, audit log | Chớm → cần nâng cảnh giác (đúng hướng hôm qua, giờ có số liệu cụ thể hơn) | Con số 26,1% skill-có-lỗ-hổng trên diện rộng là căn cứ SỐ để nói to hơn về lựa chọn "84 skill private + provenance sha256". Đồng thời khuyến nghị "agent = principal hạng nhất" (identity/RBAC/JIT/audit) là góc NHÌN MỚI GH#13 chưa có — câu hỏi cụ thể: các hook/rule của overstack chạy với quyền gì, có tự giới hạn phạm vi (task-scoped) không, hay luôn full quyền của phiên? Nên bổ sung câu hỏi này vào GH#13 |
| **Eval / observability runtime** | `wikieval`, `medic eval`, `trace-grader` — tĩnh/CI | Không có phát hiện đảo chiều mới trong đợt quét này (không trùng với 2 nguồn có ngày mới nhất) | Thua (không đổi) | Giữ nguyên đề xuất GH#11, không đổi ưu tiên |
| **Knowledge / context engineering** | `llmwiki` có Origin/ADR/concept/entity, pipeline `ingest`, `wiki-room` on-demand | Củng cố thêm: giới học thuật/công nghiệp gọi context engineering là "kỹ năng AI định hình của 2026" (không phải ý tưởng ngách) — bốn nhóm kỹ thuật chuẩn: write/select/compress/isolate | Ngang/Hơn (không đổi) | overstack đã làm đúng 2/4 (write=ingest, select=wiki-room on-demand); có thể tự nhận diện rõ hơn 2 nhóm còn thiếu (compress, isolate) khi mô tả `llmwiki` — không cần build ngay, chỉ cần đặt đúng tên khi so sánh |

## Tín hiệu đáng chú ý nhất kỳ này — khác gì với hôm qua

**1. Self-evolving skills: cộng đồng CHƯA hội tụ về kiến trúc, chứ không phải overstack chậm.** Hôm qua bản rà kết luận "nên nới ưu tiên GH#10 vì CoEvoSkills có verifier tách biệt". Hôm nay, SkillAudit đề xuất hướng ngược lại (không cần verifier riêng), và một bài riêng phản biện chính phương pháp benchmark harness-evolution đang dùng để so sánh các hướng này. Kết luận đúng hơn cho GH#10 không phải "làm ngay theo verifier tách biệt" mà là "đợi thêm 1-2 kỳ quét nữa để xem hướng nào thắng thế trước khi chọn kiến trúc, vì build sai kiến trúc rồi phải đảo lại tốn hơn chờ".

**2. Dreaming đã có ROI đo được, không còn là ý tưởng research-preview mơ hồ.** Đây là nâng cấp thật của mức độ tin cậy so với hôm qua (lúc đó lý do "chưa vội" là "còn preview, chưa production"). Giờ Harvey và Wisedocs đã công bố số cụ thể (6x, 50%). Nếu có kỳ tới vẫn không thấy overstack có tương đương, nên cân nhắc raise issue thật (chưa raise hôm nay vì cần thêm 1 kỳ xác nhận xu hướng ổn định, không phải một tin đơn lẻ).

**3. Supply-chain đã có tên chiến dịch + con số quy mô lớn (26,1%/42.447 skill).** Không đổi kết luận so với hôm qua (vẫn "leo thang, overstack đang đúng hướng phòng thủ chủ động"), nhưng giờ có bằng chứng định lượng mạnh hơn nhiều để trích dẫn khi cần thuyết phục ai đó rằng lựa chọn "private + provenance" là cố ý, không phải ngẫu nhiên.

**4. Một trục hoàn toàn mới xuất hiện (enterprise control-plane) nhưng KHÔNG phải gap của overstack** — khác phân khúc thị trường (nhiều-dev-dùng-chung-ngân-sách vs single-operator). Ghi nhận để không nhầm lẫn "chưa có" với "cần có".

## Nên claim thêm gì — tóm tắt ưu tiên

1. **Hạ nhẹ ưu tiên GH#10 vừa nâng hôm qua** — bằng chứng mới (SkillAudit + bài phản biện benchmark) cho thấy cộng đồng chưa hội tụ kiến trúc self-evolving-skill đúng; chờ thêm tín hiệu ổn định thay vì build theo hướng verifier-tách-biệt ngay.
2. **Theo dõi Dreaming sát hơn** — đã có ROI thật (Harvey 6x, Wisedocs 50%) từ nghiên cứu-preview; chưa raise issue mới hôm nay, nhưng nếu kỳ quét tới vẫn xác nhận xu hướng, nên raise một issue riêng cho "vòng tự-consolidate bài học chạy nền" (khác `record-episode`/`failure-flywheel` hiện tại vốn cần gọi tay).
3. **Bổ sung câu hỏi cụ thể vào GH#13**: hook/rule nội bộ của overstack chạy với quyền gì — có task-scoped hay luôn full quyền phiên? Đây là góc nhìn "agent = principal hạng nhất" (identity/RBAC/JIT/audit) vừa xuất hiện giữa tháng 7, GH#13 hiện chưa hỏi câu này.
4. **Claim to hơn con số 26,1% skill-có-lỗ-hổng / chiến dịch ClawHavoc đặt tên** khi mô tả vì sao overstack chọn 84 skill private + `/skill-provenance` — giờ có số liệu ngành cụ thể để so sánh, không chỉ nói chung chung "an toàn hơn".
5. **Không đuổi theo "enterprise control-plane"** (Claude apps gateway) — khác phân khúc, không phải gap; chỉ ghi vào radar để nhắc lại nếu định hướng overstack đổi sang multi-user.
6. **Memory (GH#9), Observability (GH#11) — không đổi**, giữ nguyên đề xuất các kỳ trước.

## Nguồn

- [Claude Code Changelog (July 2026)](https://www.gradually.ai/en/changelogs/claude-code/)
- [Claude Developer Platform Updates by Anthropic — July 2026](https://releasebot.io/updates/anthropic/claude-developer-platform)
- [Claude AI Gets Yet Another Boost in VS Code 1.128](https://visualstudiomagazine.com/articles/2026/07/08/claude-ai-gets-yet-another-boost-in-vs-code-1-128.aspx)
- [Context vs. Memory Engineering in Agentic AI Systems](https://machinelearningmastery.com/context-vs-memory-engineering-in-agentic-ai-systems/)
- [AI Agent Memory 2026: Progress Benchmark Report — Mem0](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
- [Context Engineering AI: How To Build Smarter LLM Agents In 2026 — Mem0](https://mem0.ai/blog/context-engineering-ai-agents-guide)
- [Evolving the Harness, Not the Model: Unlocking Self-Improving AI Agents](https://www.franksworld.com/2026/07/21/evolving-the-harness-not-the-model-unlocking-self-improving-ai-agents/)
- [Rethinking the Evaluation of Harness Evolution for Agents — HuggingFace Papers](https://huggingface.co/papers/2607.12227)
- [MetaSkill-Evolve: Recursive Self-Improvement of LLM Agents via Two-Timescale Meta-Skill Evolution](https://arxiv.org/pdf/2607.05297)
- [SkillAudit: Ground-Truth-Free Skill Evolution via Paired Trajectory Auditing](https://arxiv.org/pdf/2606.14239)
- [Harness Engineering for Self-Improvement — Lil'Log (Lilian Weng)](https://lilianweng.github.io/posts/2026-07-04-harness/)
- [Skill Issues: How We Discovered Supply Chain Attack Vectors in an AI Agent Skills Marketplace — Orca Security](https://orca.security/resources/blog/ai-agent-skill-supply-chain-security/)
- [OpenClaw's Skill Marketplace and the Emerging AI Supply Chain Threat — Unit42 (Palo Alto Networks)](https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/)
- [Microsoft at Black Hat USA 2026: Defending trust in the age of AI and supply chain attacks](https://www.microsoft.com/en-us/security/blog/2026/07/17/microsoft-at-black-hat-usa-2026-defending-trust-in-the-age-of-ai-and-supply-chain-attacks/)
- [AI Agent Security Risks 2026: MCP, OpenClaw & Supply Chain](https://blog.cyberdesserts.com/ai-agent-security-risks/)
- [New in Claude Managed Agents: dreaming, outcomes, and multiagent orchestration — Claude by Anthropic](https://claude.com/blog/new-in-claude-managed-agents)
- [Anthropic will let its managed agents dream — The New Stack](https://thenewstack.io/anthropic-managed-agents-dreaming-outcomes/)
- [Claude's New Dreaming Feature Builds Self-Improving AI Agents — Forbes](https://www.forbes.com/sites/jonmarkman/2026/05/11/claudes-new-dreaming-feature-builds-self-improving-ai-agents/)

## Origin

Tạo theo yêu cầu trực tiếp của user (phiên 24/07/2026): "cài last30days repo nếu chưa có" (đã xác nhận có sẵn, không cần cài lại) rồi "đánh giá những gì repo của chúng ta làm được so với các ý tưởng mới trên thế giới ... so sánh nên claim thêm cái gì". Nối tiếp trực tiếp [[innovation-230726]] (hôm qua) và chuỗi frontier-scan gốc (`llmwiki/html/overstack-vs-world-30d.html`, scan #1–#3, 03/07–12/07/2026). Phương pháp giống hệt bản hôm qua: 5 WebSearch theo đúng 5 trục cố định của `fdk/wiki/concepts/frontier-gap-scan.md`, KHÔNG dùng engine `/last30days` (đã cân nhắc — không hợp chủ đề kỹ thuật/dev, xem đoạn mở đầu). KHÔNG tự raise/cập nhật issue GH — việc đó thuộc về skill `/frontier-scan` khi được gọi riêng.
