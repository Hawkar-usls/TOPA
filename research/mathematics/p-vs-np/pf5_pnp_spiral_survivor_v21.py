#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pf5_clause_subsumption_contraction_v20 as v20


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def run():
    rows = []
    first_survivor = None
    first_terminal_true = None

    # Reuse the already pre-frozen v20 holdout verbatim. Locator only.
    for n, m, seeds in v20.FROZEN_GROUPS:
        for seed in seeds:
            source = v20.v18.v12.canonical_formula(
                v20.v18.v9.random_connected_3cnf(
                    seed, variable_count=n, clause_count=m
                )
            )
            final, transcript, runtime = v20.exact_closure(source)
            assert v20.replay(source, transcript) == final
            crystal = v20.v18.v14.crystal(final)
            status = v20.terminal_status(final)
            row = {
                "n": n,
                "m": m,
                "seed": seed,
                "source_crystal_sha256": v20.v18.v14.crystal(source)["sha256"],
                "final_crystal": crystal,
                "terminal_status": status,
                "subsumption_steps": v20.count_kind(
                    transcript, "CLAUSE_SUBSUMPTION"
                ),
                "twin_steps": v20.count_kind(transcript, "COMPLEMENTARY_TWIN"),
                "single_resolvent_steps": v20.count_kind(
                    transcript, "SINGLE_RESOLVENT"
                ),
                "pure_steps": v20.count_kind(transcript, "PURE_LITERAL"),
                "transcript_sha256": digest(transcript),
                "runtime_ledger": runtime,
            }
            rows.append(row)
            if first_survivor is None and status == "OPEN_RESIDUAL":
                first_survivor = row
            if first_terminal_true is None and status == "TRUE":
                first_terminal_true = row

    assert first_survivor is not None
    assert first_terminal_true is not None
    result = {
        "artifact_id": "PF5-PNP-SPIRAL-SURVIVOR-V21",
        "status": "FINITE_FROZEN_LOCATOR_COMPLETE",
        "input_holdout": "V20_FRESH_FROZEN_GROUPS_UNCHANGED",
        "case_count": len(rows),
        "decision_heuristic": False,
        "new_solver": False,
        "uses_sat_oracle": False,
        "uses_pswidth_score": False,
        "uses_hephaestus_for_decision": False,
        "first_survivor": first_survivor,
        "first_terminal_true": first_terminal_true,
        "survivor_count": sum(
            row["terminal_status"] == "OPEN_RESIDUAL" for row in rows
        ),
        "terminal_true_count": sum(
            row["terminal_status"] == "TRUE" for row in rows
        ),
        "rows_manifest_sha256": digest(
            [
                (
                    row["n"],
                    row["m"],
                    row["seed"],
                    row["final_crystal"]["sha256"],
                    row["terminal_status"],
                )
                for row in rows
            ]
        ),
        "next_gate": "STRUCTURAL_AUDIT_FIRST_V20_SURVIVOR",
        "hephaestus_role": "ACCOUNTING_RECURRENCE_ONLY_NO_DECISION_AUTHORITY",
        "universal_exact_closure": "OPEN",
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
    first = result["first_survivor"]
    solved = result["first_terminal_true"]
    print("PF5_PNP_SPIRAL_SURVIVOR_V21 =", result["status"])
    print("SURVIVOR_COUNT =", result["survivor_count"])
    print("TERMINAL_TRUE_COUNT =", result["terminal_true_count"])
    print("FIRST_SURVIVOR =", (first["n"], first["m"], first["seed"]))
    print("FIRST_SURVIVOR_SHA256 =", first["final_crystal"]["sha256"])
    print("FIRST_SURVIVOR_CNF =", first["final_crystal"]["canonical_cnf"])
    print("FIRST_TERMINAL_TRUE =", (solved["n"], solved["m"], solved["seed"]))
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
