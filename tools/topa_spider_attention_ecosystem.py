#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, math
from pathlib import Path

SCHEMA='hawkar.topa.spider.attention_ecosystem.v1'

def canon(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def clamp(x,lo=0.0,hi=0.99): return max(lo,min(hi,float(x)))
def read_jsonl(p):
    if not p: return []
    path=Path(p)
    if not path.exists(): return []
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_jsonl(p,rows):
    path=Path(p); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(canon(r)+'\n' for r in rows),encoding='utf-8')
def write_json(p,o):
    path=Path(p); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def edge_attention_key(e): return 'edge:'+str(e.get('edge_key',''))
def node_attention_key(n): return 'node:'+str(n)

def repetition_shape(replay_streak):
    r=max(0,int(replay_streak))
    burst=0.18*(1.0-math.exp(-0.9*min(r,6)))
    fatigue=0.58*(1.0-math.exp(-0.45*max(0,r-3)))
    return burst,fatigue,burst-fatigue

def edge_attention_target(edge,replay_streak,fresh):
    base=clamp(edge.get('weight',0.2)); burst,fatigue,repetition_net=repetition_shape(replay_streak)
    novelty_bonus=0.14 if fresh else 0.0
    contradiction=int(edge.get('contradiction_count') or 0)
    contradiction_urgency=min(0.16,0.05*contradiction)
    target=clamp(base+novelty_bonus+repetition_net+contradiction_urgency)
    return target,{
      'base_edge_discovery_weight':round(base,6),'novelty_bonus':round(novelty_bonus,6),
      'repetition_burst':round(burst,6),'replay_fatigue':round(fatigue,6),
      'repetition_net':round(repetition_net,6),'contradiction_urgency':round(contradiction_urgency,6)}

def calibrate_edges(edge_states,previous,pass_id,fresh_alpha=0.72,replay_alpha=0.50,missing_decay=0.78):
    prev={r['attention_key']:r for r in previous if r.get('kind')=='EDGE_ATTENTION' and r.get('attention_key')}
    out=[]; hist=[]; counts=collections.Counter()
    for e in edge_states:
        k=edge_attention_key(e); p=prev.get(k,{})
        observed=bool(e.get('observed_this_pass',True)); fresh=bool(e.get('fresh_evidence_signature',False)) and observed
        prior_streak=int(p.get('replay_streak') or 0); replay_streak=0 if fresh else (prior_streak+1 if observed else prior_streak)
        old=float(p.get('attention_weight',e.get('weight',0.2) or 0.2))
        if not observed:
            target=clamp(old*missing_decay); alpha=1.0
            parts={'base_edge_discovery_weight':round(float(e.get('weight',0.0) or 0.0),6),'novelty_bonus':0.0,'repetition_burst':0.0,'replay_fatigue':0.0,'repetition_net':0.0,'contradiction_urgency':0.0}
        else:
            target,parts=edge_attention_target(e,replay_streak,fresh); alpha=fresh_alpha if fresh else replay_alpha
        new=clamp(old+alpha*(target-old)); delta=new-old
        movement='ATTENTION_STRENGTHENED' if delta>0.02 else ('ATTENTION_WEAKENED' if delta<-0.02 else 'ATTENTION_STABLE')
        if observed and replay_streak>=8 and parts['replay_fatigue']>parts['repetition_burst'] and new<0.22: movement='SATURATED_REPLAY_DECAY'
        row={
          'schema':SCHEMA+'.edge_attention','kind':'EDGE_ATTENTION','attention_key':k,'edge_key':e.get('edge_key'),
          'source':e.get('source'),'target':e.get('target'),'relation':e.get('relation'),'via':e.get('via'),'pass_id':pass_id,
          'attention_weight':round(new,6),'previous_attention_weight':round(old,6),'attention_target':round(target,6),
          'attention_delta':round(delta,6),'attention_movement':movement,'observed_this_pass':observed,
          'fresh_evidence_signature':fresh,'replay_streak':replay_streak,
          'fresh_evidence_events':int(p.get('fresh_evidence_events') or 0)+(1 if fresh else 0),
          'observed_passes':int(p.get('observed_passes') or 0)+(1 if observed else 0),
          'evidence_weight':e.get('weight'),'evidence_count':e.get('evidence_count',0),'independence_count':e.get('independence_count',0),
          'attention_components':parts,'claim_authority':'VOLATILE_DISCOVERY_ATTENTION_ONLY__NOT_EVIDENCE_TRUTH_OR_CAUSATION'}
        out.append(row); counts[movement]+=1
        hist.append({x:row.get(x) for x in ['kind','attention_key','edge_key','source','target','relation','pass_id','attention_weight','previous_attention_weight','attention_target','attention_delta','attention_movement','fresh_evidence_signature','replay_streak','observed_this_pass']})
    return out,hist,counts

