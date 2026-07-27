#!/usr/bin/env python3
"""code-logger — ghi log framework BẰNG CODE, không phụ thuộc agent nhớ.

Xem llmwiki/wiki/concepts/log-model.md để biết sổ này khác gì scratch-log/mem-rank/
touches/provenance-log — mỗi sổ trả lời một câu hỏi hẹp, KHÔNG phối hợp với nhau.

Vấn đề: AGENT.md/CLAUDE.md bảo "ALWAYS append to wiki/log.md after every operation" —
nhưng đó là kỷ luật con-người/agent, agent QUÊN là chuyện thường → log.md drift, không
phản ánh thực tế. Cùng họ với `hooklib.audit()` (đã ghi raw event BẰNG CODE) và
`harness-events.py _machine_log` ("model không thể quên log"). code-logger nâng cấp ý đó
cho LOG NGHIỆP VỤ (curated), không chỉ raw audit:

1. record(root, event, **fields)  — gọi TỪ HOOK (PostToolUse…). Append 1 dòng JSONL vào
   harness/metrics/events.jsonl. Đây là "sổ cái" framework: mọi thay đổi file framework
   được CODE ghi lại, không nhờ agent. (events.jsonl gitignored — lịch sử local thô.)
2. render_md(root)  — sinh lại block <!-- log:auto:start --> … <!-- log:auto:end --> trong
   llmwiki/wiki/log.md từ events.jsonl. Gọi từ Stop hook → phần "log gần đây" của log.md là
   CODE-generated; phần curated người viết NẰM NGOÀI marker được giữ nguyên.

CLI: code-logger.py [--root DIR] [--tail N | --summary | --render-md | --record EVENT k=v ...]
Fail-open TUYỆT ĐỐI: logging không bao giờ được làm gãy phiên (mọi lỗi → nuốt).
"""
import hashlib
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

AUTO_START = "<!-- log:auto:start -->"
AUTO_END = "<!-- log:auto:end -->"
# loại file framework đáng log (bỏ qua audit/, html render, file tạm)
FRAMEWORK_PREFIXES = ("llmwiki/", "harness/", "skills/", "fdk/", ".github/", ".pre-commit-config")


def _events_path(root: Path) -> Path:
    p = root / "harness" / "metrics"
    p.mkdir(parents=True, exist_ok=True)
    # events.jsonl = lịch sử local thô → gitignore
    gi = root / ".gitignore"
    try:
        if not gi.exists() or "harness/metrics/events.jsonl" not in gi.read_text(encoding="utf-8", errors="ignore"):
            with open(gi, "a", encoding="utf-8") as f:
                f.write("\n# code-logger raw event history (local)\nharness/metrics/events.jsonl\n")
    except Exception:
        pass
    return p / "events.jsonl"


def is_framework_file(rel: str) -> bool:
    rel = (rel or "").replace("\\", "/").lstrip("./")
    return rel.endswith((".md", ".py", ".sh", ".yaml", ".yml", ".json")) and rel.startswith(FRAMEWORK_PREFIXES)


def _chain_hash(prev_h: str, body: dict) -> str:
    """Hash 1 mắt xích = sha256(prev_h + nội-dung-chuẩn-hoá). Bao cả `prev` (nằm trong body)."""
    canon = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256((str(prev_h) + "\n" + canon).encode("utf-8")).hexdigest()


def _last_hash(path: Path) -> str:
    """`h` của dòng cuối (mắt xích gần nhất). '' nếu file rỗng / dòng cuối chưa hashed (pre-audit)."""
    try:
        last = ""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for ln in f:
                if ln.strip():
                    last = ln
        return (json.loads(last).get("h") or "") if last else ""
    except Exception:
        return ""


def record(root, event: str, **fields) -> None:
    """Append 1 event vào sổ cái — gọi từ hook. Móc vào hash-chain tamper-evident. Fail-open."""
    try:
        root = Path(root)
        path = _events_path(root)
        rec = {"ts": datetime.now().isoformat(timespec="seconds"), "event": event}
        rec.update({k: v for k, v in fields.items() if v is not None})
        rec.setdefault("actor", "agent")              # event từ hook = agent; reconcile ghi đè "system"/"human"
        with open(path, "a", encoding="utf-8") as f:
            # flock TRƯỚC khi đọc đuôi: 2 session ghi đồng thời từng cùng đọc một tail
            # → 2 mắt xích cùng `prev` → chuỗi đứt oan (race 2026-07-17, dòng 1307/1308).
            try:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX)
            except Exception:
                pass                                   # không flock được (fs lạ) → thà race còn hơn mất event
            rec["prev"] = _last_hash(path) or "genesis"   # neo vào mắt xích trước (append-only)
            rec["h"] = _chain_hash(rec["prev"], rec)        # rec lúc này chưa có "h"
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _read_events(root: Path, limit: int = 0):
    try:
        lines = _events_path(root).read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out[-limit:] if limit else out


