#!/usr/bin/env python3
"""skill-provenance — sổ nguồn gốc + toàn vẹn (sha256) cho từng skill (GH#13).

VÌ SAO: overstack cài/chưng cất skill từ nhiều nguồn (tự viết, kéo từ marketplace
ngoài, distill trong phiên dự án khác). `orca-sec-scans` quét vuln/secret NỘI DUNG,
nhưng không trả lời "skill này TỪ ĐÂU tới" và "có bị sửa lén sau khi cài không".
Script này là lớp provenance bổ trợ: ghi nguồn + checksum lúc cài, rồi verify
checksum bất cứ lúc nào để phát hiện skill bị sửa ngoài luồng (supply-chain drift).

Thuần stdlib, offline, no-LLM. Store = fdk/skills.provenance.json:
    { "schema": "skill-provenance/v1",
      "skills": { "<name>": {
          "source": "<url|repo#ref|local-authored>",
          "recorded": "<YYYY-MM-DD>",
          "files": { "SKILL.md": "<sha256>", ... } } } }

VERBS:
    record <name> --source <src>     # sha256 mọi file trong skills/<name>/, ghi entry
    record --all --source local-authored   # backfill toàn bộ skill hiện có (một lần)
    check [name]                     # recompute; báo MODIFIED / UNTRACKED / MISSING
    check --ci                       # exit 1 nếu có MODIFIED hoặc UNTRACKED (cho CI)
    list                             # in bảng name → source → #files
    --self-test                      # kiểm bất biến nội bộ, không đụng đĩa thật

STATUS (verb check):
    OK        — mọi file khớp checksum đã ghi.
    MODIFIED  — file có checksum khác entry (bị sửa sau khi record).
    UNTRACKED — skill có trên đĩa nhưng CHƯA có provenance (chưa ai record).
    MISSING   — entry có trong sổ nhưng skills/<name>/ không còn trên đĩa.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "skills"
STORE = REPO / "fdk" / "skills.provenance.json"
SCHEMA = "skill-provenance/v1"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def skill_files(name: str) -> dict[str, str]:
    """{relpath-trong-skill-dir: sha256} cho file skill được PUBLISH (= file có trong git).

    Chỉ băm file GIT TRACKED. Trước đây `rglob("*")` băm mọi thứ trên đĩa, gồm cả artifact
    KHÔNG commit — vd `skills/visual-qa/assets/node_modules/` (13 MB, 0 file tracked, có symlink):
    máy dev đã `npm install` thì hash có nó, CI clone sạch thì không ⇒ **MODIFIED lệch vĩnh viễn,
    không ai sửa được**. Sổ provenance là "nguồn gốc của thứ ship ra", nên phải bám git — thứ
    không được publish thì không thuộc chủ quyền của sổ. (Bắt 17/07/26 khi CI PR #78 đỏ.)
    Fail-open: git lỗi → quay về quét đĩa (giữ hành vi cũ, không chặn).
    """
    root = SKILLS / name
    try:
        out = subprocess.run(["git", "ls-files", "-z", "--", f"skills/{name}"],
                             cwd=REPO, capture_output=True, text=True, check=True).stdout
        rels = [x for x in out.split("\0") if x]
        if rels:
            return {str(Path(r).relative_to(f"skills/{name}")): _sha256(REPO / r)
                    for r in sorted(rels) if (REPO / r).is_file()}
    except Exception:
        pass
    return {str(p.relative_to(root)): _sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


def load_store() -> dict:
    if not STORE.exists():
        return {"schema": SCHEMA, "skills": {}}
    data = json.loads(STORE.read_text(encoding="utf-8"))
    data.setdefault("skills", {})
    return data


def save_store(data: dict) -> None:
    data["schema"] = SCHEMA
    STORE.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                     encoding="utf-8")


def on_disk_skills() -> list[str]:
    return sorted(d.name for d in SKILLS.iterdir()
                  if d.is_dir() and (d / "SKILL.md").exists())


def cmd_record(a) -> int:
    data = load_store()
    if a.all:
        names = on_disk_skills()
    else:
        if not a.name:
            sys.exit("✗ record: cần <name> hoặc --all")
        names = [a.name]
    today = date.today().isoformat()
    for name in names:
        if not (SKILLS / name / "SKILL.md").exists():
            sys.exit(f"✗ skills/{name}/SKILL.md không tồn tại")
        # --all backfill: không đè source đã có (giữ nguồn thật đã ghi trước đó)
        if a.all and name in data["skills"] and data["skills"][name].get("source"):
            continue
        data["skills"][name] = {
            "source": a.source,
            "recorded": today,
            "files": skill_files(name),
        }
    save_store(data)
    print(f"✓ recorded {len(names)} skill(s) → {STORE.relative_to(REPO)}")
    return 0


def evaluate(data: dict):
    """Trả (rows, has_problem). rows = [(name, status, detail)]."""
    recorded = data["skills"]
    disk = set(on_disk_skills())
    rows, problem = [], False
    for name in sorted(disk | set(recorded)):
        if name not in recorded:
            rows.append((name, "UNTRACKED", "chưa có provenance"))
            problem = True
        elif name not in disk:
            rows.append((name, "MISSING", "entry còn nhưng skill đã xoá"))
            problem = True
        else:
            now = skill_files(name)
            saved = recorded[name].get("files", {})
            if now != saved:
                changed = sorted(set(now) ^ set(saved)) or \
                    [f for f in now if now[f] != saved.get(f)]
                rows.append((name, "MODIFIED", "lệch: " + ", ".join(changed[:4])))
                problem = True
            else:
                rows.append((name, "OK", recorded[name].get("source", "?")))
    return rows, problem


def cmd_check(a) -> int:
    data = load_store()
    rows, problem = evaluate(data)
    if getattr(a, "json", False):
        recorded = data["skills"]
        out = [{"name": n, "status": s, "detail": d,
                "source": recorded.get(n, {}).get("source"),
                "adapt_mode": recorded.get(n, {}).get("adapt_mode")} for n, s, d in rows]
        print(json.dumps({"schema": "skill-provenance-check/v1", "rows": out}, ensure_ascii=False))
        return 0
    if a.name:
        rows = [r for r in rows if r[0] == a.name]
        if not rows:
            sys.exit(f"✗ không có skill '{a.name}' trên đĩa lẫn trong sổ")
    bad = [r for r in rows if r[1] != "OK"]
    for name, status, detail in (bad if a.ci else rows):
        mark = "✓" if status == "OK" else "✗"
        print(f"  {mark} {status:9} {name}  — {detail}")
    if a.ci:
        # MISSING không phải lỗi CI (skill có thể được cố ý gỡ); chỉ MODIFIED/UNTRACKED chặn
        block = [r for r in bad if r[1] in ("MODIFIED", "UNTRACKED")]
        if block:
            print(f"\n✗ skill-provenance: {len(block)} vấn đề (MODIFIED/UNTRACKED) — "
                  f"chạy `record` để cập nhật sổ hoặc điều tra sửa đổi lạ.")
            return 1
        print(f"✓ skill-provenance: {len(rows)} skill, checksum khớp, không skill lạ.")
    return 0


def cmd_list(a) -> int:
    data = load_store()
    for name in sorted(data["skills"]):
        e = data["skills"][name]
        print(f"  {name:32}  {e.get('source','?'):22}  {len(e.get('files',{}))} file  "
              f"({e.get('recorded','?')})")
    print(f"\n  {len(data['skills'])} skill có provenance.")
    return 0


def self_test() -> int:
    # sha256 ổn định + evaluate phân loại đúng trên store giả.
    assert _sha256(Path(__file__)) == _sha256(Path(__file__))
    disk = set(on_disk_skills())
    assert disk, "phải thấy ít nhất 1 skill trên đĩa"
    sample = sorted(disk)[0]
    fake = {"schema": SCHEMA, "skills": {
        sample: {"source": "x", "recorded": "2026-01-01", "files": skill_files(sample)},
        "__ghost__": {"source": "y", "recorded": "2026-01-01", "files": {"SKILL.md": "00"}},
    }}
    rows, problem = evaluate(fake)
    by = {r[0]: r[1] for r in rows}
    assert by[sample] == "OK", by[sample]
    assert by["__ghost__"] == "MISSING", by.get("__ghost__")
    # skill khác trên đĩa (không phải sample) phải UNTRACKED
    others = [n for n in disk if n != sample]
    if others:
        assert by[others[0]] == "UNTRACKED", by[others[0]]
    assert problem is True
    print("✓ self-test passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="skill-provenance.py",
                                 description="Sổ nguồn gốc + checksum cho skill (GH#13).")
    ap.add_argument("--self-test", action="store_true", help="kiểm bất biến nội bộ")
    sub = ap.add_subparsers(dest="verb")

    p_rec = sub.add_parser("record", help="ghi provenance cho 1 skill (hoặc --all)")
    p_rec.add_argument("name", nargs="?", help="tên skill; bỏ trống khi dùng --all")
    p_rec.add_argument("--all", action="store_true", help="backfill mọi skill hiện có")
    p_rec.add_argument("--source", required=True, help="nguồn: url | repo#ref | local-authored")

    p_chk = sub.add_parser("check", help="verify checksum + phát hiện skill lạ")
    p_chk.add_argument("name", nargs="?", help="giới hạn 1 skill")
    p_chk.add_argument("--ci", action="store_true", help="exit 1 nếu MODIFIED/UNTRACKED")
    p_chk.add_argument("--json", action="store_true",
                       help="in rows kèm source/adapt_mode — để medic phân biệt "
                            "external-pull (rủi ro thật) với local-authored (dev churn bình thường)")

    sub.add_parser("list", help="liệt kê provenance đã ghi")

    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.verb == "record":
        return cmd_record(a)
    if a.verb == "check":
        return cmd_check(a)
    if a.verb == "list":
        return cmd_list(a)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
