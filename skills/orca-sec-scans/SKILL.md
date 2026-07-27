---
name: orca-sec-scans
description: Quét bảo mật mã nguồn bằng Trivy — tự check/cài Trivy nếu chưa có, quét vuln + misconfig + secret trên be/fe, xuất report JSON+HTML, tóm tắt HIGH/CRITICAL, và đề xuất/áp dụng fix (bump deps, USER non-root). NGOÀI quét static Trivy, còn KIỂM CHỨNG ĐỘNG các giả định mặc định hay sai của dev (auth chỉ ở UI, "nội bộ nên an toàn", CORS, config default, lệch branch deploy) bằng request thật. Dùng khi user nói "quét bảo mật", "trivy", "scan vuln", "security scan", "check CVE", "có lỗ hổng không", "an toàn chưa", "/orca-sec-scans".
---

# Skill: orca-sec-scans

## Purpose

Một luồng quét bảo mật static, **chỉ-đọc** (Trivy không sửa mã khi quét), dùng được local lẫn CI/Jenkins. Bao trùm: dependency CVE (Go/Node/Python lockfile), misconfig (Dockerfile/compose/nginx), và secret lộ trong file.

## Triggers

- User nói "quét bảo mật", "scan", "trivy", "check CVE", "security scan", "có lỗ hổng không"
- Trước khi release / merge nhánh deploy
- Định kỳ trong CI (`trivy fs . --config trivy.yaml --exit-code 1`)

## Workflow

### Bước 0 — Check + Install Trivy (BẮT BUỘC chạy trước)

```bash
if ! command -v trivy >/dev/null 2>&1; then
  echo "Trivy chưa có → cài…"
  if [[ "$(uname)" == "Darwin" ]]; then
    brew install trivy
  else
    # Linux: dùng script chính thức Aqua (không cần root nếu set BINDIR)
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
      | sh -s -- -b /usr/local/bin
  fi
fi
trivy --version   # xác nhận; DB vuln tự cập nhật lần chạy đầu
```

### Bước 1 — Detect ngôn ngữ (scope quét)

Tìm lockfile để biết hệ sinh thái: `go.sum`/`go.mod` (Go), `package-lock.json`/`pnpm-lock.yaml` (Node), `requirements.txt`/`poetry.lock` (Python). Bỏ qua `node_modules`, `.next`, `.contentlayer`, `_archives`, `.git`.

### Bước 2 — Quét (HIGH+CRITICAL trước cho nhanh)

```bash
trivy fs <dir> \
  --scanners vuln,misconfig,secret \
  --severity HIGH,CRITICAL \
  --skip-dirs '**/node_modules' --skip-dirs '**/.next' \
  --skip-dirs '**/.contentlayer' --skip-dirs '_archives' \
  --no-progress
```

Repo bonbon-ai: quét riêng `be` và `fe` (mỗi cái là submodule). Ưu tiên `--config trivy.yaml` nếu repo đã có.

### Bước 3 — Xuất report đầy đủ

```bash
mkdir -p security
TPL=$(find $(brew --prefix trivy 2>/dev/null || echo /opt/homebrew) -name html.tpl 2>/dev/null | head -1)
trivy fs . <cờ skip-dirs như trên> --no-progress -f json     -o security/trivy-report.json
trivy fs . <cờ skip-dirs như trên> --no-progress -f template --template "@$TPL" -o security/trivy-report.html
```

### Bước 4 — Tóm tắt & đề xuất fix

Đếm HIGH/CRITICAL theo từng target, in bảng. Sau đó đề xuất (KHÔNG auto-bump hàng loạt nếu submodule đang có thay đổi chưa commit):

