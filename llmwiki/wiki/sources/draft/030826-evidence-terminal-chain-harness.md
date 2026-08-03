---
type: draft
title: "evidence-terminal-chain — chuỗi kết luận phải chấm dứt ở chứng cứ xem được"
status: proposed
tags: [rule, evidence, grounding, anti-fabrication, claim-receipts, harness]
timestamp: 2026-08-03
task: T-260803-01
r7_meta: true
---

# 030826-evidence-terminal-chain-harness

**Status:** proposed

## What

Thêm vào harness một luật buộc mọi kết luận phải kết thúc ở **chứng cứ quan sát được**, không bao giờ kết thúc ở một lập luận khác: chuỗi `A ← B ← chứng cứ C` là hợp lệ, còn chuỗi `A ← B ← C` mà C lại là một suy luận nữa thì phải khai tiếp C dựa trên cái gì, cho tới khi chạm một điểm cuối mà người đọc mở ra xem được.

## Context

Wiki đã có ba mảnh liền kề, và không mảnh nào phủ được yêu cầu này.

`[[decision-anchoring]]` đặt ra nguyên tắc nền mà đề xuất này kế thừa nguyên vẹn: *"quảng cáo một năng lực = phải thăm dò nó, không phải kiểm sự tồn tại của nó."* Trang đó cũng để lại một bài học thiết kế quan trọng — bốn trạng thái liveness bắt buộc phải tách `UNAVAILABLE` ("không kiểm tra được") khỏi `ORPHAN` ("đã biến mất"), vì trộn hai sự thật rất khác nhau vào một tín hiệu sẽ khiến người xem hoảng vì cảnh báo giả. Luật chứng cứ dưới đây áp đúng kỷ luật đó cho một trục khác: "chưa kiểm chứng" phải tách khỏi "đã kiểm chứng", không được nhập nhèm.

`[[provenance-log]]` và `[[log-model]]` cho biết những sổ nào đang tồn tại và mỗi sổ giữ phạm vi hẹp nào — đây là nơi một chứng cứ loại "tool có ghi lại" sẽ trỏ tới, nên luật mới tiêu thụ chúng chứ không đẻ sổ thứ sáu.

`harness/scripts/claim-receipts.py` cùng `harness/claim-receipts.config.yaml` đã có taxonomy claim gồm `tool-output`, `inference`, `external-testimony`, `absence`, `ungrounded-opinion`, `observed-metric`, và đã verify được rằng một reference có resolve trên đĩa hay không. Đang ở `strictness: advisory`, `verified: false`, `resolver: filesystem`. Chỗ hở: nhãn `inference` được gán xong rồi **thả** — không có gì buộc một `inference` phải truy ngược về `tool-output`.

`harness/scripts/grounding-check.py` định schema verdict `{decision, claim, reason, required_evidence[]}`, tất định và không gọi LLM, với ba mã thoát phân biệt (0 hợp lệ, 2 schema sai, 3 hạ tầng không đọc được). Chỗ hở: nó chỉ áp cho verdict của evaluator, và nó kiểm `required_evidence` **có tồn tại** chứ không kiểm từng mục có phải là điểm cuối xem được hay lại là một suy luận nữa.

Issue mở `llmwiki/wiki/sources/draft/110726-anti-fabrication-observed-metrics.md` nằm trên trục khác — cấm bịa **số đo** về người dùng, không nói gì về hình dạng chuỗi suy luận.

Ngoài ra `policy.yaml` hiện có 18 luật R1 đến R18. Hai luật gần tinh thần này nhất là R16 `report-show-path` (artifact phải tự khai đường dẫn của chính nó) và R17 `problem-tree-flush` (phiên chạm framework phải để lại vết). Cả hai đều thuộc họ "artifact phải tự chứng", nên luật mới nằm cùng họ và đánh số tiếp là R19.

## Global constraints

Chép nguyên văn giá trị thật từ policy, docstring engine và cổng đang chạy — mỗi task ngầm mang theo toàn bộ mục này.

