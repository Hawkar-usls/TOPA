#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))
from topa_arxiv_gateway import remote_search
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

def openalex(query,limit):
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
        out.append({
          "provider":"OPENALEX","archive_id":w.get("id"),"title":w.get("title") or "",
          "text":abstract,"source_url":w.get("doi") or w.get("id") or "",
          "relation_tags":["P_VS_NP","LITERATURE_DISCOVERY"],
          "review_state":"UNEXAMINED","scientific_authority":"DISCOVERY_METADATA_ONLY",
          "claim_ceiling":"PAPER_METADATA_AND_CLAIMS_REQUIRE_SEPARATE_VALIDATION"
        })
    return out

def arxiv_records(query,limit):
    records,rc=remote_search(query,limit=limit,page_size=min(limit,100))
    out=[]
    for r in records:
        out.append({
          "provider":"ARXIV","archive_id":r.get("arxiv_id"),"title":r.get("title") or "",
          "text":r.get("abstract") or "","source_url":r.get("abs_url") or r.get("entry_id") or "",
          "relation_tags":["P_VS_NP","LITERATURE_DISCOVERY"],
          "review_state":"UNEXAMINED","scientific_authority":"DISCOVERY_METADATA_ONLY",
          "claim_ceiling":"PAPER_METADATA_AND_CLAIMS_REQUIRE_SEPARATE_VALIDATION",
          "source_record_sha256":r.get("record_sha256")
        })
    return out,rc

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);ap.add_argument("--max-queries",type=int,default=6);ap.add_argument("--per-source",type=int,default=12);a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    assoc=fetch_json(ASSOC_URL)
    seeds=(assoc.get("topa_query_seeds") or [])[:max(1,a.max_queries)]
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
      "source_commit":assoc.get("source_commit"),"query_seed_count":len(seeds),"query_receipts":query_receipts,
      "record_count":len(records),"node_count":len(nodes),"edge_count":len(edges),
      "source_records_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
      "spider_receipt":sr,
      "authority":{"truth":False,"proof":False,"scientific_claim_promotion":False,"fundamentum_mutation":False},
      "claim_ceiling":"DISCOVERY_AND_CANDIDATE_RELATIONS_ONLY__NO_PNP_CLAIM_PROMOTION"
    }
    write(out/"LATEST.json",latest)
    print(json.dumps(latest,ensure_ascii=False,indent=2,sort_keys=True))

if __name__=="__main__":main()
