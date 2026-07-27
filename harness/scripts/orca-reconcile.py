#!/usr/bin/env python3
"""orca-reconcile — đối soát task orchestration của Orca: việc nào chưa kết thúc, vì sao.

Vì sao tồn tại (đo 2026-07-20, T-260720-01):
  Trên 59 task orchestration: 13 (22%) từng được dispatch, **46 (78%) có `dispatch: null`
  — chưa bao giờ được giao**. Toàn bộ 14 task treo (ready/blocked) đều thuộc nhóm này,
  rải từ 2026-05-22 tới 2026-07-17. Không cổng nào đối soát, không ai dọn.

  `dispatch-verify.py` đã đóng một vòng KHÁC (lời-hứa proposal ↔ artifact trên đĩa).
  Vòng này — runtime task state — trước nay không ai đóng.

PHÂN NHÓM là điểm chính, không phải đếm:
  · chưa-từng-dispatch  → câu hỏi "VÌ SAO người điều phối không giao?"
                          (gốc: không biết lúc nào worker xong → xem orca-dispatch.py)
  · đã-giao-rồi-treo    → câu hỏi "worker chết ở đâu?"
  · failed-chưa-triage  → cần người phán
  Hai nhóm đầu đòi hai hành động hoàn toàn khác nhau; gộp lại là mất thông tin.

KỶ LUẬT: tool này CHỈ BÁO CÁO. Không gọi task-update, không reset, không xoá.
  Đóng một task là hành động có chủ ý của người — một worker chạy lâu bị đoán nhầm
  là đã chết thì việc đang chạy bị giết oan.

Fail-open: thiếu `orca` / runtime tắt / JSON lạ → coi là BÌNH THƯỜNG (exit 0, im).
  Người không dùng orchestration không bao giờ bị cổng sức khoẻ làm phiền.

CLI:
    orca-reconcile.py [--scope current|all] [--stale-days 7] [--json]
    orca-reconcile.py --stamp "<spec>"      # đóng dấu dự án trước khi task-create
    orca-reconcile.py --self-test
"""
from __future__ import annotations

import argparse
import datetime
import json
import shutil
import subprocess
import sys

DEFAULT_STALE_DAYS = 7
OPEN_STATUSES = ("ready", "blocked", "failed")

# Sổ task của Orca là RUNTIME-GLOBAL — guide của chính Orca ghi "Orchestration messages
# and tasks are runtime-global". Đo 2026-07-20: 18 terminal thuộc NHIỀU DỰ ÁN khác nhau
# cùng ghi vào MỘT sổ, nên `task-list` chạy ở repo A trả về cả việc của repo B
# (thực đo: 11/17 task treo thuộc bonbon-ai · HRIS/payroll · DMS Coteccons).
#
# Hệ quả không chỉ là báo cáo nhiễu: một orchestrator chạy ở dự án A NHÌN THẤY và
# CLAIM được task của dự án B — phá đúng mục tiêu "tách bias ở tầng vật lý" (cô lập
# được worktree và CLI, nhưng sổ việc thì dùng chung).
#
# Orca không có chỗ gắn dự án (`task-create` không có trường tag; `task-list` không có
# bộ lọc scope — đã kiểm). Nên scope ở TẦNG CỦA TA, hai nửa:
#   · GHI  — `--stamp` đóng dấu repo root vào spec lúc tạo → chính xác vĩnh viễn,
#            còn đúng cả khi terminal tạo nó đã chết (thực đo: 0/17 terminal còn sống).
#   · ĐỌC  — task cũ không có dấu thì suy đoán theo path tuyệt đối trong spec;
#            không suy được thì trả "unknown", KHÔNG đoán bừa.
PROJECT_MARK = "[orca-project:"


def stamp_spec(spec: str, root: str) -> str:
    """Đóng dấu dự án vào spec lúc TẠO task — nửa 'ghi' của cơ chế scope."""
    return f"{spec}\n{PROJECT_MARK}{root}]"


def git_root(cwd=".") -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def load_map():
    """Quy thuộc backfill do NGƯỜI xác nhận, cho task cũ không tự khai được (harness/orca-project-map.json)."""
    try:
        import pathlib as _pl
        f = _pl.Path(__file__).resolve().parents[1] / "orca-project-map.json"
        return (json.loads(f.read_text(encoding="utf-8")) or {}).get("tasks", {}) or {}
    except Exception:  # noqa: BLE001 — thiếu file là bình thường
        return {}


def attribute(spec: str, roots, task_id="", pmap=None) -> str:
    """Task này thuộc dự án nào. Thứ tự tin cậy GIẢM DẦN — không đảo:
      1. dấu `--stamp` trong spec — máy tự khai lúc tạo, chính xác nhất
      2. map người xác nhận      — backfill cho task cũ không tự khai được
      3. dò path tuyệt đối       — suy đoán
      4. 'unknown'               — không suy được thì nói không biết, KHÔNG đoán bừa
    """
    spec = spec or ""
    if PROJECT_MARK in spec:
        tail = spec.split(PROJECT_MARK, 1)[1]
        if "]" in tail:
            return tail.split("]", 1)[0].strip()
    if task_id and (pmap or {}).get(task_id):
        return pmap[task_id]
    # root DÀI NHẤT thắng để /a/b/c không bị quy nhầm về /a khi cả hai đều là repo đã biết.
    best = ""
    for r in roots:
        if r and r in spec and len(r) > len(best):
            best = r
    return best or "unknown"


