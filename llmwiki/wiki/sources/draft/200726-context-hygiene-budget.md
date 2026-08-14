---
type: draft
title: "Vệ sinh dữ liệu nền + trần ngân sách cho cái gì được vào context"
status: proposed
tags: [context, code-graph, skill-load, budget, hygiene, downstream]
timestamp: 2026-07-20
task: T-260720-02
---

# Vệ sinh nền + trần ngân sách cho context

**Status:** proposed

Yêu cầu gốc, gói trong một câu: làm sao để agent ở dự án khách nhận đúng lượng context cần thiết — biết năng lực nào có sẵn và thấy đúng vùng code liên quan — mà không bị chôn dưới đống dữ liệu thừa.

**Sequence diagram:** [200726-context-hygiene-seq.html](../../../html/200726-context-hygiene-seq.html)

## Context

Ba nguồn tri thức đã có trong wiki đều chạm thẳng vào đề xuất này, và đọc chúng trước đã đổi hẳn hình dạng bản thiết kế.

[[skill-craft]] dựng sẵn khung kinh tế cho toàn bộ chuyện này. Nó tách hai loại phí: **context load** là phí máy trả, vì `description` của một skill model-invoked nằm trong cửa sổ ngữ cảnh mọi lượt mọi phiên kể cả phiên không bao giờ gọi tới nó; còn **cognitive load** là phí người trả, khi skill chỉ-gọi-tay khiến người dùng phải tự nhớ nó tồn tại. Concept này cũng nêu sẵn quy tắc chọn: chỉ để model-invoked khi agent *phải* tự với tới hoặc khi một skill khác *phải* gọi được nó; còn lại thì `disable-model-invocation: true` và không trả context load nào. Khung này viết từ 2026-07-15 và chưa được thi hành trên kho skill hiện tại.

`ADR-009` (session-orientation + auto-index + force-query) chốt rằng phiên mới phải *biết hệ thống có gì* thay vì lơ ngơ, và code-index phải tự khớp. Đề xuất này không đảo ADR-009 — nó đứng trên đó, và chỉ nói thêm rằng "biết có gì" không đồng nghĩa với "nạp hết mọi thứ".

`ADR-005` (logger và bản đồ năng lực đi xuống cùng dự án) là lý do phần vệ sinh phải chạy được ở downstream chứ không riêng repo framework: `build-capabilities` và `code-logger` đã travel xuống mọi dự án khách, nên bất cứ luật vệ sinh nào cũng phải travel cùng đường.

Ngoài wiki, phiên này đo trực tiếp trên hệ đang chạy và trên hai repo ngoài ([[graph-model]] cho bối cảnh đồ thị nội bộ). Các số đo nằm ở `## Evidence`.

## Global constraints

Chép nguyên văn từ nguồn có thẩm quyền, áp cho mọi task bên dưới.

- `llmwiki/CLAUDE.md`: "thứ gì auto-fire/tự-bơm context vào MỌI phiên (hook SessionStart/UserPromptSubmit, dòng auto-load) chỉ được phục vụ *dự án hiện tại*; context *nội-bộ-framework* (FDK, inventory, runbook sửa rule) phải **opt-in** qua skill gọi chủ động." (`ADR-004`)
- `llmwiki/CLAUDE.md`: "Match a file's verbosity to its reader… Documentation a human reads or reviews (review reports, ADRs, README, CONTRIBUTING and runbooks, output-reports, HTML pages) must be full, readable prose with complete sentences."
- `llmwiki/CLAUDE.md`, cái thang chống over-engineering: "**Hiểu bài trước, leo thang sau.** Đọc code, trace flow end-to-end rồi mới sửa. Diff nhỏ ĐẶT SAI CHỖ = bug thứ hai." Bậc rẻ nhất là xoá.
- `llmwiki/CLAUDE.md`, 5-Why: "**Tìm HỘI TỤ trước khi sửa.** Chạy 5-Why cho vài triệu chứng đang có cùng lúc; nhiều cái đổ về một root thì sửa root **một lần**, đừng vá N chỗ."
- `harness/travel-policy.yaml`: mọi năng lực phải khai đúng tầng (`global_shared` / `travel_in_repo` / `framework_only`), và từ phiên này installer không đọc policy lúc chạy — danh sách `STRIP_TIER3` nằm trong `install-harness.sh`, được `harness/validators/travel_policy_sync.py` gác đồng bộ hai chiều.
- Fail-open tuyệt đối ở tầng hook: thiếu công cụ, DB lỗi, hay timeout thì bỏ qua, không bao giờ làm gãy phiên của người dùng.
- Tất định trước, LLM sau: phần nào đếm được, lọc được, so được thì phải chạy bằng code không gọi model.