- **Tất định, 0 token, không gọi LLM.** Tiền lệ bắt buộc, chép từ docstring `harness/scripts/grounding-check.py`: *"validator schema cho verdict của evaluator (tất định, 0-token, KHÔNG LLM)"*. Mọi thứ trong đề xuất này phải chạy được khi không có mạng và không có model.
- **Ba mã thoát phân biệt.** Chép từ cùng docstring: `0 = hợp lệ`, `2 = đọc được nhưng schema sai`, `3 = hạ tầng lỗi, KHÔNG đọc được file`. Lý do ghi sẵn ở đó: *"Trước bản vá này, case này trả về 0 giống hệt 'hợp lệ', nên một cổng chỉ check rc==0 không phân biệt được 'chưa ai chấm' với 'đã chấm PASS' — gate coi như bị bypass bằng cách không sinh output."* Validator mới tuyệt đối không được trả 0 khi không đọc được đầu vào.
- **Advisory trước, blocking sau, và chỉ khi `verified: true`.** Chép nguyên tắc từ `harness/claim-receipts.config.yaml`: *"strictness: advisory — advisory (warn, exit 0) until resolver is symbol-aware; then 'strict'"* và *"Only then does an unresolved reference block."* Luật mới đi đúng đường đó: không chặn ai cho tới khi có corpus fixture thật chứng minh tỉ lệ báo oan chấp nhận được.
- **Mọi rule phải có bite-test.** Cổng `medic` probe `coverage` hiện đọc `18/18 rule có bite-test`. Thêm R19 mà không thêm bite-test sẽ làm cổng này tụt xuống 18/19 và `medic` đỏ.
- **Mọi `harness/tests/*-test.sh` phải có step trong CI.** Cổng `tests-wired` trong `.github/workflows/harness.yml` duyệt từng file và `exit 1` nếu thiếu: `grep -q "$(basename "$t")" .github/workflows/harness.yml || { echo "chưa wire vào CI: $t"; exit 1; }`.
- **Năng lực mới phải có neo capproof.** `medic` probe `capproof` hiện đọc `212/212 có NEO khai báo`; một validator mới không khai neo sẽ bị bêu `UNPROVEN`.
- **Luật wiki áp cho chính đề xuất này.** R2: mọi file wiki phải có `## Origin`. R3: thêm file wiki thì phải thêm dòng vào `llmwiki/wiki/index.md`, và cột Summary phải là câu mô tả nội dung thật chứ không phải ngày tháng. R1: không bao giờ ghi vào `raw/`. R5: file wiki nằm trong subfolder, không nằm ở gốc `wiki/`.
- **Travel-policy phải khai tầng cho file mới.** `harness/validators/travel_policy_sync.py` gác hai chiều; validator mới phải được xếp tầng rõ ràng, vì `install-harness.sh --global` gỡ đúng danh sách `framework_only` khỏi `~/.claude/harness` và giữ lại phần `global_shared`.
- **Văn xuôi đầy đủ cho tài liệu người đọc.** Chép từ `CLAUDE.md` (feedback 2026-06-27): tài liệu người đọc — ADR, README, report, trang HTML — phải là văn xuôi đủ câu, không được viết kiểu nén.

## Non-goals

- **Không validate văn xuôi tự do trong chat.** Không tồn tại cách tất định và 0-token để parse một đoạn lý luận tiếng Việt lẫn tiếng Anh rồi dựng đúng cây suy luận của nó. Phần chat được gác bằng **luật chữ** cộng với việc chấm mẫu, không bằng validator. Cố gate phần này sẽ đẻ ra một cổng báo oan liên tục, và cổng báo oan liên tục thì người ta học cách phớt lờ — lúc đó mất luôn tín hiệu thật.
- **Không dùng LLM để trích chuỗi suy luận.** Vi phạm ràng buộc 0-token ở trên, và biến chính cổng chống-bịa thành một thứ có thể bịa.
- **Không thay thế `claim-receipts.py` hay `grounding-check.py`.** Hai engine đó giữ nguyên phạm vi hẹp của mình; đề xuất này tiêu thụ lại phần resolver của chúng.
- **Không tự đi kiểm chứng hộ.** Validator không fetch URL, không gọi mạng lúc chạy gate. Nó kiểm **hình dạng và tính giải được** của chứng cứ, còn việc mở link ra đọc là của người hoặc của một bước riêng có mạng.
- **Không truy hồi ngược mọi tài liệu cũ.** Luật áp cho tài liệu mới và tài liệu được sửa, theo đúng cách ratchet mà `capproof` đang dùng (nợ tồn trong baseline thì xanh, nợ mới thì đỏ).

## Approaches

