# overstack (`rheinmir/setup`) — bộ workflow chạy được

Sinh từ một lượt khảo sát **read-only** repo `Rheinmir/setup` nhánh `orca`, commit `5456eb3` (2026-09-04), cộng với **hai lần cài thật vào sandbox** (`HOME` bị cô lập) và một lần **đối chiếu với bản cài thật** đang nằm ở `/Users/giatran/orca/workspaces/hoh-autonomous/isonade`.

overstack không phải một CLI. Nó là **ba trụ** cắm vào dự án của bạn:

| Trụ | Là gì | Cài vào đâu |
|---|---|---|
| **Harness** | 19 luật tất định (R1–R19) + validator Python, không cần LLM, không cần API key | per-project `.harness/` + global `~/.claude/harness/` |
| **Skills** | 87 skill gọi bằng `/<tên>` trong phiên chat agent | global `~/.claude/skills/` (qua `npx skills`) |
| **llmwiki** | khung wiki `concepts/entities/sources/draft` + `raw/` inbox | per-project `.llmwiki/` |

## Cài dùng tại chỗ — một lệnh, chỉ nạp khi cần
```bash
mkdir -p .claude/skills && ln -sfn ../../doyourmagic/setup/skills/dym-setup .claude/skills/dym-setup
```
Chỉ hub `dym-setup` vào context (1 dòng). Gõ `/dym-setup` xem bảng slug, `/dym-setup install` để chạy một workflow. **Chế độ đặt tên:** mặc định `dym-<repo>-<slug>` (repo = `setup`). Mỗi thư mục `skills/dym-setup-<slug>/` là một SKILL.md tự chứa — promote lên repo chính bằng cách copy sang `skills/<tên-mới>/` rồi register (xem skill `doyourmagic` mục Promote). Sơ đồ luồng skill: [`flow.html`](flow.html).

Bundle chia theo **đối tượng người dùng**, không theo tính năng:

- **Nhánh tiêu thụ (`01`–`05`)** — bạn muốn *dùng* overstack trong dự án của mình.
- **Nhánh đóng góp (`06`)** — bạn clone chính `rheinmir/setup` để *sửa* framework.

| # | Skill (gọi qua hub) | Mục đích | Nhánh |
|---|------|----------|-------|
| 1 | [`/dym-setup install`](skills/dym-setup-install/SKILL.md) | Một dòng `curl \| bash`, cờ nào có thật ở đâu, file nào rơi xuống đâu, **và bản vá bắt buộc cho bẫy dot-layout** | Tiêu thụ — setup |
| 2 | [`/dym-setup guardrail-cli`](skills/dym-setup-guardrail-cli/SKILL.md) | Gọi validator từ shell: 3 mode, 19 luật, mã thoát **0/1/2 không đồng nhất** | Tiêu thụ — dùng hằng ngày (terminal) |
| 3 | [`/dym-setup agent-workflow`](skills/dym-setup-agent-workflow/SKILL.md) | Vòng `propose → gate → dispatch`: các lệnh `/<skill>` — **chỉ gõ trong chat**, không phải terminal | Tiêu thụ — dùng hằng ngày (chat) |
| 4 | [`/dym-setup ci`](skills/dym-setup-ci/SKILL.md) | Cắm luật vào CI **dự án của bạn** như cổng chặn thật, rẽ nhánh đúng mã thoát | Tiêu thụ — CI |
| 5 | [`/dym-setup maintain`](skills/dym-setup-maintain/SKILL.md) | Update bản mới, migrate dự án cũ, `--self-heal` với rc 0/3/4, gỡ sạch | Tiêu thụ — bảo trì |
| 6 | [`/dym-setup contributor`](skills/dym-setup-contributor/SKILL.md) | `/fdk` → `fdk-gate.py` (21 step) → `medic` → `/fdk-uat` canary → `/ship` | Đóng góp |

## Thứ tự chạy đề xuất

**Người mới dùng:** `01` (bắt buộc — gồm bản vá) → `02` để tự tay xác nhận luật CẮN → rồi `03` và `04` song song (đường chat và đường CI độc lập nhau) → `05` khi cần nâng bản.

**Người đóng góp:** vào thẳng `06`; nó không phụ thuộc `01`–`05`, vì repo framework dùng layout **không dấu chấm** và không dính bẫy ở `01`.

## Bốn cái bẫy đắt nhất — đọc trước khi gõ lệnh

