---
name: dym-scientific-agent-skills-dong-gop-them-sua-skill
description: "Đóng góp: thêm hoặc sửa một skill. repo có một số luật ngầm mà CI chặn cứng và validator báo lỗi rất khó hiểu (đặc biệt là luật strictyaml). File này là bản kê đúng thứ tự, để PR không bị đá vì lý do hình thức."
disable-model-invocation: true
---

# Skill: dym-scientific-agent-skills-dong-gop-them-sua-skill — Đóng góp: thêm hoặc sửa một skill

> Track ĐÓNG GÓP. File này dành cho người clone **chính repo skill** để sửa nó. Nếu bạn chỉ muốn *dùng* skill, quay lại [01](01-cai-dat-skills.md).

**Vì sao dùng:** repo có một số luật ngầm mà CI chặn cứng và validator báo lỗi rất khó hiểu (đặc biệt là luật `strictyaml`). File này là bản kê đúng thứ tự, để PR không bị đá vì lý do hình thức.
**Sinh ra cái gì:** một `skills/<name>/` hợp lệ, một `tests/<name>/` nếu skill có `scripts/`, một entry trong `tests/skill-requirements.toml`, và một PR vượt cổng.

---

## 0. Có nên nằm trong repo này không

`AGENTS.md` liệt kê các loại **bị từ chối như thường lệ**:

- Skill kỹ thuật phần mềm/phán đoán code chung — chúng cạnh tranh chỗ chọn ở *mọi* task.
- Hạ tầng chung có dán thêm một ví dụ khoa học (vector database, cloud SDK) — nhận một cái là phải gánh mọi đối thủ.
- Skill "orchestrator" rộng, chuyên route sang skill khác — theo thiết kế là đè lên mọi chuyên gia.
- Provider thứ hai cho một dịch vụ đã có skill.

Trong phạm vi: một skill **hẹp** cho **một** package/database/platform/workflow nghiên cứu — `scanpy`, `depmap`, `benchling-integration`, `experimental-design`.

Các skill dùng chung đang tồn tại (`docx`, `pdf`, `pptx`, `generate-image`, `markdown-mermaid-writing`) là **helper định dạng output hẹp**, và `AGENTS.md` nói thẳng chúng **không phải tiền lệ** để mở rộng phạm vi.

## 1. Layout

```text
plugin.json                 # manifest Agent Plugins (repo root)
skills/<skill-name>/
├── SKILL.md        # BẮT BUỘC — file duy nhất bắt buộc
├── references/     # tuỳ chọn: tài liệu dài, chỉ nạp khi cần
├── scripts/        # tuỳ chọn: helper chạy được
└── assets/         # tuỳ chọn: template, tài nguyên tĩnh
```

Ba luật tuyệt đối:

- **Tên thư mục = `name` trong frontmatter.** Không khớp là hỏng.
- **Test KHÔNG BAO GIỜ nằm dưới `skills/`.** Thư mục skill chỉ chứa thứ agent nạp. Test đi vào `tests/<skill-name>/`, fixture vào `tests/<skill-name>/fixtures/`.
- **Diagram cũng không nằm dưới `skills/`.** Nếu có, nó ở `docs/images/<skill-name>.png`.

Test trỏ về skill bằng neo tường minh, không đi đường tương đối:

```python
SKILL_ROOT = Path(__file__).resolve().parents[2] / "skills" / "<skill-name>"
```

## 2. Frontmatter — chỉ 6 field, không hơn

Spec định nghĩa một tập **đóng**. Bất kỳ khoá top-level nào khác là lỗi validation.

| Field | Bắt buộc | Ràng buộc |
|---|---|---|
| `name` | ✅ | 1–64 ký tự, chỉ chữ thường/số/gạch nối, không gạch đầu/cuối/liên tiếp, **phải bằng tên thư mục** |
| `description` | ✅ | 1–1024 ký tự. Nói skill làm gì **và** khi nào dùng, kèm từ khoá kích hoạt. Viết ngôi thứ ba |
| `license` | — | tên license hoặc trỏ tới file license đi kèm |
| `compatibility` | — | tối đa 500 ký tự, **chỉ** yêu cầu môi trường; không có thì bỏ hẳn field |
| `allowed-tools` | — | **chuỗi ngăn cách bằng dấu cách**, ví dụ `Read Write Edit Bash`. Không phải YAML list, không phải dấu phẩy |
| `metadata` | — | map khoá chuỗi → giá trị **chuỗi**. Bắt buộc có `metadata.version` |

