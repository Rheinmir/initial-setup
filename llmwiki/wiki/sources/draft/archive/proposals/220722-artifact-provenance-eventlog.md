---
type: draft
title: "Artifact-provenance event log — pattern Kafka git-native cho code/docs/decision"
status: implemented
tags: [event-log, kafka-pattern, provenance, git-native, decision-anchoring, cap-theorem]
timestamp: 2026-07-22
task: T-260722-01
---

# Artifact-provenance event log — pattern Kafka git-native cho code/docs/decision

**Status:** implemented (T1-T5 committed 2026-07-24; T6 hoãn, chờ U-05)

Yêu cầu gốc, một câu: cần một sổ sự kiện có thứ tự, timestamp UTC, gắn được git account/commit — biết "sự kiện nào sinh ra artifact nào" — và **đa writer thật** (nhiều session, nhiều vendor agent, nhiều nhánh git), merge được qua branch, tương quan được thay đổi CODE với thay đổi DOCS theo độ gần thời gian (fallback bằng phán đoán agent khi mơ hồ), và chừa sẵn chỗ để sau này chuyển sang dạng broker/server nếu cần.

**Sequence diagram:** [220722-artifact-provenance-eventlog-seq.html](../../../html/220722-artifact-provenance-eventlog-seq.html)

## Context

**Đánh giá ban đầu của tôi (Kafka mới = thừa) đã SAI ở 2 điểm, do user chỉ ra và tôi tự kiểm chứng lại:** Tôi từng nói git + `harness/metrics/events.jsonl` đã cho đủ 90% thứ cần. Kiểm tra thật lộ ra 2 lỗ: (1) `events.jsonl` **bị gitignore** (`.gitignore:27`) — không đi theo git, không merge qua nhánh/máy khác dù đã hash-chain (`prev`/`h`) và đã share được 25 session TRÊN CÙNG MỘT MÁY; (2) chỉ `actor: {agent, system}` ghi vào nó qua hook `hooklib.py::code_log()` của riêng Claude Code — vendor agent khác (Codex, Cursor...) không được wiring vào cùng file. User còn chỉ ra assumption "single-writer" của tôi cũng sai — nhiều session/nhiều vendor agent đã cùng tạo log độc lập rồi, không phải một luồng ghi duy nhất.

**Tiền lệ đã chạy sống — hash-chain đã có, chỉ chưa git-track.** `harness/scripts/code-logger.py::record()` (dòng 52-91) đã cài đúng thuật toán hash-chain: `h = sha256(prev_h + "\n" + canon_json(rec))`, dùng `fcntl.flock` chống race đa-phiên (sinh ra sau một race có thật 2026-07-17), có `audit_verify()`/`audit_rechain()` tự phát hiện và tự nối lại chuỗi đứt. Đây là **thuật toán đúng, chỉ sai storage tier** (gitignored thay vì git-tracked).

**Một tiền lệ KHÁC đã giải đúng nửa còn lại — `scratch-log.jsonl`.** Cùng cơ chế `secondary-memory` (`mechanisms.yaml`), nhưng `harness/scripts/scratch-log.py` tự khai trong docstring: *"Khác events.jsonl (gitignored local): scratch-log.jsonl được TRACK trong git → history bất biến = lưới an toàn 'không mất'."* Nó **git-tracked** (không nằm trong 10 dòng bị ignore của `.gitignore`), nhưng KHÔNG có hash-chain, KHÔNG phân loại theo topic, và ghi bằng agent gọi tay (`note`) — curated, không phải hook tự động toàn diện.

⇒ Hai hệ thống hiện có, mỗi cái giải đúng MỘT NỬA bài toán: `events.jsonl` = hash-chain + tự động, không git-track. `scratch-log.jsonl` = git-track, không hash-chain + không tự động toàn diện. Không cái nào giải "đa writer" hay "merge qua branch" hay "tương quan code↔docs".

