---
type: draft
title: "Graph stack — bài học từ thread Grapuco: sửa 2, đo 3, nháp 1"
status: proposed
tags: [graph, wiki-sync, code-graph, retrieval-eval, persona, room, grower, prototyper, maintainer]
timestamp: 2026-07-19
task: T-260719-02
---

# 190726-graph-lessons-grapuco

**Status:** implemented (2026-07-20)
**Proposed:** 2026-07-19
**Task:** `T-260719-02`
**Sequence diagram:** [190726-graph-lessons-grapuco-seq.html](../../../html/190726-graph-lessons-grapuco-seq.html)

## Request (một câu)

Đọc thread tranh luận cộng đồng về Grapuco (một sản phẩm context-management/graph), rút ra những gì graph stack của overstack học được, qua ba lens persona Grower · Prototyper · Maintainer, và chốt thành một danh sách việc phải làm.

## Context

Đã force-query wiki trước khi draft. Các trang chi phối proposal này:

- **[[010726-query-retrieval-eval]]** (`fdk/wiki/concepts/query-retrieval-eval.md`) — trang quan trọng nhất ở đây. Ta **đã có sẵn bộ đo truy hồi**: `harness/scripts/query-log.py` (telemetry JSONL mỗi query), `harness/scripts/retrieval-eval.py` (hit@k + token, so baseline `harness/metrics/retrieval-baseline.json`, `--check` exit 2 khi tụt), goldens ở `llmwiki/wiki/sources/evals/retrieval/`. Nâng L0→L1 giữ hit@5 7/10 mà token giảm 272k→95k (−65%), và eval đã **chặn 3 lần thử L1 tồi**. Nghĩa là mọi task "đo" trong proposal này **không phải xây mới**, chỉ thêm golden/nhánh đo vào bộ đã chạy.
- **ADR-004-framework-dev-context-opt-in** (`fdk/wiki/sources/adr/ADR-004-framework-dev-context-opt-in.md`) — beneficiary phải khai rõ; framework-dev context là opt-in. Proposal này là phiên `/fdk` (đánh giá chính framework) nên dùng đúng ngoại lệ đó, nhưng SC vẫn phải đo trên dự án đích.
- **ADR-009-session-orientation-autoindex-forcequery** (`fdk/wiki/sources/adr/ADR-009-session-orientation-autoindex-forcequery.md`) — force-query là nơi `query` được gọi; telemetry đo chính đường đó. Đây là lý do vá `/query` (T1) chạm được tới hầu hết lượt đọc wiki.
- **ADR-015-boris-archetypes-into-template** (`fdk/wiki/sources/adr/ADR-015-boris-archetypes-into-template.md`) + `harness/archetypes.config.yaml` — 6 persona (`llmwiki/personas/*.md`) là posture dispatch; file config còn `verified: false` (routing CLI/model theo archetype là best-guess chưa đo).
- **[[wiki-core-relations]]** — quan hệ lõi của wiki, nền cho `wiki-graph.py`.
- **150726-unknown-ledger** (archived) — cơ chế ghi nợ `U-NN`, hiện ở `/lint`, không chặn cổng.
- Mã nguồn đã đọc: `harness/scripts/wiki-sync.py` (neo `.last-sync.json`, cổng no-op tất định 0 token, exit 3 = drift), `harness/scripts/wiki-graph.py` (đồ thị in-memory từ `[[wikilink]]`, **không embedding**), `harness/scripts/archetype.py` (chỉ resolve/dispatch — **không có handoff**), `skills/council/SKILL.md` (đã hỗ trợ ghế persona: `roster --personas …`, thư viện 18 persona).
- Nguồn ngoài: `llmwiki/wiki/draft/grapuco-discuss.md` — thread cộng đồng, 9 người phản biện.

**Phát hiện nền tảng khi đọc code:** `grep -n "stale" skills/query/SKILL.md` → **0 kết quả**. Cờ `code-drift` do `wiki-sync` ghi vào `stale.json` chỉ được tiêu thụ ở `/lint`. Đường **đọc** không hề biết tới nó.

## Ba lens trong room

### GROWER (`/grow` — lặp theo dữ liệu dùng thật)

Phần vendor tự nói là marketing claim, không phải tín hiệu. Thứ đáng đọc là **phản đối**, vì mỗi phản đối là một giả thuyết churn. Thread hội tụ về 4 nhóm:

1. **"Model đã đủ giỏi đọc repo"** — ba người nói độc lập (Kenzo Pham, Steven Lee, Đinh Chương). Ba tín hiệu độc lập cùng hướng là mức bằng chứng cao nhất thread này cho được. Nhắm thẳng vào `code-graph` MCP (AST/call-graph), **không** chạm `llmwiki` (ADR/decisions). → phải **đo**, không được cãi bằng suy đoán.
2. **Chi phí embedding** — Đinh Chương: *"hễ có commit mới hoặc vài docs ta phải embedding vào nhánh graph, khá tốn thời gian và token"*. Ta đã né sẵn về mặt kiến trúc (in-memory, 0 token, cổng no-op) nhưng **chưa có con số** → lợi thế không đo được không phải lợi thế.
3. **"Graph thành source-of-truth → feed knowledge sai → hallucinate"** — đây là **gap thật** của ta, xem phát hiện ở `## Context`.
4. **"Business logic mới là phần khó"** + câu hỏi kiểm chứng của Đinh Chương *"thành viên mới có nắm được toàn bộ kiến thức đó không?"* → biến thành golden đo được.

### PROTOTYPER (`/proto` — đẻ ý tưởng, phần lớn không ship)

Ranh giới nghề: không productionize, không yêu ý tưởng nào. Hai hướng nháp rút từ thread:

- **Kịch bản gốc của thread — FE/BE hai repo, hai agent — ta chưa phục vụ được.** `impact-check` hiện chỉ chạy trong MỘT repo. Nhưng `code-graph` MCP đã có `list_projects` — nghĩa là nối hai project để hỏi "đổi schema BE thì FE chạm gì" là một **nháp rẻ**, không phải dự án. Đây là hướng đáng bắn thử. Nếu không ra gì thì vứt, đó là điểm.
- **Hướng thứ hai đã bị chính Prototyper loại:** xây "Context Hub" tập trung như Grapuco. Loại không phải vì khó, mà vì thread đã cho sẵn hai vết thương của hướng đó (chi phí embedding, hallucinate khi graph là source-of-truth). Bắn một prototype vào hướng đã biết là hố thì không phải khám phá.

Bàn giao cho Builder: đúng **một** hướng (cross-repo impact), có timebox.

### MAINTAINER (`/maintain` — an toàn, tin cậy, rẻ ở scale)

Không chạy theo feature mới. Ba điều kiện dán vào việc của người khác:

- **T1 phải fail-open tuyệt đối.** `stale.json` hỏng/thiếu/khoá → `/query` vẫn trả lời bình thường, tuyệt đối không chặn. Cùng kỷ luật hook đang áp: hook fail-open, CLI/CI thì lỗi phải nổi. Một cổng cảnh báo làm chết đường đọc còn tệ hơn không có cổng.
- **Cảnh báo bị nhờn là cảnh báo chết.** Nếu tỉ lệ cảnh báo giả cao, agent học cách phớt lờ và ta mất luôn tín hiệu thật. Tỉ lệ false-positive là **guardrail metric**, không phải chi tiết triển khai.
- **Trần eval là trần cứng.** `retrieval-eval` **từ chối chạy khi >30 golden** (hard-cap đã có, chống mạ-vàng-eval). T2 và T4 cùng thêm golden → phải đếm trước, không được đụng trần rồi mới biết.

### Hở thứ sáu — do user nêu trong room

Sáu file `llmwiki/personas/*.md` đều có mục `## DON'T (ranh giới)` chỉ đích danh persona khác (*"đó là Builder"*, *"đó là Maintainer"*) và một mục `## Stop khi`. Nhưng **không có cơ chế nào để gọi persona đó vào room, cũng không có chỗ nào ghi lại ý tưởng đang bị bỏ**. `archetype.py` chỉ `resolve`/`dispatch` — không có handoff.

Hệ quả: ranh giới persona hiện là **ngõ cụt**. Prototyper nói "không productionize, đó là Builder" xong ý tưởng bốc hơi. Đúng như user mô tả: càng nhiều ý thì càng rơi.

Điều may là **hai nửa cơ chế đã có sẵn**, chỉ chưa nối: `/raise-issue` ghi issue có owner vào ledger local (cho việc hoãn lại), và `/council` đã hỗ trợ ghế persona `roster --personas …` (cho việc gọi vào room ngay). Cái thiếu là 6 persona archetype nằm ở một thư viện **khác** với 18 persona của council — hai sổ hộ khẩu, không ai gọi được ai.

