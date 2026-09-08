---
name: dym-arex-skill-lenh-chat-trong-tui
description: "Lệnh chat trong TUI (KHÔNG phải lệnh shell). Nửa số thao tác hay dùng của DisCo (đăng nhập provider, đổi mode, export, resume, compact) là lệnh gõ trong dấu nhắc TUI. Dán chúng vào terminal là command not found."
disable-model-invocation: true
---

# Skill: dym-arex-skill-lenh-chat-trong-tui — Lệnh chat trong TUI (KHÔNG phải lệnh shell)

**Vì sao dùng:** Nửa số thao tác hay dùng của DisCo (đăng nhập provider, đổi mode, export, resume, compact) là **lệnh gõ trong dấu nhắc TUI**. Dán chúng vào terminal là `command not found`.
**Sinh ra cái gì:** Không sinh file gì — đây là bảng tra.

---

## Cách phân biệt

| Loại | Nhận dạng | Gõ ở đâu |
|---|---|---|
| Lệnh shell | `disco ...` | Terminal |
| Lệnh chat built-in | `/settings`, `/login`, `/creator`… | Dấu nhắc DisCo, sau khi chạy `disco` |
| Gọi skill | `/skill:<tên>` | Dấu nhắc DisCo **hoặc** nhét trong chuỗi prompt của `disco -p "..."` |

`/skill:<tên>` là ngoại lệ duy nhất đi được cả hai chỗ, vì `-p` truyền nguyên chuỗi vào cho agent:

```bash
disco --researcher -p "/skill:vllm <task>"          # hợp lệ
```

## Danh sách lệnh built-in (đọc thẳng từ `BUILTIN_SLASH_COMMANDS` trong `core/slash-commands.ts` — đủ 24 lệnh)

### Provider & model
| Lệnh | Tác dụng |
|---|---|
| `/login <provider>` | Cấu hình xác thực provider |
| `/logout` | Gỡ xác thực provider |
| `/model <provider/model>` | Chọn model (mở UI chọn) |
| `/scoped-models` | Bật/tắt model cho vòng lặp Ctrl+P |
| `/settings` | Mở menu settings |

### Mode & session
| Lệnh | Tác dụng |
|---|---|
| `/creator` | Chuyển sang Creator **trong một session mới** |
| `/researcher` | Chuyển sang Researcher **trong một session mới** |
| `/new` | Session mới |
| `/resume` | Tiếp một session khác |
| `/session` | Xem thông tin & thống kê session |
| `/name` | Đặt tên hiển thị cho session |
| `/fork` | Tạo nhánh mới từ một message người dùng trước đó |
| `/clone` | Nhân bản session tại vị trí hiện tại |
| `/tree` | Điều hướng cây session (chuyển nhánh) |
| `/compact` | Nén context thủ công |

### Vào / ra
| Lệnh | Tác dụng |
|---|---|
| `/export` | Xuất session (mặc định HTML; chỉ định `.html`/`.jsonl` được) |
| `/import` | Nhập & tiếp một session từ file JSONL |
| `/share` | Chia sẻ session dưới dạng GitHub gist **secret** |
| `/copy` | Copy message cuối của agent vào clipboard |

### Khác
| Lệnh | Tác dụng |
|---|---|
| `/trust` | Lưu quyết định trust project cho các session sau |
| `/reload` | Nạp lại keybindings, extension, skill, prompt, theme, context file |
| `/changelog` | Xem changelog |
| `/hotkeys` | Xem toàn bộ phím tắt |
| `/quit` | Thoát |

## ⚠️ `/creator` và `/researcher` mở SESSION MỚI

Cả hai **cảnh báo trước** rồi mới mở session mới với context sạch. Session cũ vẫn còn, lấy lại bằng `/resume`, và export **từ session mới chỉ chứa hoạt động của session mới**. Đừng trông đợi đổi mode giữa chừng mà giữ nguyên mạch hội thoại.

Nếu một yêu cầu thuộc mode kia, DisCo **dừng trước khi làm** và gợi ý chuyển — nó không bao giờ tự đổi mode ngầm.

## Gọi skill: `/skill:<tên>`

Ở Researcher:

```text
/skill:repo-skills-router <mô tả task>
/skill:vllm determine and verify the highest-throughput configuration for <model and workload>
/skill:<graph-entry> Complete <task> within <constraints>, and verify it with <evaluator>.
```

Ở Creator (7 entry point hay dùng):

```text
/skill:distill-ml-knowledge identify <source or task anchor>; scope, ground, construct, and verify the operating skill graph.
/skill:create-repo-skill Create and verify a repository skill for /absolute/path/to/repo.
/skill:refresh-repo-skill Refresh /absolute/path/to/existing-skill against the current repository at /absolute/path/to/repo.
/skill:extend-repo-skill Add <capability> coverage to /absolute/path/to/existing-skill using /absolute/path/to/repo as evidence.
/skill:import-repo-skills-to-agent import vllm and sglang to ~/.claude
/skill:create-paper-skills Use Distiller to generate and verify paper-replication skills for each run in this config. config_path: /absolute/path/to/distiller-run-config.toml
/skill:design-meta-skill <lỗ hổng năng lực lặp lại, có bằng chứng>
```

Router **bị tắt** (`disco repo-skills router disable`) vẫn gọi tay `/skill:repo-skills-router` được — tắt chỉ bỏ nó khỏi việc chọn tự động.

## Cạm bẫy

- **`/login` không có lệnh shell tương đương.** Muốn phi-tương-tác thì dùng biến môi trường (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `MISTRAL_API_KEY`).
- **`/share` đẩy session lên GitHub gist.** Secret gist vẫn là "ai có link là xem được". Kiểm nội dung trước.
- **Sau khi cài/cập nhật skill phải `/new` hoặc mở `disco` mới** — session đang chạy không thấy skill mới.
- Extension có thể đăng ký thêm lệnh chat và cả cờ CLI (vd `--plan` từ plan-mode extension); `disco --help` sẽ liệt kê các cờ đó ở mục **Extension CLI Flags**.

## Bước kế

`09-contributor-phat-trien-cli.md` nếu bạn định sửa chính DisCo.
