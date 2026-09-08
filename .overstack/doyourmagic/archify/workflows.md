# Archify — bộ workflow chạy được

Sinh ra từ một lượt khám phá **read-only** repo `tt-a1i/archify` (commit `06dd052602dd9a369e4d034e24faef0917b5a60c`, package `archify/package.json` v`2.17.0-dev.1`, bin `archify/bin/archify.mjs`). Archify là **một agent skill + một CLI zero-dependency** sinh sơ đồ HTML tự chứa (architecture / workflow / sequence / dataflow / lifecycle) từ JSON IR có schema.

Ba sự thật quan trọng nhất, đã kiểm chứng bằng cách chạy thật chứ không đọc README:

1. Package đặt `"private": true` — **không có trên npm**. `npx archify` không chạy. Mọi lệnh đều là `node <đường-dẫn-skill>/bin/archify.mjs …`.
2. CLI chạy được khi thư mục `node_modules` **không tồn tại**. `render` / `validate` / `deliver` / `compare` / `visual-check` đều xanh trên cây nguồn sạch; `devDependencies` (ajv, parse5, saxes, simple-icons) chỉ phục vụ test và build.
3. Mã thoát **không** theo quy ước 0/1 quen thuộc: `2` là lỗi cách dùng (lệnh lạ, cờ lạ, kiểu sơ đồ lạ, `--repo-root` sai chỗ) **và cũng là** trạng thái "visual-check bị bỏ qua vì không có Chrome". `1` là thất bại thật của validate/render/deliver/check. Người gọi trong CI phải phân nhánh có chủ đích.

Bộ này chia theo **đối tượng dùng**, không theo tính năng:

- **Nhánh người dùng (`01`–`08`)** — bạn cài Archify vào harness/dự án của mình và vẽ sơ đồ.
- **Nhánh người đóng góp (`09`)** — bạn clone chính Archify về để sửa công cụ.

| # | File | Mục đích | Nhánh |
|---|------|----------|-------|
| 1 | [01-install-and-verify.md](01-install-and-verify.md) | Cài Archify vào agent harness (skills CLI / copy tay / ZIP), rồi chứng minh nó chạy bằng `doctor` và `demo` | Người dùng — cài đặt |
| 2 | [02-agent-chat-authoring.md](02-agent-chat-authoring.md) | Prompt gõ **trong khung chat của agent** — chọn loại sơ đồ, mô tả hệ thống, tinh chỉnh từng vòng, dán Mermaid vào | Người dùng — dùng hằng ngày (chat) |
| 3 | [03-cli-authoring-loop.md](03-cli-authoring-loop.md) | Vòng lặp **shell** thật: `guide` → viết JSON → `validate --json` → `deliver --json` → `check`; đọc `diagnostics[]`, hiểu mã thoát | Người dùng — dùng hằng ngày (terminal) |
| 4 | [04-repository-evidence.md](04-repository-evidence.md) | Sơ đồ architecture gắn bằng chứng mã nguồn thật (`sources[]` + `meta.repository` + `--repo-root`), fail-closed | Người dùng — nâng cao |
| 5 | [05-visual-check-and-preview.md](05-visual-check-and-preview.md) | Bằng chứng trình duyệt thật (`visual-check`, biên lai + ảnh chụp) và vòng preview loopback khi đang chỉnh tay | Người dùng — nghiệm thu |
| 6 | [06-compare-architecture-delta.md](06-compare-architecture-delta.md) | So hai bản architecture (base/head) ra HTML delta + biên lai máy đọc được, dùng cho review PR | Người dùng — review |
| 7 | [07-migrate-workflow-v2.md](07-migrate-workflow-v2.md) | Nâng nguồn workflow `schema_version: 1` lên `2`, và xử lý khi migration đòi sửa tay | Người dùng — bảo trì |
| 8 | [08-ci-diagram-gate.md](08-ci-diagram-gate.md) | Chốt cổng CI **của dự án bạn**: mọi JSON sơ đồ phải validate xanh trước khi merge | Người dùng — CI |
| 9 | [09-contributor-build-and-test.md](09-contributor-build-and-test.md) | `npm ci` + `npm test`, 93 file test, test trình duyệt thật, quy tắc regenerate artifact, luật release | Người đóng góp |

