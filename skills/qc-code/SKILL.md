---
name: qc-code
description: >-
  Review code phong cách SENIOR 10 năm — bốn mục security · performance · naming · logic, mỗi mục cho
  ĐIỂM/10 + LỖI NẶNG NHẤT + CÁCH SỬA, rồi một kết luận PASS-sang-bước-kế hay CẦN-SỬA. Mục logic tìm bug
  (null/rỗng/âm/overflow, off-by-one, race) và SINH một test-case tái hiện cho mỗi bug (đặt tên qc-*),
  các test đó auto-chạy qua hook tất định (0-token, không LLM). Gọi khi user nói "qc code", "review code",
  "soi code", "chấm điểm code", "kiểm tra chất lượng code", "/qc-code". KHÁC /orca-sec-scans (Trivy quét
  TĨNH — vuln/misconfig/secret) và /code-review built-in (review tổng quát): qc-code là format senior
  bốn-mục-chấm-điểm-verdict + sinh test tái hiện. Mặc định review DIFF hiện tại; chỉ định file khi cần.
---

# Skill: qc-code

## When to use
- User muốn một cặp mắt senior soi code trước khi chốt: "review code", "soi code", "chấm điểm code".
- Trước commit một thay đổi đáng kể — cắm tùy chọn vào `/orca-workflow` trước `verify-before-commit`.
- KHÔNG dùng cho: quét bảo mật tĩnh (đó là `/orca-sec-scans` — Trivy) hay xử lý một sự cố đã xảy ra (đó là `/orca-issue` — repro-first).

## Phạm vi review (mặc định = diff hiện tại)
Mặc định soi **thay đổi kể từ base** (`git diff` từ commit/branch gốc) — đúng lúc trước commit, nhanh, đúng thứ vừa viết. User chỉ định file/thư mục thì soi cái đó. KHÔNG mặc định toàn codebase (chậm, tốn token, phần lớn không đổi).

## Steps
1. **Xác định phạm vi** — `git diff <base>..HEAD --stat` (hoặc file user nêu). Đọc code trong phạm vi đó.
2. **Chấm bốn mục** (mục dưới). Mỗi mục: **điểm/10 · lỗi nặng nhất · cách sửa**. → Xong khi cả bốn mục đều có đủ ba phần.
3. **Mục logic: sinh test tái hiện** cho mỗi bug (mục "logic & bug" bên dưới). → Xong khi mỗi bug có một test đỏ chạy được.
4. **Kết luận** — `PASS` (sang bước kế) hay `CẦN SỬA` (liệt kê phải sửa gì trước khi pass). → Xong khi verdict rõ + danh sách phải-sửa nếu CẦN SỬA.
5. **Ghi test vào dự án** (mục "Ghi test" dưới) + nhắc `qc-regression.py --run` auto-chạy chúng.

## Bốn mục

### 1. Security — điểm/10 · lỗi nặng nhất · cách sửa
Soi: **SQL injection** (chuỗi nối vào query, thiếu parameterize) · **XSS** (output không escape, `innerHTML`/`dangerouslySetInnerHTML`) · **lộ API key / secrets** (hardcode key, secret trong log/repo) · **validate input** (nhận dữ liệu ngoài không kiểm) · **phân quyền** (thiếu check ai-được-làm-gì, IDOR). Đây là ranh giới tin cậy — không lười ở đây (carve-out CLAUDE.md).

### 2. Performance — điểm/10 · lỗi nặng nhất · cách sửa · 3 điểm chậm nhất
Soi: **query N+1** (vòng lặp gọi DB từng phần tử thay vì một query) · **vòng lặp lồng vô ích** (O(n²) khi O(n) đủ) · **memory leak âm thầm** (listener/timer không gỡ, ref giữ mãi, cache không giới hạn). **Chỉ ra 3 điểm chậm nhất** và cách tối ưu từng cái (với ước lượng độ lớn: O(?), số round-trip).

### 3. Naming & readability — điểm/10 · lỗi nặng nhất · bảng đổi tên
Soi: **tên có nói đúng việc nó làm** không (hàm `getUser` mà ghi DB, biến `data` vô nghĩa) · **convention nhất quán** (camelCase/snake_case lẫn lộn, số nhiều/ít lộn). **Trả về bảng:**

| Tên cũ | Tên mới | Lý do |
|--------|---------|-------|
| `d` | `dueDate` | tên một chữ không nói được gì |

