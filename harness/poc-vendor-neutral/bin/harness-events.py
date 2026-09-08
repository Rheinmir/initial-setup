#!/usr/bin/env python3
"""Hook sự kiện cho harness PoC (ngoài PreToolUse/llmwiki-validate):
  stop     R3 index-sync   — chặn kết thúc lượt nếu wiki/index.md lệch file thật (exit 2)
  audit    R4 log-append   — ghi .claude/audit/audit.jsonl (có timestamp) + sinh .claude/audit/log.md
  session  R8 health       — in trạng thái + CHECK DRIFT vs remote (cảnh báo nếu policy lệch)
  docs     R10 docs-gate   — mỗi N prompt: inject directive đề nghị bổ sung docs + gọi /docs-site-macos

MỌI lỗi → fail-open (exit 0). Drift-check best-effort (timeout ngắn), tắt bằng env LLMWIKI_NO_DRIFT=1.
"""
import glob
import json
import os
import sys


def _overstack_prefix(root: str) -> str:
    """Thư mục overstack của dự án: chuẩn mới `.llmwiki` trước, `llmwiki` để tương thích ngược.
    Giữ đồng bộ với harness/scripts/overstack_paths.py::OVERSTACK_DIRS — đổi một nơi phải đổi
    nơi kia (harness-lint bắt hằng-số-lệch giữa script).

    Lưu ý glob (đo 2026-09-04, python 3.9): prefix dấu chấm VIẾT NGUYÊN VĂN thì `glob.glob`
    vẫn khớp bình thường — chỉ wildcard phải-khớp-dấu-chấm (`**/*.md` từ gốc) mới mù. Nên
    dựng prefix bằng hàm này là đủ, không cần đổi sang os.walk."""
    for name in (".llmwiki", "llmwiki"):
        if os.path.isdir(os.path.join(root, name)):
            return name
    return "llmwiki"

REMOTE_POLICY = ("https://raw.githubusercontent.com/Rheinmir/setup/orca/"
                 "harness/poc-vendor-neutral/policy.yaml")


def root():
    return os.environ.get("CLAUDE_PROJECT_DIR", ".")


def _stdin():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def _audit_dir():
    d = os.path.join(root(), ".claude/audit")
    os.makedirs(d, exist_ok=True)
    return d