Mọi thứ khác — tác giả, version upstream, ngày review, config theo client — đi vào **trong** `metadata`.

### Ba cái bẫy YAML khiến skill "biến mất"

**(a) Flow style JSON làm hỏng TOÀN BỘ frontmatter.** Validator dùng `strictyaml`, thứ **từ chối** flow mapping/sequence kiểu JSON. Không phải trượt một check — cả frontmatter không parse được, `name` và `description` thành không đọc được, skill không đăng ký được.

```yaml
# SAI — làm gãy validator
metadata: {"version": "1.1", "skill-author": "K-Dense Inc."}

# ĐÚNG
metadata:
  version: "1.1"
  skill-author: K-Dense Inc.
```

**(b) Scalar trong `metadata` phải được quote** nếu nó trông giống số/bool/ngày: `version: "1.0"`, `last-reviewed: "2026-07-23"` — spec đòi chúng là chuỗi.

**(c) `metadata.openclaw` và `metadata.hermes` là ngoại lệ: giữ dạng nested mapping**, không phải chuỗi JSON. `resolveOpenClawManifestBlock()` của OpenClaw đòi `typeof candidate === "object"`; một chuỗi JSON sẽ **âm thầm tắt** dependency gating và credential injection. Nested mapping vẫn qua `skills-ref validate`.

```yaml
metadata:
  version: "1.1"
  skill-author: Exa
  openclaw:
    primaryEnv: EXA_API_KEY
    envVars:
      - name: EXA_API_KEY
        required: true
        description: Exa search API key.
  hermes:
    category: research
```

**Và:** `required_environment_variables` top-level của Hermes **không dùng được ở repo này** — nó trượt validator và, vì `strictyaml` từ chối cả document, kéo theo `name`/`description` chết chung. Khai credential qua `compatibility` và `metadata.openclaw.envVars`.

Gate `requires` / `requires_toolsets` thất bại sẽ **ẩn** skill khỏi agent, nên chỉ gate vào thứ skill thực sự không chạy được nếu thiếu.

## 3. Template SKILL.md

```markdown
---
name: skill-name
description: What the skill does and when an agent should use it, including the terms that should trigger it.
license: MIT
compatibility: Requires Python 3.12+ with <package> installed. Needs network access.
metadata:
  version: "1.0"
  skill-author: Your Name
---

# Skill Title

## When to use

Use this skill when...

## Workflow

1. ...

## Examples

...
```

Luật phần thân:

- **Dưới 500 dòng.** CI cảnh báo khi vượt. Tài liệu dài chuyển vào `references/` để agent chỉ nạp khi cần.
- Đưa workflow, lệnh, ví dụ chạy được — không phải giải thích nền.
- Nêu package, dependency hệ thống, credential, nhu cầu mạng.
- Nêu caveat khoa học và các bước kiểm chứng có ý nghĩa.
- Logic mong manh hoặc lặp lại thì đẩy vào `scripts/`, đừng bắt agent dựng lại mỗi lần.
- Không bao giờ có secret, API key, URL riêng tư, dữ liệu chưa công bố.
- Tham chiếu file khác bằng đường dẫn tương đối từ gốc skill, **sâu tối đa một cấp**.

## 4. Versioning

- Skill mới: bắt đầu ở `metadata.version: "1.0"`.
- Sửa skill có sẵn: **bump trong cùng PR** — minor cho cải tiến thường (`"1.2"` → `"1.3"`), major chỉ khi breaking change hoặc thiết kế lại đáng kể (`"1.9"` → `"2.0"`).
- Suite test chỉ kiểm `metadata.version` **có mặt và được quote**, không kiểm giá trị — nên bump version không bao giờ kéo theo sửa test.
- Nếu version của *collection* đổi, `plugin.json` `version` phải khớp `pyproject.toml` `[project].version` (hiện cả hai là `2.66.0`).

