---
name: dym-cti-expert-install-and-register
description: "Cài đặt & đăng ký với Claude Code. đưa cti-expert từ một thư mục git thành skill + 8 lệnh /cti + MCP server dùng được từ bất kỳ dự án nào."
disable-model-invocation: true
---

# Skill: dym-cti-expert-install-and-register — Cài đặt & đăng ký với Claude Code

**Vì sao dùng:** đưa cti-expert từ một thư mục git thành skill + 8 lệnh `/cti*` + MCP server dùng được từ bất kỳ dự án nào.
**Sinh ra cái gì:** một clone tại `~/.claude/skills/cti-expert`, symlink lệnh trong `~/.claude/commands/`, `.mcp.json` per-machine, và (tuỳ chọn) `.venv` cho lớp sâu.

---

## Bước 1 — Clone vào đúng chỗ

```bash
git clone https://github.com/7onez/cti-expert.git ~/.claude/skills/cti-expert
cd ~/.claude/skills/cti-expert
```

Vị trí không bắt buộc phải là `~/.claude/skills/` — mọi đường dẫn trong repo đều giải theo thư mục chứa `SKILL.md` (`AGENTS.md` §1). Nhưng `register.sh` mặc định symlink *vào* `~/.claude/skills/cti-expert`, nên clone thẳng vào đó là đường ít ma sát nhất.

## Bước 2 — Installer công cụ OSINT bên thứ ba

```bash
bash scripts/install.sh                # lõi: python deps + whois/dig/jq/exiftool + maigret/sherlock/holehe/...
bash scripts/install.sh --headless     # + Scrapling headless Chromium (~200 MB)
bash scripts/install.sh --go           # + subfinder/amass/gau/gitleaks/httpx (~150 MB)
bash scripts/install.sh --all          # + tất cả
```

Ba cờ này là **toàn bộ** cờ mà script nhận — kiểm bằng khối `case $arg in` tại `scripts/install.sh:47-51`; mọi đối số khác bị bỏ qua im lặng.

Chi tiết dễ nhầm: installer dựng venv của nó tại **`$HOME/.claude/skills/.venv`** (`install.sh:34`), tức là *ngoài* repo và dùng chung cho các skill. Đây **không phải** `.venv` mà pipeline sâu đọc — cái đó ở Bước 4.

Windows native: `powershell -ExecutionPolicy Bypass -File scripts\install.ps1` với cờ `-Headless` / `-Go` / `-All`.

## Bước 3 — Chọn MỘT trong hai cách đăng ký

### 3a. `register.sh` — symlink, không có hook

```bash
bash scripts/register.sh --dry-run     # xem trước, không đụng gì
bash scripts/register.sh               # thật
```

Làm đúng 3 việc (`scripts/register.sh`):
1. symlink repo → `~/.claude/skills/cti-expert`
2. symlink từng `commands/*.md` → `~/.claude/commands/` (8 file; file thật đã tồn tại thì **của bạn thắng**, script bỏ qua)
3. ghi `.mcp.json` ở repo root qua `intel.py mcp --write`

Vì tất cả là symlink, `git pull` cập nhật bản đã cài mà không cần chạy lại. Gỡ: `bash scripts/register.sh --uninstall` (giữ nguyên `.mcp.json`, `cases/`, `knowledge/`).

Cờ lạ → script thoát **2** (`register.sh:23-29`).

### 3b. Plugin — skill + lệnh + MCP + **hook an toàn** trong một đơn vị

```bash
claude
/plugin marketplace add ~/.claude/skills/cti-expert
/plugin install cti-expert
```

Khác biệt thật sự: `register.sh` **không cài được hook**, mà hai tính chất an toàn của repo lại nằm ở đó — `leakguard.py` chặn ghi dữ liệu case vào file tracked, `actionguard.py` hỏi trước hành động outbound. Xem [07-safety-gates.md](07-safety-gates.md). Nếu bạn định điều tra thật, chọn 3b.

Sau cả hai cách: **khởi động lại Claude Code** (skill và lệnh nạp lúc startup).

## Bước 4 — `.venv` cho lớp sâu (khuyến nghị, không bắt buộc)

```bash
cd ~/.claude/skills/cti-expert
uv venv && uv pip install -r requirements.txt
```

Không có `.venv` thì lớp stdlib vẫn chạy đầy đủ: collector, KB, pipeline tất định, mọi op thuần trong [04](04-cli-dispatcher.md). Cái bị khoá là:

| Cần `.venv` | Vì |
|---|---|
| `intel.py harness ...` (điều phối LLM) | `claude-agent-sdk` |
| MCP server `intel` (78 `@tool`) | `claude-agent-sdk` qua `intel_engine/harness/mcp-server` |
| `graph` / `network` / `gantt` / `graphviz` | `matplotlib`, `graphviz` (+ binary `dot`) |

`intel.py` tự chọn interpreter theo thứ tự `$INTEL_PY` → `.venv/bin/python` của repo → interpreter đang chạy (`scripts/backend/intel.py:60-64`).

## Bước 5 — Verify

```bash
python3 scripts/backend/backend.py status
```

Kết quả mong đợi khi đứng trong clone (chạy thật, không có `.venv`, không có key):

```
Intel backend: Tier 2 (CLI) — $INTEL_HOME=<repo>/intel_engine (via in-repo (self-contained))
  available: CLI (harness/cli.py, tools/kb/*.py), KB (knowledge/), BinaryPivot (/binary)
  unlocks:   /kb  /recall  /binary
```

Dạng máy đọc: `python3 scripts/backend/backend.py status --json` → object có `tier`, `tier_label`, `intel_home`, `method`, `trail[]`, `capabilities{cli,kb_tools,mcp_present,mcp_executable,knowledge_dir,binary_pivot}`.

`backend.py` chỉ nhận đúng 4 lệnh — `status` (mặc định), `check`, `env`, `path` (`backend.py:285`). Không có lệnh nào khác.

Trong Claude Code, kiểm tiếp: `/cti-status` (health check), `/mcp` (thấy server `intel`), `/hooks` (thấy 3 mục — chỉ khi cài theo 3b).

## Bẫy đã gặp

- **Lệnh `/cti*` không được nhận** → chưa chạy `register.sh` hoặc chưa restart Claude Code.
- **`.mcp.json` không ghi được** → chạy tay `python3 scripts/backend/intel.py mcp --write`; file đã tồn tại thì cần `--force`, nếu không nó thoát **5** (`intel.py:_cmd_mcp`).
- **`.mcp.json` chứa đường dẫn tuyệt đối** → cố ý gitignore, mỗi máy tự sinh. Đừng commit.
- **Windows** chạy `register.sh` từ Git Bash/WSL vì nó dùng symlink.
