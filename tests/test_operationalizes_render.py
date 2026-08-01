#!/usr/bin/env python3
"""SC-001/SC-002: cạnh operationalizes + node lá Protocol phải xuất hiện thật trong wiki-graph.html."""
import subprocess
import sys
import tempfile
import pathlib


def test_operationalizes_edge_rendered():
    with tempfile.TemporaryDirectory() as td:
        wiki = pathlib.Path(td) / "wiki" / "concepts"
        wiki.mkdir(parents=True)
        (wiki / "a.md").write_text(
            "---\ntype: concept\nlayer: mental-model\n---\n\n# A\n\nXem `propose`.\n",
            encoding="utf-8")
        out = pathlib.Path(td) / "out.html"
        repo_root = pathlib.Path(__file__).resolve().parents[1]
        r = subprocess.run(
            [sys.executable, str(repo_root / "fdk/tools/build-wiki-graph.py"),
             str(wiki.parent), "--code-root", str(repo_root), "--out", str(out)],
            capture_output=True, text=True, cwd=str(repo_root))
        assert r.returncode == 0, r.stderr
        html = out.read_text(encoding="utf-8")
        assert '"rel": "operationalizes"' in html or '"rel":"operationalizes"' in html, \
            "cạnh operationalizes không xuất hiện trong HTML sinh ra"
        assert "wiki-protocol" in html, "node Protocol không có class riêng"


if __name__ == "__main__":
    test_operationalizes_edge_rendered()
    print("PASS")
