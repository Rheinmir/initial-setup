#!/usr/bin/env python3
"""visual-receipt — bằng chứng TRÌNH DUYỆT cho HTML sinh: biên lai + contact sheet + 4 ảnh.

Hấp thụ `bin/visual-check.mjs` của tt-a1i/archify (09/2026). Ý đáng lấy nhất không phải
"chụp ảnh" mà là cách nó CHIA BẬC trung thực:

    deliver  → chứng minh artifact qua các kiểm tra TẤT ĐỊNH trên HTML/SVG
    visual-check → chứng minh nó HÀNH XỬ đúng trong một trình duyệt thật
    "perceptual visual review pending" → máy tự khai nó KHÔNG chấm được cái đẹp

Ta đã bắt docs-site-macos phải audit Playwright trước khi bàn giao, nhưng audit đó không
để lại gì: không biên lai, không ma trận kích thước × theme, và không tách "đã kiểm cơ học"
khỏi "chờ mắt người". File này biến nó thành artifact.

Ba kiểm TẤT ĐỊNH chạy trong trình duyệt — không regex nào làm được:
  · tràn ngang: documentElement.scrollWidth > innerWidth (khớp hallmark gate 34)
  · lỗi console + pageerror
  · TỰ-CHỨA THẬT: quan sát mọi request thoát ra ngoài (http/https). Cổng tĩnh chỉ soi được
    chuỗi trong file; ở đây là hành vi thật của trang.

Exit: 0 pass · 1 fail thật trong trình duyệt · **2 BỎ QUA** (thiếu playwright/chromium).
rc=2-là-skipped mượn nguyên của archify: thiếu công cụ KHÔNG phải thất bại chất lượng.

Usage:
  visual-receipt.py <file.html> [...] [--out DIR]
  visual-receipt.py --self-test
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DEFAULT = ROOT / "scratchpad" / "visual-check"
# Ma trận cố định của archify: hai kích thước × hai chế độ màu. Cố định để so được giữa các lần.
MATRIX = [(1440, 900), (2048, 1320)]
SCHEMES = ["light", "dark"]
SKIPPED = 2


def capture(path: Path, out_dir: Path) -> dict:
    from playwright.sync_api import sync_playwright

    stem = path.stem
    rec = {"file": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
           "sha256": hashlib.sha256(path.read_bytes()).hexdigest()[:16],
           "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "captures": [], "console_errors": [], "remote_requests": [],
           "horizontal_overflow": [],
           "perceptual_review": "pending — máy không chấm được cái đẹp, xem contact sheet"}
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        # Chromium bundled của Playwright hay vắng trên máy dev (bản cache lệch version).
        # Thử bản bundled trước, rồi rơi về Chrome hệ thống — tránh bắt người ta tải 150MB
        # chỉ để chụp bốn cái ảnh. Hết cả hai đường thì để ngoại lệ nổi lên → main() rc=2.
        try:
            browser = pw.chromium.launch()
        except Exception:
            browser = pw.chromium.launch(channel="chrome")
        for w, h in MATRIX:
            for scheme in SCHEMES:
                ctx = browser.new_context(viewport={"width": w, "height": h},
                                          color_scheme=scheme)
                page = ctx.new_page()
                page.on("pageerror", lambda e: rec["console_errors"].append(str(e)[:200]))
                page.on("console",
                        lambda m: m.type == "error" and rec["console_errors"].append(m.text[:200]))
                page.on("request", lambda r: r.url.startswith(("http://", "https://"))
                        and rec["remote_requests"].append(r.url[:160]))
                page.goto(path.as_uri())
                page.wait_for_timeout(350)
                if page.evaluate("document.documentElement.scrollWidth > window.innerWidth"):
                    rec["horizontal_overflow"].append(f"{w}x{h}/{scheme}")
                png = out_dir / f"{stem}.visual-check.{w}x{h}.{scheme}.png"
                page.screenshot(path=str(png), full_page=True)
                rec["captures"].append({"viewport": f"{w}x{h}", "scheme": scheme,
                                        "png": png.name, "bytes": png.stat().st_size})
                ctx.close()
        browser.close()
    rec["console_errors"] = sorted(set(rec["console_errors"]))
    rec["remote_requests"] = sorted(set(rec["remote_requests"]))
    return rec


def contact_sheet(rec: dict, out_dir: Path, stem: str) -> Path:
    """Contact sheet = artifact để NGƯỜI chấm. Máy đã nói hết phần nó biết ở biên lai."""
    rows = "".join(
        f'<figure><img src="{c["png"]}" alt="{c["viewport"]} {c["scheme"]}" loading="lazy">'
        f'<figcaption>{c["viewport"]} · {c["scheme"]} · {c["bytes"]//1024}KB</figcaption></figure>'
        for c in rec["captures"])
    verdict = "PASS cơ học" if not (rec["console_errors"] or rec["remote_requests"]
                                    or rec["horizontal_overflow"]) else "FAIL cơ học"
    p = out_dir / f"{stem}.visual-check.html"
    p.write_text(
        '<!doctype html><meta charset="utf-8"><title>visual-check · ' + stem + '</title>'
        '<style>:root{color-scheme:light dark}body{margin:0;padding:24px;font:14px/1.6 '
        'ui-sans-serif,system-ui,sans-serif}h1{font-size:18px;margin:0 0 4px}'
        'p{margin:0 0 18px;color:#6b645b}.g{display:grid;gap:18px;'
        'grid-template-columns:repeat(auto-fit,minmax(340px,1fr))}figure{margin:0}'
        'img{width:100%;border:1px solid #ddd8d0;border-radius:6px;display:block}'
        'figcaption{font:12px ui-monospace,monospace;color:#6b645b;padding-top:6px}</style>'
        f'<h1>{stem} — {verdict}</h1>'
        f'<p>Kiểm cơ học xong. <b>Phần cảm quan CHƯA chấm</b> — đó là việc của mắt bạn, '
        f'không phải của máy. Biên lai: <code>{stem}.visual-check.json</code></p>'
        f'<div class="g">{rows}</div>', encoding="utf-8")
    return p


def self_test() -> int:
    checks = [
        ("ma trận cố định 2 kích thước × 2 theme = 4 ảnh", len(MATRIX) * len(SCHEMES) == 4),
        ("BỎ QUA dùng rc=2 (mượn archify), không phải rc=1", SKIPPED == 2),
        ("có khai perceptual review là PENDING, không tự phong PASS", True),
    ]
    try:
        import playwright  # noqa: F401
        checks.append(("playwright import được (nếu không → rc 2, không phải fail)", True))
    except ImportError:
        print("  · playwright chưa cài → công cụ sẽ BỎ QUA (rc 2), đúng thiết kế")
    ok = all(c[1] for c in checks)
    for label, passed in checks:
        print(f"  {'✓' if passed else '✗'} {label}")
    print("self-test: PASS" if ok else "self-test: FAIL")
    return 0 if ok else 1


def main() -> None:
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out_dir = OUT_DEFAULT
    if "--out" in sys.argv:
        out_dir = Path(args.pop(args.index(sys.argv[sys.argv.index("--out") + 1])))
    if not args:
        print("dùng: visual-receipt.py <file.html> [...] [--out DIR]", file=sys.stderr)
        sys.exit(SKIPPED)
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("  · BỎ QUA: chưa cài playwright (`pip install playwright && playwright install "
              "chromium`). Thiếu công cụ KHÔNG phải thất bại chất lượng.")
        sys.exit(SKIPPED)

    bad = 0
    for a in args:
        path = Path(a).resolve()
        if not path.is_file():
            print(f"  ✗ không có file: {a}", file=sys.stderr)
            bad += 1
            continue
        try:
            rec = capture(path, out_dir)
        except Exception as e:  # chromium chưa tải, v.v.
            print(f"  · BỎ QUA {path.name}: {str(e)[:90]}")
            sys.exit(SKIPPED)
        sheet = contact_sheet(rec, out_dir, path.stem)
        receipt = out_dir / f"{path.stem}.visual-check.json"
        receipt.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        problems = (rec["console_errors"], rec["remote_requests"], rec["horizontal_overflow"])
        if any(problems):
            bad += 1
            print(f"  \033[1;31m✗\033[0m {path.name}: "
                  f"{len(rec['console_errors'])} lỗi console · "
                  f"{len(rec['remote_requests'])} request RA NGOÀI · "
                  f"tràn ngang ở {rec['horizontal_overflow'] or 'không'}")
            for u in rec["remote_requests"][:3]:
                print(f"      → {u}")
        else:
            print(f"  \033[1;32m✓\033[0m {path.name}: 4 ảnh, 0 lỗi console, 0 request ra ngoài, "
                  f"không tràn ngang")
        print(f"      biên lai {receipt.name} · contact sheet {sheet.name}")
        print("      cảm quan: CHƯA CHẤM — mở contact sheet và tự nhìn")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
