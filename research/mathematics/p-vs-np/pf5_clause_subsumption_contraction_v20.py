#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import pf5_complementary_twin_contraction_v18 as v18

DIAGNOSTIC = (6, 24, 913600)
DIAGNOSTIC_CRYSTAL_SHA256 = "df47995b674dd2cc26323082e2037f9611c5f46ad2aa599b4730ce574fe1cc98"
FROZEN_GROUPS = [
    (6, 24, list(range(914600, 914616))),
    (7, 28, list(range(914700, 914716))),
]


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def add_ledger(target, source):
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def discover_and_contract_one(formula):
    residual = v18.v12.canonical_formula(formula)
    before_crystal = v18.v14.crystal(residual)
    clause_sets = [set(clause) for clause in residual]
    ledger = {
        "clause_pair_tests": 0,
        "failed_pair_tests": 0,
        "literal_membership_checks": 0,
        "successful_contractions": 0,
        "clauses_removed": 0,
        "certificate_bytes": 0,
        "state_bytes_peak": before_crystal["bytes"],
        "cumulative_state_bytes": before_crystal["bytes"],
    }

    # Frozen pre-provider order: i increases, j increases over every j != i.
    for i, left in enumerate(residual):
        left_set = clause_sets[i]
        for j, right in enumerate(residual):
            if i == j:
                continue
            ledger["clause_pair_tests"] += 1
            if len(left) >= len(right):
                ledger["failed_pair_tests"] += 1
                continue

            is_subset = True
            for literal in left:
                ledger["literal_membership_checks"] += 1
                if literal not in clause_sets[j]:
                    is_subset = False
                    break
            if not is_subset:
                ledger["failed_pair_tests"] += 1
                continue

            contracted = v18.v12.canonical_formula(
                tuple(clause for index, clause in enumerate(residual) if index != j)
            )
            after_crystal = v18.v14.crystal(contracted)
            certificate = {
                "operator": "CLAUSE_SUBSUMPTION_CONTRACTION",
                "identity": "A AND (A OR B) == A",
                "subsuming_index": i,
                "subsumed_index": j,
                "subsuming_clause": list(left),
                "subsumed_clause": list(right),
                "strict_subset": True,
                "residual_before_sha256": before_crystal["sha256"],
                "residual_after_sha256": after_crystal["sha256"],
            }
            ledger["successful_contractions"] = 1
            ledger["clauses_removed"] = 1
            ledger["certificate_bytes"] = len(
                json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()
            )
            ledger["state_bytes_peak"] = max(
                ledger["state_bytes_peak"], after_crystal["bytes"]
            )
            ledger["cumulative_state_bytes"] += after_crystal["bytes"]
            return contracted, certificate, ledger

    return residual, None, ledger


def replay_subsumption(formula, certificate):
    residual, found, _ = discover_and_contract_one(formula)
    if found is None or found != certificate:
        raise AssertionError("subsumption certificate mismatch")
    return residual


def exact_closure(formula):
    residual = v18.v12.canonical_formula(formula)
    transcript = []
    ledger = {"v13": {}, "v15": {}, "v18": {}, "v20": {}}

    while True:
        reduced, inherited_transcript, inherited_ledger = v18.exact_closure(residual)
        transcript.extend(inherited_transcript)
        for lane in ("v13", "v15", "v18"):
            add_ledger(ledger[lane], inherited_ledger[lane])
        residual = reduced

        contracted, certificate, local = discover_and_contract_one(residual)
        add_ledger(ledger["v20"], local)
        if certificate is None:
            break
        transcript.append({"kind": "CLAUSE_SUBSUMPTION", "certificate": certificate})
        residual = contracted

    return residual, transcript, ledger


def replay(original, transcript):
    residual = v18.v12.canonical_formula(original)
    for entry in transcript:
        kind = entry["kind"]
        if kind == "PURE_LITERAL":
            residual, _ = v18.v12.replay_certificate(residual, [entry["certificate"]])
        elif kind == "TAUTOLOGICAL_RESOLVENT":
            residual = v18.v13.replay_tr_certificate(residual, entry["certificate"])
        elif kind == "SINGLE_RESOLVENT":
            residual = v18.v15.replay_single(residual, entry["certificate"])
        elif kind == "COMPLEMENTARY_TWIN":
            residual = v18.replay_twin(residual, entry["certificate"])
        elif kind == "CLAUSE_SUBSUMPTION":
            residual = replay_subsumption(residual, entry["certificate"])
        else:
            raise AssertionError(f"unknown transcript kind: {kind}")
    return residual


