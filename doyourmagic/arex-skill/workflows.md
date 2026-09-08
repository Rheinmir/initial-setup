# AREX-Skill / DisCo — bộ workflow chạy được

Sinh ra từ một lượt khảo sát **chỉ đọc** repo `VectorSpaceLab/AREX-Skill` (clone `--depth 1` vào scratchpad, không sửa một file nào trong repo đích).

**Repo này là hai thứ đóng chung một chỗ:**

1. **`disco`** — CLI/TUI agent nghiên cứu, npm package `@arex-skill/disco` v0.2.1, bin trỏ `dist/cli.js`, `engines.node >= 22.19.0`. Manifest **duy nhất** của cả repo là `cli/package.json` (không có monorepo workspaces).
2. **AREX-Skill Library** — 1.000 repo skill + một router định tuyến, nằm ở `skills/repositories/`, cài vào máy bằng `disco repo-skills install`.

Ngoài ra `cli/packages/coding-agent/src/disco/skills/` chứa 17 skill bundled: **15 meta** (Creator dùng để *chế tạo* skill), 1 `operating` (`repo-skills-router`), 1 `shared` (`workflow-authoring`).

Bộ tài liệu tách theo **đối tượng**, và trong track người dùng còn tách tiếp **lệnh terminal** với **lệnh chat trong TUI** — trộn hai loại vào một file là cách nhanh nhất để ai đó dán `/login` vào shell.

| # | File | Mục đích | Track / Loại lệnh |
|---|---|---|---|
| 1 | [01-cai-dat-disco.md](01-cai-dat-disco.md) | Cài `disco` (installer curl · npm/pnpm/bun · build từ nguồn), kiểm Node >= 22.19.0, cấu hình provider | Người dùng — setup · **shell** |
| 2 | [02-cai-thu-vien-skill.md](02-cai-thu-vien-skill.md) | `repo-skills install/status/update/router`, exit code làm cổng, đường lùi cài tay, cấu trúc thư viện | Người dùng — setup · **shell** |
| 3 | [03-chay-viec-researcher.md](03-chay-viec-researcher.md) | Chạy việc nghiên cứu thật: `-p`, `--mode json`, gọi thẳng `/skill:`, exit code print mode | Người dùng — hằng ngày · **shell** |
| 4 | [04-xuat-skill-sang-agent-khac.md](04-xuat-skill-sang-agent-khac.md) | Xuất repo skill sang `~/.claude` / `~/.agents`: cả đường Creator lẫn helper `.mjs` với transaction + `--resume` | Người dùng — tích hợp · **shell** |
| 5 | [05-creator-tao-repo-skill.md](05-creator-tao-repo-skill.md) | Creator: tạo · verify · refresh · extend một repo skill; ranh giới mode; 15 meta skill | Người dùng — chế tạo · **shell** |
| 6 | [06-creator-paper-to-skills.md](06-creator-paper-to-skills.md) | Distiller paper → skill: file TOML, 3 trường bắt buộc, `recovery_mode = "hard"`, đầu ra ở đâu | Người dùng — chế tạo · **shell** |
| 7 | [07-tich-hop-ci.md](07-tich-hop-ci.md) | Ghim commit thư viện và gác drift trong CI của **dự án bạn** (ví dụ viết mới, tối thiểu) | Người dùng — CI · **shell** |
| 8 | [08-lenh-chat-trong-tui.md](08-lenh-chat-trong-tui.md) | 24 lệnh chat built-in + quy ước `/skill:<tên>` — **không** dán vào terminal | Người dùng — hằng ngày · **chat/TUI** |
| 9 | [09-contributor-phat-trien-cli.md](09-contributor-phat-trien-cli.md) | Bản đồ code, vòng lặp dev, 7 cổng `prepublishOnly`, luật provenance, release asset | Contributor — code · **shell** |
| 10 | [10-contributor-dong-gop-skill.md](10-contributor-dong-gop-skill.md) | Đóng góp/refresh repo skill: file bắt buộc, rebuild router, catalog, yêu cầu PR | Contributor — skill · **shell** |

## Thứ tự chạy đề xuất

**Người mới dùng để nghiên cứu:** `01` → `02` → `03`. Đó là đường tối thiểu để có kết quả. `08` đọc song song ngay từ đầu vì `/login` nằm ở đó.

**Muốn dùng skill trong Claude Code/Codex mà không đổi agent:** `01` → `02` → `04`. Bỏ qua `03`.

**Muốn tự tạo skill:** `01` → `02` → `05` (nguồn là repo) hoặc `06` (nguồn là paper). `05` và `06` độc lập nhau.

**Cần tái lập kết quả về sau:** thêm `07` ngay sau `02`, trước khi có kết quả nào đáng giữ.

**Contributor:** vào thẳng `09` (sửa CLI) hoặc `10` (đóng góp skill). Hai file này không phụ thuộc `01`–`08`; `09` tự dựng bản dev qua `scripts/build-from-source-link.sh`.

## Bộ này được KIỂM CHỨNG thế nào, không phải chép lại README

Mỗi lệnh trong `01`–`10` đều đối chiếu với mã nguồn thật, không chỉ với tài liệu:

| Khẳng định | Nguồn đã đọc |
|---|---|
| Tên bin, script npm, `engines.node`, dependency | `cli/package.json` (manifest duy nhất — đọc **trước** mọi trang prose) |
| Toàn bộ cờ CLI và văn bản help | `cli/packages/coding-agent/src/cli/args.ts` → `printHelp()` |
| Subcommand `repo-skills` và cú pháp của nó | `cli/packages/coding-agent/src/cli/repo-skills.ts` → `parseRepoSkillsCommand()` / `printRepoSkillsHelp()` |
| **Exit code `repo-skills`**: `1` khi có drift, `2` khi sai cú pháp | `repo-skills.ts` — `process.exitCode = 1` khi `status.issues.length > 0`; `RepoSkillsLibraryError(..., 2)` ở mọi nhánh parse lỗi |
| **Exit code print mode**: `1` khi `stopReason` là error/aborted, `129` SIGHUP, `143` SIGTERM | `cli/packages/coding-agent/src/modes/print-mode.ts` — literal `exitCode = 1` và `process.exit(signal === "SIGHUP" ? 129 : 143)` |
| Clone shallow `--depth 1 --filter=blob:none`, thông điệp lỗi offline | `cli/packages/coding-agent/src/core/repo-skills-library-manager.ts` |
| 24 lệnh chat built-in (không đoán từ docs) | `cli/packages/coding-agent/src/core/slash-commands.ts` → `BUILTIN_SLASH_COMMANDS` |
| Quy ước `/skill:<tên>` | `core/agent-session.ts`, `modes/interactive/interactive-mode.ts`, `modes/rpc/rpc-mode.ts` — cùng dựng `` `skill:${skill.name}` `` |
| Cờ + exit code `0`/`2` của helper export | `.../disco/skills/import-repo-skills-to-agent/scripts/export_repo_skills_to_agent.mjs` — parser và literal `return 0` / `return 2` |
| Cờ + exit code `0`/`1`/`2` của rebuild router | `.../disco/skills/verify-repo-skill/scripts/update_repo_skills_router.mjs` — `parseArgs()` và `main()` |
| **Đúng 15** meta skill, không phải 17 | Grep `disco-role` trong từng `SKILL.md` dưới `src/disco/skills/`: 15 `meta` + 1 `operating` + 1 `shared` |
| **1000 / 2209 / 20 / 178** | Đếm thật: `wc -l repositories.jsonl` = 1000, `assignments.jsonl` = 2209, `repository-index.jsonl` = 1000 |
| Điều kiện lỗi của `build-from-source-link.sh` | Đọc chính script — 5 nhánh `exit 1` |
| Trường TOML của Distiller + mặc định | `examples/creator/paper-to-skills/distiller-run-config.toml` (và bản canonical trong `create-paper-skills/assets/`) |
| Đường dẫn agent dir, tên config dir | `cli/packages/coding-agent/src/config.ts` — `APP_NAME`, `CONFIG_DIR_NAME`, `getAgentDir()` |
| Cấu hình test | `cli/vitest.config.ts` — `DISCO_OFFLINE=1`, `fileParallelism: false`, timeout 30s |
| Luật provenance/release | `cli/AGENTS.md` |
| Yêu cầu PR, checklist skill | `CONTRIBUTING.md` |

**Kiểm chứng tách bạch consumer/contributor:** repo **không có `.github/workflows/`** — không tìm thấy file CI nào. Nên `07-tich-hop-ci.md` là ví dụ **viết mới có chủ đích** cho phía người dùng, không phải bản sao pipeline nội bộ (vì không có cái nào để sao). Cổng nội bộ của dự án là `npm run prepublishOnly`, nằm ở `09`, và cố tình **không** được đề xuất làm CI cho người dùng.

### Một chỗ docs lệch code, đã đối chiếu

`docs/disco-workflows.md` và `cli/docs/packages.md` (mục *Mode Targeting*) đều tài liệu hoá cờ `disco install <source> --for creator|researcher|both|default`. **Cờ này không có trong parser** — `package-manager-cli.ts` không có nhánh nào bắt `--for`, nó rơi vào `invalidOption`, in `Unknown option --for for "install".` và đặt `process.exitCode = 1`. Usage chính thức là `disco install <source> [-l] [--approve|--no-approve]`. Chi tiết ở mục 9 của `09-contributor-phat-trien-cli.md`.

### Điều KHÔNG được kiểm chứng

Không chạy `npm ci`, `npm test`, `disco repo-skills install`, hay bất kỳ lệnh nào cần mạng/model provider. Máy này đang chạy Node **22.17.0**, thấp hơn ngưỡng `>=22.19.0` của package. Mọi khẳng định về exit code, cờ, và số liệu ở trên đến từ **đọc mã và đếm file**, không từ thực thi. Trên máy này cũng **chưa có** bản tích hợp AREX-Skill nào từ trước để đối chiếu "usage thực tế trông thế nào" (`~/.disco` không tồn tại; `~/.agents/skills` có 95 skill nhưng không có `repositories/`).
