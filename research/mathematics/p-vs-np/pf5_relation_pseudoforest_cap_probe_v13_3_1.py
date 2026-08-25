#!/usr/bin/env python3
"""v13.3.1: component-local repair of the pseudoforest counter.

The v13.3 theorem and frozen diagnostic source are unchanged.  This wrapper
repairs only a pre-provider implementation bug: tree_count must receive the
vertices of one relation component, not the global relation-graph vertex count.
"""
from __future__ import annotations

import pf5_relation_pseudoforest_cap_probe_v13_3 as base


def count_pseudoforest_repaired(n, edges):
    adj=[[] for _ in range(n)]
    for k,(i,j,A,R) in enumerate(edges):
        adj[i].append((j,k)); adj[j].append((i,k))
    seen=set(); result=1
    for start in range(n):
        if start in seen: continue
        verts=[]; edge_ids=set(); stack=[start]; seen.add(start)
        while stack:
            u=stack.pop(); verts.append(u)
            for w,k in adj[u]:
                edge_ids.add(k)
                if w not in seen:
                    seen.add(w); stack.append(w)
        if not edge_ids:
            result*=2
            continue
        mapping={v:i for i,v in enumerate(sorted(verts))}
        comp=[]
        for k in sorted(edge_ids):
            i,j,allowed,reasons=edges[k]
            comp.append((mapping[i],mapping[j],allowed,reasons))
        local_n=len(mapping)
        if len(comp)<=local_n-1:
            result*=base.tree_count(local_n,comp,{})
            continue
        if len(comp)!=local_n:
            raise AssertionError('not pseudoforest')
        parent=list(range(local_n))
        def find(x):
            while parent[x]!=x:
                parent[x]=parent[parent[x]]; x=parent[x]
            return x
        closing=None; tree=[]
        for e in comp:
            i,j=e[0],e[1]; a,b=find(i),find(j)
            if a==b:
                if closing is not None: raise AssertionError('multiple cycles')
                closing=e
            else:
                if a>b:a,b=b,a
                parent[b]=a; tree.append(e)
        if closing is None: raise AssertionError('missing cycle edge')
        u,v,allowed,_=closing
        subtotal=0
        for a,b in allowed:
            subtotal+=base.tree_count(local_n,tree,{u:a,v:b})
        result*=subtotal
    return result


base.count_pseudoforest=count_pseudoforest_repaired

if __name__=='__main__':
    base.main()
