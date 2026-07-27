---
type: draft
title: "Decision-anchoring-PLAN"
status: implemented
timestamp: 2026-07-21
task: T-260721-03
---

# Decision-anchoring — PLAN thi hành

**Goal:** thi hành T1-T8 (v0.1 MUST + v0.2 SHOULD + v0.3 COULD) của SPEC — neo quyết định vào symbol, liveness suy từ code-graph. T9 (promote concept) KHÔNG nằm trong PLAN này — nó chỉ có ý nghĩa sau khi T1-T8 xanh, đúng luật commit-trước-wiki-sau.
**Architecture:** một engine liveness duy nhất (`harness/scripts/decision-liveness.py`) đọc TRỰC TIẾP `.graph-agent/index.db` (sqlite) thay vì gọi MCP `search_symbols`/`get_symbol_context` — lý do: script này chạy NGOÀI context Claude (subprocess/CLI), không có quyền gọi MCP tool; chỉ Claude-agent mới gọi được MCP. Đây là một BIẾN THỂ THI HÀNH của "THĂM DÒ code-graph" (Global constraints), không phải vi phạm nó — thăm dò chuyển từ "gọi MCP rồi kiểm response" sang "đọc thẳng DB mà chính MCP server ghi ra, kiểm schema + checksum tươi mới trước khi tin". Freshness ("project đã reindex") đo bằng so `sha256(file)[:16]` trên đĩa với cột `checksum` trong bảng `files` — đúng thuật toán server đã dùng (xác nhận bằng cách đọc DB thật: `245df759d10b7cc0` == `hashlib.sha256(data).hexdigest()[:16]`).
**Tech stack:** Python 3 stdlib (sqlite3, subprocess, re, hashlib) — không thêm dependency, tái dùng `db_has_schema()` từ `harness/scripts/dep-health.py` qua `importlib.util` (file có dấu gạch ngang, không import thẳng bằng tên module).
**SPEC nguồn:** `llmwiki/wiki/sources/draft/210721-decision-anchoring.md` (duyệt ngầm 2026-07-21, user: "rồi làm đi" + "trong chiều này xong cả 3 v0.1-0.3")

## Origin
- **SPEC:** `llmwiki/wiki/sources/draft/210721-decision-anchoring.md`
- **Commit:** _(verify-before-commit điền)_

## Global constraints

- `llmwiki/CLAUDE.md`: *"Wiki entries are only created AFTER code is committed — never during proposal or planning."* — không tạo `concepts/decision-anchoring.md` trong PLAN này (đó là T9, ngoài phạm vi).
- `dep-health.py` (nguyên tắc): *"quảng cáo một năng lực = phải THĂM DÒ nó, không phải kiểm sự tồn tại của nó."* — áp dụng qua checksum-freshness thay vì chỉ kiểm file `.is_file()`.
- Fail-open ở hook; fail-CLOSED CHỈ ở gate thật (không có gate mới ở đây — mọi báo cáo T1-T8 đều KHÔNG CHẶN, khớp FR-006/FR-007).
- Dependency chain (SPEC Global constraints): git khả dụng → code-graph resolve được → project đã reindex → LÚC ĐÓ mới tin liveness. Đứt bất kỳ tầng nào → UNAVAILABLE, không rơi xuống ORPHAN. Bản đọc-trực-tiếp-DB implement 3 tầng này là: `shutil.which("git")` → `db_has_schema(db_path)` → checksum trên `files.checksum` khớp `sha256(disk)[:16]`.
- Không đổi cơ chế `live_probe` hiện có — chỉ thêm trường mới (`anchor_symbol`, `confirmed`) cạnh nó (Non-goals SPEC).
- Mọi thứ báo cáo qua CLI/`/lint`, không xây UI riêng (Non-goals SPEC).
- Bằng chứng thật quan trọng đã xác nhận khi khảo sát: `.graph-agent/index.db` hiện có 108 file / 984 symbol, **KHÔNG index** `llmwiki/.claude/hooks/stop.py` (chỉ 4/10 file trong `hooks/` được index) — DB thật đang STALE/không đầy đủ ngay lúc viết PLAN này. Đây không phải lỗi cần fix ở PLAN này (out of scope: sửa indexer) — nó là ĐÚNG bằng chứng sống cho việc UNAVAILABLE phải hoạt động đúng trên dữ liệu thật, không giả lập. T2/T3 verify trên pilot `_debounced` SẼ trả UNAVAILABLE thật (not LIVE) vì lý do này — vẫn thoả SC-001 vì SC-001 chỉ đòi `why` trả được NỘI DUNG WHY, không đòi trạng thái phải là LIVE.
- T4 (test 3 nhánh code-side) và T5 (test drift) chạy trên **sandbox** (temp dir + `git init` riêng, KHÔNG phải nhánh git thật của repo) vì DB thật không index đủ để dựng cả 3 nhánh một cách kiểm-soát-được. Sandbox test engine `compute_state()`/`resolve_symbol()` với dữ liệu tự dựng — hành vi kiểm là CƠ CHẾ, không phụ thuộc symbol cụ thể nào.

## File structure

- Tạo `harness/scripts/decision-liveness.py` — engine liveness + CLI (`check`, `why`, `--self-test`). Trách nhiệm duy nhất: parse `mechanisms.yaml`, resolve `anchor_symbol`/`live_probe`, tính LIVE/STALE/ORPHAN/UNAVAILABLE.
- Sửa `harness/mechanisms.yaml` — thêm 1 entry mới (`stop-debounce`, T2) + 1 entry mới (`code-graph-probe-boundary`, T6), cả hai có `anchor_symbol`+`confirmed`.
- Sửa `llmwiki/skills/wiki-loop/lint.md` — thêm bước `8e` gọi `decision-liveness.py check`.
- Tạo `harness/scripts/decision-guard.py` — T8: validator so `git diff` của `mechanisms.yaml` THEO TỪNG `id`, cảnh báo xoá-lén.

### Task 1: Schema `anchor_symbol`/`confirmed` + engine liveness 4 trạng thái

**Thoả:** FR-001, FR-002, FR-004, FR-007

**Files:**
- Tạo: `harness/scripts/decision-liveness.py`
- Sửa: `harness/mechanisms.yaml` — chỉ thêm comment mô tả 2 trường mới ở đầu file (dòng ~14, cạnh comment `kind`/`surface` đã có), KHÔNG sửa 23 entry hiện có (chúng không có `anchor_symbol`, script phải bỏ qua không lỗi).

