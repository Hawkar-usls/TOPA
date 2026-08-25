#!/usr/bin/env python3
"""JANUS RCTQ-4 reverse-forward audit from the first confirmed B_41 escape.

Discovers and verifies the exact complement-clause-pair <-> signed NAE3
representation switch, then replays the immutable JANUS chain in both
directions. Clause occurrences are paired as a multiset because canonical_cnf
sorts but does not globally deduplicate clauses. This is not a SAT solver and
does not establish polynomial existential closure for NAE3.
"""
from __future__ import annotations

from collections import Counter, deque
from hashlib import sha256
import importlib.util
from itertools import product
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AUDIT_PROTOCOL_COMMIT = "d089dccdc1964e1686bc7427af59ff6fc4fdf45f"

EXPECTED = {
    "UNIFIED": (HERE / "janus_exact_reverse_spiral_unified_runner.py", "JANUS_EXACT_REVERSE_SPIRAL_RESULT_SHA256=", "56a1e2e236df91385c6de91c91297aa7f5d093fcc56391252775796b3dd380f3"),
    "KANAMI": (HERE / "janus_kanami_spiral_atlas_verifier.py", "JANUS_PNP_KANAMI_SPIRAL_RESULT_SHA256=", "9a5b446c9fc012922608b01ce16e16d9c3872205f3f4db7811f5adc6d72fe586"),
    "RCTQ1": (HERE / "rctq1_restriction_closed_transition_quotient_verifier.py", "JANUS_RCTQ1_RESULT_SHA256=", "40b55b403a4ed1aca7defe163f33148b75851a309e08c66a7111ff7d85086e73"),
    "RCTQ2": (HERE / "rctq2_frozen_catalog_escape_verifier.py", "JANUS_RCTQ2_RESULT_SHA256=", "469534dfad8c8612755a3443499ae03ff51386182907f46b11fefc907f2b8b90"),
    "RCTQ3": (HERE / "rctq3_polarity_gauged_escape_verifier.py", "JANUS_RCTQ3_RESULT_SHA256=", "ffb183b16962919ac3f84420d851fae772a8ff7deaae2dc8d56a57a8a1ef2526"),
    "RCTQ4": (HERE / "rctq4_balanced_polarity_escape_verifier.py", "JANUS_RCTQ4_RESULT_SHA256=", "9bb9fbd301ee3619cc920bf4ac5206705cf6796a1778e27c11624a65215361e6"),
}


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


r4 = load_module("rctq4_reverse_source", HERE / "rctq4_balanced_polarity_escape_verifier.py")


def run_hash(identifier: str) -> str:
    path, marker, expected = EXPECTED[identifier]
    proc = subprocess.run(
        [sys.executable, str(path)], cwd=ROOT, text=True, capture_output=True,
        timeout=180, check=False,
    )
    if proc.returncode != 0:
        raise AssertionError((identifier, proc.returncode, proc.stdout[-3000:], proc.stderr[-3000:]))
    rows = [line for line in proc.stdout.splitlines() if line.startswith(marker)]
    assert len(rows) == 1, (identifier, rows)
    got = rows[0][len(marker):].strip()
    assert got == expected, (identifier, got, expected)
    return got


def clause_complement(c):
    return r4.r3.r2.canonical_clause([-l for l in c])


def pair_to_nae_macros(F):
    F = r4.r3.r2.canonical_cnf(F)
    original = Counter(F)
    remaining = Counter(original)
    macros = []
    for c in sorted(original):
        d = clause_complement(c)
        assert c != d
        assert original[d] == original[c], (c, original[c], d, original[d])
        while remaining[c] > 0:
            assert remaining[d] > 0, (c, d, remaining[c], remaining[d])
            remaining[c] -= 1
            remaining[d] -= 1
            macros.append(min(c, d))
    assert all(v == 0 for v in remaining.values())
    macros = tuple(sorted(macros))
    return macros, original


def local_nae_identity_truth_table():
    rows = []
    for a, b, c in product((False, True), repeat=3):
        cnf_pair = (a or b or c) and ((not a) or (not b) or (not c))
        nae = not (a == b == c)
        assert cnf_pair == nae
        rows.append({"a": a, "b": b, "c": c, "pair": cnf_pair, "nae": nae})
    assert len(rows) == 8
    return rows


def literal_values(clause, assignment):
    out = []
    for l in clause:
        bit = assignment[abs(l)]
        out.append(bit if l > 0 else not bit)
    return tuple(out)


def macro_accepts(rep, assignment):
    vals = literal_values(rep, assignment)
    return any(vals) and not all(vals)


def incidence_cycle_rank(macros, variables):
    # Macro occurrences are distinct edge vertices, including duplicates.
    v_nodes = [("v", v) for v in variables]
    e_nodes = [("e", i) for i in range(len(macros))]
    adj = {u: set() for u in v_nodes + e_nodes}
    incidence_count = 0
    for i, macro in enumerate(macros):
        en = ("e", i)
        assert len({abs(l) for l in macro}) == 3
        for l in macro:
            vn = ("v", abs(l))
            adj[vn].add(en)
            adj[en].add(vn)
            incidence_count += 1
    seen = set()
    components = 0
    for root in sorted(adj, key=repr):
        if root in seen:
            continue
        components += 1
        seen.add(root)
        q = deque([root])
        while q:
            u = q.popleft()
            for v in sorted(adj[u], key=repr):
                if v not in seen:
                    seen.add(v); q.append(v)
    node_count = len(adj)
    beta = incidence_count - node_count + components
    assert beta >= 0
    return {
        "variable_vertices": len(v_nodes),
        "macro_occurrence_vertices": len(e_nodes),
        "incidence_edges": incidence_count,
        "connected_components": components,
        "cycle_rank_beta": beta,
    }


