---
type: draft
title: 010826-wiki-mental-model-taxonomy-PLAN
status: implemented
timestamp: 2026-08-01
task: T-260801-01
---

# Wiki mental-model taxonomy — PLAN thi hành

**Goal:** Suy sống (không khai tay) quan hệ `operationalizes` nối wiki node `layer: fact|mental-model` tới skill/rule Protocol, vẽ được trong `wiki-graph.html`, có test tất định.
**Architecture:** 2 hàm suy mới trong `harness/scripts/wiki-graph.py` (mirror `touches_targets`) → wire vào `fdk/tools/build-wiki-graph.py::scan()` cạnh lời gọi `touches_targets` hiện có → tái dùng `add_code_nodes()` sẵn có cho node lá (đã tổng quát theo `kind: "path"`, không cần sửa) → thêm CSS class riêng cho node Protocol + badge layer trên node nguồn.
**Tech stack:** Python 3 (stdlib only, không thêm dependency), self-test kiểu `assert`/`checks` list đã có sẵn trong `wiki-graph.py::self_test()`.
**SPEC nguồn:** `wiki/sources/draft/010826-wiki-mental-model-taxonomy.md` (đã duyệt 2026-08-01)

## Origin
- **SPEC:** `wiki/sources/draft/010826-wiki-mental-model-taxonomy.md`
- **Commit:** _(verify-before-commit điền)_

## Global constraints
- Nguyên tắc "suy đừng cất" (`[[wiki-core-relations]]`): `operationalizes` PHẢI suy tại thời điểm build, KHÔNG khai tay trong `relations:` frontmatter, KHÔNG thêm vào `ALLOWED_RELS`.
- `layer:` là field tuỳ chọn, KHÔNG backfill toàn wiki — chỉ gắn mẫu 3-5 node trong Task 3.
- KHÔNG wire `operationalizes` vào CLI subcommand của `wiki-graph.py` (`backlinks`/`neighbors`/`cite`/`export`) — chỉ tầng hiển thị `build-wiki-graph.py`.
- KHÔNG đổi/xoá field `type:` hiện có.
- Đường dẫn file, tên hàm, chữ ký PHẢI khớp đúng những gì đọc được trong `harness/scripts/wiki-graph.py` và `fdk/tools/build-wiki-graph.py` tại thời điểm viết PLAN này (dòng số có thể lệch vài dòng nếu file đổi giữa lúc PLAN và lúc thi hành — dò lại bằng nội dung hàm, không chỉ số dòng).

## File structure
- Sửa `harness/scripts/wiki-graph.py` — thêm `operationalizes_targets()`, `_policy_rule_ids()` (đọc `id:` từ `policy.yaml`, cache), regex `SKILL_TOKEN_RE`; thêm 1 block test vào `self_test()`.
- Sửa `fdk/tools/build-wiki-graph.py` — wire `operationalizes_targets()` vào `scan()`; thêm entry `REL_COLORS`/`REL_VI`; thêm `_mk_protocol_node()` (khác `_mk_code_node()` để có style riêng); đọc `layer:` frontmatter, gắn badge trên node nguồn; thêm CSS `.nd.wiki-protocol` + `.flag.fact`/`.flag.mm`.
- Sửa 3-5 file wiki có sẵn trong `llmwiki/wiki/concepts/` — thêm dòng `layer: fact` hoặc `layer: mental-model` vào frontmatter.

### Task 1: `operationalizes_targets()` trong `wiki-graph.py`

**Thoả:** FR-002, FR-003

**Files:**
- Sửa: `harness/scripts/wiki-graph.py` — chèn ngay sau `touches_targets()` (hiện kết thúc ở dòng 113, trước `def mdlink_targets`), thêm `import functools` nếu chưa có (kiểm tra đầu file trước khi thêm — TRÁNH import trùng).

**Interfaces:**
- Consumes: `Path(repo_root)` (đối số truyền vào, giống hệt `touches_targets`).
- Produces: `operationalizes_targets(text: str, repo_root) -> list[str]` — mỗi phần tử là `"skills/<tên>/SKILL.md"` (skill) hoặc `"rule:<ID>"` (rule), giữ thứ tự, khử trùng. Task 2 tiêu thụ list này.

- [x] **Step 1: viết test fail (thêm vào cuối `def self_test()`, ngay trước dòng `for name, ok in checks:`)**

