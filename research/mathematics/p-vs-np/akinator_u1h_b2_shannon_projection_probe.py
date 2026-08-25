#!/usr/bin/env python3
"""Finite mechanics for U1-H B2 Shannon projection baseline.

Checks Boolean projection identity over all 3-variable truth tables, B2 OR gadget,
and the exact no-sharing size recurrence. It does not prove a lower bound on
minimum B2 projection size.
"""

from itertools import product


def b2_or(a,b):
    u=(not a) and (not b)
    return not u


def projection_table(table):
    # table key=(x,y1,y2), project x existentially
    return {(y1,y2): bool(table[(0,y1,y2)] or table[(1,y1,y2)])
            for y1,y2 in product((0,1),repeat=2)}


def check_all_truth_tables():
    inputs=list(product((0,1),repeat=3))
    for mask in range(1<<len(inputs)):
        table={inp: bool((mask>>i)&1) for i,inp in enumerate(inputs)}
        proj=projection_table(table)
        for y in product((0,1),repeat=2):
            lhs=proj[y]
            rhs=b2_or(table[(0,*y)],table[(1,*y)])
            assert lhs==rhs


def check_recurrence():
    for S0 in range(0,51):
        S=S0
        for k in range(0,16):
            expected=(2**k)*(S0+1)-1
            assert S==expected
            S=2*S+1


def main():
    for a,b in product((False,True),repeat=2):
        assert b2_or(a,b)==(a or b)
    check_all_truth_tables()
    check_recurrence()
    print("AKINATOR_U1H_B2_OR_GADGET = PASS")
    print("AKINATOR_U1H_EXISTENTIAL_SHANNON_IDENTITY_ALL_3VAR_TABLES = PASS")
    print("AKINATOR_U1H_NAIVE_NO_SHARING_SIZE_RECURRENCE = PASS")
    print("MINIMUM_B2_PROJECTION_SIZE_LOWER_BOUND = NOT_PROVED")
    print("PROOF_CARRYING_B2_PROJECTION_COMPRESSION = OPEN")
    print("P_VS_NP = OPEN")

if __name__=='__main__':
    main()
