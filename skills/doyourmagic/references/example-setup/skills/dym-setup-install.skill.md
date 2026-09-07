---
name: dym-setup-install
description: "Cài overstack vào dự án (bootstrap 1 dòng), cờ nào có thật ở đâu, ghi gì vào $HOME, xác nhận rào cắn, gỡ. Gọi khi: 'cài overstack', 'bootstrap', 'setup harness', 'gỡ overstack'."
---

# Skill: dym-setup-install — Cài overstack vào dự án của bạn

## When to use
- **Tại sao chạy:** biến agent của bạn thành cộng sự có luật cứng — 19 rule tất định chặn agent ghi bậy, 0 token, không cần API key.
- **Sinh ra gì:** `.harness/` (lõi luật) · `.llmwiki/` (khung wiki) · `.github/workflows/harness.yml` · `.pre-commit-config.yaml` · `.claude/settings.json` (merge) · `CAPABILITIES.md` · và một bản engine global ở `~/.claude/harness/`.
- Gọi qua hub: `/dym-setup install` — hoặc trực tiếp `/dym-setup-install` nếu đã symlink riêng.

## Steps
### 1. Lệnh chuẩn (một dòng)

Chạy **tại thư mục gốc dự án**:

```bash
curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash
```

Mặc định = **cả 3 trụ** (harness + skills global + llmwiki). Đây là mặc định thật, không phải cần thêm cờ: `bootstrap.sh` tự chèn `--full` khi bạn không truyền `--harness-only`.

Cờ đi sau `bash -s --`:

```bash
# chỉ harness, không đụng ~/.claude/skills
curl -fsSL .../bootstrap.sh | bash -s -- --harness-only

# ép vendor thay vì để nó tự dò
curl -fsSL .../bootstrap.sh | bash -s -- --vendor claude,opencode

# bỏ bước self-test cuối (nhanh hơn ~10s)
curl -fsSL .../bootstrap.sh | bash -s -- --no-verify
```

Đổi nguồn/nhánh (fork, canary):

```bash
HARNESS_BASE=https://raw.githubusercontent.com/<owner>/<repo>/<branch>/harness/poc-vendor-neutral \
  bash -c 'curl -fsSL $HARNESS_BASE/bootstrap.sh | bash'
```

### 2. ⚠️ `--harness-only` chỉ tồn tại ở `bootstrap.sh`

`bootstrap.sh` **dịch** cờ này rồi bỏ nó đi trước khi gọi `install.sh`. Nếu bạn đã clone repo và gọi thẳng installer:

```bash
bash harness/poc-vendor-neutral/install.sh .  --harness-only
# tham số lạ: --harness-only
# rc = 1  → KHÔNG cài gì cả
```

Đúng là:

```bash
bash harness/poc-vendor-neutral/install.sh .            # = harness-only
bash harness/poc-vendor-neutral/install.sh . --full     # = cả 3 trụ
bash harness/poc-vendor-neutral/install.sh . --with-wiki --no-verify
```

Danh sách cờ `install.sh` chấp nhận (nguyên văn từ `case` của nó): `--vendor <list>` · `--no-verify` · `--clean` · `--with-skills` · `--with-wiki` · `--full`. Tham số không bắt đầu bằng `-` được hiểu là `project_root`.

### 3. Lệnh này ghi vào `$HOME`, không chỉ vào dự án

Đọc kỹ trước khi chạy trên máy đang làm việc:

| Đích | Khi nào | Ghi gì |
|---|---|---|
| `<project>/.harness/`, `<project>/.llmwiki/` | luôn | lõi + khung wiki |
| `<project>/.claude/settings.json` | vendor `claude` được dò thấy | merge 6 hook (có backup `.bak`) |
| `~/.claude/harness/` | luôn (khi chưa có, hoặc bản cũ hơn) | engine global: `hooks/`, `harness/scripts/` (58 file), `fdk/tools/` (17 file) |
| `~/.claude/settings.json` | luôn | merge 8 hook global + 3 `permissions.deny` (có backup `.bak.*`) |
| `~/.claude/skills/` | **chỉ khi `--full` / `--with-skills`** | `npx skills add rheinmir/setup#orca --global --all` — **đè 87 skill global** |
| `~/.openclaude/skills` | khi có binary `openclaude` | symlink sang `~/.claude/skills` |

