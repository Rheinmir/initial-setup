# 04 — Sơ đồ architecture gắn bằng chứng mã nguồn thật

**Vì sao dùng:** khi sơ đồ kiến trúc phải chứng minh được nó phản ánh mã thật, không phải trí nhớ của ai đó. Node có bằng chứng tự đánh dấu `SRC n` trong viewer và mở đúng file + khoảng dòng, ghim vào một commit công khai.

**Kết quả nhận được:** một HTML architecture trong đó các thành phần dẫn ngược về file/dòng thật, và một cổng fail-closed từ chối render nếu bằng chứng không kiểm chứng được.

**Chỉ dành cho `architecture`.** `workflow`, `sequence`, `dataflow`, `lifecycle` từ chối `--repo-root` với rc `2`.

```bash
export A=~/.claude/skills/archify
```

## Ba thứ phải khớp cùng lúc

Đọc từ `renderers/shared/repository-evidence.mjs` (hàm `verifyRepositoryEvidence`, dòng 87+):

1. **`meta.repository.url`** — phải là URL GitHub công khai dạng `https://github.com/owner/repo`. URL khác host hoặc khác dạng → `repository-evidence/url-invalid`.
2. **`meta.repository.revision`** — phải là **SHA commit đủ 40 ký tự**. Rút gọn 7 ký tự bị từ chối: `repository-evidence/revision-invalid`.
3. **`--repo-root <path>`** — phải trỏ vào **thư mục top-level của Git checkout**, và `origin` của nó phải khớp `meta.repository.url`. Không phải top-level → `repository-evidence/root-not-top-level` (kèm đúng đường dẫn nên dùng). Origin lệch → `repository-evidence/origin-mismatch`.

Cấu trúc `sources[]` trên mỗi component, lấy từ `schemas/architecture.schema.json`: mảng 1–3 phần tử, mỗi phần tử bắt buộc `path` (≤240 ký tự), tuỳ chọn `line`, `end_line` (số nguyên ≥1), `label` (≤48 ký tự).

## Spec tối thiểu đã chạy xanh thật

Ví dụ này tôi đã soạn và chạy trọn vòng trên chính repo archify:

```bash
REV=$(git -C /path/to/archify rev-parse HEAD)   # phải là SHA 40 ký tự

cat > evidence.architecture.json <<JSON
{
  "schema_version": 1,
  "diagram_type": "architecture",
  "meta": {
    "title": "Archify CLI — evidence probe",
    "quality_profile": "showcase",
    "repository": {
      "url": "https://github.com/tt-a1i/archify",
      "revision": "$REV"
    }
  },
  "layout": { "mode": "grid" },
  "components": [
    {
      "id": "cli", "type": "backend", "label": "archify CLI", "row": 0, "col": 0,
      "sources": [
        { "path": "archify/bin/archify.mjs", "line": 1, "end_line": 40, "label": "entry" }
      ]
    },
    {
      "id": "renderer", "type": "backend", "label": "Renderer", "row": 0, "col": 1,
      "sources": [
        { "path": "archify/renderers/architecture/render-architecture.mjs", "line": 1, "end_line": 30 }
      ]
    }
  ],
  "connections": [
    { "from": "cli", "to": "renderer", "label": "spawns" }
  ]
}
JSON

node $A/bin/archify.mjs validate architecture evidence.architecture.json \
  --quality showcase --repo-root /path/to/archify
```

Kết quả thật:

```
ok architecture /…/evidence.architecture.json (9 artifact checks; composition showcase: 0 errors, 0 warnings)
```

rc `0`.

## Hai đường thất bại, đã kiểm chứng

**Quên `--repo-root` khi spec có khai bằng chứng** — cổng fail-closed, rc **`1`**:

```
This diagram declares source evidence. Pass --repo-root <repository> so Archify can verify it before rendering.
[repository-evidence/root-required] … Fix: pass --repo-root with the matching local Git checkout.
```

**Dùng `--repo-root` với loại khác architecture** — lỗi cách dùng, rc **`2`**:

```
--repo-root is currently supported for architecture diagrams only.
```

Khác biệt này quan trọng trong CI: `1` nghĩa là spec của bạn sai, `2` nghĩa là dòng lệnh của bạn sai.

## Giao artifact có bằng chứng

`--repo-root` được chấp nhận bởi `render`, `validate`, `deliver`, `preview`, và `compare` — luôn chỉ ở chế độ architecture:

```bash
node $A/bin/archify.mjs deliver architecture evidence.architecture.json out/arch.html \
  --quality showcase --repo-root /path/to/archify --json
```

## Kỷ luật khi thu thập bằng chứng

Từ `references/authoring-contract.md` mục "Repository evidence":

- Soi **entrypoint, biên runtime, kho dữ liệu, transport, cấu hình triển khai** trước khi viết sơ đồ.
- **Chỉ ghi bằng chứng bạn thật sự đã kiểm.** `sources[]` là một tuyên bố, không phải chú thích.
- **Không suy ra quan hệ nhân quả lúc chạy từ việc file nằm gần nhau hay tên giống nhau.** Cùng thư mục không có nghĩa là gọi nhau.
- Artifact thường (không khai `sources`) vẫn hoàn toàn không dính mã nguồn — bằng chứng là opt-in, không phải mặc định.

## Liên quan: profile `deployment-ownership`

Architecture có thêm một engineering profile tuỳ chọn cho review triển khai sản xuất. Nó **fail closed**: thiếu owner đã khai, thiếu vị trí region, thiếu phạm vi database riêng, hoặc thiếu tên các điểm cắt biên thì validate hỏng. Nó không bao giờ bật ngầm và **không** soi hạ tầng đang chạy.

Chỉ bật khi người dùng yêu cầu đúng thứ đó. Từ ngữ về region/cluster/biên bảo mật trong sơ đồ **không** tự nó là lý do bật profile. Và một khi đã bật thì không được gỡ ra chỉ để validate xanh — sửa dữ liệu, hoặc báo cáo chẩn đoán một cách trung thực.
