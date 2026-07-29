---
type: draft
title: "Graph-engineering gaps — PLAN thi hành"
status: proposed
tags: [plan, graph-engineering, pdf-gap]
timestamp: 2026-07-29
---

# Graph-engineering gaps — PLAN thi hành

**Goal:** đóng các gap ĐÁNG LÀM theo PDF "Graph Engineering" (đối chiếu tại `290726-spec-vs-overstack.md` + trang `llmwiki/html/290726-pdf-gap-overstack.html`): (T1) ratchet theo điểm số cho loop-runner, (T2) edge ID + typed edges cho wiki-graph, (T3) /query trích edge ID, (T4) grounding-feedback schema cho evaluator, (T5) bốn hạn mức budget còn thiếu, (T6) sổ giả thuyết đã bỏ. KHÔNG làm commit-DAG hub và KG extraction/resolution LLM (xem "Ngoài phạm vi" cuối file — chính PDF §VIII.C khuyên đừng khi chưa đau).

**Architecture:** mọi task là NÂNG CẤP TẠI CHỖ trên module sẵn có (loop-runner.py, wiki-graph.py, token-budget.py, provenance-log.py) — không service mới, không dependency mới, giữ nguyên tắc travel-được (git + Python stdlib + hook vendor). Mọi giá trị chưa chắc nằm trong config adapter (`# ASSUMPTION`), đúng /build-now-adapt-later.

**Tech stack:** Python 3 stdlib. Git thao tác qua `subprocess` (pattern sẵn trong `provenance-log.py::_git_sha`). Self-test theo convention `--self-test` assert-based sẵn có ở cả 4 module.

**SPEC nguồn:** `llmwiki/wiki/sources/draft/290726-spec-vs-overstack.md` (gap-analysis 67 mục + mục "Đối chiếu bổ sung với PDF gốc"; duyệt qua chỉ thị "viết plan để implement những phần còn thiếu trong pdf", 2026-07-29). Nhánh làm việc: `graph-engineering` (tách từ `orca` @ `9032ae4`).

## Origin
- **SPEC:** `llmwiki/wiki/sources/draft/290726-spec-vs-overstack.md`
- **PDF:** `~/Downloads/Graph-Engineering-Athropic-Karpathy-Loop.pdf` (§II ratchet, §V grounding + edge citation, §VIII complexity budget, Appendix TABLE VI)
- **Commit:** _(verify-before-commit điền)_
- **Xác nhận thật trước khi viết PLAN:** `grep -nE 'git reset|revert|score|Trial' harness/scripts/loop-runner.py` → 0 kết quả (gốc 1 có thật); `wiki-graph.py` edges là tuple `(src, dst, "wikilink"|"mdlink")` không ID không type (dòng 181); `token-budget.py` budgets chỉ có `per_session_tokens` + `per_task_usd` (dòng 27); frontmatter `relations:` đã được `fdk/tools/build-wiki-graph.py` đọc (derives-from/depends-on/implements) — T2 tái dùng cú pháp này, không phát minh mới.

## Global constraints

- Fail-open: hạ tầng lỗi → exit 0 + cảnh báo; không hook/CLI nào được phá phiên làm việc.
- Không phá backward-compat: mọi cờ CLI mới đều optional; không có cờ thì hành vi cũ giữ nguyên bit-một-bit (self-test cũ phải vẫn PASS).
- Append-only cho mọi sổ sự kiện; không xoá vật lý.
- Mọi ngưỡng chưa calibrate → config adapter kèm `# ASSUMPTION`, KHÔNG hardcode trong engine.
- Reasoning không dispatch ra model rẻ; mọi phần dưới đây là code tất định, 0 token.
- Mirror discipline: sửa `skills/<x>/SKILL.md` thì sửa cả `llmwiki/skills/<loop>/<x>.md` (chạy `python3 harness/scripts/sync-skills.py`), không CI skills-sync đỏ.
- Sau MỖI task: `python3 harness/scripts/fdk-gate.py` + `python3 fdk/tools/medic.py --ci` phải xanh trước khi sang task kế.

## File structure

