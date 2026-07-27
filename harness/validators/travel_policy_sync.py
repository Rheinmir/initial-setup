#!/usr/bin/env python3
"""travel-policy-sync: `travel-policy.yaml` phải khớp cái `install-harness.sh` thật sự copy.

travel-policy.yaml là VĂN BẢN MÔ TẢ; thứ sinh ra hành vi là installer. Khi hai bên
lệch, mọi câu trả lời "cái gì tới tay user" đọc từ policy đều sai mà không ai biết.
Validator này đọc khối `--global` của installer, dựng tập pattern thực sự được copy
xuống `~/.claude/harness/`, rồi đối chiếu hai chiều với policy:

  - tầng `framework_only` khai "không đi xuống" mà installer VẪN copy  → lỗi
  - tầng `global_shared` khai "đi xuống" mà installer KHÔNG copy       → lỗi

Contract: `travel_policy_sync.py [--root path]` (CLI / pre-commit / CI).
Exit 0 = khớp, exit 2 = lệch (liệt kê trên stderr). Thiếu file → 0 (fail-open,
downstream không có repo framework).
"""
from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Đường dẫn trong policy nhưng KHÔNG do installer --global lo:
#   llmwiki/.claude/hooks/*.py → copy phẳng vào $GH/hooks/ (đã kiểm qua entry engine_core khác)
#   research_reach → skill ngoài, cài bằng `agent-reach install`, không qua installer
SKIP_SECTIONS = {"research_reach"}


def copied_patterns(installer: Path) -> list[str]:
    """Pattern repo-relative mà khối --global của install-harness.sh copy xuống global."""
    text = installer.read_text(encoding="utf-8")
    start = text.find('= "--global" ]')
    if start < 0:
        return []
    end = text.find('SETTINGS="$HOME/.claude/settings.json"', start)
    block = text[start:end if end > 0 else len(text)]

    pats = []
    # glob hay nằm NGOÀI dấu nháy: `cp "$SRC/harness/scripts/"*.py` — phải ghép đuôi lại,
    # bỏ đuôi thì pattern cụt thành thư mục và mọi file trong đó bị coi là không travel.
    for m in re.finditer(r'^\s*cp\s+(-R\s+)?"\$SRC/([^"]+)"(\S*)\s+"\$GH/([^"]*)"', block, re.M):
        recursive, src, dest = bool(m.group(1)), m.group(2) + m.group(3), m.group(4)
        if recursive:
            # `cp -R "$SRC/dir/." "$GH/dir/"` → cả cây con
            src = src.rstrip("/.") + "/**"
        pats.append((src, dest.rstrip("/")))
    return pats


def strip_list(installer: Path) -> list[str]:
    """Danh sách STRIP_TIER3 hardcode trong installer — cái nó THỰC SỰ gỡ khỏi global."""
    m = re.search(r'STRIP_TIER3="\n(.*?)\n"', installer.read_text(encoding="utf-8"), re.S)
    return [ln.strip() for ln in m.group(1).splitlines() if ln.strip()] if m else []


def travels(path: str, pats, skip_same_dest: bool = False) -> bool:
    """path có tới ~/.claude/harness không.

    skip_same_dest=True (dùng cho tầng 3 khi installer có block gỡ): bỏ qua bản copy giữ
    NGUYÊN đường dẫn repo-relative — `rm -f "$GH/<rel>"` gỡ đúng nó. Bản copy sang đích KHÁC
    (fdk/tools/x.py → $GH/hooks/x.py) thì rm không chạm tới: vẫn tới tay user, vẫn tính travel.
    """
    parts = path.split("/")
    for p, dest in pats:
        if skip_same_dest and dest == path.rsplit("/", 1)[0]:
            continue
        if p.endswith("/**"):
            if path.startswith(p[:-2]):
                return True
            continue
        # khớp theo TỪNG segment: `*` của shell không vượt `/`, fnmatch thì có
        pp = p.split("/")
        if len(pp) == len(parts) and all(fnmatch.fnmatch(a, b) for a, b in zip(parts, pp)):
            return True
    return False


