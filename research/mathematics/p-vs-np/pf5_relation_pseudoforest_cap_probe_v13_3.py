#!/usr/bin/env python3
"""PF5 relation-pseudoforest signature cap probe v13.3.

Post-hoc only on the already-observed seed 909002.  This tests a polynomial
extension of v3: greedily retain a strongest-first pseudoforest of certified
binary projected-clause relations (at most one cycle per connected component),
then count its allowed bit patterns exactly.

For a unicyclic component, remove its unique cycle-closing edge e=(u,v).  The
remaining graph is a tree.  For each of the at most four endpoint pairs allowed
by e, run exact tree DP with u and v fixed and sum the counts.  Thus counting is
O(poly(n)) and no arbitrary relation-graph #counting oracle is introduced.
Ignoring rejected sound relation edges only loosens the signature bound.
"""
from __future__ import annotations

import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import pf5_slime_pswidth_blind_probe_v9 as v9

SEED=909002; N=5; M=7
PREFIX=['c:0','v:1','c:1','v:2','c:3']; CHOICES=['c:2','c:5','c:6']


def load(path):
    spec=importlib.util.spec_from_file_location('slime_v3_pseudoforest_probe',path)
    if spec is None or spec.loader is None: raise RuntimeError('cannot load')
    m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m
    try: spec.loader.exec_module(m)
    except Exception: sys.modules.pop(spec.name,None); raise
    return m


def distinct_projected(formula,indices,vars_):
    s=set()
    for i in sorted(indices):
        p=frozenset(l for l in formula[i] if abs(l) in vars_)
        if p:s.add(p)
    return sorted(s,key=lambda c:(len(c),tuple(sorted(c))))


def all_edges(p,clauses):
    rows=[]
    for i in range(len(clauses)):
        for j in range(i+1,len(clauses)):
            allowed,reasons=p._allowed_pairs(clauses[i],clauses[j])
            if len(allowed)<4: rows.append((len(allowed),i,j,tuple(allowed),tuple(reasons)))
    return sorted(rows,key=lambda r:(r[0],r[1],r[2]))


class DSU:
    def __init__(self,n): self.p=list(range(n)); self.cycle=[False]*n
    def find(self,x):
        while self.p[x]!=x:
            self.p[x]=self.p[self.p[x]]; x=self.p[x]
        return x
    def add_edge(self,a,b):
        ra,rb=self.find(a),self.find(b)
        if ra==rb:
            if self.cycle[ra]: return False
            self.cycle[ra]=True; return True
        if self.cycle[ra] and self.cycle[rb]: return False
        if ra>rb:ra,rb=rb,ra
        cyc=self.cycle[ra] or self.cycle[rb]
        self.p[rb]=ra; self.cycle[ra]=cyc
        return True


def pseudoforest_edges(p,clauses):
    d=DSU(len(clauses)); out=[]
    for strength,i,j,allowed,reasons in all_edges(p,clauses):
        if d.add_edge(i,j): out.append((i,j,allowed,reasons))
    return out


def tree_count(n,edges,fixed=None):
    fixed=fixed or {}
    adj=[[] for _ in range(n)]
    for i,j,allowed,_ in edges:
        A=set(allowed); adj[i].append((j,A,False)); adj[j].append((i,A,True))
    seen=set(); total=1
    for root in range(n):
        if root in seen: continue
        parent={root:-1}; pedge={}; order=[root]; seen.add(root)
        for u in order:
            for w,A,rev in adj[u]:
                if w in parent: continue
                parent[w]=u; pedge[w]=(A,rev); order.append(w); seen.add(w)
        dp={}
        for u in reversed(order):
            vals=[0,0]
            for uv in (0,1):
                if u in fixed and fixed[u]!=uv: continue
                count=1
                for child,par in parent.items():
                    if par!=u: continue
                    A,rev=pedge[child]; subtotal=0
                    for cv in (0,1):
                        pair=(cv,uv) if rev else (uv,cv)
                        if pair in A: subtotal+=dp[child][cv]
                    count*=subtotal
                vals[uv]=count
            dp[u]=vals
        total*=dp[root][0]+dp[root][1]
    return total


