---
name: dym-cti-expert-case-pipeline-and-kb
description: "Chạy một case: pipeline, cluster, KB. đây là đường tất định (không LLM) chạy hết vòng thu thập → nạp KB → tìm chồng lấn → chấm rủi ro → phân cụm."
disable-model-invocation: true
---

# Skill: dym-cti-expert-case-pipeline-and-kb — Chạy một case: pipeline, cluster, KB

> Lệnh **shell**. Bản chat tương đương: `/cti-case`, `/cti-cluster`, `/cti-recall` trong [03](03-investigate-in-claude-code.md).

**Vì sao dùng:** đây là đường tất định (không LLM) chạy hết vòng thu thập → nạp KB → tìm chồng lấn → chấm rủi ro → phân cụm.
**Sinh ra cái gì:** `intel_engine/cases/<CASE-ID>/` chứa `raw/*.json`, graph, report; và KB tại `intel_engine/knowledge/`.

---

## Luật một-case-store (đọc trước, hỏng ở đây rất im lặng)

```
$INTEL_HOME/cases/<CASE-ID>/     # = intel_engine/cases/<CASE-ID>/
```

CLI, pipeline và MCP server đều giải về đúng chỗ này. Xác nhận:

```bash
python3 scripts/backend/backend.py status
python3 scripts/backend/intel.py cases --path
```

**Đừng tạo `cases/` ở repo root và đừng tự truyền `-o cases/...`.** Nó bị gitignore nên trông vô hại, nhưng hậu quả im lặng: `kb_ingest` đọc `$INTEL_HOME/cases/` không thấy gì, tương quan chạy trên tập rỗng và báo *"no shared indicators"* thay vì báo lỗi. Nếu thấy *"no raw pivot JSON in …"* thì bạn đã ghi sai đường dẫn — đó không phải bug (CLAUDE.md RULE 2).

## Mở một case

```bash
# 1. seed file: mỗi dòng một domain/URL
cat > /tmp/seeds.txt <<'EOF'
site-a.example
https://site-b.example/login
EOF

# 2. xem trước lệnh thật
python3 scripts/backend/intel.py --dry-run pipeline open CASE-0001 /tmp/seeds.txt

# 3. chạy
python3 scripts/backend/intel.py pipeline open CASE-0001 /tmp/seeds.txt
```

`pipeline` có đúng 4 sub-lệnh (`intel_engine/tools/intel.py`): `open`, `loop`, `clusters`, `status`.

Cờ đáng biết của `open`:

| Cờ | Tác dụng | Tốn credit? |
|---|---|---|
| `--jobs N` | song song hoá thu thập | không |
| `--whois-reverse` | bật reverse-WHOIS | **có** (WhoisXML DRS) |
| `--fofa-full` | reverse FOFA trên toàn bộ lịch sử thay vì ~1 năm | **có** |
| `--serp` [`--serp-region CODE`] | lớp quảng cáo: Google Ads Transparency → tài khoản đã xác minh đang **trả tiền** và tên pháp nhân tài trợ (sống sót qua WHOIS privacy và xoay domain) | **có** (1 search SerpApi/host) — nên nó opt-in |
| `--render-extract` / `--render` | render DOM sau JS (mở khoá token SaaS/analytics) | không, nhưng cần playwright |
| `--archive` | lưu bằng chứng | không |
| `--no-pssl`, `--no-graph`, `--no-report` | bỏ bớt giai đoạn | — |
| `--force` | chạy lại dù đã có cache | tuỳ lớp |
| `--analyst`, `--classification`, `--operator` | metadata cho báo cáo | không |

Probe cloaking miễn phí vẫn chạy kể cả không có `--serp`.

## Trạng thái, hội tụ, và biên chưa khai thác

```bash
python3 scripts/backend/intel.py pipeline status CASE-0001   # audit output đã lưu
python3 scripts/backend/intel.py frontier CASE-0001          # seed MIỄN PHÍ kế tiếp + lead có phí bị hoãn
python3 scripts/backend/intel.py loop CASE-0001              # collect→assess lặp tới khi hội tụ
python3 scripts/backend/intel.py reopen CASE-0001            # mở lại case nguội khi có seed mới
```

`frontier` là câu trả lời cho "còn gì chưa làm mà không tốn tiền" — chạy nó trước khi quyết định mua thêm credit.

## Phân cụm: đơn vị phán xét là CLUSTER, không phải case

```bash
python3 scripts/backend/intel.py clusters CASE-0001
```

`clusters` **không thu thập gì** — nó chia case đã có thành các thành phần cùng-operator. Chạy nó **trước** khi kết luận, vì một case thường chứa nhiều operator không liên quan.

## Truy vấn KB

```bash
python3 scripts/backend/intel.py kb --stats
```

Trên clone sạch (chạy thật):

```
entities: 0   facts: 0   edges: 0
by type: {}
edges by rel: {}
facts by source: {}
```

KB rỗng là đúng — `intel_engine/knowledge/` bị gitignore, mỗi máy tự dựng.

```bash
python3 scripts/backend/intel.py recall site-a.example        # "đã gặp chưa?" — chạy TRƯỚC khi thu thập
python3 scripts/backend/intel.py kb --entity site-a.example   # fact + edge của một entity
python3 scripts/backend/intel.py kb --cluster site-a.example  # domain chia sẻ chỉ dấu
python3 scripts/backend/intel.py kb --cluster site-a.example --strong --max-prevalence 8
python3 scripts/backend/intel.py kb --shared --min 2          # chỉ dấu dùng chung toàn KB
```

**`--strong` là cờ đáng dùng mặc định khi kết luận.** Nó loại edge boilerplate (CSS/DOM template dùng chung) và mọi chỉ dấu xuất hiện ở hơn `--max-prevalence` domain (mặc định 8) — tức favicon kit generic, email registrar. Không có nó, bạn dễ nối nhầm kiểu "cùng dùng WP-Rocket".

## Nạp và làm sạch

```bash
python3 scripts/backend/intel.py ingest --case CASE-0001       # nạp output webpivot vào KB
python3 scripts/backend/intel.py ingest-rwhois <file>          # nạp kết quả reverse-WHOIS
python3 scripts/backend/intel.py hypothesize                   # xếp hạng giả thuyết cùng-operator
python3 scripts/backend/intel.py risk --case CASE-0001         # NRD / bulletproof hosting / money trail
python3 scripts/backend/intel.py clean                         # vệ sinh KB
python3 scripts/backend/intel.py export-graph                  # xuất đồ thị
```

## Kiểm soát dương tính giả

```bash
python3 scripts/backend/intel.py noise <indicator>              # hạ tầng dùng chung?
python3 scripts/backend/intel.py reference check favicon:123456789   # BENIGN / SIGNAL / UNKNOWN
python3 scripts/backend/intel.py reference add ...              # sổ FP đã kiểm chứng
```

Sổ này là **ngoại lệ duy nhất** của RULE 1: nó được phép chứa giá trị chỉ dấu thật, vì đó chính là công việc của nó — và nó sống trong KB đã gitignore, không phải trong file tracked.

## Đường LLM (CHƯA CHẠY THẬT — cần `.venv`)

```bash
python3 scripts/backend/intel.py harness open CASE-0001 https://site-a.example
python3 scripts/backend/intel.py harness continue CASE-0001
python3 scripts/backend/intel.py harness status CASE-0001      # không gọi LLM, không cần API key
python3 scripts/backend/intel.py tool-calls CASE-0001          # model THỰC SỰ đã gọi gì
```

`tool-calls` là thứ dùng để kiểm chứng agent — nó đọc audit log, không đọc lời kể của agent.
