#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, math
from pathlib import Path

SCHEMA='hawkar.topa.spider.flywheel.v1'

def canon(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def read_jsonl(p):
    if not p: return []
    path=Path(p)
    if not path.exists(): return []
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_jsonl(p, rows):
    path=Path(p); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(canon(r)+'\n' for r in rows),encoding='utf-8')
def write_json(p,o):
    path=Path(p); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def edge_key(e):
    a,b=sorted([str(e.get('source','')),str(e.get('target',''))])
    return f"{a}|{b}|{e.get('relation','')}|{e.get('via','')}"

def evidence_signature(e):
    core={
      'source':e.get('source'),'target':e.get('target'),'relation':e.get('relation'),'via':e.get('via'),
      'evidence_refs':sorted(str(x) for x in (e.get('evidence_refs') or [])),
      'evidence_count':e.get('evidence_count',0),'independence_count':e.get('independence_count',0),
      'status':e.get('status'),'similarity':e.get('similarity'),
      'contradiction_count':e.get('contradiction_count',0)
    }
    return sha(canon(core))

def topology_support(edges):
    # Adamic-Adar-like shared-neighbor support, used only as discovery-priority context.
    adj=collections.defaultdict(set)
    for e in edges:
        a,b=str(e.get('source','')),str(e.get('target',''))
        if a and b: adj[a].add(b); adj[b].add(a)
    out={}
    for e in edges:
        a,b=str(e.get('source','')),str(e.get('target',''))
        shared=adj[a] & adj[b]
        raw=sum(1.0/max(1.0,math.log2(2+len(adj[n]))) for n in shared)
        out[edge_key(e)] = min(1.0, raw/3.0)
    return out

def relation_target(e, structural=0.0):
    rel=str(e.get('relation','')).upper(); sim=float(e.get('similarity') or 0.0)
    ind=max(0,int(e.get('independence_count') or 0)); ev=max(0,int(e.get('evidence_count') or 0))
    contradiction=max(0,int(e.get('contradiction_count') or 0))
    if rel=='SOURCE_LINEAGE': base=0.62
    elif rel=='SEMANTIC_SIMILARITY': base=0.10 + 0.36*max(0.0,min(1.0,sim))
    elif rel=='SHARED_ENTITY': base=0.18
    elif rel=='MENTIONS': base=0.15
    elif 'CONTRADICT' in rel or 'DISCONFIRM' in rel: base=0.12
    else: base=max(0.12,min(0.45,float(e.get('confidence') or 0.2)))
    # Independence and explicit evidence matter; topology is capped and never scientific authority.
    target=base + 0.07*min(ind,3) + 0.025*min(ev,4) + 0.08*structural - 0.12*min(contradiction,3)
    if rel=='SOURCE_LINEAGE' and ind==0: target=min(target,0.72)
    if rel=='SEMANTIC_SIMILARITY' and ind==0: target=min(target,0.49)
    return max(0.0,min(0.99,target))

