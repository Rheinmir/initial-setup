# PoC — harness vendor-neutral (1 lõi, nhiều dây cắm)

Chứng minh kiến trúc trong `llmwiki/html/250626-harness-architecture-vs-current.html`:
**logic chặn KHÔNG nằm trong MCP, cũng KHÔNG nhúng vào 1 vendor — nó là 1 CLI lõi đọc
`policy.yaml`, và mỗi vendor chỉ là caller mỏng gọi vào (hoặc đọc config sinh ra từ policy).**

## Cài — 1 dòng (không cần clone repo)

Chạy NGAY trong thư mục dự án của bạn — **1 dòng này cài/UPDATE CẢ 3 TRỤ** (harness + skills + llmwiki), khỏi nhớ cờ:
```bash
curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash
```
Cuối lần chạy in **bảng TRẠNG THÁI 3 TRỤ** (mỗi trụ ✓ hay bỏ qua). Kèm cờ:
```bash
curl -fsSL .../bootstrap.sh | bash -s -- --harness-only          # CHỈ harness (bỏ skills + llmwiki)
curl -fsSL .../bootstrap.sh | bash -s -- --clean                 # cài MỚI = gỡ cũ rồi cài (vẫn đủ 3 trụ)
curl -fsSL .../bootstrap.sh | bash -s -- --vendor claude,opencode # ép vendor
```

> **Tốc độ:** harness + llmwiki **nhanh như code** (copy + mkdir). Trụ skills chạy `npx` (bước mạng, chậm hơn vài giây) — nay **mặc định bật** để 1 lệnh lo trọn; không muốn thì `--harness-only`. `bash install.sh` (đã clone repo) thì ngược lại: mặc định harness-only, thêm `--full` mới đủ 3.

> **Harness là HOOK, không phải MCP.** Cài xong KHÔNG thấy trong `/mcp` là ĐÚNG — kiểm bằng **`/hooks`** (hoặc khối `hooks` trong `.claude/settings.json`). `/mcp` chỉ liệt kê MCP server (tool cho model gọi), harness không nằm ở đó.
>
> **Phạm vi khác nhau:** harness + llmwiki cài **theo từng project** (hook trong `.claude/settings.json`, khung `llmwiki/` của project). Skills cài **GLOBAL** (`~/.claude/skills`, dùng mọi project). Bootstrap **mặc định cài cả 3** — dùng `--harness-only` nếu chỉ muốn lớp per-project, không đụng skill global.

## Luật được gác — đủ R1–R10

Cài xong, harness đăng ký **5 hook sự kiện** trong `.claude/settings.json`, phủ cả 10 rule của bản production:

| Rule | Gác bằng | Hook event |
|---|---|---|
| **R1·R2·R5·R7·R9** (no-write-raw · origin · folder · proposal · okf-frontmatter) | lõi `llmwiki-validate.py` — chặn lúc Write | **PreToolUse** |
| **R3** index-sync | `harness-events.py stop` — chặn kết thúc lượt nếu `index.md` lệch | **Stop** |
| **R4** log-append | `harness-events.py audit` — ghi `audit.jsonl` (+timestamp) **+ sinh `log.md`** | **PostToolUse** |
| **R6** verify-before-commit | pre-commit + CI gọi lõi (+ skill `/verify-before-commit`) | repo / skill |
| **R8** pattern-health | `harness-events.py session` — in trạng thái **+ check drift vs remote** | **SessionStart** |
| **R10** docs-gate | `harness-events.py docs` — mỗi N prompt **inject directive gọi `/docs-site-macos`** | **UserPromptSubmit** |

Chặn-cứng: **R1/R2/R3/R5/R7/R9**. Tự-động/báo-cáo/nhắc: **R4/R8/R10**. Cổng commit: **R6**.
Mọi hook sự kiện đều **fail-open** (lỗi hạ tầng → exit 0, không phá session).

> **3 trụ khi đẩy sang dự án khác:** Harness (10R, per-project) · Skills (workflow: propose/verify-before-commit…, global) · llmwiki (khung wiki, per-project). One-liner **`bootstrap.sh | bash`** (không cờ) lo trọn **CẢ 3 trụ** trong 1 lệnh; `--harness-only` nếu chỉ muốn trụ 1.
> URL trỏ nhánh `orca` → luôn kéo **bản mới nhất** (không outdate); chỉ hỏng nếu đổi tên branch/đường dẫn. Đổi nguồn: đặt env `HARNESS_BASE`.