**Interfaces:**
- Produces (dùng bởi Task 2, 3, 6, 7):
  - `parse_mechanisms(text: str) -> list[dict]` — mỗi dict có khoá `id, name, desc, live_probe, anchor_symbol, confirmed, status` (thiếu thì `None`, `status` mặc định `"active"`).
  - `resolve_symbol(anchor_symbol: str, root: Path, db_path: Path) -> tuple[str, object]` — trả `(UNAVAILABLE, reason:str)` hoặc `(ORPHAN, reason:str)` hoặc `("RESOLVED", (line_start:int, line_end:int))`.
  - `compute_state(entry: dict, root: Path, db_path: Path) -> dict` — trả `{"path_state": "LIVE"|"ORPHAN"|None, "symbol_state": "LIVE"|"STALE"|"ORPHAN"|"UNAVAILABLE"|None, "symbol_info": str|None}`.
  - Hằng số: `LIVE, STALE, ORPHAN, UNAVAILABLE = "LIVE","STALE","ORPHAN","UNAVAILABLE"`.
  - `ROOT`, `MECH_PATH`, `DB_PATH` (module-level `Path`).

- [ ] **Step 1: viết self-test trước (assert-based, khớp convention `dep-health.py --self-test`)**

```python
# trong harness/scripts/decision-liveness.py, hàm self_test()
def ck(name, cond, fails):
    print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
    if not cond:
        fails.append(name)

def self_test() -> int:
    fails = []
    # 1. parse_mechanisms trên file thật: 23 mục cũ không có anchor_symbol -> compute_state
    #    bỏ qua symbol_state (None), không đổi trạng thái path_state đang có.
    text = MECH_PATH.read_text(encoding="utf-8")
    entries = parse_mechanisms(text)
    ck("parse >= 23 mục (không mất mục nào)", len(entries) >= 23, fails)
    legacy = [e for e in entries if not e.get("anchor_symbol")]
    ck("mục cũ (không anchor_symbol) -> symbol_state None",
       all(compute_state(e, ROOT, DB_PATH)["symbol_state"] is None for e in legacy[:23]), fails)
    return 1 if fails else 0
```

- [ ] **Step 2: chạy cho THẤY nó fail (chưa có `parse_mechanisms`/`compute_state`)**

Chạy: `python3 harness/scripts/decision-liveness.py --self-test`
Mong đợi: FAIL — `NameError: name 'parse_mechanisms' is not defined` (hoặc tương đương import lỗi).

- [ ] **Step 3: code engine đầy đủ**

