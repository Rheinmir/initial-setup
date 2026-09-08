# nüwa (女娲 · Skill造人术) — bộ workflow chạy được

Sinh ra từ một lượt khảo sát **chỉ đọc** repo `alchaincyf/nuwa-skill` (clone `--depth 1`, không sửa file nào trong repo đích). Đây **không phải package npm/pip**: repo không có manifest nào cả — entry point là `SKILL.md` ở gốc (YAML frontmatter `name: huashu-nuwa`), kèm `references/` (phương pháp luận agent đọc lúc chạy), `scripts/` (4 công cụ CLI thật) và `examples/` (15 skill hoàn chỉnh đã chắt lọc).

Điều nüwa làm: bạn đưa một cái tên (hoặc chỉ một nỗi bối rối), nó chạy khảo cứu 6 agent song song → chắt lọc khung tư duy → sinh ra một *persona skill* chạy được, có nguồn truy vết và ranh giới trung thực.

Bộ tài liệu này tách theo **đối tượng**, và trong track người dùng còn tách tiếp **lệnh chat** với **lệnh terminal** — trộn hai loại vào một file là cách nhanh nhất để ai đó dán lệnh chat vào shell.

| # | File | Mục đích | Track / Loại lệnh |
|---|---|---|---|
| 1 | [01-install.md](01-install.md) | Cài skill vào Claude Code / Codex / Cursor / OpenClaw; kiểm chứng đã nạp; hiểu repo thực chất là gì | Người dùng — cài đặt (shell) |
| 2 | [02-distill-a-person.md](02-distill-a-person.md) | Chắt lọc một nhân vật đã biết tên: ba mức chi phí, 6 pha, 4 chốt duyệt, 6 tiêu chí nghiệm thu | Người dùng — chat |
| 3 | [03-diagnose-then-distill.md](03-diagnose-then-distill.md) | Chưa biết chắt lọc ai: 10 chiều nhu cầu → 2–3 ứng viên; và 15 skill có sẵn để khỏi tốn tiền | Người dùng — chat |
| 4 | [04-use-and-update-persona.md](04-use-and-update-persona.md) | Gọi persona ra làm việc, luật nhập vai/thoát vai, Agentic Protocol, và cập nhật tăng dần | Người dùng — chat |
| 5 | [05-helper-scripts-cli.md](05-helper-scripts-cli.md) | Bốn script trong `scripts/`: cú pháp, output thật, mã thoát, điểm mù | Người dùng — shell |
| 6 | [06-fidelity-scorecard.md](06-fidelity-scorecard.md) | Chấm bảo chân 5 chiều/100 bằng hai agent độc lập, xuất `FIDELITY.md` | Người dùng — chat |
| 7 | [07-publish-and-get-listed.md](07-publish-and-get-listed.md) | Đóng gói repo riêng, cổng CI tối thiểu, chạy máy kiểm tại máy, PR vào `COMMUNITY.md` | Người dùng — shell + GitHub |
| 8 | [08-contributor-repo-itself.md](08-contributor-repo-itself.md) | Sửa chính nüwa: luật cấm PR vào `SKILL.md`, cách chạy kiểm, ba lỗi đang bỏ ngỏ | Người đóng góp — shell |

## Thứ tự chạy gợi ý

**Lần đầu dùng**: `01` → (`02` nếu đã biết muốn ai, `03` nếu chưa) → `04` để làm việc với thành phẩm. `05` xen vào giữa `02` khi cần nạp tư liệu gốc (phụ đề/transcript) hoặc tự chấm ở chốt Phase 4.

**Nếu định phát hành**: `06` (chấm bảo chân) → `07` (repo riêng + CI + PR vào chỉ mục). Đừng đảo thứ tự — `07` đòi một `FIDELITY.md` có điểm thật.

**Người đóng góp**: đọc thẳng `08`, không phụ thuộc `01`–`07`.

