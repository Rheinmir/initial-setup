# CTI Expert — bộ workflow chạy được

Sinh từ một lượt khảo sát **read-only** repo `7onez/cti-expert` tại commit `08bed57` (2026-08-28, plugin version `2.8.0`), chạy thật trong sandbox trên macOS (không cài `.venv`, không dùng API key, không đụng mạng ngoài trừ khi ghi rõ).

CTI Expert là **một skill, hai lớp**:

- **Lớp collector của chính cti-expert** — `scripts/` (webpivot, osint, generator báo cáo), `SKILL.md`, 8 lệnh `/cti*`, 3 hook an toàn cho Claude Code.
- **Engine vendored `intel_engine/`** — pipeline điều tra, KB tương quan, MCP server 78 `@tool`, các skill render/analysis/engage.

Tất cả đi qua **một dispatcher CLI duy nhất**: `scripts/backend/intel.py`, hiện có **121 op** (đếm trực tiếp từ bảng `DISPATCH`).

Bundle chia theo **đối tượng người dùng**, không theo tính năng:

- **Nhánh tiêu thụ (`01`–`08`)** — bạn là analyst, muốn *dùng* cti-expert để điều tra.
- **Nhánh đóng góp (`09`)** — bạn clone repo về để *sửa chính công cụ*.

| # | File | Mục đích | Nhánh |
|---|------|----------|-------|
| 1 | [01-install-and-register.md](01-install-and-register.md) | Clone, chạy `install.sh`, chọn giữa `register.sh` (symlink) và `/plugin install` (kèm hook), dựng `.venv`, verify bằng `backend.py status` | Tiêu thụ — cài đặt |
| 2 | [02-api-keys-and-capabilities.md](02-api-keys-and-capabilities.md) | `.env`, op `capabilities` (thiếu key thì mất gì), sổ chi phí `api-usage` tách khỏi cost model | Tiêu thụ — cấu hình |
| 3 | [03-investigate-in-claude-code.md](03-investigate-in-claude-code.md) | **CHỈ lệnh chat** — 8 lệnh `/cti*` đã đăng ký, vòng đời AEAD, cách đọc marker `[model]` / `[unimplemented]` | Tiêu thụ — dùng hằng ngày (chat) |
| 4 | [04-cli-dispatcher.md](04-cli-dispatcher.md) | **CHỈ lệnh shell** — `intel.py list`, `--dry-run`, mã thoát 2/3/4/5, các op thuần không cần mạng/không cần key | Tiêu thụ — dùng hằng ngày (terminal) |
| 5 | [05-case-pipeline-and-kb.md](05-case-pipeline-and-kb.md) | Mở case, `pipeline`/`clusters`/`loop`/`frontier`, nạp KB, `recall`, `hypothesize`, luật MỘT case store | Tiêu thụ — điều tra |
| 6 | [06-reports-and-iocs.md](06-reports-and-iocs.md) | Sinh HTML offline + bundle IOC/STIX + DOCX, `redact.py`, render graph (đòi `.venv`) | Tiêu thụ — bàn giao |
| 7 | [07-safety-gates.md](07-safety-gates.md) | Cái gì bị CHẶN (RULE 1 leakguard), cái gì HỎI (actionguard outbound), cái gì im lặng — và vì sao đừng nới rào | Tiêu thụ — vận hành an toàn |
| 8 | [08-ci-monitoring.md](08-ci-monitoring.md) | Ví dụ CI tối giản **tự viết** cho dự án của bạn: sweep typosquat + CT-monitor định kỳ, rẽ nhánh theo mã thoát | Tiêu thụ — tự động hoá |
| 9 | [09-contributor-develop-and-gate.md](09-contributor-develop-and-gate.md) | `audit.sh`, chạy test, thêm một tool đúng RULE 3, hook test hai chiều, đồng bộ engine vendored | Đóng góp |

## Thứ tự chạy đề xuất

**Analyst lần đầu:** `01` → `02` (dừng lại được ở keyless, không bắt buộc có key) → `03` **hoặc** `04` tuỳ bạn làm việc trong chat hay terminal → `05` khi có case thật → `06` khi cần bàn giao → `07` đọc **trước** khi chạm bất cứ thứ gì outbound → `08` khi muốn theo dõi liên tục.

