---
name: dym-setup-guardrail-cli
description: "Gọi validator overstack từ SHELL: 3 mode (path/files/claude-hook), 19 luật R1–R19, mã thoát 0/1/2 không đồng nhất, 4 đường fail-open. Gọi khi: 'luật còn cắn không', 'chạy validator', 'test rule', 'exit code validator'."
---

# Skill: dym-setup-guardrail-cli — Gọi guardrail từ terminal: 3 mode, 19 luật, mã thoát

## When to use
- **Tại sao chạy:** tự tay xác nhận luật CÓ cắn, và biết chính xác mã thoát để rẽ nhánh trong script/CI thay vì đoán 0/1.
- **Sinh ra gì:** không sinh file. Chỉ in vi phạm ra **stderr** rồi thoát với mã tương ứng.
- Gọi qua hub: `/dym-setup guardrail-cli` — hoặc trực tiếp `/dym-setup-guardrail-cli` nếu đã symlink riêng.

## Steps
### 1. Một binary, ba mode

```
python3 .harness/poc-vendor-neutral/bin/llmwiki-validate.py [--policy P] {path <FILE> | files <F...> | claude-hook}
```

| Mode | Đọc gì | Áp luật tầng | Mã thoát khi VI PHẠM |
|---|---|---|---|
| `path <FILE>` | 1 đường dẫn | `repo` | **2** |
| `files <F...>` | nhiều đường dẫn | `repo` | **1** |
| `claude-hook` | JSON hook Claude từ **stdin** | `session` | **2** |

`--policy P` trỏ policy khác; mặc định là `policy.yaml` cạnh binary.

**Cùng một vi phạm, hai mã thoát khác nhau** — đây không phải lỗi đánh máy, nó nằm ngay trong mã (`block_code = 2` cho `path`/`claude-hook`, `= 1` cho `files`). Script nào rẽ nhánh theo mã thoát phải biết mình đang gọi mode nào.

Đo thật trên file thiếu `## Origin` + thiếu frontmatter:

```bash
$ python3 $V files .llmwiki/wiki/concepts/bad.md
[R2 origin-required] .llmwiki/wiki/concepts/bad.md thiếu '## Origin' — …
[R9 okf-frontmatter] .llmwiki/wiki/concepts/bad.md thiếu YAML frontmatter (--- … ---) — …
rc=1

$ python3 $V path .llmwiki/wiki/concepts/bad.md
[R2 origin-required] …
[R9 okf-frontmatter] …
rc=2
```

### 2. ⚠️ Bốn đường fail-open — đều thoát 0

| Tình huống | Mã thoát | Hệ quả |
|---|---|---|
| Mode lạ (`bogus`) | **0** + `mode lạ 'bogus' — fail-open` ra stderr | gõ sai mode → CI xanh giả |
| Không tham số | **0** + dòng usage | như trên |
| **File không tồn tại** | **0**, im lặng hoàn toàn | target sai đường dẫn → CI xanh giả |
| Không đọc được `policy.yaml` | **0** + `không đọc được policy … — fail-open` | thiếu `pyyaml` → mọi luật tắt, không ai biết |

Trong CI, luôn kiểm tra file tồn tại **trước** khi giao cho validator — xem [04](../dym-setup-ci/SKILL.md).

### 3. Bộ 19 luật (đếm từ `policy.yaml`, không đếm từ README)

`enforce_at: session` = chặn lúc agent định ghi (hook). `repo` = chặn lúc commit/PR (pre-commit + CI).

| ID | Tên | Chặn gì | Tầng |
|---|---|---|---|
| R1 | no-write-raw | agent ghi vào `raw/` — inbox của con người, chỉ đọc | session |
| R2 | origin-required | wiki content thiếu `## Origin` | session + repo |
| R3 | index-sync | `wiki/index.md` lệch tập file thật | session + repo |
| R4 | audit-log | ghi `.claude/audit/audit.jsonl` (không chặn) | session |
| R5 | folder-structure | file `.md` nằm trần ở `wiki/` root | session + repo |
| R6 | verify-before-commit | commit chưa qua validator + lint + drift-test | repo |
| R7 | proposal-complete | SPEC thiếu `## Agent Task Assignment` / Sequence diagram / `## Global constraints` | session + repo |
| R8 | session-health | báo số rule đang gác + drift policy đầu phiên (không chặn) | session |
| R9 | okf-frontmatter | wiki content thiếu YAML frontmatter + `type:` | session + repo |
| R10 | docs-gate | nhắc bổ sung docs mỗi N prompt (không chặn) | session |
| R11 | seq-html-glass-style | `*-seq.html` không theo style liquid-glass | session + repo |
| R12 | pull-before-change | chưa `pull-gate` trước khi fan-out / trước push | session + repo |
| R13 | decision-to-adr | quyết định `architecture` trong `decisions.md` không ref ADR | repo |
| R14 | patterns-protected | agent tự sửa `llmwiki/patterns/` (unlock: `LLMWIKI_PATTERNS_UNLOCK=1`) | session |
| R15 | no-ai-attribution | commit message ghi công cho AI (`Co-Authored-By: Claude…`, 🤖) | repo |
| R16 | report-show-path | HTML report dưới `llmwiki/html/` không nhúng đường dẫn tuyệt đối của chính nó | session |
| R17 | problem-tree-flush | SessionEnd chạm bề mặt framework mà problem-tree chưa cập nhật (không chặn) | session |
| R18 | plan-executable | `*-PLAN.md` thiếu Files/Interfaces/code từng bước | session + repo |
| R19 | evidence-terminal | khối ```evidence-chain có đường đi không kết thúc ở nút chứng cứ | session + repo |

### 4. Thử luật cắn — bốn lệnh đủ

```bash
V=.harness/poc-vendor-neutral/bin/llmwiki-validate.py