**Dán nguyên khối này vào system prompt của AI** (agent tự cài khi được yêu cầu):

```text
# Harness guardrail
Khi user yêu cầu "cài harness / bật guardrail", chạy ở THƯ MỤC GỐC dự án:

curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash

1 dòng này cài/UPDATE CẢ 3 TRỤ (harness + skills global + seed llmwiki). Harness = validator
vendor-neutral: chặn ghi raw/, ép mọi wiki file có "## Origin"… qua hook native (Claude/opencode)
+ CI (.github/workflows/harness.yml) làm sàn. Cuối lần chạy in bảng TRẠNG THÁI 3 TRỤ.
Cờ tùy chọn (thêm sau `| bash -s --`):
  --harness-only             CHỈ harness (bỏ skills + llmwiki)
  --vendor claude,opencode   ép vendor (mặc định tự dò)
  --clean                    cài MỚI = gỡ cũ rồi cài
  --no-verify                bỏ chạy test
Sau khi cài: nhắc user mở session Claude mới (hoặc /hooks reload) để hook có hiệu lực.
Gỡ: bash harness/poc-vendor-neutral/uninstall.sh .   (giữ nguyên config khác của user)
Sửa luật: harness/poc-vendor-neutral/policy.yaml → chạy lại lệnh cài.
```

> Đã clone repo sẵn? Dùng `bash harness/poc-vendor-neutral/install.sh <dự-án>` (mục dưới). Gỡ: `uninstall.sh`.

## Chạy thử

```bash
bash demo.sh         # 13 assertion: lõi chặn đúng + sinh wiring 9 file
bash test-broad.sh   # 68 assertion: false-positive, normalize, bash, biên require_origin, files-mode, fail-open, GAPS
```

### Test rộng phát hiện gì (đáng chú ý)
- **False-positive guard PASS**: `coleslaw.md`, `draw.md`, `raws/`, `myraw/` (chứa chuỗi "raw") **không** bị chặn nhầm — glob khớp segment `raw/`, không khớp substring.
- **KNOWN GAPS (mục C, có chủ đích)**: lõi session soi *bề mặt* lệnh bash nên **KHÔNG** bắt: `python3 -c "open('…/raw/…','w')"`, `rm …/raw/…`, `sed -i <script> …/raw/…` (script chen giữa `-i` và file). Đây đúng là lý do **sàn đảm bảo phải ở CI/sandbox**, không phải regex hook — khớp kết quả verify 2026-06-25.
- **layer**: `raw/` bị chặn ở session nhưng **được phép** ở repo (con người commit raw/ hợp lệ) — do `enforce_at` trong policy, không hard-code.

## Cài vào dự án (1 lệnh)

```bash
bash harness/poc-vendor-neutral/install.sh /đường-dẫn/dự-án
#   [--vendor claude,opencode,cursor,codex,kiro]   # bỏ → tự dò
#   [--no-verify]
```
Tự làm B0–B4: copy lõi → dò vendor → `gen-converters.py` → **merge** `.claude/settings.json` + `opencode.json` (backup `.bak`), thả `harness.yml` vào `.github/workflows/`, tạo `.pre-commit-config.yaml`, copy advisory cho Cursor/Kiro → chạy `demo.sh` + `test-broad.sh`. Idempotent. CI + pre-commit luôn cài (sàn); adapter chỉ cài cho vendor có mặt. Sau đó mở session Claude mới để hook có hiệu lực.

## Gỡ / cài lại

```bash
bash harness/poc-vendor-neutral/uninstall.sh /đường-dẫn/dự-án   # gỡ ĐÚNG phần harness, giữ config của bạn
bash harness/poc-vendor-neutral/install.sh   /đường-dẫn/dự-án --clean   # cài MỚI = gỡ cũ rồi cài
```
`uninstall.sh` đảo ngược: gỡ CI, gỡ hook harness khỏi `.claude/settings.json` (giữ hook khác của bạn), gỡ glob deny harness khỏi `opencode.json` (giữ rule khác), gỡ pre-commit hook + advisory, xoá lõi. Có backup `.bak`. Cờ: `--keep-core` (chỉ gỡ wiring) · `--purge-bak`.

## Thành phần

