#!/usr/bin/env python3
"""Fail-closed validator for TOPA sacred-scripture research artifacts.

This validates corpus structure and epistemic/rights guardrails only.
A PASS does not establish the truth, antiquity, authorship, canon status,
or metaphysical claims of any text.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research" / "sacred-scriptures"
MANIFEST = BASE / "CORPUS_MANIFEST.v0.1.json"
PROTOCOL = BASE / "JANUS_COUNCIL_PROTOCOL.v0.1.json"
FIRST_PASS = BASE / "TOPA_FIRST_PASS.v0.1.json"
LINEAGE = BASE / "JANUS_EXISTING_LINEAGE.v0.1.json"
RESIDUAL_PROTOCOL = BASE / "INDEPENDENT_RESIDUAL_PROTOCOL.v0.1.json"
FLOOD_TEST = BASE / "FLOOD_STEMMA_BLIND_TEST.v0.1.json"
SOURCE_RECEIPTS = BASE / "SOURCE_DISCOVERY_RECEIPTS.v0.1.json"

ALLOWED_CLASSES = {
    "PRIMARY_CANON",
    "SECONDARY_SACRED",
    "CONTESTED_CANON",
    "HISTORICAL_RELIGIOUS_TEXT",
    "ORAL_COMMUNITY_CONTROLLED",
}

REQUIRED_LAWS = {
    "TEXT_EXISTS != EVENT_TRUTH",
    "CANONICAL_STATUS != EMPIRICAL_TRUTH",
    "SHARED_MOTIF != SHARED_SOURCE",
    "MODEL_CONSENSUS != INDEPENDENT_CONFIRMATION",
}

REQUIRED_RESIDUAL_LAWS = {
    "TEXTUAL_SIMILARITY != INDEPENDENT_DISCOVERY",
    "INDEPENDENT_DISCOVERY != SUPERNATURAL_CAUSE",
    "RESIDUAL != REVELATION",
    "MODEL_CONSENSUS != INDEPENDENT_CONFIRMATION",
    "UNKNOWN = VALID_RESULT",
}

FORBIDDEN_METAPHYSICAL_PROMOTIONS = {
    "SUPERNATURAL_PROVEN",
    "REVELATION_PROVEN",
    "ONE_RELIGION_TRUE",
    "PROPHECY_PROVEN",
    "ANCIENT_GLOBAL_NETWORK_PROVEN",
}


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def fail(message: str) -> None:
    raise AssertionError(message)


def validate_manifest(data: dict) -> None:
    if data.get("coverage_claim") != "NOT_EXHAUSTIVE":
        fail("Corpus must not claim exhaustive coverage.")

    laws = set(data.get("laws", []))
    missing_laws = REQUIRED_LAWS - laws
    if missing_laws:
        fail(f"Missing epistemic laws: {sorted(missing_laws)}")

    traditions = data.get("traditions")
    if not isinstance(traditions, list) or not traditions:
        fail("traditions must be a non-empty list")

    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    oral_count = 0

    for tradition in traditions:
        tid = tradition.get("id")
        if not isinstance(tid, str) or not tid:
            fail("Every tradition requires a non-empty id")
        if tid in seen_ids:
            fail(f"Duplicate tradition id: {tid}")
        seen_ids.add(tid)

        if not tradition.get("label"):
            fail(f"Tradition {tid} lacks label")
        if not tradition.get("source_status"):
            fail(f"Tradition {tid} lacks source_status")

        works = tradition.get("works")
        if not isinstance(works, list) or not works:
            fail(f"Tradition {tid} has no works")

        for work in works:
            if not isinstance(work, list) or len(work) != 2:
                fail(f"Work entry in {tid} must be [title, class]")
            title, klass = work
            if not isinstance(title, str) or not title:
                fail(f"Invalid work title in {tid}")
            if klass not in ALLOWED_CLASSES:
                fail(f"Invalid class {klass!r} for {tid}/{title}")
            pair = (tid, title.casefold())
            if pair in seen_pairs:
                fail(f"Duplicate work inside tradition: {tid}/{title}")
            seen_pairs.add(pair)
            if klass == "ORAL_COMMUNITY_CONTROLLED":
                oral_count += 1

    if oral_count == 0:
        fail("At least one oral/community-controlled corpus must exercise the permission gate")

    roots = data.get("verified_source_roots", [])
    for root in roots:
        if not root.get("url", "").startswith("https://"):
            fail(f"Verified source root must use HTTPS: {root}")
        if not root.get("ingest_rule"):
            fail(f"Verified source root lacks ingest_rule: {root.get('name')}")


def validate_protocol(data: dict) -> None:
    boundary = data.get("constitutional_boundary", {})
    if boundary.get("model_output_is_evidence") is not False:
        fail("model_output_is_evidence must be false")
    if boundary.get("agent_count_is_source_count") is not False:
        fail("agent_count_is_source_count must be false")
    if boundary.get("consensus_is_truth") is not False:
        fail("consensus_is_truth must be false")

    nodes = data.get("nodes", [])
    names = {n.get("node") for n in nodes}
    required = {
        "TOPA",
        "HRain",
        "iNaiHR",
        "Demi_Head",
        "Janus_Genesis",
        "Janus-Fundamentum",
        "Fast-CAT-SHAiTan",
        "AIFC",
        "Janus-Cosmos",
        "janus-distributed-ai-swarm",
        "janus-meta-registry",
    }
    missing = required - names
    if missing:
        fail(f"Missing required JANUS review nodes: {sorted(missing)}")

    stages = [s.get("stage") for s in data.get("pipeline", [])]
    if len(stages) != len(set(stages)):
        fail("Duplicate pipeline stage id")
    if "S5_ATTACK" not in stages or "S6_BLIND_CONTROL" not in stages:
        fail("Adversarial and blind-control stages are mandatory")

    forbidden = set(data.get("forbidden_shortcuts", []))
    if "USING_MODEL_AGREEMENT_AS_REPLICATION" not in forbidden:
        fail("Model-agreement anti-pseudoreplication rule is mandatory")


def validate_first_pass(data: dict) -> None:
    if data.get("runtime_claim") is None:
        fail("First pass must state its runtime claim")
    if data.get("topa_state") not in {"PASS_WITH_OPEN_GATES", "HOLD", "FAIL"}:
        fail("Invalid TOPA state")

    killer = data.get("best_next_killer_test", {})
    for key in ("question", "success_condition", "failure_condition"):
        if not killer.get(key):
            fail(f"Killer test missing {key}")

    if killer.get("world_truth_effect") != "NONE; even a successful textual stemma would establish textual/historical relationships, not supernatural causation.":
        fail("Killer test must preserve metaphysical boundary")


def validate_lineage(data: dict) -> None:
    if data.get("status") != "DISCOVERED_UPSTREAM_LINEAGE":
        fail("Lineage status changed unexpectedly")
    if not data.get("discovered_artifacts"):
        fail("Lineage must contain discovered upstream artifacts")


def validate_residual_protocol(data: dict) -> None:
    if data.get("status") != "FROZEN_METHOD_V0_1":
        fail("Independent residual protocol must remain frozen for v0.1")

    laws = set(data.get("core_laws", []))
    missing = REQUIRED_RESIDUAL_LAWS - laws
    if missing:
        fail(f"Residual protocol missing laws: {sorted(missing)}")

    stages = [s.get("stage") for s in data.get("subtraction_pipeline", [])]
    required_stages = {
        "R0_SOURCE_ROOT_COLLAPSE",
        "R1_TRANSLATION_AND_SEMANTIC_CONTROL",
        "R2_HISTORICAL_CONTACT_GRAPH",
        "R3_EXPECTED_CONVERGENCE_NULL",
        "R4_BLIND_RARE_BUNDLE_TEST",
        "R5_ADVERSARIAL_REATTACK",
    }
    if not required_stages.issubset(set(stages)):
        fail("Residual subtraction pipeline is incomplete")

    if any(s.get("fail_closed") is not True for s in data.get("subtraction_pipeline", [])):
        fail("Every residual subtraction stage must fail closed")

    ceiling = data.get("promotion_ceiling", {})
    if ceiling.get("from_texts_alone") != "UNRESOLVED_INDEPENDENT_RESIDUAL":
        fail("Texts-alone promotion ceiling was weakened")
    forbidden = set(ceiling.get("forbidden_promotions", []))
    if not FORBIDDEN_METAPHYSICAL_PROMOTIONS.issubset(forbidden):
        fail("Required metaphysical promotion prohibitions are missing")


def validate_flood_test(data: dict) -> None:
    if data.get("status") != "PREREGISTERED_NOT_YET_SCORED":
        fail("Flood test v0.1 must remain preregistered and unscored until execution")
    if data.get("parent_protocol") != "INDEPENDENT_RESIDUAL_PROTOCOL.v0.1.json":
        fail("Flood test must bind to the frozen residual protocol")

    features = data.get("frozen_feature_schema", [])
    if len(features) < 20 or len(features) != len(set(features)):
        fail("Flood feature schema must be sufficiently broad and non-duplicated")

    controls = set(data.get("control_design", {}).get("minimum_groups", []))
    required_controls = {
        "non-flood catastrophe narratives matched for genre",
        "feature-shuffled synthetic controls",
    }
    if not required_controls.issubset(controls):
        fail("Flood test lacks mandatory negative controls")

    if data.get("residual_interpretation") != "UNRESOLVED_INDEPENDENT_RESIDUAL only. It is a target for another spiral, not evidence of revelation or supernatural causation.":
        fail("Flood residual interpretation boundary changed")


def validate_source_receipts(data: dict) -> None:
    if data.get("status") != "PARTIAL_VERIFIED_SOURCE_MAP":
        fail("Source map must remain partial, not exhaustive")
    if data.get("rule") != "SOURCE_VERIFIED != MIRROR_RIGHTS_VERIFIED":
        fail("Source verification / reuse-rights separation is mandatory")
    receipts = data.get("receipts", [])
    if not receipts:
        fail("Source receipts cannot be empty")
    for receipt in receipts:
        if not receipt.get("url", "").startswith("https://"):
            fail("Every source receipt requires HTTPS URL")
        if not receipt.get("reuse_state"):
            fail("Every source receipt requires reuse_state")


def main() -> int:
    required_paths = [
        MANIFEST,
        PROTOCOL,
        FIRST_PASS,
        LINEAGE,
        RESIDUAL_PROTOCOL,
        FLOOD_TEST,
        SOURCE_RECEIPTS,
    ]
    missing = [str(p.relative_to(ROOT)) for p in required_paths if not p.exists()]
    if missing:
        print("TOPA_SACRED_SCRIPTURES_CHECK=FAIL")
        print("missing:", ", ".join(missing))
        return 1

    try:
        manifest = load(MANIFEST)
        protocol = load(PROTOCOL)
        first_pass = load(FIRST_PASS)
        lineage = load(LINEAGE)
        residual = load(RESIDUAL_PROTOCOL)
        flood = load(FLOOD_TEST)
        receipts = load(SOURCE_RECEIPTS)
        validate_manifest(manifest)
        validate_protocol(protocol)
        validate_first_pass(first_pass)
        validate_lineage(lineage)
        validate_residual_protocol(residual)
        validate_flood_test(flood)
        validate_source_receipts(receipts)
    except (json.JSONDecodeError, AssertionError, OSError) as exc:
        print("TOPA_SACRED_SCRIPTURES_CHECK=FAIL")
        print(type(exc).__name__ + ":", exc)
        return 1

    tradition_count = len(manifest["traditions"])
    work_count = sum(len(t["works"]) for t in manifest["traditions"])
    node_count = len(protocol["nodes"])
    motif_count = len(first_pass.get("motif_families_for_content_pass", []))
    residual_stage_count = len(residual.get("subtraction_pipeline", []))
    flood_feature_count = len(flood.get("frozen_feature_schema", []))
    receipt_count = len(receipts.get("receipts", []))

    print("TOPA_SACRED_SCRIPTURES_CHECK=PASS")
    print(f"TRADITIONS={tradition_count}")
    print(f"WORK_ENTRIES={work_count}")
    print(f"JANUS_NODES={node_count}")
    print(f"MOTIF_FAMILIES={motif_count}")
    print(f"RESIDUAL_SUBTRACTION_STAGES={residual_stage_count}")
    print(f"FLOOD_FROZEN_FEATURES={flood_feature_count}")
    print(f"SOURCE_RECEIPTS={receipt_count}")
    print("PASS_SCOPE=STRUCTURE_RIGHTS_AND_EPISTEMIC_GUARDRAILS_ONLY")
    return 0


if __name__ == "__main__":
    sys.exit(main())
