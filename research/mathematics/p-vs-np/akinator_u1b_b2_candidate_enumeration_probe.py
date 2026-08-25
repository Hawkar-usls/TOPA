#!/usr/bin/env python3
"""Finite mechanics for complete one-step frozen-B2 candidate enumeration."""


def signed_literals(V):
    return [s * i for i in range(1, V + 1) for s in (-1, 1)]


def legal_pairs(V):
    lits = signed_literals(V)
    out = []
    for a in lits:
        for b in lits:
            if abs(a) == abs(b):
                continue
            out.append((a, b))
    return out


def canonical_unordered_pairs(V):
    lits = signed_literals(V)
    out = set()
    for a in lits:
        for b in lits:
            if abs(a) == abs(b):
                continue
            out.add(tuple(sorted((a, b))))
    return out


def extension_clauses(e, a, b):
    return [frozenset({-e, a}), frozenset({-e, b}), frozenset({e, -a, -b})]


def main():
    for V in range(2, 101):
        ordered = legal_pairs(V)
        assert len(ordered) <= 4 * V * V
        assert len(ordered) == 4 * V * (V - 1)
        canonical = canonical_unordered_pairs(V)
        assert len(canonical) <= len(ordered)

    # Constant-size definition mechanics.
    V = 7
    e = V + 1
    for a, b in legal_pairs(V)[:100]:
        clauses = extension_clauses(e, a, b)
        assert len(clauses) == 3
        assert all(len(c) <= 3 for c in clauses)
        assert all(abs(l) <= e for c in clauses for l in c)

    print("AKINATOR_U1B_B2_SIGNED_LITERAL_COUNT = PASS")
    print("AKINATOR_U1B_ALL_NEXT_B2_CANDIDATES_QUADRATIC = PASS")
    print("AKINATOR_U1B_CANONICAL_PAIR_DEDUP = PASS")
    print("AKINATOR_U1B_CONSTANT_DEFINITION_BYTES_MECHANICS = PASS")
    print("POLY_ONE_STEP_PROPOSAL = ANALYTICAL_BOUND_PLUS_FINITE_MECHANICS")
    print("POLY_GLOBAL_SELECTION = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
