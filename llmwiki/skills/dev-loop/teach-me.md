---
name: teach-me
description: >-
  Giải thích MỘT thứ (một file, hàm, tính năng, cơ chế, khái niệm, lỗi, hay hệ thống) theo cấu trúc cố định
  BẢY BƯỚC — Tên gọi → Nguồn gốc → Lý do tồn tại → Cơ chế hoạt động (+ sơ đồ hệ thống & code) → Trade-off
  → Giới hạn → Vị trí trong toàn bộ hệ thống — và CĂN THEO NGƯỜI NGHE (engineer, sếp/manager, designer, PM,
  sinh viên, bố mẹ, trẻ 5 tuổi…): cùng bảy bước, đổi độ sâu, từ vựng, phép so sánh, giọng. CHỨNG bước "Cơ chế
  hoạt động" bằng RUNTIME thật — chạy code với đầu vào cụ thể, thêm instrument/breakpoint (pdb/debugpy · node
  --inspect · print/log), quan sát state THẬT — thay vì đọc-rồi-đoán, rồi dọn sạch instrument. Gọi khi user
  nói "teach me", "giải thích", "dạy tôi", "cái này chạy thế nào", "sơ đồ hoá", "ELI5", "explain like I'm…",
  "giải thích như cho trẻ 5 tuổi", "nói dễ hiểu", "giải thích cho sếp/manager/designer/bố mẹ/vợ tôi…",
  "làm sao nói với sếp cái này", "/teach-me". KHÁC /onboard-codebase và /join-project (cả dự án → wiki):
  teach-me phạm vi MỘT thứ, sâu, có sơ đồ, chứng bằng chạy thật, không ghi wiki.
---

# Skill: teach-me

## When to use
- User muốn hiểu sâu MỘT thứ cụ thể: một file, một hàm, một tính năng, một hệ thống con, một khái niệm, một thông báo lỗi — "cái này chạy thế nào", "giải thích cho tôi".
- User muốn giải thích thứ đó cho MỘT NGƯỜI NGHE cụ thể — "ELI5", "nói với sếp thế nào", "giải thích cho designer", "cho bố mẹ tôi hiểu".
- KHÔNG dùng cho: hiểu cả một codebase lạ (đó là `/onboard-codebase` → wiki, hoặc `/join-project` → orient nhanh read-only). teach-me hẹp và sâu, không ghi wiki.

## Bạn ĐƯỢC DÙNG công cụ để CHỨNG, không chỉ đọc
Câu "nó chạy thế nào" phải được **chứng bằng runtime thật**, không suy đoán từ đọc tĩnh. Công cụ trong môi trường Claude Code:
- **Python:** `python3 -m pdb <file>`, hoặc `breakpoint()` tạm, hoặc `debugpy`. Rẻ hơn: chèn `print(...)`/`logging` ở điểm quan tâm rồi chạy.
- **Node/JS:** `node --inspect`, `console.trace()`, `debugger;` tạm, hoặc `console.log` ở điểm quan tâm.
- **Khái niệm/công cụ (git, HTTP, SQL…):** dựng ca nhỏ nhất trong thư mục tạm rồi chạy thật (vd `git init` hai nhánh sửa cùng dòng → merge → thấy conflict thật).
- **Bất kỳ:** built-in `/run` (chạy app thật) và `/verify` (drive flow, quan sát hành vi). Chạy với **đầu vào cụ thể**, quan sát **state thật ở dòng cụ thể**.

"Hàm này chắc trả về X" là phỏng đoán. "Tôi chạy với đầu vào Y, đặt breakpoint ở dòng Z, quan sát state là W" là **dữ kiện**. Luôn ưu tiên dữ kiện — với MỌI người nghe. Người nghe chỉ đổi cách TRÌNH BÀY bằng chứng, không đổi việc PHẢI có bằng chứng.

