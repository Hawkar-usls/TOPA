#!/usr/bin/env python3
"""PF5 boundary coverage matrix v0.1 accounting repair.

PF5-BCM-001 repair: preserve and charge partial OBDD construction work when
the frozen node cap is reached during BUILD.  Controls and caps are unchanged.
"""

from __future__ import annotations

from hashlib import sha256
import json
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import pf5_boundary_coverage_matrix_v0 as base


def run_obdd_fixed(c: base.Control) -> Dict:
    proof: List[Dict] = []
    max_state = 0
    cumulative = 0
    update_ops = 0
    build_ops = 0
    phase = "BUILD"

    d, raw_root = base.build_control(c)
    b = base.BDD(c.obdd_order)
    memo: Dict[Tuple[int, int], int] = {}
    rec_calls = 0

    def rec(r: int, i: int) -> int:
        nonlocal rec_calls
        rec_calls += 1
        key = (r, i)
        if key in memo:
            return memo[key]
        if r in (0, 1):
            memo[key] = r
            return r
        if i == len(c.obdd_order):
            raise AssertionError("raw root nonconstant after full OBDD order")
        x = c.obdd_order[i]
        lo = rec(d.restrict(r, x, False), i + 1)
        hi = rec(d.restrict(r, x, True), i + 1)
        out = b.mk(x, lo, hi)
        memo[key] = out
        return out

    try:
        root = rec(raw_root, 0)
        build_ops = b.ops + d.ops + rec_calls
        max_state = b.state_bytes(root)
        cumulative = max_state
        phase = "UPDATE"

        for x in c.projection_order:
            before = b.ops
            pre = root
            c0 = b.restrict(pre, x, False)
            c1 = b.restrict(pre, x, True)
            root = b.apply_or(c0, c1)
            update_ops += b.ops - before
            proof.append({"x": x, "pre": pre, "c0": c0, "c1": c1, "post": root})
            sb = b.state_bytes(root)
            max_state = max(max_state, sb)
            cumulative += sb
            base.check_common_caps(
                max_state,
                base.json_bytes(proof),
                cumulative,
                build_ops + update_ops,
            )

        if root not in (0, 1):
            raise AssertionError("all roots projected but OBDD state is nonterminal")
        final_scalar = bool(root)
        witness: Optional[Dict[int, bool]] = None
        witness_ops = 0
        if final_scalar:
            witness = {}
            for recd in reversed(proof):
                witness_ops += 1
                if b.eval(int(recd["c0"]), witness):
                    witness[int(recd["x"])] = False
                elif b.eval(int(recd["c1"]), witness):
                    witness[int(recd["x"])] = True
                else:
                    raise AssertionError("OBDD witness lift failed")
        cert = {
            "order": b.order,
            "nodes": sorted((u, *k) for u, k in b.nodes.items()),
            "root": root,
            "proof": proof,
        }
        return {
            "lane": "FROZEN_ORDER_OBDD",
            "status": "PASS_EXACT_CLOSED",
            "cap_reason": None,
            "cap_phase": None,
            "final_scalar": final_scalar,
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": base.json_bytes(proof),
            "witness_bytes": base.json_bytes(witness or {}),
            "build_ops": build_ops,
            "failed_discovery_ops": 0,
            "root_projection_ops": update_ops,
            "terminal_finalize_ops": 0,
            "verification_ops": 0,
            "witness_ops": witness_ops,
            "nonterminal_nodes_total": len(b.nodes),
            "certificate_sha256": sha256(base.canon_json(cert).encode()).hexdigest(),
            "witness": witness,
        }
    except base.CapHit as e:
        # The original v0 dropped this work when BUILD raised before the helper
        # returned.  Recompute counters from the live partial objects.
        build_ops = b.ops + d.ops + rec_calls
        partial_payload = {
            "order": b.order,
            "partial_nodes": sorted((u, *k) for u, k in b.nodes.items()),
        }
        partial_bytes = base.json_bytes(partial_payload)
        if phase == "BUILD":
            max_state = max(max_state, partial_bytes)
            cumulative = max(cumulative, partial_bytes)
        failed = build_ops if phase == "BUILD" else 0
        return {
            "lane": "FROZEN_ORDER_OBDD",
            "status": "CAP_HIT",
            "cap_reason": str(e),
            "cap_phase": phase,
            "final_scalar": None,
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": base.json_bytes(proof),
            "witness_bytes": 0,
            "build_ops": build_ops,
            "failed_discovery_ops": failed,
            "root_projection_ops": update_ops,
            "terminal_finalize_ops": 0,
            "verification_ops": 0,
            "witness_ops": 0,
            "nonterminal_nodes_total": len(b.nodes),
            "certificate_sha256": None,
            "witness": None,
        }


def main(argv: Sequence[str]) -> int:
    base.run_obdd = run_obdd_fixed
    result = base.matrix_run()
    result["accounting_revision"] = "v0.1_PF5_BCM_001_REPAIR"
    # Rebind the result hash because the revision field is part of the receipt.
    result.pop("result_sha256", None)
    result["result_sha256"] = sha256(base.canon_json(result).encode()).hexdigest()
    base.print_summary(result)
    print("PF5_BCM_001_FAILED_BUILD_COST_ACCOUNTING = REPAIRED")
    if "--json-out" in argv:
        i = list(argv).index("--json-out")
        path = argv[i + 1]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
