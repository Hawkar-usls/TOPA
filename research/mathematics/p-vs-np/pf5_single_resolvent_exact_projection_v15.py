#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_pure_literal_exact_projection_v12 as v12
import pf5_tautological_resolvent_projection_v13 as v13
import pf5_pnp_spiral_hephaestus_crystal_v14 as v14

DIAGNOSTIC_SEED=907004
HOLDOUT=list(range(910000,910032))
VARIABLE_COUNT=5
CLAUSE_COUNT=7


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def canon_resolvent(literals):
    return tuple(sorted(set(int(x) for x in literals)))


def taut_witness(a,b,ledger):
    sb=set(b)
    for lit in sorted(a,key=v13.literal_order):
        ledger['complement_literal_checks']+=1
        if -lit in sb:
            return lit
    return None


def discover_and_project_one(formula):
    residual=v12.canonical_formula(formula)
    ledger={
        'variable_tests':0,'failed_variable_tests':0,'clause_polarity_checks':0,
        'pair_checks':0,'complement_literal_checks':0,'non_taut_resolvent_rows':0,
        'unique_resolvent_insertions':0,'successful_projections':0,'clauses_removed':0,
        'clauses_emitted':0,'certificate_bytes':0,
    }
    for variable in v13.variables_of(residual):
        ledger['variable_tests']+=1
        pos=[]; neg=[]
        for idx,clause in enumerate(residual):
            ledger['clause_polarity_checks']+=1
            if variable in clause and -variable in clause:
                raise AssertionError('tautological source clause unsupported')
            if variable in clause: pos.append((idx,clause))
            elif -variable in clause: neg.append((idx,clause))
        if not pos or not neg:
            ledger['failed_variable_tests']+=1; continue
        pair_cert=[]; unique={}
        for pi,pc in pos:
            pb=tuple(l for l in pc if l!=variable)
            for ni,nc in neg:
                ledger['pair_checks']+=1
                nb=tuple(l for l in nc if l!=-variable)
                tw=taut_witness(pb,nb,ledger)
                if tw is not None:
                    pair_cert.append({'positive_clause_index':pi,'negative_clause_index':ni,'kind':'TAUTOLOGICAL','witness_literal':tw,'complement':-tw})
                    continue
                r=canon_resolvent(pb+nb)
                if any(-l in set(r) for l in r):
                    raise AssertionError('non-taut classification contradiction')
                ledger['non_taut_resolvent_rows']+=1
                h=digest(list(r))
                if h not in unique:
                    unique[h]=r; ledger['unique_resolvent_insertions']+=1
                pair_cert.append({'positive_clause_index':pi,'negative_clause_index':ni,'kind':'NON_TAUTOLOGICAL','resolvent':list(r),'resolvent_sha256':h})
        # v13 owns the zero-resolvent case. v15 owns exactly one unique non-tautological resolvent.
        if len(unique)!=1:
            ledger['failed_variable_tests']+=1; continue
        emitted=next(iter(unique.values()))
        kept=tuple(c for c in residual if variable not in c and -variable not in c)
        removed=[c for c in residual if variable in c or -variable in c]
        projected=kept+(emitted,)
        cert={
            'operator':'SINGLE_NONTAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION',
            'variable':variable,
            'positive_parent_count':len(pos),'negative_parent_count':len(neg),
            'cross_pair_count':len(pos)*len(neg),
            'unique_non_tautological_resolvent_count':1,
            'emitted_resolvent':list(emitted),
            'emitted_resolvent_sha256':digest(list(emitted)),
            'pair_certificates':pair_cert,
            'removed_clauses':[list(c) for c in removed],
            'residual_before_sha256':v13.digest_formula(residual),
            'residual_after_sha256':v13.digest_formula(projected),
        }
        ledger['successful_projections']=1
        ledger['clauses_removed']=len(removed)
        ledger['clauses_emitted']=1
        ledger['certificate_bytes']=len(json.dumps(cert,sort_keys=True,separators=(",",":")).encode())
        return projected,cert,ledger
    return residual,None,ledger


def replay_single(formula,certificate):
    residual,cert,_=discover_and_project_one(formula)
    if cert is None or cert!=certificate:
        raise AssertionError('single-resolvent certificate mismatch')
    return residual


def add_ledger(target,source):
    for k,v in source.items(): target[k]=target.get(k,0)+v


def exact_closure(formula):
    residual=v12.canonical_formula(formula)
    transcript=[]
    led={'v13':{},'v15':{}}
    while True:
        r13,t13,l13=v13.exact_composed_closure(residual)
        for e in t13: transcript.append(e)
        add_ledger(led['v13'],l13['pure']); add_ledger(led['v13'],l13['tr'])
        residual=r13
        r15,c15,l15=discover_and_project_one(residual)
        add_ledger(led['v15'],l15)
        if c15 is None: break
        transcript.append({'kind':'SINGLE_RESOLVENT','certificate':c15})
        residual=r15
    return residual,transcript,led


