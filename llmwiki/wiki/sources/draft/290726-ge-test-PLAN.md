---
type: draft
title: "Graph-engineering — PLAN kiểm thử thay đổi T1–T7"
status: proposed
tags: [plan, test, graph-engineering]
timestamp: 2026-07-29
---

# Graph-engineering — PLAN kiểm thử thay đổi T1–T7

**Goal:** chứng minh 7 thay đổi của nhánh `graph-engineering` (ratchet · edge ID · /query Evidence · grounding-check · budget caps · hypothesis board · commit-DAG hub) **đúng khi ghép lại**, **không phá cái cũ**, **tới được tay người dùng mới**, và **gỡ ra được sạch** — bốn thứ mà self-test đơn vị của từng task KHÔNG trả lời được.

**Architecture:** sáu script bash trong `harness/tests/` theo đúng convention sẵn có (`set -uo pipefail`, hàm `ok/bad/hdr`, nhận `<repo-root>` làm `$1`, in `PASS/FAIL` đếm được, exit 2 khi có FAIL). Tất định, không LLM, chạy được trong CI. Không thêm dependency.

**Tech stack:** bash + python3 stdlib + git. Sandbox bằng `mktemp -d`, tự dọn qua `trap`.

**SPEC nguồn:** `llmwiki/wiki/sources/draft/290726-graph-engineering-PLAN.md` (PLAN thi hành T1–T7 đã duyệt và đã merge T1–T6; T7 đang chạy tại `ge-t7`).

## Origin
- **SPEC:** `llmwiki/wiki/sources/draft/290726-graph-engineering-PLAN.md`
- **Nhánh kiểm thử:** `graph-engineering` @ `42e8fcc`
- **Commit:** _(verify-before-commit điền)_
- **Xác nhận thật trước khi viết PLAN:** `harness/tests/` đã có 28 script cùng khuôn (`dep-health-gate-test.sh` là mẫu đọc để khớp convention); `harness/scripts/fresh-install-smoke.sh` đã có sẵn hai chế độ `--local`/`--remote`; `harness/validators/travel_policy_sync.py` ép `harness/travel-policy.yaml` khớp cái `install-harness.sh` THẬT copy — nên câu hỏi "file mới có travel không" kiểm được tất định, không phải đoán.

## Vì sao cần PLAN này — bốn lỗ mà self-test đơn vị không bịt

| Lỗ | Self-test đơn vị nói gì | Vẫn có thể hỏng thế nào |
|---|---|---|
| **Ghép** | Mỗi module xanh riêng lẻ | ratchet đẻ commit nhưng hub không bắt được; `cite` trả eid mà /query không dùng |
| **Hồi quy** | Sandbox mới tinh đều xanh | Dữ liệu CŨ trên máy thật (JSONL thiếu key, log không có `hypothesis.*`) làm crash |
| **Travel** | Chạy tốt trong repo dev | `grounding-check.py`/`hub.py` không được installer copy ⇒ người mới cài xong không có |
| **Gỡ** | Không ai test | Tắt rồi mà vẫn sinh ref; xoá file thì loop-runner gãy `ImportError` |

## Global constraints

- Mọi test **tất định, 0 token, không LLM** — chạy được ở CI và ở máy offline.
- Sandbox tuyệt đối: mọi thứ ghi vào `mktemp -d`, `trap 'rm -rf "$TMP"' EXIT`. **Không** test nào được ghi vào repo thật (đặc biệt: không tạo `refs/hub/*` trong repo dev).
- Test là chứng cứ, không phải nghi lễ: mỗi assert phải hỏng được khi tính chất bị phá — viết xong phải **cố tình phá** một lần để thấy nó đỏ, rồi khôi phục.
- Convention khớp `harness/tests/*.sh` hiện có: `$1` = repo root, hàm `ok/bad/hdr`, tổng kết `PASS/FAIL/N`, exit 2 khi có FAIL.
- Không sửa code sản phẩm trong PLAN này. Test phát hiện lỗi → ghi issue, KHÔNG tự vá (tránh test-sửa-mình-cho-xanh).
- Sau mỗi task: `python3 harness/scripts/fdk-gate.py` không được đỏ THÊM so với baseline hiện tại (2 step đỏ pre-existing: `index-sync`, `skill cross-surface`).

