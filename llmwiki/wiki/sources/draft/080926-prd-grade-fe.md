---
type: draft
title: "/prd-grade-fe — hub dựng frontend production-grade: hallmark giữ hệ thiết kế xuyên màn hình, impeccable kiểm soát biến"
status: proposed
tags: [skill, frontend, hallmark, impeccable, design-system, anti-slop, adapt-modes]
timestamp: 2026-09-08
---

# 080926-prd-grade-fe

**Status:** proposed

## What
Tạo skill hub `/prd-grade-fe`: phỏng vấn nguồn theme (mặc định macOS glassmorphism · trỏ tài liệu thiết kế · paste URL trang đích) → khoá toàn bộ thông số vào `design.md` (hallmark) và `.impeccable/` (impeccable) từ MỘT nguồn → dựng UI kỷ luật → chạy vòng audit tất định + LLM dọn AI-slop/anti-pattern → mới deliver.

## Context
Hai năng lực đã có nhưng đứng rời:

- **hallmark** (`skills/hallmark/SKILL.md`, 68.8K + 27 file references) — sàn design anti-slop. Có sẵn: gate 3 câu hỏi (Audience/Use case/Tone), 20 theme catalog + custom OKLCH, `study <URL>` trích DNA từ trang thật qua WebFetch, `design.md` khoá hệ xuyên màn hình (references/design-md.md — khi có file này luật đảo chiều: mọi màn hình PHẢI chung hệ), slop-test 58 gate, `audit`/`redesign`.
- **impeccable** (bundle `doyourmagic/impeccable/`, kiểm chứng trên `impeccable@3.6.1`) — 61 luật tất định `npx impeccable detect` (rc 0 sạch / 1 lỗi vận hành / 2 có finding), đọc `.impeccable/design.json` + `DESIGN.md` để biết token hợp lệ; 23 lệnh chat (`audit`, `harden`, `polish`, `document`…). CLI **chưa cài** trên máy này (`npx --no-install impeccable` → missing packages); skill chat cũng chưa cài trong `~/.claude/skills`.

Khoảng trống user chỉ ra: không có MỘT cửa để (1) chọn nguồn thông số, (2) đổ cùng bộ thông số vào cả hai công cụ mà không drift, (3) bắt buộc đi vòng audit trước khi giao. Hiện mỗi phiên tự ghép tay → mỗi màn một kiểu, và detect tất định chưa từng chạy trong repo này.

Bẫy đã đo trong bundle, skill phải né:
- `npx impeccable install --help` **cài thật** (không có nhánh help) → skill KHÔNG bao giờ gọi `install`.
- Target không tồn tại → `Warning: cannot access` rồi **rc 0** → phải assert file tồn tại trước khi detect.
- `npx` gộp stderr vào stdout → dùng `--json` (stdout) để máy đọc, không dựa vào `2>`.
- `--scope type` tách rời nuốt target → luôn viết dính `--scope=type`.
- Glass/translucent dễ dính `low-contrast`, `gpt-thin-border-wide-shadow` (chính `index.html` của bundle dính 18 finding lượt đầu) → preset mặc định PHẢI được audit trước khi điền.

**Phát hiện lúc soi tarball `impeccable@3.6.1`** (`cli/engine/design-system.mjs`): impeccable đọc `DESIGN.md`/`design.md` ở **gốc project** — đúng path hallmark khoá hệ — và chỉ dùng **frontmatter YAML** (`colors:{}`, `typography:{role:{fontFamily,fontSize}, scale:{}}`, `rounded:{}`; OKLCH được parse). Sidecar `.impeccable/design.json` là tuỳ chọn. Vậy MỘT file `design.md` gánh cả hai: frontmatter cho impeccable, thân markdown + block token cho hallmark; `design-sync.py` chỉ cần sinh frontmatter + `tokens.css` từ block token. Tarball npm KHÔNG chứa skill chat; rubric lấy từ repo GitHub `pbakaus/impeccable` `plugin/skills/impeccable/reference/*.md` (sparse-clone, sha `2bc2879`).

Adapt-modes (memory `adapt-modes-taxonomy`): detect CLI = **KÉO NGOÀI** (pin `impeccable@3.6.1`, chạy qua `npx -y`, không vendor bytes); rubric `audit`/`harden`/`polish` = **HÒA TAN** (distill từ tarball npm vào `references/`, skill self-contained không cần cài skill impeccable global); hallmark = đã ở trong repo, chỉ gọi.

