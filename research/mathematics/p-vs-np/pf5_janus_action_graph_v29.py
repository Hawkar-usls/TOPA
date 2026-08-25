#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter, deque

import pf5_proof_carrying_2sat_backdoor_k2_v28 as v28

MAX_POLICY_DEPTH = 2
EXPECTED_V28_RESULT_SHA256 = "830103432809de48e5b3bc268e397060501e65fc2b4d18bbb92c5691f1939328"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def canonical_formula(formula): return v28.canonical_formula(formula)
def variables_of(formula): return v28.variables_of(formula)
def crystal(formula): return v28.crystal(formula)
def add(ledger, key, value=1): ledger[key] = ledger.get(key, 0) + value


def simplify_assignment(formula, assignment, ledger):
    kept=[]
    for clause in formula:
        add(ledger,"simplify_clause_checks")
        reduced=[]; satisfied=False
        for literal in clause:
            add(ledger,"simplify_literal_checks")
            variable=abs(literal)
            if variable in assignment:
                if bool(assignment[variable]) == (literal > 0): satisfied=True; break
            else: reduced.append(int(literal))
        if not satisfied: kept.append(tuple(reduced))
    out=canonical_formula(tuple(kept)); add(ledger,"simplified_state_bytes",crystal(out)["bytes"]); return out


def incidence_components(formula, ledger):
    if not formula: return []
    if any(len(c)==0 for c in formula): return [formula]
    var_to_clauses={}
    for ci,clause in enumerate(formula):
        for literal in clause:
            add(ledger,"incidence_literal_visits")
            var_to_clauses.setdefault(abs(literal),[]).append(ci)
    unseen=set(range(len(formula))); components=[]
    while unseen:
        start=min(unseen); queue=deque([start]); clause_ids=set(); seen_vars=set()
        while queue:
            ci=queue.popleft()
            if ci in clause_ids: continue
            clause_ids.add(ci); unseen.discard(ci); add(ledger,"incidence_clause_visits")
            for literal in formula[ci]:
                variable=abs(literal)
                if variable in seen_vars: continue
                seen_vars.add(variable); add(ledger,"incidence_variable_visits")
                for other_ci in var_to_clauses.get(variable,[]):
                    if other_ci not in clause_ids: queue.append(other_ci); add(ledger,"incidence_adjacency_visits")
        components.append(canonical_formula(tuple(formula[i] for i in sorted(clause_ids))))
    components.sort(key=lambda f:(crystal(f)["sha256"],len(f))); return components


def terminal_status(formula):
    if formula == (): return "SAT"
    if any(len(c)==0 for c in formula): return "UNSAT"
    return None


def solve_2sat_leaf(formula, ledger):
    terminal=terminal_status(formula)
    if terminal is not None:
        add(ledger,"leaf_terminal"); return {"closed":True,"status":terminal,"kind":"TERMINAL","state_sha256":crystal(formula)["sha256"]}
    if any(len(c)>2 for c in formula): return None
    solved,local=v28.v26.solve_2sat(formula)
    for key,value in local.items():
        if isinstance(value,int): add(ledger,"leaf_v26_"+key,value)
    if solved["status"] not in {"SAT","UNSAT"}: raise AssertionError("verified 2-CNF leaf not closed by v26")
    add(ledger,"leaf_direct_2sat")
    return {"closed":True,"status":solved["status"],"kind":"DIRECT_2SAT","state_sha256":crystal(formula)["sha256"],"proof_sha256":digest(solved)}


def evaluate_admitted_leaf(formula, ledger):
    direct=solve_2sat_leaf(formula,ledger)
    if direct is not None: return direct
    components=incidence_components(formula,ledger)
    if len(components)<=1:
        return {"closed":False,"status":"OPEN","kind":"NO_ADMITTED_LEAF","state_sha256":crystal(formula)["sha256"],"component_count":len(components)}
    children=[]; statuses=[]
    for component in components:
        solved=solve_2sat_leaf(component,ledger)
        if solved is None:
            return {"closed":False,"status":"OPEN","kind":"COMPONENT_PRODUCT_HAS_NON_2SAT_CHILD","state_sha256":crystal(formula)["sha256"],"component_count":len(components)}
        children.append(solved); statuses.append(solved["status"])
    status="UNSAT" if "UNSAT" in statuses else "SAT"; add(ledger,"leaf_component_product")
    return {"closed":True,"status":status,"kind":"COMPONENT_PRODUCT_2SAT","state_sha256":crystal(formula)["sha256"],"component_count":len(components),"children_sha256":digest(children)}


