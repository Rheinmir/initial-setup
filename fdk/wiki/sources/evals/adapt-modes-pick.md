---
type: eval
id: adapt-modes-pick
title: "Adapt-modes — chọn kiểu absorb nào khi bản chất nhỏ + cần gác tất định"
input: "Absorb một năng lực ngoài vào overstack có những kiểu nào, và chọn kiểu nào khi bản chất nhỏ gọn, muốn gác tất định, không muốn dependency ngoài?"
expected: "Ba kiểu: HÒA TAN (dissolve — distill ý, viết lại thành của mình), KÉO NGOÀI (external-pull — pin + provenance, engine ở ngoài), NHÚNG-SỞ-HỮU (vendor bytes). Bản chất nhỏ + gác tất định + 0 dep → chọn HÒA TAN."
asserts:
  - 'contains:HÒA TAN'
  - 'contains:KÉO NGOÀI'
  - 'regex:(?i)(dissolve|hòa tan)'
rubric: "ĐẠT nếu nêu đủ 3 kiểu adapt-modes và chọn đúng HÒA TAN cho ca bản-chất-nhỏ/gác-tất-định/0-dep. KHÔNG đạt nếu thiếu kiểu hoặc chọn sai."
---

# Golden: adapt-modes-pick

Sinh từ query THẬT của phiên 2026-07-17 (`/query` tiền lệ absorb trước vòng T-260717-02) — câu hỏi người dùng thật, đáp án đã kiểm chứng bằng chính vòng absorb thành công sau đó. Nguồn tri thức: `llmwiki/wiki/concepts/adapt-modes.md`.

## Origin
- Query-log 2026-07-17 (tier 2, pages: adapt-modes, ADR-003, design-foundation) → distill thành golden bởi vòng grower 2026-07-18 (T-260718 khép vòng đo).