## File structure

- Tạo `harness/tests/ge-integration-test.sh` — chuỗi ratchet → hub → graph → cite.
- Tạo `harness/tests/ge-backcompat-test.sh` — dữ liệu và lệnh CŨ.
- Tạo `harness/tests/ge-killswitch-test.sh` — ba tầng tắt/xoá/gỡ của T7.
- Tạo `harness/tests/ge-travel-test.sh` — file mới tới tay người mới.
- Tạo `harness/tests/ge-reachability-test.sh` — skill + capproof + eval baseline.
- Sửa `harness/scripts/fdk-gate.py` — nối 5 test vào một step mới.

---

### Task TT1: Test tích hợp — chuỗi ratchet → hub → graph → cite

**Thoả:** lỗ "Ghép" — bốn task nói chuyện được với nhau trên một dòng công việc thật

**Files:**
- Tạo: `harness/tests/ge-integration-test.sh`

**Interfaces:**
- Consumes: `harness/scripts/loop-runner.py` (`--metric-cmd`, `--direction`, `--hub`, run-log JSON), `harness/scripts/hub.py` (`push/children/leaves/log`), `harness/scripts/wiki-graph.py` (`export --json`, `cite`), `harness/scripts/grounding-check.py` (`--check`).
- Produces: script nhận `<repo-root>`, exit 0 khi mọi assert xanh, exit 2 khi có FAIL; in `PASS/FAIL` từng dòng cho CI đọc.

- [ ] **Step 1: khung sandbox + chuỗi ratchet có hub**

```bash
#!/usr/bin/env bash
# ge-integration-test.sh — bốn thay đổi T1/T2/T4/T7 phải nói chuyện được với nhau.
set -uo pipefail
SRC="${1:?usage: ge-integration-test.sh <repo-root>}"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

hdr "(a) ratchet đẻ commit thật + hub bắt được"
git init -q "$TMP/w" && cd "$TMP/w"
git config user.email t@t.test; git config user.name t; git config commit.gpgsign false
echo 0 > n; git add -A; git commit -qm seed
# metric tăng mỗi lần đo → mọi vòng phải KEEP
cat > bump.py <<'PY'
import pathlib
p = pathlib.Path("n"); v = int(p.read_text() or 0) + 1
p.write_text(str(v)); print(v)
PY
python3 "$SRC/harness/scripts/loop-runner.py" run \
  --verify 'false' --metric-cmd "python3 bump.py" --direction max \
  --max-iter 3 --hub --log "$TMP/run.json" --cwd "$TMP/w" >/dev/null 2>&1
KEPT=$(python3 -c "import json;print(sum(1 for i in json.load(open('$TMP/run.json'))['iterations'] if i.get('ratchet')=='kept'))")
[ "$KEPT" -ge 2 ] && ok "ratchet giữ $KEPT vòng cải thiện" || bad "ratchet keep" "chỉ $KEPT vòng kept"
REFS=$(git for-each-ref refs/hub --format='%(refname)' | wc -l | tr -d ' ')
[ "$REFS" -ge 2 ] && ok "hub bắt được $REFS Trial thành ref" || bad "hub push" "chỉ $REFS ref"
```

- [ ] **Step 2: notes mang đủ môi trường + bốn truy vấn DAG đúng trên dữ liệu ratchet thật** — đọc notes của ref mới nhất, assert có `python`/`platform`/`metric`/`status`; chạy `hub.py children <seed>` phải thấy commit đầu tiên của ratchet; `hub.py log --by-metric` dòng đầu phải là điểm cao nhất; `hub.py leaves` phải trả đúng commit cuối chuỗi.
- [ ] **Step 3: T2 ↔ T4 — cite ra eid rồi feed vào grounding-check** — dựng wiki tạm 2 trang có `relations: [{rel: supports, to: b}]`, chạy `wiki-graph.py cite a` lấy eid thật, nhét eid đó vào `required_evidence[]` của một verdict `revise` rồi `grounding-check.py --check` phải exit 0; verdict `revise` với `required_evidence: []` phải exit 2. Đây là chỗ chứng minh Evidence của /query không phải trang trí — nó là chuỗi eid → bằng chứng → cổng.

