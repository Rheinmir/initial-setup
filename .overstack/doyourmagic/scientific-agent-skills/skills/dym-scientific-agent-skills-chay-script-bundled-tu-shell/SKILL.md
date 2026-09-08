---
name: dym-scientific-agent-skills-chay-script-bundled-tu-shell
description: "Chạy script bundled thẳng từ shell (không cần agent). 105/163 skill mang thư mục scripts/, và 90 skill trong số đó có script viết bằng argparse. Đây là CLI thật, chạy tất định, không tốn token — dùng được trong Makefile, cron, CI, hoặc chỉ để kiểm nhanh mà không mở agent."
disable-model-invocation: true
---

# Skill: dym-scientific-agent-skills-chay-script-bundled-tu-shell — Chạy script bundled thẳng từ shell (không cần agent)

> **Mọi thứ trong file này gõ vào terminal.** Prompt cho agent nằm ở [03-dung-skill-trong-agent.md](03-dung-skill-trong-agent.md).

**Vì sao dùng:** 105/163 skill mang thư mục `scripts/`, và 90 skill trong số đó có script viết bằng `argparse`. Đây là **CLI thật, chạy tất định, không tốn token** — dùng được trong Makefile, cron, CI, hoặc chỉ để kiểm nhanh mà không mở agent.
**Sinh ra cái gì:** JSON/TSV trên stdout hoặc file do `-o` chỉ định, cộng một exit code mà bạn **bắt buộc** phải branch.

---

## Tìm script chạy được

```bash
# skill nào có scripts/
ls -d skills/*/scripts | cut -d/ -f2

# script nào là CLI argparse
grep -l argparse skills/*/scripts/*.py | head -20

# mọi script argparse đều trả lời --help (đây là hợp đồng CI của repo)
python skills/paper-lookup/scripts/paginate.py --help
```

Hợp đồng "`--help` luôn chạy" không phải lời hứa suông: `tests/_contract/cli.py` sinh test case cho **mọi** script argparse trong repo, và `tests/_meta` chạy nó lên toàn bộ 163 skill trong mỗi PR.

## Ví dụ 1 — chuyển toạ độ genomic (thuần stdlib, offline, đã chạy thật)

```bash
python skills/genomic-coordinates/scripts/convert_coords.py --list
python skills/genomic-coordinates/scripts/convert_coords.py chr1 1000 2000 --from bed --to gff
```

Output thật:

```
contig	input	output	length	status	detail
chr1	1000-2000	1001-2000	1000	ok
```

Và bảng quy ước từ `--list`:

```
format         convention            notes
bed            0-based half-open     BED3/6/12, narrowPeak, broadPeak
gff            1-based inclusive     GFF3
gtf            1-based inclusive     GTF/GFF2, GENCODE, Ensembl
vcf            1-based inclusive     POS..POS+len(REF)-1
sam            1-based inclusive     SAM text POS (BAM stores it 0-based)
interval-list  1-based inclusive     Picard/GATK
```

Script cùng skill: `audit_intervals.py`, `check_contigs.py`, `normalize_variant.py`. Cả bốn chỉ dùng thư viện chuẩn — không cài gì thêm.

## Ví dụ 2 — phân trang API văn liệu, có đối chiếu số lượng

```bash
# xem kế hoạch gọi mà không gọi mạng
python skills/paper-lookup/scripts/paginate.py \
  --api openalex --query "search=crispr" --max-records 200 --dry-run
```

Output thật của `--dry-run` (exit 0, không có request nào rời máy):

```json
{
  "api": "openalex",
  "first_url": "https://api.openalex.org/works?...&per-page=100&cursor=%2A",
  "delay_seconds": 0.2,
  "query_format": "query is a raw parameter string, e.g. 'search=crispr' or 'filter=publication_year:2024'"
}
```

API hỗ trợ: `biorxiv`, `crossref`, `europepmc`, `medrxiv`, `openalex` (xem `--list-apis`).

Các script chị em, đều đọc từ file hoặc `-` (stdin), nên ghép pipe được:

```bash
python skills/paper-lookup/scripts/arxiv_atom.py feed.xml --ids-only
python skills/paper-lookup/scripts/openalex_abstract.py works.json --text-only
python skills/paper-lookup/scripts/jats_to_text.py article.xml
```

## Ví dụ 3 — client sub-command (ARAX knowledge graph)

```bash
python skills/ncats-arax/scripts/arax_client.py --help
python skills/ncats-arax/scripts/arax_client.py preflight
```

Sub-command: `preflight` (kiểm OpenAPI + version của production), `normalize` (chuẩn hoá thuật ngữ tự do thành CURIE, chỉ để review), `one-hop`, `two-hop`, `summarize`. Không cần API key. Lưu ý ràng buộc mà chính skill nêu: **truy vấn có thể public**, chỉ dùng cho câu hỏi nghiên cứu không nhạy cảm.

## Exit code — ĐỌC, đừng giả định 0/1

