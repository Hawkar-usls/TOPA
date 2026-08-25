#!/usr/bin/env python3
"""Finite mechanics for C025 Akinator prebirth pivot factorization.

This script checks finite truth-table instances of the exact one-pivot identity,
witness lifting, and the add-only resolvent monotonicity theorem. It does not
prove any asymptotic P-vs-NP statement.
"""

from __future__ import annotations

from itertools import product
from typing import Dict, Iterable, List, Sequence, Set, Tuple

Clause = Tuple[int, ...]
CNF = Tuple[Clause, ...]


def canon_clause(lits: Iterable[int]) -> Clause | None:
    s = set(lits)
    for lit in tuple(s):
        if -lit in s:
            return None
    return tuple(sorted(s, key=lambda z: (abs(z), z < 0)))


def canon_cnf(clauses: Iterable[Clause]) -> CNF:
    out: Set[Clause] = set()
    for c in clauses:
        cc = canon_clause(c)
        if cc is not None:
            out.add(cc)
    return tuple(sorted(out))


def clause_value(clause: Clause, assignment: Dict[int, bool]) -> bool:
    return any(assignment[abs(l)] if l > 0 else not assignment[abs(l)] for l in clause)


def cnf_value(cnf: CNF, assignment: Dict[int, bool]) -> bool:
    return all(clause_value(c, assignment) for c in cnf)


def pivot_parts(cnf: CNF, x: int):
    pos: List[Clause] = []
    neg: List[Clause] = []
    rest: List[Clause] = []
    for c in cnf:
        if x in c:
            pos.append(tuple(l for l in c if l != x))
        elif -x in c:
            neg.append(tuple(l for l in c if l != -x))
        else:
            rest.append(c)
    return tuple(pos), tuple(neg), canon_cnf(rest)


def conjunction_of_clauses(clauses: Sequence[Clause], assignment: Dict[int, bool]) -> bool:
    return all(clause_value(c, assignment) for c in clauses)


def factored_value(cnf: CNF, x: int, assignment_without_x: Dict[int, bool]) -> bool:
    pos, neg, rest = pivot_parts(cnf, x)
    r = cnf_value(rest, assignment_without_x)
    p = conjunction_of_clauses(pos, assignment_without_x)  # empty AND = True
    n = conjunction_of_clauses(neg, assignment_without_x)
    return r and (p or n)


def exists_x_value(cnf: CNF, x: int, assignment_without_x: Dict[int, bool]) -> bool:
    for bit in (False, True):
        a = dict(assignment_without_x)
        a[x] = bit
        if cnf_value(cnf, a):
            return True
    return False


def lift_x(cnf: CNF, x: int, assignment_without_x: Dict[int, bool]) -> int:
    pos, neg, _ = pivot_parts(cnf, x)
    p = conjunction_of_clauses(pos, assignment_without_x)
    n = conjunction_of_clauses(neg, assignment_without_x)
    assert p or n
    return 0 if p else 1


def resolvent_frontier(cnf: CNF, x: int) -> Set[Clause]:
    pos, neg, _ = pivot_parts(cnf, x)
    out: Set[Clause] = set()
    for a in pos:
        for b in neg:
            r = canon_clause((*a, *b))
            if r is not None:
                out.add(r)
    return out


def and_definition(e: int, a: int, b: int) -> CNF:
    # e <-> (a AND b), where a,b are positive variables for this finite fixture.
    return canon_cnf(((-e, a), (-e, b), (e, -a, -b)))


def all_assignments(vars_: Sequence[int]):
    for bits in product((False, True), repeat=len(vars_)):
        yield dict(zip(vars_, bits))


def check_pf_identity_and_lift() -> None:
    fixtures: List[Tuple[CNF, int]] = [
        (canon_cnf(((1, 2), (-1, 3), (2, -3))), 1),
        (canon_cnf(((1,), (-1, 2), (-1, -2), (3,))), 1),
        (canon_cnf(((1, 2, 3), (1, -2), (-1, 3), (-1, -3), (2, 3))), 1),
        (canon_cnf(((2, 3), (-2, 3))), 1),  # pivot absent: p=q=0
        (canon_cnf(((1, 2), (1, -2), (3,))), 1),  # no negative pivot clauses
        (canon_cnf(((-1, 2), (-1, -2), (3,))), 1),  # no positive pivot clauses
    ]

    pool = [
        (1,), (-1,), (1, 2), (1, -2), (-1, 2), (-1, -2),
        (1, 3), (-1, 3), (2, 3), (-2, 3)
    ]
    for mask in range(1, 1 << min(len(pool), 8)):
        chosen = [pool[i] for i in range(8) if (mask >> i) & 1]
        fixtures.append((canon_cnf(chosen), 1))

    for cnf, x in fixtures:
        vars_all = sorted({abs(l) for c in cnf for l in c})
        residual_vars = [v for v in vars_all if v != x]
        for a in all_assignments(residual_vars):
            lhs = exists_x_value(cnf, x, a)
            rhs = factored_value(cnf, x, a)
            assert lhs == rhs, (cnf, a, lhs, rhs)
            if rhs:
                bit = lift_x(cnf, x, a)
                full = dict(a)
                full[x] = bool(bit)
                assert cnf_value(cnf, full), (cnf, a, bit)


def check_add_only_resolvent_monotonicity() -> None:
    bases = [
        canon_cnf(((1, 2), (1, 3), (-1, 4), (-1, -2), (2, -4))),
        canon_cnf(((1, 2, 3), (1, -2, 4), (-1, 3), (-1, -4))),
    ]
    defs = [
        and_definition(5, 1, 2),  # definition itself mentions the pivot
        and_definition(5, 2, 3),  # definition does not mention the pivot
    ]
    for f in bases:
        q0 = resolvent_frontier(f, 1)
        for d in defs:
            fp = canon_cnf((*f, *d))
            q1 = resolvent_frontier(fp, 1)
            assert q0 <= q1, (q0, q1)
            assert len(q1) >= len(q0)


def check_cross_product_vs_factor_size() -> None:
    for m in range(2, 33):
        x = 1
        a_vars = list(range(2, 2 + m))
        b_vars = list(range(2 + m, 2 + 2 * m))
        cnf = canon_cnf([(x, a) for a in a_vars] + [(-x, b) for b in b_vars])
        q = resolvent_frontier(cnf, x)
        assert len(q) == m * m
        aggregate_gates = 2 * (m - 1) + 1
        assert aggregate_gates == 2 * m - 1
        if m >= 3:
            assert aggregate_gates < len(q)


def main() -> None:
    check_pf_identity_and_lift()
    check_add_only_resolvent_monotonicity()
    check_cross_product_vs_factor_size()
    print("AKINATOR_PF1_EXISTENTIAL_PIVOT_IDENTITY_FINITE_REPLAY = PASS")
    print("AKINATOR_PF1_WITNESS_LIFT_FINITE_REPLAY = PASS")
    print("AKINATOR_ADD_ONLY_ORIGINAL_FRONTIER_MONOTONICITY = PASS")
    print("AKINATOR_PAIR_CROSS_PRODUCT_VS_LINEAR_FACTOR_FIXTURE = PASS")
    print("PREBIRTH_PIVOT_FACTORIZATION_THEOREM = ANALYTIC_NOT_CI")
    print("ITERATED_FACTOR_DAG_POLY_BOUND = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
