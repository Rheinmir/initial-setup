#!/usr/bin/env python3
"""build-capabilities — sinh BẢN ĐỒ NĂNG LỰC BẰNG CODE, luôn-mới, ở CẢ HAI bối cảnh.

Vấn đề: framework đã quá lớn (57 skill + rule + tool) → agent KHÔNG chắc biết hết cái
gì có để dùng → nhiều thứ không bao giờ được dùng tới. Không thể dựa vào agent "nhớ".
Giải: một file CAPABILITIES.md SINH TỪ ĐĨA bằng code (không hardcode, không drift), liệt kê
gọn mọi skill + rule (+ tool nếu là repo framework); AGENT.md trỏ tới nó; `--check` chặn
commit nếu nó cũ → nên nó LUÔN khớp thực tế.

HAI BỐI CẢNH (quyết định scope 2026-06-28, xem ADR-005):
  • Repo framework (có fdk/tools + harness/scripts): map ĐẦY ĐỦ skill+rule+fdk-tool+script,
    ghi fdk/CAPABILITIES.md. `--check` là cổng cứng trong fdk-gate.
  • Dự án downstream (cài framework, KHÔNG có fdk/): skill là GLOBAL ~/.claude/skills, rule
    từ policy.yaml đã cài → map GỌN "đồ nghề bạn có Ở DỰ ÁN NÀY", ghi <root>/CAPABILITIES.md.
    KHÔNG có cổng `--check` cứng ở đây (skill global đổi ngoài project → không phải lỗi của họ).

CLI:
  build-capabilities.py                 # tự nhận bối cảnh, ghi CAPABILITIES.md
  build-capabilities.py --root <path>   # ép root (deployed cạnh hooks gọi với --root <project>)
  build-capabilities.py --check         # exit 2 nếu CAPABILITIES.md cũ (CHỈ dùng ở repo framework)
"""
import json
import re
import subprocess
import sys
from pathlib import Path


