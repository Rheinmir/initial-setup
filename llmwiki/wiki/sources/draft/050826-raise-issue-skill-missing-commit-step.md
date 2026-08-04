---
type: issue
kind: tech-debt
title: "Skill raise-issue thiếu bước commit — ledger mặc định untracked, không travel theo repo như quảng cáo"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, raise-issue, ledger, git, tech-debt, skills]
timestamp: 2026-08-05
id: 050826-raise-issue-skill-missing-commit-step
source_session: "Phát hiện khi user hỏi vì sao file ledger 010826-wiki-mental-model-taxonomy.md không có trên branch/git-log/PR nào dù raise-issue báo đã raise xong"
---

# Issue: Skill raise-issue thiếu bước commit — ledger mặc định untracked

## Vấn đề (một câu)
Skill `raise-issue` (7 bước: phân loại → query wiki → viết draft → assign → đăng ký index → mirror tracker → xác nhận) **không có bước `git add`/`commit` nào**, nên mọi issue nó tạo ra mặc định nằm ở trạng thái untracked trên đĩa — mâu thuẫn trực tiếp với định nghĩa của chính nó: *"Issue = một file draft ... đi theo repo khi clone ... Đây luôn là NGUỒN CHÂN LÝ"* và với hợp đồng tracker (`issue-tracker.md`): *"Nguồn chân lý: local-markdown ... Luôn chạy được, không cần mạng, **đi theo repo khi clone**"*.

