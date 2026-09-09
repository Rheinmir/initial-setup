---
type: plan
issue: 060726-design-standard-ai-elite
title: "PROPOSAL — Nền chuẩn thiết kế AI-elite chống AI-slop (design-standard + gác 2 tầng)"
status: draft
timestamp: 2026-07-06
tags: [plan, design, anti-slop, taste, harness, foundation]
---

# PROPOSAL — Nền chuẩn thiết kế "AI-elite" chống AI-slop (design-standard + gác 2 tầng)

Ngày: 2026-07-06 · Trạng thái: **DRAFT — chờ duyệt** · Loại: foundation (đổi luật chơi, Meadows bậc cao)
Draft path: `llmwiki/wiki/sources/draft/060726-design-standard-ai-elite-PLAN.md`

## 1. Bối cảnh
Repo đã có ~8 skill thiết kế (`design-taste-frontend` v1/v2, `high-end-visual-design`, `minimalist-ui`,
`industrial-brutalist-ui`, `gpt-taste`, `redesign-existing-projects`, `stitch-design-taste`, imagegen-*).
Vấn đề hệ thống: **mỗi skill tự mang luật riêng, không có nền chung** → (a) chuẩn "chống AI-slop" bị lặp và
lệch nhau giữa các skill; (b) **HTML do chính framework sinh** (report, docs-site, council, problem-tree)
**không hề bị soi** cùng chuẩn đó — ta cấm purple-gradient trong skill nhưng generator của ta vẫn có thể đẻ ra nó.

Đầu vào: distill `raw/design-tip-of-someone-on-internet.md` (13 tip → 3 trục: ĐO ĐƯỢC / QUY TRÌNH / PHÁN ĐOÁN)
+ nghiên cứu 8 nguồn design-agent mạnh nhất (taste-skill, avoid-ai-design, Anthropic frontend-design,
Emil Kowalski motion, high-end-visual-design, Refactoring UI, claude-design-auditor, Meta Astryx).

## 2. Quyết định người dùng đã chốt (2026-07-06)
- **Phạm vi**: gác CẢ HAI đầu ra — HTML framework tự sinh **và** bộ skill design downstream — bằng **1 nền chung** (không phân mảnh chuẩn).
- **Độ gác**: **2 tầng** (lint mềm mặc định, vài tell chắc-chắn-sai hard-gate) — **NHƯNG** khi user đã chốt "sửa antipattern này" thì phải **kill gọn trong 1 shot** (đường auto-fix tất định).

## 3. Nguyên tắc (leverage point — Meadows)
Không đẻ thêm skill design (bậc thấp, sinh drift). Thay vào đó **đổi luật chơi**: một *nguồn chuẩn duy nhất* +
*vòng phản hồi tất định* (validator tự cắn) + *đường sửa 1-shot*. Mỗi skill/generator chỉ **trỏ vào nền**, không chép luật.
Kỷ luật cốt lõi kế thừa từ taste-skill: **không luật nào tự bắn mù** — brand thật là màu tím thì validator không được fail cứng; mọi luật ĐO ĐƯỢC phải có **đường override ghi vết**.

## 4. Kiến trúc — 3 mảnh, 1 nền

### 4.1 `design-standard` — nguồn chuẩn duy nhất (canon)
Một concept wiki máy-đọc: `wiki/concepts/design-standard.md` + bản HTML người-đọc.
Chứa **bảng luật hợp nhất** chia 2 nhóm, mỗi luật gắn: ngưỡng · nguồn hội tụ · mức nghiêm trọng **P0/P1/P2**
(P0 = người thường thấy ngay là AI; P1 = dev/designer nhận ra; P2 = lỗi craft) · **đường override**.

