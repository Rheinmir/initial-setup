---
name: visual-qa
description: >-
  WORKFLOW tự-kiểm THỊ GIÁC khép kín cho SPA local (app do /br sinh, hoặc bất kỳ web app):
  chụp headless từng route → BASELINE pixel-diff (bắt thay đổi ngoài ý muốn) → bất biến
  máy-kiểm (design conformance) → agent ĐỌC HẾT ảnh theo rubric → FINDINGS.md → sửa → chụp
  lại → chỉ pass khi máy VÀ mắt cùng sạch. Dùng khi đổi theme/UI/rebrand, khi extension MCP
  không chụp được localhost, hoặc cần gate UI cho frame. Trigger: "qa thị giác", "visual qa",
  "route-shots", "screenshot từng route", "kiểm giao diện", "baseline diff", "UI có regression
  không", "test giao diện headless", "/visual-qa".
---

# Skill: visual-qa — workflow tự-kiểm thị giác (capture → diff → judge → fix → re-verify)

> **Vì sao tồn tại:** agent sửa UI rồi *tự khen* là sai lệch có hệ thống (failure
> `ui-pass-without-full-visual-review`). Ảnh chụp ra mà không ai mở = như chưa test. Workflow
> này thay "agent tự nhìn rồi tự cho pass" bằng **ba tầng kiểm độc lập**, trong đó hai tầng là máy.
>
> **Quyết định 13/07/26 (từ /last30days):** ngành chỉ có MỘT thứ đã chín cho UI-do-AI-sinh —
> **baseline snapshot + pixel diff** (`argos-ci/argos`: *"detects unintended visual changes"*;
> Playwright `toHaveScreenshot`). Tầng "LLM-judge chấm screenshot theo rubric" còn là biên giới
> (Agent-as-a-Judge, paper-stage) — nên ta **tự làm** tầng đó, không chờ ai.

## When to use
- Vừa đổi theme / UI / rebrand và cần biết **có làm hỏng gì ngoài ý muốn không**.
- Frame có `ui_role≠none` cần gate acceptance (xem skill `br` § Vòng tự-kiểm thị giác).
- Extension browser không chụp được localhost (thường gặp) → headless CLI thay thế.

## Workflow (6 bước — chạy đủ, không cắt bước)

**0. App phải đang chạy.** Biết route list (lấy từ router THẬT, không đoán) + tài khoản login.

**1. CHỤP + BẰNG CHỨNG.**
```bash
node skills/visual-qa/assets/route-shots.mjs \
  --base http://localhost:5230 --out <dir>/qa-shots \
  --baseline <dir>/qa-baseline \
  --user demo --pass demo --assert
```
Sinh `<out>/*.png` + **`MANIFEST.json`** (route → file → bytes). Không có file = **CHƯA TỪNG CHỤP**.

**2. BASELINE DIFF (máy tầng 1) — bắt thay đổi NGOÀI Ý MUỐN.**
Lần đầu tự tạo baseline. Lần sau so pixel-by-pixel. **Ngưỡng mặc định = 0**: mọi diff ≠ 0 đều
FAIL và phải được xem + duyệt tay bằng `--update-baseline`. Đây là tầng duy nhất bắt được loại
lỗi mà bất-biến-CSS và mắt agent đều MÙ (vd: sửa quá tay làm phẳng cả UI).

**3. BẤT BIẾN MÁY-KIỂM (máy tầng 2) — design conformance + a11y.**
Chạy in-page bằng computed style:
- `contrast-aa` — **WCAG AAA cho MỌI text node** (tính tỉ lệ tương phản từ màu chữ + nền hiệu dụng; 7:1 thường, 4.5:1 chữ lớn). **FAIL cứng.**
- `monochrome-surface` — pane lớn (sidebar/aside/nav) phải cùng màu nền. **FAIL cứng.**
- `rogue-slab` — **MỌI** phần tử ≥2% viewport có nền đục lệch nền body > 1.6:1. **FAIL cứng.**
  (`monochrome-surface` chỉ soi sidebar/aside/nav ⇒ mù với mảng màu lạ là `<div>` bất kỳ giữa trang.)