- Sửa `harness/scripts/loop-runner.py` — thêm ratchet mode (metric + direction + git keep/revert + Trial records).
- Sửa `harness/loop-runner.config.yaml` — block `ratchet:` (adapter, ASSUMPTION values).
- Sửa `harness/scripts/wiki-graph.py` — edge ID ổn định + đọc frontmatter `relations:` thành typed edges + lệnh `edge`/`cite`.
- Sửa `skills/query/SKILL.md` + `llmwiki/skills/wiki-loop/query.md` — bước Evidence trích edge ID.
- Tạo `harness/scripts/grounding-check.py` — validator schema verdict `{decision, claim, reason, required_evidence[]}`.
- Sửa `skills/qc-code/SKILL.md` + `llmwiki/skills/dev-loop/qc-code.md` — verdict JSON theo schema + chạy grounding-check.
- Sửa `harness/scripts/token-budget.py` + `harness/token-budget.config.yaml` — 4 trần mới.
- Sửa `harness/scripts/provenance-log.py` — topic `hypothesis.*` + CLI `post-hypothesis`/`read-hypotheses`.

---

### Task 1: Ratchet theo điểm số cho loop-runner (PDF §II, gốc 1)

**Thoả:** PDF R-1.1 (Trial ghi trước vòng kế), R-1.3 (revert = git reset, không undo tay), R-1.4 (dừng theo budget / N lần không cải thiện)

**Files:**
- Sửa: `harness/scripts/loop-runner.py`
- Sửa: `harness/loop-runner.config.yaml`

**Interfaces:**
- Consumes: `run_loop(...)` hiện có (dòng 172), `DEFAULTS` (dòng 64), `_run_cmd(cmd, cwd)` (dòng 166), run-log JSON `iterations[]` hiện có.
- Produces (dùng bởi Task 4 và mọi caller loop):
  - CLI mới (optional, không có = hành vi cũ): `--metric-cmd CMD` (shell in MỘT số float ở dòng stdout cuối), `--direction {max,min}` (default `max`), `--no-improve-k N` (default 3), `--min-delta F` (default 0.0).
  - Hàm mới: `parse_score(out_tail: str) -> float | None` — lấy float cuối cùng parse được từ output; `git_keep(cwd) -> str` — `git add -A && git commit -m "ratchet keep iter N"` trả HEAD sha; `git_revert_to(sha, cwd) -> None` — `git reset --hard <sha>`.
  - Trial record trong run-log `iterations[]`: thêm fields `{"score": float|None, "commit": str|None, "ratchet": "kept"|"reverted"|"crash"|None}`.
  - Config block mới trong `loop-runner.config.yaml`: `ratchet: {metric_cmd: null, direction: max, no_improve_k: 3, min_delta: 0.0}` — mỗi giá trị kèm `# ASSUMPTION`.

- [ ] **Step 1: self-test scenario trước (RED)** — thêm vào `selftest()` (dòng 374) ba scenario chạy trong temp git repo (`git init` + commit mồi):

```python
def _mk_git_sandbox(tmp):
    subprocess.run(["git", "init", "-q", tmp], check=True)
    (Path(tmp) / "w.txt").write_text("0")
    subprocess.run(["git", "-C", tmp, "add", "-A"], check=True)
    subprocess.run(["git", "-C", tmp, "commit", "-qm", "seed"], check=True)

# scenario ratchet-keep: metric tăng dần → mọi iter "kept", summary kept>=2
# metric_cmd = _py("import pathlib;p=pathlib.Path('n');v=int(p.read_text() or 0)+1;p.write_text(str(v));print(v)")
# scenario ratchet-revert: metric cố định → iter 2+ "reverted" (không vượt min_delta)
# scenario ratchet-crash: metric_cmd exit 1 → "crash" + revert về commit giữ cuối
```

Chạy `python3 harness/scripts/loop-runner.py selftest` → 3 scenario mới FAIL (chưa có code) — đó là RED đúng nghĩa.

- [ ] **Step 2: implement trong `run_loop()`** — sau nhánh verify (không đổi nhánh verify-only), nếu `metric_cmd` được set thì mỗi iteration chạy thêm:

