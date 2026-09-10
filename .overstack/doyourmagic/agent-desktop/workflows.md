# agent-desktop — bundle doyourmagic

Nguồn: `git@github.com:lahfir/agent-desktop.git` · bản đo `0.8.5` (npm, 2026-09-06) ·
chạy thật 2026-09-09 trên macOS 24.6 arm64, quyền Accessibility + Screen Recording đã cấp.
Chế độ đặt tên: **mặc định** (`dym-agent-desktop` + `dym-agent-desktop-<slug>`).

agent-desktop là CLI Rust (workspace 5 crate, ~107k dòng) cho AI agent nhìn và điều khiển
app desktop qua accessibility tree của OS. Nó **không phải** agent — vòng lặp quan sát-hành
động nằm ở phía người gọi. Mọi lệnh trả một envelope JSON trên stdout.

## Bảng skill

| skill | mục đích | nhánh | lệnh gọi |
|---|---|---|---|
| `dym-agent-desktop` | hub định tuyến | — | `/dym-agent-desktop` |
| `dym-agent-desktop-install` | cài pin scope, quyền TCC, xác minh | tiêu thụ | `/dym-agent-desktop install` |
| `dym-agent-desktop-drive` | skeleton → drill → act → verify, hệ ref, mã lỗi | tiêu thụ | `/dym-agent-desktop drive` |
| `dym-agent-desktop-session` | session/trace/multi-agent cursor, biên lai | tiêu thụ | `/dym-agent-desktop session` |
| `dym-agent-desktop-route` | chọn tool: agent-desktop vs orca computer vs web tools | quyết định | `/dym-agent-desktop route` |

Không có nhánh **đóng góp**: repo là Rust workspace với CI riêng, hook riêng, release-please;
sửa chính tool nằm ngoài phạm vi dùng của ta. Nếu cần, đọc `CONTRIBUTING.md` trong clone.

## Thứ tự chạy đề xuất

`route` (chọn có nên dùng không) → `install` (một lần mỗi máy) → `drive` (vòng việc) →
`session` (chỉ khi cần biên lai hoặc nhiều agent song song).

## Bẫy đắt nhất

1. **macOS-only.** `npm/scripts/postinstall.js` khai `SUPPORTED_PLATFORMS = ['darwin']`.
   Crate `windows` và `linux` mỗi cái 6 file / 76 dòng — stub trả `PLATFORM_NOT_SUPPORTED`.
   Bảng `TARGET_MAP` có linux/win32 nhưng không bao giờ tới được nhánh đó.
2. **Electron không bật AX thì mù.** Teams: `orca computer` thấy 5 node, agent-desktop
   `ref_count: 4`, cả hai dừng ở node "Web content". Không tool AX nào cứu được.
3. **Ref phải bọc nháy trong shell** — `@$SID:e1` không nở đúng, phải `"@${SID}:e1"`.
   Sai thì báo `INVALID_ARGS` với ref cụt (`'@1'`), dễ tưởng là lỗi tool.
4. **Trace hậu-hành-động là best-effort** (trừ `--trace-strict`). Thiếu dòng trace KHÔNG
   chứng minh không có hành động.
5. **`session start` không lan sang tiến trình sau** — phải tự truyền env hoặc `--session`.
6. **`AGENT_DESKTOP_HOME` phải tuyệt đối**, tương đối/rỗng → `INVALID_ARGS` trước mọi lệnh.

## Kiểm chứng thế nào

| khẳng định | bằng chứng | kết quả |
|---|---|---|
| Cài được, không bẩn `$HOME` | `HOME=$S/home npm i -g --prefix $S/prefix agent-desktop` | rc=0, ~4s; `$S/home` chỉ mọc `.npm/` |
| Binary chạy | `agent-desktop version` | rc=0 · `{"os":"macos","target":"aarch64","version":"0.8.5"}` |
| Quyền đọc được | `agent-desktop permissions` | rc=0 · accessibility+screen_recording `granted`, automation `unknown` |
| `AGENT_DESKTOP_HOME` có hiệu lực | `AGENT_DESKTOP_HOME=$S/adhome … status` | `data.state_root` = đúng đường dẫn; state mọc dưới đó |
| Mã thoát 0 / 1 / 2 | `version` · `get @sdeadbeef:e1` · `get` (thiếu arg) | rc=0 · rc=1 (`SNAPSHOT_NOT_FOUND`) · rc=2 (`INVALID_ARGS`) |
| `STALE_REF` khi ref sai | `get "@s23de9t04j589e:e9999" --property text` | rc=1 · `STALE_REF` + `recovery.requires_fresh_snapshot: true` |
| Ref sống qua tiến trình khác | snapshot lúc T, `get "@s23de9t04j589e:e1"` ở lệnh CLI sau, vài phút sau | rc=0 · `{"property":"text","value":""}` |
| refmap ghi xuống đĩa | `find $AGENT_DESKTOP_HOME` | `snapshots/<id>/refmap.json` cho từng snapshot |
| Cửa sổ nhập nhằng → lỗi tường minh | `snapshot --app "Microsoft Teams" --skeleton` | rc=1 · `AMBIGUOUS_TARGET` + 2 ứng viên (w-12891, w-9249) |
| `orca computer` tự chọn cửa sổ trong cùng ca | `orca computer get-app-state --app "Microsoft Teams"` | rc=0, im lặng lấy w-9249 |
| Skeleton rẻ hơn full | System Settings: `--skeleton -i --compact` vs `-i --compact` | 4630 B / 27 ref vs 24185 B / 168 ref |
| `orca` treeText gọn hơn JSON | System Settings, cùng lúc | orca 3313 ký tự / 117 dòng vs ad full 24185 B |
| Electron mù ở cả hai | Teams w-9249 | orca 5 node · ad `ref_count: 4`, cùng dừng ở "Web content" |
| `find` chạy | `find --app "System Settings" --role button --limit 3` | rc=0 · 3 match, `total_matches: 15`, `truncated: true` |
| `batch` chạy | 2 lệnh, `--stop-on-error` | rc=0 · `completed_entries: 2`, 629 ms, `max_entries: 64` |
| Session + trace | `session start --name dymprobe` → snapshot → `trace show` | rc=0 · JSONL có `command.start` / `snapshot.saved` (ref_count 58) / `command.end` (duration_ms) |
| `session end` | `session end <id>` | rc=0 · `ended_at` |
| Doc đi kèm binary | `agent-desktop skills` | rc=0 · liệt kê skill `agent-desktop` + 5 file references |
| Độ trưởng thành | `npm view agent-desktop time` | 36 version, 2026-02-23 → 2026-09-06 |
| Kích thước | `ls -lh bin/` | binary 3.0M + helper 498.5K |
| Quy mô mã | `find crates -name '*.rs'` | core 497 file / 57.6k dòng · macos 221 / 34.5k · ffi 182 / 14.9k · windows 6 / 76 · linux 6 / 76 |

**Chưa kiểm chứng** (cần UI thật và nhiều tiến trình đồng thời): multi-agent cursor overlay,
lease con trỏ, `launch --cdp`, notifications (`--headed`), actionability `occluder`,
drag/hover vật lý.

## Install (dùng tại chỗ)

```bash
mkdir -p .claude/skills && ln -sfn ../../.overstack/doyourmagic/agent-desktop/skills/dym-agent-desktop .claude/skills/dym-agent-desktop
```
