---
name: dym-browser-use
disable-model-invocation: true
domains: [browser, qa, playwright]
source: browser-use/browser-use
description: "browser-use/browser-harness — lái trình duyệt qua CDP thay vì script Playwright dùng-một-lần · gõ /dym-browser-use <slug> · slugs: repl · qa · cloud"
---

# dym-browser-use

Hub bundle `doyourmagic` cho `github.com/browser-use/browser-use` (v0.13.10, đo 09/2026)
và repo em của nó `github.com/browser-use/browser-harness` (v0.1.13).

## Steps
1. Đọc ARGUMENTS → `<slug>`. Không có slug → in bảng dưới rồi DỪNG.
2. Tìm file con theo thứ tự, lấy file ĐẦU TIÊN tồn tại, đọc ĐÚNG MỘT file:
   (1) `../dym-browser-use-<slug>/SKILL.md` (cạnh hub — cài qua `npx skills add rheinmir/dym`);
   (2) `.overstack/doyourmagic/browser-use/skills/dym-browser-use-<slug>/SKILL.md` (bundle trong dự án);
   (3) `.claude/skills/dym-browser-use-<slug>/SKILL.md`.
   Làm theo Steps/Rules của file đó. Không đọc file con khác. Không thấy cả 3 → nói rõ, dừng.

| slug | mục đích |
|---|---|
| `repl` | Lái trình duyệt kiểu REPL có trạng thái — mỗi lượt một hành động, tab giữ nguyên giữa các lượt. Thay `playwright-verify` khi việc cần NHIỀU bước. |
| `qa` | Chấm điểm 1–5 một site/app kèm bằng chứng, gồm cả lỗi console/network mà ảnh chụp không thấy. |
| `cloud` | Cloud browser + tunnel `localhost` ra ngoài, khi cần môi trường sạch hoặc chạy song song. Tốn credit. |

## Rules
- KHÔNG cài `browser-use` (gói agent, 50+ dep gồm openai/anthropic/google-genai) chỉ để lái
  trình duyệt. Thứ cần là `browser-harness`: 4 dep (`cdp-use`, `fetch-use`, `pillow`,
  `websockets`), không SDK LLM nào.
- `browser-use` v0.13 KHÔNG dùng Playwright. Mọi chữ "playwright" trong mã nguồn nó chỉ là
  comment/link tài liệu (đo: `grep -ril playwright browser_use/` → chỉ trúng comment; `pyproject.toml:244`
  ghi `# "pytest-playwright-asyncio>=0.7.0",  # not actually needed I think`). Đừng đọc repo đó
  để tìm "mẹo Playwright" — không có.
