# 02 — Cài Humanizer làm plugin Claude Code (lệnh chat)

**Vì sao dùng:** đường này không đụng terminal và không đẻ file nào trong repo dự án. Đổi lại nó chỉ chạy trên Claude Code.

**Sinh ra cái gì:** một marketplace tên `humanizer` và một plugin `humanizer` trong cấu hình Claude Code của bạn. Lệnh gọi skill thành `/humanizer:humanizer`.

> **Mọi lệnh dưới đây gõ trong khung chat của Claude Code, không phải trong terminal.** Gõ chúng vào shell sẽ báo `command not found`.

## Yêu cầu

Claude Code `2.1.142` trở lên. Kiểm tra bằng terminal:

```bash
claude --version
```

## Các bước

Trong chat Claude Code:

```text
/plugin marketplace add blader/humanizer
```

```text
/plugin install humanizer@humanizer
```

Cú pháp `humanizer@humanizer` là `<tên plugin>@<tên marketplace>`. Hai tên trùng nhau vì `.claude-plugin/marketplace.json` đặt `name: "humanizer"` và khai đúng một plugin cũng tên `humanizer`, `source: "./"`.

## Kiểm tra đã cài đúng

```text
/plugin
```

Bảng plugin phải hiện `humanizer` phiên bản `2.11.2` (giá trị lấy từ `.claude-plugin/plugin.json` → `version`).

Muốn kiểm chứng manifest trước khi cài, chạy trong **terminal** trên một bản clone:

```bash
claude plugin validate .
```

Output thật khi lành:

```
Validating marketplace manifest: <đường-dẫn>/.claude-plugin/marketplace.json

✔ Validation passed
```

## Gọi skill

```text
/humanizer:humanizer

[dán văn bản vào đây]
```

Cài qua Skills CLI (workflow `01`) thì tên ngắn hơn: `/humanizer`. Cách gọi bằng câu tự nhiên ("humanize đoạn này giúp tôi") hoạt động ở cả hai đường cài, vì Claude khớp theo trường `description` trong metadata của `SKILL.md`.

## Chọn 01 hay 02

Chỉ chọn một. Cài cả hai thì có hai bản prompt giống hệt nhau cùng nạp, agent dễ chọn nhầm bản cũ khi bạn cập nhật một bên. Nếu lỡ cài cả hai, gỡ bên Skills CLI bằng `npx skills remove humanizer --agent claude-code -y`.