## Global constraints

Chép nguyên văn giá trị thật từ wiki/ADR/policy — mọi task ngầm mang theo section này:

- **Wiki entry chỉ tạo SAU khi code đã commit** — không tạo trong lúc proposal/planning (CLAUDE.md).
- **Mọi file wiki phải có `## Origin`** — nguồn luôn truy được.
- **Luôn cập nhật `llmwiki/wiki/index.md`** khi thêm/bớt file wiki; **luôn append `llmwiki/wiki/log.md`** sau mỗi thao tác.
- **File wiki không được nằm ở `wiki/` root** — chỉ `concepts/`, `entities/`, `sources/`, `draft/`, `architecture/`, `tours/` (R5 validator gác).
- **`retrieval-eval` từ chối chạy khi >30 golden** (hard-cap, exit ≠ 0) — chống mạ vàng eval, [[010726-query-retrieval-eval]].
- **Hook fail-open; CLI/CI thì lỗi bất ngờ phải nổi (exit ≠ 0)** — quy ước đã ghi ngay trong docstring `wiki-sync.py`.
- **Skill canonical `skills/` ↔ mirror `llmwiki/skills/` phải byte-identical**, đồng bộ qua `sync-skills`; `medic` gác parity.
- **Commit CẤM mọi AI-attribution** (`Co-Authored-By`, "Generated with…") — R15 chặn cứng, ADR-016-no-ai-attribution-in-commits (`fdk/wiki/sources/adr/ADR-016-no-ai-attribution-in-commits.md`).
- **`medic --ci` phải xanh trước push**; commit-msg hook R13 có bug đệ quy đã biết → chạy medic thủ công rồi `commit --no-verify` khi cần.
- **Beneficiary khai rõ ở mọi kết luận** (ADR-004): proposal này là phiên `/fdk` nên được phép đánh giá chính framework, nhưng **SC phải đo trên dự án đích**.

## Non-goals

Cố ý **KHÔNG** làm:

- **KHÔNG xây "Context Hub" tập trung** kiểu Grapuco Hub — không quản lý version/phân quyền context xuyên nhiều phần mềm, không phân phối context tới nhiều agent qua một server.
- **KHÔNG đưa embedding/vector vào graph.** `wiki-graph` giữ nguyên in-memory từ `[[wikilink]]`, 0 token. Chính chi phí embedding là vết thương thread đã chỉ ra.
- **KHÔNG gỡ `code-graph` trong đợt này** — T2 chỉ *đo* để có số; quyết định giữ/bỏ/đặt-ngưỡng là đợt sau, dựa trên số đó.
- **KHÔNG làm cảnh báo stale thành cổng chặn.** Chỉ cảnh báo, không block (xem Assumptions).
- **KHÔNG viết persona mới**, không sửa `verified: false` trong `archetypes.config.yaml` (nợ đó cần đo dispatch thật, ngoài phạm vi).
- **KHÔNG productionize nháp cross-repo (T5)** — nó là nháp, ra quyết định go/no-go rồi dừng.

## Approaches

### Phương án A — Vá điểm theo ba tầng: sửa 2, đo 3, nháp 1 ✅ CHỌN

Chia việc theo *độ chắc của bằng chứng*: chỗ nào đã chứng minh là lỗ thì **sửa**; chỗ nào mới là giả thuyết thì **đo** trước khi động vào; chỗ nào là hướng mới thì **nháp** có timebox.

- Ưu: mỗi việc tương xứng với bằng chứng đang có; hai việc sửa đều là diff nhỏ dùng lại cơ chế sẵn có; không cam kết kiến trúc nào trước khi có số.
- Nhược: không cho ra một "sản phẩm" nghe kêu; sáu việc rời rạc cần kỷ luật để không bỏ dở.

### Phương án B — Xây Context Hub như Grapuco

Dựng một lớp context tập trung: versioned, phân quyền, phân phối cho nhiều repo/agent, graph có embedding làm source-of-truth.

- Ưu: giải đúng kịch bản FE/BE của thread ở quy mô doanh nghiệp; là hướng vendor đang đặt cược.
- Nhược: **thừa hưởng trọn hai vết thương thread đã chỉ** — chi phí embedding mỗi commit, và hallucinate khi graph thành source-of-truth. Ta lại đang thắng đúng hai điểm đó nhờ kiến trúc 0-token. Đổi thế mạnh lấy thế yếu của đối thủ là nước đi ngược.
- **Loại.**

