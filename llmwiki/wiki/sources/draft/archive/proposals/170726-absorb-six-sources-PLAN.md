---
type: draft
title: absorb-six-sources-PLAN
status: proposed
timestamp: 2026-07-17
task: T-260717-02
---

# Absorb HÒA TAN 6 nguồn — PLAN thi hành

**Goal:** Distill 6 nguồn GitHub vào 5 bề mặt có sẵn (qc-code, orca-sec-scans, hallmark/design-foundation, mem-rank, orca-issue) — không thêm skill mới, không thêm dependency.
**Architecture:** Mỗi task là một lát cắt dọc: clone nguồn → đọc → distill vào đúng anchor của file đích → verify bằng rg/self-test → đích canonical `skills/` rồi sync mirror một lượt ở T6. Executor là Claude trong phiên (SPEC đã chốt — distill cần phán đoán); PLAN vẫn viết đủ để agent không-context làm đúng.
**Tech stack:** Markdown (SKILL.md), Python 3 (mem-rank.py — stdlib, không thêm lib), bash verify (rg), sync bằng `harness/scripts/sync-skills.py`.
**SPEC nguồn:** `wiki/sources/draft/170726-absorb-six-sources.md` (đã duyệt 2026-07-17, gate_5a6720864d05)

## Origin
- **SPEC:** `wiki/sources/draft/170726-absorb-six-sources.md`
- **Commit:** _(verify-before-commit điền)_

## Global constraints

Chép nguyên văn từ SPEC — mọi task ngầm mang theo:

- **ADR-003:** "Toàn bộ hành vi [skill] sống trong [canonical]. Sửa hành vi chỉ sửa file này; mirror và bản remote được đồng bộ qua `sync-template`, không chép tay." Đích sửa là `skills/<tên>/SKILL.md` (canonical), sau đó sync mirror `llmwiki/skills/`.
- **Parity CI:** `skills-sync.yml` chặn drift 2 cây skill — commit thiếu sync là đỏ.
- **R15:** cấm AI-attribution trong commit message (chặn cứng ở commit-msg hook).
- **adapt-modes:** "Ghi `adapt_mode` vào `provenance` cho mỗi skill ngoài" — mỗi phần hòa tan ghi `adapt_mode: dissolve` + nguồn + ngày vào mục Origin của skill đích.
- **Ponytail/CLAUDE.md mục 2:** không phình — tổng diff mỗi skill đích ≤ ~80 dòng; distill là NÉN, không phải chép.
- **Cổng trước push:** `medic --ci` xanh; wiki entry chính thức chỉ tạo SAU khi code commit.
- **Prose rule (feedback 2026-06-27):** phần thêm vào SKILL.md người đọc được — câu hoàn chỉnh, không caveman.

## File structure

- Sửa `skills/qc-code/SKILL.md` (74 dòng) — thêm bảng 13 nhóm check + nhãn severity + mục "Nhận review"
- Sửa `skills/orca-sec-scans/SKILL.md` (130 dòng) — mở rộng mục "Khi nào chạy" (dòng 117-121) thành bảng trigger-conditions
- Tạo `skills/hallmark/references/frontend-design-delta.md` — CHỈ các luật frontend-design mà sàn chưa có (nếu U-01 xác nhận nguồn tồn tại)
- Sửa `llmwiki/wiki/concepts/design-foundation.md` — thêm mục đối chiếu + Origin
- Sửa `harness/scripts/mem-rank.py` — thêm lệnh `export` / `import <file>` + self-test round-trip
- Clone tạm (gitignored): `scratchpad/gstack`, `scratchpad/code-review-skill`, `scratchpad/everything-claude-code`, `scratchpad/anthropic-skills`; `scratchpad/superpowers` đã có sẵn
- Mirror `llmwiki/skills/**` — KHÔNG sửa tay; sinh bằng `sync-skills.py` ở T6

### Task 1: 13 nhóm check + severity → `skills/qc-code/SKILL.md`

**Thoả:** FR-001, FR-002

