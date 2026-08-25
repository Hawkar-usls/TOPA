#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import pf5_order_invariant_twin_repair_v22 as v22

DIAGNOSTIC = (6, 24, 915600)
DIAGNOSTIC_BASE_SHA256 = "e16d4ee3a5fbbfacf4004b8323c4cc9900e9a3567d5c376034d805c508bb8863"
FROZEN_GROUPS = [
    (6, 24, list(range(916600, 916616))),
    (7, 28, list(range(916700, 916716))),
]


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def add_ledger(target, source):
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def semantic_key(clause, ledger=None):
    values = set()
    for literal in clause:
        if ledger is not None:
            ledger["semantic_key_literal_visits"] += 1
        values.add(int(literal))
    return tuple(sorted(values, key=lambda literal: (abs(literal), literal < 0)))


def strict_subset(left, right, ledger):
    if len(left) >= len(right):
        return False
    right_set = set(right)
    for literal in left:
        ledger["subset_literal_checks"] += 1
        if literal not in right_set:
            return False
    return True


def discover_and_contract_one(formula):
    residual = v22.v20.v18.v12.canonical_formula(formula)
    before = v22.v20.v18.v14.crystal(residual)
    ledger = {
        "variable_tests": 0,
        "failed_variable_tests": 0,
        "clause_polarity_checks": 0,
        "pair_checks": 0,
        "semantic_key_literal_visits": 0,
        "subset_literal_checks": 0,
        "successful_contractions": 0,
        "clauses_replaced": 0,
        "certificate_bytes": 0,
        "state_bytes_peak": before["bytes"],
        "cumulative_state_bytes": before["bytes"],
    }

    for variable in v22.v20.v18.v13.variables_of(residual):
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

        found_for_variable = False
        for positive_index, positive_clause in positive:
            positive_body_raw = tuple(
                literal for literal in positive_clause if literal != variable
            )
            positive_body = semantic_key(positive_body_raw, ledger)
            for negative_index, negative_clause in negative:
                ledger["pair_checks"] += 1
                negative_body_raw = tuple(
                    literal for literal in negative_clause if literal != -variable
                )
                negative_body = semantic_key(negative_body_raw, ledger)

                # Equality belongs to v22, not v24.  v24 is strict SSR only.
                if strict_subset(positive_body, negative_body, ledger):
                    replace_index = negative_index
                    replacement = negative_body
                    orientation = "POSITIVE_BODY_STRICT_SUBSET_NEGATIVE_BODY"
                elif strict_subset(negative_body, positive_body, ledger):
                    replace_index = positive_index
                    replacement = positive_body
                    orientation = "NEGATIVE_BODY_STRICT_SUBSET_POSITIVE_BODY"
                else:
                    continue

                rewritten = tuple(
                    replacement if index == replace_index else clause
                    for index, clause in enumerate(residual)
                )
                contracted = v22.v20.v18.v12.canonical_formula(rewritten)
                after = v22.v20.v18.v14.crystal(contracted)
                certificate = {
                    "operator": "SELF_SUBSUMING_RESOLUTION_CONTRACTION",
                    "identity": "If C+=(x OR A), C-=(NOT x OR B), A strict-subset B then replace C- by B; symmetric for B strict-subset A",
                    "variable": variable,
                    "positive_parent_index": positive_index,
                    "negative_parent_index": negative_index,
                    "positive_parent": list(positive_clause),
                    "negative_parent": list(negative_clause),
                    "positive_body_semantic": list(positive_body),
                    "negative_body_semantic": list(negative_body),
                    "orientation": orientation,
                    "replaced_parent_index": replace_index,
                    "replacement_clause": list(replacement),
                    "residual_before_sha256": before["sha256"],
                    "residual_after_sha256": after["sha256"],
                }
                ledger["successful_contractions"] = 1
                ledger["clauses_replaced"] = 1
                ledger["certificate_bytes"] = len(
                    json.dumps(
                        certificate, sort_keys=True, separators=(",", ":")
                    ).encode()
                )
                ledger["state_bytes_peak"] = max(
                    ledger["state_bytes_peak"], after["bytes"]
                )
                ledger["cumulative_state_bytes"] += after["bytes"]
                return contracted, certificate, ledger

        if not found_for_variable:
            ledger["failed_variable_tests"] += 1

    return residual, None, ledger


