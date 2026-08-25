#!/usr/bin/env python3
"""Finite mechanics for the deterministic live-width path-DP lane.

Checks interval bags, exact path-DP feasibility against root brute force on small
B2 circuits, constant-width parity traces, and finite instances of the pair-
fanout architecture. Analytic asymptotic claims remain separate from CI.
"""

from __future__ import annotations

from itertools import product


def lit(name, neg=False):
    return (name, bool(neg))


def lit_value(L, env):
    name, neg = L
    v = env[name]
    return (not v) if neg else v


def live_bags(gates):
    first = {}
    last = {}
    for t, (out, a, b) in enumerate(gates):
        vars_here = {out, a[0], b[0]}
        for v in vars_here:
            first.setdefault(v, t)
            last[v] = t
    bags = []
    for t in range(len(gates)):
        bag = tuple(sorted(v for v in first if first[v] <= t <= last[v]))
        bags.append(bag)
    width = max((len(b) - 1 for b in bags), default=-1)
    return first, last, bags, width


def verify_path_decomposition(gates, bags):
    # Every gate-local primal clique is covered.
    for t, (out, a, b) in enumerate(gates):
        need = {out, a[0], b[0]}
        assert need.issubset(set(bags[t]))

    # Every variable appears on a contiguous interval.
    all_vars = set().union(*(set(b) for b in bags)) if bags else set()
    for v in all_vars:
        idx = [i for i, bag in enumerate(bags) if v in bag]
        assert idx == list(range(min(idx), max(idx) + 1))


def path_dp_feasible(gates, unary):
    _, _, bags, _ = live_bags(gates)
    prev_bag = tuple()
    prev_states = {tuple()}

    for t, bag in enumerate(bags):
        pos = {v: i for i, v in enumerate(bag)}
        prev_pos = {v: i for i, v in enumerate(prev_bag)}
        inter = tuple(v for v in bag if v in prev_pos)

        allowed_inter = set()
        for state in prev_states:
            allowed_inter.add(tuple(state[prev_pos[v]] for v in inter))

        out, a, b = gates[t]
        next_states = set()
        for bits in product((False, True), repeat=len(bag)):
            if tuple(bits[pos[v]] for v in inter) not in allowed_inter:
                continue
            env = {v: bits[pos[v]] for v in bag}
            if any(v in env and env[v] != val for v, val in unary.items()):
                continue
            if env[out] != (lit_value(a, env) and lit_value(b, env)):
                continue
            next_states.add(bits)

        prev_bag = bag
        prev_states = next_states
        if not prev_states:
            return False

    return bool(prev_states)


def eval_gates(gates, root_env):
    env = dict(root_env)
    for out, a, b in gates:
        env[out] = lit_value(a, env) and lit_value(b, env)
    return env


def parity_gates(n):
    assert n >= 2
    gates = []
    prev = "x0"
    for i in range(1, n):
        x = f"x{i}"
        t1 = f"p{i}_a"
        t2 = f"p{i}_b"
        nxt = f"p{i}"
        gates.append((t1, lit(prev), lit(x)))
        gates.append((t2, lit(prev, True), lit(x, True)))
        gates.append((nxt, lit(t1, True), lit(t2, True)))
        prev = nxt
    return gates, prev


def check_path_dp_vs_bruteforce():
    for n in range(2, 6):
        gates, out = parity_gates(n)
        roots = [f"x{i}" for i in range(n)]
        for fixed_prefix in range(n + 1):
            for prefix_bits in product((False, True), repeat=fixed_prefix):
                rho = dict(zip(roots[:fixed_prefix], prefix_bits))
                for out_value in (False, True):
                    unary = dict(rho)
                    unary[out] = out_value
                    got = path_dp_feasible(gates, unary)

                    expected = False
                    free = roots[fixed_prefix:]
                    for free_bits in product((False, True), repeat=len(free)):
                        root_env = dict(rho)
                        root_env.update(zip(free, free_bits))
                        env = eval_gates(gates, root_env)
                        if env[out] == out_value:
                            expected = True
                            break
                    assert got == expected


def check_parity_constant_live_width():
    widths = []
    for n in range(2, 65):
        gates, _ = parity_gates(n)
        _, _, bags, width = live_bags(gates)
        verify_path_decomposition(gates, bags)
        widths.append(width)
    assert max(widths) <= 5


def pair_fanout_gates(n):
    assert n >= 3
    gates = []
    es = []
    for i in range(n):
        e = f"e{i}"
        es.append(e)
        gates.append((e, lit(f"x{i}"), lit(f"y{i}")))

    gs = []
    for i in range(n):
        for j in range(i + 1, n):
            g = f"g{i}_{j}"
            gs.append(g)
            gates.append((g, lit(es[i]), lit(es[j])))

    # Keep every pair gate in one output cone.
    acc = gs[0]
    for k, g in enumerate(gs[1:], 1):
        nxt = f"agg{k}"
        gates.append((nxt, lit(acc), lit(g)))
        acc = nxt
    return gates, acc


def check_pair_fanout_canonical_trace():
    for n in range(3, 15):
        gates, _ = pair_fanout_gates(n)
        _, _, bags, width = live_bags(gates)
        verify_path_decomposition(gates, bags)
        assert width >= n - 1
        assert len(gates) < 2 * n * n


def main():
    check_path_dp_vs_bruteforce()
    check_parity_constant_live_width()
    check_pair_fanout_canonical_trace()
    print("AKINATOR_LIVE_BAGS_PATH_DECOMPOSITION_FINITE = PASS")
    print("AKINATOR_LIVE_DP_EXACT_FEASIBILITY_VS_BRUTE_FORCE = PASS")
    print("AKINATOR_PARITY_CHAIN_CONSTANT_LIVE_WIDTH_FINITE = PASS")
    print("AKINATOR_PAIR_FANOUT_LARGE_LIVE_WIDTH_CANONICAL_FINITE = PASS")
    print("LIVE_WIDTH_DP_COMPLEXITY = ANALYTIC_THEOREM_NOT_CI")
    print("PAIR_FANOUT_ANY_TOPOLOGICAL_ORDER_LOWER_BOUND = ANALYTIC_NOT_CI")
    print("EQUIVALENT_LOW_WIDTH_REWRITE_DISCOVERY = OPEN")
    print("GLOBAL_PROGRESS_CERTIFICATE = OPEN")
    print("POLYNOMIAL_AKINATOR = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
