# 03 — Vòng lặp soạn sơ đồ bằng CLI trong terminal

**Vì sao dùng:** khi bạn tự viết JSON IR (hoặc kịch bản hoá việc sinh sơ đồ) và không muốn qua agent. CLI là zero-dependency, chạy được ngay trên cây nguồn sạch.

**Kết quả nhận được:** một file HTML tự chứa đã được kiểm nguyên tử, kèm biên lai JSON có SHA-256 và số byte của cả spec lẫn artifact.

> Mọi lệnh dưới đây gõ **trong terminal**. Prompt cho agent nằm ở [02-agent-chat-authoring.md](02-agent-chat-authoring.md).

Đặt biến cho gọn (đường dẫn tới thư mục skill đã cài ở [01](01-install-and-verify.md)):

```bash
export A=~/.claude/skills/archify
```

## Bước 0 — Chọn loại sơ đồ bằng `guide`

```bash
node $A/bin/archify.mjs guide "Show an API request with Redis cache miss"
```

Đã chạy, kết quả thật:

```
Recommendation: API request chain  [sequence]
Confidence: high
Question answered: Who calls whom, in what order, and what returns?

Use when: API documentation, debugging request latency, auth reviews, or explaining cache fallback.
Avoid when: Order is unimportant and the audience only needs the stable service topology.
Must include: callers and callees; request and return messages; fallback or error path; async side effects
Presentation: classic · trace · views optional

Copy-ready prompt:
Use Archify sequence mode to show this request from caller to final response. …
```

Dạng máy đọc, và bản tiếng Trung:

```bash
node $A/bin/archify.mjs guide "Map Kafka topics, consumer groups, replay, and DLQ" --json
node $A/bin/archify.mjs guide "CI/CD approval gate" --lang zh
```

## Bước 1 — Đọc đúng ba file, không hơn

Với loại `<type>` đã chọn:

```bash
cat $A/schemas/<type>.schema.json
cat $A/schemas/common.schema.json
ls  $A/examples/                       # chọn một ví dụ JSON cùng loại
```

Ví dụ JSON có sẵn (19 mục trong `examples/`, gồm cả HTML đã render):

```
agent-run.lifecycle.json          agent-tool-call.workflow.json
async-job-roundtrip.sequence.json brand-aware-delivery.architecture.json
cache-miss-request.sequence.json  checkout-platform.base.architecture.json
checkout-platform.head.architecture.json  deployment-release.lifecycle.json
event-stream.dataflow.json        incident-response.workflow.json
product-analytics.dataflow.json   production-deployment.architecture.json
release-delivery.workflow.json    web-app.architecture.json
```

Dùng ví dụ để lấy **hình dạng trường**, không lấy nội dung. Nguồn workflow mới dùng `schema_version: 2`; chỉ giữ `1` khi cần bảo toàn hình học cũ.

## Bước 2 — Ba cái bẫy schema architecture tôi tự vấp phải

Đây là ba lỗi tôi gặp thật khi viết một spec architecture từ đầu, và cách CLI trả lời:

**Bẫy 1 — khoá top-level là `connections`, không phải `relationships`.**

```
/ must NOT have additional properties {"additionalProperty":"relationships"}
  supportedFixes: ["remove unsupported property \"relationships\""]
```

Khoá hợp lệ, lấy từ `schemas/architecture.schema.json`: `schema_version`, `diagram_type`, `meta`, `layout`, `components`, `boundaries`, `connections`, `cards`. Bắt buộc: `schema_version`, `diagram_type`, `meta`, `components`.

**Bẫy 2 — không có `layout` nghĩa là đặt tự do, và mọi component phải có `pos`.**

```
Component "cli" must include pos [x, y] when layout.mode is omitted (free placement).
```

`layout.mode` chỉ nhận đúng một giá trị: `"grid"`. Thêm `"layout": { "mode": "grid" }` rồi dùng `row`/`col` là xong.

**Bẫy 3 — nhãn rộng hơn ô sẽ chặn validate.**

```
Label "Architecture renderer" (~139px) is wider than component "renderer" (120px) — shorten the label or widen size.
```

Sửa bằng cách rút nhãn hoặc đặt `size: [w, h]` cho component đó. Ô mặc định rộng 120px.

## Bước 3 — Validate sau **mỗi** lần sửa

```bash
node $A/bin/archify.mjs validate workflow candidate.json --quality showcase --json
```

Chạy thật trên ví dụ đóng gói sẵn, dạng người đọc:

```
ok workflow /…/examples/agent-tool-call.workflow.json (9 artifact checks; composition showcase: 0 errors, 0 warnings)
```

**Ngưỡng nghiệm thu:** đủ **9** artifact check, `0 errors`, `0 warnings`. Biên lai chỉ có 4 check là validate cơ bản, không phải showcase. Nếu `meta.quality_profile` bị thiếu hoặc gõ sai tên, sửa nó **trước** khi động vào hình học.

Khi thất bại, `--json` trả về một object có `diagnostics[]` ổn định. Ví dụ thật (rc `1`):

