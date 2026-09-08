# Scientific Agent Skills — bộ workflow chạy được

Sinh ra từ một lượt khám phá **read-only** repo `K-Dense-AI/scientific-agent-skills` (commit `1e5eeff`, tag `v2.66.0`, `plugin.json` + `pyproject.toml` cùng version `2.66.0`). Đây **không phải một CLI**: nó là một **thư viện 163 Agent Skills** cho khoa học/nghiên cứu, đồng thời là một **Agent Plugins 1.0.0 package** (`plugin.json` + cây `skills/`). Repo tự nó chỉ mang **tooling nội bộ** để kiểm/quét skill (`scan_skills.py`, `scan_pr_skills.py`, `tests/run_all.py`).

Vì vậy bundle chia làm hai track theo **đối tượng**, không theo tính năng:

- **Track NGƯỜI DÙNG (`01`–`06`)** — bạn muốn cài skill vào agent của mình (Claude Code, Cursor, Codex, Gemini CLI…) và dùng chúng trong dự án riêng.
- **Track ĐÓNG GÓP (`07`–`08`)** — bạn clone chính repo này để thêm/sửa một skill và cần vượt qua các cổng CI của nó.

| # | File | Mục đích | Track |
|---|------|----------|-------|
| 1 | [01-cai-dat-skills.md](01-cai-dat-skills.md) | Ba đường cài đã kiểm chứng (`npx skills`, `gh skill`, Agent Plugins/clone tay), chọn subset thay vì cài cả 163, vị trí file thật sau khi cài | Người dùng — setup |
| 2 | [02-tham-dinh-truoc-khi-cai.md](02-tham-dinh-truoc-khi-cai.md) | Đọc skill trước khi cài, tra `docs/security-report.md`, danh sách 16 skill đang có finding CRITICAL/HIGH, tự chạy scanner | Người dùng — bắt buộc trước 01 |
| 3 | [03-dung-skill-trong-agent.md](03-dung-skill-trong-agent.md) | **Chỉ là prompt trong chat** — cách kích hoạt skill, prompt mẫu nhiều bước, 25 skill cần API key và khai báo env ở đâu | Người dùng — dùng hằng ngày |
| 4 | [04-chay-script-bundled-tu-shell.md](04-chay-script-bundled-tu-shell.md) | **Chỉ là lệnh shell** — chạy thẳng `skills/<name>/scripts/*.py` không cần agent, bảng exit code phi-chuẩn (3, 4) phải branch | Người dùng — dùng hằng ngày |
| 5 | [05-pin-va-cap-nhat.md](05-pin-va-cap-nhat.md) | Ghim theo tag/SHA, `gh skill update`, `npx skills update`, gỡ skill, metadata truy vết mà installer chèn vào frontmatter | Người dùng — bảo trì |
| 6 | [06-gate-trong-ci-cua-ban.md](06-gate-trong-ci-cua-ban.md) | Ví dụ CI **viết mới, tối thiểu** cho dự án của bạn: khoá version skill + validate spec + chặn drift. Không sao chép pipeline nội bộ của repo | Người dùng — CI |
| 7 | [07-dong-gop-them-sua-skill.md](07-dong-gop-them-sua-skill.md) | Layout thư mục, 6 field frontmatter hợp lệ, luật `strictyaml`, versioning, test đặt ở đâu, checklist trước PR | Đóng góp |
| 8 | [08-dong-gop-validate-test-scan.md](08-dong-gop-validate-test-scan.md) | Chạy `skills-ref validate`, `tests/_meta`, `tests/run_all.py`, `--isolated`, luật một-skill-một-process, scanner bảo mật | Đóng góp |

## Thứ tự chạy gợi ý

**Người mới dùng:** `02` **trước** `01` (repo tự khuyến cáo không cài hết, và 16/163 skill đang có finding CRITICAL/HIGH) → `01` cài subset → `03` và `04` độc lập nhau, chọn theo việc bạn làm qua agent hay qua shell → `05` khi cần khoá version → `06` khi muốn chặn drift trong CI.

**Người đóng góp:** nhảy thẳng `07` → `08`. Hai file này không phụ thuộc `01`–`06`.

## Bundle này được KIỂM CHỨNG thế nào, không phải chép lại README

Mọi lệnh trong `01`–`08` đều đối chiếu với source hoặc chạy thật trên máy này (macOS, Python 3.13 venv riêng, không cài `uv`):

| Khẳng định | Chứng cứ |
|---|---|
| Cấu trúc package, version | `plugin.json`, `pyproject.toml` (cả hai `2.66.0`) |
| 163 skill, 105 skill có `scripts/` | đếm thật trên cây `skills/` |
| `gh skill install` đặt file ở đâu | **chạy thật**: `--agent claude-code --scope project` → `.claude/skills/depmap/`; `--agent cursor` → `.agents/skills/depmap/` |
| Cờ `gh skill install/preview` | `gh skill install --help` trên `gh` 2.92.0, **không** lấy từ README |
| `npx skills` subcommand + cờ | `npx skills@1.5.23 --help`; `add --list` trả về "Found 163 skills" |
| Skill hợp lệ theo spec | **chạy thật** `skills-ref validate` cho cả 163 thư mục → 0 lỗi |
| Cổng CI nhanh nhất | **chạy thật** `pytest tests/_meta -q` → 10 passed, 1213 subtests, 1.82s, chỉ cần pytest |
| Luật một-skill-một-process | **chạy thật** `pytest tests/paper-lookup tests/ncats-arax` → bị `tests/conftest.py` từ chối |
| `run_all.py` chạy được từng skill | **chạy thật** `python tests/run_all.py paper-lookup` → 79 passed |
| Exit code phi-chuẩn | `--help` thật của `arxiv_atom.py` (exit 3) và `paginate.py` (exit 4), cộng `fail()` trong `skills/paper-lookup/scripts/_common.py:219` |
| 16 skill CRITICAL/HIGH | phân tích `docs/security-report.json` (`max_severity`), không phải bảng tóm tắt trong markdown |
| CI chặn ở ngưỡng nào | `.github/workflows/pr-skill-scan.yml:87` truyền `--fail-on HIGH`, ghi đè mặc định `CRITICAL` trong `scan_pr_skills.py:207` |
| Ví dụ CI cho người dùng | **viết mới**. `.github/workflows/*.yml` của repo là pipeline nội bộ của *chính repo* và cố ý không tái sử dụng |

### Ba chỗ tài liệu lệch code — đã kiểm và ghi lại

1. **`scripts/generate_skill_image.py` không tồn tại trong repo.** `AGENTS.md` dành hẳn mục "Skill diagrams" hướng dẫn chạy nó, nhưng `.gitignore` có dòng `/scripts/` nên toàn bộ thư mục đó không được commit. `find` trên cây đã clone: 0 kết quả. Đừng lên kế hoạch dựa vào lệnh này.
2. **`--agent gemini` trong README là sai.** Giá trị hợp lệ của `gh skill` là `gemini-cli` (xem danh sách trong `gh skill install --help`).
3. **README ghi `gh skill install <repo>` là "browse and install interactively"** — đúng khi chạy trong terminal tương tác, nhưng ở chế độ non-interactive (CI, agent) `gh` **bắt buộc** phải có tên skill.

Ngoài ra `AGENTS.md` nói workflow scan "failing on HIGH or above" — điều này đúng với **workflow**, nhưng mặc định của chính script là `CRITICAL`; chạy tay thì phải tự truyền `--fail-on HIGH` nếu muốn giống CI.
