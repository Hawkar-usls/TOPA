#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from collections import Counter
from pathlib import Path
from typing import Any
from topa_spider_silk import make_bridge, sha

SAT_FAMILIES={
 'PROOF_TRACE','DRAT_FRAT_LRAT','BACKWARD_PROOF_TRIMMING','UNSAT_CORE','CONFLICT_GRAPH_CUT',
 'BACKDOOR_STRUCTURE','BOUNDARY_WIDTH','PROOF_COMPLEXITY'
}
DEBUG_FAMILIES={
 'DIFFERENTIAL_STATE_NARROWING','FIRST_DIVERGENCE','DELTA_DEBUGGING','CAUSE_EFFECT_CHAIN',
 'DYNAMIC_SLICING','VALIDITY_PRESERVING_PERTURBATION'
}
SAT_TERMS=(' sat ',' satisfiability ',' cnf ',' boolean ',' unsat ',' unsatisfiable ',' drat ',' frat ',' lrat ',
           ' resolution ',' clause ',' cdcl ',' qbf ',' proof ',' solver ')
DEBUG_TERMS=(' debug',' bug',' failure',' failing',' program',' software',' test ',' execution',' compiler',' trace reduction')


def norm(x: Any)->str:
    if isinstance(x,list): x=' '.join(map(str,x))
    return ' '+ ' '.join(re.findall(r'[a-z0-9]+',str(x or '').casefold())) +' '

def has_phrase(surface:str, phrase:str)->bool:
    p=' '.join(re.findall(r'[a-z0-9]+',phrase.casefold()))
    if not p:return False
    return re.search(r'(?<![a-z0-9])'+re.escape(p).replace(r'\ ',r'\s+')+r'(?![a-z0-9])',surface) is not None

def compile_families(cfg):
    return {f['id']:[a for a in f.get('aliases',[]) if a.strip()] for f in cfg.get('families',[])}

def strict_match(c, families):
    title=norm(c.get('title')); body=norm(c.get('abstract')); surf=title+' '+body
    sat_context=any(t in surf for t in SAT_TERMS)
    debug_context=any(t in surf for t in DEBUG_TERMS)
    matched=[]; details={}
    for fid,aliases in families.items():
        th=[a for a in aliases if has_phrase(title,a)]
        bh=[a for a in aliases if has_phrase(body,a)]
        if not(th or bh): continue
        # A generic graph/width term is useful for this mission only if the paper is actually SAT/proof adjacent.
        if fid in SAT_FAMILIES and not sat_context and not any(has_phrase(surf,x) for x in ('drat','frat','lrat','unsat','unsatisfiable')):
            continue
        # Cause-effect/slicing terms are too broad outside software/failure analysis.
        if fid in DEBUG_FAMILIES and fid!='DELTA_DEBUGGING' and not debug_context and not has_phrase(surf,'delta debugging'):
            continue
        matched.append(fid); details[fid]={'title_aliases':th,'body_aliases':bh[:12]}
    # Resource-accounting alone is not mission-specific enough.
    if matched==['RESOURCE_ACCOUNTING']:
        matched=[]; details={}
    score=0.0
    for fid in matched:
        x=details[fid]
        score += 2.0 if x['title_aliases'] else 1.0
        score += min(1.0,.15*len(set(x['title_aliases']+x['body_aliases'])))
    return sorted(matched),details,round(score,6)

