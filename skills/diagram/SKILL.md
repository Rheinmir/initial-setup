---
name: diagram
description: >-
  Vẽ SƠ ĐỒ và BIỂU ĐỒ bằng máy, không để model tự bịa hình. Gọi khi user nói —
  tiếng Việt "vẽ sơ đồ", "vẽ biểu đồ", "vẽ luồng", "sơ đồ kiến trúc", "sơ đồ hệ thống",
  "sơ đồ quy trình", "luồng xử lý", "flow", "graph", "đồ thị", "biểu đồ", "chart",
  "trực quan hoá", "visualize", "mô hình hoá", "vẽ hộ", "diagram hoá", "chuyển mô tả
  thành hình", "so sánh hai luồng"; tiếng Anh "draw a diagram", "architecture diagram",
  "workflow diagram", "sequence diagram", "data flow", "state machine", "lifecycle",
  "dependency graph", "org chart", "chart", "plot", "dashboard", "visualize this",
  "turn this into a diagram", "convert Mermaid", "diff two flows". Bao cả hai họ —
  sơ đồ QUAN HỆ/LUỒNG (hộp + mũi tên) và biểu đồ DỮ LIỆU (số liệu). KHÔNG dùng cho
  màn hình UI/landing page — đó là `hallmark`.
---

# diagram — vẽ đúng bằng máy, không để model bịa hình

Nguyên tắc trung tâm, mượn của `archify` và giữ nguyên vì nó đúng: **model KHÔNG vẽ**.
Model chỉ điền logic vào một tờ khai có schema (có những khối nào, khối A nối khối B ra sao).
Việc dựng hình là của **code tất định**. Vẽ xong, máy tự soi lại bố cục; hỏng thì **giữ nguyên
bản tốt trước đó** và nói rõ chỗ sai, tuyệt đối không nhả ra một hình rác.

Đó cũng là lý do skill này tồn tại thay vì để model tự vẽ SVG: một cái hình sai trông vẫn
"có vẻ được", nên lỗi bố cục là loại lỗi đi lọt xa nhất.

## Chọn nhánh trước khi làm bất cứ gì

| Bạn đang thể hiện cái gì | Nhánh | Engine |
|---|---|---|
| Quan hệ / luồng / trình tự giữa các thành phần (hộp + mũi tên) | **Sơ đồ** | `archify` |
| Số liệu — so sánh, phân bố, xu hướng, tỉ trọng | **Biểu đồ** | `dataviz` + kỷ luật lieflat dưới đây |
| Một màn hình sản phẩm | **không phải việc ở đây** | `hallmark` |

Không chắc? Hỏi: *"cái tôi vẽ có TRỤC SỐ không?"* Có → biểu đồ. Không → sơ đồ.

## Nhánh SƠ ĐỒ — qua `archify`

Engine ngoài, KÉO NGOÀI theo `[[adapt-modes]]`: ta **không** viết lại, chỉ ghim + gọi.
Cài: `npx skills add Rheinmir/archify -g -s archify` (đích thật là `~/.agents/skills/archify`).
Đây là **fork** của `tt-a1i/archify`: thêm preset thứ 5 `macos` (liquid glass + Roboto) và đặt
làm **mặc định** — bỏ trống `meta.visual_preset` là ra đúng theme của nhà, không phải áp thêm
bước nào. Nhánh vá `macos-roboto` là nhánh MẶC ĐỊNH của fork, nên không cần ghim ref.

Hai cái bẫy đã trả giá, đừng lặp lại:

- **Không có cờ `--ref`.** Và `owner/repo@nhánh` KHÔNG ghim được nhánh lúc cài: CLI in ra
  `Source: …git @macos-roboto` nhưng vẫn cài nhánh mặc định, đồng thời hiểu phần sau `@` là
  TÊN SKILL nên báo `No matching skills found`. Đó là lý do pin bằng default-branch, không
  bằng cú pháp.
- **`-l` không thay được cài thật.** `add … -l` báo `Found 1 skill` xanh trong khi lệnh cài
  thật vẫn hỏng. Kiểm đường cài phải cài thật rồi vẽ một sơ đồ, xem `data-preset` ra gì.

Upstream ra bản mới thì rebase nhánh, đừng cài đè bằng `tt-a1i/archify`.

Gọi bằng ngôn ngữ tự nhiên trong chat — **không có prefix lệnh**:

```text
Use Archify to draw: Browser -> API -> Redis cache -> PostgreSQL fallback.
```

Nói rõ LOẠI thì khỏi phải đoán — `architecture` · `workflow` · `sequence` · `dataflow` ·
`lifecycle`. Dán Mermaid có sẵn vào cũng được, nó vẽ lại cho đẹp.

Ba điều phải biết trước khi gọi, đã kiểm chứng bằng cách chạy thật:

1. Package đặt `"private": true` — **không có trên npm**. `npx archify` không chạy. Mọi lệnh
   shell đều là `node ~/.agents/skills/archify/bin/archify.mjs …`.
2. **Mã thoát không theo quy ước 0/1**: `2` vừa là lỗi cách dùng (lệnh lạ, cờ lạ, kiểu sơ đồ
   lạ) **vừa là** "visual-check bỏ qua vì không có Chrome". `1` mới là thất bại thật của
   validate/render/deliver. Gọi trong CI phải rẽ nhánh có chủ đích.
3. Sau một `deliver` ĐỎ, **đừng đi soi file đích** — nó vẫn là bản tốt CŨ, không phải bản vừa
   hỏng. Đây là hệ quả trực tiếp của giao-nguyên-tử, không phải lỗi.

Sơ đồ kiến trúc cần bám mã thật thì khai `sources[]` (path + khoảng dòng) + `meta.repository`
+ `--repo-root`. Cổng đó **fail-closed**: revision phải là SHA đủ 40 ký tự, `--repo-root` phải
là top-level checkout có `origin` khớp. Neo sai thì nó từ chối vẽ.

