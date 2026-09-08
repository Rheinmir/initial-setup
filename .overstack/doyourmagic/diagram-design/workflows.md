# Diagram Design — bộ workflow chạy được

Sinh ra từ một lượt khám phá **read-only** repo `cathrynlavery/diagram-design`, tại commit `4451eadc484d76aa860edf3289c16fcd082dcdbf` (2026-09-02, `fix: consolidate reviewed repository corrections (#174)`), manifest `.claude-plugin/plugin.json` v`2.6.12`.

Diagram Design là một **plugin / agent-skill**, không phải thư viện. Nó dạy agent của bạn vẽ 39 loại sơ đồ thành file HTML tự chứa (inline SVG + inline CSS), mang **màu và font brand của bạn**, và vẽ lại được nguồn draw.io/Mermaid có sẵn.

Bốn sự thật quan trọng nhất, có được bằng cách **chạy thật** chứ không đọc README:

1. **Không có CLI để vẽ sơ đồ.** Toàn bộ việc vẽ diễn ra trong chat. Trong `skills/diagram-design/scripts/` chỉ có đúng **3 script Python stdlib thuần**: hai extractor import và một self-check output. Không `package.json`, không `pyproject.toml`, không bước build, không dependency runtime.
2. **Mã thoát chia làm hai quy ước khác nhau** trong cùng một repo. Hai extractor dùng **0/2** (`2` gộp chung: file hỏng, định dạng không hỗ trợ, **và** lỗi cách dùng argparse). `self_check.py` dùng **0/1**. Script gọi phải phân nhánh có chủ đích, và với `rc=2` thì phải đọc stderr mới biết lỗi thuộc loại nào.
3. **`/doctor` báo Playwright "không có" dù Playwright đã cài** — false negative có thật, tái hiện được. Probe tại `scripts/verify-doctor.py:158` dùng `playwright.__version__`, một thuộc tính mà package `playwright` **không có**; lệnh raise `AttributeError` và bị hiểu là "chưa cài". Đo trên máy có `playwright 1.58.0` và `sync_api` import sạch.
4. **`SKILL.md` còn đúng 4 byte trước trần cứng.** Cổng CI chặn ở 40.000 byte (`MAX_SKILL_BYTES = 40_000`, `scripts/verify-semantic-motion.py:23`); file hiện tại **39.996 byte**. Người đóng góp thêm một từ vào `SKILL.md` là gãy CI.

Bộ này chia theo **đối tượng dùng**, và trong nhánh người dùng còn tách tiếp theo **bề mặt gõ lệnh** — chat và shell không bao giờ nằm chung một file, để bạn không dán nhầm câu chat vào terminal.

| # | File | Mục đích | Nhánh · bề mặt |
|---|------|----------|----------------|
| 1 | [01-install-and-verify.md](01-install-and-verify.md) | Cài theo 7 host (Claude Code, Codex, Droid, Pi, Kiro, OpenCode, Cowork) + editable install; ba bằng chứng chạy thật; hai bẫy môi trường đã đo | Người dùng — cài đặt (hỗn hợp, có nhãn) |
| 2 | [02-brand-onboarding-and-profiles.md](02-brand-onboarding-and-profiles.md) | Cổng style-guide chặn sơ đồ đầu tiên; onboard brand từ URL/skill/folder/tay; thư viện profile và marker `.diagram-design` cho nhiều khách hàng | Người dùng — chat |
| 3 | [03-authoring-in-chat.md](03-authoring-in-chat.md) | Bảng 39 loại theo *thứ bạn đang thể hiện*; 7 semantic pattern; 4 mode motion; 4 núm chỉnh và 9 preset size | Người dùng — chat |
| 4 | [04-import-extractors-shell.md](04-import-extractors-shell.md) | `drawio_extract.py` và `mermaid_extract.py`: cờ thật, digest thật, ranh giới tin cậy, mã thoát 0/2 | Người dùng — shell |
| 5 | [05-import-export-slash-commands.md](05-import-export-slash-commands.md) | `/import-drawio`, `/import-mermaid`, `/export-diagram`, `/doctor`: cờ, mặc định, và các trường hợp **bị từ chối** | Người dùng — chat |
| 6 | [06-selfcheck-and-your-ci.md](06-selfcheck-and-your-ci.md) | `self_check.py` kiểm gì; đường xanh và đường đỏ thật; workflow CI **tối thiểu viết mới** cho repo của bạn | Người dùng — shell |
| 7 | [07-contributor-gates.md](07-contributor-gates.md) | ~48 cổng local, luật cấm bump version trong PR (ADR 0009), trần 40.000 byte, cách đọc từng cổng đỏ | Người đóng góp — shell |

## Thứ tự chạy gợi ý

**Người mới:** `01` → **`02` (đừng bỏ qua** — sơ đồ đầu tiên sẽ bị cổng style-guide chặn và bạn sẽ tưởng agent treo) → `03` để vẽ sơ đồ đầu tiên → `06` để khoá chất lượng.

**Đã có sơ đồ draw.io/Mermaid cần chuyển:** `01` → `02` → `05` là đủ. Chỉ xuống `04` khi bạn muốn *nhìn* nguồn có gì trước khi vẽ lại, hoặc cần cắm extractor vào script.

**Chỉ cần xuất PNG/SVG từ file có sẵn:** thẳng `05` §4. Nhớ cài Playwright trước; `--svg-only` thì không cần.

**Người đóng góp:** nhảy thẳng `07`; nó không phụ thuộc `01`–`06`. Nhưng đọc `04` trước, vì hợp đồng mã thoát của extractor là thứ `07` cấm bạn phá.

