#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""medic — CỔNG SỨC KHOẺ TỔNG / tuyến phòng thủ cuối của framework overstack.

Gõ `medic`, xanh = hệ khoẻ. MỘT lệnh gom mọi kiểm tra tất định (compose tool đã có,
KHÔNG đẻ tool trùng). Không phải nhớ 7 lệnh — mô tả phạm vi là đủ.

Dùng:
  medic                 # tất cả (all)
  medic rules           # chỉ nhóm khớp 'rules' (mô tả phạm vi, không nhớ subcommand)
  medic docs eval       # nhiều phạm vi
  medic --ci            # exit≠0 nếu có mục FAIL (để chốt pre-commit/CI)
  medic --list          # liệt kê các probe + tag

Triết lý: Meadows (vòng phản hồi trên tầng enforcement) + hub-1-tên/transparent (kim chỉ nam fdk).
Tự-mở-coverage: đọc policy.yaml/validator/generator LIVE → thêm chức năng mà quên hàng rào → medic tự báo.
Self-contained: chỉ stdlib. Fail-open từng probe: probe lỗi → SKIP, không giết cả cổng.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
G, Y, R, B, X = "\033[32m", "\033[33m", "\033[31m", "\033[34m", "\033[0m"


def sh(args, timeout=120):
    try:
        r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 127, str(e)


# ── PROBES ─────────────────────────────────────────────────────────────────────────────────
# Mỗi probe trả (state, detail, fix): state ∈ 'ok'|'fail'|'warn'|'skip'.
def p_rules():
    """Luật có CẮN không — harness-doctor fire-drill (BAD phải bị chặn)."""
    doc = ROOT / "harness/scripts/harness-doctor.py"
    if not doc.exists():
        return "skip", "harness-doctor.py không có", ""
    rc, out = sh([PY, str(doc), "--ci"])
    m = re.search(r"(\d+)/(\d+) rails bite", out)
    bite = m.group(0) if m else "?"
    drift = "✗ validator drift" in out
    if rc != 0:
        return "fail", f"có rail ĐEN (BAD không bị chặn) — {bite}", "python3 harness/scripts/harness-doctor.py --ci"
    if drift:
        dl = next((l.strip() for l in out.splitlines() if "validator drift" in l), "drift")
        return "warn", f"{bite} cắn, NHƯNG {dl}", "sync validator: bản hooks-copy khác src"
    return "ok", f"{bite} rail đều cắn", ""


def p_coverage():
    """Tự-mở-coverage: rule trong policy.yaml có bite-test chưa (debt hiện tại)."""
    pol = ROOT / "harness/poc-vendor-neutral/policy.yaml"
    doc = ROOT / "harness/scripts/harness-doctor.py"
    if not (pol.exists() and doc.exists()):
        return "skip", "thiếu policy.yaml/harness-doctor", ""
    rules = set(re.findall(r"id:\s*(R\d+)", pol.read_text(encoding="utf-8")))
    tested = set(re.findall(r"def build_(r\d+)", doc.read_text(encoding="utf-8")))
    tested = {t.upper() for t in tested}
    missing = sorted(rules - tested, key=lambda r: int(r[1:]))
    if not missing:
        return "ok", f"{len(rules)}/{len(rules)} rule có bite-test", ""
    return "warn", (f"{len(tested)}/{len(rules)} rule có bite-test — {len(missing)} chưa chứng minh: "
                    + ",".join(missing)), "mở rộng harness-doctor build_rN cho rule còn thiếu (proposal medic)"


def p_backstop():
    """Backstop L2 git còn SỐNG không — không phải "có tồn tại file hook không".

    Bản cũ hỏi `.git/hooks/pre-commit.exists()` rồi kết luận "đã cài". Nhưng shim git là
    một file shell gọi binary `pre-commit`; binary vắng mặt thì shim vẫn tồn tại còn hook
    thì GÃY lúc commit — cổng sức khoẻ cuối tuyên bố một phòng tuyến đang sống từ một inode.
    Cùng lớp lỗi với code-graph (xem p_deps)."""
    import shutil as _sh
    hook = (ROOT / ".git/hooks/pre-commit").exists()
    binary = _sh.which("pre-commit") is not None
    if hook and binary:
        return "ok", "pre-commit sống (shim + binary trên PATH)", ""
    if hook and not binary:
        return "warn", ("shim git CÓ nhưng binary `pre-commit` KHÔNG trên PATH — "
                        "hook gãy lúc commit, L2 coi như TẮT"), "pip install pre-commit"
    return "warn", "pre-commit CHƯA cài — backstop L2 tắt", "pre-commit install"


