---
name: dym-cti-expert-contributor-develop-and-gate
description: "Nhánh đóng góp: sửa chính cti-expert. repo có 6 luật cứng và một engine vendored; vi phạm chúng thường hỏng im lặng chứ không đỏ test."
disable-model-invocation: true
---

# Skill: dym-cti-expert-contributor-develop-and-gate — Nhánh đóng góp: sửa chính cti-expert

**Vì sao dùng:** repo có 6 luật cứng và một engine vendored; vi phạm chúng thường hỏng **im lặng** chứ không đỏ test.
**Sinh ra cái gì:** một thay đổi đi qua được `scripts/audit.sh` và toàn bộ test, không làm tụt rào an toàn.

> File này độc lập với `01`–`08`. Nhưng đọc [04](04-cli-dispatcher.md) trước sẽ giúp — bảng `DISPATCH` mà bạn phải cập nhật ở đây chính là thứ file đó mô tả.

---

## Cài môi trường dev

```bash
git clone https://github.com/7onez/cti-expert.git && cd cti-expert
bash scripts/install-hooks.sh          # hook git pre-commit → leakcheck.sh (BẮT BUỘC mỗi clone)
uv venv && uv pip install -r requirements.txt    # cho §9 của audit + engine test cần SDK
```

`.git/hooks/` không được track, nên `install-hooks.sh` phải chạy lại ở mỗi clone mới. Không có nó thì RULE 1 chỉ còn một lớp.

## Cổng duy nhất: `scripts/audit.sh`

```bash
bash scripts/audit.sh
```

Chạy thật **không có `.venv`** → `AUDIT: clean`, rc=0. Nó gate 9 mục:

| § | Kiểm gì |
|---|---|
| 1 | leak check RULE 1, **hai lượt**: diff (cái commit này THÊM vào) + tree (mọi file text đã track) |
| 2 | mọi op `DISPATCH` giải được ra một script có thật (RULE 3) |
| 3–4 | shim collector vẫn là re-export, chưa bị biến ngược thành bản sao (RULE 4) |
| 5 | số `@tool` khớp con số ghi trong `CLAUDE.md` |
| 6 | `py_compile` + test ở repo root |
| 7 | mọi đường dẫn hook mà `hooks.json` đăng ký còn tồn tại |
| 8 | test engine vendored, tập stdlib-only (15 file) |
| 9 | test engine cần `claude_agent_sdk` — **SKIP** nếu không có `.venv` |

§1 có hai lượt vì chúng trả lời hai câu khác nhau. Lượt diff chỉ thấy dòng ai đó vừa chạm; một giá trị rò rỉ nằm sẵn trong file không ai mở sẽ sống mãi — đã có 4 giá trị sống sót nhiều tháng đúng theo cách đó. Lượt diff cũng chỉ soi dòng **thêm vào**: từ chối cả dòng `-` từng làm cổng tự khoá (cách duy nhất để gỡ một giá trị đã rò là `--no-verify`, tức cổng đẩy bạn về đúng lối tắt nó sinh ra để chặn).

**§9 bị SKIP là bẫy thật.** Cục bộ nó in:

```
== 9. vendored-engine tests needing claude_agent_sdk ==
  SKIPPED (claude_agent_sdk not importable) — 5 tests incl. the context-governor check.
```

CI có job riêng (`engine-tests` trong `.github/workflows/audit.yml`) và job đó **fail nếu thấy dòng SKIPPED** — vì một guard bị bỏ qua im lặng thì không phải guard.

## Chạy test tay

```bash
for t in tests/test_*.py; do python3 "$t" >/dev/null 2>&1 && echo "PASS $t" || echo "FAIL $t"; done
```

10 file ở repo root, tất cả **zero-dep** (không cần pytest). Chạy thật, cả 10 rc=0:

