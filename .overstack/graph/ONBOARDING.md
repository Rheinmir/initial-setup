# ONBOARDING — overstack (`rheinmir/setup`)

> Sinh bởi `/orca-onboard` ngày 2026-07-28 tại commit `9032ae4`, nhánh `orca`.
> Nguồn: static parse 846 file tracked + 620 commit lịch sử (từ 2026-04-28) + đọc tài liệu gốc.
> Không có bước nào đoán đường dẫn — mọi file nhắc trong trang này đều tồn tại trên đĩa.

---

## 1. Dự án này là gì

**overstack** là một *lớp khung đặt lên trên dự án của bạn* (a stack you put **over** your project). Nó không phải thư viện bạn import, cũng không phải service bạn chạy. Nó là tập hợp các file được cài vào thư mục gốc của một dự án bất kỳ để biến AI agent đang làm việc trong đó — Claude Code, opencode, Antigravity, Cursor — thành một cộng sự kỹ thuật **tự kỷ luật**.

Chữ "tự kỷ luật" ở đây có nghĩa rất cụ thể: agent không được phép tự chọn có tuân thủ hay không. Kỷ luật được cài đặt bằng code tất định chạy trước và sau mỗi hành động của agent, tốn 0 token, và agent không có quyền phủ quyết.

Bốn năng lực mà overstack cấp cho một agent:

1. **Trí nhớ dài hạn** — thư mục `llmwiki/` là một nền tri thức có cấu trúc (concepts / entities / sources / adr / draft) mà agent đọc trước khi hành động và ghi vào sau khi học được điều mới. Nhờ vậy tri thức không chết theo phiên chat.
2. **Nguyên tắc không thể phá** — thư mục `harness/` chứa guardrail tất định: 18 rule khai báo trong `policy.yaml`, được 15 validator Python thuần thực thi qua hook của vendor, có CI và pre-commit làm sàn phía dưới.
3. **Tay nghề đóng gói sẵn** — thư mục `skills/` chứa 84 skill dạng `SKILL.md`, gọi bằng `/<tên>`. Mỗi skill là một quy trình đã được viết ra thành lời, để agent không phải ứng biến lại từ đầu mỗi lần.
4. **Điều phối nhiều agent** — tích hợp Orca (worktree/workspace/terminal) cùng các skill `orca-*` để chia việc cho nhiều agent chạy song song mà vẫn có cổng người duyệt.

**Ngôn ngữ và quy mô:** 846 file được phân tích — 585 Markdown, 125 Python, 39 Shell, 32 YAML, 30 JSON, 8 HTML. Đây là một dự án nơi **tài liệu và cấu hình chính là sản phẩm**, còn Python/Shell là bộ máy thực thi. Ai quen đọc repo theo hướng "tìm hàm main" sẽ lạc — cửa vào thật là `bootstrap.sh` và `policy.yaml`.

**Nhánh làm việc chính là `orca`**, không phải `main`. Mọi URL cài đặt trong tài liệu đều trỏ vào `orca`, nên nhánh này vừa là nhánh phát triển vừa là nhánh phát hành.

---

## 2. Một dòng cài đặt — hợp đồng với người dùng

Toàn bộ trải nghiệm người mới gói trong một lệnh chạy tại thư mục gốc dự án đích:

```bash
curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/harness/poc-vendor-neutral/bootstrap.sh | bash
```

Lệnh này cài hoặc cập nhật **cả ba trụ** và in bảng trạng thái ba trụ ở cuối. Cờ tuỳ chọn: `--harness-only` (chỉ guardrail, không đụng skill global), `--clean` (gỡ cũ rồi cài mới), `--vendor claude,opencode` (ép vendor thay vì tự dò), `uninstall`.

Điểm cần nhớ về **phạm vi cài đặt**, vì đây là nguồn hiểu lầm phổ biến nhất:

| Trụ | Cài ở đâu | Hệ quả |
|---|---|---|
| harness | per-project (`.claude/settings.json` của dự án) | mỗi dự án có guardrail riêng |
| llmwiki | per-project (thư mục `llmwiki/`) | tri thức đi theo repo |
| skills | **global** (`~/.claude/skills`) | dùng chung mọi dự án trên máy |

