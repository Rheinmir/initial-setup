---
type: draft
title: "code-graph → KÉO NGOÀI: pin travel-policy Tầng 1 + bootstrap cài trong install-harness.sh"
status: proposed
tags: [adapt-modes, external-pull, code-graph, travel-policy, install-harness, mcp]
timestamp: 2026-07-21
task: T-260721-01
---

# code-graph → chính thức hoá thành KÉO NGOÀI

**Status:** proposed

Yêu cầu gốc, một câu: nếu code-graph quan trọng tới mức đáng sửa bug hôm qua, thì `curl` cài framework phải tự mang nó theo — nếu không thì phải chọn dứt khoát giữa từ bỏ, viết lại, hay giữ một bản ổn định để kéo về.

**Sequence diagram:** [210726-codegraph-external-pull-seq.html](../../../html/210726-codegraph-external-pull-seq.html)

## Context

[[adapt-modes]] đã đặt tên sẵn cho đúng ba lựa chọn user đưa ra hôm nay, chỉ khác cách gọi: "từ bỏ, distill phiên bản riêng" = **HÒA TAN**; "tách một bản lưu đơn để kéo về" = nghe giống **NHÚNG-SỞ-HỮU** nhưng đọc kỹ nhu cầu thật (*"có chỗ để kéo về và cài đặt ổn định"*) lại đúng là mô tả của **KÉO NGOÀI**. Bảng quyết định trong concept này là căn cứ chọn ở `## Approaches`.

Dữ kiện quyết định, đo trực tiếp trong phiên đo này: `git log` trong repo code-graph thật (`/Volumes/.../workspace/graph`) cho hai tác giả — `rheinmir <rheinmir@gmail.com>` và `Trần Bùi Hoàng Gia <hgia.tb@gmail.com>` — và remote `https://github.com/Rheinmir/graph-kit.git`. `Rheinmir` là cùng tổ chức GitHub sở hữu `rheinmir/setup` — chính framework này. Đây không phải công cụ bên thứ ba như `last30days`/`agent-reach`; đây là repo khác của cùng tác giả, đã có remote thật, 2.206 dòng code (không tính `.venv`).

`harness/travel-policy.yaml` Tầng 1 `research_reach` là tiền lệ chạy thật cho đúng kiểu adapt này: `last30days`, `agent-reach` đăng ký ở đó, engine sống global, state máy-local không travel, tái lập bằng lệnh doctor riêng của từng công cụ.

`harness/scripts/dep-health.py` (đã đọc để lấy nguyên tắc) ghi lại một bài học đắt liên quan trực tiếp: *"quảng cáo một năng lực = phải THĂM DÒ nó, không phải kiểm sự tồn tại của nó."* Bài học đó sinh ra vì `code-graph` từng hỏng nhiều tuần mà framework vẫn quảng cáo nó dựa trên `(root / ".graph-agent" / "index.db").is_file()` — file tồn tại không có nghĩa dùng được. Nguyên tắc này áp thẳng vào bootstrap: cài xong phải verify, không chỉ ghi entry rồi tin.

`llmwiki/.claude/hooks/code_graph_keeper.py` đã tồn tại và cài qua SessionStart, nhưng nó chỉ **giữ registry bền** cho server ĐÃ CÀI — không cài server. Draft này lấp đúng khoảng trống trước nó: bootstrap cài server; keeper giữ nó sống qua restart. Hai trách nhiệm khác nhau, không gộp — xem `## Non-goals`.

Số đo biện minh cho việc đầu tư formalize (từ draft `[[200726-context-hygiene-budget]]`, đã thi hành T1-T4 trong phiên trước): sau khi vệ sinh, `get_callers("save")` cho 5 kết quả sạch thay vì 65 lẫn rác — trả lời đúng nợ đã ghi trong bàn giao *"chưa đo get_callers — phần duy nhất biện minh cho sự tồn tại của nó"*.

## Global constraints

