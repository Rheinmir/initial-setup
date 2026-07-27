---
type: concept
title: "Mô hình graph — MỘT bài toán, năm bản cài"
status: implemented
tags: [graph, code-graph, wiki-graph, touches, drift, architecture]
timestamp: 2026-07-20
id: graph-model
relations:
  - {rel: depends-on, to: wiki-core-relations}
  - {rel: touches, path: harness/scripts/wiki-graph.py}
  - {rel: touches, path: fdk/tools/build-wiki-graph.py}
  - {rel: touches, path: harness/scripts/wiki-sync.py}
---

# Mô hình graph — MỘT bài toán, năm bản cài

## Bài toán thật là gì

Framework này sinh ra rất nhiều artifact: concept, ADR, draft, eval, issue, plan. Câu hỏi đáng tiền chỉ có một:

> **Các artifact liên quan gì đến nhau, và liên quan gì đến code?**

Còn **code liên quan gì đến code là sản phẩm phụ** — nó lớn nhất về số lượng, dễ dựng nhất, và ít giá trị nhất, vì nó không trả lời được câu hỏi thực sự đau: *"đổi file này thì tài liệu nào vừa trở thành sai?"*

Đây là khung phải giữ khi đụng bất cứ graph nào trong repo. Trước 2026-07-20 khung này chưa được viết ra, nên năm bản cài mọc lên rời rạc và không ai thấy chúng đang giải chung một việc.

## Năm bản cài, ba lát cắt

| Lát cắt | Ai giữ | Node → Edge | Quy mô đo 2026-07-20 |
|---|---|---|---|
| **artifact ↔ artifact** | `harness/scripts/wiki-graph.py` (query, in-memory) · `fdk/tools/build-wiki-graph.py` (vẽ) | trang wiki → `[[wikilink]]` | 194 cạnh · 184 cạnh |
| **artifact ↔ code** ⭐ | `build-wiki-graph.py`, quan hệ `touches` | trang wiki → path code | **283 cạnh** |
| code ↔ code | code-graph MCP (ngoài repo) · `build-wiki-graph` vẽ lại | symbol → `CALLS`/`IMPORTS` | 272.529 cạnh · 2.333 cạnh |

Thêm hai bản vẽ không phải graph riêng — `memory-map.py` và `whiteboard-skill-map.py` chỉ `importlib` chính renderer của `build-wiki-graph.py` rồi bơm node/edge khác vào. Đó là tái dùng đúng cách.

**Lát cắt giữa là lý do tồn tại của cả nhóm.** Hai lát ngoài đều có thứ khác làm tốt hơn: quan hệ code↔code thì code-graph giữ mịn hơn nhiều (18.560 cạnh `IMPORTS` so với 2.333 cạnh vẽ lại), còn quan hệ wiki↔wiki thì bản thân file markdown đã mang sẵn. Chỉ `touches` là thứ **không có nguồn nào khác**.

## Vì sao grep không giải được — đo, không suy đoán

`harness/scripts/wiki-sync.py` có hàm `map_suspects()` trả lời đúng câu hỏi của lát cắt giữa, nhưng **đảo chiều và cài bằng grep**: với mỗi file code vừa đổi, tìm mọi trang wiki có chứa chuỗi path hoặc basename. Docstring của nó tự khai *"heuristic tất định, thiên về recall"*.

Đo trên cùng 8 file code đổi, so với `touches` đảo chiều:

| | Số |
|---|---|
| grep nghi | 36 trang |
| graph có cạnh thật | 25 trang |
| Trùng nhau | 21 |
| **grep báo THỪA** | **15** |
| **grep BỎ SÓT** | **4** |

Grep hỏng **cả hai chiều**: kêu oan 15 trang, đồng thời bỏ lọt 4 trang có quan hệ thật. Nó không đạt recall như docstring tự nhận, cũng không đạt precision. Lý do cấu trúc: grep khớp *chuỗi ký tự*, nên một path nhắc trong văn xuôi hay trong ví dụ code đều tính như nhau, còn một quan hệ khai trong frontmatter thì nó không thấy.

⇒ Cờ drift của toàn hệ hiện đang được quyết định bởi phép đoán, trong khi cạnh thật đã nằm sẵn trong graph.

## Bài học gốc: sự thật SUY RA ĐƯỢC thì phải SUY, đừng CẤT

`touches` từng chỉ có **21 cạnh trên 2.559 (0,8%)** — cầu nối quan trọng nhất mà gần như rỗng. 5-Why ra nguyên nhân:

> Vì sao cũ? → `fdk/tools/wiki-relations.py` chạy đúng một lần ngày 02/07 → **vì sao một lần?** nó là *migrator*, không phải *maintainer* → **vì sao không ai nối vào nhịp?** vì được đóng khung là "dập quan hệ vào frontmatter" → **Root: một sự thật SUY RA ĐƯỢC bị cất như sự thật ĐƯỢC KHAI.** Cất rồi thì nó đóng băng.

Đối chứng ngay trong cùng hệ: `wikilink` **không bao giờ cũ**, vì nó được suy lại mỗi lần dựng graph. Khác biệt duy nhất giữa hai quan hệ là một cái được suy, một cái được cất.

Sửa: chuyển logic suy diễn từ writer sang engine (`wiki-graph.py::touches_targets`) — path trong backtick, có `/`, và **tồn tại trên đĩa**. Kết quả **21 → 283 cạnh, 283/283 đích có thật** (không false-positive vì điều kiện bắt buộc tồn tại). Frontmatter khai tay vẫn thắng nên không nhân đôi.

Một chi tiết ngược đời đáng nhớ: `touches_targets` **không được** `strip_code`, ngược hẳn với `wikilink_targets` — vì path nằm **chính trong** inline-code. Strip thì nó về 0.

