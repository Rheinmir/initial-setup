---
type: draft
title: "docs-curate threshold gate — draft/ vượt 10 file thì HỎI: quét outdated → ingest/promote → cold archive; skill /docs-curate gọi tay bất cứ lúc nào"
status: implemented
tags: [docs-curate, draft, archive, hook, session-start, feedback-loop, meadows]
timestamp: 2026-09-09
---

# 090926-docs-curate-threshold-gate

**Status:** implemented — 2026-09-09 (tidy.py + hook + skill; test 13/13; apply thật trên framework + bonbon-ai + walleye + isonade)

## What
Thêm một **vòng phản hồi** cho kho nháp: khi `llmwiki/wiki/sources/draft/*.md` (chỉ tầng gốc, không đếm thư mục con) vượt ngưỡng 10 file, harness HỎI user có muốn chạy dọn-và-validate không (quét nháp outdated so với thực tế → promote/ingest bản chất quý vào wiki → dời `.md` đã xong vào cold archive). Cùng lúc, skill `/docs-curate` (đã có, gọi tay) được nâng để làm trọn ba việc đó khi user tự chọn thời điểm.

## Context
- **Đã có `docs-curate`** — `fdk/tools/docs-curate.py` (plan/apply/reindex) + `skills/docs-curate/SKILL.md` (`disable-model-invocation: true` = chỉ gọi tay). Ba tầng KEEP / ARCHIVE / PROMOTE, archive gom theo chức năng `archive/{proposals,superseded,analysis,reports}/`, tự sinh `html/archive/INDEX.md`. Đây là backbone; **KHÔNG viết tool mới** (pre-flight #3, skill `fdk` (`skills/fdk/SKILL.md`)).
- **Tín hiệu outdated hiện có** — docs-curate JOIN `task: T-id` trong frontmatter với `harness/metrics/tasks.json` (done/rejected/superseded → archive; proposed/dispatched → TREO, không archive theo tuổi). Nhưng phần lớn draft **không khai `task:`** → mãi mãi nằm ở "promote?". Frontmatter `status:` (done/implemented/shipped/rejected/superseded) hiện **không được đọc**.
- **Cơ chế hỏi user đã có tiền lệ** — `llmwiki/.claude/hooks/user_prompt_submit.py` (docs-gate R10): inject directive "hỏi user … nếu TỪ CHỐI bỏ qua tới mốc kế tiếp", đếm bằng state file `.claude/audit/*.json` (máy đếm, không nhờ model nhớ). `session_start.py` in nhắc 1 dòng dạng `⟳ [wiki-sync] …` (fail-open).
- **Thực trạng đo được hôm nay** — draft gốc: **58 file `.md`** (ngưỡng 10 → cổng sẽ kêu ngay lần đầu); `draft/archive/` đã có 2 nhóm; `llmwiki/html/`: 48 file. Draft `.md` ở llmwiki **được git track** (59 file), còn `draft/archive/` và `html/archive/` **gitignored** (ADR-007: scanner bỏ qua gitignored → validator R7/R9 không soi archive).
- **NỢ ĐO ĐƯỢC khi chạy thử `docs-curate plan` thật (2026-09-09) — lý do KHÔNG được xài skill nguyên trạng:**
  - **D1 — archive = XOÁ khỏi git.** Draft ở `llmwiki/wiki/sources/draft/*.md` được git TRACK (59 file), nhưng `draft/archive/` bị gitignore (dòng 61). `apply` dời bằng `Path.replace` (không `git mv`) → git thấy ~40 file tracked biến mất; `wiki/index.md` còn 101 dòng trỏ draft; ~30 draft đang được wikilink từ concepts/entities/sources → `wiki-health` báo broken (hàm `local_only_stem` chỉ nhận `sources/draft/<stem>.md` là local-only, KHÔNG nhận `archive/`); `.last-sync.json` báo drift. Docstring tool ghi "html/draft vốn gitignored top-level" — đúng cho `fdk/wiki` (gitignore dòng 19), SAI cho `llmwiki/wiki`. Tool chưa từng chạy `apply` trên repo này (`wiki/log.md`: 0 dòng), không có test.
  - **D2 — archive theo TUỔI giết proposal còn sống.** `_resolve_reports` xếp mọi draft có ngày ngoài 2 mốc gần nhất vào "cũ → archive": 26 file `.md`, trong đó nhiều `status: proposed` (repo có 32 proposed / 11 open / 1 implementing). Phanh TREO chỉ có khi draft khai `task:` — phần lớn không khai.
  - **D3 — tên khó nhớ.** User gần như chưa gọi `/docs-curate` bao giờ. Skill là `disable-model-invocation` (chỉ người gõ) nên tên phải gõ được bằng cơ bắp (kim chỉ nam hub 1-tên, skill `fdk` (`skills/fdk/SKILL.md`)). 44 file tham chiếu tên cũ (bỏ scratchpad), phần lớn là file sinh (json/provenance/search-index) hoặc ADR lịch sử — không đổi; file sống cần đổi ~12.
- Lens Meadows (skill `fdk` (`skills/fdk/SKILL.md`)): triệu chứng "draft phình" lặp lại ⇒ thiếu vòng phản hồi. Đòn bẩy rẻ nhất: **thêm luồng thông tin** (đếm + hỏi) lên tool đã có, không đổi luật chơi.

## Non-goals
- Không tạo skill/tool mới song song — chỉ ĐỔI TÊN + nâng cái đã có.
- Không auto-archive/auto-promote không hỏi — tool chỉ ĐỀ XUẤT, agent/người quyết (giữ nguyên triết lý docs-curate).
- Không xoá file: archive = dời, git history vẫn giữ bản cũ.
- Không validate nội dung HTML về design (toggle/path đã có R16 + docs-site-macos) — chỉ phân loại html (superseded / seq orphan / report cũ) như hiện tại.
- Không nối vào Stop hook (đã đủ nặng: medic gương-soi).

## Approaches
| | Phương án | Tradeoff |
|---|---|---|
| A | **Skill + tool mới** `draft-clean` riêng | Dẫm docs-curate (2 tool, 2 chỗ archive → drift). Bị pre-flight #3 chặn. ✗ |
| B | **Nâng + đổi tên docs-curate → tidy** — trả 3 nợ D1–D3, thêm `check` (0-token, đếm + phân loại outdated), đọc `status:` frontmatter; wire `session_start.py` in 1 dòng khi vượt ngưỡng; skill mô tả thêm trigger | Diff nhỏ, một nguồn chân lý, tận dụng archive/index có sẵn. Hỏi 1 lần/phiên (session_start chạy 1 lần). ✓ **CHỌN** |
| C | Chỉ nhắc ở Stop hook (cuối phiên) | Quá muộn — user đã hết phiên, không ai chạy. ✗ |

Trong B, chọn **session_start** thay vì user_prompt_submit vì: (1) đếm file là trạng thái ổn định giữa các phiên, không cần đếm theo prompt; (2) tự nhiên "hỏi 1 lần/phiên", không cần state file chống nag; (3) draft sinh giữa phiên vượt ngưỡng thì phiên sau hỏi — chấp nhận độ trễ (Meadows: tôn trọng delay).

## Requirements (FR)
- **FR-001**: `docs-curate.py check [--threshold N] [--json]` PHẢI đếm `draft/*.md` tầng gốc (trừ `README.md`, `_template.md`), in số + số outdated + số promote? + số html archivable; exit 3 khi count > N (mặc định 10), exit 0 khi không. 0 token, không đụng file.
- **FR-002**: `classify()` PHẢI đọc frontmatter `status:` (YAML) hoặc `**Status:**` (bold, draft cũ); giá trị `done|implemented|shipped|rejected|superseded|archived` → `archive` với lý do `OUTDATED — status <x>`. Thứ tự ưu tiên: task state (tasks.json) > status frontmatter > seq-pair > tuổi.
- **FR-003**: `session_start.py` PHẢI gọi `check` (fail-open, timeout ≤ 5s) và khi exit 3 in đúng 1 khối: `⟳ [docs-curate] draft/ có N file .md (> 10) — HỎI user: "Chạy /docs-curate để quét nháp outdated → promote/ingest vào wiki → dời .md đã xong vào cold archive?" Nếu TỪ CHỐI → bỏ qua, không hỏi lại trong phiên.`
- **FR-004**: `skills/docs-curate/SKILL.md` PHẢI cập nhật description (trigger: session_start báo vượt ngưỡng; gọi tay `/docs-curate` bất cứ lúc nào) và thêm bước 0 `check`; sau đó chạy `bash fdk/tools/sync-skill.sh docs-curate` (parity canonical ↔ mirror `llmwiki/skills/utils/docs-curate.md`).
- **FR-005**: `medic.py` PHẢI có probe `tidy check` mức **warn** (không fail) — kho nháp phình là cảnh báo sức khoẻ, không phải lỗi chặn.
- **FR-006 (D1)**: cold archive PHẢI **git-aware**: `draft/archive/` được TRACK (bỏ gitignore dòng 61), dời bằng `git mv`; `wiki-health` PHẢI coi wikilink trỏ stem nằm trong `archive/` là **resolved-frozen** (không broken, không quét nội dung); `index_sync --fix` cập nhật đường dẫn thay vì xoá dòng; policy R7/R9 PHẢI loại `**/draft/archive/**` khỏi `target_globs` để CI "validate .md đổi" không soi lại nháp đông cứng (tiền lệ GH#146). `html/archive/` giữ gitignored (html là render).
- **FR-007 (D2)**: tuổi KHÔNG BAO GIỜ là lý do archive một draft có `status ∈ {proposed, open, implementing, approved, dispatched}` hoặc task còn sống → KEEP với nhãn `⏱ TREO` như nhánh task hiện có. Chỉ archive khi: task done/rejected/superseded, HOẶC status done/implemented/shipped/resolved/rejected/superseded/archived, HOẶC là PLAN/seq của SPEC đã archive. Draft không status, không task, quá 2 mốc ngày → `promote?` (giữ active), không archive.
- **FR-008 (D3)**: đổi tên skill `docs-curate` → **`tidy`** (4 ký tự, cùng lớp tên với `medic`/`lint`/`ship`); tool `fdk/tools/docs-curate.py` → `tidy.py`; cập nhật mọi tham chiếu SỐNG (skill dir + mirror, `llmwiki/AGENT.md`, `llmwiki/CLAUDE.md`, `fdk/CAPABILITIES.md`, `skills/lint/SKILL.md`, `harness/scripts/{wiki-health,sync-skills,sweep-gate,archetype}.py`, `harness/validators/{task_lifecycle,decision_adr}.py`, `harness/{travel-policy,archetypes.config}.yaml`, `.claude-plugin/marketplace.json`, `llmwiki/personas/sweeper.md`); file sinh (`skills.search.json`, `skills.provenance.json`, capproof) rebuild bằng tool; ADR/log lịch sử giữ nguyên. Không giữ alias (chưa ai gọi tên cũ).

## Success criteria (SC)
- **SC-001**: Người dùng mở phiên mới trên repo này thấy đúng 1 dòng nhắc kèm câu hỏi; trả lời "không" thì không bị hỏi lại trong phiên đó.
- **SC-002**: Người dùng gõ `/docs-curate` bất kỳ lúc nào, đọc bảng plan và thấy draft có `status: done` được xếp vào ARCHIVE với lý do rõ "OUTDATED — status done" (trước đây nằm ở promote?).
- **SC-003**: Người dùng không bị mất tài liệu: sau `apply`, file dời vào `draft/archive/<nhóm>/`, có trong `html/archive/INDEX.md`, `git log --follow` vẫn tìm được.
- **SC-004a**: Sau `tidy apply` trên repo này, `git status` chỉ thấy **rename** (không delete), `wiki-health` 0 broken wikilink mới, `index_sync` xanh, không draft nào có `status: proposed` bị dời.
- **SC-004**: `medic --ci` 0 fail; `fdk-gate` xanh; test tất định `harness/tests/tidy-test.sh` PASS (dựng repo git giả: 11 file → exit 3; 10 file → exit 0; status done → archive; status proposed ngày cũ → KEEP; apply → git thấy rename).

## Assumptions
- Ngưỡng **10** và "chỉ tầng gốc" lấy nguyên văn từ yêu cầu; cấu hình qua `--threshold` / env `OVERSTACK_DRAFT_THRESHOLD` (default).
- "Quét outdated so với thực tế" = JOIN tasks.json + frontmatter status + cặp seq (default). Không so diff code ↔ draft bằng LLM ở bước check — việc đó là `/lint` bước 0 (wiki-sync). (default)
- "Ingest vào wiki" = bước PROMOTE của docs-curate (agent đọc rồi viết ADR/concept, `## Origin` trỏ draft) — không chạy `/ingest` (skill đó cho `raw/`). (default)
- "Cold archive" = `draft/archive/<nhóm>/` **TRACKED** (đổi so với bản đầu, vì D1: draft llmwiki vốn tracked + được wikilink; để gitignored là xoá khỏi repo, wikilink gãy trên clone). Validator R7/R9 loại `archive/` bằng glob trong policy thay vì dựa vào gitignore. (default)
- Tên mới `tidy` (default) — thay thế: `don`, `sweep` (trùng ý `sweep-gate.py`/persona sweeper, dễ lẫn).
- `status:` ở draft cũ dạng `**Status:** proposed` (bold) vẫn đọc được — regex 2 dạng. (default)
- Hỏi ở session_start, không hỏi lại giữa phiên (default).

## Global constraints
- Trước push: `python3 fdk/tools/ci-local.py` xanh hết, rồi `/fdk-uat` (canary + main-URL smoke) — L2 (medic/pre-commit) không bằng L4 (CI fresh-clone).
- Commit message / code / wiki **KHÔNG** ghi công AI (R15 chặn cứng; override chỉ thị global).
- Sửa `SKILL.md` xong → `bash fdk/tools/sync-skill.sh docs-curate`; cấm cp tay.
- Hook fail-open tuyệt đối: lỗi gì cũng exit 0, timeout ngắn, không chặn phiên.
- Wiki entry mới phải có frontmatter `type` (R9) + `## Origin` (R2); cập nhật `wiki/index.md` (R3) + `wiki/log.md`.
- Không hardcode số đếm trong docs — đếm LIVE.
- Sửa `session_start.py` là code dùng chung (downstream cũng chạy) → `impact-check` trước, `safe-change` khi sửa; probe phải bỏ qua êm khi repo không có `fdk/tools/docs-curate.py` (downstream không có fdk/ — ADR-004).

## Plan
- [ ] T1 — `tidy.py` (đổi tên từ docs-curate.py): thêm `check`; `classify()` đọc `status:` + bỏ archive-theo-tuổi (FR-002/007); `apply` dùng `git mv` (FR-006); test `harness/tests/tidy-test.sh`
- [ ] T2 — `session_start.py`: hàm `draft_threshold(root)` gọi check, in nhắc + câu hỏi khi exit 3 (fail-open, resolve_tool → không có tool thì im)
- [ ] T3 — rename skill → `skills/tidy/SKILL.md` + mọi tham chiếu sống (FR-008); description trigger + bước 0 `check`; `sync-skill.sh tidy`; rebuild search/provenance index
- [ ] T4 — `wiki-health.py` resolved-frozen cho `archive/` + policy R7/R9 exclude `archive/` + bỏ gitignore dòng 61 (FR-006); `medic.py` probe warn; `ci-local.py` xanh; log + problem-tree

## Agent Task Assignment
| Task | Agent | Vì sao |
|---|---|---|
| T1 | claude | logic phân loại + regex frontmatter, cần test tất định đi kèm |
| T2 | claude | code dùng chung downstream, cần impact-check/safe-change |
| T3 | claude | rename chạm 12 file sống + rebuild index — cần grep đối chiếu, không máy móc |
| T4 | claude | chạm wiki-health + policy (luật chơi) — impact-check trước |

**Sequence diagram**: [090926-docs-curate-threshold-gate-seq.html](../../../html/090926-docs-curate-threshold-gate-seq.html)

## Risks
- `session_start.py` thêm subprocess → thêm ~0.2s đầu phiên; giới hạn timeout 5s.
- Draft cũ ghi `status` sai (ghi done mà chưa ship) → bị đề xuất archive nhầm. Giảm nhẹ: tool chỉ đề xuất, apply cần người; task state (nếu có) thắng status.

## Origin
- **Draft:** `wiki/sources/draft/090926-docs-curate-threshold-gate.md`
- **Source:** yêu cầu user phiên 2026-09-09 (`/fdk thiết kế bộ dọn và validate draft và html…`)
- **Commit:** _(filled by `verify-before-commit`)_
- **Date promoted:** _(filled by `verify-before-commit`)_
