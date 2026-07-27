---
type: draft
title: 020726-wiki-core-relations — đánh giá hệ thống wiki + thiết kế lõi quan hệ, traceability, chống context rot
tags: [proposal, wiki-core, traceability, relations, context-rot, fdk]
timestamp: 2026-07-02
id: 020726-wiki-core-relations
relations:
  - {rel: touches, path: llmwiki/.claude/hooks/wiki_ledger.py}
  - {rel: touches, path: llmwiki/.claude/hooks/post_tool_use.py}
  - {rel: touches, path: llmwiki/.claude/hooks/validators/rel_integrity.py}
  - {rel: touches, path: fdk/tools/wiki-relations.py}
  - {rel: touches, path: fdk/tools/build-wiki-graph.py}
---

# 020726-wiki-core-relations — Từ "queue dữ liệu" thành lõi tri thức có quan hệ

**Type:** concept (promoted)
**Status:** shipped — đủ 6 bước 2026-07-02. Bước 1+2&3: ledger flock (G1 test 8-process pass), migrate 82 trang, validator warn-only. Bước 4-6 (user quyết đẩy sớm, tiêu chí tốc độ): stale-propagation cap=1 (G2 — 9.8ms/lần ghi, chu trình an toàn), skill `/wiki-room` (G3 — depth cap=1, budget, circuit breaker), wiki-graph HTML (13ms build, `llmwiki/html/wiki-graph-{fdk,llmwiki}.html`)
**Tags:** proposal, wiki-core, traceability, output-report
**Proposed:** 2026-07-02

## What
Đánh giá hệ thống llmwiki hiện tại theo 6 tiêu chuẩn tường minh, chỉ ra khoảng trống, và thiết kế "wiki-core v2": wiki không còn là hàng đợi chứa dữ liệu đơn thuần mà là lõi tri thức có **schema quan hệ, ledger thay đổi, validator quan hệ, traceability hai chiều code↔wiki↔phiên, và cơ chế bơm context 3 tầng** để chống context rot.

---

## Phần 1 — Đánh giá hệ thống hiện tại

### 1.1 Tiêu chuẩn đánh giá (chọn khung nào, vì sao)

Không có một chuẩn công nghiệp duy nhất cho "wiki làm memory cho AI agent", nên khung dưới đây được ghép từ ba nguồn chuẩn đã có tên tuổi, mỗi nguồn phụ trách một mặt:

1. **W3C PROV (provenance model)** — chuẩn về truy xuất nguồn gốc: mọi artefact phải trả lời được *cái này sinh ra từ đâu, bởi hoạt động nào, lúc nào, thay thế cái gì*. Đây là gốc cho tiêu chí Provenance và Change lifecycle.
2. **Nguyên tắc knowledge-graph / ontology engineering** (typed relations, referential integrity, no dangling edges) — gốc cho tiêu chí Relational integrity và Queryability.
3. **Thực hành context engineering cho LLM** (progressive disclosure, retrieval eval, index-first) — gốc cho tiêu chí Context efficiency và tiêu chí Human observability (con người phải đọc được thứ máy đọc).

Từ đó ra 6 tiêu chí chấm, mỗi tiêu chí chấm theo 3 mức: ✅ đạt / 🟡 một phần / ❌ thiếu.

### 1.2 Bảng chấm hiện trạng

| # | Tiêu chí | Mức | Bằng chứng trong repo |
|---|----------|-----|----------------------|
| 1 | **Provenance** — mọi trang truy được nguồn | ✅ | `## Origin` bắt buộc (R2, hook chặn thật — vừa chặn tôi ở R9/R16 trong chính phiên này); draft → promote qua `verify-before-commit` có ghi commit SHA |
| 2 | **Change lifecycle** — thêm / sửa / xóa đều có sự kiện, khác phiên vẫn nối được | 🟡 | Thêm mới (ingest) tốt; `log.md` là nhật ký *văn xuôi cho người*, máy không parse được; **sửa** trang không đánh dấu các trang trỏ tới nó thành stale; **xóa** không có tombstone — xóa file là mất dấu, link `[[...]]` thành treo |
| 3 | **Relational integrity** — quan hệ có kiểu, được validate | ❌ | `[[wikilink]]` chỉ là chuỗi vô kiểu (không phân biệt *implements* / *supersedes* / *touches-code*); lint chạy định kỳ theo "cảm giác stale", không phải validator chặn; không có kiểm tra link treo tự động khi ghi |
| 4 | **Queryability** — hỏi có cấu trúc, không chỉ grep | 🟡 | Skill `query` + force-query (ADR-009) + code-graph MCP cho code; nhưng wiki bản thân không query được theo quan hệ ("trang nào bị ảnh hưởng nếu tôi sửa X?" — hiện không trả lời được bằng máy) |
| 5 | **Context efficiency** — bơm đủ mà không rót thừa, có đường "mở thêm room" | 🟡 | Index 1 dòng/trang + orientation hook + opt-in `/fdk` (ADR-004) là đúng hướng; nhưng chưa có *quy ước 3 tầng* tường minh, chưa có cơ chế chuẩn "context rot rồi → mở room nạp chi tiết" (hiện là ứng biến bằng Explore/subagent tùy phiên) |
| 6 | **Human observability** — người xem được toàn cảnh quan hệ + lịch sử | 🟡 | `build-health-dashboard.py`, `build-docs-index.py`, overstack.html có sẵn nền; nhưng không có view *đồ thị quan hệ* và *timeline thay đổi* — người muốn biết "trang này ai sửa, phiên nào, kéo theo gì" phải đọc tay log.md |