## Steps
1. **Xác định NGƯỜI NGHE** — đọc câu hỏi, xếp vào một nhóm ở bảng "Người nghe" dưới. Không nêu → mặc định **người đang hỏi = engineer** (teach-me là skill của dev); riêng từ khoá "ELI5"/"như cho trẻ 5 tuổi" không kèm ai khác → **trẻ 5 tuổi**. → Xong khi chốt được một nhóm + điều họ quan tâm.
2. **Xác định phạm vi + đọc nguồn** — user chỉ đích danh thứ cần giải thích; không rõ → hỏi một câu kèm gợi ý từ context. Đọc đúng loại nguồn: *code* → đọc code, hiểu mục đích trước cú pháp; *khái niệm* → tách thành phần cốt lõi; *thông báo lỗi* → tìm nguyên nhân gốc, không dịch lại câu chữ bề mặt; *tài liệu* → rút các ý thật sự quan trọng với người nghe.
3. **DRIVE runtime** (nếu chạy được) — chạy với một đầu vào cụ thể, thêm instrument/breakpoint tạm, quan sát state thật. Instrument chèn vào code người dùng thì làm trên bản copy hoặc gỡ ở bước 5. → Xong khi có ít nhất một quan sát runtime cụ thể (đầu vào → state ở dòng nào). Không chạy được → ghi "giải thích tĩnh" (mục Rules).
4. **Sinh output theo "Khung output"** — dòng Người nghe → TL;DR + phép so sánh → bảy phần ĐÚNG THỨ TỰ → So what; độ sâu từng phần theo bảng "Độ sâu theo người nghe". → Xong khi đủ mọi khối, không phần nào bị bỏ trống hoặc gộp tắt vào phần khác.
5. **DỌN SẠCH instrument** — gỡ mọi `print`/`breakpoint`/`debugger` tạm đã chèn; `git diff` xác nhận code người dùng sạch như trước. → Xong khi diff không còn instrument tạm.

## Người nghe — họ quan tâm gì, so sánh bằng gì, giọng nào

| Nhóm | Họ quan tâm | Phép so sánh lấy từ | Giọng |
|---|---|---|---|
| **Engineer** (mặc định) | chạy thế nào, kiến trúc, trade-off, bảo trì | thứ họ đã biết: "giống hash map nhưng…", pattern quen | chính xác, gọn, dùng đúng thuật ngữ (thiếu thuật ngữ họ thấy bị coi thường) |
| Đồng nghiệp khác mảng | ảnh hưởng tới việc của họ, cần biết gì để phối hợp | công việc chung, quy trình team | thực tế, "cái này đổi gì với bạn" |
| **Manager** | tác động, rủi ro, thời gian, chi phí, năng lực đội | kết quả kinh doanh, nhân sự, ngân sách | dẫn bằng tác động, định lượng khi được, chốt bằng quyết định cần đưa ra |
| Director | chiến lược, ROI, lợi thế cạnh tranh | bức tranh lớn, phân bổ nguồn lực | toàn cảnh, ngắn |
| Product Manager | giá trị cho người dùng, ưu tiên, phạm vi | user story, làm gì / bỏ gì | theo tính năng và người dùng |
| Designer | trải nghiệm, luồng tương tác, accessibility | màn hình, thao tác người dùng thấy | theo cái người dùng nhìn và bấm |
| Sinh viên / cao học | lý thuyết + ứng dụng; cao học: sắc thái, ca biên, hệ quả sâu | kiến thức nền môn học | học thuật; thuật ngữ kèm ngữ cảnh ngắn |
| Học sinh cấp 2–3 (≈12–17 tuổi) | nhân quả rõ, từng bước | điện thoại, mạng xã hội, game, trường lớp | hơi thân mật, không "làm màu trẻ trung" |
| Trẻ ≈10 tuổi / lớp 5 | nhân quả cơ bản | trường học, thể thao, bài tập nhóm, trò chơi điện tử | như cô giáo được yêu thích |
| **Trẻ 5 tuổi** (khi "ELI5") | một ý dễ nhớ | đồ chơi, con vật, kẹo, sân chơi, sách tranh | vui, hào hứng, câu rất ngắn |
| Bố mẹ / người lớn tuổi | hiểu mà không bị coi thường | công nghệ họ đang dùng, việc nhà | tôn trọng, rõ, kiên nhẫn |
| Vợ/chồng/bạn đời, bạn bè | câu chuyện dễ theo | việc thường ngày, trải nghiệm chung, văn hoá đại chúng | ấm, trò chuyện, có thể hài hước |