- `shadow-clipped` — aura outset trong cha `overflow:hidden` (có ngưỡng blur). Cảnh báo.
- `overlap` — hai control (`button/a/input/[role=button]`) KHÔNG phải cha-con mà rect chồng ≥4px cả hai chiều. Bắt lỗi **nút đè lên nhau** (vd `position:fixed` với magic-offset lúc badge rộng biến thiên). **FAIL cứng.**
- `row-misalign` — control cùng cha, gần cùng hàng (top lệch ≤6px) mà **chiều cao lệch >3px**. Bắt lỗi **nút cạnh nhau không bằng chiều cao** (vd nút toggle cao hơn badge do padding/font khác). **FAIL cứng.**
  (Hai rule này thêm 15/07/26 vì cả `/redesign-existing-projects` [đọc CSS TĨNH — không đo được rect] lẫn unit-test [kiểm NỘI DUNG, không kiểm toạ độ] đều mù với lỗi hình học lúc render. Ngưỡng overlap CỐ Ý không dùng %-diện-tích: bug thật chỉ clip mép nút = 18% dt, mọi ngưỡng % đều lọt — 2 control độc lập chồng ≥ vài px đã là lỗi.)

Mở rộng bất biến theo design spec của dự án.

**4. ĐỌC ẢNH — COVERAGE CỨNG + RUBRIC (tầng người/agent).**
MANIFEST có N route → **PHẢI `Read` đủ N ảnh**. FINDINGS phải có **một dòng cho MỖI route**
(kể cả "sạch"). Chấm theo **rubric**, không cảm tính — vd neumorphism: ① mặt đơn sắc ② bóng
không bị cắt ③ CTA phẳng accent ④ chữ/icon AA ⑤ empty-state đúng brand ⑥ focus ring.

**5. FINDINGS.md → SỬA.** Bảng `# · route · vấn đề · mức · **nguyên nhân GỐC** · cách sửa`.

**6. CHỤP LẠI → ĐỌC LẠI → mới pass.** Máy sạch **VÀ** mắt sạch. Thiếu một trong hai = chưa xong.

## Rules (luật rút từ máu — đừng lặp lại)

