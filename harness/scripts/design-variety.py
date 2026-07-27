#!/usr/bin/env python3
"""design-variety — cổng Variety travel-được (tất định, 0 token).

Chưng cất từ hallmark: `.hallmark/log.json` + slop-test gate 8 + trục F (Variety).
Mỗi HTML ta sinh nên stamp macrostructure/theme của nó vào một comment:

    <!-- design: macrostructure=<tên> theme=<tên> -->

Script này đọc stamp đó từ các trang trong một thư mục (hoặc từ design-log), và
BÁO khi một trang mới LẶP cấu trúc trang trước — structural distance, KHÔNG phải
colour-swap. Đây là thứ đưa slop-test từ một-lần thành cưỡng-chế-xuyên-phiên,
không nhờ model nhớ.

Log travel-được (theo repo, append-only): `llmwiki/html/.design-log.jsonl`
mỗi dòng `{date, file, macrostructure, theme, brief}`. Đồng dạng các .jsonl ledger khác.

BÁO CÁO, KHÔNG CHẶN — chất lượng, không phải an toàn.

Dùng:
  design-variety.py                    # quét stamp trong llmwiki/html/*.html
  design-variety.py --log              # đọc .design-log.jsonl thay vì stamp
  design-variety.py --stamp <file> --macro <M> --theme <T> --brief "<...>"  # ghi 1 dòng log
  design-variety.py --json
"""
import argparse
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML_DIR = ROOT / "llmwiki" / "html"
LOG = HTML_DIR / ".design-log.jsonl"
STAMP = re.compile(r"<!--\s*design:\s*macrostructure=(\S+)\s+theme=(\S+)\s*-->", re.I)


def read_stamps(html_dir):
    """Đọc stamp macrostructure từ mỗi *.html (bỏ *-seq.html? KHÔNG — chúng cũng là artifact)."""
    rows = []
    for f in sorted(glob.glob(str(html_dir / "*.html"))):
        t = Path(f).read_text(encoding="utf-8", errors="ignore")
        m = STAMP.search(t)
        rows.append({"file": Path(f).name,
                     "macrostructure": m.group(1) if m else None,
                     "theme": m.group(2) if m else None})
    return rows


def read_log(log):
    if not log.is_file():
        return []
    return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]


def report(rows):
    stamped = [r for r in rows if r.get("macrostructure")]
    unstamped = [r for r in rows if not r.get("macrostructure")]
    # đếm mỗi macrostructure xuất hiện bao nhiêu lần → lặp = variety kém
    from collections import Counter
    c = Counter(r["macrostructure"] for r in stamped)
    repeats = {k: n for k, n in c.items() if n > 1}
    return stamped, unstamped, repeats


def self_test() -> int:
    """Tất định: 2 trang cùng macrostructure phải bị BÁO lặp, trang khác không."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        hd = Path(d)
        for name, macro in (("a.html", "hero-grid"), ("b.html", "hero-grid"), ("c.html", "broadsheet")):
            (hd / name).write_text(f"<!-- design: macrostructure={macro} theme=t1 -->", encoding="utf-8")
        stamped, unstamped, repeats = report(read_stamps(hd))
        ok = len(stamped) == 3 and not unstamped and repeats == {"hero-grid": 2}
    print("design-variety self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--stamp", help="ghi 1 dòng vào design-log cho file này")
    ap.add_argument("--macro", default="")
    ap.add_argument("--theme", default="")
    ap.add_argument("--brief", default="")
    ap.add_argument("--date", default="", help="YYYY-MM-DD (không có Date.now trong CI)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())

    if a.stamp:
        rec = {"date": a.date, "file": a.stamp, "macrostructure": a.macro,
               "theme": a.theme, "brief": a.brief}
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"✓ design-log += {a.stamp} [{a.macro}/{a.theme}]")
        sys.exit(0)

    rows = read_log(LOG) if a.log else read_stamps(HTML_DIR)
    stamped, unstamped, repeats = report(rows)

    if a.json:
        print(json.dumps({"stamped": len(stamped), "unstamped": len(unstamped),
                          "repeats": repeats}, ensure_ascii=False, indent=2))
        sys.exit(0)

    print(f"design-variety · {len(stamped)} trang có stamp, {len(unstamped)} chưa stamp")
    if repeats:
        print("  ⚠ macrostructure LẶP (variety kém — colour-swap của cùng fingerprint):")
        for k, n in sorted(repeats.items(), key=lambda x: -x[1]):
            print(f"    {k}: {n} trang")
    if unstamped and not a.log:
        print(f"  {len(unstamped)} trang chưa stamp `<!-- design: macrostructure=… theme=… -->` "
              f"→ cổng Variety mù với chúng. (Bao gồm các *-seq.html hiện dùng CÙNG một glass template — "
              f"theo trục Variety chúng LÀ slop; đây là nợ đã biết, xem [[design-foundation]].)")
    print("\nBÁO CÁO, không chặn. Trang mới nên dùng macrostructure KHÁC trang trước (structural distance).")
    sys.exit(0)


if __name__ == "__main__":
    main()
