---
name: tidy
disable-model-invocation: true
description: >-
  Dọn + validate kho nháp và render (wiki/sources/draft/*.md + llmwiki/html/*.html) khi phình to —
  ex docs-curate (đổi tên 2026-09-09 vì tên cũ không ai gọi). Ba tầng — PROMOTE bản chất quý lên wiki
  ADR/concept, ARCHIVE nháp đã xong (status done/implemented hoặc task done) vào archive/<nhóm>/ bằng
  git mv (TRACKED, không xoá, không giết draft còn proposed), KEEP canonical — rồi RE-INDEX. Gọi tay
  bất cứ lúc nào, hoặc khi đầu phiên báo "[tidy] draft/ có N file (> 10)". Trigger — "tidy",
  "dọn nháp", "dọn docs", "draft quá nhiều", "archive draft", "quét nháp lỗi thời", "/tidy".
---

# Skill: tidy

## When to use
- Đầu phiên thấy `🧹 [tidy] draft/ có N file .md tầng gốc (> ngưỡng 10)` — hook `session_start.py` hỏi user; user ĐỒNG Ý → chạy skill này. User TỪ CHỐI → bỏ qua, không hỏi lại trong phiên.
- User tự gọi `/tidy` khi thấy `draft/` hoặc `llmwiki/html/` lộn xộn, khó tìm, sợ mất bản chất quý.
- `/lint` bước 8c (docs-sprawl pulse) hoặc `medic` probe `tidy` báo warn.

## Vì sao 3 tầng (không chỉ "merge")
Cái QUÝ trong nháp là **quyết định / bài học / pattern** — nó phải lên **wiki** (concept/ADR, travel + được commit + được index). Còn nháp đã thi hành xong và render html là lịch sử → **archive** (giữ, không xoá). Tool tất định lo đếm + phân loại + dời + index; phần đọc-hiểu để promote là việc của agent.

## Steps
0. **Check (0 token, không đụng file):**
   ```bash
   python3 harness/scripts/tidy.py check          # downstream không có harness/: python3 ~/.claude/harness/harness/scripts/tidy.py check --root .
   ```
   Exit 3 = vượt ngưỡng (mặc định 10 file `.md` tầng gốc, thư mục con không tính; đổi bằng `--threshold N` hoặc env `OVERSTACK_DRAFT_THRESHOLD`).
1. **Plan (dry-run):** `python3 harness/scripts/tidy.py plan` → bảng KEEP / ARCHIVE / PROMOTE? kèm lý do từng file. Đọc kỹ cột lý do:
   - `OUTDATED — status done|implemented|…` hoặc `task T-… đã done` → nháp đã xong → ARCHIVE.
   - `⏱ TREO — status proposed/open…` → còn sống, **tuổi không phải lý do archive**; muốn dọn thì hỏi user quyết làm-tiếp hay reject (đổi `status:` trong frontmatter rồi chạy lại).
   - `PROMOTE?` = draft không status, không task → agent đọc rồi quyết.
2. **PROMOTE bản chất QUÝ vào wiki — làm TRƯỚC khi apply** (phán đoán của agent): với mỗi mục `PROMOTE?` và mỗi mục ARCHIVE có vẻ chứa quyết định/bài học **chưa có** trong wiki → viết `llmwiki/wiki/sources/adr/ADR-NNN-<slug>.md` (quyết định) hoặc `llmwiki/wiki/concepts/<slug>.md` (khái niệm), đúng frontmatter `type:` + `## Origin` trỏ draft; cập nhật `wiki/index.md` + `wiki/log.md`. Đã có trong wiki → chỉ archive. Không promote thứ tầm thường (report tiến độ, render trùng).
3. **Apply:** `python3 harness/scripts/tidy.py apply` — dời nhóm ARCHIVE vào `archive/<proposals|superseded|analysis|reports>/` (file tracked → `git mv`, git thấy **rename** không delete), sắp xếp cả file đã archive từ trước, rồi re-index (`build-docs-index` nếu có, `index_sync --fix`, `html/archive/INDEX.md`).
   - Tool **từ chối dời file tracked khi đích bị `.gitignore`** (dời = xoá khỏi repo) và in dòng gitignore cần bỏ. Đây là chủ ý, không phải lỗi.
4. **Verify + commit:** `git status` chỉ thấy rename/`archive/INDEX.md`; `python3 harness/scripts/wiki-health.py --wiki-dir llmwiki/wiki --fail-on broken` sạch (wikilink trỏ stem trong archive/ = resolved-frozen, không broken); `index_sync` xanh. Commit gồm ADR/concept mới promote + các rename. Append `wiki/log.md`.

## Rules
- **PROMOTE trước APPLY.** Archive giờ TRACKED nên promote-sau vẫn làm được, nhưng đừng để bản chất chôn dưới `archive/` mà không ai biết.
- **Archive = DỜI, KHÔNG XOÁ.** Không bao giờ `rm` nháp; `git mv` giữ history (`git log --follow`).
- **Tuổi không phải lý do archive** một draft còn `status: proposed/open/implementing`. Chỉ status/task đã xong (hoặc PLAN/seq đi theo SPEC đã archive) mới archive. Muốn dọn draft treo → người quyết, đổi status, chạy lại.
- Canonical (`overstack.html`, `index.html`, `wiki-graph.html`, `*-cheatsheet`, `*-health-dashboard`, `problem-tree`, `line-status`) không bao giờ archive. Html report có ngày: giữ 2 mốc ngày gần nhất (`--keep-dates N`), cũ hơn archive — html là render, không áp cho `.md`.
- Vai rõ: **tool** = đếm/phân loại/dời/re-index (tất định, 0 token); **agent** = promote (đọc-hiểu). Không lẫn.
- Wiki entry mới phải có `## Origin` + frontmatter `type` (R2/R9); cập nhật `wiki/index.md` + `wiki/log.md` (R3).
- Validator R7/R9/R18 và `wiki-health`/`index_sync` **bỏ qua `archive/`** (nháp đông cứng) — đừng "sửa cho đúng chuẩn" file trong archive, chúng là lịch sử.

## Test tất định
`bash harness/tests/tidy-test.sh` — 11 assertion: ngưỡng `>10` (thư mục con không tính), status done → archive, proposed cũ → keep, đích gitignored → không dời, đích tracked → git rename, vòng khép về exit 0.
