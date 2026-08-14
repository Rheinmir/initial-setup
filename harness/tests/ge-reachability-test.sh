#!/usr/bin/env bash
# ge-reachability-test — TT5: "tới tay agent" + "không tụt baseline".
#
# Bối cảnh: T1–T7 sửa engine VÀ sửa skill. Một skill sửa xong mà router không tìm ra
# thì năng lực mới bằng không — agent vẫn gọi đúng skill cũ và không bao giờ chạm tới
# bước mới. Đó là lớp lỗi mà self-test đơn vị của từng engine KHÔNG thấy được.
#
# Khoá 5 bất biến:
#   (a) bộ golden router hiện có KHÔNG tụt (chạy chính engine BM25, không mô phỏng);
#   (b) năng lực MỚI phải lên BỀ MẶT router (frontmatter name/description + "## Trigger
#       phrases") — đó là ĐÚNG ba trường build-skill-search.py lập chỉ mục; nằm trong
#       thân bài SKILL.md là vô hình với router;
#   (c) engine mới phải có NEO bằng chứng (capproof), không được khai suông;
#   (d) baseline truy hồi không tụt coverage và không bị hạ lặng lẽ;
#   (e) ba bề mặt phát hành skill (canonical · mirror · chỉ mục search) khớp nhau.
#
# READ-ONLY với repo thật: chỉ chạy các cờ --check/--self-test/--capproof-json (không ghi),
# mọi thứ sinh ra đều nằm trong mktemp -d và bị trap dọn.
set -uo pipefail

# __pycache__ ĐƯỢC track trong repo này, mà test nạp engine bằng importlib → python sẽ
# ghi đè .pyc và làm bẩn cây làm việc. Tắt bytecode để test không để lại dấu vết nào.
export PYTHONDONTWRITEBYTECODE=1

