---
name: teach-me
description: >-
  Giải thích MỘT thứ (một file, hàm, tính năng, cơ chế, hay hệ thống) theo cấu trúc cố định BẢY BƯỚC —
  Tên gọi → Nguồn gốc → Lý do tồn tại → Cơ chế hoạt động (+ sơ đồ hệ thống & code) → Trade-off → Giới hạn
  → Vị trí trong toàn bộ hệ thống. Điểm phân biệt: CHỨNG bước "Cơ chế hoạt động" bằng RUNTIME thật — chạy
  code với đầu vào cụ thể, thêm instrument/breakpoint (pdb/debugpy · node --inspect · print/log), quan sát
  state THẬT — thay vì đọc-rồi-đoán, rồi dọn sạch instrument. Gọi khi user nói "teach me", "giải thích",
  "dạy tôi", "cái này chạy thế nào", "sơ đồ hoá", "/teach-me". KHÁC /onboard-codebase và /join-project (cả dự án
  → wiki): teach-me phạm vi MỘT thứ, sâu, có sơ đồ, chứng bằng chạy thật, không ghi wiki.
---

# Skill: teach-me

## When to use
- User muốn hiểu sâu MỘT thứ cụ thể: một file, một hàm, một tính năng, một hệ thống con — "cái này chạy thế nào", "giải thích cho tôi".
- KHÔNG dùng cho: hiểu cả một codebase lạ (đó là `/onboard-codebase` → wiki, hoặc `/join-project` → orient nhanh read-only). teach-me hẹp và sâu, không ghi wiki.

## Bạn ĐƯỢC DÙNG công cụ để CHỨNG, không chỉ đọc
Đây là điểm phân biệt. Câu "nó chạy thế nào" phải được **chứng bằng runtime thật**, không suy đoán từ đọc tĩnh. Công cụ trong môi trường Claude Code:
- **Python:** `python3 -m pdb <file>`, hoặc `import pdb; pdb.set_trace()` / `breakpoint()` tạm, hoặc `debugpy`. Rẻ hơn: chèn `print(...)`/`logging` ở điểm quan tâm rồi chạy.
- **Node/JS:** `node --inspect`, `console.trace()`, `debugger;` tạm, hoặc `console.log` ở điểm quan tâm.
- **Bất kỳ:** built-in `/run` (chạy app thật) và `/verify` (drive flow, quan sát hành vi). Chạy với **đầu vào cụ thể**, quan sát **state thật ở dòng cụ thể**.

"Hàm này chắc trả về X" là phỏng đoán. "Tôi chạy với đầu vào Y, đặt breakpoint ở dòng Z, quan sát state là W" là **dữ kiện**. Luôn ưu tiên dữ kiện.

## Steps
1. **Xác định phạm vi** — user chỉ đích danh thứ cần giải thích. Không rõ → hỏi một câu ("giải thích cái gì?") kèm gợi ý từ context. Đọc code trong phạm vi đó.
2. **DRIVE runtime** (nếu chạy được) — chạy với một đầu vào cụ thể, thêm instrument/breakpoint tạm, quan sát state thật. → Xong khi có ít nhất một quan sát runtime cụ thể (đầu vào → state ở dòng nào). Không chạy được → ghi "giải thích tĩnh" (mục Rules).
3. **Sinh bảy phần** (mục dưới), ĐÚNG THỨ TỰ. → Xong khi cả bảy phần có mặt, không phần nào bị bỏ trống hoặc gộp tắt vào phần khác.
4. **DỌN SẠCH instrument** — gỡ mọi `print`/`breakpoint`/`debugger` tạm đã chèn; `git diff` xác nhận code người dùng sạch như trước. → Xong khi diff không còn instrument tạm.

## Bảy phần (output cố định — ĐÚNG THỨ TỰ, không phần nào bị bỏ)

Khung "hiểu sâu một vấn đề" — mọi thứ đem ra giải thích (file, hàm, tính năng, cơ chế, khái niệm, hệ thống con) đều đi qua đủ bảy bước theo mạch một câu chuyện: nó tên gì → từ đâu ra → vì sao phải có → nó chạy ra sao → đánh đổi gì để có nó → nó KHÔNG làm được gì → nó đứng ở đâu trong bức tranh lớn.

```
Tên gọi
    ↓
Nguồn gốc
    ↓
Lý do tồn tại
    ↓
Cơ chế hoạt động
    ↓
Trade-off
    ↓
Giới hạn
    ↓
Vị trí trong toàn bộ hệ thống
```

### 1. Tên gọi
Tên chính xác (đúng danh xưng dùng trong code/docs), tên/thuật ngữ đồng nghĩa hay gặp, và nếu tên gây hiểu lầm (đặt sai bản chất) thì nói rõ luôn ở đây.

### 2. Nguồn gốc
Nó xuất hiện từ đâu — commit/PR/quyết định nào đưa nó vào, mượn ý tưởng từ đâu (thư viện/paper/pattern có sẵn hay tự nghĩ ra), ai/tình huống nào tạo ra nhu cầu này lần đầu. Có bằng chứng thật (git log, Origin của file, ADR) thì trích, không suy đoán.

### 3. Lý do tồn tại
Nó giải bài toán gì; **không có nó thì sao** — điều gì khó hơn/vỡ/phải làm tay. Đây là phần "vấn đề giải quyết" cũ, giữ nguyên tinh thần: phải trả lời được câu "bỏ cái này đi, ai đau đầu tiên".

