#!/usr/bin/env python3
"""PF5 Slime signature-cap gap microscope v12.1.

Post-hoc diagnostic for the first already-observed blind-v12 suboptimal source,
seed 908001.  This is not a new holdout.  It compares the frozen v2 signature-
cap candidate against the exact optimal caterpillar order and records both
source-only surrogate values and exact PS cut values at every local choice.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_slime_exact_optimality_gap_v11 as v11

SEED = 908001
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7
NEW = "SLIME_SIGNATURE_CAP_PRESSURE"


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_signature_cap_router_v2_pin_diag", path
    )
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


def source_state(producer, formula):
    cnf = producer.v1.canonical_cnf(formula)
    groups, clause_to_group = producer.v1.clause_group_map(cnf)
    profiles = producer.v1.variable_profiles(cnf, clause_to_group)
    adjacency = producer.v1.incidence(cnf)
    unique_profiles = sorted(set(profiles.values()))
    profile_ids = {profile: index for index, profile in enumerate(unique_profiles)}
    leaf_group = {}
    for variable, profile in profiles.items():
        leaf_group[f"v:{variable}"] = f"VP:{profile_ids[profile]}"
    for clause_index, group_id in clause_to_group.items():
        leaf_group[f"c:{clause_index}"] = f"CG:{group_id}"
    return cnf, adjacency, leaf_group


def graph_metrics(producer, adjacency, leaf_group, selected):
    return {
        "semantic_frontier_pairs": producer.v1.SlimeSemanticCandidateRouter._semantic_frontier(
            adjacency, selected, leaf_group
        ),
        "incidence_crossing_edges": producer.v1.SlimeSemanticCandidateRouter._crossing(
            adjacency, selected
        ),
    }


def mask_of(selected, leaf_index):
    mask = 0
    for leaf in selected:
        mask |= 1 << leaf_index[leaf]
    return mask


def candidate_row(producer, cnf, adjacency, leaf_group, trial, leaf, leaf_index, cut_values):
    cap = producer.signature_cap_exponent(cnf, trial)
    graph = graph_metrics(producer, adjacency, leaf_group, trial)
    return {
        "leaf": leaf,
        "signature_cap_log2": cap["cap_log2"],
        "signature_cap_left_log2": cap["left_log2"],
        "signature_cap_right_log2": cap["right_log2"],
        "exact_next_ps": cut_values[mask_of(trial, leaf_index)],
        **graph,
    }


def local_diagnostics(producer, cnf, order, leaves, leaf_index, cut_values, adjacency, leaf_group):
    selected = set()
    remaining = set(leaves)
    rows = []
    for step, chosen in enumerate(order[:-1]):
        candidates = [
            candidate_row(
                producer,
                cnf,
                adjacency,
                leaf_group,
                selected | {leaf},
                leaf,
                leaf_index,
                cut_values,
            )
            for leaf in sorted(remaining)
        ]
        chosen_row = next(row for row in candidates if row["leaf"] == chosen)
        exact_best = min(row["exact_next_ps"] for row in candidates)
        cap_best = min(row["signature_cap_log2"] for row in candidates)
        exact_best_rows = [row for row in candidates if row["exact_next_ps"] == exact_best]
        cap_best_rows = [row for row in candidates if row["signature_cap_log2"] == cap_best]
        rows.append(
            {
                "step": step,
                "chosen": chosen,
                "chosen_metrics": chosen_row,
                "exact_best_next_ps": exact_best,
                "exact_best_candidates": exact_best_rows,
                "cap_best_log2": cap_best,
                "cap_best_candidates": cap_best_rows,
                "chosen_exact_local_gap": chosen_row["exact_next_ps"] - exact_best,
                "chosen_cap_local_gap": chosen_row["signature_cap_log2"] - cap_best,
                "cap_tie_hides_exact_difference": (
                    chosen_row["signature_cap_log2"] == cap_best
                    and chosen_row["exact_next_ps"] > exact_best
                    and any(
                        row["signature_cap_log2"] == chosen_row["signature_cap_log2"]
                        and row["exact_next_ps"] < chosen_row["exact_next_ps"]
                        for row in candidates
                    )
                ),
            }
        )
        selected.add(chosen)
        remaining.remove(chosen)
    return rows


def prefix_trace(producer, cnf, order, leaf_index, cut_values, adjacency, leaf_group):
    selected = set()
    rows = []
    for step, leaf in enumerate(order[:-1]):
        selected.add(leaf)
        row = {
            "step": step,
            "added": leaf,
            "exact_ps_cut": cut_values[mask_of(selected, leaf_index)],
            "signature_cap": producer.signature_cap_exponent(cnf, selected),
        }
        row.update(graph_metrics(producer, adjacency, leaf_group, selected))
        rows.append(row)
    return rows


def run(producer, producer_identity):
    formula = v9.random_connected_3cnf(SEED, VARIABLE_COUNT, CLAUSE_COUNT)
    router = producer.SlimeSignatureCapCandidateRouter()
    manifest = router.generate_manifest(formula)
    new_order = next(c.linear_leaf_order for c in manifest.candidates if c.name == NEW)
    leaves = sorted(new_order)
    leaf_index = {leaf: i for i, leaf in enumerate(leaves)}
    cut_values, ledger = v11.exact_cut_cache(formula, leaves)
    optimum, optimum_order = v11.exact_optimal_order(leaves, cut_values)
    new_width = v11.order_width_from_cache(new_order, leaf_index, cut_values)
    assert new_width == 6 and optimum == 4

    cnf, adjacency, leaf_group = source_state(producer, formula)
    local = local_diagnostics(
        producer, cnf, new_order, leaves, leaf_index, cut_values, adjacency, leaf_group
    )
    first_exact_gap = next((row for row in local if row["chosen_exact_local_gap"] > 0), None)
    first_cap_tie_failure = next((row for row in local if row["cap_tie_hides_exact_difference"]), None)
    new_trace = prefix_trace(producer, cnf, new_order, leaf_index, cut_values, adjacency, leaf_group)
    opt_trace = prefix_trace(producer, cnf, optimum_order, leaf_index, cut_values, adjacency, leaf_group)

    result = {
        "artifact_id": "PF5-SLIME-SIGNATURE-CAP-GAP-MICROSCOPE-V12.1",
        "status": "POSTHOC_DIAGNOSTIC_COMPLETE",
        "seed": SEED,
        "posthoc_not_holdout": True,
        "producer": producer_identity,
        "formula": [list(c) for c in formula],
        "new_order": new_order,
        "exact_optimal_order": optimum_order,
        "new_width": new_width,
        "exact_optimal_width": optimum,
        "optimality_gap": new_width - optimum,
        "local_choice_diagnostics": local,
        "first_exact_local_gap": first_exact_gap,
        "first_signature_cap_tie_failure": first_cap_tie_failure,
        "new_prefix_trace": new_trace,
        "optimal_prefix_trace": opt_trace,
        "worst_new_prefix": max(new_trace, key=lambda row: row["exact_ps_cut"]),
        "worst_optimal_prefix": max(opt_trace, key=lambda row: row["exact_ps_cut"]),
        "exact_verifier_ledger": ledger,
        "diagnostic_split": {
            "SURROGATE_TOO_COARSE": first_cap_tie_failure is not None,
            "LOCAL_GREEDY_MAY_STILL_BE_NONOPTIMAL": True,
        },
        "next_feature_must_be_source_only": True,
        "p_vs_np": "OPEN",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-path", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    raw = args.producer_path.read_bytes()
    producer = import_producer(args.producer_path)
    result = run(
        producer,
        {
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "PINNED_V2_POSTHOC_DIAGNOSTIC",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_SLIME_SIGNATURE_CAP_GAP_MICROSCOPE_V12_1 =", result["status"])
    print("FORMULA =", result["formula"])
    print("NEW_ORDER =", result["new_order"])
    print("OPTIMAL_ORDER =", result["exact_optimal_order"])
    print("WIDTHS =", result["new_width"], result["exact_optimal_width"])
    print("FIRST_EXACT_LOCAL_GAP =", result["first_exact_local_gap"])
    print("FIRST_SIGNATURE_CAP_TIE_FAILURE =", result["first_signature_cap_tie_failure"])
    print("WORST_NEW_PREFIX =", result["worst_new_prefix"])
    print("WORST_OPTIMAL_PREFIX =", result["worst_optimal_prefix"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