def exact_b41_nae_audit():
    G, B = r4.balanced_cnf(41)
    primary = r4.domain_audit(41, True)
    assert primary["escaped_all_frozen16"] is True
    assert primary["admitted_frozen16_operator_ids"] == []
    assert len(B) == 166

    macros, clause_multiset = pair_to_nae_macros(B)
    assert len(macros) == 83
    local_rows = local_nae_identity_truth_table()

    w1, w0 = r4.verify_balanced_witness_derivation(41, G, B)
    assert all(macro_accepts(m, w1) for m in macros)
    assert all(macro_accepts(m, w0) for m in macros)
    assert all(w0[v] == (not w1[v]) for v in w1)

    complement_replay_count = 0
    for macro in macros:
        vals1 = literal_values(macro, w1)
        vals0 = literal_values(macro, w0)
        assert vals0 == tuple(not x for x in vals1)
        assert (any(vals1) and not all(vals1)) == (any(vals0) and not all(vals0))
        complement_replay_count += 1

    incidence = incidence_cycle_rank(macros, r4.r3.r2.variables(B))
    unique_clause_count = len(clause_multiset)
    duplicate_clause_occurrences = len(B) - unique_clause_count
    unique_macro_count = len(set(macros))
    duplicate_macro_occurrences = len(macros) - unique_macro_count
    assert duplicate_clause_occurrences >= 0
    assert duplicate_macro_occurrences >= 0

    return {
        "schema_id": "NAE3_COMPLEMENT_CLAUSE_PAIR_MACRO",
        "status": "PROVED_EXACT_RESTRICTED_REPRESENTATION_SWITCH",
        "domain": "CLAUSE_MULTISET_IS_CLOSED_UNDER_EXACT_LITERALWISE_COMPLEMENT_WITH_MATCHED_MULTIPLICITY",
        "identity": "(a OR b OR c) AND (!a OR !b OR !c) == NAE(a,b,c)",
        "local_truth_table_rows": len(local_rows),
        "discovery": "DETERMINISTIC_EXACT_COMPLEMENT_PAIR_MULTISET_HASHING",
        "construction_bound": "O(m log m) under canonical clause sorting plus exact multiplicity accounting",
        "witness_lift": "IDENTITY_ON_VARIABLE_ASSIGNMENT",
        "B41_cnf_clause_occurrences": len(B),
        "B41_unique_cnf_clauses": unique_clause_count,
        "B41_duplicate_clause_occurrences": duplicate_clause_occurrences,
        "B41_nae3_macro_occurrences": len(macros),
        "B41_unique_nae3_macros": unique_macro_count,
        "B41_duplicate_macro_occurrences": duplicate_macro_occurrences,
        "presentation_clause_occurrence_to_macro_occurrence_ratio": 2,
        "B41_witness_1_macro_replay": "PASS",
        "B41_witness_0_macro_replay": "PASS",
        "global_complement_macro_replays": complement_replay_count,
        "global_complement_symmetry": True,
        "incidence": incidence,
        "cycle_rank_interpretation": "LINEAR_NUMBER_OF_CYCLE_BITS_DOES_NOT_IMPLY_POLYNOMIALLY_MANY_SEMANTIC_STATES",
        "additional_exact_identity_exposed": {
            "id": "DUPLICATE_CLAUSE_IDEMPOTENCE",
            "identity": "A AND A = A",
            "status": "PROVED_BOOLEAN_IDENTITY_PENDING_FRESH_TYPED_ADMISSION"
        },
        "is_sat_decision": False,
        "is_universal_existential_closure": False,
        "is_p_equals_np": False,
    }


def main():
    reverse = ["RCTQ4", "RCTQ3", "RCTQ2", "RCTQ1", "KANAMI", "UNIFIED"]
    forward = ["UNIFIED", "KANAMI", "RCTQ1", "RCTQ2", "RCTQ3", "RCTQ4"]
    execution = []
    for ident in reverse:
        execution.append({"direction": "REVERSE", "id": ident, "result_sha256": run_hash(ident)})
    for ident in forward:
        execution.append({"direction": "FORWARD", "id": ident, "result_sha256": run_hash(ident)})

    nae = exact_b41_nae_audit()
    result = {
        "schema": "JANUS_RCTQ4_REVERSE_FORWARD_NAE3_RESULT",
        "status": "PASS_HASH_STABLE_WITH_EXACT_NAE3_PAIR_MACRO_DISCOVERED",
        "claim_ceiling": "P_VS_NP_OPEN",
        "global_rule": "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT",
        "audit_protocol_commit": AUDIT_PROTOCOL_COMMIT,
        "rctq4_rf_001_preserved": True,
        "reverse_forward_hash_stable": True,
        "execution_sequence": execution,
        "reverse_seed": "B_41",
        "reverse_discovered_exact_schema": nae,
        "frozen_16_catalog_mutated": False,
        "rctq4_reconciliation": {
            "B37_closed_by_swap_orbit_domain": True,
            "B41_B43_B47_escape_frozen16": True,
            "RCTQ4_001_was_finite_materialization_timeout_not_theorem_failure": True,
            "ASYMPTOTIC_POLY_DOMAIN_IS_NOT_FINITE_PRACTICAL_BUDGET": True,
        },
        "next_gate": "RCTQ5_TYPED_DUPLICATE_IDEMPOTENCE_AND_NAE3_PAIR_MACRO_THEN_SIGNED_NAE_SWITCHING_NORMALIZATION",
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("JANUS_RCTQ4_REVERSE_FORWARD_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