### Phương án C — Chỉ sửa T1 + T6, bỏ hết phần đo

Làm đúng hai lỗ đã chứng minh, không đo gì.

- Ưu: diff nhỏ nhất, xong trong một phiên.
- Nhược: bỏ qua phản đối mạnh nhất thread (ba người độc lập nói `code-graph` hết cần). Không đo thì sáu tháng nữa vẫn cãi bằng niềm tin, và ta có sẵn `retrieval-eval` rồi — không đo là lãng phí bộ đồ nghề đã dựng.
- **Loại,** nhưng giữ tinh thần: T1 + T6 là hai việc **ưu tiên cao nhất**, ba việc đo có thể chạy song song/sau.

**Chốt A** vì nó là phương án duy nhất khớp bằng chứng: hai lỗ đã chứng minh thì sửa ngay, ba giả thuyết thì đo bằng bộ đo đã chạy sẵn, một hướng mới thì nháp rẻ rồi quyết. Và A giữ nguyên thứ đang thắng (0-token, không embedding) thay vì đánh đổi nó.

## Requirements (FR)

- **FR-001**: Đường **đọc** wiki PHẢI cảnh báo khi trang trả về đang mang cờ `code-drift` trong `stale.json`, thay vì chỉ cảnh báo ở `/lint`.
- **FR-002**: Cảnh báo ở FR-001 PHẢI fail-open — `stale.json` thiếu, hỏng, hoặc không đọc được thì `/query` vẫn trả lời bình thường, không lỗi, không chặn.
- **FR-003**: Hệ thống PHẢI đo được đóng góp thật của `code-graph` vào việc định vị code, bằng nhánh có-và-không-có trên cùng bộ golden, kết quả ghi thành số so được với baseline.
- **FR-004**: Hệ thống PHẢI ghi lại chi phí mỗi lần đồng bộ wiki (thời gian, token nếu có) để chứng minh — hoặc bác bỏ — lợi thế "0 token" theo thời gian.
- **FR-005**: Bộ eval PHẢI có golden dạng "người mới vào dự án": một agent không có context nào ngoài wiki phải chạm đúng file và không vi phạm business rule đã ghi trong ADR.
- **FR-006**: Khi một persona chạm ranh giới nghề của mình, ý tưởng bị bỏ PHẢI được ghi lại kèm persona chủ đích, thay vì biến mất.
- **FR-007**: Một persona PHẢI gọi được persona khác vào room ngay trong phiên, dùng cơ chế ghế sẵn có, không phải copy-paste posture bằng tay.
- **FR-008**: Mọi golden thêm mới PHẢI được đếm trước để tổng không vượt trần 30 của `retrieval-eval`.

## Plan

- [x] **T1 — Nối `stale.json` sang đường đọc.** `/query` đọc `stale.json`; trang nào mang cờ `code-drift` thì output kèm một dòng cảnh báo nêu file code đã đổi. Fail-open tuyệt đối. Đồng bộ canonical ↔ mirror. *(FR-001, FR-002)*
- [x] **T2 — Đo `code-graph` có đáng không.** Chạy `retrieval-eval` hai nhánh (có/không `code-graph`) trên bộ golden định-vị-code, ghi hit@k + token + số tool-call vào `harness/metrics/`. Kết luận chỉ là **số**, không kèm quyết định gỡ. *(FR-003, FR-008)*
- [x] **T3 — Ghi chi phí sync.** `wiki-sync.py --check` ghi `sync_ms` (+ `sync_tokens` nếu có) vào `harness/metrics/`; báo cáo tỉ lệ commit đi qua cổng no-op. *(FR-004)*
- [x] **T4 — Golden "người mới".** Thêm golden vào `llmwiki/wiki/sources/evals/retrieval/`: agent context-rỗng, chỉ có wiki, nhận task sửa một feature — chấm chạm-đúng-file + không-vi-phạm-ADR. Đếm trần golden trước khi thêm. *(FR-005, FR-008)*
- [x] **T5 — Nháp cross-repo impact (timebox, throwaway).** Dùng `code-graph` `list_projects` nối hai project FE/BE, thử trả lời "đổi schema BE thì FE chạm gì". Output là **quyết định go/no-go + ghi chú**, không phải code ship. *(hướng Prototyper bàn giao)*
- [x] **T6 — Vá hở persona-room.** (a) Mỗi `llmwiki/personas/*.md` thêm một dòng vào `## DON'T`: chạm ranh giới thì ghi handoff qua `/raise-issue` với owner = persona đích, KHÔNG bỏ ý. (b) Đăng ký 6 persona archetype vào roster của `council` để gọi được vào room bằng cơ chế ghế đã có. *(FR-006, FR-007)*