**Files:**
- Sửa: `skills/qc-code/SKILL.md` (chèn sau mục `### 4. Logic & bug` kết thúc ~dòng 47, trước `## Kết luận (verdict)` dòng 48)
- Nguồn: `scratchpad/gstack/review/SKILL.md`, `scratchpad/code-review-skill/SKILL.md`

**Interfaces:**
- Consumes: cấu trúc 4 mục hiện có của qc-code (giữ nguyên, không đổi tên mục).
- Produces: mục mới `## Bản đồ 13 nhóm lỗi (gstack) + severity` — T5 chèn mục "Nhận review" NGAY SAU mục này nên tên heading phải đúng nguyên văn trên.

- [ ] **Step 1: clone 2 nguồn (depth 1, vào scratchpad — gitignored)**

```bash
cd /Users/giatran/orca/setup/setup
git clone --depth 1 https://github.com/garrytan/gstack scratchpad/gstack
git clone --depth 1 https://github.com/awesome-skills/code-review-skill scratchpad/code-review-skill
ls scratchpad/gstack/review/SKILL.md scratchpad/code-review-skill/SKILL.md
```

Mong đợi: cả 2 path in ra, không lỗi. Nếu `review/SKILL.md` không tồn tại → `find scratchpad/gstack -name "SKILL.md" | head` để tìm skill review thật, cập nhật path nguồn trong các step sau.

- [ ] **Step 2: đọc nguồn, distill bảng vào qc-code**

Đọc `scratchpad/gstack/review/SKILL.md` đủ để viết MỖI nhóm một câu mô tả + một ví dụ ngắn. Chèn vào `skills/qc-code/SKILL.md` trước dòng `## Kết luận (verdict)` khối sau (mô tả mỗi nhóm distill từ nguồn, KHÔNG chép nguyên đoạn):

```markdown
## Bản đồ 13 nhóm lỗi (gstack) + severity

Mỗi finding gắn đúng MỘT nhóm + MỘT severity. 5 nhóm CRITICAL soi trước:

| # | Nhóm (CRITICAL) | Soi cái gì |
|---|---|---|
| 1 | SQL & data safety | <1 câu distill từ nguồn> |
| 2 | Race condition & concurrency | <1 câu> |
| 3 | LLM output trust boundary | <1 câu> |
| 4 | Shell injection | <1 câu> |
| 5 | Enum & value completeness | <1 câu> |

8 nhóm INFORMATIONAL: async/sync mixing · column/field-name safety · LLM prompt ·
type coercion · view/frontend · time-window safety · completeness gaps · distribution & CI/CD
— mỗi nhóm một dòng định nghĩa (distill từ nguồn).

**Severity** (distill từ awesome-skills/code-review-skill): `blocking` = sai là không được merge ·
`important` = phải sửa sớm, không chặn merge · `nit` = nhỏ, tuỳ tác giả · `suggestion` = hướng
cải thiện, không bắt buộc. Format finding: `[<nhóm>][<severity>] <mô tả> — <cách sửa>`.
```

Ghi chú thi hành: các ô `<1 câu...>` PHẢI được thay bằng câu thật distill từ file nguồn ngay trong lượt sửa này — không được để nguyên dấu ngoặc nhọn (R7 quét placeholder lúc commit).

- [ ] **Step 3: verify bằng rg**

```bash
rg -c '^\| [0-9]' skills/qc-code/SKILL.md        # mong đợi: 5 (5 dòng bảng CRITICAL)
rg -c 'blocking|important|nit|suggestion' skills/qc-code/SKILL.md   # mong đợi: ≥1
rg -n '<1 câu' skills/qc-code/SKILL.md            # mong đợi: KHÔNG khớp gì (exit 1)
wc -l skills/qc-code/SKILL.md                     # mong đợi: ≤ 74+55 = 129 dòng (trần ponytail)
```

### Task 2: trigger-conditions → `skills/orca-sec-scans/SKILL.md`

**Thoả:** FR-003

**Files:**
- Sửa: `skills/orca-sec-scans/SKILL.md:117-121` (mục `### Khi nào chạy quét động (BẮT BUỘC)`)
- Nguồn: `scratchpad/everything-claude-code/skills/security-review/SKILL.md`

