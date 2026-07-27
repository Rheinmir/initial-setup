#!/usr/bin/env python3
"""L1/SessionStart: code-graph keeper — BÁO CÁO, fail-open tuyệt đối.

Mục đích: giữ "luồng thật" của code-graph bền qua restart.
- Server code-graph chạy `--watch` chỉ re-watch các repo có trong
  ~/.graph-agent/repos.txt. Nếu repo code của project bị rớt khỏi registry
  (xoá tay, clone mới, đổi path) → restart là mất auto-reindex.
- Hook này quét project tìm repo code có .graph-agent/index.db, tự re-register
  nếu thiếu, và cảnh báo nếu manifest tồn tại nhưng chưa index (clone mới).

KHÔNG reindex per-edit (watcher đã lo, debounce 2s). Chỉ vá durability + visibility.
Mọi lỗi → exit 0, không bao giờ làm gãy phiên.
"""
import os
import sys
from pathlib import Path

try:
    from hooklib import project_dir, read_payload
except Exception:
    def read_payload() -> dict:
        import json
        try:
            return json.load(sys.stdin)
        except Exception:
            return {}

    def project_dir(payload: dict) -> str:
        return os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd()


MANIFESTS = {"go.mod", "package.json", "pyproject.toml", "Cargo.toml"}
SKIP = {"node_modules", ".next", ".git", "vendor", "dist", "build",
        ".venv", "__pycache__", "llmwiki", ".orca-onboard", ".understand-anything"}
REG = Path(os.environ.get("GRAPH_HOME", Path.home() / ".graph-agent")) / "repos.txt"
MAX_DEPTH = 2  # code thật có thể nằm ở subdir của submodule (vd <sub>/<svc>/go.mod)


def find_code_dirs(root: Path):
    """Quét tới MAX_DEPTH, trả mọi thư mục chứa 1 manifest (go.mod/package.json…)."""
    out = []

    def walk(d: Path, depth: int):
        if depth > MAX_DEPTH:
            return
        if any((d / m).is_file() for m in MANIFESTS):
            out.append(d)
        try:
            entries = list(d.iterdir())
        except Exception:
            return
        for e in entries:
            if e.is_dir() and e.name not in SKIP and not e.name.startswith("."):
                walk(e, depth + 1)

    walk(root, 0)
    return out



def _db_usable(db_path) -> bool:
    """DB sqlite này query được không — mở được VÀ có bảng thật.

    Mượn nguyên định nghĩa của harness/scripts/dep-health.py (một nguồn duy nhất). Import
    được thì import; không thì tự kiểm tại chỗ theo đúng cùng tiêu chí — hook KHÔNG bao giờ
    được phép chết vì thiếu harness.
    """
    try:
        import importlib.util
        for cand in (Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / "harness/scripts/dep-health.py",
                     Path.home() / ".claude/harness/harness/scripts/dep-health.py"):
            if cand.is_file():
                spec = importlib.util.spec_from_file_location("_dephealth", cand)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return bool(mod.db_has_schema(Path(db_path)))
    except Exception:
        pass
    try:
        import sqlite3
        # KHÔNG mode=ro: WAL thiếu -shm thì ro báo hỏng trên DB lành (xem dep-health).
        conn = sqlite3.connect(str(db_path))
        try:
            names = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        return {"symbols", "files"} <= names
    except Exception:
        return False


def main() -> None:
    payload = read_payload()
    root = Path(project_dir(payload)).resolve()
    if not (root / "llmwiki").is_dir():
        sys.exit(0)  # không phải project llmwiki → bỏ qua

    code_dirs = find_code_dirs(root)
    if not code_dirs:
        sys.exit(0)

    reg_entries = set()
    if REG.exists():
        reg_entries = {l.strip() for l in REG.read_text(encoding="utf-8").splitlines() if l.strip()}

    # "Có file index.db" KHÔNG suy ra "code-graph dùng được" — DB 0 byte hoặc thiếu bảng
    # `symbols` vẫn là một file. Cùng anti-pattern đã khai tử ở session_start, và ở ĐÂY nó
    # nặng hơn: kết luận này (a) GHI path vào registry global ~/.graph-agent/repos.txt,
    # (b) DẬP TẮT cảnh báo "chưa index". Dùng chung đúng một định nghĩa với dep-health.py
    # để hai nơi không bao giờ trôi khỏi nhau.
    db_dirs = [d for d in code_dirs
               if (d / ".graph-agent" / "index.db").is_file()
               and _db_usable(d / ".graph-agent" / "index.db")]
    if not db_dirs:
        sys.exit(0)  # project KHÔNG dùng code-graph → im hoàn toàn, không nag

    def covered_by_indexed(d: Path) -> bool:
        """True nếu một ancestor/descendant của d đã có db (vd submodule wrapper có subdir đã index)."""
        ds = str(d)
        for x in db_dirs:
            xs = str(x)
            if xs == ds or xs.startswith(ds + os.sep) or ds.startswith(xs + os.sep):
                return True
        return False

    added, missing_db = [], []
    for d in code_dirs:
        if d in db_dirs:
            if str(d) not in reg_entries:
                reg_entries.add(str(d))
                added.append(d)
        elif not covered_by_indexed(d):
            missing_db.append(d)

    if added:
        REG.parent.mkdir(parents=True, exist_ok=True)
        REG.write_text("\n".join(sorted(reg_entries)) + "\n", encoding="utf-8")

    msgs = []
    if added:
        msgs.append("⟳ [code-graph] re-registered cho watcher: "
                    + ", ".join(d.name for d in added))
    if missing_db:
        rel = ", ".join(str(d.relative_to(root)) for d in missing_db)
        msgs.append(f"⟳ [code-graph] {len(missing_db)} repo chưa index ({rel}) — "
                    "gọi reindex_repo(<path>) để bật auto-watch.")
    if msgs:
        print("\n".join(msgs))
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)  # fail-open tuyệt đối
