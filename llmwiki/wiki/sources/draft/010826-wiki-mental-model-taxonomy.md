---
type: issue
kind: architecture
title: "Tái tổ chức wiki theo taxonomy Fact/Concept/Mental-Model/Framework + visualize cho người học mới"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, wiki, taxonomy, mental-model, visualization, onboarding, graph-model]
timestamp: 2026-08-01
id: 010826-wiki-mental-model-taxonomy
source_session: "Phiên hỏi user về cách wiki nên tái tổ chức để phục vụ người tư duy theo mental model"
---

# Issue: Tái tổ chức wiki theo taxonomy Fact/Concept/Mental-Model/Framework + visualize cho người học mới

## Vấn đề (một câu)
Wiki hiện tại phân loại nội dung theo *nơi lưu* (`concepts/`, `entities/`, `sources/`, `architecture/`) và theo *quan hệ có kiểu* (`implements`/`touches`/`depends-on`...), nhưng không phân loại theo **độ trừu tượng nhận thức** (fact → concept → mental model → framework) — nên không trả lời được câu hỏi của một người tư duy theo mental model: "khái niệm này đứng ở tầng nào, và tôi cần biết những fact/concept nào trước khi nó thành mental model trong đầu tôi?"

## Bối cảnh & bằng chứng
User (tư duy theo mental model) đưa ra bảng phân tầng 5 mức:

| Khái niệm | Là gì | Ví dụ |
|---|---|---|
| Fact | Sự thật riêng lẻ | Kafka dùng log append-only |
| Concept | Một khái niệm | Producer là gì |
| Knowledge | Tập hợp nhiều fact và concept | Biết cách dùng Kafka |
| Mental Model | Mô hình giải thích cách hệ thống vận hành | Producer → Broker → Partition → Consumer, dự đoán được tác động khi đổi |
| Framework | Cấu trúc giải quyết một lớp vấn đề | MVC, CQRS, Clean Architecture |

Yêu cầu hai vế: (1) wiki phải **visualize** để một người mental-model-first "thấy" được mô hình, không chỉ đọc văn xuôi tuần tự; (2) người **học cái mới hoàn toàn** (chưa có mental model sẵn) phải follow được — tức cần đường đi từ fact/concept lên tới mental model, không nhảy cóc.

**Cập nhật (cùng phiên, comment thêm của user):** bảng 5 mức ở trên là *bối cảnh*, không phải *nền tảng cần dựng*. User nêu rõ: "nó không phải tất cả" — cái phải làm nền tảng là một **chuỗi 3 lớp có thứ tự bắt buộc**:

```
Facts (Dữ liệu)
    ↓
Mental Models (Diễn giải)
    ↓
Protocols / Checklists (Thực thi ổn định)
```

Đây là thu hẹp có chủ đích, quan trọng cho phạm vi issue: nó gộp Concept/Knowledge vào dưới "Facts→Mental Model" (chi tiết trung gian, không cần tầng riêng), và **thêm hẳn một lớp thứ ba mà bảng 5 mức không có**: Protocol/Checklist — nơi một mental-model đã hiểu được đóng băng thành hành động lặp lại được, ổn định, không phụ thuộc trí nhớ. Lớp thứ ba này **đã tồn tại sẵn trong repo dưới một cái tên khác**: mọi `SKILL.md` và mọi rule trong `rule-registry` chính là Protocol/Checklist theo đúng định nghĩa này (một trình tự bước cố định, thực thi được, không cần diễn giải lại mỗi lần). Cái đang thiếu không phải là *xây* lớp 3 — mà là **liên kết tường minh** từ một Mental Model (trang wiki) tới Protocol (skill/rule) mà nó tạo ra, cùng cơ chế cho lớp 1 (Facts, nguồn dữ liệu có `derives-from`) nuôi đúng Mental Model nào.

