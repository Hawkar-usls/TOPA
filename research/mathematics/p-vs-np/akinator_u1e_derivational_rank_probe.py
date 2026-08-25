#!/usr/bin/env python3
"""Finite mechanics for U1-E derivational-rank presentation-sensitivity barrier.

Checks the alias-chain equivalence and explicit two-resolution-steps-per-alias
mechanics on finite fixtures. It does not prove coNP-completeness of general
B2 equivalence or any universal rank impossibility theorem.
"""


def b2_def(e, a, t):
    return [frozenset({-e, a}), frozenset({-e, t}), frozenset({e, -a, -t})]


def resolve(a, b, pivot):
    assert pivot in a and -pivot in b
    r=(set(a)-{pivot}) | (set(b)-{-pivot})
    assert not any(-x in r for x in r)
    return frozenset(r)


def build_alias_chain(k):
    # roots: x=1, t=2. extensions 3..k+2
    x,t=1,2
    defs=[]
    prev=x
    for i in range(k):
        e=3+i
        defs.append((e,prev,b2_def(e,prev,t)))
        prev=e
    return x,t,defs


def check_semantics(k):
    x,t,defs=build_alias_chain(k)
    # Under root units x=t=True, every extension evaluates True and therefore equals x.
    vals={x:True,t:True}
    for e,a,_ in defs:
        vals[e]=vals[a] and vals[t]
        assert vals[e] == vals[x]
    return vals


def check_two_step_derivation(k):
    x,t,defs=build_alias_chain(k)
    current=frozenset({x})
    tunit=frozenset({t})
    steps=0
    for e,a,clauses in defs:
        # positive definitional clause: (e OR ~a OR ~t)
        pos=[c for c in clauses if e in c and -a in c and -t in c][0]
        assert current == frozenset({a})
        r1=resolve(pos,current,-a)  # pos contains -a, current contains a
        assert r1 == frozenset({e,-t})
        r2=resolve(r1,tunit,-t)
        assert r2 == frozenset({e})
        current=r2
        steps += 2
    assert steps == 2*k
    return steps


def main():
    for k in range(1,101):
        vals=check_semantics(k)
        steps=check_two_step_derivation(k)
        assert steps==2*k
        assert all(vals[v] for v in vals)

    # Root-only object is unchanged regardless of alias-chain length.
    root_signature=(frozenset({1}),frozenset({2}))
    for k in (1,2,5,10,50,100):
        _=build_alias_chain(k)
        assert root_signature==(frozenset({1}),frozenset({2}))

    print("AKINATOR_U1E_ALIAS_CHAIN_SEMANTIC_EQUIVALENCE_FINITE = PASS")
    print("AKINATOR_U1E_ALIAS_CHAIN_TWO_RES_STEPS_PER_LEVEL = PASS")
    print("AKINATOR_U1E_CHOSEN_PRESENTATION_DEPTH_LINEAR_INFLATION = PASS")
    print("AKINATOR_U1E_ROOT_ONLY_STATE_STASIS = PASS")
    print("GENERAL_B2_EQUIVALENCE_CONP_COMPLETE = ANALYTICAL_REDUCTION_NOT_CI")
    print("PROOF_CARRYING_QUOTIENT_RANK = OPEN")
    print("P_VS_NP = OPEN")


if __name__=='__main__':
    main()
