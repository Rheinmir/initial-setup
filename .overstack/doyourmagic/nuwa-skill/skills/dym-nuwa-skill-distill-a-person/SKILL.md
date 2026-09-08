---
name: dym-nuwa-skill-distill-a-person
description: "Chắt lọc một nhân vật (đường trực tiếp, chat-only). Vì sao dùng: bạn đã biết muốn chắt lọc ai (Munger, Feynman, Paul Graham, Trương Nhất Minh…) và muốn ra một skill chạy được, có nguồn truy vết."
disable-model-invocation: true
---

# Skill: dym-nuwa-skill-distill-a-person — Chắt lọc một nhân vật (đường trực tiếp, chat-only)

**Vì sao dùng**: bạn đã biết muốn chắt lọc ai (Munger, Feynman, Paul Graham, Trương Nhất Minh…) và muốn ra một skill chạy được, có nguồn truy vết.
**Sinh ra cái gì**: một thư mục skill tự chứa `.claude/skills/<tên>-perspective/` gồm `SKILL.md`, `references/research/01-06.md`, `references/sources/`.

> ⚠️ **Toàn bộ file này là lệnh CHAT**, gõ vào cửa sổ hội thoại của agent, **không phải terminal**. Lệnh shell nằm ở [05-helper-scripts-cli.md](05-helper-scripts-cli.md).

---

## Câu lệnh khởi động

```
蒸馏一个保罗·格雷厄姆
造一个张小龙的视角Skill
distill Paul Graham
```

## Việc agent sẽ hỏi (Phase 0A) và cách trả lời để không bị kẹt

SKILL.md quy định 6 mục xác nhận. Mục quan trọng nhất là **档位 (mức chắt lọc)** — vì đây là tác vụ dài, nhiều agent, nhiều vòng tìm kiếm; tài liệu của repo nói thẳng rằng một lần chạy trên model cao cấp có thể tốn **hàng chục USD**:

| Mức | Quy mô khảo cứu | Dùng khi | Chi phí |
|---|---|---|---|
| 快速 (nhanh) | 3 chiều (著作 + 对话 + 表达), mỗi chiều tối đa 5 nguồn | thử hiệu quả / nhân vật ít tư liệu / ngân sách chặt | ≈ 1/3 mức chuẩn |
| 标准 (chuẩn, mặc định) | 6 chiều đầy đủ | đa số trường hợp | trung bình |
| 深度 (sâu) | 6 chiều + tải toàn bộ tư liệu gốc (sách/phụ đề/trường văn) | định open-source bản tinh phẩm | cao nhất |

Trả lời gọn để chạy thẳng mức chuẩn:

```
Nhân vật: Charlie Munger. Chân dung toàn diện. Dùng làm cố vấn tư duy.
Skill mới (chưa có sẵn). Không có tư liệu local. Mức 标准.
```

Muốn rẻ:

```
蒸馏芒格，走快速档，只要3个维度
```

**Có tư liệu gốc trong tay thì nói ngay** — sách PDF, transcript phỏng vấn, phụ đề video, export blog. Repo gọi đây là **本地语料模式**: agent đọc tư liệu bạn đưa trước, rồi chỉ tìm mạng cho các chiều còn thiếu. Chất lượng cao hơn hẳn so với tìm mạng thuần.

```
Tôi có 2 quyển PDF và 3 file transcript ở ~/tulieu/munger/, ưu tiên dùng chúng.
```

## Đường ống 6 pha, và 4 chốt dừng bạn phải duyệt

| Pha | Agent làm gì | Sản phẩm |
|---|---|---|
| 0.5 | Tạo cây thư mục skill **trước khi** khảo cứu | `references/research/`, `references/sources/{books,transcripts,articles}/` |
| 1 | Bung **6 subagent song song**, mỗi agent một chiều | `01-writings.md` … `06-timeline.md` |
| 🔴 1.5 | **CHỐT** — bảng tóm tắt chất lượng khảo cứu | bảng số nguồn / phát hiện chính / điểm mâu thuẫn |
| 2 | Chắt lọc khung tư duy (mô hình tâm trí 3–7, heuristic 5–10, DNA biểu đạt, tension, ranh giới trung thực) | ghi chú chắt lọc |
| 🔴 2.5 | **CHỐT** — xác nhận bản chắt lọc trước khi viết | tóm tắt N mô hình / N heuristic |
| 3 | Lắp thành `SKILL.md` theo `references/skill-template.md` | `SKILL.md` hoàn chỉnh |
| 🔴 4 | **CHỐT** — 3 bài kiểm tra bằng subagent độc lập | báo cáo pass/fail 6 tiêu chí |
| 🔴 5 | **CHỐT** — 2 agent tinh luyện song song | bản vá cải thiện |

