#!/usr/bin/env python3
"""prose-antipattern — soi AI-tell trong VĂN XUÔI người đọc (0 token, no-LLM).

Chỗ hổng nó bịt: ta có cổng cho HTML (`frontend-antipattern.py`), cho code, cho commit
(`no_ai_attribution.py`), nhưng KHÔNG có gì gác giọng văn của ADR/proposal/report/wiki —
đúng nơi giọng AI lộ rõ nhất và cũng là nơi người ngoài đọc.

Hấp thụ từ blader/humanizer (35 pattern, 09/2026). Lấy CÓ ĐO, không bê nguyên:
chạy thử cả 6 nhóm ứng viên trên 266 trang wiki thật rồi mới chọn.

  BỊ LOẠI vì là nhiễu trên corpus của ta, không phải vì sai:
    · em-dash bão hoà   → khớp 96/266 (36%). Trong văn kỹ thuật tiếng Việt, gạch ngang là
      dấu tách mệnh đề bình thường. Nó là AI-tell của văn MARKETING TIẾNG ANH, không phải
      của tài liệu ta. Bê nguyên là lặp lại đúng lỗi genre-scoped mà frontend-antipattern
      đã ghi (Inter/system font false-positive trên chính seq.html).
    · bold quá tay      → khớp 113/266 (42%). Ta dùng **đậm** để đánh dấu THUẬT NGỮ.

  GIỮ — bốn luật còn lại, tất định và không phụ thuộc ngôn ngữ marketing:
    [WARN] "not X but Y" / "không phải X mà là Y"  — 11/266 lúc cắm, nợ thật nhưng mỏng.
    [WARN] kết bài lạc quan sáo                     — 0/266, gác ngay không tốn gì.
    [WARN] hedge chồng ("có thể sẽ có thể")         — 0/266.
    [WARN] filler "in order to" / "nhằm mục đích để" — 1/266.

Toàn WARN có chủ ý: đây là chất lượng giọng văn, không phải an toàn. Cổng chặn giọng văn
là cách nhanh nhất khiến người ta viết né validator thay vì viết hay hơn.

Exit: 0 sạch · 2 có WARN (medic map: 2→warn). Fail-open: đọc không được → sạch.

Usage:
  prose-antipattern.py [file.md ...]   # mặc định: wiki concepts/ + entities/, bỏ archive
  prose-antipattern.py --json
  prose-antipattern.py --self-test
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RULES = [
    ("not-x-but-y",
     re.compile(r"không phải\s+\S.{0,60}?\s+mà (?:là|chính là)\b|\bnot\s+\w.{0,40}?\s+but\s+\w", re.I),
     'khuôn "không phải X mà là Y" — nhịp tương phản mà model rất hay rơi vào. '
     'Nói thẳng Y trước, chỉ giữ khuôn khi X thật sự là hiểu nhầm phổ biến cần đính chính.'),
    ("closing-cliche",
     re.compile(r"(hy vọng .{0,40}(hữu ích|giúp ích)|chúc bạn .{0,30}(thành công|may mắn)|i hope this helps)", re.I),
     "kết bài lạc quan sáo — câu chúc không mang thông tin. Kết bằng bước kế tiếp cụ thể, hoặc dừng."),
    ("hedge-stack",
     re.compile(r"(có thể sẽ có thể|có lẽ có thể|perhaps possibly|might potentially)", re.I),
     "chồng hai lớp rào đón — mỗi lớp làm câu yếu đi mà không thêm độ chính xác. Giữ một."),
    ("filler-purpose",
     re.compile(r"\bin order to\b|nhằm mục đích để", re.I),
     'filler chỉ mục đích — "để" là đủ.'),
]


def scan_text(text: str, rel: str) -> list:
    """Bỏ code block trước khi soi: lệnh/định danh không phải văn xuôi."""
    body = re.sub(r"```.*?```", " ", text, flags=re.S)
    body = re.sub(r"`[^`\n]*`", " ", body)
    out = []
    for rid, rx, msg in RULES:
        m = rx.search(body)
        if m:
            out.append({"level": "WARN", "rule": rid, "file": rel,
                        "msg": msg, "snippet": m.group(0)[:70]})
    return out


def scan(path: Path) -> list:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []  # fail-open
    rel = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    return scan_text(text, rel)


def default_targets() -> list:
    wiki = ROOT / "llmwiki" / "wiki"
    return [p for d in ("concepts", "entities") for p in (wiki / d).rglob("*.md")
            if "/archive/" not in p.as_posix()]


def self_test() -> int:
    BAD = ("Đây không phải một cache mà là một index đảo ngược. "
           "Ta dùng nó in order to giảm truy vấn. Có thể sẽ có thể chậm hơn ở lần đầu. "
           "Hy vọng phần này hữu ích cho bạn.")
    GOOD = ("Đây là một index đảo ngược, dùng để giảm truy vấn. Lần đầu chậm hơn ~40ms. "
            "Bước kế: đo lại sau khi bật cache.\n\n```sh\n# not a but b — trong code block, phải được tha\n```")
    bad = scan_text(BAD, "bad.md")
    good = scan_text(GOOD, "good.md")
    hit = {f["rule"] for f in bad}
    checks = [
        ("BAD bắt not-x-but-y", "not-x-but-y" in hit),
        ("BAD bắt filler-purpose", "filler-purpose" in hit),
        ("BAD bắt hedge-stack", "hedge-stack" in hit),
        ("BAD bắt closing-cliche", "closing-cliche" in hit),
        ("GOOD sạch — code block được tha", len(good) == 0),
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
    targets = [Path(a) for a in args] if args else default_targets()
    findings = []
    for t in targets:
        findings += scan(t)
    if as_json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    elif findings:
        for f in findings:
            print(f"  \033[1;33m⚠\033[0m {f['file']}: [{f['rule']}] {f['msg']}")
            print(f"      → {f['snippet']}")
        print(f"\n  {len(findings)} WARN trên {len(targets)} file")
    else:
        print(f"  \033[1;32m✓\033[0m {len(targets)} file văn xuôi sạch AI-tell")
    sys.exit(2 if findings else 0)


if __name__ == "__main__":
    main()
