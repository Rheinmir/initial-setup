#!/usr/bin/env python3
"""evidence_leaf — mot nut co phai DIEM CUOI hop le khong (R19 evidence-terminal).

KHONG co CLI, KHONG doc file cau hinh: harness/scripts/grounding-check.py nhap lai module nay
de dung CHUNG mot bo luat diem cuoi. Hai ban luat song song ve cung mot khai niem chac chan se
lech nhau sau vai thang, nen o day chi co MOT ban.
"""
import importlib.util
from pathlib import Path

EVIDENCE_KINDS = frozenset({
    "observed", "tool-record", "graph-edge", "web", "parametric", "absence",
})

_resolve = None


def _claim_receipts_resolve():
    """claim-receipts.py co DAU GACH NGANG trong ten -> `import claim_receipts` KHONG chay duoc.
    Phai nap qua importlib tu duong dan file. Nap lazy + cache o module-level."""
    global _resolve
    if _resolve is None:
        p = Path(__file__).resolve().parents[1] / "scripts" / "claim-receipts.py"
        spec = importlib.util.spec_from_file_location("claim_receipts", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _resolve = mod.resolve
    return _resolve


def check_leaf(node, root: Path, cfg: dict):
    """Tra (ok, ly_do). Nut la ma kind khong phai loai chung cu -> tu choi."""
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
    """Luat o TANG CHUOI, khong phai tang nut. Task 3 cai luat parametric o day."""
    return True, ""