**Phương án A — quét văn xuôi bằng heuristic.** Dò các từ nối nhân quả ("vì", "do", "because", "nên") trong văn xuôi, dựng chuỗi, rồi cảnh báo khi chuỗi kết thúc ở một mệnh đề không chứa reference. Rẻ để bắt đầu và không bắt tác giả đổi cách viết. Nhưng độ chính xác thấp tới mức vô dụng: tiếng Việt và tiếng Anh trộn nhau, một câu có thể chứa nhiều mệnh đề nhân quả lồng nhau, và "vì" nhiều khi chỉ là liên từ tu từ. Kết quả thực tế sẽ là một cổng vừa bỏ sót vừa báo oan, tức là đúng cái bẫy đã ghi ở Non-goals.

**Phương án B — khối chuỗi chứng cứ tường minh.** Tài liệu mang kết luận phải kèm một khối máy đọc được, khai từng mắt xích dưới dạng `{id, claim, kind, because[], evidence}`. Validator dựng đồ thị từ khối đó và đòi **mọi đường đi từ gốc tới lá** phải kết thúc ở một nút loại chứng cứ, với yêu cầu riêng theo từng loại chứng cứ. Hoàn toàn tất định, không cần NLP, không cần LLM, chạy được offline. Giá phải trả là tác giả phải viết thêm khối đó — nhưng chính việc phải viết ra mới là cơ chế ép suy nghĩ, giống hệt cách `## Origin` ép truy nguồn.

**Phương án C — chỉ mở rộng `grounding-check.py`.** Giữ nguyên schema verdict hiện có, chỉ thêm ràng buộc rằng mỗi mục trong `required_evidence[]` phải thuộc một loại chứng cứ hợp lệ. Rẻ nhất, gần như không đẻ code mới. Nhưng phạm vi quá hẹp: nó chỉ chạm được verdict của evaluator, trong khi phần lớn kết luận của hệ nằm ở report, trang wiki, ADR và output-report của skill.

**Chọn B, và nuốt C vào trong B.** Phương án B là cái duy nhất phủ được yêu cầu gốc. Phần kiểm "một mục có phải chứng cứ hợp lệ không" được tách thành một hàm dùng chung, rồi `grounding-check.py` gọi lại chính hàm đó cho `required_evidence[]` của nó — như vậy đạt luôn lợi ích của C mà không phải viết hai bộ luật song song có nguy cơ lệch nhau. Phương án A bị loại thẳng và ghi lý do vào Non-goals để lần sau không ai đề xuất lại.

## Taxonomy chứng cứ — sáu loại, mỗi loại một điều kiện kết thúc

Đây là phần lõi của luật. Một nút chỉ được coi là **điểm cuối hợp lệ** khi nó thuộc một trong sáu loại dưới đây và thoả đúng điều kiện của loại đó.

| kind | Điều kiện để được tính là điểm cuối | Kiểm bằng gì (tất định) |
|---|---|---|
| `observed` | Một đường dẫn `file:line` hoặc `path` resolve được trên đĩa, hoặc một lệnh chạy lại được kèm output đã ghi | Tái dùng `resolve()` của `claim-receipts.py` |
| `tool-record` | Id của một mục trong `provenance-log.jsonl` / `events.jsonl` / ledger | Tra id trong sổ tương ứng |
| `graph-edge` | Một `eid` cạnh trong wiki graph (đúng thứ `/query` đang trích) | Tra eid trong graph |
| `web` | URL tuyệt đối trỏ tới **đúng chỗ tìm được**, kèm **ngày truy cập** và **trích nguyên văn** đoạn được dựa vào | Kiểm hình dạng URL, có mặt ngày và đoạn trích; **không** fetch mạng lúc gate |
| `parametric` | Thông tin đến từ **training của model**. Bắt buộc tự khai đúng loại này, **chỉ rõ nguồn gốc** (tên chuẩn, tài liệu, tác giả, đặc tả), và mang cờ chưa-kiểm-chứng | Kiểm có trường `origin` không rỗng và có cờ; **không** được là điểm cuối duy nhất của một kết luận dùng để quyết định |
| `absence` | Chính lệnh hoặc truy vấn đã chạy để tìm, kèm output rỗng của nó | Lệnh phải chạy lại được |

Hai loại cuối là phần bổ sung theo yêu cầu, và cũng là hai loại nguy hiểm nhất.

