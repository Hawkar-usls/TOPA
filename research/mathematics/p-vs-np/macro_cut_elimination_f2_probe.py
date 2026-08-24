#!/usr/bin/env python3
"""Finite replay for C025-E2R-L1G-F2 v1.1.

Checks finite mechanics only:
- pure Resolution context lifting on an overlap fixture;
- historical weakening-normalization route as a regression check, not as the
  authoritative theorem path;
- small nested negative-frontier macro complement refutations;
- factorial recurrence ceilings.

The asymptotic q lower bound is analytical/source-theorem based.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from math import factorial, log

Clause = frozenset[int]


def taut(c: Clause) -> bool:
    return any(-x in c for x in c)


def resolve(a: Clause, b: Clause, pivot: int) -> Clause | None:
    if pivot in a and -pivot in b:
        out = frozenset((a - {pivot}) | (b - {-pivot}))
    elif -pivot in a and pivot in b:
        out = frozenset((a - {-pivot}) | (b - {pivot}))
    else:
        return None
    return None if taut(out) else out


def restrict_clause(c: Clause, rho: dict[int, bool]) -> Clause | None:
    out = set()
    for lit in c:
        v = abs(lit)
        if v not in rho:
            out.add(lit)
            continue
        lit_true = rho[v] if lit > 0 else not rho[v]
        if lit_true:
            return None
        # falsified assigned literal is deleted
    return frozenset(out)


def check_pure_context_lifting_overlap() -> None:
    # Base complement-style refutation:
    # {1}, {-1,2}, {-2} |- empty.
    # Context C={2,3} overlaps proof variable 2.  Available contextual Gamma
    # premise is {1,2,3}; Delta remains exact.  Pure Resolution derives {3},
    # a strict subclause of C, with no weakening.
    g = frozenset({1, 2, 3})
    d1 = frozenset({-1, 2})
    d2 = frozenset({-2})
    r1 = resolve(d1, d2, 2)
    assert r1 == frozenset({-1})
    r2 = resolve(g, r1, 1)
    assert r2 == frozenset({2, 3})
    r3 = resolve(r2, d2, 2)
    assert r3 == frozenset({3})
    assert r3 <= frozenset({2, 3})

    # Restrict by the assignment falsifying C: 2=False, 3=False.
    rho = {2: False, 3: False}
    assert restrict_clause(g, rho) == frozenset({1})
    assert restrict_clause(d1, rho) == frozenset({-1})
    assert restrict_clause(d2, rho) is None  # satisfied and deleted
    assert resolve(frozenset({1}), frozenset({-1}), 1) == frozenset()


@dataclass(frozen=True)
class Node:
    kind: str  # axiom | weaken | res
    clause: Clause
    p1: int = -1
    p2: int = -1
    pivot: int = 0


def verify_rw(nodes: list[Node], axioms: set[Clause]) -> None:
    for i, n in enumerate(nodes):
        if n.kind == "axiom":
            assert n.clause in axioms
        elif n.kind == "weaken":
            assert 0 <= n.p1 < i and nodes[n.p1].clause <= n.clause
        elif n.kind == "res":
            assert 0 <= n.p1 < i and 0 <= n.p2 < i
            assert resolve(nodes[n.p1].clause, nodes[n.p2].clause, n.pivot) == n.clause
        else:
            raise AssertionError(n.kind)


def normalize_weakening(nodes: list[Node], axioms: set[Clause]) -> list[Clause]:
    out: list[Clause] = []
    for i, n in enumerate(nodes):
        if n.kind == "axiom":
            assert n.clause in axioms
            out.append(n.clause)
        elif n.kind == "weaken":
            c = out[n.p1]
            assert c <= n.clause
            out.append(c)
        else:
            a, b = out[n.p1], out[n.p2]
            r = resolve(a, b, n.pivot)
            if r is not None:
                assert r <= n.clause
                out.append(r)
            elif n.pivot not in a and -n.pivot not in a:
                assert a <= n.clause
                out.append(a)
            elif n.pivot not in b and -n.pivot not in b:
                assert b <= n.clause
                out.append(b)
            else:
                candidates = [c for c in (a, b) if c <= n.clause]
                assert candidates
                out.append(min(candidates, key=len))
    return out


def check_historical_weakening_regression() -> None:
    axioms = {frozenset({1}), frozenset({-1, 2}), frozenset({-2}), frozenset({-3})}
    ns = [
        Node("axiom", frozenset({1})),
        Node("axiom", frozenset({-1, 2})),
        Node("axiom", frozenset({-2})),
        Node("axiom", frozenset({-3})),
        Node("weaken", frozenset({1, 3}), 0),
        Node("weaken", frozenset({-1, 2, 3}), 1),
        Node("weaken", frozenset({-2, 3}), 2),
        Node("res", frozenset({2, 3}), 4, 5, 1),
        Node("res", frozenset({3}), 7, 6, 2),
        Node("res", frozenset(), 8, 3, 3),
    ]
    verify_rw(ns, axioms)
    pure = normalize_weakening(ns, axioms)
    assert all(pure[i] <= ns[i].clause for i in range(len(ns)))
    assert pure[-1] == frozenset()


@dataclass(frozen=True)
class Macro:
    locals: tuple[int, ...]
    neg_children: tuple["Macro", ...] = ()


def or_cnf(a: set[Clause], b: set[Clause]) -> set[Clause]:
    out: set[Clause] = set()
    for x in a:
        for y in b:
            c = frozenset(x | y)
            if not taut(c):
                out.add(c)
    return out


def pos_neg(m: Macro) -> tuple[set[Clause], set[Clause]]:
    pos: set[Clause] = {frozenset({l}) for l in m.locals}
    child_pairs = [pos_neg(c) for c in m.neg_children]
    for _pc, nc in child_pairs:
        pos |= nc
    neg: set[Clause] = {frozenset(-l for l in m.locals)}
    for pc, _nc in child_pairs:
        neg = or_cnf(neg, pc)
    return pos, neg


def resolution_closure_refutes(axioms: set[Clause], max_lines: int = 10000) -> tuple[bool, int]:
    clauses = set(c for c in axioms if not taut(c))
    if frozenset() in clauses:
        return True, len(clauses)
    changed = True
    while changed and len(clauses) <= max_lines:
        changed = False
        current = list(clauses)
        for a, b in combinations(current, 2):
            vars_ = {abs(x) for x in a} & {abs(x) for x in b}
            for v in vars_:
                r = resolve(a, b, v)
                if r is None or r in clauses:
                    continue
                clauses.add(r)
                changed = True
                if not r:
                    return True, len(clauses)
                if len(clauses) > max_lines:
                    return False, len(clauses)
    return False, len(clauses)


def check_nested_macro_complements() -> None:
    fixtures = [
        Macro((1, -2, 3)),
        Macro((4,), (Macro((1, -2)),)),
        Macro((5,), (Macro((4,), (Macro((1, -2)),)),)),
        Macro((6,), (Macro((1, 2)), Macro((2, -3)))),
    ]
    for m in fixtures:
        p, n = pos_neg(m)
        ok, lines = resolution_closure_refutes(p | n)
        assert ok and lines < 10000


def check_factorial_recurrences() -> None:
    for q in range(0, 9):
        H = factorial(q + 2)
        line_exp = factorial(q + 3)
        comp = factorial(q + 4)
        full = factorial(q + 5)
        assert 3 * H <= line_exp
        if q:
            assert H + factorial(q + 3) + 2 <= comp
        assert line_exp + comp + 1 <= full


def check_asymptotic_shape() -> None:
    for k in (64, 128, 256, 512):
        q = max(2, int(k / max(1.0, log(k))))
        assert log(factorial(q + 5)) > log(q)


def main() -> None:
    check_pure_context_lifting_overlap()
    check_historical_weakening_regression()
    check_nested_macro_complements()
    check_factorial_recurrences()
    check_asymptotic_shape()
    print("C025_E2R_L1G_F2_PURE_RESTRICTION_LIFT_OVERLAP = PASS")
    print("C025_E2R_L1G_F2_HISTORICAL_WEAKENING_NORMALIZATION = PASS")
    print("C025_E2R_L1G_F2_NESTED_COMPLEMENT_REFUTATION_FIXTURES = PASS")
    print("C025_E2R_L1G_F2_FACTORIAL_RECURRENCE_CEILING = PASS")
    print("C025_E2R_L1G_F2_Q_LOWER_BOUND_ALGEBRA_SHAPE = PASS")
    print("claim_boundary = finite mechanics only; asymptotic q lower bound uses pure analytical F2 plus the external NW lower bound")

if __name__ == "__main__":
    main()
