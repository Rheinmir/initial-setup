#!/usr/bin/env bash
# Kill-switch của commit-DAG hub (T7): TẮT được · XOÁ được · GỠ được.
#
# Bối cảnh: hub là tính năng opt-in được thêm vào một vòng lặp đã chạy sản xuất. Lời hứa
# trong `llmwiki/wiki/concepts/commit-dag-hub.md` là ba tầng rút lui — tắt bằng cờ/config,
# xoá sạch dữ liệu bằng `purge`, gỡ hẳn code bằng cách xoá `hub.py`. Lời hứa đó chỉ có giá
# trị nếu có ai đó kiểm nó bằng lệnh thật; ngược lại nó mục dần theo từng lần "tiện tay"
# thêm một `import hub` ở đầu loop-runner.
#
# Khoá 6 bất biến:
#   (a) MẶC ĐỊNH TẮT — chạy ratchet với config THẬT mà không bật cờ thì không ref nào sinh
#       ra, và run-log giữ đúng schema cũ (không có key `hub`, không có `hub_ref`);
#   (b) công tắc có THẬT — config `hub.enabled: true` thì ref phải xuất hiện (nếu không,
#       assert (a) chỉ đang xanh vì hub đã chết, không phải vì nó tắt đúng);
#   (c) `--no-hub` ĐÈ được config đang bật — kill-switch một-lần-chạy;
#   (d) `purge` xoá sạch `refs/hub/*` + `refs/notes/hub`, và KHÔNG có `--yes` thì chỉ in;
#   (e) `prune --keep-top K` giữ đúng node điểm cao nhất;
#   (f) GỠ CODE — vắng `hub.py` thì loop-runner vẫn chạy (nạp động, không import tĩnh),
#       kể cả khi người dùng vẫn truyền `--hub`;
#   (g) `git revert` commit T7 trong một clone sandbox → ba engine anh em vẫn xanh.
#
# SANDBOX: mọi thứ nằm trong `mktemp -d`. Không lệnh nào ghi vào repo thật — đặc biệt
# KHÔNG tạo `refs/hub/*` trong repo dev (mọi lệnh hub đều đi kèm --root trỏ vào sandbox).
# PYTHONDONTWRITEBYTECODE: nhánh hub BẬT nạp hub.py bằng exec_module, mà việc đó ghi
# `harness/scripts/__pycache__/hub.pyc` — file .pyc ở repo này ĐANG ĐƯỢC TRACK, nên chạy
# test sẽ làm bẩn `git status`. Tắt ghi bytecode là cách giữ sandbox tuyệt đối.
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1

SRC="${1:?usage: ge-killswitch-test.sh <repo-root>}"
SRC=$(cd "$SRC" && pwd)
PASS=0; FAIL=0; N=0
ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }
hdr() { printf '\n\033[1m── %s\033[0m\n' "$1"; }

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

LR="$SRC/harness/scripts/loop-runner.py"
HUB="$SRC/harness/scripts/hub.py"
CFG="$SRC/harness/loop-runner.config.yaml"

# Repo git dùng-một-lần + metric TĂNG DẦN (mọi vòng ratchet đều "kept" → mỗi vòng một commit).
mk_repo() {
  git init -q "$1"
  git -C "$1" config user.email ks@test.local
  git -C "$1" config user.name "killswitch test"
  git -C "$1" config commit.gpgsign false
  printf '0\n' > "$1/n"
  cat > "$1/bump.py" <<'PY'
import pathlib
p = pathlib.Path("n"); v = int(p.read_text() or 0) + 1
p.write_text(str(v)); print(v)
PY
  git -C "$1" add -A
  git -C "$1" commit -qm seed
}

nrefs()  { git -C "$1" for-each-ref refs/hub --format='%(refname)' | wc -l | tr -d ' '; }
# Số vòng ratchet đã GIỮ trong run-log — chốt chặn ca "xanh vì chẳng chạy gì".
kept_of() {
  python3 -c "
import json,sys
its = json.load(open(sys.argv[1]))['iterations']
print(sum(1 for i in its if i.get('ratchet') == 'kept'))" "$1" 2>/dev/null || echo 0
}

# ── (a) TẮT là mặc định ─────────────────────────────────────────────────────
hdr "(a) mặc định TẮT — config THẬT của repo, không cờ, thì không ref nào sinh ra"
mk_repo "$TMP/a"
( cd "$TMP" && python3 "$LR" run --verify 'false' --config "$CFG" \
    --metric-cmd "python3 bump.py" --direction max --max-iter 2 \
    --log "$TMP/a.json" --episodic "$TMP/a-ep.md" --cwd "$TMP/a" --quiet ) >/dev/null 2>&1

KEPT_A=$(kept_of "$TMP/a.json")
[ "${KEPT_A:-0}" -ge 2 ] \
  && ok "ratchet THỰC SỰ chạy ($KEPT_A vòng kept) — assert dưới không xanh khống" \
  || bad "tiền đề (a)" "ratchet không chạy (kept=$KEPT_A) ⇒ mọi assert 'không có ref' là vô nghĩa"