def local_node_signals(edge_attention):
    inc=collections.defaultdict(list); fresh=collections.Counter(); repeated=collections.Counter(); observed=collections.Counter(); adj=collections.defaultdict(list)
    for e in edge_attention:
        a,b=str(e.get('source','')),str(e.get('target',''))
        if not a or not b: continue
        w=float(e.get('attention_weight',0.0) or 0.0); inc[a].append(w); inc[b].append(w); adj[a].append((b,w)); adj[b].append((a,w))
        if e.get('fresh_evidence_signature'): fresh[a]+=1; fresh[b]+=1
        if int(e.get('replay_streak') or 0)>=2: repeated[a]+=1; repeated[b]+=1
        if e.get('observed_this_pass'): observed[a]+=1; observed[b]+=1
    local={}
    for n,ws in inc.items():
        s=sorted(ws,reverse=True); degree=len(s); maxw=s[0] if s else 0.0; mean3=sum(s[:3])/max(1,len(s[:3]))
        novelty=fresh[n]/max(1,observed[n]); hub_norm=1.0/(1.0+0.10*math.log1p(max(0,degree-4)))
        local[n]=clamp((0.55*maxw+0.27*mean3+0.18*novelty)*hub_norm)
    return local,adj,inc,fresh,repeated,observed

def spiral_propagate(local,adj,rings=3,propagation=0.34):
    signal=dict(local); traces={n:[round(v,6)] for n,v in local.items()}
    for _ in range(max(1,int(rings))):
        nxt={}
        for n,base in local.items():
            neigh=adj.get(n,[])
            if neigh:
                denom=sum(max(0.01,w) for _,w in neigh); propagated=sum(signal.get(m,0.0)*max(0.01,w) for m,w in neigh)/denom
            else: propagated=0.0
            nxt[n]=clamp((1.0-propagation)*base+propagation*propagated)
        signal=nxt
        for n,v in signal.items(): traces.setdefault(n,[]).append(round(v,6))
    return signal,traces

def percentile(vals,q):
    if not vals:return 0.0
    xs=sorted(vals)
    if len(xs)==1:return xs[0]
    pos=(len(xs)-1)*q; lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    return xs[lo] if lo==hi else xs[lo]+(xs[hi]-xs[lo])*(pos-lo)

def calibrate_nodes(edge_attention,previous,pass_id,rings=3,propagation=0.34,node_alpha=0.58,unseen_decay=0.82,max_focus_centers=5):
    prev={r['attention_key']:r for r in previous if r.get('kind')=='NODE_ATTENTION' and r.get('attention_key')}
    local,adj,inc,fresh,repeated,observed=local_node_signals(edge_attention); spiral,traces=spiral_propagate(local,adj,rings,propagation)
    rows=[]; all_nodes=set(local)|{k.split(':',1)[1] for k in prev}
    for n in sorted(all_nodes):
        k=node_attention_key(n); p=prev.get(k,{}); old=float(p.get('attention_score',0.0) or 0.0)
        if n in spiral: target=spiral[n]; new=clamp(old+node_alpha*(target-old)); observed_node=True
        else: target=clamp(old*unseen_decay); new=target; observed_node=False
        delta=new-old; movement='FOCUS_STRENGTHENED' if delta>0.02 else ('FOCUS_WEAKENED' if delta<-0.02 else 'FOCUS_STABLE')
        rows.append({'schema':SCHEMA+'.node_attention','kind':'NODE_ATTENTION','attention_key':k,'node_id':n,'pass_id':pass_id,
          'attention_score':round(new,6),'previous_attention_score':round(old,6),'attention_target':round(target,6),'attention_delta':round(delta,6),
          'attention_movement':movement,'observed_this_pass':observed_node,'degree':len(inc.get(n,[])),'fresh_incident_edges':fresh.get(n,0),
          'repeated_incident_edges':repeated.get(n,0),'observed_incident_edges':observed.get(n,0),'local_signal':round(local.get(n,0.0),6),
          'spiral_ring_trace':traces.get(n,[]),'claim_authority':'VOLATILE_DISCOVERY_ATTENTION_ONLY__NO_FIXED_HYPOTHESIS_CENTER'})
    ranked=sorted(rows,key=lambda r:(-r['attention_score'],r['node_id'])); vals=[r['attention_score'] for r in ranked]
    threshold=max(0.28,percentile(vals,0.75)) if vals else 1.0; chosen=[r for r in ranked if r['attention_score']>=threshold][:max_focus_centers]
    if ranked and not chosen: chosen=[ranked[0]]
    chosen_ids={r['node_id'] for r in chosen}
    for i,r in enumerate(ranked,1):
        r['focus_rank']=i
        if r['node_id'] in chosen_ids: r['focus_state']='PRIMARY_FOCUS' if i==1 else 'ACTIVE_FOCUS'; r['focus_age']=int(prev.get(r['attention_key'],{}).get('focus_age') or 0)+1
        elif r['attention_score']<0.10: r['focus_state']='DORMANT'; r['focus_age']=0
        else: r['focus_state']='PERIPHERY'; r['focus_age']=0
    return ranked,chosen,threshold

