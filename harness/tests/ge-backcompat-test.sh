#!/usr/bin/env bash
# ge-backcompat-test.sh — dữ liệu và lệnh CŨ vẫn chạy sau T1–T7.
#
# Bối cảnh: self-test đơn vị của từng engine chạy trên sandbox MỚI TINH nên luôn xanh.
# Máy thật thì có JSONL ghi từ trước khi T5 thêm 4 counter, sổ provenance ghi từ trước khi
# T6 thêm topic hypothesis.*, và consumer đọc mermaid/dot từ trước khi T2 nâng edge tuple
# 3→4 phần. Lớp lỗi này chỉ lộ ra khi cho code MỚI đọc dữ liệu CŨ.
#
# Khoá 4 bất biến:
#   (a) token-budget đọc row JSONL thiếu counter mới → counter mặc định 0, không crash,
#       không bao giờ tự vượt trần;
#   (b) loop-runner KHÔNG cờ mới (và với config CŨ không có mục ratchet/hub) → run-log giữ
#       đúng bộ khoá cũ, không rò field ratchet/hub_ref;
#   (c) export mermaid/dot còn nguyên và KHÔNG mất cạnh nào so với export json (chứng minh
#       việc nâng edge tuple lên 4 phần không phá consumer cũ);
#   (d) sổ provenance chỉ có code.change/docs.change (không hypothesis.*) vẫn đọc được, và
#       khi ghi thêm một sự kiện hypothesis.* thì dòng cũ KHÔNG đổi một byte, hash-chain của
#       writer vẫn liền mạch.
#
# Tất định, 0 token, không LLM. Mọi thứ ghi vào mktemp -d; repo thật chỉ được ĐỌC.
set -uo pipefail

SRC="${1:?usage: ge-backcompat-test.sh <repo-root>}"
cd "$SRC"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

hdr "(a) token-budget đọc JSONL CŨ (thiếu 4 counter của T5) không crash"
mkdir -p "$TMP/proj/harness/metrics"
# Row đúng schema TRƯỚC T5: chỉ session/in/out/model/task — không calls/subagents/workers/graph_writes.
# Đường dẫn thật là harness/metrics/tokens.jsonl (PLAN ghi nhầm 'token-usage.jsonl').
printf '{"session":"old","in":100,"out":50,"model":"default","task":""}\n' \
  > "$TMP/proj/harness/metrics/tokens.jsonl"
if OUT=$(python3 "$SRC/harness/scripts/token-budget.py" --root "$TMP/proj" --report 2>&1); then
  echo "$OUT" | grep -q "calls=0 subagents=0 workers=0 graph_writes=0" \
    && ok "row cũ đọc được, 4 counter mới mặc định 0" \
    || bad "backcompat token-budget --report" "không thấy counter mặc định: $OUT"
  echo "$OUT" | grep -q "in=100" \
    && ok "số liệu cũ (in=100) không bị nuốt" \
    || bad "backcompat token-budget --report" "mất số liệu row cũ: $OUT"
else
  bad "backcompat token-budget --report" "crash trên row cũ: $OUT"
fi

# Trần counter mới không được kích hoạt bởi row cũ (thiếu khoá = 0, không phải 'vượt').
python3 "$SRC/harness/scripts/token-budget.py" --root "$TMP/proj" check old >/dev/null 2>&1
[ $? -eq 0 ] && ok "check trên session toàn row cũ: exit 0 (không báo vượt trần ma)" \
             || bad "backcompat token-budget check" "row cũ bị tính là vượt trần"

# Row CŨ và row MỚI (có counter) sống chung trong một file: tổng phải cộng đúng cả hai.
python3 "$SRC/harness/scripts/token-budget.py" --root "$TMP/proj" record old \
  --in 10 --out 5 --calls 2 >/dev/null 2>&1
