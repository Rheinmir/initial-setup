---
type: draft
title: "Artifact-provenance-eventlog-PLAN"
status: implemented
timestamp: 2026-07-23
task: T-260722-01
---

# Artifact-provenance event log — PLAN thi hành

**Goal:** xây `harness/scripts/provenance-log.py` — adapter DUY NHẤT ghi/đọc sự kiện artifact-level (code.change/docs.change/decision.confirm) vào `harness/metrics/provenance-log.jsonl` (git-tracked, hash-chain theo writer, merge qua `merge=union`), cộng wiring vào decision-anchoring (`decision-liveness.py confirm`) và Stop hook (phân loại file đổi theo path-prefix).
**Architecture:** một file JSONL git-tracked, mỗi dòng = 1 sự kiện, hash-chain **theo từng `writer_id`** (không phải chuỗi toàn cục), merge qua git driver built-in `merge=union` (đã verify thật — xem Origin). Toàn bộ đọc/ghi qua 3 hàm trong MỘT module (`append_event`/`read_events`/`correlate`) — không nơi nào khác chạm thẳng file.
**Tech stack:** Python 3 stdlib (`json`, `hashlib`, `subprocess`, `datetime`, `fcntl`), tái dùng thuật toán hash-chain của `code-logger.py::_chain_hash`, tái dùng pattern sandbox-test đã verify trong `decision-liveness.py --self-test`.
**SPEC nguồn:** `llmwiki/wiki/sources/draft/220722-artifact-provenance-eventlog.md` (duyệt qua "chạy /plan đi", 2026-07-23)

**Phạm vi PLAN này: CHỈ T1-T5 (v0.1 + v0.2).** T6 (rotate, v0.3/COULD) bị loại khỏi PLAN — SPEC's Assumptions tự khai ngưỡng rotate là `(default, find-out-later → U-05)`, chưa có số cụ thể để viết test chống. Viết task cho một ngưỡng chưa quyết là placeholder giả trang — đúng điều khoản "Cổng ngược" của `/plan`: DỪNG thay vì viết PLAN nửa vời cho phần này. Mở PLAN riêng cho T6 khi U-05 được trả nợ.

## Origin
- **SPEC:** `llmwiki/wiki/sources/draft/220722-artifact-provenance-eventlog.md`
- **Commit:** _(verify-before-commit điền)_
- **Xác nhận thật trước khi viết PLAN (đúng luật "PLAN được quyền bác SPEC nếu bất khả thi"):** test `merge=union` trên sandbox git thật (`/tmp/union-test`) — 3 branch tự thêm dòng độc lập, merge xong đủ cả 3 dòng, KHÔNG cần `git config merge.union.driver` thêm gì — driver built-in hoạt động ngay từ `.gitattributes`. SPEC's tuyên bố kỹ thuật cốt lõi (FR-004) ĐÚNG, không cần sửa Approach A.

## Global constraints

(chép nguyên văn từ SPEC)

- `llmwiki/CLAUDE.md` prose rule: `## Context` và concept sẽ-promote viết văn xuôi đầy đủ, không caveman.
- Nguyên tắc "suy đừng cất": field nào git tính được (sha, author, UTC date) thì SUY, không cất tay song song.
- Không được PHÁ VỠ `events.jsonl` hay `scratch-log.jsonl` hiện có — log THỨ BA, mục đích riêng.
- Append-only, không xoá vật lý.
- Fail-open TUYỆT ĐỐI ở writer (`except Exception: pass`) — ghi log không bao giờ được chặn công việc chính.
- **Không** suy lại quan hệ NỘI DUNG "wiki nói về code nào" — `touches_targets` (`wiki-graph.py`) đã giải xong; `correlate()` CHỈ trả lời "cùng phiên/mạch công việc theo thời gian không".
- **Không** gộp vào `scratch-log.jsonl` — hai hợp đồng tin cậy khác nhau (curated/optional vs mandatory/automatic).
- Nhánh "cần agent phán đoán" của `correlate()` trả `related: None` — CHÍNH AGENT gọi nó mới là bên dùng tool-use schema `{is_related, confidence, reasoning}` để phán đoán tiếp; `correlate()` KHÔNG tự gọi LLM (nó là hàm thuần, tất định).

## File structure

