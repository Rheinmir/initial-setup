---
title: "Overstack vs thế giới — 31/07/2026"
status: living
tags: [innovation, frontier, comparison, gap-analysis]
timestamp: 2026-07-31
id: innovation-310726
---

# Overstack vs thế giới — rà soát 31/07/2026

Tiếp nối [[innovation-300726]] (1 ngày trước). Kỳ này **`last30days` lần đầu cài đủ bộ** — 4 kỳ trước ghi "`SETUP_COMPLETE=true`" nhưng đó chỉ là marker onboarding; `~/.claude/skills/last30days/` thực chất chỉ có `SKILL.md` (127.7K, không `scripts/`) — engine `last30days.py` không tồn tại trên máy nên mọi lần gọi trước đây rơi vào nhánh lỗi Python-version rồi bị bỏ qua. Đã tải repo thật (`github.com/mvanhorn/last30days-skill`, tarball `main` 12MB vì `git clone` qua egress-guard bị treo) và cài `scripts/` + `agents/` + `references/` vào đúng đường thật (`~/.agents/skills/last30days`, symlink từ `~/.claude/skills/last30days`), nâng `SKILL.md` từ v3.3.2 lên v3.18.4 khớp bản. Chạy được bằng `python3.13` (Homebrew, vì hệ dùng `python3` mặc định là 3.9.6 — đúng vướng mắc kỳ 29/07 đã ghi nhận) — xác nhận **4/5 nguồn lõi sống** (Reddit, HN, GitHub, YouTube; thiếu X/Twitter vì chưa cấp cookie/API key).

Đối chiếu lại `fdk/CAPABILITIES.md` (vẫn 84 skill · 18 rule · 19 fdk-tool · 63 harness-script — không đổi 4 kỳ liên tiếp) và ledger `llmwiki/wiki/sources/ISSUES.md`: GH#9, GH#13 vẫn `done`; **GH#10, GH#11, GH#12 vẫn `open`** — đây là 3 trục quét sâu kỳ này (`last30days` + 3 WebSearch có mục tiêu, thay vì 5 WebSearch cố định như runbook mặc định, vì engine giờ đã dùng được thật).

## Bảng đối chiếu — cột CŨ (overstack đang có) và MỚI (thế giới, tính đến 31/07)

