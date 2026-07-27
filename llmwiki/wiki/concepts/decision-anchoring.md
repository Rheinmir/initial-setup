---
type: concept
title: "Decision-anchoring — neo quyết định vào symbol, liveness suy từ code-graph"
tags: [decision-anchoring, code-graph, mechanisms-yaml, source-of-truth, why]
timestamp: 2026-07-21
---

# Decision-anchoring

Decision-anchoring giải một câu hỏi cụ thể: khi code là nguồn chân lý duy nhất, làm sao từ một dòng code cụ thể tìm ngược lại được LÝ DO (WHY) nó tồn tại, và làm sao biết ngay khi code đổi mà lý do đó chưa được ai xác nhận lại. Cách giải không phải cất một bảng ánh xạ tay giữa code và tài liệu — bảng đó luôn drift, vì không ai buộc phải cập nhật nó mỗi khi code đổi. Cách giải là NEO một quyết định vào một toạ độ trong code (một symbol cụ thể, không phải một file), rồi để máy tự SUY ra quyết định đó còn sống, đã cũ, hay đã mất — bằng cách đọc trực tiếp trạng thái thật của code, không phải bằng cách hỏi ai đó có nhớ cập nhật hay không.

## Vì sao đây là tổng quát hoá, không phải ý tưởng mới

`harness/mechanisms.yaml` (ADR-001, council-025) đã làm đúng hình dạng này ở mức thô từ trước: mỗi mục có `id`, `desc` (WHY, văn xuôi người viết) và `live_probe` — một đường dẫn repo-relative phải tồn tại trên đĩa. `medic` chạy probe `narrative`: một cơ chế được khai LIVE mà `live_probe` biến mất khỏi đĩa thì bị bắt ngay với thông điệp "manifest nói dối". Cơ chế này đã bắt được drift thật trong chính phiên thiết kế decision-anchoring — thư mục `harness-local/` bị dời sai chỗ, và `live_probe` trỏ vào chỗ trống lập tức chặn `medic`.

Giới hạn của `live_probe` là nó neo ở mức file/thư mục, không phải symbol: sửa bất kỳ dòng nào bên trong một file không làm neo gãy hay báo cần xác nhận lại, dù logic bên trong đã đổi hoàn toàn. Decision-anchoring mở rộng đúng nguyên lý đó xuống mức mịn hơn — neo vào một hàm/lớp/method cụ thể — bằng cách thêm hai trường mới cạnh `live_probe` cũ: `anchor_symbol` (toạ độ symbol) và `confirmed` (ngày người xác nhận lần cuối).

## Bốn trạng thái, suy ra chứ không cất tay

Mỗi mục có `anchor_symbol` được liveness engine (`harness/scripts/decision-liveness.py`) suy ra đúng một trong bốn trạng thái:

- **LIVE** — symbol còn resolve được, và vùng dòng của nó không đổi kể từ `confirmed:`.
- **STALE** — symbol còn resolve được (tên chưa đổi), nhưng vùng dòng đã đổi kể từ lần xác nhận cuối — có thể vẫn đúng, cần người đọc lại.
- **ORPHAN** — symbol không resolve được nữa. Nguyên nhân có thể là đổi tên hoặc xoá hẳn; liveness không phân biệt được hai nguyên nhân đó (chỉ biết "không tìm thấy nữa"), nên cả hai phát ra cùng một tín hiệu.
- **UNAVAILABLE** — không kết luận được gì, vì một trong ba tầng của dependency chain bị đứt: git không có trên PATH, index code-graph thiếu/hỏng schema, hoặc project chưa reindex đủ để phản ánh trạng thái mới nhất của file. UNAVAILABLE bắt buộc phải tách biệt tuyệt đối khỏi ORPHAN — "không kiểm tra được" và "đã biến mất" là hai sự thật rất khác nhau, và trộn chúng lại sẽ khiến người xem hoảng vì những cảnh báo ORPHAN giả.

## Thăm dò trực tiếp, không qua MCP