def replay(original,transcript):
    residual=v12.canonical_formula(original)
    for e in transcript:
        if e['kind']=='PURE_LITERAL':
            residual,_=v12.replay_certificate(residual,[e['certificate']])
        elif e['kind']=='TAUTOLOGICAL_RESOLVENT':
            residual=v13.replay_tr_certificate(residual,e['certificate'])
        elif e['kind']=='SINGLE_RESOLVENT':
            residual=replay_single(residual,e['certificate'])
        else: raise AssertionError('unknown transcript kind')
    return residual


def body_false(clause,removed_literal,assignment,ledger):
    for lit in clause:
        if lit==removed_literal: continue
        ledger['literal_checks']+=1
        if assignment[abs(lit)]==(lit>0): return False
    return True


def lift_witness(original,final_residual,transcript,final_assignment):
    ledger={'projection_steps_reversed':0,'removed_clause_checks':0,'literal_checks':0,'assignments_restored':0,'default_free_assignments':0}
    assignment={v:False for v in v13.variables_of(original)}
    ledger['default_free_assignments']=len(assignment)
    assignment.update({int(k):bool(v) for k,v in final_assignment.items()})
    if not v13.formula_true(final_residual,assignment,ledger): raise AssertionError('bad residual witness')
    for e in reversed(transcript):
        ledger['projection_steps_reversed']+=1
        c=e['certificate']; v=c['variable']
        if e['kind']=='PURE_LITERAL':
            assignment[v]=bool(c['witness_value']); ledger['assignments_restored']+=1; continue
        need_true=False; need_false=False
        for row in c['removed_clauses']:
            clause=tuple(row); ledger['removed_clause_checks']+=1
            if v in clause and body_false(clause,v,assignment,ledger): need_true=True
            elif -v in clause and body_false(clause,-v,assignment,ledger): need_false=True
        if need_true and need_false: raise AssertionError('projection witness conflict')
        assignment[v]=True if need_true else False
        ledger['assignments_restored']+=1
    if not v13.formula_true(original,assignment,ledger): raise AssertionError('lifted witness fails source')
    return assignment,ledger


def semantic_audit(source,residual,transcript):
    sv=v13.variables_of(source); rv=v13.variables_of(residual)
    ledger={'source_assignment_rows':0,'residual_assignment_rows':0,'literal_checks':0,'witness_lift_calls':0,'witness_lift_ops':0}
    projected=set()
    for bits in itertools.product((False,True),repeat=len(sv)):
        ledger['source_assignment_rows']+=1; a=dict(zip(sv,bits))
        if v13.formula_true(source,a,ledger): projected.add(tuple(a[v] for v in rv))
    models=set()
    for bits in itertools.product((False,True),repeat=len(rv)):
        ledger['residual_assignment_rows']+=1; a=dict(zip(rv,bits))
        if v13.formula_true(residual,a,ledger):
            models.add(bits); _,ll=lift_witness(source,residual,transcript,a); ledger['witness_lift_calls']+=1; ledger['witness_lift_ops']+=sum(ll.values())
    return projected==models,ledger


def count_kind(t,k): return sum(e['kind']==k for e in t)


