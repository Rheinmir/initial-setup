#!/usr/bin/env python3
"""self-report — hệ tự chấm: đọc CÁC SỔ ĐÃ CÓ, chấm "hệ đang chạy tốt tới đâu", và khi phát hiện
vấn đề tái diễn thì tự RAISE ISSUE về repo mẹ (rheinmir/setup) — sớm, có bằng chứng, không spam.

Vì sao: mọi tín hiệu đã được ghi sẵn (token-budget, biên lai okf-scan, chuỗi episode, wiki-sync,
wiki-health, flywheel) nhưng KHÔNG AI ĐỌC CHÚNG CÙNG NHAU. Một chỉ số lẻ thì vô nghĩa; đặt cạnh
nhau mới thấy "recall trả về thứ agent không bao giờ mở" hay "wiki drift 3 phiên liền chưa ai rà".
Tất định, 0 token LLM — chấm bằng ngưỡng, không bằng ý kiến.

  --report [--json]              chấm hệ, in bảng (mặc định)
  --check                        exit 2 nếu có finding mức 'high' (dùng làm gate)
  --raise [--dry-run]            tạo issue cho finding chưa từng raise (dedupe + cooldown + cap)
  --self-test

Cấu hình: harness/self-report.config.yaml (every, raise, repo, thresholds — verified:false).
Lịch sử: harness/metrics/self-report.jsonl · đã raise: harness/metrics/self-report-raised.json

RIÊNG TƯ: issue chỉ mang SỐ ĐO + tên lớp vấn đề + đường dẫn tương đối. TUYỆT ĐỐI không nội dung
file, không prompt, không transcript — repo mẹ là public.
Fail-open: mọi lỗi hạ tầng → exit 0. Công cụ đo không được phá phiên.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

MET = "harness/metrics"
HIST = f"{MET}/self-report.jsonl"
RAISED = f"{MET}/self-report-raised.json"
DEFAULTS = {
    "every": 50,                 # bao nhiêu prompt thì chấm một lần (hook UserPromptSubmit)
    "raise": "auto",             # auto | propose | off
    "repo": "rheinmir/setup",
    "cooldown_days": 7,          # cùng một lớp vấn đề: không raise lại trong N ngày
    "max_per_run": 2,            # trần chống spam
    "min_sessions": 3,           # dưới ngưỡng này thì chưa đủ dữ liệu để kết luận
    "coverage_floor": 0.34,      # recall trả về mà agent mở < mức này = tín hiệu xấu
    "budget_near": 0.85,
}


def _now():
    return datetime.now(timezone.utc)


def load_cfg(root: Path) -> dict:
    cfg = dict(DEFAULTS)
    try:
        import yaml
        d = yaml.safe_load((root / "harness" / "self-report.config.yaml").read_text(encoding="utf-8"))
        if isinstance(d, dict):
            for k, v in d.items():
                if v is not None:
                    cfg[k] = v
    except Exception:
        pass
    return cfg


def _jsonl(p: Path):
    out = []
    try:
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                out.append(json.loads(ln))
    except Exception:
        pass
    return out


def _json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def _run(root: Path, args, timeout=25):
    try:
        r = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 127, str(e)[:200]


# ── thu số đo từ các sổ ĐÃ CÓ (không đẻ sổ mới) ──────────────────────────────────────────
def gather(root: Path, cfg: dict) -> dict:
    m = {"ts": _now().isoformat(timespec="seconds"), "root": str(root)}

    cost = _json(root / MET / "cost-by-session.json", {})
    sess = list(cost.values()) if isinstance(cost, dict) else (cost or [])
    m["sessions"] = len(sess)
    m["turns_avg"] = round(sum(int(s.get("turns") or 0) for s in sess) / len(sess), 1) if sess else 0
    m["tokens_max"] = max([int((s.get("tokens") or {}).get("input_tokens", 0))
                           + int((s.get("tokens") or {}).get("output_tokens", 0)) for s in sess] or [0])

    rec = _jsonl(root / MET / "context-receipts.jsonl")
    scans = [r for r in rec if r.get("kind") != "verify"]
    vers = [r for r in rec if r.get("kind") == "verify"]
    m["scans"] = len(scans)
    m["scan_sessions"] = len({r.get("session") for r in scans if r.get("session")})
    m["returned_avg"] = round(sum(len(r.get("returned") or []) for r in scans) / len(scans), 2) if scans else 0
    covs = [float(v.get("coverage") or 0) for v in vers if (v.get("returned") or [])]
    m["coverage_avg"] = round(sum(covs) / len(covs), 3) if covs else None
    m["verifies"] = len(covs)

    eps = [x for x in _jsonl(root / MET / "memory.jsonl") if x.get("kind") == "episode"]
    m["episodes"] = len(eps)
    m["episodes_orphan"] = sum(1 for e in eps if not e.get("parent"))
    m["chain_max"] = 0
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("mr", HERE / "mem-rank.py")
        mr = importlib.util.module_from_spec(spec); spec.loader.exec_module(mr)
        m["chain_max"] = len(mr.chain(root))
    except Exception:
        pass

    rc, _ = _run(root, [sys.executable, str(HERE / "wiki-sync.py"), "--check"], timeout=30)
    m["wiki_drift"] = (rc == 3)
    m["wiki_anchor_missing"] = (rc == 2)

    wd = next((d for d in ("fdk/wiki", ".llmwiki/wiki", "llmwiki/wiki") if (root / d).is_dir()), None)
    m["broken_links"] = None
    if wd:
        rc, out = _run(root, [sys.executable, str(HERE / "wiki-health.py"), "--wiki-dir", wd], timeout=40)
        try:
            m["broken_links"] = len(json.loads(out).get("broken_wikilinks") or [])
        except Exception:
            pass

    hv = _json(root / MET / "handover-state.json", {})
    m["handovers"] = len(list((root / ".llmwiki" / "handover").glob("*-continue.md"))) \
        if (root / ".llmwiki" / "handover").is_dir() else len(hv)

    rc, out = _run(root, [sys.executable, str(HERE / "flywheel.py"), "--kind", "failure", "--report"], timeout=20)
    m["failure_classes"] = sum(1 for ln in out.splitlines() if ln.strip().startswith(("-", "•"))) if rc == 0 else 0
    return m


# ── chấm: mỗi finding có bằng chứng + ngưỡng + cách sửa ──────────────────────────────────
def findings(m: dict, cfg: dict) -> list:
    f = []

    def add(key, sev, title, evidence, fix):
        f.append({"key": key, "severity": sev, "title": title, "evidence": evidence, "fix": fix})

    enough = m["sessions"] >= int(cfg["min_sessions"])

    if enough and m["scan_sessions"] == 0:
        add("recall-never-ran", "high",
            "Không phiên nào để lại biên lai quét context",
            f"{m['sessions']} phiên có số đo, 0 phiên có biên lai okf-scan",
            "Hook SessionStart chưa nạp (mở session mới / `/hooks` reload) hoặc thiếu okf-scan.py "
            "ở bản global — chạy lại installer.")
    elif enough and m["scan_sessions"] < m["sessions"] / 2:
        add("recall-partial", "medium",
            "Quá nửa số phiên không quét context",
            f"{m['scan_sessions']}/{m['sessions']} phiên có biên lai",
            "Kiểm hook SessionStart có chạy ở mọi phiên không (hook global cần stamp .harness-stamp).")

    if m["coverage_avg"] is not None and m["verifies"] >= 3 and m["coverage_avg"] < float(cfg["coverage_floor"]):
        add("recall-coverage-low", "high",
            "Recall trả về thứ agent hầu như không mở",
            f"coverage trung bình {m['coverage_avg']:.0%} qua {m['verifies']} phiên "
            f"(trả về ~{m['returned_avg']} mục/lần)",
            "Truy vấn/tag của okf-scan đang lệch nhu cầu thật: xem lại cách sinh query trong "
            "session_start.recall(), hoặc bổ sung `tags` cho trang wiki hay dùng.")

    if m["episodes"] >= 3 and m["episodes_orphan"] > m["episodes"] / 2:
        add("episode-chain-broken", "medium",
            "Chuỗi phiên gãy — quá nửa episode không có cha",
            f"{m['episodes_orphan']}/{m['episodes']} episode thiếu `parent`",
            "Stop-hook có truyền `--parent auto` không? Bản global cũ chưa có — chạy lại installer.")

    if m["wiki_drift"]:
        add("wiki-drift", "medium", "Code đã đổi nhưng wiki chưa được rà",
            "wiki-sync --check exit 3 (có cờ code-drift trong stale.json)",
            "Chạy `/lint` rà các trang bị cờ rồi `wiki-sync.py --mark-synced`.")
    if m["wiki_anchor_missing"]:
        add("wiki-anchor-missing", "low", "Neo wiki-sync mất hiệu lực",
            "wiki-sync --check exit 2 (chưa có neo hoặc neo hỏng sau rebase)",
            "Chạy `wiki-sync.py --mark-synced` để neo lại.")
    if m["broken_links"]:
        add("wiki-broken-links", "medium", "Wiki có wikilink gãy",
            f"{m['broken_links']} wikilink trỏ trang không tồn tại",
            "Chạy `wiki-health.py --wiki-dir <wiki>` xem danh sách rồi sửa hoặc đổi sang đường dẫn.")

    if m["handovers"] >= 3 and m["sessions"] and m["handovers"] > m["sessions"] / 2:
        add("handover-churn", "medium", "Bàn giao quá dày — trần có thể đặt quá thấp",
            f"{m['handovers']} lần bàn giao / {m['sessions']} phiên (trung bình {m['turns_avg']} lượt/phiên)",
            "Nâng trần trong token-budget.config.yaml (`token-budget.py configure`) hoặc bỏ bớt "
            "mục khỏi `auto_handover.triggers`.")
    return f


def fingerprint(root: Path, fd: dict) -> str:
    return f"self-report:{fd['key']}"


# ── raise issue về repo mẹ — dedupe, cooldown, trần ──────────────────────────────────────
def raise_findings(root: Path, cfg: dict, fs: list, dry_run=False) -> list:
    mode = str(cfg.get("raise", "auto")).lower()
    if mode == "off" or not fs:
        return []
    state = _json(root / RAISED, {})
    out, made = [], 0
    for fd in [x for x in fs if x["severity"] in ("high", "medium")]:
        if made >= int(cfg["max_per_run"]):
            break
        fp = fingerprint(root, fd)
        last = state.get(fp, {}).get("ts")
        if last:
            try:
                if _now() - datetime.fromisoformat(last) < timedelta(days=int(cfg["cooldown_days"])):
                    out.append({**fd, "action": "cooldown", "since": last})
                    continue
            except Exception:
                pass
        body = issue_body(root, fd, fp)
        title = f"[self-report] {fd['title']}"
        if mode == "propose" or dry_run:
            # Trần áp cho CẢ propose: một lượt đổ 5 đề xuất vào mặt người dùng cũng là spam,
            # chỉ là spam ở chỗ khác. Bug thật, bắt bằng self-test (trần từng chỉ đếm raise thành công).
            out.append({**fd, "action": "propose", "title": title, "body": body})
            made += 1
            continue
        # dedupe phía remote: cùng fingerprint đã có issue (kể cả đã đóng) thì thôi
        rc, o = _run(root, ["gh", "issue", "list", "--repo", str(cfg["repo"]), "--state", "all",
                            "--search", fp, "--json", "number", "--limit", "1"], timeout=25)
        if rc == 0 and (o or "").strip() not in ("", "[]"):
            state[fp] = {"ts": _now().isoformat(timespec="seconds"), "note": "đã có issue remote"}
            out.append({**fd, "action": "duplicate"})
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
            tf.write(body); bp = tf.name
        rc, o = _run(root, ["gh", "issue", "create", "--repo", str(cfg["repo"]),
                            "--title", title, "--body-file", bp, "--label", "needs-triage"], timeout=40)
        os.unlink(bp)
        url = (o or "").strip().splitlines()[-1] if rc == 0 else ""
        state[fp] = {"ts": _now().isoformat(timespec="seconds"), "url": url, "rc": rc}
        out.append({**fd, "action": "raised" if rc == 0 else "raise-failed", "url": url, "log": o[:200]})
        made += 1
    try:
        (root / RAISED).parent.mkdir(parents=True, exist_ok=True)
        (root / RAISED).write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    return out


def issue_body(root: Path, fd: dict, fp: str) -> str:
    """CHỈ số đo + tên lớp + đường dẫn tương đối. Không nội dung file, không prompt, không transcript."""
    return f"""> Sinh tự động bởi `harness/scripts/self-report.py` từ số đo trong sổ của một bản cài overstack.