Và một hiểu lầm nữa được tài liệu nhấn mạnh nhiều lần: **harness là HOOK, không phải MCP**. Cài xong mà không thấy gì trong `/mcp` là đúng — kiểm bằng `/hooks`.

`harness/downstream-contract.yaml` ghi lại hợp đồng này. Đổi bootstrap là đổi trải nghiệm của mọi người dùng đã cài, nên đây là file nhạy cảm nhất repo dù churn không cao.

---

## 3. Kiến trúc năm lớp

`harness/harness.md` mô tả kiến trúc harness theo năm lớp, và đây là xương sống để hiểu toàn bộ repo:

```
L0 POLICY   policy.yaml — 18 rule bất biến, khai báo, không phụ thuộc vendor
L1 SESSION  adapter per vendor (Claude Code: hooks + permissions.deny) → validators/
L2 REPO     .pre-commit-config.yaml — backstop vendor-neutral, gate mọi commit
L3 AUDIT    JSONL audit tự động — log bằng máy, không nhờ model tự nhớ
L4 EVALS    wiki-health (0 token) + promptfoo golden questions (định kỳ)
```

Ý tưởng cốt lõi, viết trong `harness/poc-vendor-neutral/README.md`: **logic chặn không nằm trong MCP, cũng không nhúng vào một vendor — nó là một CLI lõi đọc `policy.yaml`, và mỗi vendor chỉ là caller mỏng gọi vào**. Vì thế cùng một luật cắn được ở Claude Code, ở opencode, và ở CI mà không phải viết lại ba lần.

Ba tầng phòng thủ chồng lên nhau có chủ đích: hook vendor bắt sớm nhất (trước khi ghi file), pre-commit bắt khi vendor bị tắt hoặc người dùng gõ `git commit` tay, CI bắt khi cả hai bị bỏ qua. Một tầng hỏng thì hai tầng còn lại vẫn chặn.

Mọi hook đều **fail-open**: lỗi hạ tầng thì exit 0 và ghi cảnh báo, không phá phiên làm việc. Đây là đánh đổi có ý thức — guardrail hỏng thầm lặng vẫn tốt hơn guardrail làm agent không dùng được.

---

## 4. Bản đồ 15 tầng (layers)

Mỗi file thuộc đúng một tầng. Sắp theo thứ tự đọc hợp lý cho người mới.

| Tầng | Số file | Là gì |
|---|---:|---|
| `project-bootstrap` | 14 | README, CLAUDE.md, và prompt dựng dự án mới `00`→`03` + `setup.md` |
| `harness-core` | 15 | Lõi CLI vendor-neutral + installer một dòng (`poc-vendor-neutral/`) |
| `harness-policy` | 39 | `policy.yaml` 18 rule, `foundation.yaml`, `mechanisms.yaml`, các `*.config.yaml` |
| `harness-validators` | 15 | 15 validator Python thuần thực thi từng rule |
| `harness-scripts` | 68 | Script vận hành: cài đặt, fdk-gate, sync-skills, council, loop-runner, eval |
| `harness-quality` | 46 | Test fire-drill, evals promptfoo, metrics JSONL |
| `vendor-adapter` | 28 | Hook Claude Code (`llmwiki/.claude/hooks/`) + `.claude/settings.json` |
| `skills` | 199 | 84 skill canonical dạng `SKILL.md` cùng asset đi kèm |
| `skills-mirror` | 84 | Bản mirror trong `llmwiki/skills/` để đi kèm khuôn wiki |
| `knowledge-base` | 224 | `llmwiki/wiki/` — concepts, entities, sources, adr, draft, index, log |
| `llmwiki-rules` | 8 | `llmwiki/CLAUDE.md`, `llmwiki/AGENT.md` — rule agent nạp mỗi phiên |
| `fdk` | 27 | Framework Dev Kit — 19 tool sinh docs/capabilities, `medic.py` |
| `fdk-wiki` | 60 | Wiki RIÊNG của framework: ADR-001..010, concepts, decisions |
| `docs-html` | 12 | HTML self-contained sinh bằng code: `overstack.html`, `wiki-graph.html` |
| `ci-gate` | 7 | GitHub Actions, pre-commit, `.template-manifest.json` |

