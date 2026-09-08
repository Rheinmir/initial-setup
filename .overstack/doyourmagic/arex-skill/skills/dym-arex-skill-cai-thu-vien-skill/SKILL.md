---
name: dym-arex-skill-cai-thu-vien-skill
description: "Cài & bảo trì thư viện AREX-Skill. disco cài xong vẫn chưa có kiến thức vận hành nào. Bước này mới nạp 1.000 repo skill + router vào agent dir."
disable-model-invocation: true
---

# Skill: dym-arex-skill-cai-thu-vien-skill — Cài & bảo trì thư viện AREX-Skill

**Vì sao dùng:** `disco` cài xong vẫn chưa có kiến thức vận hành nào. Bước này mới nạp **1.000 repo skill + router** vào agent dir.
**Sinh ra cái gì:** `~/.disco/agent/skills/repositories/{repo-skills,repo-skills-router}/`, kèm bản ghi commit nguồn để về sau đối chiếu drift.

---

## 1. Cài

```bash
disco repo-skills install
```

Lệnh này clone **shallow** (`--depth 1 --filter=blob:none`) repo chính thức, chỉ copy phần runtime collection, rồi ghi lại commit nguồn. **Git phải có sẵn trên máy.**

Output mẫu (in ra bởi `printInstallResult`):

```text
Installed repository skills from commit <sha>.
Official skills: <n>
Local skills preserved: <n>
Total repo skills: <n>
Routed repositories: 1000
Area-family assignments: 2209
Router taxonomy: 20 areas, 178 families
Router: enabled
Start a new Researcher session to load the updated repository skill index.
```

Chạy lại khi đã cài rồi thì nó **không** cài lại, chỉ in:
`Repository skills are already managed. Run 'disco repo-skills update' to check for updates.`

## 2. Soi trạng thái — và đây là lệnh dùng làm cổng CI

```bash
disco repo-skills status
```

`status` **hoàn toàn local**: kiểm digest của skill được quản lý, sự hiện diện của router, độ phủ routing. Nó **không** gọi GitHub. In:

```text
Installed: yes
Managed by DisCo: yes
Source: <repo url>
Commit: <sha> (<12 ký tự đầu>)
Official skills / Local skills / Total repo skills
Routed repositories / Area-family assignments / Router taxonomy
Files: <n>
Router: enabled | disabled | not installed
Drift: none          ← hoặc "Drift/issues:" kèm danh sách
```

**Exit code (kiểm bằng mã, không phải bằng README):**

| Tình huống | Exit |
|---|---|
| Sạch, không drift | `0` |
| Có bất kỳ mục nào trong `status.issues` (drift / thiếu router / hỏng) | `1` |
| Sai cú pháp lệnh (`--force` cho `status`, subcommand lạ, `router foo`) | `2` |

Cụ thể: `repo-skills.ts` set `process.exitCode = 1` khi `status.issues.length > 0`; mọi lỗi parse ném `RepoSkillsLibraryError(..., 2)`. Đừng viết script kiểu `|| true` — 1 và 2 mang nghĩa khác nhau.

## 3. Cập nhật

```bash
disco repo-skills update            # kiểm HEAD remote và áp bản mới
disco repo-skills update --force    # thay cả skill official đã bị sửa local; giữ backup
```

Luật cập nhật:
- Chỉ thay các **skill ID official được quản lý**.
- Skill do Creator tạo hoặc bạn tự import **được giữ nguyên**.
- Nếu một skill official bị sửa local, hoặc đụng ID với skill không được quản lý → lệnh **dừng**. Chỉ `--force` mới đè, và nó in `Backup: <path>` để phục hồi.

## 4. Bật/tắt router

```bash
disco repo-skills router disable
disco repo-skills router enable
```

Mặc định `repo-skills-router` là **điểm vào duy nhất mà model nhìn thấy**; các repo skill root và sub-skill đều `disable-model-invocation: true` nên không bị nhồi vào context ban đầu. Tắt router = bỏ nó khỏi việc chọn skill tự động, **nhưng vẫn gọi tay được** bằng `/skill:repo-skills-router`.

> Mọi thay đổi install / update / router **chỉ có hiệu lực ở session Researcher mới**. Chính CLI cũng in dòng nhắc này.

## 5. Chế độ offline

```bash
disco --offline ...           # hoặc: export DISCO_OFFLINE=1
```

Khi offline, `install`/`update` **thất bại có chủ đích** với thông báo:
`Repository skill install/update is unavailable in offline mode. Re-run without --offline or DISCO_OFFLINE.`
`status` vẫn chạy được vì nó vốn không cần mạng.

## 6. Đường lùi: cài tay

```bash
git clone https://github.com/VectorSpaceLab/AREX-Skill.git
cd AREX-Skill
mkdir -p ~/.disco/agent/skills/repositories
cp -R \
  skills/repositories/repo-skills \
  skills/repositories/repo-skills-router \
  ~/.disco/agent/skills/repositories/
```

Chạy `disco repo-skills install` sau đó sẽ **nhận nuôi** bản copy tay nếu nó chưa bị sửa, và giữ các skill ID local khác.

## 7. Cấu trúc bạn vừa cài (để biết đường mà đọc)

```text
~/.disco/agent/skills/repositories/
├── repo-skills/
│   ├── repository-index.jsonl        # 1000 dòng, mỗi dòng 1 repo
│   └── <skill-id>/
│       ├── SKILL.md
│       ├── sub-skills/
│       ├── references/repo-provenance.md
│       ├── references/repo-routing-metadata.json
│       └── scripts/
└── repo-skills-router/
    ├── SKILL.md
    └── references/
        ├── areas/            # 20 area
        ├── families/<area>/  # 178 family
        └── index/            # taxonomy.json · repositories.jsonl (1000) · assignments.jsonl (2209) · build-metadata.json
```

Đường định tuyến: `request → area → family → repository skill root → sub-skill`.

⚠️ **Mỗi skill có license riêng.** Trường `license` trong `SKILL.md` của skill đó mới là quyết định, không phải Apache-2.0 của repo gốc. Kiểm trước khi copy/redistribute.

## Bước kế

`03-chay-viec-researcher.md` — thực sự dùng chỗ kiến thức vừa cài.
