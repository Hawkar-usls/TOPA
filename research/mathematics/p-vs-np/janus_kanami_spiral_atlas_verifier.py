#!/usr/bin/env python3
"""Fail-closed verifier for the JANUS P-vs-NP Kanami spiral method atlas.

This validates provenance/classification consistency only.  It does not promote
new SAT operators and does not claim P=NP.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha1, sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ATLAS_PATH = ROOT / "data" / "JANUS-PNP-KANAMI-SPIRAL-METHOD-ATLAS-2026-08-25-v1.0.json"
FROZEN_PATH = ROOT / "data" / "JANUS-PNP-REVERSE-SPIRAL-METHOD-UNIFICATION-2026-08-25-v1.0.json"

EXPECTED_ACTIVE = (
    "PURE_LITERAL_EXISTS",
    "TAUTOLOGICAL_RESOLVENT_EXISTS",
    "SINGLE_NTR_EXISTS",
    "COMPLEMENTARY_TWIN",
    "CLAUSE_SUBSUMPTION",
    "SELF_SUBSUMING_RESOLUTION",
    "COMPONENT_PRODUCT",
    "TWO_SAT_SCC",
    "AFFINE_GF2_JOIN",
    "ACI_SHARED_FACTOR",
    "LITERAL_ACI_EXISTS",
    "SYMMETRIC_WEIGHT_EXISTS",
    "SWAP_ORBIT_WEIGHT_EXISTS",
    "SWAP_ORBIT_WEIGHT_EXISTS_CLOSED",
)

EXPECTED_MISSED_RANKING = (
    "FIRST_CLASS_EXACT_RESTRICTION_PARTIAL_ASSIGNMENT",
    "CONTEXT_CERTIFIED_TRANSITION_CONGRUENCE",
    "UNIFY_OLD_Q_TOTAL_CRITERION_WITH_NEW_9D_FRONTIER_ACCOUNTING",
    "UNIFORM_STATE_CAP_NOT_GLOBAL_PROGRESS",
    "DEAD_STATE_GC_AND_WITNESS_BYTE_TRANSFER",
    "EXACT_SCHEMA_RECOGNITION_AS_TYPED_OPERATOR_FAMILY",
    "REATTACH_UP_FAILED_LITERAL_BCE",
)


def git_blob_sha(data: bytes) -> str:
    return sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def load(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    return json.loads(raw), raw


def flatten_frozen(frozen: dict) -> list[dict]:
    return [m for phase in frozen["reverse_spiral"] for m in phase["methods"]]


def main() -> None:
    atlas, atlas_raw = load(ATLAS_PATH)
    frozen, frozen_raw = load(FROZEN_PATH)

    assert atlas["schema"] == "JANUS_PNP_KANAMI_SPIRAL_METHOD_ATLAS"
    assert atlas["primary_goal"] == "RESOLVE_P_VS_NP"
    assert atlas["claim_ceiling"] == "P_VS_NP_OPEN"
    assert atlas["global_rule"] == "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT"
    assert atlas["P_VS_NP"] == "OPEN"
    assert atlas["universal_polynomial_sat_algorithm"] == "NOT_ESTABLISHED"

    frozen_rows = flatten_frozen(frozen)
    atlas_rows = atlas["legacy_76_method_atlas"]
    assert len(frozen_rows) == 76
    assert len(atlas_rows) == 76
    assert atlas["inherits_frozen_manifest"]["legacy_method_count"] == 76

    frozen_pairs = [(m["id"], m["status"]) for m in frozen_rows]
    atlas_pairs = [(m["id"], m["status"]) for m in atlas_rows]
    assert atlas_pairs == frozen_pairs, "legacy atlas must preserve frozen ID/status order exactly"
    assert len({m["id"] for m in atlas_rows}) == 76
    assert all(isinstance(m.get("gives"), str) and m["gives"] for m in atlas_rows)

    frozen_counts = Counter(m["status"] for m in frozen_rows)
    atlas_counts = Counter(m["status"] for m in atlas_rows)
    assert frozen_counts == atlas_counts

    active = tuple(atlas["active_keymaster_catalog_unchanged"])
    assert active == EXPECTED_ACTIVE
    assert len(active) == 14

    # No missed node may acquire active SAT authority in this atlas.
    missed = atlas["missed_or_underrepresented_nodes"]
    assert len(missed) == 12
    assert all(m["status"] != "ACTIVE_EXACT" for m in missed)
    assert all(m.get("missed_in_v1") is True for m in missed)

    sourced = 0
    reattach = 0
    source_receipts = []
    for m in missed:
        source = m.get("source")
        if source:
            p = ROOT / source
            assert p.is_file(), (m["id"], source)
            raw = p.read_bytes()
            observed = git_blob_sha(raw)
            assert observed == m["source_blob_sha"], (m["id"], observed, m["source_blob_sha"])
            sourced += 1
            source_receipts.append({"id": m["id"], "git_blob_sha": observed})
        else:
            assert m.get("source_reattachment_required") is True
            assert m["status"] == "HISTORICAL_EXACT_CANDIDATE_NEEDS_SOURCE_REATTACHMENT"
            reattach += 1
    assert sourced == 9
    assert reattach == 3

    passes = atlas["kanami_spiral_passes"]
    assert [p["pass"] for p in passes] == list(range(len(passes)))
    assert len(passes) == 6
    assert [p["direction"] for p in passes] == ["REVERSE", "FORWARD", "REVERSE", "FORWARD", "REVERSE", "FORWARD"]
    assert passes[-1]["fixed_point"] is True
    assert passes[-1]["new_findings"] == []
    assert "not a claim" in passes[-1]["fixed_point_scope"].lower()
    assert all(p["new_findings"] for p in passes[:-1])

    ranked = atlas["janus_missed_summary_ranked"]
    assert tuple(x["id"] for x in ranked) == EXPECTED_MISSED_RANKING
    assert [x["rank"] for x in ranked] == list(range(1, len(ranked) + 1))

    next_gate = atlas["next_exact_gate"]
    assert next_gate["id"] == "U1_L2C2C2R_RESTRICTION_CONGRUENCE_BRIDGE"
    instruction = next_gate["instruction"]
    assert "RESTRICT" in instruction
    assert "INTACT_GATE_CONGRUENCE_REUSE" in instruction
    assert "Q_total" in instruction

    obligations = atlas["new_proof_obligation_graph"]["P_EQUALS_NP_ROUTE"]
    assert obligations[0] == "O1_TYPED_EXACT_RESTRICTION_AND_WITNESS_MERGE"
    assert obligations[-1] == "SAT_IN_P_THEREFORE_P_EQUALS_NP"
    assert "P_VS_NP" in atlas["new_proof_obligation_graph"]["still_open"]

    # Frozen baseline blob is immutable and explicitly linked.
    observed_frozen_blob = git_blob_sha(frozen_raw)
    assert observed_frozen_blob == atlas["inherits_frozen_manifest"]["blob_sha"]

    payload = {
        "schema": "JANUS_PNP_KANAMI_SPIRAL_ATLAS_VERIFICATION_RESULT",
        "status": "PASS_KANAMI_SPIRAL_FIXED_POINT_AUDIT",
        "claim_ceiling": "P_VS_NP_OPEN",
        "legacy_method_count": len(atlas_rows),
        "legacy_status_counts": dict(sorted(atlas_counts.items())),
        "missed_or_underrepresented_count": len(missed),
        "missed_with_current_source_receipt": sourced,
        "historical_candidates_requiring_source_reattachment": reattach,
        "active_keymaster_operator_count": len(active),
        "active_catalog_changed": False,
        "kanami_pass_count": len(passes),
        "kanami_direction_sequence": [p["direction"] for p in passes],
        "audited_fixed_point": True,
        "fixed_point_scope_limited": True,
        "highest_priority_missed_bridge": ranked[0]["id"],
        "second_priority_missed_bridge": ranked[1]["id"],
        "central_reframing": "GLOBAL_PROGRESS_EXISTS_FOR_DP_ELIMINATION_BUT_UNIFORM_CANONICAL_STATE_BOUND_REMAINS_OPEN",
        "next_exact_gate": next_gate["id"],
        "atlas_sha256": sha256(atlas_raw).hexdigest(),
        "frozen_manifest_git_blob_sha": observed_frozen_blob,
        "source_receipts": source_receipts,
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
    }
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    print("JANUS_PNP_KANAMI_SPIRAL = PASS")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("JANUS_PNP_KANAMI_SPIRAL_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