```python
#!/usr/bin/env python3
"""decision-liveness — suy LIVE/STALE/ORPHAN/UNAVAILABLE cho anchor_symbol trong mechanisms.yaml.

Đọc TRỰC TIẾP .graph-agent/index.db (sqlite) — script chạy ngoài context Claude nên KHÔNG
gọi được MCP search_symbols/get_symbol_context (chỉ Claude-agent gọi được). Thay vào đó áp
đúng nguyên tắc dep-health.py ở tầng khác: quảng cáo một năng lực = phải THĂM DÒ, không phải
kiểm tồn tại — ở đây thăm dò là kiểm schema (db_has_schema, tái dùng dep-health.py) + kiểm
checksum file trên đĩa khớp cột `checksum` trong bảng `files` (proxy cho "project đã reindex",
vì không có cách nào khác đọc trạng thái reindex mà không qua MCP).

CLI:
    decision-liveness.py check [--json]      # mọi mục có anchor_symbol/live_probe -> trạng thái
    decision-liveness.py why <symbol>        # tra ngược symbol -> quyết định (mechanisms.yaml)
    decision-liveness.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MECH_PATH = ROOT / "harness/mechanisms.yaml"
DB_PATH = ROOT / ".graph-agent/index.db"

LIVE, STALE, ORPHAN, UNAVAILABLE = "LIVE", "STALE", "ORPHAN", "UNAVAILABLE"


def _load_dep_health():
    spec = importlib.util.spec_from_file_location(
        "dep_health", ROOT / "harness/scripts/dep-health.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_dh = _load_dep_health()


def parse_mechanisms(text: str) -> list:
    """Regex parse, cùng khuôn medic.py p_narrative() — không thêm dep pyyaml. Mỗi block bắt
    đầu bằng '- id:' (khớp indent 2 dấu cách của mechanisms.yaml thật)."""
    blocks = re.split(r'(?=^\s*-\s*id:\s*)', text, flags=re.M)
    entries = []
    for b in blocks:
        m_id = re.search(r'^\s*-\s*id:\s*(\S+)', b, re.M)
        if not m_id:
            continue

        def field(key, block=b):
            m = re.search(rf'^\s*{key}:\s*"?(.+?)"?\s*$', block, re.M)
            return m.group(1).strip() if m else None

        entries.append({
            "id": m_id.group(1),
            "name": field("name"),
            "desc": field("desc"),
            "live_probe": field("live_probe"),
            "anchor_symbol": field("anchor_symbol"),
            "confirmed": field("confirmed"),
            "status": field("status") or "active",
        })
    return entries


def parse_anchor(anchor_symbol: str):
    """<project>::<file>::<qualified-name> -> (project, file, name) hoặc None nếu sai định dạng."""
    parts = anchor_symbol.split("::")
    return tuple(parts) if len(parts) == 3 else None


def db_status(db_path: Path) -> str:
    """'ok'|'degraded'|'absent' — CHỈ kiểm schema (đọc trực tiếp DB, không cần server process
    sống — khác dep-health.probe_code_graph() vốn kiểm SERVER health cho tool-call qua MCP)."""
    if not db_path.is_file():
        return "absent"
    return "ok" if _dh.db_has_schema(db_path) else "degraded"


def resolve_symbol(anchor_symbol: str, root: Path, db_path: Path):
    """Trả (UNAVAILABLE, reason) | (ORPHAN, reason) | ("RESOLVED", (line_start, line_end))."""
    if not shutil.which("git"):
        return UNAVAILABLE, "git không có trên PATH (tầng 1 dependency chain đứt)"
    status = db_status(db_path)
    if status != "ok":
        return UNAVAILABLE, f"index.db {status} (tầng 2 đứt — DB thiếu/hỏng schema)"
    parsed = parse_anchor(anchor_symbol)
    if not parsed:
        return UNAVAILABLE, f"anchor_symbol sai định dạng: {anchor_symbol!r}"
    _project, file_rel, name = parsed
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute("SELECT id, checksum FROM files WHERE path = ?", (file_rel,)).fetchone()
        if not row:
            return UNAVAILABLE, f"{file_rel} chưa được index (tầng 3 đứt — project chưa reindex)"
        file_id, checksum = row
        disk = root / file_rel
        if not disk.is_file():
            return ORPHAN, f"{file_rel} đã bị xoá khỏi đĩa — symbol {name!r} không còn"
        real = hashlib.sha256(disk.read_bytes()).hexdigest()[:16]
        if checksum and real != checksum:
            return UNAVAILABLE, (f"{file_rel} đổi trên đĩa nhưng index chưa bắt kịp "
                                  f"(checksum lệch) — cần reindex trước khi tin liveness")
        sym = conn.execute(
            "SELECT line_start, line_end FROM symbols WHERE file_id = ? AND name = ?",
            (file_id, name)).fetchone()
    finally:
        conn.close()
    if not sym:
        return ORPHAN, f"symbol {name!r} không resolve được trong {file_rel} (đổi tên hoặc xoá)"
    return "RESOLVED", sym


def _commit_before_or_on(date_str: str, root: Path):
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "log", "-1", f"--until={date_str} 23:59:59", "--format=%H"],
            capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


def _touched_since(commit: str, file_rel: str, line_start: int, line_end: int, root: Path) -> bool:
    """True nếu diff commit->HEAD có hunk chạm [line_start, line_end] (số dòng phía NEW)."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "diff", "--unified=0", commit, "HEAD", "--", file_rel],
            capture_output=True, text=True, timeout=15)
    except Exception:
        return True  # không đọc được diff -> báo STALE (an toàn hơn im lặng LIVE)
    for m in re.finditer(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', out.stdout, re.M):
        new_start = int(m.group(1))
        new_len = int(m.group(2) or "1")
        new_end = new_start + max(new_len - 1, 0)
        if new_start <= line_end and new_end >= line_start:
            return True
    return False


def compute_state(entry: dict, root: Path, db_path: Path) -> dict:
    result = {"path_state": None, "symbol_state": None, "symbol_info": None}
    if entry.get("live_probe"):
        result["path_state"] = LIVE if (root / entry["live_probe"]).exists() else ORPHAN
    anchor = entry.get("anchor_symbol")
    if not anchor:
        return result
    state, info = resolve_symbol(anchor, root, db_path)
    if state in (UNAVAILABLE, ORPHAN):
        result["symbol_state"], result["symbol_info"] = state, info
        return result
    line_start, line_end = info
    confirmed = entry.get("confirmed")
    if not confirmed:
        result["symbol_state"] = STALE
        result["symbol_info"] = "có anchor_symbol nhưng chưa 'confirmed:' — coi như chưa xác nhận"
        return result
    _project, file_rel, _name = parse_anchor(anchor)
    commit = _commit_before_or_on(confirmed, root)
    if not commit:
        result["symbol_state"] = STALE
        result["symbol_info"] = f"không tìm được commit quanh confirmed={confirmed}"
        return result
    if _touched_since(commit, file_rel, line_start, line_end, root):
        result["symbol_state"] = STALE
        result["symbol_info"] = f"vùng dòng {line_start}-{line_end} đổi kể từ confirmed={confirmed}"
    else:
        result["symbol_state"] = LIVE
        result["symbol_info"] = f"resolve tại {file_rel}:{line_start}-{line_end}, không đổi kể từ {confirmed}"
    return result


def cmd_check(args):
    text = MECH_PATH.read_text(encoding="utf-8")
    entries = [e for e in parse_mechanisms(text) if e.get("anchor_symbol") or e.get("live_probe")]
    rows = []
    for e in entries:
        st = compute_state(e, ROOT, DB_PATH)
        rows.append({"id": e["id"], **st})
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    icon = {LIVE: "✓", STALE: "⚠", ORPHAN: "✗", UNAVAILABLE: "·", None: "-"}
    for r in rows:
        print(f"{icon[r['path_state']]}path {icon[r['symbol_state']]}symbol  {r['id']}"
              + (f" — {r['symbol_info']}" if r['symbol_info'] else ""))
    return 0


def cmd_why(args):
    text = MECH_PATH.read_text(encoding="utf-8")
    entries = parse_mechanisms(text)
    hits = [e for e in entries
            if (e.get("anchor_symbol") and args.symbol in e["anchor_symbol"])
            or (e.get("live_probe") and args.symbol in e["live_probe"])]
    if not hits:
        print(f"· không tìm thấy quyết định nào neo vào {args.symbol!r}")
        return 1
    for e in hits:
        st = compute_state(e, ROOT, DB_PATH)
        state = st["symbol_state"] or st["path_state"] or "?"
        print(f"[{e['id']}] {e['name']}  ({state})")
        print(f"  WHY: {e['desc']}")
        if st["symbol_info"]:
            print(f"  liveness: {st['symbol_info']}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="decision-anchoring liveness")
    sub = ap.add_subparsers(dest="cmd")
    p_check = sub.add_parser("check")
    p_check.add_argument("--json", action="store_true")
    p_why = sub.add_parser("why")
    p_why.add_argument("symbol")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if args.cmd == "check":
        sys.exit(cmd_check(args))
    if args.cmd == "why":
        sys.exit(cmd_why(args))
    ap.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
```

(Hàm `self_test()` viết ở Step 1 được MỞ RỘNG ở Task 4/5 — cùng file, cùng hàm, thêm case chứ không tạo hàm mới, tránh trùng lặp harness sandbox setup.)

- [ ] **Step 4: chạy lại — PASS**

Chạy: `python3 harness/scripts/decision-liveness.py --self-test`
Mong đợi: PASS, in `[OK ] parse >= 23 mục (không mất mục nào)` và `[OK ] mục cũ (không anchor_symbol) -> symbol_state None`.

- [ ] **Step 5: verify SC-007 (UNAVAILABLE khi code-graph không tới được) — thêm case vào self_test()**

```python
    # SC-007: DB không tồn tại -> mọi anchor_symbol phải UNAVAILABLE, KHÔNG ORPHAN
    fake_entry = {"id": "x", "anchor_symbol": "setup::nofile.py::foo", "confirmed": "2026-07-21"}
    st = compute_state(fake_entry, ROOT, Path("/khong-ton-tai/index.db"))
    ck("SC-007: DB vắng -> UNAVAILABLE không phải ORPHAN", st["symbol_state"] == UNAVAILABLE, fails)
```

Chạy: `python3 harness/scripts/decision-liveness.py --self-test` → PASS.

- [ ] **Step 6: verify FR-010 recovery (không cache UNAVAILABLE)**

```python
    # FR-010 recovery: gọi lại với DB THẬT (nếu có) ngay sau lần DB-vắng ở trên -> không kẹt UNAVAILABLE
    if DB_PATH.is_file():
        st2 = compute_state(fake_entry, ROOT, DB_PATH)
        ck("FR-010: recovery không kẹt cache UNAVAILABLE (đổi sang UNAVAILABLE lý do KHÁC hoặc ORPHAN vì DB thật không có nofile.py)",
           st2["symbol_state"] in (UNAVAILABLE, ORPHAN) and st2["symbol_info"] != st["symbol_info"], fails)
```

