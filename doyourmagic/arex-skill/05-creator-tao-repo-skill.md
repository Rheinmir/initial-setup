# 05 — Creator: tạo / verify / refresh / extend một repo skill

**Vì sao dùng:** Repo bạn cần chưa có trong thư viện 1.000 skill, hoặc skill có sẵn đã lệch so với upstream.
**Sinh ra cái gì:** Một graph skill tự chứa (`SKILL.md` + `sub-skills/` + `references/` + `scripts/`) đã qua verify, kèm artifact review nằm **ngoài** cây runtime.

---

## 0. Ranh giới mode (đọc trước, đỡ mất lượt)

| Mode | Nhìn thấy skill nào | Nhiệm vụ |
|---|---|---|
| **Researcher** (mặc định) | `operating` + `shared`, kể cả user skill không khai `metadata.disco-role` | Dùng kiến thức vận hành để **làm** việc nghiên cứu |
| **Creator** | `metadata.disco-role: meta` + `shared` | **Chế tạo** và bảo trì skill |

Creator có 15 meta skill (đếm được: 15 thư mục khai `disco-role: meta` trong `cli/packages/coding-agent/src/disco/skills/`). Hai thư mục còn lại: `repo-skills-router` là `operating`, `workflow-authoring` là `shared`.

Mở Creator:

```bash
disco --creator                      # tương tác
disco --creator -p "<yêu cầu>"       # một phát rồi thoát
```

## 1. Điểm vào chuẩn khi chưa biết chọn đường nào

```bash
disco --creator -p "/skill:distill-ml-knowledge identify <source or task anchor>; scope, ground, construct, and verify the operating skill graph."
```

`distill-ml-knowledge` xác định anchor rồi lái qua 4 pha: **scope → ground → construct → verify**. Nguồn là repository thì nó thường tái dùng `create-repo-skill`; nguồn là paper thì đi đường paper (xem `06`). Chỉ khi có **bằng chứng về một lỗ hổng năng lực lặp lại** nó mới chuyển sang `design-meta-skill`.

## 2. Tạo repo skill

```bash
disco --creator -p "/skill:create-repo-skill Create and verify a repository skill for /absolute/path/to/repo."
```

Rút gọn (Creator tự chọn entry):

```bash
disco --creator -p "Create a repo skill for /path/to/repo."
disco --creator -p "Create a skill for /path/to/repo using Python /path/to/env/bin/python"
```

Ủy quyền luôn cả chọn phạm vi trích xuất **và** import vào thư viện sau khi verify xanh — chỉ thêm khi bạn thực sự muốn bỏ hai cổng duyệt đó:

```bash
disco --creator -p "Create a repo skill for /path/to/repo with auto decide and auto import."
```

Workflow làm: phân tích cấu trúc repo → chuẩn bị/kiểm môi trường Python inspection (qua `prepare-repo-skill-env`) → viết guidance runtime → ghi provenance → bàn cho `verify-repo-skill`.

## 3. `verify-repo-skill` gác cái gì

- Sinh **usability case có assertion**;
- Tự tinh chỉnh ở mức nội dung (self-refinement);
- Chạy example/test native an toàn nếu repo có;
- Cổng chất lượng tĩnh;
- Ghi artifact coverage + review.

Chỉ qua hết mới coi là "ready". Artifact review **không** nằm trong cây runtime skill.

## 4. Refresh — khi upstream đã đổi

```bash
disco --creator -p "/skill:refresh-repo-skill Refresh /absolute/path/to/existing-skill against the current repository at /absolute/path/to/repo."
```

Dạng ngắn: `disco --creator -p "Refresh the skill at /path/to/repo/skills/example-skill against the current /path/to/repo code."`

Refresh **giữ guidance còn đúng**, chỉ đối chiếu phần đã cũ với baseline nguồn hiện tại.

## 5. Extend — khi skill vẫn đúng nhưng thiếu vùng

```bash
disco --creator -p "/skill:extend-repo-skill Add streaming inference coverage to /absolute/path/to/existing-skill using /absolute/path/to/repo as evidence."
```

Phân biệt cho rõ: **refresh** = nội dung đã lệch so với upstream; **extend** = nội dung đúng nhưng chưa phủ workflow mới.

## 6. Sau khi verify: deploy ở đâu

Creator đề xuất **một** scope rồi mới import sau khi bạn duyệt:

- Gắn với task/project/dataset/evaluator/máy cụ thể, hoặc tái dùng chưa chắc → `<project-dir>/.agents/skills/` (chỉ nạp khi project được trust).
- Tự chứa, có provenance, đã verify chéo project → mới đề xuất `~/.disco/agent/skills/`.
- Một graph **không** xẻ đôi giữa hai scope.

Repo skill đi đường import chuyên biệt `~/.disco/agent/skills/repositories/repo-skills/` kèm rebuild router anh em — **không** đẩy routing metadata qua importer graph tổng quát.

Cuối cùng Creator viết một handoff cho session Researcher mới.

## 7. Danh mục 15 meta skill (để biết cái gì tự chạy, cái gì phải gọi)

**Gọi tay (entry point):** `distill-ml-knowledge`, `create-repo-skill`, `refresh-repo-skill`, `extend-repo-skill`, `import-repo-skills-to-agent`, `create-paper-skills`, `design-meta-skill`.

**Được workflow tự nạp — đừng gọi tay theo checklist:** `prepare-repo-skill-env`, `verify-repo-skill`, `paper-skills-distiller`, `plan-paper-skill-modules`, `create-paper-module-skill`, `prepare-paper-recovery-env`, `recover-paper-result`, `analyze-paper-recovery`.

## Bước kế

`06-creator-paper-to-skills.md` — đường paper → skill, cần một file config TOML.
