#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_tautological_resolvent_projection_v13 as v13

SEEDS=list(range(907000,907016))
VARIABLE_COUNT=5
CLAUSE_COUNT=7


def lit_key(lit:int):
    return (abs(lit), lit < 0)


def canonical_cnf(formula):
    clauses=[]
    for clause in formula:
        clauses.append(tuple(sorted((int(x) for x in clause), key=lit_key)))
    return tuple(sorted(clauses))


def crystal(formula):
    canon=canonical_cnf(formula)
    payload=json.dumps([list(c) for c in canon],separators=(",",":"),sort_keys=False).encode()
    variables=sorted({abs(l) for c in canon for l in c})
    return {
        "schema":"janus.pnp.hephaestus.crystal.v1",
        "canonical_cnf":[list(c) for c in canon],
        "sha256":hashlib.sha256(payload).hexdigest(),
        "bytes":len(payload),
        "variables":len(variables),
        "clauses":len(canon),
        "literal_occurrences":sum(len(c) for c in canon),
        "identity_claim":"CANONICAL_SYNTACTIC_IDENTITY_ONLY",
    }


def transcript_bytes(transcript):
    return len(json.dumps(transcript,sort_keys=True,separators=(",",":")).encode())


def run():
    rows=[]
    seen={}
    first_survivor=None
    total_state_bytes=0
    total_proof_bytes=0
    total_revisits=0

    for spiral_index,seed in enumerate(SEEDS):
        source=v9.random_connected_3cnf(seed,variable_count=VARIABLE_COUNT,clause_count=CLAUSE_COUNT)
        residual,transcript,ledger=v13.exact_composed_closure(source)
        sc=crystal(source)
        rc=crystal(residual)
        proof_b=transcript_bytes(transcript)
        total_state_bytes += sc["bytes"] + rc["bytes"]
        total_proof_bytes += proof_b
        prior=seen.get(rc["sha256"])
        revisit=prior is not None and prior["canonical_cnf"]==rc["canonical_cnf"]
        if revisit:
            total_revisits += 1
        else:
            seen[rc["sha256"]]=rc
        pure=sum(x["kind"]=="PURE_LITERAL" for x in transcript)
        tr=sum(x["kind"]=="TAUTOLOGICAL_RESOLVENT" for x in transcript)
        status="SOLVED_EMPTY" if rc["clauses"]==0 else "SURVIVES_EXACT_CLOSURE"
        row={
            "spiral_index":spiral_index,
            "seed":seed,
            "input_crystal":sc,
            "exact_rules_applied":{"pure_literal_steps":pure,"tautological_resolvent_steps":tr},
            "proof_transcript_bytes":proof_b,
            "output_crystal":rc,
            "revisit":revisit,
            "status":status,
            "runtime_ledger":ledger,
            "closed_gates":["V12_PURE_LITERAL_FIXED_POINT","V13_TAUTOLOGICAL_RESOLVENT_FIXED_POINT"],
            "open_gate":None if status=="SOLVED_EMPTY" else "NEXT_THEOREM_ONLY_EXACT_REDUCTION",
            "do_not_repeat":["PURE_LITERAL","ALL_RESOLVENTS_TAUTOLOGICAL"] if status!="SOLVED_EMPTY" else [],
        }
        rows.append(row)
        if first_survivor is None and status=="SURVIVES_EXACT_CLOSURE":
            first_survivor={
                "seed":seed,
                "spiral_index":spiral_index,
                "source_crystal_sha256":sc["sha256"],
                "residual_crystal":rc,
                "transcript":[x for x in transcript],
            }

    source_batch=hashlib.sha256(json.dumps([(r["seed"],r["input_crystal"]["sha256"]) for r in rows],separators=(",",":"),sort_keys=True).encode()).hexdigest()
    result={
        "artifact_id":"PF5-PNP-SPIRAL-HEPHAESTUS-CRYSTAL-V14",
        "status":"FINITE_SPIRAL_REPLAY_COMPLETE",
        "branch":"pnp-spiral-hephaestus-crystal-v14",
        "hephaestus_role":"EXACT_SYNTACTIC_CRYSTALLIZER_RECURRENCE_GUARD_COST_ACCOUNTANT",
        "historical_claim_boundary":"HEPHAESTUS_CRYSTAL_STORAGE_METRICS_ARE_NOT_P_VS_NP_EVIDENCE",
        "heuristic_decision_logic":False,
        "uses_sat_oracle":False,
        "uses_pswidth_score":False,
        "uses_truth_table":False,
        "uses_slime":False,
        "seed_order_frozen":SEEDS,
        "source_batch_sha256":source_batch,
        "rows":rows,
        "first_surviving_obstruction":first_survivor,
        "global_ledger":{"state_bytes":total_state_bytes,"proof_bytes":total_proof_bytes,"exact_syntactic_revisits":total_revisits},
        "spiral_law":"INPUT_TO_EXACT_RULES_TO_OUTPUT_CRYSTAL_TO_NEW_FACT_TO_OPEN_GATE",
        "hash_semantics":"HASH_EQUALITY_ONLY_SUPPORTS_CANONICAL_SYNTACTIC_IDENTITY",
        "next_gate":"ANALYZE_FIRST_SURVIVING_CRYSTAL_FOR_THEOREM_ONLY_EXACT_REDUCTION",
        "p_vs_np":"OPEN",
    }
    payload=json.dumps(result,sort_keys=True,separators=(",",":")).encode()
    result["result_sha256"]=hashlib.sha256(payload).hexdigest()
    return result


def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--json-out',type=Path); a=p.parse_args()
    result=run()
    if a.json_out:
        a.json_out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    print('PF5_PNP_SPIRAL_HEPHAESTUS_V14 =',result['status'])
    print('FIRST_SURVIVOR =',result['first_surviving_obstruction']['seed'] if result['first_surviving_obstruction'] else None)
    if result['first_surviving_obstruction']:
        r=result['first_surviving_obstruction']['residual_crystal']
        print('FIRST_SURVIVOR_CRYSTAL_SHA256 =',r['sha256'])
        print('FIRST_SURVIVOR_CNF =',r['canonical_cnf'])
    print('GLOBAL_LEDGER =',result['global_ledger'])
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =',result['result_sha256'])

if __name__=='__main__': main()
