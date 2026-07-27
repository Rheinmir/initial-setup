---
type: concept
title: "Log-model — MỘT hệ nhiều sổ, mỗi sổ ĐỘC LẬP trả lời MỘT câu hỏi"
tags: [log-model, events-jsonl, scratch-log, mem-rank, touches, provenance-log, parallel-independent]
timestamp: 2026-07-22
---

# Log-model

Repo này có nhiều cơ chế "ghi lại chuyện đã xảy ra" — dễ tưởng chúng phải phối hợp chặt với nhau, nhưng thực ra **KHÔNG**. Mỗi cái trả lời đúng MỘT câu hỏi hẹp, ghi độc lập, không cần biết tới cơ chế khác. Trang này tồn tại để một agent BẤT KỲ (vendor nào, phiên nào) đọc MỘT LẦN là định vị được toàn bộ, không phải dò lại từng file.

## Vì sao KHÔNG nên ép chúng phối hợp chặt (bài học phiên 2026-07-22)

Lúc thiết kế `provenance-log.jsonl` (xem `[[220722-artifact-provenance-eventlog]]`), phản xạ đầu tiên là cố cho nó "biết" về mọi log khác — phân loại `code.change`/`docs.change` xuyên suốt, tự suy tương quan wiki↔code. Đó là sai hướng: `touches` (bên dưới) **đã giải xong** câu hỏi "trang wiki này nói về code nào" — content-based, tất định, chạy sống 21→283 cạnh. Bắt `provenance-log` suy lại câu đó bằng heuristic thời gian (yếu hơn nhiều) là **làm lại việc đã xong, tệ hơn bản gốc**. Nguyên tắc rút ra: **mỗi log giữ đúng phạm vi hẹp của nó, đừng cố hợp nhất thành một sơ đồ chung** — hệ mỏng manh hơn khi bị ép phối hợp chặt, bền hơn khi mỗi mảnh tự đứng một mình.

## Bảng tra nhanh — hỏi gì thì tra file nào

| Câu hỏi | Sổ nào trả lời | File | Git-track? | Ghi bằng gì |
|---|---|---|---|---|
| "Framework file X vừa đổi, tool/actor nào?" | `events.jsonl` | `harness/scripts/code-logger.py` | ✗ (local) | Tự động, mọi PostToolUse hook |
| "Vì sao tôi vừa sửa cái này?" (ghi chú ngữ cảnh) | `scratch-log.jsonl` | `harness/scripts/scratch-log.py` | ✓ | Agent gọi tay (`note`), tự nguyện |
| "Phiên trước đã làm gì, kết luận gì?" (truy hồi ngữ nghĩa) | `memory.jsonl` | `harness/scripts/mem-rank.py` | ✗ (local) | Agent gọi tay (`add`/`episode`) |
| "Trang wiki NÀY nói về code nào?" (không phải log — QUAN HỆ suy từ nội dung) | `touches` | `harness/scripts/wiki-graph.py::touches_targets` | n/a (suy lúc query) | KHÔNG ghi gì — parse backtick-path trong nội dung mỗi lần hỏi |
| "Task T-YYMMDD-NN đang trạng thái nào?" | `tasks.json` + event `task.new`/`task.set` | `harness/scripts/code-logger.py` | ✗ (state), ✓ transition (vào `events.jsonl`... nhưng `events.jsonl` cũng gitignored — xem lưu ý dưới) | `task_new()`/`task_set()` |
| "Quyết định/artifact NÀY sinh lúc nào, ai, git sha nào — travel qua máy khác được?" | `provenance-log.jsonl` (**ĐỀ XUẤT, CHƯA BUILD**) | `harness/scripts/provenance-log.py` (chưa tồn tại) | ✓ (thiết kế mới) | Tự động, hook hẹp (chỉ sự kiện Ý NGHĨA artifact-level) |

## Vì sao KHÔNG git-track hết — đây là lựa chọn có chủ ý, không phải sơ suất

`events.jsonl`/`memory.jsonl`/`tasks.json` gitignored vì chúng dày đặc, per-machine, không ai cần travel (mọi tool-call, mọi phiên) — git-track chúng sẽ làm phình repo vô ích. `scratch-log.jsonl` git-track vì nó CURATED (agent tự chọn ghi khi đáng) nên thưa hơn nhiều. `provenance-log.jsonl` (đề xuất) git-track vì phạm vi nó còn HẸP HƠN scratch-log (chỉ artifact-level, không phải context-vụn) — cùng logic, siết chặt hơn một nấc.

## Sơ đồ độc lập (ASCII — mỗi log là 1 cột, KHÔNG có mũi tên nối ngang)

```
   events.jsonl        scratch-log.jsonl      memory.jsonl         touches              provenance-log.jsonl
   (mọi tool-call)     (ngữ cảnh vụn)          (ngữ nghĩa,          (wiki→code,          (artifact origin,
   local, tự động      git-track, tay          truy hồi top-k)      content-based,       ĐỀ XUẤT — git-track,
                                                local, tay           KHÔNG lưu gì)        hẹp, tự động)
        │                    │                     │                    │                    │
        ▼                    ▼                     ▼                    ▼                    ▼
  "tool nào đụng      "vì sao tôi sửa       "phiên trước đã      "trang wiki X       "quyết định Y
   file gì lúc nào"    dòng này"             làm gì, kết luận      nhắc code path      sinh lúc nào,
                                              gì" (relevance,       nào, path đó        ai, sha nào,
                                              không phải thời       có thật không"      merge qua
                                              gian)                                    branch được"

   KHÔNG cái nào cần đọc cái khác để hoạt động đúng. Không có "log tổng" nào hợp nhất cả 5.
```

## Nếu bạn là agent mới đọc trang này lần đầu

Đừng cố tìm một API/class hợp nhất cả 5 sổ — không có, và **không nên có**. Cần trả lời câu hỏi nào thì tra đúng cột trong bảng trên. Muốn thêm một log MỚI (như `provenance-log`) — giữ nó hẹp, đặt CÂU HỎI nó trả lời vào docstring đầu file (đúng convention 4 file kia đã làm), và thêm một dòng vào bảng này — đừng thử nối nó với các log cũ.

## Notes
- [[graph-model]] — "MỘT bài toán, năm bản cài" cho code-graph/wiki-graph, cùng tinh thần "nhiều bản cài độc lập, đừng ép hợp nhất" áp cho log ở đây.
- [[220722-artifact-provenance-eventlog]] — SPEC `provenance-log.jsonl`, đã cắt bớt phần "tự suy tương quan code↔wiki" sau bài học trang này (xem Origin của SPEC đó).
- [[decision-anchoring]] — dùng `git log`/`git diff` trực tiếp cho STALE, không qua log nào ở đây — một ví dụ khác của "suy từ git, đừng cất tay".

## Origin
- **Source:** phiên 2026-07-22, câu hỏi "vẽ ra các cơ chế parallel log hoạt động độc lập" + "sao phải cố kiểm soát cái mỏng manh như vậy" — phản biện trực tiếp việc `provenance-log.jsonl`'s `correlate()` định tự suy quan hệ wiki↔code mà `touches` đã giải xong.
- **Bằng chứng đọc thật trong phiên:** docstring 3 file (`code-logger.py:1-19`, `scratch-log.py:1-16`, `mem-rank.py:1-24`), `wiki-graph.py:88-96` (`touches_targets`).
- **Date:** 2026-07-22