## Vì sao từng có hai bản cài cho cùng một câu hỏi

`wiki-graph.py` (query cho agent) và `build-wiki-graph.py` (vẽ cho người) trả lời cùng câu hỏi "cái gì link tới cái gì" bằng hai regex độc lập, không chia sẻ dòng code nào. Đo được **lệch thật 208 vs 164 cạnh**, và mỗi bên sai một kiểu khác nhau nên không thể chọn bừa bên nào làm chuẩn:

- `wiki-graph.py` **không** bỏ code-fence → đếm cả `[[...]]` trong ví dụ code là cạnh thật
- `build-wiki-graph.py` bỏ code-fence đúng nhưng **giữ nguyên** `[[trang#anchor]]` → sinh cạnh trỏ tới trang không tồn tại

Nay một nguồn: `wikilink_targets()` / `mdlink_targets()` trong `wiki-graph.py`, bên kia nạp qua `importlib` có fail-open. Khoá bằng `harness/tests/wikigraph-single-source-test.sh`.

## Điều dễ hiểu nhầm: code-graph KHÔNG travel

`code-graph` là MCP server riêng ở `workspace/graph`, **không xuất hiện trong `harness/travel-policy.yaml` lẫn template manifest**. Người curl-cài overstack **không hề có nó**. Nó là tool của một máy, không phải năng lực của framework — nên orientation phải gác bằng thăm dò (`harness/scripts/dep-health.py`), không được quảng cáo mù.

Đo A/B sau khi sửa server: tra hàm/lớp/method **hoà 11-11** với grep; tra hằng số **thua 13-5** (code-graph không index hằng số module-level). Phần duy nhất chưa đo là `get_callers` — đúng phần grep không làm được, và cũng đúng phần biện minh cho sự tồn tại của nó.

## Việc còn nợ, theo thứ tự

1. **Bỏ lớp `imports` khỏi `build-wiki-graph.py`** — 2.333 cạnh vẽ lại thứ code-graph giữ mịn hơn.
2. **`wiki-sync` đọc graph thay vì grep** — hết kêu oan 15, hết bỏ sót 4. Quan trọng hơn: nó biến `touches` thành thứ **có người tiêu thụ**, mà theo đúng root ở trên, thứ không ai tiêu thụ thì không ai nuôi.
3. **Merge `wiki-graph.py` + `build-wiki-graph.py`** — sau (1) thì hai bên gần trùng khít, merge thành việc gọn.

Thứ tự không ngẫu nhiên: (2) là chỗ thu lãi và cũng là chỗ khoá cho `touches` không mục lại lần nữa.

## Sau khi làm xong: còn lại MỘT hệ

Kỳ vọng đúng là chỉ còn một hệ ôm trọn các vấn đề này. Cụ thể nó trông thế nào:

**MỘT engine** — `harness/scripts/wiki-graph.py` giữ mô hình graph (artifact↔artifact + artifact↔code), travel xuống máy user, 0 token, có CLI truy vấn (`backlinks`, `neighbors`, `orphans`, `broken`, `export`).

**Nhiều view, không view nào tự dựng model:**

| View | Vai trò sau merge |
|---|---|
| `fdk/tools/build-wiki-graph.py` | renderer HTML — mất scanner riêng, mất lớp `imports` |
| `fdk/tools/memory-map.py` · `whiteboard-skill-map.py` | đã chỉ là renderer, không đổi |
| `harness/scripts/wiki-sync.py` | **đọc graph** để đánh cờ drift, thay grep |
| `/lint` · `/query` | tiêu thụ cờ drift như hiện tại |

**Biến mất hẳn:**

- `fdk/tools/wiki-relations.py` — nó chỉ làm hai việc, và **cả hai đều suy ra được**: `derives-from` từ mục `## Origin` (mọi file wiki bắt buộc có), `touches` từ path backtick. Khi cả hai đã suy tại engine thì cái writer này không còn lý do tồn tại — và cùng với nó, biến mất luôn khái niệm "dập quan hệ vào frontmatter", tức là biến mất nguồn gốc của việc quan hệ bị đóng băng.
- `graph.db` ở gốc repo — xác minh 0 file / 0 symbol / 0 cạnh, tàn dư lần thử index sớm.
- `llmwiki/html/wiki-graph-static.html` — bản bake không-JS đã cũ, bị bản JS thay thế.

**Nằm ngoài hệ, tuỳ chọn:** code-graph MCP. Nó cấp lát cắt code↔code khi có mặt, nhưng không travel và không phải năng lực framework — gác bằng `harness/scripts/dep-health.py`, thiếu thì hệ vẫn chạy đủ.

Nói gọn: **một engine · nhiều view · một dependency ngoài tuỳ chọn.** Không còn hai scanner cãi nhau, không còn writer dập quan hệ, không còn grep đoán thay cho cạnh thật.

## Origin
- **Source:** phiên `/fdk` 2026-07-20 — user hỏi "code-graph vốn là cái gì phục vụ cái gì, db chúng ta có nhiều graph lắm", rồi chốt khung: *"cả 3 cái đều để giải 1 bài toán thôi — artifact liên quan gì đến nhau và liên quan gì đến code; code liên quan gì đến nhau là sản phẩm phụ"*
- **Đo trong phiên:** kiểm kê 5 graph · `touches` 21→283 · grep-vs-graph 36/25/21/15/4 · A/B code-graph 11-11 và 13-5
- **Commit:** `bc39047` (touches tự suy + nhúng graph vào overstack), `1995a34` (một nguồn chân lý cho wikilink)
- **Liên quan:** [[wiki-core-relations]] — từ vựng quan hệ mà mô hình này thực thi
