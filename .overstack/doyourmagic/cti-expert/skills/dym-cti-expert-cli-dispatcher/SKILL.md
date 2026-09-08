---
name: dym-cti-expert-cli-dispatcher
description: "Dispatcher CLI: `intel.py` (CHỈ trong terminal). chạy đúng một công cụ, script hoá, hoặc làm việc khi không có agent nào cả."
disable-model-invocation: true
---

# Skill: dym-cti-expert-cli-dispatcher — Dispatcher CLI: `intel.py` (CHỈ trong terminal)

> **Mọi lệnh trong file này là lệnh SHELL.** Dán vào chat Claude Code thì chỉ là văn bản. Bản chat ở [03-investigate-in-claude-code.md](03-investigate-in-claude-code.md).

**Vì sao dùng:** chạy đúng một công cụ, script hoá, hoặc làm việc khi không có agent nào cả.
**Sinh ra cái gì:** stdout (thường có `--json`), file trong case store, và mã thoát dùng để rẽ nhánh.

---

## Một điểm vào cho 121 op

```bash
cd ~/.claude/skills/cti-expert
python3 scripts/backend/intel.py list       # bản đồ đầy đủ, mỗi op một dòng mô tả
python3 scripts/backend/intel.py --help     # docstring + ví dụ
```

`intel.py list` in tier backend rồi 121 op. Con số này đếm trực tiếp từ bảng `DISPATCH` (`scripts/backend/intel.py:70`), không phải từ tài liệu:

```bash
python3 -c "import sys; sys.path.insert(0,'scripts/backend'); import intel; print(len(intel.DISPATCH))"
# 121
```

Runner khuyến nghị trong docstring là `uv run intel.py <op>`, nhưng dispatcher là stdlib-only nên `python3` chạy y hệt.

## `--dry-run` — xem lệnh thật trước khi tiêu credit

```bash
python3 scripts/backend/intel.py --dry-run pipeline open CASE-0001 seeds.txt
```

In ra chính xác lệnh sẽ chạy, kèm `cd` (cwd quan trọng vì engine dùng đường dẫn tương đối):

```
cd <repo>/intel_engine && <python> <repo>/intel_engine/tools/intel.py open CASE-0001 seeds.txt
```

Dùng nó mỗi khi bạn không chắc một op ánh xạ tới script nào. Cờ phải đứng **trước** tên op (`-n` là bí danh).

## Mã thoát — đọc từ các lệnh `return` literal

| rc | Nghĩa | Xử lý |
|---|---|---|
| `0` | thành công (hoặc mã thoát của script engine truyền ngược ra) | — |
| `2` | op không có trong `DISPATCH` | `intel.py list` để tra tên đúng |
| `3` | không tìm thấy backend (Tier 3 / stateless) | đặt `$INTEL_HOME`, hoặc chạy ở nơi có `intel_engine` |
| `4` | backend giải được nhưng thiếu script của component đó | component chưa cài |
| `5` | không exec được interpreter (hoặc `mcp --write` gặp file đã có mà thiếu `--force`) | đặt `$INTEL_PY` |
| `130` | Ctrl-C | — |

**Đừng giả định 0/1.** Với op nào không nằm trong 5 trường hợp trên, `intel.py` trả nguyên `returncode` của script engine — mã của script đó, không phải của dispatcher (`scripts/backend/intel.py:495`).

Kiểm nhanh:

```bash
python3 scripts/backend/intel.py nosuchop; echo "rc=$?"   # rc=2
```

## Op thuần — không mạng, không key, chạy ngay

Nhóm này an toàn để thử ngay sau khi clone:

```bash
# Hash này là file hash hay credential? Chặn trước khi bạn nộp lên sandbox công khai.
python3 scripts/backend/intel.py hash-id 5f4dcc3b5aa765d61d8327deb882cf99
```

Kết quả thật:

```
1 hash(es): 0 safe to submit, 1 blocked
  ⛔ 5f4dcc3b5aa765d61d8327de… → AMBIGUOUS: could be a FILE hash or CREDENTIAL material —
     treat as credential until the source is known. Re-run with --context file|credential …
{"results": [...], "summary": {"total": 1, "submittable": 0, "blocked": 1}}
```

Các op thuần khác:

```bash
python3 scripts/backend/intel.py sensitive-paths --help    # phân loại URL theo mẫu đường dẫn nhạy cảm
python3 scripts/backend/intel.py email-permute --help      # tên/handle → email CANDIDATES (giả thuyết)
python3 scripts/backend/intel.py noise <indicator>         # chỉ dấu này là hạ tầng dùng chung?
python3 scripts/backend/intel.py capabilities              # key nào có, thiếu thì mất gì
python3 scripts/backend/intel.py email-hygiene <domain>    # điểm 0-100 + hạng A-F
```

> `email-permute` sinh **giả thuyết, không bao giờ là finding** — chính docstring của nó nói vậy. Đưa một email permute vào báo cáo như sự thật là lỗi tradecraft mà repo có test riêng để chống.

## Ba lệnh không phải op

```bash
python3 scripts/backend/intel.py list                  # bản đồ op
python3 scripts/backend/intel.py mcp                   # in khối .mcp.json (không ghi)
python3 scripts/backend/intel.py mcp --write [--force] # ghi ./.mcp.json
python3 scripts/backend/intel.py cases                 # liệt kê case trong store
python3 scripts/backend/intel.py cases <NAME>          # cây file của một case
python3 scripts/backend/intel.py cases --path [NAME]   # chỉ in đường dẫn (để script hoá)
```

## Op cần `.venv` — CHƯA CHẠY THẬT trong lần khảo sát này

| Op | Cần |
|---|---|
| `harness open/continue/status` | `claude-agent-sdk` |
| `graph`, `network`, `gantt`, `graphviz`, `mermaid`, `timeline` | `matplotlib` / `graphviz` + binary `dot` / `mmdc` |
| `report` (PDF/DOCX qua IntelReport) | `pandoc` + `xelatex` |
| `dashboard` | chạy server loopback-only |

Không có `.venv` thì chúng thoát non-zero với thông báo import; lớp stdlib phía trên không bị ảnh hưởng.

## Nhóm op theo pha (trích từ `DISPATCH`)

- **Pipeline cả case:** `pipeline`, `harness`, `clusters`, `loop`, `frontier`, `reopen`, `scope`
- **Thu thập:** `pivot-extract`/`webpivot`, `whois`, `reverse-whois`, `ct-monitor`, `wayback-ga`, `impersonate`, `search-pivot`/`query`/`dork-sweep`, `censys`, `jarm`, `intelx`, `docmeta`, `paths`, `capture`, `screenshot`, `serp`, `pssl`, `liveness`, `exhaust`, `subdomain`, `github-osint`, `username`, `phone`, `traffic`
- **Tương quan / KB:** `kb`, `recall`, `kb-stats`, `risk`, `reference`, `cert-overlap`, `cert-pivot`, `hypothesize`, `noise`, `operators`, `calibration`, `convergence`, `domains`, `victims`, `crossref`, `drift`
- **Nạp KB:** `ingest`, `ingest-report`, `ingest-rwhois`
- **Bàn giao:** `graph-build`, `graph`, `network`, `report`, `evidence-report`, `timeline`, `misp-export`, `misp`
- **Outbound (bị gate):** `engage`, `engage-harvest`, `anyrun --submit`, `misp push/publish` → xem [07](07-safety-gates.md)
- **Tự kiểm:** `eval`

`intel.py list` là nguồn chân lý; bảng trên chỉ để định hướng.