**Nguyên tắc "suy đừng cất" ([[graph-model]]) áp dụng ở đây.** `touches` từng chết vì ghi tay một lần rồi đóng băng (21→283 cạnh khi chuyển sang suy diễn từ engine). Event log mới PHẢI ưu tiên field suy-được-từ-git (sha, author, UTC date, diff) hơn field phải tự khai tay — tránh lặp lại đúng lỗi đó ở một hệ mới.

**Tích hợp bắt buộc với decision-anchoring (`[[decision-anchoring]]`, `T-260721-03`, vừa build+commit thật cùng tuần).** `decision-liveness.py` hiện tự chạy `git log`/`git diff` MỖI LẦN gọi để tính STALE — không giữ lịch sử "ai xác nhận, khi nào, đổi gì kể từ lần trước". `mechanisms.yaml` chỉ giữ `confirmed:` cuối cùng, không giữ các lần confirm trước. Event log mới là chỗ tự nhiên để ghi transition này — đúng cách `code-logger.py::task_new/task_set` đã ghi transition cho task lifecycle vào `events.jsonl`.

**CAP framing (do user đề xuất, chốt luận điểm chính của Approach A):** chọn **AP** (Availability + Partition tolerance), bỏ Consistency liên tục — mỗi "lãnh địa" (session/vendor/máy) tự ghi log ĐỘC LẬP không cần đồng bộ realtime (đúng cách git branch vốn hoạt động: offline-first, không cần hỏi ai để tiếp tục làm việc); hợp nhất ("công quốc → vương quốc") chỉ xảy ra ở thời điểm merge, dùng đúng cơ chế git đã có sẵn (không cần tự viết consensus/CRDT).

## Global constraints

- `llmwiki/CLAUDE.md` 5-Why: chạy trước khi sửa/xây — đã chạy 2 vòng trong phiên (trỏ-nhầm-root, agent-tự-reindex), luận điểm CAP/AP ở đây tiếp nối đúng mạch đó.
- `llmwiki/CLAUDE.md` prose rule: `## Context` và concept sẽ-promote viết văn xuôi đầy đủ, không caveman.
- Nguyên tắc "suy đừng cất" ([[graph-model]]): field nào git tính được (sha, author, UTC date) thì SUY, không cất tay song song.
- `adapt-modes` ([[adapt-modes]]): cơ chế mới là **HÒA TAN** — tự viết, không có upstream để pin (không phải KÉO NGOÀI/NHÚNG-SỞ-HỮU).
- Không được PHÁ VỠ `events.jsonl` hay `scratch-log.jsonl` hiện có — đây là log THỨ BA, mục đích riêng (artifact-provenance ordered by topic), không thay thế 2 cái kia.
- Append-only, không xoá vật lý — cùng kỷ luật đã áp cho `mechanisms.yaml` trong decision-anchoring (`status: retired`, không xoá dòng).
- Fail-open tuyệt đối ở writer (theo đúng pattern `code-logger.py::record()`: `except Exception: pass`) — ghi log không bao giờ được chặn công việc chính.
- `harness/travel-policy.yaml`: engine mới thuộc tầng nào phải khai đúng — khả năng cao là `travel_in_repo` (file log git-tracked sống TRONG repo dự án, không phải global_shared, vì mỗi repo có lịch sử riêng).

## Non-goals