### 4. Logic & bug — điểm/10 · lỗi nặng nhất · TEST tái hiện mỗi bug
Soi: **edge case** (null · rỗng · số âm · overflow) · **off-by-one** (`<` vs `<=`, index cuối) · **race condition** (state chia sẻ, await xen kẽ, đọc-rồi-ghi không atomic). Mỗi bug tìm được → **viết một test-case ĐỎ tái hiện lỗi** (chứng minh bug có thật, không phải nghi ngờ). Test đỏ là dữ kiện; verdict là ý kiến.

## Bản đồ 13 nhóm lỗi (gstack) + severity

Mỗi finding gắn đúng MỘT nhóm + MỘT severity, format: `[<nhóm>][<severity>] <mô tả> — <cách sửa>`. 5 nhóm CRITICAL soi trước:

| # | Nhóm (CRITICAL) | Soi cái gì |
|---|---|---|
| 1 | SQL & data safety | Nối chuỗi vào query (kể cả đã `.to_i`) thay vì parameterize; check-then-set không atomic (TOCTOU); ghi DB vòng qua validation của model; N+1 thiếu eager-load. |
| 2 | Race condition & concurrency | Đọc-kiểm-ghi không có unique constraint; find-or-create thiếu index → gọi song song đẻ bản ghi trùng; chuyển status không dùng `WHERE old_status=?` atomic; render HTML thô trên dữ liệu người dùng (XSS). |
| 3 | LLM output trust boundary | Giá trị LLM sinh (email/URL/tên) ghi DB không validate format; output có cấu trúc không kiểm type/shape; URL do LLM sinh được fetch không allowlist (SSRF); output LLM vào knowledge-base không sanitize (stored prompt-injection). |
| 4 | Shell injection | `subprocess`/`os.system` với `shell=True` + nội suy chuỗi — dùng argument array; `eval`/`exec` trên code LLM sinh không sandbox. |
| 5 | Enum & value completeness | Thêm một giá trị enum/status/tier mới → PHẢI đọc code NGOÀI diff: mọi consumer switch/filter/hiển thị giá trị anh em, mọi allowlist `%w[]`, mọi chuỗi `case/if-elif` — thiếu một consumer là bug âm thầm. |

8 nhóm INFORMATIONAL (soi sau, thiên về auto-fix): **async/sync mixing** (gọi sync blocking trong `async def`, `time.sleep` thay `asyncio.sleep`) · **column/field-name safety** (tên cột trong ORM query lệch schema → rỗng âm thầm) · **LLM prompt** (list 0-indexed trong prompt, prompt khai tool không khớp code, limit khai nhiều chỗ dễ drift) · **type coercion** (giá trị qua biên Ruby→JSON→JS đổi kiểu; input hash/digest không normalize kiểu) · **view/frontend** (style inline re-parse mỗi render, O(n·m) lookup trong view, filter phía app thay vì `WHERE`) · **time-window safety** ("hôm nay" không phủ 24h, hai feature dùng hai kiểu bucket thời gian cho cùng dữ liệu) · **completeness gaps** (bản 80-90% khi 100% chỉ tốn thêm chút code, test thiếu nhánh negative dễ bổ sung) · **distribution & CI/CD** (version tool trong workflow lệch dự án, secret hardcode, tag `v1.2.3` vs `1.2.3` lệch nhau, publish không idempotent).

**Severity** (distill từ awesome-skills/code-review-skill): `[blocking]` = phải sửa trước khi merge · `[important]` = nên sửa, không đồng ý thì bàn · `[nit]` = nhỏ, tuỳ tác giả · `[suggestion]` = hướng khác đáng cân nhắc, không bắt buộc. Nhóm CRITICAL thiên về `blocking/important`; nhóm INFORMATIONAL thiên về `nit/suggestion` — nhưng severity đi theo TÁC ĐỘNG thật của finding, không đi theo nhóm một cách máy móc.

## Nhận review — verify trước khi sửa

Chiều ngược của skill này: khi MÌNH là người nhận finding (từ người, từ LLM reviewer, kể cả từ chính /qc-code). Finding là CLAIM, chưa phải sự thật (distill từ `obra/superpowers` receiving-code-review):

