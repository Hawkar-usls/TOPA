#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path

SCHEMA='hawkar.topa.spider.hrain_package.v1'

def canon(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sh(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def read_jsonl(p):
    path=Path(p)
    if not p or not path.exists(): return []
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8')) if p and Path(p).exists() else None

def pack(nodes_path,state_path,history_path=None,receipts=None,fur_path=None):
    nodes=read_jsonl(nodes_path); state=read_jsonl(state_path); history=read_jsonl(history_path) if history_path else []; fur=read_jsonl(fur_path) if fur_path else []
    by_edge=defaultdict(list)
    for h in history:
        if h.get('edge_key'): by_edge[h['edge_key']].append(h)
    fur_by_subject={x.get('subject_id'):x for x in fur if x.get('subject_id')}
    edges=[]
    for e in state:
        edges.append({
          'edge_key':e.get('edge_key'),'source':e.get('source'),'target':e.get('target'),'relation':e.get('relation'),'via':e.get('via'),
          'weight':e.get('weight'),'previous_weight':e.get('previous_weight'),'target_weight':e.get('target_weight'),'movement':e.get('movement'),
          'independence_count':e.get('independence_count',0),'evidence_count':e.get('evidence_count',0),'semantic_similarity':e.get('semantic_similarity'),
          'topology_support':e.get('topology_support'),'history':by_edge.get(e.get('edge_key'),[]),
          'claim_authority':'DISCOVERY_PRIORITY_ONLY__NOT_TRUTH_OR_CAUSATION'
        })
    packed_nodes=[]
    fur_subjects=0
    for n in nodes:
        x=dict(n); f=fur_by_subject.get(str(n.get('id')))
        if f:
            x['context_fur']=f.get('context_fur',{})
            x['fur_coverage']=f.get('coverage',{})
            x['fur_history']=f.get('history',[])
            x['fur_acquisition_queue']=f.get('acquisition_queue',[])
            fur_subjects+=1
        packed_nodes.append(x)
    receipt_objs=[read_json(p) for p in (receipts or []) if p]
    fur_scores=[float(x.get('coverage',{}).get('score',0) or 0) for x in fur]
    pkg={
      'schema':SCHEMA,'status':'READY_FOR_HRAIN_SPIDER_MODE','nodes':packed_nodes,'edges':edges,'receipts':[x for x in receipt_objs if x],
      'stats':{'nodes':len(nodes),'edges':len(edges),'history_rows':len(history),'fur_subjects':fur_subjects,'fur_mean_coverage':round(sum(fur_scores)/len(fur_scores),6) if fur_scores else 0.0},
      'laws':['HRAIN_VISUAL_WEIGHT_IS_NOT_TRUTH','GRAPH_EDGE_IS_NOT_CAUSATION','REPLAY_IS_NOT_NEW_EVIDENCE','HRAIN_DOES_NOT_WRITE_BACK_TO_ARCHIVE_SOURCE','CONTEXT_COMPLETENESS_IS_NOT_CLAIM_STRENGTH','UNKNOWN_STAYS_UNKNOWN'],
      'ui_contract':{'default_min_weight':0.18,'retain_full_graph_in_memory':True,'render_filtered_subset':True,'edge_history_available':bool(history),'context_fur_available':bool(fur),'context_fur_fields':['coverage','facet status','observations','conflicts','acquisition queue']}
    }
    pkg['package_sha256']=sh(canon({k:v for k,v in pkg.items() if k!='package_sha256'}))
    return pkg

def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        r=Path(td)
        (r/'n.jsonl').write_text('{"id":"A","label":"A","type":"document"}\n{"id":"B","label":"B","type":"document"}\n',encoding='utf-8')
        (r/'s.jsonl').write_text('{"edge_key":"A|B|SEMANTIC_SIMILARITY|","source":"A","target":"B","relation":"SEMANTIC_SIMILARITY","weight":0.4,"movement":"STABLE"}\n',encoding='utf-8')
        (r/'h.jsonl').write_text('{"edge_key":"A|B|SEMANTIC_SIMILARITY|","pass_id":"P1","weight":0.3}\n',encoding='utf-8')
        (r/'f.jsonl').write_text('{"subject_id":"A","coverage":{"score":0.2},"context_fur":{"weather":{"status":"UNKNOWN","observations":[],"missing":["cloud_cover"]}},"history":[{"pass_id":"F1"}],"acquisition_queue":[{"facet":"weather"}]}\n',encoding='utf-8')
        p=pack(r/'n.jsonl',r/'s.jsonl',r/'h.jsonl',fur_path=r/'f.jsonl')
        assert p['stats']['nodes']==2 and p['stats']['edges']==1 and p['stats']['history_rows']==1 and p['stats']['fur_subjects']==1
        assert p['nodes'][0]['context_fur']['weather']['status']=='UNKNOWN'
        return {'schema':SCHEMA+'.self_test','status':'PASS','history_joined':True,'fur_joined':True,'hash_present':bool(p['package_sha256'])}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); sp.add_parser('self-test')
    q=sp.add_parser('pack'); q.add_argument('--nodes',required=True); q.add_argument('--state',required=True); q.add_argument('--history'); q.add_argument('--fur'); q.add_argument('--receipt',action='append',default=[]); q.add_argument('--out',required=True)
    a=ap.parse_args()
    if a.cmd=='self-test': print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    p=pack(a.nodes,a.state,a.history,a.receipt,a.fur); out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(p,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8'); print(json.dumps({'status':'PASS','package_sha256':p['package_sha256'],'stats':p['stats']},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
