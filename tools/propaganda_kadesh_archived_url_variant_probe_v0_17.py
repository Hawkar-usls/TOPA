#!/usr/bin/env python3
"""Diagnostic-only archived URL-variant probe for frozen BR03 Kadesh.

Searches Wayback CDX and recent Common Crawl prefix captures for the SAME two
Scribd numeric document IDs. Slug changes are allowed; document identity is not.
No source prose is persisted. Only archive coordinates, hashes, lengths, identity
and frozen boundary booleans are recorded.
"""
from __future__ import annotations
import gzip,hashlib,html,json,re,ssl,urllib.parse,urllib.request
from pathlib import Path
OUT=Path('research/propaganda-defense/execution/KADESH_ARCHIVED_URL_VARIANT_PROBE.v0.17.json')
UA='TOPA-Kadesh-Archived-Variant-Probe/0.17 (+https://github.com/Hawkar-usls/TOPA)'
IDS=['462138503','493951399']
COLLINFO='https://index.commoncrawl.org/collinfo.json'
DATA='https://data.commoncrawl.org/'

def sha(b):return hashlib.sha256(b).hexdigest()
def get(u,headers=None,maxb=20*1024*1024,timeout=45):
 h={'User-Agent':UA,'Accept':'*/*'};h.update(headers or {})
 try:
  req=urllib.request.Request(u,headers=h)
  with urllib.request.urlopen(req,timeout=timeout,context=ssl.create_default_context()) as r:
   b=r.read(maxb+1);tr=len(b)>maxb;b=b[:maxb]
   return {'ok':True,'status':getattr(r,'status',200),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type'),'content_range':r.headers.get('Content-Range'),'bytes':len(b),'sha256':sha(b),'truncated':tr,'body':b}
 except Exception as e:return {'ok':False,'error':f'{type(e).__name__}: {e}'}
def pub(x):return {k:v for k,v in x.items() if k!='body'}
def norm(b):
 s=b.decode('utf-8','replace');s=re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m.group(1),16)),s);s=s.replace('\\/','/').replace('\\n',' ');s=re.sub(r'(?s)<[^>]+>',' ',s);return re.sub(r'\s+',' ',html.unescape(s)).strip()
def near(t,p,pat,r=2200):return bool(re.search(pat,t[max(0,p-r):min(len(t),p+r)],re.I))
def analyze(t):
 low=t.lower(); nums=sorted({int(x) for x in re.findall(r'(?<!\d)(26[6-9]|27\d|28[0-7])(?!\d)',t)})
 pos=lambda n:[m.start() for m in re.finditer(rf'(?<!\d){n}(?!\d)',t)]
 p266,p277,p278,p287=map(pos,(266,277,278,287))
 ident=('the texts of the battle of kadesh' in low and ('john a. wilson' in low or 'john a wilson' in low or 'johna. wilson' in low) and 'american journal of semitic languages and literatures' in low and '1927' in low and ('university of chicago' in low or 'jstor' in low))
 geom=(any(near(t,p,r'the poem|texts of the battle of kadesh') for p in p266) and any(near(t,p,r'the council urges peace|end of poem') for p in p277) and any(near(t,p,r'the record',1800) for p in p278) and any(near(t,p,r'comment on the texts|prisoners presented to amon') for p in p287))
 markers={'the_poem':'the poem' in low,'council_urges_peace':'the council urges peace' in low,'the_record':'the record' in low,'comment_on_the_texts':'comment on the texts' in low}
 content=len(t)>=35000 and all(markers.values()) and len(nums)>=18
 return {'normalized_chars':len(t),'normalized_sha256':sha(t.encode()),'identity_ok':ident,'geometry_ok':geom,'content_ok':content,'candidate_content_sufficient':ident and geom and content,'page_numbers_seen_266_287':nums,'coverage_count':len(nums),'markers':markers,'p266_ok':any(near(t,p,r'the poem|texts of the battle of kadesh') for p in p266),'p277_ok':any(near(t,p,r'the council urges peace|end of poem') for p in p277),'p278_ok':any(near(t,p,r'the record',1800) for p in p278),'p287_ok':any(near(t,p,r'comment on the texts|prisoners presented to amon') for p in p287)}
def wayback(docid):
 wildcard=f'www.scribd.com/document/{docid}/*';q=urllib.parse.urlencode({'url':wildcard,'output':'json','filter':['statuscode:200','mimetype:text/html'],'collapse':'digest','fl':'timestamp,original,statuscode,mimetype,digest,length','from':'2019','to':'2026'},doseq=True);x=get('https://web.archive.org/cdx/search/cdx?'+q,maxb=8*1024*1024);caps=[]
 if x.get('ok'):
  try:
   a=json.loads(x['body'].decode()); hdr=a[0] if a else [];caps=[dict(zip(hdr,row)) for row in a[1:]]
  except:pass
 out=[]
 for c in caps[-12:]:
  u=f"https://web.archive.org/web/{c['timestamp']}id_/{c['original']}";s=get(u,maxb=8*1024*1024);r={'cdx':c,'snapshot':pub(s)}
  if s.get('ok'):r['analysis']=analyze(norm(s['body']))
  out.append(r)
 return pub(x),caps,out