## Khung output (cố định — ĐÚNG THỨ TỰ, không khối nào bị bỏ)

```
Người nghe: <nhóm> — <điều họ quan tâm>
TL;DR: <MỘT câu "nó là gì"> + <MỘT phép so sánh với thứ người nghe đã biết>
    ↓
1. Tên gọi → 2. Nguồn gốc → 3. Lý do tồn tại → 4. Cơ chế hoạt động
→ 5. Trade-off → 6. Giới hạn → 7. Vị trí trong toàn bộ hệ thống
    ↓
So what: <điều này có nghĩa gì với CHÍNH người nghe — quyết định, hành động, hay điều cần nhớ>
```

Bảy phần là mạch một câu chuyện: nó tên gì → từ đâu ra → vì sao phải có → nó chạy ra sao → đánh đổi gì để có nó → nó KHÔNG làm được gì → nó đứng ở đâu trong bức tranh lớn. TL;DR + so sánh mở cửa (người nghe biết ngay đang nói về cái gì); So what đóng cửa (người nghe biết mang về làm gì). Mục đích luôn đi trước cơ chế — không ai quan tâm cú pháp khi chưa biết nó tồn tại để làm gì.

Tên bảy tiêu đề giữ nguyên với mọi người nghe (để user tự kiểm khung); với người nghe không kỹ thuật được thêm phụ đề đời thường, vd "5. Trade-off — được gì, mất gì".

### 1. Tên gọi
Tên chính xác (đúng danh xưng dùng trong code/docs), tên/thuật ngữ đồng nghĩa hay gặp, và nếu tên gây hiểu lầm (đặt sai bản chất) thì nói rõ luôn ở đây.

### 2. Nguồn gốc
Nó xuất hiện từ đâu — commit/PR/quyết định nào đưa nó vào, mượn ý tưởng từ đâu (thư viện/paper/pattern có sẵn hay tự nghĩ ra), tình huống nào tạo ra nhu cầu này lần đầu. Có bằng chứng thật (git log, Origin của file, ADR) thì trích, không suy đoán.

### 3. Lý do tồn tại
Nó giải bài toán gì; **không có nó thì sao** — điều gì khó hơn/vỡ/phải làm tay. Phải trả lời được câu "bỏ cái này đi, ai đau đầu tiên".

### 4. Cơ chế hoạt động (+ sơ đồ hệ thống & sơ đồ code)
Nó CHẠY thế nào, ở hai cấp:
- **Cấp HỆ THỐNG** — thành phần lớn, ai gọi ai, dữ liệu đi đâu, ranh giới process/service/OS. Sơ đồ: hộp + mũi tên luồng.
- **Cấp CODE** — đường thực thi cụ thể: hàm nào gọi hàm nào, state đổi ở đâu, nhánh nào chạy với đầu vào đã thử. Sơ đồ: call flow / sequence.

Bước **BẮT BUỘC chứng bằng runtime thật** — neo vào quan sát cụ thể (dòng Z, state W), không mô tả chung chung như tài liệu.

### 5. Trade-off
Để có được cái này, đã đánh đổi gì — chọn nhánh này thì mất nhánh khác ra sao (hiệu năng đổi lấy đơn giản, linh hoạt đổi lấy an toàn kiểu…). Biết có phương án khác từng bị cân nhắc/bỏ qua thì nói rõ vì sao bỏ.

