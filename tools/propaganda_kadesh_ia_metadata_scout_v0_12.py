#!/usr/bin/env python3
import json,re,ssl,urllib.parse,urllib.request
from pathlib import Path
OUT=Path('research/propaganda-defense/execution/KADESH_IA_METADATA_SCOUT.v0.12.json')
UA='TOPA-Kadesh-IA-Metadata-Scout/0.12 (+https://github.com/Hawkar-usls/TOPA)'
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=20,context=ssl.create_default_context()) as r:
            b=r.read(8*1024*1024); return {'ok':True,'status':getattr(r,'status',200),'bytes':len(b),'body':b}
    except Exception as e:return {'ok':False,'error':f'{type(e).__name__}: {e}'}
def search(q):
    p=[('q',q),('fl[]','identifier'),('fl[]','title'),('fl[]','year'),('fl[]','date'),('fl[]','volume'),('fl[]','description'),('fl[]','identifier-access'),('fl[]','external-identifier'),('rows','100'),('page','1'),('output','json')]
    u='https://archive.org/advancedsearch.php?'+urllib.parse.urlencode(p); x=get(u); docs=[]; nf=None
    if x.get('ok'):
        try:
            j=json.loads(x['body'].decode()); docs=j.get('response',{}).get('docs',[]); nf=j.get('response',{}).get('numFound')
        except Exception: pass
    return {'query':q,'ok':x.get('ok',False),'error':x.get('error'),'numFound':nf,'docs':docs}
def score(d):
    s=' '.join(str(d.get(k,'')) for k in ('title','year','date','volume','description','external-identifier','identifier-access')).lower(); n=0
    if 'american journal of semitic languages' in s:n+=8
    if '1062-0516' in s:n+=6
    if re.search(r'\bv\.?\s*43\b|\bvol(?:ume)?\.?\s*43\b',s):n+=8
    if '1926' in s:n+=2
    if '1927' in s:n+=3
    if '1928' in s:n+=1
    return n
qs=['"1062-0516"','title:("American Journal of Semitic Languages and Literatures")','title:("American Journal" AND "Semitic Languages")','"American Journal of Semitic Languages"','("Semitic Languages and Literatures") AND (1926 OR 1927 OR 1928)']
runs=[search(q) for q in qs]; pool={}
for r in runs:
    for d in r['docs']:
        if d.get('identifier'):pool[d['identifier']]=d
ranked=sorted([{'score':score(d),**d} for d in pool.values()],key=lambda x:(-x['score'],str(x.get('identifier'))))
likely=[d for d in ranked if d['score']>=8][:30]
out={'schema':'topa.propaganda_defense.kadesh_ia_metadata_scout.v0.12','date':'2026-08-24','status':'DIAGNOSTIC_ONLY','frozen':{'authority':'John A. Wilson / AJSL 43.4 (1927)','doi':'10.1086/370157','locus':'THE POEM, journal pp.266-278; Record excluded','changed':False},'query_runs':runs,'unique_items':len(pool),'top_ranked':ranked[:50],'likely_same_journal_items':likely,'summary':{'likely_count':len(likely),'likely_ids':[d.get('identifier') for d in likely],'semantic_values_populated':0,'base_rate_coding_permission':False,'score_permission':False}}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('TOPA_KADESH_IA_METADATA_SCOUT_V0_12=COMPLETE');print('UNIQUE_ITEMS='+str(len(pool)));print('LIKELY_COUNT='+str(len(likely)));print('LIKELY_IDS='+(','.join(d.get('identifier') for d in likely) if likely else 'NONE'));print('BASE_RATE_CODING_PERMISSION=false');print('SCORE_PERMISSION=false')
