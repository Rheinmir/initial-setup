---
type: plan
issue: 030726-foundation-section
title: "PLAN — Foundation section phổ quát cho mọi wiki (GH#6)"
status: draft
timestamp: 2026-07-04
tags: [plan, foundation, overstack, wiki-template]
---

# Plan triển khai: Foundation section (issue `030726-foundation-section`, GH#6)

## 1. Bối cảnh ngắn

Mọi wiki dựng bằng overstack (kể cả `overstack.html`) thiếu mục **Foundation** trả lời 3 câu gốc: *dự án giải quyết bài toán gì · vì sao nó tồn tại · vì sao chọn các công nghệ này*. Tri-thức "vì sao" hiện rải rác trong ADR/commit/report rời (ví dụ `llmwiki/html/030726-yaml-vs-python.html`). Giải pháp theo đúng pattern đã có của repo: **nguồn khai báo YAML → generator derive → medic probe gác drift** (giống bộ ba `harness/mechanisms.yaml` → `build-overstack-docs.py` → `medic p_narrative`, council-025 / ADR-001).

## 2. Khảo sát thực tế (đã xác minh trong code)

- `fdk/tools/build-overstack-docs.py` — hàm `load_mechanisms(root)` (dòng ~296) đọc `harness/mechanisms.yaml` bằng `yaml.safe_load`, fail-open (trả `[]` + warning stderr). Hàm `sections(root)` (dòng ~310) trả list section dạng tuple `(slug, nav_title, kicker, h1, [html_blocks])` — tab mới chỉ là một `S.append((...))`. Sentinel link nội bộ dùng `@slug` (dòng ~904).
- `harness/mechanisms.yaml` — mẫu manifest chuẩn: header giải thích "vì sao file tồn tại", `version: 1`, list item có `id/name/kind/desc/live_probe`. Schema `foundation.yaml` bắt chước phong cách này.
- `fdk/tools/medic.py` — probe `p_narrative()` (dòng 100-138): parse manifest bằng **regex thuần stdlib** (không import yaml), check (a) live_probe tồn tại, (b) name xuất hiện trong `overstack.html`, fail-open thành `skip` nếu không parse được. Đăng ký trong list `PROBES` (dòng ~205) dạng `(name, tags, fn)`. Probe foundation mới theo đúng khuôn này.
- `harness/scripts/harness-doctor.py` — có các `probe_*` (install-time, advisory); probe nội dung foundation đặt ở **medic** là đúng tầng hơn (giống narrative), doctor chỉ cần check file tồn tại (optional).
- Seed/bootstrap: `harness/scripts/install-harness.sh` copy các file `harness/*.yaml` từ template (dòng 177-230, pattern `[ -f ... ] || cp` = không đè file đã có); `harness/poc-vendor-neutral/install.sh` (dòng ~178) đã có tiền lệ seed template từ `harness/templates/` (problem-tree-template.html) — travel-kit pattern của `[[020726-orca-issue-ledger-travel]]`.
- `harness/templates/` hiện chỉ có `problem-tree-template.html` — chỗ đặt template seed mới.

## 3. Danh sách file tạo / sửa

| # | File | Hành động |
|---|------|-----------|
| 1 | `harness/foundation.yaml` | **TẠO** — nguồn chân lý Foundation của CHÍNH repo overstack (điền thật: YAML, Python ít nhất) |
| 2 | `harness/templates/foundation-template.yaml` | **TẠO** — bản seed rỗng-có-placeholder cho dự án mới |
| 3 | `fdk/tools/build-overstack-docs.py` | **SỬA** — thêm `load_foundation(root)` + tab/section "Nền tảng" trong `sections()` |
| 4 | `fdk/tools/medic.py` | **SỬA** — thêm `p_foundation()` + đăng ký vào `PROBES` |
| 5 | `harness/scripts/install-harness.sh` | **SỬA** — seed `foundation.yaml` nếu chưa có (`[ -f ... ] || cp` từ template) |
| 6 | `harness/poc-vendor-neutral/install.sh` | **SỬA** — seed tương tự qua curl `$REPO_RAW/harness/templates/foundation-template.yaml` (cạnh khối problem-tree hiện có) |
| 7 | `llmwiki/html/overstack.html` | **REGEN** — chạy lại generator (không sửa tay) |
| 8 | `llmwiki/wiki/index.md`, `llmwiki/wiki/log.md` | **SỬA** — cập nhật index + log theo rule wiki |

Tùy chọn (nếu còn budget): `harness/scripts/harness-doctor.py` thêm probe advisory "foundation.yaml tồn tại".

