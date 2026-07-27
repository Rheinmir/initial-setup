---
type: concept
title: "Provenance-log — sổ sự kiện artifact-level git-native, đa writer, merge=union"
tags: [provenance-log, event-log, kafka-pattern, git-native, cap-theorem, decision-anchoring]
timestamp: 2026-07-24
---

# Provenance-log

Provenance-log trả lời một câu hỏi hẹp và cụ thể: "sự kiện nào sinh ra artifact nào, do ai (writer_id), lúc nào (UTC), tại git commit nào" — cho những sự kiện có Ý NGHĨA ở mức artifact (một quyết định được xác nhận, một file code/docs đổi thật), không phải mọi tool-call. Đây không phải một hệ event-log tổng quát mới — nó là bản git-native, rẻ, của pattern Kafka (ordered append log, đa producer, hash-chain tamper-evident), dựng từ đúng những mảnh đã chạy sống sẵn trong repo thay vì xây từ đầu.

## Vì sao cần một sổ thứ ba, không tái dùng cái đã có

Repo này đã có hai cơ chế ghi-lại-chuyện-đã-xảy-ra trước khi provenance-log ra đời: `harness/metrics/events.jsonl` (hash-chain, tự động qua hook, nhưng gitignored — không đi theo git, không merge qua nhánh/máy khác) và `harness/metrics/scratch-log.jsonl` (git-tracked, nhưng không hash-chain và ghi bằng agent gọi tay, không tự động toàn diện). Mỗi cái giải đúng một nửa bài toán. Provenance-log hợp cả hai điểm mạnh — git-tracked VÀ hash-chain VÀ tự động — nhưng phạm vi hẹp hơn nhiều: chỉ sự kiện artifact-level, không phải mọi thao tác. Bản đồ đầy đủ của cả năm cơ chế log trong repo (kể cả `memory.jsonl` và quan hệ nội dung `touches`) nằm ở `[[log-model]]` — nguyên tắc cốt lõi rút ra từ đó: mỗi log giữ đúng phạm vi hẹp của mình, KHÔNG cố hợp nhất hay phối hợp chặt với log khác, hệ càng độc lập càng bền.

## CAP framing — chọn Availability + Partition tolerance, bỏ Consistency liên tục

Thay vì cố giữ mọi writer (nhiều session, nhiều vendor agent, nhiều máy) đồng bộ liên tục — một bài toán tốn kém và không cần thiết ở quy mô này — provenance-log để mỗi "lãnh địa" (session/vendor/máy) tự ghi log ĐỘC LẬP, không cần hỏi ai để tiếp tục làm việc (đúng cách git branch vốn hoạt động: offline-first). Hợp nhất chỉ xảy ra ở thời điểm merge, và merge dùng đúng cơ chế git đã có sẵn — driver built-in `merge=union` (`.gitattributes: harness/metrics/provenance-log.jsonl merge=union`), xác nhận thật bằng test: hai nhánh tự thêm sự kiện độc lập, merge xong đủ cả hai bên, không cần resolve conflict tay, không cần viết consensus hay CRDT riêng.

Hash-chain (`prev`/`h`, tái dùng nguyên thuật toán `code-logger.py::_chain_hash`) tính RIÊNG theo từng `writer_id` — không phải một chuỗi toàn cục — vì nhiều writer ghi song song không có quan hệ trước-sau tự nhiên với nhau; ép chung một chuỗi sẽ tạo tranh chấp giả.

## Ranh giới cố ý với `correlate()` — không làm lại việc `touches` đã giải

Bản thiết kế đầu tiên định cho `correlate()` (hàm tương quan code-change ↔ docs-change) tự suy quan hệ NỘI DUNG — "file này liên quan file kia về ngữ nghĩa". Phản biện giữa phiên chỉ ra đây là làm lại yếu hơn một việc đã giải xong: `harness/scripts/wiki-graph.py::touches_targets` đã suy quan hệ wiki→code từ NỘI DUNG (parse path trong backtick, xác nhận tồn tại trên đĩa), tất định, chạy sống (21→283 cạnh khi chuyển từ ghi tay sang suy diễn). `correlate()` được thu hẹp lại đúng phạm vi của nó: CHỈ trả lời "hai sự kiện có khả năng cùng một phiên/mạch công việc theo THỜI GIAN không" — dựa trên `writer_id`/`task_id` giống nhau và độ gần `ts_utc`. Khi tín hiệu rõ, trả `related: True/False`; khi mơ hồ, trả `related: None` kèm lý do "cần agent phán đoán" — bên GỌI (một agent) tự dùng tool-use/structured-output built-in của Claude (schema `{is_related, confidence, reasoning}`) để phán đoán tiếp, `correlate()` bản thân là hàm thuần, không tự gọi LLM.

