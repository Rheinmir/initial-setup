

## 2026-08-01 — fdk — teach-me: khung bảy bước
Feedback Rhein: "học cái gì cũng phải có cấu trúc [Tên gọi→Nguồn gốc→Lý do tồn tại→Cơ chế hoạt động→Trade-off→Giới hạn→Vị trí trong hệ thống] để hiểu sâu". Đổi skill teach-me từ khung "bốn phần" (2 cấp + bộ ba + tóm tắt) sang khung bảy bước cố định, đúng thứ tự — dồn nội dung runtime-driven (2 sơ đồ hệ thống/code) vào bước 4, sơ đồ tóm tắt luồng vào bước 7, thêm mới Trade-off (bước 5) và Giới hạn (bước 6) — hai góc trước đây không có chỗ đứng riêng. Sync canonical→mirror→global install (parity 3 bản byte-identical), regen skill-search index, bump capability-stamp 1.3.60→1.3.61, cập nhật fdk-problem-tree.html (node p-45, solved, scope=[skills]). fdk-gate 21/21 PASS.

## 2026-08-11 — distill (bypass ingest) — repowise-dev/repowise

Yêu cầu trực tiếp "repowise-dev/repowise distill nó đi". `llmwiki/raw/` khoá ghi cho agent (deny rule + luật "chỉ người ghi") — hỏi user, chọn bỏ qua `raw/`, ghi thẳng vào wiki theo mạch [[frontier-gap-scan]] (quét đối thủ) thay vì `/ingest` chuẩn 7 bước.

