---
name: dym-nuwa-skill-helper-scripts-cli
description: "Bốn script phụ trợ chạy trong terminal. Vì sao dùng: đây là phần duy nhất của repo chạy được ngoài chat — tải/làm sạch phụ đề để nạp tư liệu gốc, tổng hợp bảng khảo cứu cho chốt 1.5, và tự chấm 6 tiêu chí Phase 4."
disable-model-invocation: true
---

# Skill: dym-nuwa-skill-helper-scripts-cli — Bốn script phụ trợ chạy trong terminal

**Vì sao dùng**: đây là phần duy nhất của repo chạy được ngoài chat — tải/làm sạch phụ đề để nạp tư liệu gốc, tổng hợp bảng khảo cứu cho chốt 1.5, và tự chấm 6 tiêu chí Phase 4.
**Sinh ra cái gì**: file transcript sạch, bảng tóm tắt khảo cứu, báo cáo pass/fail có mã thoát dùng được trong CI.

> ⚠️ Toàn bộ file này là lệnh **SHELL**. Lệnh chat nằm ở [02](02-distill-a-person.md), [03](03-diagnose-then-distill.md), [04](04-use-and-update-persona.md).

Ký hiệu `$NUWA` dưới đây = thư mục cài skill, ví dụ `~/.claude/skills/nuwa-skill`:

```bash
export NUWA=~/.claude/skills/nuwa-skill
```

Phụ thuộc: **Python 3** (dùng type hint `list[str]`/`tuple[bool, str]` → cần **3.9+**, chuẩn nhất là 3.10+), và **`yt-dlp`** cho script tải phụ đề. Không có `requirements.txt`; cả bốn script chỉ dùng thư viện chuẩn (`sys`, `re`, `pathlib`).

---

## `download_subtitles.sh` — tải phụ đề YouTube

```bash
bash $NUWA/scripts/download_subtitles.sh <YouTube_URL> [thư_mục_ra]
```

Thứ tự thử: phụ đề người làm tiếng Trung (`zh-Hans,zh-Hant,zh,zh-CN,zh-TW`) → phụ đề người làm tiếng Anh (`en,en-US,en-GB`) → phụ đề tự động (`zh-Hans,zh,en`). Định dạng SRT, `--skip-download` nên không tải video.

Mã thoát: `0` khi tìm được phụ đề, `1` khi không có URL hoặc không tìm thấy phụ đề nào (đã kiểm chứng: gọi không tham số → `exit 1` kèm dòng hướng dẫn dùng).

Kiểm tra `yt-dlp` trước:

```bash
command -v yt-dlp || brew install yt-dlp   # macOS; hoặc: pipx install yt-dlp
```

**Lỗi đã kiểm chứng trong nhánh 1**: nhánh phụ đề tiếng Trung dò file mới bằng `find ... -newer /tmp/.ytdlp_marker`, mà `/tmp/.ytdlp_marker` **không bao giờ được tạo ra** ở bất kỳ đâu trong repo. `find` lỗi, stderr bị nuốt, biến `FOUND` rỗng → script luôn rơi xuống nhánh 2 và chạy thêm một lượt `yt-dlp` tiếng Anh, rồi báo thành công ở nhánh 2 (nhánh này dùng `-mmin -1` nên vẫn thấy đúng file `.srt` tiếng Trung vừa tải). Hệ quả thực tế: **file vẫn đúng, chỉ tốn thêm một lần gọi mạng và dòng thông báo sai ngôn ngữ**. Kiểm lại bằng chính tên file:

```bash
ls -la <thư_mục_ra>/*.srt <thư_mục_ra>/*.vtt 2>/dev/null
```

## `srt_to_transcript.py` — làm sạch SRT/VTT thành văn bản đọc được

```bash
python3 $NUWA/scripts/srt_to_transcript.py input.srt [output.txt]
python3 $NUWA/scripts/srt_to_transcript.py input.vtt
```

Không truyền tham số thứ hai thì file ra là `<tên>_transcript.txt` cạnh file vào. Script bỏ số thứ tự, mốc thời gian, thẻ HTML, chú thích `align:`/`position:`, **khử dòng lặp liên tiếp** (bệnh kinh niên của phụ đề tự động), rồi gộp thành đoạn khi tích đủ >200 ký tự hoặc gặp dấu kết câu `。！？.!?`. VTT được nhận diện qua đuôi file hoặc header `WEBVTT`, cắt bỏ header và khối `NOTE` trước khi xử lý như SRT.

Chạy thật với một SRT 3 dòng có 1 dòng lặp và 1 thẻ `<i>`:

```
✅ 转换完成: demo_transcript.txt
   字数: 28  段落数: 3
```

Nội dung ra — thẻ `<i>` bị gỡ, dòng lặp bị khử:

```
Hello world.

This is a test
```

Mã thoát: `0` khi thành công; `1` khi thiếu tham số hoặc file vào không tồn tại (`❌ 文件不存在: ...`).

Kết quả nên bỏ vào `references/sources/transcripts/` của thư mục skill đang chắt lọc.

## `merge_research.py` — bảng tóm tắt cho chốt Phase 1.5

```bash
python3 $NUWA/scripts/merge_research.py <đường_dẫn_thư_mục_skill>
```

