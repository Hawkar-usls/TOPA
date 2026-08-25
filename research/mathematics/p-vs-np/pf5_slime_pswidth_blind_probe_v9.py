#!/usr/bin/env python3
"""PF5 Slime PS-width blind probe v9.

The Slime producer is external and pinned by workflow commit.  This script
first generates and hashes *all* candidate manifests, then and only then runs an
independent exact finite PS-signature scorer.  The scorer is exponential and is
an audit oracle only; it is not the claimed runtime algorithm.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import random
from pathlib import Path

FROZEN_HOLDOUT_SEEDS = [
    905101,
    905102,
    905103,
    905104,
    905105,
    905106,
    905107,
    905108,
]


def variables_of(formula):
    return sorted({abs(lit) for clause in formula for lit in clause})


def project_formula(formula, clause_indices, variables):
    return tuple(
        tuple(lit for lit in formula[index] if abs(lit) in variables)
        for index in sorted(clause_indices)
    )


def assignment_signatures(projected, ledger):
    variables = sorted({abs(lit) for clause in projected for lit in clause})
    signatures = set()
    for bits in itertools.product((False, True), repeat=len(variables)):
        ledger["assignment_rows"] += 1
        assignment = dict(zip(variables, bits))
        satisfied = []
        for clause_index, clause in enumerate(projected):
            clause_satisfied = False
            for literal in clause:
                ledger["literal_checks"] += 1
                if assignment[abs(literal)] == (literal > 0):
                    clause_satisfied = True
                    break
            if clause_satisfied:
                satisfied.append(clause_index)
        signatures.add(tuple(satisfied))
    return signatures


def ps_cut_value(formula, selected_leaves, ledger):
    selected_clauses = {
        int(leaf.split(":", 1)[1])
        for leaf in selected_leaves
        if leaf.startswith("c:")
    }
    selected_variables = {
        int(leaf.split(":", 1)[1])
        for leaf in selected_leaves
        if leaf.startswith("v:")
    }
    all_clauses = set(range(len(formula)))
    all_variables = set(variables_of(formula))

    left = project_formula(
        formula,
        all_clauses - selected_clauses,
        selected_variables,
    )
    right = project_formula(
        formula,
        selected_clauses,
        all_variables - selected_variables,
    )
    left_signatures = assignment_signatures(left, ledger)
    right_signatures = assignment_signatures(right, ledger)
    ledger["cuts"] += 1
    return (
        max(len(left_signatures), len(right_signatures)),
        len(left_signatures),
        len(right_signatures),
    )


def caterpillar_cut_family(order):
    """Exact edge-cut family of a right-linear/caterpillar leaf order."""
    all_leaves = frozenset(order)

    def canonical_partition_side(side):
        side = frozenset(side)
        complement = all_leaves - side
        if len(side) < len(complement):
            return side
        if len(complement) < len(side):
            return complement
        return min(side, complement, key=lambda x: tuple(sorted(x)))

    cuts = set()
    for leaf in order:
        cuts.add(canonical_partition_side([leaf]))

    prefix = set()
    for leaf in order[:-1]:
        prefix.add(leaf)
        cuts.add(canonical_partition_side(prefix))

    expected = max(1, 2 * len(order) - 3)
    assert len(cuts) == expected, (len(order), len(cuts), expected)
    return sorted(cuts, key=lambda cut: (len(cut), tuple(sorted(cut))))


def score_candidate(formula, order):
    ledger = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    maximum = 0
    worst = None
    for cut in caterpillar_cut_family(order):
        value, left_size, right_size = ps_cut_value(formula, set(cut), ledger)
        if value > maximum:
            maximum = value
            worst = {
                "selected": sorted(cut),
                "cut_value": value,
                "left_ps": left_size,
                "right_ps": right_size,
            }
    return {
        "exact_caterpillar_ps_width": maximum,
        "worst_cut": worst,
        "verifier_ledger": ledger,
    }


def direct_boundary_signatures(formula, selected_clauses, selected_variables):
    """Independent C032-style direct boundary calculation for audit checks."""
    all_clauses = set(range(len(formula)))
    all_variables = set(variables_of(formula))

    outside_clauses = sorted(all_clauses - selected_clauses)
    left_variables = sorted(selected_variables)
    left_signatures = set()
    for bits in itertools.product((False, True), repeat=len(left_variables)):
        assignment = dict(zip(left_variables, bits))
        signature = tuple(
            local_index
            for local_index, clause_index in enumerate(outside_clauses)
            if any(
                abs(lit) in selected_variables
                and assignment[abs(lit)] == (lit > 0)
                for lit in formula[clause_index]
            )
        )
        left_signatures.add(signature)

    inside_clauses = sorted(selected_clauses)
    right_variables_set = all_variables - selected_variables
    right_variables = sorted(right_variables_set)
    right_signatures = set()
    for bits in itertools.product((False, True), repeat=len(right_variables)):
        assignment = dict(zip(right_variables, bits))
        signature = tuple(
            local_index
            for local_index, clause_index in enumerate(inside_clauses)
            if any(
                abs(lit) in right_variables_set
                and assignment[abs(lit)] == (lit > 0)
                for lit in formula[clause_index]
            )
        )
        right_signatures.add(signature)
    return left_signatures, right_signatures


def verify_cut_identity(formula, selected_clauses, selected_variables):
    ledger = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    all_clauses = set(range(len(formula)))
    all_variables = set(variables_of(formula))
    left = assignment_signatures(
        project_formula(formula, all_clauses - selected_clauses, selected_variables),
        ledger,
    )
    right = assignment_signatures(
        project_formula(formula, selected_clauses, all_variables - selected_variables),
        ledger,
    )
    direct_left, direct_right = direct_boundary_signatures(
        formula,
        selected_clauses,
        selected_variables,
    )
    return left == direct_left and right == direct_right


def connected_block_chain(group_count):
    clauses = []
    for index in range(group_count):
        left = 2 * index + 1
        right = 2 * index + 2
        clauses.append((left, right))
        clauses.append((left, right))
    hub = 2 * group_count + 1
    for index in range(group_count - 1):
        clauses.append((2 * index + 2, 2 * (index + 1) + 1, hub))
    return tuple(clauses)


def duplicate_family(variable_count, clause_count):
    clause = tuple(range(1, variable_count + 1))
    return tuple(clause for _ in range(clause_count))


def unit_family(variable_count):
    return tuple((variable,) for variable in range(1, variable_count + 1))


def random_connected_3cnf(seed, variable_count=7, clause_count=10):
    rng = random.Random(seed)
    clauses = []

    # Frozen connected 3-CNF chain backbone.
    for start in range(1, variable_count - 1):
        variables = [start, start + 1, start + 2]
        clauses.append(
            tuple(v if rng.getrandbits(1) else -v for v in variables)
        )

    seen = {
        tuple(sorted(clause, key=lambda x: (abs(x), x < 0)))
        for clause in clauses
    }
    while len(clauses) < clause_count:
        variables = rng.sample(range(1, variable_count + 1), 3)
        clause = tuple(v if rng.getrandbits(1) else -v for v in variables)
        key = tuple(sorted(clause, key=lambda x: (abs(x), x < 0)))
        if key in seen:
            continue
        seen.add(key)
        clauses.append(clause)
    return tuple(clauses)


def build_controls():
    controls = []
    for group_count in [2, 3, 4, 5]:
        controls.append(
            (
                f"CAL_CONNECTED_BLOCK_G{group_count}",
                "CALIBRATION",
                connected_block_chain(group_count),
            )
        )
    controls.extend(
        [
            ("KNOWN_DUPLICATE_K4_4", "KNOWN_GAP", duplicate_family(4, 4)),
            ("KNOWN_DUPLICATE_K6_6", "KNOWN_GAP", duplicate_family(6, 6)),
        ]
    )
    for seed in FROZEN_HOLDOUT_SEEDS:
        controls.append(
            (
                f"HOLDOUT_CONNECTED3CNF_{seed}",
                "BLIND_HOLDOUT",
                random_connected_3cnf(seed),
            )
        )
    controls.append(("PRESSURE_UNIT_N8", "PRESSURE", unit_family(8)))
    return controls


def import_producer(path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_semantic_candidate_router_pin",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load producer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def comparison_label(left, right):
    if left < right:
        return "WIN"
    if left == right:
        return "TIE"
    return "LOSS"


def run_with_router(router_class, producer_identity):
    controls = build_controls()
    router = router_class()

    # PHASE 1: all candidate manifests are generated and frozen before any
    # exact PS-signature probe occurs.
    frozen = []
    for fixture_id, phase, formula in controls:
        manifest = router.generate_manifest(formula)
        assert manifest.frozen_before_probe is True
        assert manifest.exact_ps_width_computed_inside_generator is False
        assert manifest.sat_oracle_used is False
        frozen.append(
            {
                "id": fixture_id,
                "phase": phase,
                "formula": [list(clause) for clause in formula],
                "manifest": manifest.to_dict(),
            }
        )

    manifest_batch_payload = [
        (
            item["id"],
            item["manifest"]["source_sha256"],
            item["manifest"]["manifest_sha256"],
        )
        for item in frozen
    ]
    manifest_batch_sha256 = hashlib.sha256(
        json.dumps(
            manifest_batch_payload,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    ).hexdigest()

    # Independent definitional canary after freeze.
    identity_checks = 0
    identity_rng = random.Random(905199)
    for item in frozen[:8]:
        formula = tuple(tuple(clause) for clause in item["formula"])
        variables = variables_of(formula)
        for _ in range(4):
            selected_clauses = {
                index
                for index in range(len(formula))
                if identity_rng.getrandbits(1)
            }
            selected_variables = {
                variable
                for variable in variables
                if identity_rng.getrandbits(1)
            }
            assert verify_cut_identity(
                formula,
                selected_clauses,
                selected_variables,
            )
            identity_checks += 1

    # PHASE 2: exact bounded scoring after the entire manifest batch is frozen.
    results = []
    totals = {
        "generator_ops": 0,
        "verifier_cuts": 0,
        "verifier_assignment_rows": 0,
        "verifier_literal_checks": 0,
    }

    for item in frozen:
        formula = tuple(tuple(clause) for clause in item["formula"])
        manifest = item["manifest"]
        totals["generator_ops"] += manifest["total_generation_ops"]

        scored = {}
        for candidate in manifest["candidates"]:
            score = score_candidate(formula, candidate["linear_leaf_order"])
            scored[candidate["name"]] = score
            ledger = score["verifier_ledger"]
            totals["verifier_cuts"] += ledger["cuts"]
            totals["verifier_assignment_rows"] += ledger["assignment_rows"]
            totals["verifier_literal_checks"] += ledger["literal_checks"]

        widths = {
            name: score["exact_caterpillar_ps_width"]
            for name, score in scored.items()
        }
        slime_width = widths["SLIME_SEMANTIC_PRESSURE"]
        lexical_width = widths["LEXICAL_BASELINE"]
        best_non_slime_width = min(
            width
            for name, width in widths.items()
            if name != "SLIME_SEMANTIC_PRESSURE"
        )
        best_width = min(widths.values())

        results.append(
            {
                "fixture": item["id"],
                "phase": item["phase"],
                "source_variables": len(variables_of(formula)),
                "source_clauses": len(formula),
                "manifest_sha256": manifest["manifest_sha256"],
                "generation_ops": manifest["total_generation_ops"],
                "candidate_widths": widths,
                "slime_width": slime_width,
                "lexical_width": lexical_width,
                "best_non_slime_width": best_non_slime_width,
                "best_width": best_width,
                "slime_vs_lexical": comparison_label(slime_width, lexical_width),
                "slime_vs_best_non_slime": comparison_label(
                    slime_width,
                    best_non_slime_width,
                ),
                "exact_scores": scored,
            }
        )

    holdout = [row for row in results if row["phase"] == "BLIND_HOLDOUT"]

    def counts(field):
        return {
            label: sum(row[field] == label for row in holdout)
            for label in ["WIN", "TIE", "LOSS"]
        }

    return {
        "artifact_id": "PF5-SLIME-PSWIDTH-BLIND-PROBE-V9",
        "status": "FINITE_EXACT_PROBE_COMPLETE",
        "producer": producer_identity,
        "holdout_seeds_frozen_before_provider_run": FROZEN_HOLDOUT_SEEDS,
        "candidate_manifest_batch_frozen_before_exact_probe": True,
        "manifest_batch_sha256": manifest_batch_sha256,
        "c032_cut_identity_checks": identity_checks,
        "controls": results,
        "holdout_summary": {
            "count": len(holdout),
            "vs_lexical": counts("slime_vs_lexical"),
            "vs_best_non_slime": counts("slime_vs_best_non_slime"),
            "mean_slime_width": sum(row["slime_width"] for row in holdout)
            / len(holdout),
            "mean_lexical_width": sum(row["lexical_width"] for row in holdout)
            / len(holdout),
        },
        "global_cost_ledger": totals,
        "exact_probe_is_finite_exponential_verifier_not_runtime_algorithm": True,
        "universal_candidate_completeness": "OPEN",
        "universal_polynomial_semantic_decomposition_discovery": "OPEN",
        "p_vs_np": "OPEN",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-path", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    raw = args.producer_path.read_bytes()
    producer_sha256 = hashlib.sha256(raw).hexdigest()
    module = import_producer(args.producer_path)
    result = run_with_router(
        module.SlimeSemanticCandidateRouter,
        {
            "path": str(args.producer_path),
            "file_sha256": producer_sha256,
            "role": "EXTERNAL_HEURISTIC_PRODUCER_NOT_VERIFIER",
        },
    )

    payload = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    result["result_sha256"] = hashlib.sha256(payload).hexdigest()

    if args.json_out:
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    print("PF5_SLIME_PSWIDTH_BLIND_PROBE_V9 =", result["status"])
    print("MANIFEST_BATCH_SHA256 =", result["manifest_batch_sha256"])
    print("C032_CUT_IDENTITY_CHECKS =", result["c032_cut_identity_checks"])
    print("HOLDOUT_VS_LEXICAL =", result["holdout_summary"]["vs_lexical"])
    print(
        "HOLDOUT_VS_BEST_NON_SLIME =",
        result["holdout_summary"]["vs_best_non_slime"],
    )
    for row in result["controls"]:
        print(
            row["fixture"],
            row["phase"],
            row["candidate_widths"],
            "SLIMEvLEX=", row["slime_vs_lexical"],
            "SLIMEvBESTNON=", row["slime_vs_best_non_slime"],
        )
    print("GLOBAL_COST_LEDGER =", result["global_cost_ledger"])
    print("UNIVERSAL_CANDIDATE_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
