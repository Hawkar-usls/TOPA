#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))
from topa_arxiv_gateway import remote_search, build_smart_arxiv_query
from topa_spider import build_graph, receipt as spider_receipt, write_jsonl

ASSOC_URL="https://raw.githubusercontent.com/Hawkar-usls/iNaiHR/janus/fundamentum-associative-memory/data/fundamentum-associative/ASSOCIATIONS.json"
UA="TOPA-JANUS-PNP-Autoresearch/1.0 (+https://github.com/Hawkar-usls/TOPA)"

def fetch_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)

def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sh(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def normalize_query(q):
    q=str(q or "").strip()
    return " ".join(re.sub(r"\\b(?:all|ti|abs|cat):", "", q, flags=re.I).replace("(", " ").replace(")", " ").replace('"', " ").split())

def corpus_query_seeds(index,limit=3):
    if not isinstance(index,dict) or index.get("schema")!="JANUS_P_VS_NP_MATERIALS_INDEX":
        return []
    frontier=index.get("next_frontier") or {}
    missing=str(frontier.get("missing_object") or "")
    blob=" ".join([
      missing,
      " ".join(map(str,index.get("anti_loop_laws") or [])),
      " ".join(str(x.get("why_relevant") or "")+" "+str(x.get("blocker") or "") for x in (index.get("open_access_materials") or []) if isinstance(x,dict))
    ]).casefold()
    vocab=[
      "projection","compositional","invariant","interaction","certificate","consistency",
      "forgetting","knowledge compilation","polymorphism","few subpowers","constraint satisfaction",
      "variable elimination","extended resolution","backdoor","treewidth","affine","SAT"
    ]
    ranked=[v for v in vocab if all(t in blob for t in v.split())]
    topics=[
      "SAT projection compositional invariant interaction certificate",
      "knowledge compilation forgetting existential quantification SAT",
      "constraint satisfaction polymorphism few subpowers projection"
    ]
    if ranked:
        topics.insert(0,"P versus NP SAT "+" ".join(ranked[:5]))
    out=[]
    for i,q in enumerate(topics):
        if q not in [x["query"] for x in out]:
            out.append({"id":f"DRIVE_FRONTIER_{i+1}","query":q,"source":"P_VS_NP_MATERIALS_INDEX"})
        if len(out)>=limit: break
    return out

def openalex(query,limit):
    query=normalize_query(query)
    url="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":query,"per-page":limit})
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=45) as r:data=json.load(r)
    out=[]
    for w in data.get("results",[]):
        inv=w.get("abstract_inverted_index") or {}
        words=[]
        for token,positions in inv.items():
            for p in positions:words.append((p,token))
        abstract=" ".join(t for _,t in sorted(words))[:12000]
        authors=[str((a.get("author") or {}).get("display_name") or "") for a in (w.get("authorships") or []) if (a.get("author") or {}).get("display_name")]
        out.append({
          "provider":"OPENALEX","archive_id":w.get("id"),"title":w.get("title") or "",
          "authors":authors,"doi":w.get("doi"),"published":w.get("publication_date"),"updated":w.get("updated_date"),
          "text":abstract,"source_url":w.get("doi") or w.get("id") or "",
          "query_provenance":{"query":query,"provider":"OPENALEX"},
          "relation_tags":["P_VS_NP","LITERATURE_DISCOVERY"],
          "review_state":"UNEXAMINED","scientific_authority":"DISCOVERY_METADATA_ONLY",
          "claim_ceiling":"PAPER_METADATA_AND_CLAIMS_REQUIRE_SEPARATE_VALIDATION"
        })
    return out