Bản thiết kế ban đầu giả định việc resolve symbol sẽ đi qua MCP tool (`search_symbols`/`get_symbol_context`) mà Claude gọi trong phiên. Thực tế thi hành lộ ra một ràng buộc không lường trước: `decision-liveness.py` chạy như một script CLI độc lập, ngoài context của Claude, nên nó không có quyền gọi MCP tool — chỉ chính Claude-agent mới gọi được. Lời giải là đọc TRỰC TIẾP file sqlite (`.graph-agent/index.db`) mà server code-graph tự ghi ra, áp đúng nguyên tắc đã có sẵn trong `dep-health.py`: *"quảng cáo một năng lực = phải thăm dò nó, không phải kiểm sự tồn tại của nó."* Thăm dò ở đây nghĩa là kiểm DB có đủ bảng (`symbols`, `files`) chứ không chỉ kiểm file `.db` có mặt, và kiểm checksum (`sha256(file)[:16]`, đúng thuật toán server đã dùng để ghi cột `checksum`) khớp giữa nội dung trên đĩa và bản đã index — đây là cách duy nhất, không qua MCP, để biết "project đã reindex" hay chưa.

Bằng chứng thật xác nhận thiết kế UNAVAILABLE là cần thiết chứ không phải lý thuyết suông: tại thời điểm pilot symbol đầu tiên (`_debounced` trong `stop.py`) được neo, `.graph-agent/index.db` của chính repo này chưa index file đó — chạy `why _debounced` trả về đúng UNAVAILABLE kèm lý do "chưa được index", trong khi vẫn in được nội dung WHY đầy đủ. Đây chính là điểm quan trọng nhất của thiết kế: đọc WHY và biết trạng thái liveness là hai câu hỏi độc lập — một cơ chế UNAVAILABLE không ngăn người dùng đọc được lý do quyết định.

## Trỏ nhầm root, và vì sao reindex vẫn phải do agent chủ động

Kiểm chứng thật (2 phiên Claude Code độc lập, spawn trong một workspace UAT ngày 2026-07-21) lộ ra một góc mù: `ROOT = Path(__file__).parents[2]` khiến script tự suy root theo VỊ TRÍ BẢN ĐANG CHẠY — mà travel-policy tầng `global_shared` chủ động nhân bản `decision-liveness.py` ra global harness home (`~/.claude/harness`) để mọi phiên gọi được không cần đứng trong repo. Bản nhân ra không đồng bộ toàn vẹn: có `mechanisms.yaml` nhưng thiếu chính file mà nó tham chiếu chéo tầng (`llmwiki/.claude/hooks/stop.py`) và thiếu `.graph-agent/index.db` — kết quả là UNAVAILABLE dù không có gì hỏng về logic. 5-Why đầy đủ: `travel-policy` phân loại theo TỪNG FILE độc lập, không mô hình hoá quan hệ tham chiếu chéo tầng (một mục ở `harness/` trỏ symbol ở `llmwiki/`) — góc mù này chưa từng lộ trước decision-anchoring vì mọi `live_probe` cũ đều trỏ file NẰM TRONG CHÍNH tầng `global_shared`.

Vá đã áp: `resolve_symbol()` tự phân biệt UNAVAILABLE "chưa reindex" (tạm, tự khỏi) khỏi "file/DB không tồn tại ở ROOT này — có thể đang chạy nhầm bản global_shared" (cấu trúc, cần đổi root).

**Vì sao không để máy TỰ reindex khi thấy UNAVAILABLE, mà bắt agent chủ động gọi?** Hai ràng buộc cộng lại, không phải thiếu sót UX: (a) `reindex_repo()` là MCP tool call — chỉ phiên agent đang sống mới gọi được, một script CLI chạy qua subprocess không có kết nối MCP, không thể gọi dù muốn; (b) cố ý không để máy "tự sửa" lặng lẽ — đúng ranh giới Non-goals đã chốt (*"máy chỉ flag, người xác nhận hoặc sửa"*), vì code-graph server có tiền sử hỏng-mà-không-ai-biết nhiều tuần (`dep-health.py`), nên KHÔNG được giả định watcher đã lo xong rồi báo LIVE — phải thăm dò thật. Đo được thật ngày viết trang này: agent test lần đầu dừng ở UNAVAILABLE và báo đúng "không kiểm tra được" thay vì tự ý phán LIVE — hành vi ĐÚNG, dù tốn thêm một lượt hỏi mới ra được LIVE thật (sau khi được nhắc gọi `reindex_repo` qua code-graph MCP). Vá rẻ đã áp để giảm ma sát: cả docstring CLI lẫn trang này giờ đều nói thẳng — UNAVAILABLE vì chưa reindex thì agent nên tự gọi `reindex_repo(root)` trước khi coi đó là kết luận cuối, tránh lặp lại đúng nguyên nhân đã giết `touches` ("thứ không ai tiêu thụ thì không ai nuôi" — WHY trả lời sai-cảm-giác ở lượt đầu khiến người dùng ngừng tin sớm).