OUT2=$(python3 "$SRC/harness/scripts/token-budget.py" --root "$TMP/proj" --report 2>&1)
echo "$OUT2" | grep -q "in=110" && echo "$OUT2" | grep -q "calls=2" \
  && ok "row cũ + row mới cùng file: in=110, calls=2 (cộng đúng, không loại row cũ)" \
  || bad "backcompat trộn row cũ/mới" "tổng sai: $OUT2"

hdr "(b) loop-runner KHÔNG cờ mới → run-log giữ đúng schema cũ"
python3 "$SRC/harness/scripts/loop-runner.py" run --verify 'true' \
  --max-iter 1 --log "$TMP/old.json" --cwd "$TMP/proj" >/dev/null 2>&1
python3 - "$TMP/old.json" <<'PY' && ok "verify-only: bộ khoá run-log y hệt trước T1/T7" \
                                   || bad "backcompat loop-runner" "run-log rò field mới khi không bật cờ"
import json, sys
OLD_TOP = {"tool", "verdict", "reason", "iterations_run", "verify_cmd", "revise_cmd",
           "guards", "state_paths", "started_at", "ended_at", "elapsed_s", "iterations"}
log = json.load(open(sys.argv[1]))
assert set(log) == OLD_TOP, sorted(set(log) ^ OLD_TOP)
it = log["iterations"][0]
assert {"iter", "verify_exit", "duration_s"} <= set(it), it
for k in ("ratchet", "score", "commit", "hub_ref"):
    assert k not in it, f"rò field {k}"
PY

# Config CŨ (chưa có mục ratchet:/hub: mà T1/T7 thêm) vẫn nạp được và vẫn ra schema cũ.
# Sinh từ CHÍNH config thật rồi cắt hai mục mới — KHÔNG chép tay hằng số guard sang đây:
# chép tay là rò giá trị quarantine ra khỏi adapter (adapt-registry leak-gate cắn), và làm
# test lệch khi ai đó chỉnh guard trong config thật.
python3 - "$SRC/harness/loop-runner.config.yaml" "$TMP/old-config.yaml" <<'PY'
import re, sys
src, dst = sys.argv[1], sys.argv[2]
out, skip = [], False
for line in open(src, encoding="utf-8"):
    if re.match(r"^(ratchet|hub):", line):        # mục do T1/T7 thêm → bản "cũ" không có
        skip = True
        continue
    if skip and re.match(r"^\S", line):           # hết khối thụt lề = hết mục cần cắt
        skip = False
    if not skip:
        out.append(line)
open(dst, "w", encoding="utf-8").write("".join(out))
PY
python3 "$SRC/harness/scripts/loop-runner.py" run --verify 'true' \
  --config "$TMP/old-config.yaml" --log "$TMP/oldcfg.json" --cwd "$TMP/proj" >/dev/null 2>&1
python3 - "$TMP/oldcfg.json" <<'PY' && ok "config cũ (không mục ratchet/hub): chạy được, không field mới" \
                                    || bad "backcompat config cũ" "config thiếu mục mới làm lệch run-log"
import json, sys
log = json.load(open(sys.argv[1]))
assert "ratchet" not in log and "hub" not in log, sorted(log)
assert log["verdict"] == "SUCCESS", log["verdict"]
PY

# ĐỐI CHỨNG DƯƠNG: bật cờ mới thì field mới PHẢI xuất hiện — nếu không, hai assert trên
# chỉ đang xanh vì cái detector đã mù, chứ không vì tính chất được giữ.
git init -q "$TMP/w"
git -C "$TMP/w" config user.email t@t.test
git -C "$TMP/w" config user.name t
git -C "$TMP/w" config commit.gpgsign false
printf '0\n' > "$TMP/w/n"
cat > "$TMP/w/bump.py" <<'PY'
import pathlib
p = pathlib.Path("n"); v = int(p.read_text().strip() or 0) + 1
p.write_text(str(v)); print(v)
PY
git -C "$TMP/w" add -A >/dev/null 2>&1
git -C "$TMP/w" commit -qm seed >/dev/null 2>&1
python3 "$SRC/harness/scripts/loop-runner.py" run --verify 'false' \
  --metric-cmd "python3 bump.py" --direction max --max-iter 2 --no-hub \
  --log "$TMP/new.json" --cwd "$TMP/w" >/dev/null 2>&1
