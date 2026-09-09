---
type: draft
title: capability-proof-map-PLAN
status: proposed
timestamp: 2026-07-18
task: T-260718-01
---

# Capability-proof map — PLAN thi hành

**Goal:** CAPABILITIES.md chứng được mỗi năng lực CÒN SỐNG (proof), bêu UNPROVEN + TRÙNG-ỨNG-VIÊN; medic probe `capproof` ratchet chặn nợ mới.
**Architecture:** Toàn bộ tính toán nằm trong `build-capabilities.py` (chỗ đã tự-cộng, travel downstream); medic probe chỉ GỌI nó ra JSON rồi so baseline; guard test fire-drill cả hai chiều. 0 LLM, stdlib-only (parse mechanisms bằng regex như medic đang làm).
**Tech stack:** Python 3 stdlib (re, json, pathlib), bash guard test, khuôn medic probe `(state, detail, fix)`.
**SPEC nguồn:** `wiki/sources/draft/180726-capability-proof-map.md` (đã duyệt 2026-07-18, gate_bd49612032be)

## Origin
- **SPEC:** `wiki/sources/draft/180726-capability-proof-map.md`
- **Commit:** _(verify-before-commit điền)_

## Global constraints

Chép nguyên văn từ SPEC — mọi task ngầm mang theo:

- **ADR-005:** `build-capabilities.py` travel downstream (deploy cạnh hooks, chạy với `--root`); sửa nó phải giữ tương thích downstream — downstream KHÔNG có `harness/tests/` nên proof-resolver phải fail-open thành "không đo được ở downstream", không đỏ oan.
- **Khuôn medic:** probe mới theo đúng khuôn 12 probe sẵn có trong `fdk/tools/medic.py` (tên ngắn, tags, chỉ chẩn đoán không sửa, `--ci` exit 1); medic tự báo nếu probe mới quên hàng rào.
- **Hook 0-token:** toàn bộ resolver + probe là code thuần, 0 LLM.
- **Ponytail:** không đẻ script mới nếu nhét được vào `build-capabilities.py` sẵn có; diff tối thiểu; ratchet baseline là MỘT file JSON.
- **R15:** cấm AI-attribution trong commit; **medic --ci xanh trước push**.
- **KHÔNG tự dedupe** — TRÙNG-ỨNG-VIÊN chỉ báo; dedupe là vòng `/propose` riêng.

## File structure

- Sửa `fdk/tools/build-capabilities.py` (203 dòng) — thêm resolver + 2 section mới + 2 flag CLI; KHÔNG đổi format section sẵn có
- Sửa `fdk/tools/medic.py` — thêm `def p_capproof()` cạnh các probe (sau `p_capsurface`), đăng ký vào `PROBES` (dòng ~291)
- Tạo `harness/metrics/capproof-baseline.json` — chốt nợ tồn (sinh bằng flag, không viết tay)
- Tạo `harness/tests/capproof-test.sh` — guard fire-drill
- Sửa `.github/workflows/harness.yml` — thêm 1 step chạy guard test

### Task 1: Proof-resolver + section UNPROVEN trong `build-capabilities.py`

**Thoả:** FR-001, FR-002, FR-004

**Files:**
- Sửa: `fdk/tools/build-capabilities.py` — thêm hàm sau `first_sentence` (dòng 99-102); gọi trong `build()` (sau đoạn thu `skills`/`rules`/`tools`/`scripts`, trước khi ghép `out`); thêm flag trong `main()` (dòng 171-203)

**Interfaces:**
- Consumes: `skills` list `(name, loop, desc)`, `rules` list `(rid, rname)`, `tools`/`scripts` name-list — đều đã có trong `build()`.
- Produces: `capproof(root) -> dict` schema `capproof/v1`:
  ```json
  {"schema": "capproof/v1", "downstream": false,
   "counts": {"total": 0, "proven": 0, "unproven": 0},
   "items": {"skill:qc-code": {"proof": "harness/tests/...", "via": "tests"}},
   "unproven": ["skill:x"], "dups": [{"a": "skill:unknown", "b": "script:unknown-ledger.py", "why": "name-token: unknown"}]}
  ```
  Task 2 (probe) và Task 4 (dups) đều đứng trên dict này — key dạng `<kind>:<name>` với kind ∈ `skill|rule|tool|script|mech`.

