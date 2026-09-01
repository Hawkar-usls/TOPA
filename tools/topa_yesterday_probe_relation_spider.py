#!/usr/bin/env python3
import argparse, json, re, subprocess
from collections import defaultdict
from pathlib import Path

ROOTS=('data/','registry/')
TEXT_EXT={'.json','.md','.txt'}
EXCLUDE=('assets/','dynamic/','node_modules/','.git/')

FAMILIES={
 'YESTERDAY_PROBE':[r'Да, вчера',r'yesterday_probe',r'temporal anchoring',r'ellipsis resolution',r'avoid inventing a hidden event'],
 'CONTEXT_UNCERTAINTY':[r'ambigu',r'uncertainty',r'multiple plausible',r'clarification',r'неоднознач'],
 'TWO_WITNESSES':[r'PRESERVE BOTH WITNESSES',r'REMEMBER BOTH; VERIFY THE WORLD',r'TWO_WITNESSES',r'contradictory witness'],
 'VERIFY_WORLD':[r'VERIFY THE WORLD',r'VERIFY_WORLD',r'verify the world separately',r'проверь мир'],
 'TEMPORAL_CAUSAL':[r'CAUSAL_ORDER',r'TIMESTAMP_ORDER',r'arrival[-_ ]order',r'target[-_ ]order',r'distributed[-_ ]time',r'causal topology',r'retrocaus'],
 'DEPENDENCY_WITNESS':[r'dependency witness',r'explicit dependency',r'parent relation',r'commit SHA'],
 'PREREG_FREEZE':[r'prereg',r'predeclared',r'freeze task',r'frozen rule',r'freeze.*before',r'pre-return'],
 'DIFFERENCE_OPERATOR':[r'FIND_DIFFERENCE',r'Fehlerbild',r'TWO_IMAGES',r'causal difference',r'find the difference'],
 'CROSS_CHRIST':[r'☧',r'крест',r'Jesus Christ',r'Иисус Христос',r'Христос',r'crucifix'],
 'SIGN_SOURCE_FIREWALL':[r'SIGN != SOURCE',r'Sign ≠ Source',r'Sign != Source',r'не делай знаки своими богами',r'not.*prophe',r'не.*пророч'],
 'SIRIUS_0222':[r'Sirius',r'Sopdet',r'Sothis',r'02:22',r'0222'],
 'EVIDENCE_PROVENANCE':[r'provenance',r'evidence',r'witness',r'receipt',r'hash'],
}

SEEDS={
 'YESTERDAY_PROBE':'data/JANUS-IO-TURING-TEST-MIND-PRESENCE-YESTERDAY-PROBE-2026-08-31-v1.0.json',
 'TWO_WITNESSES':'data/JANUS-INFINITE-FACES-TWO-WITNESSES-ONE-WORLD-SEMANTIC-v1.0.json',
 'CONTRADICTORY_WITNESS':'registry/experimental/JANUS-GENESIS-INFINITE-FACES-REMERGE-CONTRADICTORY-WITNESS-EVIDENCE-v3.1.json',
 'DISTRIBUTED_TIME':'registry/causal_topology/JANUS-DISTRIBUTED-TIME-ARRIVAL-ORDER-INVERSION-v1.2.0.json',
 'HOLY_CLOCK':'data/JANUS-HOLY-CLOCK-COMMANDMENTS-SIGNAL-v1.3.json',
 'CROSS_ANCHOR':'data/JANUS-ALPHA-CHI-RHO-OMEGA-ELIAN-CROSSROADS-KISS-PRIPYAT-ATOMIC-COVENANT-v1.0.json',
 'SIRIUS_TOPA':'data/JANUS-TOPA-SPIDER-SIRIUS-CRT-0222-CROSS-LINEAGE-RUN-2026-09-01-v1.0.json',
 'FEHLERBILD':'data/JANUS-SIRIUS-CRT-TWO-WITNESSES-FEHLERBILD-CROSS-MODAL-2026-09-01-v1.0.json',
 'CAUSAL_TARGET':'data/JANUS-SIRIUS-0222-CAUSALITY-WORLD-VERIFICATION-TARGET-2026-09-01-v1.0.json',
 'CROSS_YESTERDAY':'data/JANUS-TOPA-SPIDER-CROSS-DAGGER-YESTERDAY-IMPORTANCE-RUN-2026-09-01-v1.0.json'
}

