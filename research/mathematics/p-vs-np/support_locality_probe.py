#!/usr/bin/env python3
"""C025-E2R-L1 transitive support-locality probe.

This probe defines/checks the support-local restriction and the root-restriction
monotonicity theorem. It does not prove a lower bound for unrestricted ER3 or
transfer any external heavy-width theorem.
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


def restricted_support_upper_bound(
    supports: dict[int, frozenset[int]],
    assigned_root_vars: set[int],
) -> dict[int, frozenset[int]]:
    """Sound upper bound after restricting root variables.

    Any surviving residual extension function can depend only on previously
    depended-on roots that were not fixed by the restriction. Constant/alias
    simplification may remove even more dependencies, never add them.
    """
    return {
        ext: frozenset(root for root in support if root not in assigned_root_vars)
        for ext, support in supports.items()
    }


def main() -> None:
    roots = {1, 2, 3, 4, 5, 6}

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

    polar = [Ext(7, -1, -2), Ext(8, -7, 3)]
    p = compute_supports({1, 2, 3}, polar)
    assert p[8] == frozenset({1, 2, 3})

    # Root-restriction monotonicity: no support can gain a root variable.
    for assigned in (
        set(),
        {1},
        {1, 3},
        {2, 4, 6},
        roots,
    ):
        restricted = restricted_support_upper_bound(b, assigned)
        for ext, residual_support in restricted.items():
            assert residual_support <= b[ext]
            assert residual_support.isdisjoint(assigned)
            assert len(residual_support) <= len(b[ext])

    # Therefore kappa-locality is preserved under root restrictions.
    local_defs = balanced[:4]  # max support size 4
    local_supports = compute_supports(roots, local_defs)
    assert max(map(len, local_supports.values())) <= 4
    restricted = restricted_support_upper_bound(local_supports, {1, 3, 5})
    assert max(map(len, restricted.values())) <= 4

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
    print("C025_E2R_L1_ROOT_RESTRICTION_SUPPORT_MONOTONICITY = PASS")
    print("C025_E2R_L1_ROOT_RESTRICTION_LOCALITY_STABILITY = PASS")
    print("claim_boundary = support/locality mechanics only; no unrestricted ER3 lower bound or literature transfer established")


if __name__ == "__main__":
    main()
