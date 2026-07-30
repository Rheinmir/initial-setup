#!/usr/bin/env python3
"""token-budget — a per-session / per-task token + dollar governor (2026 AI-FinOps trend).

Providers cap spend only at org/project granularity; agents need per-session/per-task caps, and
no agent framework ships one. This counts tokens by code, sums per session, computes $ from
configured rates, and warns/blocks when a cap is crossed.

  record SESSION --in N --out M [--model X] [--task T]   append usage (BY CODE, fail-open).
      [--calls N] [--subagents N] [--workers N] [--graph-writes N]   complexity counters (PDF §VIII.B).
  --report                                               per-session totals + $ + counters + over-cap flag.
  check SESSION                                          exit 2 if over cap AND mode:block.
  --self-test                                            deterministic cost + cap logic in temp dir.

The ONE adapter = harness/token-budget.config.yaml (rates, budgets, mode — verified:false).
Counting + cost math are deterministic, built now. Rates + caps are the unknowns; default
mode 'warn' so an un-tuned cap never kills a session.
"""
import json
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import bnal_config

_FALLBACK = {"verified": False, "mode": "warn",
             "budgets": {"per_session_tokens": 2000000, "per_task_usd": 5.0,
                         "per_session_model_calls": 500, "per_workflow_subagents": 16,
                         "max_concurrent_workers": 8, "per_session_graph_writes": 200},
             "rates": {"default": {"input": 0.003, "output": 0.015}}}

COUNTERS = {  # cờ CLI -> (khoá trong row JSONL, khoá budget trong config)
    "calls":        ("calls",        "per_session_model_calls"),
    "subagents":    ("subagents",    "per_workflow_subagents"),
    "workers":      ("workers",      "max_concurrent_workers"),
    "graph-writes": ("graph_writes", "per_session_graph_writes"),
}
# shortcut: workers cộng dồn y hệt các counter khác (trần = tổng, không phải đỉnh đồng thời),
# đổi sang max() khi có ca thật cần đo peak concurrency trong một session.


def _metrics_file(root: Path) -> Path:
    return root / "harness" / "metrics" / "tokens.jsonl"


def _config_file(root: Path) -> Path:
    return root / "harness" / "token-budget.config.yaml"


def _ensure_gitignored(root: Path) -> None:
    try:
        (root / "harness" / "metrics").mkdir(parents=True, exist_ok=True)
        gi = root / ".gitignore"
        cur = gi.read_text(encoding="utf-8", errors="ignore") if gi.exists() else ""
        if "harness/metrics/tokens.jsonl" not in cur:
            with open(gi, "a", encoding="utf-8") as f:
                f.write("\n# token-budget local usage log\nharness/metrics/tokens.jsonl\n")
    except Exception:
        pass


def load_config(root: Path) -> dict:
    cfg = bnal_config.load(root, "token-budget", _FALLBACK)
    return cfg


def cost_usd(in_tok, out_tok, model, rates) -> float:
    """Deterministic $ from tokens. Unknown model -> 'default' rate."""
    r = rates.get(model) or rates.get("default") or {"input": 0, "output": 0}
    return (in_tok / 1000.0) * float(r.get("input", 0)) + (out_tok / 1000.0) * float(r.get("output", 0))


