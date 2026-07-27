#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""skill-usage — ĐO TẦN SUẤT skill từ transcript phiên Claude Code (GH#8).

Nguồn dữ liệu ĐÃ CÓ, không thêm hạ tầng thu thập: transcript
`~/.claude/projects/-Users-giatran-orca-setup-setup/*.jsonl` chứa mọi lời gọi
Skill-tool (name="Skill", input.skill). Đây chính là nguồn caveman-stats/orca-eval.

Chỉ ĐỌC LOCAL, chỉ project repo này (privacy), không side-effect mạng.
Chỉ đo TẦN SUẤT — KHÔNG đo chất lượng (đó là việc của trace-grader/orca-eval).

CLI:
  skill-usage.py --weekly              # bảng tuần hiện tại + skill chết + sinh HTML
  skill-usage.py --week 2026-W27       # chốt 1 tuần ISO cụ thể
  skill-usage.py --top 20              # đổi top-N (mặc định 15)
  skill-usage.py --dead-weeks 4        # skill "chết" = idle >= N tuần (mặc định 4)
  skill-usage.py --json                # in JSON thô, không render
  skill-usage.py --no-html             # chỉ in bảng, không ghi file
  skill-usage.py --transcripts DIR     # override thư mục transcript

Deterministic: cùng tập transcript → cùng số liệu (sort ổn định theo count, tên).
"""
import argparse
import collections
import datetime as dt
import glob
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML_DIR = ROOT / "llmwiki" / "html"
PROJECTS_DIR = Path.home() / ".claude" / "projects"
# Fallback khi không suy được worktree (git vắng): dir transcript của repo chính.
FALLBACK_TRANSCRIPTS = PROJECTS_DIR / "-Users-giatran-orca-setup-setup"


def encode_project_dir(path: Path) -> str:
    """Claude Code mã hoá cwd → tên thư mục transcript: mọi '/' và '.' thành '-'."""
    s = str(path.resolve())
    return "".join("-" if c in "/." else c for c in s)


def discover_transcript_dirs(root: Path):
    """Suy MỌI dir transcript thuộc CHÍNH repo này (privacy: chỉ repo này).

    Mỗi worktree phiên chạy ghi transcript vào dir riêng theo cwd-mã-hoá → chỉ đọc
    1 dir = bỏ sót phần lớn usage. `git worktree list` cho mọi cwo hợp lệ của repo.
    """
    dirs = []
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "worktree", "list", "--porcelain"],
            capture_output=True, text=True, timeout=15,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        out = ""
    for line in out.splitlines():
        if line.startswith("worktree "):
            d = PROJECTS_DIR / encode_project_dir(Path(line[len("worktree "):]))
            if d.is_dir() and d not in dirs:
                dirs.append(d)
    if FALLBACK_TRANSCRIPTS.is_dir() and FALLBACK_TRANSCRIPTS not in dirs:
        dirs.append(FALLBACK_TRANSCRIPTS)
    return dirs


def iso_week(ts: dt.datetime) -> str:
    y, w, _ = ts.isocalendar()
    return f"{y:04d}-W{w:02d}"


def parse_ts(s):
    if not s:
        return None
    try:
        # Transcript ghi UTC (…Z). Quy về giờ ĐỊA PHƯƠNG trước khi gom ISO-week —
        # nếu không, call khuya giờ VN (UTC+7) bị gán nhầm sang tuần trước.
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def collect(transcript_dirs):
    """Trả list event {skill, ts(datetime), week, session} từ mọi .jsonl trong mọi dir."""
    events = []
    files = sorted(f for d in transcript_dirs for f in glob.glob(str(d / "*.jsonl")))
    for f in files:
        try:
            fh = open(f, encoding="utf-8")
        except OSError:
            continue
        with fh:
            for line in fh:
                line = line.strip()
                if not line or '"Skill"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = o.get("message")
                content = msg.get("content") if isinstance(msg, dict) else None
                if not isinstance(content, list):
                    continue
                ts = parse_ts(o.get("timestamp"))
                if ts is None:
                    continue
                session = o.get("sessionId") or Path(f).stem
                for b in content:
                    if (
                        isinstance(b, dict)
                        and b.get("type") == "tool_use"
                        and b.get("name") == "Skill"
                    ):
                        skill = (b.get("input") or {}).get("skill")
                        if skill:
                            events.append(
                                {"skill": skill, "ts": ts, "week": iso_week(ts), "session": session}
                            )
    return events


def aggregate(events):
    """Gom theo skill: count, last_used, số session chạm, count-per-week."""
    per_skill = collections.defaultdict(
        lambda: {"count": 0, "last_used": None, "sessions": set(), "weeks": collections.Counter()}
    )
    weeks_seen = set()
    for e in events:
        s = per_skill[e["skill"]]
        s["count"] += 1
        s["sessions"].add(e["session"])
        s["weeks"][e["week"]] += 1
        if s["last_used"] is None or e["ts"] > s["last_used"]:
            s["last_used"] = e["ts"]
        weeks_seen.add(e["week"])
    return per_skill, sorted(weeks_seen)


def prev_week(week: str) -> str:
    y, w = int(week[:4]), int(week[6:])
    monday = dt.date.fromisocalendar(y, w, 1) - dt.timedelta(days=7)
    yy, ww, _ = monday.isocalendar()
    return f"{yy:04d}-W{ww:02d}"


def build_report(events, target_week, top_n, dead_weeks):
    per_skill, all_weeks = aggregate(events)
    prev = prev_week(target_week)

    # Xếp hạng TỔNG (mọi thời gian) — deterministic: -count, rồi tên.
    ranking = []
    for name, s in per_skill.items():
        ranking.append(
            {
                "skill": name,
                "count": s["count"],
                "sessions": len(s["sessions"]),
                "last_used": s["last_used"].date().isoformat() if s["last_used"] else None,
                "this_week": s["weeks"].get(target_week, 0),
                "prev_week": s["weeks"].get(prev, 0),
            }
        )
    ranking.sort(key=lambda r: (-r["count"], r["skill"]))

    # Skill "chết": đã từng thấy nhưng idle >= dead_weeks tuần so với tuần đích.
    ty, tw = int(target_week[:4]), int(target_week[6:])
    target_monday = dt.date.fromisocalendar(ty, tw, 1)
    dead = []
    for r in ranking:
        if not r["last_used"]:
            continue
        last = dt.date.fromisoformat(r["last_used"])
        idle_days = (target_monday - last).days
        if idle_days >= dead_weeks * 7:
            dead.append({**r, "idle_weeks": idle_days // 7})
    dead.sort(key=lambda r: (-r["idle_weeks"], r["skill"]))

    # Tổng phiên trong tuần đích/tuần trước.
    def sessions_in(week):
        return len({e["session"] for e in events if e["week"] == week})

    return {
        "target_week": target_week,
        "prev_week": prev,
        "generated_from": len({e["session"] for e in events}),
        "total_calls": len(events),
        "distinct_skills": len(per_skill),
        "sessions_this_week": sessions_in(target_week),
        "sessions_prev_week": sessions_in(prev),
        "calls_this_week": sum(1 for e in events if e["week"] == target_week),
        "calls_prev_week": sum(1 for e in events if e["week"] == prev),
        "ranking": ranking[:top_n],
        "full_ranking": ranking,
        "dead": dead,
        "all_weeks": all_weeks,
    }


# ---------------------------------------------------------------- console ----
def print_report(rep):
    tw = rep["target_week"]
    print(f"\n📊 Skill-usage · tuần {tw} (so tuần trước {rep['prev_week']})")
    print(f"   {rep['total_calls']} lời gọi · {rep['distinct_skills']} skill · "
          f"{rep['generated_from']} phiên (toàn bộ transcript)")
    d = rep["calls_this_week"] - rep["calls_prev_week"]
    print(f"   tuần này: {rep['calls_this_week']} gọi / {rep['sessions_this_week']} phiên "
          f"({'+' if d >= 0 else ''}{d} vs tuần trước)\n")

    print(f"  {'skill':28} {'tổng':>5} {'phiên':>6} {'tuần':>5} {'Δtuần':>6}  lần cuối")
    print("  " + "-" * 68)
    for r in rep["ranking"]:
        delta = r["this_week"] - r["prev_week"]
        print(f"  {r['skill'][:28]:28} {r['count']:>5} {r['sessions']:>6} "
              f"{r['this_week']:>5} {('+' if delta >= 0 else '')+str(delta):>6}  {r['last_used']}")

    if rep["dead"]:
        print(f"\n  💀 Skill chết (idle ≥ tuần):")
        for r in rep["dead"]:
            print(f"     {r['skill'][:32]:32} idle {r['idle_weeks']}w · "
                  f"{r['count']} lần · cuối {r['last_used']}")
    else:
        print("\n  💀 Không có skill chết theo ngưỡng hiện tại.")
    print()


# ------------------------------------------------------------------- html ----
def render_html(rep) -> str:
    e = html.escape
    tw = rep["target_week"]
    max_count = max((r["count"] for r in rep["ranking"]), default=1) or 1

    def delta_badge(d):
        if d > 0:
            return f'<span class="up">▲ {d}</span>'
        if d < 0:
            return f'<span class="down">▼ {abs(d)}</span>'
        return '<span class="flat">–</span>'

    rows = []
    for i, r in enumerate(rep["ranking"], 1):
        w = round(r["count"] / max_count * 100)
        rows.append(f"""      <tr>
        <td class="rank">{i}</td>
        <td class="skill"><span class="bar" style="width:{w}%"></span><span class="name">{e(r['skill'])}</span></td>
        <td class="num">{r['count']}</td>
        <td class="num">{r['sessions']}</td>
        <td class="num">{r['this_week']}</td>
        <td class="num">{delta_badge(r['this_week'] - r['prev_week'])}</td>
        <td class="date">{e(r['last_used'] or '—')}</td>
      </tr>""")

    if rep["dead"]:
        dead_rows = "".join(
            f"""      <tr><td class="skill"><span class="name">{e(r['skill'])}</span></td>
        <td class="num">{r['idle_weeks']}w</td><td class="num">{r['count']}</td>
        <td class="date">{e(r['last_used'] or '—')}</td></tr>""" for r in rep["dead"]
        )
        dead_block = f"""    <table class="grid dead">
      <thead><tr><th>skill chết</th><th>idle</th><th>tổng dùng</th><th>lần cuối</th></tr></thead>
      <tbody>
{dead_rows}
      </tbody>
    </table>"""
    else:
        dead_block = '<p class="empty">Không có skill chết theo ngưỡng hiện tại. 🌿</p>'

    dc = rep["calls_this_week"] - rep["calls_prev_week"]
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Skill-usage · {e(tw)}</title>
<style>
  :root {{
    --bg:#0b1220; --panel:rgba(255,255,255,.06); --edge:rgba(255,255,255,.12);
    --ink:#e8eefc; --muted:#8aa0c8; --accent:#6ea8ff; --up:#4ade80; --down:#f87171;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; padding:2.5rem 1.2rem; background:
      radial-gradient(1200px 600px at 20% -10%, #16305e 0%, transparent 60%), var(--bg);
    color:var(--ink); font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  }}
  .wrap {{ max-width:900px; margin:0 auto; }}
  h1 {{ font-size:1.5rem; margin:0 0 .2rem; letter-spacing:-.01em; }}
  .sub {{ color:var(--muted); margin:0 0 1.6rem; font-size:.92rem; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:.8rem; margin-bottom:1.6rem; }}
  .card {{ background:var(--panel); border:1px solid var(--edge); border-radius:14px; padding:1rem 1.1rem; backdrop-filter:blur(12px); }}
  .card .k {{ color:var(--muted); font-size:.78rem; text-transform:uppercase; letter-spacing:.05em; }}
  .card .v {{ font-size:1.7rem; font-weight:650; margin-top:.25rem; }}
  h2 {{ font-size:1.05rem; margin:1.8rem 0 .7rem; }}
  table {{ width:100%; border-collapse:collapse; background:var(--panel);
    border:1px solid var(--edge); border-radius:14px; overflow:hidden; }}
  th,td {{ padding:.55rem .7rem; text-align:left; border-bottom:1px solid rgba(255,255,255,.06); }}
  th {{ color:var(--muted); font-size:.74rem; text-transform:uppercase; letter-spacing:.04em; font-weight:600; }}
  tr:last-child td {{ border-bottom:none; }}
  td.rank {{ color:var(--muted); width:2rem; }}
  td.num,td.date {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  td.date {{ color:var(--muted); font-size:.85rem; }}
  td.skill {{ position:relative; min-width:200px; }}
  .bar {{ position:absolute; left:0; top:50%; transform:translateY(-50%); height:70%;
    background:linear-gradient(90deg,rgba(110,168,255,.35),rgba(110,168,255,.08));
    border-radius:6px; z-index:0; }}
  .name {{ position:relative; z-index:1; font-weight:550; }}
  .up {{ color:var(--up); }} .down {{ color:var(--down); }} .flat {{ color:var(--muted); }}
  .dead .name {{ color:#f8b4b4; }}
  .empty {{ color:var(--muted); background:var(--panel); border:1px solid var(--edge);
    border-radius:14px; padding:1rem; }}
  footer {{ color:var(--muted); font-size:.78rem; margin-top:2rem; text-align:center; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Skill-usage · tuần {e(tw)}</h1>
  <p class="sub">So với tuần trước {e(rep['prev_week'])} · nguồn: {rep['generated_from']} phiên transcript ·
     chỉ đo tần suất (không đo chất lượng) · GH#8</p>

  <div class="cards">
    <div class="card"><div class="k">Lời gọi / tuần</div><div class="v">{rep['calls_this_week']}
      <small style="font-size:.8rem;color:var(--muted)">({'+' if dc>=0 else ''}{dc})</small></div></div>
    <div class="card"><div class="k">Phiên / tuần</div><div class="v">{rep['sessions_this_week']}</div></div>
    <div class="card"><div class="k">Skill distinct</div><div class="v">{rep['distinct_skills']}</div></div>
    <div class="card"><div class="k">Skill chết</div><div class="v">{len(rep['dead'])}</div></div>
  </div>

  <h2>Top skill dùng nhiều nhất</h2>
  <table class="grid">
    <thead><tr><th>#</th><th>skill</th><th>tổng</th><th>phiên</th><th>tuần này</th><th>Δ tuần</th><th>lần cuối</th></tr></thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>

  <h2>Skill chết (idle lâu → cân nhắc gộp/bỏ)</h2>
{dead_block}

  <footer>Sinh bởi fdk/tools/skill-usage.py · deterministic · đọc local, không telemetry ra ngoài</footer>
</div>
</body>
</html>
"""


