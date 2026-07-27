---
name: lint
description: Periodic wiki health check — orphans, missing links, contradictions, stale (wiki→wiki VÀ code→wiki drift), index gaps. Bước 0 là cổng no-op tất định (wiki-sync, 0 token) — code không đổi kể từ neo thì kết luận "wiki current" và dừng sớm hợp lệ.
---

# Skill: lint

## When to invoke
After every 10 ingests, or when wiki stale/inconsistent, hoặc session_start báo `[wiki-sync] code đã đổi N commit`.

## Steps

0. **Code-drift gate (0 token)** — `RUN: python3 harness/scripts/wiki-sync.py --check` (downstream không có harness/ trong repo thì dùng bản global: `python3 ~/.claude/harness/harness/scripts/wiki-sync.py --check --root .`).

0b. **Hồ sơ cho từng cờ ⚑ (0 token — JOIN bộ nhớ thứ cấp 2 bước, wired 2026-07-18):** với MỖI file code mà bước 0 báo "⇐" (nguyên nhân trang nghi stale):
   - Bước 1 — PHIÊN NÀO chạm (kho dày, file-level): `RUN: grep "<tên-file>" harness/metrics/events.jsonl | tail -3` → lấy `session` + `ts`.
   - Bước 2 — VÌ SAO (why của phiên đó): `RUN: grep "<session-id-8-ký-tự>" harness/metrics/scratch-log.jsonl | tail -2`.
   Đính `phiên · ts · why` vào cờ khi báo user — cờ-có-hồ-sơ phán trong vài giây (đọc why đủ biết thay đổi có vô hiệu claim không), cờ-trần phải mò diff. Why rỗng/auto-đúc-từ-commit → ghi chú "hồ sơ mỏng, cần mở diff" thay vì im. (Giới hạn thật: scratch-log 1 why/phiên; events dày nhưng chỉ có path — độ giàu why phụ thuộc phiên có ghi tay không.)
   - Exit 0 (`current`): code không đổi kể từ neo → nếu mục đích lượt lint này là "wiki có khớp code không" thì **dừng tại đây, trả lời "wiki đã current"** — no-op là kết quả tốt, đừng bịa việc. Vẫn muốn quét sức khoẻ nội-wiki (orphan/index/origin) thì đi tiếp bước 1.
   - Exit 3 (`drift`): các trang nghi stale đã được cờ `code-drift` trong `stale.json` kèm file code gây ra. **Lập docs-impact-plan TRƯỚC khi sửa**: mỗi trang định sửa phải truy về một thay-đổi-code cụ thể (`code đổi → trang → sửa gì → vì sao`); trang không truy được về thay đổi nào thì KHÔNG đụng.
     - **Phân loại drift trước khi sửa (rubric 4 nhánh, mượn ý temporal-invalidation từ RedPlanetHQ/core, github.com/RedPlanetHQ/core `prompts/statements.ts`)**: claim cũ và thực tế mới quan hệ với nhau kiểu gì?
       - **contradiction** — hai claim không thể cùng đúng (vd "API dùng key X" khi key đã đổi tên) → claim cũ **SAI**, sửa đè bình thường.
       - **superseding** — claim cũ TỪNG đúng, nay hết hiệu lực vì đổi kiến trúc (vd đổi engine/refactor) → **đừng sửa đè câm lặng**: thêm 2 trường vào frontmatter của trang — `invalid_at: YYYY-MM-DD` + `invalidated_by: <commit-sha hoặc file gây invalidate>` — rồi mới cập nhật nội dung. Trang vẫn giữ 1 dòng ngắn nói claim cũ từng đúng tới khi nào (đừng xoá lịch sử, chỉ đóng dấu).
       - **progression** — cả hai đều đúng, khác giai đoạn (vd "đang thiết kế X" → "đã ship X") → giữ cả hai, KHÔNG invalidate, chỉ nối thêm claim mới.
       - **equivalence** — cùng nghĩa khác lời (do ingest 2 lần) → coi là trùng lặp, gộp về 1 câu, không phải drift thật.
       - Field `invalid_at`/`invalidated_by` là optional, R9 (okf_frontmatter) không chặn khoá lạ — an toàn thêm mà không cần sửa validator.
   - Exit 2 (chưa có neo / neo mất hiệu lực): làm trọn lint rồi chốt neo ở bước 10.