def exact_close(formula, ledger):
    residual,transcript,runtime=v28.v26.v24.exact_closure(formula)
    if v28.v26.v24.replay(formula,transcript)!=residual: raise AssertionError("v24 branch closure replay failed")
    add(ledger,"closure_calls"); add(ledger,"closure_transcript_steps",len(transcript)); add(ledger,"closure_output_bytes",crystal(residual)["bytes"])
    for lane,values in runtime.items():
        for key,value in values.items():
            if isinstance(value,int): add(ledger,f"closure_{lane}_{key}",value)
    return residual,transcript


def resolve_state(formula, depth_remaining, ledger):
    closed,transcript=exact_close(formula,ledger); leaf=evaluate_admitted_leaf(closed,ledger)
    if leaf["closed"]:
        return {"closed":True,"status":leaf["status"],"kind":"LEAF","leaf":leaf,"closure_transcript_sha256":digest(transcript),"state_sha256":crystal(closed)["sha256"]}
    if depth_remaining==0:
        return {"closed":False,"status":"OPEN","kind":"DEPTH_EXHAUSTED","state_sha256":crystal(closed)["sha256"],"leaf_probe":leaf}
    for variable in variables_of(closed):
        add(ledger,"policy_variable_candidates"); branches=[]; accepted=True
        for value in (False,True):
            add(ledger,"policy_branch_expansions")
            child=resolve_state(simplify_assignment(closed,{variable:value},ledger),depth_remaining-1,ledger)
            branches.append({"assignment":{str(variable):value},"child":child})
            if not child["closed"]: accepted=False; break
        if accepted:
            statuses=[r["child"]["status"] for r in branches]
            return {"closed":True,"status":"SAT" if "SAT" in statuses else "UNSAT","kind":"ADAPTIVE_BRANCH","variable":variable,"branches":branches,"closure_transcript_sha256":digest(transcript),"state_sha256":crystal(closed)["sha256"]}
    return {"closed":False,"status":"OPEN","kind":"NO_POLICY_AT_DEPTH","depth_remaining":depth_remaining,"state_sha256":crystal(closed)["sha256"],"leaf_probe":leaf}


def unit_propagate(formula, initial_assignment, ledger):
    assignment=dict(initial_assignment); residual=canonical_formula(formula); trace=[]
    while True:
        simplified=[]; conflict=False
        for clause in residual:
            add(ledger,"up_clause_checks"); reduced=[]; satisfied=False
            for literal in clause:
                add(ledger,"up_literal_checks"); variable=abs(literal)
                if variable in assignment:
                    if bool(assignment[variable])==(literal>0): satisfied=True; break
                else: reduced.append(literal)
            if satisfied: continue
            if len(reduced)==0: conflict=True; break
            simplified.append(tuple(reduced))
        if conflict: return True,assignment,trace
        residual=canonical_formula(tuple(simplified))
        units=sorted({c[0] for c in residual if len(c)==1},key=lambda lit:(abs(lit),lit<0))
        if not units: return False,assignment,trace
        progressed=False
        for literal in units:
            variable=abs(literal); value=literal>0
            if variable in assignment:
                if assignment[variable]!=value: return True,assignment,trace
                continue
            assignment[variable]=value; trace.append(int(literal)); add(ledger,"up_assignments"); progressed=True
        if not progressed: return False,assignment,trace


def failed_literal_probes(formula, ledger):
    rows=[]
    for variable in variables_of(formula):
        for value in (False,True):
            add(ledger,"failed_literal_probes")
            conflict,assignment,trace=unit_propagate(formula,{variable:value},ledger)
            if conflict:
                rows.append({"assumed_literal":variable if value else -variable,"forced_literal":-variable if value else variable,"propagation_trace":trace,"assignment_sha256":digest({str(k):bool(v) for k,v in sorted(assignment.items())})})
    return rows