def cc_indexes():
 x=get(COLLINFO,maxb=4*1024*1024);arr=[]
 if x.get('ok'):
  try:arr=json.loads(x['body'].decode())[:8]
  except:pass
 return pub(x),[{'id':i.get('id'),'api':i.get('cdx-api')} for i in arr if i.get('id') and i.get('cdx-api')]
def cc(docid,indexes):
 rows=[]
 for idx in indexes:
  base=f'https://www.scribd.com/document/{docid}/';q=urllib.parse.urlencode({'url':base,'output':'json','matchType':'prefix','filter':'status:200'});x=get(idx['api']+'?'+q,maxb=8*1024*1024);recs=[]
  if x.get('ok'):
   for line in x['body'].decode('utf-8','replace').splitlines():
    try:
     r=json.loads(line)
     if all(k in r for k in ('filename','offset','length')):recs.append(r)
    except:pass
  entry={'index':idx,'request':pub(x),'records':[]}
  for r in recs[:6]:
   try:o=int(r['offset']);l=int(r['length'])
   except:continue
   y=get(DATA+r['filename'],headers={'Range':f'bytes={o}-{o+l-1}'},maxb=l+1024,timeout=60);wr={'cdx':{k:r.get(k) for k in ('url','timestamp','digest','filename','offset','length')},'range':pub(y)}
   if y.get('ok'):
    try:
     m=gzip.decompress(y['body']);a=re.split(br'\r?\n\r?\n',m,maxsplit=1);b=re.split(br'\r?\n\r?\n',a[1],maxsplit=1) if len(a)==2 else []
     if len(b)==2:
      p=b[1];wr['payload_sha256']=sha(p);wr['payload_bytes']=len(p);wr['analysis']=analyze(norm(p))
    except Exception as e:wr['parse_error']=f'{type(e).__name__}: {e}'
   entry['records'].append(wr)
  rows.append(entry)
 return rows
def main():
 coll,idxs=cc_indexes();targets=[];strong=[]
 for did in IDS:
  wreq,wcaps,wrows=wayback(did);ccrows=cc(did,idxs);tr={'document_id':did,'wayback_request':wreq,'wayback_capture_count':len(wcaps),'wayback_rows':wrows,'commoncrawl_prefix_rows':ccrows};targets.append(tr)
  for r in wrows:
   if r.get('analysis',{}).get('candidate_content_sufficient'):strong.append({'archive':'WAYBACK','document_id':did,'coordinate':r['cdx'],'analysis':r['analysis'],'snapshot_sha256':r['snapshot'].get('sha256')})
  for e in ccrows:
   for r in e['records']:
    if r.get('analysis',{}).get('candidate_content_sufficient'):strong.append({'archive':'COMMON_CRAWL','document_id':did,'index_id':e['index']['id'],'coordinate':r['cdx'],'analysis':r['analysis'],'payload_sha256':r.get('payload_sha256')})
 out={'schema':'topa.propaganda_defense.kadesh_archived_url_variant_probe.v0.17','date':'2026-08-24','status':'DIAGNOSTIC_ONLY','frozen':{'authority':'John A. Wilson / AJSL / UChicago / JSTOR','doi':'10.1086/370157','jstor_stable_id':'528771','locus':'THE POEM, journal pp.266-278; Record excluded','changed':False},'archive_firewall':{'wayback_authority':0,'commoncrawl_authority':0,'scribd_authority':0,'archive_adds_source_root':False,'mirror_adds_source_root':False,'source_root_count_if_admitted':1},'commoncrawl_collinfo':coll,'commoncrawl_indexes':idxs,'targets':targets,'summary':{'strong_candidate_count':len(strong),'strong_candidates':strong,'archived_transport_admission_review_eligible':bool(strong),'br03_retrieval_pass':False,'semantic_values_populated':0,'base_rate_coding_permission':False,'score_permission':False},'laws':['NUMERIC_DOCUMENT_ID_FROZEN_SLUG_MAY_VARY','ARCHIVE_SNAPSHOT != SOURCE_AUTHORITY','ARCHIVE_COPY != INDEPENDENT_WITNESS','FULL_LOCUS_GEOMETRY_REQUIRED','DIAGNOSTIC_PASS != BR03_RETRIEVAL_PASS']}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print('TOPA_KADESH_ARCHIVED_URL_VARIANT_PROBE_V0_17=COMPLETE');print('STRONG_CANDIDATES='+str(len(strong)));print('ARCHIVED_TRANSPORT_ADMISSION_REVIEW_ELIGIBLE='+str(bool(strong)).lower());print('BR03_RETRIEVAL_PASS=false');print('BASE_RATE_CODING_PERMISSION=false');print('SCORE_PERMISSION=false')
if __name__=='__main__':main()
