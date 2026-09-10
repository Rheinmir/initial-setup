---
type: draft
title: "Pin archify sang fork Rheinmir/archify — docs overstack còn trỏ upstream"
status: proposed
tags: [archify, diagram, adapt-modes, drift, skill-pin]
timestamp: 2026-09-08
---

# 080926-archify-fork-pin

**Status:** proposed

## What

`skills/diagram` khai nguồn cài engine sơ đồ là `tt-a1i/archify`. Máy dev đã đổi sang fork
`Rheinmir/archify` nhánh `macos-roboto` để giữ preset `macos` (liquid glass + Roboto, đặt làm
mặc định) sống sót qua `skills update`. Tài liệu và thực tế giờ lệch nhau: máy nào cài theo
docs sẽ ra preset `classic`, không ai biết vì sao khác.

## Bằng chứng đo được

| Nơi | Đang nói gì |
|---|---|
| `skills/diagram/SKILL.md:39` | ``npx skills add tt-a1i/archify -g`` |
| `skills/diagram/SKILL.md:130` | ``Nhánh sơ đồ: `tt-a1i/archify` (KÉO NGOÀI…)`` |
| `llmwiki/skills/utils/diagram.md:39,130` | mirror của hai dòng trên |
| `~/.agents/.skill-lock.json` (máy dev) | `Rheinmir/archify` · `ref: macos-roboto` |

Fork: `Rheinmir/archify` @ `macos-roboto` = `fbca0d1`, dựng trên upstream `920543b`
(`archify` 2.17.0-dev.1). Nội dung vá: preset thứ 5 khai vào đúng 4 chỗ archify định nghĩa một
preset (schema enum · validator biên dịch sẵn · i18n · `assets/template.html`), cộng
`renderers/shared/cli.mjs` đổi mặc định `classic` → `macos`, và `SKILL.md` của archify sửa cho
khớp hành vi.

## Đề xuất thay đổi

Sửa **duy nhất bản canonical** `skills/diagram/SKILL.md` (2 dòng), rồi chạy
`bash fdk/tools/sync-skill.sh diagram` để đẩy ra mirror `llmwiki/skills/utils/diagram.md` và
bản cài `~/.claude`. Không sửa tay mirror — đó đúng là nguồn drift mà `sync-skill.sh` sinh ra
để chặn (eval 020726).

```diff
 dòng 39
-Cài: `npx skills add tt-a1i/archify -g` (đích thật là `~/.agents/skills/archify`).
+Cài: `npx skills add Rheinmir/archify -g -s archify` (đích thật là `~/.agents/skills/archify`).
+Fork của tt-a1i/archify; nhánh vá `macos-roboto` là nhánh MẶC ĐỊNH của fork nên không ghim ref.
+Kèm hai bẫy đã trả giá (xem mục Rủi ro).

 dòng 130
-- Nhánh sơ đồ: `tt-a1i/archify` (KÉO NGOÀI — engine sống ngoài, ta ghim + gọi).
+- Nhánh sơ đồ: `Rheinmir/archify` @ `macos-roboto` (KÉO NGOÀI — fork của `tt-a1i/archify`;
+  engine sống ngoài, ta ghim + gọi).
```

## Cấu trúc nào sinh ra drift này

Câu hỏi Meadows, trả lời thật: **cái pin chỉ tồn tại dưới dạng văn xuôi trong một `SKILL.md`,
và không có gì đối chiếu nó với `.skill-lock.json`.** Đã kiểm: `adapt-registry.py` là sổ ẩn-số
trong code (build-now-adapt-later), không phải sổ quyết định KÉO NGOÀI; `adapt-modes.md` không
ghi pin của từng engine. Nên bất kỳ ai repoint một skill lần sau, docs lại lệch im lặng.

