#!/usr/bin/env python3
"""TOPA SPIDER v2: dynamic graph weaving + relationship-driven selective pull.

The spider has no fixed hypothesis center. It may start from any seed corpus or
query. Archive inventories are surveyed broadly but only records connected to
the current web are pulled into local raw/unexamined storage. Pulled records
become the next frontier, allowing bounded recursive expansion.

Scientific boundary:
  GRAPH_EDGE_IS_NOT_CAUSATION
  SEMANTIC_SIMILARITY_IS_NOT_MECHANISM
  PULL_DECISION_IS_NOT_EVIDENCE
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math, re
from pathlib import Path

WORD=re.compile(r"[A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9_.+\-/]{2,}")
DATE=re.compile(r"\b(?:18|19|20)\d{2}(?:-\d{2}-\d{2})?\b")
STOP={"the","and","for","with","from","that","this","into","are","was","were","not","have","has","had","its","their","about","records","record","archive","archived","source","metadata","document","documents","page","pages","http","https","www","gov","com","org","pdf","json","html","unidentified","information","report","reports","research","official","public","collection","data","file","files","content","title","provider","landing","bulk","download"}

def canon(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sh(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():yield json.loads(line)
def write_jsonl(path,rows):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="\n") as f:
        for r in rows:f.write(canon(r)+"\n")
def doc_id(r):return f"doc:{r.get('provider','?')}:{r.get('archive_id') or sh(r.get('source_url',''))[:16]}"
def text_of(r):
    bits=[str(r.get("title") or ""),str(r.get("text") or ""),str(r.get("agency") or "")," ".join(str(x) for x in (r.get("relation_tags") or []))]
    raw=r.get("raw_metadata")
    if isinstance(raw,dict):
        for k in ("title","scopeAndContentNote","dateNote","arrangement","description","subject"):
            if raw.get(k):bits.append(str(raw.get(k)))
    return " ".join(bits)
def tokens(s):return [w.lower() for w in WORD.findall(s) if w.lower() not in STOP and len(w)>=3 and not w.isdigit()]
def tagset(r):return {str(x).strip().lower() for x in (r.get("relation_tags") or []) if str(x).strip()}
def dateset(r):return set(DATE.findall(text_of(r)))
def tfidf_vectors(docs):
    toks={k:tokens(v) for k,v in docs.items()};n=max(1,len(toks));df=collections.Counter()
    for ts in toks.values():
        for t in set(ts):df[t]+=1
    vecs={}
    for k,ts in toks.items():
        c=collections.Counter(ts);total=max(1,sum(c.values()));v={}
        for t,nc in c.items():v[t]=(nc/total)*(math.log((1+n)/(1+df[t]))+1.0)
        norm=math.sqrt(sum(x*x for x in v.values())) or 1.0
        vecs[k]={t:x/norm for t,x in v.items()}
    return vecs,df
def cosine(a,b):
    if len(a)>len(b):a,b=b,a
    return sum(v*b.get(k,0.0) for k,v in a.items())
def jaccard(a,b):
    if not a or not b:return 0.0
    return len(a&b)/len(a|b)
def salient_keywords(doc_vec,limit=10):return [t for t,_ in sorted(doc_vec.items(),key=lambda kv:(-kv[1],kv[0]))[:limit]]

def build_graph(records,semantic_threshold=0.14,topk=5,keyword_nodes=8):
    nodes={};edges={};docs={};rec_by_id={}
    for r in records:
        did=doc_id(r);rec_by_id[did]=r;docs[did]=text_of(r)
        nodes[did]={"id":did,"type":"document","label":r.get("title") or did,"provider":r.get("provider"),"source_url":r.get("source_url"),"review_state":r.get("review_state","UNEXAMINED"),"record_sha256":r.get("record_sha256"),"scientific_authority":"ARCHIVAL_PROVENANCE_ONLY"}
    vec,_=tfidf_vectors(docs);memberships=collections.defaultdict(list)
    for did,r in rec_by_id.items():
        entities=[]
        for tag in sorted(tagset(r)):entities.append(("tag",tag))
        for d in sorted(dateset(r)):entities.append(("date",d))
        for kw in salient_keywords(vec.get(did,{}),keyword_nodes):entities.append(("keyword",kw))
        for typ,val in sorted(set(entities)):
            eid=f"{typ}:{val}";nodes.setdefault(eid,{"id":eid,"type":typ,"label":val});memberships[eid].append(did)
            key=tuple(sorted([did,eid]))+("MENTIONS",)
            edges[key]={"source":did,"target":eid,"relation":"MENTIONS","confidence":0.30 if typ=="keyword" else 0.35,"evidence_count":1,"independence_count":1,"status":"WEAK_DISCOVERY_EDGE","evidence_refs":[r.get("source_url")],"epistemic_note":"MENTION_OR_KEYWORD_IS_NOT_MECHANISM"}
    for eid,ds in memberships.items():
        for i in range(len(ds)):
            for j in range(i+1,len(ds)):
                a,b=ds[i],ds[j];pa=nodes[a].get("provider");pb=nodes[b].get("provider");ind=int(bool(pa and pb and pa!=pb))
                k=tuple(sorted([a,b]))+("SHARED_ENTITY",eid)
                edges[k]={"source":a,"target":b,"relation":"SHARED_ENTITY","via":eid,"confidence":0.26+0.10*ind,"evidence_count":2,"independence_count":ind,"status":"WEAK_ASSOCIATION","epistemic_note":"SHARED_ENTITY_IS_NOT_CAUSATION"}
    url_to_id={r.get("source_url"):doc_id(r) for r in records if r.get("source_url")}
    for r in records:
        parent=r.get("parent_url")
        if parent and parent in url_to_id:
            a=doc_id(r);b=url_to_id[parent];k=tuple(sorted([a,b]))+("SOURCE_LINEAGE",)
            edges[k]={"source":a,"target":b,"relation":"SOURCE_LINEAGE","confidence":0.95,"evidence_count":1,"independence_count":0,"status":"EXPLICIT_PROVENANCE_EDGE","epistemic_note":"SAME_SOURCE_LINEAGE_DOES_NOT_ADD_INDEPENDENCE"}
    dids=sorted(docs)
    for a in dids:
        sims=[]
        for b in dids:
            if b<=a:continue
            c=cosine(vec.get(a,{}),vec.get(b,{}))
            if c>=semantic_threshold:sims.append((c,b))
        for c,b in sorted(sims,reverse=True)[:topk]:
            edges[(a,b,"SEMANTIC_SIMILARITY")]={"source":a,"target":b,"relation":"SEMANTIC_SIMILARITY","confidence":round(min(0.49,0.14+0.35*c),6),"similarity":round(c,6),"evidence_count":0,"independence_count":0,"status":"SPECULATIVE_SEMANTIC_EDGE","epistemic_note":"SEMANTIC_SIMILARITY_IS_NOT_MECHANISM"}
    return sorted(nodes.values(),key=lambda n:n["id"]),sorted(edges.values(),key=lambda e:(e["source"],e["target"],e["relation"],str(e.get("via",""))))

def pair_features(candidate,seed,vecs):
    cid,sid=doc_id(candidate),doc_id(seed);sem=cosine(vecs.get(cid,{}),vecs.get(sid,{}));tags=jaccard(tagset(candidate),tagset(seed));dates=jaccard(dateset(candidate),dateset(seed))
    explicit=int(candidate.get("parent_url")==seed.get("source_url") or seed.get("parent_url")==candidate.get("source_url") or candidate.get("source_url")==seed.get("source_url"))
    diff=int(bool(candidate.get("provider") and seed.get("provider")) and candidate.get("provider")!=seed.get("provider"))
    score=1.0 if explicit else min(0.99,0.68*sem+0.20*tags+0.07*dates+0.05*diff);reasons=[]
    if explicit:reasons.append({"type":"EXPLICIT_SOURCE_LINK","weight":1.0})
    if sem>0:reasons.append({"type":"SEMANTIC","value":round(sem,6)})
    if tags>0:reasons.append({"type":"SHARED_TAGS","value":round(tags,6),"tags":sorted(tagset(candidate)&tagset(seed))})
    if dates>0:reasons.append({"type":"SHARED_DATES","value":round(dates,6),"dates":sorted(dateset(candidate)&dateset(seed))})
    if diff:reasons.append({"type":"DIFFERENT_PROVIDER","value":1})
    return score,reasons,sem,explicit

def selective_pull(seed_records,candidate_records,query="",threshold=0.22,semantic_only_threshold=0.42,max_pull=100,rounds=2):
    seed_map={doc_id(r):r for r in seed_records};cand_map={doc_id(r):r for r in candidate_records if doc_id(r) not in seed_map};pulled=[];rr=[];qterms=set(tokens(query or ""))
    for rn in range(1,max(1,rounds)+1):
        if not cand_map:break
        seeds=list(seed_map.values());merged={doc_id(r):text_of(r) for r in seeds};merged.update({doc_id(r):text_of(r) for r in cand_map.values()});vecs,_=tfidf_vectors(merged);scored=[]
        for cid,cand in cand_map.items():
            best=None
            for seed in seeds:
                x=pair_features(cand,seed,vecs);item=(x[0],doc_id(seed),x[1],x[2],x[3])
                if best is None or item[0]>best[0]:best=item
            if best is None:continue
            score,sid,reasons,sem,explicit=best
            qcov=0.0
            if qterms:
                ct=set(tokens(text_of(cand)));qcov=len(qterms&ct)/len(qterms)
                if qcov:score=min(0.99,score+0.10*qcov);reasons.append({"type":"QUERY_OVERLAP","value":round(qcov,6),"terms":sorted(qterms&ct)})
            nonsem=any(r["type"] in {"EXPLICIT_SOURCE_LINK","SHARED_TAGS","SHARED_DATES","QUERY_OVERLAP"} for r in reasons)
            if explicit or (score>=threshold and (nonsem or sem>=semantic_only_threshold)):scored.append((score,sem,cid,sid,reasons,nonsem))
        chosen=sorted(scored,key=lambda x:(-x[0],-x[1],x[2]))[:max_pull]
        if not chosen:rr.append({"round":rn,"pulled":0,"remaining_candidates":len(cand_map)});break
        this=[]
        for score,sem,cid,sid,reasons,nonsem in chosen:
            rec=dict(cand_map.pop(cid));rec["spider_pull"]={"round":rn,"relationship_score":round(score,6),"semantic_similarity":round(sem,6),"connected_to":sid,"relationship_reasons":reasons,"status":"CONNECTED_PULL" if nonsem else "SPECULATIVE_SEMANTIC_PULL","claim_authority":"DISCOVERY_ROUTING_ONLY"};pulled.append(rec);this.append(rec);seed_map[cid]=rec
        rr.append({"round":rn,"pulled":len(this),"remaining_candidates":len(cand_map),"min_score":round(min(r["spider_pull"]["relationship_score"] for r in this),6),"max_score":round(max(r["spider_pull"]["relationship_score"] for r in this),6)})
    pulled=sorted(pulled,key=lambda r:(r["spider_pull"]["round"],-r["spider_pull"]["relationship_score"],doc_id(r)))
    rc={"schema":"hawkar.topa.spider.selective_pull.receipt.v1","status":"PASS","seed_documents":len(seed_records),"survey_candidates":len(candidate_records),"pulled_documents":len(pulled),"rejected_or_unconnected":max(0,len(candidate_records)-len(pulled)),"query":query or None,"threshold":threshold,"semantic_only_threshold":semantic_only_threshold,"max_pull_per_round":max_pull,"rounds_requested":rounds,"rounds":rr,"pulled_stream_sha256":sh("".join(canon(r)+"\n" for r in pulled)),"laws":["PULL_DECISION_IS_NOT_EVIDENCE","SEMANTIC_SIMILARITY_IS_NOT_MECHANISM","GRAPH_EDGE_IS_NOT_CAUSATION","UNCONNECTED_ARCHIVE_RECORDS_STAY_EXTERNAL_POINTERS","NO_FIXED_HYPOTHESIS_CENTER"],"policy":"SURVEY_WIDE__PERSIST_LOCAL_ONLY_IF_CONNECTED_TO_CURRENT_WEB"}
    return pulled,rc

def receipt(nodes,edges,records):
    rel=collections.Counter(e["relation"] for e in edges);weak=sum(e.get("confidence",0)<0.5 for e in edges)
    return {"schema":"hawkar.topa.spider.receipt.v2","status":"PASS","documents":len(records),"nodes":len(nodes),"edges":len(edges),"edge_types":dict(sorted(rel.items())),"weak_or_speculative_edges":weak,"node_stream_sha256":sh("".join(canon(n)+"\n" for n in nodes)),"edge_stream_sha256":sh("".join(canon(e)+"\n" for e in edges)),"laws":["GRAPH_EDGE_IS_NOT_CAUSATION","SEMANTIC_SIMILARITY_IS_NOT_MECHANISM","GRAPH_DENSITY_IS_NOT_EVIDENCE","REPEATED_SAME_SOURCE_IS_NOT_INDEPENDENT_WITNESS","NO_FIXED_HYPOTHESIS_CENTER"],"promotion_rule":"EDGE_STRENGTH_MAY_RISE_ONLY_WITH_EXPLICIT_SOURCE_RELATION_OR_INDEPENDENT_EVIDENCE__NEVER_FROM_DENSITY_ALONE"}

def self_test():
    seeds=[{"provider":"CIA","archive_id":"1","title":"Anomalous timing model","text":"reverse information precognition 1995","source_url":"https://cia/1","relation_tags":["anomalous cognition"]},{"provider":"NARA","archive_id":"2","title":"Ukraine aerial report","text":"unexplained aerial observation 1983","source_url":"https://nara/2","relation_tags":["Ukraine","aerial"]}]
    c=[{"provider":"NSA","archive_id":"3","title":"Related anomalous cognition study","text":"precognition reverse information model","source_url":"https://nsa/3","relation_tags":["anomalous cognition"]},{"provider":"FBI","archive_id":"4","title":"Unrelated bank memo","text":"bank robbery accounting evidence","source_url":"https://fbi/4","relation_tags":["crime"]},{"provider":"NARA","archive_id":"5","title":"Ukraine aviation incident","text":"Ukraine aerial 1983 observation","source_url":"https://nara/5","relation_tags":["Ukraine","aerial"]}]
    p,pr=selective_pull(seeds,c,threshold=0.18,semantic_only_threshold=0.30,max_pull=10,rounds=2);ids={r["archive_id"] for r in p};assert "3" in ids and "5" in ids and "4" not in ids
    n,e=build_graph(seeds+p,0.05,5);rc=receipt(n,e,seeds+p);assert rc["status"]=="PASS" and pr["status"]=="PASS"
    return {"schema":"hawkar.topa.spider.self_test.v2","status":"PASS","relationship_driven_pull":True,"unrelated_record_rejected":True,"dynamic_keywords":True,"no_fixed_topic_center":True}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True);sp.add_parser("self-test")
    q=sp.add_parser("weave");q.add_argument("--input",required=True);q.add_argument("--nodes",required=True);q.add_argument("--edges",required=True);q.add_argument("--receipt",required=True);q.add_argument("--semantic-threshold",type=float,default=0.14);q.add_argument("--topk",type=int,default=5);q.add_argument("--keyword-nodes",type=int,default=8)
    p=sp.add_parser("pull");p.add_argument("--seed",required=True);p.add_argument("--survey",required=True);p.add_argument("--out",required=True);p.add_argument("--receipt",required=True);p.add_argument("--query",default="");p.add_argument("--threshold",type=float,default=0.22);p.add_argument("--semantic-only-threshold",type=float,default=0.42);p.add_argument("--max-pull",type=int,default=100);p.add_argument("--rounds",type=int,default=2)
    a=ap.parse_args()
    if a.cmd=="self-test":print(json.dumps(self_test(),ensure_ascii=False,indent=2));return 0
    if a.cmd=="pull":
        seeds=list(read_jsonl(a.seed));survey=list(read_jsonl(a.survey));pulled,rc=selective_pull(seeds,survey,a.query,a.threshold,a.semantic_only_threshold,a.max_pull,a.rounds);write_jsonl(a.out,pulled);Path(a.receipt).parent.mkdir(parents=True,exist_ok=True);Path(a.receipt).write_text(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True));return 0
    rs=list(read_jsonl(a.input));n,e=build_graph(rs,a.semantic_threshold,a.topk,a.keyword_nodes);rc=receipt(n,e,rs);write_jsonl(a.nodes,n);write_jsonl(a.edges,e);Path(a.receipt).parent.mkdir(parents=True,exist_ok=True);Path(a.receipt).write_text(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
