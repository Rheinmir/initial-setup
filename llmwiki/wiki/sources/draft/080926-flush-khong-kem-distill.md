---
type: issue
kind: process
title: "Vế GHI của problem-tree tự động, vế DỌN thủ công — thẻ pending tồn hàng tuần không ai thấy"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, process, problem-tree, r17, feedback-loop, medic]
timestamp: 2026-09-08
id: 080926-flush-khong-kem-distill
source_session: "Phiên vẽ sơ đồ hoh 2026-09-07/08 — /fdk rà cây trước khi kết lượt, thấy 3 thẻ pending tồn 25 ngày"
---

# Issue: flush tự động mà distill thủ công

## Vấn đề (một câu)

Hook SessionEnd (R17) **tự** ghi thẻ `p-auto` khi phiên chạm bề mặt framework, nhưng việc
**chưng lọc** thẻ đó chỉ xảy ra khi có người nhớ — nên nợ tích lại hàng tuần mà không cổng nào
kêu.

## Bối cảnh & bằng chứng

Đây là lần **thứ hai** cùng một khuôn, và `[[p-10]]` đã gọi đúng tên cách sửa từ hồi đó —
*"cơ chế flush p-auto phải kèm distill"* — rồi không ai dựng.

| Lô | Thẻ | Tồn bao lâu | Ai phát hiện |
|---|---|---|---|
| 02/07 → 20/07 | `p-auto-02…20` (19 thẻ) | 19 ngày | người, tình cờ, lúc triage 21/07 |
| 14/08 → 18/08 | `p-auto-21/22/23` | **25 ngày** | người, tình cờ, lúc /fdk 08/09 |

Vế ghi có hook nên chạy đều; vế dọn không có gì nên phụ thuộc trí nhớ. Hai lô trên đều chỉ lộ
ra khi có người ngồi đọc sổ, không phải khi có cổng kêu. Chính lượt `/fdk` hôm nay cũng suýt bỏ
qua: đã thêm node mới rồi định đi tiếp, dù skill bắt "TRƯỚC KHI kết thúc turn phải rà và cập
nhật cây".

Lỗi thứ hai lộ ra khi đọc kỹ: `p-auto-21` và `p-auto-22` **trùng khít** — cùng phiên
`dba79064`, cùng ngày, cùng danh sách bề mặt. `flush_problem_tree()` không chốt idempotent theo
`session_id`, nên SessionEnd bắn lần hai cho một phiên là ghi thẻ thứ hai.

## Đã làm

**1. Dọn backlog — chưng lọc 3 thẻ, có bằng chứng git, không chép phán quyết cũ.**

Lượt triage 21/07 kết luận "bề mặt toàn artifact tự sinh". Lô này **không** thế: `p-auto-21/22`
có `harness/poc-vendor-neutral/install.sh` và 2 file config. Nên phải truy git thật:

| Thẻ | Phiên | Kết luận |
|---|---|---|
| `p-auto-21` | `dba79064` 14/08 | Công việc đã ship qua `1474a88` *"checkpoint trước merge graph-engineering"*, bề mặt khớp đúng commit đó. Khiếm khuyết THẬT của phiên (xoá nhầm `llmwiki/commands/serve`) đã bị bắt và khôi phục ở vòng lint-drift 04/09. Không còn gì treo. |
| `p-auto-22` | `dba79064` 14/08 | Trùng khít `p-auto-21` — không phải vấn đề thứ hai mà là lỗi hook. |
| `p-auto-23` | `72190e1c` 18/08 | Bề mặt là artifact tự sinh + ghi chép innovation; tính năng của cửa sổ đó ship qua `41ed323` *"feat(graph-mode)"*. Không có vấn đề riêng. |

Cả ba: `status: solved`, `parent: p-10`, `scope: ["harness"]`.

**2. Vá lỗi ghi trùng** — `llmwiki/.claude/hooks/session_end.py`: chốt idempotent theo
`session_id`; phiên đã có thẻ pending thì không ghi thêm. Kèm `indent=1` cho khớp định dạng sổ —
trước đó hook ghi `indent=2` nên mỗi lần xả sổ đẻ một diff ~950 dòng che mất phần thật sự đổi.

**3. Dựng vòng phản hồi cho vế dọn** — probe `problemtree` trong `fdk/tools/medic.py`: đếm thẻ
còn `pending` và tuổi thẻ già nhất, cảnh báo từ `STALE_CARD_DAYS = 14`. Ngưỡng 14 vì hai lô đã
trôi 19 và 25 ngày. Chọn **warn** chứ chưa **fail** theo thang Meadows — thêm vòng phản hồi
trước, đổi luật chơi sau; nâng lên fail khi backlog giữ được ở 0.

**4. Test hồi quy** — `harness/tests/flush-idempotent-test.sh`, 4 assertion, đã wire vào CI.

## Phạm vi

`llmwiki/.claude/hooks/session_end.py` · `fdk/tools/medic.py` · `harness/tests/flush-idempotent-test.sh`
· `.github/workflows/harness.yml` · `llmwiki/html/fdk-problem-tree.html`.

## Không thuộc phạm vi

- Không tự động hoá phần *phán quyết* của distill — đọc bề mặt rồi kết luận vẫn là việc của người
  hoặc agent có ngữ cảnh; probe chỉ **nhắc**, không tự đóng thẻ.
- Không sửa cách sinh id `p-auto-NN` (`count + 1` sẽ đụng id nếu có ai xoá thẻ) — lỗi khác, chưa gặp.
- Không đụng `p-10`, chỉ ghi thêm một câu rằng vế dọn nay đã có vòng phản hồi.

## Tiêu chí HOÀN THÀNH

- [x] 3 thẻ `p-auto-21/22/23` chưng lọc xong, `medic problemtree` báo `cây vấn đề sạch — 0 thẻ pending`
- [x] Cùng một phiên bắn SessionEnd hai lần → vẫn 1 thẻ; phiên khác → vẫn ghi được
- [x] Xả sổ giữ `indent=1`, không đẻ diff toàn file
- [x] `flush-idempotent-test.sh` 4/4 PASS và đã wire vào `.github/workflows/harness.yml`
- [ ] `/fdk-uat` xanh, không còn lỗi

## Assign & lý do

`@Rheinmir` · Claude · `/fdk`. Đã thực hiện trong chính lượt raise vì việc dọn không tách rời
được việc hiểu *vì sao nó tồn đọng*: phải đọc từng thẻ mới biết cái nào là vấn đề thật, và chính
lúc đọc mới lộ ra lỗi ghi trùng.

## Origin

- **Raise + fix bởi:** phiên vẽ sơ đồ `hoh` 2026-09-07/08, lượt `/fdk` rà cây trước khi kết lượt.
- **Bằng chứng:** `git show 1474a88` · `git show 41ed323` · `medic problemtree` trước (3 thẻ,
  già nhất 25 ngày) và sau (sạch) · `flush-idempotent-test.sh` 4/4.
- **Nền:** `[[p-10]]` — "cơ chế flush p-auto phải kèm distill", nêu 21/07, dựng 08/09.