def count_pseudoforest(n,edges):
    # Split selected pseudoforest into components and identify the unique cycle
    # edge, if any, by deterministic union-find replay.
    adj=[[] for _ in range(n)]
    for k,(i,j,A,R) in enumerate(edges):
        adj[i].append((j,k)); adj[j].append((i,k))
    seen=set(); result=1
    for start in range(n):
        if start in seen:continue
        verts=[]; edge_ids=set(); stack=[start]; seen.add(start)
        while stack:
            u=stack.pop(); verts.append(u)
            for w,k in adj[u]:
                edge_ids.add(k)
                if w not in seen: seen.add(w); stack.append(w)
        comp_edges=[edges[k] for k in sorted(edge_ids)]
        if len(comp_edges)<=len(verts)-1:
            # Tree component; isolated vertices included.
            result*=tree_count(n,comp_edges,{}) if comp_edges else 2
            continue
        if len(comp_edges)!=len(verts): raise AssertionError('not pseudoforest')
        # Find one closing edge under deterministic replay.
        parent={v:v for v in verts}
        def find(x):
            while parent[x]!=x:
                parent[x]=parent[parent[x]]; x=parent[x]
            return x
        closing=None; tree=[]
        for e in comp_edges:
            i,j=e[0],e[1]; a,b=find(i),find(j)
            if a==b:
                if closing is not None: raise AssertionError('multiple cycles')
                closing=e
            else:
                if a>b:a,b=b,a
                parent[b]=a; tree.append(e)
        if closing is None: raise AssertionError('missing cycle edge')
        u,v,allowed,_=closing; subtotal=0
        for a,b in allowed:
            subtotal += tree_count(n,tree,{u:a,v:b})
        # tree_count includes isolated vertices outside this component; divide
        # them out exactly. This diagnostic keeps n tiny and explicit.
        outside=n-len(verts)
        subtotal//=2**outside
        result*=subtotal
    return result


def side(p,formula,indices,vars_):
    clauses=distinct_projected(formula,indices,vars_); edges=pseudoforest_edges(p,clauses)
    pattern=count_pseudoforest(len(clauses),edges)
    assignment=1<<len(vars_)
    return {'clause_count':len(clauses),'edge_count':len(edges),'cycle_rank':max(0,len(edges)-len(clauses)+1) if clauses else 0,'pattern_bound':pattern,'signature_cap':min(assignment,pattern)}


def cap(p,formula,selected):
    allc=set(range(len(formula))); allv={abs(l) for c in formula for l in c}
    sv={int(x.split(':',1)[1]) for x in selected if x.startswith('v:')}; sc={int(x.split(':',1)[1]) for x in selected if x.startswith('c:')}; rv=allv-sv
    L=side(p,formula,allc-sc,sv); R=side(p,formula,sc,rv)
    return {'left':L,'right':R,'combined_cap':max(L['signature_cap'],R['signature_cap'])}


def run(p,identity):
    formula=v9.random_connected_3cnf(SEED,N,M); rows=[]
    for choice in CHOICES: rows.append({'choice':choice,'cap':cap(p,formula,set(PREFIX+[choice]))})
    good=next(r for r in rows if r['choice']=='c:2')['cap']['combined_cap'] < next(r for r in rows if r['choice']=='c:5')['cap']['combined_cap']
    result={'artifact_id':'PF5-RELATION-PSEUDOFOREST-CAP-PROBE-V13.3','status':'POSTHOC_THEOREM_FEATURE_PROBE_COMPLETE','seed':SEED,'posthoc_not_holdout':True,'producer':identity,'prefix':PREFIX,'rows':rows,'pseudoforest_cap_distinguishes_c2_from_c5':good,'theorem':{'at_most_one_cycle_per_component':True,'unicyclic_count_by_break_edge_and_four_endpoint_conditions':True,'rejected_sound_edges_only_loosen_upper_bound':True,'source_only':True,'polynomial_feature_construction':True,'no_arbitrary_relation_graph_counting':True},'p_vs_np':'OPEN'}
    payload=json.dumps(result,sort_keys=True,separators=(',',':')).encode(); result['result_sha256']=hashlib.sha256(payload).hexdigest(); return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--producer-path',type=Path,required=True); ap.add_argument('--json-out',type=Path); a=ap.parse_args(); raw=a.producer_path.read_bytes(); p=load(a.producer_path)
    r=run(p,{'path':str(a.producer_path),'file_sha256':hashlib.sha256(raw).hexdigest(),'role':'PINNED_V3_POSTHOC_PSEUDOFOREST_PROBE'})
    if a.json_out:a.json_out.write_text(json.dumps(r,indent=2,sort_keys=True),encoding='utf-8')
    print('PF5_RELATION_PSEUDOFOREST_CAP_PROBE_V13_3 =',r['status'])
    for row in r['rows']:print(row['choice'],row['cap'])
    print('DISTINGUISHES =',r['pseudoforest_cap_distinguishes_c2_from_c5']); print('P_VS_NP = OPEN'); print('RESULT_SHA256 =',r['result_sha256'])
if __name__=='__main__':main()
