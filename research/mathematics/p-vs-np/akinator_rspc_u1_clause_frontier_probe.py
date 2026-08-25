#!/usr/bin/env python3
"""Finite mechanics for U1 complete clause-frontier width dichotomy.

Checks exact clause-universe counting and a small width-bounded Resolution
saturation fixture. It does not prove expander G-PHP width lower bounds or any
asymptotic Akinator theorem.
"""

from math import comb


def universe(n: int, w: int) -> int:
    return sum((2 ** k) * comb(n, k) for k in range(0, min(w, n) + 1))


def tautological(clause):
    s = set(clause)
    return any(-x in s for x in s)


def resolve(a, b, p):
    # p in a, -p in b
    r = (set(a) - {p}) | (set(b) - {-p})
    if tautological(r):
        return None
    return frozenset(r)


def saturates_to_empty(initial, w):
    assert all(len(c) <= w for c in initial)
    known = set(map(frozenset, initial))
    changed = True
    while changed:
        changed = False
        old = list(known)
        new = set()
        for i, a in enumerate(old):
            for b in old[i + 1:]:
                for p in a:
                    if -p in b:
                        r = resolve(a, b, p)
                        if r is not None and len(r) <= w and r not in known:
                            if len(r) == 0:
                                return True
                            new.add(r)
        if new:
            known |= new
            changed = True
    return frozenset() in known


def check_counts():
    for n in range(3, 21):
        assert universe(n, 1) == 1 + 2 * n
        assert universe(n, 2) == 1 + 2 * n + 4 * comb(n, 2)
        # Fixed width 3 is bounded by a fixed cubic polynomial.
        assert universe(n, 3) <= 9 * (n + 1) ** 3

    # Growing linear width has at least the 2^w sign choices for one variable subset.
    for n in range(6, 31):
        w = n // 3
        assert universe(n, w) >= 2 ** w


def check_saturation():
    # (x1 v x2), (~x1 v x3), (~x2 v x3), (~x3)
    # Width-2 Resolution derives ~x1, ~x2 and then empty.
    F = [
        frozenset({1, 2}),
        frozenset({-1, 3}),
        frozenset({-2, 3}),
        frozenset({-3}),
    ]
    assert saturates_to_empty(F, 2)

    # A satisfiable width-2 fixture must not derive empty.
    G = [frozenset({1, 2}), frozenset({-1, 2})]
    assert not saturates_to_empty(G, 2)


def main():
    check_counts()
    check_saturation()
    print("AKINATOR_U1_CLAUSE_UNIVERSE_EXACT_COUNT = PASS")
    print("AKINATOR_U1_FIXED_WIDTH_POLY_COUNT_FINITE = PASS")
    print("AKINATOR_U1_GROWING_WIDTH_EXPONENTIAL_SUBCOUNT_FINITE = PASS")
    print("AKINATOR_U1_WIDTH_BOUNDED_SATURATION_FIXTURE = PASS")
    print("EXPANDER_GPHP_WIDTH_LOWER_BOUND = EXTERNAL_PLUS_FROZEN_TRANSFER_NOT_CI")
    print("SPARSE_WIDE_B2_INTERFACE = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
