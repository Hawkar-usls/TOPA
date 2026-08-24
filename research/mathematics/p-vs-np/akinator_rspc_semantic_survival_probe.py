#!/usr/bin/env python3
"""Finite mechanics for C025 Akinator RSPC.

This script checks finite instances of the SAT -> residual-nonconstancy reduction
and the explicit one-witness compositional counterexample. It does NOT prove
NP-completeness or any asymptotic lower bound; those are analytic complexity
claims in the accompanying note.
"""

from __future__ import annotations

from itertools import product


def all_assignments(n: int):
    yield from product((False, True), repeat=n)


def is_nonconstant(values):
    vals = set(values)
    return vals == {False, True}


def check_sat_to_nonconstancy_reduction() -> None:
    # Exhaust every Boolean function F:{0,1}^n->{0,1} for n<=3.
    # C_F(z,x)=z AND F(x) is nonconstant iff F has at least one satisfying input.
    checked = 0
    for n in range(0, 4):
        xs = list(all_assignments(n))
        table_len = len(xs)
        for table_mask in range(1 << table_len):
            table = {
                x: bool((table_mask >> i) & 1)
                for i, x in enumerate(xs)
            }
            sat = any(table.values())
            c_values = []
            for z in (False, True):
                for x in xs:
                    c_values.append(z and table[x])
            assert is_nonconstant(c_values) == sat
            checked += 1
    assert checked == 2 + 4 + 16 + 256


def a(x: bool, y: bool) -> bool:
    return x or y


def b(x: bool, y: bool) -> bool:
    return x or (not y)


def check_single_witness_counterexample() -> None:
    w1_a = (False, True)
    w1_b = (False, False)
    assert a(*w1_a) is True
    assert b(*w1_b) is True
    assert w1_a != w1_b  # same support, conflicting retained witnesses

    common_positive = [
        xy for xy in all_assignments(2)
        if a(*xy) and b(*xy)
    ]
    assert common_positive
    assert any(x is True for x, _ in common_positive)

    conj_values = [a(x, y) and b(x, y) for x, y in all_assignments(2)]
    assert is_nonconstant(conj_values)


def check_polynomial_pair_enumeration() -> None:
    # Finite algebra check only: ordered pairs grow quadratically in explicit V.
    for v in range(2, 100):
        pairs = [(i, j) for i in range(v) for j in range(v) if i != j]
        assert len(pairs) == v * (v - 1)


def main() -> None:
    check_sat_to_nonconstancy_reduction()
    check_single_witness_counterexample()
    check_polynomial_pair_enumeration()
    print("AKINATOR_RSPC_SAT_TO_NONCONSTANCY_FINITE_REPLAY = PASS")
    print("AKINATOR_RSPC_SINGLE_WITNESS_COUNTEREXAMPLE = PASS")
    print("AKINATOR_RSPC_PAIR_ENUMERATION_FINITE_ALGEBRA = PASS")
    print("GENERAL_RESIDUAL_NONCONSTANCY_NP_COMPLETE = ANALYTIC_REDUCTION_NOT_CI")
    print("WITNESS_FRONTIER_SUPERPOLY_LOWER_BOUND = NOT_PROVED")
    print("SOURCE_MATCHED_RESTRICTION_HARDNESS = OPEN")
    print("PROOF_CARRYING_STRUCTURAL_SELECTOR = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
