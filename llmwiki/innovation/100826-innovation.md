---
title: "Overstack vs thế giới — 10/08/2026"
status: living
tags: [innovation, frontier, comparison, gap-analysis]
timestamp: 2026-08-10
id: innovation-100826
---

# Overstack vs thế giới — rà soát 10/08/2026

Tiếp nối [[innovation-070826]] (3 ngày trước, có khoảng trống 08-09/08 không quét). Trước khi quét, xác nhận thật hai điều kiện tiên quyết:

1. **`last30days`** — kiểm tra project-local (`skills/last30days/`) chỉ có `SKILL.md` (127.7K), **KHÔNG có `scripts/`/`agents/`/`assets/`/`references/`** — đúng bẫy đã ghi trong memory kỳ #7 ("SKILL.md không phải bằng chứng engine tồn tại"). Đã copy đầy đủ 4 thư mục từ repo gốc `github.com/mvanhorn/last30days-skill` (clone tại `/Users/giatran/orca/last30day/last30days-skill`, cùng version `3.3.2`) vào `skills/last30days/`. Máy này không có `python3.12/3.13` trong PATH mặc định (chỉ `python3` = 3.9.6) nhưng có `python3.13` qua Homebrew (`/opt/homebrew/bin/python3.13`) — dùng bản đó. `--diagnose` xác nhận 5 nguồn keyless sống: Reddit, YouTube, Hacker News, Polymarket, GitHub (X thiếu vì chưa đăng nhập cookie, TikTok/Instagram thiếu vì chưa có ScrapeCreators key, web-grounding thiếu vì chưa có Brave/Exa/Serper key).
2. **`fdk/CAPABILITIES.md`** — vẫn **84 skill · 18 rule · 19 fdk-tool · 63 harness-script**, đứng yên **10 kỳ liên tiếp** (27/07 → 10/08).
3. **GH#9-13** — trạng thái không đổi sau 3 kỳ: #9 CLOSED, #10 OPEN, #11 OPEN, #12 OPEN, #13 CLOSED (`gh issue view` xác nhận trực tiếp, không suy từ memory).

Kỳ này chạy 4 truy vấn cố định qua engine `last30days` (reddit+hackernews+github, không có nguồn X/web-grounding do thiếu key) cộng 2 truy vấn WebSearch tự chọn để đào sâu tín hiệu nóng nhất và xác minh watch-item chiến lược từ kỳ trước.

## Bảng đối chiếu — cột CŨ (overstack đang có) và MỚI (thế giới, tính đến 10/08)

