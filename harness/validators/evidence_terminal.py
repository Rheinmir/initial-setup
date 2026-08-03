#!/usr/bin/env python3
"""evidence_terminal — R19: moi duong di tu ket luan xuong la phai ket thuc o nut CHUNG CU.

Chuoi "A vi B vi chung cu C" hop le. Chuoi "A vi B vi C" ma C lai la mot suy luan nua thi
CHUA xong — phai khai tiep C dua tren cai gi. Bat hinh dang chuoi thi tat dinh va re; bat noi
dung tung menh de thi khong. Luat nay gac hinh dang.

  --check FILE            doc khoi ```evidence-chain trong FILE, validate. FILE='-' doc stdin.
  --no-evidence-chain     tat luat cho DUNG mot lan chay (uu tien cao nhat).
  --self-test             kiem tra tat dinh, khong doc file ngoai.
  --root DIR              goc repo (mac dinh: suy tu vi tri file nay).

Cong tac BA TANG, uu tien tu HEP toi RONG:
  co --no-evidence-chain  >  env OVERSTACK_EVIDENCE_TERMINAL  >  config enabled
Tat o BAT KY tang nao van IN mot dong len stderr noi ro tang nao da tat. Mot co che im lang
luc khong hoat dong se bi nham la dang hoat dong — cong cam nguy hiem hon cong do.

Exit code (BA gia tri PHAN BIET — mot cong chi coi 0 la "da cham va hop le"):
  0 = chuoi hop le, HOAC luat dang tat, HOAC tai lieu khong khai chuoi
  2 = doc duoc nhung chuoi/schema sai
  3 = ha tang loi — KHONG doc duoc FILE. KHONG dung return 0 o day: mot cong chi check rc==0
      se khong phan biet duoc "chua ai cham" voi "da cham PASS" (bai hoc grounding-check.py).
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
    if raw is not None and str(raw).strip().lower() in ("0", "false", "off"):
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
    except Exception as e:  # noqa: BLE001 — bat rong co chu y: yaml nem nhieu loai
        return None, f"khoi evidence-chain khong parse duoc: {e}"
    if not isinstance(nodes, list) or not nodes:
        return None, "khoi evidence-chain phai la mot danh sach khong rong"
    for n in nodes:
        if not isinstance(n, dict) or not n.get("id"):
            return None, f"nut thieu 'id' hoac khong phai mapping: {n!r}"
    return nodes, None


def validate_chain(nodes, root: Path, cfg: dict):
    """Duyet MOI duong tu goc toi la. Tra (ok, ly_do).

    Goc = nut khong bi nut nao tro toi qua 'because'. Mot chuoi vong tron khong co goc nao,
    nen fallback lay nut dau tien de van bat duoc vong (khong im lang bo qua)."""
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
            ok, why = check_leaf_cached(node, root, cfg)
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


def check_leaf_cached(node, root, cfg):
    return evidence_leaf.check_leaf(node, root, cfg)


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

    for f in fails:
        print("FAIL:", f)
    print("self-test:", "PASS" if not fails else f"{len(fails)} FAIL")
    return 0 if not fails else 2


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