> **Cập nhật 2026-09-07 (sau lượt fix #116–#119):** `orca` HEAD `16e1971` **xanh toàn bộ CI** lần đầu; `fdk-gate` 21/21; `template_version` 1.3.69 (installer tự cài lại global khi thấy version đổi — đã đo trên máy thật: `1.3.68 → 1.3.69`, smoke OK). Bẫy migrate (#106) và pre-commit trỏ engine đã gỡ cũng đã vá ở #117. Skill `/playwright-verify` có trong repo (#119, 88 skill).

> **Đã sửa ở upstream.** Ba lỗi dưới đây được vá trong PR #114, merge vào `orca` ngày 2026-09-06 (commit `d8f1967`, đóng #111 · #112 · #113). Phần mô tả giữ nguyên vì nó vẫn đúng cho **bản cài cũ** trên máy bạn — bản cài chỉ hết lỗi sau khi bạn chạy lại installer. Cài từ `orca` từ nay: bỏ qua bản vá tay.


1. **Cài xong nhưng KHÔNG luật nào cắn ở tầng phiên.** Installer đặt lõi vào `.harness/` (có dấu chấm) nhưng hook sinh ra lại trỏ `harness/` (không dấu chấm) → mọi hook Claude rơi vào nhánh `|| exit 0`, im lặng. Hook **global** thì gác bằng `llmwiki/.harness-stamp` trong khi stamp thật nằm ở `.llmwiki/.harness-stamp` → cũng bỏ qua. Chỉ CI còn sống. **Đã tái hiện 1:1 trên bản cài thật của máy này.** Bản vá 3 dòng: `01`. Riêng ba luật **R14 · R16 · R19** hardcode segment `llmwiki` ngay trong glob của luật nên bản vá đó không cứu — vá riêng ở `02` mục 5.
2. **`--harness-only` KHÔNG phải cờ của `install.sh`.** Nó là cờ của `bootstrap.sh`. Gọi thẳng `bash install.sh . --harness-only` → `tham số lạ: --harness-only`, **exit 1**, không cài gì. `install.sh` trần vốn đã là harness-only. Chi tiết: `01`.
3. **Mã thoát của validator không đồng nhất.** Cùng một vi phạm: mode `files` thoát **1**, mode `path` và `claude-hook` thoát **2**. Mode lạ, thiếu tham số, hoặc **file không tồn tại** đều thoát **0** (fail-open) — target sai đường dẫn sẽ không làm CI đỏ. Chi tiết: `02`, `04`.
4. **Một dòng `curl | bash` cũng ghi vào `$HOME`, không chỉ vào dự án.** Nó cài global harness ở `~/.claude/harness/`, merge `~/.claude/settings.json`, và với `--full` thì `npx skills add ... --global --all` đè lên `~/.claude/skills`. Muốn thử an toàn: cô lập `HOME`. Chi tiết: `01`.

## Bundle này được KIỂM CHỨNG thế nào, không chỉ diễn giải README

Môi trường đo: macOS 24.6.0, `python3` 3.9 (Command Line Tools), `git`, không mạng cho phần validator.

| Khẳng định | Nguồn kiểm chứng |
|---|---|
| Ba trụ + cờ `--harness-only/--clean/uninstall` | `README.md` + `harness/poc-vendor-neutral/bootstrap.sh:20-45` (khối dịch cờ `WANT_FULL`) |
| `install.sh` chỉ nhận `--vendor/--no-verify/--clean/--with-skills/--with-wiki/--full` | `install.sh:21-31` (`case`), nhánh `-*) … exit 1` |
| `--harness-only` gãy ở `install.sh` | Chạy thật: `bash install.sh $SB/proj --harness-only` → `tham số lạ: --harness-only`, **rc=1** |
| Layout dot `.harness/` + `.llmwiki/` cho dự án downstream | `install.sh:94-96` (`[ -d "$ROOT/fdk/wiki" ] \|\| { OVERSTACK_DIR=".llmwiki"; HARNESS_DIR=".harness"; }`) + cài thật, `find` ra `.harness/poc-vendor-neutral` |
| Hook Claude sinh ra trỏ `harness/` không dấu chấm | `gen-converters.py:25` (`CLI = "harness/poc-vendor-neutral/bin/llmwiki-validate.py"`) và `:49` (`EVT`); hàm `merge_claude_hooks` trong `install.sh` copy snippet nguyên văn, không rewrite đường dẫn |
| pre-commit cũng trỏ sai | `install.sh:153` — heredoc hardcode `entry: python3 harness/poc-vendor-neutral/…` |
| Hook im lặng KHÔNG chặn | Chạy thật đúng chuỗi lệnh trong `.claude/settings.json` với payload `Write llmwiki/raw/hack.md` → **rc=0**; cùng payload qua `.harness/…` → **rc=2** kèm `[R1 no-write-raw]` |
| pre-commit gãy TO (không im lặng) | Chạy thật entry của `.pre-commit-config.yaml` → `can't open file … harness/poc-vendor-neutral/…` **rc=2** |
| Hook global bị stamp-guard chặn | `~/.claude/settings.json` sinh ra 8 hook, tất cả gác `[ -f "${CLAUDE_PROJECT_DIR:-.}/llmwiki/.harness-stamp" ]`; installer ghi stamp ở `.llmwiki/.harness-stamp` → guard sai |
| Deny-glob global cũng trượt | `~/.claude/settings.json` → `permissions.deny = ["Edit(./llmwiki/raw/**)", …]`, không phủ `.llmwiki/raw/**` |
| Tái hiện trên bản cài THẬT, không chỉ sandbox | `/Users/giatran/orca/workspaces/hoh-autonomous/isonade`: `.harness/` có lõi, `harness/` không; stamp ở `.llmwiki/`; cả 6 hook project + 8 hook global đều trỏ đường không dấu chấm |
| CI vẫn sống | `.github/workflows/harness.yml` sinh ra tự clone framework rồi gọi `$HOME/.claude/harness/harness/poc-vendor-neutral/bin/llmwiki-validate.py` — đường global, đúng |
| 19 luật R1–R19 + `enforce_at` từng luật | Parse `harness/poc-vendor-neutral/policy.yaml` bằng `yaml.safe_load` — đếm từ đĩa, không đếm bảng trong README |
| Mã thoát validator 0/1/2 | `bin/llmwiki-validate.py:280,283,286,294` (`block_code`) + chạy thật cả 6 trường hợp (bad/good/path/mode lạ/không tham số/file thiếu) |
| Validator vẫn chấm đúng file trong `.llmwiki/` | Chạy thật trên `.llmwiki/wiki/concepts/bad.md` → bắt R2 + R9; glob `**/wiki/concepts/**` phủ cả layout dot — **lỗi nằm ở dây, không nằm ở luật** |
| Self-test 13 + 80 assertion | Chạy thật `test-broad.sh` → **80 PASS**. Nhãn `(68)` trong log cài và `broad 54 = 67` ở tên job CI đều là chuỗi cứng đã trôi — PR #114 sửa cả hai thành 13 + 80 = 93 |
| `install-harness.sh` rc 0/3/4 | `install-harness.sh:718` (`exit 3` — còn nợ), `:741` (`exit 4` — smoke fail), `:463` (`exit 0` global) |
| Global install chạy smoke thật | Log cài: `GLOBAL smoke OK: no_write_raw chặn đúng (rc=2)` (`install-harness.sh:461`) |
| 21 step của `fdk-gate` + exit 2 | Parse AST `harness/scripts/fdk-gate.py` → `len(STEPS) == 21`; mã thoát tại `:136,146,148` |
| `medic` chấm repo FRAMEWORK, không chấm dự án bạn | `fdk/tools/medic.py` — dòng `ROOT = Path(__file__).resolve().parents[2]` |
| `health-check.py` đòi `.template-manifest.json` | `health-check.py:159-178` + chạy thật trên dự án sạch → **rc=1**, `manifest không tồn tại` |
| 87 skill / 19 rule / 23 fdk-tool / 68 harness-script | `fdk/CAPABILITIES.md` dòng 3 (sinh bằng code) + `ls skills \| wc -l` = 87 |
| R14/R16/R19 chết dưới layout dot | Nạp `glob_to_regex` của chính validator rồi khớp thử: `**/llmwiki/patterns/**` **TRƯỢT** `.llmwiki/patterns/p.md` nhưng **KHỚP** `llmwiki/patterns/p.md`; `**/raw/**` và `**/wiki/concepts/**/*.md` vẫn khớp bình thường |
| Bản vá policy ở `02` mục 5 cứu R14 ở **hook per-project**; hook **global** (validator `patterns_guard.py`) còn hở, vá ở PR #115 | Chạy thật: trước vá `Write .llmwiki/patterns/p.md` → rc=0; sau vá + `gen-converters.py` → **rc=2** kèm `[R14 patterns-protected]`, YAML vẫn parse đủ 19 rule |
| `check_deny_write_bash` bỏ qua glob của luật | `bin/llmwiki-validate.py:89-93` — chỉ kiểm `"raw/" in cmd`. Chạy thật: bash ghi `raw/` bị báo **hai** dòng (R1 + R14); bash ghi `llmwiki/patterns/p.md` → **rc=0**, không chặn |
| HEAD của `orca` không qua chính `fdk-gate` của nó | Chạy thật trên clone sạch: `✗ THIẾU 5/21 step`, **rc=2**. Đỏ: `L4 wiki-health` (broken wikilink từ `entities/repowise.md`, quét 175 trang) · `overstack-docs current` · `task-lifecycle` · `bnal self-test wired` · `graph-engineering tests` (chỉ `ge-reachability-test.sh` đỏ, 6/7 còn lại PASS). `git status` sau khi chạy vẫn sạch → gate read-only |
| 18 probe của `medic` | Chạy thật `python3 fdk/tools/medic.py --list` → 18 dòng, rc=0 |
| CI của overstack **không** được bê nguyên vào `04` | `.github/workflows/harness.yml` của repo tự-cài framework, chạy fire-drill + self-test *của chính framework* — `04` viết mới, tối giản, cho người tiêu thụ |

**Chưa kiểm chứng, đã ghi rõ tại chỗ:** đường `--with-skills` (cần `npx` + mạng, và nó ghi đè `~/.claude/skills` global nên không chạy trong sandbox này); mọi lệnh `/<skill>` ở `03` (chỉ chạy trong phiên agent, không có mã thoát để đo); `05` phần `install-harness.sh --self-heal` (đọc mã + mã thoát, chưa chạy trên một dự án có nợ wiki thật); `06` phần `/fdk-uat` canary (cần quyền push nhánh lên remote).
