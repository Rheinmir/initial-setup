# 06 — CI tối thiểu cho fork của bạn

**Vì sao dùng:** repo gốc **không có CI** (`ls .github` → không tồn tại). Nếu bạn fork và sửa template, đây là mức tự động hoá nhỏ nhất đáng có.
**Sinh ra cái gì:** một file workflow, chặn merge khi `validate.mjs` fail.

Đây là ví dụ viết mới cho nhu cầu của bạn — không phải bản sao pipeline nội bộ của ai (repo gốc không có gì để chép).

## Mức 1 — chỉ validate (đủ cho 90% thay đổi, chạy vài giây, zero dependency)

`.github/workflows/validate.yml`:

```yaml
name: validate
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - run: node scripts/validate.mjs
```

Không cần `npm install` — `validate.mjs` chỉ dùng `node:fs`, `node:path`, `node:vm`, `node:url`. Exit 1 làm đỏ job, đúng như mong đợi.

## Mức 2 — thêm smoke browser (chỉ bật khi thực sự đụng code render)

Chậm hơn nhiều và cần tải Chromium. Để job riêng để không chặn các PR chỉ sửa chữ.

```yaml
  smoke:
    runs-on: ubuntu-latest
    # chỉ chạy khi template thay đổi
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      # script resolve playwright qua `npm root -g` → BẮT BUỘC cài global
      - run: npm install -g playwright
      - run: npx playwright install --with-deps chromium
      - run: node scripts/smoke-new-charts.mjs
```

`-g` không phải thói quen xấu ở đây — `scripts/smoke-new-charts.mjs` gọi `execFileSync('npm', ['root','-g'])` rồi import từ đường dẫn đó. Cài local là script không tìm thấy module.

## Chạy cùng thứ đó ở local trước khi push

```bash
node scripts/validate.mjs && echo "OK để push"
```

## Chưa gác được cái gì

Cả hai gate đều không chấm được *thẩm mỹ* và *tính trung thực của dữ liệu* — hai thứ chiếm phần lớn giá trị của skill này. Checklist 14 mục ở `SKILL.md` §8 (nhãn chồng nhau, cỡ chữ tối thiểu 6.5/5.5, tiêu đề có phải kết luận không, một trang nhiều hình đã phân bổ template chưa) vẫn phải soi bằng mắt. Đừng để CI xanh làm bạn tưởng đã xong.
