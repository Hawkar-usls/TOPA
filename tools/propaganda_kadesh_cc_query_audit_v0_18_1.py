#!/usr/bin/env python3
"""Optimized reverse audit for TOPA BR03 Kadesh archive discovery.

The query grammar is validated once using documented positive controls. Only the
positive-control-passing query form is replayed on one representative Common
Crawl index per year (2019-2026) for the SAME two frozen Scribd numeric IDs.
Discovery metadata only; no WARC/source prose persisted; no coding unlock.
"""
from __future__ import annotations
import hashlib,json,re,urllib.error,urllib.parse,urllib.request
from pathlib import Path

OUT=Path('research/propaganda-defense/execution/KADESH_CC_QUERY_AUDIT.v0.18.1.json')
UA='TOPA-Kadesh-CC-Audit/0.18.1 (+https://github.com/Hawkar-usls/TOPA)'
COLL='https://index.commoncrawl.org/collinfo.json'
WAYBACK='https://web.archive.org/cdx/search/cdx'
IDS=['462138503','493951399']
YEARS=range(2019,2027)

def sha(b): return hashlib.sha256(b).hexdigest()
def get(u,timeout=12,maxb=4*1024*1024):
    req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'*/*'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            b=r.read(maxb+1)
            return {'ok':True,'status':getattr(r,'status',200),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type'),'bytes':min(len(b),maxb),'sha256':sha(b[:maxb]),'truncated':len(b)>maxb,'body':b[:maxb]}
    except urllib.error.HTTPError as e:
        try:b=e.read(32768)
        except:b=b''
        return {'ok':False,'status':e.code,'error':f'HTTPError: {e}','error_body_bytes':len(b),'error_body_sha256':sha(b)}
    except Exception as e:return {'ok':False,'error':f'{type(e).__name__}: {e}'}
def pub(x):return {k:v for k,v in x.items() if k!='body'}
def q(api,params):
    u=api+'?'+urllib.parse.urlencode(params)
    x=get(u)
    rec=[]
    if x.get('ok'):
        for line in x['body'].decode('utf-8','replace').splitlines():
            try:
                j=json.loads(line)
                if isinstance(j,dict):rec.append({k:j.get(k) for k in ('timestamp','url','status','mime','digest','length','offset','filename') if k in j})
            except:pass
    return {'url':u,'request':pub(x),'records':rec}
def selected(coll):
    out=[]
    for y in YEARS:
        xs=[]
        for x in coll:
            m=re.match(rf'CC-MAIN-{y}-(\d+)$',x.get('id',''))
            if m and x.get('cdx-api'):xs.append((abs(int(m.group(1))-26),x))
        if xs:
            x=sorted(xs,key=lambda z:z[0])[0][1];out.append({'id':x['id'],'api':x['cdx-api']})
    return out

def main():
    c=get(COLL,maxb=4*1024*1024); coll=[]
    if c.get('ok'):
        try:coll=json.loads(c['body'].decode())
        except:pass
    idxs=selected(coll)
    api='https://index.commoncrawl.org/CC-MAIN-2026-17-index'
    controls={
      'EXACT':q(api,{'url':'example.com','output':'json','limit':'1'}),
      'MATCHTYPE_PREFIX':q(api,{'url':'example.com/','output':'json','matchType':'prefix','limit':'5'}),
      'WILDCARD':q(api,{'url':'example.com/*','output':'json','limit':'5'})
    }
    passes={k:bool(v['request'].get('ok') and v['records']) for k,v in controls.items()}
    if passes['WILDCARD']: mode='WILDCARD'
    elif passes['MATCHTYPE_PREFIX']: mode='MATCHTYPE_PREFIX'
    elif passes['EXACT']: mode='EXACT_ONLY'
    else: mode='NONE'

    historical=[]; coordinates=[]
    for idx in idxs:
        health=q(idx['api'],{'url':'example.com','output':'json','limit':'1'})
        row={'index':idx,'health_pass':bool(health['request'].get('ok') and health['records']),'health':{'request':health['request'],'record_count':len(health['records'])},'targets':[]}
        for did in IDS:
            if mode=='WILDCARD': params={'url':f'www.scribd.com/document/{did}/*','output':'json','limit':'200'}
            elif mode=='MATCHTYPE_PREFIX': params={'url':f'https://www.scribd.com/document/{did}/','output':'json','matchType':'prefix','limit':'200'}
            elif mode=='EXACT_ONLY': params={'url':f'https://www.scribd.com/document/{did}/','output':'json','limit':'50'}
            else: params=None
            if params:
                z=q(idx['api'],params); rec=[r for r in z['records'] if did in (r.get('url') or '')]
            else:z={'request':{'ok':False,'error':'query grammar positive controls failed'},'records':[]};rec=[]
            row['targets'].append({'document_id':did,'request':z['request'],'record_count':len(rec),'records':rec[:50]})
            for r in rec:coordinates.append({'index_id':idx['id'],'document_id':did,**r})
        historical.append(row)

    params={'url':'www.scribd.com/document/493951399/*','output':'json','filter':['statuscode:200','mimetype:text/html'],'collapse':'digest','fl':'timestamp,original,statuscode,mimetype,digest,length','from':'2019','to':'2026'}
    wu=WAYBACK+'?'+urllib.parse.urlencode(params,doseq=True); w=get(wu,timeout=20); wr=[]
    if w.get('ok'):
        try:
            a=json.loads(w['body'].decode()); hdr=a[0] if a else [];wr=[dict(zip(hdr,x)) for x in a[1:]]
        except:pass

    health=sum(1 for r in historical if r['health_pass'])
    grammar=mode!='NONE' and passes.get('EXACT',False)
    out={'schema':'topa.propaganda_defense.kadesh_cc_query_audit.v0.18.1','date':'2026-08-24','status':'DIAGNOSTIC_ONLY','frozen':{'authority':'John A. Wilson / AJSL / University of Chicago / JSTOR','doi':'10.1086/370157','jstor_stable_id':'528771','locus':'THE POEM, journal pp.266-278; Record excluded','changed':False},'query_grammar_positive_controls':controls,'positive_control_pass':passes,'selected_target_mode':mode,'selected_indexes':idxs,'historical':historical,'candidate_coordinates':coordinates,'wayback_retry_493951399':{'request':pub(w),'capture_count':len(wr),'captures':wr[:30]},'summary':{'query_builder_validated':grammar,'healthy_historical_indexes':health,'historical_indexes_tested':len(idxs),'candidate_cdx_coordinates':len(coordinates),'wayback_493951399_capture_count':len(wr),'br03_retrieval_pass':False,'semantic_values_populated':0,'base_rate_coding_permission':False,'score_permission':False},'next_gate':'If candidate_cdx_coordinates > 0, run a separate bounded v0.19 WARC payload-integrity probe over only those coordinates; otherwise preserve this as a validated sampled negative and do not infer universal archive absence.','laws':['POSITIVE_CONTROL_PRECEDES_NEGATIVE_INFERENCE','ONE_INDEX_PER_YEAR_IS_SAMPLED_NOT_EXHAUSTIVE','CDX_COORDINATE != LOCUS_CONTENT','ARCHIVE_COPY != INDEPENDENT_WITNESS','NUMERIC_DOCUMENT_ID_FROZEN','NO_SOURCE_PROSE_PERSISTED','NO_SEMANTIC_CODING','NO_SCORE']}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('TOPA_KADESH_CC_QUERY_AUDIT_V0_18_1=COMPLETE')
    print('QUERY_BUILDER_VALIDATED='+str(grammar).lower())
    print('SELECTED_MODE='+mode)
    print(f'HISTORICAL_HEALTH={health}/{len(idxs)}')
    print('CANDIDATE_CDX_COORDINATES='+str(len(coordinates)))
    print('WAYBACK_493951399_CAPTURES='+str(len(wr)))
    print('BR03_RETRIEVAL_PASS=false')
    print('BASE_RATE_CODING_PERMISSION=false')
    print('SCORE_PERMISSION=false')
if __name__=='__main__':main()
