#!/usr/bin/env python3
"""Targeted IA serial/collection discovery for AJSL volume 43 issue 4 (1927-07).
Metadata-only until an exact issue identifier is discovered. No source text is persisted.
"""
import json,re,ssl,urllib.parse,urllib.request
from pathlib import Path
OUT=Path('research/propaganda-defense/execution/KADESH_IA_SERIAL_TARGET.v0.13.json')
COLL='pub_american-journal-of-semitic-languages-and-literatures'
UA='TOPA-Kadesh-IA-Serial-Target/0.13 (+https://github.com/Hawkar-usls/TOPA)'
def get(u,maxb=10*1024*1024):
    req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=25,context=ssl.create_default_context()) as r:
            b=r.read(maxb);return {'ok':True,'status':getattr(r,'status',200),'bytes':len(b),'final_url':r.geturl(),'body':b}
    except Exception as e:return {'ok':False,'error':f'{type(e).__name__}: {e}'}
def pub(x):return {k:v for k,v in x.items() if k!='body'}
def search(q):
    p=[('q',q),('fl[]','identifier'),('fl[]','title'),('fl[]','date'),('fl[]','year'),('fl[]','volume'),('fl[]','description'),('fl[]','collection'),('rows','200'),('page','1'),('output','json')]
    u='https://archive.org/advancedsearch.php?'+urllib.parse.urlencode(p);x=get(u);resp={}
    if x.get('ok'):
        try:resp=json.loads(x['body'].decode()).get('response',{})
        except:pass
    return {'query':q,'request':pub(x),'numFound':resp.get('numFound'),'docs':resp.get('docs',[])}
meta=get(f'https://archive.org/metadata/{COLL}'); meta_obj={}
if meta.get('ok'):
    try:meta_obj=json.loads(meta['body'].decode())
    except:pass
queries=[
 f'collection:{COLL} AND date:[1926-01-01 TO 1928-12-31]',
 f'collection:{COLL} AND year:1927',
 f'collection:{COLL} AND (volume:43 OR title:(43))',
 f'identifier:{COLL}* AND 1927',
 'identifier:(sim_american-journal-of-semitic-languages-and-literatures*) AND year:1927'
]
runs=[search(q) for q in queries];pool={}
for r in runs:
    for d in r['docs']:
        if d.get('identifier'):pool[d['identifier']]=d
def score(d):
    s=' '.join(str(d.get(k,'')) for k in ('identifier','title','date','year','volume','description')).lower();n=0
    if '1927' in s:n+=4
    if re.search(r'(^|[^0-9])43([^0-9]|$)',s):n+=5
    if re.search(r'(^|[^0-9])4([^0-9]|$)',s):n+=2
    if '07' in s or 'jul' in s:n+=2
    if 'american-journal-of-semitic' in s:n+=5
    return n
ranked=sorted([{'score':score(d),**d} for d in pool.values()],key=lambda x:(-x['score'],str(x.get('identifier'))))
exactish=[d for d in ranked if d['score']>=12][:30]
out={'schema':'topa.propaganda_defense.kadesh_ia_serial_target.v0.13','date':'2026-08-24','status':'DIAGNOSTIC_ONLY','frozen':{'authority':'John A. Wilson / AJSL 43.4 Jul 1927','doi':'10.1086/370157','locus':'THE POEM, pp.266-278; Record excluded','changed':False},'collection_identifier':COLL,'collection_metadata_request':pub(meta),'collection_metadata':meta_obj.get('metadata',{}),'collection_file_count':len(meta_obj.get('files',[])),'search_runs':runs,'unique_children':len(pool),'ranked_children':ranked[:80],'exactish_candidates':exactish,'summary':{'candidate_count':len(exactish),'candidate_ids':[d.get('identifier') for d in exactish],'semantic_values_populated':0,'base_rate_coding_permission':False,'score_permission':False}}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('TOPA_KADESH_IA_SERIAL_TARGET_V0_13=COMPLETE');print('COLLECTION_FILES='+str(len(meta_obj.get('files',[]))));print('UNIQUE_CHILDREN='+str(len(pool)));print('CANDIDATES='+str(len(exactish)));print('CANDIDATE_IDS='+(','.join(d.get('identifier') for d in exactish) if exactish else 'NONE'));print('BASE_RATE_CODING_PERMISSION=false');print('SCORE_PERMISSION=false')