- **Dep bump dễ** (direct dep, sửa thẳng manifest): vd `python-multipart` trong `requirements.txt`.
- **Dep indirect**: `go get <pkg>@<ver>` rồi `go build ./...` verify. Lưu ý `go get` có thể nâng directive `go`; nếu vượt base image trong Dockerfile thì bump luôn `FROM golang:X-alpine` cho khớp.
- **Misconfig DS-0002 (root user)**: thêm `USER` non-root vào Dockerfile (`adduser -D` alpine, `useradd -m` debian, hoặc `USER node` cho image node-alpine; nhớ `chown` thư mục ghi như volume/data).
- **Secret**: nếu Trivy flag → xoay key ngay, không chỉ xoá khỏi file.

### Bước 5 — Re-scan xác nhận

Chạy lại Bước 2 trên target đã fix, xác nhận `remaining = NONE`.

## Quét ĐỘNG — kiểm chứng giả định của dev (bổ sung cho Trivy)

> **Nguyên tắc: Trivy (static) KHÔNG bắt được lỗi kiến trúc/logic/cấu hình runtime.** Lỗ hổng nặng nhất thường nằm ở **giả định mặc định của developer** — phải kiểm chứng bằng **request thật**, không tin lời. "Chạy được" ≠ "an toàn".

*Đúc kết từ sự cố 22/06/2026: API ETL payroll không có auth (auth chỉ ở tầng web, path `/etl` qua nginx đi vòng qua) → ai cũng `curl` lấy được lương + PII 3.637 NV; tưởng "nội bộ" nhưng có domain public `devtingting.coteccons.vn` (IP public) bắc cầu ra cả internet. Trivy không phát hiện — chỉ `curl`/`dig` thật mới ra.*

### Checklist "ĐỪNG TIN — phải kiểm chứng" (dev assumption → thực tế → cách verify)

1. **"API sau reverse proxy được bảo vệ vì web/UI có login."**
   → SAI: auth thường chỉ ở tầng web; path proxy (`/etl`, `/api`...) browser gọi thẳng nên đi VÒNG qua login.
   → Verify: `curl` THẲNG từng route API **không kèm cookie/token** → phải `401`. Nếu `200`+data = lỗ hổng. Auth phải ở tầng API/proxy (vd nginx `auth_request`), KHÔNG chỉ ở UI.
   ```bash
   for p in data/stats/all report/export sync/status; do
     curl -k -o /dev/null -w "$p -> %{http_code}\n" https://HOST/etl/$p; done   # mong đợi 401
   ```

2. **"Server nội bộ / IP private (192.168.x) nên ngoài không vào được."**
   → SAI: một public domain / `tailscale funnel` / port-forward có thể bắc cầu vào.
   → Verify: `dig +short <mọi subdomain khả dĩ>` → có IP public không? Thử curl từ mạng ngoài. KHÔNG tin "nội bộ" — kiểm DNS thật.

3. **"Mở CORS là lỗ hổng / đóng CORS là đủ an toàn."**
   → SAI HƯỚNG: CORS chỉ chặn **browser ĐỌC** cross-origin. KHÔNG chặn `curl`/script; KHÔNG chặn **CSRF GHI** (POST query-param / không-body = *simple request* → không preflight → server chạy bất kể CORS). Lỗ thật thường là **no-auth + port mở**. Đừng tốn công CORS khi cửa chính (auth) chưa khóa.

4. **"Config mặc định để nguyên là ổn."**
   → Check biến default lọt prod: `CORS_ORIGINS` còn `localhost:3000`? secret/flag còn giá trị mẫu? `BIND_HOST` vô tình `0.0.0.0`?
   ```bash
   curl -k -D- -o /dev/null -H "Origin: http://localhost:3000" https://HOST/etl/health | grep -i access-control
   ```

5. **"Branch nào deploy cũng như nhau."**
   → SAI: CI (Jenkins) clone branch X nhưng server chạy branch Y → lệch. Merge conflict có thể **rớt nguyên block** (vd `networks:` trong compose → `undefined network`, deploy fail).
   → Verify: branch CI clone == branch đang chạy? `git diff <ci-branch> <running-branch> -- docker-compose.yml .env* deploy/`.