- **Không** dựng broker thật (Kafka/NATS/Redis Streams) trong bản này — nhưng **PHẢI** chừa sẵn adapter boundary để migrate sau nếu cần (yêu cầu bổ sung của user), xem FR-007.
- **Không** giải consensus/CRDT tổng quát cho mọi loại dữ liệu — chỉ giải đúng bài toán "append-only log, entry độc lập theo dòng, hiếm khi 2 bên sửa CÙNG một dòng" (đúng tính chất của event log, không phải state có thể conflict thật).
- **Không** đảm bảo tương quan code↔docs chính xác 100% — heuristic (độ gần thời gian + cùng session/task) kèm fallback phán đoán agent cho ca mơ hồ, chấp nhận sai số (nguyên văn user: "chấp nhận nợ thôi").
- **Không** thay thế `events.jsonl` (audit trail chi tiết mọi tool-call, local, KHÔNG cần travel) hay `scratch-log.jsonl` (ghi chú ngữ cảnh curated) — event log mới chỉ bắt sự kiện **có ý nghĩa artifact-level** (commit, decision-confirm, docs-promote, task-milestone), không phải mọi keystroke.
- **Không** suy lại quan hệ NỘI DUNG "trang wiki này nói về code nào" — `touches_targets` (`wiki-graph.py`) đã giải xong, content-based, tất định. `correlate()` (FR-005) chỉ trả lời "hai sự kiện có cùng phiên/mạch công việc không" (thời gian), một câu hỏi HOÀN TOÀN KHÁC. Xem `[[log-model]]` — bài học phiên 2026-07-22: cố ép các log phối hợp/hợp nhất làm hệ MỎNG MANH hơn, không bền hơn; mỗi log giữ đúng phạm vi hẹp của nó thì độc lập, dễ tin hơn.
- **Không** gộp `provenance-log.jsonl` vào `scratch-log.jsonl` có sẵn, dù cả hai đều git-tracked (đã cân nhắc kỹ, không phải bỏ qua vì lười so sánh). Lý do KHÔNG phải "khác chủ đề" — lý do là **hai HỢP ĐỒNG TIN CẬY khác nhau**: `scratch-log.py` tự khai *"why OPTIONAL — không ép agent"* (best-effort, agent CHỌN ghi khi thấy đáng); `provenance-log` cần ngược lại — FR-006 hứa *"lịch sử ĐẦY ĐỦ các lần confirm"*, nên một lần bump `confirmed:` không được ghi PHẢI là BUG (hook gãy), không được phép là "agent thấy không đáng ghi". Gộp chung một file, phân biệt chỉ bằng field `kind`, sẽ tái tạo đúng loại nhầm lẫn đã tốn công sửa trong chính phiên này (UNAVAILABLE-vì-hạ-tầng-gãy lẫn với UNAVAILABLE-vì-chưa-reindex ở `decision-liveness.py`; mirror-drift ở `/lint` bước 8e) — "thiếu 1 dòng" sẽ mơ hồ giữa cố ý bỏ qua và hỏng thật.
- **Không** xây UI riêng — tiêu thụ qua CLI + query, khớp cách `decision-liveness.py`/`code-logger.py` đã làm.

## Approaches

**Phương án A — Git-native partitioned append-log, hash-chain theo writer, merge bằng `merge=union` (chọn).** Một file JSONL git-tracked (`harness/metrics/provenance-log.jsonl`, KHÔNG gitignore), mỗi entry mang `writer_id` (session+vendor+machine), `topic` (code.change/docs.change/decision.confirm/task.milestone), `ts_utc` (ISO8601 UTC tường minh, khác `events.jsonl` hiện dùng giờ local), `git_sha` (HEAD tại thời điểm ghi — SUY được, không tự khai), `prev`/`h` (hash-chain **theo từng writer_id riêng**, không phải một chuỗi toàn cục — vì nhiều writer ghi song song không có "trước-sau" tự nhiên giữa các writer khác nhau, chỉ có trước-sau TRONG một writer). Merge qua branch dùng driver **`merge=union`** có sẵn trong git (`.gitattributes`: `harness/metrics/provenance-log.jsonl merge=union`) — hợp dòng cả 2 bên, không đè, đúng bản chất "công quốc hợp nhất" (union, không phải 3-way text merge kén chọn). Ưu điểm: tái dùng nguyên thuật toán hash-chain đã chứng minh chạy (`code-logger.py`), không cần server, travel tự nhiên qua git clone/pull/merge. Nhược điểm: file lớn dần theo thời gian — chấp nhận được vì chỉ ghi sự kiện Ý NGHĨA (không phải mọi tool-call), và có thể nén/rotate định kỳ giống `ledger-snapshot.py` đã làm cho các ledger khác.