| Test | Khẳng định gì |
|---|---|
| `test_hooks.py` | 58 check — hook nổ đúng mục tiêu, im ở ca an toàn, cả hai fail-open, wiring plugin độc lập máy |
| `test_references.py` | 580 check — data file có tài liệu, consumer nạp data thật, file hỏng thì báo to |
| `test_no_sample_submission.py` | 30 check — không có đường nộp mẫu nào KHÔNG bị gate |
| `test_indicator_classification.py` | RULE 5 — 16 placeholder, 7 tên thật, 8 tên privacy, 7 NS managed, 3 NS tự host |
| `test_collect_core.py` | egress gate, tái dùng cache, `--force`, fan-out, vòng collect→ingest→correlate |
| `test_cluster_corroboration.py` · `test_social_noise_classification.py` | logic gộp/tách cụm |
| `test_email_permute.py` · `test_email_hygiene_nullmx.py` · `test_osint_tools.py` | tool thuần |

Engine vendored có bộ riêng: `intel_engine/tests/` (`test_tool_registry` cho RULE 2, `test_tool_gate` cho phê duyệt submission, `test_engage`, …). `run_eval.py` đặt **cả hai** thư mục lên path để không bộ nào lặng lẽ ngừng chạy.

## Sáu luật, và cái giá khi phá

### RULE 1 — không bao giờ đưa dữ liệu case vào skill
File tracked chỉ chứa code + tradecraft. Không tên người thật, không hạ tầng của case, không GA4/GTM/GSC thật, không case ID, không PII operator — kể cả trong comment, fixture, hay "ví dụ thực tế". Dữ liệu điều tra sống **duy nhất** trong `intel_engine/cases/`, `intel_engine/knowledge/`, `intel_engine/MEMORY/`, `.env` (đều gitignore).

Ngoại lệ duy nhất và hẹp: sổ FP curated (`/reference add`) — chứa giá trị chỉ dấu là *công việc của nó*, và nó nằm trong KB đã gitignore.

Cần ví dụ trong file tracked thì dùng: `example.com`, `registrant@example.com`, `Operator A`, `G-XXXXXXXXXX`, `GTM-XXXXXXX`, `UA-100000001`, `CASE-0001`, `1ExampleBitcoinAddressDoNotUse`. Hằng số công cộng chung chung (địa chỉ registrar, dải CDN/ASN, hash favicon Sedo/Wix) thì được — chúng mô tả tooling, không mô tả case.

### RULE 2 — đúng MỘT case store
`$INTEL_HOME/cases/<CASE-ID>/`. Đừng tạo `cases/` ở repo root: nó gitignore nên trông vô hại, nhưng `kb_ingest` sẽ đọc rỗng và báo "no shared indicators" thay vì báo lỗi.

### RULE 3 — mọi tool mới phải đăng ký với bề mặt MCP
Thêm một tool thì làm đủ **bốn** việc:

1. Bọc thành `@tool(name, description, {params})` trong `intel_engine/harness/tools.py` — `mcp_server.py` tự phát hiện, không cần sửa lần hai.
2. Thêm dòng vào `DISPATCH` trong `scripts/backend/intel.py` để CLI T2 với tới được.
3. Cập nhật con số `@tool` trong `CLAUDE.md` (hiện **78**; `audit.sh` §5 so khớp). Kiểm: `grep -c '@tool(' intel_engine/harness/tools.py`.
4. Nếu nó là lệnh mới trong `SKILL.md` §3, nó **phải** ánh xạ tới một op `DISPATCH` thật hoặc một `@tool` thật. Một lệnh có tài liệu mà không có gì thực thi còn tệ hơn là không có lệnh.

Thêm một *chế độ* cho tool sẵn có thì **không** tạo `@tool` mới — chỉ mở rộng description.

Smoke-check:

```bash
.venv/bin/python intel_engine/harness/mcp_server.py   # gửi JSON-RPC tools/list, xác nhận tool có mặt
```

