#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter

import pf5_proof_carrying_2sat_scc_v26 as v26

K_MAX = 2
LANES = [
    "STRONG_2SAT_BACKDOOR_K_LE_1",
    "STRONG_2SAT_BACKDOOR_K_LE_2",
    "RENAMABLE_HORN",
    "RENAMABLE_DUAL_HORN",
]


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def vars_of(formula):
    return v26.variables_of(formula)


def crystal(formula):
    return v26.crystal(formula)


def add_ledger(target, source, prefix=""):
    for key, value in source.items():
        target[prefix + key] = target.get(prefix + key, 0) + int(value)


def strong_2sat_backdoor(formula, ledger):
    variables = vars_of(formula)
    for k in range(K_MAX + 1):
        for subset in itertools.combinations(variables, k):
            ledger["backdoor_subsets_tested"] += 1
            chosen = set(subset)
            ok = True
            for clause in formula:
                ledger["backdoor_clause_checks"] += 1
                remaining = 0
                for literal in clause:
                    ledger["backdoor_literal_checks"] += 1
                    if abs(literal) not in chosen:
                        remaining += 1
                if remaining > 2:
                    ok = False
                    break
            if ok:
                return list(subset)
    return None


def renaming_constraints(formula, dual=False, ledger=None):
    constraints = []
    for clause in formula:
        for left_index in range(len(clause)):
            for right_index in range(left_index + 1, len(clause)):
                left = int(clause[left_index])
                right = int(clause[right_index])
                if ledger is not None:
                    ledger["renaming_pair_constraints"] += 1
                if dual:
                    constraints.append((-left, -right))
                else:
                    constraints.append((left, right))
    return v26.v24.v22.v20.v18.v12.canonical_formula(tuple(constraints))


def verify_renaming(formula, assignment, dual, ledger):
    for clause in formula:
        positive_after = 0
        negative_after = 0
        for literal in clause:
            ledger["renaming_verify_literal_checks"] += 1
            flip = bool(assignment.get(abs(literal), False))
            is_positive_after = (literal > 0) != flip
            positive_after += int(is_positive_after)
            negative_after += int(not is_positive_after)
        if dual:
            if negative_after > 1:
                return False
        else:
            if positive_after > 1:
                return False
    return True


def recognize_renamable(formula, dual, ledger):
    constraints = renaming_constraints(formula, dual=dual, ledger=ledger)
    solved, local = v26.solve_2sat(constraints)
    add_ledger(ledger, local, prefix="renaming_2sat_")
    if solved["status"] != "SAT":
        return None, solved["status"], crystal(constraints)["sha256"]
    assignment = {int(variable): bool(value) for variable, value in solved["assignment"].items()}
    for variable in vars_of(formula):
        assignment.setdefault(variable, False)
    if not verify_renaming(formula, assignment, dual=dual, ledger=ledger):
        raise AssertionError("renaming witness failed class verification")
    return assignment, "SAT", crystal(constraints)["sha256"]


def pressure_map(formula, ledger):
    wide = [clause for clause in formula if len(clause) > 2]
    pressure = Counter()
    for clause in wide:
        seen = set()
        for literal in clause:
            ledger["pressure_literal_visits"] += 1
            variable = abs(literal)
            if variable not in seen:
                pressure[variable] += 1
                seen.add(variable)
    return wide, pressure


def profile(formula, n, m, seed, ledger):
    wide, pressure = pressure_map(formula, ledger)
    backdoor = strong_2sat_backdoor(formula, ledger)
    horn_assignment, horn_status, horn_constraints_sha = recognize_renamable(formula, False, ledger)
    dual_assignment, dual_status, dual_constraints_sha = recognize_renamable(formula, True, ledger)

    actions = []
    if backdoor is not None and len(backdoor) <= 1:
        actions.append("STRONG_2SAT_BACKDOOR_K_LE_1")
    if backdoor is not None and len(backdoor) <= 2:
        actions.append("STRONG_2SAT_BACKDOOR_K_LE_2")
    if horn_assignment is not None:
        actions.append("RENAMABLE_HORN")
    if dual_assignment is not None:
        actions.append("RENAMABLE_DUAL_HORN")

    return {
        "n":n,"m":m,"seed":seed,
        "residual_crystal":crystal(formula),
        "variable_count":len(vars_of(formula)),
        "clause_count":len(formula),
        "max_clause_width":max(len(clause) for clause in formula),
        "wide_clause_count":len(wide),
        "wide_clause_variable_sets":[sorted({abs(lit) for lit in clause}) for clause in wide],
        "wide_clause_pressure":[{"variable":v,"hits":pressure[v]} for v in sorted(pressure,key=lambda v:(-pressure[v],v))],
        "strong_2sat_backdoor_k_max":K_MAX,
        "strong_2sat_backdoor":backdoor,
        "renamable_horn":horn_assignment is not None,
        "renamable_horn_flip_assignment":None if horn_assignment is None else {str(v):horn_assignment[v] for v in sorted(horn_assignment)},
        "renamable_horn_constraint_sha256":horn_constraints_sha,
        "renamable_horn_constraint_status":horn_status,
        "renamable_dual_horn":dual_assignment is not None,
        "renamable_dual_horn_flip_assignment":None if dual_assignment is None else {str(v):dual_assignment[v] for v in sorted(dual_assignment)},
        "renamable_dual_horn_constraint_sha256":dual_constraints_sha,
        "renamable_dual_horn_constraint_status":dual_status,
        "actionable_frontier":actions,
    }