def render_md(root, keep: int = 40) -> bool:
    """Sinh lại auto-block trong wiki/log.md từ events.jsonl. Giữ nguyên text ngoài marker. Fail-open."""
    try:
        root = Path(root)
        log = root / "llmwiki" / "wiki" / "log.md"
        if not log.is_file():
            return False
        evs = _read_events(root, keep)
        if not evs:
            return False
        lines = [AUTO_START, "", "### 🤖 Log tự-động (code-logger, không do agent ghi)", "",
                 "| Thời điểm | Event | Chi tiết |", "|---|---|---|"]
        for e in evs:
            ts = e.get("ts", "").replace("T", " ")
            det = e.get("path") or e.get("file") or e.get("detail") or ""
            extra = " · ".join(f"{k}={v}" for k, v in e.items() if k not in ("ts", "event", "path", "file", "detail"))
            cell = (str(det) + (" · " + extra if extra else "")).replace("|", "\\|")[:120]
            lines.append(f"| {ts} | `{e.get('event','')}` | {cell} |")
        lines += ["", AUTO_END]
        block = "\n".join(lines)
        text = log.read_text(encoding="utf-8")
        if AUTO_START in text and AUTO_END in text:
            # marker cũ có thể đứng lệch giữa file (agent vẫn append thủ công phía dưới
            # mỗi lần) — gộp pre+post (bỏ block cũ) rồi đặt lại block ở CUỐI file, để
            # block "sự kiện mới nhất" luôn nằm đúng vị trí thời gian của nó.
            pre = text.split(AUTO_START)[0].rstrip()
            post = text.split(AUTO_END, 1)[1].strip()
            body = pre + ("\n\n" + post if post else "")
            new = body.rstrip() + "\n\n" + block + "\n"
        else:
            new = text.rstrip() + "\n\n" + block + "\n"
        log.write_text(new, encoding="utf-8")
        return True
    except Exception:
        return False


# ─── Cost Attribution (Trụ 1 Outer Harness) ──────────────────────────────────
# build-now-adapt-later: ĐƠN GIÁ token là ẩn số (đổi theo provider/thời điểm) → nhốt vào
# harness/cost-rates.json (verified:false). Engine không bao giờ hardcode con số "đúng"; nó
# dùng DEFAULT_RATES để chạy được ngay, file override (nếu có) đè lên. USD trên 1 TRIỆU token.
DEFAULT_RATES = {  # ASSUMPTION (not verified) — sửa trong harness/cost-rates.json
    "opus":   {"in": 15.0, "out": 75.0, "cache_write": 18.75, "cache_read": 1.50},
    "sonnet": {"in": 3.0,  "out": 15.0, "cache_write": 3.75,  "cache_read": 0.30},
    "haiku":  {"in": 1.0,  "out": 5.0,  "cache_write": 1.25,  "cache_read": 0.10},
    "_default": {"in": 15.0, "out": 75.0, "cache_write": 18.75, "cache_read": 1.50},
}


def _load_rates(root: Path) -> dict:
    rates = {k: dict(v) for k, v in DEFAULT_RATES.items()}
    try:
        f = root / "harness" / "cost-rates.json"
        if f.is_file():
            ov = json.loads(f.read_text(encoding="utf-8"))
            for k, v in (ov.get("rates") or {}).items():
                if isinstance(v, dict):
                    rates.setdefault(k, {}).update(v)
    except Exception:
        pass
    return rates


def _rates_verified(root: Path) -> bool:
    try:
        f = root / "harness" / "cost-rates.json"
        return bool(f.is_file() and json.loads(f.read_text(encoding="utf-8")).get("_verified"))
    except Exception:
        return False


def _rate_for(model: str, rates: dict) -> dict:
    m = (model or "").lower()
    for key in rates:
        if key not in ("_default",) and key in m:
            return rates[key]
    return rates.get("_default", DEFAULT_RATES["_default"])


