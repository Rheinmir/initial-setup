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
                         "max_concurrent_workers": 8, "per_session_graph_writes": 200,
                         "per_session_tool_calls": 2000, "min_evidence": 0},
             "rates": {"default": {"input": 0.003, "output": 0.015}}}

COUNTERS = {  # cờ CLI -> (khoá trong row JSONL, khoá budget trong config)
    "calls":        ("calls",        "per_session_model_calls"),
    "subagents":    ("subagents",    "per_workflow_subagents"),
    "workers":      ("workers",      "max_concurrent_workers"),
    "graph-writes": ("graph_writes", "per_session_graph_writes"),
    "tool-calls":   ("tool_calls",   "per_session_tool_calls"),
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
                        "max_concurrent_workers": 8, "per_session_graph_writes": 200,
                         "per_session_tool_calls": 2000, "min_evidence": 0}}
    with tempfile.TemporaryDirectory() as td:
        record(td, "s1", 10, 10, counters={"calls": 2})
        record(td, "s1", 10, 10, counters={"calls": 2})
        row = totals(td, cfg2)["s1"]
    sum_ok = row["calls"] == 4 and row["in"] == 20 and row["subagents"] == 0
    breach = over_budget(row, cfg2)                               # calls 4>3, các trần khác trong hạn
    calls_ok = len(breach) == 1 and "per_session_model_calls" in breach[0]
    legacy_ok = over_budget({"in": 1, "out": 1, "usd": 0.0}, cfg2) == []   # row JSONL cũ thiếu khoá counter
    # ── bước hỏi lúc cài (configure) — khoá bằng test tất định, KHÔNG dựa pty ────────────
    class _FakeTTY:
        """tty giả: trả lần lượt các câu người dùng gõ. Test pty thật bị echo làm nhiễu."""
        def __init__(self, answers): self.a = list(answers); self.out = []
        def write(self, s): self.out.append(s)
        def flush(self): pass
        def readline(self): return self.a.pop(0) if self.a else ""
        def close(self): pass

    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        (r / "harness" / "metrics").mkdir(parents=True)
        (r / "harness" / "metrics" / "cost-by-session.json").write_text(json.dumps(
            {"s": {"turns": 100, "models": ["opus"],
                   "tokens": {"input_tokens": 1000, "output_tokens": 2000}}}), encoding="utf-8")
        obs = observed(r)
        obs_ok = obs.get("turns") == 100 and obs.get("tokens") == 3000 and obs.get("usd", 0) > 0

        # Enter hết = nhận gợi ý; gợi ý phải bám SỐ ĐO (2× turns = 200 calls), không phải số đoán.
        t = _FakeTTY(["y\n"] + ["\n"] * 8 + ["warn\n"])
        configure_with(r, t)
        c1 = load_config(r)
        sug_ok = c1["budgets"]["per_session_model_calls"] == 200
        warn_ok = c1.get("mode") == "warn" and c1.get("verified") is False

        # chọn block ⇒ verified bật theo (chữ ký "tôi đã xem và chấp nhận các con số này")
        t2 = _FakeTTY(["y\n"] + ["\n"] * 8 + ["block\n"])
        configure_with(r, t2)
        c2 = load_config(r)
        block_ok = c2.get("mode") == "block" and c2.get("verified") is True

        # giá trị gõ tay phải thắng gợi ý
        t3 = _FakeTTY(["y\n", "12345\n", "1.5\n", "7\n", "\n", "\n", "\n", "\n", "\n", "warn\n"])
        configure_with(r, t3)
        c3 = load_config(r)
        typed_ok = (c3["budgets"]["per_session_tokens"] == 12345
                    and abs(c3["budgets"]["per_task_usd"] - 1.5) < 1e-9
                    and c3["budgets"]["per_session_model_calls"] == 7)

        # nhập rác KHÔNG được phá config (giữ nguyên bản trước, không crash)
        t4 = _FakeTTY(["y\n", "không-phải-số\n"] + ["\n"] * 8)
        rc_bad = configure_with(r, t4)
        c4 = load_config(r)
        junk_ok = rc_bad == 0 and c4["budgets"]["per_session_tokens"] == 12345

        # MẶC ĐỊNH KHÔNG HỎI THÊM: Enter ở câu đầu → thoát ngay, không hỏi câu nào, không ghi file.
        t5 = _FakeTTY(["\n"])
        rc_skip = configure_with(r, t5)
        c5 = load_config(r)
        skip_ok = (rc_skip == 0 and c5["budgets"]["per_session_tokens"] == 12345
                   and "◇" not in "".join(t5.out))

    conf_ok = obs_ok and sug_ok and warn_ok and block_ok and typed_ok and junk_ok and skip_ok
    ok = (cost_ok and not within and len(over) == 2 and sum_ok and calls_ok
          and legacy_ok and conf_ok)
    if not conf_ok:
        print(f"  configure: obs={obs_ok} sug={sug_ok} warn={warn_ok} "
              f"block={block_ok} typed={typed_ok} junk={junk_ok} skip={skip_ok}")
    print("token-budget self-test:", "ALL PASS" if ok else "FAIL")
    return 0 if ok else 1


