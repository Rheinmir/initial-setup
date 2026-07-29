---
name: fdk
disable-model-invocation: true
description: Front-door on-demand cho phát triển framework HOẶC distill/author một skill — SELF-CONTAINED, chạy được ở BẤT KỲ project nào (không phụ thuộc file repo-local). Gọi khi đang sửa chính framework, hoặc đang viết/chưng cất một skill trong phiên của dự án khác. KHÔNG dùng cho dev tính năng dự án thường (đó là phần lớn phiên — ADR-004).
---

# Skill: fdk — Framework Dev Kit (self-contained)

On-demand: KHÔNG auto-bơm đầu phiên (phần lớn phiên là dev dự án khác). Skill này **tự chứa đủ** guidance để chạy ở bất kỳ project nào; mục "bản đầy đủ" ở cuối chỉ áp dụng KHI bạn đang ở trong repo framework.

## Tư tưởng mặc định — Donella Meadows: sửa HỆ THỐNG, đừng sửa triệu chứng
Mọi việc framework đi qua lens tư duy hệ thống & vòng phản hồi (systems thinking, *Thinking in Systems*):
- **Gặp lỗi/vấn đề → hỏi "cấu trúc nào sinh ra nó?"** trước khi vá chỗ đau. Một triệu chứng lặp lại là tín hiệu của vòng phản hồi thiếu hoặc sai — vá tay lần thứ 2 cho cùng một loại lỗi là sai quy trình; đúng là đổi cấu trúc (rule harness, skill, template, hook) để loại lỗi đó không tái sinh. (Đây chính là failure-flywheel và problem-tree đang làm.)
- **Chọn điểm đòn bẩy (leverage point) cao nhất với chi phí thấp nhất**, theo thang Meadows: sửa tham số < thêm vòng phản hồi < đổi luồng thông tin < đổi luật chơi < đổi mục tiêu/paradigm. Trước khi code, tự hỏi: fix này nằm ở bậc nào? Có bậc cao hơn rẻ không? (Vd: thay vì dặn agent nhớ — bậc thấp — thì thêm validator tự cắn — đổi luật chơi.)
- **Nuôi vòng phản hồi, đừng chỉ bắn một phát**: mỗi thay đổi phải có đường tín hiệu quay về (verify tất định, ledger, log, eval) để hệ tự thấy mình lệch. Thay đổi không có feedback loop = thay đổi mù.
- **Tôn trọng độ trễ (delay)**: hiệu ứng của rule/skill mới chỉ lộ sau nhiều phiên — đừng kết luận sớm, cũng đừng chồng thêm fix khi fix trước chưa kịp phát tác; ghi ngày vào ledger để đo.

## Kim chỉ nam thứ 2 — Hub & trình bày (UX cho user, feedback 2026-07-03)
Cạnh tư duy Meadows, mọi tool/skill/hub framework tuân nguyên tắc dùng-được-và-an-toàn của user:
- **Hub 1-tên, mô tả-phạm-vi — đừng bắt nhớ nhiều lệnh con.** Một hub làm HẾT việc liên quan; user chỉ mô tả *phạm vi* (all > 1 phần / phần tương đương / mức độ), không phải nhớ subcommand. Tên lệnh phải NGẮN, gõ được bằng cơ-bắp (user quen `curl`; tên khó nhớ = không bao giờ được gọi → vô dụng). Vd `medic` (cổng sức khoẻ tổng) thay tên dài.
- **TL;DR — phần user đọc cô đọng + ĐỦ ý, không dè sẻn.** User có thói quen "too long didn't read": ngắn nhưng không cụt, không ki bo giải thích.
- **Model tư duy minh bạch** — user đọc phần *think* để kiểm hướng đi. Đừng giấu suy luận.
- **Cuối output: inject recap + dạy dùng thụ động** — nhắc lại tinh gọn tool này làm gì + hint use-case tiêu biểu VÀ bất ngờ (user không ngờ cũng dùng được) → user học cách dùng mà không phải hỏi.
- **Minh bạch = an toàn; usage > performance.** Cho user ĐỌC ĐƯỢC cấu trúc thư mục + under-the-hood, không chỉ tối ưu cho query. Đã hiển thị thì transparent → user thấy an toàn khi dùng hệ. Ưu tiên tính-dùng-được hơn tối ưu ngầm.