# R1 — agent ghi vào raw/ (mode hook)
echo '{"tool_name":"Write","tool_input":{"file_path":"llmwiki/raw/x.md","content":"x"}}' \
  | python3 $V claude-hook; echo "rc=$?"      # 2 + [R1 no-write-raw]

# R1 qua Bash redirect
echo '{"tool_name":"Bash","tool_input":{"command":"echo hi > .llmwiki/raw/a.md"}}' \
  | python3 $V claude-hook; echo "rc=$?"      # 2

# R2 + R9 — wiki page thiếu Origin/frontmatter (mode repo)
printf '# Thiếu\n\nnội dung\n' > .llmwiki/wiki/concepts/bad.md
python3 $V files .llmwiki/wiki/concepts/bad.md; echo "rc=$?"   # 1

# R5 — file .md nằm trần ở wiki/ root
printf -- '---\ntype: x\n---\n## Origin\nz\n' > .llmwiki/wiki/loose.md
python3 $V files .llmwiki/wiki/loose.md; echo "rc=$?"           # 1 + [R5 folder-structure]
```

Trang wiki **hợp lệ** tối thiểu (qua cả R2, R5, R9):

```markdown
---
type: concept
---

# Tên khái niệm

## Origin
Nguồn: cuộc họp 06/09/2026 · file raw/notes.md
```

### 5. Ba luật CHẾT dưới layout dot — ĐÃ SỬA Ở UPSTREAM (PR #114)

> **Audit sau merge (PR #115):** #114 mới vá glob R14 ở lõi vendor-neutral (hook per-project). Validator production `patterns_guard.py` mà hook **global** gọi vẫn hardcode `llmwiki/patterns` ở nhánh write — đo rc=0 dưới `.llmwiki/patterns/`. Đã vá ở PR #115.

> **Đã sửa ở upstream.** Ba lỗi dưới đây được vá trong PR #114, merge vào `orca` ngày 2026-09-06 (commit `d8f1967`, đóng #111 · #112 · #113). Phần mô tả giữ nguyên vì nó vẫn đúng cho **bản cài cũ** trên máy bạn — bản cài chỉ hết lỗi sau khi bạn chạy lại installer. Cài từ `orca` từ nay: bỏ qua bản vá tay.


`01` sửa **đường dây** (hook trỏ sai file). Đây là chuyện khác: ba luật hardcode segment `llmwiki` **trong chính glob của luật**, nên khi dự án dùng `.llmwiki/` thì glob không khớp và luật im lặng không bao giờ cắn:

| Luật | Glob trong `policy.yaml` | `.llmwiki/…` |
|---|---|---|
| R14 patterns-protected | `**/llmwiki/patterns/**`, `llmwiki/patterns/**` | TRƯỢT |
| R16 report-show-path | `**/llmwiki/html/*.html` | TRƯỢT |
| R19 evidence-terminal | `**/llmwiki/wiki/**/*.md` | TRƯỢT |

**R11 KHÔNG nằm trong nhóm này** dù glob đầu của nó cũng chứa `llmwiki`: nó có glob thứ hai `**/html/*-seq.html` không kèm tên thư mục gốc, nên vẫn khớp bình thường.

Các luật còn lại dùng glob **không** kèm tên thư mục gốc (`**/raw/**`, `**/wiki/concepts/**/*.md`) nên vẫn khớp bình thường. Đo thật:

```
TRƯỢT  **/llmwiki/patterns/**       vs .llmwiki/patterns/p.md
KHỚP   **/llmwiki/patterns/**       vs  llmwiki/patterns/p.md
TRƯỢT  **/llmwiki/wiki/**/*.md      vs .llmwiki/wiki/concepts/a.md
KHỚP   **/raw/**                    vs .llmwiki/raw/a.md
KHỚP   **/wiki/concepts/**/*.md     vs .llmwiki/wiki/concepts/a.md
```

Cách vá tại chỗ — thêm biến thể dot vào `policy.yaml` của dự án rồi sinh lại adapter:

```bash
python3 - <<'PY'
import re, pathlib
p = pathlib.Path(".harness/poc-vendor-neutral/policy.yaml")
s = p.read_text(encoding="utf-8")
# thêm dòng glob song song cho mọi glob chứa 'llmwiki/'
out = []
for line in s.splitlines(True):
    out.append(line)
    m = re.match(r'^(\s*- )"?([^"\n]*llmwiki/[^"\n]*)"?\s*$', line)
    if m and ".llmwiki/" not in m.group(2):
        out.append(f'{m.group(1)}"{m.group(2).replace("llmwiki/", ".llmwiki/")}"\n')
