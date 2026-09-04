#!/usr/bin/env python3
"""skill-health — soi hình dạng mọi skill bằng CODE, không nhờ model nhớ (0 token).

Đo 5 mục theo concept skill-craft (wiki/concepts/skill-craft.md). Một dữ kiện
("skill này 340 dòng, 0 completion criterion, 61% câu cấm") đổi được hành vi;
một lời khuyên ("hãy viết gọn") thì không.

BÁO CÁO, KHÔNG CHẶN — đây là chất lượng, không phải an toàn. Exit luôn 0 trừ khi
--ci và có skill vượt ngưỡng CỨNG (chỉ để CI cảnh báo, mặc định vẫn không chặn).

Đo:
  1. context load — tổng token description của skill CÒN model-invoked
  2. completion criterion — bước '### Task'/'N.' không có điều kiện kiểm được ở cuối
  3. negation — tỉ lệ câu cấm (KHÔNG/đừng/cấm/never/don't) trên tổng câu
  4. sprawl — SKILL.md > ngưỡng dòng mà không có progressive disclosure (không link file .md khác)
  5. duplication — description gần trùng nhau giữa các skill (chớm — chỉ cảnh báo cặp giống >0.8)

`--fidelity` — thang BẢO CHÂN (hấp thụ alchaincyf/nuwa-skill, 09/2026). Năm mục trên đo HÌNH
DẠNG; thang này hỏi câu đắt hơn: skill CÓ HÀNH XỬ như nó khai không. Hai chiều đo tĩnh được
(minh bạch nguồn 15 · đầy đủ cấu trúc 15) chấm luôn ở đây, 0 token. Ba chiều còn lại (nhất
quán lập trường 30 · nhận diện văn phong 20 · trung thực ở rìa 20) in ra là CHƯA CHẤM kèm
lệnh — KHÔNG bịa điểm, vì chấm chúng cần LLM và giám khảo TÁCH RỜI khỏi agent trả bài
(SkillLens arXiv 2605.23899: LLM tự chấm chính nó đúng 46,4%, gần bằng đoán mò).

Đo lần đầu 2026-09-04: 85/86 skill đạt ≥22/30 phần tĩnh — nghĩa là hình dạng ta ổn, và toàn
bộ thông tin phân biệt nằm đúng ở 70 điểm CHƯA AI CHẤM.

Dùng:
  python3 harness/scripts/skill-health.py                 # bảng xếp hạng, exit 0
  python3 harness/scripts/skill-health.py --json          # máy đọc
  python3 harness/scripts/skill-health.py --skills-dir X  # mặc định ./skills
"""
import argparse
import glob
import json
import os
import re
import sys
from difflib import SequenceMatcher

# ngưỡng — chọn theo phân bố hiện tại, chỉnh được (SPEC 150726 Assumptions)
DESC_CHARS_WARN = 400        # description dài hơn → cân nhắc rút
LINES_WARN = 200             # SKILL.md dài hơn mà không disclosure → sprawl
NEGATION_WARN = 0.45         # >45% câu là câu cấm → nặng negation (guardrail-skill vốn cao, ngưỡng phải thật cao mới là tín hiệu)
TOTAL_TOKEN_WARN = 6000      # tổng context load model-invoked vượt → cảnh báo

NEG_RE = re.compile(r"\b(KHÔNG|ĐỪNG|đừng|không|cấm|CẤM|never|don't|do not|must not|chớ)\b", re.IGNORECASE)
# câu hoàn thành thường có completion criterion nếu chứa các dấu hiệu "đến khi/xong/pass/exit/→"
DONE_HINT_RE = re.compile(r"(hoàn tất|đã xong|hết|PASS|exit 0|exit 2|→|đến khi|cho tới khi|until|verify|kiểm|assert)", re.IGNORECASE)
# CHỈ bước thi hành thật cần completion criterion: checklist '- [ ]' và '### Task/Step'.
# Danh sách prose đánh số (nguyên tắc thiết kế, tham chiếu) KHÔNG phải bước hành động —
# đếm chúng là biến lint thành máy kêu sói (đúng lỗi no-op mà skill-craft cảnh báo).
# Bước thi hành nhiều dòng cần "chạy X → mong đợi Y". Một checkbox '- [ ]' một dòng
# TỰ NÓ là điều kiện kiểm được (chính cái ô tick) → không tính là thiếu criterion.
STEP_RE = re.compile(r"^\s*### (?:Task|Bước|Step)", re.MULTILINE)
EXEC_STEP_RE = re.compile(r"^\s*### (?:Task|Bước|Step)[^\n]*\n(.*?)(?=^\s*### (?:Task|Bước|Step)|\Z)",
                          re.M | re.S)