## Evidence

Đây là phần quan trọng nhất của draft, vì nó vừa biện minh cho việc được chọn vừa chặn ba hướng đã thử và bỏ.

**Quy mô thật ở dự án khách.** `code-graph get_stats` trả về 16 project, 5.970 file, 52.533 symbol, **546.133 cạnh**. Con số này lớn gấp khoảng 1.900 lần đồ thị wiki nội bộ (283 cạnh `touches`), nên mọi kết luận rút ra từ quy mô wiki đều không áp được sang đây.

**Chất lượng dữ liệu nền, đo bằng một truy vấn điển hình.** `get_callers("save")` trả về khoảng 65 kết quả, ước lượng 2.000 token, và hỏng bốn cách cùng lúc. Thứ nhất, không phân tách project: một câu trả lời trộn lẫn `web/app/api/auth/login/route.ts`, `etl/generate_report.py`, `src/payroll_data_process/…`, `components-page/…` và `scratchpad/spec-kit/…`, nghĩa là agent đang làm ở dự án khách A nhận về callers của dự án B — đây là lỗi đúng-sai, không phải lỗi ngân sách. Thứ hai, index cả rác: trong kết quả có `.next/standalone/node_modules/.pnpm/next@14.2.35…/crypto-browserify/index.js`, tức build artifact và `node_modules` đã nằm trong đồ thị. Thứ ba, trùng lặp thô: `apply_date_cell_format:187` xuất hiện ba lần trong cùng một response, `<module>` của crypto-browserify lặp năm lần. Thứ tư, khớp theo tên chứ không theo symbol, nên `Manifest.save` của một CLI Python nằm chung mâm với `model.save` của backend — đúng như nợ đã ghi trong bàn giao: "tra tên đã hoà 11-11 với grep".

**Chi phí context của kho skill.** 83 skill, tổng `description` là 34.195 ký tự, ước lượng **10.686 token**, tức khoảng 5,3% cửa sổ 200k, nạp lại mỗi phiên. Trung vị mỗi mô tả là 358 ký tự; nhóm dài nhất gồm `docs-site-macos` 1.092, `fdk-uat` 1.062, `council` 1.015, `ship` 990 — dài gấp ba lần trung vị.

**Baseline hành vi, dùng để đo hiệu quả sau này.** `skill-usage.py` đếm trên 46 phiên: 102 lượt gọi Skill, **26 skill riêng biệt được dùng**, tức **57/83 skill chưa bao giờ được gọi lần nào**. Nhóm dùng nhiều nhất là `fdk` 17, `docs-site-macos` 14, `propose` 13, `council` 9.

**Bằng chứng phản diện từ repo ngoài.** `tirth8205/code-review-graph` (22.043 sao, 713 commit, 31.391 dòng test, CI có cổng coverage) commit thẳng kết quả eval vào repo, và không một dòng nào trong 13 dòng benchmark `token_efficiency` có ratio vượt 1.0. Trường hợp cụ thể: một commit trong fastapi mà đọc thẳng file hết 6.045 token, `git diff` hết 299, còn context do graph sinh ra hết **195.653**. Đọc code thì thấy nguyên nhân không phải thuật toán — họ có đủ trọng số cạnh, suy giảm theo hop, sàn cắt và cap 500 node — mà là **chỗ duy nhất họ để lỏng: ngân sách**, được giao cho LLM tự giác qua một dòng prompt "nhớ dùng minimal trước". Benchmark `impact_accuracy` của họ cũng cho recall 1.0 nhưng precision trung vị chỉ khoảng 0.5.