def detect_root() -> Path:
    """Repo framework (script ở fdk/tools/) → parents[2]. Nếu script đã được DEPLOY cạnh hooks
    (parents[2] không có fdk/tools) → dùng dự án đang gọi: git-root của CWD, hoặc CWD."""
    repo = Path(__file__).resolve().parents[2]
    if (repo / "fdk" / "tools").is_dir() and (repo / "harness" / "scripts").is_dir():
        return repo
    try:
        r = subprocess.run(["git", "-C", str(Path.cwd()), "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip():
            return Path(r.stdout.strip())
    except Exception:
        pass
    return Path.cwd()


ROOT = detect_root()


def is_framework_repo(root: Path) -> bool:
    return (root / "fdk" / "tools").is_dir() and (root / "harness" / "scripts").is_dir()


def cap_path(root: Path) -> Path:
    """Repo framework → fdk/CAPABILITIES.md. Downstream → <root>/CAPABILITIES.md."""
    return (root / "fdk" / "CAPABILITIES.md") if (root / "fdk").is_dir() else (root / "CAPABILITIES.md")


def skills_dir(root: Path) -> Path:
    """Repo có skills/ nguồn → dùng nó. Downstream KHÔNG có → skill là GLOBAL ~/.claude/skills."""
    local = root / "skills"
    if local.is_dir() and any(local.glob("*/SKILL.md")):
        return local
    return Path.home() / ".claude" / "skills"


def parse_frontmatter_desc(p: Path):
    """Lấy `description` từ YAML frontmatter (hỗ trợ inline + folded >-)."""
    try:
        t = p.read_text(encoding="utf-8")
    except Exception:
        return ""
    m = re.match(r"^---\n(.*?)\n---", t, re.S)
    if not m:
        return ""
    fm = m.group(1)
    dm = re.search(r"^description:\s*(.*)$", fm, re.M)
    if not dm:
        return ""
    val = dm.group(1).strip()
    if val in (">", ">-", "|", "|-"):  # folded/literal → gom dòng thụt sau
        body = []
        for ln in fm[dm.end():].splitlines():
            if ln.strip() and (ln.startswith(" ") or ln.startswith("\t")):
                body.append(ln.strip())
            elif ln.strip():
                break
        val = " ".join(body)
    return val.strip().strip('"').strip("'")


def load_loops(root: Path):
    """LOOP_MAP từ sync-skills.py (nguồn duy nhất). Downstream không có file này → {} (mọi skill về utils)."""
    try:
        t = (root / "harness" / "scripts" / "sync-skills.py").read_text(encoding="utf-8")
        m = re.search(r"LOOP_MAP\s*=\s*\{(.*?)\}", t, re.S)
        return dict(re.findall(r'"([a-z0-9-]+)"\s*:\s*"([a-z-]+)"', m.group(1))) if m else {}
    except Exception:
        return {}


def first_sentence(s, n=90):
    s = re.split(r"(?<=[.!?。])\s|—| - |\. ", s or "", 1)[0].strip()
    return (s[:n] + "…") if len(s) > n else s


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
        # regex trước đây CHỈ bắt harness/scripts/ — bỏ sót fdk/tools/ (bug thật: fdk-uat wrap
        # medic.py ở fdk/tools/, có --self-test, vẫn bị bêu UNPROVEN vì lệch đường dẫn).
        for sub in ("harness/scripts", "fdk/tools"):
            for eng in re.findall(sub + r'/([\w\-]+\.py)', body):
                ep = root / sub / eng
                if not ep.is_file():
                    continue
                et = ep.read_text(encoding="utf-8", errors="ignore")
                if "--self-test" in et:
                    return f"{sub}/{eng} --self-test", "selftest"
                if re.search(r'["\']selftest["\']', et):
                    return f"{sub}/{eng} selftest", "selftest"
    if kind in ("script", "tool", "mech"):                             # 4b. engine tự có self-test
        # hai quy ước cùng tồn tại trong codebase: flag "--self-test" (đa số) và subcommand
        # "selftest" không gạch ngang (vd loop-runner.py) — cả hai đều hợp lệ, resolver phải
        # nhận cả hai thay vì đòi quy ước duy nhất.
        if "--self-test" in body:
            return f"{name} --self-test", "selftest"
        if re.search(r'["\']selftest["\']', body):
            return f"{name} selftest", "selftest"
    if kind in ("script", "tool", "mech") and "os.execv(" in body:    # 4c. thin os.execv shim
        # shim gán biến từ os.path.join(os.path.dirname(...), "target.py") rồi execv biến đó —
        # KHÔNG match cấu trúc os.path.join(...) (dấu ')' lồng bên trong phá [^)]*), chỉ cần
        # tìm chuỗi "*.py" bất kỳ trong file — shim mỏng chỉ có đúng 1 chuỗi .py là target.
        m = re.search(r'["\']([\w\-]+\.py)["\']', body)
        if m:
            sub = "harness/scripts" if kind == "script" else "fdk/tools"
            target = root / sub / m.group(1)
            if target.is_file() and "--self-test" in target.read_text(encoding="utf-8", errors="ignore"):
                return f"{m.group(1)} --self-test (qua shim delegate)", "shim-delegate"
    if name.replace(".py", "") in src["goldens"]:                     # 5. golden eval nhắc tên
        return "wiki/sources/evals/*", "golden"
    if kind != "mech" and name.replace(".py", "") in src["medic"]:    # 6. medic probe nhắc tên
        return "fdk/tools/medic.py", "medic-tag"
    # 7. N/A — skill THUẦN PROMPT (không tham chiếu engine .py nào trong SKILL.md) không có
    # code-path để test; đếm nó là "unproven" là capproof tự tạo nợ giả (root-cause 2026-07-18:
    # 34/38 skill-unproven hoá ra rơi đúng nhóm này — brandkit/caveman-*/gpt-taste/imagegen-*…).
    # Chỉ áp dụng skill; script/tool luôn LÀ code nên không được exempt qua nhánh này.
    if kind == "skill" and not re.search(r'python3 (?:harness/scripts|fdk/tools)/[\w\-]+\.py', body):
        return "N/A — pure-prompt skill, không có engine .py để test", "no-engine"
    return None, "none"


def _dup_candidates(items: dict, descs: dict) -> list:
    """Ứng viên trùng — CHỈ BÁO, người phán (dedupe = vòng /propose riêng). Hai tín hiệu tất định:
    (a) chung token tên HIẾM giữa 2 kind khác nhau, hoặc cùng kind mà stem này chứa stem kia
        (bắt ca 'đã merge nhưng bản cũ còn sống': flywheel.py ⊂ failure-flywheel.py);
    (b) desc Jaccard token ≥ 0.5 (cả hai ≥ 5 token)."""
    def toks(s):
        return {t for t in re.findall(r"[a-z]{4,}", (s or "").lower()) if t not in PROOF_STOP}
    def stem(k):
        return k.split(":", 1)[1].replace(".py", "").replace("_", "-")
    names = {k: toks(stem(k).replace("-", " ")) for k in items}
    dups = []
    keys = sorted(items)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            ka, kb = a.split(":")[0], b.split(":")[0]
            if ka == kb == "rule":
                continue
            if stem(a) == stem(b):
                continue  # wrapper theo thiết kế: skill/mech ↔ chính engine cùng tên — không phải dup
            shared = names[a] & names[b]
            substem = stem(a) in stem(b) or stem(b) in stem(a)
            mech_pair = (ka == "mech") != (kb == "mech")
            strong = substem or len(shared) >= 2   # 1 token chung chung (scan/design/verify) chưa đủ nghi
            if shared and strong and not mech_pair and (ka != kb or substem):
                dups.append({"a": a, "b": b, "why": f"name-token: {'+'.join(sorted(shared)[:2])}"})
                continue
            ta, tb = toks(descs.get(a, "")), toks(descs.get(b, ""))
            if len(ta) >= 5 and len(tb) >= 5:
                jac = len(ta & tb) / len(ta | tb)
                if jac >= 0.5:
                    dups.append({"a": a, "b": b, "why": f"desc-jaccard {jac:.2f}"})
    return dups


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
        base = root / sub
        if not base.is_dir():
            continue
        for f in sorted(base.glob("*.py")):
            body = f.read_text(encoding="utf-8", errors="ignore")
            p, via = _resolve_one(root, src, kind, f.name, body)
            items[f"{kind}:{f.name}"] = {"proof": p, "via": via}
            mdoc = re.search(r'"""(.+?)$', body, re.M)
            descs[f"{kind}:{f.name}"] = mdoc.group(1) if mdoc else ""
    man = root / "harness" / "mechanisms.yaml"
    if man.is_file():
        mt = man.read_text(encoding="utf-8")
        # per-entry BLOCK (không phải flat file) — để `proof:` khai tay đúng ĐÚNG entry, không
        # lẫn giữa các mechanism cạnh nhau (2026-07-18: mech kind bị loại khỏi tier 6 medic-tag
        # có chủ ý — chống false-positive — nên khi coverage THẬT tồn tại nhưng khác từ vựng
        # (vd secondary-memory ↔ memory-map-user-reachability-test.sh), đường thoát tường minh
        # là khai tay ở ĐÚNG CHỖ dữ liệu sống — manifest entry — không phải hack docstring .py).
        for blk in re.split(r'(?=^  - id:)', mt, flags=re.M)[1:]:
            idm = re.search(r'^\s*-\s*id:\s*(\S+)', blk, re.M)
            lpm = re.search(r'^\s*live_probe:\s*(.+?)\s*$', blk, re.M)
            if not (idm and lpm):
                continue
            mid, lp = idm.group(1), lpm.group(1)
            proofm = re.search(r'^\s*proof:\s*(.+?)\s*$', blk, re.M)
            if proofm and (root / proofm.group(1)).exists():
                items[f"mech:{mid}"] = {"proof": proofm.group(1), "via": "manifest-proof"}
                continue
            lpp = root / lp
            if lpp.is_dir():          # mechanism cấu trúc (thư mục) — narrative probe đã tự
                items[f"mech:{mid}"] = {"proof": f"{lp} (thư mục tồn tại)", "via": "dir-exists"}
                continue
            body = lpp.read_text(encoding="utf-8", errors="ignore") if lpp.is_file() else ""
            p, via = _resolve_one(root, src, "mech", mid, body)
            items[f"mech:{mid}"] = {"proof": p, "via": via}
    unproven = sorted(k for k, v in items.items() if v["proof"] is None)
    return {"schema": "capproof/v1", "downstream": False,
            "counts": {"total": len(items), "proven": len(items) - len(unproven), "unproven": len(unproven)},
            "items": items, "unproven": unproven, "dups": _dup_candidates(items, descs)}


def build(root: Path) -> str:
    repo = is_framework_repo(root)
    loops = load_loops(root)
    skills = []
    for d in sorted(skills_dir(root).glob("*/")):
        name = d.name
        sk = d / "SKILL.md"
        if sk.is_file():
            skills.append((name, loops.get(name, "utils"), first_sentence(parse_frontmatter_desc(sk))))
    by_loop = {}
    for name, loop, desc in skills:
        by_loop.setdefault(loop, []).append((name, desc))

    rules = []
    # policy.yaml ở vị trí khác nhau tuỳ bối cảnh: repo framework dùng poc-vendor-neutral/;
    # dự án CÀI per-project để ở harness/policy.yaml (xem install-harness.sh). Tìm cả hai.
    pol = next((p for p in (
        root / "harness" / "poc-vendor-neutral" / "policy.yaml",   # repo framework
        root / "harness" / "policy.yaml",                          # dự án đã cài (per-project)
    ) if p.is_file()), None)
    if pol and pol.is_file():
        for blk in re.findall(r"id:\s*(R\d+).*?name:\s*([^\n]+)", pol.read_text(encoding="utf-8"), re.S):
            rules.append((blk[0], blk[1].strip().strip('"')))
        rules = sorted(set(rules), key=lambda r: int(r[0][1:]))

    out = ["<!-- SINH BẰNG CODE: build-capabilities.py — ĐỪNG sửa tay; chạy lại để cập nhật. -->",
           "# CAPABILITIES — toàn bộ đồ nghề (luôn-mới, đếm từ đĩa)", ""]

    if repo:
        tools = sorted(p.name for p in (root / "fdk" / "tools").glob("*.py"))
        scripts = sorted(p.name for p in (root / "harness" / "scripts").glob("*.py"))
        out += [f"**{len(skills)} skill · {len(rules)} rule · {len(tools)} fdk-tool · {len(scripts)} harness-script.** "
                "Agent: đây là danh sách ĐẦY ĐỦ những gì bạn có để dùng. Tìm nhanh: `python3 fdk/tools/build-skill-search.py` "
                "rồi `find-skill \"<việc cần làm>\"`. Phát triển framework: gọi `/fdk`.", ""]
    else:
        out += [f"**{len(skills)} skill · {len(rules)} rule** khả dụng Ở DỰ ÁN NÀY "
                "(skill là global `~/.claude/skills`; rule do harness đã cài ở đây gác). "
                "Agent: đây là đồ nghề bạn CÓ — đừng làm lại thứ đã tồn tại. Tìm nhanh: `find-skills \"<việc>\"`. "
                "(Đồ nghề DEV framework — fdk-gate, build-capabilities… — chỉ có trong repo framework.)", ""]

    LOOP_ORDER = ["wiki-loop", "dev-loop", "orchestrate", "utils"]
    out.append("## Skills (gọi bằng `/<tên>`)")
    out += [
        "",
        "> **HAI cách tiếp cận KHÁC NHAU HOÀN TOÀN — chọn trước khi bới danh sách:**",
        "> - **`/br` (oneshot mockup)** — nhắm *một phát ra MOCKUP* từ dữ liệu tổng hợp sẵn có (`raw/`), rồi *sửa agile NGAY trên mockup*. Đi bề rộng nhanh. Dùng khi có tài liệu thô và cần sản phẩm chạy được sớm để bàn tiếp. (`/br auto` = interview tự-điền.)",
        "> - **`/orca-workflow` (plan + spec)** — xử lý *task PLAN + SPEC chức năng* bài bản: khi làm dần *từng phần* dự án, hoặc *sửa vài chức năng trên dự án cũ*. Đi bề sâu, gate từng bước (propose→gate→dispatch→verify).",
        ">",
        "> KHÔNG thay thế nhau: `/br` = oneshot rồi agile trên mockup · `/orca-workflow` = plan/spec truy vết từng bước. Các skill dev-loop bên dưới phần lớn là *bước con* do `/orca-workflow` điều phối.",
        "",
    ]
    for loop in LOOP_ORDER + [l for l in by_loop if l not in LOOP_ORDER]:
        if loop not in by_loop:
            continue
        out.append(f"\n### {loop} ({len(by_loop[loop])})")
        for name, desc in sorted(by_loop[loop]):
            out.append(f"- **`/{name}`** — {desc}" if desc else f"- **`/{name}`**")

    out.append("\n## Harness rules (gác tự động — vi phạm bị chặn)")
    for rid, rname in rules:
        out.append(f"- **{rid}** — {rname}")

    if repo:
        out.append("\n## FDK tools (`python3 fdk/tools/<x>`)")
        out += [f"- `{t}`" for t in tools]
        out.append("\n## Harness scripts (`python3 harness/scripts/<x>`)")
        out += [f"- `{s}`" for s in scripts]
        cp = capproof(root)
        if not cp.get("downstream"):
            out.append(f"\n## Neo bằng chứng — {cp['counts']['proven']}/{cp['counts']['total']} năng lực có neo KHAI BÁO")
            out.append("**Đọc cho đúng: đây KHÔNG phải bằng chứng năng lực còn SỐNG.** Mỗi năng lực được map "
                       "tất định tới một *điểm neo* bằng chứng trên đĩa (frontmatter `proof:` > rule-map > tests "
                       "> self-test > golden > medic). Việc map là **tĩnh** — nó kiểm file/chuỗi có mặt, "
                       "**không thực thi gì cả**. Nó bắt được ca 'năng lực này chẳng có test/golden/rule nào neo "
                       "vào' (hữu ích thật), nhưng KHÔNG bắt được ca 'test có mà đỏ' hay 'engine có mà chết'. "
                       "Muốn biết một dependency ngoài còn sống thì hỏi `harness/scripts/dep-health.py`. "
                       "Chi tiết neo: `build-capabilities.py --capproof-json`.")
            # shortcut: neo TĨNH (0 thực thi), nâng lên chạy thật khi có ngân sách CI —
            # rẻ nhất là tier `selftest` (engine đã có --self-test) rồi mới tới `tests`.
            if cp["unproven"]:
                out.append(f"\n## CHƯA CÓ NEO ({len(cp['unproven'])}) — năng lực có mặt nhưng không neo vào test/golden/rule nào")
                out += [f"- `{k}` — thêm proof rẻ nhất: test nhắc tên trong harness/tests/, hoặc khai `proof:` trong frontmatter" for k in cp["unproven"]]
            if cp["dups"]:
                out.append(f"\n## TRÙNG-ỨNG-VIÊN ({len(cp['dups'])}) — máy phát hiện, NGƯỜI phán (dedupe = vòng /propose riêng)")
                out += [f"- `{d['a']}` ↔ `{d['b']}` — {d['why']}" for d in cp["dups"]]
        out.append("\n## Origin\n- Sinh bằng `fdk/tools/build-capabilities.py` từ đĩa (skills/, policy.yaml, fdk/tools/, harness/scripts/, sync-skills LOOP_MAP). KHÔNG hardcode.")
    else:
        out.append("\n## Đồ nghề dev-framework")
        out.append("- Chỉ có trong repo framework (dự án này chỉ CÀI framework, không phát triển nó). "
                   "Cần sửa chính skill/rule/validator → làm ở repo framework với `/fdk`.")
        out.append("\n## Origin\n- Sinh bằng `build-capabilities.py` (deploy cạnh hooks) từ global skills + policy.yaml đã cài. KHÔNG hardcode.")
    return "\n".join(out) + "\n"


def main():
    global ROOT
    args = sys.argv[1:]
    if "--root" in args:
        i = args.index("--root")
        ROOT = Path(args[i + 1]).resolve()
    elif any(a.startswith("--root=") for a in args):
        ROOT = Path(next(a.split("=", 1)[1] for a in args if a.startswith("--root="))).resolve()
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
    cap = cap_path(ROOT)
    content = build(ROOT)
    if "--check" in args:
        if not is_framework_repo(ROOT):
            # Downstream: skill global đổi ngoài project → KHÔNG chặn commit của họ. Chỉ thông báo.
            print("[build-capabilities] downstream: --check chỉ là cổng cứng ở repo framework; bỏ qua.")
            sys.exit(0)
        cur = cap.read_text(encoding="utf-8") if cap.is_file() else ""
        if cur.strip() != content.strip():
            print("[build-capabilities] CAPABILITIES.md CŨ so với đĩa — chạy "
                  "`python3 fdk/tools/build-capabilities.py` để cập nhật (agent cần map đúng).", file=sys.stderr)
            sys.exit(2)
        print("CAPABILITIES.md khớp đĩa ✓")
        sys.exit(0)
    cap.parent.mkdir(parents=True, exist_ok=True)
    cap.write_text(content, encoding="utf-8")
    try:
        shown = cap.relative_to(ROOT)
    except ValueError:
        shown = cap
    print(f"✓ wrote {shown} ({content.count(chr(10))} dòng)")


if __name__ == "__main__":
    main()
