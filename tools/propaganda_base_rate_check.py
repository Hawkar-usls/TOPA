#!/usr/bin/env python3
import hashlib
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
freeze = load("ANCIENT_BASE_RATE_SOURCE_FREEZE.v0.3.json")
packet_path = R / "BASE_RATE_CODING_PACKET_TEMPLATE.v0.2.json"
packet = load("BASE_RATE_CODING_PACKET_TEMPLATE.v0.2.json")
sprint = load("CURRENT_SPRINT.v0.4.json")

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
state = packet.get("current_state", {})
if state.get("semantic_values_populated") != 0:
    errors.append("semantic values must remain zero")
if state.get("issued_to_coders") is not False:
    errors.append("base-rate packet must not be issued yet")
if state.get("source_authorities") != "8/8 FROZEN":
    errors.append("packet must bind 8/8 frozen source authorities")
if state.get("exact_sub_locus_commitments") != "INCOMPLETE":
    errors.append("exact sub-locus commitments must remain explicitly incomplete at this state")
if state.get("base_rate_coding_permission") is not False:
    errors.append("base-rate coding permission must remain false until commitment gate")
if state.get("score_permission") is not False:
    errors.append("score permission must remain false")

packet_sha256 = hashlib.sha256(packet_path.read_bytes()).hexdigest()
expected_packet_sha256 = "da80734a96ea26bce3111b3deb7a4ebc5c78334199c9b4ff095e395525319155"
if packet_sha256 != expected_packet_sha256:
    errors.append(f"published zero-value packet SHA-256 drift: {packet_sha256}")

summary = freeze.get("summary", {})
if summary.get("source_locus_authorities_frozen") != 8:
    errors.append("v0.3 must preserve 8/8 source-locus authorities")
if summary.get("required") != 8:
    errors.append("v0.3 required count must remain 8")
if summary.get("source_or_metadata_commitments_complete") is not False:
    errors.append("source/metadata commitments must remain incomplete at this state")
if summary.get("semantic_X01_X35_cells_populated") != 0:
    errors.append("source freeze must report zero semantic cells")
if summary.get("base_rate_coding_permission") is not False:
    errors.append("source freeze must not authorize coding yet")
if summary.get("score_permission") is not False:
    errors.append("source freeze score permission must remain false")

br05 = freeze.get("BR05_HITTITE_TREATY", {})
if br05.get("status") != "LOCUS_AUTHORITY_FROZEN_HASH_COMMITMENT_PENDING":
    errors.append("BR05 must be source-authority frozen but hash commitment pending")
if br05.get("primary_base_rate_locus") != "CTH 62.II A column I lines 19′–28′":
    errors.append("BR05 exact primary locus drift")
if "not multiple independent political events" not in br05.get("anti_pseudoreplication_rule", ""):
    errors.append("BR05 anti-pseudoreplication rule missing")

if sprint.get("current_first_unmet_requirement") != "BR01_BR08_EXACT_SUB_LOCUS_AND_SOURCE_OR_METADATA_COMMITMENTS":
    errors.append("current sprint must localize exact sub-locus/source commitment gate")
if sprint.get("entry_gates", {}).get("base_rate_coding_permission") is not False:
    errors.append("sprint must not authorize coding before commitment gate")
if sprint.get("score_permission") is not False:
    errors.append("sprint score permission must remain false")

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
print("ANCIENT_SOURCE_AUTHORITIES=8/8_FROZEN")
print(f"ZERO_VALUE_PACKET_SHA256={packet_sha256}")
print("EXACT_SUB_LOCUS_COMMITMENTS=INCOMPLETE")
print("SEMANTIC_VALUES_POPULATED=0")
print("BASE_RATE_CODING_PERMISSION=false")
print("SACRED_FLOOD_A_B_CONTAMINATION=BLOCKED")
print("SCORE_PERMISSION=false")