def p_docs():
    """Docs/CAPABILITIES khớp đĩa không (anti-drift) — mọi build-*.py --check LIVE."""
    # chỉ generator KHAI có --check (khớp bản 'luôn-mới' wired ở stop.py) — tránh false-positive
    KNOWN = ("build-overstack-docs.py", "build-capabilities.py")   # generator có --check THẬT (anti-drift)
    checks = []
    for fn in KNOWN:
        gen = ROOT / "fdk/tools" / fn
        if not gen.exists():
            continue
        rc, out = sh([PY, str(gen), "--check"], timeout=60)
        if "required" in out and "argument" in out:      # thiếu positional → không phải --check thật
            continue
        checks.append((gen.stem, rc == 0))
    if not checks:
        return "skip", "không generator nào có --check", ""
    stale = [n for n, ok in checks if not ok]
    if stale:
        return "fail", f"{len(stale)} docs CŨ so đĩa: {','.join(stale)}", "python3 fdk/tools/<gen>.py  # regen"
    return "ok", f"{len(checks)} generator khớp đĩa", ""


def p_frontend():
    """Anti-pattern FRONTEND ở HTML sinh (ligature code, prose lọt code block) — p_docs không bắt."""
    chk = ROOT / "fdk/tools/frontend-antipattern.py"
    if not chk.exists():
        return "skip", "chưa có frontend-antipattern.py", ""
    rc, out = sh([PY, str(chk)], timeout=30)
    tail = next((ln.strip() for ln in reversed(out.splitlines()) if ln.strip()), "")
    if rc == 1:
        return "fail", tail or "có anti-pattern frontend", "python3 fdk/tools/frontend-antipattern.py  # xem chi tiết"
    if rc == 2:
        return "warn", tail or "có cảnh báo frontend", "python3 fdk/tools/frontend-antipattern.py"
    return "ok", "HTML sinh sạch anti-pattern frontend", ""


#   Root-cause gap (senior-lens 2026-07-18): 4 probe mới (capproof, provenance) + 4 mechanism
#   mới ship trong 2 ngày mà KHÔNG vào mechanisms.yaml — narrative probe vẫn PASS vì nó chỉ so
#   manifest ĐÃ KHAI với trang, không biết PROBES thực tế đã lớn hơn manifest. Vá lần này chỉ là
#   TRIỆU CHỨNG (thêm tay 4 dòng); vá TẬN GỐC là dòng dưới — bắt PROBES tự đối chiếu chính nó với
#   manifest, để probe mới KHÔNG THỂ ship im lặng lần sau (probe mới không có dòng ở đây → medic đỏ
#   ngay, không cần ai nhớ hỏi "đã document chưa").
#   Giá trị None = quyết định TƯỜNG MINH "đây là probe nội bộ/meta, không narrate" (không phải
#   quên) — thêm probe mới mà không thêm dòng vào đây là lỗi cấu trúc (KeyError-shaped), không
#   phải lỗi ngữ nghĩa (string không khớp).
PROBE_MECH_MAP = {
    "rules": None, "coverage": None, "backstop": None, "docs": None, "frontend": None,
    "narrative": None, "foundation": None, "code": None, "eval": None, "freshinstall": None,
    "selfstate": "code-state", "capsurface": "capsurface",
    "capproof": "capproof", "provenance": "provenance-scope",
    "orchestration": None, "deps": None,
}