```python
if metric_cmd:
    m_exit, m_out = _run_cmd(metric_cmd, cwd)
    score = parse_score(m_out) if m_exit == 0 else None
    if score is None:
        rec["ratchet"] = "crash"
        if last_kept_sha:
            git_revert_to(last_kept_sha, cwd)
    elif _better(score, best_score, direction, min_delta):
        rec["ratchet"], rec["commit"] = "kept", git_keep(cwd)
        best_score, last_kept_sha, no_improve = score, rec["commit"], 0
    else:
        rec["ratchet"] = "reverted"
        if last_kept_sha:
            git_revert_to(last_kept_sha, cwd)
        no_improve += 1
    rec["score"] = score
    if no_improve_k and no_improve >= no_improve_k:
        verdict, reason = NO_PROGRESS, f"{no_improve} lần liên tiếp không cải thiện metric"
        break
```

`_better(s, best, d, delta)` = `s > best + delta` khi `max`, `s < best - delta` khi `min`; `best_score` khởi tạo bằng lần đo baseline TRƯỚC vòng lặp (R-1.1: Trial baseline cũng ghi vào run-log, `ratchet: "baseline"`).

- [ ] **Step 3: wire CLI + config (GREEN)** — thêm 4 `add_argument` cạnh dòng 481-486, đọc `ratchet:` block trong `load_config()` (dòng 321), CLI override config. Chạy: `python3 harness/scripts/loop-runner.py selftest` → **ALL PASS kể cả 5 scenario cũ**. Cập nhật `loop-runner.config.yaml` với block `ratchet:` + comment ASSUMPTION.

---

### Task 2: Edge ID ổn định + typed edges cho wiki-graph (PDF §V, gốc 2a)

**Thoả:** PDF §V "the answer can cite edge identifiers"; edge types SUPPORTS/CONTRADICTS/SUPERSEDES/DEPENDS_ON của Appendix

**Files:**
- Sửa: `harness/scripts/wiki-graph.py`

**Interfaces:**
- Consumes: `class Graph` (dòng 171, `self.edges: list[(src, dst, type)]`), `build_graph(wiki)` (dòng 188), frontmatter cú pháp `relations:` ĐANG được `fdk/tools/build-wiki-graph.py` đọc — tái dùng y nguyên: `relations: [{rel: derives-from, to: page-x}, ...]` cộng rel mới `supports`, `contradicts`, `supersedes`.
- Produces (dùng bởi Task 3):
  - `edge_id(src: str, dst: str, typ: str) -> str` = `"e:" + hashlib.sha1(f"{src}|{dst}|{typ}".encode()).hexdigest()[:8]` — thuần, ổn định qua các lần build.
  - Edge tuple mở rộng thành 4 phần `(src, dst, typ, eid)`; MỌI chỗ unpack 3 phần hiện có (dòng 294, 391...) sửa theo.
  - Lệnh CLI mới: `edge <eid>` — in `{eid, from, to, type}` hoặc exit 1 nếu không có; `cite <page>` — in mọi cạnh inbound+outbound của trang, mỗi dòng `eid  from -> to  (type)`.
  - `cmd_export` JSON: mỗi edge thêm `"eid"`.

- [ ] **Step 1: test trước** — thêm `--self-test`: dựng wiki tạm 3 trang (`a.md` wikilink tới `b`; `b.md` frontmatter `relations: [{rel: supports, to: a}]`), assert: (1) edges chứa type `supports`; (2) `edge_id` deterministic — gọi 2 lần cùng input ra cùng eid; (3) `cite a` liệt kê đủ 2 cạnh với eid. Chạy → FAIL.
- [ ] **Step 2: implement** — hàm lõi + parse frontmatter relations (KHÔNG cần lib yaml):

```python
import hashlib

def edge_id(src: str, dst: str, typ: str) -> str:
    return "e:" + hashlib.sha1(f"{src}|{dst}|{typ}".encode()).hexdigest()[:8]

_REL_LINE = re.compile(r"-\s*\{\s*rel:\s*([\w-]+)\s*,\s*to:\s*([\w./-]+)\s*\}")
_FM = re.compile(r"^---\n(.*?)\n---", re.S)
ALLOWED_RELS = {"derives-from", "depends-on", "implements",
                "supports", "contradicts", "supersedes"}

def frontmatter_relations(text: str) -> list:
    m = _FM.match(text)
    if not m:
        return []
    return [(rel, to) for rel, to in _REL_LINE.findall(m.group(1))
            if rel in ALLOWED_RELS]
```

Trong `build_graph()` sau vòng wikilink/mdlink: `for rel, to in frontmatter_relations(text): dst = resolve(to); g.edges.append((srel, dst, rel, edge_id(srel, dst, rel)))`. Nâng MỌI consumer unpack 3 phần (dòng 294, 391…) lên 4 phần. Hai lệnh mới:

