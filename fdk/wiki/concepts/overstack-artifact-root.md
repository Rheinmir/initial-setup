---
type: concept
title: .overstack/ — một gốc cho mọi artifact sinh ra / kéo về, và dym-sync
status: implemented
tags: [layout, artifacts, doyourmagic, dym, drift, migration, sync-template]
timestamp: 2026-09-08
id: overstack-artifact-root
relations:
  - {rel: depends-on, to: harness-enforcement-floor}
  - {rel: relates-to, to: onboarding-tour}
---

# `.overstack/` — một gốc cho mọi thứ framework SINH RA hoặc KÉO VỀ

Quy ước từ 2026-09-08: thứ gì không phải lõi framework, không phải tri thức dự án, mà là **artifact** (sinh bằng code, hoặc kéo từ kho ngoài) thì nằm dưới **một** thư mục ẩn `.overstack/`. Trước đó chúng rải ở gốc repo (`doyourmagic/`, `.orca-onboard/`, `.understand-anything/`, `.overstack-kit/`) và đồ thị onboarding phải thêm luật riêng cho từng cái; layer catch-all phình từ 14 lên 120 node chỉ vì không có quy ước.

| Thư mục | Gì | Ai sinh / kéo |
|---|---|---|
| `.overstack/doyourmagic/<repo>/` | bundle skill cho tool ngoài (hub + sub-skill, `workflows.md`) | skill `/doyourmagic`, đồng bộ với kho [rheinmir/dym](https://github.com/Rheinmir/dym) |
| `.overstack/doyourmagic/dym/SKILL.md` | **meta-hub `/dym`** — bảng domain → hub → slug, skill duy nhất model-invocable | `dym-sync.py index` |
| `.overstack/onboard/` | input + script phase 1 của `/orca-onboard` (`parse.py`, `build_graph.py`) | skill `/orca-onboard` |
| `.overstack/graph/` | `knowledge-graph.json`, `ONBOARDING.md`, `meta.json` | `build_graph.py` |
| `.overstack/kit/` | sandbox clone overstack cho `/fdk` (gitignore) | `fdk-kit.sh pull` |

**Không dời** `.claude/`, `.github/`, `.agent`, `.cursor`: vị trí do tool ngoài quy định.

## Đổi đường dẫn độc quyền mà không dặn ai — `PATH_MIGRATIONS`
`harness/scripts/sync-template.py` có bảng `PATH_MIGRATIONS = [(cũ, mới), …]` và `migrate_paths()`: chạy **mỗi lần sync**, trước mọi bước hậu-sync; `git mv` giữ lịch sử, không có git thì `shutil.move`; idempotent (đích đã có thì bỏ qua, người dùng tự dời rồi). Lần sau framework dời một thư mục độc quyền, chỉ thêm một dòng vào bảng — downstream sync là tự theo. `--selftest` chứng idempotent.

## Bundle tool ngoài: dạng skill + drift + định tuyến — `dym-sync.py`
`harness/scripts/dym-sync.py` (stdlib, đi downstream qua manifest, `--selftest`):

| Lệnh | Việc |
|---|---|
| `lint [bundle]` | bundle phải có `skills/<hub>/SKILL.md` với `domains:`; sub-skill có `name` + `description`. rc 1 |
| `migrate <bundle> --domains a,b` | dạng cũ `NN-*.md` → `skills/<hub>-<slug>/SKILL.md` (thân giữ nguyên) + hub sinh theo template |
| `index` | sinh meta-hub `/dym` từ `domains:` của từng hub |
| `install [dym\|<bundle>] [--auto slug,..]` | symlink vào `.claude/skills/`; `--auto` bỏ `disable-model-invocation` để agent tự nạp theo `description` |
| `check [--yes] [--json]` | đĩa ↔ baseline ↔ dym (clone `--depth 1`): NEW-LOCAL · SAME · LOCAL · REMOTE-AHEAD · CONFLICT; hỏi y/N rồi push; rc 3 khi có việc cần quyết |
| `push <bundle> [--yes]` | copy vào clone → nhánh `dym/<bundle>` → PR (`gh`) → ghi `.dym-baseline.json` |

**Định tuyến theo domain, không đẻ engine.** Mỗi hub khai `domains: [chart, report]`. `/dym` là skill **duy nhất** model-invocable (1 dòng context) — agent thấy "vẽ chart" thì gọi `/dym`, đọc bảng, đi tiếp vào `dym-lieflat-charts`, hub chỉ tới đúng một sub-skill. 9 bundle × 70 sub-skill vẫn 0 dòng context. Frontend/UI: `hallmark` vẫn là sàn, bundle chỉ là flavour bên trên.

**Drift là việc người quyết.** Hook Stop (`dym_drift_mirror`) chỉ nhắc một dòng khi phiên đụng `.overstack/doyourmagic/`, fail-open, debounce như medic; không tự push lên kho chung.

## Đã đo (2026-09-08)
- Đồ thị onboarding: 1204 node, 17 → 16 layer, catch-all 120 → 15 (chỉ còn file gốc repo).
- 9 bundle migrate sang dạng skill, 14 domain; `check` trước push: 8 NEW-LOCAL + impeccable DIFF (7/9 chưa bao giờ lên dym).
- Bỏ `embed-ollama.py`/`embed-voyage.py` cùng đợt: đường embedding chưa ai bật, test treo 30s chờ port chết.

## Origin
- **Source:** phiên 2026-09-08 (nghiên cứu graph generator `.overstack/onboard/tmp/build_graph.py` → gốc bệnh là layout)
- **Commit:** a887454 (layout + PATH_MIGRATIONS), 8071f3e (dym-sync), 700b0e6 (bỏ embed)
- **Date:** 2026-09-08