## Success criteria (SC)

Đo trên **dự án đích** (ADR-004), nói bằng thứ người dùng nhận được:

- **SC-001**: Một dev dùng overstack **không còn nhận câu trả lời từ trang wiki đã lỗi thời mà không được báo** — mọi câu trả lời dựa trên trang đang mang cờ drift đều kèm cảnh báo nhìn thấy được. *(Bằng chứng máy: golden có trang bị đánh cờ → output chứa dòng cảnh báo.)*
- **SC-002**: Cảnh báo ở SC-001 **không làm dev mất niềm tin vào cảnh báo** — tỉ lệ cảnh báo giả đủ thấp để dev không tập thói quen phớt lờ. Đây là guardrail: SC-001 đạt mà SC-002 hỏng thì coi như thất bại. *(Bằng chứng: tỉ lệ trang bị cờ mà thực tế vẫn đúng, đếm trên một đợt drift thật.)*
- **SC-003**: Đường đọc wiki **không bao giờ hỏng vì cơ chế cảnh báo** — dev vẫn tra được wiki kể cả khi file trạng thái hỏng. *(Bằng chứng: test xoá/làm hỏng `stale.json` → `/query` vẫn trả lời, exit 0.)*
- **SC-004**: Đội ngũ **trả lời được bằng số** câu hỏi "code-graph có còn đáng bật không", thay vì tranh luận bằng cảm tính. *(Bằng chứng: bảng so hai nhánh có delta hit@k và token.)*
- **SC-005**: Chi phí đồng bộ wiki **không âm thầm phình lên** — thời gian chờ mỗi commit giữ ở mức dev không có động cơ tắt hook. *(Bằng chứng: p95 `sync_ms` theo dõi được; cổng no-op vẫn chiếm đa số commit.)*
- **SC-006**: Một người mới vào dự án **nắm được vì sao feature tồn tại và luật nào chi phối nó** chỉ bằng wiki, không cần hỏi người cũ. *(Bằng chứng: golden T4 pass.)*
- **SC-007**: Ý tưởng nêu ra trong một phiên **không còn rơi mất khi nó thuộc nghề của persona khác** — mỗi ý chạm ranh giới đều tìm lại được sau đó. *(Bằng chứng: sau một phiên đa-persona, mọi ý bị bỏ đều có bản ghi kèm owner.)*

## Assumptions

Mọi trường user không nói mà model tự điền:

- Cảnh báo stale chỉ **cảnh báo**, không chặn `/query` `(default)` — chặn đường đọc rủi ro cao hơn nhiều so với lợi ích, và trái kỷ luật fail-open.
- Cảnh báo hiển thị ở mức **mỗi trang một dòng**, không kèm diff chi tiết `(default)` — chi tiết đã có ở `/lint`.
- T2 chấm trên **bộ golden định-vị-code hiện có**, không viết golden mới cho riêng nó `(default, find-out-later)` — nếu golden hiện có không đủ đại diện thì phải bổ sung, mà bổ sung lại đụng trần 30. Cần kiểm số golden thực tế trước khi chạy.
- Ngưỡng "delta đáng kể" của T2 chưa chốt `(default, find-out-later)` — sẽ đọc số rồi mới đặt ngưỡng, tránh đặt ngưỡng vừa khít số mình muốn.
- T3 chỉ ghi `sync_ms`; `sync_tokens` gần như luôn bằng 0 ở cổng no-op `(default)` — vẫn ghi field cho đủ, nhưng không kỳ vọng nó biến thiên.
- T5 timebox **một phiên** `(default)` — hết giờ mà chưa ra tín hiệu thì kết luận no-go, đúng tinh thần throwaway.
- T6(b) đăng ký persona archetype vào roster council bằng **cùng định dạng 18 persona sẵn có** `(default)` — không đổi engine `council.py`, vì SKILL.md đã nói rõ persona chỉ là chữ nhét vào prompt.
- T6(a) dùng `/raise-issue` chứ không dựng ledger mới `(default)` — nó đã có owner + ledger local + surface qua `/lint`, đúng hình dạng cần.

