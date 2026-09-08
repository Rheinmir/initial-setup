---
name: dym-nuwa-skill-contributor-repo-itself
description: "Đóng góp vào chính repo nüwa (contributor track). Vì sao dùng: bạn muốn sửa công cụ, không phải dùng nó — vá script, sửa tài liệu, hoặc đề xuất thay đổi phương pháp luận."
disable-model-invocation: true
---

# Skill: dym-nuwa-skill-contributor-repo-itself — Đóng góp vào chính repo nüwa (contributor track)

**Vì sao dùng**: bạn muốn sửa *công cụ*, không phải dùng nó — vá script, sửa tài liệu, hoặc đề xuất thay đổi phương pháp luận.
**Sinh ra cái gì**: một PR đúng luật, hoặc một issue được người bảo trì tiếp nhận.

> Lệnh **SHELL** + thao tác GitHub. Track này độc lập với 01–07.

---

## Luật số một, đọc trước khi gõ phím

**`SKILL.md` là tài sản lõi và KHÔNG nhận PR từ bên ngoài.** Mọi dòng trong đó đã qua kiểm thực và tối ưu theo phiên bản của người bảo trì. Tìm ra lỗi hay ý cải tiến trong phương pháp luận → **mở issue**, ý được chấp nhận sẽ do người bảo trì tự viết vào và ghi công bạn trong commit (tiền lệ: PR #59 phát hiện lỗi vượt hạn `description`).

| Loại đóng góp | Đường đi |
|---|---|
| Lỗi/ý tưởng phương pháp luận | mở issue, **đừng PR thẳng vào `SKILL.md`** |
| Sửa script trong `scripts/` | PR thẳng, kèm bước tái hiện |
| Dịch README / sửa lỗi chính tả | PR thẳng |
| Persona skill của bạn | **không vào `examples/`** — xem [07](07-publish-and-get-listed.md) |
| Công cụ phái sinh / sưu tập / điều phối | PR thêm dòng vào `COMMUNITY.md` |

## Dựng môi trường

Không có bước build, không có trình quản lý gói, không có `requirements.txt`. Chỉ cần Python 3 và (cho một script) `yt-dlp`:

```bash
git clone https://github.com/alchaincyf/nuwa-skill && cd nuwa-skill
python3 --version                 # 3.9+ (code dùng type hint list[str])
command -v yt-dlp || brew install yt-dlp
```

## Chạy toàn bộ kiểm tra hiện có

Repo **không có test suite**. Vòng kiểm chứng thực tế là chạy script trên các ví dụ có sẵn:

```bash
# Cấu trúc research 01-06 (Jobs, Karpathy, Trump, MrBeast, PG, Ilya, Zhang Yiming, Zhang Xuefeng, Sun Yuchen)
python3 scripts/merge_research.py examples/steve-jobs-perspective   # kỳ vọng thoát 0, in bảng
# Cấu trúc references phẳng (Munger, Feynman, Taleb, Musk, Naval)
python3 scripts/merge_research.py examples/munger-perspective       # kỳ vọng thoát 1: 目录不存在

python3 scripts/quality_check.py examples/steve-jobs-perspective/SKILL.md   # kỳ vọng 6/6, thoát 0
python3 scripts/quality_check.py examples/munger-perspective/SKILL.md       # kỳ vọng 5/6, thoát 1

printf '1\n00:00:01,000 --> 00:00:03,000\n<i>Hello</i> world.\n\n2\n00:00:03,000 --> 00:00:05,000\nHello world.\n' > /tmp/demo.srt
python3 scripts/srt_to_transcript.py /tmp/demo.srt    # kỳ vọng gỡ thẻ <i> và khử dòng lặp
```

Quét toàn bộ 15 ví dụ để thấy script đứng ở đâu trước và sau khi bạn sửa:

```bash
for d in examples/*/; do
  printf '%-40s ' "$d"
  python3 scripts/quality_check.py "$d/SKILL.md" 2>/dev/null | grep '结果:' || echo "LỖI"
done
```

## Kiểm máy dành cho PR thu nhận cộng đồng

```bash
GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/community_check.py --check-repo <owner>/<repo>
```

Chế độ này chính là chế độ test tay mà chính file ghi trong docstring. Chế độ CI (không có `--check-repo`) cần các biến `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, `PR_NUMBER` và sẽ **đăng comment lên PR** — đừng chạy chế độ đó tại máy.

Lưu ý an toàn khi sửa workflow: nó dùng `pull_request_target` (chạy với quyền ghi trên repo gốc) và **cố ý chỉ checkout script trên `main`, không bao giờ checkout hay chạy code của PR**. Giữ nguyên tính chất đó; nếu bạn thêm bước checkout PR, đó là lỗ hổng chiếm quyền chứ không phải cải tiến.

## Checklist trước khi mở PR

- [ ] Không đụng `SKILL.md`
- [ ] Không có `.DS_Store` hay rác tương tự
- [ ] Một PR chỉ làm một việc (đừng gói nhiều nhân vật vào một PR)
- [ ] Mô tả PR nói rõ: làm gì, vì sao, kiểm chứng thế nào

## Việc đang bỏ ngỏ, nếu bạn muốn tìm chỗ để đóng góp

- **`download_subtitles.sh` có nhánh chết**: nhánh phụ đề tiếng Trung dò file mới bằng `find ... -newer /tmp/.ytdlp_marker` trong khi `/tmp/.ytdlp_marker` không được tạo ở bất kỳ đâu trong repo, nên nhánh đó không bao giờ báo thành công và luôn rơi xuống nhánh tiếng Anh (tốn thêm một lần gọi `yt-dlp`). Nhánh 2 và 3 dùng `-mmin -1` nên vẫn tìm ra file; sửa nhánh 1 cho đồng bộ là một PR gọn, đúng loại "sửa script" được nhận thẳng.
- **`merge_research.py` chỉ đọc được `references/research/01-06.md`**, trong khi 5/15 ví dụ chính chủ dùng file phẳng đặt tên tự do — hoặc mở rộng script, hoặc thống nhất cấu trúc ví dụ.
- **`quality_check.py` đếm 诚实边界 bằng regex mục danh sách**, nên ranh giới trung thực viết dạng đoạn văn hay bảng bị chấm 0 (chính `munger-perspective` dính lỗi này).