Quan sát đáng chú ý: **`knowledge-base` (224) và `skills` (199) chiếm gần một nửa repo**. Đây không phải repo code có kèm docs — đây là repo tri thức có kèm bộ máy thực thi.

---

## 5. Mười tám rule — luật là dữ liệu, không phải code

`harness/policy.yaml` là nguồn chân lý duy nhất. Thêm luật nghĩa là thêm một entry ở đây rồi nối validator, chứ không rải `if` khắp hook.

| Rule | Tên | Chặn cứng? | Bắt ở đâu |
|---|---|---|---|
| R1 | `no-write-raw` | ✅ | PreToolUse — cấm ghi vào `llmwiki/raw/` |
| R2 | `origin-required` | ✅ | PreToolUse — mọi trang wiki phải có `## Origin` |
| R3 | `index-sync` | ✅ | Stop — `index.md` phải khớp file trên đĩa |
| R4 | `log-append` | tự động | PostToolUse — ghi `audit.jsonl` và sinh `log.md` |
| R5 | `folder-structure` | ✅ | PreToolUse — cấm tạo thư mục lạ trong wiki |
| R6 | `verify-before-commit` | cổng commit | pre-commit + CI + skill `/verify-before-commit` |
| R7 | `proposal-complete` | ✅ | PreToolUse — draft phải đủ mục bắt buộc |
| R8 | `pattern-sync-health` | báo cáo | SessionStart — kiểm drift so với remote |
| R9 | `okf-frontmatter` | ✅ | PreToolUse — frontmatter đúng schema |
| R10 | `docs-gate` | nhắc | UserPromptSubmit — định kỳ nhắc sinh docs |
| R11 | `seq-html-glass-style` | | HTML phải theo design system glass |
| R12 | `pull-before-change` | | kéo trước khi sửa, chống ghi đè |
| R13 | `decision-to-adr` | ✅ | quyết định kiến trúc phải ref một ADR |
| R14 | `patterns-protected` | | `llmwiki/patterns/` là vùng bảo vệ |
| R15 | `no-ai-attribution` | ✅ | cấm ghi công AI vào commit |
| R16 | `report-show-path` | | report phải in đường dẫn file thật |
| R17 | `problem-tree-flush` | | vấn đề xuyên phiên phải được flush ra cây |
| R18 | `plan-executable` | | PLAN phải thi hành được, không mơ hồ |

R15 đáng chú ý về mặt lịch sử: log cho thấy đã có một lần `git filter-repo` cắt 50 dòng `Co-Authored-By` khỏi lịch sử. Luật này sinh ra từ một quyết định đã trả giá bằng viết lại lịch sử repo.

Validator tương ứng nằm ở `harness/validators/`: `no_write_raw.py`, `origin_required.py`, `index_sync.py`, `folder_structure.py`, `okf_frontmatter.py`, `proposal_complete.py`, `decision_adr.py`, `patterns_guard.py`, `no_ai_attribution.py`, `report_show_path.py`, `task_lifecycle.py`, `agent_claude_parity.py`, `duplicate_basename.py`, `travel_policy_sync.py`, `code_health.py`.

---

## 6. Các luồng chính

### 6.1 Luồng cài đặt (người dùng mới)

```
curl bootstrap.sh | bash
  ├─ dò vendor (claude / opencode / …)
  ├─ trụ 1 harness  → install.sh → chép validators + lõi, ghi hook vào .claude/settings.json
  ├─ trụ 2 skills   → npx skills add rheinmir/setup#orca --global --all → ~/.claude/skills
  ├─ trụ 3 llmwiki  → seed khung wiki vào ./llmwiki/
  └─ in bảng trạng thái 3 trụ
```

File liên quan: `harness/poc-vendor-neutral/bootstrap.sh`, `install.sh`, `uninstall.sh`, `harness/scripts/install-harness.sh` (bản per-project đầy đủ L0–L4), `harness/version.json` (đánh dấu phiên bản template đã cài).

