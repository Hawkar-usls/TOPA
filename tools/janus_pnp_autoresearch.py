#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

TOOLS=Path(__file__).resolve().parent
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))
try:
    from topa_arxiv_gateway import build_smart_arxiv_query, remote_search
    from topa_spider import build_graph, receipt as spider_receipt, write_jsonl
except ImportError:
    build_smart_arxiv_query=remote_search=build_graph=spider_receipt=write_jsonl=None

ASSOC_URL="https://raw.githubusercontent.com/Hawkar-usls/iNaiHR/janus/fundamentum-associative-memory/data/fundamentum-associative/ASSOCIATIONS.json"
KEYMASTER_FORGE_URL="https://raw.githubusercontent.com/Hawkar-usls/Janus-Demiurge/janus/autonomous-keymaster-lockpick/janus_model/autonomous-keymaster/KEYMASTER_AUTONOMOUS_FORGE_LATEST.json"
UA="TOPA-JANUS-PNP-Autoresearch/1.2 (+https://github.com/Hawkar-usls/TOPA)"

ROTATIONS=(
 ("parity constraints knowledge compilation structured d-DNNF vtree","XOR SAT incidence treewidth knowledge compilation","parity decision diagrams TDD BDD structured circuits","factor width CNF knowledge compilation parameterized complexity","Tseitin parity structured decomposable circuits lower bounds","XOR constraints dynamic programming decomposition exact algorithms"),
 ("independent transversal maximum degree two partitioned graph","rainbow independent set paths cycles partition constraints","partitioned independent set matching augmentation degree two","multilinear monomial read twice product of sums algorithm","Pi Sigma 3 Pi 2 multilinear monomial read twice","squarefree monomial detection bounded occurrence arithmetic formula"),
 ("Boolean CSP affine parity exact decomposition tractable islands","GF2 affine quotient residual width SAT exact algorithm","matroid parity matching parity constraints SAT decomposition","branchwidth rankwidth parity CSP exact dynamic programming","signed Tseitin formulas structural decomposition SAT","knowledge compilation lower bounds parity constraints treewidth"),
 ("SAT exact algorithm bounded occurrence structural parameter","3-SAT bounded occurrence matching reduction exact algorithm","constraint satisfaction polymorphism decomposition Boolean SAT","proof carrying elimination variable elimination SAT width","separator signatures SAT dynamic programming exact","circuit SAT knowledge compilation exact transformation polynomial"),
)

def fetch_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)