## Adapter DUY NHẤT — chừa sẵn chỗ đổi sang broker thật

Mọi nơi trong repo đọc/ghi provenance-log đều PHẢI đi qua ba hàm trong `harness/scripts/provenance-log.py`: `append_event()`, `read_events()`, `correlate()`. Không có call site nào chạm thẳng định dạng file JSONL. Đây là điểm neo có chủ ý — nếu sau này quy mô đủ lớn để cần một broker thật (Kafka/NATS/Redis Streams), việc migrate chỉ cần viết lại nội dung MỘT file này, không sửa mọi nơi gọi nó. Bản hiện tại KHÔNG dựng broker (yêu cầu vượt quá quy mô thật của repo — hàng trăm sự kiện, không phải hàng triệu/giây, và một broker cần một tiến trình server sống, phá vỡ tính local-first của toàn framework) — chỉ định nghĩa interface, đúng nguyên tắc "chừa slot, không xây sẵn hai backend".

## Bài học `/fable5` — bug thật từ một cái tên biến đoán sai

Bản đầu của `_writer_id()` đọc biến môi trường `CLAUDE_SESSION_ID` để phân biệt session — biến này KHÔNG TỒN TẠI trong hook context thật của Claude Code; tên biến thật là `CLAUDE_CODE_SESSION_ID` (xác nhận bằng `env` thật, có UUID phiên thật). Vì self-test luôn override `writer_id` bằng tay, lỗi này không bị bắt cho tới khi verify thủ công qua `/fable5` (Move 2 GROUND — kiểm bằng công cụ, không tin trí nhớ): mọi sự kiện ghi qua hook thật đều mang `writer_id` rơi về giá trị mặc định `unknown-session`, vô hiệu hoá đúng phần lời hứa "phân biệt đa writer". Đã vá, và thêm một case self-test mới phủ đúng nhánh đọc-biến-môi-trường-mặc-định — bài học: test phủ đường override tay không chứng minh gì về đường mặc định thật, hai đường phải test riêng.

## Bằng chứng thật (đo lúc viết trang này, không phải ước lượng)

Tại thời điểm promote trang này, `harness/metrics/provenance-log.jsonl` có 98 sự kiện thật: 53 `code.change`, 44 `docs.change`, 1 `decision.confirm` (pilot `stop-debounce` của `[[decision-anchoring]]`) — toàn bộ sinh ra từ Stop hook tự bắn thật qua nhiều lượt làm việc trong phiên xây dựng cơ chế này, không phải dữ liệu giả lập.

## `/lint` đã nối — không còn là hạ tầng đứng một mình

Bước 8f của `/lint` tra `provenance-log.jsonl` như một nguồn "vì sao đổi" THỨ HAI cạnh `events.jsonl`/`scratch-log.jsonl` ở bước 0b — khác biệt quan trọng: git-tracked, đi theo được khi clone sang máy khác, điều hai nguồn kia không làm được (`events.jsonl` gitignored-local, `scratch-log.jsonl` không tự động toàn diện). Đây là bước bắt buộc phải làm SAU khi write-side đã chạy thật — trước đó, `read_events()`/`correlate()` chỉ được gọi trong self-test, một khoảng trống bị chính `/fable5` chỉ ra khi hỏi "tiếp tục chưa" và verify bằng grep thật thay vì tin lời tự thuật.

## Notes
- [[log-model]] — bản đồ 5 cơ chế log độc lập, ranh giới không phối hợp chặt.
- [[decision-anchoring]] — tích hợp trực tiếp qua `decision-liveness.py confirm`, mỗi lần bump `confirmed:` phát 1 event `decision.confirm`.
- [[graph-model]] — nguyên tắc "suy đừng cất" áp cho việc SUY `git_sha`/`ts_utc` từ git thay vì tự khai tay.
- `harness/scripts/provenance-log.py` — adapter, `--self-test`.
- `.gitattributes` — dòng `merge=union` cho `harness/metrics/provenance-log.jsonl`.

## Origin
- **Source:** `llmwiki/wiki/sources/draft/220722-artifact-provenance-eventlog.md` (SPEC, `T-260722-01`), `llmwiki/wiki/sources/draft/220722-artifact-provenance-eventlog-PLAN.md` (PLAN thi hành T1-T5).
- **Commit:** _(verify-before-commit điền)_
- **Date:** 2026-07-24