- [ ] **Step 1: viết resolver (thêm sau `first_sentence`, trước `build`)**

```python
PROOF_STOP = {"check", "build", "test", "sync", "run", "skill", "orca", "harness", "code", "wiki"}


def _proof_sources(root: Path):
    """Đọc MỘT LẦN các nguồn bằng chứng; downstream thiếu harness/tests → None (không đo được)."""
    tests_dir = root / "harness" / "tests"
    if not tests_dir.is_dir():
        return None
    tests = {p.name: p.read_text(encoding="utf-8", errors="ignore") for p in sorted(tests_dir.glob("*.*"))}
    doctor = root / "harness" / "scripts" / "harness-doctor.py"
    doctor_txt = doctor.read_text(encoding="utf-8", errors="ignore") if doctor.is_file() else ""
    goldens = ""
    gd = root / "llmwiki" / "wiki" / "sources" / "evals"
    if gd.is_dir():
        goldens = " ".join(p.read_text(encoding="utf-8", errors="ignore") for p in gd.rglob("*.md"))
    medic_txt = (root / "fdk" / "tools" / "medic.py").read_text(encoding="utf-8", errors="ignore") \
        if (root / "fdk" / "tools" / "medic.py").is_file() else ""
    return {"tests": tests, "doctor": doctor_txt, "goldens": goldens, "medic": medic_txt}


def _resolve_one(root: Path, src: dict, kind: str, name: str, body: str = "") -> tuple:
    """(proof, via) — thứ tự tất định, khai-tay thắng suy-diễn. proof=None ⇒ UNPROVEN."""
    m = re.search(r'^proof:\s*(.+?)\s*$', body[:800], re.M)          # 1. frontmatter khai tay
    if m and (root / m.group(1)).exists():
        return m.group(1), "frontmatter"
    if kind == "rule":                                                # 2. rule ↔ harness-doctor
        marker = f"build_{name.lower()}"
        if marker in src["doctor"]:
            return f"harness/scripts/harness-doctor.py:{marker}", "rule-map"
    for tn, tt in src["tests"].items():                               # 3. tên trong harness/tests/
        if name in tt or name.replace(".py", "") in tn:
            return f"harness/tests/{tn}", "tests"
    if kind == "skill" and body:                                      # 4. engine skill bọc có --self-test
        for eng in re.findall(r'harness/scripts/([\w\-]+\.py)', body):
            ep = root / "harness" / "scripts" / eng
            if ep.is_file() and "--self-test" in ep.read_text(encoding="utf-8", errors="ignore"):
                return f"harness/scripts/{eng} --self-test", "selftest"
    if kind in ("script", "tool") and "--self-test" in body:          # 4b. script tự có self-test
        return f"{name} --self-test", "selftest"
    if name.replace(".py", "") in src["goldens"]:                     # 5. golden eval nhắc tên
        return "wiki/sources/evals/*", "golden"
    if kind != "mech" and name.replace(".py", "") in src["medic"]:    # 6. medic probe nhắc tên
        return "fdk/tools/medic.py", "medic-tag"
    return None, "none"
```

- [ ] **Step 2: hàm `capproof(root)` gom mọi capability (đặt ngay sau `_resolve_one`)**

