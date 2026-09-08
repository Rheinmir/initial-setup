---
name: prd-grade-fe
description: "Pipeline MỘT CỬA ra frontend chuẩn production có CỔNG MÁY GÁC: phỏng vấn nguồn theme một tin nhắn (A preset macOS glassmorphism mặc định · B folder/file tài liệu thiết kế · C paste URL trang đích), khoá thông số vào MỘT file design.md (hallmark và impeccable đọc chung) rồi sinh tokens.css + frontmatter bằng design-sync.py, dựng trang token-only theo hallmark, chạy fe-gate.sh (impeccable detect 61 luật tất định rc 0/1/2 + Playwright 4 viewport) và rubric audit/harden/polish, KHÔNG giao khi cổng chưa xanh. Gọi khi user nói 'frontend production', 'production-grade frontend', 'dựng FE chuẩn production', 'giao diện kỷ luật', 'prd-grade-fe', '/prd-grade-fe'. Khác hallmark (sàn design, không có gate impeccable) và khác /br (dây chuyền BR→frame, không lo riêng tầng frontend)."
version: 1.0.0
---

# prd-grade-fe

`$SKILL` dưới đây = **Base directory của skill này** (dòng "Base directory for this skill" khi skill được nạp; trong repo framework là `skills/prd-grade-fe`). Mọi script và reference đi kèm thư mục skill, không phụ thuộc repo.

Hub mỏng. Không sở hữu luật thiết kế: thẩm mỹ là của **hallmark** (`skills/hallmark/SKILL.md`), luật tất định là của **impeccable** (`npx -y impeccable@3.6.1 detect`, pin cứng). Hub sở hữu **thứ tự** và **hợp đồng giữa các pha**, cộng hai script có `--self-test`:

| File | Vai trò |
|---|---|
| `scripts/design-sync.py` | `design.md` là nguồn chân lý: block ```css :root{}``` → frontmatter YAML (impeccable đọc) + `tokens.css`. `--check` rc 1 khi drift. |
| `scripts/fe-gate.sh` | Cổng trước khi giao: assert target tồn tại → `detect --json` → rc 0/1/2 đúng nghĩa → `viewport-check.mjs` 320/375/414/768. Exit 0 xanh · 1 lỗi impeccable · 2 finding/viewport đỏ · 3 skipped (thiếu node/mạng) · 4 target thiếu. |
| `references/presets/macos-glass.design.md` | Preset mặc định đã qua detect rc 0; bằng chứng ở `macos-glass.evidence.md`. |
| `references/intake.md` | Route A/B/C → `design.md`. |
| `references/impeccable-audit.md` | Rubric audit (5 trục /20) · harden · polish, distill có nguồn. |

## When to use
- User muốn một trang/màn hình frontend **đưa vào production**, không phải mockup nhanh (mockup nhanh → `/br` hoặc hallmark trần).
- User đưa theme dưới dạng "mặc định đi", "đây là tài liệu thiết kế", hoặc "làm giống trang này: <URL>".
- Project đã có `design.md` và cần thêm màn hình **cùng hệ** kèm cổng kiểm.

## Steps

### Pha 0 — Pre-flight (không hỏi thứ máy tự thấy)
```bash
ls design.md DESIGN.md tokens.css 2>/dev/null; command -v node && echo node-ok
python3 $SKILL/scripts/design-sync.py --check 2>/dev/null; echo sync-rc=$?
```
- Có `design.md` và `--check` rc 0 → nói "hệ đã khoá, dùng lại" và nhảy Pha 3 (trừ khi user đòi đổi theme → `references/intake.md` § "Khi project đã có design.md").
- Không có `node` → vẫn làm Pha 1–3, nhưng Pha 4 sẽ ghi `skipped` và report KHÔNG được nói sạch.

### Pha 1 — Interview MỘT tin nhắn (gộp câu của hallmark, không hỏi nối đuôi)
> Trước khi dựng, cần 4 thứ. Trả lời phần nào cũng được, hoặc nói **"go ahead"**:
> 1. **Nguồn theme** — [A] macOS glass mặc định · [B] đường dẫn tài liệu thiết kế (file/folder) · [C] URL trang đích
> 2. **Audience** — ai dùng, họ biết gì sẵn?
> 3. **Use case** — một hành động trang này phải dẫn tới?
> 4. **Tone** — chọn một cực: editorial · brutalist · soft · utilitarian · luxury · playful · technical · austere

"go ahead" hoặc bỏ trống → chọn **A**, suy luận 2–4 từ brief, **công bố suy luận một câu ở đầu reply** (hallmark Step 1 opt-out protocol). Không có ngoại lệ "brief đã đủ rõ": vẫn hỏi, user vẫy qua trong hai giây.

