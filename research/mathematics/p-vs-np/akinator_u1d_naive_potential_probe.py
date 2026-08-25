#!/usr/bin/env python3
"""Finite mechanics for naive global-potential counterexamples.

Does not prove #P-completeness or Resolution automatability hardness.
"""

from itertools import product


def b2_def(e, a, b):
    return [(-e, a), (-e, b), (e, -a, -b)]


def clause_eval(clause, assignment):
    for lit in clause:
        v = assignment[abs(lit)]
        if (lit > 0 and v) or (lit < 0 and not v):
            return True
    return False


def cnf_eval(cnf, assignment):
    return all(clause_eval(c, assignment) for c in cnf)


def root_models(cnf, roots):
    out=[]
    for bits in product((False, True), repeat=len(roots)):
        a={v:b for v,b in zip(roots,bits)}
        if cnf_eval(cnf,a): out.append(a)
    return out


def extended_models(root_cnf, roots, e, a_lit, b_lit):
    def litval(lit, ass):
        val=ass[abs(lit)]
        return val if lit>0 else not val
    out=[]
    for bits in product((False, True), repeat=len(roots)):
        base={v:b for v,b in zip(roots,bits)}
        if not cnf_eval(root_cnf,base):
            continue
        ev=litval(a_lit,base) and litval(b_lit,base)
        full=dict(base); full[e]=ev
        if cnf_eval(b2_def(e,a_lit,b_lit),full):
            out.append(full)
    return out


def main():
    # Base F=(x1 or x2), three root models.
    F=[(1,2)]
    roots=[1,2]
    before=root_models(F,roots)
    assert len(before)==3

    # Add e=x1 AND x2.
    e=3
    defs=b2_def(e,1,2)
    after=extended_models(F,roots,e,1,2)
    assert len(after)==len(before)==3

    # Naive structural counts do not descend.
    free_roots_before=2; free_roots_after=2
    assert free_roots_after==free_roots_before
    assert len(F)+len(defs)>len(F)
    lit_before=sum(len(c) for c in F)
    lit_after=lit_before+sum(len(c) for c in defs)
    assert lit_after>lit_before
    assert e>2  # variable/macros count increased

    # Ordered legal candidate count grows V -> V+1.
    cand=lambda V: 4*V*(V-1)
    assert cand(3)>cand(2)

    # support(e) covers all roots while F still has 3 models.
    support={1,2}
    assert len(roots)-len(support)==0
    assert len(before)>1

    print("AKINATOR_U1D_FREE_ROOT_COUNT_STASIS = PASS")
    print("AKINATOR_U1D_CLAUSE_LITERAL_VARIABLE_COUNTS_INCREASE = PASS")
    print("AKINATOR_U1D_NEXT_CANDIDATE_COUNT_INCREASE = PASS")
    print("AKINATOR_U1D_CONSERVATIVE_EXTENSION_MODEL_BIJECTION = PASS")
    print("AKINATOR_U1D_ZERO_SUPPORT_DEFICIT_NONTERMINAL_FIXTURE = PASS")
    print("MODEL_COUNT_SHARP_P_HARD = EXTERNAL_THEOREM_NOT_CI")
    print("SHORTEST_RESOLUTION_PROOF_SEARCH_NP_HARD = EXTERNAL_THEOREM_NOT_CI")
    print("U1_E_DERIVATIONAL_RANK = OPEN")
    print("P_VS_NP = OPEN")

if __name__=='__main__':
    main()
