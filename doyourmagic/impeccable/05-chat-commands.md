# 05 — 23 lệnh `/impeccable` (chỉ gõ trong CHAT)

**Vì sao dùng:** một bộ từ vựng design chung với agent — `audit`, `critique`, `polish`, `harden`... — thay vì mỗi lần lại mô tả lại từ đầu.
**Sinh ra cái gì:** thay đổi code trong dự án, cộng các artifact dưới `.impeccable/` (`PRODUCT.md`, `DESIGN.md`, `surfaces/*.md`, `critique/*.md`).

> ⚠️ **Mọi thứ trong file này gõ trong khung chat của AI agent, KHÔNG phải terminal.** CLI chặn cố ý:
> ```
> $ npx impeccable init
> "init" is not a CLI command. Type /impeccable init in your AI coding agent's chat ...   (rc 1)
> ```
> Lệnh shell nằm ở `01`–`04`. Đừng trộn hai loại.

---

## Bắt đầu: `/impeccable init` (một lần cho mỗi dự án)

```
/impeccable init
```

`init` soi dự án, hỏi **chỉ những khoảng trống thật sự** về bối cảnh sản phẩm bền vững, rồi ghi `PRODUCT.md` (người dùng, mục đích, bối cảnh vận hành, ràng buộc, giọng điệu, bằng chứng). Nếu đã có code, nó đề nghị luôn `DESIGN.md` (màu, typography, component). Nó cũng cấu hình trước live mode và ghi `buildPath` vào `.impeccable/config.json`.

Mọi lệnh khác đọc hai file này trước khi làm việc. Bỏ `init` là mọi lệnh sau đó đoán mò bối cảnh.

`buildPath` có hai giá trị:

| Giá trị | Nghĩa |
|---|---|
| `"comp"` | Sinh bản comp full-fidelity trước rồi build bám theo. Đậm hơn, lâu hơn. |
| `"code"` | Build thẳng bằng code, tham vọng ghi vào direction contract của surface brief. Gọn hơn, nhanh hơn. |

```json
{ "buildPath": "comp" }
```

Ghi đè trên một máy bằng `.impeccable/config.local.json` (ví dụ harness của bạn không có image generation). Không cần chạy lại `init` để đổi: mỗi trang quyết định có toggle ở footer, lật là bind cho phiên đó.

## 23 lệnh

Đếm và mô tả lấy từ `plugin/skills/impeccable/scripts/command-metadata.json`, không phải từ bảng trong README.

### Thiết lập & bối cảnh

| Lệnh | Tham số | Làm gì |
|---|---|---|
| `/impeccable init` | — | Setup một lần: PRODUCT.md, cấu hình live, gợi ý bước kế |
| `/impeccable document` | — | Sinh `DESIGN.md` từ code đang có (màu, type, spacing, radii, component). Theo format Google Stitch |
| `/impeccable extract` | `[target]` | Gom pattern/component/token lặp lại vào design system |
| `/impeccable shape` | `[feature]` | Lên UX/UI **trước khi** viết code, có phỏng vấn nhiều vòng |

### Review & đánh giá

| Lệnh | Tham số | Làm gì |
|---|---|---|
| `/impeccable critique` | `[area]` | Review dưới góc UX: hierarchy, information architecture, cognitive load, cộng hưởng cảm xúc |
| `/impeccable audit` | `[area]` | Kiểm tra kỹ thuật: a11y, performance, theming, responsive, anti-pattern. Ra báo cáo có điểm và mức P0–P3 |

### Sửa & hoàn thiện

| Lệnh | Tham số | Làm gì |
|---|---|---|
| `/impeccable polish` | `[target]` | Pass cuối: alignment, spacing, nhất quán, micro-detail |
| `/impeccable harden` | `[target]` | Sẵn sàng production: error handling, i18n, tràn chữ, edge case |
| `/impeccable clarify` | `[target]` | Sửa UX copy, thông báo lỗi, microcopy, nhãn |
| `/impeccable optimize` | `[target]` | Chẩn và sửa performance UI: tải, render, animation |
| `/impeccable adapt` | `[target] [context]` | Responsive: breakpoint, layout co giãn, vùng chạm |

### Đổi hướng thẩm mỹ

| Lệnh | Tham số | Làm gì |
|---|---|---|
| `/impeccable bolder` | `[target]` | Đẩy thiết kế an toàn/nhạt lên mức thú vị hơn |
| `/impeccable quieter` | `[target]` | Hạ nhiệt thiết kế quá gắt, giữ chủ đích |
| `/impeccable distill` | `[target]` | Bóc về phần cốt lõi, bỏ phức tạp thừa |
| `/impeccable delight` | `[target]` | Thêm khoảnh khắc vui, cá tính |
| `/impeccable overdrive` | `[target]` | Đẩy qua giới hạn thường thấy bằng kỹ thuật tham vọng |

