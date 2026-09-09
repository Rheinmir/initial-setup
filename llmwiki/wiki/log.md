

## 2026-09-09 — tidy — docs-curate → tidy + cổng ngưỡng nháp (proposal 090926-docs-curate-threshold-gate)
- `harness/scripts/tidy.py` (mới, thay `fdk/tools/docs-curate.py`): `check` 0-token (draft tầng gốc > 10 → exit 3), `plan/apply/reindex`; trả 3 nợ đo được: D1 `git mv` vào `archive/` TRACKED (từ chối dời file tracked khi đích gitignored), D2 tuổi không archive draft còn proposed (chỉ status/task đã xong), D3 tên `tidy`.
- `session_start.py`: `draft_threshold()` hỏi user chạy `/tidy` 1 lần/phiên khi vượt ngưỡng (fail-open, downstream chạy qua global).
- `wiki-health.py` (stem trong archive/ = resolved-frozen), `index_sync.py` (archive/ không tính index, row trỏ archive/ hợp lệ), `okf_frontmatter.py`/`proposal_complete.py` (miễn archive/), engine `llmwiki-validate.py` + policy R2/R7/R9/R18 `exclude_globs: **/draft/archive/**`.
- `medic` probe `tidy` (warn); `.gitignore` bỏ ignore `llmwiki/wiki/sources/draft/archive/`; manifest + `harness/tests/tidy-test.sh` (11 assert); skill `skills/tidy/SKILL.md` + mirror `llmwiki/skills/utils/tidy.md`; tham chiếu sống đổi tên.

<!-- log:auto:start -->

### 🤖 Log tự-động (code-logger, không do agent ghi)