### 6. Giới hạn
Nó KHÔNG làm được gì, hoặc làm tệ ở đâu — trần quy mô, ca biên nó không phủ, điều kiện nó gãy. Khác Trade-off: Trade-off là "đánh đổi có chủ đích lúc thiết kế", Giới hạn là "biên nó dừng lại, dù muốn hay không".

### 7. Vị trí trong toàn bộ hệ thống (+ sơ đồ tóm tắt luồng)
Nó nối vào đâu trong bức tranh lớn — ai gọi nó (upstream), nó gọi/ảnh hưởng gì (downstream), nó đứng lớp nào. Chốt bằng MỘT sơ đồ tóm tắt luồng đầu-cuối: input → các chặng → output.

## Độ sâu theo người nghe (bảy phần luôn đủ — chỉ đổi độ sâu)

| Người nghe | Bước 4 Cơ chế | Bước 5–6 nói bằng | Sơ đồ | Code / thuật ngữ | Độ dài |
|---|---|---|---|---|---|
| Engineer, đồng nghiệp, cao học | đủ hai cấp; trích dòng + state quan sát được | hiệu năng, bảo trì, ca biên | flowchart + sequence | trích code thật; thuật ngữ đúng | sâu, nhưng không lan man |
| Manager, Director, PM | chỉ cấp hệ thống; bằng chứng runtime nói thành một câu ("đã chạy thử: X → Y") | chi phí, rủi ro, thời gian, công sức đội | MỘT sơ đồ hộp-mũi tên | KHÔNG code block, KHÔNG backtick — tên file viết chữ thường | ngắn — đọc xong trong khoảng 2 phút (≈ 500 từ tiếng Anh ≈ 700 tiếng Việt phần chữ, không tính sơ đồ), chốt bằng đề xuất |
| Designer | luồng người dùng nhìn thấy | trải nghiệm, accessibility | luồng màn hình | không code; thuật ngữ UI thì được | vừa |
| Sinh viên, học sinh | từng bước nhân quả; cấp code rút gọn | "chọn A thì mất B" bằng ví dụ | một sơ đồ đơn giản | thuật ngữ nào dùng thì định nghĩa ngay lần đầu | vừa |
| Trẻ em, bố mẹ, bạn đời, bạn bè | kể như một câu chuyện có phép so sánh | "được gì, mất gì" đời thường | tuỳ chọn, rất đơn giản | KHÔNG thuật ngữ, không log thô; buộc phải dùng thì giải nghĩa liền | ngắn; trẻ em càng ngắn |

### Hiệu chỉnh ngôn ngữ
- **Người nghe đơn giản** (trẻ em, không kỹ thuật, gia đình): không jargon — bằng không; một ý mỗi câu; cụ thể hơn trừu tượng ("máy chủ giống người bồi bàn" hơn "máy chủ xử lý giao tiếp client-server"); nói "bạn/con" cho gần.
- **Người nghe kỹ thuật** (engineer, cao học): dùng đúng thuật ngữ; dồn chữ vào phần *đáng chú ý* — trade-off, ca biên, quyết định thiết kế; so với thứ họ đã biết; gọn, tôn trọng cái họ đã biết.
- **Người nghe kinh doanh** (manager, director, PM): dẫn bằng tác động và kết quả; định lượng khi được; bỏ chi tiết cài đặt trừ khi được hỏi; đóng khung thành quyết định ("nghĩa là ta nên…").

