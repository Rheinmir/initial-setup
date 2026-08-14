#!/usr/bin/env python3
"""code-complexity: nới Trụ 4 (Quality Gates) — điểm sức khoẻ file TẤT ĐỊNH, KHÔNG-LLM, chỉ Python (`ast`/`tokenize` stdlib).

GỐC: đối chiếu `repowise-dev/repowise` (AGPL-3.0, xem [[repowise]] trong llmwiki) — họ có 49 detector
tree-sitter đa ngôn ngữ, calibrated trên corpus lỗi thật (ROC AUC 0.737/21 repo). Đây là bản
CLEAN-ROOM: đọc README/docstring thuật toán của họ (McCabe CCN, LCOM4, Rabin-Karp clone detection —
đều là kỹ thuật CS công khai), rồi tự viết lại bằng stdlib Python, KHÔNG copy dòng code nào của họ.
Giữ MIT sạch (repo repowise là AGPL-3.0, không được port nguyên code sang project MIT này).

build-now-adapt-later:
  • CONTRACT (dựng now): CCN (McCabe) + NLOC per-function, LCOM4-lite cohesion + god-class per-class,
    duplicate-code (token-chunk hash, KHÔNG phải Rabin-Karp sliding thật — chunk cố định để đơn giản)
    — tất cả bằng `ast`/`tokenize` stdlib, chỉ file .py trong PY_ROOTS.
  • QUARANTINE (unknown, KHÔNG dựng ở đây): trọng số bên dưới là heuristic TỰ CHỌN, KHÔNG calibrated
    trên corpus lỗi thật như repowise — không có claim "defect-validated"/ROC-AUC nào ở tool này.
    ponytail: trọng số cứng trong `_SCORE_WEIGHTS`, nâng cấp khi có nhãn bug-fix thật để calib lại.
  • Đa ngôn ngữ (TS/Go/Rust/...) như repowise KHÔNG dựng — repo này chủ yếu Python, mở rộng khi cần
    (`languages.py`-style bảng ánh xạ AST node cho ngôn ngữ khác, không sửa engine).

Advisory-only (giống `_deep_lint` trong code_health.py) — luôn exit 0, chỉ báo cáo, không chặn commit.
Dùng: code_complexity.py [--root DIR] [--top N] · code_complexity.py --selftest
"""
import argparse
import ast
import hashlib
import sys
import tokenize
from io import StringIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from code_health import PY_ROOTS, SKIP_PARTS, _py_files  # noqa: E402

# Ngưỡng — tự chọn, không calibrated (xem QUARANTINE ở docstring).
CCN_THRESHOLD = 9          # complex_method: McCabe CCN >= ngưỡng này
LARGE_METHOD_NLOC = 60     # large_method: hàm dài hơn ngưỡng (dòng không-rỗng)
GOD_CLASS_NLOC = 200
GOD_CLASS_METHODS = 15
DUP_MIN_FUNC_LINES = 15    # bỏ qua hàm quá nhỏ khi tìm trùng lặp (giảm nhiễu)
DUP_CHUNK_TOKENS = 30      # kích thước khối token so trùng (không phải sliding-window Rabin-Karp thật)

_SCORE_WEIGHTS = {
    "complex_method": -0.5,   # mỗi hàm CCN>=ngưỡng, cap structural
    "large_method": -0.5,
    "god_class": -1.5,
    "low_cohesion": -1.0,
    "duplicate_chunk": -0.3,  # mỗi khối trùng, cap duplication
}
STRUCTURAL_CAP = -2.5
DUPLICATION_CAP = -1.0


def _nloc(lines, start, end):
    """Số dòng không-rỗng trong [start, end] (1-indexed, inclusive)."""
    return sum(1 for ln in lines[start - 1:end] if ln.strip())


def _cyclomatic_complexity(func: ast.AST) -> int:
    """McCabe CCN: 1 + số điểm rẽ nhánh (if/for/while/except/ternary/bool-op/comprehension-if/match-case)."""
    complexity = 1
    for node in ast.walk(func):
        if node is func:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue  # không đếm nhánh của hàm lồng bên trong vào hàm cha
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            complexity += 1 + len(node.ifs)
        elif hasattr(ast, "Match") and isinstance(node, ast.Match):
            complexity += max(len(node.cases) - 1, 0)
    return complexity