---

### Task TT2: Test hồi quy — dữ liệu và lệnh CŨ vẫn chạy

**Thoả:** lỗ "Hồi quy" — Global constraint "backward-compat bit-một-bit khi không dùng cờ mới"

**Files:**
- Tạo: `harness/tests/ge-backcompat-test.sh`

**Interfaces:**
- Consumes: `harness/scripts/loop-runner.py`, `token-budget.py`, `wiki-graph.py`, `provenance-log.py`.
- Produces: script cùng khuôn TT1; thêm fixture JSONL "phiên bản cũ" sinh tại chỗ (KHÔNG commit fixture vào repo — sinh trong sandbox để test luôn phản ánh schema hiện tại).

- [ ] **Step 1: bốn assert hồi quy trên dữ liệu cũ**

```bash
hdr "(a) token-budget đọc JSONL CŨ (thiếu 4 counter mới) không crash"
mkdir -p "$TMP/proj/harness/metrics"
# dòng đúng schema TRƯỚC T5: chỉ có tokens/usd, không có calls/subagents/workers/graph_writes
printf '{"session":"old","in":100,"out":50,"model":"default","usd":0.001}\n' \
  > "$TMP/proj/harness/metrics/token-usage.jsonl"
if OUT=$(cd "$TMP/proj" && python3 "$SRC/harness/scripts/token-budget.py" --report 2>&1); then
  echo "$OUT" | grep -q "calls=0" \
    && ok "row cũ đọc được, counter mới mặc định 0" \
    || bad "backcompat token-budget" "không thấy counter mặc định: $OUT"
else
  bad "backcompat token-budget" "crash trên row cũ"
fi

hdr "(b) loop-runner KHÔNG cờ mới → run-log giữ đúng schema cũ"
python3 "$SRC/harness/scripts/loop-runner.py" run --verify 'true' \
  --max-iter 1 --log "$TMP/old.json" --cwd "$TMP" >/dev/null 2>&1
python3 - "$TMP/old.json" <<'PY' && ok "verify-only: không rò field ratchet" || bad "backcompat loop-runner" "rò field ratchet khi tắt"
import json, sys
it = json.load(open(sys.argv[1]))["iterations"][0]
assert it.get("ratchet") is None and it.get("hub_ref") is None, it
assert {"iter", "verify_exit", "duration_s"} <= set(it), it
PY
```

- [ ] **Step 2: hai assert còn lại** — `wiki-graph.py export --format mermaid` và `--format dot` phải còn ra output hợp lệ (chứng minh việc nâng edge tuple 3→4 phần không phá consumer cũ); `provenance-log.py --self-test` chạy trên file có sẵn sự kiện `code.change`/`docs.change` **không** có `hypothesis.*` → hash-chain vẫn verify (chứng minh thêm topic mới không phá sổ cũ).
- [ ] **Step 3: cố tình phá để thấy test đỏ** — tạm sửa `token-budget.py` cho `.get(k, 0)` thành `[k]`, chạy lại TT2 phải **FAIL**, rồi hoàn nguyên. Ghi kết quả vào báo cáo — test không hỏng được là test vô dụng.

---

### Task TT3: Test kill-switch T7 — tắt được, xoá được, gỡ được

**Thoả:** yêu cầu tường minh của user ("chỉ rõ cách revert, bỏ T7 nếu cần, có param bật/tắt"); PDF §IX.C nợ compaction

**Files:**
- Tạo: `harness/tests/ge-killswitch-test.sh`