6. **"paramiko/SSH kết nối được là xong."**
   → `Transport(...)` / `AutoAddPolicy` KHÔNG verify host key → MITM đánh cắp pass + file. Verify: phải pin known_hosts + `RejectPolicy`.

7. **"Token/secret truyền sao cũng được."**
   → Token trong URL `?token=` → vào nginx/uvicorn access-log, Referer, history. Verify: secret đi qua **header/cookie**, KHÔNG qua query string.

8. **"`SELECT *` cho tiện."**
   → Trả mọi cột gồm PII (CCCD/MST/BHXH/lương) + `search` toàn-cột làm oracle dò giá trị. Verify: whitelist cột trả về; search không quét cột nhạy cảm.

### Trigger-conditions — hành vi code nào BẮT BUỘC scan

Không chờ ai nhớ gọi skill — diff rơi vào bảng là nghĩa vụ scan kích hoạt (distill từ `WorldFlowAI/everything-claude-code` security-review):

| Thay đổi vừa làm | Bắt buộc | Vì sao |
|---|---|---|
| Thêm/sửa auth, session, phân quyền | Trivy + quét động | Token để localStorage dính XSS, thiếu check role trước thao tác nhạy cảm — lớp lỗi authorization là thứ Trivy không thấy. |
| Nhận input người dùng (form, param, upload) | Trivy + quét động | Input không validate bằng schema + file upload không giới hạn size/type/extension là cửa vào SQLi/XSS/RCE. |
| Đụng secret / credential / API key | Trivy (secret scan) | Key hardcode trong source hoặc lọt git history — phải ở env var và platform secret, `.env` phải gitignore. |
| Mở API endpoint mới | Trivy + quét động | Endpoint mới mặc định THIẾU rate-limit + CSRF + check quyền; error message dễ lộ chi tiết nội bộ/stack trace. |
| Thanh toán / dữ liệu nhạy cảm | Trivy + quét động + review tay | PII/tiền không được vào log, error phải generic; một lỗ là compromise cả nền tảng — err on the side of caution. |
| Đưa app ra public domain / đổi reverse proxy | Quét động | Lỗ no-auth "nội bộ" biến thành internet-exposed đúng lúc đó (checklist giả định dev ở trên). |

Không rơi vào bảng → scan theo nhịp release là đủ. Câu tự kiểm: **"diff này có làm một trong 6 việc trên không?"** — trả lời được dưới một phút. User nói "có lỗ hổng không", "an toàn chưa" → luôn là trigger.

## Rules

- **Static (Trivy) + Động (checklist trên) là HAI lớp khác nhau — chạy CẢ HAI.** Trivy bắt CVE/misconfig/secret-in-file; nó KHÔNG bắt auth bypass, public exposure, CORS/CSRF logic, lệch branch. Đừng coi report Trivy sạch = an toàn.
- **Không tin giả định mặc định của dev** — mọi "đã có login", "nội bộ nên an toàn", "chạy được rồi" phải kiểm chứng bằng request thật trước khi kết luận.
- Trivy **không sửa mã** khi quét — an toàn chạy bất kỳ lúc nào.
- Finding đã review & chấp nhận → ghi vào `.trivyignore` (1 ID/dòng + comment lý do + ngày), KHÔNG xoá khỏi report.
- Không commit `security/*.json|html` lên server deploy — chỉ là artifact review.
- Khi deploy bonbon-ai: **chỉ push `be` và `fe`** (2 submodule) lên server; tooling (trivy.yaml, security/, skill) không lên server.
- Mọi thay đổi fix phải qua build/verify trước khi commit (`go build ./...`, `pnpm i`, …).

## Origin
- **Absorb 2026-07-17 (adapt_mode: dissolve, T-260717-02):** bảng trigger-conditions distill từ `WorldFlowAI/everything-claude-code` (`skills/security-review/SKILL.md` — When to Activate + 10 nhóm checklist). Clone depth-1 trong scratchpad/, không vendor bytes.
