# Operation Log

## 2026-09-02 — maintenance — vá R3 index-sync + soi duplicate-basename (fdk-gate drift)

`python3 harness/validators/index_sync.py --wiki-dir llmwiki/wiki` báo 18 file thiếu khỏi `wiki/index.md` (8 `sources/*-session-provenance.md` từ 24/07 đến 13/08, 10 `sources/draft/*.md`). Đọc từng file thật (không suy đoán tên/ngày) rồi thêm đúng 18 dòng vào bảng, theo house-style sẵn có: 8 dòng session-provenance khớp khuôn `Auto-distill scratch-log phiên <hash> ngày DD/MM...` (5 dòng `(stub) — chỉ chạm ...` vì chỉ đụng `gitignore`/`entities/repowise.md`, 1 dòng có nội dung thật vì phiên đó soạn draft BIV); 6 dòng `draft` + 4 dòng `issue` khớp khuôn "SPEC ..."/"Issue: ..." đã dùng cho các `sources/draft/*` khác. Validator giờ exit 0.

Soi `python3 harness/validators/duplicate_basename.py --wiki-dir llmwiki/wiki`: `200826-docs-site-macos-mermaid-sidebar-fix.md` trùng basename ở `draft/unknown/` và `sources/draft/`. Diff hai file: **KHÔNG phải bản sao** — `sources/draft/` là SPEC (`type: draft`), `draft/unknown/` là unknown-ledger (`type: unknown-ledger`, khai `source_spec:` trỏ ngược về chính SPEC đó), nội dung hoàn toàn khác nhau. Đối chiếu 2 file unknown-ledger khác cùng thư mục (`unknown-context-hygiene.md`, `unknown-frontend-design.md`) lộ ra quy ước đặt tên: file trong `draft/unknown/` phải mang tiền tố `unknown-<slug>.md`, không được trùng basename với SPEC nguồn — file `200826-...` phá quy ước đó (thiếu tiền tố `unknown-`) nên mới đụng basename. Không xoá/gộp file nào — nội dung khác nhau thật, cần người quyết hướng sửa (nhiều khả năng: đổi tên `draft/unknown/200826-docs-site-macos-mermaid-sidebar-fix.md` → `draft/unknown/unknown-docs-site-macos-mermaid-sidebar-fix.md`), báo lại thay vì tự đoán. `duplicate_basename.py` vẫn đỏ, cố ý để nguyên.

<!-- log:auto:start -->

### 🤖 Log tự-động (code-logger, không do agent ghi)

