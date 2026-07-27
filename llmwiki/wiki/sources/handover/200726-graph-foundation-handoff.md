---
type: draft
title: "Bàn giao: nền graph + bản đồ quan hệ — làm tiếp từ đâu"
status: proposed
tags: [handoff, graph, capabilities, travel-policy, foundation]
timestamp: 2026-07-20
---

# Bàn giao — nền graph + bản đồ quan hệ

**Đọc trước:** [[graph-model]] (kiến trúc + số đo). File này chỉ nói **làm gì tiếp**.

## Việc tiếp theo, theo thứ tự

### 0. `travel-policy.yaml` phải khớp `install-harness.sh` — CHẶN mọi việc dưới

**Bằng chứng nó sai ngay lúc này:**

```
install-harness.sh:128   cp fdk/tools/build-capabilities.py → ~/.claude/hooks/
travel-policy.yaml:71    build-capabilities.py → TẦNG 3 FRAMEWORK-ONLY ("chỉ chạy ở repo framework")
```

Installer copy xuống. Hợp đồng khai ở lại. Trong phiên 2026-07-20 tôi đọc `travel-policy` **ba lần** để trả lời "cái gì tới tay user" và cả ba lần coi nó là sự thật — nó không phải, nó là văn bản mô tả, còn thứ sinh ra hành vi là installer.

**Làm:** validator đối chiếu hai bên (đọc mọi `cp .../X` trong `install-harness.sh` ↔ mục khai trong `travel-policy.yaml`), lệch thì đỏ. Hoặc mạnh hơn: sinh `travel-policy` từ installer.

**Hệ quả nếu bỏ qua:** mọi câu trả lời "cái gì travel" trong phiên trước **chưa được kiểm chéo** — phải coi là chưa xác minh.

⏱ ~1 giờ cho validator. Nửa ngày nếu chọn hướng sinh tự động.

### 1. `wiki-graph.py` phải quét được nhiều kho (`--also`)

Engine hiện chỉ quét MỘT wiki dir. Renderer `build-wiki-graph.py` quét được cả hai (`llmwiki/wiki` + `fdk/wiki`).

**Đo được:** trong 41 wikilink báo "gãy" — **29 là oan** vì trang có thật ở `fdk/wiki`; 6 là ví dụ văn xuôi trong `log.md`; 3 là tên skill không phải trang wiki; **chỉ 3 gãy thật**. Tức **93% báo động là nhiễu**.

**Vì sao chặn:** kế hoạch merge lấy `wiki-graph.py` làm engine chuẩn. Merge trước khi có `--also` = biến 29 link lành thành 29 link gãy trên toàn hệ, và cờ drift ở bước 3 thừa hưởng nguyên khối nhiễu đó.

⏱ ~30 phút.

### 2. Bỏ lớp `imports` khỏi `build-wiki-graph.py`

2.333 cạnh `imports` vẽ lại thứ code-graph đã giữ mịn hơn (18.560 cạnh `IMPORTS`). Bỏ đi thì graph này chỉ còn giữ thứ **không ai thay được**: wiki↔wiki + wiki↔code.

⏱ ~30 phút. Rủi ro: node code rụng theo — kiểm `touches` vẫn hiện đúng sau khi bỏ.

### 3. `wiki-sync` đọc graph thay vì grep

`map_suspects()` chính là `touches` đảo chiều, cài bằng grep. **Đo trên 8 file code đổi:** grep nghi 36 trang, graph có cạnh thật 25, trùng 21 ⇒ grep **báo thừa 15** và **bỏ sót 4**. Hỏng cả hai chiều dù docstring tự nhận "thiên về recall".

**Đây là chỗ thu lãi lớn nhất**, và quan trọng hơn: nó biến `touches` thành thứ **có người tiêu thụ**. Theo root đã tìm ra, thứ không ai tiêu thụ thì không ai nuôi — `touches` từng chết đúng vì thế.

⏱ ~2 giờ, gồm đối chiếu lại cờ drift trên một đợt thật.

### 4. Merge `wiki-graph.py` + `build-wiki-graph.py`

Sau (1) và (2) thì hai bên gần trùng khít. Engine giữ model, renderer chỉ vẽ.

**Biến mất sau merge:** `fdk/tools/wiki-relations.py` — nó chỉ làm hai việc (`derives-from` từ `## Origin`, `touches` từ path backtick) và **cả hai đều suy ra được**. Mất nó là mất luôn khái niệm "dập quan hệ vào frontmatter", tức mất chính cơ chế đã khiến `touches` đóng băng ở 21 cạnh suốt 18 ngày.

⏱ nửa ngày.

### 5. `CAPABILITIES.md` sinh TỪ graph, không từ `os.listdir`