def record(root, session, in_tok, out_tok, model=None, task=None, counters=None) -> dict:
    root = Path(root)
    rec = {"session": session or "default", "in": int(in_tok or 0), "out": int(out_tok or 0),
           "model": model or "default", "task": task or ""}
    for key, _ in COUNTERS.values():          # counter = 0 thì không ghi -> row cũ không đổi bit nào
        n = int((counters or {}).get(key, 0) or 0)
        if n:
            rec[key] = n
    try:
        _ensure_gitignored(root)
        with open(_metrics_file(root), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return rec


def _read(root: Path):
    try:
        lines = _metrics_file(root).read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out = []
    for ln in lines:
        ln = ln.strip()
        if ln:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
    return out


def totals(root, cfg):
    rates = cfg.get("rates", {})
    zero = {"in": 0, "out": 0, "usd": 0.0}
    zero.update({key: 0 for key, _ in COUNTERS.values()})
    by_sess = defaultdict(lambda: dict(zero))
    for r in _read(Path(root)):
        s = by_sess[r.get("session", "default")]
        s["in"] += int(r.get("in", 0)); s["out"] += int(r.get("out", 0))
        s["usd"] += cost_usd(int(r.get("in", 0)), int(r.get("out", 0)), r.get("model", "default"), rates)
        for key, _ in COUNTERS.values():
            s[key] += int(r.get(key, 0))   # .get -> row JSONL cũ thiếu khoá vẫn đọc được
    return by_sess


def over_budget(sess_row, cfg):
    """Returns list of breached caps (empty = within budget)."""
    b = cfg.get("budgets", {})
    out = []
    if sess_row["in"] + sess_row["out"] > int(b.get("per_session_tokens", 1e18)):
        out.append(f"session tokens {sess_row['in']+sess_row['out']} > cap {b.get('per_session_tokens')}")
    if sess_row["usd"] > float(b.get("per_task_usd", 1e18)):
        out.append(f"session ${sess_row['usd']:.2f} > cap ${b.get('per_task_usd')}")
    for key, budget_key in COUNTERS.values():
        cap = b.get(budget_key)
        if cap and sess_row.get(key, 0) > int(cap):   # .get -> row cũ thiếu khoá = 0, không bao giờ vượt
            out.append(f"{budget_key} {sess_row.get(key, 0)} > cap {cap}")
    return out


def report(root) -> str:
    cfg = load_config(Path(root))
    by = totals(root, cfg)
    out = [f"TokenBudget — {len(by)} session(s)  (mode={cfg.get('mode')}, verified={cfg.get('verified')})"]
    for s, row in sorted(by.items()):
        flag = " ⚠ OVER" if over_budget(row, cfg) else ""
        ctr = " ".join(f"{key}={row.get(key, 0)}" for key, _ in COUNTERS.values())
        out.append(f"  {s:<16} in={row['in']:<9} out={row['out']:<9} ${row['usd']:.3f}  {ctr}{flag}")
    return "\n".join(out)


def self_test() -> int:
    cfg = {"verified": True, "mode": "block",
           "budgets": {"per_session_tokens": 1000, "per_task_usd": 0.05},
           "rates": {"default": {"input": 0.003, "output": 0.015}, "opus": {"input": 0.015, "output": 0.075}}}
    c = cost_usd(1000, 1000, "opus", cfg["rates"])           # 0.015 + 0.075 = 0.09
    cost_ok = abs(c - 0.09) < 1e-9
    within = over_budget({"in": 100, "out": 100, "usd": 0.01}, cfg)
    over = over_budget({"in": 800, "out": 800, "usd": 0.2}, cfg)   # tokens 1600>1000, $0.2>0.05
    # 4 trần counter: cộng dồn per-session, chỉ trần THẬT SỰ bị vượt mới báo.
    cfg2 = {"verified": True, "mode": "warn",
            "budgets": {"per_session_tokens": 100000, "per_task_usd": 5.0,
                        "per_session_model_calls": 3, "per_workflow_subagents": 16,
                        "max_concurrent_workers": 8, "per_session_graph_writes": 200}}
    with tempfile.TemporaryDirectory() as td:
        record(td, "s1", 10, 10, counters={"calls": 2})
        record(td, "s1", 10, 10, counters={"calls": 2})
        row = totals(td, cfg2)["s1"]
    sum_ok = row["calls"] == 4 and row["in"] == 20 and row["subagents"] == 0
    breach = over_budget(row, cfg2)                               # calls 4>3, các trần khác trong hạn
    calls_ok = len(breach) == 1 and "per_session_model_calls" in breach[0]
    legacy_ok = over_budget({"in": 1, "out": 1, "usd": 0.0}, cfg2) == []   # row JSONL cũ thiếu khoá counter
    ok = cost_ok and not within and len(over) == 2 and sum_ok and calls_ok and legacy_ok
    print("token-budget self-test:", "ALL PASS" if ok else "FAIL")
    return 0 if ok else 1


def _opt(args, flag):
    if flag in args:
        i = args.index(flag); v = args[i + 1] if len(args) > i + 1 else None; del args[i:i + 2]; return v
    return None


def sync_from_cost(root: Path):
    """Đồng bộ token THẬT từ `cost-by-session.json` (code-logger.py ghi qua hook) sang sổ này.

    Vì sao cần: trước bản này KHÔNG hook nào gọi `record`, nên `tokens.jsonl` chưa từng tồn
    tại và mọi trần đều đang cap một con số luôn bằng 0 — trần không có dữ liệu thì không phải
    trần. Nguồn token thật đã có sẵn ở cost-by-session.json; đọc lại rẻ hơn nhiều so với dựng
    thêm một đường ghi song song (và tránh hai sổ lệch nhau).

    Idempotent theo phiên: mỗi session giữ ĐÚNG một row `source=cost-sync`, chạy lại thì ghi đè
    chứ không cộng dồn. Row do `record` tạo tay được giữ nguyên. Fail-open tuyệt đối.
    """
    try:
        src = root / "harness" / "metrics" / "cost-by-session.json"
        if not src.exists():
            return -1, None
        data = json.loads(src.read_text(encoding="utf-8") or "{}")
        if not isinstance(data, dict):
            return -1, None
        rows, latest = [], None
        for sid, v in data.items():
            if not isinstance(v, dict):
                continue
            tk = v.get("tokens") or {}
            # cache_read KHÔNG cộng vào input: giá khác hẳn, gộp vào là thổi phồng chi phí.
            row = {"session": sid, "source": "cost-sync",
                   "in": int(tk.get("input_tokens") or 0),
                   "out": int(tk.get("output_tokens") or 0),
                   "model": (v.get("models") or ["default"])[-1],
                   "turns": int(v.get("turns") or 0)}
            row["usd"] = cost_usd(row["in"], row["out"], row["model"], load_config(root).get("rates", {}))
            # calls: xấp xỉ bằng số lượt — hook không thấy được số model-call thật, nên khai
            # một xấp xỉ đo được còn hơn để trần treo trên số 0 vĩnh viễn.
            row["calls"] = row["turns"]
            rows.append(row)
            latest = sid
        path = _metrics_file(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        keep = []
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("source") != "cost-sync":      # giữ row ghi tay, chỉ thay row sync
                    keep.append(r)
        with path.open("w", encoding="utf-8") as f:
            for r in keep + rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return len(rows), latest
    except Exception:
        return -1, None                                  # fail-open: sổ tiền không được phá phiên


def main() -> None:
    args = sys.argv[1:]
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    r = _opt(args, "--root")
    if r:
        root = Path(r)
    in_tok = _opt(args, "--in"); out_tok = _opt(args, "--out"); model = _opt(args, "--model"); task = _opt(args, "--task")
    counters = {}
    for flag, (key, _) in COUNTERS.items():
        v = _opt(args, "--" + flag)
        try:
            counters[key] = int(v or 0)
        except ValueError:                     # fail-open: counter rác thì bỏ qua, không phá phiên
            pass
    if "--self-test" in args:
        sys.exit(self_test())
    if "--report" in args:
        print(report(root)); return
    if args and args[0] == "record":
        if len(args) < 2:
            print("usage: token-budget.py record SESSION --in N --out M [--model X] "
                  "[--calls N] [--subagents N] [--workers N] [--graph-writes N]", file=sys.stderr); sys.exit(2)
        rec = record(root, args[1], in_tok or 0, out_tok or 0, model, task, counters)
        extra = "".join(f" {key}={rec[key]}" for key, _ in COUNTERS.values() if key in rec)
        print(f"recorded {rec['session']}: in={rec['in']} out={rec['out']} model={rec['model']}{extra}"); return
    if args and args[0] == "sync":
        n, sess = sync_from_cost(root)
        if n < 0:
            print("[token-budget] chưa có cost-by-session.json — không có gì để đồng bộ"); return
        print(f"[token-budget] sync {n} phiên từ cost-by-session.json"
              + (f" (mới nhất: {sess})" if sess else "")); return
    if args and args[0] == "check":
        if len(args) < 2:
            print("usage: token-budget.py check SESSION", file=sys.stderr); sys.exit(2)
        cfg = load_config(root)
        row = totals(root, cfg).get(args[1], {"in": 0, "out": 0, "usd": 0.0})
        breaches = over_budget(row, cfg)
        if not breaches:
            print(f"[token-budget] {args[1]} within budget (${row['usd']:.3f})"); sys.exit(0)
        msg = f"[token-budget] {args[1]} OVER: " + "; ".join(breaches)
        if str(cfg.get("mode")).lower() == "block" and cfg.get("verified") is True:
            print(msg + "  (mode:block)", file=sys.stderr); sys.exit(2)
        print(msg + "  (mode:warn — set mode:block + verified:true to enforce)", file=sys.stderr); sys.exit(0)
    print(__doc__)


if __name__ == "__main__":
    main()