def blocked_clause_rows(formula, ledger):
    rows=[]
    for ci,clause in enumerate(formula):
        for literal in clause:
            add(ledger,"blocked_literal_candidates")
            parents=[(di,other) for di,other in enumerate(formula) if di!=ci and -literal in other]
            all_tautological=True
            for _,other in parents:
                add(ledger,"blocked_resolvent_checks")
                resolvent=[x for x in clause if x!=literal]+[x for x in other if x!=-literal]
                add(ledger,"blocked_resolvent_literal_visits",len(resolvent)); s=set(resolvent)
                if not any(-x in s for x in s): all_tautological=False; break
            if all_tautological:
                rows.append({"clause_index":ci,"blocking_literal":int(literal),"opposite_parent_count":len(parents)}); break
    return rows


def structural_fingerprint(formula, ledger):
    widths=Counter(len(c) for c in formula); degree=Counter(); signed={}
    for clause in formula:
        for literal in clause:
            variable=abs(literal); degree[variable]+=1; pos,neg=signed.get(variable,(0,0)); pos+=literal>0; neg+=literal<0; signed[variable]=(pos,neg); add(ledger,"fingerprint_literal_visits")
    components=incidence_components(formula,ledger)
    return {"variables":len(variables_of(formula)),"clauses":len(formula),"bytes":crystal(formula)["bytes"],"width_histogram":{str(k):widths[k] for k in sorted(widths)},"degree_multiset":sorted(degree.values()),"signed_degree_multiset":sorted([list(v) for v in signed.values()]),"incidence_component_count":len(components),"sha256":crystal(formula)["sha256"]}


def build_v28_survivors(ledger):
    survivors=[]
    for n,m,seeds in v28.FROZEN_GROUPS:
        for seed in seeds:
            source=canonical_formula(v28.v26.v24.v22.v20.v18.v9.random_connected_3cnf(seed,variable_count=n,clause_count=m))
            residual,transcript,_=v28.v26.v24.exact_closure(source)
            if v28.v26.terminal_status(residual)!="OPEN_RESIDUAL": continue
            provider,_,_,_=v28.provider_on_open(source,residual,transcript); add(ledger,"v28_provider_replays")
            if provider["status"]=="OPEN_UNSUPPORTED": survivors.append({"n":n,"m":m,"seed":seed,"source_sha256":crystal(source)["sha256"],"residual":residual,"residual_sha256":crystal(residual)["sha256"]})
    if len(survivors)!=4: raise AssertionError(f"expected 4 authoritative v28 survivors, got {len(survivors)}")
    return survivors