def _opt(args, flag):
    if flag in args:
        i = args.index(flag); v = args[i + 1] if len(args) > i + 1 else None; del args[i:i + 2]; return v
    return None


def observed(root: Path) -> dict:
    """Số ĐO THẬT từ cost-by-session.json — dùng làm gợi ý khi hỏi, thay cho số đoán.

    Đặt trần bằng cách bốc một con số tròn là cách chắc chắn nhất để hoặc chặn nhầm việc
    thật, hoặc không bao giờ chạm trần. Gợi ý theo phiên nặng nhất đã đo được thì trần bám
    workload thật của chính máy này.
    """
    try:
        src = root / "harness" / "metrics" / "cost-by-session.json"
        if not src.exists():
            return {}
        data = json.loads(src.read_text(encoding="utf-8") or "{}")
        best = {"tokens": 0, "usd": 0.0, "turns": 0, "sessions": 0}
        cfg_rates = load_config(root).get("rates", {})
        for v in data.values():
            if not isinstance(v, dict):
                continue
            tk = v.get("tokens") or {}
            i, o = int(tk.get("input_tokens") or 0), int(tk.get("output_tokens") or 0)
            model = (v.get("models") or ["default"])[-1]
            best["sessions"] += 1
            best["tokens"] = max(best["tokens"], i + o)
            best["turns"] = max(best["turns"], int(v.get("turns") or 0))
            best["usd"] = max(best["usd"], cost_usd(i, o, model, cfg_rates))
        return best if best["sessions"] else {}
    except Exception:
        return {}


# ── khung hỏi (wizard một cột, không phải log thô) ───────────────────────────────────────
# Đây là thứ ĐẦU TIÊN người mới thấy sau curl|bash. Log thô trông như tràn lỗi; một cột
# ┌ │ └ tách câu hỏi khỏi gợi ý thì đọc được ngay cả khi terminal đang cuộn nhanh.
_D, _C, _G, _B, _R = "\033[2m", "\033[36m", "\033[32m", "\033[1m", "\033[0m"


def _w(tty, text: str) -> None:
    try:
        tty.write(text); tty.flush()
    except Exception:
        pass


def _open(tty, title: str) -> None:
    _w(tty, f"\n{_D}┌{_R}  {_B}{title}{_R}\n{_D}│{_R}\n")


def _note(tty, text: str) -> None:
    _w(tty, f"{_D}│{_R}  {_D}{text}{_R}\n")


def _close(tty, text: str) -> None:
    _w(tty, f"{_D}│{_R}\n{_D}└{_R}  {text}\n\n")


def _ask(prompt: str, default, tty, hint: str = ""):
    """Hỏi một câu qua /dev/tty trong khung. Enter = giữ mặc định. Không có tty → mặc định im lặng."""
    if tty is None:
        return default
    try:
        _w(tty, f"{_D}│{_R}\n{_C}◇{_R}  {prompt}\n")
        if hint:
            _w(tty, f"{_D}│{_R}  {_D}{hint}{_R}\n")
        _w(tty, f"{_D}│{_R}  {_C}›{_R} {_D}[{default}]{_R} ")
        line = tty.readline().strip()
        return default if not line else line
    except Exception:
        return default


def _ask_yes(prompt: str, tty, hint: str = "") -> bool:
    """Câu Có/Không, MẶC ĐỊNH KHÔNG — Enter là thoát, không ép ai đi hết một route hỏi đáp."""
    if tty is None:
        return False
    try:
        _w(tty, f"{_D}│{_R}\n{_C}◆{_R}  {prompt}\n")
        if hint:
            _w(tty, f"{_D}│{_R}  {_D}{hint}{_R}\n")
        _w(tty, f"{_D}│{_R}  {_C}›{_R} {_D}[Enter = không]{_R} ")
        return tty.readline().strip().lower() in ("y", "yes", "c", "co", "có", "1")
    except Exception:
        return False


