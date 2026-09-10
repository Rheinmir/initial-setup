# ruflo — bundle doyourmagic

Nguồn: `git@github.com:ruvnet/ruflo.git` · bản đo npm `ruflo@3.40.0` (= `claude-flow@3.40.0`)
· chạy thật 2026-09-10 trên macOS 24.6 arm64. Chế độ đặt tên: **mặc định**.

ruflo là lớp **điều phối bên trong Claude Code**: MCP tool dựng topology/memory, còn việc
thật do **Task tool của Claude Code** làm. Nó không phải runtime chạy agent độc lập.

## Bảng skill

| skill | mục đích | nhánh | lệnh gọi |
|---|---|---|---|
| `dym-ruflo` | hub định tuyến | — | `/dym-ruflo` |
| `dym-ruflo-install` | cài pin scope + dấu chân 1.5 GB | tiêu thụ | `/dym-ruflo install` |
| `dym-ruflo-init` | init ghi gì vào dự án (241 file, 13 hook) | tiêu thụ | `/dym-ruflo init` |
| `dym-ruflo-route` | dùng hay không · 4 tầng điều phối | quyết định | `/dym-ruflo route` |

## Thứ tự chạy đề xuất
`route` → `install` (hộp cát) → `init` (dự án rỗng) → quyết định.

## Bẫy đắt nhất
1. **`ruflo init` chiếm `settings.json`** — thay `statusLine`, `model`, `permissions`,
   `env`, thêm 13 hook. Không hỏi, không backup.
2. **`--skip-claude` in thông báo sai** — vẫn báo "4 hook types enabled in settings.json"
   trong khi không tạo file nào.
3. **1.5 GB** và ghi `.claude-flow/` + `Library/` vào `$HOME` lúc cài.
4. **Đo rc qua pipe là sai** — `cmd | head` trả rc của `head`.

## Kiểm chứng thế nào

| khẳng định | ca chạy | kết quả |
|---|---|---|
| Cài được | `HOME=$S/home npm i -g --prefix $S/prefix ruflo` | rc=0 · prefix **1.5 GB** · home mọc `.npm/`, `.claude-flow/`, `Library/` |
| Phiên bản | `ruflo --version` | rc=0 · `ruflo v3.40.0` |
| Mã thoát | `--version` · `status` (chưa init) · lệnh sai | 0 · 1 · 1 |
| `doctor` chạy | `ruflo doctor` | rc=0 |
| init mặc định | `ruflo init --no-signup` trong git repo rỗng | rc=0 · **241 file .claude/** (148 command · 44 helper · 30 skill · 18 agent) · 8 file `.claude-flow/` · 6.0 MB |
| init chiếm settings | đọc `.claude/settings.json` | **13 hook / 10 loại**; ngoài hooks còn `statusLine`, `permissions`, `model`=`claude-sonnet-5`, `env`, `claudeFlow` |
| `--skip-claude` | `init --minimal --skip-claude --no-signup` | `.claude/` **4 thư mục rỗng, 0 file**, 108 KB — nhưng vẫn in "Hooks: 4 hook types enabled in settings.json" (sai) |
| Không trùng tên skill | `comm` 30 skill ruflo ↔ 86 skill overstack ↔ 8 skill Orca | **0 trùng** |
| Mô hình thực thi | `CLAUDE.md:88` | *"Never use MCP tools alone for execution — Task tool agents do the actual work"* |
| Quy mô | `find`/`du` | 129 MB repo · 2280 file nguồn · 25 gói `v3/@claude-flow/*` · 108 agent .md · `hooks.ts` 211 KB |

**Chưa kiểm chứng**: swarm/hive-mind chạy thật, neural, embeddings, ruvector (cần
PostgreSQL), daemon, MCP server, autopilot, 108 agent.

## Install (dùng tại chỗ)

```bash
mkdir -p .claude/skills && ln -sfn ../../.overstack/doyourmagic/ruflo/skills/dym-ruflo .claude/skills/dym-ruflo
```
