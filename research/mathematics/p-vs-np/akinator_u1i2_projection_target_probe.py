#!/usr/bin/env python3
from itertools import product

def project_x_and_f(table):
    return {y: int(any((x and bool(v)) for x in (0,1))) for y,v in table.items()}

def main():
    for m in range(4):
        ys=list(product((0,1), repeat=m))
        for mask in range(1 << len(ys)):
            f={y:(mask >> i) & 1 for i,y in enumerate(ys)}
            p=project_x_and_f(f)
            assert p == f
            assert all(p.values()) == all(f.values())
    print('AKINATOR_U1I2_X_AND_F_PROJECTION_EQUALS_F_FINITE = PASS')
    print('AKINATOR_U1I2_PROJ_TRUE_IFF_TAUTOLOGY_FINITE = PASS')
    print('PROJ_TRUE_B2_CONP_COMPLETE = ANALYTICAL_REDUCTION_NOT_CI')
    print('GENERAL_TARGET_EQUIVALENCE_CONP_COMPLETE = ANALYTICAL_REDUCTION_NOT_CI')
    print('UNIVERSAL_PROOF_CARRYING_REWRITE_COMPLETENESS = OPEN')
    print('P_VS_NP = OPEN')

if __name__ == '__main__':
    main()