Với `web`, link không được trỏ chung chung vào trang chủ của một nguồn; nó phải trỏ tới đúng chỗ đã đọc, và phải kèm đoạn trích nguyên văn — vì trang web đổi nội dung, còn đoạn trích thì đóng băng cái mà kết luận thật sự dựa vào. Ngày truy cập cho người đọc sau này biết bản mình đang mở có còn là bản đã dùng hay không.

Với `parametric`, đây là loại **không xem được** — nó là lời khai về thứ model nhớ. Chính vì thế luật không cấm nó, mà bắt nó **lộ diện**: phải tự khai là kiến thức từ training, phải chỉ ra nó đến từ đâu để người khác đi kiểm được, và phải mang cờ chưa-kiểm-chứng. Quan trọng nhất, một chuỗi dẫn tới quyết định **không được kết thúc chỉ bằng `parametric`** — nó phải được nâng cấp thành `web` hoặc `observed`, hoặc phải đi kèm một điểm cuối thuộc loại khác. Đây chính là chỗ mà bịa đặt hay chui vào dưới lớp áo tự tin, nên nó là loại duy nhất bị hạ cấp bằng luật.

## Ví dụ thật lấy làm fixture

Phiên 03/08/2026 kết luận "OpenClaude tự dừng agent giữa chừng". Chuỗi đúng dạng mà luật muốn ép, và sẽ được đóng băng thành fixture xanh của bộ test:

```
C1  agent tự dừng giữa việc          ← because C2
C2  lượt bị cắt bởi một refusal chèn sẵn, không phải model sinh ra   ← because E1, E2
E1  [observed] 11 lượt refusal có tổng usage = 0 token, trong khi 297 lượt bình thường
    trung vị 50.477 token — đo từ ~/.openclaude/projects/<proj>/<session>.jsonl
E2  [observed] ngay sau mỗi lượt bị cắt là entry system subtype=stop_hook_summary
    trong cùng file transcript
```

Chuỗi phản-ví-dụ, sẽ là fixture đỏ: `C1 ← C2 ← C3` với C3 là "vì model bị giới hạn an toàn" mà không có nút chứng cứ nào phía sau — đúng hình dạng mà yêu cầu gốc cấm.

## Công tắc bật/tắt — ba tầng, và tắt thì phải LỘ RA

Luật này phải tắt được. Một cơ chế ép kỷ luật mà không có đường tắt sẽ bị né bằng cách tệ hơn nhiều: người ta viết khối chuỗi cho có, và lúc đó cổng vẫn xanh trong khi chất lượng đã chết. Ba tầng dưới đây chép đúng khuôn kill-switch mà repo đã chạy sống ở `hub.enabled` cộng cờ `--no-hub`, được `harness/tests/ge-killswitch-test.sh` gác bằng hai mệnh đề: công tắc phải có thật, và cờ một-lần-chạy phải đè được config đang bật.

- **Tầng bền — `enabled: true|false` trong `harness/evidence-terminal.config.yaml`.** Đây là công tắc đi theo repo, commit được, cả team dùng chung. Dùng khi một dự án quyết định chưa áp luật này.
- **Tầng phiên — biến môi trường `OVERSTACK_EVIDENCE_TERMINAL=0`.** Tắt cho một máy hoặc một phiên mà không phải sửa file trong repo, đúng quy ước `OVERSTACK_*` đang dùng ở `OVERSTACK_WIKIGRAPH` và `OVERSTACK_STOP_DEBOUNCE_S`.
- **Tầng một-lần-chạy — cờ `--no-evidence-chain`.** Đè cả hai tầng trên cho đúng một lần gọi, dành cho lúc chạy thử hoặc lúc gỡ rối chính validator.

Thứ tự ưu tiên đi từ hẹp tới rộng: cờ CLI thắng biến môi trường, biến môi trường thắng file config.

**Tắt không có nghĩa là biến mất.** Khi luật bị tắt, validator trả mã 0 nhưng vẫn in một dòng lên `stderr` nói rõ nó đang tắt và đang tắt vì tầng nào. Lý do là bài học đã ghi trong `[[decision-anchoring]]`: một cơ chế im lặng khi không hoạt động sẽ bị nhầm là đang hoạt động, và người ta yên tâm về một thứ đã chết từ lâu. Cổng câm nguy hiểm hơn cổng đỏ.