Repo cố ý dùng exit code phi-chuẩn ở các chỗ mà API trả **HTTP 200 cho một thất bại thầm lặng**. Trích từ docstring của `fail()` trong `skills/paper-lookup/scripts/_common.py:219`:

> *Scripts here exit non-zero on silent-failure conditions — a JATS document with no `<body>`, an arXiv Error entry, a pagination shortfall — precisely because the APIs return HTTP 200 for them.*

| Script | Exit | Nghĩa | Nguồn |
|---|---|---|---|
| `paper-lookup/arxiv_atom.py` | `3` | feed là **arXiv error response** (đến dưới dạng HTTP 200, `totalResults` 1, một entry tên 'Error') | `arxiv_atom.py:166` |
| `paper-lookup/paginate.py` | `4` | **thiếu hụt khi đối chiếu số lượng** — trả về ít record hơn API tự khai | `paginate.py:478` |
| `paper-lookup/paginate.py` | `2` | thiếu `--api`/`--query` | `paginate.py:426` |
| `analytical-method-validation`, `iso-standards-readiness`, `pkpd-modeling` (`scripts/_common.py`) | `0` / `1` / `2` | `EXIT_OK` / `EXIT_FINDINGS` / `EXIT_INPUT_ERROR` — **`1` nghĩa là "có finding", không phải "crash"** | `_common.py:32-34` |
| `exa-search`, `lab-hardware-cad`, `pyopenms` | `2` | lỗi đầu vào | `sys.exit(2)` literal |

Nghĩa là script gói vào automation phải branch tường minh:

```bash
python skills/paper-lookup/scripts/paginate.py --api crossref --query "query=crispr" -o out.json
rc=$?
case $rc in
  0) echo "ok" ;;
  4) echo "count reconciliation shortfall — kết quả KHÔNG đầy đủ, đừng dùng"; exit 1 ;;
  *) echo "lỗi (exit $rc)"; exit $rc ;;
esac
```

Với ba skill dùng `EXIT_FINDINGS = 1`, làm ngược lại: `1` là kết quả hợp lệ ("tìm thấy vấn đề"), gộp chung với lỗi thật là sai.

**Cách kiểm exit code của một script bất kỳ trước khi tin nó:**

```bash
grep -rn 'sys.exit(\|SystemExit(\|EXIT_[A-Z_]* *=\|code=' skills/<name>/scripts/*.py
python skills/<name>/scripts/<script>.py --help   # nhiều script ghi thẳng mã lạ vào description
```

## Dependency

Script không tự cài gì. 34 skill hoàn toàn thuần thư viện chuẩn — chạy ngay với `python3` là xong:

```
adaptyv, analytical-method-validation, bgpt-paper-search, clinical-decision-support,
clinical-reports, consciousness-council, dhdna-profiler, generate-image, genomic-coordinates,
ginkgo-cloud-lab, hypothesis-generation, iso-standards-readiness, markdown-mermaid-writing,
market-research-reports, ncats-arax, ontology-term-resolution, optimize-for-gpu, pacsomatic,
paper-lookup, paperzilla, parallel-web, pathml, pathogen-variant-surveillance, peer-review,
pi-agent, protocolsio-integration, research-grants, scholar-evaluation, scientific-brainstorming,
scientific-critical-thinking, scientific-writing, treatment-plans, venue-templates, what-if-oracle
```

(Nguồn: các mục `packages = []` trong `tests/skill-requirements.toml`.)

Với skill cần package, `tests/skill-requirements.toml` chính là bản kê chính xác cần cài — dùng nó thay vì đoán từ `import`:

```bash
python3 - <<'PY'
import tomllib
cfg = tomllib.load(open("tests/skill-requirements.toml", "rb"))
entry = cfg["skills"]["scanpy"]
print("python:", entry.get("python", cfg["defaults"].get("python")))
print("packages:", " ".join(entry.get("packages", [])))
PY
```

Rồi chạy trong môi trường tạm, không đụng môi trường hệ thống:

```bash
uv run --with scanpy --with anndata python skills/scanpy/scripts/<script>.py --help
```

## Cạm bẫy

- **Đừng gộp `scripts/` của nhiều skill vào cùng một `sys.path`.** 32 skill cùng ship một file tên `scripts/_common.py`; import chung một tiến trình thì `_common` trỏ về skill nào nạp trước. Chạy bằng đường dẫn đầy đủ tới từng script, đừng `sys.path.append` nhiều thư mục skill.
- **18 package được ghi nhận là không cài được ở đâu cả** trong mục `[unavailable]` của `tests/skill-requirements.toml`, kèm lý do — `matlabengine` cần MATLAB cài sẵn, `omero-py` cần build C++, `flash-attn`/`deepspeed`/`bitsandbytes` cần CUDA toolchain, `rsgislib`/`pdal` chỉ có trên conda-forge. Đọc mục đó trước khi mất một buổi.
- **Vài skill cần interpreter cũ hơn 3.13** (`pytdc`, `molfeat`, `deepchem`, `histolab`, `vaex`, `ete3`). Khoá `python` trong entry `tests/skill-requirements.toml` của skill đó nói rõ bản nào.