**Nhóm A — ĐO ĐƯỢC (validator cắn được), ưu tiên build trước:**
| Luật | Ngưỡng/check | P | Nguồn |
|---|---|---|---|
| Cấm em-dash/en-dash hiển thị | regex `[—–]` trong text render | P0 | taste-skill, auditor |
| Cấm gradient tím/chàm mặc định + `bg-clip-text` heading | quét hue gradient CSS | P0 | taste-skill, avoid-ai, Anthropic |
| Cấm font mặc định vô hồn | `font-family` ∈ {Inter,Roboto,Open Sans,Lato,Arial,Helvetica} không lý do | P0 | 4 nguồn |
| Cấm serif display mặc định | `Fraunces`,`Instrument_Serif` làm default | P1 | taste-skill |
| Cấm bảng hex "premium-consumer" (beige+brass+oxblood) | match danh sách hex đặt tên | P1 | taste-skill |
| Type-scale cực trị | weight 100–200 vs 800–900; bước size ≥3× | P1 | Anthropic |
| Spacing lưới 4/8 | mọi margin/padding chia hết 4 | P2 | Refactoring UI, auditor |
| Contrast WCAG | body ≥4.5:1, large ≥3:1, UI ≥3:1 | P0/P1 | auditor, taste-skill |
| Animate chỉ transform/opacity | AST/CSS scan prop layout bị animate | P1 | Emil, high-end, taste-skill |
| Duration UI <300ms | micro 100–150 / std 150–250 / modal 200–300 | P2 | Emil |
| Easing theo loại tương tác | enter/exit=ease-out; on-screen=ease-in-out; marquee=linear-only | P2 | Emil, high-end |
| `prefers-reduced-motion` cho mọi animation | media-query tồn tại/animated element | P1 | Emil, taste-skill |
| Cấm `window.addEventListener('scroll')` | grep = fail | P2 | taste-skill |
| `min-h-[100dvh]` không `h-screen` | grep `h-screen` ở hero | P2 | taste-skill |
| Luật số 3 + eyebrow cap | ≤3 màu, ≤3 font, eyebrow ≤ ceil(sections/3) | P1 | tip#7, taste-skill |
| Cấm 3 feature-card y hệt / zigzag >2 / marquee >1 | đếm | P1 | taste-skill, avoid-ai |
| 1 accent · 1 radius-scale · 1 theme | đếm hue accent / radius / theme-flip = 1 | P1 | taste-skill |
| Cấm icon `<path>` tự vẽ | icon phải import từ lib cho phép | P2 | taste-skill, high-end |
| Cấm số hoàn-hảo-giả / tên generic | regex `99.99%`,`John Doe`,`Acme` | P1 | taste-skill |
| Cấm `#000`/`#fff` thuần | ban pure black/white | P2 | taste-skill, Refactoring UI |

**Nhóm B — PHÁN ĐOÁN (flag & hỏi, KHÔNG auto-fail):** product-first/brief-read đúng audience; "thay mặc định bằng quyết định"; 1 hướng + 1 rủi ro thẩm mỹ có chủ đích; animation *có động cơ*; bẫy mặc-định-bậc-2 ("Space Grotesk trap"); hierarchy bằng de-emphasis; materiality (double-bezel/two-layer shadow) trông thật; chất lượng copy; nhịp whitespace. → dành cho lens judge.

### 4.2 `ai-slop-lint` — validator tất định (Nhóm A)
`harness/scripts/ai-slop-lint.py` (+ `harness/validators/` nếu cần hook). Nhận file/dir HTML/CSS (và, tùy chọn, JSX/CSS của skill output).
- **Mặc định = mềm**: in danh sách vi phạm kiểu medic-warning (P0/P1/P2, kèm file:line + luật + đường override). Không chặn commit.
- **Tầng cứng (hẹp)**: chỉ **P0 chắc-chắn-sai** (em-dash, purple-gradient tell, font trần không-lý-do) mới fail gate — nối vào `medic --ci` cho HTML framework sinh.
- **`--fix` (KILL 1-SHOT — điểm user yêu cầu)**: khi user chốt sửa một tell, chạy `ai-slop-lint --fix <target> --rule <id>` **giết tất định** đúng tell đó trong 1 lượt: `—`→` - `, purple-gradient→neutral+1 accent, font trần→font đã duyệt, `h-screen`→`min-h-[100dvh]`, `#000/#fff`→off-black/off-white, `bg-clip-text` heading→bỏ, flag scroll-listener. Idempotent, chạy lại sạch.
- **Override ghi vết**: file có `<!-- design-standard: allow purple (brand) -->` (hoặc mục trong `design-standard.overrides.yaml`) thì luật đó bỏ qua + log lý do → không false-positive phá "chủ đích".

