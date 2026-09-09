---
type: issue
kind: tech-debt
title: "retrieval-eval giòn (TOKEN_EPS=0 ⇒ spam mọi lần wiki lớn) + pull-gate hit@1→0 bị nuốt khi re-baseline"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, ci, retrieval-eval, baseline, tech-debt, harness]
timestamp: 2026-07-03
id: 030726-retrieval-eval-baseline-rot
source_session: "phiên fix CI 2026-07-03 — sau khi fix R3 lộ ra retrieval-eval đỏ sẵn"
---

# Issue: retrieval-eval baseline rot + guard-rail quá giòn

## Vấn đề (một câu)
Gate `retrieval-eval --check` đặt `TOKEN_EPS=0.0` (mọi tăng token = regression) nên fail mỗi lần wiki lớn lên; baseline `harness/metrics/retrieval-baseline.json` đã lỗi thời nặng; và golden `pull-gate` bị tụt hit@1→0 (trang đúng bị các trang phình chiếm hết top-5) — khi re-baseline để cứu CI thì hit@0 bị nuốt vào baseline, mất cảnh báo.

## Bối cảnh & bằng chứng
- Phiên 2026-07-03 fix CI: sau khi vá R3 index-sync, `retrieval-eval` lộ ra đỏ SẴN trên HEAD sạch (stash-test): explain-clone-site token 4906→71244, fdk-what 21603→63936, trend-bnal-2 32041→66771, **pull-gate hit@k 1→0**. Không do phiên này gây ra.
- `TOKEN_EPS=0.0` (harness/scripts/retrieval-eval.py:46) + comment "token phình bất kỳ = hồi quy" → guard-rail bắt buộc re-baseline thủ công mỗi lần thêm/ sửa trang → nguồn "CI spam liên tục".
- pull-gate expected `ADR-002-pull-before-change-gates` VẪN tồn tại (`fdk/wiki/sources/adr/`), chỉ bị outranked bởi trang phình — cùng gốc với token bloat.
- Quyết định phiên này (user chọn): re-baseline để CI xanh + raise issue này để KHÔNG chôn pull-gate. Baseline đã được re-write; pull-gate ghi hit=0 (cần khôi phục về 1).

## Phạm vi
- `harness/scripts/retrieval-eval.py` (TOKEN_EPS, diff logic), `harness/scripts/query-proxy.py` (top-N ranking), `harness/metrics/retrieval-baseline.json`, corpus wiki phình. Universal (mọi project dùng harness).

## Không thuộc phạm vi
- Không bỏ hẳn gate retrieval-eval (guard chống context-bloat vẫn giá trị).
- Không xoá golden pull-gate.

## Hướng gợi ý (không bắt buộc)
1. **Nới TOKEN_EPS** thành ngưỡng tương đối (vd +10%/golden) thay vì 0 tuyệt đối → wiki lớn lên không spam, vẫn chặn phình đột biến.
2. **Khôi phục pull-gate hit@1**: điều tra trang nào phình chiếm top-5, trim/tách trang đó hoặc chỉnh ranking query-proxy để ADR-002 quay lại top-5. Sau đó cập nhật baseline hit=1.
3. **Tách "token growth hợp lệ" khỏi "hit regression"**: chỉ hit@k tụt mới là regression cứng; token dùng ngưỡng mềm + cảnh báo.
4. Cân nhắc auto-rebaseline có kiểm soát trong `/medic` khi chỉ token tăng và mọi hit giữ nguyên.

## Tiêu chí HOÀN THÀNH
- pull-gate về hit@1 (baseline ghi hit=1, không phải 0).
- Thêm 1 trang wiki bình thường KHÔNG làm `retrieval-eval --check` đỏ (ngưỡng mềm hoạt động).

## Assign & lý do
- @Rheinmir chủ; Claude dispatch (đụng validator harness). Mở `/fdk`. P2 — CI đã xanh tạm bằng re-baseline, đây là trả nợ bản chất.

## Repo/paper tham khảo
- Nội bộ: `skills/dev-loop/wikieval.md` (cùng khuôn baseline+diff), `fdk/wiki/concepts/query-retrieval-eval.md`.

## Đã giải (2026-07-04, /fdk issue-16)
- **Gốc**: `retrieve_L1` xếp hạng bằng độ-phủ-term trên TOÀN VĂN — trái docstring "tầng-1 xếp hạng bằng title+heading" — nên trang phình generic (tình cờ chứa cả term tiếng Việt "hoạt/động") đè ADR-002 có tiêu đề khớp hẳn xuống hạng 6, rớt top-5.
- **Fix 1 — ranking (`query-proxy.py`)**: thêm `HEAD_BOOST=2`, khoá xếp hạng = `2×score(head) + score(full)`. ADR-002 quay về hạng 0; hit@5 22/30 → **30/30**, không golden nào tụt (heading-primary thuần gãy skill-sot; boost cân bằng thì không).
- **Fix 2 — ngưỡng token (`retrieval-eval.py`)**: `TOKEN_EPS=0.0` tuyệt đối → `TOKEN_REL_EPS=0.15` tương đối. Token phình ≤ +15%/golden = WARN note (không đỏ); > +15% = hồi quy cứng; hit@k tụt vẫn cứng tuyệt đối.
- **Baseline** re-write: pull-gate `hit=1` recall=1.0.
- **Kiểm chứng feedback loop còn cắn**: thêm 1 trang wiki thường → 15 golden nhích token nhưng `--check` vẫn OK (chỉ note), hết spam; self-test 30/30 coherent.
- **Còn nợ (để full 3/3 trụ)**: chưa bọc skill (trụ skills) + chưa promote guidance vào wiki concept `query-retrieval-eval` (trụ llmwiki) — mới vá tầng harness. Ghi ở problem-tree node p-15.

## Origin
Raise bởi phiên fix-CI 2026-07-03. Bằng chứng: stash-test retrieval-eval trên HEAD sạch; harness/scripts/retrieval-eval.py:46; git run harness fail #28668773256.
