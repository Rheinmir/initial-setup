---
type: concept
title: "Adapt-modes — các KIỂU absorb năng lực vào dự án (gọi đúng tên, chọn đúng phương án)"
status: active
timestamp: 2026-07-07
tags: [adapt, travel, absorb, external-pull, dissolve, vendor, provenance, capability]
---

# Adapt-modes — các kiểu absorb một năng lực vào dự án

Khi mang một năng lực ngoài (skill/tool/tri-thức) vào overstack, có **≥3 kiểu adapt khác nhau** — trước đây gộp chung
thành "absorb" nên hay chọn nhầm phương án. Concept này đặt tên cố định để lần sau **gọi đúng tên, chọn đúng đường**.

Hai trục phân loại:
- **Sở hữu**: framework tự nắm (viết lại / ôm bytes) ↔ upstream nắm (chỉ pin + audit).
- **Vị trí / travel**: nằm trong repo (đi theo git) ↔ global-ngoài (chỉ recipe đi theo git).

## Kiểu 1 — HÒA TAN (dissolve / native-absorb)
"Hòa tan hoàn toàn thành một phần của framework."
- **Cách**: distill **bản chất** rồi VIẾT LẠI thành code/concept CỦA framework (validator, skill nội bộ, wiki ADR/concept). Không còn phụ thuộc ngoài.
- **Sở hữu**: framework 100%, tự maintain.
- **Travel**: đi như source framework — `global_shared` (engine) hoặc `travel_in_repo` (wiki). Xem `travel-policy`.
- **Chọn khi**: bản chất nhỏ-gọn, cần kiểm soát/sửa sâu, cần **gác tất định**, muốn 0 external dep.
- **Ví dụ**: distill `design-tip` → concept `design-standard` + validator `ai-slop-lint`; promote raw → wiki ADR.
- **Giá phải trả**: tự chịu maintain + chất lượng; không có "update từ upstream".

## Kiểu 2 — KÉO NGOÀI (external-pull / pinned-infra)
"Kéo từ hạ tầng ngoài."
- **Cách**: KHÔNG viết lại; framework chỉ giữ **con trỏ + pin** = mirror `SKILL.md` + `fdk/skills.provenance.json` (source + commit + sha). Engine sống **global/ngoài**.
- **Sở hữu**: upstream nắm & maintain; framework chỉ **pin + audit sha + health-check**.
- **Travel**: chỉ **recipe** đi theo git; engine cài global (`~/.agents/skills`); **state máy-local KHÔNG travel**.
- **Chọn khi**: công cụ lớn/nặng, đổi nhanh, không muốn ôm chục-nghìn-LOC, chấp nhận phụ thuộc ngoài.
- **Ví dụ**: `last30days` (mvanhorn), `agent-reach` (Panniantong) — đăng ký ở `travel-policy.yaml` Tầng 1 `research_reach`.
- **Giá phải trả**: phụ thuộc mạng/upstream; state máy-local (yt-dlp/ffmpeg/Node/mcporter + cookie login + API key) phải **tái lập mỗi máy** bằng `agent-reach doctor` / `install --safe` (self-heal). Đây là ranh giới `build-now-adapt-later`.

## Kiểu 3 — NHÚNG-SỞ-HỮU (vendor / fork-in) — điểm giữa
- **Cách**: copy **nguyên bytes** code ngoài VÀO repo rồi framework sở hữu & sửa (fork).
- **Sở hữu**: framework nắm bytes (đã copy), sửa được; **mất** đường update tự động từ upstream.
- **Travel**: `travel_in_repo` (làm nặng repo).
- **Chọn khi**: cần hard-own + sửa + chạy offline + không muốn dep runtime; chấp nhận bloat + gánh maintain.
- **Ví dụ**: `bird-search` vendored bên trong last30days chính là vendor ở tầng con.

### Vì sao Kiểu 3 dễ nhầm nhất (chìa khoá: chép "bản chất" hay chép "bytes")
Nó mượn mỗi cực một nửa — **gốc code bên ngoài** (giống KÉO NGOÀI) nhưng **framework sở hữu & nằm trong repo** (giống HÒA TAN) — nên hay lẫn với cả hai:
- **≠ HÒA TAN**: HÒA TAN chép cái **Ý** (đọc hiểu rồi TỰ VIẾT LẠI, code là của mình, hiểu từng dòng). NHÚNG chép cái **BYTES** (bê nguyên code người khác, không viết lại — sở hữu nhưng không phải mình viết). *Dấu hiệu*: có nguyên cây source lạ + LICENSE của họ = NHÚNG.
- **≠ KÉO NGOÀI**: KÉO NGOÀI giữ **dây nối upstream** (pin + update được, engine ở ngoài). NHÚNG **cắt dây** (copy vào là fork, mất auto-update, muốn bản mới phải re-vendor tay). *Dấu hiệu*: bytes nằm TRONG repo + đã sửa cục bộ = NHÚNG; chỉ có provenance trỏ ra ngoài = KÉO NGOÀI.
- Câu một dòng: cùng "framework sở hữu", nhưng HÒA TAN sở hữu thứ mình **hiểu**, còn NHÚNG sở hữu thứ mình phải **nuôi hộ** (tự backport bản vá bảo mật của upstream).

## Bảng quyết định — gọi tên nào?
| Câu hỏi chốt | → Kiểu |
|---|---|
| Bản chất nhỏ, muốn gác tất định, 0 dep ngoài? | **HÒA TAN** |
| Công cụ nặng/đổi nhanh, chấp nhận dep, chỉ pin + audit? | **KÉO NGOÀI** |
| Cần ôm bytes để sửa + chạy offline, chịu bloat? | **NHÚNG-SỞ-HỮU** |

## Không được nhầm
- **KÉO NGOÀI ≠ travel_in_repo**: nhét engine nặng vào mỗi repo = "copy-per-repo bloat" mà `travel-policy` cố tình từ chối. External-pull chỉ để **recipe** travel.
- **State máy-local không bao giờ travel** ở kiểu 2 — luôn cần một bước self-heal per máy.
- Ghi `adapt_mode` vào `provenance` cho mỗi skill ngoài để về sau biết nó thuộc kiểu nào.

## Origin
- Feedback user 2026-07-07: "có ít nhất 2 kiểu adapt — hòa tan hoàn toàn thành 1 phần framework, và kéo từ hạ tầng ngoài; cần biết để lần sau gọi đúng tên đúng phương án."
- Ca cụ thể sinh ra concept: cài `last30days` + `agent-reach` theo kiểu external-pull (phiên 2026-07-07) + phản biện travel-in-repo bằng `travel-policy` v4 (3 tầng global_shared/travel_in_repo/framework_only).
- Liên quan: `travel-policy`, skill `build-now-adapt-later`, `skill-provenance`, `docs-curate` (promote bản chất → wiki).
