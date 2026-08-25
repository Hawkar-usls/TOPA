#!/usr/bin/env python3
"""PF5 Slime v5 logarithmic-feedback residual-gap microscope v15.1.

Post-hoc only on the first already-observed v15 suboptimal holdout, seed 911000.
No new holdout claim is made.

At every frozen v5 choice we compare:
  * v5 full pair-relation feedback status/cap under 4^r <= L^2;
  * the effective v5 cap (v5 when CLOSED, otherwise v4 fallback);
  * v4 pseudoforest cap;
  * exact next PS cut value from the small exponential audit oracle.

This separates residual source-language coarseness from a genuine whole-order /
greedy future obstruction.
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

SEED = 911000
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7
V5 = "SLIME_LOG_FEEDBACK_RELATION_PRESSURE"


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location("janus_slime_v5_1_diag_pin", path)
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
    router = producer.SlimeLogFeedbackCandidateRouter()
    manifest = router.generate_manifest(formula)
    order = next(c.linear_leaf_order for c in manifest.candidates if c.name == V5)
    leaves = sorted(order)
    index = {leaf: i for i, leaf in enumerate(leaves)}
    cut_values, ledger = v11.exact_cut_cache(formula, leaves)
    optimum, optimum_order = v11.exact_optimal_order(leaves, cut_values)
    v5_width = v11.order_width_from_cache(order, index, cut_values)
    assert v5_width == 5 and optimum == 4

    cnf = producer.v1.canonical_cnf(formula)
    selected = set()
    remaining = set(leaves)
    local = []

    for step, chosen in enumerate(order[:-1]):
        candidates = []
        for leaf in sorted(remaining):
            trial = selected | {leaf}
            feedback = producer.log_feedback_relation_signature_cap(cnf, trial)
            pseudo = producer.v4.relation_pseudoforest_signature_cap(cnf, trial)
            closed = feedback["status"] == "CLOSED_POLY_UNDER_FEEDBACK_BUDGET"
            effective = feedback["combined_cap"] if closed else pseudo["combined_cap"]
            exact = cut_values[mask_of(trial, index)]
            candidates.append(
                {
                    "leaf": leaf,
                    "feedback_status": feedback["status"],
                    "feedback_cap": feedback["combined_cap"],
                    "effective_v5_cap": effective,
                    "v4_pseudoforest_cap": pseudo["combined_cap"],
                    "exact_next_ps": exact,
                    "left_cycle_rank": feedback["left"]["cycle_rank"],
                    "right_cycle_rank": feedback["right"]["cycle_rank"],
                    "left_4_pow_r": feedback["left"]["worst_case_4_pow_r"],
                    "right_4_pow_r": feedback["right"]["worst_case_4_pow_r"],
                    "left_budget": feedback["left"]["budget_L_pow_q"],
                    "right_budget": feedback["right"]["budget_L_pow_q"],
                }
            )

        chosen_row = next(row for row in candidates if row["leaf"] == chosen)
        best_exact = min(row["exact_next_ps"] for row in candidates)
        best_effective = min(row["effective_v5_cap"] for row in candidates)
        exact_best_rows = [row for row in candidates if row["exact_next_ps"] == best_exact]
        effective_best_rows = [row for row in candidates if row["effective_v5_cap"] == best_effective]
        hidden = (
            chosen_row["effective_v5_cap"] == best_effective
            and chosen_row["exact_next_ps"] > best_exact
            and any(
                row["effective_v5_cap"] == chosen_row["effective_v5_cap"]
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
                "best_effective_v5_cap": best_effective,
                "best_effective_v5_candidates": effective_best_rows,
                "chosen_exact_local_gap": chosen_row["exact_next_ps"] - best_exact,
                "chosen_effective_cap_gap": chosen_row["effective_v5_cap"] - best_effective,
                "v5_cap_tie_hides_exact_difference": hidden,
            }
        )
        selected.add(chosen)
        remaining.remove(chosen)

    first_local_gap = next((row for row in local if row["chosen_exact_local_gap"] > 0), None)
    first_hidden = next((row for row in local if row["v5_cap_tie_hides_exact_difference"]), None)
    open_steps = [
        row for row in local
        if row["chosen_metrics"]["feedback_status"] == "OPEN_FEEDBACK_BUDGET"
    ]

    def prefix_trace(candidate_order):
        chosen = set()
        rows = []
        for step, leaf in enumerate(candidate_order[:-1]):
            chosen.add(leaf)
            feedback = producer.log_feedback_relation_signature_cap(cnf, chosen)
            pseudo = producer.v4.relation_pseudoforest_signature_cap(cnf, chosen)
            closed = feedback["status"] == "CLOSED_POLY_UNDER_FEEDBACK_BUDGET"
            rows.append(
                {
                    "step": step,
                    "added": leaf,
                    "feedback_status": feedback["status"],
                    "effective_v5_cap": feedback["combined_cap"] if closed else pseudo["combined_cap"],
                    "exact_ps_cut": cut_values[mask_of(chosen, index)],
                    "max_cycle_rank": max(
                        feedback["left"]["cycle_rank"],
                        feedback["right"]["cycle_rank"],
                    ),
                }
            )
        return rows

    v5_trace = prefix_trace(order)
    optimal_trace = prefix_trace(optimum_order)
    result = {
        "artifact_id": "PF5-SLIME-LOG-FEEDBACK-GAP-MICROSCOPE-V15.1",
        "status": "POSTHOC_DIAGNOSTIC_COMPLETE",
        "seed": SEED,
        "posthoc_not_holdout": True,
        "producer": producer_identity,
        "formula": [list(c) for c in formula],
        "v5_order": order,
        "exact_optimal_order": optimum_order,
        "v5_width": v5_width,
        "exact_optimal_width": optimum,
        "optimality_gap": v5_width - optimum,
        "local_choice_diagnostics": local,
        "first_exact_local_gap": first_local_gap,
        "first_v5_cap_tie_failure": first_hidden,
        "chosen_path_open_feedback_steps": open_steps,
        "chosen_path_open_feedback_step_count": len(open_steps),
        "v5_prefix_trace": v5_trace,
        "optimal_prefix_trace": optimal_trace,
        "worst_v5_prefix": max(v5_trace, key=lambda row: row["exact_ps_cut"]),
        "worst_optimal_prefix": max(optimal_trace, key=lambda row: row["exact_ps_cut"]),
        "diagnostic_split": {
            "V5_SURROGATE_STILL_TOO_COARSE": first_hidden is not None,
            "HAS_ANY_LOCAL_EXACT_MISSTEP": first_local_gap is not None,
            "PURE_GREEDY_FUTURE_OBSTRUCTION_IF_NO_LOCAL_MISSTEP": first_local_gap is None,
            "FEEDBACK_BUDGET_OPEN_ON_CHOSEN_PATH": bool(open_steps),
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
            "role": "PINNED_V5_1_POSTHOC_DIAGNOSTIC",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_SLIME_LOG_FEEDBACK_GAP_MICROSCOPE_V15_1 =", result["status"])
    print("FORMULA =", result["formula"])
    print("V5_ORDER =", result["v5_order"])
    print("OPTIMAL_ORDER =", result["exact_optimal_order"])
    print("WIDTHS =", result["v5_width"], result["exact_optimal_width"])
    print("FIRST_EXACT_LOCAL_GAP =", result["first_exact_local_gap"])
    print("FIRST_V5_CAP_TIE_FAILURE =", result["first_v5_cap_tie_failure"])
    print("OPEN_FEEDBACK_STEPS =", result["chosen_path_open_feedback_step_count"])
    print("DIAGNOSTIC_SPLIT =", result["diagnostic_split"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
