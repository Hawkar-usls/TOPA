#!/usr/bin/env python3
"""C025-E2R-L1 transitive support-locality probe.

This probe defines and checks the *restriction* only. It does not prove a lower
bound for ER3 or transfer any external heavy-width theorem.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Ext:
    var: int
    left: int
    right: int


def root_support(lit: int, root_vars: set[int], supports: dict[int, frozenset[int]]) -> frozenset[int]:
    v = abs(lit)
    if v in root_vars:
        return frozenset({v})
    if v in supports:
        return supports[v]
    raise ValueError(f"unknown/forward variable {v}")


def compute_supports(root_vars: set[int], definitions: list[Ext]) -> dict[int, frozenset[int]]:
    if any(v <= 0 for v in root_vars):
        raise ValueError("root vars must be positive")
    supports: dict[int, frozenset[int]] = {}
    used = set(root_vars)
    last = max(root_vars, default=0)
    for d in definitions:
        if d.var <= last or d.var in used:
            raise ValueError("extension ids must be fresh/increasing")
        left = root_support(d.left, root_vars, supports)
        right = root_support(d.right, root_vars, supports)
        supports[d.var] = frozenset(left | right)
        used.add(d.var)
        last = d.var
    return supports


def is_kappa_local(root_vars: set[int], definitions: list[Ext], kappa: int) -> bool:
    if kappa < 1:
        return False
    supports = compute_supports(root_vars, definitions)
    return all(len(s) <= kappa for s in supports.values())


def main() -> None:
    roots = {1, 2, 3, 4, 5, 6}

    # Chain grows support exactly by one root each time.
    chain = [
        Ext(7, 1, 2),
        Ext(8, 7, 3),
        Ext(9, 8, 4),
        Ext(10, 9, 5),
        Ext(11, 10, 6),
    ]
    supports = compute_supports(roots, chain)
    assert [len(supports[v]) for v in range(7, 12)] == [2, 3, 4, 5, 6]
    assert is_kappa_local(roots, chain[:3], 4)
    assert not is_kappa_local(roots, chain, 4)

    # Balanced composition tracks transitive support, not direct fan-in (which is always 2).
    balanced = [
        Ext(7, 1, 2),
        Ext(8, 3, 4),
        Ext(9, 5, 6),
        Ext(10, 7, 8),
        Ext(11, 10, 9),
    ]
    b = compute_supports(roots, balanced)
    assert b[7] == frozenset({1, 2})
    assert b[10] == frozenset({1, 2, 3, 4})
    assert b[11] == frozenset({1, 2, 3, 4, 5, 6})

    # Polarity does not change support.
    polar = [Ext(7, -1, -2), Ext(8, -7, 3)]
    p = compute_supports({1, 2, 3}, polar)
    assert p[8] == frozenset({1, 2, 3})

    # Forward dependency is rejected.
    try:
        compute_supports({1, 2}, [Ext(3, 1, 4), Ext(4, 1, 2)])
    except ValueError:
        pass
    else:
        raise AssertionError("forward dependency accepted")

    print("C025_E2R_L1_TRANSITIVE_SUPPORT = PASS")
    print("C025_E2R_L1_POLARITY_INVARIANCE = PASS")
    print("C025_E2R_L1_FORWARD_DEPENDENCY_REJECTION = PASS")
    print("C025_E2R_L1_KAPPA_LOCAL_ADMISSION = PASS")
    print("claim_boundary = locality restriction mechanics only; no ER3 lower bound or literature transfer established")


if __name__ == "__main__":
    main()
