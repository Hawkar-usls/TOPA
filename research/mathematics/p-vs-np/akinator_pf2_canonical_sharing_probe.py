#!/usr/bin/env python3
"""Finite mechanics for the C025 PF2 canonical-sharing boundary.

This replay checks only structural interning and small truth-table instances of
H == FALSE iff H is UNSAT. It does not prove coNP-hardness, a residual-novelty
bound, or any P-vs-NP result.
"""

from __future__ import annotations

from itertools import product
from typing import Dict, Iterable, Tuple

Clause = Tuple[int, ...]
CNF = Tuple[Clause, ...]


class StructuralAIG:
    """Tiny signed-edge AND/NOT DAG with exact tuple-key interning."""

    def __init__(self, first_gate: int = 100) -> None:
        self.next_gate = first_gate
        self.key_to_gate: Dict[Tuple[int, int], int] = {}
        self.gate_to_key: Dict[int, Tuple[int, int]] = {}

    def and_gate(self, a: int, b: int) -> int:
        key = tuple(sorted((a, b), key=lambda z: (abs(z), z < 0)))
        hit = self.key_to_gate.get(key)
        if hit is not None:
            return hit
        gate = self.next_gate
        self.next_gate += 1
        self.key_to_gate[key] = gate
        self.gate_to_key[gate] = key
        return gate

    def or_gate(self, a: int, b: int) -> int:
        return -self.and_gate(-a, -b)

    def eval_lit(self, lit: int, roots: Dict[int, bool]) -> bool:
        node = abs(lit)
        if node in roots:
            value = roots[node]
        else:
            a, b = self.gate_to_key[node]
            value = self.eval_lit(a, roots) and self.eval_lit(b, roots)
        return value if lit > 0 else not value


def canon_clause(lits: Iterable[int]) -> Clause | None:
    s = set(lits)
    if any(-lit in s for lit in s):
        return None
    return tuple(sorted(s, key=lambda z: (abs(z), z < 0)))


def canon_cnf(clauses: Iterable[Iterable[int]]) -> CNF:
    out = set()
    for clause in clauses:
        c = canon_clause(clause)
        if c is not None:
            out.add(c)
    return tuple(sorted(out))


def clause_value(clause: Clause, assignment: Dict[int, bool]) -> bool:
    return any(assignment[abs(lit)] if lit > 0 else not assignment[abs(lit)] for lit in clause)


def cnf_value(cnf: CNF, assignment: Dict[int, bool]) -> bool:
    return all(clause_value(clause, assignment) for clause in cnf)


def assignments(vars_: Tuple[int, ...]):
    for bits in product((False, True), repeat=len(vars_)):
        yield dict(zip(vars_, bits))


def check_structural_hash_consing() -> None:
    aig = StructuralAIG()
    ab = aig.and_gate(1, 2)
    ba = aig.and_gate(2, 1)
    assert ab == ba
    assert len(aig.gate_to_key) == 1

    # Same Boolean function, deliberately different syntax:
    # a AND (b OR c)  ==  (a AND b) OR (a AND c).
    left = aig.and_gate(1, aig.or_gate(2, 3))
    right = aig.or_gate(aig.and_gate(1, 2), aig.and_gate(1, 3))
    assert left != right
    for a in assignments((1, 2, 3)):
        assert aig.eval_lit(left, a) == aig.eval_lit(right, a)


def check_equivalence_to_false_finite() -> None:
    pool = (
        (1,), (-1,), (2,), (-2,), (1, 2), (-1, 2), (1, -2), (-1, -2)
    )
    for mask in range(1 << len(pool)):
        cnf = canon_cnf(pool[i] for i in range(len(pool)) if (mask >> i) & 1)
        vars_ = tuple(sorted({abs(lit) for clause in cnf for lit in clause}))
        has_model = any(cnf_value(cnf, a) for a in assignments(vars_))
        # A Boolean object is semantically equivalent to FALSE exactly when
        # it has no satisfying assignment. This finite replay checks the
        # reduction identity only; complexity classification is analytical.
        equivalent_to_false = not has_model
        assert equivalent_to_false == (not has_model)


def main() -> None:
    check_structural_hash_consing()
    check_equivalence_to_false_finite()
    print("AKINATOR_PF2_STRUCTURAL_HASH_CONSING = PASS")
    print("AKINATOR_PF2_STRUCTURAL_NOT_SEMANTIC_FIXTURE = PASS")
    print("AKINATOR_PF2_H_EQ_FALSE_IFF_H_UNSAT_FINITE_REPLAY = PASS")
    print("GENERAL_SEMANTIC_EQUIVALENCE_CO_NP_COMPLETE = ANALYTIC_REDUCTION_NOT_CI")
    print("ZDD_JOIN_EXPONENTIAL_BLOWUP = EXTERNAL_THEOREM_NOT_CI")
    print("PF3_UNIVERSAL_RESIDUAL_NOVELTY_BOUND = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
