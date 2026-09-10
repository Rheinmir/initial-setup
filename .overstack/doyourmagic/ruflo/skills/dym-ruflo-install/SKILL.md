---
name: dym-ruflo-install
disable-model-invocation: true
description: "Cài ruflo (claude-flow) có pin scope và đo dấu chân thật trước khi cho nó chạm máy: 1.5 GB prefix, tự ghi .claude-flow/ và Library/ vào $HOME. Gọi khi định thử ruflo/claude-flow."
---

# dym-ruflo-install

## When to use
- Định thử ruflo/claude-flow trên máy này và muốn thử **trong hộp cát**, không để nó
  vương vãi.
- Cần con số thật để cãi lại "cài phát là xong" trước khi đưa vào dự án.

## Steps

1. **Cài pin scope** — bắt buộc, xem Rules:

```bash
S=./scratchpad/ruflo-probe && mkdir -p $S/{home,prefix}
HOME=$S/home npm install -g --prefix $S/prefix ruflo
RF=$S/prefix/bin/ruflo
```
Đo 2026-09-10: rc=0. **`$S/prefix` = 1.5 GB.** `$S/home` mọc thêm `.npm/`,
**`.claude-flow/`** và **`Library/`** — installer/first-run ghi vào `$HOME`, không chỉ
vào prefix.

2. **Xác minh**:

```bash
$RF --version      # ruflo v3.40.0 · rc=0
$RF doctor         # rc=0
$RF status         # chưa init: "[ERROR] RuFlo is not initialized" · rc=1
```

3. **Xem bề mặt lệnh** trước khi đi tiếp — nó rất rộng:

```bash
$RF --help
```
17 nhóm lệnh: init · start · status · agent · swarm · memory · task · session · mcp ·
hooks · neural · security · policy · performance · embeddings · hive-mind · ruvector ·
guidance · autopilot · config · doctor · daemon · migrate · workflow · analyze · route ·
providers.

4. **Gỡ**: xoá `$S` là hết (prefix + home cô lập đều nằm trong đó).

## Rules
- **Không bao giờ `npm i -g ruflo` trần trong phiên agent.** 1.5 GB vào prefix npm toàn
  cục, cộng thư mục lạ trong `$HOME`.
- **Mã thoát: 0 ok · 1 lỗi** (đo: `--version` 0, `status` chưa-init 1, lệnh sai 1).
  Cẩn thận khi đo qua pipe — `cmd | head` trả rc của `head`, không phải của ruflo; dùng
  `out=$(cmd 2>&1); rc=$?`.
- Bản đo `ruflo@3.40.0` = `claude-flow@3.40.0`, cùng lúc phát hành. Repo 129 MB, 2280 file
  nguồn, workspace 25 gói `v3/@claude-flow/*`.
- Chưa kiểm chứng trong lượt này: `swarm`, `hive-mind`, `neural`, `embeddings`,
  `ruvector` (cần PostgreSQL), `daemon`, MCP server chạy thật.
