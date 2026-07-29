---
type: draft
title: "Distill vào /br — stream UI/UX thống nhất (hallmark) + spec rõ mọi mắt xích (orca-workflow)"
status: proposed
tags: [br, hallmark, orca-workflow, design-system, spec, distill]
timestamp: 2026-07-16
---
**Type:** draft
**Status:** proposed
**Proposed:** 2026-07-16

## What
Distill 2 cơ chế vào dây chuyền `/br` để bịt 2 lỗ hổng của pipeline nhiều-frame: (A) mockup các frame lệch nhau (không thống nhất UI/UX), (B) frame/field mơ hồ, thiếu spec.

## Context
`/br` cắt tài liệu thô → nhiều frame, mỗi frame chạy độc lập qua loop-runner. Hai hệ quả: mỗi frame dễ tự chế màu/spacing riêng (UI chắp vá), và frame/field interview dễ khai mơ hồ. Có sẵn `br/DESIGN.md` (NFR clause) + frame-template 4 section + interview S1–S10, nhưng KHÔNG có cơ chế ÉP nhất quán/spec — chỉ là lời dặn.

## Cơ chế A — stream UI/UX thống nhất (distill `hallmark`)
Nguồn: `~/.claude/skills/hallmark` (references/*, verbs/redesign). Ba trụ:
1. **`design.md` = hệ thiết kế KHOÁ ở gốc project** — đọc TRƯỚC, đè mọi lựa chọn (genre/theme/type/motion defer về nó).
2. **Luật ĐẢO NGƯỢC diversification** — dự án có design.md thì các trang phải *chia sẻ hệ, GIỐNG nhau*, không đa dạng hoá. Đây chính là "thống nhất xuyên trang/frame".
3. **Locked tokens, không ứng biến giữa render** — mọi màu + font trỏ token có tên (`var(--color-accent)`); cấm inline hex/OKLCH/`font-family:"…"`; thiếu token thì thêm vào block rồi trỏ.

**Áp vào /br:** `br/DESIGN.md` §4.1 nay là "token khoá + luật đảo ngược"; frame UI (`## UI hoạt động ra sao`) chỉ dùng token DESIGN.md, cấm inline; drift bị `/qc-uiux` (consistency) + engine visual-qa bắt tất định → stream chạy bằng GATE, không bằng lời dặn.

## Cơ chế B — spec rõ mọi mắt xích (học `/orca-workflow`)
Nguồn: propose sinh **FR** (id bền `**FR-01**: hệ thống PHẢI…`) + **SC** (đo NGƯỜI, không đo máy) + acceptance là bằng chứng của SC. Mang rigor đó xuống:
- **Frame:** frame-template thêm section `## Spec (FR/SC)`; frame-lint R7 (`REQUIRED_BODY_SECTIONS`) gác cứng — frame thiếu FR/SC = chưa xong. Mỗi dòng nghiệm thu truy về một FR (frame→FR→clause).
- **Interview:** mỗi field S1–S10 hỏi ra phải nêu field làm gì + tiêu chí "trả lời thế nào là ĐỦ"; field `missing/assumed` = spec chưa đủ, hiện ở bảng "Giả định đang gánh".

## Files
| File | Action |
|------|--------|
| `skills/br/assets/design-template.md` | +§4.1 token khoá + luật đảo ngược |
| `skills/br/assets/frame-template.md` | +section `## Spec (FR/SC)` + note token-stream cho UI |
| `fdk/tools/frame-lint.py` | `REQUIRED_BODY_SECTIONS` +`## Spec`; fixture selftest cập nhật |
| `skills/br/SKILL.md` | +doctrine "Stream UI thống nhất + Spec rõ ràng"; Mode 1/3 cập nhật |

## Origin
- **Draft:** `wiki/sources/draft/160726-br-ui-stream-spec-distill.md`
- **Commit:** _(verify-before-commit điền)_
- **Date promoted:** _(verify-before-commit điền)_
