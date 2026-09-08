---
name: dym-cti-expert-safety-gates
description: "Rào an toàn: cái gì bị CHẶN, cái gì HỎI, cái gì im lặng. để bạn không ngạc nhiên giữa case, và quan trọng hơn — để bạn không tắt nhầm một rào."
disable-model-invocation: true
---

# Skill: dym-cti-expert-safety-gates — Rào an toàn: cái gì bị CHẶN, cái gì HỎI, cái gì im lặng

**Vì sao dùng:** để bạn không ngạc nhiên giữa case, và quan trọng hơn — để bạn không tắt nhầm một rào.
**Sinh ra cái gì:** không sinh gì; nó đổi cách bạn đọc mọi prompt xác nhận mà cti-expert bật lên.

---

## Ba hook, và chúng chỉ tồn tại khi cài theo đường plugin

`hooks/hooks.json` đăng ký đúng ba mục:

| Hook | Bắt sự kiện | Hành vi |
|---|---|---|
| `leakguard.py` | `PreToolUse` · `Write\|Edit\|NotebookEdit` | **deny** — chặn ghi dữ liệu case vào file *tracked* |
| `actionguard.py` | `PreToolUse` · `Bash\|mcp__.*` | **ask** — hỏi trước hành động outbound không thu hồi được |
| `sessionguard.py` | `SessionStart` | báo tier backend + cảnh báo khi số `@tool` đổi |

`bash scripts/register.sh` **không cài được hook**. Chỉ `/plugin install cti-expert` mới có ([01](01-install-and-register.md) bước 3b). Verify bằng `/hooks` trong Claude Code — phải thấy 3 mục.

## `leakguard.py` — RULE 1 tại thời điểm GHI

Repo cấm dữ liệu điều tra lọt vào file tracked: tên người thật, hạ tầng của case, GA4/GTM thật, case ID, PII của operator — kể cả dưới dạng "ví dụ minh hoạ" trong comment hay fixture test.

Có **hai** lớp thi hành, cố ý:

1. `scripts/leakcheck.sh` chạy ở git pre-commit (cài bằng `bash scripts/install-hooks.sh`, phải chạy mỗi lần clone mới vì `.git/hooks/` không được track).
2. `hooks/leakguard.py` chạy ở **thời điểm Write/Edit**.

Lý do có cái thứ hai: hook git chỉ nổ lúc commit và `git commit --no-verify` bỏ qua được, trong khi một agent thì **ghi liên tục và commit hiếm khi**. Ở tầng Write không có cờ `--no-verify` nào cả.

`leakguard.py` **không tự cài lại các mẫu regex** — nó gọi ra `scripts/leakcheck.sh`. Một bản sao thứ hai sẽ trôi lệch, và một guard đã trôi lệch thì luôn báo sạch.

Nó chỉ deny khi **cả hai** đúng: đường dẫn nằm trong một checkout cti-expert, **và** git không ignore đường dẫn đó. Ghi vào `intel_engine/cases/`, `intel_engine/knowledge/`, `.env` — tức các kho đã gitignore — hoàn toàn không bị đụng. Ghi ngoài checkout cũng vậy.

Khi cần ví dụ trong file tracked, dùng placeholder rõ ràng giả: `example.com`, `registrant@example.com`, `G-XXXXXXXXXX`, `CASE-0001`, `1ExampleBitcoinAddressDoNotUse`.

## `actionguard.py` — gate outbound (ask, không phải deny)

Danh sách là **dữ liệu**, không phải code: `hooks/references/outbound_actions.json`. Đọc trực tiếp:

```bash
python3 -c "
import json;d=json.load(open('hooks/references/outbound_actions.json'))
print('MCP :', list(d['mcp_tools']['entries']))
for e in d['bash_patterns']['entries']: print('bash:', e['match'], '| flag:', e.get('flag_required'))"
```

**7 MCP tool bị gate:** `engage_account`, `harvest_authenticated`, `anyrun_submit`, `capture_evidence`, `pivot_extract`, `misp_push`, `misp_publish`.

**11 pattern bash bị gate:**

