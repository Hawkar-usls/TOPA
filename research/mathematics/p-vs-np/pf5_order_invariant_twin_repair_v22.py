#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import pf5_clause_subsumption_contraction_v20 as v20

DIAGNOSTIC = (6, 24, 914600)
DIAGNOSTIC_BASE_SHA256 = "bde7a737b6d7f2232e5531b0b8cc0d7d0826ba4dda09166e66ccba191e634f13"
FROZEN_GROUPS = [
    (6, 24, list(range(915600, 915616))),
    (7, 28, list(range(915700, 915716))),
]


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def add_ledger(target, source):
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def semantic_clause_key(clause, ledger=None):
    unique = set()
    for literal in clause:
        if ledger is not None:
            ledger["semantic_key_literal_visits"] += 1
        unique.add(int(literal))
    if ledger is not None:
        ledger["semantic_key_builds"] += 1
    return tuple(sorted(unique, key=lambda literal: (abs(literal), literal < 0)))


def discover_and_contract_one(formula):
    residual = v20.v18.v12.canonical_formula(formula)
    before = v20.v18.v14.crystal(residual)
    ledger = {
        "variable_tests": 0,
        "failed_variable_tests": 0,
        "clause_polarity_checks": 0,
        "pair_checks": 0,
        "semantic_key_literal_visits": 0,
        "semantic_key_builds": 0,
        "existing_clause_key_checks": 0,
        "successful_contractions": 0,
        "clauses_removed": 0,
        "clauses_emitted": 0,
        "certificate_bytes": 0,
        "state_bytes_peak": before["bytes"],
        "cumulative_state_bytes": before["bytes"],
    }

    for variable in v20.v18.v13.variables_of(residual):
        ledger["variable_tests"] += 1
        positive = []
        negative = []
        for index, clause in enumerate(residual):
            ledger["clause_polarity_checks"] += 1
            if variable in clause and -variable in clause:
                raise AssertionError("tautological source clause unsupported")
            if variable in clause:
                positive.append((index, clause))
            elif -variable in clause:
                negative.append((index, clause))

        if not positive or not negative:
            ledger["failed_variable_tests"] += 1
            continue

        for positive_index, positive_clause in positive:
            positive_body = tuple(lit for lit in positive_clause if lit != variable)
            positive_key = semantic_clause_key(positive_body, ledger)
            for negative_index, negative_clause in negative:
                ledger["pair_checks"] += 1
                negative_body = tuple(lit for lit in negative_clause if lit != -variable)
                negative_key = semantic_clause_key(negative_body, ledger)
                if positive_key != negative_key:
                    continue

                kept = tuple(
                    clause
                    for index, clause in enumerate(residual)
                    if index not in (positive_index, negative_index)
                )
                already_present = False
                for clause in kept:
                    ledger["existing_clause_key_checks"] += 1
                    if semantic_clause_key(clause, ledger) == positive_key:
                        already_present = True
                        break

                emitted = kept if already_present else kept + (positive_key,)
                contracted = v20.v18.v12.canonical_formula(emitted)
                after = v20.v18.v14.crystal(contracted)
                certificate = {
                    "operator": "ORDER_INVARIANT_COMPLEMENTARY_TWIN_REPAIR",
                    "identity": "(A OR x) AND (A OR NOT x) == A",
                    "variable": variable,
                    "positive_parent_index": positive_index,
                    "negative_parent_index": negative_index,
                    "positive_parent": list(positive_clause),
                    "negative_parent": list(negative_clause),
                    "positive_body_raw": list(positive_body),
                    "negative_body_raw": list(negative_body),
                    "semantic_common_body": list(positive_key),
                    "semantic_body_sha256": digest(list(positive_key)),
                    "body_already_present_semantically": already_present,
                    "residual_before_sha256": before["sha256"],
                    "residual_after_sha256": after["sha256"],
                }
                ledger["successful_contractions"] = 1
                ledger["clauses_removed"] = 2
                ledger["clauses_emitted"] = 0 if already_present else 1
                ledger["certificate_bytes"] = len(
                    json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()
                )
                ledger["state_bytes_peak"] = max(
                    ledger["state_bytes_peak"], after["bytes"]
                )
                ledger["cumulative_state_bytes"] += after["bytes"]
                return contracted, certificate, ledger

        ledger["failed_variable_tests"] += 1

    return residual, None, ledger