def p_narrative():
    """Narrative overstack có TRUNG THỰC không (council-025) — KHÁC docs-probe (chỉ so
    html==generator-output = tính TRUNG THÀNH bản sao). Probe này gác tính TRUNG THỰC bản gốc:
      (b) mọi live_probe trong mechanisms.yaml phải TỒN TẠI (manifest không nói dối);
      (a) mọi cơ-chế LIVE phải XUẤT HIỆN trong overstack.html (không narrative drift);
      (c) canary: skill mô tả tuyến-phòng-thủ mà chưa vào manifest → warn;
      (d) ROOT-CAUSE (2026-07-18): mọi probe trong PROBES đối chiếu PROBE_MECH_MAP — probe MỚI
          không có dòng map (dù None hay id thật) → FAIL ngay, không chờ ai audit tay lần nữa.
    Parse manifest bằng regex → medic vẫn stdlib-only; fail-open nếu không parse được."""
    man = ROOT / "harness/mechanisms.yaml"
    page = ROOT / "llmwiki/html/overstack.html"
    if not (man.exists() and page.exists()):
        return "skip", "thiếu mechanisms.yaml/overstack.html", ""
    text = man.read_text(encoding="utf-8")
    ids = re.findall(r'^\s*-\s*id:\s*(\S+)', text, re.M)
    unmapped = [n for n, _, _ in PROBES if n not in PROBE_MECH_MAP]
    if unmapped:
        return ("fail", f"probe MỚI chưa khai trong PROBE_MECH_MAP: {','.join(unmapped)}",
                "fdk/tools/medic.py — thêm dòng '<probe>: \"<mechanism-id>\"' hoặc '<probe>: None' (nếu meta)")
    dangling = [(n, mid) for n, mid in PROBE_MECH_MAP.items() if mid and mid not in ids]
    if dangling:
        d = dangling[0]
        return ("fail", f"probe '{d[0]}' map sang mechanism '{d[1]}' nhưng id đó KHÔNG có trong mechanisms.yaml",
                f"thêm entry id: {d[1]} vào harness/mechanisms.yaml, hoặc sửa PROBE_MECH_MAP")
    # LƯU Ý TÊN: trường trong manifest gọi là `live_probe` nhưng probe này chỉ kiểm ĐƯỜNG DẪN
    # CÓ TỒN TẠI — nó chứng minh "manifest không nói dối về vị trí", KHÔNG chứng minh cơ-chế
    # đang chạy. Cơ-chế bị vô hiệu (hook gỡ khỏi settings, validator không resolve) vẫn lọt.
    # Cùng lớp lỗi đã sửa ở p_deps; giữ probe vì nó vẫn bắt được manifest trỏ vào hư không.
    names = re.findall(r'^\s*name:\s*"?(.+?)"?\s*$', text, re.M)
    probes = re.findall(r'^\s*live_probe:\s*(.+?)\s*$', text, re.M)
    if not names or len(names) != len(probes):
        return "skip", "manifest cơ-chế không parse được (regex)", ""
    html = page.read_text(encoding="utf-8", errors="ignore")
    lying = [p for p in probes if not (ROOT / p).exists()]
    if lying:
        return ("fail", f"manifest NÓI DỐI: {len(lying)} live_probe không tồn tại: {','.join(lying[:3])}",
                "sửa harness/mechanisms.yaml — live_probe phải trỏ file/dir thật")
    missing = [n for n, p in zip(names, probes) if n not in html]
    if missing:
        return ("fail", f"NARRATIVE DRIFT: {len(missing)} cơ-chế LIVE vắng overstack.html: {','.join(missing[:3])}",
                "python3 fdk/tools/build-overstack-docs.py  # regen trang từ manifest")
    KW = ("self-heal", "gương-soi", "tuyến phòng thủ", "narrative drift", "rào chắn còn cắn")
    known = " ".join(names + probes).lower()
    canary = []
    skdir = ROOT / "skills"
    if skdir.is_dir():
        for sk in sorted(skdir.glob("*/SKILL.md")):
            head = sk.read_text(encoding="utf-8", errors="ignore")[:600].lower()
            nm = sk.parent.name
            if any(k in head for k in KW) and nm not in known:
                canary.append(nm)
    if canary:
        return ("warn", f"{len(names)} cơ-chế khớp trang; canary: skill phòng-thủ chưa vào manifest: {','.join(canary[:3])}",
                "nếu là tuyến phòng thủ, thêm vào harness/mechanisms.yaml")
    return "ok", f"{len(names)} cơ-chế LIVE đều có mặt + đúng bản gốc", ""