## Requirements (FR)

**FR-001**: Hệ thống PHẢI định nghĩa một khối chuỗi chứng cứ máy đọc được, mỗi nút gồm `id`, `claim`, `kind`, `because[]`, và `evidence` khi nút là điểm cuối.

**FR-002**: Hệ thống PHẢI từ chối một chuỗi khi tồn tại bất kỳ đường đi nào từ gốc tới lá mà lá đó không phải nút chứng cứ hợp lệ.

**FR-003**: Hệ thống PHẢI hỗ trợ đúng sáu loại chứng cứ `observed`, `tool-record`, `graph-edge`, `web`, `parametric`, `absence`, mỗi loại có điều kiện kết thúc riêng như bảng taxonomy.

**FR-004**: Với `kind: web`, hệ thống PHẢI đòi một URL tuyệt đối, một ngày truy cập, và một đoạn trích nguyên văn; thiếu bất kỳ trường nào thì nút không được tính là điểm cuối.

**FR-005**: Với `kind: parametric`, hệ thống PHẢI đòi trường `origin` không rỗng nêu nguồn gốc của kiến thức, PHẢI đánh dấu nút là chưa kiểm chứng, và PHẢI từ chối khi một chuỗi chỉ kết thúc bằng `parametric` mà không có điểm cuối loại khác đi kèm.

**FR-006**: Hệ thống PHẢI phát hiện chu trình trong đồ thị `because[]` và coi đó là chuỗi không hợp lệ, vì một chuỗi vòng tròn không bao giờ chạm chứng cứ.

**FR-007**: Hệ thống PHẢI dùng ba mã thoát phân biệt 0, 2, 3 đúng như `grounding-check.py`, và tuyệt đối không trả 0 khi không đọc được đầu vào.

**FR-008**: `grounding-check.py` PHẢI gọi lại đúng hàm kiểm điểm cuối dùng chung, để `required_evidence[]` của verdict chịu cùng một bộ luật.

**FR-009**: Luật PHẢI có bản chữ trong `CLAUDE.md` và `AGENT.md` cho phần chat, nơi validator không với tới.

**FR-010**: Luật PHẢI chạy ở chế độ advisory cho tới khi cấu hình khai `verified: true`, và PHẢI có bite-test cùng một step trong CI.

**FR-011**: Hệ thống PHẢI tắt được ở ba tầng — khoá `enabled` trong file cấu hình, biến môi trường `OVERSTACK_EVIDENCE_TERMINAL`, và cờ `--no-evidence-chain` cho một lần chạy — với thứ tự ưu tiên cờ thắng biến môi trường, biến môi trường thắng file cấu hình.

**FR-012**: Khi bị tắt, hệ thống PHẢI trả mã thoát 0 và PHẢI in lên `stderr` một dòng nêu rõ luật đang tắt cùng tầng nào đã tắt nó; hệ thống KHÔNG được im lặng hoàn toàn.

## Success criteria (SC)

**SC-001**: Người đọc một kết luận của hệ có thể đi từ kết luận đó tới một thứ mở ra xem được — file, lệnh chạy lại được, hoặc link tới đúng chỗ trên mạng — mà không phải hỏi lại tác giả. Kiểm bằng: lấy năm kết luận gần nhất trong wiki, mỗi cái phải đi hết được xuống điểm cuối.

**SC-002**: Khi model dùng kiến thức từ training của nó, người đọc nhận ra ngay điều đó và biết đi đâu để kiểm — thay vì tưởng đó là một sự thật đã được đo. Kiểm bằng: mọi nút `parametric` trong corpus đều có `origin` đọc được và cờ chưa-kiểm-chứng hiển thị ra trang.

**SC-003**: Một chuỗi lập luận vòng vo không có chứng cứ bị chặn lại **trước khi** nó thành kết luận được người khác tin và hành động theo. Kiểm bằng: fixture đỏ trong bộ test phải bị bắt.

**SC-004**: Luật không làm người viết bỏ chạy — trong ba mươi ngày đầu chạy advisory, số lần báo oan trên mỗi tài liệu đủ thấp để tác giả vẫn viết khối chuỗi thay vì tìm cách né. Kiểm bằng: đếm cảnh báo trên corpus thật trước khi bật blocking.

