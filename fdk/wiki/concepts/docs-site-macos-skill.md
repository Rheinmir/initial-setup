---
type: concept
title: docs-site-macos (skill)
status: stub
tags: [skill, docs-site-macos, glass, theme, R11]
timestamp: 2026-06-27
id: docs-site-macos-skill
relations:
  - {rel: depends-on, to: onboarding-tour}
---

# docs-site-macos (skill)

Skill sinh trang docs/HTML theme macOS **liquid-glass** (white glass trên nền blue gradient, traffic-light chrome, animated SVG diagram). Là **chuẩn style của seq HTML** mà [[rule-registry|R11]] enforce, và theme render on-demand cho output [[cursor-explain-site|extract-site Mode 3]].

Canonical: `skills/docs-site-macos/SKILL.md` → mirror `llmwiki/skills/utils/docs-site-macos.md`. (Bản trùng `skills/docs-site-macos-skill/` đã được hợp nhất vào đây — 2026-06-28; file concept này giữ tên cũ để wikilink `[[docs-site-macos-skill]]` không vỡ.)

Cơ chế bảy-phase mà skill đi qua mỗi lần sinh một trang (nhận yêu cầu → palette/background → page architecture → diagram → interaction layer nav/toggle/theme → a11y/self-contained → xuất file + auto-host) được minh hoạ đầy đủ bằng sequence diagram tại `llmwiki/html/200826-docs-site-macos-how-it-works-seq.html`, trích số dòng thật từ SKILL.md cho từng bước.

Hai vùng đang được nâng cấp qua proposal `T-260820-01` (`llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md`, đang chờ duyệt): (1) engine diagram — thay heuristic rect-detection bằng Mermaid auto-layout thật (`beautiful-mermaid`) cho diagram phức tạp; (2) bug positioning `.theme-row{bottom:-<pad-nav>}` (SKILL.md dòng 807) gây lệch nút toggle dark/light, sửa bằng CSS custom property `--nav-pad-y`.

## Origin
- Stub tạo để giải broken wikilink `[[docs-site-macos-skill]]` từ [[cursor-explain-site]] (2026-06-27) — theo precedent stub [[R10]].
- Skill thật: `llmwiki/skills/utils/docs-site-macos.md`.
