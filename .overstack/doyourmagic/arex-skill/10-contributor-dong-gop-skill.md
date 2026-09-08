# 10 — Contributor: đóng góp / refresh một repo skill vào thư viện

**Vì sao dùng:** Bạn muốn thêm repo vào bộ 1.000, hoặc cập nhật một skill đã cũ so với upstream.
**Sinh ra cái gì:** Một cây skill runtime dưới `skills/repositories/repo-skills/<skill-id>/`, router đã sinh lại, catalog đã cập nhật, và một PR khai đủ nguồn gốc.

---

## 1. File bắt buộc của một skill mới

```text
skills/repositories/repo-skills/<skill-id>/
├── SKILL.md                                    ← bắt buộc
├── references/repo-provenance.md               ← bắt buộc
├── references/repo-routing-metadata.json       ← bắt buộc (v2)
├── sub-skills/                                 ← khi upstream có nhiều vùng workflow lớn
└── scripts/                                    ← script validate/preflight nhỏ, nếu giúp skill an toàn hơn
```

`repo-routing-metadata.json` v2 chỉ giữ mức tối thiểu: định danh chuẩn `owner/repository`, skill ID, taxonomy hash, routing status, và assignment chính xác. **Lý do phân loại và bằng chứng đầy đủ nằm NGOÀI** cây runtime — trong artifact routing-decision hoặc thư mục handoff `skills/disco/routing_decision/` của repo.

**Tách bạch:** test case, review note, generation report **không** nằm trong thư mục skill runtime, trừ khi chúng thực sự là guidance runtime.

## 2. Cách sinh: dùng Creator, đừng viết tay

```bash
disco --creator -p "/skill:create-repo-skill Create and verify a repository skill for /absolute/path/to/repo."
```

Rồi để `verify-repo-skill` gác. Phân loại (classification) là **bước riêng sau verify**, đối chiếu với taxonomy cố định.

Khi không có family nào khớp chính xác → ghi `unclassified` và **hỏi người dùng** có import không. Muốn đưa vào thì đề xuất mở rộng taxonomy và **chờ duyệt** trước khi đổi taxonomy canonical. Phân loại bị gián đoạn hoặc không truy cập được là `blocked`/`failed` — **không** đoán bừa một route.

## 3. Rebuild router (đừng sửa tay Markdown sinh ra)

```bash
node cli/packages/coding-agent/src/disco/skills/verify-repo-skill/scripts/update_repo_skills_router.mjs \
  --library-root skills/repositories
```

**Cờ (đọc từ `parseArgs` trong chính script):**

| Cờ | Nghĩa |
|---|---|
| `--library-root <dir>` | Thư mục chứa cặp `repo-skills/` + `repo-skills-router/`. **Dùng cái này khi build trong checkout** |
| `--agent-dir <dir>` | Agent root; tự nối `skills/repositories`. **Không dùng chung với `--library-root`** |
| `--template-dir <dir>` | Thư mục template |
| `--include-skill <ids>` | Lọc tập skill (lặp lại hoặc phân tách bằng dấu phẩy) |
| `--output-router-dir <dir>` | Ghi router ra chỗ khác |
| `--routing-entry <path>` | Thêm entry routing |
| `--router-visibility <v>` | Visibility của router |
| `--timeout <n>` | Timeout lock |
| `-h`, `--help` | In help rồi `exit 0` |

Output khi thành công:

```text
updated <router-dir>: <n> skills, <n> assignments, <n> areas, <n> families
```

**Exit code:**

| Tình huống | Exit |
|---|---|
| Thành công | `0` |
| `RouterError`: sai đối số, dùng cả `--agent-dir` lẫn `--library-root`, `--already-locked` mà thiếu `DISCO_IMPORT_LOCK_PATH` | `2` |
| Lỗi ngoài dự kiến khác | `1` |

Truyền `--agent-dir` thì script **tự chạy lại chính nó dưới lock** (trừ khi `DISCO_IMPORT_LOCK_PATH` đã được set) — đó là hành vi đúng, đừng tưởng nó treo.

Số phải khớp thực tế hiện tại: **1000** repository, **2209** assignment, **20** area, **178** family (đếm được: `wc -l references/index/repositories.jsonl` = 1000, `assignments.jsonl` = 2209, `repository-index.jsonl` = 1000).

## 4. Cập nhật catalog công khai

