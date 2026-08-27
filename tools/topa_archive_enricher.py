#!/usr/bin/env python3
"""TOPA selective archive enricher.

Consumes only SPIDER-selected archive pointers. Public HTML/JSON pages are
fetched and converted to bounded text/provenance. Large PDFs and other binary
objects are not mirrored into Git; discovered binary URLs remain pointers.

Scientific boundary: a record is fetched because it is connected, not because
its claim is true.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
from pathlib import Path

import topa_archive_gateway as base

ALLOWED_HOSTS=base.OFFICIAL_HOSTS
MAX_TEXT=180000


def canon(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def rh(r):
    c={k:v for k,v in r.items() if k!="record_sha256"}
    return hashlib.sha256(canon(c).encode("utf-8")).hexdigest()

def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():yield json.loads(line)

def write_jsonl(path,rows):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="\n") as f:
        for r in rows:f.write(canon(r)+"\n")

def enrich_record(record):
    r=dict(record);url=str(r.get("source_url") or "")
    host=urllib.parse.urlparse(url).hostname or ""
    if host not in ALLOWED_HOSTS:
        r["enrichment"]={"status":"REJECTED_NONOFFICIAL_HOST","host":host};r["record_sha256"]=rh(r);return r
    try:
        payload,meta=base.fetch(url)
    except Exception as exc:
        r["enrichment"]={"status":"FETCH_BLOCKED","error":f"{type(exc).__name__}: {exc}","epistemic_note":"FAILED_FETCH_IS_NOT_PROOF_OF_ABSENCE"};r["record_sha256"]=rh(r);return r
    ct=str(meta.get("content_type") or "").lower()
    enrichment={"status":"PASS","fetch":meta,"discovered_binary_pointers":[]}
    if "html" in ct or (not ct and payload.lstrip().startswith(b"<")):
        parser=base.LinkParser();parser.feed(payload.decode("utf-8","replace"))
        text=base.html_text(payload)[:MAX_TEXT]
        binaries=[]
        for href,_ in parser.links:
            u=urllib.parse.urljoin(url,href)
            path=urllib.parse.urlparse(u).path.lower()
            if path.endswith((".pdf",".zip",".tif",".tiff",".mp3",".wav",".mp4",".mov")):
                binaries.append(u)
        enrichment["discovered_binary_pointers"]=sorted(set(binaries))[:100]
        r["text"]=text
        if parser.title:r["title"]=parser.title
        r["retrieval_state"]="ENRICHED_PUBLIC_HTML"
    elif "json" in ct:
        try:
            obj=json.loads(payload.decode("utf-8"))
            text=canon(obj)[:MAX_TEXT]
        except Exception:
            text=payload.decode("utf-8","replace")[:MAX_TEXT]
        r["text"]=text;r["retrieval_state"]="ENRICHED_PUBLIC_JSON"
    else:
        # The selected URL itself is binary. Hash/size are legitimate provenance,
        # but do not commit bytes or pretend text was extracted.
        r["retrieval_state"]="BINARY_POINTER_HASHED_NOT_MIRRORED"
        enrichment["binary_pointer"]={"url":url,"sha256":meta.get("sha256"),"bytes":meta.get("bytes"),"content_type":meta.get("content_type")}
    enrichment["claim_ceiling"]="FETCHED_SOURCE_CONTENT_OR_POINTER__NOT_CLAIM_TRUTH"
    r["enrichment"]=enrichment;r["record_sha256"]=rh(r);return r

def run(rows):
    out=[enrich_record(r) for r in rows]
    counts={}
    for r in out:
        s=(r.get("enrichment") or {}).get("status","UNKNOWN");counts[s]=counts.get(s,0)+1
    receipt={"schema":"hawkar.topa.archive_enricher.receipt.v1","status":"PASS" if out else "FAIL_EMPTY","input_records":len(out),"enrichment_status_counts":counts,"stream_sha256":hashlib.sha256("".join(canon(r)+"\n" for r in out).encode()).hexdigest(),"laws":["FETCHED_BECAUSE_CONNECTED_IS_NOT_EVIDENCE","BINARY_POINTER_IS_NOT_EXTRACTED_TEXT","FAILED_FETCH_IS_NOT_PROOF_OF_ABSENCE"]}
    return out,receipt

def self_test():
    r={"provider":"X","source_url":"https://example.com/x","title":"x"};e=enrich_record(r)
    assert e["enrichment"]["status"]=="REJECTED_NONOFFICIAL_HOST"
    return {"schema":"hawkar.topa.archive_enricher.self_test.v1","status":"PASS","official_host_gate":True,"deep_fetch_requires_selection":True}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True);sp.add_parser("self-test")
    q=sp.add_parser("enrich");q.add_argument("--input",required=True);q.add_argument("--out",required=True);q.add_argument("--receipt",required=True)
    a=ap.parse_args()
    if a.cmd=="self-test":print(json.dumps(self_test(),indent=2));return 0
    rows,rc=run(list(read_jsonl(a.input)));write_jsonl(a.out,rows);Path(a.receipt).write_text(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(rc,ensure_ascii=False,indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
