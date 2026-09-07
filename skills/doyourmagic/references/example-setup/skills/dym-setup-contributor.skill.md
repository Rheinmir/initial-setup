---
name: dym-setup-contributor
description: "Sửa CHÍNH overstack: fdk-gate 21 step (exit 0/2), medic 18 probe, sửa luật đúng đường policy→gen-converters, /fdk-uat canary, /ship, R15 no-ai-attribution. Gọi khi: 'contribute overstack', 'sửa rule harness', 'fdk-gate', 'release overstack'."
---

# Skill: dym-setup-contributor — Đóng góp: sửa chính overstack

## When to use
- **Tại sao chạy:** repo framework có định-nghĩa-hoàn-thành riêng, máy-đọc-được. Bạn không tự đoán "đã đủ chưa" — bạn chạy một lệnh và nó trả lời.
- **Sinh ra gì:** bảng ✓/✗ 21 step, `RELEASE-vX.Y.Z.md` khi cắt release, và (khi cần) nhánh canary `uat/<ts>` trên remote.
- Gọi qua hub: `/dym-setup contributor` — hoặc trực tiếp `/dym-setup-contributor` nếu đã symlink riêng.

## Steps
### 1. Lấy repo và định vị

```bash
git clone -b orca https://github.com/rheinmir/setup.git
cd setup
python3 -c "import yaml" || pip install pyyaml     # thiếu pyyaml → validator fail-open, mọi cổng xanh giả
```

Không có `package.json` / `pyproject.toml` / `Makefile`. "Entry point" của repo là:

| Đường | Là gì |
|---|---|
| `harness/poc-vendor-neutral/policy.yaml` | **nguồn chân lý duy nhất** của 19 luật |
| `harness/poc-vendor-neutral/gen-converters.py` | sinh mọi adapter vendor + CI + pre-commit từ policy |
| `harness/poc-vendor-neutral/bin/llmwiki-validate.py` | lõi validator (đọc policy, không hardcode luật) |
| `harness/scripts/` (68 file) · `harness/validators/` (18 file) | engine + validator production |
| `fdk/tools/` (23 file) | đồ nghề phát triển **chính** framework |
| `skills/` (87 thư mục) | canonical skill, mirror sang `llmwiki/skills/` |
| `fdk/wiki/` | wiki RIÊNG của framework (ADR-001..010) — không travel xuống dự án |

Front door on-demand cho mọi việc phát triển framework: gọi `/fdk` **trong chat** (pre-flight + inventory live).

### 2. Cổng bắt buộc: `fdk-gate.py`

Định-nghĩa-hoàn-thành, bản máy đọc. **exit 0 = đủ điều kiện push · exit 2 = thiếu step.**

```bash
python3 harness/scripts/fdk-gate.py --root .
python3 harness/scripts/fdk-gate.py --root . --json   # cùng mã thoát, output máy đọc
```

21 step, mỗi step trỏ tới một gate đã có (single source — không lặp lại logic):

`R3 index-sync` · `L4 wiki-health` · `arch-scan` · `harness-lint` · `agent↔claude parity` · `duplicate-basename` · `harness-doctor` · `adapt-registry leak-gate` · `overstack-docs current` · `capabilities current` · `skill mirror parity` · `skill cross-surface` · `task-lifecycle` · `audit-chain` · `code-health` · `bnal self-test wired` · `policy↔converters drift` · `graph-engineering tests` · `vendor-neutral demo` · `vendor-neutral broad` · `BNAL feature self-tests`

Thêm gate mới = thêm một dòng vào `STEPS` (và cập nhật checklist con-người ở master-wiki cho khớp).

### ⚠️ HEAD của `orca` từng KHÔNG qua chính cổng của nó (tới `5456eb3`; đã sửa ở #116)

