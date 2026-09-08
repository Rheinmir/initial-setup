---
name: dym-cti-expert-investigate-in-claude-code
description: "Điều tra bằng lệnh chat (CHỈ trong Claude Code). đây là bề mặt mà cti-expert được thiết kế quanh — agent tự định tuyến theo loại target và tự chạy chuỗi công cụ."
disable-model-invocation: true
---

# Skill: dym-cti-expert-investigate-in-claude-code — Điều tra bằng lệnh chat (CHỈ trong Claude Code)

> **Mọi lệnh trong file này là lệnh CHAT.** Gõ vào terminal sẽ không chạy. Bản terminal ở [04-cli-dispatcher.md](04-cli-dispatcher.md).

**Vì sao dùng:** đây là bề mặt mà cti-expert được thiết kế quanh — agent tự định tuyến theo loại target và tự chạy chuỗi công cụ.
**Sinh ra cái gì:** case trong `intel_engine/cases/<CASE-ID>/`, bảng domain hiển thị trong chat, và file export theo [06](06-reports-and-iocs.md).

---

## Đúng 8 lệnh được đăng ký

`scripts/register.sh` symlink 8 file trong `commands/` vào `~/.claude/commands/`. Đây là 8 lệnh duy nhất chạy được từ prompt nguội ở bất kỳ dự án nào:

| Lệnh | Làm gì | Op T2 tương đương | Tool T1 tương đương |
|---|---|---|---|
| `/cti <target> [--deep\|--quick\|--passive]` | **điểm vào** — định tuyến theo loại target | *(cả chuỗi)* | *(cả chuỗi)* |
| `/cti-recall <seed>` | đã gặp chưa? **luôn chạy đầu tiên** | `recall` | `domain_verdict`, `which_cases` |
| `/cti-case <CASE-ID> <seed> [seed...]` | pipeline tất định đầy đủ | `pipeline open` | *(không có — chỉ CLI)* |
| `/cti-pivot <url\|domain\|ip> [--passive]` | thu thập MỘT target | `pivot-extract` | `pivot_extract` |
| `/cti-cluster <domain\|CASE-ID>` | mở rộng & tương quan | `kb`, `cert-overlap` | `kb_cluster`, `cert_overlap` |
| `/cti-check <indicator>` | kiểm soát dương tính giả | `reference check` | `reference_check`, `reference_add` |
| `/cti-report <CASE-ID> [--graph\|--pdf]` | render graph + PDF/DOCX | `graph`, `report` | `render_diagram`, `render_report` |
| `/cti-status` | tier backend / MCP / credit | `backend.py status` | `api_usage` |

**Mọi `/lệnh` khác bạn thấy trong `SKILL.md` §3 (`/case`, `/sweep`, `/query`, `/username`, `/flow`, `/brief`...) là quy ước đọc từ file đó, không phải lệnh đã đăng ký.** Sau khi skill đã nạp chúng là chỉ dẫn rõ ràng cho agent; gõ ở prompt nguội thì không có gì xảy ra. Khi phân vân: dùng `/cti` và mô tả mục tiêu bằng tiếng Việt/tiếng Anh bình thường.

## Đọc marker trước khi tin một lệnh đã chạy

`SKILL.md` §3 gắn marker cho từng lệnh. Đây là cơ chế chống "agent kể chuyện đã gọi tool":

| Marker | Nghĩa | Được nói gì |
|---|---|---|
| có **T2:** / **T1:** | có op CLI hoặc MCP tool thật đằng sau | gọi, rồi báo cáo kết quả nó trả về |
| **[model]** | không có code, và không cần — nó mô tả *cách làm việc* (kiểu tóm tắt, checklist, đọc lại KB) | cứ làm; **không** được nói là đã chạy tool |
| **[unimplemented]** | tradecraft có tài liệu, chưa có gì thực thi | nói thẳng ra, rồi làm tay theo technique được link |

Lệnh không marker và không có dòng T1/T2 → coi như `[unimplemented]`.

## Vòng đời AEAD

Bốn pha, và thứ tự có lý do:

```
/cti-recall scam-site.example          # 1. Acquire — đã gặp seed này chưa?
/cti-pivot https://scam-site.example   # 2. Acquire — thu thập một target
/cti-check favicon:123456789           # 3. Enrich — chỉ dấu này là link thật hay noise dùng chung?
/cti-cluster scam-site.example         # 4. Enrich — mở rộng sang domain anh em
                                       # 5. Assess — ICD-203, đơn vị phán xét là CLUSTER
/cti-report CASE-0001 --graph --pdf    # 6. Deliver
```

**`/cti-recall` chạy trước là bắt buộc trong tradecraft của repo, không phải gợi ý.** Nếu seed đã thuộc case cũ, thu thập lại vừa tốn credit vừa tạo bản sao lệch trong KB.

**`/cti-check` trước khi cluster cũng vậy.** Một favicon Wix mặc định hay một nameserver Cloudflare sẽ "nối" hàng nghìn domain vô can. Gộp sai thì bạn nêu tên người vô tội; tách sai thì mất case. Xem RULE 5 trong [09](09-contributor-develop-and-gate.md) để hiểu vì sao logic này được bảo vệ bằng test.

## Ba cờ của `/cti`

- `--quick` — recall + một lượt thu thập, không mở rộng cluster.
- `--deep` — fan-out sub-agent song song: bạn (orchestrator) chạy lượt đầu, rồi mỗi identifier phát hiện được giao cho một sub-agent chạy `/cti <seed> --quick`.
- `--passive` — **không chạm target sống**; chỉ làm việc trên bản chụp Wayback/urlscan. `--deep --passive` lan truyền: mọi sub-agent chạy `--quick --passive`.

Dùng `--passive` khi operator không được biết là bị nhìn. Đây là quyết định tradecraft, không phải tối ưu tốc độ.

## Guided flow & template (quy ước, không phải lệnh đăng ký)

Sau khi skill đã nạp:

- `/flow person` · `/flow domain` · `/flow email` · `/flow quick` → `experience/guided-flows/*.md`
- `/template run due-diligence` · `security-audit` · `background-check` → `experience/case-templates/*.md`

## `--yolo`

Nối vào bất kỳ lệnh nào để bỏ mọi prompt xác nhận tương tác; agent tự quyết. **Nó không tắt hook `actionguard.py`** — hook chạy ở tầng harness Claude Code, ngoài tầm của cờ này (xem [07](07-safety-gates.md)).

## Khi có gì đó lạ

```
/cti-status     # tier backend, case store, số MCP tool, số dư credit
/mcp            # server `intel` có kết nối không
/hooks          # 3 mục — chỉ khi cài theo đường plugin
/cost           # chi phí model (KHÔNG gồm credit API bên thứ ba)
```
