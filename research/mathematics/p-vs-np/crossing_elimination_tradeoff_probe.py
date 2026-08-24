#!/usr/bin/env python3
"""Finite mechanics replay for C025-E2R-L1F crossing elimination.

This checks the exact one-extension clause expansion and all abstract
polarity cases of a Resolution inference.  It does not prove the external
asymptotic heavy-width lower bound.
"""
from __future__ import annotations
from itertools import product

Clause = frozenset[int]


def taut(c: Clause) -> bool:
    return any(-x in c for x in c)


def canon(xs) -> Clause | None:
    c = frozenset(xs)
    return None if taut(c) else c


def resolve(p: Clause, q: Clause, pivot: int) -> Clause | None:
    if pivot not in p or -pivot not in q:
        return None
    return canon((p - {pivot}) | (q - {-pivot}))


def expand_one(c: Clause, e: int, a: int, b: int) -> list[Clause]:
    if taut(c):
        return []
    if e in c and -e in c:
        return []
    if e in c:
        base = c - {e}
        out = []
        for lit in (a, b):
            x = canon(base | {lit})
            if x is not None and x not in out:
                out.append(x)
        return out
    if -e in c:
        base = c - {-e}
        x = canon(base | {-a, -b})
        return [] if x is None else [x]
    return [c]


def with_state(base: set[int], state: int, e: int) -> Clause:
    # state: -1 => ~e, 0 => absent, +1 => e
    xs = set(base)
    if state:
        xs.add(e if state > 0 else -e)
    return frozenset(xs)


def check_non_e_pivot() -> None:
    e, a, b, y = 20, 1, 2, 10
    A = {3}
    B = {4}
    for sa, sb in product((-1, 0, 1), repeat=2):
        p = with_state(A | {y}, sa, e)
        q = with_state(B | {-y}, sb, e)
        raw_r = (p - {y}) | (q - {-y})
        r = canon(raw_r)
        targets = [] if r is None else expand_one(r, e, a, b)
        ep = expand_one(p, e, a, b)
        eq = expand_one(q, e, a, b)
        for target in targets:
            witnesses = [
                resolve(pp, qq, y)
                for pp in ep
                for qq in eq
                if y in pp and -y in qq
            ]
            assert target in witnesses, (sa, sb, target, ep, eq, witnesses)


def check_e_pivot() -> None:
    e, a, b = 20, 1, 2
    A = frozenset({3})
    B = frozenset({4})
    p = A | {e}
    q = B | {-e}
    ep = expand_one(p, e, a, b)
    eq = expand_one(q, e, a, b)
    assert len(ep) == 2 and len(eq) == 1
    pa = next(c for c in ep if a in c)
    pb = next(c for c in ep if b in c)
    nq = eq[0]
    r1 = resolve(pa, nq, a)
    assert r1 == frozenset({3, 4, -b}), r1
    r2 = resolve(pb, r1, b)
    assert r2 == frozenset({3, 4}), r2


def check_definition_evaporates() -> None:
    e, a, b = 20, 1, 2
    defs = [
        frozenset({-e, a}),
        frozenset({-e, b}),
        frozenset({e, -a, -b}),
    ]
    for d in defs:
        assert expand_one(d, e, a, b) == [], (d, expand_one(d, e, a, b))


def check_factor_two() -> None:
    e, a, b = 20, 1, 2
    fixtures = [
        frozenset({3}),
        frozenset({3, e}),
        frozenset({3, -e}),
    ]
    assert all(len(expand_one(c, e, a, b)) <= 2 for c in fixtures)


def check_support_monotonicity() -> None:
    # Once an ancestor support needs >1 neighborhoods, union cannot make the
    # descendant support a subset of one of those same fixed neighborhoods.
    neighborhoods = [frozenset({1, 2}), frozenset({3, 4})]
    crossing = frozenset({1, 3})
    assert not any(crossing <= n for n in neighborhoods)
    descendant = crossing | {2}
    assert crossing <= descendant
    assert not any(descendant <= n for n in neighborhoods)


def main() -> None:
    check_non_e_pivot()
    check_e_pivot()
    check_definition_evaporates()
    check_factor_two()
    check_support_monotonicity()
    print("C025_E2R_L1F_NON_E_PIVOT_ALL_POLARITY_CASES = PASS")
    print("C025_E2R_L1F_E_PIVOT_TWO_STEP_SIMULATION = PASS")
    print("C025_E2R_L1F_EXTENSION_DEFINITION_EVAPORATION = PASS")
    print("C025_E2R_L1F_ONE_GATE_LINE_MULTIPLIER_LE_2 = PASS")
    print("C025_E2R_L1F_LOCAL_DESCENDANT_OF_CROSSING_REJECTED_BY_SUPPORT = PASS")
    print("claim_boundary = finite elimination mechanics only; asymptotic tradeoff uses the external NW heavy-width lower bound")


if __name__ == "__main__":
    main()