| Trục | 🔵 CŨ — Overstack đang có | 🟢 MỚI — Thế giới (đến 31/07) | Verdict | Nên claim thêm |
|---|---|---|---|---|
| **Self-evolving skills (GH#10, vẫn `open`)** | `failure-flywheel` — weakness-mining thủ công, cluster lỗi bằng tay, người-trong-vòng-lặp | `last30days` tìm được: (1) một PR thật (`aleksandrlyubarev-blip/Romeo_PHD`, 06/07) áp đúng **loop 3 giai đoạn từ arXiv:2606.09498** — "weakness mining -> minimal harness proposals -> held-in/held-out validation with a non-regression rule" — GẦN NHƯ TRÙNG khung `failure-flywheel` đang dùng, nay đã có người triển khai thật ngoài overstack; (2) `SkillCuratorPlugin` (PraisonAI-Plugins, 10/07) — plugin lifecycle **tự động** giữ "auto-authored skill library" khoẻ bằng provenance + usage telemetry + archive khôi phục được, không cần người theo dõi | **Ngang về khung lý thuyết** (paper xác nhận đúng hướng `failure-flywheel`), **Thua về tự-động-hoá bước cluster** (SkillCuratorPlugin làm tự động cái mà `failure-flywheel` vẫn làm tay) — không đổi so với nhận định 30/07, nhưng nay có ví dụ CODE THẬT để tham chiếu thay vì chỉ có paper | Khi tự động hoá bước cluster của `failure-flywheel` (việc còn thiếu, đã nêu 2 kỳ liên tiếp), tham khảo TRỰC TIẾP 2 nguồn code thật này thay vì chỉ paper: cách `SkillCuratorPlugin` dùng usage-telemetry để quyết định archive/giữ skill tự-sinh, và cách PR RoboQC ánh xạ non-regression rule vào "held-in/held-out validation" cụ thể |
| **Observability runtime (GH#11, vẫn `open`, quét lại lần đầu từ 03/07)** | Chỉ eval tĩnh (`medic`, retrieval-eval, skill-resolve-eval chạy CI) — không có tracing/simulation lúc runtime | Galileo (Cisco mua lại 04/2026) có Graph View (từ 07/2026, 2 chế độ Aggregated/Expanded — mỗi lệnh gọi agent là 1 node), Trace View debug từng bước, và **guardrail runtime tự-sửa** (self-correction loop chặn output xấu TRƯỚC khi tới user, cả pre- lẫn post-LLM check); Arthur gộp tracing+eval+guardrail vào một Agent Development Toolkit thay vì ghép nhiều vendor | **Thua rõ, không đổi** — đây là trục overstack yếu nhất trong 3 trục `open`, đã 4 tuần chưa có cơ chế nào dù chỉ ở mức thô sơ | Bước rẻ nhất trước khi tính đến nền tảng ngoài: thêm 1 lớp trace-log thô cho `orca`/`Workflow` tool — mỗi lệnh gọi agent ghi step (input/output rút gọn + timestamp) vào file cục bộ, KHÔNG cần tích hợp Galileo/Arthur ngay — đủ để trả lời "agent nào làm gì lúc nào" khi debug, rồi nâng cấp lên guardrail runtime khi thật sự cần |
| **Orchestration scale (GH#12, vẫn `open`, quét lại lần 2 sau 30/07)** | `orca` 3-10 agent song song qua `Workflow` tool (pipeline/parallel), pattern supervisor (1 agent điều phối, không tự spawn nested subagent — giới hạn nền tảng Claude Code) | Xác nhận: **supervisor topology là default sản xuất 2026** (Claude Code subagent, LangGraph Supervisor, OpenAI Agents SDK handoffs đều hội tụ về cùng pattern overstack đã chọn) — không lệch hướng; nhưng về QUY MÔ, Kimi K2.5 điều phối 100 sub-agent với 1.500 tool-call song song qua **Parallel-Agent Reinforcement Learning**, Kimi K2.6 scale tới 300 agent | **Ngang về pattern** (supervisor, xác nhận lần 2 liên tiếp — không mở gap mới), **Thua về kỹ thuật throughput ở quy mô cực lớn** (Parallel-Agent RL cho 1.500 tool-call/lượt) — nhưng khoảng cách không cấp thiết vì orca mới cần 3-10 agent, chưa chạm ngưỡng "two-phase agent discovery" (kỹ thuật nêu 30/07) hay Parallel-Agent RL | Không cần làm ngay — quy mô hiện tại (3-10 agent) còn xa ngưỡng 100+. Ghi nhận Parallel-Agent RL làm tài liệu tham chiếu THỨ HAI (sau "two-phase agent discovery" của 30/07) cho lúc `Workflow` tool cần scale vượt ~20 agent |
| **MCP protocol supply-chain (tiếp nối lo ngại nêu 30/07 — OX Security, chưa raise issue)** | Chưa xác minh overstack có tự nhúng MCP client/server ngoài Claude Code hay không (câu hỏi treo từ báo cáo 30/07) | **MCP vừa ra spec mới 2026-07-28** — "stateless core, stronger OAuth and OIDC authorization, versioned extensions" — đây có khả năng là bản vá kiến trúc trực tiếp nhắm đúng loại lỗ hổng OX Security nêu hôm 30/07 (điểm yếu kiến trúc trong chính SDK) | **Tín hiệu tích cực, chưa xác minh xong** — nếu Claude Code (nền tảng overstack chạy trên) đã áp dụng spec 2026-07-28, rủi ro nêu hôm 30/07 giảm nhẹ đáng kể; nếu chưa, rủi ro vẫn treo y nguyên | Việc rẻ, ưu tiên cao kỳ này: kiểm 1 dòng xem Claude Code hiện dùng MCP spec version nào — nếu đã lên `2026-07-28`, có thể đóng luôn phần "theo dõi MCP SDK" còn treo từ 30/07 mà không cần raise issue mới; nếu chưa, giữ nguyên mục theo dõi |
| **Vận hành tool nghiên cứu (`last30days`, không phải trục cạnh tranh overstack-vs-thế-giới, nhưng là finding đáng ghi)** | 4 kỳ liên tiếp (27/07-30/07) báo "`last30days` đã cài, `SETUP_COMPLETE=true`" — nhưng đó chỉ là marker onboarding, KHÔNG đồng nghĩa engine chạy được | Kỳ này phát hiện `~/.claude/skills/last30days/` chỉ có `SKILL.md`, thiếu toàn bộ `scripts/` — mọi lần gọi trước đây thực chất rơi vào lỗi Python 3.9.6 rồi bị âm thầm bỏ qua (kỳ 29-30/07 đều chủ động chuyển sang 5 WebSearch tay vì lý do này). Đã tải + cài đủ `scripts/last30days.py` (v3.18.4) qua `python3.13`, xác nhận chạy thật, thu được 47 evidence item (Reddit/HN/GitHub) cho kỳ này | N/A (bài học vận hành, không phải Ngang/Thua) | **Sửa cách kiểm tra "đã cài chưa" trong runbook `frontier-gap-scan`**: đừng chỉ tin `SETUP_COMPLETE=true` trong `.env` — đó là marker onboarding, không phải bằng chứng engine tồn tại. Kiểm tra thật: `test -f $(readlink -f ~/.claude/skills/last30days)/scripts/last30days.py`. Việc này giải thích tại sao 3 kỳ liên tiếp (27-29/07) coi `last30days` là "công cụ chưa tối ưu" — thực ra nó chưa từng chạy được, không phải vấn đề chất lượng nguồn |

## Tín hiệu đáng chú ý nhất kỳ này — khác gì với 30/07

**1. `last30days` lần đầu chạy được thật sau 4 kỳ báo nhầm "đã cài".** Đây là phát hiện vận hành quan trọng nhất kỳ này: gap giữa "marker onboarding ghi `SETUP_COMPLETE=true`" và "engine thực sự có trên đĩa" đã khiến 3-4 kỳ trước đánh giá sai chất lượng công cụ. Sau khi cài đúng (`scripts/` + `python3.13`), công cụ cho ra bằng chứng thật — cụ thể là tìm ra 1 PR thật áp dụng đúng loại kỹ thuật `failure-flywheel` đang dùng (arXiv:2606.09498), điều mà 5 WebSearch tay các kỳ trước không bắt được vì WebSearch không sâu tới cấp GitHub PR/issue.

**2. GH#10 (self-evolving skills) có bằng chứng CODE THẬT lần đầu, không chỉ paper.** Các kỳ trước (03/07, 30/07) chỉ trích dẫn tên framework (CoEvoSkills, SkillForge) hoặc paper học thuật (DemoEvolve). Kỳ này `last30days` tìm ra 2 repo thật đang vận hành đúng ý tưởng: `SkillCuratorPlugin` (tự động hoá phần `failure-flywheel` còn thiếu) và PR RoboQC (áp trực tiếp loop 3 giai đoạn của paper vào một agent QC thật).

**3. GH#12 (orchestration scale) được xác nhận LẦN 2 liên tiếp là Ngang về pattern (supervisor).** Không mở gap mới — nhưng có thêm 1 con số cụ thể (Kimi K2.5: 100 agent / 1.500 tool-call qua Parallel-Agent RL) làm mốc tham chiếu thứ hai cùng "two-phase agent discovery" của 30/07.

**4. Tín hiệu MCP 2026-07-28 có thể đóng một phần lo ngại treo từ 30/07 (OX Security).** Chưa xác minh xong nhưng đây là việc rẻ, nên làm sớm.

**5. GH#11 (observability runtime) vẫn là trục yếu nhất — 4 tuần liên tiếp `Thua` không đổi.** Khác các trục kia (đều có ít nhất 1 tín hiệu Ngang hoặc kỹ thuật cụ thể để tham chiếu), GH#11 chưa có gì để bám ngoài "eval tĩnh". Bước rẻ nhất (trace-log thô, không cần platform ngoài) nên được ưu tiên hơn tiếp tục chỉ quan sát.

## Nên claim thêm gì — tóm tắt ưu tiên

1. **Sửa runbook `frontier-gap-scan`**: đổi tiêu chí "đã cài `last30days` chưa" từ đọc `SETUP_COMPLETE=true` sang kiểm tra thật `scripts/last30days.py` có tồn tại — tránh lặp lại sai lầm 4 kỳ liên tiếp.
2. **GH#10 (self-evolving, vẫn open)**: khi tự động hoá bước cluster của `failure-flywheel`, tham khảo trực tiếp code `SkillCuratorPlugin` (PraisonAI-Plugins PR #12) và PR RoboQC (áp dụng arXiv:2606.09498) — có ví dụ thật thay vì chỉ suy luận từ paper.
3. **GH#11 (observability, vẫn open, yếu nhất)**: thêm trace-log thô cho `orca`/`Workflow` tool trước — bước rẻ, không cần tích hợp Galileo/Arthur ngay, giải quyết đúng nhu cầu debug "agent nào làm gì lúc nào".
4. **Xác minh 1 dòng: Claude Code có dùng MCP spec 2026-07-28 chưa** — nếu có, đóng bớt lo ngại OX Security treo từ 30/07 mà không cần raise issue mới.
5. **GH#12 (orchestration scale)**: không cần làm ngay (quy mô hiện tại 3-10 agent còn xa ngưỡng), chỉ ghi nhận Parallel-Agent RL làm tài liệu tham chiếu thứ hai.
6. **GH#9, GH#13 (đã đóng)**: không quét lại kỳ này — không có tín hiệu thay đổi hướng từ 2 kỳ liên tiếp trước.

## Nguồn

- `~/Documents/Last30Days/self-improving-ai-agent-harness-skill-evolution-observability-orchestration-scale-raw-v3.md` (raw output `last30days` v3.18.4, chạy 31/07/2026, 47 evidence item: 13 GitHub, 19 HN, 15 Reddit)
- [feat(marketing): store story + self-improving under your control — IgorGanapolsky/ThumbGate PR #3004](https://github.com/IgorGanapolsky/ThumbGate/pull/3004)
- [feat(thumbgate): Self-Improving Firewall pitch — IgorGanapolsky/mac-yolo-safeguards PR #854](https://github.com/IgorGanapolsky/mac-yolo-safeguards/pull/854)
- [Most "self-improving" AI agents don't improve (Hacker News)](https://loadbearingtech.substack.com/p/self-improving-agent-loops-verifier)
- [CERN: Genesis Mission will develop and deploy self-improving AI models [pdf]](https://indico.cern.ch/event/1662511/contributions/6989580/attachments/3241179/5781542/Genesis%20Mission%20and%20HEP%20-%20LHC.pdf)
- [feat(tuning): self-improving formation P3 — muxi-ai/runtime PR #285](https://github.com/muxi-ai/runtime/pull/285)
- [feat: add skill-library curator plugin for self-improving agents — MervinPraison/PraisonAI-Plugins PR #12](https://github.com/MervinPraison/PraisonAI-Plugins/pull/12)
- [Add Self-Harness for RoboQC: design doc and working loop prototype — aleksandrlyubarev-blip/Romeo_PHD PR #9 (arXiv:2606.09498)](https://github.com/aleksandrlyubarev-blip/Romeo_PHD/pull/9)
- [6 Best AI Agent Observability Platforms (2026) — Galileo](https://galileo.ai/blog/best-ai-agent-observability-platforms)
- [Choosing an AI Observability Platform in 2026 — Arthur](https://www.arthur.ai/column/what-to-look-for-ai-observability-platform-2026)
- [Agent observability: The complete guide for 2026 — Braintrust](https://www.braintrust.dev/articles/agent-observability-complete-guide-2026)
- [AI Agent Observability 2026: Tracing & Monitoring Stack](https://www.digitalapplied.com/blog/ai-agent-observability-2026-tracing-monitoring-stack-guide)
- [Multi-Agent Orchestration: 5 Patterns That Work in 2026](https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work)
- [Best Multi-agent Orchestration Frameworks in 2026 — TrueFoundry](https://www.truefoundry.com/blog/multi-agent-orchestration-frameworks)
- [How to Orchestrate Multi-Agent AI Systems at Scale in 2026 — Atlan](https://atlan.com/know/multi-agent-system-orchestration/)
- [Multi-Agent AI Orchestration Guide & 2026 Updates — Codebridge](https://www.codebridge.tech/articles/mastering-multi-agent-orchestration-coordination-is-the-new-scale-frontier)
- [Week 28 · July 6–10, 2026 — Claude Code Docs](https://code.claude.com/docs/en/whats-new/2026-w28)
- [AI Agent Frameworks (2026 Update): 8 SDKs Compared — morphllm](https://www.morphllm.com/ai-agent-framework)
- [Claude Developer Platform Updates by Anthropic — July 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude-developer-platform)
- [Claude Code Updates by Anthropic — July 2026 (Releasebot)](https://releasebot.io/updates/anthropic/claude-code)
