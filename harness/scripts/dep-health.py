#!/usr/bin/env python3
"""dep-health — dependency NGOÀI còn dùng được không. Tất định, 0 token, fail-open.

Vì sao tồn tại (bài học đắt, 2026-07-20):
  Hook orientation quảng cáo code-graph ở MỌI phiên dựa trên đúng một câu hỏi:

      has_cg = (root / ".graph-agent" / "index.db").is_file()

  Tức là **"file có tồn tại không"**. Nhưng file tồn tại KHÔNG có nghĩa tool dùng được:
  DB 0 byte, DB thiếu schema, server chết, server chạy code cũ — tất cả đều lọt qua
  câu hỏi đó. Thực tế: code-graph hỏng nhiều tuần (một DB thiếu bảng `symbols` giết cả
  fan-out) mà framework vẫn lùa mọi phiên vào nó; agent gọi, ăn lỗi, rồi mới quay về
  grep — trả phí cả hai đường. Đo được: nhánh code-graph tốn 37 tool-call so với 14.

  Nguyên tắc rút ra, áp cho MỌI dependency ngoài:
      quảng cáo một năng lực = phải THĂM DÒ nó, không phải kiểm sự tồn tại của nó.

BẮT ĐƯỢC: thiếu hẳn · DB hỏng/thiếu schema · tiến trình server chết · CLI vắng PATH ·
  runtime câm · **server chạy CODE CŨ** · **orphan tích luỹ**.

  Hai cái sau là bản vá cho chính lỗi của bản đầu: bản đầu chỉ hỏi "CÓ tiến trình nào
  không" — tức mắc lại đúng lớp lỗi nó đi sửa, chỉ nhẹ hơn — rồi tự khai "không bắt được
  server code cũ" như một giới hạn kiến trúc. Hoá ra KHÔNG phải giới hạn: so thời điểm
  khởi động tiến trình (`ps -o lstart`) với commit cuối của repo server (`git log -1`)
  là đủ, chẳng cần nói giao thức MCP. Bài học: "giới hạn kiến trúc" thường là chỗ mình
  chưa hỏi đủ năm lần.

  Đo thật 2026-07-20 khi viết dòng này: 10 tiến trình server cùng sống (cũ nhất 4 ngày),
  mỗi phiên spawn một và không ai dọn; hai con lâu đời giữ 1207 fd tới cùng vài file DB —
  dấu vết của một rò rỉ connection ở indexer (đã vá riêng ở repo server).

VẪN KHÔNG BẮT ĐƯỢC: server sống + code mới nhưng trả kết quả SAI về mặt logic. Muốn bắt
  thì phải chạy một truy vấn thật rồi assert kết quả — đó là việc của eval, không phải
  của probe sức khoẻ.

CLI:
    dep-health.py [--json]        # bảng người đọc / JSON cho máy
    dep-health.py --quiet-ok      # chỉ in khi CÓ vấn đề (dùng ở hook)
    dep-health.py --reap-orphans  # kill server orphan, GIỮ tiến trình mới nhất
    dep-health.py --self-test
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

OK, DEGRADED, ABSENT = "ok", "degraded", "absent"


def db_has_schema(db_path: Path) -> bool:
    """DB sqlite này query được không — mở được VÀ có bảng thật.

    Đây là câu hỏi mà `.is_file()` không trả lời được, và chính chỗ hụt đó đã để
    code-graph hỏng lọt lưới nhiều tuần.

    WAL + mode=ro: KHÔNG dùng được. SQLite ở chế độ WAL cần file `-shm`; khi không server
    nào đang mở DB thì `-shm` biến mất, và `mode=ro` KHÔNG tạo được nó → "unable to open
    database file" trên một DB hoàn toàn LÀNH. Đo 2026-07-20: cùng file, mode=ro lỗi còn
    read-write đọc ra 4 bảng / 22.276 symbol. Đây cũng là lời giải cho lần đo đầu báo
    "11 DB hỏng" (tôi đã đổ oan cho ổ ngoài chưa mount). File đã được kiểm tồn tại trước
    khi tới đây nên connect thường KHÔNG có rủi ro tạo DB rỗng.
    """
    try:
        conn = sqlite3.connect(str(db_path))   # KHÔNG mode=ro — xem ghi chú WAL ở trên
        try:
            names = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            conn.close()
        return {"symbols", "files"} <= names
    except sqlite3.Error:
        return False


def _procs(needle: str) -> list:
    """PID của mọi tiến trình khớp needle."""
    try:
        out = subprocess.run(["pgrep", "-f", needle], capture_output=True, text=True, timeout=5)
        return [l.strip() for l in out.stdout.splitlines() if l.strip()] if out.returncode == 0 else []
    except Exception:  # noqa: BLE001
        return []


def _ppid(pid: str):
    try:
        out = subprocess.run(["ps", "-o", "ppid=", "-p", pid],
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def is_orphan(pid: str) -> bool:
    """Tiến trình này CÓ THẬT là orphan không — tức CHA ĐÃ CHẾT.

    Định nghĩa này được viết lại sau một lần làm hỏng thật (2026-07-20): bản đầu coi
    "orphan = không phải tiến trình mới nhất" rồi kill 9 con, giữ cái mới nhất. Sai —
    cái mới nhất thuộc một phiên Claude Code KHÁC đang mở, còn server của phiên đang
    chạy lệnh thì nằm trong nhóm bị giết. Kết quả: tự cắt MCP của mình, và nhiều khả
    năng cắt luôn của các phiên khác.

    "Mới nhất" không bao giờ suy ra "của tôi". Con trỏ đúng là quan hệ CHA: tiến trình
    còn cha sống là của MỘT phiên nào đó — không được đụng. Chỉ tiến trình đã bị
    reparent (PPID 1 trên macOS/Linux) mới thật sự mồ côi.
    """
    pp = _ppid(pid)
    return pp in ("1", "0") if pp else False


def _proc_started_at(pid: str):
    """Epoch giây lúc tiến trình khởi động (None nếu không đọc được)."""
    try:
        out = subprocess.run(["ps", "-o", "lstart=", "-p", pid],
                             capture_output=True, text=True, timeout=5)
        s = out.stdout.strip()
        if not s:
            return None
        import time as _t
        return _t.mktime(_t.strptime(s, "%a %b %d %H:%M:%S %Y"))
    except Exception:  # noqa: BLE001
        return None


def _repo_last_commit_epoch(repo: Path):
    try:
        out = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%ct"],
                             capture_output=True, text=True, timeout=10)
        return float(out.stdout.strip()) if out.stdout.strip() else None
    except Exception:  # noqa: BLE001
        return None


def _server_repo_from_config():
    """Đường dẫn repo của MCP server code-graph, đọc từ ~/.claude.json (best-effort)."""
    try:
        cfg = json.loads((Path.home() / ".claude.json").read_text(encoding="utf-8"))
        args = ((cfg.get("mcpServers") or {}).get("code-graph") or {}).get("args") or []
        for a in args:
            if a.endswith("server.py"):
                return Path(a).resolve().parent
    except Exception:  # noqa: BLE001
        pass
    return None


def probe_code_graph(root: Path) -> dict:
    dbs = [p for p in [root / ".graph-agent" / "index.db"] if p.is_file()]
    if not dbs:
        try:
            dbs = [d / ".graph-agent" / "index.db" for d in root.iterdir()
                   if d.is_dir() and (d / ".graph-agent" / "index.db").is_file()]
        except OSError:
            dbs = []
    if not dbs:
        return {"name": "code-graph", "status": ABSENT,
                "reason": "không có .graph-agent/index.db nào trong project"}
    usable = [p for p in dbs if db_has_schema(p)]
    if not usable:
        return {"name": "code-graph", "status": DEGRADED,
                "reason": f"{len(dbs)} index.db có mặt nhưng KHÔNG cái nào có schema "
                          f"(0 byte hoặc index chưa chạy xong)",
                "fix": "chạy lại reindex cho repo, hoặc xoá .graph-agent/index.db rỗng"}
    pids = _procs("graph/server.py")
    if not pids:
        return {"name": "code-graph", "status": DEGRADED, "dbs_usable": len(usable),
                "reason": "DB lành nhưng KHÔNG thấy tiến trình server đang chạy",
                "fix": "khởi động lại Claude Code để MCP server lên lại"}

    # Bản đầu chỉ hỏi "CÓ tiến trình nào không" → tôi mắc lại đúng lớp lỗi đang đi sửa.
    # Câu đúng là "tiến trình MỚI NHẤT có mới hơn code không". Đo được từ ngoài: so
    # thời điểm khởi động với commit cuối của repo server. Đây chính là ca "server chạy
    # code CŨ" mà bản trước tự khai là không bắt được — hoá ra bắt được.
    starts = [s for s in (_proc_started_at(p) for p in pids) if s]
    newest = max(starts) if starts else None
    repo = _server_repo_from_config()
    commit = _repo_last_commit_epoch(repo) if repo else None
    res = {"name": "code-graph", "status": OK, "dbs_usable": len(usable),
           "server_procs": len(pids)}
    if newest and commit and commit > newest:
        return {**res, "status": DEGRADED,
                "reason": (f"server đang chạy CODE CŨ — tiến trình mới nhất khởi động trước "
                           f"commit cuối của repo server {int((commit - newest) / 60)} phút"),
                "fix": "khởi động lại Claude Code để nạp code mới"}
    # Orphan: mỗi phiên spawn một server, không ai dọn. Không sập ngay (idle ~15MB) nhưng
    # tích luỹ, và trước khi vá rò rỉ thì mỗi con còn gom fd theo số lượt reindex.
    if len(pids) > 2:
        return {**res, "status": DEGRADED,
                "reason": f"{len(pids)} tiến trình server cùng sống — orphan tích luỹ qua các phiên",
                "fix": "dep-health.py --reap-orphans (giữ tiến trình mới nhất, kill phần còn lại)"}
    return res


def probe_orca(root: Path) -> dict:
    if shutil.which("orca") is None:
        return {"name": "orca", "status": ABSENT, "reason": "orca không có trên PATH"}
    try:
        out = subprocess.run(["orca", "status", "--json"], capture_output=True,
                             text=True, timeout=20)
        d = json.loads(out.stdout)
        rt = ((d.get("result") or {}).get("runtime") or {})
        if rt.get("reachable") and rt.get("state") == "ready":
            return {"name": "orca", "status": OK, "runtime": rt.get("state")}
        return {"name": "orca", "status": DEGRADED,
                "reason": f"runtime state={rt.get('state')!r} reachable={rt.get('reachable')}",
                "fix": "mở app Orca, hoặc `orca open`"}
    except Exception as e:  # noqa: BLE001
        return {"name": "orca", "status": DEGRADED, "reason": f"orca status lỗi: {str(e)[:60]}"}


def collect(root: Path) -> list:
    return [probe_code_graph(root), probe_orca(root)]


def self_test() -> int:
    """Tất định, KHÔNG cần dependency nào — chạy được ở CI."""
    import tempfile
    fails = []

    def ck(name, cond):
        print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        empty = tmp / "empty.db"
        empty.touch()
        ck("DB 0 byte → KHÔNG có schema (đúng ca đã để lọt lưới)", not db_has_schema(empty))
        ck("file không tồn tại → không có schema", not db_has_schema(tmp / "khong-co.db"))

        good = tmp / "good.db"
        c = sqlite3.connect(good)
        c.executescript("CREATE TABLE symbols(a); CREATE TABLE files(b);")
        c.close()
        ck("DB có đủ bảng symbols+files → usable", db_has_schema(good))

        half = tmp / "half.db"
        c = sqlite3.connect(half)
        c.executescript("CREATE TABLE symbols(a);")  # thiếu files
        c.close()
        ck("DB THIẾU một bảng → vẫn coi là hỏng (không nửa vời)", not db_has_schema(half))

        r = probe_code_graph(tmp)
        ck("project không có index.db → absent, không phải degraded", r["status"] == ABSENT)

        (tmp / "sub" / ".graph-agent").mkdir(parents=True)
        (tmp / "sub" / ".graph-agent" / "index.db").touch()
        r = probe_code_graph(tmp)
        ck("có index.db nhưng rỗng → DEGRADED (KHÔNG được quảng cáo)", r["status"] == DEGRADED)

        ck("mọi probe luôn trả dict có 'status'",
           all(isinstance(p, dict) and "status" in p for p in collect(tmp)))
        ck("tiến trình không tồn tại → danh sách rỗng", _procs("khong-co-tien-trinh-nao-ten-nay") == [])
        ck("PID rác → không đọc được thời điểm khởi động", _proc_started_at("999999999") is None)
        ck("repo không phải git → không có commit epoch", _repo_last_commit_epoch(tmp) is None)
        ck("PID rác → không phán bừa là orphan", is_orphan("999999999") is False)
        # Ca có nghĩa: tiến trình ĐANG CHẠY test này chắc chắn còn cha sống (shell/claude),
        # nên không được coi là orphan. Đây đúng là bất biến đã bị vi phạm khi tôi kill nhầm.
        import os as _os2
        ck("tiến trình còn CHA SỐNG → KHÔNG phải orphan (bất biến đã bị vi phạm)",
           is_orphan(str(_os2.getpid())) is False)

    print(f"\nSELF-TEST: {'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="dependency ngoài còn dùng được không")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet-ok", action="store_true", help="chỉ in khi có vấn đề")
    ap.add_argument("--reap-orphans", action="store_true",
                    help="kill tiến trình server orphan, GIỮ cái mới nhất (hành động có chủ ý)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if a.reap_orphans:
        import os as _os
        pids = _procs("graph/server.py")
        ages = [(p, _proc_started_at(p) or 0) for p in pids]
        if len(ages) < 2:
            print(f"· {len(ages)} tiến trình server — không có orphan để dọn.")
            sys.exit(0)
        orphans = [pid for pid, _ in ages if is_orphan(pid)]
        alive_parent = [pid for pid, _ in ages if pid not in orphans]
        if not orphans:
            print(f"· {len(ages)} tiến trình server, TẤT CẢ đều còn cha sống "
                  f"(thuộc các phiên đang mở) — không có orphan thật để dọn.")
            sys.exit(0)
        killed = 0
        for pid in orphans:
            try:
                _os.kill(int(pid), 15)
                killed += 1
                print(f"  ✓ kill {pid} (cha đã chết)")
            except Exception as e:  # noqa: BLE001
                print(f"  ✗ {pid}: {e}")
        print(f"dọn {killed} orphan THẬT · giữ nguyên {len(alive_parent)} tiến trình còn cha sống")
        sys.exit(0)
    try:
        deps = collect(Path(a.root).resolve())
    except Exception:  # noqa: BLE001 — fail-open tuyệt đối
        sys.exit(0)
    if a.json:
        print(json.dumps({"deps": deps}, ensure_ascii=False, indent=1))
        sys.exit(0)
    bad = [d for d in deps if d["status"] == DEGRADED]
    if a.quiet_ok and not bad:
        sys.exit(0)
    for d in deps:
        icon = {"ok": "✓", "degraded": "⚠", "absent": "·"}[d["status"]]
        line = f"{icon} {d['name']}: {d['status']}"
        if d.get("reason"):
            line += f" — {d['reason']}"
        print(line)
        if d.get("fix"):
            print(f"    → {d['fix']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