> **Cập nhật 2026-09-07 (sau lượt fix #116–#119):** `orca` HEAD `16e1971` **xanh toàn bộ CI** lần đầu; `fdk-gate` 21/21; `template_version` 1.3.69 (installer tự cài lại global khi thấy version đổi — đã đo trên máy thật: `1.3.68 → 1.3.69`, smoke OK). Bẫy migrate (#106) và pre-commit trỏ engine đã gỡ cũng đã vá ở #117. Skill `/playwright-verify` có trong repo (#119, 88 skill).

Chạy thật trên clone sạch tại `5456eb3` (2026-09-04), không sửa gì:

```
✗ THIẾU 5/21 step → CHƯA đủ điều kiện push.
rc = 2
```

| Step đỏ | Thông điệp |
|---|---|
| `L4 wiki-health` | quét 175 trang `llmwiki/wiki`, broken wikilink từ `entities/repowise.md`: `[[code-graph]]` ×3, `[[frontier-gap-scan]]`, `[[innovation-110826]]`, … |
| `overstack-docs current` | `[build-overstack-docs] ⚠ 1 skill chưa phân nhóm mind map (đang ở '❓ chưa phân loại'): diag…` |
| `task-lifecycle` | `[task-lifecycle] LỆCH state-machine Trụ 3` |
| `bnal self-test wired` | `[bnal-selftest] DRIFT — script có --self-test nhưng fdk-gate KHÔNG chạy (1): overstack_pat…` |
| `graph-engineering tests` | chạy riêng từng test: 6/7 PASS, đỏ duy nhất là `harness/tests/ge-reachability-test.sh` (rc=2) |

Nghĩa là: **đừng dùng "gate xanh" làm mốc so sánh cho thay đổi của bạn.** Chụp baseline trước khi sửa:

```bash
python3 harness/scripts/fdk-gate.py --root . --json > /tmp/gate-before.json
# … sửa …
python3 harness/scripts/fdk-gate.py --root . --json > /tmp/gate-after.json
python3 - <<'PY'
import json
b = {r["step"]: r["ok"] for r in json.load(open("/tmp/gate-before.json"))["results"]}
a = {r["step"]: r["ok"] for r in json.load(open("/tmp/gate-after.json"))["results"]}
new = [s for s in a if a[s] is False and b.get(s) is True]
fixed = [s for s in a if a[s] is True and b.get(s) is False]
print("BẠN LÀM ĐỎ THÊM:", new or "không")
print("bạn sửa xanh:   ", fixed or "không")
PY
```

Chỉ `BẠN LÀM ĐỎ THÊM: không` mới là điều kiện đủ để đi tiếp.

Gate **read-only**: `git status --porcelain` sau khi chạy vẫn sạch (đã kiểm).

### 3. Cổng sức khoẻ tổng: `medic`

```bash
python3 fdk/tools/medic.py             # tất cả
python3 fdk/tools/medic.py --list      # liệt kê probe
python3 fdk/tools/medic.py rules docs  # chỉ nhóm khớp mô tả phạm vi
python3 fdk/tools/medic.py --ci        # exit ≠ 0 nếu có mục FAIL
```

18 probe (đếm thật từ `--list`): `rules` · `coverage` · `backstop` · `docs` · `wikisummary` · `frontend` · `prose` · `narrative` · `foundation` · `selfstate` · `code` · `eval` · `freshinstall` · `capsurface` · `capproof` · `provenance` · `orchestration` · `deps`.

`medic` fail-open từng probe: probe lỗi → SKIP, không giết cả cổng. Nó cũng **chỉ chạy trên repo framework** — `ROOT = Path(__file__).resolve().parents[2]`, nên gọi từ bản global thì nó chấm chính bản global.

### 4. Sửa một luật — đường đúng

```bash
# 1. sửa luật (nguồn chân lý DUY NHẤT)
$EDITOR harness/poc-vendor-neutral/policy.yaml

# 2. sinh lại MỌI adapter từ policy — đừng sửa file trong out/ bằng tay
python3 harness/poc-vendor-neutral/gen-converters.py

# 3. self-test lõi
bash harness/poc-vendor-neutral/demo.sh         # 13 assertion
bash harness/poc-vendor-neutral/test-broad.sh   # 80 assertion

# 4. chứng adapter không drift khỏi policy
bash harness/tests/policy-converters-drift-test.sh

# 5. cổng đầy đủ
python3 harness/scripts/fdk-gate.py --root .
```

Thêm skill mới: `python3 fdk/tools/new-skill.py` (sinh vào **cả hai** cây publish cùng lúc — `skills/` canonical và `llmwiki/skills/` mirror). Kiểm parity: `python3 harness/scripts/sync-skills.py --check`.

Quyết định kiến trúc: viết ADR vào `fdk/wiki/sources/adr/`. Gate **R13** ép mọi quyết định `architecture` trong `decisions.md` phải ref một ADR.

### 5. UAT trước khi công bố năng lực mới

Gọi `/fdk-uat` **trong chat**. Nó có hai pha, và pha 2 là pha duy nhất kiểm được **giá trị mặc định**:

1. **Canary trước merge** — đẩy lên nhánh tạm `uat/<ts>`, rồi `curl` bootstrap **từ raw của chính nhánh đó** với `HARNESS_BASE` + `REPO_RAW` + `SKILLS_REF` trỏ canary. FAIL thì xoá canary, nhánh chính chưa hề bị bẩn.
2. **main-URL smoke ngay sau merge** — chạy đúng lệnh người mới gõ, **không override biến nào**. Chỉ pha này bắt được chỗ hardcode tên nhánh. FAIL thì gỡ commit khỏi remote.

Vì sao `SKILLS_REF` phải override được ở pha 1: không có nó, cài-từ-nhánh-X vẫn kéo skill của `orca` → bài UAT chấm bản CŨ rồi báo PASS cho bản MỚI. Một cổng nói dối mà vẫn xanh còn tệ hơn không có cổng.

`medic --ci` và `fresh-install-smoke.sh` cài từ working-tree qua `file://` nên **không** chứng minh được đường remote. Bản đầy đủ curl-github: `bash harness/scripts/fresh-install-smoke.sh --remote`.

### 6. Push / release

Gọi `/ship` **trong chat** — nó dừng chờ duyệt trước mọi bước side-effect. Năm mức:

| Mức | Làm gì |
|---|---|
| `ship push` | đẩy, không tag |
| `ship release` | đẩy + tag `vX.Y.Z` + `RELEASE-vX.Y.Z.md` |
| `ship pr` | đẩy nhánh + `gh pr create` |
| `ship mr` | đẩy nhánh + `glab mr create` |
| `ship merge` | liệt kê PR/MR *đến* → kéo về → gate + test → chỉ merge nếu xanh |

Checklist nó chạy trước khi đẩy: `medic --ci` → git sạch (rác `scratchpad/` không track) → selftest các engine chạm tới → version `x.x.x+1` từ tag gần nhất (chỉ mức release) → patch note trung thực có mục **Known-limitations**, không phóng đại.

⚠️ **R15 no-ai-attribution** chặn commit message ghi công cho AI: `Co-Authored-By: Claude…`, "Generated with Claude Code", 🤖. Nếu môi trường agent của bạn tự chèn trailer đó, phải gỡ trước khi commit — nếu không pre-commit/CI đỏ.

### 7. CI của repo (đọc để hiểu, đừng bê xuống dự án tiêu thụ)

`.github/workflows/harness.yml` chạy trên mọi PR và push lên `orca`, ba job:

- **selftest** — `demo.sh` + `test-broad.sh` + `wiki-graph-user-reachability-test.sh` + `memory-map-user-reachability-test.sh`
- **validate-content** — `llmwiki-validate.py files` trên các `.md` thay đổi (mode `files`, **exit 1**)
- **repo-health** — `index_sync.py` trên **cả hai** wiki (`fdk/wiki` và `llmwiki/wiki`), `wiki-health.py --fail-on broken`, `arch-scan.py`

Tên job từng ghi "demo 13 + broad 54 = 67 assertion" trong khi số thật là **13 + 80**; PR #114 đã sửa thành `13 + 80 = 93`. Nhớ cập nhật nhãn này mỗi lần thêm assertion.

Muốn cắm luật vào CI của một dự án *tiêu thụ*, đừng copy file này — dùng bản tối giản ở [04](../dym-setup-ci/SKILL.md).

## Rules
- > **Cập nhật 2026-09-07 (sau lượt fix #116–#119):** `orca` HEAD `16e1971` **xanh toàn bộ CI** lần đầu; `fdk-gate` 21/21; `template_version` 1.3.69 (installer tự cài lại global khi thấy version đổi — đã đo trên máy thật: `1.3.68 → 1.3.69`, smoke OK). Bẫy migrate (#106) và pre-commit trỏ engine đã gỡ cũng đã vá ở #117. Skill `/playwright-verify` có trong repo (#119, 88 skill).
- ⚠️ **R15 no-ai-attribution** chặn commit message ghi công cho AI: `Co-Authored-By: Claude…`, "Generated with Claude Code", 🤖. Nếu môi trường agent của bạn tự chèn trailer đó, phải gỡ trước khi commit — nếu không pre-commit/CI đỏ.