```text
docs/imported-repo-skills.md
```

Catalog phải khớp với `repo-routing-metadata.json` và `repo-provenance.md`. `docs/repository-catalog.md` (673KB) là trang data dùng chung — đổi nó thì giữ đồng bộ count, grouping, path, và phần tóm tắt bản địa hoá ở README tiếng Trung.

## 5. Kiểm nhanh tại chỗ

```bash
# cú pháp Python của mọi script trong skill
find skills/repositories/repo-skills/<skill-id> -type f -name '*.py' -print0 \
  | xargs -0 -r python -m py_compile

# liệt kê toàn bộ file để soi cây trước khi mở PR
find skills/repositories/repo-skills/<skill-id> -type f | sort

# docs không được chứa tab
python - <<'PY'
from pathlib import Path
for p in sorted(Path('docs').glob('*.md')):
    if '\t' in p.read_text():
        print(f'tab: {p}')
PY
```

## 6. Refresh một skill đã có

```bash
disco --creator -p "/skill:refresh-repo-skill Refresh the existing repo skill at /path/to/skill against /path/to/upstream-repository. Preserve correct workflows, update stale guidance, run verification, and prepare a contribution-ready result."
```

Refresh xong mới coi là **hoàn tất** khi cả 4 nhóm dưới đồng bộ:

1. **Cây runtime** — cập nhật *mọi* file public bị ảnh hưởng, không chỉ `SKILL.md` gốc.
2. **Provenance** — `references/repo-provenance.md` phản ánh trạng thái repo hiện tại.
3. **License metadata** — giải license một lần cho repo upstream canonical tại đúng commit nguồn:
   ```bash
   gh api "repos/<owner>/<repo>/license?ref=<source-commit>" --jq '.license.spdx_id // empty'
   ```
4. **Routing & catalog** — so phạm vi năng lực mới với baseline routing cũ; artifact review giữ **ngoài** cây skill runtime.

Luật cải thiện skill có sẵn:
- Bám bằng chứng: source, docs upstream, example, hoặc hành vi package đã inspect;
- **Giữ nguyên guidance còn đúng**;
- Cập nhật provenance khi commit nguồn / version package / tập bằng chứng đổi;
- Cập nhật routing metadata khi độ phủ hoặc hướng dẫn chọn đổi;
- Script phải **tất định và an toàn**: tránh download, training, khởi động server, hay thao tác xoá file, trừ khi có cổng chặn rõ ràng.

## 7. Yêu cầu bắt buộc của PR

Mọi PR thêm/sửa repo skill sinh ra phải khai:

- URL repo upstream + **commit hoặc tag nguồn**;
- **Model và provider** đã dùng để sinh skill;
- **Mức reasoning/thinking** (`low`/`medium`/`high` hoặc tương đương của provider);
- Skill do DisCo sinh, do copy workflow skill, hay sửa tay;
- Lệnh verify / bước review đã chạy;
- Khoảng trống đã biết, check bị bỏ, credential thiếu, giới hạn môi trường;
- Xác nhận đã cập nhật `skills/repositories/repo-skills-router/` khi routing đổi.

Dùng nhiều model hoặc nhiều lượt thì **liệt kê từng model kèm vai trò** (generation / review / refinement / verification).

## 8. Checklist cuối

- [ ] Link trong README/docs trỏ tới file có thật
- [ ] Docs EN và zh cùng cập nhật khi có cặp
- [ ] Thay đổi skill runtime kèm provenance + bằng chứng nguồn
- [ ] Router và catalog nhất quán với thay đổi skill
- [ ] PR khai model, provider, mức reasoning, bước verify
- [ ] Script bị đụng đã được syntax-check hoặc verify cách khác
- [ ] Phần tóm tắt cuối nói rõ **cái gì đã verify và cái gì chưa**

## 9. Cạm bẫy

- **Đừng sửa tay Markdown router sinh ra.** Sửa generator rồi chạy lại `update_repo_skills_router.mjs`.
- **Đừng đẩy repo routing metadata qua importer graph tổng quát** — repo graph có đường import chuyên biệt riêng.
- **Đừng đoán route.** `unclassified` / `blocked` / `failed` là kết quả hợp lệ; route sai thì độc hại hơn là không route.
- **License từng skill là license nói lời cuối**, không phải Apache-2.0 của repo. Ghi đúng vào metadata `SKILL.md`.
