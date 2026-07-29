#!/usr/bin/env bash
# ge-integration-test — bốn thay đổi T1 (ratchet) · T2 (edge ID) · T4 (grounding) · T7 (hub)
# phải NÓI CHUYỆN ĐƯỢC với nhau trên một dòng công việc thật.
#
# Lỗ nó bịt ("Ghép", 290726-ge-test-PLAN): mỗi self-test đơn vị chỉ chứng minh module của nó
# đúng trong sandbox riêng của nó. Ghép lại vẫn hỏng được theo bốn kiểu:
#   (a) ratchet đẻ commit thật nhưng hub không bắt được Trial nào;
#   (b) hub ghi ref nhưng notes thiếu môi trường ⇒ thí nghiệm cũ không tái lập được;
#   (c) DAG trả lời sai trên dữ liệu ratchet THẬT (children/leaves/log --by-metric);
#   (d) `cite` trả eid mà eid đó không resolve ngược được, hoặc cổng grounding không nhận
#       ⇒ mục Evidence của /query chỉ là trang trí.
#
# Sandbox tuyệt đối: mọi ghi đều nằm trong mktemp -d (repo git riêng + wiki riêng). Repo thật
# CHỈ được đọc — không refs/hub, không metrics, không file nào sinh ra trong đó.
set -uo pipefail

SRC="$(cd "${1:?usage: ge-integration-test.sh <repo-root>}" && pwd)"
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
W="$TMP/w"

# ── (a) ratchet đẻ commit thật + hub bắt được ─────────────────────────────────
hdr "(a) ratchet đẻ commit thật + hub bắt được"
git init -q "$W"
git -C "$W" config user.email t@t.test
git -C "$W" config user.name t
git -C "$W" config commit.gpgsign false
printf '0\n' > "$W/n"
# metric tăng mỗi lần đo → mọi vòng đều phải KEEP (dòng công việc "cải thiện đều")
cat > "$W/bump.py" <<'PY'
import pathlib
p = pathlib.Path("n"); v = int(p.read_text() or 0) + 1
p.write_text(str(v)); print(v)
PY
git -C "$W" add -A
git -C "$W" commit -qm seed
SEED=$(git -C "$W" rev-parse HEAD)

python3 "$SRC/harness/scripts/loop-runner.py" run \
  --verify 'false' --metric-cmd "python3 bump.py" --direction max \
  --max-iter 3 --hub --log "$TMP/run.json" --cwd "$W" >/dev/null 2>&1

KEPT=0; BEST_REF=; BEST_SCORE=; BEST_COMMIT=; FIRST_COMMIT=; LAST_COMMIT=
eval "$(python3 - "$TMP/run.json" <<'PY' 2>/dev/null
import json, sys
log = json.load(open(sys.argv[1]))
kept = [i for i in log["iterations"] if i.get("ratchet") == "kept"]
best = max(kept, key=lambda i: i.get("score") or 0) if kept else {}
print(f"KEPT={len(kept)}")
print(f"BEST_REF={best.get('hub_ref') or ''}")
print(f"BEST_SCORE={best.get('score') if best.get('score') is not None else ''}")
print(f"BEST_COMMIT={best.get('commit') or ''}")
print(f"FIRST_COMMIT={kept[0].get('commit') if kept else ''}")
print(f"LAST_COMMIT={(log.get('ratchet') or {}).get('last_kept_commit') or ''}")
PY
)"

[ "$KEPT" -ge 2 ] && ok "ratchet giữ $KEPT vòng cải thiện (commit thật trong sandbox)" \
                  || bad "ratchet keep" "chỉ $KEPT vòng kept"
REFS=$(git -C "$W" for-each-ref refs/hub --format='%(refname)' | wc -l | tr -d ' ')
[ "$REFS" -ge 2 ] && ok "hub bắt được $REFS Trial thành ref refs/hub/*" \
                  || bad "hub push" "chỉ $REFS ref — ratchet đẻ commit mà hub không thấy"
[ -n "$BEST_REF" ] && ok "run-log mang hub_ref của từng Trial ($BEST_REF)" \
                   || bad "hub_ref trong run-log" "không có hub_ref nào ⇒ hub chạy ngoài luồng ratchet"

# ── (b) notes mang đủ môi trường để tái lập ───────────────────────────────────
hdr "(b) notes của Trial mang đủ môi trường + đúng metric/status"
git -C "$W" notes --ref=refs/notes/hub show "${BEST_COMMIT:-HEAD}" > "$TMP/note.json" 2>/dev/null
if python3 - "$TMP/note.json" "${BEST_SCORE:-}" <<'PY' 2>"$TMP/note.err"
import json, platform, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
need = {"python", "platform", "metric", "status"}
assert need <= set(d), "thiếu field: %s" % sorted(need - set(d))
assert d["python"] == platform.python_version(), "python=%s" % d["python"]
assert d["platform"], "platform rỗng"
assert float(d["metric"]) == float(sys.argv[2]), "metric=%s, run-log=%s" % (d["metric"], sys.argv[2])
assert d["status"] == "kept", "status=%s" % d["status"]
PY
then
  ok "notes có python/platform + metric & status khớp run-log"