**Interfaces:**
- Consumes: mục "Khi nào chạy quét động" hiện có (danh sách ngắn) — thay bằng bảng đầy đủ.
- Produces: heading mới `### Trigger-conditions — hành vi code nào BẮT BUỘC scan` (T6 ghi Origin ngay cuối file này).

- [ ] **Step 1: clone nguồn**

```bash
cd /Users/giatran/orca/setup/setup
git clone --depth 1 https://github.com/WorldFlowAI/everything-claude-code scratchpad/everything-claude-code
ls scratchpad/everything-claude-code/skills/security-review/SKILL.md
```

Mong đợi: path in ra. Không tồn tại → `find scratchpad/everything-claude-code -name "*.md" -path "*security*"`, dùng path tìm được.

- [ ] **Step 2: thay mục 117-121 bằng bảng trigger**

Đọc nguồn, thay mục `### Khi nào chạy quét động (BẮT BUỘC)` bằng:

```markdown
### Trigger-conditions — hành vi code nào BẮT BUỘC scan

| Thay đổi vừa làm | Bắt buộc | Vì sao (distill từ nguồn) |
|---|---|---|
| Thêm/sửa cơ chế auth, session, phân quyền | Trivy + quét động | <1 câu> |
| Nhận input người dùng (form, param, upload) | Trivy + quét động | <1 câu> |
| Đụng secret/credential/API key | Trivy (secret scan) | <1 câu> |
| Mở API endpoint mới | Trivy + quét động | <1 câu> |
| Tính năng thanh toán / dữ liệu nhạy cảm | Trivy + quét động + review tay | <1 câu> |

Không rơi vào bảng → scan theo nhịp release là đủ. Câu tự kiểm: "diff này có làm một
trong 5 việc trên không?" — trả lời được dưới một phút.
```

Các ô `<1 câu>` thay bằng câu thật từ nguồn ngay trong lượt sửa (như Task 1).

- [ ] **Step 3: verify**

```bash
rg -c '^\| ' skills/orca-sec-scans/SKILL.md       # mong đợi: tăng ≥6 dòng bảng so với trước
rg -n '<1 câu' skills/orca-sec-scans/SKILL.md     # mong đợi: KHÔNG khớp (exit 1)
```

### Task 3: frontend-design → hallmark delta (verify U-01 TRƯỚC)

**Thoả:** FR-005

**Files:**
- Tạo: `skills/hallmark/references/frontend-design-delta.md` (chỉ khi U-01 = CÓ)
- Sửa: `llmwiki/wiki/concepts/design-foundation.md` (thêm mục đối chiếu ngay trước `## Origin`)
- Nguồn: `scratchpad/anthropic-skills/skills/frontend-design/` (path xác định ở Step 1)

**Interfaces:**
- Consumes: sàn 6 discipline trong `skills/hallmark/references/slop-test.md` (đọc để đối chiếu, không sửa).
- Produces: file delta chỉ chứa luật SÀN CHƯA CÓ; concept design-foundation trỏ tới nó bằng đường dẫn tương đối `skills/hallmark/references/frontend-design-delta.md`.

- [ ] **Step 1: verify U-01 — nguồn có tồn tại không**

```bash
cd /Users/giatran/orca/setup/setup
git clone --depth 1 https://github.com/anthropics/skills scratchpad/anthropic-skills
find scratchpad/anthropic-skills -maxdepth 3 -iname "*frontend*"
```

Mong đợi: một thư mục/file khớp `frontend-design`. **CÓ** → đóng sổ rồi làm tiếp Step 2:
`python3 harness/scripts/unknown-ledger.py --resolve --file unknown-frontend-design.md --id U-01 --value "CÓ — path <path thật>" --fixed "T3 chạy đủ" --date 2026-07-17`.
**KHÔNG CÓ** → đóng sổ với `--value "KHÔNG tồn tại"`, ghi một dòng vào mục Origin của concept design-foundation ("đã kiểm anthropics/skills 2026-07-17 — không có frontend-design, task rút gọn"), bỏ Step 2-3, task kết thúc hợp lệ.

- [ ] **Step 2: đối chiếu từng luật, viết delta**

