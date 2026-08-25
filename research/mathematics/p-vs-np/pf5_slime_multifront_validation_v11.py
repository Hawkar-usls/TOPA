#!/usr/bin/env python3
"""PF5 Slime multi-front fresh validation v11.

All v2 and external benchmark orders are frozen before the independent exact
C032/STV PS-signature scorer runs. No exact-score feedback enters generation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9

FROZEN_SEEDS = list(range(907000, 907032))
EXTERNAL_RANDOM_COUNT = 32
EXTERNAL_DOMAIN = "PF5-SLIME-MULTIFRONT-V11-EXTERNAL-RANDOM"
STRUCTURED_NAMES = {
    "MF_DEFAULT",
    "MF_EDGE_TIGHT",
    "MF_EDGE_GLOBAL",
    "MF_SEM_TIGHT",
    "MF_SEM_GLOBAL",
    "MF_BALANCED_EDGE",
    "MF_BALANCED_SEM",
    "MF_TRACE_NARROW",
}


def import_v2(path: Path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_semantic_candidate_swarm_v2_pin",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load v2 producer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def seal(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def external_seed(source_sha256: str, index: int) -> int:
    payload = f"{EXTERNAL_DOMAIN}|{source_sha256}|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def external_order(leaves, source_sha256: str, index: int):
    order = list(leaves)
    random.Random(external_seed(source_sha256, index)).shuffle(order)
    return order


def compare(a: int, b: int) -> str:
    if a < b:
        return "WIN"
    if a == b:
        return "TIE"
    return "LOSS"


def add_ledger(total, score):
    for key, value in score["verifier_ledger"].items():
        total[key] += value


def run(router_class, producer_identity):
    router = router_class()
    frozen = []
    producer_generation_ops = 0
    external_generation_ops = 0

    # Phase 1: generate every order and seal the complete batch.
    for seed in FROZEN_SEEDS:
        formula = v9.random_connected_3cnf(seed, variable_count=7, clause_count=10)
        manifest = router.generate_manifest(formula)
        assert manifest.artifact_id == "JANUS-SLIME-SEMANTIC-CANDIDATE-SWARM-V2"
        assert len(manifest.candidates) == 16
        assert manifest.frozen_before_probe is True
        assert manifest.exact_ps_width_computed_inside_generator is False
        assert manifest.sat_oracle_used is False
        assert manifest.feature_certificate["probe_feedback_free"] is True
        names = {candidate.name for candidate in manifest.candidates}
        assert STRUCTURED_NAMES <= names
        assert sum(name.startswith("MF_HASH_EXPLORE_") for name in names) == 8

        producer_generation_ops += manifest.total_generation_ops
        v2_orders = [
            {
                "name": candidate.name,
                "order": list(candidate.linear_leaf_order),
                "order_sha256": seal(candidate.linear_leaf_order),
            }
            for candidate in manifest.candidates
        ]
        leaves = list(manifest.candidates[0].linear_leaf_order)
        external = []
        for index in range(EXTERNAL_RANDOM_COUNT):
            order = external_order(leaves, manifest.source_sha256, index)
            external_generation_ops += len(order) + 1
            external.append(
                {
                    "index": index,
                    "seed": external_seed(manifest.source_sha256, index),
                    "order": order,
                    "order_sha256": seal(order),
                }
            )
        frozen.append(
            {
                "seed": seed,
                "formula": [list(clause) for clause in formula],
                "source_sha256": manifest.source_sha256,
                "manifest_sha256": manifest.manifest_sha256,
                "v2_orders": v2_orders,
                "external_orders": external,
            }
        )

    batch_projection = [
        {
            "seed": row["seed"],
            "source_sha256": row["source_sha256"],
            "manifest_sha256": row["manifest_sha256"],
            "v2": [(x["name"], x["order_sha256"]) for x in row["v2_orders"]],
            "external": [x["order_sha256"] for x in row["external_orders"]],
        }
        for row in frozen
    ]
    batch_sha256 = seal(batch_projection)

    # Phase 2: exact bounded audit.
    verifier = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    results = []
    structured_hit_counts = {name: 0 for name in sorted(STRUCTURED_NAMES)}
    full_hit_counts = {}

    for row in frozen:
        formula = tuple(tuple(clause) for clause in row["formula"])
        v2_scores = {}
        for candidate in row["v2_orders"]:
            score = v9.score_candidate(formula, candidate["order"])
            add_ledger(verifier, score)
            v2_scores[candidate["name"]] = score["exact_caterpillar_ps_width"]

        external_scores = []
        for candidate in row["external_orders"]:
            score = v9.score_candidate(formula, candidate["order"])
            add_ledger(verifier, score)
            external_scores.append(score["exact_caterpillar_ps_width"])

        default_width = v2_scores["MF_DEFAULT"]
        best_structured_width = min(v2_scores[name] for name in STRUCTURED_NAMES)
        best_full_width = min(v2_scores.values())
        best_external_width = min(external_scores)
        best_structured_names = sorted(
            name for name in STRUCTURED_NAMES
            if v2_scores[name] == best_structured_width
        )
        best_full_names = sorted(
            name for name, width in v2_scores.items()
            if width == best_full_width
        )
        for name in best_structured_names:
            structured_hit_counts[name] += 1
        for name in best_full_names:
            full_hit_counts[name] = full_hit_counts.get(name, 0) + 1

        results.append(
            {
                "seed": row["seed"],
                "source_sha256": row["source_sha256"],
                "manifest_sha256": row["manifest_sha256"],
                "default_width": default_width,
                "best_structured_width": best_structured_width,
                "best_structured_names": best_structured_names,
                "best_full_v2_width": best_full_width,
                "best_full_v2_names": best_full_names,
                "best_external_random_width": best_external_width,
                "structured_vs_default": compare(best_structured_width, default_width),
                "full_v2_vs_default": compare(best_full_width, default_width),
                "full_v2_vs_external_random": compare(best_full_width, best_external_width),
                "all_v2_widths": v2_scores,
                "external_random_widths": external_scores,
            }
        )

    def outcome_counts(field):
        return {
            label: sum(row[field] == label for row in results)
            for label in ["WIN", "TIE", "LOSS"]
        }

    result = {
        "artifact_id": "PF5-SLIME-MULTIFRONT-VALIDATION-V11",
        "status": "FRESH_FINITE_VALIDATION_COMPLETE",
        "producer": producer_identity,
        "fresh_source_seeds_frozen_before_provider_run": FROZEN_SEEDS,
        "source_n": 7,
        "source_m": 10,
        "v2_candidates_per_source": 16,
        "external_random_candidates_per_source": EXTERNAL_RANDOM_COUNT,
        "all_candidate_orders_frozen_before_exact_probe": True,
        "candidate_batch_sha256": batch_sha256,
        "structured_vs_default": outcome_counts("structured_vs_default"),
        "full_v2_vs_default": outcome_counts("full_v2_vs_default"),
        "full_v2_vs_external_random": outcome_counts("full_v2_vs_external_random"),
        "mean_widths": {
            "default": sum(r["default_width"] for r in results) / len(results),
            "best_structured": sum(r["best_structured_width"] for r in results) / len(results),
            "best_full_v2": sum(r["best_full_v2_width"] for r in results) / len(results),
            "best_external_random": sum(r["best_external_random_width"] for r in results) / len(results),
        },
        "structured_front_hit_counts": structured_hit_counts,
        "full_front_hit_counts": dict(sorted(full_hit_counts.items())),
        "results": results,
        "generation_cost_ledger": {
            "v2_producer_ops": producer_generation_ops,
            "external_random_generation_ops": external_generation_ops,
            "total_generation_ops": producer_generation_ops + external_generation_ops,
        },
        "exact_verifier_cost_ledger": verifier,
        "exact_probe_is_finite_exponential_audit_only": True,
        "runtime_selection_by_exact_ps_score": "FORBIDDEN",
        "universal_candidate_completeness": "OPEN",
        "surviving_gate": "POLYNOMIAL_SEMANTIC_DECOMPOSITION_CANDIDATE_COMPLETENESS_WITH_CHARGED_DISCOVERY",
        "p_vs_np": "OPEN",
    }
    result["result_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-path", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    raw = args.producer_path.read_bytes()
    module = import_v2(args.producer_path)
    result = run(
        module.SlimeSemanticCandidateSwarmV2,
        {
            "commit": "21deebb20e226871f9f1c23a34d5a0693283efef",
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "PINNED_MULTI_FRONT_CANDIDATE_PRODUCER_NOT_JUDGE",
        },
    )

    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print("PF5_SLIME_MULTIFRONT_VALIDATION_V11 =", result["status"])
    print("CANDIDATE_BATCH_SHA256 =", result["candidate_batch_sha256"])
    print("STRUCTURED_VS_DEFAULT =", result["structured_vs_default"])
    print("FULL_V2_VS_DEFAULT =", result["full_v2_vs_default"])
    print("FULL_V2_VS_EXTERNAL_RANDOM =", result["full_v2_vs_external_random"])
    print("MEAN_WIDTHS =", result["mean_widths"])
    print("STRUCTURED_FRONT_HITS =", result["structured_front_hit_counts"])
    print("FULL_FRONT_HITS =", result["full_front_hit_counts"])
    for row in result["results"]:
        print(
            "SEED", row["seed"],
            "DEFAULT", row["default_width"],
            "STRUCT", row["best_structured_width"], row["best_structured_names"],
            "FULL", row["best_full_v2_width"], row["best_full_v2_names"],
            "RANDOM", row["best_external_random_width"],
            "FULLvRANDOM", row["full_v2_vs_external_random"],
        )
    print("GENERATION_COST =", result["generation_cost_ledger"])
    print("VERIFIER_COST =", result["exact_verifier_cost_ledger"])
    print("UNIVERSAL_CANDIDATE_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
