#!/usr/bin/env python3
"""Finite replay for C025-E2R-L1G.

Checks two distinct claims only:
1) parity has exponential exact root-CNF expansion despite a linear B2 gate DAG;
2) under the frozen crossing-monotone restriction, crossing macros flatten to
   conjunctions of local literals and ER3 clauses expand only polynomially in
   explicit macro-leaf volume.

No unrestricted ER/ER3 lower bound is inferred from this finite replay.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product

Clause = frozenset[int]


@dataclass(frozen=True)
class Gate:
    var: int
    left: int
    right: int
    crossing: bool = True


def eval_lit(lit: int, values: dict[int, bool]) -> bool:
    v = values[abs(lit)]
    return v if lit > 0 else not v


def evaluate_gates(root_assignment: dict[int, bool], gates: list[Gate]) -> dict[int, bool]:
    values = dict(root_assignment)
    for g in gates:
        values[g.var] = eval_lit(g.left, values) and eval_lit(g.right, values)
    return values


def parity_b2(n: int) -> tuple[list[Gate], int]:
    assert n >= 1
    if n == 1:
        return [], 1
    gates: list[Gate] = []
    nxt = n + 1
    y = 1
    for x in range(2, n + 1):
        t1 = nxt; nxt += 1
        t2 = nxt; nxt += 1
        yp = nxt; nxt += 1
        gates.append(Gate(t1, y, x))
        gates.append(Gate(t2, -y, -x))
        gates.append(Gate(yp, -t1, -t2))
        y = yp
    return gates, y


def exact_positive_cnf_false_rows(n: int, fn) -> set[Clause]:
    clauses: set[Clause] = set()
    for bits in product((False, True), repeat=n):
        if fn(bits):
            continue
        clauses.add(frozenset((-i if bits[i-1] else i) for i in range(1, n + 1)))
    return clauses


def check_parity_barrier() -> None:
    for n in range(2, 9):
        gates, out = parity_b2(n)
        assert len(gates) == 3 * (n - 1)
        for bits in product((False, True), repeat=n):
            roots = {i + 1: bits[i] for i in range(n)}
            values = evaluate_gates(roots, gates)
            assert values[out] == (sum(bits) % 2 == 1)
        cnf = exact_positive_cnf_false_rows(n, lambda bits: sum(bits) % 2 == 1)
        assert len(cnf) == 2 ** (n - 1)
        assert all(len(c) == n for c in cnf)


def crossing_monotone(gates: list[Gate], root_or_local_atoms: set[int]) -> bool:
    crossing_ids: set[int] = set()
    known = set(root_or_local_atoms)
    for g in gates:
        for lit in (g.left, g.right):
            v = abs(lit)
            if v not in known and v not in crossing_ids:
                raise ValueError(f"unknown/forward operand {lit}")
            if v in crossing_ids and lit < 0:
                return False
        if g.var in known or g.var in crossing_ids:
            raise ValueError("nonfresh gate id")
        if g.crossing:
            crossing_ids.add(g.var)
        else:
            known.add(g.var)
    return True


def flatten_crossing(var: int, gate_map: dict[int, Gate], local_atoms: set[int]) -> tuple[int, ...]:
    def flat_lit(lit: int) -> list[int]:
        v = abs(lit)
        if v in local_atoms:
            return [lit]
        g = gate_map[v]
        if lit < 0:
            raise ValueError("negative crossing dependency is not monotone")
        return flat_lit(g.left) + flat_lit(g.right)

    out = flat_lit(var)
    seen: set[int] = set()
    uniq: list[int] = []
    for lit in out:
        if lit not in seen:
            seen.add(lit)
            uniq.append(lit)
    return tuple(uniq)


def expand_clause_monotone(clause: tuple[int, ...], macros: dict[int, tuple[int, ...]]) -> set[Clause]:
    acc: set[Clause] = {frozenset()}
    for lit in clause:
        v = abs(lit)
        if v not in macros:
            options = [frozenset({lit})]
        elif lit > 0:
            options = [frozenset({leaf}) for leaf in macros[v]]
        else:
            options = [frozenset({-leaf for leaf in macros[v]})]
        nxt: set[Clause] = set()
        for a in acc:
            for b in options:
                c = frozenset(a | b)
                if not any(-x in c for x in c):
                    nxt.add(c)
        acc = nxt
    return acc


def resolve(p: Clause, q: Clause, pivot: int) -> Clause | None:
    if pivot not in p or -pivot not in q:
        return None
    c = frozenset((p - {pivot}) | (q - {-pivot}))
    if any(-x in c for x in c):
        return None
    return c


def check_monotone_flattening_and_expansion() -> None:
    gates = [Gate(20, 1, 2), Gate(21, 20, 3), Gate(22, 21, -4)]
    locals_ = set(range(1, 9))
    assert crossing_monotone(gates, locals_)
    gm = {g.var: g for g in gates}
    macros = {v: flatten_crossing(v, gm, locals_) for v in (20, 21, 22)}
    assert macros[20] == (1, 2)
    assert macros[21] == (1, 2, 3)
    assert macros[22] == (1, 2, 3, -4)

    assert len(expand_clause_monotone((22,), macros)) == 4
    assert expand_clause_monotone((-22,), macros) == {frozenset({-1, -2, -3, 4})}

    # Cartesian choices are an UPPER bound, not an equality: overlapping macro
    # leaves can canonicalize to the same clause. This fixture intentionally
    # overlaps supports and should produce 11 distinct clauses, <= 2*3*4.
    c = expand_clause_monotone((20, 21, 22), macros)
    assert len(c) == 11
    assert len(c) <= 2 * 3 * 4
    assert len(c) <= (1 + sum(len(x) for x in macros.values())) ** 3

    bad = [Gate(20, 1, 2), Gate(21, -20, 3)]
    assert not crossing_monotone(bad, locals_)


def check_flattened_pivot() -> None:
    for r in range(2, 9):
        leaves = list(range(1, r + 1))
        A, B = 100, 101
        cur = frozenset({B, *(-x for x in leaves)})
        for leaf in leaves:
            nxt = resolve(frozenset({A, leaf}), cur, leaf)
            assert nxt is not None
            cur = nxt
        assert cur == frozenset({A, B})


def main() -> None:
    check_parity_barrier()
    check_monotone_flattening_and_expansion()
    check_flattened_pivot()
    print("C025_E2R_L1G_PARITY_LINEAR_B2_GATE_COUNT = PASS")
    print("C025_E2R_L1G_PARITY_EXACT_CNF_EXPONENTIAL = PASS")
    print("C025_E2R_L1G_GENERIC_POLY_ELIMINATION_ROUTE = REFUTED")
    print("C025_E2R_L1G_CROSSING_MONOTONE_ADMISSION = PASS")
    print("C025_E2R_L1G_MONOTONE_FLATTENING = PASS")
    print("C025_E2R_L1G_OVERLAP_CANONICALIZATION = PASS")
    print("C025_E2R_L1G_ER3_MACRO_CLAUSE_POLY_UPPER_BOUND = PASS")
    print("C025_E2R_L1G_FLATTENED_PIVOT_CHAIN = PASS")
    print("C025_E2R_L1G_NEGATIVE_CROSSING_DEPENDENCY_REJECTION = PASS")
    print("claim_boundary = finite mechanics only; restricted asymptotic consequence uses the established NW local-functional lower bound")


if __name__ == "__main__":
    main()
