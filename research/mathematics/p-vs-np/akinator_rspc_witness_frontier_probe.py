#!/usr/bin/env python3
"""Finite mechanics probe for the Akinator RSPC witness-frontier dichotomy.

This checks only finite parity/point-frontier mechanics and symbolic-intersection
reduction fixtures. It does not prove NP-completeness or any asymptotic selector
lower bound.
"""

from itertools import product


def parity(bits):
    return sum(bits) & 1


def point_macro(a, x):
    return all(ai == xi for ai, xi in zip(a, x))


def explicit_frontier_complete_requires_all_odd_points(n):
    sats = [a for a in product((0, 1), repeat=n) if parity(a) == 1]
    # Any total positive parity witness compatible with a total point witness a
    # must equal a exactly. Therefore all odd points are required.
    frontier = set(sats)
    assert len(frontier) == 2 ** (n - 1)
    for a in sats:
        assert parity(a) == 1
        assert point_macro(a, a)
        assert all((w == a) == all(wi == ai for wi, ai in zip(w, a)) for w in frontier)
        assert any(w == a for w in frontier)

    # Deleting even one required point breaks partner-completeness for that point.
    victim = sats[0]
    reduced = frontier - {victim}
    assert not any(w == victim for w in reduced)
    return len(frontier)


def cnf_eval(clauses, assignment):
    # literal encoding: positive i means x_i, negative -i means not x_i; variables are 1-based
    for clause in clauses:
        ok = False
        for lit in clause:
            val = assignment[abs(lit) - 1]
            ok |= bool(val) if lit > 0 else not bool(val)
        if not ok:
            return False
    return True


def symbolic_intersection_fixture():
    # F = (x1 or x2) and (~x1 or x2), satisfiable exactly when x2=1.
    F = [(1, 2), (-1, 2)]
    models = [a for a in product((0, 1), repeat=2) if cnf_eval(F, a)]
    assert models == [(0, 1), (1, 1)]

    # R_g := F, R_h := TRUE. Intersection nonempty iff F has a model.
    true_models = list(product((0, 1), repeat=2))
    inter = [a for a in models if a in true_models]
    assert inter == models and inter

    # Unsatisfiable fixture.
    U = [(1,), (-1,)]
    umodels = [a for a in product((0, 1), repeat=1) if cnf_eval(U, a)]
    assert umodels == []


def main():
    sizes = {}
    for n in range(2, 9):
        sizes[n] = explicit_frontier_complete_requires_all_odd_points(n)
        assert sizes[n] == 2 ** (n - 1)
    symbolic_intersection_fixture()

    print("AKINATOR_RSPC_EXPLICIT_PARITY_FRONTIER_FINITE = PASS")
    print("AKINATOR_RSPC_POINT_PARTNER_UNIQUE_COMPATIBILITY = PASS")
    print("AKINATOR_RSPC_SYMBOLIC_INTERSECTION_FINITE_REPLAY = PASS")
    print("EXPLICIT_FRONTIER_EXPONENTIAL_THEOREM = ANALYTICAL_COUNT_NOT_CI")
    print("SYMBOLIC_INTERSECTION_NP_COMPLETE = ANALYTICAL_REDUCTION_NOT_CI")
    print("UNIVERSAL_RESTRICTED_SELECTOR_FRONTIER = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
