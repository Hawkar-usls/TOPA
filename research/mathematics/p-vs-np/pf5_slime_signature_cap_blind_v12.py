#!/usr/bin/env python3
"""PF5 Slime signature-cap blind validation v12.

Calibration seed 907000 was already observed in v11/v11.1 and is reported only
as a training diagnostic.  Fresh holdout seeds 908000..908015 are frozen before
provider execution.  The pinned Janus-Demiurge v2 producer receives raw CNF and
emits both the old Slime semantic-pressure candidate and the new proof-carrying
signature-cap candidate.  TOPA freezes all manifests before invoking the exact
small-instance subset-DP caterpillar PS-width judge.

The exact judge is exponential and is an audit oracle only, never the claimed
runtime algorithm.
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

CALIBRATION_SEED = 907000
FROZEN_HOLDOUT_SEEDS = list(range(908000, 908016))
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7
OLD = "SLIME_SEMANTIC_PRESSURE"
NEW = "SLIME_SIGNATURE_CAP_PRESSURE"


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_signature_cap_router_v2_pin", path
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


def build_sources():
    rows = [
        (
            "CALIBRATION_907000_ALREADY_OBSERVED",
            "CALIBRATION_POSTHOC",
            CALIBRATION_SEED,
            v9.random_connected_3cnf(
                CALIBRATION_SEED,
                variable_count=VARIABLE_COUNT,
                clause_count=CLAUSE_COUNT,
            ),
        )
    ]
    for seed in FROZEN_HOLDOUT_SEEDS:
        rows.append(
            (
                f"BLIND_{seed}",
                "BLIND_HOLDOUT",
                seed,
                v9.random_connected_3cnf(
                    seed,
                    variable_count=VARIABLE_COUNT,
                    clause_count=CLAUSE_COUNT,
                ),
            )
        )
    return rows


def run(router_class, producer_identity):
    router = router_class()

    # Phase 1: freeze every source and complete five-candidate manifest before
    # any exact cut value or optimum is computed.
    frozen = []
    total_generation_ops = 0
    for fixture, phase, seed, formula in build_sources():
        manifest = router.generate_manifest(formula)
        assert manifest.frozen_before_probe is True
        assert manifest.exact_ps_width_computed_inside_generator is False
        assert manifest.sat_oracle_used is False
        candidate_names = [candidate.name for candidate in manifest.candidates]
        assert OLD in candidate_names and NEW in candidate_names
        total_generation_ops += manifest.total_generation_ops
        frozen.append(
            {
                "fixture": fixture,
                "phase": phase,
                "seed": seed,
                "formula": [list(c) for c in formula],
                "manifest": manifest.to_dict(),
            }
        )

    batch = [
        (
            item["fixture"],
            item["manifest"]["source_sha256"],
            item["manifest"]["manifest_sha256"],
        )
        for item in frozen
    ]
    manifest_batch_sha256 = hashlib.sha256(
        json.dumps(batch, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    # Phase 2: independent exponential exact audit.
    totals = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    results = []
    for item in frozen:
        formula = tuple(tuple(c) for c in item["formula"])
        manifest = item["manifest"]
        leaves = sorted(manifest["candidates"][0]["linear_leaf_order"])
        leaf_index = {leaf: i for i, leaf in enumerate(leaves)}
        cut_values, ledger = v11.exact_cut_cache(formula, leaves)
        for key in totals:
            totals[key] += ledger[key]

        optimum, optimum_order = v11.exact_optimal_order(leaves, cut_values)
        assert v11.order_width_from_cache(optimum_order, leaf_index, cut_values) == optimum

        widths = {}
        for candidate in manifest["candidates"]:
            widths[candidate["name"]] = v11.order_width_from_cache(
                candidate["linear_leaf_order"], leaf_index, cut_values
            )
        old_width = widths[OLD]
        new_width = widths[NEW]
        results.append(
            {
                "fixture": item["fixture"],
                "phase": item["phase"],
                "seed": item["seed"],
                "source_sha256": manifest["source_sha256"],
                "manifest_sha256": manifest["manifest_sha256"],
                "candidate_widths": widths,
                "old_slime_width": old_width,
                "new_slime_width": new_width,
                "exact_optimal_width": optimum,
                "old_gap": old_width - optimum,
                "new_gap": new_width - optimum,
                "delta_new_minus_old": new_width - old_width,
                "new_vs_old": (
                    "WIN" if new_width < old_width
                    else "TIE" if new_width == old_width
                    else "LOSS"
                ),
                "new_is_exact_optimal": new_width == optimum,
                "exact_optimal_order": optimum_order,
                "formula": item["formula"],
            }
        )

    calibration = next(row for row in results if row["phase"] == "CALIBRATION_POSTHOC")
    holdout = [row for row in results if row["phase"] == "BLIND_HOLDOUT"]

    def count(label):
        return sum(row["new_vs_old"] == label for row in holdout)

    summary = {
        "holdout_cases": len(holdout),
        "new_vs_old_wins": count("WIN"),
        "new_vs_old_ties": count("TIE"),
        "new_vs_old_losses": count("LOSS"),
        "new_exact_optimal_cases": sum(row["new_is_exact_optimal"] for row in holdout),
        "old_exact_optimal_cases": sum(row["old_gap"] == 0 for row in holdout),
        "mean_old_width": sum(row["old_slime_width"] for row in holdout) / len(holdout),
        "mean_new_width": sum(row["new_slime_width"] for row in holdout) / len(holdout),
        "mean_optimal_width": sum(row["exact_optimal_width"] for row in holdout) / len(holdout),
        "mean_old_gap": sum(row["old_gap"] for row in holdout) / len(holdout),
        "mean_new_gap": sum(row["new_gap"] for row in holdout) / len(holdout),
        "max_new_gap": max(row["new_gap"] for row in holdout),
        "first_new_loss_seed": next(
            (row["seed"] for row in holdout if row["new_vs_old"] == "LOSS"), None
        ),
        "first_new_suboptimal_seed": next(
            (row["seed"] for row in holdout if not row["new_is_exact_optimal"]), None
        ),
    }

    result = {
        "artifact_id": "PF5-SLIME-SIGNATURE-CAP-BLIND-V12",
        "status": "FINITE_BLIND_EXACT_OPTIMUM_AUDIT_COMPLETE",
        "producer": producer_identity,
        "producer_feature": "LOG_SIGNATURE_CAP_UPPER_BOUND",
        "calibration_seed_already_observed": CALIBRATION_SEED,
        "calibration_excluded_from_holdout_summary": True,
        "holdout_seeds_frozen_before_provider_run": FROZEN_HOLDOUT_SEEDS,
        "variable_count": VARIABLE_COUNT,
        "clause_count": CLAUSE_COUNT,
        "all_sources_and_manifests_frozen_before_exact_dp": True,
        "adaptive_candidate_generation_after_exact_dp": False,
        "manifest_batch_sha256": manifest_batch_sha256,
        "calibration": calibration,
        "holdout_summary": summary,
        "controls": results,
        "global_cost_ledger": {
            "producer_generation_ops": total_generation_ops,
            "exact_subset_dp_cut_evaluations": totals["cuts"],
            "exact_verifier_assignment_rows": totals["assignment_rows"],
            "exact_verifier_literal_checks": totals["literal_checks"],
        },
        "exact_dp_is_exponential_audit_oracle_not_runtime_algorithm": True,
        "signature_cap_is_upper_bound_not_exact_pswidth": True,
        "universal_candidate_completeness": "OPEN",
        "universal_polynomial_semantic_decomposition_discovery": "OPEN",
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
        producer.SlimeSignatureCapCandidateRouter,
        {
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "PINNED_EXTERNAL_HEURISTIC_PRODUCER_NOT_VERIFIER",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print("PF5_SLIME_SIGNATURE_CAP_BLIND_V12 =", result["status"])
    print("MANIFEST_BATCH_SHA256 =", result["manifest_batch_sha256"])
    print("CALIBRATION =", {
        "old": result["calibration"]["old_slime_width"],
        "new": result["calibration"]["new_slime_width"],
        "opt": result["calibration"]["exact_optimal_width"],
    })
    print("HOLDOUT_SUMMARY =", result["holdout_summary"])
    for row in result["controls"]:
        if row["phase"] == "BLIND_HOLDOUT":
            print(row["seed"], "OLD=", row["old_slime_width"], "NEW=", row["new_slime_width"], "OPT=", row["exact_optimal_width"], row["new_vs_old"])
    print("GLOBAL_COST_LEDGER =", result["global_cost_ledger"])
    print("UNIVERSAL_CANDIDATE_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
