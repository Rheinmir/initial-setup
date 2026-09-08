---
title: "Overstack vs thế giới — 17/08/2026: agent trust, skill supply-chain, orchestration graph"
status: living
tags: [innovation, frontier, comparison, gap-analysis, last30days]
timestamp: 2026-08-17
id: innovation-170826
---

# Overstack vs thế giới — rà soát 17/08/2026

Tiếp nối [[innovation-110826]] (11/08, quét 1 đối thủ cụ thể theo yêu cầu). Kỳ này quay lại kiểu quét chủ đề chung bằng `/last30days` (khác `/frontier-scan` — 8 trục cố định), theo yêu cầu trực tiếp của user. Chạy 3 truy vấn `last30days` (Python 3.13, không có API key social nên nguồn thật = Reddit/HackerNews/GitHub/Polymarket qua RSS/keyless, thiếu X/TikTok): (1) "AI coding agent framework new features memory context engineering", (2) "AI agent skill marketplace supply chain security provenance", (3) "self-improving AI agent evaluation harness knowledge graph wiki". Đối chiếu với `fdk/CAPABILITIES.md` (85 skill · 19 rule · 19 fdk-tool · 67 harness-script) và `llmwiki/wiki/sources/ISSUES.md` (issue đang mở) để tránh trùng claim đã track.

## Bảng đối chiếu

