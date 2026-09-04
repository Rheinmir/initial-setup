# Operation Log

## 2026-09-02 — maintenance — vá R3 index-sync + soi duplicate-basename (fdk-gate drift)

`python3 harness/validators/index_sync.py --wiki-dir llmwiki/wiki` báo 18 file thiếu khỏi `wiki/index.md` (8 `sources/*-session-provenance.md` từ 24/07 đến 13/08, 10 `sources/draft/*.md`). Đọc từng file thật (không suy đoán tên/ngày) rồi thêm đúng 18 dòng vào bảng, theo house-style sẵn có: 8 dòng session-provenance khớp khuôn `Auto-distill scratch-log phiên <hash> ngày DD/MM...` (5 dòng `(stub) — chỉ chạm ...` vì chỉ đụng `gitignore`/`entities/repowise.md`, 1 dòng có nội dung thật vì phiên đó soạn draft BIV); 6 dòng `draft` + 4 dòng `issue` khớp khuôn "SPEC ..."/"Issue: ..." đã dùng cho các `sources/draft/*` khác. Validator giờ exit 0.

Soi `python3 harness/validators/duplicate_basename.py --wiki-dir llmwiki/wiki`: `200826-docs-site-macos-mermaid-sidebar-fix.md` trùng basename ở `draft/unknown/` và `sources/draft/`. Diff hai file: **KHÔNG phải bản sao** — `sources/draft/` là SPEC (`type: draft`), `draft/unknown/` là unknown-ledger (`type: unknown-ledger`, khai `source_spec:` trỏ ngược về chính SPEC đó), nội dung hoàn toàn khác nhau. Đối chiếu 2 file unknown-ledger khác cùng thư mục (`unknown-context-hygiene.md`, `unknown-frontend-design.md`) lộ ra quy ước đặt tên: file trong `draft/unknown/` phải mang tiền tố `unknown-<slug>.md`, không được trùng basename với SPEC nguồn — file `200826-...` phá quy ước đó (thiếu tiền tố `unknown-`) nên mới đụng basename. Không xoá/gộp file nào — nội dung khác nhau thật, cần người quyết hướng sửa (nhiều khả năng: đổi tên `draft/unknown/200826-docs-site-macos-mermaid-sidebar-fix.md` → `draft/unknown/unknown-docs-site-macos-mermaid-sidebar-fix.md`), báo lại thay vì tự đoán. `duplicate_basename.py` vẫn đỏ, cố ý để nguyên.

<!-- log:auto:start -->

### 🤖 Log tự-động (code-logger, không do agent ghi)