SRC="$(cd "${1:?usage: ge-reachability-test.sh <repo-root>}" && pwd)"
cd "$SRC"
PASS=0; FAIL=0; N=0
ok()   { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad()  { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr()  { printf '\n\033[1m── %s\033[0m\n' "$1"; }
note() { printf '        \033[2m%s\033[0m\n' "$1"; }   # delta/xu hướng — không phải assert
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

# ─────────────────────────────────────────────────────────────────────────────
hdr "(a) bộ golden router hiện có KHÔNG tụt"

if python3 "$SRC/harness/scripts/skill-resolve-eval.py" --self-test >/dev/null 2>&1; then
  ok "skill-resolve-eval --self-test xanh (mọi expected là skill THẬT trên đĩa)"
else
  bad "skill-resolve self-test" "đỏ — golden trỏ skill không tồn tại hoặc engine không nạp được"
fi

python3 "$SRC/harness/scripts/skill-resolve-eval.py" --check >/dev/null 2>&1
RC=$?
[ "$RC" -eq 0 ] \
  && ok "skill-resolve-eval --check: không hồi quy so baseline" \
  || bad "skill-resolve --check" "rc=$RC — router tụt so với baseline đã chốt"

# delta SỐ, không chỉ pass/fail (§7.4: theo xu hướng)
DELTA=$(python3 - "$SRC" <<'PY' 2>/dev/null
import importlib.util, json, sys
from pathlib import Path
root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("sre", root / "harness/scripts/skill-resolve-eval.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
res = mod.run(3)
base = json.loads((root / "llmwiki/wiki/sources/evals/skill-resolve/baseline.json").read_text(encoding="utf-8"))
c, b = res["totals"], base["totals"]
print("hit@1 %d/%d (baseline %d/%d, delta %+d) · hit@3 %d/%d (baseline %d/%d, delta %+d)"
      % (c["hit1"], c["n"], b["hit1"], b["n"], c["hit1"] - b["hit1"],
         c["hit3"], c["n"], b["hit3"], b["n"], c["hit3"] - b["hit3"]))
PY
)
note "${DELTA:-(không đọc được delta)}"

# ─────────────────────────────────────────────────────────────────────────────
hdr "(b) năng lực MỚI của T2/T4 có lên BỀ MẶT router không"

# Thân bài có bước Evidence — chứng minh thay đổi T2 đã đáp xuống skill (nếu assert này
# đỏ thì (b2)/(b3) dưới đây vô nghĩa, không phải lỗi reachability).
grep -q 'wiki-graph\.py cite' "$SRC/skills/query/SKILL.md" \
  && ok "skills/query/SKILL.md có bước Evidence (cite cạnh) — thay đổi T2 đã đáp xuống" \
  || bad "T2 landed" "không thấy bước 'wiki-graph.py cite' trong skills/query/SKILL.md"

# Bề mặt router = ĐÚNG ba trường mà build-skill-search.py lập chỉ mục. Dùng chính hàm
# parse_frontmatter/trigger_section/tokenize của engine để test không drift khỏi router.
surface_has() {   # surface_has <skill> <kw1,kw2,...>
  python3 - "$SRC" "$1" "$2" <<'PY'
import importlib.util, sys
from pathlib import Path
root, skill, kws = Path(sys.argv[1]), sys.argv[2], set(sys.argv[3].split(","))
spec = importlib.util.spec_from_file_location("bss", root / "fdk/tools/build-skill-search.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
text = (root / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
fm = m.parse_frontmatter(text)
surface = " ".join([fm.get("name", ""), fm.get("description", ""), m.trigger_section(text)])
on_surface = sorted(set(m.tokenize(surface)) & kws)
in_body = sorted(set(m.tokenize(text)) & kws)
print("surface=%s body=%s" % (",".join(on_surface) or "-", ",".join(in_body) or "-"))
sys.exit(0 if on_surface else 1)
PY
}

Q_KW="evidence,cite,citation,eid,edge,cạnh,trích"
OUT=$(surface_has query "$Q_KW"); RC=$?
[ "$RC" -eq 0 ] \
  && ok "query: năng lực Evidence có trên bề mặt router ($OUT)" \
  || bad "query reachability" "năng lực Evidence CHỈ nằm trong thân bài, router mù ($OUT)"

C_KW="verdict,grounding,schema"
OUT=$(surface_has qc-code "$C_KW"); RC=$?
[ "$RC" -eq 0 ] \
  && ok "qc-code: năng lực verdict/grounding có trên bề mặt router ($OUT)" \
  || bad "qc-code reachability" "năng lực verdict CHỈ nằm trong thân bài, router mù ($OUT)"

# Engine THẬT: hỏi đúng năng lực mới, skill vừa sửa phải lọt top-3.
resolve_top3() {  # resolve_top3 <query> <skill-mong-doi>
  python3 - "$SRC" "$1" "$2" <<'PY'
import importlib.util, sys
from pathlib import Path
root, q, want = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
spec = importlib.util.spec_from_file_location("bss", root / "fdk/tools/build-skill-search.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
hits = m.score_query(m.build_index(str(root / "skills")), q, 3)
print("top3=" + ", ".join("%s(%.1f)" % (n, s) for n, s, _ in hits) or "top3=-")
sys.exit(0 if want in [n for n, _, _ in hits] else 1)
PY
}

OUT=$(resolve_top3 "evidence edge citation trong câu trả lời wiki" query); RC=$?
[ "$RC" -eq 0 ] \
  && ok "router THẬT: hỏi về evidence/edge → /query lọt top-3 ($OUT)" \
  || bad "router THẬT (query)" "hỏi về evidence/edge mà KHÔNG ra /query ($OUT)"

OUT=$(resolve_top3 "grounding check verdict review code" qc-code); RC=$?
[ "$RC" -eq 0 ] \
  && ok "router THẬT: hỏi về grounding/verdict → /qc-code lọt top-3 ($OUT)" \
  || bad "router THẬT (qc-code)" "hỏi về grounding/verdict mà KHÔNG ra /qc-code ($OUT)"

# ─────────────────────────────────────────────────────────────────────────────
hdr "(c) capproof — engine mới PHẢI có neo bằng chứng, không khai suông"

CP="$TMP/capproof.json"
python3 "$SRC/fdk/tools/build-capabilities.py" --root "$SRC" --capproof-json > "$CP" 2>/dev/null
# LƯU Ý: chạy build-capabilities.py KHÔNG cờ sẽ GHI fdk/CAPABILITIES.md — dùng
# --capproof-json (read-only) để test không bẩn repo thật.

if [ -s "$CP" ]; then
  UNPROVEN=$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1]))['unproven']))" "$CP")
  TOTAL=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['counts']['total'])" "$CP")
  [ "$UNPROVEN" = "0" ] \
    && ok "capproof: 0/$TOTAL năng lực khai mà không neo bằng chứng" \
    || bad "capproof" "$UNPROVEN năng lực khai suông (không neo test/golden/rule nào)"
else
  bad "capproof" "--capproof-json không ra JSON"
fi

# Ratchet so baseline: nợ MỚI hoặc TỤT (proven → unproven) đều đỏ.
RATCHET=$(python3 - "$CP" "$SRC/harness/metrics/capproof-baseline.json" <<'PY' 2>/dev/null
import json, sys
cp = json.load(open(sys.argv[1])); base = json.load(open(sys.argv[2]))
proven, known = set(base["proven"]), set(base["proven"]) | set(base["unproven"])
new = [k for k in cp["unproven"] if k not in known]
dem = [k for k in cp["unproven"] if k in proven]
added = [k for k in cp["items"] if k not in known]
print("RED %s" % (new + dem) if (new or dem) else "GREEN %d năng lực MỚI so baseline, tất cả có neo" % len(added))
PY
)
case "$RATCHET" in
  GREEN*) ok "capproof ratchet: không nợ mới, không tụt"; note "${RATCHET#GREEN }" ;;
  *)      bad "capproof ratchet" "${RATCHET:-không so được baseline}" ;;
esac