- Tạo `harness/scripts/provenance-log.py` — module DUY NHẤT: `append_event()`, `read_events()`, `correlate()`, `classify_topic()`, CLI (`confirm-emit`, `record-changed`, `--self-test`).
- Tạo `.gitattributes` dòng mới: `harness/metrics/provenance-log.jsonl merge=union`.
- Sửa `harness/scripts/decision-liveness.py` — thêm subcommand `confirm <id> [--date YYYY-MM-DD]`: bump `confirmed:` trong `mechanisms.yaml` bằng text-edit, rồi gọi `provenance_log.append_event(topic="decision.confirm", ...)`.
- Sửa `llmwiki/.claude/hooks/stop.py::regen_docs()` — sau khi có `st` (git status --porcelain), gọi `provenance-log.py record-changed` qua subprocess (cùng pattern `resolve_tool`/`subprocess.run` đã dùng cho `wg`).

### Task 1: Module adapter — `append_event()`/`read_events()`, hash-chain theo writer

**Thoả:** FR-001, FR-002, FR-003, FR-007, FR-008

**Files:**
- Tạo: `harness/scripts/provenance-log.py`

**Interfaces:**
- Produces (dùng bởi Task 2, 3, 4, 5):
  - `append_event(root: Path, topic: str, **fields) -> None` — fail-open tuyệt đối, không bao giờ raise.
  - `read_events(root: Path, writer_id: str = None, topic: str = None, ref: str = None) -> list[dict]`.
  - `_chain_hash(prev_h: str, body: dict) -> str`, `_last_hash_for_writer(path: Path, writer_id: str) -> str`.
  - `_writer_id() -> str`, `_git_sha(root: Path) -> str`.
  - Hằng số: `EVENTS_PATH_REL = "harness/metrics/provenance-log.jsonl"`.

- [ ] **Step 1: viết self-test trước (assert-based, khớp convention `decision-liveness.py --self-test`)**

```python
# trong harness/scripts/provenance-log.py, hàm self_test()
def ck(name, cond, fails):
    print(f"  {'[OK ]' if cond else '[FAIL]'} {name}")
    if not cond:
        fails.append(name)

def self_test() -> int:
    import tempfile
    fails = []
    td = Path(tempfile.mkdtemp())
    (td / "harness" / "metrics").mkdir(parents=True)
    import subprocess as sp
    sp.run(["git", "init", "-q"], cwd=td)
    sp.run(["git", "config", "user.email", "t@t.t"], cwd=td)
    sp.run(["git", "config", "user.name", "t"], cwd=td)
    (td / "f.txt").write_text("x")
    sp.run(["git", "add", "-A"], cwd=td)
    sp.run(["git", "commit", "-q", "-m", "init"], cwd=td)

    append_event(td, "code.change", writer_id="w1", path="f.txt")
    events = read_events(td, writer_id="w1")
    ck("append_event ghi đúng 1 dòng, đọc lại được", len(events) == 1, fails)
    ck("event mang ts_utc dạng ISO8601 kết thúc 'Z'", events[0]["ts_utc"].endswith("Z"), fails)
    ck("event mang git_sha thật (không phải 'unknown')", len(events[0]["git_sha"]) == 40, fails)
    ck("mắt xích đầu tiên của writer -> prev='genesis'", events[0]["prev"] == "genesis", fails)

    append_event(td, "code.change", writer_id="w1", path="g.txt")
    e2 = read_events(td, writer_id="w1")
    ck("mắt xích thứ 2 cùng writer -> prev = h của mắt xích 1", e2[1]["prev"] == e2[0]["h"], fails)

    append_event(td, "code.change", writer_id="w2", path="h.txt")
    e_w2 = read_events(td, writer_id="w2")
    ck("writer KHÁC -> chuỗi riêng, prev='genesis' (không lẫn với w1)", e_w2[0]["prev"] == "genesis", fails)

    return 1 if fails else (0 if not fails else 1)
```

- [ ] **Step 2: chạy cho THẤY nó fail (chưa có `append_event`/`read_events`)**

Chạy: `python3 harness/scripts/provenance-log.py --self-test`
Mong đợi: FAIL — `NameError: name 'append_event' is not defined`.

- [ ] **Step 3: code adapter đầy đủ**