### 6.2 Luồng chặn một hành động sai (runtime)

```
Agent gọi Write("llmwiki/raw/x.md")
  → hook PreToolUse: llmwiki/.claude/hooks/pre_tool_use.py
    → gọi lõi harness/poc-vendor-neutral/bin/llmwiki-validate.py
      → đọc policy.yaml, khớp R1 no-write-raw
        → verdict DENY, in stderr viết CHO AGENT ĐỌC (không phải cho người)
  → Write không bao giờ xảy ra
```

Chi tiết quan trọng: thông điệp lỗi được viết để agent đọc và tự sửa, không phải để người debug. Đây là lý do harness hoạt động mà không cần người ngồi canh.

Còn `Stop` hook (`llmwiki/.claude/hooks/stop.py`) chặn ở đầu kia: agent không được kết thúc lượt nếu `index.md` lệch so với đĩa (R3). Nghĩa là "quên cập nhật mục lục" là trạng thái không thể tồn tại.

### 6.3 Luồng làm việc hằng ngày — propose → gate → dispatch

Đây là quy trình chuẩn của overstack, và cũng là thứ được sửa nhiều nhất (`skills/orca-workflow/SKILL.md` churn 32 — đứng thứ 8 toàn repo):

```
/propose        viết draft vào llmwiki/wiki/sources/draft/ rồi DỪNG, chờ người duyệt
   ↓ (người gật)
/plan           mở draft thành brief thi hành được: đường dẫn chính xác, bước 2–5 phút,
                khối Interfaces cho task hàng xóm — để agent CLI rẻ không hỏi lại được vẫn làm đúng
   ↓
dispatch        giao cho agent (Orca worktree / opencode / agy) chạy song song
   ↓
/verify-before-commit   typecheck + lint + smoke, promote draft thành wiki thật,
                        điền Origin/Commit, rồi mới mở cổng commit (R6)
```

Human-in-the-loop nằm ở **cổng**, không nằm ở lời nhắc. Agent không thể "quên hỏi" vì `/propose` dừng bằng cấu trúc chứ không bằng lời dặn.

### 6.4 Luồng tự bảo trì framework

```
/fdk              front-door: pre-flight + inventory live
python3 harness/scripts/fdk-gate.py    definition-of-done cho MỌI thay đổi framework
python3 fdk/tools/medic.py             cổng sức khoẻ tổng — chứng minh luật CÒN CẮN
```

`medic.py` là tuyến phòng thủ cuối và là file được depend nhiều nhất trong `fdk/` (in-degree 33). Nó không kiểm tra "file có tồn tại không" mà chạy **fire-drill**: cố tình vi phạm rồi xác nhận bị chặn. Bài học đằng sau nằm trong commit `fix(honesty): vá TOÀN BỘ lớp lỗi "tồn tại ≠ dùng được" — 8 chỗ, theo mức nguy hiểm` và `feat(deps): quảng cáo năng lực phải THĂM DÒ, không được kiểm sự tồn tại`.

### 6.5 Luồng sinh tài liệu

```
fdk/tools/build-capabilities.py   → fdk/CAPABILITIES.md      (đếm skill/rule/tool từ đĩa)
fdk/tools/build-overstack-docs.py → llmwiki/html/overstack.html
fdk/tools/build-wiki-graph.py     → llmwiki/html/wiki-graph.html (vector concept↔code)
fdk/tools/build-skill-search.py   → fdk/skills.search.json (BM25 index cho find-skill)
```

Nguyên tắc: **tài liệu sinh bằng code, đọc thẳng từ đĩa**, nên bảng skill/rule không thể nói dối. `CAPABILITIES.md` mở đầu bằng dòng `<!-- SINH BẰNG CODE: build-capabilities.py — ĐỪNG sửa tay -->`.

---

## 7. File nóng — nơi công việc thật diễn ra

Đo bằng số commit chạm vào file trong 365 ngày. Đây là chỉ báo tốt nhất cho "sửa ở đâu thì đụng nhiều thứ".

