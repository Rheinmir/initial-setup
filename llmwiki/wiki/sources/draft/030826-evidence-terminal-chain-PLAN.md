---
type: draft
title: evidence-terminal-chain-PLAN
status: proposed
timestamp: 2026-08-03
task: T-260803-01
r7_meta: true
---

# evidence-terminal-chain — PLAN thi hành

**Goal:** Một luật harness `R19 evidence-terminal` buộc mọi chuỗi kết luận phải chấm dứt ở chứng cứ quan sát được, kèm công tắc bật/tắt ba tầng và bộ test tự chứng minh nó cắn thật.

**Architecture:** Một validator CLI đọc khối `evidence-chain` trong tài liệu, dựng đồ thị có hướng từ trường `because`, duyệt mọi đường từ gốc tới lá, và đòi mọi lá là nút chứng cứ hợp lệ. Logic "một nút có phải điểm cuối hợp lệ không" tách ra một module riêng không có CLI, để `grounding-check.py` gọi lại đúng hàm đó thay vì có bộ luật thứ hai. Công tắc ba tầng nằm ở chính validator, quyết định trước khi đọc file.

**Tech stack:** Python 3 thuần, `pyyaml` (CI đã cài, `harness/validators/okf_frontmatter.py` và `patterns_guard.py` đã dùng), test bằng bash theo khuôn `harness/tests/*-test.sh` cộng `--self-test` trong chính script Python — đúng pattern repo đang có, không thêm pytest.

**SPEC nguồn:** `wiki/sources/draft/030826-evidence-terminal-chain-harness.md` (duyệt 2026-08-03, có bổ sung công tắc bật/tắt cùng ngày)

## Origin

- **SPEC:** `wiki/sources/draft/030826-evidence-terminal-chain-harness.md`
- **Trang seq:** `llmwiki/html/030826-evidence-terminal-chain-seq.html`
- **Task ID:** `T-260803-01`
- **Commit:** _(verify-before-commit điền)_

## Global constraints

Chép nguyên văn từ SPEC. Mỗi task ngầm mang theo toàn bộ mục này; khi dispatch phải bơm nguyên văn section này kèm brief của task.

- **Tất định, 0 token, KHÔNG gọi LLM, chạy được offline.** Tiền lệ chép từ docstring `harness/scripts/grounding-check.py`: *"validator schema cho verdict của evaluator (tất định, 0-token, KHÔNG LLM)"*.
- **Ba mã thoát phân biệt.** `0` = hợp lệ. `2` = đọc được nhưng schema hoặc chuỗi sai. `3` = hạ tầng lỗi, KHÔNG đọc được đầu vào. Tuyệt đối không trả `0` khi không đọc được đầu vào — lý do ghi sẵn trong docstring `grounding-check.py`: *"một cổng chỉ check rc==0 không phân biệt được 'chưa ai chấm' với 'đã chấm PASS' — gate coi như bị bypass bằng cách không sinh output."*
- **Advisory trước, blocking chỉ khi `verified: true`.** Tiền lệ `harness/claim-receipts.config.yaml`: *"strictness: advisory — advisory (warn, exit 0) until resolver is symbol-aware; then 'strict'"*.
- **`medic` probe `coverage` đang đọc `18/18 rule có bite-test`.** Nó regex `def build_(r\d+)` trong `harness/scripts/harness-doctor.py` và so với `id:\s*(R\d+)` trong `policy.yaml`. Thêm `R19` mà thiếu `def build_r19` sẽ tụt xuống `18/19` và medic chuyển sang warn.
- **Cổng `tests-wired` trong `.github/workflows/harness.yml`** duyệt từng `harness/tests/*-test.sh` và `exit 1` nếu tên file không xuất hiện trong workflow.
- **`medic` probe `capproof` đang đọc `212/212 có NEO khai báo`** — năng lực mới phải khai neo, nếu không bị bêu `UNPROVEN`.
- **Luật wiki áp cho chính tài liệu sinh ra:** R2 mọi file wiki phải có `## Origin`; R3 thêm file wiki phải thêm dòng vào `llmwiki/wiki/index.md` với Summary là câu mô tả nội dung thật; R5 file wiki nằm trong subfolder; R1 không bao giờ ghi vào `raw/`.
- **`harness/validators/travel_policy_sync.py` gác hai chiều** — file mới phải khai tầng trong `harness/travel-policy.yaml`.
- **Tài liệu người đọc viết văn xuôi đủ câu** (CLAUDE.md, feedback 2026-06-27) — trang concept và luật chữ không được viết kiểu nén.
- **Validator KHÔNG fetch mạng lúc chạy gate.**

## File structure

- Tạo `harness/validators/evidence_leaf.py` — trách nhiệm duy nhất: trả lời "một nút có phải điểm cuối hợp lệ không" theo từng `kind`, cộng luật ở tầng chuỗi cấm toàn-bộ-lá-là-`parametric`. Không có CLI, không đọc file, để `grounding-check.py` nhập lại được mà không kéo theo tác dụng phụ.
- Tạo `harness/validators/evidence_terminal.py` — trách nhiệm duy nhất: công tắc ba tầng, đọc khối `evidence-chain`, dựng đồ thị, bắt chu trình, duyệt mọi đường gốc-tới-lá, ánh xạ kết quả sang ba mã thoát.
- Tạo `harness/evidence-terminal.config.yaml` — `enabled`, `strictness`, `verified`, cùng ADAPT-CHECKLIST nâng lên strict.
- Tạo `harness/tests/evidence-terminal-test.sh` — fixture xanh, bốn fixture đỏ, và ba ca công tắc.
- Tạo `llmwiki/wiki/concepts/evidence-terminal-chain.md` — trang concept chốt schema, sáu loại điểm cuối, và giới hạn của cơ chế.
- Sửa `harness/scripts/grounding-check.py` — gọi `evidence_leaf.check_leaf` cho từng mục `required_evidence[]`.
- Sửa `harness/scripts/harness-doctor.py` — thêm `def build_r19` làm bite-test.
- Sửa `harness/poc-vendor-neutral/policy.yaml` — khai `R19 evidence-terminal`.
- Sửa `harness/travel-policy.yaml` — cập nhật dòng mô tả `harness/validators/*.py` cho khớp số validator và dải rule mới.
- Sửa `.github/workflows/harness.yml` — thêm step chạy `evidence-terminal-test.sh`.
- Sửa `CLAUDE.md` và `AGENT.md` — luật chữ cho phần chat.

## Định dạng khối `evidence-chain` — hợp đồng chung của mọi task

Khối là một fenced block có info string `evidence-chain`, nội dung là một danh sách YAML. Mọi task đọc hoặc sinh khối này đều dùng đúng định dạng dưới đây.