**Kết luận đánh giá:** trụ Provenance đã chặt (điểm mạnh nhất, nhờ harness chặn thật). Ba khoảng trống làm wiki vẫn là "queue": (a) quan hệ vô kiểu và không được validate, (b) sửa/xóa không phát sinh sự kiện máy-đọc-được nên không lan truyền được ảnh hưởng giữa các phiên, (c) chưa có tầng hiển thị quan hệ cho người.

### 1.3 Quy trình adapt fdk hiện tại (trả lời "chưa hiểu rõ quy trình")

Chuỗi hiện hành, viết tường minh:

```
raw/ có file mới ──/ingest──▶ distill thành trang OKF (concepts/entities/sources)
                                   │  bắt buộc: frontmatter + ## Origin + [[links]]
ý tưởng/feature ──/propose──▶ draft trong sources/draft/ (status: proposed) ──▶ DỪNG chờ duyệt
duyệt ──▶ code (impact-check → safe-change) ──▶ /verify-before-commit
                                   │  gate: typecheck/lint/smoke + promote draft → wiki chính thức
                                   ▼  ghi commit SHA vào ## Origin, cập nhật index.md + log.md
định kỳ ──/lint──▶ quét orphan/stale ; /wikieval ──▶ eval truy hồi golden
framework thay đổi ──/sync-template + /health-check──▶ đồng bộ chuẩn, chống drift
```

Điểm yếu của chuỗi này đúng như nhận xét: mọi mắt xích đều ghi **văn bản cho người**, không mắt xích nào ghi **sự kiện có cấu trúc cho máy** — nên không thể validate quan hệ hay trace tự động.

---

## Phần 2 — Thiết kế wiki-core v2

