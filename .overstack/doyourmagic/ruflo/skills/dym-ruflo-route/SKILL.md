---
name: dym-ruflo-route
disable-model-invocation: true
description: "Quyết định dùng ruflo hay không, và chọn giữa 4 lớp điều phối agent: ruflo · herdr · orca-dispatch (ta) · Task tool trần. Gọi khi phân vân 'có nên cài claude-flow/ruflo không' hoặc khi cần điều phối nhiều agent."
---

# dym-ruflo-route

## When to use
- Ai đó đề xuất cài ruflo/claude-flow vào dự án dùng overstack.
- Cần điều phối nhiều agent và không chắc dùng tầng nào.

## Steps

1. **Xác định việc thuộc tầng nào** — 4 tầng này KHÔNG thay thế nhau:

| tầng | việc | công cụ |
|---|---|---|
| trong MỘT phiên Claude Code | fan-out subagent, memory chung, hook tự học | **ruflo** (hoặc Task tool trần) |
| nhiều PHIÊN CLI trên một máy | mỗi agent một pane, biết pane nào kẹt/xong | **herdr** |
| giao việc cho CLI bất kỳ qua Orca, biết lúc xong | sentinel shell + poll terminal | **orca-dispatch.py** (của ta) |
| chỉ cần chạy song song rồi gom | không cần gì thêm | `Task` tool / `claude -p` |

2. **Nếu định dùng ruflo, chạy `/dym-ruflo init` TRƯỚC** để biết nó ghi đè gì.

3. **Verdict cho dự án overstack: KHÔNG LẤY nguyên khối.**

| lý do | bằng chứng đo được |
|---|---|
| Chiếm `.claude/` | init ghi **241 file**, **13 hook / 10 loại**, thay `statusLine` · `permissions` · `model` · `env` — đúng những thứ overstack đang sở hữu |
| Không phải runtime độc lập | *"Never use MCP tools alone for execution — Task tool agents do the actual work"* (CLAUDE.md của chính nó) — bỏ Claude Code là không còn gì chạy |
| Chi phí cài | 1.5 GB prefix + ghi `.claude-flow/` và `Library/` vào `$HOME` |
| Bề mặt quá rộng để bảo trì | 2280 file nguồn, 25 gói workspace, 17 nhóm lệnh, `hooks.ts` 211 KB · `doctor.ts` 113 KB |

**Cái đáng học, không đáng nuốt** (mode HÒA TAN, chép Ý không chép code):
- `autopilot` — vòng "chưa xong hết task thì đừng dừng", cắm vào Stop hook. Ta đã có
  Stop hook; đây là một pattern rẻ để thêm.
- `hooks route` / `hooks explain` — định tuyến task→agent bằng pattern đã học, và **giải
  thích được quyết định**. Phần `explain` mới là chỗ hay.
- `swarm compress-message` — nén thông điệp giữa agent về một ngân sách token.

## Rules
- Đừng chạy `ruflo init` trong worktree đang có overstack. Muốn thử thì dựng dự án rỗng
  riêng, xong xoá.
- Đừng đọc "60+ agent, consensus, neural, vector memory" như năng lực đã kiểm chứng —
  lượt đo này chỉ chứng được install · init · doctor · status · help. Phần swarm/neural/
  embeddings/ruvector **chưa kiểm chứng**.
- Cùng một sản phẩm hai tên: npm `ruflo` = `claude-flow`, lỗi vẫn in `claude-flow`.
