---
name: dym-archify-contributor-build-and-test
description: "Nhánh người đóng góp: build, test, và luật của repo. bạn clone chính Archify về để sửa renderer, validator, CLI, hay skill contract — chứ không phải để vẽ sơ đồ."
disable-model-invocation: true
---

# Skill: dym-archify-contributor-build-and-test — Nhánh người đóng góp: build, test, và luật của repo

**Vì sao dùng:** bạn clone chính Archify về để sửa renderer, validator, CLI, hay skill contract — chứ không phải để vẽ sơ đồ.

**Kết quả nhận được:** một vòng lặp test chạy được cục bộ, và hiểu đúng những gì repo này coi là bằng chứng.

> Nhánh này độc lập với `01`–`08`. Nhưng hãy đọc [03-cli-authoring-loop.md](03-cli-authoring-loop.md) trước: hợp đồng CLI (mã thoát + biên lai máy đọc được) là thứ bạn **không được** phá.

## Bố cục repo

```
archify/          # package skill — đơn vị được cài đi (package.json ở đây)
  bin/            # archify.mjs (CLI, ~1990 dòng), preview.mjs, visual-check.mjs, open-artifact.mjs
  renderers/      # architecture/ workflow/ sequence/ dataflow/ lifecycle/ shared/
  schemas/        # 5 schema + common.schema.json + README.md
  scripts/        # check-render-output.mjs, check-update.mjs, generate-*.mjs, render-examples.mjs
  examples/       # nguồn JSON + HTML đã render
  references/     # authoring-contract, delivery-contract, viewer-runtime, brand-marks
  test/           # 93 file *.test.mjs + golden.mjs + fixtures/ + helpers/
  SKILL.md        # hợp đồng cho agent
scripts/          # builder cấp repo: build-gallery, build-guide, build-zip.sh, run-tests.mjs …
docs/             # site tĩnh sinh ra
examples/         # ví dụ cấp repo (dùng cho README/gallery)
.github/workflows/ci.yml
```

Lưu ý tầng thư mục: `package.json` nằm ở `archify/`, **không** ở gốc repo. Mọi lệnh npm chạy từ `archify/`.

## Vòng lặp cục bộ

```bash
cd archify
npm ci
npm test
```

`npm test` (từ `archify/package.json` → mục `scripts.test`) chạy nối tiếp:

```
check:brand-marks       -> node scripts/generate-brand-marks.mjs --check
check:validators        -> node scripts/generate-validators.mjs --check
check:release-identity  -> node ../scripts/check-release-identity.mjs
                        -> node test/golden.mjs
                        -> node ../scripts/run-tests.mjs
```

Bước cuối liệt kê mọi `test/*.test.mjs` (93 file) và chạy chúng bằng `node --test`, thêm `--test-concurrency=2` khi Node ≥ 18.19. Nó trả về đúng mã thoát của test runner.

Trong lúc phát triển, chạy test hẹp nhất trước, rồi mới cả bộ trước khi xin review:

```bash
cd archify
node --test test/cli.test.mjs
node --test test/geometry.test.mjs
```

## Hai check "generate --check" hay bắt lỗi bạn trước

Hai file trong `renderers/shared/` — bộ validator sinh ra (~420 KB) và bộ brand-mark sinh ra (~160 KB) — là **file sinh tự động**. Sửa schema hoặc dữ liệu brand mà quên regenerate thì `npm test` đỏ ngay ở bước đầu:

```bash
cd archify
npm run generate:validators      # sinh lại
npm run generate:brand-marks
npm run check:validators         # chỉ kiểm, không ghi — đây là thứ CI chạy
npm run check:brand-marks
```

## Test trình duyệt thật

Kiểm tra tĩnh trên SVG/XML **không** chứng minh được độ đọc được trên desktop, thứ tự chồng lớp, việc font ổn định, hay tương tác. Khi bạn động vào adaptive reader hoặc bố cục viewer:

```bash
cd archify
ARCHIFY_CHROME="/path/to/chrome" node --test test/desktop-reader-browser.test.mjs
```

Ba bộ test trình duyệt khác mà CI chạy riêng:

```bash
node --test test/i18n.test.mjs               # cả 5 loại sơ đồ localize tương tác viewer
node --test test/semantic-radar.test.mjs     # va chạm + kéo thả của Semantic Radar
npm run test:webm                            # decode một export motion thật, từ chối frame tĩnh
```

**Một test trình duyệt bị bỏ qua vì thiếu Chrome là *skipped*, không phải *passed*.** Báo cáo bằng chứng trình duyệt tự động tách rời với review thị giác cảm quan.

## Ma trận CI