Đọc SKILL.md nguồn + `skills/hallmark/references/slop-test.md`. Với TỪNG luật của nguồn: đã có trong sàn → ghi vào bảng "trùng — bỏ"; chưa có → ghi vào bảng "thiếu — absorb". Tạo `skills/hallmark/references/frontend-design-delta.md`:

```markdown
# frontend-design (anthropics/skills) — delta so với sàn hallmark

## Luật sàn CHƯA có (absorb làm checkpoint)
| Luật | Nội dung (distill) | Áp khi nào |
|---|---|---|
<mỗi luật thiếu một dòng — distill từ nguồn, câu hoàn chỉnh>

## Luật trùng sàn (không absorb — đã có)
| Luật nguồn | Đã có ở |
|---|---|
<mỗi luật trùng một dòng, cột phải trỏ discipline/cổng slop-test tương ứng>

## Origin
- **Source:** `anthropics/skills` skill `frontend-design` (clone 2026-07-17, depth 1)
- **adapt_mode:** dissolve — đối chiếu từng luật với sàn [[design-foundation]], chỉ absorb phần thiếu.
```

Hai khối `<mỗi luật...>` thay bằng dòng thật ngay trong lượt viết. Nếu sau đối chiếu KHÔNG có luật nào thiếu → vẫn tạo file với bảng "thiếu" ghi đúng một dòng "(không — sàn đã phủ)" + bảng trùng đầy đủ; đó là kết quả hợp lệ (đối chiếu có bằng chứng ≠ không làm).

- [ ] **Step 3: nối concept + verify**

Thêm vào `llmwiki/wiki/concepts/design-foundation.md` (trước `## Origin`) mục 3-5 dòng: đối chiếu frontend-design ngày nào, delta nằm ở `skills/hallmark/references/frontend-design-delta.md`, bao nhiêu luật absorb / bao nhiêu trùng.

```bash
rg -n "frontend-design-delta" llmwiki/wiki/concepts/design-foundation.md   # mong đợi: ≥1 khớp
python3 harness/scripts/unknown-ledger.py --list | rg "U-01"               # mong đợi: status resolved
```

### Task 4: `export` / `import` → `harness/scripts/mem-rank.py`

**Thoả:** FR-004

**Files:**
- Sửa: `harness/scripts/mem-rank.py` — thêm 2 hàm sau `def delete` (dò `rg -n "^def delete" harness/scripts/mem-rank.py`), 2 nhánh dispatch trong `main()` (sau nhánh `delete`), 1 khối self-test, cập nhật docstring dòng 8-16.

**Interfaces:**
- Consumes: `_read(root)` (trả list dict), `_write_all(root, mems)`, `_store_file(root)` — đều có sẵn.
- Produces: CLI `mem-rank.py export` (JSONL ra stdout) và `mem-rank.py import <file>` (in `imported N, skipped M`); T6 không phụ thuộc chữ ký này nhưng SC-002 đo bằng nó.

- [ ] **Step 1: thêm 2 hàm**

```python
def export_all(root) -> int:
    """Dump toàn bộ store ra stdout dạng JSONL — memory di chuyển máy bằng file."""
    mems = _read(root)
    for m in mems:
        print(json.dumps(m, ensure_ascii=False))
    return len(mems)


def import_file(root, path) -> tuple:
    """Nạp JSONL vào store, dedupe theo id (bản trong store thắng — append-only, không ghi đè)."""
    have = {m.get("id") for m in _read(root)}
    added, skipped = [], 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            skipped += 1
            continue
        if not isinstance(rec, dict) or not rec.get("id") or rec["id"] in have:
            skipped += 1
            continue
        have.add(rec["id"])
        added.append(rec)
    if added:
        _write_all(root, _read(root) + added)
    return len(added), skipped
```

- [ ] **Step 2: dispatch trong `main()` (sau nhánh `delete`)**

```python
    if args and args[0] == "export":
        export_all(root); return
    if args and args[0] == "import":
        if len(args) < 2:
            print("usage: mem-rank.py import <file.jsonl>", file=sys.stderr); sys.exit(2)
        n, sk = import_file(root, args[1])
        print(f"imported {n}, skipped {sk}"); return
```