### Pha 2 — Khoá biến (`references/intake.md`)
- **A**: `cp $SKILL/references/presets/macos-glass.design.md ./design.md`, đổi tên project ở dòng đầu.
- **B**: đọc tài liệu → bảng schema có nguồn file:dòng → MỘT câu hỏi bù → ghi `design.md` + § Provenance.
- **C**: hallmark `study <URL>` (URL mode, refuse list + attestation) → "lock the DNA" → `design.md` có § Provenance + § Notes (rhythm blind spot, anti-pattern không mang theo).
- Rồi: `python3 $SKILL/scripts/design-sync.py && python3 $SKILL/scripts/design-sync.py --check` → rc 0 mới đi tiếp.
- Công bố Genre / Macrostructure / Theme ra lời (hallmark Step 2.5).

### Pha 3 — Build theo hallmark, hệ đã khoá
- Chạy hallmark default flow (Step 2 macrostructure → 3 ruleset → 5 preview → 6 build) với `design.md` locked: diversification **đảo chiều** (màn hình phải CHUNG hệ).
- Mọi màu, font, radius, motion qua `var(--…)` từ `tokens.css` (hallmark discipline 3). Không hex/oklch inline; thiếu token thì thêm vào block `:root` của `design.md` rồi chạy `design-sync.py` lại.
- Output HTML cho người xem: toggle sáng/tối bằng nút gạt có nhãn + `html[data-theme]` + localStorage + chống FOUC; thang chữ compact 13″; footer ghi path **tương đối** của chính file.
- Stamp đầu file: `<!-- design: macrostructure=<M> theme=<T> -->` và `/* Hallmark · pre-emit critique: P? H? E? S? R? V? */` (6 trục, trục nào < 3 thì sửa trước khi sang Pha 4).

### Pha 4 — Gate (máy trước, người sau)
1. `bash $SKILL/scripts/fe-gate.sh <output.html …>`; đọc bảng `antipattern | file:line | snippet` và `fe-gate.report.json`.
   - rc 2 → sửa đúng finding (đổi token trong `design.md` → sync lại, hoặc sửa markup) → chạy lại. **Tối đa 3 vòng.** Ghi số finding từng vòng để đưa vào report.
   - rc 1 / 3 / 4 → dừng, ghi nguyên nhân. Không có đường nào từ 1/3/4 tới "sạch".
2. Nạp `references/impeccable-audit.md`: chấm 5 trục /20, liệt kê P0–P3; làm checklist Harden rồi Polish. **P0 phải = 0.**
3. Chạy hallmark slop-test (`skills/hallmark/references/slop-test.md`) trên output; gate nào đỏ thì sửa.
4. Chạy lại `fe-gate.sh` một lần cuối sau mọi chỉnh sửa (sửa harden/polish có thể tái sinh finding).

### Pha 5 — Deliver + report
Report gồm, theo thứ tự: (1) suy luận/đáp án Pha 1; (2) Genre/Macrostructure/Theme + nguồn theme; (3) 6 điểm critique; (4) bảng finding vòng 1..n và rc cuối; (5) điểm audit /20 + P0 count; (6) 4 viewport; (7) path output tương đối; (8) `skipped` nếu có. Câu "sẵn sàng production" chỉ được viết khi fe-gate exit 0 và P0 = 0.

## Rules
- Không chép rubric hallmark vào đây; sửa luật thì sửa ở hallmark hoặc `references/impeccable-audit.md` (có nguồn + sha).
- **Không bao giờ** gọi `npx impeccable install` (bản 3.6.1 không có `--help` cho install, nó cài thật vào `$HOME`). `--scope` luôn viết dính (`--scope=type`). Tin JSON ở stdout, không tin stderr (npx gộp luồng).
- Vòng sửa quá 3 mà còn finding → giao kèm bảng dư và nói thẳng; hoặc waiver có lý do trong `.impeccable/config.json` (`{"ignores":[...]}`) được nêu trong report. Không ignore lén.
- Thiếu node/mạng → report ghi `skipped: <lý do>`, exit gate ≠ 0. Không có ngoại lệ "chắc cũng ổn".
- `design.md` đã tồn tại → không ghi đè; đổi hệ thì AMEND `## Variants` (no-overwrite policy của hallmark design-md).
- Self-check khi sửa skill: `python3 $SKILL/scripts/design-sync.py --self-test && bash $SKILL/scripts/fe-gate.sh --self-test`, rồi `bash fdk/tools/sync-skill.sh prd-grade-fe`.

## Ví dụ gọi
```
/prd-grade-fe dựng trang danh sách đơn hàng cho app quản lý kho, mặc định theme
/prd-grade-fe trang pricing, theme lấy từ docs/brand/ (folder)
/prd-grade-fe landing cho sản phẩm X, làm giống https://example.com
```
