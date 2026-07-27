#!/usr/bin/env python3
"""bnal_config — shared BNAL adapter loader. ONE place replacing the load_config() that was
copy-pasted into ~17 features. Each feature: cfg = bnal_config.load(root, "<name>", FALLBACK).

proof: harness/scripts/flywheel.py
(thư viện dùng chung, không có CLI riêng để --self-test — exercised transitively bởi
flywheel.py/archetype.py/mem-rank.py --self-test, cả 3 đều import bnal_config trực tiếp)

Reads harness/<name>.config.yaml, overlays non-None keys onto a deep copy of the fallback dict.
Fail-open: missing file / no PyYAML / parse error → fallback. The adapter boundary is unchanged —
the config FILE is still the one quarantine per feature; only this loader is shared."""
import copy
from pathlib import Path


def load(root, name, fallback):
    cfg = copy.deepcopy(fallback)
    try:
        import yaml
        p = Path(root) / "harness" / f"{name}.config.yaml"
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for k, v in data.items():
                if v is not None:
                    cfg[k] = v
    except Exception:
        pass
    return cfg
