#!/usr/bin/env python3
"""Execute the pre-frozen KADESH_TRANSPORT_OBJECT_IDENTITY_GATE.v0.20.

No source prose is persisted. Only hashes, counts, marker geometry and pass/fail
booleans are written. A PASS only makes the transport object eligible for a
separate admission review; BR03, coding and SCORE remain locked here.
"""
from __future__ import annotations
import hashlib,html,json,re,urllib.error,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GATE=ROOT/'research/propaganda-defense/KADESH_TRANSPORT_OBJECT_IDENTITY_GATE.v0.20.json'
OUT=ROOT/'research/propaganda-defense/execution/KADESH_TRANSPORT_OBJECT_IDENTITY_RUN.v0.20.json'
UA='TOPA-Kadesh-Transport-Identity/0.20 (+https://github.com/Hawkar-usls/TOPA)'
ORIGINAL='https://www.scribd.com/document/493951399/Wilson-John-The-Texts-of-the-Battle-of-Kadesh'
TIMESTAMPS=['20250825141753','20260111160515']

def sha(b):return hashlib.sha256(b).hexdigest()
def get(u,maxb=12*1024*1024,timeout=30):
 req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'*/*','Accept-Encoding':'identity'})
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r:
   b=r.read(maxb+1);return {'ok':True,'status':getattr(r,'status',200),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type'),'bytes':min(len(b),maxb),'sha256':sha(b[:maxb]),'truncated':len(b)>maxb,'body':b[:maxb]}
 except urllib.error.HTTPError as e:
  try:b=e.read(65536)
  except:b=b''
  return {'ok':False,'status':e.code,'error':f'HTTPError: {e}','error_body_sha256':sha(b),'error_body_bytes':len(b)}
 except Exception as e:return {'ok':False,'error':f'{type(e).__name__}: {e}'}
def pub(x):return {k:v for k,v in x.items() if k!='body'}
def norm(b):
 s=b.decode('utf-8','replace');s=re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m.group(1),16)),s);s=s.replace('\\/','/').replace('\\n',' ');s=re.sub(r'(?is)<style.*?</style>',' ',s);s=re.sub(r'(?s)<[^>]+>',' ',s);return re.sub(r'\s+',' ',html.unescape(s)).strip()
def positions(t,pat):return [m.start() for m in re.finditer(pat,t,re.I)]
def nearest_dist(a,b):return min((abs(x-y) for x in a for y in b),default=10**12)
def nearest_pair(a,b):
 if not a or not b:return (None,None,10**12)
 x,y=min(((x,y) for x in a for y in b),key=lambda z:abs(z[0]-z[1]));return x,y,abs(x-y)
def words(s):return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿĀ-žḀ-ỿ']+",s.lower())
def asset_bind(raw):
 s=raw.decode('utf-8','replace').replace('\\/','/')
 pats=re.findall(r'https?://[^"\'<>\\\s]+',s)
 hit=[u.rstrip('),.;]') for u in pats if '/img/document/493951399/original/' in u]
 return sorted(set(hit))[:20]
