#!/usr/bin/env python3
"""Finite mechanics for PHP certified-stage-rank positive control.

Checks only the rank decrement algebra and constant-overhead B2 truth-table
encoding of Cook's macro x' = a OR (b AND c). It does not reproduce Cook's
asymptotic O(n^4) ER proof theorem.
"""

from itertools import product


def cook_macro(a,b,c):
    return a or (b and c)


def b2_macro(a,b,c):
    t = b and c
    u = (not a) and (not t)
    return not u


def stage_rank(m):
    assert m >= 1
    return m-1


def main():
    for a,b,c in product((False,True), repeat=3):
        assert cook_macro(a,b,c) == b2_macro(a,b,c)

    for n in range(2,501):
        ranks=[stage_rank(m) for m in range(n,0,-1)]
        assert ranks[0] == n-1
        assert ranks[-1] == 0
        for x,y in zip(ranks,ranks[1:]):
            assert y == x-1
        assert len(ranks)-1 == n-1

    print("AKINATOR_U1F_COOK_MACRO_B2_TRUTH_EQUIVALENCE = PASS")
    print("AKINATOR_U1F_PHP_STAGE_RANK_STRICT_DESCENT = PASS")
    print("AKINATOR_U1F_PHP_STAGE_COUNT_LINEAR = PASS")
    print("COOK_PHP_O_N4_ER_PROOF = EXTERNAL_THEOREM_NOT_CI")
    print("UNIVERSAL_CERTIFIED_STAGE_DECOMPOSITION = OPEN")
    print("P_VS_NP = OPEN")

if __name__=='__main__':
    main()
