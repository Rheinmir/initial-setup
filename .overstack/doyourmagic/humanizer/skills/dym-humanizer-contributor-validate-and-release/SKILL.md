---
name: dym-humanizer-contributor-validate-and-release
description: "Sửa chính Humanizer: bộ kiểm và luật phát hành (contributor). bạn clone blader/humanizer về để thêm pattern, sửa prompt, hay mở PR. Repo không có build step, không có test runner, không có package.json — chỉ có một validator Python và hai lệnh kiểm bên ngoài."
disable-model-invocation: true
---

# Skill: dym-humanizer-contributor-validate-and-release — Sửa chính Humanizer: bộ kiểm và luật phát hành (contributor)

**Vì sao dùng:** bạn clone `blader/humanizer` về để thêm pattern, sửa prompt, hay mở PR. Repo **không có build step, không có test runner, không có `package.json`** — chỉ có một validator Python và hai lệnh kiểm bên ngoài.

**Sinh ra cái gì:** một cây làm việc qua được đúng ba lệnh mà CI chạy, trước khi bạn push.

## Dựng môi trường

```bash
git clone https://github.com/blader/humanizer.git
cd humanizer
```

Cần: Python 3 (CI dùng `3.12`) và Node 22 cho hai lệnh kiểm còn lại. Không có dependency nào phải cài.

## Ba lệnh kiểm — đúng những gì CI chạy

Lấy từ `.github/workflows/validate.yml`, chạy trên mọi pull request và mọi push vào `main`:

```bash
python3 scripts/validate-package.py
npx --yes skills@1.5.20 add . --list
npm install --global @anthropic-ai/claude-code && claude plugin validate .
```

`AGENTS.md` cũng bắt chạy đúng ba lệnh này trước khi publish.

### Output và exit code thật

Lành:

```
$ python3 scripts/validate-package.py
Humanizer package v2.11.2 is valid
$ echo $?
0
```

Hỏng (đã tái hiện bằng cách đổi `metadata.version` thành `9.9.9` trên một bản copy):

```
$ python3 scripts/validate-package.py
Use one package version in all files: ['2.11.2', '9.9.9']
$ echo $?
1
```

Validator dùng `raise SystemExit("<thông điệp>")`, nên **mọi lỗi đều thoát code `1`** và in đúng một dòng lý do — không có mã lỗi riêng theo loại lỗi. Fail-fast: nó dừng ở lỗi đầu tiên, sửa xong phải chạy lại để thấy lỗi kế.

Hai lệnh còn lại khi lành:

```
$ npx --yes skills@1.5.20 add . --list
◇  Found 1 skill
◇  Available Skills
Humanizer
│    humanizer

$ claude plugin validate .
Validating marketplace manifest: <đường-dẫn>/.claude-plugin/marketplace.json

✔ Validation passed
```

## Validator kiểm chính xác những gì

Đọc `scripts/validate-package.py`, chín cửa theo đúng thứ tự:

| # | Cửa | Vỡ khi |
|---|---|---|
| 1 | `SKILL.md` mở đầu bằng YAML metadata | thiếu khối `---` |
| 2 | Không có field `compatibility:` hoặc `allowed-tools:` | thêm field không được hỗ trợ |
| 3 | Có `metadata.version` trong `SKILL.md` | thiếu, hoặc đặt `version` ở cấp gốc |
| 4 | Ba nơi cùng một version | lệch giữa `SKILL.md`, mục README đầu tiên, `plugin.json` |
| 5 | Đúng một `SKILL.md` thường ở gốc repo | thêm `SKILL.md` thứ hai, hoặc biến nó thành symlink |
| 6 | `plugin.json` → `"skills": ["./"]` | trỏ loader đi chỗ khác |
| 7 | `AGENTS.md` còn đủ 5 câu luật Plain Language | xoá mất một dòng trong mục "Writing style" |
| 8 | Pattern trong `SKILL.md` đánh số liền 1→35, và README liệt kê đủ 1–35 | thêm/bớt/đánh số nhảy cóc, hoặc quên cập nhật bảng README |
| 9 | `SKILL.md` ≤ 500 dòng | prompt phình ra |

Hiện `SKILL.md` dài **456 dòng** — còn 44 dòng dư địa. Thêm một pattern mới tốn cỡ 9–11 dòng, nên trần 500 dòng là ràng buộc thật, không phải hình thức. `AGENTS.md` nói thẳng: *"Prefer a short, clear instruction over another exception or repeated explanation."*

## Thêm hoặc sửa một pattern

Cửa số 8 nghĩa là một pattern chạm **bốn** chỗ, quên chỗ nào là CI đỏ:

1. `SKILL.md` — thêm mục `### NN. <tiêu đề>` với đủ **Words/Phrases to watch**, **Problem**, **Before**, **After**.
2. `README.md` — thêm dòng `| NN | **Tên** | trước | sau |` vào đúng bảng nhóm.
3. `README.md` — sửa số tổng ("The 35 patterns") ở tiêu đề mục.
4. `scripts/validate-package.py` — sửa `range(1, 36)` ở **hai** chỗ (dòng 76 và 82).

Đánh số phải liền mạch: `pattern_numbers != list(range(1, 36))` so sánh **theo danh sách có thứ tự**, nên không được nhảy số và cũng không được đảo thứ tự các mục trong file.

## Đổi version

`AGENTS.md`: version phải khớp ở ba nơi, và **không được** thêm field `version` ở cấp gốc của skill:

```bash
grep -n 'version' SKILL.md | head -3
grep -n '^- \*\*[0-9]' README.md | head -1
grep -n '"version"' .claude-plugin/plugin.json
```

Kèm một ghi chú release ngắn trong README cho mọi thay đổi hành vi hoặc mọi bản vá không hiển nhiên.

## Luật viết bắt buộc

Toàn bộ comment, prompt, tài liệu, mô tả, thông điệp validator và báo cáo tiến độ phải viết bằng **Plain Language** (`AGENTS.md` → "Writing style"): nêu ý chính trước, dùng từ thông dụng và thể chủ động, câu và đoạn ngắn, một khái niệm một tên gọi, dùng `must` cho yêu cầu bắt buộc, giữ nguyên định danh — lệnh — đường dẫn — trường schema — trích dẫn — cụm từ bị theo dõi, và giữ đủ nghĩa kỹ thuật. Năm câu trong số này bị validator kiểm chữ, cửa số 7.

Thêm một luật nữa: **giữ skill portable**. Không viết chỉ dẫn khoá vào một agent cụ thể. Claude Code, OpenCode, Codex chỉ là ví dụ, không phải giới hạn.

## Trước khi mở PR

```bash
python3 scripts/validate-package.py && \
npx --yes skills@1.5.20 add . --list && \
claude plugin validate . && \
echo "READY"
```

Ra `READY` là qua đúng bộ cửa CI sẽ chạy.