else
  bad "notes môi trường" "$(tail -1 "$TMP/note.err")"
fi

# ── (c) bốn truy vấn DAG trên dữ liệu ratchet THẬT ────────────────────────────
hdr "(c) truy vấn DAG đúng trên chuỗi commit do ratchet sinh"
KIDS=$(python3 "$SRC/harness/scripts/hub.py" children "$SEED" --root "$W" 2>/dev/null)
if [ -n "$FIRST_COMMIT" ] && printf '%s\n' "$KIDS" | grep -q "$FIRST_COMMIT"; then
  ok "children <seed> thấy commit đầu tiên của ratchet"
else
  bad "hub children" "con của seed không chứa commit ratchet đầu tiên ($FIRST_COMMIT)"
fi

TOP=$(python3 "$SRC/harness/scripts/hub.py" log --by-metric --root "$W" 2>/dev/null | awk 'NR==2 {print $1}')
if [ -n "$BEST_REF" ] && [ "$TOP" = "$BEST_REF" ]; then
  ok "log --by-metric: dòng đầu là Trial điểm cao nhất ($BEST_SCORE)"
else
  bad "hub log --by-metric" "dòng đầu '$TOP' ≠ ref điểm cao nhất '$BEST_REF'"
fi

LEAVES=$(python3 "$SRC/harness/scripts/hub.py" leaves --root "$W" 2>/dev/null)
if [ -n "$LAST_COMMIT" ] && [ "$LEAVES" = "$LAST_COMMIT" ]; then
  ok "leaves = đúng commit cuối chuỗi (biên chưa khám phá)"
else
  bad "hub leaves" "leaves='$LEAVES' ≠ commit kept cuối '$LAST_COMMIT'"
fi

LIN=$(python3 "$SRC/harness/scripts/hub.py" lineage "$LAST_COMMIT" --root "$W" 2>/dev/null)
if printf '%s\n' "$LIN" | head -1 | grep -q "$LAST_COMMIT" && printf '%s\n' "$LIN" | tail -1 | grep -q "$SEED"; then
  ok "lineage: con → gốc, chạm lại đúng commit seed"
else
  bad "hub lineage" "chuỗi tổ tiên không đi từ '$LAST_COMMIT' về '$SEED'"
fi

# ── (d) T2 → T4: eid từ cite phải resolve ngược VÀ đi lọt cổng grounding ──────
hdr "(d) T2 → T4: cite ra edge ID thật, eid vào thẳng cổng grounding"
mkdir -p "$TMP/wiki/concepts"
cat > "$TMP/wiki/concepts/a.md" <<'MD'
---
type: concept
relations:
  - {rel: supports, to: b}
---
# a
MD
printf '# b\n' > "$TMP/wiki/concepts/b.md"

EID=$(python3 "$SRC/harness/scripts/wiki-graph.py" cite a --wiki-dir "$TMP/wiki" 2>/dev/null | awk 'NR==1 {print $1}')
if printf '%s' "$EID" | grep -qE '^e:[0-9a-f]{8}$'; then
  ok "cite <page> trả edge ID đúng dạng ($EID)"
else
  bad "wiki-graph cite" "không ra eid hợp lệ: '$EID'"
fi

python3 "$SRC/harness/scripts/wiki-graph.py" edge "${EID:-e:none}" --wiki-dir "$TMP/wiki" \
  > "$TMP/edge.json" 2>/dev/null
if python3 - "$TMP/edge.json" <<'PY' 2>/dev/null
import json, sys
e = json.load(open(sys.argv[1], encoding="utf-8"))
assert e["from"] == "concepts/a.md" and e["to"] == "concepts/b.md" and e["type"] == "supports", e
PY
then
  ok "edge <eid> resolve NGƯỢC đúng cạnh a→b (bằng chứng thật, không phải chuỗi bất kỳ)"
else
  bad "wiki-graph edge" "eid không resolve ngược về cạnh a -supports-> b"
fi

printf '{"decision":"revise","claim":"c","reason":"r","required_evidence":["%s"]}' "$EID" > "$TMP/v-ok.json"
python3 "$SRC/harness/scripts/grounding-check.py" --check "$TMP/v-ok.json" >/dev/null 2>&1
[ $? -eq 0 ] && ok "verdict revise mang eid làm required_evidence → cổng cho qua (exit 0)" \
             || bad "grounding-check nhận eid" "verdict có eid thật vẫn bị chặn"

printf '{"decision":"revise","claim":"c","reason":"r","required_evidence":[]}' > "$TMP/v-bad.json"
python3 "$SRC/harness/scripts/grounding-check.py" --check "$TMP/v-bad.json" >/dev/null 2>&1
[ $? -eq 2 ] && ok "verdict revise KHÔNG bằng chứng → cổng chặn (exit 2)" \
             || bad "grounding-check chặn rỗng" "required_evidence rỗng vẫn lọt ⇒ chuỗi eid chỉ là trang trí"

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
