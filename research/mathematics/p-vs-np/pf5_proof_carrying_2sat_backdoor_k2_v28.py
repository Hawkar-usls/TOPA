#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json

import pf5_proof_carrying_2sat_scc_v26 as v26

FROZEN_GROUPS = [
    (6, 24, list(range(918600, 918616))),
    (7, 28, list(range(918700, 918716))),
]
K_MAX = 2


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def canonical_formula(formula):
    return v26.v24.v22.v20.v18.v12.canonical_formula(formula)


def variables_of(formula):
    return v26.variables_of(formula)


def crystal(formula):
    return v26.crystal(formula)


def assignment_json(assignment):
    return {str(variable): bool(assignment[variable]) for variable in sorted(assignment)}


def add_flat(target, source, prefix):
    for key, value in source.items():
        if key == "state_bytes_peak":
            peak_key = prefix + "state_bytes_peak_max"
            target[peak_key] = max(target.get(peak_key, 0), int(value))
        else:
            out_key = prefix + key
            target[out_key] = target.get(out_key, 0) + int(value)


def discover_strong_backdoor(formula, ledger):
    variables = variables_of(formula)
    tested = 0
    for k in range(K_MAX + 1):
        for subset in itertools.combinations(variables, k):
            tested += 1
            ledger["backdoor_subsets_tested"] += 1
            chosen = set(subset)
            accepted = True
            for clause in formula:
                ledger["backdoor_clause_checks"] += 1
                remaining = 0
                for literal in clause:
                    ledger["backdoor_literal_checks"] += 1
                    if abs(literal) not in chosen:
                        remaining += 1
                if remaining > 2:
                    accepted = False
                    break
            if accepted:
                certificate = {
                    "kind": "STRONG_2SAT_BACKDOOR",
                    "k": k,
                    "variables": list(subset),
                    "tested_candidate_ordinal": tested,
                    "residual_sha256": crystal(formula)["sha256"],
                    "definition": "DELETE_BACKDOOR_VARIABLE_LITERALS_LEAVES_WIDTH_LE_2",
                }
                cert_bytes = len(
                    json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()
                )
                ledger["backdoor_certificate_bytes"] += cert_bytes
                ledger["cumulative_state_bytes"] += cert_bytes
                ledger["state_bytes_peak"] = max(ledger["state_bytes_peak"], cert_bytes)
                return list(subset), certificate
            ledger["failed_backdoor_subsets"] += 1
    return None, None


def verify_backdoor(formula, certificate, ledger):
    variables = tuple(int(v) for v in certificate["variables"])
    if tuple(sorted(variables)) != variables or len(variables) != certificate["k"]:
        return False
    if len(variables) > K_MAX or len(set(variables)) != len(variables):
        return False
    if any(variable not in variables_of(formula) for variable in variables):
        return False
    chosen = set(variables)
    for clause in formula:
        ledger["verification_ops"] += 1
        remaining = 0
        for literal in clause:
            ledger["verification_ops"] += 1
            if abs(literal) not in chosen:
                remaining += 1
        if remaining > 2:
            return False
    return certificate["residual_sha256"] == crystal(formula)["sha256"]


def simplify_branch(formula, assignment, ledger):
    kept = []
    rows = []
    for clause_index, clause in enumerate(formula):
        ledger["branch_simplification_clause_checks"] += 1
        satisfied_literal = None
        reduced = []
        for literal in clause:
            ledger["branch_simplification_literal_checks"] += 1
            variable = abs(literal)
            if variable in assignment:
                if bool(assignment[variable]) == (literal > 0):
                    satisfied_literal = int(literal)
                    break
            else:
                reduced.append(int(literal))
        if satisfied_literal is not None:
            rows.append(
                {
                    "clause_index": clause_index,
                    "source_clause": list(clause),
                    "action": "DROP_SATISFIED",
                    "satisfied_literal": satisfied_literal,
                }
            )
        else:
            reduced_tuple = tuple(reduced)
            kept.append(reduced_tuple)
            rows.append(
                {
                    "clause_index": clause_index,
                    "source_clause": list(clause),
                    "action": "KEEP_REDUCED",
                    "reduced_clause": list(reduced_tuple),
                }
            )
    branch = canonical_formula(tuple(kept))
    certificate = {
        "kind": "BACKDOOR_BRANCH_SIMPLIFICATION",
        "assignment": assignment_json(assignment),
        "source_residual_sha256": crystal(formula)["sha256"],
        "branch_sha256": crystal(branch)["sha256"],
        "rows": rows,
    }
    cert_bytes = len(
        json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()
    )
    branch_bytes = crystal(branch)["bytes"]
    ledger["branch_certificate_bytes"] += cert_bytes
    ledger["branch_state_bytes"] += branch_bytes
    ledger["cumulative_state_bytes"] += cert_bytes + branch_bytes
    ledger["state_bytes_peak"] = max(ledger["state_bytes_peak"], cert_bytes + branch_bytes)
    return branch, certificate


