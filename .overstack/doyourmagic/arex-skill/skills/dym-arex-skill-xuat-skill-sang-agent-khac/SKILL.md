---
name: dym-arex-skill-xuat-skill-sang-agent-khac
description: "Xuất repo skill sang Claude Code / Codex / agent khác. Bạn không muốn đổi sang DisCo, chỉ muốn mượn vài repo skill (vd vllm, sglang) cho agent đang dùng."
disable-model-invocation: true
---

# Skill: dym-arex-skill-xuat-skill-sang-agent-khac — Xuất repo skill sang Claude Code / Codex / agent khác

**Vì sao dùng:** Bạn không muốn đổi sang DisCo, chỉ muốn mượn vài repo skill (vd `vllm`, `sglang`) cho agent đang dùng.
**Sinh ra cái gì:** `<target-skills-root>/repositories/{repo-skills,repo-skills-router}/` ở agent đích, với `repository-index.jsonl` và router được **sinh lại** cho đúng tập đã chọn.

---

## 1. Đường ngắn — nhờ Creator làm

```bash
# Claude Code (skills root cấp user)
disco --creator -p "/skill:import-repo-skills-to-agent import vllm and sglang to ~/.claude"

# Codex (agent root cấp user hiện hành — KHÔNG phải ~/.codex cũ)
disco --creator -p "/skill:import-repo-skills-to-agent import vllm and sglang to ~/.agents"
```

**Khởi động lại agent đích sau khi import.**

## 2. Đường chính xác — gọi thẳng helper

Skill chỉ là lớp bọc; mọi thao tác ghi file đều do một script làm:

```text
cli/packages/coding-agent/src/disco/skills/import-repo-skills-to-agent/scripts/export_repo_skills_to_agent.mjs
```

Xuất chọn lọc sang Codex:

```bash
node <đường-dẫn-skill>/scripts/export_repo_skills_to_agent.mjs \
  --source-agent-dir ~/.disco/agent \
  --target-agent-dir ~/.agents \
  --target-agent codex \
  --include-skill vllm \
  --include-skill sglang
```

Xuất toàn bộ, agent-neutral, vào đúng một skills root:

```bash
node <đường-dẫn-skill>/scripts/export_repo_skills_to_agent.mjs \
  --source-agent-dir ~/.disco/agent \
  --target-skills-root ~/.claude/skills \
  --target-agent agent-neutral
```

**Cờ (đọc từ parser trong `export_repo_skills_to_agent.mjs`):**

| Cờ | Nghĩa |
|---|---|
| `--source-agent-dir <dir>` | Agent root nguồn. Mặc định `$DISCO_CODING_AGENT_DIR`, không có thì `~/.disco/agent` |
| `--target-skills-root <dir>` | Đích **đã là** skills root (`~/.agents/skills`, `~/.claude/skills`) |
| `--target-agent-dir <dir>` | Đích là **agent root**; helper tự nối `skills/repositories` |
| `--target <dir> --target-kind skills-root\|agent-root` | Dạng tổng quát khi tên thư mục không tự nói lên |
| `--target-agent codex\|agent-neutral` | `codex` sẽ chèn thêm `agents/openai.yaml` với `policy.allow_implicit_invocation: false` |
| `--include-skill <id>` | Lặp lại được, hoặc truyền danh sách phân tách bằng dấu phẩy. **Bỏ hẳn cờ này = xuất toàn bộ** |
| `--overwrite-skill <id>` | Duyệt việc đè **đúng** skill đó. Không có cờ → helper **từ chối** conflict |
| `--router-visibility enabled\|disabled` | Chỉ dùng khi user nói rõ muốn đổi; mặc định giữ nguyên visibility của router đích |
| `--resume <transaction-dir>` | Chạy lại đúng transaction đã lưu sau khi đứt |
| `-h`, `--help` | In help rồi `exit 0` |

**Exit code:** `0` = commit thành công; `2` = mọi lỗi (kèm rollback nếu đã vào pha mutation). Không có mã nào khác. Đối số lạ → `ExportError: unknown argument: <x>` → exit 2.

## 3. Helper thực sự làm gì (9 bước, có transaction)

1. Validate nguồn/đích, an toàn symlink, định danh skill, `repo-routing-metadata.json` v2, assignment taxonomy, và **nguồn/đích không chồng nhau**.
2. Sinh một router lọc theo tập đã chọn — **không đụng collection nguồn**.
3. Trộn record đã chọn với record không liên quan ở đích, theo `skill_id` + `owner/repository`.
4. Stage cây `repo-skills/` cuối cùng.
5. Với đích Codex: thêm/ cập nhật `agents/openai.yaml` cạnh mọi `SKILL.md` gốc và con — **trừ** `repo-skills-router`.
6. Sinh lại `repository-index.jsonl` và router từ record đã trộn (không copy index cũ, không nối Markdown).
7. Revalidate taxonomy, link, index, visibility router, ranh giới chọn/không-chọn, policy Codex.
8. Chỉ thay `repositories/repo-skills/` và `repositories/repo-skills-router/` ở đích, qua transaction đã persist.
9. Validate bản đã cài rồi commit — hoặc **khôi phục nguyên trạng đích cũ** nếu bước sau mutation hỏng.

Ràng buộc kiểm được: `repository-index.jsonl` gốc phải **byte-for-byte** khớp `repo-skills-router/references/index/repositories.jsonl`. Xuất tập con **không được** rò skill không chọn vào bất kỳ index hay trang area/family nào. Skill repository không liên quan sẵn có ở đích phải còn nguyên.

## 4. Khi bị đứt giữa chừng

Helper in ra thư mục transaction. Chạy lại **đúng** transaction đó:

```bash
node <đường-dẫn-skill>/scripts/export_repo_skills_to_agent.mjs --resume /path/to/transaction-dir
```

- **Đừng vá tay** cây đích dở dang.
- Không cần gõ lại đối số; nhưng đối số nào gõ lại thì **phải khớp manifest**, lệch là resume dừng trước khi mutation.
- Nếu rollback không khôi phục được đúng snapshot: giữ nguyên đường dẫn staging/backup nó báo và dừng lại soi tay.

## 5. Ở agent đích, dùng thế nào

`repo-skills-router` giữ nguyên trạng thái model-visible; các repo skill vẫn ẩn khỏi việc chọn ngầm (qua frontmatter portable, và với Codex thì thêm policy OpenAI chỉ áp ở đích). Nghĩa là ở Claude Code bạn gọi router hoặc gọi thẳng skill, chứ nó không tự nhảy vào mọi hội thoại.

⚠️ Nếu `~/.claude/skills` hay `~/.agents/skills` của bạn đã đông skill sẵn: helper chỉ đụng **thư mục con `repositories/`**, phần còn lại không suy suyển.

⚠️ **License:** mỗi repo skill mang license riêng trong `SKILL.md`. Copy sang agent khác là hành vi redistribute — kiểm trường đó trước.

## Bước kế

`05-creator-tao-repo-skill.md` nếu muốn tự tạo skill thay vì chỉ mượn.