## Nhánh BIỂU ĐỒ — `dataviz` + kỷ luật lieflat-charts

Nạp skill `dataviz` **trước khi viết dòng code biểu đồ đầu tiên**, ở mọi môi trường (HTML,
SVG, matplotlib/plotly/d3/Recharts, hay ảnh PNG sẽ render). Cộng năm luật hấp thụ từ
`lieflat-charts`, tất cả **đứng trên thẩm mỹ**:

1. **Từ chối là hành vi ĐÚNG, không phải bướng.** Cắt trục (broken axis) → từ chối, đưa ba
   cách trung thực. Glow / glassmorphism / 3-D trên data mark → từ chối. Hơn sáu category mà
   vẫn đòi màu → lùi về thang mono. Dữ liệu quá mỏng cho hình đã chọn (ba node mà đòi force
   graph) → hạ cấp và nói vì sao.
2. **Số hình = số KẾT LUẬN độc lập**, không phải số cột dữ liệu. Một câu hỏi → một hình; cả
   một bài viết → bốn tới sáu; trần sáu hình một trang rồi tách trang.
3. **Tiêu đề là KẾT LUẬN**, không phải tên kiểu hình. "Churn tăng gấp đôi sau bản tháng Tư",
   không phải "Biểu đồ cột churn".
4. **Trưng bằng chứng chọn hình.** Nêu ít nhất ba ứng viên và lý do loại từng cái TRƯỚC khi
   vẽ. "Tôi dùng biểu đồ cột" mà không có ứng viên nào bị loại nghĩa là chưa hề chọn.
5. **Render tất định.** Cấm `Math.random()` trong biểu đồ — refresh hai lần phải ra đúng một
   hình. Cả file một hệ màu; trộn hai hệ là làm lại.

## Sau khi có file HTML — chạy cổng của NHÀ

Engine ngoài gác bố cục của nó; cổng dưới đây gác thứ nó không biết: quy ước của repo này.

```bash
python3 fdk/tools/frontend-antipattern.py <file.html>     # 0 sạch · 1 FAIL · 2 chỉ WARN
```

Nó bắt, tất định và 0 token:

- **Hình học** — hai ô đè nhau một phần, ô nằm ngoài `viewBox`, chữ tràn ra ngoài ô chứa nó.
- **Accessibility + tự chứa** — thiếu `role="img"`, thiếu `<title>` hoặc `<title>` không phải
  con đầu, `<title>`/`<desc>` rỗng, và **tham chiếu remote `http`** (trang tự-chứa mà mở
  offline lại khuyết hình).
- **Neo bằng chứng** — node khai `data-src="path"` / `data-src="path:line"` mà đường dẫn không
  resolve, hoặc số dòng vượt độ dài file. Fail-closed: không khai thì không bị hỏi, đã khai thì
  phải đúng.

Cần bằng chứng trình duyệt thật (không phải chỉ phân tích tĩnh):

```bash
python3 fdk/tools/visual-receipt.py <file.html>           # 0 pass · 1 fail · 2 BỎ QUA
```

Ra bốn ảnh (1440×900 và 2048×1320, mỗi cỡ sáng + tối), một biên lai JSON, và một contact
sheet để **người** chấm. Nó kiểm trong trình duyệt thật ba thứ regex không làm được: tràn
ngang, lỗi console, và **mọi request thoát ra ngoài** — tức tính tự-chứa đo bằng hành vi chứ
không bằng chuỗi trong file.

## Rules

- **Model không vẽ.** Model điền tờ khai; code dựng hình. Thấy mình đang gõ toạ độ SVG bằng
  tay cho một hình mới là đã đi sai nhánh.
- **Không nhả hình rác.** Bản mới không qua cổng thì giữ bản tốt cũ, báo rõ chỗ sai. Generator
  của repo này đã làm đúng vậy (`_deliver` trong `build-overstack-docs.py`: render ra file tạm,
  chạy cổng trên file tạm, xanh mới `os.replace`).
- **BỎ QUA ≠ SẠCH.** Thiếu Chrome, thiếu mạng, thiếu engine → nói "bỏ qua", tuyệt đối không
  báo "đạt". Một cổng nói dối mà vẫn xanh tệ hơn không có cổng.
- **Đừng bê ràng buộc phong cách của engine ngoài về làm luật nhà.** Đo trước: archify đòi mũi
  tên thẳng ngang/dọc, nhưng sơ đồ của repo này cố ý toả nan quạt (6·4·10 đường chéo hợp lệ ở
  ba sơ đồ) — nên luật đó bị loại khi hấp thụ, còn ba luật hình học kia thì nhận.
- **Sơ đồ trong tài liệu tự sinh thì dùng generator, đừng gọi agent.** Mỗi sơ đồ vẽ qua chat
  tốn một lượt agent, mãi mãi; code sinh SVG tốn 0. Chỉ dùng nhánh chat cho hình mới hoặc hình
  dùng một lần.

## Origin

- Nhánh sơ đồ: `Rheinmir/archify` @ `macos-roboto` (KÉO NGOÀI — fork của `tt-a1i/archify`;
  engine sống ngoài, ta ghim + gọi). Xem `sources/draft/080926-archify-fork-pin.md`.
- Kỷ luật biểu đồ: `larashero3-dotcom/lieflat-charts` (HÒA TAN — chỉ lấy luật, không lấy bộ vẽ).
- Cổng hình học + giao nguyên tử: hấp thụ từ archify vào `fdk/tools/frontend-antipattern.py`
  và `fdk/tools/build-overstack-docs.py`, xem `wiki/sources/draft/040926-absorb-round.md`.