### Miền cụ thể

| Lệnh | Tham số | Làm gì |
|---|---|---|
| `/impeccable typeset` | `[target]` | Font, hierarchy, cỡ, weight, độ đọc |
| `/impeccable layout` | `[target]` | Layout, spacing, nhịp thị giác; sửa grid đơn điệu |
| `/impeccable colorize` | `[target]` | Thêm màu có chiến lược cho giao diện quá đơn sắc |
| `/impeccable animate` | `[target]` | Motion có mục đích, micro-interaction |
| `/impeccable onboard` | `[target]` | Luồng onboarding, first-run, empty state |

### Chế độ đặc biệt

| Lệnh | Tham số | Làm gì |
|---|---|---|
| `/impeccable live` | — | Chọn element trong trình duyệt, sinh biến thể HTML+CSS, hot-swap qua HMR |
| `/impeccable craft` | `[mô tả]` | **Deprecated**: alias tương thích cho một yêu cầu new-work thường. Không thêm hành vi gì |

## Cách gọi

Hầu hết lệnh nhận một tham số tuỳ chọn để khoanh vùng:

```
/impeccable audit blog            # audit trang hub + trang bài blog
/impeccable critique landing      # review UX trang landing
/impeccable polish settings       # pass cuối trước khi ship
/impeccable harden checkout       # error handling + edge case
```

Hoặc mô tả thẳng, không cần lệnh con:

```
/impeccable làm lại khối hero này
```

Gõ `/impeccable` một mình để agent liệt kê toàn bộ lệnh.

**Codex** dùng skill chứ không dùng `/prompts:` — mở `/skills` hoặc gõ `$impeccable`. Bản cài repo-local nằm ở `.agents/skills/`, bản user-wide ở `~/.agents/skills/`. GitHub Copilot dùng `.github/skills/`. Skill mới cài mà chưa thấy thì khởi động lại tool.

## Ghim lệnh hay dùng

```
/impeccable pin audit      → tạo shortcut /audit
/impeccable unpin audit
```

Thực thi bởi `scripts/pin.mjs` trong bản cài skill.

## `/impeccable live` — cần gì để chạy

Live mode chỉ chạy khi có **dev server đang chạy kèm HMR** (Vite, Next.js, Bun...), hoặc một file HTML tĩnh đang mở trong trình duyệt.

Dây nối được ghi vào `.impeccable/live/config.json` (file này **commit**). Đây là file thật của repo Impeccable:

```json
{
  "files": ["site/layouts/Base.astro"],
  "insertBefore": "</body>",
  "commentSyntax": "html",
  "cspChecked": true
}
```

Vòng lặp (từ `reference/live.md`): agent boot `live.mjs` → bạn mở URL app → agent poll bằng `live-poll.mjs` (timeout dài, 600000 ms) → bạn chọn element và hành động trong overlay → agent sinh biến thể → bạn accept/discard.

Vài điều đáng biết khi dùng:

- **Đừng mở URL của `serverPort`.** Đó là cổng của helper, không phải app. Mở đúng URL app phục vụ `pageFile`.
- **Ký hiệu Impeccable trên thanh overlay** mờ đi kèm chấm hổ phách nhấp nháy khi không có ai đang poll `/poll` — nghĩa là vòng lặp đã đứt, cần khởi động lại poll.
- **Đứt giữa chừng thì đừng đoán.** Journal dưới `.impeccable/live/sessions/` là nguồn chân lý; agent chạy `live-status.mjs` hoặc `live-resume.mjs` để phát lại phần chưa xác nhận.
- Hành vi khác nhau theo harness: Claude Code chạy poll như background task; Cursor dùng poll one-shot trong terminal nền (đừng dùng `--stream`); Codex dùng poll foreground đã yield.

Luồng live đầu-cuối **chưa được chạy thật** trong lượt khảo sát này (cần dev server + harness thật); phần trên đọc từ `plugin/skills/impeccable/reference/live.md` và `scripts/live*.mjs`.

## Tự chẩn đoán

```
node .claude/skills/impeccable/scripts/doctor.mjs           # báo cáo cho người đọc
node .claude/skills/impeccable/scripts/doctor.mjs --json    # cho lệnh trong skill
node .claude/skills/impeccable/scripts/doctor.mjs --fix     # chỉ áp các migration máy móc
```

`doctor` quét độ lệch của artifact Impeccable trong dự án: git drift, sweep từng workspace, kiểm ignore-list đối chiếu registry luật đang sống, phân giải script hook. `--fix` cố ý hẹp — chỉ chạy migration mức `auto`, những thứ không cần phán đoán. **Finding không phải lỗi**: mã thoát là 0 trừ khi bản thân lượt chạy hỏng.
