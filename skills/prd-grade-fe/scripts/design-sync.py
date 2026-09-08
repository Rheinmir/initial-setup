#!/usr/bin/env python3
"""design-sync — design.md là nguồn chân lý; sinh frontmatter (impeccable đọc) + tokens.css từ block :root{}.

impeccable@3.6.1 (cli/engine/design-system.mjs) đọc DESIGN.md/design.md ở gốc project và CHỈ dùng
frontmatter YAML: colors:{}, typography:{role:{fontFamily,fontSize}, scale:{}}, rounded:{}.
hallmark khoá hệ bằng thân markdown + block ```css :root{}``` của cùng file. Script này nối hai đầu:
block :root là nguồn, frontmatter + tokens.css là bản sinh. --check rc 1 khi bản sinh lệch nguồn.

Exit: 0 sạch/đã ghi · 1 drift (--check) · 2 thiếu token bắt buộc hoặc thiếu block.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT_RE = re.compile(r"```css\s*\n(:root\s*\{.*?\})\s*\n```", re.S)
DECL_RE = re.compile(r"--([a-z0-9-]+)\s*:\s*([^;]+);")
FM_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
REQUIRED = ["color-paper", "color-ink", "color-accent", "font-display", "font-body", "font-mono"]


def parse_tokens(md):
    m = ROOT_RE.search(md)
    if not m:
        print("design-sync: không thấy block ```css :root{} trong design.md", file=sys.stderr)
        sys.exit(2)
    return {k: v.strip() for k, v in DECL_RE.findall(m.group(1))}


def frontmatter_yaml(t):
    q = lambda v: '"' + v.replace('"', "'") + '"'
    out = ["---", "# SINH từ block :root bởi design-sync.py — đừng sửa tay; sửa block rồi chạy lại", "colors:"]
    out += [f"  {k[6:]}: {q(v)}" for k, v in t.items() if k.startswith("color-")]
    out.append("typography:")
    for role in ("display", "body", "mono"):
        if f"font-{role}" in t:
            out += [f"  {role}:", f"    fontFamily: {q(t['font-' + role])}"]
    sizes = {k[5:]: v for k, v in t.items() if k.startswith("text-")}
    if sizes:
        out.append("  scale:")
        out += [f"    {k}: {q(v)}" for k, v in sizes.items()]
    radii = {k[7:]: v for k, v in t.items() if k.startswith("radius-")}
    if radii:
        out.append("rounded:")
        out += [f"  {k}: {q(v)}" for k, v in radii.items()]
    out.append("---\n")
    return "\n".join(out)


def render(md):
    t = parse_tokens(md)
    missing = [k for k in REQUIRED if k not in t]
    if missing:
        print(f"design-sync: thiếu token bắt buộc {missing}", file=sys.stderr)
        sys.exit(2)
    body = FM_RE.sub("", md, count=1)
    css = "/* SINH từ design.md bởi design-sync.py — đừng sửa tay */\n" + ROOT_RE.search(md).group(1) + "\n"
    return frontmatter_yaml(t) + body, css


SAMPLE = """# Design — Sample

## Tokens
```css
:root {
  --color-paper: oklch(98% 0.005 250);  --color-paper-2: oklch(95% 0.01 250);
  --color-ink: oklch(20% 0.02 250);     --color-ink-2: oklch(40% 0.02 250);
  --color-rule: oklch(88% 0.01 250);    --color-accent: oklch(62% 0.19 250);
  --color-accent-ink: oklch(99% 0 0);   --color-focus: oklch(62% 0.19 250);
  --font-display: "SF Pro Display", -apple-system, sans-serif;
  --font-body: "SF Pro Text", -apple-system, sans-serif;
  --font-mono: "SF Mono", ui-monospace, monospace;
  --radius-card: 14px; --radius-pill: 999px;
  --text-base: 14px;
}
```
"""


def self_test():
    t = parse_tokens(SAMPLE)
    assert {"color-paper", "color-ink", "color-accent", "font-display", "font-body", "font-mono"} <= set(t), t.keys()
    assert t["color-accent"].startswith("oklch("), "OKLCH giữ nguyên, không đổi sang hex"
    md1, css1 = render(SAMPLE)
    md2, css2 = render(md1)
    assert (md1, css1) == (md2, css2), "idempotent"
    fm = md1.split("---")[1]
    assert "colors:" in fm and "typography:" in fm and "rounded:" in fm
    assert render(md1.replace("oklch(62% 0.19 250)", "oklch(50% 0.1 20)"))[1] != css1, "đổi 1 token → css đổi → --check bắt được"
    print("design-sync --self-test: 4/4 ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    root = Path(a.root)
    src = next((root / n for n in ("design.md", "DESIGN.md") if (root / n).is_file()), None)
    if not src:
        print(f"design-sync: không có design.md ở {root}", file=sys.stderr)
        sys.exit(2)
    md_new, css_new = render(src.read_text())
    css_p = root / "tokens.css"
    drift = [p.name for p, new in ((src, md_new), (css_p, css_new)) if not p.is_file() or p.read_text() != new]
    if a.check:
        print("design-sync --check:", "khớp đĩa" if not drift else f"DRIFT {drift}")
        sys.exit(1 if drift else 0)
    src.write_text(md_new)
    css_p.write_text(css_new)
    print(f"design-sync: đã ghi {src.name} (frontmatter) + tokens.css")


if __name__ == "__main__":
    main()
