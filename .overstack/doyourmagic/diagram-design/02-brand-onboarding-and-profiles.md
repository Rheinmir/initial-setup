# 02 — Onboard brand và quản lý profile khách hàng

**Vì sao dùng:** sơ đồ **đầu tiên** trong một dự án mới sẽ bị **chặn** bởi một cổng bắt buộc. Skill từ chối im lặng xuất sơ đồ mang màu mặc định vào một dự án có brand. Không biết cổng này thì bạn tưởng agent bị treo.

**File này sinh ra gì:** một `style-guide.md` mang màu và font của bạn, cộng (tuỳ chọn) một thư viện profile ở `~/.diagram-design/profiles/` dùng chung được cho nhiều khách hàng.

> Toàn bộ file này là **thao tác chat** — trừ vài lệnh `mkdir`/`cat` để soi file trên đĩa. Không có CLI onboarding.

---

## 1. Cổng style-guide chạy như thế nào

Trích `SKILL.md` §0 — trước khi vẽ sơ đồ đầu tiên, skill:

1. Tìm marker `<project-root>/.diagram-design`. Marker hợp lệ trỏ tới profile có thật → **chọn thẳng profile đó, bỏ qua cổng**. `profile: default` cũng bỏ qua cổng.
2. Không có marker → mở `references/style-guide.md` và so với token mặc định đã ship: paper `#f5f5f5`, ink `#2d3142`, accent `#eb6c36` (atomic-tangerine).
3. Vẫn y nguyên mặc định → **dừng lại và hỏi bạn**, đúng 6 lựa chọn:

> *"This is your first diagram in this project. The style guide is still at the default (neutral white-smoke + atomic-tangerine). Do you want to customize it to match your brand first? Options: (a) pull from your website URL, (b) extract from an installed skill, (c) extract from a local folder / design-system directory, (d) paste tokens manually, (e) proceed with the default for now, (f) load a saved client profile."*

Sau khi đã tuỳ biến (hoặc bạn chọn (e)), cổng không hỏi lại nữa.

**Trạng thái "custom-unsaved":** token khác mặc định nhưng không có profile header ở đầu file → skill bỏ qua cổng và **mời bạn lưu thành profile**. Đừng bỏ lỡ lời mời đó, vì bản cập nhật plugin có thể ghi đè working copy.

---

## 2. Đường nhanh nhất — onboard từ website

Gõ trong chat:

```text
onboard diagram-design to https://yoursite.com
```

Luồng, theo `README.md` §Onboarding và `references/onboarding.md` §URL:

```
→ tải trang chủ
→ trích palette trội + font stack
→ ánh xạ vào 5 vai trò ngữ nghĩa: paper, ink, muted, accent, link
→ hiện diff đề xuất
→ (bạn duyệt) ghi token vào references/style-guide.md
```

Bảng ánh xạ thật (README §"What gets extracted"):

| Lấy từ site của bạn | Thành token |
|---|---|
| Nền `<body>` | `paper` |
| Màu chữ chính | `ink` |
| Chữ phụ / caption | `muted` |
| Card / container | `paper-2` |
| Màu brand dùng nhiều nhất (CTA, link, heading) | `accent` |
| Font của `<h1>` | `title` |
| Font của `<body>` | `node-name` |
| Font của `<code>` / `<pre>` | `sublabel` |

Hai thứ chạy tự động, không phải hỏi:

- **Kiểm tương phản WCAG AA** cho `ink` trên `paper` **trước khi ghi**. Màu của bạn trượt ở cỡ chữ 9–12px thì skill đề xuất giá trị đã hiệu chỉnh và giải thích vì sao.
- **Biên lai fidelity**: URL đã lấy mẫu, vai trò từng màu, họ font + trọng lượng, URL nguồn font, và mọi fallback. Font public của site được dùng thật rồi verify sau khi render, chứ không âm thầm thay bằng font hệ thống.

### Ba đường onboard còn lại

| Cách | Gõ gì | Khi nào |
|---|---|---|
| Từ một skill đã cài | *"onboard diagram-design from the `<tên-skill>` skill"* | Bạn đã có một skill khác chứa design token |
| Từ thư mục local | *"onboard diagram-design from ./design-system"* | Có sẵn thư mục design-system / token file |
| Dán tay | *"set diagram-design tokens: paper #…, ink #…, accent #…"* | Bạn biết chính xác mã màu |

Chi tiết từng nhánh nằm ở `references/onboarding.md` (§URL, §Skill, §Folder).

### Sửa tay, không qua agent