def arxiv_records(query,limit):
    aq=query if re.search(r"\\b(?:all|ti|abs|cat):",query,re.I) else build_smart_arxiv_query(query)
    records,rc=remote_search(aq,limit=limit,page_size=min(limit,100))
    out=[]
    for r in records:
        out.append({
          "provider":"ARXIV","archive_id":r.get("arxiv_id"),"arxiv_id":r.get("arxiv_id"),"title":r.get("title") or "",
          "authors":r.get("authors") or [],"doi":r.get("doi") or None,"published":r.get("published"),"updated":r.get("updated"),
          "text":r.get("abstract") or "","source_url":r.get("abs_url") or r.get("entry_id") or "",
          "query_provenance":r.get("query_provenance") or {"query":aq,"provider":"ARXIV"},
          "relation_tags":["P_VS_NP","LITERATURE_DISCOVERY"],
          "review_state":"UNEXAMINED","scientific_authority":"DISCOVERY_METADATA_ONLY",
          "claim_ceiling":"PAPER_METADATA_AND_CLAIMS_REQUIRE_SEPARATE_VALIDATION",
          "source_record_sha256":r.get("record_sha256")
        })
    return out,rc

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);ap.add_argument("--max-queries",type=int,default=6);ap.add_argument("--per-source",type=int,default=12);ap.add_argument("--corpus-index");a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    assoc=fetch_json(ASSOC_URL)
    index=json.loads(Path(a.corpus_index).read_text(encoding="utf-8-sig")) if a.corpus_index else {}
    combined=[*corpus_query_seeds(index,limit=min(3,a.max_queries)),*(assoc.get("topa_query_seeds") or [])]
    seeds=[];seen=set()
    for seed in combined:
        q=str(seed.get("query") or seed.get("focus") or "").strip()
        nk=normalize_query(q).casefold()
        if not q or not nk or nk in seen: continue
        seen.add(nk);seeds.append(seed)
        if len(seeds)>=max(1,a.max_queries): break
    all_records=[];query_receipts=[]
    for seed in seeds:
        q=str(seed.get("query") or seed.get("focus") or "").strip()
        if not q:continue
        qr={"id":seed.get("id"),"query":q,"arxiv":{"status":"UNRESOLVED"},"openalex":{"status":"UNRESOLVED"}}
        try:
            rows,rc=arxiv_records(q,a.per_source);all_records.extend(rows);qr["arxiv"]={"status":"PASS","records":len(rows),"receipt":rc}
        except Exception as e:
            qr["arxiv"]={"status":"UNAVAILABLE","error":type(e).__name__+":"+str(e)}
        try:
            rows=openalex(q,a.per_source);all_records.extend(rows);qr["openalex"]={"status":"PASS","records":len(rows)}
        except Exception as e:
            qr["openalex"]={"status":"UNAVAILABLE","error":type(e).__name__+":"+str(e)}
        query_receipts.append(qr)
        time.sleep(1.0)
    dedup={}
    for r in all_records:
        k=(r.get("provider"),r.get("archive_id") or r.get("source_url") or sh(r))
        dedup[k]=r
    records=list(dedup.values())
    nodes,edges=build_graph(records,semantic_threshold=0.12,topk=6)
    src=out/"source-records.jsonl"
    write_jsonl(src,records);write_jsonl(out/"spider-nodes.jsonl",nodes);write_jsonl(out/"spider-edges.jsonl",edges)
    sr=spider_receipt(nodes,edges,records);write(out/"spider-receipt.json",sr)
    latest={
      "schema":"janus.topa.pnp_autoresearch_cycle.v1","status":"PASS_WITH_DEGRADED_SOURCES_ALLOWED",
      "source_commit":assoc.get("source_commit"),"corpus_index_sha256":sh(index) if index else None,
      "drive_frontier_seed_count":sum(1 for s in seeds if str(s.get("source") or "")=="P_VS_NP_MATERIALS_INDEX"),
      "query_seed_count":len(seeds),"query_receipts":query_receipts,
      "record_count":len(records),"node_count":len(nodes),"edge_count":len(edges),
      "source_records_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
      "spider_receipt":sr,
      "authority":{"truth":False,"proof":False,"scientific_claim_promotion":False,"fundamentum_mutation":False},
      "claim_ceiling":"DISCOVERY_AND_CANDIDATE_RELATIONS_ONLY__NO_PNP_CLAIM_PROMOTION"
    }
    write(out/"LATEST.json",latest)
    print(json.dumps(latest,ensure_ascii=False,indent=2,sort_keys=True))

if __name__=="__main__":main()
