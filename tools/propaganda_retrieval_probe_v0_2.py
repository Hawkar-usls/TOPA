#!/usr/bin/env python3
import json,re,urllib.request,urllib.parse,hashlib
from pathlib import Path
UA='TOPA-retrieval-probe/0.2 (+https://github.com/Hawkar-usls/TOPA)'
OUT=Path('research/propaganda-defense/execution/RETRIEVAL_ARCHIVE_PROBE.v0.2.json')

def get(url,maxb=5*1024*1024):
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

# Hathi catalog search. We only discover identifiers/links here; no page-content claim.
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
