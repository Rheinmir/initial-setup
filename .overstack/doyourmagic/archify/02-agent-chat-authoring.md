# 02 — Soạn sơ đồ từ khung chat của agent

**Vì sao dùng:** đây là đường dùng chính của Archify. Bạn mô tả hệ thống bằng ngôn ngữ tự nhiên, agent tự chọn loại sơ đồ, tự viết JSON IR theo schema, tự chạy validate/deliver, rồi trả về đường dẫn HTML.

**Kết quả nhận được:** một file HTML tự chứa, đã qua validate, cùng biên lai (SHA-256 + số byte của cả spec lẫn artifact) do agent báo lại.

> **Mọi thứ trong file này gõ vào khung chat của agent, không phải terminal.** Lệnh shell nằm ở [03-cli-authoring-loop.md](03-cli-authoring-loop.md). Đừng dán chéo giữa hai file.

## Điều kiện tiên quyết

Skill đã cài theo [01-install-and-verify.md](01-install-and-verify.md) và agent có quyền chạy shell (agent cần gọi `node bin/archify.mjs` bên dưới).

## Bước 1 — Khởi động từ mô tả, không cần repo

```text
Use Archify to draw: Browser -> API -> Redis cache -> PostgreSQL fallback.
```

Khi cần sơ đồ bám mã thật, mở repo rồi hỏi:

```text
Analyze this repository, then use archify to create a high-level runtime architecture diagram.
Show 8–12 core components, one primary path, external dependencies, and trust boundaries.
Put supporting detail in cards instead of adding more edges.
```

## Bước 2 — Nói rõ loại sơ đồ khi bạn đã biết mình muốn gì

Bảng router lấy nguyên từ `SKILL.md` mục "Type router":

| Loại | Dùng cho | Nêu trong prompt |
|---|---|---|
| `architecture` | Thành phần, dịch vụ, biên cloud/bảo mật, hạ tầng | Phạm vi, thành phần lõi, đường chính |
| `workflow` | Quy trình, cổng duyệt, tool call, runbook, CI/CD | Người tham gia, thứ tự, nhánh rẽ, ngoại lệ |
| `sequence` | Chuỗi gọi API, vòng đời request, trace bất đồng bộ, giá trị trả về | Bên gọi, bên bị gọi, return, thời điểm |
| `dataflow` | Pipeline, ETL/ELT, lineage, quản trị dữ liệu, bên tiêu thụ | Nguồn, phép biến đổi, kho, biên |
| `lifecycle` | Chuyển trạng thái, retry, chờ, trạng thái kết thúc | Trạng thái, sự kiện, đường retry/huỷ |

Chưa chắc chọn gì thì hỏi thẳng, agent sẽ chạy `guide` giúp:

```text
Which Archify diagram type fits: "Show CI/CD checks, approval, deploy, and rollback"?
```

## Bước 3 — Tinh chỉnh từng vòng nhỏ

Archify giữ nguồn JSON đã gõ, nên yêu cầu hẹp là rẻ và ổn định:

```text
add Redis
move auth to the left
highlight the rollback path
put the retry budget in a card instead of a new edge
```

Nguyên tắc trong `SKILL.md` mà agent buộc phải theo, bạn nên biết để không yêu cầu ngược:

- **Một đường chính rõ ràng**, nhánh phụ rẽ ra từ node gần nhất trên đường chính. Tối đa ~12 node chính.
- **Chi tiết bổ trợ đi vào `cards`**, không đẻ thêm cạnh.
- Agent chỉ được thêm điều khiển hình học (`via`, `channelX`, `channelY`, `labelAt`) **sau khi** một chẩn đoán cụ thể đòi, và mỗi vòng sửa đúng một thứ.
- Nhãn quan hệ là **dữ liệu ngữ nghĩa**. Xoá nhãn không phải cách sửa va chạm hình học — agent phải dời nhãn, đổi route, giãn khoảng cách trước, rồi mới rút gọn chữ mà vẫn giữ nghĩa.