```python
def cmd_edge(g, eid: str):
    for (s, d, t, e) in g.edges:
        if e == eid:
            print(json.dumps({"eid": e, "from": s, "to": d, "type": t}))
            return 0
    print(f"khong co canh {eid}", file=sys.stderr)
    return 1

def cmd_cite(g, page: str):
    rel = resolve_page(page, g)
    for (s, d, t, e) in g.edges:
        if s == rel or d == rel:
            print(f"{e}  {s} -> {d}  ({t})")
```
- [ ] **Step 3: GREEN + không vỡ ai** — `python3 harness/scripts/wiki-graph.py --self-test` PASS; chạy smoke trên wiki thật: `python3 harness/scripts/wiki-graph.py export --json | python3 -c "import json,sys; d=json.load(sys.stdin); assert all('eid' in e for e in d['edges']); print(len(d['edges']), 'edges OK')"`.

---

### Task 3: /query trích dẫn edge ID (gốc 2b)

**Thoả:** PDF §V query contract bước (7) "attach stable edge identifiers"

**Files:**
- Sửa: `skills/query/SKILL.md`
- Sửa: `llmwiki/skills/wiki-loop/query.md`

**Interfaces:**
- Consumes: `wiki-graph.py cite <page>` (Task 2 Produces).
- Produces: hợp đồng output mới của /query — mục cuối câu trả lời:

```
## Evidence
- e:1a2b3c4d  concepts/log-model -> concepts/provenance  (supports)
- e:9f8e7d6c  sources/adr/ADR-008 -> concepts/wiki-split  (derives-from)
```

- [ ] **Step 1: sửa canonical** — thêm vào `skills/query/SKILL.md` bước sau-tổng-hợp: "Với MỖI trang wiki đã dùng làm căn cứ, chạy `python3 harness/scripts/wiki-graph.py cite <page>`; đính mục `## Evidence` liệt kê eid của các cạnh thật sự chống lưng câu trả lời (không liệt kê cạnh không dùng). Không có cạnh nào → ghi `Evidence: none (page-level only)` — trung thực hơn bịa cạnh."
- [ ] **Step 2: sync mirror + kiểm parity** — `python3 harness/scripts/sync-skills.py` rồi `diff skills/query/SKILL.md llmwiki/skills/wiki-loop/query.md` phần thân phải khớp; chạy `python3 fdk/tools/build-capabilities.py` để CAPABILITIES cập nhật mô tả.

---

### Task 4: Grounding-feedback schema cho evaluator (PDF §V, gốc 4 bước nhỏ)

**Thoả:** PDF §V grounding layer — feedback có cấu trúc `{decision, claim, reason, required_evidence[]}`; "looks good" thành schema-invalid (§4.4 spec)

**Files:**
- Tạo: `harness/scripts/grounding-check.py`
- Sửa: `skills/qc-code/SKILL.md`
- Sửa: `llmwiki/skills/dev-loop/qc-code.md`

**Interfaces:**
- Consumes: JSON verdict do evaluator (agent chạy /qc-code hoặc council judge) tự phát.
- Produces:
  - Schema (điều kiện hard-fail): `decision` ∈ {`approve`, `revise`}; `claim` non-empty str; `reason` non-empty str; `decision == "revise"` ⇒ `required_evidence` là list ≥1 str non-empty; field lạ → warn, không fail (forward-compat).
  - CLI: `python3 harness/scripts/grounding-check.py --check FILE` (hoặc `-` đọc stdin) — exit 0 hợp lệ, exit 2 + liệt kê lỗi từng field nếu không; `--self-test` 6 case (approve hợp lệ; revise hợp lệ; revise thiếu evidence → fail; decision lạ → fail; claim rỗng → fail; "looks good" free-text → fail vì không phải JSON).

- [ ] **Step 1: viết `grounding-check.py` với `--self-test` trước** — module ~90 dòng, thuần stdlib:

