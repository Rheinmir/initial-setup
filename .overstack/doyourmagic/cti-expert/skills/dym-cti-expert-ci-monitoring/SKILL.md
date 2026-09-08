---
name: dym-cti-expert-ci-monitoring
description: "Chạy cti-expert trong CI của **dự án bạn**. biến các op miễn phí, không cần key thành một job theo dõi định kỳ — typosquat của thương hiệu, cert mới trong CT log — thay vì nhớ chạy tay."
disable-model-invocation: true
---

# Skill: dym-cti-expert-ci-monitoring — Chạy cti-expert trong CI của **dự án bạn**

**Vì sao dùng:** biến các op miễn phí, không cần key thành một job theo dõi định kỳ — typosquat của thương hiệu, cert mới trong CT log — thay vì nhớ chạy tay.
**Sinh ra cái gì:** một workflow trong repo *của bạn*, file state được commit, và artifact JSON để soi khi có phát hiện.

> Ví dụ dưới đây được **viết mới cho trường hợp của người tiêu thụ**. Nó *không phải* bản chép của `.github/workflows/audit.yml` hay `smoke.yml` trong repo cti-expert — hai file đó gate việc phát triển *chính công cụ* (drift cấu trúc, cài từ máy trắng) và không có tác dụng gì cho bạn. Đọc chúng để hiểu, đừng copy.

---

## Chọn op nào cho CI

Điều kiện để một op hợp với CI: **không cần key, không cần `.venv`, và mã thoát nói được điều gì đó.** Ba ứng viên:

| Op | Làm gì | Chi phí |
|---|---|---|
| `impersonate <domain>` | sinh + kiểm biến thể typosquat qua crt.sh + DNS | miễn phí (thêm `--fofa`/`--urlscan` mới tốn credit) |
| `ct-monitor watch --state <file> <pattern>` | poll CT log, lọc cert mới khớp thương hiệu | miễn phí |
| `hash-id`, `sensitive-paths`, `email-hygiene` | thuần, không mạng | miễn phí |

Kiểm offline trước khi wire (chạy thật, không chạm mạng):

```bash
python3 scripts/backend/intel.py impersonate example.com --generate-only --max 5
```

```json
{"seed":"example.com","label":"example","tld":"com","variants":[
 {"domain":"xample.com","technique":"omission"},
 {"domain":"eeexample.com","technique":"repetition"},
 {"domain":"wxample.com","technique":"replacement"},
 {"domain":"wexample.com","technique":"insertion"},
 {"domain":"rxample.com","technique":"replacement"}],
 "count":5,"truncated":true}
```

`--generate-only` là chế độ hoàn toàn offline — dùng nó cho bước "CI có chạy được không" mà không phụ thuộc mạng.

## Ví dụ tối giản — GitHub Actions

Đặt ở repo **của bạn**, `.github/workflows/brand-watch.yml`:

```yaml
name: brand-watch

on:
  schedule:
    - cron: '0 6 * * *'      # 06:00 UTC mỗi ngày
  workflow_dispatch:

permissions:
  contents: write            # để commit lại file state của ct-monitor

jobs:
  watch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # Lớp stdlib của cti-expert không cần cài gì — clone là chạy.
      - name: Fetch cti-expert
        run: git clone --depth 1 https://github.com/7onez/cti-expert.git "$RUNNER_TEMP/cti"

      - name: Typosquat sweep
        run: |
          set -euo pipefail
          python3 "$RUNNER_TEMP/cti/scripts/backend/intel.py" \
            impersonate "${{ vars.BRAND_DOMAIN }}" --pretty > impersonate.json

      - name: CT-log watch (state được commit để chỉ báo cái MỚI)
        run: |
          set -euo pipefail
          mkdir -p .brandwatch
          python3 "$RUNNER_TEMP/cti/scripts/backend/intel.py" \
            ct-monitor watch "${{ vars.BRAND_KEYWORD }}" \
            --state .brandwatch/ct-state.json --json > ct-new.json

      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: brand-watch-${{ github.run_number }}
          path: |
            impersonate.json
            ct-new.json

      - name: Persist CT state
        run: |
          git config user.name  github-actions
          git config user.email github-actions@github.com
          git add .brandwatch/ct-state.json
          git diff --cached --quiet || git commit -m "chore(brand-watch): cập nhật state CT"
          git push
```

