#!/usr/bin/env python3
"""L1/SessionEnd: audit + tự sinh dòng tổng kết phiên vào wiki/log.md (R4 bằng máy)
+ R17 flush problem-tree: phiên chạm framework mà chưa vào sổ → append stub pending
bằng code thuần (đảm bảo 'tắt app bình thường thì cây truy vết vẫn nằm đúng chỗ').
SessionEnd không block được — chỉ ghi nhận."""
import datetime
import json
import pathlib
import re
import subprocess
import sys

from hooklib import audit, find_wiki_dir, project_dir, read_payload

# repo framework dùng fdk-problem-tree.html; dự án downstream dùng problem-tree.html (seed bởi install.sh)
TREE_CANDIDATES = ("llmwiki/html/fdk-problem-tree.html", "llmwiki/html/problem-tree.html")
FW_SURFACES = ("skills/", "harness/", "llmwiki/", "fdk/")


def flush_problem_tree(root: pathlib.Path, session_id: str) -> None:
    """Tất định, 0 token, fail-open. Gộp cả untracked (bài học p-auto-01)."""
    tree = next((root / rel for rel in TREE_CANDIDATES if (root / rel).is_file()), None)
    if tree is None:
        return
    try:
        diff = subprocess.run(["git", "diff", "--name-only", "HEAD"],
                              cwd=root, capture_output=True, text=True, timeout=10).stdout.split()
        status = subprocess.run(["git", "status", "--porcelain"],
                                cwd=root, capture_output=True, text=True, timeout=10).stdout
        untracked = [l[3:] for l in status.splitlines() if l.startswith("?? ")]
        touched = set(diff) | set(untracked)
    except Exception:
        return
    tree_names = ("fdk-problem-tree.html", "problem-tree.html")
    fw = sorted(p for p in touched if p.startswith(FW_SURFACES) and not p.endswith(tree_names))
    if not fw or any(p.endswith(tree_names) for p in touched):
        return
    try:
        html = tree.read_text(encoding="utf-8")
        m = re.search(r'(id="tree-data">\s*)(\[.*?\])(\s*</script>)', html, re.S)
        if not m:
            return
        nodes = json.loads(m.group(2))
        n_auto = sum(1 for n in nodes if str(n.get("id", "")).startswith("p-auto-")) + 1
        nodes.append({
            "id": f"p-auto-{n_auto:02d}", "parent": None,
            "title": "Thẻ ghi-tạm tự động: phiên chạm framework, chưa vào sổ",
            "desc": "Bề mặt bị chạm: " + ", ".join(fw[:8]) + (" …" if len(fw) > 8 else "")
                    + ". Thẻ do hook SessionEnd tự ghi (flush — xả sổ trước khi thoát); "
                      "lần /fdk kế tiếp sẽ chưng lọc về đúng nhánh.",
            "status": "open", "scope": [],
            "date": datetime.date.today().strftime("%d/%m/%y"),
            "session": (session_id or "unknown")[:8], "pending": True,
        })
        html = html[:m.start(2)] + json.dumps(nodes, ensure_ascii=False, indent=2) + html[m.end(2):]
        tree.write_text(html, encoding="utf-8")
    except Exception:
        pass


def summarize_today(root: pathlib.Path, session_id: str):
    f = root / ".claude" / "audit" / (datetime.date.today().isoformat() + ".jsonl")
    if not f.is_file():
        return None
    tools = 0
    files = set()
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if session_id and rec.get("session_id") != session_id:
            continue
        if rec.get("event") == "PostToolUse":
            tools += 1
            if rec.get("file_path"):
                files.add(pathlib.Path(rec["file_path"]).name)
    return tools, sorted(files)


def snapshot_ledgers(root: pathlib.Path) -> None:
    """Maintainer #2 (2026-07-18): ký ức máy-local (flywheel/memory/events/audit/tasks) gom
    tarball mỗi cuối phiên — backup không chờ ai nhớ. resolve_tool: repo-local → global
    (downstream dùng engine ~/.claude/harness). Fail-open tuyệt đối."""
    try:
        from hooklib import resolve_tool
        snap = resolve_tool(str(root), "harness/scripts/ledger-snapshot.py")
        if snap:
            subprocess.run([sys.executable, snap, "export", "--quiet", "--root", str(root)],
                           capture_output=True, timeout=30)
    except Exception:
        pass


def main() -> None:
    payload = read_payload()
    audit(payload, "SessionEnd")

    root = pathlib.Path(project_dir(payload))
    flush_problem_tree(root, payload.get("session_id", ""))
    snapshot_ledgers(root)
    wiki = find_wiki_dir(str(root))
    if wiki is None:
        sys.exit(0)
    summary = summarize_today(root, payload.get("session_id", ""))
    if not summary or summary[0] == 0:
        sys.exit(0)
    tools, files = summary
    sid = (payload.get("session_id") or "")[:8]
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    shown = ", ".join(files[:8]) + (" …" if len(files) > 8 else "")
    line = f"- {stamp} — session `{sid}` — {tools} tool calls — files: {shown or '(none)'}\n"
    try:
        with open(wiki / "log.md", "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