def verify_simplification(formula, certificate, ledger):
    assignment = {int(k): bool(v) for k, v in certificate["assignment"].items()}
    if certificate["source_residual_sha256"] != crystal(formula)["sha256"]:
        return None
    if len(certificate["rows"]) != len(formula):
        return None
    kept = []
    for expected_index, (clause, row) in enumerate(zip(formula, certificate["rows"])):
        ledger["verification_ops"] += 1
        if row["clause_index"] != expected_index or tuple(row["source_clause"]) != tuple(clause):
            return None
        satisfied = [
            int(literal)
            for literal in clause
            if abs(literal) in assignment
            and bool(assignment[abs(literal)]) == (literal > 0)
        ]
        ledger["verification_ops"] += len(clause)
        if satisfied:
            if row["action"] != "DROP_SATISFIED" or int(row["satisfied_literal"]) not in satisfied:
                return None
        else:
            reduced = tuple(
                int(literal) for literal in clause if abs(literal) not in assignment
            )
            if row["action"] != "KEEP_REDUCED" or tuple(row["reduced_clause"]) != reduced:
                return None
            kept.append(reduced)
    branch = canonical_formula(tuple(kept))
    if certificate["branch_sha256"] != crystal(branch)["sha256"]:
        return None
    return branch


def branch_terminal(branch):
    if branch == ():
        return "SAT", {"kind": "EMPTY_FORMULA_AFTER_SIMPLIFICATION"}
    empty_indices = [index for index, clause in enumerate(branch) if len(clause) == 0]
    if empty_indices:
        return "UNSAT", {
            "kind": "EMPTY_CLAUSE_AFTER_SIMPLIFICATION",
            "empty_clause_indices": empty_indices,
        }
    return None, None


def solve_branch(branch, ledger):
    terminal, proof = branch_terminal(branch)
    if terminal is not None:
        ledger["terminal_branch_certificates"] += 1
        proof_bytes = len(json.dumps(proof, sort_keys=True, separators=(",", ":")).encode())
        ledger["branch_solver_certificate_bytes"] += proof_bytes
        ledger["cumulative_state_bytes"] += proof_bytes
        ledger["state_bytes_peak"] = max(ledger["state_bytes_peak"], proof_bytes)
        return {"status": terminal, "proof": proof, "assignment": {}}, {}
    if any(len(clause) > 2 for clause in branch):
        raise AssertionError("strong backdoor produced non-2-CNF branch")
    solved, local = v26.solve_2sat(branch)
    if solved["status"] == "UNSUPPORTED_NON_2CNF":
        raise AssertionError("v26 rejected verified 2-CNF branch")
    return solved, local


def verify_terminal_branch(branch, solved, ledger):
    proof = solved["proof"]
    if solved["status"] == "SAT" and proof.get("kind") == "EMPTY_FORMULA_AFTER_SIMPLIFICATION":
        ledger["verification_ops"] += 1
        return branch == ()
    if solved["status"] == "UNSAT" and proof.get("kind") == "EMPTY_CLAUSE_AFTER_SIMPLIFICATION":
        ledger["verification_ops"] += len(branch)
        return any(len(clause) == 0 for clause in branch)
    return None