Nguyên tắc thiết kế: **không thay nền markdown** (giữ tính travel/clone-sống-sót của wiki), chỉ thêm 4 lớp mỏng lên trên. Mỗi lớp là một đơn vị độc lập (nguyên tắc #4 Modular), chảy về chuẩn chung (#3), và là hậu cần (#7) — đúng nhóm "ăn lãi kép" của fdk-dev-strategy.

### 2.1 Lớp 1 — Schema quan hệ có kiểu (frontmatter mở rộng)

Frontmatter OKF thêm hai khóa, vẫn là YAML thuần:

```yaml
---
type: concept
title: ...
id: fdk-dev-strategy            # slug bất biến, đổi tên file không gãy quan hệ
relations:
  - {rel: implements, to: adr-004}        # trang này hiện thực quyết định nào
  - {rel: supersedes, to: old-strategy}   # thay thế trang nào (chuỗi version)
  - {rel: touches, path: fdk/tools/artifacts.py}  # chạm file code nào
  - {rel: derives-from, to: raw/fdk-stragegy.md}  # distill từ nguồn nào
timestamp: 2026-07-02
---
```

Bộ kiểu quan hệ tối thiểu (đủ dùng, không phát minh ontology to): `implements` · `supersedes` · `touches` (wiki→code) · `derives-from` · `depends-on` · `contradicts` (lint dùng để báo mâu thuẫn). `[[wikilink]]` trong thân bài vẫn giữ — nó là quan hệ mềm "liên quan", còn `relations:` là quan hệ cứng được validate.

### 2.2 Lớp 2 — Ledger sự kiện (máy đọc), log.md thành view

File mới `wiki/ledger.jsonl`, **append-only**, mỗi thao tác wiki/code ghi một dòng JSON:

```json
{"ts":"2026-07-02T14:02:11","session":"c0fd85d2","action":"modify",
 "target":"concepts/fdk-dev-strategy.md","commit":"49d2361",
 "touched_code":["fdk/tools/artifacts.py"],"invalidates":["concepts/old-strategy"]}
```

- `action` ∈ `add` | `modify` | `delete` | `promote` | `stale-mark`.
- Hook `post_tool_use` (đã có sẵn hạ tầng) tự append khi Write/Edit chạm `wiki/` — không nhờ model tự giác.
- **Xóa = tombstone**: file không bị xóa cứng; đổi `type: tombstone`, giữ Origin + lý do + trỏ `superseded-by`. Validator chặn link trỏ tới tombstone mà không qua supersedes.
- **Sửa khác phiên**: sự kiện `modify` kèm commit SHA; script lan truyền đánh `stale-mark` lên mọi trang có `relations` trỏ tới target — phiên sau mở trang stale sẽ thấy cờ ngay trong orientation.
- `log.md` giữ nguyên cho người đọc, nhưng từ nay **sinh từ ledger** (một view), hết cảnh hai nguồn lệch nhau.

### 2.3 Lớp 3 — Validator quan hệ (chặn thật, tầng hook + CI)

Mở rộng bộ validator sẵn có (cùng chỗ với R2/R5/R9) thêm 4 luật mới:

| Luật | Chặn gì |
|------|---------|
| R-rel-1 dangling | `relations.to` / `[[link]]` trỏ tới id không tồn tại và không phải tombstone |
| R-rel-2 code-drift | `touches.path` trỏ tới file không còn tồn tại (đối chiếu code-graph) → buộc cập nhật hoặc tombstone |
| R-rel-3 supersedes-chain | trang bị supersede vẫn được trang khác trỏ `depends-on` → báo đỏ |
| R-rel-4 ledger-gap | có commit chạm `wiki/` mà không có dòng ledger tương ứng (CI so git log ↔ ledger) |

Trả lời trực tiếp "thay đổi validate bằng quan hệ": mọi Write/Edit vào wiki đi qua R-rel-1..3 tại hook (nhanh, cục bộ), CI chạy R-rel-4 + toàn cục (sàn enforcement thật, đúng harness-enforcement-floor).

### 2.4 Lớp 4 — Context 3 tầng, "mở thêm room" khi context rot

Quy ước hóa thứ đang làm ứng biến thành cơ chế đặt tên được:

- **Tier A — luôn bơm (≤ ~2KB):** index 1 dòng/trang + cờ stale + 5 sự kiện ledger gần nhất. Đây là "bản đồ", không phải nội dung.
- **Tier B — bơm theo truy vấn:** trang OKF đầy đủ của đúng các node liên quan (đi theo `relations` 1 bước từ chủ đề đang làm). Force-query hiện có nâng cấp: trả kèm hàng xóm quan hệ, không chỉ trang trúng keyword.
- **Tier C — room:** khi phiên chính đã rot (context dài, tóm tắt nhiều), mở **subagent Explore/general-purpose** với brief = Tier A + danh sách id cần đào; room nạp Tier B/C đầy đủ, trả về kết luận nén. Room là chỗ "nạp chi tiết hơn tất cả" mà không phá phiên chính. Quy ước này viết thành skill nhỏ (`/wiki-room`) để gọi được chủ động thay vì tùy hứng.

Chống rot không phải "bơm ít đi" mà là **bơm đúng tầng**: phiên chính giữ bản đồ, chi tiết sống trong room dùng-xong-bỏ.

### 2.5 Hiển thị cho người

Tận dụng nền build sẵn có (`build-docs-index.py`, health-dashboard, theme docs-site-macos), thêm một trang HTML `wiki-graph`:

- **Đồ thị quan hệ** (node = trang, cạnh tô màu theo kiểu quan hệ, node stale/tombstone đánh dấu riêng) — dùng đúng kỹ thuật mind map bezier + draggable node đã có trong skill, không thêm thư viện.
- **Timeline ledger**: dòng thời gian add/modify/delete theo phiên + commit, click một sự kiện → thấy trang, diff link, các trang bị stale theo.
- **Trang chi tiết**: mỗi node hiển thị Origin, chuỗi supersedes, danh sách file code touches, và các phiên đã chạm vào — đây là câu trả lời "traceability hiển thị lên cho người đầy đủ".

### 2.6 Roadmap tối thiểu (để thành "1 trụ mạnh")

| Bước | Việc | Ăn tiêu chí |
|------|------|-------------|
| 1 | Ledger JSONL + hook auto-append + tombstone thay xóa cứng | #2 lifecycle |
| 2 | Frontmatter `id` + `relations` cho ~18 trang concept hiện có (migrate bằng script, không tay) | #3 integrity |
| 3 | 4 validator R-rel (hook + CI) | #3, #4 |
| 4 | Stale-propagation + nâng force-query trả hàng xóm quan hệ | #4, #5 |
| 5 | Quy ước 3 tầng + skill `/wiki-room` | #5 |
| 6 | Trang HTML wiki-graph + timeline | #6 |

Bước 1–3 là lõi chặt ("tối thiểu để trụ mạnh"); 4–6 là phần đọc-ra-ngoài và cho người. Mỗi bước là một proposal/commit độc lập, đi đúng vòng propose → gate → dispatch.

---

## Phần 3 — Council review (5 phản biện, blind peer-rank)

Trước khi hiện thực, proposal được đưa qua `/council` — 5 seat mang lăng kính đối trọng nhau (Taleb↔Ilya Sutskever, Munger↔Kahneman, cộng Marcus Aurelius) phản biện độc lập, 3 judge xếp hạng MÙ (không biết tác giả), aggregate bằng mean-rank xác định (seed 42, `harness/scripts/council.py`). Kết quả đồng thuận rất mạnh — winner (Ilya) đạt mean-rank 1.0 tuyệt đối, cả 3 judge xếp #1 giống nhau.

### 3.1 Bảng đồng thuận

| Hạng | Seat | Mean rank | Nhận xét cốt lõi |
|------|------|-----------|-------------------|
| 1 | Ilya Sutskever | 1.0 | Thiết kế thiếu 2 giới hạn cứng khi scale: concurrency control cho ledger, depth-cap cho room; validator chỉ bắt cú pháp, không bắt ngữ nghĩa |
| 2 | Nassim Taleb | 2.0 | Lan truyền (stale-propagation, room lồng) không có "giảm chấn" — chính cơ chế chống rot có thể tự thành nguồn rot mới ở tải cao |
| 3 | Charlie Munger | 3.33 | Quy mô giải pháp (6 hệ thống con) vượt quy mô người vận hành (1 người + agent) — rủi ro thật là bị bỏ hoang, không phải bị sai |
| 4 | Marcus Aurelius | 4.0 | Bước 1-3 tự-cưỡng-chế (bền); bước 4-6 phụ thuộc hành vi con người tương lai — nên ghi rõ là giới hạn chấp nhận, không phải tính năng chắc chắn xong |
| 5 | Daniel Kahneman | 4.67 | Đúng về mặt bias-audit (bảng 6 tiêu chí có confirmation bias, tốc độ sinh văn bản là "System 1 giả trang System 2") nhưng judge đánh giá đây là phản biện *meta*, ít hành động cụ thể hơn 4 seat kia cho quyết định roadmap kế tiếp |

**Điểm bất đồng lớn nhất (dissent):** Aurelius bị 3 judge xếp lệch nhau nhiều nhất (hạng 3/5/4, variance 0.667) — một judge coi "phân định kiểm soát rõ ràng" là đóng góp hạng nhì, hai judge khác xếp thấp hơn vì cho rằng nó ít cụ thể/hành động hơn Taleb/Munger. Cách giải quyết: không lấy trung bình che đi bất đồng — cả hai phía đều đúng một phần, nên chairman giữ nguyên khuyến nghị cốt lõi của Aurelius (tách rõ "lõi tự-cưỡng-chế" khỏi "lớp phụ thuộc hành vi") nhưng đặt nó ở vai trò *khung phân loại* cho roadmap, không phải một rủi ro kỹ thuật độc lập ngang hàng Ilya/Taleb.

### 3.2 Chairman synthesis — verdict cuối

**Verdict: proposal đúng hướng chẩn đoán nhưng SAI LIỀU LƯỢNG — hiện thực phải thu hẹp phạm vi và thêm 3 guardrail cứng trước khi build, không phải sau.**

Ba seat kỹ thuật (Ilya #1, Taleb #2) hội tụ vào đúng MỘT lớp: **Lớp 2 (ledger + stale-propagation) và Lớp 4 (room)** là nơi rủi ro thật nằm — không phải vì ý tưởng sai, mà vì thiết kế gốc thiếu giới hạn cứng (bound) ở đúng hai chỗ có khả năng khuếch đại: ghi ledger đồng thời (concurrency) và đệ quy room (depth). Đây là điểm hội tụ mạnh nhất của cả hội đồng — không phải ý kiến riêng lẻ.

Munger (#3) đúng ở một trục khác, không mâu thuẫn với Ilya/Taleb mà bổ sung: ngay cả khi 2 guardrail trên được thêm, quy mô 6-bước vẫn có thể vượt sức một người duy trì. Cách giải quyết không phải bỏ ý tưởng mà **nén roadmap**: gộp bước 2 (migrate relations) và bước 3 (validator) làm SONG SONG thay vì tuần tự — đúng như Taleb cảnh báo (migrate trước validator ổn định tạo rác lịch sử không sửa được), và để agent tự suy `relations:` lúc `verify-before-commit` thay vì bắt người/agent nhớ gõ tay — đúng đề xuất né-giết-proposal #1 của Munger.

Aurelius (#4) đúng về ranh giới nhưng hội đồng đánh giá đây là *cách phân loại*, không phải *rủi ro mới*: áp dụng bằng cách ghi rõ trong roadmap rằng bước 5-6 (`/wiki-room`, HTML graph) là "tiện ích phụ thuộc hành vi con người", KHÔNG cam kết cùng mức "xong = xong" như bước 1-3.

Kahneman (#5) đúng về bias nhưng ít actionable nhất theo đánh giá judge — hội đồng vẫn giữ 1 hành động cụ thể duy nhất từ seat này: **bỏ dòng tự dẫn chứng "vừa chặn tôi ở R9/R16" khỏi lý do chấm ✅ Provenance** trong Phần 1 — đó đúng là mẫu N=1 thiên vị, thay bằng bằng chứng khách quan hơn (số lượng ADR đã chốt qua R13, số lần R2/R9 chặn trong lịch sử ledger nếu có).

### 3.3 Thay đổi bắt buộc vào thiết kế (từ hội đồng, không phải tùy chọn)

| # | Thay đổi | Từ seat | Áp vào |
|---|----------|---------|--------|
| G1 | `ledger.jsonl` cần concurrency control (file lock, hoặc shard-per-session rồi merge có thứ tự) — không coi Bước 1 là "xong" nếu chưa test ghi song song | Ilya | 2.2 |
| G2 | `stale-propagation` giới hạn N=1 bước lan truyền (không đệ quy vô hạn) + khử chu trình tường minh nếu `relations` tạo vòng | Ilya, Taleb | 2.2 |
| G3 | `/wiki-room` (Tier C) cấm room mở room con (depth cap = 1), có budget token/node cứng, circuit breaker trả kết quả cắt ngắn thay vì tiếp tục đào | Ilya, Taleb | 2.4 |
| G4 | Bước 2 (migrate relations) và Bước 3 (validator, kể cả ở chế độ warn-only) phải triển khai SONG SONG, không tuần tự — tránh ghi rác quan hệ vào ledger append-only trước khi có ai kiểm tra | Taleb | Roadmap |
| G5 | `relations:` trong frontmatter do agent tự suy và điền lúc `verify-before-commit`, người chỉ review — không bắt gõ tay mỗi lần ghi wiki | Munger | 2.1 |
| G6 | Bước 4 (stale-propagation) và Bước 5 (`/wiki-room`) không cùng "hạng" với bước 1-3 trong bảng roadmap — đánh dấu riêng là "phụ thuộc hành vi, chấp nhận có thể không xảy ra", không cam kết như tính năng chắc chắn | Aurelius | Roadmap |
| G7 | Validator R-rel chỉ đảm bảo *toàn vẹn tham chiếu* (referential integrity), không đảm bảo *đúng ngữ nghĩa* — ghi rõ giới hạn này trong Notes, đừng để ai hiểu lầm "validator xanh = quan hệ đúng nghĩa" | Ilya, Aurelius | 2.3 + Notes |

### 3.4 Roadmap đã sửa theo council (thay thế bảng 2.6 gốc)

| Bước | Việc | Guardrail đi kèm |
|------|------|-------------------|
| 1 | Ledger JSONL + hook auto-append + tombstone + **concurrency control (G1)** | Test ghi song song trước khi coi "xong" |
| 2+3 (song song) | Frontmatter `id`+`relations` (auto-suy lúc verify-before-commit, G5) **CÙNG LÚC với** validator R-rel-1..3 ở chế độ warn-only | G4: không migrate hàng loạt trước khi validator tồn tại |
| 4 | Stale-propagation **giới hạn N=1 bước** (G2) — KHÔNG phải lan vô hạn như bản gốc | Đánh dấu "phụ thuộc hành vi một phần" (G6) |
| 5 | `/wiki-room` với **depth cap=1, budget cứng, circuit breaker** (G3) | Đánh dấu rõ "tiện ích, không phải nghĩa vụ" (G6) |
| 6 | Trang HTML wiki-graph + timeline | Không đổi — thấp rủi ro nhất, làm sau cùng |

**Kết luận chairman:** duyệt hiện thực Bước 1 và Bước 2+3 (song song) trước; Bước 4-6 chờ đánh giá lại sau khi 1-3 chạy ổn định ít nhất vài tuần thực tế (đúng đề xuất "chạy thử 4-6 tuần trước khi build tiếp" của Munger) — không build hết 6 bước cùng lúc như roadmap gốc.

Transcript đầy đủ (5 câu trả lời gốc, thứ tự trình bày chống thiên kiến vị trí, 3 ranking mù, mean-rank, dissent table): `llmwiki/wiki/sources/draft/020726-council-transcript-wiki-core.json`. Báo cáo HTML: `llmwiki/html/council/council-report-005-seed42.html`.

## Files
| File | Action |
|------|--------|
| `llmwiki/wiki/sources/draft/020726-wiki-core-relations.md` | created (document này), sửa thêm Phần 3 sau council |
| `llmwiki/wiki/sources/draft/020726-council-transcript-wiki-core.json` | created (transcript council, seed 42) |
| `llmwiki/html/council/council-report-005-seed42.html` | created (báo cáo HTML tự sinh bởi council.py) |
| `llmwiki/wiki/index.md` | modified |
| `llmwiki/wiki/log.md` | modified |

## Notes
- Đây là **proposal + đánh giá**, chưa code — theo rule dev-loop: dừng chờ duyệt trước khi hiện thực.
- Liên quan: `fdk-dev-strategy` (#3/#4/#7 ăn lãi kép), `harness-enforcement-floor`, [[rule-registry]], `query-retrieval-eval`.

## Kiểm chứng NGOÀI-MẪU (2026-07-03 — benchmark self-index)
Council seed42 chê bộ test cũ "tự chọn đề thi (ludic fallacy)". Đáp lại: để **council ra đề** → dựng app **ngoài-mẫu** (TS plugin-host, ground-truth niêm phong hash) → chạy **engine thật** `build-wiki-graph.py` → chấm mù bằng cơ chế benchmark chuẩn ngành (edge P/R/F1 + hallucination/omission-rate + negative-control; áp từ ContextBench/Unified-KG-Benchmark qua `/last30days`).

**Kết quả (graph-builder đơn lẻ):** semantic-relation F1 **0.842** (P .889/R .8), hallucination .125, negative PASS. Phân tích năng lực:
- ✅ **Mạnh:** đọc đúng 5/5 quan hệ khai tường minh (derives-from/supersedes/contradicts/implements/depends-on); **không** đối-xứng-hóa contradicts; **không** bịa cạnh negative; **không** bịa implements cho YAML hỏng.
- ❌ **Giòn (3 defect → [[failure-flywheel]]):** (1) `enrich_code` chỉ parse `.py` → **mù imports/touches code TS**; (2) graph-builder thiếu cờ chu trình + không quarantine YAML hỏng; (3) `WIKILINK_RE` không strip code-fence → false-positive `[[NotALink]]`.

**Kết luận:** xác nhận engine **robust ở mặt thiết kế, chưa anti-fragile** ở đuôi ngoài-mẫu. ⚠️ Phạm vi: mới test `build-wiki-graph.py` đơn lẻ; hook auto-touches + validator `rel_integrity` + code-graph MCP **chưa exercise** — cần run tích hợp mới kết luận toàn hệ. Report: `llmwiki/html/030726-self-index-benchmark-report.html`. Đề: `council-report-010-seed42.html`. Proposal: [[020726-council-chon-de-thi-self-index]].

## Origin
- **Source:** yêu cầu user 2026-07-02 (/goal — đánh giá hệ thống, lõi wiki quan hệ + traceability + chống context rot) + khảo sát repo (hooks, validators, fdk/tools, wiki structure)
- **Draft:** `wiki/sources/draft/020726-wiki-core-relations.md`
- **Commit:** `d4d8b90` — feat(wiki-core): ledger sự kiện + relations có kiểu + validator R-rel (bước 1+2&3)
- **Date promoted:** 2026-07-02