**Cập nhật lần 2 (cùng phiên, comment thứ hai của user):** cái giá của việc dựng Mental Model có thể **rườm rà** — không phải fact nào cũng đáng, hoặc kịp, đi qua một lớp diễn giải đầy đủ trước khi thành hành động được. Yêu cầu thêm: phải có **đường tắt Fact → Protocol/Checklist trực tiếp**, bỏ qua Mental Model, cho những trường hợp không cần tầng diễn giải — thay vì buộc MỌI checklist phải có một Mental Model làm trung gian, tức thay vì để hệ thống **phình ra** theo đúng luật 3 lớp một cách cứng nhắc. Nói cách khác: chuỗi 3 lớp là **con đường đầy đủ nhất có thể có**, không phải **con đường bắt buộc duy nhất** — Mental Model là tầng tùy chọn (bồi đắp hiểu biết khi cần dự đoán/giải thích hệ vận hành), còn Fact→Protocol trực tiếp là đường lối tắt hợp lệ khi checklist đã đủ tự-giải-thích. Đây đúng cảnh báo Munger (#3) đã trích ở trên ("quy mô giải pháp vượt quy mô người vận hành") áp dụng ngược lại: đừng để chính taxonomy này trở thành lý do phải tạo Mental Model cho mọi thứ.

Đối chiếu wiki hiện có:
- [[graph-model]] đã có visualize thật (`fdk/tools/build-wiki-graph.py` → HTML graph node/edge), nhưng trục màu/phân nhóm hiện tại là *loại quan hệ* (`touches`, `wikilink`...) và *loại file* (concept/entity/source), **không phải trục độ-trừu-tượng**. Một `concept/` có thể thực chất là Fact đơn lẻ, một `architecture/` có thể là Mental Model hoặc Framework — hiện không phân biệt được bằng máy.
- [[wiki-core-relations]] (020726) đã thiết kế "quan hệ có kiểu" (`implements`/`supersedes`/`touches`/`derives-from`/`depends-on`/`contradicts`) và bài học cốt lõi: **"sự thật suy ra được thì phải suy, đừng cất"** (touches từng cất tay, đóng băng ở 21 cạnh, sau chuyển sang suy tại engine thì lên 283 cạnh, luôn tươi). Bài học này áp thẳng vào taxonomy mới: nếu thêm field `level: fact|concept|mental-model|framework` phải để **agent suy lúc `verify-before-commit`** (giống cách `relations:` được đề xuất tự suy — mục G5 trong council review của wiki-core-relations), không bắt gõ tay mỗi trang — gõ tay sẽ đóng băng y hệt `touches` từng bị.
- Council review của wiki-core-relations (seed42, 5 seat) đã cảnh báo đúng loại rủi ro sẽ lặp lại ở đây nếu làm ẩu: Munger (#3) — "quy mô giải pháp vượt quy mô người vận hành", Aurelius (#4) — tách rõ phần "tự-cưỡng-chế" khỏi phần "phụ thuộc hành vi con người tương lai". Một taxonomy mới cần học đúng hai cảnh báo này: đừng thêm hệ thống con thứ 7, và đừng kỳ vọng con người tự giác gắn nhãn.
- Chưa có bằng chứng nào trong wiki về "đường học cho newcomer" (progressive path từ fact lên mental model) — mục Human observability trong wiki-core-relations tự chấm 🟡, thiếu đúng phần "view theo tầng trừu tượng".

## Phạm vi
- Nền tảng phân loại là **3 lớp có thứ tự**: Facts (Dữ liệu) → Mental Models (Diễn giải) → Protocols/Checklists (Thực thi ổn định) — không phải toàn bộ bảng 5 mức ban đầu; bảng 5 mức chỉ dùng để minh hoạ bối cảnh, không phải taxonomy cần build.
- Cách **phân loại nội dung wiki hiện có** vào 2 lớp đầu (Fact/Mental-Model) — field mới trong frontmatter OKF hoặc suy ra được từ cấu trúc `relations:` sẵn có (vd: node có nhiều `depends-on` hội tụ + không `touches` code trực tiếp → khả năng là Mental Model).
- Cách **liên kết lớp 2 → lớp 3** (Mental Model → Protocol) VÀ đường tắt **lớp 1 → lớp 3** (Fact → Protocol trực tiếp, không qua Mental Model) — cùng một loại quan hệ, khác điểm xuất phát; lớp 3 KHÔNG cần xây mới, chỉ cần được nhìn nhận và link đúng.
- Cách **view HTML** (`build-wiki-graph.py` / trang mới) thể hiện được cả 3 lớp — filter/tô màu theo lớp, không chỉ theo loại quan hệ như hiện tại.
- Cách dẫn **người học mới** đi theo đúng chiều Fact → Mental Model → Protocol, tức một "learning path" suy ra được từ đồ thị quan hệ hiện có (`depends-on` + quan hệ liên kết lớp-3 mới), không phải danh sách tay.
- Universal: đụng cơ chế wiki dùng chung (frontmatter OKF, engine `wiki-graph.py`, renderer `build-wiki-graph.py`) và cách skill/rule được tham chiếu từ wiki — ảnh hưởng mọi dự án dùng overstack, không riêng dự án hiện tại.

## Không thuộc phạm vi
- KHÔNG đổi engine quan hệ hiện có (`touches`/`wikilink`) hay merge `wiki-graph.py` + `build-wiki-graph.py` — đó là nợ riêng đã ghi ở mục "Việc còn nợ" của [[graph-model]], xử lý độc lập.
- KHÔNG viết lại nội dung toàn bộ ~80+ trang wiki hiện có để gắn nhãn tầng ngay lập tức — nếu taxonomy được duyệt, migrate là một bước riêng (giống G4 của council: migrate + validator phải song song, không tuần tự vô kiểm soát).
- KHÔNG bắt buộc con người tự gõ tay field `level` — nếu không suy được bằng máy ở mức đủ tin cậy, đây là lý do để KHÔNG làm, không phải lý do để hạ chuẩn.
- KHÔNG viết lại hay chuyển định dạng hệ skill/rule hiện có để "thành" Protocol/Checklist — chúng ĐÃ LÀ lớp 3, việc cần làm chỉ là link, không phải build lại.
- KHÔNG cố nhồi cả 5 mức của bảng ban đầu (Concept, Knowledge, Framework) thành field riêng — theo comment mới nhất của user, chỉ 3 lớp Facts/Mental-Models/Protocols mới là nền tảng bắt buộc.
- KHÔNG bắt buộc mọi Protocol/Checklist phải có một Mental Model làm trung gian — theo comment thứ hai của user, Mental Model là tầng TUỲ CHỌN; ép buộc nó là nguyên nhân trực tiếp gây phình hệ thống mà user cảnh báo.

## Hướng gợi ý (không bắt buộc)
1. Thử suy `level: fact|mental-model` tự động từ tín hiệu đã có trong graph thay vì tạo trường tay mới: fan-in `depends-on` cao + không có `touches` code trực tiếp ⇒ ứng viên Mental Model; có `touches` code cụ thể + `derives-from` một nguồn duy nhất ⇒ ứng viên Fact. Đo thử trên tập nhỏ trước khi tin.
2. Nếu suy tự động không đủ tin cậy, để agent gợi ý `level` lúc `verify-before-commit` (như G5 làm với `relations:`), người chỉ review — tránh lặp lỗi "cất tay rồi đóng băng" đã xảy ra với `touches`.
3. Thêm một quan hệ mới (cùng họ với `implements`/`touches`) — vd `operationalizes: {to: <skill-id hoặc rule-id>}` — khai được trên CẢ trang Fact lẫn trang Mental Model, trỏ sang skill/rule là Protocol/Checklist của nó. Trang Fact tự khai `operationalizes` thẳng chính là đường tắt — không có luật nào bắt nó phải đi qua một Mental Model trước.
4. View HTML: thêm một chế độ lọc/tô theo 3 lớp bên cạnh chế độ hiện có (theo loại quan hệ) trong `build-wiki-graph.py` — tái dùng renderer sẵn có, không viết engine mới (đúng bài học "nhiều view, không view nào tự dựng model" của [[graph-model]]).
5. Learning path cho newcomer: một truy vấn trên graph hiện có (`depends-on` ngược chiều từ một Mental-Model node, rồi `operationalizes` xuôi chiều tới Protocol) đã có thể sinh thứ tự đọc Fact→Mental-Model→Protocol gợi ý — thử trước khi build UI riêng.

## Tiêu chí HOÀN THÀNH
- Có định nghĩa tường minh (field hoặc quy tắc suy luận) phân biệt được Fact vs Mental Model cho một tập mẫu trang wiki đã chọn.
- Có ít nhất 1 trang Mental Model khai được quan hệ `operationalizes` (hoặc tên tương đương) trỏ đúng tới một skill/rule Protocol/Checklist đang tồn tại thật trong repo.
- Có ít nhất một view HTML render được cả 3 lớp (màu/nhóm/filter), verify bằng cách mở trang và xác nhận bằng mắt trên tập mẫu.
- Có tối thiểu 1 ví dụ "learning path" đầy đủ chuỗi Fact → Mental Model → Protocol sinh ra từ đồ thị quan hệ hiện có (không tay), verify bằng cách người chưa biết chủ đề follow theo và xác nhận thứ tự hợp lý.
- Có tối thiểu 1 ví dụ đường tắt Fact → Protocol trực tiếp (không qua Mental Model) chạy được bằng cùng cơ chế quan hệ — chứng minh chuỗi 3 lớp không phải đường bắt buộc duy nhất.
- Không phá vỡ engine/quan hệ hiện có — `harness/tests/wikigraph-single-source-test.sh` (nếu còn áp dụng) vẫn xanh.

## Assign & lý do
`@Rheinmir` — chủ ledger issue hiện tại của repo này, tất cả issue kiến trúc khác (GH#6, #7, #12...) cùng chủ. Dispatch `Claude` vì việc cần đọc hiểu cả `graph-model`/`wiki-core-relations` và cân nhắc trade-off thiết kế (không phải việc máy móc thuần). Entry `/fdk` vì đây là phát triển CHÍNH cơ chế wiki của framework, không phải feature một dự án downstream.

## Origin
- **Source:** phiên `/raise-issue` 2026-08-01 — user (tự nhận tư duy theo mental model) đưa bảng taxonomy Fact/Concept/Knowledge/Mental-Model/Framework, hỏi wiki nên tái tổ chức thế nào để (a) visualize được mental model, (b) người học mới follow được. **Comment bổ sung #1 cùng phiên:** bảng 5 mức không phải nền tảng — nền tảng thật là chuỗi 3 lớp có thứ tự Facts → Mental Models → Protocols/Checklists. **Comment bổ sung #2:** Mental Model là tầng TUỲ CHỌN, không bắt buộc — phải có đường tắt Fact → Protocol trực tiếp để tránh hệ thống phình ra. Cả hai đã cập nhật vào Bối cảnh/Phạm vi/Không-thuộc-phạm-vi/Hướng gợi ý/Tiêu chí ở trên.
- **Bằng chứng đối chiếu:** `llmwiki/wiki/concepts/graph-model.md`, `llmwiki/wiki/sources/draft/020726-wiki-core-relations.md` (đọc trước khi viết issue này, R7-f).
- **Chưa code, chưa quyết định thiết kế cuối** — issue này CHỈ ghi bối cảnh + phạm vi cho phiên nhận, mở bằng `/fdk` để thiết kế và (nếu cần) chạy `/council` trước khi build, đúng cách [[wiki-core-relations]] đã làm.
