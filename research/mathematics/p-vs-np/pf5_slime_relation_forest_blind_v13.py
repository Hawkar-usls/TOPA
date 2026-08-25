#!/usr/bin/env python3
"""PF5 Slime relation-forest blind validation v13.

Known seed 908001 is calibration only. Fresh holdouts 909000..909015 are frozen
before provider execution. A pinned Janus-Demiurge v3 producer emits one complete
six-candidate manifest containing v1, v2, and v3 Slime candidates. TOPA freezes
all sources/manifests before invoking the exponential exact small-instance
caterpillar PS-width subset-DP judge.

The exact DP is an audit oracle only, never the claimed runtime algorithm.
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

CALIBRATION_SEED = 908001
FROZEN_HOLDOUT_SEEDS = list(range(909000, 909016))
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7
V1 = "SLIME_SEMANTIC_PRESSURE"
V2 = "SLIME_SIGNATURE_CAP_PRESSURE"
V3 = "SLIME_RELATION_FOREST_PRESSURE"


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location("janus_slime_v3_pin_v13", path)
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


def sources():
    rows = [
        ("CALIBRATION_908001_ALREADY_OBSERVED", "CALIBRATION_POSTHOC", CALIBRATION_SEED)
    ]
    rows.extend((f"BLIND_{seed}", "BLIND_HOLDOUT", seed) for seed in FROZEN_HOLDOUT_SEEDS)
    return [
        (
            fixture,
            phase,
            seed,
            v9.random_connected_3cnf(seed, VARIABLE_COUNT, CLAUSE_COUNT),
        )
        for fixture, phase, seed in rows
    ]


def run(router_class, producer_identity):
    router = router_class()

    # Phase 1: freeze all sources and complete manifests before any exact score.
    frozen = []
    generation_ops = 0
    for fixture, phase, seed, formula in sources():
        manifest = router.generate_manifest(formula)
        assert manifest.frozen_before_probe is True
        assert manifest.exact_ps_width_computed_inside_generator is False
        assert manifest.sat_oracle_used is False
        names = [c.name for c in manifest.candidates]
        assert V1 in names and V2 in names and V3 in names
        assert len(manifest.candidates) == 6
        generation_ops += manifest.total_generation_ops
        frozen.append(
            {
                "fixture": fixture,
                "phase": phase,
                "seed": seed,
                "formula": [list(c) for c in formula],
                "manifest": manifest.to_dict(),
            }
        )

    batch_preimage = [
        (
            x["fixture"],
            x["manifest"]["source_sha256"],
            x["manifest"]["manifest_sha256"],
        )
        for x in frozen
    ]
    manifest_batch_sha256 = hashlib.sha256(
        json.dumps(batch_preimage, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    # Phase 2: independent exponential exact judge.
    totals = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    controls = []
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
        w1, w2, w3 = widths[V1], widths[V2], widths[V3]
        controls.append(
            {
                "fixture": item["fixture"],
                "phase": item["phase"],
                "seed": item["seed"],
                "source_sha256": manifest["source_sha256"],
                "manifest_sha256": manifest["manifest_sha256"],
                "candidate_widths": widths,
                "v1_width": w1,
                "v2_width": w2,
                "v3_width": w3,
                "exact_optimal_width": optimum,
                "v1_gap": w1 - optimum,
                "v2_gap": w2 - optimum,
                "v3_gap": w3 - optimum,
                "v3_vs_v2": "WIN" if w3 < w2 else "TIE" if w3 == w2 else "LOSS",
                "v3_vs_v1": "WIN" if w3 < w1 else "TIE" if w3 == w1 else "LOSS",
                "v3_exact_optimal": w3 == optimum,
                "exact_optimal_order": optimum_order,
                "formula": item["formula"],
            }
        )

    calibration = next(x for x in controls if x["phase"] == "CALIBRATION_POSTHOC")
    holdout = [x for x in controls if x["phase"] == "BLIND_HOLDOUT"]

    def ncmp(field, label):
        return sum(x[field] == label for x in holdout)

    summary = {
        "holdout_cases": len(holdout),
        "v3_vs_v2_wins": ncmp("v3_vs_v2", "WIN"),
        "v3_vs_v2_ties": ncmp("v3_vs_v2", "TIE"),
        "v3_vs_v2_losses": ncmp("v3_vs_v2", "LOSS"),
        "v3_vs_v1_wins": ncmp("v3_vs_v1", "WIN"),
        "v3_vs_v1_ties": ncmp("v3_vs_v1", "TIE"),
        "v3_vs_v1_losses": ncmp("v3_vs_v1", "LOSS"),
        "v1_exact_optimal_cases": sum(x["v1_gap"] == 0 for x in holdout),
        "v2_exact_optimal_cases": sum(x["v2_gap"] == 0 for x in holdout),
        "v3_exact_optimal_cases": sum(x["v3_gap"] == 0 for x in holdout),
        "mean_v1_width": sum(x["v1_width"] for x in holdout) / len(holdout),
        "mean_v2_width": sum(x["v2_width"] for x in holdout) / len(holdout),
        "mean_v3_width": sum(x["v3_width"] for x in holdout) / len(holdout),
        "mean_optimal_width": sum(x["exact_optimal_width"] for x in holdout) / len(holdout),
        "mean_v1_gap": sum(x["v1_gap"] for x in holdout) / len(holdout),
        "mean_v2_gap": sum(x["v2_gap"] for x in holdout) / len(holdout),
        "mean_v3_gap": sum(x["v3_gap"] for x in holdout) / len(holdout),
        "max_v3_gap": max(x["v3_gap"] for x in holdout),
        "first_v3_vs_v2_loss_seed": next((x["seed"] for x in holdout if x["v3_vs_v2"] == "LOSS"), None),
        "first_v3_suboptimal_seed": next((x["seed"] for x in holdout if not x["v3_exact_optimal"]), None),
    }

    result = {
        "artifact_id": "PF5-SLIME-RELATION-FOREST-BLIND-V13",
        "status": "FINITE_BLIND_EXACT_OPTIMUM_AUDIT_COMPLETE",
        "producer": producer_identity,
        "producer_feature": "PROJECTED_CLAUSE_RELATION_FOREST_CAP",
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
        "controls": controls,
        "global_cost_ledger": {
            "producer_generation_ops": generation_ops,
            "exact_subset_dp_cut_evaluations": totals["cuts"],
            "exact_verifier_assignment_rows": totals["assignment_rows"],
            "exact_verifier_literal_checks": totals["literal_checks"],
        },
        "exact_dp_is_exponential_audit_oracle_not_runtime_algorithm": True,
        "relation_forest_cap_is_upper_bound_not_exact_pswidth": True,
        "universal_candidate_completeness": "OPEN",
        "universal_polynomial_semantic_decomposition_discovery": "OPEN",
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
        producer.SlimeRelationForestCandidateRouter,
        {
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "PINNED_EXTERNAL_HEURISTIC_PRODUCER_NOT_VERIFIER",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_SLIME_RELATION_FOREST_BLIND_V13 =", result["status"])
    print("MANIFEST_BATCH_SHA256 =", result["manifest_batch_sha256"])
    print("CALIBRATION =", {k: result["calibration"][k] for k in ("v1_width", "v2_width", "v3_width", "exact_optimal_width")})
    print("HOLDOUT_SUMMARY =", result["holdout_summary"])
    for row in result["controls"]:
        if row["phase"] == "BLIND_HOLDOUT":
            print(row["seed"], "V1=", row["v1_width"], "V2=", row["v2_width"], "V3=", row["v3_width"], "OPT=", row["exact_optimal_width"], "V3/V2=", row["v3_vs_v2"])
    print("GLOBAL_COST_LEDGER =", result["global_cost_ledger"])
    print("UNIVERSAL_CANDIDATE_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
