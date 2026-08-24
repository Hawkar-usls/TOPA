#!/usr/bin/env python3
import json, urllib.request, urllib.parse, hashlib
from pathlib import Path

UA='TOPA-retrieval-probe/0.1 (+https://github.com/Hawkar-usls/TOPA)'
OUT=Path('research/propaganda-defense/execution/RETRIEVAL_TRANSPORT_PROBE.v0.1.json')

def fetch(url, timeout=30, maxb=20*1024*1024):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'*/*'})
        with urllib.request.urlopen(req,timeout=timeout) as r:
            b=r.read(maxb+1)
            return {'ok':True,'requested_url':url,'final_url':r.geturl(),'status':getattr(r,'status',200),'content_type':r.headers.get('Content-Type'),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'body':b}
    except Exception as e:
        return {'ok':False,'requested_url':url,'error':f'{type(e).__name__}: {e}'}

def pub(x): return {k:v for k,v in x.items() if k!='body'}

res={'schema':'topa.propaganda_defense.retrieval_transport_probe.v0.1','date':'2026-08-24','scope':'TRANSPORT_DIAGNOSTIC_ONLY_NO_SOURCE_OR_LOCUS_CHANGE','probes':{}}

# Same digitized journal volume already identified by Google Books, containing Wilson 1927 pp.266-287.
vol=fetch('https://www.googleapis.com/books/v1/volumes/2l5uKJXiO70C')
g={'metadata':pub(vol)}
if vol.get('ok'):
    try:
        j=json.loads(vol['body'].decode())
        ai=j.get('accessInfo',{})
        vi=j.get('volumeInfo',{})
        g['volume_identity']={'id':j.get('id'),'title':vi.get('title'),'publishedDate':vi.get('publishedDate'),'viewability':ai.get('viewability'),'publicDomain':ai.get('publicDomain'),'pdf':ai.get('pdf'),'epub':ai.get('epub'),'webReaderLink':ai.get('webReaderLink')}
        dl=(ai.get('pdf') or {}).get('downloadLink')
        if dl:
            d=fetch(dl,maxb=100*1024*1024)
            g['pdf_download']=pub(d)
        q=urllib.parse.quote('THE TEXTS OF THE BATTLE OF KADESH')
        sw=fetch(f'https://www.google.com/books?id=2l5uKJXiO70C&jscmd=SearchWithinVolume2&q={q}')
        g['search_within_volume']=pub(sw)
        if sw.get('ok'):
            try:
                sj=json.loads(sw['body'].decode())
                g['searchable']=sj.get('searchable')
                g['results']=[{k:r.get(k) for k in ('page_id','page_number','page_url','snippet_text')} for r in sj.get('entry',sj.get('results',[]))[:20]]
            except Exception as e: g['search_json_error']=str(e)
    except Exception as e:g['metadata_json_error']=str(e)
res['probes']['BR03_KADESH_GOOGLE_BOOKS']=g

# Secure pinned mirror of ORACC-derived Q003475. Authority remains ORACC; this is transport diagnostics only.
mirror='https://raw.githubusercontent.com/niekveldhuis/Digital-Assyriology/49b565bc91253d473580445c436e1fc02f2098a0/Scrape-Oracc/Output/rinap_rinap3_Q003475.txt'
m=fetch(mirror)
om={'mirror':pub(m)}
if m.get('ok'):
    s=m['body'].decode('utf-8','replace')
    om['validation']={'same_oracc_id':'rinap/rinap3/Q003475' in s,'same_text_name':'Sennacherib 001' in s,'lines_1_4':all(f',Sennacherib 001,{i},' in s for i in range(1,5)),'line_count':sum(1 for ln in s.splitlines() if 'rinap/rinap3/Q003475' in ln)}
res['probes']['BR04_ORACC_VERSIONED_MIRROR']=om

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print('TOPA_RETRIEVAL_TRANSPORT_PROBE=COMPLETE')
print('KADESH_GOOGLE_METADATA_OK='+str(bool(vol.get('ok'))).lower())
print('ORACC_PINNED_MIRROR_OK='+str(bool(m.get('ok'))).lower())
