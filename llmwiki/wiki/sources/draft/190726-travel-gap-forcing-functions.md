---
type: draft
title: "Bịt 3 lỗ travel của đường curl update — mỗi fix tự mang forcing function"
status: proposed
tags: [travel, bootstrap, capability-stamp, fdk-uat, fdk-poc, harness-lint, global-shared]
timestamp: 2026-07-19
task: T-260719-01
---

# 190726 — Bịt 3 lỗ travel đường curl update + forcing functions

**Status:** proposed
**Task:** T-260719-01
**Sequence diagram:** [190726-travel-gap-forcing-functions-seq.html](../../../html/190726-travel-gap-forcing-functions-seq.html)

## Restate

Sau UAT thật 18/07 phát hiện dự án cũ chạy curl update xong mà agent vẫn "mù" persona/council: sửa 3 lỗ travel (skill trỏ path repo-relative chết ở downstream; capability-stamp bỏ sót 4 nhóm file global; fdk-uat/fdk-poc chỉ test dự án trống) sao cho **mỗi fix kèm hàng rào máy tự gác** — user quên cũng không tái nợ, và bài test từ nay chạy trên **dự án dang dở thật** thay vì sân sạch pass-quá-dễ.

## Context

- ADR-017-global-shared-engine-repo-data-travel (`fdk/wiki/sources/adr/ADR-017-global-shared-engine-repo-data-travel.md`) — engine 1 bản ở `~/.claude/harness/`, repo chỉ giữ data + stamp (council-036/038, GH#63 v4). Quyết định ĐÚNG, giữ nguyên; lỗ nằm ở chỗ **văn bản 34 skill chưa dời theo kiến trúc**.
- ADR-005-logger-and-capabilities-travel-downstream (`fdk/wiki/sources/adr/ADR-005-logger-and-capabilities-travel-downstream.md`) — "không vào CAPABILITIES.md → user vĩnh viễn không biết năng lực đó tồn tại"; đã áp cho skills, **chưa áp cho engine**.
- `harness/travel-policy.yaml` v4 — khai 3 tầng nhưng **thiếu dòng `llmwiki/personas/`** dù `install-harness.sh --global` (dòng 139) có copy → drift chính-sách↔code.
- `harness/scripts/capability-stamp.py` — forcing function "đổi surface phải bump version" ĐÃ wired vào fdk-gate + medic; surface hiện chỉ đếm skills + rules + `harness/scripts/` + hooks.
- Bằng chứng UAT tay 18/07 (`scratchpad/uat-update-path/old-proj/`): bootstrap chạy sạch, archetype resolve persona từ global OK, **nhưng** lệnh y nguyên trong skill (`python3 harness/scripts/archetype.py`) chết `No such file or directory`; 34/69 skill global dính path repo-relative, chỉ 3 skill có fallback; CAPABILITIES.md downstream 0 dòng engine.
- Bài học UAT canary 260718 (comment trong install-harness.sh): "preamble rỗng" — chính lớp lỗi này, đã từng cắn.
- **Quét mở rộng (19/07, theo yêu cầu user "chức năng khác lỗi tương tự chứ không phải riêng persona"):** đối chiếu path trong toàn bộ 69 skill global với dự án UAT thật, sau khi lọc false-positive (ví dụ minh hoạ, output path, lỗi regex `.jsonl`↔`.json`) còn lại **cùng lớp lỗi ở 2 dạng**: (a) **path chết** — `health-check` gọi `harness/scripts/health-check.py --root .` và đọc `harness/version.json`, cả hai không tồn tại per-project sau curl v4 (chỉ ở global); (b) **tín hiệu cũ tiền-v4** — `join-project` kiểm tra `test -f llmwiki/.claude/hooks/pre_tool_use.py` để suy ra "harness ON/OFF", nhưng file này KHÔNG BAO GIỜ được tạo bởi đường bootstrap v4 (hook thật fire từ global, gác bằng `.harness-stamp`) → skill báo **"harness: OFF" SAI** dù hook đang chạy thật — nặng hơn persona vì nói dối tích cực thay vì chỉ im lặng.

## Global constraints

Chép nguyên văn từ wiki/CLAUDE.md/ADR — mọi task ngầm mang theo:

- **R15 / ADR-016:** cấm Co-Authored-By / AI-attribution trong commit message (commit-msg hook chặn cứng).
- **ADR-017:** engine = GLOBAL-SHARED tại `~/.claude/harness/`; KHÔNG copy engine vào từng repo downstream; repo chỉ giữ data travel (tầng 2) + `llmwiki/.harness-stamp`.
- **Fail-open ở downstream:** mọi hook/engine chạy ở dự án người dùng phải fail-open — "install cũ thiếu tool thì bỏ qua, KHÔNG chặn" (tiền lệ code-logger, medic probe).
- **Skill 2 cây:** canonical `skills/` ↔ mirror `llmwiki/skills/` phải parity — đồng bộ qua `sync-skills.py`, medic gác (memory: parity canonical↔llmwiki mirror).
- **EVERY wiki file must have an `## Origin` section** — nguồn luôn truy được.
- **Trước push:** `medic --ci` xanh (luật cắn / drift / docs / code / eval) — checklist /ship.
- **"CI là sàn"** — rào chắn R1–R17 luôn cài, không tắt.
- **Prose rule 2026-06-27:** tài liệu người đọc (draft này, HTML) = câu đầy đủ, không caveman.

## Impact — file/module bị chạm

| File | Chạm gì |
|---|---|
| `harness/scripts/capability-stamp.py` | nới `surface()` thêm 4 nhóm file |
| `harness/travel-policy.yaml` | khai `llmwiki/personas/` vào global_shared |
| `harness/scripts/install-harness.sh` | copy resolver shim lên global (1 dòng) |
| `harness/scripts/` (file MỚI: resolver shim) | resolve repo-local → global |
| `harness/scripts/harness-lint.py` | check mới: skill trỏ engine path trần |
| 31 SKILL.md (canonical + mirror, qua sync-skills) | đổi lệnh engine sang resolver |
| `skills/fdk-uat/` + `llmwiki/skills/utils/fdk-uat.md` | thêm bài migrate (fixture dang dở) |
| `skills/fdk-poc/` + mirror | nhận cờ dùng fixture dang dở |
| file MỚI: script fixture "dự án dang dở" (dùng chung uat+poc) | dựng sân test thật-bẩn |
| `fdk/tools/build-capabilities.py` | thêm mục Engine (global) |
| `harness/version.json` | bump qua `capability-stamp --update` |

## Có thể vỡ gì (side effects)

1. **Chính commit này làm đỏ fdk-gate** — surface đổi → sha đổi → phải `capability-stamp --update` trong cùng commit (hành vi đúng thiết kế, không phải bug).
2. **Sửa 31 skill hàng loạt** → rủi ro lệch canonical↔mirror → bắt buộc đi qua `sync-skills.py`, medic bắt parity.
3. **Lint check mới false-positive** trên skill framework_only (fdk, fdk-uat, fdk-poc, new-skill, sync-template, medic…) vốn chạy hợp lệ trong repo framework → danh sách miễn trừ khai tường minh trong config, không hardcode.
4. **Resolver trên máy chưa cài global** (chưa từng bootstrap) → phải in thông báo rõ "chạy curl bootstrap trước", không stacktrace.
5. **fdk-uat lâu hơn** (2 bài thay 1) → chấp nhận: cổng release, không phải vòng dev thường.

## Non-goals

- KHÔNG đảo ADR-017 (không copy engine trở lại từng repo).
- KHÔNG đụng cơ chế npx skills / SKILLS_REF (đang đúng).
- KHÔNG tự động sửa các dự án downstream đang tồn tại — chúng nhận fix qua đúng 1 lần curl update sau khi release (đó là toàn bộ ý nghĩa của fix).
- KHÔNG thêm registry global tracking dự án (đã bác ở council-036).
- KHÔNG viết lại fdk-poc — chỉ thêm cờ nhận fixture.

## Approaches

**A. Copy engine trở lại từng repo (đảo v4).** Mọi path repo-relative trong skill sống lại, không cần sửa skill nào. Tradeoff: bloat mỗi repo, update phải re-bootstrap từng repo ("mỗi lần 1 cái" — đúng cái v4 vừa diệt), đảo ADR-017 mới 2 tuần tuổi. **Bác.**

**B. Resolver chuẩn + lint chặn tái phạm + stamp phủ đủ + UAT migrate trên fixture dang dở.** Giữ nguyên kiến trúc v4; sửa MỘT resolver thay vì nhớ 34 chỗ; mọi lối tái phạm đều có máy gác (lint tại commit, stamp tại push, uat tại release). Tradeoff: diff 31 skill một lần + 1 file shim mới. **← CHỌN — root-cause, mỗi lỗ một forcing function, không dựa trí nhớ.**

**C. Sed 34 skill sang path global tuyệt đối, không shim.** Ít file mới nhất. Tradeoff: dev framework mất khả năng test engine bản-đang-sửa (path global luôn thắng), và không có rào chống skill mới tái phạm — 6 tháng sau lại y nguyên. **Bác** (chỉ trị triệu chứng).

## Plan

- [ ] **T1 — capability-stamp phủ đủ payload global + travel-policy khai personas.** Nới `surface()`: thêm `llmwiki/personas/*.md`, `harness/validators/*.py`, `harness/*.yaml`, `fdk/tools/*.py` (khớp đúng danh sách install-harness --global thực copy); thêm dòng personas vào travel-policy.yaml; chạy `--update` bump version. *Forcing function: fdk-gate/medic đã wired — từ nay sửa persona/validator/yaml/tools mà quên bump = push đỏ kèm lệnh sửa.*
- [ ] **T2 — Resolver chuẩn + rule lint + sửa skill dính 2 dạng lỗi cùng họ.** Shim resolve repo-local → `~/.claude/harness` (một file, install-harness copy lên global); đổi skill downstream-facing sang gọi qua resolver, gồm cả (a) **31 skill trỏ path repo-relative chết** (3 skill có fallback sẵn quy về cùng convention) và (b) **skill dò tín hiệu tồn tại tiền-v4** — `join-project` (`test -f llmwiki/.claude/hooks/pre_tool_use.py`) và `health-check` (`harness/version.json` + `harness/scripts/health-check.py` per-project) đổi sang kiểm tín hiệu v4 đúng (`llmwiki/.harness-stamp` + đọc version qua global); check harness-lint mới chặn CẢ HAI dạng (path engine trần VÀ check-tồn-tại nhắm file tiền-v4 đã biết không còn được tạo, miễn trừ framework_only theo config); sync 2 cây skill. *Forcing function: skill mới viết sai (path chết hoặc tín hiệu cũ) là đỏ ngay máy dev.*
- [ ] **T3 — Fixture "dự án dang dở" dùng chung + bài migrate mặc định.** Script fixture dựng dự án thật-bẩn: wiki có nội dung + nợ (thiếu Origin, index lệch), settings.json có hook user, pre-commit sẵn, engine-in-repo đời cũ sót lại, uncommitted changes. fdk-uat chạy bài migrate MẶC ĐỊNH cạnh bài trống (8 assert tất định: không đè wiki, hook user còn, pre-commit không phá, gỡ engine cũ đúng U10, stamp đúng, persona resolve, engine chạy qua resolver, CAPABILITIES có engine); fdk-poc nhận cờ dùng cùng fixture. *Forcing function: fdk-uat là cổng /ship — release hỏng đường update tự chặn chính nó.*
- [ ] **T4 — CAPABILITIES.md downstream thêm mục Engine.** build-capabilities.py liệt kê engine từ cây global đã cài (không hardcode), mỗi dòng kèm lệnh gọi qua resolver; verify trên dự án fixture của T3. *Khép ADR-005 cho engine: agent tra bản đồ là biết có gì, gọi thế nào.*

## Requirements (FR)

- **FR-001**: capability-stamp surface PHẢI phủ 100% nhóm file mà `install-harness.sh --global` copy (skills, rules, scripts, hooks, personas, validators, yaml config, fdk/tools).
- **FR-002**: travel-policy.yaml PHẢI khai `llmwiki/personas/` ở tầng global_shared (hết drift chính-sách↔code).
- **FR-003**: Hệ PHẢI có đúng MỘT quy ước gọi engine từ skill, chạy đúng ở cả repo framework (ưu tiên bản repo-local đang sửa) lẫn downstream (fallback global), và báo lỗi dễ hiểu khi global chưa cài.
- **FR-004**: harness-lint PHẢI chặn (đỏ) skill chứa (a) path engine repo-relative trần không qua quy ước FR-003, HOẶC (b) check-tồn-tại nhắm file tiền-v4 đã biết không còn được bootstrap tạo (`llmwiki/.claude/hooks/*.py` per-project, `harness/scripts/*.py` per-project, `harness/version.json` per-project) thay vì tín hiệu v4 đúng (`llmwiki/.harness-stamp`); skill framework_only miễn trừ qua config tường minh.
- **FR-005**: fdk-uat PHẢI chạy mặc định bài migrate trên fixture "dự án dang dở" (wiki có nợ, hook user, pre-commit sẵn, engine cũ sót, uncommitted changes) với 8 assert tất định; fdk-poc PHẢI dùng được cùng fixture qua cờ.
- **FR-006**: CAPABILITIES.md sinh ở downstream PHẢI có mục Engine liệt kê từ cây global thật, mỗi dòng kèm lệnh gọi được.

## Success criteria (SC)

- **SC-001**: Dev sửa persona/validator/config mà quên bump → cú push bị chặn với thông báo nêu đúng một lệnh sửa; khắc phục dưới 1 phút — nợ không bao giờ âm thầm.
- **SC-002**: Người dùng ở dự án cũ chạy đúng MỘT lệnh curl, mở phiên mới → gọi persona/council/wikieval được ngay lần đầu, không sửa tay bất kỳ file nào.
- **SC-003**: Người viết skill mới quên quy ước engine → biết ngay tại commit trên máy mình, không phải đợi người dùng downstream báo lỗi.
- **SC-004**: Một bản release làm hỏng đường update-vào-dự-án-đang-chạy không thể tới tay người dùng — bị chặn tự động ở cổng release.
- **SC-005**: Agent vào dự án downstream trả lời đúng "mình có công cụ gì, gọi thế nào" chỉ bằng đọc CAPABILITIES.md — không cần đoán, không cần user chỉ.

Bằng chứng máy (không thay thế SC): fdk-uat 2 bài xanh; harness-lint đỏ trên skill cố tình vi phạm; capability-stamp --check đỏ khi sửa persona không bump; grep CAPABILITIES.md có mục Engine.

## Assumptions

- Resolver shim đặt trong `harness/scripts/` để tự travel theo cơ chế copy sẵn có của install-harness; tên file chốt lúc /plan. (default)
- Danh sách skill framework_only miễn trừ lint: fdk, fdk-uat, fdk-poc, new-skill, sync-template, medic, harness-tour, snapshot-push — chốt danh sách đầy đủ lúc /plan. (default)
- Fixture dang dở dựng trong thư mục scratch ngoài git-tracking, dùng mạng thật tới GitHub raw như UAT hiện tại. (default)
- Bài "dự án trống" của fdk-uat GIỮ LẠI làm smoke đường người-mới; verdict PASS đòi cả hai bài. (default — theo lời user: case trống "quá dễ pass", không đại diện, nhưng vẫn là một đường cài có thật)
- 3 skill đã có fallback (harness-update, lint, orca-onboard) quy về cùng convention trong đợt sửa 31 skill. (default)

## Agent Task Assignment

| Task | Agent (CLI) | Lý do chọn | Status |
|---|---|---|---|
| T1 — stamp surface + travel-policy | CLAUDE | đụng forcing function của cổng push — sai một ly là gate mù/kẹt cả repo | pending |
| T2 — resolver + lint + 31 skill | CLAUDE | thiết kế convention + sửa văn bản skill cần hiểu ngữ cảnh từng skill, không sed mù được | pending |
| T3 — fixture dang dở + migrate uat/poc | CLAUDE | thiết kế fixture + 8 assert là phần não; chạy lặp về sau đã là script tất định | pending |
| T4 — CAPABILITIES mục Engine | OPENCODE big-pickle | thuần cơ khí: liệt kê cây thư mục, format bảng, chạy verify script có sẵn | pending |

## Self-review

1. **Phủ yêu cầu:** 3 lỗ từ phiên audit 18/07 → T1 (lỗ c: stamp), T2 (lỗ a: path chết), T3 (lỗ 4: uat sân sạch); lỗ b (CAPABILITIES mù engine) → T4; bổ sung mid-turn #1 của user (test trên dự án dang dở thật, áp cả fdk-poc) → đã nâng T3 thành fixture dùng chung + cờ cho fdk-poc; bổ sung mid-turn #2 của user ("chức năng khác lỗi tương tự chứ không phải persona") → quét thật 69 skill, xác nhận 2 chức năng thêm (join-project báo sai trạng thái, health-check gọi path chết) cùng họ lỗi → đã nhập vào T2/FR-004 thay vì mở task riêng (cùng resolver + cùng rule lint sửa được cả cụm). Mỗi yêu cầu về đúng một task. ✓
2. **Quét placeholder:** draft sạch mọi đánh dấu để-sau; hai chi tiết cố ý dời sang /plan (tên file shim, danh sách miễn trừ đầy đủ) được khai tường minh ở Assumptions với tag (default), không phải placeholder trôi. ✓
3. **Nhất quán tên-kiểu:** "resolver"/"shim" chỉ cùng một thứ — thống nhất gọi "resolver shim" trong Plan/FR; capability-stamp/fdk-gate/medic/harness-lint gọi đúng tên file thật xuyên suốt. ✓

## Origin

- **Draft:** `wiki/sources/draft/190726-travel-gap-forcing-functions.md`
- **Nguồn trực tiếp:** phiên audit 18-19/07/2026 — UAT tay đường update tại `scratchpad/uat-update-path/old-proj/` (bằng chứng còn nguyên) + grep 34/69 skill global + đọc capability-stamp.py/install-harness.sh/travel-policy.yaml; bổ sung mid-turn của user về fixture dang dở.
- **Commit:** _(filled by verify-before-commit)_
- **Date promoted:** _(filled by verify-before-commit)_
