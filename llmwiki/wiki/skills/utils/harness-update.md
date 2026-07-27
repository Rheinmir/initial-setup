---
name: harness-update
description: TỰ BẢO TRÌ framework overstack trên máy user (self-maintain) — migrate llmwiki cũ lên harness (case B) hoặc update bản mới (case C). MỘT lệnh `install-harness.sh --self-heal` tự cài + tự backfill nợ wiki (Origin/index/OKF) + refresh bản đồ năng lực + health-check trong 1 process, không vòng lặp re-run. Trigger: "tự bảo trì framework", "self-maintain", "migrate harness", "update harness", "update overstack", "nâng cấp harness", "cài harness vào dự án cũ", "/harness-update".
---

# Skill: harness-update

## Purpose
Một lệnh gọi là xong cho dự án CŨ: cài/update harness stack (L0–L4) và tự động trả nợ wiki legacy thay user. KHÔNG dùng cho project chưa có gì + cần populate wiki từ code — đó là `/new-project-setup` (case A).

**< 30s:** dùng cờ `--self-heal` — installer tự backfill nợ (Origin + index + OKF) ngay trong process rồi re-audit 1 lần. Agent chỉ gọi 1 lệnh, đọc 1 kết quả, báo cáo. KHÔNG còn vòng lặp re-run phía agent (đó là cái làm chậm bản cũ — xem `230626-harness-update-sub30s`).

## Steps

**1. Chạy installer 1 lần với `--self-heal` (tự detect migrate/update; thiếu nguồn thì clone template):**
```bash
test -f harness/scripts/install-harness.sh \
  && bash harness/scripts/install-harness.sh . --self-heal \
  || { git clone -q --depth 1 -b orca git@github.com:rheinmir/setup.git /tmp/llmwiki-tpl \
       && bash /tmp/llmwiki-tpl/harness/scripts/install-harness.sh . --self-heal ; rm -rf /tmp/llmwiki-tpl; }
```
Installer tự làm trọn gói: cài L0–L4 → audit (Origin/index/OKF gộp 1 process qua `audit.py`) → nếu có nợ thì TỰ backfill (Origin lấy hash bằng 1 lượt `git log` cho cả lô; index thêm row thiếu; OKF migrate bold `**Type:**` → YAML) → re-audit 1 lần → activate + smoke.

**2. Đọc exit code (KHÔNG vòng lặp re-run — self-heal đã chạy bên trong):**
- `rc=0` → sạch (đã tự backfill xong). Sang bước 3.
- `rc=3` → còn nợ self-heal KHÔNG tự sửa được (vd file conflict, type OKF không suy được): danh sách nằm ngay trong output. Sửa thủ công 1 lần rồi chạy lại bước 1.
- `rc khác` (1/4) → lỗi hạ tầng (network, python3, validator hỏng) — DỪNG, báo user nguyên văn, không tự đoán.

**3. Nghiệm thu + log:**
- Xác nhận bảng "Harness tự kiểm" có **⛔×3 BỊ CHẶN ✓** trong output bước 1 (installer đã chạy `pre-commit install` nếu có pre-commit; chưa có thì nhắc user `pipx install pre-commit`).
- **Refresh bản đồ năng lực** (để agent thấy đúng đồ nghề sau update — ADR-005): `python3 ~/.claude/harness/hooks/build-capabilities.py --root .` (bản deploy cạnh hooks) HOẶC `python3 fdk/tools/build-capabilities.py` (nếu đang trong repo framework) → sinh lại `CAPABILITIES.md`. Không có file build-capabilities (bản cũ) → bỏ qua, không lỗi.
- **Health-check** (tuỳ chọn, xác nhận rào còn cắn sau update): `/health-check` hoặc `python3 ~/.claude/harness/hooks/health-check.py`.
- Append vào `llmwiki/wiki/log.md`: `## YYYY-MM-DD — harness-update — migrate/update xong (--self-heal), nợ đã backfill: <n> file`. Số liệu lấy từ dòng `[audit] backfill xong — Origin:<a> index:<b> OKF:<c>` trong output.

**4. Báo cáo cho user (bắt buộc đủ 4 ý):**
- Mode đã chạy (migrate hay update) + số nợ self-heal đã backfill (Origin/index/OKF từ dòng `[audit] backfill xong`)
- Settings root: file backup `.bak.*` nếu có merge
- Nhắc: **mở session mới thì hooks mới load**
- Mời: `/harness-tour` để xem hàng rào cắn trực quan

## Rules
- Backfill là THÊM, không bao giờ sửa/xóa nội dung wiki có sẵn (self-heal trong installer giữ đúng quy tắc này).
- Không đụng `raw/` dưới mọi hình thức.
- rc=3 (nợ còn lại) cần user/skill xử 1 lần; rc khác (hạ tầng) là việc của user — phân biệt rõ, không cố chữa lỗi hạ tầng.
- Không cờ `--self-heal` → installer chạy y hệt hành vi cũ (audit rồi exit 3 nếu nợ) — backward-compatible.
- Case A (chưa có llmwiki, cần đọc code populate wiki) → chuyển hướng sang `/new-project-setup`.