```python
def capproof(root: Path) -> dict:
    src = _proof_sources(root)
    if src is None:
        return {"schema": "capproof/v1", "downstream": True}
    items, descs = {}, {}
    for d in sorted(skills_dir(root).glob("*/")):
        sk = d / "SKILL.md"
        if sk.is_file():
            body = sk.read_text(encoding="utf-8", errors="ignore")
            p, via = _resolve_one(root, src, "skill", d.name, body)
            items[f"skill:{d.name}"] = {"proof": p, "via": via}
            descs[f"skill:{d.name}"] = parse_frontmatter_desc(sk) or ""
    pol = root / "harness" / "poc-vendor-neutral" / "policy.yaml"
    if pol.is_file():
        for rid in re.findall(r"id:\s*(R\d+)", pol.read_text(encoding="utf-8")):
            p, via = _resolve_one(root, src, "rule", rid)
            items[f"rule:{rid}"] = {"proof": p, "via": via}
    for sub, kind in (("fdk/tools", "tool"), ("harness/scripts", "script")):
        for f in sorted((root / sub).glob("*.py")):
            body = f.read_text(encoding="utf-8", errors="ignore")
            p, via = _resolve_one(root, src, kind, f.name, body)
            items[f"{kind}:{f.name}"] = {"proof": p, "via": via}
            descs[f"{kind}:{f.name}"] = (re.search(r'"""(.+?)$', body, re.M) or [None, ""])[1]
    man = root / "harness" / "mechanisms.yaml"
    if man.is_file():
        mt = man.read_text(encoding="utf-8")
        for mid, lp in zip(re.findall(r'^\s*-\s*id:\s*(\S+)', mt, re.M),
                           re.findall(r'^\s*live_probe:\s*(.+?)\s*$', mt, re.M)):
            lpp = root / lp
            body = lpp.read_text(encoding="utf-8", errors="ignore") if lpp.is_file() else ""
            p, via = _resolve_one(root, src, "mech", mid, body)
            items[f"mech:{mid}"] = {"proof": p, "via": via}
    unproven = sorted(k for k, v in items.items() if v["proof"] is None)
    return {"schema": "capproof/v1", "downstream": False,
            "counts": {"total": len(items), "proven": len(items) - len(unproven), "unproven": len(unproven)},
            "items": items, "unproven": unproven, "dups": _dup_candidates(items, descs)}
```

(`_dup_candidates` định nghĩa ở Task 4 — Task 1 chèn tạm `def _dup_candidates(items, descs): return []` một dòng, Task 4 thay thân thật; đây là stub CÓ CHỦ Ý để Task 1 tự chạy được, không phải placeholder bỏ ngỏ.)

- [ ] **Step 3: nối vào `build()` + `main()`**

Trong `build()` — trước dòng `return "\n".join(out) + "\n"`, chỉ nhánh `if repo:`:

```python
    if repo:
        cp = capproof(root)
        if not cp.get("downstream"):
            out.append(f"\n## Proof — năng lực còn sống ({cp['counts']['proven']}/{cp['counts']['total']} có bằng chứng)")
            out.append("Mỗi năng lực map tất định sang bằng chứng chạy được (frontmatter `proof:` > rule-map > tests > self-test > golden > medic). Chi tiết: `build-capabilities.py --capproof-json`.")
            if cp["unproven"]:
                out.append(f"\n## UNPROVEN ({len(cp['unproven'])}) — có mặt nhưng CHƯA chứng được còn sống")
                out += [f"- `{k}` — thêm proof rẻ nhất: test nhắc tên trong harness/tests/, hoặc khai `proof:` trong frontmatter" for k in cp["unproven"]]
            if cp["dups"]:
                out.append(f"\n## TRÙNG-ỨNG-VIÊN ({len(cp['dups'])}) — máy phát hiện, NGƯỜI phán (dedupe = vòng /propose riêng)")
                out += [f"- `{d['a']}` ↔ `{d['b']}` — {d['why']}" for d in cp["dups"]]
```

Trong `main()` — sau khối `--root`, trước `cap = cap_path(ROOT)`:

```python
    if "--capproof-json" in args:
        print(json.dumps(capproof(ROOT), ensure_ascii=False, indent=1)); sys.exit(0)
    if "--write-capproof-baseline" in args:
        cp = capproof(ROOT)
        bl = ROOT / "harness" / "metrics" / "capproof-baseline.json"
        bl.parent.mkdir(parents=True, exist_ok=True)
        bl.write_text(json.dumps({"schema": "capproof-baseline/v1",
                                  "proven": sorted(k for k, v in cp["items"].items() if v["proof"]),
                                  "unproven": cp["unproven"]}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"✓ baseline: {cp['counts']['proven']} proven, {cp['counts']['unproven']} unproven (nợ tồn đã chốt)"); sys.exit(0)
```

(`import json` thêm vào đầu file nếu chưa có.)

- [ ] **Step 4: chạy cho THẤY**

