#!/usr/bin/env python3
"""PF5 Component-Product v2.2 strict witness-glue replay.

Repairs CP-001 and CP-002 together.  The outer witness is constructed only
from the actual selected inner-lane witnesses stored in component records.
"""

from __future__ import annotations

from hashlib import sha256
import json
import sys
from typing import Dict, Sequence

import pf5_boundary_coverage_matrix_v0 as base
import pf5_component_product_representation_v2 as v2
import pf5_representation_escape_ladder_v1 as ladder


def selected_witness(component_record: Dict) -> Dict[int, bool]:
    selected = component_record.get("selected")
    if selected is None:
        raise AssertionError("component has no selected passing representation")
    witness = selected.get("witness")
    if witness is None:
        raise AssertionError("selected representation did not return a witness")
    return {int(k): bool(v) for k, v in witness.items()}


def strict_compose_witness(m: int, f: int, eq_record: Dict, fan_record: Dict) -> Dict[int, bool]:
    eq_w = selected_witness(eq_record)
    fan_w = selected_witness(fan_record)
    eq_map, fan_map = v2.global_maps(m, f)

    out: Dict[int, bool] = {}
    for local, val in eq_w.items():
        if local not in eq_map:
            raise AssertionError(f"EQ witness root outside manifest: {local}")
        global_id = eq_map[local]
        if global_id in out:
            raise AssertionError(f"duplicate global root {global_id}")
        out[global_id] = val

    for local, val in fan_w.items():
        if local not in fan_map:
            raise AssertionError(f"FAN witness root outside manifest: {local}")
        global_id = fan_map[local]
        if global_id in out:
            raise AssertionError(f"component overlap at global root {global_id}")
        out[global_id] = val

    expected = set(range(1, 2 * m + 2 * f + 1))
    if set(out) != expected:
        raise AssertionError(
            f"incomplete union missing={sorted(expected-set(out))} extra={sorted(set(out)-expected)}"
        )
    return out


def run_rung_strict(m: int, f: int = 6) -> Dict:
    old = v2.compose_witness
    try:
        v2.compose_witness = strict_compose_witness
        r = v2.run_rung(m, f)
    finally:
        v2.compose_witness = old

    w = strict_compose_witness(m, f, r["components"][0], r["components"][1])
    assert base.json_bytes(w) == r["outer_witness_bytes"]

    hc = ladder.make_hybrid_controls()[[8, 10, 12].index(m)]
    d, root = ladder.build_hybrid(hc)
    assert d.eval(root, w)

    r["witness_glue_source"] = "SELECTED_COMPONENT_WITNESSES_ONLY"
    r["witness_glue_complete_root_count"] = len(w)
    r["witness_glue_sha256"] = sha256(base.canon_json(w).encode()).hexdigest()
    r["selected_inner_witness_sha256"] = [
        sha256(base.canon_json(selected_witness(cr)).encode()).hexdigest()
        for cr in r["components"]
    ]
    return r


def main(argv: Sequence[str]) -> int:
    rungs = [run_rung_strict(m, 6) for m in (8, 10, 12)]
    result = {
        "artifact_id": "PF5-COMPONENT-PRODUCT-REPRESENTATION-V2.2",
        "repairs": [
            "PF5-CP-001-OUTER-WITNESS-BYPASS",
            "PF5-CP-002-STRICT-GLUE-ADAPTER-SHAPE",
        ],
        "claim_ceiling": "P_VS_NP = OPEN",
        "caps": base.CAPS,
        "lane_order": v2.LANE_ORDER,
        "rungs": rungs,
        "v1_escape_repaired_with_strict_inner_witness_glue": all(
            r["status"] == "PASS_EXACT_CLOSED"
            and r["witness_valid"] is True
            and r["witness_glue_source"] == "SELECTED_COMPONENT_WITNESSES_ONLY"
            for r in rungs
            if r["rung"] in ("HYBRID_EQ10_FAN6", "HYBRID_EQ12_FAN6")
        ),
        "universal_polynomial_coverage": "OPEN",
        "next_front": "CONNECTED_BOUNDARY_ADHESION_GATE",
        "p_vs_np": "OPEN",
    }
    result["result_sha256"] = sha256(base.canon_json(result).encode()).hexdigest()

    for r in rungs:
        print(
            r["rung"],
            "status=", r["status"],
            "source=", r["witness_glue_source"],
            "roots=", r["witness_glue_complete_root_count"],
            "outer_witness_sha=", r["witness_glue_sha256"],
        )
    print(
        "PF5_CP_STRICT_COMPONENT_WITNESS_GLUE =",
        result["v1_escape_repaired_with_strict_inner_witness_glue"],
    )
    print("NEXT_FRONT = CONNECTED_BOUNDARY_ADHESION_GATE")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])

    if "--json-out" in argv:
        i = list(argv).index("--json-out")
        with open(argv[i + 1], "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