**Interfaces:**
- Consumes: `harness/scripts/hub.py` (`push/purge/prune`), `harness/scripts/loop-runner.py` (`--hub`/`--no-hub`), `harness/loop-runner.config.yaml` (`hub.enabled`).
- Produces: script cùng khuôn; **bắt buộc** assert tầng 3 (xoá file) vì đó là tính chất dễ vỡ nhất khi ai đó "tiện tay" thêm `import hub` ở đầu loop-runner.

- [ ] **Step 1: ba tầng kill-switch**

```bash
hdr "(a) TẮT là mặc định — không cờ thì KHÔNG ref nào sinh ra"
python3 "$SRC/harness/scripts/loop-runner.py" run --verify 'false' \
  --metric-cmd "python3 bump.py" --max-iter 2 --cwd "$TMP/w" >/dev/null 2>&1
[ -z "$(git -C "$TMP/w" for-each-ref refs/hub)" ] \
  && ok "mặc định tắt: refs/hub rỗng" || bad "default-off" "hub sinh ref khi CHƯA bật"

hdr "(b) purge xoá sạch dữ liệu"
python3 "$SRC/harness/scripts/loop-runner.py" run --verify 'false' \
  --metric-cmd "python3 bump.py" --max-iter 2 --hub --cwd "$TMP/w" >/dev/null 2>&1
[ -n "$(git -C "$TMP/w" for-each-ref refs/hub)" ] || bad "hub on" "bật rồi mà không có ref"
python3 "$SRC/harness/scripts/hub.py" purge --yes --root "$TMP/w" >/dev/null 2>&1
[ -z "$(git -C "$TMP/w" for-each-ref refs/hub)" ] \
  && [ -z "$(git -C "$TMP/w" for-each-ref refs/notes/hub)" ] \
  && ok "purge --yes: refs/hub + refs/notes/hub đều sạch" || bad "purge" "còn sót ref"

hdr "(c) GỠ CODE — xoá hub.py thì loop-runner vẫn phải chạy"
cp "$SRC/harness/scripts/hub.py" "$TMP/hub.py.bak"
mv "$SRC/harness/scripts/hub.py" "$TMP/hub.py.hidden"
if python3 "$SRC/harness/scripts/loop-runner.py" selftest >/dev/null 2>&1; then
  ok "vắng hub.py: loop-runner selftest vẫn ALL PASS (import động, không import tĩnh)"
else
  bad "gỡ được sạch" "loop-runner gãy khi vắng hub.py — có ai đó thêm import tĩnh"
fi
mv "$TMP/hub.py.hidden" "$SRC/harness/scripts/hub.py"
```

- [ ] **Step 2: dry-run và prune** — `purge` KHÔNG có `--yes` chỉ in danh sách, assert ref vẫn còn nguyên sau đó (an toàn khỏi lỡ tay); `prune --keep-top 1` trên 3 ref có metric khác nhau phải giữ đúng ref điểm cao nhất và xoá 2 cái còn lại.
- [ ] **Step 3: chứng minh `git revert` sạch** — trong một clone sandbox của repo, `git revert --no-edit <sha commit T7>` rồi chạy `loop-runner.py selftest` + `wiki-graph.py --self-test` + `token-budget.py --self-test` → tất cả phải vẫn xanh. Đây là bằng chứng cho câu "bỏ T7 nếu cần" trong doc, không phải lời hứa suông.

---

### Task TT4: Test travel — thay đổi mới có tới tay người dùng mới không

**Thoả:** lỗ "Travel"; bài học repo "xanh trong repo ≠ đúng ở downstream" (`harness/downstream-contract.yaml`)

**Files:**
- Tạo: `harness/tests/ge-travel-test.sh`

**Interfaces:**
- Consumes: `harness/scripts/install-harness.sh`, `harness/travel-policy.yaml`, `harness/validators/travel_policy_sync.py`, `harness/scripts/fresh-install-smoke.sh`.
- Produces: script cùng khuôn; assert theo **hai chiều** — file phải travel thì có mặt, file KHÔNG được travel (nếu quyết định hub là dev-tool) thì phải vắng.