| Trục | 🔵 Overstack đang có | 🟢 Ý tưởng mới thế giới (30 ngày qua) | Verdict |
|---|---|---|---|
| **Human-in-loop trước hành động rủi ro** | System-prompt bắt xác nhận trước hành động phá huỷ/khó-đảo-ngược (destructive/hard-to-reverse/shared-state); không có bước chấm điểm rủi ro tự động trước khi hỏi | *"Humans missed 1 in 3 threats approving AI agent commands across 40k game runs"* — nghiên cứu 40k lượt cho thấy con người tự duyệt lệnh agent bỏ sót 1/3 mối nguy (HN, 339 điểm, 245 bình luận) | **Thua — gap mới.** Cơ chế "hỏi người" hiện tại đúng hướng nhưng dữ liệu ngành cho thấy tự nó không đủ; cần lớp risk-score tất định (regex/heuristic trên lệnh) trước khi hỏi, không thay thế người mà lọc bớt cái người dễ bỏ sót |
| **Skill supply-chain: sync + rollback** | `skill-provenance` (GH#13, done) — ghi/kiểm sha256 khi cài skill ngoài, phát hiện bị sửa lén | PR thật (`the-Drunken-coder/DCS#1`, "port Thermos skills to Codex"): registry tuỳ biến bị từ chối ghi, đồng bộ cài **trọn cây skill** kèm **atomic lock write + rollback** | **Thua — mở rộng GH#13 đã đóng.** Có checksum-audit nhưng chưa có cơ chế atomic-install (nửa chừng lỗi thì rollback, không để skill tree ở trạng thái dở dang) |
| **Agent trust / anti-fabrication** | 3 issue đang mở: eval-blinding (GH#71), anti-fabrication số đo bịa (GH#72), behavioral-integrity-verification mô tả≠hành-vi (GH#102) | *"AI agents lie, cheat and steal. That is putting off users"* (The Economist qua HN, 164 điểm, 212 bình luận) — xác nhận đây là lo ngại tầm ngành, không phải riêng overstack | **Ngang — đã đi trước bài toán.** Không phải gap mới; tín hiệu này nên đẩy ưu tiên 3 issue kể trên lên, vì thị trường đang thực sự phạt các agent nói dối |
| **Context engineering: RAG vs file-first** | `wiki-loop` (`ingest`/`query`) — file-first, LLM đọc source thật, không vector DB | IBM Technology: *"Is the vector database destined for the museum of things we needed in 2024?"* — xu hướng nghi ngờ RAG/vector-DB cho corpus vừa, ưu tiên context window lớn + retrieval chọn lọc | **Ngang/đi trước.** Thiết kế file-first hiện tại của wiki-loop đã đúng hướng dịch chuyển của ngành, không cần đổi |
| **Orchestration đa-agent kiểu graph** | Skill `orchestration` (DAG task, blocking ask/reply) nhưng gap **orchestration-scale** (GH#12, open) — chưa có DAG-execution runtime hàng-trăm-subagent có verify | LangGraph tiếp tục là chuẩn de-facto cho graph-based multi-agent orchestration (IBM Technology, 605k views) | **Thua nhẹ — GH#12 vẫn mở**, không phải gap mới nhưng tín hiệu ngành xác nhận hướng graph-runtime là đúng để đầu tư tiếp |
| **Skill format: chuẩn mở liên-nền-tảng** | 85 skill dạng SKILL.md riêng của overstack, chưa đối chiếu với chuẩn ngoài | *"the skill.md format is an open standard, published at agentskills.io, Apache 2.0, adopted across a bunch of major AI coding platforms"* (IBM Technology, 372k views) | **Cần kiểm tra — chưa xác định.** Chưa biết SKILL.md của overstack có tương thích agentskills.io hay không; nếu tương thích thì skill overstack portable sang Cursor/Codex miễn phí, nếu không thì đây là gap tương thích |
| **License/dependency compliance trong CI** | `orca-sec-scans` (Trivy): vuln + misconfig + secret, không quét license SPDX | Dependency Review Action thấy trong evidence (PR CI thật): tự động chấm "0 vulnerable, 0 incompatible license, N package license không rõ" ngay trên PR | **Thua — gap nhỏ, mới.** `orca-sec-scans` chưa có nhánh license-compliance (SPDX) bên cạnh vuln-scan |

## Nên claim thêm (ưu tiên theo effort, thấp→cao)

1. **Kiểm tra tương thích SKILL.md ↔ agentskills.io** (rẻ nhất — chỉ đối chiếu spec, không code). Nếu khớp, đây là điểm bán được ("skill overstack portable"); nếu lệch, ghi rõ điểm lệch.
2. **License/SPDX scan thêm vào `orca-sec-scans`** — Trivy hỗ trợ sẵn license-scan (`trivy fs --scanners license`), có thể là bật thêm cờ chứ không phải viết mới (kiểm ladder trước khi build).
3. **Atomic-lock + rollback cho quá trình cài/đồng bộ skill** — mở rộng `skill-provenance`/`sync-skills.py`, không phải tool mới. Ceiling hiện tại: nếu sync giữa chừng lỗi, skill tree ở trạng thái dở dang không có cơ chế lùi.
4. **Risk-score tất định trước khi hỏi confirm hành động rủi ro** — gap có tác động an toàn cao nhất trong kỳ này. Không thay người quyết định, chỉ lọc bớt lệnh nguy hiểm dễ bị người duyệt vội bỏ sót (data: 1/3 miss rate).

Không raise GH issue tự động trong phiên này — raise issue là hành động công khai, cần user xác nhận trước (theo `/raise-issue`). 4 mục trên sẵn sàng làm input cho `/raise-issue` nếu user muốn mở.

## Nguồn
- HN: "Humans missed 1 in 3 threats approving AI agent commands across 40k game runs" — https://scalex.dev/blog/ai-agent-permissions-stats/ (2026-08-06, 339pts/245cmt)
- HN/Economist: "AI agents lie, cheat and steal. That is putting off users" — https://www.economist.com/business/2026/08/12/ai-agents-lie-cheat-and-steal-that-is-putting-off-users (2026-08-13, 164pts/212cmt)
- GitHub PR: the-Drunken-coder/DCS#1 "feat: port Thermos skills to Codex" — https://github.com/the-Drunken-coder/DCS/pull/1 (2026-08-13)
- YouTube (IBM Technology): "What AI Agent Skills Are and How They Work" — https://www.youtube.com/watch?v=Lg-meK5IU8Q
- YouTube (IBM Technology): "Is RAG Still Needed? Choosing the Best Approach for LLMs" — https://www.youtube.com/watch?v=UabBYexBD4k
- YouTube (IBM Technology): "LangChain vs LangGraph: A Tale of Two Frameworks" — https://www.youtube.com/watch?v=qAF1NjEVHhY
- HN: "Meta debuts first AI coding agent to take on Anthropic and OpenAI" — https://www.cnbc.com/2026/08/05/meta-debuts-muse-code-to-take-on-anthropic-and-openai-.html (2026-08-05)
- Đối chiếu nội bộ: `fdk/CAPABILITIES.md`, `llmwiki/wiki/sources/ISSUES.md` (GH#12, GH#13, GH#71, GH#72, GH#102), `skills/orca-sec-scans/`, `skills/skill-provenance/`

## Origin
Kích hoạt bởi yêu cầu trực tiếp của user (phiên 2026-08-17): "cài last30days repo nếu chưa có" + "đánh giá những gì repo của chúng ta làm được so với các ý tưởng mới trên thế giới ... ra 1 file /llmwiki/innovation/ddmmyy-innovation.md". `last30days` đã có sẵn tại `skills/last30days/` (không cần cài mới), chỉ cần Python 3.12+ (`/opt/homebrew/bin/python3.13`, máy có sẵn python3 mặc định là 3.9.6 không đủ). Không có API key social (`SCRAPECREATORS_API_KEY`/`XAI_API_KEY`/...) nên nguồn thật giới hạn ở Reddit(RSS)/HackerNews/GitHub/Polymarket — YouTube xuất hiện qua kết quả tìm kiếm không lọc theo ngày chặt (một số video cũ hơn 30 ngày lọt vào do YouTube fallback giữ tất cả khi 0 kết quả trong range).