def verify_branch_solver(branch, solved, ledger):
    terminal_result = verify_terminal_branch(branch, solved, ledger)
    if terminal_result is not None:
        return terminal_result
    if solved["status"] == "SAT":
        return v26.formula_satisfied(branch, solved["assignment"], ledger)
    if solved["status"] == "UNSAT":
        return v26.verify_unsat_certificate(branch, solved["proof"], ledger)
    return False


def merge_residual_witness(residual, backdoor_assignment, branch_assignment, ledger):
    merged = {variable: False for variable in variables_of(residual)}
    ledger["witness_default_assignments"] += len(merged)
    for variable, value in backdoor_assignment.items():
        merged[int(variable)] = bool(value)
        ledger["witness_merge_ops"] += 1
    for variable, value in branch_assignment.items():
        variable = int(variable)
        if variable in backdoor_assignment and bool(backdoor_assignment[variable]) != bool(value):
            raise AssertionError("branch assignment conflicts with backdoor assignment")
        merged[variable] = bool(value)
        ledger["witness_merge_ops"] += 1
    if not v26.formula_satisfied(residual, merged, ledger):
        raise AssertionError("merged branch witness does not satisfy pre-branch residual")
    return merged


def provider_on_open(source, residual, transcript):
    ledger = {
        "backdoor_subsets_tested": 0,
        "failed_backdoor_subsets": 0,
        "backdoor_clause_checks": 0,
        "backdoor_literal_checks": 0,
        "backdoor_certificate_bytes": 0,
        "branch_count": 0,
        "branch_simplification_clause_checks": 0,
        "branch_simplification_literal_checks": 0,
        "branch_certificate_bytes": 0,
        "branch_solver_certificate_bytes": 0,
        "branch_state_bytes": 0,
        "terminal_branch_certificates": 0,
        "witness_default_assignments": 0,
        "witness_merge_ops": 0,
        "witness_lift_ops": 0,
        "witness_bytes": 0,
        "verification_ops": 0,
        "state_bytes_peak": 0,
        "cumulative_state_bytes": 0,
    }

    direct, direct_ledger = v26.solve_2sat(residual)
    if direct["status"] == "SAT":
        residual_witness = {
            variable: bool(direct["assignment"].get(variable, False))
            for variable in variables_of(residual)
        }
        if not v26.formula_satisfied(residual, residual_witness, ledger):
            raise AssertionError("direct v26 witness failed residual")
        source_witness, lift_ledger = v26.v24.lift_witness(
            source, residual, transcript, residual_witness
        )
        ledger["witness_lift_ops"] += sum(int(v) for v in lift_ledger.values())
        source_json = assignment_json(source_witness)
        ledger["witness_bytes"] += len(json.dumps(source_json,sort_keys=True,separators=(",",":")).encode())
        return {
            "status":"SAT",
            "route":"DIRECT_V26_2SAT",
            "direct_v26":direct,
            "backdoor":None,
            "branches":[],
            "residual_witness":assignment_json(residual_witness),
            "source_witness":source_json,
        }, ledger, direct_ledger, {}
    if direct["status"] == "UNSAT":
        return {
            "status":"UNSAT",
            "route":"DIRECT_V26_2SAT",
            "direct_v26":direct,
            "backdoor":None,
            "branches":[],
            "residual_witness":None,
            "source_witness":None,
        }, ledger, direct_ledger, {}
    if direct["status"] != "UNSUPPORTED_NON_2CNF":
        raise AssertionError("unexpected direct v26 status")

    backdoor, backdoor_certificate = discover_strong_backdoor(residual, ledger)
    if backdoor is None:
        return {
            "status":"OPEN_UNSUPPORTED",
            "route":"NO_BACKDOOR_K_LE_2",
            "direct_v26":direct,
            "backdoor":None,
            "branches":[],
            "residual_witness":None,
            "source_witness":None,
        }, ledger, direct_ledger, {}
    if not verify_backdoor(residual, backdoor_certificate, ledger):
        raise AssertionError("backdoor certificate failed verification")

    branch_rows = []
    branch_v26_total = {}
    for bits in itertools.product((False, True), repeat=len(backdoor)):
        assignment = dict(zip(backdoor, bits))
        ledger["branch_count"] += 1
        branch, simplification_certificate = simplify_branch(residual, assignment, ledger)
        replayed_branch = verify_simplification(residual, simplification_certificate, ledger)
        if replayed_branch != branch:
            raise AssertionError("branch simplification certificate failed replay")
        if any(len(clause) > 2 for clause in branch):
            raise AssertionError("verified strong backdoor branch wider than 2")
        solved, local_v26 = solve_branch(branch, ledger)
        add_flat(branch_v26_total, local_v26, "")
        if not verify_branch_solver(branch, solved, ledger):
            raise AssertionError("branch solver proof failed verification")
        branch_rows.append({
            "assignment":assignment_json(assignment),
            "simplification_certificate":simplification_certificate,
            "branch_crystal":crystal(branch),
            "solver_status":solved["status"],
            "solver_proof":solved["proof"],
            "solver_assignment":None if solved["assignment"] is None else assignment_json(solved["assignment"]),
        })

    sat_index = next((i for i,row in enumerate(branch_rows) if row["solver_status"] == "SAT"), None)
    if sat_index is not None:
        chosen = branch_rows[sat_index]
        backdoor_assignment = {int(k):bool(v) for k,v in chosen["assignment"].items()}
        branch_assignment = {} if chosen["solver_assignment"] is None else {int(k):bool(v) for k,v in chosen["solver_assignment"].items()}
        residual_witness = merge_residual_witness(
            residual, backdoor_assignment, branch_assignment, ledger
        )
        source_witness, lift_ledger = v26.v24.lift_witness(
            source, residual, transcript, residual_witness
        )
        ledger["witness_lift_ops"] += sum(int(v) for v in lift_ledger.values())
        if not v26.formula_satisfied(source, source_witness, ledger):
            raise AssertionError("v24-lifted backdoor witness failed source")
        residual_json = assignment_json(residual_witness)
        source_json = assignment_json(source_witness)
        ledger["witness_bytes"] += len(json.dumps(residual_json,sort_keys=True,separators=(",",":")).encode())
        ledger["witness_bytes"] += len(json.dumps(source_json,sort_keys=True,separators=(",",":")).encode())
        final_proof = {
            "kind":"STRONG_2SAT_BACKDOOR_SAT",
            "backdoor_certificate":backdoor_certificate,
            "chosen_sat_branch_index":sat_index,
            "branch_manifest_sha256":digest(branch_rows),
            "residual_witness_sha256":digest(residual_json),
            "source_witness_sha256":digest(source_json),
        }
        return {
            "status":"SAT",
            "route":"STRONG_2SAT_BACKDOOR_K_LE_2",
            "direct_v26":direct,
            "backdoor":backdoor_certificate,
            "branches":branch_rows,
            "final_proof":final_proof,
            "residual_witness":residual_json,
            "source_witness":source_json,
        }, ledger, direct_ledger, branch_v26_total

    if not all(row["solver_status"] == "UNSAT" for row in branch_rows):
        raise AssertionError("backdoor branch set contains unknown status")
    final_proof = {
        "kind":"STRONG_2SAT_BACKDOOR_UNSAT",
        "backdoor_certificate":backdoor_certificate,
        "branch_count":len(branch_rows),
        "expected_branch_count":2 ** len(backdoor),
        "branch_assignments":[row["assignment"] for row in branch_rows],
        "branch_manifest_sha256":digest(branch_rows),
    }
    if final_proof["branch_count"] != final_proof["expected_branch_count"]:
        raise AssertionError("incomplete UNSAT backdoor branch coverage")
    return {
        "status":"UNSAT",
        "route":"STRONG_2SAT_BACKDOOR_K_LE_2",
        "direct_v26":direct,
        "backdoor":backdoor_certificate,
        "branches":branch_rows,
        "final_proof":final_proof,
        "residual_witness":None,
        "source_witness":None,
    }, ledger, direct_ledger, branch_v26_total