Tạo `llmwiki/wiki/entities/repowise.md` (entity, so sánh điểm chạm thật với `code-graph`/`/ingest`/`harness/validators/code_health.py`) + `llmwiki/innovation/110826-innovation.md` (bảng đối chiếu, kết luận: 1 gap mới đủ chín — code-health tất định/defect-validated + dead-code + PR-bot 0-LLM, KHÔNG trùng GH#9-13/#101/#102 — chưa raise, chờ user xác nhận vì tạo issue là hành động công khai).

## 2026-08-11 — distill cơ chế (clean-room) — code_complexity.py

User yêu cầu tiếp: không chỉ doc, distill CƠ CHẾ nguyên code sang Python. repowise là AGPL-3.0, overstack MIT — hỏi user cách port, chọn **clean-room** (đọc README thuật toán qua `gh api`, không tải/copy code gốc, tự viết lại bằng stdlib).

Ship `harness/validators/code_complexity.py`: McCabe CCN + NLOC per-function (`ast`), LCOM4-lite cohesion + god-class per-class (connected-components qua `self.attr`/gọi-lẫn-nhau, safety-valve khi 0 tín hiệu), duplicate-code (token-chunk hash, đơn giản hơn sliding Rabin-Karp thật), điểm 1-10/file, advisory-only. Selftest assert-based (`--selftest`) xanh; chạy thật trên 124 file .py trong repo, bắt đúng finding thật (kể cả cặp mirror `proposal_complete.py` trùng gần 100% — xác nhận detector không phải false-positive ngẫu nhiên).

Ghi rõ ceiling KHÔNG làm ở lượt này (cập nhật `llmwiki/innovation/110826-innovation.md`): không "defect-validated" (trọng số tự chọn, không calibrated), chỉ Python (không tree-sitter đa ngôn ngữ), chưa có dead-code/PR-bot/refactor-plan-sinh-cụ-thể, chưa wire vào gate/medic (đứng standalone advisory, cần hỏi trước khi nâng hard-gate).


<!-- log:auto:start -->

### 🤖 Log tự-động (code-logger, không do agent ghi)

| Thời điểm | Event | Chi tiết |
|---|---|---|
| 2026-08-01 16:35:19 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Write · session=8a8ad17d · actor=agent · prev=a61 |
| 2026-08-01 16:35:25 | `file.write` | llmwiki/wiki/sources/ISSUES.md · tool=Edit · session=8a8ad17d · actor=agent · prev=0ff68dd9815c83de257d01f0f9bfa966f132c |
| 2026-08-01 16:35:58 | `file.write` | llmwiki/wiki/sources/ISSUES.md · tool=Edit · session=8a8ad17d · actor=agent · prev=a04d9321d8f298b9d5030463e40b3b0c9da94 |
| 2026-08-01 16:39:43 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=918e |
| 2026-08-01 16:39:59 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=63a8 |
| 2026-08-01 16:40:11 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=bdfd |
| 2026-08-01 16:40:29 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=7115 |
| 2026-08-01 16:40:39 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=1c93 |
| 2026-08-01 16:40:46 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=1be3 |
| 2026-08-01 16:40:53 | `file.write` | llmwiki/wiki/sources/ISSUES.md · tool=Edit · session=8a8ad17d · actor=agent · prev=0b82cf15a00d24237bad15ee4547a2ce796a8 |
| 2026-08-01 16:43:10 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=b539 |
| 2026-08-01 16:43:17 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=0ef9 |
| 2026-08-01 16:43:23 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=2ddd |
| 2026-08-01 16:43:31 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=57e2 |
| 2026-08-01 16:43:38 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=2828 |
| 2026-08-01 16:43:45 | `file.write` | llmwiki/wiki/sources/draft/010826-wiki-mental-model-taxonomy.md · tool=Edit · session=8a8ad17d · actor=agent · prev=6d11 |
| 2026-08-02 22:53:47 | `commit.reconcile` |  · actor=system · agent_n=2 · human_n=0 · prev=d2af35c0314085f86aa2dbc1774db08da2c110ed6a8977bfbc3281fe7ff22c0d · h=735a |
| 2026-08-03 09:09:22 | `file.write` | llmwiki/innovation/030826-innovation.md · tool=Write · session=d1a42e6e · actor=agent · prev=735a51db09cace928d3ff494d88 |
| 2026-08-03 15:27:26 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=3b20b398 · actor=agent · prev=ee0aaaf25eeab32abbc528dcb86328ce94e8 |
| 2026-08-03 15:27:26 | `file.write` | skills/docs-site-macos/SKILL.md · tool=Edit · session=3b20b398 · actor=agent · prev=genesis · h=ee0aaaf25eeab32abbc528dc |
| 2026-08-03 15:27:36 | `file.write` | llmwiki/skills/utils/docs-site-macos.md · tool=Edit · session=3b20b398 · actor=agent · prev=54cfbbad2d6bf3b196e3d0ec98f4 |
| 2026-08-03 15:27:36 | `file.write` | llmwiki/skills/utils/docs-site-macos.md · tool=Edit · session=3b20b398 · actor=agent · prev=c54deb946d526ff9501ecebdb093 |
| 2026-08-03 15:28:19 | `commit.reconcile` |  · actor=system · agent_n=2 · human_n=0 · prev=8ee01a899dc3359d1093c440840cd389963793d9eb5ed00404cf6100f3823cd0 · h=3910 |
| 2026-08-03 15:30:46 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/sources/030826-session-provenance.md'] · prev=f50f48ed568 |
| 2026-08-03 15:30:46 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['harness/metrics/.stop-debounce.json', 'llmwiki/wiki/log.md'] · prev=39 |
| 2026-08-03 15:34:08 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=3b20b398 · actor=agent · prev=1e81b26513467829b547ae6eed360c72dbf1795866c217 |
| 2026-08-03 15:34:08 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=3b20b398 · actor=agent · prev=fe33e32a8b13cdd6de9d8cedb4529554c3dd2dd98bec94 |
| 2026-08-03 15:35:32 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=1 · human=['fdk/skills.provenance.json'] · prev=a94bae66b9ceaf32117a8a0c9635912825 |
| 2026-08-04 09:06:19 | `file.write` | llmwiki/innovation/040826-innovation.md · tool=Write · session=4f625e3f · actor=agent · prev=d68f3e502b114125517938360a1 |
| 2026-08-05 00:05:24 | `file.write` | llmwiki/wiki/sources/draft/050826-raise-issue-skill-missing-commit-step.md · tool=Write · session=8a8ad17d · actor=agent |
| 2026-08-05 00:05:31 | `file.write` | llmwiki/wiki/sources/ISSUES.md · tool=Edit · session=8a8ad17d · actor=agent · prev=1e1ff2316a81f673dd08f4819d9fdf07918e2 |
| 2026-08-05 00:05:49 | `file.write` | llmwiki/wiki/sources/ISSUES.md · tool=Edit · session=8a8ad17d · actor=agent · prev=9609959b4197aa2d2bd31daa165c933c424f8 |
| 2026-08-05 00:06:00 | `commit.reconcile` |  · actor=system · agent_n=2 · human_n=0 · prev=4336f77a3ce4a97f11ab3ffd6604086c6b11acb2f445c89e96391b6908dbe4bd · h=9434 |
| 2026-08-05 00:09:17 | `file.write` | llmwiki/wiki/sources/draft/050826-distill-zero-mem-graph-branch.md · tool=Write · session=5a9be8ac · actor=agent · prev= |
| 2026-08-05 00:09:28 | `file.write` | llmwiki/wiki/sources/ISSUES.md · tool=Edit · session=5a9be8ac · actor=agent · prev=115ce2f9cecc86e63bfb6569b45af0b58e2ec |
| 2026-08-05 00:09:48 | `file.write` | llmwiki/wiki/sources/ISSUES.md · tool=Edit · session=5a9be8ac · actor=agent · prev=f19e26b74b4d10955d8b0f1ed555118a875b9 |
| 2026-08-05 00:31:22 | `file.write` | llmwiki/wiki/sources/draft/050826-distill-zero-mem-graph-branch.md · tool=Edit · session=5a9be8ac · actor=agent · prev=f |
| 2026-08-05 09:07:25 | `file.write` | llmwiki/innovation/050826-innovation.md · tool=Write · session=d3d1153e · actor=agent · prev=cacfe103b57ee7dc8165c665c95 |
| 2026-08-06 09:07:16 | `file.write` | llmwiki/innovation/060826-innovation.md · tool=Write · session=2015d100 · actor=agent · prev=100900cda8e9f542902a6c111a3 |
| 2026-08-06 21:30:59 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/.claude/hooks/stop.py'] · prev=7fd509169ad2d44812fa78d7e24caaa |
| 2026-08-06 21:30:59 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=2 · human=['llmwiki/wiki/log.md', 'harness/poc-vendor-neutral/install.sh'] · prev= |
| 2026-08-06 21:31:00 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/.claude/hooks/stop.py'] · prev=e91712c74f4577298c817488aee925f |
| 2026-08-06 21:31:00 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['harness/tests/anti-idle-stop-test.sh', 'llmwiki/wiki/log.md', 'harness |
| 2026-08-06 21:38:41 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/log.md'] · prev=0e9ae81bfa7e43e932087e33bb49c4fff4d58dab4 |
| 2026-08-06 21:38:43 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/log.md'] · prev=b0745ed920eb86253bb3f1441bb053116794b587b |
| 2026-08-07 09:05:48 | `file.write` | llmwiki/innovation/070826-innovation.md · tool=Write · session=55337220 · actor=agent · prev=391ead7b79edd967e758d9a563a |
| 2026-08-07 23:22:45 | `task.new` |  · task=T-260807-01 · title=Windows PowerShell harness installer · state=proposed · actor=agent · prev=583dd4aadc6b64444 |
| 2026-08-07 23:24:31 | `file.write` | llmwiki/wiki/sources/draft/070826-windows-powershell-installer.md · tool=Write · session=63352240 · actor=agent · prev=8 |
| 2026-08-07 23:24:56 | `file.write` | llmwiki/html/070826-windows-powershell-installer-seq.html · tool=Write · session=63352240 · actor=agent · prev=751849ea4 |
| 2026-08-07 23:25:04 | `file.write` | llmwiki/html/070826-windows-powershell-installer-seq.html · tool=Edit · session=63352240 · actor=agent · prev=8ee679b427 |
| 2026-08-07 23:25:09 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=63352240 · actor=agent · prev=a05dab819e8adf92e3fbdc21d84f193a261f6c8adfcf3b |
| 2026-08-07 23:25:18 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=63352240 · actor=agent · prev=263b32fe60e84b52bd0b807f460aa64993358d7b28bb25c1 |
| 2026-08-07 23:25:57 | `file.write` | llmwiki/wiki/sources/draft/070826-windows-powershell-installer.md · tool=Edit · session=63352240 · actor=agent · prev=b1 |
| 2026-08-07 23:25:57 | `file.write` | llmwiki/wiki/sources/draft/070826-windows-powershell-installer.md · tool=Edit · session=63352240 · actor=agent · prev=87 |
| 2026-08-07 23:25:57 | `file.write` | llmwiki/html/070826-windows-powershell-installer-seq.html · tool=Edit · session=63352240 · actor=agent · prev=9cb7cc0742 |
| 2026-08-07 23:25:57 | `file.write` | llmwiki/html/070826-windows-powershell-installer-seq.html · tool=Edit · session=63352240 · actor=agent · prev=c71dcd66a6 |
| 2026-08-07 23:26:20 | `file.write` | llmwiki/wiki/draft/unknown/unknown-windows-hook-runtime.md · tool=Write · session=63352240 · actor=agent · prev=bcc2323f |
| 2026-08-07 23:40:22 | `task.set` |  · task=T-260807-01 · state=superseded · note=file SPEC/HTML/unknown đã xoá theo yêu cầu user 2026-08-07; backup ở scrat |
| 2026-08-07 23:42:06 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=0 · prev=601408d0dca99f51730493db84259d4a7eb4be75ad5d70db9300c3e97a86a8a4 · h=21d7 |
| 2026-08-07 23:42:06 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/sources/070826-session-provenance.md', 'harness/metrics/t |
| 2026-08-07 23:42:06 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/log.md'] · prev=9360090063d66d00323ac505e39fa50bdf8baf54e |
| 2026-08-07 23:42:08 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/sources/070826-session-provenance.md', 'harness/metrics/t |
| 2026-08-07 23:42:08 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/log.md'] · prev=dc556359918eb1637a3b8bf4b723eb4c7ffa0a6fe |
| 2026-08-07 23:42:08 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/index.md'] · prev=7e9024cee23d37070ab9e0594a92d8a22fca562 |
| 2026-08-07 23:44:41 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/log.md'] · prev=0b099ec3c34c33e0ba6bd223ca9f918c56c5a0355 |
| 2026-08-07 23:44:43 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['llmwiki/wiki/log.md'] · prev=a298d8c0621dedddb47b9e395179ec062e9470889 |
| 2026-08-09 08:13:48 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/index.md', 'llmwiki/wiki/log.md'] · prev=794600a446ec613a |
| 2026-08-09 08:13:48 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['harness/egress-guard.config.yaml', 'llmwiki/wiki/sources/090826-sessio |
| 2026-08-09 08:13:50 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/index.md', 'llmwiki/wiki/log.md'] · prev=91fba384937708bb |
| 2026-08-09 08:13:50 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['harness/egress-guard.config.yaml', 'llmwiki/wiki/sources/090826-sessio |
| 2026-08-09 09:15:59 | `file.write` | harness/scripts/token-attrib.py · tool=Write · session=b8afb386 · actor=agent · prev=3c0569fdc5fea42424acc73640c10720524 |
| 2026-08-09 09:15:59 | `file.write` | harness/scripts/token-attrib.py · tool=Write · session=b8afb386 · actor=agent · prev=8a1bc8ea88c167d0ea10662f4b29ba70489 |
| 2026-08-09 09:18:38 | `file.write` | harness/tests/token-attrib-test.sh · tool=Write · session=b8afb386 · actor=agent · prev=5e72a855945f0b56710e2cf344578fdd |
| 2026-08-09 09:18:38 | `file.write` | harness/tests/token-attrib-test.sh · tool=Write · session=b8afb386 · actor=agent · prev=2cd7e12490b429e81b3ef67cb78ddb1e |
| 2026-08-09 09:24:36 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=1 · human=['llmwiki/wiki/log.md'] · prev=30a8f7167a46b594fad119b5301d4f43bc5c8e170 |
| 2026-08-09 09:24:36 | `commit.reconcile` |  · actor=system · agent_n=1 · human_n=2 · human=['harness/scripts/fdk-gate.py', 'fdk/CAPABILITIES.md'] · prev=dca2f4a509 |
| 2026-08-09 09:24:36 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['harness/version.json'] · prev=bb74d81461d9f724092d338961e814947051f2f1 |
| 2026-08-09 09:24:38 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=3 · human=['harness/scripts/fdk-gate.py', 'harness/tests/token-attrib-test.sh', 'f |
| 2026-08-09 09:24:38 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=1 · human=['harness/version.json'] · prev=992d731569a307e767c64a4cc0af0152e43c8a02 |
| 2026-08-09 09:24:38 | `commit.reconcile` |  · actor=system · agent_n=0 · human_n=2 · human=['llmwiki/wiki/log.md', 'harness/scripts/token-attrib.py'] · prev=06ec1f |
| 2026-08-10 09:09:16 | `file.write` | llmwiki/wiki/sources/draft/100826-skill-behavioral-integrity-verification.md · tool=Write · session=12cffa69 · actor=age |
| 2026-08-10 09:09:43 | `file.write` | llmwiki/wiki/sources/ISSUES.md · tool=Edit · session=12cffa69 · actor=agent · prev=482105fc5c78199244cbe5774d59a23236a71 |
| 2026-08-10 09:11:05 | `file.write` | llmwiki/innovation/100826-innovation.md · tool=Write · session=12cffa69 · actor=agent · prev=a2bbab266bfecae768ee2869cfe |
| 2026-08-11 10:12:54 | `file.write` | llmwiki/wiki/entities/repowise.md · tool=Write · session=dba79064 · actor=agent · prev=652f0f23ce2a66575fa482784088b5e9f |
| 2026-08-11 10:13:30 | `file.write` | llmwiki/innovation/110826-innovation.md · tool=Write · session=dba79064 · actor=agent · prev=53d86eac11cf99766dd456c1f6a |
| 2026-08-11 10:13:36 | `file.write` | llmwiki/wiki/index.md · tool=Edit · session=dba79064 · actor=agent · prev=0e1c2cac6e226f975053a2e839d1ecf5dc3145126a8687 |
| 2026-08-11 10:13:43 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=78846909f59c5c5970efc7998ab2bd51ae56d6cee60679b9 |
| 2026-08-11 16:44:08 | `file.write` | harness/validators/code_complexity.py · tool=Write · session=dba79064 · actor=agent · prev=0a0f981ad6083af5cc1d542a50b7a |
| 2026-08-11 16:44:51 | `file.write` | llmwiki/innovation/110826-innovation.md · tool=Edit · session=dba79064 · actor=agent · prev=64fc7c174ddfb071c147c357f2fb |
| 2026-08-11 16:45:05 | `file.write` | llmwiki/wiki/log.md · tool=Edit · session=dba79064 · actor=agent · prev=460d7efdad92bc4ccc1b85f8a9952a9b0b89e1820333ac39 |

<!-- log:auto:end -->