DISCLOSURE_RE = re.compile(r"\]\([^)]+\.md\)|`[^`]+\.md`")  # link/nhắc tới file .md khác → có disclosure

# ── Fidelity scorecard (hấp thụ alchaincyf/nuwa-skill `references/fidelity-scorecard.md`) ──
# skill-health cũ chỉ đo HÌNH DẠNG (dài/ngắn, câu cấm, thiếu criterion). Nó không trả lời
# được câu đắt hơn: skill này CÓ HÀNH XỬ như nó khai không. nüwa trả lời bằng thang 5 chiều
# /100 và một luật sắt: AGENT TRẢ BÀI VÀ AGENT CHẤM PHẢI TÁCH RỜI — dẫn SkillLens
# (arXiv 2605.23899) đo được LLM tự chấm skill của chính nó chỉ đúng 46,4%, gần bằng đoán mò.
#
# Hai chiều dưới đây đo TĨNH được nên đo luôn ở đây (0 token). Ba chiều còn lại
# (nhất quán lập trường 30 · nhận diện văn phong 20 · trung thực ở rìa 20) BẮT BUỘC cần
# LLM + giám khảo tách rời → in ra là CHƯA CHẤM kèm lệnh, KHÔNG bịa điểm.
# ponytail: đo 30/100 tất định còn hơn bịa 100/100.
SOURCE_RE = re.compile(r"^#{1,4}\s*(nguồn|source|origin|reference|tham khảo|distil)", re.I | re.M)
EXAMPLE_RE = re.compile(r"^\s*```|^\s*(?:ví dụ|example|mẫu)\b", re.I | re.M)
BOUNDARY_RE = re.compile(
    r"(khi nào KHÔNG|không dùng khi|when not to|not for\b|KHÁC\s+/|thay vì|instead of)", re.I)


def _provenance_names():
    """Skill có khai xuất xứ trong fdk/skills.provenance.json → tính là minh bạch nguồn."""
    for up in (2, 3):
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * up))
            with open(os.path.join(root, "fdk", "skills.provenance.json"), encoding="utf-8") as f:
                d = json.load(f)
            return set(d.get("skills") or d.keys())
        except Exception:
            continue
    return set()


def frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def field(fm, key):
    m = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
    return m.group(1).strip() if m else ""


