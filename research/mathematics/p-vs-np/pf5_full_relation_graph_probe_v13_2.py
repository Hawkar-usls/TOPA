#!/usr/bin/env python3
"""PF5 full projected-relation graph probe v13.2.

Post-hoc only on the already-observed v13 residual gap seed 909002, at the first
wrong local choice.  v3 intentionally selected only a forest of sound pairwise
projected-clause relations so counting stayed polynomial.  This diagnostic
constructs *all* such certified pairwise relations and, using an exponential
small-instance audit counter only, checks whether the discarded cycle edges
explain the forest-cap overestimate.

No full-relation counter is proposed as a runtime algorithm here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9

SEED=909002
VARIABLE_COUNT=5
CLAUSE_COUNT=7
PREFIX=['c:0','v:1','c:1','v:2','c:3']
CHOICES=['c:2','c:5','c:6']


def import_producer(path:Path):
    spec=importlib.util.spec_from_file_location('slime_v3_full_relation_diag',path)
    if spec is None or spec.loader is None: raise RuntimeError('cannot load producer')
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module
    try: spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name,None); raise
    return module


def distinct_projected(formula,clause_indices,visible_variables):
    vals=set()
    for idx in sorted(clause_indices):
        p=frozenset(l for l in formula[idx] if abs(l) in visible_variables)
        if p: vals.add(p)
    return sorted(vals,key=lambda c:(len(c),tuple(sorted(c))))


def all_relation_edges(producer,clauses):
    edges=[]
    for i in range(len(clauses)):
        for j in range(i+1,len(clauses)):
            allowed,reasons=producer._allowed_pairs(clauses[i],clauses[j])
            if len(allowed)<4:
                edges.append({
                    'i':i,'j':j,'allowed':[list(x) for x in allowed],
                    'reasons':list(reasons),'allowed_pair_count':len(allowed),
                })
    return edges


def cycle_rank(n,edges):
    if n==0:return 0
    adj=[[] for _ in range(n)]
    for e in edges:
        adj[e['i']].append(e['j']); adj[e['j']].append(e['i'])
    seen=set(); components=0
    for root in range(n):
        if root in seen:continue
        components+=1; stack=[root]; seen.add(root)
        while stack:
            u=stack.pop()
            for w in adj[u]:
                if w not in seen:
                    seen.add(w); stack.append(w)
    return len(edges)-n+components


def count_all_relation_patterns(n,edges):
    count=0
    for bits in itertools.product((0,1),repeat=n):
        ok=True
        for e in edges:
            if [bits[e['i']],bits[e['j']]] not in e['allowed']:
                ok=False; break
        if ok: count+=1
    return count


def side_report(producer,formula,clause_indices,visible_variables):
    clauses=distinct_projected(formula,clause_indices,visible_variables)
    all_edges=all_relation_edges(producer,clauses)
    forest_raw=producer._relation_forest(clauses)
    forest=[{'i':i,'j':j,'allowed':[list(x) for x in allowed],'reasons':list(reasons),'allowed_pair_count':len(allowed)} for i,j,allowed,reasons in forest_raw]
    assignment_bound=1<<len(visible_variables)
    forest_patterns=producer._count_forest_patterns(len(clauses),forest_raw)
    full_patterns=count_all_relation_patterns(len(clauses),all_edges)
    return {
        'visible_variables':sorted(visible_variables),
        'projected_clauses':[sorted(c,key=lambda x:(abs(x),x<0)) for c in clauses],
        'all_relation_edges':all_edges,
        'forest_edges':forest,
        'discarded_edges':[e for e in all_edges if not any(e['i']==f['i'] and e['j']==f['j'] for f in forest)],
        'cycle_rank':cycle_rank(len(clauses),all_edges),
        'assignment_bound':assignment_bound,
        'forest_pattern_bound':forest_patterns,
        'full_relation_pattern_bound_audit_only':full_patterns,
        'forest_signature_cap':min(assignment_bound,forest_patterns),
        'full_relation_signature_cap_audit_only':min(assignment_bound,full_patterns),
    }


def choice_report(producer,formula,selected):
    all_c=set(range(len(formula))); all_v={abs(l) for c in formula for l in c}
    sv={int(x.split(':',1)[1]) for x in selected if x.startswith('v:')}
    sc={int(x.split(':',1)[1]) for x in selected if x.startswith('c:')}
    rv=all_v-sv
    left=side_report(producer,formula,all_c-sc,sv)
    right=side_report(producer,formula,sc,rv)
    return {
        'left':left,'right':right,
        'forest_combined_cap':max(left['forest_signature_cap'],right['forest_signature_cap']),
        'full_relation_combined_cap_audit_only':max(left['full_relation_signature_cap_audit_only'],right['full_relation_signature_cap_audit_only']),
        'max_cycle_rank':max(left['cycle_rank'],right['cycle_rank']),
    }


def run(producer,identity):
    formula=v9.random_connected_3cnf(SEED,VARIABLE_COUNT,CLAUSE_COUNT)
    rows=[]
    for choice in CHOICES:
        rows.append({'choice':choice,**choice_report(producer,formula,set(PREFIX+[choice]))})
    useful=(next(r for r in rows if r['choice']=='c:2')['full_relation_combined_cap_audit_only'] < next(r for r in rows if r['choice']=='c:5')['full_relation_combined_cap_audit_only'])
    cycle_explains=any(
        r['choice']=='c:2' and r['full_relation_combined_cap_audit_only']<r['forest_combined_cap'] and r['max_cycle_rank']>0
        for r in rows
    )
    result={
        'artifact_id':'PF5-FULL-RELATION-GRAPH-PROBE-V13.2',
        'status':'POSTHOC_DIAGNOSTIC_COMPLETE',
        'seed':SEED,
        'posthoc_not_holdout':True,
        'producer':identity,
        'prefix_before_gap':PREFIX,
        'choice_rows':rows,
        'full_relation_bound_distinguishes_c2_from_c5':useful,
        'discarded_cycle_relations_explain_some_forest_overestimate':cycle_explains,
        'full_relation_count_is_exponential_audit_only':True,
        'candidate_runtime_restriction':'ONLY_ADMIT_A_POLYNOMIALLY_COUNTABLE_RELATION_GRAPH_CLASS_SUCH_AS_FOREST_OR_CACTUS_AFTER_PROOF',
        'p_vs_np':'OPEN',
    }
    payload=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result['result_sha256']=hashlib.sha256(payload).hexdigest(); return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--producer-path',type=Path,required=True); ap.add_argument('--json-out',type=Path); a=ap.parse_args()
    raw=a.producer_path.read_bytes(); p=import_producer(a.producer_path)
    r=run(p,{'path':str(a.producer_path),'file_sha256':hashlib.sha256(raw).hexdigest(),'role':'PINNED_V3_POSTHOC_FULL_RELATION_AUDIT'})
    if a.json_out:a.json_out.write_text(json.dumps(r,indent=2,sort_keys=True),encoding='utf-8')
    print('PF5_FULL_RELATION_GRAPH_PROBE_V13_2 =',r['status'])
    for row in r['choice_rows']:
        print(row['choice'],'FOREST=',row['forest_combined_cap'],'FULL=',row['full_relation_combined_cap_audit_only'],'CYCLE_RANK=',row['max_cycle_rank'])
    print('DISTINGUISHES_C2_FROM_C5 =',r['full_relation_bound_distinguishes_c2_from_c5'])
    print('CYCLE_EXPLAINS =',r['discarded_cycle_relations_explain_some_forest_overestimate'])
    print('P_VS_NP = OPEN'); print('RESULT_SHA256 =',r['result_sha256'])

if __name__=='__main__':main()
