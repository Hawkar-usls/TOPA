#!/usr/bin/env python3
"""PF5 Slime adversarial loss search v10.

This is not a SAT algorithm. It freezes a deterministic corpus of connected
3-CNFs, asks the pinned external Slime producer for assignment-independent
candidate orders for the entire corpus, seals all manifests, and only then uses
the finite exponential v9 exact PS-width scorer to search for counterexamples
to the current Slime heuristic.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9

SEARCH_SEEDS = list(range(906000, 906128))
PRODUCER_ROLE = "EXTERNAL_HEURISTIC_PRODUCER_NOT_VERIFIER"


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_semantic_candidate_router_pin_v10", path
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


def corpus_formula(seed: int):
    return v9.random_connected_3cnf(seed, variable_count=7, clause_count=10)


def run(router_class, producer_identity: dict) -> dict:
    router = router_class()

    # Phase 1: freeze every source and every candidate manifest before any
    # exact PS-width score is computed.
    frozen = []
    generation_ops = 0
    for seed in SEARCH_SEEDS:
        formula = corpus_formula(seed)
        manifest = router.generate_manifest(formula)
        assert manifest.frozen_before_probe is True
        assert manifest.exact_ps_width_computed_inside_generator is False
        assert manifest.sat_oracle_used is False
        generation_ops += manifest.total_generation_ops
        frozen.append(
            {
                "seed": seed,
                "formula": [list(c) for c in formula],
                "source_sha256": manifest.source_sha256,
                "manifest": manifest.to_dict(),
            }
        )

    batch_preimage = [
        (x["seed"], x["source_sha256"], x["manifest"]["manifest_sha256"])
        for x in frozen
    ]
    manifest_batch_sha256 = hashlib.sha256(
        json.dumps(batch_preimage, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    # Phase 2: independent finite exact audit. No new source or candidate is
    # created after this line.
    verifier = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    rows = []
    losses = []
    ties = 0
    wins = 0
    for item in frozen:
        formula = tuple(tuple(c) for c in item["formula"])
        widths = {}
        per_candidate_ledgers = {}
        for candidate in item["manifest"]["candidates"]:
            score = v9.score_candidate(formula, candidate["linear_leaf_order"])
            widths[candidate["name"]] = score["exact_caterpillar_ps_width"]
            led = score["verifier_ledger"]
            per_candidate_ledgers[candidate["name"]] = led
            verifier["cuts"] += led["cuts"]
            verifier["assignment_rows"] += led["assignment_rows"]
            verifier["literal_checks"] += led["literal_checks"]

        slime = widths["SLIME_SEMANTIC_PRESSURE"]
        best_non = min(
            value for name, value in widths.items()
            if name != "SLIME_SEMANTIC_PRESSURE"
        )
        best_non_names = sorted(
            name for name, value in widths.items()
            if name != "SLIME_SEMANTIC_PRESSURE" and value == best_non
        )
        if slime > best_non:
            outcome = "LOSS"
        elif slime == best_non:
            outcome = "TIE"
        else:
            outcome = "WIN"

        row = {
            "seed": item["seed"],
            "source_sha256": item["source_sha256"],
            "manifest_sha256": item["manifest"]["manifest_sha256"],
            "candidate_widths": widths,
            "slime_width": slime,
            "best_non_slime_width": best_non,
            "best_non_slime_candidates": best_non_names,
            "slime_vs_best_non_slime": outcome,
            "formula": item["formula"],
            "verifier_ledgers": per_candidate_ledgers,
        }
        rows.append(row)
        if outcome == "LOSS":
            losses.append(row)
        elif outcome == "TIE":
            ties += 1
        else:
            wins += 1

    result = {
        "artifact_id": "PF5-SLIME-ADVERSARIAL-LOSS-V10",
        "status": "FINITE_ADVERSARIAL_CORPUS_COMPLETE",
        "producer": producer_identity,
        "search_seeds_frozen_before_provider_run": SEARCH_SEEDS,
        "sources_and_manifests_frozen_before_exact_probe": True,
        "adaptive_source_generation_after_probe": False,
        "manifest_batch_sha256": manifest_batch_sha256,
        "corpus_size": len(rows),
        "summary": {
            "slime_wins": wins,
            "slime_ties": ties,
            "slime_losses": len(losses),
            "first_loss_seed": losses[0]["seed"] if losses else None,
            "max_loss_gap": max(
                (x["slime_width"] - x["best_non_slime_width"] for x in losses),
                default=0,
            ),
        },
        "loss_receipts": losses,
        "all_rows": rows,
        "global_cost_ledger": {
            "slime_generation_ops": generation_ops,
            "exact_verifier_cuts": verifier["cuts"],
            "exact_verifier_assignment_rows": verifier["assignment_rows"],
            "exact_verifier_literal_checks": verifier["literal_checks"],
        },
        "interpretation": (
            "A loss refutes completeness of the current frozen Slime candidate "
            "heuristic on this finite corpus only. No loss would mean only that "
            "this corpus did not expose one."
        ),
        "next_gate": "EXPLAIN_FIRST_SLIME_LOSS_WITH_PROOF_CARRYING_SOURCE_FEATURE_OR_EXPAND_FROZEN_ADVERSARY",
        "universal_candidate_completeness": "OPEN",
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

    producer_bytes = args.producer_path.read_bytes()
    producer_sha256 = hashlib.sha256(producer_bytes).hexdigest()
    producer = import_producer(args.producer_path)
    result = run(
        producer.SlimeSemanticCandidateRouter,
        {
            "path": str(args.producer_path),
            "file_sha256": producer_sha256,
            "role": PRODUCER_ROLE,
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print("PF5_SLIME_ADVERSARIAL_LOSS_V10 =", result["status"])
    print("MANIFEST_BATCH_SHA256 =", result["manifest_batch_sha256"])
    print("SUMMARY =", result["summary"])
    if result["loss_receipts"]:
        first = result["loss_receipts"][0]
        print("FIRST_LOSS =", first["seed"], first["candidate_widths"])
    print("GLOBAL_COST_LEDGER =", result["global_cost_ledger"])
    print("UNIVERSAL_CANDIDATE_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
