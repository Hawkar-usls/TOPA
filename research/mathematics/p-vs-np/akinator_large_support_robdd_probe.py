#!/usr/bin/env python3
"""Finite mechanics for the large-support ROBDD certificate lane.

Checks exact AND/NOT construction on reduced ordered decision DAGs, linear parity
certificates, and the explicit EQ_n bad-order exponential frontier. The script
validates finite mechanics only; asymptotic theorems are proved in the note.
"""

from __future__ import annotations

from itertools import product


class ROBDD:
    def __init__(self, order):
        self.order = {name: i for i, name in enumerate(order)}
        self.nodes = {0: None, 1: None}
        self.unique = {}
        self.next_id = 2

    def mk(self, idx, low, high):
        if low == high:
            return low
        key = (idx, low, high)
        if key in self.unique:
            return self.unique[key]
        u = self.next_id
        self.next_id += 1
        self.unique[key] = u
        self.nodes[u] = key
        return u

    def var(self, name):
        return self.mk(self.order[name], 0, 1)

    def top(self, u):
        return 10**18 if u < 2 else self.nodes[u][0]

    def cof(self, u, idx):
        if u < 2:
            return u, u
        var_idx, low, high = self.nodes[u]
        if var_idx == idx:
            return low, high
        return u, u

    def negate(self, root):
        memo = {}

        def rec(u):
            if u == 0:
                return 1
            if u == 1:
                return 0
            if u in memo:
                return memo[u]
            idx, low, high = self.nodes[u]
            out = self.mk(idx, rec(low), rec(high))
            memo[u] = out
            return out

        return rec(root)

    def and_(self, a, b):
        memo = {}

        def rec(u, v):
            if u == 0 or v == 0:
                return 0
            if u == 1:
                return v
            if v == 1:
                return u
            key = (u, v) if u <= v else (v, u)
            if key in memo:
                return memo[key]
            idx = min(self.top(u), self.top(v))
            u0, u1 = self.cof(u, idx)
            v0, v1 = self.cof(v, idx)
            out = self.mk(idx, rec(u0, v0), rec(u1, v1))
            memo[key] = out
            return out

        return rec(a, b)

    def or_(self, a, b):
        return self.negate(self.and_(self.negate(a), self.negate(b)))

    def xor(self, a, b):
        left = self.and_(a, self.negate(b))
        right = self.and_(self.negate(a), b)
        return self.or_(left, right)

    def iff(self, a, b):
        return self.negate(self.xor(a, b))

    def reachable_nodes(self, root):
        seen = set()

        def dfs(u):
            if u < 2 or u in seen:
                return
            seen.add(u)
            _, low, high = self.nodes[u]
            dfs(low)
            dfs(high)

        dfs(root)
        return seen

    def size(self, root):
        return len(self.reachable_nodes(root))

    def eval(self, root, assignment):
        u = root
        while u >= 2:
            idx, low, high = self.nodes[u]
            u = high if assignment[idx] else low
        return bool(u)


def build_parity(n):
    names = [f"x{i}" for i in range(n)]
    bdd = ROBDD(names)
    root = 0
    for name in names:
        root = bdd.xor(root, bdd.var(name))
    return bdd, root


def build_eq(n, interleaved):
    if interleaved:
        order = [name for i in range(n) for name in (f"x{i}", f"y{i}")]
    else:
        order = [f"x{i}" for i in range(n)] + [f"y{i}" for i in range(n)]
    bdd = ROBDD(order)
    root = 1
    for i in range(n):
        pair_eq = bdd.iff(bdd.var(f"x{i}"), bdd.var(f"y{i}"))
        root = bdd.and_(root, pair_eq)
    return bdd, root


def check_truth_tables():
    for n in range(1, 6):
        bdd, root = build_parity(n)
        for bits in product((False, True), repeat=n):
            assert bdd.eval(root, bits) == (sum(bits) % 2 == 1)

    for n in range(1, 5):
        for interleaved in (False, True):
            bdd, root = build_eq(n, interleaved)
            order = sorted(bdd.order, key=bdd.order.get)
            for bits in product((False, True), repeat=2 * n):
                env = dict(zip(order, bits))
                expected = all(env[f"x{i}"] == env[f"y{i}"] for i in range(n))
                assignment = tuple(env[name] for name in order)
                assert bdd.eval(root, assignment) == expected


def check_parity_linear_size():
    for n in range(1, 33):
        bdd, root = build_parity(n)
        assert bdd.size(root) <= 2 * n


def check_eq_order_gap():
    for n in range(1, 10):
        bad, bad_root = build_eq(n, interleaved=False)
        good, good_root = build_eq(n, interleaved=True)
        bad_size = bad.size(bad_root)
        good_size = good.size(good_root)
        # The X-then-Y cut has 2^n distinct residual equality targets.
        assert bad_size >= 2**n
        # The interleaved representation remains constant-width / linear-size.
        assert good_size <= 4 * n


def check_residual_frontier_exactness_small_n():
    # After fixing all X bits in EQ_n with X-then-Y order, the residual function
    # is exactly one point-indicator on Y. There are 2^n distinct such functions.
    for n in range(1, 9):
        residual_signatures = set()
        ys = list(product((False, True), repeat=n))
        for x in product((False, True), repeat=n):
            signature = tuple(y == x for y in ys)
            residual_signatures.add(signature)
        assert len(residual_signatures) == 2**n


def main():
    check_truth_tables()
    check_parity_linear_size()
    check_eq_order_gap()
    check_residual_frontier_exactness_small_n()
    print("AKINATOR_ROBDD_AND_NOT_EXACT_TRUTH_TABLE_REPLAY = PASS")
    print("AKINATOR_ROBDD_PARITY_LINEAR_SIZE_FINITE = PASS")
    print("AKINATOR_ROBDD_EQ_BAD_ORDER_EXPONENTIAL_FRONTIER_FINITE = PASS")
    print("AKINATOR_ROBDD_EQ_INTERLEAVED_LINEAR_SIZE_FINITE = PASS")
    print("AKINATOR_ROBDD_RESIDUAL_FRONTIER_EXACTNESS_FINITE = PASS")
    print("ROBDD_LOCAL_CERTIFICATE_THEOREM = ANALYTIC_NOT_CI")
    print("GOOD_ORDER_DISCOVERY = OPEN")
    print("GLOBAL_PROGRESS = OPEN")
    print("POLYNOMIAL_AKINATOR = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
