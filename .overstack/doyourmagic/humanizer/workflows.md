# Humanizer — bộ workflow chạy được

Sinh từ một lượt khảo sát **read-only** repo `blader/humanizer` tại commit `e2e92e7` (2026-08-18), bản đóng gói `2.11.2`. Humanizer **không phải** thư viện hay CLI: nó là một file prompt Markdown duy nhất (`SKILL.md`, 456 dòng, 35 pattern) mà mọi agent hỗ trợ skill đều nạp được. Repo không có build step, không có `package.json`, không có dependency.

Bộ này chia theo **người dùng**, không theo tính năng:

- **Người dùng cuối (`01`–`05`)** — bạn muốn dùng Humanizer để chữa văn của mình.
- **Người sửa tool (`06`)** — bạn clone repo về để đổi chính prompt đó.

Trong nhánh người dùng lại chia tiếp theo **nơi gõ lệnh**, vì trộn hai loại là nguồn lỗi copy-paste phổ biến nhất: `01` và `06` gõ trong **terminal**; `02`–`05` gõ trong **khung chat của agent**.

| # | File | Việc nó làm | Gõ ở đâu | Nhánh |
|---|------|-------------|----------|-------|
| 1 | [01-install-shell.md](01-install-shell.md) | Cài bằng Skills CLI (`npx skills add`) hoặc copy tay một file `SKILL.md`; xem/cập nhật/gỡ | Terminal | Người dùng — cài đặt |
| 2 | [02-install-claude-plugin.md](02-install-claude-plugin.md) | Đường cài thay thế, chỉ cho Claude Code: `/plugin marketplace add` rồi `/plugin install` | Chat | Người dùng — cài đặt |
| 3 | [03-humanize-pasted-text.md](03-humanize-pasted-text.md) | Chế độ mặc định: dán văn bản, nhận nháp + phần soi + bản cuối; khớp giọng bằng mẫu văn | Chat | Người dùng — dùng hằng ngày |
| 4 | [04-humanize-files-and-embedded.md](04-humanize-files-and-embedded.md) | Chế độ file (ghi đè tại chỗ, chỉ văn xuôi) và chế độ embedded (chỉ trả bản cuối) | Chat | Người dùng — dùng hằng ngày |
| 5 | [05-tune-false-positives.md](05-tune-false-positives.md) | Chặn sửa quá tay: danh sách "không được gắn cờ", chi tiết người cần giữ, cách khoá phạm vi | Chat | Người dùng — tinh chỉnh |
| 6 | [06-contributor-validate-and-release.md](06-contributor-validate-and-release.md) | Chín cửa của validator, ba lệnh CI, luật thêm pattern, luật đồng bộ version | Terminal | Người sửa tool |

## Thứ tự nên chạy

Người mới: chọn **một** trong `01` hoặc `02` (đừng cài cả hai) → `03` → `04` khi cần chữa file trong repo → `05` ngay lần đầu thấy nó bào mất giọng của bạn.

Người sửa tool: nhảy thẳng `06`, không phụ thuộc `01`–`05`.

## Không có workflow CI cho người dùng

Cố ý bỏ. Humanizer không phát hành binary, không có lệnh `check`, không trả exit code nào để CI bám vào — sản phẩm của nó là một prompt do người bấm nút chạy trong agent. File `.github/workflows/validate.yml` trong repo chỉ kiểm **chính gói skill** và đã được mô tả trong `06`; nó không kiểm văn bản của bạn, nên không được copy vào CI dự án khác.

## Bộ này được kiểm chứng thế nào, không chỉ chép lại README

Mọi lệnh trong `01`–`06` đều đã đối chiếu với nguồn hoặc chạy thật, không lấy từ văn xuôi README:

- **Cờ của Skills CLI** (`-g/--global`, `-a/--agent`, `-s/--skill`, `-l/--list`, `-y`): chạy `npx --yes skills@1.5.20 add --help` và đọc output.
- **Đường dẫn cài thật**: cài thật vào một dự án git rỗng trong sandbox → `./.claude/skills/humanizer/` + `skills-lock.json` ở gốc; với `--agent '*'` thì có `.agents/skills/humanizer/` là bản thật và `.claude/skills/humanizer` là symlink trỏ về đó.
- **Bẫy `remove --agent '*'`**: chạy thật, CLI in `■ Invalid agents: *`, không gỡ gì cả — dù `--help` bảo dùng được `'*'`. Dạng chạy được là nêu đích danh agent, đã xác nhận bằng `--agent claude-code -y`.
- **Rác kèm theo khi cài**: liệt kê thật thư mục sau khi cài — CLI copy nguyên repo (`README.md`, `AGENTS.md`, `scripts/`, `.github/`), không chỉ `SKILL.md`.
- **Ba chế độ trả kết quả** (pasted / file / embedded) và quy trình 4 bước: `SKILL.md` → "How to return the result" và "Rewrite process".
- **Ranh giới "không bịa fact"**, quyền đè của mẫu văn lên §14, và ranh giới "chỉ sửa văn xuôi": trích thẳng từ `SKILL.md`, mục "What to do", "Match the writer's voice", "How to return the result".
- **Danh sách false positive và chi tiết người cần giữ**: `SKILL.md` → "Check for false positives".
- **Exit code của validator**: đọc các lời gọi `raise SystemExit(...)` trong `scripts/validate-package.py` (mọi lỗi đều là `1`, không có mã riêng theo loại), rồi **tái hiện thật** trên một bản copy bằng cách làm lệch version → in `Use one package version in all files: ['2.11.2', '9.9.9']`, `rc=1`. Đường lành cho `Humanizer package v2.11.2 is valid`, `rc=0`.
- **Chín cửa của validator**: đọc từng nhánh trong `scripts/validate-package.py`, gồm cả trần 500 dòng (`SKILL.md` hiện 456 dòng) và ràng buộc `range(1, 36)` ở hai chỗ.
- **Ba lệnh CI**: `.github/workflows/validate.yml`, và cả ba đã chạy thật trên bản clone — `claude plugin validate .` cho `✔ Validation passed`, `skills add . --list` cho `Found 1 skill`.
- **Yêu cầu phiên bản Claude Code**: README nêu `2.1.142+`; máy kiểm chứng chạy `2.1.260`.
- **Luật dành cho người sửa tool** (đồng bộ version 3 nơi, cấm `version` cấp gốc, Plain Language, giữ tính portable): `AGENTS.md`, đối chiếu chéo với đúng những gì validator kiểm chữ.