## Ví dụ — cùng một thứ, ba người nghe (chỉ mở đầu + So what)
Thứ cần giải thích: **database index**.
- **Trẻ 5 tuổi** — TL;DR: "Index là trang mục lục của cuốn sách to đùng, giúp máy tính tìm đúng trang thật nhanh, khỏi lật từng trang." · So what: "Nhờ có mục lục, trò chơi của con mở ra nhanh hơn đó!"
- **Manager** — TL;DR: "Index là cấu trúc giúp tra dữ liệu nhanh, giống mục lục sách; đổi lại mỗi lần ghi dữ liệu chậm đi một chút và tốn thêm dung lượng." · So what: "Trang báo cáo đang chậm vì thiếu index ở bảng đơn hàng; thêm index mất khoảng nửa ngày công, rủi ro thấp — đề xuất làm trong sprint này."
- **Engineer** — TL;DR: "B-tree index biến tra cứu O(n) quét cả bảng thành O(log n), giống hash map có thứ tự nhưng đổi lại mỗi INSERT/UPDATE phải cập nhật cây." · So what: "Kiểm `EXPLAIN` truy vấn chậm: thấy `Seq Scan` trên cột lọc thì cân nhắc index, nhưng đo write amplification trước khi thêm."

## Sơ đồ — hai đường
- **Mặc định: mermaid inline** — khối ```mermaid``` (flowchart cho cấu trúc, sequenceDiagram cho luồng theo thời gian). Nhanh, đọc-được-dạng-text.
- **Opt-in: HTML explainer** — user muốn GIỮ / chia sẻ / cần hình đẹp thật → render một trang theo `/docs-site-macos` (glass, toggle sáng/tối, in full-path, thang chữ compact 13″); sơ đồ gọi `/diagram`. Đứng trên nền `[[design-foundation]]`, KHÔNG đẻ theme mới. Hỏi user trước khi ra file, đừng ép.

## Rules
- **Đủ khung, đúng thứ tự, không gộp tắt** — Người nghe → TL;DR → bảy phần → So what. Thiếu một phần (kể cả khi "hiển nhiên" hay "không áp dụng") thì nói rõ vì sao thiếu, không lặng lẽ bỏ qua.
- **Người nghe đổi CÁCH NÓI, không đổi SỰ THẬT** — được lược chi tiết, được đơn giản hoá mạnh cho người không kỹ thuật (truyền được 80% ý cốt lõi còn hơn 100% chính xác mà người nghe bỏ cuộc), nhưng KHÔNG nói sai; chỗ lược mạnh ghi "(đã đơn giản hoá)". Nén bằng chứng thành một câu cho người không kỹ thuật thì câu đó không được nói to hơn điều đã quan sát (thấy một ca → nói "một ca", không nói "luôn luôn"); con số (số lần sửa, số dòng, số file) đếm lại từ git/đĩa, không ước.
- **Không bao giờ nói giọng bề trên** — giải thích cho trẻ 5 tuổi phải thấy thú vị chứ không phải bị "làm ngu đi"; giải thích cho manager phải thấy được trao quyền quyết, không bị coi là không hiểu.
- **Người nghe không kỹ thuật = không code, kể cả backtick** — không code block, không định dạng `inline code` cho tên file/thư mục (bài học eval eli5: bản có skill vẫn trượt vì backtick tên thư mục khi viết cho manager).
- **Chứng bằng runtime, không đoán:** phần "Cơ chế hoạt động" ưu tiên DRIVE code thật. Chỉ khi không chạy được (thiếu môi trường, cần prod) mới giải thích tĩnh — và **nói rõ** "đây là giải thích tĩnh, chưa chứng bằng chạy". Khẳng định phụ thuộc runtime chưa quan sát → ghi nợ `[[150726-unknown-ledger]]`, đừng khẳng định bừa.
- **Instrument tạm → DỌN SẠCH:** mọi `print`/`breakpoint`/`debugger`/`console.log` chèn để quan sát phải gỡ hết; `git diff` xác nhận trước khi kết thúc.
- **Phạm vi MỘT thứ:** teach-me không phân tích cả dự án (đó là `/onboard-codebase`/`/join-project`) và không ghi wiki.
- **Không đẻ debugger mới** — dùng công cụ có sẵn (pdb/debugpy · node --inspect · print/log · /run · /verify).
- **Trade-off và Giới hạn không được lẫn vào nhau** — Trade-off là đánh đổi CÓ CHỦ ĐÍCH lúc thiết kế; Giới hạn là biên nó KHÔNG VƯỢT QUA ĐƯỢC dù muốn, thường lộ ra khi dùng thật.