```python
REQUIRED = {"decision", "claim", "reason"}
DECISIONS = {"approve", "revise"}

def check_verdict(obj: dict) -> list[str]:
    errs = []
    missing = REQUIRED - set(obj)
    if missing:
        errs.append("thiếu field: " + ", ".join(sorted(missing)))
    if obj.get("decision") not in DECISIONS:
        errs.append("decision phải là approve|revise")
    for k in ("claim", "reason"):
        if not str(obj.get(k, "")).strip():
            errs.append(f"{k} rỗng")
    if obj.get("decision") == "revise":
        ev = obj.get("required_evidence")
        if not (isinstance(ev, list) and ev and all(str(x).strip() for x in ev)):
            errs.append("revise bắt buộc required_evidence[] >= 1 mục non-empty")
    return errs
```

Chạy `python3 harness/scripts/grounding-check.py --self-test` → PASS cả 6 case.

- [ ] **Step 2: wire vào /qc-code** — sửa `skills/qc-code/SKILL.md`: verdict cuối (PASS/CẦN SỬA) phải kèm block JSON theo schema trên (PASS → `decision: approve`; CẦN SỬA → `decision: revise` + `required_evidence` = danh sách bằng chứng cụ thể cần bổ sung, mỗi mục trỏ file:line hoặc test-case); ghi JSON ra `/tmp/qc-verdict.json` rồi chạy `python3 harness/scripts/grounding-check.py --check /tmp/qc-verdict.json` — exit 2 thì verdict CHƯA hợp lệ, phải viết lại (agent không được nộp "nhìn ổn"). Sync mirror như Task 3 Step 2.

---

### Task 5: Bốn hạn mức budget còn thiếu (PDF §VIII.B complexity budget)

**Thoả:** PDF "Every run should declare: maximum model calls, maximum sub-agents, maximum concurrent workers, maximum graph writes"

**Files:**
- Sửa: `harness/scripts/token-budget.py`
- Sửa: `harness/token-budget.config.yaml`

**Interfaces:**
- Consumes: `record()` (dòng 62), `over_budget()` (dòng 101), `load_config()` (dòng 51), metrics JSONL hiện có.
- Produces:
  - Config `budgets:` thêm 4 khoá (mỗi khoá `# ASSUMPTION (not verified)`): `per_session_model_calls: 500`, `per_workflow_subagents: 16`, `max_concurrent_workers: 8`, `per_session_graph_writes: 200`.
  - CLI `record` nhận thêm counters optional: `--calls N`, `--subagents N`, `--workers N`, `--graph-writes N` — cộng dồn per-session y hệt tokens.
  - `over_budget()` trả thêm cờ vượt cho 4 trần; `--report` in 4 cột mới; `check SESSION` exit 2 khi vượt BẤT KỲ trần nào và `mode: block`.

- [ ] **Step 1: self-test case mới trước** — thêm vào `self_test()` (dòng 122): config tạm `per_session_model_calls: 3`, record 2 lần `--calls 2` → session vượt trần calls nhưng KHÔNG vượt tokens; assert `over_budget` báo đúng trần bị vượt và chỉ trần đó. Chạy → FAIL.
- [ ] **Step 2: implement + GREEN** — hằng số counter dùng chung + mở rộng ba hàm:

```python
COUNTERS = {  # cli-flag -> (row key, budget key)
    "calls":        ("calls",        "per_session_model_calls"),
    "subagents":    ("subagents",    "per_workflow_subagents"),
    "workers":      ("workers",      "max_concurrent_workers"),
    "graph-writes": ("graph_writes", "per_session_graph_writes"),
}

# record(): row.update({k: int(extra.get(k, 0)) for k, _ in COUNTERS.values()})
# totals(): agg[key] = agg.get(key, 0) + row.get(key, 0)   # .get -> file JSONL cũ thiếu key vẫn đọc được

def over_budget(sess_row, cfg):
    b = cfg.get("budgets", {})
    over = []
    if b.get("per_session_tokens") and sess_row["tokens"] > b["per_session_tokens"]:
        over.append("per_session_tokens")
    if b.get("per_task_usd") and sess_row["usd"] > b["per_task_usd"]:
        over.append("per_task_usd")
    for key, budget_key in COUNTERS.values():
        cap = b.get(budget_key)
        if cap and sess_row.get(key, 0) > cap:
            over.append(budget_key)
    return over  # [] = trong trần; check SESSION exit 2 khi over và mode == "block"
```

`python3 harness/scripts/token-budget.py --self-test` → ALL PASS (case cũ + mới). Config thêm 4 khoá (mỗi khoá `# ASSUMPTION (not verified)`): `per_session_model_calls: 500`, `per_workflow_subagents: 16`, `max_concurrent_workers: 8`, `per_session_graph_writes: 200`; giữ `mode: warn`.

