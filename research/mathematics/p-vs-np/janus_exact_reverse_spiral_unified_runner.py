#!/usr/bin/env python3
"""JANUS exact-only reverse-spiral integration runner.

This runner is intentionally whitelist-only.  It validates the frozen reverse
spiral method manifest, runs only theorem-bearing exact verifiers explicitly
listed below, and refuses to execute historical heuristic/observer code.

It is an integration/consistency receipt.  It does NOT prove a universal
polynomial SAT algorithm and does NOT resolve P vs NP.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
PNP = Path(__file__).resolve().parent
MANIFEST = ROOT / "data" / "JANUS-PNP-REVERSE-SPIRAL-METHOD-UNIFICATION-2026-08-25-v1.0.json"

FROZEN_MANIFEST_COMMIT = "74db4cfa068289eaee82c5582755a19362148c48"
FROZEN_MANIFEST_BLOB_SHA = "dc3f2bf922f03b438697e04cff558ef75a58aed3"
ANCHOR_COMMIT = "10fee90e78dc3e205832fcec940e223c7bc0883e"

EXPECTED_ACTIVE_CATALOG = (
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

# This is the complete executable surface of this integration runner.
# No directory discovery, globbing, dynamic method selection or ranking exists.
EXACT_EXECUTION_WHITELIST = (
    {
        "id": "KEYMASTER_BASE",
        "path": PNP / "u1l2c2k_keymaster_exact_algebra_verifier.py",
        "marker": "U1L2C2K_RESULT_SHA256=",
        "status": "PASS_EXACT_METHOD_ALGEBRA",
    },
    {
        "id": "SWAP_ORBIT_C2C1",
        "path": PNP / "u1l2c2c1_swap_orbit_weight_quotient_verifier.py",
        "marker": "U1L2C2C1_RESULT_SHA256=",
        "status": "PASS_RESTRICTED_AUTOMATIC_EXACT_C2C_QUOTIENT",
    },
    {
        "id": "KEYMASTER_EXTENSION_K1",
        "path": PNP / "u1l2c2k1_keymaster_catalog_extension_verifier.py",
        "marker": "U1L2C2K1_RESULT_SHA256=",
        "status": "PASS_EXACT_CATALOG_EXTENSION",
    },
)


def load_manifest() -> dict:
    raw = MANIFEST.read_bytes()
    data = json.loads(raw)
    assert data["schema"] == "JANUS_PNP_REVERSE_SPIRAL_METHOD_UNIFICATION"
    assert data["claim_ceiling"] == "P_VS_NP_OPEN"
    assert data["primary_goal"] == "RESOLVE_P_VS_NP"
    assert data["global_rule"] == "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT"
    assert data["anchor_commit"] == ANCHOR_COMMIT
    assert tuple(data["unified_exact_keymaster_catalog"]) == EXPECTED_ACTIVE_CATALOG
    return data


def collect_methods(manifest: dict) -> tuple[list[dict], Counter]:
    rows: list[dict] = []
    counts: Counter = Counter()
    seen: set[tuple[str, str]] = set()
    for phase in manifest["reverse_spiral"]:
        phase_id = phase["phase"]
        for method in phase["methods"]:
            row = {"phase": phase_id, **method}
            key = (phase_id, method["id"])
            assert key not in seen
            seen.add(key)
            rows.append(row)
            counts[method["status"]] += 1
    return rows, counts


def validate_separation(manifest: dict, rows: list[dict]) -> dict:
    active_catalog = set(manifest["unified_exact_keymaster_catalog"])
    pruned = {r["id"] for r in rows if r["status"] == "PRUNED"}
    barriers = {r["id"] for r in rows if r["status"] == "BARRIER_NEGATIVE"}
    governance = {r["id"] for r in rows if r["status"] == "GOVERNANCE_ONLY"}

    assert active_catalog.isdisjoint(pruned)
    assert active_catalog.isdisjoint(barriers)
    assert active_catalog.isdisjoint(governance)

    executable_names = {spec["path"].name for spec in EXACT_EXECUTION_WHITELIST}
    assert len(executable_names) == len(EXACT_EXECUTION_WHITELIST)
    # Whitelist is literal and cannot be populated from method/history names.
    assert all("slime" not in n.lower() for n in executable_names)
    assert all("walksat" not in n.lower() for n in executable_names)
    assert all("physarum" not in n.lower() for n in executable_names)
    assert all("odonto" not in n.lower() for n in executable_names)

    forbidden_contract = set(manifest["admission_contract"]["forbidden"])
    required_contract = set(manifest["admission_contract"]["required"])
    assert "random_selection" in forbidden_contract
    assert "score_selection" in forbidden_contract
    assert "top_k" in forbidden_contract
    assert "sat_oracle_inside_runtime_discovery" in forbidden_contract
    assert "theorem_or_identity" in required_contract
    assert "replayable_certificate" in required_contract

    return {
        "active_catalog_count": len(active_catalog),
        "pruned_historical_method_count": len(pruned),
        "negative_barrier_count": len(barriers),
        "governance_method_count": len(governance),
        "executable_whitelist_count": len(EXACT_EXECUTION_WHITELIST),
        "pruned_disjoint_from_active": True,
        "barriers_disjoint_from_active": True,
        "governance_disjoint_from_active": True,
        "heuristic_execution_surface": "EMPTY",
    }


def parse_verifier_output(stdout: str, marker: str) -> tuple[dict, str]:
    lines = stdout.splitlines()
    marker_rows = [line for line in lines if line.startswith(marker)]
    assert len(marker_rows) == 1, (marker, marker_rows)
    result_sha = marker_rows[0][len(marker):].strip()
    assert len(result_sha) == 64 and all(c in "0123456789abcdef" for c in result_sha)
    json_lines = [line for line in lines if not line.startswith(marker)]
    payload = json.loads("\n".join(json_lines))
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    assert sha256(packed).hexdigest() == result_sha
    return payload, result_sha


def run_exact_verifiers() -> list[dict]:
    results: list[dict] = []
    for spec in EXACT_EXECUTION_WHITELIST:
        path: Path = spec["path"]
        assert path.is_file(), path
        proc = subprocess.run(
            [sys.executable, str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError({
                "verifier": spec["id"],
                "returncode": proc.returncode,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
            })
        payload, result_sha = parse_verifier_output(proc.stdout, spec["marker"])
        assert payload["claim_ceiling"] == "P_VS_NP_OPEN"
        assert payload["status"] == spec["status"]
        results.append({
            "id": spec["id"],
            "file": path.name,
            "status": payload["status"],
            "result_sha256": result_sha,
            "payload": payload,
        })
    return results


def validate_cross_controls(verifiers: list[dict]) -> dict:
    by_id = {r["id"]: r["payload"] for r in verifiers}

    base = by_id["KEYMASTER_BASE"]
    assert base["catalog"]["active_exact_operator_count"] == 12
    assert base["heuristic_injection_control"]["admitted"] is False
    assert base["heuristic_injection_control"]["reason"] == "REFUSE_NONEXACT_SELECTION_AUTHORITY"
    assert base["frontier_controls"]["frontier_explosion_input"] == 64
    assert base["frontier_controls"]["frontier_explosion_preserved"] == 64
    assert base["frontier_controls"]["silent_top_k_truncation"] is False

    swap = by_id["SWAP_ORBIT_C2C1"]
    assert swap["theorem_ledger"]["PAIR_SWAP_DISCOVERY_POLYNOMIAL"] is True
    assert swap["theorem_ledger"]["EXISTENTIAL_UPDATE_EXACT_AND_CLOSED"] is True
    assert swap["theorem_ledger"]["P_EQUALS_NP"] is False
    explosion = next(c for c in swap["controls"] if c["name"] == "ASYMMETRIC_ORBIT_EXPLOSION")
    assert explosion["result"] == "REFUSE_ORBIT_STATE_PRODUCT_EXCEEDS_N^4"

    ext = by_id["KEYMASTER_EXTENSION_K1"]
    assert ext["base_exact_operator_count"] == 12
    assert ext["extended_exact_operator_count"] == 14
    assert ext["heuristic_injection"]["admitted"] is False
    assert ext["heuristic_injection"]["reason"] == "REFUSE_NONEXACT_SELECTION_AUTHORITY"
    assert ext["composition_CNf_to_orbit_then_exists"]["admitted"] is True
    assert ext["orbit_self_composition"]["admitted"] is True

    return {
        "base_keymaster_exact_catalog": 12,
        "extended_keymaster_exact_catalog": 14,
        "heuristic_injection_refused_before_extension": True,
        "heuristic_injection_refused_after_extension": True,
        "frontier_explosion_64_preserved": True,
        "asymmetric_orbit_explosion_refused": True,
        "swap_orbit_closed_exists_composition": True,
    }


def main() -> None:
    manifest = load_manifest()
    rows, counts = collect_methods(manifest)
    separation = validate_separation(manifest, rows)
    verifier_results = run_exact_verifiers()
    cross = validate_cross_controls(verifier_results)

    payload = {
        "schema": "JANUS_PNP_EXACT_REVERSE_SPIRAL_UNIFIED_RESULT",
        "status": "PASS_EXACT_REVERSE_SPIRAL_INTEGRATION",
        "claim_ceiling": "P_VS_NP_OPEN",
        "anchor_commit": ANCHOR_COMMIT,
        "frozen_manifest_commit": FROZEN_MANIFEST_COMMIT,
        "frozen_manifest_blob_sha": FROZEN_MANIFEST_BLOB_SHA,
        "global_rule": manifest["global_rule"],
        "reverse_direction": manifest["direction"],
        "historical_method_rows": len(rows),
        "method_status_counts": dict(sorted(counts.items())),
        "unified_exact_catalog": list(EXPECTED_ACTIVE_CATALOG),
        "separation_controls": separation,
        "executed_exact_verifiers": [
            {
                "id": r["id"],
                "file": r["file"],
                "status": r["status"],
                "result_sha256": r["result_sha256"],
            }
            for r in verifier_results
        ],
        "cross_controls": cross,
        "active_universal_debt": manifest["active_universal_debt"],
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
        "next_gate": "U1-L2C2C2_EXACT_TRANSITION_EQUIVALENCE_BEYOND_LITERAL_SWAP_ORBITS_PLUS_GLOBAL_CANONICAL_STATE_BOUND",
    }
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    print("JANUS_EXACT_REVERSE_SPIRAL_UNIFIED = PASS")
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("JANUS_EXACT_REVERSE_SPIRAL_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
