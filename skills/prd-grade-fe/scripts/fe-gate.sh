#!/usr/bin/env bash
# fe-gate — cổng tất định trước khi giao UI (/prd-grade-fe pha 4).
# Exit: 0 xanh · 1 impeccable lỗi vận hành · 2 có finding hoặc viewport đỏ · 3 skipped (thiếu node/mạng) · 4 target thiếu
# Bẫy đã đo trên impeccable@3.6.1: target không tồn tại → "Warning: cannot access" rồi rc 0 (giả sạch) → assert ở đây trước.
# JSON (--json) ra stdout là MẢNG PHẲNG: {antipattern,name,severity,file,line,snippet}. npx gộp stderr vào stdout nên chỉ tin --json.
set -u
IMP="npx -y impeccable@3.6.1"
HERE=$(cd "$(dirname "$0")" && pwd)
REP=fe-gate.report.json

gate() {
  local noview=0; [ "${1:-}" = "--no-viewport" ] && { noview=1; shift; }
  [ $# -gt 0 ] || { echo "usage: fe-gate.sh [--no-viewport] <target>..."; return 4; }
  for t in "$@"; do
    [ -e "$t" ] || { echo "fe-gate: target không tồn tại: $t (impeccable sẽ trả rc 0 giả — chặn ở đây)"; printf '{"detect_rc":4,"missing":"%s"}\n' "$t" > $REP; return 4; }
  done
  command -v node >/dev/null || { echo '{"detect_rc":3,"skipped":["node không có"]}' > $REP; echo "fe-gate: skipped — không có node. KHÔNG phải sạch."; return 3; }
  local out rc; out=$($IMP detect --json --no-advisory "$@" 2>/dev/null); rc=$?
  if [ $rc = 1 ] || [ -z "$out" ]; then
    echo "fe-gate: impeccable lỗi vận hành hoặc không tải được (rc=$rc). KHÔNG phải sạch."
    printf '{"detect_rc":%s,"skipped":["impeccable không chạy"]}\n' "$rc" > $REP
    [ $rc = 1 ] && return 1 || return 3
  fi
  printf '%s' "$out" | RC=$rc node -e '
    let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{
      let j; try{ j=JSON.parse(s.slice(s.indexOf("["))); }catch(e){ console.error("fe-gate: JSON không parse được"); process.exit(1); }
      const f=Array.isArray(j)?j:(j.findings||[]);
      for(const x of f) console.log(`${x.antipattern}\t${x.file}:${x.line}\t${(x.snippet||x.name||"").slice(0,90)}`);
      require("fs").writeFileSync(process.env.REP||"fe-gate.report.json",JSON.stringify({detect_rc:Number(process.env.RC),findings:f},null,1));
    })' || return 1
  [ $rc = 2 ] && { echo "fe-gate: rc 2 — có finding, sửa rồi chạy lại (tối đa 3 vòng)"; return 2; }
  if [ $noview = 0 ]; then
    node "$HERE/viewport-check.mjs" "$@" || { echo "fe-gate: viewport đỏ (scroll ngang ở 320/375/414/768)"; return 2; }
  fi
  echo "fe-gate: XANH (detect rc 0$( [ $noview = 0 ] && echo ' + 4 viewport'))"; return 0
}

self_test() {
  local d; d=$(mktemp -d)
  printf '<html><body style="font-family:Georgia;color:#111;background:#fff"><h1>Sạch</h1><p>ok</p></body></html>' > "$d/clean.html"
  printf '<html><body style="font-family:Inter;color:#808080;background:linear-gradient(#667eea,#764ba2)"><h1>Hi</h1><h4>skip</h4></body></html>' > "$d/dirty.html"
  ( cd "$d" && gate --no-viewport "$d/clean.html" >/dev/null ); r1=$?
  ( cd "$d" && gate --no-viewport "$d/dirty.html" >/dev/null ); r2=$?
  ( cd "$d" && gate --no-viewport "$d/nope.html" >/dev/null ); r3=$?
  echo "clean=$r1 dirty=$r2 missing=$r3"
  if [ "$r1" = 0 ] && [ "$r2" = 2 ] && [ "$r3" = 4 ]; then echo "fe-gate --self-test: 3/3 ok"; else echo "fe-gate --self-test: FAIL (cần mạng cho npx lần đầu; 3 = skipped)"; exit 1; fi
}

case "${1:-}" in --self-test) self_test ;; "") gate ;; *) gate "$@" ;; esac
