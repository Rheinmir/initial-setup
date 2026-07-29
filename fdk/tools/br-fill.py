#!/usr/bin/env python3
"""br-fill — fill-chain tất định cho `/br interview --proactive` + checksum hợp đồng (T-260714-01).

Hai việc, đều KHÔNG gọi model:

  fill            Đọc spec-template (field nào required) + br/spec-filled.md (field nào
                  missing/conflict) + registry defaults (skills/br/assets/defaults.yaml,
                  project override br/defaults.yaml thắng khi trùng field) → in block
                  markdown ĐỀ XUẤT điền (mỗi mục kèm `filled_by` + `verified: false`)
                  và danh sách CÂU HỎI THẬT (field carve-out + field không có default).
                  Carve-out KHÔNG BAO GIỜ nhận giá trị máy — dù registry có entry.

  check-contract  Checksum hợp đồng (vá G1, council c9dc13d): mọi required field S1–S10
                  phải được ≥1 clause trong br/BR.clauses.json khai `fields: [...]` —
                  thiếu field nào in tên field đó + exit 2. Gate chạy ở cuối /br compile.

  selftest        Fixture inline, exit 0/2.

Usage:
  br-fill.py fill [--root .] [--json]
  br-fill.py check-contract [--root .]
  br-fill.py selftest
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

QUESTION_CAP = 5  # trần câu hỏi thật mỗi vòng interview (SPEC FR-003)

TEMPLATE_FIELD_RE = re.compile(r"- `(S\d+\.\d+)` \((required|optional)\)\s*(.*)")
FILLED_BLOCK_RE = re.compile(r"^### (S\d+\.\d+)", re.M)
STATUS_RE = re.compile(r"status:\s*`?(filled|missing|conflict|assumed)`?")


def framework_assets() -> Path:
    # fdk/tools/br-fill.py → parents[2] = gốc repo/framework (chứa skills/br/assets)
    return Path(__file__).resolve().parents[2] / "skills" / "br" / "assets"


def parse_template(text):
    """→ {field_id: {"required": bool, "label": str}} theo thứ tự khai trong template."""
    fields = {}
    for fid, req, label in TEMPLATE_FIELD_RE.findall(text):
        fields[fid] = {"required": req == "required", "label": label.strip()}
    return fields


def parse_filled(text):
    """→ {field_id: status}. Field có block nhưng không ghi status → coi là missing."""
    statuses = {}
    parts = FILLED_BLOCK_RE.split(text)
    # parts = [đầu-file, fid1, body1, fid2, body2, ...]
    for i in range(1, len(parts) - 1, 2):
        fid, body = parts[i], parts[i + 1]
        m = STATUS_RE.search(body)
        statuses[fid] = m.group(1) if m else "missing"
    return statuses


def load_registry(root: Path):
    """Merge registry asset + override project (project thắng theo field)."""
    if yaml is None:
        sys.exit("br-fill: cần PyYAML (python3 -m pip install pyyaml)")
    base = framework_assets() / "defaults.yaml"
    reg = {"carveout": [], "defaults": []}
    for src in [base, root / "br" / "defaults.yaml"]:
        if not src.exists():
            continue
        data = yaml.safe_load(src.read_text()) or {}
        for c in data.get("carveout") or []:
            reg["carveout"] = [x for x in reg["carveout"] if x["field"] != c["field"]] + [c]
        for d in data.get("defaults") or []:
            reg["defaults"] = [x for x in reg["defaults"] if x["field"] != d["field"]] + [d]
    return reg


def classify(template, statuses, registry):
    """Lõi fill-chain. → (suggestions, questions) — questions gồm cả carve-out.

    Thứ tự thang: raw-extract đã xảy ra trước (statuses là kết quả của nó);
    ở đây chỉ xử field required còn missing/conflict: carve-out chặn trước,
    rồi default (loop-26/spec-kit), còn lại thành câu hỏi (lens-fill là việc
    của model sau khi người chọn top-5 — tool không đoán thay lens).
    """
    carve = {c["field"]: c.get("reason", "") for c in registry["carveout"]}
    defaults = {d["field"]: d for d in registry["defaults"]}
    suggestions, questions = [], []
    for fid, meta in template.items():
        if not meta["required"]:
            continue
        status = statuses.get(fid, "missing")
        if status not in ("missing", "conflict"):
            continue
        if fid in carve:
            questions.append({"field": fid, "label": meta["label"], "status": status,
                              "why": f"carve-out: {carve[fid]}"})
        elif fid in defaults:
            d = defaults[fid]
            suggestions.append({
                "field": fid, "label": meta["label"], "status": status,
                "value": str(d.get("value", "")).strip(),
                "filled_by": f"{d.get('source', 'default')}:{','.join(d.get('refs') or []) or fid}",
                "verified": False,
                "note": str(d.get("note", "")).strip(),
            })
        else:
            questions.append({"field": fid, "label": meta["label"], "status": status,
                              "why": "không có default trong registry"})
    # carve-out chiếm suất hỏi trước (SPEC: carve-out luôn là câu hỏi thật)
    questions.sort(key=lambda q: 0 if q["why"].startswith("carve-out") else 1)
    return suggestions, questions


def render_fill_md(suggestions, questions):
    out = ["<!-- br-fill: đề xuất máy điền — dán vào NNN-answers.md, giữ nguyên filled_by/verified -->"]
    if suggestions:
        out.append("\n# ĐỀ XUẤT MÁY ĐIỀN (assumed — người duyệt gạch dòng nào không đồng ý)\n")
        for s in suggestions:
            out += [f"## {s['field']} — {s['label']}",
                    f"`filled_by: {s['filled_by']}` · `verified: false`", "",
                    s["value"], ""]
            if s["note"]:
                out.append(f"> note: {s['note']}\n")
    if questions:
        out.append(f"\n# CÂU HỎI THẬT ({len(questions)} field — trần {QUESTION_CAP} câu/vòng)\n")
        if len(questions) > QUESTION_CAP:
            out.append(f"> ⚠ vượt trần: chọn {QUESTION_CAP} theo Impact × Uncertainty "
                       f"(carve-out đã xếp trước), phần còn lại lens-fill.\n")
        for q in questions:
            out.append(f"- `{q['field']}` ({q['status']}) {q['label']} — {q['why']}")
    if not suggestions and not questions:
        out.append("\n✓ không field required nào missing/conflict — không có gì để điền/hỏi.")
    return "\n".join(out)


def cmd_fill(root: Path, as_json: bool):
    template = parse_template((framework_assets() / "spec-template.md").read_text())
    spec_filled = root / "br" / "spec-filled.md"
    if not spec_filled.exists():
        sys.exit(f"br-fill: không thấy {spec_filled} — chạy /br interview bước extract trước.")
    statuses = parse_filled(spec_filled.read_text())
    suggestions, questions = classify(template, statuses, load_registry(root))
    if as_json:
        print(json.dumps({"suggestions": suggestions, "questions": questions,
                          "question_cap": QUESTION_CAP}, ensure_ascii=False, indent=2))
    else:
        print(render_fill_md(suggestions, questions))
    return 0


def check_contract(template, statuses, clauses):
    """→ danh sách lỗi. Mọi required field phải được ≥1 clause khai trong `fields`."""
    claimed = set()
    any_fields = False
    for cid, meta in clauses.items():
        fs = (meta or {}).get("fields") or []
        if fs:
            any_fields = True
        claimed.update(fs)
    problems = []
    if clauses and not any_fields:
        problems.append("BR.clauses.json chưa clause nào khai `fields:` — compile bản cũ; "
                        "chạy lại /br compile (Mode 2 bước 3) để khai field↔clause.")
        return problems
    for fid, meta in template.items():
        if not meta["required"]:
            continue
        if fid not in claimed:
            status = statuses.get(fid, "missing")
            problems.append(f"required field `{fid}` ({meta['label']}, status={status}) "
                            f"không có clause đối ứng")
    return problems


def cmd_check_contract(root: Path):
    template = parse_template((framework_assets() / "spec-template.md").read_text())
    spec_filled = root / "br" / "spec-filled.md"
    clauses_p = root / "br" / "BR.clauses.json"
    if not clauses_p.exists():
        sys.exit(f"br-fill: không thấy {clauses_p} — chạy /br compile trước.")
    statuses = parse_filled(spec_filled.read_text()) if spec_filled.exists() else {}
    problems = check_contract(template, statuses, json.loads(clauses_p.read_text()))
    if problems:
        print("✗ checksum hợp đồng THỦNG (G1):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2
    print("✓ checksum hợp đồng: mọi required field S1–S10 có clause đối ứng.")
    return 0


def cmd_selftest():
    template = parse_template(
        "- `S1.1` (required) Bài toán.\n"
        "- `S1.2` (optional) Phụ.\n"
        "- `S7.2` (required) Bảo mật & phân quyền.\n"
        "- `S7.5` (required) Giao diện.\n"
        "- `S8.2` (required) Deadline.\n")
    statuses = parse_filled(
        "### S1.1 Bài toán\n`status: filled` · `provenance: raw:a.docx`\n\n"
        "### S7.2 Bảo mật\n`status: missing`\n\n"
        "### S7.5 Giao diện\nstatus: missing\n")
    assert statuses == {"S1.1": "filled", "S7.2": "missing", "S7.5": "missing"}, statuses
    registry = {
        "carveout": [{"field": "S7.2", "reason": "auth"}],
        "defaults": [{"field": "S7.5", "source": "loop-26", "refs": ["A2"], "value": "Neumorphism", "note": ""},
                     {"field": "S7.2", "source": "loop-26", "refs": ["XX"], "value": "KHÔNG ĐƯỢC DÙNG", "note": ""}],
    }
    sugg, ques = classify(template, statuses, registry)
    # carve-out thắng default: S7.2 có entry default nhưng PHẢI là câu hỏi
    assert [s["field"] for s in sugg] == ["S7.5"], sugg
    assert sugg[0]["verified"] is False and sugg[0]["filled_by"] == "loop-26:A2", sugg
    # S8.2 required, không có block trong spec-filled → missing → câu hỏi; carve-out xếp trước
    assert [q["field"] for q in ques] == ["S7.2", "S8.2"], ques
    md = render_fill_md(sugg, ques)
    assert "verified: false" in md and "S7.2" in md and "KHÔNG ĐƯỢC DÙNG" not in md
    # check-contract: đủ claim → pass; bỏ claim S7.5 → fail đúng field; clauses cũ không fields → báo back-compat
    ok = check_contract(template, statuses,
                        {"C1": {"fields": ["S1.1", "S8.2"]}, "C2": {"fields": ["S7.2", "S7.5"]}})
    assert ok == [], ok
    bad = check_contract(template, statuses, {"C1": {"fields": ["S1.1", "S8.2", "S7.2"]}})
    assert len(bad) == 1 and "S7.5" in bad[0], bad
    old = check_contract(template, statuses, {"C1": {"provenance": "raw", "assumed": False}})
    assert len(old) == 1 and "compile bản cũ" in old[0], old
    # registry thật của framework phải load được và carve-out không rỗng
    reg = load_registry(Path("."))
    assert reg["carveout"] and reg["defaults"], "registry asset thiếu/hỏng"
    assert all("value" in d and d["value"] for d in reg["defaults"])
    print("✓ br-fill selftest pass")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="fill-chain tất định + checksum hợp đồng cho /br")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fill", help="đề xuất điền field missing từ registry defaults")
    f.add_argument("--root", default=".")
    f.add_argument("--json", action="store_true")
    c = sub.add_parser("check-contract", aliases=["check"],
                       help="checksum hợp đồng S1–S10 ↔ clause (G1)")
    c.add_argument("--root", default=".")
    sub.add_parser("selftest")
    a = ap.parse_args(argv)
    if a.cmd == "fill":
        return cmd_fill(Path(a.root), a.json)
    if a.cmd in ("check-contract", "check"):
        return cmd_check_contract(Path(a.root))
    return cmd_selftest()


if __name__ == "__main__":
    sys.exit(main())