def certificate_is_semantically_valid(certificate):
    variable = certificate["variable"]
    positive_parent = tuple(certificate["positive_parent"])
    negative_parent = tuple(certificate["negative_parent"])
    if variable not in positive_parent or -variable not in negative_parent:
        return False
    positive_body = tuple(lit for lit in positive_parent if lit != variable)
    negative_body = tuple(lit for lit in negative_parent if lit != -variable)
    return (
        semantic_clause_key(positive_body)
        == semantic_clause_key(negative_body)
        == tuple(certificate["semantic_common_body"])
    )


def replay_repair(formula, certificate):
    residual, found, _ = discover_and_contract_one(formula)
    if found is None or found != certificate:
        raise AssertionError("order-invariant twin certificate mismatch")
    if not certificate_is_semantically_valid(found):
        raise AssertionError("invalid order-invariant twin certificate")
    return residual


def exact_closure(formula):
    residual = v20.v18.v12.canonical_formula(formula)
    transcript = []
    ledger = {"v13": {}, "v15": {}, "v18": {}, "v20": {}, "v22": {}}

    while True:
        reduced, inherited_transcript, inherited_ledger = v20.exact_closure(residual)
        transcript.extend(inherited_transcript)
        for lane in ("v13", "v15", "v18", "v20"):
            add_ledger(ledger[lane], inherited_ledger[lane])
        residual = reduced

        contracted, certificate, local = discover_and_contract_one(residual)
        add_ledger(ledger["v22"], local)
        if certificate is None:
            break
        transcript.append({"kind": "ORDER_INVARIANT_TWIN", "certificate": certificate})
        residual = contracted

    return residual, transcript, ledger


def replay(original, transcript):
    residual = v20.v18.v12.canonical_formula(original)
    for entry in transcript:
        kind = entry["kind"]
        if kind == "PURE_LITERAL":
            residual, _ = v20.v18.v12.replay_certificate(
                residual, [entry["certificate"]]
            )
        elif kind == "TAUTOLOGICAL_RESOLVENT":
            residual = v20.v18.v13.replay_tr_certificate(residual, entry["certificate"])
        elif kind == "SINGLE_RESOLVENT":
            residual = v20.v18.v15.replay_single(residual, entry["certificate"])
        elif kind == "COMPLEMENTARY_TWIN":
            residual = v20.v18.replay_twin(residual, entry["certificate"])
        elif kind == "CLAUSE_SUBSUMPTION":
            residual = v20.replay_subsumption(residual, entry["certificate"])
        elif kind == "ORDER_INVARIANT_TWIN":
            residual = replay_repair(residual, entry["certificate"])
        else:
            raise AssertionError(f"unknown transcript kind: {kind}")
    return residual


def lift_witness(original, final_residual, transcript, final_assignment):
    # v22 is a pointwise equivalence, so only projection steps need reverse lifts.
    without_v22 = [
        entry for entry in transcript if entry["kind"] != "ORDER_INVARIANT_TWIN"
    ]
    return v20.lift_witness(original, final_residual, without_v22, final_assignment)


def semantic_audit(source, residual, transcript):
    source_variables = v20.v18.v13.variables_of(source)
    residual_variables = v20.v18.v13.variables_of(residual)
    ledger = {
        "source_assignment_rows": 0,
        "residual_assignment_rows": 0,
        "literal_checks": 0,
        "witness_lift_calls": 0,
        "witness_lift_ops": 0,
    }

    projected = set()
    for bits in itertools.product((False, True), repeat=len(source_variables)):
        ledger["source_assignment_rows"] += 1
        assignment = dict(zip(source_variables, bits))
        if v20.v18.v13.formula_true(source, assignment, ledger):
            projected.add(tuple(assignment[v] for v in residual_variables))

    models = set()
    for bits in itertools.product((False, True), repeat=len(residual_variables)):
        ledger["residual_assignment_rows"] += 1
        assignment = dict(zip(residual_variables, bits))
        if v20.v18.v13.formula_true(residual, assignment, ledger):
            models.add(bits)
            _, lift_ledger = lift_witness(source, residual, transcript, assignment)
            ledger["witness_lift_calls"] += 1
            ledger["witness_lift_ops"] += sum(lift_ledger.values())

    return projected == models, ledger


def terminal_status(residual):
    if residual == ():
        return "TRUE"
    if any(len(clause) == 0 for clause in residual):
        return "FALSE"
    return "OPEN_RESIDUAL"


def count_kind(transcript, kind):
    return sum(entry["kind"] == kind for entry in transcript)


def has_semantic_twin(formula):
    _, certificate, _ = discover_and_contract_one(formula)
    return certificate is not None


