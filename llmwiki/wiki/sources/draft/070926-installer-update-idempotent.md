---
type: source
title: "Installer update đè lên dự án phiên bản cũ — bốn lỗ đo được và kịch bản sửa"
status: proposed
tags: [installer, migration, layout-dot, capability-stamp, rollback]
timestamp: 2026-09-07
---

# Installer update đè lên dự án cũ — kịch bản sửa

## Vấn đề

`install-harness.sh` được thiết kế cho lần cài đầu. Khi nó chạy lần thứ hai trên một
dự án đã cài từ bản cũ hơn, bốn chỗ hở lộ ra. Cả bốn đều **im lặng** — không lỗi, không
cảnh báo, chỉ để lại một dự án ở trạng thái nửa vời.

### Lỗ 1 — detect layout mù, dựng khung thứ hai bên cạnh khung đang dùng

```sh
if [ -d "$ROOT/llmwiki" ]; then MODE="migrate"; else MODE="new"; fi
```

Điều kiện chỉ hỏi về `llmwiki/` **trần**. Từ `e342280`, dự án downstream dùng layout ẩn
`.llmwiki/` + `.harness/`. Một dự án đã ở chuẩn mới sẽ rơi vào `MODE=new`, và bước kế
tiếp dựng nguyên bộ khung trần:

```sh
mkdir -p "$ROOT/llmwiki/wiki"/{concepts,entities,sources/adr,sources/draft,draft/orca} \
         "$ROOT/llmwiki"/{raw,html,skills}
```

Kết quả: **hai bộ wiki cùng tồn tại**. Hook trỏ vào một bộ (theo `.harness-stamp`),
người dùng và agent ghi vào bộ kia. Không có gì báo lỗi vì cả hai đều hợp lệ về cấu trúc.

Nghịch lý: hàm trả lời đúng câu hỏi này **đã tồn tại** trong `harness/scripts/overstack_paths.py`
và có self-test cho cả ba ca (layout cũ / layout mới / repo framework):

```python
def needs_migration(root) -> list:
    """Thư mục còn RƠI RỚT ở chuẩn cũ (có bản trần, chưa có bản dấu chấm)."""
```

Nhưng `fdk-gate`, `okf-scan`, `session-continue`, `unknown-ledger` gọi nó — **installer thì không**.

### Lỗ 2 — đè script không backup, không so version

```sh
cp "$SRC/harness/scripts/"*.py "$ROOT/harness/scripts/" 2>/dev/null || true
```

Đè thẳng mọi `.py`. Không hỏi bản đích mới hay cũ hơn, không giữ bản cũ. `settings.json`
có backup (`.bak.$(date +%s)`) và `~/.openclaude/settings.json` còn có khôi phục khi merge
hỏng — nhưng thư mục `harness/` thì không có gì. Dự án nào sửa tay một validator sẽ mất
sửa đó, và chỉ biết khi hành vi đổi.

### Lỗ 3 — `version.json` đứng yên, dự án tưởng mình current

```sh
[ -f "$ROOT/harness/version.json" ] || cp "$SRC/harness/version.json" "$ROOT/harness/version.json"
```

Nhánh `SAME_BUNDLE=0` (đường đi của **mọi dự án downstream**) chỉ chép khi file **chưa tồn tại**.
Dự án đã cài rồi thì giữ nguyên version cũ vĩnh viễn, dù engine vừa bị đè bằng bản mới.

Hệ quả nối tiếp: `capability-stamp` so hai số bằng nhau rồi kết luận không có gì mới, nên
năng lực vừa được chép vào **không bao giờ được công bố**. Đây đúng lớp bẫy đã ghi ở cạm bẫy
số 4 của file bàn giao `070926-overstack-memory-selfreport.md` — lần đó là quên bump, lần này
là bump không bao giờ tới.

### Lỗ 4 — không có điểm quay lại

Update là một chuỗi `cp` không giao dịch. Đứt giữa chừng (mạng, quyền ghi, đĩa đầy) để lại
một `harness/` lai giữa hai phiên bản, và không có gì ghi lại trạng thái trước đó để quay về.

## Kịch bản sửa

Sáu bước, mỗi bước có một câu hỏi kiểm chứng trả lời được bằng lệnh. Thứ tự có lý do:
detect trước khi đụng đĩa, snapshot trước khi đè, bump sau cùng khi mọi thứ đã xanh.

### B0 — Cổng vào: từ chối chạy trên cây bẩn