def evaluate(raw,gate):
 t=norm(raw);low=t.lower();
 p={n:positions(t,rf'(?<!\d){n}(?!\d)') for n in range(266,288)}
 poem=positions(t,r'\bthe poem\b'); council=positions(t,r'council urges peace'); record=positions(t,r'\bthe record\b'); comment=positions(t,r'comment on the texts')
 pp266,poem_sel,d266=nearest_pair(p[266],poem);pp277,coun_sel,d277=nearest_pair(p[277],council);pp278,rec_sel,d278=nearest_pair(p[278],record);pp287,com_sel,d287=nearest_pair(p[287],comment)
 ordering=all(x is not None for x in (poem_sel,rec_sel,com_sel)) and poem_sel<rec_sel<com_sel
 span=t[poem_sel:rec_sel] if poem_sel is not None and rec_sel is not None and poem_sel<rec_sel else ''
 toks=words(span);aset=asset_bind(raw)
 checks={
  'document_id':'493951399' in raw.decode('utf-8','replace'),
  'title':'the texts of the battle of kadesh' in low,
  'all_pages_266_287':all(bool(p[n]) for n in range(266,288)),
  'the_poem':bool(poem),'council_urges_peace':bool(council),'the_record':bool(record),'comment_on_the_texts':bool(comment),
  'ordering':ordering,
  'poem_near_266':d266<=gate['per_snapshot_mandatory']['nearest_page_geometry']['THE_POEM_near_page_266_max_chars'],
  'council_near_277':d277<=gate['per_snapshot_mandatory']['nearest_page_geometry']['COUNCIL_URGES_PEACE_near_page_277_max_chars'],
  'record_near_278':d278<=gate['per_snapshot_mandatory']['nearest_page_geometry']['THE_RECORD_near_page_278_max_chars'],
  'comment_near_287':d287<=gate['per_snapshot_mandatory']['nearest_page_geometry']['COMMENT_ON_THE_TEXTS_near_page_287_max_chars'],
  'poem_span_chars':len(span)>=gate['per_snapshot_mandatory']['poem_span_between_THE_POEM_and_THE_RECORD_min_normalized_chars'],
  'poem_span_tokens':len(toks)>=gate['per_snapshot_mandatory']['poem_span_min_word_tokens'],
  'embedded_original_asset':bool(aset)
 }
 return {'normalized_chars':len(t),'normalized_sha256':sha(t.encode()),'page_coverage_count':sum(bool(p[n]) for n in range(266,288)),'marker_counts':{'the_poem':len(poem),'council_urges_peace':len(council),'the_record':len(record),'comment_on_the_texts':len(comment)},'geometry_distances_chars':{'p266_to_THE_POEM':d266,'p277_to_COUNCIL':d277,'p278_to_THE_RECORD':d278,'p287_to_COMMENT':d287},'selected_marker_positions':{'the_poem':poem_sel,'the_record':rec_sel,'comment_on_the_texts':com_sel},'poem_span_chars':len(span),'poem_span_word_tokens':len(toks),'poem_span_sha256':sha(span.encode()),'poem_wordset_sha256':sha('\n'.join(sorted(set(toks))).encode()),'embedded_original_asset_count':len(aset),'embedded_original_asset_urls':aset,'checks':checks,'pass':all(checks.values()),'_wordset':set(toks)}
def main():
 gate=json.loads(GATE.read_text()); gate_bytes=GATE.read_bytes();rows=[]
 for ts in TIMESTAMPS:
  u=f'https://web.archive.org/web/{ts}if_/{ORIGINAL}';x=get(u);r={'timestamp':ts,'url':u,'response':pub(x)}
  if x.get('ok'):r['analysis']=evaluate(x['body'],gate)
  else:r['analysis']={'pass':False,'checks':{},'_wordset':set()}
  rows.append(r)
 a,b=rows[0]['analysis'],rows[1]['analysis'];wa=a.pop('_wordset',set());wb=b.pop('_wordset',set());jacc=len(wa&wb)/len(wa|wb) if wa|wb else 0.0
 cross={'both_snapshots_pass':bool(a.get('pass') and b.get('pass')),'poem_wordset_jaccard':jacc,'jaccard_pass':jacc>=gate['cross_timestamp_mandatory']['poem_span_word_set_jaccard_min'],'same_page_coverage':a.get('page_coverage_count')==b.get('page_coverage_count')==22,'same_marker_vector':a.get('marker_counts')==b.get('marker_counts')}
 final=all(cross.values())
 out={'schema':'topa.propaganda_defense.kadesh_transport_object_identity_run.v0.20','date':'2026-08-24','gate_path':str(GATE.relative_to(ROOT)),'gate_sha256':sha(gate_bytes),'gate_status':gate['status'],'frozen':gate['transport_object_frozen'],'source_authority':gate['source_authority_frozen'],'snapshots':rows,'cross_timestamp':cross,'result':{'transport_object_identity_content_sufficiency':'PASS_CANDIDATE' if final else 'FAIL','transport_admission_review_eligible':final,'br03_retrieval_pass':False,'semantic_values_populated':0,'base_rate_coding_permission':False,'score_permission':False},'laws':gate['laws']}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print('TOPA_KADESH_TRANSPORT_IDENTITY_V0_20='+('PASS_CANDIDATE' if final else 'FAIL'))
 print('SNAPSHOT_PASS='+str(sum(bool(r['analysis'].get('pass')) for r in rows))+'/2')
 print('POEM_WORDSET_JACCARD='+f'{jacc:.6f}')
 print('TRANSPORT_ADMISSION_REVIEW_ELIGIBLE='+str(final).lower())
 print('BR03_RETRIEVAL_PASS=false')
 print('BASE_RATE_CODING_PERMISSION=false')
 print('SCORE_PERMISSION=false')
if __name__=='__main__':main()
