#!/usr/bin/env python3
"""loop-cost — estimate token spend of a loop stage BEFORE running it (T7, GH#15).

Absorbed from cobusgreyling/loop-engineering's `loop-cost`: the point is to decide
`probe: on/off` and how many adversarial rounds to allow with a cost basis, instead
of a passive budget guard that only cuts AFTER tokens are already spent.

Estimate model (deliberately simple — a planning heuristic, not a billing oracle):

    tokens ≈ base + components × cases × rounds × per_call

  · components — how many component traces the stage touches (e.g. p01..p30 → 30)
  · cases      — probe cases generated per component (T5 adversarial), or 1 for a plain run
  · rounds     — revise rounds allowed (loop-runner max_iter)
  · per_call   — avg tokens per model call for this stage
  · base       — fixed overhead (paraphrase-plan gate, setup)

Exit: 0 = under budget (or no budget given) · 1 = estimate exceeds --budget.

Usage:
  loop-cost.py estimate --components 30 --cases 3 --rounds 4 [--per-call 1500] [--budget 200000]
  loop-cost.py selftest
"""
import argparse
import sys

DEFAULT_PER_CALL = 1500   # avg tokens per model call, ballpark for a component probe
DEFAULT_BASE = 2000       # paraphrase-plan gate + setup overhead


def estimate(components, cases, rounds, per_call=DEFAULT_PER_CALL, base=DEFAULT_BASE):
    """Pure function so it is trivially testable. Returns estimated token count."""
    if min(components, cases, rounds, per_call) < 0 or base < 0:
        raise ValueError("all inputs must be non-negative")
    return base + components * cases * rounds * per_call


def cmd_estimate(a):
    tokens = estimate(a.components, a.cases, a.rounds, a.per_call, a.base)
    print(f"  loop-cost estimate: {tokens:,} tokens")
    print(f"    = {a.base:,} base + {a.components} components × {a.cases} cases "
          f"× {a.rounds} rounds × {a.per_call:,}/call")
    if a.budget is not None:
        headroom = a.budget - tokens
        if headroom < 0:
            print(f"  [OVER] exceeds budget {a.budget:,} by {-headroom:,} — giảm cases/rounds hoặc probe:off")
            return 1
        print(f"  [ok]   under budget {a.budget:,} (headroom {headroom:,})")
    return 0


def selftest():
    ok = True
    # 1. formula is exact
    got = estimate(components=30, cases=3, rounds=4, per_call=1500, base=2000)
    want = 2000 + 30 * 3 * 4 * 1500  # 542000
    ok &= (got == want) or _fail(f"estimate {got} != {want}")
    # 2. monotone in every knob (more work ⇒ never cheaper)
    b = estimate(10, 2, 2, 1000, 0)
    ok &= all(estimate(*args) >= b for args in
              [(11, 2, 2, 1000, 0), (10, 3, 2, 1000, 0), (10, 2, 3, 1000, 0), (10, 2, 2, 1100, 0)]) \
        or _fail("not monotone in a knob")
    # 3. zero work ⇒ only base (probe off = no per-case spend)
    ok &= (estimate(0, 5, 5, 1000, 777) == 777) or _fail("zero components should cost only base")
    # 4. negative input rejected
    try:
        estimate(-1, 1, 1); ok &= _fail("negative not rejected")
    except ValueError:
        pass
    print("loop-cost self-test:", "ALL PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


def _fail(msg):
    print("  [FAIL]", msg)
    return False


def build_parser():
    p = argparse.ArgumentParser(prog="loop-cost.py", description="Estimate loop token spend before running (T7).")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("estimate", help="estimate token spend for a loop stage")
    e.add_argument("--components", type=int, required=True, help="component traces touched (e.g. 30)")
    e.add_argument("--cases", type=int, default=1, help="probe cases per component (T5); 1 = plain run")
    e.add_argument("--rounds", type=int, default=1, help="revise rounds allowed (loop-runner max_iter)")
    e.add_argument("--per-call", type=int, default=DEFAULT_PER_CALL, dest="per_call", help="avg tokens/model call")
    e.add_argument("--base", type=int, default=DEFAULT_BASE, help="fixed overhead tokens")
    e.add_argument("--budget", type=int, default=None, help="fail (exit 1) if estimate exceeds this")
    e.set_defaults(func=cmd_estimate)
    s = sub.add_parser("selftest", help="assert the estimate formula")
    s.set_defaults(func=lambda a: selftest())
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    sys.exit(args.func(args))