def _iter_functions(tree, lines):
    """Yield (qualname, node, ccn, nloc) cho mọi def top-level + method, không đệ quy vào def lồng nhau."""
    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qualname = f"{prefix}{child.name}"
                end = getattr(child, "end_lineno", child.lineno)
                yield qualname, child, _cyclomatic_complexity(child), _nloc(lines, child.lineno, end)
                # không descend tiếp vào thân hàm để tránh đếm hàm lồng 2 lần ở tầng module
            elif isinstance(child, ast.ClassDef):
                yield from walk(child, f"{prefix}{child.name}.")
            else:
                yield from walk(child, prefix)
    yield from walk(tree, "")


def _self_name(args: ast.arguments):
    posonly = getattr(args, "posonlyargs", [])
    all_args = posonly + args.args
    return all_args[0].arg if all_args else None


def _class_cohesion(cls: ast.ClassDef):
    """LCOM4-lite: connected components giữa method dựa trên self.attr chung / gọi lẫn nhau.
    Safety valve: 0 tín hiệu self.attr nào trong cả lớp → lcom4=1 (không báo false-positive)."""
    methods = [n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(methods) < 2:
        return 1, len(methods)

    method_names = {m.name for m in methods}
    attrs_by_method = {}
    calls_by_method = {}
    any_signal = False

    for m in methods:
        self_name = _self_name(m.args)
        attrs, calls = set(), set()
        if self_name:
            for node in ast.walk(m):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == self_name:
                    attrs.add(node.attr)
                    any_signal = True
                    if node.attr in method_names:
                        calls.add(node.attr)
        attrs_by_method[m.name] = attrs
        calls_by_method[m.name] = calls

    if not any_signal:
        return 1, len(methods)

    parent = {m.name: m.name for m in methods}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    names = [m.name for m in methods]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if attrs_by_method[a] & attrs_by_method[b]:
                union(a, b)
            elif b in calls_by_method[a] or a in calls_by_method[b]:
                union(a, b)

    lcom4 = len({find(n) for n in names})
    return lcom4, len(methods)


def _iter_classes(tree, lines):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            end = getattr(node, "end_lineno", node.lineno)
            lcom4, method_count = _class_cohesion(node)
            yield node.name, node, lcom4, method_count, _nloc(lines, node.lineno, end)


def _duplicate_chunks(files):
    """Token-chunk hashing (không phải sliding Rabin-Karp thật — xem docstring). Trả dict hash -> [(file, func, start_line), ...]."""
    chunks = {}
    for path, source, tree, lines in files:
        try:
            tokens = list(tokenize.generate_tokens(StringIO(source).readline))
        except tokenize.TokenizeError:
            continue
        for qualname, func, _ccn, nloc in _iter_functions(tree, lines):
            if nloc < DUP_MIN_FUNC_LINES:
                continue
            start, end = func.lineno, getattr(func, "end_lineno", func.lineno)
            toks = [t.string for t in tokens
                    if start <= t.start[0] <= end
                    and t.type not in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE,
                                       tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER)]
            for i in range(0, len(toks) - DUP_CHUNK_TOKENS + 1, DUP_CHUNK_TOKENS):
                chunk = toks[i:i + DUP_CHUNK_TOKENS]
                h = hashlib.sha1("|".join(chunk).encode()).hexdigest()
                chunks.setdefault(h, []).append((str(path), qualname, start + i))
    return chunks


