---
name: dym-arex-skill-contributor-phat-trien-cli
description: "Contributor: sửa chính DisCo CLI. Bạn clone AREX-Skill để đổi công cụ, không phải để dùng nó."
disable-model-invocation: true
---

# Skill: dym-arex-skill-contributor-phat-trien-cli — Contributor: sửa chính DisCo CLI

**Vì sao dùng:** Bạn clone AREX-Skill để đổi **công cụ**, không phải để dùng nó.
**Sinh ra cái gì:** `cli/dist/` đã build, một lệnh `disco` link từ checkout, và một cây gate đã chạy xanh.

> Track này độc lập với `01`–`08`. Không cần cài bản release trước.

---

## 1. Bản đồ code (đây là chỗ dễ lạc nhất)

```text
AREX-Skill/
├── cli/                                    ← package npm @arex-skill/disco
│   ├── package.json                        ← MANIFEST DUY NHẤT của cả repo
│   ├── npm-shrinkwrap.json                 ← dependency được ghim
│   ├── vitest.config.ts                    ← root test trỏ về packages/coding-agent
│   ├── tsconfig.build.json / tsconfig.examples.json
│   ├── AGENTS.md                           ← luật bảo trì provenance/release
│   ├── docs/                               ← 30+ trang tài liệu CLI
│   ├── scripts/                            ← upstream-provenance · verify-package · copy-assets
│   └── packages/coding-agent/
│       ├── UPSTREAM_MANIFEST.json          ← kiểm kê provenance
│       ├── src/
│       │   ├── cli.ts                      ← entry process (bin → dist/cli.js)
│       │   ├── main.ts                     ← điều phối, 33KB
│       │   ├── config.ts                   ← APP_NAME · CONFIG_DIR_NAME · đường dẫn agent dir
│       │   ├── package-manager-cli.ts      ← install/remove/update/list/config
│       │   ├── cli/args.ts                 ← PARSER CỜ + printHelp()
│       │   ├── cli/repo-skills.ts          ← subcommand repo-skills
│       │   ├── core/repo-skills-library-manager.ts  ← clone/adopt/update/drift
│       │   ├── core/slash-commands.ts      ← 24 lệnh chat built-in
│       │   ├── modes/print-mode.ts         ← -p / --mode json, exit code
│       │   ├── modes/interactive/          ← TUI (interactive-mode.ts ~207KB)
│       │   └── disco/skills/               ← 17 skill bundled (15 meta + 1 operating + 1 shared)
│       └── test/                           ← ~60 file test vitest
├── skills/repositories/                    ← thư viện runtime 1000 skill + router
├── docs/                                   ← tài liệu cấp repo (song ngữ EN/zh)
├── examples/                               ← export session HTML + starter TOML
└── scripts/                                ← installer + build-from-source-link.sh
```

Không có manifest nào ngoài `cli/package.json` — repo **không** phải monorepo có workspaces.

## 2. Vòng lặp dev

```bash
cd cli
npm ci --ignore-scripts        # dùng npm-shrinkwrap.json đã ghim
npm run typecheck              # tsc --noEmit -p tsconfig.build.json
npm test                       # vitest --run + node --test scripts/upstream-provenance.test.mjs
npm run build                  # clean + tsc + copy-assets + chmod +x dist/cli.js dist/rpc-entry.js
```

Chạy một file test:

```bash
cd cli
npx vitest --run packages/coding-agent/test/disco-mode-skills.test.ts
```

Test chạy với `DISCO_OFFLINE=1`, `PI_OFFLINE=1`, `fileParallelism: false`, timeout 30s, reporter `dot` (`vitest.config.ts`). Không song song hoá — đừng ngạc nhiên khi nó chậm.

Link bản dev thành lệnh `disco` global:

```bash
cd ..
bash scripts/build-from-source-link.sh
```

## 3. Cổng đầy đủ trước khi publish

```bash
cd cli
npm run prepublishOnly
```

Nó chạy tuần tự 7 việc, đứt ở đâu dừng ở đó:

```text
verify:provenance → typecheck → test → test:examples → verify:rpiv-todo-contract → build → verify:package
```

| Script | Lệnh thật | Gác cái gì |
|---|---|---|
| `verify:provenance` | `node scripts/upstream-provenance.mjs --check` | `UPSTREAM_MANIFEST.json` khớp file trên đĩa. **Local-only**, không cần checkout Pi |
| `typecheck` | `tsc --noEmit -p tsconfig.build.json` | Kiểu |
| `test` | `vitest --run` + `node --test scripts/upstream-provenance.test.mjs` | Hành vi |
| `test:examples` | `tsc --noEmit -p tsconfig.examples.json` | Ví dụ trong `examples/` vẫn compile |
| `verify:rpiv-todo-contract` | `node scripts/verify-rpiv-todo-contract.mjs` | Hợp đồng TODO của RPIV |
| `build` | như trên | Ra `dist/` |
| `verify:package` | `node scripts/verify-package.mjs` | Audit đúng file được đóng gói |

Thử đóng gói:

```bash
cd cli
npm publish --dry-run --ignore-scripts
```

## 4. Provenance — chỗ dễ vỡ nhất

Phạm vi kiểm kê: `packages/coding-agent/src`, `packages/coding-agent/test`, `docs`, `examples`.

