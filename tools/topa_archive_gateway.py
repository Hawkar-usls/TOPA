#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, html, json, re, time, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path

UA="TOPA-Archive-Gateway/1.0 (+https://github.com/Hawkar-usls/TOPA)"
NARA_BULK="https://www.archives.gov/research/catalog/catalog-bulk-downloads/uap-bulk-download"
NSA_UFO="https://www.nsa.gov/Helpful-Links/NSA-FOIA/Frequently-Requested-Information/Unidentified-Flying-Objects-UFOs/"
NSA_NO_RECORDS="https://www.nsa.gov/Helpful-Links/NSA-FOIA/Frequently-Requested-Information/UFO-and-Other-Paranormal-Information/"
FBI_UFO="https://vault.fbi.gov/UFO"
CIA_SEEDS=[
 "https://www.cia.gov/readingroom/document/0000015452",
 "https://www.cia.gov/readingroom/document/cia-rdp94-01353r002301740011-0",
 "https://www.cia.gov/readingroom/document/cia-rdp96-00791r000200280002-5",
 "https://www.cia.gov/readingroom/document/cia-rdp96-00791r000200300002-2",
 "https://www.cia.gov/readingroom/docs/CIA-RDP96-00791R000200270001-7.pdf",
 "https://www.cia.gov/readingroom/docs/CIA-RDP96-00789R003200240001-0.pdf",
]
OFFICIAL_HOSTS={"archives.gov","www.archives.gov","catalog.archives.gov","cia.gov","www.cia.gov","foia.cia.gov","nsa.gov","www.nsa.gov","fbi.gov","www.fbi.gov","vault.fbi.gov"}

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def canon(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def rec_hash(r):
    c={k:v for k,v in r.items() if k!="record_sha256"}
    return sha256_bytes(canon(c).encode())

def fetch(url, timeout=45.0):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        b=resp.read()
        return b,{"url":resp.geturl(),"status":getattr(resp,"status",200),"content_type":resp.headers.get("content-type",""),"sha256":sha256_bytes(b),"bytes":len(b)}

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self._title=[]; self._in_title=False
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            d=dict(attrs); href=d.get("href")
            if href:self.links.append((href,d.get("title","")))
        elif tag.lower()=="title": self._in_title=True
    def handle_endtag(self,tag):
        if tag.lower()=="title": self._in_title=False
    def handle_data(self,data):
        if self._in_title:self._title.append(data)
    @property
    def title(self): return " ".join(" ".join(self._title).split())

def html_text(payload):
    s=payload.decode("utf-8","replace")
    s=re.sub(r"(?is)<script.*?</script>|<style.*?</style>"," ",s)
    s=re.sub(r"(?s)<[^>]+>"," ",s)
    return " ".join(html.unescape(s).split())

def archive_record(provider,source_url,title,text="",archive_id="",extra=None,source_meta=None):
    rec={"schema":"hawkar.topa.archive_record.v1","provider":provider,"source_url":source_url,
      "archive_id":archive_id,"title":" ".join(title.split()),"text":" ".join(text.split())[:200000],
      "source_fetch":source_meta or {},"scientific_authority":"DISCOVERY_AND_ARCHIVAL_PROVENANCE_ONLY",
      "claim_ceiling":"ARCHIVED_SOURCE_OR_METADATA__NOT_PHYSICAL_TRUTH","review_state":"UNEXAMINED"}
    if extra: rec.update(extra)
    rec["record_sha256"]=rec_hash(rec); return rec

def parse_nara_bulk_page(payload, source_meta, limit=500):
    s=payload.decode("utf-8","replace")
    meta_urls=re.findall(r'href=["\']([^"\']*catalog-export-(\d+)\.json[^"\']*)["\']',s,re.I)
    zip_urls=re.findall(r'href=["\']([^"\']*?(\d+)(?:-[^"\']*)?\.zip[^"\']*)["\']',s,re.I)
    zips={}
    for href,naid in zip_urls: zips.setdefault(naid,urllib.parse.urljoin(NARA_BULK,html.unescape(href)))
    out=[]
    for href,naid in meta_urls[:limit]:
        u=urllib.parse.urljoin(NARA_BULK,html.unescape(href))
        out.append(archive_record("NARA",u,f"NARA UAP metadata NAID {naid}",archive_id=naid,
            extra={"collection":"UAP bulk downloads","landing_page":NARA_BULK,"binary_pointer":zips.get(naid),
                   "binary_policy":"POINTER_ONLY_UNLESS_EXPLICIT_SMALL_FETCH","relation_tags":["UAP","NARA","BULK_METADATA"]},
            source_meta=source_meta))
    return out

def expand_nara_metadata(record, timeout=45.0):
    b,m=fetch(record["source_url"],timeout)
    obj=json.loads(b.decode("utf-8")); rows=obj if isinstance(obj,list) else [obj]; out=[]
    for x in rows:
        if not isinstance(x,dict): continue
        title=str(x.get("title") or record["title"]); naid=str(x.get("naId") or record.get("archive_id") or "")
        text=" ".join(str(x.get(k) or "") for k in ["scopeAndContentNote","dateNote","arrangement"])
        creators=x.get("creators") or []
        agency="; ".join(str(c.get("heading") or "") for c in creators if isinstance(c,dict))
        extra={"collection":"NARA_UAP_BULK","agency":agency,"raw_metadata":x,
               "binary_pointer":record.get("binary_pointer"),"landing_page":record.get("landing_page"),
               "relation_tags":["UAP","NARA",agency] if agency else ["UAP","NARA"]}
        out.append(archive_record("NARA",record["source_url"],title,text,naid,extra,m))
    return out

def harvest_landing(provider,url,limit=100):
    b,m=fetch(url); p=LinkParser(); p.feed(b.decode("utf-8","replace")); text=html_text(b)
    out=[archive_record(provider,url,p.title or f"{provider} landing page",text[:12000],extra={"relation_tags":[provider,"LANDING_PAGE"]},source_meta=m)]
    seen=set()
    for href,_ in p.links:
        u=urllib.parse.urljoin(url,href); h=urllib.parse.urlparse(u).hostname or ""
        if h not in OFFICIAL_HOSTS or u in seen: continue
        seen.add(u)
        if provider=="FBI" and ("ufo" not in u.lower() and "vault.fbi.gov" not in u.lower()): continue
        if provider=="NSA" and not any(t in u.lower() for t in ["ufo","foia","paranormal"]): continue
        out.append(archive_record(provider,u,f"{provider} linked archival resource",extra={"parent_url":url,"relation_tags":[provider,"LINK"]}))
        if len(out)>=limit: break
    return out

def cia_seed_records(limit=100):
    out=[]
    for u in CIA_SEEDS[:limit]:
        try:
            b,m=fetch(u); ct=m.get("content_type","")
            if "pdf" in ct.lower() or u.lower().endswith(".pdf"):
                out.append(archive_record("CIA",u,u.rsplit("/",1)[-1],archive_id=u.rsplit("/",1)[-1].replace(".pdf",""),
                    extra={"content_type":ct,"binary_policy":"POINTER_AND_HASH_ONLY","relation_tags":["CIA","DECLASSIFIED"]},source_meta=m))
            else:
                p=LinkParser(); p.feed(b.decode("utf-8","replace"))
                out.append(archive_record("CIA",u,p.title or u.rsplit("/",1)[-1],html_text(b)[:50000],u.rsplit("/",1)[-1],
                    {"relation_tags":["CIA","DECLASSIFIED"]},m))
        except Exception as e:
            out.append(archive_record("CIA",u,u.rsplit("/",1)[-1],extra={"fetch_error":type(e).__name__,"relation_tags":["CIA","FAILED_FETCH"],
                "epistemic_note":"FAILED_FETCH_IS_NOT_PROOF_OF_ABSENCE"}))
        time.sleep(0.2)
    return out

def write_jsonl(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="\n") as f:
        for r in rows: f.write(canon(r)+"\n")

def ingest(providers,limit,expand_nara):
    rows=[]; errors=[]
    for pr in providers:
        try:
            if pr=="nara":
                b,m=fetch(NARA_BULK); base=parse_nara_bulk_page(b,m,limit)
                if expand_nara:
                    for r in base[:limit]:
                        try: rows.extend(expand_nara_metadata(r))
                        except Exception as e: r["expand_error"]=type(e).__name__; rows.append(r)
                else: rows.extend(base)
            elif pr=="cia": rows.extend(cia_seed_records(limit))
            elif pr=="nsa": rows.extend(harvest_landing("NSA",NSA_UFO,limit)); rows.extend(harvest_landing("NSA",NSA_NO_RECORDS,limit))
            elif pr=="fbi": rows.extend(harvest_landing("FBI",FBI_UFO,limit))
            else: errors.append({"provider":pr,"error":"UNKNOWN_PROVIDER"})
        except Exception as e: errors.append({"provider":pr,"error":f"{type(e).__name__}: {e}"})
    ded={}
    for r in rows: ded[(r.get("provider"),r.get("source_url"),r.get("archive_id"))]=r
    rows=sorted(ded.values(),key=lambda r:(r.get("provider",""),r.get("archive_id",""),r.get("source_url","")))
    receipt={"schema":"hawkar.topa.archive_gateway.receipt.v1","status":"PASS" if rows else "FAIL_EMPTY",
      "providers":providers,"records":len(rows),"errors":errors,
      "record_stream_sha256":sha256_bytes("".join(canon(r)+"\n" for r in rows).encode()),
      "storage_policy":"GIT_STORES_METADATA_TEXT_HASHES_POINTERS__HUGE_BINARIES_REMAIN_AT_OFFICIAL_SOURCE",
      "laws":["DECLASSIFICATION_IS_PROVENANCE_NOT_TRUTH","SEARCH_HIT_IS_NOT_EVIDENCE","ARCHIVED_REPORT_IS_NOT_DIRECT_OBSERVATION","FAILED_FETCH_IS_NOT_PROOF_OF_ABSENCE"]}
    return rows,receipt

def self_test():
    fixture=b'<html><head><title>NARA UAP</title></head><body><a href="https://catalog.archives.gov/medialz/bulk-downloads/uaps/JSON/catalog-export-488808322.json">m</a><a href="https://catalog.archives.gov/medialz/bulk-downloads/uaps/zips/488808322.zip">z</a></body></html>'
    rows=parse_nara_bulk_page(fixture,{"sha256":sha256_bytes(fixture),"url":"fixture"},10)
    assert len(rows)==1 and rows[0]["archive_id"]=="488808322" and rows[0]["binary_pointer"].endswith("488808322.zip")
    assert rows[0]["claim_ceiling"].startswith("ARCHIVED_SOURCE")
    return {"schema":"hawkar.topa.archive_gateway.self_test.v1","status":"PASS","nara_parser":True,"pointer_only_binary":True}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True); sp.add_parser("self-test")
    q=sp.add_parser("ingest"); q.add_argument("--providers",default="nara,cia,nsa,fbi"); q.add_argument("--limit",type=int,default=25)
    q.add_argument("--expand-nara",action="store_true"); q.add_argument("--out",required=True); q.add_argument("--receipt",required=True)
    a=ap.parse_args()
    if a.cmd=="self-test": print(json.dumps(self_test(),indent=2)); return 0
    rows,receipt=ingest([x.strip().lower() for x in a.providers.split(",") if x.strip()],a.limit,a.expand_nara)
    write_jsonl(Path(a.out),rows); Path(a.receipt).parent.mkdir(parents=True,exist_ok=True)
    Path(a.receipt).write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)); return 0 if rows else 1
if __name__=="__main__": raise SystemExit(main())
