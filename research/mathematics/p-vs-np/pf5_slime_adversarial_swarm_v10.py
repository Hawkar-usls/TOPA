#!/usr/bin/env python3
"""PF5 Slime adversarial fixed random-swarm stress v10.

All candidate orders are frozen before exact scoring. The exact C032/STV
caterpillar PS scorer is imported from v9 and remains a finite exponential audit
oracle, never the candidate generator or claimed runtime algorithm.
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

FROZEN_SOURCE_SEEDS = list(range(906500, 906532))
CHALLENGERS_PER_SOURCE = 32
DOMAIN = "PF5-SLIME-ADVERSARIAL-SWARM-V10"


def repaired_import_producer(path: Path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_semantic_candidate_router_v10_pin",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load producer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def deterministic_challenger_seed(source_sha256: str, index: int) -> int:
    payload = f"{DOMAIN}|{source_sha256}|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def challenger_order(leaves, source_sha256: str, index: int):
    order = list(leaves)
    rng = random.Random(deterministic_challenger_seed(source_sha256, index))
    rng.shuffle(order)
    return order


def seal_payload(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def compare(a: int, b: int) -> str:
    if a < b:
        return "WIN"
    if a == b:
        return "TIE"
    return "LOSS"


def run(router_class, producer_identity):
    router = router_class()
    frozen_sources = []
    random_generation_ops = 0
    slime_generation_ops = 0

    # Phase 1: freeze every source and every candidate before exact scoring.
    for seed in FROZEN_SOURCE_SEEDS:
        formula = v9.random_connected_3cnf(seed, variable_count=7, clause_count=10)
        manifest = router.generate_manifest(formula)
        assert manifest.frozen_before_probe is True
        assert manifest.exact_ps_width_computed_inside_generator is False
        assert manifest.sat_oracle_used is False
        slime = next(
            candidate
            for candidate in manifest.candidates
            if candidate.name == "SLIME_SEMANTIC_PRESSURE"
        )
        leaves = list(slime.linear_leaf_order)
        challengers = []
        for index in range(CHALLENGERS_PER_SOURCE):
            order = challenger_order(leaves, manifest.source_sha256, index)
            random_generation_ops += len(order)
            challengers.append(
                {
                    "index": index,
                    "seed": deterministic_challenger_seed(
                        manifest.source_sha256, index
                    ),
                    "order": order,
                    "order_sha256": seal_payload(order),
                }
            )
        slime_generation_ops += manifest.total_generation_ops
        frozen_sources.append(
            {
                "seed": seed,
                "formula": [list(clause) for clause in formula],
                "source_sha256": manifest.source_sha256,
                "slime_manifest_sha256": manifest.manifest_sha256,
                "slime_order": leaves,
                "slime_order_sha256": seal_payload(leaves),
                "challengers": challengers,
            }
        )

    frozen_batch_projection = [
        {
            "seed": row["seed"],
            "source_sha256": row["source_sha256"],
            "slime_manifest_sha256": row["slime_manifest_sha256"],
            "slime_order_sha256": row["slime_order_sha256"],
            "challenger_order_sha256": [
                c["order_sha256"] for c in row["challengers"]
            ],
        }
        for row in frozen_sources
    ]
    frozen_batch_sha256 = seal_payload(frozen_batch_projection)

    # Phase 2: exact finite audit, after batch freeze.
    verifier_totals = {
        "cuts": 0,
        "assignment_rows": 0,
        "literal_checks": 0,
    }
    results = []
    for row in frozen_sources:
        formula = tuple(tuple(clause) for clause in row["formula"])
        slime_score = v9.score_candidate(formula, row["slime_order"])
        for key in verifier_totals:
            verifier_totals[key] += slime_score["verifier_ledger"][key]

        challenger_scores = []
        for challenger in row["challengers"]:
            score = v9.score_candidate(formula, challenger["order"])
            for key in verifier_totals:
                verifier_totals[key] += score["verifier_ledger"][key]
            challenger_scores.append(
                {
                    "index": challenger["index"],
                    "order_sha256": challenger["order_sha256"],
                    "exact_caterpillar_ps_width": score[
                        "exact_caterpillar_ps_width"
                    ],
                }
            )

        slime_width = slime_score["exact_caterpillar_ps_width"]
        best_random_width = min(
            item["exact_caterpillar_ps_width"] for item in challenger_scores
        )
        best_randoms = [
            item for item in challenger_scores
            if item["exact_caterpillar_ps_width"] == best_random_width
        ]
        strict_better_random_count = sum(
            item["exact_caterpillar_ps_width"] < slime_width
            for item in challenger_scores
        )
        slime_rank = 1 + strict_better_random_count
        results.append(
            {
                "seed": row["seed"],
                "source_sha256": row["source_sha256"],
                "slime_manifest_sha256": row["slime_manifest_sha256"],
                "slime_width": slime_width,
                "best_random_width": best_random_width,
                "slime_vs_best_random": compare(
                    slime_width, best_random_width
                ),
                "slime_tie_aware_rank_among_33": slime_rank,
                "strictly_better_random_challengers": strict_better_random_count,
                "best_random_challengers": best_randoms,
                "all_random_widths": [
                    item["exact_caterpillar_ps_width"]
                    for item in challenger_scores
                ],
            }
        )

    outcome_counts = {
        label: sum(row["slime_vs_best_random"] == label for row in results)
        for label in ["WIN", "TIE", "LOSS"]
    }
    loss_rows = [row for row in results if row["slime_vs_best_random"] == "LOSS"]
    maximum_loss_ratio = max(
        (
            row["slime_width"] / row["best_random_width"]
            for row in loss_rows
        ),
        default=1.0,
    )
    worst_loss = max(
        loss_rows,
        key=lambda row: row["slime_width"] / row["best_random_width"],
        default=None,
    )

    result = {
        "artifact_id": "PF5-SLIME-ADVERSARIAL-SWARM-V10",
        "status": "FINITE_ADVERSARIAL_PROBE_COMPLETE",
        "producer": producer_identity,
        "source_seeds_frozen_before_provider_run": FROZEN_SOURCE_SEEDS,
        "challengers_per_source": CHALLENGERS_PER_SOURCE,
        "challenger_generation_uses_exact_score": False,
        "all_33_orders_per_source_frozen_before_exact_probe": True,
        "frozen_candidate_batch_sha256": frozen_batch_sha256,
        "outcome_counts_vs_best_random": outcome_counts,
        "sources_with_random_escape": len(loss_rows),
        "maximum_loss_ratio": maximum_loss_ratio,
        "worst_loss": worst_loss,
        "results": results,
        "generation_cost_ledger": {
            "slime_generation_ops": slime_generation_ops,
            "random_order_generation_ops": random_generation_ops,
            "total_generation_ops": slime_generation_ops
            + random_generation_ops,
        },
        "exact_verifier_cost_ledger": verifier_totals,
        "exact_probe_is_finite_exponential_audit_only": True,
        "current_single_front_slime_router_portfolio_complete": False
        if loss_rows
        else "NOT_ESTABLISHED",
        "next_gate": "SLIME_MULTI_FRONT_PROOF_CARRYING_CANDIDATE_SWARM"
        if loss_rows
        else "STRONGER_ADVERSARIAL_PORTFOLIO",
        "universal_candidate_completeness": "OPEN",
        "p_vs_np": "OPEN",
    }
    payload = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    result["result_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-path", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    producer_bytes = args.producer_path.read_bytes()
    producer = repaired_import_producer(args.producer_path)
    result = run(
        producer.SlimeSemanticCandidateRouter,
        {
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(producer_bytes).hexdigest(),
            "role": "PINNED_EXTERNAL_CANDIDATE_PRODUCER",
        },
    )

    if args.json_out:
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    print("PF5_SLIME_ADVERSARIAL_SWARM_V10 =", result["status"])
    print("FROZEN_BATCH_SHA256 =", result["frozen_candidate_batch_sha256"])
    print("OUTCOME_COUNTS =", result["outcome_counts_vs_best_random"])
    print("SOURCES_WITH_RANDOM_ESCAPE =", result["sources_with_random_escape"])
    print("MAXIMUM_LOSS_RATIO =", result["maximum_loss_ratio"])
    print("WORST_LOSS =", result["worst_loss"])
    for row in result["results"]:
        print(
            "SEED", row["seed"],
            "SLIME", row["slime_width"],
            "BEST_RANDOM", row["best_random_width"],
            "OUTCOME", row["slime_vs_best_random"],
            "RANK", row["slime_tie_aware_rank_among_33"],
            "BETTER_RANDOM", row["strictly_better_random_challengers"],
        )
    print("GENERATION_COST =", result["generation_cost_ledger"])
    print("VERIFIER_COST =", result["exact_verifier_cost_ledger"])
    print("UNIVERSAL_CANDIDATE_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
