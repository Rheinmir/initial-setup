---
type: issue
kind: foundation
title: "fdk-gate đỏ 4/21 ngay trên orca pristine — cổng đang bị vòng qua chứ không phải đang gác"
status: open
assignee: "@Rheinmir"
dispatch: human
entry: /fdk
priority: P1
tags: [issue, foundation, fdk-gate, harness, ci, forcing-function]
timestamp: 2026-09-05
id: 050926-fdk-gate-red-on-orca
source_session: "Phiên chưng cất skill reskin (PR#107) — submit qua fdk-kit.sh bị chặn, đo baseline mới lộ ra gate đã đỏ sẵn"
---

# Issue: fdk-gate đỏ 4/21 ngay trên orca pristine

## Vấn đề (một câu)

`harness/scripts/fdk-gate.py` đỏ **4/21 step trên chính `orca` khi chưa có thay đổi nào**, nên `fdk-kit.sh submit` (chạy gate rồi mới cho push) không bao giờ qua được — mọi submit buộc đi đường thủ công, tức là cổng đang bị **vòng qua** chứ không phải đang **gác**.

## Bối cảnh & bằng chứng

Phát hiện khi chưng cất skill `reskin` (PR#107) và định submit đúng đường `/fdk` mô tả:

```
bash .overstack-kit/fdk/tools/fdk-kit.sh submit skill/reskin "<msg>"
```

`submit` chạy `fdk-gate.py` với `set -euo pipefail`, gate đỏ thì abort trước khi commit. Để biết bao nhiêu phần là do mình, tôi stash sạch thay đổi rồi chạy gate trên bản pristine của `orca`:

```
git stash push -u -m "<tag>" && python3 harness/scripts/fdk-gate.py
```

Kết quả pristine: **5 step đỏ**, không cái nào do nhánh mới gây ra.

Điểm cần nói rõ: đây **không phải** lời kêu ca rằng gate quá nghiêm. Trong chính lượt này gate đã bắt được một bug thật của tôi — `description` trong frontmatter chứa `': '` làm YAML hỏng, và CLI `skills` **bỏ qua skill có frontmatter hỏng mà không báo lỗi**, nghĩa là skill sẽ nằm trong repo mà không bao giờ tới người dùng. Không có gate thì PR đó merge xong là có một skill chết. Gate có giá trị; vấn đề là nó **không còn xanh được nữa** nên không ai chạy nó trước khi push.

### Bốn step đỏ, có bằng chứng cụ thể

| step | lệnh gate chạy | triệu chứng đo được |
|---|---|---|
| `L4 wiki-health` | `wiki-health.py --wiki-dir llmwiki/wiki --fail-on broken,summary` | **12** broken wikilink; ví dụ `entities/repowise.md` trỏ `[[code-graph]]`, `[[frontier-gap-scan]]`, `[[innovation-110826]]` — không có node nào tồn tại. `bare_date_summary` = 0 (vế summary đã sạch) |
| `task-lifecycle` | `harness/validators/task_lifecycle.py --root .` | 1 task state lạ: `T-260820-01` mang `completed` (hợp lệ chỉ `proposed/approved/dispatched/done` + terminal `superseded`). 4 draft trỏ task không có trong `tasks.json`: `T-260721-02`, `T-260721-01`, `T-260720-02`, `T-260902-01` |
| `bnal self-test wired` | `harness/scripts/bnal-selftest.py --check` | `overstack_paths` có `--self-test` nhưng chưa được nối vào step "BNAL feature self-tests" của `fdk-gate.py` |
| `graph-engineering tests` | 7 script `harness/tests/ge-*.sh` | `ge-reachability` đỏ vì `fdk/skills.search.json` lệch `skills/` (đã sửa được bằng `build-skill-search.py`). `ge-travel` đỏ ở `fresh-install-smoke --local`, mục "parity hứa↔giao": doc hứa một skill mà bản cài global trên máy không có |

### Ba cái này sửa được ngay, một cái không

`ge-reachability` chỉ cần chạy lại generator. `wiki-health` và `bnal-selftest` là nợ dữ liệu/wiring, sửa được và kiểm chứng được.

`ge-travel` khác về **chất**: nó so tài liệu với **bản cài global trên máy đang chạy**, nên hễ thêm skill mà chưa `npx skills add . --global --all` là đỏ. Mà lệnh đó ghi vào `$HOME` của người chạy — một side-effect ngoài repo. Nghĩa là gate đang buộc mọi người **mutate máy mình** thì mới push được. Đây có thể là chỗ đáng thiết kế lại (so với bản cài trong sandbox mà smoke tự dựng, thay vì global thật), chứ không chỉ là "sửa dữ liệu cho xanh".

## Phạm vi

- `harness/scripts/fdk-gate.py` và bốn kiểm tra nó gọi.
- Dữ liệu: `llmwiki/wiki/**` (wikilink hỏng), `harness/metrics/tasks.json` + draft trỏ task.
- `harness/scripts/fresh-install-smoke.sh` — phần "parity hứa↔giao".
- Universal, không local: ai clone `orca` cũng gặp.

## Không thuộc phạm vi

- Không nới lỏng luật cho xanh. Xoá/tắt step là làm hỏng đúng thứ đang cần cứu.
- Không sửa nội dung skill/PR nào đang mở.
- Không đổi hợp đồng tracker hay quy trình submit — chỉ làm cho gate xanh được trở lại.

## Hướng gợi ý (không bắt buộc)

1. **Trả bốn step về xanh** theo thứ tự rẻ→đắt: regenerate artifact → vá 12 wikilink → nối `overstack_paths` vào gate → dọn 5 mục task-lifecycle.
2. **Tách "gate của repo" khỏi "trạng thái máy người chạy".** `ge-travel` nên so với bản cài trong sandbox mà smoke tự dựng, không so với `$HOME`. Còn nếu cố ý so global thì `fdk-kit.sh submit` phải nói thẳng ra và tự chạy bước cài, đừng để người dùng đoán.
3. **Thêm forcing function chống tái phát**: CI chạy `fdk-gate` trên chính `orca` sau mỗi merge, đỏ thì báo ngay. Gate chỉ đỏ khi có người vừa làm nó đỏ mới truy được nguyên nhân; đỏ tích luỹ nhiều tuần thì không ai dám nhận.
4. Cân nhắc cho `fdk-kit.sh submit` in **diff giữa baseline và hiện tại** thay vì chỉ pass/fail — "nhánh của bạn không thêm step đỏ nào" là thông tin đủ để cho push, và nó khớp với cách người ta thực sự làm việc trên một repo có nợ.

## Tiêu chí HOÀN THÀNH

- `python3 harness/scripts/fdk-gate.py` trên `orca` sạch, **không thay đổi gì**, in `ĐỦ 21/21`.
- `bash fdk/tools/fdk-kit.sh submit <branch> "<msg>"` chạy trọn từ đầu tới lúc mở PR, không phải đi đường thủ công.
- Có một đường tự động (CI hoặc hook) chạy `fdk-gate` trên `orca` sau merge và báo khi đỏ.
- Nếu chọn hướng 2: `ge-travel` xanh trên một máy **chưa từng** chạy `npx skills add --global`.

## Assign & lý do

`@Rheinmir`, `dispatch: human`, nhãn `ready-for-human`. Ba trong bốn step là dọn dữ liệu, một agent làm được. Nhưng `ge-travel` là **quyết định thiết kế** — gate nên so với repo hay với máy người chạy — và mục 4 đổi chính định nghĩa "đủ điều kiện push". Giao cho CLI headless thì nó chỉ còn cách đoán thay người rồi im lặng, đúng thứ nhãn `ready-for-human` sinh ra để chặn.

## Origin

Raise bởi `/raise-issue` trong phiên chưng cất skill `reskin` (2026-09-05, session `012S7a8C`). Bằng chứng: chạy `fdk-gate.py` trên `orca` pristine (stash sạch rồi chạy) và trên nhánh `skill/reskin`; output từng validator chép trong bảng trên. Node problem-tree tương ứng: `p-fdk-gate-baseline` trong `llmwiki/html/fdk-problem-tree.html`. PR liên quan: [Rheinmir/setup#107](https://github.com/Rheinmir/setup/pull/107).