## Bước 4 — Dán Mermaid vào

Archify **không** parse Mermaid một cách máy móc; agent đọc Mermaid để lấy topology rồi soạn JSON Archify mới:

```text
Convert this Mermaid to an Archify diagram:

flowchart LR
  A[Client] --> B[Gateway]
  B --> C[(Postgres)]
```

Ánh xạ, theo `SKILL.md` mục "Mermaid input":

- `flowchart` / `graph` → `workflow` (hoặc `architecture` nếu là bản đồ thành phần)
- `sequenceDiagram` → `sequence`
- `stateDiagram` → `lifecycle`

## Bước 5 — Yêu cầu tuỳ chọn (chỉ nói khi bạn thực sự cần)

Mặc định Archify chọn bản tĩnh, preset `classic`, không subtitle, legend `auto`. Chỉ nêu khi muốn khác:

```text
make it showcase quality
use the signal-flow visual preset
enable trace animation for the demo
set the viewer UI language to zh-CN
add up to five guided story chapters
```

`meta.locale` chỉ nhận `en` hoặc `zh-CN`, và **chỉ** đổi phần UI của viewer (tiêu đề trang, Legend, thông báo lỗi, a11y, thuộc tính `lang`) — không dịch nội dung bạn viết. Với mọi ngôn ngữ khác, agent phải bỏ `meta.locale` và **nói rõ** rằng UI viewer rơi về tiếng Anh.

## Bước 6 — Đọc phần agent trả về, và biết khi nào nó đang nói quá

Theo `SKILL.md` mục "Output", agent phải trả về: đường dẫn HTML đã kiểm, loại sơ đồ, tóm tắt validate, biên lai spec/artifact, trạng thái bằng chứng trình duyệt, và trạng thái review thị giác **trung thực**.

Ba tuyên bố này tách rời nhau, đừng để bị gộp:

| Tuyên bố | Được chứng minh bởi | KHÔNG chứng minh |
|---|---|---|
| Artifact qua kiểm tất định | `deliver` (9 artifact check, 0 lỗi 0 cảnh báo ở profile showcase) | Trông đẹp hay không |
| Hành vi thật trong trình duyệt | `visual-check` (xem [05](05-visual-check-and-preview.md)) | Thẩm mỹ |
| Review thị giác | Người thật hoặc reviewer đọc được ảnh | — |

Dấu hiệu agent nói quá, chặn ngay:

- Một biên lai chỉ có **4** artifact check bị gọi là "showcase". Showcase phải đủ **9** check, 0 lỗi, 0 cảnh báo.
- Lệnh thoát khác 0 mà vẫn được mô tả là thành công — `SKILL.md` cấm điều này bằng chữ.
- "Đã kiểm tra bằng mắt" khi chưa có ai mở HTML.

## Bước 7 — Khám phá artifact

HTML sinh ra đã có sẵn phím tắt, không cần cài thêm gì:

| Hành động | Phím |
|---|---|
| Mở Diagram Guide | <kbd>?</kbd> |
| Tìm và focus một node | <kbd>/</kbd> |
| Dò một tuyến có hướng | <kbd>R</kbd> |
| So một hoặc hai vai trò | <kbd>L</kbd> |
| Radar tổng quan | <kbd>M</kbd> |
| Chạy story / đổi chương | <kbd>P</kbd> / <kbd>[</kbd> <kbd>]</kbd> |
| Chế độ trình chiếu | <kbd>F</kbd> |
| Đổi style / theme / mở Export | <kbd>S</kbd> / <kbd>T</kbd> / <kbd>E</kbd> |
| Zoom / reset | <kbd>+</kbd> / <kbd>-</kbd> / <kbd>0</kbd> |

Link sâu ổn định: `#focus=<id>`, `#focus=<id>&reach=upstream|downstream`, `#relation=<id>`, `#route=<source>~<target>`, `#lens=<kind>~<kind>`, `#view=<view-id>`.