## 4. Schema `foundation.yaml` đề xuất

```yaml
# foundation.yaml — NGUỒN CHÂN LÝ mục "Nền tảng" của wiki/overstack.html.
# overstack.html DERIVE từ file này (không chép tay); medic probe `foundation`
# cắn khi khai một mục mà trang vắng (giống narrative-as-data, ADR-001).
version: 1

foundation:
  problem: >-            # câu 1 — dự án giải quyết bài toán gì
    ...
  why-exists: >-         # câu 2 — vì sao nó tồn tại (không dùng cái có sẵn?)
    ...
  tech-choices:          # câu 3 — vì sao chọn các công nghệ này
    - tech: "YAML"
      role: "policy-as-data: rule/mechanism/persona khai báo, tách khỏi engine"
      why: "diff-được, review-được, agent sửa data không sửa code enforcement"
      alternatives-rejected:
        - alt: "hardcode list trong Python"
          reason: "chép tay đóng băng → narrative drift (council-025)"
      evidence-link: ["[[ADR-001]]", "llmwiki/html/council/council-report-026-seed42.html"]
    - tech: "Python (stdlib)"
      role: "engine tất định: validator/generator/probe"
      why: "..."
      alternatives-rejected: [...]
      evidence-link: ["llmwiki/html/030726-yaml-vs-python.html"]
```

Ghi chú schema: `evidence-link` chấp nhận cả `[[wikilink]]` lẫn path repo-relative; probe chỉ verify path (wikilink để R-validator wiki hiện có lo). Template seed giữ nguyên khung, giá trị là placeholder `"TODO: ..."` — probe **skip khi toàn placeholder** để dự án mới cài không bị đỏ ngay (fail-open giống `p_narrative`).

## 5. Các bước triển khai (thứ tự)

1. **Tạo `harness/foundation.yaml`** — điền nội dung thật cho repo này: `problem`, `why-exists` (distill từ tab "overstack là gì" + ADR-001/004), tối thiểu 2 `tech-choices` (YAML → ADR-001 + council-026; Python stdlib → report yaml-vs-python). Đây là bước nội dung nặng nhất, làm trước để generator có data thật.
2. **Sửa generator** `fdk/tools/build-overstack-docs.py`:
   - Thêm `load_foundation(root)` clone khuôn `load_mechanisms` (yaml.safe_load, fail-open trả `{}` + stderr warning).
   - Trong `sections()`: `S.append(("foundation", "Nền tảng", "0X · Nền tảng", "Nền tảng — vì sao overstack tồn tại", [...]))` — vị trí ngay sau tab "01 · Tổng quan" (người mới đọc đầu tiên). Render: 2 khối prose (problem, why-exists) + bảng tech-choices (tech / role / why / alternatives-rejected / evidence). Khi manifest trống/placeholder → render notice "foundation.yaml chưa điền" (giống pattern dòng 755 với mechanisms trống), KHÔNG crash.
   - Escape mọi giá trị qua `esc()`; evidence path render thành `<code>`, wikilink render nguyên văn.
3. **Regen** `python3 fdk/tools/build-overstack-docs.py` → kiểm tab mới trong `llmwiki/html/overstack.html`; xác nhận `--check` (docs probe) xanh.
4. **Thêm medic probe** `p_foundation()` trong `fdk/tools/medic.py`, clone khuôn `p_narrative`:
   - Không có `harness/foundation.yaml` hoặc `overstack.html` → `skip` (dự án chưa opt-in).
   - Parse bằng **regex stdlib** (`tech:`, path trong `evidence-link`): (a) evidence path khai mà không tồn tại → `fail` "manifest nói dối"; (b) `tech` name khai mà vắng trong `overstack.html` → `fail` "FOUNDATION DRIFT" + fix-hint regen; (c) toàn giá trị `TODO` → `warn` "foundation chưa điền".
   - Đăng ký: `("foundation", ["foundation", "docs", "drift"], p_foundation)` vào `PROBES`.
5. **Sync mirror medic** — kiểm tra xem `fdk/tools/medic.py` có bản deploy downstream/mirror không (skill `medic`, `llmwiki/skills/utils/medic.md` mô tả); nếu install-harness copy medic vào dự án, bản copy tự mang probe mới — chỉ cần bump `harness/version.json` nếu quy trình yêu cầu.
6. **Seed bootstrap**:
   - Tạo `harness/templates/foundation-template.yaml`.
   - `install-harness.sh`: thêm dòng `[ -f "$ROOT/harness/foundation.yaml" ] || cp "$SRC/harness/templates/foundation-template.yaml" "$ROOT/harness/foundation.yaml"` cạnh khối copy các yaml khác (~dòng 177-230) — **không đè** foundation đã điền của dự án cũ.
   - `poc-vendor-neutral/install.sh`: khối curl tương tự cạnh problem-tree (~dòng 178), fail-soft.