- `harness/travel-policy.yaml` Tầng 1 `global_shared`: *"cài 1 lần, mọi project được gác đều dùng chung. Update 1 chỗ. KHÔNG copy vào từng repo."*
- [[adapt-modes]] Kiểu 2 nguyên văn: *"KHÔNG viết lại; framework chỉ giữ con trỏ + pin... Engine sống global/ngoài... chỉ recipe đi theo git; engine cài global; state máy-local KHÔNG travel."*
- Fail-open tuyệt đối: bootstrap thất bại (mạng, remote không tới được) KHÔNG được làm gãy `install-harness.sh --global` — đúng luật đã áp cho mọi hook trong framework này.
- `llmwiki/CLAUDE.md`: *"Edit to shared code → invoke impact-check then safe-change."* `install-harness.sh` là mã dùng chung mọi lần cài, đổi sai lan ra mọi máy.

## Non-goals

- **Không** vendor bytes của graph-kit vào `setup/setup` — đã bác ở `## Approaches`, đúng cảnh báo trong [[adapt-modes]] rằng NHÚNG "sở hữu thứ mình phải nuôi hộ".
- **Không** viết lại parser/indexer/server từ đầu thành mã nội bộ framework — HÒA TAN đã bác, cùng tác giả sở hữu cả hai repo nên không có lý do tái tạo.
- **Không** ép mọi máy cài framework phải có code-graph — vẫn optional như `research_reach`, fail-open nếu bỏ qua.
- **Không** đổi thêm gì trong chính source graph-kit ngoài hai fix đã làm ở phiên trước (SKIP_DIRS, `_each_db` dedupe/nhãn/trần) — việc ở đây là formalize đường cài, không phải sửa thêm engine.
- **Không** gộp trách nhiệm bootstrap (một lần lúc cài) với `code_graph_keeper.py` (mỗi phiên giữ registry tươi) thành một hook.

## Approaches

**Phương án A — KÉO NGOÀI, pin + bootstrap (chọn).** `travel-policy.yaml` khai code-graph ở Tầng 1 theo khuôn `research_reach`; `install-harness.sh --global` thêm bước clone `Rheinmir/graph-kit` pin theo commit, dựng `.venv`, ghi entry MCP, verify bằng thăm dò thật (không chỉ kiểm tồn tại file). Ưu điểm: khớp đúng cả ba tiêu chí trong bảng quyết định của [[adapt-modes]] — phụ thuộc ngoài chấp nhận được (chính là tác giả), chỉ pin + audit, state máy-local vốn dĩ không travel được dù chọn kiểu nào. Nhược điểm: cần mạng lúc cài lần đầu — chấp nhận được vì đã có tiền lệ `research_reach` sống với cùng ràng buộc.

**Phương án B — giữ nguyên hiện trạng, chỉ có keeper hook.** Chi phí bằng không, nhưng không trả lời được câu hỏi gốc: máy mới `curl` cài framework sẽ không có code-graph, `CAPABILITIES.md`/`session_start.py` tiếp tục nhắc tới một năng lực không tự có mặt. Bác — đây chính là khoảng trống user chỉ ra.

**Phương án C — NHÚNG-SỞ-HỮU.** Copy bytes vào `harness/vendor/graph-kit/`. Bác: hai fix hôm qua đã cho thấy engine còn đang sửa tích cực; vendor một bản là bắt đầu trôi ngay từ commit tiếp theo trên `Rheinmir/graph-kit`, đúng chi phí "nuôi hộ" mà concept cảnh báo. Nhu cầu thật của user (*"có chỗ để kéo về ổn định"*) đã được KÉO NGOÀI giải qua cơ chế pin — không cần trả giá bằng bản sao trôi dạt.

## Requirements (FR)

**FR-001**: `harness/travel-policy.yaml` Tầng 1 (`global_shared`) PHẢI có một mục cho code-graph, viết theo đúng khuôn đã dùng cho `research_reach`: nguồn (`Rheinmir/graph-kit`), adapt_mode (KÉO NGOÀI), state máy-local không travel (`.venv`, `~/.graph-agent/repos.txt`, tiến trình `--watch`), lệnh tái lập mỗi máy.

**FR-002**: `install-harness.sh --global` PHẢI có bước bootstrap: kiểm `~/.claude.json` đã có `mcpServers.code-graph` chưa; thiếu thì clone `Rheinmir/graph-kit` pin theo commit cố định, dựng `.venv`, ghi entry MCP đúng schema đã thấy trong `~/.claude.json` hiện tại (`command` = python trong `.venv`, `args` = `[server.py, --watch]`). Fail-open: lỗi ở bước này in cảnh báo, KHÔNG dừng install.

