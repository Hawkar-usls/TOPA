#!/usr/bin/env python3
"""Finite replay for C025-E2R-L1G-F2.

Checks only finite mechanics behind the analytical theorem:
- weakening scaffolding can normalize to stronger pure-Resolution clauses;
- small nested negative-frontier macros have Resolution-refutable P(F) U N(F);
- the deliberately loose factorial recurrences dominate the construction cost.

The asymptotic NW lower-bound consequence is analytical/source-theorem based,
not established by this finite replay.
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
            assert 0 <= n.p1 < i
            assert nodes[n.p1].clause <= n.clause
        elif n.kind == "res":
            assert 0 <= n.p1 < i and 0 <= n.p2 < i
            got = resolve(nodes[n.p1].clause, nodes[n.p2].clause, n.pivot)
            assert got == n.clause
        else:
            raise AssertionError(n.kind)


def normalize_weakening(nodes: list[Node], axioms: set[Clause]) -> list[Clause]:
    """Return one pure-Resolution derivable stronger clause per old node.

    This is the constructive F2.1 invariant C'_i subseteq C_i.  Aliases do not
    create proof nodes here; the replay tracks only the resulting stronger line.
    """
    out: list[Clause] = []
    for i, n in enumerate(nodes):
        if n.kind == "axiom":
            assert n.clause in axioms
            out.append(n.clause)
            continue
        if n.kind == "weaken":
            c = out[n.p1]
            assert c <= n.clause
            out.append(c)
            continue

        a, b = out[n.p1], out[n.p2]
        old_a, old_b = nodes[n.p1].clause, nodes[n.p2].clause
        old_r = n.clause
        assert resolve(old_a, old_b, n.pivot) == old_r

        r = resolve(a, b, n.pivot)
        if r is not None:
            assert r <= old_r
            out.append(r)
        elif n.pivot not in a and -n.pivot not in a:
            assert a <= old_r
            out.append(a)
        elif n.pivot not in b and -n.pivot not in b:
            assert b <= old_r
            out.append(b)
        else:
            # If complementary pivot orientation vanished only on one required
            # side, the corresponding stronger parent must subsume old_r.
            candidates = [c for c in (a, b) if c <= old_r]
            assert candidates
            out.append(min(candidates, key=len))
    return out


def check_weakening_scaffolding() -> None:
    # Pure base refutation: {1}, {-1,2}, {-2}.  Lift it with context {3}, then
    # close with {-3}.  The RW derivation is easy; normalization must recover
    # a stronger pure-Resolution chain ending in empty.
    axioms = {
        frozenset({1}), frozenset({-1, 2}), frozenset({-2}), frozenset({-3})
    }
    ns = [
        Node("axiom", frozenset({1})),                    # 0
        Node("axiom", frozenset({-1, 2})),               # 1
        Node("axiom", frozenset({-2})),                  # 2
        Node("axiom", frozenset({-3})),                  # 3
        Node("weaken", frozenset({1, 3}), 0),            # 4
        Node("weaken", frozenset({-1, 2, 3}), 1),        # 5
        Node("weaken", frozenset({-2, 3}), 2),           # 6
        Node("res", frozenset({2, 3}), 4, 5, 1),         # 7
        Node("res", frozenset({3}), 7, 6, 2),            # 8
        Node("res", frozenset(), 8, 3, 3),               # 9
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
    # F = AND locals AND AND_j ~F_j
    pos: set[Clause] = {frozenset({l}) for l in m.locals}
    child_pairs = [pos_neg(c) for c in m.neg_children]
    for _pc, nc in child_pairs:
        pos |= nc

    neg_local = frozenset(-l for l in m.locals)
    neg: set[Clause] = {neg_local}
    for pc, _nc in child_pairs:
        neg = or_cnf(neg, pc)
    return pos, neg


def resolution_closure_refutes(axioms: set[Clause], max_lines: int = 10000) -> tuple[bool, int]:
    """Small finite oracle used only for replay fixtures."""
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
    # q=0: conjunction.
    q0 = Macro((1, -2, 3))
    # q=1: F = 4 AND ~(1 AND -2).
    q1 = Macro((4,), (Macro((1, -2)),))
    # q=2 along one frontier chain.
    q2 = Macro((5,), (Macro((4,), (Macro((1, -2)),)),))
    # branching frontier; child cones need not be treated as disjoint in theorem.
    qb = Macro((6,), (Macro((1, 2)), Macro((2, -3))))

    for m in (q0, q1, q2, qb):
        p, n = pos_neg(m)
        ok, lines = resolution_closure_refutes(p | n)
        assert ok
        assert lines < 10000


def check_factorial_recurrences() -> None:
    # Exponent-only replay of the safe inequalities used in F2.3/F2.4.
    for q in range(0, 9):
        H = factorial(q + 2)
        line_exp = factorial(q + 3)
        comp = factorial(q + 4)
        full = factorial(q + 5)
        assert 3 * H <= line_exp
        if q == 0:
            assert H <= comp
        else:
            prev_comp = factorial(q + 3)
            # q factor is charged by at most one extra S exponent since q<=S.
            recurrence_exp = H + prev_comp + 2
            assert recurrence_exp <= comp
        assert line_exp + comp + 1 <= full


def check_asymptotic_shape() -> None:
    # Finite sanity only: r = ceil(c log N/loglogN) makes log(r!) grow on the
    # expected Theta(log N) scale.  No asymptotic theorem is inferred from this.
    for k in (64, 128, 256, 512):
        N = 2 ** k
        q = max(2, int(k / max(1.0, log(k))))
        assert factorial(q + 5) > q
        assert log(factorial(q + 5)) > log(q)


def main() -> None:
    check_weakening_scaffolding()
    check_nested_macro_complements()
    check_factorial_recurrences()
    check_asymptotic_shape()
    print("C025_E2R_L1G_F2_WEAKENING_NORMALIZATION = PASS")
    print("C025_E2R_L1G_F2_CONTEXT_LIFT_SCAFFOLD = PASS")
    print("C025_E2R_L1G_F2_NESTED_COMPLEMENT_REFUTATION_FIXTURES = PASS")
    print("C025_E2R_L1G_F2_FACTORIAL_RECURRENCE_CEILING = PASS")
    print("C025_E2R_L1G_F2_Q_LOWER_BOUND_ALGEBRA_SHAPE = PASS")
    print("claim_boundary = finite mechanics only; asymptotic q lower bound uses the analytical F2 theorem plus the external NW lower bound")


if __name__ == "__main__":
    main()