def classify(task: dict, has_dispatch: bool) -> str:
    if task.get("status") == "failed":
        return "failed-chua-triage"
    return "da-giao-roi-treo" if has_dispatch else "chua-tung-dispatch"


def age_days(created_at: str, now=None) -> int:
    """Tuổi theo ngày. Chuỗi lạ → 0 (fail-open: không bịa tuổi)."""
    if not created_at:
        return 0
    now = now or datetime.datetime.now()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return max(0, (now - datetime.datetime.strptime(created_at[:19], fmt)).days)
        except ValueError:
            continue
    return 0


def _orca_json(*args, timeout=25):
    try:
        out = subprocess.run(["orca", *args], capture_output=True, text=True, timeout=timeout)
        return json.loads(out.stdout)
    except Exception:  # noqa: BLE001 — fail-open có chủ đích
        return None


def known_roots():
    """Repo root đã biết: của chính ta + của mọi terminal đang sống (để dò task cũ)."""
    roots = {git_root()}
    d = _orca_json("terminal", "list", "--json")
    for term in ((d or {}).get("result") or {}).get("terminals", []):
        if term.get("worktreePath"):
            roots.add(term["worktreePath"])
    return {r for r in roots if r}


def collect(stale_days=DEFAULT_STALE_DAYS, scope="current"):
    """Trả (available, report). available=False nghĩa là không có Orca — KHÔNG phải lỗi.

    scope='current' (mặc định) chỉ tính task thuộc repo đang đứng — vì sổ Orca là
    runtime-global, không lọc thì báo cáo lẫn việc của dự án khác (xem chú thích đầu file).
    scope='all' xem toàn sổ. Task 'unknown' LUÔN được kể riêng, không im lặng vứt.
    """
    if shutil.which("orca") is None:
        return False, {"reason": "orca không có trên PATH"}
    d = _orca_json("orchestration", "task-list", "--json")
    if not d or not d.get("ok"):
        return False, {"reason": "runtime Orca không phản hồi"}
    tasks = (d.get("result") or {}).get("tasks") or []
    me, roots, pmap = git_root(), known_roots(), load_map()
    groups: dict[str, list] = {}
    others: dict[str, int] = {}
    for t in tasks:
        if t.get("status") not in OPEN_STATUSES:
            continue
        proj = attribute(t.get("spec") or "", roots, t.get("id", ""), pmap)
        # FAIL-SAFE: chỉ loại task CHỨNG MINH ĐƯỢC là của dự án KHÁC. "unknown" thì GIỮ —
        # task cũ hay viết path tương đối nên không quy thuộc được (thực đo: 15/17 unknown),
        # vứt chúng đi sẽ báo "0 task treo" trong khi 3 task của chính repo này đang nằm đó.
        # Thà hiện một task không phải của mình còn hơn giấu một task là của mình.
        if scope == "current" and proj != me and proj != "unknown":
            others[proj] = others.get(proj, 0) + 1
            continue
        ds = _orca_json("orchestration", "dispatch-show", "--task", t.get("id", ""), "--json")
        has = bool(((ds or {}).get("result") or {}).get("dispatch"))
        groups.setdefault(classify(t, has), []).append({
            "id": t.get("id"), "status": t.get("status"), "project": proj,
            "age_days": age_days(t.get("created_at", "")),
            "spec": (t.get("spec") or "")[:90],
        })
    stale = [x for g in groups.values() for x in g if x["age_days"] >= stale_days]
    return True, {
        "scope": scope, "project": me, "excluded_other_projects": others,
        "total_tasks": len(tasks),
        "open_total": sum(len(v) for v in groups.values()),
        "groups": {k: len(v) for k, v in groups.items()},
        "stale_count": len(stale),
        "max_age_days": max([x["age_days"] for x in stale], default=0),
        "stale_days_threshold": stale_days,
        "detail": groups,
    }