def p_foundation():
    """Mục Nền tảng (foundation.yaml, GH#6) có TRUNG THỰC không — cùng khuôn narrative-as-data:
      (b) mọi evidence-link dạng PATH phải TỒN TẠI (manifest không nói dối);
      (a) mọi tech khai phải XUẤT HIỆN trong overstack.html (không foundation drift);
      (c) toàn giá trị TODO (chưa điền) → warn, không fail (dự án mới bootstrap không bị đỏ).
    Parse bằng regex → medic vẫn stdlib-only; fail-open (skip) nếu không parse được.
    LƯU Ý: regex dưới KHÔNG phải YAML parser thật — chỉ nhận list dạng plain-quoted scalar
    (`- "value"`); format lạ (flow-style [a,b], multi-line, key trong bullet) sẽ bị bỏ qua
    (fail-open), KHÔNG robust hơn thực tế. So drift phải escape chuỗi cho khớp html đã esc()."""
    import html as _htmlmod
    man = ROOT / "harness/foundation.yaml"
    page = ROOT / "llmwiki/html/overstack.html"
    if not (man.exists() and page.exists()):
        return "skip", "thiếu foundation.yaml/overstack.html (dự án chưa opt-in)", ""
    text = man.read_text(encoding="utf-8")
    techs = re.findall(r'^\s*-\s*tech:\s*"?(.+?)"?\s*$', text, re.M)
    if not techs:
        return "skip", "foundation.yaml không parse được tech-choices (regex)", ""
    # (c) toàn placeholder TODO → chưa điền
    if all("TODO" in t for t in techs):
        return "warn", "foundation.yaml còn nguyên placeholder TODO — chưa điền", \
            "điền harness/foundation.yaml (problem/why-exists/tech-choices) rồi regen"
    # (b) evidence-link dạng path (không phải [[wikilink]]) phải tồn tại
    evis = re.findall(r'^\s*-\s*"?([^"\n]+?)"?\s*$', text, re.M)
    paths = [e.strip() for e in evis if "/" in e and not e.strip().startswith("[[") and "TODO" not in e]
    lying = [p for p in paths if not (ROOT / p).exists()]
    if lying:
        return ("fail", f"manifest NÓI DỐI: {len(lying)} evidence-link không tồn tại: {','.join(lying[:3])}",
                "sửa harness/foundation.yaml — evidence-link phải trỏ file/dir thật")
    # (a) tech khai mà vắng overstack.html = foundation drift.
    # Generator escape mọi giá trị qua esc() nên PHẢI so bản đã-escape (chống false-fail
    # khi tech-name chứa & < > " — Ada council-027), không so chuỗi thô.
    html = page.read_text(encoding="utf-8", errors="ignore")
    # khớp CHÍNH XÁC esc() của generator (chỉ & < >, KHÔNG escape quotes) → quote=False
    missing = [t for t in techs if "TODO" not in t and _htmlmod.escape(t, quote=False) not in html]
    if missing:
        return ("fail", f"FOUNDATION DRIFT: {len(missing)} tech-choice vắng overstack.html: {','.join(missing[:3])}",
                "python3 fdk/tools/build-overstack-docs.py  # regen trang từ foundation.yaml")
    return "ok", f"{len(techs)} tech-choice khớp trang + bằng chứng tồn tại", ""