**Muốn thử mà không đụng máy thật** — cô lập `HOME` (đây chính là cách bundle này được đo):

```bash
SB=$(mktemp -d); mkdir -p "$SB/fakehome" "$SB/proj/.claude"
git -C "$SB/proj" init -q
HOME="$SB/fakehome" bash /path/to/clone/harness/poc-vendor-neutral/install.sh "$SB/proj"
# mọi thứ global rơi vào $SB/fakehome/.claude/, ~/.claude thật không bị đụng
```

### 4. 🔴 Bẫy dot-layout — ĐÃ SỬA Ở UPSTREAM (PR #114)

> **Đã sửa ở upstream.** Ba lỗi dưới đây được vá trong PR #114, merge vào `orca` ngày 2026-09-06 (commit `d8f1967`, đóng #111 · #112 · #113). Phần mô tả giữ nguyên vì nó vẫn đúng cho **bản cài cũ** trên máy bạn — bản cài chỉ hết lỗi sau khi bạn chạy lại installer. Cài từ `orca` từ nay: bỏ qua bản vá tay.

Cài từ `orca` kể từ `d8f1967` thì bỏ qua mục này. Nếu bản cài của bạn có trước đó, hoặc bạn không muốn chạy lại installer, dùng bản vá tay bên dưới.

**Triệu chứng:** cài xong, log in `TRẠNG THÁI 3 TRỤ ✓`, nhưng **không luật nào cắn** khi agent ghi bậy; và mọi `git commit` chạm file `.md` thì pre-commit đỏ với `can't open file`.

**Nguyên nhân:** với dự án downstream, installer chọn layout có dấu chấm (`.harness/`, `.llmwiki/`) vì `fdk/wiki` không tồn tại. Nhưng ba chỗ sinh dây vẫn hardcode đường **không** dấu chấm:

- `gen-converters.py` — `CLI = "harness/poc-vendor-neutral/bin/llmwiki-validate.py"`, `EVT = "harness/poc-vendor-neutral/bin/harness-events.py"`
- `install.sh` — heredoc pre-commit: `entry: python3 harness/poc-vendor-neutral/bin/llmwiki-validate.py files`
- `install-harness.sh` (global) — mọi hook gác bằng `[ -f "${CLAUDE_PROJECT_DIR:-.}/llmwiki/.harness-stamp" ]`, còn stamp thật nằm ở `.llmwiki/.harness-stamp`

Hậu quả đo được:

```bash
# đúng chuỗi lệnh trong .claude/settings.json
echo '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/raw/hack.md","content":"x"}}' \
| ( [ -f "$PWD/harness/poc-vendor-neutral/bin/llmwiki-validate.py" ] \
    && exec python3 "$PWD/harness/poc-vendor-neutral/bin/llmwiki-validate.py" claude-hook || exit 0 )
echo "rc=$?"      # → 0   KHÔNG chặn

# cùng payload, đường thật
echo '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/raw/hack.md","content":"x"}}' \
| python3 .harness/poc-vendor-neutral/bin/llmwiki-validate.py claude-hook
echo "rc=$?"      # → 2   [R1 no-write-raw] chặn ghi: llmwiki/raw/hack.md
```

Ba tầng gác đều trượt cùng lúc: hook project (im lặng), hook global (stamp guard sai), deny-glob global (`./llmwiki/raw/**` không phủ `.llmwiki/raw/**`). **Chỉ CI còn sống** vì nó gọi đường global tuyệt đối.

### Bản vá (chạy một lần, ngay sau khi cài)