### 4.3 `design-review` lens — pass phán đoán (Nhóm B)
Không mã hoá được → LLM-as-design-reviewer chấm trên **render thật** (screenshot qua Computer-Use/Chrome MCP đã có), xuất P0/P1/P2 + đề xuất. On-demand (không auto-fire), tái dùng hạ tầng browser sẵn có. *Có thể là phase sau.*

## 5. Wiring (không chép luật — chỉ trỏ)
- Mỗi skill design mirror (`llmwiki/skills/utils/design-*.md`, `high-end-*`, `minimalist-ui`, …) thêm **1 dòng** "Chuẩn nền: tuân `design-standard` (nhóm A cắn tự động, nhóm B là lens)". Không xoá/chép nội dung skill.
- HTML generator framework (`fdk/tools/build-overstack-docs.py`, `build-docs-index.py`, `docs-site-macos`, `md-to-html`, `council.py`, problem-tree) gọi `ai-slop-lint` (mềm) trước khi emit; P0 nối `medic --ci`.
- Bảng `AGENT.md`/`CLAUDE.md` + `CAPABILITIES.md`: đăng ký chuẩn + script mới.

## 6. Rollout theo phase (surgical, mỗi bước verify)
1. **P1 — canon**: viết `design-standard.md` + HTML người-đọc (theme-toggle, full-path, compact-font). *Verify*: lint wiki xanh, index cập nhật.
2. **P2 — lint lõi**: `ai-slop-lint.py` với ~8 luật P0/P1 rẻ nhất (em-dash, purple, font, h-screen, #000/#fff, scroll-listener, luật-số-3, contrast). *Verify*: test trên 1 HTML "bẩn" cố tình + 1 HTML sạch (golden).
3. **P3 — `--fix` 1-shot** cho đúng các luật P0 ở P2. *Verify*: fix rồi lint lại = sạch, idempotent.
4. **P4 — wiring mềm** vào 1 generator (build-overstack-docs) + `medic --ci` cho tầng cứng hẹp. *Verify*: medic xanh.
5. **P5 — trỏ skill** (1 dòng/skill) + `design-review` lens (nếu còn ngân sách).

Mỗi phase là 1 commit độc lập, có cửa verify. Dừng & báo giữa các phase.

## 7. Rủi ro & ranh giới (không làm)
- **False-positive giết "chủ đích"** (bold/maximalism/brand-purple) → giảm thiểu bằng: tầng cứng CỰC hẹp + override ghi vết + mặc định mềm.
- **KHÔNG** đẻ skill design mới; **KHÔNG** chép luật vào từng skill; **KHÔNG** hard-gate nhóm B (phán đoán); **KHÔNG** đụng nội dung skill downstream ngoài 1 dòng trỏ.
- **KHÔNG** mã hoá Astryx-token-audit ở phase này (ghi nhận là substrate dài hạn, để sau).

## Origin
- Distill: `raw/design-tip-of-someone-on-internet.md` (13 tip).
- Research: taste-skill (Leonxlnx), avoid-ai-design (funboy322), Anthropic frontend-design, Emil Kowalski/web-animation-design (vercel-labs), high-end-visual-design, Refactoring UI (Wathan/Schoger), claude-design-auditor (Ashutos1997), Meta Astryx.
- Bối cảnh phiên: agent nền `a5a9a19` (corpus có nguồn), `/last30days` (engine thiếu → WebSearch thay).