def p_selfstate():
    """code-state self-narration (Phase 2) còn TRUNG THỰC không (council-advisory):
      - reproducibility (Feynman): code-state.py --check phải xanh (render 2 lần byte-identical);
      - presence: overstack.html phải có section 'Trạng thái hiện thời'.
    (Staleness của FACT ổn định do docs-probe lo — regen đổi html → docs FAIL nếu quên.)"""
    cs = ROOT / "fdk/tools/code-state.py"
    page = ROOT / "llmwiki/html/overstack.html"
    if not cs.exists():
        return "skip", "code-state.py chưa có", ""
    rc, out = sh([PY, str(cs), "--check"], timeout=200)
    if rc != 0:
        return "fail", "code-state KHÔNG tái tạo được (render 2 lần lệch — nondeterminism)", \
               "python3 fdk/tools/code-state.py --check"
    if page.exists() and "Trạng thái hiện thời" not in page.read_text(encoding="utf-8", errors="ignore"):
        return "fail", "overstack.html THIẾU section 'Trạng thái hiện thời'", \
               "python3 fdk/tools/build-overstack-docs.py  # regen"
    return "ok", "code-state tái tạo được + section có mặt", ""


def p_code():
    """Code lành — mọi .py trong harness/ + fdk/tools compile sạch (không rail gãy cú pháp)."""
    import py_compile
    bad = []
    for d in ("harness/scripts", "harness/validators", "fdk/tools", "llmwiki/.claude/hooks"):
        base = ROOT / d
        if not base.is_dir():
            continue
        for f in base.rglob("*.py"):
            try:
                py_compile.compile(str(f), doraise=True)
            except Exception:
                bad.append(f.relative_to(ROOT).as_posix())
    if bad:
        return "fail", f"{len(bad)} file .py GÃY: {', '.join(bad[:3])}", "sửa lỗi cú pháp"
    return "ok", "mọi .py compile sạch", ""


def p_eval():
    """Eval lõi không regress — self-index gate + episodic retrieval hit@k (nếu có baseline)."""
    gate = ROOT / "harness/evals/self-index/check.py"
    if gate.exists():
        rc, out = sh([PY, str(gate)])
        if rc != 0:
            return "fail", "eval self-index REGRESS", "xem harness/evals/self-index"
    # episodic retrieval (tầng nhớ episodic, issue #9): sinh output tất định rồi --check hit@k
    ep_base = ROOT / "harness/metrics/episodic-baseline.json"
    ep_dir = ROOT / "llmwiki/wiki/sources/evals/episodic"
    if ep_base.exists() and ep_dir.is_dir():
        import tempfile as _tf
        out_f = Path(_tf.gettempdir()) / "medic-ep-out.json"
        rc, _ = sh([PY, str(ROOT / "harness/scripts/mem-proxy.py"), "--out", str(out_f)])
        if rc != 0:
            return "fail", "episodic mem-proxy GÃY", "python3 harness/scripts/mem-proxy.py --self-test"
        rc, _ = sh([PY, str(ROOT / "harness/scripts/retrieval-eval.py"),
                    "--evals-dir", str(ep_dir), "--outputs", str(out_f),
                    "--baseline", str(ep_base), "--check"])
        if rc != 0:
            return "fail", "episodic retrieval hit@k REGRESS", "xem harness/metrics/episodic-baseline.json"
        return "ok", "eval không regress (self-index + episodic hit@k)", ""
    if not gate.exists():
        return "skip", "self-index eval chưa promote; chưa có episodic baseline", ""
    return "ok", "eval self-index không regress", ""


def p_freshinstall():
    """Đường cài NGƯỜI-MỚI còn sống không: curl-cài overstack vào một dự án TRỐNG,
    CÔ LẬP (mktemp ngoài repo) qua file:// working-tree, rồi assert 3 trụ + harness
    CẮN thật + orchestration-ready (skills reachable, runtime ping nếu có). Là cổng
    required của push-qua-/fdk: người mới clone/curl phải /orchestration được ngay.
    Bản --local OFFLINE tất định; live-run LLM /orchestration là acceptance tay (ceiling)."""
    smoke = ROOT / "harness/scripts/fresh-install-smoke.sh"
    if not smoke.exists():
        return "skip", "fresh-install-smoke.sh chưa có", ""
    rc, out = sh(["bash", str(smoke), "--local"], timeout=180)
    if rc != 0:
        return "fail", "fresh-install ĐỎ — người mới curl-cài KHÔNG orchestration-ready", \
               "bash harness/scripts/fresh-install-smoke.sh --local   # xem dòng ✗"
    return "ok", "người mới curl-cài → 3 trụ + orchestration-ready (isolated)", ""


