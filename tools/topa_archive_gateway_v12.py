#!/usr/bin/env python3
"""TOPA Archive Gateway v1.2 — broad CIA STARGATE collection inventory.

The previous CIA provider used a small exact-ID seed list. V1.2 adds a polite
collection enumerator for the official CIA Reading Room STARGATE collection.
It harvests listing metadata only; document pages/PDFs are fetched later only
if SPIDER selects a pointer as connected.

This keeps survey broad and ephemeral while making deep retrieval selective.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import time
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

import topa_archive_gateway_v11 as v11

base = v11.base
CIA_STARGATE = "https://www.cia.gov/readingroom/collection/stargate"


def canon(o):
    return json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items=[]
        self._href=None
        self._buf=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            self._href=dict(attrs).get("href")
            self._buf=[]
    def handle_data(self,data):
        if self._href is not None:
            self._buf.append(data)
    def handle_endtag(self,tag):
        if tag.lower()=="a" and self._href is not None:
            text=" ".join(" ".join(self._buf).split())
            self.items.append((self._href,text))
            self._href=None; self._buf=[]


def cia_collection_inventory(limit=100, max_pages=20, delay=0.35):
    rows=[]; errors=[]; seen=set(); pages_scanned=0
    for page in range(max_pages):
        if len(rows)>=limit:
            break
        url=CIA_STARGATE + ("" if page==0 else f"?page={page}")
        try:
            payload,meta=base.fetch(url)
        except Exception as exc:
            errors.append({"page":page,"url":url,"error":f"{type(exc).__name__}: {exc}"})
            # A blocked page does not imply collection exhaustion.
            if page==0:
                break
            continue
        pages_scanned += 1
        parser=AnchorParser(); parser.feed(payload.decode("utf-8","replace"))
        before=len(rows)
        for href,label in parser.items:
            absolute=urllib.parse.urljoin(url,html.unescape(href))
            parsed=urllib.parse.urlparse(absolute)
            if parsed.hostname not in {"cia.gov","www.cia.gov","foia.cia.gov"}:
                continue
            marker="/readingroom/document/"
            if marker not in parsed.path.lower():
                continue
            archive_id=parsed.path.rstrip("/").split("/")[-1]
            key=archive_id.lower()
            if not archive_id or key in seen:
                continue
            seen.add(key)
            title=label or archive_id
            rec=base.archive_record(
                "CIA",absolute,title,archive_id=archive_id,
                extra={
                    "collection":"STARGATE",
                    "collection_listing":url,
                    "relation_tags":["CIA","STARGATE","COLLECTION_POINTER"],
                    "retrieval_state":"POINTER_ONLY__FETCH_IF_SPIDER_CONNECTED",
                    "binary_policy":"NO_DOCUMENT_BYTES_FETCHED_DURING_BROAD_SURVEY"
                },
                source_meta=meta
            )
            rows.append(rec)
            if len(rows)>=limit:
                break
        # Stop if a successfully fetched listing page contains no new documents.
        if len(rows)==before and page>0:
            break
        if page+1<max_pages and len(rows)<limit:
            time.sleep(max(0.2,delay))
    receipt={
        "schema":"hawkar.topa.cia_stargate_inventory.receipt.v1",
        "status":"PASS" if rows else "BLOCKED_OR_EMPTY",
        "collection":CIA_STARGATE,
        "records":len(rows),
        "pages_scanned":pages_scanned,
        "errors":errors,
        "retrieval_policy":"LISTING_POINTERS_ONLY__DEEP_FETCH_REQUIRES_SPIDER_SELECTION",
        "record_stream_sha256":hashlib.sha256("".join(canon(r)+"\n" for r in rows).encode("utf-8")).hexdigest(),
        "law":"COLLECTION_POINTER_IS_NOT_EVIDENCE"
    }
    return rows,receipt


def ingest(providers,limit,expand_nara,cia_pages=20):
    # Run the existing provider set except CIA; replace CIA seed-only mode with
    # broad official collection inventory. Exact seed knowledge remains in the
    # TOPA bootstrap web and therefore does not need to bias the archive survey.
    noncia=[p for p in providers if p!="cia"]
    rows=[]; receipts={}; errors=[]
    if noncia:
        existing,rc=v11.ingest(noncia,limit,expand_nara)
        rows.extend(existing); receipts["other_providers"]=rc
        errors.extend(rc.get("errors") or [])
    if "cia" in providers:
        cia,crc=cia_collection_inventory(limit=limit,max_pages=cia_pages)
        rows.extend(cia); receipts["cia_collection"]=crc
        errors.extend(crc.get("errors") or [])
    ded={}
    for r in rows:
        ded[(r.get("provider"),r.get("source_url"),r.get("archive_id"))]=r
    rows=sorted(ded.values(),key=lambda r:(r.get("provider",""),r.get("archive_id",""),r.get("source_url","")))
    rc={
        "schema":"hawkar.topa.archive_gateway.receipt.v1.2",
        "status":"PASS" if rows else "FAIL_EMPTY",
        "providers":providers,
        "records":len(rows),
        "provider_receipts":receipts,
        "errors":errors,
        "record_stream_sha256":hashlib.sha256("".join(canon(r)+"\n" for r in rows).encode("utf-8")).hexdigest(),
        "survey_policy":"BROAD_METADATA_POINTERS__DEEP_FETCH_ONLY_AFTER_SPIDER_SELECTION",
        "laws":["DECLASSIFICATION_IS_PROVENANCE_NOT_TRUTH","SEARCH_HIT_IS_NOT_EVIDENCE","FAILED_FETCH_IS_NOT_PROOF_OF_ABSENCE"]
    }
    return rows,rc


def self_test():
    fixture='''<html><body><a href="/readingroom/document/cia-rdp96-00791r000200300002-2">Summary Report</a><a href="/readingroom/collection/stargate?page=2">Next</a><a href="https://example.com/x">x</a></body></html>'''
    p=AnchorParser();p.feed(fixture)
    docs=[]
    for href,label in p.items:
        u=urllib.parse.urljoin(CIA_STARGATE,href)
        if "/readingroom/document/" in urllib.parse.urlparse(u).path.lower():
            docs.append((u,label))
    assert len(docs)==1 and docs[0][1]=="Summary Report"
    return {"schema":"hawkar.topa.archive_gateway.self_test.v1.2","status":"PASS","cia_collection_pointer_parser":True,"deep_fetch_during_survey":False}


def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True);sp.add_parser("self-test")
    q=sp.add_parser("ingest");q.add_argument("--providers",default="nara,cia,nsa,fbi");q.add_argument("--limit",type=int,default=100);q.add_argument("--expand-nara",action="store_true");q.add_argument("--cia-pages",type=int,default=20);q.add_argument("--out",required=True);q.add_argument("--receipt",required=True)
    a=ap.parse_args()
    if a.cmd=="self-test":
        print(json.dumps(self_test(),ensure_ascii=False,indent=2));return 0
    rows,receipt=ingest([x.strip().lower() for x in a.providers.split(",") if x.strip()],a.limit,a.expand_nara,a.cia_pages)
    base.write_jsonl(Path(a.out),rows)
    Path(a.receipt).parent.mkdir(parents=True,exist_ok=True)
    Path(a.receipt).write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True))
    return 0 if rows else 1


if __name__=="__main__":
    raise SystemExit(main())
