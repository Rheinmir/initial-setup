---
type: issue
kind: tech-debt
title: "skill-provenance.py + build-skill-search.py: path resolution vỡ sau khi travel xuống global harness home"
status: open
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, travel, global-shared, path-resolution, skill-provenance, skill-search]
timestamp: 2026-07-24
id: 240726-global-tool-path-resolution-broken
source_session: "Phiên hỏi '2 file skills.provenance.json/skills.search.json có xuống máy khách không' → /fdk-uat xác minh thật trên global harness home hiện có"
---

# Issue: skill-provenance.py + build-skill-search.py vỡ path resolution sau khi travel

## Vấn đề (một câu)
Hai tool `fdk/tools/skill-provenance.py` và `fdk/tools/build-skill-search.py` tự suy ra thư mục `skills/` bằng cách đi ngược từ vị trí file của chính chúng (`Path(__file__).resolve().parents[2]` / `os.path.dirname(__file__) + "/../.."`), đúng khi còn nằm trong repo gốc nhưng **sai khi travel xuống `~/.claude/harness/fdk/tools/`** (global install) — nơi `skills/` thật nằm ở `~/.claude/skills/`, không phải `~/.claude/harness/skills/` (không tồn tại) — nên hai năng lực này coi như không hoạt động ở global mà không báo lỗi rõ ràng.

## Bối cảnh & bằng chứng
- Cài global qua `install-harness.sh --global` copy `fdk/tools/*.py` vào `$GH/fdk/tools/` (`harness/scripts/install-harness.sh:136`), gồm cả 2 tool này — xác nhận CÓ travel.
- Skill thật được cài **riêng** qua `npx skills add ... --global --all` (gọi trong `harness/poc-vendor-neutral/install.sh:254`) → nằm ở `~/.claude/skills/`, không nằm dưới `~/.claude/harness/`.
- Tái hiện THẬT trên máy hiện có (bản `~/.claude/harness/` sẵn có từ các lần cài thật trước, đúng trạng thái downstream sau curl bootstrap `--global`):
  ```
  $ python3 ~/.claude/harness/fdk/tools/build-skill-search.py
  No SKILL.md found under /Users/giatran/.claude/harness/skills
  # → không sinh fdk/skills.search.json

  $ python3 ~/.claude/harness/fdk/tools/skill-provenance.py list
    0 skill có provenance.
  # → sai, máy có 94 skill thật ở ~/.claude/skills/
  ```
- Đối chiếu: chạy đúng bản trong repo (`python3 fdk/tools/build-skill-search.py`) → `✓ indexed 84 skills · 1886 terms …` bình thường. Vậy lỗi chỉ phát sinh SAU KHI travel, không phải lỗi logic BM25/provenance.
- Cả hai **im lặng trả về rỗng** thay vì lỗi rõ ràng — tool tự coi như "chạy xong" trong khi vô dụng, cùng lớp với dòng dưới.
- **Đây là một instance MỚI của một lớp lỗi đã biết**: [[190726-travel-gap-forcing-functions]] (T-260719-01, status `proposed`) đã ghi nhận "34/69 skill global dính path repo-relative" cho *skill* — nhưng quét đó chưa phủ 2 *tool* này ở `fdk/tools/`. Liên quan thêm: `030726-skill-resolve-supplychain` (GH#13 — chính là issue gốc sinh ra `skill-provenance.py`) và [[110726-shipped-vs-documented-parity]] (GH#77, done — lớp lỗi "tài liệu hứa N năng lực, installer chỉ giao M").

## Phạm vi
- `fdk/tools/skill-provenance.py` (biến `REPO`/`SKILLS`, dòng ~39-40).
- `fdk/tools/build-skill-search.py` (biến `ROOT`/`SKILLS_DIR`, dòng ~32-34).
- Chỉ ảnh hưởng khi chạy từ **global harness home** (`~/.claude/harness/...`); hành vi trong repo gốc không đổi.

## Không thuộc phạm vi
- Không sửa lại toàn bộ 34/69 skill đã ghi trong `190726-travel-gap-forcing-functions` — đó là task T-260719-01 riêng, đang `proposed`.
- Không đổi vị trí output JSON (`fdk/skills.*.json` vẫn ghi cạnh bản tool đang chạy, kể cả ở global).
- Không đổi cơ chế cài skill (`npx skills add --global`).

## Hướng gợi ý (không bắt buộc)
Thêm hàm fallback nhỏ ở mỗi tool: nếu `<ROOT>/skills` không tồn tại/rỗng (không có `*/SKILL.md`) và `ROOT` tên là `harness` (dấu hiệu đang chạy từ global harness home), thử `<ROOT>/../skills` (`~/.claude/skills`). Không đổi hành vi trong repo gốc vì candidate đầu tiên vẫn khớp ngay.

## Tiêu chí HOÀN THÀNH
- [ ] `python3 ~/.claude/harness/fdk/tools/build-skill-search.py` (chạy từ bản global thật) → in `✓ indexed N skills…` với N ≈ số skill thật ở `~/.claude/skills/`, sinh đúng `~/.claude/harness/fdk/skills.search.json`.
- [ ] `python3 ~/.claude/harness/fdk/tools/skill-provenance.py list` (chạy từ bản global) → không còn báo 0 nếu có skill đã record; `record --all` chạy được và thấy đúng danh sách skill thật.
- [ ] Chạy lại 2 lệnh trên trong repo gốc (`fdk/tools/...`) → hành vi KHÔNG đổi so với trước fix.
- [ ] Có ít nhất 1 check tự động (self-test hoặc test nhỏ) exercise nhánh fallback này.

## Assign & lý do
`@Rheinmir` — chủ repo, cùng người đứng tên toàn bộ ledger `ISSUES.md`. Dispatch Claude vì đây là sửa path resolution cục bộ, không cần quyết định thiết kế lớn; mở qua `/fdk` vì đây là năng lực nội bộ framework (fdk/), không phải feature dự án downstream.

## Origin
Raised bởi skill `/raise-issue` (phiên 2026-07-24), theo yêu cầu user sau khi `/fdk-uat` tái hiện bug thật (không suy đoán từ đọc code) trên global harness home hiện có của máy này. Bằng chứng thực nghiệm nằm nguyên trong phần "Bối cảnh & bằng chứng" ở trên.