[ "$(nrefs "$TMP/a")" = 0 ] \
  && ok "mặc định tắt: refs/hub rỗng dù ratchet đã đẻ commit" \
  || bad "default-off" "hub sinh $(nrefs "$TMP/a") ref khi CHƯA ai bật"

python3 - "$TMP/a.json" <<'PY' >/dev/null 2>&1 \
  && ok "run-log giữ schema cũ: không key 'hub', không field 'hub_ref'" \
  || bad "default-off schema" "run-log rò field của hub khi hub đang tắt"
import json, sys
log = json.load(open(sys.argv[1]))
assert "hub" not in log, "log có key 'hub' khi hub tắt"
assert all("hub_ref" not in i for i in log["iterations"]), "iteration có hub_ref khi hub tắt"
PY

# ── (b) công tắc có thật ────────────────────────────────────────────────────
hdr "(b) công tắc có THẬT — hub.enabled: true thì ref phải xuất hiện"
mk_repo "$TMP/b"
cat > "$TMP/cfg-on.yaml" <<'YAML'
hub:
  enabled: true
  agent: "killswitch-test"
YAML
( cd "$TMP" && python3 "$LR" run --verify 'false' --config "$TMP/cfg-on.yaml" \
    --metric-cmd "python3 bump.py" --direction max --max-iter 2 \
    --log "$TMP/b.json" --cwd "$TMP/b" --quiet ) >/dev/null 2>&1
[ "$(nrefs "$TMP/b")" -ge 2 ] \
  && ok "bật bằng config: $(nrefs "$TMP/b") ref sinh ra ⇒ assert (a) hỏng được" \
  || bad "config-on" "bật rồi mà chỉ có $(nrefs "$TMP/b") ref — công tắc không nối vào gì"

# ── (c) --no-hub đè config đang bật ─────────────────────────────────────────
hdr "(c) --no-hub ĐÈ được config đang bật (kill-switch cho một lần chạy)"
mk_repo "$TMP/c"
( cd "$TMP" && python3 "$LR" run --verify 'false' --config "$TMP/cfg-on.yaml" --no-hub \
    --metric-cmd "python3 bump.py" --direction max --max-iter 2 \
    --log "$TMP/c.json" --cwd "$TMP/c" --quiet ) >/dev/null 2>&1
KEPT_C=$(kept_of "$TMP/c.json")
[ "$(nrefs "$TMP/c")" = 0 ] && [ "${KEPT_C:-0}" -ge 2 ] \
  && ok "--no-hub: ratchet vẫn chạy ($KEPT_C kept) nhưng refs/hub rỗng" \
  || bad "--no-hub" "còn $(nrefs "$TMP/c") ref (kept=$KEPT_C) — cờ tắt không đè được config"

# ── (d) purge: dry-run an toàn, --yes xoá sạch ──────────────────────────────
hdr "(d) purge — không --yes chỉ in, có --yes xoá sạch ref VÀ notes"
mk_repo "$TMP/d"
for i in 1 2 3; do
  printf '%s\n' "$i" > "$TMP/d/f$i"
  git -C "$TMP/d" add -A
  git -C "$TMP/d" commit -qm "c$i"
  python3 "$HUB" push --agent agent-d --hypothesis "thu $i" --metric "0.$i" --root "$TMP/d" >/dev/null 2>&1
done
[ "$(nrefs "$TMP/d")" = 3 ] || bad "tiền đề (d)" "push không tạo đủ 3 ref (có $(nrefs "$TMP/d"))"

python3 "$HUB" purge --root "$TMP/d" >/dev/null 2>&1
[ "$(nrefs "$TMP/d")" = 3 ] \
  && [ -n "$(git -C "$TMP/d" for-each-ref refs/notes/hub)" ] \
  && ok "purge KHÔNG --yes = dry-run: 3 ref + notes còn nguyên" \
  || bad "purge dry-run" "dry-run đã xoá dữ liệu — lỡ tay là mất"

python3 "$HUB" purge --yes --root "$TMP/d" >/dev/null 2>&1
[ "$(nrefs "$TMP/d")" = 0 ] \
  && [ -z "$(git -C "$TMP/d" for-each-ref refs/notes/hub)" ] \
  && ok "purge --yes: refs/hub + refs/notes/hub đều sạch" \
  || bad "purge --yes" "còn sót ref ($(nrefs "$TMP/d")) hoặc notes"

# ── (e) prune: giữ đúng top-K theo metric ───────────────────────────────────
hdr "(e) prune --keep-top 1 giữ đúng node điểm CAO NHẤT, không phải node cuối"
mk_repo "$TMP/e"
i=0
for m in 0.1 0.9 0.5; do
  i=$((i + 1))
  printf '%s\n' "$m" > "$TMP/e/f$i"
  git -C "$TMP/e" add -A
  git -C "$TMP/e" commit -qm "c$i"
  python3 "$HUB" push --agent agent-e --hypothesis "diem $m" --metric "$m" --root "$TMP/e" >/dev/null 2>&1
