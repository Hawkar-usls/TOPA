#!/usr/bin/env python3
"""Finite mechanics for the bounded-cover Akinator RSPC lane.

This checks only the algebra 2^(C*Delta) <= (2N)^C under the frozen direct
parity accounting assumption N >= 2^(Delta-1), and small exhaustive residual
survival mechanics. It does NOT prove a fixed-C universal selector theorem.
"""

from itertools import product


def check_encoding_algebra() -> None:
    for Delta in range(1, 13):
        # Minimal admissible encoded length for the algebra check.
        N = 2 ** (Delta - 1)
        assert 2 ** Delta <= 2 * N
        for C in range(1, 6):
            lhs = 2 ** (C * Delta)
            rhs = (2 * N) ** C
            assert lhs <= rhs


def nonconstant(vals):
    return set(vals) == {False, True}


def check_exact_survival_small_supports() -> None:
    # Synthetic functions on k support bits. Exhaustive enumeration exactly
    # finds the first 0/1 witness pair whenever the function is nonconstant.
    for k in range(1, 5):
        xs = list(product((False, True), repeat=k))
        table_size = 1 << k
        for mask in range(1 << table_size):
            # Keep runtime finite: full sweep for k<=3, selected masks for k=4.
            if k == 4 and mask not in (0, 1, 3, 0xAAAA, 0x5555, (1 << table_size) - 1):
                continue
            vals = [bool((mask >> i) & 1) for i in range(table_size)]
            got_nonconstant = nonconstant(vals)
            zero = next((xs[i] for i, v in enumerate(vals) if not v), None)
            one = next((xs[i] for i, v in enumerate(vals) if v), None)
            assert got_nonconstant == (zero is not None and one is not None)


def check_candidate_count() -> None:
    for V in range(1, 100):
        not_candidates = V
        and_candidates = V * V
        assert not_candidates + and_candidates <= V * V + V


def main() -> None:
    check_encoding_algebra()
    check_exact_survival_small_supports()
    check_candidate_count()
    print("AKINATOR_BC_FIXED_C_ENCODING_ALGEBRA = PASS")
    print("AKINATOR_BC_EXACT_SURVIVAL_SMALL_SUPPORT_REPLAY = PASS")
    print("AKINATOR_BC_POLY_CANDIDATE_COUNT = PASS")
    print("AKINATOR_BC_FIXED_C_SURVIVAL_POLY = ANALYTIC_INPUT_RELATIVE_BOUND_NOT_CI")
    print("AKINATOR_BC_C1_GLOBAL_ESCAPE = REFUTED_BY_PRIOR_NW_LOCAL_TRANSFER_NOT_CI")
    print("AKINATOR_BC_EXISTS_FIXED_C_GT1_SUFFICIENT = OPEN")
    print("AKINATOR_BC_EVERY_FIXED_C_INSUFFICIENT = NOT_PROVED")
    print("POLYNOMIAL_AKINATOR = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