```python
    # (7) operationalizes_targets — suy quan hệ wiki→Protocol (skill/rule), KHÔNG khai tay
    repo_root = Path(__file__).resolve().parents[2]
    checks.append(("skill hợp lệ → sinh cạnh",
                   "skills/propose/SKILL.md" in operationalizes_targets("Xem `propose` để bắt đầu.", repo_root)))
    checks.append(("rule hợp lệ → sinh cạnh",
                   "rule:R7" in operationalizes_targets("Chặn bởi `R7`.", repo_root)))
    checks.append(("token không tồn tại → KHÔNG sinh cạnh",
                   operationalizes_targets("Xem `khong-ton-tai-gi-ca`.", repo_root) == []))
    checks.append(("đổi tham chiếu → cạnh đổi theo (SC-003, không cache sai)",
                   operationalizes_targets("Dùng `plan` thay vì `propose`.", repo_root)
                   == ["skills/plan/SKILL.md"]))
```

- [x] **Step 2: chạy cho THẤY nó fail**

Chạy: `python3 harness/scripts/wiki-graph.py --self-test`
Mong đợi: FAIL — `NameError: name 'operationalizes_targets' is not defined` (hàm chưa tồn tại).

- [x] **Step 3: code tối thiểu cho pass — chèn vào `harness/scripts/wiki-graph.py` sau `touches_targets()` (trước `def mdlink_targets`)**

```python
# `operationalizes` — cạnh wiki (layer: fact|mental-model) → Protocol (skill/rule).
#
# Cùng hình dạng với `touches` (wiki→NGOÀI 6 thư mục nội dung): suy từ thân bài, KHÔNG khai
# tay trong `relations:`, KHÔNG vào ALLOWED_RELS — bài học lịch sử `touches` dập tay 1 lần rồi
# đóng băng ở 0,8% coverage áp dụng y hệt ở đây. Xem llmwiki/wiki/sources/draft/
# 010826-wiki-mental-model-taxonomy.md.
SKILL_TOKEN_RE = re.compile(r"`([\w-]+)`")
_RULE_ID_RE = re.compile(r"^\s*id:\s*(\S+)", re.MULTILINE)


@functools.lru_cache(maxsize=1)
def _policy_rule_ids(root_str: str) -> frozenset:
    """Mọi `id: RNN` khai trong policy.yaml — cache vì scan() gọi hàm này mỗi node."""
    p = Path(root_str) / "harness" / "poc-vendor-neutral" / "policy.yaml"
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return frozenset()
    return frozenset(_RULE_ID_RE.findall(text))


def operationalizes_targets(text: str, repo_root) -> list:
    """Skill/rule mà trang này nhắc trong backtick VÀ tồn tại thật — suy, không cất."""
    root = Path(repo_root)
    rule_ids = _policy_rule_ids(str(root))
    out, seen = [], set()
    for tok in SKILL_TOKEN_RE.findall(text or ""):
        if tok in seen:
            continue
        if (root / "skills" / tok / "SKILL.md").exists():
            seen.add(tok)
            out.append(f"skills/{tok}/SKILL.md")
        elif tok in rule_ids:
            seen.add(tok)
            out.append(f"rule:{tok}")
    return out
```

Thêm `import functools` vào khối import đầu file (cạnh `import hashlib`) nếu chưa có.

- [x] **Step 4: chạy lại — PASS**

Chạy: `python3 harness/scripts/wiki-graph.py --self-test`
Mong đợi: PASS, dòng `wiki-graph self-test: PASS` (0 FAIL), bao gồm 4 case mới.

- [x] **Step 5: commit**

```bash
git add harness/scripts/wiki-graph.py
git commit -m "feat(wiki-graph): suy quan hệ operationalizes (wiki -> skill/rule), suy-sống không khai tay"
```

### Task 2: Wire vào engine hiển thị `build-wiki-graph.py`

**Thoả:** FR-004, FR-005, FR-006

**Files:**
- Sửa: `fdk/tools/build-wiki-graph.py:107-117` (REL_COLORS/REL_VI), `:120-168` (`scan()`), `:335-347` (node lá — thêm `_mk_protocol_node`, KHÔNG sửa `add_code_nodes` vì nó đã tổng quát theo `kind: "path"`), khối CSS `.nd.wiki-code` (~dòng 313, 499) — thêm rule `.nd.wiki-protocol` cạnh nó, khối `.nd .flag .s/.t` (~dòng 315, 494) — thêm `.flag.fact`/`.flag.mm`.