1. **Orphans** — `RUN: grep -rL "wiki/" --include="*.md" llmwiki/wiki/concepts/ llmwiki/wiki/entities/` → files not referenced anywhere. Flag each.

2. **Missing links** — scan pages for entity/concept names that exist as wiki files but not written as `[[wikilinks]]`. Fix in place.

3. **Contradictions** — compare claims about same entity across ≤2 pages at a time. Flag pairs (file:line vs file:line). Do NOT pick winner — flag for human review.

4. **Stale claims** — `RUN: grep -rl "raw/" --include="*.md" llmwiki/wiki/` → pages referencing raw/. Flag each.

5. **Index gaps** — `RUN: comm -23 <(find llmwiki/wiki -name "*.md" | sort) <(grep -o "llmwiki/wiki/[^)]*" llmwiki/wiki/index.md | sort)` → files missing from index. Add rows.

6. **Empty pages** — `RUN: for f in llmwiki/wiki/**/*.md; do [ $(wc -l < "$f") -lt 5 ] && echo "$f"; done` → flag for deletion or content.

7. **Missing Origin** — `RUN: grep -rL "## Origin" llmwiki/wiki/concepts/ llmwiki/wiki/entities/` → flag each as incomplete.

8. **Marker nợ thiếu trigger** — `RUN: grep -rn "shortcut:" --include="*.py" --include="*.js" --include="*.ts" --include="*.sh" . | grep -v ",";` → mỗi marker `shortcut:` cố ý phải có định dạng `<trần hiện tại>, <trigger nâng cấp>` (dấu phẩy tách 2 vế). Dòng lọt qua grep này = marker thiếu trigger nâng cấp (nợ không hạn → dễ thành "never"). Flag từng dòng cho người viết bổ sung trigger; KHÔNG tự đoán trigger.

8c. **Nợ unknown (fill-first, chờ verify — tất định, 0 token)** — `RUN: python3 harness/scripts/unknown-ledger.py --list` → in số unknown mở + cái cũ nhất + SPEC nào nhiều nợ nhất. Đây là các default model điền "để việc chạy tiếp, tính sau" (`(default, find-out-later)`). **BÁO CÁO, KHÔNG CHẶN** — fill-first cố ý không chặn; chặn ở đây là phản bội cơ chế. Mục đích: nợ hiện ra để không chìm, người duyệt tự quyết khi nào trả (xem `[[150726-unknown-ledger]]`).

8b. **Skill-health (hình dạng skill, tất định — 0 token)** — `RUN: python3 harness/scripts/skill-health.py` (repo có `skills/`) → in tổng context load model-invoked + skill nào có cờ: `desc` (description quá dài) · `sprawl` (SKILL.md quá dài mà không progressive disclosure) · `negation` (tỉ lệ câu cấm cao — nên chuyển sang câu khẳng định) · `weak-criterion` (khối `### Task` thiếu điều kiện kiểm được ở cuối) · cặp description chớm-trùng. Tiêu chí gốc ở `[[skill-craft]]`. **Báo cáo, KHÔNG chặn** — chất lượng, không phải an toàn. Flag để người viết cân nhắc, đừng tự sửa hàng loạt.

8b. **Skill-usage pulse (0 token, chỉ repo framework)** — `RUN: python3 fdk/tools/skill-usage.py --weekly --no-html` → bảng tần suất tuần + skill chết (idle ≥4 tuần). Đây là dây nuôi máy đo "skill nào đáng giữ" (wired 2026-07-18, vòng grower): usage tụt/chết là DỮ KIỆN cho quyết định cắt-giữ, không phải cảm tính. Downstream không có `fdk/tools` → bỏ qua bước này.

8c. **Docs-sprawl pulse (0 token)** — `RUN: python3 fdk/tools/docs-curate.py plan | head -5` → đếm KEEP/ARCHIVE. Nhóm ARCHIVE ≥ 30 mục → báo user gợi ý chạy `/docs-curate` (apply dời vào `archive/` + reindex — có gate người duyệt, tool không tự dời khi lint). Draft/html là RENDER ephemeral; để phình là chôn bản chất dưới rác — vòng đời phải có người quét theo nhịp (wired 2026-07-18).

