#!/usr/bin/env python3
"""Finite mechanics for C025 Akinator proof-carrying elimination selector.

This probe exhausts all small CNFs with <=3 clauses on <=3 variables and checks
Davis–Putnam elimination against direct existential projection. It also verifies
an explicit complete-resolvent certificate, cap-aware first-fit mechanics on a
finite fixture set, and the finite algebra of degree drift.

It does NOT prove universal ELIM-CAP_C availability or P=NP.
"""

from __future__ import annotations

from itertools import combinations, product
from typing import Dict, FrozenSet, Iterable, List, Sequence, Tuple

Lit = int
Clause = FrozenSet[Lit]
CNF = Tuple[Clause, ...]


def canonical_clause(lits: Iterable[Lit]) -> Clause:
    return frozenset(lits)


def is_tautology(c: Clause) -> bool:
    return any(-x in c for x in c)


def canon_cnf(clauses: Iterable[Clause]) -> CNF:
    unique = {c for c in clauses if not is_tautology(c)}
    return tuple(sorted(unique, key=lambda c: (len(c), tuple(sorted(c)))))


def all_non_tautological_clauses(n: int) -> List[Clause]:
    # State per variable: 0 absent, +1 positive, -1 negative.
    out: List[Clause] = []
    for states in product((-1, 0, 1), repeat=n):
        lits = []
        for i, s in enumerate(states, 1):
            if s == 1:
                lits.append(i)
            elif s == -1:
                lits.append(-i)
        out.append(frozenset(lits))
    assert len(out) == 3**n
    return out


def eval_clause(c: Clause, assignment: Dict[int, bool]) -> bool:
    if not c:
        return False
    return any((lit > 0) == assignment[abs(lit)] for lit in c)


def eval_cnf(F: CNF, assignment: Dict[int, bool]) -> bool:
    return all(eval_clause(c, assignment) for c in F)


def vars_of(F: CNF) -> Tuple[int, ...]:
    return tuple(sorted({abs(l) for c in F for l in c}))


def resolve_pair(C: Clause, D: Clause, x: int):
    assert x in C and -x in D
    r = frozenset((C - {x}) | (D - {-x}))
    if is_tautology(r):
        witness = next(abs(l) for l in r if -l in r)
        return None, witness
    return r, None


def eliminate_with_certificate(F: CNF, x: int):
    P = tuple(c for c in F if x in c)
    N = tuple(c for c in F if -x in c)
    R = tuple(c for c in F if x not in c and -x not in c)

    pair_records = []
    resolvents = []
    for C in P:
        for D in N:
            r, taut_witness = resolve_pair(C, D, x)
            pair_records.append((C, D, r, taut_witness))
            if r is not None:
                resolvents.append(r)

    out = canon_cnf((*R, *resolvents))
    cert = {
        "pivot": x,
        "P": P,
        "N": N,
        "R": R,
        "pairs": tuple(pair_records),
        "output": out,
    }
    return out, cert


def verify_certificate(F: CNF, cert) -> bool:
    x = cert["pivot"]
    P = tuple(c for c in F if x in c)
    N = tuple(c for c in F if -x in c)
    R = tuple(c for c in F if x not in c and -x not in c)
    if cert["P"] != P or cert["N"] != N or cert["R"] != R:
        return False
    expected_records = []
    expected_res = []
    for C in P:
        for D in N:
            r, w = resolve_pair(C, D, x)
            expected_records.append((C, D, r, w))
            if r is not None:
                expected_res.append(r)
    if cert["pairs"] != tuple(expected_records):
        return False
    expected_out = canon_cnf((*R, *expected_res))
    return cert["output"] == expected_out


def projection_equivalent(F: CNF, G: CNF, x: int, universe: Sequence[int]) -> bool:
    remaining = [v for v in universe if v != x]
    for bits in product((False, True), repeat=len(remaining)):
        alpha = dict(zip(remaining, bits))
        lhs = eval_cnf(G, alpha)
        rhs = False
        for xv in (False, True):
            full = dict(alpha)
            full[x] = xv
            if eval_cnf(F, full):
                rhs = True
                break
        if lhs != rhs:
            return False
    return True


def exhaustive_small_cnf_elimination() -> int:
    checked = 0
    for n in range(1, 4):
        clauses = all_non_tautological_clauses(n)
        # Exhaust every distinct CNF with 0..3 clauses.
        for m in range(0, 4):
            for chosen in combinations(clauses, m):
                F = canon_cnf(chosen)
                for x in range(1, n + 1):
                    G, cert = eliminate_with_certificate(F, x)
                    assert verify_certificate(F, cert)
                    assert x not in vars_of(G)
                    assert projection_equivalent(F, G, x, list(range(1, n + 1)))
                    checked += 1
    assert checked > 10_000
    return checked