def _cost_path(root: Path) -> Path:
    p = root / "harness" / "metrics"
    p.mkdir(parents=True, exist_ok=True)
    gi = root / ".gitignore"
    try:
        if not gi.exists() or "harness/metrics/cost-by-session.json" not in gi.read_text(encoding="utf-8", errors="ignore"):
            with open(gi, "a", encoding="utf-8") as f:
                f.write("harness/metrics/cost-by-session.json\n")
    except Exception:
        pass
    return p / "cost-by-session.json"


def run_cost(root, transcript: str, session: str = "") -> dict:
    """Đọc transcript JSONL của 1 RUN, cộng token theo model, quy ra cost (đơn giá adapter),
    rồi UPSERT 1 bản ghi theo session vào cost-by-session.json (idempotent — Stop bắn nhiều lần
    không nhân đôi). Đây là Trụ 1 Cost Attribution: 1 dòng cost / 1 run. Fail-open."""
    try:
        root = Path(root)
        tp = Path(transcript)
        if not tp.is_file():
            return {}
        rates = _load_rates(root)
        per_model = {}   # model → {input_tokens, output_tokens, cache_creation, cache_read}
        seen = {}        # message id → usage (dedupe streamed updates, lấy bản cuối)
        first_ts = last_ts = None
        for ln in tp.read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if o.get("type") != "assistant":
                continue
            msg = o.get("message") or {}
            u = msg.get("usage") or {}
            if not u:
                continue
            model = msg.get("model") or "?"
            # Bỏ qua turn synthetic (compaction/sidechain do Claude Code tự bơm — không phải call model thật)
            if model in ("<synthetic>", "?"):
                continue
            mid = msg.get("id") or o.get("uuid") or id(o)
            seen[mid] = (model, u)
            ts = o.get("timestamp") or o.get("ts")
            if ts:
                first_ts = first_ts or ts
                last_ts = ts
        for model, u in seen.values():
            acc = per_model.setdefault(model, {"input_tokens": 0, "output_tokens": 0,
                                               "cache_creation": 0, "cache_read": 0})
            acc["input_tokens"] += int(u.get("input_tokens") or 0)
            acc["output_tokens"] += int(u.get("output_tokens") or 0)
            acc["cache_creation"] += int(u.get("cache_creation_input_tokens") or 0)
            acc["cache_read"] += int(u.get("cache_read_input_tokens") or 0)
        if not per_model:
            return {}
        cost = 0.0
        totals = {"input_tokens": 0, "output_tokens": 0, "cache_creation": 0, "cache_read": 0}
        for model, t in per_model.items():
            r = _rate_for(model, rates)
            cost += (t["input_tokens"] * r["in"] + t["output_tokens"] * r["out"]
                     + t["cache_creation"] * r["cache_write"] + t["cache_read"] * r["cache_read"]) / 1_000_000
            for k in totals:
                totals[k] += t[k]
        rec = {
            "session": session or tp.stem,
            "project": root.resolve().name,
            "models": sorted(per_model),
            "turns": len(seen),
            "tokens": totals,
            "cost_usd": round(cost, 4),
            "rates_verified": _rates_verified(root),
            "first_ts": first_ts,
            "last_ts": last_ts,
        }
        cp = _cost_path(root)
        try:
            ledger = json.loads(cp.read_text(encoding="utf-8")) if cp.is_file() else {}
        except Exception:
            ledger = {}
        ledger[rec["session"]] = rec  # upsert: 1 run = 1 dòng, luôn mới
        cp.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")
        return rec
    except Exception:
        return {}


def cost_summary(root) -> None:
    """Break down cost theo project/model/run từ cost-by-session.json (Trụ 1)."""
    root = Path(root)
    try:
        ledger = json.loads(_cost_path(root).read_text(encoding="utf-8"))
    except Exception:
        print("cost-by-session.json: chưa có dữ liệu")
        return
    from collections import defaultdict
    by_proj = defaultdict(lambda: [0.0, 0])
    by_model = defaultdict(float)
    total = 0.0
    for r in ledger.values():
        c = float(r.get("cost_usd") or 0)
        total += c
        by_proj[r.get("project", "?")][0] += c
        by_proj[r.get("project", "?")][1] += 1
        for m in r.get("models", []):
            by_model[m] += c
    unverified = any(not r.get("rates_verified") for r in ledger.values())
    print(f"Cost Attribution — {len(ledger)} run, tổng ${total:.2f} USD"
          + ("  ⚠️ đơn giá CHƯA verify (DEFAULT_RATES)" if unverified else ""))
    print("  theo project:")
    for p, (c, n) in sorted(by_proj.items(), key=lambda x: -x[1][0]):
        print(f"    ${c:8.2f}  {n:3d} run  {p}")
    print("  theo model:")
    for m, c in sorted(by_model.items(), key=lambda x: -x[1]):
        print(f"    ${c:8.2f}  {m}")


