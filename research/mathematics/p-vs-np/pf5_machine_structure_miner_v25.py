#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict

import pf5_self_subsuming_resolution_v24 as v24

V24_RESULT_SHA256 = "865eb2de5fdc2c7ae0687f261304bfbafa36ac61cacdd0bcb14441dba1e8a8b9"
EXPECTED_TERMINALS = {"TRUE": 18, "FALSE": 3, "OPEN_RESIDUAL": 11}
LANE_PRIORITY = [
    "COMPONENT_PRODUCT",
    "UNIT_PROPAGATION_CERTIFICATE",
    "BIJUNCTIVE_2SAT_SCC",
    "HORN_FORWARD_CHAIN",
    "DUAL_HORN_FORWARD_CHAIN",
]


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def add(counter, key, amount=1):
    counter[key] = counter.get(key, 0) + amount


def variables_of(formula):
    return v24.v22.v20.v18.v13.variables_of(formula)


def crystal(formula):
    return v24.v22.v20.v18.v14.crystal(formula)


def interaction_components(formula, ledger):
    variables = variables_of(formula)
    adjacency = {variable: set() for variable in variables}
    for clause in formula:
        ledger["clause_visits"] += 1
        clause_variables = sorted({abs(int(literal)) for literal in clause})
        ledger["literal_visits"] += len(clause)
        for i, left in enumerate(clause_variables):
            for right in clause_variables[i + 1 :]:
                if right not in adjacency[left]:
                    ledger["graph_edge_insertions"] += 1
                adjacency[left].add(right)
                adjacency[right].add(left)

    components = []
    seen = set()
    for start in variables:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component = []
        while stack:
            current = stack.pop()
            component.append(current)
            for nxt in sorted(adjacency[current]):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        components.append(tuple(sorted(component)))
    components.sort()
    edge_count = sum(len(neighbors) for neighbors in adjacency.values()) // 2
    cycle_rank = edge_count - len(variables) + len(components) if variables else 0
    return components, edge_count, cycle_rank


def variable_signature(formula, variable, ledger):
    context = Counter()
    for clause in formula:
        if variable not in clause and -variable not in clause:
            continue
        self_sign = "P" if variable in clause else "N"
        for literal in clause:
            if abs(literal) == variable:
                continue
            ledger["signature_context_visits"] += 1
            other_sign = "P" if literal > 0 else "N"
            context[(self_sign, other_sign, len(clause))] += 1
    return tuple((list(key), count) for key, count in sorted(context.items()))


def pair_motifs(formula, ledger):
    motifs = Counter()
    for i, left in enumerate(formula):
        left_set = set(left)
        for right in formula[i + 1 :]:
            ledger["clause_pair_tests"] += 1
            right_set = set(right)
            same = len(left_set & right_set)
            opposite = sum(1 for literal in left_set if -literal in right_set)
            widths = tuple(sorted((len(left), len(right))))
            motifs[(widths[0], widths[1], same, opposite)] += 1
    return motifs


