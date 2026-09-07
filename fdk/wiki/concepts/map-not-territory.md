---
type: concept
title: "map-not-territory — model càng mạnh, khoảng cách bản đồ↔lãnh thổ càng rộng; tìm unknowns TRƯỚC khi prompt"
status: living
tags: [prompting, unknowns, assumptions, fable5, process, gate]
timestamp: 2026-09-07
id: map-not-territory
relations:
  - {rel: depends-on, to: harness-enforcement-floor}
  - {rel: relates-to, to: rule-registry}
---

# map-not-territory — tìm unknowns trước khi prompt

**Bản đồ** = mọi thứ ta đưa vào context (prompt, `CLAUDE.md`, skill, wiki). **Lãnh thổ** = codebase thật + ý định ngầm của người yêu cầu. Luận điểm của Thariq (Anthropic, quanh Fable 5): model càng mạnh thì khoảng cách này **không thu hẹp mà nới rộng** — vì model mạnh lấp chỗ mơ hồ bằng một câu trả lời *tự tin*, lỗi lan ra nhiều file và chỉ lộ muộn. Hệ quả: chỗ đáng đầu tư không phải "prompt hay hơn" mà là **tìm ra mình chưa biết gì** trước khi để model chạy, và **soát lại bản đồ mỗi khi đổi model** (bản đồ vẽ cho model cũ có thể sai với model mới).

## Kỹ thuật (chưng cất)
1. **Hỏi model liệt kê unknowns** trước khi làm — "để làm đúng việc này, cần biết gì mà chưa có trong context?" — rồi đi *tra* (fact) hoặc *hỏi* (decision), đừng để nó tự lấp.
2. **Paraphrase-plan** — bắt model kể lại kế hoạch bằng lời của nó trước khi chạm code; chỗ nó kể lệch là chỗ bản đồ thiếu.
3. **Khai giả định ra giấy** — mọi thứ model tự điền phải nhìn thấy được và sửa được ở một chỗ.
4. **Map-freshness audit khi đổi model** — soát lại `CLAUDE.md`/skill với model mới: luật viết để bù điểm yếu của model cũ có thể thành nhiễu.

## Đối chiếu overstack — ĐÃ CÓ vs THIẾU
| Kỹ thuật | overstack đã có | Ở đâu |
|---|---|---|
| Liệt kê unknowns trước khi làm | **Có** — `/propose` bước 0b "Tìm unknowns" (thêm 2026-09-07, GH#40) + bước 0 force-query wiki | `skills/propose/SKILL.md` |
| Khai giả định + thang 3 tầng `(default)` / `(default, find-out-later → unknown-ledger)` / `[CẦN LÀM RÕ]` | **Có** | `skills/propose/SKILL.md` mục "Tự điền hay hỏi" |
| Gate: SPEC còn `[CẦN LÀM RÕ]` không được ra cổng duyệt | **Có** — R7 `forbid_contains` | `harness/poc-vendor-neutral/policy.yaml` R7 |
| Unknown đã fill-default nhưng phải có sổ, truy được, trả được | **Có** — `unknown-ledger.py` (0-token) | `harness/scripts/unknown-ledger.py` |
| Floor check / đa giả thuyết trước khi trả lời | **Có** — skill `fable5` | `skills/fable5/SKILL.md` |
| Paraphrase-plan như một *gate* máy-đọc | **Thiếu** — hiện chỉ là bước prompt (`/plan` viết PLAN cho agent context=0 là dạng gần nhất) | — |
| Map-freshness audit khi đổi model | **Thiếu** — không hook nào ghi model-id của phiên để phát hiện đổi model | — |

Hai mục thiếu **cố ý chưa làm**: gate paraphrase cần LLM chấm (không tất định, trái sàn 0-token của harness), còn audit-đổi-model cần tín hiệu model-id trong payload hook mà Claude Code chưa cấp ổn định. Ghi lại để không lấp bằng mặc định.

## Notes
- [[harness-enforcement-floor]] — vì sao gate phải tất định.
- [[rule-registry]] — R7 nằm ở đâu trong sổ luật.

## Origin
- **Source:** GH#40 (mirror của ledger `050726-map-not-territory-fable5-unknowns.md` — ledger chưa từng được commit, xem GH#99) · [explainx.ai — Map Is Not the Territory](https://explainx.ai/blog/map-is-not-territory-fable-5-thariq-unknowns-2026) · [Thariq @trq212](https://x.com/trq212/status/2073101078145724589) · [the-decoder](https://the-decoder.com/anthropic-developer-shares-prompting-tips-for-fable-5-that-focus-on-finding-your-own-blind-spots-first/) · [Anthropic — Fable 5 & Mythos 5](https://www.anthropic.com/news/claude-fable-5-mythos-5)
- **Date:** 2026-09-07