def run():
    # Diagnostic is already inspected; use it only to verify the repair contract.
    n, m, seed = DIAGNOSTIC
    diagnostic_source = v20.v18.v9.random_connected_3cnf(
        seed, variable_count=n, clause_count=m
    )
    diagnostic_base, _, _ = v20.exact_closure(diagnostic_source)
    assert v20.v18.v14.crystal(diagnostic_base)["sha256"] == DIAGNOSTIC_BASE_SHA256
    _, diagnostic_first_certificate, _ = discover_and_contract_one(diagnostic_base)
    assert diagnostic_first_certificate is not None
    assert certificate_is_semantically_valid(diagnostic_first_certificate)

    diagnostic_final, diagnostic_transcript, _ = exact_closure(diagnostic_source)
    assert replay(diagnostic_source, diagnostic_transcript) == diagnostic_final
    assert not has_semantic_twin(diagnostic_final)
    diagnostic_ok, _ = semantic_audit(
        diagnostic_source, diagnostic_final, diagnostic_transcript
    )
    assert diagnostic_ok
    diagnostic = {
        "n": n,
        "m": m,
        "seed": seed,
        "role": "DIAGNOSTIC_ONLY_NOT_BLIND",
        "base_crystal": v20.v18.v14.crystal(diagnostic_base),
        "first_v22_certificate": diagnostic_first_certificate,
        "final_crystal": v20.v18.v14.crystal(diagnostic_final),
        "terminal_status": terminal_status(diagnostic_final),
        "semantic_twin_remaining": False,
        "semantic_audit_pass": True,
    }

    # Phase 1: materialize/hash every pre-frozen source before provider reduction.
    frozen_sources = []
    for n, m, seeds in FROZEN_GROUPS:
        for seed in seeds:
            source = v20.v18.v12.canonical_formula(
                v20.v18.v9.random_connected_3cnf(
                    seed, variable_count=n, clause_count=m
                )
            )
            frozen_sources.append(
                {
                    "n": n,
                    "m": m,
                    "seed": seed,
                    "source": source,
                    "source_crystal": v20.v18.v14.crystal(source),
                }
            )
    source_manifest_sha256 = digest(
        [
            (row["n"], row["m"], row["seed"], row["source_crystal"]["sha256"])
            for row in frozen_sources
        ]
    )

    # Phase 2: freeze all v20 baselines and v22 outputs before semantic audit.
    frozen = []
    for item in frozen_sources:
        baseline, _, _ = v20.exact_closure(item["source"])
        baseline_had_missed_twin = has_semantic_twin(baseline)
        final, transcript, runtime = exact_closure(item["source"])
        assert replay(item["source"], transcript) == final
        assert not has_semantic_twin(final)
        frozen.append(
            {
                **item,
                "baseline": baseline,
                "baseline_had_missed_twin": baseline_had_missed_twin,
                "final": final,
                "transcript": transcript,
                "runtime": runtime,
            }
        )

    reduction_batch_sha256 = digest(
        [
            (
                row["n"],
                row["m"],
                row["seed"],
                v20.v18.v14.crystal(row["baseline"])["sha256"],
                row["baseline_had_missed_twin"],
                v20.v18.v14.crystal(row["final"])["sha256"],
                row["transcript"],
            )
            for row in frozen
        ]
    )

    # Phase 3: bounded exhaustive audit after every output is frozen.
    rows = []
    runtime_total = {"v13": {}, "v15": {}, "v18": {}, "v20": {}, "v22": {}}
    audit_total = {}
    seen = {}
    revisits = 0
    for item in frozen:
        ok, audit = semantic_audit(item["source"], item["final"], item["transcript"])
        assert ok
        add_ledger(audit_total, audit)
        for lane in runtime_total:
            add_ledger(runtime_total[lane], item["runtime"][lane])

        baseline_crystal = v20.v18.v14.crystal(item["baseline"])
        final_crystal = v20.v18.v14.crystal(item["final"])
        prior = seen.get(final_crystal["sha256"])
        revisit = prior is not None and prior["canonical_cnf"] == final_crystal["canonical_cnf"]
        if revisit:
            revisits += 1
        else:
            seen[final_crystal["sha256"]] = final_crystal

        steps = count_kind(item["transcript"], "ORDER_INVARIANT_TWIN")
        rows.append(
            {
                "n": item["n"],
                "m": item["m"],
                "seed": item["seed"],
                "source_crystal_sha256": item["source_crystal"]["sha256"],
                "baseline_crystal_sha256": baseline_crystal["sha256"],
                "final_crystal_sha256": final_crystal["sha256"],
                "baseline_had_missed_semantic_twin": item["baseline_had_missed_twin"],
                "baseline_bytes": baseline_crystal["bytes"],
                "final_bytes": final_crystal["bytes"],
                "v22_steps": steps,
                "feature_fired": steps > 0,
                "terminal_status": terminal_status(item["final"]),
                "semantic_twin_remaining": False,
                "semantic_audit_pass": True,
                "exact_final_revisit": revisit,
            }
        )

    fired = [row for row in rows if row["feature_fired"]]
    result = {
        "artifact_id": "PF5-ORDER-INVARIANT-TWIN-REPAIR-V22",
        "status": "FINITE_FRESH_BLIND_IMPLEMENTATION_REPAIR_AUDIT_COMPLETE",
        "protocol_receipt": "data/PF5-V22-FROZEN-ORDER-INVARIANT-TWIN-REPAIR-PROTOCOL.json",
        "parent_gap": "data/PF5-V18-002-BODY-ORDER-SENSITIVITY.json",
        "repair_type": "IMPLEMENTATION_REPAIR_OF_EXISTING_EXACT_THEOREM",
        "feature": "ORDER_INVARIANT_COMPLEMENTARY_TWIN_REPAIR",
        "feature_identity": "(A OR x) AND (A OR NOT x) == A",
        "theorem_changed": False,
        "feature_is_heuristic": False,
        "diagnostic": diagnostic,
        "frozen_groups": [
            {"n": n, "m": m, "seeds": seeds} for n, m, seeds in FROZEN_GROUPS
        ],
        "case_count": len(rows),
        "all_sources_frozen_before_provider_reduction": True,
        "all_provider_outputs_frozen_before_semantic_audit": True,
        "holdout_not_conditioned_on_feature_presence": True,
        "adaptive_extension_after_results": False,
        "source_manifest_sha256": source_manifest_sha256,
        "reduction_batch_sha256": reduction_batch_sha256,
        "decision_heuristic": False,
        "uses_sat_oracle": False,
        "uses_truth_table_in_runtime": False,
        "uses_pswidth_score": False,
        "uses_hephaestus_for_decision": False,
        "runtime_rule_polynomial_in_explicit_residual_size": True,
        "witness_lift_replayable_from_certificate": True,
        "summary": {
            "cases": len(rows),
            "baseline_cases_with_missed_semantic_twin": sum(
                row["baseline_had_missed_semantic_twin"] for row in rows
            ),
            "feature_fired_cases": len(fired),
            "feature_noop_cases": len(rows) - len(fired),
            "total_v22_steps": sum(row["v22_steps"] for row in rows),
            "terminal_true_cases": sum(row["terminal_status"] == "TRUE" for row in rows),
            "terminal_false_cases": sum(row["terminal_status"] == "FALSE" for row in rows),
            "open_residual_cases": sum(row["terminal_status"] == "OPEN_RESIDUAL" for row in rows),
            "positive_byte_delta_cases": sum(row["baseline_bytes"] > row["final_bytes"] for row in rows),
            "mean_baseline_crystal_bytes": sum(row["baseline_bytes"] for row in rows) / len(rows),
            "mean_final_crystal_bytes": sum(row["final_bytes"] for row in rows) / len(rows),
            "all_semantic_audits_pass": all(row["semantic_audit_pass"] for row in rows),
            "all_final_residuals_semantic_twin_free": all(
                not row["semantic_twin_remaining"] for row in rows
            ),
            "exact_final_revisits": revisits,
        },
        "rows": rows,
        "runtime_discovery_ledger": runtime_total,
        "finite_semantic_audit_ledger": audit_total,
        "hephaestus_role": "ACCOUNTING_RECURRENCE_ONLY_NO_DECISION_AUTHORITY",
        "universal_exact_closure": "OPEN",
        "next_gate": "FIRST_RESIDUAL_SURVIVING_V12_V13_V15_V18_V20_V22",
        "p_vs_np": "OPEN",
    }
    result["result_sha256"] = digest(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = run()
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_ORDER_INVARIANT_TWIN_REPAIR_V22 =", result["status"])
    print("SOURCE_MANIFEST_SHA256 =", result["source_manifest_sha256"])
    print("REDUCTION_BATCH_SHA256 =", result["reduction_batch_sha256"])
    print("SUMMARY =", result["summary"])
    print("RUNTIME_LEDGER =", result["runtime_discovery_ledger"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
