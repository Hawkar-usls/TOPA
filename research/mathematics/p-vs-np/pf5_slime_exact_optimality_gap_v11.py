#!/usr/bin/env python3
"""PF5 Slime exact small-instance optimality-gap audit v11.

The external Slime producer remains frozen and assignment-independent.  For a
small frozen connected-3CNF corpus, TOPA computes the exact optimum over every
right-linear/caterpillar leaf order by subset dynamic programming.  The exact
oracle is exponential and is used only as a finite adversarial judge.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9

FROZEN_SEEDS = list(range(907000, 907016))
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_semantic_candidate_router_pin_v11", path
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


def exact_cut_cache(formula, leaves):
    n = len(leaves)
    full = (1 << n) - 1
    ledger = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    values = [0] * (1 << n)
    for mask in range(1, full):
        selected = {leaves[i] for i in range(n) if mask & (1 << i)}
        value, _, _ = v9.ps_cut_value(formula, selected, ledger)
        values[mask] = value
    return values, ledger


def order_width_from_cache(order, leaf_index, cut_values):
    n = len(order)
    singleton_max = max(cut_values[1 << leaf_index[leaf]] for leaf in order)
    prefix = 0
    maximum = singleton_max
    for leaf in order[:-1]:
        prefix |= 1 << leaf_index[leaf]
        maximum = max(maximum, cut_values[prefix])
    return maximum


def exact_optimal_order(leaves, cut_values):
    n = len(leaves)
    full = (1 << n) - 1
    inf = 10**18
    dp = [inf] * (1 << n)
    chosen_last_added = [-1] * (1 << n)
    dp[0] = 0

    # dp[mask] is the minimum possible maximum prefix-cut value for an order
    # whose current prefix contains exactly mask.  The singleton-edge term of
    # a caterpillar is handled globally below because every leaf contributes a
    # singleton edge regardless of order.
    for mask in range(1, full):
        cut = cut_values[mask]
        bits = mask
        best = inf
        best_bit = -1
        while bits:
            bit = bits & -bits
            previous = mask ^ bit
            candidate = max(dp[previous], cut)
            if candidate < best:
                best = candidate
                best_bit = bit
            bits ^= bit
        dp[mask] = best
        chosen_last_added[mask] = best_bit

    singleton_max = max(cut_values[1 << i] for i in range(n))
    optimum = inf
    optimum_last = -1
    optimum_prefix_mask = 0
    for last in range(n):
        prefix_mask = full ^ (1 << last)
        candidate = max(singleton_max, dp[prefix_mask])
        if candidate < optimum:
            optimum = candidate
            optimum_last = last
            optimum_prefix_mask = prefix_mask

    reverse_indices = []
    mask = optimum_prefix_mask
    while mask:
        bit = chosen_last_added[mask]
        if bit <= 0:
            raise AssertionError("broken DP predecessor")
        index = bit.bit_length() - 1
        reverse_indices.append(index)
        mask ^= bit
    prefix_indices = list(reversed(reverse_indices))
    order = [leaves[i] for i in prefix_indices] + [leaves[optimum_last]]
    if sorted(order) != sorted(leaves):
        raise AssertionError("optimal order is not a leaf permutation")
    return optimum, order


def run(router_class, producer_identity):
    router = router_class()

    # Phase 1: freeze every source and manifest first.
    frozen = []
    total_generation_ops = 0
    for seed in FROZEN_SEEDS:
        formula = v9.random_connected_3cnf(
            seed, variable_count=VARIABLE_COUNT, clause_count=CLAUSE_COUNT
        )
        manifest = router.generate_manifest(formula)
        assert manifest.frozen_before_probe is True
        assert manifest.exact_ps_width_computed_inside_generator is False
        assert manifest.sat_oracle_used is False
        total_generation_ops += manifest.total_generation_ops
        frozen.append(
            {
                "seed": seed,
                "formula": [list(c) for c in formula],
                "manifest": manifest.to_dict(),
            }
        )

    batch = [
        (x["seed"], x["manifest"]["source_sha256"], x["manifest"]["manifest_sha256"])
        for x in frozen
    ]
    manifest_batch_sha256 = hashlib.sha256(
        json.dumps(batch, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    # Phase 2: exponential exact judge after freeze.
    rows = []
    totals = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    for item in frozen:
        formula = tuple(tuple(c) for c in item["formula"])
        manifest = item["manifest"]
        leaves = sorted(manifest["candidates"][0]["linear_leaf_order"])
        leaf_index = {leaf: i for i, leaf in enumerate(leaves)}
        cut_values, ledger = exact_cut_cache(formula, leaves)
        for key in totals:
            totals[key] += ledger[key]

        optimum, optimum_order = exact_optimal_order(leaves, cut_values)
        verified_optimum_width = order_width_from_cache(
            optimum_order, leaf_index, cut_values
        )
        assert verified_optimum_width == optimum

        candidate_widths = {}
        for candidate in manifest["candidates"]:
            candidate_widths[candidate["name"]] = order_width_from_cache(
                candidate["linear_leaf_order"], leaf_index, cut_values
            )
        slime = candidate_widths["SLIME_SEMANTIC_PRESSURE"]
        gap = slime - optimum
        rows.append(
            {
                "seed": item["seed"],
                "source_sha256": manifest["source_sha256"],
                "manifest_sha256": manifest["manifest_sha256"],
                "leaf_count": len(leaves),
                "candidate_widths": candidate_widths,
                "exact_optimal_caterpillar_ps_width": optimum,
                "exact_optimal_order": optimum_order,
                "slime_width": slime,
                "slime_optimality_gap": gap,
                "slime_is_optimal": gap == 0,
                "formula": item["formula"],
            }
        )

    gaps = [r for r in rows if r["slime_optimality_gap"] > 0]
    result = {
        "artifact_id": "PF5-SLIME-EXACT-OPTIMALITY-GAP-V11",
        "status": "FINITE_EXACT_OPTIMUM_AUDIT_COMPLETE",
        "producer": producer_identity,
        "frozen_seeds_before_provider_run": FROZEN_SEEDS,
        "variable_count": VARIABLE_COUNT,
        "clause_count": CLAUSE_COUNT,
        "all_sources_and_manifests_frozen_before_exact_dp": True,
        "adaptive_candidate_generation_after_exact_dp": False,
        "manifest_batch_sha256": manifest_batch_sha256,
        "summary": {
            "cases": len(rows),
            "slime_optimal": sum(r["slime_is_optimal"] for r in rows),
            "slime_suboptimal": len(gaps),
            "first_gap_seed": gaps[0]["seed"] if gaps else None,
            "max_optimality_gap": max(
                (r["slime_optimality_gap"] for r in gaps), default=0
            ),
            "mean_slime_width": sum(r["slime_width"] for r in rows) / len(rows),
            "mean_optimal_width": sum(
                r["exact_optimal_caterpillar_ps_width"] for r in rows
            ) / len(rows),
        },
        "gap_receipts": gaps,
        "all_rows": rows,
        "global_cost_ledger": {
            "slime_generation_ops": total_generation_ops,
            "exact_subset_dp_cut_evaluations": totals["cuts"],
            "exact_verifier_assignment_rows": totals["assignment_rows"],
            "exact_verifier_literal_checks": totals["literal_checks"],
        },
        "exact_dp_is_exponential_audit_oracle_not_runtime_algorithm": True,
        "interpretation": (
            "Any positive gap proves only that the frozen Slime heuristic is "
            "not optimal for caterpillar PS-width on that finite source. It "
            "does not imply hardness."
        ),
        "next_gate": "EXPLAIN_EXACT_SLIME_GAP_WITH_ASSIGNMENT_INDEPENDENT_PROOF_CARRYING_FEATURE",
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
    producer_raw = args.producer_path.read_bytes()
    producer_sha256 = hashlib.sha256(producer_raw).hexdigest()
    producer = import_producer(args.producer_path)
    result = run(
        producer.SlimeSemanticCandidateRouter,
        {
            "path": str(args.producer_path),
            "file_sha256": producer_sha256,
            "role": "EXTERNAL_HEURISTIC_PRODUCER_NOT_VERIFIER",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_SLIME_EXACT_OPTIMALITY_GAP_V11 =", result["status"])
    print("MANIFEST_BATCH_SHA256 =", result["manifest_batch_sha256"])
    print("SUMMARY =", result["summary"])
    if result["gap_receipts"]:
        first = result["gap_receipts"][0]
        print("FIRST_GAP =", first["seed"], "SLIME=", first["slime_width"], "OPT=", first["exact_optimal_caterpillar_ps_width"])
    print("GLOBAL_COST_LEDGER =", result["global_cost_ledger"])
    print("UNIVERSAL_CANDIDATE_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
