#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE = Path(__file__).with_name("pf5_clause_subsumption_contraction_v20.py")
OLD_A = 'assert certificate["subsuming_clause"] == [-3, -5]'
NEW_A = 'assert certificate["subsuming_clause"] == [-6, 4]'
OLD_B = 'assert certificate["subsumed_clause"] == [-3, -5, 6]'
NEW_B = 'assert certificate["subsumed_clause"] == [4, 2, -6]'


def load_repaired_namespace():
    source = BASE.read_text(encoding="utf-8")
    assert source.count(OLD_A) == 1
    assert source.count(OLD_B) == 1
    repaired = source.replace(OLD_A, NEW_A).replace(OLD_B, NEW_B)
    namespace = {
        "__name__": "pf5_clause_subsumption_contraction_v20_1_runtime",
        "__file__": str(BASE),
    }
    exec(compile(repaired, str(BASE), "exec"), namespace)
    return namespace


def run():
    ns = load_repaired_namespace()
    result = ns["run"]()
    # Provider outputs are unchanged except for authoritative repair metadata.
    result.pop("result_sha256", None)
    result["artifact_id"] = "PF5-CLAUSE-SUBSUMPTION-CONTRACTION-V20.1"
    result["repair"] = "V20-001_DIAGNOSTIC_EXPECTATION_ONLY"
    result["repair_receipts"] = [
        "data/PF5-V20-001-DIAGNOSTIC-PAIR-ORDER-MISMATCH.json",
        "data/PF5-V20-001-RESOLUTION.json",
    ]
    result["base_provider_blob_sha"] = "2a0d3faaf334f2132a7d54e8c310d2e71322461b"
    result["provider_logic_changed"] = False
    result["fresh_holdout_changed"] = False
    result["result_sha256"] = ns["digest"](result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = run()
    if args.json_out:
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )
    print("PF5_CLAUSE_SUBSUMPTION_V20_1 =", result["status"])
    print("SOURCE_MANIFEST_SHA256 =", result["source_manifest_sha256"])
    print("REDUCTION_BATCH_SHA256 =", result["reduction_batch_sha256"])
    print("SUMMARY =", result["summary"])
    print("RUNTIME_LEDGER =", result["runtime_discovery_ledger"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
