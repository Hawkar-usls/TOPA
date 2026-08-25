#!/usr/bin/env python3
"""PF5 Representation Escape Ladder v1.

Composes already-revealed representation weaknesses while keeping the v0.1
caps and accounting rules unchanged.  This is a finite representation/update
coverage experiment, not a hardness or P-vs-NP proof.
"""

from __future__ import annotations

from hashlib import sha256
import json
import sys
from typing import Dict, List, Sequence, Tuple

import pf5_boundary_coverage_matrix_v0 as base
import pf5_boundary_coverage_matrix_v0_1 as repair


ORIGINAL_BUILD_CONTROL = base.build_control


def make_hybrid_controls() -> List[base.Control]:
    fan_n = 6
    out: List[base.Control] = []
    for m in (8, 10, 12):
        root_count = 2 * m + 2 * fan_n
        roots = tuple(range(1, root_count + 1))
        out.append(
            base.Control(
                name=f"HYBRID_EQ{m}_FAN{fan_n}",
                kind="HYBRID_EQ_FANOUT",
                param=m,
                root_vars=roots,
                projection_order=roots,
                obdd_order=roots,
                spec=("HYBRID_EQ_FANOUT", m, fan_n),
            )
        )
    return out


def build_hybrid(c: base.Control):
    if c.kind != "HYBRID_EQ_FANOUT":
        return ORIGINAL_BUILD_CONTROL(c)

    m = int(c.spec[1])
    fan_n = int(c.spec[2])
    d = base.Dag()
    vs = {v: d.var(v) for v in c.root_vars}

    # Equality block: x_1..x_m, y_1..y_m.
    eq_root = 1
    for i in range(1, m + 1):
        eq_root = d.land(eq_root, d.eq(vs[i], vs[m + i]))

    # Disjoint fan-out block starts after the equality roots.
    u0 = 2 * m
    v0 = 2 * m + fan_n
    e = [d.land(vs[u0 + i], vs[v0 + i]) for i in range(1, fan_n + 1)]
    pair_nodes: List[int] = []
    for i in range(fan_n):
        for j in range(i + 1, fan_n):
            pair_nodes.append(d.land(e[i], e[j]))
    fan_root = 1
    for z in pair_nodes:
        fan_root = d.land(fan_root, z)

    root = d.land(eq_root, fan_root)
    return d, root


def explicit_sat_reference(c: base.Control):
    if c.kind != "HYBRID_EQ_FANOUT":
        return base.brute_sat(c)
    d, root = build_hybrid(c)
    witness = {v: True for v in c.root_vars}
    assert d.eval(root, witness)
    # One explicit witness evaluation; no search.
    return True, witness, 1


def main(argv: Sequence[str]) -> int:
    # Patch only the experiment surface.  Core lane implementations and all
    # v0 caps remain unchanged.  Use the v0.1 OBDD accounting repair.
    base.make_controls = make_hybrid_controls
    base.build_control = build_hybrid
    base.brute_sat = explicit_sat_reference
    base.run_obdd = repair.run_obdd_fixed

    result = base.matrix_run()
    result["artifact_id"] = "PF5-REPRESENTATION-ESCAPE-LADDER-V1"
    result["protocol"] = "PF5_REPRESENTATION_ESCAPE_LADDER_V1.md"
    result["question"] = (
        "composite proof-carrying representation closure under repeated existential "
        "projection after combining revealed OBDD-order, boundary-width and template-coverage weaknesses"
    )
    escapes = [
        c["name"]
        for c in result["controls"]
        if c["representation_coverage_hole_under_v0_caps"]
    ]
    result["ladder"] = {
        "m_values": [8, 10, 12],
        "fanout_n": 6,
        "caps_changed_from_v0_1": False,
        "coverage_escape_rungs": escapes,
        "first_coverage_escape_rung": escapes[0] if escapes else None,
        "semantic_hardness_claim": False,
        "explicit_all_true_sat_witness": True,
    }
    result["portfolio"]["finite_composite_escape_found"] = bool(escapes)
    result["portfolio"]["finite_composite_escape_rungs"] = escapes
    result["portfolio"]["representation_lower_bound"] = "NOT_ESTABLISHED"
    result["portfolio"]["p_vs_np"] = "OPEN"
    result.pop("result_sha256", None)
    result["result_sha256"] = sha256(base.canon_json(result).encode()).hexdigest()

    base.print_summary(result)
    print("ESCAPE_RUNGS = " + (",".join(escapes) if escapes else "NONE"))
    print(
        "FIRST_REPRESENTATION_COVERAGE_ESCAPE = "
        + (escapes[0] if escapes else "NONE")
    )
    print("REPRESENTATION_LOWER_BOUND = NOT_ESTABLISHED")
    print("P_VS_NP = OPEN")

    if "--json-out" in argv:
        i = list(argv).index("--json-out")
        path = argv[i + 1]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
