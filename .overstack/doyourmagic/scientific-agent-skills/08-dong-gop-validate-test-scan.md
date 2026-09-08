# 08 — Đóng góp: validate, test, scan

> Track ĐÓNG GÓP. Mọi lệnh chạy từ **gốc repo skill đã clone**.

**Vì sao dùng:** đây là các cổng CI thật. Chạy trước là biết PR đỏ ở đâu trong vài giây thay vì chờ vòng CI.
**Sinh ra cái gì:** kết quả pass/fail cục bộ khớp với cái CI sẽ nói, cộng comment markdown của scanner nếu bạn chạy wrapper.

---

## Thiết lập môi trường

Đường chính thức:

```bash
uv sync
```

**Nếu máy chưa có `uv`** (như máy đã dùng để kiểm chứng bundle này), cổng nhanh nhất vẫn chạy được bằng venv thuần, vì `tests/_meta` chỉ cần thư viện chuẩn + pytest:

```bash
python3.13 -m venv .venv
./.venv/bin/pip install pytest
./.venv/bin/python -m pytest tests/_meta -q
```

Repo yêu cầu Python **3.13+** (`pyproject.toml` → `requires-python = ">=3.13"`).

## Cổng 1 — spec conformance

```bash
# một skill
uv run skills-ref validate skills/<name>

# cả bộ, đúng như CI làm
for d in skills/*/; do uv run skills-ref validate "$d"; done
```

Đã chạy thật trên cả 163 thư mục (qua venv thuần, không `uv`): **0 lỗi**. Output khi hợp lệ: `Valid skill: skills/depmap`, exit 0.

`.github/workflows/skill-spec-validation.yml` chạy đúng thứ đó ở mọi PR chạm `skills/`, **cộng** các luật repo mà `skills-ref` không kiểm: `metadata.version` có mặt, `allowed-tools` là chuỗi ngăn cách bằng dấu cách, scalar trong `metadata` được quote, và cảnh báo khi vượt 500 dòng.

Không có `uv`? `skills-ref` cài được thẳng:

```bash
./.venv/bin/pip install "skills-ref @ git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref"
./.venv/bin/skills-ref validate skills/<name>
```

Nó còn hai subcommand hữu ích khi debug: `read-properties` (in property của skill dạng JSON) và `to-prompt` (sinh XML `<available_skills>` mà agent thực sự thấy).

## Cổng 2 — `tests/_meta`, tín hiệu nhanh nhất trong repo

```bash
uv run --with pytest python -m pytest tests/_meta -q
```

**Đã chạy thật:** `10 passed, 1213 subtests passed in 1.82s`. Thuần thư viện chuẩn, không package khoa học nào, vài giây.

Nó chạy hợp đồng cấu trúc dùng chung lên **mọi** skill và đỏ khi:

- một skill ship `scripts/` mà không có suite ở `tests/<name>/`, hoặc không có entry trong `tests/skill-requirements.toml`;
- frontmatter sai chuẩn, vượt 500 dòng, có test hoặc bytecode dưới `skills/`;
- link nội bộ không giải được, script không parse được;
- có `eval`/`exec`/`os.system`, có module trùng tên thư viện chuẩn, có đường dẫn cục bộ hardcode;
- shell script không hợp lệ;
- manifest Agent Plugins trôi khỏi `pyproject.toml`;
- các bản sao byte-identical (cây OOXML của docx/pptx/xlsx; bộ sinh schematic AI ở năm skill) trôi khỏi nhau.

Nó **không** phải một trong các process per-skill: nó cố ý trải trên tất cả cùng lúc, an toàn vì nó **không bao giờ import code skill, chỉ parse**.

`.github/workflows/skill-tests.yml` chạy cổng này ở mọi PR — skill có script chưa test **không** vào được repo.

## Cổng 3 — suite của từng skill

```bash
# một skill
uv run --with pytest python -m pytest tests/<name> -q

# tất cả, mỗi skill một process, sau cổng repo-wide
uv run --with pytest python tests/run_all.py
```

**Đã chạy thật:** `python tests/run_all.py paper-lookup` → `79 passed, 47 subtests passed in 1.73s`, tổng kết `1 passed, 0 failed`.

### Luật MỘT SKILL MỘT PROCESS — không phải sở thích

