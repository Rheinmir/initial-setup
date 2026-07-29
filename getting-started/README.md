# Getting Started — chạy khép kín dây chuyền /br (manual test full)

Runbook để bạn **tự tay đi hết một vòng** dây chuyền: từ tài liệu thô → sản phẩm code,
mỗi bước gọi slash nào và bỏ file gì vào đâu. Kèm cách cài đặt và bộ test chuẩn.

---

## 0. Cài đặt — MỘT dòng curl (không cần clone)

**Cần sẵn:** `curl`, `python3`, `git`. Thêm `node` nếu dùng `/visual-qa`.

```bash
curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash
```

Chạy lệnh này **ngay trong thư mục dự án của bạn**. Mặc định nó cài/update **cả 3 trụ**:
- **harness** — hook + rule (các luật tự cắn khi agent làm sai),
- **skills** — bộ skill (`/br`, `/unknown`, `/visual-qa`, …),
- **llmwiki** — khung wiki + `raw/` (hộp thư nhận tài liệu thô).

Cờ tuỳ chọn (đặt sau `bash -s --`):
```bash
... | bash -s -- --harness-only     # chỉ harness, bỏ skills + llmwiki
... | bash -s -- --clean            # cài mới: gỡ bản cũ rồi cài
... | bash -s -- --vendor claude,opencode
```
Đổi nguồn/branch: đặt biến `HARNESS_BASE=…` trước lệnh.

### Vào một DỰ ÁN MỚI — từ số 0

```bash
mkdir my-app && cd my-app && git init          # 1. có thư mục + git
curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash
                                               # 2. cài dây chuyền (3 trụ)
ls                                             # 3. thấy llmwiki/ + .claude/ (hook) xuất hiện
cp <tài-liệu-thô-của-bạn>.md llmwiki/raw/      # 4. bỏ tài liệu vào hộp thư raw/
```
Rồi mở Claude Code trong thư mục đó và gõ **`/br interview`** — vào §2 chạy tiếp vòng.

> Đã có llmwiki bản cũ muốn nâng cấp → gọi **`/harness-update`**. Đang ở CHÍNH repo framework
> → đã có sẵn, bỏ qua bước cài.

## 1. Kiểm hệ khoẻ TRƯỚC khi chạy

**Trong repo framework** (nơi có đủ `fdk/tools/`) — chạy BỘ TEST CHUẨN:
```bash
bash getting-started/smoke-test.sh
```
Chạy selftest MỌI tool cốt lõi (frame-lint, loop-runner, br-run, br-contract, br-sync,
loop-cost, br-rail, unknown, checkpoint, harness-doctor…). **`✅ HỆ KHOẺ` mới bắt đầu.**
(1 dòng `⚠ br-run integration` là env-dependent — không chặn, xem §5.)

**Trong DỰ ÁN MỚI cài bằng curl** — file này KHÔNG có sẵn ở đó (bootstrap chỉ cài harness +
skills + llmwiki). Thay vào đó: bootstrap **tự verify** ngay khi cài (trừ khi bạn thêm
`--no-verify`) — thấy nó báo cài xong không lỗi là được. Muốn kiểm sâu thì copy
`getting-started/smoke-test.sh` từ repo framework sang, hoặc gọi `/medic` nếu dự án có.

## 2. Vòng khép kín — slash gì, bỏ file gì

Chạy tuần tự lần đầu; sau đó lặp `run`/`status` tới khi mọi frame xanh.