```bash
python3 fdk/tools/build-capabilities.py --capproof-json | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['counts'],'| dups:',len(d.get('dups',[])))"
# Mong đợi: counts in ra, total ≈ 90+18+~55+~20; unproven > 0 (nợ tồn thật)
python3 fdk/tools/build-capabilities.py && rg -c "UNPROVEN" fdk/CAPABILITIES.md
# Mong đợi: CAPABILITIES.md có mục UNPROVEN
python3 fdk/tools/build-capabilities.py --root $(mktemp -d) --capproof-json
# Mong đợi: {"schema": "capproof/v1", "downstream": true} — không crash, không đỏ oan (FR-004)
```

- [ ] **Step 5: commit**

```bash
git add fdk/tools/build-capabilities.py fdk/CAPABILITIES.md
git commit -m "feat(capproof): proof-resolver 6 tang + muc UNPROVEN trong CAPABILITIES (T-260718-01 T1)"
```

### Task 2: medic probe `capproof` (ratchet)

**Thoả:** FR-003

**Files:**
- Sửa: `fdk/tools/medic.py` — thêm `def p_capproof()` ngay trước dòng `PROBES = [` (~291); thêm entry vào list `PROBES`
- Tạo: `harness/metrics/capproof-baseline.json` (bằng flag Task 1, không viết tay)

**Interfaces:**
- Consumes: `build-capabilities.py --capproof-json` (schema `capproof/v1`) + baseline `capproof-baseline/v1` {proven[], unproven[]}.
- Produces: probe `(state, detail, fix)`; fail ⇔ nợ MỚI hoặc TỤT.

- [ ] **Step 1: viết probe**

```python
def p_capproof():
    """Năng lực MỚI vào phải kèm bằng chứng sống; năng lực đã-proven không được tụt.
    Ratchet: nợ tồn trong baseline chỉ đếm, không đỏ (gate cries wolf thì bị tắt)."""
    bc = ROOT / "fdk/tools/build-capabilities.py"
    bl = ROOT / "harness/metrics/capproof-baseline.json"
    if not bc.exists():
        return "skip", "không có build-capabilities.py", ""
    rc, out = sh([PY, str(bc), "--capproof-json"])
    try:
        cp = json.loads(out)
    except Exception:
        return "skip", "capproof-json không parse được", ""
    if cp.get("downstream"):
        return "skip", "downstream: không đo được (không có harness/tests) — by design", ""
    if not bl.exists():
        return ("warn", f"{cp['counts']['unproven']} UNPROVEN, chưa có baseline — chốt nợ tồn đi",
                "python3 fdk/tools/build-capabilities.py --write-capproof-baseline")
    base = json.loads(bl.read_text(encoding="utf-8"))
    known = set(base.get("proven", [])) | set(base.get("unproven", []))
    new_debt = [k for k in cp["unproven"] if k not in known]
    demoted = [k for k in cp["unproven"] if k in set(base.get("proven", []))]
    if new_debt or demoted:
        parts = ([f"{len(new_debt)} năng lực MỚI không proof: {','.join(new_debt[:3])}"] if new_debt else []) \
              + ([f"{len(demoted)} năng lực TỤT (mất proof): {','.join(demoted[:3])}"] if demoted else [])
        return ("fail", " · ".join(parts),
                "thêm test/frontmatter proof: cho từng cái, hoặc chốt có chủ ý: build-capabilities.py --write-capproof-baseline")
    return "ok", (f"{cp['counts']['proven']}/{cp['counts']['total']} proven · nợ tồn {cp['counts']['unproven']}"
                  + (f" · {len(cp.get('dups', []))} trùng-ứng-viên" if cp.get("dups") else "")), ""
```

Entry đăng ký (thêm vào list `PROBES`, sau dòng của `capsurface`):

```python
    ("capproof",  p_capproof,  "capproof proof unproven ratchet dup"),
```

(Nhìn 2 dòng đầu list `PROBES` hiện có để khớp đúng shape tuple — nếu shape là `(name, fn, tags)` thì dùng như trên; nếu có thêm trường, chép theo hàng xóm. `import json` đã có trong medic.)

- [ ] **Step 2: chốt nợ tồn + chạy**