Không có mục nào rơi vào nhóm bắt buộc `[CẦN LÀM RÕ]` (auth/phân quyền, lưu trữ dữ liệu, tiền, pháp lý, ranh giới tin cậy): proposal này không chạm dữ liệu người dùng, không chạm xác thực, không chạm thanh toán.

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|------|-------------|-----------|--------|
| T1 — nối `stale.json` → `/query` | CLAUDE | Chạm đường đọc chính + đòi kỷ luật fail-open; sai ở đây là feed knowledge sai cho mọi phiên sau | pending |
| T2 — đo `code-graph` | CLAUDE | Đọc số rồi đặt ngưỡng là phán đoán, dễ tự lừa nếu giao máy rẻ | pending |
| T3 — metric chi phí sync | OPENCODE big-pickle | Thuần cơ khí: thêm field đo, ghi JSONL, verify được bằng chạy lại | pending |
| T4 — golden "người mới" | CLAUDE | Thiết kế golden từ ADR cần phán đoán về cái gì đáng chấm | pending |
| T5 — nháp cross-repo impact | OPENCODE deepseek-v4-flash | Đúng posture Prototyper: bắn nhanh, throwaway, CLI rẻ | pending |
| T6 — vá hở persona-room | CLAUDE | Chạm 6 file persona + roster council; nhỏ nhưng phải khớp convention hai cây skill | pending |

## Render brief

Dùng cho bước render `.html` (một sơ đồ mỗi task, tag từng bước legacy / add / block).

**T1** — Bên tham gia: Agent · `/query` · `stale.json` · `wiki-sync` · `/lint`. Bước: (1 legacy) `wiki-sync --check` phát hiện code đổi → ghi cờ `code-drift` vào `stale.json`; (2 block) HIỆN TẠI `/query` không đọc `stale.json` → trả trang stale **không cảnh báo** → agent lập luận trên tri thức cũ; (3 legacy) `/lint` đọc cờ — nhưng chỉ chạy theo chu kỳ, giữa hai lần lint là vùng mù; (4 add) `/query` đọc `stale.json` trước khi trả; (5 add) trang có cờ → gắn một dòng cảnh báo nêu file code đã đổi; (6 add) `stale.json` thiếu/hỏng → nuốt lỗi, trả lời bình thường (fail-open). *Prose:* nêu rõ đây là bug hở kiểu classic — phát hiện đúng nhưng cảnh báo không đi tới nơi tiêu thụ; nêu rủi ro cảnh báo bị nhờn.

**T2** — Bên tham gia: golden định-vị-code · `retrieval-eval` · nhánh CÓ code-graph · nhánh KHÔNG code-graph · `harness/metrics/`. Bước: (1 legacy) bộ golden + baseline đã tồn tại từ đợt L0→L1; (2 add) chạy nhánh có `code-graph`; (3 add) chạy nhánh chỉ grep/read; (4 add) ghi hit@k + token + số tool-call của cả hai; (5 block) nếu tổng golden vượt 30 → `retrieval-eval` từ chối chạy, phải đếm trước; (6 add) xuất bảng so — **chỉ số, chưa quyết định gỡ**. *Prose:* ba người độc lập nói code-graph hết cần; Grower không được cãi bằng suy đoán; giải thích vì sao ngưỡng đặt SAU khi đọc số.

**T3** — Bên tham gia: commit · `wiki-sync --check` · `harness/metrics/` · Dev. Bước: (1 legacy) mỗi commit chạy cổng no-op tất định; (2 legacy) code không đổi → exit 0, không gọi LLM; (3 add) ghi `sync_ms` (+`sync_tokens`) mỗi lần check; (4 add) báo cáo tỉ lệ commit qua cổng no-op; (5 block) p95 `sync_ms` vượt ngưỡng → cảnh báo, vì cổng chậm thì dev tắt hook và cổng bị tắt là cổng chết. *Prose:* lợi thế kiến trúc không đo được thì không phải lợi thế, chỉ là niềm tin.

