#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "research" / "propaganda-defense"

def load(name):
    with open(R / name, "r", encoding="utf-8") as f:
        return json.load(f)

errors = []
atlas = load("MANIPULATION_ATLAS_INDEX.v0.1.json")
schema = load("CROSS_EPOCH_OBSERVABLE_SCHEMA.v0.1.json")
freeze = load("ANCIENT_BASE_RATE_SOURCE_FREEZE.v0.2.json")
packet = load("BASE_RATE_CODING_PACKET_TEMPLATE.v0.1.json")
sprint = load("CURRENT_SPRINT.v0.3.json")

if atlas.get("technique_total") != 138:
    errors.append("atlas technique_total must remain 138 for v0.1")

ids = [d.get("id") for d in schema.get("dimensions", [])]
expected = [f"X{i:02d}" for i in range(1, 36)]
if ids != expected:
    errors.append("cross-epoch schema must contain ordered X01-X35 exactly once")

packet_ids = packet.get("feature_ids", [])
if packet_ids != expected:
    errors.append("packet template feature ids must exactly match X01-X35")
if packet.get("feature_cell_contract", {}).get("value", "NON_NULL") is not None:
    errors.append("packet template semantic value must be null")
if packet.get("current_state", {}).get("semantic_values_populated") != 0:
    errors.append("semantic values must remain zero before 8/8 source gate")
if packet.get("current_state", {}).get("issued_to_coders") is not False:
    errors.append("base-rate packet must not be issued yet")
if packet.get("current_state", {}).get("base_rate_coding_permission") is not False:
    errors.append("base-rate coding permission must remain false while BR05 is open")
if packet.get("current_state", {}).get("score_permission") is not False:
    errors.append("score permission must remain false")

summary = freeze.get("summary", {})
if summary.get("locus_roots_frozen_hash_pending") != 7:
    errors.append("v0.2 must preserve 7 frozen locus roots")
if summary.get("open_source_gate") != 1:
    errors.append("v0.2 must preserve exactly one open source gate")
if freeze.get("remaining_open", {}).get("id") != "BR05_HITTITE_TREATY":
    errors.append("BR05 Hittite treaty must remain the explicit open source gate")
if freeze.get("remaining_open", {}).get("policy") != "DO_NOT_DOWNGRADE_SOURCE_REQUIREMENT_TO_FORCE_8_OF_8":
    errors.append("anti-force source-quality rule missing")
if summary.get("semantic_X01_X35_cells_populated") != 0:
    errors.append("source freeze must report zero semantic cells")
if summary.get("score_permission") is not False:
    errors.append("source freeze score permission must remain false")

if sprint.get("current_first_unmet_requirement") != "BR05_MODERN_HITTITE_TREATY_SOURCE_AND_LOCUS_AUTHORITY":
    errors.append("current sprint must localize BR05 as first unmet requirement")
if sprint.get("entry_gates", {}).get("base_rate_coding_permission") is not False:
    errors.append("sprint must not authorize coding before BR05 closure")
if sprint.get("score_permission") is not False:
    errors.append("sprint score permission must remain false")

# Defensive and blindness invariants.
joined_locks = "\n".join(schema.get("hard_rules", []) + sprint.get("hard_locks", []))
for required in [
    "OBSERVABLE_FORM != MANIPULATIVE_INTENT",
    "NO_SACRED_TARGET_CODING_BEFORE_BASE_RATE_CONTROLS",
    "NO_FLOOD_A_B_CONTAMINATION",
    "NO_SCORE"
]:
    if required not in joined_locks:
        errors.append(f"missing invariant: {required}")

if errors:
    print("TOPA_BASE_RATE_PRESCORE_CHECK=FAIL")
    for e in errors:
        print(f"ERROR={e}")
    raise SystemExit(1)

print("TOPA_BASE_RATE_PRESCORE_CHECK=PASS")
print("ATLAS_TECHNIQUES=138")
print("CROSS_EPOCH_DIMENSIONS=35")
print("ANCIENT_SOURCE_ROOTS=7/8_FROZEN_BR05_OPEN")
print("SEMANTIC_VALUES_POPULATED=0")
print("BASE_RATE_CODING_PERMISSION=false")
print("SACRED_FLOOD_A_B_CONTAMINATION=BLOCKED")
print("SCORE_PERMISSION=false")