### 4. Cơ chế hoạt động (+ sơ đồ hệ thống & sơ đồ code)
Nó CHẠY thế nào, ở hai cấp:
- **Cấp HỆ THỐNG** — thành phần lớn, ai gọi ai, dữ liệu đi đâu, ranh giới process/service/OS. Sơ đồ: hộp + mũi tên luồng.
- **Cấp CODE** — đường thực thi cụ thể: hàm nào gọi hàm nào, state đổi ở đâu, nhánh nào chạy với đầu vào đã thử. Sơ đồ: call flow / sequence.

Đây là bước **BẮT BUỘC chứng bằng runtime thật** (xem mục "Bạn ĐƯỢC DÙNG công cụ để CHỨNG" dưới) — neo vào quan sát cụ thể (dòng Z, state W), không mô tả chung chung như tài liệu.

### 5. Trade-off
Để có được cái này, đã đánh đổi gì — chọn nhánh này thì mất nhánh khác ra sao (hiệu năng đổi lấy đơn giản, linh hoạt đổi lấy an toàn kiểu, tốc độ phát triển đổi lấy kiểm soát chặt…). Nếu biết có phương án khác từng bị cân nhắc/bỏ qua, nói rõ vì sao bỏ.

### 6. Giới hạn
Nó KHÔNG làm được gì, hoặc làm tệ ở đâu — trần quy mô, ca biên nó không phủ, điều kiện nó gãy. Khác Trade-off: Trade-off là "đánh đổi có chủ đích lúc thiết kế", Giới hạn là "biên nó dừng lại, dù muốn hay không".

### 7. Vị trí trong toàn bộ hệ thống (+ sơ đồ tóm tắt luồng)
Nó nối vào đâu trong bức tranh lớn hơn — ai gọi nó (upstream), nó gọi/ảnh hưởng gì (downstream), nó đứng lớp nào (hạ tầng/nghiệp vụ/giao diện…). Chốt bằng MỘT sơ đồ tóm tắt luồng đầu-cuối: input → các chặng → output — đọc một lần là nắm được toàn cảnh và thấy đúng chỗ đứng của nó.

## Sơ đồ — hai đường
- **Mặc định: mermaid inline** — khối ```mermaid``` (flowchart cho cấu trúc, sequenceDiagram cho luồng theo thời gian). Nhanh, đọc-được-dạng-text, render ở surface hỗ trợ. Đủ cho phần lớn "teach me nhanh".
- **Opt-in: HTML explainer** — user muốn GIỮ / chia sẻ / cần hình đẹp thật → render một trang theo `/docs-site-macos` (glass, toggle sáng/tối, in full-path, thang chữ compact 13″) với sơ đồ SVG. Đứng trên nền `[[design-foundation]]`, KHÔNG đẻ theme mới. Hỏi user trước khi ra file, đừng ép.

## Rules
- **Đủ bảy phần, đúng thứ tự, không gộp tắt.** Thiếu một phần (kể cả khi có vẻ "hiển nhiên" hay "không áp dụng") thì phải nói rõ vì sao thiếu, không được lặng lẽ bỏ qua — user cần thấy đủ khung để tự kiểm mình đã hiểu sâu tới đâu.
- **Chứng bằng runtime, không đoán:** phần "Cơ chế hoạt động" ưu tiên DRIVE code thật. Chỉ khi không chạy được (thiếu môi trường, cần prod) mới giải thích tĩnh — và **nói rõ** "đây là giải thích tĩnh, chưa chứng bằng chạy". Nếu một khẳng định phụ thuộc runtime chưa quan sát → ghi nợ `[[150726-unknown-ledger]]`, đừng khẳng định bừa.
- **Instrument tạm → DỌN SẠCH:** mọi `print`/`breakpoint`/`debugger`/`console.log` chèn để quan sát phải gỡ hết; `git diff` xác nhận trước khi kết thúc. Không để rác trong code người dùng (surgical, CLAUDE.md).
- **Phạm vi MỘT thứ:** teach-me không phân tích cả dự án (đó là `/onboard-codebase`/`/join-project`) và không ghi wiki.
- **Không đẻ debugger mới** — dùng công cụ có sẵn (pdb/debugpy · node --inspect · print/log · /run · /verify).
- **Trade-off và Giới hạn không được lẫn vào nhau** — Trade-off là đánh đổi CÓ CHỦ ĐÍCH lúc thiết kế (chọn A thì bỏ B); Giới hạn là biên nó KHÔNG VƯỢT QUA ĐƯỢC dù có muốn, thường lộ ra sau khi dùng thật (case biên, quy mô, điều kiện gãy).

## Origin
- Distill từ yêu cầu user 2026-07-16 (teach-me: 2 cấp + bộ ba + tóm tắt, mỗi phần sơ đồ; skill biết dùng breakpoint/debugger). Grounded-runtime mượn triết lý built-in `/verify`.
- **Cập nhật 2026-08-01 (feedback Rhein qua `/fdk`):** đổi khung "bốn phần" (2 cấp + bộ ba + tóm tắt) sang khung **bảy bước cố định** — Tên gọi → Nguồn gốc → Lý do tồn tại → Cơ chế hoạt động → Trade-off → Giới hạn → Vị trí trong hệ thống. Lý do: "học cái gì cũng phải có cấu trúc này để hiểu sâu" — bảy bước phủ được hai góc trước đây thiếu (Trade-off, Giới hạn) mà bốn phần cũ không có chỗ đứng riêng. Nội dung runtime-driven + hai sơ đồ (hệ thống/code) giữ nguyên, dồn vào bước 4; sơ đồ tóm tắt luồng dồn vào bước 7.
- Absorb qua `/propose` → `160726-teach-me-skill`, task `T-260716-01`.
- **Commit:** _(verify-before-commit điền)_
