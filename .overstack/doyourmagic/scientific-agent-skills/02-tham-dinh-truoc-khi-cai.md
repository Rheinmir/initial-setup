# 02 — Thẩm định một skill TRƯỚC khi cài

**Vì sao dùng:** Agent Skill là chỉ dẫn mà agent của bạn sẽ *tuân theo* — nó có thể bảo agent chạy code tuỳ ý, cài package, gọi mạng, sửa file. Repo này nhận đóng góp cộng đồng và tự nói thẳng là không đảm bảo đã soát hết. Đây là bước bắt buộc trước [01](01-cai-dat-skills.md).
**Sinh ra cái gì:** một quyết định cài/không cài cho từng skill, dựa trên nội dung skill + báo cáo quét của repo + (tuỳ chọn) một lần quét cục bộ của chính bạn.

---

## Bước 1 — Đọc `SKILL.md` mà không cài

```bash
# render SKILL.md trong terminal, không ghi file nào
gh skill preview K-Dense-AI/scientific-agent-skills literature-review

# ghim một version cụ thể để đọc
gh skill preview K-Dense-AI/scientific-agent-skills literature-review@v2.66.0
```

Chạy tương tác, `gh skill preview` còn cho picker để duyệt thêm `scripts/`, `references/`. Đây mới là chỗ cần soi: một skill xấu hiếm khi xấu ở `SKILL.md`, nó xấu trong `scripts/`.

Cần đọc bằng shell (grep, diff) thì clone read-only rồi soi:

```bash
git clone --depth 1 https://github.com/K-Dense-AI/scientific-agent-skills.git /tmp/sas
cd /tmp/sas

# skill này chạm mạng ở đâu, gọi shell ở đâu
grep -rnE 'requests\.|urlopen|subprocess|os\.system|curl |wget ' skills/literature-review/

# skill này đòi biến môi trường nào
grep -rn 'environ\|getenv\|API_KEY' skills/literature-review/
```

## Bước 2 — Tra báo cáo quét của repo

