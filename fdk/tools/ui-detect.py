#!/usr/bin/env python3
"""ui-detect — mượn 61 luật UI tất định của impeccable, OPT-IN, không kéo dep vào medic.

Vì sao KÉO NGOÀI chứ không HÒA TAN (xem [[adapt-modes]]): `frontend-antipattern.py` của ta
có 9 luật, tự viết, offline, chạy trong mọi cổng. impeccable có **61** luật cùng lớp cộng
contrast WCAG tính trên cascade thật — viết lại là ôm hàng nghìn dòng và một engine CSS.
Nhưng nó cần npm + puppeteer, còn medic là stdlib-only và phải chạy offline. Nên: giữ nguyên
cổng nhà, thêm MỘT lệnh opt-in gọi engine ngoài khi người ta chủ động muốn.

Ba cái bẫy đã đo thật (2026-09-04, impeccable@3.6.1) và đã né sẵn trong file này:
  1. `npx` GỘP stderr vào stdout (npm 10.9.2) → findings dạng text không tách được luồng.
     Né: luôn dùng `--json` (JSON đi stdout theo thiết kế).
  2. Đường dẫn sai chỉ in `Warning: cannot access` rồi thoát **0** — CI xanh mà quét 0 file.
     Né: tự kiểm target tồn tại trước khi gọi.
  3. Mã thoát KHÔNG phải 0/1: **0** sạch · **1** có target không quét được · **2** CÓ finding.
     Coi `!=0` là crash là hiểu ngược.

Quy ước rc=2-là-skipped mượn của archify `visual-check`: thiếu công cụ ≠ thất bại.

Exit: 0 sạch hoặc BỎ QUA (thiếu npx/mạng) · 1 quét không xong · 2 có finding.

Usage:
  ui-detect.py [file-or-dir ...]        # mặc định: llmwiki/html/overstack.html
  ui-detect.py --json
  ui-detect.py --self-test
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINNED = "impeccable@3.6.1"          # pin: engine ngoài đổi luật giữa chừng là cổng đổi nghĩa
DEFAULT = [ROOT / "llmwiki" / "html" / "overstack.html"]
TIMEOUT = 300
# BỎ QUA ≠ SẠCH. Trộn hai thứ này là kiểu nói dối tệ nhất của một cổng chất lượng:
# báo xanh trong khi chưa hề chạy. archify tách rõ bằng rc=2=skipped; ta dùng sentinel.
SKIPPED = -1


def available() -> bool:
    return shutil.which("npx") is not None


def run(targets: list) -> tuple:
    """Trả (rc, findings). rc theo hợp đồng của impeccable, đã đọc từ main.mjs:492."""
    missing = [t for t in targets if not Path(t).exists()]
    if missing:
        print(f"  ✗ target không tồn tại: {', '.join(str(m) for m in missing)}", file=sys.stderr)
        return 1, []
    cmd = ["npx", "--yes", PINNED, "detect", "--json", *[str(t) for t in targets]]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT, cwd=ROOT)
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"  · bỏ qua: không chạy được engine ngoài ({str(e)[:60]})", file=sys.stderr)
        return SKIPPED, []
    # npx trộn cảnh báo npm (EBADENGINE…) vào stdout — cắt từ dấu mở mảng JSON đầu tiên.
    raw = p.stdout or ""
    i = raw.find("[")
    try:
        findings = json.loads(raw[i:]) if i >= 0 else []
        return p.returncode, findings
    except ValueError:
        pass
    # JSON hỏng. Nguyên nhân ĐO ĐƯỢC (2026-09-04): stdout qua `npx` bị cắt ở đúng 64KiB —
    # overstack.html trả 65299 byte, đứt giữa chuỗi ở char 64555. Không phải lỗi mạng, và
    # KHÔNG được im lặng coi là sạch. Lấy lại con số bằng `--quiet` (output vài chục byte,
    # không thể bị cắt) rồi báo "đếm được, không có chi tiết".
    # ponytail: fallback đếm; muốn chi tiết đầy đủ thì cài local `npm i -D impeccable`.
    if len(raw) >= 65000:
        try:
            q = subprocess.run(["npx", "--yes", PINNED, "detect", "--quiet",
                                *[str(t) for t in targets]],
                               capture_output=True, text=True, timeout=TIMEOUT, cwd=ROOT)
            out = (q.stdout or "") + (q.stderr or "")
            m = re.search(r"(\d+)\s+anti-pattern", out)
            if m:
                return q.returncode, [{"antipattern": "(chi-tiết bị cắt)",
                                       "file": ", ".join(str(t) for t in targets),
                                       "snippet": f"{m.group(1)} finding — JSON >64KiB bị npx cắt; "
                                                  f"cài local `npm i -D {PINNED.split('@')[0]}` để xem đủ",
                                       "_count": int(m.group(1))}]
        except (subprocess.TimeoutExpired, OSError):
            pass
    return SKIPPED, []


def self_test() -> int:
    """Tất định, KHÔNG cần mạng: chứng minh hợp đồng mã thoát và bẫy target-thiếu."""
    checks = [
        ("target không tồn tại → rc 1, KHÔNG phải 0 (bẫy đã đo của impeccable)",
         run([ROOT / "khong-he-co-file-nay.html"])[0] == 1),
        ("pin phiên bản tường minh (engine ngoài không tự đổi luật)",
         PINNED.count("@") == 1 and PINNED.split("@")[1][0].isdigit()),
        ("thiếu npx → available() False, không nổ",
         isinstance(available(), bool)),
        ("BỎ QUA khác SẠCH — sentinel riêng, không trả 0", SKIPPED != 0),
    ]
    ok = True
    for label, passed in checks:
        print(f"  {'✓' if passed else '✗'} {label}")
        ok = ok and passed
    print("self-test: PASS" if ok else "self-test: FAIL")
    return 0 if ok else 1


def main() -> None:
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    as_json = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    targets = [Path(a) for a in args] if args else DEFAULT
    if not available():
        print("  · ui-detect BỎ QUA: không có npx trên PATH (không phải lỗi — engine là opt-in)")
        sys.exit(0)
    rc, findings = run(targets)
    if rc == SKIPPED:
        print("  · ui-detect BỎ QUA: engine ngoài không chạy được (mạng/npx). "
              "KHÔNG kết luận là sạch — chưa hề quét.")
        sys.exit(0)
    if as_json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
        sys.exit(rc)
    primary = [f for f in findings if not f.get("advisory")]
    for f in primary[:25]:
        loc = f"{f.get('file','?')}" + (f":{f['line']}" if f.get("line") else "")
        print(f"  \033[1;31m✗\033[0m {loc}  [{f.get('antipattern')}] {str(f.get('snippet'))[:70]}")
    if rc == 0:
        print(f"  \033[1;32m✓\033[0m {len(targets)} file sạch theo 61 luật của {PINNED}")
    elif rc == 2:
        n = primary[0].get("_count") if len(primary) == 1 and "_count" in primary[0] else len(primary)
        extra = "" if "_count" in (primary[0] if primary else {}) else \
            f" ({len(findings) - len(primary)} advisory không tính)"
        print(f"\n  {n} finding chính{extra} — {PINNED}")
        print(f"  Đối chiếu: cổng nhà `frontend-antipattern.py` có 9 luật và báo file này SẠCH. "
              f"Đây đúng là phần 61 luật ngoài nhìn thấy mà ta không.")
    sys.exit(rc)


if __name__ == "__main__":
    main()