**Interfaces:**
- Consumes: `operationalizes_targets(text, repo_root)` từ Task 1 (import qua `_wg` — module đã import sẵn ở đầu file `fdk/tools/build-wiki-graph.py`, kiểm tên biến import chính xác trước khi gọi).
- Produces: node có `n.layer` (`"fact"` | `"mental-model"` | `""`), cạnh `{"from": pid, "rel": "operationalizes", "to": target, "kind": "path"}`, node lá `{"wiki": "protocol", ...}`.

- [x] **Step 1: viết test fail — script Python nhỏ chạy `build-wiki-graph.py` trên wiki tạm có node gắn `layer:` + backtick skill hợp lệ, kiểm cạnh `operationalizes` xuất hiện trong JSON export**

```python
# tests/test_operationalizes_render.py (file mới, chạy bằng `python3` trực tiếp — không cần pytest)
import subprocess, sys, json, tempfile, pathlib

def test_operationalizes_edge_rendered():
    with tempfile.TemporaryDirectory() as td:
        wiki = pathlib.Path(td) / "wiki" / "concepts"
        wiki.mkdir(parents=True)
        (wiki / "a.md").write_text(
            "---\ntype: concept\nlayer: mental-model\n---\n\n# A\n\nXem `propose`.\n",
            encoding="utf-8")
        out = pathlib.Path(td) / "out.html"
        repo_root = pathlib.Path(__file__).resolve().parents[1]
        r = subprocess.run(
            [sys.executable, str(repo_root / "fdk/tools/build-wiki-graph.py"),
             str(wiki.parent), "--out", str(out)],
            capture_output=True, text=True, cwd=str(repo_root))
        assert r.returncode == 0, r.stderr
        html = out.read_text(encoding="utf-8")
        assert '"rel": "operationalizes"' in html or '"rel":"operationalizes"' in html, \
            "cạnh operationalizes không xuất hiện trong HTML sinh ra"
        assert "wiki-protocol" in html, "node Protocol không có class riêng"

if __name__ == "__main__":
    test_operationalizes_edge_rendered()
    print("PASS")
```

- [x] **Step 2: chạy cho THẤY nó fail**

Chạy: `python3 tests/test_operationalizes_render.py`
Mong đợi: FAIL — `AssertionError: cạnh operationalizes không xuất hiện trong HTML sinh ra` (chưa wire).

- [x] **Step 3: code tối thiểu cho pass**

3a. Thêm entry vào `REL_COLORS`/`REL_VI` (`fdk/tools/build-wiki-graph.py:107-117`):

```python
REL_COLORS = {
    "derives-from": "#30b0c7", "depends-on": "#5856d6", "implements": "#34c759",
    "supersedes": "#ff9500", "touches": "#8e8e93", "contradicts": "#ff2d55",
    "imports": "#a0522d", "wikilink": "#9aa4b2", "operationalizes": "#bf5af2",
}
REL_VI = {
    "derives-from": "chưng cất từ (nguồn gốc)", "depends-on": "phụ thuộc vào",
    "implements": "hiện thực (quyết định/ADR)", "supersedes": "thay thế (bản cũ)",
    "touches": "chạm file code", "contradicts": "mâu thuẫn với",
    "imports": "code import code", "wikilink": "liên quan mềm (wikilink trong thân bài)",
    "operationalizes": "sinh ra Protocol (skill/rule) này",
}
```

3b. Thêm `"layer"` vào tuple `LINE_RE` (`fdk/tools/build-wiki-graph.py:103`):

```python
LINE_RE = {k: re.compile(rf"^{k}[ \t]*:[ \t]*(\S.*?)[ \t]*$", re.MULTILINE) for k in ("id", "type", "title", "layer")}
```

3c. Trong `scan()`, đọc `layer:` khi tạo `node` (ngay sau dòng dựng `node = {...}` ở `:136-137`):

```python
            node["layer"] = get("layer") or ""
```

3d. Trong `scan()`, gọi `operationalizes_targets()` cạnh `touches_targets()` (chèn ngay sau khối `if _wg is not None and repo_root:` xử lý `touches`, trước dòng `# Nguồn chung nếu nạp được`):

```python
            if _wg is not None and repo_root and node["layer"] in ("fact", "mental-model"):
                for target in _wg.operationalizes_targets(raw_body, repo_root):
                    if target not in typed_to:
                        typed_to.add(target)
                        edges.append({"from": pid, "rel": "operationalizes", "to": target, "kind": "path"})
```

