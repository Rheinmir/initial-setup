# 03 — Chạy việc nghiên cứu ở Researcher mode (shell)

**Vì sao dùng:** Đây là đường dùng chính hằng ngày — giao một mục tiêu nghiên cứu cụ thể, để router chọn skill và agent tự chạy + tự kiểm chứng.
**Sinh ra cái gì:** Session file, sản phẩm thật trong thư mục làm việc (script, config, số đo), và output trên stdout theo `--mode`.

> File này **chỉ có lệnh shell**. Lệnh gõ trong TUI nằm ở `08-lenh-chat-trong-tui.md`.

---

## 1. Tương tác

```bash
disco                      # Researcher là mode MẶC ĐỊNH
disco --researcher         # nói rõ ra, cho session mới
```

Ví dụ prompt gõ ở dấu nhắc:

```text
Use the installed skills to benchmark vLLM and SGLang on this machine under the same model, workload, and hardware constraints. Report verified throughput and preserve the commands and measurements needed to reproduce the comparison.
```

## 2. Một phát rồi thoát (`-p` / `--print`)

```bash
disco -p "Fix the failing tests in this repository and run the relevant test suite"

disco --researcher -p "Benchmark vLLM and SGLang with the same model and workload on this machine. Tune each server under identical hardware and memory constraints, report the best verified throughput for each, and preserve the commands and measurements needed to reproduce the comparison."
```

**Exit code của print mode** (đọc từ `modes/print-mode.ts`, không phải từ README):

| Tình huống | Exit |
|---|---|
| Hoàn tất bình thường | `0` |
| Message cuối của assistant có `stopReason` là `error` hoặc `aborted` — lỗi in ra **stderr** | `1` |
| Nhận `SIGHUP` | `129` |
| Nhận `SIGTERM` | `143` |

Nghĩa là: `exit 0` **không** đảm bảo nhiệm vụ nghiên cứu thành công, chỉ đảm bảo phiên agent kết thúc không lỗi. Muốn gác chất lượng thì phải tự kiểm sản phẩm nó tạo ra.

## 3. Gọi thẳng một skill khi đã biết chính xác cần gì

```bash
disco --researcher -p "/skill:vllm determine and verify the highest-throughput vLLM configuration for <model and workload>"
```

Quy ước tên lệnh là `skill:<tên-skill>` (dựng trong `agent-session.ts` / `interactive-mode.ts` / `rpc-mode.ts`). Gọi thẳng thì bỏ qua bước router, tiết kiệm lượt và dễ audit hơn.

Gọi router một cách tường minh (kể cả khi đã `router disable`):

```bash
disco --researcher -p "/skill:repo-skills-router <mô tả task>"
```

## 4. Chạy một graph task-specific do Creator dựng

```bash
disco --researcher -p "/skill:<graph-entry> Complete <research task> within <environment and budget constraints>, and verify it with <evaluator>."
```

Nơi graph được deploy (ghi trong handoff của Creator):
- Gắn với **một** task/project/dataset/evaluator/máy cụ thể, hoặc chưa chắc tái dùng được → `<project-dir>/.agents/skills/`, **chỉ nạp sau khi project được trust**.
- Tự chứa, có provenance, đã verify chéo nhiều project → mới đề xuất `~/.disco/agent/skills/`.
- **Một graph không bao giờ bị xẻ đôi giữa hai scope.**

## 5. Cờ đáng dùng nhất trong ngày

```bash
# Output máy đọc được: mỗi dòng 1 JSON event
disco --mode json -p "..." > events.jsonl

# Chế độ chỉ đọc (không sửa file được)
disco --tools read,grep,find,ls -p "Review the code in src/"

# Chặn một tool cụ thể, giữ nguyên phần còn lại
disco --exclude-tools ask_question -p "..."

# Session
disco --continue "What did we discuss?"     # tiếp session trước (-c)
disco --resume                              # chọn session để tiếp (-r)
disco --name "Refactor auth module"         # đặt tên session (-n)
disco --no-session -p "..."                 # ephemeral, không lưu

# Nạp thêm file vào message đầu
disco @prompt.md "Use this plan while creating the skill"

# Xuất session ra HTML rồi thoát
disco --export session.html

# Mức thinking
disco --thinking high -p "..."     # off|minimal|low|medium|high|xhigh|max
```

`--mode text|json|rpc` chọn **giao thức output**, độc lập hoàn toàn với agent mode (`--creator`/`--researcher`).

## 6. Router hành xử thế nào (để đọc log cho đúng)

Với một request phù hợp, DisCo đọc `repo-skills-router`, mở 1–2 trang area khả dĩ, so các trang family, rồi mới đọc skill được chọn (ví dụ `vllm/SKILL.md`, `sglang/SKILL.md`). Nó **không** nhồi mô tả hay nội dung của 1.000 skill vào context ban đầu. Thấy nó đọc 3–4 file router trước khi làm việc thật là **đúng**, không phải lãng phí.

## 7. Cạm bẫy

- **Cài/cập nhật xong phải mở session mới.** Session đang chạy không thấy skill mới.
- **Đề bài phải là kết quả cụ thể, kiểm chứng được.** "Tìm hiểu vLLM" thì router không có gì để bám; "đo throughput đã verify của vLLM vs SGLang cùng model/workload, giữ lại lệnh để tái lập" thì có.
- **Nhầm mode.** Nếu một request thuộc mode kia, DisCo **dừng trước khi làm** và gợi ý chuyển mode; nó không bao giờ tự đổi mode ngầm.
- **Prompt nhiều message:** `disco "msg1" "msg2"` gửi tuần tự; ở print mode chỉ message cuối của assistant quyết định exit code.

## Bước kế

- Muốn dùng skill trong Claude Code / Codex thay vì trong DisCo → `04-xuat-skill-sang-agent-khac.md`
- Muốn **tạo** skill mới → `05-creator-tao-repo-skill.md`