**Người đóng góp:** nhảy thẳng `09`; nó không phụ thuộc `01`–`08`, nhưng `04` giúp hiểu bảng `DISPATCH` mà `09` bắt bạn cập nhật.

**Ranh giới quan trọng:** `03` là lệnh **chat**, gõ vào terminal sẽ không chạy. `04`–`06`, `08`, `09` là lệnh **shell**, gõ vào chat Claude Code thì chỉ là văn bản. Hai file tách riêng chính vì lỗi này.

## Bundle này được kiểm chứng ra sao, không phải chép lại README

Mọi lệnh trong `01`–`09` đều đối chiếu với mã nguồn thật, và phần lớn được **chạy thật** trong sandbox:

| Khẳng định | Nguồn kiểm chứng |
|---|---|
| 121 op CLI, tên op và script đích | bảng `DISPATCH` trong `scripts/backend/intel.py:70-230`, đếm bằng `len(intel.DISPATCH)` |
| Mã thoát `2` (op lạ), `3` (không thấy backend), `4` (thiếu script engine), `5` (không exec được interpreter), `130` (Ctrl-C) | các lệnh `return` literal trong `scripts/backend/intel.py:452-505`; xác nhận `rc=2` bằng cách chạy `intel.py nosuchop` |
| `backend.py` chỉ nhận 4 lệnh `status/check/env/path` | `argparse` `choices=` tại `scripts/backend/backend.py:285` |
| Tier 2 "in-repo (self-contained)" là mặc định khi chạy trong clone | chạy thật `python3 scripts/backend/backend.py status --json` |
| `--dry-run` in ra đúng lệnh sẽ chạy, không thực thi | chạy thật `intel.py --dry-run pipeline open CASE-0001 seeds.txt` |
| 8 lệnh `/cti*` là lệnh đã đăng ký, mọi `/lệnh` khác trong SKILL.md chỉ là quy ước | bảng tại `SKILL.md` §3.0 + `commands/*.md` frontmatter (8 file) + `scripts/register.sh` |
| Danh sách hành động bị gate (ask) | `hooks/references/outbound_actions.json` — 7 MCP tool + 11 pattern bash, đọc trực tiếp bằng `json.load` |
| Hook fail-open, đúng 3 hook đăng ký | `hooks/hooks.json` + `tests/test_hooks.py` chạy thật: 58 check PASS |
| 10 test zero-dep ở repo root đều xanh | chạy thật từng file `python3 tests/test_*.py`, rc=0 |
| `audit.sh` xanh khi không có `.venv`, §9 bị SKIP | chạy thật `bash scripts/audit.sh` → `AUDIT: clean`, §9 in dòng SKIPPED |
| 78 `@tool` trên MCP surface | `grep -c '@tool(' intel_engine/harness/tools.py` |
| Generator HTML + IOC chạy được bằng `python3` thuần, không cần cài gì | chạy thật với `scripts/sample-cti-report-data.json` → HTML 87 KB, `ioc.txt`/`ioc.csv`/`ioc.stix.json` |
| `capabilities` chạy được ở chế độ KEYLESS và nói rõ mất gì | chạy thật `intel.py capabilities` không có `.env` |
| CI của repo gate cái gì | `.github/workflows/audit.yml` + `smoke.yml` — **đọc để hiểu, không chép** làm ví dụ CI cho người tiêu thụ; `08` là ví dụ tự viết |
| Luật đóng góp RULE 1–6 | `CLAUDE.md`, `STRUCTURE.md` |

Ba điểm bundle này **không** kiểm chứng được vì không cài `.venv` và không chạy outbound: đường LLM `harness` (cần `claude-agent-sdk`), render `graph`/`network`/`report` (cần matplotlib/graphviz/pandoc), và mọi thứ có `--submit`/`engage`. Chỗ nào phụ thuộc chúng đều được đánh dấu **CHƯA CHẠY THẬT** trong file tương ứng.
