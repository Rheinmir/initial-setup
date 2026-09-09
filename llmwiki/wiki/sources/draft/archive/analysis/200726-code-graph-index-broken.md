---
type: issue
kind: foundation
title: "code-graph MCP hỏng — MỘT database thiếu schema giết toàn bộ truy vấn (fan-out không cô lập lỗi)"
status: resolved
assignee: maintainer
resolved: 2026-07-20
dispatch: human
entry: /fdk
priority: P1
tags: [issue, code-graph, mcp, orientation, foundation]
timestamp: 2026-07-20
id: 200726-code-graph-index-broken
source_session: "T-260719-02 — đo A/B code-graph (task T2 của proposal 190726-graph-lessons-grapuco)"
---

# Issue: code-graph MCP hỏng — một database rác giết cả tool, mà orientation vẫn dặn mọi phiên dùng nó TRƯỚC

## Triệu chứng

Mọi truy vấn đọc của code-graph MCP đều lỗi schema:

```
mcp__code-graph__get_stats       → Error: no such table: files
mcp__code-graph__search_symbols  → Error: no such table: symbols
mcp__code-graph__list_projects   → trả 17 mục, TẤT CẢ đều tên "index.db"
```

Đã tự tay tái hiện trong phiên chính (không chỉ nghe agent báo), và **5 subagent độc lập** đều gặp đúng ba lỗi này.

## Nguyên nhân gốc — ĐÃ SỬA (đính chính chẩn đoán ban đầu)

> **Chẩn đoán đầu tiên của tôi SAI.** Tôi viết *"đường GHI và đường ĐỌC trỏ hai database khác nhau"*. Không phải. Đó là suy luận từ triệu chứng, chưa đọc code. Sau khi đọc `db.py` + `server.py` và tái hiện, nguyên nhân thật là **hai bug độc lập**, cả hai đã sửa ở commit `2727ede` của repo `workspace/graph`.

**Bug 1 — fan-out không cô lập lỗi (đây mới là thứ giết `search_symbols`).**
`_each_db()` và `get_stats()` duyệt MỌI database trong registry, còn `get_all_db_paths()` chỉ kiểm `.exists()`. Một repo đã đăng ký nhưng index chưa chạy xong để lại `index.db` **có file mà chưa có bảng** — truy vấn chạm nó là ném `no such table: symbols` và **giết cả lệnh**, kể cả khi mọi database còn lại đều lành.

Tái hiện dứt khoát: đúng **một** database hỏng (`payroll-frontend-develop`) làm chết toàn bộ, trong khi **16** database khác query tốt. *Một cái là đủ* — đó là lý do triệu chứng trông như "ghi một nơi đọc một nẻo": `reindex_repo` báo thành công thật (2660 file, 21972 symbol) vì nó chỉ ghi vào database của repo mình, còn `search_symbols` fan-out thì chết ở database rác của repo khác.

**Đính chính số liệu:** lần đo đầu tôi báo "11 database hỏng". Sai — lúc đó ổ ngoài `/Volumes/giatbhSSD(APFS)` chưa sẵn sàng nên đọc ra 0 byte. Đo lại: 19 repo trong registry, **1 database thiếu schema**, 2 mục trỏ file không tồn tại (vô hại, đã bị `.exists()` lọc), 16 lành.

**Bug 2 — `list_projects` trả tên file thay vì tên repo.**
Nó dùng `os.path.basename(p).rsplit("-", 1)[0]` — tàn dư của layout cũ khi database đặt tên `<repo>-<hash>.db` chung một thư mục. Sau khi chuyển sang `<repo>/.graph-agent/index.db` thì `basename` luôn là `index.db`, nên **mọi** repo đều hiện thành `index.db` (đo: 17 mục giống hệt).

**Cách sửa:** đặt guard `is_usable_db()` ngay trong `get_all_db_paths()` — hàm dùng chung — thay vì bọc `try/except` ở từng caller. Một guard, mọi caller hưởng, database rác không bao giờ lọt xuống tầng dưới. `list_projects` lấy tên thư mục ông của file database.

**Kết quả sau sửa:** `get_all_db_paths` 17 → 16 (loại đúng cái rác), `list_projects` trả tên repo thật, `search_symbols("flag_stale")` trả 8 kết quả thay vì ném lỗi, tổng 53.208 symbol query được.

## ĐÃ XÁC MINH TỪ PHÍA CLIENT (sau restart, 2026-07-20)

| Tool | Trước | Sau |
|---|---|---|
| `list_projects` | 17× `"index.db"` | 16 tên repo thật (`setup`, `bonbon-ai-backend`, `payroll-*`…) |
| `get_stats` | `no such table: files` | 16 project · 5.963 file · **53.208 symbol** · 550.651 edge |
| `search_symbols("flag_stale")` | `no such table: symbols` | `harness/scripts/wiki-sync.py:138` — đúng |

## Đo lại A/B — câu trả lời THẬT cho câu hỏi gốc

Chạy lại đúng 5 nhiệm vụ × 2 nhánh trên tool đã lành (`harness/metrics/code-graph-ab.json`):

| | code-graph | grep/Read | |
|---|---|---|---|
| Lần 1 (tool HỎNG) | 37 | 14 | 2.64× đắt — *đo chi phí của lỗi* |
| **Lần 2 (tool LÀNH)** | **24** | **16** | **1.50× đắt** |
| — tra hàm/lớp/method | 11 | 11 | **HOÀ** |
| — tra hằng số | 13 | 5 | **THUA 2.6×** |

