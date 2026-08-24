#!/usr/bin/env python3
import json,re,urllib.request,urllib.parse,hashlib
from pathlib import Path
UA='TOPA-retrieval-probe/0.2 (+https://github.com/Hawkar-usls/TOPA)'
OUT=Path('research/propaganda-defense/execution/RETRIEVAL_ARCHIVE_PROBE.v0.2.json')

def get(url,maxb=8*1024*1024):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'*/*'})
        with urllib.request.urlopen(req,timeout=35) as r:
            b=r.read(maxb+1)
            return {'ok':True,'requested_url':url,'final_url':r.geturl(),'status':getattr(r,'status',200),'content_type':r.headers.get('Content-Type'),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'body':b}
    except Exception as e:return {'ok':False,'requested_url':url,'error':f'{type(e).__name__}: {e}'}

def pub(x):return {k:v for k,v in x.items() if k!='body'}
out={'schema':'topa.propaganda_defense.retrieval_archive_probe.v0.2','date':'2026-08-24','scope':'BR03_SAME_PUBLICATION_ARCHIVE_TRANSPORT_DIAGNOSTIC_ONLY','probes':{}}

# Internet Archive advanced search for the journal volume/issue.
q='title:("American Journal of Semitic Languages and Literatures") AND year:[1926 TO 1928]'
ia='https://archive.org/advancedsearch.php?'+urllib.parse.urlencode({'q':q,'fl[]':['identifier','title','year','description'],'rows':50,'page':1,'output':'json'},doseq=True)
x=get(ia)
entry={'request':pub(x)}
if x.get('ok'):
    try:
        j=json.loads(x['body'].decode())
        entry['numFound']=j.get('response',{}).get('numFound')
        entry['docs']=j.get('response',{}).get('docs',[])
    except Exception as e:entry['parse_error']=str(e)
out['probes']['INTERNET_ARCHIVE']=entry

# Hathi HTML catalog search: diagnostic only.
look='The American journal of Semitic languages and literatures v.43 1926-1927'
hu='https://catalog.hathitrust.org/Search/Home?'+urllib.parse.urlencode({'lookfor':look,'type':'all','inst':''})
h=get(hu)
he={'request':pub(h)}
if h.get('ok'):
    s=h['body'].decode('utf-8','replace')
    he['contains_v43']=bool(re.search(r'v\.?\s*43|1926\s*[-–]\s*1927',s,re.I))
    he['handle_links']=list(dict.fromkeys(re.findall(r'https?://hdl\.handle\.net/2027/[^"\'<>\s&]+',s)))[:30]
    he['babel_links']=list(dict.fromkeys(re.findall(r'https?://babel\.hathitrust\.org/cgi/[^"\'<>\s]+',s)))[:30]
    he['record_links']=list(dict.fromkeys(re.findall(r'href=["\']([^"\']*(?:Record|RecordHome|pt\?id=)[^"\']*)',s,re.I)))[:50]
out['probes']['HATHITRUST_CATALOG']=he

# Hathi public Bibliographic API by print ISSN. Enumerate items and locate v43/1926-1927.
hapi='https://catalog.hathitrust.org/api/volumes/full/issn/1062-0516.json'
hb=get(hapi,maxb=20*1024*1024)
hbe={'request':pub(hb),'v43_candidates':[]}
if hb.get('ok'):
    try:
        j=json.loads(hb['body'].decode())
        hbe['top_keys']=list(j.keys()) if isinstance(j,dict) else []
        # API usually returns a records mapping. Walk recursively and collect dicts with item IDs + enum/chron text.
        def walk(o):
            if isinstance(o,dict):
                txt=' '.join(str(o.get(k,'')) for k in ('enumcron','enum_chron','item_enum_chron','rights','htid','item_id','orig'))
                ident=o.get('htid') or o.get('item_id') or o.get('itemid')
                if ident and re.search(r'v\.?\s*43|1926\s*[-–/]\s*1927|1926-1927',txt,re.I):
                    hbe['v43_candidates'].append({k:o.get(k) for k in o.keys() if k in ('htid','item_id','itemid','enumcron','enum_chron','item_enum_chron','rights','orig','usRightsString')})
                for v in o.values(): walk(v)
            elif isinstance(o,list):
                for v in o: walk(v)
        walk(j)
        # fallback: store compact record/item hints containing 43 or 1927 if exact field names differ
        raw=json.dumps(j,ensure_ascii=False)
        hbe['contains_1927']=('1927' in raw)
        hbe['contains_v43']=bool(re.search(r'v\\?\.?\s*43|v\.43',raw,re.I))
    except Exception as e:hbe['parse_error']=str(e)
out['probes']['HATHITRUST_BIB_API']=hbe

# For discovered Hathi v43 items, probe public meta/structure endpoints. No assumption that content API is unauthenticated.
htd=[]
for c in hbe.get('v43_candidates',[])[:10]:
    hid=c.get('htid') or c.get('item_id') or c.get('itemid')
    if not hid: continue
    item={'htid':hid,'catalog_fields':c}
    for resource in ('meta','structure'):
        u=f'https://babel.hathitrust.org/cgi/htd/{resource}/{urllib.parse.quote(str(hid),safe=".")}?v=2&alt=json'
        r=get(u,maxb=10*1024*1024)
        item[resource]=pub(r)
        if r.get('ok'):
            try:item[resource+'_json']=json.loads(r['body'].decode())
            except Exception as e:item[resource+'_parse_error']=str(e)
    htd.append(item)
out['probes']['HATHITRUST_DATA_API']=htd

# Google in-volume endpoint without Books API quota; diagnostic snippets/page IDs only.
q2=urllib.parse.quote('The Texts of the Battle of Kadesh')
g=get(f'https://www.google.com/books?id=2l5uKJXiO70C&jscmd=SearchWithinVolume2&q={q2}')
ge={'request':pub(g)}
if g.get('ok'):
    try:
        j=json.loads(g['body'].decode())
        ge['searchable']=j.get('searchable')
        arr=j.get('entry',j.get('results',[]))
        ge['results']=[{k:r.get(k) for k in ('page_id','page_number','page_url','snippet_text')} for r in arr[:50]]
    except Exception as e:ge['parse_error']=str(e)
out['probes']['GOOGLE_IN_VOLUME']=ge

OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('TOPA_RETRIEVAL_ARCHIVE_PROBE=COMPLETE')
print('HATHI_V43_CANDIDATES='+str(len(hbe.get('v43_candidates',[]))))
