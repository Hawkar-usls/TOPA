#!/usr/bin/env python3
"""PF5 Slime v4 pseudoforest residual-gap microscope v14.1.

Post-hoc only on the first already-observed v14 suboptimal holdout, seed 910000.
No new holdout claim is made. At every frozen v4 choice, compare the source-only
pseudoforest cap, v3 forest cap, v2 coarse cap, and exact next PS cut value. This
separates two failure modes:

1. SURROGATE_TOO_COARSE: the chosen v4 candidate ties/wins on source-only cap but
   another candidate has a smaller exact next PS value;
2. GREEDY_FUTURE_OBSTRUCTION: every local exact choice is minimal, yet the final
   order still misses the exact optimal caterpillar width.
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

SEED = 910000
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7
V4 = "SLIME_RELATION_PSEUDOFOREST_PRESSURE"


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location("janus_slime_v4_diag_pin", path)
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
    router = producer.SlimeRelationPseudoforestCandidateRouter()
    manifest = router.generate_manifest(formula)
    order = next(c.linear_leaf_order for c in manifest.candidates if c.name == V4)
    leaves = sorted(order)
    index = {leaf: i for i, leaf in enumerate(leaves)}
    cut_values, ledger = v11.exact_cut_cache(formula, leaves)
    optimum, optimum_order = v11.exact_optimal_order(leaves, cut_values)
    v4_width = v11.order_width_from_cache(order, index, cut_values)
    assert v4_width == 6 and optimum == 4

    cnf = producer.v1.canonical_cnf(formula)
    selected = set()
    remaining = set(leaves)
    local = []

    for step, chosen in enumerate(order[:-1]):
        candidates = []
        for leaf in sorted(remaining):
            trial = selected | {leaf}
            pseudo = producer.relation_pseudoforest_signature_cap(cnf, trial)
            forest = producer.v3.relation_forest_signature_cap(cnf, trial)
            coarse = producer.v2.signature_cap_exponent(cnf, trial)
            exact = cut_values[mask_of(trial, index)]
            candidates.append(
                {
                    "leaf": leaf,
                    "pseudoforest_cap": pseudo["combined_cap"],
                    "forest_cap": forest["combined_cap"],
                    "v2_cap_log2": coarse["cap_log2"],
                    "exact_next_ps": exact,
                    "left_pseudoforest_cap": pseudo["left"]["certified_signature_cap"],
                    "right_pseudoforest_cap": pseudo["right"]["certified_signature_cap"],
                    "left_unicyclic_components": pseudo["left"]["unicyclic_components"],
                    "right_unicyclic_components": pseudo["right"]["unicyclic_components"],
                }
            )

        chosen_row = next(row for row in candidates if row["leaf"] == chosen)
        best_exact = min(row["exact_next_ps"] for row in candidates)
        best_pseudo = min(row["pseudoforest_cap"] for row in candidates)
        exact_best_rows = [row for row in candidates if row["exact_next_ps"] == best_exact]
        pseudo_best_rows = [row for row in candidates if row["pseudoforest_cap"] == best_pseudo]
        hidden = (
            chosen_row["pseudoforest_cap"] == best_pseudo
            and chosen_row["exact_next_ps"] > best_exact
            and any(
                row["pseudoforest_cap"] == chosen_row["pseudoforest_cap"]
                and row["exact_next_ps"] < chosen_row["exact_next_ps"]
                for row in candidates
            )
        )
        local.append(
            {
                "step": step,
                "chosen": chosen,
                "chosen_metrics": chosen_row,
                "best_exact_next_ps": best_exact,
                "best_exact_candidates": exact_best_rows,
                "best_pseudoforest_cap": best_pseudo,
                "best_pseudoforest_candidates": pseudo_best_rows,
                "chosen_exact_local_gap": chosen_row["exact_next_ps"] - best_exact,
                "chosen_pseudoforest_cap_gap": chosen_row["pseudoforest_cap"] - best_pseudo,
                "pseudoforest_cap_tie_hides_exact_difference": hidden,
            }
        )
        selected.add(chosen)
        remaining.remove(chosen)

    first_local_gap = next((row for row in local if row["chosen_exact_local_gap"] > 0), None)
    first_hidden = next((row for row in local if row["pseudoforest_cap_tie_hides_exact_difference"]), None)

    def prefix_trace(candidate_order):
        chosen = set()
        rows = []
        for step, leaf in enumerate(candidate_order[:-1]):
            chosen.add(leaf)
            pseudo = producer.relation_pseudoforest_signature_cap(cnf, chosen)
            rows.append(
                {
                    "step": step,
                    "added": leaf,
                    "pseudoforest_cap": pseudo["combined_cap"],
                    "exact_ps_cut": cut_values[mask_of(chosen, index)],
                    "unicyclic_components_total": (
                        pseudo["left"]["unicyclic_components"]
                        + pseudo["right"]["unicyclic_components"]
                    ),
                }
            )
        return rows

    v4_trace = prefix_trace(order)
    optimal_trace = prefix_trace(optimum_order)
    result = {
        "artifact_id": "PF5-SLIME-PSEUDOFOREST-GAP-MICROSCOPE-V14.1",
        "status": "POSTHOC_DIAGNOSTIC_COMPLETE",
        "seed": SEED,
        "posthoc_not_holdout": True,
        "producer": producer_identity,
        "formula": [list(c) for c in formula],
        "v4_order": order,
        "exact_optimal_order": optimum_order,
        "v4_width": v4_width,
        "exact_optimal_width": optimum,
        "optimality_gap": v4_width - optimum,
        "local_choice_diagnostics": local,
        "first_exact_local_gap": first_local_gap,
        "first_pseudoforest_cap_tie_failure": first_hidden,
        "v4_prefix_trace": v4_trace,
        "optimal_prefix_trace": optimal_trace,
        "worst_v4_prefix": max(v4_trace, key=lambda row: row["exact_ps_cut"]),
        "worst_optimal_prefix": max(optimal_trace, key=lambda row: row["exact_ps_cut"]),
        "diagnostic_split": {
            "PSEUDOFOREST_SURROGATE_STILL_TOO_COARSE": first_hidden is not None,
            "HAS_ANY_LOCAL_EXACT_MISSTEP": first_local_gap is not None,
            "PURE_GREEDY_FUTURE_OBSTRUCTION_IF_NO_LOCAL_MISSTEP": first_local_gap is None,
        },
        "exact_verifier_ledger": ledger,
        "next_feature_or_search_rule_must_be_source_only": True,
        "arbitrary_relation_graph_counting_admitted": False,
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
            "role": "PINNED_V4_POSTHOC_DIAGNOSTIC",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_SLIME_PSEUDOFOREST_GAP_MICROSCOPE_V14_1 =", result["status"])
    print("FORMULA =", result["formula"])
    print("V4_ORDER =", result["v4_order"])
    print("OPTIMAL_ORDER =", result["exact_optimal_order"])
    print("WIDTHS =", result["v4_width"], result["exact_optimal_width"])
    print("FIRST_EXACT_LOCAL_GAP =", result["first_exact_local_gap"])
    print("FIRST_PSEUDOFOREST_CAP_TIE_FAILURE =", result["first_pseudoforest_cap_tie_failure"])
    print("DIAGNOSTIC_SPLIT =", result["diagnostic_split"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
