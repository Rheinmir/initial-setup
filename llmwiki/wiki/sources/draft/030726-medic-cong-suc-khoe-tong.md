---
type: draft
title: "030726-medic — cổng sức khoẻ tổng / tuyến phòng thủ cuối của framework (1 lệnh, tự-mở-coverage)"
status: proposed
tags: [medic, health-gate, enforcement, harness-doctor, hub, output-report]
timestamp: 2026-07-03
relations:
  - {rel: derives-from, to: harness-doctor}
  - {rel: touches, path: fdk/tools/medic.py}
  - {rel: touches, path: harness/scripts/harness-doctor.py}
  - {rel: touches, path: fdk/tools/build-overstack-docs.py}
---

# 030726-medic — cổng sức khoẻ tổng / tuyến phòng thủ cuối

**Type:** draft · **Status:** proposed · **Proposed:** 2026-07-03 · **Task:** T-260703-01

## What
`medic` — MỘT lệnh gom mọi kiểm tra tất định của framework thành một **cổng sức khoẻ tổng / tuyến phòng thủ cuối**. Gõ `medic`, xanh = hệ khoẻ; user không phải nhớ/gọi 7 công cụ lẻ.

## Context (force-query + kim chỉ nam)
- **[[fdk]] kim chỉ nam 2 (hub & trình bày, 2026-07-03):** hub 1-tên, mô-tả-phạm-vi (không nhớ subcommand), tên NGẮN gõ như `curl`; output TL;DR cô-đọng-đủ-ý; cuối output recap + dạy dùng thụ động; **transparent (show cấu trúc thư mục) = an toàn, usage > performance**. `medic` là hiện thân đầu tiên của kim chỉ nam này.
- **`harness/scripts/harness-doctor.py`** (đã có) — fire-drill "mỗi rule 1 fixture BAD+GOOD, chạy validator thật, BAD phải bị chặn". Là **probe `rules`** của medic. Vấn đề: mới phủ **5/17** rule.
- **`build-overstack-docs.py` / `build-capabilities.py`** (đã có, `--check`, wired `stop.py`) — probe `docs`.
- Meadows: medic = vòng phản hồi trên chính tầng enforcement; **tự-mở-coverage** để không mục nào lọt lưới khi hệ lớn lên.

## Đã hiện thực (user "thực hiện luôn")
`fdk/tools/medic.py` (stdlib-only, fail-open từng probe) + symlink `~/.local/bin/medic` (gõ toàn cục). 6 probe compose tool đã có: `rules` (harness-doctor), `coverage` (rule có bite-test chưa — đọc policy.yaml LIVE), `backstop` (pre-commit), `docs` (build-*.py --check), `code` (compileall), `eval` (self-index gate nếu đã promote). `medic [phạm vi]` lọc probe; `--ci` exit≠0 khi có FAIL; `--list`. Output có recap + use-case + **cấu trúc thư mục** (kim chỉ nam).

**medic đã chứng minh vai ngay lần chạy đầu** — tự bắt: capabilities stale (đã regen), validator `proposal_complete.py` drift; và **bắt luôn cú sync SAI HƯỚNG** của chính tôi (làm R7 thành rail đen 4/5) → khôi phục → 5/5. Đây đúng là "hàng rào cuối".

## Impact
| Vùng | Ảnh hưởng |
|------|-----------|
| `fdk/tools/medic.py` | **mới** — hub, chỉ đọc/gọi tool khác, không sửa chúng |
| `harness/scripts/harness-doctor.py` | mở rộng `build_rN` 5→17 (Plan T3) — rủi ro chạm fire-drill hiện có |
| `~/.local/bin/medic` | symlink mới (máy-local; downstream tự cài qua Plan T4) |
| Không tool nào bị sửa hành vi | medic chỉ orchestrate |

## Plan
- [x] **T1 — Hub `medic.py`** 6 probe compose, scope-arg, `--ci`/`--list`, fail-open, output theo kim chỉ nam (recap + dir-structure).
- [x] **T2 — Gõ toàn cục** symlink `~/.local/bin/medic`.
- [ ] **T3 — Tự-mở-coverage đầy đủ**: mở `harness-doctor` `build_rN` phủ **17/17** (4 tầng: content-validator mở rộng · hook_event feed synthetic-event · process_gate temp-git BAD-state · documentary presence-check). Baseline coverage → medic FAIL nếu coverage TỤT hoặc rule mới thiếu bite-test.
- [ ] **T4 — Chốt cổng cuối**: wire `medic --ci` vào pre-commit + CI + copy symlink xuống downstream (install-harness). Đây là "đổi luật chơi" — blast-radius cao.
- [ ] **T5 — Backstop + eval**: cài pre-commit; promote self-index eval `scratchpad → harness/evals/self-index` để probe `eval` sống.

## Agent Task Assignment
| Task | Agent (CLI) | Lý do | Status |
|------|-------------|-------|--------|
| T1 Hub medic.py | Claude | thiết kế probe + output UX = substance | done |
| T2 symlink | Claude | 1 lệnh | done |
| T3 coverage 17/17 | Claude | fixture BAD/GOOD + synthetic hook/git = reasoning-heavy | pending |
| T4 wire CI/pre-commit | Claude | blast-radius cao, cần cẩn trọng | pending |
| T5 backstop+eval promote | Claude | di chuyển + verify | pending |

**Sequence diagram:** [030726-medic-cong-suc-khoe-tong-seq.html](../../../html/030726-medic-cong-suc-khoe-tong-seq.html)

## Success
1. `medic` zero-arg chạy, in PASS/FAIL + fix-hint từng probe + recap + cấu trúc (đạt T1/T2).
2. `medic --ci` exit≠0 khi có FAIL (chốt được) — **đã chứng minh** (docs stale → fail; sửa → pass).
3. Coverage lên 17/17; thêm rule mới thiếu bite-test → medic tự FAIL (T3).
4. Wire pre-commit/CI: commit làm hệ yếu bị chặn (T4).
5. `medic` gõ được ở downstream sau install-harness (T4).

## Origin
- **Draft:** `wiki/sources/draft/030726-medic-cong-suc-khoe-tong.md`
- **Commit:** _(verify-before-commit điền)_
- **Date promoted:** _(verify-before-commit điền)_