def certificate_is_valid(certificate):
    variable = certificate["variable"]
    positive_parent = tuple(certificate["positive_parent"])
    negative_parent = tuple(certificate["negative_parent"])
    if variable not in positive_parent or -variable not in negative_parent:
        return False
    positive_body = semantic_key(
        tuple(literal for literal in positive_parent if literal != variable)
    )
    negative_body = semantic_key(
        tuple(literal for literal in negative_parent if literal != -variable)
    )
    orientation = certificate["orientation"]
    replacement = tuple(certificate["replacement_clause"])
    if orientation == "POSITIVE_BODY_STRICT_SUBSET_NEGATIVE_BODY":
        valid_subset = set(positive_body) < set(negative_body)
        expected = negative_body
    elif orientation == "NEGATIVE_BODY_STRICT_SUBSET_POSITIVE_BODY":
        valid_subset = set(negative_body) < set(positive_body)
        expected = positive_body
    else:
        return False
    return (
        valid_subset
        and replacement == expected
        and tuple(certificate["positive_body_semantic"]) == positive_body
        and tuple(certificate["negative_body_semantic"]) == negative_body
    )


def replay_ssr(formula, certificate):
    residual, found, _ = discover_and_contract_one(formula)
    if found is None or found != certificate:
        raise AssertionError("SSR certificate mismatch")
    if not certificate_is_valid(found):
        raise AssertionError("invalid SSR certificate")
    return residual


def has_ssr(formula):
    _, certificate, _ = discover_and_contract_one(formula)
    return certificate is not None


def exact_closure(formula):
    residual = v22.v20.v18.v12.canonical_formula(formula)
    transcript = []
    ledger = {"v13": {}, "v15": {}, "v18": {}, "v20": {}, "v22": {}, "v24": {}}

    while True:
        reduced, inherited_transcript, inherited_ledger = v22.exact_closure(residual)
        transcript.extend(inherited_transcript)
        for lane in ("v13", "v15", "v18", "v20", "v22"):
            add_ledger(ledger[lane], inherited_ledger[lane])
        residual = reduced

        contracted, certificate, local = discover_and_contract_one(residual)
        add_ledger(ledger["v24"], local)
        if certificate is None:
            break
        transcript.append({"kind": "SELF_SUBSUMING_RESOLUTION", "certificate": certificate})
        residual = contracted

    return residual, transcript, ledger


def replay(original, transcript):
    residual = v22.v20.v18.v12.canonical_formula(original)
    for entry in transcript:
        kind = entry["kind"]
        if kind == "PURE_LITERAL":
            residual, _ = v22.v20.v18.v12.replay_certificate(
                residual, [entry["certificate"]]
            )
        elif kind == "TAUTOLOGICAL_RESOLVENT":
            residual = v22.v20.v18.v13.replay_tr_certificate(
                residual, entry["certificate"]
            )
        elif kind == "SINGLE_RESOLVENT":
            residual = v22.v20.v18.v15.replay_single(
                residual, entry["certificate"]
            )
        elif kind == "COMPLEMENTARY_TWIN":
            residual = v22.v20.v18.replay_twin(residual, entry["certificate"])
        elif kind == "CLAUSE_SUBSUMPTION":
            residual = v22.v20.replay_subsumption(residual, entry["certificate"])
        elif kind == "ORDER_INVARIANT_TWIN":
            residual = v22.replay_repair(residual, entry["certificate"])
        elif kind == "SELF_SUBSUMING_RESOLUTION":
            residual = replay_ssr(residual, entry["certificate"])
        else:
            raise AssertionError(f"unknown transcript kind: {kind}")
    return residual


def lift_witness(original, final_residual, transcript, final_assignment):
    # SSR is pointwise equivalence; it requires no reverse assignment change.
    without_ssr = [
        entry for entry in transcript if entry["kind"] != "SELF_SUBSUMING_RESOLUTION"
    ]
    return v22.lift_witness(original, final_residual, without_ssr, final_assignment)