def source_truth(source, audit_ledger):
    return v26.source_truth(source, audit_ledger)


def run():
    sources = []
    for n,m,seeds in FROZEN_GROUPS:
        for seed in seeds:
            source = canonical_formula(
                v26.v24.v22.v20.v18.v9.random_connected_3cnf(
                    seed, variable_count=n, clause_count=m
                )
            )
            sources.append({"n":n,"m":m,"seed":seed,"source":source,"source_crystal":crystal(source)})
    source_manifest_sha256 = digest(
        [(row["n"],row["m"],row["seed"],row["source_crystal"]["sha256"]) for row in sources]
    )

    baselines = []
    for row in sources:
        residual, transcript, inherited = v26.v24.exact_closure(row["source"])
        assert v26.v24.replay(row["source"], transcript) == residual
        baselines.append({**row,"residual":residual,"transcript":transcript,"inherited":inherited})
    baseline_manifest_sha256 = digest(
        [(row["seed"],crystal(row["residual"])["sha256"],v26.terminal_status(row["residual"])) for row in baselines]
    )

    frozen = []
    runtime_total = {}
    inherited_total = {"v13":{},"v15":{},"v18":{},"v20":{},"v22":{},"v24":{}}
    for row in baselines:
        for lane in inherited_total:
            add_flat(inherited_total[lane], row["inherited"][lane], "")
        baseline_status = v26.terminal_status(row["residual"])
        provider = None
        local = {}
        direct_v26_ledger = {}
        branch_v26_ledger = {}
        final_status = baseline_status
        if baseline_status == "OPEN_RESIDUAL":
            provider, local, direct_v26_ledger, branch_v26_ledger = provider_on_open(
                row["source"], row["residual"], row["transcript"]
            )
            final_status = {
                "SAT":"TRUE",
                "UNSAT":"FALSE",
                "OPEN_UNSUPPORTED":"OPEN_RESIDUAL",
            }[provider["status"]]
        add_flat(runtime_total, local, "v28_")
        add_flat(runtime_total, direct_v26_ledger, "direct_v26_")
        add_flat(runtime_total, branch_v26_ledger, "branch_v26_")
        frozen.append({
            **row,
            "baseline_status":baseline_status,
            "provider":provider,
            "final_status":final_status,
        })

    provider_batch_sha256 = digest([
        (
            row["seed"], crystal(row["residual"])["sha256"], row["baseline_status"],
            row["provider"], row["final_status"]
        ) for row in frozen
    ])

    # Post-freeze independent finite audit only.
    audit_total = {"truth_table_rows":0,"verification_ops":0}
    rows = []
    counts = {
        "cases":len(frozen),"v24_true":0,"v24_false":0,"v24_open":0,
        "direct_2sat_sat":0,"direct_2sat_unsat":0,"entered_dark_non2cnf":0,
        "backdoor_found_k0":0,"backdoor_found_k1":0,"backdoor_found_k2":0,
        "no_backdoor_k_le_2":0,"backdoor_branch_count":0,
        "backdoor_sat_cases":0,"backdoor_unsat_cases":0,
        "final_true":0,"final_false":0,"final_open":0,
    }
    all_audits_pass = True
    for row in frozen:
        counts[{"TRUE":"v24_true","FALSE":"v24_false","OPEN_RESIDUAL":"v24_open"}[row["baseline_status"]]] += 1
        provider = row["provider"]
        if provider is not None:
            if provider["route"] == "DIRECT_V26_2SAT":
                counts["direct_2sat_sat" if provider["status"] == "SAT" else "direct_2sat_unsat"] += 1
            else:
                counts["entered_dark_non2cnf"] += 1
                if provider["backdoor"] is None:
                    counts["no_backdoor_k_le_2"] += 1
                else:
                    counts[f"backdoor_found_k{provider['backdoor']['k']}"] += 1
                    counts["backdoor_branch_count"] += len(provider["branches"])
                    counts["backdoor_sat_cases" if provider["status"] == "SAT" else "backdoor_unsat_cases"] += 1
        counts[{"TRUE":"final_true","FALSE":"final_false","OPEN_RESIDUAL":"final_open"}[row["final_status"]]] += 1

        audit_pass = None
        if row["final_status"] in {"TRUE","FALSE"}:
            truth = source_truth(row["source"], audit_total)
            audit_pass = truth if row["final_status"] == "TRUE" else not truth
            all_audits_pass = all_audits_pass and audit_pass
        rows.append({
            "n":row["n"],"m":row["m"],"seed":row["seed"],
            "source_sha256":row["source_crystal"]["sha256"],
            "baseline_crystal":crystal(row["residual"]),
            "baseline_status":row["baseline_status"],
            "provider_route":None if provider is None else provider["route"],
            "provider_status":None if provider is None else provider["status"],
            "backdoor":None if provider is None else provider["backdoor"],
            "branch_count":0 if provider is None else len(provider["branches"]),
            "provider_proof_sha256":None if provider is None else digest(provider),
            "final_status":row["final_status"],
            "finite_semantic_audit_pass":audit_pass,
        })

    assert all_audits_pass
    result = {
        "artifact_id":"PF5-PROOF-CARRYING-2SAT-BACKDOOR-K2-V28",
        "status":"FINITE_FRESH_BLIND_PROOF_CARRYING_BACKDOOR_AUDIT_COMPLETE",
        "feature":"STRONG_2SAT_BACKDOOR_K_LE_2",
        "k_max":K_MAX,
        "case_count":32,
        "frozen_groups":[{"n":n,"m":m,"seeds":seeds} for n,m,seeds in FROZEN_GROUPS],
        "all_sources_frozen_before_provider":True,
        "all_v24_baselines_frozen_before_provider":True,
        "all_provider_outputs_frozen_before_semantic_audit":True,
        "holdout_not_conditioned_on_backdoor_presence":True,
        "adaptive_extension_after_results":False,
        "uses_sat_oracle":False,
        "uses_truth_table_in_provider":False,
        "truth_table_used_only_after_provider_freeze_for_finite_audit":True,
        "uses_hephaestus_for_decision":False,
        "backdoor_discovery_polynomial_for_fixed_k_max":True,
        "branch_count_bounded_by_2_pow_k_max":True,
        "all_failed_backdoor_candidates_charged":True,
        "source_manifest_sha256":source_manifest_sha256,
        "baseline_manifest_sha256":baseline_manifest_sha256,
        "provider_batch_sha256":provider_batch_sha256,
        "summary":counts,
        "rows":rows,
        "runtime_ledger":runtime_total,
        "inherited_v24_runtime_ledger":inherited_total,
        "finite_audit_ledger":audit_total,
        "all_terminal_semantic_audits_pass":all_audits_pass,
        "lane_admission_scope":"RESIDUALS_WITH_DETERMINISTIC_STRONG_2SAT_BACKDOOR_SIZE_LE_2_ONLY_IF_FRESH_AUDIT_PASSES",
        "universal_exact_closure":"OPEN",
        "p_vs_np":"OPEN",
    }
    result["rows_manifest_sha256"] = digest([
        (row["seed"],row["baseline_crystal"]["sha256"],row["provider_route"],row["provider_status"],row["final_status"])
        for row in rows
    ])
    result["result_sha256"] = digest({k:v for k,v in result.items() if k!="result_sha256"})
    return result


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--json-out"); args=parser.parse_args()
    result=run()
    if args.json_out:
        with open(args.json_out,"w",encoding="utf-8") as handle:
            json.dump(result,handle,indent=2,sort_keys=True); handle.write("\n")
    print("PF5_PROOF_CARRYING_2SAT_BACKDOOR_K2_V28 =",result["status"])
    print("SOURCE_MANIFEST_SHA256 =",result["source_manifest_sha256"])
    print("BASELINE_MANIFEST_SHA256 =",result["baseline_manifest_sha256"])
    print("PROVIDER_BATCH_SHA256 =",result["provider_batch_sha256"])
    print("SUMMARY =",result["summary"])
    print("RUNTIME_LEDGER =",result["runtime_ledger"])
    print("ROWS_MANIFEST_SHA256 =",result["rows_manifest_sha256"])
    print("P_VS_NP =",result["p_vs_np"])
    print("RESULT_SHA256 =",result["result_sha256"])

if __name__=="__main__": main()