**Phương án B — Broker thật (Kafka/NATS/Redis Streams tự host).** Giải đúng bài toán multi-producer/multi-consumer/replay ở QUY MÔ mà repo này chưa chạm tới (hàng nghìn sự kiện qua nhiều tháng, không phải hàng triệu/giây). Bác: cần một tiến trình server sống (phá vỡ local-first/offline-first mà toàn bộ framework này đang giữ — xem bài học `dep-health.py` về server orphan/hỏng-mà-không-ai-biết), cần vận hành hạ tầng (uptime, partition strategy, consumer group) không ai yêu cầu ở quy mô này, và không tự travel qua git clone (phải đồng bộ riêng). Giữ lại như **hướng migrate sau** qua adapter (FR-007), không phải bản build ngay.

**Phương án C — `git notes` gắn trực tiếp vào commit.** Zero tiền lệ trong repo (grep toàn repo: 0 kết quả) — sẽ là cơ chế hoàn toàn mới phải học lại từ đầu. Bác: `git notes` không fetch mặc định khi clone (cần cấu hình `refs/notes/*` riêng — kém portable hơn một file thường), mỗi note khoá vào ĐÚNG MỘT commit (không tự nhiên cho nhiều sự kiện xảy ra GIỮA hai commit, ví dụ decision-confirm không đi kèm commit code nào), và merge notes cũng cần cấu hình riêng (`notes.rewriteMode`) — không đơn giản hơn Phương án A mà lại kém trực quan hơn (đọc notes cần lệnh riêng, không `cat`/`grep` thẳng được như JSONL).

## Requirements (FR)

**FR-001**: Hệ thống PHẢI ghi mỗi sự kiện có ý nghĩa artifact-level (commit thật, decision-anchoring confirm/re-confirm, docs promote, task lifecycle milestone) thành một dòng JSONL trong `harness/metrics/provenance-log.jsonl`, GIT-TRACKED (không nằm trong `.gitignore`).

**FR-002**: Mỗi entry PHẢI mang `writer_id` (định danh session+vendor+machine, không giả định single-writer), `topic`, `ts_utc` (ISO8601 UTC tường minh — SUY được từ `datetime.now(timezone.utc)`, không phải giờ local như `events.jsonl` hiện tại), `git_sha` (HEAD tại thời điểm ghi, SUY từ `git rev-parse HEAD`, không tự khai tay).

**FR-003**: Hash-chain (`prev`/`h`, tái dùng nguyên thuật toán `code-logger.py::_chain_hash`) PHẢI tính RIÊNG theo từng `writer_id` — không có một chuỗi toàn cục duy nhất, vì nhiều writer ghi song song không có quan hệ trước-sau tự nhiên với nhau.

**FR-004**: File PHẢI merge được qua git branch bằng driver `merge=union` (khai trong `.gitattributes`) — hai nhánh cùng thêm dòng vào file này, merge xong PHẢI còn đủ dòng của cả hai bên, không mất dòng nào.

**FR-005**: Hệ thống PHẢI cung cấp một truy vấn tương quan HẸP — CHỈ trả lời "hai sự kiện này có khả năng CÙNG một phiên/mạch công việc không" (dựa trên `writer_id`/`task_id` giống nhau + cách nhau dưới ngưỡng thời gian, xem Assumptions), KHÔNG cố suy quan hệ NỘI DUNG (không phân tích path/text để đoán "file A liên quan file B về mặt ngữ nghĩa" — câu hỏi đó `harness/scripts/wiki-graph.py::touches_targets` đã giải xong bằng content-based, tất định, và KHÔNG được làm lại yếu hơn ở đây, xem `[[log-model]]`). Trong ngưỡng → đề xuất liên quan; ngoài ngưỡng hoặc nhiều ứng viên cùng lúc → PHẢI trả về "cần agent phán đoán" thay vì tự động khẳng định. **Nhánh "cần agent phán đoán" PHẢI trả lời qua tool-use/structured-output built-in của Claude** (schema tối thiểu `{is_related: bool, confidence: float, reasoning: string}`), KHÔNG PHẢI free-text rồi tự parse — đúng nguyên tắc "ép output có hình dạng, không ép sáng tạo" của các engine constrained-decoding (outlines/llguidance/xgrammar), áp dụng qua cơ chế provider hỗ trợ vì Claude API không lộ logits để dùng trực tiếp các engine đó (kết luận từ phiên `/fable5` 2026-07-22 — xem Origin).