---

### Task 6: Sổ giả thuyết đã bỏ (PDF §III.E message board)

**Thoả:** PDF "a discarded change may still teach other agents that an idea fails under one condition" — học từ việc đã vứt mà không chép transcript

**Files:**
- Sửa: `harness/scripts/provenance-log.py`

**Interfaces:**
- Consumes: `append_event(root, topic, **fields)` / `read_events(root, topic=...)` hiện có (adapter DUY NHẤT — đúng FR-007 của chính module, không mở đường ghi thứ hai).
- Produces:
  - Topic mới: `hypothesis.posted`, `hypothesis.discarded` — fields `{text: str, ref: str|None}` (`ref` = đường dẫn draft/PLAN/commit liên quan).
  - CLI: `post-hypothesis --text "..." [--discarded] [--ref PATH]` → append_event topic tương ứng; `read-hypotheses [--discarded-only] [--limit N]` → in bảng `ts · writer · status · text · ref`, mới nhất trước.

- [ ] **Step 1: mở rộng `--self-test`** — thêm case: post 2 hypothesis (1 posted, 1 discarded) vào sandbox, `read-hypotheses --discarded-only` trả đúng 1, hash-chain của writer vẫn liền mạch (verify bằng hàm chain-check sẵn có). Chạy → FAIL.
- [ ] **Step 2: implement + GREEN** — hai subcommand mỏng gọi thẳng adapter, không mở đường ghi thứ hai:

```python
def cmd_post_hypothesis(root, text: str, discarded: bool, ref: str | None) -> int:
    topic = "hypothesis.discarded" if discarded else "hypothesis.posted"
    append_event(root, topic, text=text.strip(), ref=ref)  # fail-open sẵn trong append_event
    return 0

def cmd_read_hypotheses(root, discarded_only: bool, limit: int) -> int:
    evs = [e for e in read_events(root)
           if e.get("topic", "").startswith("hypothesis.")]
    if discarded_only:
        evs = [e for e in evs if e["topic"] == "hypothesis.discarded"]
    for e in sorted(evs, key=lambda x: x.get("ts_utc", ""), reverse=True)[:limit]:
        status = e["topic"].split(".", 1)[1]
        print(f"{e.get('ts_utc','')}  {e.get('writer_id','')[:24]:<24}  "
              f"{status:<9}  {e.get('text','')}  {e.get('ref') or ''}")
    return 0

# main(): sub "post-hypothesis" (--text bắt buộc, --discarded flag, --ref optional)
#         sub "read-hypotheses" (--discarded-only flag, --limit default 20)
```

`python3 harness/scripts/provenance-log.py --self-test` ALL PASS. Ghi chú sử dụng 3 dòng vào docstring đầu file (nơi đã liệt kê CLI).

---

---

### Task 7: Commit-DAG hub LOCAL — opt-in, gỡ được sạch (PDF §III, gốc 3)

**Thoả:** PDF §III.C bảy lệnh `push · fetch · log · children · leaves · lineage · diff`; §III.D "the DAG is the graph" (node mang agent/hypothesis/metric/runtime/status); §IX.C nợ đã biết của AgentHub (compaction, reproducibility, indexing) — chặn ngay từ commit đầu, không để lại sau.

**Nguyên tắc cốt lõi (user chỉ định):** T7 **mặc định TẮT**. Hệ chạy y hệt hôm nay khi không bật. Bật/tắt bằng một tham số, gỡ bỏ hoàn toàn bằng một lệnh + xoá một file. Không script nào khác `import hub`, không hook nào tự gọi — dependency một chiều, cắt lúc nào cũng được.

**Vì sao local không cần server:** mọi Orca worktree dùng chung một `.git` object store → commit của agent A tự động thấy được từ agent B, không cần push/fetch qua mạng. "Hub" chỉ còn là ref namespace `refs/hub/*` (ngoài `refs/heads` nên không đụng nhánh, không cần main, không merge queue) + `git notes --ref=hub` cất metadata + một CLI mỏng.