Trong Claude Code kiểm bằng `/mcp`. Lưu ý Claude Code **cache danh sách tool lúc connect** — đăng ký cũ sẽ lái một bề mặt lỗi thời mà không báo gì; đó chính là lý do `sessionguard.py` cảnh báo khi số `@tool` đổi.

### RULE 4 — drift wrapper/collector phải tự lành
5 collector tồn tại ở cả hai lớp. Mỗi cái có **một file canonical + một shim re-export 9 dòng** (Windows-safe, không symlink):

| collector | canonical (sửa ở đây) | shim (đừng sửa) |
|---|---|---|
| `pivot_extract`, `cdn_ranges`, `graph_build`, `wayback_ga` | `scripts/webpivot/` | `intel_engine/WebPivot/tools/` |
| `whois_enrich` | `intel_engine/WebPivot/tools/` | `scripts/webpivot/` |

Đừng bao giờ biến shim ngược thành bản sao. Di chuyển thư mục thì sửa lại độ sâu tương đối trong shim.

Wrapper của harness probe `--help` từng collector và lọc bỏ cờ không hỗ trợ (`_supported_flags`/`_filter_args`). **Cờ bị bỏ được nêu ra trong kết quả tool — đó là cố ý.** Một `--submit`/`--archive-missing` bị rơi nghĩa là bằng chứng đã KHÔNG được lưu trữ; đừng làm im tiếng nó.

### RULE 5 — đổi phân loại chỉ dấu thì phải có test
Hai file cai quản việc gộp cụm:

- `intel_engine/tools/kb/noise_filters.py` — `MANAGED_DNS_SUFFIXES`, favicon parking, host parking. Mô hình bảo trì: gặp provider nào thêm provider đó.
- `intel_engine/tools/kb/hypothesize.py` — `_tier()`, xếp một quan hệ vào attribution / corroborating / noise.

`uses_nameserver` là **có điều kiện**: uỷ quyền cho provider managed là noise; uỷ quyền cho nameserver do chính operator vận hành là bằng chứng attribution (bạn không thể trỏ domain tới `ns1.<host-của-họ>` nếu không kiểm soát zone đó). Thêm một provider vào `MANAGED_DNS_SUFFIXES` do đó **làm yếu** clustering — có chủ đích, và đó là lý do danh sách này quan trọng.

Mọi thay đổi hai file này phải kèm check phân loại phủ **ít nhất một provider managed và một nameserver tự host**.

### RULE 6 — lớp harness là một phần của skill
`hooks/` + `.claude-plugin/plugin.json` là nơi hai tính chất an toàn thực sự được thi hành dưới Claude Code. Chi tiết ở [07](07-safety-gates.md). Ba điểm dành cho người sửa code:

- `leakguard.py` **không được** tự cài lại mẫu regex — nó shell ra `leakcheck.sh`. Bản sao thứ hai sẽ trôi lệch, và guard trôi lệch thì luôn báo sạch.
- Thêm một năng lực outbound nghĩa là **thêm một dòng vào `hooks/references/outbound_actions.json`**, không phải chỉ thêm cờ confirm trong Python.
- Đừng nới rào để tắt prompt. Ưu tiên siết `flag_required` hoặc khớp chính xác. Dấu cách cuối trong `intel.py engage ` (tha cho `engage-report`) là hình mẫu cần bắt chước.

## Đồng bộ engine vendored — là merge ba chiều, không phải copy

Upstream: cây làm việc `intelligence_assist` (GitHub `0xdefh/Intelligence-AS`). Đồng bộ **một chiều**, cti-expert không bao giờ ghi ngược.

"Copy rồi áp lại 5 shim" là **không đủ**. Cây vendored còn mang hơn chục file mà cti-expert đã vá có chủ đích, và ghi đè chúng hỏng **im lặng** — collector vẫn chạy, chỉ là thôi tìm thấy gì. Hai ví dụ đã biết: `wp_common` đi lên thêm một cấp để tìm `.env` (cti-expert lồng sâu hơn; bản upstream giải mọi API key thành rỗng), và `pivot_extract` bật reverse-WHOIS mặc định với `--no-whois-reverse` là opt-out (upstream làm ngược lại).