def lift_witness(original, final_residual, transcript, final_assignment):
    # Subsumption and complementary-twin steps are pointwise equivalences and
    # require no assignment modification. Projection certificates carry lifts.
    without_subsumption = [
        entry for entry in transcript if entry["kind"] != "CLAUSE_SUBSUMPTION"
    ]
    return v18.lift_witness(
        original, final_residual, without_subsumption, final_assignment
    )


def semantic_audit(source, residual, transcript):
    source_variables = v18.v13.variables_of(source)
    residual_variables = v18.v13.variables_of(residual)
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
        if v18.v13.formula_true(source, assignment, ledger):
            projected.add(tuple(assignment[v] for v in residual_variables))

    models = set()
    for bits in itertools.product((False, True), repeat=len(residual_variables)):
        ledger["residual_assignment_rows"] += 1
        assignment = dict(zip(residual_variables, bits))
        if v18.v13.formula_true(residual, assignment, ledger):
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
    # Non-blind diagnostic only: locate the already observed first v19 survivor.
    n, m, seed = DIAGNOSTIC
    diagnostic_source = v18.v9.random_connected_3cnf(
        seed, variable_count=n, clause_count=m
    )
    diagnostic_base, _, _ = v18.exact_closure(diagnostic_source)
    assert v18.v14.crystal(diagnostic_base)["sha256"] == DIAGNOSTIC_CRYSTAL_SHA256
    first, certificate, _ = discover_and_contract_one(diagnostic_base)
    assert certificate is not None
    assert certificate["subsuming_clause"] == [-3, -5]
    assert certificate["subsumed_clause"] == [-3, -5, 6]
    assert replay_subsumption(diagnostic_base, certificate) == first

    diagnostic_final, diagnostic_transcript, _ = exact_closure(diagnostic_source)
    assert replay(diagnostic_source, diagnostic_transcript) == diagnostic_final
    diagnostic_ok, _ = semantic_audit(
        diagnostic_source, diagnostic_final, diagnostic_transcript
    )
    assert diagnostic_ok

    diagnostic = {
        "n": n,
        "m": m,
        "seed": seed,
        "role": "DIAGNOSTIC_ONLY_NOT_BLIND",
        "base_crystal": v18.v14.crystal(diagnostic_base),
        "first_v20_certificate": certificate,
        "final_crystal": v18.v14.crystal(diagnostic_final),
        "terminal_status": terminal_status(diagnostic_final),
        "semantic_audit_pass": True,
    }

    # Phase 1: materialize/hash all fresh sources before any v20 reduction.
    frozen_sources = []
    for n, m, seeds in FROZEN_GROUPS:
        for seed in seeds:
            source = v18.v12.canonical_formula(
                v18.v9.random_connected_3cnf(seed, variable_count=n, clause_count=m)
            )
            frozen_sources.append(
                {
                    "n": n,
                    "m": m,
                    "seed": seed,
                    "source": source,
                    "source_crystal": v18.v14.crystal(source),
                }
            )

    source_manifest_sha256 = digest(
        [
            (row["n"], row["m"], row["seed"], row["source_crystal"]["sha256"])
            for row in frozen_sources
        ]
    )

    # Phase 2: freeze all baseline and v20 provider outputs before semantic audit.
    frozen = []
    for item in frozen_sources:
        baseline, _, _ = v18.exact_closure(item["source"])
        final, transcript, runtime = exact_closure(item["source"])
        assert replay(item["source"], transcript) == final
        frozen.append(
            {
                **item,
                "baseline": baseline,
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
                v18.v14.crystal(row["baseline"])["sha256"],
                v18.v14.crystal(row["final"])["sha256"],
                row["transcript"],
            )
            for row in frozen
        ]
    )

    # Phase 3: bounded exhaustive semantic audit after freeze.
    rows = []
    runtime_total = {"v13": {}, "v15": {}, "v18": {}, "v20": {}}
    audit_total = {}
    seen = {}
    revisits = 0

    for item in frozen:
        ok, audit = semantic_audit(item["source"], item["final"], item["transcript"])
        assert ok
        add_ledger(audit_total, audit)
        for lane in runtime_total:
            add_ledger(runtime_total[lane], item["runtime"][lane])

        baseline_crystal = v18.v14.crystal(item["baseline"])
        final_crystal = v18.v14.crystal(item["final"])
        prior = seen.get(final_crystal["sha256"])
        revisit = prior is not None and prior["canonical_cnf"] == final_crystal["canonical_cnf"]
        if revisit:
            revisits += 1
        else:
            seen[final_crystal["sha256"]] = final_crystal

        steps = count_kind(item["transcript"], "CLAUSE_SUBSUMPTION")
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
                "subsumption_steps": steps,
                "feature_fired": steps > 0,
                "terminal_status": terminal_status(item["final"]),
                "proof_transcript_bytes": len(
                    json.dumps(item["transcript"], sort_keys=True, separators=(",", ":")).encode()
                ),
                "semantic_audit_pass": True,
                "exact_final_revisit": revisit,
            }
        )

    fired = [row for row in rows if row["feature_fired"]]
    result = {
        "artifact_id": "PF5-CLAUSE-SUBSUMPTION-CONTRACTION-V20",
        "status": "FINITE_FRESH_BLIND_EXACT_EQUIVALENCE_AUDIT_COMPLETE",
        "protocol_receipt": "data/PF5-V20-FROZEN-SUBSUMPTION-PROTOCOL.json",
        "protocol_clarification": "data/PF5-V20-PROTOCOL-001-PAIR-ORDER-CLARIFICATION.json",
        "feature": "CLAUSE_SUBSUMPTION_CONTRACTION",
        "feature_identity": "A AND (A OR B) == A",
        "feature_is_heuristic": False,
        "feature_is_logical_equivalence": True,
        "diagnostic": diagnostic,
        "frozen_groups": [
            {"n": n, "m": m, "seeds": seeds} for n, m, seeds in FROZEN_GROUPS
        ],
        "case_count": len(rows),
        "all_sources_frozen_before_provider_reduction": True,
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
        "uses_hephaestus_for_decision": False,
        "runtime_rule_polynomial_in_explicit_residual_size": True,
        "witness_lift_replayable_from_certificate": True,
        "summary": {
            "cases": len(rows),
            "feature_fired_cases": len(fired),
            "feature_noop_cases": len(rows) - len(fired),
            "total_subsumption_steps": sum(row["subsumption_steps"] for row in rows),
            "terminal_true_cases": sum(row["terminal_status"] == "TRUE" for row in rows),
            "terminal_false_cases": sum(row["terminal_status"] == "FALSE" for row in rows),
            "open_residual_cases": sum(row["terminal_status"] == "OPEN_RESIDUAL" for row in rows),
            "positive_byte_delta_cases": sum(row["baseline_bytes"] > row["final_bytes"] for row in rows),
            "mean_baseline_crystal_bytes": sum(row["baseline_bytes"] for row in rows) / len(rows),
            "mean_final_crystal_bytes": sum(row["final_bytes"] for row in rows) / len(rows),
            "all_semantic_audits_pass": all(row["semantic_audit_pass"] for row in rows),
            "exact_final_revisits": revisits,
        },
        "rows": rows,
        "runtime_discovery_ledger": runtime_total,
        "finite_semantic_audit_ledger": audit_total,
        "hephaestus_role": "ACCOUNTING_RECURRENCE_ONLY_NO_DECISION_AUTHORITY",
        "universal_exact_closure": "OPEN",
        "next_gate": "FIRST_RESIDUAL_SURVIVING_V12_V13_V15_V18_V20",
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
    print("PF5_CLAUSE_SUBSUMPTION_V20 =", result["status"])
    print("SOURCE_MANIFEST_SHA256 =", result["source_manifest_sha256"])
    print("REDUCTION_BATCH_SHA256 =", result["reduction_batch_sha256"])
    print("SUMMARY =", result["summary"])
    print("RUNTIME_LEDGER =", result["runtime_discovery_ledger"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