done
python3 "$HUB" prune --keep-top 1 --root "$TMP/e" >/dev/null 2>&1
[ "$(nrefs "$TMP/e")" = 3 ] \
  && ok "prune KHÔNG --yes = dry-run: 3 ref còn nguyên" \
  || bad "prune dry-run" "dry-run đã xoá ref (còn $(nrefs "$TMP/e"))"

python3 "$HUB" prune --keep-top 1 --yes --root "$TMP/e" >/dev/null 2>&1
PRUNED=$(python3 "$HUB" log --root "$TMP/e" 2>/dev/null)
if [ "$(nrefs "$TMP/e")" = 1 ] && printf '%s' "$PRUNED" | grep -q '0\.9'; then
  ok "prune --keep-top 1 --yes: còn đúng 1 ref, đúng node metric 0.9"
else
  bad "prune keep-top" "còn $(nrefs "$TMP/e") ref, node giữ lại không phải 0.9"
fi

# ── (f) GỠ CODE: vắng hub.py thì loop-runner vẫn chạy ───────────────────────
hdr "(f) GỠ CODE — bản loop-runner KHÔNG có hub.py bên cạnh vẫn phải chạy"
mkdir -p "$TMP/nohub"
cp "$LR" "$TMP/nohub/loop-runner.py"   # sandbox: chỉ chép loop-runner, hub.py vắng theo cấu trúc
if python3 "$TMP/nohub/loop-runner.py" selftest >/dev/null 2>&1; then
  ok "vắng hub.py: loop-runner selftest vẫn ALL PASS (nạp động, không import tĩnh)"
else
  bad "gỡ được sạch" "loop-runner gãy khi vắng hub.py — có ai đó thêm import tĩnh"
fi

mk_repo "$TMP/f"
( cd "$TMP" && python3 "$TMP/nohub/loop-runner.py" run --verify 'false' --hub \
    --metric-cmd "python3 bump.py" --direction max --max-iter 2 \
    --log "$TMP/f.json" --cwd "$TMP/f" --quiet ) >/dev/null 2>&1
KEPT_F=$(kept_of "$TMP/f.json")
[ "${KEPT_F:-0}" -ge 2 ] && [ "$(nrefs "$TMP/f")" = 0 ] \
  && ok "vắng hub.py mà vẫn truyền --hub: ratchet chạy đủ ($KEPT_F kept), không crash, không ref" \
  || bad "fail-open khi gỡ" "--hub + vắng hub.py làm hỏng ratchet (kept=$KEPT_F, ref=$(nrefs "$TMP/f"))"

if grep -rnE '^[[:space:]]*(import|from)[[:space:]]+hub\b' \
     "$SRC/harness" "$SRC/fdk" --include='*.py' >/dev/null 2>&1; then
  bad "không import tĩnh" "có file import hub ở mức module — tầng gỡ-code sẽ vỡ lần tới"
else
  ok "không file .py nào trong harness/ hay fdk/ import tĩnh module hub"
fi

# ── (g) git revert commit T7 → phần còn lại vẫn xanh ────────────────────────
hdr "(g) git revert commit T7 trong clone sandbox — ba engine anh em vẫn xanh"
T7=$(git -C "$SRC" log --diff-filter=A --format='%H' -- harness/scripts/hub.py | head -1)
if [ -z "$T7" ]; then
  bad "tìm commit T7" "không tìm được commit thêm harness/scripts/hub.py"
else
  git clone -q "$SRC" "$TMP/clone" >/dev/null 2>&1
  git -C "$TMP/clone" config user.email ks@test.local
  git -C "$TMP/clone" config user.name "killswitch test"
  git -C "$TMP/clone" config commit.gpgsign false
  if git -C "$TMP/clone" revert --no-edit "$T7" >/dev/null 2>&1 \
     && [ ! -f "$TMP/clone/harness/scripts/hub.py" ]; then
    ok "revert ${T7:0:7} sạch, không xung đột, hub.py biến mất khỏi cây"
    for e in loop-runner.py:selftest wiki-graph.py:--self-test token-budget.py:--self-test; do
      s="${e%%:*}"; a="${e##*:}"
      if ( cd "$TMP/clone" && python3 "harness/scripts/$s" "$a" ) >/dev/null 2>&1; then
        ok "sau revert: $s $a vẫn xanh"
      else
        bad "sau revert: $s" "self-test đỏ khi bỏ T7 — 'bỏ T7 nếu cần' là lời hứa suông"
      fi
    done
  else
    bad "revert T7" "revert xung đột hoặc hub.py còn sót — không bỏ T7 sạch được"
  fi
fi

hdr "kết quả"
printf '  %d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
