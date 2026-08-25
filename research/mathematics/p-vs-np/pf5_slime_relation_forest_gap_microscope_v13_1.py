#!/usr/bin/env python3
"""PF5 Slime v3 relation-forest residual-gap microscope v13.1.

Post-hoc only on the first already-observed v13 suboptimal holdout, seed 909002.
No new holdout claim is made. The script compares the frozen v3 order with the
exact-optimal caterpillar order and, at every v3 choice, compares the source-only
relation-forest signature cap to the exact next PS value.
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

SEED = 909002
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7
V3 = "SLIME_RELATION_FOREST_PRESSURE"


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location("janus_slime_v3_diag_pin", path)
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


def mask_of(selected, index):
    mask = 0
    for leaf in selected:
        mask |= 1 << index[leaf]
    return mask


def run(producer, producer_identity):
    formula = v9.random_connected_3cnf(SEED, VARIABLE_COUNT, CLAUSE_COUNT)
    router = producer.SlimeRelationForestCandidateRouter()
    manifest = router.generate_manifest(formula)
    v3_order = next(c.linear_leaf_order for c in manifest.candidates if c.name == V3)
    leaves = sorted(v3_order)
    index = {leaf: i for i, leaf in enumerate(leaves)}
    cut_values, ledger = v11.exact_cut_cache(formula, leaves)
    optimum, optimum_order = v11.exact_optimal_order(leaves, cut_values)
    v3_width = v11.order_width_from_cache(v3_order, index, cut_values)
    assert v3_width == 5 and optimum == 4

    cnf = producer.v1.canonical_cnf(formula)
    selected = set()
    remaining = set(leaves)
    local = []
    for step, chosen in enumerate(v3_order[:-1]):
        candidates = []
        for leaf in sorted(remaining):
            trial = selected | {leaf}
            rel = producer.relation_forest_signature_cap(cnf, trial)
            old = producer.v2.signature_cap_exponent(cnf, trial)
            exact = cut_values[mask_of(trial, index)]
            candidates.append(
                {
                    "leaf": leaf,
                    "relation_forest_cap": rel["combined_cap"],
                    "v2_signature_cap_log2": old["cap_log2"],
                    "exact_next_ps": exact,
                    "left_relation_cap": rel["left"]["certified_signature_cap"],
                    "right_relation_cap": rel["right"]["certified_signature_cap"],
                    "left_relation_edges": rel["left"]["relation_edge_count"],
                    "right_relation_edges": rel["right"]["relation_edge_count"],
                }
            )
        chosen_row = next(x for x in candidates if x["leaf"] == chosen)
        best_exact = min(x["exact_next_ps"] for x in candidates)
        best_rel = min(x["relation_forest_cap"] for x in candidates)
        local.append(
            {
                "step": step,
                "chosen": chosen,
                "chosen_metrics": chosen_row,
                "best_exact_next_ps": best_exact,
                "best_exact_candidates": [x for x in candidates if x["exact_next_ps"] == best_exact],
                "best_relation_cap": best_rel,
                "best_relation_candidates": [x for x in candidates if x["relation_forest_cap"] == best_rel],
                "chosen_exact_local_gap": chosen_row["exact_next_ps"] - best_exact,
                "chosen_relation_cap_gap": chosen_row["relation_forest_cap"] - best_rel,
                "relation_cap_tie_hides_exact_difference": (
                    chosen_row["relation_forest_cap"] == best_rel
                    and chosen_row["exact_next_ps"] > best_exact
                    and any(
                        x["relation_forest_cap"] == chosen_row["relation_forest_cap"]
                        and x["exact_next_ps"] < chosen_row["exact_next_ps"]
                        for x in candidates
                    )
                ),
            }
        )
        selected.add(chosen)
        remaining.remove(chosen)

    first_local_gap = next((x for x in local if x["chosen_exact_local_gap"] > 0), None)
    first_hidden = next((x for x in local if x["relation_cap_tie_hides_exact_difference"]), None)

    def prefix_trace(order):
        chosen = set()
        rows = []
        for step, leaf in enumerate(order[:-1]):
            chosen.add(leaf)
            rel = producer.relation_forest_signature_cap(cnf, chosen)
            rows.append(
                {
                    "step": step,
                    "added": leaf,
                    "relation_forest_cap": rel["combined_cap"],
                    "exact_ps_cut": cut_values[mask_of(chosen, index)],
                }
            )
        return rows

    v3_trace = prefix_trace(v3_order)
    opt_trace = prefix_trace(optimum_order)
    result = {
        "artifact_id": "PF5-SLIME-RELATION-FOREST-GAP-MICROSCOPE-V13.1",
        "status": "POSTHOC_DIAGNOSTIC_COMPLETE",
        "seed": SEED,
        "posthoc_not_holdout": True,
        "producer": producer_identity,
        "formula": [list(c) for c in formula],
        "v3_order": v3_order,
        "exact_optimal_order": optimum_order,
        "v3_width": v3_width,
        "exact_optimal_width": optimum,
        "optimality_gap": v3_width - optimum,
        "local_choice_diagnostics": local,
        "first_exact_local_gap": first_local_gap,
        "first_relation_cap_tie_failure": first_hidden,
        "v3_prefix_trace": v3_trace,
        "optimal_prefix_trace": opt_trace,
        "worst_v3_prefix": max(v3_trace, key=lambda x: x["exact_ps_cut"]),
        "worst_optimal_prefix": max(opt_trace, key=lambda x: x["exact_ps_cut"]),
        "diagnostic_split": {
            "RELATION_FOREST_SURROGATE_STILL_TOO_COARSE": first_hidden is not None,
            "GREEDY_LOOKAHEAD_REMAINS_POSSIBLE_OBSTRUCTION": True,
        },
        "exact_verifier_ledger": ledger,
        "next_feature_or_search_rule_must_be_source_only": True,
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
            "role": "PINNED_V3_POSTHOC_DIAGNOSTIC",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_SLIME_RELATION_FOREST_GAP_MICROSCOPE_V13_1 =", result["status"])
    print("FORMULA =", result["formula"])
    print("V3_ORDER =", result["v3_order"])
    print("OPTIMAL_ORDER =", result["exact_optimal_order"])
    print("WIDTHS =", result["v3_width"], result["exact_optimal_width"])
    print("FIRST_EXACT_LOCAL_GAP =", result["first_exact_local_gap"])
    print("FIRST_RELATION_CAP_TIE_FAILURE =", result["first_relation_cap_tie_failure"])
    print("DIAGNOSTIC_SPLIT =", result["diagnostic_split"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