```bash
# 1. hook Claude của dự án: harness/ → .harness/
python3 - <<'PY'
import json, pathlib, re
p = pathlib.Path(".claude/settings.json")
d = json.loads(p.read_text(encoding="utf-8"))
n = 0
for ev, defs in d.get("hooks", {}).items():
    for grp in defs:
        for h in grp.get("hooks", []):
            c = h.get("command", "")
            new = re.sub(r'(?<![\w.])harness/poc-vendor-neutral/', '.harness/poc-vendor-neutral/', c)
            if new != c:
                h["command"] = new; n += 1
p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"đã vá {n} hook")
PY

# 2. pre-commit
sed -i '' 's#python3 harness/poc-vendor-neutral/#python3 .harness/poc-vendor-neutral/#' .pre-commit-config.yaml   # macOS
# sed -i    's#python3 harness/poc-vendor-neutral/#python3 .harness/poc-vendor-neutral/#' .pre-commit-config.yaml # Linux

# 3. stamp cho hook global — symlink, một nguồn chân lý
mkdir -p llmwiki && ln -sf ../.llmwiki/.harness-stamp llmwiki/.harness-stamp
```

Bước 3 tạo `llmwiki/` rỗng chỉ để chứa symlink stamp. Nếu bạn không muốn thư mục đó, cách thay thế là sửa `~/.claude/settings.json` đổi mọi `llmwiki/.harness-stamp` → `.llmwiki/.harness-stamp` và `./llmwiki/raw/**` → `./.llmwiki/raw/**` — nhưng lần chạy installer sau sẽ ghi đè lại, nên symlink bền hơn.

### Nghiệm thu bản vá

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/raw/x.md","content":"x"}}' \
| python3 "$PWD/.harness/poc-vendor-neutral/bin/llmwiki-validate.py" claude-hook; echo "rc=$?"
# kỳ vọng: rc=2 + dòng [R1 no-write-raw]

pre-commit run --all-files 2>&1 | tail -3    # không còn "can't open file"
```

**Cách né bẫy ngay từ đầu:** nếu dự án bạn KHÔNG ngại thư mục trần ở gốc, tạo sẵn `harness/` và `llmwiki/` **trước** khi cài — `install.sh` thấy `$ROOT/.harness` không tồn tại thì giữ `HARNESS_DIR="harness"`. Nhưng dot-layout tồn tại có lý do (cổng thiết kế của dự án quét `**/*.html` sẽ vớ phải `overstack.html` 530KB), nên bản vá ở trên là đường khuyên dùng.

### 5. Xác nhận cài đúng

```bash
ls -d .harness .llmwiki .github/workflows/harness.yml .pre-commit-config.yaml CAPABILITIES.md
head -3 CAPABILITIES.md          # "87 skill · 19 rule · 23 fdk-tool · 68 harness-script"
cat .llmwiki/.harness-stamp      # {"schema": 1, "guarded_by": "1.3.68"}
bash .harness/poc-vendor-neutral/demo.sh       >/dev/null && echo "demo ok (13 assertion)"
bash .harness/poc-vendor-neutral/test-broad.sh >/dev/null && echo "broad ok (80 assertion)"
```

Tài liệu người-đọc đi kèm bản cài (self-contained, mở bằng `file://`, không cần mạng): `.llmwiki/html/overstack.html`.

**Claude Code: phải mở session mới (hoặc `/hooks` reload) thì hook mới nạp.**

### 6. Gỡ

```bash
bash .harness/poc-vendor-neutral/uninstall.sh .              # gỡ wiring + lõi
bash .harness/poc-vendor-neutral/uninstall.sh . --keep-core  # chỉ gỡ wiring
bash .harness/poc-vendor-neutral/uninstall.sh . --purge-bak  # xoá luôn file .bak
```

`uninstall.sh` chỉ đảo ngược phần installer thêm vào **dự án**: CI workflow, hook pre-commit, hook trong `settings.json`. Nó **không** gỡ `~/.claude/harness/` hay `~/.claude/skills/` — hai thứ đó dùng chung cho mọi dự án, xoá tay nếu thật sự muốn.

## Rules
- > **Đã sửa ở upstream.** Ba lỗi dưới đây được vá trong PR #114, merge vào `orca` ngày 2026-09-06 (commit `d8f1967`, đóng #111 · #112 · #113). Phần mô tả giữ nguyên vì nó vẫn đúng cho **bản cài cũ** trên máy bạn — bản cài chỉ hết lỗi sau khi bạn chạy lại installer. Cài từ `orca` từ nay: bỏ qua bản vá tay.
