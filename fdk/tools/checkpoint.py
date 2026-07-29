#!/usr/bin/env python3
"""checkpoint — reversible-trace time machine cho một agent-run (distill từ SHEPHERD).

SHEPHERD (arxiv 2605.10913 "Reversible Agentic Execution Traces") mô hình hoá một
lượt chạy agent thành TRACE kiểu git: mỗi effect = một commit, mọi state quá khứ
LUÔN reachable/replayable (roll về BẤT KỲ hash nào), và mỗi effect mang một
"reversibility tier" — reversible (ghi filesystem, tự roll-back được) · compensable
(side-effect cần handler bù, vd ghi DB) · irreversible (model call, email, gọi API
ngoài — chỉ audit được, không undo được). Ta không có substrate Python của SHEPHERD;
substrate của ta là GIT. Tool này áp đúng 3 ý cốt lõi lên git:

  save   — đóng một CHECKPOINT (commit) vào trace + ghi tier vào sổ .checkpoints.jsonl
  list   — xem trace (mọi step, tier; irreversible được đánh dấu ⚠ không tự undo)
  rollback <seq|hash> — khôi phục cây về BẤT KỲ checkpoint; GIỮ lịch sử (mọi state vẫn
           reachable, đúng nguyên tắc SHEPHERD) + CẢNH BÁO nếu có checkpoint SAU mốc đích
           mang tier compensable/irreversible (effect đó đã materialize, roll code KHÔNG
           undo được — compensable phải chạy handler bù, irreversible phải xử tay).
  tier-gate <tier> — cổng TRƯỚC khi để một effect materialize: reversible→0, compensable→3
           (cần handler), irreversible→4 (cần người xác nhận). Đây là "gate before materialize".

Usage:
  checkpoint.py save --label L [--tier reversible|compensable|irreversible] [--effect E] [--root .]
  checkpoint.py list [--root .]
  checkpoint.py rollback <seq|hash> [--root .]
  checkpoint.py tier-gate <tier>
  checkpoint.py selftest
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TIERS = ("reversible", "compensable", "irreversible")
TIER_EXIT = {"reversible": 0, "compensable": 3, "irreversible": 4}
LEDGER = ".checkpoints.jsonl"


def git(args, root):
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)


def _ledger_path(root):
    return Path(root) / LEDGER


def _read_ledger(root):
    p = _ledger_path(root)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def save(root, label, tier="reversible", effect=""):
    root = Path(root)
    if tier not in TIERS:
        print(f"[checkpoint] tier không hợp lệ: {tier} (chọn {TIERS})", file=sys.stderr)
        return 2
    git(["add", "-A"], root)
    # commit; nếu không có gì đổi thì vẫn tạo checkpoint rỗng (--allow-empty) để mốc luôn tồn tại
    c = git(["commit", "--no-verify", "--allow-empty", "-m", f"chkpt: {label}"], root)
    if c.returncode != 0:
        print(f"[checkpoint] commit lỗi: {c.stderr.strip()}", file=sys.stderr)
        return 1
    h = git(["rev-parse", "HEAD"], root).stdout.strip()
    ledger = _read_ledger(root)
    seq = (ledger[-1]["seq"] + 1) if ledger else 1
    rec = {"seq": seq, "hash": h, "label": label, "tier": tier, "effect": effect}
    with _ledger_path(root).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    # ghi sổ xong cần đưa sổ vào commit kế; ở đây commit sổ luôn để trace tự-mô-tả
    git(["add", LEDGER], root)
    git(["commit", "--no-verify", "--amend", "--no-edit"], root)
    # cập nhật hash sau amend
    rec["hash"] = git(["rev-parse", "HEAD"], root).stdout.strip()
    # rewrite dòng cuối với hash đúng
    lines = _ledger_path(root).read_text(encoding="utf-8").splitlines()
    lines[-1] = json.dumps(rec, ensure_ascii=False)
    _ledger_path(root).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[checkpoint] #{seq} '{label}' [{tier}] @ {rec['hash'][:8]}")
    return 0


def record(root, label, tier="reversible", effect="", commit_hash=None):
    """Ghi một entry sổ trỏ vào COMMIT CÓ SẴN (không tạo commit mới) — dùng khi một
    pipeline khác (vd br-run) đã tự commit và chỉ cần checkpoint-trace làm sổ tier/rollback.
    Tránh double-commit khi wire vào /br run."""
    root = Path(root)
    if tier not in TIERS:
        print(f"[checkpoint] tier không hợp lệ: {tier}", file=sys.stderr)
        return 2
    h = commit_hash or git(["rev-parse", "HEAD"], root).stdout.strip()
    if git(["cat-file", "-e", h], root).returncode != 0:
        print(f"[checkpoint] commit không tồn tại: {h}", file=sys.stderr)
        return 1
    ledger = _read_ledger(root)
    seq = (ledger[-1]["seq"] + 1) if ledger else 1
    rec = {"seq": seq, "hash": h, "label": label, "tier": tier, "effect": effect}
    with _ledger_path(root).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[checkpoint] #{seq} '{label}' [{tier}] @ {h[:8]} (record — không commit mới)")
    return 0


def list_cmd(root):
    ledger = _read_ledger(root)
    if not ledger:
        print("[checkpoint] chưa có checkpoint nào (chạy `save`).")
        return 0
    print("seq  tier          hash      label / effect")
    for r in ledger:
        mark = "⚠ " if r["tier"] == "irreversible" else ("~ " if r["tier"] == "compensable" else "  ")
        eff = f"  · {r['effect']}" if r.get("effect") else ""
        print(f"{r['seq']:>3}  {mark}{r['tier']:<11} {r['hash'][:8]}  {r['label']}{eff}")
    return 0


def rollback(root, target):
    root = Path(root)
    ledger = _read_ledger(root)
    if not ledger:
        print("[checkpoint] không có trace để rollback.", file=sys.stderr)
        return 1
    # tìm checkpoint đích theo seq, hash-prefix, hoặc label (vd frame_id) — lấy mốc MỚI NHẤT khớp label
    tgt = None
    for r in ledger:
        if str(r["seq"]) == str(target) or r["hash"].startswith(str(target)):
            tgt = r
            break
    if not tgt:
        for r in reversed(ledger):
            if str(target) in r["label"]:
                tgt = r
                break
    if not tgt:
        print(f"[checkpoint] không tìm thấy checkpoint '{target}'.", file=sys.stderr)
        return 1
    # SHEPHERD: trace CHỈ TĂNG, mọi state reachable — KHÔNG xoá lịch sử, KHÔNG rewind sổ.
    # Khôi phục cây về mốc đích, NHƯNG giữ sổ append-only (checkout sẽ cuốn sổ về quá khứ nên
    # phải phục hồi + ghi chính hành động rollback thành một step mới của trace).
    full = _read_ledger(root)
    r1 = git(["checkout", tgt["hash"], "--", "."], root)
    if r1.returncode != 0:
        print(f"[checkpoint] checkout lỗi: {r1.stderr.strip()}", file=sys.stderr)
        return 1
    seq = full[-1]["seq"] + 1
    full.append({"seq": seq, "hash": "", "label": f"rollback→#{tgt['seq']} {tgt['label']}",
                 "tier": "reversible", "effect": f"khôi phục cây về {tgt['hash'][:8]}"})
    _ledger_path(root).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in full) + "\n", encoding="utf-8")
    git(["add", "-A"], root)
    git(["commit", "--no-verify", "--allow-empty", "-m", f"chkpt: rollback → #{tgt['seq']} {tgt['label']}"], root)
    full[-1]["hash"] = git(["rev-parse", "HEAD"], root).stdout.strip()
    _ledger_path(root).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in full) + "\n", encoding="utf-8")
    # CẢNH BÁO tier: checkpoint SAU mốc đích có effect đã materialize không undo được bằng roll code
    after = [r for r in ledger if r["seq"] > tgt["seq"] and r["tier"] != "reversible"]
    print(f"[checkpoint] đã rollback cây về #{tgt['seq']} '{tgt['label']}' (@ {tgt['hash'][:8]}). Lịch sử GIỮ nguyên.")
    if after:
        print("  ⚠ CÁC EFFECT SAU MỐC NÀY ĐÃ MATERIALIZE — roll code KHÔNG undo được:")
        for r in after:
            how = "chạy handler BÙ" if r["tier"] == "compensable" else "XỬ TAY (không đảo được)"
            print(f"     #{r['seq']} [{r['tier']}] {r['label']}  → {how}"
                  + (f" · {r['effect']}" if r.get("effect") else ""))
    return 0


def tier_gate(tier):
    if tier not in TIERS:
        print(f"[checkpoint] tier không hợp lệ: {tier}", file=sys.stderr)
        return 2
    if tier == "reversible":
        print("[gate] reversible — cho phép materialize (tự roll-back được).")
    elif tier == "compensable":
        print("[gate] compensable — cần HANDLER BÙ trước khi để side-effect landing.", file=sys.stderr)
    else:
        print("[gate] irreversible — DỪNG, cần NGƯỜI xác nhận (model call/email/API ngoài).", file=sys.stderr)
    return TIER_EXIT[tier]


def selftest():
    ok = True
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        git(["init", "-q"], root); git(["config", "user.email", "t@t"], root); git(["config", "user.name", "t"], root)
        (root / "app.py").write_text("v = 1\n"); git(["add", "-A"], root); git(["commit", "-q", "--no-verify", "-m", "base"], root)

        import io, contextlib
        def run(fn, *a):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                rc = fn(*a)
            return rc, buf.getvalue()

        (root / "app.py").write_text("v = 2\n")
        run(save, str(root), "b1-reversible", "reversible", "sửa app v2")
        (root / "app.py").write_text("v = 3\n")
        run(save, str(root), "b2-send-email", "irreversible", "gửi email khách")
        (root / "app.py").write_text("v = 4\n")
        run(save, str(root), "b3-reversible", "reversible", "sửa app v4")

        led = _read_ledger(root)
        c_seq = [r["seq"] for r in led] == [1, 2, 3]
        c_tier = led[1]["tier"] == "irreversible"

        # rollback về #1 (reversible) — cây phải = v2, và PHẢI cảnh báo về #2 irreversible
        rc, out = run(rollback, str(root), "1")
        c_tree = (root / "app.py").read_text().strip() == "v = 2"
        c_warn = "irreversible" in out and "b2-send-email" in out and "KHÔNG undo" in out
        # lịch sử giữ: commit cũ v4 vẫn reachable (SHEPHERD: mọi state reachable)
        c_hist = git(["cat-file", "-e", led[2]["hash"]], root).returncode == 0
        # rollback được về BẤT KỲ hash (dùng prefix của #3)
        rc2, _ = run(rollback, str(root), led[2]["hash"][:8])
        c_anyhash = (root / "app.py").read_text().strip() == "v = 4"

        # tier-gate: reversible→0, compensable→3, irreversible→4
        g_ok = (run(tier_gate, "reversible")[0] == 0 and run(tier_gate, "compensable")[0] == 3
                and run(tier_gate, "irreversible")[0] == 4)

        # record: trỏ vào commit CÓ SẴN, không tạo commit mới (wire /br run không double-commit)
        n_before = len(git(["log", "--oneline"], root).stdout.splitlines())
        (root / "app.py").write_text("v = 9\n")
        git(["add", "-A"], root); git(["commit", "-q", "--no-verify", "-m", "frame(frame-x): lam x"], root)
        fx_hash = git(["rev-parse", "HEAD"], root).stdout.strip()
        run(record, str(root), "frame(frame-x) SUCCESS", "reversible", "app.py", fx_hash)
        n_after = len(git(["log", "--oneline"], root).stdout.splitlines())
        led2 = _read_ledger(root)
        c_record = (led2[-1]["label"] == "frame(frame-x) SUCCESS" and led2[-1]["hash"] == fx_hash
                    and n_after == n_before + 1)  # +1 là commit frame, record KHÔNG thêm commit
        # rollback theo LABEL (frame_id) — không cần nhớ seq/hash
        (root / "app.py").write_text("v = 10\n")
        run(save, str(root), "b-sau", "reversible", "")
        rc3, _ = run(rollback, str(root), "frame-x")
        c_label_rb = (root / "app.py").read_text().strip() == "v = 9"

    checks = [
        ("save ghi trace tuần tự (seq 1,2,3)", c_seq),
        ("tier ghi đúng vào sổ", c_tier),
        ("rollback về #1 → cây byte đúng (v2)", c_tree),
        ("rollback CẢNH BÁO effect irreversible sau mốc", c_warn),
        ("lịch sử GIỮ (state v4 vẫn reachable)", c_hist),
        ("rollback về BẤT KỲ hash (v4)", c_anyhash),
        ("tier-gate 3 mức exit đúng (0/3/4)", g_ok),
        ("record trỏ commit sẵn, KHÔNG double-commit", c_record),
        ("rollback theo LABEL (frame_id)", c_label_rb),
    ]
    print("checkpoint self-test — reversible trace (SHEPHERD distill trên git)\n" + "-" * 60)
    for name, good in checks:
        ok = ok and good
        print(f"  [{'PASS' if good else 'FAIL'}] {name}")
    print("-" * 60)
    print(f"  RESULT: {'ALL PASS' if ok else 'FAILURES PRESENT'}")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="checkpoint.py", description="Reversible-trace time machine (distill từ SHEPHERD) trên git.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("save", help="đóng một checkpoint vào trace + ghi tier")
    s.add_argument("--label", required=True); s.add_argument("--tier", default="reversible", choices=TIERS)
    s.add_argument("--effect", default=""); s.add_argument("--root", default=".")
    s.set_defaults(func=lambda a: save(a.root, a.label, a.tier, a.effect))
    rc = sub.add_parser("record", help="ghi entry sổ trỏ vào commit CÓ SẴN (không commit mới — cho pipeline đã tự commit)")
    rc.add_argument("--label", required=True); rc.add_argument("--tier", default="reversible", choices=TIERS)
    rc.add_argument("--effect", default=""); rc.add_argument("--hash", default=None); rc.add_argument("--root", default=".")
    rc.set_defaults(func=lambda a: record(a.root, a.label, a.tier, a.effect, a.hash))
    l = sub.add_parser("list", help="xem trace + tier"); l.add_argument("--root", default=".")
    l.set_defaults(func=lambda a: list_cmd(a.root))
    r = sub.add_parser("rollback", help="khôi phục cây về BẤT KỲ checkpoint (giữ lịch sử)")
    r.add_argument("target"); r.add_argument("--root", default=".")
    r.set_defaults(func=lambda a: rollback(a.root, a.target))
    g = sub.add_parser("tier-gate", help="cổng trước khi effect materialize (exit theo tier)")
    g.add_argument("tier", choices=TIERS)
    g.set_defaults(func=lambda a: tier_gate(a.tier))
    t = sub.add_parser("selftest"); t.set_defaults(func=lambda a: selftest())
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
