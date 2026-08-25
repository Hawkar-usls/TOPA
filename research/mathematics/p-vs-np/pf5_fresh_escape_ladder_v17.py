#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_single_resolvent_exact_projection_v15 as v15
import pf5_pnp_spiral_hephaestus_crystal_v14 as v14

FROZEN_GROUPS=[
    (6,24,list(range(911600,911608))),
    (7,28,list(range(911700,911708))),
    (8,32,list(range(911800,911808))),
    (9,36,list(range(911900,911908))),
    (10,40,list(range(912000,912008))),
    (12,48,list(range(912200,912208))),
]


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def run():
    # Phase 1: freeze every source and the complete source manifest first.
    frozen=[]
    for n,m,seeds in FROZEN_GROUPS:
        for seed in seeds:
            f=v9.random_connected_3cnf(seed,variable_count=n,clause_count=m)
            frozen.append({'n':n,'m':m,'seed':seed,'source':[list(c) for c in f],'source_crystal':v14.crystal(f)})
    manifest=[(r['n'],r['m'],r['seed'],r['source_crystal']['sha256']) for r in frozen]
    source_manifest_sha256=digest(manifest)

    # Phase 2: exact theorem-only closure. No audit/score is visible here.
    rows=[]; first=None; seen={}; revisits=0
    for index,item in enumerate(frozen):
        source=tuple(tuple(c) for c in item['source'])
        residual,transcript,ledger=v15.exact_closure(source)
        rc=v14.crystal(residual)
        prior=seen.get(rc['sha256'])
        revisit=prior is not None and prior['canonical_cnf']==rc['canonical_cnf']
        if revisit: revisits+=1
        else: seen[rc['sha256']]=rc
        row={
            'ladder_index':index,'n':item['n'],'m':item['m'],'seed':item['seed'],
            'source_crystal_sha256':item['source_crystal']['sha256'],'source_bytes':item['source_crystal']['bytes'],
            'residual_crystal':rc,'revisit':revisit,
            'pure_steps':sum(e['kind']=='PURE_LITERAL' for e in transcript),
            'all_taut_steps':sum(e['kind']=='TAUTOLOGICAL_RESOLVENT' for e in transcript),
            'single_resolvent_steps':sum(e['kind']=='SINGLE_RESOLVENT' for e in transcript),
            'proof_transcript_bytes':len(json.dumps(transcript,sort_keys=True,separators=(",",":")).encode()),
            'status':'EMPTY' if rc['clauses']==0 else 'SURVIVES',
        }
        rows.append(row)
        if first is None and row['status']=='SURVIVES':
            first={**row,'source':item['source'],'transcript':transcript}

    reduction_batch_sha256=digest([(r['n'],r['m'],r['seed'],r['residual_crystal']['sha256'],r['proof_transcript_bytes']) for r in rows])

    # Phase 3: bounded exhaustive audit only after every reduction is frozen.
    audit=None
    if first is not None:
        source=tuple(tuple(c) for c in first['source'])
        residual=tuple(tuple(c) for c in first['residual_crystal']['canonical_cnf'])
        ok,ledger=v15.semantic_audit(source,residual,first['transcript'])
        if not ok: raise AssertionError('first-survivor semantic projection audit failed')
        audit={'seed':first['seed'],'n':first['n'],'m':first['m'],'pass':True,'ledger':ledger}

    result={
        'artifact_id':'PF5-FRESH-EXACT-CLOSURE-ESCAPE-LADDER-V17',
        'status':'FINITE_FROZEN_ESCAPE_LADDER_COMPLETE',
        'frozen_groups':[{'n':n,'m':m,'seeds':seeds} for n,m,seeds in FROZEN_GROUPS],
        'case_count':len(rows),'all_sources_frozen_before_reduction':True,'adaptive_extension_after_results':False,
        'source_manifest_sha256':source_manifest_sha256,'reduction_batch_sha256':reduction_batch_sha256,
        'runtime_exact_closure':['PURE_LITERAL_EXISTENTIAL_PROJECTION','TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION','SINGLE_NONTAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION'],
        'decision_heuristic':False,'uses_slime':False,'uses_sat_oracle':False,'uses_pswidth_score':False,'uses_truth_table_in_runtime':False,
        'hephaestus_role':'ACCOUNTING_RECURRENCE_ONLY_NO_DECISION_AUTHORITY',
        'rows':rows,'survivor_count':sum(r['status']=='SURVIVES' for r in rows),'first_survivor':first,
        'exact_syntactic_revisits':revisits,'first_survivor_semantic_audit':audit,
        'next_gate':'THEOREM_ONLY_ANALYSIS_OF_FIRST_FRESH_SURVIVOR' if first is not None else 'NO_SURVIVOR_IN_FROZEN_V17_LADDER',
        'universal_exact_closure':'OPEN','p_vs_np':'OPEN'
    }
    payload=json.dumps(result,sort_keys=True,separators=(",",":")).encode(); result['result_sha256']=hashlib.sha256(payload).hexdigest(); return result


def main():
    p=argparse.ArgumentParser(); p.add_argument('--json-out',type=Path); a=p.parse_args(); d=run()
    if a.json_out: a.json_out.write_text(json.dumps(d,indent=2,sort_keys=True),encoding='utf-8')
    print('PF5_FRESH_ESCAPE_LADDER_V17 =',d['status'])
    print('SOURCE_MANIFEST_SHA256 =',d['source_manifest_sha256'])
    print('REDUCTION_BATCH_SHA256 =',d['reduction_batch_sha256'])
    print('SURVIVOR_COUNT =',d['survivor_count'])
    print('FIRST_SURVIVOR =',None if d['first_survivor'] is None else (d['first_survivor']['n'],d['first_survivor']['m'],d['first_survivor']['seed']))
    if d['first_survivor'] is not None:
        print('FIRST_SURVIVOR_SHA256 =',d['first_survivor']['residual_crystal']['sha256'])
        print('FIRST_SURVIVOR_CNF =',d['first_survivor']['residual_crystal']['canonical_cnf'])
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =',d['result_sha256'])
if __name__=='__main__': main()
