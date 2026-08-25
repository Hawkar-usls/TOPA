#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_single_resolvent_exact_projection_v15 as v15
import pf5_pnp_spiral_hephaestus_crystal_v14 as v14

SEEDS=list(range(907000,907016))

def run():
    rows=[]; seen={}; first=None; revisits=0
    for i,seed in enumerate(SEEDS):
        src=v9.random_connected_3cnf(seed,variable_count=5,clause_count=7)
        residual,transcript,ledger=v15.exact_closure(src)
        c=v14.crystal(residual)
        prior=seen.get(c['sha256'])
        revisit=prior is not None and prior['canonical_cnf']==c['canonical_cnf']
        if revisit: revisits+=1
        else: seen[c['sha256']]=c
        row={'spiral_index':i,'seed':seed,'crystal':c,'revisit':revisit,'v15_steps':sum(e['kind']=='SINGLE_RESOLVENT' for e in transcript),'status':'EMPTY' if c['clauses']==0 else 'SURVIVES'}
        rows.append(row)
        if first is None and row['status']=='SURVIVES': first=row
    result={
      'artifact_id':'PF5-PNP-SPIRAL-SURVIVOR-V16','status':'FINITE_REPLAY_COMPLETE',
      'parent':'data/PF5-PNP-SPIRAL-JOURNAL-V15.json','seed_order_frozen':SEEDS,
      'rows':rows,'first_survivor':first,'survivor_count':sum(r['status']=='SURVIVES' for r in rows),
      'exact_syntactic_revisits':revisits,'decision_heuristic':False,
      'do_not_repeat':['PURE_LITERAL','ALL_TAUTOLOGICAL_RESOLVENTS','SINGLE_UNIQUE_NONT AUTOLOGICAL_RESOLVENT'.replace(' ', '')],
      'next_gate':'THEOREM_ONLY_ANALYSIS_OF_FIRST_V16_SURVIVOR','p_vs_np':'OPEN'
    }
    payload=json.dumps(result,sort_keys=True,separators=(",",":")).encode(); result['result_sha256']=hashlib.sha256(payload).hexdigest(); return result

def main():
    p=argparse.ArgumentParser(); p.add_argument('--json-out',type=Path); a=p.parse_args(); d=run()
    if a.json_out: a.json_out.write_text(json.dumps(d,indent=2,sort_keys=True),encoding='utf-8')
    print('PF5_PNP_SPIRAL_SURVIVOR_V16 =',d['status'])
    print('SURVIVOR_COUNT =',d['survivor_count'])
    print('FIRST_SURVIVOR =',d['first_survivor']['seed'] if d['first_survivor'] else None)
    if d['first_survivor']:
        print('FIRST_SURVIVOR_SHA256 =',d['first_survivor']['crystal']['sha256'])
        print('FIRST_SURVIVOR_CNF =',d['first_survivor']['crystal']['canonical_cnf'])
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =',d['result_sha256'])
if __name__=='__main__': main()