File CI của dự án chạy `npm ci` + `npm test` (working-directory `archify`) trên **Node 18, 20, 22, 24**, cộng các job riêng có Chrome và ffmpeg cho WebM, adaptive reader, i18n, và Semantic Radar. Đừng gửi PR chỉ mới xanh trên bản Node bạn đang cài.

## Bằng chứng theo loại thay đổi

Lấy từ mục "Evidence by change type" của hướng dẫn đóng góp:

**Renderer / layout / validation** — kèm file JSON typed nhỏ nhất, đã che thông tin nhạy cảm, tái hiện được hành vi. Tối thiểu:

1. Chạy test regression tập trung.
2. Chạy ứng viên với các example đã check-in và fixture tương thích đã đóng băng.
3. Chạy `npm test` từ `archify/`.
4. Với thay đổi nhìn thấy được: render HTML cuối rồi chạy `visual-check`.
5. Xem ảnh chụp hoặc HTML sinh ra bằng một bề mặt thị giác thật.

**CLI / biên lai / delivery** — giữ nguyên hành vi mã thoát khác 0 và các biên lai máy đọc được. Một `validate` xanh không chứng minh delivery nguyên tử; một `deliver` xanh không chứng minh chất lượng cảm quan. Test đúng giai đoạn thất bại mà bạn vừa sửa.

**Package / plugin / release** — artifact xuất bản phải tái tạo được từ nội dung repo đã track. Không đóng gói cây làm việc bằng `cp`/`rsync` không giới hạn; dùng đường staging chỉ-lấy-file-đã-track, an toàn với symlink. Thêm test âm chứng minh file untracked và symlink ra ngoài **không** lọt được vào archive. Coi một version đã publish là bất biến — không tái sử dụng tag/version cho nội dung khác.

Test hành vi công khai qua một khe được hỗ trợ khi có thể: `archify render`, `validate`, `deliver`, `visual-check`, hoặc SVG/HTML cuối. Test helper riêng tư hữu ích cho ca biên, nhưng không thay được một regression ở mức CLI hay artifact.

## Artifact sinh ra

Builder cấp repo, chạy **từ gốc repo**:

```bash
node scripts/build-gallery.mjs docs
node scripts/build-guide.mjs docs/guide.html
node scripts/build-start.mjs docs/start.html
node scripts/build-readme-showcase.mjs
scripts/build-zip.sh /tmp/archify-contrib.zip
```

Container zip chuẩn **chỉ build bằng Node 22**. Builder từ chối major khác, để một bản zlib khác không thể xuất bản một biểu diễn byte thứ hai cho cùng nội dung package.

Quy tắc: chỉ regenerate artifact nào có đầu vào thẩm quyền thật sự đổi, và lý tưởng là làm **một lần sau khi** phần cài đặt được chấp nhận. Liệt kê mọi file đã regenerate trong mô tả PR. Đừng regenerate HTML/GIF/ảnh/manifest/archive không liên quan chỉ để nhánh trông "mới".

Đổi runtime skill, schema, renderer, hoặc file skill contract đã publish thì phải kiểm độ tươi của bản zip đóng gói và commit archive build lại khi nội dung package đã track khác đi.

## Báo bug cho có ích

1. Version hoặc commit chính xác, cách cài, lệnh, môi trường.
2. File JSON typed nhỏ nhất, đã che dữ liệu, còn tái hiện được lỗi.
3. Biên lai validation máy đọc được đầy đủ, hoặc lỗi nguyên văn.
4. Kỳ vọng so với thực tế.
5. Ảnh chụp artifact cuối **chỉ khi** lỗi mang tính thị giác.

Không thay bằng chứng tất định bằng ảnh chụp. Với lỗi thị giác, giữ **cả hai**.

## Trước khi xin review

- Rebase/merge `main` mới nhất; giải quyết xung đột artifact sinh ra bằng cách build lại từ nguồn cuối, rồi chạy lại các check bị ảnh hưởng.
- Điền mẫu pull request với lệnh chính xác và **số liệu**; đừng chỉ viết "tests pass".
- Thêm/cập nhật regression test cho thay đổi hành vi.
- Xác nhận các example công khai và fixture tương thích vẫn hành xử như dự định.
- Ghi `visual review: passed | failed | skipped` một cách trung thực cho thay đổi nhìn thấy được.
- Xác nhận **CI remote thật sự đã chạy** trên head hiện tại. Xanh cục bộ không có nghĩa là CI trên GitHub xanh, và **không có check nào cũng không phải là xanh**.
- Gỡ file không liên quan, debug output, đường dẫn cục bộ, nhiễu sinh ra, và dữ liệu nhạy cảm khỏi diff.

Đừng đổi version/tag/định danh phân phối trong một PR tính năng thường, trừ khi issue hoặc maintainer nói rõ phần release nằm trong phạm vi.