````
```evidence-chain
- id: C1
  claim: "agent tự dừng giữa việc"
  kind: inference
  because: [C2]
- id: C2
  claim: "lượt bị cắt bởi refusal chèn sẵn, không do model sinh"
  kind: inference
  because: [E1, E2]
- id: E1
  claim: "11 lượt refusal có tổng usage 0 token, 297 lượt thường trung vị 50477"
  kind: observed
  evidence:
    ref: "harness/tests/fixtures/openclaude-usage.json"
- id: E2
  claim: "ngay sau mỗi lượt cắt là entry system subtype=stop_hook_summary"
  kind: observed
  evidence:
    ref: "harness/tests/fixtures/openclaude-usage.json"
```
````

Trường `kind` nhận `inference` cho nút suy luận, hoặc một trong sáu loại chứng cứ `observed`, `tool-record`, `graph-edge`, `web`, `parametric`, `absence`. Nút `inference` bắt buộc có `because` không rỗng. Nút chứng cứ bắt buộc có `evidence` và không được có `because`.

---

### Task 1: Trang concept chốt schema và sáu loại điểm cuối

**Thoả:** FR-001, FR-003

**Files:**
- Tạo: `llmwiki/wiki/concepts/evidence-terminal-chain.md`
- Sửa: `llmwiki/wiki/index.md` (thêm một dòng)
- Sửa: `llmwiki/wiki/log.md` (append)

**Interfaces:**
- Consumes: định dạng khối `evidence-chain` ở mục trên, nguyên văn.
- Produces: văn bản chuẩn mà Task 2, 3, 7 trích lại — tên sáu `kind` và điều kiện của từng loại. Không sinh code.

- [ ] **Step 1: viết trang concept**

Tạo `llmwiki/wiki/concepts/evidence-terminal-chain.md` với frontmatter `type: concept`, và các mục: định nghĩa chuỗi, bảng sáu loại điểm cuối kèm điều kiện, ví dụ xanh và ví dụ đỏ, một mục nói rõ giới hạn, và `## Origin`.

Mục giới hạn phải chứa nguyên văn câu sau, vì đây là chỗ người đọc dễ tưởng cổng mạnh hơn thực tế:

> Validator kiểm được rằng một đường dẫn có resolve trên đĩa hay không. Nó hoàn toàn không kiểm được nội dung file đó có thật sự chống lưng cho mệnh đề hay không. Một nút `observed` trỏ tới một file có thật nhưng không liên quan vẫn qua cổng.

- [ ] **Step 2: chạy validator wiki cho THẤY nó pass**

Chạy: `python3 harness/validators/origin_required.py llmwiki/wiki/concepts/evidence-terminal-chain.md`
Mong đợi: rc=0, không in gì.

Chạy: `python3 harness/validators/okf_frontmatter.py llmwiki/wiki/concepts/evidence-terminal-chain.md`
Mong đợi: rc=0.

- [ ] **Step 3: thêm dòng index và log**

Thêm vào `llmwiki/wiki/index.md` một dòng có Summary là câu mô tả thật:

```
| [evidence-terminal-chain](concepts/evidence-terminal-chain.md) | concept | Schema chuỗi chứng cứ và sáu loại điểm cuối của luật R19 — chuỗi kết luận phải chấm dứt ở thứ xem được, kèm giới hạn "resolve path không đồng nghĩa chống lưng nội dung" |
```

- [ ] **Step 4: chạy R3 index-sync — PASS**

Chạy: `python3 harness/validators/index_sync.py --wiki-dir llmwiki/wiki`
Mong đợi: rc=0.

- [ ] **Step 5: commit**

```bash
git add llmwiki/wiki/concepts/evidence-terminal-chain.md llmwiki/wiki/index.md llmwiki/wiki/log.md
git commit -m "docs(evidence): trang concept schema chuỗi chứng cứ + 6 loại điểm cuối"
```

---

### Task 2: Validator lõi — công tắc, đồ thị, chu trình, ba mã thoát

**Thoả:** FR-002, FR-006, FR-007

Task này là một lát cắt dọc: kết thúc task, chạy được lệnh thật trên một file thật và nhận đúng mã thoát. Nó cài sẵn `observed` làm loại điểm cuối duy nhất để chạy được đầu-cuối; năm loại còn lại do Task 3 thêm vào.

**Files:**
- Tạo: `harness/validators/evidence_terminal.py`
- Tạo: `harness/validators/evidence_leaf.py` (bản tối thiểu, chỉ `observed`)

**Interfaces:**
- Consumes: `bnal_config.load(root, name, fallback)` từ `harness/scripts/bnal_config.py`; `resolve(ref, root)` từ `harness/scripts/claim-receipts.py`.
- Produces: cho Task 3 — `evidence_leaf.check_leaf(node, root, cfg) -> (bool, str)` và `evidence_leaf.EVIDENCE_KINDS`. Cho Task 6 — cùng hai tên đó. Cho Task 9 — `evidence_terminal.switch_state(argv, env, cfg) -> (bool, str)`.

- [ ] **Step 1: viết self-test fail**

Thêm vào cuối `harness/validators/evidence_terminal.py` một hàm `self_test()` với ba ca đầu tiên:

```python
def self_test() -> int:
    fails = []
    ok, why = validate_chain([
        {"id": "C1", "claim": "a", "kind": "inference", "because": ["E1"]},
        {"id": "E1", "claim": "b", "kind": "observed", "evidence": {"ref": "harness/policy.yaml"}},
    ], ROOT_DEFAULT, {})
    if not ok:
        fails.append(f"chuoi hop le bi tu choi: {why}")

    ok, why = validate_chain([
        {"id": "C1", "claim": "a", "kind": "inference", "because": ["C2"]},
        {"id": "C2", "claim": "b", "kind": "inference", "because": []},
    ], ROOT_DEFAULT, {})
    if ok:
        fails.append("la la nut inference ma van pass")

    ok, why = validate_chain([
        {"id": "C1", "claim": "a", "kind": "inference", "because": ["C2"]},
        {"id": "C2", "claim": "b", "kind": "inference", "because": ["C1"]},
    ], ROOT_DEFAULT, {})
    if ok:
        fails.append("chuoi vong tron ma van pass")

    for f in fails:
        print("FAIL:", f)
    print("self-test:", "PASS" if not fails else f"{len(fails)} FAIL")
    return 0 if not fails else 2
```

- [ ] **Step 2: chạy cho THẤY nó fail**

Chạy: `python3 harness/validators/evidence_terminal.py --self-test`
Mong đợi: FAIL — `NameError: name 'validate_chain' is not defined`

- [ ] **Step 3: code tối thiểu cho pass**

Viết phần còn lại của `harness/validators/evidence_terminal.py`:

```python
#!/usr/bin/env python3
"""evidence_terminal — R19: moi duong di tu ket luan xuong la phai ket thuc o nut CHUNG CU.

  --check FILE            doc khoi ```evidence-chain trong FILE, validate. FILE='-' doc stdin.
  --no-evidence-chain     tat luat cho DUNG mot lan chay (uu tien cao nhat).
  --self-test             kiem tra tat dinh, khong doc file ngoai.
  --root DIR              goc repo (mac dinh: suy tu vi tri file nay).