def configure(root: Path, if_tty: bool = False) -> int:
    """Bước hỏi lúc cài: đặt trần theo workload THẬT, rồi mới bật chặn.

    Vì sao phải hỏi thay vì ship số mặc định + bật block luôn: mọi trần trong config đều gắn
    `# ASSUMPTION (not verified)` — bật `mode: block` trên một con số đoán thì hoặc nó chặn
    nhầm việc thật (đo được: một phiên dev bình thường đã $6.74, vượt trần đoán $5), hoặc nó
    treo quá cao nên chẳng bao giờ cắn. Cả hai đều tệ hơn không có trần, vì chúng tạo cảm
    giác an toàn giả.

    curl | bash chiếm mất stdin, nên đọc từ /dev/tty. Không có tty (CI, headless) → giữ
    nguyên mặc định và nói rõ cách chỉnh sau, KHÔNG treo chờ nhập.
    """
    try:
        tty = open("/dev/tty", "r+")
    except Exception:
        tty = None
    if tty is None:
        print("[token-budget] không có terminal — giữ trần mặc định (mode: warn).\n"
              "  chỉnh sau: python3 harness/scripts/token-budget.py configure")
        return 0
    return configure_with(root, tty)


def configure_with(root: Path, tty) -> int:
    """Phần hỏi thuần — nhận tty đã mở, nên self-test bơm được tty giả.

    Tách khỏi `configure()` vì test qua pty thật bị echo terminal làm nhiễu: đo được lần trước
    là 6/7 câu đúng còn câu cuối đọc nhầm echo. Cổng chỉ đúng trên một máy thì không phải cổng.

    Câu ĐẦU TIÊN là Có/Không, mặc định KHÔNG: phần lớn người cài chỉ muốn xong việc; ép trả lời
    9 câu về trần trước khi dùng được là thu phí sai chỗ. Chọn không → giữ mặc định, KHÔNG ghi
    file (verified vẫn false), in đúng một dòng cách chỉnh sau.
    """
    cfg = load_config(root)
    b = dict(cfg.get("budgets") or {})
    obs = observed(root)

    _open(tty, "overstack · trần phiên & độ phức tạp")
    if obs:
        _note(tty, f"Đo trên máy này: {obs['sessions']} phiên · nặng nhất {obs['tokens']:,} token "
                   f"· {obs['turns']} lượt · ~${obs['usd']:.2f}")
        _note(tty, "Gợi ý bên dưới = ~2× phiên nặng nhất (đủ chỗ thở, vẫn bắt được ca bất thường).")
    else:
        _note(tty, "Chưa có dữ liệu đo — mặc định là số ĐOÁN, chỉnh lại sau khi chạy vài phiên.")
    _note(tty, "Vượt trần → tự bàn giao sang phiên mới (session-continue), không mất việc.")

    if not _ask_yes("Tự đặt trần bây giờ?", tty,
                    "Enter = dùng mặc định, xong luôn · y = đặt 8 thông số"):
        _close(tty, f"{_G}✓{_R} giữ mặc định "
                    f"{_D}(chỉnh sau: python3 harness/scripts/token-budget.py configure){_R}")
        if tty is not None and hasattr(tty, "close"):
            tty.close()
        return 0

    # Có số đo → gợi ý bám ĐO THẬT (2×). KHÔNG lấy max() với mặc định: mặc định là số đoán,
    # kẹp sàn theo nó thì trần luôn ≥ số đoán và chẳng bao giờ cắn — đúng cái bệnh đang chữa.
    sug_tok = int(obs["tokens"] * 2) if obs.get("tokens") else b.get("per_session_tokens", 2_000_000)
    sug_usd = round(obs["usd"] * 2, 2) if obs.get("usd") else b.get("per_task_usd", 5.0)
    sug_call = int(obs["turns"] * 2) if obs.get("turns") else b.get("per_session_model_calls", 500)
    sug_tool = int(obs["tool_calls"] * 2) if obs.get("tool_calls") else b.get("per_session_tool_calls", 2000)

    try:
        b["per_session_tokens"] = int(str(_ask("max tokens / phiên", sug_tok, tty)).replace(",", "").replace("_", ""))
        b["per_task_usd"] = float(_ask("max chi phí USD / task", sug_usd, tty,
                                       "gói subscription: số này chỉ để xem — mặc định KHÔNG kích hoạt bàn giao"))
        b["per_session_model_calls"] = int(_ask("max model calls / phiên", sug_call, tty))
        b["per_workflow_subagents"] = int(_ask("max sub-agents / workflow", b.get("per_workflow_subagents", 16), tty))
        b["max_concurrent_workers"] = int(_ask("max worker song song", b.get("max_concurrent_workers", 8), tty))
        b["per_session_graph_writes"] = int(_ask("max graph writes / phiên", b.get("per_session_graph_writes", 200), tty))
        b["per_session_tool_calls"] = int(_ask("max tool calls / phiên", sug_tool, tty))
        # SÀN dưới, không phải trần trên: 0 = tắt. Ép cổng chốt phải có N bằng chứng.
        b["min_evidence"] = int(_ask("tối thiểu bao nhiêu bằng chứng để CHỐT", b.get("min_evidence", 0), tty, "0 = tắt"))
        mode = str(_ask("vượt trần thì CHẶN hay chỉ cảnh báo?", cfg.get("mode", "warn"), tty,
                        "block | warn — chỉ đổi hành vi lệnh `check` gõ tay; bàn giao tự động chạy độc lập")
                   ).strip().lower()
        mode = mode if mode in ("block", "warn") else "warn"
    except (KeyboardInterrupt, EOFError, ValueError):
        _close(tty, f"{_D}bỏ qua — giữ trần mặc định (mode: warn){_R}")
        return 0

    # verified chỉ bật khi người dùng THỰC SỰ chọn block: chữ ký "tôi đã xem và chấp nhận
    # những con số này", không phải một cờ tự bật.
    write_config(root, b, mode, verified=(mode == "block"))
    _close(tty, f"{_G}✓{_R} ghi harness/token-budget.config.yaml  "
                f"{_D}(mode: {mode}{', ĐANG CHẶN thật' if mode == 'block' else ', chỉ cảnh báo'}"
                f" · đổi sau: token-budget.py configure){_R}")
    if tty is not None and hasattr(tty, "close"):
        tty.close()
    return 0