def audit_rechain(root) -> None:
    """Sửa chuỗi ĐỨT bằng cách tính lại prev/h từ điểm đứt — KHÔNG đổi nội dung event nào.

    Dùng cho ca đã chẩn đoán là race đa-phiên (2 mắt xích cùng `prev`), không phải tamper.
    Việc sửa TỰ LỘ: sau khi rechain, append 1 event `audit.rechain` ghi số mắt xích tính lại
    — ai đọc sổ đều thấy chuỗi từng được nối lại, không giấu được."""
    root = Path(root)
    path = _events_path(root)
    try:
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    except Exception:
        print("rechain: chưa có events.jsonl")
        return
    objs = [json.loads(ln) for ln in lines]
    first = next((i for i, o in enumerate(objs) if o.get("h")), None)
    if first is None:
        print("rechain: chuỗi chưa khởi tạo — không có gì để nối")
        return
    prev_h, fixed, from_line = "genesis", 0, None
    out = lines[:first]
    for i in range(first, len(objs)):
        body = {k: v for k, v in objs[i].items() if k != "h"}
        body["prev"] = prev_h
        h = _chain_hash(prev_h, body)
        if objs[i].get("prev") != prev_h or objs[i].get("h") != h:
            fixed += 1
            if from_line is None:
                from_line = i + 1
        body["h"] = h
        out.append(json.dumps(body, ensure_ascii=False))
        prev_h = h
    if not fixed:
        print("rechain: chuỗi đã nguyên vẹn — không sửa gì")
        return
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    record(root, "audit.rechain", actor="system", fixed=fixed, from_line=from_line,
           note="tính lại prev/h từ điểm đứt (race đa-phiên cùng prev) — nội dung event giữ nguyên")
    print(f"rechain: tính lại {fixed} mắt xích từ dòng {from_line} — nội dung event không đổi")


def audit_verify(root) -> bool:
    """Trụ 5 — Audit & Analytics. Kiểm tra toàn vẹn chuỗi tamper-evident của events.jsonl
    rồi in tóm tắt hội tụ (số sự kiện, khoảng thời gian, phân loại). Đọc RAW (không nuốt
    dòng hỏng như _read_events) để chính tamper cũng lộ ra.

    Trả True nếu chuỗi NGUYÊN VẸN / chưa khởi tạo / chưa có file (fail-open); False nếu
    chuỗi ĐỨT hoặc JSON hỏng giữa file (dùng cho `--audit --check` ở gate)."""
    root = Path(root)
    try:
        raw = _events_path(root).read_text(encoding="utf-8").splitlines()
    except Exception:
        print("audit: chưa có events.jsonl")
        return True
    lines = [ln for ln in raw if ln.strip()]
    total = len(lines)
    objs = []
    for i, ln in enumerate(lines):
        try:
            objs.append(json.loads(ln))
        except Exception:
            print(f"audit: ✗ dòng {i + 1} JSON hỏng — không verify được phần còn lại")
            return False
    first = next((i for i, o in enumerate(objs) if o.get("h")), None)
    pre = total if first is None else first
    broken = None
    if first is not None:
        prev_h = "genesis"
        for i in range(first, total):
            o = objs[i]
            if not o.get("h"):
                broken = (i + 1, "thiếu hash (dòng pre-audit chen vào giữa chuỗi)"); break
            if o.get("prev") != prev_h:
                broken = (i + 1, "đứt liên kết prev (dòng bị chèn hoặc xoá)"); break
            if _chain_hash(o.get("prev", "genesis"), {k: v for k, v in o.items() if k != "h"}) != o["h"]:
                broken = (i + 1, "hash không khớp (nội dung dòng bị sửa)"); break
            prev_h = o["h"]
    from collections import Counter
    c = Counter(o.get("event", "?") for o in objs)
    ts = [o.get("ts") for o in objs if o.get("ts")]
    span = f", {ts[0]} → {ts[-1]}" if ts else ""
    print(f"Audit & Analytics (Trụ 5) — {total} sự kiện{span}")
    print(f"  pre-audit (chưa bảo vệ chuỗi): {pre}")
    if first is None:
        print("  chuỗi tamper-evident: CHƯA khởi tạo — sẽ bắt đầu từ event tiếp theo")
    elif broken:
        print(f"  chuỗi tamper-evident: ✗ ĐỨT ở dòng {broken[0]} — {broken[1]}")
    else:
        print(f"  chuỗi tamper-evident: ✓ {total - pre} mắt xích liên tục, toàn vẹn")
    print("  theo loại sự kiện:")
    for k, n in c.most_common():
        print(f"    {n:4d}  {k}")
    print("  ⚠️ tamper-EVIDENT, không tamper-proof: bắt sửa/chèn/xoá dòng giữa file; KHÔNG chống được")
    print("     agent tự tính lại cả chuỗi, và không bắt cắt-đuôi (cần neo ngoại bộ — council: khoan làm).")
    return broken is None


