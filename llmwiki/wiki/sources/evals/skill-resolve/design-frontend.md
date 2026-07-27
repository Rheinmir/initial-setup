---
type: eval
id: design-frontend
query: "anti-slop frontend landing page portfolio redesign với design system thật"
expected: [hallmark, design-taste-frontend]
---

# skill-resolve golden: design-frontend

Câu người dùng gõ phải phân giải về skill đúng (chống chọn nhầm cùng-năng-lực).

Query chung chung về anti-slop + design system, KHÔNG nêu gu cụ thể → phải về **sàn** (hallmark) trước, taste skill xếp sau. `design-taste-frontend` vẫn trong expected: nó là flavour hợp lệ cùng năng lực, chỉ không được chiếm top-1 của query không-nêu-gu.

## Origin
- Raise bởi GH#13 (Skill-resolve ambiguity) — phiên 2026-07-04, expected gốc `[design-taste-frontend]`.
- **Cập nhật 2026-07-18:** quyết định [[design-foundation]] (absorb hallmark 150726, user duyệt) đặt hallmark làm SÀN mặc định — "việc chạm UI không nêu gu → sàn"; golden cũ mã hoá thế giới trước-hallmark nên lỗi thời, không phải eval-regression thật. Trigger: description hallmark khai thêm năng lực design.md (commit c38b17d) làm hallmark thắng hạng — đúng chủ ý.