| Pattern | Vì sao |
|---|---|
| `en_engage.py`, `intel.py engage ` | đăng ký/đăng nhập trên nền tảng của target — outbound, quy được về bạn, không thu hồi |
| `en_harvest.py`, `intel.py engage-harvest` | lái phiên đã đăng nhập bên trong khu vực thành viên của target |
| `bp_anyrun.py submit`, `--submit`, `--confirm-submission` | nộp mẫu lên sandbox công khai |
| `sh_misp.py push` / `publish`, `intel.py misp push` / `publish` | đẩy/công bố event ra ngoài |

Hai tool có `flag_required` — `capture_evidence` và `pivot_extract` chỉ hỏi khi có `--submit`. Đường mặc định của chúng (thu thập thụ động) **không** bị hỏi. Đó là chủ đích: hỏi quá nhiều là cách nhanh nhất để một rào bị tắt hẳn.

Cùng logic ở chi tiết `intel.py engage ` — dấu cách cuối **có tải trọng**: nó giữ cho `intel.py engage-report` (chỉ render write-up cục bộ) không bật prompt.

Không bị gate, cố ý: `detect_login`, `url_paths`, `passive_ssl`, và mọi thu thập thông thường.

## Vì sao gate được nhân đôi

Gate trong code (`submit(confirm=…)`, preflight của Engage) sống trong `intel_engine/` — thư mục **vendored**. Một lần đồng bộ ba chiều có thể revert nó mà **không** làm hỏng test nào (suýt xảy ra ngày 2026-08-23). Hook sống trong cây của chính cti-expert và bắt theo **tên tool**, nên một lần sync không với tới được.

Hệ quả cho người tiêu thụ: nếu bạn thấy một prompt xác nhận mà tool cũng đã tự hỏi — đó không phải bug, đó là hai rào độc lập.

## Cả hai PreToolUse hook đều FAIL-OPEN

Hook chết vì lỗi nội bộ thì **cho qua**, không chặn. Một hook lỗi không được phép làm liệt mọi thao tác ghi trong repo. Backstop là `scripts/audit.sh` và hook git pre-commit.

Kiểm chứng: `tests/test_hooks.py` khẳng định **cả hai chiều** — nổ đúng mục tiêu, im lặng ở ca an toàn kề bên. Chạy thật:

```bash
python3 tests/test_hooks.py
# PASS — Claude Code hooks (58 checks: RULE 1 write-time gate fires on tracked files and stays
# out of the case stores, outbound actions ask, passive work is silent, both hooks fail open,
# and the plugin wiring is machine-independent)
```

`audit.sh` §7 kiểm thêm rằng mọi đường dẫn `hooks.json` khai báo vẫn còn tồn tại — đổi tên một script sẽ vô hiệu hoá hook đó **im lặng**.

## Không bao giờ nộp mẫu của chính case lên sandbox công khai

Nộp một mẫu lên ANY.RUN/VirusTotal công khai là báo cho operator biết họ đang bị điều tra, và không rút lại được. Repo có test riêng cho việc này:

```bash
python3 tests/test_no_sample_submission.py
# PASS — no UNGATED sample-submission path (30 checks: every endpoint either read-only or behind
# the marked-and-enforced confirmation gate, contract stated to the analyst)
```

Trước khi nộp bất kỳ hash nào, chạy `hash-id` (xem [04](04-cli-dispatcher.md)): một chuỗi 32 hex có thể là MD5 của file **hoặc** NTLM của mật khẩu. Nộp nhầm cái sau là làm rò credential.

## Nguyên tắc khi rào làm phiền bạn

Từ `CLAUDE.md` RULE 6, và nó đúng cho cả người dùng lẫn người sửa repo:

> **Đừng nới rào để tắt một prompt.** Ưu tiên siết `flag_required`, hoặc khớp chính xác hơn, thay vì xoá một dòng. Một rào mà bạn phải tắt đi mới làm việc được là một rào sẽ bị tắt hẳn.

`--yolo` của skill bỏ prompt tương tác **của skill**; nó không đụng tới hook ở tầng harness.