def structural_profile(formula, seed, n, m, ledger):
    c = crystal(formula)
    widths = [len(clause) for clause in formula]
    ledger["clause_visits"] += len(formula)
    ledger["literal_visits"] += sum(widths)
    width_hist = Counter(widths)
    horn = all(sum(literal > 0 for literal in clause) <= 1 for clause in formula)
    dual_horn = all(sum(literal < 0 for literal in clause) <= 1 for clause in formula)
    bijunctive = all(len(clause) <= 2 for clause in formula)
    unit_count = sum(len(clause) == 1 for clause in formula)
    variables = variables_of(formula)
    components, interaction_edges, cycle_rank = interaction_components(formula, ledger)

    signature_counts = Counter()
    for variable in variables:
        signature_counts[json.dumps(variable_signature(formula, variable, ledger), separators=(",", ":"))] += 1
    signature_collisions = sorted(count for count in signature_counts.values() if count > 1)

    motifs = pair_motifs(formula, ledger)
    actions = []
    if len(components) > 1:
        actions.append("COMPONENT_PRODUCT")
    if unit_count > 0:
        actions.append("UNIT_PROPAGATION_CERTIFICATE")
    if bijunctive:
        actions.append("BIJUNCTIVE_2SAT_SCC")
    if horn:
        actions.append("HORN_FORWARD_CHAIN")
    if dual_horn:
        actions.append("DUAL_HORN_FORWARD_CHAIN")

    signature_object = {
        "width_hist": sorted(width_hist.items()),
        "variable_count": len(variables),
        "clause_count": len(formula),
        "component_sizes": sorted(len(component) for component in components),
        "interaction_edges": interaction_edges,
        "cycle_rank": cycle_rank,
        "horn": horn,
        "dual_horn": dual_horn,
        "bijunctive": bijunctive,
        "unit_count": unit_count,
        "variable_signature_multiset": sorted(signature_counts.values()),
        "pair_motif_multiset": sorted((list(key), count) for key, count in motifs.items()),
    }

    return {
        "n": n,
        "m": m,
        "seed": seed,
        "residual_crystal": c,
        "variable_count": len(variables),
        "clause_count": len(formula),
        "deficiency_m_minus_n": len(formula) - len(variables),
        "width_histogram": {str(width): count for width, count in sorted(width_hist.items())},
        "max_clause_width": max(widths) if widths else 0,
        "unit_clause_count": unit_count,
        "horn": horn,
        "dual_horn": dual_horn,
        "bijunctive_2cnf": bijunctive,
        "interaction_components": [list(component) for component in components],
        "interaction_edge_count": interaction_edges,
        "interaction_cycle_rank": cycle_rank,
        "variable_signature_collision_class_sizes": signature_collisions,
        "signature_collision_is_symmetry_proof": False,
        "pair_motifs": [
            {"widths": [key[0], key[1]], "same_sign_overlap": key[2], "opposite_sign_overlap": key[3], "count": count}
            for key, count in sorted(motifs.items())
        ],
        "actionable_frontier": actions,
        "structural_signature_sha256": digest(signature_object),
    }