Chạy: `python3 harness/scripts/decision-liveness.py --self-test` → PASS. (`nofile.py` không có thật trong index.db → vẫn UNAVAILABLE nhưng vì lý do KHÁC "chưa index", chứng minh function không cache; test thật hơn ở Task 4/5 dùng sandbox có cả hai nhánh LIVE/UNAVAILABLE đổi qua lại.)

- [ ] **Step 7: commit**

```bash
git add harness/scripts/decision-liveness.py harness/mechanisms.yaml
git commit -m "feat(decision-anchoring): T1 — schema anchor_symbol/confirmed + engine liveness 4 trạng thái"
```

### Task 2: Neo pilot `_debounced`/`require_ok` (stop.py)

**Thoả:** FR-001, SC-001

**Files:**
- Sửa: `harness/mechanisms.yaml` (thêm 1 entry mới ở cuối mảng `mechanisms:`)

**Interfaces:**
- Consumes: không có trường mới nào — dùng đúng schema Task 1 đã định (`anchor_symbol`, `confirmed`).
- Produces: entry `id: stop-debounce` mà Task 3 (`why _debounced`) và self-test Task 1 sẽ đọc.

- [ ] **Step 1: thêm entry (nội dung `desc` lấy nguyên ý từ comment thật trong `stop.py:18-25`, không bịa)**

```yaml
  - id: stop-debounce
    name: "stop-debounce (_debounced/require_ok)"
    kind: hook
    surface: [mechanism]
    desc: "Stop hook debounce theo thời gian (mặc định 180s) cho 2 bước nặng nhất (build-wiki-graph 49s + medic --ci 26s) — p-45: cổng kích hoạt lỏng nên chúng fire gần mọi lượt dev framework, 75-90s thuế mỗi lần dừng. require_ok=True (dùng cho gate medic) chỉ bỏ qua nếu lần trước ĐÃ healthy — một FAIL luôn chạy lại ngay, debounce không bao giờ giấu regression thật."
    live_probe: llmwiki/.claude/hooks/stop.py
    anchor_symbol: "setup::llmwiki/.claude/hooks/stop.py::_debounced"
    confirmed: "2026-07-21"
```

- [ ] **Step 2: verify bằng chính engine Task 1**

Chạy: `python3 harness/scripts/decision-liveness.py check`
Mong đợi: một dòng cho `stop-debounce` — `path_state=LIVE` (file `stop.py` có thật), `symbol_state` gần như chắc chắn `UNAVAILABLE` (lý do: `.graph-agent/index.db` thật hiện KHÔNG index `stop.py` — đã xác nhận bằng khảo sát trực tiếp DB trước khi viết PLAN này). Đây là kết quả ĐÚNG theo dependency chain, không phải lỗi — evidence đính kèm vào Self-review khi verify.

- [ ] **Step 3: commit**

```bash
git add harness/mechanisms.yaml
git commit -m "feat(decision-anchoring): T2 — neo pilot symbol-level đầu tiên (_debounced, stop.py)"
```

### Task 3: Lệnh `why <symbol>`

**Thoả:** FR-003, SC-001

**Files:**
- Đã tạo ở Task 1: `harness/scripts/decision-liveness.py` (subcommand `why` đã viết sẵn trong Step 3 của Task 1 — Task này chỉ VERIFY, không thêm code mới).

**Interfaces:**
- Consumes: `parse_mechanisms`, `compute_state` (Task 1).
- Produces: output người đọc được qua CLI — không có consumer code nào khác.

- [ ] **Step 1: chạy trên pilot Task 2**

```bash
python3 harness/scripts/decision-liveness.py why _debounced
```

Mong đợi: in ra `[stop-debounce] stop-debounce (_debounced/require_ok)  (UNAVAILABLE)` + dòng `WHY: Stop hook debounce theo thời gian...` (đúng nội dung `desc` đã viết ở Task 2) + dòng `liveness: ... chưa được index...`. **Đây thoả SC-001**: người đọc được LÝ DO THIẾT KẾ mà không phải grep tay — trạng thái liveness UNAVAILABLE không ảnh hưởng gì tới việc đọc WHY (hai câu hỏi độc lập, đúng thiết kế `cmd_why` ở Task 1).

- [ ] **Step 2: chạy trên `live_probe` cũ (không có anchor_symbol) để xác nhận đường path-level vẫn hoạt động**

```bash
python3 harness/scripts/decision-liveness.py why orientation
```

Mong đợi: in `[orientation] orientation  (LIVE)` (từ `path_state`, vì `orientation` chỉ có `live_probe`, không có `anchor_symbol`) + `WHY:` đúng desc thật của entry `orientation` trong `mechanisms.yaml`.

- [ ] **Step 3: không cần commit riêng — code đã commit ở Task 1, đây là bước verify thuần**

### Task 4: Test 3 nhánh code-side (sửa thân / đổi tên / xoá) trên sandbox

**Thoả:** FR-002 (3 nhánh), SC-003

**Files:**
- Sửa: `harness/scripts/decision-liveness.py` — mở rộng `self_test()` (không tạo file test riêng, giữ 1 file "1 lệnh chạy hết" đúng convention `dep-health.py --self-test`).

**Interfaces:**
- Consumes: `compute_state`, `resolve_symbol` (Task 1), stdlib `tempfile`/`sqlite3`/`subprocess`.

- [ ] **Step 1: viết case dựng sandbox — git repo tạm + DB sqlite tạm mô phỏng đúng schema thật**

