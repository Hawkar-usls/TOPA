#!/usr/bin/env python3
"""Finite replay for C025-E2R-L1G-F3.

Checks the depth/frontier metrics, depth-one exponential counterfamily,
paired structural bound, and exponent recurrences used by the analytical
proof-level (b,d) cut-elimination theorem.  No asymptotic theorem is inferred
from the finite replay alone.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from math import log

Clause = frozenset[int]

@dataclass(frozen=True)
class Gate:
    var: int
    left: int
    right: int


def taut(c: Clause) -> bool:
    return any(-x in c for x in c)


def or_cnf(a: set[Clause], b: set[Clause]) -> set[Clause]:
    out: set[Clause] = set()
    for x in a:
        for y in b:
            c = frozenset(x | y)
            if not taut(c):
                out.add(c)
    return out


def analyze(local_atoms: set[int], gates: list[Gate]):
    known = set(local_atoms)
    gm: dict[int, Gate] = {}
    pos = {v: {frozenset({v})} for v in local_atoms}
    neg = {v: {frozenset({-v})} for v in local_atoms}
    depth = {v: 0 for v in local_atoms}
    for g in gates:
        assert g.var not in known
        assert abs(g.left) in known and abs(g.right) in known
        gm[g.var] = g
        def E(lit: int): return pos[abs(lit)] if lit > 0 else neg[abs(lit)]
        def EN(lit: int): return neg[abs(lit)] if lit > 0 else pos[abs(lit)]
        pos[g.var] = set(E(g.left)) | set(E(g.right))
        neg[g.var] = or_cnf(set(EN(g.left)), set(EN(g.right)))
        ds = []
        for lit in (g.left, g.right):
            v = abs(lit)
            ds.append(0 if v in local_atoms else depth[v] + (1 if lit < 0 else 0))
        depth[g.var] = max(ds)
        known.add(g.var)
    def cone(v: int) -> set[int]:
        if v in local_atoms:
            return set()
        out = {v}
        g = gm[v]
        for lit in (g.left, g.right):
            u = abs(lit)
            if u not in local_atoms:
                out |= cone(u)
        return out
    def frontier(v: int) -> set[tuple[int, int]]:
        out: set[tuple[int, int]] = set()
        stack = [v]; seen: set[int] = set()
        while stack:
            p = stack.pop()
            if p in seen or p in local_atoms:
                continue
            seen.add(p)
            for lit in (gm[p].left, gm[p].right):
                u = abs(lit)
                if u in local_atoms:
                    continue
                if lit < 0:
                    out.add((p, u))
                else:
                    stack.append(u)
        return out
    bwidth = {v: max((len(frontier(u)) for u in cone(v)), default=0) for v in gm}
    return pos, neg, depth, bwidth


def depth_one_family(k: int):
    local = set(range(1, 2*k + 1)); gates: list[Gate] = []; nxt = 2*k + 1; gs = []
    for j in range(k):
        g = nxt; nxt += 1
        gates.append(Gate(g, 2*j + 1, 2*j + 2)); gs.append(g)
    out = nxt; nxt += 1
    gates.append(Gate(out, -gs[0], -gs[1]))
    for j in range(2, k):
        new = nxt; nxt += 1
        gates.append(Gate(new, out, -gs[j])); out = new
    return local, gates, out


def Ebd(b: int, d: int) -> int:
    return (b + 2) ** (d + 1)


def within_bd_bound(count: int, S: int, b: int, d: int) -> bool:
    if count <= 1:
        return True
    return log(count) <= Ebd(b, d) * log(S) + 1e-12


def check_depth_one_barrier() -> None:
    for k in range(2, 9):
        local, gates, out = depth_one_family(k)
        pos, neg, depth, bwidth = analyze(local, gates)
        assert depth[out] == 1
        assert bwidth[out] == k
        assert len(pos[out]) == k
        assert len(neg[out]) == 2 ** k
        assert len(gates) == 2*k - 1


def check_small_signed_dags() -> None:
    local = {1, 2, 3, 4}
    for s5, s6, s5b in product((-1, 1), repeat=3):
        gates = [Gate(5, 1, -2), Gate(6, s5*5, 3), Gate(7, s6*6, s5b*5)]
        pos, neg, depth, bwidth = analyze(local, gates)
        S = len(local) + 3*len(gates)
        for v in (5, 6, 7):
            assert within_bd_bound(len(pos[v]), S, bwidth[v], depth[v])
            assert within_bd_bound(len(neg[v]), S, bwidth[v], depth[v])


def check_monotone_base() -> None:
    local = {1,2,3,4,5}
    gates = [Gate(6,1,-2), Gate(7,6,3), Gate(8,7,-4), Gate(9,8,5)]
    pos, neg, depth, bwidth = analyze(local, gates)
    assert depth[9] == 0 and bwidth[9] == 0
    assert len(pos[9]) == 5 and len(neg[9]) == 1


def check_cut_recurrence() -> None:
    for b in range(1, 7):
        for d in range(1, 7):
            e = Ebd(b, d); prev = Ebd(b, d-1)
            recurrence_exp = max(e + 1, e + 3*prev + 1) + 1
            assert recurrence_exp <= 3*e
            assert 3*e + 3*e + 1 <= 7*e


def check_tradeoff_shape() -> None:
    for b in (1,2,4,8,16):
        for d in (1,2,4,8):
            assert abs(log(Ebd(b,d)) - (d+1)*log(b+2)) < 1e-12


def main() -> None:
    check_depth_one_barrier()
    check_small_signed_dags()
    check_monotone_base()
    check_cut_recurrence()
    check_tradeoff_shape()
    print("C025_E2R_L1G_F3_NEGATIVE_DEPTH_METRIC = PASS")
    print("C025_E2R_L1G_F3_FRONTIER_WIDTH_METRIC = PASS")
    print("C025_E2R_L1G_F3_DEPTH_ONE_EXPONENTIAL_FRONTIER = PASS")
    print("C025_E2R_L1G_F3_DEPTH_ALONE_POLY_ROUTE = REFUTED")
    print("C025_E2R_L1G_F3_BD_REPRESENTATION_BOUND_FINITE = PASS")
    print("C025_E2R_L1G_F3_BD_CUT_RECURRENCE_CEILING = PASS")
    print("C025_E2R_L1G_F3_WIDTH_DEPTH_TRADEOFF_ALGEBRA = PASS")
    print("C025_E2R_L1G_F3_Q0_MONOTONE_BASE = PASS")
    print("claim_boundary = finite mechanics only; asymptotic width-depth tradeoff uses analytical F3 plus the external NW lower bound")

if __name__ == "__main__":
    main()
