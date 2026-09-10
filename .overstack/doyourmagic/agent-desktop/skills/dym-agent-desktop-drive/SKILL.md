---
name: dym-agent-desktop-drive
disable-model-invocation: true
description: "Lái app desktop macOS bằng agent-desktop: skeleton → drill → act → verify, hệ ref @snapshot:eN bền giữa các lần gọi CLI, bảng mã lỗi và cách rẽ nhánh. Gọi khi cần đọc/bấm/gõ trong app desktop và đã cài binary."
---

# dym-agent-desktop-drive

## When to use
- Cần đọc trạng thái hoặc thao tác trong một app desktop macOS (native hoặc Electron có
  bật AX), nhiều bước, và muốn ref không chết giữa chừng.
- Cần bằng chứng "đã bấm đúng phần tử nào" chứ không phải toạ độ mù.
- Web thuần trong trình duyệt → xem `/dym-agent-desktop route` trước, thường playwright
  hoặc CDP rẻ hơn nhiều.

## Steps

Đặt trước: `AD=<đường dẫn binary>`, `export AGENT_DESKTOP_HOME=<abs>`.

1. **Chốt cửa sổ trước khi snapshot.** App nhiều cửa sổ → `snapshot --app` trả
   `AMBIGUOUS_TARGET` kèm danh sách ứng viên (đây là tính năng, không phải lỗi):

```bash
$AD list-windows --app "Microsoft Teams"
$AD snapshot --window-id w-9249 --skeleton -i --compact
```

2. **Skeleton trước, drill sau** — chỉ khi app dày:

```bash
$AD snapshot --app "System Settings" --skeleton -i --compact   # đo: 4630 B, 27 ref
$AD snapshot --root "@s23de9t04j589e:e5" -i --compact           # bung đúng vùng cần
```
App thưa (Finder, Calculator, TextEdit) → bỏ skeleton, snapshot thẳng.
Đã biết tên/role → `find` rẻ nhất, khỏi snapshot:

```bash
$AD find --app "System Settings" --role button --name "Sound" --exact --limit 2
```

3. **Hành động bằng ref đầy đủ** `@<snapshot_id>:e<N>` — luôn bọc nháy vì `:` trong shell:

```bash
$AD click "@s23de9t04j589e:e12"
$AD set-value "@s23de9t04j589e:e2" "text"
$AD toggle "@s23de9t04j589e:e6"      # hoặc check/uncheck (idempotent)
$AD select "@s23de9t04j589e:e4" "Option B"
```
Mặc định **headless**: đi đường AX ngữ nghĩa, không cướp focus, không di chuột, không
tổng hợp phím. Cần gõ/kéo thật thì thêm `--headed` toàn cục:
`$AD --headed drag --from "@s..:e1" --to "@s..:e5"`.

4. **Chờ trạng thái thay vì sleep**:

```bash
$AD wait --element "@s..:e5" --predicate actionable --timeout 5000
$AD wait --text "Done" --app "App" --timeout 5000
$AD wait --menu --app "App"        # chờ menu bung
```

5. **Verify bằng cách drill lại đúng vùng** đã đổi. Ref của vùng khác vẫn sống
   (scoped invalidation) — không cần snapshot lại cả app.

6. **Gộp nhiều lệnh một lượt** khi các bước không phụ thuộc quan sát giữa chừng:

```bash
$AD batch '[{"command":"list-surfaces","args":{"app":"System Settings"}},{"command":"clipboard-get","args":{}}]' --stop-on-error
```
Đo: 2 lệnh trong 629 ms, `max_entries: 64`, `max_input_bytes: 1 MiB`.

## Rules
- **Mã thoát: `0` ok · `1` lỗi có cấu trúc · `2` lỗi tham số** (đo thật cả ba). Rẽ nhánh
  theo `error.code`, KHÔNG theo `error.message` — repo tự khai message/suggestion có thể
  đổi giữa các bản.
- Ref **bền giữa các tiến trình**: snapshot lấy ở lệnh trước vẫn resolve ở lệnh sau nhờ
  refmap ghi xuống `$AGENT_DESKTOP_HOME/snapshots/<id>/refmap.json` (đo: ref lấy cách đó
  vài phút, tiến trình khác, vẫn `get` được). Đây là điểm khác nền tảng so với
  `orca computer` element-index (chỉ sống trong một lượt trả về).
- Ref sai chỉ số → `STALE_REF` (rc=1) kèm `recovery.strategy`; snapshot_id không tồn tại
  → `SNAPSHOT_NOT_FOUND`. Không bao giờ đoán index kế tiếp.
- Mã lỗi hay gặp: `PERM_DENIED` (cấp quyền + mở lại terminal) · `AMBIGUOUS_TARGET` (chốt
  `--window-id` hoặc thêm `--exact`) · `ACTION_NOT_SUPPORTED` (đổi lệnh khác) ·
  `POLICY_DENIED` (đang headless mà cần `--headed`) · `TIMEOUT` (đọc `error.details.kind`
  trước khi nới timeout).
- Click bị `receives_events` + `occluder: {...}` = có phần tử đè lên. Đưa cửa sổ ra trước
  hoặc dẹp cái đè, **đừng retry mù**.
- **Electron không bật AX thì cả hai tool đều mù.** Đo trên Microsoft Teams: `orca computer`
  thấy 5 node, `agent-desktop` thấy `ref_count: 4` — cùng dừng ở ranh giới "Web content".
  Đường ra: `launch --cdp` (chỉ khi chấp nhận khởi động lại app) rồi dùng client CDP.
- Toàn bộ doc gốc lấy từ chính binary khi cần chi tiết: `$AD skills get desktop --full`
  (in SKILL + 5 file references). Đừng chép chúng vào repo.