**Ba hướng đã thử trong phiên và bị bác bằng số.** Hướng thứ nhất là chấm điểm BM25 trên prompt của người dùng để tự động gợi ý skill: đo trên 1.877 prompt người thật (sau khi lọc bỏ 22.863 tool-result, 4.412 message subagent và 751 meta bằng cờ transcript) cho thấy điểm tuyệt đối trôi theo độ dài prompt — một log Jenkins dán vào đạt 3.159 điểm trong khi trung vị chỉ 11.61 — và margin top-1/top-2 thì nổ ở đuôi thưa, khiến những câu vô nghĩa nhất như `'tiếp tục'`, `'ok'`, `'xong chua'` lại đạt margin vô cực. Hướng thứ hai là chỉ chấm điểm phần đầu và cuối prompt: 622/841 prompt dài đổi hẳn kết luận khi cắt, tức 74% bất đồng, nên cả hai cách đều đang đoán bừa. Hướng thứ ba là dùng min-cut hoặc normalized cut: sai hình dạng bài toán, vì min-cut giải "chia đồ thị làm hai nửa rẻ nhất" chứ không giải "chọn tập node dưới ngân sách"; bài đúng hình dạng là Prize-Collecting Steiner Tree, nhưng nó chỉ đáng khi đo được rằng xếp-hạng-rồi-cắt bỏ sót cụm liên quan thật.

**Ngưỡng vỡ của cách "nạp hết", tính từ chính số đo trên.** Trung bình mỗi skill tốn 129 token mô tả. Chiếu lên cửa sổ 200k: 83 skill hiện tại chiếm 5,3%; 120 skill chiếm 7,7%; **155 skill chạm 10%**; 200 skill chiếm 12,9%; **310 skill chạm 20%**; 500 skill chiếm 32,2%. Kết luận "nạp hết rẻ hơn scorer" vì vậy đúng ở quy mô hôm nay nhưng có hạn sử dụng, và nó hết hạn một cách *âm thầm* — không có cảnh báo nào, chỉ là cửa sổ ngày càng chật mà không ai truy được nguyên nhân. Nguồn phình nhanh nhất là skill adapt từ ngoài, vì chúng vào theo lô và không ai kiểm ngân sách lúc cài.

**Cơ chế cho quy mô lớn đã tồn tại và đang chạy.** Phiên đo này chạy dưới chế độ deferred tools: danh sách tool chỉ mang **tên**, còn schema chỉ được nạp khi agent gọi `ToolSearch`. Đó là progressive disclosure ở tầng tool, và nó chính là hình mẫu cần nhân sang tầng skill khi kho vượt ngưỡng. Đáng ghi nhận: khảo sát 30+ system prompt thương mại trong `x1xhlol/system-prompts-and-models-of-ai-tools` không tìm thấy agent nào có cơ chế này — mẫu tiến bộ nhất chỉ tới index-file cộng đọc-theo-yêu-cầu của v0.

**Điểm hội tụ.** Cả ba nguồn đều hỏng hoặc thành công ở cùng một chỗ, và không chỗ nào là thuật toán: một repo 22k sao thất bại vì thiếu cưỡng chế ngân sách; bài toán chọn skill hoá ra không cần scorer vì nạp hết chỉ tốn 5,3% context và model tự chọn tốt hơn; và code-graph bị chặn bởi vệ sinh dữ liệu chứ không bởi thiếu thuật toán chọn.

**Code-graph không phải hạ tầng do framework này sở hữu — cần nói rõ trước khi đọc phần thi hành T1-T4.** Server thật (`server.py`, `indexer.py`, `db.py`) sống ở một repo riêng ngoài `setup/setup` (`/Volumes/.../workspace/graph`), đăng ký MCP chỉ nằm trong `~/.claude.json` cá nhân của máy vận hành — không một dòng nào trong `travel-policy.yaml` hay `install-harness.sh` cài đặt hay travel nó. Framework chỉ có một hook phụ trợ (`code_graph_keeper.py`, cài qua SessionStart) giữ registry bền qua restart, fail-open tuyệt đối. Điều đáng ghi nhận: `session_start.py:118-146` không quảng cáo mù — nó thăm dò thật qua `dep-health.py` trước khi hiện gợi ý, và đã có A/B thật (`harness/metrics/code-graph-ab.json`): tra hàm/lớp/method hoà 11-11 với grep, tra hằng số thua 2,6× (13 vs 5 tool-call) nên đã tự viết luôn dòng cảnh báo dùng grep cho hằng số. Đây KHÔNG phải một hạ tầng hứa suông — nó đã tự đo giới hạn của chính mình trước khi phiên này chạm vào.