# R4 — sinh log.md (người đọc được) từ audit.jsonl
def _machine_log():
    d = os.path.join(root(), ".claude/audit")
    jf = os.path.join(d, "audit.jsonl")
    if not os.path.exists(jf):
        return
    try:
        recs = [json.loads(x) for x in open(jf, encoding="utf-8") if x.strip()]
    except Exception:
        return
    out = ["# Machine log (R4 — sinh tự động từ audit.jsonl, đừng sửa tay)", ""]
    for e in recs[-300:]:
        out.append(f"- {e.get('ts', '')} · {e.get('tool', '')} · {e.get('path', '') or ''}".rstrip(" ·"))
    try:
        open(os.path.join(d, "log.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    except OSError:
        pass


def _gitignored(path, cwd):
    """True nếu path bị .gitignore loại (archive/draft/html local-only — khớp canonical
    index_sync.py: file gitignored KHÔNG bắt buộc có trong index). Fail-open: git lỗi → False."""
    try:
        import subprocess
        return subprocess.run(["git", "check-ignore", "-q", path],
                              cwd=cwd, capture_output=True, timeout=5).returncode == 0
    except Exception:
        return False


def m_stop():
    r = root()
    _machine_log()  # R4: làm tươi log.md cuối lượt
    idx = os.path.join(r, _overstack_prefix(r), "wiki", "index.md")
    if not os.path.exists(idx):
        return 0
    try:
        index = open(idx, encoding="utf-8").read()
    except OSError:
        return 0
    missing = []
    for sub in ("concepts", "entities", "sources", "draft", "architecture", "tours"):  # khớp global index_sync
        for f in glob.glob(os.path.join(r, _overstack_prefix(r), "wiki", sub, "**", "*.md"), recursive=True):
            base = os.path.basename(f)
            if base in ("README.md", "_template.md", "index.md", "log.md"):
                continue
            if base[:-3] not in index and not _gitignored(f, r):  # bỏ qua file gitignored (archive/draft local-only)
                missing.append(os.path.relpath(f, r))
    if missing:
        sys.stderr.write("[R3 index-sync] wiki/index.md chưa liệt kê: " + ", ".join(missing[:10]) +
                         ("…" if len(missing) > 10 else "") + " — cập nhật index trước khi kết thúc.\n")
        return 2
    return 0


def m_audit():
    data = _stdin()
    try:
        import datetime
        rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
               "tool": data.get("tool_name"),
               "path": (data.get("tool_input") or {}).get("file_path")}
        with open(os.path.join(_audit_dir(), "audit.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _machine_log()  # R4 full: log.md sinh từ jsonl
    except Exception:
        pass
    return 0


def m_session():
    pol = os.path.join(root(), "harness/poc-vendor-neutral/policy.yaml")
    n = 0
    try:
        import yaml
        n = len((yaml.safe_load(open(pol, encoding="utf-8")) or {}).get("rules", {}))
    except Exception:
        pass
    print(f"[harness] {n} rule đang gác (policy.yaml) — vi phạm bị hook chặn ngay. Kiểm hook: /hooks")
    # R8 full: check drift vs remote (best-effort, fail-open, tắt bằng LLMWIKI_NO_DRIFT=1)
    if os.environ.get("LLMWIKI_NO_DRIFT") != "1":
        try:
            import hashlib
            import urllib.request
            local = hashlib.md5(open(pol, "rb").read()).hexdigest()
            remote = hashlib.md5(urllib.request.urlopen(REMOTE_POLICY, timeout=2).read()).hexdigest()
            if local != remote:
                print("[harness R8] policy.yaml LỆCH remote — cập nhật: "
                      "curl -fsSL .../poc-vendor-neutral/bootstrap.sh | bash")
        except Exception:
            pass
    return 0


def m_docs():
    every = int(os.environ.get("LLMWIKI_DOCS_GATE_EVERY", "5") or 5)
    try:
        p = os.path.join(_audit_dir(), ".docs-gate.json")
        try:
            c = json.load(open(p)).get("n", 0)
        except Exception:
            c = 0
        c += 1
        json.dump({"n": c}, open(p, "w"))
        if every > 0 and c % every == 0:
            # R10 full: inject DIRECTIVE (UserPromptSubmit stdout → vào context → Claude hành động).
            # 2 trụ: TÀI LIỆU (docs-site-macos) + ĐÁNH GIÁ/eval (wikieval) — hỏi user TRƯỚC khi chạy nặng.
            print(f"[harness R10 docs-gate] Đã qua {every} lượt. ĐỀ NGHỊ với user 2 việc — hỏi trước khi chạy: "
                  f"(1) BỔ SUNG TÀI LIỆU cho {every} việc gần đây? Đồng ý → /docs-site-macos "
                  f"(hoặc /cursor-animated-sites cho luồng/sequence), rồi viết output-report (YAML frontmatter, OKF). "
                  f"(2) BỔ SUNG ĐÁNH GIÁ/eval? Đồng ý → skill `wikieval` thêm/chạy case cho phần vừa làm "
                  f"(output agent thì `trace-grader`/`council`). Từ chối → bỏ qua, không nhắc lại lượt này.")
    except Exception:
        pass
    return 0


def m_session_end():
    """R17 problem-tree-flush: phiên chạm framework mà sổ chưa cập nhật → append stub pending
    bằng code thuần (0 token). Fail-open mọi nhánh. Bản vendor-neutral của
    llmwiki/.claude/hooks/session_end.py::flush_problem_tree."""
    import datetime
    import re
    import subprocess
    r = root()
    tree = None
    for rel in (f"{_overstack_prefix(r)}/html/fdk-problem-tree.html",
                f"{_overstack_prefix(r)}/html/problem-tree.html"):
        if os.path.isfile(os.path.join(r, rel)):
            tree = os.path.join(r, rel)
            break
    if not tree:
        return 0
    try:
        diff = subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=r,
                              capture_output=True, text=True, timeout=10).stdout.split()
        st = subprocess.run(["git", "status", "--porcelain"], cwd=r,
                            capture_output=True, text=True, timeout=10).stdout
        touched = set(diff) | {l[3:] for l in st.splitlines() if l.startswith("?? ")}
    except Exception:
        return 0
    names = ("fdk-problem-tree.html", "problem-tree.html")
    fw = sorted(p for p in touched
                if p.startswith(("skills/", "harness/", ".harness/", "llmwiki/", ".llmwiki/", "fdk/")) and not p.endswith(names))
    if not fw or any(p.endswith(names) for p in touched):
        return 0
    try:
        html = open(tree, encoding="utf-8").read()
        m = re.search(r'(id="tree-data">\s*)(\[.*?\])(\s*</script>)', html, re.S)
        if not m:
            return 0
        nodes = json.loads(m.group(2))
        sid = (_stdin().get("session_id") or "unknown")[:8]
        # Một phiên chỉ được một thẻ. SessionEnd bắn nhiều lần cho cùng một phiên
        # (resume, thoát lại) → không chốt thì ra thẻ trùng khít; đã dính thật ở repo
        # framework: p-auto-21 ≡ p-auto-22, cùng phiên dba79064, 14/08/26.
        if any(x.get("session") == sid and x.get("pending") for x in nodes):
            return 0
        n = sum(1 for x in nodes if str(x.get("id", "")).startswith("p-auto-")) + 1
        nodes.append({
            "id": f"p-auto-{n:02d}", "parent": None,
            "title": "Thẻ ghi-tạm tự động: phiên chạm framework, chưa vào sổ",
            "desc": "Bề mặt bị chạm: " + ", ".join(fw[:8]) + (" …" if len(fw) > 8 else "")
                    + ". Thẻ do hook SessionEnd tự ghi (flush — xả sổ trước khi thoát).",
            "status": "open", "scope": [],
            "date": datetime.date.today().strftime("%d/%m/%y"),
            "session": sid, "pending": True,
        })
        out = html[:m.start(2)] + json.dumps(nodes, ensure_ascii=False, indent=1) + html[m.end(2):]
        open(tree, "w", encoding="utf-8").write(out)
    except Exception:
        pass
    return 0


def main():
    ev = sys.argv[1] if len(sys.argv) > 1 else ""
    fn = {"stop": m_stop, "audit": m_audit, "session": m_session, "docs": m_docs,
          "session-end": m_session_end}.get(ev)
    try:
        sys.exit(fn() if fn else 0)
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
