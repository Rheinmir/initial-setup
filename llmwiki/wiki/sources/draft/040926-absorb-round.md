# 040926-absorb-round
**Type:** draft
**Status:** proposed
**Tags:** adapt-modes, absorb, doyourmagic, gate
**Proposed:** 2026-09-04

## What
Đóng vòng cho 8 lượt `/doyourmagic` chạy cùng ngày: từ 8 bundle tài liệu → **9 thay đổi framework**, mỗi cái đi kèm bite-test và một phán quyết `[[adapt-modes]]` có tên.

## Output

| # | Lấy từ | Kiểu | Thành cái gì | Bằng chứng |
|---|---|---|---|---|
| 1 | diagram-design `self_check.py` | HÒA TAN | 4 luật SVG trong `frontend-antipattern.py` | 86 svg đo trước; FAIL cho 2 luật đang 0 vi phạm, WARN cho 2 luật có nợ (20/33, 17/33) |
| 2 | humanizer 35 pattern | HÒA TAN | `prose-antipattern.py`, probe `prose` | Loại em-dash (96/266) + bold (113/266) bằng SỐ ĐO; giữ 4 luật |
| 3 | — (lỗ hổng quy trình) | — | `/doyourmagic` step 9 kết ở cổng adapt-modes | 8 lượt trước ra 0 quyết định |
| 4 | lieflat-charts + dataviz | HÒA TAN | Kỷ luật #9 của hallmark | dataviz 0/22 lời gọi, 1 mention trong repo (đã archive) |
| 5 | nuwa `fidelity-scorecard.md` | HÒA TAN | `skill-health.py --fidelity` | 85/86 đạt phần tĩnh → thông tin phân biệt nằm ở 70 điểm chưa chấm |
| 6 | archify `repository-evidence.mjs` | HÒA TAN | Neo `data-src` fail-closed cho node sơ đồ | 3 node overstack neo thật; đổi neo giả → 1 FAIL |
| 7 | impeccable 61 luật | **KÉO NGOÀI** | `ui-detect.py` opt-in, pin `@3.6.1` | 342 finding trên overstack — cổng nhà 9 luật báo sạch |
| 8 | archify `visual-check.mjs` | HÒA TAN | `visual-receipt.py` — biên lai + contact sheet + 4 ảnh | chạy thật: 4 ảnh, 0 lỗi console, 0 request ra ngoài |
| 9 | cti-expert workflow 08 | HÒA TAN (mẩu) | `supply-watch.py` — chân 3 của orca-sec-scans | `orca --tld com,dev` → 38 tên na ná đang sống |

**KHÔNG LẤY, có lý do:** cti-expert nguyên khối (121 op, cần key+mạng, kéo bẩn một cổng đang keyless) · scientific-agent-skills (catalog 163 skill, lấy theo nhu cầu) · diagram-design làm bộ VẼ (mỗi sơ đồ tốn một lượt agent — xem dưới).

## Bài học đắt nhất: so sai trục thì đảo ngược kết luận

Lượt đầu tôi kết luận "diagram-design rẻ hơn Mermaid" vì so **dung lượng**: 0 dep so với 610KB engine nhúng. Sai trục. Trục quyết định chi phí của một framework regen docs theo nhịp là **số lượt agent mỗi sơ đồ** và **code có tự sinh được không LLM**:

| | Agent trả gì mỗi sơ đồ | Code tự sinh được? |
|---|---|---|
| Mermaid | ~10–20 dòng text | ĐƯỢC |
| diagram-design | trọn inline SVG bằng tay | **KHÔNG** (tài liệu của chính nó: "Không có CLI để vẽ sơ đồ") |
| Generator Python của ta | **0** | đã tự sinh rồi |

Đo thêm thì lộ: hai generator chính (`build-overstack-docs.py`, `build-wiki-graph.py`) nhắc "mermaid" **0 lần** và dựng SVG thẳng ở 37 chỗ. Cả repo có đúng 1 khối ```` ```mermaid ```` — trong archive. Nên thứ đáng lấy từ diagram-design co lại còn **luật**, không phải bộ vẽ. Luật đó chạy trên cả Mermaid lẫn SVG-Python.

Luật này đã ghi vào step 9 của `/doyourmagic` để lần sau không phải trả giá lại.

## Một khuôn lặp lại ba lần: BỎ QUA ≠ SẠCH

`ui-detect` (npx không chạy), `visual-receipt` (thiếu chromium), `supply-watch` (crt.sh không gọi được) — cả ba đều phải phân biệt "chưa kiểm được" với "kiểm rồi, sạch". Bản nháp đầu của `ui-detect` in `✓ sạch theo 61 luật` trong khi chưa hề quét nổi. Quy ước rc=2-là-skipped mượn của archify `visual-check`.

## Files
| File | Action |
|------|--------|
| `fdk/tools/frontend-antipattern.py` | modified (4 luật SVG + neo bằng chứng, self-test 4→10) |
| `fdk/tools/prose-antipattern.py` | created |
| `fdk/tools/ui-detect.py` | created |
| `fdk/tools/visual-receipt.py` | created |
| `fdk/tools/supply-watch.py` | created |
| `fdk/tools/medic.py` | modified (probe `prose`) |
| `harness/scripts/skill-health.py` | modified (`--fidelity`) |
| `harness/scripts/dep-health.py` | modified (orphan = cha đã chết) |
| `skills/doyourmagic/SKILL.md` · `skills/hallmark/SKILL.md` · `skills/orca-sec-scans/SKILL.md` | modified |

## Notes
- Mọi công cụ mới đều có `--self-test` xanh. `medic --ci`: 0 fail · 0 warn · 17 ok.
- Nợ mở đã khai: 20/33 sơ đồ còn thiếu `role="img"`, 17/33 thiếu `<title>` — WARN có chủ ý, nâng lên FAIL khi nợ về 0.
- Nợ mở thứ hai: `ui-detect` báo 342 finding trên overstack.html mà chưa ai phân loại.

## Origin
- **Draft:** `wiki/sources/draft/040926-absorb-round.md`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