## Requirements
- **FR-001** Interview MỘT tin nhắn: nguồn theme [A mặc định macOS glass · B path tài liệu · C URL] + Audience/Use case/Tone; "go ahead" → suy luận và công bố.
- **FR-002** `design.md` ở gốc project là nguồn chân lý duy nhất: frontmatter (impeccable) + block token (hallmark) sinh từ MỘT nguồn bằng `design-sync.py`; `--check` rc 1 khi drift.
- **FR-003** Preset macOS glass mặc định đã qua `impeccable detect` rc 0, kèm bảng finding trước/sau.
- **FR-004** Route B: file/folder tài liệu → schema design.md, hỏi bù đúng 1 lần. Route C: `hallmark study` URL → lock the DNA, attestation, fallback screenshot.
- **FR-005** Rubric audit/harden/polish distill self-contained có nguồn file + sha.
- **FR-006** `fe-gate.sh`: assert path tồn tại → `detect --json` → rc 0/1/2 đúng nghĩa → playwright 4 viewport; thiếu node/mạng ghi `skipped` và exit ≠ 0.
- **FR-007** Hub SKILL.md 5 pha điều phối, không chép rubric; vòng sửa tối đa 3, dư thì báo thẳng.
- **FR-008** Register + parity 3 bản + medic --ci xanh + chạy thử end-to-end 1 trang mẫu.

## Non-goals
- Không sửa hallmark hay impeccable; chỉ gọi + distill.
- Không cài impeccable skill vào `~/.claude/skills` (tránh trùng 23 lệnh với router).
- Không thay `/br` (pipeline BR→frame) — `/prd-grade-fe` là bước dựng UI bên trong một frame hoặc đứng riêng.
- Không build component library; một trang/màn hình mỗi lần chạy, hệ thiết kế giữ qua `design.md`.

