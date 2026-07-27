# harness-local/ — harness RIÊNG của dự án này

Nơi **dự án này** tự phát triển rule/validator riêng, chạy **song song** với harness framework
(R1–R13) mà KHÔNG giẫm chân nó. Folder này **thuộc về dự án** — `sync-template`/framework-update
**không bao giờ đụng** (không nằm trong `.template-manifest.json`).

## Cách thêm một rule (3 bước)
1. `cp harness-local/validators/_template.py harness-local/validators/<ten>.py` rồi viết logic.
2. Khai rule vào `harness-local/policy.yaml` với id **`P<n>`** (P = project; **KHÔNG** dùng `R<n>` — đụng framework), **kèm `fixtures: {bad, good}`** (xem dưới).
3. Xong. Rule tự chạy ở: write-time (PreToolUse hook), commit (pre-commit), merge (CI) — y như framework.

## Fire-drill — chứng rule RIÊNG còn cắn (bắt buộc khai fixtures)
Rule framework (R1–R18) được `harness-doctor` dựng fixture xấu/tốt để CHỨNG còn cắn (bắt "dark rail" —
rule chết âm thầm vì hook fail-open). Rule RIÊNG của bạn framework không đoán được fixture, nên **bạn tự khai**:

```yaml
- id: P1
  name: no-console-log
  validator: harness-local/validators/no_console_log.py
  fixtures:
    bad:  { path: "src/x.js", content: "console.log(1)" }   # PHẢI bị chặn (exit 2)
    good: { path: "src/x.js", content: "const x = 1" }      # PHẢI qua (exit 0)
```

`harness-local/run.py firedrill` drive validator qua hai fixture: `bad` phải chặn, `good` phải qua.
- Rule CÓ validator mà **thiếu fixtures** → firedrill FAIL (blind-spot: không chứng được rule còn sống ≡ dark rail của chính rule đó).
- `bad` không bị chặn → **rule CHẾT** (đỏ). `good` bị chặn → rule **over-block** (đỏ).
- **CI downstream chạy `firedrill` mỗi PR** — rule riêng của bạn mục ruỗng thì CI đỏ ngay, không im lặng.
- CI **không gọi `run.py` của repo** mà chạy engine luôn-mới từ harness-src (pin `HARNESS_REF`), trỏ
  `HARNESS_LOCAL_DIR` vào thư mục này: `run.py` repo có thể là bản cũ chưa có `firedrill` (mode lạ
  rơi về `check` → degrade âm thầm). Engine đi theo framework; rules/validators ở lại với dự án.

## Contract của một project validator (API ỔN ĐỊNH — framework cam kết không đổi)
Một validator = 1 file `.py` trong `harness-local/validators/` (KHÔNG bắt đầu bằng `_`):

- **Input** — nhận event qua **stdin JSON** *hoặc* **argv là đường dẫn file**:
  - `{"action":"write","file_path":"...","content":"..."}` — khi agent ghi file (PreToolUse)
  - `{"action":"bash","command":"..."}` — khi agent chạy Bash
  - `{"action":"stop"}` — cuối lượt
  - hoặc `validator.py <file1> <file2> ...` — pre-commit/CI truyền file đổi
- **Output / exit code:**
  - `exit 0` = PASS (cho qua)
  - `exit 2` = BLOCK (chặn) — in lý do ra **stderr**
- **Fail-open:** lỗi bất ngờ → exit 0 (đừng làm gãy phiên/commit của người khác).

Vì cùng contract, bạn có thể copy một validator framework (`harness/validators/*.py`) làm mẫu.

## Vì sao không giẫm chân (sandbox các case fail)
- **Không đụng framework:** id `P<n>` ≠ `R<n>`; validator nằm dir riêng; framework không đọc folder này để quyết định gì.
- **Sống sót framework-update:** ngoài manifest → `sync-template` bỏ qua. Contract ổn định → validator cũ vẫn chạy khi framework lên version.
- **Độc lập:** rule project + rule framework đều phải pass (AND). Project KHÔNG tắt được rule framework.
- **An toàn khi vắng:** không có rule nào → runner no-op, dự án chạy như thường.

## Đăng ký (policy.yaml)
Mỗi rule một block (xem `policy.yaml`). Dùng `harness-local/run.py --list` để xem rule hiện có,
`harness-local/run.py --check` để self-test (id hợp lệ + validator compile),
`harness-local/run.py firedrill` để CHỨNG mỗi rule còn cắn (bad→chặn, good→qua).
