#!/usr/bin/env python3
"""Exact reverse->forward reconciliation after JANUS RCTQ-1.

Executes only frozen exact verifiers/runners in an explicit sequence. No search,
ranking, scoring, thresholding or heuristic selection is present.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PNP = Path(__file__).resolve().parent
AUDIT_PATH = ROOT / "data" / "JANUS-PNP-RCTQ1-REVERSE-FORWARD-AUDIT-2026-08-25-v1.0.json"
KANAMI_RECEIPT_PATH = ROOT / "data" / "JANUS-PNP-KANAMI-SPIRAL-FIRST-TERMINAL-RECEIPT-2026-08-25-v1.0.json"
RCTQ_RECEIPT_PATH = ROOT / "data" / "JANUS-PNP-RCTQ1-FIRST-TERMINAL-RECEIPT-2026-08-25-v1.0.json"

SPECS = {
    "RCTQ1": {
        "path": PNP / "rctq1_restriction_closed_transition_quotient_verifier.py",
        "marker": "JANUS_RCTQ1_RESULT_SHA256=",
        "expected_sha": "40b55b403a4ed1aca7defe163f33148b75851a309e08c66a7111ff7d85086e73",
    },
    "KANAMI": {
        "path": PNP / "janus_kanami_spiral_atlas_verifier.py",
        "marker": "JANUS_PNP_KANAMI_SPIRAL_RESULT_SHA256=",
        "expected_sha": "9a5b446c9fc012922608b01ce16e16d9c3872205f3f4db7811f5adc6d72fe586",
    },
    "UNIFIED": {
        "path": PNP / "janus_exact_reverse_spiral_unified_runner.py",
        "marker": "JANUS_EXACT_REVERSE_SPIRAL_RESULT_SHA256=",
        "expected_sha": "56a1e2e236df91385c6de91c91297aa7f5d093fcc56391252775796b3dd380f3",
    },
}

SEQUENCE = ["RCTQ1", "KANAMI", "UNIFIED", "UNIFIED", "KANAMI", "RCTQ1"]
DIRECTIONS = ["REVERSE", "REVERSE", "REVERSE", "FORWARD", "FORWARD", "FORWARD"]


def parse_output(stdout: str, marker: str):
    lines = stdout.splitlines()
    marker_rows = [line for line in lines if line.startswith(marker)]
    assert len(marker_rows) == 1, (marker, marker_rows)
    result_sha = marker_rows[0][len(marker):].strip()
    assert len(result_sha) == 64

    # Extract the JSON object from the first line that begins with '{' through
    # the line immediately before the matching closing top-level object. Since
    # all frozen verifiers print one pretty JSON object, first/last braces are
    # unambiguous before the marker.
    marker_index = lines.index(marker_rows[0])
    before = lines[:marker_index]
    starts = [i for i, line in enumerate(before) if line.strip().startswith("{")]
    assert starts, stdout[-2000:]
    start = starts[0]
    end = max(i for i in range(start, len(before)) if before[i].strip() == "}")
    payload = json.loads("\n".join(before[start:end + 1]))
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    assert sha256(packed).hexdigest() == result_sha
    return payload, result_sha


def execute(name):
    spec = SPECS[name]
    assert spec["path"].is_file()
    proc = subprocess.run(
        [sys.executable, str(spec["path"])],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError({"name": name, "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:]})
    payload, result_sha = parse_output(proc.stdout, spec["marker"])
    assert result_sha == spec["expected_sha"]
    assert payload["P_VS_NP"] == "OPEN"
    return payload, result_sha


def main():
    audit = json.loads(AUDIT_PATH.read_text())
    kanami_receipt = json.loads(KANAMI_RECEIPT_PATH.read_text())
    rctq_receipt = json.loads(RCTQ_RECEIPT_PATH.read_text())

    assert audit["global_rule"] == "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT"
    assert audit["active_catalog_changed"] is False
    assert audit["active_keymaster_operator_count_before"] == 14
    assert audit["active_keymaster_operator_count_after"] == 14
    assert audit["new_central_gate"] == "RCTQ2_UNIVERSAL_EXACT_CAPPED_TRANSITION_AVAILABILITY_OR_FROZEN_CATALOG_ESCAPE_FAMILY"
    assert len(audit["janus_reconciliation"]) == 6
    assert rctq_receipt["first_run"]["result_sha256"] == SPECS["RCTQ1"]["expected_sha"]
    assert kanami_receipt["first_run"]["result_sha256"] == SPECS["KANAMI"]["expected_sha"]

    runs = []
    payloads = {}
    for direction, name in zip(DIRECTIONS, SEQUENCE):
        payload, h = execute(name)
        runs.append({"direction": direction, "id": name, "result_sha256": h})
        payloads.setdefault(name, payload)

    # Reverse and forward replay must be hash-stable.
    assert runs[0]["result_sha256"] == runs[-1]["result_sha256"]
    assert runs[1]["result_sha256"] == runs[-2]["result_sha256"]
    assert runs[2]["result_sha256"] == runs[3]["result_sha256"]

    rctq = payloads["RCTQ1"]
    kanami = payloads["KANAMI"]
    unified = payloads["UNIFIED"]

    assert rctq["barrier_theorem"]["ALL_RESTRICTION_FUTURE_CONGRUENCE_CLASSES_POLYNOMIAL"] is False
    assert rctq["critical_reframing"]["POLY_MATERIALIZED_DETERMINISTIC_TRACE_VOLUME"].startswith("OPEN")
    assert rctq["positive_theorems_verified"]["RESTRICT_EXACTNESS"] is True
    assert rctq["positive_theorems_verified"]["RCTQ1_CERTIFIED_ALIAS_LANGUAGE_RESTRICTION_CLOSED"] is True
    assert kanami["highest_priority_missed_bridge"] == "FIRST_CLASS_EXACT_RESTRICTION_PARTIAL_ASSIGNMENT"
    assert unified["cross_controls"]["frontier_explosion_64_preserved"] is True
    assert unified["separation_controls"]["heuristic_execution_surface"] == "EMPTY"

    payload = {
        "schema": "JANUS_PNP_RCTQ1_REVERSE_FORWARD_AUDIT_RESULT",
        "status": "PASS_RCTQ1_REVERSE_FORWARD_HASH_STABLE_RECONCILIATION",
        "claim_ceiling": "P_VS_NP_OPEN",
        "global_rule": audit["global_rule"],
        "execution_sequence": runs,
        "reverse_forward_hash_stable": True,
        "active_keymaster_operator_count": 14,
        "active_catalog_changed": False,
        "rctq1_positive_bridge": [
            "EXACT_RESTRICT_PARTIAL_ASSIGNMENT",
            "CERTIFIED_INTACT_B2_ALIAS_RESTRICTION_CLOSURE",
        ],
        "rctq1_negative_barrier": "ALL_COUNTERFACTUAL_RESTRICTION_FUTURE_CONGRUENCE_CLASSES_CAN_BE_2^n",
        "preserved_old_theorem": "KEYMASTER_FRONTIER_PRODUCT_BOUND_WITH_M_DEFINED_ON_ACTUALLY_MATERIALIZED_FRONTIER",
        "central_reframing": "BOUND_THE_ACTUAL_DETERMINISTIC_TRACE_NOT_THE_ENTIRE_RESTRICTION_UNIVERSE",
        "two_surviving_exact_routes": [
            "SINGLE_TRACE_UNIVERSAL_EXACT_CAPPED_TRANSITION_AVAILABILITY",
            "FRONTIER_POLYNOMIAL_MATERIALIZED_TRACE_VOLUME",
        ],
        "next_gate": audit["new_central_gate"],
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
    }
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("JANUS_RCTQ1_REVERSE_FORWARD_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
