#!/usr/bin/env python3
"""Execute pre-frozen BR03 Kadesh transport admission policy v0.21.

Re-fetches only two frozen Wayback if_ snapshots, recomputes normalized Poem spans,
page/section geometry and hashes. No source prose is persisted. PASS may set only
BR03_RETRIEVAL_PASS=true; base-rate coding and SCORE remain locked.
"""
from __future__ import annotations
import hashlib,html,json,re,urllib.error,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POL=ROOT/'research/propaganda-defense/KADESH_BR03_TRANSPORT_ADMISSION_POLICY.v0.21.json'
OUT=ROOT/'research/propaganda-defense/execution/KADESH_BR03_TRANSPORT_ADMISSION_RUN.v0.21.json'
UA='TOPA-Kadesh-BR03-Admission/0.21 (+https://github.com/Hawkar-usls/TOPA)'

def sha(b):return hashlib.sha256(b).hexdigest()
def get(u,maxb=12*1024*1024,timeout=30):
 req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'*/*','Accept-Encoding':'identity'})
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r:
   b=r.read(maxb+1);return {'ok':True,'status':getattr(r,'status',200),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type'),'bytes':min(len(b),maxb),'sha256':sha(b[:maxb]),'truncated':len(b)>maxb,'body':b[:maxb]}
 except urllib.error.HTTPError as e:
  try:b=e.read(65536)
  except:b=b''
  return {'ok':False,'status':e.code,'error':f'HTTPError: {e}','error_body_bytes':len(b),'error_body_sha256':sha(b)}
 except Exception as e:return {'ok':False,'error':f'{type(e).__name__}: {e}'}
def pub(x):return {k:v for k,v in x.items() if k!='body'}
def norm(b):
 s=b.decode('utf-8','replace');s=re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m.group(1),16)),s);s=s.replace('\\/','/').replace('\\n',' ');s=re.sub(r'(?is)<style.*?</style>',' ',s);s=re.sub(r'(?s)<[^>]+>',' ',s);return re.sub(r'\s+',' ',html.unescape(s)).strip()
def pos(t,p):return [m.start() for m in re.finditer(p,t,re.I)]
def nearest(a,b):
 if not a or not b:return (None,None,10**12)
 x,y=min(((x,y) for x in a for y in b),key=lambda z:abs(z[0]-z[1]));return x,y,abs(x-y)
def words(s):return re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿĀ-žḀ-ỿ']+",s.lower())
def eval_snapshot(raw,expected_sha):
 t=norm(raw);low=t.lower();pages={n:pos(t,rf'(?<!\d){n}(?!\d)') for n in range(266,288)}
 marks={'the_poem':pos(t,r'\bthe poem\b'),'council':pos(t,r'council urges peace'),'the_record':pos(t,r'\bthe record\b'),'comment':pos(t,r'comment on the texts')}
 _,p_poem,d266=nearest(pages[266],marks['the_poem']);_,p_coun,d277=nearest(pages[277],marks['council']);_,p_rec,d278=nearest(pages[278],marks['the_record']);_,p_com,d287=nearest(pages[287],marks['comment'])
 span=t[p_poem:p_rec] if p_poem is not None and p_rec is not None and p_poem<p_rec else ''
 toks=words(span);presence={'the_poem':bool(marks['the_poem']),'council_urges_peace':bool(marks['council']),'the_record':bool(marks['the_record']),'comment_on_the_texts':bool(marks['comment'])}
 span_sha=sha(span.encode())
 checks={
  'document_id':'493951399' in raw.decode('utf-8','replace'),
  'exact_title':'the texts of the battle of kadesh' in low,
  'pages_266_287':all(pages[n] for n in range(266,288)),
  'marker_presence':all(presence.values()),
  'marker_order':p_poem is not None and p_rec is not None and p_com is not None and p_poem<p_rec<p_com,
  'p266_poem_geometry':d266<=3000,
  'p277_council_geometry':d277<=3500,
  'p278_record_geometry':d278<=2200,
  'p287_comment_geometry':d287<=3500,
  'substantial_span_chars':len(span)>=8000,
  'substantial_span_tokens':len(toks)>=1200,
  'expected_poem_span_sha256':span_sha==expected_sha,
 }
 return {'normalized_chars':len(t),'page_coverage_count':sum(bool(pages[n]) for n in range(266,288)),'marker_presence_vector':presence,'marker_counts_diagnostic_only':{'the_poem':len(marks['the_poem']),'council_urges_peace':len(marks['council']),'the_record':len(marks['the_record']),'comment_on_the_texts':len(marks['comment'])},'geometry_distances_chars':{'p266_to_THE_POEM':d266,'p277_to_COUNCIL':d277,'p278_to_THE_RECORD':d278,'p287_to_COMMENT':d287},'poem_span_chars':len(span),'poem_span_word_tokens':len(toks),'poem_span_sha256':span_sha,'expected_poem_span_sha256':expected_sha,'checks':checks,'pass':all(checks.values()),'_wordset':set(toks)}