## Khi nào dùng
- Đang sửa CHÍNH framework (skill / rule / validator / hook / wiki), HOẶC
- Đang distill / author một skill trong phiên của project bất kỳ.

## Pre-flight — chạy trước mọi thay đổi framework/skill
1. **Pull trước khi sửa** — đồng bộ base, đừng làm trên bản cũ.
2. **Biết luật** — nếu repo có harness: xem `rule-registry` / `policy.yaml`. Luật phổ quát luôn đúng: file wiki phải có `## Origin`; không ghi `raw/`; file wiki đúng subfolder (concepts/entities/sources/draft/…); proposal phải đủ cặp `.md`+`.html`.
3. **Đừng dẫm module cũ** — trước khi tạo skill/validator/script/hook mới, **grep tên** xem đã tồn tại chưa; sửa code dùng-chung thì map caller trước (impact-check) rồi safe-change.
4. **Propose trước** — mọi thay đổi → draft kế hoạch, STOP chờ duyệt; đừng code thẳng.
5. **Surgical → verify → ghi vết** — chỉ chạm cái buộc phải chạm; chạy test/drift-test; cập nhật registry/log.

## Distill / author một skill (dùng ở project bất kỳ)
- 1 skill = 1 file `SKILL.md`: frontmatter `name` + `description`, rồi `## When to use`, `## Steps`, `## Rules`.
- `description` phải **đủ trigger** — nêu rõ KHI NÀO gọi (từ khoá, tình huống); đây là thứ router dùng để chọn skill.
- `## Steps` = các bước cụ thể, kiểm chứng được. `## Rules` = ràng buộc + anti-pattern.
- Giữ **self-contained**: đừng trỏ tới file chỉ có ở 1 repo; nếu cần thì ghi "nếu file X có mặt thì…".
- Sau khi viết: thử 1–2 câu mẫu xem skill có được trigger đúng không.

## Inventory — đừng tin số nhớ, đếm LIVE (path tuỳ layout repo)
```bash
ls -d skills/*/ 2>/dev/null | wc -l                                   # số skill
ls harness/validators/*.py 2>/dev/null | wc -l                        # số validator
grep -cE 'id: R' harness/poc-vendor-neutral/policy.yaml 2>/dev/null   # số rule
```

## Problem-tree — sổ vấn đề CHUNG của cả framework (không riêng /fdk)
`llmwiki/html/fdk-problem-tree.html` là ledger duy nhất cho MỌI vấn đề framework — bất kỳ skill/phiên nào chạm việc framework (propose, harness-update, orca-workflow…) phát hiện hay giải một vấn đề đều phải cập nhật nó; /fdk là người gác: mỗi lần /fdk được gọi, TRƯỚC KHI kết thúc turn phải rà và cập nhật cây (tạo từ template nếu chưa có; không ở repo framework nhưng project có `llmwiki/` thì dùng path project-local cùng tên):
- **Dạng**: single-file HTML style /docs-site-macos (liquid-glass). Nội dung = **cây vấn đề** — mỗi node là một bài toán gặp trong session; node nối cha→con bằng SVG connector do JS tự vẽ (đo `getBoundingClientRect`, vẽ lại khi resize) — không hardcode toạ độ.
- **Data tách khỏi markup**: toàn bộ node nằm trong một block `<script type="application/json" id="tree-data">`; mỗi lần update chỉ thêm/sửa JSON, không đụng markup. Mỗi node: `{id, parent, title, desc, status: solved|partial|open, scope: "full" | ["harness"|"skills"|"llmwiki"...], date, solvedBy?, session?}`.
- **Scope là biến cố định theo 3 trụ**: `"full"` = giải trọn cả 3 trụ (harness + skills + llmwiki); còn không thì liệt kê danh sách trụ đã phủ (vd `["skills"]` = mới giải ở tầng skill). `status: solved` mà `scope` chưa full thì cây phải hiện rõ "solved x/3 trụ" — không được đọc nhầm thành giải trọn.
- **Append-only về lịch sử**: không xoá node cũ; vấn đề được giải thì đổi `status` + ghi `solvedBy` (giải bằng skill/rule/commit nào).
- **Màu theo ĐỘ PHỦ, không theo status**: xanh lá CHỈ khi giải trọn 3/3 trụ; thang nghiêm-trọng-giảm-dần: 0/3 (chưa có gì — nghiêm trọng nhất) = đỏ `#ef4444` → 1/3 = cam `#f97316` → 2/3 = vàng `#eab308` → 3/3 = xanh lá `#22c55e`. Badge ghi kèm x/3. Không bao giờ tô xanh lá cho thứ mới giải một phần.

