---
name: query
description: Synthesize answer from wiki; persist new insights as wiki entries
---

# Skill: query

## Purpose
Answer question by synthesizing wiki knowledge. Valuable findings not in wiki become new pages, compounding knowledge over time.

## When to invoke
When user asks question requiring synthesis across multiple wiki pages or raw sources.

## Steps — progressive disclosure 3 tầng (ĐỪNG nạp cả trang ở bước 1)
> Nguyên tắc: quét RẺ để xếp hạng trước, chỉ ĐỌC FULL vài trang cao điểm. Đo trên bộ golden
> `wiki/sources/evals/retrieval/` cho thấy cách này giữ nguyên recall mà cắt ~65% token so với
> "đọc mọi trang khớp" (baseline L0). Kiểm chứng: `retrieval-eval.py --check`.

0. **Tầng 0 — truy hồi NGỮ NGHĨA (episodic + memory), KHÔNG chỉ theo link:** trước khi quét wiki,
   hỏi tầng nhớ episodic xem *phiên trước* đã đụng câu hỏi này chưa:
   `python3 harness/scripts/mem-rank.py retrieve "<câu hỏi>" --k 5` (thêm `--kind-filter episode`
   để chỉ lấy sự kiện phiên). Trả về top-k memory/episode liên quan theo **nghĩa** (token-overlap,
   sẽ là embedding khi adapter `mem-rank.config.yaml` được wire) — bắt được trang KHÔNG có
   `[[wikilink]]` trỏ tới. NOOP (rỗng) thì bỏ qua, không nhồi nhiễu. Dùng kết quả này để mồi
   danh sách trang cho Tầng 1 + biết "việc này từng làm ở phiên nào".
1. **Tầng 1 — quét, KHÔNG mở full trang nào:** `ripgrep` câu hỏi trên `wiki/index.md` + nội dung wiki (`rg -c '<term>' wiki/` để đếm khớp), xếp hạng trang theo **độ phủ term** (trang chứa nhiều term của câu hỏi nhất). Câu hỏi về code → dùng code-graph MCP (`search_symbols`) thay `rg`. Kết quả tầng này = danh sách slug + dòng khớp; chưa `Read` full trang nào.
2. **Tầng 2 — khoan:** chỉ `Read` FULL **top-N trang cao điểm nhất** (mặc định ~5). Bỏ phần đuôi bảng xếp hạng — không đọc cho "chắc".
3. **Tầng 3 — bối cảnh:** nếu câu trả lời cần mạch liên quan, lần theo `[[wikilinks]]` của các trang vừa đọc (tương đương timeline/related của engram) — vẫn chỉ mở trang được trỏ tới, không mở tất cả.
3b. **Cổng drift trên đường ĐỌC (0 token, fail-open)** — trước khi tổng hợp, hỏi xem trang mình vừa đọc có đang lệch code không:
   `RUN: python3 harness/scripts/wiki-sync.py --flags-for "<slug1,slug2,…>"` (downstream không có `harness/` trong repo thì dùng bản global: `python3 ~/.claude/harness/harness/scripts/wiki-sync.py --flags-for "…" --root .`).
   Truyền đúng các trang đã `Read` ở tầng 2–3. Lệnh **luôn exit 0**; im lặng = không trang nào bị cờ.
   Có dòng `⚑ CẢNH BÁO DRIFT` → **chuyển nguyên văn cảnh báo đó vào câu trả lời** (một dòng mỗi trang, đặt ngay đầu phần trả lời) rồi mới trả lời bình thường; đừng nuốt cảnh báo, cũng đừng từ chối trả lời.
   Vì sao có bước này: `wiki-sync --check` ghi cờ `code-drift` vào `stale.json`, nhưng trước 2026-07-19 chỉ `/lint` đọc cờ đó — mà lint chạy theo chu kỳ, nên giữa hai lần lint `/query` trả về trang đã lệch code **mà không cảnh báo gì**. Đó đúng là ca "wiki là nguồn sự thật nhưng nội dung đã lệch" khiến model lập luận tự tin trên tri thức cũ.

4. If answer needs info not in wiki, check `raw/` for unprocessed sources.
5. Synthesize and answer directly.
6. Evaluate: does answer contain non-obvious insight, connection, or conclusion not already in wiki?
   - If yes: create new wiki page (concept or source), update `wiki/index.md`, log in `wiki/log.md`.
   - If no: skip.
7. Append to `wiki/log.md`: `## YYYY-MM-DD — query — <question summary>` with note on whether new page created.
8. **Telemetry (đo TRUY HỒI — fail-open):** sau khi trả lời, ghi lại query để độ hiệu quả truy-hồi đo được:
   `python3 harness/scripts/query-log.py --record --question "<câu hỏi>" --pages "<slug1,slug2>" --tokens <ước tính token đã đọc> --tier <1|2|3>`
   `--pages` = các trang wiki thực sự đọc; `--tier` = tầng sâu nhất chạm tới (1 quét / 2 đọc full / 3 wikilinks). Script fail-open — không bao giờ làm gãy phiên. Giới hạn đã biết: chỉ đo khi skill `query` được gọi, không đo lượt model tự Read thẳng.

## Rules
- **OKF v0.1 (R9):** any new wiki page starts with a YAML frontmatter block (`---`) with a non-empty `type`; copy the matching `_template.md` and keep the `## Origin` section.
- Never invent facts. Synthesize from wiki and `raw/` only.
- Query revealing gap (missing entity, missing concept) should trigger `ingest` of relevant `raw/` source if one exists.

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