def main():
 pol=json.loads(POL.read_text()); original=pol['transport_representation']['original_url']; expected=pol['mandatory_replay_checks']['expected_poem_span_sha256']; rows=[]
 for ts in pol['transport_representation']['wayback_timestamps']:
  u=f'https://web.archive.org/web/{ts}if_/{original}';x=get(u);r={'timestamp':ts,'url':u,'response':pub(x)}
  r['analysis']=eval_snapshot(x['body'],expected[ts]) if x.get('ok') else {'pass':False,'checks':{},'_wordset':set()};rows.append(r)
 a,b=rows[0]['analysis'],rows[1]['analysis'];wa=a.pop('_wordset',set());wb=b.pop('_wordset',set());jacc=len(wa&wb)/len(wa|wb) if wa|wb else 0.0
 cross={'both_retrievable':all(r['response'].get('ok') for r in rows),'both_snapshot_checks_pass':bool(a.get('pass') and b.get('pass')),'poem_wordset_jaccard':jacc,'jaccard_pass':jacc>=pol['mandatory_replay_checks']['poem_span_wordset_jaccard_min'],'same_page_coverage':a.get('page_coverage_count')==b.get('page_coverage_count')==22,'same_marker_presence_vector':a.get('marker_presence_vector')==b.get('marker_presence_vector') and all(a.get('marker_presence_vector',{}).values()),'stable_expected_span_hashes':all(r['analysis'].get('checks',{}).get('expected_poem_span_sha256') for r in rows)}
 state={'semantic_values_populated':0,'base_rate_coding_permission':False,'score_permission':False,'sacred_flood_coder_A':'UNASSIGNED','sacred_flood_coder_B':'UNASSIGNED'}
 final=all(cross.values()) and state['semantic_values_populated']==pol['state_integrity']['semantic_values_populated_before_review_must_equal'] and pol['transport_representation']['source_root_count']==1 and not pol['transport_representation']['transport_adds_independent_source_root'] and pol['rights_gate']['publication_year']==1927 and not pol['rights_gate']['global_public_domain_claim']
 result={'BR03_RETRIEVAL_PASS':bool(final),'ancient_base_rate_external_retrieval':'8/8_CANDIDATE_PENDING_GLOBAL_CONSISTENCY_REVIEW' if final else '7/8_OR_LESS','base_rate_coding_permission':False,'semantic_values_populated':0,'score_permission':False,'next_required_gate':'BASE_RATE_8_OF_8_RETRIEVAL_REVERSE_CONSISTENCY_AND_CODING_UNLOCK_REVIEW' if final else 'BR03_TRANSPORT_REPAIR'}
 out={'schema':'topa.propaganda_defense.kadesh_br03_transport_admission_run.v0.21','date':'2026-08-24','policy_path':str(POL.relative_to(ROOT)),'policy_sha256':sha(POL.read_bytes()),'policy_status':pol['status'],'source_authority':pol['source_authority'],'transport_representation':pol['transport_representation'],'rights_gate':pol['rights_gate'],'snapshots':rows,'cross_timestamp':cross,'state_integrity_observed':state,'result':result,'laws':pol['laws']}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print('TOPA_KADESH_BR03_ADMISSION_V0_21='+('PASS' if final else 'FAIL'))
 print('SNAPSHOTS_PASS='+str(sum(bool(r['analysis'].get('pass')) for r in rows))+'/2')
 print('POEM_WORDSET_JACCARD='+f'{jacc:.6f}')
 print('STABLE_EXPECTED_SPAN_HASHES='+str(cross['stable_expected_span_hashes']).lower())
 print('BR03_RETRIEVAL_PASS='+str(final).lower())
 print('ANCIENT_BASE_RATE_EXTERNAL_RETRIEVAL='+('8/8_CANDIDATE' if final else 'NOT_8/8'))
 print('BASE_RATE_CODING_PERMISSION=false')
 print('SCORE_PERMISSION=false')
if __name__=='__main__':main()