1. **Đọc hết feedback rồi mới phản ứng** — restate yêu cầu bằng lời của mình; chỗ nào chưa hiểu thì HỎI trước khi sửa bất kỳ mục nào (các mục có thể liên quan nhau — hiểu một nửa là sửa sai).
2. **Verify claim với code thật** — chạy hoặc đọc đúng đoạn được trỏ: claim có đúng với codebase NÀY không, sửa theo có vỡ gì không, code hiện tại có lý do tồn tại không.
3. **Chỉ sửa khi đã tự thấy lỗi** — finding sai thì phản hồi bằng lý lẽ kỹ thuật kèm bằng chứng, không lặng lẽ bỏ qua, cũng không lặng lẽ làm theo. Không verify được thì nói thẳng: "chưa kiểm được vì thiếu X".
4. **Sửa từng mục một, test từng mục** — không gộp một lượt rồi hy vọng.
5. **Cấm màn diễn đồng thuận** — "You're absolutely right!" / khen ngợi feedback thay cho hành động là tín hiệu đang blind-comply. Xác nhận kỹ thuật hoặc bắt tay làm, không diễn.

Blind-comply với review sai tạo ra bug mới mang vẻ mặt "đã được review" — lớp bug khó nghi ngờ nhất.

## Kết luận (verdict)
Một trong hai, kèm lý do:
- **PASS** — không lỗi nặng ở mục nào, sang bước kế được.
- **CẦN SỬA** — liệt kê **cụ thể** phải sửa gì trước khi pass (ưu tiên security + logic-có-test-đỏ trước naming).

> **Verdict là ADVISORY — người quyết, không chặn commit.** Thứ gác cứng là các test tái hiện (đỏ→xanh). Đừng để user tưởng "qc-code PASS = an toàn tuyệt đối"; nó là một cặp mắt senior, không phải bằng chứng.

## Ghi test tái hiện vào dự án
Mỗi test ở mục logic:
- **Đặt vào thư mục test chuẩn của dự án** — tự phát hiện: `tests/` · `test/` · `__tests__/` · file `*_test.py` · `*.spec.ts` · `*.test.js` cạnh nguồn. Không có → báo rõ và để test cạnh file nguồn, KHÔNG đoán bừa cấu trúc.
- **Tên `qc-<slug-bug>`** (vd `qc-off-by-one-pagination`) — phân biệt test do qc-code sinh, để `qc-regression.py` gom được.
- **Chạy bằng runner có sẵn** của dự án (pytest/vitest/jest) — không đẻ framework test mới.
- Test PHẢI đỏ trước khi fix (tái hiện), xanh sau khi fix (bằng chứng). Nếu bug quay lại → test đỏ lại (chống tái phát).

## Auto-chạy test (tất định, 0-token)
`python3 harness/scripts/qc-regression.py --run` chạy đúng các test `qc-*` và báo đỏ/xanh — **không gọi LLM**. Nó auto-chạy ở `verify-before-commit` (trước commit); bật thêm PostToolUse cho phản hồi tức thì nếu muốn. Fail-open nếu chưa có test `qc-*` nào. Đây là phần "tự động hook khi sửa code" — chỉ hook phần rẻ tất định, LLM review (skill này) giữ gọi tay.

## Rules
- **Tách đắt/rẻ:** LLM review (skill này) = gọi tay / bước workflow tùy chọn. Test tự-sinh = auto-chạy qua hook tất định. KHÔNG bao giờ gọi LLM trong hook (nguyên tắc hook-0-token của overstack).
- **Verdict advisory, test tất định gác cứng** — không để LLM verdict chặn commit.
- **Không dẫm:** `/orca-sec-scans` = Trivy tĩnh · `/code-review` built-in = tổng quát · `/orca-issue` = sự cố repro-first. `/qc-code` = senior 4-mục-chấm-điểm + sinh test.
- **Review có unknown?** Nếu một nhận định phụ thuộc thứ chưa chắc (config prod, hành vi runtime chưa thấy) → ghi nợ `[[150726-unknown-ledger]]` thay vì khẳng định bừa.

## Origin
- Distill từ yêu cầu user 2026-07-15 (qc-code 4 mục + sinh test + auto-hook). Quyết định "nối vào đâu" đã hỏi user → option 3 (LLM thủ công, test auto-hook tất định), phạm vi diff hiện tại.
- Absorb qua `/propose` → `150726-qc-code-skill`, task `T-260715-04`.
- **Absorb 2026-07-17 (adapt_mode: dissolve, T-260717-02):** bản đồ 13 nhóm lỗi distill từ `garrytan/gstack` (`review/checklist.md`); severity từ `awesome-skills/code-review-skill`; mục "Nhận review" từ `obra/superpowers` (`receiving-code-review`). Clone depth-1 trong scratchpad/, không vendor bytes.
- **Commit:** _(verify-before-commit điền)_
