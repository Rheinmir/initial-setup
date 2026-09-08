---
name: dym-diagram-design-authoring-in-chat
description: "Vẽ sơ đồ bằng chat (không có CLI cho việc này). đây là công dụng chính của tool. Không có lệnh shell nào tạo sơ đồ — việc chọn loại, chọn nội dung và viết SVG là do agent làm, dựa trên SKILL.md và các file references/type-.md."
disable-model-invocation: true
---

# Skill: dym-diagram-design-authoring-in-chat — Vẽ sơ đồ bằng chat (không có CLI cho việc này)

**Vì sao dùng:** đây là công dụng chính của tool. Không có lệnh shell nào tạo sơ đồ — việc chọn loại, chọn nội dung và viết SVG là do **agent** làm, dựa trên `SKILL.md` và các file `references/type-*.md`.

**File này sinh ra gì:** một file `.html` tự chứa (inline SVG + inline CSS), mở được bằng `file://`, không cần build, không cần server.

> **Toàn bộ file này là câu gõ trong chat.** Đừng dán vào terminal. Phần shell nằm ở `04` và `06`.

---

## 1. Câu gõ tối thiểu

```text
Make me an architecture diagram of my app: frontend, backend, database, Redis cache.
I need a quadrant showing Q2 projects by impact vs effort.
Give me a sequence of a bearer call with token refresh on 401.
```

Agent sẽ: chọn loại → nạp `references/type-<loại>.md` tương ứng → **xác nhận với bạn trước khi vẽ** → dựng HTML → lưu file.

Bước xác nhận là bắt buộc theo `SKILL.md` §3 ("Confirm before drawing"). Nếu agent vẽ luôn không hỏi, nó đang bỏ qua skill.

---

## 2. Chọn loại — 39 lựa chọn, chọn theo *thứ bạn đang thể hiện*

`SKILL.md` §3 không hỏi "bạn muốn sơ đồ gì" mà hỏi "bạn đang cho thấy cái gì". Bảng rút gọn theo nhóm:

**Cấu trúc & hệ thống**
| Đang cho thấy… | Loại |
|---|---|
| Thành phần + kết nối trong một hệ thống | Architecture |
| Cảnh quan IT cũ nhóm theo phase/phòng ban (trạng thái *before* của đề xuất hiện đại hoá) | IT current-state |
| Phần mềm chạy ở đâu — zone, host, artifact, replica, port | Deployment |
| Cái gì phụ thuộc cái gì, có fan-in và chu trình mà cây không diễn đạt được | Dependency graph |
| Phân cấp bằng bao chứa / phạm vi | Nested |
| Quan hệ cha → con | Tree |
| Sở hữu/báo cáo/định tuyến/escalation của người hoặc agent | Org chart |
| Các tầng trừu tượng xếp chồng | Layer stack |
| Class + operation + kế thừa + composition | UML class |

**Luồng & thời gian**
| Đang cho thấy… | Loại |
|---|---|
| Logic quyết định có nhánh | Flowchart |
| Thông điệp giữa các actor theo thứ tự thời gian | Sequence |
| Trạng thái + chuyển tiếp + guard | State machine |
| Quy trình liên phòng ban có bàn giao | Swimlane |
| Sự kiện đặt trên trục thời gian | Timeline |
| Task và phase trên timeline | Gantt |
| Chu trình tự tăng cường (flywheel), bước cuối nuôi bước đầu | Loop |
| Quy trình tuần tự nhiều actor có bàn giao dữ liệu | Process |
| Hành trình người dùng qua các giai đoạn + cảm xúc | User journey |
| Xương sống câu chuyện cắt theo release, có đường cắt | Story map |
| Công việc theo trạng thái, có WIP limit và mục bị chặn | Kanban |

**Dữ liệu**
| Đang cho thấy… | Loại |
|---|---|
| Thực thể + trường + quan hệ | ER / data model |
| Bảng vật lý: kiểu SQL, ràng buộc, index, FK cấp cột | Database schema |
| Stack dữ liệu đầu-cuối trên cụm container | High-Level |
| Lưu trữ nhiều tầng có mức chất lượng và chính sách truy cập | Medallion |
| Luồng dữ liệu theo vai trò: ai làm gì ở mỗi bước pipeline | Data flow |
| Topology tích hợp nền tảng dữ liệu: nguồn → lõi → tiêu thụ | DP integration |
| Ma trận quyền theo vai trò / thành phần | DP security matrix |

