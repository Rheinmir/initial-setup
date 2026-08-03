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
    if kind == "web":
        # Link phai tro DUNG CHO da doc, khong phai trang chu. Doan trich la thu dong bang
        # noi dung ma ket luan that su dua vao — trang web doi, doan trich thi khong.
        url = str(ev.get("url") or "")
        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "web phai co 'url' tuyet doi (http:// hoac https://)"
        if not ev.get("accessed"):
            return False, "web phai co 'accessed' — ngay truy cap"
        if not str(ev.get("quote") or "").strip():
            return False, "web phai co 'quote' — trich nguyen van doan duoc dua vao"
        return True, ""
    if kind == "parametric":
        # Loai DUY NHAT khong xem duoc. Khong cam, nhung bat no LO DIEN.
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


def chain_level_check(leaves):
    """Luat o TANG CHUOI, khong phai tang nut.

    parametric la loai DUY NHAT khong xem duoc — no khong duoc lam diem cuoi duy nhat cua mot
    chuoi dan toi quyet dinh. Cho phep no dung mot minh la mo cua hau hop thuc hoa phong doan:
    ket luan luc do tua hoan toan vao tri nho cua model, khong co mot mo neo nao ngoai doi thuc."""
    if not leaves:
        return False, "chuoi khong co la nao — khong cham duoc chung cu"
    if all(n.get("kind") == "parametric" for n in leaves):
        return False, ("moi la deu la 'parametric' — ket luan dang tua hoan toan vao tri nho cua "
                       "model. Nang mot la len 'web' (co link) hoac 'observed' (co file/lenh).")
    return True, ""
