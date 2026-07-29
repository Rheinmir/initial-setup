---
type: draft
title: 280726-onboard-setup
status: proposed
tags: [orca-onboard, output-report]
timestamp: 2026-07-28
---

# 280726-onboard-setup

**Status:** proposed

## Agent CLI Availability
| Agent | Binary | Status |
|-------|--------|--------|
| Antigravity | `agy` | ✅ 1.0.3 |
| OpenCode | `opencode` | ✅ 1.15.10 (nhưng treo khi dispatch — xem Notes) |
| Kiro | `kiro-cli` | ❌ not found |

## Agent Task Assignment
| Task | Agent | Model | Status |
|------|-------|-------|--------|
| Phase 1 — Graph generation (853 files) | distilled pipeline: bash + python static parse + Claude (layers/tour) | no-LLM parse + Opus | done |
| Phase 2 — Domain enrichment | Claude main thread | Opus | done |
| Phase 3 — Wiki generation | opencode | DeepSeek Flash v4 | skipped (user gate) |
| Phase 4 — HTML docs | opencode dispatch fail → Claude main thread assemble + python fill | Opus (fallback) | done |

## What

Onboard chính repo overstack (`rheinmir/setup`, nhánh `orca`, commit `9032ae4`) bằng pipeline distilled understand-anything: dựng knowledge graph tất định từ 846 file, chưng cất thành `ONBOARDING.md`, rồi bóc tách miền nghiệp vụ thành `domain-graph.json` và dựng trang HTML onboarding kèm vector quan hệ concept↔code.

Người dùng chốt ở cổng Phase 0.5 là chạy **Phase 1 + 2 + 4**, bỏ Phase 3, vì `llmwiki/` của repo này đã có 354 file curated do người viết — sinh wiki tự động sẽ giẫm lên nội dung thật. Đây là quyết định đúng và đã được tôn trọng: không một file nào trong `llmwiki/wiki/concepts/` hay `entities/` bị chạm.

## Kết quả đo được

| Chỉ số | Giá trị |
|---|---|
| File phân tích | 846 (853 tracked, trừ 7 binary/lock) |
| Node trong graph | 846 — 593 document, 183 file code, 70 config |
| Cạnh | 2 905 — 1 640 documents, 717 depends_on, 360 configures, 115 related (co-change), 42 calls, 31 imports |
| Tầng kiến trúc | 15, mỗi node thuộc đúng một tầng |
| Bước tour | 13, mọi `file:line` đã đối chiếu tồn tại thật |
| Node orphan | 86 / 846 |
| Domain / flow / step | 7 / 26 / 124 — **124/124 step trỏ file:line hợp lệ** |
| Thời gian static parse | 0,83 giây, **0 token** |
| Cảnh báo validate graph | không có |

## Output

- `.understand-anything/knowledge-graph.json` — 967 KB, nodes + edges + layers + tour
- `.understand-anything/ONBOARDING.md` — 24,7 KB bản chưng cất cho người và agent đọc
- `.understand-anything/meta.json` — neo commit để lần sau chạy `--update`
- `.orca-onboard/intermediate/domain-graph.json` — 7 miền, 26 luồng, 124 bước có file:line thật
- `llmwiki/html/onboarding-setup.html` — 86 KB, skeleton v2 frozen + JSON island
- `llmwiki/html/wiki-graph.html` — vẽ lại: 336 node, 375 cạnh, primary = llmwiki
- Xem tại: `http://localhost:8766/llmwiki/html/onboarding-setup.html`

## Files
| File | Action |
|------|--------|
| `.understand-anything/knowledge-graph.json` | created |
| `.understand-anything/ONBOARDING.md` | created |
| `.understand-anything/meta.json` | created |
| `.orca-onboard/intermediate/domain-graph.json` | created |
| `.orca-onboard/tmp/parse.py` | created (static parser, 0 token) |
| `.orca-onboard/tmp/build_graph.py` | created (layers + tour + validate) |
| `.orca-onboard/tmp/mk_onboard_json.py` | created (STEP A fallback) |
| `.orca-onboard/tmp/onboard.json` | created (dữ liệu cho skeleton) |
| `llmwiki/html/onboarding-setup.html` | created (gitignored — cần `git add -f` nếu muốn commit) |
| `llmwiki/html/wiki-graph.html` | modified (regen bởi STEP C) |
| `llmwiki/wiki/index.md` | modified (thêm 1 row cho draft này) |
| `llmwiki/wiki/log.md` | modified (thêm entry ngày 28/07) |
| `llmwiki/wiki/draft/orca/280726-onboard-setup.md` | created (chính file này) |

Không có file nào trong `llmwiki/wiki/concepts/`, `llmwiki/wiki/entities/`, `skills/`, `harness/`, `fdk/` bị sửa.

