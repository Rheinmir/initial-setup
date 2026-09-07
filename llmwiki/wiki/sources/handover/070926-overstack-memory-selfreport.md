---
type: source
title: "Bàn giao phiên 889c2c4c — doyourmagic bundle-skill, repo dym, session-continue, memory chain, self-report"
status: open
tags: [handover, harness, memory, doyourmagic, self-report, session-continue]
timestamp: 2026-09-07
id: 070926-overstack-memory-selfreport
---

# Bàn giao — overstack, phiên 889c2c4c (2026-09-06 → 07)

Phiên này đẩy 16 PR vào `orca` (#114 → #129). Trạng thái lúc bàn giao: `orca` HEAD **`f2db8f5`**, `template_version` **1.3.74** trên remote. CI trên `f2db8f5`: **xanh** (2 workflow / 4 job — `check`, `repo health`, `validate file .md đổi`, `self-test lõi 93 assertion`). Issue mở: **18**, tất cả là frontier/research.

> Bước 0 bên dưới **đã xong** sau khi file này được viết lần đầu. Phiên sau bắt đầu thẳng từ **việc 1**.

## Đọc trước

- `fdk/wiki/concepts/fdk.md` — front-door phát triển framework (pre-flight, module map).
- `fdk/wiki/concepts/harness-enforcement-floor.md` — vì sao gate phải tất định; L2 (pre-commit) ≠ L4 (CI).
- `fdk/wiki/concepts/map-not-territory.md` — mới thêm ở #121, giải thích tại sao phải *tìm unknowns* trước khi prompt.

File này chỉ nói **làm gì tiếp**; kiến trúc nằm ở ba link trên.

## Việc tiếp theo

### 0. ~~Push nhánh `fix/overstack-check-path-agnostic`~~ — **ĐÃ XONG**

Merged qua **PR #129** → `orca` `f2db8f5` (2026-09-07 09:25 UTC). Đo lại trên worktree tại
`f2db8f5`: `fdk-gate` **21/21 pass**, `origin/orca` khớp local `0 0`. Không phải làm gì nữa.

Giữ mục này lại vì **lý do** đằng sau nó còn dùng được, và cái bẫy thì sẽ quay lại:

`overstack.html` nhúng wiki-graph, mà wiki-graph in **đường dẫn tuyệt đối của chính nó** (R16).
Đường đó khác theo máy ⇒ `--check` so nguyên văn là so **máy**, không phải so **nội dung**. Trước
khi vá, `fdk-gate` trên `orca` đỏ **20/21** với *bất kỳ ai clone về*:

```
fdk-gate: ✗ THIẾU 1/21 — overstack-docs current
build-overstack-docs.py --check → "overstack.html CŨ so với đĩa"
regen xong: diff = 0 dòng          ← nội dung y hệt, chỉ 2 dòng path khác
```

Bản vá chuẩn hoá dòng path ở cả hai vế trước khi so. Kèm `capability-stamp --update`
(1.3.73 → 1.3.74) — thiếu bump thì downstream so `1.3.73 == 1.3.73` rồi tưởng mình current,
không bao giờ biết có `self-report`/`okf-scan`.

**Bài học giữ lại:** gate nào so **nguyên văn artifact sinh ra** đều có lớp bẫy này. Kiểm bằng
"regen rồi diff" trước khi tin rằng artifact thật sự cũ.

### 1. Hiệu chỉnh ngưỡng `self-report` bằng dữ liệu thật

`harness/self-report.config.yaml` đang `verified: false`; mọi ngưỡng là **số đoán** — nhất là `coverage_floor: 0.34` và `min_sessions: 3`.

```bash
python3 harness/scripts/self-report.py --report          # xem hiện trạng
cat harness/metrics/self-report.jsonl                    # xu hướng qua các lần chấm
```

Cần ~20 phiên thật rồi xem finding nào là **báo động giả**. Chỉ đặt `verified: true` khi đã có ít nhất một finding dẫn tới sửa thật (ADAPT-CHECKLIST ghi trong chính file config).

**Vì sao ở vị trí 1:** cơ chế đã bật `raise: auto` — ngưỡng sai nghĩa là **tự mở issue rác lên repo mẹ**. Cooldown 7 ngày + trần 2/lượt chỉ giảm thiệt hại, không sửa gốc.

⏱ nửa ngày (chủ yếu là chờ tích phiên). Rủi ro: nếu chưa yên tâm, đặt `raise: propose` trước.

### 2. Chốt lại neo `wiki-sync` sau khi rà wiki một lượt

```bash
python3 harness/scripts/wiki-sync.py --check      # hiện: rc=2, "neo 1566eb9657 không còn trong lịch sử"
```

Neo mất hiệu lực sau squash-merge. Đây là lý do `self-report` báo `wiki-anchor-missing` (mức low). Phải **rà thật** rồi mới `--mark-synced` — xem cạm bẫy #4.

⏱ ~1 giờ nếu rà nghiêm túc. Rủi ro: chốt neo mà chưa rà = tự tay xoá tín hiệu drift.

### 3. Quyết định về 18 issue frontier còn mở

`#7 #10 #11 #12 #15 #71 #73 #74 #75 #81 #83 #84 #86 #88 #89 #93 #101 #102`. Đã `git grep` từng keyword: **không có code thật** trong repo cho chúng. Chúng là research/feature, không phải bug.

Việc cần làm không phải "đóng cho sạch" mà là **xếp ưu tiên**: cái nào còn đúng với hướng hiện tại, cái nào đã bị thực tế vượt qua (ví dụ #71/#73/#74 về blinding/QWK/auto-wire chống lạc quan giờ giao nhau với `self-report` vừa làm).

⏱ ~2 giờ đọc + gắn nhãn. Rủi ro: thấp.

## Việc dọn nhỏ

Gộp chung ⏱ ~30 phút, làm lúc nào cũng được:

- `pre-commit` chưa cài trên clone framework → `medic` báo `backstop L2 tắt`. Sửa: `pipx install pre-commit && pre-commit install`.
- `doyourmagic/setup/` trong worktree `isonade` chưa commit (nó là dự án tiêu thụ, không phải repo framework) — quyết định giữ hay bỏ.
- `rheinmir/dym` mới có 2 bundle (`setup/` dạng skill, `impeccable/` dạng doc cũ). Chuyển `impeccable/` sang dạng skill khi rảnh.

## Nợ mở, không chặn

| Việc | Trạng thái |
|---|---|
| `token-budget.py` / `code-logger.py` ghi vào `<root>/harness/` **trần** ở dự án layout dot | Đã xác nhận trên `isonade`; chưa sửa. Sửa phải đi cả cụm (cả `session-continue` đọc cùng đường) |
| `sub-agents` / `workers` / `graph-writes` trong token-budget | Không hook nào `record` → luôn 0, không dự đoán được. Vẫn chỉ là sổ |
| `okf-scan verify` chỉ thấy **tool-call** | Bác bỏ được "đã đọc" khi coverage 0%; **không** chứng minh được chất lượng đọc. Chưa có cách đo tốt hơn |
| `wiki-sync --mark-synced` tin lời agent | Không gì bắt buộc "rà xong mới được chốt neo". Giờ đã có `okf-scan --check`/coverage làm bằng chứng — có thể gác, **chưa làm** |
| `rates` trong `token-budget.config.yaml` | Số minh hoạ, chưa đối chiếu bảng giá thật. Với gói subscription thì `$` chỉ để xem — đã bỏ khỏi `auto_handover.triggers` |
| CI không chạy `fdk-gate` | Nên step `overstack-docs current` trôi được (bước 0). Cân nhắc thêm `fdk-gate --json` vào CI |

## Cạm bẫy — mỗi cái đã trả giá một lần trong phiên này

1. **`npx skills add <repo> --help` KHÔNG in help — nó cài thật.** Chạy trong worktree framework → tạo `.agents/`, `skills-lock.json`, 7 symlink trong `skills/` → `fresh-install-smoke` báo "SKILL RỚT", gate đỏ. Đúng lớp bẫy mà chính skill `doyourmagic` đã ghi. Dọn: `rm -rf .agents .claude/skills skills-lock.json llmwiki/skills/utils/dym-*.md` + gỡ symlink.

2. **R15 chặn commit ghi công AI.** `Co-Authored-By: Claude…` / `Generated with…` / 🤖 trong **commit message** làm pre-commit đỏ. Attribution để ở **PR body** (R15 chỉ quét commit message — ADR-016).

3. **SSH port 22 bị chặn trên mạng này.** `git@github.com` timeout. Đổi remote sang HTTPS; `gh` đã đăng nhập nên push được. Repo `dym` đã đổi.

4. **Sửa hook global mà không bump `harness/version.json` = user cũ không nhận.** `install.sh` chỉ cài lại tầng global khi version đổi. Đo thật: `1.3.68 → 1.3.69` mới kéo được guard mới về. Cùng lớp: `capability-stamp --update` (bước 0).

5. **Biến vòng lặp đè tham số.** `recall()` dùng `sid` cho cả tham số lẫn biến lặp → biên lai `okf-scan` ghi **nhầm phiên**. Chỉ lộ vì test kiểm biên lai theo đúng session. Bài học: test phải khoá *danh tính*, không chỉ *có/không*.

6. **Regex trên HTML đã escape.** Bản vá đầu của bước 0 khớp `class="foot"` trong khi trang nhúng dạng `class=&quot;foot&quot;` → **0/2 khớp**, "sửa" xong vẫn đỏ. Luôn đếm số khớp trước khi tin regex.

7. **Hook chỉ có hiệu lực ở session MỚI.** Mọi thay đổi hook cần mở phiên mới (hoặc `/hooks` reload). Đo: 10 phiên trên `isonade` không có biên lai nào chỉ vì chưa restart.

## Đã thử và BỎ

- **`index_roots` dạng list cho `.overstack.yaml`** (#49): `enrich_code()` index module-path theo **một** root; nhiều root làm id node va nhau. Ba lợi ích issue nêu đều đạt bằng `code_root` đơn + mỗi thư mục con tự khai file riêng. YAGNI — đã ghi lý do vào issue.
- **Mở issue cho "dương tính giả" của `no_write_raw` production**: probe lại thấy regex **neo theo path**, không phải grep chuỗi con. Lần chặn gặp phải là do dòng lệnh chứa nguyên văn `> .llmwiki/raw/…` (đúng đích R1). Không phải bug — đã sửa lại PR body thay vì mở issue.
- **Promote hub `dym-setup` lên repo chính**: hub chỉ có nghĩa **cạnh bundle** (nó đọc file con theo đường tương đối). Chỉ sub-skill mới promote được.
- **Đóng 18 issue frontier cho sạch bảng**: không có code thật cho chúng; đóng khống là nói dối. Để mở, xếp ưu tiên ở việc #3.

## Origin

- **Source:** phiên Claude Code `889c2c4c-de4c-411b-8d4e-08ad14eb5e25` (2026-09-06 → 2026-09-07), làm việc trên worktree `hoh-autonomous/isonade` + các worktree tạm trong scratchpad.
- **Commit trong phiên:** `orca` `aadea1b`…`f2db8f5` — PR #114 #115 #116 #117 #118 #119 #120 #121 #122 #123 #124 #126 #127 #128 #129 (tất cả merged; #129 mang bản vá gate + chính file này).
- **Repo phụ tạo mới:** `github.com/Rheinmir/dym` — kho bundle `/doyourmagic` đã chạy.
- **Concept liên quan:** `fdk/wiki/concepts/map-not-territory.md` · `fdk/wiki/concepts/harness-enforcement-floor.md` · `fdk/wiki/concepts/fdk.md` (wiki RIÊNG của framework — wikilink từ `llmwiki/wiki` không trỏ sang được, dùng đường dẫn)
- **Date:** 2026-09-07