```sh
[ -z "$(git -C "$ROOT" status --porcelain 2>/dev/null)" ] || {
  warn "cây làm việc bẩn — commit hoặc stash trước khi update (rollback dựa vào git)"; exit 5; }
```

**Vì sao đứng đầu:** mọi cơ chế quay lại ở B5 đều dựa vào việc phân biệt được "thay đổi do
installer" với "thay đổi của người dùng". Cây bẩn thì không phân biệt được.

**Kiểm:** chạy trên repo có 1 file sửa → rc 5, không file nào bị đụng.

### B1 — Detect layout bằng hàm đã có, không bằng một điều kiện `-d`

```sh
LAYOUT=$(python3 "$SRC/harness/scripts/overstack_paths.py" --layout "$ROOT")
# → "dot" | "plain" | "framework" | "none"
```

`MODE=new` chỉ khi `LAYOUT=none`. `LAYOUT=dot` hoặc `plain` đều là `migrate`, và migrate
**không được** dựng khung mới.

**Vì sao dùng `overstack_paths` chứ không viết lại:** hai định nghĩa "dự án này ở layout nào"
mà nằm ở hai nơi thì sớm muộn cũng lệch. Hàm đó đã có self-test khoá cả ca repo framework
(không bao giờ tự migrate).

**Kiểm:** dựng ba thư mục giả (`.llmwiki/`, `llmwiki/`, rỗng) → ba giá trị khác nhau; dự án
`.llmwiki/` chạy installer xong **không** sinh ra `llmwiki/` trần.

### B2 — Snapshot trước khi đè

```sh
SNAP="$ROOT/.harness-snapshot/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$SNAP"
cp -R "$ROOT/harness" "$SNAP/harness" 2>/dev/null || true
cp -R "$ROOT/harness-local" "$SNAP/harness-local" 2>/dev/null || true
echo "$OLD_VERSION" > "$SNAP/from-version"
```

Chỉ giữ **ba bản gần nhất**, xoá dần bản cũ hơn — snapshot không được phình thành rác.

**Vì sao không dựa hẳn vào git:** `harness/` ở nhiều dự án nằm trong `.gitignore`, và cài
lại có thể xảy ra ngay sau `clone` khi chưa có commit nào.

**Kiểm:** sau update, `diff -r "$SNAP/harness" "$ROOT/harness"` liệt kê đúng những file
installer đã đổi — không thừa, không thiếu.

### B3 — Đè có so sánh, và chừa vùng của dự án

Ba nhóm, ba luật khác nhau:

| Nhóm | Luật | Lý do |
|---|---|---|
| Engine (`scripts/`, `validators/`, `poc-vendor-neutral/`) | đè khi bản nguồn **mới hơn** | đây là phần dùng chung, dự án không nên sửa |
| Cấu hình (`policy.yaml`, `*.config.yaml`) | merge, giữ khoá dự án đã đặt | dự án có quyền chỉnh ngưỡng |
| Vùng dự án (`harness-local/`, `evals/`, `metrics/`) | **không đụng** | rule và số đo riêng của dự án |

So sánh version dùng chính `template_version` trong `version.json`, so theo semver chứ không
so chuỗi. Bản đích **mới hơn** bản nguồn ⇒ dừng và báo, không hạ cấp âm thầm.

**Kiểm:** đặt một validator sửa tay trong `harness-local/` → sau update còn nguyên byte;
đặt `version.json` của đích cao hơn nguồn → installer từ chối, rc khác 0.

### B4 — Bump stamp là bước cuối, và luôn chạy

```sh
cp "$SRC/harness/version.json" "$ROOT/harness/version.json"
python3 "$ROOT/harness/scripts/capability-stamp.py" --update
```

Bỏ điều kiện `[ -f … ] ||`. Bump **sau** khi engine đã vào và smoke đã xanh, để version luôn
mô tả đúng thứ đang nằm trên đĩa — không phải thứ ta định cài.

**Kiểm:** dự án ở `1.3.70`, cài bản `1.3.75` → sau update đọc ra `1.3.75`; `capability-stamp
--check` rc 0 và liệt kê được năng lực mới.

### B5 — Smoke rồi mới tuyên bố xong; đỏ thì tự quay lại

```sh
RC=0
echo '{"action":"write","file_path":"llmwiki/raw/x.md"}' \
  | python3 "$ROOT/harness/validators/no_write_raw.py" >/dev/null 2>&1 || RC=$?
[ "$RC" = "2" ] || { warn "smoke FAIL — khôi phục snapshot"; cp -R "$SNAP/harness/." "$ROOT/harness/"; exit 6; }
```