**FR-003**: Bootstrap PHẢI thăm dò sau khi cài, không chỉ kiểm tồn tại — đúng nguyên tắc `dep-health.py`. Verify bằng cách chạy thử engine cục bộ (import module hoặc gọi `get_stats`-equivalent) và xác nhận trả về dict có khoá `files/symbols/edges`, không phải lỗi "no such table".

**FR-004**: Nguồn gốc (`repo#commit`) của code-graph đang pin PHẢI ghi ở một nơi cố định để biết khi nào cần re-pin — không ép vào `fdk/skills.provenance.json` (schema đó dành cho `skills/<name>/`, code-graph không phải skill theo nghĩa đó); ghi ngay trong comment của mục travel-policy ở FR-001, theo đúng cách `research_reach` đã ghi version pin (`v3.11.0`, `v1.5.0`) ngay trong dòng khai.

**FR-005**: `code_graph_keeper.py` PHẢI giữ nguyên hành vi hiện tại (giữ registry bền mỗi phiên) — bootstrap (FR-002) là bước một lần lúc cài, keeper là bước lặp lại mỗi phiên; không gộp, không rewrite hook đó trong đợt này.

**FR-006**: Hai fix đã áp trực tiếp lên `/Volumes/.../workspace/graph` trong phiên trước (thêm `scratchpad` vào `SKIP_DIRS`, viết lại `_each_db` để gắn nhãn/dedupe/trần) PHẢI được commit và push lên `Rheinmir/graph-kit` trước khi FR-002 pin theo sha — pin một commit chưa tồn tại trên remote là vô nghĩa.

## Success criteria (SC)

**SC-001**: Một máy hoàn toàn mới (chưa từng cấu hình `~/.claude.json` cho code-graph) chạy `curl`-bootstrap xong thì `mcpServers.code-graph` tồn tại VÀ gọi `get_stats` trả về số liệu thật, không cần thao tác tay nào khác ngoài lệnh cài ban đầu.

**SC-002**: Một máy đã có code-graph cấu hình theo cách cũ (thủ công, giống máy đang dùng bây giờ) chạy lại bootstrap không phá cấu hình hiện có — idempotent, không ghi đè entry MCP đang hoạt động bằng một bản pin cũ hơn.

**SC-003**: Bootstrap thất bại vì mạng hoặc remote không tới được thì `install-harness.sh --global` vẫn hoàn tất phần còn lại và chỉ in cảnh báo — không một người dùng nào bị chặn cài framework chỉ vì không có mạng để lấy code-graph.

## Plan

- [ ] **T1 — Push 2 fix đã áp trong phiên trước lên `Rheinmir/graph-kit`.** Verify: `git log` trên remote có commit chứa `_each_db` mới; lấy sha thật để pin ở T3.
- [ ] **T2 — Viết mục travel-policy.yaml theo FR-001/FR-004.** Verify: đối chiếu bằng mắt với khuôn `research_reach` đã có — cùng cấu trúc dòng.
- [ ] **T3 — Viết bước bootstrap trong `install-harness.sh --global` theo FR-002/FR-003.** Verify: chạy `bash install-harness.sh --global` trên một `$HOME` giả (biến `HOME=/tmp/fake-home`) chưa từng có `~/.claude.json`, xác nhận entry MCP xuất hiện và `get_stats`-equivalent trả dict hợp lệ.
- [ ] **T4 — Test SC-001 và SC-002 bằng kịch bản trước/sau.** Verify: chạy hai lần liên tiếp trên cùng `$HOME` giả, lần hai không đổi entry đã có (idempotent).
- [ ] **T5 — Test SC-003 bằng cách giả lập mất mạng (chặn DNS remote hoặc dùng URL sai).** Verify: `install-harness.sh --global` vẫn exit 0, có dòng cảnh báo code-graph bootstrap thất bại.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| T1 | OpenCode (rẻ) | Thuần cơ học: nội dung đã duyệt xong ở phiên trước, chỉ `git commit`/`push` đúng lệnh, không có phán đoán nào cần Claude | pending |
| T2 | OpenCode (rẻ) | Chép khuôn `research_reach` có sẵn, có lưới an toàn tất định (`travel_policy_sync.py` bắt sai định dạng) — rủi ro giao agent rẻ thấp | pending |
| T3 | Claude | Đụng `install-harness.sh` — mã dùng chung mọi máy cài framework, sai một dòng lan diện rộng; cần đọc hiểu luồng trước khi sửa, không phải chép khuôn | pending |
| T4 | OpenCode (rẻ) | Bước verify đã viết rõ trong Plan (chạy 2 lần, so diff) — cơ học nếu quy trình đã đặc tả sẵn, không cần phán đoán thêm | pending |
| T5 | Claude | Cần hiểu đúng chỗ script gọi mạng để chặn ĐÚNG điểm mô phỏng lỗi — sai chỗ chặn thì test không kiểm tra được nhánh fail-open thật, cùng lớp rủi ro với T3 | pending |

