#!/usr/bin/env python3
"""bnal_guard — shared 'emit advisory/block per mode+verified' tail for the checker/guard features.
ONE place replacing the _emit_and_exit / advisory-vs-strict logic that was copy-pasted into
egress-guard, inject-scan, spec-gate, claim-receipts, prospect-critic.

emit(problems, ...): problems=[] → exit 0 (pass). Else block (exit 2) ONLY when mode==enforce_mode
AND verified is True; otherwise advisory (stderr, exit 0). Fail-safe: an un-verified guess never blocks.

proof: harness/scripts/egress-guard.py
(thư viện dùng chung, không có CLI riêng — exercised transitively bởi egress-guard.py --self-test,
import trực tiếp bnal_guard)"""
import sys


def emit(problems, *, tag, mode, verified, enforce_mode="block",
         advise="set verified:true to enforce"):
    if not problems:
        sys.exit(0)
    body = "\n".join(problems) if any("\n" in p for p in problems) else "; ".join(problems)
    msg = f"{tag} {body}"
    if str(mode).lower() == enforce_mode and verified is True:
        print(f"{msg}  ({enforce_mode})", file=sys.stderr)
        sys.exit(2)
    print(f"{msg}  (advisory — {advise})", file=sys.stderr)
    sys.exit(0)
