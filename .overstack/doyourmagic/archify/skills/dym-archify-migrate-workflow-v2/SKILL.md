---
name: dym-archify-migrate-workflow-v2
description: "Nâng nguồn workflow từ `schema_version: 1` lên `2`. bạn còn giữ các file .workflow.json viết theo schema v1 với hình học cố định thủ công, và muốn chuyển sang hợp đồng bố cục dễ đọc của v2 (giải toạ độ tự động, có ràng buộc khoảng hở tối thiểu)."
disable-model-invocation: true
---

# Skill: dym-archify-migrate-workflow-v2 — Nâng nguồn workflow từ `schema_version: 1` lên `2`

**Vì sao dùng:** bạn còn giữ các file `*.workflow.json` viết theo schema v1 với hình học cố định thủ công, và muốn chuyển sang hợp đồng bố cục dễ đọc của v2 (giải toạ độ tự động, có ràng buộc khoảng hở tối thiểu).

**Kết quả nhận được:** một file JSON v2 mới — hoặc một bộ chẩn đoán nói rõ chỗ nào bản v1 không thể thoả ràng buộc v2 và cần bạn sửa tay.

Chỉ áp dụng cho `workflow`. Các loại khác không có đường migrate.

```bash
export A=~/.claude/skills/archify
```

## Chạy

```bash
node $A/bin/archify.mjs migrate workflow old.workflow.json new.workflow.json --to-schema 2 --json
```

Cú pháp nghiêm ngặt, đọc từ `commandMigrate()` trong `bin/archify.mjs`: đúng ba đối số vị trí (`workflow`, nguồn, đích) và bắt buộc `--to-schema 2`. Sai bất cứ điều nào → rc `2` với:

```
Usage: archify migrate workflow <old.json> <new.json> --to-schema 2 [--json]
```

Nguồn và đích **phải là hai file khác nhau** (`migration/source-destination`). Không có ghi đè tại chỗ, có chủ đích.

`migrate` **không** có cờ `--quality`. Nó ghim mọi giai đoạn theo `meta.quality_profile` sẵn có của tài liệu (mặc định `standard`) và chủ động loại bỏ mọi profile lơ lửng trong môi trường.

## Đường xanh — đã kiểm chứng

Chạy trên các fixture v1 đóng gói sẵn:

```bash
node $A/bin/archify.mjs migrate workflow \
  $A/test/fixtures/v1-workflow-explicit-coordinates.workflow.json \
  /tmp/migrated.workflow.json --to-schema 2
```

rc `0`. Ba fixture khác cũng cho rc `0`: `v1-workflow-700x400.workflow.json`, `automatic-routing-node-border-clearance.workflow.json`.

## Đường đỏ — cũng đã kiểm chứng, và bạn sẽ gặp

Không phải nguồn v1 nào cũng chuyển được tự động. Chạy trên `test/fixtures/v1-baseline/agent-tool-call.workflow.json`:

```json
{
  "ok": false,
  "command": "migrate",
  "type": "workflow",
  "source": { "path": "…/v1-baseline/agent-tool-call.workflow.json", "sha256": "4903056b…", "bytes": 5360 },
  "fromSchemaVersion": 1,
  "toSchemaVersion": 2,
  "preExistingDiagnostics": [],
  "migrationDiagnostics": [],
  "newSchemaDiagnostics": [
    {
      "code": "workflow/route-preset-conflict",
      "severity": "error",
      "message": "Workflow edge \"chat->planner\" cannot satisfy route preset \"drop\" under readable-v2 constraints (minimum 8px endpoint stubs, 16px interior turns, and 28px direct clearance)."
    }
  ]
}
```

rc `1`.

### Ba nhóm chẩn đoán, ba việc khác nhau

Biên lai tách ba mảng, đừng lẫn:

| Mảng | Nghĩa | Việc cần làm |
|---|---|---|
| `preExistingDiagnostics` | Nguồn v1 vốn đã sai từ trước | Sửa file **v1** trước, rồi migrate lại |
| `migrationDiagnostics` | Bản thân phép chuyển đổi hỏng (đường dẫn, trùng file, JSON không đọc được) | Sửa dòng lệnh |
| `newSchemaDiagnostics` | Chuyển được, nhưng kết quả không thoả ràng buộc v2 | Sửa hình học/route trong bản v2 bằng tay |

`workflow/route-preset-conflict` ở trên thuộc nhóm ba: preset route `drop` của cạnh đó không sống nổi dưới ràng buộc readable-v2 (stub đầu cuối ≥8px, khúc quẹo trong ≥16px, khoảng hở trực tiếp ≥28px). Cách sửa là đổi preset route hoặc giãn bố cục — không phải cưỡng ép công cụ.

## Sau khi migrate

Luôn validate bản mới trước khi dùng:

```bash
node $A/bin/archify.mjs validate workflow /tmp/migrated.workflow.json --quality showcase --json
```

Chẩn đoán hình học v2 dùng biên lai compiler ổn định:

```bash
node $A/bin/archify.mjs validate workflow /tmp/migrated.workflow.json --layout-json
```

Nội tại của solver **không** phải nút điều khiển để soạn thảo. Chỉ tác động qua các trường đã khai trong nguồn.

## Khi nào **không** nên migrate

Từ `SKILL.md`: giữ `schema_version: 1` khi một nguồn hiện có cần **hình học cố định cũ** — ví dụ sơ đồ đã in vào tài liệu và toạ độ phải khớp từng pixel. Nguồn workflow **mới** thì luôn dùng v2.

Hợp đồng chuẩn về bố cục, pin, migration và biên lai nằm ở `renderers/workflow/README.md`, mục "Layout contracts".