```json
{
  "schemaVersion": 1,
  "ok": false,
  "command": "validate",
  "stage": "render",
  "type": "workflow",
  "diagnostics": [
    {
      "code": "schema/required",
      "severity": "error",
      "message": "/ must have required property 'schema_version' …",
      "subject": { "diagramType": "workflow", "path": "/" },
      "evidence": { "keyword": "required", "missingProperty": "schema_version" },
      "supportedFixes": ["add required property \"schema_version\""]
    }
  ]
}
```

Quy tắc sửa: chỉ đụng vào `subject` được chẩn đoán, đối chiếu `evidence`, chọn một cách trong `supportedFixes`, chạy lại. Nếu hai vòng liên tiếp không giảm được số lỗi khách quan thì dừng và báo trung thực — đừng đoán mò.

Chẩn đoán hình học workflow v2 dùng biên lai compiler ổn định:

```bash
node $A/bin/archify.mjs validate workflow candidate.json --layout-json
```

Với architecture, `inspect` là bí danh của đúng lệnh đó:

```bash
node $A/bin/archify.mjs inspect architecture candidate.json
```

## Bước 4 — Giao artifact

```bash
node $A/bin/archify.mjs deliver workflow candidate.json out/workflow.html --quality showcase --json
```

Biên lai thật đã chạy:

```json
{
  "schemaVersion": 1,
  "ok": true,
  "command": "deliver",
  "type": "workflow",
  "input": "/…/agent-tool-call.workflow.json",
  "output": "/…/wf.html",
  "specification": { "sha256": "4d3f6c23…", "bytes": 5687 },
  "artifact":      { "sha256": "e083cfe2…", "bytes": 723038 },
  "validation": {
    "checksPassed": 9, "checkCount": 9,
    "compositionProfile": "showcase", "compositionStatus": "pass",
    "errors": 0, "warnings": 0
  }
}
```

`deliver` đóng băng chính xác các byte của spec vào một snapshot riêng cùng thư mục, render và kiểm snapshot đó, rồi **thay thế nguyên tử** file HTML đích. Thất bại thì file cũ được giữ nguyên — nên **đừng** chạy `visual-check` sau một `deliver` hỏng: bạn sẽ đi soi artifact tốt cũ chứ không phải bản vừa hỏng.

Thêm `--open` khi muốn mở ngay file vừa commit:

```bash
node $A/bin/archify.mjs deliver workflow candidate.json out/workflow.html --quality showcase --open --json
```

Trình mở lỗi không làm hỏng thành công: JSON vẫn ra stdout, đường dẫn tuyệt đối dự phòng ra stderr.

## Bước 5 — Kiểm lại một HTML đã có

```bash
node $A/bin/archify.mjs check out/workflow.html
```

In JSON gồm 9 check có tên (`single_svg`, `finite_svg`, `orthogonal_arrows`, `label_route_clearance`, `relationship_crossings`, `relationship_corridors`, `container_border_runs`, `route_rhythm`, `legend_clearance`) cộng khối `composition` với số đo thật (`properCrossings`, `maxBends`, `maxStretch`, `minSegmentPx`, …) và `suggestedLimits`. rc `0` khi xanh, `1` khi hỏng (`scripts/check-render-output.mjs:276`).

## Lệnh phụ hay dùng

```bash
node $A/bin/archify.mjs render workflow candidate.json out/raw.html   # render trần, KHÔNG kiểm — không dùng để nghiệm thu
node $A/bin/archify.mjs brands postgres                                # → "data: postgresql"
node $A/bin/archify.mjs brands "grafana" --json
node $A/bin/archify.mjs brands capture "https://example.com" --json    # ghim digest cho brand chưa có preset
node $A/bin/archify.mjs demo /tmp/archify-demo
```

`brands` chỉ dùng khi node **thật sự** là sản phẩm đó. Đừng suy ra brand từ vai trò mơ hồ như "database", và badge không bao giờ thay được `type`/`label`/quan hệ.

> `node $A/bin/archify.mjs examples` **ghi đè** các file HTML trong `$A/examples/` ngay tại chỗ (nó gọi `scripts/render-examples.mjs` không tham số, xuất về `skillRoot/examples`). Muốn xuất chỗ khác thì gọi thẳng script: `node $A/scripts/render-examples.mjs /tmp/out`.

## Bảng mã thoát

| rc | Nghĩa | Kiểm chứng |
|---|---|---|
| `0` | Thành công | `validate` ví dụ đóng gói, `deliver`, `check`, `compare`, `doctor`, `demo` |
| `1` | Thất bại thật: schema/layout/artifact-check hỏng, doctor "not ready", visual-check fail | `validate` JSON hỏng → `1`; thiếu `--repo-root` khi spec khai bằng chứng → `1` |
| `2` | Dùng sai: lệnh lạ, cờ lạ, kiểu sơ đồ lạ, `--repo-root` trên loại không hỗ trợ. **Và** visual-check bị bỏ qua vì không có Chrome | `bogus` → `2`; `--repo-root` trên workflow → `2`; `EXIT.skipped = 2` tại `bin/visual-check.mjs:24` |

`2` mang hai nghĩa khác nhau tuỳ lệnh. Trong script CI, phân nhánh theo **lệnh** trước rồi mới theo mã, đừng gộp `!= 0` thành một nhánh.
