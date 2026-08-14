---
title: "Overstack vs thế giới — 11/08/2026: repowise-dev/repowise"
status: living
tags: [innovation, frontier, comparison, gap-analysis, competitor]
timestamp: 2026-08-11
id: innovation-110826
---

# Overstack vs thế giới — rà soát 11/08/2026 (repowise)

Tiếp nối [[innovation-100826]] (hôm qua). Khác các kỳ trước (quét 4-5 trục bằng `last30days`/WebSearch), kỳ này là **quét 1 đối thủ cụ thể theo yêu cầu trực tiếp** ("repowise-dev/repowise distill nó đi") — không phải chu kỳ tuần đầy đủ. Xác nhận tiền đề: GH#9-13/#101/#102 không đổi kể từ 100826 (không re-check `gh` lần này vì không phải chu kỳ đầy đủ).

## repowise-dev/repowise là gì
Codebase-intelligence CLI + MCP server (Python, AGPL-3.0, 5088★, push gần nhất 2026-08-10). Index 1 lần → 5 lớp (graph/git/docs/decisions/code-health) → phục vụ 10 MCP tool task-shaped + dashboard + PR bot + VS Code extension. Chi tiết đầy đủ: [[repowise]].

## Đối chiếu điểm chạm thật với overstack (không phải toàn bộ 5 trục cũ)

| Trục chạm | 🔵 Overstack đang có | 🟢 repowise có | Verdict |
|---|---|---|---|
| **MCP code-context tool** | `code-graph` — 12 tool entity-shaped (1 file/symbol/lệnh), không staleness meta, không batch nhiều target | 10 tool **task-shaped**, batchable, `_meta.stale_warning` khi index lệch HEAD | **Thua về ergonomics** — không phải thiếu năng lực nền (graph có), mà thiếu lớp "câu hỏi task" bọc ngoài + cảnh báo stale |
| **Code-health scoring** | `harness/validators/code_health.py` — chỉ `py_compile` cú pháp, đỏ/xanh nhị phân | 49 detector tất định, 1-10/file, 3 tín hiệu (defect/maintainability/perf), calibrated trên corpus lỗi thật (ROC AUC 0.737/21 repo), sinh refactoring plan cụ thể (Extract Class/Method, Break Cycle...) | **Thua rõ — gap mới, chưa từng track trong ledger** |
| **Dead-code detection** | Không có | `get_dead_code` theo confidence tier + cleanup-impact | **Thua — gap mới** |
| **PR review tự động, 0-LLM** | Không có (chỉ có `/code-review` LLM-based) | PR bot free, blast-radius symbol-level, change-risk vs phân phối commit riêng của repo, Check Run gate-được, im lặng khi sạch | **Thua — nhưng khác category** (repowise 0-LLM deterministic; `/code-review` LLM-based sâu hơn về ngữ nghĩa, không đối nghịch trực tiếp) |
| **Command-output distillation** | Không có trong framework, NHƯNG user đã có `rtk` (RTK — Rust Token Killer) riêng, global, tự thiết kế trước khi biết repowise tồn tại | `repowise distill <cmd>` — 61-89% token, lossless qua marker | **Không phải gap** — trục này đã có giải pháp tương đương ở tầng user-tool, không cần xây trong overstack |
| **Doc generation (wiki)** | `/ingest`+`/query`: LLM đọc source thật → chất lượng cao, tốn token+thời gian người, per-file surgical | Sinh wiki 0-LLM từ structure trước (miễn phí), nâng cấp prose theo yêu cầu, có freshness/confidence score | **Khác model chi phí, không phải thua** — overstack ưu tiên độ chính xác từ nguồn thật, repowise ưu tiên phủ 100% miễn phí trước |

## Cập nhật cùng ngày: user yêu cầu không chỉ doc mà distill CƠ CHẾ — đã build một lát cắt thật

