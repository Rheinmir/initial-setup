---
name: propose
description: Plan a feature before coding — draft in wiki/sources/draft/, stop for approval
---

# Skill: propose

## Purpose
Plan feature/change before writing code. Surfaces impact on existing functionality, gets alignment before implementation.

## When to use
- New feature, endpoint, component, or behaviour requested
- Change touches shared/core code
- Scope unclear or multi-interpretable

## What this skill produces — and what it deliberately does NOT
`/propose` sinh **SPEC** (bản thiết kế): thứ **NGƯỜI** đọc để bấm duyệt ở cổng. Nó KHÔNG phải kế hoạch thi hành.
Kế hoạch code-level (đường dẫn chính xác, chữ ký hàm, test, code từng bước) là việc của skill **`/plan`**, chạy SAU khi SPEC được duyệt.

Lý do tách (đối chiếu `obra/superpowers`, tỷ lệ spec:plan ≈ 1:8 — 82–511 dòng so với 673–2621 dòng): nếu nhồi code-level vào SPEC thì draft phình tới mức người duyệt không đọc nổi thứ mình đang duyệt, và **cổng duyệt mất tác dụng**. Hai văn bản, hai người đọc.

## Steps
0. **Force-query wiki TRƯỚC khi draft** — query/đọc wiki (`concepts/`, `entities/`, `sources/adr/`, `decisions.md`) tìm concept/ADR/quyết định liên quan; tóm tắt vào `## Context` của draft + cite `[[wikilink]]`/path. KHÔNG propose "mù" (R7-f chặn draft thiếu `## Context` có nội dung).
0b. **Tìm unknowns TRƯỚC khi draft** (map ≠ territory, GH#40 — xem `fdk/wiki/concepts/map-not-territory.md`): model càng mạnh càng lấp chỗ mơ hồ bằng câu trả lời tự tin. Trước khi viết một dòng SPEC, liệt kê ngắn "để làm đúng việc này tôi CHƯA biết gì?" — soi 5 chỗ bản đồ hay nói dối: (a) ý định ngầm của người yêu cầu, (b) quy ước tribal không có trong wiki hay `CLAUDE.md`, (c) hình dạng dữ liệu thật (schema, sample, biên), (d) môi trường chạy (version, env, quyền), (e) thứ đã đổi kể từ lần wiki được viết. Mỗi unknown đi vào đúng tầng của `## Assumptions` bên dưới: fact → tra; decision rủi ro thấp → `(default)`; cần kiểm lại → `(default, find-out-later → unknown-ledger)`; hỏng-kiến-trúc-nếu-sai → `[CẦN LÀM RÕ]`. Không có unknown nào là dấu hiệu chưa tìm, không phải dấu hiệu đã hiểu.
1. Restate request in one sentence to confirm understanding.
2. List every existing file, function, or module affected or must change.
3. List every existing feature or behaviour that could break as side effect.
4. Propose minimal implementation plan as numbered steps.
5. State what success looks like (verifiable criteria).
6. Create draft file at `llmwiki/wiki/sources/draft/DDMMYY-feature-name-module.md` (e.g. `260425-new-approval-button-fe.md`) containing proposal output from steps 1–5. Draft MUST include (enforced by validator R7 — blocked at write-time and commit if missing):
   - `## Context` — tóm tắt wiki liên quan đã query ở bước 0 (concept/ADR/decision), cite `[[wikilink]]`/path (force-query grounding — R7-f chặn nếu thiếu/rỗng)
   - `## Global constraints` — ràng buộc **bao trùm mọi task**, chép **nguyên văn** giá trị thật từ wiki/ADR/policy (sàn version, giới hạn dependency, luật đặt tên, gate bắt buộc trước push…). Mỗi task ngầm mang theo section này; agent thi hành chỉ nhìn thấy task của nó, nên ràng buộc chung phải nằm ở một chỗ ai cũng được bơm. **R7-h chặn nếu thiếu/rỗng.**
   - `## Non-goals` — cái gì cố ý KHÔNG làm. Không có mục này thì scope trôi lúc thi hành.
   - `## Approaches` — 2–3 phương án **khác nhau về bản chất** + tradeoff từng cái + phương án chọn và vì sao. **Cấm chọn thầm.**
   - `## Plan` — tasks as `- [ ]` checklist items
   - `## Requirements (FR)` — **id ổn định** cho từng yêu cầu chức năng: `**FR-001**: Hệ thống PHẢI …`. Đây là neo để PLAN truy vết ngược (R18 chặn PLAN bỏ sót id nào).
   - `## Success criteria (SC)` — **id ổn định** cho từng tiêu chí: `**SC-001**: …`. Xem mục "Tiêu chí phải đo NGƯỜI, không đo MÁY" bên dưới.
   - `## Assumptions` — mọi trường **user không nói mà model tự điền**, mỗi dòng gắn tag **`(default)`**. Xem mục "Tự điền hay hỏi" bên dưới.

## Fact hay decision — tra trước, hỏi sau, tự điền phần giữa
Có một câu hỏi đứng **trước** cả "tự điền hay hỏi": **đây là một FACT hay một DECISION?**

- **Fact** — có câu trả lời đúng, tra được bằng cách khám phá môi trường: đọc file, chạy lệnh, grep, xem `git remote -v`, đọc `package.json`. → **TRA, tuyệt đối không hỏi.** Hỏi user một thứ mà công cụ trả lời được là lãng phí lượt của họ, và làm họ tưởng bạn không biết đọc môi trường.
- **Decision** — không có câu trả lời đúng, là một lựa chọn. Đây mới là chỗ chia tiếp thành `(default)` / `[CẦN LÀM RÕ]` bên dưới. Quyết định là **của user** — nhưng phần lớn quyết định rủi ro thấp thì tự điền default hợp lý rồi khai ra, chỉ leo lên hỏi khi rủi ro cao.

Ranh giới: nếu bạn *có thể* tìm ra bằng một lệnh, đó là fact — đi tìm. Nếu hai người hợp lý có thể chọn khác nhau, đó là decision — xử theo tầng dưới.

**Lựa chọn THIẾT KẾ user không nói = decision rủi ro thấp → fill từ nền, đừng hỏi.** Khi brief đụng UI mà user không nói rõ macrostructure, theme, type-pairing, hay màu anchor, ĐỪNG phỏng vấn — fill mặc định hợp brief từ catalog `[[design-foundation]]` (nguồn: `skills/hallmark/references/macrostructures/` + `references/genres/`), gắn tag `(default)`, và **ghi tên macrostructure + theme đã chọn vào `## Assumptions`**. User liếc là biết máy chọn gì, đổi một dòng nếu không thích. Chọn sai macrostructure thì sửa nhanh — nó không phải auth hay tiền. Đây là nguồn tham chiếu để fill unknown thiết kế, cắm vào đúng hệ `(default)` này. (Brief mang creative-intent mà không theme nào hợp → hallmark tự sang nhánh Custom; vẫn 6 discipline + slop-test.)

## Tự điền hay hỏi — mặc định là TỰ ĐIỀN
User đã mô tả hết những gì họ biết. Đừng phỏng vấn họ về thứ họ không biết — **tự điền mặc định hợp lý, rồi KHAI RA là mình điền**:

- **`(default)`** — model tự chọn. Cứ chạy tiếp, không hỏi. Người duyệt liếc `## Assumptions` là phân biệt được ngay đâu là lời họ, đâu là lời máy, và sửa dòng nào họ không đồng ý.
- **`(default, find-out-later → [[unknown-<slug>]] U-NN)`** — tầng GIỮA: model điền một default NGAY để không chặn việc, **nhưng ghi thành nợ có sổ** thay vì im lặng. Dùng khi default *có rủi ro và ta biết sẽ phải kiểm lại* — kể cả khi hạ một `[CẦN LÀM RÕ]` xuống (user bảo "cứ điền, tính sau"). Ghi nợ bằng `python3 harness/scripts/unknown-ledger.py --add …` → nó in `U-NN` để dán vào dòng Assumptions. Nợ này KHÔNG chặn cổng — chỉ hiện ra ở `/lint` để không chìm. Xem `[[150726-unknown-ledger]]`.
- **`[CẦN LÀM RÕ: <câu hỏi cụ thể>]`** — model **TỪ CHỐI đoán**, đặt thẳng vào chỗ đó trong SPEC. Chỉ dùng cho nhóm mà một mặc định sai là **hỏng kiến trúc hoặc hỏng người dùng**, khớp carve-out của `CLAUDE.md`:
  - cơ chế xác thực / phân quyền (ai được làm gì)
  - lưu trữ dữ liệu: lưu gì, ở đâu, bao lâu, ai đọc được
  - tiền / thanh toán / hạn mức
  - thứ có hệ quả pháp lý hoặc tuân thủ
  - bất kỳ ranh giới tin cậy nào (nhập liệu từ ngoài, biên hệ thống)

  **R7-n chặn cổng duyệt nếu SPEC còn `[CẦN LÀM RÕ]` chưa được trả lời.** User trả lời → thay bằng giá trị thật; user bảo "cứ đoán đi" → hạ xuống `(default)` **một cách có chủ ý**, có ghi vết.

Sai cái nút màu thì sửa ba mươi giây. Sai cơ chế auth thì cái `(default)` đó lặng lẽ trở thành một quyết định kiến trúc, và người duyệt lướt qua vì nó *trông như đã xong*. `(default)` một mình là cái máy hợp thức hoá phỏng đoán; nó chỉ an toàn khi đi kèm `[CẦN LÀM RÕ]`.

**Interview chỉ chạy khi user YÊU CẦU** (`/br interview`) — và khi chạy thì trần **5 câu**, chọn theo (Impact × Uncertainty).

**Interview dạng chọn-đáp-án LUÔN có một đáp án cuối: "điền mặc định bây giờ, tìm hiểu sau (ghi nợ unknown)".** User không chắc, không muốn dừng để nghĩ, nhưng cũng không muốn model đoán thầm → chọn đáp án này: model điền default hợp lý ngay (việc chạy tiếp) và ghi một unknown vào sổ để trả nợ sau. Đây là đường thoát cho mọi câu user chưa sẵn sàng trả lời mà vẫn giữ được truy vết — không ép trả lời, không đoán im lặng.

## Trả nợ unknown — khi có thông tin thật
Một unknown đã ghi (`(default, find-out-later)`) không phải để quên. Khi có thông tin thật:
1. **Điền giá trị đúng vào SPEC/PLAN nguồn** — thay dòng `(default, find-out-later → …)` bằng giá trị thật.
2. **Đóng sổ:** `python3 harness/scripts/unknown-ledger.py --resolve --file unknown-<nguồn>.md --id U-NN --value "<giá trị đúng>" --fixed "<sửa ở đâu>" --date <YYYY-MM-DD>`. Sổ giữ **cả** giá-trị-đã-fill lẫn giá-trị-đúng (audit — sáu tháng sau biết model đã đoán gì, đúng không, sửa ở đâu).
3. **Nếu default sai ĐÃ đẻ code sai** (đã thi hành trên giá trị đoán) → mở `/orca-issue` (repro-first) hoặc `/raise-issue`, link ngược `U-NN` trong body.

Nợ mở hiện ra ở `/lint` (báo cáo, không chặn) — `unknown-ledger.py --list`. Trả nợ là hành động **có chủ ý** của người/agent; skill chỉ cung cấp luồng, không tự "tìm hiểu" giùm.

**Khi có hỏi — hỏi cho đúng cách:**
- **Một câu một lượt.** Chờ trả lời rồi mới hỏi câu sau. Hỏi chùm làm người ta hoang mang và trả lời qua loa.
- **Luôn kèm phương án khuyến nghị**, đặt đầu tiên, để user gật một tiếng ("đồng ý" / "cái đầu") là xong thay vì phải tự soạn câu trả lời.

## Tiêu chí phải đo NGƯỜI, không đo MÁY
`SC-xxx` phải **đo được** và **không dính công nghệ** — nói người dùng nhận được gì, không nói cái máy làm gì:

- ✅ "User hoàn tất tạo tài khoản dưới 2 phút" · "chịu 1000 người đồng thời không suy giảm" · "giảm 50% ticket hỗ trợ về X"
- ❌ "chạy `pytest` ra exit 0" · "validator trả về 2" — đó là đo **cái máy**. Một hệ thống có thể xanh toàn tập mà vẫn vô dụng.

Cách kiểm ở tầng máy **vẫn ghi**, nhưng ghi như **bằng chứng** của `SC-xxx`, không thay thế nó.
   - `## Agent Task Assignment` — table `| Task | Agent (CLI) | Lý do chọn | Status |`, one row per task, **no empty Agent cell**, Status=pending. Pick agents by cost table; if all on one agent, say why.
   - `**Sequence diagram:**` link to companion `.html` (must exist on disk)
   - **Task ID bền (Trụ 3 — best-effort, fail-open):** `python3 harness/scripts/code-logger.py --task new title="<feature>"` → in `T-YYMMDD-NN`; ghi vào frontmatter `task: T-YYMMDD-NN`. Lệnh **fail-open** — install cũ thiếu `--task` hoặc store lỗi → in "bỏ qua", cứ để trống `task:`, KHÔNG chặn propose. Đây là id mà gate/dispatch/verify dùng để advance vòng đời + neo vào audit trail bất biến (events.jsonl chained).
   Add row to `llmwiki/wiki/index.md` and append to `llmwiki/wiki/log.md`.
7. Create the **companion HTML page** at `llmwiki/html/DDMMYY-feature-name-seq.html`. For EACH task in Plan the page MUST contain **both** parts — a page that is only diagrams with no rich prose, OR only prose with no diagram, is INCOMPLETE (R7 checks `diagram-box` count ≥ task count):
   - **(A) Animated diagram** — one per task, titled by its task + badge naming the assigned agent; lifelines = participants; messages are **all visible by default** (`.msg` opacity ≥ .82) — the animation only *highlights* the running step (auto-loop, click to pause), **never hide a message with `opacity:0`** (lesson 130626 / R7-d); 2-color: indigo = existing, emerald = added/changed, amber = blocked/fail branches.
   - **(B) Rich detail prose** — alongside each diagram, a readable explanation in **full, complete sentences** (not terse diagram labels): what changes and why, the data/flow at runtime, the safe-vs-blocked branch, and the concrete risk. This is human-read documentation → honour the prose rule (CLAUDE.md 2026-06-27): never caveman or over-compressed here. The diagram is the skeleton; this prose is the body — both are required.
   - **Style:** the page MUST use the `docs-site-macos` liquid-glass look (light gradient field + refraction layers + glass tier-2 cards + Apple-tint badges) — clone an existing `llmwiki/html/*-seq.html`. Never hand-roll a dark/flat theme (lesson 250626 "sao xấu thế").
   - **Authoring split — Claude thinks, a cheaper CLI renders:** the `.md` is the SUBSTANCE (Claude's job) and must be render-complete — besides Plan + prose, include a `## Render brief` section giving, per task, the diagram's ordered steps (each tagged legacy / add / block) **and** the full prose paragraph. The `.html` is then a **mechanical render** of that brief and, in orchestrated runs, MAY be dispatched to a cheaper CLI (OpenCode `big-pickle` / `agy` / `kiro`, $0) — see `orca-workflow`. Standalone `/propose`: Claude renders directly and `## Render brief` is optional. Because the render is free when delegated, prefer **Full** `docs-site-macos` richness for the `.html` rather than a stripped page — Claude's token cost is the substance only and does not grow with HTML richness.
   - Link both ways: `.md` ↔ `.html`
8. **Self-review — soi lại bằng mắt mới, sửa tại chỗ.** Ghi kết quả vào `## Self-review` của draft (3 mắt lưới):
   1. **Phủ yêu cầu** — mỗi yêu cầu trong request chỉ được về đúng một task. Thiếu → thêm task.
   2. **Quét placeholder** — không được còn `TBD`, `TODO`, "xử lý lỗi phù hợp", "handle edge cases", "tương tự Task N". **R7-g chặn.**
   3. **Nhất quán tên-kiểu** — cùng một thứ phải gọi cùng một tên xuyên suốt draft (hàm `clearLayers()` ở task 3 mà `clearFullLayers()` ở task 7 là một con bug đã sinh ra ngay trong lúc viết).
   Tìm thấy lỗi thì sửa thẳng, không cần review lại vòng hai.
9. STOP. No code. Show the draft content + the HTML preview URL. Wait for user to approve or redirect.
10. **Sau khi user DUYỆT** — bàn giao sang `/plan` (Skill tool → `plan`) để mở rộng SPEC này thành `DDMMYY-<tên>-PLAN.md` thi hành được. Đừng dispatch task khi chưa có PLAN: agent CLI rẻ chạy headless không thừa hưởng context nào và không hỏi lại được — nó chỉ có đúng thứ ta bơm vào (bài học 250626: giao hàng ~1/5 khi brief mỏng).

## Rules
- **OKF v0.1 (R9):** the draft starts with a YAML frontmatter block (`---`) with `type: draft` (+ optional `title`/`status`/`tags`/`timestamp`/`task`); copy `sources/draft/_template.md`. Keep `**Status:** proposed` in the body so R7 can gate it.
- Never begin implementation during this skill.
- The proposal is a PAIR: `.md` + `.html` (one diagram per task). Validator R7 blocks incomplete proposals at write and commit — fix before asking for approval.
- If impact list empty, state explicitly "No existing code affected."
- If multiple approaches exist, present with tradeoffs — do not pick silently.

---

## Output Report

After all main skill tasks complete, write a propose draft to the wiki.

### Steps

**1. Build the filename:**
- Format: `DDMMYY-<ten>.md`
- `DDMMYY` = today (e.g., `020626` for 2 June 2026)
- `<ten>` = 2–4 kebab-case words summarising what was done (e.g., `landing-page-coteccons`, `brand-kit-fintech`, `ingest-auth-spec`)

**2. Write** `llmwiki/wiki/sources/draft/DDMMYY-<ten>.md`:

```
# DDMMYY-<ten>
**Type:** draft
**Status:** proposed
**Tags:** <skill-name>, output-report
**Proposed:** YYYY-MM-DD

## What
<One sentence — what this skill invocation produced or decided>

## Output
<Key artefacts, files created/modified, or decisions made>

## Files
| File | Action |
|------|--------|
| `path/to/file` | created / modified |

## Notes
- Invoked via: `/<skill-name>` skill

## Origin
- **Draft:** `wiki/sources/draft/DDMMYY-<ten>.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
```

**3. Update wiki index & log:**
- `llmwiki/wiki/index.md` — append one row: `| [DDMMYY-<ten>](sources/draft/DDMMYY-<ten>.md) | draft | YYYY-MM-DD |`
- `llmwiki/wiki/log.md` — append: `## YYYY-MM-DD — <skill-name> — <ten>`

> Skip only when the skill produces zero artefacts and zero decisions (e.g., a pure display mode like `/caveman-stats`).
