#!/usr/bin/env python3
"""U1-L2B1A all-boundary dependency-mask lift.

Reuses the exact frozen U1-L2B0 circuit universe and truth tables. Extends only
projection-cost metadata from singleton projected boundary p to all 16 possible
boundary dependency masks for one global projected root x.
"""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json

import u1l2b0_exact_local_equivalence_kernel as KER


def dependency_count_mask(gates, mask: int) -> int:
    deps = [bool((mask >> i) & 1) for i in range(KER.K)]
    count = 0
    for a, b in gates:
        d = deps[KER.sid(a)] or deps[KER.sid(b)]
        deps.append(d)
        count += int(d)
    return count


def popcount(x: int) -> int:
    return x.bit_count()


def main() -> None:
    circuits = KER.enumerate_circuits()
    assert len(circuits) == 20792, "frozen B0 admitted circuit universe drifted"

    # Replay Boolean semantics independently for every source circuit.
    for gates, out_sign, b_out, truth, enc in circuits:
        assert KER.row_truth_mask(gates, out_sign, b_out) == truth, enc

    best = {}
    rows_by_class = defaultdict(list)
    enc_to_circuit = {}
    distinct_functions = set()

    for gates, out_sign, b_out, truth, enc in circuits:
        distinct_functions.add(truth)
        enc_to_circuit[enc] = (gates, out_sign, b_out, truth)
        for mask in range(1 << KER.K):
            ac = dependency_count_mask(gates, mask)
            g = len(gates)
            key = (truth, mask)
            cost = (ac, g, enc)
            rows_by_class[key].append((ac, g, enc))
            if key not in best or cost < best[key][0]:
                best[key] = (cost, gates, out_sign, b_out, enc)

    assert len(distinct_functions) == 1254, "frozen B0 function count drifted"
    assert len(best) == len(distinct_functions) * (1 << KER.K)

    strict_by_pop = [0] * (KER.K + 1)
    same_gate_ac_drop_by_pop = [0] * (KER.K + 1)
    source_encodings_with_strict = set()
    lexical_replays = []

    for gates, out_sign, b_out, truth, enc in circuits:
        sg = len(gates)
        for mask in range(1 << KER.K):
            sac = dependency_count_mask(gates, mask)
            (tac, tg, tenc), tgates, tout, tbout, _ = best[(truth, mask)]
            if tg > sg or not (tac < sac or tg < sg):
                continue

            # Exact identity replay remains complete truth-table equality.
            assert KER.row_truth_mask(tgates, tout, tbout) == truth
            assert KER.row_truth_mask(gates, out_sign, b_out) == truth
            assert tac <= sac
            assert tg <= sg

            pc = popcount(mask)
            strict_by_pop[pc] += 1
            if tg == sg and tac < sac:
                same_gate_ac_drop_by_pop[pc] += 1
            source_encodings_with_strict.add(enc)
            lexical_replays.append({
                "dependency_mask": mask,
                "dependency_mask_bits": format(mask, f"0{KER.K}b"),
                "dependency_popcount": pc,
                "truth_hex": f"{truth:04x}",
                "source": enc,
                "target": tenc,
                "source_cost": [sac, sg],
                "target_cost": [tac, tg],
            })

    lexical_replays.sort(key=lambda r: (r["source"], r["dependency_mask"], r["target"]))

    # Exact Pareto audit in every (truth, mask) class.
    classes_with_multiple_pareto = 0
    classes_with_growth_required_for_lower_ac = 0
    max_pareto_points = 0
    tradeoff_examples = []

    for (truth, mask), rows in sorted(rows_by_class.items()):
        pairs = sorted(set((ac, g) for ac, g, _ in rows))
        pareto = []
        for ac, g in pairs:
            if not any(ac2 <= ac and g2 <= g and (ac2 < ac or g2 < g) for ac2, g2 in pairs):
                pareto.append((ac, g))
        max_pareto_points = max(max_pareto_points, len(pareto))
        if len(pareto) > 1:
            classes_with_multiple_pareto += 1

        found_growth_tradeoff = False
        for ac, g, enc in rows:
            lower = [(ac2, g2, enc2) for ac2, g2, enc2 in rows if ac2 < ac]
            if not lower:
                continue
            if any(g2 <= g for _, g2, _ in lower):
                continue
            found_growth_tradeoff = True
            min_g = min(g2 for _, g2, _ in lower)
            target = min((ac2, g2, enc2) for ac2, g2, enc2 in lower if g2 == min_g)
            tradeoff_examples.append({
                "truth_hex": f"{truth:04x}",
                "dependency_mask": mask,
                "source": enc,
                "source_cost": [ac, g],
                "target": target[2],
                "target_cost": [target[0], target[1]],
            })
            break
        if found_growth_tradeoff:
            classes_with_growth_required_for_lower_ac += 1

    catalog_rows = []
    for (truth, mask), ((ac, g, enc), gates, out_sign, b_out, _) in sorted(best.items()):
        # Independent target replay for every retained representative.
        assert KER.row_truth_mask(gates, out_sign, b_out) == truth
        catalog_rows.append({
            "truth_hex": f"{truth:04x}",
            "dependency_mask": mask,
            "ac": ac,
            "gate_count": g,
            "encoding": enc,
        })

    catalog_payload = {
        "schema": "JANUS_U1L2B1A_ALL_DEPENDENCY_MASK_CATALOG",
        "source_catalog_sha256": "d69755c8206f52f9ba398b99ebe312d1aeb1ee283b60edefdc1d5280f860179a",
        "k": KER.K,
        "g_max": KER.G_MAX,
        "canonical_rows": catalog_rows,
    }
    catalog_bytes = json.dumps(catalog_payload, sort_keys=True, separators=(",", ":")).encode()
    catalog_sha = sha256(catalog_bytes).hexdigest()

    result = {
        "schema": "JANUS_U1L2B1A_ALL_BOUNDARY_DEPENDENCY_MASK_RESULT",
        "status": "PASS_EXHAUSTIVE_ALL_16_DEPENDENCY_MASKS",
        "frozen_admitted_circuits": len(circuits),
        "distinct_functions": len(distinct_functions),
        "dependency_masks": 1 << KER.K,
        "canonical_function_mask_classes": len(best),
        "strict_replacements_by_dependency_popcount": strict_by_pop,
        "same_gate_strict_ac_drop_by_dependency_popcount": same_gate_ac_drop_by_pop,
        "source_circuits_with_at_least_one_strict_replacement": len(source_encodings_with_strict),
        "classes_with_multiple_pareto_costs": classes_with_multiple_pareto,
        "max_pareto_points_in_one_class": max_pareto_points,
        "classes_where_lower_ac_requires_gate_growth_within_scope": classes_with_growth_required_for_lower_ac,
        "tradeoff_examples": sorted(tradeoff_examples, key=lambda r: (r["source"], r["dependency_mask"]))[:12],
        "catalog_bytes": len(catalog_bytes),
        "catalog_sha256": catalog_sha,
        "lexical_replay_receipts": lexical_replays[:16],
        "claim_ceiling": "P_VS_NP_OPEN",
        "next_gate": "U1-L2B2_LOCAL_NORMAL_FORM_ESCAPE_AND_COMPLETENESS_GATE",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("ALL_MASK_RESULT_SHA256=" + sha256(packed).hexdigest())


if __name__ == "__main__":
    main()