```python
    # --- Task 4: SC-003 — 3 nhánh code-side trên sandbox (KHÔNG đụng repo thật; DB thật
    # hiện không đủ index để dựng cả 3 nhánh trên cùng 1 symbol có kiểm soát) ---
    import tempfile, os

    def _sandbox_repo():
        td = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q"], cwd=td)
        subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=td)
        subprocess.run(["git", "config", "user.name", "t"], cwd=td)
        return Path(td)

    def _make_db(db_path, file_rel, checksum, symbols):
        # symbols: list[(name, line_start, line_end)]
        conn = sqlite3.connect(str(db_path))
        conn.executescript(
            "CREATE TABLE files(id INTEGER PRIMARY KEY, path TEXT, checksum TEXT);"
            "CREATE TABLE symbols(id INTEGER PRIMARY KEY, file_id INTEGER, name TEXT, "
            "line_start INTEGER, line_end INTEGER);")
        conn.execute("INSERT INTO files(id, path, checksum) VALUES (1, ?, ?)", (file_rel, checksum))
        for i, (name, ls, le) in enumerate(symbols, start=1):
            conn.execute("INSERT INTO symbols(id, file_id, name, line_start, line_end) "
                         "VALUES (?, 1, ?, ?, ?)", (i, name, ls, le))
        conn.commit()
        conn.close()

    def _sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]

    root = _sandbox_repo()
    mod = root / "mod.py"
    mod.write_text("def foo():\n    return 1\n\n\ndef bar():\n    return 2\n\n\ndef baz():\n    return 3\n")
    subprocess.run(["git", "add", "."], cwd=root)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root)
    confirmed_date = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%ad", "--date=short"],
                                     capture_output=True, text=True).stdout.strip()
    db = root / "index.db"
    _make_db(db, "mod.py", _sha(mod), [("foo", 1, 2), ("bar", 5, 6), ("baz", 9, 10)])

    entry_foo = {"id": "e-foo", "anchor_symbol": "sandbox::mod.py::foo", "confirmed": confirmed_date}
    entry_bar = {"id": "e-bar", "anchor_symbol": "sandbox::mod.py::bar", "confirmed": confirmed_date}
    entry_baz = {"id": "e-baz", "anchor_symbol": "sandbox::mod.py::baz", "confirmed": confirmed_date}

    st0 = compute_state(entry_bar, root, db)
    ck("sandbox baseline: bar chưa đổi -> LIVE", st0["symbol_state"] == LIVE, fails)

    # nhánh 1 — sửa thân foo() giữ tên, đổi tên baz()->baz2(), xoá hẳn KHÔNG áp dụng ở nhánh này
    mod.write_text("def foo():\n    return 999\n\n\ndef bar():\n    return 2\n\n\ndef baz2():\n    return 3\n")
    subprocess.run(["git", "add", "."], cwd=root)
    subprocess.run(["git", "commit", "-q", "-m", "edit+rename"], cwd=root)
    _make_db(db, "mod.py", _sha(mod), [("foo", 1, 2), ("bar", 5, 6), ("baz2", 9, 10)])

    st_foo = compute_state(entry_foo, root, db)
    ck("SC-003 sửa thân giữ tên -> STALE không phải ORPHAN", st_foo["symbol_state"] == STALE, fails)
    st_baz = compute_state(entry_baz, root, db)
    ck("SC-003 đổi tên -> ORPHAN đúng 1 chỗ (baz cũ)", st_baz["symbol_state"] == ORPHAN, fails)
    st_bar2 = compute_state(entry_bar, root, db)
    ck("SC-003 symbol không đụng (bar) vẫn LIVE, không lan cảnh báo", st_bar2["symbol_state"] == LIVE, fails)

    # nhánh 2 — xoá hẳn bar(), không có thay thế
    mod.write_text("def foo():\n    return 999\n\n\ndef baz2():\n    return 3\n")
    subprocess.run(["git", "add", "."], cwd=root)
    subprocess.run(["git", "commit", "-q", "-m", "delete bar"], cwd=root)
    _make_db(db, "mod.py", _sha(mod), [("foo", 1, 2), ("baz2", 5, 6)])

    st_bar3 = compute_state(entry_bar, root, db)
    ck("SC-003 xoá hẳn -> ORPHAN (cùng tín hiệu như đổi tên, đúng thiết kế FR-002)",
       st_bar3["symbol_state"] == ORPHAN, fails)

    import shutil as _sh
    _sh.rmtree(root, ignore_errors=True)
```

- [ ] **Step 2: chạy — PASS cả 4 assertion mới**

Chạy: `python3 harness/scripts/decision-liveness.py --self-test`
Mong đợi: PASS toàn bộ, gồm 4 dòng `[OK ] SC-003 ...` + `[OK ] sandbox baseline...`.

- [ ] **Step 3: commit**

```bash
git add harness/scripts/decision-liveness.py
git commit -m "test(decision-anchoring): T4 — 3 nhánh code-side (sửa thân/đổi tên/xoá) trên sandbox, SC-003"
```

### Task 5: Test drift thật kiểu `harness-local` trên sandbox

**Thoả:** SC-002

**Files:**
- Sửa: `harness/scripts/decision-liveness.py` (tiếp tục mở rộng `self_test()`).

**Interfaces:**
- Consumes: `compute_state` (đường `path_state`, dùng `live_probe` — không dùng `anchor_symbol`).

- [ ] **Step 1: mô phỏng lại đúng thao tác `git mv` làm `live_probe` gãy, đo phát hiện NGAY (không cần medic full suite)**

```python
    # --- Task 5: SC-002 — mô phỏng ca harness-local (file có live_probe bị dời) ---
    root2 = _sandbox_repo()
    target = root2 / "harness-local"
    target.mkdir()
    (target / "README.md").write_text("x")
    subprocess.run(["git", "add", "."], cwd=root2)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root2)

    entry_hl = {"id": "e-hl", "live_probe": "harness-local"}
    st_before = compute_state(entry_hl, root2, root2 / "index.db")
    ck("SC-002 trước khi dời: path_state LIVE", st_before["path_state"] == LIVE, fails)

    # git mv đúng thao tác đã xảy ra thật trong phiên 2026-07-21
    subprocess.run(["git", "mv", "harness-local", "llmwiki/harness-local-drift"], cwd=root2)
    subprocess.run(["git", "commit", "-q", "-m", "mv (mô phỏng drift)"], cwd=root2)

    st_after = compute_state(entry_hl, root2, root2 / "index.db")
    ck("SC-002 sau khi dời: path_state ORPHAN NGAY (không cần medic --ci)",
       st_after["path_state"] == ORPHAN, fails)
    # phát hiện ngay = một lệnh gọi compute_state() duy nhất, KHÔNG chạy build-wiki-graph.py
    # (49s) hay medic.py --ci (26s) — đúng nội dung SC-002 "không phải đợi medic --ci bắt được"
    _sh.rmtree(root2, ignore_errors=True)
```

- [ ] **Step 2: chạy — PASS**

Chạy: `python3 harness/scripts/decision-liveness.py --self-test`
Mong đợi: PASS thêm 2 dòng `[OK ] SC-002 ...`.

- [ ] **Step 3: commit**

```bash
git add harness/scripts/decision-liveness.py
git commit -m "test(decision-anchoring): T5 — mô phỏng drift kiểu harness-local trên sandbox, SC-002"
```

### Task 6: Neo boundary cho KÉO NGOÀI (`dep-health.py`/`code_graph_keeper.py`)

**Thoả:** FR-005, SC-004

**Files:**
- Sửa: `harness/mechanisms.yaml` (thêm 1 entry mới)

**Interfaces:**
- Consumes: schema Task 1.
- Produces: entry mà self-test Task 1's "quét toàn bộ anchor_symbol" (SC-004) sẽ đối chiếu.

