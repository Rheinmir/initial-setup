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

### Task TT7: Acceptance — chấm lại bài nghiệm thu §X của PDF

**Thoả:** thước đo cuối của PDF §X — *"Every important output can be traced to an objective, a plan, an artifact, a source, a graph path, an evaluator decision, and a bounded execution record"*. Trước T1–T7 overstack đạt **5/7**, đứt ở `graph path` (không edge ID) và nửa `evaluator decision` (rubric theo suite, không theo output). Task này đo lại bằng lệnh thật, không bằng cảm tính.

**Vì sao tách khỏi TT1:** TT1 hỏi *"các module có nói chuyện được với nhau không"*. TT7 hỏi *"một auditor lạ có truy được toàn bộ chuỗi từ một output ngẫu nhiên không"* — câu hỏi của người dùng cuối, không phải của lập trình viên. Một hệ có thể xanh hết integration mà vẫn trượt §X.

**Files:**
- Tạo: `harness/tests/ge-acceptance-test.sh`

**Interfaces:**
- Consumes: `harness/scripts/wiki-graph.py` (`cite`), `hub.py` (`lineage`, `log`), `grounding-check.py`, `provenance-log.py` (`read-events`), `harness/metrics/*.json`, một trang wiki thật làm mẫu.
- Produces: script in **bảng chấm 7 mắt xích** (`✓`/`✗` + lệnh chứng minh cho từng mắt xích) và exit 2 nếu điểm **thấp hơn** ngưỡng khai trong script (`EXPECT_LINKS=6`) — tức là hồi quy traceability bị chặn, không chỉ được ghi nhận.

- [ ] **Step 1: chấm 7 mắt xích bằng lệnh thật**

```bash
hdr "§X — truy vết một output qua 7 mắt xích"
SCORE=0
link() {  # link <tên> <lệnh chứng minh>
  if eval "$2" >/dev/null 2>&1; then SCORE=$((SCORE+1)); ok "$1"; else bad "$1" "không truy được: $2"; fi
}
PAGE="concepts/commit-dag-hub.md"
link "1. objective — SPEC gốc tồn tại"        "test -f llmwiki/wiki/sources/draft/290726-graph-engineering-PLAN.md"
link "2. plan step — PLAN có task tương ứng"  "grep -q '### Task 7' llmwiki/wiki/sources/draft/290726-graph-engineering-PLAN.md"
link "3. artifact version — commit tạo file"  "git log --oneline --diff-filter=A -- harness/scripts/hub.py | grep -q ."
link "4. source — trang wiki có ## Origin"    "grep -q '^## Origin' llmwiki/wiki/$PAGE"
link "5. graph path — cite ra edge ID"        "python3 harness/scripts/wiki-graph.py cite ${PAGE%.md} | grep -qE '^e:[0-9a-f]{8}'"
link "6. evaluator — verdict có rubric-schema" "echo '{\"decision\":\"approve\",\"claim\":\"c\",\"reason\":\"r\"}' | python3 harness/scripts/grounding-check.py --check -"
link "7. execution record — chi phí/độ trễ"   "test -s harness/metrics/cost-by-session.json"
printf '\n  §X SCORE: %d/7  (ngưỡng chặn hồi quy: %d)\n' "$SCORE" "${EXPECT_LINKS:-6}"
[ "$SCORE" -ge "${EXPECT_LINKS:-6}" ] || bad "§X acceptance" "tụt xuống $SCORE/7"
```

- [ ] **Step 2: mắt xích 5 phải là đường THẬT, không phải chuỗi bất kỳ** — lấy eid từ `cite`, feed ngược vào `wiki-graph.py edge <eid>` và assert `from`/`to` khớp đúng trang đang xét. Một eid trả về mà không resolve ngược được thì mắt xích 5 là giả — đây chính là lỗi "fluent answers citing irrelevant edges" mà PDF §VII.3 cảnh báo.
- [ ] **Step 3: ghi điểm vào metrics để theo XU HƯỚNG** — append `{"ts", "score", "expect"}` vào `harness/metrics/acceptance-x.jsonl` (fail-open). PDF §7.4: theo dõi xu hướng chứ không phải điểm đơn lẻ; lần sau tụt điểm sẽ thấy ngay thay vì phát hiện muộn.

---

### Task TT8: Test MỤC ĐÍCH — từng thay đổi có làm đúng việc nó sinh ra để làm không

**Thoả:** khoảng cách giữa *"chạy đúng như viết"* và *"đạt mục đích"*. Self-test hiện tại chứng minh vế đầu. Task này tấn công vế sau bằng ca đối kháng — thứ PDF §VII.2 gọi là adversarial case và xếp ngang hàng gold set.

**Files:**
- Tạo: `harness/tests/ge-purpose-test.sh`

**Interfaces:**
- Consumes: cả 6 engine của T1–T7.
- Produces: script cùng khuôn; mỗi assert gắn với **một câu mục đích** viết thành lời, để khi đỏ thì biết *mục đích nào* vỡ chứ không chỉ *hàm nào* lỗi.

- [ ] **Step 1: ratchet phải GIỮ ĐƯỢC CÁI TỐT NHẤT, không phải cái cuối cùng**