## Thứ tự chạy gợi ý

**Người mới:** `01` → chọn một trong hai nhánh dùng — `02` nếu bạn để agent tự soạn JSON, `03` nếu bạn tự viết JSON trong terminal (hai nhánh độc lập, không phụ thuộc nhau) → `05` khi cần nghiệm thu một artifact trước khi giao → `04` khi sơ đồ phải phản ánh mã thật → `06` khi bắt đầu review thay đổi kiến trúc → `08` khi muốn khoá cổng CI → `07` chỉ khi bạn còn nguồn workflow v1 cũ.

**Người đóng góp:** nhảy thẳng `09`; nó không phụ thuộc `01`–`08`. Nhưng đọc `03` trước vì hợp đồng CLI (mã thoát + biên lai) là thứ `09` cấm bạn phá.

## Bộ này được kiểm chứng thế nào, không phải chép lại README

Mọi lệnh trong `01`–`09` đều được đối chiếu với mã nguồn, và phần lớn được **chạy thật** trên macOS + Node v22.17.0 với clone sạch (không `npm install`):

- **Danh sách lệnh con và cờ**: `archify/bin/archify.mjs` — hàm `usage()` (dòng 15–35) và khối `switch (command)` cuối file (dòng ~1934–1990).
- **Mã thoát**: các lời gọi `process.exit(...)` / `process.exitCode = …` có thật trong `archify/bin/archify.mjs` (`fail()` dòng 38–41 mặc định code **2**), `archify/scripts/check-render-output.mjs:276` (`process.exit(ok ? 0 : 1)`), và hằng `EXIT = { pass: 0, fail: 1, skipped: 2 }` tại `archify/bin/visual-check.mjs:24`. Đã xác nhận bằng chạy thật: lệnh lạ → `2`, `--repo-root` trên workflow → `2`, validate JSON hỏng → `1`.
- **Script npm**: `archify/package.json` → `scripts` (không phải mục "Useful repository commands" của README).
- **Zero-dependency**: chạy `validate` khi `ls node_modules` báo *No such file or directory* — vẫn xanh.
- **Hợp đồng schema architecture**: `archify/schemas/architecture.schema.json`. Khoá top-level thật là `connections`, **không phải** `relationships`; `layout.mode` chỉ nhận `"grid"`. Cả hai lỗi này tôi đã tự gặp khi soạn spec thử và sửa theo `supportedFixes` mà CLI trả về.
- **Luồng bằng chứng mã nguồn**: `archify/renderers/shared/repository-evidence.mjs` (hàm `verifyRepositoryEvidence`, dòng 87+) — đã chạy trọn vòng trên chính repo archify, gồm cả hai đường thất bại (`repository-evidence/root-required` → `1`, `--repo-root` sai kiểu → `2`).
- **Sidecar của visual-check**: quan sát trực tiếp file sinh ra sau khi chạy — `<tên>.visual-check.json`, `<tên>.visual-check.html`, và 4 ảnh PNG `1440x900`/`2048x1320` × `light`/`dark`.
- **Hợp đồng chat của agent**: `archify/SKILL.md` (front matter + mục "Fast authoring path", "Delivery"), `archify/references/authoring-contract.md`, `archify/references/delivery-contract.md`.
- **Nhánh người đóng góp**: `CONTRIBUTING.md` mục "Local setup" / "Evidence by change type", `scripts/run-tests.mjs`, và `.github/workflows/ci.yml` (ma trận Node 18/20/22/24).
- **CI của người dùng ở `08` là bản viết mới**, tối thiểu, có chủ đích — **không** sao chép `.github/workflows/ci.yml` của chính Archify (file đó build và test *Archify*, không phải cách bạn tích hợp Archify).

Chưa kiểm chứng được (nêu rõ thay vì đoán): lệnh cài `npx skills add tt-a1i/archify -g` phụ thuộc CLI `skills` bên thứ ba và cần mạng — trong `01` tôi ghi kèm đường cài thủ công đã kiểm chứng được bằng cấu trúc thư mục.