## Adapt vào overstack remote — khi đang dev TỪ một dự án khác
Đang dở dự án khác mà muốn chưng cất một skill rồi đẩy vào overstack? `fdk-gate` + `fdk/tools` KHÔNG có ở dự án đó (cố ý — ADR-004), nên kéo **kit** về sandbox rồi submit bằng PR — đừng sửa tay lung tung:

1. **Pull kit** (lần đầu — chạy thẳng từ remote, không cần file local):
   ```bash
   bash <(curl -fsSL https://raw.githubusercontent.com/Rheinmir/setup/orca/fdk/tools/fdk-kit.sh) pull
   ```
   → clone overstack vào `.overstack-kit/` (tự thêm vào `.gitignore`, KHÔNG đụng dự án của bạn).
2. **Distill skill TRONG kit:** `cd .overstack-kit && python3 fdk/tools/new-skill.py <tên>` → viết `SKILL.md` → register (mirror + LOOP_MAP + bảng AGENT/CLAUDE + CAPABILITIES — pre-flight #3 + checklist).
3. **Check:** `bash .overstack-kit/fdk/tools/fdk-kit.sh check` — `fdk-gate` đủ 15 bước mới hợp lệ.
4. **Submit (TỰ mở PR):** `bash .overstack-kit/fdk/tools/fdk-kit.sh submit skill/<tên> "<mô tả>"` → gate xanh → push branch → `gh pr create` vào `orca`.

Đang Ở TRONG repo overstack thì bỏ qua bước pull — `fdk-kit check` / `submit` chạy thẳng trên repo.

## Nếu đang TRONG repo framework (Rheinmir/setup) — bản đầy đủ
Các file dưới đây CHỈ có trong repo framework, KHÔNG distribute xuống project khác (cố ý — ADR-004). Khi có mặt thì đọc để lấy bản chi tiết:
- `fdk/wiki/concepts/fdk.md` — front-door đầy đủ (pre-flight + module map theo loại).
- `fdk/docs/CONTRIBUTING.md` — runbook thêm/sửa **rule harness** (content-check / hook-event / process-gate; số kế tiếp R13).
- `fdk/README.md` + `fdk/tools/` — kit folder (vd `build-cheatsheet.py`).
- **Sửa SKILL.md xong → `bash fdk/tools/sync-skill.sh <tên>`** — đồng bộ canonical → mirror llmwiki + bản cài `~/.claude` trong 1 lệnh, tự verify parity. ĐỪNG cp tay từng bản (nguồn drift — eval 020726).
- `llmwiki/html/*-fdk-docs.html` — bản đọc HTML.

## Rules
- **BẰNG CHỨNG > LỜI: kiểm UI/thị giác chỉ hợp lệ khi có FILE ẢNH thật, liệt kê ra.** (feedback 2026-07-13: "chỉ tin file không tin think"). Cấm tuyên bố một UI/route "pass/đẹp/fixed" chỉ bằng suy luận (`think`) — phải: (1) chạy visual-qa chụp thật → sinh `MANIFEST.json` liệt kê MỌI route đã test → file ảnh + bytes; (2) **không có file ảnh (hoặc bytes=0) = CHƯA TỪNG LÀM = fail**, bất kể model nói gì; (3) sau khi SỬA UI phải chụp LẠI và đọc lại ảnh trước khi cho green (re-verify bằng file, không bằng lời). Điểm đòn bẩy Meadows: đổi luồng-thông-tin sang artifact kiểm được, thay vì tin phát biểu. Đây cũng là luật của dây chuyền /br (frame `ui_role≠none`) — xem skill `br` § "Vòng tự-kiểm THỊ GIÁC" + skill `visual-qa`.
- **TRƯỚC KHI ship push/PR — đối chiếu với luồng CI GitHub, không chỉ pre-commit.** L2 (pre-commit) KHÔNG bằng L4 (CI fresh-clone): có gate CHỈ chạy trên CI, hoặc auto-fix chạy ở Stop-hook (cuối lượt) nên commit-rồi-push-ngay lọt qua L2 mà CI đỏ (đã cháy: R3 index-sync bắt draft mới thiếu `wiki/index.md` — fix ở Stop-hook không kịp trước commit; xem `[[harness-enforcement-floor]]`). Nên trước mọi push: (1) chạy `python3 fdk/tools/medic.py --ci`; (2) chạy TRỌN các step job `repo health` trong `.github/workflows/harness.yml` tại local (R3 index-sync cả `llmwiki/wiki` + `fdk/wiki`, wiki-health, arch-scan, `code_health.py`, harness-lint, agent-parity, dup-basename, auto-index-test, R13 gate, policy-converters-drift, harness-doctor --ci, `build-capabilities.py --check`, adapt-registry --check). Xanh hết mới push → không đẩy đỏ lên CI. Ship skill nên gọi bước này ở checklist.
- **KHÔNG ghi công AI** — commit message / PR / code / wiki KHÔNG được chèn `Co-Authored-By: Claude…`, `Generated with Claude Code`, `🤖`, hay bất kỳ credit/attribution nào cho AI. Author & committer chỉ là danh tính người dùng. Nếu template/tool sinh sẵn trailer ghi công thì cắt bỏ trước khi commit.
- **On-demand only** — không đăng ký hook auto-fire đầu phiên (ADR-004).
- **Self-contained** — phần trên (pre-flight + distill + inventory) đủ chạy ở project khác; mục "bản đầy đủ" chỉ áp dụng KHI các file đó tồn tại. Không bao giờ giả định file repo-local có mặt.
- Đếm số luôn LIVE; không hardcode (anti-drift).
- **HTML cho NGƯỜI đọc phải giải nghĩa thuật ngữ** — nội dung hiển thị trong report/visualization (title, mô tả node, chú thích) viết tiếng Việt thường; thuật ngữ chuyên ngành bắt buộc kèm giải nghĩa ngắn trong ngoặc ngay lần xuất hiện đầu (vd: "flush (xả sổ — tự ghi trước khi thoát)", "untracked (file git chưa theo dõi)"). Không viết tắt jargon trần cho người xem — jargon trần chỉ được phép trong file máy đọc.
- **HTML cho người xem phải có TOGGLE sáng/tối (feedback 2026-07-06 — nhắc lần 2, không tái phạm)** — mọi file HTML sinh ra để NGƯỜI xem (report, cây, dashboard, docs, proposal render…) phải có nút chuyển dark/light: `prefers-color-scheme` chỉ là mặc định ban đầu, user bấm toggle thì override qua `html[data-theme]` + lưu `localStorage` (kèm script chống FOUC trong head). KHÔNG ép cứng một mode. Dạng bắt buộc: NÚT GẠT (switch) có nhãn, hàng footer dính đáy sidebar/nav — KHÔNG chip icon rải góc. Snippet chuẩn: skill `docs-site-macos` § "Theme Toggle sáng/tối"; generator tham khảo `_DARK_RULES` trong `fdk/tools/build-overstack-docs.py` (một nguồn emit 2 khối, chống drift).
- **HTML cho người xem: THANG CỠ CHỮ COMPACT cho màn 13″** (feedback 2026-07-06) — GIẢM size chứ không tăng: body ~13.5px, nav 12px, list/bảng 12.5px, nhãn 10–10.5px; tăng cỡ chữ làm màn 13″ tệ hơn (ít nội dung, wrap chật). Dễ đọc = line-height/contrast, không phải font to. Chi tiết: docs-site-macos § Best Practices.
- **HTML report/visualization phải SHOW FULL PATH** — mọi file HTML sinh ra để xem (report, cây, dashboard, proposal render…) phải hiển thị đường dẫn tuyệt đối của chính nó ngay trên trang (footer hoặc titlebar, dạng `<code>` copy được), để người xem biết file nằm đâu mà mở lại/sửa. Sinh file xong phải điền path thật, không placeholder.