Exit code (BA gia tri PHAN BIET — cong chi coi 0 la "da cham va hop le"):
  0 = chuoi hop le, HOAC luat dang tat (van in mot dong len stderr noi ro dang tat)
  2 = doc duoc nhung chuoi/schema sai
  3 = ha tang loi — KHONG doc duoc FILE. KHONG dung return 0 o day.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bnal_config  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evidence_leaf  # noqa: E402

ROOT_DEFAULT = Path(__file__).resolve().parents[2]
BLOCK_RE = re.compile(r"```evidence-chain\s*\n(.*?)```", re.DOTALL)

_FALLBACK = {"enabled": True, "strictness": "advisory", "verified": False}


def load_cfg(root: Path) -> dict:
    return bnal_config.load(root, "evidence-terminal", _FALLBACK)


def switch_state(argv, env, cfg):
    """Ba tang, uu tien tu HEP toi RONG: co CLI > bien moi truong > file config.
    Tra (enabled, layer). layer noi ro TANG NAO da tat — de thong bao khong mo ho."""
    if "--no-evidence-chain" in argv:
        return False, "co --no-evidence-chain"
    raw = env.get("OVERSTACK_EVIDENCE_TERMINAL")
    if raw is not None and raw.strip().lower() in ("0", "false", "off"):
        return False, "bien moi truong OVERSTACK_EVIDENCE_TERMINAL"
    if not cfg.get("enabled", True):
        return False, "harness/evidence-terminal.config.yaml (enabled: false)"
    return True, ""


def parse_block(text):
    """Tra (nodes, err). Khong co khoi -> (None, None): tai lieu khong khai chuoi, khong phai loi."""
    m = BLOCK_RE.search(text or "")
    if not m:
        return None, None
    try:
        import yaml
        nodes = yaml.safe_load(m.group(1))
    except Exception as e:
        return None, f"khoi evidence-chain khong parse duoc: {e}"
    if not isinstance(nodes, list) or not nodes:
        return None, "khoi evidence-chain phai la mot danh sach khong rong"
    for n in nodes:
        if not isinstance(n, dict) or not n.get("id"):
            return None, f"nut thieu 'id' hoac khong phai mapping: {n!r}"
    return nodes, None


def validate_chain(nodes, root: Path, cfg: dict):
    """Duyet MOI duong tu goc toi la. Tra (ok, ly_do)."""
    by_id = {n["id"]: n for n in nodes}
    targets = {b for n in nodes for b in (n.get("because") or [])}
    roots = [n for n in nodes if n["id"] not in targets] or nodes[:1]
    leaves_seen = []

    def walk(node, path):
        nid = node["id"]
        if nid in path:
            return False, f"chuoi vong tron tai '{nid}': {' -> '.join(path + [nid])}"
        because = node.get("because") or []
        if not because:
            ok, why = evidence_leaf.check_leaf(node, root, cfg)
            if not ok:
                return False, f"la '{nid}' khong phai diem cuoi hop le: {why}"
            leaves_seen.append(node)
            return True, ""
        if node.get("kind") in evidence_leaf.EVIDENCE_KINDS:
            return False, f"nut chung cu '{nid}' khong duoc co 'because'"
        for b in because:
            child = by_id.get(b)
            if child is None:
                return False, f"nut '{nid}' tro toi id khong ton tai: '{b}'"
            ok, why = walk(child, path + [nid])
            if not ok:
                return False, why
        return True, ""

    for r in roots:
        ok, why = walk(r, [])
        if not ok:
            return False, why
    ok, why = evidence_leaf.chain_level_check(leaves_seen)
    if not ok:
        return False, why
    return True, ""


def main() -> None:
    argv = sys.argv[1:]
    root = ROOT_DEFAULT
    if "--root" in argv:
        i = argv.index("--root")
        root = Path(argv[i + 1])
        del argv[i:i + 2]
    cfg = load_cfg(root)

    enabled, layer = switch_state(argv, os.environ, cfg)
    if not enabled:
        print(f"[R19 evidence-terminal] DANG TAT boi {layer} — khong kiem chuoi chung cu",
              file=sys.stderr)
        sys.exit(0)

    if "--self-test" in argv:
        sys.exit(self_test())

    if "--check" not in argv:
        print("usage: evidence_terminal.py --check FILE | --self-test", file=sys.stderr)
        sys.exit(3)
    i = argv.index("--check")
    if i + 1 >= len(argv):
        print("usage: evidence_terminal.py --check FILE", file=sys.stderr)
        sys.exit(3)
    target = argv[i + 1]
    try:
        text = sys.stdin.read() if target == "-" else Path(target).read_text(encoding="utf-8")
    except OSError as e:
        print(f"[R19] KHONG doc duoc dau vao ({e}) — khong ket luan duoc", file=sys.stderr)
        sys.exit(3)

    nodes, err = parse_block(text)
    if err:
        print(f"[R19] {err}", file=sys.stderr)
        sys.exit(2)
    if nodes is None:
        sys.exit(0)

    ok, why = validate_chain(nodes, root, cfg)
    if ok:
        sys.exit(0)
    strict = cfg.get("strictness") == "strict" and cfg.get("verified") is True
    print(f"[R19 evidence-terminal] {why}", file=sys.stderr)
    sys.exit(2 if strict else 0)


if __name__ == "__main__":
    main()
```

Và bản tối thiểu của `harness/validators/evidence_leaf.py`:

```python
#!/usr/bin/env python3
"""evidence_leaf — mot nut co phai DIEM CUOI hop le khong. Khong CLI, khong doc file ngoai:
grounding-check.py nhap lai module nay de dung CHUNG mot bo luat, khong co ban thu hai."""
import importlib.util
from pathlib import Path

EVIDENCE_KINDS = frozenset({
    "observed", "tool-record", "graph-edge", "web", "parametric", "absence",
})

_resolve = None