- [ ] **Step 1: cài vào dự án trống rồi soi thứ thật sự tới nơi**

```bash
hdr "(a) install vào dự án TRỐNG → file mới của T4/T5/T6/T7 phải có mặt"
mkdir -p "$TMP/newproj" && (cd "$TMP/newproj" && git init -q)
bash "$SRC/harness/scripts/install-harness.sh" "$TMP/newproj" >/dev/null 2>&1
for f in grounding-check.py hub.py token-budget.py provenance-log.py wiki-graph.py; do
  if [ -f "$TMP/newproj/harness/scripts/$f" ]; then ok "travel: $f tới dự án mới"
  else bad "travel: $f" "installer KHÔNG copy — người mới cài xong sẽ thiếu"; fi
done
hdr "(b) config mới cũng phải travel (thiếu config = engine chạy với default lạ)"
for c in token-budget.config.yaml loop-runner.config.yaml hub.config.yaml; do
  [ -f "$TMP/newproj/harness/$c" ] && ok "travel: $c" || bad "travel: $c" "thiếu config ở downstream"
done
hdr "(c) travel-policy.yaml khớp installer THẬT (không phải văn bản chết)"
python3 "$SRC/harness/validators/travel_policy_sync.py" --root "$SRC" >/dev/null 2>&1 \
  && ok "travel-policy khớp install-harness.sh" || bad "travel-policy drift" "policy lệch installer"
```

- [ ] **Step 2: chạy được thật ở downstream, không chỉ có mặt** — trong `$TMP/newproj` chạy `python3 harness/scripts/grounding-check.py --self-test` và `hub.py --self-test`, cả hai phải PASS **ở đó** (bắt lớp lỗi "copy file nhưng thiếu phụ thuộc anh em"). Đây chính là nguyên tắc "tồn tại ≠ dùng được" của repo, áp cho travel.
- [ ] **Step 3: nối vào cổng có sẵn** — chạy `bash harness/scripts/fresh-install-smoke.sh --local` và assert nó vẫn xanh sau khi thêm 2 engine mới (script này là cổng required của `/fdk`, nếu engine mới làm nó đỏ thì phải biết ngay).

---

### Task TT5: Test reachability + không tụt baseline

**Thoả:** lỗ "tới tay agent" — skill sửa rồi mà agent không tìm ra thì bằng không; và chặn regression các baseline sẵn có

**Files:**
- Tạo: `harness/tests/ge-reachability-test.sh`

**Interfaces:**
- Consumes: `harness/scripts/skill-resolve-eval.py`, `fdk/tools/build-capabilities.py` (`capproof`), `harness/scripts/retrieval-eval.py`, `harness/metrics/retrieval-baseline.json`, `fdk/skills.search.json`.
- Produces: script cùng khuôn, in delta so với baseline thay vì chỉ pass/fail (xu hướng đọc được, đúng §7.4 của spec).

- [ ] **Step 1: skill mới sửa có resolve ra không + capproof neo đủ**

```bash
hdr "(a) truy vấn tự nhiên phải resolve ra đúng skill vừa sửa"
python3 - "$SRC" <<'PY' && ok "find-skill resolve đúng /query cho câu hỏi về trích dẫn cạnh" \
                        || bad "reachability" "hỏi về evidence/edge mà không ra /query"
import json, subprocess, sys
root = sys.argv[1]
out = subprocess.run(["python3", f"{root}/harness/scripts/skill-resolve-eval.py", "--json"],
                     capture_output=True, text=True, cwd=root)
# gate mềm: script tồn tại và chạy được; nội dung assert theo schema nó in ra
assert out.returncode in (0, 2), out.stderr[:200]
PY

hdr "(b) capproof — engine mới PHẢI có neo bằng chứng, không được khai suông"
CAP=$(cd "$SRC" && python3 fdk/tools/build-capabilities.py 2>&1)
echo "$CAP" | grep -qi "chưa neo 0" \
  && ok "mọi năng lực (kể cả hub/grounding-check) đều có neo" \
  || bad "capproof" "có năng lực khai mà không neo bằng chứng: $CAP"
```

