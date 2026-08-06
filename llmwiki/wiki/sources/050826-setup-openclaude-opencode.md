---
type: source
title: "Setup OpenClaude + OpenCode — runbook cho agent khác dựng lại đúng cấu hình đang chạy"
status: shipped
tags: [runbook, opencode, openclaude, provider, azure, harness-global]
timestamp: 2026-08-05
---

# Setup OpenClaude + OpenCode

Runbook để một agent hoặc một người **không có context nào của phiên này** dựng lại đúng cấu hình đang chạy trên máy, ngày 2026-08-05. Mọi con số dưới đây đọc trực tiếp từ đĩa lúc viết, không lấy từ trí nhớ.

## Token nằm ở đâu — đọc mục này trước

Toàn bộ token **không nằm trong repo**. Chúng nằm ở một file duy nhất ngoài repo, quyền `600`:

```
~/.config/overstack/ai-secrets.env
```

File đó khai bốn biến: `AZURE_FOUNDRY_KEY`, `ASKCTD_FOUNDRY_KEY`, `CTD_OPUS_KEY`, `NINEROUTER_KEY`.

Nạp trước khi làm bất cứ việc gì:

```bash
source ~/.config/overstack/ai-secrets.env
```

Nếu bạn đang dựng trên **máy khác** và không có file đó, xin bốn giá trị từ chủ máy rồi tạo lại đúng đường dẫn trên với `chmod 600`. Runbook này cố ý không chứa giá trị token — repo được push lên GitHub, nên một token nằm trong file tracked là một token đã rò.

Để token tự nạp mỗi phiên shell, thêm dòng `source` trên vào `~/.zshrc`. Trên máy hiện tại thì ba biến `AZURE_FOUNDRY_KEY`, `ASKCTD_FOUNDRY_KEY`, `CTD_OPUS_KEY` đang được `export` trực tiếp trong `~/.zshrc` (ba dòng đầu file), còn `NINEROUTER_KEY` thì chưa — xem mục nợ kỹ thuật ở cuối.

## Phần 1 — OpenCode

Phiên bản đang chạy: `1.15.10`, cài qua Homebrew tại `/opt/homebrew/bin/opencode`.

### Config

Một file duy nhất: `~/.config/opencode/opencode.json`.

Có một điểm dễ nhầm cần biết trước: Orca đặt biến `OPENCODE_CONFIG_DIR` trỏ tới `~/Library/Application Support/orca/opencode-hooks/shared`, và thư mục đó **không chứa** `opencode.json` — nó chỉ chứa plugin `orca-opencode-status.js`. Đã kiểm bằng cách chạy `opencode models` với đúng environment của Orca: cả năm provider tự khai vẫn hiện đủ. Kết luận: biến đó chỉ thêm plugin, config chính vẫn được đọc từ `~/.config/opencode/`.

### Năm provider đang khai

| Provider | baseURL | Model | Key |
|---|---|---|---|
| `ctd` | `https://ctd-opus-resource.openai.azure.com/openai/v1` | `gpt-5.6-terra` | `{env:CTD_OPUS_KEY}` |
| `askctd` | `https://askctd-resource.openai.azure.com/openai/v1` | `gpt-5.6-sol` | `{env:ASKCTD_FOUNDRY_KEY}` |
| `foundry` | `https://tinhdh-api-python-resource.services.ai.azure.com/openai/v1` | `DeepSeek-V4-Pro` | `{env:AZURE_FOUNDRY_KEY}` |
| `azure` | `https://tinhdh-api-python-resource.cognitiveservices.azure.com/openai/deployments` | `gpt-5.4` | `{env:AZURE_FOUNDRY_KEY}` |
| `9router` | `https://apipool.n8ntinhdao.com/v1` | `c-fable-5`, `c-sonnet-5`, `c-opus-4-8`, `c-opus-4-7`, `c-haiku-4-5` | ⚠️ đang hardcode trong file |

**Model mặc định: `ctd/gpt-5.6-terra`.** Đây là thứ chạy khi gọi `opencode` mà không truyền cờ `-m`.

Ngoài năm provider trên, `opencode models` còn liệt kê `openai` (48 model), `gitlab` (23) và `opencode` (7 model free) — đó là catalog dựng sẵn của chính opencode, không phải do config này khai. Provider `azure` hiện 66 model vì catalog dựng sẵn được trộn với phần tự khai.

### Dựng lại từ đầu

```bash
brew install opencode                      # hoặc theo hướng dẫn của opencode.ai
mkdir -p ~/.config/opencode
```

