#!/usr/bin/env python3
"""br-run — the deterministic /br run driver (GH#15): isolated worktree + wired revise.

Turns "/br run <frame>" from SKILL prose into a real, testable command:
  1. frame-lint the frame (structural).
  2. require a CLEAN working tree.
  3. create an ISOLATED git worktree from the baseline (branch br-run/<frame_id>) — the
     loop only ever touches this worktree, never the user's checkout or main.
  4. run loop-runner with the 6 guards + the revise adapter WIRED to fdk/tools/br-revise.py
     (which renders skills/br/assets/revise-prompt.md and calls `claude -p`).
  5. commit-on-success into the worktree branch (never main); print a one-line summary.
  6. record run_log_ref on the frame so `/br status` picks it up. Human reviews + merges.

DETERMINISTIC (built + selftested): frame load, worktree create/remove, the exact
loop-runner command, run-log summary, frame run_log_ref update. QUARANTINED (verified:
false): the `claude -p` call inside br-revise — injected via --revise-cmd so the whole
driver is selftested end-to-end with a deterministic stub (no model).

Usage:
  br-run.py run <frame.md> [--root .] [--baseline <ref>] [--keep-worktree]
                 [--revise-cmd "<override>"] [--print-prompt]
  br-run.py selftest
"""
import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
_FL = _HERE.with_name("frame-lint.py")
_spec = importlib.util.spec_from_file_location("frame_lint", _FL)
_frame_lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frame_lint)
parse_frontmatter = _frame_lint.parse_frontmatter
check_frames = _frame_lint.check

LOOP_RUNNER = _REPO / "harness" / "scripts" / "loop-runner.py"
BR_REVISE = _REPO / "fdk" / "tools" / "br-revise.py"
# Cùng lớp bẫy với br-fill/br-revise: bản CÀI (~/.claude/harness/) không mang skills/
# theo, skill nằm ở ~/.claude/skills. Thiếu fallback thì MỌI frame chết ở bước revise.
_TPL_REPO = _REPO / "skills" / "br" / "assets" / "revise-prompt.md"
DEFAULT_TEMPLATE = _TPL_REPO if _TPL_REPO.is_file() else (
    Path.home() / ".claude" / "skills" / "br" / "assets" / "revise-prompt.md")

# checkpoint-trace (distill SHEPHERD): mỗi frame-run = 1 checkpoint trong sổ trace của
# dây chuyền → rollback cả pipeline về frame bất kỳ + tier-gate trước effect không-đảo.
_cp_spec = importlib.util.spec_from_file_location("checkpoint", _HERE.with_name("checkpoint.py"))
_checkpoint = importlib.util.module_from_spec(_cp_spec)
_cp_spec.loader.exec_module(_checkpoint)


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def worktree_clean(root):
    r = _git(["status", "--porcelain"], root)
    return r.returncode == 0 and not r.stdout.strip()


def create_worktree(root, frame_id, baseline):
    wt = Path(root) / ".br-worktrees" / frame_id
    branch = f"br-run/{frame_id}"
    _git(["worktree", "remove", "--force", str(wt)], root)  # best-effort clean of a stale one
    _git(["branch", "-D", branch], root)
    r = _git(["worktree", "add", "-B", branch, str(wt), baseline], root)
    if r.returncode != 0:
        raise RuntimeError(f"git worktree add failed: {r.stderr.strip()}")
    return wt, branch


def remove_worktree(root, wt, branch):
    _git(["worktree", "remove", "--force", str(wt)], root)
    _git(["branch", "-D", branch], root)


def default_revise_cmd(frame_path, atest, vout, cwd, template):
    """The WIRING: loop-runner's --revise → br-revise (renders the prompt, calls claude -p)."""
    return (f'python3 {json.dumps(str(BR_REVISE))} run --frame {json.dumps(str(frame_path))} '
            f'--template {json.dumps(str(template))} --verify {json.dumps(atest)} '
            f'--verify-output {json.dumps(str(vout))} --cwd {json.dumps(str(cwd))}')


