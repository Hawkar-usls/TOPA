#!/usr/bin/env python3
from __future__ import annotations
import argparse, collections, hashlib, json, math, re
from pathlib import Path

WORD=re.compile(r"[A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9_.+\-/]{2,}")
DATE=re.compile(r"\b(?:19|20)\d{2}(?:-\d{2}-\d{2})?\b")
PLACE_TERMS={"ukraine","ukrainian","kyiv","kiev","odesa","odessa","chernobyl","palomar","arizona","colorado","petrozavodsk","ussr","soviet"}
TOPIC_TERMS={"uap","ufo","tachyon","tachyons","retrocausality","retrocausal","precognition","nuclear","palomar","star gate","stargate","remote viewing","advanced potential","reverse information","future to past","future-to-past"}
STOP={"the","and","for","with","from","that","this","into","are","was","were","not","have","has","had","its","their","about","records","record","archive","archived","source","metadata"}

def canon(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sh(s):return hashlib.sha256(s.encode()).hexdigest()
def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():yield json.loads(line)

def doc_id(r):return f"doc:{r.get('provider','?')}:{r.get('archive_id') or sh(r.get('source_url',''))[:16]}"
def text_of(r):return " ".join([str(r.get("title") or ""),str(r.get("text") or "")," ".join(str(x) for x in (r.get("relation_tags") or []))])
def tokens(s):return [w.lower() for w in WORD.findall(s) if w.lower() not in STOP and len(w)>=3]

def tfidf_vectors(docs):
    toks={k:tokens(v) for k,v in docs.items()};n=max(1,len(toks));df=collections.Counter()
    for ts in toks.values():
        for t in set(ts):df[t]+=1
    vecs={}
    for k,ts in toks.items():
        c=collections.Counter(ts);total=max(1,sum(c.values()));v={}
        for t,nc in c.items():
            if df[t]<2:continue
            v[t]=(nc/total)*(math.log((1+n)/(1+df[t]))+1.0)
        norm=math.sqrt(sum(x*x for x in v.values())) or 1.0
        vecs[k]={t:x/norm for t,x in v.items()}
    return vecs

def cosine(a,b):
    if len(a)>len(b):a,b=b,a
    return sum(v*b.get(k,0.0) for k,v in a.items())

def entity_nodes(r):
    txt=text_of(r);low=txt.lower();out=[]
    for t in sorted(TOPIC_TERMS):
        if t in low:out.append(("topic",t))
    for p in sorted(PLACE_TERMS):
        if p in low:out.append(("place",p))
    for d in sorted(set(DATE.findall(txt))):out.append(("date",d))
    for tag in r.get("relation_tags") or []:
        tag=str(tag).strip().lower()
        if tag:out.append(("tag",tag))
    return sorted(set(out))

def build_graph(records,semantic_threshold=0.14,topk=5):
    nodes={};edges={};docs={};memberships=collections.defaultdict(list)
    for r in records:
        did=doc_id(r);docs[did]=text_of(r)
        nodes[did]={"id":did,"type":"document","label":r.get("title") or did,"provider":r.get("provider"),"source_url":r.get("source_url"),"review_state":r.get("review_state","UNEXAMINED"),"record_sha256":r.get("record_sha256"),"scientific_authority":"ARCHIVAL_PROVENANCE_ONLY"}
        for typ,val in entity_nodes(r):
            eid=f"{typ}:{val}";nodes.setdefault(eid,{"id":eid,"type":typ,"label":val});memberships[eid].append(did)
            key=tuple(sorted([did,eid]))+("MENTIONS",)
            edges[key]={"source":did,"target":eid,"relation":"MENTIONS","confidence":0.35,"evidence_count":1,"independence_count":1,"status":"WEAK_DISCOVERY_EDGE","evidence_refs":[r.get("source_url")]}
    for eid,ds in memberships.items():
        for i in range(len(ds)):
            for j in range(i+1,len(ds)):
                a,b=ds[i],ds[j];pa=nodes[a].get("provider");pb=nodes[b].get("provider");independent=int(bool(pa and pb and pa!=pb))
                k=tuple(sorted([a,b]))+("SHARED_ENTITY",eid)
                edges[k]={"source":a,"target":b,"relation":"SHARED_ENTITY","via":eid,"confidence":0.28+0.12*independent,"evidence_count":2,"independence_count":independent,"status":"WEAK_ASSOCIATION","epistemic_note":"SHARED_ENTITY_IS_NOT_CAUSATION"}
    url_to_id={r.get("source_url"):doc_id(r) for r in records if r.get("source_url")}
    for r in records:
        parent=r.get("parent_url")
        if parent and parent in url_to_id:
            a=doc_id(r);b=url_to_id[parent];k=tuple(sorted([a,b]))+("SOURCE_LINEAGE",)
            edges[k]={"source":a,"target":b,"relation":"SOURCE_LINEAGE","confidence":0.95,"evidence_count":1,"independence_count":0,"status":"EXPLICIT_PROVENANCE_EDGE","epistemic_note":"SAME_SOURCE_LINEAGE_DOES_NOT_ADD_INDEPENDENCE"}
    vec=tfidf_vectors(docs);dids=sorted(docs)
    for a in dids:
        sims=[]
        for b in dids:
            if b<=a:continue
            c=cosine(vec.get(a,{}),vec.get(b,{}))
            if c>=semantic_threshold:sims.append((c,b))
        for c,b in sorted(sims,reverse=True)[:topk]:
            k=(a,b,"SEMANTIC_SIMILARITY")
            edges[k]={"source":a,"target":b,"relation":"SEMANTIC_SIMILARITY","confidence":round(min(0.49,0.15+0.35*c),6),"similarity":round(c,6),"evidence_count":0,"independence_count":0,"status":"SPECULATIVE_SEMANTIC_EDGE","epistemic_note":"SEMANTIC_SIMILARITY_IS_NOT_MECHANISM"}
    return sorted(nodes.values(),key=lambda n:n["id"]),sorted(edges.values(),key=lambda e:(e["source"],e["target"],e["relation"],str(e.get("via",""))))

def receipt(nodes,edges,records):
    rel=collections.Counter(e["relation"] for e in edges);weak=sum(e.get("confidence",0)<0.5 for e in edges)
    return {"schema":"hawkar.topa.spider.receipt.v1","status":"PASS","documents":len(records),"nodes":len(nodes),"edges":len(edges),"edge_types":dict(sorted(rel.items())),"weak_or_speculative_edges":weak,"node_stream_sha256":sh("".join(canon(n)+"\n" for n in nodes)),"edge_stream_sha256":sh("".join(canon(e)+"\n" for e in edges)),"laws":["GRAPH_EDGE_IS_NOT_CAUSATION","SEMANTIC_SIMILARITY_IS_NOT_MECHANISM","GRAPH_DENSITY_IS_NOT_EVIDENCE","REPEATED_SAME_SOURCE_IS_NOT_INDEPENDENT_WITNESS"],"promotion_rule":"EDGE_STRENGTH_MAY_RISE_ONLY_WITH_EXPLICIT_SOURCE_RELATION_OR_INDEPENDENT_EVIDENCE__NEVER_FROM_DENSITY_ALONE"}

def write_jsonl(path,rows):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="\n") as f:
        for r in rows:f.write(canon(r)+"\n")

