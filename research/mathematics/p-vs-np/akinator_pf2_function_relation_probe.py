#!/usr/bin/env python3
"""Finite mechanics for PF2 function-to-relation projection barrier."""

from itertools import product


def gate_e(x: int, y: int) -> int:
    return x & y


def projected_relation_single():
    rel = set()
    for e, y in product((0, 1), repeat=2):
        ok = any(e == gate_e(x, y) for x in (0, 1))
        if ok:
            rel.add((e, y))
    return rel


def projected_relation_pair():
    # t is fixed true; e1=x&t=x, e2=(not x)&t=not x.
    rel = set()
    for e1, e2 in product((0, 1), repeat=2):
        ok = any(e1 == x and e2 == (1 - x) for x in (0, 1))
        if ok:
            rel.add((e1, e2))
    return rel


def main() -> None:
    single = projected_relation_single()
    assert single == {(0, 0), (0, 1), (1, 1)}
    # At y=1 both e outputs are admitted, so no total Boolean function e=h(y)
    # can have this exact graph.
    y1_values = {e for e, y in single if y == 1}
    assert y1_values == {0, 1}

    pair = projected_relation_pair()
    assert pair == {(0, 1), (1, 0)}
    m1 = {a for a, _ in pair}
    m2 = {b for _, b in pair}
    assert m1 == {0, 1} and m2 == {0, 1}
    cartesian = {(a, b) for a in m1 for b in m2}
    assert pair < cartesian
    assert (0, 0) in cartesian - pair and (1, 1) in cartesian - pair

    print("AKINATOR_PF2_FUNCTION_GRAPH_TO_RELATION = PASS")
    print("AKINATOR_PF2_PER_MACRO_MARGINAL_CORRELATION_LOSS = PASS")
    print("LIVE_WIDTH_DP_BRIDGE = IMPORTED_INTERNAL_THEOREM_NOT_REPROVED_HERE")
    print("UNIVERSAL_POLY_BOUNDARY_QUOTIENT = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