Quét `<skill>/references/research/01-writings.md … 06-timeline.md`, đếm URL duy nhất làm số nguồn, đếm dấu hiệu sơ cấp/thứ cấp, rút tiêu đề `##` làm phát hiện chính, và dò mâu thuẫn bằng các từ khoá 矛盾/相反/但实际上/然而…不同/争议.

Chạy thật trên `examples/steve-jobs-perspective`:

```
┌──────────────┬──────────┬──────────────────────────┐
│ Agent        │ 来源数量  │ 关键发现                  │
├──────────────┼──────────┼──────────────────────────┤
│ 著作          │ 24       │ 一、核心著作与一手文献, ... │
│ 对话          │ 27       │ 一、核心访谈索引, ...       │
│ 表达          │ 26       │ 一、Keynote演讲：语言特征... │
│ 他者          │ 29       │ 一、同事与合作者视角, ...   │
│ 决策          │ 0        │ 一、早期决策（1972-1976）...│
│ 时间线        │ 12       │ 第一章：早年（1955-1976）...│
├──────────────┼──────────┼──────────────────────────┤
│ 总来源数      │ 118      │ 一手占比: 134/244         │
│ 矛盾点        │ 5处      │ 著作: 争议。不妥协          │
│ 信息不足维度   │ 无       │ —                        │
└──────────────┴──────────┴──────────────────────────┘
```

Mã thoát: `0` khi in được bảng; `1` khi thiếu tham số hoặc **không có** `references/research/` (đã kiểm chứng trên `examples/munger-perspective`: `❌ 目录不存在: .../references/research`, thoát `1`).

Đọc bảng thế nào:
- **Cột 来源数量 bằng 0** không có nghĩa là chiều đó rỗng — nó đếm URL, nên file viết bằng trích dẫn không có link (như `05-decisions.md` của Jobs) sẽ ra 0. Mở file kiểm bằng mắt trước khi bắt chạy lại khảo cứu.
- **一手占比 là đếm từ khoá**, không phải phân loại thật (đếm số lần xuất hiện 一手/primary/本人/原文 so với 二手/转述/总结/评论). Con số `134/244` là chỉ dấu thô, không phải tỉ lệ nguồn chính xác.
- Cảnh báo tự động: tổng nguồn <10 → khuyên hạ kỳ vọng hoặc bổ sung; thiếu chiều → khuyên bổ sung hoặc ghi vào ranh giới trung thực.

## `quality_check.py` — tự chấm 6 tiêu chí Phase 4

```bash
python3 $NUWA/scripts/quality_check.py <đường_dẫn/SKILL.md>
```

Chạy thật trên `examples/steve-jobs-perspective/SKILL.md`:

```
质量检查: SKILL.md
==================================================
  心智模型数量       ✅ PASS  6个心智模型 ✅
  模型局限性        ✅ PASS  有局限性标注 ✅
  表达DNA辨识度     ✅ PASS  表达DNA特征: 21项 ✅
  诚实边界         ✅ PASS  诚实边界: 3条 ✅
  内在张力         ✅ PASS  内在张力: 2处 ✅
  一手来源占比       ✅ PASS  未标记来源类型（跳过检查）
==================================================
结果: 6/6 通过
🎉 全部通过，可以交付
```

**Mã thoát chỉ có hai giá trị: `0` khi đủ 6/6, `1` cho mọi trường hợp còn lại.** Đừng nhầm dòng chữ 「⚠️ 基本通过」 (5/6) là qua — đã kiểm chứng trên `examples/munger-perspective/SKILL.md`: in 「基本通过，建议修复不通过项后交付」 nhưng vẫn **thoát `1`**:

```
  诚实边界         ❌ FAIL  诚实边界: 0条 ❌ (应≥3条)
结果: 5/6 通过
⚠️ 基本通过，建议修复不通过项后交付
```

Vì vậy nếu gắn vào CI, `exit != 0` nghĩa là "chưa hoàn hảo", không phải "hỏng" — chọn ngưỡng có chủ đích chứ đừng mặc định chặn cứng (xem cổng CI mẫu trong [07](07-publish-and-get-listed.md)).

Một số điểm mù của bộ kiểm này, biết trước để đọc kết quả cho đúng:
- **诚实边界 đếm bằng regex**: chỉ nhận mục danh sách bắt đầu bằng `-` hoặc `*` nằm dưới heading chứa chữ 「诚实边界」. Viết ranh giới trung thực bằng đoạn văn hoặc bảng → đếm ra 0 và trượt, dù nội dung có thật (đây đúng là lý do `munger-perspective` trượt).
- **一手来源占比 tự bỏ qua** khi không tìm thấy section 来源/Source/Reference hoặc không có nhãn 一手/二手 — cả hai trường hợp đều báo PASS. Một PASS ở dòng này **không chứng minh** tỉ lệ nguồn sơ cấp >50%.
- **内在张力 đếm từ khoá** (张力/矛盾/tension/paradox/一方面…另一方面/既…又), không hiểu nghĩa. Dễ đạt bằng cách viết đủ chữ.

Nói cách khác: `quality_check.py` là cổng *hình thức*, không thay được thang chấm bảo chân ở [06](06-fidelity-scorecard.md).
