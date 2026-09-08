#!/usr/bin/env bash
# flush-idempotent-test — R17 flush problem-tree: MỘT phiên chỉ được MỘT thẻ p-auto.
# SessionEnd có thể bắn nhiều lần cho cùng một phiên (resume, thoát lại); không chốt
# theo session_id thì ra thẻ trùng khít — đã dính thật: p-auto-21 ≡ p-auto-22, cùng
# phiên dba79064, 14/08/26. Kiểm luôn indent=1 để mỗi lần xả sổ không đẻ diff ~950 dòng.
#
# Usage: bash harness/tests/flush-idempotent-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
H="$ROOT/llmwiki/.claude/hooks/session_end.py"
pass=0; fail=0
ok(){  printf '  \033[1;32m✓\033[0m %s\n' "$1"; pass=$((pass+1)); }
bad(){ printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

[ -f "$H" ] || { bad "thiếu session_end.py"; printf '\n1 FAIL\n'; exit 1; }

OUT="$(ROOT_ARG="$ROOT" python3 - "$H" <<'PY'
import importlib.util, json, os, pathlib, re, shutil, subprocess, sys, tempfile
hook = sys.argv[1]
sys.path.insert(0, os.path.dirname(hook))  # hooklib nằm cạnh hook
tmp = pathlib.Path(tempfile.mkdtemp())
try:
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)
    (tmp / "harness").mkdir()
    (tmp / "harness" / "x.py").write_text("# chạm bề mặt framework\n")
    (tmp / "llmwiki" / "html").mkdir(parents=True)
    tree = tmp / "llmwiki" / "html" / "problem-tree.html"
    tree.write_text('<script type="application/json" id="tree-data">[]</script>\n', encoding="utf-8")
    spec = importlib.util.spec_from_file_location("se", hook)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    def n():
        raw = tree.read_text(encoding="utf-8")
        return len(json.loads(re.search(r'id="tree-data">(.*?)</script>', raw, re.S).group(1)))
    mod.flush_problem_tree(tmp, "dba79064-aaaa"); a = n()
    mod.flush_problem_tree(tmp, "dba79064-aaaa"); b = n()
    mod.flush_problem_tree(tmp, "72190e1c-bbbb"); c = n()
    ind = '\n {\n  "id"' in tree.read_text(encoding="utf-8")
    print(f"{a} {b} {c} {int(ind)}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
PY
)" || { bad "hook không chạy được"; printf '\n1 FAIL\n'; exit 1; }

set -- $OUT
[ "${1:-}" = "1" ] && ok "phiên mới → ghi 1 thẻ" || bad "phiên mới không ghi thẻ (được ${1:-?})"
[ "${2:-}" = "1" ] && ok "CÙNG phiên bắn lần 2 → VẪN 1 thẻ (chốt idempotent cắn)" || bad "thẻ trùng: cùng phiên ra ${2:-?} thẻ"
[ "${3:-}" = "2" ] && ok "phiên KHÁC → ghi thẻ mới (không chặn nhầm)" || bad "chặn nhầm phiên khác (được ${3:-?})"
[ "${4:-}" = "1" ] && ok "giữ indent=1 — xả sổ không đẻ diff toàn file" || bad "indent lệch định dạng sổ"

printf '\n\033[1m═══ flush-idempotent: %d test — \033[1;32m%d PASS\033[0m / \033[1;31m%d FAIL\033[0m\033[0m\n' "$((pass+fail))" "$pass" "$fail"
[ "$fail" -eq 0 ]