def run():
    ledger = {
        "backdoor_subsets_tested":0,"backdoor_clause_checks":0,"backdoor_literal_checks":0,
        "renaming_pair_constraints":0,"renaming_verify_literal_checks":0,"pressure_literal_visits":0,
    }
    dark_rows = []
    v26_counts = Counter()

    for n,m,seeds in v26.FROZEN_GROUPS:
        for seed in seeds:
            source = v26.v24.v22.v20.v18.v12.canonical_formula(
                v26.v24.v22.v20.v18.v9.random_connected_3cnf(seed,variable_count=n,clause_count=m)
            )
            residual, transcript, _ = v26.v24.exact_closure(source)
            assert v26.v24.replay(source, transcript) == residual
            baseline_status = v26.terminal_status(residual)
            if baseline_status != "OPEN_RESIDUAL":
                v26_counts[baseline_status] += 1
                continue
            solved, local = v26.solve_2sat(residual)
            add_ledger(ledger, local, prefix="v26_replay_")
            if solved["status"] == "SAT":
                v26_counts["TRUE_BY_2SAT"] += 1
            elif solved["status"] == "UNSAT":
                v26_counts["FALSE_BY_2SAT"] += 1
            elif solved["status"] == "UNSUPPORTED_NON_2CNF":
                v26_counts["DARK_OPEN"] += 1
                dark_rows.append(profile(residual,n,m,seed,ledger))
            else:
                raise AssertionError("unexpected v26 status")

    assert len(dark_rows) == 9
    coverage = {lane:0 for lane in LANES}
    for row in dark_rows:
        for lane in row["actionable_frontier"]:
            coverage[lane] += 1

    priority = {lane:index for index,lane in enumerate(LANES)}
    ranked = sorted(
        [{"lane":lane,"dark_coverage":count,"coverage_fraction":count/len(dark_rows)} for lane,count in coverage.items()],
        key=lambda item:(-item["dark_coverage"],priority[item["lane"]]),
    )
    dominant = ranked[0]["lane"] if ranked and ranked[0]["dark_coverage"] > 0 else None
    next_gate = {
        "STRONG_2SAT_BACKDOOR_K_LE_1":"V28_FRESH_PROOF_CARRYING_2SAT_BACKDOOR_K1",
        "STRONG_2SAT_BACKDOOR_K_LE_2":"V28_FRESH_PROOF_CARRYING_2SAT_BACKDOOR_K2",
        "RENAMABLE_HORN":"V28_FRESH_PROOF_CARRYING_RENAMABLE_HORN",
        "RENAMABLE_DUAL_HORN":"V28_FRESH_PROOF_CARRYING_RENAMABLE_DUAL_HORN",
        None:"V28_CONNECTED_BOUNDARY_ADHESION_OBSERVER",
    }[dominant]

    result = {
        "artifact_id":"PF5-DARK-RESIDUAL-STRUCTURE-MINER-V27",
        "status":"POST_HOC_DARK_RESIDUAL_MACHINE_DISCOVERY_COMPLETE",
        "role":"OBSERVER_ONLY_NO_SOURCE_SAT_DECISION",
        "source_v26_result_sha256":"b3b1d9361bc109ccc1454fa38f0f7fd87439b5db4f31a790f4391206b80ae498",
        "dark_residual_count":len(dark_rows),
        "k_max_frozen_before_observation":K_MAX,
        "modifies_dark_residual":False,
        "uses_sat_oracle":False,
        "uses_truth_table":False,
        "renamable_class_recognition_uses_proof_carrying_v26_2sat":True,
        "rows":dark_rows,
        "ranked_actionable_frontier":ranked,
        "dominant_actionable_lane":dominant,
        "next_gate":next_gate,
        "observer_cost_ledger":ledger,
        "fresh_holdout_required_before_lane_admission":True,
        "universal_exact_closure":"OPEN",
        "p_vs_np":"OPEN",
    }
    result["rows_manifest_sha256"] = digest([(row["seed"],row["residual_crystal"]["sha256"],row["actionable_frontier"]) for row in dark_rows])
    result["result_sha256"] = digest({k:v for k,v in result.items() if k!="result_sha256"})
    return result


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--json-out"); args=parser.parse_args()
    result=run()
    if args.json_out:
        with open(args.json_out,"w",encoding="utf-8") as handle:
            json.dump(result,handle,indent=2,sort_keys=True); handle.write("\n")
    print("PF5_DARK_RESIDUAL_STRUCTURE_MINER_V27 =",result["status"])
    print("DARK_RESIDUAL_COUNT =",result["dark_residual_count"])
    print("RANKED_ACTIONABLE_FRONTIER =",result["ranked_actionable_frontier"])
    print("DOMINANT_ACTIONABLE_LANE =",result["dominant_actionable_lane"])
    print("NEXT_GATE =",result["next_gate"])
    print("ROWS_MANIFEST_SHA256 =",result["rows_manifest_sha256"])
    print("OBSERVER_COST_LEDGER =",result["observer_cost_ledger"])
    print("P_VS_NP =",result["p_vs_np"])
    print("RESULT_SHA256 =",result["result_sha256"])

if __name__=="__main__": main()