## Assumptions

- Pin theo commit sha trực tiếp, không theo tag/version riêng — **(default)**: `Rheinmir/graph-kit` chưa có versioning (không thấy tag nào trong `git log`), dùng sha là cách rẻ nhất khớp thực tế hiện có; nếu về sau graph-kit ra tag chính thức thì đổi sang pin theo tag, giống `research_reach` đang làm với `last30days`/`agent-reach`.
- Bootstrap chỉ chạy trong nhánh `--global` của `install-harness.sh`, không chạy ở cài per-repo — **(default)**: khớp đúng cách `research_reach` hoạt động (cài 1 lần, dùng chung mọi project), và đúng travel-policy Tầng 1.
- Bootstrap **không** tự động đăng ký (index) repo hiện tại vào code-graph ngay lúc cài — **(default)**: chỉ dựng `.venv` + ghi entry MCP; việc index/register vẫn cần một hành động có ý thức (`reindex_repo` hoặc do `code_graph_keeper.py` tự phát hiện ở phiên sau, hook này đã có sẵn dòng cảnh báo *"gọi reindex_repo(<path>) để bật auto-watch"*). Lý do không mặc định tự index: một tiến trình `--watch` mới cộng một lần quét toàn repo là chi phí tài nguyên xuất hiện bất ngờ trên máy người khác ngay lúc `curl` — không phải quyết định nên tự động hoá âm thầm, dù không thuộc nhóm carve-out CẦN LÀM RÕ (không phải auth/tiền/dữ liệu/pháp lý) nên không chặn cổng, chỉ ghi rõ để người duyệt thấy.

## Self-review

**Phủ yêu cầu.** Ba nhánh của câu hỏi gốc — "curl không tự cài", "từ bỏ + distill riêng", "tách một bản để kéo về" — đều được xử lý: nhánh một là toàn bộ FR-002/FR-003 (T3); nhánh hai bị bác có lý do đo được ở `## Approaches`; nhánh ba được nhận diện lại đúng thành KÉO NGOÀI thay vì NHÚNG, và giải bằng FR-001/FR-004.

**Quét chỗ bỏ ngỏ.** Không còn ô trống chờ đoán hộ. Một quyết định rủi ro thấp (không tự-index lúc cài) đã hạ xuống `(default)` có lý do rõ thay vì để mơ hồ.

**Nhất quán tên-kiểu.** Dùng thống nhất "bootstrap" cho bước cài một lần, "keeper" cho hook giữ bền mỗi phiên (khớp đúng tên file `code_graph_keeper.py`, không đặt tên khác cho cùng một thứ), "pin" cho việc khoá vào một commit/tag cụ thể — đúng thuật ngữ [[adapt-modes]] dùng.

## Origin
- **Source:** phiên `/fdk` 2026-07-21 — tiếp nối từ `[[200726-context-hygiene-budget]]` sau khi T1-T4 thi hành xong và lộ ra code-graph không nằm trong travel-policy
- **Concept nền:** [[adapt-modes]] (Kiểu 2 — KÉO NGOÀI) · `harness/travel-policy.yaml` Tầng 1 `research_reach` (tiền lệ) · `dep-health.py` (nguyên tắc thăm dò trước khi quảng cáo)
- **Task:** `T-260721-01`
