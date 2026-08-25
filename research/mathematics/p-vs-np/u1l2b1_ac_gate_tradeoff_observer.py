#!/usr/bin/env python3
"""Exact observer for AC_x versus gate-count tradeoffs in frozen U1-L2B0 scope.

No catalog mutation, no heuristic ranking. Enumerates the same frozen k=4,g<=3
circuits and asks whether a lower affected-cone representation exists only at a
strictly larger gate count than a given source representation.
"""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json

import u1l2b0_exact_local_equivalence_kernel as KER


def main() -> None:
    circuits = KER.enumerate_circuits()

    by_class = defaultdict(list)
    for gates, out_sign, b_out, truth, enc in circuits:
        for p in range(KER.K):
            ac = KER.dependency_count(gates, p)
            g = len(gates)
            by_class[(truth, p)].append((ac, g, enc))

    class_pareto = {}
    classes_with_tradeoff = 0
    source_circuits_requiring_growth_for_lower_ac = set()
    source_instances_requiring_growth = 0
    max_required_growth = 0
    lexical_examples = []

    for key, rows in sorted(by_class.items()):
        # Achievable cost pairs and their lexical witness.
        pair_witness = {}
        for ac, g, enc in rows:
            pair_witness[(ac, g)] = min(enc, pair_witness.get((ac, g), enc))

        pairs = sorted(pair_witness)
        pareto = []
        for ac, g in pairs:
            dominated = any((ac2 <= ac and g2 <= g and (ac2 < ac or g2 < g)) for ac2, g2 in pairs)
            if not dominated:
                pareto.append((ac, g))
        class_pareto[key] = pareto

        class_has_tradeoff = False
        for ac, g, enc in rows:
            lower = [(ac2, g2, enc2) for ac2, g2, enc2 in rows if ac2 < ac]
            if not lower:
                continue
            feasible_nongrowth = [(ac2, g2, enc2) for ac2, g2, enc2 in lower if g2 <= g]
            if feasible_nongrowth:
                continue

            min_growth_g = min(g2 for _, g2, _ in lower)
            best_targets = sorted((ac2, g2, enc2) for ac2, g2, enc2 in lower if g2 == min_growth_g)
            target = best_targets[0]
            growth = min_growth_g - g
            assert growth > 0
            class_has_tradeoff = True
            source_instances_requiring_growth += 1
            source_circuits_requiring_growth_for_lower_ac.add(enc)
            max_required_growth = max(max_required_growth, growth)
            lexical_examples.append({
                "truth_hex": f"{key[0]:04x}",
                "projected_var": key[1],
                "source": enc,
                "source_cost": [ac, g],
                "lower_ac_target": target[2],
                "target_cost": [target[0], target[1]],
                "required_gate_growth": growth,
                "class_pareto_costs": [list(x) for x in pareto],
            })

        if class_has_tradeoff:
            classes_with_tradeoff += 1

    lexical_examples.sort(key=lambda r: (r["source"], r["projected_var"], r["lower_ac_target"]))

    multi_pareto_classes = sum(1 for v in class_pareto.values() if len(v) > 1)
    max_pareto_points = max(len(v) for v in class_pareto.values())

    result = {
        "schema": "JANUS_U1L2B1_AC_GATE_TRADEOFF_OBSERVER",
        "catalog_scope": {"k": KER.K, "g_max": KER.G_MAX},
        "admitted_circuits": len(circuits),
        "function_projection_classes": len(by_class),
        "classes_with_multiple_pareto_costs": multi_pareto_classes,
        "max_pareto_points_in_one_class": max_pareto_points,
        "classes_where_some_source_needs_gate_growth_for_lower_ac": classes_with_tradeoff,
        "source_instances_where_lower_ac_requires_gate_growth": source_instances_requiring_growth,
        "distinct_source_encodings_where_lower_ac_requires_gate_growth": len(source_circuits_requiring_growth_for_lower_ac),
        "max_required_gate_growth_within_frozen_scope": max_required_growth,
        "lexical_examples": lexical_examples[:20],
        "firewall": [
            "OBSERVER_ONLY_NO_CATALOG_CHANGE",
            "EXACT_COMPLETE_TRUTH_TABLE_CLASSES_ONLY",
            "LOCAL_TRADEOFF_DOES_NOT_IMPLY_GLOBAL_LOWER_BOUND",
            "P_VS_NP_OPEN"
        ]
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("TRADEOFF_RESULT_SHA256=" + sha256(packed).hexdigest())


if __name__ == "__main__":
    main()