Tìm điểm phân kỳ bằng **định danh blob**, không bằng trí nhớ: index mọi cặp `(blob, path)` upstream từng commit, cộng cây làm việc hiện tại; rồi hash từng file vendored.

| blob vendored | nghĩa | hành động |
|---|---|---|
| khớp một blob upstream của cùng path | bản sao thuần | ghi đè an toàn |
| path có ở upstream, blob không khớp cái nào | **bản vá của cti-expert** | merge 3 chiều |
| path không tồn tại ở upstream | **chỉ cti-expert có** | phải sống sót; **không bao giờ** `rsync --delete` |

Với mỗi bản vá, chọn merge base bằng khoảng cách diff nhỏ nhất trên lịch sử blob của path đó, rồi `git merge-file <ours> <base> <theirs>`. Chờ đợi khối `@tool`/`def` trùng lặp ở chỗ base có trước một tool mà cả hai phía sau đó cùng thêm:

```bash
grep -oE '^async def [a-z_]+' <file> | sort | uniq -d
```

Ba cái bẫy còn lại:

- Loại trừ `.venv`, `__pycache__`, `cases/`, `knowledge/`, `MEMORY/`, `.env`.
- Đổi tên `SKILL.md` của từng component thành `SKILL.reference.md` — repo có **đúng một** `SKILL.md`, ở root.
- **zsh không word-split tham số không quote** — một `rsync $EXCLUDES` dựng dạng một chuỗi sẽ loại trừ *không gì cả*, và kéo nguyên 500 MB `.venv` vào cây.

Sau khi sync, verify đủ 5 thứ:

```bash
bash scripts/audit.sh
for t in tests/test_*.py; do python3 "$t" >/dev/null && echo "PASS $t"; done
for t in intel_engine/tests/test_*.py; do python3 "$t" >/dev/null 2>&1 && echo "PASS $t"; done
.venv/bin/python intel_engine/harness/mcp_server.py    # gửi tools/list
python3 scripts/backend/intel.py pipeline open <CASE> <seeds>
```

## CI của repo (đọc để hiểu, không copy)

| Workflow | Gate gì |
|---|---|
| `audit.yml` job `structural` | `bash scripts/audit.sh` — stdlib/grep, không venv, chạy trong vài giây |
| `audit.yml` job `engine-tests` | cài `requirements.txt` rồi chạy lại audit; **fail nếu §9 báo SKIPPED** |
| `audit.yml` job `leak-diff` | chỉ trên PR — quét **chỉ các dòng THÊM VÀO** so với base ref, nên giá trị ví dụ đã có sẵn trong cây không bị gắn cờ lại |
| `smoke.yml` | clone→install→run trên container ubuntu tối giản (root, không sudo, không sẵn git/curl/python) + macOS/ubuntu runner thường; gate bằng `scripts/smoke-test.sh` |

Hai workflow này gate việc phát triển **chính công cụ**. Nếu bạn là người tiêu thụ và muốn CI, xem [08](08-ci-monitoring.md) — ví dụ ở đó được viết mới cho mục đích khác hẳn.

## Trước khi mở PR

```bash
bash scripts/audit.sh                        # phải in "AUDIT: clean"
python3 tests/test_hooks.py                  # nếu bạn chạm hooks/
python3 tests/test_indicator_classification.py   # nếu bạn chạm noise_filters/hypothesize (RULE 5)
python3 scripts/backend/intel.py list        # nếu bạn thêm op — nó phải xuất hiện, và audit §2 phải xanh
grep -c '@tool(' intel_engine/harness/tools.py   # nếu bạn thêm @tool — số này phải khớp CLAUDE.md
```

Mọi thứ track trong repo này là **public-facing**. Coi như vậy.
