#!/usr/bin/env python3
"""PF5 v13 exact tautological-resolvent existential projection.

The new runtime rule is not heuristic.  It scans the explicit CNF and applies
one exact Davis–Putnam special case only when every positive×negative resolvent
of a variable is tautological.  No SAT, PS-width, truth table, Slime trace, or
candidate score is visible to the reducer.

Bounded exponential semantic/PS-width checks occur only after all blind source
reductions have been frozen and are audit oracles, not runtime algorithms.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_pure_literal_exact_projection_v12 as v12

DIAGNOSTIC_SEED = 907003
FROZEN_HOLDOUT_SEEDS = list(range(909000, 909032))
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7


def digest_payload(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def digest_formula(formula):
    return v12.digest_formula(v12.canonical_formula(formula))


def literal_order(literal):
    return (abs(literal), literal < 0)


def variables_of(formula):
    return sorted({abs(literal) for clause in formula for literal in clause})


def clause_true(clause, assignment, ledger=None):
    for literal in clause:
        if ledger is not None:
            ledger["literal_checks"] += 1
        variable = abs(literal)
        if variable not in assignment:
            raise AssertionError(f"assignment missing variable {variable}")
        if assignment[variable] == (literal > 0):
            return True
    return False


def formula_true(formula, assignment, ledger=None):
    return all(clause_true(clause, assignment, ledger) for clause in formula)


def tautology_witness(positive_body, negative_body, ledger):
    negative_set = set(negative_body)
    for literal in sorted(positive_body, key=literal_order):
        ledger["complement_literal_checks"] += 1
        if -literal in negative_set:
            return literal
    return None


def discover_and_project_one(formula):
    """Return exact projected residual, certificate-or-None, charged ledger.

    Acceptance is exactly the theorem premise: both polarities occur and every
    positive×negative resolvent is tautological.  Variables are scanned in
    increasing numeric order.  Failed theorem tests are charged.
    """
    residual = v12.canonical_formula(formula)
    ledger = {
        "variable_tests": 0,
        "failed_variable_tests": 0,
        "clause_polarity_checks": 0,
        "pair_checks": 0,
        "complement_literal_checks": 0,
        "successful_projections": 0,
        "clauses_removed": 0,
        "certificate_bytes": 0,
        "residual_bytes_peak": len(
            json.dumps(residual, separators=(",", ":")).encode()
        ),
    }

    for variable in variables_of(residual):
        ledger["variable_tests"] += 1
        positive = []
        negative = []
        for index, clause in enumerate(residual):
            ledger["clause_polarity_checks"] += 1
            if variable in clause and -variable in clause:
                raise AssertionError("tautological source clause not supported")
            if variable in clause:
                positive.append((index, clause))
            elif -variable in clause:
                negative.append((index, clause))

        # Pure variables belong to the already-admitted v12 rule and are not
        # claimed as v13 successes.
        if not positive or not negative:
            ledger["failed_variable_tests"] += 1
            continue

        pair_certificates = []
        all_tautological = True
        for positive_index, positive_clause in positive:
            positive_body = tuple(lit for lit in positive_clause if lit != variable)
            for negative_index, negative_clause in negative:
                ledger["pair_checks"] += 1
                negative_body = tuple(
                    lit for lit in negative_clause if lit != -variable
                )
                witness = tautology_witness(
                    positive_body, negative_body, ledger
                )
                if witness is None:
                    all_tautological = False
                    break
                pair_certificates.append(
                    {
                        "positive_clause_index": positive_index,
                        "negative_clause_index": negative_index,
                        "witness_literal_in_positive_body": witness,
                        "complement_in_negative_body": -witness,
                    }
                )
            if not all_tautological:
                break

        if not all_tautological:
            ledger["failed_variable_tests"] += 1
            continue

        removed = [
            clause
            for clause in residual
            if variable in clause or -variable in clause
        ]
        kept = tuple(
            clause
            for clause in residual
            if variable not in clause and -variable not in clause
        )
        if not removed:
            raise AssertionError("successful projection removed no clauses")

        certificate = {
            "operator": "TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION",
            "variable": variable,
            "positive_parent_count": len(positive),
            "negative_parent_count": len(negative),
            "cross_pair_count": len(positive) * len(negative),
            "all_cross_resolvents_tautological": True,
            "pair_certificates": pair_certificates,
            "removed_clauses": [list(clause) for clause in removed],
            "removed_clauses_sha256": digest_payload(
                [list(clause) for clause in removed]
            ),
            "residual_before_sha256": digest_formula(residual),
            "residual_after_sha256": digest_formula(kept),
        }
        if len(pair_certificates) != certificate["cross_pair_count"]:
            raise AssertionError("missing tautological-resolvent pair certificate")

        ledger["successful_projections"] = 1
        ledger["clauses_removed"] = len(removed)
        ledger["certificate_bytes"] = len(
            json.dumps(
                certificate, sort_keys=True, separators=(",", ":")
            ).encode()
        )
        ledger["residual_bytes_peak"] = max(
            ledger["residual_bytes_peak"],
            len(json.dumps(kept, separators=(",", ":")).encode()),
        )
        return kept, certificate, ledger

    return residual, None, ledger


def replay_tr_certificate(formula, certificate):
    expected_residual, expected_certificate, _ = discover_and_project_one(formula)
    if expected_certificate is None:
        raise AssertionError("certificate claims projection where theorem gate fails")
    if expected_certificate != certificate:
        raise AssertionError("tautological-resolvent certificate mismatch")
    return expected_residual


def add_ledgers(target, source):
    for key, value in source.items():
        if key == "residual_bytes_peak":
            target[key] = max(target.get(key, 0), value)
        else:
            target[key] = target.get(key, 0) + value


def exact_composed_closure(formula):
    """v12 pure closure <-> v13 exact tautological-resolvent closure."""
    residual = v12.canonical_formula(formula)
    transcript = []
    pure_total = {
        "rounds": 0,
        "literal_occurrence_checks": 0,
        "clause_membership_checks": 0,
        "clauses_removed": 0,
        "certificate_bytes": 0,
        "residual_bytes_peak": 0,
        "witness_lift_ops": 0,
    }
    tr_total = {
        "variable_tests": 0,
        "failed_variable_tests": 0,
        "clause_polarity_checks": 0,
        "pair_checks": 0,
        "complement_literal_checks": 0,
        "successful_projections": 0,
        "clauses_removed": 0,
        "certificate_bytes": 0,
        "residual_bytes_peak": 0,
    }

    while True:
        pure_residual, pure_transcript, pure_ledger = (
            v12.exact_pure_literal_projection(residual)
        )
        add_ledgers(pure_total, pure_ledger)
        for certificate in pure_transcript:
            transcript.append(
                {"kind": "PURE_LITERAL", "certificate": certificate}
            )
        residual = pure_residual

        tr_residual, tr_certificate, tr_ledger = discover_and_project_one(residual)
        add_ledgers(tr_total, tr_ledger)
        if tr_certificate is None:
            break
        transcript.append(
            {
                "kind": "TAUTOLOGICAL_RESOLVENT",
                "certificate": tr_certificate,
            }
        )
        residual = tr_residual

    return residual, transcript, {"pure": pure_total, "tr": tr_total}


def replay_composed(original, transcript):
    residual = v12.canonical_formula(original)
    for entry in transcript:
        if entry["kind"] == "PURE_LITERAL":
            residual, _ = v12.replay_certificate(
                residual, [entry["certificate"]]
            )
        elif entry["kind"] == "TAUTOLOGICAL_RESOLVENT":
            residual = replay_tr_certificate(residual, entry["certificate"])
        else:
            raise AssertionError("unknown transcript kind")
    return residual


def body_false(clause, removed_literal, assignment, ledger):
    for literal in clause:
        if literal == removed_literal:
            continue
        ledger["literal_checks"] += 1
        variable = abs(literal)
        if variable not in assignment:
            raise AssertionError(f"lift missing variable {variable}")
        if assignment[variable] == (literal > 0):
            return False
    return True


def lift_witness(original, final_residual, transcript, final_assignment):
    ledger = {
        "projection_steps_reversed": 0,
        "removed_clause_checks": 0,
        "literal_checks": 0,
        "assignments_restored": 0,
    }
    assignment = dict(final_assignment)
    if not formula_true(final_residual, assignment, ledger):
        raise AssertionError("supplied residual witness does not satisfy residual")

    for entry in reversed(transcript):
        ledger["projection_steps_reversed"] += 1
        certificate = entry["certificate"]
        variable = certificate["variable"]
        if entry["kind"] == "PURE_LITERAL":
            assignment[variable] = bool(certificate["witness_value"])
            ledger["assignments_restored"] += 1
            continue

        positive_requires_true = False
        negative_requires_false = False
        for clause_as_list in certificate["removed_clauses"]:
            clause = tuple(clause_as_list)
            ledger["removed_clause_checks"] += 1
            if variable in clause:
                if body_false(clause, variable, assignment, ledger):
                    positive_requires_true = True
            elif -variable in clause:
                if body_false(clause, -variable, assignment, ledger):
                    negative_requires_false = True
            else:
                raise AssertionError("removed clause lacks projected variable")
        if positive_requires_true and negative_requires_false:
            raise AssertionError("tautological-resolvent proof failed witness lift")
        assignment[variable] = True if positive_requires_true else False
        ledger["assignments_restored"] += 1

    if not formula_true(original, assignment, ledger):
        raise AssertionError("lifted witness does not satisfy source")
    return assignment, ledger


def exact_semantic_projection_audit(source, residual, transcript):
    """Finite exhaustive verifier only; never called by the runtime reducer."""
    source = v12.canonical_formula(source)
    residual = v12.canonical_formula(residual)
    source_variables = variables_of(source)
    residual_variables = variables_of(residual)
    ledger = {
        "source_assignment_rows": 0,
        "residual_assignment_rows": 0,
        "literal_checks": 0,
        "witness_lift_calls": 0,
        "witness_lift_ops": 0,
    }

    projected_source_models = set()
    for bits in itertools.product((False, True), repeat=len(source_variables)):
        ledger["source_assignment_rows"] += 1
        assignment = dict(zip(source_variables, bits))
        if formula_true(source, assignment, ledger):
            projected_source_models.add(
                tuple(assignment[v] for v in residual_variables)
            )

    residual_models = set()
    for bits in itertools.product((False, True), repeat=len(residual_variables)):
        ledger["residual_assignment_rows"] += 1
        assignment = dict(zip(residual_variables, bits))
        if formula_true(residual, assignment, ledger):
            residual_models.add(bits)
            _, lift_ledger = lift_witness(
                source, residual, transcript, assignment
            )
            ledger["witness_lift_calls"] += 1
            ledger["witness_lift_ops"] += (
                lift_ledger["projection_steps_reversed"]
                + lift_ledger["removed_clause_checks"]
                + lift_ledger["literal_checks"]
                + lift_ledger["assignments_restored"]
            )

    return projected_source_models == residual_models, ledger


def count_kind(transcript, kind):
    return sum(entry["kind"] == kind for entry in transcript)


def diagnostic_907003():
    formula = v9.random_connected_3cnf(
        DIAGNOSTIC_SEED,
        variable_count=VARIABLE_COUNT,
        clause_count=CLAUSE_COUNT,
    )
    assert formula == (
        (-1, 2, 3),
        (-2, 3, -4),
        (-3, 4, -5),
        (-5, 1, -2),
        (2, -4, 5),
        (-5, -1, 2),
        (1, 5, -2),
    )

    pure_residual, pure_transcript, _ = v12.exact_pure_literal_projection(formula)
    assert pure_residual == formula
    assert pure_transcript == []

    residual, transcript, ledger = exact_composed_closure(formula)
    replayed = replay_composed(formula, transcript)
    assert residual == replayed
    tr_entries = [
        entry for entry in transcript if entry["kind"] == "TAUTOLOGICAL_RESOLVENT"
    ]
    assert [entry["certificate"]["variable"] for entry in tr_entries[:2]] == [1, 3]
    first = tr_entries[0]["certificate"]
    assert first["positive_parent_count"] == 2
    assert first["negative_parent_count"] == 2
    assert first["cross_pair_count"] == 4
    assert len(first["pair_certificates"]) == 4
    assert residual == ()

    semantic_ok, semantic_ledger = exact_semantic_projection_audit(
        formula, residual, transcript
    )
    assert semantic_ok
    return {
        "seed": DIAGNOSTIC_SEED,
        "source": [list(clause) for clause in formula],
        "pure_only_residual": [list(clause) for clause in pure_residual],
        "pure_only_is_noop": True,
        "composed_residual": [list(clause) for clause in residual],
        "transcript": transcript,
        "tautological_resolvent_steps": count_kind(
            transcript, "TAUTOLOGICAL_RESOLVENT"
        ),
        "pure_literal_steps_after_new_projection": count_kind(
            transcript, "PURE_LITERAL"
        ),
        "runtime_ledger": ledger,
        "semantic_audit_pass": semantic_ok,
        "semantic_audit_ledger": semantic_ledger,
        "diagnostic_used_only_to_select_exact_theorem_rule": True,
    }


def run():
    diagnostic = diagnostic_907003()

    # PHASE 1: freeze every blind source before any source reduction result is
    # inspected by the exact judge.
    frozen_sources = []
    for seed in FROZEN_HOLDOUT_SEEDS:
        formula = v9.random_connected_3cnf(
            seed,
            variable_count=VARIABLE_COUNT,
            clause_count=CLAUSE_COUNT,
        )
        frozen_sources.append((seed, v12.canonical_formula(formula)))
    source_batch_sha256 = digest_payload(
        [
            (seed, [list(clause) for clause in formula])
            for seed, formula in frozen_sources
        ]
    )

    # PHASE 2a: freeze the already-admitted v12 pure-only baseline.
    pure_rows = []
    pure_batch = []
    for seed, formula in frozen_sources:
        residual, transcript, ledger = v12.exact_pure_literal_projection(formula)
        replayed, _ = v12.replay_certificate(formula, transcript)
        assert residual == replayed
        pure_rows.append(
            {
                "seed": seed,
                "source": formula,
                "residual": residual,
                "transcript": transcript,
                "ledger": ledger,
            }
        )
        pure_batch.append(
            (
                seed,
                digest_formula(formula),
                digest_formula(residual),
                transcript,
            )
        )
    pure_batch_sha256 = digest_payload(pure_batch)

    # PHASE 2b: independently freeze the composed exact v12+v13 closure. No
    # PS-width or satisfiability oracle is available in this phase.
    composed_rows = []
    composed_batch = []
    runtime_totals = {"pure": {}, "tr": {}}
    for seed, formula in frozen_sources:
        residual, transcript, ledger = exact_composed_closure(formula)
        replayed = replay_composed(formula, transcript)
        assert residual == replayed
        add_ledgers(runtime_totals["pure"], ledger["pure"])
        add_ledgers(runtime_totals["tr"], ledger["tr"])
        composed_rows.append(
            {
                "seed": seed,
                "source": formula,
                "residual": residual,
                "transcript": transcript,
                "ledger": ledger,
            }
        )
        composed_batch.append(
            (
                seed,
                digest_formula(formula),
                digest_formula(residual),
                transcript,
            )
        )
    composed_batch_sha256 = digest_payload(composed_batch)

    # PHASE 3: only now may bounded exponential audit oracles inspect the
    # frozen residuals.
    exact_ps_totals = {"cuts": 0, "assignment_rows": 0, "literal_checks": 0}
    semantic_totals = {
        "source_assignment_rows": 0,
        "residual_assignment_rows": 0,
        "literal_checks": 0,
        "witness_lift_calls": 0,
        "witness_lift_ops": 0,
    }
    rows = []
    pure_by_seed = {row["seed"]: row for row in pure_rows}
    for composed in composed_rows:
        seed = composed["seed"]
        pure = pure_by_seed[seed]
        pure_opt, _, pure_opt_ledger = v12.exact_optimum_for_formula(
            pure["residual"]
        )
        composed_opt, _, composed_opt_ledger = v12.exact_optimum_for_formula(
            composed["residual"]
        )
        for key in exact_ps_totals:
            exact_ps_totals[key] += pure_opt_ledger[key] + composed_opt_ledger[key]

        semantic_ok, semantic_ledger = exact_semantic_projection_audit(
            composed["source"], composed["residual"], composed["transcript"]
        )
        if not semantic_ok:
            raise AssertionError(f"semantic projection audit failed for seed {seed}")
        for key in semantic_totals:
            semantic_totals[key] += semantic_ledger[key]

        tr_steps = count_kind(
            composed["transcript"], "TAUTOLOGICAL_RESOLVENT"
        )
        rows.append(
            {
                "seed": seed,
                "pure_only_residual_clauses": len(pure["residual"]),
                "composed_residual_clauses": len(composed["residual"]),
                "pure_only_solved_to_empty": len(pure["residual"]) == 0,
                "composed_solved_to_empty": len(composed["residual"]) == 0,
                "tautological_resolvent_steps": tr_steps,
                "pure_steps_in_composed_closure": count_kind(
                    composed["transcript"], "PURE_LITERAL"
                ),
                "new_operator_fired": tr_steps > 0,
                "pure_only_exact_optimal_caterpillar_ps_width": pure_opt,
                "composed_exact_optimal_caterpillar_ps_width": composed_opt,
                "incremental_exact_width_delta": pure_opt - composed_opt,
                "semantic_projection_audit_pass": semantic_ok,
                "composed_certificate_sha256": digest_payload(
                    composed["transcript"]
                ),
            }
        )

    fired = [row for row in rows if row["new_operator_fired"]]
    result = {
        "artifact_id": "PF5-TAUTOLOGICAL-RESOLVENT-EXACT-PROJECTION-V13",
        "status": "FINITE_BLIND_EXACT_PROJECTION_AUDIT_COMPLETE",
        "new_feature": "TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION",
        "new_feature_is_heuristic": False,
        "new_feature_uses_slime": False,
        "new_feature_uses_sat_oracle": False,
        "new_feature_uses_pswidth_score": False,
        "new_feature_uses_truth_table": False,
        "new_feature_acceptance_predicate": (
            "BOTH_POLARITIES_AND_EVERY_POSITIVE_X_NEGATIVE_RESOLVENT_TAUTOLOGICAL"
        ),
        "diagnostic": diagnostic,
        "holdout_seeds_frozen_before_provider_run": FROZEN_HOLDOUT_SEEDS,
        "holdout_not_conditioned_on_feature_presence": True,
        "source_batch_frozen_before_reducer": True,
        "source_batch_sha256": source_batch_sha256,
        "pure_only_batch_frozen_before_composed_reducer": True,
        "pure_only_batch_sha256": pure_batch_sha256,
        "all_composed_reductions_frozen_before_exact_judges": True,
        "composed_reduction_batch_sha256": composed_batch_sha256,
        "adaptive_seed_extension_after_results": False,
        "summary": {
            "cases": len(rows),
            "new_feature_fired_cases": len(fired),
            "new_feature_noop_cases": len(rows) - len(fired),
            "tautological_resolvent_projection_steps": sum(
                row["tautological_resolvent_steps"] for row in rows
            ),
            "pure_only_solved_to_empty_cases": sum(
                row["pure_only_solved_to_empty"] for row in rows
            ),
            "composed_solved_to_empty_cases": sum(
                row["composed_solved_to_empty"] for row in rows
            ),
            "incremental_solved_to_empty_cases": sum(
                row["composed_solved_to_empty"]
                and not row["pure_only_solved_to_empty"]
                for row in rows
            ),
            "positive_incremental_exact_width_delta_cases": sum(
                row["incremental_exact_width_delta"] > 0 for row in rows
            ),
            "mean_pure_only_optimal_width": sum(
                row["pure_only_exact_optimal_caterpillar_ps_width"]
                for row in rows
            ) / len(rows),
            "mean_composed_optimal_width": sum(
                row["composed_exact_optimal_caterpillar_ps_width"]
                for row in rows
            ) / len(rows),
            "all_semantic_projection_audits_pass": all(
                row["semantic_projection_audit_pass"] for row in rows
            ),
        },
        "rows": rows,
        "runtime_global_cost_ledger": runtime_totals,
        "exact_pswidth_judge_global_cost_ledger": exact_ps_totals,
        "semantic_projection_audit_global_cost_ledger": semantic_totals,
        "runtime_rule_is_polynomial_in_explicit_residual_size": True,
        "exact_pswidth_judge_is_exponential_audit_oracle_not_runtime_algorithm": True,
        "semantic_truth_table_is_exponential_audit_oracle_not_runtime_algorithm": True,
        "witness_lift_is_replayable_from_certificate_given_residual_witness": True,
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
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )
    print("PF5_TAUTOLOGICAL_RESOLVENT_V13 =", result["status"])
    print("SOURCE_BATCH_SHA256 =", result["source_batch_sha256"])
    print("PURE_ONLY_BATCH_SHA256 =", result["pure_only_batch_sha256"])
    print(
        "COMPOSED_REDUCTION_BATCH_SHA256 =",
        result["composed_reduction_batch_sha256"],
    )
    print("SUMMARY =", result["summary"])
    print("RUNTIME_LEDGER =", result["runtime_global_cost_ledger"])
    print("EXACT_PSWIDTH_JUDGE_LEDGER =", result["exact_pswidth_judge_global_cost_ledger"])
    print("SEMANTIC_AUDIT_LEDGER =", result["semantic_projection_audit_global_cost_ledger"])
    print("TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION = EXACT")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