| Churn | File | Tầng | Vì sao nóng |
|---:|---|---|---|
| 166 | `llmwiki/wiki/log.md` | knowledge-base | Nhật ký append-only, R4 ghi mỗi phiên — nóng là bình thường, không phải mùi xấu |
| 99 | `llmwiki/html/overstack.html` | docs-html | Sinh lại mỗi lần skill/rule đổi (`chore(docs): regen overstack.html` xuất hiện nhiều lần) |
| 85 | `llmwiki/wiki/index.md` | knowledge-base | R3 ép khớp đĩa, nên mọi trang wiki mới đều chạm |
| 67 | `fdk/tools/build-overstack-docs.py` | fdk | Bộ sinh docs — mọi thay đổi trình bày đi qua đây |
| 66 | `fdk/CAPABILITIES.md` | fdk | Sinh lại mỗi lần thêm skill/rule/tool |
| 55 | `harness/version.json` | harness-policy | Đánh dấu phiên bản template, bump mỗi lần đổi khuôn |
| 34 | `llmwiki/CLAUDE.md` | llmwiki-rules | Rule hành vi agent — chỉnh liên tục theo bài học mới |
| 32 | `skills/orca-workflow/SKILL.md` | skills | Quy trình chủ đạo, cùng mirror `llmwiki/skills/orchestrate/orca-workflow.md` (cũng 32) |
| 31 | `llmwiki/AGENT.md` | llmwiki-rules | Bản rule cho agent không phải Claude |
| 30 | `harness/scripts/install-harness.sh` | harness-scripts | Đường cài per-project |
| 30 | `skills/orca-onboard/SKILL.md` | skills | Chính skill sinh ra trang này |
| 29 | `fdk/wiki/log.md` | fdk-wiki | Nhật ký riêng của framework |

**Cặp file luôn đi cùng nhau** (co-change ≥ 4 lần, 115 cặp được phát hiện): `skills/<tên>/SKILL.md` ↔ `llmwiki/skills/<nhóm>/<tên>.md`. Đây là quan hệ canonical↔mirror. Sửa một bên mà quên bên kia là lỗi **mirror-drift** — CI có job riêng bắt lỗi này (`fix(ci): sync canonical skills/lint/SKILL.md — CI skills-sync đỏ`).

**File được depend nhiều nhất** (in-degree, bỏ qua index/log): `fdk/tools/medic.py` (33), `harness/scripts/install-harness.sh` (33), `fdk/tools/build-capabilities.py` (29), `harness/version.json` (28), `harness/scripts/code-logger.py` (27), `llmwiki/CLAUDE.md` (27). Sửa những file này là thay đổi lan rộng — dùng `/impact-check` hoặc `/safe-change` trước.

---

## 8. Đang làm gì gần đây

Đọc 60 commit subject 90 ngày gần nhất, có bốn dòng công việc rõ rệt:

**(a) Artifact provenance event log** — chuỗi `feat(provenance-log): T1..T5`, thiết kế sổ sự kiện git-native theo pattern Kafka, chọn CAP = AP, dùng `.gitattributes merge=union` để nhiều writer merge được qua git branch. Đã wiring vào Stop hook và `/lint` bước 8f. Draft gốc: `llmwiki/wiki/sources/draft/220722-artifact-provenance-eventlog.md` cùng file `-PLAN.md`. T6 hoãn, chờ trả nợ U-05.

**(b) Decision anchoring** — chuỗi `feat/fix(decision-anchoring): T1..T9`, neo quyết định kiến trúc vào symbol code thật với bốn trạng thái liveness LIVE/STALE/ORPHAN/UNAVAILABLE, dựa trên code-graph MCP. Đã đánh dấu implemented. Có một issue mở về metric adoption: `llmwiki/wiki/sources/draft/210721-decision-anchoring-adoption-metric.md`.

**(c) Trung thực về năng lực** — nhóm commit `fix(honesty)`, `feat(deps)`, `fix(code-graph)` xoay quanh một bài học đắt: **"tồn tại ≠ dùng được"**. code-graph MCP hỏng nhiều tuần trong khi mọi phiên vẫn bị lùa vào dùng nó, vì code chỉ kiểm tra server có được khai báo trong config hay không. Kết quả: `harness/scripts/dep-health.py` giờ **thăm dò thật** (mở DB, kiểm bảng `symbols`) thay vì kiểm sự tồn tại. Đây là bài học nên nhớ khi viết bất kỳ đoạn "kiểm tra tính khả dụng" nào trong repo này.

