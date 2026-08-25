#!/usr/bin/env python3
"""PF5 logarithmic feedback-edge relation cap probe v14.3.

Post-hoc mechanism admission on already-observed seed 910000 only.

Let G be the graph of all sound binary relations among distinct nonempty
projected clauses. Let r = |E|-|V|+components be its cyclomatic number. A
canonical spanning forest leaves exactly r feedback edges. If U is the set of
feedback-edge endpoints, |U| <= 2r. Enumerate the at most 2^|U| <= 4^r binary
assignments to U; reject assignments violating a feedback edge; for every
survivor count the spanning forest exactly by tree DP with U fixed. Hence exact
relation-pattern counting costs O(4^r poly(L)).

With a frozen universal exponent q=2, admit the full relation graph only when
4^r <= L^q, where L is an explicit source-size proxy. Otherwise return OPEN for
this feature (a later Slime portfolio may fall back to earlier candidates).
This is a restricted polynomial message language, not arbitrary graph counting.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9

SEED = 910000
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7
PREFIX = ["c:0", "v:2", "c:4", "v:5", "c:3"]
CHOICES = ["c:5", "c:6", "v:4"]
CAPABILITY_EXPONENT_Q = 2


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location("slime_v4_feedback_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load producer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def distinct_projected(formula, clause_indices, visible_variables):
    values = set()
    for index in sorted(clause_indices):
        projected = frozenset(
            lit for lit in formula[index] if abs(lit) in visible_variables
        )
        if projected:
            values.add(projected)
    return sorted(values, key=lambda c: (len(c), tuple(sorted(c))))


def all_relation_edges(producer, clauses):
    edges = []
    for i in range(len(clauses)):
        for j in range(i + 1, len(clauses)):
            allowed, reasons = producer.v3._allowed_pairs(clauses[i], clauses[j])
            if len(allowed) < 4:
                edges.append((i, j, tuple(allowed), tuple(reasons)))
    return sorted(edges, key=lambda e: (len(e[2]), e[0], e[1]))


def spanning_forest_and_feedback(node_count, edges):
    parent = list(range(node_count))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    forest = []
    feedback = []
    for edge in edges:
        i, j = edge[0], edge[1]
        ri, rj = find(i), find(j)
        if ri == rj:
            feedback.append(edge)
        else:
            if ri > rj:
                ri, rj = rj, ri
            parent[rj] = ri
            forest.append(edge)
    return forest, feedback


def forest_components(node_count, forest_edges):
    adjacency = [[] for _ in range(node_count)]
    for edge_index, (i, j, _, _) in enumerate(forest_edges):
        adjacency[i].append((j, edge_index))
        adjacency[j].append((i, edge_index))
    seen = set()
    components = []
    for start in range(node_count):
        if start in seen:
            continue
        vertices = []
        edge_ids = set()
        stack = [start]
        seen.add(start)
        while stack:
            node = stack.pop()
            vertices.append(node)
            for nxt, edge_id in adjacency[node]:
                edge_ids.add(edge_id)
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        components.append(
            (
                tuple(sorted(vertices)),
                tuple(forest_edges[i] for i in sorted(edge_ids)),
            )
        )
    return components


def tree_component_count(vertices, edges, fixed):
    if not vertices:
        return 1
    adjacency = {v: [] for v in vertices}
    for i, j, allowed, _ in edges:
        aset = set(allowed)
        adjacency[i].append((j, aset, False))
        adjacency[j].append((i, aset, True))
    root = min(vertices)
    parent = {root: None}
    parent_edge = {}
    order = [root]
    for node in order:
        for nxt, allowed, reversed_dir in adjacency[node]:
            if nxt in parent:
                continue
            parent[nxt] = node
            parent_edge[nxt] = (allowed, reversed_dir)
            order.append(nxt)
    if set(order) != set(vertices):
        raise AssertionError("forest component disconnected")
    children = {v: [] for v in vertices}
    for child, par in parent.items():
        if par is not None:
            children[par].append(child)
    dp = {}
    for node in reversed(order):
        vals = [0, 0]
        for node_value in (0, 1):
            if node in fixed and fixed[node] != node_value:
                continue
            count = 1
            for child in children[node]:
                allowed, reversed_dir = parent_edge[child]
                subtotal = 0
                for child_value in (0, 1):
                    pair = (
                        (child_value, node_value)
                        if reversed_dir
                        else (node_value, child_value)
                    )
                    if pair in allowed:
                        subtotal += dp[child][child_value]
                count *= subtotal
            vals[node_value] = count
        dp[node] = vals
    return dp[root][0] + dp[root][1]


def exact_bounded_feedback_count(node_count, edges, work_budget):
    forest, feedback = spanning_forest_and_feedback(node_count, edges)
    rank = len(feedback)
    endpoints = sorted({v for e in feedback for v in (e[0], e[1])})
    enumeration_rows = 1 << len(endpoints)
    if enumeration_rows > work_budget:
        return {
            "status": "OPEN_FEEDBACK_BUDGET",
            "cycle_rank": rank,
            "endpoint_count": len(endpoints),
            "enumeration_rows": enumeration_rows,
        }

    components = forest_components(node_count, forest)
    total = 0
    accepted_endpoint_rows = 0
    feedback_checks = 0
    tree_dp_calls = 0
    for bits in itertools.product((0, 1), repeat=len(endpoints)):
        fixed = dict(zip(endpoints, bits))
        feedback_ok = True
        for i, j, allowed, _ in feedback:
            feedback_checks += 1
            if (fixed[i], fixed[j]) not in set(allowed):
                feedback_ok = False
                break
        if not feedback_ok:
            continue
        accepted_endpoint_rows += 1
        ways = 1
        for vertices, component_edges in components:
            ways *= tree_component_count(vertices, component_edges, fixed)
            tree_dp_calls += 1
        total += ways
    return {
        "status": "CLOSED_POLY_UNDER_FEEDBACK_BUDGET",
        "cycle_rank": rank,
        "endpoint_count": len(endpoints),
        "enumeration_rows": enumeration_rows,
        "accepted_endpoint_rows": accepted_endpoint_rows,
        "feedback_checks": feedback_checks,
        "tree_dp_calls": tree_dp_calls,
        "exact_relation_pattern_count": total,
    }


def side_report(producer, formula, clause_indices, visible_variables, L):
    clauses = distinct_projected(formula, clause_indices, visible_variables)
    edges = all_relation_edges(producer, clauses)
    work_budget = L ** CAPABILITY_EXPONENT_Q
    count = exact_bounded_feedback_count(len(clauses), edges, work_budget)
    assignment_bound = 1 << len(visible_variables)
    report = {
        "visible_variables": sorted(visible_variables),
        "distinct_projected_clause_count": len(clauses),
        "relation_edge_count": len(edges),
        "source_size_L": L,
        "capability_exponent_q": CAPABILITY_EXPONENT_Q,
        "work_budget_L_pow_q": work_budget,
        **count,
    }
    if count["status"] == "CLOSED_POLY_UNDER_FEEDBACK_BUDGET":
        report["certified_signature_cap"] = min(
            assignment_bound,
            count["exact_relation_pattern_count"],
        )
    else:
        report["certified_signature_cap"] = None
    return report


def choice_report(producer, formula, selected):
    all_clauses = set(range(len(formula)))
    all_variables = {abs(lit) for clause in formula for lit in clause}
    selected_variables = {
        int(x.split(":", 1)[1]) for x in selected if x.startswith("v:")
    }
    selected_clauses = {
        int(x.split(":", 1)[1]) for x in selected if x.startswith("c:")
    }
    right_variables = all_variables - selected_variables
    literal_count = sum(len(c) for c in formula)
    L = 1 + len(all_variables) + len(formula) + literal_count
    left = side_report(
        producer, formula, all_clauses - selected_clauses, selected_variables, L
    )
    right = side_report(
        producer, formula, selected_clauses, right_variables, L
    )
    statuses = {left["status"], right["status"]}
    if statuses == {"CLOSED_POLY_UNDER_FEEDBACK_BUDGET"}:
        combined = max(left["certified_signature_cap"], right["certified_signature_cap"])
        status = "CLOSED_POLY_UNDER_FEEDBACK_BUDGET"
    else:
        combined = None
        status = "OPEN_FEEDBACK_BUDGET"
    return {
        "status": status,
        "combined_cap": combined,
        "left": left,
        "right": right,
    }


def run(producer, identity):
    formula = v9.random_connected_3cnf(SEED, VARIABLE_COUNT, CLAUSE_COUNT)
    rows = []
    for choice in CHOICES:
        rows.append(
            {
                "choice": choice,
                **choice_report(producer, formula, set(PREFIX + [choice])),
            }
        )
    c5 = next(r for r in rows if r["choice"] == "c:5")
    c6 = next(r for r in rows if r["choice"] == "c:6")
    distinguishes = (
        c5["status"] == c6["status"] == "CLOSED_POLY_UNDER_FEEDBACK_BUDGET"
        and c6["combined_cap"] < c5["combined_cap"]
    )
    result = {
        "artifact_id": "PF5-LOG-FEEDBACK-RELATION-CAP-PROBE-V14.3",
        "status": "POSTHOC_THEOREM_FEATURE_PROBE_COMPLETE",
        "seed": SEED,
        "posthoc_not_holdout": True,
        "producer": identity,
        "capability_exponent_q_frozen": CAPABILITY_EXPONENT_Q,
        "prefix": PREFIX,
        "choice_rows": rows,
        "bounded_feedback_cap_distinguishes_c6_from_c5": distinguishes,
        "theorem": {
            "cycle_rank_equals_non_tree_feedback_edge_count_for_spanning_forest": True,
            "feedback_endpoint_count_at_most_2r": True,
            "endpoint_assignments_at_most_4_pow_r": True,
            "forest_remainder_counted_exactly_by_tree_dp": True,
            "runtime_bound": "O(4^r * poly(L))",
            "admission_rule": "4^r <= L^q with fixed q=2",
            "admitted_work_is_polynomial_in_explicit_source": True,
            "source_only": True,
            "arbitrary_relation_graph_counting_admitted": False,
        },
        "next_candidate_class": "SLIME_LOG_FEEDBACK_RELATION_PRESSURE",
        "p_vs_np": "OPEN",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--producer-path", type=Path, required=True)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    raw = args.producer_path.read_bytes()
    producer = import_producer(args.producer_path)
    result = run(
        producer,
        {
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "PINNED_V4_POSTHOC_LOG_FEEDBACK_PROBE",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_LOG_FEEDBACK_RELATION_CAP_PROBE_V14_3 =", result["status"])
    for row in result["choice_rows"]:
        print(row["choice"], row["status"], "CAP=", row["combined_cap"], "L/R rank=", row["left"]["cycle_rank"], row["right"]["cycle_rank"], "rows=", row["left"]["enumeration_rows"], row["right"]["enumeration_rows"])
    print("DISTINGUISHES =", result["bounded_feedback_cap_distinguishes_c6_from_c5"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