```python
#!/usr/bin/env python3
"""provenance-log — sổ sự kiện artifact-level, git-tracked, hash-chain THEO TỪNG writer_id.

Khác events.jsonl/scratch-log.jsonl/memory.jsonl/touches — xem llmwiki/wiki/concepts/log-model.md
để biết ranh giới. Sổ này CHỈ ghi sự kiện Ý NGHĨA artifact-level (code.change/docs.change/
decision.confirm/task.milestone), KHÔNG phải mọi tool-call. Adapter DUY NHẤT — mọi nơi khác
PHẢI gọi qua 3 hàm append_event/read_events/correlate, không chạm thẳng file (FR-007, chừa
slot migrate sang broker thật sau này chỉ bằng cách viết lại nội dung file này).

CLI:
    provenance-log.py record-changed [--root DIR]     # phân loại + ghi mọi file đổi (git status)
    provenance-log.py confirm-emit --id ID [--note TEXT] [--root DIR]  # T3 dùng nội bộ
    provenance-log.py --self-test
"""
from __future__ import annotations

import hashlib
import json
import re
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path

EVENTS_PATH_REL = "harness/metrics/provenance-log.jsonl"

# Đồng bộ tay với llmwiki/.claude/hooks/stop.py::_CODE_RE — hai file khác thư mục (hooks/ vs
# harness/scripts/), import chéo phức tạp hơn giá trị mang lại cho 1 regex; đổi 1 bên thì đổi
# luôn bên kia (cùng pattern đã chấp nhận ở medic.py's PROBE_MECH_MAP).
_CODE_RE = re.compile(r"\.(py|js|jsx|ts|tsx|mjs|cjs|go|rs|java|rb|php|c|h|cpp|cc|sh)$")


def _events_path(root: Path) -> Path:
    return Path(root) / EVENTS_PATH_REL


def _canon(body: dict) -> str:
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _chain_hash(prev_h: str, body: dict) -> str:
    """Tái dùng nguyên thuật toán code-logger.py::_chain_hash (FR-003)."""
    return hashlib.sha256((str(prev_h) + "\n" + _canon(body)).encode("utf-8")).hexdigest()


def _last_hash_for_writer(path: Path, writer_id: str) -> str:
    """h của dòng CUỐI CÙNG thuộc writer_id này. 'genesis' nếu writer chưa ghi dòng nào."""
    last = None
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rec = json.loads(ln)
                except Exception:
                    continue
                if rec.get("writer_id") == writer_id:
                    last = rec
    except FileNotFoundError:
        return "genesis"
    return (last.get("h") or "genesis") if last else "genesis"


def _writer_id() -> str:
    """<vendor>::<session_id>::<hostname> (FR-002) — không đăng ký tập trung (Assumptions)."""
    import os
    session = os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("SESSION_ID") or "unknown-session"
    vendor = os.environ.get("PROVENANCE_VENDOR", "claude-code")
    return f"{vendor}::{session}::{socket.gethostname()}"


def _git_sha(root: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=5)
        sha = out.stdout.strip()
        return sha if sha else "unknown"
    except Exception:
        return "unknown"


def append_event(root, topic: str, **fields) -> None:
    """Fail-open TUYỆT ĐỐI (FR-008) — never raise, never block caller."""
    try:
        root = Path(root)
        path = _events_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        writer_id = fields.pop("writer_id", None) or _writer_id()
        rec = {
            "writer_id": writer_id,
            "topic": topic,
            "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "git_sha": _git_sha(root),
        }
        rec.update({k: v for k, v in fields.items() if v is not None})
        with open(path, "a", encoding="utf-8") as f:
            try:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX)
            except Exception:
                pass
            rec["prev"] = _last_hash_for_writer(path, writer_id)
            rec["h"] = _chain_hash(rec["prev"], rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_events(root, writer_id: str = None, topic: str = None, ref: str = None) -> list:
    path = _events_path(Path(root))
    out = []
    if not path.is_file():
        return out
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = json.loads(ln)
            except Exception:
                continue
            if writer_id and rec.get("writer_id") != writer_id:
                continue
            if topic and rec.get("topic") != topic:
                continue
            if ref and rec.get("ref") != ref:
                continue
            out.append(rec)
    return out
```

- [ ] **Step 4: chạy lại — PASS**

Chạy: `python3 harness/scripts/provenance-log.py --self-test`
Mong đợi: PASS toàn bộ 6 case trong Step 1.

- [ ] **Step 5: verify SC-005 (fail-open thật khi ghi lỗi) — thêm case vào self_test()**

```python
    # SC-005: DB path trỏ vào thư mục KHÔNG THỂ TẠO (fail-open thật, không phải lời hứa)
    bad_root = Path("/proc/nonexistent-root-xyz")  # path chắc chắn không ghi được
    try:
        append_event(bad_root, "code.change", writer_id="w1", path="x")
        ck("SC-005: ghi vào root hỏng không raise (fail-open thật)", True, fails)
    except Exception as e:
        ck(f"SC-005: fail-open THẤT BẠI — lộ exception {type(e).__name__}", False, fails)
```

