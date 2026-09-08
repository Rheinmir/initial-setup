#!/usr/bin/env bash
# flush-idempotent-test — R17 xả sổ: MỘT phiên chỉ được MỘT thẻ p-auto.
#
# Kiểm CẢ HAI bản cài đặt, vì logic này bị chép làm hai:
#   A. llmwiki/.claude/hooks/session_end.py::flush_problem_tree   (repo framework)
#   B. harness/poc-vendor-neutral/bin/harness-events.py::m_session_end  (bản PHÁT XUỐNG
#      downstream — đây mới là bản người dùng thật chạm vào)
# Vá một bản rồi tưởng xong là cách hỏng đã xảy ra: p-auto-21 ≡ p-auto-22 (phiên dba79064,
# 14/08/26) được vá ở A trước, còn B vẫn nguyên lỗi cho tới khi UAT lôi ra. Test này tồn tại
# để lần sau hai bản lệch nhau thì đỏ ngay, không cần ai nhớ.
#
# Usage: bash harness/tests/flush-idempotent-test.sh [repo-root]   (exit 0 = pass)
set -u
ROOT="$(cd "${1:-.}" && pwd)"
A="$ROOT/llmwiki/.claude/hooks/session_end.py"
B="$ROOT/harness/poc-vendor-neutral/bin/harness-events.py"
pass=0; fail=0
ok(){  printf '  \033[1;32m✓\033[0m %s\n' "$1"; pass=$((pass+1)); }
bad(){ printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

check(){   # $1=nhãn  $2=chuỗi "a b c indent"
  set -- "$1" $2
  [ "${2:-}" = "1" ] && ok "$1 · phiên mới → 1 thẻ"                              || bad "$1 · phiên mới ra ${2:-?} thẻ"
  [ "${3:-}" = "1" ] && ok "$1 · CÙNG phiên bắn lần 2 → VẪN 1 thẻ (chốt cắn)"    || bad "$1 · ghi trùng: ra ${3:-?} thẻ"
  [ "${4:-}" = "2" ] && ok "$1 · phiên KHÁC → ghi thẻ mới (không chặn nhầm)"     || bad "$1 · chặn nhầm phiên khác (${4:-?})"
  [ "${5:-}" = "1" ] && ok "$1 · giữ indent=1, xả sổ không đẻ diff toàn file"    || bad "$1 · indent lệch định dạng sổ"
}

[ -f "$A" ] || { bad "thiếu session_end.py"; printf '\n1 FAIL\n'; exit 1; }
[ -f "$B" ] || { bad "thiếu harness-events.py"; printf '\n1 FAIL\n'; exit 1; }

OUT_A="$(python3 - "$A" <<'PY'
import importlib.util, json, os, pathlib, re, shutil, subprocess, sys, tempfile
hook = sys.argv[1]; sys.path.insert(0, os.path.dirname(hook))
tmp = pathlib.Path(tempfile.mkdtemp())
try:
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)
    (tmp / "harness").mkdir(); (tmp / "harness" / "x.py").write_text("# chạm framework\n")
    (tmp / "llmwiki" / "html").mkdir(parents=True)
    tree = tmp / "llmwiki" / "html" / "problem-tree.html"
    tree.write_text('<script type="application/json" id="tree-data">[]</script>\n', encoding="utf-8")
    spec = importlib.util.spec_from_file_location("se", hook)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    n = lambda: len(json.loads(re.search(r'id="tree-data">(.*?)</script>',
                    tree.read_text(encoding="utf-8"), re.S).group(1)))
    def dirty(i):   # để lại một file framework CHƯA commit -> hook mới có cớ xả sổ
        (tmp / "harness" / f"t{i}.py").write_text("# chạm framework\n")
    def commit():   # dọn sổ về sạch -> lần bắn sau, chốt session là thứ DUY NHẤT chặn được
        subprocess.run(["git", "add", "-A"], cwd=tmp, capture_output=True)
        subprocess.run(["git", "-c", "user.name=u", "-c", "user.email=u@u",
                        "commit", "-q", "-m", "x"], cwd=tmp, capture_output=True)
    # Phải commit sổ giữa các lần bắn: hook CỐ Ý bỏ qua khi chính file sổ đang bẩn.
    # Không commit thì lần bắn thứ ba bị chặn vì lý do đó, và assertion "phiên khác
    # vẫn ghi được" đỗ mà không hề chạm tới chốt session — đỗ vì lý do sai.
    dirty(1); mod.flush_problem_tree(tmp, "dba79064-aaaa"); a = n(); commit()
    dirty(2); mod.flush_problem_tree(tmp, "dba79064-aaaa"); b = n(); commit()
    dirty(3); mod.flush_problem_tree(tmp, "72190e1c-bbbb"); c = n(); commit()
    print(f'{a} {b} {c} {int(chr(10) + " {" + chr(10) + chr(32)+chr(32) + chr(34) + "id" + chr(34) in tree.read_text(encoding="utf-8"))}')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
PY
)" || { bad "bản A không chạy được"; OUT_A="x x x x"; }

OUT_B="$(python3 - "$B" <<'PY'
import json, pathlib, re, shutil, subprocess, sys, tempfile
ev = sys.argv[1]
tmp = pathlib.Path(tempfile.mkdtemp())
try:
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)
    (tmp / "harness").mkdir(); (tmp / "harness" / "x.py").write_text("# chạm framework\n")
    (tmp / "llmwiki" / "html").mkdir(parents=True)
    tree = tmp / "llmwiki" / "html" / "problem-tree.html"
    tree.write_text('<script type="application/json" id="tree-data">[]</script>\n', encoding="utf-8")
    env = {**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(tmp)}
    def fire(sid):
        subprocess.run([sys.executable, ev, "session-end"], cwd=str(tmp), env=env,
                       input=json.dumps({"session_id": sid}), text=True,
                       capture_output=True, timeout=30)
    n = lambda: len(json.loads(re.search(r'id="tree-data">(.*?)</script>',
                    tree.read_text(encoding="utf-8"), re.S).group(1)))
    def dirty(i):
        (tmp / "harness" / f"t{i}.py").write_text("# chạm framework\n")
    def commit():
        subprocess.run(["git", "add", "-A"], cwd=str(tmp), capture_output=True)
        subprocess.run(["git", "-c", "user.name=u", "-c", "user.email=u@u",
                        "commit", "-q", "-m", "x"], cwd=str(tmp), capture_output=True)
    # xem chú thích ở bản A: bẩn -> bắn -> commit. Không dọn sổ giữa các lần thì
    # assertion 3 đỗ vì hook bỏ qua do sổ đang bẩn, chứ không hề chạm chốt session.
    dirty(1); fire("dba79064-aaaa"); a = n(); commit()
    dirty(2); fire("dba79064-aaaa"); b = n(); commit()
    dirty(3); fire("72190e1c-bbbb"); c = n(); commit()
    print(f'{a} {b} {c} {int(chr(10) + " {" + chr(10) + chr(32)+chr(32) + chr(34) + "id" + chr(34) in tree.read_text(encoding="utf-8"))}')
finally:
    shutil.rmtree(tmp, ignore_errors=True)
PY
)" || { bad "bản B không chạy được"; OUT_B="x x x x"; }

check "A hooks/session_end" "$OUT_A"
check "B harness-events (bản phát downstream)" "$OUT_B"

printf '\n\033[1m═══ flush-idempotent: %d test — \033[1;32m%d PASS\033[0m / \033[1;31m%d FAIL\033[0m\033[0m\n' "$((pass+fail))" "$pass" "$fail"
[ "$fail" -eq 0 ]