```bash
cd cli

# Sau khi CỐ Ý sửa file đã có trong 4 thư mục trên:
npm run refresh:provenance

# Khi THÊM file mới do DisCo sở hữu — phải duyệt tường minh từng file:
npm run refresh:provenance -- --add-local docs/dynamic-workflows.md
```

Luật (từ `cli/AGENTS.md`):
- Refresh **không được** âm thầm nuốt file lạ, chấp nhận file khai báo bị thiếu, hay đổi hash/mapping upstream. **Đọc diff manifest sau khi refresh.**
- Workflow upstream đầy đủ chỉ dùng khi **baseline Pi thật sự đổi**:
  ```bash
  node scripts/upstream-provenance.mjs --write --upstream-root /path/to/pi
  ```
  Cần checkout Pi sạch, pin đúng repo/tag/commit. **Không** dọn/sửa checkout Pi bên ngoài chỉ để release được `cli`.
- `scripts/build-from-source-link.sh` là **smoke build/link**, không phải cổng release.
- Git worktree **không cần sạch** để release npm, nhưng nên commit/tag trạng thái đã review để truy được về đúng revision.

## 5. Sửa skill bundled

Nguồn chân lý duy nhất: `cli/packages/coding-agent/src/disco/skills/`.

Khi sửa:
- Khai **rõ** input và output mong đợi;
- Xin xác nhận người dùng ở điểm tốn kém hoặc phá huỷ, trừ khi user đã uỷ quyền;
- Giữ thay đổi môi trường **cô lập**;
- Tách nội dung runtime sinh ra khỏi test và report;
- Tách việc cài meta-skill khỏi việc deploy graph mà nó sinh ra;
- Repo graph đi đường import chuyên biệt `~/.disco/agent/skills/repositories/repo-skills/` + rebuild router anh em — **không** đẩy routing metadata qua importer graph tổng quát;
- Cập nhật `cli/packages/coding-agent/src/disco/skills/README.md` khi tên/đường dẫn/mặc định/ranh giới đổi;
- **Sửa generator và template cùng lúc.** Hành vi router do `update_repo_skills_router.mjs` render ra **không được** sửa chỉ ở file Markdown đã commit.

Test skill bundled nằm ngay cạnh: `cli/packages/coding-agent/src/disco/skills/*.test.ts` (9 file, vd `export_repo_skills_to_agent.test.ts`, `skill-role-contracts.test.ts`).

## 6. Cần test gì khi đụng vào discovery/routing

Theo `CONTRIBUTING.md`, thay đổi ở đường phát hiện & định tuyến skill phải chứng minh được:
- skill ẩn được quản lý **có đăng ký** nhưng **không lọt** vào prompt ban đầu;
- router live **đè** fallback bundled;
- skill của project **chưa trust thì không nạp**;
- skill từ package đã cài **vẫn dùng được**.

## 7. Release asset của installer

Installer ở gốc repo được publish làm **GitHub Release asset**, không nằm trong tarball npm:

```bash
python3 scripts/prepare-disco-release-assets.py
```

Ghi ra `dist/disco-release-assets/`: `install-disco.sh`, `install-disco.ps1`, `SHA256SUMS`, `release-metadata.json`. Đính 2 file installer + `SHA256SUMS` vào GitHub Release tương ứng, **verify URL `releases/latest/download` ổn định** rồi mới sửa tài liệu công khai. Helper release npm chuẩn bị sẵn các file này nhưng **không bao giờ tự upload hay tự tạo GitHub Release**.

## 8. Cạm bẫy

- **Repo không có CI.** Không có `.github/workflows/` — mọi cổng phải tự chạy tay. `npm run prepublishOnly` là thứ gần nhất với "CI".
- **Không sửa tay `dist/`** hay asset runtime của binary standalone như thể chúng là source.
- **Docs song ngữ.** README gốc, installation, architecture, disco-meta-skills, refreshing-repo-skills, CONTRIBUTING, và skills/README là cặp EN/zh — sửa một bên phải sửa bên kia **trong cùng một change**.
- **`repository-catalog.md` nặng 673KB** — một trang data dùng chung phủ 1000 root và 2209 membership. Đổi catalog thì phải giữ đồng bộ count, grouping, path và phần tóm tắt trong README tiếng Trung.
- **Node phải >= 22.19.0.** Bản thấp hơn có thể `npm ci` được nhưng gãy ở runtime.

## 9. Lỗi drift đã phát hiện được (đọc mã, không đọc README)

`docs/disco-workflows.md` và `cli/docs/packages.md` (mục *Mode Targeting*) đều tài liệu hoá:

```bash
disco install <source> --for creator|researcher|both|default
```

**Cờ `--for` không tồn tại trong parser.** `package-manager-cli.ts` không có nhánh nào bắt `--for`; nó rơi vào `invalidOption` và lệnh in:

```text
Unknown option --for for "install".
```

rồi `process.exitCode = 1`. Usage string chính thức của lệnh là `disco install <source> [-l] [--approve|--no-approve]`. Đây là docs đi trước code (hoặc code đã lùi) — điểm đáng làm PR.

## Bước kế

`10-contributor-dong-gop-skill.md` nếu bạn đóng góp **skill** chứ không phải code CLI.
