#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research" / "propaganda-defense"


def load(name: str):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def require(cond: bool, msg: str):
    if not cond:
        raise SystemExit(f"TOPA_PROPAGANDA_DEFENSE_CHECK=FAIL: {msg}")


def main() -> int:
    corpus = load("CORPUS_MANIFEST.v0.1.json")
    manual = load("DEFENSIVE_MANUAL.v0.1.json")
    protocol = load("JANUS_PROTOCOL.v0.1.json")
    receipts = load("SOURCE_DISCOVERY_RECEIPTS.v0.1.json")
    authority = load("SOURCE_AUTHORITY_AND_BIAS_MATRIX.v0.1.json")
    progress = load("PROJECT_PROGRESS_LOG.v0.1.json")

    require(corpus.get("coverage_claim") == "NOT_EXHAUSTIVE", "coverage must remain explicitly non-exhaustive")
    sources = corpus.get("sources", [])
    require(len(sources) >= 36, "seed corpus unexpectedly shrank below 36 records")
    required_classes = {
        "FOUNDATIONAL_THEORY",
        "MILITARY_AND_STRATCOM",
        "FIMI_AND_INFLUENCE_OPS",
        "MISINFORMATION_SCIENCE",
        "MEDIA_LITERACY_AND_VERIFICATION",
        "UKRAINE_DEFENSIVE_PRACTICE",
    }
    observed = {s.get("cluster") for s in sources}
    require(required_classes <= observed, f"missing source class: {sorted(required_classes-observed)}")
    ids = [s.get("id") for s in sources]
    require(len(ids) == len(set(ids)), "duplicate source IDs")
    for s in sources:
        require(s.get("rights"), f"missing rights state for {s.get('id')}")
        require(s.get("use"), f"missing defensive-use state for {s.get('id')}")

    firewall = set(corpus.get("hard_firewall", []))
    for law in {
        "DESCRIPTION_OF_INFLUENCE_TECHNIQUE != AUTHORIZATION_TO_USE_IT",
        "RED_TEAM_TTP != EXECUTION_PLAYBOOK",
        "NO_REAL_AUDIENCE_TARGETING_OR_MICROTARGETING",
        "NO_COVERT_ATTRIBUTION_OR_DECEPTIVE_CAMPAIGN_DESIGN",
    }:
        require(law in firewall, f"missing corpus firewall law: {law}")

    require(manual.get("score_permission") is False, "manual score permission must remain false")
    red = manual.get("red_team_firewall", {})
    require(len(red.get("not_allowed", [])) >= 5, "red-team firewall weakened")
    require("create deployable propaganda messages" in red.get("not_allowed", []), "deployable propaganda generation must remain blocked")

    laws = set(protocol.get("laws", []))
    for law in {
        "PROPAGANDA_LABEL != CLAIM_FALSEHOOD",
        "CLAIM_FALSEHOOD != PROPAGANDA_INTENT",
        "PROPAGANDA_CAN_USE_TRUE_INFORMATION",
        "REACH != PERSUASION",
        "MODEL_OUTPUT != ATTRIBUTION",
        "COUNTER_PROPAGANDA_CAN_ITSELF_BECOME_PROPAGANDA",
    }:
        require(law in laws, f"missing epistemic law: {law}")
    require(protocol.get("score_permission") is False, "protocol score permission must remain false")

    require(receipts.get("status") == "WEB_VERIFIED_SEED_RECEIPTS", "source receipt status changed unexpectedly")
    require(len(receipts.get("verified", [])) >= 14, "verified source receipt set shrank")

    require(authority.get("core_law") == "THE_SAME_ANALYTIC_STANDARD_APPLIES_REGARDLESS_OF_ACTOR_ALIGNMENT_OR_SOURCE_PRESTIGE", "symmetry rule missing")
    afw = set(authority.get("firewall", []))
    require("OFFICIAL_SOURCE != EXCLUSIVE_TRUTH" in afw, "official-source ceiling missing")
    require("OPPOSITION_SOURCE != AUTOMATIC_FALSEHOOD" in afw, "opposition-source symmetry missing")
    require("SYMMETRY_IS_A_TEST_NOT_FALSE_EQUIVALENCE" in afw, "false-equivalence guard missing")

    policy = progress.get("policy", {})
    require(policy.get("append_only_semantics") is True, "progress log must remain append-only")
    require(policy.get("negative_results_preserved") is True, "negative result preservation missing")
    require(progress.get("current_snapshot", {}).get("score_permission") is False, "project score permission must remain false")
    sacred = [e for e in progress.get("entries", []) if e.get("event") == "SACRED_TEXT_PARALLEL_GATE_PRESERVED"]
    require(sacred and sacred[-1].get("status") == "UNCHANGED_EXTERNAL_LANE", "sacred-text independent-coder gate must remain unchanged")

    print("TOPA_PROPAGANDA_DEFENSE_CHECK=PASS")
    print(f"SEED_SOURCES={len(sources)}")
    print(f"SOURCE_CLASSES={len(observed)}")
    print(f"WEB_VERIFIED_RECEIPTS={len(receipts.get('verified', []))}")
    print("OPERATIONAL_FIREWALL=PASS")
    print("SOURCE_SYMMETRY_GATE=PASS")
    print("SACRED_TEXT_A_B_GATE=UNCHANGED")
    print("SCORE_PERMISSION=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
