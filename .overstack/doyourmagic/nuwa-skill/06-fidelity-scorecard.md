# 06 — Chấm bảo chân (Fidelity Scorecard) cho skill vừa làm ra

**Vì sao dùng**: đây là "kiểm định xuất xưởng" — thứ duy nhất trong repo có thể nói skill của bạn *giống người thật đến đâu*, và là điều kiện cứng để được thu vào `COMMUNITY.md`.
**Sinh ra cái gì**: một file `FIDELITY.md` ở gốc thư mục skill, có bảng điểm 5 chiều, lý do từng câu, ngày chấm và tên model đã dùng.

> Chủ yếu là lệnh CHAT (điều phối agent). Phần commit/PR nằm ở [07](07-publish-and-get-listed.md).

---

## Vì sao không để một agent tự chấm mình

`references/fidelity-scorecard.md` mở đầu bằng dẫn chứng từ bài SkillLens (arXiv 2605.23899): LLM tự chấm chất lượng skill của chính nó chỉ đúng **46.4%** — gần bằng đoán mò. Luật sắt của thang chấm vì thế là **agent trả bài và agent chấm phải tách rời**.

## Quy trình bốn bước

```
Chạy thang chấm bảo chân cho .claude/skills/munger-perspective/ theo
references/fidelity-scorecard.md: ra đề, spawn agent trả bài (chỉ đọc
file trong thư mục skill, cấm truy mạng), rồi spawn agent chấm độc lập.
Ghi kết quả vào FIDELITY.md.
```

1. **Ra đề** — 3 câu lập trường đã biết (chọn chủ đề nhân vật công khai phát biểu nhiều lần) + 1 câu ngoài phạm vi + 1 câu lấy mẫu văn phong.
2. **Agent trả bài** — chỉ đọc file trong thư mục skill, nhập vai theo skill, **cấm truy mạng**, và không biết mình đang bị đo chiều nào.
3. **Agent chấm** — agent độc lập, nhận bài làm + rubric + đường dẫn skill, đối chiếu lập trường công khai thật của nhân vật, chấm từng chiều. Agent chấm không tham gia trả bài.
4. **Xuất `FIDELITY.md`** — bảng điểm, lý do phán định từng câu, ngày chấm, model dùng để trả bài/chấm.

## Năm chiều, tổng 100

| # | Chiều | Điểm | Đo cái gì | Đo bằng cách nào |
|---|---|---|---|---|
| 1 | 立场一致性 (nhất quán lập trường) | 30 | trả lời có cùng hướng với phát ngôn công khai không | 3 câu, mỗi câu 10đ: đúng cả hướng lẫn chi tiết = 10; đúng hướng lệch chi tiết = 6; lệch lập trường = 0 |
| 2 | 风格辨识度 (nhận diện văn phong) | 20 | che tên đi có nhận ra là ai không | agent chấm đọc mù: cú pháp, dùng từ, cách ví von có vân tay riêng hay là giọng AI chung |
| 3 | 边缘诚实度 (trung thực ở rìa) | 20 | gặp câu nhân vật chưa từng bàn thì ghi nhận suy luận hay bịa chắc nịch | 1 câu ngoài phạm vi: tuyên bố rõ "đây là suy luận từ khung" và giữ mức bất định = trọn điểm; nguỵ trang thành quan điểm bản thân người đó = 0 |
| 4 | 来源透明度 (minh bạch nguồn) | 15 | bản thảo khảo cứu có truy vết được không | kiểm tĩnh file skill: có section nguồn, tỉ lệ sơ cấp >50%, câu trích then chốt có xuất xứ |
| 5 | 结构完整度 (đầy đủ cấu trúc) | 15 | có đủ bộ khung chống trôi vai và vận hành trung thực không | kiểm tĩnh: 3–7 mô hình tâm trí, ≥3 ranh giới trung thực, ≥2 cặp tension, có danh sách phản mô thức, luật nhập vai có ràng buộc chống trôi |

Chiều 4 và 5 là kiểm tĩnh — trùng phần lớn với `quality_check.py` ở [05](05-helper-scripts-cli.md), nên chạy script trước cho rẻ, rồi mới đốt token cho chiều 1–3.

## Thang hạng

| Hạng | Điểm | Nghĩa |
|---|---|---|
| A | ≥85 | tinh phẩm ngay từ xuất xưởng, yên tâm dùng làm cố vấn tư duy |
| B | 70–84 | đạt, có vài chiều yếu nhưng đã ghi nhận |
| C | 55–69 | dùng được nhưng phải cẩn thận, bắt buộc đọc ranh giới trung thực |
| D | <55 | không nên dùng, cần nấu lại |

**≥B (70) là ngưỡng vào `COMMUNITY.md`.** 15 skill chính chủ đều hạng A.

## Chống gian lận (ghi thẳng trong rubric)

- Agent trả bài không biết mình bị đo chiều nào.
- Agent chấm không tham gia trả bài, chỉ đối chiếu sự thật công khai.
- Kết luận quan trọng nên cho **2 agent chấm chạy độc lập**; lệch >10 điểm thì người phải xem lại.

## Mẫu `FIDELITY.md`

```markdown
# 保真度评分卡

**总分：NN/100 · 等级X** | 测试日期：YYYY-MM-DD | 答题/评分：独立双agent

| 维度 | 得分 | 判定摘要 |
|------|------|---------|
| 立场一致性 | NN/30 | ... |
| 风格辨识度 | NN/20 | ... |
| 边缘诚实度 | NN/20 | ... |
| 来源透明度 | NN/15 | ... |
| 结构完整度 | NN/15 | ... |

## 测试记录
...
```

## Cạm bẫy đã kiểm chứng

- **Không được để trống hay ước lượng các trường then chốt.** Máy kiểm của repo (`.github/scripts/community_check.py`) quét *dòng trường* (测试日期/总分/各维评分…) và **loại thẳng** nếu gặp 预估/待跑/待测/待补/待定/待填/占位/未实测/未测试/自评分 hoặc ngày mẫu `YYYY-MM-DD`. Tiền lệ: PR #70 bị chặn vì "điền sẵn mẫu rồi thêm một dòng tổng điểm" không được tính là đã chạy test.
- Máy kiểm **chỉ quét dòng trường**, không quét toàn văn — nên viết "chiều X chưa thực đo" trong phần ranh giới trung thực là an toàn, không bị đánh nhầm thành gian lận.
- Thang chấm là **báo cáo đối ngoại** (ai cũng chạy lại được để kiểm chứng), khác với Phase 4 là **tự kiểm nội bộ** trong lúc sản xuất. Đừng lấy Phase 4 pass thay cho `FIDELITY.md`.
