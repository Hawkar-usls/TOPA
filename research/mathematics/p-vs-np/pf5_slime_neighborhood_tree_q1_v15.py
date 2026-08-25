#!/usr/bin/env python3
"""PF5 Slime source-driven neighborhood-tree q=1 fresh probe v15."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pf5_slime_balanced_branch_q1_v14 as v14
import pf5_slime_capped_pswidth_compiler_v12 as v12

FROZEN_Q = 1
FROZEN_ROWS = [
    (10,42,911010),(10,42,911011),
    (12,50,911012),(12,50,911013),
    (14,59,911014),(14,59,911015),
    (16,67,911016),(16,67,911017),
    (18,76,911018),(18,76,911019),
    (20,84,911020),(20,84,911021),
]


def digest_json(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def import_v5(path: Path):
    import importlib.util
    spec=importlib.util.spec_from_file_location("janus_slime_neighborhood_cluster_tree_v5_pin",path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Slime v5")
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


def key(result):
    return (
        result["peak_ps_state"], result["total_ps_states"],
        result["pair_attempts"], result["certificate_bytes"], result["tree_digest"]
    )


def compile_portfolio(formula, manifest):
    attempts=[]; closed=[]; work=0
    for candidate in manifest.candidates:
        result=v14.compile_balanced_tree(formula,candidate.tree,q=FROZEN_Q)
        if result["terminal"]=="CLOSED_BALANCED_PSWIDTH_CAP":
            assert v14.replay_balanced_certificate(formula,result)
            work += result["total_work_units"]
            row={
                "candidate":candidate.name,
                "generation_ops":candidate.generation_ops,
                "tree_digest":candidate.tree_digest,
                "terminal":"CLOSED_NEIGHBORHOOD_PSWIDTH_CAP",
                "peak_ps_state":result["peak_ps_state"],
                "total_ps_states":result["total_ps_states"],
                "pair_attempts":result["pair_attempts"],
                "certificate_bytes":result["certificate_bytes"],
                "certificate_digest":result["certificate"]["certificate_digest"],
                "certificate_replayed_before_discard":True,
                "_full":result,
            }
            closed.append(row)
        else:
            assert result["terminal"]=="OPEN_BALANCED_STATE_CAP"
            assert result["failure"]["distinct_states_at_refusal"]==result["cap"]+1
            work += result["failure"]["ledger"]["total_work_units"]
            row={
                "candidate":candidate.name,
                "generation_ops":candidate.generation_ops,
                "tree_digest":candidate.tree_digest,
                "terminal":"OPEN_NEIGHBORHOOD_STATE_CAP",
                "failure":result["failure"],
                "claim":"NEIGHBORHOOD_TREE_Q1_CAP_SCOPED_OPEN_NOT_HARDNESS",
            }
        attempts.append(row)

    cap=max(2,len(v12.all_incidence_leaves(formula)))
    if not closed:
        phase_counts={}
        depth_counts={}
        for row in attempts:
            phase=row["failure"]["phase"]
            depth=row["failure"]["depth"]
            phase_counts[phase]=phase_counts.get(phase,0)+1
            depth_counts[str(depth)]=depth_counts.get(str(depth),0)+1
        return {
            "terminal":"OPEN_NEIGHBORHOOD_PORTFOLIO_Q1_EXHAUSTED",
            "cap":cap,
            "closed_candidates":0,
            "open_candidates":len(attempts),
            "compiler_work_units":work,
            "failure_phase_counts":phase_counts,
            "failure_depth_counts":depth_counts,
            "attempts":attempts,
            "claim":"CURRENT_FIVE_NEIGHBORHOOD_TREE_HEURISTICS_Q1_EXHAUSTED_NOT_HARDNESS",
        }

    selected=min(closed,key=lambda row:key(row["_full"]))
    selected_full=selected["_full"]
    assert v14.replay_balanced_certificate(formula,selected_full)
    selected_name=selected["candidate"]
    selected_key=list(key(selected_full))
    selected_certificate=selected_full["certificate"]
    for row in attempts:
        row.pop("_full",None)
    return {
        "terminal":"CLOSED_NEIGHBORHOOD_PORTFOLIO_Q1",
        "cap":cap,
        "closed_candidates":len(closed),
        "open_candidates":len(attempts)-len(closed),
        "compiler_work_units":work,
        "selected_candidate":selected_name,
        "selected_key":selected_key,
        "selected_certificate":selected_certificate,
        "selected_certificate_replay":True,
        "attempts":attempts,
    }


def run(producer_class,producer_identity):
    producer=producer_class()
    frozen=[]
    for n,m,seed in FROZEN_ROWS:
        formula=v12.random_connected_3cnf(seed,n,m)
        manifest=producer.generate_manifest(formula)
        frozen.append((n,m,seed,formula,manifest))
    batch_sha=digest_json([
        (n,m,seed,digest_json(formula),manifest.manifest_sha256)
        for n,m,seed,formula,manifest in frozen
    ])

    results=[]; recovered=0; closed_total=0; open_total=0
    gen_total=0; comp_total=0; winner_counts={}
    for n,m,seed,formula,manifest in frozen:
        p=compile_portfolio(formula,manifest)
        recovered += int(p["terminal"]=="CLOSED_NEIGHBORHOOD_PORTFOLIO_Q1")
        closed_total += p["closed_candidates"]
        open_total += p["open_candidates"]
        gen_total += manifest.total_generation_ops
        comp_total += p["compiler_work_units"]
        if p.get("selected_candidate"):
            winner_counts[p["selected_candidate"]]=winner_counts.get(p["selected_candidate"],0)+1
        results.append({
            "n":n,"m":m,"density":m/n,"seed":seed,
            "formula_sha256":digest_json(formula),
            "manifest_sha256":manifest.manifest_sha256,
            "incidence_leaves":len(v12.all_incidence_leaves(formula)),
            "portfolio":p,
        })

    interpretation=(
        "SOURCE_DRIVEN_NONCONTIGUOUS_TREE_RECOVERS_Q1_ON_FINITE_CONTROL"
        if recovered else
        "CURRENT_FIVE_NEIGHBORHOOD_TREE_HEURISTICS_Q1_EXHAUSTED_ON_FRESH_DENSE_LADDER"
    )
    out={
        "artifact_id":"PF5-SLIME-NEIGHBORHOOD-TREE-Q1-V15",
        "status":"FINITE_SOURCE_DRIVEN_TREE_PROBE_COMPLETE",
        "producer":producer_identity,
        "q":FROZEN_Q,
        "frozen_rows":[list(x) for x in FROZEN_ROWS],
        "all_formulas_and_tree_manifests_frozen_before_compilation":True,
        "frozen_batch_sha256":batch_sha,
        "runtime_assignment_enumeration":False,
        "runtime_exact_width_oracle":False,
        "runtime_sat_oracle":False,
        "results":results,
        "recovered_sources":recovered,
        "exhausted_sources":len(results)-recovered,
        "closed_candidates":closed_total,
        "open_candidates":open_total,
        "selected_candidate_counts":dict(sorted(winner_counts.items())),
        "global_ledger":{
            "tree_generation_ops":gen_total,
            "compiler_work_units":comp_total,
            "candidate_attempts":len(results)*5,
        },
        "terminal_interpretation":interpretation,
        "arbitrary_binary_tree_q1_completeness":"OPEN",
        "some_fixed_q_completeness":"OPEN",
        "p_vs_np":"OPEN",
    }
    out["result_sha256"]=digest_json(out)
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--producer-path",type=Path,required=True)
    parser.add_argument("--json-out",type=Path)
    args=parser.parse_args()
    raw=args.producer_path.read_bytes()
    module=import_v5(args.producer_path)
    result=run(module.SlimeNeighborhoodClusterTreeV5,{
        "commit":"5a2ce5175049b59869c95d801b394f36ffdd3a4e",
        "path":str(args.producer_path),
        "file_sha256":hashlib.sha256(raw).hexdigest(),
        "role":"PINNED_SOURCE_DRIVEN_NONCONTIGUOUS_TREE_PRODUCER",
    })
    if args.json_out:
        args.json_out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print("PF5_SLIME_NEIGHBORHOOD_TREE_Q1_V15 =",result["status"])
    print("FROZEN_BATCH_SHA256 =",result["frozen_batch_sha256"])
    print("RECOVERED_SOURCES =",result["recovered_sources"])
    print("EXHAUSTED_SOURCES =",result["exhausted_sources"])
    print("CLOSED_CANDIDATES =",result["closed_candidates"])
    print("OPEN_CANDIDATES =",result["open_candidates"])
    print("SELECTED_COUNTS =",result["selected_candidate_counts"])
    for row in result["results"]:
        p=row["portfolio"]
        print("N",row["n"],"M",row["m"],"SEED",row["seed"],p["terminal"],"CAP",p["cap"],"CLOSED",p["closed_candidates"],"OPEN",p["open_candidates"],"SELECTED",p.get("selected_candidate"),"PEAK",p.get("selected_key",[None])[0],"PHASES",p.get("failure_phase_counts"))
    print("TERMINAL_INTERPRETATION =",result["terminal_interpretation"])
    print("GLOBAL_LEDGER =",result["global_ledger"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =",result["result_sha256"])


if __name__=="__main__":
    main()
