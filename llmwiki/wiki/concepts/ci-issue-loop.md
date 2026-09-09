---
type: concept
title: "Vòng CI → issue → agent: biến một gate đỏ thành việc làm được ngay"
tags: [ci, issue, agent, ledger, gate, maintainer]
timestamp: 2026-09-09
id: ci-issue-loop
---

# Vòng CI → issue → agent

Ba lớp gác nối liền nhau để một gate đỏ không nằm im trong tab Actions: **cắn sớm ở
máy** (pre-commit), **cắn chắc ở CI** (workflow), và khi vẫn lọt thì **tự mở một issue
đủ dữ kiện để agent nhận là làm được ngay** — không phải một thông báo đỏ nữa để bỏ quên.

## Vì sao có

Ngày 2026-09-09 phát hiện `skills-sync` đỏ suốt hai ngày, ba commit liên tiếp trên nhánh
`orca`, mà không ai biết. Nguyên nhân kỹ thuật thì nhỏ: sổ `fdk/skills.provenance.json`
không được `record` lại sau khi sửa ba skill, nên checksum lệch. Nguyên nhân hệ thống mới
là thứ đáng sửa: **không có gì bắt cập nhật sổ khi skill đổi**, nên CI là nơi đầu tiên
biết — và CI lại không có đường báo ra ngoài.

Hai câu hỏi tách ra từ đó, và mỗi câu dẫn tới một lớp khác nhau:

- *Vì sao CI là nơi ĐẦU TIÊN biết?* → thiếu chỗ cắn sớm hơn ở máy.
- *Đỏ rồi thì ai biết?* → thiếu đường báo ra khỏi tab Actions.

## Ba lớp

**Lớp 1 — cắn sớm ở máy.** Hook pre-commit chạy đúng lệnh mà CI chạy
(`skill-provenance.py check --ci`), giới hạn `files: ^skills/`. Sửa skill mà quên record
thì hỏng commit tại chỗ, không cần chờ CI. Hook đã fire-drill: làm bẩn một `SKILL.md` →
FAIL; khôi phục → PASS. Lớp này có hai lỗ cố ý chấp nhận — máy chưa `pre-commit install`,
và `--no-verify` — nên nó không thay được lớp 2.

**Lớp 2 — cắn chắc ở CI.** Hai workflow `harness` và `skills-sync` vẫn là sàn đảm bảo.
Không lớp nào ở máy được phép làm lý do bỏ chúng.

**Lớp 3 — đỏ thì tự mở issue.** `.github/workflows/ci-raise-issue.yml` bắt sự kiện
`workflow_run` của hai workflow trên, và chỉ chạy khi hội đủ ba điều kiện: kết luận là
`failure`, sự kiện gốc là `push`, và nhánh là nhánh mặc định. Đỏ trên nhánh PR **không**
đổ vào ledger chung — đó là việc của người mở PR. Đỏ lại cùng một workflow thì bình luận
vào issue đang mở chứ không đẻ issue trùng.

## Thân issue: cấu trúc trước, log sau

Một issue chỉ hữu ích khi agent nhận là làm được mà không hỏi lại ai. Nên thân issue mở
đầu bằng một khối YAML máy đọc, do `harness/scripts/ci-fail-parse.py` cắt ra từ chính log:

```yaml
ci-fail:
  workflow: "skills-sync"
  failed_step: "..."
  repro_cmd: "python3 fdk/tools/skill-provenance.py check --ci"
  exit_code: "1"
  fix_hint: "chạy `record` để cập nhật sổ hoặc điều tra sửa đổi lạ."
  failed_checks:
    - "MODIFIED  doyourmagic  — lệch: SKILL.md, ..."
```

`repro_cmd` là thứ biến issue từ *đọc được* thành *làm được*: lần ngược từ dòng
`##[error]` tới `##[group]Run <cmd>` của đúng step đỏ đó, ra nguyên văn lệnh chạy lại tại
máy. `failed_checks` và `fix_hint` bám quy ước in của **chính repo này** — `ok()`/`bad()`
trong `harness/tests/*.sh`, `↳ sửa:` của medic, dấu `✗` của 35 tool. Không khớp thì parser
khai `parsed: false` và để log thô lại; thà nói không biết còn hơn đoán sai cho agent.

