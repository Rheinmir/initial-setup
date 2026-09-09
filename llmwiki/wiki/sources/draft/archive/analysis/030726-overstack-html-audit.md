---
type: issue
kind: tech-debt
title: "overstack.html — audit đa-góc-nhìn: mâu thuẫn nội tại, lỗi thời 3 commit, UX (dark mode/search/a11y)"
status: done
assignee: "@Rheinmir"
dispatch: Claude
entry: /fdk
priority: P2
tags: [issue, overstack, docs, audit, generator, ux, drift]
timestamp: 2026-07-03
id: 030726-overstack-html-audit
source_session: "Phiên Fable đánh giá thuần overstack.html (không code); 3 subagent audit song song: nội-dung-vs-repo, mâu-thuẫn-nội-tại, UX/design."
---

# Issue: overstack.html — audit đa-góc-nhìn cần polish

## Vấn đề (một câu)
Trang docs chính thức `llmwiki/html/overstack.html` chính xác cao về số liệu (bake từ đĩa) nhưng mang **4 mâu thuẫn nội tại mức CAO**, **lỗi thời 3 commit** (thiếu hẳn GH#8 skill-usage analytics), và thiếu UX nền (dark mode / tìm kiếm / accessibility) — mọi fix phải làm trong generator `fdk/tools/build-overstack-docs.py`, không sửa tay HTML.

## Bối cảnh & bằng chứng
Trang sinh hoàn toàn bởi `fdk/tools/build-overstack-docs.py` (prose là chuỗi tay trong script; số liệu FACT pull live từ đĩa). Generator ghi đè `OUT = llmwiki/html/overstack.html` và có `--check` (exit 2 nếu file lệch bản sinh, được medic/docs-probe gọi) → **sửa tay HTML sẽ bị bắt là drift và mất khi regen**. HTML regen lần cuối ở commit `5f34d2d`; HEAD hiện đi trước 3 commit.

Ba audit song song (phiên 2026-07-03, chỉ đọc). Các mục số liệu đã được verify lại từ đĩa và **khớp 100%**: skill 71, rule 17, validator 14, hook 10, cơ chế 17, script 44, 18 persona-lens, URL bootstrap. Liên quan: [[030726-skill-usage-dashboard]] (GH#8, phần lỗi thời chính).

### A. Mâu thuẫn nội tại
- **[CAO] 3 lớp gác vs 4 lớp gác** — trong cùng tab Harness: đầu tab "phải qua 3 lớp gác" (L0→L2→L4); ngay dưới heading "Bốn lớp gác (L0–L4)" liệt kê L0/L1/L2/L4. **L3 không tồn tại ở đâu** và không giải thích. Tab Tham chiếu lại nói "3 lớp".
- **[CAO] "Mỗi rule = 1 validator" vs FACT "17 rule, 14 validator"** — hai mệnh đề không thể cùng đúng. Thực tế: một số rule enforce qua hook, không có validator file riêng (chỉ 10 rule được tag tường minh trong validator source; commit `ef12c4a` xác nhận 17/17 có bite-test). Slogan phóng, bảng FACT đúng → trang tự đá nhau.
- **[CAO] R10 mô tả 2 kiểu khác nhau** ở 2 chỗ (trụ thứ hai là `/orca-workflow` hay `wikieval`?). Hệ quả trực tiếp của **bảng rule bị lặp nguyên văn ×2** — mỗi bản lặp là mầm drift, và drift đã xảy ra.
- **[CAO] BNAL "20 verified:false" không tự khớp** — liệt kê chỉ ra 15, và 5 mục `verified:true` nằm ngay cạnh; 20 = 15+5 thì nhãn sai.
- **[VỪA] Quickstart tự mâu thuẫn về lệnh phải nhớ** — mở đầu bảo nhớ `/propose`, bước 3 bảo gọi `/orca-workflow` và "hiếm khi gọi tay skill con". Nên thống nhất quanh `/orca-workflow` (entry đúng).
- **[THẤP]** "trụ" mang 2 nghĩa (5 trụ AgentOps vs 2 trụ docs-gate, trang phải tự chú thích); 2 persona cùng viết tắt **LT** (Lão Tử vs Linus); "trang chỉ tạo SAU commit" vs luồng propose viết draft TRƯỚC — không nói draft được miễn trừ.

### B. Lỗi thời so với repo
- **[CAO] Thiếu hoàn toàn skill-usage analytics + weekly dashboard (GH#8, `7bf48e8`)** — grep 0 hit. Regen sau khi bổ sung nội dung.
- **[VỪA]** `/raise-issue` và `/ovs-notes` vẫn nằm nhóm "❓ chưa phân loại" trong khi `llmwiki/AGENT.md` đã xếp vào loop `utils` → sửa `LOOP_GROUPS` trong generator.
- **[THẤP]** Claim "2 phút" (Quickstart) không có nguồn/lệnh tái tạo — trái chuẩn FACT trang tự đề ra. ("0 token" thì hợp lý.)

### C. Cấu trúc & trùng lặp (nguồn chính của file 144KB)
- Bảng 17 rule lặp **×2** nguyên văn; danh sách 17 cơ chế **×3**; danh sách skill **×3 trong riêng tab Tham chiếu**; hướng dẫn cài curl **×2**; "medic gương-soi" lặp 2 lần liền nhau trong tab 14.
- Cross-reference lệch: tab Harness bảo mind map "cuối trang" nhưng nav đặt nó ở tab 02 — **trước cả Cài đặt**, người mới đập mặt vào bảng tra cứu 71 mục trước khi biết cài.
- **Giọng maintainer rò vào tài liệu user**: TODO nội bộ ("chưa phân loại, thêm vào LOOP_GROUPS"), mốc nội bộ ("bài học 250626 'sao xấu thế'"), skill đặc thù dự án khác (`/check-approve` DMS, `/snapshot-push` bonbon-ai) liệt kê ngang hàng skill framework.
- Thuật ngữ nhắc nhiều nhưng không định nghĩa: **OKF v0.1, dark-rail, ADR-xxx (đọc ở đâu?), pass^k, 5 phase persona Boris, "the kit"**.

### D. UX / thiết kế
- **Tốt**: hệ token glass nhất quán, line-length có kiểm soát, không asset thừa (144KB toàn text thật + 148 node mind-map), scroll-spy + copy-button + reduced-motion chuẩn.
- **[CAO] Không có dark mode** — 0 `prefers-color-scheme`; hạ tầng CSS var đã sẵn, chi phí thấp.
- **[CAO] Không có tìm kiếm** + anchor chỉ cấp section `#s0…#s16` (theo chỉ số, gãy nghĩa khi reorder). 9.400 từ / 17 section.
- **[CAO] Accessibility gần 0** — 148 node mind-map là `div` clickable không tabindex/aria (vô hình với bàn phím + screen-reader); nút ☰/✕ không aria-label; không skip-link.
- **[THẤP]** emoji làm icon nav (điểm "AI-slop" dễ thấy nhất); h3 15.5px gần bằng body → hierarchy yếu; 4/5 bảng không bọc `overflow-x` → nguy cơ tràn ngang mobile.

## Phạm vi
- `fdk/tools/build-overstack-docs.py` (nguồn duy nhất — CSS/JS/prose đều là chuỗi trong script).
- `llmwiki/html/overstack.html` (artifact sinh ra; không sửa tay).
- Universal cho framework overstack (không phải local một dự án downstream).

## Không thuộc phạm vi
- Không sửa tay HTML.
- Không đổi engine harness/validator/rule thật (đây là vấn đề tài liệu, không phải hành vi hệ).
- Không viết lại toàn bộ trang — chỉ sửa nguồn generator có mục tiêu.

## Hướng gợi ý (không bắt buộc)
**Đợt 1 — sửa sự thật:** chốt "4 lớp L0–L4" + giải thích L3 vắng (hoặc đánh lại số); sửa slogan thành "17 rule, enforce bởi 14 validator + hook"; chốt một mô tả R10; sửa nhãn BNAL 20/15+5; thống nhất Quickstart quanh `/orca-workflow`; cập nhật `LOOP_GROUPS` (raise-issue, ovs-notes); thêm mục GH#8. **Chống drift tận gốc**: render bảng rule/cơ chế/skill từ MỘT nguồn dùng chung trong generator (không copy chuỗi 2–3 nơi) — fix quan trọng nhất vì mâu thuẫn R10 sinh từ lặp.

**Đợt 2 — UX:** dark mode qua token hoá + `@media (prefers-color-scheme: dark)`; search Ctrl-K client-side (filter h2/h4/tên skill) + anchor semantic (`#harness`…) + id trên h3/h4; a11y pass tối thiểu (~20 dòng: aria nav toggle, `role/tabindex/Enter` cho node mind-map, skip-link); bọc 5 bảng trong `.table-wrap`.

**Đợt 3 — biên tập:** tách giọng (dời TODO nội bộ + skill đặc-thù-dự-án sang tab FDK); thêm glossary ngắn (OKF, ADR, dark-rail, pass^k, 5 phase Boris); đổi 1 trong 2 "LT"; cân nhắc dời tab Tham chiếu xuống sau Cài đặt.

## Tiêu chí HOÀN THÀNH
- `python3 fdk/tools/build-overstack-docs.py --check` pass (không drift).
- Grep "skill-usage"/"dashboard" trong HTML có hit (GH#8 xuất hiện).
- Không còn "3 lớp" và "4 lớp" đồng thời; L3 hoặc tồn tại hoặc số được đánh lại nhất quán; slogan validator khớp bảng FACT; R10 mô tả một lần duy nhất; nhãn BNAL tự khớp.
- Bảng rule/cơ chế/skill render từ một nguồn (grep xác nhận không còn bảng rule lặp nguyên văn ×2).
- `prefers-color-scheme: dark` có mặt; node mind-map keyboard-accessible; 5 bảng bọc overflow-x.
- `/raise-issue` và `/ovs-notes` nằm đúng nhóm `utils` trong mind map.

## Assign & lý do
`@Rheinmir` (chủ framework), entry `/fdk` vì đây là dev CHÍNH framework (generator + docs). Dispatch Claude: công việc chủ yếu là biên tập generator Python + CSS/JS có mục tiêu, không cần đa-model. Nên làm theo 3 đợt — đợt 1 (sự thật + chống-drift) là ưu tiên vì đang gây hiểu sai cho người cài mới.

## Origin
Raise bởi skill `/raise-issue` (phiên Fable 2026-07-03). Nguồn bằng chứng: 3 subagent audit song song trên `llmwiki/html/overstack.html` (nội-dung-vs-repo verify từ đĩa tại HEAD ~v1.0.6+2; mâu-thuẫn-nội-tại; UX/design) + generator `fdk/tools/build-overstack-docs.py`. Không code trong phiên phát hiện — cố ý defer để handoff.

## Kết quả (2026-07-04 — done, đợt 1+2)
Mọi sửa ở generator `fdk/tools/build-overstack-docs.py` (không sửa tay HTML). `--check` pass.
- **Đợt 1 (sự thật + chống-drift):** bỏ mâu thuẫn "Bốn lớp gác" → "Ba lớp CHẶN" + giải thích L3 để trống có chủ đích; slogan "mỗi rule = 1 validator" → "enforce bởi validator + hook" (khớp FACT 17 rule/14 validator) ở cả 3 chỗ; nhãn BNAL tự khớp động (N = X false + Y true); **bảng rule render 1 lần** (bỏ lặp ×2 ở tab Tham chiếu → link tới tab chủ đề); LOOP_GROUPS thêm ovs-notes + frontier-scan (hết "chưa phân loại"); GH#8 skill-usage xuất hiện (auto-derive từ mechanisms.yaml). File 137KB→124KB.
- **Đợt 2 (UX):** dark mode qua `@media (prefers-color-scheme: dark)` + token override; mọi bảng bọc `.table-wrap` (overflow-x — trước class dùng mà KHÔNG có CSS); mind-map node keyboard-accessible (tabindex/role=button/aria-expanded + Enter/Space); skip-link + aria-label nút nav.
- **Đợt 3 (biên tập — defer):** glossary, tách giọng maintainer, đổi 1 "LT" trùng — không thuộc tiêu chí HOÀN THÀNH, để lần sau.