Độ chính xác hoà 5/5 ở cả hai lần.

**Nguyên nhân khoản thua:** code-graph **chỉ index function/class/method**. `search_symbols("CONTENT_DIRS")` trả rỗng (agent A5b xác nhận trực tiếp). Nhưng orientation lại bảo thử nó TRƯỚC cho mọi thứ — nên mỗi lần tìm hằng số là một lần trả phí hai lần: thử code-graph, hụt, rồi mới grep.

**Đã sửa:** dòng orientation trong `llmwiki/.claude/hooks/session_start.py` khai rõ phạm vi — code-graph cho hàm/lớp/method và nhất là `get_callers`; hằng số·config·chuỗi thì grep thẳng.

**Trả lời thread Grapuco:** ở repo cỡ này, với ca **định-vị-hàm** thì ba người nói *"model đã đủ giỏi đọc repo"* là **đúng** — code-graph hoà, không hơn. Giá trị còn lại của nó nằm ở `get_callers` / quan hệ gọi (550.651 cạnh) — thứ grep không làm được, và **chưa** nằm trong bộ đo này.

## Vì sao P1 chứ không phải "tool phụ hỏng thì thôi"

Hook orientation in ở **mỗi phiên** dòng đại ý: *"QUERY trước khi đọc/grep rộng — dùng `mcp__code-graph__*` để ĐỊNH VỊ code nhanh, đừng grep mù."*

Nên đây không phải một tool hỏng nằm im. Đây là một tool hỏng mà framework **chủ động lùa mọi phiên vào**. Agent nghe lời, gọi code-graph, ăn lỗi, rồi mới quay về grep — trả phí cho cả hai đường.

## Bằng chứng định lượng (đo trong phiên này)

5 nhiệm vụ định-vị-code, mỗi nhiệm vụ chạy 2 nhánh (`harness/metrics/code-graph-ab.json`):

| Nhiệm vụ | Nhánh code-graph | Nhánh chỉ grep/Read |
|---|---|---|
| `flag_stale` | 5 | 2 |
| `HARD_CAP` | 5 | 3 |
| `detect_wiki_dir` | 13 | 3 |
| `cmd_roster` | 6 | 3 |
| `CONTENT_DIRS` | 8 | 3 |
| **Tổng** | **37** | **14** |

Độ chính xác **hoà 5/5 — hai nhánh ra cùng đáp án**. Khác biệt duy nhất là chi phí: nhánh được khuyên dùng đắt **2.64×**.

Đọc cho đúng: con số này **KHÔNG** nói code-graph vô dụng. Nó nói *chi phí của một tool đang hỏng mà ta bắt mọi phiên thử trước*. Giá trị thật của code-graph vẫn **chưa đo được** — phải sửa server rồi đo lại.

## Việc phải làm

- [x] Sửa server — commit `2727ede` (`workspace/graph`): guard `is_usable_db()` tại `get_all_db_paths()` + `list_projects` lấy tên repo.
- [ ] **Khởi động lại MCP server** rồi kiểm lại `list_projects` / `search_symbols` từ phía client.
- [ ] Cân nhắc để `code_graph_keeper.py` tự thăm dò một truy vấn rẻ rồi mới quảng cáo code-graph ở orientation — hàng rào chống tái phát, không còn gấp sau khi bug đã sửa nhưng vẫn đáng làm (lần này framework lùa mọi phiên vào một tool hỏng suốt nhiều tuần mà không ai hay).
- [ ] Sau khi sửa: chạy lại A/B (5 task × 2 nhánh) để cuối cùng cũng trả lời được câu hỏi gốc — code-graph có đáng bật không.

## Tiêu chí xong

`search_symbols` trả kết quả thật ngay sau `reindex_repo`, `list_projects` trả tên project thật, và bảng A/B chạy lại cho ra **giá trị thật** của code-graph thay vì chi phí của lỗi.

## Giới hạn của bằng chứng

Số tool-call là **agent tự khai**, không phải log hệ thống: `harness/metrics/events.jsonl` chỉ ghi tool GHI (`Edit`/`Write`, 1455 + 306 bản ghi), **không ghi** `Read`/`Grep`/MCP. Muốn đo đường tìm-kiếm một cách chống-gian-lận thì phải thêm telemetry phía đọc — đó là việc riêng, chưa làm.

## Bối cảnh

- Sinh từ task **T2** của [[190726-graph-lessons-grapuco]] (proposal đọc thread cộng đồng Grapuco qua lens Grower/Prototyper/Maintainer).
- Chặn luôn task **T5** của cùng proposal (nháp cross-repo impact FE/BE) — nháp đó dựa trên `list_projects` để nối hai project, nên nền hỏng thì nháp không chạy được. T5 chốt **no-go**, lý do là nền chứ không phải ý tưởng.
- Handoff này ghi qua đúng cơ chế vừa dựng ở task **T6** (ranh giới persona không còn là ngõ cụt): Grower chạm giới hạn nghề — sửa server MCP là việc hardening, không phải việc đo — nên chuyển cho **Maintainer**.

## Origin
- **Source:** phiên đo A/B task T2, proposal `wiki/sources/draft/190726-graph-lessons-grapuco.md`
- **Bằng chứng:** `harness/metrics/code-graph-ab.json`
- **Task:** `T-260719-02`