def adaptive_forge_queries(forge,limit=8):
    if not isinstance(forge,dict): return []
    cycle=int(forge.get("cycle_count") or 0)
    base=list(forge.get("search_queries") or [])[:2]
    base.extend(ROTATIONS[(cycle//2)%len(ROTATIONS)])
    target=forge.get("target") or {}
    phrase=" ".join([str(target.get("from_type") or "").replace("_"," ").lower(),str(target.get("to_type") or "").replace("_"," ").lower()]).strip()
    if phrase: base.extend([phrase+" exact algorithm",phrase+" lower bound decomposition"])
    out=[];seen=set()
    for q in base:
        q=" ".join(str(q or "").split());k=q.lower()
        if q and k not in seen: seen.add(k);out.append(q)
        if len(out)>=limit:break
    return out

def forge_seeds(forge,limit=6):
    if not isinstance(forge,dict): return []
    fw=forge.get("firewall") or {}
    if forge.get("schema")!="janus.keymaster.autonomous_forge.v1": return []
    if fw.get("P_VS_NP")!="OPEN" or fw.get("D1")!="EMPTY": return []
    if fw.get("branch_only_research") is not True: return []
    if fw.get("automatic_theorem_promotion") is not False or fw.get("automatic_p_equals_np_claim") is not False:return []
    if forge.get("keymaster_shadow_admission") is not False:return []
    target=forge.get("target") or {};out=[]
    for i,q in enumerate(adaptive_forge_queries(forge,limit)):
        out.append({"id":f"Q-KEYMASTER-ADAPT-{i+1:02d}","query":q,"focus":f"Keymaster #1 gap: {target.get('from_type','?')} -> {target.get('to_type','?')}","source":"JANUS_KEYMASTER_AUTONOMOUS_FORGE","authority":"DISCOVERY_QUERY_ONLY"})
    return out

def merge_query_seeds(assoc,forge,max_queries):
    generic=list((assoc or {}).get("topa_query_seeds") or [])
    stalled=isinstance(forge,dict) and forge.get("status") in {"SEARCHED_NO_NOVEL_FALLBACK_CANDIDATE","DUPLICATE_CANDIDATE_NO_ADVANCE"}
    targeted=forge_seeds(forge,limit=max_queries if stalled else min(4,max_queries))
    rows=[];seen=set()
    for row in targeted+generic:
        q=str(row.get("query") or row.get("focus") or "").strip();k=" ".join(q.lower().split())
        if not q or k in seen:continue
        seen.add(k);rows.append(row)
        if len(rows)>=max(1,max_queries):break
    return rows

def read_jsonl(path):
    if not path or not Path(path).exists():return []
    out=[]
    for raw in Path(path).read_text(encoding="utf-8",errors="replace").splitlines():
        try:v=json.loads(raw)
        except Exception:continue
        if isinstance(v,dict):out.append(v)
    return out

def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sh(x):return hashlib.sha256(canon(x).encode()).hexdigest()
def record_key(r):
    p=str(r.get("provider") or "").upper();a=str(r.get("archive_id") or "").strip().lower()
    if a:return ("ARCHIVE",p,a)
    u=str(r.get("source_url") or "").strip().lower()
    if u:return ("URL",u)
    t=" ".join(str(r.get("title") or "").lower().split())
    return ("TITLE",t) if t else ("SHA",sh(r))
def merge_records(prior,current):
    d={}
    for r in list(prior)+list(current):
        if isinstance(r,dict):d[record_key(r)]=r
    return list(d.values())
def novel_records(prior,current):
    old={record_key(r) for r in prior if isinstance(r,dict)}
    return [r for r in current if isinstance(r,dict) and record_key(r) not in old]
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def request_json(url,attempts=4):
    last=None
    for i in range(attempts):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
        except urllib.error.HTTPError as e:
            last=e
            if e.code not in (429,500,502,503,504) or i+1>=attempts:raise
            try:wait=max(4*(2**i),float(e.headers.get("Retry-After") or 0))
            except ValueError:wait=4*(2**i)
            time.sleep(min(wait,45))
        except Exception as e:
            last=e
            if i+1>=attempts:raise
            time.sleep(min(4*(2**i),30))
    raise last

def openalex(query,limit):
    url="https://api.openalex.org/works?"+urllib.parse.urlencode({"search":query,"per-page":max(1,min(limit,50))})
    data=request_json(url);out=[]
    for w in data.get("results",[]):
        inv=w.get("abstract_inverted_index") or {};words=[]
        for token,positions in inv.items():
            for p in positions:words.append((p,token))
        out.append({"provider":"OPENALEX","archive_id":w.get("id"),"title":w.get("title") or "","text":" ".join(t for _,t in sorted(words))[:12000],"source_url":w.get("doi") or w.get("id") or "","relation_tags":["P_VS_NP","LITERATURE_DISCOVERY"],"review_state":"UNEXAMINED","scientific_authority":"DISCOVERY_METADATA_ONLY","claim_ceiling":"PAPER_METADATA_AND_CLAIMS_REQUIRE_SEPARATE_VALIDATION"})
    return out

def crossref(query,limit):
    url="https://api.crossref.org/works?"+urllib.parse.urlencode({"query.bibliographic":query,"rows":max(1,min(limit,50)),"select":"DOI,title,abstract,URL"})
    data=request_json(url,3);out=[]
    for x in (data.get("message") or {}).get("items",[]):
        tt=x.get("title") or [];title=tt[0] if isinstance(tt,list) and tt else str(tt or "");doi=str(x.get("DOI") or "");abstract=x.get("abstract") or ""
        out.append({"provider":"CROSSREF","archive_id":doi or x.get("URL"),"title":title,"text":str(abstract)[:12000],"source_url":x.get("URL") or ("https://doi.org/"+doi if doi else ""),"relation_tags":["P_VS_NP","LITERATURE_DISCOVERY"],"review_state":"UNEXAMINED","scientific_authority":"DISCOVERY_METADATA_ONLY","claim_ceiling":"PAPER_METADATA_AND_CLAIMS_REQUIRE_SEPARATE_VALIDATION"})
    return out

def arxiv_records(query,limit):
    smart=build_smart_arxiv_query(query);records,rc=remote_search(smart,limit=limit,page_size=min(limit,100));out=[]
    for r in records:
        out.append({"provider":"ARXIV","archive_id":r.get("arxiv_id"),"title":r.get("title") or "","text":r.get("abstract") or "","source_url":r.get("abs_url") or r.get("entry_id") or "","relation_tags":["P_VS_NP","LITERATURE_DISCOVERY"],"review_state":"UNEXAMINED","scientific_authority":"DISCOVERY_METADATA_ONLY","claim_ceiling":"PAPER_METADATA_AND_CLAIMS_REQUIRE_SEPARATE_VALIDATION","source_record_sha256":r.get("record_sha256")})
    rc=dict(rc);rc["natural_query"]=query;rc["compiled_query"]=smart;return out,rc

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);ap.add_argument("--prior-records");ap.add_argument("--max-queries",type=int,default=8);ap.add_argument("--per-source",type=int,default=12);a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True);assoc=fetch_json(ASSOC_URL)
    try:forge=fetch_json(KEYMASTER_FORGE_URL)
    except Exception as e:forge={"status":"UNAVAILABLE","error":type(e).__name__+":"+str(e)}
    prior=read_jsonl(a.prior_records) if a.prior_records else [];seeds=merge_query_seeds(assoc,forge,a.max_queries);all_records=[];receipts=[]
    for i,seed in enumerate(seeds):
        q=str(seed.get("query") or seed.get("focus") or "").strip()
        if not q:continue
        qr={"id":seed.get("id"),"query":q,"source":seed.get("source"),"arxiv":{"status":"UNRESOLVED"},"openalex":{"status":"UNRESOLVED"},"crossref":{"status":"UNRESOLVED"}}
        try:rows,rc=arxiv_records(q,a.per_source);all_records.extend(rows);qr["arxiv"]={"status":"PASS","records":len(rows),"receipt":rc}
        except Exception as e:qr["arxiv"]={"status":"UNAVAILABLE","error":type(e).__name__+":"+str(e)}
        time.sleep(2.5)
        try:rows=openalex(q,a.per_source);all_records.extend(rows);qr["openalex"]={"status":"PASS","records":len(rows)}
        except Exception as e:qr["openalex"]={"status":"UNAVAILABLE","error":type(e).__name__+":"+str(e)}
        time.sleep(2.5)
        try:rows=crossref(q,a.per_source);all_records.extend(rows);qr["crossref"]={"status":"PASS","records":len(rows)}
        except Exception as e:qr["crossref"]={"status":"UNAVAILABLE","error":type(e).__name__+":"+str(e)}
        receipts.append(qr)
        if i+1<len(seeds):time.sleep(2)
    current=merge_records([],all_records);novel=novel_records(prior,current);records=merge_records(prior,current)
    nodes,edges=build_graph(records,semantic_threshold=0.12,topk=6);src=out/"source-records.jsonl";write_jsonl(src,records);write_jsonl(out/"spider-nodes.jsonl",nodes);write_jsonl(out/"spider-edges.jsonl",edges);sr=spider_receipt(nodes,edges,records);write(out/"spider-receipt.json",sr)
    health={s:{"pass_queries":sum(1 for q in receipts if (q.get(s) or {}).get("status")=="PASS"),"unavailable_queries":sum(1 for q in receipts if (q.get(s) or {}).get("status")=="UNAVAILABLE"),"records_retrieved":sum(int((q.get(s) or {}).get("records") or 0) for q in receipts)} for s in ("arxiv","openalex","crossref")}
    live=any(v["pass_queries"] for v in health.values());status="PASS_NOVEL_SOURCES_ADDED" if novel else ("PASS_STALLED_NO_NOVEL_SOURCES" if live else "DEGRADED_ALL_DISCOVERY_SOURCES_UNAVAILABLE")
    latest={"schema":"janus.topa.pnp_autoresearch_cycle.v2","status":status,"source_commit":assoc.get("source_commit"),"query_seed_count":len(seeds),"query_receipts":receipts,"source_health":health,"keymaster_forge":{"url":KEYMASTER_FORGE_URL,"status":forge.get("status") if isinstance(forge,dict) else "UNAVAILABLE","state_sha256":forge.get("state_sha256") if isinstance(forge,dict) else None,"cycle_count":forge.get("cycle_count") if isinstance(forge,dict) else None,"target":forge.get("target") if isinstance(forge,dict) else None,"targeted_query_count":sum(1 for s in seeds if s.get("source")=="JANUS_KEYMASTER_AUTONOMOUS_FORGE"),"adaptive_query_rotation":True,"query_is_evidence":False,"query_grants_authority":False},"record_count":len(records),"retrieved_cycle_record_count":len(current),"novel_cycle_record_count":len(novel),"new_cycle_record_count":len(novel),"duplicate_cycle_record_count":max(0,len(current)-len(novel)),"prior_record_count":len(prior),"corpus_merge_policy":"APPEND_MERGE_HARD_DEDUPE__EMPTY_CYCLE_DOES_NOT_ERASE_HISTORY","node_count":len(nodes),"edge_count":len(edges),"source_records_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"spider_receipt":sr,"authority":{"truth":False,"proof":False,"scientific_claim_promotion":False,"fundamentum_mutation":False},"claim_ceiling":"DISCOVERY_AND_CANDIDATE_RELATIONS_ONLY__NO_PNP_CLAIM_PROMOTION"}
    write(out/"LATEST.json",latest);print(json.dumps(latest,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=="__main__":main()