**(d) Egress guard và UAT thật** — mới nhất (27–28/07): nối `egress-guard.py` vào PreToolUse cho Bash, và siết `/fdk-uat` thành gate cứng bắt buộc dựng workspace Orca thật thay vì chạy filesystem-only rồi báo hoàn tất. Lý do ghi trong `llmwiki/wiki/log.md`: cùng một lỗi tái diễn hai lần (21/07 → 24/07) vì bước đó được đánh dấu "(tuỳ chọn)" — dấu hiệu cần đổi **cấu trúc** thay vì nhắc thêm.

Phân bố loại commit 180 ngày: `feat` 192, `docs` 140, `fix` 115, `chore` 58, `skill` 28, `refactor` 14. Tỷ lệ docs cao bằng 3/4 feat — đúng với bản chất repo.

---

## 9. Guided tour — 13 bước

Thứ tự đọc được thiết kế để đi từ "cửa vào người dùng" tới "bộ máy bên trong" rồi quay ra "cách tự bảo trì".

1. **Ba trụ — bắt đầu ở README** — `README.md`, `CLAUDE.md`, `llmwiki/AGENT.md`
2. **Một dòng cài** — `harness/poc-vendor-neutral/bootstrap.sh`, `install.sh`, `uninstall.sh`, `harness/downstream-contract.yaml`
3. **policy.yaml — luật là dữ liệu** — `harness/policy.yaml`, `harness/poc-vendor-neutral/policy.yaml`, `harness/foundation.yaml`, `harness/mechanisms.yaml`
4. **Lõi thực thi** — `harness/poc-vendor-neutral/bin/llmwiki-validate.py`, `bin/harness-events.py`, `gen-converters.py`
5. **15 validator, 0 token** — `harness/validators/no_write_raw.py`, `origin_required.py`, `index_sync.py`, `folder_structure.py`, `decision_adr.py`, `okf_frontmatter.py`
6. **Dây cắm vendor, fail-open** — `llmwiki/.claude/hooks/pre_tool_use.py`, `post_tool_use.py`, `stop.py`, `session_start.py`, `.claude/settings.json`
7. **Trụ tri thức** — `llmwiki/wiki/index.md`, `log.md`, `llmwiki/CLAUDE.md`, `llmwiki/AGENT.md`
8. **Trụ kỹ năng, canonical rồi mirror** — `skills/orca-workflow/SKILL.md`, `skills/propose/SKILL.md`, `skills/verify-before-commit/SKILL.md`, `harness/scripts/sync-skills.py`, `fdk/tools/sync-skill.sh`
9. **Vòng hằng ngày propose → gate → dispatch** — `skills/propose/SKILL.md`, `skills/plan/SKILL.md`, `skills/verify-before-commit/SKILL.md`, `skills/orca-workflow/SKILL.md`, `skills/ship/SKILL.md`
10. **FDK — đồ nghề làm framework** — `fdk/CAPABILITIES.md`, `fdk/tools/build-capabilities.py`, `build-skill-search.py`, `new-skill.py`, `harness/scripts/fdk-gate.py`
11. **Docs sinh bằng code** — `fdk/tools/build-overstack-docs.py`, `build-wiki-graph.py`, `llmwiki/html/overstack.html`, `wiki-graph.html`
12. **Cổng sức khoẻ cuối** — `fdk/tools/medic.py`, `.pre-commit-config.yaml`, `.github/workflows/harness.yml`, `harness/scripts/harness-doctor.py`
13. **Dựng dự án mới bằng một prompt** — `00-New-Project.md`, `01-Project-Kickoff.md`, `02-Setup-Knowledge-Base.md`, `03-Scaffold-Application.md`, `setup.md`

---

## 10. Quy ước cần biết trước khi sửa

