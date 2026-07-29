#!/usr/bin/env python3
"""br-queue — resumable RUN QUEUE for /br run (GH#15), scheduled as a DAG (GH#75).

A queue file (br/queue.yaml) is a LIST of frames to run. Each entry points at a
frame and — optionally — a prompt: either `prompt_file` (a template path) or
`prompt` (inline text written straight into the queue). The driver runs entries in
order, writes each entry's outcome (status/verdict/commit) BACK to the queue file
after every run, so re-running the queue SKIPS `done` entries and continues where it
left off (resume).

The order is NOT the order you happened to type. Each frame declares `depends_on:
[frame_id, ...]` in its frontmatter (frame-lint R5 already rejects cycles), so the
queue is a DAG and the driver runs it in topological order (declaration order breaks
ties, so a queue with no deps behaves exactly as before). Two consequences, both from
Atomic Task Graph (arXiv 2607.01942):

  • A frame that fails BLOCKS its whole downstream subgraph — those frames are marked
    `blocked` and never run, because their input is broken. Running them would burn a
    model call to produce a failure we can already predict.
  • `affected <frame_id>` names the subgraph a change ripples into (that frame plus
    everything transitively downstream). `--reset` puts exactly those back to pending,
    so re-running the queue repairs THAT SUBGRAPH instead of the whole line.

NOT implemented, deliberately: subgraph reuse (caching a green frame by input hash).
At our scale — tens of frames, not thousands of nodes — `status: done` already skips
them, and a hash cache would buy nothing but a staleness bug. The paper's own limits
apply here too: this scheduling only pays off while the graph is small and the
acceptance tests are deterministic.

DETERMINISTIC (built + selftested here): parsing the queue, resolving each entry's
prompt (inline > prompt_file > default template), topological order, downstream
blocking, affected-subgraph computation, skip-done resume logic, and writing the queue
back. QUARANTINED (verified:false): the per-frame run itself (loop-runner + `claude -p`
revise) — injected as `runner_fn` so the queue logic is testable without a model.

Usage:
  br-queue.py run      --queue br/queue.yaml [--root .] [--stop-on-fail] [--dry-run]
  br-queue.py list     --queue br/queue.yaml
  br-queue.py affected <frame_id> --queue br/queue.yaml [--root .] [--reset]
  br-queue.py selftest
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
_FL = _HERE.with_name("frame-lint.py")
_spec = importlib.util.spec_from_file_location("frame_lint", _FL)
_frame_lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frame_lint)
parse_frontmatter = _frame_lint.parse_frontmatter

DEFAULT_TEMPLATE = _REPO / "skills" / "br" / "assets" / "revise-prompt.md"
LOOP_RUNNER = _REPO / "harness" / "scripts" / "loop-runner.py"
BR_REVISE = _REPO / "fdk" / "tools" / "br-revise.py"
_QHEADER = ("# QUEUE prompt cho /br run — driver: fdk/tools/br-queue.py (resumable).\n"
            "# status: pending|done|failed do driver TỰ cập nhật. Chạy lại = bỏ qua done, chạy tiếp.\n")


def load_queue(path):
    if yaml is None:
        raise RuntimeError("PyYAML required to read the queue file")
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("queue must be a YAML list of entries")
    return data


def save_queue(path, entries):
    body = yaml.safe_dump(entries, allow_unicode=True, sort_keys=False, default_flow_style=False)
    Path(path).write_text(_QHEADER + body, encoding="utf-8")


def _frame_path(entry, root):
    p = Path(entry["frame"])
    return p if p.is_absolute() else Path(root) / p


def load_graph(entries, root):
    """Read each entry's frame frontmatter → (frame_ids, deps, errors) keyed by queue index.

    deps[i] = the frame_ids entry i depends on, RESTRICTED to frames present in this
    queue (a dep on a frame outside the queue is someone else's business — same call
    frame-lint's cycle check makes). Frames that fail to parse get frame_id None; the
    caller falls back to declaration order for them rather than refusing to run.
    """
    fids, raw_deps, errors = {}, {}, {}
    for i, e in enumerate(entries):
        try:
            fm = parse_frontmatter(_frame_path(e, root).read_text(encoding="utf-8"))
            fids[i] = fm.get("frame_id")
            raw_deps[i] = list(fm.get("depends_on") or [])
        except (OSError, ValueError, KeyError) as exc:
            errors[i] = str(exc)
            fids[i] = None
            raw_deps[i] = []
    in_queue = {f for f in fids.values() if f}
    deps = {i: [d for d in raw_deps[i] if d in in_queue and d != fids[i]] for i in fids}
    return fids, deps, errors


def topo_order(entries, fids, deps):
    """Kahn, with declaration order as the tie-break → a dep-free queue keeps its old order.

    A cycle should be impossible (frame-lint R5 gates it), but if one slips through we
    do NOT hang or drop frames: the remaining entries are appended in declaration order
    and the caller warns. Fail-open — a scheduling bug must never eat a frame.
    """
    idx_of = {f: i for i, f in fids.items() if f}
    pending = {i: {idx_of[d] for d in deps[i] if d in idx_of} for i in range(len(entries))}
    order, done = [], set()
    while len(order) < len(entries):
        ready = [i for i in range(len(entries)) if i not in done and not (pending[i] - done)]
        if not ready:                                  # cycle — take the rest as declared
            order += [i for i in range(len(entries)) if i not in done]
            return order, True
        order.append(ready[0])
        done.add(ready[0])
    return order, False


def downstream(target_fids, fids, deps):
    """Every queue index that depends on any of `target_fids`, transitively (the subgraph
    a failure poisons / a change ripples into). Excludes the targets themselves."""
    hit, frontier = set(), set(target_fids)
    while frontier:
        nxt = set()
        for i, dl in deps.items():
            if i in hit or fids.get(i) in target_fids:
                continue
            if frontier & set(dl):
                hit.add(i)
                if fids.get(i):
                    nxt.add(fids[i])
        frontier = nxt
    return hit


def resolve_prompt(entry, tmpdir, idx):
    """inline `prompt` > `prompt_file` > default template. Returns a template path."""
    inline = entry.get("prompt")
    if inline is not None and str(inline).strip():
        p = Path(tmpdir) / f"entry-{idx}.prompt.md"
        p.write_text(str(inline), encoding="utf-8")
        return str(p), "inline"
    pf = entry.get("prompt_file")
    if pf:
        return str(pf), "prompt_file"
    return str(DEFAULT_TEMPLATE), "default"


def _default_runner(entry, frame_fm, template_path, root):
    """Per-frame run — delegates to br-run (frame-lint gate + clean-tree check +
    bookkeeping commit, so 40 frames in a row don't pollute each other's commits).
    Optional entry field `revise_cmd:` overrides the LLM adapter (stubs/tests)."""
    fid = frame_fm.get("frame_id", "frame")
    frame_path = entry["frame"] if Path(entry["frame"]).is_absolute() else str(Path(root) / entry["frame"])
    cmd = ["python3", str(_HERE.with_name("br-run.py")), "run", frame_path,
           "--root", str(root), "--template", str(template_path)]
    if entry.get("revise_cmd"):
        cmd += ["--revise-cmd", str(entry["revise_cmd"])]
    subprocess.run(cmd, capture_output=True, text=True)
    log_path = Path(root) / "br" / "frames" / f"{fid}.run.json"
    if log_path.exists():
        d = json.loads(log_path.read_text(encoding="utf-8"))
        return {"verdict": d.get("verdict"), "commit": d.get("commit"),
                "scope_clean": d.get("scope_clean"), "changed_files": d.get("changed_files")}
    return {"verdict": "ERROR", "commit": None}


def run_queue(queue_path, root=".", stop_on_fail=False, dry_run=False, runner_fn=None):
    entries = load_queue(queue_path)
    runner_fn = runner_fn or _default_runner
    fids, deps, _errs = load_graph(entries, root)
    order, cyclic = topo_order(entries, fids, deps)
    if cyclic:
        print("  [warn] depends_on có CHU TRÌNH — chạy theo thứ tự khai báo. "
              "Chạy `frame-lint check` để tìm vòng lặp.")
    ran, skipped, blocked = 0, 0, 0
    poisoned = set()          # frame_ids that failed this run → their subgraph must not run
    with tempfile.TemporaryDirectory() as td:
        for i in order:
            entry = entries[i]
            fid = entry.get("frame", f"#{i}")
            if entry.get("status") == "done":
                skipped += 1
                print(f"  [skip] {fid} (done)")
                continue
            broken = poisoned & set(deps[i])
            if broken:
                # Localized repair (ATG): the input to this frame is broken, so running it
                # would burn a model call on a failure we can already predict. Mark and move on.
                entry["status"] = "blocked"
                entry["blocked_by"] = sorted(broken)
                entry.pop("verdict", None)
                blocked += 1
                if fids.get(i):
                    poisoned.add(fids[i])
                if not dry_run:
                    save_queue(queue_path, entries)
                print(f"  [blocked] {fid}: chờ {', '.join(sorted(broken))} xanh đã")
                continue
            tmpl, src = resolve_prompt(entry, td, i)
            if dry_run:
                dep_txt = f"  deps={','.join(deps[i])}" if deps[i] else ""
                print(f"  [plan] {fid}  prompt={src}:{tmpl}{dep_txt}")
                continue
            try:
                frame_fm = parse_frontmatter(_frame_path(entry, root).read_text(encoding="utf-8"))
            except (OSError, ValueError, KeyError) as e:
                entry["status"] = "failed"; entry["verdict"] = f"frame-load-error: {e}"
                save_queue(queue_path, entries)
                print(f"  [FAIL] {fid}: cannot load frame — {e}")
                if fids.get(i):
                    poisoned.add(fids[i])
                if stop_on_fail:
                    break
                continue
            res = runner_fn(entry, frame_fm, tmpl, root)
            ran += 1
            verdict = res.get("verdict")
            entry["status"] = "done" if verdict == "SUCCESS" else "failed"
            entry["verdict"] = verdict
            entry["commit"] = res.get("commit")
            entry.pop("blocked_by", None)       # it ran, so whatever blocked it before is moot
            if entry["status"] == "failed" and fids.get(i):
                poisoned.add(fids[i])           # its downstream subgraph is now unrunnable
            save_queue(queue_path, entries)     # write-back after EACH entry → resumable
            # bookkeeping: the write-back dirties the tree, which would make br-run REFUSE
            # the next frame (clean-tree gate). Commit the queue state right away.
            # NOTE: `(root/".git").exists()` only holds when --root IS the repo top-level;
            # for a nested --root (e.g. br/payroll inside a bigger repo, no .git of its
            # own) this was always False and the commit silently never ran, leaving
            # queue.yaml dirty forever after the first frame (bug found running the
            # payroll pipeline, GH#15 — same "assume root == repo root" class as the
            # loop-runner path-prefix bugs).
            in_repo = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                                     cwd=str(root), capture_output=True, text=True
                                     ).stdout.strip() == "true"
            if in_repo:
                subprocess.run(["git", "add", str(Path(queue_path).resolve())], cwd=str(root),
                               capture_output=True, text=True)
                subprocess.run(["git", "commit", "-q", "--no-verify", "-m",
                                f"chore(queue): {fid} → {entry['status']}"], cwd=str(root),
                               capture_output=True, text=True)
            tag = "done" if entry["status"] == "done" else "FAIL"
            print(f"  [{tag}] {fid}: {verdict} (prompt={src})")
            if entry["status"] == "failed" and stop_on_fail:
                print("  (stop-on-fail: dừng, chạy lại queue để tiếp tục sau khi sửa)")
                break
    print("-" * 56)
    print(f"  queue: ran={ran} · skipped(done)={skipped} · blocked={blocked} · total={len(entries)}")
    if blocked:
        print("  (blocked = upstream đỏ nên KHÔNG chạy — sửa upstream rồi chạy lại queue)")
    return 0


def affected(queue_path, frame_id, root=".", reset=False):
    """The subgraph a change to `frame_id` ripples into: that frame + everything downstream.

    This is the whole point of the DAG — when you change one frame you re-run THAT
    SUBGRAPH, not the line. `--reset` puts exactly those entries back to pending so the
    next `run` repairs them and leaves every other green frame alone.
    """
    entries = load_queue(queue_path)
    fids, deps, _ = load_graph(entries, root)
    if frame_id not in set(fids.values()):
        print(f"  frame không có trong queue: {frame_id}")
        return 1
    hit = downstream({frame_id}, fids, deps)
    self_idx = [i for i, f in fids.items() if f == frame_id]
    targets = sorted(set(self_idx) | hit)
    print(f"  Đổi {frame_id} → phải chạy lại {len(targets)} frame:")
    for i in targets:
        role = "chính nó" if i in self_idx else f"phụ thuộc ({', '.join(deps[i])})"
        print(f"    - {fids[i]}  [{entries[i].get('status','pending')}]  — {role}")
    if reset:
        for i in targets:
            entries[i]["status"] = "pending"
            entries[i].pop("verdict", None)
            entries[i].pop("blocked_by", None)
        save_queue(queue_path, entries)
        print(f"  → đã reset {len(targets)} frame về pending. Chạy: br-queue.py run --queue {queue_path}")
    else:
        print("  (thêm --reset để đặt đúng nhóm này về pending rồi chạy lại)")
    return 0


def list_queue(queue_path):
    for i, e in enumerate(load_queue(queue_path)):
        print(f"  {i}. {e.get('frame')}  [{e.get('status','pending')}]"
              + (f"  verdict={e.get('verdict')}" if e.get('verdict') else "")
              + (f"  blocked_by={','.join(e.get('blocked_by') or [])}" if e.get('blocked_by') else "")
              + (f"  @{str(e.get('commit'))[:8]}" if e.get('commit') else ""))
    return 0


def selftest():
    ok = True
    if yaml is None:
        print("  [FAIL] PyYAML missing"); return 1
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); (root / "br" / "frames").mkdir(parents=True)
        def frame(fid, deps=()):
            (root / "br" / "frames" / f"{fid}.md").write_text(
                "---\nschema_version: 0\nframe_id: %s\ncreated_by: human\nparent_br: BR.md\n"
                "clause_ids: [S1.1]\nparent_br_hash: x\nmuc_tieu: \"m\"\nscope_code: [\"src/**\"]\n"
                "scope_test: [\"tests/**\"]\nacceptance_test: \"true\"\ndepends_on: [%s]\n---\n# %s\n"
                % (fid, ", ".join(deps), fid), encoding="utf-8")
        for f in ("f1", "f2", "f3"):
            frame(f)
        q = root / "queue.yaml"
        save_queue(q, [
            {"frame": "br/frames/f1.md", "status": "pending"},
            {"frame": "br/frames/f2.md", "prompt": "inline {{muc_tieu}}", "status": "pending"},
            {"frame": "br/frames/f3.md", "status": "done"},   # already done → must be skipped
        ])
        # fake runner: f1 succeeds, f2 fails (records what prompt source it saw)
        seen = {}
        def fake(entry, fm, tmpl, root_):
            seen[fm["frame_id"]] = Path(tmpl).read_text(encoding="utf-8")
            return {"verdict": "SUCCESS" if fm["frame_id"] == "f1" else "NO_PROGRESS",
                    "commit": "abc123" if fm["frame_id"] == "f1" else None}
        run_queue(str(q), root=str(root), runner_fn=fake)
        after = load_queue(q)
        checks = [
            ("f1 → done", after[0]["status"] == "done" and after[0]["commit"] == "abc123"),
            ("f2 → failed", after[1]["status"] == "failed" and after[1]["verdict"] == "NO_PROGRESS"),
            ("f3 stayed done (skipped)", after[2]["status"] == "done"),
            ("f2 used INLINE prompt (raw, rendered later by br-revise)", "inline {{muc_tieu}}" in seen.get("f2", "")),
            ("f3 never ran (skip-done)", "f3" not in seen),
        ]
        # RESUME: fix f2 to succeed, re-run → only f2 runs (f1/f3 done), queue completes
        seen.clear()
        def fake2(entry, fm, tmpl, root_):
            seen[fm["frame_id"]] = tmpl
            return {"verdict": "SUCCESS", "commit": "def456"}
        run_queue(str(q), root=str(root), runner_fn=fake2)
        after2 = load_queue(q)
        checks += [
            ("resume ran ONLY f2", set(seen) == {"f2"}),
            ("f2 now done after resume", after2[1]["status"] == "done" and after2[1]["commit"] == "def456"),
            ("f1 untouched on resume", after2[0]["commit"] == "abc123"),
        ]

        # ---- DAG scheduling (GH#75 / ATG) — a fresh queue: a → b → c, plus independent d.
        # DECLARED out of order on purpose: c, b, d, a. Topo order must fix that.
        frame("a"); frame("b", ["a"]); frame("c", ["b"]); frame("d")
        q2 = root / "queue2.yaml"
        save_queue(q2, [{"frame": "br/frames/%s.md" % f, "status": "pending"} for f in ("c", "b", "d", "a")])
        ran_order = []
        def fake_ok(entry, fm, tmpl, root_):
            ran_order.append(fm["frame_id"])
            return {"verdict": "SUCCESS", "commit": "c0ffee"}
        run_queue(str(q2), root=str(root), runner_fn=fake_ok)
        checks += [
            ("topo order: a before b before c (declared c,b,d,a)",
             ran_order.index("a") < ran_order.index("b") < ran_order.index("c")),
            ("independent frame d still ran", "d" in ran_order),
        ]

        # ---- Downstream blocking: b fails → c must NOT run (its input is broken), d must.
        save_queue(q2, [{"frame": "br/frames/%s.md" % f, "status": "pending"} for f in ("c", "b", "d", "a")])
        ran2 = []
        def fake_b_fails(entry, fm, tmpl, root_):
            ran2.append(fm["frame_id"])
            fid_ = fm["frame_id"]
            return {"verdict": "NO_PROGRESS" if fid_ == "b" else "SUCCESS", "commit": None}
        run_queue(str(q2), root=str(root), runner_fn=fake_b_fails)
        st = {e["frame"].split("/")[-1][:-3]: e for e in load_queue(q2)}
        checks += [
            ("b failed", st["b"]["status"] == "failed"),
            ("c BLOCKED, never ran (upstream b red)", st["c"]["status"] == "blocked" and "c" not in ran2),
            ("c records blocked_by: b", st["c"].get("blocked_by") == ["b"]),
            ("d unaffected — still ran and went green", st["d"]["status"] == "done" and "d" in ran2),
            ("a unaffected — went green", st["a"]["status"] == "done"),
        ]

        # ---- Localized repair: fix b, re-run → ONLY b and c run. a and d stay green, untouched.
        ran3 = []
        def fake_all_ok(entry, fm, tmpl, root_):
            ran3.append(fm["frame_id"])
            return {"verdict": "SUCCESS", "commit": "fixed1"}
        run_queue(str(q2), root=str(root), runner_fn=fake_all_ok)
        st2 = {e["frame"].split("/")[-1][:-3]: e for e in load_queue(q2)}
        checks += [
            ("repair ran ONLY the broken subgraph (b, c)", set(ran3) == {"b", "c"}),
            ("whole graph green after repair", all(st2[f]["status"] == "done" for f in "abcd")),
            ("blocked_by cleared once c ran", "blocked_by" not in st2["c"]),
        ]

        # ---- affected(): naming the subgraph a change ripples into, and resetting exactly it.
        rc = affected(str(q2), "b", root=str(root), reset=True)
        st3 = {e["frame"].split("/")[-1][:-3]: e for e in load_queue(q2)}
        checks += [
            ("affected(b) exits 0", rc == 0),
            ("affected --reset put b + c back to pending",
             st3["b"]["status"] == "pending" and st3["c"]["status"] == "pending"),
            ("affected --reset left a and d green (not the whole line)",
             st3["a"]["status"] == "done" and st3["d"]["status"] == "done"),
            ("affected on unknown frame exits 1", affected(str(q2), "nope", root=str(root)) == 1),
        ]

        # ---- Cycle must not hang or drop frames (frame-lint R5 gates it; we fail open).
        frame("z1", ["z2"]); frame("z2", ["z1"])
        q3 = root / "queue3.yaml"
        save_queue(q3, [{"frame": "br/frames/z1.md"}, {"frame": "br/frames/z2.md"}])
        e3 = load_queue(q3)
        f3, d3, _ = load_graph(e3, str(root))
        o3, cyc3 = topo_order(e3, f3, d3)
        checks += [
            ("cycle detected, flagged", cyc3 is True),
            ("cycle still yields every frame exactly once (fail-open)", sorted(o3) == [0, 1]),
        ]
    print("br-queue self-test — resumable queue + DAG scheduling (fake runner)\n" + "-" * 56)
    for name, good in checks:
        ok = ok and good
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
    print("-" * 56)
    print(f"  RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="br-queue.py", description="Resumable run queue for /br run.")
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="run pending entries in order (skips done); writes status back")
    r.add_argument("--queue", required=True)
    r.add_argument("--root", default=".")
    r.add_argument("--stop-on-fail", action="store_true")
    r.add_argument("--dry-run", action="store_true", help="print the plan (which prompt each entry uses)")
    r.set_defaults(func=lambda a: run_queue(a.queue, a.root, a.stop_on_fail, a.dry_run))
    l = sub.add_parser("list", help="show queue entries + status")
    l.add_argument("--queue", required=True)
    l.set_defaults(func=lambda a: list_queue(a.queue))
    af = sub.add_parser("affected", help="frames a change to FRAME_ID ripples into (it + downstream)")
    af.add_argument("frame_id")
    af.add_argument("--queue", required=True)
    af.add_argument("--root", default=".")
    af.add_argument("--reset", action="store_true", help="put exactly those back to pending")
    af.set_defaults(func=lambda a: affected(a.queue, a.frame_id, a.root, a.reset))
    s = sub.add_parser("selftest", help="deterministic resumable-queue checks (fake runner)")
    s.set_defaults(func=lambda a: selftest())
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        build_parser().parse_args(["--help"]); return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