Mở `skills/diagram-design/references/style-guide.md` và sửa thẳng bảng token. Mọi thứ phía sau đọc từ đó — cả 39 loại sơ đồ, primitive annotation, và gallery — vì chúng tham chiếu **tên vai trò** (`accent`), không phải mã màu (`#eb6c36`).

---

## 3. Profile — làm việc với nhiều khách hàng

Đây là phần đáng giá nhất và cũng dễ hiểu sai nhất.

### Đường dẫn chuẩn (từ `references/profiles.md` §"Paths and terms")

| Thứ | Đường dẫn |
|---|---|
| Thư viện profile | `~/.diagram-design/profiles/` |
| Một profile | `~/.diagram-design/profiles/<slug>.md` |
| Marker dự án | `<project-root>/.diagram-design` |

Nội dung marker đúng **một dòng, đúng ngữ pháp này**:

```text
profile: <slug>
```

Marker được đối xử như **dữ liệu không đáng tin** (untrusted repository data). Chỉ đúng ngữ pháp trên mới được chấp nhận; sai định dạng hoặc trỏ tới profile không tồn tại thì skill **báo lỗi rõ ràng**, không đoán, không tự sửa.

### Vì sao dùng marker thay vì copy-đè

Dự án có marker thì skill **đọc thẳng** `~/.diagram-design/profiles/<slug>.md` và **để nguyên working copy đã cài**. Nghĩa là ba workspace song song, ba brand khác nhau, không cái nào đè cái nào. Đây là điểm khác biệt so với `load` kiểu copy-over.

### Các verb của lệnh `/profile`

Ở Claude Code gõ `/diagram-design:profile`; ở Factory Droid / Pi gõ `/profile`.

| Gõ | Làm gì |
|---|---|
| `/profile` (không tham số) | `list`, đánh dấu profile đang active theo marker hoặc working copy |
| `/profile <name>` (không verb) | tương đương `load <name>` |
| `/profile list` | liệt kê thư viện |
| `/profile save [name]` | lưu style-guide hiện tại thành profile |
| `/profile load [name]` | nạp profile (copy-over) |
| `/profile switch <name>` | **đồng nghĩa `load`** — có thật, dù không xuất hiện trong argument-hint |
| `/profile show` | xem profile đang active |
| `/profile update [name]` | cập nhật profile đã có |
| `/profile reset` | đưa về mặc định |
| `/profile delete [name]` | xoá profile |

Verb lạ hoặc thừa tham số → skill in các dạng hợp lệ và **dừng, không ghi gì**.

### Bốn quy tắc an toàn (từ `commands/profile.md` §"Required behavior")

1. **Luôn xác nhận trước** khi ghi đè profile đã có, đổi marker dự án, hoặc xoá profile — **kể cả khi lệnh được gọi từ script**. Không có đường bỏ qua xác nhận.
2. Dự án chọn bằng marker: đọc thẳng profile, **không** copy đè working copy.
3. Với `load` kiểu copy-over: **verify lại sau khi ghi**. Đích không ghi được thì skill đề xuất chuyển sang luồng marker.
4. Sau `save`/`update`: xác nhận đúng **một** metadata header và phần thân không đổi.

Và một câu đáng dán lên tường, nguyên văn từ command: *"Never claim a write succeeded without re-reading it."*

---

## 4. Công thức đủ dùng cho agency 3 khách hàng

```bash
# một lần, tạo thư viện
mkdir -p ~/.diagram-design/profiles
```

Rồi trong chat, lặp cho từng khách:

```text
onboard diagram-design to https://client-a.com
/diagram-design:profile save client-a
```

Cuối cùng, ở mỗi repo dự án:

```bash
echo 'profile: client-a' > /path/to/project-a/.diagram-design
echo 'profile: client-b' > /path/to/project-b/.diagram-design
```

Kiểm tra:

```bash
ls ~/.diagram-design/profiles/
cat /path/to/project-a/.diagram-design
```

Từ giờ mọi sơ đồ sinh trong `project-a` mang brand `client-a`, không cần nhớ gì thêm, và bản cài plugin không bị đụng vào.

Profile **sống sót qua cập nhật plugin**. Working copy `style-guide.md` thì không.

---

## 5. Xong bước này khi

- [ ] `references/style-guide.md` không còn là bộ token mặc định (hoặc bạn đã cố ý chọn (e)).
- [ ] Nếu làm nhiều khách: `~/.diagram-design/profiles/` có ít nhất một `.md`, và dự án có `.diagram-design` một dòng đúng ngữ pháp.
- [ ] `/diagram-design:profile` liệt kê được và chỉ đúng profile đang active.

**Tiếp theo:** `03-authoring-in-chat.md`.
