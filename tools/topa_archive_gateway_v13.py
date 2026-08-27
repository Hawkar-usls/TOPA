#!/usr/bin/env python3
"""TOPA Archive Gateway v1.3 — CIA STARGATE mobile-listing fallback.

The canonical collection URL currently loops redirects for Python/GitHub
runners while public indexed collection pages are served with the official
`mobile-app=true` view. This provider tries that official same-domain view and
harvests document pointers only. It does not fetch document bodies during the
broad survey.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import time
import urllib.parse
from pathlib import Path

import topa_archive_gateway_v12 as v12

base=v12.base
CIA_STARGATE_CANONICAL="https://www.cia.gov/readingroom/collection/stargate"
CIA_STARGATE_MOBILE="https://www.cia.gov/readingroom/collection/stargate?mobile-app=true&theme=false"


def canon(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"))

def page_url(page):
    return CIA_STARGATE_MOBILE + f"&page={page}"

def cia_collection_inventory(limit=100,max_pages=20,delay=0.35,start_page=0):
    rows=[];errors=[];seen=set();pages_scanned=0
    for page in range(start_page,start_page+max_pages):
        if len(rows)>=limit:break
        url=page_url(page)
        try:payload,meta=base.fetch(url)
        except Exception as exc:
            errors.append({"page":page,"url":url,"error":f"{type(exc).__name__}: {exc}"})
            if page==start_page:break
            continue
        pages_scanned+=1;p=v12.AnchorParser();p.feed(payload.decode("utf-8","replace"));before=len(rows)
        for href,label in p.items:
            absolute=urllib.parse.urljoin(CIA_STARGATE_CANONICAL,html.unescape(href));parsed=urllib.parse.urlparse(absolute)
            if parsed.hostname not in {"cia.gov","www.cia.gov","foia.cia.gov"}:continue
            if "/readingroom/document/" not in parsed.path.lower():continue
            aid=parsed.path.rstrip("/").split("/")[-1];key=aid.lower()
            if not aid or key in seen:continue
            seen.add(key)
            rows.append(base.archive_record("CIA",absolute,label or aid,archive_id=aid,extra={
                "collection":"STARGATE","collection_listing":url,"relation_tags":["CIA","STARGATE","COLLECTION_POINTER"],
                "retrieval_state":"POINTER_ONLY__FETCH_IF_SPIDER_CONNECTED","binary_policy":"NO_DOCUMENT_BYTES_FETCHED_DURING_BROAD_SURVEY"
            },source_meta=meta))
            if len(rows)>=limit:break
        if len(rows)==before and page>start_page:break
        if len(rows)<limit:time.sleep(max(0.2,delay))
    return rows,{"schema":"hawkar.topa.cia_stargate_inventory.receipt.v1.1","status":"PASS" if rows else "BLOCKED_OR_EMPTY","canonical_collection":CIA_STARGATE_CANONICAL,"listing_mode":"OFFICIAL_MOBILE_VIEW","records":len(rows),"pages_scanned":pages_scanned,"errors":errors,"retrieval_policy":"LISTING_POINTERS_ONLY__DEEP_FETCH_REQUIRES_SPIDER_SELECTION","record_stream_sha256":hashlib.sha256("".join(canon(r)+"\n" for r in rows).encode()).hexdigest(),"law":"COLLECTION_POINTER_IS_NOT_EVIDENCE"}

def ingest(providers,limit,expand_nara,cia_pages=20,cia_start_page=0):
    noncia=[p for p in providers if p!="cia"];rows=[];receipts={};errors=[]
    if noncia:
        existing,rc=v12.v11.ingest(noncia,limit,expand_nara);rows.extend(existing);receipts["other_providers"]=rc;errors.extend(rc.get("errors") or [])
    if "cia" in providers:
        cia,crc=cia_collection_inventory(limit,cia_pages,start_page=cia_start_page);rows.extend(cia);receipts["cia_collection"]=crc;errors.extend(crc.get("errors") or [])
    ded={(r.get("provider"),r.get("source_url"),r.get("archive_id")):r for r in rows};rows=sorted(ded.values(),key=lambda r:(r.get("provider",""),r.get("archive_id",""),r.get("source_url","")))
    return rows,{"schema":"hawkar.topa.archive_gateway.receipt.v1.3","status":"PASS" if rows else "FAIL_EMPTY","providers":providers,"records":len(rows),"provider_receipts":receipts,"errors":errors,"record_stream_sha256":hashlib.sha256("".join(canon(r)+"\n" for r in rows).encode()).hexdigest(),"survey_policy":"BROAD_METADATA_POINTERS__DEEP_FETCH_ONLY_AFTER_SPIDER_SELECTION"}

def self_test():
    assert page_url(5).startswith(CIA_STARGATE_CANONICAL) and "mobile-app=true" in page_url(5) and "page=5" in page_url(5)
    return {"schema":"hawkar.topa.archive_gateway.self_test.v1.3","status":"PASS","official_mobile_listing_fallback":True,"deep_fetch_during_survey":False}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True);sp.add_parser("self-test")
    q=sp.add_parser("ingest");q.add_argument("--providers",default="nara,cia,nsa,fbi");q.add_argument("--limit",type=int,default=100);q.add_argument("--expand-nara",action="store_true");q.add_argument("--cia-pages",type=int,default=20);q.add_argument("--cia-start-page",type=int,default=0);q.add_argument("--out",required=True);q.add_argument("--receipt",required=True)
    a=ap.parse_args()
    if a.cmd=="self-test":print(json.dumps(self_test(),indent=2));return 0
    rows,rc=ingest([x.strip().lower() for x in a.providers.split(",") if x.strip()],a.limit,a.expand_nara,a.cia_pages,a.cia_start_page);base.write_jsonl(Path(a.out),rows);Path(a.receipt).parent.mkdir(parents=True,exist_ok=True);Path(a.receipt).write_text(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True));return 0 if rows else 1
if __name__=="__main__":raise SystemExit(main())