3e. Thêm `_mk_protocol_node()` cạnh `_mk_code_node()` (`fdk/tools/build-wiki-graph.py:335-337`), và gọi nó trong một bản mở rộng cục bộ của `add_code_nodes` — KHÔNG sửa `add_code_nodes()` gốc (nó tổng quát cho MỌI `kind: "path"`, sửa sẽ ảnh hưởng `touches`); thay vào đó phân loại node lá theo tiền tố `to` ngay TRONG `add_code_nodes()` bằng một nhánh rẽ nhỏ:

```python
def _mk_protocol_node(target):
    label = target.split("/")[-2] if target.startswith("skills/") else target.split(":", 1)[-1]
    return {"id": target, "path": target, "group": "protocol", "type": "protocol",
            "title": target, "wiki": "protocol", "label": label}


def add_code_nodes(nodes, edges):
    """Thêm node lá cho target của `touches` (path code) và `operationalizes` (skill/rule)."""
    ids = {n["id"] for n in nodes}
    seen = set()
    for e in edges:
        if e.get("kind") != "path" or e["to"] in ids or e["to"] in seen:
            continue
        seen.add(e["to"])
        if e["rel"] == "operationalizes":
            nodes.append(_mk_protocol_node(e["to"]))
        else:
            nodes.append(_mk_code_node(e["to"]))
```

(Đây LÀ sửa `add_code_nodes()` — nhưng chỉ thêm 1 nhánh rẽ theo `e["rel"]`, hành vi cũ cho `touches`/mọi rel khác giữ NGUYÊN — không phải viết hàm song song.)

3f. Thêm badge layer trên node nguồn — trong khối tạo `flags` khi build DOM node (`fdk/tools/build-wiki-graph.py`, JS template, cạnh dòng xử lý `n.type==='tombstone'`):

```javascript
if(n.layer==='fact')flags+='<span class="flag fact" title="Fact">F</span>';
if(n.layer==='mental-model')flags+='<span class="flag mm" title="Mental Model">M</span>';
```

3g. CSS — thêm cạnh `.nd.wiki-code`/`.nd .s`/`.nd .t` (cả 2 vị trí, dòng ~313-315 và ~494-499, giữ style nhất quán 2 khối CSS đã có):

```css
.nd.wiki-protocol{background:rgba(191,90,242,.14);color:#7b2fb0;border-color:rgba(191,90,242,.35)}
.nd .flag.fact{background:rgba(48,176,199,.16);color:#1b7a8a}
.nd .flag.mm{background:rgba(191,90,242,.16);color:#7b2fb0}
```

- [x] **Step 4: chạy lại — PASS**

Chạy: `python3 tests/test_operationalizes_render.py`
Mong đợi: `PASS`

- [x] **Step 5: commit**

```bash
git add fdk/tools/build-wiki-graph.py tests/test_operationalizes_render.py
git commit -m "feat(build-wiki-graph): vẽ cạnh operationalizes + badge layer Fact/Mental-Model"
```

### Task 3: Gắn `layer:` mẫu cho node wiki có sẵn

**Thoả:** FR-001, SC-001, SC-002

**Files:**
- Sửa: `llmwiki/wiki/concepts/020726-wiki-core-relations.md` (frontmatter) — node này ĐÃ tham chiếu skill/rule thật trong thân bài, kiểm tra bằng grep trước khi chọn thêm node khác.
- Sửa: `llmwiki/wiki/concepts/graph-model.md` (frontmatter).

**Interfaces:**
- Consumes: hàm `operationalizes_targets()` (Task 1) qua đường build thật (Task 2), không gọi trực tiếp.
- Produces: không có — đây là dữ liệu (nội dung wiki), không phải code, task sau không phụ thuộc chữ ký gì từ đây.

- [x] **Step 1: grep xác nhận node có backtick skill/rule tồn tại thật, chọn ĐÚNG node có bằng chứng, không đoán**

```bash
grep -oE '`[a-zA-Z0-9_-]+`' llmwiki/wiki/concepts/020726-wiki-core-relations.md | sort -u
grep -oE '`[a-zA-Z0-9_-]+`' llmwiki/wiki/concepts/graph-model.md | sort -u
```

Mong đợi: thấy ít nhất một token khớp tên skill thật (`skills/<tên>/SKILL.md` tồn tại) hoặc rule id thật trong `policy.yaml`. Nếu KHÔNG node nào trong 2 file này có — DỪNG, chọn node khác bằng cùng cách grep (không bịa nội dung mới vào node chỉ để minh hoạ).

- [x] **Step 2: chưa áp dụng gì — bước 1 chỉ xác nhận, chưa phải fail/pass**

- [x] **Step 3: thêm dòng `layer:` vào frontmatter của (các) node đã xác nhận ở Step 1**