```bash
python3 fdk/tools/build-capabilities.py --write-capproof-baseline
# Mong đợi: "✓ baseline: N proven, M unproven (nợ tồn đã chốt)"
python3 fdk/tools/medic.py capproof
# Mong đợi: ✓ capproof — X/Y proven · nợ tồn M (ok, không fail vì nợ tồn đã trong baseline)
python3 fdk/tools/medic.py --ci; echo "rc=$?"
# Mong đợi: rc=0, 13 probe (12 cũ + capproof)
```

- [ ] **Step 3: commit**

```bash
git add fdk/tools/medic.py harness/metrics/capproof-baseline.json
git commit -m "feat(medic): probe capproof — ratchet no moi/tut do, no ton dem (T-260718-01 T2)"
```

### Task 3: guard test `capproof-test.sh` — fire-drill chính cơ chế

**Thoả:** FR-005

**Files:**
- Tạo: `harness/tests/capproof-test.sh`
- Sửa: `.github/workflows/harness.yml` — thêm step sau step `downstream fire-drill`

**Interfaces:**
- Consumes: `--capproof-json` + `--write-capproof-baseline` (Task 1) + logic new/demoted của probe (Task 2). Sandbox tự dựng skill giả — không đụng baseline thật.
- Produces: exit 0 = mọi chiều đúng; CI step.

- [ ] **Step 1: viết test (khuôn các guard test sẵn có: ok/bad + fire-drill bẩn→đỏ)**

```bash
#!/usr/bin/env bash
# capproof-test — gate bắt "năng lực có mặt mà không chứng được còn sống" PHẢI tự chứng nó chạy.
# 4 chiều: nợ MỚI → đỏ · TỤT → đỏ · nợ tồn trong baseline → xanh · sandbox không đụng đồ thật.
set -u
ROOT="$(cd "${1:-.}" && pwd)"
BC="$ROOT/fdk/tools/build-capabilities.py"
fail=0
ok(){ printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
bad(){ printf '  \033[1;31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

j(){ python3 "$BC" --root "$1" --capproof-json; }

# Sandbox = bản repo tối thiểu: skills/ + harness/tests + policy + scripts đủ cho resolver
SB="$(mktemp -d)"
mkdir -p "$SB/skills/proven-sk" "$SB/skills/orphan-sk" "$SB/harness/tests" \
         "$SB/harness/scripts" "$SB/fdk/tools" "$SB/harness/metrics" "$SB/harness/poc-vendor-neutral"
printf -- '---\nname: proven-sk\ndescription: co test\n---\n' > "$SB/skills/proven-sk/SKILL.md"
printf -- '---\nname: orphan-sk\ndescription: khong co gi\n---\n' > "$SB/skills/orphan-sk/SKILL.md"
printf 'echo proven-sk duoc test o day\n' > "$SB/harness/tests/proven-sk-test.sh"
printf 'rules: []\n' > "$SB/harness/poc-vendor-neutral/policy.yaml"

# 1. resolver phân loại đúng: proven-sk có proof, orphan-sk UNPROVEN
u=$(j "$SB" | python3 -c "import sys,json;print(','.join(json.load(sys.stdin)['unproven']))")
echo "$u" | grep -q "skill:orphan-sk" && ok "orphan-sk bị bêu UNPROVEN" || bad "orphan-sk lọt lưới ($u)"
echo "$u" | grep -q "skill:proven-sk" && bad "proven-sk bị bêu OAN" || ok "proven-sk được nhận proof (tests)"

# 2. baseline chốt nợ → probe-logic xanh (nợ tồn không đỏ)
python3 "$BC" --root "$SB" --write-capproof-baseline >/dev/null
u2=$(j "$SB" | python3 -c "
import sys,json
cp=json.load(sys.stdin); base=json.load(open('$SB/harness/metrics/capproof-baseline.json'))
known=set(base['proven'])|set(base['unproven'])
new=[k for k in cp['unproven'] if k not in known]
dem=[k for k in cp['unproven'] if k in set(base['proven'])]
print('RED' if (new or dem) else 'GREEN')")
[ "$u2" = "GREEN" ] && ok "nợ tồn trong baseline → XANH (ratchet đúng chiều)" || bad "nợ tồn làm đỏ ($u2)"

# 3. thêm capability MỚI không proof → đỏ
mkdir -p "$SB/skills/new-orphan"; printf -- '---\nname: new-orphan\ndescription: x\n---\n' > "$SB/skills/new-orphan/SKILL.md"
u3=$(j "$SB" | python3 -c "
import sys,json
cp=json.load(sys.stdin); base=json.load(open('$SB/harness/metrics/capproof-baseline.json'))
known=set(base['proven'])|set(base['unproven'])
print('RED' if [k for k in cp['unproven'] if k not in known] else 'GREEN')")
[ "$u3" = "RED" ] && ok "năng lực MỚI không proof → ĐỎ" || bad "nợ mới lọt ($u3)"

# 4. xoá proof của cái đã-proven → đỏ (TỤT)
rm "$SB/harness/tests/proven-sk-test.sh"
u4=$(j "$SB" | python3 -c "
import sys,json
cp=json.load(sys.stdin); base=json.load(open('$SB/harness/metrics/capproof-baseline.json'))
print('RED' if [k for k in cp['unproven'] if k in set(base['proven'])] else 'GREEN')")
[ "$u4" = "RED" ] && ok "proof bị xoá → ĐỎ (bắt tụt)" || bad "tụt không bị bắt ($u4)"

# 5. baseline THẬT của repo không bị đụng
git -C "$ROOT" diff --quiet -- harness/metrics/capproof-baseline.json 2>/dev/null \
  && ok "baseline thật nguyên vẹn" || bad "test đã đụng baseline thật!"
rm -rf "$SB"
[ "$fail" -eq 0 ] && { printf '\n\033[1m═══ capproof-test: \033[1;32mPASS\033[0m\033[0m\n'; exit 0; }
printf '\n\033[1m═══ capproof-test: \033[1;31m%d VI PHẠM\033[0m\033[0m\n' "$fail"; exit 1
```

