#!/usr/bin/env python3
"""PF5 full relation-graph probe v14.2 for already-observed seed 910000.

Post-hoc diagnostic only. At the first v4 local gap, compare the polynomial v4
pseudoforest cap with an exponential audit-only count of *all* already-certified
binary projected-clause relations. This asks whether the residual gap is caused
by relation edges rejected to keep cyclomatic number <=1, or whether pairwise
relations themselves are insufficient.
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


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location("slime_v4_full_relation_diag", path)
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
                edges.append(
                    {
                        "i": i,
                        "j": j,
                        "allowed": [list(x) for x in allowed],
                        "reasons": list(reasons),
                        "allowed_pair_count": len(allowed),
                    }
                )
    return edges


def graph_cycle_rank(node_count, edges):
    if node_count == 0:
        return 0
    adjacency = [[] for _ in range(node_count)]
    for edge in edges:
        adjacency[edge["i"]].append(edge["j"])
        adjacency[edge["j"]].append(edge["i"])
    seen = set()
    components = 0
    for root in range(node_count):
        if root in seen:
            continue
        components += 1
        stack = [root]
        seen.add(root)
        while stack:
            node = stack.pop()
            for nxt in adjacency[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return len(edges) - node_count + components


def count_all_relation_patterns(node_count, edges):
    count = 0
    for bits in itertools.product((0, 1), repeat=node_count):
        if all(
            [bits[e["i"]], bits[e["j"]]] in e["allowed"]
            for e in edges
        ):
            count += 1
    return count


def side_report(producer, formula, clause_indices, visible_variables):
    clauses = distinct_projected(formula, clause_indices, visible_variables)
    all_edges = all_relation_edges(producer, clauses)
    pseudo_edges, rejected = producer._relation_pseudoforest(clauses)
    pseudo_patterns, shape = producer._count_pseudoforest_patterns(
        len(clauses), pseudo_edges
    )
    full_patterns = count_all_relation_patterns(len(clauses), all_edges)
    assignment_bound = 1 << len(visible_variables)
    return {
        "visible_variables": sorted(visible_variables),
        "projected_clauses": [
            sorted(c, key=lambda x: (abs(x), x < 0)) for c in clauses
        ],
        "all_relation_edges": all_edges,
        "all_relation_edge_count": len(all_edges),
        "all_relation_cycle_rank": graph_cycle_rank(len(clauses), all_edges),
        "pseudoforest_edge_count": len(pseudo_edges),
        "pseudoforest_rejected_sound_edges": rejected,
        "pseudoforest_tree_components": shape["tree_components"],
        "pseudoforest_unicyclic_components": shape["unicyclic_components"],
        "assignment_bound": assignment_bound,
        "pseudoforest_pattern_bound": pseudo_patterns,
        "full_relation_pattern_bound_audit_only": full_patterns,
        "pseudoforest_signature_cap": min(assignment_bound, pseudo_patterns),
        "full_relation_signature_cap_audit_only": min(assignment_bound, full_patterns),
    }


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
    left = side_report(
        producer, formula, all_clauses - selected_clauses, selected_variables
    )
    right = side_report(
        producer, formula, selected_clauses, right_variables
    )
    return {
        "left": left,
        "right": right,
        "pseudoforest_combined_cap": max(
            left["pseudoforest_signature_cap"],
            right["pseudoforest_signature_cap"],
        ),
        "full_relation_combined_cap_audit_only": max(
            left["full_relation_signature_cap_audit_only"],
            right["full_relation_signature_cap_audit_only"],
        ),
        "max_full_relation_cycle_rank": max(
            left["all_relation_cycle_rank"],
            right["all_relation_cycle_rank"],
        ),
    }


def run(producer, producer_identity):
    formula = v9.random_connected_3cnf(SEED, VARIABLE_COUNT, CLAUSE_COUNT)
    rows = []
    for choice in CHOICES:
        rows.append(
            {
                "choice": choice,
                **choice_report(producer, formula, set(PREFIX + [choice])),
            }
        )
    c5 = next(row for row in rows if row["choice"] == "c:5")
    c6 = next(row for row in rows if row["choice"] == "c:6")
    full_distinguishes = (
        c6["full_relation_combined_cap_audit_only"]
        < c5["full_relation_combined_cap_audit_only"]
    )
    c6_extra_cycles_help = (
        c6["full_relation_combined_cap_audit_only"]
        < c6["pseudoforest_combined_cap"]
        and c6["max_full_relation_cycle_rank"] > 1
    )
    result = {
        "artifact_id": "PF5-FULL-RELATION-GRAPH-PROBE-V14.2",
        "status": "POSTHOC_DIAGNOSTIC_COMPLETE",
        "seed": SEED,
        "posthoc_not_holdout": True,
        "producer": producer_identity,
        "prefix_before_first_v4_gap": PREFIX,
        "choice_rows": rows,
        "full_relation_bound_distinguishes_c6_from_c5": full_distinguishes,
        "c6_additional_cycles_explain_some_pseudoforest_overestimate": c6_extra_cycles_help,
        "full_relation_count_is_exponential_audit_only": True,
        "arbitrary_relation_graph_counting_admitted": False,
        "next_gate_if_cycle_rank_bounded": "PROOF_CARRYING_BOUNDED_FEEDBACK_EDGE_RELATION_CAP",
        "next_gate_if_pairwise_insufficient": "HIGHER_ARITY_PROJECTED_CLAUSE_RELATIONS",
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
            "role": "PINNED_V4_POSTHOC_FULL_RELATION_AUDIT",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_FULL_RELATION_GRAPH_PROBE_V14_2 =", result["status"])
    for row in result["choice_rows"]:
        print(
            row["choice"],
            "PSEUDO=", row["pseudoforest_combined_cap"],
            "FULL=", row["full_relation_combined_cap_audit_only"],
            "CYCLE_RANK=", row["max_full_relation_cycle_rank"],
        )
    print("FULL_DISTINGUISHES_C6_FROM_C5 =", result["full_relation_bound_distinguishes_c6_from_c5"])
    print("C6_EXTRA_CYCLES_HELP =", result["c6_additional_cycles_explain_some_pseudoforest_overestimate"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
