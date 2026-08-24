#!/usr/bin/env python3
"""Finite implementation-parity probe for C024 / Issue #211.

This file encodes the resolution-sink padding construction used to attack the
universal polynomial residual-count bound for the exact deterministic Policy-0A.

The asymptotic theorem is documented in
C024_ISSUE_211_RESOLUTION_SINK_COUNTERFAMILY.md.  This executable only checks
finite mechanics: source-GT encoding, sink-budget starvation, zero local
additions at the first pivot, core-only branching, and core projection after a
branch.  A finite PASS is not itself the asymptotic proof.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations, permutations
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


def simplify_one(cnf: CNF, variable: int, value: bool) -> CNF | None:
    true_literal = variable if value else -variable
    false_literal = -true_literal
    residual: list[Clause] = []
    for clause in cnf:
        if true_literal in clause:
            continue
        if false_literal in clause:
            reduced = tuple(lit for lit in clause if lit != false_literal)
            if not reduced:
                return None
            residual.append(reduced)
        else:
            residual.append(clause)
    return canonical_cnf(residual)


def unit_propagate(cnf: CNF) -> tuple[CNF | None, bool]:
    while True:
        units = [clause[0] for clause in cnf if len(clause) == 1]
        if not units:
            return cnf, False
        assignments: dict[int, bool] = {}
        for literal in units:
            var = abs(literal)
            value = literal > 0
            if var in assignments and assignments[var] != value:
                return None, True
            assignments[var] = value
        for var, value in sorted(assignments.items()):
            cnf = simplify_one(cnf, var, value)
            if cnf is None:
                return None, True
            if not cnf:
                return cnf, False


def limited_resolution(
    cnf: CNF,
    max_width: int,
    attempt_budget: int,
    addition_budget: int,
) -> tuple[CNF, bool, int, int]:
    clauses = set(cnf)
    positive: dict[int, list[Clause]] = defaultdict(list)
    negative: dict[int, list[Clause]] = defaultdict(list)

    for clause in sorted(clauses, key=lambda item: (len(item), item)):
        for literal in clause:
            (positive if literal > 0 else negative)[abs(literal)].append(clause)

    attempts = 0
    additions = 0
    for pivot in sorted(set(positive) & set(negative)):
        for left in positive[pivot]:
            for right in negative[pivot]:
                attempts += 1
                if attempts > attempt_budget or additions >= addition_budget:
                    return canonical_cnf(clauses), False, attempts - 1, additions
                resolvent = (set(left) - {pivot}) | (set(right) - {-pivot})
                if any(-literal in resolvent for literal in resolvent):
                    continue
                if len(resolvent) > max_width:
                    continue
                normalized = canonical_clause(resolvent)
                if normalized is None:
                    continue
                if not normalized:
                    return canonical_cnf(clauses | {()}), True, attempts, additions + 1
                if normalized not in clauses:
                    clauses.add(normalized)
                    additions += 1
    return canonical_cnf(clauses), False, attempts, additions


def branch_variable(cnf: CNF) -> int:
    frequencies = Counter(abs(lit) for clause in cnf for lit in clause)
    maximum = max(frequencies.values())
    return min(var for var, count in frequencies.items() if count == maximum)


@dataclass(frozen=True)
class PaddedGT:
    n: int
    cnf: CNF
    core_cnf: CNF
    variable_count: int
    core_variables: frozenset[int]
    sink_d: int
    sink_a: int
    p: int
    B: int


def build_padded_gt(n: int) -> PaddedGT:
    if n < 3:
        raise ValueError("use n >= 3")

    B = 256 * n * n
    p = 64 * n * n

    # Resolution sink receives the smallest ids so pivot d is visited first.
    d = 1
    a = 2
    next_var = 3
    u = list(range(next_var, next_var + p))
    next_var += p
    v = list(range(next_var, next_var + p))
    next_var += p

    # Directed source GT_n variables.
    x: dict[tuple[int, int], int] = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            x[(i, j)] = next_var
            next_var += 1
    core_variables = frozenset(x.values())

    core: list[Clause] = []
    for i, j in combinations(range(n), 2):
        ij = x[(i, j)]
        ji = x[(j, i)]
        core.append((ij, ji))       # totality
        core.append((-ij, -ji))     # antisymmetry

    for i, j, k in permutations(range(n), 3):
        core.append((-x[(i, j)], -x[(j, k)], x[(i, k)]))

    for j in range(n):
        core.append(tuple(x[(i, j)] for i in range(n) if i != j))

    core_cnf = canonical_cnf(core)

    padding: list[Clause] = []

    # Uniform branch-frequency boosters.  Each private leaf occurs once.
    for core_var in sorted(core_variables):
        for _ in range(B):
            leaf = next_var
            next_var += 1
            padding.append((core_var, leaf))

    # Resolution sink: every d-resolvent contains both a and -a.
    for leaf in u:
        padding.append((d, a, leaf))
    for leaf in v:
        padding.append((-d, -a, leaf))

    return PaddedGT(
        n=n,
        cnf=canonical_cnf((*core_cnf, *padding)),
        core_cnf=core_cnf,
        variable_count=next_var - 1,
        core_variables=core_variables,
        sink_d=d,
        sink_a=a,
        p=p,
        B=B,
    )


def core_projection(cnf: CNF, core_variables: frozenset[int]) -> CNF:
    return canonical_cnf(
        clause
        for clause in cnf
        if clause and all(abs(lit) in core_variables for lit in clause)
    )


def finite_probe(n: int = 3) -> None:
    family = build_padded_gt(n)
    propagated, contradiction = unit_propagate(family.cnf)
    assert not contradiction
    assert propagated is not None

    core_root, core_contradiction = unit_propagate(family.core_cnf)
    assert not core_contradiction
    assert core_root is not None
    assert core_projection(propagated, family.core_variables) == core_root

    literal_count = sum(len(clause) for clause in propagated)
    attempt_budget = max(64, 4 * literal_count)
    addition_budget = max(8, len(propagated) // 4)
    assert family.p * family.p > attempt_budget

    saturated, refuted, attempts, additions = limited_resolution(
        propagated,
        max_width=max(map(len, propagated)) + 1,
        attempt_budget=attempt_budget,
        addition_budget=addition_budget,
    )
    assert not refuted
    assert additions == 0
    assert attempts == attempt_budget
    assert saturated == propagated

    frequencies = Counter(abs(lit) for clause in saturated for lit in clause)
    selected = branch_variable(saturated)
    assert selected in family.core_variables
    assert min(frequencies[var] for var in family.core_variables) >= family.B
    assert frequencies[family.sink_d] == 2 * family.p
    assert frequencies[family.sink_a] == 2 * family.p
    assert family.B > 2 * family.p

    # Check one recursive projection step under both truth values of the selected
    # core variable.  Booster units may fire, but they must not change the core.
    for value in (False, True):
        full_child = simplify_one(saturated, selected, value)
        core_child = simplify_one(core_root, selected, value)
        if core_child is None:
            assert full_child is None or unit_propagate(full_child)[1]
            continue
        assert full_child is not None
        full_post, full_bad = unit_propagate(full_child)
        core_post, core_bad = unit_propagate(core_child)
        assert full_bad == core_bad
        if not full_bad:
            assert full_post is not None and core_post is not None
            assert core_projection(full_post, family.core_variables) == core_post

    # Closed-form root bounds used by the asymptotic proof.
    V = n * (n - 1)
    L_gt_upper = 3 * n**3
    L_boost_upper = 2 * V * family.B
    L_sink = 6 * family.p
    L0_upper = L_gt_upper + L_boost_upper + L_sink
    assert family.p**2 > 4 * L0_upper

    print("TOPA_POLICY0A_PADDED_GT_FINITE_PROBE = PASS")
    print(f"n = {n}")
    print(f"variables = {family.variable_count}")
    print(f"clauses = {len(family.cnf)}")
    print(f"literal_count = {literal_count}")
    print(f"attempt_budget = {attempt_budget}")
    print(f"sink_pair_attempts_available = {family.p**2}")
    print(f"resolution_attempts_charged = {attempts}")
    print(f"resolution_additions = {additions}")
    print(f"selected_branch_variable = {selected}")
    print("claim_boundary = finite mechanics only; asymptotic lower bound comes from the separate proof + GT_n theorem")


if __name__ == "__main__":
    finite_probe()