## Eval — sửa skill thì phải đo lại (nếu repo có `harness/scripts/wikieval.py`)
Học theo eli5: mỗi ca = một prompt + 4–5 khẳng định kiểm được, chạy bản skill cũ và mới trên CÙNG prompt rồi so tỉ lệ đạt.
- Goldens: `fdk/wiki/sources/evals/teach-me-*.md` — ba ca phủ ba kiểu người nghe (engineer · manager · trẻ 5 tuổi); assert tất định (thứ tự bảy phần, không code cho manager, có phép so sánh cho trẻ em…) + `rubric` cho giám khảo.
- Chạy A/B: mỗi phiên bản skill do một agent độc lập trả lời từng prompt → gom thành `harness/evals/teach-me-ab-<ddmmyy>-<old|new>.json` (map golden-id → câu trả lời) → `python3 harness/scripts/wikieval.py --outputs <file>`. Bản mới không được có tỉ lệ đạt thấp hơn bản cũ.

## Origin
- Distill từ yêu cầu user 2026-07-16 (teach-me: 2 cấp + bộ ba + tóm tắt, mỗi phần sơ đồ; skill biết dùng breakpoint/debugger). Grounded-runtime mượn triết lý built-in `/verify`.
- **Cập nhật 2026-08-01 (feedback Rhein qua `/fdk`):** đổi khung "bốn phần" sang khung **bảy bước cố định** — Tên gọi → Nguồn gốc → Lý do tồn tại → Cơ chế hoạt động → Trade-off → Giới hạn → Vị trí trong hệ thống. Nội dung runtime-driven + hai sơ đồ dồn vào bước 4; sơ đồ tóm tắt luồng dồn vào bước 7.
- **Cập nhật 2026-09-11 (HÒA TAN từ [dreambigou/eli5](https://github.com/dreambigou/eli5) @ `a766623`, MIT):** thêm bước xác định **Người nghe** (bảng 12 nhóm tuổi/học vấn/vai trò/quan hệ, gộp từ bốn bảng của eli5), khung mở-đóng **TL;DR + phép so sánh → … → So what** (từ "what → analogy → details → so what"), bảng độ sâu bảy phần theo người nghe, hiệu chỉnh ngôn ngữ ba nhóm, ví dụ cùng-một-thứ-ba-người-nghe, luật "không giọng bề trên / đơn giản hoá không nói sai / không backtick cho người không kỹ thuật", và vòng eval A/B (eli5 `run-evals.py --a/--b` → tái dùng `wikieval.py` + goldens thay vì chép runner). Khác eli5: mặc định người nghe là engineer (không phải trẻ 5 tuổi), bảy bước giữ nguyên, bằng chứng runtime vẫn bắt buộc với mọi người nghe.
  - A/B lần đầu (3 ca, mỗi bản do agent độc lập trả lời, outputs ở `harness/evals/teach-me-ab-110926-{old,new}.json`): khẳng định tất định cũ 8/13 → mới 13/13; giám khảo mù 4 tiêu chí cũ 6/12 → mới 9/12. Ca manager bản mới vẫn trượt vì dài (~718 tiếng) và một câu bằng chứng nói quá điều đã quan sát → thêm ngưỡng độ dài tính theo tiếng Việt + luật nén bằng chứng (chưa đo lại sau hai luật này).
- Absorb qua `/propose` → `160726-teach-me-skill`, task `T-260716-01`.
- **Commit:** _(verify-before-commit điền)_
