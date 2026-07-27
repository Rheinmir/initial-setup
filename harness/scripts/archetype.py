#!/usr/bin/env python3
"""archetype — gọi 5 archetype của Boris Cherny như PERSONA dispatch (cho agy/opencode/kiro trong
orca-workflow) + phase-map (route tool theo archetype). Đọc harness/archetypes.config.yaml.

  --list                 bảng 5 archetype: keyword · phase · cli · tools.
  --get <keyword|name>   in PREAMBLE persona (posture) + lệnh dispatch gợi ý + tools — để orca-workflow
                         INJECT khi dispatch. (vd `archetype.py --get /sweep`)
  --phase <name>         phase-map (#2): tool overstack hợp archetype đó.
  --self-test            kiểm keyword→archetype, tools, posture-file (fdk-gate BNAL self-test).

The ONE adapter = harness/archetypes.config.yaml (cli/model routing — verified:false). Map
keyword/tools/posture là tất định; CLI nào hợp archetype nào là phán đoán (quarantine).
"""
import os
import sys
from pathlib import Path

import bnal_config

_FALLBACK = {"verified": False, "archetypes": {
    "prototyper": {"keyword": "/proto", "phase": "0→1 explore", "cli": "opencode",
                   "tools": ["last30days", "build-now-adapt-later"], "posture": "llmwiki/personas/prototyper.md"},
    "builder": {"keyword": "/build", "phase": "1→N production", "cli": "claude",
                "tools": ["propose", "verify-before-commit"], "posture": "llmwiki/personas/builder.md"},
    "sweeper": {"keyword": "/sweep", "phase": "clean / unship", "cli": "opencode",
                "tools": ["simplify", "docs-curate", "sweep-gate"], "posture": "llmwiki/personas/sweeper.md"},
    "grower": {"keyword": "/grow", "phase": "iterate PMF", "cli": "claude",
               "tools": ["success-flywheel", "wikieval"], "posture": "llmwiki/personas/grower.md"},
    "maintainer": {"keyword": "/maintain", "phase": "scale / harden", "cli": "claude",
                   "tools": ["harness-update", "orca-sec-scans"], "posture": "llmwiki/personas/maintainer.md"},
    "tester": {"keyword": "/test", "phase": "verify design-first", "cli": "claude",
               "tools": ["qc-code", "wikieval"], "posture": "llmwiki/personas/tester.md"},
}}


def _archetypes(root):
    return bnal_config.load(root, "archetypes", _FALLBACK).get("archetypes", {})


def resolve(arcs, token):
    """keyword (/sweep) hoặc name (sweeper) → (name, spec)."""
    t = (token or "").strip().lower()
    for name, spec in arcs.items():
        if name == t or str(spec.get("keyword", "")).lower() == t or str(spec.get("keyword", "")).lstrip("/").lower() == t.lstrip("/"):
            return name, spec
    return None, None


def dispatch_cmd(spec, project="<project>"):
    cli = spec.get("cli", "claude")
    model = spec.get("model")
    if cli == "opencode":
        m = f" -m {model}" if model else " -m opencode/big-pickle"
        return f'opencode run{m} --dir "{project}" "<task>"'
    if cli == "agy":
        return 'agy -p "<task>"'
    if cli == "kiro":
        return f'kiro run --dir "{project}" "<task>"'
    return "(Claude trực tiếp — phân tích/nuance; không dispatch CLI)"


def _posture_path(root, rel: str):
    """REPO-LOCAL → GLOBAL (~/.claude/harness) — downstream không có llmwiki/personas trong repo;
    install --global copy personas lên harness home (bài học UAT canary 260718: preamble rỗng)."""
    import os
    for base in (Path(root),
                 Path(os.environ.get("OVERSTACK_HARNESS_HOME") or (Path.home() / ".claude" / "harness"))):
        p = base / rel
        if p.is_file():
            return p
    return None


def get(root, token):
    arcs = _archetypes(root)
    name, spec = resolve(arcs, token)
    if not name:
        return f"[archetype] không có '{token}'. Có: " + ", ".join(f"{n} ({s.get('keyword')})" for n, s in arcs.items())
    pp = _posture_path(root, spec.get("posture", ""))
    posture = pp.read_text(encoding="utf-8") if pp else f"(thiếu file posture {spec.get('posture')} — cả repo lẫn global)"
    return (f"# Dispatch persona: {name.upper()}  ·  {spec.get('keyword')}  ·  phase {spec.get('phase')}\n"
            f"# CLI gợi ý: {spec.get('cli')}{(' / ' + spec['model']) if spec.get('model') else ''}\n"
            f"# Lệnh: {dispatch_cmd(spec)}\n"
            f"# Tools overstack hợp phase: {', '.join(spec.get('tools', []))}\n\n"
            f"--- PREAMBLE (inject vào task khi dispatch) ---\n{posture.strip()}\n")


def list_all(root):
    arcs = _archetypes(root)
    out = ["5 ARCHETYPE (Boris Cherny) — persona dispatch + từ khoá:",
           f"  {'archetype':<12} {'keyword':<10} {'cli':<9} {'phase':<16} tools"]
    for name, s in arcs.items():
        out.append(f"  {name:<12} {s.get('keyword',''):<10} {s.get('cli',''):<9} {s.get('phase',''):<16} {', '.join(s.get('tools', []))}")
    return "\n".join(out)


def self_test() -> int:
    root = Path(__file__).resolve().parents[2]
    arcs = _archetypes(root)
    n1, s1 = resolve(arcs, "/sweep")
    n2, s2 = resolve(arcs, "maintainer")
    n3, _ = resolve(arcs, "/nope")
    n4, s4 = resolve(arcs, "/test")
    posture_ok = all(_posture_path(root, s.get("posture", "")) is not None for s in arcs.values())
    ok = (n1 == "sweeper" and "simplify" in s1.get("tools", []) and n2 == "maintainer"
          and n3 is None and n4 == "tester" and "qc-code" in s4.get("tools", [])
          and len(arcs) == 6 and posture_ok)
    print("archetype self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> None:
    args = sys.argv[1:]
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    if "--root" in args:
        i = args.index("--root"); root = Path(args[i + 1]); del args[i:i + 2]
    if "--self-test" in args:
        sys.exit(self_test())
    if "--list" in args:
        print(list_all(root)); return
    if "--phase" in args:
        i = args.index("--phase")
        name, spec = resolve(_archetypes(root), args[i + 1] if len(args) > i + 1 else "")
        if not spec:
            print("usage: archetype.py --phase <archetype|keyword>", file=sys.stderr); sys.exit(2)
        print(f"{name} ({spec.get('phase')}) → tools: {', '.join(spec.get('tools', []))}"); return
    if "--get" in args:
        i = args.index("--get")
        if len(args) <= i + 1:
            print("usage: archetype.py --get <keyword|name>", file=sys.stderr); sys.exit(2)
        print(get(root, args[i + 1])); return
    print(list_all(root))


if __name__ == "__main__":
    main()