def run():
    ledger={}; survivors=build_v28_survivors(ledger); rows=[]
    complete={"COMPONENT_PRODUCT_2SAT_ZERO_BRANCH":0,"ADAPTIVE_ACTION_GRAPH_DEPTH_1":0,"ADAPTIVE_ACTION_GRAPH_DEPTH_2":0}
    reduction={"FAILED_LITERAL_UNIT_PROPAGATION":0,"BLOCKED_CLAUSE_AVAILABLE":0}
    for item in survivors:
        residual=item["residual"]; fingerprint=structural_fingerprint(residual,ledger)
        zero=resolve_state(residual,0,ledger); depth1=resolve_state(residual,1,ledger); depth2=resolve_state(residual,2,ledger)
        if zero["closed"] and zero["leaf"]["kind"]=="COMPONENT_PRODUCT_2SAT": complete["COMPONENT_PRODUCT_2SAT_ZERO_BRANCH"]+=1
        if depth1["closed"]: complete["ADAPTIVE_ACTION_GRAPH_DEPTH_1"]+=1
        if depth2["closed"]: complete["ADAPTIVE_ACTION_GRAPH_DEPTH_2"]+=1
        failed=failed_literal_probes(residual,ledger); blocked=blocked_clause_rows(residual,ledger)
        if failed: reduction["FAILED_LITERAL_UNIT_PROPAGATION"]+=1
        if blocked: reduction["BLOCKED_CLAUSE_AVAILABLE"]+=1
        rows.append({"n":item["n"],"m":item["m"],"seed":item["seed"],"source_sha256":item["source_sha256"],"residual_sha256":item["residual_sha256"],"fingerprint":fingerprint,"zero_plan":zero,"depth1_plan":depth1,"depth2_plan":depth2,"failed_literal_rows":failed,"blocked_clause_rows":blocked})
    ranked_complete=sorted([{"lane":lane,"survivor_coverage":coverage,"coverage_fraction":coverage/len(survivors)} for lane,coverage in complete.items()],key=lambda r:(-r["survivor_coverage"],r["lane"]))
    ranked_reduction=sorted([{"lane":lane,"survivor_signal":coverage,"signal_fraction":coverage/len(survivors)} for lane,coverage in reduction.items()],key=lambda r:(-r["survivor_signal"],r["lane"]))
    dominant=ranked_complete[0]
    next_gate="V30_FRESH_PROOF_CARRYING_ADAPTIVE_ACTION_GRAPH" if dominant["survivor_coverage"]>0 else ("V30_FRESH_PROOF_CARRYING_PREPROCESSING_SIGNAL" if ranked_reduction[0]["survivor_signal"]>0 else "V30_DARK_RESIDUAL_RELATIONAL_OBSERVER")
    result={"artifact_id":"PF5-JANUS-ACTION-GRAPH-V29","status":"POST_HOC_V28_SURVIVOR_MACHINE_POLICY_DISCOVERY_COMPLETE","role":"OBSERVER_ONLY_NO_NEW_SOURCE_SAT_AUTHORITY","source_v28_result_sha256":EXPECTED_V28_RESULT_SHA256,"survivor_count":len(survivors),"max_policy_depth_frozen_before_observation":MAX_POLICY_DEPTH,"admitted_leaf_languages":["TERMINAL","DIRECT_PROOF_CARRYING_2SAT_V26","EXACT_INCIDENCE_COMPONENT_PRODUCT_OF_V26_2SAT_LEAVES"],"action_order":["V24_EXACT_CLOSURE","ADMITTED_LEAF_TEST","LEXICOGRAPHIC_VARIABLE_BRANCH_FALSE_THEN_TRUE","RECURSE_TO_DEPTH_AT_MOST_2"],"uses_sat_oracle":False,"uses_truth_table":False,"modifies_authoritative_v28_survivors":False,"component_decomposition_theorem_reused":True,"failed_literal_and_blocked_clause_are_reduction_signals_only":True,"ranked_complete_action_frontier":ranked_complete,"ranked_reduction_signal_frontier":ranked_reduction,"dominant_complete_lane":dominant,"next_gate":next_gate,"rows":rows,"observer_cost_ledger":ledger,"rows_manifest_sha256":digest([(r["seed"],r["residual_sha256"],digest(r["depth1_plan"]),digest(r["depth2_plan"]),len(r["failed_literal_rows"]),len(r["blocked_clause_rows"])) for r in rows]),"universal_fixed_depth_policy_exists":"OPEN","universal_exact_closure":"OPEN","p_vs_np":"OPEN"}
    result["result_sha256"]=digest({k:v for k,v in result.items() if k!="result_sha256"}); return result


def main():
    p=argparse.ArgumentParser(); p.add_argument("--json-out"); a=p.parse_args(); result=run()
    if a.json_out:
        with open(a.json_out,"w",encoding="utf-8") as h: json.dump(result,h,indent=2,sort_keys=True); h.write("\n")
    print("PF5_JANUS_ACTION_GRAPH_V29 =",result["status"]); print("SURVIVOR_COUNT =",result["survivor_count"]); print("RANKED_COMPLETE_ACTION_FRONTIER =",result["ranked_complete_action_frontier"]); print("RANKED_REDUCTION_SIGNAL_FRONTIER =",result["ranked_reduction_signal_frontier"]); print("DOMINANT_COMPLETE_LANE =",result["dominant_complete_lane"]); print("NEXT_GATE =",result["next_gate"]); print("ROWS_MANIFEST_SHA256 =",result["rows_manifest_sha256"]); print("OBSERVER_COST_LEDGER =",result["observer_cost_ledger"]); print("P_VS_NP =",result["p_vs_np"]); print("RESULT_SHA256 =",result["result_sha256"])

if __name__=="__main__": main()