python3 - "$TMP/new.json" <<'PY' && ok "đối chứng: bật --metric-cmd thì field ratchet CÓ (detector không mù)" \
                                  || bad "đối chứng dương" "bật cờ mới mà run-log vẫn không có field ratchet"
import json, sys
log = json.load(open(sys.argv[1]))
assert "ratchet" in log, sorted(log)
assert any(i.get("ratchet") for i in log["iterations"]), log["iterations"]
PY

hdr "(c) export mermaid/dot cũ không mất cạnh sau khi edge tuple lên 4 phần"
mkdir -p "$TMP/wiki/concepts"
printf '# A\n\nxem [[b]]\n' > "$TMP/wiki/concepts/a.md"
printf -- '---\ntype: concept\nrelations:\n  - {rel: supports, to: a}\n---\n\n# B\n\nxem [[a]]\n' \
  > "$TMP/wiki/concepts/b.md"
python3 "$SRC/harness/scripts/wiki-graph.py" export --format mermaid --wiki-dir "$TMP/wiki" > "$TMP/g.mmd" 2>&1
python3 "$SRC/harness/scripts/wiki-graph.py" export --format dot --wiki-dir "$TMP/wiki" > "$TMP/g.dot" 2>&1
python3 "$SRC/harness/scripts/wiki-graph.py" export --json --wiki-dir "$TMP/wiki" > "$TMP/g.json" 2>&1
head -1 "$TMP/g.mmd" | grep -q '^flowchart LR$' \
  && ok "mermaid còn đúng header 'flowchart LR'" || bad "export mermaid" "header đổi: $(head -1 "$TMP/g.mmd")"
head -1 "$TMP/g.dot" | grep -q '^digraph wiki {$' \
  && tail -1 "$TMP/g.dot" | grep -q '^}$' \
  && ok "dot còn đúng khung 'digraph wiki { … }'" || bad "export dot" "khung dot hỏng"
python3 - "$TMP/g.json" "$TMP/g.mmd" "$TMP/g.dot" <<'PY' && ok "mermaid/dot đủ đúng số cạnh của export json (không rơi cạnh typed)" \
                                                        || bad "export cũ mất cạnh" "số mũi tên lệch số cạnh json"
import json, sys
edges = json.load(open(sys.argv[1]))["edges"]
assert edges, "đồ thị mẫu không có cạnh nào — fixture hỏng"
mmd = [l for l in open(sys.argv[2]).read().splitlines() if "-->" in l or "-.->" in l]
dot = [l for l in open(sys.argv[3]).read().splitlines() if "->" in l]
assert len(mmd) == len(edges), f"mermaid {len(mmd)} != json {len(edges)}"
assert len(dot) == len(edges), f"dot {len(dot)} != json {len(edges)}"
PY

