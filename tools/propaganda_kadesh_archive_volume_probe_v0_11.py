#!/usr/bin/env python3
"""Diagnostic-only whole-volume archival discovery for frozen BR03 Kadesh.

Searches Internet Archive metadata for scans of The American Journal of Semitic
Languages and Literatures, prioritizing volume 43 / 1926-1927 / ISSN 1062-0516.
For bounded candidates, fetches only machine-readable OCR/PDF representations
and records hashes/marker booleans; no source text is persisted.
"""
from __future__ import annotations

import hashlib, json, re, ssl, urllib.parse, urllib.request
from pathlib import Path

OUT=Path("research/propaganda-defense/execution/KADESH_ARCHIVE_VOLUME_PROBE.v0.11.json")
UA="TOPA-Kadesh-Archive-Volume-Probe/0.11 (+https://github.com/Hawkar-usls/TOPA)"
TITLE="the texts of the battle of kadesh"

def sha(b): return hashlib.sha256(b).hexdigest()
def fetch(url,maxb=40*1024*1024):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json,text/plain,application/pdf,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=45,context=ssl.create_default_context()) as r:
            b=r.read(maxb+1); tr=len(b)>maxb; b=b[:maxb]
            return {"ok":True,"requested_url":url,"final_url":r.geturl(),"status":getattr(r,"status",200),"content_type":r.headers.get("Content-Type"),"bytes":len(b),"sha256":sha(b),"truncated":tr,"body":b}
    except Exception as e:return {"ok":False,"requested_url":url,"error":f"{type(e).__name__}: {e}"}
def pub(x): return {k:v for k,v in x.items() if k!="body"}
def ia_search(q):
    params=[("q",q),("fl[]","identifier"),("fl[]","title"),("fl[]","year"),("fl[]","date"),("fl[]","volume"),("fl[]","description"),("fl[]","identifier-access"),("fl[]","external-identifier"),("rows","100"),("page","1"),("output","json")]
    u="https://archive.org/advancedsearch.php?"+urllib.parse.urlencode(params)
    x=fetch(u,maxb=8*1024*1024); docs=[]
    if x.get("ok"):
        try:docs=json.loads(x["body"].decode("utf-8","replace")).get("response",{}).get("docs",[])
        except:pass
    return pub(x),docs

def score_doc(d):
    s=" ".join(str(d.get(k,"")) for k in ("title","year","date","volume","description","external-identifier")).lower()
    score=0
    if "american journal of semitic languages" in s:score+=5
    if "1062-0516" in s:score+=4
    if re.search(r"\bv\.?\s*43\b|\bvol(?:ume)?\.?\s*43\b",s):score+=5
    if "1926" in s or "1927" in s:score+=2
    return score

def marker_state(text):
    low=re.sub(r"\s+"," ",text).lower()
    return {"article_title":TITLE in low,"john_wilson":"john a. wilson" in low or "john a wilson" in low,"journal_name":"american journal of semitic languages" in low,"page_266":bool(re.search(r"(?:^|\D)266(?:\D|$)",low)),"page_277":bool(re.search(r"(?:^|\D)277(?:\D|$)",low)),"page_278":bool(re.search(r"(?:^|\D)278(?:\D|$)",low)),"the_poem":"the poem" in low,"the_record":"the record" in low,"council_urges_peace":"council urges peace" in low}

def main():
    queries=[
      'identifier-access:"urn:issn:1062-0516"',
      '"1062-0516"',
      'title:("American Journal of Semitic Languages and Literatures")',
      'title:("American Journal" AND "Semitic Languages")',
      '("American Journal of Semitic Languages") AND (1927 OR 1926)',
    ]
    searches=[]; pool={}
    for q in queries:
        req,docs=ia_search(q); searches.append({"query":q,"request":req,"num_docs":len(docs)})
        for d in docs:
            i=d.get("identifier")
            if i:pool[i]=d
    ranked=sorted(({"score":score_doc(d),**d} for d in pool.values()),key=lambda d:(-d["score"],str(d.get("identifier"))))
    candidates=[]
    for d in ranked[:20]:
        ident=d["identifier"]; mx=fetch(f"https://archive.org/metadata/{urllib.parse.quote(ident)}",maxb=10*1024*1024); rec={"search_doc":d,"metadata_request":pub(mx),"representations":[]}
        files=[]
        if mx.get("ok"):
            try:files=json.loads(mx["body"].decode("utf-8","replace")).get("files",[])
            except:pass
        names=[f.get("name") for f in files if f.get("name")]
        # Prefer OCR-derived text, then searchable PDF; bounded to three representations.
        preferred=[n for n in names if n.endswith(('_djvu.txt','_text.pdf','_bw.pdf','.pdf'))]
        preferred=sorted(preferred,key=lambda n:(0 if n.endswith('_djvu.txt') else 1,len(n)))[:3]
        for name in preferred:
            u=f"https://archive.org/download/{urllib.parse.quote(ident)}/{urllib.parse.quote(name)}"; x=fetch(u,maxb=60*1024*1024); rr=pub(x)
            if x.get("ok"):
                b=x["body"]; ispdf=b.startswith(b"%PDF"); rr["pdf_magic"]=ispdf
                if not ispdf:
                    t=b.decode("utf-8","replace"); rr["normalized_text_sha256"]=sha(re.sub(r"\s+"," ",t).encode()); rr["markers"]=marker_state(t); rr["content_candidate"]=rr["markers"]["article_title"] and rr["markers"]["john_wilson"] and rr["markers"]["page_266"] and rr["markers"]["page_278"] and rr["markers"]["the_record"]
                else:rr["content_candidate"]=False
            rec["representations"].append(rr)
        rec["content_candidate"] = any(r.get("content_candidate") for r in rec["representations"])
        candidates.append(rec)
    hits=[c for c in candidates if c.get("content_candidate")]
    out={"schema":"topa.propaganda_defense.kadesh_archive_volume_probe.v0.11","date":"2026-08-24","status":"DIAGNOSTIC_ONLY","frozen":{"authority":"John A. Wilson, AJSL 43.4 (1927)","doi":"10.1086/370157","jstor_stable_id":"528771","locus":"THE POEM, journal pp.266-278; Record excluded","changed":False},"searches":searches,"ranked_documents":ranked[:50],"inspected_candidates":candidates,"summary":{"unique_archive_items":len(pool),"inspected_candidates":len(candidates),"content_candidate_count":len(hits),"candidate_identifiers":[c["search_doc"].get("identifier") for c in hits],"semantic_values_populated":0,"base_rate_coding_permission":False,"score_permission":False},"laws":["WHOLE_VOLUME_SCAN_CAN_BE_SAME_PUBLICATION_TRANSPORT","ARCHIVE_ITEM != INDEPENDENT_WITNESS","ARTICLE_IDENTITY_AND_BOUNDARY_REQUIRED","OCR_HASH != ORIGINAL_SCAN_HASH","NO_CODING_UNLOCK_FROM_DIAGNOSTIC"]}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print("TOPA_KADESH_ARCHIVE_VOLUME_PROBE_V0_11=COMPLETE"); print(f"UNIQUE_ARCHIVE_ITEMS={len(pool)}"); print(f"CONTENT_CANDIDATES={len(hits)}"); print("CANDIDATE_IDS="+(",".join(c["search_doc"].get("identifier") for c in hits) if hits else "NONE")); print("BASE_RATE_CODING_PERMISSION=false"); print("SCORE_PERMISSION=false")
if __name__=="__main__":main()