def self_test():
    rs=[{"provider":"CIA","archive_id":"1","title":"Tachyon reverse information Ukraine","text":"precognition 1995","source_url":"https://cia/1","relation_tags":["tachyon"]},{"provider":"NARA","archive_id":"2","title":"Ukraine UAP record","text":"1995 unexplained object","source_url":"https://nara/2","relation_tags":["UAP"]},{"provider":"CIA","archive_id":"3","title":"same lineage","text":"tachyon","source_url":"https://cia/3","parent_url":"https://cia/1"}]
    n,e=build_graph(rs,0.05,5);rc=receipt(n,e,rs)
    assert rc["status"]=="PASS" and any(x["relation"]=="SOURCE_LINEAGE" for x in e) and any(x["relation"]=="SEMANTIC_SIMILARITY" for x in e)
    assert all(x.get("confidence",0)<0.5 for x in e if x["relation"]=="SEMANTIC_SIMILARITY")
    return {"schema":"hawkar.topa.spider.self_test.v1","status":"PASS","weak_semantic_edges":True,"lineage_edge":True,"no_density_promotion":True}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True);sp.add_parser("self-test")
    q=sp.add_parser("weave");q.add_argument("--input",required=True);q.add_argument("--nodes",required=True);q.add_argument("--edges",required=True);q.add_argument("--receipt",required=True);q.add_argument("--semantic-threshold",type=float,default=0.14);q.add_argument("--topk",type=int,default=5)
    a=ap.parse_args()
    if a.cmd=="self-test":print(json.dumps(self_test(),indent=2));return 0
    rs=list(read_jsonl(a.input));n,e=build_graph(rs,a.semantic_threshold,a.topk);rc=receipt(n,e,rs)
    write_jsonl(a.nodes,n);write_jsonl(a.edges,e);Path(a.receipt).write_text(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
