---
name: dym-agent-desktop-session
disable-model-invocation: true
description: "Session + trace JSONL + xuất HTML của agent-desktop làm BẰNG CHỨNG cho một lượt computer-use, và cursor riêng cho từng agent khi nhiều agent chạy song song trên một máy. Gọi khi cần log lại 'agent đã bấm gì' hoặc khi nhiều agent tranh nhau con trỏ."
---

# dym-agent-desktop-session

## When to use
- Một lượt thao tác desktop cần **để lại biên lai**: `/br qc`, `/fdk-poc`, hay bất kỳ
  verdict nào phải cãi lại được bằng log chứ không bằng lời model.
- **Nhiều agent chạy song song** trên cùng một máy macOS (đúng bối cảnh Orca worktree) —
  chuột là tài nguyên dùng chung, cần lease và cần biết cursor nào của agent nào.
- Chỉ chạy một lệnh đọc lẻ → bỏ qua skill này, session là thừa.

## Steps

1. **Mở session một lần cho cả lượt việc** (trace bật sẵn):

```bash
$AD session start --name br-frame-07        # → data.session_id, data.next
export AGENT_DESKTOP_SESSION=run-1788964205617-6007-0
```
Cần ảnh pre/post mỗi hành động để replay: `session start --screenshots`
(`artifacts: full`) — **nhạy cảm**, coi như screenshot, đừng đẩy vào repo.

2. **Chạy việc bình thường** — mọi lệnh trong scope tự ghi JSONL, không cần `--trace`
   từng lệnh. Segment nằm ở
   `$AGENT_DESKTOP_HOME/sessions/<id>/trace/<pid>-<procTs>.jsonl`.

3. **Đọc lại bằng chứng**:

```bash
$AD trace show --limit 200                  # JSON gọn cho agent đọc
$AD trace export --out ./scratchpad/run.html   # HTML một file cho người xem
```
Đo thật: mỗi lệnh sinh `command.start` → sự kiện nghiệp vụ (vd `snapshot.saved` kèm
`ref_count`, `snapshot_id`) → `command.end` kèm `duration_ms`, `ok`. Có `ts_ms` và `seq`
đơn điệu theo tiến trình → ghép được thứ tự thật giữa nhiều tiến trình.

4. **Đóng và dọn**:

```bash
$AD session end $AGENT_DESKTOP_SESSION
$AD session gc --ended --older-than 86400
```

5. **Nhiều agent song song** (chưa kiểm chứng bằng chạy thật trong lượt này — theo doc
   của tool):

```bash
$AD session start --cursor --multi-agent    # một session dùng chung
AGENT_DESKTOP_AGENT_ID=frame-07 $AD click "@s..:e5"   # mỗi agent một ID ổn định
$AD cursor-overlay disable                  # tắt mọi cursor của session
```
Harness truyền **cùng một session ID** cho mọi subagent; mỗi subagent tự khai
`AGENT_DESKTOP_AGENT_ID` (hoặc `--agent-id`, cờ thắng env). Ba ID khác nhau → ba con trỏ
có màu/nhãn riêng. Thao tác UI bắt buộc có ID; quan sát/clipboard/quản trị thì không.
Lease tuần tự hoá truy cập vào con trỏ OS dùng chung.

## Rules
- Session **không tự lan** sang tiến trình sau: `session start` chỉ tạo manifest, phải
  tự truyền `AGENT_DESKTOP_SESSION` hoặc `--session <id>`. Thứ tự ưu tiên:
  `--session` > env > không session.
- `--session <id>` trần (không có manifest từ `session start`) chỉ chọn namespace
  snapshot, KHÔNG bật trace — người gọi cũ không bị mọc file lạ.
- Trace **tự che** trường nhạy cảm (`text`, `value`, `name`, `token`, `password`, `url`,
  `title`, … → `{"redacted": true}`). Nhưng `--screenshots` thì KHÔNG che gì — ảnh là ảnh.
- `--trace <path>` ghi đè về một file duy nhất, dùng cho CI/one-off. `--trace-strict` mới
  fail khi ghi trace hỏng; mặc định trace hậu-hành-động là best-effort → **đừng dùng
  "không có dòng trace" làm bằng chứng "không có hành động"**.
- Ref là **snapshot-scoped trong một namespace**; lookup không bao giờ chui sang namespace
  khác. Agent A không dùng được ref của agent B trừ khi cùng session và cùng snapshot.
- Trước khi lấy trace làm biên lai, `status` phải cho thấy `tracing: true` và `session_id`
  đúng cái đang dùng.