- [ ] **Step 2: chạy + nối CI**

```bash
bash harness/tests/capproof-test.sh .
# Mong đợi: 6 dòng ✓, PASS
```

Thêm vào `.github/workflows/harness.yml` (sau step `downstream fire-drill`):

```yaml
      - name: capproof — checklist năng lực tự soi còn cắn (nợ mới đỏ, nợ tồn đếm)
        run: bash harness/tests/capproof-test.sh .
```

- [ ] **Step 3: commit**

```bash
git add harness/tests/capproof-test.sh .github/workflows/harness.yml
git commit -m "test(capproof): guard fire-drill 4 chieu + CI step (T-260718-01 T3)"
```

### Task 4: giải-cũ-còn-sống + `_dup_candidates` thật

**Thoả:** FR-006, FR-007

**Files:**
- Sửa: `fdk/tools/build-capabilities.py` — thay stub `_dup_candidates` (Task 1 Step 2) bằng thân thật; phần mech đã vào resolver từ Task 1 (FR-006 nằm trong `capproof()` — khối `mechanisms.yaml`)

**Interfaces:**
- Consumes: `items` dict + `descs` dict từ `capproof()` (Task 1).
- Produces: `_dup_candidates(items, descs) -> list[{"a","b","why"}]` — nạp vào key `dups` của schema, hiện ở mục TRÙNG-ỨNG-VIÊN.

- [ ] **Step 1: thân thật của `_dup_candidates`**

```python
def _dup_candidates(items: dict, descs: dict) -> list:
    """Ứng viên trùng — CHỈ BÁO, người phán. Hai tín hiệu tất định:
    (a) chung token tên HIẾM (không nằm trong PROOF_STOP) giữa 2 kind khác nhau;
    (b) desc Jaccard token ≥ 0.5 (cả hai ≥ 5 token)."""
    def toks(s):
        return {t for t in re.findall(r"[a-z]{4,}", (s or "").lower()) if t not in PROOF_STOP}
    names = {k: toks(k.split(":", 1)[1].replace("-", " ").replace(".py", "").replace("_", " ")) for k in items}
    dups, seen = [], set()
    keys = sorted(items)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a.split(":")[0] == b.split(":")[0] == "rule":
                continue
            pair = (a, b)
            if pair in seen:
                continue
            shared = names[a] & names[b]
            if shared and a.split(":")[0] != b.split(":")[0]:
                dups.append({"a": a, "b": b, "why": f"name-token: {sorted(shared)[0]}"}); seen.add(pair); continue
            ta, tb = toks(descs.get(a, "")), toks(descs.get(b, ""))
            if len(ta) >= 5 and len(tb) >= 5:
                jac = len(ta & tb) / len(ta | tb)
                if jac >= 0.5:
                    dups.append({"a": a, "b": b, "why": f"desc-jaccard {jac:.2f}"}); seen.add(pair)
    return dups
```