## Notes

- Gọi qua skill `/orca-onboard`, project root `/Users/thoaidd/Documents/Development/harness/setup`.
- Cấu tạo repo: 585 Markdown, 125 Python, 39 Shell, 32 YAML, 30 JSON, 8 HTML. Đây là repo nơi tri thức và cấu hình chính là sản phẩm, còn Python/Shell là bộ máy thực thi — nên tầng `knowledge-base` (224 file) và `skills` (199 file) chiếm gần một nửa.
- **Phase 1 chạy static parse thuần, không tốn token nào.** Toàn bộ 846 node và 2 905 cạnh dựng trong 0,83 giây bằng regex import/require, markdown link, path mention, cộng tín hiệu git (churn 365 ngày, recent 30 ngày, co-change ngưỡng ≥4). Quyết định này theo đúng bài học ghi trong SKILL.md từ run `120626-zca-bridge`: việc bóc import là mechanical, LLM không chính xác hơn regex mà lại đắt.
- **Bước 1.7 code-graph MCP bị bỏ qua đúng luật.** `python3 harness/scripts/dep-health.py --json` trả `status: absent` với lý do "không có `.graph-agent/index.db` nào trong project". Skill quy định chỉ chạy khi `status == "ok"`, nên không index. Đây chính là nguyên tắc "tồn tại ≠ dùng được" mà repo đã trả giá để học.
- **opencode dispatch thất bại hai lần.** Lần một `timeout` không có trên macOS nên lệnh không chạy. Lần hai chạy thật thì `opencode run ... --model opencode/deepseek-v4-flash-free` treo hết 5 phút rồi bị kill (exit 143), không sinh ra `onboard.json`. Theo đúng đường fallback ghi trong SKILL.md, Claude main thread tự assemble JSON theo schema skeleton rồi python điền vào skeleton v2 — không bao giờ tự viết HTML thô. Cần điều tra riêng vì đây là lần thứ hai opencode treo khi được dispatch không kèm `--dangerously-skip-permissions`.
- **Engine `build-wiki-graph.py` suýt chọn nhầm bản.** Lệnh gợi ý trong SKILL.md dùng `ls repo-local global | head -1`, nhưng `ls` sắp xếp theo alphabet nên đường dẫn tuyệt đối `/Users/...` đứng trước `fdk/tools/...` và bản GLOBAL (cũ hơn, không nhận `--also`) được chọn. Đã thay bằng vòng lặp `for` kiểm tra theo đúng thứ tự ưu tiên repo-local → global. Đây là lỗi thật trong SKILL.md, nên sửa ở canonical.
- Reasoning (layers, tour, domain, narrative) giữ trong Claude main thread, không dispatch — đúng luật dispatch của skill.
- Bước sync push `SKILL.md` lên `rheinmir/setup` được bỏ qua vì đang đứng CHÍNH trong repo đó và `skills/orca-onboard/SKILL.md` không bị sửa trong phiên này (đã `diff` xác nhận canonical khớp cả bản cài `~/.agents/skills/` và `~/.claude/skills/`).

## Đề xuất việc tiếp theo

1. Sửa `skills/orca-onboard/SKILL.md` bước STEP C: thay `ls a b | head -1` bằng vòng lặp ưu tiên repo-local, vì `ls` sort alphabet chọn sai engine. Lỗi tái hiện được 100%.
2. Điều tra vì sao `opencode run` treo khi dispatch từ Claude Code — hiện mọi phase mechanical đều phải rơi về Claude, làm mất hẳn lợi ích chi phí mà dispatch board hứa.
3. Cân nhắc promote phần "Đang làm gì gần đây" và "Điểm cần cẩn thận" trong `ONBOARDING.md` thành một concept trong `fdk/wiki/` — đó là tri thức về chính framework (ADR-008), không thuộc `llmwiki/wiki/`.

## Cost Estimate (thực tế so với dự toán)

| Phase | Dự toán | Thực tế |
|-------|---------|---------|
| Phase 1 (graph) | ~$0.60 | static parse 0 token; chỉ tốn phần Claude viết layers/tour/ONBOARDING |
| Phase 2 (domain) | ~$0.50 | Claude main thread, đúng dự toán |
| Phase 3 (wiki) | ~$0.02 | $0 — bỏ theo quyết định ở cổng |
| Phase 4 (HTML) | ~$0.01 | opencode fail → Claude assemble, đắt hơn dự toán nhưng vẫn nhỏ |

## Origin
- **Draft:** `wiki/draft/orca/280726-onboard-setup.md`
- **Commit phân tích:** `9032ae42fbe1e74115bf852decd12c6ca57d467e`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