## Global constraints
- **Một nguồn chân lý thông số**: block token `:root{}` trong `design.md` (format hallmark references/design-md.md). Frontmatter YAML của chính file đó (impeccable đọc) và `tokens.css` đều SINH từ block bằng `design-sync.py`; sửa tay phần sinh là drift → `--check` đỏ.
- **Mọi màu/font trong output tham chiếu token** (`var(--color-*)`, `var(--font-*)`) — discipline 3 của hallmark; inline hex/oklch là fail.
- **Cổng giao hàng tất định**: `impeccable detect --json` rc phải = 0 trên mọi file output (rc 2 → sửa → chạy lại, tối đa 3 vòng, còn dư thì báo thẳng, không giấu); rc 1 là lỗi vận hành → dừng, không coi là sạch.
- **Mobile floor**: 320/375/414/768 px không scroll ngang (hallmark discipline 5), kiểm bằng `/playwright-verify`.
- **HTML cho người xem**: có toggle sáng/tối + localStorage + chống FOUC; thang chữ compact 13″; hiện path tương đối của chính nó (không path tuyệt đối — bài học #131).
- **Không ghi công AI** trong commit/file (R15). Skill sửa xong chạy `bash fdk/tools/sync-skill.sh prd-grade-fe`, không cp tay.
- Fail-open với công cụ thiếu: không có `node`/mạng thì bước detect ghi `skipped: <lý do>` trong report, KHÔNG được báo "sạch".

## Approaches
- **A — Hub mỏng gọi hallmark + impeccable, một script sync + một script gate (chọn).** SKILL.md ~250 dòng điều phối 5 pha; 2 script python/bash nhỏ có `--self-test`; preset macOS-glass là một `design.md` đã qua detect rc 0. Rẻ, tái dùng toàn bộ 27 references của hallmark.
- **B — Skill độc lập, chép rubric hallmark vào** — bác: 68.8K+ nội dung trùng, drift ngay commit sau.
- **C — Cài impeccable skill global và dặn agent "nhớ chạy"** — bác: bậc đòn bẩy thấp nhất (dặn nhớ), không có gate; 23 lệnh chat đè router.

## Plan
- [ ] T1 — Scaffold `skills/prd-grade-fe/` bằng `fdk/tools/new-skill.py --loop dev-loop` + viết SKILL.md hub 5 pha: (0) pre-flight phát hiện `design.md`/`.impeccable/`/node/mạng; (1) interview MỘT tin nhắn gộp: nguồn theme [A mặc định macOS glass · B path tài liệu · C URL] + 3 câu hallmark; (2) khoá biến; (3) build theo hallmark default flow với design.md locked; (4) vòng audit; (5) deliver report.
- [ ] T2 — Preset mặc định `references/presets/macos-glass.design.md`: agent senior frontend dựng trang probe từ token docs-site-macos (glass ladder, `--edge-hi`, SF Pro stack), chạy `npx -y impeccable@3.6.1 detect --json` lặp tới rc 0, ghi bảng finding trước/sau làm bằng chứng; kết quả điền vào preset (OKLCH cho paper/ink/accent, contrast đã đo, radius/blur/opacity ladder, motion).
- [ ] T3 — `skills/prd-grade-fe/scripts/design-sync.py`: đọc block token trong `design.md` → sinh frontmatter YAML (impeccable: colors/typography/rounded) ghi ngược vào chính `design.md` + `tokens.css`; `--check` so đĩa (rc 1 nếu drift); `--self-test` 4 assert (token đủ 8 màu + 3 font, OKLCH giữ nguyên, idempotent, drift bắt được).
- [ ] T4 — Intake routes trong `references/intake.md`: route B (file/folder tài liệu thiết kế → đọc, map về schema design.md, liệt kê trường thiếu để hỏi bù đúng 1 lần); route C (URL → gọi `hallmark study` URL mode → "lock the DNA" → design.md, kèm attestation + fallback screenshot khi SPA/auth-wall). Route A = copy preset.
- [ ] T5 — Distill rubric `audit`/`harden`/`polish` từ repo `pbakaus/impeccable@2bc2879` (`plugin/skills/impeccable/reference/{audit,harden,polish}.md`, sparse-clone vào scratchpad — tarball npm không chứa skill) thành `references/impeccable-audit.md` — checklist P0–P3 self-contained, ghi rõ nguồn file + sha.
- [ ] T6 — `skills/prd-grade-fe/scripts/fe-gate.sh`: assert từng target tồn tại → `detect --json --no-advisory` → phân nhánh rc 0/1/2 đúng nghĩa → in bảng finding → gọi playwright-verify 4 viewport → exit 0 chỉ khi cả hai xanh. Có `--self-test` trên file sạch/bẩn/thiếu.
- [ ] T7 — Register + parity: `sync-skill.sh prd-grade-fe`, `build-capabilities.py`, LOOP_MAP/bảng AGENT-CLAUDE, index, node problem-tree; test trigger 2 câu mẫu ("dựng frontend production cho app X", "/prd-grade-fe paste link"); `medic --ci` xanh.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 — SKILL.md hub 5 pha | Claude | Hợp đồng skill, nuance điều phối 2 công cụ | pending |
| T2 — preset macOS-glass qua detect | Claude (subagent senior frontend) | Phải đọc finding và tinh chỉnh thẩm mỹ, không cơ học | pending |
| T3 — design-sync.py | Claude | Parser + drift check, sai là drift âm thầm | pending |
| T4 — intake routes | Claude | Map tài liệu tự do về schema, cần phán đoán | pending |
| T5 — distill rubric impeccable | OpenCode `big-pickle` (fallback Claude) | Đọc tarball rồi tóm checklist, cơ học; watchdog 90s | pending |
| T6 — fe-gate.sh | Claude | Ngữ nghĩa rc 0/1/2 và bẫy rc 0 giả, sai là gate mù | pending |
| T7 — register + parity | OpenCode `big-pickle` (fallback Claude) | Chạy tool sẵn có, cơ học | pending |

**Sequence diagram:** [080926-prd-grade-fe-seq.html](../../../html/080926-prd-grade-fe-seq.html)

## Risks
- `npx -y impeccable@3.6.1` cần mạng lần đầu → gate skip trên máy offline; đã ràng buộc phải ghi `skipped`, không báo sạch.
- Bản npm 3.6.1 đi sau git main (bundle đã đo) → pin cứng version trong script, không dùng `@latest`.
- Glass mặc định có thể không đạt rc 0 mà vẫn đẹp → T2 phải chọn: hạ blur/tăng opacity cho đủ contrast; nếu bất khả thì ghi waiver có lý do vào `.impeccable/config.json` (cách 03-tune) — waiver là quyết định có ghi vết, không phải ignore lén.
- Trùng năng lực với `hallmark redesign --multi-page` (cũng sinh design.md) → `new-skill.py --strict` sẽ đo; hub này KHÔNG sinh design.md theo cách riêng, chỉ gọi hallmark.

## Success criteria
- `python3 skills/prd-grade-fe/scripts/design-sync.py --self-test` và `bash skills/prd-grade-fe/scripts/fe-gate.sh --self-test` rc 0.
- Preset macOS-glass: `detect --json` trên trang probe rc 0, bảng trước/sau có trong references.
- Chạy thử end-to-end trên 1 trang mẫu: design.md sinh → build → fe-gate xanh → report có 6 điểm pre-emit critique hallmark + số finding từng vòng.
- `sync-skill.sh` parity 3 bản; `medic --ci` xanh; `build-capabilities.py --check` xanh.

## Self-review
- Bậc đòn bẩy: gate tất định (đổi luật chơi) thay vì dặn agent nhớ (tham số) — đúng Meadows.
- Một nguồn chân lý + `--check` = vòng phản hồi có sẵn, không thêm sổ append-only mới.
- Không dẫm module: hallmark/impeccable chỉ được gọi; `new-skill.py --strict` chạy ở T1.

## Notes
- [[hallmark]] · [[adapt-modes-taxonomy]] · [[docs-site-macos]] · [[playwright-verify]]
- Bundle nguồn: `doyourmagic/impeccable/02-detect-cli-scan.md`, `05-chat-commands.md`, `03-tune-detector-ignores.md`.

## Origin
- **Draft:** `wiki/sources/draft/080926-prd-grade-fe.md`
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