def analyze(root: Path):
    """Trả dict path -> {score, findings: [str, ...]}."""
    parsed = []
    for path in _py_files(root):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError):
            continue
        parsed.append((path, source, tree, source.splitlines()))

    dup_chunks = _duplicate_chunks(parsed)
    dup_by_file = {}
    for hits in dup_chunks.values():
        distinct_funcs = {(f, q) for f, q, _ln in hits}
        if len(distinct_funcs) < 2:
            continue
        for f, _q, _ln in hits:
            dup_by_file[f] = dup_by_file.get(f, 0) + 1

    report = {}
    for path, _source, tree, lines in parsed:
        key = str(path)
        findings = []
        structural = 0.0
        for qualname, _f, ccn, nloc in _iter_functions(tree, lines):
            if ccn >= CCN_THRESHOLD:
                findings.append(f"complex_method:{qualname} (CCN={ccn})")
                structural += _SCORE_WEIGHTS["complex_method"]
            if nloc >= LARGE_METHOD_NLOC:
                findings.append(f"large_method:{qualname} ({nloc} nloc)")
                structural += _SCORE_WEIGHTS["large_method"]
        for cname, _c, lcom4, method_count, cnloc in _iter_classes(tree, lines):
            if cnloc >= GOD_CLASS_NLOC and method_count >= GOD_CLASS_METHODS:
                findings.append(f"god_class:{cname} ({cnloc} nloc, {method_count} methods)")
                structural += _SCORE_WEIGHTS["god_class"]
            elif lcom4 >= 2 and method_count >= 3:
                findings.append(f"low_cohesion:{cname} (lcom4={lcom4})")
                structural += _SCORE_WEIGHTS["low_cohesion"]
        structural = max(structural, STRUCTURAL_CAP)

        n_dup = dup_by_file.get(key, 0)
        duplication = max(n_dup * _SCORE_WEIGHTS["duplicate_chunk"], DUPLICATION_CAP)
        if n_dup:
            findings.append(f"duplicate_chunk: {n_dup} khối trùng token với hàm khác")

        score = max(1.0, min(10.0, 10.0 + structural + duplication))
        report[key] = {"score": round(score, 1), "findings": findings}
    return report


def _selftest():
    """ponytail: check tất định tối thiểu — assert 3 detector cốt lõi thật sự bắt được ca rõ ràng."""
    complex_src = "def f(a, b, c, d, e):\n" + "".join(
        f"    if a == {i}:\n        pass\n    elif b == {i}:\n        pass\n" for i in range(4)
    )
    tree = ast.parse(complex_src)
    func = tree.body[0]
    ccn = _cyclomatic_complexity(func)
    assert ccn >= CCN_THRESHOLD, f"CCN thấp bất thường: {ccn}"

    cohesive_src = (
        "class Cohesive:\n"
        "    def a(self):\n        self.x = 1\n"
        "    def b(self):\n        return self.x\n"
    )
    lcom4, _mc = _class_cohesion(ast.parse(cohesive_src).body[0])
    assert lcom4 == 1, f"class dùng chung self.x phải cohesive (lcom4=1), got {lcom4}"

    split_src = (
        "class Split:\n"
        "    def a(self):\n        self.x = 1\n"
        "    def b(self):\n        return self.x\n"
        "    def c(self):\n        self.y = 2\n"
        "    def d(self):\n        return self.y\n"
    )
    lcom4, _mc = _class_cohesion(ast.parse(split_src).body[0])
    assert lcom4 == 2, f"2 cụm method rời nhau phải lcom4=2, got {lcom4}"

    dup_body = "\n".join(f"    x{i} = {i} + {i} * 2 - {i}" for i in range(20))
    dup_src = (
        f"def one():\n{dup_body}\n    return x0\n\n"
        f"def two():\n{dup_body}\n    return x0\n"
    )
    tree2 = ast.parse(dup_src)
    lines2 = dup_src.splitlines()
    chunks = _duplicate_chunks([(Path("<selftest>"), dup_src, tree2, lines2)])
    dup_hits = [h for h in chunks.values() if len({(f, q) for f, q, _ln in h}) >= 2]
    assert dup_hits, "2 hàm thân giống hệt nhau phải bị bắt trùng lặp"

    print("[code-complexity] selftest OK — CCN/cohesion/duplication đều bắt đúng ca rõ ràng.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--top", type=int, default=15, help="số file điểm thấp nhất hiển thị")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        _selftest()
        return

    root = Path(args.root).resolve()
    report = analyze(root)
    if not report:
        print("[code-complexity] không thấy .py nào trong PY_ROOTS — bỏ qua.")
        return

    ranked = sorted(report.items(), key=lambda kv: kv[1]["score"])
    worst = [(p, d) for p, d in ranked if d["findings"]][: args.top]
    if not worst:
        print(f"[code-complexity] ✓ {len(report)} file, không file nào có finding (heuristic, không defect-validated).")
        return

    print(f"[code-complexity] {len(report)} file, {len(worst)} file điểm thấp nhất có finding (heuristic, KHÔNG defect-validated):")
    for p, d in worst:
        rel = Path(p).relative_to(root) if Path(p).is_absolute() else p
        print(f"  {d['score']:>4.1f}/10  {rel}")
        for f in d["findings"][:5]:
            print(f"           · {f}")


if __name__ == "__main__":
    main()
