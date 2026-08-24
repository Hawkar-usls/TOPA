#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research" / "sacred-scriptures"
FILES = {
    "independence": BASE / "CODER_INDEPENDENCE_CONTRACT.v0.1.json",
    "arbitration": BASE / "ARBITRATION_PROTOCOL.v0.1.json",
    "packet_template": BASE / "SOURCE_CODING_PACKET_TEMPLATE.v0.1.json",
    "null_freeze": BASE / "execution" / "SYNTHETIC_NULL_FREEZE.v0.1.json",
}

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    out = BASE / "execution" / "PRE_CODER_CONTRACT_FREEZE_GATE.v0.1.json"
    errors = []
    data = {}
    for name, path in FILES.items():
        if not path.exists():
            errors.append(f"missing:{name}:{path}")
            continue
        try:
            data[name] = load(path)
        except Exception as e:
            errors.append(f"unreadable:{name}:{type(e).__name__}:{e}")
    if not errors:
        if data["independence"].get("status") != "FROZEN_BEFORE_ANY_SEMANTIC_CODING":
            errors.append("independence_status")
        if data["arbitration"].get("status") != "FROZEN_BEFORE_ANY_A_B_CODING_OUTPUT":
            errors.append("arbitration_status")
        if data["packet_template"].get("status") != "FROZEN_TEMPLATE_NO_SEMANTIC_VALUES":
            errors.append("packet_template_status")
        for key in ("independence", "arbitration", "packet_template"):
            if data[key].get("score_permission") is not False:
                errors.append(f"score_permission_must_remain_false:{key}")
        if data["packet_template"].get("template_contains_feature_values") is not False:
            errors.append("packet_template_contains_feature_values")
        if data["packet_template"].get("template_contains_expected_answers") is not False:
            errors.append("packet_template_contains_expected_answers")
        expected_feature_hash = data["null_freeze"].get("input_schema_sha256")
        packet_feature_hash = data["packet_template"].get("feature_authority", {}).get("feature_schema_sha256")
        if not expected_feature_hash or packet_feature_hash != expected_feature_hash:
            errors.append("feature_schema_hash_mismatch")
    coding_root = BASE / "coding"
    preexisting_semantic_receipts = []
    if coding_root.exists():
        for p in coding_root.rglob("*.json"):
            try:
                j = load(p)
            except Exception:
                continue
            if j.get("schema", "").startswith("topa.sacred_scriptures.coder_receipt") or j.get("semantic_feature_values_present") is True:
                preexisting_semantic_receipts.append(str(p.relative_to(ROOT)))
    if preexisting_semantic_receipts:
        errors.append("semantic_coding_receipt_predates_gate")
    ok = not errors
    receipt = {
        "schema": "topa.sacred_scriptures.pre_coder_contract_freeze_gate.v0.1",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PRE_CODER_CONTRACTS_FROZEN_ORIGIN_PRIME_READY" if ok else "PRE_CODER_CONTRACT_GATE_BLOCKED",
        "spiral_authority": "DOUBLE_CODING_REVERSE_SPIRAL.v0.1.json",
        "contract_sha256": {
            k: sha256(v) for k, v in FILES.items() if v.exists()
        },
        "preexisting_semantic_coding_receipts": preexisting_semantic_receipts,
        "semantic_coding_permission": ok,
        "genuine_independence_still_required_at_execution": True,
        "same_reasoning_instance_may_count_as_two_coders": False,
        "arbitration_rules_frozen_before_outputs": bool(not errors and data["arbitration"].get("status") == "FROZEN_BEFORE_ANY_A_B_CODING_OUTPUT"),
        "packet_template_contains_feature_values": None if "packet_template" not in data else data["packet_template"].get("template_contains_feature_values"),
        "score_permission": False,
        "errors": errors,
        "epistemic_effect": "PRE_CODER_METHOD_PERMISSION_ONLY_NO_SEMANTIC_RESULT_NO_SCORE"
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