def _tasks_path(root: Path) -> Path:
    p = root / "harness" / "metrics"
    p.mkdir(parents=True, exist_ok=True)
    gi = root / ".gitignore"
    try:
        if not gi.exists() or "harness/metrics/tasks.json" not in gi.read_text(encoding="utf-8", errors="ignore"):
            with open(gi, "a", encoding="utf-8") as f:
                f.write("harness/metrics/tasks.json\n")
    except Exception:
        pass
    return p / "tasks.json"


def _load_tasks(root: Path) -> dict:
    try:
        return json.loads(_tasks_path(root).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_tasks(root: Path, tasks: dict) -> None:
    _tasks_path(root).write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def task_new(root, title: str, **fields) -> str:
    """Trụ 3 — tạo task, ID bền T-YYMMDD-NN, state=proposed. State store mutable (cache),
    nhưng MỖI chuyển trạng thái ghi 1 mắt xích vào events.jsonl → audit trail bất biến (Trụ 5).
    Fail-open: lỗi I/O → trả "" (flow gọi không bao giờ vỡ)."""
    try:
        root = Path(root)
        tasks = _load_tasks(root)
        day = datetime.now().strftime("%y%m%d")
        seq = sum(1 for t in tasks if t.startswith(f"T-{day}-")) + 1
        tid = f"T-{day}-{seq:02d}"
        now = datetime.now().isoformat(timespec="seconds")
        tasks[tid] = {"id": tid, "title": title, "state": "proposed", "created": now, "updated": now,
                      "history": [{"state": "proposed", "ts": now}],
                      **{k: v for k, v in fields.items() if v is not None}}
        _save_tasks(root, tasks)
        record(root, "task.new", task=tid, title=title, state="proposed")
        return tid
    except Exception:
        return ""


def task_set(root, tid: str, state: str, note: str = "") -> bool:
    """Chuyển trạng thái — cập nhật store + ghi 1 mắt xích audit bất biến. Fail-open."""
    try:
        root = Path(root)
        tasks = _load_tasks(root)
        if tid not in tasks:
            return False
        now = datetime.now().isoformat(timespec="seconds")
        tasks[tid]["state"] = state
        tasks[tid]["updated"] = now
        h = {"state": state, "ts": now}
        if note:
            h["note"] = note
        tasks[tid].setdefault("history", []).append(h)
        _save_tasks(root, tasks)
        record(root, "task.set", task=tid, state=state, note=note or None)
        return True
    except Exception:
        return False


def task_list(root) -> None:
    tasks = _load_tasks(Path(root))
    if not tasks:
        print("tasks: chưa có task nào")
        return
    print(f"Task Tracking (Trụ 3) — {len(tasks)} task")
    for tid, t in sorted(tasks.items()):
        print(f"  {tid:>13}  {t.get('state',''):<11}  {t.get('title','')}")


def task_show(root, tid: str) -> None:
    t = _load_tasks(Path(root)).get(tid)
    if not t:
        print(f"task: không thấy {tid}")
        return
    print(f"{t['id']}  [{t['state']}]  {t.get('title','')}")
    print(f"  tạo: {t.get('created','')}  ·  đổi gần nhất: {t.get('updated','')}")
    print("  lịch sử (audit trail bất biến — chuỗi trong events.jsonl):")
    for h in t.get("history", []):
        note = f"  — {h['note']}" if h.get("note") else ""
        print(f"    {h.get('ts','')}  → {h.get('state','')}{note}")


def reconcile(root, files) -> None:
    """Trụ 5 — quy ACTOR (agent vs người/tool ngoài) tại chốt GIT. Gọi từ pre-commit hook.
    Nguyên lý: git là kênh DUY NHẤT mọi thay đổi muốn tồn tại đều phải qua. File framework
    được stage mà KHÔNG có `file.write` của agent (kể từ lần reconcile trước) → người/tool ngoài
    đã sửa (hook in-process của agent mù với bash/Cursor/vim). Ghi 1 mắt xích `commit.reconcile`
    vào chuỗi bất biến. Fail-open TUYỆT ĐỐI — logging không bao giờ chặn commit."""
    try:
        root = Path(root)
        fw = [f.replace("\\", "/").lstrip("./") for f in files if is_framework_file(f)]
        if not fw:
            return
        evs = _read_events(root)
        last = -1
        for i, e in enumerate(evs):
            if e.get("event") == "commit.reconcile":
                last = i
        agent_paths = {e.get("path") for e in evs[last + 1:]
                       if e.get("event") == "file.write" and e.get("path")}
        agent = [f for f in fw if f in agent_paths]
        human = [f for f in fw if f not in agent_paths]
        record(root, "commit.reconcile", actor="system",
               agent_n=len(agent), human_n=len(human), human=human or None)
        if human:
            print(f"[reconcile] {len(agent)} agent-logged · {len(human)} NGOÀI agent-log "
                  f"(người/tool ngoài): {', '.join(human[:6])}")
        else:
            print(f"[reconcile] {len(agent)} file framework đều agent-logged ✓")
    except Exception:
        pass


def main() -> None:
    args = sys.argv[1:]
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if "--root" in args:
        i = args.index("--root")
        root = Path(args[i + 1])
        del args[i:i + 2]
    if "--run-cost" in args:
        def _opt(name):
            for a in args:
                if a.startswith(name + "="):
                    return a.split("=", 1)[1]
            return ""
        rec = run_cost(root, _opt("--transcript"), _opt("--session"))
        print(f"run.cost: ${rec.get('cost_usd')} ({rec.get('turns')} turns)" if rec else "skip (no transcript/usage)")
    elif "--cost-summary" in args:
        cost_summary(root)
    elif "--audit" in args:
        if "--rechain" in args:
            audit_rechain(root)
        ok = audit_verify(root)
        if "--check" in args:          # chế độ gate: chuỗi đứt → exit 2 (interactive --audit vẫn exit 0)
            sys.exit(0 if ok else 2)
    elif "--reconcile" in args:
        i = args.index("--reconcile")
        reconcile(root, args[i + 1:])
    elif "--task" in args:
        try:
            i = args.index("--task")
            sub = args[i + 1] if len(args) > i + 1 else "list"
            rest = args[i + 2:]
            kv = dict(a.split("=", 1) for a in rest if "=" in a)
            pos = [a for a in rest if "=" not in a]
            if sub == "new":
                title = kv.get("title") or (" ".join(pos) if pos else "untitled")
                tid = task_new(root, title, **{k: v for k, v in kv.items() if k != "title"})
                print(f"task tạo: {tid}  [proposed]  {title}" if tid else "task: bỏ qua (fail-open)")
            elif sub == "set":
                tid = pos[0] if pos else kv.get("task", "")
                state = kv.get("state") or (pos[1] if len(pos) > 1 else "")
                print(f"task {tid} → {state}" if task_set(root, tid, state, kv.get("note", "")) else f"task: bỏ qua {tid} (fail-open)")
            elif sub == "show":
                task_show(root, pos[0] if pos else kv.get("task", ""))
            else:
                task_list(root)
        except Exception:
            print("task: bỏ qua (fail-open)")
    elif "--render-md" in args:
        ok = render_md(root)
        print("rendered log.md auto-block" if ok else "skip (no events / no log.md)")
    elif "--summary" in args:
        evs = _read_events(root)
        from collections import Counter
        c = Counter(e.get("event", "?") for e in evs)
        print(f"events.jsonl: {len(evs)} dòng")
        for k, n in c.most_common():
            print(f"  {n:4d}  {k}")
    elif "--record" in args:
        i = args.index("--record")
        ev = args[i + 1] if len(args) > i + 1 else "manual"
        fields = dict(a.split("=", 1) for a in args[i + 2:] if "=" in a)
        record(root, ev, **fields)
        print(f"recorded: {ev} {fields}")
    else:  # --tail N (default 20)
        n = 20
        if "--tail" in args:
            j = args.index("--tail")
            if len(args) > j + 1 and args[j + 1].isdigit():
                n = int(args[j + 1])
        for e in _read_events(root, n):
            print(json.dumps(e, ensure_ascii=False))


if __name__ == "__main__":
    main()
