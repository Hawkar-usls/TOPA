#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path

INCLUDE_PREFIXES=("data/","registry/")
EXCLUDE_PREFIXES=("dynamic/","assets/","node_modules/",".git/","data/music/the-alan-parsons-project/")

# Conjunctive signatures frozen before this run. Every group inside a signature
# must be represented in the same JSON document. This is deliberately stricter
# than the broad relation pass and is used to find specificity/dark nodes.
SIGNATURES={
  "OBSERVER_SOURCE_VERDICT": [
    ["observer","observation","witness","наблюд","свидетел"],
    ["source","signal","источник","сигнал"],
    ["verdict","prediction","prophecy","вердикт","предсказ","пророч"]
  ],
  "TWO_WITNESSES_DIFFERENCE": [
    ["two witnesses","both witnesses","preserve both","два свидетел","сохрани оба"],
    ["difference","delta","compare","comparison","различ","дельта","сравн"]
  ],
  "REFERENCE_FRAME_PLUS_CHANGE": [
    ["reference frame","baseline","anchor","invariant","stable","fixed","система отсч","якор","инвариант","стабил"],
    ["difference","delta","transition","change","различ","дельта","переход","измен"]
  ],
  "SIGN_SOURCE_EXACT": [
    ["sign != source","sign ≠ source","signal != source"]
  ],
  "MEMORY_ORIGIN_PRIME": [
    ["memory","памят"],
    ["origin_prime","origin prime","return + memory","reset","возврат","сброс"]
  ],
  "HUMAN_SYSTEM_BRIDGE": [
    ["human","человек"],
    ["system","систем"],
    ["bridge","translation","мост","перевод"]
  ],
  "UNKNOWN_BOUNDARY_GATE": [
    ["unknown","uncertainty","неизвест","неопредел"],
    ["gate","boundary","гейт","границ"]
  ],
  "LAYER_PLUS_CONTRAST": [
    ["layer","overlay","stack","слой","насло"],
    ["contrast","dual","duality","light","dark","shadow","контраст","дуал","свет","тьм","тень"]
  ],
  "MACHINE_HUMAN_DIFFERENCE": [
    ["machine","машин"],
    ["human","человек"],
    ["difference","invariant","variation","различ","инвариант","вариац"]
  ],
  "CAUSAL_DIFFERENCE_CONTROL": [
    ["causal","causality","причин"],
    ["difference","witness","control","различ","свидетел","контрол"]
  ],
  "TIME_MEMORY_PROVENANCE": [
    ["yesterday","today","tomorrow","вчера","сегодня","завтра"],
    ["memory","provenance","chronology","timestamp","памят","происхожд","хронолог","метк"]
  ]
}


def strings(x):
    if isinstance(x,str): return [x]
    if isinstance(x,dict):
        out=[]
        for k,v in x.items(): out += [str(k)] + strings(v)
        return out
    if isinstance(x,list):
        out=[]
        for v in x: out += strings(v)
        return out
    return []


def scan(root):
    docs=[]; failures=[]
    root=Path(root)
    for p in root.rglob('*.json'):
        rel=p.relative_to(root).as_posix()
        if not rel.startswith(INCLUDE_PREFIXES) or rel.startswith(EXCLUDE_PREFIXES): continue
        if p.stat().st_size>2_000_000: continue
        try: obj=json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            failures.append({'path':rel,'error':type(e).__name__}); continue
        docs.append((rel,'\n'.join(strings(obj)).lower()))
    return docs,failures


def match_signature(text, groups):
    group_hits=[]
    for group in groups:
        hits=sorted({kw for kw in group if kw in text})
        if not hits: return None
        group_hits.append(hits)
    distinct=sorted({x for g in group_hits for x in g})
    score=sum(1.35 if ' ' in x else 1.0 for x in distinct)
    return {'score':round(score,3),'group_hits':group_hits,'matched':distinct}


