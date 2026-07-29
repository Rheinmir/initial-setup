---
type: issue
kind: tech-debt
title: "Skill-resolve ambiguity + supply-chain: chống 'cùng năng lực chọn nhầm' và audit nguồn skill"
status: resolved
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, skills, disambiguation, security, supply-chain, frontier-chom]
timestamp: 2026-07-03
id: 030726-skill-resolve-supplychain
source_session: "frontier-gap-scan baseline 03/07/2026 — trục CHỚM #2"
---

# Issue: Nhập nhằng skill + supply-chain chưa được đo/chặn

## Vấn đề (một câu)
Với 71 skill và nhiều biến thể cùng-năng-lực (tour-guide vs tour-guide-supademo, design-taste v1/v2…), rủi ro chọn nhầm skill tăng; thế giới đã có benchmark đo việc này (SkillResolve-Bench) và paper audit supply-chain skill — overstack chưa có cơ chế tương ứng.

## Bối cảnh & bằng chứng
- Trục Skill security/supply-chain = **Chớm**. Nguồn: frontier-gap-scan, report overstack-vs-world-30d.
- Thế giới: SkillResolve-Bench (arXiv 2606.10388) đo nhập nhằng cùng-năng-lực trong skill retrieval; "Formal Analysis & Supply Chain Security for Agentic AI Skills" (2603.00195); "Repository-Aware Security Analysis of Agent Skill Ecosystem" (2603.16572); NIST mở chuẩn agent (02/2026).
- overstack hiện: `orca-sec-scans` (Trivy static+dynamic), R-rule chặn ghi sai vùng, `build-skill-search.py`. Chưa có: đo/chặn 2-skill-cùng-trigger, audit provenance skill khi cài.

## Phạm vi
- `new-skill` (kiểm trùng trigger lúc scaffold), `build-skill-search.py`, marketplace.json, R-rules. Universal.

## Không thuộc phạm vi
- Không chặn cứng mọi biến thể (biến thể style hợp lệ — vd tour-guide-<tên>); chỉ cảnh báo + phân giải.

## Hướng gợi ý (không bắt buộc)
- `/new-skill`: rule kiểm "2 skill cùng trigger/năng lực" → cảnh báo + buộc phân biệt description.
- Provenance skill: ghi nguồn + checksum khi cài skill ngoài (bổ trợ orca-sec-scans).
- Mini golden theo tinh thần SkillResolve-Bench: tập câu → skill đúng, chặn regress retrieval.

## Tiêu chí HOÀN THÀNH
- `/new-skill` cảnh báo được khi trùng trigger với skill hiện có.
- Có mini golden retrieval skill gắn CI.

## Assign & lý do
- @Rheinmir chủ; Claude dispatch. Mở `/fdk`. P2 (chớm).

## Repo/paper tham khảo
- SkillResolve-Bench — arXiv 2606.10388 (đo & giải nhập nhằng cùng-năng-lực trong skill retrieval).
- "Formal Analysis & Supply Chain Security for Agentic AI Skills" — arXiv 2603.00195.
- "Context Matters: Repository-Aware Security Analysis of Agent Skill Ecosystem" — arXiv 2603.16572.
- "Knowledge Activation: AI Skills as Institutional Knowledge Primitive" — arXiv 2603.14805 (nền lý thuyết skill).
- `jeremylongshore/claude-code-plugins-plus-skills` (tonsofskills, ccpi CLI) — mẫu marketplace + package manager có provenance.

## Resolution (2026-07-04, GH#13)
Cả 3 tiêu chí HOÀN THÀNH đạt:
- **Cảnh báo trùng-năng-lực khi scaffold** — `fdk/tools/new-skill.py` gọi engine BM25 của `build-skill-search.py` với (name+desc) skill sắp tạo; top-1 ≥ ngưỡng 12.0 (calibrate: biến thể trùng ≈26–44, skill mới lạ ≈7) → in block `⚠ TRÙNG NĂNG LỰC?` + top-3; flag `--strict` chặn cho CI. Chỉ cảnh báo, không chặn cứng biến thể hợp lệ (đúng phạm vi).
- **Mini golden retrieval (SkillResolve-Bench spirit)** — `harness/scripts/skill-resolve-eval.py` + 18 golden `llmwiki/wiki/sources/evals/skill-resolve/*.md` (gồm cặp nhập nhằng thật: tour-guide↔supademo, design-taste↔v1, raise-issue↔orca-issue, medic↔health-check, ship↔snapshot-push…). Hiện hit@1 18/18; baseline chốt, `--check` exit 2 khi regress, gắn CI `skills-sync.yml`.
- **Provenance skill** — `skill-provenance` (+ tool `fdk/tools/skill-provenance.py`) ghi nguồn+sha256 mọi file skill vào `fdk/skills.provenance.json`; `check --ci` báo MODIFIED/UNTRACKED chặn skill lạ hoặc bị-sửa; backfill 74 skill = `local-authored`. Bổ trợ (không thay) `orca-sec-scans`.

Trục #5 frontier-gap-scan chuyển **Chớm → có cơ chế**. Tái-kiểm kỳ scout sau.

## Origin
Raise bởi phiên frontier-gap-scan 2026-07-03. Bằng chứng: report overstack-vs-world-30d + frontier-gap-scan.
