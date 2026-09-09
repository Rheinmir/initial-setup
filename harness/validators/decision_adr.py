#!/usr/bin/env python3
"""R13 decision→ADR gate + vòng đời ADR (create/edit/supersede-delete).

Ép quyết định KIẾN TRÚC phải có ADR, nhưng KHÔNG làm ADR bất biến cứng — cho EDIT thoải mái
và cho XÓA khi đã bị đè (superseded). Ba luật:

  (1) DECISION→ADR  — mỗi row Type='architecture' trong decisions.md phải trỏ một 'ADR-N'
      ở cột Outcome, hoặc khai rõ '(no-adr: <lý do>)'. Ép: quyết định lớn → có bản ghi ADR.

  (2) EDIT tự do    — sửa NỘI DUNG một ADR không bao giờ bị chặn (validator chỉ soi linkage
      + xóa). Tinh chỉnh status/Context/Decision thoải mái.

  (3) DELETE-NEEDS-SUPERSEDE — xóa một file ADR khỏi git CHỈ hợp lệ khi nó đã bị ĐÈ:
      nội dung cũ có 'Superseded by ADR-M', HOẶC một ADR còn lại ghi 'supersede(s) ADR-N'.
      Chống mất quyết định còn sống; cho phép dọn ADR đã lỗi thời.

Contract:
  decision_adr.py <files...>        # pre-commit per-file: soi decisions.md đổi
  decision_adr.py --guard-deletions # pre-commit always_run: bắt ADR bị xóa (git staged)
Exit 0 = ok, 2 = vi phạm. Fail-open ở nhánh git (mạng/không-repo → bỏ qua).
"""
import os
import re
import subprocess
import sys
from pathlib import Path

ADR_REF = re.compile(r"ADR-\d+", re.IGNORECASE)
ARCH_TYPES = ("architecture",)  # chỉ ép ADR cho quyết định kiến trúc; rule/gate/design/docs/test miễn
SUPERSEDED_BY = re.compile(r"supersed\w*\s+by\s+ADR-\d+", re.IGNORECASE)


def check_decisions(path: str) -> list:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return []
    bad = []
    for ln in text.splitlines():
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        _date, decision, typ, _ctx, outcome = cells[:5]
        if "---" in decision or decision.lower() == "decision":
            continue  # header / separator
        if typ.lower() in ARCH_TYPES:
            if not ADR_REF.search(outcome) and "no-adr" not in outcome.lower():
                bad.append(f"  • '{decision[:48]}' (architecture) — cột Outcome thiếu 'ADR-N' "
                           f"(promote /tidy hoặc /adr new) hoặc khai '(no-adr: <lý do>)'")
    return bad


def _adr_dirs(root: Path):
    return [d for d in (root / "fdk/wiki/sources/adr", root / "llmwiki/wiki/sources/adr") if d.is_dir()]


def guard_deletions(root: Path) -> list:
    try:
        diff = subprocess.run(["git", "diff", "--cached", "--name-status"], cwd=str(root),
                              capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []  # fail-open
    deleted = []
    for l in diff.splitlines():
        parts = l.split("\t")
        if parts and parts[0] == "D" and len(parts) > 1:
            p = parts[1].replace("\\", "/")
            if "/sources/adr/ADR-" in p:
                deleted.append(p)
    if not deleted:
        return []
    remaining = ""
    for d in _adr_dirs(root):
        for f in d.glob("ADR-*.md"):
            try:
                remaining += f.read_text(encoding="utf-8", errors="replace") + "\n"
            except OSError:
                pass
    bad = []
    for path in deleted:
        m = ADR_REF.search(path)
        adrn = m.group(0) if m else None
        try:
            old = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=str(root),
                                capture_output=True, text=True, timeout=10).stdout
        except Exception:
            old = ""
        was_superseded = bool(SUPERSEDED_BY.search(old))
        overridden = bool(adrn and re.search(rf"supersed\w*[^\n]*{re.escape(adrn)}\b", remaining, re.IGNORECASE))
        if not (was_superseded or overridden):
            bad.append(f"  • {path} — XÓA ADR còn LIVE: phải bị đè trước (status 'Superseded by ADR-M', "
                       f"hoặc một ADR khác ghi 'supersedes {adrn or 'ADR-N'}'). Dùng /adr supersede.")
    return bad


def main() -> None:
    args = sys.argv[1:]
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
    problems = []
    if "--guard-deletions" in args:
        problems += guard_deletions(root)
    for p in args:
        if p.startswith("-"):
            continue
        if Path(p).name == "decisions.md":
            problems += check_decisions(p)
    if problems:
        print("[R13 decision→ADR] vi phạm vòng đời quyết định/ADR:\n" + "\n".join(problems), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