def run():
    terminal_counts = Counter()
    rows = []
    ledger = {
        "clause_visits": 0,
        "literal_visits": 0,
        "clause_pair_tests": 0,
        "signature_context_visits": 0,
        "graph_edge_insertions": 0,
    }

    for n, m, seeds in v24.FROZEN_GROUPS:
        for seed in seeds:
            source = v24.v22.v20.v18.v12.canonical_formula(
                v24.v22.v20.v18.v9.random_connected_3cnf(
                    seed, variable_count=n, clause_count=m
                )
            )
            final, transcript, _ = v24.exact_closure(source)
            assert v24.replay(source, transcript) == final
            status = v24.terminal_status(final)
            terminal_counts[status] += 1
            if status == "OPEN_RESIDUAL":
                rows.append(structural_profile(final, seed, n, m, ledger))

    assert dict(terminal_counts) == EXPECTED_TERMINALS
    assert len(rows) == 11

    coverage = {lane: 0 for lane in LANE_PRIORITY}
    for row in rows:
        for lane in row["actionable_frontier"]:
            coverage[lane] += 1

    priority_index = {lane: index for index, lane in enumerate(LANE_PRIORITY)}
    ranked = sorted(
        (
            {
                "lane": lane,
                "survivor_coverage": count,
                "coverage_fraction": count / len(rows),
                "status": "EXISTING_EXACT_THEOREM" if lane == "COMPONENT_PRODUCT" else "STANDARD_POLY_CLASS_PROVIDER_REQUIRED",
            }
            for lane, count in coverage.items()
        ),
        key=lambda item: (-item["survivor_coverage"], priority_index[item["lane"]]),
    )
    dominant = ranked[0]["lane"] if ranked and ranked[0]["survivor_coverage"] > 0 else None

    clusters = defaultdict(list)
    motif_global = Counter()
    for row in rows:
        clusters[row["structural_signature_sha256"]].append(row["seed"])
        for motif in row["pair_motifs"]:
            key = (
                motif["widths"][0], motif["widths"][1],
                motif["same_sign_overlap"], motif["opposite_sign_overlap"]
            )
            motif_global[key] += motif["count"]

    cluster_rows = sorted(
        (
            {"signature_sha256": signature, "count": len(seeds), "seeds": sorted(seeds)}
            for signature, seeds in clusters.items()
        ),
        key=lambda item: (-item["count"], item["signature_sha256"]),
    )
    top_motifs = [
        {
            "widths": [key[0], key[1]],
            "same_sign_overlap": key[2],
            "opposite_sign_overlap": key[3],
            "count": count,
        }
        for key, count in motif_global.most_common(20)
    ]

    next_gate = {
        "COMPONENT_PRODUCT": "V26_FRESH_COMPONENT_PRODUCT_REPLAY",
        "UNIT_PROPAGATION_CERTIFICATE": "V26_FRESH_PROOF_CARRYING_UNIT_PROPAGATION",
        "BIJUNCTIVE_2SAT_SCC": "V26_FRESH_PROOF_CARRYING_2SAT_SCC",
        "HORN_FORWARD_CHAIN": "V26_FRESH_PROOF_CARRYING_HORN",
        "DUAL_HORN_FORWARD_CHAIN": "V26_FRESH_PROOF_CARRYING_DUAL_HORN",
        None: "V26_FRESH_STRUCTURAL_OBSTRUCTION_HOLDOUT",
    }[dominant]

    result = {
        "artifact_id": "PF5-MACHINE-STRUCTURE-MINER-V25",
        "status": "POST_HOC_MACHINE_DISCOVERY_COMPLETE",
        "role": "OBSERVER_ONLY_NO_FORMULA_REWRITE",
        "source_role": "V24_FROZEN_OUTPUTS_ONLY",
        "v24_result_sha256": V24_RESULT_SHA256,
        "v24_terminal_counts": dict(terminal_counts),
        "open_residual_cases": len(rows),
        "modifies_formula": False,
        "uses_sat_oracle": False,
        "uses_truth_table": False,
        "uses_hephaestus_for_decision": False,
        "runtime_profiler_polynomial_in_explicit_residual_size": True,
        "admission_effect": "NONE_POST_HOC_DISCOVERY_ONLY",
        "fresh_holdout_required_before_lane_admission": True,
        "rows": rows,
        "structural_clusters": cluster_rows,
        "top_recurring_pair_motifs": top_motifs,
        "ranked_actionable_frontier": ranked,
        "dominant_actionable_lane": dominant,
        "next_gate": next_gate,
        "observer_cost_ledger": ledger,
        "universal_exact_closure": "OPEN",
        "p_vs_np": "OPEN",
    }
    result["rows_manifest_sha256"] = digest(
        [(row["seed"], row["residual_crystal"]["sha256"], row["structural_signature_sha256"]) for row in rows]
    )
    result["result_sha256"] = digest({key: value for key, value in result.items() if key != "result_sha256"})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out")
    args = parser.parse_args()
    result = run()
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print("PF5_MACHINE_STRUCTURE_MINER_V25 =", result["status"])
    print("V24_TERMINALS =", result["v24_terminal_counts"])
    print("OPEN_RESIDUAL_CASES =", result["open_residual_cases"])
    print("RANKED_ACTIONABLE_FRONTIER =", result["ranked_actionable_frontier"])
    print("DOMINANT_ACTIONABLE_LANE =", result["dominant_actionable_lane"])
    print("NEXT_GATE =", result["next_gate"])
    print("ROWS_MANIFEST_SHA256 =", result["rows_manifest_sha256"])
    print("OBSERVER_COST_LEDGER =", result["observer_cost_ledger"])
    print("P_VS_NP =", result["p_vs_np"])
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
