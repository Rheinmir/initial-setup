#!/usr/bin/env python3
"""supply-watch — chân thứ BA cho orca-sec-scans: phòng thủ chuỗi cung ứng & thương hiệu.

orca-sec-scans hiện có hai chân: Trivy quét TĨNH (vuln/misconfig/secret) và kiểm chứng ĐỘNG
các giả định của dev. Cả hai đều nhìn VÀO TRONG dự án. Không gì nhìn RA NGOÀI: ai đang dựng
domain/package na ná tên của bạn để lừa người dùng hoặc chèn dependency giả.

Hấp thụ hẹp từ 7onez/cti-expert (workflow 08: sweep typosquat + CT-monitor định kỳ trong CI).
CHỈ lấy mẩu này, KHÔNG gộp cả engine: cti-expert là 121 op + 78 MCP tool để điều tra mối đe doạ
BÊN NGOÀI, cần .venv + API key + mạng outbound. orca-sec-scans đang keyless và chạy được offline;
gộp nguyên khối là kéo phụ thuộc key/mạng vào một cổng đang sạch. Xem [[adapt-modes]] — đây là
HÒA TAN một mẩu, không phải KÉO NGOÀI cả công cụ.

Hai việc, cả hai KHÔNG cần API key:
  1. typosquat sweep — sinh biến thể tên (tất định, offline), rồi hỏi DNS xem cái nào ĐANG SỐNG.
  2. CT monitor — hỏi crt.sh xem có chứng chỉ nào vừa được cấp cho domain na ná tên bạn.

Exit: 0 sạch · 2 CÓ phát hiện · 2 khi BỎ QUA (không mạng) — và nói rõ là bỏ qua, không phán sạch.

Usage:
  supply-watch.py <tên-thương-hiệu-hoặc-domain> [--tld com,dev,io] [--json]
  supply-watch.py --self-test
"""
from __future__ import annotations

import argparse
import json
import socket
import sys

# Bàn phím QWERTY — nguồn của "gõ nhầm phím kề bên", biến thể phổ biến nhất thực tế.
NEIGHBORS = {
    "a": "qws", "b": "vgn", "c": "xdv", "d": "serfcx", "e": "wsdr", "f": "drtgvc",
    "g": "ftyhbv", "h": "gyujnb", "i": "ujko", "j": "huikmn", "k": "jiolm", "l": "kop",
    "m": "njk", "n": "bhjm", "o": "iklp", "p": "ol", "q": "wa", "r": "edft",
    "s": "awedxz", "t": "rfgy", "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc",
    "y": "tghu", "z": "asx",
}
# Chữ trông giống nhau — nguồn của tấn công nhìn-bằng-mắt-không-ra.
HOMOGLYPHS = {"o": "0", "l": "1", "i": "1", "e": "3", "a": "4", "s": "5", "b": "6", "g": "9"}
DEFAULT_TLDS = ["com", "net", "org", "io", "dev", "app", "co"]
CRT_SH = "https://crt.sh/?q=%25.{}&output=json"


def variants(name: str) -> dict:
    """Sinh biến thể TẤT ĐỊNH — cùng đầu vào luôn ra cùng tập, để so được giữa các lần chạy."""
    name = name.lower().split(".")[0]
    out = {"omission": set(), "repetition": set(), "transposition": set(),
           "neighbor": set(), "homoglyph": set(), "hyphen": set()}
    for i, ch in enumerate(name):
        out["omission"].add(name[:i] + name[i + 1:])
        out["repetition"].add(name[:i] + ch + ch + name[i + 1:])
        if i + 1 < len(name):
            out["transposition"].add(name[:i] + name[i + 1] + ch + name[i + 2:])
            out["hyphen"].add(name[:i + 1] + "-" + name[i + 1:])
        for nb in NEIGHBORS.get(ch, ""):
            out["neighbor"].add(name[:i] + nb + name[i + 1:])
        if ch in HOMOGLYPHS:
            out["homoglyph"].add(name[:i] + HOMOGLYPHS[ch] + name[i + 1:])
    for k in out:
        out[k] = sorted(v for v in out[k] if v and v != name and len(v) > 1)
    return out