8d. **Claim-receipts trên draft ACTIVE (0 token)** — với mỗi draft KEEP/TREO (không rà đồ sắp archive): `RUN: python3 harness/scripts/claim-receipts.py --check <draft>` → trích mọi file/path văn bản TRÍCH DẪN, verify còn resolve trên đĩa. Unresolved = bằng chứng tất định **nội-dung-outdated** (trỏ tới thứ đã chết/đổi tên) — flag kèm danh sách ref chết, người quyết sửa-hay-archive. Advisory (adapter `claim-receipts.config.yaml` verified:false) — không chặn, chỉ soi (wired 2026-07-18, ca unwired thứ 7).

8e. **Decision-anchoring liveness (0 token, tất định)** — `RUN: python3 harness/scripts/decision-liveness.py check` (downstream không có `harness/` trong repo thì dùng bản global: `python3 ~/.claude/harness/harness/scripts/decision-liveness.py check`; repo không có `harness/mechanisms.yaml` → bỏ qua bước này). In mọi mục có `anchor_symbol`/`live_probe` kèm nhãn `LIVE`/`STALE`/`ORPHAN`/`UNAVAILABLE` — người duyệt phân biệt ORPHAN (cần sửa neo hoặc xoá quyết định qua `status: retired`, KHÔNG xoá vật lý) với STALE (cần đọc lại, có thể vẫn đúng) chỉ bằng nhãn, không phải đọc lại toàn bộ nội dung (SC-005). **BÁO CÁO, KHÔNG CHẶN** — khớp khuôn không-chặn của draft-age/unknown-ledger (bước 8c).

8f. **Provenance-log lookup (0 token, tất định)** — với mỗi file/quyết định bước 0b đang xét "vì sao đổi": `RUN: grep "<tên-file-hoặc-id>" harness/metrics/provenance-log.jsonl | tail -5` (downstream dùng bản global tương tự bước 0). Mỗi dòng khớp mang `writer_id`/`topic`/`ts_utc` (UTC tường minh)/`git_sha` — nguồn "vì sao" THỨ HAI cạnh `events.jsonl`/`scratch-log.jsonl` ở bước 0b, khác biệt quan trọng: **git-tracked, đi theo được khi clone sang máy khác** (2 nguồn kia hoặc gitignored-local hoặc không tự động toàn diện — xem `[[log-model]]`). Dùng làm CLUE bổ sung, không thay thế bước 0b. **BÁO CÁO, KHÔNG CHẶN.**

9. Append to `llmwiki/wiki/log.md`: `## YYYY-MM-DD — lint` with issues found/fixed vs flagged.

10. **Chốt neo** — `RUN: python3 harness/scripts/wiki-sync.py --mark-synced` (hoặc bản global như bước 0). Chỉ ghi khi nội dung wiki thực sự đổi (content-hash); tự xoá cờ `code-drift` đã rà. Vòng phản hồi phải khép: không chốt neo = lần check sau báo drift giả.

## Rules
- Fix automatically: missing links (step 2), index gaps (step 5).
- Flag, not resolve: contradictions, orphans, empty pages — need human decision.
- **Surgical update** (distill openwiki 060726): sửa trang stale = thay đúng câu sai, KHÔNG viết lại trang còn đúng; ưu tiên sửa 1 câu hơn thêm 1 đoạn.
- **Soft diff budget**: <5 file code đổi → sửa tối đa 1–2 trang wiki; thấy cần sửa >3 trang → dừng lại tự vấn vì sao trước khi sửa rộng.
- **Cấm formatting-only edit**: không reformat bảng, không chuẩn hoá dòng trống/wording khi nội dung xung quanh không sai — diff nhiễu là nợ cho reviewer.
- **Canonical home**: mỗi concept một trang chính chủ; trang khác chỉ nhắc ngắn + `[[wikilink]]`, không nhân bản giải thích.
- **No-op hợp lệ**: "wiki đã current, không sửa gì" là một kết quả lint thành công — ghi log rồi dừng, đừng sửa lấy có.

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
