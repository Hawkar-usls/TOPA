#!/usr/bin/env python3
"""C025-E2R barrier probe.

This executable does NOT prove an ER lower bound. It checks two narrow facts:

1) K Boolean extension bits can induce at most 2^K signatures on root assignments,
   so pure assignment-class counting cannot force K > n.
2) The frozen B2 gate e <-> (a AND b), with negated input literals allowed,
   computes parity on n roots using exactly 3(n-1) extension gates, while the
   flat root-only CNF/DNF representation of parity needs 2^(n-1) cases.

The probe is a falsifier for naive additive class/case-count invariants.
"""

from __future__ import annotations

from itertools import product
from math import ceil, log2


def signature_ceiling(n: int, k: int) -> int:
    if n < 0 or k < 0:
        raise ValueError("n,k must be nonnegative")
    return min(1 << n, 1 << k)


def class_count_lower_bound(m: int) -> int:
    if m < 1:
        raise ValueError("m must be positive")
    return ceil(log2(m)) if m > 1 else 0


def parity(values: tuple[bool, ...]) -> bool:
    out = False
    for value in values:
        out ^= value
    return out


def xor_via_three_and_gates(y: bool, x: bool) -> bool:
    t1 = y and x
    t2 = (not y) and (not x)
    y_next = (not t1) and (not t2)
    return y_next


def parity_via_b2(values: tuple[bool, ...]) -> tuple[bool, int]:
    if not values:
        raise ValueError("need at least one root variable")
    y = values[0]
    gates = 0
    for x in values[1:]:
        y = xor_via_three_and_gates(y, x)
        gates += 3
    return y, gates


def clause_is_implicate_of_parity_one(n: int, clause: tuple[int, ...]) -> bool:
    """Brute-force whether clause is implied by PARITY_n = 1."""
    vars_seen = {abs(lit) for lit in clause}
    if any(v < 1 or v > n for v in vars_seen):
        raise ValueError("literal outside root range")
    if any(-lit in clause for lit in clause):
        return True  # tautological clause
    for bits in product([False, True], repeat=n):
        if not parity(bits):
            continue
        sat = False
        for lit in clause:
            value = bits[abs(lit) - 1]
            sat |= value if lit > 0 else (not value)
        if not sat:
            return False
    return True


def verify_no_short_nontrivial_parity_implicates(n: int) -> None:
    # Exhaust all clauses of width < n for small n. No non-tautological one may
    # be implied by odd parity.
    literals = tuple(range(1, n + 1))
    for choices in product([-1, 0, 1], repeat=n):
        clause = tuple(sign * var for sign, var in zip(choices, literals) if sign)
        if not clause or len(clause) >= n:
            continue
        assert not clause_is_implicate_of_parity_one(n, clause), (n, clause)


def main() -> None:
    # Semantic signature ceiling: even the strongest possible partition has
    # M <= 2^n classes, so log2(M) <= n.
    for n in range(1, 13):
        m = 1 << n
        assert class_count_lower_bound(m) == n
        for k in range(0, n + 4):
            assert signature_ceiling(n, k) <= (1 << k)
            assert signature_ceiling(n, k) <= (1 << n)

    # Exact B2 parity construction.
    for n in range(1, 10):
        for bits in product([False, True], repeat=n):
            got, gates = parity_via_b2(bits)
            assert got == parity(bits)
            assert gates == 3 * (n - 1)

    # Brute-check the key prime-implicate fact for small n.
    for n in range(2, 7):
        verify_no_short_nontrivial_parity_implicates(n)

    n = 12
    gates = 3 * (n - 1)
    flat_cases = 1 << (n - 1)

    print("C025_E2R_SEMANTIC_SIGNATURE_CEILING = PASS")
    print("C025_E2R_CLASS_COUNT_SUPERPOLY_METHOD = REFUTED")
    print("C025_E2R_PARITY_B2_COMPRESSION = PASS")
    print("C025_E2R_FLAT_CASE_COUNT_INVARIANT = REFUTED")
    print(f"fixture_n = {n}")
    print(f"fixture_extension_gates = {gates}")
    print(f"fixture_flat_cnf_or_dnf_cases = {flat_cases}")
    print(
        "claim_boundary = falsifies naive semantic/flat-case extension-count "
        "invariants only; unrestricted ER3 extension-count lower bound remains open"
    )


if __name__ == "__main__":
    main()