def self_test() -> int:
    """Tất định: fixture 1 dòng transcript Skill-call → collect/aggregate phải đếm đúng."""
    import json as _json
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        line = {"type": "assistant", "timestamp": "2026-07-14T10:00:00.000Z",
                "sessionId": "st-1", "message": {"content": [
                    {"type": "tool_use", "name": "Skill", "input": {"skill": "qc-code"}}]}}
        (td / "s1.jsonl").write_text(_json.dumps(line) + "\n", encoding="utf-8")
        events = collect([td])
        ok = len(events) == 1 and events[0]["skill"] == "qc-code" and iso_week(parse_ts(line["timestamp"])) == "2026-W29"
    print("skill-usage self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Đo tần suất skill từ transcript (GH#8)")
    ap.add_argument("--weekly", action="store_true", help="chốt tuần + sinh HTML")
    ap.add_argument("--week", help="tuần ISO YYYY-Www (mặc định: tuần mới nhất có dữ liệu)")
    ap.add_argument("--top", type=int, default=15, help="top-N skill (mặc định 15)")
    ap.add_argument("--dead-weeks", type=int, default=4, help="skill chết = idle >= N tuần")
    ap.add_argument("--transcripts", type=Path, action="append",
                    help="ép 1 dir transcript cụ thể (lặp lại cho nhiều dir); "
                         "mặc định: TỰ suy mọi worktree của repo qua git")
    ap.add_argument("--json", action="store_true", help="in JSON thô")
    ap.add_argument("--no-html", action="store_true", help="không ghi file HTML")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())

    dirs = args.transcripts or discover_transcript_dirs(ROOT)
    dirs = [d for d in dirs if d.is_dir()]
    if not dirs:
        print("⚠️  Không thấy thư mục transcript nào (repo chưa có phiên?).", file=sys.stderr)
        return 2

    events = collect(dirs)
    if not events:
        print("⚠️  Không tìm thấy lời gọi Skill nào trong transcript.", file=sys.stderr)
        return 1
    print(f"· nguồn: {len(dirs)} dir transcript (worktree) · {len(events)} lời gọi Skill",
          file=sys.stderr)

    _, all_weeks = aggregate(events)
    target = args.week or all_weeks[-1]

    rep = build_report(events, target, args.top, args.dead_weeks)

    if args.json:
        print(json.dumps({k: v for k, v in rep.items() if k != "full_ranking"},
                         ensure_ascii=False, indent=2))
        return 0

    print_report(rep)

    if not args.no_html:
        HTML_DIR.mkdir(parents=True, exist_ok=True)
        out = HTML_DIR / f"weekly-{target}.html"
        out.write_text(render_html(rep), encoding="utf-8")
        print(f"✅ Dashboard: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
