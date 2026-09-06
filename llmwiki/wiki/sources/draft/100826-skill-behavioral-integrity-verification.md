---
type: issue
kind: feature-gap
title: "skill-provenance thiếu lớp Behavioral Integrity Verification (mô tả khai báo ≠ hành vi thật lúc chạy)"
status: open
assignee: Rheinmir
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, skill-security, supply-chain, observability]
timestamp: 2026-08-10
id: 100826-skill-behavioral-integrity-verification
source_session: "/frontier-scan thủ công 10/08/2026, kỳ tiếp nối innovation-070826"
---

# Issue: skill-provenance thiếu lớp Behavioral Integrity Verification

## Vấn đề (một câu)
`/skill-provenance` hiện chỉ kiểm nguồn (URL/commit) + sha256 checksum tĩnh khi cài skill — không có bước đối chiếu "SKILL.md khai báo làm gì" với "tool-call/side-effect thật khi skill chạy", trong khi thế giới đã có framework hình thức + sản phẩm thương mại làm đúng lớp này.

## Bối cảnh & bằng chứng
Kỳ scan trước (`llmwiki/innovation/070826-innovation.md`, mục 4) đã ghi nhận đây là "hạt giống" chưa đủ chín — chỉ có 1 khảo sát 42k-skill nói 80% mismatch, chưa đủ để raise. Quét lại hôm nay (10/08) phát hiện đã leo thang thành:

1. **BIV (Behavioral Integrity Verification)** — framework hình thức, arXiv 2605.11770v1 ("Behavioral Integrity Verification for AI Agent Skills"): định nghĩa bài toán như typed-set-comparison giữa capability khai báo và capability thật, qua một taxonomy chung nối code + instruction + metadata. Test trên registry OpenClaw: 250,706 behavioral deviations, 80.0% skill (39,933/49,918) có ≥1 mismatch. Root-cause: 81.1% oversight (không cố ý), 18.9% adversarial intent, 5.0% skill có multi-stage attack chain dự đoán được.
2. **Mondoo "AI Agent Skill Security Scanner"** — Layer 3 chạy LLM-powered threat analysis, phát hiện behavior-mismatch giữa mục đích khai báo và hành vi thật.
3. **Cisco "Skill Scanner"** — kết hợp pattern-based detection + LLM-as-a-judge + behavioral dataflow analysis.

Đây là lớp phòng thủ KHÁC, bổ sung (không thay thế) provenance tĩnh hiện có ở `fdk/tools/skill-provenance.py`. Liên quan nhưng KHÔNG trùng [GH#13](https://github.com/Rheinmir/setup/issues/13) (đã done/closed — phạm vi đó là source+hash tĩnh lúc cài, không kiểm hành vi runtime).

## Phạm vi
- `fdk/tools/skill-provenance.py` (thêm bước kiểm behavioral-integrity, không sửa logic provenance tĩnh hiện có).
- Có thể chạm `harness/scripts/medic.py` nếu muốn gate behavioral-check vào `medic --ci`.
- Universal (framework-level), không phải một dự án con cụ thể.

## Không thuộc phạm vi
- Không sửa lại provenance tĩnh (source+sha256) đã có — vẫn giữ nguyên.
- Không tự viết lại toàn bộ skill-security scanner (không cần bằng Cisco/Mondoo) — chỉ cần một bước đối chiếu mô tả↔hành vi đủ dùng nội bộ.
- Không raise trùng GH#13 (đã closed, phạm vi khác).

## Hướng gợi ý (không bắt buộc)
So khớp mô tả trong SKILL.md/frontmatter (`description`, các tool được liệt trong body) với tool-call thật quan sát được qua transcript/log khi skill chạy lần đầu hoặc lúc review — dùng LLM-as-judge (giống Cisco/Mondoo) hoặc rule tĩnh đơn giản trước (regex tool-name trong description vs tool thật gọi), cảnh báo nếu lệch quá ngưỡng. Tham khảo taxonomy BIV để phân loại oversight-vs-adversarial khi báo cáo, tránh gộp chung mọi lệch thành "nguy hiểm".

## Tiêu chí HOÀN THÀNH
- `skill-provenance` (hoặc tool mới cạnh nó) có thể chạy một pass đối chiếu description↔tool-call-thật cho ≥1 skill thật trong repo và ra kết quả match/mismatch có giải thích.
- Có ít nhất 1 test/demo tái hiện được (một skill cố tình khai sai để kiểm cảnh báo có bắn không).
- Ghi lại trong wiki `skill-provenance` sự khác biệt giữa lớp tĩnh (đã có) và lớp behavioral (mới) để không nhầm hai lớp khi trả lời câu hỏi so sánh.

## Assign & lý do
`@Rheinmir` / dispatch `Claude` / mở bằng `/fdk` — đây là gap tầng framework (không phải dự án con), tiếp nối trực tiếp công cụ `skill-provenance` đã có, hợp để Claude tự triển khai khi rảnh tay.

## Origin
Raised bởi phiên frontier-scan thủ công 2026-08-10 (tiếp nối `llmwiki/innovation/070826-innovation.md`, gap chuỗi 3 kỳ: 070826 nêu hạt giống → 100826 xác nhận đủ chín để raise). Bằng chứng: arXiv 2605.11770v1, Mondoo AI Agent Skill Security Scanner, Cisco Skill Scanner, arXiv 2603.00195 (đã cite ở GH#13 gốc).