## 5. Skill có `scripts/` — ba thứ đi kèm bắt buộc

1. `tests/<name>/test_scripts.py` (fixture ở `tests/<name>/fixtures/`).
2. Một entry `[skills.<name>]` trong `tests/skill-requirements.toml`. Dùng `packages = []` nếu script chỉ dùng thư viện chuẩn — vẫn được cấp môi trường sạch, và CI chạy đúng tập đó ở mỗi PR.
3. Thêm `python = "3.11"` (hoặc bản phù hợp) vào entry nếu skill không chạy được trên interpreter mặc định; `uv` sẽ tải interpreter đó khi cần.

`tests/_meta` **đỏ** nếu thiếu (1) hoặc (2). Package hoàn toàn không cài được thì ghi vào mục `[unavailable]` kèm lý do — runner in ra để lỗ hổng lộ diện trong output test.

## 6. Sửa `skills/` xong thì sửa gì nữa

- `docs/skills.md` — catalog người đọc, nhóm theo lĩnh vực.
- `docs/examples.md` — nếu skill mới thay đổi một workflow ví dụ.
- `README.md` — chỉ khi con số ở cấp repo đổi (số skill, số database).

## 7. Checklist trước khi mở PR

Chép nguyên từ `AGENTS.md`:

- [ ] Tên thư mục và `name` trong frontmatter **khớp chính xác**.
- [ ] Không có `tests/`, không có `test_*.py` ở bất kỳ đâu dưới `skills/<name>/`.
- [ ] Chỉ 6 field top-level theo spec; mọi thứ khác nằm trong `metadata`.
- [ ] `metadata.version` tồn tại, được quote, và đã bump nếu sửa skill cũ.
- [ ] `metadata` là block mapping; block `openclaw`/`hermes` là nested mapping.
- [ ] `uv run skills-ref validate skills/<name>` pass.
- [ ] Nếu version collection đổi: `plugin.json` khớp `pyproject.toml`.
- [ ] `uv run --with pytest python -m pytest tests/_meta -q` pass — **đây là cổng CI chặn**.
- [ ] Nếu có `scripts/`: có `tests/<name>/`, có `[skills.<name>]`, và `python tests/run_all.py --isolated <name>` pass.
- [ ] Nếu có `docs/images/<name>.png`: nhãn viết đúng chính tả, mũi tên trỏ đúng chỗ. Ảnh là tuỳ chọn.
- [ ] Ví dụ và script đã test, hoặc đánh dấu rõ là minh hoạ.
- [ ] Không secret, không dữ liệu riêng; kết quả scan sạch hoặc được giải thích trong PR.

Cách chạy từng lệnh trong checklist: [08-dong-gop-validate-test-scan.md](08-dong-gop-validate-test-scan.md).

## Cạm bẫy đã kiểm chứng

- **`scripts/generate_skill_image.py` KHÔNG tồn tại trong repo.** `AGENTS.md` có hẳn mục "Skill diagrams" hướng dẫn chạy nó với `OPENROUTER_API_KEY`, nhưng `.gitignore` chứa dòng `/scripts/` (có neo `/` đầu, cố ý, để không nuốt nhầm `skills/<name>/scripts/`) nên thư mục đó chưa bao giờ được commit. `find` trên cây clone: 0 kết quả. Diagram là tuỳ chọn và **không** có CI check nào — đừng lên kế hoạch dựa vào lệnh này.
- **32 skill cùng ship một file `scripts/_common.py`.** Đặt tên module top-level trong `scripts/` là chuyện có hệ quả: xem luật một-skill-một-process ở [08](08-dong-gop-validate-test-scan.md).
- **Bốn skill document (`docx`, `pdf`, `pptx`, `xlsx`) là của Anthropic**, vendored từ `anthropics/skills` và theo dõi upstream. Sửa chúng ở đây là đi ngược dòng — `tests/_meta` còn báo đỏ nếu các bản sao byte-identical (cây OOXML; bộ sinh schematic AI dùng chung ở năm skill) trôi khỏi nhau, nên phải sửa đồng thời.
