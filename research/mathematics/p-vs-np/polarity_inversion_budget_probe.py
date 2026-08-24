#!/usr/bin/env python3
"""Finite replay for the C025-E2R-L1G-F1 negative-edge budget.

The replay checks exact syntactic CNF expansion on small signed AND DAGs and
verifies the deliberately loose S^((q+2)!) representation bound.  It does not
claim a proof-level Resolution cut-elimination bound.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from math import factorial

Clause = frozenset[int]


@dataclass(frozen=True)
class Gate:
    var: int
    left: int
    right: int


def or_cnf(a: set[Clause], b: set[Clause]) -> set[Clause]:
    out: set[Clause] = set()
    for x in a:
        for y in b:
            c = frozenset(x | y)
            if not any(-z in c for z in c):
                out.add(c)
    return out


def exact_expansions(local_atoms: set[int], gates: list[Gate]):
    pos = {v: {frozenset({v})} for v in local_atoms}
    neg = {v: {frozenset({-v})} for v in local_atoms}
    neg_edges: dict[int, frozenset[tuple[int,int]]] = {v: frozenset() for v in local_atoms}
    known = set(local_atoms)

    for g in gates:
        if g.var in known:
            raise ValueError("nonfresh gate")
        for lit in (g.left, g.right):
            if abs(lit) not in known:
                raise ValueError("unknown/forward operand")

        def E(lit: int):
            return pos[abs(lit)] if lit > 0 else neg[abs(lit)]

        def EN(lit: int):
            return neg[abs(lit)] if lit > 0 else pos[abs(lit)]

        pos[g.var] = set(E(g.left)) | set(E(g.right))
        neg[g.var] = or_cnf(set(EN(g.left)), set(EN(g.right)))

        edges: set[tuple[int,int]] = set()
        for lit in (g.left, g.right):
            u = abs(lit)
            if u not in local_atoms:
                edges.update(neg_edges[u])
                if lit < 0:
                    edges.add((g.var, u))
        neg_edges[g.var] = frozenset(edges)
        known.add(g.var)

    return pos, neg, neg_edges


def factorial_bound(S: int, q: int) -> int:
    return S ** factorial(q + 2)


def check_all_sign_patterns() -> None:
    # Three-gate topology: 5=(1 ? 2), 6=(5 ? 3), 7=(6 ? 4).
    # Local sign choices are free; crossing-edge signs determine q.
    locals_ = {1,2,3,4}
    for s12, s23 in product((-1,1), repeat=2):
        gates = [
            Gate(5, 1, -2),
            Gate(6, s12*5, 3),
            Gate(7, s23*6, -4),
        ]
        pos, neg, qedges = exact_expansions(locals_, gates)
        S = len(locals_) + len(gates) + 2*len(gates)
        for v in (5,6,7):
            q = len(qedges[v])
            assert len(pos[v]) <= factorial_bound(S,q)
            assert len(neg[v]) <= factorial_bound(S,q)


def check_q0_monotone_case() -> None:
    locals_={1,2,3,4,5}
    gates=[Gate(6,1,-2), Gate(7,6,3), Gate(8,7,-4), Gate(9,8,5)]
    pos,neg,qe=exact_expansions(locals_,gates)
    assert len(qe[9]) == 0
    assert len(pos[9]) == 5
    assert len(neg[9]) == 1


def parity_b2(n: int):
    gates=[]; y=1; nxt=n+1
    for x in range(2,n+1):
        t1,t2,yp=nxt,nxt+1,nxt+2; nxt+=3
        gates += [Gate(t1,y,x), Gate(t2,-y,-x), Gate(yp,-t1,-t2)]
        y=yp
    return gates,y


def check_parity_q_growth() -> None:
    for n in range(2,8):
        gates,out=parity_b2(n)
        pos,neg,qe=exact_expansions(set(range(1,n+1)),gates)
        q=len(qe[out])
        assert q == 3*n-4
        # Exact distributed positive parity CNF.
        assert len(pos[out]) == 2**(n-1)
        S=n+3*len(gates)
        assert len(pos[out]) <= factorial_bound(S,q)
        assert len(neg[out]) <= factorial_bound(S,q)


def main() -> None:
    check_all_sign_patterns()
    check_q0_monotone_case()
    check_parity_q_growth()
    print("C025_E2R_L1G_F1_NEGATIVE_EDGE_ACCOUNTING = PASS")
    print("C025_E2R_L1G_F1_Q0_MONOTONE_EXPANSION = PASS")
    print("C025_E2R_L1G_F1_FACTORIAL_EXPANSION_BOUND_FINITE = PASS")
    print("C025_E2R_L1G_F1_PARITY_NEGATIVE_EDGE_GROWTH = PASS")
    print("claim_boundary = formula-representation mechanics only; proof-level macro-cut elimination remains open")


if __name__ == "__main__":
    main()
