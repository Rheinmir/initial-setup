---
type: issue
title: 3 gap lệnh của pipeline /br khi clone-ngược (G1 ingest-repo · G2 reverse BR · G3 modularize)
status: proposed
tags: [issue, br, gap, self-improve, clone, memos]
timestamp: 2026-07-12
---

# 120726-pipeline-gaps-raised
**Type:** issue (raised) · **Status:** proposed · để dev khác pull qua /fdk

## Bối cảnh
Pipeline `/br` thiết kế build-XUÔI (docs → BR → frames → code). Khi thử clone-NGƯỢC một repo có sẵn (Memos, xem `120726-clone-memos-flow`), lộ 3 chỗ KHÔNG có lệnh tương ứng. Đây là các issue đã raise, CHƯA implement.

## G1 — `/br ingest-repo <url>`
**Thiếu:** không có lệnh kéo một Git repo làm đầu vào pipeline (hiện `git clone` tay).
**Đề xuất:** shallow clone → đặt AGENTS.md/README/manifest vào `raw/` → dựng project workspace. Mỏng, chủ yếu script.
**Ưu tiên:** trung bình (tiện, không chặn).

## G2 — `/br reverse` (chưng BR NGƯỢC từ code) — ƯU TIÊN CAO NHẤT
**Thiếu:** `/br interview` chỉ đi xuôi từ tài liệu; không có đường code có sẵn → BR clause_id.
**Đề xuất:** nhận output `/onboard-codebase` → sinh `BR.md` (mỗi feature = 1 clause), đánh dấu clause "quan sát-từ-code" khác "yêu cầu mới". Tái dùng `frame-template` + `frame-lint`, KHÔNG tạo schema mới.
**Ưu tiên:** CAO — mở khoá mọi "clone/onboard → pipeline".

## G3 — `/modularize` (đóng gói module + microservice-by-path)
**Thiếu:** không có skill wrap app thành (a) standalone runnable, (b) microservice mount-by-path.
**Đề xuất:** sinh Dockerfile/compose + reverse-proxy snippet + base-path patch + health-check; 2 target. Đụng deploy → nặng nhất, làm sau.
**Ưu tiên:** thấp (làm khi tới bước đóng gói).

## Thứ tự đề xuất
raise (xong) → G2 → G1 → G3.

## Origin
Raise từ phiên 2026-07-12 khi thiết kế luồng clone Memos. Cặp: `120726-clone-memos-flow.md`.
