#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pf5_complementary_twin_contraction_v18 as v18


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def add_ledger(target, source):
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def run():
    # V18-001 repair: keep the deterministic increasing-variable scan exactly as
    # frozen. The first match on 911600 is x2, not the illustrative later x4 twin.
    n, m, seed = v18.DIAGNOSTIC
    source = v18.v9.random_connected_3cnf(seed, variable_count=n, clause_count=m)
    base, _, _ = v18.v15.exact_closure(source)
    assert v18.v14.crystal(base)["sha256"] == v18.DIAGNOSTIC_BASE_SHA256

    first, first_certificate, _ = v18.discover_and_contract_one(base)
    assert first_certificate is not None
    assert first_certificate["variable"] == 2
    assert set(first_certificate["common_body"]) == {-3, -4}
    assert v18.replay_twin(base, first_certificate) == first

    final, transcript, diagnostic_runtime = v18.exact_closure(source)
    assert v18.replay(source, transcript) == final
    ok, diagnostic_audit = v18.semantic_audit(source, final, transcript)
    assert ok
    diagnostic = {
        "n": n,
        "m": m,
        "seed": seed,
        "base_crystal": v18.v14.crystal(base),
        "first_v18_certificate": first_certificate,
        "final_crystal": v18.v14.crystal(final),
        "terminal_status": v18.terminal_status(final),
        "semantic_audit_pass": True,
        "semantic_audit_ledger": diagnostic_audit,
        "runtime_ledger": diagnostic_runtime,
        "repair_receipt": "data/PF5-V18-001-DIAGNOSTIC-ORDER-MISMATCH.json",
    }

    # Phase 1: exactly the same pre-frozen holdout as v18.
    frozen_sources = []
    for n, m, seeds in v18.FROZEN_GROUPS:
        for seed in seeds:
            formula = v18.v12.canonical_formula(
                v18.v9.random_connected_3cnf(seed, variable_count=n, clause_count=m)
            )
            frozen_sources.append(
                {
                    "n": n,
                    "m": m,
                    "seed": seed,
                    "source": formula,
                    "source_crystal": v18.v14.crystal(formula),
                }
            )
    source_manifest_sha256 = digest(
        [
            (row["n"], row["m"], row["seed"], row["source_crystal"]["sha256"])
            for row in frozen_sources
        ]
    )

    # Phase 2: freeze baseline and repaired-provider reductions before any audit.
    frozen = []
    for item in frozen_sources:
        baseline, _, _ = v18.v15.exact_closure(item["source"])
        final, transcript, runtime = v18.exact_closure(item["source"])
        assert v18.replay(item["source"], transcript) == final
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

    # Phase 3: bounded exhaustive audit after every reduction is frozen.
    rows = []
    audit_total = {}
    runtime_total = {"v13": {}, "v15": {}, "v18": {}}
    seen = {}
    revisits = 0
    for item in frozen:
        ok, audit = v18.semantic_audit(
            item["source"], item["final"], item["transcript"]
        )
        assert ok
        add_ledger(audit_total, audit)
        for lane in ("v13", "v15", "v18"):
            add_ledger(runtime_total[lane], item["runtime"][lane])

        baseline_crystal = v18.v14.crystal(item["baseline"])
        final_crystal = v18.v14.crystal(item["final"])
        prior = seen.get(final_crystal["sha256"])
        revisit = (
            prior is not None
            and prior["canonical_cnf"] == final_crystal["canonical_cnf"]
        )
        if revisit:
            revisits += 1
        else:
            seen[final_crystal["sha256"]] = final_crystal

        twin_steps = v18.count_kind(item["transcript"], "COMPLEMENTARY_TWIN")
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
                "proof_transcript_bytes": len(
                    json.dumps(
                        item["transcript"], sort_keys=True, separators=(",", ":")
                    ).encode()
                ),
                "terminal_status": v18.terminal_status(item["final"]),
                "semantic_audit_pass": True,
                "exact_final_revisit": revisit,
            }
        )

    fired = [row for row in rows if row["feature_fired"]]
    result = {
        "artifact_id": "PF5-COMPLEMENTARY-TWIN-CONTRACTION-V18.1",
        "status": "FINITE_BLIND_EXACT_EQUIVALENCE_AUDIT_COMPLETE",
        "repair": "V18-001_DIAGNOSTIC_ORDER_ONLY",
        "feature": "COMPLEMENTARY_TWIN_CLAUSE_CONTRACTION",
        "feature_identity": "(A OR x) AND (A OR NOT x) == A",
        "feature_is_heuristic": False,
        "feature_is_logical_equivalence": True,
        "diagnostic": diagnostic,
        "frozen_groups": [
            {"n": n, "m": m, "seeds": seeds} for n, m, seeds in v18.FROZEN_GROUPS
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
        "summary": {
            "cases": len(rows),
            "feature_fired_cases": len(fired),
            "feature_noop_cases": len(rows) - len(fired),
            "total_twin_steps": sum(row["twin_steps"] for row in rows),
            "terminal_true_cases": sum(row["terminal_status"] == "TRUE" for row in rows),
            "terminal_false_cases": sum(row["terminal_status"] == "FALSE" for row in rows),
            "open_residual_cases": sum(
                row["terminal_status"] == "OPEN_RESIDUAL" for row in rows
            ),
            "positive_byte_delta_cases": sum(
                row["baseline_bytes"] > row["final_bytes"] for row in rows
            ),
            "mean_baseline_crystal_bytes": sum(row["baseline_bytes"] for row in rows)
            / len(rows),
            "mean_final_crystal_bytes": sum(row["final_bytes"] for row in rows)
            / len(rows),
            "all_semantic_audits_pass": all(row["semantic_audit_pass"] for row in rows),
            "exact_final_revisits": revisits,
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
    print("PF5_COMPLEMENTARY_TWIN_V18_1 =", result["status"])
    print("SOURCE_MANIFEST_SHA256 =", result["source_manifest_sha256"])
    print("REDUCTION_BATCH_SHA256 =", result["reduction_batch_sha256"])
    print("SUMMARY =", result["summary"])
    print("RUNTIME_LEDGER =", result["runtime_discovery_ledger"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
