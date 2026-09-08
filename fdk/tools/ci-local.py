#!/usr/bin/env python3
"""ci-local — chạy TRỌN các step `run:` của mọi workflow GitHub tại local, trước khi push.

Vì sao: medic --ci và pre-commit là L2; CI fresh-clone là L4 và có gate CHỈ ở đó (search-index,
skill-provenance, retrieval-eval…). Đã cháy 2026-09-08: medic xanh, push, CI đỏ 2 job. Dặn
"nhớ chạy trọn job repo-health" là bậc đòn bẩy thấp nhất; script này biến lời dặn thành lệnh.

  python3 fdk/tools/ci-local.py            # chạy hết, in ✓/✗ từng step, exit 1 nếu có ✗
  python3 fdk/tools/ci-local.py --list     # chỉ liệt kê step sẽ chạy
  python3 fdk/tools/ci-local.py --job repo-health --workflow harness.yml
  python3 fdk/tools/ci-local.py --self-test

Bỏ qua step cài đặt/đẩy (pip, npm ci, npx skills, git push/config/commit, actions/*): chúng là
việc của runner, không phải gate. RUNNER_TEMP được set vì vài step ghi vào đó.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("ci-local: cần PyYAML (pip install pyyaml)")

SKIP_PREFIX = ("pip ", "pip3 ", "npm ci", "npm install", "npx skills", "git push", "git config", "git commit", "gh ")
ROOT = Path(__file__).resolve().parents[2]


def steps(workflow_dir=ROOT / ".github" / "workflows", only_wf=None, only_job=None):
    out = []
    for wf in sorted(workflow_dir.glob("*.yml")):
        if only_wf and wf.name != only_wf:
            continue
        data = yaml.safe_load(wf.read_text()) or {}
        for jname, job in (data.get("jobs") or {}).items():
            if only_job and jname != only_job:
                continue
            for st in job.get("steps") or []:
                cmd = st.get("run")
                if not cmd or cmd.strip().startswith(SKIP_PREFIX):
                    continue
                out.append((wf.name, jname, st.get("name") or cmd.strip().splitlines()[0][:70], cmd))
    return out


def run(items, verbose_fail=6):
    env = dict(os.environ, RUNNER_TEMP=tempfile.mkdtemp(prefix="ci-local-"), CI="true")
    fails = []
    for wf, job, name, cmd in items:
        r = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, env=env, cwd=ROOT)
        ok = r.returncode == 0
        print(f"{'✓' if ok else '✗'} {wf}:{job} · {name}")
        if not ok:
            fails.append((wf, job, name, (r.stdout + r.stderr).strip().splitlines()[-verbose_fail:]))
    for wf, job, name, tail in fails:
        print(f"\n--- ✗ {wf}:{job} · {name}\n" + "\n".join(tail))
    print(f"\nci-local: {len(items) - len(fails)}/{len(items)} step xanh" + (" — KHÔNG push" if fails else " — đủ điều kiện push (L4 tại local)"))
    return 1 if fails else 0


def self_test():
    items = steps()
    assert len(items) >= 10, f"phát hiện quá ít step: {len(items)}"
    assert any(j == "repo-health" for _, j, _, _ in items), "thiếu job repo-health"
    assert not any(c.strip().startswith("pip ") for *_, c in items), "step pip phải bị bỏ qua"
    # smoke thật trên một step rẻ, chứng minh runner chạy được chứ không chỉ liệt kê
    cheap = [i for i in items if "capabilities current" in i[2]]
    assert cheap and run(cheap) == 0, "step 'capabilities current' phải xanh"
    print("ci-local --self-test: 4/4 ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--workflow")
    ap.add_argument("--job")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    items = steps(only_wf=a.workflow, only_job=a.job)
    if a.list:
        for wf, job, name, _ in items:
            print(f"{wf}:{job} · {name}")
        print(f"{len(items)} step")
        return
    sys.exit(run(items))


if __name__ == "__main__":
    main()
