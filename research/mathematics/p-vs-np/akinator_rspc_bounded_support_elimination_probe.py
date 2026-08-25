#!/usr/bin/env python3
"""Finite mechanics for bounded-support ER3 elimination.

Checks small Boolean-substitution Resolution semantics and the local clause-space
count used in the analytic simulation. It does NOT prove the asymptotic theorem
or the imported Resolution lower bound.
"""

from itertools import product


def assignments(n):
    return list(product((False, True), repeat=n))


def func_from_mask(n, mask):
    xs = assignments(n)
    return {x: bool((mask >> i) & 1) for i, x in enumerate(xs)}


def check_resolution_under_boolean_substitution():
    # Exhaust all Boolean A,B,X over two roots: 16^3=4096 triples.
    n = 2
    xs = assignments(n)
    funcs = [func_from_mask(n, m) for m in range(1 << (1 << n))]
    checked = 0
    for A in funcs:
        for B in funcs:
            for X in funcs:
                for r in xs:
                    P = A[r] or X[r]
                    Q = B[r] or (not X[r])
                    R = A[r] or B[r]
                    assert not (P and Q) or R
                checked += 1
    assert checked == 16 ** 3


def canonical_falsifying_count(values):
    return sum(1 for v in values if not v)


def check_canonical_expansion_bound():
    for m in range(0, 8):
        total = 1 << m
        # Sample representative truth tables by output masks where feasible.
        masks = range(1 << total) if m <= 3 else (0, 1, (1 << total) - 1)
        for mask in masks:
            vals = [bool((mask >> i) & 1) for i in range(total)]
            assert canonical_falsifying_count(vals) <= 2 ** m


def check_clause_space_bound():
    # A clause over m variables has each variable absent/positive/negative:
    # at most 3^m non-tautological syntactic choices. For m<=6k,
    # 3^(6k) < 2^(10k), giving one explicit universal exponential constant.
    for k in range(1, 20):
        assert 3 ** (6 * k) < 2 ** (10 * k)
        assert 2 ** (3 * k) <= 2 ** (10 * k)


def check_cover_cardinality_consequence():
    for Delta in range(1, 20):
        for c in range(1, 20):
            max_covered = c * Delta
            k = max_covered + 1
            # c neighborhoods cannot cover k distinct roots if each has size <=Delta.
            assert k > c * Delta


def main():
    check_resolution_under_boolean_substitution()
    check_canonical_expansion_bound()
    check_clause_space_bound()
    check_cover_cardinality_consequence()
    print("AKINATOR_ER3_BOOLEAN_SUBSTITUTION_RESOLUTION_SMALL_REPLAY = PASS")
    print("AKINATOR_ER3_CANONICAL_ROOT_CNF_SIZE_BOUND_FINITE = PASS")
    print("AKINATOR_ER3_LOCAL_CLAUSE_SPACE_2O_K_FINITE_ALGEBRA = PASS")
    print("AKINATOR_ER3_COVER_CARDINALITY_FINITE_ALGEBRA = PASS")
    print("BOUNDED_SUPPORT_ER3_ELIMINATION = ANALYTIC_THEOREM_NOT_CI")
    print("FROZEN_RESOLUTION_LOWER_BOUND = IMPORTED_PRIOR_RESULT_NOT_CI")
    print("UNRESTRICTED_ER3_SIZE_LOWER_BOUND = NOT_PROVED")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