Docstring (sau dòng `delete ID`): thêm 2 dòng `export` / `import <file.jsonl>` mô tả một câu mỗi lệnh.

- [ ] **Step 3: self-test round-trip — thêm vào `self_test()` trước dòng return/print tổng kết**

```python
    # ── export/import round-trip (portability máy↔máy) ──
    with tempfile.TemporaryDirectory() as d2:
        src, dst = Path(d2) / "src", Path(d2) / "dst"
        src.mkdir(); dst.mkdir()
        add(src, "portable fact", mid="port1")
        dump = "\n".join(json.dumps(m, ensure_ascii=False) for m in _read(src))
        f = Path(d2) / "mem.jsonl"; f.write_text(dump, encoding="utf-8")
        n1, _ = import_file(dst, str(f))
        n2, _ = import_file(dst, str(f))          # import lần 2 phải skip hết (dedupe)
        roundtrip_ok = n1 == 1 and n2 == 0 and _read(dst)[0]["id"] == "port1"
```

và nối `roundtrip_ok` vào biểu thức tổng `ok` của self_test (dò `rg -n "ok =" harness/scripts/mem-rank.py` trong hàm self_test, thêm `and roundtrip_ok`).

- [ ] **Step 4: chạy verify**

```bash
python3 harness/scripts/mem-rank.py --self-test        # mong đợi: PASS (có round-trip)
T=$(mktemp -d); python3 harness/scripts/mem-rank.py add "hello export" --root "$T" >/dev/null
python3 harness/scripts/mem-rank.py export --root "$T" | wc -l    # mong đợi: 1
python3 -m py_compile harness/scripts/mem-rank.py && echo OK      # mong đợi: OK
```

### Task 5: superpowers → qc-code "Nhận review" + orca-issue đối chiếu

**Thoả:** FR-006

**Files:**
- Sửa: `skills/qc-code/SKILL.md` — chèn mục `## Nhận review — verify trước khi sửa` NGAY SAU mục `## Bản đồ 13 nhóm lỗi (gstack) + severity` (Task 1 tạo)
- Sửa: `skills/orca-issue/SKILL.md:15-27` (Steps 5 chốt + Rules) — chỉ thêm chốt mà vòng hiện tại CHƯA nói
- Nguồn: `scratchpad/superpowers/skills/receiving-code-review/SKILL.md`, `scratchpad/superpowers/skills/systematic-debugging/SKILL.md` (có sẵn, không cần clone)

**Interfaces:**
- Consumes: heading `## Bản đồ 13 nhóm lỗi (gstack) + severity` nguyên văn từ Task 1 (anchor chèn).
- Produces: mục `## Nhận review — verify trước khi sửa` trong qc-code; orca-issue giữ nguyên cấu trúc "5 chốt".

- [ ] **Step 1: distill receiving-code-review → qc-code**

Đọc nguồn rồi chèn (distill thành ~10-15 dòng, câu hoàn chỉnh):

```markdown
## Nhận review — verify trước khi sửa

Finding của reviewer (người, LLM, kể cả chính /qc-code) là CLAIM, chưa phải sự thật.
Trước khi sửa theo bất kỳ finding nào: (1) tái hiện hoặc đọc đúng đoạn code được trỏ —
claim có đúng với code thật không; (2) claim mơ hồ → hỏi lại/ghi chú, không đoán ý;
(3) chỉ sửa khi đã tự thấy lỗi; finding sai → phản hồi kèm bằng chứng thay vì lặng lẽ bỏ qua.
Blind-comply với review sai tạo bug mới mang vẻ mặt "đã được review".
```

(Đoạn trên là khung distill — khi thi hành, đối chiếu nguồn và điều chỉnh cho đúng tinh thần nguồn, giữ ≤15 dòng.)

- [ ] **Step 2: đối chiếu systematic-debugging → orca-issue**