Sửa 2 dòng là **bậc thấp nhất** của thang đòn bẩy (sửa tham số). Bậc cao hơn — một cổng tự cắn
— để ngỏ, chưa đề xuất làm ngay vì lỗi mới xảy ra **một lần** và chỉ có 2/89 skill nằm ngoài
overstack (`archify`, `depmap`); `/fdk` cũng dặn tôn trọng độ trễ, đừng chồng fix khi fix trước
chưa kịp phát tác. Ghi ra đây để lần thứ hai gặp thì biết là tín hiệu cấu trúc, không phải xui.

## Rủi ro

- **Hai giả định của bản đề xuất đầu đều SAI, đã đo bằng cách chạy thật:**
  1. `--ref` không tồn tại (`skills add --help`).
  2. `owner/repo@nhánh` cũng KHÔNG ghim nhánh lúc cài. CLI in `Source: …git @macos-roboto`
     rồi vẫn cài nhánh mặc định, và hiểu phần sau `@` là TÊN SKILL → `No matching skills found
     for: macos-roboto`. Bản cài rơi về upstream: `cli.mjs` mặc định `classic`, không Roboto,
     `ref` trong lock thành `None`.
  Cách thật sự chạy: đặt `macos-roboto` làm **nhánh mặc định của fork**
  (`gh repo edit Rheinmir/archify --default-branch macos-roboto`), rồi
  `npx skills add Rheinmir/archify -g -s archify`. Cần `-s archify` vì không có nó CLI lọc
  skill theo chuỗi sau `@` và không khớp gì.
- Fork đứng yên ở upstream `920543b`. Upstream ra bản mới thì phải rebase; đường rebase là
  `hoh/tools/archify-macos-preset.py` chạy lại trên cây sạch (đã kiểm: khớp hash 7/7 với bản
  đang cài) — nhưng script đó hiện nằm ngoài overstack, ở repo `hoh`.

## Bài học: `-l` không thay được cài thật

`npx skills add … -l` báo `Found 1 skill` — xanh — trong khi lệnh cài thật hỏng ở bước sau.
Cổng "liệt kê được" và cổng "cài xong dùng đúng" là hai cổng khác nhau; lấy cái rẻ thay cái
đắt thì được một biên lai không chứng minh điều nó có vẻ chứng minh. Cùng họ với khuôn
"BỎ QUA ≠ SẠCH" đã ghi ở `sources/draft/040926-absorb-round.md`.

## Kiểm chứng

- [x] `npx skills add Rheinmir/archify -g -s archify` → bản cài mang bản vá (`cli.mjs` mặc định `macos`, template `126ac96c0390`)
- [x] Vẽ với spec KHÔNG khai `meta.visual_preset` → `data-preset="macos"`, Roboto có, `visual-check pass · 0 diagnostic`
- [x] `bash fdk/tools/sync-skill.sh diagram` → parity 3 bản, hash `01d31768b31e`
- [ ] `python3 fdk/tools/medic.py --ci` xanh
- [ ] Trọn job `repo health` của `.github/workflows/harness.yml` chạy local, xanh

## Files

| File | Action |
|------|--------|
| `skills/diagram/SKILL.md` | modified (canonical — lệnh cài + 2 bẫy đã trả giá) |
| `llmwiki/skills/utils/diagram.md` | modified (sync-skill.sh sinh, không sửa tay) |
| `llmwiki/wiki/sources/draft/080926-archify-fork-pin.md` | created |
| `llmwiki/wiki/index.md` | modified (R3 index-sync) |
| `llmwiki/html/fdk-problem-tree.html` | modified (node p-50) |

## Origin

- **Phát hiện:** phiên vẽ sơ đồ `hoh` 2026-09-07/08 — gọi thẳng `Skill(archify)` thay vì vào
  bằng `/diagram`, nên đổi nguồn cài mà không đi qua cửa trước của overstack.
- **Fork:** `Rheinmir/archify` = `fbca0d1` (trên upstream `920543b`); `macos-roboto` đặt làm nhánh mặc định 2026-09-08
- **Nền:** `[[adapt-modes]]` — archify là phán quyết KÉO NGOÀI ở vòng absorb
  `sources/draft/040926-absorb-round.md` (mục 6 và 8 HÒA TAN; engine để ngoài)