**Đo thật sau khi sửa T1-T3 (áp trực tiếp lên hai DB thật, không phải bản demo):** `get_callers("save")` từ 65 kết quả thô, lẫn project, lẫn rác, trùng lặp → **5 kết quả sạch**, mỗi dòng có nhãn project, 0 rác — sau khi reindex 2/19 repo trong registry (`setup/setup`: 2.744→109 file, 96% từng là rác; `fe`: gỡ 1.612 file rác). Đây là câu trả lời cho nợ đã ghi trong bàn giao *"chưa đo `get_callers` — phần duy nhất biện minh cho sự tồn tại của nó"*: có, sau khi vệ sinh nó cho kết quả grep không làm được (quan hệ gọi, không phải khớp tên). 17/19 repo còn lại trong registry chưa reindex — ngoài phạm vi đợt này.

## Non-goals

Những thứ cố ý **không** làm trong phạm vi này, mỗi thứ kèm lý do đã đo:

- **Không** xây engine chấm điểm prompt để tự động inject skill. Đã bác bằng số ở `## Evidence`; nạp hết rẻ hơn và chính xác hơn.
- **Không** thêm embedding vào bất kỳ đường nào. BM25 thuần stdlib đang hit@1 18/18 trên golden, và `mem-rank` đã cho thấy embedding là nhánh chưa verified (`verified: false`, `embedder_cmd: null`).
- **Không** cài Prize-Collecting Steiner Tree hay bất kỳ thuật toán chọn tối ưu nào ở vòng này. Điều kiện kích hoạt được ghi thành FR để phiên sau biết khi nào mở lại.
- **Không** đụng `parser`, không thêm ngôn ngữ, không đổi cách index sinh ra symbol.
- **Không** đổi hành vi mặc định của bất kỳ hook nào theo hướng bơm thêm. Mọi thay đổi ở đây phải là *cắt bớt* hoặc *lọc*, không phải *cộng thêm*.

## Approaches

**Phương án A — lọc nguồn và cưỡng chế trần bằng code (chọn).** Loại `node_modules`, `.next`, `dist`, `build`, `scratchpad` khỏi index; ràng buộc truy vấn theo project đang mở; khử trùng lặp; cap số kết quả kèm cờ báo đã cắt. Song song, chuyển các skill chỉ-bao-giờ-gọi-tay sang `disable-model-invocation: true` theo đúng quy tắc của [[skill-craft]]. Ưu điểm: mỗi thay đổi đều tất định, kiểm được bằng một lệnh, và đều thuộc bậc thấp của cái thang (xoá và lọc, không thêm cơ chế). Nhược điểm: không giải được ca "phải đi qua node điểm thấp mới tới cụm giá trị", nhưng ca đó chưa đo được là có tồn tại.

**Phương án B — giữ nguyên dữ liệu, xây tầng xếp hạng thông minh phía trên.** Cài trọng số cạnh, suy giảm theo hop, sàn cắt, rồi tiến tới PCST. Ưu điểm: về lý thuyết chọn tốt hơn khi đồ thị lớn. Nhược điểm quyết định: xếp hạng trên đồ thị chứa `node_modules` là tối ưu việc chọn rác, và repo 22k sao đã chứng minh bằng eval của chính họ rằng có đủ bộ trọng số vẫn ra 195k token khi thiếu trần. Bác.

**Phương án C — không đụng gì, dặn agent tự tiết chế.** Chi phí bằng không, và đây chính xác là cách `code-review-graph` chọn (`detail_level` thủ công cộng một dòng prompt nhắc dùng `minimal` trước). Eval của họ cho thấy đường mặc định vẫn ra 195.653 token. Bác — ngân sách giao cho model tự giác thì không phải ngân sách.

Chọn **A**, và giữ B lại như một pha sau có điều kiện kích hoạt đo được.

## Requirements (FR)