def rank(docs,groups,topk=10):
    rows=[]
    for path,text in docs:
        m=match_signature(text,groups)
        if m:
            rows.append({'path':path,**m})
    rows.sort(key=lambda r:(-r['score'],r['path']))
    return rows[:topk],len(rows)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--yesterday-root',required=True)
    ap.add_argument('--current-root',required=True)
    ap.add_argument('--source-ref',required=True)
    ap.add_argument('--source-blob',required=True)
    ap.add_argument('--yesterday-ref',required=True)
    ap.add_argument('--current-ref',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    yd,yf=scan(a.yesterday_root); cd,cf=scan(a.current_root)
    results={}; dark=[]; pre=[]; today=[]
    hubs=defaultdict(lambda:{'signatures':set(),'score_sum':0.0,'preexisting':False})
    for name,groups in SIGNATURES.items():
        yt,yc=rank(yd,groups); ct,cc=rank(cd,groups)
        if yc:
            st='STRICT_PREEXISTING_RELATION'; pre.append(name)
        elif cc:
            st='STRICT_TODAY_ONLY_RELATION'; today.append(name)
        else:
            st='STRICT_DARK_NODE'; dark.append(name)
        results[name]={'required_groups':groups,'yesterday_count':yc,'current_count':cc,'status':st,'top_yesterday':yt,'top_current':ct}
        ypaths={r['path'] for r in yt}
        for r in ct:
            h=hubs[r['path']]; h['signatures'].add(name); h['score_sum']+=r['score']; h['preexisting']|=(r['path'] in ypaths)
    hs=[]
    for p,v in hubs.items(): hs.append({'path':p,'signature_count':len(v['signatures']),'signatures':sorted(v['signatures']),'score_sum':round(v['score_sum'],3),'preexisting_top_hit':v['preexisting']})
    hs.sort(key=lambda r:(-r['signature_count'],-r['score_sum'],r['path']))
    out={
      'schema':'topa.app_deep_mechanics_strict_conjunctive_sieve.v1',
      'status':'PASS',
      'purpose':'Second sieve after broad relation pass; require compound concepts in one pre-existing JSON and expose genuine dark nodes.',
      'provenance':{'source_ref_frozen_before_both_topa_passes':a.source_ref,'source_blob_sha':a.source_blob,'yesterday_ref':a.yesterday_ref,'current_ref_frozen_before_topa':a.current_ref},
      'scan':{'yesterday_documents':len(yd),'current_documents':len(cd),'yesterday_parse_failures':yf,'current_parse_failures':cf,'APP_corpus_excluded':True},
      'signature_results':results,
      'strict_hubs':hs[:25],
      'summary':{'signatures_total':len(SIGNATURES),'preexisting_count':len(pre),'preexisting':pre,'today_only_count':len(today),'today_only':today,'dark_count':len(dark),'dark_nodes':dark},
      'interpretation_ceiling':'A strict conjunctive preexisting hit means multiple concepts co-occurred in one older JANUS JSON. It does not establish that the music encoded JANUS, that JANUS predicted the music analysis, or that any causal channel exists.',
      'dark_node_rule':'STRICT_DARK_NODE means no same-document hit under this frozen signature vocabulary and snapshot; it is a research target, not proof of nonexistence.',
      'scientific_firewall':['STRICT_CO_OCCURRENCE != CAUSATION','PREEXISTING_RELATION != PROPHECY','MUSIC_ANALOGY != AUTHORIAL_INTENT','NO_HIT != NO_RELATION','SIGN != SOURCE'],
      'canonical_seal':'BROAD OVERLAP IS CHEAP. REQUIRE COMPOUND WITNESSES. WHAT SURVIVES THE STRICT SIEVE MAY BE STUDIED; WHAT DOES NOT SURVIVE BECOMES A DARK NODE.'
    }
    Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out['summary'],ensure_ascii=False,indent=2))

if __name__=='__main__': main()
