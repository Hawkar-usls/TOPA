#!/usr/bin/env python3
"""Observer-only analysis of the frozen U1-L2B0 exact catalog.

Does not change k/g/catalog selection. It classifies already-admitted exact
replacement pairs by whether they reduce gate count or only the projected
syntactic affected-cone at identical gate count.
"""

from __future__ import annotations

from hashlib import sha256
import json

import u1l2b0_exact_local_equivalence_kernel as KER


def semantic_depends(truth: int, p: int) -> bool:
    for row in range(KER.ROWS):
        other = row ^ (1 << p)
        if row < other:
            if ((truth >> row) & 1) != ((truth >> other) & 1):
                return True
    return False


def main() -> None:
    circuits = KER.enumerate_circuits()

    best = {}
    for gates, out_sign, b_out, truth, enc in circuits:
        for p in range(KER.K):
            dep = KER.dependency_count(gates, p)
            cost = (dep, len(gates), enc)
            key = (truth, p)
            if key not in best or cost < best[key][0]:
                best[key] = (cost, gates, out_sign, b_out, enc)

    gate_drop_pairs = 0
    same_gate_dep_drop_pairs = 0
    same_gate_dep_drop_semantic_dep_pairs = 0
    same_gate_dep_drop_semantic_independent_pairs = 0
    source_encodings_same_gate_dep_drop = set()
    examples_dep = []
    examples_indep = []

    for gates, out_sign, b_out, truth, enc in circuits:
        sg = len(gates)
        for p in range(KER.K):
            sd = KER.dependency_count(gates, p)
            (td, tg, tenc), tgates, tout, tbout, _ = best[(truth, p)]

            # Same admission rule as frozen provider.
            if tg > sg or not (td < sd or tg < sg):
                continue

            # Independent semantic replay of target/source identity.
            assert KER.row_truth_mask(gates, out_sign, b_out) == truth
            assert KER.row_truth_mask(tgates, tout, tbout) == truth

            if tg < sg:
                gate_drop_pairs += 1
            elif tg == sg and td < sd:
                same_gate_dep_drop_pairs += 1
                source_encodings_same_gate_dep_drop.add(enc)
                record = {
                    "projected_var": p,
                    "truth_hex": f"{truth:04x}",
                    "semantic_depends_on_projected_var": semantic_depends(truth, p),
                    "source": enc,
                    "target": tenc,
                    "source_cost": [sd, sg],
                    "target_cost": [td, tg],
                }
                if record["semantic_depends_on_projected_var"]:
                    same_gate_dep_drop_semantic_dep_pairs += 1
                    examples_dep.append(record)
                else:
                    same_gate_dep_drop_semantic_independent_pairs += 1
                    examples_indep.append(record)

    examples_dep.sort(key=lambda r: (r["source"], r["projected_var"], r["target"]))
    examples_indep.sort(key=lambda r: (r["source"], r["projected_var"], r["target"]))

    result = {
        "schema": "JANUS_U1L2B0_PROJECTION_SPECIFIC_OBSERVER",
        "catalog_scope": {"k": KER.K, "g_max": KER.G_MAX},
        "admitted_circuits": len(circuits),
        "gate_drop_replacement_pairs": gate_drop_pairs,
        "same_gate_count_strict_affected_cone_drop_pairs": same_gate_dep_drop_pairs,
        "same_gate_count_affected_cone_drop_semantic_dep_pairs": same_gate_dep_drop_semantic_dep_pairs,
        "same_gate_count_affected_cone_drop_semantic_independent_pairs": same_gate_dep_drop_semantic_independent_pairs,
        "source_circuits_with_same_gate_affected_cone_drop": len(source_encodings_same_gate_dep_drop),
        "lexical_examples_output_still_depends_on_projected_var": examples_dep[:12],
        "lexical_examples_output_independent_of_projected_var": examples_indep[:12],
        "interpretation_firewall": [
            "OBSERVER_DOES_NOT_CHANGE_FROZEN_CATALOG",
            "SAME_GATE_DEP_DROP_IS_EXACT_LOCAL_IDENTITY_NOT_GLOBAL_COMPLEXITY_THEOREM",
            "P_VS_NP_OPEN"
        ]
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("OBSERVER_RESULT_SHA256=" + sha256(packed).hexdigest())


if __name__ == "__main__":
    main()
