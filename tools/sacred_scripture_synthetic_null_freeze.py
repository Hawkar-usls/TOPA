#!/usr/bin/env python3
"""Freeze reproducible synthetic-null generator commitments without scoring.

C09/C10 are generator specifications at this phase. Actual shuffled matrices are
forbidden until the double-coded feature matrix is frozen. Seeds are derived
only from immutable method/source commitments, never from observed scores.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

GENERATOR_VERSION = "topa-sacred-scriptures-nullgen-v0.1"
NULL_IDS = ("C09", "C10")


def h(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def commitment(null_id: str, schema_sha: str, prescore_sha: str, generator_sha: str) -> str:
    payload = "\0".join([
        "TOPA-SYNTHETIC-NULL-SEED-COMMITMENT-V1",
        null_id,
        schema_sha,
        prescore_sha,
        generator_sha,
    ]).encode("utf-8")
    return h(payload)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind-test", default="research/sacred-scriptures/FLOOD_STEMMA_BLIND_TEST.v0.1.json")
    ap.add_argument("--prescore", default="research/sacred-scriptures/execution/PRESCORE_SUCCESS_RECEIPT.v0.1.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    script_path = Path(__file__)
    generator_sha = h(script_path.read_bytes())
    blind_raw = Path(args.blind_test).read_bytes()
    blind = json.loads(blind_raw.decode("utf-8"))
    features = blind.get("frozen_feature_schema")
    if not isinstance(features, list) or len(features) < 10 or len(features) != len(set(features)):
        raise SystemExit("invalid or duplicate frozen feature schema")
    schema_sha = h(canon(features))

    prescore_raw = Path(args.prescore).read_bytes()
    prescore = json.loads(prescore_raw.decode("utf-8"))
    if prescore.get("status") != "PRESCORE_GATE_SATISFIED" or prescore.get("gate", {}).get("score_permission") is not False:
        raise SystemExit("prescore authority receipt not in expected score-locked state")
    prescore_sha = h(prescore_raw)

    nulls = [
        {
            "slot": "C09",
            "independent_control_id": "C09_WITHIN_PACKET_FEATURE_SHUFFLE",
            "control_class": "FEATURE_SHUFFLED_SYNTHETIC_NULL",
            "generator_version": GENERATOR_VERSION,
            "generator_sha256": generator_sha,
            "seed_commitment": commitment("C09", schema_sha, prescore_sha, generator_sha),
            "input_schema_sha256": schema_sha,
            "input_matrix_state": "BLOCKED_UNTIL_DOUBLE_CODED_MATRIX_FREEZE",
            "shuffle_constraints": [
                "Operate only on scorer-visible feature values after opaque packet IDs are assigned",
                "Never ingest source identity, tradition, language, chronology, geography, control class or contact graph",
                "Preserve PRESENT/ABSENT/UNKNOWN/NOT_APPLICABLE value vocabulary exactly",
                "Preserve each packet's count of UNKNOWN and NOT_APPLICABLE values",
                "Shuffle eligible PRESENT/ABSENT assignments only among type-compatible non-missing feature positions within each packet",
                "Use deterministic Fisher-Yates driven by the committed seed derivation after matrix freeze",
                "Emit a full permutation receipt and reject a no-op shuffle"
            ],
            "leakage_check": "Generator input schema explicitly rejects all scorer-forbidden metadata keys before permutation.",
            "output_state": "NOT_GENERATED_BEFORE_DOUBLE_CODING",
            "status": "GENERATOR_AND_SEED_COMMITMENT_FROZEN"
        },
        {
            "slot": "C10",
            "independent_control_id": "C10_ACROSS_PACKET_FEATURE_SHUFFLE",
            "control_class": "FEATURE_SHUFFLED_SYNTHETIC_NULL",
            "generator_version": GENERATOR_VERSION,
            "generator_sha256": generator_sha,
            "seed_commitment": commitment("C10", schema_sha, prescore_sha, generator_sha),
            "input_schema_sha256": schema_sha,
            "input_matrix_state": "BLOCKED_UNTIL_DOUBLE_CODED_MATRIX_FREEZE",
            "shuffle_constraints": [
                "Operate only on scorer-visible feature values after opaque packet IDs are assigned",
                "Never ingest source identity, tradition, language, chronology, geography, control class or contact graph",
                "For each feature independently, permute eligible values across opaque packets",
                "Preserve each feature's marginal PRESENT/ABSENT counts and preserve UNKNOWN/NOT_APPLICABLE positions",
                "Use deterministic Fisher-Yates driven by the committed seed derivation after matrix freeze",
                "Emit a full permutation receipt and reject a no-op global permutation"
            ],
            "leakage_check": "Cross-packet permutation is feature-column local and cannot access hidden source-family labels.",
            "output_state": "NOT_GENERATED_BEFORE_DOUBLE_CODING",
            "status": "GENERATOR_AND_SEED_COMMITMENT_FROZEN"
        }
    ]

    out = {
        "schema": "topa.sacred_scriptures.synthetic_null_freeze.v0.1",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "TWO_OF_TWO_SYNTHETIC_NULL_GENERATORS_FROZEN",
        "generator_version": GENERATOR_VERSION,
        "generator_sha256": generator_sha,
        "blind_test_sha256": h(blind_raw),
        "input_schema_sha256": schema_sha,
        "feature_count": len(features),
        "prescore_success_receipt_sha256": prescore_sha,
        "nulls": nulls,
        "frozen_count": 2,
        "required_count": 2,
        "actual_null_outputs_exist": False,
        "double_coding_permission_from_null_freeze": True,
        "score_permission": False,
        "anti_peeking_rule": "Actual shuffled matrices are generated only after the double-coded, arbitrated scorer matrix is frozen. Generator identity, constraints and seed commitments are frozen now so null behavior cannot be tuned to results.",
        "epistemic_effect": "NULL_METHOD_COMMITMENT_ONLY_NO_SCORE_NO_RESULT_CREDIT"
    }
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("TOPA_SYNTHETIC_NULL_FREEZE=PASS")
    print("SYNTHETIC_NULL_SLOTS=2/2")
    print(f"FEATURE_SCHEMA_SHA256={schema_sha}")
    print(f"GENERATOR_SHA256={generator_sha}")
    print(f"RECEIPT={p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