## CRUD trên chính mục quyết định, không chỉ trên code nó neo vào

Một lỗ hổng dễ bỏ sót là chỉ nghĩ tới CRUD phía code (đổi/xoá symbol) mà quên CRUD phía quyết định (đổi/xoá chính mục trong `mechanisms.yaml`). Xoá vật lý một mục có `anchor_symbol` là lỗ hổng nghiêm trọng nhất nếu bỏ qua: liveness chỉ kiểm được những gì CÒN neo để kiểm — mục biến mất thì code vẫn chạy bình thường, không ORPHAN, không STALE, và WHY biến mất không một dấu vết, đúng chính căn bệnh "docs rot" mà cơ chế này sinh ra để chống, chỉ khác là lần này xảy ra ngay trong chính cơ chế được thiết kế để ngăn nó. Kỷ luật bắt buộc là append-only: xoá hợp lệ luôn đi qua `status: retired`, không bao giờ xoá dòng. `harness/scripts/decision-guard.py` so `git diff` của `mechanisms.yaml` THEO TỪNG `id` (không so nguyên file) để bắt xoá lén mà không báo oan khi hai người sửa hai mục khác nhau trong cùng một merge.

## Bằng chứng thật (FR-010 trust boundary — đối chiếu bằng máy, không tự khai)

Bốn con số dưới đây KHÔNG phải Claude tự khai lúc viết trang này — chúng được `harness/scripts/decision-anchoring-crosscheck.py` đo lại bằng máy mỗi lần chạy `check`, so với đúng các con số ghi ở đây; sai một số là script tự FAIL, không dựa vào lời tự thuật.

<!-- FACT: total_mechanisms=25 -->
<!-- FACT: anchored_symbol_count=2 -->
<!-- FACT: liveness_self_test_exit=0 -->
<!-- FACT: guard_self_test_exit=0 -->

Hai mục đầu tiên có `anchor_symbol` (`stop-debounce` neo vào `_debounced` trong `llmwiki/.claude/hooks/stop.py`, `code-graph-probe-boundary` neo vào `probe_code_graph` trong `harness/scripts/dep-health.py`) là pilot symbol-level đầu tiên của toàn bộ cơ chế — 23 mục còn lại trong `mechanisms.yaml` tiếp tục dùng `live_probe` mức-file cũ, không bị đổi hành vi.

## Notes
- [[adapt-modes]] — ba dạng biên (HÒA TAN/KÉO NGOÀI/NHÚNG-SỞ-HỮU) quyết định neo trực tiếp hay neo qua adapter cho code KÉO NGOÀI.
- `harness/mechanisms.yaml` — ADR-001, tiền lệ đã chạy sống, nguồn gốc `live_probe`.
- `harness/scripts/decision-liveness.py` — engine suy 4 trạng thái, CLI `check`/`why`.
- `harness/scripts/decision-guard.py` — khoá lỗ hổng xoá-vật-lý.
- `harness/scripts/decision-anchoring-crosscheck.py` — trust boundary cho chính trang này.

## Origin
- **Source:** `llmwiki/wiki/sources/draft/210721-decision-anchoring.md` (SPEC, task `T-260721-03`), `llmwiki/wiki/sources/draft/210721-decision-anchoring-PLAN.md` (PLAN thi hành T1-T9).
- **Commit:** _(verify-before-commit điền)_
- **Date:** 2026-07-21