def description(text):
    m = re.search(r"^description:\s*(.*?)(?=^\w[\w-]*:|^---)", text, re.M | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def analyze(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    fm = frontmatter(t)
    body = t[t.find("---", 3) + 3:] if t.startswith("---") else t
    disabled = re.search(r"disable-model-invocation:\s*true", fm) is not None
    desc = description(t)
    lines = t.count("\n") + 1
    sentences = [s for s in re.split(r"[.\n](?:\s|$)", body) if len(s.strip()) > 12]
    neg = sum(1 for s in sentences if NEG_RE.search(s))
    neg_ratio = neg / len(sentences) if sentences else 0.0
    has_disclosure = DISCLOSURE_RE.search(body) is not None
    # completion criterion: đếm bước không có dấu hiệu "done"
    steps = STEP_RE.findall(body)
    weak = sum(1 for m in EXEC_STEP_RE.finditer(body) if not DONE_HINT_RE.search(m.group(1)))
    # Fidelity: hai chiều đo tĩnh được (15 + 15 điểm trên thang 100 của nüwa)
    prov = _provenance_names()
    name = os.path.basename(os.path.dirname(path))
    has_source = bool(SOURCE_RE.search(body)) or name in prov
    struct_parts = [bool(desc), bool(EXAMPLE_RE.search(body)),
                    bool(BOUNDARY_RE.search(body)), not (steps and weak)]
    fid_source = 15 if has_source else 0
    fid_struct = round(15 * sum(struct_parts) / len(struct_parts))

    flags = []
    if not disabled and len(desc) > DESC_CHARS_WARN:
        flags.append(f"desc {len(desc)}c")
    if lines > LINES_WARN and not has_disclosure:
        flags.append(f"sprawl {lines}d")
    if neg_ratio > NEGATION_WARN:
        flags.append(f"negation {neg_ratio:.0%}")
    if steps and weak:
        flags.append(f"weak-criterion {weak}/{len(steps)}")
    return {
        "fidelity_source": fid_source,
        "fidelity_structure": fid_struct,
        "fidelity_scored": fid_source + fid_struct,
        "fidelity_unscored": 70,
        "name": os.path.basename(os.path.dirname(path)),
        "disabled": disabled,
        "desc_chars": len(desc),
        "desc_tokens": len(desc) // 4,
        "lines": lines,
        "neg_ratio": round(neg_ratio, 2),
        "weak_criteria": weak,
        "steps": len(steps),
        "flags": flags,
        "_desc": desc,
    }


def _print_fidelity(rows):
    """Thang bảo chân 5 chiều của nüwa — in ĐÚNG phần đo được, khai thẳng phần chưa chấm."""
    print("\n🔬 Fidelity scorecard (thang 100, hấp thụ nuwa-skill)")
    print("   ĐO TĨNH ĐƯỢC ở đây: minh bạch nguồn 15 · đầy đủ cấu trúc 15")
    print("   CHƯA CHẤM (cần LLM + giám khảo TÁCH RỜI): lập trường 30 · văn phong 20 · trung thực-ở-rìa 20")
    print("   Luật sắt: agent trả bài ≠ agent chấm. LLM tự chấm chính nó chỉ đúng 46,4% (SkillLens).\n")
    weak = sorted((r for r in rows if r["fidelity_scored"] < 22),
                  key=lambda r: r["fidelity_scored"])
    print(f"   {len(rows) - len(weak)}/{len(rows)} skill đạt ≥22/30 phần đo tĩnh.")
    if weak:
        print(f"   {len(weak)} skill yếu nhất ở phần đo được:")
        for r in weak[:12]:
            miss = []
            if not r["fidelity_source"]:
                miss.append("không khai nguồn")
            if r["fidelity_structure"] < 15:
                miss.append(f"cấu trúc {r['fidelity_structure']}/15")
            print(f"     {r['name']:<30} {r['fidelity_scored']:>2}/30  ({', '.join(miss)})")
    print("\n   Chấm 70 điểm còn lại cho MỘT skill:")
    print("     python3 harness/scripts/council.py prepare   # packet mù, giám khảo không thấy ai trả bài")
    print("     → agent TRẢ BÀI chỉ được đọc file trong thư mục skill, cấm truy mạng")
    print("     → agent CHẤM là phiên khác, nhận bài + rubric, không tham gia trả bài")
    print("     → ghi kết quả vào <skill>/FIDELITY.md kèm ngày và tên model đã dùng")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills-dir", default="skills")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fidelity", action="store_true",
                    help="in thang bảo chân 5 chiều (30 điểm đo tĩnh + 70 chưa chấm)")
    ap.add_argument("--ci", action="store_true")
    a = ap.parse_args()

    rows = [analyze(p) for p in sorted(glob.glob(os.path.join(a.skills_dir, "*", "SKILL.md")))]
    if not rows:
        print(f"skill-health: không thấy skill nào trong {a.skills_dir}/", file=sys.stderr)
        sys.exit(0)

    live = [r for r in rows if not r["disabled"]]
    total_tok = sum(r["desc_tokens"] for r in live)

    # duplication (chớm): cặp description giống > 0.8
    dups = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            if rows[i]["_desc"] and rows[j]["_desc"]:
                s = SequenceMatcher(None, rows[i]["_desc"][:200], rows[j]["_desc"][:200]).ratio()
                if s > 0.8:
                    dups.append((rows[i]["name"], rows[j]["name"], round(s, 2)))

    for r in rows:
        r.pop("_desc", None)

    if a.json:
        print(json.dumps({"total_model_invoked_tokens": total_tok, "n_disabled": len(rows) - len(live),
                          "skills": rows, "dup_pairs": dups}, ensure_ascii=False, indent=2))
        sys.exit(0)

    if a.fidelity:
        _print_fidelity(rows)
        sys.exit(0)

    flagged = sorted([r for r in rows if r["flags"]], key=lambda r: len(r["flags"]), reverse=True)
    print(f"skill-health · {len(rows)} skill ({len(live)} model-invoked, {len(rows)-len(live)} tắt)")
    print(f"  context load model-invoked: ~{total_tok:,} token/lượt"
          + ("  ⚠ vượt ngưỡng" if total_tok > TOTAL_TOKEN_WARN else ""))
    if flagged:
        print(f"  {len(flagged)} skill có cờ (báo cáo, KHÔNG chặn):")
        for r in flagged:
            print(f"    {r['name']:<26} {' · '.join(r['flags'])}")
    else:
        print("  không skill nào vượt ngưỡng hình dạng.")
    if dups:
        print(f"  {len(dups)} cặp description chớm-trùng (>0.8): "
              + ", ".join(f"{x}↔{y}" for x, y, _ in dups[:5]))
    sys.exit(0)


if __name__ == "__main__":
    main()