Tạo `~/.config/opencode/opencode.json` theo khuôn dưới. Chỉ dùng cú pháp `{env:TÊN_BIẾN}` cho `apiKey`, không viết token thẳng vào file.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ctd": {
      "npm": "@ai-sdk/openai",
      "name": "Azure OpenAI — ctd-opus",
      "options": {
        "baseURL": "https://ctd-opus-resource.openai.azure.com/openai/v1",
        "apiKey": "{env:CTD_OPUS_KEY}"
      },
      "models": { "gpt-5.6-terra": { "name": "gpt-5.6-terra" } }
    },
    "askctd": {
      "npm": "@ai-sdk/openai",
      "name": "Azure OpenAI — askctd",
      "options": {
        "baseURL": "https://askctd-resource.openai.azure.com/openai/v1",
        "apiKey": "{env:ASKCTD_FOUNDRY_KEY}"
      },
      "models": { "gpt-5.6-sol": { "name": "gpt-5.6-sol" } }
    },
    "foundry": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Azure AI Foundry (OpenAI-compatible v1)",
      "options": {
        "baseURL": "https://tinhdh-api-python-resource.services.ai.azure.com/openai/v1",
        "apiKey": "{env:AZURE_FOUNDRY_KEY}"
      },
      "models": { "DeepSeek-V4-Pro": { "name": "DeepSeek V4 Pro (Foundry deployment)" } }
    },
    "azure": {
      "npm": "@ai-sdk/azure",
      "name": "Azure OpenAI (cognitiveservices)",
      "options": {
        "resourceName": "tinhdh-api-python-resource",
        "baseURL": "https://tinhdh-api-python-resource.cognitiveservices.azure.com/openai/deployments",
        "apiKey": "{env:AZURE_FOUNDRY_KEY}",
        "apiVersion": "2024-12-01-preview"
      },
      "models": { "gpt-5.4": { "name": "Azure deployment: gpt-5.4" } }
    },
    "9router": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Claude {9Router}",
      "options": {
        "baseURL": "https://apipool.n8ntinhdao.com/v1",
        "apiKey": "{env:NINEROUTER_KEY}"
      },
      "models": {
        "c-fable-5":  { "name": "cc/claude-fable-5" },
        "c-sonnet-5": { "name": "cc/claude-sonnet-5" },
        "c-opus-4-8": { "name": "cc/claude-opus-4-8" },
        "c-opus-4-7": { "name": "cc/claude-opus-4-7" },
        "c-haiku-4-5":{ "name": "cc/claude-haiku-4-5-20251001" }
      }
    }
  },
  "model": "ctd/gpt-5.6-terra"
}
```

### Nghiệm thu — chạy thật, đừng tin config suông

```bash
source ~/.config/overstack/ai-secrets.env
opencode models | grep '^ctd/'          # kỳ vọng: ctd/gpt-5.6-terra
opencode run "Trả lời đúng hai chữ: OK TERRA"
```

Dòng đầu output của lệnh cuối phải là `> build · gpt-5.6-terra` — đó là bằng chứng model mặc định đã đúng, chứ không phải chỉ có mặt trong danh sách.

## Phần 2 — OpenClaude

Phiên bản đang chạy: `0.27.0`, binary tại `~/.local/bin/openclaude`.

### Xác thực

`openclaude auth status` trên máy này trả về:

```json
{ "loggedIn": true, "authMethod": "third_party", "apiProvider": "openai" }
```

Credential **không nằm trong file nào** dưới `~/.openclaude/` — nó nằm trong macOS Keychain, mục `Claude Code-credentials`. Vì vậy phần xác thực **không sao chép được bằng cách copy file**: trên máy mới phải tự chạy `openclaude auth login` (hoặc cấu hình provider third-party tương ứng) rồi mới dùng được. Đây là giới hạn thật, không phải thiếu sót của runbook — nếu bạn thấy hướng dẫn nào bảo copy file credential thì hướng dẫn đó sai.

### Config

Một file: `~/.openclaude/settings.json`. Bốn khoá ngoài `hooks`:

```json
{
  "model": "gpt-5.6-sol",
  "env": { "CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS": "30000" },
  "skipDangerousModePermissionPrompt": true,
  "skipFullAccessModePermissionPrompt": true
}
```

**Cảnh báo về khoá `model`: nó KHÔNG có tác dụng ở cấu hình này.** Đo ngày 2026-08-06, ba lần chạy liên tiếp:

| Cách đặt model | Model thật sự chạy |
|---|---|
| khoá `model` trong `settings.json` | ✗ bị bỏ qua |
| biến môi trường `ANTHROPIC_MODEL` | ✗ bị bỏ qua |
| cờ `--model gpt-5.6-terra` | ✓ ăn |

Bằng chứng: một phiên tạo mới hoàn toàn, sau khi `settings.json` đã ghi `gpt-5.6-terra` được hơn bảy tiếng, vẫn chạy `gpt-5.6-sol` suốt 144 lượt, không một lượt nào dùng terra. Orca không phải thủ phạm — `ps` cho thấy nó gọi `openclaude --dangerously-skip-permissions`, không truyền `--model`; cũng không có settings cấp project nào đè.

Vì vậy khoá `model` trong file này chỉ nên coi là **ghi chú cho người đọc biết máy đang thực tế dùng model nào**, không phải nút bấm. Muốn đổi model thật thì truyền `--model` lúc gọi, hoặc dựng một shim `openclaude` trên `PATH` tự thêm cờ đó.

`CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` phải ở mức tối thiểu `30000`. Lý do: `SessionEnd` có deadline riêng ở tiến trình cha, nên đặt `timeout` cho từng hook là chưa đủ — thiếu biến này thì hook `SessionEnd` của harness bị cắt giữa chừng.

### Hook — 12 event, hai nguồn

`~/.openclaude/settings.json` hiện có **12 event**, tổng 18 hook, đến từ hai nguồn khác nhau và **phải cùng tồn tại**:

- **10 hook của Orca** — cùng trỏ về một script `~/.orca/agent-hooks/openclaude-hook.sh`, gắn ở `UserPromptSubmit`, `Stop`, `StopFailure`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `SubagentStart`, `SubagentStop`, `TeammateIdle`. Đây là telemetry: script POST về `127.0.0.1` với `--max-time 1.5` và luôn `exit 0`, nên nó không chặn và không sửa được hành vi agent.
- **8 hook của harness** — `pre_tool_use.py`, `orca_guard.py`, `post_tool_use.py`, `stop.py`, `session_end.py`, `session_start.py`, `code_graph_keeper.py`, `user_prompt_submit.py`, mỗi cái `timeout: 30`.

Tám hook harness **không cấu hình tay**. Chạy installer, nó tự merge và giữ nguyên toàn bộ hook Orca:

```bash
cd <repo overstack>
bash harness/scripts/install-harness.sh --global
```

Installer tự phát hiện binary `openclaude` trên `PATH`. Máy không có OpenClaude thì nó in một dòng bỏ qua và vẫn cài phần Claude bình thường. Nó cũng tự tạo backup `~/.openclaude/settings.json.bak.<nano>` mỗi lần chạy, và chạy lại nhiều lần không nhân đôi hook.

### Nghiệm thu

```bash
openclaude auth status                     # loggedIn: true
python3 -c "import json;d=json.load(open('$HOME/.openclaude/settings.json'));\
print('model:',d['model'],'| events:',len(d['hooks']))"
```

Kỳ vọng: `model: gpt-5.6-sol | events: 12`. Nếu số event nhỏ hơn 12 thì hoặc installer chưa chạy, hoặc Orca chưa từng khởi động trên máy đó.

## Thứ tự làm trên máy mới

1. Tạo `~/.config/overstack/ai-secrets.env` với bốn token, `chmod 600`, rồi `source` nó.
2. Cài `opencode`, viết `~/.config/opencode/opencode.json` theo khuôn trên, nghiệm thu bằng `opencode run`.
3. Cài `openclaude`, chạy `openclaude auth login`, đặt `model` và `env` trong `~/.openclaude/settings.json`.
4. Chạy `install-harness.sh --global` để merge 8 hook harness vào cả hai scope.
5. Mở **pane/terminal mới** — pane đang mở kế thừa environment cũ nên sẽ không thấy token vừa thêm.

## Nợ kỹ thuật đã biết

- **`9router` đang hardcode API key** trong `~/.config/opencode/opencode.json`, khác với bốn provider kia dùng `{env:...}`. Khuôn ở runbook này đã đổi sang `{env:NINEROUTER_KEY}` và biến đó đã có trong file secrets, nhưng **file config trên máy hiện tại thì chưa đổi**. Đổi xong nên xoay key vì nó đã nằm trên đĩa dạng rõ.
- **Provider `orcaflow` đã bị gỡ** ngày 2026-08-05. Nó trỏ `http://localhost:20128/v1` với ba model `osonnet`/`oopus`/`ohaiku`, nhưng không có tiến trình nào nghe cổng đó, không có binary, và không phải tính năng của app Orca — đã kiểm bằng `lsof -nP -iTCP:20128 -sTCP:LISTEN` (rỗng) và grep toàn bộ `/Applications/Orca.app/Contents/Resources` (0 hit). Nếu sau này dựng lại proxy đó thì thêm luôn một probe, đừng chỉ khai vào config.
- **`askctd/gpt-5.6-sol` từng làm agent tự dừng giữa việc.** Đo trên transcript phiên `d06197e5`: 11 lượt trả đúng câu `"I'm sorry, but I cannot assist with that request."` với `usage` bằng 0 ở mọi trường, trong khi 297 lượt bình thường có trung vị 50.477 token. Không tốn token nghĩa là câu đó không do model sinh ra sau khi suy luận — nó được chèn từ phía provider. Cân nhắc trước khi chọn model này để dispatch.

## Origin

- **Phiên:** `b8afb386`, 2026-08-05
- **Đọc trực tiếp từ:** `~/.config/opencode/opencode.json`, `~/.openclaude/settings.json`, `~/.zshrc`, `openclaude auth status`, `opencode models`, `lsof`
- **Secrets:** `~/.config/overstack/ai-secrets.env` (ngoài repo, `600`)
- **Liên quan:** `harness/scripts/install-harness.sh` (merge hook global), `llmwiki/wiki/sources/050826-session-provenance.md`