Chạy: `python3 harness/scripts/provenance-log.py --self-test` → PASS.

- [ ] **Step 6: viết CLI tối thiểu (`main()`) để Task 2-5 gọi được từ subprocess**

```python
def main():
    import argparse, sys
    ap = argparse.ArgumentParser(description="provenance-log — artifact event ledger")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("record-changed").add_argument("--root", default=".")
    p_confirm = sub.add_parser("confirm-emit")
    p_confirm.add_argument("--id", required=True)
    p_confirm.add_argument("--note", default=None)
    p_confirm.add_argument("--root", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if args.cmd == "confirm-emit":
        append_event(Path(args.root), "decision.confirm", ref=args.id, note=args.note)
        sys.exit(0)
    if args.cmd == "record-changed":
        sys.exit(0)  # thân thật viết ở Task 5 (cần classify_topic từ Task 5)
    ap.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: commit**

```bash
git add harness/scripts/provenance-log.py
git commit -m "feat(provenance-log): T1 — adapter append_event/read_events, hash-chain theo writer"
```

### Task 2: `.gitattributes` merge=union — verify merge 2 branch thật

**Thoả:** FR-004

**Files:**
- Tạo: `.gitattributes` (thêm dòng nếu file đã tồn tại, tạo mới nếu chưa — kiểm bằng `test -f .gitattributes`).
- Sửa: `harness/scripts/provenance-log.py` — mở rộng `self_test()`.

**Interfaces:**
- Consumes: `append_event()`, `read_events()` (Task 1).

- [ ] **Step 1: thêm dòng `.gitattributes` (repo thật, không phải sandbox)**

```bash
grep -qxF "harness/metrics/provenance-log.jsonl merge=union" .gitattributes 2>/dev/null || \
  echo "harness/metrics/provenance-log.jsonl merge=union" >> .gitattributes
```

Mong đợi: `cat .gitattributes | grep provenance-log` in ra đúng dòng.

- [ ] **Step 2: thêm case self-test — merge 2 branch thật trên sandbox (KHÔNG đụng repo thật)**

```python
    # --- Task 2: SC-001 — merge=union thật trên sandbox git 2 branch ---
    td2 = Path(tempfile.mkdtemp())
    sp.run(["git", "init", "-q"], cwd=td2)
    sp.run(["git", "config", "user.email", "t@t.t"], cwd=td2)
    sp.run(["git", "config", "user.name", "t"], cwd=td2)
    (td2 / ".gitattributes").write_text(f"{EVENTS_PATH_REL} merge=union\n")
    (td2 / "harness" / "metrics").mkdir(parents=True)
    (td2 / EVENTS_PATH_REL).write_text("")
    sp.run(["git", "add", "-A"], cwd=td2)
    sp.run(["git", "commit", "-q", "-m", "init"], cwd=td2)

    sp.run(["git", "checkout", "-q", "-b", "branch-a"], cwd=td2)
    append_event(td2, "code.change", writer_id="session-a", path="a.py")
    sp.run(["git", "add", "-A"], cwd=td2)
    sp.run(["git", "commit", "-q", "-m", "event a"], cwd=td2)

    sp.run(["git", "checkout", "-q", "-"], cwd=td2)  # quay lại nhánh trước (main/master)
    append_event(td2, "code.change", writer_id="session-b", path="b.py")
    sp.run(["git", "add", "-A"], cwd=td2)
    sp.run(["git", "commit", "-q", "-m", "event b"], cwd=td2)

    merge_out = sp.run(["git", "merge", "branch-a", "--no-edit"], cwd=td2, capture_output=True, text=True)
    ck("SC-001: git merge không lỗi", merge_out.returncode == 0, fails)
    merged = read_events(td2)
    ck("SC-001: merge xong ĐỦ 2 sự kiện của cả 2 nhánh, không mất dòng",
       len(merged) == 2 and {e["writer_id"] for e in merged} == {"session-a", "session-b"}, fails)
