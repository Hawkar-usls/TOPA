#!/usr/bin/env python3
"""Fail-closed prescore gate for TOPA sacred-text Flood calibration.

PASS means only that source identities/loci and imported JANUS canaries are structurally
frozen while SCORE remains locked. It is not permission to infer textual dependence,
historical events, or metaphysical claims.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research" / "sacred-scriptures"
FREEZE = BASE / "PRESCORE_SOURCE_FREEZE.v0.1.json"
BRIDGE = BASE / "ANCIENT_WRITING_METHOD_BRIDGE.v0.1.json"
BASELINE = BASE / "PHILOLOGY_BASELINE.v0.1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(msg: str) -> None:
    raise AssertionError(msg)


def main() -> int:
    missing = [p.name for p in (FREEZE, BRIDGE, BASELINE) if not p.exists()]
    if missing:
        print("TOPA_PRESCORE_GATE=FAIL")
        print("missing:", ", ".join(missing))
        return 1
    try:
        freeze = load(FREEZE)
        bridge = load(BRIDGE)
        baseline = load(BASELINE)

        if freeze.get("status") != "SOURCE_IDENTITIES_AND_LOCI_FROZEN__BYTE_HASHES_PENDING__SCORE_BLOCKED":
            fail("Unexpected prescore freeze status")
        if freeze.get("score_permission") is not False:
            fail("SCORE must remain locked in v0.1")

        sources = {s.get("id"): s for s in freeze.get("sources", [])}
        required_ids = {"F01_ATRAHASIS", "F02_GILGAMESH_XI", "F03_GENESIS_6_9", "F04_QURAN_NOAH", "F05_SATAPATHA_MANU"}
        if set(sources) != required_ids:
            fail(f"Prescore source set changed: {sorted(set(sources))}")

        if sources["F02_GILGAMESH_XI"].get("frozen_primary_narrative_locus") != "Tablet XI lines 8-203":
            fail("Gilgamesh XI locus drift")
        if sources["F03_GENESIS_6_9"].get("frozen_locus") != "Genesis 6:5-9:17":
            fail("Genesis locus drift")
        if "v1.8.1" not in sources["F03_GENESIS_6_9"].get("machine_baseline", "") or "2021" not in sources["F03_GENESIS_6_9"].get("machine_baseline", ""):
            fail("BHSA exact release/data version missing")
        if sources["F04_QURAN_NOAH"].get("frozen_primary_locus") != "Q 11:25-49":
            fail("Quran Noah locus drift")
        if sources["F05_SATAPATHA_MANU"].get("frozen_primary_locus") != "Śatapatha-Brāhmaṇa 1.8.1.[1]-[10]":
            fail("Satapatha flood locus drift")
        if sources["F05_SATAPATHA_MANU"].get("provenance_conflict", {}).get("state") != "OPEN_RECORDED_NO_SILENT_RESOLUTION":
            fail("GRETIL provenance conflict must stay explicit until resolved")

        required_canaries = {
            "LINEAR_A_REPRESENTATION_CANARY_PASS",
            "EGYPT_LEMMA_ID_CANARY_PASS",
            "EGYPT_TEXT_ID_CANARY_PASS",
        }
        bridge_required = set(bridge.get("prescore_gate", {}).get("required_before_flood_score", []))
        if not required_canaries.issubset(bridge_required):
            fail("Required Linear A / Egypt canaries missing")
        if bridge.get("prescore_gate", {}).get("failure_action") != "BLOCK_FLOOD_SCORE_AND_REPAIR_PIPELINE":
            fail("Canary failure must block score")

        if baseline.get("status") != "SOURCE_BASELINE_PARTIAL_FREEZE_WITH_GRETIL_PROVENANCE_CONFLICT":
            fail("Philology baseline status does not preserve provenance conflict")

        pending = [s["id"] for s in freeze["sources"] if str(s.get("hash_state", "")).startswith("PENDING")]
        if not pending:
            fail("v0.1 unexpectedly has no pending source hashes; use a new version to unlock SCORE")

    except (AssertionError, json.JSONDecodeError, OSError, KeyError) as exc:
        print("TOPA_PRESCORE_GATE=FAIL")
        print(type(exc).__name__ + ":", exc)
        return 1

    print("TOPA_PRESCORE_GATE=PASS_LOCKED")
    print("SCORE_PERMISSION=false")
    print("LINEAR_A_CANARY=REQUIRED_NOT_YET_EXECUTED")
    print("EGYPT_CANARIES=REQUIRED_NOT_YET_EXECUTED")
    print("SOURCE_HASHES=PENDING")
    print("PASS_SCOPE=FROZEN_IDENTITIES_LOCI_AND_FAIL_CLOSED_LOCK_ONLY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