**FR-001**: Index của code-graph PHẢI loại trừ thư mục phụ thuộc và sản phẩm build (`node_modules`, `.next`, `dist`, `build`, `.venv`, `vendor`) cùng thư mục nháp (`scratchpad`), theo danh sách khai tường minh trong config chứ không hardcode rải rác.

**FR-002**: Truy vấn code-graph PHẢI cho phép giới hạn về một project tường minh, và mọi kết quả — kể cả khi không giới hạn — PHẢI gắn nhãn project để không còn lẫn nguồn im lặng. **Đã thi hành đúng nửa sau** (tham số `project` + nhãn trên mọi row); nửa đầu — tự nhận diện project đang mở làm mặc định thay vì mặc định tìm hết — **chưa làm**, vì cần suy `cwd` của tiến trình MCP ra repo root và chưa kiểm được điều đó đúng với mọi cách server được khởi động. Ghi làm việc tiếp, không tự nhận đã xong để tránh đúng loại lỗi `missing-verification` vừa distill trong phiên này.

**FR-003**: Kết quả trả về PHẢI khử trùng lặp theo khoá `(path, line, src_symbol)` trước khi ra khỏi tool.

**FR-004**: Mọi tool trả danh sách PHẢI cưỡng chế trần số lượng bằng code, và khi cắt thì PHẢI kèm cờ báo đã cắt cùng tổng số thật, để agent biết mình đang xem một phần.

**FR-005**: Skill nào chỉ bao giờ được gọi bằng tay PHẢI khai `disable-model-invocation: true` theo quy tắc trong [[skill-craft]], nhằm bỏ hẳn context load của nó.

**FR-006**: Nhóm mô tả skill dài bất thường PHẢI được cắt về gần trung vị, và ngân sách ký tự PHẢI phân bổ theo rủi ro bị gọi nhầm hoặc bị bỏ quên, không chia đều.

**FR-008**: Skill cài từ nguồn NGOÀI PHẢI mặc định `disable-model-invocation: true`, và chỉ được nâng lên model-invoked khi nêu được lý do agent phải tự với tới hoặc skill khác phải gọi tới. Đây là van chặn nguồn phình nhanh nhất, đặt ngay tại cửa cài thay vì dọn dẹp định kỳ về sau.

**FR-009**: Hệ thống PHẢI cảnh báo khi tổng ngân sách mô tả skill model-invoked vượt 10% cửa sổ ngữ cảnh, để cách "nạp hết" không hết hạn âm thầm. Phép đếm PHẢI **cộng token thật của từng mô tả đang bật model-invocation**, tuyệt đối không được nhân số skill với hằng số 129 — con số 129 chỉ là trung bình *hôm nay* và chính T5 sẽ làm nó trôi khi cắt nhóm mô tả dài. Nhân hằng số làm cổng báo sai theo hướng dễ chịu, tức im lặng đúng lúc lẽ ra phải nổ, và đó là kiểu hỏng khó phát hiện nhất. Mốc "khoảng 155 skill" trong `## Evidence` chỉ để hình dung quy mô, không phải công thức cài đặt. Khi chạm ngưỡng, đường đi tiếp là nhân mô hình progressive disclosure của deferred tools sang tầng skill: danh sách chỉ mang tên, mô tả đầy đủ nạp theo yêu cầu, và `build-skill-search.py` đóng vai router tra cứu — đây là vai trò đúng của BM25, khác hẳn vai trò auto-inject đã bị bác ở `## Evidence`.

**FR-007**: Hệ thống PHẢI ghi lại điều kiện kích hoạt để mở lại phương án B, gồm ngưỡng kích thước đồ thị sau khi đã lọc và bằng chứng đo được rằng xếp-hạng-rồi-cắt bỏ sót cụm liên quan thật.

## Success criteria (SC)

**SC-001**: Người dùng hỏi "ai gọi hàm này" ở một dự án khách thì nhận được câu trả lời chỉ chứa kết quả thuộc chính dự án đó, không lẫn dự án khác — kiểm bằng cách chạy lại đúng truy vấn `get_callers("save")` đã đo trong `## Evidence`.

**SC-002**: Không kết quả nào trả về trỏ vào thư mục phụ thuộc, sản phẩm build, hay thư mục nháp.