Đọc nguồn, so với 5 chốt hiện có (`skills/orca-issue/SKILL.md:15-22`). Chốt nào nguồn có mà vòng chưa nói thành lời (ứng viên đã biết: "đọc thông báo lỗi NGUYÊN VĂN trước khi đoán", "cấm shotgun-fix — mỗi lần chỉ đổi MỘT biến rồi đo lại") → thêm vào `## Rules` dưới dạng mỗi chốt một dòng. Chốt đã có tương đương → KHÔNG thêm (ghi vào Origin "đã có: <chốt>").

- [ ] **Step 3: verify**

```bash
rg -n "## Nhận review" skills/qc-code/SKILL.md          # mong đợi: 1 khớp, nằm sau mục Bản đồ
wc -l skills/qc-code/SKILL.md                            # mong đợi: ≤ 145 (74 gốc + T1 + T5 ≤ ~70)
wc -l skills/orca-issue/SKILL.md                         # mong đợi: ≤ 40 (28 gốc + ≤12)
```

### Task 6: provenance + sync mirror + verify toàn cục

**Thoả:** FR-007

**Files:**
- Sửa: mục `## Origin` của `skills/qc-code/SKILL.md`, `skills/orca-sec-scans/SKILL.md`, `skills/orca-issue/SKILL.md` (file nào chưa có mục Origin thì thêm cuối file)
- Sinh: `llmwiki/skills/**` qua sync (KHÔNG sửa tay)

**Interfaces:**
- Consumes: mọi diff của T1-T5 đã xong.
- Produces: cây mirror khớp canonical; medic xanh — điều kiện để commit.

- [ ] **Step 1: ghi provenance từng đích**

Vào Origin mỗi skill đã sửa, thêm dòng theo mẫu (điền đúng nguồn của skill đó):

```markdown
- **Absorb 2026-07-17 (adapt_mode: dissolve):** distill từ `garrytan/gstack` (review/SKILL.md — 13 nhóm check) + `awesome-skills/code-review-skill` (severity) + `obra/superpowers` (receiving-code-review). Clone depth-1 trong scratchpad/, không vendor bytes.
```

- [ ] **Step 2: sync mirror + kiểm parity**

```bash
python3 harness/scripts/sync-skills.py            # GHI mirror từ canonical
python3 harness/scripts/sync-skills.py --check    # mong đợi: exit 0, không kêu LỆCH
```

- [ ] **Step 3: cổng toàn cục + commit**

```bash
python3 fdk/tools/medic.py --ci                   # mong đợi: 0 fail
git add skills/qc-code/SKILL.md skills/orca-sec-scans/SKILL.md skills/orca-issue/SKILL.md \
        skills/hallmark/references/frontend-design-delta.md llmwiki/wiki/concepts/design-foundation.md \
        harness/scripts/mem-rank.py llmwiki/skills/ llmwiki/wiki/draft/unknown/unknown-frontend-design.md
git commit -m "feat(absorb): hoa tan 6 nguon — qc-code 13 nhom+severity, sec-scans trigger, mem-rank export/import, hallmark delta, orca-issue doi chieu (T-260717-02)"
```

Mong đợi: pre-commit hooks xanh (R15 sẽ chặn nếu message có AI-attribution — message trên sạch).

## Self-review

1. **Phủ SPEC:** FR-001+FR-002→Task 1 · FR-003→Task 2 · FR-005→Task 3 · FR-004→Task 4 · FR-006→Task 5 · FR-007→Task 6. Đủ 7 FR, không id nào rơi (R18 grep được qua các dòng `**Thoả:**`).
2. **Quét placeholder:** các khung `<1 câu>`/`<mỗi luật...>` trong PLAN là NỘI DUNG CHỜ DISTILL có lệnh verify đi kèm (`rg -n '<1 câu'` phải exit 1 trước khi task được tính xong) — không phải placeholder bỏ ngỏ; mọi step đều có lệnh + output mong đợi.
3. **Nhất quán tên:** heading `## Bản đồ 13 nhóm lỗi (gstack) + severity` viết nguyên văn ở Task 1 (Produces) và Task 5 (anchor); hàm `export_all`/`import_file` nhất quán giữa Step 1/2/3 của Task 4; đường dẫn delta `skills/hallmark/references/frontend-design-delta.md` nhất quán Task 3 Files/Step 2/Step 3.