Thư mục `scripts/` của các skill chiếm tên module top-level trần — **32 skill ship `scripts/_common.py`** — nên gom hai skill vào một interpreter khiến `_common` giải về skill nào import trước, và bạn **âm thầm test nhầm file**.

`tests/conftest.py` từ chối phiên như vậy. Đã kiểm chứng bằng cách cố tình vi phạm:

```
$ pytest tests/paper-lookup tests/ncats-arax -q
ERROR: cannot collect 2 skills in one process: their scripts/ directories share
module names (_common.py and friends), so imports would resolve to the wrong skill.
Run one skill at a time with `pytest tests/<skill>`, or the whole tree with
`python tests/run_all.py`.
```

`tests/run_all.py` fork một process cho mỗi skill, nên nó là cách đúng để chạy nhiều hơn một.

### Cú pháp `run_all.py` (parse tay, không dùng argparse)

```bash
python tests/run_all.py                     # mọi skill dưới tests/, có kèm _meta
python tests/run_all.py qutip pydicom       # chỉ các skill nêu tên — BỎ QUA _meta
python tests/run_all.py -- -x --tb=long     # mọi thứ sau `--` chuyển thẳng cho pytest
python tests/run_all.py --isolated          # mỗi suite một môi trường uv riêng
python tests/run_all.py --isolated scanpy qiskit
```

Chi tiết quan trọng đọc từ `tests/run_all.py:130`: **chỉ lượt chạy đầy đủ mới chạy `tests/_meta`**. Nêu tên skill nghĩa là bạn muốn skill đó, không phải một cuộc kiểm toàn repo. Trước khi push, hãy chạy một lượt không tham số ít nhất một lần.

Quy ước exit của `run_all.py`:

| Tình huống | Xử lý |
|---|---|
| suite pass | tính là passed |
| suite không collect được test nào (pytest exit **5**) | báo là **"empty"**, **không** làm đỏ lượt chạy |
| suite fail | in `FAILED <name> (pytest exit <code>)`, tổng exit = 1 |
| `--isolated` mà skill không có `[skills.<name>]` | in hướng dẫn, tính skill đó là fail |
| `--isolated` mà không có `uv` trên PATH | `sys.exit` kèm thông báo, không chạy gì |

**"Empty" không phải pass.** Suite collect 0 test lặng lẽ trôi qua; nếu bạn vừa thêm test mà thấy `empty`, tên file/hàm của bạn sai quy ước.

### `--isolated`: một môi trường cho mỗi skill

Môi trường project **cố ý không** mang package khoa học của các skill: các pin upstream loại trừ nhau. `AGENTS.md` liệt kê xung đột thật: `opentrons` cần `numpy<2`; `esm` chặn `transformers` dưới bản mà skill `transformers` nhắm; `geniml` và `spikeinterface` ghim `zarr<3` chọi với `zarr-python` 3.x; `bioservices` chặn `lxml<6` chọi `matchms`; còn `pytdc`, `molfeat`, `deepchem`, `histolab`, `vaex`, `ete3` mỗi cái cần interpreter cũ hơn 3.13.

```bash
python tests/run_all.py --isolated                 # mọi suite, mỗi cái một env
python tests/run_all.py --isolated scanpy qiskit   # chỉ các skill này
```

`uv` cache wheel toàn cục nên lần chạy sau dựng lại mỗi môi trường trong vài mili-giây.

**Lượt `--isolated` đầy đủ KHÔNG chạy trong CI** — vài môi trường cần CUDA toolchain, JDK, hoặc MATLAB cài sẵn. Chạy nó trước một release, hoặc khi bạn đụng vào hợp đồng dùng chung.

## Hợp đồng dùng chung — đừng viết lại thứ đã có

`tests/_contract/` giữ các assertion mà mọi skill đều chia sẻ, được `tests/conftest.py` đăng ký thành module `skill_contract`:

```python
import skill_contract

# mọi script argparse phải trả lời --help; tự skip khi thiếu package,
# chạy thật dưới --isolated
CliHelpTests = skill_contract.cli.help_test_case(SKILL_ROOT)

# cho script kiểu thư viện có ví dụ trong `if __name__ == "__main__"`
DemoBlockTests = skill_contract.cli.demo_test_case(SKILL_ROOT, ("doe_designs.py",))
```

