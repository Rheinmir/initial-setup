# 040926-lint-drift-catchup
**Type:** draft
**Status:** proposed
**Tags:** lint, output-report, wiki-sync, drift
**Proposed:** 2026-09-04

## What
Bù drift tồn đọng sau 159 commit / 6 tuần kể từ neo `b226621183` (2026-07-20): đóng 3 cờ hạ tầng (medic docs, pattern-health, harness-stamp) và rà 12 trang wiki LIVE bị cờ `code-drift`, sửa đúng 1 câu.

## Output

**Hạ tầng — 3 drift đã đóng:**

| Drift | Trạng thái trước | Hành động | Sau |
|---|---|---|---|
| `medic --ci` docs | `✗ 1 docs CŨ so đĩa: build-overstack-docs` | regen `build-overstack-docs.py` | 0 fail · 0 warn · 16 ok |
| pattern-health thiếu file | `llmwiki/commands/serve` mất từ 1474a88 (2026-08-14, commit checkpoint) | khôi phục từ `1474a88^` | hash `e1846847abcedbea` khớp ĐÚNG BYTE với template global → xác nhận là xoá nhầm, không phải retire |
| harness-stamp lệch | stamp `1.3.54` ≠ global `1.3.65` | ghi lại stamp đúng cách installer làm (`poc-vendor-neutral/install.sh:240`) | `1.3.65` = repo `harness/version.json` = global |

**Wiki — 157 cờ, phân loại rồi mới đụng:**

| Nhóm | Số cờ | Xử lý |
|---|---|---|
| `sources/` + `draft/` | 108 | Không đụng — bản ghi lịch sử theo thời điểm (progression) |
| `archive/proposals/` + handover | 37 | Không đụng — đã archive |
| `concepts/` + `entities/` LIVE | 12 | **Rà từng trang** bằng `claim-receipts.py --check` |

Trong 12 trang LIVE, chỉ **1** ref chết là drift thật:

- `concepts/problem-tree.md` — proposal `020726-orca-issue-ledger-travel.md` đã được promote khỏi `draft/`, đường dẫn trong mục Origin còn trỏ `sources/draft/`. **Contradiction** → sửa đè 1 câu.

Các cờ còn lại KHÔNG phải drift, đã kiểm từng cái:

- `commit-dag-hub.md` → `a.txt`, `evidence-terminal-chain.md` → `harness/tests/fixtures/openclaude-usage.json`: nằm trong khối ví dụ có rào, không phải claim về file có thật.
- `skill-craft.md` → `skills/productivity/writing-great-skills/SKILL.md`: đường dẫn repo NGOÀI (`mattpocock/skills`), extractor không resolve được là đúng.
- `problem-tree.md` → `llmwiki/html/problem-tree.html`: câu văn đã tự nói "riêng repo framework dùng `fdk-problem-tree.html`" — vẫn đúng.
- `wiki-core-relations.md` → số 82/4/6: "migrate 82 trang" là sự kiện lịch sử 2026-07-02, không phải số đo sống (progression).
- Phần lớn cờ còn lại là **cờ đúng-trang-sai-lý-do**. Đo ngược "file nào sinh nhiều cờ nhất" cho ra thủ phạm thật, khác giả thuyết ban đầu: không phải việc dữ liệu đổi, mà là needle **basename** trong `map_suspects` — `log.py` khớp 64/240 trang, `scratch-log.jsonl` 58, `ledger.jsonl` 56, `SKILL.md` 42 (tên đó có ở 85 chỗ trong repo), `serve` 30 vì đó là một từ tiếng Anh.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/overstack.html` | modified (regen) |
| `llmwiki/commands/serve` | restored |
| `llmwiki/.harness-stamp` | modified (1.3.54 → 1.3.65) |
| `llmwiki/wiki/concepts/problem-tree.md` | modified (1 câu) |
| `llmwiki/wiki/log.md` | modified |
| `llmwiki/wiki/index.md` | modified |
| `llmwiki/wiki/.last-sync.json` | modified (chốt neo lại) |
| `harness/scripts/wiki-sync.py` | modified (lọc archive + basename định-danh) |
| `harness/tests/wiki-sync-test.sh` | modified (8 → 10 assertion) |

## Notes
- Invoked via: `/lint` skill
- Ngân sách diff mềm được tôn trọng: 157 cờ → rà 12 trang → sửa 1 câu. Trang không truy được về một thay-đổi-code cụ thể thì không đụng.
- **Đã sửa trong cùng phiên** (maintainer duyệt): `map_suspects` trong `wiki-sync.py` nay (1) không quét `sources/draft/archive/` và `sources/handover/` — bản ghi lịch sử mà chính /lint cấm sửa, cờ ở đó chỉ sinh việc không ai được làm; (2) chỉ dùng basename làm needle khi nó ĐỊNH DANH được — phải có đuôi và khớp ≤ 8 trang, ngược lại chỉ khớp path đầy đủ. Đo lại trên đúng neo 6 tuần: **159 → 115 cờ**; 2 cờ LIVE bị gỡ (`entities/repowise.md` do từ "serve", `concepts/skill-craft.md` do "SKILL.md") đúng là 2 cờ đã rà tay ra false positive ở trên. Recall thật giữ nguyên — khớp path đầy đủ không đụng tới.
- `harness/tests/wiki-sync-test.sh`: 8 → **10 assertion** (archive-không-cờ · basename-không-định-danh-không-cờ · path-đầy-đủ-vẫn-cờ). Bite-test: gỡ fix ra thì assertion mới đỏ đúng chỗ.

## Origin
- **Draft:** `wiki/sources/draft/040926-lint-drift-catchup.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
