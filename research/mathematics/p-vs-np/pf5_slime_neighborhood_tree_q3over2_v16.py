#!/usr/bin/env python3
"""PF5 fixed q=3/2 neighborhood-tree capped STV probe v16."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import pf5_slime_balanced_branch_q1_v14 as v14
import pf5_slime_capped_pswidth_compiler_v12 as v12
import pf5_slime_neighborhood_tree_q1_v15 as v15

Q_LABEL = "3/2"
FROZEN_ROWS = [
    (10,42,912010),(10,42,912011),
    (12,50,912012),(12,50,912013),
    (14,59,912014),(14,59,912015),
]


def digest_json(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def cap_q3over2(r: int) -> int:
    """Exact ceil(sqrt(r^3)) using integer arithmetic only."""
    if r < 1:
        raise ValueError("r must be positive")
    cube = r ** 3
    root = math.isqrt(cube)
    return root if root * root == cube else root + 1


def compile_tree_with_cap(formula, tree, cap: int):
    formula=v12.canonical_formula(formula)
    nodes,postorder,preorder=v14.validate_tree(formula,tree)
    ledger=v12.WorkLedger(); forward={}; complement={}
    try:
        for node_id in postorder:
            node=nodes[node_id]
            if node["kind"]=="LEAF":
                leaf=node["leaf"]
                if leaf.startswith("v:"):
                    x=int(leaf.split(":",1)[1])
                    forward[node_id]=v12.variable_leaf_state(formula,x,cap,ledger,node_id)
                else:
                    out=set(); v12.insert_capped(out,frozenset(),cap,ledger,"FORWARD",node_id); forward[node_id]=out
            else:
                inside=v12.clause_ids_of_leaves(node["leaves"])
                forward[node_id]=v12.forward_join(forward[node["left"]],forward[node["right"]],inside,cap,ledger,node_id)
        root_comp=set(); v12.insert_capped(root_comp,frozenset(),cap,ledger,"COMPLEMENT","R"); complement["R"]=root_comp
        for node_id in preorder:
            node=nodes[node_id]
            if node["kind"]!="INTERNAL": continue
            left,right=node["left"],node["right"]
            complement[left]=v12.complement_join(forward[right],complement[node_id],v12.clause_ids_of_leaves(nodes[left]["leaves"]),cap,ledger,left)
            complement[right]=v12.complement_join(forward[left],complement[node_id],v12.clause_ids_of_leaves(nodes[right]["leaves"]),cap,ledger,right)
    except v12.StateCapExceeded as exc:
        return {
            "terminal":"OPEN_Q3OVER2_STATE_CAP",
            "q":Q_LABEL,
            "cap":cap,
            "tree_digest":digest_json(tree),
            "failure":{
                "phase":exc.phase,"node_id":exc.node_id,"depth":nodes[exc.node_id]["depth"],
                "cap":exc.cap,"distinct_states_at_refusal":len(exc.states),
                "first_cap_plus_one_signatures":[list(x) for x in exc.states],
                "partial_state_digest":digest_json(exc.states),"ledger":exc.ledger,
            },
            "claim":"Q3OVER2_CAP_SCOPED_OPEN_NOT_HARDNESS",
        }

    rows=[]; peak=0; total=0
    for node_id in preorder:
        payload=v14.state_payload(nodes[node_id],forward[node_id],complement[node_id])
        rows.append(payload); peak=max(peak,payload["forward_count"],payload["complement_count"]); total += payload["forward_count"]+payload["complement_count"]
    ledger.certificate_state_entries=total
    core={
        "formula_digest":digest_json(formula),"tree":tree,"tree_digest":digest_json(tree),
        "q":Q_LABEL,"cap":cap,"nodes":rows,"peak_ps_state":peak,"total_ps_states":total,"ledger":ledger.to_dict(),
    }
    cert=dict(core); cert["certificate_digest"]=digest_json(core)
    cert_bytes=len(json.dumps(cert,sort_keys=True,separators=(",",":")).encode())
    return {
        "terminal":"CLOSED_Q3OVER2_PSWIDTH_CAP","q":Q_LABEL,"cap":cap,"tree_digest":digest_json(tree),
        "peak_ps_state":peak,"total_ps_states":total,"pair_attempts":ledger.pair_attempts,
        "total_work_units":ledger.to_dict()["total_work_units"],"certificate_bytes":cert_bytes,"certificate":cert,
    }


def replay_q3over2(formula,result):
    if result.get("terminal")!="CLOSED_Q3OVER2_PSWIDTH_CAP": return False
    wrapped={"terminal":"CLOSED_BALANCED_PSWIDTH_CAP","certificate":result["certificate"]}
    return v14.replay_balanced_certificate(formula,wrapped)


def selection_key(result):
    return (result["peak_ps_state"],result["total_ps_states"],result["pair_attempts"],result["certificate_bytes"],result["tree_digest"])


def compile_portfolio(formula,manifest):
    r=len(v12.all_incidence_leaves(formula)); cap=cap_q3over2(r)
    attempts=[]; closed=[]; work=0
    for candidate in manifest.candidates:
        result=compile_tree_with_cap(formula,candidate.tree,cap)
        if result["terminal"]=="CLOSED_Q3OVER2_PSWIDTH_CAP":
            assert replay_q3over2(formula,result); work += result["total_work_units"]
            row={"candidate":candidate.name,"terminal":result["terminal"],"tree_digest":candidate.tree_digest,"peak_ps_state":result["peak_ps_state"],"total_ps_states":result["total_ps_states"],"pair_attempts":result["pair_attempts"],"certificate_bytes":result["certificate_bytes"],"certificate_digest":result["certificate"]["certificate_digest"],"certificate_replayed_before_discard":True,"_full":result}
            closed.append(row)
        else:
            assert result["failure"]["distinct_states_at_refusal"]==cap+1; work += result["failure"]["ledger"]["total_work_units"]
            row={"candidate":candidate.name,"terminal":result["terminal"],"tree_digest":candidate.tree_digest,"failure":result["failure"],"claim":result["claim"]}
        attempts.append(row)
    if not closed:
        return {"terminal":"OPEN_Q3OVER2_PORTFOLIO_EXHAUSTED","q":Q_LABEL,"cap":cap,"closed_candidates":0,"open_candidates":len(attempts),"compiler_work_units":work,"attempts":attempts,"claim":"CURRENT_NEIGHBORHOOD_PORTFOLIO_Q3OVER2_EXHAUSTED_NOT_HARDNESS"}
    selected=min(closed,key=lambda x:selection_key(x["_full"])); full=selected["_full"]; assert replay_q3over2(formula,full)
    selected_name=selected["candidate"]; selected_key=list(selection_key(full)); selected_cert=full["certificate"]
    for row in attempts: row.pop("_full",None)
    return {"terminal":"CLOSED_Q3OVER2_PORTFOLIO","q":Q_LABEL,"cap":cap,"closed_candidates":len(closed),"open_candidates":len(attempts)-len(closed),"compiler_work_units":work,"selected_candidate":selected_name,"selected_key":selected_key,"selected_certificate":selected_cert,"selected_certificate_replay":True,"attempts":attempts}


def run(producer_class,producer_identity):
    producer=producer_class(); frozen=[]
    for n,m,seed in FROZEN_ROWS:
        formula=v12.random_connected_3cnf(seed,n,m); manifest=producer.generate_manifest(formula); frozen.append((n,m,seed,formula,manifest))
    batch=digest_json([(n,m,seed,digest_json(formula),manifest.manifest_sha256) for n,m,seed,formula,manifest in frozen])
    results=[]; recovered=0; closed_total=0; open_total=0; gen=0; comp=0; winners={}
    for n,m,seed,formula,manifest in frozen:
        p=compile_portfolio(formula,manifest); recovered += int(p["terminal"]=="CLOSED_Q3OVER2_PORTFOLIO"); closed_total += p["closed_candidates"]; open_total += p["open_candidates"]; gen += manifest.total_generation_ops; comp += p["compiler_work_units"]
        if p.get("selected_candidate"): winners[p["selected_candidate"]]=winners.get(p["selected_candidate"],0)+1
        results.append({"n":n,"m":m,"seed":seed,"density":m/n,"formula_sha256":digest_json(formula),"manifest_sha256":manifest.manifest_sha256,"incidence_leaves":len(v12.all_incidence_leaves(formula)),"cap":p["cap"],"portfolio":p})
    out={
        "artifact_id":"PF5-SLIME-NEIGHBORHOOD-TREE-Q3OVER2-V16","status":"FINITE_FIXED_Q3OVER2_PROBE_COMPLETE","producer":producer_identity,
        "q":Q_LABEL,"cap_formula":"ceil(sqrt(r^3)) exact integer arithmetic","frozen_rows":[list(x) for x in FROZEN_ROWS],
        "all_formulas_and_manifests_frozen_before_compilation":True,"frozen_batch_sha256":batch,
        "runtime_assignment_enumeration":False,"runtime_exact_width_oracle":False,"runtime_sat_oracle":False,"runtime_cap_escalation":False,
        "results":results,"recovered_sources":recovered,"exhausted_sources":len(results)-recovered,"closed_candidates":closed_total,"open_candidates":open_total,"selected_candidate_counts":dict(sorted(winners.items())),
        "global_ledger":{"tree_generation_ops":gen,"compiler_work_units":comp,"candidate_attempts":len(results)*5},
        "terminal_interpretation":"Q3OVER2_FINITE_RECOVERY_OBSERVED" if recovered else "CURRENT_NEIGHBORHOOD_PORTFOLIO_Q3OVER2_EXHAUSTED_ON_ALL_FRESH_SOURCES",
        "universal_fixed_q_candidate_completeness":"OPEN","p_vs_np":"OPEN",
    }
    out["result_sha256"]=digest_json(out); return out


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--producer-path",type=Path,required=True); parser.add_argument("--json-out",type=Path); args=parser.parse_args()
    raw=args.producer_path.read_bytes(); module=v15.import_v5(args.producer_path)
    result=run(module.SlimeNeighborhoodClusterTreeV5,{"commit":"5a2ce5175049b59869c95d801b394f36ffdd3a4e","path":str(args.producer_path),"file_sha256":hashlib.sha256(raw).hexdigest(),"role":"UNCHANGED_Q1_NEIGHBORHOOD_TREE_PRODUCER"})
    if args.json_out: args.json_out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print("PF5_SLIME_NEIGHBORHOOD_TREE_Q3OVER2_V16 =",result["status"]); print("FROZEN_BATCH_SHA256 =",result["frozen_batch_sha256"]); print("RECOVERED_SOURCES =",result["recovered_sources"]); print("EXHAUSTED_SOURCES =",result["exhausted_sources"]); print("CLOSED_CANDIDATES =",result["closed_candidates"]); print("OPEN_CANDIDATES =",result["open_candidates"]); print("SELECTED_COUNTS =",result["selected_candidate_counts"])
    for row in result["results"]:
        p=row["portfolio"]; print("N",row["n"],"M",row["m"],"SEED",row["seed"],"R",row["incidence_leaves"],"K",row["cap"],p["terminal"],"CLOSED",p["closed_candidates"],"OPEN",p["open_candidates"],"SELECTED",p.get("selected_candidate"),"PEAK",p.get("selected_key",[None])[0])
    print("GLOBAL_LEDGER =",result["global_ledger"]); print("TERMINAL_INTERPRETATION =",result["terminal_interpretation"]); print("P_VS_NP = OPEN"); print("RESULT_SHA256 =",result["result_sha256"])


if __name__=="__main__": main()
