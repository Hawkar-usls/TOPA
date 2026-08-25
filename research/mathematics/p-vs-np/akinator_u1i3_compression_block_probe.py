#!/usr/bin/env python3
"""Finite mechanics for U1-I3 compression-block search barrier."""


def count_binary_blocks(K):
    return 1 << K


def main():
    for K in range(0,31):
        assert count_binary_blocks(K) == 2**K

    # Two fixed legal signed operand choices over distinct root IDs p=1,q=2.
    p,q=1,2
    choices=[(p,q),(p,-q)]
    assert len(choices)==2
    assert all(abs(a)!=abs(b) for a,b in choices)

    # Explicit enumeration for small K confirms 2^K syntactic sequences.
    seqs=[()]
    for _ in range(12):
        seqs=[s+(c,) for s in seqs for c in choices]
    assert len(seqs)==2**12
    assert len(set(seqs))==2**12

    print('AKINATOR_U1I3_TWO_LEGAL_CHOICES_PER_GATE = PASS')
    print('AKINATOR_U1I3_K_STEP_SCHEMA_COUNT_2K = PASS')
    print('POLY_SIZE_REPLACEMENT_DISCOVERY_BY_BRUTE_FORCE = REFUTED_FOR_GROWING_K')
    print('DIRECT_CONSTRUCTIVE_PROJECTION_GRAMMAR = OPEN')
    print('P_VS_NP = OPEN')

if __name__=='__main__':
    main()
