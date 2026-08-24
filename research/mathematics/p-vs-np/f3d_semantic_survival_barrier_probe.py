#!/usr/bin/env python3
"""Finite mechanics replay for C025-E2R-L1G-F3-D semantic survival barrier.

This script validates small instances of the explicit B2 counterfamily from
C025_E2R_L1G_F3D_SEMANTIC_SURVIVAL_BARRIER.md. It is not an asymptotic proof.
"""
from __future__ import annotations

from itertools import product
from typing import Dict, Iterable, List, Sequence, Set, Tuple

Literal = Tuple[str, str, bool]  # kind, name, negated
Gate = Tuple[str, Literal, Literal]


def root(name: str, neg: bool = False) -> Literal:
    return ("root", name, neg)


def ext(name: str, neg: bool = False) -> Literal:
    return ("ext", name, neg)


def build_counterfamily(B: int, D: int) -> Tuple[Set[str], List[Gate], str]:
    if B < 2 or D < 1:
        raise ValueError("require B>=2 and D>=1")

    roots: Set[str] = {"z"}
    gates: List[Gate] = []
    tops: List[str] = []

    for j in range(1, B + 1):
        y = f"y{j}"
        roots.add(y)
        name = f"g{j}_1"
        gates.append((name, root("z"), root(y)))
        prev = name
        for t in range(2, D + 1):
            name = f"g{j}_{t}"
            gates.append((name, root("z"), ext(prev, True)))
            prev = name
        tops.append(prev)

    agg = "A2"
    gates.append((agg, ext(tops[0], True), ext(tops[1], True)))
    for j in range(3, B + 1):
        nxt = f"A{j}"
        gates.append((nxt, ext(agg), ext(tops[j - 1], True)))
        agg = nxt

    return roots, gates, agg


def transitive_supports(roots: Set[str], gates: Sequence[Gate]) -> Dict[str, Set[str]]:
    support: Dict[str, Set[str]] = {r: {r} for r in roots}
    for name, a, b in gates:
        support[name] = set(support[a[1]]) | set(support[b[1]])
    return support


def is_local(support: Set[str], neighborhoods: Sequence[Set[str]]) -> bool:
    return any(support <= hood for hood in neighborhoods)


def structural_metrics(
    roots: Set[str], gates: Sequence[Gate], neighborhoods: Sequence[Set[str]]
) -> Tuple[int, int]:
    support = transitive_supports(roots, gates)
    crossing = {name: not is_local(support[name], neighborhoods) for name, _, _ in gates}
    gate_map = {name: (a, b) for name, a, b in gates}

    depth: Dict[str, int] = {}
    for name, a, b in gates:
        candidates = [0]
        for operand in (a, b):
            if operand[0] != "ext":
                continue
            child = operand[1]
            inc = int(operand[2] and crossing.get(child, False) and crossing.get(name, False))
            candidates.append(depth[child] + inc)
        depth[name] = max(candidates)

    memo: Dict[str, Set[Tuple[str, str]]] = {}

    def frontier(name: str) -> Set[Tuple[str, str]]:
        if name in memo:
            return set(memo[name])
        if not crossing.get(name, False):
            memo[name] = set()
            return set()
        out: Set[Tuple[str, str]] = set()
        for operand in gate_map[name]:
            if operand[0] != "ext":
                continue
            child = operand[1]
            if not crossing.get(child, False):
                continue
            if operand[2]:
                out.add((child, name))
            else:
                out.update(frontier(child))
        memo[name] = set(out)
        return out

    b = max((len(frontier(name)) for name, _, _ in gates), default=0)
    d = max(depth.values(), default=0)
    return b, d


def exact_residual_truth_tables(
    roots: Set[str], gates: Sequence[Gate], rho: Dict[str, int]
) -> Dict[str, Tuple[int, ...]]:
    free = sorted(roots - set(rho))
    tables: Dict[str, List[int]] = {name: [] for name, _, _ in gates}

    for bits in product((0, 1), repeat=len(free)):
        assignment = dict(rho)
        assignment.update(dict(zip(free, bits)))
        values: Dict[str, int] = {}

        def value(literal: Literal) -> int:
            kind, name, neg = literal
            raw = assignment[name] if kind == "root" else values[name]
            return 1 - raw if neg else raw

        for name, a, b in gates:
            values[name] = value(a) & value(b)
            tables[name].append(values[name])

    return {name: tuple(values) for name, values in tables.items()}


def is_constant(table: Tuple[int, ...]) -> bool:
    return bool(table) and all(v == table[0] for v in table)


def replay(B: int, D: int) -> Dict[str, int]:
    roots, gates, final = build_counterfamily(B, D)

    # Abstract locality hypergraph: z and each y_j are individually local,
    # but no neighborhood contains both z and any y_j.
    neighborhoods = [{"z"}] + [{r} for r in sorted(roots) if r != "z"]

    b, d = structural_metrics(roots, gates, neighborhoods)
    assert b >= B, (B, D, b, d)
    assert d >= D, (B, D, b, d)
    assert len(gates) == B * D + (B - 1)

    tables = exact_residual_truth_tables(roots, gates, {"z": 0})
    assert all(is_constant(table) for table in tables.values())
    assert set(tables[final]) == {1}

    return {
        "B": B,
        "D": D,
        "gates": len(gates),
        "pre_b": b,
        "pre_d": d,
        "restriction_size": 1,
        "surviving_nonconstant_extensions": 0,
    }


def main() -> None:
    rows = []
    for B in range(2, 7):
        for D in range(1, 7):
            rows.append(replay(B, D))

    assert len(rows) == 30
    print("C025_F3D_D0_COUNTERFAMILY_FINITE_REPLAY = PASS")
    print("C025_F3D_D0_ARBITRARY_TESTED_FRONTIER_WIDTH_COLLAPSES_BY_ONE_ROOT_BIT = PASS")
    print("C025_F3D_D0_ARBITRARY_TESTED_INVERSION_DEPTH_COLLAPSES_BY_ONE_ROOT_BIT = PASS")
    print("C025_F3D_D0_ALL_TESTED_CROSSING_MACROS_CONSTANT_AFTER_Z0 = PASS")
    print("C025_F3D_CLAIM_CEILING = FINITE_MECHANICS_ONLY")
    print("C025_F3D_NEXT = EXACT_SOKOLOV_SELF_REDUCTION_SEMANTIC_SURVIVAL")


if __name__ == "__main__":
    main()