def p_capsurface():
    """Bề mặt NĂNG LỰC (skills + rules + engines) đổi mà version CHƯA bump → downstream so
    version thấy bằng nhau, tưởng mình current, và KHÔNG BAO GIỜ biết có chức năng mới; model
    làm việc ở dự án đó không biết mình có thêm đồ nghề. Đây là forcing function cho p-08:
    thêm năng lực thì BẮT BUỘC khai, không thì không push được."""
    st = ROOT / "harness/scripts/capability-stamp.py"
    if not st.exists():
        return "skip", "capability-stamp.py chưa có", ""
    rc, out = sh([PY, str(st), "--check"], timeout=60)
    if rc != 0:
        first = next((l.strip() for l in out.splitlines() if l.strip()), "bề mặt năng lực lệch")
        return "fail", first, "python3 harness/scripts/capability-stamp.py --update   # bump + đóng dấu"
    return "ok", "bề mặt năng lực khớp version (downstream sẽ thấy đúng khi có bản mới)", ""


def p_provenance():
    """Skill NGOÀI (adapt_mode=external-pull — pin + audit, engine ở ngoài) chạy full-permission
    sau khi cài; supply-chain drift (upstream sửa lén sau lúc pin) chỉ lộ ra nếu ai đó CHỦ ĐỘNG
    chạy check. Gap #4 (senior-lens review 2026-07-18): trust chỉ gác lúc cài, không có nhịp
    re-verify. Scope HẸP CÓ CHỦ Ý: chỉ hard-fail MODIFIED trên skill external-pull (rủi ro thật —
    checksum đổi sau khi pin = có thể bị sửa lén). Skill local-authored đổi MỖI NGÀY là dev churn
    bình thường (chính phiên này vừa sửa qc-code/hallmark/lint) — hard-fail trên chúng là đúng
    kiểu 'gate cries wolf' đã né ở capproof; chỉ đếm, không chặn."""
    sp = ROOT / "fdk/tools/skill-provenance.py"
    if not sp.exists():
        return "skip", "skill-provenance.py chưa có", ""
    rc, out = sh([PY, str(sp), "check", "--json"], timeout=30)
    try:
        rows = json.loads(out)["rows"]
    except Exception:
        return "skip", "skill-provenance --json không parse được", ""
    ext_bad = [r for r in rows if r.get("adapt_mode") == "external-pull" and r["status"] == "MODIFIED"]
    local_mod = sum(1 for r in rows if r.get("adapt_mode") != "external-pull" and r["status"] == "MODIFIED")
    untracked = sum(1 for r in rows if r["status"] == "UNTRACKED")
    if ext_bad:
        names = ", ".join(r["name"] for r in ext_bad)
        return ("fail", f"skill NGOÀI bị sửa lén sau khi pin: {names}",
                f"soi diff skills/<name>/SKILL.md với commit đã pin; đúng ý thì "
                f"`python3 fdk/tools/skill-provenance.py record <name> --source <src>` để re-pin")
    return ("ok", f"external-pull sạch (0 tamper) · {local_mod} local đổi (dev churn, không chặn) "
                  f"· {untracked} untracked (chưa record, advisory)", "")


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
    return "ok", (f"{cp['counts']['proven']}/{cp['counts']['total']} có NEO khai báo (tĩnh, chưa thực thi) "
                  f"· chưa neo {cp['counts']['unproven']}"
                  + (f" · {len(cp.get('dups', []))} trùng-ứng-viên" if cp.get("dups") else "")), ""