def run(inp,cfg):
    families=compile_families(cfg); old=inp['live_arxiv'].get('candidates',[]); kept=[]; rejected=[]; counts=Counter()
    for c in old:
        fam,details,score=strict_match(c,families)
        if not fam:
            rejected.append({'arxiv_id':c.get('arxiv_id'),'title':c.get('title'),'old_families':c.get('matched_families',[])})
            continue
        x=dict(c); x['matched_families']=fam; x['match_details']=details; x['route_score']=score; x['sieve']='STRICT_WORD_BOUNDARY_AND_DOMAIN_GATE'
        counts.update(fam); kept.append(x)
    kept.sort(key=lambda x:(-x['route_score'],str(x.get('arxiv_id'))))
    inp['live_arxiv']['pre_strict_candidates_retained']=len(old)
    inp['live_arxiv']['candidates_retained']=len(kept)
    inp['live_arxiv']['family_counts_strict']=dict(sorted(counts.items()))
    inp['live_arxiv']['strict_rejected_count']=len(rejected)
    inp['live_arxiv']['strict_rejected']=rejected
    inp['live_arxiv']['candidates']=kept
    canonical=[b for b in inp.get('research_bridges',[]) if b.get('source_kind')=='CANONICAL_EXTERNAL_SOURCE']
    live=[make_bridge(c['arxiv_id'],'LIVE_ARXIV_CANDIDATE',c['matched_families'],cfg,c['route_score']) for c in kept]
    inp['research_bridges']=canonical+live
    inp['strict_sieve']={
      'status':'PASS','mode':'WORD_BOUNDARY_PLUS_DOMAIN_COMPATIBILITY','input_candidates':len(old),'retained':len(kept),'rejected':len(rejected),
      'note':'Rejected records remain discoverable in the uploaded pre-strict artifact; rejection is routing, not a claim that the paper is scientifically irrelevant.'
    }
    inp['laws']=sorted(set(inp.get('laws',[])+['SHORT_ALIAS_SUBSTRING_IS_NOT_A_PATTERN_MATCH','CROSS_DOMAIN_TERM_OVERLAP_IS_NOT_A_MISSION_BRIDGE']))
    inp.pop('semantic_sha256',None); inp['semantic_sha256']=sha(inp)
    return inp

def self_test():
    cfg={'families':[{'id':'UNSAT_CORE','aliases':['MUS','unsat core']},{'id':'CAUSE_EFFECT_CHAIN','aliases':['cause-effect chain']},{'id':'DELTA_DEBUGGING','aliases':['delta debugging']}]}
    base={'live_arxiv':{'candidates':[
      {'arxiv_id':'a','title':'Scheduling cause-effect chains','abstract':'end to end real time scheduling','matched_families':['CAUSE_EFFECT_CHAIN']},
      {'arxiv_id':'b','title':'A MUS extraction algorithm for SAT','abstract':'minimal unsatisfiable cores for CNF satisfiability','matched_families':['UNSAT_CORE']},
      {'arxiv_id':'c','title':'Delta debugging for compiler failures','abstract':'program test failure reduction','matched_families':['DELTA_DEBUGGING']}]},'research_bridges':[],'laws':[]}
    d=run(base,cfg); ids={x['arxiv_id'] for x in d['live_arxiv']['candidates']}
    assert ids=={'b','c'} and d['strict_sieve']['rejected']==1
    return {'schema':'hawkar.topa.spider.silk.strict.self_test.v1','status':'PASS','word_boundary':True,'domain_gate':True}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); sp.add_parser('self-test')
    p=sp.add_parser('refine'); p.add_argument('--input',required=True); p.add_argument('--config',required=True); p.add_argument('--out',required=True); p.add_argument('--receipt',required=True)
    a=ap.parse_args()
    if a.cmd=='self-test': print(json.dumps(self_test(),indent=2,sort_keys=True)); return 0
    d=run(json.loads(Path(a.input).read_text()),json.loads(Path(a.config).read_text()))
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    r={'schema':'hawkar.topa.spider.silk.strict.receipt.v1','status':'PASS','pre_strict':d['strict_sieve']['input_candidates'],'retained':d['strict_sieve']['retained'],'rejected':d['strict_sieve']['rejected'],'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'semantic_sha256':d['semantic_sha256'],'laws':['SHORT_ALIAS_SUBSTRING_IS_NOT_A_PATTERN_MATCH','P_VS_NP_IS_OPEN']}
    Path(a.receipt).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n'); print(json.dumps(r,indent=2,sort_keys=True)); return 0
if __name__=='__main__': raise SystemExit(main())
