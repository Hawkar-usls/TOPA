#!/usr/bin/env python3
"""Executable prescore canaries for TOPA sacred-text research.

These fixtures test method behavior only. PASS gives permission to proceed to
blind-packet construction after source seals are present; it adds no evidence
for any historical, theological, or metaphysical claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CANARY_IDS = [
    "LINEAR_A_REPRESENTATION_CANARY_PASS",
    "LINEAR_A_SUPPORT_FLOOR_CANARY_PASS",
    "EGYPT_LEMMA_ID_CANARY_PASS",
    "EGYPT_TEXT_ID_CANARY_PASS",
]

def sha(obj) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def representation_canary():
    fixtures = [
        {"token": "*900", "type": "PUNCTUATION", "semantic_credit": 0},
        {"token": "10", "type": "NUMERIC_EXACT", "semantic_credit": 0},
        {"token": "≈¹⁄₄", "type": "NUMERIC_APPROX_OR_UNCERTAIN", "semantic_credit": 0},
        {"token": "SA·RA₂", "type": "SEMANTIC_CANDIDATE", "semantic_credit": 1},
    ]
    semantic = [x["token"] for x in fixtures if x["semantic_credit"] > 0]
    passed = semantic == ["SA·RA₂"] and all(
        x["semantic_credit"] == 0 for x in fixtures if x["type"] != "SEMANTIC_CANDIDATE"
    )
    return passed, {"fixtures": fixtures, "semantic_candidates": semantic}

def support_floor_canary():
    floor = 10
    cases = [
        {"signal": True, "support": 8, "expected_admit": False},
        {"signal": True, "support": 9, "expected_admit": False},
        {"signal": True, "support": 10, "expected_admit": True},
        {"signal": False, "support": 100, "expected_admit": False},
    ]
    for c in cases:
        c["observed_admit"] = bool(c["signal"] and c["support"] >= floor)
    passed = all(c["observed_admit"] == c["expected_admit"] for c in cases)
    return passed, {"frozen_support_floor": floor, "cases": cases, "historical_reference": "KU-RO G0 8/10 SUPPORT_BLOCKED"}

def lemma_id_canary():
    items = [
        {"form": "Sꜣḥ", "lemma_id": 127020, "class": "Orion constellation name"},
        {"form": "sꜣḫ", "lemma_id": 127110, "class": "verb: glorify/make excellent"},
        {"form": "sꜣḫ", "lemma_id": 127120, "class": "noun: spiritual/glorified state"},
    ]
    keys = [("TLA", x["lemma_id"]) for x in items]
    spelling_groups = {}
    for x in items:
        spelling_groups.setdefault(x["form"].casefold(), []).append(x["lemma_id"])
    passed = len(set(keys)) == 3 and set(spelling_groups["sꜣḫ"]) == {127110, 127120}
    return passed, {"items": items, "identity_keys": keys, "spelling_groups": spelling_groups}

def text_id_canary():
    refs = [
        {"label": "PT355", "utterance": 355, "sections": [572, 573, 574]},
        {"label": "PT366", "utterance": 366, "sections": list(range(626, 634))},
        {"label": "PT222", "utterance": 222, "section_start": 199},
        {"label": "PT477", "utterance": 477, "section_start": 956},
    ]
    typed = set()
    collision = False
    for r in refs:
        u = ("utterance", r["utterance"])
        if u in typed:
            collision = True
        typed.add(u)
        sec_values = r.get("sections", [r.get("section_start")])
        for s in sec_values:
            k = ("section", s)
            if k in typed:
                collision = True
            typed.add(k)
    adversarial = {("utterance", 355), ("section", 355)}
    passed = (not collision) and len(adversarial) == 2 and ("utterance", 355) != ("section", 355)
    return passed, {"references": refs, "adversarial_pair": [["utterance", 355], ["section", 355]], "typed_identity_count": len(typed)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="research/sacred-scriptures/CANARY_RUN.v0.1.json")
    args = ap.parse_args()
    tests = [
        (CANARY_IDS[0], representation_canary),
        (CANARY_IDS[1], support_floor_canary),
        (CANARY_IDS[2], lemma_id_canary),
        (CANARY_IDS[3], text_id_canary),
    ]
    results = []
    for cid, fn in tests:
        passed, evidence = fn()
        results.append({
            "id": cid,
            "status": "PASS" if passed else "FAIL",
            "fixture_sha256": sha(evidence),
            "evidence": evidence,
        })
    all_pass = all(x["status"] == "PASS" for x in results)
    out = {
        "schema": "topa.sacred_scriptures.canary_run.v0.1",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FOUR_OF_FOUR_PASS" if all_pass else "CANARY_FAILURE",
        "method_bridge": "ANCIENT_WRITING_METHOD_BRIDGE.v0.2.json",
        "results": results,
        "pass_count": sum(x["status"] == "PASS" for x in results),
        "required_pass_count": 4,
        "blind_packet_permission_from_canaries": all_pass,
        "score_permission": False,
        "epistemic_effect": "METHOD_PERMISSION_ONLY_NO_WORLD_TRUTH_CREDIT",
    }
    p = Path(args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"TOPA_CANARIES={'PASS' if all_pass else 'FAIL'}")
    for r in results:
        print(f"{r['id']}={r['status']}")
    print(f"CANARY_PASS_COUNT={out['pass_count']}/4")
    print(f"RECEIPT={p}")
    return 0 if all_pass else 2

if __name__ == "__main__":
    raise SystemExit(main())
