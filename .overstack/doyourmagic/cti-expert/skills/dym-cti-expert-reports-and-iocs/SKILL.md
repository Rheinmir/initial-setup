---
name: dym-cti-expert-reports-and-iocs
description: "Bàn giao: báo cáo HTML, bundle IOC/STIX, DOCX, bản đã che. biến case thành thứ người khác đọc được và tool khác nuốt được, không cần cài gì thêm cho đường mặc định."
disable-model-invocation: true
---

# Skill: dym-cti-expert-reports-and-iocs — Bàn giao: báo cáo HTML, bundle IOC/STIX, DOCX, bản đã che

> Lệnh **shell**. Bản chat tương đương: `/cti-report <CASE-ID>` trong [03](03-investigate-in-claude-code.md).

**Vì sao dùng:** biến case thành thứ người khác đọc được và tool khác nuốt được, không cần cài gì thêm cho đường mặc định.
**Sinh ra cái gì:** `.html` offline một file, `.txt`/`.csv`/`.stix.json` IOC, `.docx` (khi cần), và bản `.redacted.md` để chia sẻ.

---

## Đầu vào: một file report JSON

Mọi generator ăn cùng một JSON. Repo có sẵn mẫu để bạn soi cấu trúc:

```bash
python3 -c "import json;print(list(json.load(open('scripts/sample-cti-report-data.json'))))"
# ['case', 'executive_summary', 'subjects', 'findings', 'connections', 'timeline',
#  'sources', 'intelligence_gaps', 'recommendations', 'visitor_stats', 'caveats']
```

Bộ export mặc định theo `AGENTS.md` §4 là `.md` + `.html` + `.json` + `.csv` + bundle IOC. DOCX chỉ khi được yêu cầu.

## HTML — bản người ta thực sự đọc

```bash
python3 scripts/generate-cti-html.py REPORT.json REPORT.html
```

Chạy thật với file mẫu:

```
HTML report written: /tmp/.../r.html (87 KB)
  case: Acme Corporation Exposure Assessment  |  subjects: 5  findings: 7  connections: 5
  open in any browser - fully offline, no external dependencies.
```

Stdlib thuần — **không cần `.venv`, không cần uv, không cần mạng**. File tự chứa hoàn toàn, mở bằng `file://` là xong.

## Bundle IOC → STIX 2.1 + phẳng + CSV

```bash
python3 scripts/generate-cti-iocs.py REPORT.json IOC-PREFIX --format all
```

`--format` nhận `stix` | `flat` | `csv` | `all`. Chạy thật:

```
Extracted 16 indicators/selectors + 5 attribution links
  by category: contact=1, identity=6, network=7, social=2
  wrote: IOC-PREFIX.txt
  wrote: IOC-PREFIX.csv
  wrote: IOC-PREFIX.stix.json
```

## DOCX — chỉ khi được yêu cầu

```bash
# Lai: văn xuôi từ Markdown + biểu đồ/sơ đồ từ JSON  (đường đầy đủ)
python3 scripts/generate-cti-docx-hybrid.py REPORT.md REPORT.json REPORT.docx

# Chỉ JSON, không cần pandoc
python3 scripts/generate-cti-docx.py REPORT.json REPORT.docx

# Chỉ Markdown
python3 scripts/generate-cti-docx-hybrid.py REPORT.md REPORT.docx
```

Generator tự ép UTF-8 và tự dò pandoc — không cần prelude `PYTHONUTF8` hay chỉnh PATH, kể cả trên Windows.

Nếu chưa có dependency, dùng `uv run` thay `python3`: các script mang **PEP 723 inline deps** nên `uv` tự cấp phát.

## Bản đã che, để chia sẻ ra ngoài (OPT-IN)

```bash
python3 scripts/redact.py REPORT.md -o REPORT.redacted.md --map REPORT.map.json
```

Điểm cần nắm:

- **Dùng MỘT `--map` cho mọi file** của cùng case, để một selector giữ nguyên placeholder ở khắp nơi. Hai map khác nhau làm mất khả năng đối chiếu chéo.
- **Không bao giờ gửi file `.map.json`** — nó là chìa khoá đảo ngược.
- `--restore` + `--map` để khôi phục; round-trip khôi phục **nguyên vẹn từng byte** (`scripts/smoke-test.sh` kiểm chính điều này).
- Mặc định che PII. Hạ tầng (`URL`/`DOMAIN`/`IPV4`/`IPV6`) **không** bị che trừ khi bạn thêm `--all-types` — vì trong báo cáo CTI, hạ tầng của đối tượng *chính là phần phân tích*, không phải PII vô tình.
- `--list-types` liệt kê loại; `--custom 'CASE_REF=\bCR-\d{6}\b'` thêm mẫu riêng, lặp được.
- `--dry-run` xem trước.

## Render đồ hoạ (CHƯA CHẠY THẬT — cần `.venv` + binary hệ thống)

```bash
python3 scripts/backend/intel.py graph-build ...           # → case_graph.json (đầu vào render)
python3 scripts/backend/intel.py graph case_graph.json out --legend
python3 scripts/backend/intel.py network ...               # đồ thị liên kết
python3 scripts/backend/intel.py timeline ...              # vòng đời hạ tầng
python3 scripts/backend/intel.py report assessment.md out --pdf --docx
python3 scripts/backend/intel.py evidence-report ...       # manifest bằng chứng có hash
```

| Cần | Cho |
|---|---|
| `matplotlib` | chart, timeline, gantt |
| `graphviz` (pip) + binary `dot` | đồ thị entity/hạ tầng |
| `mermaid-cli` (`mmdc`) | sơ đồ luồng IntelGraph |
| `pandoc` + `xelatex` | PDF của IntelReport |

## Chia sẻ ra cộng đồng (MISP) — có gate

```bash
python3 scripts/backend/intel.py misp-export ...   # dựng event tại chỗ, KHÔNG chạm mạng
python3 scripts/backend/intel.py misp push ...     # STAGE lên instance của bạn (chỉ tổ chức, chưa publish)
python3 scripts/backend/intel.py misp publish ...  # đồng bộ ra cộng đồng — KHÔNG THU HỒI ĐƯỢC
```

Ba op tách rời vì là ba quyết định khác nhau. `push` và `publish` đều nằm trong danh sách gate outbound — xem [07](07-safety-gates.md). Một chỉ dấu đã publish sẽ thành luật chặn của người khác; bạn không rút lại được.
