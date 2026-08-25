#!/usr/bin/env python3
"""PF5 exact pure-literal existential projection v12.

No heuristic candidate generation is used by the new feature.  The reducer is a
source-level exact SAT projection rule.  A bounded exponential PS-width oracle
is used only after the frozen holdout sources have been created, for finite
before/after audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_slime_exact_optimality_gap_v11 as v11

DIAGNOSTIC_SEED = 907000
FROZEN_HOLDOUT_SEEDS = list(range(908000, 908032))
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7


def canonical_formula(formula):
    return tuple(tuple(int(lit) for lit in clause) for clause in formula)


def digest_formula(formula):
    return hashlib.sha256(
        json.dumps(formula, sort_keys=False, separators=(",", ":")).encode()
    ).hexdigest()


def literal_polarity_counts(formula, ledger):
    counts = {}
    for clause in formula:
        for literal in clause:
            ledger["literal_occurrence_checks"] += 1
            variable = abs(literal)
            row = counts.setdefault(variable, [0, 0])
            if literal > 0:
                row[0] += 1
            else:
                row[1] += 1
    return counts


def exact_pure_literal_projection(formula):
    residual = canonical_formula(formula)
    transcript = []
    ledger = {
        "rounds": 0,
        "literal_occurrence_checks": 0,
        "clause_membership_checks": 0,
        "clauses_removed": 0,
        "certificate_bytes": 0,
        "residual_bytes_peak": len(json.dumps(residual, separators=(",", ":")).encode()),
        "witness_lift_ops": 0,
    }

    while True:
        ledger["rounds"] += 1
        counts = literal_polarity_counts(residual, ledger)
        chosen = None
        for variable in sorted(counts):
            positive, negative = counts[variable]
            if (positive == 0) ^ (negative == 0):
                chosen = (variable, positive, negative)
                break
        if chosen is None:
            break

        variable, positive, negative = chosen
        value = positive > 0
        satisfying_literal = variable if value else -variable
        opposite_literal = -satisfying_literal
        removed = []
        kept = []
        for index, clause in enumerate(residual):
            ledger["clause_membership_checks"] += len(clause)
            if opposite_literal in clause:
                raise AssertionError("purity certificate violated")
            if satisfying_literal in clause:
                removed.append((index, clause))
            else:
                kept.append(clause)

        before_hash = digest_formula(residual)
        residual = tuple(kept)
        after_hash = digest_formula(residual)
        removed_payload = [list(clause) for _, clause in removed]
        removed_hash = hashlib.sha256(
            json.dumps(removed_payload, separators=(",", ":")).encode()
        ).hexdigest()
        certificate = {
            "variable": variable,
            "positive_occurrences": positive,
            "negative_occurrences": negative,
            "witness_value": value,
            "satisfying_literal": satisfying_literal,
            "removed_clause_count": len(removed),
            "removed_clauses_sha256": removed_hash,
            "residual_before_sha256": before_hash,
            "residual_after_sha256": after_hash,
        }
        ledger["certificate_bytes"] += len(
            json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()
        )
        ledger["clauses_removed"] += len(removed)
        ledger["witness_lift_ops"] += 1
        ledger["residual_bytes_peak"] = max(
            ledger["residual_bytes_peak"],
            len(json.dumps(residual, separators=(",", ":")).encode()),
        )
        transcript.append(certificate)

    return residual, transcript, ledger


def replay_certificate(original, transcript):
    residual = canonical_formula(original)
    witness = {}
    for step in transcript:
        counts = {}
        for clause in residual:
            for literal in clause:
                row = counts.setdefault(abs(literal), [0, 0])
                row[0 if literal > 0 else 1] += 1
        variable = step["variable"]
        if variable not in counts:
            raise AssertionError("certificate variable missing")
        positive, negative = counts[variable]
        if positive != step["positive_occurrences"] or negative != step["negative_occurrences"]:
            raise AssertionError("polarity count mismatch")
        if not ((positive == 0) ^ (negative == 0)):
            raise AssertionError("certificate variable is not pure")
        expected_value = positive > 0
        if step["witness_value"] != expected_value:
            raise AssertionError("witness value mismatch")
        sat_lit = variable if expected_value else -variable
        if any(-sat_lit in clause for clause in residual):
            raise AssertionError("opposite polarity exists")
        removed = [clause for clause in residual if sat_lit in clause]
        kept = tuple(clause for clause in residual if sat_lit not in clause)
        if len(removed) != step["removed_clause_count"]:
            raise AssertionError("removed-clause count mismatch")
        if digest_formula(residual) != step["residual_before_sha256"]:
            raise AssertionError("before hash mismatch")
        if digest_formula(kept) != step["residual_after_sha256"]:
            raise AssertionError("after hash mismatch")
        witness[variable] = expected_value
        residual = kept
    return residual, witness


def exact_optimum_for_formula(formula):
    formula = canonical_formula(formula)
    variables = sorted({abs(lit) for clause in formula for lit in clause})
    leaves = [f"v:{v}" for v in variables] + [f"c:{i}" for i in range(len(formula))]
    leaves = sorted(leaves)
    if not leaves:
        return 1, [], {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    if len(leaves) == 1:
        return 1, leaves, {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    cut_values, ledger = v11.exact_cut_cache(formula, leaves)
    optimum, order = v11.exact_optimal_order(leaves, cut_values)
    return optimum, order, ledger


def diagnostic_907000():
    formula = v9.random_connected_3cnf(
        DIAGNOSTIC_SEED,
        variable_count=VARIABLE_COUNT,
        clause_count=CLAUSE_COUNT,
    )
    residual, transcript, ledger = exact_pure_literal_projection(formula)
    replay_residual, witness = replay_certificate(formula, transcript)
    assert residual == replay_residual
    assert formula == (
        (-1, 2, -3),
        (2, 3, 4),
        (-3, -4, -5),
        (1, -5, 2),
        (-1, -2, -5),
        (1, 4, -5),
        (2, -5, -3),
    )
    assert transcript[0]["variable"] == 5
    assert transcript[0]["positive_occurrences"] == 0
    assert transcript[0]["negative_occurrences"] == 5
    assert len(residual) == 0
    return {
        "seed": DIAGNOSTIC_SEED,
        "source": [list(c) for c in formula],
        "projection_steps": transcript,
        "residual": [list(c) for c in residual],
        "witness_prefix": {str(k): v for k, v in sorted(witness.items())},
        "ledger": ledger,
        "diagnostic_used_to_select_feature": True,
    }


def run():
    diagnostic = diagnostic_907000()

    # Freeze all holdout sources before any exact before/after PS-width audit.
    frozen = []
    for seed in FROZEN_HOLDOUT_SEEDS:
        formula = v9.random_connected_3cnf(
            seed,
            variable_count=VARIABLE_COUNT,
            clause_count=CLAUSE_COUNT,
        )
        frozen.append((seed, canonical_formula(formula)))
    source_batch_sha256 = hashlib.sha256(
        json.dumps(
            [(seed, [list(c) for c in formula]) for seed, formula in frozen],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()

    # Exact polynomial reducer phase. No PS-width values are visible here.
    reduced = []
    reducer_totals = {
        "rounds": 0,
        "literal_occurrence_checks": 0,
        "clause_membership_checks": 0,
        "clauses_removed": 0,
        "certificate_bytes": 0,
        "witness_lift_ops": 0,
    }
    for seed, formula in frozen:
        residual, transcript, ledger = exact_pure_literal_projection(formula)
        replay_residual, witness = replay_certificate(formula, transcript)
        assert residual == replay_residual
        for key in reducer_totals:
            reducer_totals[key] += ledger[key]
        reduced.append(
            {
                "seed": seed,
                "formula": formula,
                "residual": residual,
                "transcript": transcript,
                "witness_prefix": witness,
                "ledger": ledger,
            }
        )

    reduction_batch_sha256 = hashlib.sha256(
        json.dumps(
            [
                (
                    row["seed"],
                    digest_formula(row["formula"]),
                    digest_formula(row["residual"]),
                    row["transcript"],
                )
                for row in reduced
            ],
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()

    # Only after all source rewrites are frozen, run the bounded exponential judge.
    rows = []
    judge_totals = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    for row in reduced:
        source_opt, source_order, source_ledger = exact_optimum_for_formula(row["formula"])
        residual_opt, residual_order, residual_ledger = exact_optimum_for_formula(row["residual"])
        for key in judge_totals:
            judge_totals[key] += source_ledger[key] + residual_ledger[key]
        rows.append(
            {
                "seed": row["seed"],
                "projection_steps": len(row["transcript"]),
                "source_variables": len(v9.variables_of(row["formula"])),
                "source_clauses": len(row["formula"]),
                "residual_variables": len(v9.variables_of(row["residual"])),
                "residual_clauses": len(row["residual"]),
                "solved_by_pure_literal_projection": len(row["residual"]) == 0,
                "source_exact_optimal_caterpillar_ps_width": source_opt,
                "residual_exact_optimal_caterpillar_ps_width": residual_opt,
                "exact_width_delta": source_opt - residual_opt,
                "source_optimal_order": source_order,
                "residual_optimal_order": residual_order,
                "certificate_sha256": hashlib.sha256(
                    json.dumps(row["transcript"], sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest(),
            }
        )

    fired = [row for row in rows if row["projection_steps"] > 0]
    solved = [row for row in rows if row["solved_by_pure_literal_projection"]]
    result = {
        "artifact_id": "PF5-PURE-LITERAL-EXACT-PROJECTION-V12",
        "status": "FINITE_BLIND_EXACT_PROJECTION_AUDIT_COMPLETE",
        "feature": "PURE_LITERAL_EXISTENTIAL_PROJECTION",
        "feature_is_heuristic": False,
        "feature_uses_sat_oracle": False,
        "feature_uses_pswidth_score": False,
        "feature_uses_truth_table": False,
        "diagnostic": diagnostic,
        "holdout_seeds_frozen_before_provider_run": FROZEN_HOLDOUT_SEEDS,
        "holdout_not_conditioned_on_feature_presence": True,
        "source_batch_frozen_before_reducer": True,
        "source_batch_sha256": source_batch_sha256,
        "all_reductions_frozen_before_exact_pswidth_judge": True,
        "reduction_batch_sha256": reduction_batch_sha256,
        "adaptive_seed_extension_after_results": False,
        "summary": {
            "cases": len(rows),
            "feature_fired_cases": len(fired),
            "feature_noop_cases": len(rows) - len(fired),
            "solved_to_empty_cases": len(solved),
            "mean_projection_steps": sum(row["projection_steps"] for row in rows) / len(rows),
            "mean_source_optimal_width": sum(row["source_exact_optimal_caterpillar_ps_width"] for row in rows) / len(rows),
            "mean_residual_optimal_width": sum(row["residual_exact_optimal_caterpillar_ps_width"] for row in rows) / len(rows),
            "positive_exact_width_delta_cases": sum(row["exact_width_delta"] > 0 for row in rows),
        },
        "rows": rows,
        "reducer_global_cost_ledger": reducer_totals,
        "exact_judge_global_cost_ledger": judge_totals,
        "exact_judge_is_exponential_audit_oracle_not_runtime_algorithm": True,
        "runtime_rule_is_polynomial_in_explicit_residual_size": True,
        "universal_semantic_decomposition_discovery": "OPEN",
        "p_vs_np": "OPEN",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = run()
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_PURE_LITERAL_EXACT_PROJECTION_V12 =", result["status"])
    print("SOURCE_BATCH_SHA256 =", result["source_batch_sha256"])
    print("REDUCTION_BATCH_SHA256 =", result["reduction_batch_sha256"])
    print("SUMMARY =", result["summary"])
    print("REDUCER_LEDGER =", result["reducer_global_cost_ledger"])
    print("EXACT_JUDGE_LEDGER =", result["exact_judge_global_cost_ledger"])
    print("PURE_LITERAL_EXISTENTIAL_PROJECTION = EXACT")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