def semantic_audit(source, residual, transcript):
    source_variables = v22.v20.v18.v13.variables_of(source)
    residual_variables = v22.v20.v18.v13.variables_of(residual)
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
        if v22.v20.v18.v13.formula_true(source, assignment, ledger):
            projected.add(tuple(assignment[v] for v in residual_variables))

    models = set()
    for bits in itertools.product((False, True), repeat=len(residual_variables)):
        ledger["residual_assignment_rows"] += 1
        assignment = dict(zip(residual_variables, bits))
        if v22.v20.v18.v13.formula_true(residual, assignment, ledger):
            models.add(bits)
            _, lift_ledger = lift_witness(
                source, residual, transcript, assignment
            )
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


def run():
    # Diagnostic only: validate theorem certificate and fixed point, not a fragile pair order.
    n, m, seed = DIAGNOSTIC
    diagnostic_source = v22.v20.v18.v9.random_connected_3cnf(
        seed, variable_count=n, clause_count=m
    )
    diagnostic_base, _, _ = v22.exact_closure(diagnostic_source)
    assert v22.v20.v18.v14.crystal(diagnostic_base)["sha256"] == DIAGNOSTIC_BASE_SHA256
    _, first_certificate, _ = discover_and_contract_one(diagnostic_base)
    assert first_certificate is not None
    assert certificate_is_valid(first_certificate)

    diagnostic_final, diagnostic_transcript, _ = exact_closure(diagnostic_source)
    assert replay(diagnostic_source, diagnostic_transcript) == diagnostic_final
    assert not has_ssr(diagnostic_final)
    diagnostic_ok, _ = semantic_audit(
        diagnostic_source, diagnostic_final, diagnostic_transcript
    )
    assert diagnostic_ok
    diagnostic = {
        "n": n,
        "m": m,
        "seed": seed,
        "role": "DIAGNOSTIC_ONLY_NOT_BLIND",
        "base_crystal": v22.v20.v18.v14.crystal(diagnostic_base),
        "first_v24_certificate": first_certificate,
        "final_crystal": v22.v20.v18.v14.crystal(diagnostic_final),
        "terminal_status": terminal_status(diagnostic_final),
        "ssr_remaining": False,
        "semantic_audit_pass": True,
    }

    # Phase 1: materialize/hash every fresh source before any provider reduction.
    frozen_sources = []
    for n, m, seeds in FROZEN_GROUPS:
        for seed in seeds:
            source = v22.v20.v18.v12.canonical_formula(
                v22.v20.v18.v9.random_connected_3cnf(
                    seed, variable_count=n, clause_count=m
                )
            )
            frozen_sources.append(
                {
                    "n": n,
                    "m": m,
                    "seed": seed,
                    "source": source,
                    "source_crystal": v22.v20.v18.v14.crystal(source),
                }
            )
    source_manifest_sha256 = digest(
        [
            (row["n"], row["m"], row["seed"], row["source_crystal"]["sha256"])
            for row in frozen_sources
        ]
    )

    # Phase 2: freeze v22 baselines and v24 outputs before semantic audit.
    frozen = []
    for item in frozen_sources:
        baseline, _, _ = v22.exact_closure(item["source"])
        baseline_had_ssr = has_ssr(baseline)
        final, transcript, runtime = exact_closure(item["source"])
        assert replay(item["source"], transcript) == final
        assert not has_ssr(final)
        frozen.append(
            {
                **item,
                "baseline": baseline,
                "baseline_had_ssr": baseline_had_ssr,
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
                v22.v20.v18.v14.crystal(row["baseline"])["sha256"],
                row["baseline_had_ssr"],
                v22.v20.v18.v14.crystal(row["final"])["sha256"],
                row["transcript"],
            )
            for row in frozen
        ]
    )

    # Phase 3: bounded exhaustive semantic audit only after outputs are frozen.
    rows = []
    runtime_total = {
        "v13": {}, "v15": {}, "v18": {}, "v20": {}, "v22": {}, "v24": {}
    }
    audit_total = {}
    seen = {}
    revisits = 0
    for item in frozen:
        ok, audit = semantic_audit(
            item["source"], item["final"], item["transcript"]
        )
        assert ok
        add_ledger(audit_total, audit)
        for lane in runtime_total:
            add_ledger(runtime_total[lane], item["runtime"][lane])

        baseline_crystal = v22.v20.v18.v14.crystal(item["baseline"])
        final_crystal = v22.v20.v18.v14.crystal(item["final"])
        prior = seen.get(final_crystal["sha256"])
        revisit = (
            prior is not None
            and prior["canonical_cnf"] == final_crystal["canonical_cnf"]
        )
        if revisit:
            revisits += 1
        else:
            seen[final_crystal["sha256"]] = final_crystal

        steps = count_kind(item["transcript"], "SELF_SUBSUMING_RESOLUTION")
        rows.append(
            {
                "n": item["n"],
                "m": item["m"],
                "seed": item["seed"],
                "source_crystal_sha256": item["source_crystal"]["sha256"],
                "baseline_crystal_sha256": baseline_crystal["sha256"],
                "final_crystal_sha256": final_crystal["sha256"],
                "baseline_had_ssr": item["baseline_had_ssr"],
                "baseline_bytes": baseline_crystal["bytes"],
                "final_bytes": final_crystal["bytes"],
                "v24_steps": steps,
                "feature_fired": steps > 0,
                "terminal_status": terminal_status(item["final"]),
                "ssr_remaining": False,
                "semantic_audit_pass": True,
                "exact_final_revisit": revisit,
            }
        )

    fired = [row for row in rows if row["feature_fired"]]
    result = {
        "artifact_id": "PF5-SELF-SUBSUMING-RESOLUTION-V24",
        "status": "FINITE_FRESH_BLIND_EXACT_EQUIVALENCE_AUDIT_COMPLETE",
        "protocol_receipt": "data/PF5-V24-FROZEN-SELF-SUBSUMING-RESOLUTION-PROTOCOL.json",
        "parent_audit": "data/PF5-V23-STRUCTURAL-AUDIT-SELF-SUBSUMING-RESOLUTION.json",
        "feature": "SELF_SUBSUMING_RESOLUTION_CONTRACTION",
        "feature_is_heuristic": False,
        "feature_is_logical_equivalence": True,
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
            "baseline_cases_with_ssr": sum(row["baseline_had_ssr"] for row in rows),
            "feature_fired_cases": len(fired),
            "feature_noop_cases": len(rows) - len(fired),
            "total_v24_steps": sum(row["v24_steps"] for row in rows),
            "terminal_true_cases": sum(row["terminal_status"] == "TRUE" for row in rows),
            "terminal_false_cases": sum(row["terminal_status"] == "FALSE" for row in rows),
            "open_residual_cases": sum(row["terminal_status"] == "OPEN_RESIDUAL" for row in rows),
            "positive_byte_delta_cases": sum(row["baseline_bytes"] > row["final_bytes"] for row in rows),
            "mean_baseline_crystal_bytes": sum(row["baseline_bytes"] for row in rows) / len(rows),
            "mean_final_crystal_bytes": sum(row["final_bytes"] for row in rows) / len(rows),
            "all_semantic_audits_pass": all(row["semantic_audit_pass"] for row in rows),
            "all_final_residuals_ssr_free": all(not row["ssr_remaining"] for row in rows),
            "exact_final_revisits": revisits,
        },
        "rows": rows,
        "runtime_discovery_ledger": runtime_total,
        "finite_semantic_audit_ledger": audit_total,
        "hephaestus_role": "ACCOUNTING_RECURRENCE_ONLY_NO_DECISION_AUTHORITY",
        "universal_exact_closure": "OPEN",
        "next_gate": "FIRST_RESIDUAL_SURVIVING_V12_V13_V15_V18_V20_V22_V24",
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
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )
    print("PF5_SELF_SUBSUMING_RESOLUTION_V24 =", result["status"])
    print("SOURCE_MANIFEST_SHA256 =", result["source_manifest_sha256"])
    print("REDUCTION_BATCH_SHA256 =", result["reduction_batch_sha256"])
    print("SUMMARY =", result["summary"])
    print("RUNTIME_LEDGER =", result["runtime_discovery_ledger"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
