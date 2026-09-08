---
name: dym-archify-compare-architecture-delta
description: "So sánh hai bản architecture (Architecture Delta). review thiết kế và review PR. Thay vì bắt người đọc so hai sơ đồ bằng mắt, Archify so hai nguồn architecture đã validate và sinh một trang Before / Delta / After kèm biên lai máy đọc được."
disable-model-invocation: true
---

# Skill: dym-archify-compare-architecture-delta — So sánh hai bản architecture (Architecture Delta)

**Vì sao dùng:** review thiết kế và review PR. Thay vì bắt người đọc so hai sơ đồ bằng mắt, Archify so hai **nguồn architecture đã validate** và sinh một trang Before / Delta / After kèm biên lai máy đọc được.

**Kết quả nhận được:** một file HTML delta tự chứa và một sidecar `*.receipt.json` liệt kê chính xác cái gì thêm, bớt, đổi, dời — không suy diễn.

Chỉ hỗ trợ `architecture`.

```bash
export A=~/.claude/skills/archify
```

## Chạy

```bash
node $A/bin/archify.mjs compare architecture base.json head.json out/delta.html --json
```

Đã chạy thật với hai ví dụ đóng gói sẵn:

```bash
node $A/bin/archify.mjs compare architecture \
  $A/examples/checkout-platform.base.architecture.json \
  $A/examples/checkout-platform.head.architecture.json \
  out/delta.html --json
```

rc `0`. Sinh ra hai file:

```
delta.html          1.9M
delta.receipt.json  5.2K
```

Sidecar biên lai mặc định đặt cạnh HTML, cùng tên gốc. Đổi chỗ bằng `--receipt`:

```bash
node $A/bin/archify.mjs compare architecture base.json head.json out/delta.html \
  --receipt out/delta-receipt.json --json
```

Các cờ khác giống phần còn lại của CLI: `--quality standard|showcase`, và `--repo-root <path>` khi hai nguồn có khai bằng chứng mã (xem [04](04-repository-evidence.md)).

## Đọc biên lai

Các khoá top-level thật (quan sát trực tiếp trên `delta.receipt.json` đã sinh):

```
schemaVersion  ok  command  type  comparatorVersion  canonicalVersion
completeness   proofLevel   base   head   summary   changes
identity       view         limitations   artifact   validation
```

`base` và `head` mỗi bên mang `title`, `rawSha256`, `semanticSha256`, `bytes`. Hai loại hash tách biệt có chủ đích: `rawSha256` đổi khi byte đổi (kể cả chỉ format lại), `semanticSha256` chỉ đổi khi ý nghĩa đổi.

`summary` thật từ lần chạy trên:

```json
{
  "components":  { "added": 1, "changed": 1, "evidenceChanged": 0, "removed": 1, "moved": 1 },
  "connections": { "added": 1, "changed": 2, "removed": 1, "rerouted": 1 },
  "boundaries":  { "added": 0, "changed": 2, "removed": 0, "geometryChanged": 0 },
  "presentationChanged": true,
  "provenanceChanged": false
}
```

`identity` nói rõ cái gì được coi là "cùng một thứ" giữa hai bản:

```json
{
  "components":  "components[].id",
  "connections": "connections[].id (required)",
  "boundaries":  "boundaries[].kind + boundaries[].label (derived)"
}
```

**Hệ quả thực dụng:** nếu bạn đổi `id` của một component, delta sẽ đọc thành *xoá một cái, thêm một cái*, không phải *đổi tên*. Giữ `id` ổn định qua các bản chỉnh sửa nếu muốn delta có nghĩa. Và **`connections[].id` là bắt buộc** để so cạnh — nguồn không đặt id cho cạnh thì không so cạnh được tử tế.

## Giới hạn — trích nguyên văn từ biên lai

```
"Authored Architecture IR only; no runtime impact, causality, risk, or mergeability is inferred."
"Boundary identity is conservatively derived from kind + label."
```

`completeness: "complete"`, `proofLevel: "authored"`. Nói cách khác: đây là delta trên **sự kiện bạn đã khai**, không phải phân tích tác động. Trang này không được dùng để tuyên bố "thay đổi này an toàn để merge" hay "rủi ro thấp". Nó nói *cái gì đã đổi trong bản khai*, chấm hết.

## Gắn vào review PR

Chạy giữa `main` và nhánh, khi nguồn architecture nằm trong repo:

```bash
git show main:docs/architecture.json > /tmp/base.json
node $A/bin/archify.mjs compare architecture \
  /tmp/base.json docs/architecture.json \
  /tmp/delta.html --json > /tmp/delta-summary.json
```

Rồi đính `/tmp/delta.html` vào PR, hoặc trích `summary` từ `/tmp/delta-summary.json` vào phần mô tả. Xem [08-ci-diagram-gate.md](08-ci-diagram-gate.md) cho phần chốt cổng.

Trong viewer, người đọc chọn một thay đổi đã khai, hoặc chạy một lượt Review hữu hạn chỉ để xem. Viewer không suy ra tác động, rủi ro, hay độ an toàn khi merge.