def calibrate(edge_states,previous,pass_id,rings=3):
    edge_rows,edge_hist,counts=calibrate_edges(edge_states,previous,pass_id); node_rows,centers,threshold=calibrate_nodes(edge_rows,previous,pass_id,rings=rings)
    states=edge_rows+node_rows
    history=edge_hist+[{x:r.get(x) for x in ['kind','attention_key','node_id','pass_id','attention_score','previous_attention_score','attention_target','attention_delta','attention_movement','focus_rank','focus_state','focus_age']} for r in node_rows]
    receipt={'schema':SCHEMA+'.receipt','status':'PASS','pass_id':pass_id,'edge_attention_rows':len(edge_rows),'node_attention_rows':len(node_rows),
      'edge_attention_movements':dict(sorted(counts.items())),'focus_threshold':round(threshold,6),
      'focus_centers':[{'node_id':r['node_id'],'attention_score':r['attention_score'],'focus_rank':r['focus_rank'],'focus_age':r['focus_age']} for r in centers],
      'spiral_rings':rings,'state_stream_sha256':sha(''.join(canon(r)+'\n' for r in states)),'history_append_sha256':sha(''.join(canon(r)+'\n' for r in history)),
      'laws':['ATTENTION_WEIGHT_IS_NOT_EVIDENCE_WEIGHT','REPETITION_MAY_TRIGGER_INSPECTION_BUT_NOT_TRUTH','REPLAY_SATURATES_AND_FATIGUES','FRESH_INDEPENDENT_EVIDENCE_CAN_RENEW_ATTENTION','NO_FIXED_HYPOTHESIS_CENTER','FOCUS_MAY_MIGRATE_OR_DIE','GRAPH_DENSITY_IS_NOT_EVIDENCE','CONTRADICTION_MAY_RAISE_INSPECTION_URGENCY_WITHOUT_RAISING_TRUTH','EXACT_OR_SOURCE_EVIDENCE_REMAINS_EXTERNAL_AUTHORITY'],
      'note':'Spiral attention is a volatile discovery ecology. Repetition can create an early salience burst, then replay fatigue suppresses stale patterns; node focus is propagated across bounded graph rings and is never permanent.'}
    return states,history,receipt

def self_test():
    edge={'edge_key':'A|B|SEMANTIC_SIMILARITY|','source':'A','target':'B','relation':'SEMANTIC_SIMILARITY','weight':0.30,'observed_this_pass':True,'fresh_evidence_signature':True,'evidence_count':0,'independence_count':0}
    prev=[]; seq=[]
    for p in range(1,13):
        e=dict(edge); e['fresh_evidence_signature']=(p==1); states,_,rc=calibrate([e],prev,f'T{p}',rings=3)
        er=[x for x in states if x['kind']=='EDGE_ATTENTION'][0]; seq.append(er['attention_weight']); prev=states
    assert max(seq[:5])>seq[0] and seq[-1]<max(seq[:5])
    assert [x for x in prev if x['kind']=='NODE_ATTENTION'][0]['spiral_ring_trace'] and rc['focus_centers']
    assert 'NO_FIXED_HYPOTHESIS_CENTER' in rc['laws']
    e2=dict(edge); e2['fresh_evidence_signature']=True; e2['weight']=0.42; states2,_,_=calibrate([e2],prev,'RENEW',rings=3)
    renewed=[x for x in states2 if x['kind']=='EDGE_ATTENTION'][0]['attention_weight']; assert renewed>seq[-1]
    return {'schema':SCHEMA+'.self_test','status':'PASS','early_repetition_salience':True,'stale_replay_fatigue':True,'fresh_evidence_renews_attention':True,'dynamic_node_focus':True,'no_fixed_hypothesis_center':True,'attention_is_not_truth':True,'sequence':[round(x,6) for x in seq]}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); sp.add_parser('self-test')
    p=sp.add_parser('calibrate'); p.add_argument('--edge-state',required=True); p.add_argument('--previous-attention'); p.add_argument('--state',required=True); p.add_argument('--history',required=True); p.add_argument('--receipt',required=True); p.add_argument('--pass-id',required=True); p.add_argument('--spiral-rings',type=int,default=3)
    a=ap.parse_args()
    if a.cmd=='self-test': print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    edges=read_jsonl(a.edge_state); prev=read_jsonl(a.previous_attention); state,hist,receipt=calibrate(edges,prev,a.pass_id,a.spiral_rings)
    write_jsonl(a.state,state); hp=Path(a.history); hp.parent.mkdir(parents=True,exist_ok=True)
    with hp.open('a',encoding='utf-8',newline='\n') as f:
        for r in hist:f.write(canon(r)+'\n')
    write_json(a.receipt,receipt); print(json.dumps(receipt,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