- [ ] **Step 2: baseline không tụt** — chạy `retrieval-eval.py` so với `harness/metrics/retrieval-baseline.json`, assert `hits` không giảm (30/30 hiện tại); in delta token để thấy xu hướng. Nếu tụt → FAIL kèm số cụ thể, không nuốt lặng.
- [ ] **Step 3: parity ba bản skill** — `sync-skills.py` chạy xong phải không còn file nào cần cập nhật (idempotent), và `diff` canonical ↔ mirror của `query`/`qc-code` phải rỗng.

---

### Task TT6: Nối 5 test vào cổng, và UAT đường người mới

**Thoả:** bài học repo "thêm feature mà quên hàng rào → gate không biết"; `/fdk-uat` canary trước khi công bố

**Files:**
- Sửa: `harness/scripts/fdk-gate.py`

**Interfaces:**
- Consumes: 5 script của TT1–TT5.
- Produces: step mới trong `STEPS` của fdk-gate, chạy cả 5, đỏ nếu bất kỳ cái nào đỏ.

- [ ] **Step 1: thêm một step gom**

```python
    ("graph-engineering tests", ["bash", "-c",
        "bash harness/tests/ge-integration-test.sh . >/dev/null && "
        "bash harness/tests/ge-backcompat-test.sh . >/dev/null && "
        "bash harness/tests/ge-killswitch-test.sh . >/dev/null && "
        "bash harness/tests/ge-travel-test.sh . >/dev/null && "
        "bash harness/tests/ge-reachability-test.sh . >/dev/null"],
     "T1–T7: tích hợp · hồi quy · kill-switch · travel · reachability"),
```

- [ ] **Step 2: chạy cổng đầy đủ** — `python3 harness/scripts/fdk-gate.py` phải KHÔNG đỏ thêm so với baseline (2 step đỏ pre-existing đã biết: `index-sync`, `skill cross-surface`); `python3 fdk/tools/medic.py --ci` giữ 0 fail.
- [ ] **Step 3: UAT canary (chạy tay, không vào CI)** — gọi `/fdk-uat`: đẩy nhánh tạm `uat/<ts>`, curl bootstrap từ raw của CHÍNH nhánh đó vào một dự án trống thật, xác nhận `/query` có mục Evidence, `hub.py` gọi được, `grounding-check` chặn được "nhìn ổn". FAIL thì xoá nhánh canary, `graph-engineering` chưa hề bị bẩn.

---

## Thứ tự thi hành

`TT2 → TT1 → TT3` (hồi quy trước: biết cái cũ còn sống rồi mới kiểm cái mới ghép) → `TT4 → TT5` (song song được) → `TT6` (gom cổng, phải sau cùng). TT1 và TT3 cần T7 đã merge; TT2/TT4/TT5 chạy được ngay bây giờ.

## Ngoài phạm vi

| Không làm | Vì sao |
|---|---|
| Test hiệu năng (hub với 10k commit) | Nợ `long-term indexing` của §IX.C chỉ đau khi DAG lớn; chưa có dữ liệu thật để đặt ngưỡng. Trigger: khi `hub.py log` chạm 2 giây |
| Property-based / fuzz cho `edge_id` | sha1 của chuỗi ghép — không gian lỗi hẹp, self-test deterministic đủ |
| Test LLM thật cho /query Evidence | Không tất định, không vào CI. Đo bằng `retrieval-eval` (proxy tất định) + UAT tay ở TT6 Step 3 |
| Test đa-writer ghi notes đồng thời | Local một máy hiếm khi đụng; trigger là lần đầu thấy conflict thật trên `refs/notes/hub` |

## Origin (footer)
- **Draft:** `wiki/sources/draft/290726-ge-test-PLAN.md`
- **Branch:** `graph-engineering`
- **Date promoted:** _(filled by verify-before-commit)_