**SC-003**: Agent làm việc ở dự án khách tự gọi đúng skill mà không cần người nhắc tên, đo bằng **số skill riêng biệt được gọi** trong `skill-usage.py` — baseline hôm nay là 26/83 trên 46 phiên. Phép đo phải thực hiện trên các phiên **độc lập**, tức phiên không bàn về chính cơ chế này, vì phiên đang thảo luận đã bị nhiễm và mọi lời tự khai của agent trong đó đều vô giá trị.

**SC-004**: Context nạp cố định mỗi phiên giảm đo được so với hôm nay (10.686 token cho mô tả skill), mà số skill riêng biệt được gọi ở SC-003 **không giảm**. Chỉ giảm token mà mất lượt gọi đúng thì coi như thất bại.

**SC-005**: Một người mới đọc kết quả truy vấn hiểu ngay mình đang xem toàn bộ hay một phần, không phải đoán.

## Plan

- [x] **T1 — Khai danh sách loại trừ và scope project.** Code-graph thật nằm ngoài repo này (`/Volumes/.../workspace/graph`, MCP cá nhân khai trong `~/.claude.json`, KHÔNG thuộc travel-policy — xem ghi chú cuối mục Evidence). `SKIP_DIRS` trong `indexer.py` đã có sẵn `node_modules/.next/dist/build/vendor`; chỉ thiếu `scratchpad` — đã thêm. Tham số `project` thêm vào 7 tool (`search_symbols`, `get_callers`, `get_callees`, `get_file_symbols`, `get_file_imports`, `get_symbol_context`, `list_files`) qua `server.py`. Verify thật: `get_callers("save")` sau reindex 2/19 repo → 0 path `node_modules`/`.next`/`scratchpad`, mọi dòng có nhãn `project`.
- [x] **T2 — Khử trùng lặp và cưỡng chế trần.** `_each_db()` viết lại: gắn nhãn project, dedupe theo toàn bộ field của row (bắt được ca một repo đăng ký 2 alias path), cap qua `MAX_RESULTS` (env `GRAPH_MAX_RESULTS`, mặc định 20 — chính là U-02), trả `{results, total, truncated}`. Verify thật: `get_callers("save")` 65 raw → 57 sau dedupe (tầng query, không cần reindex) → 5 sau khi reindex sạch nguồn.
- [x] **T3 — Reindex sau khi lọc và đo lại quy mô.** `prune_ignored()` mới trong `indexer.py`, tự chạy mỗi `index_repo()`, xoá cascade `files→symbols→edges` khớp `SKIP_DIRS` hiện tại. Verify thật: `setup/setup` 2.744→109 file (2.636 = 96% là rác); `fe` prune 1.612 file. Chưa reindex 17/19 repo còn lại trong registry — ngoài phạm vi đợt này.
- [ ] **T4 — Rà 83 skill theo quy tắc [[skill-craft]], chuyển nhóm chỉ-gọi-tay sang `disable-model-invocation: true`.** Căn cứ chọn: skill chưa từng được gọi trong 46 phiên **và** không được skill nào khác gọi tới. Verify: đếm lại tổng ký tự `description` của nhóm còn model-invoked.
- [ ] **T5 — Cắt nhóm mô tả dài về gần trung vị, bổ sung vế "không dùng khi… dùng X thay thế" cho các cụm skill dễ gọi nhầm nhau.** Verify: trung vị và max của độ dài mô tả, so với 358 và 1.092 hôm nay.
- [ ] **T7 — Đặt van tại cửa cài skill ngoài và cổng cảnh báo ngân sách.** Skill adapt từ ngoài mặc định user-invoked; thêm một phép đếm tổng ngân sách mô tả model-invoked, cảnh báo khi vượt 10% cửa sổ. Verify: cài thử một skill ngoài và xác nhận nó không tự động vào context; chạy phép đếm ra con số so được với 10.686 token hôm nay.
- [ ] **T6 — Ghi điều kiện kích hoạt phương án B vào wiki** kèm toàn bộ số đo phản diện trong `## Evidence`, để phiên sau không đi lại vòng đã đi. Verify: trang concept tồn tại và được `index.md` trỏ tới.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| T1 | Claude | Chạm cấu hình index dùng chung mọi dự án khách; sai scope là hỏng đúng-sai, không phải hỏng thẩm mỹ | pending |
| T2 | Claude | Đụng đường trả kết quả của tool, cần giữ fail-open tuyệt đối | pending |
| T3 | OpenCode (rẻ) | Thuần cơ học: chạy lệnh, chép số vào wiki | pending |
| T4 | Claude | Cần phán đoán "skill này có bao giờ được skill khác gọi không" — đọc nhầm là làm skill biến mất khỏi tầm với | pending |
| T5 | Claude | Viết văn bản người đọc, phải theo luật prose đầy đủ | pending |
| T7 | Claude | Van tại cửa cài + cổng ngân sách; đặt sai thì skill ngoài lặng lẽ chiếm context của mọi phiên | pending |
| T6 | Claude | Chưng cất bài học phản diện, phần quý nhất của phiên | pending |