```

- [ ] **Step 3: chạy — PASS**

Chạy: `python3 harness/scripts/provenance-log.py --self-test`
Mong đợi: PASS thêm 2 dòng `[OK ] SC-001 ...`.

- [ ] **Step 4: commit**

```bash
git add .gitattributes harness/scripts/provenance-log.py
git commit -m "feat(provenance-log): T2 — merge=union cho provenance-log.jsonl, verify SC-001 thật"
```

### Task 3: Wiring decision-anchoring — `decision-liveness.py confirm`

**Thoả:** FR-006

**Files:**
- Sửa: `harness/scripts/decision-liveness.py:408-419` (hàm `main()`, thêm subparser `confirm`).

**Interfaces:**
- Consumes: `provenance_log.append_event()` (Task 1) — import qua `importlib.util`, cùng pattern đã dùng để load `dep-health.py` trong chính file này.
- Produces: CLI `decision-liveness.py confirm <id> [--date YYYY-MM-DD]`.

- [ ] **Step 1: viết hàm bump text-edit + gọi append_event (thêm vào `decision-liveness.py`, trước `def main():`)**

```python
def _load_provenance_log():
    spec = importlib.util.spec_from_file_location(
        "provenance_log", ROOT / "harness/scripts/provenance-log.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def bump_confirmed(mech_id: str, date_str: str, root: Path = ROOT) -> bool:
    """Sửa TRỰC TIẾP dòng 'confirmed:' của đúng entry mech_id trong mechanisms.yaml (text-edit,
    giữ nguyên mọi dòng khác — KHÔNG parse/serialize lại cả YAML, tránh phá format comment).
    Trả True nếu tìm thấy và sửa được, False nếu không tìm thấy mech_id."""
    text = MECH_PATH.read_text(encoding="utf-8")
    blocks = re.split(r'(?=^\s*-\s*id:\s*)', text, flags=re.M)
    for i, b in enumerate(blocks):
        m_id = re.search(r'^\s*-\s*id:\s*(\S+)', b, re.M)
        if not (m_id and m_id.group(1) == mech_id):
            continue
        if re.search(r'^\s*confirmed:', b, re.M):
            new_b = re.sub(r'^(\s*confirmed:\s*).*$', rf'\g<1>"{date_str}"', b, count=1, flags=re.M)
        else:
            new_b = b.rstrip("\n") + f'\n    confirmed: "{date_str}"\n'
        blocks[i] = new_b
        MECH_PATH.write_text("".join(blocks), encoding="utf-8")
        pl = _load_provenance_log()
        pl.append_event(root, "decision.confirm", ref=mech_id, note=f"bump confirmed: {date_str}")
        return True
    return False
```

- [ ] **Step 2: viết test fail trước (thêm case vào `self_test()` của `decision-liveness.py`)**

```python
    # --- Task 3: FR-006 — bump_confirmed phát event decision.confirm thật ---
    import tempfile as _tf, shutil as _sh3
    td3 = Path(_tf.mkdtemp())
    (td3 / "harness").mkdir()
    fake_mech = td3 / "harness" / "mechanisms.yaml"
    fake_mech.write_text('mechanisms:\n  - id: demo-id\n    live_probe: x\n    confirmed: "2020-01-01"\n')
    sp.run(["git", "init", "-q"], cwd=td3)
    sp.run(["git", "config", "user.email", "t@t.t"], cwd=td3)
    sp.run(["git", "config", "user.name", "t"], cwd=td3)
    (td3 / "x").write_text("x")
    sp.run(["git", "add", "-A"], cwd=td3)
    sp.run(["git", "commit", "-q", "-m", "init"], cwd=td3)
    global MECH_PATH
    _orig_mech = MECH_PATH
    MECH_PATH = fake_mech
    try:
        ok = bump_confirmed("demo-id", "2026-07-23", root=td3)
        ck("FR-006: bump_confirmed tìm đúng entry, trả True", ok, fails)
        new_text = fake_mech.read_text()
        ck("FR-006: confirmed: đã đổi thành ngày mới", '"2026-07-23"' in new_text, fails)
        pl = _load_provenance_log()
        evs = pl.read_events(td3, topic="decision.confirm", ref="demo-id")
        ck("FR-006: đúng 1 event decision.confirm được ghi", len(evs) == 1, fails)
    finally:
        MECH_PATH = _orig_mech
        _sh3.rmtree(td3, ignore_errors=True)
```

- [ ] **Step 3: chạy cho THẤY fail (chưa có `bump_confirmed`/`_load_provenance_log`)**

Chạy: `python3 harness/scripts/decision-liveness.py --self-test`
Mong đợi: FAIL — `NameError: name 'bump_confirmed' is not defined`.

- [ ] **Step 4: thêm code Step 1 vào file thật, thêm subparser CLI**

Sửa `main()` (dòng 408-419 hiện tại), chèn trước dòng `args = ap.parse_args()`:

```python
    p_confirm = sub.add_parser("confirm")
    p_confirm.add_argument("id")
    p_confirm.add_argument("--date", default=None)
```

Và trong khối xử lý `args.cmd` (sau `if args.cmd == "why":`), thêm:

```python
    if args.cmd == "confirm":
        date_str = args.date or datetime.now().strftime("%Y-%m-%d")
        ok = bump_confirmed(args.id, date_str)
        print(f"{'✓' if ok else '✗'} confirmed: {args.id} -> {date_str}" if ok
              else f"✗ không tìm thấy id={args.id!r} trong mechanisms.yaml")
        sys.exit(0 if ok else 1)
```

Thêm `import importlib.util` và `from datetime import datetime` vào đầu file nếu chưa có (kiểm bằng `grep "^import\|^from" harness/scripts/decision-liveness.py` trước khi thêm, tránh trùng).

- [ ] **Step 5: chạy lại — PASS**

Chạy: `python3 harness/scripts/decision-liveness.py --self-test`
Mong đợi: PASS thêm 3 dòng `[OK ] FR-006 ...`.

- [ ] **Step 6: verify CLI thật trên repo thật (không phải sandbox) — dùng chính pilot đã có**

```bash
python3 harness/scripts/decision-liveness.py confirm stop-debounce --date 2026-07-23
python3 harness/scripts/provenance-log.py --self-test   # xác nhận adapter vẫn lành sau khi bị gọi chéo
grep "decision.confirm" harness/metrics/provenance-log.jsonl | tail -1
```

Mong đợi: dòng cuối `harness/metrics/provenance-log.jsonl` có `"topic":"decision.confirm"`, `"ref":"stop-debounce"`.

- [ ] **Step 7: commit**

```bash
git add harness/scripts/decision-liveness.py
git commit -m "feat(decision-anchoring): T3 — subcommand confirm phát event decision.confirm (FR-006)"
```

### Task 4: `correlate()` — phạm vi hẹp temporal-proximity, tool-use schema khi mơ hồ

**Thoả:** FR-005

**Files:**
- Sửa: `harness/scripts/provenance-log.py` — thêm `correlate()` + mở rộng `self_test()`.

**Interfaces:**
- Consumes: `read_events()` (Task 1) — 2 dict event đã đọc từ đó.
- Produces: `correlate(event_a: dict, event_b: dict, threshold_s: int = 600) -> dict` với khoá `related: bool|None`, `reason: str`.

- [ ] **Step 1: viết test fail trước**

```python
    # --- Task 4: FR-005/SC-003 — correlate() CHỈ temporal, không suy nội dung ---
    ea = {"writer_id": "w1", "ts_utc": "2026-07-22T01:00:00Z"}
    eb_close = {"writer_id": "w1", "ts_utc": "2026-07-22T01:05:00Z"}
    eb_far_diff_writer = {"writer_id": "w2", "ts_utc": "2026-07-22T10:00:00Z"}
    eb_ambiguous = {"writer_id": "w2", "ts_utc": "2026-07-22T01:03:00Z", "task_id": "T-1"}
    ea_task = {**ea, "task_id": "T-1"}

    r1 = correlate(ea, eb_close)
    ck("SC-003: cùng writer, trong ngưỡng 10' -> related=True", r1["related"] is True, fails)

    r2 = correlate(ea, eb_far_diff_writer)
    ck("SC-003: khác writer, khác task, cách xa -> related=False (không đề xuất sai)",
       r2["related"] is False, fails)

    r3 = correlate(ea_task, eb_ambiguous)
    ck("FR-005: khác writer nhưng cùng task_id, ngoài ngưỡng -> None (cần agent phán đoán)",
       r3["related"] is None and "agent" in r3["reason"], fails)
```

- [ ] **Step 2: chạy cho THẤY fail**

Chạy: `python3 harness/scripts/provenance-log.py --self-test`
Mong đợi: FAIL — `NameError: name 'correlate' is not defined`.

- [ ] **Step 3: code `correlate()`**

```python
def _parse_ts(ts_utc: str) -> datetime:
    return datetime.strptime(ts_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def correlate(event_a: dict, event_b: dict, threshold_s: int = 600) -> dict:
    """FR-005: CHỈ temporal-proximity — 'hai sự kiện có cùng phiên/mạch công việc không'.
    KHÔNG phân tích nội dung/path để suy quan hệ ngữ nghĩa — đó là việc của
    wiki-graph.py::touches_targets (content-based, đã giải xong, xem log-model.md).
    related=True/False khi tín hiệu RÕ; related=None ('cần agent phán đoán') khi mơ hồ —
    caller (agent) tự dùng tool-use schema {is_related, confidence, reasoning} để quyết tiếp."""
    ts_a, ts_b = _parse_ts(event_a["ts_utc"]), _parse_ts(event_b["ts_utc"])
    delta = abs((ts_a - ts_b).total_seconds())
    same_writer = event_a.get("writer_id") == event_b.get("writer_id")
    same_task = bool(event_a.get("task_id")) and event_a.get("task_id") == event_b.get("task_id")
    if same_writer and delta <= threshold_s:
        return {"related": True, "reason": f"cùng writer_id, cách nhau {int(delta)}s <= ngưỡng {threshold_s}s"}
    if not same_writer and not same_task:
        return {"related": False, "reason": "khác writer_id, khác task_id — không có tín hiệu liên quan"}
    return {"related": None,
            "reason": "cần agent phán đoán — tín hiệu thời gian không đủ rõ ràng (tool-use schema {is_related, confidence, reasoning})",
            "delta_s": delta, "same_writer": same_writer, "same_task": same_task}
```

- [ ] **Step 4: chạy lại — PASS**

Chạy: `python3 harness/scripts/provenance-log.py --self-test`
Mong đợi: PASS thêm 3 dòng `[OK ] SC-003.../FR-005...`.

- [ ] **Step 5: commit**

```bash
git add harness/scripts/provenance-log.py
git commit -m "feat(provenance-log): T4 — correlate() phạm vi hẹp temporal-only (FR-005)"
```

### Task 5: Wiring Stop hook — phân loại code.change/docs.change theo PATH PREFIX

**Thoả:** FR-001

**Files:**
- Sửa: `harness/scripts/provenance-log.py` — thêm `classify_topic()` + thân thật cho CLI `record-changed`.
- Sửa: `llmwiki/.claude/hooks/stop.py:132-138` (trong `regen_docs()`, ngay sau khối `if (wikigraph_on and ...)`).

**Interfaces:**
- Consumes: `append_event()` (Task 1).
- Produces: `classify_topic(path: str) -> str | None` — `"docs.change"` | `"code.change"` | `None`.

- [ ] **Step 1: viết test fail trước cho `classify_topic()`**

```python
    # --- Task 5: FR-001 — classify_topic() theo PATH PREFIX, không theo đuôi file ---
    ck("wiki thật (llmwiki/wiki/*.md) -> docs.change",
       classify_topic("llmwiki/wiki/concepts/decision-anchoring.md") == "docs.change", fails)
    ck("SKILL.md KHÔNG phải wiki (dù cùng đuôi .md) -> code.change, không phải docs.change",
       classify_topic("skills/fdk-uat/SKILL.md") == "code.change", fails)
    ck("README.md ở gốc repo -> code.change (không thuộc llmwiki/wiki/)",
       classify_topic("README.md") == "code.change", fails)
    ck("file .py bất kỳ -> code.change", classify_topic("harness/scripts/foo.py") == "code.change", fails)
    ck("file .json (không khớp _CODE_RE, không phải wiki) -> None (không ghi)",
       classify_topic("harness/metrics/tasks.json") is None, fails)
```

- [ ] **Step 2: chạy cho THẤY fail**

Chạy: `python3 harness/scripts/provenance-log.py --self-test`
Mong đợi: FAIL — `NameError: name 'classify_topic' is not defined`.

- [ ] **Step 3: code `classify_topic()` + thân thật `record-changed`**

```python
def classify_topic(path: str) -> str:
    """'docs.change' CHỈ khi path nằm trong llmwiki/wiki/ (wiki thật) VÀ đuôi .md — theo PREFIX,
    không theo đuôi file (SKILL.md/README.md/*-PLAN.md không phải wiki dù cùng đuôi .md).
    'code.change' nếu khớp _CODE_RE và KHÔNG phải wiki. None nếu không thuộc loại nào."""
    p = path.replace("\\", "/").lstrip("./")
    if p.startswith("llmwiki/wiki/") and p.endswith(".md"):
        return "docs.change"
    if _CODE_RE.search(p):
        return "code.change"
    return None


def _changed_paths(root: Path) -> list:
    out = subprocess.run(["git", "-C", str(root), "status", "--porcelain"],
                          capture_output=True, text=True, timeout=8).stdout
    paths = []
    for ln in out.splitlines():
        if len(ln) < 4:
            continue
        p = ln[3:].strip()
        if " -> " in p:  # rename: lấy path MỚI
            p = p.split(" -> ", 1)[1]
        paths.append(p.strip('"'))
    return paths


def record_changed(root: Path) -> int:
    n = 0
    for p in _changed_paths(root):
        topic = classify_topic(p)
        if topic:
            append_event(root, topic, path=p)
            n += 1
    return n
```

Sửa hàm `main()` (Task 1 Step 6) — thay dòng `if args.cmd == "record-changed": sys.exit(0)` bằng:

```python
    if args.cmd == "record-changed":
        n = record_changed(Path(args.root))
        print(f"· ghi {n} sự kiện")
        sys.exit(0)
```

- [ ] **Step 4: chạy lại — PASS**

Chạy: `python3 harness/scripts/provenance-log.py --self-test`
Mong đợi: PASS thêm 5 dòng `[OK ] ... -> docs.change/code.change/None`.

- [ ] **Step 5: wiring vào `stop.py::regen_docs()` — thêm ngay sau khối `if (wikigraph_on and ...)` (dòng 138, sau `_debounce_mark(root, "wiki-graph")`)**

```python
        # T5 (provenance-log, T-260722-01): phân loại file đổi theo path-prefix, ghi sự kiện
        # artifact-level. Gọi qua subprocess (CLI, không import chéo hooks/ <-> harness/scripts/)
        # — cùng pattern subprocess.run([sys.executable, wg, ...]) đã dùng cho wiki-graph ở trên.
        pl = resolve_tool(root, "harness/scripts/provenance-log.py")
        if pl:
            subprocess.run([sys.executable, pl, "record-changed", "--root", root],
                           cwd=root, capture_output=True, timeout=30)
```

- [ ] **Step 6: verify thật trên repo thật — sửa 1 file code + 1 file wiki, xem phân loại đúng**

```bash
touch /tmp/_t5_verify_marker
echo "// t5 verify" >> harness/scripts/provenance-log.py   # đã có sẵn, chỉ thêm comment vô hại rồi bỏ sau
python3 harness/scripts/provenance-log.py record-changed --root .
grep "harness/scripts/provenance-log.py" harness/metrics/provenance-log.jsonl | tail -1
git checkout -- harness/scripts/provenance-log.py   # bỏ dòng comment thử nghiệm, không commit
```

Mong đợi: dòng cuối có `"topic":"code.change"`, `"path":"harness/scripts/provenance-log.py"`.

- [ ] **Step 7: commit**

```bash
git add harness/scripts/provenance-log.py llmwiki/.claude/hooks/stop.py
git commit -m "feat(provenance-log): T5 — wiring Stop hook, classify_topic theo path-prefix (FR-001)"
```

## Self-review

**Phủ SPEC.** Mọi FR có task nhận: FR-001 (T1 khai file + T5 wiring hook), FR-002/FR-003 (T1), FR-004 (T2), FR-005 (T4), FR-006 (T3), FR-007 (T1 — adapter là chính T1), FR-008 (T1). T6 (v0.3/COULD) loại khỏi PLAN có lý do tường minh (U-05 chưa trả nợ) — không phải bỏ sót, ghi rõ ở đầu file.

**Quét chỗ bỏ ngỏ.** Rà toàn văn, không còn mục nào chỉ mô tả *phải làm gì* mà thiếu *làm thế nào cụ thể* — Task 2-5 đều viết code đầy đủ dù dùng chung file với Task 1 (import/gọi hàm thật, không mô tả suông). Mỗi bước Verify có lệnh chạy chính xác + output mong đợi cụ thể.

**Nhất quán tên-kiểu.** `append_event()`/`read_events()`/`correlate()`/`classify_topic()` là 4 hàm public duy nhất xuyên suốt Task 1-5, không đặt tên khác ở chỗ khác. `EVENTS_PATH_REL` là hằng số path duy nhất (Task 5's `_changed_paths()` không hardcode lại path). `writer_id`/`topic`/`ts_utc`/`git_sha`/`prev`/`h` là bộ field cố định từ Task 1, Task 3/4/5 chỉ thêm field phụ (`ref`, `note`, `path`, `task_id`) không đổi tên field gốc.