p.write_text("".join(out), encoding="utf-8")
print("đã thêm biến thể .llmwiki/ vào policy")
PY
python3 .harness/poc-vendor-neutral/gen-converters.py   # sinh lại adapter từ policy
```

Nghiệm thu:

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":".llmwiki/patterns/p.md","content":"x"}}' \
  | python3 $V claude-hook; echo "rc=$?"     # trước vá: 0 · sau vá: 2 [R14]
```

### 6. Lỗ trong `check_deny_write_bash` — ĐÃ SỬA Ở UPSTREAM (PR #114)

> **Đã sửa ở upstream.** Ba lỗi dưới đây được vá trong PR #114, merge vào `orca` ngày 2026-09-06 (commit `d8f1967`, đóng #111 · #112 · #113). Phần mô tả giữ nguyên vì nó vẫn đúng cho **bản cài cũ** trên máy bạn — bản cài chỉ hết lỗi sau khi bạn chạy lại installer. Cài từ `orca` từ nay: bỏ qua bản vá tay.


Nhánh xử lý tool `Bash` **không đọc glob của luật**. Nó chỉ kiểm tra chuỗi con `"raw/"` có trong câu lệnh không:

```python
def check_deny_write_bash(command, rule):
    cmd = command or ""
    if "raw/" in cmd and (BASH_WRITE.search(cmd) or BASH_COPY.search(cmd)):
        return f"[{_tag(rule)}] chặn bash ghi raw/: {cmd[:100]}"
    return None
```

Hai hệ quả đo được:

- **Dương tính giả:** một lệnh bash ghi vào `raw/` bị báo **hai lần** — một dòng `[R1 no-write-raw]` và một dòng `[R14 patterns-protected]` với cùng nội dung "chặn bash ghi raw/". R14 không liên quan gì tới `raw/`.
- **Âm tính giả:** `echo x > llmwiki/patterns/p.md` qua tool `Bash` → **rc=0**, không chặn, dù đó đúng là đích R14 muốn gác. Nói cách khác **R14 chỉ gác đường `Write/Edit`, không gác đường `Bash`** — kể cả với layout không dấu chấm.

Đừng dựa vào R14 để khoá `patterns/` trước một agent có quyền `Bash`. Muốn khoá thật: đặt quyền ở `permissions.deny` của Claude, hoặc để file ngoài repo.

### 7. Self-test lõi

```bash
bash .harness/poc-vendor-neutral/demo.sh          # 13 assertion
bash .harness/poc-vendor-neutral/test-broad.sh    # 80 assertion
```

Cả hai in `OK`/`FAIL` từng dòng và thoát 0 khi xanh. Số thật đo được là **80** (`demo.sh` 13). Nhãn `(68)` trong log cài và `broad 54 = 67 assertion` ở tên job CI là chuỗi cứng đã trôi — PR #114 sửa cả hai thành `13 + 80 = 93`.

## Rules
- > **Audit sau merge (PR #115):** #114 mới vá glob R14 ở lõi vendor-neutral (hook per-project). Validator production `patterns_guard.py` mà hook **global** gọi vẫn hardcode `llmwiki/patterns` ở nhánh write — đo rc=0 dưới `.llmwiki/patterns/`. Đã vá ở PR #115.
- > **Đã sửa ở upstream.** Ba lỗi dưới đây được vá trong PR #114, merge vào `orca` ngày 2026-09-06 (commit `d8f1967`, đóng #111 · #112 · #113). Phần mô tả giữ nguyên vì nó vẫn đúng cho **bản cài cũ** trên máy bạn — bản cài chỉ hết lỗi sau khi bạn chạy lại installer. Cài từ `orca` từ nay: bỏ qua bản vá tay.
- > **Đã sửa ở upstream.** Ba lỗi dưới đây được vá trong PR #114, merge vào `orca` ngày 2026-09-06 (commit `d8f1967`, đóng #111 · #112 · #113). Phần mô tả giữ nguyên vì nó vẫn đúng cho **bản cài cũ** trên máy bạn — bản cài chỉ hết lỗi sau khi bạn chạy lại installer. Cài từ `orca` từ nay: bỏ qua bản vá tay.