- [ ] **Step 1: thêm entry — anchor trỏ vào ADAPTER trong repo (`dep-health.py`), KHÔNG trỏ ra `graph-kit` ngoài repo**

```yaml
  - id: code-graph-probe-boundary
    name: "code-graph probe boundary (thăm dò thay vì kiểm tồn tại)"
    kind: tool
    surface: [mechanism]
    desc: "Quyết định 2026-07-20: quảng cáo một dependency ngoài (code-graph) phải THĂM DÒ nó (schema DB, tiến trình server, code server có mới không) — không chỉ kiểm file .is_file(). Neo vào adapter trong repo (dep-health.py), không trỏ thẳng ra graph-kit ngoài repo vì graph-kit không index được (KÉO NGOÀI không version hoá theo pin)."
    live_probe: harness/scripts/dep-health.py
    anchor_symbol: "setup::harness/scripts/dep-health.py::probe_code_graph"
    confirmed: "2026-07-21"
```

- [ ] **Step 2: verify SC-004 — quét toàn bộ, không entry nào trỏ ra ngoài repo**

Thêm case vào `self_test()`:

```python
    # --- Task 6: SC-004 — mọi anchor_symbol trong mechanisms.yaml (thật) trỏ vào file TRONG repo ---
    real_entries = parse_mechanisms(MECH_PATH.read_text(encoding="utf-8"))
    anchored = [e for e in real_entries if e.get("anchor_symbol")]
    def _in_repo(e):
        parsed = parse_anchor(e["anchor_symbol"])
        return bool(parsed) and (ROOT / parsed[1]).resolve().is_relative_to(ROOT)
    ck(f"SC-004: {len(anchored)} mục có anchor_symbol, 100% trỏ file trong repo",
       len(anchored) > 0 and all(_in_repo(e) for e in anchored), fails)
```

Chạy: `python3 harness/scripts/decision-liveness.py --self-test` → PASS.

- [ ] **Step 3: commit**

```bash
git add harness/mechanisms.yaml harness/scripts/decision-liveness.py
git commit -m "feat(decision-anchoring): T6 — neo boundary KÉO NGOÀI vào adapter dep-health.py, SC-004"
```

### Task 7: Nối `/lint` báo cáo ORPHAN + STALE

**Thoả:** FR-006, SC-005

**Files:**
- Sửa: `llmwiki/skills/wiki-loop/lint.md` — thêm bước `8e` (sau `8d`, trước bước `9` "Append to log.md"), cùng khuôn report-không-chặn của `8c`/`8b`.

**Interfaces:**
- Consumes: `python3 harness/scripts/decision-liveness.py check` (Task 1) — output CLI, không có interface code.

- [ ] **Step 1: thêm bước vào `lint.md`**

Sửa file, chèn ngay sau dòng cuối của mục `8d` (trước mục `9. Append to llmwiki/wiki/log.md`):

```markdown
8e. **Decision-anchoring liveness (0 token, tất định)** — `RUN: python3 harness/scripts/decision-liveness.py check` (repo không có `harness/mechanisms.yaml` → bỏ qua bước này). In mọi mục có `anchor_symbol`/`live_probe` kèm nhãn `LIVE`/`STALE`/`ORPHAN`/`UNAVAILABLE` — người duyệt phân biệt ORPHAN (cần sửa neo hoặc xoá quyết định qua `status: retired`, KHÔNG xoá vật lý) với STALE (cần đọc lại, có thể vẫn đúng) chỉ bằng nhãn, không phải đọc lại toàn bộ nội dung (SC-005). **BÁO CÁO, KHÔNG CHẶN** — khớp khuôn không-chặn của draft-age/unknown-ledger (bước 8c).
```

- [ ] **Step 2: verify SC-005 — chạy thật, đọc output không cần hỏi lại máy**

Chạy: `python3 harness/scripts/decision-liveness.py check`
Mong đợi: mỗi dòng có ĐÚNG MỘT icon path + MỘT icon symbol rõ ràng (✓/⚠/✗/·), người đọc phân biệt ORPHAN (`✗`) khỏi STALE (`⚠`) ngay trên dòng, không cần mở file. Đối chiếu bằng mắt với 2 entry đã thêm ở Task 2/6.

- [ ] **Step 3: commit**

```bash
git add llmwiki/skills/wiki-loop/lint.md
git commit -m "feat(decision-anchoring): T7 — nối /lint báo cáo ORPHAN+STALE, SC-005"
```

### Task 8: Khoá lỗ hổng xoá-vật-lý (validator per-id git diff)

**Thoả:** FR-009 (Delete), FR-010 (Race), SC-006, SC-008(a)

**Files:**
- Tạo: `harness/scripts/decision-guard.py`

**Interfaces:**
- Consumes: `parse_mechanisms` (từ `decision-liveness.py`, import qua `importlib.util` — cùng pattern đã dùng để load `dep-health.py` ở Task 1, tránh trùng lặp parser).
- Produces: CLI đứng riêng, gọi được từ `/lint` (không bắt buộc trong T7 — T7 chỉ gọi `check`; `decision-guard.py` là công cụ RIÊNG cho câu hỏi "ai vừa xoá lén", chạy khi nghi ngờ hoặc thêm vào CI sau, ngoài phạm vi PLAN này để giữ T7 đúng đúng 1 trách nhiệm).

- [ ] **Step 1: viết `decision-guard.py` — so `git diff` HEAD vs working tree (hoặc 2 ref truyền vào) THEO TỪNG id**