| File | Vai trò |
|---|---|
| `policy.yaml` | **NGUỒN CHÂN LÝ DUY NHẤT** — luật (glob, layer). Dày tùy ý. Sửa ở đây. |
| `bin/llmwiki-validate.py` | **LÕI** vendor-neutral. Đọc policy, áp luật. Modes: `path` / `files` / `claude-hook`. exit 2=chặn (session), 1=fail (repo), 0=ok. fail-open khi lỗi hạ tầng. |
| `gen-converters.py` | Đọc policy → **sinh wiring** mọi vendor vào `out/`. Đây là "luồng cài đặt" B2/B3. |
| `out/…` | Wiring sinh ra (xem dưới). |

## Hai layer (policy quyết định, không phải code)

`enforce_at` trong policy lái hành vi:
- `session` (agent định ghi): `path` + `claude-hook` áp. `no_write_raw` ở đây → agent bị chặn ghi `raw/`.
- `repo` (commit/PR): `files` áp. `no_write_raw` **KHÔNG** ở repo → con người commit `raw/` vẫn hợp lệ; chỉ `require_origin` chạy. Demo mục 3 chứng minh điều này.

## Vendor wiring (sinh ra trong `out/`)

| Vendor | Cơ chế (đã kiểm chứng 2026-06-25) | File sinh ra | Gọi CLI? |
|---|---|---|---|
| Claude | PreToolUse hook → CLI `claude-hook` | `claude/settings.snippet.json` | ✅ |
| opencode | `permission.edit:deny` (native) + plugin gọi CLI | `opencode/opencode.json`, `opencode/plugin/harness.js` | native + (plugin ✅) |
| Antigravity | Permission Deny-rule theo path | `antigravity/permissions.snippet.txt` | native |
| Cursor | rules advisory (KHÔNG chặn ghi) | `cursor/.cursor/rules/harness.mdc` | — (nhắc) |
| Codex | AGENTS.md advisory | `codex/AGENTS.snippet.md` | — (nhắc) |
| Kiro | steering advisory | `kiro/.kiro/steering/harness.md` | — (nhắc) |
| **MỌI vendor** | **CI + pre-commit → CLI `files`** | `ci/harness.yml`, `pre-commit-snippet.yaml` | ✅ |

> **Sàn đảm bảo = CI + pre-commit**, vì rules advisory bị lờ ở mọi vendor non-Claude
> (opencode #29329, Cursor/Kiro/Antigravity tương tự). Session hook chỉ là phản hồi
> nhanh ở nơi vendor cho phép deny. MCP không cần ở đâu cả.

## Thêm luật mới

Sửa `policy.yaml` (thêm 1 rule) → `python3 gen-converters.py`. Mọi vendor cập nhật theo,
không đụng code adapter. Thêm *vendor* mới = thêm 1 nhánh ~15 dòng trong `gen-converters.py`.

## Lên production

- Gộp `policy.yaml` này vào `harness/policy.yaml` (đã cùng tinh thần R1/R2).
- Đóng gói `bin/llmwiki-validate.py` thành release pin version (xoá copy editable + sync hash-3-mốc).
- `gen-converters.py` gọi từ `install-harness.sh --vendor claude,opencode,…`.

## Cài từ một FORK — `bootstrap-fork.sh`

`bootstrap.sh` mặc định kéo mọi thứ từ repo gốc ở nhánh chính. Cài từ fork phải trỏ đúng **bốn** biến (`HARNESS_BASE` · `REPO_RAW` · `SKILLS_REF` · `HARNESS_REPO`) — sai một cái là bản cài lặng lẽ trộn hai nguồn mà cổng nghiệm thu vẫn xanh, vì nó chấm nhầm bản cũ. `bootstrap-fork.sh` gói cả bốn:

```bash
curl -fsSL https://raw.githubusercontent.com/dragonwar000/setup/graph-engineering/harness/poc-vendor-neutral/bootstrap-fork.sh | bash
```

Đổi nguồn không cần sửa file, và kiểm trước khi cài:

```bash
... | FORK_OWNER=<owner> FORK_REPO=<repo> FORK_REF=<ref> bash
... | bash -s -- --print-source      # chỉ in nguồn rồi thoát, không tải gì
... | bash -s -- --harness-only      # cờ của bootstrap.sh vẫn dùng nguyên
```

Script probe hai file nguồn trước khi cài, nên ref sai hoặc fork private báo lỗi 404 nói thẳng, thay vì biểu hiện muộn thành "cài xong mà thiếu file".