def tamper_rejection() -> None:
    F = canon_cnf([
        frozenset({1, 2}),
        frozenset({-1, 3}),
        frozenset({-2, -3}),
    ])
    G, cert = eliminate_with_certificate(F, 1)
    assert verify_certificate(F, cert)

    bad = dict(cert)
    bad["output"] = canon_cnf((*G, frozenset({2})))
    assert not verify_certificate(F, bad)

    bad2 = dict(cert)
    bad2["pivot"] = 2
    assert not verify_certificate(F, bad2)


def serialized_size_units(F: CNF) -> int:
    # Exact finite fixture metric: one unit per clause record plus one per literal.
    return sum(1 + len(c) for c in F)


def first_fit_cap(F: CNF, original_N: int, C: int):
    cap = original_N**C
    for x in vars_of(F):
        G, cert = eliminate_with_certificate(F, x)
        if serialized_size_units(G) <= cap:
            assert verify_certificate(F, cert)
            return x, G, cert
    return None


def check_cap_first_fit_finite() -> None:
    fixtures = [
        canon_cnf([]),
        canon_cnf([frozenset({1})]),
        canon_cnf([frozenset({1, 2}), frozenset({-1, 2})]),
        canon_cnf([
            frozenset({1, 2}), frozenset({-1, 3}),
            frozenset({-2, 4}), frozenset({-3, -4}),
        ]),
    ]
    for F in fixtures:
        original_N = max(2, serialized_size_units(F))
        current = F
        prev_var_count = len(vars_of(current))
        for _ in range(16):
            if not vars_of(current):
                break
            picked = first_fit_cap(current, original_N, C=3)
            assert picked is not None
            _, nxt, cert = picked
            assert verify_certificate(current, cert)
            assert len(vars_of(nxt)) <= prev_var_count - 1
            current = nxt
            prev_var_count = len(vars_of(current))
        assert not vars_of(current)
        # Terminal CNF is exact SAT truth value on zero variables.
        terminal_sat = eval_cnf(current, {})
        original_sat = any(
            eval_cnf(F, dict(zip(vars_of(F), bits)))
            for bits in product((False, True), repeat=len(vars_of(F)))
        )
        assert terminal_sat == original_sat


def check_degree_drift_algebra() -> None:
    # Finite recurrence witness for the statement that repeated squaring doubles
    # the exponent relative to the original symbolic base N.
    exponent = 1
    seq = []
    for t in range(9):
        seq.append(exponent)
        assert exponent == 2**t
        exponent *= 2
    assert seq[-1] == 256


def check_boundary_clause_ceiling() -> None:
    # A non-tautological clause over w variables is encoded by absent/+/- per var.
    for w in range(0, 10):
        assert len(all_non_tautological_clauses(w)) == 3**w


def main() -> None:
    checked = exhaustive_small_cnf_elimination()
    tamper_rejection()
    check_cap_first_fit_finite()
    check_degree_drift_algebra()
    check_boundary_clause_ceiling()
    print(f"AKINATOR_DP_ELIM_EXHAUSTIVE_SMALL_CNF_CASES = {checked}")
    print("AKINATOR_DP_ELIM_PROJECTION_EQUIVALENCE_FINITE = PASS")
    print("AKINATOR_DP_ELIM_CERTIFICATE_TAMPER_REJECTION = PASS")
    print("AKINATOR_ELIM_CAP_FIRST_FIT_FINITE = PASS")
    print("AKINATOR_ELIM_VARIABLE_COUNT_PROGRESS_FINITE = PASS")
    print("AKINATOR_ELIM_DEGREE_DRIFT_FINITE_ALGEBRA = PASS")
    print("AKINATOR_ELIM_BOUNDARY_3POW_W_FINITE_ALGEBRA = PASS")
    print("DAVIS_PUTNAM_ELIMINATION_THEOREM = ANALYTIC_NOT_CI")
    print("ELIM_CAP_C_UNIVERSAL_AVAILABILITY = OPEN")
    print("MACRO_RESTORE_CAP_UNIVERSAL_AVAILABILITY = OPEN")
    print("POLYNOMIAL_AKINATOR = OPEN")
    print("P_VS_NP = OPEN")


if __name__ == "__main__":
    main()