**FR-006**: Decision-anchoring's `confirmed:` bump (trong `mechanisms.yaml`) PHẢI phát ra một entry `topic: decision.confirm` vào log mới — tạo lịch sử các lần confirm mà hiện `mechanisms.yaml` chỉ giữ giá trị cuối cùng.

**FR-007**: Toàn bộ ghi/đọc PHẢI đi qua một module adapter DUY NHẤT (`harness/scripts/provenance-log.py`: `append_event()`/`read_events()`/`correlate()`) — không có call site nào gọi thẳng vào format file JSONL. Đây là điểm neo để MIGRATE sang broker thật (Phương án B) sau này chỉ bằng cách viết lại nội dung file này, không sửa mọi nơi gọi nó (yêu cầu bổ sung của user — chừa slot broker migration).

**FR-008**: Writer PHẢI fail-open tuyệt đối (đúng pattern `code-logger.py::record()`: `except Exception: pass`) — ghi log không bao giờ được chặn hay làm chậm công việc chính.

## Success criteria (SC)

**SC-001**: Hai branch git khác nhau, mỗi branch tự thêm sự kiện độc lập (mô phỏng 2 session/2 vendor agent), sau khi `git merge` — người đọc thấy ĐỦ sự kiện của cả hai bên trong file kết quả, không mất dòng nào, không cần resolve conflict tay.

**SC-002**: Người dùng đọc `provenance-log.jsonl` của MỘT commit bất kỳ, tìm được: ai (writer_id) tạo, lúc nào (UTC), sinh ra artifact nào — không cần hỏi lại hay đoán.

**SC-003**: Với một cặp sự kiện code-change + docs-change xảy ra gần nhau thật (trong phiên decision-anchoring vừa build — vd sửa `decision-liveness.py` rồi cập nhật `concepts/decision-anchoring.md` cùng phiên), truy vấn `correlate()` đề xuất đúng cặp liên quan; với hai sự kiện KHÔNG liên quan cách xa thời gian, `correlate()` không đề xuất sai.

**SC-004**: `mechanisms.yaml`'s `stop-debounce` entry sau khi bump `confirmed:` một lần thật — `provenance-log.jsonl` có đúng 1 entry `topic: decision.confirm` mới, đọc lại thấy rõ lịch sử xác nhận (không chỉ giá trị cuối).

**SC-005**: Tắt hoàn toàn hệ thống ghi log này (giả lập lỗi ghi file) — công việc chính (git commit, decision-liveness check) vẫn chạy bình thường, không bị chặn (fail-open thật, không phải lời hứa).

## Assumptions

- Ngưỡng thời gian tương quan code↔docs mặc định **10 phút cùng session** — **(default, find-out-later → cần đo trên dữ liệu phiên thật, U-04)**: hợp lý theo cảm quan (một lượt sửa-rồi-cập-nhật-docs thường trong vài phút), chưa đo bằng số liệu thật.
- `writer_id` định danh bằng `<vendor>::<session_id>::<hostname>` — **(default)**: đủ phân biệt session/vendor/máy như user yêu cầu, không cần đăng ký tập trung.
- File đặt tại `harness/metrics/provenance-log.jsonl` (cùng thư mục các ledger khác, khác tên để không đụng `events.jsonl`) — **(default)**: theo đúng convention thư mục đã có.
- Rotate/nén file khi lớn — **(default, find-out-later → U-05)**: chưa quyết ngưỡng cụ thể (số dòng hay dung lượng), để `ledger-snapshot.py` xử lý tương tự các ledger khác khi cần, chưa build riêng trong v0.1.
- Adapter migrate-sang-broker (FR-007) chỉ định nghĩa INTERFACE (3 hàm), KHÔNG build sẵn driver Kafka thật — **(default)**: đúng scope "chừa slot", không phải "xây sẵn 2 backend".