**Files:**
- Tạo: `harness/scripts/hub.py`
- Tạo: `harness/hub.config.yaml`
- Tạo: `llmwiki/wiki/concepts/commit-dag-hub.md`
- Sửa: `harness/scripts/loop-runner.py`
- Sửa: `harness/loop-runner.config.yaml`
- Sửa: `harness/scripts/fdk-gate.py`

**Interfaces:**
- Consumes: `git` qua `subprocess` (pattern `provenance-log.py::_git_sha`); `run_loop()` của loop-runner sau khi Trial có `commit` + `score` (T1 Produces).
- Produces:
  - `hub_push(root, agent, hypothesis, metric, status, commit=None) -> str|None` — tạo `refs/hub/<agent>/<seq>` + notes JSON; trả ref name; **fail-open tuyệt đối** (mọi Exception → trả None, không bao giờ raise vào caller).
  - CLI: `push · log · children · leaves · lineage · diff · prune · purge · --self-test`.
  - Notes JSON (bắt buộc có field môi trường — nợ reproducibility của §IX.C, thêm sau thì thí nghiệm cũ mất môi trường vĩnh viễn): `{agent, hypothesis, metric, status, ts_utc, python, platform, deps_sha}`.
  - Cờ mới loop-runner: `--hub` bật, `--no-hub` tắt (override config); mặc định lấy từ `hub.enabled` trong `loop-runner.config.yaml`, **mặc định `false`**.

- [ ] **Step 1: `hub.py` + `--self-test` trước (RED)** — self-test dựng sandbox git riêng (tái dùng `_mk_git_sandbox` mà T1 đã có trong loop-runner, chép sang cho hub độc lập), assert: push tạo đúng ref + notes đọc lại được; `children` thấy 2 nhánh con từ cùng một cha; `leaves` không kể commit đã có con; `lineage` trả đúng thứ tự tới gốc; `prune` giữ đúng top-K; `purge` xoá sạch `refs/hub/*` **và** `refs/notes/hub` (assert `git for-each-ref refs/hub` rỗng).

```python
HUB_REF_NS = "refs/hub"
NOTES_REF = "refs/notes/hub"

def _env_stamp(root):
    """Môi trường phải cất NGAY từ commit đầu — thêm sau là mất vĩnh viễn (PDF §IX.C)."""
    lock = next((p for p in ("uv.lock", "poetry.lock", "requirements.txt")
                 if (Path(root) / p).exists()), None)
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "deps_sha": hashlib.sha1((Path(root) / lock).read_bytes()).hexdigest()[:12] if lock else None,
    }

def hub_push(root, agent, hypothesis, metric=None, status="kept", commit=None):
    try:
        commit = commit or _git(["rev-parse", "HEAD"], root).stdout.strip()
        seq = len(_git(["for-each-ref", f"{HUB_REF_NS}/{agent}"], root).stdout.splitlines()) + 1
        ref = f"{HUB_REF_NS}/{agent}/{seq:04d}"
        _git(["update-ref", ref, commit], root)
        note = {"agent": agent, "hypothesis": hypothesis, "metric": metric,
                "status": status, "ts_utc": _now_iso(), **_env_stamp(root)}
        _git(["notes", f"--ref={NOTES_REF}", "add", "-f",
              "-m", json.dumps(note, ensure_ascii=False), commit], root)
        return ref
    except Exception:
        return None            # fail-open: hub hỏng KHÔNG được làm gãy ratchet
```

- [ ] **Step 2: bốn truy vấn DAG (GREEN)** — `children` đảo map cha→con từ `git log --all --pretty=%H %P` giới hạn trong tập hub commit; `leaves` = hub commit không là parent của hub commit nào khác (chính là biên chưa khám phá); `lineage` = `git rev-list --topo-order <hash>`; `diff` passthrough `git diff --stat a b`. `log` in bảng ref · agent · metric · status · hypothesis, sort theo metric giảm dần khi có `--by-metric` (trả lời đúng câu hỏi chữ ký của PDF: "kết quả giữ lại nào có metric tốt nhất").
- [ ] **Step 3: kill-switch — `prune` + `purge`** — `prune --keep-top K [--older-than N]` xoá ref ngoài top-K theo metric (chặn nợ "DAG phình vô hạn"); `purge --yes` xoá **toàn bộ** `refs/hub/*` + `refs/notes/hub` rồi in số ref đã xoá. Không có `--yes` thì chỉ in thứ SẼ xoá (dry-run), không đụng gì.
- [ ] **Step 4: wiring opt-in vào loop-runner** — trong `run_loop()`, CHỈ khi `hub_enabled` bật thì sau mỗi Trial gọi:

