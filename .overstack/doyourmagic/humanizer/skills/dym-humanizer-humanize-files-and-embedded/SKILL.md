---
name: dym-humanizer-humanize-files-and-embedded
description: "Chữa file trên đĩa, và nhúng vào việc khác (chế độ file / embedded). khi văn bản đã nằm trong repo (README, docs, bài blog, release note) hoặc khi bạn muốn một task khác gọi Humanizer làm bước cuối trước khi ghi ra PR body / commit message."
disable-model-invocation: true
---

# Skill: dym-humanizer-humanize-files-and-embedded — Chữa file trên đĩa, và nhúng vào việc khác (chế độ file / embedded)

**Vì sao dùng:** khi văn bản đã nằm trong repo (README, docs, bài blog, release note) hoặc khi bạn muốn một task khác gọi Humanizer làm bước cuối trước khi ghi ra PR body / commit message.

**Sinh ra cái gì:** file được ghi đè **chỉ ở phần văn xuôi**, kèm một tóm tắt ngắn trong chat (chế độ file); hoặc chỉ mỗi văn bản cuối, không kèm nháp và phần soi (chế độ embedded).

> Lệnh trong file này gõ trong **khung chat của agent**. Bản thân Humanizer không có CLI để gọi từ shell.

## Chế độ file

Chỉ đường dẫn cho nó:

```text
Humanize phần văn xuôi trong docs/launch-post.md
```

```text
/humanizer

Viết lại README.md phần "Getting started", ghi thẳng vào file.
```

Hành vi theo `SKILL.md` → "How to return the result", mục **File mode**: chạy đủ quy trình viết lại nhưng **chỉ ghi bản cuối vào file**, rồi đưa bạn một tóm tắt ngắn. Bạn không thấy bản nháp và phần soi như ở chế độ dán (workflow `03`).

### Cái nó không được đụng

Nguyên văn: *"Change prose only. Keep code blocks, YAML metadata, data, and link targets unchanged."*

| Được sửa | Giữ nguyên |
|---|---|
| Câu văn, đoạn văn, tiêu đề | Code block |
| Câu dẫn trong bảng | YAML frontmatter |
| Chú thích dạng văn xuôi | Dữ liệu, bảng số |
| | Đích của link (`](...)`) |

### Nên làm trước khi chạy

Vì đây là ghi đè tại chỗ, hãy để git làm mạng lưới an toàn:

```bash
git status --porcelain    # phải sạch trước khi chạy
```

Sau khi chạy:

```bash
git diff -- docs/launch-post.md
```

Soi cụ thể ba thứ trong diff: (1) có claim nào biến mất không, (2) code block có bị đụng không, (3) link target có đổi không. Đây là ba chỗ dễ hỏng nhất và cũng chính là ba ranh giới skill tự đặt ra.

## Chế độ embedded

Khi một task khác dùng Humanizer làm bước cuối — viết PR description, commit message, một đoạn tài liệu — skill trả về **chỉ văn bản cuối**, không nháp, không phần soi.

Cách kích hoạt là nói rõ ngữ cảnh nhúng:

```text
Soạn PR description cho diff này, rồi dùng humanizer làm bước cuối. Chỉ trả về văn bản cuối.
```

Dùng được khi bạn muốn ghép Humanizer vào một quy trình dài mà không muốn output trung gian làm rối.

## Chạy hàng loạt nhiều file

Không có cờ `--batch`. Cứ liệt kê:

```text
Humanize phần văn xuôi trong các file này, mỗi file ghi tại chỗ:
- docs/intro.md
- docs/faq.md
- README.md
```

Mẹo giới hạn phạm vi cho repo lớn — lọc trước bằng shell rồi dán danh sách vào chat:

```bash
git diff --name-only main...HEAD -- '*.md'
```

Chỉ chữa file mình vừa đổi, không quét cả repo.

## Không có gate CI cho phía người dùng

Humanizer không phát hành binary, không có lệnh `check`, không trả exit code nào để CI bám vào. Sản phẩm của nó là một prompt. `.github/workflows/validate.yml` trong repo chỉ kiểm chính gói skill (xem workflow `06`) — **đừng copy file đó vào CI dự án bạn**, nó không kiểm văn bản của bạn.

Muốn có gate văn phong tự động trong CI thì cần một linter văn bản riêng (vale, textlint...). Humanizer là bước con người bấm nút, chạy trong agent.