**Định lượng**
| Đang cho thấy… | Loại |
|---|---|
| So sánh định lượng giữa các hạng mục | Bar chart |
| Xu hướng liên tục theo thời gian; đổi giữa đúng 2 trạng thái (slopegraph); một phân phối mỗi series (ridgeline); dịch chuyển thứ hạng qua nhiều mốc (bump) | Line chart |
| Phân phối và tương quan 2 biến; 3 biến với mark theo diện tích (bubble); 1 biến với một chấm mỗi mục (beeswarm) | Scatter plot |
| Định vị 2 trục / ưu tiên hoá | Quadrant |
| Nhiều thực thể chấm điểm trên 3–5 tiêu chí định lượng | Radar / Spider |
| Một series định lượng qua các hạng mục có chu kỳ; góc=hạng mục, bán kính=độ lớn | Polar chart |
| Phần-trên-tổng nơi kích thước tương đối là câu chuyện | Treemap |
| Một lượng tách và nhập qua các stage, bề rộng dải = số lượng | Sankey |
| Phân cấp xếp hạng hoặc tỉ lệ rơi rụng chuyển đổi | Pyramid / funnel |
| Chồng lấn giữa các tập | Venn |
| Nguyên nhân của một hệ quả, nhóm theo hạng mục (phân tích căn nguyên) | Fishbone |
| Chuỗi giá trị đối chiếu độ tiến hoá — xây gì, mua gì, cái gì đang dịch chuyển | Wardley map |

Ba quy tắc ngón tay cái, nguyên văn `SKILL.md` §3:

- Nếu một bảng 3 cột nói được điều tương tự, **chọn bảng**.
- Hai loại cùng hợp lý → chọn theo trục trội. Semantic pattern có thể thêm primitive, **không** thêm ngữ pháp bố cục thứ hai.
- Vượt ngân sách độ phức tạp (§7) → **tách thành overview + detail**.

---

## 3. Semantic pattern — chọn *hành vi* trước, *hình dạng* sau

Khi hành vi mới là thứ quan trọng, skill chọn **semantic pattern** trước rồi mới chọn visual type. Bảy pattern được định tuyến (`references/semantic-patterns.md`):

1. Hàng đợi fan-in và nút thắt cổ chai
2. Ô stage lặp lại
3. Biến đổi đầu vào phi cấu trúc
4. Vết chính sách theo cặp (paired policy trace)
5. Paved road bảo mật
6. Catalog quản trị
7. Lớp bảo mật bù trừ (compensating)

Mỗi pattern tự khai: trigger, primitive, ngân sách, anti-pattern, **fallback tĩnh**, và visual type gần nhất.

Ví dụ gõ:

```text
Show the ingestion queue with its bottleneck — use the fan-in semantic pattern.
Draw the paved road for our deploy path, with the compensating controls layered on.
```

---

## 4. Chuyển động (motion) — mặc định TẮT

`references/animation.md` định nghĩa 4 mode: `none` (mặc định), `reveal`, `step`, `loop`. Luật cứng:

- Output thường là **tĩnh và không script**. Motion phải được yêu cầu rõ ràng.
- Mọi file có motion phải có **khung tĩnh đầu tiên hoàn chỉnh** và **timing tất định**.
- `prefers-reduced-motion` → hiện khung tĩnh đầy đủ, ẩn/vô hiệu nút điều khiển.
- HTML motion dùng **đúng controller đã review trong `template-motion.html`**, verbatim. Script inline tuỳ ý, asset từ xa, CSS `@import`, và thuộc tính HTML thực thi được đều **bị từ chối** (linter `lint-skin.py` chặn cứng — xem `06`).
- ADR 0003: `reveal` là **autoplay duy nhất được phép**.

Gõ:

```text
Make it animated with the reveal mode, respecting reduced motion.
```

Ví dụ tự chứa để xem trước: `skills/diagram-design/assets/example-policy-trace-animated.html`.

---

## 5. Bốn núm chỉnh — nói ra thì được đúng ý ngay

Bốn "dial" này áp cho cả sơ đồ mới lẫn sơ đồ import (`references/output-spec.md`):

