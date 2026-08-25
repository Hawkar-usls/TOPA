#!/usr/bin/env python3
"""JANUS P=NP exact-only Konami reverse/forward fixed-point auditor.

The auditor traverses the frozen 76-node method corpus in both directions until
its exact capability/gap sets reach a fixed point.  It performs no ranking,
scoring, random search, heuristic selection, SAT-oracle discovery, or top-k
truncation.  It is a proof-obligation auditor, not a SAT solver and not a proof
that P=NP.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
BASE = DATA / "JANUS-PNP-REVERSE-SPIRAL-METHOD-UNIFICATION-2026-08-25-v1.0.json"
FULL = DATA / "JANUS-PNP-KONAMI-SPIRAL-FULL-METHOD-2026-08-25-v1.0.json"
RECEIPT = DATA / "JANUS-PNP-REVERSE-SPIRAL-UNIFIED-FIRST-TERMINAL-RECEIPT-2026-08-25-v1.0.json"

FROZEN_BASE_BLOB = "dc3f2bf922f03b438697e04cff558ef75a58aed3"
FROZEN_FULL_BLOB = "f6657e354d7f59c847f16697d61ba0ba7e296178"
FROZEN_FULL_COMMIT = "359645fa32cba8a29e1075c1c5d72108ec11287d"

# Explicit theorem/certificate facts only. Missing ids contribute inventory and
# status, but no inferred mathematical capability.
METHOD_FACTS = {
    "KEYMASTER_FRONTIER_PRODUCT_BOUND": {"FRONTIER_BOUND_CONDITIONAL"},
    "SWAP_ORBIT_WEIGHT_EXISTS": {"SWAP_ORBIT_QUOTIENT", "PAIR_SWAP_DISCOVERY_POLYNOMIAL"},
    "SWAP_ORBIT_WEIGHT_EXISTS_CLOSED": {"SEQUENTIAL_EXISTS_SWAP_ORBIT"},
    "SYMMETRIC_WEIGHT_EXISTS": {"HAMMING_WEIGHT_QUOTIENT", "SEQUENTIAL_EXISTS_WEIGHT"},
    "ACI_SHARED_FACTOR": {"ACI_QUOTIENT", "EXACT_REPRESENTATION_SWITCH"},
    "LITERAL_ACI_EXISTS": {"SEQUENTIAL_EXISTS_ACI"},
    "PURE_LITERAL_EXISTS": {"EXACT_LOCAL_CNF_REDUCTIONS", "LOCAL_WITNESS_LIFTS"},
    "TAUTOLOGICAL_RESOLVENT_EXISTS": {"EXACT_LOCAL_CNF_REDUCTIONS", "LOCAL_WITNESS_LIFTS"},
    "SINGLE_NTR_EXISTS": {"EXACT_LOCAL_CNF_REDUCTIONS", "LOCAL_WITNESS_LIFTS"},
    "COMPLEMENTARY_TWIN": {"EXACT_LOCAL_CNF_REDUCTIONS"},
    "CLAUSE_SUBSUMPTION": {"EXACT_LOCAL_CNF_REDUCTIONS"},
    "SELF_SUBSUMING_RESOLUTION": {"EXACT_LOCAL_CNF_REDUCTIONS"},
    "COMPONENT_PRODUCT": {"EXACT_COMPONENT_DECOMPOSITION", "COMPONENT_WITNESS_GLUE"},
    "TWO_SAT_SCC": {"CERTIFIED_2SAT_LEAF_DECISION", "REPLAYABLE_LEAF_CERTIFICATE"},
    "AFFINE_GF2_JOIN": {"EXACT_AFFINE_STATE", "REPLAYABLE_AFFINE_CERTIFICATE"},
    "STRONG_2SAT_BACKDOOR_K_LE_2": {"EXACT_FIXED_K_BACKDOOR_CLASS"},
    "ADAPTIVE_ACTION_GRAPH_FIXED_DEPTH": {"EXACT_FIXED_DEPTH_ACTION_CLASS"},
    "FIXED_ORDER_ROBDD": {"EXACT_ROBDD_CLASS"},
    "LIVE_WIDTH_FACTOR_DP": {"EXACT_BOUNDED_LIVE_WIDTH_CLASS"},
    "TREEWIDTH_PROJECTION_GRAMMAR": {"EXACT_BOUNDED_TREEWIDTH_CLASS"},
    "PS_WIDTH_SEMANTIC_CUT_QUOTIENT": {"EXACT_BOUNDED_PS_WIDTH_CLASS"},
    "ARTICULATION_SEPARATOR_DECOMPOSITION": {"EXACT_SEPARATOR_CLASS"},
    "TRANCEPTION_ORBIT_TEMPLATE": {"EXACT_RESTRICTED_ORBIT_CLASS"},
    "BLIND_LANGUAGE_RECOGNIZER_BOOTSTRAP": {"EXACT_RESTRICTED_LANGUAGE_RECOGNITION"},
    "HEPHAESTUS_CANONICAL_HASH_REVISIT": {"CANONICAL_SYNTACTIC_HASH", "EXACT_SYNTACTIC_RECURRENCE_GUARD"},
    "KEYMASTER_STATE_GUARD_TRANSITION_MEMORY": {"TYPED_EXACT_OPERATOR_DISPATCH"},
    "SLIME_EXACT_STATIC_INCIDENCE_FINGERPRINTS": {"EXACT_STATIC_STRUCTURAL_INVARIANTS"},
}

REPRESENTATION_TOKENS = {
    "ACI_QUOTIENT",
    "HAMMING_WEIGHT_QUOTIENT",
    "SWAP_ORBIT_QUOTIENT",
    "EXACT_AFFINE_STATE",
    "EXACT_ROBDD_CLASS",
    "EXACT_BOUNDED_PS_WIDTH_CLASS",
}

PIVOT_SENSITIVE_TOKENS = {
    "EXACT_LOCAL_CNF_REDUCTIONS",
    "SEQUENTIAL_EXISTS_ACI",
    "SEQUENTIAL_EXISTS_WEIGHT",
    "SEQUENTIAL_EXISTS_SWAP_ORBIT",
}


def load() -> tuple[dict, dict, dict]:
    base = json.loads(BASE.read_text())
    full = json.loads(FULL.read_text())
    receipt = json.loads(RECEIPT.read_text())
    assert base["schema"] == "JANUS_PNP_REVERSE_SPIRAL_METHOD_UNIFICATION"
    assert full["schema"] == "JANUS_PNP_KONAMI_SPIRAL_FULL_METHOD"
    assert base["global_rule"] == "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT"
    assert full["global_rule"] == base["global_rule"]
    assert full["canonical_method_corpus"]["blob_sha"] == FROZEN_BASE_BLOB
    assert full["current_terminal_receipt"]["commit"] == "aa30c550db9f09b8bf2c074361a48c624959d00d"
    assert receipt["P_VS_NP"] == "OPEN"
    return base, full, receipt


def flatten(base: dict) -> list[dict]:
    rows = []
    for pidx, phase in enumerate(base["reverse_spiral"]):
        for midx, method in enumerate(phase["methods"]):
            rows.append({"pidx": pidx, "midx": midx, "phase": phase["phase"], **method})
    assert len(rows) == 76
    counts = Counter(r["status"] for r in rows)
    assert dict(counts) == {
        "ACTIVE_EXACT": 15,
        "PROVENANCE_ONLY": 5,
        "EXACT_RESTRICTED": 11,
        "BARRIER_NEGATIVE": 17,
        "PRUNED": 15,
        "GOVERNANCE_ONLY": 10,
        "ALGEBRAIZED": 3,
    }
    return rows


def exact_method_transfer(row: dict, capabilities: set[str], barriers: set[str]) -> None:
    status = row["status"]
    mid = row["id"]
    if status == "PRUNED":
        return
    if status == "BARRIER_NEGATIVE":
        barriers.add(mid)
        capabilities.add("BARRIER_MEMORY_ACTIVE")
        return
    capabilities.update(METHOD_FACTS.get(mid, set()))
    if status in {"ACTIVE_EXACT", "EXACT_RESTRICTED", "ALGEBRAIZED"}:
        capabilities.add("EXACT_METHOD_CORPUS_PRESENT")
    if status == "GOVERNANCE_ONLY":
        capabilities.add("FORMAL_GOVERNANCE_PRESENT")


def apply_capability_rules(full: dict, capabilities: set[str]) -> bool:
    changed = False
    for rule in full["capability_graph"]["rules"]:
        req = set(rule["requires"])
        if req <= capabilities:
            before = len(capabilities)
            capabilities.update(rule["gives"])
            changed |= len(capabilities) != before
    return changed


def infer_exact_gaps(full: dict, capabilities: set[str], barriers: set[str]) -> set[str]:
    gaps = set()
    candidates = {x["id"] for x in full["candidate_missed_obligations_to_test_by_fixed_point"]}

    # Direct global-algorithm obligations not established by the method corpus.
    global_rule = next(r for r in full["capability_graph"]["rules"] if r["id"] == "R_GLOBAL_P_ALGORITHM")
    for req in global_rule["requires"]:
        if req not in capabilities:
            gaps.add(req)

    # Second-order exact obligations surfaced by joining previously separate lanes.
    rep_count = len(REPRESENTATION_TOKENS & capabilities)
    if rep_count >= 2 and "CROSS_LANGUAGE_SEMANTIC_EQUIVALENCE_CERTIFICATE" not in capabilities:
        gaps.add("CROSS_LANGUAGE_SEMANTIC_EQUIVALENCE_CERTIFICATE")

    if (PIVOT_SENSITIVE_TOKENS & capabilities) and "PIVOT_ORDER_INVARIANCE_OR_POLY_BRANCH_QUOTIENT" not in capabilities:
        gaps.add("PIVOT_ORDER_INVARIANCE_OR_POLY_BRANCH_QUOTIENT")

    if "FRONTIER_BOUND_CONDITIONAL" in capabilities:
        if "POLY_CANONICAL_TRANSITION_STATE_COUNT" not in capabilities:
            gaps.add("POLY_CANONICAL_TRANSITION_STATE_COUNT")
        if "POLY_CUMULATIVE_COST_BOUNDS" not in capabilities:
            gaps.add("POLY_CUMULATIVE_COST_BOUNDS")

    if rep_count >= 2 and "EXACT_SYNTACTIC_RECURRENCE_GUARD" in capabilities:
        if "WELL_FOUNDED_REPRESENTATION_SWITCHING" not in capabilities:
            gaps.add("WELL_FOUNDED_REPRESENTATION_SWITCHING")

    if "LOCAL_WITNESS_LIFTS" in capabilities and "COMPONENT_WITNESS_GLUE" in capabilities:
        if "GLOBAL_CERTIFICATE_COMPOSITION" not in capabilities:
            gaps.add("GLOBAL_CERTIFICATE_COMPOSITION")
        if "GLOBAL_WITNESS_OR_UNSAT_LIFT" not in capabilities:
            gaps.add("GLOBAL_WITNESS_OR_UNSAT_LIFT")

    discovery_barriers = {
        "ROBDD_ORDER_DISCOVERY_BARRIER",
        "COMPRESSION_BLOCK_SEARCH_BARRIER",
        "PROJECTION_TARGET_RECOGNITION_BARRIER",
        "NONUNIFORM_VS_UNIFORM_PROJECTION",
    }
    if discovery_barriers & barriers and "POLY_DISCOVERY_AND_BUILD" not in capabilities:
        gaps.add("POLY_DISCOVERY_AND_BUILD")

    if {
        "SEQUENTIAL_EXISTS_ACI",
        "SEQUENTIAL_EXISTS_WEIGHT",
        "SEQUENTIAL_EXISTS_SWAP_ORBIT",
    } <= capabilities and "UNIVERSAL_SEQUENTIAL_EXISTENTIAL_CLOSURE" not in capabilities:
        gaps.add("UNIVERSAL_SEQUENTIAL_EXISTENTIAL_CLOSURE")

    if "EXACT_METHOD_CORPUS_PRESENT" in capabilities and "ARBITRARY_CNF_EXACT_CATALOG_COVERAGE" not in capabilities:
        gaps.add("ARBITRARY_CNF_EXACT_CATALOG_COVERAGE")

    assert gaps <= candidates
    return gaps


def passport(cycle: int, direction: str, capabilities: set[str], gaps: set[str], barriers: set[str], previous: dict | None) -> dict:
    vector = (len(capabilities), len(gaps), len(barriers))
    if previous is None:
        delta = (0, 0, 0)
        second = (0, 0, 0)
    else:
        pv = tuple(previous["vector"])
        delta = tuple(vector[i] - pv[i] for i in range(3))
        pd = tuple(previous["delta"])
        second = tuple(delta[i] - pd[i] for i in range(3))
    canonical = json.dumps({
        "capabilities": sorted(capabilities),
        "gaps": sorted(gaps),
        "barriers": sorted(barriers),
    }, sort_keys=True, separators=(",", ":")).encode()
    return {
        "cycle": cycle,
        "direction": direction,
        "vector_fields": ["capability_count", "gap_count", "barrier_count"],
        "vector": vector,
        "delta": delta,
        "second_delta": second,
        "canonical_sha256": sha256(canonical).hexdigest(),
        "authority": "MEMORY_RETRIEVAL_COMPARISON_ONLY_NOT_VERDICT",
    }


def main() -> None:
    base, full, receipt = load()
    rows = flatten(base)
    capabilities = set(full["capability_graph"]["initial_tokens"])
    capabilities.update({
        "EXACT_TRAJECTORY_PASSPORT",
        "EXACT_COST_FINITE_DIFFERENCE_VIEW",
        "SENSORY_PASSPORT_NOT_VERDICT",
    })
    barriers: set[str] = set()
    gaps: set[str] = set()
    passports: list[dict] = []
    previous_passport = None

    # Manifest order is current/end -> origin/beginning. Reverse it for forward synthesis.
    end_to_beginning = rows
    beginning_to_end = list(reversed(rows))

    fixed = False
    for cycle in range(1, 17):
        cycle_start = (frozenset(capabilities), frozenset(gaps), frozenset(barriers))
        for direction, sequence in (
            ("END_TO_BEGINNING", end_to_beginning),
            ("BEGINNING_TO_END", beginning_to_end),
        ):
            for row in sequence:
                exact_method_transfer(row, capabilities, barriers)
            while apply_capability_rules(full, capabilities):
                pass
            gaps = infer_exact_gaps(full, capabilities, barriers)
            p = passport(cycle, direction, capabilities, gaps, barriers, previous_passport)
            passports.append(p)
            previous_passport = p
        cycle_end = (frozenset(capabilities), frozenset(gaps), frozenset(barriers))
        if cycle_end == cycle_start:
            fixed = True
            fixed_cycle = cycle
            break
    assert fixed

    # Directional confluence: one additional reverse+forward and forward+reverse pair
    # must leave the same fixed-point sets.
    reference = (frozenset(capabilities), frozenset(gaps), frozenset(barriers))
    for sequence in (beginning_to_end, end_to_beginning, end_to_beginning, beginning_to_end):
        for row in sequence:
            exact_method_transfer(row, capabilities, barriers)
        while apply_capability_rules(full, capabilities):
            pass
        gaps = infer_exact_gaps(full, capabilities, barriers)
    assert (frozenset(capabilities), frozenset(gaps), frozenset(barriers)) == reference

    previous_debt = set(receipt["active_universal_debt"])
    newly_explicit = sorted(gaps - previous_debt - {"P_VS_NP", "GLOBAL_POLY_STATE_AND_WORK_FOR_ARBITRARY_CNF"})

    # Collapse the detailed gaps into exact macro-fronts without ranking them.
    macro_fronts = {
        "F1_COVERAGE_AND_PIVOT": sorted(gaps & {
            "ARBITRARY_CNF_EXACT_CATALOG_COVERAGE",
            "PIVOT_ORDER_INVARIANCE_OR_POLY_BRANCH_QUOTIENT",
            "UNIVERSAL_SEQUENTIAL_EXISTENTIAL_CLOSURE",
        }),
        "F2_STATE_CONGRUENCE_AND_FRONTIER": sorted(gaps & {
            "CROSS_LANGUAGE_SEMANTIC_EQUIVALENCE_CERTIFICATE",
            "POLY_CANONICAL_TRANSITION_STATE_COUNT",
            "POLY_CUMULATIVE_COST_BOUNDS",
        }),
        "F3_DISCOVERY_AND_TERMINATION": sorted(gaps & {
            "POLY_DISCOVERY_AND_BUILD",
            "WELL_FOUNDED_REPRESENTATION_SWITCHING",
        }),
        "F4_GLOBAL_PROOF_COMPOSITION": sorted(gaps & {
            "GLOBAL_CERTIFICATE_COMPOSITION",
            "GLOBAL_WITNESS_OR_UNSAT_LIFT",
        }),
    }
    assert all(macro_fronts.values())

    payload = {
        "schema": "JANUS_PNP_KONAMI_SPIRAL_FIXED_POINT_RESULT",
        "status": "PASS_EXACT_KONAMI_FIXED_POINT_AUDIT",
        "claim_ceiling": "P_VS_NP_OPEN",
        "frozen_full_method_commit": FROZEN_FULL_COMMIT,
        "frozen_full_method_blob_sha": FROZEN_FULL_BLOB,
        "base_method_count": len(rows),
        "global_rule": full["global_rule"],
        "fixed_point_cycle": fixed_cycle,
        "directional_confluence": True,
        "capability_count": len(capabilities),
        "barrier_count": len(barriers),
        "unresolved_obligation_count": len(gaps),
        "unresolved_obligations": sorted(gaps),
        "newly_explicit_vs_previous_terminal_receipt": newly_explicit,
        "macro_fronts": macro_fronts,
        "synesthetic_passport": {
            "status": full["synesthetic_memory_core_import"]["status"],
            "trajectory_passports_emitted": len(passports),
            "final_passport": passports[-1],
            "scientific_verdict_authority": False,
            "exact_recurrence_identity_authority": "ONLY_CANONICAL_SHA_OR_SEPARATE_EQUIVALENCE_CERTIFICATE",
            "what_it_exposed": "representation-switch termination/cycle control is a distinct proof obligation rather than a memory-layer task",
        },
        "passports": passports,
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
        "next_exact_target": "F2_STATE_CONGRUENCE_AND_FRONTIER__CROSS_LANGUAGE_PROOF_CARRYING_TRANSITION_CONGRUENCE_WITH_POLY_CLASS_BOUND",
    }
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    print("JANUS_KONAMI_SPIRAL_FIXED_POINT = PASS")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("JANUS_KONAMI_SPIRAL_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
