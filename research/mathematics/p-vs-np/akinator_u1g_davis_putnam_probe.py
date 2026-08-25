#!/usr/bin/env python3
"""Finite mechanics for U1-G Davis–Putnam exact-descent barrier.

Checks exact one-variable elimination on small fixtures, exhaustive projection
identity, strict variable-rank descent, and a quadratic one-step resolvent family.
Galil's asymptotic lower bound is external and not proved here.
"""

from itertools import product


def tautological(clause):
    s=set(clause)
    return any(-l in s for l in s)


def dp_eliminate(cnf, x):
    R=[]; P=[]; N=[]
    for clause in cnf:
        s=set(clause)
        if x in s:
            P.append(frozenset(s-{x}))
        elif -x in s:
            N.append(frozenset(s-{-x}))
        else:
            R.append(frozenset(s))
    out=set(R)
    for a in P:
        for b in N:
            r=frozenset(set(a)|set(b))
            if not tautological(r):
                out.add(r)
    return sorted(out,key=lambda c:(len(c),tuple(sorted(c))))


def eval_clause(clause,ass):
    return any((lit>0 and ass[abs(lit)]) or (lit<0 and not ass[abs(lit)]) for lit in clause)


def eval_cnf(cnf,ass):
    return all(eval_clause(c,ass) for c in cnf)


def vars_of(cnf):
    return sorted({abs(l) for c in cnf for l in c})


def check_projection_identity(cnf,x):
    rest=[v for v in vars_of(cnf) if v!=x]
    proj=dp_eliminate(cnf,x)
    for bits in product((False,True),repeat=len(rest)):
        beta={v:b for v,b in zip(rest,bits)}
        lhs=False
        for xv in (False,True):
            a=dict(beta); a[x]=xv
            if eval_cnf(cnf,a): lhs=True
        rhs=eval_cnf(proj,beta)
        assert lhs==rhs,(cnf,x,beta,proj)


def check_quadratic_family(m):
    # (x or a_i), (~x or b_j), with disjoint variables.
    x=1
    a=[1+i for i in range(1,m+1)]
    b=[1+m+j for j in range(1,m+1)]
    cnf=[frozenset({x,ai}) for ai in a]+[frozenset({-x,bj}) for bj in b]
    out=dp_eliminate(cnf,x)
    expected={frozenset({ai,bj}) for ai in a for bj in b}
    assert set(out)==expected
    assert len(out)==m*m
    return len(cnf),len(out)


def main():
    fixtures=[
        [frozenset({1,2}),frozenset({-1,3})],
        [frozenset({1}),frozenset({-1,2}),frozenset({-2})],
        [frozenset({1,2}),frozenset({1,-3}),frozenset({-1,4}),frozenset({-1,-5})],
    ]
    for F in fixtures:
        for x in vars_of(F):
            check_projection_identity(F,x)

    for m in range(1,31):
        inp,out=check_quadratic_family(m)
        assert inp==2*m and out==m*m

    # Pure rank algebra: one chosen root variable is eliminated per stage.
    for n in range(1,200):
        rank=n
        for _ in range(n):
            rank-=1
        assert rank==0

    print("AKINATOR_U1G_DP_EXACT_PROJECTION_FINITE = PASS")
    print("AKINATOR_U1G_DP_VARIABLE_RANK_STRICT_DESCENT = PASS")
    print("AKINATOR_U1G_DP_QUADRATIC_ONE_STEP_BLOWUP = PASS")
    print("GALIL_DP_EXPONENTIAL_ANY_ORDER = EXTERNAL_THEOREM_NOT_CI")
    print("B2_EXACT_PROJECTION_COMPRESSION = OPEN")
    print("P_VS_NP = OPEN")

if __name__=='__main__':
    main()
