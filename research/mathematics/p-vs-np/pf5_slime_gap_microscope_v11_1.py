#!/usr/bin/env python3
"""PF5 Slime gap microscope v11.1.

Post-hoc diagnostic only for the already-observed v11 counterexample seed 907000.
No new holdout claim is made.  The script compares the frozen Slime order with
the exact-optimal caterpillar order and asks where source-only graph pressure
diverges from exact PS-state pressure.
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

DIAGNOSTIC_SEED = 907000


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_semantic_candidate_router_pin_v11_1", path
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


def source_feature_state(producer, formula):
    cnf = producer.canonical_cnf(formula)
    groups, clause_to_group = producer.clause_group_map(cnf)
    profiles = producer.variable_profiles(cnf, clause_to_group)
    adjacency = producer.incidence(cnf)
    unique_profiles = sorted(set(profiles.values()))
    profile_ids = {profile: index for index, profile in enumerate(unique_profiles)}
    leaf_group = {}
    for variable, profile in profiles.items():
        leaf_group[f"v:{variable}"] = f"VP:{profile_ids[profile]}"
    for clause_index, group_id in clause_to_group.items():
        leaf_group[f"c:{clause_index}"] = f"CG:{group_id}"
    return cnf, groups, profiles, adjacency, leaf_group


def graph_metrics(adjacency, leaf_group, selected):
    crossing = 0
    frontier_pairs = set()
    for left in selected:
        for right in adjacency[left]:
            if right not in selected:
                crossing += 1
                frontier_pairs.add((leaf_group[left], leaf_group[right]))
    return {
        "incidence_crossing_edges": crossing,
        "certified_group_frontier_pairs": len(frontier_pairs),
    }


def mask_of(selected, leaf_index):
    mask = 0
    for leaf in selected:
        mask |= 1 << leaf_index[leaf]
    return mask


def prefix_trace(order, leaf_index, cut_values, adjacency, leaf_group):
    selected = set()
    rows = []
    for step, leaf in enumerate(order[:-1]):
        selected.add(leaf)
        mask = mask_of(selected, leaf_index)
        row = {
            "step": step,
            "added": leaf,
            "selected": sorted(selected),
            "exact_ps_cut": cut_values[mask],
        }
        row.update(graph_metrics(adjacency, leaf_group, selected))
        rows.append(row)
    return rows


def local_choice_diagnostics(order, leaves, leaf_index, cut_values, adjacency, leaf_group):
    selected = set()
    remaining = set(leaves)
    rows = []
    for step, chosen in enumerate(order[:-1]):
        candidates = []
        for leaf in sorted(remaining):
            trial = selected | {leaf}
            mask = mask_of(trial, leaf_index)
            metrics = graph_metrics(adjacency, leaf_group, trial)
            candidates.append(
                {
                    "leaf": leaf,
                    "exact_next_ps": cut_values[mask],
                    **metrics,
                }
            )
        exact_best_value = min(x["exact_next_ps"] for x in candidates)
        exact_best = [x for x in candidates if x["exact_next_ps"] == exact_best_value]
        chosen_row = next(x for x in candidates if x["leaf"] == chosen)
        rows.append(
            {
                "step": step,
                "chosen": chosen,
                "chosen_metrics": chosen_row,
                "exact_best_next_ps": exact_best_value,
                "exact_best_candidates": exact_best,
                "local_exact_gap": chosen_row["exact_next_ps"] - exact_best_value,
            }
        )
        selected.add(chosen)
        remaining.remove(chosen)
    return rows


def run(producer, producer_identity):
    formula = v9.random_connected_3cnf(
        DIAGNOSTIC_SEED, variable_count=v11.VARIABLE_COUNT, clause_count=v11.CLAUSE_COUNT
    )
    router = producer.SlimeSemanticCandidateRouter()
    manifest = router.generate_manifest(formula)
    slime_order = next(
        c.linear_leaf_order for c in manifest.candidates
        if c.name == "SLIME_SEMANTIC_PRESSURE"
    )
    leaves = sorted(slime_order)
    leaf_index = {leaf: i for i, leaf in enumerate(leaves)}
    cut_values, ledger = v11.exact_cut_cache(formula, leaves)
    optimum, optimum_order = v11.exact_optimal_order(leaves, cut_values)
    slime_width = v11.order_width_from_cache(slime_order, leaf_index, cut_values)
    assert slime_width == 6 and optimum == 4

    cnf, groups, profiles, adjacency, leaf_group = source_feature_state(producer, formula)
    slime_trace = prefix_trace(
        slime_order, leaf_index, cut_values, adjacency, leaf_group
    )
    optimum_trace = prefix_trace(
        optimum_order, leaf_index, cut_values, adjacency, leaf_group
    )
    local = local_choice_diagnostics(
        slime_order, leaves, leaf_index, cut_values, adjacency, leaf_group
    )
    first_local_gap = next((row for row in local if row["local_exact_gap"] > 0), None)
    worst_slime = max(slime_trace, key=lambda row: row["exact_ps_cut"])
    worst_optimum = max(optimum_trace, key=lambda row: row["exact_ps_cut"])

    result = {
        "artifact_id": "PF5-SLIME-GAP-MICROSCOPE-V11.1",
        "status": "POSTHOC_DIAGNOSTIC_COMPLETE",
        "seed": DIAGNOSTIC_SEED,
        "posthoc_not_holdout": True,
        "producer": producer_identity,
        "formula": [list(c) for c in formula],
        "source_features": {
            "clause_groups": groups,
            "variable_profiles": {
                str(v): [list(x) for x in profiles[v]] for v in sorted(profiles)
            },
        },
        "slime_order": slime_order,
        "exact_optimal_order": optimum_order,
        "slime_width": slime_width,
        "exact_optimal_width": optimum,
        "optimality_gap": slime_width - optimum,
        "slime_prefix_trace": slime_trace,
        "optimal_prefix_trace": optimum_trace,
        "slime_local_choice_diagnostics": local,
        "first_local_exact_gap": first_local_gap,
        "worst_slime_prefix": worst_slime,
        "worst_optimal_prefix": worst_optimum,
        "exact_verifier_ledger": ledger,
        "diagnostic_question": (
            "Which assignment-independent source feature predicts exact PS-state "
            "growth missed by incidence crossing and certified-group frontier pressure?"
        ),
        "candidate_feature_families_not_yet_admitted": [
            "SIGNED_CLAUSE_OVERLAP_NEIGHBORHOOD",
            "TWO_STEP_INCIDENCE_MOTIF",
            "LOCAL_RESIDUAL_MESSAGE_SKETCH_WITH_PROOF",
        ],
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
            "role": "FROZEN_EXTERNAL_PRODUCER",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_SLIME_GAP_MICROSCOPE_V11_1 =", result["status"])
    print("FORMULA =", result["formula"])
    print("SLIME_ORDER =", result["slime_order"])
    print("OPTIMAL_ORDER =", result["exact_optimal_order"])
    print("WIDTHS =", result["slime_width"], result["exact_optimal_width"])
    print("FIRST_LOCAL_EXACT_GAP =", result["first_local_exact_gap"])
    print("WORST_SLIME_PREFIX =", result["worst_slime_prefix"])
    print("WORST_OPTIMAL_PREFIX =", result["worst_optimal_prefix"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
