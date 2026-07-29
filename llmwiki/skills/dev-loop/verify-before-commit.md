---
name: verify-before-commit
description: Gate every commit — typecheck, lint, smoke, then promote draft to wiki
---

# Skill: verify-before-commit

## When to use
After any impl task, before `git commit`.

## Steps

**Pre-commit:**
1. `RUN: <type-check-cmd>` — detect from repo: `npx tsc --noEmit` (package.json) / `go build ./...` (go.mod). Fix all errors.
2. `RUN: <lint-cmd>` — detect: `npx eslint src/` / `go vet ./...`. Fix errors; note warnings.
3. `RUN: <test-cmd>` — detect: `npm test` / `go test ./...`. Fix failures.
3b. **Test tái hiện qc-code/qc-uiux (nếu có harness):** `RUN: [ -f harness/scripts/qc-regression.py ] && python3 harness/scripts/qc-regression.py --run` — chạy các test `qc-*` do `/qc-code` (+ `/qc-uiux`) sinh (tái hiện bug/antipattern đã tìm). ĐỎ = một lỗi đã fix nay tái phát, hoặc chưa fix. Tất định, 0-token, KHÔNG gọi LLM. Fail-open nếu chưa có test `qc-*` nào — không chặn.
4. **Trụ 3 gate (nếu có harness):** `RUN: [ -f harness/validators/task_lifecycle.py ] && python3 harness/validators/task_lifecycle.py --root .` — chặn cứng nếu task-ID đi sai state-machine (lùi/nhảy/né gate) hoặc draft trỏ task lạ. Không có file (install cũ) → bỏ qua. Đây là bản CỨNG của step 8 best-effort bên dưới.
5. Smoke check: verify golden path end-to-end.
6. Commit with message: *why*, not *what*.

**Post-commit — mandatory, never skip:**
6. Find draft in `llmwiki/wiki/sources/draft/` matching feature.
   - Promote to `llmwiki/wiki/concepts/` or `llmwiki/wiki/sources/` (permanent).
   - Add `## Origin` section: `Draft: <path>` / `Commit: <hash> — <msg>` / `Date: YYYY-MM-DD`
   - `CHECK: grep -l "## Origin" <promoted-file>` — must return file.
7. `RUN: echo "promoted" >> llmwiki/wiki/log.md` — then edit log properly; update `llmwiki/wiki/index.md`.
8. **Trụ 3 — đóng vòng đời (best-effort, fail-open):** draft có frontmatter `task: T-…` → `python3 harness/scripts/code-logger.py --task set <T-id> state=done note="<commit-hash>"`. Lệnh fail-open (thiếu `--task`/id → bỏ qua, không chặn commit). Xác nhận: `--task show <T-id>` in lifecycle proposed→approved→dispatched→done; `--audit` xác minh các transition nằm trong chuỗi bất biến.

> No draft (hotfix/refactor)? Note "no draft — <reason>" in log.md, skip step 6.
> No `task:` id (install cũ / propose bỏ qua mint)? Skip step 8 — fail-open, không phải lỗi.

All steps mandatory. No exceptions.

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