## Assumptions

- Danh sách loại trừ mặc định gồm `node_modules`, `.next`, `dist`, `build`, `.venv`, `vendor`, `scratchpad` — **(default)**, suy từ chính các path rác đã thấy trong kết quả đo; dự án khách nào có thư mục sinh tự động mang tên khác thì T1 bổ sung vào danh sách config.
- Trần mặc định cho danh sách trả về đặt ở 20 kết quả — **(default, find-out-later → [[unknown-context-hygiene]] U-02)**, chọn theo con số `limit` mà `code-review-graph` dùng; chưa đo trên hành vi thật ở dự án khách.
- Ngưỡng "skill chưa từng được gọi" lấy trên 46 phiên hiện có — **(default)**; đây là cửa sổ quan sát ngắn, một skill mùa vụ như `ship` có thể bị xếp nhầm, nên T4 phải kiểm thêm điều kiện "không skill nào khác gọi tới" trước khi hạ xuống user-invoked.
- Reindex sau khi thêm luật lọc sẽ không làm mất symbol thật nào — **(default)**; T3 phải so số trước/sau và nếu symbol giảm quá tỉ lệ file bị loại thì dừng lại điều tra.

## Self-review

**Phủ yêu cầu.** Yêu cầu gốc có hai nửa: agent phải biết năng lực nào có sẵn (nửa này về T4, T5) và phải thấy đúng vùng code liên quan ở dự án khách (nửa này về T1, T2, T3). T6 phục vụ yêu cầu ngầm mà người dùng nêu rõ trong phiên — không để phiên sau đi lại vòng đã đi. Không yêu cầu nào rơi ra ngoài, không task nào không truy được về một yêu cầu.

**Quét chỗ bỏ ngỏ.** Đã rà hết draft, không còn ô trống hay câu mô tả rỗng nào chờ người khác đoán hộ. Mọi bước trong Plan đều nêu lệnh hoặc con số cụ thể để đối chiếu, và giá trị duy nhất còn chưa chắc chắn — trần 20 kết quả — đã được ghi thành nợ có sổ `U-02` thay vì để lẫn vào văn bản.

**Nhất quán tên-kiểu.** Dùng thống nhất "trần" cho giới hạn số lượng, "sàn" cho ngưỡng cắt điểm, "lọc nguồn" cho việc loại thư mục khỏi index, và "context load" theo đúng thuật ngữ [[skill-craft]] chứ không đặt tên mới.

**Một chỗ tự nghi ngờ, ghi lại thay vì giấu.** SC-004 đòi giảm token mà không giảm lượt gọi đúng — nhưng nếu T4 hạ nhầm một skill xuống user-invoked thì tác hại chỉ lộ ra sau nhiều phiên, chậm hơn nhịp review. Đó là lý do T4 phải giữ điều kiện kép và SC-003 phải đo trên phiên độc lập, chứ không đo bằng lời agent tự khai.

## Origin
- **Source:** phiên `/fdk` 2026-07-20 — chuỗi từ bàn giao nền graph tới câu hỏi "MCP dùng cách gì để agent tự gọi đúng tool"
- **Concept nền:** [[skill-craft]] · [[graph-model]] · `ADR-005` · `ADR-009`
- **Repo tham chiếu:** `tirth8205/code-review-graph` (bằng chứng phản diện về ngân sách) · `x1xhlol/system-prompts-and-models-of-ai-tools` (mẫu mô tả tool của 30+ agent)
- **Task:** `T-260720-02`