**SC-005**: Một dự án chưa muốn áp luật này tắt được nó trong vòng một phút mà không phải sửa code, và bất kỳ ai nhìn output đều biết ngay luật đang tắt chứ không tưởng nhầm là đang được gác. Kiểm bằng: tắt lần lượt ở cả ba tầng, mỗi lần đều thấy dòng thông báo trên `stderr` nêu đúng tầng đã tắt.

## Plan

- [ ] Task 1 — Chốt schema khối chuỗi chứng cứ và sáu loại điểm cuối thành một trang concept trong wiki, kèm ví dụ xanh và ví dụ đỏ lấy từ phiên 03/08.
- [ ] Task 2 — Viết `harness/validators/evidence_terminal.py`: parse khối, dựng đồ thị, phát hiện chu trình, duyệt mọi đường gốc-tới-lá, ba mã thoát 0/2/3.
- [ ] Task 3 — Viết hàm kiểm điểm cuối dùng chung theo từng `kind`, tái dùng `resolve()` của `claim-receipts.py` cho `observed`, và cài luật riêng cho `web` cùng `parametric`.
- [ ] Task 4 — Thêm cấu hình `harness/evidence-terminal.config.yaml` với `strictness: advisory` và `verified: false`, kèm checklist nâng cấp lên strict.
- [ ] Task 5 — Khai luật R19 `evidence-terminal` vào `harness/poc-vendor-neutral/policy.yaml` và nối handler, giữ `blocking: false` ở giai đoạn advisory.
- [ ] Task 6 — Nối `grounding-check.py` gọi lại hàm kiểm điểm cuối dùng chung cho `required_evidence[]`.
- [ ] Task 7 — Viết luật chữ vào `CLAUDE.md` và `AGENT.md` cho phần chat, nêu rõ ba loại chứng cứ và cấm kết thúc chuỗi bằng suy luận.
- [ ] Task 8 — Viết `harness/tests/evidence-terminal-test.sh` với fixture xanh và fixture đỏ, thêm bite-test cho R19, và nối step vào `.github/workflows/harness.yml`.
- [ ] Task 9 — Cài công tắc bật/tắt ba tầng cùng dòng thông báo khi tắt, và bọc bằng test kill-switch theo đúng hai mệnh đề mà `ge-killswitch-test.sh` đang gác.

## Assumptions

- Luật mới mang số **R19** `(default)` — tiếp sau R18, cùng họ "artifact phải tự chứng" với R16 và R17.
- Khối chuỗi được viết dưới dạng một fenced block YAML trong tài liệu `(default)` — cùng kiểu với cách `overstack.html` nhúng data tách khỏi markup, để sửa data không đụng văn xuôi.
- Bề mặt áp luật giai đoạn đầu là tài liệu dưới `llmwiki/wiki/` có mang kết luận, cộng với verdict của evaluator `(default, find-out-later)` — chưa mở rộng sang report HTML và output-report của skill cho tới khi đo được tỉ lệ báo oan.
- Validator **không** fetch URL lúc chạy gate `(default)` — giữ ràng buộc offline và 0-token; việc mở link là bước riêng của người hoặc của một job có mạng.
- Tầng travel-policy của `evidence_terminal.py` là `global_shared` `(default)` — cùng tầng với các validator khác để dự án downstream cũng được gác.
- Ngưỡng "báo oan đủ thấp" ở SC-004 chưa có con số cụ thể `(default, find-out-later)` — chốt sau khi chạy advisory trên corpus thật, vì đặt số bây giờ là bịa đúng cái loại số mà luật này cấm.
- Mặc định của khoá `enabled` là `true` `(default)` — luật bật sẵn khi cài, ai không muốn thì tắt tường minh. Bật-sẵn hợp với một luật đang ở chế độ advisory, vì nó chưa chặn được ai nên chi phí của việc bật nhầm gần bằng không, trong khi tắt-sẵn thì luật gần như không bao giờ được ai bật lên.
- Giá trị tắt của biến môi trường nhận cả `0`, `false` và `off` `(default)` — cùng khuôn với các biến `OVERSTACK_*` đang có, để người dùng không phải nhớ đúng một chuỗi.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| Task 1 — schema + trang concept | Claude | Thiết kế taxonomy và viết văn xuôi người đọc, cần phán đoán về ranh giới giữa các loại chứng cứ | pending |
| Task 2 — validator lõi | Claude | Logic đồ thị, phát hiện chu trình và ngữ nghĩa ba mã thoát là chỗ dễ sai ngầm | pending |
| Task 3 — hàm kiểm điểm cuối | Claude | Đụng code dùng chung với `claim-receipts.py`, cần map caller trước khi sửa | pending |
| Task 4 — file cấu hình | OpenCode (rẻ) | Viết YAML theo mẫu đã chốt ở Task 2 và Task 3, thuần cơ học | pending |
| Task 5 — khai R19 vào policy | Claude | Đụng `policy.yaml` là bề mặt luật, sai một trường là cổng câm | pending |
| Task 6 — nối grounding-check | Claude | Sửa engine đang chạy, phải giữ backward-compat cho ba mã thoát cũ | pending |
| Task 7 — luật chữ CLAUDE.md/AGENT.md | Claude | Văn bản luật, phải khớp từng chữ với hành vi code | pending |
| Task 8 — test + wire CI | Claude | Fixture đỏ phải thật sự bắt được, đây là chỗ test giả dễ lọt nhất | pending |
| Task 9 — công tắc ba tầng + test kill-switch | Claude | Thứ tự ưu tiên giữa ba tầng và điều kiện "tắt phải lộ ra" là ngữ nghĩa dễ cài sai thành cổng câm | pending |

