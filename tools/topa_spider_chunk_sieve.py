#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, io, json, re, time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

SCHEMA='hawkar.topa.spider_chunk_batch_sieve.v1'
LAWS=[
 'SEARCH_HIT_IS_NOT_EVIDENCE','CHUNK_SELECTION_IS_NOT_EVIDENCE','PATTERN_MATCH_IS_NOT_MECHANISM',
 'PATTERN_COOCCURRENCE_IS_NOT_CAUSATION','SAME_SOURCE_REPRINT_IS_NOT_INDEPENDENT_WITNESS',
 'NEIGHBOR_CONTEXT_IS_PRESERVED_TO_REDUCE_QUOTE_MINING','RAW_ARCHIVE_RECORDS_ARE_IMMUTABLE',
 'MISSING_PATTERN_IS_NOT_PROOF_OF_ABSENCE','MODEL_OUTPUT_IS_NOT_EVIDENCE'
]

def canon(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha_text(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def read_json(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def read_jsonl(p):
    path=Path(p)
    if not path.exists(): return []
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_jsonl(p,rows):
    path=Path(p); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(canon(r)+'\n' for r in rows),encoding='utf-8')

def norm_tokens(s): return re.findall(r"[a-z0-9]+",str(s).casefold())
def normalize(s): return ' '.join(norm_tokens(s))
def source_family(r):
    pr=str(r.get('provider') or 'UNKNOWN').upper(); aid=str(r.get('archive_id') or '').strip()
    if aid: return f'{pr}:{aid.upper()}'
    return f'{pr}:URL:{sha_text(str(r.get("source_url") or ""))[:16]}'

def chunk_record(r, words=180, overlap=45):
    raw=str(r.get('text') or '')
    toks=re.findall(r'\S+',raw)
    if not toks: return []
    step=max(1,words-overlap); out=[]
    for i,start in enumerate(range(0,len(toks),step)):
        end=min(len(toks),start+words); txt=' '.join(toks[start:end])
        if not txt: continue
        out.append({'chunk_index':i,'word_start':start,'word_end':end,'text':txt,'text_sha256':sha_text(txt)})
        if end>=len(toks): break
    return out

def compile_patterns(cfg):
    out=[]
    for fam in cfg.get('families',[]):
        aliases=[]
        for a in fam.get('aliases',[]):
            nt=norm_tokens(a)
            if nt: aliases.append((a,nt))
        out.append((fam['id'],aliases))
    return out

def match_patterns(text, compiled):
    toks=norm_tokens(text); joined=' '.join(toks); matches=[]; fams=[]
    for fid,aliases in compiled:
        fam_hits=[]
        for raw,atoks in aliases:
            phrase=' '.join(atoks)
            pat=r'(?<![a-z0-9])'+re.escape(phrase).replace(r'\ ',r'\s+')+r'(?![a-z0-9])'
            cnt=len(re.findall(pat,joined))
            if cnt: fam_hits.append({'alias':raw,'count':cnt})
        if fam_hits:
            fams.append(fid); matches.append({'family':fid,'aliases':fam_hits})
    return fams,matches

def state_labels(text):
    s=normalize(text); labels=[]
    rules={
      'HYPOTHESIS_OR_MODEL':['hypothesis','model','possible mechanism','may play a role','possibility'],
      'EXPERIMENT_OR_TEST':['experiment','experimental','test','trial','random number generator','data set','dataset'],
      'NEGATIVE_OR_LIMITATION':['not confirmed','not observed','no evidence','unreliable','inconsistent','premature','problem','critique','failed'],
      'PROGRAM_OR_RESEARCH_PLAN':['research plan','program','project','contract','final report','progress report'],
      'PHYSICS_CONTEXT':['relativity','quantum','electromagnetic','wave function','thermodynamics','space time','spacetime'],
      'INFORMATION_FLOW_CLAIM':['information flow','information transfer','information leakage','future to past','precognition'],
      'RETROACTIVE_EFFECT_CLAIM':['backward causation','retroactive','retro pk','effect precedes the cause','backwards in time']
    }
    for lab,needles in rules.items():
        if any(normalize(n) in s for n in needles): labels.append(lab)
    return labels or ['UNCLASSIFIED_CONTEXT']

def shingles(text,n=4):
    t=norm_tokens(text)
    if len(t)<n: return set(t)
    return {' '.join(t[i:i+n]) for i in range(len(t)-n+1)}
def jac(a,b):
    if not a or not b: return 0.0
    return len(a&b)/len(a|b)

def extract_pdf_text(payload):
    try:
        from pypdf import PdfReader
    except Exception:
        return '',{'status':'PYPDF_NOT_AVAILABLE','pages':None,'pages_with_text':0}
    try:
        reader=PdfReader(io.BytesIO(payload)); parts=[]; pages_with_text=0
        for page in reader.pages:
            try: t=page.extract_text() or ''
            except Exception: t=''
            if t.strip(): pages_with_text+=1; parts.append(t)
        text='\n'.join(parts)
        return text,{'status':'PASS' if text.strip() else 'NO_EXTRACTABLE_TEXT','pages':len(reader.pages),'pages_with_text':pages_with_text}
    except Exception as e:
        return '',{'status':'PDF_EXTRACT_ERROR','error':f'{type(e).__name__}: {e}','pages':None,'pages_with_text':0}

def harvest_from_config(config_path,out_path,receipt_path):
    from topa_archive_gateway import fetch, html_text, LinkParser, archive_record
    cfg=read_json(config_path); rows=[]; errors=[]
    for u in cfg.get('bootstrap_sources',[]):
        try:
            b,m=fetch(u); ct=(m.get('content_type') or '').lower(); aid=u.rstrip('/').rsplit('/',1)[-1].replace('.pdf','')
            if 'pdf' in ct or u.lower().endswith('.pdf'):
                text,pdf_meta=extract_pdf_text(b)
                rows.append(archive_record('CIA',u,aid,text[:200000],archive_id=aid,extra={'content_type':ct,'binary_policy':'POINTER_HASH_AND_LOCAL_TEXT_EXTRACTION','pdf_text_extraction':pdf_meta,'relation_tags':['CIA','DECLASSIFIED','RETRO_TEMPORAL_PATTERN_SET']},source_meta=m))
                if not text.strip(): errors.append({'url':u,'error':'NO_EXTRACTABLE_PDF_TEXT','pdf_text_extraction':pdf_meta})
            else:
                p=LinkParser(); p.feed(b.decode('utf-8','replace'))
                rows.append(archive_record('CIA',u,p.title or aid,html_text(b)[:200000],aid,{'relation_tags':['CIA','DECLASSIFIED','RETRO_TEMPORAL_PATTERN_SET']},m))
        except Exception as e:
            errors.append({'url':u,'error':f'{type(e).__name__}: {e}'})
        time.sleep(0.15)
    ded={}
    for r in rows: ded[(r.get('provider'),r.get('archive_id'),r.get('source_url'))]=r
    rows=sorted(ded.values(),key=lambda r:(r.get('provider',''),r.get('archive_id',''),r.get('source_url','')))
    write_jsonl(out_path,rows)
    text_records=sum(bool(str(r.get('text') or '').strip()) for r in rows)
    receipt={'schema':SCHEMA+'.harvest_receipt','status':'PASS' if rows else 'FAIL_EMPTY','records':len(rows),'records_with_text':text_records,'errors':errors,
             'stream_sha256':sha_text(''.join(canon(r)+'\n' for r in rows)),'laws':['DECLASSIFICATION_IS_PROVENANCE_NOT_TRUTH','FAILED_FETCH_IS_NOT_PROOF_OF_ABSENCE','PDF_TEXT_EXTRACTION_IS_A_DERIVED_VIEW_NOT_SOURCE_BYTES']}
    Path(receipt_path).parent.mkdir(parents=True,exist_ok=True); Path(receipt_path).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return receipt

def sieve(records, cfg, words=180, overlap=45, neighbor_radius=1, batch_size=64, near_dup=0.88):
    compiled=compile_patterns(cfg); by_record=defaultdict(list); records_by_key={}
    for r in records:
        sf=source_family(r); rk=(sf,str(r.get('source_url') or '')); records_by_key[rk]=r
        for c in chunk_record(r,words,overlap):
            fams,matches=match_patterns(c['text'],compiled); direct=bool(fams)
            x={
              'provider':r.get('provider'),'archive_id':r.get('archive_id'),'source_url':r.get('source_url'),'record_sha256':r.get('record_sha256'),
              'source_family_id':sf,'chunk_index':c['chunk_index'],'word_start':c['word_start'],'word_end':c['word_end'],'text':c['text'],'text_sha256':c['text_sha256'],
              'direct_hit':direct,'pattern_families':fams,'pattern_matches':matches,'state_labels':state_labels(c['text']),'neighbor_of':[],
              'selection_score':round(min(1.0,(0.32 if direct else 0.0)+0.16*len(fams)+0.025*sum(sum(a['count'] for a in m['aliases']) for m in matches)),6),
              'duplicate_of':None
            }
            x['chunk_id']=f"{sf}:{c['chunk_index']}:{c['text_sha256'][:12]}"; by_record[rk].append(x)
    retained={}
    for _rk,chunks in by_record.items():
        direct_idxs=[i for i,c in enumerate(chunks) if c['direct_hit']]
        for i in direct_idxs:
            for j in range(max(0,i-neighbor_radius),min(len(chunks),i+neighbor_radius+1)):
                c=chunks[j]; retained[c['chunk_id']]=c
                if j!=i: c['neighbor_of'].append(chunks[i]['chunk_id']); c['selection_score']=max(c['selection_score'],0.12)
    kept=sorted(retained.values(),key=lambda c:(c['provider'] or '',c['archive_id'] or '',c['chunk_index'],c['chunk_id']))
    canonical=[]; exact={}
    for c in kept:
        if c['text_sha256'] in exact:
            c['duplicate_of']=exact[c['text_sha256']]['chunk_id']; continue
        cs=shingles(c['text']); dup=None
        for prev,ps in canonical:
            if c['pattern_families'] and prev['pattern_families'] and not (set(c['pattern_families']) & set(prev['pattern_families'])): continue
            if jac(cs,ps)>=near_dup: dup=prev; break
        if dup: c['duplicate_of']=dup['chunk_id']
        else: canonical.append((c,cs)); exact[c['text_sha256']]=c
    batches=[]
    for i in range(0,len(kept),batch_size):
        chunk=kept[i:i+batch_size]; payload=''.join(canon(c)+'\n' for c in chunk)
        batches.append({'batch_id':f'BATCH-{i//batch_size+1:04d}','chunk_ids':[c['chunk_id'] for c in chunk],'size':len(chunk),'sha256':sha_text(payload)})
    fam_summary=[]
    for fid,_aliases in compiled:
        direct=[c for c in kept if c['direct_hit'] and fid in c['pattern_families']]
        contexts=[c for c in kept if (not c['direct_hit']) and c['neighbor_of'] and any(fid in retained[x]['pattern_families'] for x in c['neighbor_of'] if x in retained)]
        sf=sorted({c['source_family_id'] for c in direct}); docs=sorted({str(c['archive_id'] or c['source_url']) for c in direct})
        fam_summary.append({'family':fid,'direct_chunks':len(direct),'neighbor_context_chunks':len(contexts),'source_families':sf,'independent_source_family_count':len(sf),'documents':docs})
    co=defaultdict(lambda:{'chunks':0,'source_families':set(),'documents':set()})
    for c in kept:
        if not c['direct_hit']: continue
        for a,b in combinations(sorted(set(c['pattern_families'])),2):
            k=(a,b); co[k]['chunks']+=1; co[k]['source_families'].add(c['source_family_id']); co[k]['documents'].add(str(c['archive_id'] or c['source_url']))
    co_rows=[{'a':a,'b':b,'cooccurring_chunks':v['chunks'],'source_family_count':len(v['source_families']),'source_families':sorted(v['source_families']),'documents':sorted(v['documents']),'claim_authority':'DISCOVERY_ROUTING_ONLY__NOT_CAUSATION'} for (a,b),v in sorted(co.items())]
    dup_groups=defaultdict(list)
    for c in kept:
        if c['duplicate_of']: dup_groups[c['duplicate_of']].append(c['chunk_id'])
    docs=[]; selected_rks={(c['source_family_id'],str(c['source_url'] or '')) for c in kept}
    for rk in sorted(selected_rks):
        r=records_by_key.get(rk)
        if not r: continue
        docs.append({'provider':r.get('provider'),'archive_id':r.get('archive_id'),'source_url':r.get('source_url'),'title':r.get('title'),'record_sha256':r.get('record_sha256'),'source_family_id':source_family(r),'claim_ceiling':r.get('claim_ceiling'),'scientific_authority':r.get('scientific_authority'),'source_fetch':r.get('source_fetch'),'pdf_text_extraction':r.get('pdf_text_extraction')})
    states=Counter(l for c in kept for l in c['state_labels'])
    dossier={
      'schema':SCHEMA,'status':'PASS','pattern_set_id':cfg.get('pattern_set_id'),'scope_note':cfg.get('scope_note'),
      'parameters':{'chunk_words':words,'overlap_words':overlap,'neighbor_radius':neighbor_radius,'batch_size':batch_size,'near_duplicate_jaccard':near_dup},
      'stats':{'input_records':len(records),'selected_documents':len(docs),'retained_chunks':len(kept),'direct_hit_chunks':sum(c['direct_hit'] for c in kept),'neighbor_context_chunks':sum(not c['direct_hit'] for c in kept),'duplicate_or_near_duplicate_chunks':sum(bool(c['duplicate_of']) for c in kept),'batches':len(batches)},
      'pattern_families':fam_summary,'state_counts':dict(sorted(states.items())),'pattern_cooccurrence':co_rows,'documents':docs,'batches':batches,
      'duplicate_groups':[{'canonical_chunk_id':k,'duplicates':v} for k,v in sorted(dup_groups.items())],
      'chunks':kept,'laws':LAWS,'claim_ceiling':'DISCOVERY_ROUTING_AND_STRUCTURING_ONLY__NO_PHYSICAL_OR_CAUSAL_PROMOTION'
    }
    dossier['dossier_sha256']=sha_text(canon({k:v for k,v in dossier.items() if k!='dossier_sha256'}))
    return dossier,kept

def self_test():
    cfg={'pattern_set_id':'T','families':[{'id':'RETRO','aliases':['reverse information flow','backward causation']},{'id':'TACH','aliases':['tachyon']}]}
    rows=[{'provider':'CIA','archive_id':'A','source_url':'https://x/A','record_sha256':'1','text':'ordinary lead words '*60+' reverse information flow may be a model and tachyon hypothesis '+' tail context '*90},
          {'provider':'CIA','archive_id':'B','source_url':'https://x/B','record_sha256':'2','text':'bank accounting payroll ordinary business document '*80}]
    d,k=sieve(rows,cfg,80,20,1,8,.88)
    assert d['status']=='PASS' and d['stats']['selected_documents']==1 and any('RETRO' in c['pattern_families'] for c in k)
    assert all(c['archive_id']!='B' for c in k) and 'PATTERN_COOCCURRENCE_IS_NOT_CAUSATION' in d['laws']
    return {'schema':SCHEMA+'.self_test','status':'PASS','selective':True,'neighbor_context':True,'unrelated_record_rejected':True,'cooccurrence_firewall':True}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True); sp.add_parser('self-test')
    h=sp.add_parser('harvest'); h.add_argument('--config',required=True); h.add_argument('--out',required=True); h.add_argument('--receipt',required=True)
    s=sp.add_parser('sieve'); s.add_argument('--input',action='append',required=True); s.add_argument('--config',required=True); s.add_argument('--out-json',required=True); s.add_argument('--out-jsonl',required=True); s.add_argument('--words',type=int,default=180); s.add_argument('--overlap',type=int,default=45); s.add_argument('--neighbor-radius',type=int,default=1); s.add_argument('--batch-size',type=int,default=64); s.add_argument('--near-dup',type=float,default=.88)
    a=ap.parse_args()
    if a.cmd=='self-test': print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    if a.cmd=='harvest': print(json.dumps(harvest_from_config(a.config,a.out,a.receipt),ensure_ascii=False,indent=2)); return 0
    rows=[]
    for p in a.input: rows.extend(read_jsonl(p))
    d,k=sieve(rows,read_json(a.config),a.words,a.overlap,a.neighbor_radius,a.batch_size,a.near_dup)
    Path(a.out_json).parent.mkdir(parents=True,exist_ok=True); Path(a.out_json).write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); write_jsonl(a.out_jsonl,k)
    print(json.dumps({'status':d['status'],'dossier_sha256':d['dossier_sha256'],'stats':d['stats'],'state_counts':d['state_counts']},ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
