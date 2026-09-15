#!/usr/bin/env python3
"""Diagnostic-only exact-scan transport probe for BR03 Kadesh via Academia.

Academia is NEVER treated as source authority or an independent witness. This
probe may only discover/fetch a transport copy of the already frozen Wilson 1927
article. No source prose is persisted; only URLs, hashes, lengths and marker
booleans. Any success still requires an explicit transport-mirror admission and
an authoritative 8/8 retrieval replay.
"""
from __future__ import annotations

import hashlib, html, io, json, re, ssl, urllib.parse, urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

OUT=Path("research/propaganda-defense/execution/KADESH_ACADEMIA_TRANSPORT_PROBE.v0.10.json")
PROFILE="https://independent.academia.edu/KimKevin1"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
TITLE="The Texts of the Battle of Kadesh"

def sha(b): return hashlib.sha256(b).hexdigest()
def op(): return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
def fetch(o,u,maxb=50*1024*1024):
    req=urllib.request.Request(u,headers={"User-Agent":UA,"Accept":"text/html,application/pdf,application/json,*/*;q=0.8","Accept-Language":"en-US,en;q=0.8","Referer":PROFILE})
    try:
        with o.open(req,timeout=45) as r:
            b=r.read(maxb+1); tr=len(b)>maxb; b=b[:maxb]
            return {"ok":True,"requested_url":u,"final_url":r.geturl(),"status":getattr(r,"status",200),"content_type":r.headers.get("Content-Type"),"content_disposition":r.headers.get("Content-Disposition"),"bytes":len(b),"sha256":sha(b),"truncated":tr,"body":b}
    except Exception as e:return {"ok":False,"requested_url":u,"error":f"{type(e).__name__}: {e}"}
def pub(x): return {k:v for k,v in x.items() if k!="body"}
def flatten(s):
    s=re.sub(r"(?is)<script.*?</script>|<style.*?</style>"," ",s); s=re.sub(r"(?s)<[^>]+>"," ",s); return re.sub(r"\s+"," ",html.unescape(s)).strip()
def same_academia(u):
    try:return urllib.parse.urlparse(u).netloc.endswith("academia.edu")
    except:return False

def discover_profile(text):
    # collect hrefs/data URLs in a bounded character neighborhood of the exact title
    lows=text.lower(); needle=TITLE.lower(); poss=[]; start=0
    while True:
        i=lows.find(needle,start)
        if i<0:break
        chunk=text[max(0,i-5000):min(len(text),i+5000)]
        for pat in [r'''href=["']([^"']+)["']''',r'''(?:url|download_url|paper_url)["']?\s*[:=]\s*["']([^"']+)["']''',r'''https?://[^"'<>\\\s]+''']:
            for m in re.finditer(pat,chunk,re.I):
                val=m.group(1) if m.groups() else m.group(0)
                u=urllib.parse.urljoin(PROFILE,html.unescape(val).replace("\\/","/"))
                if same_academia(u) and u not in poss: poss.append(u)
        start=i+len(needle)
    return poss[:80]

def page_identity(body):
    s=body.decode("utf-8","replace"); t=flatten(s); low=t.lower()
    return {"text_chars":len(t),"text_sha256":sha(t.encode()),"title":TITLE.lower() in low,"wilson":"john a. wilson" in low or "john a wilson" in low,"year_1927":"1927" in low,"page_282":"282" in t,"egyptian_camp":"in the egyptian camp" in low,"record":"the record" in low,"poem":"the poem" in low}

def main():
    o=op(); p=fetch(o,PROFILE,maxb=12*1024*1024); txt=p.get("body",b"").decode("utf-8","replace") if p.get("ok") else ""
    refs=discover_profile(txt)
    pages=[]; downloads=[]
    for u in refs[:40]:
        x=fetch(o,u,maxb=12*1024*1024); rec=pub(x)
        if x.get("ok"):
            b=x["body"]; ct=(x.get("content_type") or "").lower()
            if b.startswith(b"%PDF"):
                rec["pdf_magic"]=True; downloads.append(rec)
            elif "html" in ct:
                ident=page_identity(b); rec["identity"]=ident
                s=b.decode("utf-8","replace")
                cand=[]
                for m in re.finditer(r'''(?:href|src)=["']([^"']+)["']''',s,re.I):
                    v=html.unescape(m.group(1)); au=urllib.parse.urljoin(u,v)
                    lv=au.lower()
                    if same_academia(au) and any(k in lv for k in ("download","attachment","paper","pdf")) and au not in cand:cand.append(au)
                rec["discovered_download_candidates"]=cand[:30]
                for du in cand[:15]:
                    dx=fetch(o,du,maxb=60*1024*1024); dr=pub(dx); dr["pdf_magic"]=bool(dx.get("ok") and dx.get("body",b"").startswith(b"%PDF")); downloads.append(dr)
        pages.append(rec)
    exact_pages=[r for r in pages if r.get("identity",{}).get("title") and r.get("identity",{}).get("wilson") and r.get("identity",{}).get("year_1927")]
    pdfs=[d for d in downloads if d.get("pdf_magic")]
    out={"schema":"topa.propaganda_defense.kadesh_academia_transport_probe.v0.10","date":"2026-08-24","status":"DIAGNOSTIC_ONLY","frozen":{"authority":"John A. Wilson / AJSL / JSTOR-UChicago","doi":"10.1086/370157","jstor_stable_id":"528771","locus":"THE POEM, journal pp.266-278; Record excluded","changed":False},"mirror_policy":{"academia_is_authority":False,"academia_is_independent_witness":False,"source_root_count_if_admitted":1},"profile":pub(p),"discovered_refs":refs,"inspected_pages":pages,"download_attempts":downloads,"summary":{"exact_identity_page_count":len(exact_pages),"pdf_transport_count":len(pdfs),"can_consider_exact_scan_content_validation":bool(pdfs or exact_pages),"semantic_values_populated":0,"base_rate_coding_permission":False,"score_permission":False},"laws":["TRANSPORT_MIRROR != SOURCE_AUTHORITY","MIRROR_COPY != INDEPENDENT_WITNESS","PROFILE_SNIPPET != SOURCE_BYTES","EXACT_IDENTITY_REQUIRED_BEFORE_MIRROR_VALIDATION","NO_CODING_UNLOCK_FROM_DIAGNOSTIC"]}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print("TOPA_KADESH_ACADEMIA_TRANSPORT_PROBE_V0_10=COMPLETE"); print(f"REFS={len(refs)}"); print(f"EXACT_IDENTITY_PAGES={len(exact_pages)}"); print(f"PDF_TRANSPORTS={len(pdfs)}"); print("BASE_RATE_CODING_PERMISSION=false"); print("SCORE_PERMISSION=false")
if __name__=="__main__":main()