def build_loop_command(frame_fm, cwd, baseline, revise_cmd, log_path, vout):
    fid = frame_fm.get("frame_id", "frame")
    atest = frame_fm.get("acceptance_test", "false")
    scope_list = frame_fm.get("scope_code") or []
    protect_list = frame_fm.get("scope_test") or []
    clauses = ",".join(frame_fm.get("clause_ids") or [])
    guards = frame_fm.get("guards") or {}
    # --state/--scope/--protect are `action="append"` in loop-runner (repeatable, one
    # glob per flag) — a frame with >1 scope file (e.g. ["a.py","b.py","c.py"]) must pass
    # THREE flags, not one comma-joined string. Joining silently made every glob compare
    # a real path like "a.py" against the literal pattern "a.py,b.py,c.py" — never
    # matches, so diff-jail reverted the agent's own in-scope edits every iteration
    # (looked like NO_PROGRESS). Found running frame-p28-ui-serve (3-file scope), payroll
    # pipeline GH#15.
    # Sản phẩm phụ của CÔNG CỤ, khai cứng ở đây chứ KHÔNG đọc từ frame — frame không
    # được tự nới lãnh thổ của mình. Không có danh sách này thì cache test runner và
    # log do hook của chính harness ghi ra bị tính là "agent đi lạc".
    JAIL_EXEMPT = [".vitest", ".vitest/*", "node_modules", "node_modules/*",
                   ".llmwiki/*", "llmwiki/*", ".harness/*", "harness/metrics/*",
                   ".pytest_cache/*", "__pycache__/*", ".DS_Store", "*.log"]
    exempt_flags = [x for g in JAIL_EXEMPT for x in ("--jail-exempt", g)]
    scope_flags = [x for f in scope_list for x in ("--state", f)] + \
                  [x for f in scope_list for x in ("--scope", f)]
    protect_flags = [x for f in protect_list for x in ("--protect", f)]
    cmd = [
        "python3", str(LOOP_RUNNER), "run",
        "--verify", atest,
        "--revise", revise_cmd,
        *scope_flags, *protect_flags, *exempt_flags,
        "--baseline", baseline, "--commit-on-success",
        "--commit-message", f"frame({fid}): {frame_fm.get('muc_tieu','')} [{clauses}]",
        "--confirm", "2",   # hermeticity: a frame's green must reproduce (council 2026-07-06)
        "--log", str(log_path), "--cwd", str(cwd),
    ]
    for flag, key in (("--max-iter", "max_iter"), ("--budget-seconds", "budget_seconds"),
                      ("--no-progress-k", "no_progress_k"), ("--escalate-after", "escalate_after_iter")):
        if key in guards:
            cmd += [flag, str(guards[key])]
    return cmd