def _claim_receipts_resolve():
    """claim-receipts.py co DAU GACH NGANG trong ten -> khong import thuong duoc.
    Phai nap qua importlib tu duong dan file."""
    global _resolve
    if _resolve is None:
        p = Path(__file__).resolve().parents[1] / "scripts" / "claim-receipts.py"
        spec = importlib.util.spec_from_file_location("claim_receipts", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _resolve = mod.resolve
    return _resolve


def check_leaf(node, root: Path, cfg: dict):
    """Tra (ok, ly_do). Nut la ma kind khong phai chung cu -> tu choi."""
    kind = node.get("kind")
    if kind not in EVIDENCE_KINDS:
        return False, f"kind='{kind}' khong phai loai chung cu — chuoi ket thuc o mot suy luan"
    ev = node.get("evidence") or {}
    if not isinstance(ev, dict) or not ev:
        return False, f"kind='{kind}' thieu truong 'evidence'"
    if kind == "observed":
        ref = ev.get("ref") or ev.get("cmd")
        if not ref:
            return False, "observed phai co 'ref' (duong dan) hoac 'cmd' (lenh chay lai duoc)"
        if ev.get("ref"):
            path_only = str(ev["ref"]).split(":", 1)[0]
            if not _claim_receipts_resolve()(path_only, root):
                return False, f"observed ref khong resolve tren dia: {ev['ref']}"
        return True, ""
    return True, ""


def chain_level_check(leaves):
    """Luat o TANG CHUOI, khong phai tang nut. Task 3 se cai luat parametric o day."""
    return True, ""
```

- [ ] **Step 4: chạy lại — PASS**

Chạy: `python3 harness/validators/evidence_terminal.py --self-test`
Mong đợi: in `self-test: PASS`, rc=0.

Chạy: `printf 'x\n' | python3 harness/validators/evidence_terminal.py --check -`
Mong đợi: rc=0, không in gì (tài liệu không khai chuỗi thì không phải lỗi).

Chạy: `python3 harness/validators/evidence_terminal.py --check /khong/ton/tai.md`
Mong đợi: rc=3, stderr có `KHONG doc duoc dau vao`.

- [ ] **Step 5: commit**

```bash
git add harness/validators/evidence_terminal.py harness/validators/evidence_leaf.py
git commit -m "feat(R19): validator lõi chuỗi chứng cứ — đồ thị, chu trình, 3 mã thoát"
```

---

### Task 3: Năm loại điểm cuối còn lại và luật tầng chuỗi cho `parametric`

**Thoả:** FR-003, FR-004, FR-005

**Files:**
- Sửa: `harness/validators/evidence_leaf.py` (mở rộng `check_leaf` và `chain_level_check`)

**Interfaces:**
- Consumes: `check_leaf(node, root, cfg)` và `chain_level_check(leaves)` do Task 2 tạo — giữ nguyên chữ ký, chỉ thêm nhánh.
- Produces: cùng hai chữ ký đó, nay phủ đủ sáu `kind`. Task 6 và Task 8 dựa vào bản này.

- [ ] **Step 1: viết self-test fail**

Thêm vào `self_test()` trong `harness/validators/evidence_terminal.py` bốn ca mới:

```python
    ok, why = validate_chain([
        {"id": "C1", "claim": "a", "kind": "inference", "because": ["W1"]},
        {"id": "W1", "claim": "b", "kind": "web",
         "evidence": {"url": "https://example.org/a/b#s3", "accessed": "2026-08-03",
                      "quote": "doan trich nguyen van"}},
    ], ROOT_DEFAULT, {})
    if not ok:
        fails.append(f"web du 3 truong bi tu choi: {why}")

    ok, why = validate_chain([
        {"id": "C1", "claim": "a", "kind": "inference", "because": ["W1"]},
        {"id": "W1", "claim": "b", "kind": "web",
         "evidence": {"url": "https://example.org/a/b#s3", "accessed": "2026-08-03"}},
    ], ROOT_DEFAULT, {})
    if ok:
        fails.append("web thieu 'quote' ma van pass")

    ok, why = validate_chain([
        {"id": "C1", "claim": "a", "kind": "inference", "because": ["P1"]},
        {"id": "P1", "claim": "b", "kind": "parametric",
         "evidence": {"origin": "RFC 6749 muc 4.1", "unverified": True}},
    ], ROOT_DEFAULT, {})
    if ok:
        fails.append("chuoi chi co la parametric ma van pass")

    ok, why = validate_chain([
        {"id": "C1", "claim": "a", "kind": "inference", "because": ["P1", "E1"]},
        {"id": "P1", "claim": "b", "kind": "parametric",
         "evidence": {"origin": "RFC 6749 muc 4.1", "unverified": True}},
        {"id": "E1", "claim": "c", "kind": "observed",
         "evidence": {"ref": "harness/policy.yaml"}},
    ], ROOT_DEFAULT, {})
    if not ok:
        fails.append(f"parametric di kem observed bi tu choi: {why}")
```

- [ ] **Step 2: chạy cho THẤY nó fail**

Chạy: `python3 harness/validators/evidence_terminal.py --self-test`
Mong đợi: FAIL — in `FAIL: web thieu 'quote' ma van pass` và `FAIL: chuoi chi co la parametric ma van pass`, rc=2.

- [ ] **Step 3: code tối thiểu cho pass**

Thay thân `check_leaf` sau nhánh `observed` trong `harness/validators/evidence_leaf.py`:

```python
    if kind == "web":
        url = str(ev.get("url") or "")
        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "web phai co 'url' tuyet doi (http:// hoac https://)"
        if not ev.get("accessed"):
            return False, "web phai co 'accessed' — ngay truy cap"
        if not str(ev.get("quote") or "").strip():
            return False, "web phai co 'quote' — trich nguyen van doan duoc dua vao"
        return True, ""
    if kind == "parametric":
        if not str(ev.get("origin") or "").strip():
            return False, ("parametric phai co 'origin' — kien thuc tu training den tu dau "
                           "(ten chuan/tai lieu/tac gia) de nguoi khac di kiem duoc")
        if ev.get("unverified") is not True:
            return False, "parametric phai mang co 'unverified: true' — no la loai KHONG xem duoc"
        return True, ""
    if kind == "absence":
        if not str(ev.get("cmd") or "").strip():
            return False, "absence phai co 'cmd' — chinh lenh/truy van da chay de tim"
        return True, ""
    if kind in ("tool-record", "graph-edge"):
        if not str(ev.get("id") or "").strip():
            return False, f"{kind} phai co 'id' tro toi mot muc trong so tuong ung"
        return True, ""
    return True, ""
```

Và thay `chain_level_check`:

```python
def chain_level_check(leaves):
    """parametric la loai DUY NHAT khong xem duoc — no khong duoc lam diem cuoi duy nhat
    cua mot chuoi dan toi quyet dinh. Phai nang cap len web/observed hoac di kem loai khac."""
    if not leaves:
        return False, "chuoi khong co la nao — khong cham duoc chung cu"
    if all(n.get("kind") == "parametric" for n in leaves):
        return False, ("moi la deu la 'parametric' — ket luan dang tua hoan toan vao tri nho cua "
                       "model. Nang mot la len 'web' (co link) hoac 'observed' (co file/lenh).")
    return True, ""
```

- [ ] **Step 4: chạy lại — PASS**

Chạy: `python3 harness/validators/evidence_terminal.py --self-test`
Mong đợi: in `self-test: PASS`, rc=0.

- [ ] **Step 5: commit**

```bash
git add harness/validators/evidence_leaf.py harness/validators/evidence_terminal.py
git commit -m "feat(R19): 6 loại điểm cuối — web đòi link+ngày+trích, parametric đòi origin"
```

---

### Task 4: File cấu hình với công tắc và ngưỡng advisory

**Thoả:** FR-010, FR-011

**Files:**
- Tạo: `harness/evidence-terminal.config.yaml`

**Interfaces:**
- Consumes: `bnal_config.load(root, "evidence-terminal", _FALLBACK)` do Task 2 gọi — tên file phải khớp đúng `harness/evidence-terminal.config.yaml`.
- Produces: ba khoá `enabled`, `strictness`, `verified` mà Task 2 và Task 9 đọc.

- [ ] **Step 1: viết file cấu hình**

```yaml
# evidence-terminal (R19) — moi duong di tu ket luan xuong la phai ket thuc o nut CHUNG CU.
# Engine: harness/validators/evidence_terminal.py + harness/validators/evidence_leaf.py

enabled: true                     # cong tac TANG BEN (theo repo). false = tat han luat nay.
                                  # Uu tien: co --no-evidence-chain > env OVERSTACK_EVIDENCE_TERMINAL
                                  # > khoa nay. Tat o bat ky tang nao van IN mot dong len stderr.
strictness: advisory              # ASSUMPTION (not verified) — advisory (canh bao, exit 0) cho toi
                                  # khi do duoc ti le bao oan tren corpus that; roi moi 'strict'.
verified: false                   # ASSUMPTION (not verified) — chuoi chi CHAN khi ca hai:
                                  # strictness: strict VA verified: true.

# ADAPT-CHECKLIST (chot khi co so do that):
#   1. Chay advisory tren corpus llmwiki/wiki/ that, dem so canh bao moi tai lieu.
#   2. Chot nguong "bao oan du thap" cho SC-004 — con so nay CO Y chua dat o SPEC.
#   3. Chay: python3 harness/validators/evidence_terminal.py --self-test  (phai PASS).
#   4. Lat strictness: strict VA verified: true. Chi luc do mot chuoi hong moi CHAN.
```

- [ ] **Step 2: chạy cho THẤY validator đọc được config**

Chạy: `python3 -c "import sys; sys.path.insert(0,'harness/validators'); import evidence_terminal as e; from pathlib import Path; print(e.load_cfg(Path('.')))"`
Mong đợi: in dict có `'enabled': True`, `'strictness': 'advisory'`, `'verified': False`.

- [ ] **Step 3: commit**

```bash
git add harness/evidence-terminal.config.yaml
git commit -m "feat(R19): config advisory + công tắc enabled"
```

---

### Task 5: Khai luật R19 vào `policy.yaml` và xác nhận handler được gọi thật

**Thoả:** FR-010

**Files:**
- Sửa: `harness/poc-vendor-neutral/policy.yaml` (thêm khối mới sau khối `problem_tree_flush` của R17)

**Interfaces:**
- Consumes: đường dẫn `harness/validators/evidence_terminal.py` do Task 2 tạo.
- Produces: id `R19` mà Task 8 (`def build_r19`) và `medic` probe `coverage` grep tới.

- [ ] **Step 1: thêm khối luật**

Thêm vào `harness/poc-vendor-neutral/policy.yaml`:

```yaml
  evidence_terminal:
    id: R19
    name: evidence-terminal
    kind: content_check
    statement: "Tai lieu mang ket luan co khoi ```evidence-chain PHAI de moi duong di tu goc toi la ket thuc o nut CHUNG CU (observed/tool-record/graph-edge/web/parametric/absence), khong duoc ket thuc o nut suy luan. web doi url tuyet doi + ngay truy cap + trich nguyen van; parametric (kien thuc tu training model) doi origin + co unverified va KHONG duoc la diem cuoi duy nhat."
    enforce_at: [session, repo]
    target_globs: ["**/llmwiki/wiki/**/*.md"]
    when_contains: ["```evidence-chain"]
    handler: "harness/validators/evidence_terminal.py --check FILE. Cong tac 3 tang: co --no-evidence-chain > env OVERSTACK_EVIDENCE_TERMINAL > harness/evidence-terminal.config.yaml (enabled)."
    blocking: false
```

- [ ] **Step 2: chạy cho THẤY policy parse được VÀ id có mặt**

Chạy: `python3 -c "import yaml; d=yaml.safe_load(open('harness/poc-vendor-neutral/policy.yaml')); print('R19' in open('harness/poc-vendor-neutral/policy.yaml').read())"`
Mong đợi: in `True`.

- [ ] **Step 3: xác nhận handler THẬT SỰ được gọi, không chỉ parse được**

Đây là bước chống cổng câm. Tạo một file tạm có khối chuỗi hỏng rồi chạy đúng đường mà `enforce_at` khai:

```bash
mkdir -p /tmp/r19check && cat > /tmp/r19check/bad.md <<'EOF'
# test
```evidence-chain
- id: C1
  claim: "a"
  kind: inference
  because: [C2]
- id: C2
  claim: "b"
  kind: inference
  because: []
```
EOF
python3 harness/validators/evidence_terminal.py --check /tmp/r19check/bad.md; echo "rc=$?"
```

Mong đợi: stderr in `[R19 evidence-terminal] la 'C2' khong phai diem cuoi hop le`, rc=0 (vì đang advisory).

- [ ] **Step 4: commit**

```bash
git add harness/poc-vendor-neutral/policy.yaml
git commit -m "feat(R19): khai luật evidence-terminal vào policy (advisory)"
```

---

### Task 6: Nối `grounding-check.py` dùng chung luật điểm cuối

**Thoả:** FR-008

**Files:**
- Sửa: `harness/scripts/grounding-check.py`

**Interfaces:**
- Consumes: `evidence_leaf.check_leaf(node, root, cfg)` từ Task 3 — chữ ký nguyên vẹn.
- Produces: không đổi API ngoài; ba mã thoát cũ giữ nguyên ý nghĩa.

- [ ] **Step 1: map caller trước khi sửa**

Chạy: `grep -rn "grounding-check" --include="*.py" --include="*.sh" --include="*.yaml" --include="*.md" . | grep -v "^./.openclaude/"`
Mong đợi: in ra danh sách nơi gọi. Đọc từng chỗ, xác nhận không nơi nào phụ thuộc vào việc `required_evidence[]` được chấp nhận vô điều kiện.

- [ ] **Step 2: viết self-test fail**

Thêm vào `self_test()` của `harness/scripts/grounding-check.py`:

```python
    bad = {"decision": "revise", "claim": "x", "reason": "y",
           "required_evidence": ["vi no khong hop ly"]}
    rc = check_verdict(bad)
    if rc == 0:
        fails.append("required_evidence la mot suy luan tran ma van pass")

    good = {"decision": "revise", "claim": "x", "reason": "y",
            "required_evidence": [{"kind": "observed",
                                   "evidence": {"ref": "harness/policy.yaml"}}]}
    if check_verdict(good) != 0:
        fails.append("required_evidence dung dinh dang diem cuoi bi tu choi")
```

- [ ] **Step 3: chạy cho THẤY nó fail**

Chạy: `python3 harness/scripts/grounding-check.py --self-test`
Mong đợi: FAIL — in `FAIL: required_evidence la mot suy luan tran ma van pass`, rc=2.

- [ ] **Step 4: code tối thiểu cho pass**

Trong `harness/scripts/grounding-check.py`, thêm import và nhánh kiểm. Mục dạng chuỗi trần được coi là chưa khai loại, nên không phải điểm cuối:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "validators"))
import evidence_leaf  # noqa: E402

_ROOT = Path(__file__).resolve().parents[2]


def _evidence_items_ok(items):
    """Moi muc trong required_evidence[] phai la mot DIEM CUOI, khong phai mot suy luan nua.
    Dung CHUNG evidence_leaf voi R19 — khong co bo luat thu hai."""
    for it in items:
        if not isinstance(it, dict):
            return False, (f"muc required_evidence la chuoi tran ({it!r}) — phai khai "
                           "{{kind, evidence}}, xem R19 evidence-terminal")
        ok, why = evidence_leaf.check_leaf(it, _ROOT, {})
        if not ok:
            return False, f"muc required_evidence khong phai diem cuoi: {why}"
    return True, ""
```

Rồi trong hàm kiểm verdict, ngay sau chỗ đã xác nhận `required_evidence` là list không rỗng, chèn:

```python
        ok, why = _evidence_items_ok(verdict["required_evidence"])
        if not ok:
            print(f"[grounding-check] {why}", file=sys.stderr)
            return 2
```

- [ ] **Step 5: chạy lại — PASS, và ba mã thoát cũ không đổi**

Chạy: `python3 harness/scripts/grounding-check.py --self-test`
Mong đợi: in `PASS`, rc=0.

Chạy: `python3 harness/scripts/grounding-check.py --check /khong/ton/tai.json; echo "rc=$?"`
Mong đợi: rc=3 — giữ nguyên ý nghĩa cũ "không đọc được".

- [ ] **Step 6: commit**

```bash
git add harness/scripts/grounding-check.py
git commit -m "feat(R19): grounding-check dùng chung luật điểm cuối với evidence-terminal"
```

---

### Task 7: Luật chữ cho phần chat

**Thoả:** FR-009

**Files:**
- Sửa: `./CLAUDE.md` (thêm một mục sau mục "5-Why")
- Sửa: `./AGENT.md` (thêm cùng nội dung — `harness/validators/agent_claude_parity.py` gác hai file khớp nhau)

**Interfaces:**
- Consumes: tên sáu `kind` và điều kiện từng loại, chốt ở Task 1 và cài ở Task 3 — phải khớp từng chữ.
- Produces: không sinh code.

- [ ] **Step 1: viết mục luật vào `CLAUDE.md`**

Thêm mục sau, đặt ngay sau mục "5-Why":

```markdown
## Chứng cứ — chuỗi lập luận phải chấm dứt ở thứ XEM ĐƯỢC

Được phép lập luận, nhưng cuối mỗi chuỗi phải là chứng cứ mở ra xem được, không phải một lập luận
nữa. Chuỗi `A vì B vì chứng cứ C` là xong; chuỗi `A vì B vì C` mà C lại là suy luận thì chưa xong —
phải khai tiếp C dựa trên cái gì cho tới khi chạm điểm cuối.

Sáu loại được tính là điểm cuối:
- `observed` — đường dẫn `file:line` mở ra được, hoặc lệnh chạy lại được kèm output.
- `tool-record` — id một mục trong provenance-log / events.jsonl / ledger.
- `graph-edge` — eid một cạnh trong wiki graph.
- `web` — dữ liệu tìm trên mạng: phải kèm **link tới đúng chỗ tìm được** (không phải trang chủ),
  ngày truy cập, và trích nguyên văn đoạn đã dựa vào.
- `parametric` — kiến thức từ **training của model**: phải tự khai đúng là loại này, **chỉ rõ nó ở
  đâu ra** (tên chuẩn, tài liệu, tác giả), và nói rõ là chưa kiểm chứng. KHÔNG được là điểm cuối duy
  nhất của một kết luận dùng để quyết định — phải nâng lên `web`/`observed` hoặc đi kèm loại khác.
- `absence` — chính lệnh/truy vấn đã chạy để tìm, kèm output rỗng của nó.

Không được kết luận bằng "rõ ràng là", "ai cũng biết", hay trỏ ngược về một mục lập luận khác trong
cùng câu trả lời. Tài liệu có khối ```evidence-chain thì bị R19 kiểm bằng máy; phần chat không có
validator nào với tới, nên nó là kỷ luật bắt buộc chứ không phải gợi ý.
```

- [ ] **Step 2: chép nguyên văn mục đó sang `AGENT.md`**

Dán đúng khối trên vào `AGENT.md` ở vị trí tương ứng.

- [ ] **Step 3: chạy parity gate — PASS**

Chạy: `python3 harness/validators/agent_claude_parity.py`
Mong đợi: rc=0.

- [ ] **Step 4: commit**

```bash
git add CLAUDE.md AGENT.md
git commit -m "docs(R19): luật chữ chứng cứ cho phần chat (CLAUDE.md + AGENT.md)"
```

---

### Task 8: Bộ test, bite-test R19, travel-policy, và nối CI

**Thoả:** FR-010

**Files:**
- Tạo: `harness/tests/evidence-terminal-test.sh`
- Sửa: `harness/scripts/harness-doctor.py` (thêm `def build_r19`)
- Sửa: `harness/travel-policy.yaml` (dòng mô tả `harness/validators/*.py`)
- Sửa: `.github/workflows/harness.yml` (thêm step)

**Interfaces:**
- Consumes: CLI `evidence_terminal.py --check FILE` và `--self-test` từ Task 2, luật sáu loại từ Task 3.
- Produces: `def build_r19` mà `medic` probe `coverage` grep bằng `def build_(r\d+)`.

- [ ] **Step 1: viết test fail**

Tạo `harness/tests/evidence-terminal-test.sh`:

```bash
#!/usr/bin/env bash
# evidence-terminal-test.sh — R19: chuoi ket luan phai cham dut o chung cu xem duoc.
set -uo pipefail
SRC="${1:?usage: evidence-terminal-test.sh <repo-root>}"
SRC="$(cd "$SRC" && pwd)"
V="$SRC/harness/validators/evidence_terminal.py"
PASS=0; FAIL=0; N=0
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

ok()  { N=$((N+1)); PASS=$((PASS+1)); printf '  \033[1;32mPASS\033[0m  %s\n' "$1"; }
bad() { N=$((N+1)); FAIL=$((FAIL+1)); printf '  \033[1;31mFAIL\033[0m  %s — %s\n' "$1" "$2"; }

chain() { # chain <file> <noi-dung-yaml>
  { printf '# fixture\n\n```evidence-chain\n'; printf '%s\n' "$2"; printf '```\n'; } > "$1"
}
# rc cua validator o che do advisory luon 0; tin hieu that nam o STDERR co dong [R19] hay khong.
flags() { python3 "$V" --check "$1" --root "$SRC" 2>&1 >/dev/null | grep -c '\[R19' || true; }

XANH="$TMP/xanh.md"
chain "$XANH" '- id: C1
  claim: "agent tu dung giua viec"
  kind: inference
  because: [C2]
- id: C2
  claim: "luot bi cat boi refusal chen san"
  kind: inference
  because: [E1]
- id: E1
  claim: "11 luot refusal tong usage 0 token"
  kind: observed
  evidence:
    ref: "harness/policy.yaml"'
[ "$(flags "$XANH")" = "0" ] && ok "fixture XANH: chuoi cham chung cu → khong bi bat" \
  || bad "fixture XANH" "bi bat nham"

declare -a NAMES=("ket thuc bang suy luan" "chuoi vong tron" "web thieu link/trich" "parametric don doc")
declare -a BODIES=(
'- id: C1
  claim: "a"
  kind: inference
  because: [C2]
- id: C2
  claim: "b"
  kind: inference
  because: []'
'- id: C1
  claim: "a"
  kind: inference
  because: [C2]
- id: C2
  claim: "b"
  kind: inference
  because: [C1]'
'- id: C1
  claim: "a"
  kind: inference
  because: [W1]
- id: W1
  claim: "b"
  kind: web
  evidence:
    url: "https://example.org/a"
    accessed: "2026-08-03"'
'- id: C1
  claim: "a"
  kind: inference
  because: [P1]
- id: P1
  claim: "b"
  kind: parametric
  evidence:
    origin: "RFC 6749 muc 4.1"
    unverified: true'
)
for i in "${!NAMES[@]}"; do
  f="$TMP/do-$i.md"; chain "$f" "${BODIES[$i]}"
  [ "$(flags "$f")" -ge 1 ] && ok "fixture DO: ${NAMES[$i]} → bi bat" \
    || bad "fixture DO: ${NAMES[$i]}" "LOT — validator khong bat"
done

# --- cong tac 3 tang (khuon ge-killswitch-test.sh: cong tac co THAT + co de duoc config) ---
DO0="$TMP/do-0.md"
out=$(python3 "$V" --check "$DO0" --root "$SRC" --no-evidence-chain 2>&1 >/dev/null)
{ [ "$(printf '%s' "$out" | grep -c 'DANG TAT')" -ge 1 ] \
  && [ "$(printf '%s' "$out" | grep -c '\[R19 evidence-terminal\] la ')" = "0" ]; } \
  && ok "cong tac: co --no-evidence-chain tat luat + VAN bao dang tat" \
  || bad "cong tac co CLI" "khong tat, hoac tat im lang"

out=$(OVERSTACK_EVIDENCE_TERMINAL=0 python3 "$V" --check "$DO0" --root "$SRC" 2>&1 >/dev/null)
[ "$(printf '%s' "$out" | grep -c 'OVERSTACK_EVIDENCE_TERMINAL')" -ge 1 ] \
  && ok "cong tac: env tat luat + bao dung TANG da tat" \
  || bad "cong tac env" "khong tat hoac khong noi ro tang"

[ "$(flags "$DO0")" -ge 1 ] \
  && ok "cong tac co THAT: khong tat thi luat van bat (khong phai khoa trang tri)" \
  || bad "cong tac co that" "luat khong bat ke ca khi dang bat"

printf '\n%d/%d pass\n' "$PASS" "$N"
[ "$FAIL" -eq 0 ] || exit 2
```

- [ ] **Step 2: chạy đối chứng — mỗi fixture đỏ phải ĐỎ với validator CHƯA vá**

Đây là bước chống test-giả. Tạm thời vô hiệu luật tầng chuỗi rồi chạy, để chứng minh fixture đỏ thật sự nhờ luật mới mà đỏ chứ không đỏ vì lý do khác:

```bash
cp harness/validators/evidence_leaf.py /tmp/evidence_leaf.bak
python3 - <<'PY'
import pathlib
p = pathlib.Path("harness/validators/evidence_leaf.py")
s = p.read_text()
s = s.replace('    if all(n.get("kind") == "parametric" for n in leaves):',
              '    if False:')
p.write_text(s)
PY
bash harness/tests/evidence-terminal-test.sh . ; echo "rc=$?"
```

Mong đợi: FAIL ở đúng dòng `fixture DO: parametric don doc` — chứng tỏ ca đó đang được giữ bởi luật tầng chuỗi chứ không phải may.

Khôi phục: `cp /tmp/evidence_leaf.bak harness/validators/evidence_leaf.py`

- [ ] **Step 3: chạy với bản đầy đủ — PASS**

Chạy: `bash harness/tests/evidence-terminal-test.sh .`
Mong đợi: `8/8 pass`, rc=0.

- [ ] **Step 4: thêm bite-test R19 vào harness-doctor**

Thêm vào `harness/scripts/harness-doctor.py`, theo đúng khuôn các hàm `build_rN` đang có trong file:

```python
def build_r19(tmp):
    """R19 evidence-terminal — chuoi ket thuc o suy luan phai bi bat."""
    bad = tmp / "r19-bad.md"
    bad.write_text(
        "# x\n\n```evidence-chain\n"
        "- id: C1\n  claim: \"a\"\n  kind: inference\n  because: [C2]\n"
        "- id: C2\n  claim: \"b\"\n  kind: inference\n  because: []\n"
        "```\n", encoding="utf-8")
    good = tmp / "r19-good.md"
    good.write_text(
        "# x\n\n```evidence-chain\n"
        "- id: C1\n  claim: \"a\"\n  kind: inference\n  because: [E1]\n"
        "- id: E1\n  claim: \"b\"\n  kind: observed\n"
        "  evidence:\n    ref: \"harness/policy.yaml\"\n"
        "```\n", encoding="utf-8")
    return {"validator": "harness/validators/evidence_terminal.py",
            "bad_args": ["--check", str(bad)], "good_args": ["--check", str(good)],
            "signal": "stderr"}
```

- [ ] **Step 5: chạy medic coverage — phải đọc 19/19**

Chạy: `python3 fdk/tools/medic.py coverage`
Mong đợi: in `✓ coverage   19/19 rule có bite-test`.

- [ ] **Step 6: cập nhật travel-policy cho khớp**

Trong `harness/travel-policy.yaml`, dòng mô tả hiện là `- "harness/validators/*.py — 14 validator ép R1-R17"`. Glob đã phủ file mới, nhưng chữ thì lệch. Sửa thành:

```yaml
    - "harness/validators/*.py — 16 validator ép R1-R19"
```

Chạy: `python3 harness/validators/travel_policy_sync.py`
Mong đợi: rc=0.

- [ ] **Step 7: nối step vào CI**

Thêm vào `.github/workflows/harness.yml`, ngay trước step `tests-wired`:

```yaml
      - name: evidence-terminal — R19 chuỗi kết luận phải chạm chứng cứ + kill-switch
        run: bash harness/tests/evidence-terminal-test.sh .
```

Chạy: `for t in harness/tests/*-test.sh; do grep -q "$(basename "$t")" .github/workflows/harness.yml || echo "chưa wire: $t"; done`
Mong đợi: không in dòng nào về `evidence-terminal-test.sh`.

- [ ] **Step 8: commit**

```bash
git add harness/tests/evidence-terminal-test.sh harness/scripts/harness-doctor.py \
        harness/travel-policy.yaml .github/workflows/harness.yml
git commit -m "test(R19): fixture xanh/đỏ + kill-switch, bite-test, wire CI"
```

---

### Task 9: Công tắc ba tầng — hoàn thiện và chứng minh tắt không im lặng

**Thoả:** FR-011, FR-012

Task 2 đã cài `switch_state` và dòng thông báo. Task này đóng nốt phần còn thiếu: thứ tự ưu tiên phải được chứng minh bằng ca xung đột, và trang concept phải ghi cách tắt.

**Files:**
- Sửa: `harness/validators/evidence_terminal.py` (chỉ thêm self-test, không đổi logic nếu Task 2 đúng)
- Sửa: `llmwiki/wiki/concepts/evidence-terminal-chain.md` (thêm mục "Tắt luật này thế nào")

**Interfaces:**
- Consumes: `switch_state(argv, env, cfg) -> (bool, str)` từ Task 2.
- Produces: không có API mới.

- [ ] **Step 1: viết self-test fail cho thứ tự ưu tiên**

Thêm vào `self_test()` của `harness/validators/evidence_terminal.py`:

```python
    en, layer = switch_state(["--no-evidence-chain"], {"OVERSTACK_EVIDENCE_TERMINAL": "1"},
                             {"enabled": True})
    if en or "no-evidence-chain" not in layer:
        fails.append("co CLI phai THANG env dang bat")

    en, layer = switch_state([], {"OVERSTACK_EVIDENCE_TERMINAL": "0"}, {"enabled": True})
    if en or "OVERSTACK_EVIDENCE_TERMINAL" not in layer:
        fails.append("env=0 phai THANG config enabled: true")

    en, layer = switch_state([], {}, {"enabled": False})
    if en or "config" not in layer:
        fails.append("config enabled: false phai tat duoc")

    en, _ = switch_state([], {}, {"enabled": True})
    if not en:
        fails.append("mac dinh phai la BAT")

    for raw in ("0", "false", "off", "OFF", " False "):
        en, _ = switch_state([], {"OVERSTACK_EVIDENCE_TERMINAL": raw}, {"enabled": True})
        if en:
            fails.append(f"env gia tri tat khong nhan dang: {raw!r}")
```

- [ ] **Step 2: chạy cho THẤY kết quả**

Chạy: `python3 harness/validators/evidence_terminal.py --self-test`
Mong đợi: nếu Task 2 cài đúng thì PASS ngay. Nếu FAIL ở ca `env gia tri tat khong nhan dang: ' False '` thì sửa `switch_state` cho chuẩn hoá `raw.strip().lower()` — đó chính là lỗi mà ca này sinh ra để bắt.

- [ ] **Step 3: viết mục "Tắt luật này thế nào" vào trang concept**

Thêm vào `llmwiki/wiki/concepts/evidence-terminal-chain.md`:

```markdown
## Tắt luật này thế nào

Luật tắt được ở ba tầng, ưu tiên đi từ hẹp tới rộng.

Tắt cho đúng một lần chạy, dùng khi gỡ rối chính validator:

    python3 harness/validators/evidence_terminal.py --check FILE --no-evidence-chain

Tắt cho một phiên hoặc một máy, không đụng file trong repo:

    export OVERSTACK_EVIDENCE_TERMINAL=0

Tắt bền theo repo, cả team dùng chung — đặt `enabled: false` trong
`harness/evidence-terminal.config.yaml`.

Ở cả ba tầng, validator vẫn in một dòng lên `stderr` nói rõ luật đang tắt và tầng nào đã tắt nó.
Đây là chủ ý: một cơ chế im lặng lúc không hoạt động sẽ bị nhầm là đang hoạt động, và người ta yên
tâm về một thứ đã chết. Cổng câm nguy hiểm hơn cổng đỏ.
```

- [ ] **Step 4: chạy toàn bộ test — PASS**

Chạy: `bash harness/tests/evidence-terminal-test.sh .`
Mong đợi: `8/8 pass`, rc=0.

Chạy: `python3 harness/validators/evidence_terminal.py --self-test`
Mong đợi: `self-test: PASS`, rc=0.

- [ ] **Step 5: chạy cổng tổng — PASS**

Chạy: `python3 fdk/tools/medic.py --ci`
Mong đợi: `0 fail`, và dòng `coverage   19/19 rule có bite-test`.

- [ ] **Step 6: commit**

```bash
git add harness/validators/evidence_terminal.py llmwiki/wiki/concepts/evidence-terminal-chain.md
git commit -m "feat(R19): công tắc 3 tầng có thứ tự ưu tiên + tắt vẫn báo, không im lặng"
```

## Self-review

- **Phủ SPEC.** Mười hai yêu cầu đều có task nhận: FR-001 và FR-003 ở Task 1 cùng Task 3; FR-002, FR-006, FR-007 ở Task 2; FR-004 và FR-005 ở Task 3; FR-008 ở Task 6; FR-009 ở Task 7; FR-010 ở Task 4, Task 5, Task 8; FR-011 ở Task 4 và Task 9; FR-012 ở Task 9. Không id nào bị bỏ rơi.
- **Quét placeholder.** Đã rà toàn bộ; mọi bước đổi code đều có code đầy đủ, mọi lệnh đều có output mong đợi. Không có bước nào nói "tương tự task khác" — Task 3 và Task 9 đều chép lại code thật thay vì trỏ ngược.
- **Nhất quán kiểu và tên.** `check_leaf(node, root, cfg)` trả `(bool, str)` dùng y hệt ở Task 2, 3, 6. `chain_level_check(leaves)` trả `(bool, str)` dùng ở Task 2 và 3. `switch_state(argv, env, cfg)` trả `(bool, str)` dùng ở Task 2, 8, 9. `EVIDENCE_KINDS` là `frozenset` dùng ở Task 2 và 3. Tên file `harness/evidence-terminal.config.yaml` khớp đúng tham số `"evidence-terminal"` truyền cho `bnal_config.load`.
- **Một cạm bẫy đã gài sẵn lời giải.** `claim-receipts.py` có dấu gạch ngang trong tên nên `import claim_receipts` sẽ hỏng; Task 2 chỉ rõ phải nạp qua `importlib.util.spec_from_file_location`. Không nói ra thì agent headless chắc chắn vấp.