| Núm | Giá trị | Mặc định |
|---|---|---|
| **format** | `html`, `svg`, `png`, `html+png` | `html` |
| **size** | `doc-inline`, `doc-wide`, `slide-16x9`, `slide-4x3`, `social-og`, `social-square`, `print-a4-landscape`, `print-letter-landscape`, `fit` | `doc-inline` |
| **detail** | `faithful` (≤24 node, chia zone), `balanced` (≤12), `simplified` (≤7) | `balanced` |
| **audience** | `engineer`, `mixed`, `executive` | `mixed` |

`audience` chi phối **cách dùng từ**, không phải số phần tử — đây là chỗ rất hay bị hiểu nhầm.

Bảng viewBox thật (`output-spec.md` §2):

| Preset | viewBox | Tỉ lệ | PNG @2 | Dùng cho |
|---|---|---|---|---|
| `doc-inline` | `0 0 960 600` | 8:5 | 1920×1200 | Blog, README, docs |
| `doc-wide` | `0 0 1280 720` | 16:9 | 2560×1440 | Docs full-width, Confluence/Notion |
| `slide-16x9` | `0 0 1280 720` | 16:9 | 2560×1440 | Slide deck |
| `slide-4x3` | `0 0 1024 768` | 4:3 | 2048×1536 | Deck cũ |
| `social-og` | `0 0 1200 632` | ~1.9:1 | 2400×1264 | Link preview X/LinkedIn — **chừa 64px lề mọi phía**, link-card sẽ crop |
| `social-square` | `0 0 1080 1080` | 1:1 | 2160×2160 | Post feed |
| `print-a4-landscape` | `0 0 1120 792` | ~1.41:1 | @3 → 3360×2376 | Handout in |
| `print-letter-landscape` | `0 0 1056 816` | ~1.29:1 | @3 → 3168×2448 | Handout in (US) |
| `fit` | suy ra từ nội dung | bất kỳ | @2 | Bàn giao vector |

Gõ:

```text
Same diagram at slide-16x9, simplified, executive audience.
```

---

## 6. Bắt đầu từ template thay vì từ con số 0

Ba template này copy bằng shell nhưng **điền bằng chat** — nên để ở đây cho liền mạch:

```bash
cp skills/diagram-design/assets/template.html        my-diagram.html  # light tối giản
cp skills/diagram-design/assets/template-full.html   my-diagram.html  # editorial + summary card
cp skills/diagram-design/assets/template-motion.html my-diagram.html  # có motion, accessible
```

Rồi gõ trong chat: *"fill `my-diagram.html` with an architecture diagram of …"*.

---

## 7. Những gì skill sẽ TỪ CHỐI làm (và vì sao)

`SKILL.md` §4 "Universal Anti-patterns" và §9 "Pre-Output Checklist (Taste Gate)" chạy **trước khi ghi file**. Triết lý một câu, nguyên văn: *"The highest-quality move is usually deletion."*

Ba thứ được bảo đảm ở mọi output:

- **Accessible SVG**: `role="img"`, `aria-labelledby` phân giải được, `<title>`/`<desc>` là con đầu tiên. ID có tiền tố theo sơ đồ và theo biến thể, để nhiều SVG inline chung một trang không giành nhau accessible name. Icon trang trí bị ẩn khỏi assistive tech.
- **Một file, không phụ thuộc ngoài**: không asset từ xa ngoài stylesheet Google Fonts đã duyệt, không script ngoài controller motion chính tắc, không thuộc tính thực thi được.
- **Lưới 4px** và ngân sách độ phức tạp cho từng loại.

Nếu bạn ép nó vượt ngân sách, nó sẽ đề xuất tách overview + detail chứ không nhồi.

---

## 8. Xong bước này khi

- [ ] Có một file `.html` mở bằng `file://` hiển thị đúng.
- [ ] Chạy `python3 <skill-dir>/scripts/self_check.py file.html` được `OK` (xem `06`).
- [ ] Màu trong file là brand của bạn, không phải atomic-tangerine.

**Tiếp theo:** đã có sơ đồ từ draw.io/Mermaid thì sang `04`/`05`; muốn xuất PNG/SVG thì `05`; muốn khoá chất lượng bằng CI thì `06`.