## Plan

Cắt theo MoSCoW, học từ bài học chính decision-anchoring vừa trải qua (SPEC phình 4 vòng trước khi ship — lần này cắt ngay từ đầu).

**v0.1 — MUST, lõi chạy được:**

- [x] **T1 — Module adapter `harness/scripts/provenance-log.py`: `append_event()` (hash-chain theo writer_id, UTC, git_sha SUY từ `git rev-parse HEAD`), `read_events()`.** Verify: SC-002, SC-005 (fail-open thật khi ghi lỗi).
- [x] **T2 — `.gitattributes` khai `merge=union` cho `provenance-log.jsonl`; test merge 2 branch thật.** Verify: SC-001.
- [x] **T3 — Wiring decision-anchoring: bump `confirmed:` trong `mechanisms.yaml` PHẢI gọi `append_event(topic="decision.confirm", ...)`.** Verify: SC-004.

**v0.2 — SHOULD, giá trị tương quan code↔docs:**

- [x] **T4 — `correlate()` trong adapter: đề xuất cặp code.change/docs.change theo độ gần thời gian + cùng writer_id/task_id; trả "cần agent phán đoán" khi mơ hồ, qua tool-use schema `{is_related, confidence, reasoning}` (FR-005), không phải free-text.** Verify: SC-003.
- [x] **T5 — Wiring hook ghi `topic: code.change`/`docs.change` cho các file thay đổi thật trong một phiên (tái dùng logic phát hiện `.py`/`.md` đã có ở `stop.py::_CODE_RE`).** Verify: SC-002 mở rộng — đọc lại thấy phân loại đúng code vs docs.

**v0.3 — COULD, hoãn thật sự:**

- [ ] **T6 — Rotate/nén file khi lớn (tái dùng pattern `ledger-snapshot.py`).** Verify: (default, U-05) — chưa có SC cụ thể, đóng khi có ngưỡng thật.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| T1 | Claude | Hash-chain là thuật toán bảo mật-tính-toàn-vẹn — sai một chi tiết (thứ tự hash, thời điểm lấy prev) làm hỏng cả chuỗi, cần đúng ngay từ đầu | pending |
| T2 | Claude | `.gitattributes` + test merge thật là cấu hình hạ tầng git — cần hiểu đúng semantics `merge=union` trước khi khai | pending |
| T3 | Claude | Wiring vào decision-anchoring (code vừa tự tay build) — cần hiểu đúng nơi bump `confirmed:` để không phá vỡ append-only đã có | pending |
| T4 | Claude | Heuristic tương quan + fallback phán đoán cần thiết kế đúng ngưỡng/logic, không phải thao tác cơ học | pending |
| T5 | OpenCode (rẻ) | Tái dùng logic phát hiện file code/docs đã có sẵn (`_CODE_RE`), thao tác nối dây theo mẫu đã biết | pending |
| T6 | OpenCode (rẻ) | Tái dùng nguyên pattern `ledger-snapshot.py` đã chạy sống, không cần thiết kế mới | pending |

## Self-review

**Phủ yêu cầu.** Tất cả yêu cầu gốc của user đã về đúng task: sổ sự kiện có thứ tự+UTC+git-account (T1/FR-002), đa writer thật (FR-003), merge qua branch (T2/FR-004/SC-001), tương quan code↔docs + fallback phán đoán agent (T4/FR-005/SC-003), chấp nhận nợ thay vì auto-update hoàn hảo (Non-goals), slot broker-migration bổ sung giữa turn (T7... — không, đã gộp vào FR-007/T1 vì adapter interface là một phần của T1, không tách task riêng vì nó không tự đứng được — không có gì để "chạy" nếu tách khỏi `append_event`/`read_events` mà nó bọc quanh).

