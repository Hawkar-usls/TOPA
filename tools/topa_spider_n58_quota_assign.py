#!/usr/bin/env python3
"""Assign N58 SPIDER literature candidates to quota families one-publication-per-slot.

Research-routing utility only. A search hit or abstract never counts as a fully reviewed
primary source. This tool only prevents one publication from inflating multiple quotas.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any

LAWS=[
    "ONE_PUBLICATION_COUNTS_TOWARD_AT_MOST_ONE_QUOTA",
    "ABSTRACT_ONLY_IS_NOT_FULL_THEOREM_REVIEW",
    "SEARCH_HIT_IS_NOT_EVIDENCE",
    "SPIDER_IS_OBSERVER_AND_RESEARCHER_NOT_ALGORITHM_AUTHOR",
    "P_VS_NP_IS_OPEN",
]

def norm(x: Any)->str:
    return " ".join(re.findall(r"[a-z0-9]+", str(x or "").casefold()))

def phrase_hit(surface:str, alias:str)->bool:
    a=norm(alias)
    return bool(a) and (f" {a} " in f" {surface} ")

def load_rows(root:Path)->dict[str,dict[str,Any]]:
    rows={}
    for p in root.glob("*/arxiv-corpus.jsonl"):
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip(): continue
            r=json.loads(line); aid=str(r.get("arxiv_id") or "").strip()
            if not aid: continue
            prev=rows.get(aid)
            if prev is None or str(r.get("updated") or "")>=str(prev.get("updated") or ""):
                rows[aid]=r
    return rows

def candidate_edges(rows, cfg):
    aliases={f["id"]:f.get("aliases",[]) for f in cfg["quota_families"]}
    edges={}; details={}
    for aid,r in rows.items():
        surface=norm(" ".join([str(r.get("title") or ""),str(r.get("abstract") or "")," ".join(r.get("authors") or [])]))
        fams=[]; hits={}
        for fid,als in aliases.items():
            hs=sorted({a for a in als if phrase_hit(surface,a)})
            if hs:
                fams.append(fid); hits[fid]=hs
        if fams:
            edges[aid]=fams; details[aid]=hits
    return edges,details

def max_slot_matching(edges, quotas):
    slots=[]
    for fid,q in quotas.items():
        slots.extend((fid,i) for i in range(q))
    slot_owner={}
    # most constrained publications first helps deterministic matching
    papers=sorted(edges, key=lambda a:(len(edges[a]),a))
    def dfs(aid,seen):
        for fid in sorted(edges[aid]):
            for i in range(quotas[fid]):
                s=(fid,i)
                if s in seen: continue
                seen.add(s)
                old=slot_owner.get(s)
                if old is None or dfs(old,seen):
                    slot_owner[s]=aid
                    return True
        return False
    for aid in papers:
        dfs(aid,set())
    assignment={aid:fid for (fid,_),aid in slot_owner.items()}
    return assignment

def run(root,cfg):
    rows=load_rows(root)
    quotas={f["id"]:int(f["quota"]) for f in cfg["quota_families"]}
    edges,details=candidate_edges(rows,cfg)
    assign=max_slot_matching(edges,quotas)
    counts={fid:0 for fid in quotas}
    selected=[]
    for aid,fid in sorted(assign.items(), key=lambda kv:(kv[1],kv[0])):
        counts[fid]+=1; r=rows[aid]
        selected.append({
            "arxiv_id":aid,"assigned_quota":fid,"matched_quota_families":edges[aid],
            "match_details":details[aid],"title":r.get("title"),"authors":r.get("authors"),
            "published":r.get("published"),"updated":r.get("updated"),"doi":r.get("doi"),
            "abs_url":r.get("abs_url"),"pdf_url":r.get("pdf_url"),"abstract":r.get("abstract"),
            "theorem_statement":"PENDING_PRIMARY_TEXT_REVIEW__ABSTRACT_IS_DISCOVERY_CONTEXT_ONLY",
            "exact_model_assumptions":"PENDING_PRIMARY_TEXT_REVIEW",
            "resource_required":"PENDING_PRIMARY_TEXT_REVIEW",
            "candidate_janus_insertion_point":"PENDING_ROUTING_REVIEW",
            "applicability":"PENDING_PRIMARY_TEXT_REVIEW",
            "non_applicability":"PENDING_PRIMARY_TEXT_REVIEW",
            "primary_link":r.get("doi") or r.get("abs_url"),
            "review_status":"ABSTRACT_INDEXED_NOT_PRIMARY_TEXT_REVIEWED"
        })
    missing={fid:quotas[fid]-counts[fid] for fid in quotas if counts[fid]<quotas[fid]}
    return {
        "schema":"hawkar.topa.spider.n58.distinct_quota_ledger.v1","status":"PASS",
        "raw_unique_arxiv_records":len(rows),"matched_candidate_publications":len(edges),
        "assigned_distinct_publications":len(assign),"quota_targets":quotas,"quota_candidate_assignment":counts,
        "missing_candidate_slots":missing,"primary_sources_fully_reviewed":0,
        "primary_source_target":sum(quotas.values()),"candidate_records":selected,"laws":LAWS
    }

def self_test():
    cfg={"quota_families":[{"id":"A","quota":2,"aliases":["foo"]},{"id":"B","quota":1,"aliases":["bar"]}]}
    rows={
      "1":{"arxiv_id":"1","title":"foo bar","abstract":"","authors":[]},
      "2":{"arxiv_id":"2","title":"foo","abstract":"","authors":[]},
      "3":{"arxiv_id":"3","title":"bar","abstract":"","authors":[]},
    }
    e,_=candidate_edges(rows,cfg); a=max_slot_matching(e,{"A":2,"B":1})
    assert len(a)==3 and list(a.values()).count("A")==2 and list(a.values()).count("B")==1
    return {"status":"PASS","distinct":True,"laws":LAWS}

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("self-test")
    p=sub.add_parser("assign"); p.add_argument("--root",required=True); p.add_argument("--config",required=True); p.add_argument("--out",required=True)
    a=ap.parse_args()
    if a.cmd=="self-test": print(json.dumps(self_test(),indent=2)); return
    d=run(Path(a.root),json.loads(Path(a.config).read_text(encoding="utf-8")))
    Path(a.out).write_text(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2),encoding="utf-8")
    print(json.dumps({k:d[k] for k in ["status","raw_unique_arxiv_records","matched_candidate_publications","assigned_distinct_publications","quota_candidate_assignment","missing_candidate_slots"]},sort_keys=True))
if __name__=="__main__": main()
