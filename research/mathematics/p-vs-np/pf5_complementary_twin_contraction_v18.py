#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_pure_literal_exact_projection_v12 as v12
import pf5_tautological_resolvent_projection_v13 as v13
import pf5_pnp_spiral_hephaestus_crystal_v14 as v14
import pf5_single_resolvent_exact_projection_v15 as v15

DIAGNOSTIC = (6, 24, 911600)
DIAGNOSTIC_BASE_SHA256 = "06cfc87bfe5963cb2ff913ce58aa1915236ad28b74d8c734d054862bb0cb4522"
FROZEN_GROUPS = [
    (6, 24, list(range(913600, 913616))),
    (7, 28, list(range(913700, 913716))),
]


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def add_ledger(target, source):
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def discover_and_contract_one(formula):
    """Apply the first exact (A|x)&(A|~x) == A contraction, if present."""
    residual = v12.canonical_formula(formula)
    ledger = {
        "variable_tests": 0,
        "failed_variable_tests": 0,
        "clause_polarity_checks": 0,
        "pair_checks": 0,
        "body_literal_checks": 0,
        "body_hashes": 0,
        "successful_contractions": 0,
        "clauses_removed": 0,
        "clauses_emitted": 0,
        "certificate_bytes": 0,
    }

    for variable in v13.variables_of(residual):
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
            positive_body_sha256 = digest(list(positive_body))
            ledger["body_hashes"] += 1
            for negative_index, negative_clause in negative:
                ledger["pair_checks"] += 1
                negative_body = tuple(lit for lit in negative_clause if lit != -variable)
                negative_body_sha256 = digest(list(negative_body))
                ledger["body_hashes"] += 1
                ledger["body_literal_checks"] += max(
                    len(positive_body), len(negative_body)
                )
                if positive_body != negative_body:
                    continue

                kept = tuple(
                    clause
                    for index, clause in enumerate(residual)
                    if index not in (positive_index, negative_index)
                )
                already_present = positive_body in kept
                emitted = kept if already_present else kept + (positive_body,)
                contracted = v12.canonical_formula(emitted)
                certificate = {
                    "operator": "COMPLEMENTARY_TWIN_CLAUSE_CONTRACTION",
                    "identity": "(A OR x) AND (A OR NOT x) == A",
                    "variable": variable,
                    "positive_parent_index": positive_index,
                    "negative_parent_index": negative_index,
                    "positive_parent": list(positive_clause),
                    "negative_parent": list(negative_clause),
                    "common_body": list(positive_body),
                    "positive_body_sha256": positive_body_sha256,
                    "negative_body_sha256": negative_body_sha256,
                    "body_already_present": already_present,
                    "residual_before_sha256": v13.digest_formula(residual),
                    "residual_after_sha256": v13.digest_formula(contracted),
                }
                ledger["successful_contractions"] = 1
                ledger["clauses_removed"] = 2
                ledger["clauses_emitted"] = 0 if already_present else 1
                ledger["certificate_bytes"] = len(
                    json.dumps(
                        certificate, sort_keys=True, separators=(",", ":")
                    ).encode()
                )
                return contracted, certificate, ledger

        ledger["failed_variable_tests"] += 1

    return residual, None, ledger


def replay_twin(formula, certificate):
    residual, found, _ = discover_and_contract_one(formula)
    if found is None or found != certificate:
        raise AssertionError("complementary-twin certificate mismatch")
    return residual


def exact_closure(formula):
    residual = v12.canonical_formula(formula)
    transcript = []
    ledger = {"v13": {}, "v15": {}, "v18": {}}

    while True:
        reduced, inherited_transcript, inherited_ledger = v15.exact_closure(residual)
        transcript.extend(inherited_transcript)
        add_ledger(ledger["v13"], inherited_ledger["v13"])
        add_ledger(ledger["v15"], inherited_ledger["v15"])
        residual = reduced

        contracted, certificate, twin_ledger = discover_and_contract_one(residual)
        add_ledger(ledger["v18"], twin_ledger)
        if certificate is None:
            break
        transcript.append({"kind": "COMPLEMENTARY_TWIN", "certificate": certificate})
        residual = contracted

    return residual, transcript, ledger


def replay(original, transcript):
    residual = v12.canonical_formula(original)
    for entry in transcript:
        kind = entry["kind"]
        if kind == "PURE_LITERAL":
            residual, _ = v12.replay_certificate(residual, [entry["certificate"]])
        elif kind == "TAUTOLOGICAL_RESOLVENT":
            residual = v13.replay_tr_certificate(residual, entry["certificate"])
        elif kind == "SINGLE_RESOLVENT":
            residual = v15.replay_single(residual, entry["certificate"])
        elif kind == "COMPLEMENTARY_TWIN":
            residual = replay_twin(residual, entry["certificate"])
        else:
            raise AssertionError(f"unknown transcript kind: {kind}")
    return residual