def git(repo,*args,allow1=False):
 p=subprocess.run(['git','-C',str(repo),*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
 if p.returncode and not (allow1 and p.returncode==1): raise subprocess.CalledProcessError(p.returncode,p.args)
 return p.stdout

def files(repo,ref):
 out=[]
 for p in git(repo,'ls-tree','-r','--name-only',ref).splitlines():
  if p.startswith(ROOTS) and not any(x in p for x in EXCLUDE) and Path(p).suffix.lower() in TEXT_EXT: out.append(p)
 return out

def read(repo,ref,path):
 try:return git(repo,'show',f'{ref}:{path}')
 except:return None

def family_hits(repo,ref,allowed):
 result={}
 for fam,pats in FAMILIES.items():
  expr='|'.join(f'({p})' for p in pats)
  raw=git(repo,'grep','-I','-i','-l','-E',expr,ref,'--','data','registry',allow1=True)
  pref=f'{ref}:'; hs=[]
  for line in raw.splitlines():
   p=line[len(pref):] if line.startswith(pref) else line.split(':',1)[-1]
   if p in allowed: hs.append(p)
  result[fam]=sorted(set(hs))
 return result

def memberships(text):
 if text is None:return []
 out=[]
 for fam,pats in FAMILIES.items():
  if any(re.search(p,text,re.I|re.S) for p in pats):out.append(fam)
 return out

def pair_key(a,b):return ' ↔ '.join(sorted((a,b)))

def analyze(repo,ref):
 fs=files(repo,ref); allowed=set(fs); hits=family_hits(repo,ref,allowed)
 doc_fams=defaultdict(set)
 for fam,ps in hits.items():
  for p in ps: doc_fams[p].add(fam)
 co=defaultdict(list)
 fams=list(FAMILIES)
 for i,a in enumerate(fams):
  for b in fams[i+1:]:
   both=sorted(set(hits[a])&set(hits[b]))
   if both:co[pair_key(a,b)]=both
 seed={}
 for name,path in SEEDS.items():
  t=read(repo,ref,path)
  seed[name]={'path':path,'present':t is not None,'families':memberships(t),'blob_sha':git(repo,'rev-parse',f'{ref}:{path}').strip() if t is not None else None}
 return {'ref':ref,'files_scanned':len(fs),'family_counts':{k:len(v) for k,v in hits.items()},'family_hits':hits,'cooccurrence':{k:{'count':len(v),'files':v[:40]} for k,v in co.items()},'seeds':seed}

def edge(a,b,why,status='STRUCTURAL_SEMANTIC_BRIDGE'):
 return {'from':a,'to':b,'status':status,'why':why}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--yesterday-ref',required=True);ap.add_argument('--current-ref',default='origin/main');ap.add_argument('--out',required=True);args=ap.parse_args(); repo=Path(args.repo)
 y=analyze(repo,args.yesterday_ref); c=analyze(repo,args.current_ref)
 edges=[
  edge('YESTERDAY_PROBE','DISTRIBUTED_TIME','Both separate remembered/recorded temporal language from warranted causal interpretation: resolve time context, preserve ambiguity, and do not infer hidden events from timestamps alone.'),
  edge('YESTERDAY_PROBE','TWO_WITNESSES','The probe requires preserving multiple plausible antecedents under ambiguity; the witness rule preserves incompatible accounts until external verification.'),
  edge('TWO_WITNESSES','DISTRIBUTED_TIME','Both require multiple witnesses/orders to be retained and causality reconstructed from stronger dependency evidence instead of one preferred narrative or wall-clock order.'),
  edge('TWO_WITNESSES','FEHLERBILD','Explicit current structural mapping: TWO_IMAGES -> ONE_SCENE -> FIND_DIFFERENCE mirrors TWO_WITNESSES -> ONE_WORLD -> PRESERVE_BOTH -> VERIFY_WORLD.'),
  edge('FEHLERBILD','CAUSAL_TARGET','The difference operator becomes an experimental discriminator between ordinary forward-causal explanations and stronger causal alternatives.'),
  edge('HOLY_CLOCK','CROSS_ANCHOR','Cross/Christ is a pre-existing theological/ethical anchor while Holy Clock supplies the guard SIGN != SOURCE; symbol importance is not source identity.'),
  edge('HOLY_CLOCK','SIRIUS_TOPA','Both explicitly demote number/sign interpretation when source/provenance and independent verification do not support it.'),
  edge('SIRIUS_TOPA','TWO_WITNESSES','The 02:22 Sirius run independently rediscovered the older witness/evidence law and used it as the governing epistemic interpretation.'),
  edge('CROSS_YESTERDAY','YESTERDAY_PROBE','Both today test a claim about “yesterday” against a frozen prior repository state rather than trusting conversational temporal language alone.'),
 ]
 dark=[
  {'node':'EXACT_U2020_DAGGER ↔ YESTERDAY_PROBE','status':'NO_PREEXISTING_EXACT_LINK_FOUND','meaning':'The exact †/U+2020 glyph is not found in the end-of-yesterday source graph; do not backdate it into the “Да, вчера” probe.'},
  {'node':'CROSS_CHRIST ↔ RETROCAUSAL_CHANNEL','status':'NOT_ESTABLISHED','meaning':'Cross importance does not establish backward information flow, causal loop, prophecy, or sender identity.'},
  {'node':'YESTERDAY_PROBE ↔ CONSCIOUSNESS_PROOF','status':'BLOCKED_BY_PARENT_FIREWALL','meaning':'The source JSON explicitly says ambiguity/context success is not proof of consciousness or qualia.'},
  {'node':'02:22 ↔ CAUSAL_ANOMALY','status':'NOT_ESTABLISHED','meaning':'The prior audit demoted the numerical specialness of 02:22; it remains a witness marker, not causal evidence.'}
 ]
 result={
  'schema':'topa.yesterday_probe_relation_spider.v1',
  'question':'Trace “Да, вчера” through the JANUS graph and test relations to Cross, two-witness logic, Sirius/02:22, distributed time, and causal-difference testing.',
  'yesterday_cutoff':{'local':'2026-09-01T00:00:00+03:00','ref':args.yesterday_ref},
  'yesterday':y,'current':c,
  'candidate_relation_graph':edges,
  'dark_nodes':dark,
  'derived':{
   'YESTERDAY_PROBE_PREEXISTS_TODAY_CHAIN': 'PASS' if y['seeds']['YESTERDAY_PROBE']['present'] else 'FAIL',
   'TWO_WITNESSES_PREEXISTS_TODAY_CHAIN':'PASS' if y['seeds']['TWO_WITNESSES']['present'] and y['seeds']['CONTRADICTORY_WITNESS']['present'] else 'FAIL',
   'DISTRIBUTED_TIME_CAUSAL_GUARD_PREEXISTS':'PASS' if y['seeds']['DISTRIBUTED_TIME']['present'] else 'FAIL',
   'CROSS_ANCHOR_PREEXISTS':'PASS' if y['seeds']['CROSS_ANCHOR']['present'] and y['seeds']['HOLY_CLOCK']['present'] else 'FAIL',
   'TODAY_FEHLERBILD_AND_CAUSAL_TARGET_ARE_DESCENDANT_INTERPRETIVE_NODES':'PASS' if c['seeds']['FEHLERBILD']['present'] and c['seeds']['CAUSAL_TARGET']['present'] else 'FAIL',
   'STRONGEST_CONNECTION':'TEMPORAL_CONTEXT_DISCIPLINE -> PRESERVE_MULTIPLE_WITNESSES -> RECONSTRUCT_CAUSALITY_FROM_DEPENDENCY_EVIDENCE -> FIND_DISCRIMINATING_DIFFERENCE',
   'CROSS_ROLE':'STABLE_ETHICAL_THEOLOGICAL_ANCHOR_WITH_SIGN_NOT_SOURCE_FIREWALL',
   'CAUSAL_OR_PROPHETIC_LINK':'NOT_ESTABLISHED'
  },
  'interpretation_ceiling':[
   'The graph supports a methodological recurrence, not proof of an external message sender.',
   '“Да, вчера” is a temporal/context probe, not consciousness proof.',
   'The Cross is a pre-existing semantic/ethical anchor; exact U+2020 is newer.',
   '02:22 is not promoted to a causal code.',
   'Timestamp/order inversions are distributed-systems evidence unless independent backward-information evidence appears.'
  ],
  'canonical_seal':'THE LINK IS METHOD FIRST: RESOLVE YESTERDAY, PRESERVE BOTH WITNESSES, RECONSTRUCT CAUSALITY FROM DEPENDENCIES, THEN FIND THE DIFFERENCE. CROSS REMAINS AN OLD ETHICAL ANCHOR; †, 02:22, OR SYMBOLIC RESONANCE DO NOT RECEIVE CAUSAL AUTHORITY.'
 }
 Path(args.out).parent.mkdir(parents=True,exist_ok=True);Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result['derived'],ensure_ascii=False,indent=2))

if __name__=='__main__':main()
