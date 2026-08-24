#!/usr/bin/env python3
"""Theorem-matched directed GT_n generator used by the Issue #211 line.

Source lineage:
- Beame, Impagliazzo, Pitassi, Segerlind, Formula Caching in DPLL,
  Definition 4.24 / Theorem 4.28.
- JANUS implementation source first frozen in Hawkar-usls/Janus-Fundamentum,
  branch pure-math-polynomial-residual-cache-bridge,
  experiments/direct/janus_tear_policy0a_source_gt.py.

This is an encoding/provenance artifact.  It does not by itself transfer any
lower bound through Policy-0A's extra local Resolution layer.
"""

from __future__ import annotations

from itertools import combinations, permutations, product
from typing import Iterable

Clause = tuple[int, ...]
CNF = tuple[Clause, ...]


def canonical_clause(clause: Iterable[int]) -> Clause | None:
    literals = set(clause)
    if any(-literal in literals for literal in literals):
        return None
    return tuple(sorted(literals, key=lambda literal: (abs(literal), literal < 0)))


def canonical_cnf(clauses: Iterable[Iterable[int]]) -> CNF:
    normalized: set[Clause] = set()
    for clause in clauses:
        candidate = canonical_clause(clause)
        if candidate is not None:
            normalized.add(candidate)
    return tuple(sorted(normalized, key=lambda clause: (len(clause), clause)))


def source_graph_tautology_cnf(n: int) -> tuple[CNF, int]:
    if n < 2:
        raise ValueError("GT_n requires n >= 2")

    variable: dict[tuple[int, int], int] = {}
    next_variable = 1
    for left in range(n):
        for right in range(n):
            if left == right:
                continue
            variable[(left, right)] = next_variable
            next_variable += 1

    clauses: list[Clause] = []

    # GT_n = GOP(K_n) plus totality.
    for left, right in combinations(range(n), 2):
        lr = variable[(left, right)]
        rl = variable[(right, left)]
        clauses.append((lr, rl))       # totality
        clauses.append((-lr, -rl))     # antisymmetry

    for first, second, third in permutations(range(n), 3):
        clauses.append(
            (
                -variable[(first, second)],
                -variable[(second, third)],
                variable[(first, third)],
            )
        )

    for vertex in range(n):
        clauses.append(
            tuple(variable[(other, vertex)] for other in range(n) if other != vertex)
        )

    return canonical_cnf(clauses), next_variable - 1


def satisfies(cnf: CNF, assignment: tuple[bool, ...]) -> bool:
    return all(
        any(
            (literal > 0 and assignment[literal - 1])
            or (literal < 0 and not assignment[-literal - 1])
            for literal in clause
        )
        for clause in cnf
    )


def brute_satisfiable(cnf: CNF, variable_count: int) -> bool:
    return any(
        satisfies(cnf, assignment)
        for assignment in product((False, True), repeat=variable_count)
    )


def self_test() -> None:
    for n in range(2, 5):
        cnf, variable_count = source_graph_tautology_cnf(n)
        assert variable_count == n * (n - 1)
        assert len(cnf) == n * ((n - 1) ** 2 + 1)
        assert not brute_satisfiable(cnf, variable_count)
        print(f"SOURCE_GT_{n}=UNSAT variables={variable_count} clauses={len(cnf)}")
    print("TOPA_SOURCE_GT_ENCODING_SELF_TEST=PASS")
    print("claim_boundary=finite encoding check only")


if __name__ == "__main__":
    self_test()