7. **Wiki hygiene**: cập nhật `wiki/index.md`, append `wiki/log.md`, thêm `## Origin` cho mọi trang wiki mới; chuyển issue ledger `status: open → done` khi merge; regen `fdk/CAPABILITIES.md` nếu chạm skill/tool (`python3 fdk/tools/build-capabilities.py`).
8. **Verify tổng**: `python3 fdk/tools/medic.py` xanh toàn bộ; test mutation (bước 8 checklist dưới).

## 6. Map tới 4 tiêu chí HOÀN THÀNH

| Tiêu chí | Được thoả bởi |
|---|---|
| 1. overstack.html có mục Foundation derive từ nguồn | Bước 1-3 (foundation.yaml + tab generator + regen; sửa nguồn → regen → trang đổi) |
| 2. Template seed khi bootstrap | Bước 6 (foundation-template.yaml + install-harness.sh + poc install.sh) |
| 3. ≥2 tech-choice có why + alternatives-rejected + evidence | Bước 1 (YAML, Python với ADR-001/council-026/report yaml-vs-python) |
| 4. medic probe cắn khi khai mà trang vắng | Bước 4-5 (`p_foundation`, khuôn narrative-as-data) |

## 7. Rủi ro / lưu ý

- **Derive-not-copy (ADR-001, council-025)**: tuyệt đối không viết nội dung Foundation tay vào HTML hay hardcode dict trong generator — mọi chữ đến từ `foundation.yaml`. Probe (b) chính là chốt chặn.
- **Travel-kit / ADR-004**: Foundation phải travel qua trụ được distribute (harness/ + templates/), KHÔNG qua context auto-bơm hay memory máy-local. Mọi phiên dự án downstream đọc được foundation của CHÍNH nó mà không cần /fdk.
- **medic phải stdlib-only**: `p_foundation` parse regex, không `import yaml` — giữ hợp đồng hiện có của medic.py (comment tại p_narrative).
- **Fail-open cho dự án mới**: template placeholder không được làm medic đỏ ngay sau bootstrap → probe trả `warn`/`skip` khi toàn TODO.
- **Không đè khi update**: install-harness chạy lại trên dự án cũ không được ghi đè foundation.yaml đã điền (pattern `[ -f ] || cp` như policy.yaml harness-local).
- **Không thuộc phạm vi** (theo ledger): không viết lại ADR, không đụng validator enforcement (R1-R15), không làm cho dự án ngoài — chỉ template + overstack repo này.
- **Đụng file 92KB**: build-overstack-docs.py lớn — surgical change, chỉ thêm 1 hàm load + 1 S.append, không refactor lân cận.
- Kicker số thứ tự tab ("0X ·") có thể dồn số các tab sau — kiểm nav sau regen.

## 8. Checklist test

- [ ] `python3 fdk/tools/build-overstack-docs.py` chạy sạch; tab "Nền tảng" xuất hiện, đủ 3 câu + bảng tech-choices có evidence link.
- [ ] Xoá tạm `harness/foundation.yaml` → generator vẫn chạy (notice trống, không crash); khôi phục.
- [ ] `python3 fdk/tools/medic.py foundation` → ok.
- [ ] **Mutation drift**: thêm 1 tech-choice mới vào foundation.yaml, KHÔNG regen → probe `fail` "FOUNDATION DRIFT"; regen → ok.
- [ ] **Mutation nói dối**: khai `evidence-link` path không tồn tại → probe `fail`.
- [ ] Template placeholder: copy foundation-template.yaml vào repo tạm → probe `warn`/`skip`, không `fail`.
- [ ] `bash harness/scripts/install-harness.sh` trên dir tạm: foundation.yaml được seed; chạy lần 2 không đè.
- [ ] `python3 fdk/tools/medic.py` (full) xanh; docs `--check` xanh; selftest hiện có không vỡ.

## Origin

Plan viết 2026-07-04 cho issue ledger `[[030726-foundation-section]]` (GH#6), sau khảo sát trực tiếp `fdk/tools/build-overstack-docs.py`, `harness/mechanisms.yaml`, `fdk/tools/medic.py` (p_narrative), `harness/scripts/install-harness.sh`, `harness/poc-vendor-neutral/install.sh`, `harness/templates/`.
