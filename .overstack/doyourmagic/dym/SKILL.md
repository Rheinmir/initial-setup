---
name: dym
description: "Tool ngoài ĐÃ KIỂM CHỨNG, chọn theo domain: agent · architecture · browser · chart · computer-use · copy · design-audit · desktop · diagram · frontend · macos · orchestration · playwright · qa · report · research · science · security · skill-authoring · swarm · threat-intel · writing. Gọi khi việc thuộc một domain đó (vd vẽ chart → lieflat-charts, frontend → impeccable) và skill canonical chưa phủ; gõ /dym <domain> hoặc /dym."
---

# Skill: dym — định tuyến domain → bundle tool ngoài

Sinh bởi `harness/scripts/dym-sync.py index` từ `domains:` trong hub của từng bundle. **Không sửa tay** — sửa `domains:` ở hub rồi chạy lại.

## Steps
1. Xác định domain của việc đang làm (bảng 1). Nhiều hub cùng domain → đọc bảng 2, chọn theo slug khớp việc; vẫn phân vân → hỏi user một câu.
2. Đọc ĐÚNG MỘT hub: `.overstack/doyourmagic/<bundle>/skills/<hub>/SKILL.md`, rồi làm theo nó (hub sẽ chỉ tới sub-skill).
3. Frontend/UI: `hallmark` vẫn là SÀN, bundle chỉ là flavour bên trên.

## Bảng 1 — domain → hub
| domain | hub |
|---|---|
| agent | `dym-arex-skill` · `dym-nuwa-skill` · `dym-ruflo` |
| architecture | `dym-archify` |
| browser | `dym-browser-use` |
| chart | `dym-lieflat-charts` |
| computer-use | `dym-agent-desktop` |
| copy | `dym-humanizer` |
| design-audit | `dym-impeccable` |
| desktop | `dym-agent-desktop` |
| diagram | `dym-archify` · `dym-diagram-design` |
| frontend | `dym-diagram-design` · `dym-impeccable` |
| macos | `dym-agent-desktop` |
| orchestration | `dym-ruflo` |
| playwright | `dym-browser-use` |
| qa | `dym-browser-use` |
| report | `dym-lieflat-charts` |
| research | `dym-scientific-agent-skills` |
| science | `dym-scientific-agent-skills` |
| security | `dym-cti-expert` |
| skill-authoring | `dym-arex-skill` · `dym-nuwa-skill` |
| swarm | `dym-ruflo` |
| threat-intel | `dym-cti-expert` |
| writing | `dym-humanizer` |

## Bảng 2 — hub → slug
| hub | bundle | domains | slugs |
|---|---|---|---|
| `dym-agent-desktop` | agent-desktop | computer-use, desktop, macos | drive · install · route · session |
| `dym-archify` | archify | diagram, architecture | agent-chat-authoring · ci-diagram-gate · cli-authoring-loop · compare-architecture-delta · contributor-build-and-test · install-and-verify · migrate-workflow-v2 · repository-evidence · visual-check-and-preview |
| `dym-arex-skill` | arex-skill | skill-authoring, agent | cai-dat-disco · cai-thu-vien-skill · chay-viec-researcher · contributor-dong-gop-skill · contributor-phat-trien-cli · creator-paper-to-skills · creator-tao-repo-skill · lenh-chat-trong-tui · tich-hop-ci · xuat-skill-sang-agent-khac |
| `dym-browser-use` | browser-use | browser, qa, playwright | cloud · qa · repl |
| `dym-cti-expert` | cti-expert | security, threat-intel | api-keys-and-capabilities · case-pipeline-and-kb · ci-monitoring · cli-dispatcher · contributor-develop-and-gate · install-and-register · investigate-in-claude-code · reports-and-iocs · safety-gates |
| `dym-diagram-design` | diagram-design | diagram, frontend | authoring-in-chat · brand-onboarding-and-profiles · contributor-gates · import-export-slash-commands · import-extractors-shell · install-and-verify · selfcheck-and-your-ci |
| `dym-humanizer` | humanizer | writing, copy | contributor-validate-and-release · humanize-files-and-embedded · humanize-pasted-text · install-claude-plugin · install-shell · tune-false-positives |
| `dym-impeccable` | impeccable | frontend, design-audit | browser-extension-build · chat-commands · ci-integration · contributor-build-and-test · detect-cli-scan · install-into-your-project · tune-detector-ignores |
| `dym-lieflat-charts` | lieflat-charts | chart, report | browse-templates · chart-request · ci-example · contributor-checks · install · report-request |
| `dym-nuwa-skill` | nuwa-skill | skill-authoring, agent | contributor-repo-itself · diagnose-then-distill · distill-a-person · fidelity-scorecard · helper-scripts-cli · install · publish-and-get-listed · use-and-update-persona |
| `dym-ruflo` | ruflo | orchestration, agent, swarm | init · install · route |
| `dym-scientific-agent-skills` | scientific-agent-skills | science, research | cai-dat-skills · chay-script-bundled-tu-shell · dong-gop-them-sua-skill · dong-gop-validate-test-scan · dung-skill-trong-agent · gate-trong-ci-cua-ban · pin-va-cap-nhat · tham-dinh-truoc-khi-cai |
