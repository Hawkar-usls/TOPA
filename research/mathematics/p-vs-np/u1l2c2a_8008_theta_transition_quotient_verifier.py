#!/usr/bin/env python3
"""U1-L2C2A exact donor audit: 8008 transition coding + Ramanujan theta.

No SAT oracle, floating point, sampled valuation search, heuristic score, or CAS.
"""

from __future__ import annotations

from hashlib import sha256
import json
from math import ceil, log2

D = 128
CYCLE_8008 = [0b000, 0b001, 0b010, 0b101, 0b011, 0b111, 0b110, 0b100]


def poly_mul_binomial(poly: list[int], exponent: int, sign: int) -> list[int]:
    assert sign in (-1, 1)
    out = poly[:]
    for i, coeff in enumerate(poly):
        j = i + exponent
        if coeff and j <= D:
            out[j] += sign * coeff
    return out


def theta_exponent(n: int) -> int:
    value = n * (3 * n - 1)
    assert value % 2 == 0
    return value // 2


def theta_sum_coefficients() -> tuple[list[int], list[tuple[int, int]]]:
    coeff = [0] * (D + 1)
    terms: list[tuple[int, int]] = []
    # |n| > D+1 is certainly outside the degree-D window because E(n) is quadratic.
    for n in range(-(D + 1), D + 2):
        e = theta_exponent(n)
        if 0 <= e <= D:
            coeff[e] += 1
            terms.append((n, e))
    return coeff, terms


def theta_product_coefficients() -> tuple[list[int], list[tuple[str, int, int]]]:
    # (-q;q^3)_inf (-q^2;q^3)_inf (q^3;q^3)_inf
    poly = [0] * (D + 1)
    poly[0] = 1
    factors: list[tuple[str, int, int]] = []
    m = 1
    while True:
        exps = [
            ("PLUS_A", 3 * m - 2, +1),
            ("PLUS_B", 3 * m - 1, +1),
            ("MINUS_AB", 3 * m, -1),
        ]
        admitted = False
        for name, exponent, sign in exps:
            if exponent <= D:
                admitted = True
                poly = poly_mul_binomial(poly, exponent, sign)
                factors.append((name, exponent, sign))
        if not admitted:
            break
        m += 1
    return poly, factors


def verify_8008_cycle() -> dict:
    assert len(CYCLE_8008) == 8
    assert sorted(CYCLE_8008) == list(range(8))
    transition = {CYCLE_8008[i]: CYCLE_8008[(i + 1) % 8] for i in range(8)}
    assert len(transition) == 8
    cursor = CYCLE_8008[0]
    seen = []
    for _ in range(8):
        seen.append(cursor)
        cursor = transition[cursor]
    assert cursor == CYCLE_8008[0]
    assert len(set(seen)) == 8

    semantic_states = len(CYCLE_8008)
    min_bits = ceil(log2(semantic_states))
    assert min_bits == 3
    return {
        "cycle_decimal": CYCLE_8008,
        "cycle_binary": [format(x, "03b") for x in CYCLE_8008],
        "semantic_state_count_before": semantic_states,
        "semantic_state_count_after_bijective_relabel": semantic_states,
        "minimum_fixed_width_bits_before": min_bits,
        "minimum_fixed_width_bits_after": min_bits,
        "state_count_reduction": 0,
        "verdict": "RELABEL_ONLY_NOT_COMPRESSION",
    }


def verify_theta_identity() -> dict:
    sum_coeff, terms = theta_sum_coefficients()
    product_coeff, factors = theta_product_coefficients()
    assert sum_coeff == product_coeff
    nonzero = [(i, c) for i, c in enumerate(sum_coeff) if c]
    return {
        "degree": D,
        "sum_term_count_in_window": len(terms),
        "sum_terms": terms,
        "product_factor_count": len(factors),
        "nonzero_coefficient_count": len(nonzero),
        "max_abs_coefficient": max(abs(c) for c in sum_coeff),
        "coefficient_vector_sha256": sha256(json.dumps(sum_coeff, separators=(",", ":")).encode()).hexdigest(),
        "exact_coefficient_agreement": True,
    }


def verify_theta_recurrence() -> dict:
    forward_checks = 0
    backward_checks = 0
    checked_states: set[tuple[int, int]] = set()
    for n in range(-(D + 1), D + 2):
        e = theta_exponent(n)
        if not (0 <= e <= D):
            continue
        checked_states.add((n, e))

        ef = theta_exponent(n + 1)
        if 0 <= ef <= D:
            assert ef == e + 3 * n + 1
            forward_checks += 1

        eb = theta_exponent(n - 1)
        if 0 <= eb <= D:
            assert eb == e - 3 * n + 2
            backward_checks += 1

    assert forward_checks > 0 and backward_checks > 0
    return {
        "audited_state_count": len(checked_states),
        "forward_transition_checks": forward_checks,
        "backward_transition_checks": backward_checks,
        "state_coordinates": "(n,E(n))",
        "forward_rule": "(n,E)->(n+1,E+3n+1)",
        "backward_rule": "(n,E)->(n-1,E-3n+2)",
        "verdict": "EXACT_LOW_DIMENSIONAL_TRANSITION_STATE_FOR_THETA_FAMILY",
    }


def main() -> None:
    r8008 = verify_8008_cycle()
    rtheta = verify_theta_identity()
    rrec = verify_theta_recurrence()

    result = {
        "schema": "JANUS_U1L2C2A_8008_THETA_TRANSITION_QUOTIENT_RESULT",
        "status": "PASS_EXACT_DONOR_AUDIT",
        "claim_ceiling": "P_VS_NP_OPEN",
        "frozen_protocol_commit": "29b1743e50753c0cb2d1fa221bd3b2b5e68bcdbf",
        "intel_8008_transition_guard": r8008,
        "ramanujan_theta_exact_donor": rtheta,
        "theta_transition_recurrence": rrec,
        "proof_ledger": {
            "RELABEL_ONLY_REDUCES_SEMANTIC_STATE_COUNT": False,
            "BIJECTIVE_TRANSITION_RELABEL_PRESERVES_STATE_CARDINALITY": True,
            "RAMANUJAN_THETA_SPECIALIZED_SUM_PRODUCT_SLICE_EXACT": True,
            "THETA_SPECIALIZATION_HAS_EXACT_RECURRENCE_STATE": True,
            "ARBITRARY_B2_TO_THETA_MORPHISM": "OPEN_NOT_CLAIMED",
            "NONLITERAL_SAT_FACTOR_TRANSITION_MACRO": "OPEN",
            "P_EQUALS_NP": False,
        },
        "janus_method_update": {
            "admit": "PROOF_CARRYING_TRANSITION_MACRO_ONLY_IF_IT_QUOTIENTS_OR_MACRO_REPRESENTS_SEMANTIC_STATES_AND_SUPPORTS_DIRECT_EXISTS_UPDATE",
            "reject": "PRESENTATION_ONLY_RELABELLING_AS_COMPRESSION",
            "theta_role": "EXACT_SUM_PRODUCT_AND_RECURRENCE_DONOR_PENDING_SAT_SIDE_MORPHISM",
        },
        "next_gate": "U1-L2C2B_PROOF_CARRYING_NONLITERAL_TRANSITION_MACRO_MORPHISM",
    }

    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("U1L2C2A_RESULT_SHA256=" + sha256(packed).hexdigest())


if __name__ == "__main__":
    main()
