#!/usr/bin/env python3
"""PF5 Slime q=1 dense connected 3-CNF falsification ladder v13.

No exact scorer is used. The frozen v3 Slime portfolio is attempted under the
unchanged v12 q=1 capped STV compiler. The experiment is outcome-neutral: a
portfolio exhaustion is a valid and scientifically useful terminal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import pf5_slime_capped_pswidth_compiler_v12 as v12

FROZEN_ROWS = [
    (10, 42, 909010),
    (10, 42, 909011),
    (12, 50, 909012),
    (12, 50, 909013),
    (14, 59, 909014),
    (14, 59, 909015),
    (16, 67, 909016),
    (16, 67, 909017),
    (18, 76, 909018),
    (18, 76, 909019),
    (20, 84, 909020),
    (20, 84, 909021),
]
FROZEN_Q = 1


def digest_json(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def selected_key(result):
    return (
        result["peak_ps_state"],
        result["total_ps_states"],
        result["pair_attempts"],
        result["certificate_bytes"],
        result["order_digest"],
    )


def closed_summary(candidate, generation_ops, result):
    return {
        "candidate": candidate,
        "generation_ops": generation_ops,
        "terminal": "CLOSED_PSWIDTH_CAP",
        "cap": result["cap"],
        "peak_ps_state": result["peak_ps_state"],
        "total_ps_states": result["total_ps_states"],
        "pair_attempts": result["pair_attempts"],
        "total_work_units": result["total_work_units"],
        "certificate_bytes": result["certificate_bytes"],
        "certificate_digest": result["certificate"]["certificate_digest"],
        "order_digest": result["order_digest"],
        "certificate_replayed_before_discard": True,
    }


def open_summary(candidate, generation_ops, result):
    return {
        "candidate": candidate,
        "generation_ops": generation_ops,
        "terminal": "OPEN_STATE_CAP",
        "cap": result["cap"],
        "order_digest": result["order_digest"],
        "failure": result["failure"],
        "claim": result["claim"],
    }


def compile_source(formula, manifest):
    attempts = []
    best_result = None
    best_candidate = None
    best_key = None
    closed = 0
    opened = 0
    compiler_work = 0
    max_closed_peak = 0

    for candidate in manifest.candidates:
        result = v12.compile_order(formula, candidate.linear_leaf_order, q=FROZEN_Q)
        if result["terminal"] == "CLOSED_PSWIDTH_CAP":
            assert v12.replay_closed_certificate(formula, result)
            closed += 1
            max_closed_peak = max(max_closed_peak, result["peak_ps_state"])
            compiler_work += result["total_work_units"]
            key = selected_key(result)
            attempts.append(closed_summary(candidate.name, candidate.charged_ops, result))
            if best_key is None or key < best_key:
                best_key = key
                best_result = result
                best_candidate = candidate.name
        elif result["terminal"] == "OPEN_STATE_CAP":
            opened += 1
            assert result["failure"]["distinct_states_at_refusal"] == result["cap"] + 1
            compiler_work += result["failure"]["ledger"]["total_work_units"]
            attempts.append(open_summary(candidate.name, candidate.charged_ops, result))
        else:
            raise AssertionError(result["terminal"])

    cap = max(2, len(v12.all_incidence_leaves(formula)))
    common = {
        "q": FROZEN_Q,
        "cap": cap,
        "candidate_attempts": len(attempts),
        "closed_candidates": closed,
        "open_candidates": opened,
        "slime_manifest_generation_ops": manifest.total_generation_ops,
        "compiler_total_work_units": compiler_work,
        "max_closed_peak_ps_state": max_closed_peak,
        "max_closed_peak_over_cap": (max_closed_peak / cap) if closed else None,
        "attempts": attempts,
    }

    if best_result is None:
        first_open = next(row for row in attempts if row["terminal"] == "OPEN_STATE_CAP")
        cheapest_open = min(
            (row for row in attempts if row["terminal"] == "OPEN_STATE_CAP"),
            key=lambda row: row["failure"]["ledger"]["total_work_units"],
        )
        return {
            **common,
            "terminal": "OPEN_PORTFOLIO_CAP_EXHAUSTED",
            "first_open_candidate": first_open["candidate"],
            "first_open_phase": first_open["failure"]["phase"],
            "first_open_node": first_open["failure"]["node_id"],
            "cheapest_open_candidate": cheapest_open["candidate"],
            "cheapest_open_work_units": cheapest_open["failure"]["ledger"]["total_work_units"],
            "claim": "CURRENT_SLIME_V3_Q1_PORTFOLIO_EXHAUSTED_ON_THIS_SOURCE_NOT_HARDNESS",
        }

    assert v12.replay_closed_certificate(formula, best_result)
    return {
        **common,
        "terminal": "CLOSED_PORTFOLIO_PSWIDTH_CAP",
        "selected_candidate": best_candidate,
        "selected_key": list(best_key),
        "selected_certificate": best_result["certificate"],
        "selected_certificate_replay": True,
    }


def run(slime_v3_class, producer_identity):
    router = slime_v3_class()

    # Phase 1: freeze every dense formula and every Slime manifest first.
    frozen = []
    for n, m, seed in FROZEN_ROWS:
        formula = v12.random_connected_3cnf(seed, n, m)
        manifest = router.generate_manifest(formula)
        frozen.append(
            {
                "n": n,
                "m": m,
                "seed": seed,
                "formula": formula,
                "formula_sha256": digest_json(formula),
                "manifest": manifest,
            }
        )

    frozen_batch = [
        (
            row["n"], row["m"], row["seed"],
            row["formula_sha256"], row["manifest"].manifest_sha256,
        )
        for row in frozen
    ]
    frozen_batch_sha256 = digest_json(frozen_batch)

    # Phase 2: bounded compilation only after full batch freeze.
    results = []
    first_exhausted = None
    total_closed_candidates = 0
    total_open_candidates = 0
    total_compiler_work = 0
    total_generation_ops = 0

    for row in frozen:
        portfolio = compile_source(row["formula"], row["manifest"])
        result_row = {
            "n": row["n"],
            "m": row["m"],
            "density": row["m"] / row["n"],
            "seed": row["seed"],
            "formula_sha256": row["formula_sha256"],
            "manifest_sha256": row["manifest"].manifest_sha256,
            "incidence_leaves": len(v12.all_incidence_leaves(row["formula"])),
            "portfolio": portfolio,
        }
        results.append(result_row)
        total_closed_candidates += portfolio["closed_candidates"]
        total_open_candidates += portfolio["open_candidates"]
        total_compiler_work += portfolio["compiler_total_work_units"]
        total_generation_ops += portfolio["slime_manifest_generation_ops"]
        if (
            first_exhausted is None
            and portfolio["terminal"] == "OPEN_PORTFOLIO_CAP_EXHAUSTED"
        ):
            first_exhausted = {
                "n": row["n"],
                "m": row["m"],
                "seed": row["seed"],
                "formula_sha256": row["formula_sha256"],
                "manifest_sha256": row["manifest"].manifest_sha256,
                "cap": portfolio["cap"],
                "compiler_total_work_units": portfolio["compiler_total_work_units"],
            }

    exhausted_count = sum(
        row["portfolio"]["terminal"] == "OPEN_PORTFOLIO_CAP_EXHAUSTED"
        for row in results
    )
    terminal = (
        "CURRENT_SLIME_V3_Q1_UNIVERSAL_COMPLETENESS_REFUTED_BY_FINITE_COUNTEREXAMPLE"
        if exhausted_count
        else "NO_Q1_ESCAPE_FOUND_ON_THIS_FROZEN_DENSE_LADDER"
    )

    output = {
        "artifact_id": "PF5-SLIME-Q1-DENSE-3SAT-FALSIFICATION-V13",
        "status": "FINITE_FALSIFICATION_LADDER_COMPLETE",
        "producer": producer_identity,
        "q_unchanged_from_v12": FROZEN_Q,
        "frozen_rows": [list(row) for row in FROZEN_ROWS],
        "all_formulas_and_manifests_frozen_before_compilation": True,
        "frozen_batch_sha256": frozen_batch_sha256,
        "runtime_exact_scorer_used": False,
        "runtime_sat_oracle_used": False,
        "runtime_cap_escalation_used": False,
        "results": results,
        "exhausted_sources": exhausted_count,
        "first_exhausted": first_exhausted,
        "terminal_interpretation": terminal,
        "global_ledger": {
            "slime_generation_ops": total_generation_ops,
            "compiler_work_units": total_compiler_work,
            "candidate_attempts": len(results) * 16,
            "closed_candidates": total_closed_candidates,
            "open_candidates": total_open_candidates,
        },
        "universal_some_fixed_q_completeness": "OPEN",
        "p_vs_np": "OPEN",
    }
    output["result_sha256"] = digest_json(output)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-path", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    raw = args.producer_path.read_bytes()
    module = v12.import_slime_v3(args.producer_path)
    result = run(
        module.SlimeSemanticCandidateSwarmV3Amortized,
        {
            "commit": "421794b5c7e3b96f52550cf710fe2d8d2f3b59db",
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "UNCHANGED_PINNED_SLIME_V3_CANDIDATE_PRODUCER",
        },
    )

    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print("PF5_SLIME_Q1_DENSE_3SAT_FALSIFICATION_V13 =", result["status"])
    print("FROZEN_BATCH_SHA256 =", result["frozen_batch_sha256"])
    print("EXHAUSTED_SOURCES =", result["exhausted_sources"])
    print("FIRST_EXHAUSTED =", result["first_exhausted"])
    for row in result["results"]:
        p = row["portfolio"]
        print(
            "N", row["n"], "M", row["m"], "SEED", row["seed"],
            p["terminal"], "CAP", p["cap"],
            "CLOSED", p["closed_candidates"],
            "OPEN", p["open_candidates"],
            "MAX_CLOSED_PEAK", p["max_closed_peak_ps_state"],
            "SELECTED", p.get("selected_candidate"),
        )
    print("TERMINAL_INTERPRETATION =", result["terminal_interpretation"])
    print("GLOBAL_LEDGER =", result["global_ledger"])
    print("UNIVERSAL_SOME_FIXED_q_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
