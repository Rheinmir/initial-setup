# 07 — Phát hành skill của bạn và xin thu vào COMMUNITY.md

**Vì sao dùng**: skill bạn chắt lọc ra là tài sản của bạn — repo nüwa **không nhận** persona skill vào `examples/`; đường chính thức là bạn tự host repo riêng (star về bạn) rồi thêm một dòng vào chỉ mục cộng đồng.
**Sinh ra cái gì**: một repo GitHub công khai đúng chuẩn, một cổng CI tự kiểm, và một PR một-dòng vào `COMMUNITY.md`.

> File này là lệnh **SHELL** + thao tác GitHub.

---

## Bước 1 — Đóng gói repo cho đúng chuẩn thu nhận

Bốn thứ máy kiểm sẽ đòi (đọc trực tiếp từ `.github/scripts/community_check.py`):

```
<your-repo>/
├── SKILL.md          # phải có chương 「诚实边界」 (hoặc "Honest" / "honest-limits")
├── FIDELITY.md       # phải chứa đúng chuỗi「总分：NN/100」với NN ≥ 70
└── references/       # bắt buộc có; nên có references/research/ bên trong
    └── research/     # thiếu chỉ bị ⚠️ nhắc người xem, không chặn cứng
```

```bash
gh repo create <ten-skill>-skill --public --source=. --push
```

Tự kiểm trước khi đẩy:

```bash
export NUWA=~/.claude/skills/nuwa-skill
python3 $NUWA/scripts/quality_check.py ./SKILL.md      # cổng hình thức, xem 05
grep -c '总分：' FIDELITY.md                            # phải ≥ 1
grep -n '总分：[0-9]\+/100' FIDELITY.md                 # phải khớp đúng dạng này
ls references/research/                                 # nên có 01-06
```

## Bước 2 — Chạy máy kiểm của repo ngay trên máy bạn, trước khi mở PR

`community_check.py` có chế độ chạy tay, không cần PR:

```bash
cd /đường/dẫn/nuwa-skill
GITHUB_TOKEN=$(gh auth token) python3 .github/scripts/community_check.py --check-repo <owner>/<repo>
```

Mã thoát `0` = qua toàn bộ cổng hình thức; `1` = có ít nhất một mục ❌ (script in ra từng dòng ✅/⚠️/❌). Token không bắt buộc nhưng nên có — không token thì API GitHub ẩn danh dễ dính giới hạn tần suất và script sẽ hiểu nhầm là "repo không tồn tại".

Không có token thì:

```bash
python3 .github/scripts/community_check.py --check-repo <owner>/<repo>
```

## Bước 3 — Cổng CI tối thiểu cho repo của bạn

Đây là ví dụ **viết mới cho trường hợp của bạn**, không phải bản sao `.github/workflows/community-pr-check.yml` của nüwa (workflow đó dùng `pull_request_target` để kiểm PR gửi *vào* nüwa — dùng lại trong repo bạn là sai mục đích và thừa quyền).

`.github/workflows/skill-quality.yml`:

```yaml
name: Skill quality gate

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Lấy script kiểm chất lượng của nüwa
        run: |
          curl -fsSL -o quality_check.py \
            https://raw.githubusercontent.com/alchaincyf/nuwa-skill/main/scripts/quality_check.py

      - name: Kiểm 6 tiêu chí hình thức (không chặn khi 5/6)
        run: |
          python3 quality_check.py SKILL.md | tee report.txt || true
          grep -q '结果: [56]/6 通过' report.txt

      - name: Bảo chân phải ≥70 và không có giá trị điền tạm
        run: |
          grep -Eq '总分[：:][[:space:]]*([7-9][0-9]|100)/100' FIDELITY.md
          ! grep -Eq '预估|待跑|待测|待补|待定|待填|占位|未实测|未测试|自评分|YYYY-MM-DD' FIDELITY.md
```

Chủ ý của cổng này: `quality_check.py` thoát `1` ngay cả khi 5/6 (xem [05](05-helper-scripts-cli.md)), nên chặn cứng theo mã thoát sẽ đỏ CI vì một mục hình thức. Ở đây ta bắt theo *nội dung báo cáo* — chấp nhận 5/6 và 6/6, đỏ khi ≤4/6 — rồi kiểm riêng hai điều kiện thu nhận thật sự: điểm bảo chân và không có giá trị điền tạm. Muốn nghiêm hơn thì đổi `[56]` thành `6`.

## Bước 4 — PR một dòng vào COMMUNITY.md

`COMMUNITY.md` có ba mục: 人物合集索引 (chỉ mục sưu tập nhân vật), 多人格编排 (điều phối đa nhân cách), 主题应用 (ứng dụng chuyên đề). Thêm đúng một dòng vào bảng phù hợp, đúng dạng:

```markdown
| [<owner>/<repo>](https://github.com/<owner>/<repo>) | mô tả một dòng, nêu nhân vật/chủ đề và điểm bảo chân |
```

```bash
gh repo fork alchaincyf/nuwa-skill --clone
cd nuwa-skill
git checkout -b add-<ten-skill>
# sửa đúng MỘT dòng trong COMMUNITY.md
git commit -am "docs(community): add <owner>/<repo>"
gh pr create --title "Add <owner>/<repo> to COMMUNITY.md" \
  --body "Skill: <nhân vật>. Fidelity: NN/100 (hạng A/B), chấm bằng hai agent độc lập ngày YYYY-MM-DD."
```

Bot chạy tự động khi PR **chỉ chạm `COMMUNITY.md`** và dán checklist ✅/❌ thành comment; sửa rồi push là nó chạy lại. Máy qua rồi thì người bảo trì vẫn xét tay lằn ranh đạo đức và chất lượng nội dung trước khi merge.

## Lằn ranh đạo đức (không thu, và đừng gửi)

- Chắt lọc **người thường còn sống, không phải nhân vật công chúng** mà chưa được họ đồng ý (đồng nghiệp, người yêu cũ, người quen).
- Skill phục vụ mạo danh, quấy rối, lừa đảo.
- Skill trong lĩnh vực y tế, pháp lý, đầu tư mà **không có** tuyên bố miễn trừ rõ ràng và ranh giới "không thay thế chuyên gia".

## Cạm bẫy đã kiểm chứng

- **PR chạm nhiều hơn `COMMUNITY.md` là trượt thẳng.** Workflow chỉ chạy trên `paths: ['COMMUNITY.md']`, và kiểm tra đầu tiên là "PR chỉ đổi COMMUNITY.md"; đụng vào `SKILL.md` là ❌ ngay.
- **`总分：NN/100` phải viết đúng chuỗi.** Máy kiểm dò bằng regex `总分[：:]\s*(\d+)\s*/\s*100`. Viết "Tổng điểm: 92" hay "92 points" là **không parse được** và bị ❌, dù điểm thật có cao.
- **Không đặt persona skill vào `examples/` của nüwa.** Thư mục đó là hàng chính chủ, giữ một khẩu độ chất lượng thống nhất; PR bỏ skill vào đó sẽ bị từ chối, và cũng thiệt cho bạn (star về repo người khác).
- Repo không có `SKILL.md` ở gốc vẫn thu được — máy xếp vào loại "sưu tập/công cụ" và chỉ kiểm sự tồn tại, để người xét tay.
