# 03 — Xin báo cáo nguyên trang (R01–R12)

> **Toàn bộ file này là câu chat, KHÔNG phải lệnh terminal.**

**Vì sao dùng:** khi bạn cần một trang HTML hoàn chỉnh có tiêu đề, dẫn nhập, KPI, nhiều ô biểu đồ và nguồn — không phải vài cái hình rời.
**Sinh ra cái gì:** một file `.html` đơn, dựng từ một trong 12 bộ template, mỗi bộ có sẵn bản `.zh` và `.en`.

## Bắt buộc: phải gọi tên chế độ

Chế độ mặc định là **biểu đồ**. `SKILL.md` §0.1 nói thẳng: nói "phân tích giúp tôi" hay đưa dữ liệu rất giàu **cũng không** được nâng cấp thành báo cáo. Từ khoá bật báo cáo: **báo cáo / annual report / monthly report / white paper / one-pager khảo sát / poster / brief / notebook / dashboard report**.

```text
Dùng lieflat-charts sinh một BÁO CÁO HTML nguyên trang từ dữ liệu này.

<dữ liệu>

Loại: báo cáo vận hành tháng.
Ngôn ngữ: tiếng Anh.
Người đọc: ban lãnh đạo, đọc trong 5 phút.
```

Còn mơ hồ, skill sẽ cố tình trả biểu đồ chứ không đoán.

## Chọn bộ nào (report-catalog.md)

Tên template là **tính cách bố cục**, không phải giới hạn ngành. "Travel Notebook" chở được dữ liệu thể thao; "Monthly Ops" chở được báo cáo tài chính.

| # | Tên | Bề rộng cột chữ | Mật độ | Hệ màu | Phụ thuộc |
|---|---|---:|---|---|---|
| R01 | Survey One-Pager | 1080 | 3 hình, vừa | Porcelain | font online |
| R02 | Annual Milestones | 980 | 3 hình, vừa | Palm | font online |
| R03 | Year in Data | 1080 | 4 hình, cao | Wire | font online |
| R04 | Monthly Ops | 1080 | 4 hình, cao | Porcelain | font online |
| R05 | Impact Story | 760 | 2 hình, thấp | Mono | font online |
| R06 | Eight-Year Almanac | 980 | 4 hình, rất cao | Palm | font online |
| R07 | Survey Collage Poster | 980 | 5 hình, rất cao | Palm | font online |
| R08 | Population One-Pager | 880 | 2 hình, thấp | Wire | font online |
| R09 | Data Story Dashboard | 1080 | 4 hình + KPI | Porcelain | font online |
| R10 | Travel Notebook | 980 | 4 hình + bảng | Palm | font online |
| R11 | Research Brief Card | **600×1000 cố định** | 2 hình | Mono | **Chart.js + ECharts CDN** |
| R12 | Weekly Glance | 1080 | 4 hình, cao | Palm | **Chart.js + ECharts CDN** |

Gợi nhớ nhanh: khảo sát → R01/R07/R08/R11 · dashboard vận hành → R04/R09/R12 · tài chính → R02/R03/R04/R09/R11/R12 · hồi cứu sản phẩm → R02/R05/R06/R12 · dữ liệu cá nhân → R03/R05/R06/R10/R12 · poster/social → R03/R07/R11.

**Cần chạy offline:** ưu tiên R01–R10 và bảo agent inline hoặc bỏ font online. R11–R12 phải inline thêm cả thư viện biểu đồ.
**R11 là khổ cố định 600×1000:** nội dung không vừa thì **đổi template**, tuyệt đối không thu nhỏ chữ hay cắt thông tin.

## Ràng buộc agent phải giữ (report-catalog.md §模板契约)

- Giữ nguyên bề rộng cột chữ, lưới chính, thứ tự chương mục, khoảng trắng lớn, hệ màu, quan hệ giữa các ô biểu đồ.
- **Cấm ghép hai bộ template.**
- **Cấm để sót dữ liệu demo, nguồn demo, kết luận demo, hay link Moxt** của template gốc.
- Trong một bản chỉ một ngôn ngữ — không trộn Trung/Anh/Việt.
- Mỗi ô biểu đồ vẫn phải chọn hình theo `catalog.md`; bố cục báo cáo không phải cớ để lách hợp đồng dữ liệu của biểu đồ.

## Câu chat bắt agent chứng minh đã chọn có cơ sở

```text
Trước khi sinh file: so sánh ít nhất 3 template báo cáo, ghi lý do loại từng cái,
rồi chốt đúng MỘT file templates/reports/report-NN.<lang>.html làm khung xuất phát.
```

## Nghiệm thu

1. Đúng ngôn ngữ, không trộn.
2. Bề rộng cột chữ không trôi so với template gốc (so bằng mắt với `templates/reports/index.html`).
3. Không còn chữ/số/nguồn của bản demo.
4. R11: nội dung vừa khổ, không tràn, không có thanh cuộn ngang.
5. Số biểu đồ trong trang đều có dữ liệu chống lưng — không có ô nào vẽ cho đầy.
