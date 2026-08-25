#!/usr/bin/env python3
"""PF5 Component-Product v2.1 witness-glue repair.

CP-001 repair: construct the outer SAT witness only by remapping and disjointly
unioning the actual witnesses returned by selected inner representation lanes.
No family-level all-true witness is permitted on the proof-carrying path.
"""

from __future__ import annotations

from hashlib import sha256
import json
import sys
from typing import Dict, Sequence

import pf5_boundary_coverage_matrix_v0 as base
import pf5_component_product_representation_v2 as v2
import pf5_representation_escape_ladder_v1 as ladder


def strict_compose_witness(m: int, f: int, eq_sel: Dict, fan_sel: Dict) -> Dict[int, bool]:
    eq_w = eq_sel.get("witness")
    fan_w = fan_sel.get("witness")
    if eq_w is None or fan_w is None:
        raise AssertionError("selected component did not return a witness")

    eq_map, fan_map = v2.global_maps(m, f)
    out: Dict[int, bool] = {}

    for local, val in eq_w.items():
        local_i = int(local)
        if local_i not in eq_map:
            raise AssertionError(f"EQ witness contains out-of-domain root {local_i}")
        global_i = eq_map[local_i]
        if global_i in out:
            raise AssertionError(f"duplicate global witness root {global_i}")
        out[global_i] = bool(val)

    for local, val in fan_w.items():
        local_i = int(local)
        if local_i not in fan_map:
            raise AssertionError(f"FAN witness contains out-of-domain root {local_i}")
        global_i = fan_map[local_i]
        if global_i in out:
            raise AssertionError(f"component witness overlap at root {global_i}")
        out[global_i] = bool(val)

    expected = set(range(1, 2 * m + 2 * f + 1))
    if set(out) != expected:
        missing = sorted(expected - set(out))
        extra = sorted(set(out) - expected)
        raise AssertionError(f"incomplete component witness union missing={missing} extra={extra}")
    return out


def run_rung_strict(m: int, f: int = 6) -> Dict:
    # Patch the v2 construction path only for the witness composer.
    old = v2.compose_witness
    try:
        v2.compose_witness = strict_compose_witness
        r = v2.run_rung(m, f)
    finally:
        v2.compose_witness = old

    # Reconstruct once more from the selected inner witnesses and verify exact
    # byte equality to the witness size charged by the outer replay.
    eq_sel = r["components"][0]["selected"]
    fan_sel = r["components"][1]["selected"]
    w = strict_compose_witness(m, f, eq_sel, fan_sel)
    assert base.json_bytes(w) == r["outer_witness_bytes"]

    hc = ladder.make_hybrid_controls()[[8, 10, 12].index(m)]
    d, root = ladder.build_hybrid(hc)
    assert d.eval(root, w)
    r["witness_glue_source"] = "SELECTED_COMPONENT_WITNESSES_ONLY"
    r["witness_glue_complete_root_count"] = len(w)
    r["witness_glue_sha256"] = sha256(base.canon_json(w).encode()).hexdigest()
    return r


def main(argv: Sequence[str]) -> int:
    rungs = [run_rung_strict(m, 6) for m in (8, 10, 12)]
    result = {
        "artifact_id": "PF5-COMPONENT-PRODUCT-REPRESENTATION-V2.1",
        "repair": "PF5-CP-001-OUTER-WITNESS-BYPASS",
        "claim_ceiling": "P_VS_NP = OPEN",
        "caps": base.CAPS,
        "lane_order": v2.LANE_ORDER,
        "rungs": rungs,
        "v1_escape_rungs": ["HYBRID_EQ10_FAN6", "HYBRID_EQ12_FAN6"],
        "v1_escape_repaired_with_strict_inner_witness_glue": all(
            r["status"] == "PASS_EXACT_CLOSED"
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
            "witness_source=", r["witness_glue_source"],
            "witness_roots=", r["witness_glue_complete_root_count"],
            "witness_sha=", r["witness_glue_sha256"],
        )
    print(
        "PF5_CP_001_STRICT_INNER_WITNESS_GLUE =",
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