Sáu chiều khảo cứu ở Phase 1:

| # | Chiều | Săn cái gì | File ra |
|---|---|---|---|
| 1 | 著作 | luận điểm lặp ≥3 lần (= niềm tin thật), thuật ngữ tự chế, danh sách sách gợi ý | `01-writings.md` |
| 2 | 对话 | cách trả lời khi bị truy, ví von ứng khẩu, khoảnh khắc đổi lập trường, câu từ chối trả lời | `02-conversations.md` |
| 3 | 表达 | từ/cú pháp tần suất cao, lập trường gây tranh cãi, kiểu hài | `03-expression-dna.md` |
| 4 | 他者 | mô thức người ngoài quan sát thấy, phê phán, so sánh với đồng nghiệp | `04-external-views.md` |
| 5 | 决策 | bối cảnh + logic quyết định lớn, hồi tưởng, chỗ ngôn–hành bất nhất | `05-decisions.md` |
| 6 | 时间线 | cột mốc, bước ngoặt tư tưởng, **động thái 12 tháng gần nhất** (chống lỗi thời) | `06-timeline.md` |

**Đừng bỏ qua chốt 1.5.** Tài liệu nói rõ: chất lượng khảo cứu quyết định trần chất lượng skill — chặn ở đây rẻ hơn nhiều so với làm lại ở Phase 4. Muốn bổ sung thì nói thẳng:

```
Chiều 05 决策 mỏng quá, chỉ 2 case. Chạy lại agent 5, tìm thêm các quyết định giai đoạn 1990-2000.
```

## Sáu tiêu chí Phase 4 (biết trước để không bất ngờ)

| Tiêu chí | Đạt | Trượt |
|---|---|---|
| Số mô hình tâm trí | 3–7, mỗi cái có bằng chứng nguồn | <3 hoặc >10 |
| Tính giới hạn của từng mô hình | ghi rõ điều kiện thất hiệu | chỉ ghi ưu điểm |
| Độ nhận diện DNA biểu đạt | đọc 100 chữ nhận ra là ai | giọng ChatGPT chung chung |
| Ranh giới trung thực | ≥3 giới hạn cụ thể | chỉ có "không thay thế được bản thân người đó" |
| Tension nội tại | ≥2 cặp mâu thuẫn | quan điểm nhất quán quá mức (= giả) |
| Tỉ lệ nguồn sơ cấp | >50% | chủ yếu là thuật lại thứ cấp |

Sáu tiêu chí này **có script tự kiểm** — xem [05-helper-scripts-cli.md](05-helper-scripts-cli.md#quality_checkpy). Trần lặp: vòng Phase 2→4 tối đa **2 lần**; sau 2 vòng vẫn còn mục trượt thì ghi nhận vào ranh giới trung thực và giao bản tốt nhất hiện có, không mài vô hạn.

## Cấu trúc thư mục sinh ra

```
.claude/skills/<person>-perspective/
├── SKILL.md
├── scripts/
└── references/
    ├── research/
    │   ├── 01-writings.md
    │   ├── 02-conversations.md
    │   ├── 03-expression-dna.md
    │   ├── 04-external-views.md
    │   ├── 05-decisions.md
    │   └── 06-timeline.md
    └── sources/{books,transcripts,articles}/
```

**Luật tự chứa**: mọi file khảo cứu phải nằm *bên trong* thư mục skill. Copy nguyên thư mục là chạy được ở máy khác — đây là điều kiện để phát hành mở.

## Cạm bẫy đã kiểm chứng

- **Nhân vật Trung Quốc**: Phase 0.5 tự chuyển chiến lược nguồn sang video gốc Bilibili / podcast 小宇宙 / báo Trung uy tín. Danh sách đen nguồn luôn gồm **知乎, 微信公众号, 百度百科** — cả ba bị loại ở mọi chế độ.
- **Frontmatter description của skill sinh ra phải < ~300 chữ**, trần cứng của skill-loader là 1024 ký tự. Nhồi từ khoá đuôi dài sẽ báo lỗi vượt hạn, đốt token mỗi session và làm tăng kích hoạt nhầm.
- **Ví dụ trong `examples/` không đồng nhất về cấu trúc**: Jobs/Karpathy/Trump/MrBeast dùng `references/research/01-06.md`; còn Munger/Feynman/Taleb/Musk/Naval dùng file phẳng đặt tên tự do trong `references/`. `merge_research.py` **chỉ chạy được với cấu trúc 01-06** (đã kiểm chứng: chạy trên `munger-perspective` báo `❌ 目录不存在` và thoát 1).