def lift_witness(original, final_residual, transcript, final_assignment):
    # Twin contractions are pointwise equivalences and require no assignment
    # change.  Projection certificates retain the complete reverse witness map.
    projection_transcript = [
        entry for entry in transcript if entry["kind"] != "COMPLEMENTARY_TWIN"
    ]
    return v15.lift_witness(
        original, final_residual, projection_transcript, final_assignment
    )


def semantic_audit(source, residual, transcript):
    source_variables = v13.variables_of(source)
    residual_variables = v13.variables_of(residual)
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
        if v13.formula_true(source, assignment, ledger):
            projected.add(tuple(assignment[v] for v in residual_variables))

    models = set()
    for bits in itertools.product((False, True), repeat=len(residual_variables)):
        ledger["residual_assignment_rows"] += 1
        assignment = dict(zip(residual_variables, bits))
        if v13.formula_true(residual, assignment, ledger):
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


def run():
    # Diagnostic: the exact first v17 obstruction is fixed before v18 provider use.
    n, m, seed = DIAGNOSTIC
    diagnostic_source = v9.random_connected_3cnf(
        seed, variable_count=n, clause_count=m
    )
    diagnostic_base, _, _ = v15.exact_closure(diagnostic_source)
    assert v14.crystal(diagnostic_base)["sha256"] == DIAGNOSTIC_BASE_SHA256

    first, first_certificate, _ = discover_and_contract_one(diagnostic_base)
    assert first_certificate is not None
    assert first_certificate["variable"] == 4
    assert set(first_certificate["common_body"]) == {-3, 5}
    assert replay_twin(diagnostic_base, first_certificate) == first

    diagnostic_final, diagnostic_transcript, _ = exact_closure(diagnostic_source)
    assert replay(diagnostic_source, diagnostic_transcript) == diagnostic_final
    diagnostic_ok, diagnostic_audit = semantic_audit(
        diagnostic_source, diagnostic_final, diagnostic_transcript
    )
    assert diagnostic_ok

    diagnostic = {
        "n": n,
        "m": m,
        "seed": seed,
        "base_crystal": v14.crystal(diagnostic_base),
        "first_v18_certificate": first_certificate,
        "final_crystal": v14.crystal(diagnostic_final),
        "terminal_status": terminal_status(diagnostic_final),
        "semantic_audit_pass": True,
        "semantic_audit_ledger": diagnostic_audit,
    }

    # Phase 1: freeze and hash every holdout source before any reduction.
    frozen_sources = []
    for n, m, seeds in FROZEN_GROUPS:
        for seed in seeds:
            source = v12.canonical_formula(
                v9.random_connected_3cnf(seed, variable_count=n, clause_count=m)
            )
            frozen_sources.append(
                {
                    "n": n,
                    "m": m,
                    "seed": seed,
                    "source": source,
                    "source_crystal": v14.crystal(source),
                }
            )
    source_manifest_sha256 = digest(
        [
            (row["n"], row["m"], row["seed"], row["source_crystal"]["sha256"])
            for row in frozen_sources
        ]
    )

    # Phase 2: freeze baseline and v18-composed reductions before semantic audits.
    frozen_reductions = []
    for item in frozen_sources:
        source = item["source"]
        baseline, baseline_transcript, _ = v15.exact_closure(source)
        final, transcript, runtime_ledger = exact_closure(source)
        assert replay(source, transcript) == final
        frozen_reductions.append(
            {
                **item,
                "baseline": baseline,
                "baseline_transcript": baseline_transcript,
                "final": final,
                "transcript": transcript,
                "runtime_ledger": runtime_ledger,
            }
        )

    reduction_batch_sha256 = digest(
        [
            (
                row["n"],
                row["m"],
                row["seed"],
                v14.crystal(row["baseline"])["sha256"],
                v14.crystal(row["final"])["sha256"],
                row["transcript"],
            )
            for row in frozen_reductions
        ]
    )

    # Phase 3: finite exhaustive semantic audits only after reductions are frozen.
    rows = []
    audit_total = {}
    runtime_total = {"v13": {}, "v15": {}, "v18": {}}
    seen_final = {}
    exact_revisits = 0

    for item in frozen_reductions:
        ok, audit_ledger = semantic_audit(
            item["source"], item["final"], item["transcript"]
        )
        if not ok:
            raise AssertionError(f"semantic audit failed for seed {item['seed']}")
        add_ledger(audit_total, audit_ledger)
        for lane in ("v13", "v15", "v18"):
            add_ledger(runtime_total[lane], item["runtime_ledger"][lane])

        baseline_crystal = v14.crystal(item["baseline"])
        final_crystal = v14.crystal(item["final"])
        prior = seen_final.get(final_crystal["sha256"])
        revisit = (
            prior is not None
            and prior["canonical_cnf"] == final_crystal["canonical_cnf"]
        )
        if revisit:
            exact_revisits += 1
        else:
            seen_final[final_crystal["sha256"]] = final_crystal

        twin_steps = count_kind(item["transcript"], "COMPLEMENTARY_TWIN")
        rows.append(
            {
                "n": item["n"],
                "m": item["m"],
                "seed": item["seed"],
                "source_crystal_sha256": item["source_crystal"]["sha256"],
                "baseline_crystal_sha256": baseline_crystal["sha256"],
                "final_crystal_sha256": final_crystal["sha256"],
                "baseline_bytes": baseline_crystal["bytes"],
                "final_bytes": final_crystal["bytes"],
                "twin_steps": twin_steps,
                "feature_fired": twin_steps > 0,
                "pure_steps": count_kind(item["transcript"], "PURE_LITERAL"),
                "all_taut_steps": count_kind(
                    item["transcript"], "TAUTOLOGICAL_RESOLVENT"
                ),
                "single_resolvent_steps": count_kind(
                    item["transcript"], "SINGLE_RESOLVENT"
                ),
                "proof_transcript_bytes": len(
                    json.dumps(
                        item["transcript"], sort_keys=True, separators=(",", ":")
                    ).encode()
                ),
                "terminal_status": terminal_status(item["final"]),
                "semantic_audit_pass": True,
                "exact_final_revisit": revisit,
            }
        )

    fired = [row for row in rows if row["feature_fired"]]
    result = {
        "artifact_id": "PF5-COMPLEMENTARY-TWIN-CONTRACTION-V18",
        "status": "FINITE_BLIND_EXACT_EQUIVALENCE_AUDIT_COMPLETE",
        "feature": "COMPLEMENTARY_TWIN_CLAUSE_CONTRACTION",
        "feature_identity": "(A OR x) AND (A OR NOT x) == A",
        "feature_is_heuristic": False,
        "feature_is_logical_equivalence": True,
        "diagnostic": diagnostic,
        "frozen_groups": [
            {"n": n, "m": m, "seeds": seeds} for n, m, seeds in FROZEN_GROUPS
        ],
        "case_count": len(rows),
        "all_sources_frozen_before_reduction": True,
        "holdout_not_conditioned_on_feature_presence": True,
        "all_reductions_frozen_before_semantic_audit": True,
        "adaptive_extension_after_results": False,
        "source_manifest_sha256": source_manifest_sha256,
        "reduction_batch_sha256": reduction_batch_sha256,
        "decision_heuristic": False,
        "uses_slime": False,
        "uses_sat_oracle": False,
        "uses_pswidth_score": False,
        "uses_truth_table_in_runtime": False,
        "runtime_rule_polynomial_in_explicit_residual_size": True,
        "witness_lift_replayable_from_certificate": True,
        "hephaestus_role": "ACCOUNTING_RECURRENCE_ONLY_NO_DECISION_AUTHORITY",
        "runtime_exact_closure": [
            "PURE_LITERAL_EXISTENTIAL_PROJECTION",
            "TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION",
            "SINGLE_NONTAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION",
            "COMPLEMENTARY_TWIN_CLAUSE_CONTRACTION",
        ],
        "summary": {
            "cases": len(rows),
            "feature_fired_cases": len(fired),
            "feature_noop_cases": len(rows) - len(fired),
            "total_twin_steps": sum(row["twin_steps"] for row in rows),
            "terminal_true_cases": sum(
                row["terminal_status"] == "TRUE" for row in rows
            ),
            "terminal_false_cases": sum(
                row["terminal_status"] == "FALSE" for row in rows
            ),
            "open_residual_cases": sum(
                row["terminal_status"] == "OPEN_RESIDUAL" for row in rows
            ),
            "positive_byte_delta_cases": sum(
                row["baseline_bytes"] > row["final_bytes"] for row in rows
            ),
            "mean_baseline_crystal_bytes": sum(
                row["baseline_bytes"] for row in rows
            )
            / len(rows),
            "mean_final_crystal_bytes": sum(row["final_bytes"] for row in rows)
            / len(rows),
            "all_semantic_audits_pass": all(
                row["semantic_audit_pass"] for row in rows
            ),
            "exact_final_revisits": exact_revisits,
        },
        "rows": rows,
        "runtime_discovery_ledger": runtime_total,
        "finite_semantic_audit_ledger": audit_total,
        "universal_exact_closure": "OPEN",
        "next_gate": "FIRST_RESIDUAL_SURVIVING_V12_V13_V15_V18",
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
    print("PF5_COMPLEMENTARY_TWIN_V18 =", result["status"])
    print("SOURCE_MANIFEST_SHA256 =", result["source_manifest_sha256"])
    print("REDUCTION_BATCH_SHA256 =", result["reduction_batch_sha256"])
    print("SUMMARY =", result["summary"])
    print("RUNTIME_LEDGER =", result["runtime_discovery_ledger"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