def write_config(root: Path, budgets: dict, mode: str, verified: bool) -> None:
    """Ghi lại config, GIỮ phần rates + ghi chú adapt-checklist (chỉ thay budgets/mode/verified)."""
    p = _config_file(root)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    rates_block = ""
    keep = False
    for line in old.splitlines(keepends=True):
        if line.startswith("rates:") or line.startswith("# ADAPT-CHECKLIST"):
            keep = True
        if keep:
            rates_block += line
    stamp = "VERIFIED bởi người dùng qua `token-budget.py configure`" if verified else \
            "ASSUMPTION (chưa hiệu chỉnh) — chạy `token-budget.py configure` để đặt theo workload thật"
    body = [
        "# harness/token-budget.config.yaml — trần token/chi phí/độ phức tạp (spec §5).",
        "#",
        f"# {stamp}",
        "#",
        f"verified: {'true' if verified else 'false'}",
        f"mode: {mode}                     # block = vượt trần thì exit 2 · warn = chỉ cảnh báo",
        "",
        "budgets:",
    ]
    for k, v in budgets.items():
        body.append(f"  {k}: {v}")
    body.append("")
    p.write_text("\n".join(body) + "\n" + (rates_block or ""), encoding="utf-8")


def count_tool_calls(session: str) -> int:
    """Đếm tool-call THẬT của một phiên từ transcript.

    Không lấy được từ hook: `PostToolUse` chỉ khớp `Write|Edit|MultiEdit`, nên Bash/Read/Grep
    — phần lớn tool-call — vô hình với nó. Transcript có đủ `tool_use`, đo được 1354 hành
    động trên phiên này. Trả 0 khi không tìm thấy: thà không có số còn hơn số sai.
    """
    try:
        home = Path.home() / ".claude" / "projects"
        if not home.exists():
            return 0
        n = 0
        for slug in home.iterdir():
            if not slug.is_dir():
                continue
            for f in slug.glob(f"{session}*.jsonl"):
                with f.open(encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        if '"tool_use"' not in line:
                            continue
                        try:
                            d = json.loads(line)
                        except Exception:
                            continue
                        c = (d.get("message") or {}).get("content")
                        if isinstance(c, list):
                            n += sum(1 for b in c if isinstance(b, dict) and b.get("type") == "tool_use")
        return n
    except Exception:
        return 0


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
            row["tool_calls"] = count_tool_calls(sid)   # đo thật từ transcript, 0 nếu không thấy
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
    if args and args[0] == "configure":
        sys.exit(configure(root, "--if-tty" in args))
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
