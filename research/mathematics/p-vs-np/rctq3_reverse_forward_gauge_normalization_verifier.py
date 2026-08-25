#!/usr/bin/env python3
"""JANUS RCTQ-3 reverse-forward audit with exact signed-polarity normalization.

The discovered normalization is an exact SAT-equivalent representation change,
not state-count compression and not a universal SAT progress theorem.
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

EXPECTED = {
    "UNIFIED": (HERE / "janus_exact_reverse_spiral_unified_runner.py", "JANUS_EXACT_REVERSE_SPIRAL_RESULT_SHA256=", "56a1e2e236df91385c6de91c91297aa7f5d093fcc56391252775796b3dd380f3"),
    "KANAMI": (HERE / "janus_kanami_spiral_atlas_verifier.py", "JANUS_KANAMI_SPIRAL_RESULT_SHA256=", "9a5b446c9fc012922608b01ce16e16d9c3872205f3f4db7811f5adc6d72fe586"),
    "RCTQ1": (HERE / "rctq1_restriction_closed_transition_quotient_verifier.py", "JANUS_RCTQ1_RESULT_SHA256=", "40b55b403a4ed1aca7defe163f33148b75851a309e08c66a7111ff7d85086e73"),
    "RCTQ2": (HERE / "rctq2_frozen_catalog_escape_verifier.py", "JANUS_RCTQ2_RESULT_SHA256=", "469534dfad8c8612755a3443499ae03ff51386182907f46b11fefc907f2b8b90"),
    "RCTQ3": (HERE / "rctq3_polarity_gauged_escape_verifier.py", "JANUS_RCTQ3_RESULT_SHA256=", "ffb183b16962919ac3f84420d851fae772a8ff7deaae2dc8d56a57a8a1ef2526"),
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


r3 = load_module("rctq3_reverse_provider", HERE / "rctq3_polarity_gauged_escape_verifier.py")

NORMALIZE = r3.km.base.Operator(
    "SIGNED_POLARITY_COUNT_NORMALIZE",
    "CNF",
    "CNF",
    "EXISTS_VARIABLE_WITH_NEGATIVE_OCCURRENCES_GT_POSITIVE_OCCURRENCES",
    "INDEPENDENT_VARIABLE_COMPLEMENTATION_IS_SAT_BIJECTION",
    "FLIP_VECTOR_PLUS_SOURCE_TARGET_HASH",
    "O_TOTAL_LITERAL_OCCURRENCES_PLUS_CANONICAL_SERIALIZATION",
    "XOR_FLIP_VECTOR_ON_WITNESS",
)


def run_hash(identifier: str):
    path, marker, expected = EXPECTED[identifier]
    proc = subprocess.run([sys.executable, str(path)], cwd=ROOT, text=True, capture_output=True, timeout=180, check=False)
    if proc.returncode != 0:
        raise AssertionError((identifier, proc.returncode, proc.stdout[-2000:], proc.stderr[-2000:]))
    rows = [line for line in proc.stdout.splitlines() if line.startswith(marker)]
    assert len(rows) == 1, (identifier, rows)
    got = rows[0][len(marker):].strip()
    assert got == expected, (identifier, got, expected)
    return got


def signed_normalize(F):
    F = r3.r2.canonical_cnf(F)
    counts = r3.r2.polarity_counts(F)
    flips = {v: (neg > pos) for v, (pos, neg) in counts.items()}
    changed = tuple(sorted(v for v, b in flips.items() if b))
    out = r3.r2.canonical_cnf(
        tuple(tuple((-l if flips[abs(l)] else l) for l in c) for c in F)
    )
    post = r3.r2.polarity_counts(out)
    assert all(pos >= neg for pos, neg in post.values())
    cert = {
        "source_sha256": sha256(json.dumps(F, separators=(",", ":")).encode()).hexdigest(),
        "target_sha256": sha256(json.dumps(out, separators=(",", ":")).encode()).hexdigest(),
        "flipped_variables": list(changed),
        "source_noncanonical_variable_count": len(changed),
        "target_all_pos_count_ge_neg_count": True,
    }
    return out, flips, cert


def xor_witness(w, flips):
    return {v: (not bit if flips.get(v, False) else bit) for v, bit in w.items()}


def exact_normalization_replay():
    base, G = r3.gauged_escape_cnf(37)
    norm, flips, cert = signed_normalize(G)
    assert norm == base
    expected_flips = {v for v in r3.r2.variables(G) if r3.gauge_bit(v)}
    assert {v for v, b in flips.items() if b} == expected_flips

    # Involution replay with the emitted flip vector.
    back = r3.r2.canonical_cnf(tuple(tuple((-l if flips[abs(l)] else l) for l in c) for c in norm))
    assert back == G

    wG1, wG0 = r3.inherited_witnesses(G)
    wE1 = xor_witness(wG1, flips)
    wE0 = xor_witness(wG0, flips)
    assert all(wE1.values())
    assert not any(wE0.values())
    assert r3.r2.eval_cnf(base, wE1)
    assert r3.r2.eval_cnf(base, wE0)

    terminal = r3.polarity_terminal_certificate(norm)
    assert terminal["all_clauses_have_positive_literal"] is True
    assert terminal["all_clauses_have_negative_literal"] is True

    # Exact typed extension is valid, but old RCTQ-3 receipt remains immutable.
    catalog16 = tuple(r3.frozen15()) + (NORMALIZE,)
    summary = r3.km.base.validate_catalog(catalog16)
    assert summary["active_exact_operator_count"] == 16

    return {
        "schema_id": NORMALIZE.operator_id,
        "status": "PROVED_EXACT_REPRESENTATION_NORMALIZATION",
        "domain": NORMALIZE.domain_predicate,
        "theorem": NORMALIZE.theorem_id,
        "certificate": NORMALIZE.certificate_schema,
        "complexity": NORMALIZE.complexity_bound,
        "witness_lift": NORMALIZE.witness_lift,
        "G37_to_E37_exact": True,
        "flipped_variable_count": len(cert["flipped_variables"]),
        "normalized_state_has_uniform_polarity_terminal": True,
        "composition": "G37 -> SIGNED_POLARITY_COUNT_NORMALIZE -> E37 -> UNIFORM_POLARITY_CLAUSE_WITNESS -> TERMINAL",
        "is_state_count_compression": False,
        "is_universal_sat_progress": False,
        "candidate_extended_catalog_count": 16,
    }


def main():
    sequence = ["RCTQ3", "RCTQ2", "RCTQ1", "KANAMI", "UNIFIED", "UNIFIED", "KANAMI", "RCTQ1", "RCTQ2", "RCTQ3"]
    directions = ["REVERSE"] * 5 + ["FORWARD"] * 5
    execution = []
    for d, ident in zip(directions, sequence):
        execution.append({"direction": d, "id": ident, "result_sha256": run_hash(ident)})

    normalization = exact_normalization_replay()
    result = {
        "schema": "JANUS_RCTQ3_REVERSE_FORWARD_GAUGE_NORMALIZATION_RESULT",
        "status": "PASS_HASH_STABLE_WITH_EXACT_SIGNED_NORMALIZATION_DISCOVERED",
        "claim_ceiling": "P_VS_NP_OPEN",
        "global_rule": "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT",
        "execution_sequence": execution,
        "reverse_forward_hash_stable": True,
        "reverse_discovered_exact_schema": normalization,
        "historical_15_catalog_mutated": False,
        "rctq3_escape_interpretation": "CATALOG_GAP_CLOSED_FOR_GAUGED_FAMILY_BY_EXACT_REPRESENTATION_NORMALIZATION_NOT_BY_COMPRESSION",
        "next_gate": "RCTQ4_TYPED_SIGNED_NORMALIZATION_THEN_BALANCED_POLARITY_ESCAPE_WITH_NO_COUNT_GAUGE_DEFECT",
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("JANUS_RCTQ3_REVERSE_FORWARD_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