def _set_run_log_ref(frame_path, ref):
    """Record run_log_ref on the frame frontmatter (so /br status links it), if absent."""
    text = Path(frame_path).read_text(encoding="utf-8")
    if "run_log_ref:" in text:
        return
    lines = text.splitlines()
    # insert before the SECOND '---' (end of frontmatter)
    seen = 0
    for i, ln in enumerate(lines):
        if ln.strip() == "---":
            seen += 1
            if seen == 2:
                lines.insert(i, f"run_log_ref: {ref}")
                break
    Path(frame_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(frame_path, root=".", baseline=None, keep_worktree=True, revise_cmd=None,
        template=None, print_prompt=False, use_worktree=True, ack_tier=False):
    root = Path(root).resolve()
    frame_path = Path(frame_path)
    fm = parse_frontmatter(frame_path.read_text(encoding="utf-8"))
    fid = fm.get("frame_id", "frame")
    template = template or DEFAULT_TEMPLATE

    # 1. structural gate
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = check_frames(str(frame_path), str(root), skip_verify=True)
    if rc != 0:
        print(f"[br-run] frame-lint FAILED for {fid}:\n{buf.getvalue()}", file=sys.stderr)
        return 1

    if print_prompt:
        subprocess.run(["python3", str(BR_REVISE), "run", "--frame", str(frame_path),
                        "--template", str(template), "--verify", fm.get("acceptance_test", ""),
                        "--print"])
        return 0

    # 2. TIER-GATE (SHEPHERD "gate before materialize"): a frame whose effects are not
    # plain-reversible (declared `tier: compensable|irreversible` in its frontmatter —
    # e.g. it hits an external API, sends mail, writes a DB) must be ACKNOWLEDGED by a
    # human before the loop is allowed to run. Rolling back code will NOT undo it.
    frame_tier = str(fm.get("tier", "reversible"))
    if frame_tier != "reversible" and not ack_tier:
        print(f"[br-run] TIER-GATE: frame {fid} khai tier={frame_tier} — effect sẽ KHÔNG "
              f"undo được bằng rollback code. Người xác nhận rồi chạy lại với --ack-tier.",
              file=sys.stderr)
        return 3

    # 3. clean tree required — in-place mode NEEDS this even more: the frame's commit
    # must contain ONLY the frame's work, and a dirty tree would pollute changed_files.
    if not worktree_clean(root):
        print("[br-run] REFUSING: working tree not clean. Commit/stash first.", file=sys.stderr)
        return 1

    baseline = baseline or _git(["rev-parse", "HEAD"], root).stdout.strip()

    # 3. isolated worktree
    wt, branch = (create_worktree(root, fid, baseline) if use_worktree else (root, None))
    log_path = root / "br" / "frames" / f"{fid}.run.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    vout = Path(wt) / f".{fid}.verify.out"
    rcmd = revise_cmd or default_revise_cmd(frame_path, fm.get("acceptance_test", "false"),
                                            vout, wt, template)
    try:
        # 3b. SETUP một lần trong worktree MỚI. Worktree sinh từ git nên không mang theo
        # thứ bị gitignore (node_modules, .venv…) — thiếu bước này thì verify của frame
        # báo "command not found" chứ không báo test đỏ, và mọi phanh đều cắn nhầm.
        # Chạy NGOÀI vòng lặp: cài lại mỗi iteration là đốt ngân sách vô ích.
        setup_cmd = fm.get("setup_cmd")
        if setup_cmd:
            print(f"  setup     : {setup_cmd}")
            sp = subprocess.run(setup_cmd, shell=True, cwd=str(wt),
                                capture_output=True, text=True)
            if sp.returncode != 0:
                tail = ((sp.stdout or "") + (sp.stderr or ""))[-600:]
                print(f"[br-run] SETUP FAILED (rc={sp.returncode}) cho {fid}:\n{tail}",
                      file=sys.stderr)
                return 1
        # 4. run the guarded loop (revise wired to br-revise / claude -p)
        cmd = build_loop_command(fm, wt, baseline, rcmd, log_path, vout)
        subprocess.run(cmd)
        # 5. summary + record
        result = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {}
        _set_run_log_ref(frame_path, f"br/frames/{fid}.run.json")
        # FAILED frame (in-place): its half-done RED edits would dirty the tree and block
        # every later frame in the queue (learned at scale: 1 stuck frame ERROR'd 27).
        # Save the attempt as a reviewable patch, then revert the scope → the line flows on.
        if result.get("verdict") != "SUCCESS" and not use_worktree:
            changed = result.get("changed_files") or []
            if changed:
                diff = _git(["diff", "--", *changed], root).stdout
                if diff.strip():
                    patch = root / "br" / "frames" / f"{fid}.failed.patch"
                    patch.write_text(diff, encoding="utf-8")
                    print(f"  bản dở    : lưu {patch.relative_to(root)} (xem lại được) rồi revert scope")
                _git(["checkout", "--", *changed], root)
                for rel in changed:  # untracked leftovers
                    fpath = root / rel
                    tracked = _git(["ls-files", "--error-unmatch", "--", rel], root).returncode == 0
                    if not tracked and fpath.exists():
                        fpath.unlink()
        # bookkeeping commit: run-log + frame's run_log_ref are born AFTER the loop's own
        # commit — without this the tree stays dirty and the NEXT frame refuses to start.
        _git(["add", "br/frames"], root)
        _git(["commit", "-q", "--no-verify", "-m", f"chore({fid}): run-log + run_log_ref"], root)
        # frame files may live outside br/frames (custom layout) — commit the ref change too
        _git(["add", str(frame_path)], root)
        _git(["commit", "-q", "--no-verify", "-m", f"chore({fid}): run_log_ref"], root)
        # CHECKPOINT (SHEPHERD trace): mỗi frame-run = 1 mốc trong sổ .checkpoints.jsonl —
        # trỏ vào commit sẵn có (record, không double-commit). Rollback cả dây chuyền:
        #   python3 fdk/tools/checkpoint.py rollback <frame_id|seq|hash>
        if not use_worktree:
            try:
                _checkpoint.record(
                    str(root), f"frame({fid}) {result.get('verdict')}",
                    tier=frame_tier, effect=str(fm.get("muc_tieu", "")))
            except Exception as e:  # sổ trace không được phép giết run
                print(f"[br-run] (warn) checkpoint record lỗi: {e}", file=sys.stderr)
            # sổ vừa ghi làm tree bẩn → chặn frame kế (bài học harass) — commit sổ ngay
            _git(["add", ".checkpoints.jsonl"], root)
            _git(["commit", "-q", "--no-verify", "-m", f"chore({fid}): checkpoint ledger"], root)
        verdict = result.get("verdict")
        changed = result.get("changed_files") or []
        print("\n──────── /br run — TÓM TẮT ────────")
        print(f"  frame     : {fid}")
        print(f"  verdict   : {verdict}  ({result.get('iterations_run')} vòng)")
        print(f"  file đổi  : {', '.join(changed) or '(không)'}")
        print(f"  scope sạch: {result.get('scope_clean')}"
              + (f"  · ĐỊNH ghi ngoài scope (đã revert): {result.get('attempted_out_of_scope')}"
                 if result.get('attempted_out_of_scope') else ""))
        print(f"  commit    : {result.get('commit')}")
        if use_worktree:
            print(f"  worktree  : {wt}  (branch {branch})")
            print(f"  → NGƯỜI duyệt diff rồi merge: git merge {branch}   ·   hoặc bỏ: git worktree remove --force {wt}")
        else:
            print(f"  chế độ    : IN-PLACE — sửa nằm ngay trong cây hiện tại, bật app xem liền.")
            print(f"  → không ưng: git revert {str(result.get('commit'))[:8] if result.get('commit') else '<commit>'}   ·   lỗi ở đâu: python3 fdk/tools/br-find.py <file-hoặc-từ-khoá>")
        # AUTO-QC tất định sau frame xanh (0-token, KHÔNG LLM, advisory — không chặn):
        # reuse engine test tái hiện qc-code. LLM audit senior (qc-code/qc-uiux 4-mục) gọi tay
        # qua `/br qc`. Fail-open tuyệt đối — QC không được phép giết dây chuyền.
        if verdict == "SUCCESS":
            qc = root / "harness" / "scripts" / "qc-regression.py"
            if qc.is_file():
                try:
                    r = subprocess.run(["python3", str(qc), "--run"], cwd=root,
                                       capture_output=True, text=True, timeout=120)
                    tail = (r.stdout or r.stderr or "").strip().splitlines()
                    print(f"  qc (auto) : {'✓ test qc-* xanh' if r.returncode == 0 else '✗ ' + (tail[-1][:70] if tail else 'qc-* ĐỎ')}"
                          + "  ·  audit senior: /br qc")
                except Exception:
                    pass  # engine QC lỗi/vắng → bỏ qua, không chặn frame
            else:
                print(f"  qc (auto) : (chưa có qc-regression.py)  ·  audit senior UI/code: /br qc")
        return 0 if verdict == "SUCCESS" else 2
    finally:
        if use_worktree and not keep_worktree:
            remove_worktree(root, wt, branch)


def selftest():
    ok = True
    checks = []
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _git(["init", "-q"], root); _git(["config", "user.email", "t@t"], root); _git(["config", "user.name", "t"], root)
        (root / "src").mkdir(); (root / "tests").mkdir(); (root / "br" / "frames").mkdir(parents=True)
        (root / "src" / "auth.py").write_text("def login(): return False\n")
        (root / "tests" / "test_auth.py").write_text("def test(): pass\n")
        (root / "BR.md").write_text("clause S4.1\n")
        brh = _frame_lint._sha256_file(root / "BR.md")
        atest = f"{sys.executable} -c \"import sys,pathlib;sys.exit(0 if 'return True' in pathlib.Path('src/auth.py').read_text() else 1)\""
        # Fixture PHẢI qua được frame-lint R7 (luật nội dung) — nếu không thì run()
        # dừng ở cổng cấu trúc và selftest này không kiểm được gì phía sau nó.
        frame = root / "br" / "frames" / "frame-001-auth-login.md"
        frame.write_text(
            "---\nschema_version: 0\nframe_id: frame-001-auth-login\ncreated_by: human\n"
            f"parent_br: BR.md\nclause_ids: [S4.1]\nparent_br_hash: {brh}\n"
            "muc_tieu: \"Đăng nhập trả về true khi thông tin hợp lệ, để phiên người dùng mở được\"\n"
            f"scope_code: [\"src/**\"]\nscope_test: [\"tests/**\"]\nacceptance_test: {json.dumps(atest)}\n"
            "guards:\n  max_iter: 4\n  no_progress_k: 2\n---\n"
            "# frame-001-auth-login — Đăng nhập\n\n"
            "## Nghiệp vụ\nNgười dùng không đăng nhập được thì không dùng được gì. "
            "Frame này làm hàm login trả về true cho thông tin hợp lệ.\n\n"
            "## Input / Output\n- **Input:** không có tham số trong fixture.\n"
            "- **Output:** `True` khi hợp lệ.\n\n"
            "## Spec (FR/SC)\n- **FR-01**: `login()` PHẢI trả về True.\n\n"
            "- **SC-01**: Người dùng đăng nhập và vào được ứng dụng.\n\n"
            "## Tiêu chí nghiệm thu\n- Gọi `login()` (FR-01) → nhận True.\n\n"
            "## Ngoài phạm vi\n- Đăng xuất và quên mật khẩu — frame khác lo.\n"
            "- Lưu phiên, nhớ đăng nhập, và mọi thứ chạm cơ sở dữ liệu thật.\n", encoding="utf-8")
        _git(["add", "-A"], root); _git(["commit", "-q", "-m", "base", "--no-verify"], root)

        # STUB revise (stands in for claude -p): edit the in-scope file so verify passes.
        stub = f"{sys.executable} -c \"import pathlib;pathlib.Path('src/auth.py').write_text('def login(): return True')\""
        rc = run(str(frame), root=str(root), baseline="HEAD", keep_worktree=True,
                 revise_cmd=stub, use_worktree=True)
        logf = root / "br" / "frames" / "frame-001-auth-login.run.json"
        if not logf.exists():
            # KHÔNG tung traceback: không có run-log nghĩa là loop chưa chạy tới nơi
            # (cổng cấu trúc chặn, loop-runner từ chối cờ…). Traceback giấu mất lý do.
            print("br-run selftest: FAIL — không có run-log. Loop chưa chạy tới nơi; "
                  "xem thông báo phía trên (frame-lint / loop-runner).")
            return 1
        log = json.loads(logf.read_text())
        # worktree branch exists + committed there
        branches = _git(["branch", "--list", "br-run/frame-001-auth-login"], root).stdout
        wt_commit_msg = _git(["log", "-1", "--pretty=%s", "br-run/frame-001-auth-login"], root).stdout.strip()
        checks = [
            ("run returned success", rc == 0),
            ("verdict SUCCESS", log.get("verdict") == "SUCCESS"),
            ("changed_files ⊆ scope (only src)", log.get("changed_files") == ["src/auth.py"]),
            ("scope_clean True", log.get("scope_clean") is True),
            ("commit made", bool(log.get("commit"))),
            ("worktree branch created", "br-run/frame-001-auth-login" in branches),
            ("commit on branch has frame message", wt_commit_msg.startswith("frame(frame-001-auth-login):")),
            ("frame got run_log_ref", "run_log_ref:" in frame.read_text(encoding="utf-8")),
            ("main src untouched (still False)", "return False" in (root / "src" / "auth.py").read_text()),
        ]
        remove_worktree(root, root / ".br-worktrees" / "frame-001-auth-login", "br-run/frame-001-auth-login")

        # IN-PLACE mode (the DEFAULT): change lands in the live tree + commits on the
        # CURRENT branch — "bật app lên là thấy", one working tree, no folder hunting.
        (root / "src" / "auth.py").write_text("def login(): return False\n")
        _git(["add", "-A"], root); _git(["commit", "-q", "-m", "reset", "--no-verify"], root)
        rc2 = run(str(frame), root=str(root), baseline="HEAD", revise_cmd=stub, use_worktree=False)
        recent = _git(["log", "-5", "--pretty=%s"], root).stdout
        checks += [
            ("in-place run success", rc2 == 0),
            ("in-place: live tree updated (app sees it)", "return True" in (root / "src" / "auth.py").read_text()),
            ("in-place: frame commit on CURRENT branch", "frame(frame-001-auth-login):" in recent),
            ("in-place: tree clean after run (bookkeeping committed)", worktree_clean(root)),
        ]
        # CHECKPOINT wire: sổ trace có mốc frame + tree vẫn sạch (sổ đã được commit)
        led = (root / ".checkpoints.jsonl")
        checks += [
            ("checkpoint ledger có mốc frame(frame-001-auth-login)", led.exists() and "frame(frame-001-auth-login)" in led.read_text(encoding="utf-8")),
            ("ledger đã commit (tree sạch cho frame kế)", worktree_clean(root)),
        ]
        # TIER-GATE: frame khai tier irreversible → br-run DỪNG (exit 3) khi chưa --ack-tier
        frame_ir = root / "br" / "frames" / "frame-002-mail-notify.md"
        frame_ir.write_text(frame.read_text(encoding="utf-8")
                            .replace("frame_id: frame-001-auth-login", "frame_id: frame-002-mail-notify")
                            .replace("---\n# frame-001-auth-login", "tier: irreversible\n---\n# frame-002-mail-notify"),
                            encoding="utf-8")
        _git(["add", "-A"], root); _git(["commit", "-q", "--no-verify", "-m", "add frame-002-mail-notify"], root)
        rc4 = run(str(frame_ir), root=str(root), baseline="HEAD", revise_cmd=stub, use_worktree=False)
        rc5 = run(str(frame_ir), root=str(root), baseline="HEAD", revise_cmd=stub, use_worktree=False, ack_tier=True)
        checks += [
            ("tier-gate CHẶN frame irreversible (exit 3)", rc4 == 3),
            ("--ack-tier cho chạy sau khi người xác nhận", rc5 in (0, 2)),
        ]

    print("br-run self-test — worktree + wired revise (stub, no model)\n" + "-" * 58)
    for name, good in checks:
        ok = ok and good
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
    print("-" * 58)
    print(f"  RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="br-run.py", description="Deterministic /br run driver (isolated worktree + wired revise).")
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="run one frame in an isolated worktree")
    r.add_argument("frame")
    r.add_argument("--root", default=".")
    r.add_argument("--baseline", default=None)
    r.add_argument("--keep-worktree", action="store_true", default=True)
    # DEFAULT = IN-PLACE (one working tree — the app you're running sees the change
    # immediately; safety comes from the deterministic guards, not folder isolation).
    # --worktree is the opt-in for when you truly want an isolated copy.
    r.add_argument("--worktree", dest="use_worktree", action="store_true", default=False)
    r.add_argument("--no-worktree", dest="use_worktree", action="store_false")
    r.add_argument("--revise-cmd", default=None, help="override the revise command (default: wired to br-revise.py)")
    r.add_argument("--template", default=None)
    r.add_argument("--print-prompt", action="store_true")
    r.add_argument("--ack-tier", action="store_true",
                   help="người XÁC NHẬN cho frame tier compensable/irreversible chạy (SHEPHERD tier-gate)")
    r.set_defaults(func=lambda a: run(a.frame, a.root, a.baseline, a.keep_worktree,
                                      a.revise_cmd, a.template, a.print_prompt, a.use_worktree,
                                      a.ack_tier))
    s = sub.add_parser("selftest", help="end-to-end worktree run with a deterministic stub revise")
    s.set_defaults(func=lambda a: selftest())
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not getattr(args, "func", None):
        build_parser().parse_args(["--help"]); return 2
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