Parser viết bằng Python thay `sed`/`awk`/`cut` vì hai lý do đo được, không phải sở thích:
log GitHub trả màu ở **hai dạng** (ESC thật và caret-notation `^[` hai ký tự, tuỳ job) nên
regex chỉ bắt một dạng sẽ mất sạch dòng `FAIL` mà vẫn trông như chạy đúng; và log lẫn byte
không UTF-8 khiến `sed`/`cut` của macOS bỏ ngang với `Illegal byte sequence`.

## Prompt cố định, và tiêu chuẩn nghiệm thu

Phần sau khối YAML là prompt cho agent nhận việc, chèn nguyên văn từ
[[ci-maintainer-brief]] — sửa prompt là sửa một file, không mổ workflow. Prompt bắt tái
hiện trước khi sửa (đỏ → tự nâng nhãn `ready-for-agent` và claim; **không đỏ → dừng**, đổi
`needs-info`, vì xanh ở máy mà đỏ trên CI là khác biệt môi trường phải người nhìn), bắt
chữa gốc thay vì chữa triệu chứng, và bắt hỏi lại câu *"vì sao CI là nơi đầu tiên biết"*
để thêm chỗ cắn sớm có fire-drill.

Kết thúc bằng bảng **năm tiêu chuẩn nghiệm thu**, thiếu một mục là chưa xong: tái hiện
được đỏ · gate xanh sau sửa · `medic --ci` không fail · **dòng ledger tồn tại và trỏ đúng
issue** · fire-drill chỗ cắn sớm nếu có thêm. Mỗi mục kèm lệnh chứng và bắt dán output
thật.

## Ranh giới ledger/mirror

`llmwiki/wiki/sources/ISSUES.md` là nguồn chân lý; issue GitHub chỉ là mirror. CI **không**
ghi ledger, và đây là quyết định chứ không phải thiếu sót — commit từ Actions không đi qua
pre-commit, nên không validator nào cắn nó. Một đường ghi vào nguồn chân lý mà không có
cổng là thứ đắt nhất trong cả thiết kế này. Hai hệ quả nhỏ hơn cũng nghiêng cùng hướng:
hai workflow đỏ cùng lúc sẽ đua nhau ghi một file markdown (hôm 2026-09-09 chúng đỏ trong
cùng một phút), và nếu ai đó thay `GITHUB_TOKEN` bằng PAT thì mỗi lần đỏ sẽ đẻ một commit,
commit lại đẻ một run.

Nên người ghi ledger là **agent nhận việc**, ghi ngay lúc claim chứ không để tới lúc đóng.
Việc không có dòng ledger là việc *không tồn tại* với `harness/scripts/frontier.py`, và
người kế tiếp sẽ nhận trùng.

## Giới hạn còn mở

`frontier.py` chỉ đọc ledger, nên issue do CI mở **chưa** xuất hiện trong frontier cho tới
khi có người hoặc agent claim và ghi dòng. Muốn agent tự phát hiện trọn vẹn thì cần thêm
một đường gộp mirror vào frontier (`--pull-mirror` đọc `gh issue list --label ci-fail`).
Chưa làm, vì nó đổi ngữ nghĩa "frontier = việc đã vào sổ".

## Notes
- [[ci-maintainer-brief]] — prompt cố định chèn vào mọi issue CI mở
- [[issue-tracker]] — hợp đồng tracker của repo (ledger gốc, GitHub mirror)

## Origin
- **Source:** phiên 2026-09-09 — `skills-sync` đỏ 2 ngày/3 commit trên `orca` không ai biết
- **Commit:** `59bc4d2` (fix + hook pre-commit) → `f1b` (tiêu chuẩn nghiệm thu)
- **Date:** 2026-09-09