**Canonical ↔ mirror.** Skill có hai bản: `skills/<tên>/SKILL.md` là canonical, `llmwiki/skills/<nhóm>/<tên>.md` là mirror. Sửa canonical rồi chạy `harness/scripts/sync-skills.py` hoặc `fdk/tools/sync-skill.sh`. CI có job bắt drift. Ngoài ra còn bản **cài** ở `~/.claude/skills/` — bản này bị `npx skills add` ghi đè, nên vá tay vào đó sẽ mất.

**Hai wiki tách biệt (ADR-008).** `llmwiki/wiki/` là **khuôn** wiki per-project (chỉ giữ file demo, sẽ đi theo dự án khi cài). `fdk/wiki/` là wiki RIÊNG của framework — ADR-001..010, concepts harness/fdk, decisions. Viết tri thức về chính overstack thì vào `fdk/wiki/`, đừng vào `llmwiki/wiki/`.

**FDK không travel (ADR-004/008).** `fdk/` là đồ nghề của người làm framework, không được cài xuống dự án con. `travel_policy_sync.py` và `fix(travel): medic.py bị phân loại sai` cho thấy luật này có validator canh.

**Mọi trang wiki phải có `## Origin`** (R2), và mọi trang mới phải có dòng trong `index.md` (R3). Không có ngoại lệ — hook chặn lúc Write, Stop chặn lúc kết thúc lượt.

**Chỉ được tạo file trong các thư mục đã khai báo** (R5). `folder_structure.py` chặn việc phát minh thư mục mới trong wiki.

**Không ghi công AI vào commit** (R15).

**ADR bắt buộc cho quyết định kiến trúc** (R13): `decisions.md` phải ref một ADR trong `fdk/wiki/sources/adr/`.

---

## 11. Điểm cần cẩn thận

**Repo tự-tham-chiếu.** Đây là framework đang được phát triển *bằng chính nó*: harness của repo này gác chính việc sửa harness. Nghĩa là một thay đổi sai ở `harness/validators/` có thể tự khoá phiên làm việc. `fdk-gate.py` và `medic.py` tồn tại chính vì rủi ro này.

**"Tồn tại ≠ dùng được".** Bài học đắt nhất trong lịch sử repo (mục 8c). Khi viết code kiểm tra một năng lực, phải **thăm dò thật** — mở kết nối, chạy query, xác nhận có dữ liệu — chứ không kiểm sự có mặt của file hay entry config.

**Ba bản của một skill** (canonical / mirror / cài global) là nguồn drift thường trực. Trước khi kết luận "skill này đã vá rồi", kiểm cả ba.

**Nhánh `orca` là nhánh phát hành.** URL cài đặt hardcode `orca`. Push hỏng lên `orca` là hỏng đường cài của mọi người dùng mới ngay lập tức — đó là lý do `/fdk-uat` bắt buộc chạy canary trên nhánh tạm trước khi merge.

**86 file orphan** (không có cạnh nào trong graph) — chủ yếu là trang wiki độc lập và asset. Con số này thấp so với 846 node, cho thấy repo liên kết chéo tốt.

---

## 12. Thống kê

| Chỉ số | Giá trị |
|---|---|
| File được phân tích | 846 (853 tracked, trừ 7 binary/lock) |
| Node trong graph | 846 — 593 document, 183 file code, 70 config |
| Cạnh | 2 905 — 1 640 documents, 717 depends_on, 360 configures, 115 related (co-change), 42 calls, 31 imports |
| Tầng | 15 |
| Bước tour | 13 |
| Node orphan | 86 |
| Commit | 620, từ 2026-04-28 |
| File chạm trong 30 ngày | 825 / 853 |
| Skill | 84 |
| Rule | 18 |
| Validator | 15 |
| FDK tool | 19 |
| Harness script | 63 |

---

## Origin

- **Sinh bởi:** `/orca-onboard` (Phase 1 — distilled understand-anything pipeline, static parse 0 token)
- **Commit phân tích:** `9032ae42fbe1e74115bf852decd12c6ca57d467e` (nhánh `orca`)
- **Ngày:** 2026-07-28
- **Graph:** `.understand-anything/knowledge-graph.json`
