#!/usr/bin/env python3
"""Finite mechanics for U1-I1 Inner Product cofactor/projection separator.

Checks exact cofactor count, existential projection identity, and one-variable
algebraic projection identity on small finite instances. It does not prove a
universal B2 projection-compression theorem.
"""

from itertools import product


def ip_value(x,y):
    acc=0
    for a,b in zip(x,y):
        acc ^= (a & b)
    return acc


def parity_subset(mask,y):
    acc=0
    for i,b in enumerate(y):
        if (mask>>i)&1:
            acc ^= b
    return acc


def all_cofactors(k):
    ys=list(product((0,1),repeat=k))
    sigs=[]
    for x in product((0,1),repeat=k):
        sig=tuple(ip_value(x,y) for y in ys)
        sigs.append(sig)
    return sigs


def exists_all_x(k,y):
    return int(any(ip_value(x,y) for x in product((0,1),repeat=k)))


def or_y(y):
    return int(any(y))


def one_var_identity(y_i,R):
    lhs=int(any(((x & y_i) ^ R) for x in (0,1)))
    rhs=int(bool(y_i or R))
    return lhs,rhs


def main():
    for k in range(1,8):
        sigs=all_cofactors(k)
        assert len(sigs)==2**k
        assert len(set(sigs))==2**k

        # Cofactor signatures coincide with subset parities indexed by x-mask.
        ys=list(product((0,1),repeat=k))
        for mask,x in enumerate(product((0,1),repeat=k)):
            sig=tuple(ip_value(x,y) for y in ys)
            # product() order is lexicographic, not binary-mask order, so derive actual subset mask.
            actual=sum((bit<<i) for i,bit in enumerate(x))
            expected=tuple(parity_subset(actual,y) for y in ys)
            assert sig==expected

        for y in ys:
            assert exists_all_x(k,y)==or_y(y)

    for y_i,R in product((0,1),repeat=2):
        lhs,rhs=one_var_identity(y_i,R)
        assert lhs==rhs

    print("AKINATOR_U1I_IP_DISTINCT_COFACORS_2K_FINITE = PASS")
    print("AKINATOR_U1I_IP_FULL_PROJECTION_EQUALS_OR_FINITE = PASS")
    print("AKINATOR_U1I_IP_ONE_VAR_ALGEBRAIC_PROJECTION = PASS")
    print("IP_B2_LINEAR_SIZE = ANALYTICAL_CONSTRUCTION_NOT_CI")
    print("UNIVERSAL_LOCAL_REWRITE_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")


if __name__=='__main__':
    main()
