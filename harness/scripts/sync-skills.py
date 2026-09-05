#!/usr/bin/env python3
"""sync-skills — GIỮ 2 cây skill khớp nhau, chống drift (bài học 260626).

GỐC LỖI từng cắn: repo có 2 cây phát hành skill đọc từ 2 chỗ KHÁC nhau —
  • `npx skills add rheinmir/setup#<branch>`  → đọc `skills/<name>/SKILL.md`  (FLAT, canonical)
  • `sync-template.py` / bundle llmwiki        → đọc `llmwiki/skills/<loop>/<name>.md`
Sửa 1 cây quên cây kia → máy/dự án/phiên khác nhận bản cũ. Script này biến
`skills/` thành NGUỒN CHÂN LÝ và sinh `llmwiki/skills/` y hệt (chỉ khác vị trí loop).

Dùng:
  python3 harness/scripts/sync-skills.py            # GHI: sinh/cập nhật llmwiki/skills/ từ skills/
  python3 harness/scripts/sync-skills.py --check     # KIỂM: exit 1 nếu lệch (dùng trong CI)

Thêm skill mới: tạo `skills/<name>/SKILL.md`, (tùy) khai loop trong LOOP_MAP rồi chạy script.
Skill chưa khai loop → mặc định `utils` + cảnh báo.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "skills"                 # canonical (npx publish)
LLMWIKI = REPO / "llmwiki" / "skills"    # mirror (bundle llmwiki / sync-template)

# name → loop (thư mục trong llmwiki/skills/). Skill mới không khai → 'utils'.
LOOP_MAP = {
    # dev-loop
    "impact-check": "dev-loop", "new-project-setup": "dev-loop", "onboard-codebase": "dev-loop",
    "propose": "dev-loop", "plan": "dev-loop", "safe-change": "dev-loop",
    "verify-before-commit": "dev-loop", "build-now-adapt-later": "dev-loop", "ship": "dev-loop",
    "new-skill": "dev-loop", "loop-runner": "dev-loop", "failure-flywheel": "dev-loop", "wikieval": "dev-loop",
    "skill-provenance": "dev-loop", "qc-code": "dev-loop", "teach-me": "dev-loop",
    "doyourmagic": "dev-loop", "reskin": "dev-loop",
    # orchestrate
    "orca-dispatch-reference": "orchestrate", "orca-onboard": "orchestrate", "orca-issue": "orchestrate",
    "orca-handover": "orchestrate",
    "wayfinder": "orchestrate",
    "orca-sec-scans": "orchestrate", "orca-workflow": "orchestrate", "orca-eval": "orchestrate",
    "council": "orchestrate", "trace-grader": "orchestrate",
    # wiki-loop
    "ingest": "wiki-loop", "lint": "wiki-loop", "query": "wiki-loop", "wiki-room": "wiki-loop",
    "record-episode": "wiki-loop",
    # utils
    "agent-reach": "utils",
    "cavecrew": "utils", "caveman": "utils", "fable5": "utils", "graph-mode": "utils",
    "i-have-adhd": "utils", "caveman-commit": "utils", "caveman-compress": "utils",
    "caveman-help": "utils", "caveman-review": "utils", "caveman-stats": "utils",
    "extract-site": "utils", "harness-tour": "utils",
    "harness-update": "utils", "health-check": "utils", "fdk": "utils", "fdk-uat": "utils", "medic": "utils", "md-to-html": "utils",
    "docs-curate": "utils", "raise-issue": "utils",
    "frontier-scan": "utils", "ovs-notes": "utils",
    "sync-template": "utils", "uat-nonit-testcase": "utils", "cursor-animated-sites": "utils",
    # publish 260626 — skill trước LOCAL-ONLY (đẩy vào repo để không mất khi cài máy/dự án khác)
    "orca-cli": "orchestrate", "orchestration": "orchestrate", "jenkins-agent-l3-deploy": "orchestrate",
    "brandkit": "utils", "check-approve": "utils", "computer-use": "utils",
    "design-taste-frontend": "utils", "design-taste-frontend-v1": "utils", "docs-site-macos": "utils",
    "web-crawl": "utils", "web-clone": "utils", "hallmark": "utils", "diagram": "utils",
    "find-skills": "utils", "full-output-enforcement": "utils", "gpt-taste": "utils",
    "high-end-visual-design": "utils", "image-to-code": "utils", "imagegen-frontend-mobile": "utils",
    "imagegen-frontend-web": "utils", "industrial-brutalist-ui": "utils", "join-project": "utils",
    "last30days": "utils", "minimalist-ui": "utils", "redesign-existing-projects": "utils",
    "snapshot-push": "utils", "stitch-design-taste": "utils", "tour-guide-supademo": "utils",
    "tour-guide": "utils",
    "fable5": "utils",
}


def loop_of(name):
    return LOOP_MAP.get(name, "utils")


def pairs():
    """(name, skills_src_path, llmwiki_target_path) cho mọi skill canonical."""
    out = []
    for d in sorted(SKILLS.iterdir()):
        src = d / "SKILL.md"
        if d.is_dir() and src.is_file():
            out.append((d.name, src, LLMWIKI / loop_of(d.name) / f"{d.name}.md"))
    return out


def main():
    check = "--check" in sys.argv[1:]
    drift, wrote, unmapped = [], 0, []
    for name, src, tgt in pairs():
        if name not in LOOP_MAP:
            unmapped.append(name)
        s = src.read_text(encoding="utf-8")
        cur = tgt.read_text(encoding="utf-8") if tgt.exists() else None
        if cur == s:
            continue
        if check:
            drift.append(f"  {'MISSING' if cur is None else 'STALE  '} llmwiki/skills/{loop_of(name)}/{name}.md")
        else:
            tgt.parent.mkdir(parents=True, exist_ok=True)
            tgt.write_text(s, encoding="utf-8")
            wrote += 1
            print(f"  ✎ llmwiki/skills/{loop_of(name)}/{name}.md ← skills/{name}/SKILL.md")

    if unmapped:
        print("  ⚠ chưa khai loop (mặc định utils): " + ", ".join(unmapped), file=sys.stderr)
    if check:
        if drift:
            sys.stderr.write("[sync-skills] LỆCH — skills/ và llmwiki/skills/ không khớp:\n" +
                             "\n".join(drift) + "\n  → chạy: python3 harness/scripts/sync-skills.py\n")
            sys.exit(1)
        print("[sync-skills] ✓ 2 cây khớp.")
    else:
        print(f"[sync-skills] xong — {wrote} file cập nhật từ skills/ (canonical).")


if __name__ == "__main__":
    main()
