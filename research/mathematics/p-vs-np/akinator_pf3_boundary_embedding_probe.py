#!/usr/bin/env python3
"""Finite replay for PF3 arbitrary-CNF boundary embedding.

Checks on small CNFs H(Y) that adding a fresh unit pivot x and existentially
projecting x returns exactly H(Y). This validates finite mechanics only; external
OBDD/DNNF/ZDD lower bounds and all asymptotic claims are not established by CI.
"""

from __future__ import annotations

from itertools import product
from typing import Dict, Iterable, Tuple

Clause = Tuple[int, ...]
CNF = Tuple[Clause, ...]


def canon_clause(lits: Iterable[int]) -> Clause | None:
    s = set(lits)
    if any(-lit in s for lit in s):
        return None
    return tuple(sorted(s, key=lambda z: (abs(z), z < 0)))


def canon_cnf(clauses: Iterable[Iterable[int]]) -> CNF:
    out = set()
    for clause in clauses:
        c = canon_clause(clause)
        if c is not None:
            out.add(c)
    return tuple(sorted(out))


def clause_value(clause: Clause, assignment: Dict[int, bool]) -> bool:
    return any(assignment[abs(lit)] if lit > 0 else not assignment[abs(lit)] for lit in clause)


def cnf_value(cnf: CNF, assignment: Dict[int, bool]) -> bool:
    return all(clause_value(clause, assignment) for clause in cnf)


def assignments(vars_: Tuple[int, ...]):
    for bits in product((False, True), repeat=len(vars_)):
        yield dict(zip(vars_, bits))


def exists_pivot_value(cnf: CNF, pivot: int, residual_assignment: Dict[int, bool]) -> bool:
    for bit in (False, True):
        a = dict(residual_assignment)
        a[pivot] = bit
        if cnf_value(cnf, a):
            return True
    return False


def check_arbitrary_cnf_boundary_embedding() -> None:
    pool = (
        (1,), (-1,), (2,), (-2,), (3,), (-3,),
        (1, 2), (-1, 2), (1, -2), (-1, -2),
        (2, 3), (-2, 3), (2, -3), (-2, -3),
    )

    # Freeze a deterministic sample of small explicit CNFs, including empty H.
    masks = list(range(0, 1 << 8))
    masks += [0b100000001, 0b1010101010, 0b111100001111, 0b10110100101101]

    pivot = 4
    for mask in masks:
        chosen = [pool[i] for i in range(len(pool)) if (mask >> i) & 1]
        h = canon_cnf(chosen)
        residual_vars = tuple(sorted({abs(lit) for clause in h for lit in clause}))

        f_pos = canon_cnf((*h, (pivot,)))
        f_neg = canon_cnf((*h, (-pivot,)))

        for a in assignments(residual_vars):
            target = cnf_value(h, a)
            assert exists_pivot_value(f_pos, pivot, a) == target
            assert exists_pivot_value(f_neg, pivot, a) == target


def main() -> None:
    check_arbitrary_cnf_boundary_embedding()
    print("AKINATOR_PF3_DUMMY_POSITIVE_PIVOT_BOUNDARY_EMBEDDING = PASS")
    print("AKINATOR_PF3_DUMMY_NEGATIVE_PIVOT_BOUNDARY_EMBEDDING = PASS")
    print("ONE_STEP_PROJECTED_BOUNDARY_CONTAINS_ALL_CNF_FUNCTIONS = ANALYTIC_THEOREM_FINITE_REPLAY_ONLY")
    print("OBDD_DNNF_ZDD_LOWER_BOUNDS = EXTERNAL_THEOREMS_NOT_CI")
    print("UNIVERSAL_POLY_BOUNDARY_QUOTIENT_WITH_UPDATE = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