**T4** — Bên tham gia: Agent context-rỗng · wiki (`concepts`/`ADR`/`decisions`) · task sửa feature · chấm điểm. Bước: (1 add) dựng golden: agent không có context ngoài wiki; (2 add) giao một task sửa feature có business rule nằm trong ADR; (3 add) chấm chạm-đúng-file; (4 add) chấm không-vi-phạm-rule đã ghi; (5 block) token nạp context vượt ngân sách `wiki-room` → fail; (6 legacy) nhập vào bộ `retrieval-eval` đã có. *Prose:* đây là câu hỏi của Đinh Chương biến thành eval; nó đo đúng phần cả thread đồng ý là khó — business logic, không phải cấu trúc code.

**T5** — Bên tham gia: `code-graph` `list_projects` · project BE · project FE · Prototyper · quyết định. Bước: (1 legacy) `code-graph` đã index nhiều project, có `list_projects`; (2 add) nối hai project trong một truy vấn; (3 add) hỏi "đổi schema BE thì FE chạm gì"; (4 add) đối chiếu kết quả với sự thật do người xác nhận; (5 block) hết timebox một phiên mà chưa có tín hiệu → **no-go, vứt nháp**; (6 add) có tín hiệu → bàn giao đúng một hướng cho Builder. *Prose:* nhấn đây là NHÁP, phần lớn nháp không ship và đó là điểm; nêu vì sao hướng Context Hub đã bị loại từ đầu.

**T6** — Bên tham gia: Persona A · ranh giới `## DON'T` · `/raise-issue` (ledger) · `council roster` · Persona B. Bước: (1 block) HIỆN TẠI persona A chạm ranh giới, nói "đó là Builder" → ý tưởng **bốc hơi**, không có handoff trong `archetype.py`; (2 add) thêm một dòng vào `## DON'T` của 6 persona: ghi handoff qua `/raise-issue` owner = persona đích; (3 add) ledger local giữ ý kèm owner, surface ở `/lint`, không chặn; (4 legacy) `council` vốn đã hỗ trợ ghế persona `roster --personas …`; (5 add) đăng ký 6 persona archetype vào roster → gọi được vào room ngay trong phiên; (6 add) hai sổ hộ khẩu persona nhập một, không đổi engine `council.py`. *Prose:* giải thích ranh giới persona đang là ngõ cụt, và cả hai nửa cơ chế đã có sẵn nên đây là việc **nối dây**, không phải xây mới.

## Self-review

**1. Phủ yêu cầu.** Request có ba phần: (a) đọc thread rút bài học cho graph — phủ bởi `## Ba lens trong room` + T1/T2/T3/T4/T5; (b) gọi thêm Prototyper và Maintainer vào room — phủ bởi hai tiểu mục tương ứng, mỗi persona giữ đúng ranh giới nghề (Prototyper tự loại hướng Context Hub; Maintainer không đề xuất feature nào, chỉ dán ba điều kiện lên việc người khác); (c) hở persona không gọi nhau và không lưu ý tưởng — phủ bởi T6. Mỗi yêu cầu về đúng một nhóm task, không trùng.

**2. Quét placeholder.** Đã rà toàn văn theo danh sách cấm của R7-g: không còn chỗ nào bỏ ngỏ bằng từ hoãn-binh hay bằng lời hứa xử-lý-chung-chung, cũng không có task nào mô tả bằng cách trỏ sang task khác. Hai chỗ chưa chốt được giá trị thì khai tường minh bằng tag `(default, find-out-later)` ở `## Assumptions` (bộ golden của T2, ngưỡng delta của T2) chứ không để trống.

**3. Nhất quán tên-kiểu.** Rà các tên xuất hiện nhiều lần: `stale.json` (không viết lẫn "stale file"), cờ `code-drift` (không viết lẫn "cờ stale"), `retrieval-eval` (không viết lẫn "wikieval" — hai thứ khác nhau, proposal này chỉ dùng `retrieval-eval`), `wiki-sync --check`, `code-graph`, `/raise-issue`, `council roster`. Đã thống nhất `harness/metrics/` là nơi ghi số cho cả T2 và T3.

**Một chỉnh sửa tại chỗ trong lúc self-review:** bản nháp đầu giao T2 cho `wikieval`; đã sửa thành `retrieval-eval` vì [[010726-query-retrieval-eval]] cho thấy đó mới là bộ đo hit@k + token có baseline, còn `wikieval` là eval hồi quy từ goldens wiki — dùng nhầm sẽ đo sai thứ.

## Kết quả thi hành (2026-07-20)

