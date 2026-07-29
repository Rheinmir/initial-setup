#!/usr/bin/env python3
"""duplicate-basename: under wiki/, no .md basename may live in two different dirs.

A slug is meant to be unique across the wiki. The same basename appearing in two
folders (e.g. a tracked copy in `sources/` and a gitignored copy in
`sources/draft/`) is the diverging-duplicate trap. This validator groups every
`*.md` under `wiki/` by basename (skipping README.md and _template.md scaffolding)
and fails if any basename occurs in two or more directories.

Contract: `duplicate_basename.py [--wiki-dir path/to/wiki]` (CLI / pre-commit / CI).
Default wiki dir is `llmwiki/wiki` resolved from the repo root. Exit 0 = clean,
exit 2 = duplicate basenames found (listed on stderr).
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_BASENAMES = {"README.md", "_template.md"}
# eval fixtures deliberately reuse skill slugs as query stimuli (skill-resolve/
# retrieval evals) — they are NOT diverging copies of the canonical skill doc.
SKIP_DIR_PREFIXES = ("sources/evals/",)


def find_duplicates(wiki: Path) -> dict:
    by_name = defaultdict(set)
    for f in wiki.rglob("*.md"):
        if f.name in SKIP_BASENAMES or not f.is_file():
            continue
        rel = f.relative_to(wiki).as_posix()
        if rel.startswith(SKIP_DIR_PREFIXES):
            continue
        by_name[f.name].add(f.parent.relative_to(wiki).as_posix() or ".")
    return {name: sorted(dirs) for name, dirs in by_name.items() if len(dirs) >= 2}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    wiki = ROOT / "llmwiki" / "wiki"
    if "--wiki-dir" in args:
        wiki = Path(args[args.index("--wiki-dir") + 1])
    if not wiki.is_dir():
        return 0

    dups = find_duplicates(wiki)
    if dups:
        lines = ["[duplicate-basename] same .md basename in >=2 dirs under wiki/:"]
        for name in sorted(dups):
            lines.append(f"  {name}:")
            for d in dups[name]:
                lines.append(f"      {d}/{name}")
        lines.append("  -> keep one canonical per slug (a 2nd copy is legal only if identical).")
        print("\n".join(lines), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