- `structure` — frontmatter, giới hạn 500 dòng, không test/bytecode dưới `skills/`, link giải được, script parse được, không `eval`/`exec`/`os.system`, không che module thư viện chuẩn, không đường dẫn cục bộ hardcode, shell script hợp lệ. **`tests/_meta` đã chạy toàn repo — đừng lặp lại trong suite của skill.**
- `cli` — hai case `--help` và demo-block ở trên.
- `office` / `schematic` — hành vi cho các file mà nhiều skill ship bản sao byte-identical.

Suite của một skill vì thế **chỉ nên chứa thứ đặc thù của skill đó**.

## Cổng 4 — quét bảo mật

```bash
# wrapper của repo, cần SKILL_SCANNER_LLM_API_KEY (đọc .env)
uv run python scan_pr_skills.py skills/<name> --fail-on HIGH

# hoặc CLI upstream, không qua wrapper
uv run skill-scanner scan skills/<name> --use-behavioral
```

`.github/workflows/pr-skill-scan.yml` chạy wrapper cho các skill đã đổi ở mọi PR và post một sticky comment. **Nó truyền `--fail-on HIGH`** (dòng 87), trong khi mặc định của script là `CRITICAL` (`scan_pr_skills.py:207`) — chạy tay mà muốn khớp CI thì phải tự truyền. Bảng exit code đầy đủ nằm ở [02](02-tham-dinh-truoc-khi-cai.md).

Biến môi trường cho lượt quét toàn repo (`scan_skills.py`, workflow hằng tuần):

| Biến | Mặc định | Tác dụng |
|---|---|---|
| `SKILL_SCANNER_LLM_API_KEY` | — | key cho LLM analyzer |
| `SKILL_SCANNER_LLM_MODEL` | `claude-opus-5` | model id |
| `SKILL_SCAN_WORKERS` | `8` | số skill quét song song |
| `SKILL_SCAN_FULL` | — | đặt `1` để buộc rescan toàn bộ |
| `SKILL_SCAN_MAX_AGE_DAYS` | `30` | buộc rescan toàn bộ khi lần cuối đã quá số ngày này |

```bash
uv run python scan_skills.py --full --workers 4 --max-age-days 30
```

Nó ghi **cả hai** `docs/security-report.md` và `docs/security-report.json` — markdown link sang JSON để lấy ngày quét từng skill, còn JSON là cache mà lượt sau đọc. **Luôn sinh cùng nhau.** `SECURITY.md` cố ý *không* được sinh ở đây: GitHub coi tên file đó là policy chính thức của repo và nó được viết tay.

**Xác minh finding trước khi "sửa".** `AGENTS.md` liệt kê các false positive hệ thống: `BEHAVIOR_*_EXFILTRATION` và `BEHAVIOR_ENV_VAR_HARVESTING` với skill đọc API key của chính nó rồi gọi service của chính nó; `MDBLOCK_PYTHON_SUBPROCESS` với mọi đoạn `subprocess`, kể cả dạng argument-list an toàn; `*_EVAL_EXEC` với chuỗi con trong định danh thường (`retrieval`, `executor`) hoặc `model.eval()`. Finding đôi khi trỏ vào file skill không hề có — kiểm bằng `find skills/<name> -type f` trước khi hành động.

## Trình tự chạy trước khi push

```bash
# 1. spec (vài giây)
for d in skills/*/; do uv run skills-ref validate "$d"; done

# 2. cổng repo-wide — cái CI chặn (khoảng 2 giây)
uv run --with pytest python -m pytest tests/_meta -q

# 3. suite của skill bạn đụng vào
uv run --with pytest python -m pytest tests/<name> -q

# 4. nếu có scripts/: đúng môi trường mà CI dựng
python tests/run_all.py --isolated <name>

# 5. quét, khớp ngưỡng CI
uv run python scan_pr_skills.py skills/<name> --fail-on HIGH
```

Bước 1–3 chạy được **không cần `uv`** bằng venv Python 3.13 + `pip install pytest skills-ref` (đã kiểm chứng theo đúng cách này). Bước 4 **bắt buộc** có `uv` — `run_all.py:123` thoát ngay nếu không thấy `uv` trên PATH.