**Sequence diagram:** [030826-evidence-terminal-chain-seq.html](../../../html/030826-evidence-terminal-chain-seq.html)

## Risks

- **Ma sát tác giả.** Bắt viết khối chuỗi cho mọi kết luận có thể khiến người ta viết cho có. Giảm bằng cách chỉ áp cho tài liệu mang kết luận thật, và chạy advisory đủ lâu để đo trước khi chặn.
- **Chứng cứ hình thức.** Một nút `observed` trỏ tới file có thật nhưng không thật sự chống lưng cho claim. Validator kiểm được đường dẫn resolve, không kiểm được nội dung có liên quan hay không — giới hạn này phải ghi thẳng vào trang concept, không được để người đọc tưởng cổng mạnh hơn thực tế.
- **`parametric` bị lạm dụng.** Nếu khai `parametric` quá dễ, nó thành cửa sau hợp thức hoá phỏng đoán. Chính vì thế luật cấm nó làm điểm cuối duy nhất cho kết luận dẫn tới quyết định.
- **Trùng lấn với `claim-receipts`.** Hai engine cùng đụng khái niệm reference. Giảm bằng cách tái dùng đúng hàm `resolve()` thay vì viết bản thứ hai.

## Self-review

- **Phủ yêu cầu.** Yêu cầu gốc gồm bốn phần: chuỗi phải kết thúc ở chứng cứ xem được (Task 1, 2, 3), chứng cứ web phải có link tới đúng chỗ tìm (Task 3, FR-004), chứng cứ từ training của model phải chỉ rõ nguồn gốc (Task 3, FR-005), và bật/tắt được phần suy luận này (Task 9, FR-011 và FR-012). Mỗi phần về đúng một cụm task, không phần nào rơi.
- **Quét placeholder.** Đã rà, không còn chuỗi rỗng nghĩa. Frontmatter khai `r7_meta: true` vì trang này **nói về** luật cấm placeholder và có trích nguyên văn các chuỗi bị cấm trong phần Global constraints.
- **Nhất quán tên-kiểu.** Dùng thống nhất `evidence_terminal.py` cho validator, `evidence-terminal` cho tên luật, `kind` cho loại chứng cứ, `because[]` cho cạnh suy luận, xuyên suốt toàn bộ tài liệu.

## Origin

- **Yêu cầu gốc:** user, phiên `b8afb386`, 2026-08-03 — hai lượt: luật chuỗi kết thúc ở chứng cứ, rồi bổ sung chứng cứ web phải có link và chứng cứ từ training phải chỉ rõ nguồn.
- **Prior art đã grep:** `harness/scripts/claim-receipts.py`, `harness/claim-receipts.config.yaml`, `harness/scripts/grounding-check.py`, `harness/poc-vendor-neutral/policy.yaml` (R1–R18), `llmwiki/wiki/sources/draft/110726-anti-fabrication-observed-metrics.md`.
- **Wiki đã query:** [[decision-anchoring]], [[provenance-log]], [[log-model]], [[wiki-core-relations]].
- **Task ID:** `T-260803-01`.
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
