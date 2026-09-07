---
name: dym-setup-maintain
description: "Nâng bản, migrate dự án cũ (/harness-update --self-heal rc 0/3/4/1), công cụ nào chạy được ở downstream, 16 tool bị gỡ khỏi global, trần token, gỡ. Gọi khi: 'update overstack', 'nâng bản harness', 'migrate llmwiki cũ', 'health-check'."
disable-model-invocation: true
---

# Skill: dym-setup-maintain — Nâng bản, migrate dự án cũ, và những gì bạn KHÔNG chạy được ở downstream

## When to use
- **Tại sao chạy:** overstack cập nhật thường xuyên; bản cũ để lâu thì luật mới không xuống tới dự án, và bạn không biết mình đang bị gác bởi bao nhiêu luật.
- **Sinh ra gì:** engine global mới ở `~/.claude/harness/`, lõi per-project mới ở `.harness/`, `CAPABILITIES.md` sinh lại, và (khi có nợ) các trang wiki được backfill `## Origin` / frontmatter / dòng index.
- Gọi qua hub: `/dym-setup maintain` — hoặc trực tiếp `/dym-setup-maintain` nếu đã symlink riêng.

## Steps
### 1. Update thường: chạy lại đúng lệnh cài

> **Cập nhật 2026-09-07 (sau lượt fix #116–#119):** `orca` HEAD `16e1971` **xanh toàn bộ CI** lần đầu; `fdk-gate` 21/21; `template_version` 1.3.69 (installer tự cài lại global khi thấy version đổi — đã đo trên máy thật: `1.3.68 → 1.3.69`, smoke OK). Bẫy migrate (#106) và pre-commit trỏ engine đã gỡ cũng đã vá ở #117. Skill `/playwright-verify` có trong repo (#119, 88 skill).

Installer **idempotent** — chạy lại là update.

```bash
curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash
```

Cài mới hoàn toàn (gỡ cũ rồi cài):

```bash
curl -fsSL .../bootstrap.sh | bash -s -- --clean
```

✅ **Từ `orca` commit `d8f1967` (PR #114) trở đi, chạy lại installer là CÁCH SỬA bẫy dot-layout** — không cần bản vá tay ở [01](../dym-setup-install/SKILL.md) mục 4 nữa. Với bản cài cũ hơn thì ngược lại: installer ghi đè `.claude/settings.json` + `.pre-commit-config.yaml` bằng snippet đường không-dấu-chấm, nên phải áp lại bản vá sau mỗi lần chạy.

Xác nhận bản đang chạy:

```bash
cat .llmwiki/.harness-stamp                       # {"schema": 1, "guarded_by": "1.3.68"}
python3 -c "import json;print(json.load(open('$HOME/.claude/harness/version.json')).get('template_version'))"
head -3 CAPABILITIES.md
```

### 2. Dự án cũ (đã có `llmwiki/` từ trước harness) — `/harness-update`

Gọi `/harness-update` **trong chat**. Nó chạy một lệnh shell duy nhất rồi đọc mã thoát:

```bash
test -f harness/scripts/install-harness.sh \
  && bash harness/scripts/install-harness.sh . --self-heal \
  || { git clone -q --depth 1 -b orca https://github.com/rheinmir/setup.git /tmp/llmwiki-tpl \
       && bash /tmp/llmwiki-tpl/harness/scripts/install-harness.sh . --self-heal ; rm -rf /tmp/llmwiki-tpl; }
```

Nhánh clone gần như luôn được dùng ở downstream: `install-harness.sh` nằm trong nhóm **framework-only**, bản global cố tình **không** mang nó (xem mục 4).

`--self-heal` gộp cả vòng vào một process: cài L0–L4 → audit (Origin + index + OKF) → tự backfill nợ → re-audit một lần → activate + smoke. Không có cờ này thì nó giữ hành vi cũ: audit rồi thoát 3 nếu còn nợ.

**Mã thoát — đọc rồi mới hành động, đừng re-run mù:**

| rc | Nghĩa | Làm gì |
|---|---|---|
| **0** | sạch, đã backfill xong | xong; sang bước nghiệm thu |
| **3** | còn nợ self-heal không tự sửa được (conflict file, `type` OKF không suy được) | danh sách nằm ngay trong output — sửa tay **một lần** rồi chạy lại |
| **4** | auto-smoke thất bại: 3 luật lẽ ra phải chặn mà không chặn | rào đang thủng — dừng, không dùng tiếp |
| **1** | lỗi hạ tầng (mạng, python3, validator hỏng) | dừng, báo nguyên văn, đừng đoán |

Nghiệm thu sau update:

Trong output bước trên, tìm dòng `[audit] backfill xong — Origin:<a> index:<b> OKF:<c>` — đó là số nợ đã tự trả. Rồi sinh lại bản đồ năng lực để agent thấy đúng đồ nghề sau update:

```bash
python3 ~/.claude/harness/hooks/build-capabilities.py --root .   # sinh lại CAPABILITIES.md
```

Đường cài global có smoke tự chạy; log xanh sẽ có dòng:

```
[harness] GLOBAL smoke OK: no_write_raw chặn đúng (rc=2)
```

Dòng đó **là** bằng chứng luật còn cắn ở tầng global. Không thấy nó thì đừng tin bảng "3 trụ ✓".

### 3. Kiểm tra sức khoẻ — công cụ nào dùng được ở đâu

| Lệnh | Chạy được ở dự án bạn? | Ghi chú |
|---|---|---|
| `bash .harness/poc-vendor-neutral/demo.sh` | ✅ | 13 assertion, nhanh |
| `bash .harness/poc-vendor-neutral/test-broad.sh` | ✅ | 80 assertion |
| `python3 $V claude-hook` (xem [02](../dym-setup-guardrail-cli/SKILL.md)) | ✅ | cách trực tiếp nhất để hỏi "luật còn cắn không" |
| `/harness-tour` (chat) | ✅ | Claude tự cố tình vi phạm cho bạn xem, tự dọn |
| `python3 ~/.claude/harness/harness/scripts/health-check.py --root . --offline` | ⚠️ | đòi `.template-manifest.json`; dự án thường **rc=1** + `manifest không tồn tại`. Đây là công cụ cho repo đồng bộ template, không phải cho dự án tiêu thụ |
| `harness-doctor.py --ci` | ❌ | framework-only, không có trong bản global |
| `medic` | ⚠️ | có trong global nhưng `ROOT = parents[2]` → nó chấm **chính bản global**, không chấm dự án bạn |

### 4. 16 tool cố tình bị gỡ khỏi bản global (+ 7 mục không bao giờ được chép sang)

Log cài in `GLOBAL: gỡ 16 tool framework_only`. Danh sách **16** đó là biến `STRIP_TIER3` trong `install-harness.sh` (đếm lại khi audit — bản đầu của tài liệu này gộp nhầm thành 23):

**`harness/scripts/` (10):** `adapt-registry.py` · `arch-scan.py` · `audit.py` · `bnal-selftest.py` · `dispatch-verify.py` · `fdk-gate.py` · `harness-doctor.py` · `harness-lint.py` · `skill-registry.py` · `sync-skills.py`

**`fdk/tools/` (6):** `build-cheatsheet.py` · `build-docs-index.py` · `build-health-dashboard.py` · `build-overstack-docs.py` · `new-skill.py` · `whiteboard-skill-map.py`

Ngoài ra **7 mục không nằm trong danh sách gỡ nhưng cũng vắng ở global** — chúng đơn giản không được chép sang ngay từ đầu: `harness/scripts/{install-harness.sh, fresh-install-smoke.sh, tour.sh, lib/}` và `fdk/tools/{fdk-kit.sh, sync-skill.sh, artifacts.config.yaml}`. Hệ quả với bạn giống nhau: không gọi được từ `~/.claude/harness/`.

Đây là **thiết kế**, không phải cài thiếu: tầng 3 (FDK) chỉ chạy ở repo framework. Cần chúng thì clone `rheinmir/setup` và đọc [06](../dym-setup-contributor/SKILL.md).

Còn lại ở global mà consumer dùng được: 58 script trong `harness/scripts/` (gồm `code-logger.py`, `wiki-health.py`, `wiki-graph.py`, `token-budget.py`, `loop-runner.py`, `council.py`…) và 17 tool trong `fdk/tools/`.

### 5. Trần token — mặc định là CẢNH BÁO, không chặn

Installer chạy `token-budget.py configure --if-tty`. Không có terminal (curl | bash trong script, CI) thì nó im lặng giữ mặc định:

```
[token-budget] không có terminal — giữ trần mặc định (mode: warn).
```

Mọi trần trong `token-budget.config.yaml` đều gắn `# ASSUMPTION (not verified)`. Muốn nó thật sự chặn thì phải tự chọn:

```bash
python3 ~/.claude/harness/harness/scripts/token-budget.py configure --root .
```

### 6. Gỡ

```bash
bash .harness/poc-vendor-neutral/uninstall.sh .              # CI + pre-commit + hook trong settings.json + lõi
bash .harness/poc-vendor-neutral/uninstall.sh . --keep-core  # chỉ gỡ wiring, giữ .harness/poc-vendor-neutral/
bash .harness/poc-vendor-neutral/uninstall.sh . --purge-bak  # xoá luôn các file .bak installer tạo
```

Nó **không** đụng `~/.claude/harness/`, `~/.claude/skills/`, `~/.claude/settings.json` hay symlink `~/.openclaude/skills`. Muốn sạch hoàn toàn thì xoá tay — nhớ khôi phục `~/.claude/settings.json` từ bản `.bak.*` mà installer để lại.

## Rules
- > **Cập nhật 2026-09-07 (sau lượt fix #116–#119):** `orca` HEAD `16e1971` **xanh toàn bộ CI** lần đầu; `fdk-gate` 21/21; `template_version` 1.3.69 (installer tự cài lại global khi thấy version đổi — đã đo trên máy thật: `1.3.68 → 1.3.69`, smoke OK). Bẫy migrate (#106) và pre-commit trỏ engine đã gỡ cũng đã vá ở #117. Skill `/playwright-verify` có trong repo (#119, 88 skill).