## Bối cảnh & bằng chứng
Phát hiện trong phiên `/raise-issue` cho [[010826-wiki-mental-model-taxonomy]] (2026-08-01): sau khi skill báo *"Đã raise xong"* + mirror GitHub thành công (GH#93), user hỏi lại và tái hiện được:

```
git status --porcelain llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md
?? llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md   ← untracked

git log --all --oneline -- llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md
(rỗng — không nằm trên branch nào, không lịch sử, không PR nào thấy được)
```

Đây **không phải sự cố riêng lẻ của một file**. Kiểm tra thêm trong cùng phiên xử lý: draft issue cũ hơn đã có mặt trong `ISSUES.md` từ trước, `240726-global-tool-path-resolution-broken.md`, **cũng untracked** tại thời điểm phát hiện — một issue đang `status: open` trong ledger, được người/agent khác có thể pull về xử lý, nhưng nếu họ `git clone` repo thay vì dùng đúng working tree hiện tại thì **file không tồn tại với họ**. Quét lại thư mục `llmwiki/wiki/sources/draft/` tại thời điểm raise issue này: **6 file untracked**, trong đó ít nhất 1 file (`240726-global-tool-path-resolution-broken`) đang được `ISSUES.md` trỏ tới như một issue `open` hợp lệ.

Root cause đọc trực tiếp từ thân skill `raise-issue.md`: bước 3 ("Viết draft"), bước 5 ("Đăng ký vào index"), bước 6 ("Mirror lên tracker remote") đều là thao tác **Write/Edit trên working tree**, không có thao tác git nào. Bước 7 ("Xác nhận, KHÔNG thực hiện") chỉ báo lại đường dẫn + link, không kiểm tra file đã travel-được hay chưa — nên skill tự báo "xong" trong khi lời hứa cốt lõi của nó (ledger di động theo repo) chưa được giữ.

Đối chiếu với luật git toàn cục (`~/.claude/CLAUDE.md` / system prompt): *"NEVER commit changes unless the user explicitly asks you to"* — nghĩa là hành vi hiện tại của tôi (không tự commit) là ĐÚNG theo luật đó, nhưng lại tạo ra đúng khoảng trống này: một skill tự nhận "đây là nguồn chân lý, đi theo repo" nhưng quy trình của nó không bao giờ tạo ra trạng thái đó nếu không có người nhắc riêng.

## Phạm vi
- File `skills/utils/raise-issue.md` (canonical) và bản mirror ở `llmwiki/skills/utils/raise-issue.md` (nếu tồn tại) — thêm một bước rõ ràng (có thể là bước 5.5 hoặc cuối bước 7) yêu cầu `git add` + xác nhận với user trước khi `git commit` hai file: draft mới + `ISSUES.md` vừa sửa.
- Cách skill BÁO CÁO kết quả ở bước 7 — phải phân biệt rõ "đã ghi ra đĩa" vs "đã commit, travel-được" thay vì gộp chung thành "đã raise xong".
- Universal: ảnh hưởng mọi dự án dùng overstack có gọi `/raise-issue`, không riêng dự án này.

## Không thuộc phạm vi
- KHÔNG tự động push lên remote — commit local là đủ để "đi theo repo khi clone" cục bộ; push là quyết định khác, vẫn cần hỏi riêng theo luật git hiện có.
- KHÔNG dọn 6 file draft untracked hiện có trong repo này ngay trong issue này — đó là dọn dẹp tồn đọng, xử lý riêng (có thể là một issue `process` khác nếu cần), tránh scope creep.
- KHÔNG đổi luật toàn cục "never commit unless asked" — giải pháp phải hoạt động TRONG luật đó (hỏi/xác nhận trước khi commit), không phải xin ngoại lệ.

## Hướng gợi ý (không bắt buộc)
1. Thêm vào cuối bước 5 (đăng ký index) hoặc đầu bước 7: agent chủ động đề xuất `git add <draft> <ISSUES.md>` rồi hỏi user một câu ngắn "commit ngay để ledger travel-được?" — mặc định Recommended = có, vì đây đúng lời hứa cốt lõi của ledger.
2. Bước 7 (xác nhận) đổi báo cáo thành 2 dòng rõ ràng: trạng thái ghi đĩa (luôn có) và trạng thái git (committed / còn untracked chờ user quyết) — không gộp làm một câu "đã raise xong".
3. Cân nhắc thêm một câu trong chính `issue-tracker.md` làm rõ: "ledger local-markdown chỉ thật sự là NGUỒN CHÂN LÝ *sau khi commit*; file untracked là bản nháp chưa travel" — tránh hiểu lầm lặp lại ở phiên khác.

## Tiêu chí HOÀN THÀNH
- `skills/utils/raise-issue.md` có bước commit tường minh (kèm bước hỏi xác nhận, không tự ý commit khi chưa hỏi).
- Chạy thử `/raise-issue` một lần trên issue mẫu: `git status --porcelain` trên file draft mới trả về rỗng (đã tracked/committed) ngay sau khi skill báo hoàn tất — không cần người hỏi lại như lần này.
- Không phá vỡ luật "never commit unless asked" — bước commit phải đi kèm xác nhận, verify bằng cách đọc lại skill thấy rõ điểm dừng chờ user.

## Assign & lý do
`@Rheinmir` — chủ ledger + toàn bộ issue kiến trúc/tech-debt khác của repo này. Dispatch `Claude` vì việc cần đọc và sửa đúng logic một skill Markdown (không phải chạy máy móc thuần, cần cân nhắc câu chữ bước xác nhận). Entry `/fdk` vì đây là sửa CHÍNH cơ chế của framework (một skill dùng chung), không phải việc riêng một dự án downstream.

## Origin
- **Source:** phiên `/raise-issue` 2026-08-01 cho [[010826-wiki-mental-model-taxonomy]] — user phát hiện và tái hiện bằng `git status`/`git log --all` rằng ledger vừa "raise xong" không tồn tại trên bất kỳ branch/lịch sử/PR nào; agent xác nhận đúng, tìm thêm bằng chứng hệ thống (`240726-global-tool-path-resolution-broken.md` cũng untracked), rồi commit thủ công theo yêu cầu user (`0e0c36e`) trước khi raise issue này để ghi lại root cause cho phiên khác sửa.
- **Bằng chứng đo trong phiên:** 6 file untracked trong `llmwiki/wiki/sources/draft/`, 1 trong số đó đang được `ISSUES.md` trỏ tới ở trạng thái `open`.
- **Chưa sửa skill** — issue này CHỈ ghi bối cảnh + phạm vi, việc sửa `raise-issue.md` là của phiên nhận qua `/fdk`.