- [ ] **Step 2: nghiệm thu bằng ca thật (FR-007 chốt cứng)**

```bash
python3 fdk/tools/build-capabilities.py --capproof-json | python3 -c "
import sys,json
d=json.load(sys.stdin)
hit=[x for x in d['dups'] if 'unknown' in x['a']+x['b']]
print('CA HAI SỔ UNKNOWN:', 'BẮT ĐƯỢC' if hit else 'LỌT', hit[:1])"
# Mong đợi: BẮT ĐƯỢC — skill:unknown ↔ script:unknown-ledger.py (name-token: unknown)
# LỌT → chỉnh PROOF_STOP/ngưỡng NGAY trong task này tới khi bắt được (đây là test nghiệm thu của SPEC)
python3 fdk/tools/build-capabilities.py --capproof-json | python3 -c "
import sys,json; d=json.load(sys.stdin)
mechs=[k for k in d['items'] if k.startswith('mech:')]
print(f'mech vào map: {len(mechs)} (mong đợi ~20, FR-006)')"
```

Lưu ý FR-007 chốt "bắt trong lần chạy đầu" với cấu hình cuối cùng của task — chỉnh ngưỡng là một phần của task, không phải lách nghiệm thu. Skill `unknown` là skill GLOBAL (`~/.claude/skills/`) — ở repo framework `skills_dir()` trả `skills/` local; nếu vì vậy `skill:unknown` không có trong items ở repo framework thì ca nghiệm thu thay bằng cặp tương đương trong items thật (vd `tool:unknown-*`/`script:unknown-ledger.py` nếu có, hoặc bổ sung nguồn quét `~/.claude/skills` cho nhánh dups — quyết tại chỗ, ghi vào Origin của commit).

- [ ] **Step 3: regen + medic + commit**

```bash
python3 fdk/tools/build-capabilities.py && rg -c "TRÙNG-ỨNG-VIÊN" fdk/CAPABILITIES.md   # ≥1
python3 fdk/tools/build-capabilities.py --write-capproof-baseline   # dups đổi số lượng item? (không — dups không vào baseline, chỉ unproven; chạy lại để chắc baseline khớp)
python3 fdk/tools/medic.py --ci; echo "rc=$?"                        # rc=0
bash harness/tests/capproof-test.sh .                                # PASS
git add fdk/tools/build-capabilities.py fdk/CAPABILITIES.md harness/metrics/capproof-baseline.json
git commit -m "feat(capproof): dup-candidates + mech qua resolver — giai cu con song, trung bi beu (T-260718-01 T4)"
```

## Self-review

1. **Phủ SPEC:** FR-001/002/004→T1 · FR-003→T2 · FR-005→T3 · FR-006 (mech qua resolver — code nằm ở T1 khối mechanisms, nghiệm thu ở T4 Step 2)+FR-007→T4. Đủ 7 FR (R18 grep các dòng `**Thoả:**`).
2. **Quét placeholder:** stub `_dup_candidates` của T1 là stub CÓ CHỦ Ý được T4 thay thân — khai tường minh trong cả hai task, có test nghiệm thu; mọi bước có lệnh + output mong đợi; không còn token trì hoãn.
3. **Nhất quán tên:** `capproof(root)` / `--capproof-json` / `--write-capproof-baseline` / `capproof-baseline.json` / `p_capproof` / `capproof-test.sh` thống nhất xuyên 4 task; schema `capproof/v1` + `capproof-baseline/v1` khai ở T1 Interfaces, T2/T3 tiêu thụ đúng key (`items`/`unproven`/`proven`/`downstream`/`dups`); `PROOF_STOP` dùng chung resolver + dups.
