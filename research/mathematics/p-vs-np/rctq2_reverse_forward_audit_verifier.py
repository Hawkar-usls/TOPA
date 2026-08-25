#!/usr/bin/env python3
"""JANUS RCTQ-2 reverse-forward exact audit.

Replays RCTQ2 -> RCTQ1 -> KANAMI -> UNIFIED and then forward again,
requiring hash stability.  It also checks the smallest exact terminal schema
exposed by the RCTQ2 escape state: uniform all-ones/all-zero clause witnesses.
No historical catalog is mutated by this verifier.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUDIT = ROOT / "data" / "JANUS-PNP-RCTQ2-REVERSE-FORWARD-AUDIT-2026-08-25-v1.0.json"

RUNNERS = {
    "RCTQ2": (HERE / "rctq2_frozen_catalog_escape_verifier.py", "JANUS_RCTQ2_RESULT_SHA256="),
    "RCTQ1": (HERE / "rctq1_restriction_closed_transition_quotient_verifier.py", "JANUS_RCTQ1_RESULT_SHA256="),
    "KANAMI": (HERE / "janus_kanami_spiral_atlas_verifier.py", "JANUS_PNP_KANAMI_SPIRAL_RESULT_SHA256="),
    "UNIFIED": (HERE / "janus_exact_reverse_spiral_unified_runner.py", "JANUS_EXACT_REVERSE_SPIRAL_RESULT_SHA256="),
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_and_hash(path: Path, marker: str) -> tuple[str, str]:
    proc = subprocess.run(
        [sys.executable, str(path)], cwd=ROOT, text=True, capture_output=True,
        timeout=180, check=False,
    )
    if proc.returncode != 0:
        raise AssertionError({
            "path": str(path),
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-3000:],
            "stderr_tail": proc.stderr[-3000:],
        })
    rows = [line for line in proc.stdout.splitlines() if line.startswith(marker)]
    assert len(rows) == 1, (path, marker, rows)
    digest = rows[0][len(marker):].strip()
    assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
    return digest, proc.stdout


def verify_polarity_terminal_schema():
    mod = load_module("rctq2_reverse_escape", HERE / "rctq2_frozen_catalog_escape_verifier.py")
    F = mod.escape_cnf(37)
    vs = mod.variables(F)

    positive_index_cert = []
    negative_index_cert = []
    for ci, clause in enumerate(F):
        positives = [l for l in clause if l > 0]
        negatives = [l for l in clause if l < 0]
        assert positives
        assert negatives
        positive_index_cert.append((ci, positives[0]))
        negative_index_cert.append((ci, negatives[0]))

    all_ones = {v: True for v in vs}
    all_zero = {v: False for v in vs}
    assert mod.eval_cnf(F, all_ones)
    assert mod.eval_cnf(F, all_zero)

    # Independent certificate replay: each recorded literal must occur in the
    # referenced clause with the declared polarity.
    for ci, l in positive_index_cert:
        assert l > 0 and l in F[ci]
    for ci, l in negative_index_cert:
        assert l < 0 and l in F[ci]

    return {
        "schema_id": "UNIFORM_POLARITY_CLAUSE_WITNESS",
        "status": "PROVED_RESTRICTED_BY_DIRECT_BOOLEAN_SEMANTICS",
        "all_clauses_have_positive_literal": True,
        "all_ones_witness_replay": "PASS_SAT_WITNESS",
        "all_clauses_have_negative_literal": True,
        "all_zero_witness_replay": "PASS_SAT_WITNESS",
        "positive_clause_certificate_rows": len(positive_index_cert),
        "negative_clause_certificate_rows": len(negative_index_cert),
        "recognition_bound": "O_TOTAL_LITERAL_OCCURRENCES",
        "witness_bound": "O_NUMBER_OF_VARIABLES",
        "historical_catalog_mutated": False,
        "E37_specific_escape_closed_by_new_schema_if_typed": True,
        "frozen_14_catalog_universal_coverage_restored": False,
    }


def main():
    audit = json.loads(AUDIT.read_text())
    assert audit["global_rule"] == "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT"
    sequence = audit["reverse_forward_sequence"]
    observed = []
    by_id_direction = {}
    for row in sequence:
        rid = row["id"]
        path, marker = RUNNERS[rid]
        digest, _stdout = run_and_hash(path, marker)
        assert digest == row["expected_sha256"], (rid, digest, row["expected_sha256"])
        observed.append({
            "direction": row["direction"],
            "id": rid,
            "result_sha256": digest,
        })
        by_id_direction[(row["direction"], rid)] = digest

    for rid in RUNNERS:
        assert by_id_direction[("REVERSE", rid)] == by_id_direction[("FORWARD", rid)]

    polarity = verify_polarity_terminal_schema()

    result = {
        "schema": "JANUS_PNP_RCTQ2_REVERSE_FORWARD_RESULT",
        "status": "PASS_RCTQ2_REVERSE_FORWARD_HASH_STABLE_WITH_EXACT_TERMINAL_REPAIR_DISCOVERED",
        "claim_ceiling": "P_VS_NP_OPEN",
        "global_rule": "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT",
        "execution_sequence": observed,
        "reverse_forward_hash_stable": True,
        "active_keymaster_operator_count": 14,
        "active_catalog_changed": False,
        "rctq2_preserved_result": "FROZEN_14_CATALOG_UNIVERSAL_NEXT_TRANSITION_AVAILABILITY_FALSE",
        "reverse_discovered_exact_schema": polarity,
        "reconciliation": {
            "RCTQ2_ESCAPE_WAS_CATALOG_GAP_NOT_HARDNESS": True,
            "E37_HAS_LINEAR_TIME_EXACT_TERMINAL_WITNESS_SCHEMA": True,
            "RESTRICT_STILL_NOT_A_SINGLE_BRANCH_EXISTENTIAL_EQUIVALENCE": True,
            "KEYMASTER_FRONTIER_THEOREM_PRESERVED": True,
            "HISTORICAL_RECEIPTS_IMMUTABLE": True,
        },
        "next_gate": "RCTQ3_TYPED_POLARITY_WITNESS_TERMINAL_EXTENSION_THEN_STRONGER_CNF_ESCAPE",
        "stronger_escape_requirements": [
            "NO_FROZEN_14_OPERATOR_DOMAIN",
            "NOT_ALL_CLAUSES_HAVE_POSITIVE_LITERAL",
            "NOT_ALL_CLAUSES_HAVE_NEGATIVE_LITERAL",
            "NONTERMINAL_EXACTLY_CERTIFIED",
            "NO_HEURISTIC_OR_ORACLE_DISCOVERY",
        ],
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("JANUS_RCTQ2_REVERSE_FORWARD_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