**Quét chỗ bỏ ngỏ.** Rà toàn văn, không còn mục nào chỉ mô tả *phải làm gì* mà thiếu *làm thế nào cụ thể* — 2 giá trị chưa chắc (ngưỡng thời gian, ngưỡng rotate) đã hạ xuống `(default, find-out-later)` có ghi nợ, không giả định chắc chắn.

**Nhất quán tên-kiểu.** `provenance-log.jsonl`/`provenance-log.py` là tên duy nhất xuyên suốt (không lẫn với `ledger-snapshot`/`scratch-log`/`events.jsonl` đã có); `writer_id`/`topic`/`ts_utc`/`git_sha` là 4 field cố định dùng thống nhất từ FR-002 tới Plan; `append_event()`/`read_events()`/`correlate()` là 3 hàm adapter duy nhất, không đặt tên khác ở chỗ khác.

## Origin
- **Source:** phiên 2026-07-22 — tiếp nối trực tiếp từ decision-anchoring (T-260721-03, cùng phiên trước): 5-Why "trỏ nhầm root" → 5-Why "vì sao agent phải tự reindex" → UAT thật CRUD-code/đa-luồng → câu hỏi "có event log tự chẩn đoán không, đem sang máy khác thì sao" → đánh giá Kafka-pattern (ban đầu tôi nói thiếu cần thiết, user chỉ ra sai 2 điểm: events.jsonl gitignored + multi-vendor chưa wiring) → CAP/AP framing của user → yêu cầu chừa slot broker-migration.
- **Concept nền:** `[[graph-model]]` (suy đừng cất) · `[[adapt-modes]]` (HÒA TAN) · `[[decision-anchoring]]` (T-260721-03, tích hợp bắt buộc)
- **Bằng chứng chạy thật trong phiên:** grep+đọc trực tiếp `harness/metrics/events.jsonl` (1696 dòng, 25 session, hash-chain xác nhận qua `code-logger.py::_chain_hash`), `.gitignore` (10 file bị ignore, `scratch-log.jsonl` KHÔNG bị ignore), 0 kết quả "git notes" toàn repo.
- **Vòng phản biện `/fable5` (2026-07-22):** user thách hai luận điểm bằng ẩn dụ cờ vua ("tăng trưởng vô hạn nhưng thực tế bounded, giống combinatorial explosion cờ vua") + câu hỏi "outlines có giúp được không" (kèm ảnh chụp một hội thoại khác về constrained-decoding). Kết quả phản biện: ẩn dụ cờ vua SAI cơ chế (cờ vua = pruning bằng cách vĩnh viễn không thăm phần lớn cây tìm kiếm luỹ thừa; `provenance-log.jsonl` là append-only, tăng TUYẾN TÍNH theo sự kiện ý nghĩa — không discard được, không cùng loại tăng trưởng) nhưng kết luận thực dụng của user vẫn đúng bằng lý do khác (log tuyến tính cùng bậc tăng trưởng với chính git history, chỉ thêm hằng số nhân). Điểm "log hỗn loạn thứ tự sau merge=union vẫn dùng được làm clue truy origin" của user ĐÚNG và hạ thấp mức nghiêm trọng rủi ro #2 đã nêu trước đó (timeline-skew chỉ hại use-case cần replay đúng thứ tự, không hại use-case lookup/origin-trace mà `/lint` bước 0b đã làm sống). "outlines" (constrained decoding, cần lộ logits) không áp dụng trực tiếp cho Claude API — nhưng đúng Ý TƯỞNG của nó áp được vào nhánh phán đoán của `correlate()` qua tool-use/structured-output built-in của Claude → chốt thành FR-005 sửa đổi.
- **Task:** `T-260722-01`