**Đo được:** 224 dòng · 4 danh sách phẳng · **đúng 2 dòng có từ chỉ quan hệ**. Nó là bản kiểm kê, không phải bản đồ — trả lời được "cái gì có", không trả lời được "cái gì liên quan cái gì", mà chỉ câu sau mới nói được **phải giải từ đâu**.

**Ba tính chất bắt buộc**, rút từ ba lần sai trong phiên trước:

1. **Suy ra, đừng cất** — quan hệ nào cất vào file sẽ đóng băng (bài học `touches` 21→283).
2. **Khai cả cái CHẾT** — kiểm kê hiện chỉ đếm cái sống, nên `graph.db` (0/0/0) và `wiki-graph-static.html` nằm đó nhiều tuần không ai thấy.
3. **Khai cả cái KHÔNG travel** — nếu bản đồ nói rõ `code-graph` không đi xuống, đã không mất nửa buổi sửa server cho thứ tồn tại trên một máy.

**Phạm vi CHỈ được khai quan hệ suy-ra-được-và-kiểm-được:** `touches` (path tồn tại trên đĩa) · `travel` (đọc installer, sau bước 0) · `dead` (0 node / 0 caller / không ai gọi). Quan hệ `supersedes` là phán đoán người — khai tay, và phải chấp nhận nó sẽ cũ.

⚠ **Cảnh báo:** bản kiểm kê hiện có "200/200 neo bằng chứng" mà **không một cái nào thực thi gì** — đã phải đổi tên trong phiên trước vì nó từng tự xưng "năng lực còn sống". Dựng bản đồ quan hệ theo cùng cách sẽ cho ra một bản đồ **tự tin và sai**, tệ hơn không có bản đồ.

⏱ 1–2 ngày. **Nên đi qua `/propose`** — nó chạm thứ mọi phiên đọc để định hướng.

## Việc dọn nhỏ, làm lúc nào cũng được

1. **3 wikilink gãy thật** — hai cái `[[X]]` placeholder trong template/analysis cũ; một cái `[[framework-multi-session-dev]]` trỏ tên memory chứ không phải trang wiki.
2. **2 concept trỏ HTML đã xoá** — `wiki-core-relations.md`, `problem-tree.md`. Sửa một dòng mỗi trang.
3. **Xoá `graph.db` ở gốc repo** — đã xác minh 0 file / 0 symbol / 0 cạnh.
4. **Xoá `llmwiki/html/wiki-graph-static.html`** — bản bake không-JS đã cũ.

⏱ ~20 phút cả bốn.

## Nợ mở, không chặn

| Việc | Trạng thái |
|---|---|
| Đo `get_callers` của code-graph | **chưa đo** — đây là phần duy nhất biện minh cho sự tồn tại của nó; tra tên đã hoà 11-11 với grep |
| Telemetry đường đọc | `events.jsonl` chỉ ghi `Edit`/`Write`; mọi số tool-call trong phiên trước là **agent tự khai** |
| 19/20 thẻ ghi-tạm chưa đóng · 24 issue mở · 15 pattern lệch | cùng một root: hệ giỏi phát hiện nợ, không có nhịp trả nợ |
| Pha 2 orchestrator | proposal đã duyệt, nền đã sạch, mở lúc nào cũng được |

## Cạm bẫy — đọc trước khi sửa code

1. **`touches_targets` KHÔNG được `strip_code`** — ngược hẳn `wikilink_targets`. Path nằm *chính trong* inline-code. Strip thì 283 cạnh về 0.
2. **SQLite WAL không mở được `mode=ro`** khi thiếu file `-shm`. Dùng `mode=ro` để "an toàn" sẽ báo DB lành là hỏng. Đã dính ở 4 chỗ.
3. **"Mới nhất" không suy ra "của tôi"** — với tiến trình, orphan nghĩa là *cha đã chết* (PPID 1). Định nghĩa sai từng làm chết MCP đang chạy.
4. **`build-overstack-docs` tự sinh graph trước khi nhúng** — đừng gỡ, nếu gỡ thì overstack stale lại mỗi phiên.
5. **Đọc tài liệu ≠ đo hành vi.** `travel-policy` sai so với installer. `orca-workflow` mô tả dispatch trong khi 78% task chưa từng dispatch. Trước khi nói "cái này đã có rồi", **đếm lượt chạy thật**.

## Origin
- **Source:** phiên `/fdk` 2026-07-20 — chuỗi từ "thread Grapuco" tới "làm sao luôn biết phải giải từ đâu"
- **Concept nền:** [[graph-model]]
- **Commit trong phiên:** `bc39047` (touches tự suy + nhúng graph) · `1995a34` (một nguồn wikilink) · `713875b` (sinh trước render) · `bb639b8` (concept graph-model)
