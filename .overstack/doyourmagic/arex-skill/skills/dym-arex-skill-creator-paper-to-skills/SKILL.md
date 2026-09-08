---
name: dym-arex-skill-creator-paper-to-skills
description: "Creator: paper → skill tái lập được (Distiller). Có một bài báo cần tái lập, và muốn kết quả là skill module hoá đã verify chứ không phải một bản tóm tắt."
disable-model-invocation: true
---

# Skill: dym-arex-skill-creator-paper-to-skills — Creator: paper → skill tái lập được (Distiller)

**Vì sao dùng:** Có một bài báo cần tái lập, và muốn kết quả là **skill module hoá đã verify** chứ không phải một bản tóm tắt.
**Sinh ra cái gì:** `<workspace_root>/<paper_slug>/skills/` (skill sinh ra, còn là staging cho tới khi được duyệt import) và `<workspace_root>/<paper_slug>/distillation/reports/final/` (báo cáo cuối).

---

## 1. Chuẩn bị file config

Có **hai** file TOML trong repo, cùng schema:

| File | Vai trò |
|---|---|
| `examples/creator/paper-to-skills/distiller-run-config.toml` | Starter đã chú thích kỹ — **dùng cái này** |
| `cli/packages/coding-agent/src/disco/skills/create-paper-skills/assets/distiller-run-config-template.toml` | Template canonical do skill giữ |

Từ gốc checkout AREX-Skill:

```bash
cp examples/creator/paper-to-skills/distiller-run-config.toml \
  /absolute/path/to/distiller-run-config.toml
```

## 2. Điền tối thiểu 3 trường

```toml
schema_version = 1

[defaults]
workspace_root = "/absolute/path/to/paper2skills-workspace"   # ① BẮT BUỘC sửa

[[runs]]
paper_slug   = "my_paper_slug"          # ② BẮT BUỘC sửa
paper_source = "/path/to/paper.pdf"     # ③ BẮT BUỘC sửa
original_repo_source = "unknown"
```

`paper_source` nhận: đường dẫn PDF/text local · URL PDF trực tiếp · URL hoặc mã arXiv · **tên bài báo**.
`original_repo_source` nhận: đường dẫn repo local · URL Git/GitHub · `"none"` · `"unknown"`.

Thêm bài thứ hai = thêm một khối `[[runs]]` nữa.

## 3. Các knob nên hiểu trước khi chạy (không phải mặc định nào cũng vô hại)

| Trường | Mặc định | Ý nghĩa |
|---|---|---|
| `recovery_mode` | `"hard"` | **`hard`**: các lần chạy reduced/proxy/toy/fallback chỉ được ghi làm *chẩn đoán*, **không** tính là recovery thành công. Muốn chấp nhận chúng thì phải chọn `soft` một cách tường minh |
| `ask_before_expensive_recovery` | `true` | Dừng hỏi trước khi đốt tài nguyên |
| `repo_discovery_mode` | `"ask"` | `ask` dừng hỏi trước khi đi tìm repo cài đặt · `auto` tự tìm GitHub và clone ứng viên đầu · `disabled` không bao giờ tự tìm |
| `allow_title_top_hit` | `false` | Không tự nhận kết quả đầu tiên khi tra bằng tên bài báo |
| `iteration_budget` | `10` | Số vòng refine tối đa |
| `network_timeout_seconds` | `120` | |
| `command_timeout_seconds` | `20` | |
| `runtime_constraints` | (chuỗi) | Mặc định starter cấm động vào conda env dùng chung, bắt dùng env cô lập |
| `test_root` / `skills_root` / `generated_skills_root` / `distiller_skills_root` / `attempt_dir` | `""` | Để trống là dùng layout mặc định dưới `workspace_root` |

Mọi trường trong `[defaults]` đều override được ở từng `[[runs]]`; để chuỗi rỗng `""` là kế thừa. Các override số/bool phải **bỏ comment** mới có tác dụng.

## 4. Chạy

```bash
disco --creator -p "/skill:create-paper-skills Use Distiller to generate and verify paper-replication skills for each run in this config. config_path: /absolute/path/to/distiller-run-config.toml"
```

Dạng ngắn (Creator tự chọn entry):

```bash
disco --creator -p "Use Distiller to generate and verify paper-replication skills for each run in this config. config_path: /absolute/path/to/distiller_run_config.toml"
```

## 5. Distiller làm gì (đừng gọi tay từng bước)

`create-paper-skills` ủy thác toàn bộ cho `paper-skills-distiller`, chuỗi này tự nạp các skill hỗ trợ:

1. Giải nguồn bài báo (`plan-paper-skill-modules` dựng profile + kế hoạch module + tài liệu module);
2. Sinh & validate skill mức module (`create-paper-module-skill`);
3. Chuẩn bị bằng chứng runtime có giới hạn (`prepare-paper-recovery-env`: package, model, data, runtime);
4. Chạy thí nghiệm recovery **mạnh nhất khả thi**, **không đọc repo cài đặt gốc** (`recover-paper-result`);
5. Phân tích khoảng cách so với mục tiêu bài báo → accept / refine / blocker (`analyze-paper-recovery`);
6. Refine trong `iteration_budget` nếu cần;
7. Ghi artifact từng lần thử + báo cáo cuối.

## 6. Đầu ra ở đâu

```text
<workspace_root>/<paper_slug>/skills/                       # skill sinh ra — STAGING
<workspace_root>/<paper_slug>/distillation/reports/final/   # báo cáo cuối
```

Cây `skills/` vẫn là **staging** cho tới khi được duyệt và import. Sau validation cuối, Creator đề xuất **một** deployment scope cho toàn bộ graph, chỉ import sau khi bạn duyệt, rồi viết handoff cho Researcher.

## 7. Cạm bẫy

- **`recovery_mode = "hard"` là mặc định có chủ đích.** Thấy báo cáo ghi "diagnostic" chứ không phải "recovered" thì đó là hành vi đúng, không phải lỗi.
- **Đừng gọi tay từng paper skill.** Một run bình thường chỉ cần một lệnh `create-paper-skills`.
- **`workspace_root` phải là đường dẫn tuyệt đối** và ghi được — mọi bằng chứng, skill, artifact đều đổ vào đó.
- **Đường dẫn config truyền cho DisCo phải tuyệt đối.**

## Bước kế

`07-tich-hop-ci.md` nếu muốn khoá phiên bản thư viện trong CI của **dự án bạn**.