```bash
hdr "T1 mục đích: 'giữ cái tốt hơn, vứt cái tệ hơn' — thử với metric NHIỄU"
# điểm đi theo dãy 5 → 9 → 3 → 4: đỉnh nằm ở GIỮA, không phải cuối.
cat > noisy.py <<'PY'
import pathlib
p = pathlib.Path("i"); i = int(p.read_text() or 0); p.write_text(str(i + 1))
print([5, 9, 3, 4][i % 4])
PY
python3 "$SRC/harness/scripts/loop-runner.py" run --verify 'false' \
  --metric-cmd "python3 noisy.py" --direction max --max-iter 4 \
  --log "$TMP/noisy.json" --cwd "$TMP/w" >/dev/null 2>&1
BEST=$(python3 -c "
import json; its=json.load(open('$TMP/noisy.json'))['iterations']
kept=[i for i in its if i.get('ratchet')=='kept']
print(max((i.get('score') or 0) for i in kept) if kept else -1)")
[ "$BEST" = "9.0" ] || [ "$BEST" = "9" ] \
  && ok "đỉnh 9 được giữ, hai vòng tệ sau đó bị revert (không trôi theo cái cuối)" \
  || bad "T1 mục đích" "kept cao nhất = $BEST, đáng lẽ 9"
```

- [ ] **Step 2: bốn mục đích còn lại, mỗi cái một ca đối kháng**

```bash
hdr "T7 mục đích: 'thất bại vẫn tra cứu được' — sống sót qua git gc"
python3 "$SRC/harness/scripts/hub.py" push --agent x --hypothesis "ý bỏ đi" \
  --metric 0.1 --status discarded --root "$TMP/w" >/dev/null
git -C "$TMP/w" reset -q --hard HEAD~1                  # commit rời khỏi mọi nhánh
git -C "$TMP/w" gc --prune=now --quiet 2>/dev/null       # gc thật, không nương tay
REF=$(git -C "$TMP/w" for-each-ref refs/hub --format='%(objectname)' | head -1)
git -C "$TMP/w" cat-file -e "$REF" 2>/dev/null \
  && ok "commit đã bỏ VẪN sống sau gc — ref giữ object, thất bại tra cứu được" \
  || bad "T7 mục đích" "gc nuốt mất thí nghiệm đã bỏ ⇒ hub không giữ được lineage"

hdr "T4 mục đích: 'nhìn ổn là schema-invalid' — thử các biến thể lách"
for v in '"LGTM"' \
         '{"decision":"approve","claim":"  ","reason":"r"}' \
         '{"decision":"revise","claim":"c","reason":"r","required_evidence":["  "]}' \
         '{"decision":"ok","claim":"c","reason":"r"}'; do
  echo "$v" | python3 "$SRC/harness/scripts/grounding-check.py" --check - >/dev/null 2>&1
  [ $? -eq 2 ] && ok "chặn được: $v" || bad "T4 mục đích" "lọt biến thể lách: $v"
done

hdr "T2 mục đích: 'trích dẫn được' — eid phải ỔN ĐỊNH qua các lần dựng lại"
A=$(python3 "$SRC/harness/scripts/wiki-graph.py" export --json | python3 -c "import json,sys;print(json.load(sys.stdin)['edges'][0]['eid'])")
B=$(python3 "$SRC/harness/scripts/wiki-graph.py" export --json | python3 -c "import json,sys;print(json.load(sys.stdin)['edges'][0]['eid'])")
[ "$A" = "$B" ] && ok "eid ổn định giữa 2 lần build ($A)" \
                || bad "T2 mục đích" "eid đổi giữa 2 lần build ⇒ trích dẫn vô nghĩa"
```

- [ ] **Step 3: T5 và T6** — T5 mục đích *"trần phải CHẶN được, không chỉ cảnh báo"*: dựng config `mode: block`, record vượt trần, `check <session>` phải **exit 2** (mode `warn` thì exit 0 — chứng minh công tắc thật sự có hiệu lực). T6 mục đích *"agent sau học được từ việc agent trước đã bỏ"*: post 3 hypothesis từ 2 writer khác nhau, rồi đọc lại bằng `read-hypotheses --discarded-only` từ một tiến trình riêng — phải thấy đủ, đúng thứ tự mới-trước, kèm `ref`. Đây là kiểm chứng cho chính lý do T6 tồn tại (PDF §III.E: học từ thí nghiệm hỏng mà không chép transcript).

---

### Task TT6: Nối 7 test vào cổng, và UAT đường người mới

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
        "bash harness/tests/ge-reachability-test.sh . >/dev/null && "
        "bash harness/tests/ge-acceptance-test.sh . >/dev/null && "
        "bash harness/tests/ge-purpose-test.sh . >/dev/null"],
     "T1–T7: tích hợp · hồi quy · kill-switch · travel · reachability · §X acceptance · mục đích"),
```

- [ ] **Step 2: chạy cổng đầy đủ** — `python3 harness/scripts/fdk-gate.py` phải KHÔNG đỏ thêm so với baseline (2 step đỏ pre-existing đã biết: `index-sync`, `skill cross-surface`); `python3 fdk/tools/medic.py --ci` giữ 0 fail.
- [ ] **Step 3: UAT canary (chạy tay, không vào CI)** — gọi `/fdk-uat`: đẩy nhánh tạm `uat/<ts>`, curl bootstrap từ raw của CHÍNH nhánh đó vào một dự án trống thật, xác nhận `/query` có mục Evidence, `hub.py` gọi được, `grounding-check` chặn được "nhìn ổn". FAIL thì xoá nhánh canary, `graph-engineering` chưa hề bị bẩn.

---

## Thứ tự thi hành

`TT2 → TT1 → TT3 → TT8` (hồi quy trước, rồi ghép, rồi kill-switch, rồi mục đích) → `TT4 ∥ TT5 ∥ TT7` (độc lập) → `TT6` (gom cổng, phải sau cùng). Tất cả 7 task đầu chạy được ngay vì T1–T7 đã merge.

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
