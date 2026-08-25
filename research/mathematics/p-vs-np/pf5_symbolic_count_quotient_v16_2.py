#!/usr/bin/env python3
"""PF5 symbolic count quotient v16.2.

Restricted constructive whole-order quotient for

    D(n,m) = AND_{j=1..m} (x_1 OR ... OR x_n).

The raw prefix lattice has 2^(n+m) states. The exact quotient state is only
(i,j): selected variable count and selected identical-clause count, with
(n+1)(m+1) states and at most two abstract transitions per state.

Small controls are independently checked against the exponential exact PS-cut
and raw Bellman audit. Large controls use only the symbolic quotient.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pf5_slime_exact_optimality_gap_v11 as v11
import pf5_whole_order_prefix_state_quotient_v16 as v16


def duplicate_clause_family(n: int, m: int):
    if n < 1 or m < 1:
        raise ValueError("n,m must be >=1")
    clause = tuple(range(1, n + 1))
    return tuple(clause for _ in range(m))


def leaves_for(n: int, m: int):
    return [f"v:{i}" for i in range(1, n + 1)] + [f"c:{j}" for j in range(m)]


def quotient_state_from_mask(mask: int, leaves):
    i = 0
    j = 0
    for bit_index, leaf in enumerate(leaves):
        if not (mask & (1 << bit_index)):
            continue
        if leaf.startswith("v:"):
            i += 1
        else:
            j += 1
    return i, j


def symbolic_cut(n: int, m: int, i: int, j: int, endpoint_zero: bool = True):
    if not (0 <= i <= n and 0 <= j <= m):
        raise ValueError("state out of range")
    if endpoint_zero and ((i == 0 and j == 0) or (i == n and j == m)):
        return 0
    left = 2 if (i > 0 and j < m) else 1
    right = 2 if (i < n and j > 0) else 1
    return max(left, right)


def abstract_actions(n: int, m: int, i: int, j: int):
    actions = []
    if i < n:
        actions.append(("VAR", (i + 1, j)))
    if j < m:
        actions.append(("CLAUSE", (i, j + 1)))
    return actions


def symbolic_bellman(n: int, m: int):
    future = {}
    best_action = {}
    transition_checks = 0
    for rank in range(n + m, -1, -1):
        for i in range(n + 1):
            j = rank - i
            if not (0 <= j <= m):
                continue
            state = (i, j)
            if state == (n, m):
                future[state] = 0
                best_action[state] = None
                continue
            candidates = []
            for action, nxt in abstract_actions(n, m, i, j):
                value = max(
                    symbolic_cut(n, m, nxt[0], nxt[1], endpoint_zero=True),
                    future[nxt],
                )
                transition_checks += 1
                candidates.append((value, action, nxt))
            value, action, nxt = min(candidates, key=lambda row: (row[0], row[1]))
            future[state] = value
            best_action[state] = (action, nxt)

    # Caterpillar leaf edges: every singleton concrete leaf cut must also count.
    singleton_costs = []
    if n:
        singleton_costs.append(symbolic_cut(n, m, 1, 0, endpoint_zero=False))
    if m:
        singleton_costs.append(symbolic_cut(n, m, 0, 1, endpoint_zero=False))
    leaf_edge_max = max(singleton_costs, default=0)
    optimum = max(leaf_edge_max, future[(0, 0)])
    return {
        "future": future,
        "best_action": best_action,
        "leaf_edge_max": leaf_edge_max,
        "optimum": optimum,
        "state_count": (n + 1) * (m + 1),
        "transition_checks": transition_checks,
    }


def lift_symbolic_order(n: int, m: int, best_action):
    remaining_vars = list(range(1, n + 1))
    remaining_clauses = list(range(m))
    state = (0, 0)
    order = []
    lift_checks = 0
    while state != (n, m):
        action, nxt = best_action[state]
        if action == "VAR":
            if not remaining_vars:
                raise AssertionError("VAR action has no concrete lift")
            order.append(f"v:{remaining_vars.pop(0)}")
        elif action == "CLAUSE":
            if not remaining_clauses:
                raise AssertionError("CLAUSE action has no concrete lift")
            order.append(f"c:{remaining_clauses.pop(0)}")
        else:
            raise AssertionError(action)
        state = nxt
        lift_checks += 1
    if remaining_vars or remaining_clauses:
        raise AssertionError("incomplete concrete lift")
    return order, lift_checks


def verify_small(n: int, m: int):
    formula = duplicate_clause_family(n, m)
    leaves = leaves_for(n, m)
    index = {leaf: i for i, leaf in enumerate(leaves)}
    cut_values, cut_ledger = v11.exact_cut_cache(formula, leaves)
    full = (1 << len(leaves)) - 1
    decoder_checks = 0
    decoder_mismatches = []
    for mask in range(1 << len(leaves)):
        i, j = quotient_state_from_mask(mask, leaves)
        expected = symbolic_cut(n, m, i, j, endpoint_zero=True)
        observed = v16.state_cost(mask, full, cut_values)
        decoder_checks += 1
        if expected != observed:
            decoder_mismatches.append((mask, (i, j), expected, observed))
    if decoder_mismatches:
        raise AssertionError(f"symbolic cut decoder mismatch {decoder_mismatches[:3]}")

    raw_future, raw_best_bit, raw_transition_checks = v16.exact_future_bellman(
        leaves, cut_values
    )
    raw_order = v16.reconstruct_bellman_order(leaves, raw_best_bit)
    raw_singleton = max(cut_values[1 << i] for i in range(len(leaves)))
    raw_optimum = max(raw_singleton, raw_future[0])

    symbolic = symbolic_bellman(n, m)
    lifted, lift_checks = lift_symbolic_order(n, m, symbolic["best_action"])
    lifted_width = v11.order_width_from_cache(lifted, index, cut_values)

    if symbolic["optimum"] != raw_optimum or lifted_width != raw_optimum:
        raise AssertionError("symbolic Bellman/lift mismatch")

    # Exact future value must be constant on every count state (i,j).
    quotient_future_sets = {}
    for mask in range(1 << len(leaves)):
        state = quotient_state_from_mask(mask, leaves)
        quotient_future_sets.setdefault(state, set()).add(int(raw_future[mask]))
    unsafe = {state: vals for state, vals in quotient_future_sets.items() if len(vals) != 1}
    if unsafe:
        raise AssertionError(f"count quotient not future-congruent: {unsafe}")

    return {
        "n": n,
        "m": m,
        "raw_state_count": 1 << (n + m),
        "quotient_state_count": symbolic["state_count"],
        "decoder_checks": decoder_checks,
        "raw_optimum": raw_optimum,
        "symbolic_optimum": symbolic["optimum"],
        "lifted_width": lifted_width,
        "future_congruence_verified": True,
        "cut_ledger": cut_ledger,
        "raw_bellman_transition_checks": raw_transition_checks,
        "symbolic_transition_checks": symbolic["transition_checks"],
        "lift_checks": lift_checks,
    }


def verify_large(n: int, m: int):
    symbolic = symbolic_bellman(n, m)
    order, lift_checks = lift_symbolic_order(n, m, symbolic["best_action"])
    order_payload = json.dumps(order, separators=(",", ":")).encode()
    return {
        "n": n,
        "m": m,
        "raw_state_count_symbolic_expression": f"2^{n+m}",
        "quotient_state_count": symbolic["state_count"],
        "quotient_transition_checks": symbolic["transition_checks"],
        "optimum": symbolic["optimum"],
        "lift_checks": lift_checks,
        "lifted_order_length": len(order),
        "lifted_order_sha256": hashlib.sha256(order_payload).hexdigest(),
        "lifted_order_prefix": order[:8],
        "lifted_order_suffix": order[-8:],
        "raw_subset_enumeration_used": False,
    }


def run():
    small_controls = []
    for n in range(1, 5):
        for m in range(1, 5):
            small_controls.append(verify_small(n, m))

    large_controls = [
        verify_large(n, m)
        for n, m in [(16, 16), (64, 64), (256, 256), (512, 512)]
    ]

    result = {
        "artifact_id": "PF5-SYMBOLIC-COUNT-QUOTIENT-V16.2",
        "status": "RESTRICTED_CONSTRUCTIVE_WHOLE_ORDER_QUOTIENT_PASS",
        "family": "D(n,m)=AND_m(x1 OR ... OR xn)",
        "incidence_graph": "K_{n,m}",
        "symbolic_state": "(selected_variable_count,selected_clause_count)",
        "state_bound": "(n+1)(m+1)",
        "action_classes": ["VAR", "CLAUSE"],
        "max_outgoing_abstract_actions": 2,
        "cut_decoder": {
            "left": "2 iff i>0 and j<m else 1",
            "right": "2 iff i<n and j>0 else 1",
            "cut": "max(left,right), with empty/full Bellman endpoint cost 0",
        },
        "small_exhaustive_controls": small_controls,
        "large_symbolic_only_controls": large_controls,
        "theorem": {
            "rank_terminal_preserved": True,
            "exact_cost_preserved": True,
            "abstract_action_coverage": True,
            "transition_closure": True,
            "future_congruence_by_permutation_symmetry": True,
            "concrete_order_lift": True,
            "quotient_bellman_work": "O(nm)",
            "quotient_state_count_polynomial": True,
            "raw_structural_treewidth_may_grow_as_min_n_m": True,
        },
        "epistemic_firewall": {
            "small_raw_enumeration_used_only_for_independent_validation": True,
            "large_controls_use_no_raw_subset_enumeration": True,
            "supplied_family_symmetry_is_essential": True,
            "universal_symmetry_or_message_discovery_not_proved": True,
        },
        "next_gate": "DISCOVER_PROOF_CARRYING_PREFIX_ORBITS_OR_STRONGER_MESSAGES_WITHOUT_SUPPLIED_SYMMETRY",
        "universal_polynomial_prefix_quotient": "OPEN",
        "p_vs_np": "OPEN",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    result = run()
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print("PF5_SYMBOLIC_COUNT_QUOTIENT_V16_2 =", result["status"])
    print("SMALL_CONTROLS =", len(result["small_exhaustive_controls"]))
    print("LARGE_CONTROLS =", [
        (r["n"], r["m"], r["quotient_state_count"], r["optimum"])
        for r in result["large_symbolic_only_controls"]
    ])
    print("NEXT_GATE =", result["next_gate"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