hdr "(d) sổ provenance CŨ (chưa từng có hypothesis.*) vẫn đọc và ghi tiếp được"
export PROVENANCE_VENDOR=ge-tt2
export CLAUDE_CODE_SESSION_ID=backcompat-old
mkdir -p "$TMP/prov"
# Dựng sổ theo ĐÚNG thuật toán hash-chain, nhưng bằng code ĐỘC LẬP (không import
# provenance-log) — nếu code sản phẩm đổi cách băm thì assert dưới phải đỏ.
python3 - "$TMP/prov" <<'PY'
import hashlib, json, os, socket, sys
root = sys.argv[1]
wid = f"{os.environ['PROVENANCE_VENDOR']}::{os.environ['CLAUDE_CODE_SESSION_ID']}::{socket.gethostname()}"
canon = lambda b: json.dumps(b, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
chash = lambda prev, b: hashlib.sha256((str(prev) + "\n" + canon(b)).encode("utf-8")).hexdigest()
os.makedirs(os.path.join(root, "harness", "metrics"), exist_ok=True)
prev, rows = "genesis", []
for topic, path, ts in [("code.change", "harness/scripts/foo.py", "2026-07-01T00:00:00Z"),
                        ("docs.change", "llmwiki/wiki/concepts/bar.md", "2026-07-01T00:01:00Z"),
                        ("code.change", "harness/scripts/baz.py", "2026-07-01T00:02:00Z")]:
    rec = {"writer_id": wid, "topic": topic, "ts_utc": ts, "git_sha": "unknown", "path": path}
    rec["prev"] = prev
    rec["h"] = chash(prev, rec)
    prev = rec["h"]
    rows.append(rec)
with open(os.path.join(root, "harness", "metrics", "provenance-log.jsonl"), "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
PY
cp "$TMP/prov/harness/metrics/provenance-log.jsonl" "$TMP/prov-before.jsonl"

READ=$(python3 "$SRC/harness/scripts/provenance-log.py" read-hypotheses --root "$TMP/prov" 2>&1)
RC=$?
[ "$RC" -eq 0 ] && [ -z "$READ" ] \
  && ok "sổ cũ không có hypothesis.*: read-hypotheses trả rỗng, exit 0 (không crash, không bịa)" \
  || bad "read sổ cũ" "rc=$RC out=$READ"

python3 "$SRC/harness/scripts/provenance-log.py" post-hypothesis \
  --text "ý cũ bỏ đi" --discarded --ref "llmwiki/wiki/draft/x.md" --root "$TMP/prov" >/dev/null 2>&1
python3 - "$TMP/prov/harness/metrics/provenance-log.jsonl" "$TMP/prov-before.jsonl" <<'PY' \
  && ok "ghi topic hypothesis.*: 3 dòng cũ nguyên byte, hash-chain writer vẫn liền mạch" \
  || bad "sổ cũ vỡ khi ghi topic mới" "dòng cũ bị sửa hoặc chain đứt"
import hashlib, json, sys
new_b = open(sys.argv[1], "rb").read()
old_b = open(sys.argv[2], "rb").read()
assert new_b.startswith(old_b), "dòng cũ bị viết lại/đổi thứ tự"
canon = lambda b: json.dumps(b, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
chash = lambda prev, b: hashlib.sha256((str(prev) + "\n" + canon(b)).encode("utf-8")).hexdigest()
recs = [json.loads(l) for l in new_b.decode("utf-8").splitlines() if l.strip()]
assert len(recs) == 4, f"đáng lẽ 3 dòng cũ + 1 dòng mới, có {len(recs)}"
assert recs[-1]["topic"] == "hypothesis.discarded", recs[-1]["topic"]
wid = recs[0]["writer_id"]
assert recs[-1]["writer_id"] == wid, "writer_id lệch — fixture không mô phỏng đúng writer"
prev = "genesis"
for r in [x for x in recs if x["writer_id"] == wid]:
    body = {k: v for k, v in r.items() if k != "h"}
    assert r["prev"] == prev, f"prev đứt tại {r['topic']}"
    assert chash(r["prev"], body) == r["h"], f"hash sai tại {r['topic']}"
    prev = r["h"]
PY

READ2=$(python3 "$SRC/harness/scripts/provenance-log.py" read-hypotheses --discarded-only --root "$TMP/prov" 2>&1)
[ "$(printf '%s\n' "$READ2" | grep -c 'ý cũ bỏ đi')" = "1" ] \
  && ok "đọc lại đúng 1 giả thuyết đã bỏ trên sổ vốn không có topic đó" \
  || bad "read-hypotheses sau khi ghi" "không đọc được dòng vừa ghi: $READ2"

if python3 "$SRC/harness/scripts/provenance-log.py" --self-test >/dev/null 2>&1; then
  ok "provenance-log --self-test ALL PASS (bất biến nội bộ của sổ còn nguyên)"
else
  bad "provenance-log --self-test" "self-test đỏ"
fi

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