Repo chạy [Cisco AI Defense Skill Scanner](https://github.com/cisco-ai-defense/skill-scanner) hằng tuần (cron Thứ Hai 09:00 UTC, `.github/workflows/security-scan.yml`), quét gia tăng — skill không đổi thì mang kết quả cũ sang; rescan toàn bộ ít nhất mỗi 30 ngày hoặc khi đổi scanner/model.

- Người đọc: `docs/security-report.md`
- Máy đọc (có `last_scanned` từng skill): `docs/security-report.json`

Tổng ở lần quét `2026-08-31` (đọc từ `docs/security-report.json` → `totals`):

```
163 skill · 988 finding · CRITICAL 34 · HIGH 9 · MEDIUM 241 · LOW 703 · INFO 1
skill "an toàn": 147/163
```

**16 skill đang mang finding CRITICAL hoặc HIGH** — trích từ trường `max_severity` trong JSON, không phải từ bảng tóm tắt:

| Mức | Skill | Số finding |
|---|---|---|
| CRITICAL | `autoskill` | 13 |
| CRITICAL | `citation-management` | 11 |
| CRITICAL | `consciousness-council` | 5 |
| CRITICAL | `infographics` | 9 |
| CRITICAL | `latex-posters` | 9 |
| CRITICAL | `literature-review` | 10 |
| CRITICAL | `pacsomatic` | 5 |
| CRITICAL | `research-lookup` | 8 |
| CRITICAL | `scientific-schematics` | 9 |
| CRITICAL | `scientific-slides` | 15 |
| CRITICAL | `xlsx` | 3 |
| HIGH | `geomaster` | 7 |
| HIGH | `ginkgo-cloud-lab` | 3 |
| HIGH | `histolab` | 4 |
| HIGH | `modal` | 7 |
| HIGH | `waypoint-bio` | 5 |

Tự sinh lại bảng này trên bản mới hơn:

```bash
python3 - <<'PY'
import json
d = json.load(open("docs/security-report.json"))
for s in sorted(d["skills"], key=lambda s: s["name"]):
    if (s.get("max_severity") or "").upper() in ("CRITICAL", "HIGH"):
        print(f'{s["max_severity"]:8} {s["name"]:28} {len(s["findings"])} findings  last_scanned={s["last_scanned"]}')
print(d["totals"])
PY
```

**Finding không đồng nghĩa với độc hại.** Chính `AGENTS.md` liệt kê các false positive hệ thống: `BEHAVIOR_*_EXFILTRATION` và `BEHAVIOR_ENV_VAR_HARVESTING` bắn vào bất kỳ skill nào đọc API key *của chính nó* rồi gọi service *của chính nó*; `MDBLOCK_PYTHON_SUBPROCESS` bắn vào mọi đoạn `subprocess`, kể cả dạng argument-list an toàn; `*_EVAL_EXEC` bắn vào chuỗi con trong định danh thường (`retrieval`, `executor`) hoặc `model.eval()`. Dùng bảng trên để **quyết định đọc kỹ skill nào**, không phải để kết tội.

## Bước 3 — Tự quét cục bộ (khi cần bằng chứng riêng)

```bash
uv pip install cisco-ai-skill-scanner
skill-scanner scan /path/to/skill --use-behavioral
```

Hoặc dùng wrapper của repo — nó thêm định dạng comment PR và ngưỡng chặn:

```bash
# cần SKILL_SCANNER_LLM_API_KEY (đọc từ .env qua python-dotenv)
uv run python scan_pr_skills.py skills/literature-review --fail-on HIGH
```

**Exit code của `scan_pr_skills.py` — đọc từ source, đừng đoán:**

| Exit | Nghĩa | Nguồn |
|---|---|---|
| `0` | không có skill dir hợp lệ → viết comment no-op | `scan_pr_skills.py:229` |
| `0` | thiếu `SKILL_SCANNER_LLM_API_KEY` → **fail open**, bỏ qua quét (đúng như PR từ fork) | `scan_pr_skills.py:240` |
| `1` | có finding ở mức `--fail-on` trở lên | `scan_pr_skills.py:265` |
| `0` | quét xong, dưới ngưỡng | `scan_pr_skills.py:267` |

Hai chi tiết dễ sập bẫy:

- **Mặc định `--fail-on` là `CRITICAL`**, nhưng CI của repo truyền `--fail-on HIGH` (`.github/workflows/pr-skill-scan.yml:87`). Chạy tay mà muốn giống CI thì phải tự truyền.
- **Thiếu API key trả về 0, không phải lỗi.** Nếu bạn cắm lệnh này vào gate của mình, exit 0 **không** chứng minh đã quét. Kiểm luôn stdout hoặc đảm bảo biến môi trường tồn tại.

`--fail-on` nhận: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `NEVER`.

## Bước 4 — Quyết định cài gì

Nguyên tắc rút từ chính khuyến cáo của repo, xếp theo thứ tự áp dụng:

1. **Không cài `--all`.** Cài đúng skill phục vụ việc đang làm.
2. **Skill do K-Dense viết (`metadata.skill-author: K-Dense Inc.`) đã qua review nội bộ** của họ; skill cộng đồng thì soát ở mức "hết khả năng, nguồn lực có hạn". Xem tác giả:
   ```bash
   grep -h 'skill-author' skills/*/SKILL.md | sort | uniq -c | sort -rn | head
   ```
3. **Skill có `scripts/` đáng soi hơn skill chỉ có prose.** 105/163 skill mang `scripts/`.
4. **Skill khai `metadata.openclaw.envVars` sẽ đòi credential** — 25 skill như vậy, danh sách ở [03-dung-skill-trong-agent.md](03-dung-skill-trong-agent.md).
5. **Thấy gì đáng ngờ thì mở issue** ở repo thay vì im lặng gỡ ra.

## Cạm bẫy

- **`docs/security-report.md` là ảnh chụp tại thời điểm quét**, không phải trạng thái hiện tại. Đối chiếu `last_scanned` của skill với ngày commit gần nhất chạm skill đó trước khi tin.
- **Finding trỏ vào file skill không hề có.** `AGENTS.md` cảnh báo tình huống này; xác minh bằng `find skills/<name> -type f` trước khi "sửa".
- **Quét skill không phải quét dependency.** Scanner soi nội dung skill; các package Python mà skill hướng dẫn cài vẫn là bề mặt tấn công riêng.