Cả sáu task đã chạy. Hai kết quả lệch khỏi dự kiến, ghi lại nguyên trạng:

**T1 — xong, chứng minh trên dữ liệu thật.** Thêm `wiki-sync.py --flags-for` (fail-open tuyệt đối, luôn exit 0) + bước `3b` trong `skills/query/SKILL.md`. Test `harness/tests/wiki-sync-flags-failopen-test.sh` **11/11 pass**, khoá cả hai chiều: cờ tới được đường đọc, và mọi trạng thái hỏng của `stale.json` (thiếu / JSON hỏng / sai kiểu / wiki-dir không tồn tại) đều exit 0 im lặng. Chạy trên cờ drift THẬT: ba trang (`concepts/adapt-modes.md`, `problem-tree.md`, `wiki-core-relations.md`) trước đây `/query` trả về im lặng, nay có cảnh báo.

**T2 — đổi kết luận: không đo được giá trị code-graph vì code-graph ĐANG HỎNG.** `search_symbols`/`get_stats` lỗi `no such table`; `reindex_repo` báo thành công (2660 file, 21972 symbol) mà search vẫn hỏng ⇒ đường ghi và đường đọc trỏ hai DB khác nhau. Đo được (`harness/metrics/code-graph-ab.json`, 5 task × 2 nhánh): nhánh code-graph **37 tool-call** vs baseline **14** (2.64× đắt), độ chính xác **hoà 5/5**. Con số này đo *chi phí của một tool hỏng mà orientation lùa mọi phiên vào*, KHÔNG phải giá trị của code-graph. Đúng ranh giới Grower: **dừng ở số**, không kết luận giữ/bỏ. Handoff → [[200726-code-graph-index-broken]] (assignee maintainer).

**T3 — xong.** `wiki-sync --check` ghi `sync_ms`/`status`/`suspects` vào `harness/metrics/sync-log.jsonl`, fail-open, không tự tạo thư mục (downstream không có `harness/` thì im). Lần chạy thật: **137 ms, 0 token**.

**T4 — xong, giữ trần 30.** Đổi chỗ golden `extract-site` ("Skill X dùng để làm gì?" — nông nhất bộ) lấy `newcomer-adr`. Golden mới hỏi bằng lời người mới, **không có** chữ "opt-in" hay "ADR", và ý định trong câu hỏi vi phạm ADR-004. Kết quả: **HIT, recall 1.0** — wiki nổi được cả hai trang đích. Bộ eval `hit@5 30/30`, baseline đã chốt lại, `--check` rc=0.

**T5 — NO-GO, lý do là nền chứ không phải ý tưởng.** Nháp cross-repo dựa trên `list_projects` để nối hai project, mà chính hàm đó đang trả 17 mục cùng tên `"index.db"`. Đúng tinh thần throwaway: biết sớm, vứt sớm, ghi lại lý do. Mở lại sau khi issue code-graph đóng.

**T6 — xong, và đã được dùng thật ngay trong phiên.** Sáu file `llmwiki/personas/*.md` có thêm khối "Chạm ranh giới ≠ vứt ý"; sáu archetype đăng ký vào `harness/council.personas.yaml` (kèm `--case lifecycle`, profile `archetype`, 3 cặp đối-trọng mới). `council.py roster --case lifecycle` chạy đúng và tự phát hiện cặp `prototyper ↔ maintainer`. Phép thử thật đầu tiên: handoff issue code-graph ở T2 chính là Grower chuyển việc hardening cho Maintainer qua cơ chế này.

**Một lần tôi tự sai, ghi lại để khỏi lặp:** lúc đầu tôi báo 4 hồi quy hit@k (`architecture`, `harness-local`, `onboarding-tour`, `skill-sot`) — sai, do tôi chạy `query-proxy --topn 3` trong khi baseline và CI dùng `--topn 5`. Chạy đúng cấu hình CI thì `hit@5 30/30`, không có hồi quy nào. Bài học: đọc cấu hình của cổng trước khi tuyên bố cổng đỏ.

## Origin
- **Draft:** `wiki/sources/draft/190726-graph-lessons-grapuco.md`
- **Source:** `llmwiki/wiki/draft/grapuco-discuss.md` (thread cộng đồng Grapuco, 9 người phản biện) — đọc qua lens `llmwiki/personas/{grower,prototyper,maintainer}.md`
- **Task:** `T-260719-02`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
