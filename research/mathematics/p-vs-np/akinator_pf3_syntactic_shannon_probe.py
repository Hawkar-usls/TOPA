#!/usr/bin/env python3
"""Finite replay for PF3-S1 syntactic Shannon residual-novelty barrier.

Exact frozen lane:
- Boolean DAG with structural interning;
- constant propagation, idempotence, direct complements, double negation;
- existential projection by OR(cofactor0, cofactor1);
- no distributive factoring or semantic equivalence oracle.

The script measures live and cumulative created nodes on equality CNFs.
Finite replay is not the proof of the asymptotic theorem.
"""

from __future__ import annotations


class DAG:
    def __init__(self) -> None:
        self.keys = [('F',), ('T',)]
        self.intern = {('F',): 0, ('T',): 1}

    def _get(self, key):
        if key in self.intern:
            return self.intern[key]
        idx = len(self.keys)
        self.keys.append(key)
        self.intern[key] = idx
        return idx

    def var(self, v: int) -> int:
        return self._get(('V', v))

    def _direct_complements(self, a: int, b: int) -> bool:
        return self.keys[a] == ('N', b) or self.keys[b] == ('N', a)

    def neg(self, a: int) -> int:
        if a == 0:
            return 1
        if a == 1:
            return 0
        k = self.keys[a]
        if k[0] == 'N':
            return k[1]
        return self._get(('N', a))

    def AND(self, a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        if a == 1:
            return b
        if b == 1:
            return a
        if a == b:
            return a
        if self._direct_complements(a, b):
            return 0
        if a > b:
            a, b = b, a
        return self._get(('A', a, b))

    def OR(self, a: int, b: int) -> int:
        if a == 1 or b == 1:
            return 1
        if a == 0:
            return b
        if b == 0:
            return a
        if a == b:
            return a
        if self._direct_complements(a, b):
            return 1
        if a > b:
            a, b = b, a
        return self._get(('O', a, b))

    def equality(self, a: int, b: int) -> int:
        # (not a or b) and (a or not b)
        return self.AND(self.OR(self.neg(a), b), self.OR(a, self.neg(b)))

    def restrict(self, root: int, var: int, value: bool) -> int:
        memo = {}

        def rec(u: int) -> int:
            if u in memo:
                return memo[u]
            k = self.keys[u]
            tag = k[0]
            if tag in ('F', 'T'):
                r = u
            elif tag == 'V':
                r = (1 if value else 0) if k[1] == var else u
            elif tag == 'N':
                r = self.neg(rec(k[1]))
            elif tag == 'A':
                r = self.AND(rec(k[1]), rec(k[2]))
            elif tag == 'O':
                r = self.OR(rec(k[1]), rec(k[2]))
            else:
                raise AssertionError(tag)
            memo[u] = r
            return r

        return rec(root)

    def exists(self, root: int, var: int) -> int:
        return self.OR(self.restrict(root, var, False), self.restrict(root, var, True))

    def live_node_count(self, root: int) -> int:
        seen = set()

        def visit(u: int) -> None:
            if u in seen:
                return
            seen.add(u)
            k = self.keys[u]
            if k[0] == 'N':
                visit(k[1])
            elif k[0] in ('A', 'O'):
                visit(k[1])
                visit(k[2])

        visit(root)
        return len(seen)


def equality_dag(n: int):
    d = DAG()
    xs = [d.var(i + 1) for i in range(n)]
    ys = [d.var(n + i + 1) for i in range(n)]
    root = 1
    for i in range(n):
        root = d.AND(root, d.equality(xs[i], ys[i]))
    return d, root


def run_x_first(n: int):
    d, root = equality_dag(n)
    live_after_x = []
    for v in range(1, n + 1):
        root = d.exists(root, v)
        live_after_x.append(d.live_node_count(root))
    total_after_x = len(d.keys)
    root_after_x = root

    # Continue through Y only to demonstrate that the final semantic/DAG result
    # can be TRUE even after exponential cumulative construction was paid.
    for v in range(n + 1, 2 * n + 1):
        root = d.exists(root, v)
    return {
        'n': n,
        'live_after_x': live_after_x,
        'total_after_x': total_after_x,
        'root_after_x': root_after_x,
        'final_root': root,
        'final_live': d.live_node_count(root),
        'd_total': len(d.keys),
    }


def check_pf1_equality_pair() -> None:
    # For equality pair encoded as (~x or y) & (x or ~y), the PF1 sides are
    # P=~y and N=y, hence P OR N = TRUE before branch birth.
    d = DAG()
    y = d.var(1)
    p = d.neg(y)
    n = y
    assert d.OR(p, n) == 1


def main() -> None:
    rows = []
    for n in range(1, 11):
        row = run_x_first(n)
        rows.append(row)
        assert row['final_root'] == 1
        assert row['final_live'] == 1
        # Cumulative node creation visibly dominates a 2^n lower benchmark on
        # these finite fixtures. The analytical note proves the frozen-lane
        # branch-count lower bound; this assertion is only finite mechanics.
        assert row['d_total'] >= (1 << n)

    check_pf1_equality_pair()

    # Deterministic monotone growth sanity check.
    for prev, cur in zip(rows, rows[1:]):
        assert cur['d_total'] > prev['d_total']

    print('AKINATOR_PF3_SYNTACTIC_SHANNON_EQUALITY_FINITE_REPLAY = PASS')
    print('AKINATOR_PF3_D_TOTAL_GE_2_POW_N_TESTED_N_1_TO_10 = PASS')
    print('AKINATOR_PF3_FINAL_TRUE_AFTER_EXPENSIVE_HISTORY = PASS')
    print('AKINATOR_PF3_PF1_EQUALITY_PREBIRTH_COLLAPSE = PASS')
    print('SYNTACTIC_SHANNON_EXPONENTIAL_ROUTE_CLOSURE = ANALYTIC_FROZEN_LANE_NOT_CI')
    print('PF3_UNIVERSAL_ALGEBRAIC_ORBIT_QUOTIENT = OPEN')
    print('P_VS_NP = OPEN')


if __name__ == '__main__':
    main()
