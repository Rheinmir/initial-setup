---
type: eval
id: capproof-liveness
title: "Capproof — phân biệt năng lực CÓ MẶT với năng lực CÒN SỐNG"
input: "Trong overstack, làm sao biết một năng lực (skill/rule/tool) còn sống thật chứ không chỉ có mặt trên đĩa, và nợ bằng chứng được gác thế nào?"
expected: "CAPABILITIES.md map mỗi năng lực sang bằng chứng chạy được (resolver 6 tầng: proof: frontmatter > rule-map harness-doctor > harness/tests > --self-test > golden > medic); không có bằng chứng → mục UNPROVEN. Medic probe capproof gác kiểu ratchet: nợ tồn trong baseline chỉ đếm, năng lực MỚI thiếu proof hoặc proof bị mất → đỏ."
asserts:
  - 'icontains:unproven'
  - 'regex:(?i)(capproof|bằng chứng)'
  - 'regex:(?i)ratchet|nợ'
rubric: "ĐẠT nếu nêu được cơ chế proof-map (bằng chứng chạy được cho từng năng lực), mục UNPROVEN, và ratchet (nợ cũ đếm, nợ mới đỏ). KHÔNG đạt nếu chỉ nói 'có test' chung chung."
---

# Golden: capproof-liveness

Câu hỏi user thật của phiên 2026-07-18 ("checklist năng lực tự soi + tự cộng"), đáp án là cơ chế đã ship và fire-drill (T-260718-01). Nguồn: `wiki/sources/draft/180726-capability-proof-map.md`, `fdk/tools/build-capabilities.py`.

## Origin
- Distill từ vòng T-260718-01 (đã ship, medic 13/13) bởi vòng grower 2026-07-18 — golden neo tri thức vận hành vào eval hồi quy.