User bác bỏ hướng "chỉ viết issue rồi chờ" — yêu cầu đọc code gốc (Python, cùng ngôn ngữ) và viết lại cơ chế thật trong overstack. Vì repo repowise là **AGPL-3.0** còn overstack **MIT**, đã hỏi user và chọn **clean-room**: đọc README thuật toán của họ (`packages/core/src/repowise/core/analysis/health/{complexity,biomarkers,duplication}/README.md` qua `gh api`, không tải code họ về máy) để hiểu cơ chế (McCabe CCN, LCOM4 connected-components, Rabin-Karp token clone), rồi tự viết lại bằng `ast`/`tokenize` stdlib — không copy dòng nào.

**Đã ship:** `harness/validators/code_complexity.py` — CCN McCabe + NLOC per-function, LCOM4-lite cohesion (connected components qua `self.attr`/gọi-lẫn-nhau, có safety-valve giống ý tưởng của họ khi 0 tín hiệu), god-class heuristic, duplicate-code (token-chunk hash — đơn giản hơn sliding Rabin-Karp thật của họ), điểm 1-10/file, advisory-only (exit 0). Selftest assert-based (`--selftest`) xanh. Chạy thật trên repo: 124 file .py, bắt đúng finding thật (vd phát hiện `harness/validators/proposal_complete.py` trùng token gần 100% với mirror `llmwiki/.claude/hooks/validators/proposal_complete.py` — đúng cặp canonical+mirror đã biết trong dự án, xác nhận detector hoạt động thật chứ không phải false-positive ngẫu nhiên).

**Còn thiếu, cố ý KHÔNG làm ở lượt này (ghi rõ ceiling, không giả vờ đã xong):**
- **Không "defect-validated"** — trọng số ở `_SCORE_WEIGHTS` là tự chọn, KHÔNG calibrated trên corpus lỗi thật (repowise dùng 21-repo/9-ngôn-ngữ, mình không có). Không claim ROC-AUC nào.
- **Chỉ Python** — repowise 18 ngôn ngữ qua tree-sitter; đây dùng `ast`/`tokenize` stdlib nên chỉ .py. Ladder: chưa cần thêm dependency tree-sitter khi repo này chủ yếu Python.
- **Chưa có:** dead-code detection, PR-bot 0-LLM, refactoring-plan sinh cụ thể (Extract Method/Class...), git-hotspot/churn signal (dù `harness/scripts/mem-rank.py`/code-graph đã có mảnh git-meta riêng, chưa nối vào tool này).
- **Chưa wire vào gate/medic** — đứng standalone, advisory, giống tinh thần `_deep_lint` trong `code_health.py`. Cần hỏi user trước khi nâng thành hard-gate (đổi hành vi CI).

## Có nên raise issue GitHub?

Phần code-health cốt lõi (CCN/cohesion/duplication) **đã build**, không còn là gap trống — issue nếu raise giờ nên đổi khung thành "còn thiếu gì" (dead-code, PR-bot, calibration) thay vì "chưa có gì". Vẫn KHÔNG trùng GH#9-13/#101/#102. Chưa raise trong phiên này — tạo issue GitHub là hành động công khai, cần user xác nhận trước.

## Nguồn
- https://github.com/repowise-dev/repowise (README, `gh api repos/repowise-dev/repowise/readme`, `gh repo view`, fetch 2026-08-11)
- Đối chiếu nội bộ: `fdk/CAPABILITIES.md`, `harness/validators/code_health.py`, danh sách tool `mcp__code-graph__*` (system reminder phiên này)

## Origin
Kích hoạt bởi yêu cầu trực tiếp "repowise-dev/repowise distill nó đi" (phiên 2026-08-11). `llmwiki/raw/` khoá ghi cho agent theo luật "chỉ người ghi" (`.claude/settings.json` deny Write/Edit/MultiEdit trên `llmwiki/raw/**`) — user chọn bỏ qua `raw/`, ghi thẳng entity [[repowise]] + note so sánh này thay vì chạy `/ingest` chuẩn.