Smoke phải **bơm payload vi phạm và đòi rc 2**, đồng thời bơm một payload hợp lệ và đòi rc 0.
Kiểm `[ -f validator.py ]` chỉ chứng minh file tồn tại; một validator hỏng-luôn-báo-đỏ cũng
qua được bài kiểm đó.

**Kiểm:** cố ý làm hỏng một validator giữa B3 và B5 → installer khôi phục snapshot và trả
rc 6; `diff -r` trước/sau bằng rỗng.

## Thứ tự thi hành

B1 và B4 đứng đầu về giá trị trên chi phí: B1 chặn lỗi hỏng nặng nhất (hai bộ wiki) và code
đã có sẵn; B4 là bỏ một điều kiện `||`. B2+B5 đi thành cặp — snapshot không có rollback thì
chỉ là thư mục rác, rollback không có snapshot thì không chạy được. B3 để cuối vì nó cần
quyết định chính sách: file nào thuộc engine, file nào thuộc dự án.

## Global constraints

- **Fail-open giữ nguyên ở tầng hook, fail-closed ở tầng update.** Hook thiếu file thì im
  lặng bỏ qua (không khoá cứng phiên làm việc); nhưng update mà smoke đỏ thì phải quay lại
  và báo, không được để lại trạng thái nửa vời.
- **Không bao giờ tự migrate repo framework.** `is_framework_repo()` đã khoá điều này trong
  `needs_migration()`; mọi lối vào mới phải đi qua cùng hàm đó.
- **Idempotent.** Chạy hai lần liên tiếp trên cùng dự án: lần hai không đổi byte nào và
  không tạo snapshot mới.
- **Không hạ cấp âm thầm.** Bản đích mới hơn bản nguồn ⇒ dừng, báo, để người quyết.
- **Mọi bước phải kiểm được không cần mạng.** Dựng thư mục giả trong `mktemp -d` là đủ.

## Agent Task

1. Thêm cờ `--layout <root>` cho `harness/scripts/overstack_paths.py`, in một trong bốn giá
   trị `dot|plain|framework|none`; mở rộng `--self-test` phủ cả bốn.
2. Trong `install-harness.sh`, thay điều kiện `[ -d "$ROOT/llmwiki" ]` bằng lời gọi ở bước 1.
   Với `LAYOUT=dot|plain`, bỏ qua khối "Khung llmwiki (mode new)".
3. Bỏ `[ -f "$ROOT/harness/version.json" ] ||` ở dòng chép version, chuyển lời gọi xuống sau
   smoke, kèm `capability-stamp --update`.
4. Thêm B2 (snapshot, giữ 3 bản) và B5 (smoke hai chiều + rollback).
5. Thêm B0 (từ chối cây bẩn) và B3 (ba nhóm, so semver).
6. Viết `harness/tests/installer-update-test.sh` phủ sáu bước, chạy hoàn toàn trong
   `mktemp -d`; nối vào `fdk-gate` (nếu không, `bnal-selftest` sẽ báo drift — đúng như nó đã
   bắt `handoff-log` hôm nay).

## Sequence

```
B0 cổng cây sạch
   └─ B1 detect layout (overstack_paths --layout)
        ├─ none  → dựng khung mới (đường cũ, không đổi)
        └─ dot|plain → migrate:
             B2 snapshot harness/ + harness-local/ + from-version
             B3 đè engine (semver) · merge config · chừa vùng dự án
             B5 smoke hai chiều ── đỏ ─→ khôi phục snapshot, rc 6
                   │
                   xanh
                   ↓
             B4 chép version.json + capability-stamp --update
```

## Origin

- **Đo trên:** `harness/scripts/install-harness.sh` tại `88a566f`, các dòng 487 (detect),
  492-497 (khung mode new), 503-508 (chép engine + version), 553 (harness-local), 480-481
  (smoke bản global).
- **Hàm đã có mà installer chưa dùng:** `harness/scripts/overstack_paths.py::needs_migration`
  (self-test khoá ba ca, gồm ca repo framework).
- **Liên quan:** layout ẩn vào từ `e342280`; GH#111 (`OVERSTACK_HARNESS_DIR`); cạm bẫy số 4
  trong `llmwiki/wiki/sources/handover/070926-overstack-memory-selfreport.md` (không bump
  version = user cũ không nhận).
- **Date:** 2026-09-07
