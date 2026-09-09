# doyourmagic — browser-use

Chạy 09/09/2026 trên `git@github.com:browser-use/browser-use.git` (v0.13.10, commit `2b1f9d3`)
và repo em `github.com/browser-use/browser-harness` (v0.1.13).
Chế độ đặt tên: **mặc định** (`dym-browser-use` + `dym-browser-use-<slug>`).

## Phát hiện lật ngược giả định

Câu hỏi mở đầu là "học cách họ dùng Playwright". **Họ không dùng Playwright.**
browser-use v0.13 đã bỏ hẳn Playwright, chuyển sang nói CDP trực tiếp qua `cdp-use`.
Mọi chữ "playwright" còn lại trong mã nguồn chỉ là comment và link tài liệu.

Thứ đáng học không nằm ở "mẹo Playwright" mà ở **hình dạng của công cụ**: họ tách hẳn
tầng lái trình duyệt (`browser-harness`, 4 dependency) khỏi tầng agent (`browser-use`,
50+ dependency gồm openai/anthropic/google-genai). Tầng lái trình duyệt là một **daemon
có trạng thái** — mỗi lượt gọi CLI là một hành động nhỏ, tab và cookie giữ nguyên giữa
các lượt. Đó là khác biệt bản chất với cách framework này đang làm: một script `.mjs`
viết mù toàn bộ kịch bản, chạy một phát, mất sạch state.

## Bảng skill

| skill | mục đích | nhánh | lệnh gọi |
|---|---|---|---|
| `dym-browser-use` | hub, in bảng slug rồi nạp đúng một file con | — | `/dym-browser-use` |
| `dym-browser-use-repl` | lái trình duyệt kiểu REPL có trạng thái; `file://` + `localhost` | tiêu thụ | `/dym-browser-use repl` |
| `dym-browser-use-qa` | chấm 1–5 một site/app kèm bằng chứng | tiêu thụ | `/dym-browser-use qa` |
| `dym-browser-use-cloud` | cloud browser + tunnel localhost, chạy song song | tiêu thụ | `/dym-browser-use cloud` |

## Thứ tự chạy đề xuất

`repl` là nền — hai skill kia đứng trên nó. Việc một-phát-ăn-ngay (chụp một ảnh, đọc console
một lần) vẫn thuộc về `/playwright-verify` sẵn có; `repl` chỉ vào cuộc khi việc cần nhiều bước
có điều kiện. `cloud` chỉ khi cần môi trường sạch hoặc chạy song song, vì nó tốn tiền.

## Không lấy — và vì sao

**Gói `browser-use` (agent tự lái).** Nó là một agent LLM tự quyết định bấm gì, kéo theo
openai + anthropic + google-genai + groq + ollama + mcp + posthog. Framework này đã có agent —
là chính Claude Code. Nhét thêm một vòng agent bên trong chỉ để bấm nút là trả tiền hai lần
cho cùng một việc suy luận, và mất luôn khả năng nhìn thấy agent đang làm gì.

**Workflow đóng góp cho chính repo browser-use.** Ta là người tiêu thụ, không phải contributor.

**Skill `x402`, `open-source`, `remote-browser` của họ.** Bán hàng cho Cloud của họ, không phải
tri thức chuyển giao được.

## Bảng kiểm chứng

| khẳng định | bằng chứng |
|---|---|
| browser-use không dùng Playwright | `grep -ril playwright browser_use/` → 10 file, đọc từng dòng: toàn comment + link `playwright.dev`. `pyproject.toml` không có dependency playwright nào |
| họ tự khai không cần | `pyproject.toml:244` — `# "pytest-playwright-asyncio>=0.7.0",  # not actually needed I think` |
| họ dùng CDP trực tiếp | `pyproject.toml:43` — `cdp-use==1.4.5` |
| `browser-harness` chỉ 4 dependency | `bh/pyproject.toml` → `cdp-use`, `fetch-use`, `pillow`, `websockets`. Không SDK LLM nào |
| cài được và chạy được | `python3.13 -m venv` + `pip install ./bh` → `browser-harness --help` in đầy đủ, rc=0 |
| yêu cầu Python ≥ 3.11 | `bh/pyproject.toml:10`. `python3` mặc định của máy này là **3.9.6** → cài bằng `python3` trượt ở bước build `setuptools==84.0.0`, rc=1 |
| chạy được `file://` | chạy thật: `new_tab("file:///…/overstack-architecture.html")` → `page_info()` ra `{'url': 'file:///…', 'title': '🐴 Overstack — framework hoạt động thế nào Diagram', …}`, ảnh 196.5 KB ghi ra đĩa |
| `drain_events()` trả event thật | cùng lượt trên, `EVENTS: 50` |
| daemon giữ tab qua các lượt CLI | lượt thứ hai (tiến trình mới hoàn toàn) in `STILL: 🐴 Overstack…` / `TABS: 1` mà không gọi lại `new_tab` |
| lượt sau nhanh 0.138s | `time` trên lượt hai: `0.138 total` |
| Playwright script mất 1.1–1.9s mỗi lượt | `time python3 pw.py` (launch → goto `file://` → title → close) → 3 lần: 1.89 · 1.54 · 1.06; lần chạy đầu cold-cache 3.38. Playwright `connect_over_cdp` lượt sau: 0.80 · 0.67 · 0.65, state giữ (`window.__marker` sống qua tiến trình mới). Đo bằng python-playwright, không phải node `.mjs` |
| `$HOME` sâu làm chết daemon | `HOME=/private/tmp/claude-501/…/scratchpad/fakehome` → `browser-harness: fatal: AF_UNIX path too long`, rc=1. `HOME=/tmp/bhh` → chạy |
| `doctor` fail-open rc=0 | `doctor --json` in `"healthy": false` mà vẫn rc=0 — không được rẽ nhánh theo mã thoát |
| API helper đúng như tài liệu | `grep '^def ' src/browser_harness/helpers.py` → có đủ `page_info` `click_at_xy` `drain_events` `js` `wait_for_load` `new_tab` `switch_tab` `upload_file` |
| chi phí cloud | **chưa kiểm chứng** — chép từ `skills/qa/SKILL.md` của họ, không có API key khi khảo sát |
| tunnel/proxy/interstitial gotchas | **chưa kiểm chứng** — chép từ `skills/qa/references/methodology.md`, họ ghi là "field-hit" |

## Bẫy đắt nhất

**`AF_UNIX path too long`.** Socket của daemon nằm dưới `$HOME`, macOS giới hạn đường dẫn
socket 104 ký tự. Scratchpad của Claude Code sâu hơn thế, nên chạy trong scratchpad với `HOME`
cô lập là chết ngay ở lượt đầu — và thông báo lỗi không nói gì về `$HOME`. Đặt `HOME=/tmp/bhh`.

**`doctor --json` trả rc=0 khi `healthy: false`.** Ai viết wrapper rẽ nhánh theo mã thoát sẽ
tưởng mọi thứ ổn trong khi daemon chưa sống. Parse trường `.healthy` trong JSON.

## Install (dùng tại chỗ)

```bash
mkdir -p .claude/skills && ln -sfn ../../.overstack/doyourmagic/browser-use/skills/dym-browser-use .claude/skills/dym-browser-use
```

Chỉ hub vào context — một dòng description. Gõ `/dym-browser-use` xem bảng slug,
`/dym-browser-use <slug>` để nạp một workflow.