| Thời điểm | Event | Chi tiết |
|---|---|---|
| 2026-08-20 16:50:41 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=2aedc924b9e0561933ebbe966def9820d88f |
| 2026-08-20 16:51:03 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=d37df70991273fabc0aa0299b63201c58501 |
| 2026-08-20 16:51:03 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=86219564e5016e70436f872b88e3065c285c |
| 2026-08-20 16:52:41 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=69bd47f08ef961c5a2c8b000edfaba003d66 |
| 2026-08-20 16:52:41 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=975ce6988d22b8f1b1c3621ce28988518e77 |
| 2026-08-20 16:54:14 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=eeb667ae76a3850a867bfd2400f7a676853d |
| 2026-08-20 16:54:14 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=a20acaeee733ab4535b7a9aef47735673ead |
| 2026-08-20 16:55:42 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=2 · human=['llmwiki/skills/utils/docs-site-macos.md', 'llmwiki/wiki/log.md'] · pre |
| 2026-08-25 16:42:01 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=dba79064 · actor=agent · prev=9d362ca0ce329e89707e841212e8b27eafc0 |
| 2026-08-25 16:42:01 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=dba79064 · actor=agent · prev=6a1c107e3bf8fb4ff782902f9c25da3c7f4b |
| 2026-08-25 16:42:15 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=dba79064 · actor=agent · prev=edf5b193ac2a43a8b35cd754c491d61bb61f |
| 2026-08-25 16:42:15 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=dba79064 · actor=agent · prev=78c5e8d0375375dc10af170c80cef6c92fc9 |
| 2026-08-25 16:42:33 | `file.write` | skills/docs-site-macos/vendor/README.md · tool=Edit · session=dba79064 · actor=agent · prev=a10b05672245277682f2f521703f |
| 2026-08-25 16:42:33 | `file.write` | skills/docs-site-macos/vendor/README.md · tool=Edit · session=dba79064 · actor=agent · prev=e0e12c389be97732aa470b3d340d |
| 2026-08-25 16:44:33 | `commit.reconcile` |  · actor=system · agent_n=2 · human_n=1 · human=['llmwiki/skills/utils/docs-site-macos.md'] · prev=a90e42b1c8c934ab010ea |
| 2026-09-02 22:23:18 | `task.new` |  · task=T-260902-01 · title=SessionStart episodic recall nudge · state=proposed · actor=agent · prev=b4fbfdc098a5e1db2cd |
| 2026-09-02 22:25:01 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Write · session=dba79064 · actor=agent · prev=1 |
| 2026-09-02 22:25:01 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Write · session=dba79064 · actor=agent · prev=2 |
| 2026-09-02 22:25:09 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Edit · session=dba79064 · actor=agent · prev=aa |
| 2026-09-02 22:25:09 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Edit · session=dba79064 · actor=agent · prev=4a |
| 2026-09-02 22:25:13 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Edit · session=dba79064 · actor=agent · prev=ee |
| 2026-09-02 22:25:13 | `file.write` | llmwiki/wiki/sources/draft/020926-sessionstart-episodic-recall.md · tool=Edit · session=dba79064 · actor=agent · prev=bc |
| 2026-09-02 22:26:15 | `file.write` | llmwiki/html/020926-sessionstart-episodic-recall-seq.html · tool=Write · session=dba79064 · actor=agent · prev=4a08f8b28 |
| 2026-09-02 22:26:15 | `file.write` | llmwiki/html/020926-sessionstart-episodic-recall-seq.html · tool=Write · session=dba79064 · actor=agent · prev=54fa86bbb |
| 2026-09-02 22:26:31 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=dba79064 · actor=agent · prev=c4422a6186a7bcc87d8810238fb8c2bb85f924e9329974 |
| 2026-09-02 22:26:31 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=dba79064 · actor=agent · prev=ff038a986a0e63e9595a01ad865570f8ce539b17c7c1d9 |
| 2026-09-02 22:26:49 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=d32daf24fa115e707af8c2d38061c8cfb1b5c3057f338c1a |
| 2026-09-02 22:26:49 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=f6c7d5cdc48e63a13aeb026f3102e1c81921df1e4228f6c0 |
| 2026-09-03 20:15:40 | `file.write` | llmwiki/html/030926-memory-retrieval-improvement-summary.html · tool=Write · session=dba79064 · actor=agent · prev=55a5d |
| 2026-09-03 20:15:40 | `file.write` | llmwiki/html/030926-memory-retrieval-improvement-summary.html · tool=Write · session=dba79064 · actor=agent · prev=d2fcf |
| 2026-09-03 20:17:30 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=dba79064 · actor=agent · prev=c065e6312d6230dd552d37fd235f2c7aa78d01c40f0819 |
| 2026-09-03 20:17:30 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=dba79064 · actor=agent · prev=e93ca9b3fd848b64b13af9be67bf1207e0700c619a0ee3 |
| 2026-09-03 20:17:38 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=8b33279b91cf3035e7559fa08ee87adb345c628d76c5b575 |
| 2026-09-03 20:17:38 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=a90b22aff1ec5fb7d215fa43c82428f61078fac478f9b2fc |
| 2026-09-04 09:11:37 | `file.write` | harness/scripts/wiki-sync.py · tool=Edit · session=3e970e77 · actor=agent · prev=01e00cc7e1eba30d0aab65482e0c796dd732cfc |
| 2026-09-04 09:11:37 | `file.write` | harness/scripts/wiki-sync.py · tool=Edit · session=3e970e77 · actor=agent · prev=99341691ce6394f752acb8a141f296bf0e8411b |
| 2026-09-04 09:11:53 | `file.write` | harness/scripts/wiki-sync.py · tool=Edit · session=3e970e77 · actor=agent · prev=f91c12fbf75fbedeaa09215e5c006fc439b4e77 |
| 2026-09-04 09:11:53 | `file.write` | harness/scripts/wiki-sync.py · tool=Edit · session=3e970e77 · actor=agent · prev=60c00ca6158856fc2de0ccba12fa11f8b5d4af1 |
| 2026-09-04 10:28:45 | `file.write` | harness/scripts/dep-health.py · tool=Edit · session=3e970e77 · actor=agent · prev=da98f5ddaeb2fec629737762f78e1732ac9fff |
| 2026-09-04 10:28:45 | `file.write` | harness/scripts/dep-health.py · tool=Edit · session=3e970e77 · actor=agent · prev=8a73f81581c475b25ef0b1e525719ec15085b9 |

<!-- log:auto:end -->