def self_test() -> int:
    """Tất định, KHÔNG cần runtime — chạy được ở CI."""
    fails = []

    def ck(name, cond):
        print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
        if not cond:
            fails.append(name)

    ck("không dispatch → nhóm chua-tung-dispatch",
       classify({"status": "ready"}, False) == "chua-tung-dispatch")
    ck("có dispatch → nhóm da-giao-roi-treo",
       classify({"status": "ready"}, True) == "da-giao-roi-treo")
    ck("failed → nhóm riêng dù đã dispatch",
       classify({"status": "failed"}, True) == "failed-chua-triage")
    now = datetime.datetime(2026, 7, 20)
    ck("tuổi tính đúng theo ngày", age_days("2026-07-13 00:00:00", now) == 7)
    ck("tuổi làm tròn XUỐNG, không thổi phồng", age_days("2026-07-13 10:00:00", now) == 6)
    ck("ts lạ → 0, không bịa tuổi", age_days("rác", now) == 0)
    ck("ts rỗng → 0", age_days("", now) == 0)
    # Needle ghép lúc chạy: nếu viết thẳng literal thì CHÍNH dòng check này chứa chuỗi
    # cần tìm và test tự-fail vĩnh viễn (bug đã dính lần đầu, giữ lại làm ghi nhớ).
    src = open(__file__, encoding="utf-8").read()
    calls = [ln for ln in src.splitlines() if "_orca_json(" in ln and "def " not in ln]
    # Deny-list thay allowlist: allowlist phải nới tay mỗi lần thêm một verb chỉ-đọc mới
    # (đã dính: thêm `terminal list` là test đỏ oan). Deny-list chỉ đỏ khi thật sự nguy hiểm.
    banned = ["task-" + "update", "task-" + "create", "re" + "set",
              "terminal\", \"create", "terminal\", \"close", "terminal\", \"send"]
    ck("KHÔNG lời gọi orca nào đổi state (tool chỉ báo cáo)",
       all(b not in ln for ln in calls for b in banned))
    R = ["/a/repo", "/a/repo/sub", "/other"]
    ck("dấu đóng sẵn thắng mọi suy đoán",
       attribute("việc gì đó\n[orca-project:/a/repo]", R) == "/a/repo")
    ck("task cũ không dấu → dò path trong spec",
       attribute("sửa file /other/x.ts", R) == "/other")
    ck("root DÀI NHẤT thắng (không quy nhầm repo con về repo cha)",
       attribute("đọc /a/repo/sub/f.py", R) == "/a/repo/sub")
    ck("không suy được → 'unknown', KHÔNG đoán bừa",
       attribute("việc chung chung không path", R) == "unknown")
    ck("stamp rồi attribute lại ra đúng root (khứ hồi)",
       attribute(stamp_spec("abc", "/a/repo"), R) == "/a/repo")
    ck("spec rỗng → unknown, không nổ", attribute("", R) == "unknown")
    ck("map người-xác-nhận quy thuộc được task cũ",
       attribute("không path gì", R, "task_x", {"task_x": "external:HRIS"}) == "external:HRIS")
    ck("dấu --stamp THẮNG map (máy tự khai tin hơn ghi tay)",
       attribute(stamp_spec("v", "/a/repo"), R, "task_x", {"task_x": "/sai"}) == "/a/repo")
    ck("scope current KHÔNG được vứt 'unknown' (fail-safe: giấu việc của mình còn tệ hơn)",
       "proj != \"unknown\"" in open(__file__, encoding="utf-8").read())

    avail, rep = collect()
    ck("thiếu orca/runtime → available=False, KHÔNG raise",
       isinstance(rep, dict) and isinstance(avail, bool))

    print(f"\nSELF-TEST: {'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="đối soát task orchestration Orca (chỉ báo cáo)")
    ap.add_argument("--scope", choices=("current", "all"), default="current",
                    help="current = chỉ dự án đang đứng (mặc định; sổ Orca là runtime-global)")
    ap.add_argument("--stamp", metavar="SPEC",
                    help="in ra spec đã đóng dấu dự án — dùng trước orca orchestration task-create")
    ap.add_argument("--stale-days", type=int, default=DEFAULT_STALE_DAYS)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())
    if a.stamp:
        print(stamp_spec(a.stamp, git_root()))
        sys.exit(0)

    avail, rep = collect(a.stale_days, a.scope)
    if a.json:
        print(json.dumps({"available": avail, **rep}, ensure_ascii=False, indent=1))
        sys.exit(0)
    if not avail:
        print(f"· orchestration: bỏ qua — {rep.get('reason')}")
        sys.exit(0)
    ex = rep.get("excluded_other_projects") or {}
    extra = (f"  ({sum(ex.values())} task của dự án khác đã loại — sổ Orca là runtime-global; "
             f"xem toàn bộ: --scope all)") if ex else ""
    if not rep["open_total"]:
        print(f"✓ orchestration: 0 task treo của dự án này / {rep['total_tasks']} task toàn sổ.{extra}")
        sys.exit(0)
    print(f"⚠ orchestration [{rep['scope']}]: {rep['open_total']} task chưa kết thúc "
          f"/ {rep['total_tasks']} toàn sổ (cũ nhất {rep['max_age_days']} ngày){extra}")
    for g, n in sorted(rep["groups"].items(), key=lambda kv: -kv[1]):
        print(f"   · {g}: {n}")
        for x in sorted(rep["detail"][g], key=lambda x: -x["age_days"])[:5]:
            print(f"       {x['id']}  {x['age_days']}d  {x['spec'][:60]}")
    print("   → đây là BÁO CÁO; đóng task là hành động có chủ ý (orca orchestration task-update)")
    sys.exit(0)


if __name__ == "__main__":
    main()