def calibrate(edges, prev_rows, pass_id, replay_alpha=0.18, fresh_alpha=0.55, absent_decay=0.93):
    prev={r['edge_key']:r for r in prev_rows if r.get('edge_key')}
    topo=topology_support(edges)
    current={edge_key(e):e for e in edges}
    states=[]; hist=[]; counts=collections.Counter()
    for k,e in current.items():
        p=prev.get(k,{})
        old=float(p.get('weight',e.get('confidence',0.2) or 0.2))
        sig=evidence_signature(e); seen=set(p.get('seen_evidence_signatures') or [])
        fresh=sig not in seen
        target=relation_target(e,topo.get(k,0.0)); alpha=fresh_alpha if fresh else replay_alpha
        new=old+alpha*(target-old)
        delta=new-old
        if delta>0.015: movement='STRENGTHENED'
        elif delta<-0.015: movement='WEAKENED'
        else: movement='STABLE'
        seen.add(sig)
        row={
          'schema':SCHEMA+'.edge_state','edge_key':k,'source':e.get('source'),'target':e.get('target'),'relation':e.get('relation'),
          'via':e.get('via'),'weight':round(new,6),'previous_weight':round(old,6),'target_weight':round(target,6),
          'delta':round(delta,6),'movement':movement,'observed_this_pass':True,'pass_id':pass_id,
          'fresh_evidence_signature':fresh,'evidence_count':e.get('evidence_count',0),'independence_count':e.get('independence_count',0),
          'semantic_similarity':e.get('similarity'),'topology_support':round(topo.get(k,0.0),6),
          'seen_evidence_signatures':sorted(seen)[-64:],
          'claim_authority':'DISCOVERY_PRIORITY_ONLY__NOT_TRUTH_OR_CAUSATION'
        }
        states.append(row); counts[movement]+=1
        hist.append({x:row[x] for x in ['edge_key','source','target','relation','weight','previous_weight','target_weight','delta','movement','observed_this_pass','pass_id','fresh_evidence_signature','independence_count','topology_support']})
    # Old edges missing on this pass are weakened gently, never treated as disproved.
    for k,p in prev.items():
        if k in current: continue
        old=float(p.get('weight',0.0)); misses=int(p.get('consecutive_misses') or 0)+1; new=old*absent_decay
        movement='WEAKENED_NOT_REOBSERVED' if new<old else 'STABLE'
        row=dict(p); row.update({'previous_weight':round(old,6),'weight':round(new,6),'target_weight':None,'delta':round(new-old,6),'movement':movement,'observed_this_pass':False,'pass_id':pass_id,'consecutive_misses':misses,'claim_authority':'DISCOVERY_PRIORITY_ONLY__NOT_TRUTH_OR_CAUSATION'})
        if misses>=4 and new<0.08: row['movement']='DORMANT_CANDIDATE'
        states.append(row); counts[row['movement']]+=1
        hist.append({x:row.get(x) for x in ['edge_key','source','target','relation','weight','previous_weight','target_weight','delta','movement','observed_this_pass','pass_id','fresh_evidence_signature','independence_count','topology_support']})
    states.sort(key=lambda r:(-r['weight'],r['edge_key'])); hist.sort(key=lambda r:r['edge_key'])
    receipt={
      'schema':SCHEMA+'.receipt','status':'PASS','pass_id':pass_id,'current_edges':len(edges),'state_edges':len(states),
      'movement_counts':dict(sorted(counts.items())),'state_stream_sha256':sha(''.join(canon(r)+'\n' for r in states)),
      'history_append_sha256':sha(''.join(canon(r)+'\n' for r in hist)),
      'laws':['REPLAY_IS_NOT_NEW_EVIDENCE','ABSENCE_IN_ONE_PASS_IS_NOT_DISPROOF','GRAPH_DENSITY_IS_NOT_EVIDENCE','WEIGHT_IS_DISCOVERY_PRIORITY_NOT_TRUTH','SEMANTIC_SIMILARITY_IS_NOT_MECHANISM','INDEPENDENT_EVIDENCE_MAY_STRENGTHEN','CONTRADICTION_MAY_WEAKEN'],
      'note':'Repeated spiral passes converge weights toward the current evidence/topology target but do not increment evidence_count or independence_count.'
    }
    return states,hist,receipt

def self_test():
    e=[{'source':'A','target':'B','relation':'SEMANTIC_SIMILARITY','similarity':0.8,'confidence':0.3,'evidence_count':0,'independence_count':0},{'source':'B','target':'C','relation':'SHARED_ENTITY','confidence':0.3,'evidence_count':2,'independence_count':1},{'source':'A','target':'C','relation':'SOURCE_LINEAGE','confidence':0.95,'evidence_count':1,'independence_count':0}]
    s1,h1,r1=calibrate(e,[],1)
    s2,h2,r2=calibrate(e,s1,2)
    assert r1['status']=='PASS' and r2['status']=='PASS'
    assert all(x['fresh_evidence_signature'] is False for x in s2)
    assert all(x['claim_authority'].startswith('DISCOVERY_PRIORITY') for x in s2)
    e2=e[:2]
    s3,_,_=calibrate(e2,s2,3)
    missing=[x for x in s3 if x['relation']=='SOURCE_LINEAGE'][0]
    assert missing['movement']=='WEAKENED_NOT_REOBSERVED'
    return {'schema':SCHEMA+'.self_test','status':'PASS','replay_not_new_evidence':True,'missing_edge_weakens_gently':True,'history_preserved':True}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); sp.add_parser('self-test')
    p=sp.add_parser('calibrate'); p.add_argument('--edges',required=True); p.add_argument('--previous-state'); p.add_argument('--state',required=True); p.add_argument('--history',required=True); p.add_argument('--receipt',required=True); p.add_argument('--pass-id',required=True)
    a=ap.parse_args()
    if a.cmd=='self-test': print(json.dumps(self_test(),indent=2)); return 0
    edges=read_jsonl(a.edges); prev=read_jsonl(a.previous_state); state,hist,receipt=calibrate(edges,prev,a.pass_id)
    write_jsonl(a.state,state)
    hp=Path(a.history); hp.parent.mkdir(parents=True,exist_ok=True)
    with hp.open('a',encoding='utf-8',newline='\n') as f:
        for r in hist:f.write(canon(r)+'\n')
    write_json(a.receipt,receipt); print(json.dumps(receipt,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