def policy_paths(policy: Path) -> tuple[list[str], list[str]]:
    """(framework_only, global_shared) — path repo-relative rút từ YAML, không cần pyyaml.

    framework_only là map `path: "mô tả"`; global_shared là map section → list các
    dòng `"a/b.py + c/d.py — mô tả"`.
    """
    fw, gl = [], []
    section = None       # 'framework_only' | 'global_shared' | None
    subsection = None
    for raw in policy.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip() if not raw.lstrip().startswith("#") else ""
        if not line.strip():
            continue
        if not line[0].isspace():
            section = line.split(":", 1)[0].strip()
            subsection = None
            continue
        stripped = line.strip()
        if section == "framework_only" and ":" in stripped:
            fw.append(stripped.split(":", 1)[0].strip())
        elif section == "global_shared":
            if not stripped.startswith("-"):
                subsection = stripped.rstrip(":").strip()
            elif subsection not in SKIP_SECTIONS:
                item = stripped.lstrip("- ").strip('"').split("—")[0]
                # `a/b/x.py + y.py` — vế sau viết tắt, thiếu prefix; kế thừa dir của vế trước
                prefix = ""
                for hit in re.findall(r"[\w./*-]+\.(?:py|yaml|json|md)", item):
                    if "/" in hit:
                        prefix = hit.rsplit("/", 1)[0] + "/"
                    else:
                        hit = prefix + hit
                    gl.append(hit)
    return fw, gl


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[args.index("--root") + 1]) if "--root" in args else ROOT
    installer = root / "harness" / "scripts" / "install-harness.sh"
    policy = root / "harness" / "travel-policy.yaml"
    if not installer.is_file() or not policy.is_file():
        return 0

    pats = copied_patterns(installer)
    if not pats:
        print("[travel-policy-sync] không đọc được khối --global của install-harness.sh",
              file=sys.stderr)
        return 2

    fw, gl = policy_paths(policy)
    strip = strip_list(installer)
    leaked = [p for p in fw if travels(p, pats, skip_same_dest=p in strip)]
    missing = [p for p in gl if not travels(p, pats)]
    # hằng số STRIP_TIER3 đi cùng script (không đọc policy runtime) — phải gác nó khỏi tự trôi
    drift = sorted(set(fw) ^ set(strip))

    if not leaked and not missing and not drift:
        return 0

    out = ["[travel-policy-sync] travel-policy.yaml LỆCH so với install-harness.sh:"]
    if drift:
        out.append(f"  framework_only ≠ STRIP_TIER3 trong installer — {len(drift)} lệch:")
        out += [f"      {p}  ({'chỉ trong policy' if p in fw else 'chỉ trong installer'})" for p in drift]
    if leaked:
        out.append(f"  khai framework_only (không đi xuống) nhưng installer VẪN copy — {len(leaked)}:")
        out += [f"      {p}" for p in leaked]
    if missing:
        out.append(f"  khai global_shared (đi xuống) nhưng installer KHÔNG copy — {len(missing)}:")
        out += [f"      {p}" for p in missing]
    out.append("  -> sửa MỘT bên: policy mô tả, installer mới là hành vi thật.")
    print("\n".join(out), file=sys.stderr)
    return 2


def demo():
    pats = [("fdk/tools/*.py", "fdk/tools"), ("harness/poc-vendor-neutral/**", "harness/poc-vendor-neutral"),
            ("harness/version.json", "version.json"), ("fdk/tools/build-capabilities.py", "hooks")]
    assert travels("fdk/tools/medic.py", pats)
    assert travels("harness/poc-vendor-neutral/bin/x.sh", pats)
    assert not travels("harness/scripts/medic.py", pats)
    assert not travels("fdk/tools/sub/deep.py", pats), "fnmatch * không được vượt thư mục"
    # có block gỡ: bản copy cùng chỗ bị rm dọn, bản copy sang $GH/hooks/ thì không
    assert not travels("fdk/tools/medic.py", pats, skip_same_dest=True)
    assert travels("fdk/tools/build-capabilities.py", pats, skip_same_dest=True)
    print("demo ok")


if __name__ == "__main__":
    sys.exit(demo() if "--demo" in sys.argv else main())
