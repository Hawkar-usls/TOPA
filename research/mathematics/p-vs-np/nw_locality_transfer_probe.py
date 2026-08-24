#!/usr/bin/env python3
"""C025-E2R-L1C: executable boundary between cardinality locality and NW graph locality.

This probe proves only set-theoretic locality/closure mechanics. It does not
transfer Sokolov's heavy-width theorem to ER3.
"""
from __future__ import annotations


def cardinality_local(support: set[int], kappa: int) -> bool:
    return len(support) <= kappa


def containing_neighborhood(support: set[int], neighborhoods: list[set[int]]) -> int | None:
    for i, neighborhood in enumerate(neighborhoods):
        if support <= neighborhood:
            return i
    return None


def nw_local(support: set[int], neighborhoods: list[set[int]]) -> bool:
    return containing_neighborhood(support, neighborhoods) is not None


def conjunction_support(left: set[int], right: set[int]) -> set[int]:
    return set(left | right)


def main() -> None:
    neighborhoods = [{1, 2}, {3, 4}]
    mixed = {1, 3}
    assert cardinality_local(mixed, 2)
    assert not nw_local(mixed, neighborhoods)

    # Same-neighborhood closure: union remains local.
    neighborhoods2 = [{1, 2, 3, 4}, {3, 4, 5, 6}]
    g = {1, 2}
    h = {2, 4}
    i_g = containing_neighborhood(g, neighborhoods2)
    i_h = containing_neighborhood(h, neighborhoods2)
    assert i_g == 0 and i_h == 0
    s = conjunction_support(g, h)
    assert s == {1, 2, 4}
    assert s <= neighborhoods2[0]
    assert nw_local(s, neighborhoods2)

    # Merely being local somewhere is insufficient: operands can live in
    # different neighborhoods and their conjunction can escape both.
    g2 = {1, 2}
    h2 = {5, 6}
    assert nw_local(g2, neighborhoods2)
    assert nw_local(h2, neighborhoods2)
    s2 = conjunction_support(g2, h2)
    assert not nw_local(s2, neighborhoods2)

    print("C025_E2R_L1C_KAPPA_LOCAL_TO_NW_LOCAL_TRANSFER = REFUTED")
    print("C025_E2R_L1C_SAME_NEIGHBORHOOD_EXTENSION_CLOSURE = PASS")
    print("C025_E2R_L1C_DIFFERENT_NEIGHBORHOOD_ESCAPE = PASS")
    print("claim_boundary = graph-locality mechanics only; heavy-width theorem transfer remains open")


if __name__ == "__main__":
    main()
