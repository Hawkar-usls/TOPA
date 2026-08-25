#!/usr/bin/env python3
"""Finite mechanics for RSPC tractable-language kill sweep.

Checks only closure-property counterexamples for Horn/Krom/affine semantics and
small B2 truth-table realizations. OBDD asymptotic lower bounds are external
literature theorems and are not proved by this script.
"""

from itertools import product


def bit_and(a, b):
    return tuple(x & y for x, y in zip(a, b))


def majority3(a, b, c):
    return tuple(1 if x + y + z >= 2 else 0 for x, y, z in zip(a, b, c))


def xor3(a, b, c):
    return tuple(x ^ y ^ z for x, y, z in zip(a, b, c))


def xor2(x, y):
    # B2 AND/NOT realization: (x or y) and not(x and y)
    x_or_y = not ((not x) and (not y))
    return x_or_y and not (x and y)


def or2(x, y):
    return not ((not x) and (not y))


def parity3(x, y, z):
    return xor2(xor2(x, y), z)


def check_horn_counterexample():
    models = [(0, 1), (1, 0)]
    assert all(xor2(*m) for m in models)
    meet = bit_and(*models)
    assert meet == (0, 0)
    assert not xor2(*meet)


def check_krom_counterexample():
    a, b, c = (1, 0, 0), (0, 1, 0), (0, 0, 1)
    assert parity3(*a) and parity3(*b) and parity3(*c)
    maj = majority3(a, b, c)
    assert maj == (0, 0, 0)
    assert not parity3(*maj)


def check_affine_counterexample():
    a, b, c = (0, 1), (1, 0), (1, 1)
    assert or2(*a) and or2(*b) and or2(*c)
    t = xor3(a, b, c)
    assert t == (0, 0)
    assert not or2(*t)


def check_b2_truth_tables():
    xor_rows = {(x, y): int(xor2(bool(x), bool(y))) for x, y in product((0, 1), repeat=2)}
    assert xor_rows == {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 0}
    or_rows = {(x, y): int(or2(bool(x), bool(y))) for x, y in product((0, 1), repeat=2)}
    assert or_rows == {(0, 0): 0, (0, 1): 1, (1, 0): 1, (1, 1): 1}
    par_rows = {(x, y, z): int(parity3(bool(x), bool(y), bool(z))) for x, y, z in product((0, 1), repeat=3)}
    assert sum(par_rows.values()) == 4


def main():
    check_horn_counterexample()
    check_krom_counterexample()
    check_affine_counterexample()
    check_b2_truth_tables()
    print("AKINATOR_RSPC_HORN_XOR_CLOSURE_COUNTEREXAMPLE = PASS")
    print("AKINATOR_RSPC_KROM_PARITY3_CLOSURE_COUNTEREXAMPLE = PASS")
    print("AKINATOR_RSPC_AFFINE_OR_CLOSURE_COUNTEREXAMPLE = PASS")
    print("AKINATOR_RSPC_CONSTANT_SIZE_B2_TRUTH_TABLES = PASS")
    print("OBDD_HWB_EXPONENTIAL_SIZE = EXTERNAL_THEOREM_NOT_CI")
    print("UNIVERSAL_TRACTABLE_FRONTIER_LANGUAGE = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
