---
type: draft
title: 290726-overstack-source-map
status: proposed
tags: [docs-site-macos, orca-onboard, output-report]
timestamp: 2026-07-29
---

# 290726-overstack-source-map

**Status:** proposed

## What

Sinh trang HTML self-contained mô tả mã nguồn repo overstack — `llmwiki/html/290726-overstack-source-map.html` — dựng bằng script python đọc thẳng knowledge graph, domain graph và `policy.yaml`, theo design system `/docs-site-macos` (liquid glass light-blue, sidebar-only nav, R11).

Trang này bổ sung cho `onboarding-setup.html` sinh trước đó: bản kia là guided tour 13 bước để đi tuần tự, bản này là **bản đồ tra cứu** — 15 tầng file, 18 luật đầy đủ, 7 miền với 124 bước có `file:line`, bảng file nóng và phụ thuộc.

## Output

- `llmwiki/html/290726-overstack-source-map.html` — 138,7 KB, 7 section, self-contained (0 request ngoài)
- `.orca-onboard/tmp/build_source_map.py` — generator tất định, chạy lại là trang cập nhật theo đĩa

Nội dung 7 section: Tổng quan (thống kê + mind map collapsible) · Kiến trúc 5 lớp (sơ đồ SVG kéo-thả) · Bản đồ 15 tầng (master-detail, liệt kê file thật kèm churn) · 18 luật đang gác (bảng đầy đủ từ `policy.yaml` + sơ đồ luồng chặn) · 7 miền · 26 luồng · 124 bước (master-detail, mỗi bước một `file:line`) · File nóng và lịch sử git · Quy ước và cạm bẫy.

## Files
| File | Action |
|------|--------|
| `llmwiki/html/290726-overstack-source-map.html` | created |
| `.orca-onboard/tmp/build_source_map.py` | created |
| `llmwiki/wiki/index.md` | modified |
| `llmwiki/wiki/log.md` | modified |

## Kiểm chứng đã chạy

Trang được mở thật trong Chrome (`http://localhost:8766/...`) và soi từng phần, không chỉ kiểm bằng grep:

| Hạng mục | Kết quả |
|---|---|
| Console lỗi | không có |
| Request ngoài | không có — kiểm bằng regex `src`/`href` trỏ `http(s)://` |
| Mind map bezier | vẽ đúng, nhánh đóng mặc định, click xổ được |
| Sơ đồ kéo-thả | node kéo được, connector tự đi theo |
| Master-detail | đổi pane tại chỗ, `aria-selected` chuyển đúng |
| Bảng 18 luật | 18 dòng, `statement` và `validator` khớp `policy.yaml` |
| Toggle sáng/tối | đổi hai chiều, lưu `localStorage` |

## Một bug thật đã phát hiện và sửa

Bản sinh đầu tiên có lỗi **rò CSS dark sang light mode**: hàm `dark_css()` dán prefix `html[data-theme=dark]` vào *selector đầu tiên* của một danh sách phẩy, nên `html[data-theme=dark] .hero .meta span, .steps li {…}` khiến `.steps li` (không prefix) ăn nền tối `rgba(30,38,54,.6)` ở **cả light mode** — 124 khối bước trong section 5 hiện ra xám đen. Phát hiện được vì mở trang lên xem, không phải vì đọc code.

Bản vá đầu tiên cũng sai và phải sửa tiếp: nối prefix bằng cách nhìn ký tự đầu (`.` thì dán liền) tạo ra `html[data-theme=dark].card` — nghĩa là `<html class="card">`, sai hoàn toàn; đồng thời `split(',')` xé nát selector `rect[fill='rgba(255,255,255,.7)']` vì dấu phẩy nằm trong `rgba()`.

Cách sửa cuối: **selector lưu dưới dạng list** thay vì chuỗi phẩy, prefix dán vào từng phần tử và luôn nối bằng khoảng trắng; selector SVG đổi từ match thuộc tính `fill` sang class `rect.nbox`. Bài học: khi phải emit một danh sách rule hai lần cho hai theme, đừng ghép chuỗi selector — giữ cấu trúc dữ liệu.

## Notes

- Invoked via: `/docs-site-macos` (được gọi từ trong phiên `/orca-onboard`)
- Mọi con số trên trang đọc từ `.understand-anything/knowledge-graph.json`, `.orca-onboard/intermediate/domain-graph.json`, `harness/policy.yaml` — không có số viết tay
- `llmwiki/html/*.html` bị gitignore; cần `git add -f` nếu muốn commit trang này
- Auto-host: cổng 8765 đang phục vụ thư mục khác nên trang chạy ở **8766** (`http://localhost:8766/llmwiki/html/290726-overstack-source-map.html`); không đụng server cũ của user
- Trang dài (~30k px). Vì design system bắt `scroll-behavior:smooth`, bấm nav nhảy giữa hai section xa nhau mất vài giây cuộn — chấp nhận được, nhưng nếu thấy khó chịu thì cân nhắc `scroll-behavior:auto` cho riêng trang tra cứu dài

## Origin
- **Draft:** `wiki/sources/draft/290726-overstack-source-map.md`
- **Nguồn dữ liệu:** knowledge-graph.json + domain-graph.json + policy.yaml tại commit `9032ae4`
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