```python
if hub_enabled and rec.get("ratchet") in ("kept", "reverted"):
    try:
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "hub", pathlib.Path(__file__).parent / "hub.py")
        hub = importlib.util.module_from_spec(spec); spec.loader.exec_module(hub)
        rec["hub_ref"] = hub.hub_push(cwd, agent=hub_agent,
                                      hypothesis=f"iter {it}: {verify_cmd}",
                                      metric=rec.get("score"),
                                      status="kept" if rec["ratchet"] == "kept" else "discarded",
                                      commit=rec.get("commit"))
    except Exception:
        pass                   # hub thiếu/hỏng → loop chạy tiếp như chưa có T7
```

Import động qua đường dẫn, KHÔNG `import hub` ở đầu file — xoá `hub.py` đi thì loop-runner vẫn chạy, đó chính là cơ chế gỡ-được-sạch. Thêm `--hub`/`--no-hub` vào parser; `hub.enabled: false` trong `loop-runner.config.yaml` kèm `# ASSUMPTION`.

- [ ] **Step 5: doc gỡ bỏ + wire gate** — viết `llmwiki/wiki/concepts/commit-dag-hub.md` (frontmatter OKF `type: concept`, mục `## Origin`) gồm: nó giải bài gì · bốn truy vấn với ví dụ chạy thật · **mục "Cách tắt và cách gỡ bỏ hoàn toàn"** ghi rõ ba tầng (tắt bằng config/cờ · xoá dữ liệu bằng `purge --yes` · gỡ code bằng xoá 1 file + 1 block config, kèm câu lệnh `git revert` cho commit T7) · bảng bốn nợ đã biết của §IX.C và cái nào đã chặn. Thêm `python3 harness/scripts/hub.py --self-test` vào chuỗi "BNAL feature self-tests" của `fdk-gate.py`. Nghiệm thu: `python3 harness/scripts/hub.py --self-test` PASS; `python3 harness/scripts/loop-runner.py selftest` vẫn ALL PASS **khi hub tắt**; và sau `purge --yes` thì `git for-each-ref refs/hub` rỗng.

## Thứ tự thi hành & cổng

`T1 → T2 → T3 → T4 → T5 → T6` (T3 phụ thuộc T2; còn lại độc lập — T4/T5/T6 dispatch song song được sau khi T2 xong). Sau mỗi task: `fdk-gate.py` + `medic --ci` xanh rồi mới commit (R6); commit message không ghi công AI (R15).

## Ngoài phạm vi — có trigger tường minh, không phải quên

| Gap PDF | Vì sao KHÔNG làm bây giờ | Trigger mở PLAN riêng |
|---|---|---|
| ~~Commit-DAG hub (§III, gốc 3)~~ | **ĐÃ CHUYỂN THÀNH T7** (2026-07-29) sau khi tìm ra bản local không cần server: `refs/hub/*` + `git notes` + một CLI mỏng, chi phí tụt từ "dựng service" xuống ~250 dòng. Lý do hoãn cũ (YAGNI) được thay bằng **mặc định TẮT + gỡ được sạch** — chi phí giữ nó bằng 0 khi không bật | — |
| KG extraction/resolution bằng LLM (§IV.C) | Chính PDF §VIII.C: đừng xây khi quan hệ cố định/đơn giản, sai số extraction vượt giá trị traversal | failure-flywheel ghi nhận ≥3 lần câu hỏi multi-hop mà wikilink+relations không trả lời được |
| Temporal facts / valid-time cho wiki | SUPERSEDES (rel mới của T2) đủ cho nhu cầu hiện tại; valid-time là schema wiki mới, đụng R9 | Khi có ca thật cần hỏi "điều này đúng vào thời điểm nào" mà git blame không trả lời được |
| Sóng kiểm chứng khác vai (§IX.D) | Cần engine swarm tự sở hữu trước đã — hiện mượn vendor | Khi overstack có primitive dispatch song song của riêng mình |

## Origin (footer)
- **Draft:** `wiki/sources/draft/290726-graph-engineering-PLAN.md`
- **Branch:** `graph-engineering`
- **Date promoted:** _(filled by verify-before-commit)_