## Bộ này được kiểm chứng thế nào, không phải chép lại README

Mọi lệnh trong `01`–`07` đều được đối chiếu với mã nguồn, và phần lớn được **chạy thật** trên macOS (Darwin 24.6.0) với clone sạch — không `npm install`, không venv, không cài thêm gì:

- **Bề mặt lệnh và cờ**: đọc trực tiếp frontmatter + thân của 5 file `commands/*.md` và 4 file `prompts/*.md`, **không** lấy từ mục Install/Quickstart của README. Phát hiện được chênh lệch: Claude Code có **5** command, Pi chỉ có **4** prompt (thiếu `import-drawio`).
- **Chữ ký CLI**: các lời gọi `parser.add_argument(...)` có thật — `drawio_extract.py:857-870`, `mermaid_extract.py:1314-1326`, `self_check.py:369-370`. Không lấy từ prose.
- **Mã thoát**: đọc lời gọi `SystemExit`/`sys.exit` nguyên văn (`drawio_extract.py:59,897`; `mermaid_extract.py:63,1355`; `self_check.py:385,389`), rồi **đo lại bằng chạy thật**: file thiếu → `2`, cờ lạ → `2`, extractor xanh → `0`, self-check đỏ → `1`, self-check xanh → `0`.
- **Digest thật của extractor**: chạy trên fixture của chính repo — `scripts/fixtures/sample-architecture.drawio` (12 node / 8 edge, `budget: nodes OVER`), `sample-flowchart.mmd` (9n/7e, `cycle: True`), `sample-readme-with-mermaid.md` (2 block: flowchart + sequenceDiagram), `sample-adversarial.mmd` (rc=0, parse sạch không nổ). Mọi khối output trong `04` là copy từ terminal, không phải viết lại.
- **Hành vi thật của self-check**: chạy trên `example-architecture.html` → `OK`; chĩa vào `README.md` để lấy **danh sách lỗi thật** (remote reference, thiếu `role=img`, `title` không phải con đầu, `title`/`desc` rỗng). Các phạm trù kiểm liệt kê trong `06` lấy từ chính chuỗi `errors.append(...)` trong `self_check.py:185-312`.
- **Lỗi Playwright của doctor**: tái hiện ba bước — `importlib.metadata.version('playwright')` → `1.58.0`; `from playwright.sync_api import sync_playwright` → ok; `playwright.__version__` → `AttributeError`. Rồi đối chiếu với dòng probe `scripts/verify-doctor.py:158`. Đây là kết luận **đo được**, không suy diễn.
- **Cổng người đóng góp**: chạy thật 10 cổng và ghi rc kèm dòng tổng kết — `lint-skin.py --all --baseline` (`153 checked, 20 skipped, 0 findings`), `verify-geometry.py --all` (`155 checked, 0 findings`), `verify-plugin-package.py --current-only` (`Claude, Codex, Factory 2.6.12`), `verify-doctor.py` (**rc=1**, đỏ vì môi trường). Danh sách lệnh đầy đủ lấy từ bảng và chuỗi `&&` trong `CONTRIBUTING.md` §"Validation gates", đối chiếu chéo với `.github/workflows/ci.yml`.
- **Trần byte của `SKILL.md`**: `grep` ra hằng `MAX_SKILL_BYTES = 40_000` tại `scripts/verify-semantic-motion.py:23`, rồi `wc -c` ra `39996`. Con số "còn 4 byte" là phép trừ, không phải ước lượng.
- **Hợp đồng doctor và export**: `references/doctor.md` (ngưỡng Python 3.10, hai chế độ installed-skill vs maintainer-checkout, định dạng output) và `references/export.md` (thủ tục SVG/PNG, `omit_background=True`, bẫy escape `&amp;`, luật `?motion=static`).
- **Preset size và 4 núm**: bảng `viewBox` trong `references/output-spec.md` §2, không phải mô tả trong README.
- **Profile và marker**: `references/profiles.md` §"Paths and terms" (`~/.diagram-design/profiles/<slug>.md`, marker `<project-root>/.diagram-design`, ngữ pháp `profile: <slug>`) cộng 6 quy tắc bắt buộc trong `commands/profile.md`. Phát hiện thêm: verb `switch` **có thật** dù bị bỏ khỏi argument-hint.
- **CI ở `06` là bản viết mới, tối thiểu, có chủ đích** — **không** sao chép `.github/workflows/ci.yml` của Diagram Design. File đó có ~50 gate, ma trận 3 OS × 2 Python, Playwright ghim `1.62.0` với oracle so pixel; nó build và test *Diagram Design*, không phải cách bạn tích hợp Diagram Design.

**Chưa kiểm chứng được** (nêu rõ thay vì đoán):

- Các lệnh cài của từng host (`/plugin marketplace add`, `codex plugin add`, `droid plugin install`, `pi install`) cần đúng host đó và cần mạng — chép nguyên văn từ `README.md` §Install, chưa chạy được ở đây. Đường **editable install bằng symlink** thì kiểm được bằng cấu trúc thư mục và đã ghi kèm trong `01` §2.
- Luồng **onboarding từ URL** cần agent live và mạng; nội dung `02` dựa trên `references/onboarding.md` và bảng ánh xạ trong README, chưa chạy end-to-end.
- **Xuất PNG** chưa chạy thật (Playwright có trên máy nhưng chưa render); thủ tục trong `05` lấy nguyên văn từ `references/export.md`.
