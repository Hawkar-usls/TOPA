#!/usr/bin/env python3
"""C025-E2R-L1E finite transfer-mechanics probe.

Checks only finite mechanics used by the paper theorem transfer:
- choose b outside a small NW-parity image;
- build the direct root-only truth-table CNF and brute-check UNSAT;
- verify every direct clause satisfies Sokolov functional-encoding semantic admission;
- verify same-neighborhood B2 AND-definition clauses satisfy semantic admission;
- reject a cross-neighborhood extension from the frozen NW-local restriction.

The asymptotic lower bound comes from the external heavy-width theorem plus the
proved parameter map, not from this finite replay.
"""
from __future__ import annotations
from itertools import product
from typing import Callable

Assignment = dict[int, bool]
Clause = tuple[int, ...]


def parity_on(neighborhood: tuple[int, ...], assignment: Assignment) -> bool:
    out = False
    for v in neighborhood:
        out ^= assignment[v]
    return out


def image_of_generator(n: int, neighborhoods: list[tuple[int, ...]]) -> set[tuple[bool, ...]]:
    image = set()
    for bits in product([False, True], repeat=n):
        a = {i + 1: bits[i] for i in range(n)}
        image.add(tuple(parity_on(nb, a) for nb in neighborhoods))
    return image


def choose_outside_image(n: int, neighborhoods: list[tuple[int, ...]]) -> tuple[bool, ...]:
    image = image_of_generator(n, neighborhoods)
    for b in product([False, True], repeat=len(neighborhoods)):
        if b not in image:
            return b
    raise AssertionError("small generator happened to be surjective")


def forbidding_clause(neighborhood: tuple[int, ...], local_bits: tuple[bool, ...]) -> Clause:
    # Clause false exactly on local_bits.
    return tuple(-v if bit else v for v, bit in zip(neighborhood, local_bits))


def direct_parity_cnf(
    neighborhoods: list[tuple[int, ...]],
    b: tuple[bool, ...],
) -> tuple[Clause, ...]:
    clauses: list[Clause] = []
    for nb, target in zip(neighborhoods, b):
        for local_bits in product([False, True], repeat=len(nb)):
            if (sum(local_bits) % 2 == 1) != target:
                clauses.append(forbidding_clause(nb, local_bits))
    return tuple(clauses)


def clause_satisfied(clause: Clause, assignment: Assignment) -> bool:
    return any(assignment[abs(lit)] if lit > 0 else not assignment[abs(lit)] for lit in clause)


def cnf_satisfied(cnf: tuple[Clause, ...], assignment: Assignment) -> bool:
    return all(clause_satisfied(c, assignment) for c in cnf)


def projection(v: int) -> Callable[[Assignment], bool]:
    return lambda a: a[v]


def semantic_clause_admitted(
    neighborhood: tuple[int, ...],
    target: bool,
    literal_functions: list[tuple[Callable[[Assignment], bool], bool]],
) -> bool:
    """Functional-encoding semantic condition.

    literal tuple is (function, positive_polarity). The clause is admitted if
    every local assignment satisfying parity(neighborhood)=target makes at
    least one literal true.
    """
    all_vars = tuple(sorted(set(neighborhood)))
    for bits in product([False, True], repeat=len(all_vars)):
        a = {v: bits[i] for i, v in enumerate(all_vars)}
        if parity_on(neighborhood, a) != target:
            continue
        sat = False
        for fn, positive in literal_functions:
            value = fn(a)
            sat |= value if positive else not value
        if not sat:
            return False
    return True


def support_union(*supports: set[int]) -> set[int]:
    out: set[int] = set()
    for s in supports:
        out |= s
    return out


def containing_neighborhood(support: set[int], neighborhoods: list[tuple[int, ...]]) -> int | None:
    for i, nb in enumerate(neighborhoods):
        if support <= set(nb):
            return i
    return None


def main() -> None:
    # Small non-surjective NW-style parity generator. All neighborhoods have Delta=2.
    n = 3
    neighborhoods = [(1, 2), (2, 3), (1, 2), (2, 3)]
    b = choose_outside_image(n, neighborhoods)
    assert b not in image_of_generator(n, neighborhoods)

    cnf = direct_parity_cnf(neighborhoods, b)
    assert len(cnf) == len(neighborhoods) * 2  # 2^(Delta-1) clauses/output.

    # Direct CNF is UNSAT exactly for outside-image b.
    for bits in product([False, True], repeat=n):
        a = {i + 1: bits[i] for i in range(n)}
        assert not cnf_satisfied(cnf, a)

    # Every direct root clause is a semantic functional-encoding axiom for
    # the output whose violating assignment it forbids.
    cursor = 0
    for nb, target in zip(neighborhoods, b):
        for local_bits in product([False, True], repeat=len(nb)):
            if (sum(local_bits) % 2 == 1) == target:
                continue
            clause = cnf[cursor]
            cursor += 1
            literal_functions = [
                (projection(abs(lit)), lit > 0)
                for lit in clause
            ]
            assert semantic_clause_admitted(nb, target, literal_functions)

    # Same-neighborhood B2 extension e = x1 AND (NOT x2).
    nb_index = containing_neighborhood({1, 2}, neighborhoods)
    assert nb_index is not None
    nb = neighborhoods[nb_index]
    target = b[nb_index]

    g = projection(1)
    h = projection(2)
    s = lambda a: g(a) and (not h(a))

    # (~s OR g), (~s OR ~h), (s OR ~g OR h)
    assert semantic_clause_admitted(nb, target, [(s, False), (g, True)])
    assert semantic_clause_admitted(nb, target, [(s, False), (h, False)])
    assert semantic_clause_admitted(nb, target, [(s, True), (g, False), (h, True)])

    # Cross-neighborhood support {1,3} is not legal in this frozen graph.
    assert containing_neighborhood({1, 3}, neighborhoods) is None

    print("C025_E2R_L1E_OUTSIDE_IMAGE_FIXTURE = PASS")
    print("C025_E2R_L1E_DIRECT_PARITY_CNF_UNSAT = PASS")
    print("C025_E2R_L1E_DIRECT_ROOT_AXIOM_SEMANTIC_INCLUSION = PASS")
    print("C025_E2R_L1E_SAME_NEIGHBORHOOD_EXTENSION_AXIOM_INCLUSION = PASS")
    print("C025_E2R_L1E_CROSS_NEIGHBORHOOD_REJECTION = PASS")
    print(f"fixture_root_vars = {n}")
    print(f"fixture_outputs = {len(neighborhoods)}")
    print(f"fixture_direct_clauses = {len(cnf)}")
    print("claim_boundary = finite transfer mechanics only; asymptotic lower bound relies on the cited heavy-width theorem and proved parameter map")


if __name__ == "__main__":
    main()