Hai chi tiết cố ý:

- **`--state` được commit lại.** Không có nó, mỗi lần chạy đều coi *mọi* cert là mới và job trở thành máy phát spam.
- **Không có key nào trong workflow.** Cả hai op đều chạy keyless. Ngày nào bạn thêm `--fofa`/`--urlscan`, lúc đó mới cần secret — và lúc đó nhớ đọc lại [02](02-api-keys-and-capabilities.md) về hai sổ chi phí.

## Rẽ nhánh theo mã thoát — đọc [04](04-cli-dispatcher.md) trước

Đừng viết `|| echo "failed"`. Mã thoát của dispatcher có nghĩa cụ thể:

```bash
set +e
python3 "$CTI/scripts/backend/intel.py" impersonate "$DOMAIN" --pretty > out.json
rc=$?
set -e
case "$rc" in
  0) : ;;                                            # chạy được — đọc out.json để quyết định
  2) echo "::error::sai tên op — chạy intel.py list"; exit 1 ;;
  3) echo "::error::không thấy backend — clone hỏng hoặc thiếu intel_engine"; exit 1 ;;
  4) echo "::error::component chưa cài cho op này"; exit 1 ;;
  5) echo "::error::interpreter không exec được — đặt INTEL_PY"; exit 1 ;;
  *) echo "::error::script engine thoát $rc"; exit 1 ;;
esac
```

**Quan trọng:** `0` nghĩa là *op chạy xong*, **không** nghĩa là *không có phát hiện*. Phán quyết nằm trong JSON, không nằm ở mã thoát. Muốn gate thì tự đọc JSON:

```bash
python3 - <<'PY'
import json
d = json.load(open("impersonate.json"))
imp = d["artifacts"]["impersonation"]
print(f'::notice::sinh {imp["generated"]} bien the | '
      f'{imp["existing_count"]} da TON TAI | {imp["candidate_count"]} chua dang ky')

confirmed = [p for p in d["pivots"] if p.get("kind") == "impersonation:candidate"]
if confirmed:
    print(f"::warning::{len(confirmed)} lookalike da ton tai")
    for p in confirmed[:20]:
        print(" -", p.get("value"), "|", p.get("confidence"))
PY
```

Các trường dùng ở trên (`artifacts.impersonation.generated` / `existing_count` / `candidate_count`, và `pivots[].kind`) lấy từ `build_impersonation_result` trong `intel_engine/WebPivot/tools/wp_impersonate.py`, không phải đoán. Phân biệt quan trọng: **existing** = có DNS phân giải *hoặc* đã thấy trong CT/FOFA/urlscan; **candidate** = biến thể sinh ra chưa có bằng chứng nào — đó là watchlist để theo dõi, **không phải** hạ tầng đã xác nhận.

## Cái gì **không** nên đưa vào CI

- Bất kỳ op nào trong danh sách gate outbound ([07](07-safety-gates.md)): `engage`, `engage-harvest`, `--submit`, `misp push/publish`. Hook `actionguard.py` **không chạy trong CI** — nó là hook của Claude Code, không phải của shell. Trong CI bạn chỉ còn gate trong code, và với `misp publish` thì không có nút hoàn tác nào cả.
- Pipeline case đầy đủ (`pipeline open`) với `--serp` / `--whois-reverse` / `--fofa-full`: mỗi lần chạy tiêu credit thật, và cron thì chạy mãi.
- Bất cứ thứ gì ghi vào `intel_engine/cases/` rồi commit — đó là dữ liệu điều tra, và RULE 1 tồn tại chính vì việc này.