- **THỨ GÌ TÍNH ĐƯỢC thì PHẢI để MÁY tính — cấm giao cho mắt.** Tương phản chữ là *con số* (WCAG ratio = f(màu chữ, màu nền)). Rubric ghi "chữ đạt AA" mà **không cài bất biến** ⇒ evaluator MÙ: chữ mờ lọt qua cả trang đăng nhập, agent nhìn ảnh cũng không hình dung nổi. **Tiêu chí nào định lượng được → phải thành assert, không phải thành dòng chữ trong rubric.**
- **KHÔNG ROUTE NÀO ĐƯỢC LÀ VÙNG MÙ.** Driver login-trước ⇒ `/auth` redirect ⇒ **trang sign-in không bao giờ được audit** — đúng trang có lỗi. Phải chụp **trạng thái CHƯA đăng nhập** trước, rồi mới login. Rà lại: còn state nào (modal, error, empty, loading) chưa từng vào khung hình?
- **THEME LÀ MỘT TRẠNG THÁI — chụp ĐỦ light VÀ dark.** App thường bật dark bằng class (`.dark` trên `<html>`) theo *setting app*, KHÔNG theo `prefers-color-scheme` ⇒ headless mặc định **chỉ bao giờ thấy light**, còn dark là vùng mù tuyệt đối: user mở app ở dark thấy UI vỡ mà gate vẫn xanh. Bật `--themes light,dark` (mặc định) → lần đầu chạy lòi ra **172 chỗ** trượt AAA ở dark trong khi light sạch bong. Hệ quả thiết kế: **accent phải LẬT theo theme** (mặt sáng → accent tối; mặt tối → accent sáng); một hằng số accent cho cả 2 theme là sai từ định nghĩa. Và **cấm hardcode màu chữ trên accent** (`color:#fff`) — ở theme kia thành trắng-trên-trắng 1.13:1.
- **PHỦ *MỌI* THEME APP CUNG CẤP — danh sách lấy từ APP, không tự nghĩ.** Tôi hardcode `light,dark` trong khi app có **ba** theme (`default` / `default-dark` / `paper`) ⇒ `paper` không ai đụng ⇒ nó vỡ y hệt dark, **user tìm ra chứ không phải gate**. Luật: trước khi chạy, đọc danh sách theme từ chính app (dropdown Settings→Preferences / source `THEME_OPTIONS`) rồi phủ hết. Suy rộng: mọi TRỤC trạng thái (theme, locale, role, empty/full data) phải lấy từ app, không lấy từ trí nhớ của agent.
- **ĐỔI TRẠNG THÁI PHẢI ĐI ĐÚNG ĐƯỜNG APP ĐỔI — rồi VERIFY nó đã đổi thật.** Sai 2 tầng liên tiếp: ① gắn class `.dark` bằng tay (app dùng `data-theme` + inject CSS ⇒ cơ chế KHÔNG TỒN TẠI); ② set `localStorage` (app GHI ĐÈ lại từ setting tài khoản trên server). Cả 2 lần gate XANH trên trạng thái **không có thật** — tệ hơn đỏ. Đường chắc chắn đúng là đường **người dùng bấm** (Settings → Preferences → chọn). Và luôn có bất biến: **hai theme khác nhau mà nền y hệt ⇒ ảnh GIẢ ⇒ ASSERT FAIL** (gate đang chụp cùng một theme hai lần rồi tự khen).
- **THEME LÀ CƠ CHẾ CỦA APP, ĐỌC SOURCE TRƯỚC.** Đừng giả định `.dark` / `prefers-color-scheme`. Grep `documentElement.classList` / `data-theme` / `localStorage` / inject `<style>` để biết app đổi theme bằng gì; theme thường nạp bằng **CSS inject lúc chạy** ⇒ nó THẮNG file theme tĩnh của mình ở token thường, nhưng THUA rule `!important` ⇒ ra giao diện **nửa nạc nửa mỡ** (nền theme-app + card theme-mình = mảng màu lạ giữa trang). Sửa đúng: viết bảng màu của mình **vào chính file theme mà app inject**, không viết block `.dark{}` ở nơi app không bao giờ đọc.
- **LOGIN HỎNG = GATE PHẢI CHẾT.** Login fail ⇒ mọi route redirect `/auth` ⇒ driver audit **8 bản sao trang sign-in** rồi in "design-ok". Xanh kiểu đó tệ hơn đỏ: nó xác nhận một app mà nó chưa từng nhìn thấy. `--assert` fail ngay khi login fail.
- **USER BÁO LỖI + MÁY BÁO SẠCH ⇒ MÁY SAI, KHÔNG PHẢI USER SAI.** (bài học 14/07/26 — user: *"đây là developing không phải toà án mà bảo vệ luận điểm của mình khăng khăng như vậy"*.) Gate xanh KHÔNG phải lá chắn: nó chỉ chứng minh **cái nó được dạy**, trên **state nó chụp được**. User thấy lỗi = tồn tại một state/theme/bundle mà gate chưa từng vào. **Cấm phản biện user bằng suy đoán** ("chắc do cache", "chắc bấm nhầm phím") — mỗi lần đoán là đẩy việc kiểm chứng sang cho user, và tôi đã sai 3 lần liên tiếp kiểu đó. Đúng quy trình: (1) tin báo cáo, (2) tái hiện ĐÚNG state của user (route + theme + bundle + trạng thái đăng nhập/focus), (3) chỉ nói khi đã ĐO. Không tái hiện được thì nói thẳng "chưa tái hiện được", đừng dựng giả thuyết rồi bảo vệ nó.
- **KHỬ NGẪU NHIÊN TRƯỚC KHI CHỤP, ĐỪNG NỚI NGƯỠNG.** Con trỏ nhấp nháy + animation làm **mọi** route lệch baseline ~0.04% mỗi lần chụp ⇒ gate đỏ vĩnh viễn ⇒ bị phớt lờ ⇒ regression thật lọt qua. Driver tiêm CSS `animation/transition:none; caret-color:transparent` + ẩn con trỏ CodeMirror ngay lúc init ⇒ diff về **0%**. Nới `--diff-threshold` để "hết kêu" là **làm mù máy**, không phải sửa lỗi.
- **SELECTOR THAM LAM = TỰ BẮN VÀO CHÂN.** `[class*="cursor"]` trong CSS khử-nhiễu trúng luôn `cursor-pointer`/`cursor-text` của Tailwind ⇒ **ẩn mất ô nhập ⇒ login chết ⇒ gate tự làm hỏng app nó đang kiểm**. Mọi CSS/selector do gate tiêm vào phải **hẹp nhất có thể** và phải chạy thử full-flow (login → mọi route) sau khi thêm.
- **GATE PHẢI CHẠY ĐƯỢC TỪ REPO SẠCH.** Thiếu `playwright-core` ⇒ `node route-shots.mjs` chết ngay dòng import ⇒ acceptance_test của frame UI **không bao giờ chạy** = gate chết mà không ai biết. Deps khai trong `skills/visual-qa/assets/package.json`; cài: `npm i --prefix skills/visual-qa/assets`.
- **BẰNG CHỨNG > LỜI.** Pass/fixed chỉ hợp lệ khi có FILE ẢNH. Không file = chưa làm. Cấm khai pass bằng suy luận.
- **ĐỌC HẾT, không chọn lọc.** Đọc 3/7 ảnh rồi kết luận là nguyên nhân gốc của failure `ui-pass-without-full-visual-review` — lỗi nằm sẵn trong ảnh chưa mở.
- **"Máy OK" ≠ "UI đẹp".** Bất biến chỉ biết những gì nó được dạy. Gate xanh KHÔNG phải cớ để bỏ bước đọc ảnh.
- **NGƯỠNG là con dao hai lưỡi.** Ngưỡng lỏng → lọt lỗi thật (0.5% diff bỏ lọt một regression làm phẳng toàn bộ card). Ngưỡng chặt quá → kêu oan → **gate noisy = gate CHẾT**. Baseline dùng ngưỡng 0 + duyệt tay; bất biến DOM phải có ngưỡng phân biệt lỗi thật với nhiễu.
- **CSS thì ĐO, đừng ĐOÁN.** Chẩn đoán bằng mắt sai 4 lần liên tiếp (clip → collision → sai selector → sai specificity). Chỉ khi query `getComputedStyle` mới ra gốc. Trước mọi fix CSS: **đo computed style + đo rect**, rồi mới sửa. Sau khi sửa: **đo lại** trước khi nhìn ảnh.
- **Đừng làm MÙ máy để "hết lỗi".** Hạ blur xuống dưới ngưỡng detector = che lỗi, không sửa lỗi (aura vẫn bị crop). Sửa defect, đừng sửa thước đo.
- **Trong container `overflow:hidden` (rail hẹp, tab bar): KHÔNG dùng bóng outset.** Nó sẽ bị cắt hoặc đổ vào khe → vệt xấu. Dùng **inset** (không thể tràn) hoặc bỏ bóng. `overflow-x:visible` KHÔNG khả thi khi trục kia là `auto` (CSS ép về auto).
- **playwright-core + Chrome hệ thống** (không tải chromium 130MB). Baseline diff cần `pixelmatch` + `pngjs` (nhỏ, không có thì tự bỏ qua baseline).
- **`networkidle` cấm với SPA realtime** — dùng `domcontentloaded` + chờ cố định.
- **Không dẫm `computer-use`** (desktop AX / Orca browser). Skill này là headless CLI cho SPA localhost.

## Cờ driver
`--base` `--out` `--user` `--pass` · `--route <r>` (1 route, cho frame gate) · `--assert`
(exit 1 khi: route lỗi / thiếu ảnh / vi phạm bất biến / lệch baseline) · `--baseline <dir>` ·
`--update-baseline` (duyệt thay đổi cố ý) · `--diff-threshold <%>` (mặc định 0).
