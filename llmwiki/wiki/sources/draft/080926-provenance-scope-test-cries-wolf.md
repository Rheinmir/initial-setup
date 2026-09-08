---
type: issue
kind: tech-debt
title: "skill-provenance-scope-test báo đỏ vì working tree bẩn sẵn, không phải vì test làm bẩn"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, tech-debt, harness, test, cries-wolf, skill-provenance]
timestamp: 2026-09-08
id: 080926-provenance-scope-test-cries-wolf
source_session: "Phiên vẽ sơ đồ hoh 2026-09-07/08 — chạy trọn job repo health tại local trước khi mở PR #135"
---

# Issue: skill-provenance-scope-test báo đỏ vì working tree bẩn sẵn

## Vấn đề (một câu)

`harness/tests/skill-provenance-scope-test.sh:66` khẳng định `git status --porcelain -- skills/`
phải RỖNG để kết luận "test không làm bẩn repo thật", nhưng phép đo đó không phân biệt được
thay đổi do **chính test** gây ra với thay đổi **đã có sẵn** trong working tree.

## Bối cảnh & bằng chứng

Mã hiện tại (dòng 65–66):

```bash
# 3. Repo thật không bị đụng (probe chỉ đọc, self-test không side-effect)
git -C "$ROOT" status --porcelain -- skills/ 2>/dev/null | grep -q . \
  && bad "test làm bẩn skills/ của repo thật!" || ok "repo thật (skills/) nguyên vẹn sau test"
```

Ý định đúng — chặn self-test có side-effect. Phép đo sai — nó đo **trạng thái tuyệt đối** thay
vì **hiệu số**.

Gặp thật ngày 2026-09-08 khi sửa `skills/diagram/SKILL.md` cho PR #135:

| Thời điểm | Lệnh | Kết quả |
|---|---|---|
| Có sửa đổi chưa commit trong `skills/` | `bash harness/tests/skill-provenance-scope-test.sh .` | `✗ test làm bẩn skills/ của repo thật!` → `1 VI PHẠM`, rc=1 |
| Sau khi commit, không đổi gì khác | cùng lệnh | `✓ repo thật (skills/) nguyên vẹn sau test` → `PASS` |

Hai lần chạy chỉ khác nhau ở chỗ thay đổi đã được commit hay chưa. Bản thân test không hề đụng
`skills/` trong cả hai lần — nó chạy trong sandbox `$SB` rồi `rm -rf "$SB"`.

Vì sao CI không thấy: CI chạy trên fresh-clone của một commit nên working tree luôn sạch. Đây
đúng khoảng cách L2 (local) ≠ L4 (CI) mà `[[harness-enforcement-floor]]` mô tả, nhưng lệch theo
chiều ngược lại thường gặp: **local đỏ giả**, CI xanh thật.

Tác hại không nằm ở một lần đỏ, mà ở vòng phản hồi: mọi phiên sửa framework có chạm `skills/`
đều thấy cổng này đỏ trước khi commit. Một cổng đỏ thường xuyên vì lý do không liên quan sẽ
được học thành "cổng này hay đỏ, bỏ qua đi" — và lần nó đỏ THẬT thì cũng bị bỏ qua. Cổng mất
khả năng cắn mà không ai gỡ nó.

Liên quan, không trùng: `[[100826-skill-behavioral-integrity-verification]]` nói về việc
`skill-provenance` chưa kiểm hành vi; issue này nói về phép đo sạch/bẩn của **scope-test**.

## Phạm vi

- `harness/tests/skill-provenance-scope-test.sh` — mục 3 (dòng ~64–66).
- Rà cùng khuôn ở các test khác trong `harness/tests/` nếu có dùng `git status --porcelain` làm
  khẳng định tuyệt đối thay vì hiệu số.

## Không thuộc phạm vi

- Không đụng `fdk/tools/skill-provenance.py` — công cụ chạy đúng, chỉ có phép đo trong test sai.
- Không đổi ngưỡng/ý định của mục 1 và 2 trong test (pin, tamper).
- Không sửa `medic.py` (nó phân loại "1 local đổi (dev churn, không chặn)" — hành vi đó đúng).

## Hướng gợi ý (không bắt buộc)

Đo **hiệu số**, không đo trạng thái tuyệt đối: chụp trước, so sau.

```bash
BEFORE="$(git -C "$ROOT" status --porcelain -- skills/ 2>/dev/null)"
# … thân test …
AFTER="$(git -C "$ROOT" status --porcelain -- skills/ 2>/dev/null)"
[ "$BEFORE" = "$AFTER" ] && ok "repo thật (skills/) nguyên vẹn sau test" \
                         || bad "test làm bẩn skills/ của repo thật!"
```

Giữ nguyên thông điệp khi đỏ thật; khi working tree vốn đã bẩn thì im lặng cho qua vì đó không
phải việc của test này.

## Tiêu chí HOÀN THÀNH

- [ ] Sửa `skills/<bất kỳ>/SKILL.md` mà chưa commit → test vẫn **PASS**.
- [ ] Cố tình cho test ghi một file vào `skills/` → test **đỏ** với đúng thông điệp cũ.
- [ ] `bash harness/tests/skill-provenance-scope-test.sh .` xanh trên working tree sạch.
- [ ] `fdk-gate` vẫn 21/21; CI `repo health` vẫn xanh.

## Assign & lý do

`@Rheinmir` · dispatch **Claude** · entry **/fdk**. Sửa 3 dòng bash trong một test của harness,
tiêu chí nghiệm thu tất định và chạy được bằng máy — không cần người phán. Vào bằng `/fdk` vì
chạm bề mặt framework (`harness/tests/`) nên phải qua pre-flight + fdk-gate.

## Origin

- **Raise bởi:** phiên vẽ sơ đồ `hoh` 2026-09-07/08, lúc chạy trọn job `repo health` của
  `.github/workflows/harness.yml` tại local theo yêu cầu của `/fdk` trước khi push.
- **Bằng chứng:** hai lần chạy trước/sau commit `e220bd3` (nay là `1e8e633`) trên nhánh
  `fix/archify-fork-pin`; PR [Rheinmir/setup#135](https://github.com/Rheinmir/setup/pull/135).
- **Nền:** `[[harness-enforcement-floor]]` — L2 ≠ L4.