| # | Bước | Gọi | BỎ FILE GÌ / LÀM GÌ | Ra gì |
|---|------|-----|---------------------|-------|
| 1 | Interview | `/br interview` | Copy tài liệu thô vào **`llmwiki/raw/`** (vd `getting-started/example/sample-input/PRD-link-shortener.md`) | `br/interview/NNN-questions.html` (mở xem) + `NNN-answers.md` (điền) |
| 2 | Compile | `/br compile` | Điền xong **`br/interview/NNN-answers.md`** | `br/BR.md` (clause_id) + `br/BR.clauses.json` |
| 3 | Slice | `/br slice` | Duyệt từng lát cắt khi được hỏi (STOP chờ bạn) | `br/frames/*.md` + `frame-lint` gác xanh |
| 4 | Run | `/br run <frame>` | (mỗi frame) — hoặc cả hàng đợi `br/queue.yaml` | code trong `scope_code` + commit per-frame + `<id>.run.json` |
| 5 | Status | `/br status` | — | `br/line-status.html` (frame chạy/kẹt/xong + truy lỗi→frame→clause) |
| 6 | Contract (nếu có UI) | `/br contract` | Khai `br/ui-layout.yaml` (screen↔route↔frames) | `br/UI-CONTRACT.{md,html}` |
| 7 | Visual QA (nếu có UI) | `/visual-qa` | App phải đang chạy | ảnh từng route + `MANIFEST.json` + `FINDINGS.md` |

**Xuyên suốt (bất cứ lúc nào):**
- `/unknown` — chỗ nào mơ hồ làm bạn/agent phân vân → bắt + hỏi làm rõ + lưu (không quên).
- `/br rail status|on|off|skip` — bật/tắt gate MỀM của harness (phanh cứng luôn giữ).
- `/br sync` — đẩy mỗi frame thành một GitHub sub-issue (dry-run trước).

## 3. Manual test FULL — checklist (dùng ví dụ có sẵn)

1. [ ] `bash getting-started/smoke-test.sh` → `✅ HỆ KHOẺ`.
2. [ ] `cp getting-started/example/sample-input/PRD-link-shortener.md llmwiki/raw/` → `/br interview` → mở HTML thấy câu hỏi hỏi-bù (về "lưu ở đâu", "custom alias"…).
3. [ ] Điền `answers.md` → `/br compile` → mở `br/BR.md` thấy clause_id + bảng "Giả định đang gánh".
4. [ ] `/br slice` → duyệt frame → `python3 fdk/tools/frame-lint.py check br/frames --root .` xanh.
5. [ ] `/br run <frame>` một frame → xem `<id>.run.json`: `scope_clean=true`, `changed_files ⊆ scope`.
6. [ ] `/br status` → mở `br/line-status.html` thấy màu frame.
7. [ ] (UI) khai `br/ui-layout.yaml` → `/br contract` → mở `br/UI-CONTRACT.html`.
8. [ ] (UI) chạy app → `/visual-qa` → đọc ảnh + `FINDINGS.md`.
9. [ ] Thử `/br rail skip` rồi `/br run` → thấy gate mềm bỏ 1 lần (phanh cứng vẫn gác); `/unknown` ghi một chỗ mơ hồ → thấy dòng cảnh báo vào `MEMORY.md`.

## 4. Bản đồ khái niệm (nhắc nhanh)

- **clause** = điều khoản nghiệp vụ trong BR (vd `C5.3`). **frame** = một mẩu việc gắn code
  (`scope_code` + `acceptance_test`) cắt từ clause. **screen/route** = trục hiển thị (tách
  khỏi frame). **assumption** = chỗ tự bù, chờ xác nhận. **unknown** = chỗ mơ hồ chưa làm rõ.
- Trục CODE (frame, frame-lint gác) ≠ trục HIỂN THỊ (screen/route, ui-layout). Regroup screen
  KHÔNG re-slice frame.

## 5. Troubleshoot

- **`⚠ br-run integration` đỏ trong smoke-test:** đây là selftest *tích hợp* (cần git worktree
  + loop-runner end-to-end), đỏ theo môi trường — KHÔNG chặn workflow. Các test logic khác xanh
  là đủ để bắt đầu.
- **Lệnh báo "no such file":** phần lớn tool cần chạy từ GỐC project và có `--root .`. Đứng đúng
  thư mục.
- **`/visual-qa` không chụp được:** cần `node` + `playwright-core` (`npm i playwright-core`) +
  app đang chạy; extension MCP KHÔNG chụp localhost (đó là lý do có visual-qa headless).

---
*Bộ test chuẩn: `getting-started/smoke-test.sh` · ví dụ input: `example/sample-input/` · chi
tiết mode: `skills/br/SKILL.md`.*