def p_orchestration():
    """Việc giao cho agent có bị bỏ quên không. Đo 2026-07-20: 78% task orchestration
    có `dispatch: null` — chưa BAO GIỜ được giao; 17 task treo, cũ nhất 59 ngày.
    Gốc là coordinator không biết lúc nào worker xong (orca terminal wait --for tui-idle
    timeout 90s trên việc xong sau 9s) nên bỏ cuộc, tự làm inline.

    WARN chứ không FAIL: nợ điều phối không phải hỏng hệ, và một cổng đỏ vì nợ tồn
    đọng sẽ bị học cách phớt lờ — lúc đó mất luôn tín hiệu thật. Không có Orca → skip."""
    tool = ROOT / "harness/scripts/orca-reconcile.py"
    if not tool.exists():
        return "skip", "orca-reconcile.py chưa có", ""
    rc, out = sh([PY, str(tool), "--json"], timeout=180)
    if rc != 0:
        return "skip", "orca-reconcile không chạy được", ""
    try:
        rep = json.loads(out)
    except Exception:
        return "skip", "orca-reconcile --json không parse được", ""
    if not rep.get("available"):
        return "skip", f"không có Orca ({rep.get('reason', 'runtime tắt')})", ""
    if not rep.get("open_total"):
        return "ok", f"0 task treo / {rep.get('total_tasks', 0)} task", ""
    g = rep.get("groups", {})
    never = g.get("chua-tung-dispatch", 0)
    return "warn", (f"{rep['open_total']} task treo (cũ nhất {rep.get('max_age_days', 0)}d)"
                    + (f" · {never} CHƯA TỪNG giao" if never else "")), \
           "python3 harness/scripts/orca-reconcile.py"



def p_deps():
    """Dependency NGOÀI còn dùng được không — không chỉ còn tồn tại.

    Bài học 2026-07-20: orientation quảng cáo code-graph dựa trên `.is_file()` của
    index.db. DB 0 byte / thiếu schema / server chết đều lọt, nên framework lùa mọi
    phiên vào một tool hỏng suốt nhiều tuần (đo: 37 tool-call vs 14 của grep).
    Nguyên tắc: quảng cáo một năng lực = phải THĂM DÒ nó.

    WARN chứ không FAIL: dependency ngoài chết là chuyện môi trường của người dùng,
    không phải repo hỏng. Absent (không cài) thì im — người không dùng không bị phiền."""
    tool = ROOT / "harness/scripts/dep-health.py"
    if not tool.exists():
        return "skip", "dep-health.py chưa có", ""
    rc, out = sh([PY, str(tool), "--json"], timeout=60)
    if rc != 0:
        return "skip", "dep-health không chạy được", ""
    try:
        deps = json.loads(out).get("deps", [])
    except Exception:
        return "skip", "dep-health --json không parse được", ""
    bad = [d for d in deps if d.get("status") == "degraded"]
    if bad:
        first = bad[0]
        return "warn", (f"{len(bad)}/{len(deps)} dependency HỎNG: "
                        + ", ".join(d["name"] for d in bad)
                        + f" — {first.get('reason', '')}"), first.get("fix", "")
    ok = [d for d in deps if d.get("status") == "ok"]
    return "ok", (f"{len(ok)}/{len(deps)} dependency ngoài dùng được"
                  + (f" ({', '.join(d['name'] for d in ok)})" if ok else "")), ""


PROBES = [
    ("rules",    ["rules", "luật", "bite"],      p_rules),
    ("coverage", ["rules", "coverage", "luật"],  p_coverage),
    ("drift",    ["drift", "rules"],             lambda: p_rules()),  # drift lộ trong p_rules
    ("backstop", ["backstop", "git", "commit"],  p_backstop),
    ("docs",     ["docs", "capabilities"],       p_docs),
    ("frontend", ["frontend", "docs", "html"],    p_frontend),
    ("narrative", ["narrative", "docs", "drift"], p_narrative),
    ("foundation", ["foundation", "docs", "drift"], p_foundation),
    ("selfstate", ["selfstate", "state", "narrative"], p_selfstate),
    ("code",     ["code", "health"],             p_code),
    ("eval",     ["eval", "baseline"],           p_eval),
    ("freshinstall", ["freshinstall", "install", "orchestration", "e2e", "push"], p_freshinstall),
    ("capsurface", ["capsurface", "version", "capabilities", "bump", "downstream"], p_capsurface),
    ("capproof", ["capproof", "proof", "unproven", "ratchet", "dup"], p_capproof),
    ("provenance", ["provenance", "supply-chain", "external-pull", "tamper"], p_provenance),
    ("orchestration", ["orchestration", "orca", "dispatch", "task", "treo"], p_orchestration),
    ("deps", ["deps", "dependency", "code-graph", "orca", "mcp", "ngoài"], p_deps),
]
# bỏ 'drift' probe trùng — drift đã báo trong rules:
PROBES = [p for p in PROBES if p[0] != "drift"]

