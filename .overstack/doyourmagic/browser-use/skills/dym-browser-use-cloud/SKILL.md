---
name: dym-browser-use-cloud
disable-model-invocation: true
description: "Chạy trình duyệt trên cloud Browser Use + tunnel localhost ra ngoài — khi cần môi trường sạch (không extension, không session của user), chạy song song nhiều luồng, hoặc site chặn bot. TỐN CREDIT và cần BROWSER_USE_API_KEY. Dùng khi user nói 'test trên môi trường sạch', 'chạy song song nhiều flow', 'bị captcha chặn'."
---

# dym-browser-use-cloud

## When to use
- **Nhiều luồng chạy song song** — Chrome cục bộ là một trình duyệt dùng chung, các luồng
  giành tab và focus lẫn nhau. Mỗi luồng một cloud browser thì cô lập hẳn.
- **Cần môi trường sạch** — không extension, không session đăng nhập sẵn của user, không
  giẫm lên tab user đang làm.
- **Site chặn bot / captcha** — cloud browser có IP quản lý sạch và cấu hình stealth.

**KHÔNG dùng khi** chỉ verify một trang nội bộ — trả tiền vô ích. Dùng `/dym-browser-use repl`.

## Chi phí (theo tài liệu browser-use, CHƯA tự kiểm chứng — không có API key khi khảo sát)
~$0.01/task + ~$0.006/step + $0.02/giờ browser. Cloud browser **tính tiền tới khi dừng hoặc
hết hạn** — luôn `stop_remote_daemon(name)` khi xong.

## Steps
1. **Auth**: `browser-harness auth login`, hoặc
   `printf '%s' "$BROWSER_USE_API_KEY" | browser-harness auth login --api-key-stdin`.
2. **Tunnel localhost — BẮT BUỘC `--host-header=rewrite`.** Cloud browser nằm ngoài Internet,
   không với tới cổng cục bộ.
   ```bash
   ngrok http 3000 --host-header=rewrite --log=stdout > /tmp/qa-ngrok.log 2>&1 &
   sleep 3
   PUBLIC_URL=$(curl -s http://127.0.0.1:4040/api/tunnels \
     | python3 -c 'import sys,json; print(json.load(sys.stdin)["tunnels"][0]["public_url"])')
   curl -s -H "ngrok-skip-browser-warning: true" "$PUBLIC_URL" | head -c 200   # kiểm tới APP chưa
   ```
   Không có ngrok / không auth được → `cloudflared tunnel --url http://127.0.0.1:3000`
   (không cần tài khoản, không có trang interstitial).
3. **Dựng cloud browser — TẮT proxy**:
   ```bash
   browser-harness <<'PY'
   start_remote_daemon("qa", proxyCountryCode=None)   # proxy mặc định làm hỏng TLS của ngrok
   PY
   BU_NAME=qa browser-harness <<PY
   new_tab("about:blank")
   cdp("Network.setExtraHTTPHeaders", headers={"ngrok-skip-browser-warning": "true"})
   goto_url("$PUBLIC_URL")
   wait_for_load()
   print(page_info())     # PHẢI ra title thật của app — không phải chrome-error/403/interstitial
   PY
   ```
4. **Dọn — trên MỌI nhánh**: `pkill -f "ngrok http 3000"` và `stop_remote_daemon("qa")`
   (đúng tên hàm — KHÔNG phải `stop_daemon`).

## Rules
- **`403 host not allowed` → thiếu `--host-header=rewrite`.** Vite/Next/webpack dev server
  chặn Host lạ (`server.allowedHosts`). Đây là kiểu trượt đầu tiên hay gặp nhất.
- **`chrome-error://` / lỗi SSL nhưng `curl` chạy được → tắt proxy** bằng `proxyCountryCode=None`.
  Chẩn đoán: cho cloud browser vào một site public bất kỳ trước — nếu site đó lên mà tunnel
  không lên thì thủ phạm là proxy.
- **Header bỏ qua interstitial áp theo TỪNG TAB.** `Network.setExtraHTTPHeaders` chỉ áp cho
  target hiện tại; tab mới do app mở (`target=_blank`, popup OAuth, `window.open`) sẽ rơi vào
  trang cảnh báo `ERR_NGROK_6024`. Áp lại header cho từng target mới — hoặc né cả lớp vấn đề
  bằng cloudflared.
- **Asset/API ghim vào cổng cục bộ sẽ gãy qua tunnel** — đó là hiện vật của tunnel, KHÔNG phải
  bug của app. Đừng trừ điểm. Tìm chế độ mock/demo để vẫn chạy được UI, và ghi rõ đường nào
  chỉ chạy mock.
- **Config của instance dev không phải lỗi app** — `.env` trỏ backend staging làm credential prod
  401. Xác định instance trỏ backend nào TRƯỚC khi chấm đó là bug auth.
- **Độ trễ tăng** do tunnel + cloud — đừng chấm nặng thời gian tải trừ khi chậm thảm hoạ.
- **Chỉ dừng daemon/browser MÌNH tạo.** Daemon số cũ (`bu-qa1…`) có thể của phiên khác — chọn
  `BU_NAME` sạch và duy nhất.
- Đổi option daemon (vd bật/tắt proxy) → `restart_daemon("qa")` trước;
  `start_remote_daemon` báo lỗi nếu daemon cùng tên đang chạy.
- Touch only what the task requires — no opportunistic changes.
