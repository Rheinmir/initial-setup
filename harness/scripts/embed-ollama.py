#!/usr/bin/env python3
"""Pluggable embedder for mem-rank: STDIN text -> STDOUT JSON float array, via a local
Ollama embeddings endpoint (offline, no API key). Wire it in harness/mem-rank.config.yaml:

    relevance:
      scorer: embedding
      embedder_cmd: python3 harness/scripts/embed-ollama.py

Needs `ollama serve` running with an embedding model pulled (default nomic-embed-text:
`ollama pull nomic-embed-text`). On any failure it prints nothing and exits non-zero, so
mem-rank falls back to token-overlap. Env: OLLAMA_HOST, MEMRANK_EMBED_MODEL override defaults.
"""
import json
import os
import sys
import urllib.request

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
MODEL = os.environ.get("MEMRANK_EMBED_MODEL", "nomic-embed-text")


def main() -> int:
    text = sys.stdin.read()
    body = json.dumps({"model": MODEL, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(f"{HOST}/api/embeddings", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            vec = json.loads(r.read()).get("embedding")
    except Exception as e:                       # ollama down / model missing => let mem-rank fall back
        sys.stderr.write(f"embed-ollama: {e}\n")
        return 1
    if not isinstance(vec, list) or not vec:
        return 1
    print(json.dumps(vec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