> Fingerprint: `{fp}` (dùng để dedupe — đừng sửa dòng này).

## Vấn đề
{fd['title']}

## Bằng chứng (số đo, không phải ý kiến)
{fd['evidence']}

## Hướng sửa đề xuất
{fd['fix']}

## Ghi chú
- Mức: **{fd['severity']}** · phát hiện lúc {_now().isoformat(timespec='minutes')}
- Báo cáo này chỉ mang **số tổng hợp**; không kèm nội dung file, prompt hay transcript.
- Xem tại chỗ: `python3 harness/scripts/self-report.py --report`
"""


def render(m: dict, fs: list) -> str:
    cov = f"{m['coverage_avg']:.0%}" if m["coverage_avg"] is not None else "chưa đo"
    L = ["HỆ ĐANG CHẠY TỐT TỚI ĐÂU (số đo từ sổ, 0 token)", "",
         f"  phiên đã ghi số đo      {m['sessions']}  (trung bình {m['turns_avg']} lượt/phiên)",
         f"  quét context (biên lai) {m['scans']} lần / {m['scan_sessions']} phiên · trả về ~{m['returned_avg']} mục",
         f"  agent MỞ thứ trả về     {cov}  ({m['verifies']} phiên đối chiếu transcript)",
         f"  episode / chuỗi dài nhất {m['episodes']} / {m['chain_max']}  · mồ côi {m['episodes_orphan']}",
         f"  wiki                    drift={'CÓ' if m['wiki_drift'] else 'không'}"
         + (f" · wikilink gãy {m['broken_links']}" if m["broken_links"] is not None else ""),
         f"  bàn giao tự động        {m['handovers']}", ""]
    if not fs:
        L.append("  ✓ không phát hiện vấn đề nào vượt ngưỡng")
    else:
        L.append(f"  PHÁT HIỆN {len(fs)}:")
        for fd in fs:
            L.append(f"   [{fd['severity']}] {fd['title']}")
            L.append(f"      bằng chứng: {fd['evidence']}")
            L.append(f"      sửa: {fd['fix']}")
    return "\n".join(L)


def self_test() -> int:
    ok = True

    def chk(c, msg):
        nonlocal ok
        print(("  \033[1;32m✓\033[0m " if c else "  \033[1;31m✗\033[0m ") + msg)
        ok = ok and bool(c)

    with tempfile.TemporaryDirectory() as t:
        root = Path(t); (root / MET).mkdir(parents=True)
        cfg = dict(DEFAULTS)
        base = {"sessions": 6, "turns_avg": 20, "tokens_max": 100, "scans": 6, "scan_sessions": 6,
                "returned_avg": 3, "coverage_avg": 0.8, "verifies": 6, "episodes": 5,
                "episodes_orphan": 1, "chain_max": 5, "wiki_drift": False, "wiki_anchor_missing": False,
                "broken_links": 0, "handovers": 0, "failure_classes": 0}
        chk(findings(base, cfg) == [], "hệ khoẻ → không finding nào")

        m2 = dict(base, scan_sessions=0)
        chk([x["key"] for x in findings(m2, cfg)] == ["recall-never-ran"], "0 phiên có biên lai → recall-never-ran (high)")

        m3 = dict(base, coverage_avg=0.1)
        f3 = findings(m3, cfg)
        chk(any(x["key"] == "recall-coverage-low" and x["severity"] == "high" for x in f3),
            "coverage 10% → recall-coverage-low (high)")

        m4 = dict(base, sessions=2, scan_sessions=0)
        chk(findings(m4, cfg) == [], "dưới min_sessions → chưa kết luận (không báo bừa)")

        m5 = dict(base, episodes=6, episodes_orphan=5)
        chk(any(x["key"] == "episode-chain-broken" for x in findings(m5, cfg)), "quá nửa episode mồ côi → chain-broken")

        m6 = dict(base, wiki_drift=True, broken_links=3, handovers=5)
        keys = {x["key"] for x in findings(m6, cfg)}
        chk({"wiki-drift", "wiki-broken-links", "handover-churn"} <= keys, f"bắt drift + link gãy + churn ({sorted(keys)})")

        # raise: dry-run không gọi mạng; cooldown chặn lần hai; trần max_per_run
        fs = findings(m6, cfg)
        res = raise_findings(root, dict(cfg, raise_="auto"), fs, dry_run=True)
        chk(all(r["action"] == "propose" for r in res) and len(res) <= int(cfg["max_per_run"]),
            f"--dry-run chỉ đề xuất, tôn trọng trần {cfg['max_per_run']} ({len(res)})")

        (root / RAISED).write_text(json.dumps(
            {fingerprint(root, fs[0]): {"ts": _now().isoformat(timespec='seconds')}}), encoding="utf-8")
        res2 = raise_findings(root, cfg, fs, dry_run=True)
        chk(any(r["action"] == "cooldown" for r in res2), "cooldown: lớp vừa raise không raise lại")

        chk(raise_findings(root, dict(cfg, **{"raise": "off"}), fs, dry_run=True) == [],
            "raise: off → không làm gì")

        body = issue_body(root, fs[0], "self-report:x")
        chk("Fingerprint" in body and "transcript" in body and str(root) not in body,
            "body issue có fingerprint, tự khai không kèm transcript, không lộ đường tuyệt đối")

        out = render(base, [])
        chk("HỆ ĐANG CHẠY" in out and "không phát hiện vấn đề" in out, "render đọc được khi hệ khoẻ")

    print("self-report self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 2


def _opt(args, flag, default=None):
    if flag in args:
        i = args.index(flag)
        return args[i + 1] if i + 1 < len(args) else default
    return default


def main() -> None:
    args = sys.argv[1:]
    if "--self-test" in args:
        sys.exit(self_test())
    root = Path(_opt(args, "--root") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    try:
        cfg = load_cfg(root)
        m = gather(root, cfg)
        fs = findings(m, cfg)
        try:
            (root / HIST).parent.mkdir(parents=True, exist_ok=True)
            with open(root / HIST, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({**m, "findings": [x["key"] for x in fs]}, ensure_ascii=False) + "\n")
        except Exception:
            pass
        raised = raise_findings(root, cfg, fs, "--dry-run" in args) if "--raise" in args else []
        if "--json" in args:
            print(json.dumps({"metrics": m, "findings": fs, "raised": raised}, ensure_ascii=False, indent=1))
        else:
            print(render(m, fs))
            for r in raised:
                if r["action"] == "raised":
                    print(f"  → đã raise issue: {r.get('url')}")
                elif r["action"] in ("cooldown", "duplicate"):
                    print(f"  → bỏ qua ({r['action']}): {r['title'] if 'title' in r else r['key']}")
                elif r["action"] == "propose":
                    print(f"  → đề xuất raise (chưa gửi): {r['title']}")
        if "--check" in args and any(x["severity"] == "high" for x in fs):
            sys.exit(2)
    except SystemExit:
        raise
    except Exception as e:
        print(f"self-report: lỗi hạ tầng, bỏ qua (fail-open): {e}", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
