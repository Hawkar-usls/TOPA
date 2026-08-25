#!/usr/bin/env python3
"""Finite mechanics for the polynomial-deck global-potential closure lemma.

This is only algebra/mechanics. It does not construct a universal SAT potential.
"""


def deterministic_descent(mu0, deck_fn, next_fn, mu_fn):
    state = mu0
    steps = 0
    while mu_fn(state) > 0:
        chosen = None
        for cand in deck_fn(state):
            nxt = next_fn(state, cand)
            if mu_fn(nxt) < mu_fn(state):
                chosen = nxt
                break
        assert chosen is not None
        state = chosen
        steps += 1
        assert steps <= mu0
    return steps


def main():
    # Synthetic exact potential: state is integer rank r. Polynomial deck contains
    # several legal moves, at least one of which lowers r.
    def deck(r):
        return list(range(0, min(7, r + 2)))

    def nxt(r, c):
        if c == 0:
            return max(0, r - 1)
        return r + (c % 2)

    mu = lambda r: r

    for mu0 in range(1, 500):
        steps = deterministic_descent(mu0, deck, nxt, mu)
        assert steps == mu0

    # B2 candidate bound algebra under a polynomial state-variable bound V <= N^a.
    for N in range(2, 100):
        for a in (1, 2, 3):
            V = N ** a
            deck_bound = 4 * V * V
            assert deck_bound == 4 * (N ** (2 * a))

    print("AKINATOR_U1C_POLY_DECK_SCAN_MECHANICS = PASS")
    print("AKINATOR_U1C_STRICT_INTEGER_DESCENT_STEP_BOUND = PASS")
    print("AKINATOR_U1C_B2_DECK_POLY_COMPOSITION_ALGEBRA = PASS")
    print("UNIVERSAL_SAT_DESCENT_POTENTIAL = NOT_CONSTRUCTED")
    print("RESOLUTION_AUTOMATABILITY_NP_HARD = EXTERNAL_THEOREM_NOT_CI")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