**Đường tắt đáng cân nhắc**: nếu nhân vật bạn cần đã nằm trong 15 skill chính chủ (Munger, Feynman, Naval, Taleb, Musk, Jobs, Karpathy, Ilya, MrBeast, Trump, Paul Graham, Trương Nhất Minh, Trương Tuyết Phong, Tôn Vũ Thần, X-mentor), cài thẳng bằng `npx skills add …` (danh sách đầy đủ trong `03`) — một lượt chắt lọc đầy đủ có thể tốn hàng chục USD, con số do chính repo cảnh báo.

## Bộ này được kiểm chứng ra sao, không phải chép lại README

Mỗi khẳng định đều đối chiếu mã nguồn hoặc chạy thật, không lấy từ văn xuôi README:

- **Không có manifest**: `ls package.json pyproject.toml Cargo.toml go.mod` → không file nào tồn tại; entry point xác định bằng YAML frontmatter đầu `SKILL.md`.
- **Cách cài, đường thư mục runtime**: mục 「安装」 của `README.md` (dòng 100–142), đối chiếu chéo với thư mục thật của Claude Code trên máy này.
- **Các pha, chốt duyệt, phân công 6 agent, ba mức chi phí, luật danh sách đen nguồn**: đọc trực tiếp `SKILL.md` (Phase 0A dòng 43–68, Phase 0B dòng 69–148, Phase 0.5 dòng 149–182, Phase 1 dòng 183–331, Phase 1.5 dòng 332–358, Phase 2 dòng 359–430, Phase 3 dòng 431–467, Phase 4 dòng 523–560, Phase 5 dòng 561–583).
- **Luật nhập vai, ranh giới trung thực, khung SKILL.md đích**: `references/skill-template.md`; **Agentic Protocol ba bước**: `SKILL.md` dòng 468–522.
- **Năm chiều chấm bảo chân, thang hạng, chống gian lận**: `references/fidelity-scorecard.md` (không lấy con số từ README).
- **Cú pháp và mã thoát của cả 4 script**: đọc lệnh `sys.exit(...)` / `exit N` trong mã, rồi **chạy thật** — `quality_check.py` trên `examples/steve-jobs-perspective/SKILL.md` (6/6, thoát 0) và `examples/munger-perspective/SKILL.md` (5/6, **vẫn thoát 1** dù in "基本通过"); `merge_research.py` trên cả hai (thoát 0 với cấu trúc `research/01-06`, thoát 1 với references phẳng); `srt_to_transcript.py` trên một SRT tự tạo ngoài repo (xác nhận gỡ thẻ HTML và khử dòng lặp); gọi không tham số cả hai script shell/python để xác nhận thoát 1.
- **Nhánh chết trong `download_subtitles.sh`**: xác nhận `/tmp/.ytdlp_marker` không tồn tại và không được tạo ở bất kỳ đâu trong repo, rồi tái hiện chuỗi `set -e; FOUND=$(find ... -newer /tmp/.ytdlp_marker 2>/dev/null | head -1)` để chứng minh script sống sót nhưng `FOUND` luôn rỗng.
- **Điểm mù của `quality_check.py`**: đọc thẳng regex trong `check_honest_boundary` / `check_primary_sources` / `check_tensions`, đối chiếu với ca trượt thật của `munger-perspective`.
- **Cổng thu nhận cộng đồng**: `.github/scripts/community_check.py` (`check_target_repo`, regex `总分[：:]\s*(\d+)\s*/\s*100`, danh sách mẫu điền tạm) và `.github/workflows/community-pr-check.yml` (`paths: ['COMMUNITY.md']`, `pull_request_target`).
- **CI trong `07` là ví dụ viết mới**, cố ý **không** sao chép `community-pr-check.yml` của nüwa: workflow đó kiểm PR gửi *vào* nüwa bằng `pull_request_target`, dùng lại trong repo của bạn là sai mục đích và thừa quyền.
- **Sự lệch cấu trúc giữa các ví dụ** (9 thư mục dùng `references/research/01-06.md`, 5 thư mục dùng file phẳng) đến từ liệt kê cây thư mục thật, không phải từ tài liệu.

Không có test suite trong repo, nên "verified" ở đây nghĩa là: đọc mã + chạy thật trên chính các ví dụ chính chủ.