```python
#!/usr/bin/env python3
"""decision-guard — bắt xoá-vật-lý một mục mechanisms.yaml có anchor_symbol/live_probe mà
KHÔNG đi qua status: retired. So diff THEO TỪNG id (FR-010, đóng nợ U-03) — không so nguyên
file, để hai người sửa hai mục KHÁC NHAU trong cùng file cùng một merge không báo oan nhau.

CLI:
    decision-guard.py check [--from REF] [--to REF]   # mặc định REF cũ=HEAD, REF mới=working tree
    decision-guard.py --self-test
"""
from __future__ import annotations
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MECH_PATH = ROOT / "harness/mechanisms.yaml"


def _load_liveness():
    spec = importlib.util.spec_from_file_location(
        "decision_liveness", ROOT / "harness/scripts/decision-liveness.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_dl = _load_liveness()


def _read_at(ref: str, path: Path, root: Path) -> str:
    """ref=None -> đọc working tree; ref='HEAD' -> đọc bản đã commit."""
    if ref is None:
        return path.read_text(encoding="utf-8")
    out = subprocess.run(["git", "-C", str(root), "show", f"{ref}:{path.relative_to(root)}"],
                          capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ""


def find_silent_deletes(old_text: str, new_text: str) -> list:
    """Trả list id bị XOÁ VẬT LÝ (có mặt ở old, vắng ở new) mà KHÔNG có id nào trong new
    mang status: retired thay thế đúng chỗ (kiểm bằng tập id, không kiểm nội dung — đủ cho
    câu hỏi 'mục đã biến mất chưa qua retired')."""
    old_ids = {e["id"]: e for e in _dl.parse_mechanisms(old_text) if e.get("anchor_symbol") or e.get("live_probe")}
    new_ids = {e["id"] for e in _dl.parse_mechanisms(new_text)}
    silent = []
    for oid, e in old_ids.items():
        if oid not in new_ids:
            silent.append(oid)
    return silent


def cmd_check(args):
    root = ROOT
    old_text = _read_at(args.from_ref, MECH_PATH, root)
    new_text = _read_at(args.to_ref, MECH_PATH, root) if args.to_ref else MECH_PATH.read_text(encoding="utf-8")
    if not old_text:
        print("· không đọc được bản cũ (ref không hợp lệ hoặc file mới tạo) — bỏ qua")
        return 0
    silent = find_silent_deletes(old_text, new_text)
    if not silent:
        print("✓ không có mục nào bị xoá vật lý ngoài status: retired")
        return 0
    for sid in silent:
        print(f"✗ mục '{sid}' đã BIẾN MẤT khỏi mechanisms.yaml mà không qua status: retired "
              f"(FR-009 — WHY biến mất không dấu vết, sửa lại bằng status: retired thay vì xoá dòng)")
    return 0  # BÁO CÁO, KHÔNG CHẶN (FR-006/Global constraints) — /lint gọi tay khi nghi ngờ


def self_test() -> int:
    fails = []
    def ck(name, cond):
        print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
        if not cond:
            fails.append(name)

    old = ("mechanisms:\n"
           "  - id: a\n    live_probe: x\n"
           "  - id: b\n    live_probe: y\n")
    # ca 1: xoá lén — b biến mất hoàn toàn
    new_silent = "mechanisms:\n  - id: a\n    live_probe: x\n"
    ck("phát hiện xoá lén (b biến mất)", find_silent_deletes(old, new_silent) == ["b"])

    # ca 2: xoá hợp lệ qua retired — id vẫn còn (chỉ đổi status), KHÔNG bị báo
    new_retired = ("mechanisms:\n  - id: a\n    live_probe: x\n"
                   "  - id: b\n    live_probe: y\n    status: retired\n")
    ck("xoá hợp lệ (status: retired, id còn) -> không báo", find_silent_deletes(old, new_retired) == [])

    # ca 3 (FR-010, race): hai mục KHÁC NHAU cùng đổi trong 1 merge — thêm mục mới (c) VÀ
    # retire mục cũ (b) cùng lúc -> chỉ so THEO ID, không báo oan mục hợp lệ
    new_race = ("mechanisms:\n  - id: a\n    live_probe: x\n"
                "  - id: b\n    live_probe: y\n    status: retired\n"
                "  - id: c\n    live_probe: z\n")
    ck("FR-010 race: thêm mục mới + retire mục khác cùng merge -> không báo oan (đóng nợ U-03)",
       find_silent_deletes(old, new_race) == [])

    print(f"\nSELF-TEST: {'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


def main():
    import argparse
    ap = argparse.ArgumentParser(description="decision-anchoring xoá-vật-lý guard")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("check")
    p.add_argument("--from", dest="from_ref", default="HEAD")
    p.add_argument("--to", dest="to_ref", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if args.cmd == "check":
        sys.exit(cmd_check(args))
    ap.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: chạy self-test — PASS cả 3 ca (xoá lén / retired hợp lệ / race FR-010)**

Chạy: `python3 harness/scripts/decision-guard.py --self-test`
Mong đợi: `SELF-TEST: ALL PASS`.

- [ ] **Step 3: verify SC-006 thật — thử xoá một mục có `anchor_symbol` trên sandbox, không qua `status: retired`**

```bash
python3 harness/scripts/decision-guard.py check --from HEAD
```
Mong đợi trên repo thật (chưa xoá gì): `✓ không có mục nào bị xoá vật lý ngoài status: retired` (đúng — Task 2/6 chỉ THÊM entry, không xoá).

- [ ] **Step 4: commit**

```bash
git add harness/scripts/decision-guard.py
git commit -m "feat(decision-anchoring): T8 — khoá xoá-vật-lý per-id git diff, SC-006 + race FR-010 (đóng U-03)"
```

### Task 9: Promote `concepts/decision-anchoring.md` — chỉ SAU khi T1-T8 committed và xanh

**Thoả:** FR-008, FR-010

**Files:**
- Tạo: `harness/scripts/decision-anchoring-crosscheck.py`
- Tạo: `llmwiki/wiki/concepts/decision-anchoring.md`

**Interfaces:**
- Consumes: `parse_mechanisms` (Task 1, import qua `importlib.util`), output thật của `decision-liveness.py --self-test` + `decision-guard.py --self-test` (exit code), nội dung thật `harness/mechanisms.yaml` sau Task 2/6.
- Produces: không có consumer code nào khác — đây là task cuối.

- [ ] **Step 1: viết script đối chiếu TRƯỚC (FR-010 trust-boundary — "không dựa vào lời tự khai của Claude")**

```python
#!/usr/bin/env python3
"""decision-anchoring-crosscheck — FR-010 trust boundary: concept KHÔNG được tự khai số đo；
mọi con số trích trong concept phải khớp output THẬT của decision-liveness.py/decision-guard.py.
Concept dùng convention `<!-- FACT: key=value -->` cho mỗi số đo trích dẫn; script đọc lại các
FACT đó và so với giá trị đo NGAY LÚC CHẠY — không tin lời tự khai lúc viết concept.

CLI:
    decision-anchoring-crosscheck.py check
    decision-anchoring-crosscheck.py --self-test
"""
from __future__ import annotations
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONCEPT = ROOT / "llmwiki/wiki/concepts/decision-anchoring.md"
MECH = ROOT / "harness/mechanisms.yaml"
FACT_RE = re.compile(r'<!--\s*FACT:\s*(\S+?)=(\S+?)\s*-->')


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def real_facts() -> dict:
    dl = _load("decision_liveness", "harness/scripts/decision-liveness.py")
    entries = dl.parse_mechanisms(MECH.read_text(encoding="utf-8"))
    anchored = [e for e in entries if e.get("anchor_symbol")]
    lv_rc = subprocess.run(
        [sys.executable, str(ROOT / "harness/scripts/decision-liveness.py"), "--self-test"],
        capture_output=True).returncode
    gd_rc = subprocess.run(
        [sys.executable, str(ROOT / "harness/scripts/decision-guard.py"), "--self-test"],
        capture_output=True).returncode
    return {
        "total_mechanisms": str(len(entries)),
        "anchored_symbol_count": str(len(anchored)),
        "liveness_self_test_exit": str(lv_rc),
        "guard_self_test_exit": str(gd_rc),
    }


