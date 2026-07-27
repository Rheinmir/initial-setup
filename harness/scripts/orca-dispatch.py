#!/usr/bin/env python3
"""orca-dispatch — giao việc cho agent CLI BẤT KỲ qua Orca và biết chắc lúc nó XONG.

Vì sao tồn tại (đo 2026-07-20, T-260720-01):
  Trên 59 task orchestration của runtime Orca, chỉ 13 (22%) từng được dispatch;
  46 (78%) có `dispatch: null` — chưa bao giờ được giao. Toàn bộ 14 task đang treo
  (ready/blocked) đều thuộc nhóm chưa-từng-giao.

  Nguyên nhân KHÔNG phải Orca không giao được. Thử thật: `orca terminal create
  --command 'opencode run …'` chạy ngon, opencode trả lời đúng trong vài giây.
  Nhưng cùng lượt đó `orca terminal wait --for tui-idle --timeout-ms 90000` TIMEOUT,
  và `terminal read` vẫn báo status "running" — vì thứ đang chạy là SHELL, không
  phải agent. Orca không có trường `agent_status` ở bất kỳ đâu (đã soi `terminal
  list` 12 trường và `worktree ps`).

  ⇒ Chuỗi nhân quả: giao được → KHÔNG biết lúc nào xong → giám sát thành cực hình
  → coordinator bỏ cuộc, tự làm inline → 78% việc không bao giờ được giao.

Cách giải (mode HÒA TAN, chưng cất từ herdr — github.com/ogulcancelik/herdr, AGPL-3.0):
  herdr giải bài này bằng cách QUAN SÁT pane để suy ra agent_status, thay vì TIN vào
  việc agent tự khai báo. Ta lấy đúng cái ý đó, cài bằng đồ Orca sẵn có, KHÔNG chép
  code và KHÔNG nuốt 233k dòng hạ tầng:

      bọc lệnh:  <cmd> ; echo __ORCA_DONE__<id>:$?
      rồi poll:  orca terminal read  →  tìm sentinel

  Cơ chế nằm ở SHELL — tầng mà mọi CLI đều phải đi qua — nên nó đúng với claude,
  opencode, agy, copilot, và cả vendor chưa tồn tại hôm nay. Agent không cần biết
  gì về Orca, không cần hợp tác gửi worker_done.

GIỚI HẠN ĐÃ BIẾT (nói thẳng, đừng để ai hiểu nhầm):
  Nó đo LỆNH KẾT THÚC, không đo AGENT NGHĨ XONG. Với agent chạy một-phát
  (`opencode run`, `agy -p`) thì hai thứ trùng nhau. Với agent TUI tương tác thì
  KHÔNG trùng — lúc đó mới đáng cân nhắc cài herdr thật (xem proposal T-260720-01
  § Approaches phương án B).

CLI:
    orca-dispatch.py --self-test
    orca-dispatch.py --cmd '<lệnh>' [--worktree current] [--title T]
                     [--timeout-ms 300000] [--poll-ms 2000] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time

SENTINEL_PREFIX = "__ORCA_DONE__"
DEFAULT_TIMEOUT_MS = 300_000
DEFAULT_POLL_MS = 2_000


def make_sentinel(token: str) -> str:
    return f"{SENTINEL_PREFIX}{token}"


def wrap_command(cmd: str, token: str) -> str:
    """Bọc lệnh để shell tự khai kết thúc + exit code.

    Dùng `;` chứ KHÔNG `&&` — lệnh lỗi vẫn phải in sentinel, nếu không thì
    'xong-lỗi' và 'chưa xong' trông giống hệt nhau và coordinator treo vĩnh viễn.
    """
    return f"{cmd} ; echo {make_sentinel(token)}:$?"


def find_sentinel(lines, token: str):
    """Tìm sentinel trong output. Trả exit_code (int) hoặc None nếu chưa xong.

    Bỏ qua dòng CHỨA lệnh echo (dòng shell echo lại lệnh vừa gõ) — dòng đó có
    `echo ` đứng trước sentinel, còn dòng kết quả thật thì không.
    """
    pat = re.compile(rf"(?<!echo ){re.escape(make_sentinel(token))}:(-?\d+)\s*$")
    for line in lines:
        m = pat.search(line.rstrip())
        if m:
            return int(m.group(1))
    return None


def _orca(*args, timeout=30):
    out = subprocess.run(["orca", *args], capture_output=True, text=True, timeout=timeout)
    try:
        return json.loads(out.stdout)
    except (ValueError, TypeError):
        return None


def _read_lines(handle: str):
    d = _orca("terminal", "read", "--terminal", handle, "--json")
    if not d or not d.get("ok"):
        return []
    return (d.get("result", {}).get("terminal", {}) or {}).get("tail", []) or []


def dispatch(cmd: str, worktree="current", title=None, timeout_ms=DEFAULT_TIMEOUT_MS,
             poll_ms=DEFAULT_POLL_MS, token=None):
    """Giao lệnh cho một terminal Orca mới và chờ tới khi sentinel xuất hiện.

    Trả dict: {ok, done, exit_code, waited_ms, handle, output, error}
    Fail-open: thiếu `orca` hoặc runtime tắt → ok=False + error, KHÔNG raise.
    """
    if shutil.which("orca") is None:
        return {"ok": False, "done": False, "error": "orca không có trên PATH"}
    token = token or f"{int(time.time() * 1000) % 10**10:010d}"
    wrapped = wrap_command(cmd, token)
    args = ["terminal", "create", "--worktree", worktree, "--command", wrapped, "--json"]
    if title:
        args[2:2] = ["--title", title]
    d = _orca(*args)
    if not d or not d.get("ok"):
        return {"ok": False, "done": False,
                "error": f"terminal create thất bại: {(d or {}).get('error')}"}
    handle = (d.get("result", {}).get("terminal", {}) or {}).get("handle")
    if not handle:
        return {"ok": False, "done": False, "error": "không lấy được terminal handle"}

    t0 = time.monotonic()
    while (time.monotonic() - t0) * 1000 < timeout_ms:
        lines = _read_lines(handle)
        code = find_sentinel(lines, token)
        if code is not None:
            return {"ok": True, "done": True, "exit_code": code, "handle": handle,
                    "waited_ms": int((time.monotonic() - t0) * 1000),
                    "output": [l for l in lines if make_sentinel(token) not in l]}
        time.sleep(poll_ms / 1000)
    return {"ok": True, "done": False, "handle": handle,
            "waited_ms": int((time.monotonic() - t0) * 1000),
            "error": f"hết hạn {timeout_ms}ms mà chưa thấy sentinel",
            "output": _read_lines(handle)}


def self_test() -> int:
    """Tất định, KHÔNG cần runtime Orca — chạy được ở CI."""
    fails = []

    def ck(name, cond):
        print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
        if not cond:
            fails.append(name)

    ck("wrap dùng ';' chứ không '&&' (lệnh lỗi vẫn phải in sentinel)",
       ";" in wrap_command("false", "t1") and "&&" not in wrap_command("false", "t1"))
    ck("wrap có $? để bắt exit code", wrap_command("x", "t1").endswith(":$?"))
    ck("chưa xong → None", find_sentinel(["đang chạy...", "vẫn chạy"], "t1") is None)
    ck("xong ok → 0", find_sentinel(["kết quả", f"{SENTINEL_PREFIX}t1:0"], "t1") == 0)
    ck("xong LỖI → mã khác 0", find_sentinel([f"{SENTINEL_PREFIX}t1:127"], "t1") == 127)
    ck("token khác thì KHÔNG khớp (chống nhiễu chéo)",
       find_sentinel([f"{SENTINEL_PREFIX}t9:0"], "t1") is None)
    ck("bỏ qua dòng shell echo lại lệnh",
       find_sentinel([f"$ opencode run 'x' ; echo {SENTINEL_PREFIX}t1:$?"], "t1") is None)
    ck("agent in ra chuỗi giống sentinel nhưng khác token → không nhầm",
       find_sentinel(["agent nói: __ORCA_DONE__khac:0"], "t1") is None)
    ck("thiếu orca → fail-open, không raise",
       isinstance(dispatch("echo hi"), dict) if shutil.which("orca") is None else True)

    print(f"\nSELF-TEST: {'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


def main() -> None:
    ap = argparse.ArgumentParser(description="giao việc cho agent CLI qua Orca, biết lúc xong")
    ap.add_argument("--cmd", help="lệnh chạy trong terminal (vd: opencode run \"...\")")
    ap.add_argument("--worktree", default="current")
    ap.add_argument("--title", default=None)
    ap.add_argument("--timeout-ms", type=int, default=DEFAULT_TIMEOUT_MS)
    ap.add_argument("--poll-ms", type=int, default=DEFAULT_POLL_MS)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())
    if not a.cmd:
        sys.exit("orca-dispatch: cần --cmd (hoặc --self-test)")

    r = dispatch(a.cmd, a.worktree, a.title, a.timeout_ms, a.poll_ms)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        if not r.get("ok"):
            print(f"✗ {r.get('error')}")
        elif r.get("done"):
            code = r["exit_code"]
            print(f"{'✓' if code == 0 else '✗'} xong sau {r['waited_ms']}ms · exit={code}")
            for line in r.get("output", [])[-12:]:
                print(f"   {line}")
        else:
            print(f"⏱ {r.get('error')} (handle {r.get('handle')})")
    sys.exit(0 if r.get("ok") and r.get("done") and r.get("exit_code") == 0 else 1)


if __name__ == "__main__":
    main()