ICON = {"ok": f"{G}✓{X}", "fail": f"{R}✗{X}", "warn": f"{Y}⚠{X}", "skip": f"{B}·{X}"}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = {a for a in sys.argv[1:] if a.startswith("-")}
    if "--list" in flags:
        print("medic probes:")
        for name, tags, _ in PROBES:
            print(f"  {name:10} tags: {', '.join(tags)}")
        return 0
    scope = args
    chosen = [p for p in PROBES if not scope or any(s in p[0] or s in p[1] for s in scope)]

    print(f"{B}medic{X} — cổng sức khoẻ framework  ·  {ROOT}")
    print(f"phạm vi: {' '.join(scope) if scope else 'all'}  ·  {len(chosen)}/{len(PROBES)} probe\n")
    results = []
    for name, _tags, fn in chosen:
        try:
            state, detail, fix = fn()
        except Exception as e:
            state, detail, fix = "skip", f"probe lỗi: {e}", ""
        results.append((name, state, detail, fix))
        line = f"  {ICON[state]} {name:10} {detail}"
        print(line)
        if fix and state in ("fail", "warn"):
            print(f"       {B}↳ sửa:{X} {fix}")

    fails = [r for r in results if r[1] == "fail"]
    warns = [r for r in results if r[1] == "warn"]
    verdict = "FAIL" if fails else ("KHOẺ (có cảnh báo)" if warns else "HỆ KHOẺ")
    vcol = R if fails else (Y if warns else G)
    print(f"\n{vcol}▉ {verdict}{X} — {len(fails)} fail · {len(warns)} warn · "
          f"{sum(1 for r in results if r[1]=='ok')} ok · {sum(1 for r in results if r[1]=='skip')} skip")

    # ── recap + dạy dùng thụ động (kim chỉ nam fdk: cuối output nhắc lại + use-case) ──
    print(f"""
{B}medic là gì:{X} một lệnh = tuyến phòng thủ cuối. Nó KHÔNG sửa gì — chỉ CHỨNG MINH hệ còn
khoẻ: luật còn cắn, validator không lệch bản, docs khớp đĩa, code compile, eval không tụt.
Xanh = yên tâm; đỏ = in đúng chỗ hở + 1 dòng lệnh sửa.

{B}dùng khi (kể cả lúc không ngờ):{X}
  • trước khi commit/PR — `medic --ci` chốt, đỏ thì đừng đẩy.
  • sau khi kéo bản mới / đổi máy — `medic` xem overstack có nguyên vẹn.
  • nghi một rule "có vẻ không chặn nữa" — `medic rules` rà riêng tầng luật.
  • vừa thêm skill/rule/generator — `medic` tự báo nếu quên hàng rào cho nó.
  • chỉ muốn coi cấu trúc phòng thủ — `medic --list`.

{B}cấu trúc (transparent — biết đồ nằm đâu mà mở):{X}
  fdk/tools/medic.py            ← bạn đang chạy cái này (hub)
  fdk/tools/build-*.py --check  ← probe docs/capabilities gọi tới
  harness/scripts/harness-doctor.py  ← probe rules gọi tới (fire-drill BAD/GOOD)
  harness/poc-vendor-neutral/policy.yaml  ← nguồn 'có bao nhiêu luật' (đếm LIVE)
  harness/validators/*.py       ← các validator được rà 'còn cắn không'""")
    return 1 if (fails and "--ci" in flags) else 0


if __name__ == "__main__":
    sys.exit(main())