| Thời điểm | Event | Chi tiết |
|---|---|---|
| 2026-08-20 16:07:11 | `file.write` | harness/poc-vendor-neutral/install.sh · tool=Edit · session=53f945e5 · actor=agent · prev=bcf68f0de7ee97a4913976e4e255a9 |
| 2026-08-20 16:07:11 | `file.write` | harness/poc-vendor-neutral/install.sh · tool=Edit · session=53f945e5 · actor=agent · prev=3927861be8ff66ffa303220493f867 |
| 2026-08-20 16:16:48 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:16:48 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:17:12 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:17:12 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:19:16 | `file.write` | skills/docs-site-macos/vendor/README.md · tool=Write · session=72190e1c · actor=agent · prev=40f29c87b99ea5529dc01847072 |
| 2026-08-20 16:19:16 | `file.write` | skills/docs-site-macos/vendor/README.md · tool=Write · session=72190e1c · actor=agent · prev=567781607e844a33ae01b5608d2 |
| 2026-08-20 16:19:29 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=7e1d0300e3a0b75abb10fe3fabf647123016 |
| 2026-08-20 16:19:29 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=3b87eb6e1e32dfe428708b36286987d31a5a |
| 2026-08-20 16:19:44 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=8c4e7eed56f1325b195ef5a324f72790e8d6 |
| 2026-08-20 16:19:44 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=5c842f67984e366934800a48a315ace7cc96 |
| 2026-08-20 16:21:16 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=b98dfd957321792f40c1816844d52c1e2341 |
| 2026-08-20 16:21:16 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=9e3aa6f28d8ee384cbc6be189ee779ab6ac8 |
| 2026-08-20 16:22:11 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=9d81d33861d138cca2eafdcd007b3763e1bb |
| 2026-08-20 16:22:11 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=aa4edd24f5686ad22d267d92b878136e2d1f |
| 2026-08-20 16:24:05 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=4961f3efe999ef4f1e40ff4693533e266b4a |
| 2026-08-20 16:24:05 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=6bdea73145fb8bba500287d4209f6e525973 |
| 2026-08-20 16:24:15 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=f2368c8828488b3b0e1d6aa0af4a8ebca158 |
| 2026-08-20 16:24:15 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=72190e1c · actor=agent · prev=da9124439f17597e27d4b68e65f5e9442f9f |
| 2026-08-20 16:24:30 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:24:30 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:24:35 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:24:35 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:24:48 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:24:48 | `file.write` | llmwiki/wiki/sources/draft/200826-docs-site-macos-mermaid-sidebar-fix.md · tool=Edit · session=72190e1c · actor=agent ·  |
| 2026-08-20 16:25:19 | `task.set` |  · task=T-260820-01 · state=approved · note=user duyet truc tiep trong chat, yeu cau lam ngay + day remote · actor=agent |
| 2026-08-20 16:25:19 | `task.set` |  · task=T-260820-01 · state=completed · note=implement xong, verified Playwright, push remote · actor=agent · prev=f717c |
| 2026-08-20 16:26:41 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=0 · prev=a0716e1c34cff05d19597891a972e7fcd1f9e288101c34645ff48295ae5de515 · h=5642 |
| 2026-08-20 16:26:41 | `commit.reconcile` |  · actor=system · agent_n=2 · human_n=1 · human=['llmwiki/wiki/log.md'] · prev=56420dbc28e10cdf5a008aa8540355f88a7c7c44e |
| 2026-08-20 16:26:41 | `commit.reconcile` |  · actor=system · agent_n=2 · human_n=2 · human=['harness/metrics/tasks.json', 'llmwiki/skills/utils/docs-site-macos.md' |
| 2026-08-20 16:26:41 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=0 · prev=46229ace40de79534715f0286e65547f7136bcd6b8f34a38fe3d4ced1af7c930 · h=2b02 |
| 2026-08-20 16:31:03 | `file.write` | llmwiki/html/200826-session-summary-mermaid-sidebar.html · tool=Write · session=72190e1c · actor=agent · prev=2b0247d276 |
| 2026-08-20 16:31:03 | `file.write` | llmwiki/html/200826-session-summary-mermaid-sidebar.html · tool=Write · session=72190e1c · actor=agent · prev=5d6fd9880e |
| 2026-08-20 16:46:57 | `file.write` | llmwiki/html/200826-session-summary-mermaid-sidebar.html · tool=Edit · session=72190e1c · actor=agent · prev=2cd1abcc0ec |
| 2026-08-20 16:46:57 | `file.write` | llmwiki/html/200826-session-summary-mermaid-sidebar.html · tool=Edit · session=72190e1c · actor=agent · prev=b0c25c8e588 |
| 2026-08-20 16:47:13 | `file.write` | llmwiki/html/200826-session-summary-mermaid-sidebar.html · tool=Edit · session=72190e1c · actor=agent · prev=ac5de9c368b |
| 2026-08-20 16:47:13 | `file.write` | llmwiki/html/200826-session-summary-mermaid-sidebar.html · tool=Edit · session=72190e1c · actor=agent · prev=d9b9627f1fe |
| 2026-08-20 16:47:31 | `file.write` | llmwiki/html/200826-session-summary-mermaid-sidebar.html · tool=Edit · session=72190e1c · actor=agent · prev=f6a092e35b3 |
| 2026-08-20 16:47:31 | `file.write` | llmwiki/html/200826-session-summary-mermaid-sidebar.html · tool=Edit · session=72190e1c · actor=agent · prev=f20318dcc7a |

<!-- log:auto:end -->