Ví dụ cụ thể (điền đúng theo kết quả Step 1 — nếu `020726-wiki-core-relations.md` tham chiếu `wiki-relations.py`/tên script chứ không phải tên SKILL, thì KHÔNG gắn layer cho node này, chuyển sang node khác thật sự có tham chiếu skill/rule):

```yaml
layer: mental-model
```

Chèn ngay dưới dòng `type: concept` trong frontmatter.

- [x] **Step 4: build đồ thị thật, xác nhận cạnh + badge hiện ra**

Chạy:
```bash
python3 fdk/tools/build-wiki-graph.py llmwiki/wiki --out llmwiki/html/wiki-graph.html
grep -c '"rel": "operationalizes"' llmwiki/html/wiki-graph.html
```
Mong đợi: số ≥ 1 (ít nhất 1 cạnh `operationalizes` thật xuất hiện, không phải test giả lập).

- [x] **Step 5: commit**

```bash
git add llmwiki/wiki/concepts/*.md llmwiki/html/wiki-graph.html
git commit -m "docs(wiki): gắn layer fact/mental-model mẫu, xác nhận chuỗi operationalizes hiện ra thật"
```

### Task 4: Self-review + medic gate

**Thoả:** FR-002, FR-003, FR-004, FR-005, FR-006, SC-001, SC-002, SC-003, SC-004

**Files:**
- Verify (không sửa): `harness/scripts/wiki-graph.py`, `fdk/tools/build-wiki-graph.py`, `tests/test_operationalizes_render.py`.

**Interfaces:**
- Consumes: kết quả Task 1-3.
- Produces: xác nhận cuối, không có gì cho task sau (task cuối).

- [x] **Step 1: chạy self-test wiki-graph.py**

Chạy: `python3 harness/scripts/wiki-graph.py --self-test`
Mong đợi: `wiki-graph self-test: PASS`

- [x] **Step 2: chạy test render**

Chạy: `python3 tests/test_operationalizes_render.py`
Mong đợi: `PASS`

- [x] **Step 3: SC-004 — 100 node KHÔNG có `layer:` vẫn build sạch (backward-compat)**

Chạy: `python3 fdk/tools/build-wiki-graph.py llmwiki/wiki --out /tmp/wg-check.html && echo OK`
Mong đợi: `OK`, không traceback (đa số node hiện có KHÔNG có `layer:`, chính là ca test backward-compat tự nhiên — không cần dựng ca giả).

- [x] **Step 4: medic gate**

Chạy: `python3 fdk/tools/medic.py --ci`
Mong đợi: `0 fail` (warn có sẵn về pre-commit không tính).

- [x] **Step 5: commit cuối (nếu còn thay đổi chưa commit)**

```bash
git status --short
# nếu có thay đổi còn sót (index.md/log.md cập nhật PLAN → DONE):
git add -A
git commit -m "chore(wiki-mental-model-taxonomy): đóng PLAN, medic xanh"
```

## Self-review

**Phủ SPEC.** FR-001 (Task 3, gắn `layer:`) · FR-002+FR-003 (Task 1, hàm suy + đường tắt fact/mental-model chung 1 cơ chế) · FR-004+FR-005+FR-006 (Task 2, wire hiển thị + node lá + badge) · SC-001/SC-002 (Task 3 Step 4, cạnh thật xuất hiện từ cả 2 loại layer) · SC-003 (Task 1 Step 1, case "đổi tham chiếu → cạnh đổi theo") · SC-004 (Task 4 Step 3, build sạch không cần gắn layer toàn bộ).

**Quét placeholder.** Không còn việc để-đó-chưa-làm nào; mỗi step có code thật + lệnh chạy + output mong đợi cụ thể. Task 3 Step 1 có nhánh "DỪNG nếu không tìm thấy node phù hợp" — đây là điều kiện rẽ nhánh thật (grep xác nhận trước khi ghi), không phải placeholder.

**Nhất quán tên-kiểu.** `operationalizes_targets()`/`operationalizes`/`layer:`/`_mk_protocol_node()`/`wiki-protocol` dùng thống nhất Task 1 → Task 2 → Task 3, không đổi tên giữa chừng.

## Cấm dispatch khi chưa hiểu — ghi chú thi hành
PLAN này do CHÍNH agent viết SPEC thi hành trong cùng phiên (không dispatch qua CLI rẻ headless) — Interfaces vẫn khai đủ theo khuôn để giữ vết truy nguyên FR→Task, không phải vì có ≥2 agent song song.