| Thời điểm | Event | Chi tiết |
|---|---|---|
| 2026-09-08 18:26:27 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['harness/poc-vendor-neutral/install.sh', 'harness/tests/skill-provenanc |
| 2026-09-08 18:31:39 | `file.write` | fdk/wiki/concepts/overstack-artifact-root.md · tool=Write · session=f38daa12 · actor=agent · prev=7546265c8cf30e6421dba3 |
| 2026-09-08 18:31:39 | `file.write` | fdk/wiki/concepts/overstack-artifact-root.md · tool=Write · session=f38daa12 · actor=agent · prev=785e7d002abc0b988a15d0 |
| 2026-09-08 18:35:33 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['fdk/wiki/index.md', 'harness/scripts/dym-sync.py', 'llmwiki/wiki/log.m |
| 2026-09-08 18:35:33 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=2 · human=['harness/version.json', 'harness/metrics/.stop-debounce.json'] · prev=a |
| 2026-09-09 15:26:05 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['fdk/skills.provenance.json'] · prev=d9bce65ab25046dea11972a00d42637af9 |
| 2026-09-09 16:00:36 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/sources/ci-maintainer-brief.md'] · prev=67e0cd0190519f97b |
| 2026-09-09 16:06:58 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['harness/scripts/ci-fail-parse.py'] · prev=2b1f4aa1d3087443c55425d4510e |
| 2026-09-09 16:08:13 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['fdk/CAPABILITIES.md', 'harness/version.json'] · prev=b9a220005b9f9b3a4 |
| 2026-09-09 16:12:52 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/sources/ci-maintainer-brief.md'] · prev=e82a539a24d40ca0d |
| 2026-09-09 16:27:49 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/concepts/ci-issue-loop.md', 'llmwiki/wiki/index.md'] · pr |
| 2026-09-09 16:44:09 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['harness/validators/index_sync.py', 'llmwiki/.claude/hooks/validators/i |
| 2026-09-09 16:44:09 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['harness/scripts/fdk-gate.py', 'llmwiki/wiki/sources/090926-session-pro |
| 2026-09-09 16:47:38 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['harness/validators/index_sync.py', 'llmwiki/.claude/hooks/validators/i |
| 2026-09-09 16:51:01 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['llmwiki/wiki/sources/ISSUES.md', 'llmwiki/wiki/sources/draft/090926-in |
| 2026-09-09 16:52:02 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/index.md'] · prev=ed6aafd3e7ce377efed1b62d8fb47ffe4f61308 |
| 2026-09-09 17:12:31 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=4 · human=['harness/metrics/tasks.json', 'llmwiki/wiki/sources/draft/020726-counci |
| 2026-09-09 17:12:31 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['llmwiki/wiki/sources/draft/080926-prd-grade-fe.md', 'llmwiki/wiki/sour |
| 2026-09-09 17:18:30 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/sources/draft/030726-medic-cong-suc-khoe-tong.md', 'llmwi |
| 2026-09-09 17:21:55 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['llmwiki/wiki/index.md', 'llmwiki/wiki/sources/ISSUES.md', 'llmwiki/wik |
| 2026-09-09 17:25:58 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/sources/draft/090926-fdk-gate-two-stale-steps.md'] · prev |
| 2026-09-09 17:28:50 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/sources/ISSUES.md', 'llmwiki/wiki/sources/draft/090926-fd |
| 2026-09-09 17:54:43 | `file.write` | skills/playwright-verify/SKILL.md · tool=Edit · session=d225a072 · actor=agent · prev=2e6d4ea4c900ebb21e4a71c6f6440143c3 |
| 2026-09-09 17:54:43 | `file.write` | skills/playwright-verify/SKILL.md · tool=Edit · session=d225a072 · actor=agent · prev=22f083439bbaa0fbd3a5436730f3f5cdd7 |
| 2026-09-09 17:54:52 | `file.write` | skills/playwright-verify/SKILL.md · tool=Edit · session=d225a072 · actor=agent · prev=62171054a36e0b5ccefe078b2cd43bb07e |
| 2026-09-09 17:54:52 | `file.write` | skills/playwright-verify/SKILL.md · tool=Edit · session=d225a072 · actor=agent · prev=cfea35775a94e245f30cea1fcdb32c6614 |
| 2026-09-09 17:55:00 | `file.write` | skills/playwright-verify/SKILL.md · tool=Edit · session=d225a072 · actor=agent · prev=e6d9f8a0c5377b31c26c755646b7dc240f |
| 2026-09-09 17:55:00 | `file.write` | skills/playwright-verify/SKILL.md · tool=Edit · session=d225a072 · actor=agent · prev=2d4920710831a2d731c4654d8fc09068ea |
| 2026-09-09 20:13:06 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['fdk/skills.search.json', 'fdk/skills.provenance.json', 'llmwiki/skills |
| 2026-09-09 20:13:06 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['skills/playwright-verify/SKILL.md'] · prev=8f22608713934c62af5ac53bd02 |
| 2026-09-09 20:13:23 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['skills/playwright-verify/SKILL.md'] · prev=ec521570e3bf97274b7202a7169 |
| 2026-09-09 20:13:23 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['fdk/skills.search.json', 'fdk/skills.provenance.json', 'llmwiki/skills |
| 2026-09-09 20:19:18 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/log.md', 'llmwiki/wiki/stale.json'] · prev=78d5a254d0a7ed |
| 2026-09-09 20:19:18 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['llmwiki/wiki/sources/090926-session-provenance.md', 'llmwiki/wiki/.las |
| 2026-09-09 21:07:20 | `file.write` | harness/scripts/tidy.py · tool=Write · session=35811e61 · actor=agent · prev=655203e8168c64b732324d5479c08d5321179ff6cc7 |
| 2026-09-09 21:07:20 | `file.write` | harness/scripts/tidy.py · tool=Write · session=35811e61 · actor=agent · prev=d1fb3669fc363e68e64435cb119fa7268b603e129c9 |
| 2026-09-09 21:09:02 | `file.write` | harness/tests/tidy-test.sh · tool=Write · session=35811e61 · actor=agent · prev=d40fff17ea3b2f08bc8f2a1b9dd2bd0105c92a9d |
| 2026-09-09 21:09:02 | `file.write` | harness/tests/tidy-test.sh · tool=Write · session=35811e61 · actor=agent · prev=c1a6581543b8246da45519df1c41cdd52b081312 |
| 2026-09-09 21:11:21 | `file.write` | skills/tidy/SKILL.md · tool=Write · session=35811e61 · actor=agent · prev=41530f664781493f70c5ab66b53e6db8fe1133abe0e47e |
| 2026-09-09 21:11:21 | `file.write` | skills/tidy/SKILL.md · tool=Write · session=35811e61 · actor=agent · prev=55e9dd18d6757adcf79aacd9fbcfeebafdee1583d6ae30 |

<!-- log:auto:end -->
