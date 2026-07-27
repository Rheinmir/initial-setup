#!/usr/bin/env python3
"""Pluggable embedder for mem-rank: STDIN text -> STDOUT JSON float array, via the Voyage AI
embeddings API (Anthropic's recommended embeddings provider). Wire it in
harness/mem-rank.config.yaml:

    relevance:
      scorer: embedding
      embedder_cmd: python3 harness/scripts/embed-voyage.py

Needs VOYAGE_API_KEY in the environment + network. On any failure it prints nothing and exits
non-zero, so mem-rank falls back to token-overlap. Env: MEMRANK_EMBED_MODEL overrides the model.
"""
import json
import os
import sys
import urllib.request

KEY = os.environ.get("VOYAGE_API_KEY")
MODEL = os.environ.get("MEMRANK_EMBED_MODEL", "voyage-3")


def main() -> int:
    if not KEY:
        sys.stderr.write("embed-voyage: VOYAGE_API_KEY unset\n")
        return 1
    text = sys.stdin.read()
    body = json.dumps({"model": MODEL, "input": [text]}).encode("utf-8")
    req = urllib.request.Request("https://api.voyageai.com/v1/embeddings", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {KEY}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            vec = json.loads(r.read())["data"][0]["embedding"]
    except Exception as e:                       # key/network/quota => let mem-rank fall back
        sys.stderr.write(f"embed-voyage: {e}\n")
        return 1
    if not isinstance(vec, list) or not vec:
        return 1
    print(json.dumps(vec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
