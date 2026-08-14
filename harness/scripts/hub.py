#!/usr/bin/env python3
"""hub — commit-DAG hub LOCAL: mỗi thí nghiệm của agent là MỘT commit, tra cứu bằng git ref.

Vì sao không cần server: các worktree Orca dùng chung một `.git` object store, nên commit của
agent A đã nhìn thấy được từ agent B — không có gì để "push/fetch" qua mạng. "Hub" vì thế chỉ
còn ba thứ tất định: một namespace ref `refs/hub/<agent>/<seq>` (NGOÀI `refs/heads` nên không
đụng nhánh, không cần main, không merge queue), một `git notes --ref=refs/hub` cất metadata của
node, và CLI mỏng này để hỏi DAG.

MẶC ĐỊNH TẮT. Không script nào `import hub` ở đầu file; loop-runner nạp module này ĐỘNG theo
đường dẫn và chỉ khi `hub.enabled` bật. Xoá file này đi thì mọi thứ còn lại chạy y nguyên —
xem `llmwiki/wiki/concepts/commit-dag-hub.md` mục "Cách tắt và cách gỡ bỏ hoàn toàn".

Notes JSON của mỗi node (field môi trường có NGAY từ commit đầu — nợ reproducibility của
PDF §IX.C: thêm sau thì mọi thí nghiệm cũ mất môi trường vĩnh viễn):
    {agent, hypothesis, metric, status, ts_utc, python, platform, deps_sha}

CLI:
    hub.py push --agent A --hypothesis "..." [--metric F] [--status S] [--commit SHA] [--root DIR]
    hub.py log [--by-metric] [--limit N] [--root DIR]      # bảng ref · agent · metric · status
    hub.py children <rev> [--root DIR]                     # node con trực tiếp trong tập hub
    hub.py leaves [--root DIR]                             # node chưa có con = biên chưa khám phá
    hub.py lineage <rev> [--root DIR]                      # chuỗi tổ tiên, con → gốc
    hub.py diff <a> <b> [--root DIR]                       # passthrough git diff --stat
    hub.py prune --keep-top K [--older-than N] [--yes] [--root DIR]   # chặn DAG phình vô hạn
    hub.py purge [--yes] [--root DIR]                      # kill-switch: xoá sạch dữ liệu hub
    hub.py --self-test

Hạn chế đã biết: notes gắn theo COMMIT, nên hai ref trỏ cùng một commit dùng chung một note
(lần push sau ghi đè). Bình thường mỗi Trial là một commit riêng nên không gặp.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # fail-soft: hub + self-test không bao giờ phụ thuộc PyYAML
    yaml = None

HUB_REF_NS = "refs/hub"
NOTES_REF = "refs/notes/hub"
CONFIG_REL = "harness/hub.config.yaml"

# Dùng khi không đọc được config (thiếu file / thiếu PyYAML). Giá trị thật + ghi chú
# ASSUMPTION nằm trong harness/hub.config.yaml — đó mới là adapter, đây chỉ là fail-soft.
DEFAULTS = {"prune": {"keep_top": 20, "older_than_days": 0}, "log": {"limit": 50}}

# Ký tự an toàn cho một thành phần ref name; phần còn lại bị thay bằng '-'.
_REF_SAFE = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git(args, root, check=True):
    """git trong `root`. check=True → lỗi git thành RuntimeError để hub_push bắt và fail-open."""
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} -> {p.returncode}: {(p.stderr or '').strip()[:200]}")
    return p


def load_config(root):
    cfg = json.loads(json.dumps(DEFAULTS))
    p = Path(root) / CONFIG_REL
    if yaml is None or not p.is_file():
        return cfg
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return cfg
    for section, vals in data.items():
        if isinstance(vals, dict) and isinstance(cfg.get(section), dict):
            cfg[section].update(vals)
        else:
            cfg[section] = vals
    return cfg


def _safe_agent(agent: str) -> str:
    a = "".join(c if c in _REF_SAFE else "-" for c in (agent or "agent").strip())
    return a.strip("-.") or "agent"


def _env_stamp(root) -> dict:
    """Môi trường phải cất NGAY từ commit đầu — thêm sau là mất vĩnh viễn (PDF §IX.C)."""
    lock = next((p for p in ("uv.lock", "poetry.lock", "requirements.txt")
                 if (Path(root) / p).is_file()), None)
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "deps_sha": hashlib.sha1((Path(root) / lock).read_bytes()).hexdigest()[:12] if lock else None,
    }


# ── Ghi: một Trial = một node ───────────────────────────────────────────────
def hub_push(root, agent, hypothesis, metric=None, status="kept", commit=None):
    """Tạo `refs/hub/<agent>/<seq>` + notes JSON; trả tên ref.

    FAIL-OPEN TUYỆT ĐỐI: mọi Exception → trả None. Hub hỏng (không phải repo git, thiếu
    identity, ref bẩn…) KHÔNG bao giờ được làm gãy ratchet của caller.
    """
    try:
        agent = _safe_agent(agent)
        commit = commit or _git(["rev-parse", "HEAD"], root).stdout.strip()
        existing = _git(["for-each-ref", f"{HUB_REF_NS}/{agent}"], root).stdout.splitlines()
        ref = f"{HUB_REF_NS}/{agent}/{len(existing) + 1:04d}"
        note = {"agent": agent, "hypothesis": hypothesis, "metric": metric,
                "status": status, "ts_utc": _now_iso(), **_env_stamp(root)}
        _git(["update-ref", ref, commit], root)
        _git(["notes", f"--ref={NOTES_REF}", "add", "-f",
              "-m", json.dumps(note, ensure_ascii=False), commit], root)
        return ref
    except Exception:
        return None


# ── Đọc: ref + notes ────────────────────────────────────────────────────────
def read_note(root, commit) -> dict:
    p = _git(["notes", f"--ref={NOTES_REF}", "show", commit], root, check=False)
    if p.returncode != 0:
        return {}
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"raw": p.stdout.strip()}


def hub_refs(root):
    """[(sha, refname)] của mọi node hub, theo thứ tự ref name."""
    p = _git(["for-each-ref", "--format=%(objectname)\t%(refname)", HUB_REF_NS], root, check=False)
    out = []
    for ln in p.stdout.splitlines():
        if "\t" in ln:
            sha, ref = ln.split("\t", 1)
            out.append((sha.strip(), ref.strip()))
    return out


def hub_entries(root):
    entries = []
    for sha, ref in hub_refs(root):
        e = {"sha": sha, "ref": ref}
        e.update(read_note(root, sha))
        e.setdefault("metric", None)
        entries.append(e)
    return entries


def sort_entries(entries, by_metric=False):
    if by_metric:
        # metric None xuống cuối (không có điểm thì không thể xếp hạng), còn lại giảm dần.
        return sorted(entries,
                      key=lambda e: (e.get("metric") is not None, e.get("metric") or 0.0),
                      reverse=True)
    return sorted(entries, key=lambda e: e.get("ref", ""))


# ── Bốn truy vấn DAG ────────────────────────────────────────────────────────
def _parents(root, sha):
    out = _git(["rev-list", "--parents", "-n", "1", sha], root, check=False).stdout.split()
    return out[1:]  # phần tử đầu là chính nó


def hub_children(root, rev):
    """Node hub có `rev` là cha trực tiếp. Giới hạn trong tập hub — cây thí nghiệm, không phải cả repo."""
    target = _git(["rev-parse", rev], root).stdout.strip()
    seen, out = set(), []
    for sha, ref in hub_refs(root):
        if sha in seen:
            continue
        if target in _parents(root, sha):
            seen.add(sha)
            out.append((sha, ref))
    return out


def hub_leaves(root):
    """Node hub chưa là cha của node hub nào khác — chính là biên chưa khám phá."""
    shas = {sha for sha, _ in hub_refs(root)}
    parents = set()
    for sha in shas:
        parents.update(_parents(root, sha))
    return sorted(shas - parents)


def hub_lineage(root, rev):
    """Chuỗi tổ tiên theo topo-order: chính nó trước, gốc lịch sử sau cùng."""
    return _git(["rev-list", "--topo-order", rev], root).stdout.split()


def hub_diff(root, a, b):
    return _git(["diff", "--stat", a, b], root, check=False).stdout


# ── Kill-switch: prune (giữ top-K) + purge (xoá sạch) ────────────────────────
def _older_than(ts_utc, days):
    if not days:
        return True
    if not ts_utc:
        return False  # không biết tuổi → giữ lại, an toàn hơn xoá nhầm
    try:
        ts = datetime.strptime(ts_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return False
    return ts < datetime.now(timezone.utc) - timedelta(days=days)


def hub_prune(root, keep_top, older_than_days=0, apply=True):
    """Xoá ref ngoài top-K theo metric (chặn nợ "DAG phình vô hạn" của PDF §IX.C).

    `older_than_days > 0` thu hẹp thêm: chỉ xoá node ĐÃ đủ cũ. Trả danh sách ref bị xoá
    (hoặc SẼ bị xoá khi apply=False)."""
    ranked = sort_entries(hub_entries(root), by_metric=True)
    doomed = [e for e in ranked[max(0, keep_top):] if _older_than(e.get("ts_utc"), older_than_days)]
    refs = [e["ref"] for e in doomed]
    if apply:
        for ref in refs:
            _git(["update-ref", "-d", ref], root, check=False)
    return refs


def hub_purge(root, apply=False):
    """Gỡ TOÀN BỘ dữ liệu hub: mọi `refs/hub/*` + `refs/notes/hub`. apply=False = dry-run."""
    refs = [ref for _, ref in hub_refs(root)]
    if _git(["rev-parse", "--verify", NOTES_REF], root, check=False).returncode == 0:
        refs.append(NOTES_REF)
    if apply:
        for ref in refs:
            _git(["update-ref", "-d", ref], root, check=False)
    return refs


# ── CLI ─────────────────────────────────────────────────────────────────────
def cmd_push(root, args) -> int:
    ref = hub_push(root, args.agent, args.hypothesis, args.metric, args.status, args.commit)
    if ref is None:  # fail-open: cảnh báo, KHÔNG trả mã lỗi làm gãy caller
        print("[hub] không ghi được node (bỏ qua — fail-open)", file=sys.stderr)
        return 0
    print(ref)
    return 0


def cmd_log(root, args) -> int:
    entries = sort_entries(hub_entries(root), by_metric=args.by_metric)[:args.limit]
    if not entries:
        print("(hub rỗng)")
        return 0
    print(f"{'ref':<34} {'agent':<16} {'metric':>10}  {'status':<10} hypothesis")
    for e in entries:
        metric = "—" if e.get("metric") is None else f"{e['metric']:.4g}"
        print(f"{e['ref']:<34} {str(e.get('agent', '—')):<16} {metric:>10}  "
              f"{str(e.get('status', '—')):<10} {e.get('hypothesis', '')}")
    return 0


def cmd_children(root, args) -> int:
    kids = hub_children(root, args.rev)
    for sha, ref in kids:
        print(f"{sha}  {ref}")
    return 0 if kids else 1


def cmd_leaves(root, args) -> int:
    for sha in hub_leaves(root):
        print(sha)
    return 0


def cmd_lineage(root, args) -> int:
    for sha in hub_lineage(root, args.rev):
        print(sha)
    return 0


def cmd_diff(root, args) -> int:
    print(hub_diff(root, args.a, args.b), end="")
    return 0


def cmd_prune(root, args) -> int:
    cfg = load_config(root)["prune"]
    keep = args.keep_top if args.keep_top is not None else cfg.get("keep_top", 20)
    older = args.older_than if args.older_than is not None else cfg.get("older_than_days", 0)
    refs = hub_prune(root, keep, older, apply=args.yes)
    verb = "đã xoá" if args.yes else "SẼ xoá (dry-run — thêm --yes để thi hành)"
    print(f"[hub] {verb} {len(refs)} ref ngoài top-{keep}")
    for ref in refs:
        print(f"  {ref}")
    return 0


def cmd_purge(root, args) -> int:
    refs = hub_purge(root, apply=args.yes)
    verb = "đã xoá" if args.yes else "SẼ xoá (dry-run — thêm --yes để thi hành)"
    print(f"[hub] {verb} {len(refs)} ref")
    for ref in refs:
        print(f"  {ref}")
    return 0


# ── self-test ───────────────────────────────────────────────────────────────
def ck(name, cond, fails):
    print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
    if not cond:
        fails.append(name)


def _mk_git_sandbox(tmp):
    """Repo git dùng-một-lần với một commit mồi. Chép từ loop-runner selftest có chủ ý:
    hub phải tự kiểm được kể cả khi loop-runner vắng mặt (phụ thuộc một chiều)."""
    tmp = str(tmp)
    q = {"capture_output": True, "text": True}
    subprocess.run(["git", "init", "-q", tmp], check=True, **q)
    for k, v in (("user.email", "hub@selftest.local"),
                 ("user.name", "hub selftest"),
                 ("commit.gpgsign", "false")):
        subprocess.run(["git", "-C", tmp, "config", k, v], check=True, **q)
    (Path(tmp) / "w.txt").write_text("seed")
    subprocess.run(["git", "-C", tmp, "add", "-A"], check=True, **q)
    subprocess.run(["git", "-C", tmp, "commit", "-qm", "seed"], check=True, **q)


def _commit(root, name, body):
    q = {"capture_output": True, "text": True}
    (Path(root) / name).write_text(body)
    subprocess.run(["git", "-C", str(root), "add", "-A"], **q)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", f"add {name}"], **q)
    return _git(["rev-parse", "HEAD"], root).stdout.strip()


def _load_loop_runner():
    """Nạp loop-runner ĐỘNG (tên file có dấu gạch ngang). Chỉ dùng trong self-test để chứng
    minh nhánh opt-in thật sự chạy — runtime vẫn là phụ thuộc MỘT CHIỀU loop-runner → hub."""
    import importlib.util
    p = Path(__file__).resolve().parent / "loop-runner.py"
    if not p.is_file():
        return None
    spec = importlib.util.spec_from_file_location("loop_runner_for_hub_test", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def self_test() -> int:
    import shutil as sh

    fails = []
    tmp = Path(tempfile.mkdtemp())
    root = tmp / "repo"
    _mk_git_sandbox(root)
    seed = _git(["rev-parse", "HEAD"], root).stdout.strip()

    p_sha = _commit(root, "p.txt", "p")
    ref_p = hub_push(root, "agent-a", "gia thuyet P: cache theo path la du", metric=1.0)
    ck("push tạo ref refs/hub/<agent>/0001", ref_p == f"{HUB_REF_NS}/agent-a/0001", fails)

    note = read_note(root, p_sha)
    ck("notes đọc lại được, đúng hypothesis đã push",
       note.get("hypothesis", "").startswith("gia thuyet P"), fails)
    ck("notes có ĐỦ field môi trường (python/platform/deps_sha) ngay từ commit đầu",
       {"python", "platform", "deps_sha"} <= set(note), fails)
    ck("field python là phiên bản interpreter thật", note.get("python") == platform.python_version(), fails)

    _git(["checkout", "-q", "-b", "b1", p_sha], root)
    c1 = _commit(root, "c1.txt", "1")
    hub_push(root, "agent-a", "nhanh 1: doi thuat toan", metric=3.0)
    _git(["checkout", "-q", "-b", "b2", p_sha], root)
    c2 = _commit(root, "c2.txt", "2")
    hub_push(root, "agent-b", "nhanh 2: doi cau truc du lieu", metric=2.0, status="discarded")

    kids = hub_children(root, p_sha)
    ck("children: thấy đúng 2 nhánh con từ cùng một cha",
       sorted(s for s, _ in kids) == sorted([c1, c2]), fails)
    ck("leaves: chỉ commit chưa có con (cha đã có con bị loại)",
       set(hub_leaves(root)) == {c1, c2}, fails)

    lin = hub_lineage(root, c1)
    ck("lineage: đúng thứ tự con → cha → gốc",
       lin[0] == c1 and lin[1] == p_sha and lin[-1] == seed, fails)
    ck("diff: passthrough git diff --stat giữa hai node", "c1.txt" in hub_diff(root, p_sha, c1), fails)

    ordered = [e.get("metric") for e in sort_entries(hub_entries(root), by_metric=True)]
    ck("log --by-metric sắp xếp metric giảm dần", ordered == [3.0, 2.0, 1.0], fails)

    deleted = hub_prune(root, keep_top=2)
    ck("prune --keep-top 2 giữ đúng top-2 theo metric, xoá 1",
       len(deleted) == 1 and {e.get("metric") for e in hub_entries(root)} == {3.0, 2.0}, fails)

    would = hub_purge(root, apply=False)
    ck("purge KHÔNG --yes = dry-run, không đụng ref nào",
       len(would) >= 2 and len(hub_refs(root)) == 2, fails)

    ck("fail-open: push vào thư mục không phải git repo → None, không raise",
       hub_push(tmp / "khong-phai-repo", "x", "y") is None, fails)

    lr = _load_loop_runner()
    if lr is None:
        ck("wiring: tìm thấy loop-runner.py để kiểm nhánh opt-in", False, fails)
    else:
        wr = tmp / "wire"
        _mk_git_sandbox(wr)
        _commit(wr, "n", "0")  # loop-runner's ratchet now requires a clean tree at start
        metric_up = lr._py(
            "import pathlib;"
            f"p=pathlib.Path({json.dumps(str(wr / 'n'))});"
            "v=int(p.read_text() or 0)+1;p.write_text(str(v));print(v)"
        )
        log = lr.run_loop(
            verify_cmd=lr._py("import sys;sys.exit(1)"), max_iter=2, no_progress_k=0,
            state_paths=[], cwd=str(wr), metric_cmd=metric_up, direction="max",
            no_improve_k=3, hub_enabled=True, hub_agent="loop-runner", quiet=True,
        )
        in_log = [r.get("hub_ref") for r in log["iterations"] if r.get("iter")]
        ck("wiring: hub BẬT → mỗi Trial ghi một node hub (run-log có hub_ref)",
           len(hub_refs(wr)) == 2 and len(in_log) == 2 and all(in_log), fails)

    purged = hub_purge(root, apply=True)
    refs_left = _git(["for-each-ref", HUB_REF_NS], root, check=False).stdout.strip()
    notes_gone = _git(["rev-parse", "--verify", NOTES_REF], root, check=False).returncode != 0
    ck("purge --yes xoá sạch refs/hub/* VÀ refs/notes/hub",
       len(purged) >= 2 and refs_left == "" and notes_gone, fails)

    sh.rmtree(tmp, ignore_errors=True)
    print(f"\nSELF-TEST: {'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


def build_parser():
    import argparse

    ap = argparse.ArgumentParser(prog="hub.py", description="commit-DAG hub LOCAL (opt-in, gỡ được sạch)")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    common = argparse.ArgumentParser(add_help=False)   # --root dùng chung mọi subcommand
    common.add_argument("--root", default=".")

    p = sub.add_parser("push", parents=[common], help="ghi một Trial thành node hub")
    p.add_argument("--agent", required=True)
    p.add_argument("--hypothesis", required=True)
    p.add_argument("--metric", type=float, default=None)
    p.add_argument("--status", default="kept")
    p.add_argument("--commit", default=None)
    p.set_defaults(func=cmd_push)

    p = sub.add_parser("log", parents=[common], help="bảng node hub")
    p.add_argument("--by-metric", action="store_true", help="sắp xếp theo metric giảm dần")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("children", parents=[common], help="node hub con trực tiếp của <rev>")
    p.add_argument("rev")
    p.set_defaults(func=cmd_children)

    p = sub.add_parser("leaves", parents=[common], help="node hub chưa có con (biên chưa khám phá)")
    p.set_defaults(func=cmd_leaves)

    p = sub.add_parser("lineage", parents=[common], help="chuỗi tổ tiên của <rev>, con → gốc")
    p.add_argument("rev")
    p.set_defaults(func=cmd_lineage)

    p = sub.add_parser("diff", parents=[common], help="git diff --stat giữa hai node")
    p.add_argument("a")
    p.add_argument("b")
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser("prune", parents=[common], help="giữ top-K theo metric, xoá phần còn lại")
    p.add_argument("--keep-top", type=int, default=None)
    p.add_argument("--older-than", type=int, default=None, help="chỉ xoá node cũ hơn N ngày")
    p.add_argument("--yes", action="store_true", help="thi hành thật (mặc định dry-run)")
    p.set_defaults(func=cmd_prune)

    p = sub.add_parser("purge", parents=[common], help="kill-switch: xoá sạch refs/hub/* + refs/notes/hub")
    p.add_argument("--yes", action="store_true", help="thi hành thật (mặc định dry-run)")
    p.set_defaults(func=cmd_purge)

    return ap


def main():
    ap = build_parser()
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if not getattr(args, "func", None):
        ap.print_help()
        sys.exit(1)
    sys.exit(args.func(Path(args.root), args))


if __name__ == "__main__":
    main()