def run():
    # Diagnostic first surviving Hephaestus crystal from v14.
    source=v9.random_connected_3cnf(DIAGNOSTIC_SEED,variable_count=VARIABLE_COUNT,clause_count=CLAUSE_COUNT)
    base,_,_=v13.exact_composed_closure(source)
    assert v14.crystal(base)['sha256']=='c4966d4fc14f224c3380eafb8bced50d6363975f0dd967e5d803bfcc53955132'
    one,cert,_=discover_and_project_one(base)
    assert cert is not None and cert['variable']==1 and cert['unique_non_tautological_resolvent_count']==1
    assert set(cert['emitted_resolvent'])=={-3,2,5}
    diagnostic_residual,diagnostic_transcript,_=exact_closure(source)
    assert diagnostic_residual==()
    assert replay(source,diagnostic_transcript)==diagnostic_residual
    ok,_=semantic_audit(source,diagnostic_residual,diagnostic_transcript); assert ok
    diagnostic={'seed':DIAGNOSTIC_SEED,'base_crystal':v14.crystal(base),'first_v15_certificate':cert,'final_crystal':v14.crystal(diagnostic_residual),'solved_to_empty':True}

    # Freeze sources, then baseline reductions, then v15 reductions; audit only after both are frozen.
    sources=[]
    for seed in HOLDOUT:
        f=v12.canonical_formula(v9.random_connected_3cnf(seed,variable_count=VARIABLE_COUNT,clause_count=CLAUSE_COUNT))
        sources.append((seed,f))
    source_batch_sha256=digest([(s,[list(c) for c in f]) for s,f in sources])
    frozen=[]
    for seed,f in sources:
        base,tb,lb=v13.exact_composed_closure(f)
        final,t,l=exact_closure(f)
        frozen.append({'seed':seed,'source':f,'base':base,'base_transcript':tb,'final':final,'transcript':t,'ledger':l})
    reduction_batch_sha256=digest([(r['seed'],v14.crystal(r['base'])['sha256'],v14.crystal(r['final'])['sha256'],r['transcript']) for r in frozen])

    rows=[]; audit_tot={'source_assignment_rows':0,'residual_assignment_rows':0,'literal_checks':0,'witness_lift_calls':0,'witness_lift_ops':0}
    runtime_tot={}
    for r in frozen:
        ok,al=semantic_audit(r['source'],r['final'],r['transcript']); assert ok
        add_ledger(audit_tot,al); add_ledger(runtime_tot,r['ledger']['v15'])
        bc=v14.crystal(r['base']); fc=v14.crystal(r['final'])
        steps=count_kind(r['transcript'],'SINGLE_RESOLVENT')
        rows.append({'seed':r['seed'],'v15_steps':steps,'feature_fired':steps>0,'base_crystal_sha256':bc['sha256'],'final_crystal_sha256':fc['sha256'],'base_bytes':bc['bytes'],'final_bytes':fc['bytes'],'byte_delta':bc['bytes']-fc['bytes'],'base_clauses':bc['clauses'],'final_clauses':fc['clauses'],'solved_to_empty':fc['clauses']==0,'semantic_audit_pass':True})
    fired=[x for x in rows if x['feature_fired']]
    result={
        'artifact_id':'PF5-SINGLE-RESOLVENT-EXACT-PROJECTION-V15','status':'FINITE_BLIND_EXACT_PROJECTION_AUDIT_COMPLETE',
        'feature':'SINGLE_NONTAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION','feature_is_heuristic':False,'uses_slime':False,'uses_sat_oracle':False,'uses_pswidth_score':False,'uses_truth_table_in_runtime':False,
        'hephaestus_crystal_role':'ACCOUNTING_RECURRENCE_ONLY_NO_DECISION_AUTHORITY','diagnostic':diagnostic,
        'holdout_seeds_frozen_before_provider_run':HOLDOUT,'holdout_not_conditioned_on_feature_presence':True,'source_batch_sha256':source_batch_sha256,'reduction_batch_sha256':reduction_batch_sha256,'all_reductions_frozen_before_semantic_audit':True,
        'summary':{'cases':len(rows),'feature_fired_cases':len(fired),'feature_noop_cases':len(rows)-len(fired),'total_v15_steps':sum(x['v15_steps'] for x in rows),'solved_to_empty_cases':sum(x['solved_to_empty'] for x in rows),'positive_byte_delta_cases':sum(x['byte_delta']>0 for x in rows),'mean_base_crystal_bytes':sum(x['base_bytes'] for x in rows)/len(rows),'mean_final_crystal_bytes':sum(x['final_bytes'] for x in rows)/len(rows),'all_semantic_audits_pass':all(x['semantic_audit_pass'] for x in rows)},
        'rows':rows,'runtime_discovery_ledger':runtime_tot,'finite_semantic_audit_ledger':audit_tot,
        'runtime_rule_polynomial_in_explicit_residual_size':True,'witness_lift_replayable_from_certificate':True,
        'next_gate':'FIRST_RESIDUAL_SURVIVING_V12_V13_V15','p_vs_np':'OPEN'
    }
    payload=json.dumps(result,sort_keys=True,separators=(",",":")).encode(); result['result_sha256']=hashlib.sha256(payload).hexdigest(); return result


def main():
    p=argparse.ArgumentParser(); p.add_argument('--json-out',type=Path); a=p.parse_args(); d=run()
    if a.json_out: a.json_out.write_text(json.dumps(d,indent=2,sort_keys=True),encoding='utf-8')
    print('PF5_SINGLE_RESOLVENT_V15 =',d['status'])
    print('SOURCE_BATCH_SHA256 =',d['source_batch_sha256'])
    print('REDUCTION_BATCH_SHA256 =',d['reduction_batch_sha256'])
    print('SUMMARY =',d['summary'])
    print('RUNTIME_LEDGER =',d['runtime_discovery_ledger'])
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =',d['result_sha256'])
if __name__=='__main__': main()
