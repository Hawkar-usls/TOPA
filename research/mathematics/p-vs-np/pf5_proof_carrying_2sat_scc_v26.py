#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import heapq
import itertools
import json
from collections import deque

import pf5_self_subsuming_resolution_v24 as v24

FROZEN_GROUPS = [
    (6, 24, list(range(917600, 917616))),
    (7, 28, list(range(917700, 917716))),
]


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def lit_key(literal):
    return (abs(int(literal)), int(literal) < 0)


def variables_of(formula):
    return v24.v22.v20.v18.v13.variables_of(formula)


def crystal(formula):
    return v24.v22.v20.v18.v14.crystal(formula)


def formula_satisfied(formula, assignment, ledger=None):
    for clause in formula:
        clause_ok = False
        for literal in clause:
            if ledger is not None:
                ledger["verification_ops"] = ledger.get("verification_ops", 0) + 1
            value = bool(assignment[abs(literal)])
            if value == (literal > 0):
                clause_ok = True
                break
        if not clause_ok:
            return False
    return True


def eligibility_2cnf(formula, ledger):
    for clause in formula:
        ledger["eligibility_clause_checks"] += 1
        if len(clause) > 2:
            ledger["failed_eligibility_checks"] += 1
            return False
    return True


def implication_edges(formula, ledger):
    variables = variables_of(formula)
    vertices = sorted([literal for v in variables for literal in (v, -v)], key=lit_key)
    adjacency = {literal: [] for literal in vertices}
    reverse = {literal: [] for literal in vertices}
    edge_rows = []

    for clause_index, clause in enumerate(formula):
        if len(clause) == 0 or len(clause) > 2:
            raise AssertionError("2-SAT graph received non-2-CNF residual")
        if len(clause) == 1:
            a = int(clause[0])
            derived = [(-a, a)]
        else:
            a, b = map(int, clause)
            derived = [(-a, b), (-b, a)]
        for source, target in derived:
            row = {
                "from": source,
                "to": target,
                "clause_index": clause_index,
                "clause": list(clause),
            }
            adjacency[source].append(row)
            reverse[target].append(source)
            edge_rows.append(row)
            ledger["graph_edges"] += 1

    for literal in vertices:
        adjacency[literal].sort(key=lambda row: (lit_key(row["to"]), row["clause_index"], row["clause"]))
        reverse[literal] = sorted(set(reverse[literal]), key=lit_key)

    ledger["graph_vertices"] += len(vertices)
    ledger["edge_provenance_bytes"] += len(
        json.dumps(edge_rows, sort_keys=True, separators=(",", ":")).encode()
    )
    graph_bytes = len(
        json.dumps(
            {"vertices": vertices, "edges": edge_rows},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    )
    ledger["state_bytes_peak"] = max(ledger["state_bytes_peak"], graph_bytes)
    ledger["cumulative_state_bytes"] += graph_bytes
    return vertices, adjacency, reverse, edge_rows


def deterministic_scc(vertices, adjacency, reverse, ledger):
    seen = set()
    finish = []
    neighbor_cache = {
        node: sorted({row["to"] for row in adjacency[node]}, key=lit_key)
        for node in vertices
    }

    for start in vertices:
        if start in seen:
            continue
        seen.add(start)
        stack = [(start, 0)]
        while stack:
            node, index = stack[-1]
            neighbors = neighbor_cache[node]
            if index < len(neighbors):
                nxt = neighbors[index]
                stack[-1] = (node, index + 1)
                ledger["scc_graph_visits"] += 1
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append((nxt, 0))
            else:
                finish.append(node)
                stack.pop()

    component_of = {}
    components = []
    for start in reversed(finish):
        if start in component_of:
            continue
        component_id = len(components)
        members = []
        stack = [start]
        component_of[start] = component_id
        while stack:
            node = stack.pop()
            members.append(node)
            for nxt in reverse[node]:
                ledger["reverse_edge_visits"] += 1
                if nxt not in component_of:
                    component_of[nxt] = component_id
                    stack.append(nxt)
        components.append(sorted(members, key=lit_key))

    return component_of, components


def condensation_topological_rank(vertices, adjacency, component_of, components, ledger):
    dag = {component_id: set() for component_id in range(len(components))}
    indegree = {component_id: 0 for component_id in range(len(components))}
    for source in vertices:
        source_component = component_of[source]
        for row in adjacency[source]:
            target_component = component_of[row["to"]]
            if source_component != target_component and target_component not in dag[source_component]:
                dag[source_component].add(target_component)
                indegree[target_component] += 1
                ledger["condensation_edges"] += 1

    heap = [component_id for component_id, degree in indegree.items() if degree == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        component_id = heapq.heappop(heap)
        ledger["topological_ops"] += 1
        order.append(component_id)
        for target in sorted(dag[component_id]):
            indegree[target] -= 1
            ledger["topological_ops"] += 1
            if indegree[target] == 0:
                heapq.heappush(heap, target)
                ledger["topological_ops"] += 1
    if len(order) != len(components):
        raise AssertionError("condensation graph unexpectedly cyclic")
    return {component_id: index for index, component_id in enumerate(order)}


def find_implication_path(start, goal, component_id, adjacency, component_of, ledger):
    queue = deque([start])
    parent = {start: None}
    parent_edge = {}
    while queue:
        node = queue.popleft()
        if node == goal:
            break
        for row in adjacency[node]:
            ledger["path_search_edge_visits"] += 1
            nxt = row["to"]
            if component_of[nxt] != component_id or nxt in parent:
                continue
            parent[nxt] = node
            parent_edge[nxt] = row
            queue.append(nxt)
    if goal not in parent:
        raise AssertionError("SCC path reconstruction failed")
    path = []
    current = goal
    while current != start:
        row = parent_edge[current]
        path.append(row)
        current = parent[current]
    path.reverse()
    return path


def edge_is_supported(formula, row, ledger):
    index = int(row["clause_index"])
    if index < 0 or index >= len(formula):
        return False
    clause = tuple(row["clause"])
    if tuple(formula[index]) != clause:
        return False
    source = int(row["from"])
    target = int(row["to"])
    ledger["verification_ops"] += 1
    if len(clause) == 1:
        a = int(clause[0])
        return (source, target) == (-a, a)
    if len(clause) == 2:
        a, b = map(int, clause)
        return (source, target) in {(-a, b), (-b, a)}
    return False


def verify_path(formula, path, start, goal, ledger):
    current = start
    for row in path:
        if int(row["from"]) != current or not edge_is_supported(formula, row, ledger):
            return False
        current = int(row["to"])
    return current == goal


def verify_unsat_certificate(formula, certificate, ledger):
    variable = int(certificate["variable"])
    return (
        verify_path(formula, certificate["path_pos_to_neg"], variable, -variable, ledger)
        and verify_path(formula, certificate["path_neg_to_pos"], -variable, variable, ledger)
    )


def solve_2sat(formula):
    ledger = {
        "eligibility_clause_checks": 0,
        "failed_eligibility_checks": 0,
        "graph_vertices": 0,
        "graph_edges": 0,
        "edge_provenance_bytes": 0,
        "scc_graph_visits": 0,
        "reverse_edge_visits": 0,
        "condensation_edges": 0,
        "topological_ops": 0,
        "path_search_edge_visits": 0,
        "certificate_bytes": 0,
        "witness_bytes": 0,
        "verification_ops": 0,
        "state_bytes_peak": 0,
        "cumulative_state_bytes": 0,
    }
    if not eligibility_2cnf(formula, ledger):
        return {"status": "UNSUPPORTED_NON_2CNF", "proof": None, "assignment": None}, ledger

    vertices, adjacency, reverse, edge_rows = implication_edges(formula, ledger)
    component_of, components = deterministic_scc(vertices, adjacency, reverse, ledger)
    contradiction = next(
        (variable for variable in variables_of(formula) if component_of[variable] == component_of[-variable]),
        None,
    )

    scc_manifest = {
        "components": components,
        "component_of": {str(literal): component_of[literal] for literal in vertices},
        "edge_count": len(edge_rows),
    }
    scc_sha256 = digest(scc_manifest)

    if contradiction is not None:
        component_id = component_of[contradiction]
        certificate = {
            "kind": "2SAT_UNSAT_MUTUAL_IMPLICATION",
            "variable": contradiction,
            "path_pos_to_neg": find_implication_path(
                contradiction, -contradiction, component_id, adjacency, component_of, ledger
            ),
            "path_neg_to_pos": find_implication_path(
                -contradiction, contradiction, component_id, adjacency, component_of, ledger
            ),
            "scc_manifest_sha256": scc_sha256,
            "residual_sha256": crystal(formula)["sha256"],
        }
        if not verify_unsat_certificate(formula, certificate, ledger):
            raise AssertionError("UNSAT implication certificate failed verification")
        proof_bytes = len(json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode())
        ledger["certificate_bytes"] += proof_bytes
        ledger["state_bytes_peak"] = max(ledger["state_bytes_peak"], proof_bytes)
        ledger["cumulative_state_bytes"] += proof_bytes
        return {"status": "UNSAT", "proof": certificate, "assignment": None}, ledger

    rank = condensation_topological_rank(vertices, adjacency, component_of, components, ledger)
    assignment = {
        variable: rank[component_of[variable]] > rank[component_of[-variable]]
        for variable in variables_of(formula)
    }
    if not formula_satisfied(formula, assignment, ledger):
        raise AssertionError("SCC assignment did not satisfy 2-CNF residual")
    witness = {str(variable): assignment[variable] for variable in sorted(assignment)}
    witness_bytes = len(json.dumps(witness, sort_keys=True, separators=(",", ":")).encode())
    ledger["witness_bytes"] += witness_bytes
    ledger["state_bytes_peak"] = max(ledger["state_bytes_peak"], witness_bytes)
    ledger["cumulative_state_bytes"] += witness_bytes
    proof = {
        "kind": "2SAT_SAT_WITNESS",
        "scc_manifest_sha256": scc_sha256,
        "residual_sha256": crystal(formula)["sha256"],
        "assignment_sha256": digest(witness),
    }
    proof_bytes = len(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode())
    ledger["certificate_bytes"] += proof_bytes
    ledger["cumulative_state_bytes"] += proof_bytes
    ledger["state_bytes_peak"] = max(ledger["state_bytes_peak"], proof_bytes)
    return {"status": "SAT", "proof": proof, "assignment": assignment}, ledger


def add_ledger(target, source):
    for key, value in source.items():
        target[key] = target.get(key, 0) + int(value)


def terminal_status(residual):
    return v24.terminal_status(residual)


def source_truth(source, audit_ledger):
    variables = variables_of(source)
    for bits in itertools.product((False, True), repeat=len(variables)):
        audit_ledger["truth_table_rows"] += 1
        assignment = dict(zip(variables, bits))
        if formula_satisfied(source, assignment, audit_ledger):
            return True
    return False


def run():
    # Phase 1: materialize and hash the fresh sources before provider work.
    sources = []
    for n, m, seeds in FROZEN_GROUPS:
        for seed in seeds:
            source = v24.v22.v20.v18.v12.canonical_formula(
                v24.v22.v20.v18.v9.random_connected_3cnf(
                    seed, variable_count=n, clause_count=m
                )
            )
            sources.append({"n": n, "m": m, "seed": seed, "source": source, "source_crystal": crystal(source)})
    source_manifest_sha256 = digest(
        [(row["n"], row["m"], row["seed"], row["source_crystal"]["sha256"]) for row in sources]
    )

    # Phase 2: freeze v24 baselines before v26 decisions.
    baselines = []
    for row in sources:
        residual, transcript, inherited_runtime = v24.exact_closure(row["source"])
        assert v24.replay(row["source"], transcript) == residual
        baselines.append({**row, "residual": residual, "transcript": transcript, "inherited_runtime": inherited_runtime})
    baseline_manifest_sha256 = digest(
        [(row["seed"], crystal(row["residual"])["sha256"], terminal_status(row["residual"])) for row in baselines]
    )

    # Phase 3: run only the frozen structural gate; keep non-2-CNF residuals open.
    frozen_provider = []
    runtime_total = {}
    inherited_total = {"v13": {}, "v15": {}, "v18": {}, "v20": {}, "v22": {}, "v24": {}}
    for row in baselines:
        for lane in inherited_total:
            add_ledger(inherited_total[lane], row["inherited_runtime"][lane])
        baseline_status = terminal_status(row["residual"])
        provider = None
        local = {"eligibility_clause_checks":0,"failed_eligibility_checks":0}
        final_status = baseline_status
        lifted_source_witness = None
        witness_lift_ops = 0

        if baseline_status == "OPEN_RESIDUAL":
            provider, local = solve_2sat(row["residual"])
            if provider["status"] == "SAT":
                final_status = "TRUE"
                lifted_source_witness, lift_ledger = v24.lift_witness(
                    row["source"], row["residual"], row["transcript"], provider["assignment"]
                )
                witness_lift_ops = sum(int(value) for value in lift_ledger.values())
                local["witness_lift_ops"] = local.get("witness_lift_ops", 0) + witness_lift_ops
                source_verify_ledger = {"verification_ops": 0}
                if not formula_satisfied(row["source"], lifted_source_witness, source_verify_ledger):
                    raise AssertionError("lifted 2-SAT witness failed original source")
                local["verification_ops"] = local.get("verification_ops", 0) + source_verify_ledger["verification_ops"]
                source_witness_json = {str(v): bool(lifted_source_witness[v]) for v in sorted(lifted_source_witness)}
                local["witness_bytes"] = local.get("witness_bytes", 0) + len(
                    json.dumps(source_witness_json, sort_keys=True, separators=(",", ":")).encode()
                )
            elif provider["status"] == "UNSAT":
                final_status = "FALSE"
            elif provider["status"] == "UNSUPPORTED_NON_2CNF":
                final_status = "OPEN_RESIDUAL"
            else:
                raise AssertionError("unknown v26 provider status")

        add_ledger(runtime_total, local)
        frozen_provider.append(
            {
                **row,
                "baseline_status": baseline_status,
                "provider": provider,
                "provider_runtime": local,
                "final_status": final_status,
                "lifted_source_witness": lifted_source_witness,
                "witness_lift_ops": witness_lift_ops,
            }
        )

    provider_batch_sha256 = digest(
        [
            (
                row["seed"],
                crystal(row["residual"])["sha256"],
                row["baseline_status"],
                None if row["provider"] is None else {
                    "status": row["provider"]["status"],
                    "proof": row["provider"]["proof"],
                    "assignment": None if row["provider"]["assignment"] is None else {str(v): row["provider"]["assignment"][v] for v in sorted(row["provider"]["assignment"])},
                },
                row["final_status"],
            )
            for row in frozen_provider
        ]
    )

    # Phase 4: only now use bounded exhaustive truth tables as a finite semantic audit.
    audit_total = {"truth_table_rows": 0, "verification_ops": 0}
    all_terminal_audits_pass = True
    rows = []
    counts = {
        "cases": len(frozen_provider),
        "v24_true": 0,
        "v24_false": 0,
        "v24_open": 0,
        "eligible_2sat": 0,
        "provider_sat": 0,
        "provider_unsat": 0,
        "unsupported_open": 0,
        "final_true": 0,
        "final_false": 0,
        "final_open": 0,
    }

    for row in frozen_provider:
        counts[{"TRUE":"v24_true","FALSE":"v24_false","OPEN_RESIDUAL":"v24_open"}[row["baseline_status"]]] += 1
        provider_status = None if row["provider"] is None else row["provider"]["status"]
        if provider_status in {"SAT", "UNSAT"}:
            counts["eligible_2sat"] += 1
            counts["provider_sat" if provider_status == "SAT" else "provider_unsat"] += 1
        elif provider_status == "UNSUPPORTED_NON_2CNF":
            counts["unsupported_open"] += 1

        counts[{"TRUE":"final_true","FALSE":"final_false","OPEN_RESIDUAL":"final_open"}[row["final_status"]]] += 1
        audit_pass = None
        if row["final_status"] in {"TRUE", "FALSE"}:
            truth = source_truth(row["source"], audit_total)
            audit_pass = truth if row["final_status"] == "TRUE" else not truth
            all_terminal_audits_pass = all_terminal_audits_pass and audit_pass

        proof_verified = None
        residual_assignment = None
        if provider_status == "UNSAT":
            verify_ledger = {"verification_ops": 0}
            proof_verified = verify_unsat_certificate(row["residual"], row["provider"]["proof"], verify_ledger)
            runtime_total["verification_ops"] = runtime_total.get("verification_ops", 0) + verify_ledger["verification_ops"]
        elif provider_status == "SAT":
            verify_ledger = {"verification_ops": 0}
            proof_verified = formula_satisfied(row["residual"], row["provider"]["assignment"], verify_ledger)
            runtime_total["verification_ops"] = runtime_total.get("verification_ops", 0) + verify_ledger["verification_ops"]
            residual_assignment = {str(v): row["provider"]["assignment"][v] for v in sorted(row["provider"]["assignment"])}

        rows.append(
            {
                "n": row["n"],
                "m": row["m"],
                "seed": row["seed"],
                "source_sha256": row["source_crystal"]["sha256"],
                "baseline_crystal": crystal(row["residual"]),
                "baseline_status": row["baseline_status"],
                "provider_status": provider_status,
                "provider_proof": None if row["provider"] is None else row["provider"]["proof"],
                "residual_assignment": residual_assignment,
                "proof_verified": proof_verified,
                "witness_lift_ops": row["witness_lift_ops"],
                "final_status": row["final_status"],
                "finite_semantic_audit_pass": audit_pass,
            }
        )

    all_provider_proofs_verified = all(
        row["proof_verified"] is True
        for row in rows
        if row["provider_status"] in {"SAT", "UNSAT"}
    )
    assert all_provider_proofs_verified
    assert all_terminal_audits_pass

    result = {
        "artifact_id": "PF5-PROOF-CARRYING-2SAT-SCC-V26",
        "status": "FINITE_FRESH_BLIND_PROOF_CARRYING_2SAT_AUDIT_COMPLETE",
        "feature": "BIJUNCTIVE_2SAT_SCC",
        "case_count": 32,
        "frozen_groups": [{"n":n,"m":m,"seeds":seeds} for n,m,seeds in FROZEN_GROUPS],
        "all_sources_frozen_before_provider": True,
        "all_v24_baselines_frozen_before_provider": True,
        "all_provider_outputs_frozen_before_semantic_audit": True,
        "holdout_not_conditioned_on_2sat_presence": True,
        "adaptive_extension_after_results": False,
        "uses_sat_oracle": False,
        "uses_truth_table_in_provider": False,
        "truth_table_used_only_after_provider_freeze_for_finite_audit": True,
        "uses_hephaestus_for_decision": False,
        "runtime_rule_polynomial_in_explicit_residual_size": True,
        "sat_certificate": "EXPLICIT_RESIDUAL_WITNESS_PLUS_ORIGINAL_SOURCE_LIFT",
        "unsat_certificate": "MUTUAL_IMPLICATION_PATHS_X_TO_NOT_X_AND_BACK",
        "source_manifest_sha256": source_manifest_sha256,
        "baseline_manifest_sha256": baseline_manifest_sha256,
        "provider_batch_sha256": provider_batch_sha256,
        "summary": counts,
        "rows": rows,
        "runtime_ledger": runtime_total,
        "inherited_v24_runtime_ledger": inherited_total,
        "finite_audit_ledger": audit_total,
        "all_provider_proofs_verified": all_provider_proofs_verified,
        "all_terminal_semantic_audits_pass": all_terminal_audits_pass,
        "lane_admission_scope": "2CNF_RESIDUALS_ONLY_IF_FRESH_AUDIT_PASSES",
        "universal_exact_closure": "OPEN",
        "p_vs_np": "OPEN",
    }
    result["rows_manifest_sha256"] = digest(
        [(row["seed"], row["baseline_crystal"]["sha256"], row["provider_status"], row["final_status"]) for row in rows]
    )
    result["result_sha256"] = digest({key:value for key,value in result.items() if key != "result_sha256"})
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
    print("PF5_PROOF_CARRYING_2SAT_SCC_V26 =", result["status"])
    print("SOURCE_MANIFEST_SHA256 =", result["source_manifest_sha256"])
    print("BASELINE_MANIFEST_SHA256 =", result["baseline_manifest_sha256"])
    print("PROVIDER_BATCH_SHA256 =", result["provider_batch_sha256"])
    print("SUMMARY =", result["summary"])
    print("RUNTIME_LEDGER =", result["runtime_ledger"])
    print("ROWS_MANIFEST_SHA256 =", result["rows_manifest_sha256"])
    print("P_VS_NP =", result["p_vs_np"])
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