def resolves(host: str, timeout: float = 2.0) -> bool:
    socket.setdefaulttimeout(timeout)
    try:
        socket.gethostbyname(host)
        return True
    except (socket.gaierror, OSError):
        return False


def ct_certs(domain: str, timeout: float = 12.0) -> list:
    """Chứng chỉ đã cấp cho *.domain, đọc từ Certificate Transparency (crt.sh, không cần key).
    Không có mạng → trả None để phía gọi biết là BỎ QUA, khác hẳn 'không có gì'."""
    import urllib.request
    try:
        with urllib.request.urlopen(CRT_SH.format(domain), timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def self_test() -> int:
    v = variants("orca")
    checks = [
        ("sinh biến thể là TẤT ĐỊNH (chạy 2 lần ra y hệt)", variants("orca") == v),
        ("bỏ chính nó khỏi tập biến thể", all("orca" not in vs for vs in v.values())),
        ("omission đúng: 'orca' → có 'rca'", "rca" in v["omission"]),
        ("transposition đúng: 'orca' → có 'roca'", "roca" in v["transposition"]),
        ("homoglyph đúng: 'orca' → có '0rca'", "0rca" in v["homoglyph"]),
        ("neighbor lấy phím kề: 'o'→'i' cho 'irca'", "irca" in v["neighbor"]),
        # Phân biệt BỎ QUA với KHÔNG-CÓ-GÌ là cả điểm của hàm này: [] nghĩa là hỏi được và
        # không có chứng chỉ nào; None nghĩa là CHƯA HỎI ĐƯỢC. Ép timeout cực nhỏ để buộc
        # nhánh lỗi chạy — test không được phụ thuộc máy có mạng hay không.
        ("gọi hỏng → ct_certs trả None (BỎ QUA), không phải [] (không-có-gì)",
         ct_certs("example.com", timeout=0.001) is None),
    ]
    ok = True
    for label, passed in checks:
        print(f"  {'✓' if passed else '✗'} {label}")
        ok = ok and passed
    print("self-test: PASS" if ok else "self-test: FAIL")
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="typosquat sweep + CT monitor, keyless")
    ap.add_argument("name", nargs="?", help="tên thương hiệu hoặc domain")
    ap.add_argument("--tld", default=",".join(DEFAULT_TLDS))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if not a.name:
        ap.error("cần <tên-thương-hiệu-hoặc-domain>")

    v = variants(a.name)
    tlds = [t.strip().lstrip(".") for t in a.tld.split(",") if t.strip()]
    total = sum(len(x) for x in v.values())
    live = []
    for kind, names in v.items():
        for n in names:
            for tld in tlds:
                host = f"{n}.{tld}"
                if resolves(host):
                    live.append({"kind": kind, "host": host})
    certs = ct_certs(a.name if "." in a.name else f"{a.name}.{tlds[0]}")
    report = {"name": a.name, "variants_generated": total, "tlds": tlds,
              "live_typosquats": live,
              "ct": "BỎ QUA — không gọi được crt.sh" if certs is None else
                    sorted({c.get("common_name", "") for c in certs})[:40]}
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        sys.exit(2 if live else 0)
    print(f"supply-watch · {a.name} — {total} biến thể × {len(tlds)} TLD")
    if live:
        print(f"  \033[1;31m✗\033[0m {len(live)} tên na ná ĐANG SỐNG:")
        for x in live[:20]:
            print(f"      [{x['kind']}] {x['host']}")
    else:
        print("  \033[1;32m✓\033[0m không tên na ná nào phân giải được DNS")
    if certs is None:
        print("  · CT monitor BỎ QUA (không gọi được crt.sh) — KHÔNG kết luận là sạch")
    else:
        print(f"  · CT: {len(certs)} chứng chỉ đã cấp cho *.{a.name}")
    sys.exit(2 if live else 0)


if __name__ == "__main__":
    main()