| Trục | 🔵 CŨ — Overstack đang có | 🟢 MỚI — Thế giới (đến 10/08) | Verdict | Nên claim thêm |
|---|---|---|---|---|
| **Skill supply-chain / behavioral integrity (nhánh con MỚI của GH#13 đã đóng)** | `skill-provenance`: ghi+kiểm nguồn (URL/commit) + sha256 checksum TĨNH lúc cài skill — không kiểm hành vi runtime | **BIV (Behavioral Integrity Verification)** — framework hình thức mới, arXiv 2605.11770v1: typed-set-comparison giữa capability khai báo và capability thật qua taxonomy chung code+instruction+metadata; test trên registry OpenClaw: 250,706 behavioral deviations, 80.0% skill (39,933/49,918) mismatch; root-cause 81.1% oversight / 18.9% adversarial / 5.0% multi-stage attack chain. Kèm 2 sản phẩm thương mại đã ship: **Mondoo AI Agent Skill Security Scanner** (Layer 3 LLM-powered behavior-mismatch) và **Cisco Skill Scanner** (pattern + LLM-as-judge + behavioral dataflow) | **Thua — gap mới đủ chín để raise (đã leo thang từ "hạt giống" 07/08 lên framework hình thức + 2 sản phẩm thật)** | **Đã raise [GH#102](https://github.com/Rheinmir/setup/issues/102)** kỳ này — `skill-provenance` cần thêm lớp behavioral (đối chiếu mô tả↔tool-call thật), bổ sung không thay thế provenance tĩnh hiện có |
| **Product-surface watch (GH#10/11/12) — Managed Agents có "chảy xuống" Claude Code CLI không?** | `failure-flywheel` (GH#10), trace-log đề xuất chưa làm (GH#11), `Workflow` tool + `orca` (GH#12) — tất cả phục vụ Claude Code CLI | Anthropic **Dreaming / Outcomes / Multiagent Orchestration** (công bố 06/05/2026, Code with Claude) — WebSearch xác nhận hôm nay: **vẫn CHỈ nằm trên Claude Platform API** (Managed Agents, public beta, header `managed-agents-2026-04-01`), khả dụng cho "all developers via the API" — KHÔNG thấy dấu hiệu chảy xuống Claude Code CLI | **Watch-item kỳ trước tạm đóng — câu trả lời là "chưa"**, không cần định vị lại 3 trục GH#10/11/12 lúc này | Đã `gh issue comment` cập nhật kết luận "chưa chảy xuống CLI" lên GH#10/11/12 — không hành động thêm, chỉ theo dõi tiếp ở kỳ sau nếu có tín hiệu CLI-side |
| **Harness engineering canon (GH#10/#11, quét lại — không đổi)** | Khung AHE 3 trụ (component/experience/decision, từ bài Lilian Weng đã cite 06/08) + Self-Harness pattern — đã ghi nhận, **CHƯA implement** vào trace-log `Workflow` (giờ đã treo **9 kỳ liên tiếp**) | Không có cập nhật mới đáng kể kỳ này ngoài việc WebFetch lại xác nhận đúng nội dung: Self-Harness (propose-evaluate-accept loop), AlphaEvolve, Darwin Gödel Machine — cùng canon đã biết, không có phát triển mới từ 06-07/08 | **Thua, không đổi** — vẫn là việc rẻ nhất chưa ai bắt tay | Không raise/comment thêm (không có delta thật); việc rẻ nhất vẫn treo: trace-log `Workflow` theo khung AHE, `opts.model`/`opts.effort` đã sẵn có cho lớp "decision" |
| **Agent framework / harness noise chung (quét 2 truy vấn last30days: "Claude Code updates", "AI agent memory")** | — | Tín hiệu yếu, chủ yếu Show-HN của các dự án nhỏ (harness thay thế Claude Code, agent GUI, memory-layer viết bằng Go stdlib) — không có framework/paper nào đủ trọng lượng để đổi verdict trục nào | **Không đổi** | Không hành động — ghi nhận đây là kỳ "yên tĩnh" trên 2 trục này, tiết kiệm để dồn sức cho trục có delta thật (supply-chain) |

## Tín hiệu đáng chú ý nhất kỳ này — khác gì với 07/08

**1. GH#13 (supply-chain, đã đóng) sinh ra một nhánh con MỚI đủ chín để raise: Behavioral Integrity Verification.** Đây là lần đầu tiên "hạt giống" được ghi nhận ở một kỳ trước (070826, mục 4 — chỉ 1 khảo sát 42k-skill) leo thang thành framework hình thức có tên riêng (BIV, arXiv 2605.11770v1) VÀ có ít nhất 2 sản phẩm thương mại thật đã ship đúng lớp kiểm tra đó (Mondoo, Cisco). Đã raise [GH#102](https://github.com/Rheinmir/setup/issues/102) đúng lúc — không phải phản ứng thái quá với 1 khảo sát đơn lẻ, mà phản ứng với sự leo thang có bằng chứng lặp lại qua 2 kỳ quét.

**2. Watch-item chiến lược từ kỳ 07/08 (Dreaming/Outcomes/Multiagent Orchestration có chảy xuống Claude Code CLI không?) đã có câu trả lời xác nhận: CHƯA.** Ba tính năng này vẫn khoá cứng trong Claude Platform API (Managed Agents, public beta), khác product-surface với overstack build trên Claude Code CLI. Ba trục GH#10/11/12 không cần định vị lại — đã comment cập nhật cả ba issue để đóng loop theo dõi này.

**3. GH#11 (observability) nay đã treo 9 kỳ liên tiếp — vẫn là việc rẻ nhất chưa ai bắt tay, dù khung AHE + tham chiếu Outcomes (kỳ trước) đã đủ để thiết kế mà không cần tự nghĩ từ đầu.** Không có tín hiệu mới kỳ này để thay đổi mức độ ưu tiên, chỉ xác nhận độ trễ tiếp tục tăng.

**4. Kỳ này có khoảng trống 2 ngày (08-09/08) không quét** — lần đầu gián đoạn chuỗi hàng ngày kể từ 03/08. Không phát hiện gap nào xấu đi trong khoảng trống đó (GH#9-13 đứng yên, CAPABILITIES.md đứng yên).

## Nên claim thêm gì — tóm tắt ưu tiên

1. **GH#102 (MỚI, skill behavioral integrity):** đã raise. Việc kế tiếp (không phải kỳ này) — thêm bước đối chiếu mô tả↔tool-call-thật vào `skill-provenance`, tham khảo taxonomy BIV để phân loại oversight-vs-adversarial khi báo cáo lệch.
2. **GH#11 (observability, treo 9 kỳ — vẫn là việc rẻ nhất chưa làm):** trace-log `Workflow` theo khung AHE 3 trụ — không có lý do kỹ thuật mới để trì hoãn thêm, chỉ còn là ưu tiên thời gian.
3. **GH#10/12 (self-evolving skills / orchestration scale):** không đổi thiết kế; watch-item product-surface đã đóng loop kỳ này.
4. **Theo dõi tiếp:** liệu Dreaming/Outcomes/Multiagent Orchestration có chảy xuống Claude Code CLI ở các kỳ tới không — nếu có, quét lại ngay, không chờ định kỳ.
5. Đã `gh issue comment` GH#10/11/12 (đóng loop watch-item) và `gh issue create` GH#102 (gap mới) kỳ này.

## Nguồn

- `~/orca/setup/setup/skills/last30days/scripts/last30days.py` (v3.3.2, cài lại đầy đủ project-local, chạy bằng `python3.13`, `--diagnose` xác nhận 5 nguồn keyless sống)
- last30days engine run: "Claude Code agent framework updates" (reddit+hackernews+github, 16 items, tín hiệu yếu)
- last30days engine run: "AI agent memory context engineering" (reddit+hackernews+github, 8 items, tín hiệu yếu)
- last30days engine run: "self-improving agents harness eval benchmark" — surfaced [Harness engineering for self-improvement — Lilian Weng](https://lilianweng.github.io/posts/2026-07-04-harness/) (đã cite từ 06/08, WebFetch lại xác nhận canon không đổi), [Prime Agent — Prime Intellect](https://www.primeintellect.ai/blog/prime-agent)
- last30days engine run: "AI agent skills marketplace supply chain security" (reddit+hackernews+github, 23 items)
- [Behavioral Integrity Verification for AI Agent Skills — arXiv 2605.11770v1](https://arxiv.org/abs/2605.11770v1)
- [AI Agent Skill Security Scanner — Mondoo](https://mondoo.com/ai-agent-security)
- [Malicious AI agent skills can slip past the scanners built to stop them — Help Net Security](https://www.helpnetsecurity.com/2026/07/09/malicious-ai-agent-skills-scan/) (đề cập Cisco Skill Scanner)
- WebSearch: "Claude Code CLI Dreaming OR Outcomes OR multiagent orchestration feature August 2026" — xác nhận Managed Agents vẫn API-only, public beta, header `managed-agents-2026-04-01`
- [SkillResolve-Bench: Measuring and Resolving Same-Capability Ambiguity in Agent Skill Retrieval — arXiv 2606.10388](https://arxiv.org/pdf/2606.10388) (trùng tên khái niệm với `new-skill` skill's BM25 dedup check — không hành động, chỉ ghi nhận trùng hướng)

## Origin
Nối tiếp [[innovation-070826]] sau khoảng trống 2 ngày (08-09/08 không quét). Kích hoạt bởi yêu cầu "cài last30days repo nếu chưa có + đánh giá repo so với ý tưởng mới trên thế giới, ra file so sánh cột cũ/mới" (phiên 2026-08-10). Phát hiện chính: (1) gap mới đủ chín — Behavioral Integrity Verification cho skill, đã raise GH#102; (2) watch-item chiến lược kỳ trước (Managed Agents chảy xuống CLI?) đóng loop với câu trả lời "chưa", đã comment GH#10/11/12.