# Tên engine viết TÁCH khỏi đuôi (ghép lại lúc chạy) là cố ý: capproof tier-3 công nhận
# "có test" chỉ vì tên file engine xuất hiện trong nội dung một script ở harness/tests/.
# Viết đủ tên đầy đủ ở đây thì chính test này thành NEO GIẢ cho những engine nó KHÔNG hề
# chạy — neo giả tệ hơn không có neo. Vì lý do đó cả comment này cũng không viết tên đủ.
for E in hub grounding-check wiki-graph token-budget provenance-log; do
  PROOF=$(python3 -c "
import json,sys
it=json.load(open(sys.argv[1]))['items'].get('script:'+sys.argv[2]+'.py') or {}
print((it.get('proof') or '') + ('|' + it.get('via','') if it.get('proof') else ''))" "$CP" "$E" 2>/dev/null)
  [ -n "$PROOF" ] \
    && ok "neo: $E.py → ${PROOF%%|*} (via ${PROOF##*|})" \
    || bad "neo: $E.py" "engine của T1–T7 không có điểm neo bằng chứng nào"
done

# ─────────────────────────────────────────────────────────────────────────────
hdr "(d) baseline truy hồi không tụt"

python3 "$SRC/harness/scripts/retrieval-eval.py" --self-test >/dev/null 2>&1 \
  && ok "retrieval-eval --self-test xanh (scorer coherent trên bộ golden)" \
  || bad "retrieval self-test" "đỏ"

# `--check` cần --outputs (kết quả một lần chạy query pipeline THẬT) nên KHÔNG tất định,
# không đưa vào CI được. Hai tính chất DƯỚI ĐÂY thì tất định và bắt đúng hai kiểu tụt
# thật: mất golden (coverage) và baseline bị hạ lặng lẽ (ratchet).
COV=$(python3 - "$SRC" <<'PY' 2>/dev/null
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "harness/scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location("re_", root / "harness/scripts/retrieval-eval.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
disk = {g["id"] for g in m.load_goldens(root / "llmwiki/wiki/sources/evals/retrieval")}
base = json.loads((root / "harness/metrics/retrieval-baseline.json").read_text(encoding="utf-8"))
lost = sorted(set(base["goldens"]) - disk)
s = base["summary"]
print("%s|%d|%d|%d|%d|%d|%s" % ("LOST" if lost else "OK", len(disk), len(base["goldens"]),
                                s["hits"], s["decided"], s["goldens"], ",".join(lost)))
PY
)
IFS='|' read -r ST NDISK NBASE BHITS BDEC BGOLD LOST <<< "${COV:-ERR|0|0|0|0|0|}"
[ "$ST" = "OK" ] \
  && ok "coverage: $NBASE/$NBASE golden của baseline còn trên đĩa (đĩa hiện có $NDISK)" \
  || bad "coverage tụt" "golden biến mất khỏi đĩa: ${LOST:-$COV}"
note "delta golden: $NDISK trên đĩa vs $NBASE trong baseline ($(( NDISK - NBASE )) mới)"

[ "$BHITS" = "$BDEC" ] && [ "$BDEC" = "$BGOLD" ] && [ "$BGOLD" != "0" ] \
  && ok "baseline ratchet: hits $BHITS/$BGOLD — chưa ai hạ baseline xuống dưới toàn-trúng" \
  || bad "baseline bị hạ" "hits=$BHITS decided=$BDEC goldens=$BGOLD (đáng lẽ bằng nhau)"

# ─────────────────────────────────────────────────────────────────────────────
hdr "(e) parity ba bề mặt phát hành skill"

python3 "$SRC/harness/scripts/sync-skills.py" --check >/dev/null 2>&1 \
  && ok "sync-skills --check: skills/ ↔ llmwiki/skills/ khớp" \
  || bad "sync-skills drift" "hai cây skill lệch — máy/dự án khác nhận bản cũ"

for PAIR in "query:wiki-loop" "qc-code:dev-loop"; do
  S="${PAIR%%:*}"; L="${PAIR##*:}"
  if diff -q "$SRC/skills/$S/SKILL.md" "$SRC/llmwiki/skills/$L/$S.md" >/dev/null 2>&1; then
    ok "parity: skills/$S/SKILL.md ≡ llmwiki/skills/$L/$S.md"
  else
    bad "parity $S" "canonical ↔ mirror khác nhau (skill T2/T4 sửa chưa đồng bộ)"
  fi
done

# Chỉ mục search là bề mặt THỨ BA: sửa SKILL.md mà quên dựng lại thì consumer ngoài
# (cheatsheet, fdk/skills.search.json) vẫn route theo mô tả CŨ.
python3 - "$SRC" "$TMP/skills.search.json" <<'PY' 2>/dev/null
import importlib.util, sys
from pathlib import Path
root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("bss", root / "fdk/tools/build-skill-search.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.write_json(m.build_index(str(root / "skills")), sys.argv[2])
PY
if cmp -s "$TMP/skills.search.json" "$SRC/fdk/skills.search.json"; then
  ok "parity: fdk/skills.search.json khớp chỉ mục dựng lại từ skills/"
else
  bad "search-index cũ" "fdk/skills.search.json lệch skills/ — chạy build-skill-search.py"
fi

# ─────────────────────────────────────────────────────────────────────────────
hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