def check() -> int:
    if not CONCEPT.is_file():
        print("· concept chưa tồn tại — chưa tới lúc chạy crosscheck")
        return 0
    claimed = dict(FACT_RE.findall(CONCEPT.read_text(encoding="utf-8")))
    if not claimed:
        print("✗ concept KHÔNG có FACT nào (thiếu <!-- FACT: key=value -->) — không đối chiếu được")
        return 1
    real = real_facts()
    bad = [f"{k}: concept khai {v!r}, thật đo được {real.get(k, '<không đo được>')!r}"
           for k, v in claimed.items() if real.get(k) != v]
    for b in bad:
        print(f"✗ {b}")
    if bad:
        return 1
    print(f"✓ {len(claimed)} FACT trong concept khớp output thật")
    return 0


def self_test() -> int:
    fails = []
    def ck(name, cond):
        print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
        if not cond:
            fails.append(name)
    m = FACT_RE.findall("vd: <!-- FACT: total_mechanisms=999 -->")
    ck("FACT_RE parse đúng 1 cặp key=value", m == [("total_mechanisms", "999")])
    print(f"\nSELF-TEST: {'ALL PASS' if not fails else str(len(fails)) + ' FAIL'}")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    sys.exit(check())
```

- [ ] **Step 2: chạy self-test script đối chiếu**

```bash
python3 harness/scripts/decision-anchoring-crosscheck.py --self-test
```

Mong đợi: `SELF-TEST: ALL PASS`.

- [ ] **Step 3: đo số thật (chỉ sau khi Task 1-8 đã commit) rồi viết concept với đúng số đó**

```bash
python3 -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('dl', 'harness/scripts/decision-liveness.py')
dl = importlib.util.module_from_spec(spec); spec.loader.exec_module(dl)
entries = dl.parse_mechanisms(open('harness/mechanisms.yaml', encoding='utf-8').read())
print('total_mechanisms=', len(entries))
print('anchored_symbol_count=', len([e for e in entries if e.get('anchor_symbol')]))
"
```

Dùng đúng 2 số in ra để viết `llmwiki/wiki/concepts/decision-anchoring.md` — nội dung văn xuôi đầy đủ (luật prose CLAUDE.md, KHÔNG caveman) tổng hợp `## Context`/`## Approaches` của SPEC + 4 trạng thái + dependency chain, kết bằng một khối:

```markdown
## Bằng chứng thật (FR-010 trust boundary — đối chiếu bằng máy, không tự khai)
<!-- FACT: total_mechanisms=<số thật> -->
<!-- FACT: anchored_symbol_count=<số thật> -->
<!-- FACT: liveness_self_test_exit=0 -->
<!-- FACT: guard_self_test_exit=0 -->
```

- [ ] **Step 4: chạy crosscheck thật — PHẢI pass trước khi coi concept hợp lệ**

```bash
python3 harness/scripts/decision-anchoring-crosscheck.py check
```

Mong đợi: `✓ 4 FACT trong concept khớp output thật`. Sai một số trong 4 FACT → script tự FAIL, đúng yêu cầu FR-010 ("không dựa vào lời tự khai của chính Claude khi viết concept").

- [ ] **Step 5: cập nhật index + log (luật `llmwiki/CLAUDE.md`), commit**

```bash
git add harness/scripts/decision-anchoring-crosscheck.py llmwiki/wiki/concepts/decision-anchoring.md llmwiki/wiki/index.md llmwiki/wiki/log.md
git commit -m "docs(decision-anchoring): T9 — promote concept, đối chiếu tự động với output thật T1-T8 (FR-008/FR-010)"
```

## Self-review

**Phủ SPEC.** Mỗi task khai `**Thoả:**` đúng id FR/SC của SPEC — FR-001/002/004/007 (Task 1), FR-003 (Task 3), SC-001 (Task 2+3), SC-002 (Task 5), SC-003 (Task 4), SC-004/FR-005 (Task 6), FR-006/SC-005 (Task 7), FR-009/FR-010/SC-006 (Task 8), FR-008 (Task 9). FR-004 (`confirmed` chỉ người bump) gắn vào Task 1 vì bằng chứng là SỰ VẮNG MẶT của code tự-bump trong chính engine đó — verify bằng cách đọc lại `decision-liveness.py` không có dòng nào ghi ngược vào `confirmed:`. FR-007 (không semantic drift) cũng gắn vào Task 1 cùng lý do — verify bằng cách xác nhận `decision-liveness.py`/`decision-guard.py` chỉ dùng stdlib + git + sqlite, không có lời gọi mô hình ngôn ngữ nào.

**Quét chỗ bỏ ngỏ.** Đã rà toàn văn, mọi mục Verify đều có lệnh chạy cụ thể và output mong đợi cụ thể; không mục nào chỉ nói "làm như Task khác" mà không chép code ra.

**Nhất quán tên/kiểu.** `compute_state()` trả `dict` cùng 3 khoá `path_state/symbol_state/symbol_info` xuyên suốt Task 1/4/5/6; `LIVE/STALE/ORPHAN/UNAVAILABLE` là 4 hằng số duy nhất, dùng lại y nguyên ở `decision-guard.py` qua import, không định nghĩa lại. `parse_mechanisms()` là điểm parse DUY NHẤT — `decision-guard.py` KHÔNG viết regex riêng, import từ `decision-liveness.py` (tránh trùng lặp/parser lệch nhau — bài học `medic.py`'s PROBE_MECH_MAP root-cause).

**Cổng ngược đã cân nhắc, KHÔNG bác SPEC.** Một điểm SPEC giả định (resolve qua MCP `search_symbols`/`get_symbol_context`) không khớp thực tế thi hành (script không gọi được MCP) — đây KHÔNG phải hai mục SPEC mâu thuẫn nhau, mà là một chi tiết THI HÀNH chưa được SPEC quyết định tường minh (SPEC chỉ nói "resolve qua code-graph", không nói qua kênh nào). PLAN chọn đọc trực tiếp DB — tương đương về mặt HÀNH VI (LIVE/STALE/ORPHAN/UNAVAILABLE đúng 4 trạng thái, đúng dependency chain 3 tầng) nên không cần quay lại `/propose`. Đã ghi rõ lý do trong `## Architecture` + `## Global constraints` để không im lặng trôi.
