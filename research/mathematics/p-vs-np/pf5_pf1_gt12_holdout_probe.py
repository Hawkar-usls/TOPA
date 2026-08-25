#!/usr/bin/env python3
"""PF5 finite holdout: repeated PF1 B2 factor rewrites on frozen GT12.

This is a capability experiment, not an asymptotic theorem.  The subject and
caps are frozen in the source before execution.  Each accepted rewrite is an
exact equisatisfiable one-pivot projection encoded only with B2 AND definitions
and signed literals.

The probe charges all emitted clauses/literals/gates.  If the cap is exceeded,
it returns OPEN_CAP and stops.  No post-hoc cap raise is allowed.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Union

Clause = tuple[int, ...]
CNF = tuple[Clause, ...]
Ref = Union[int, str]  # signed variable literal or constants 'T'/'F'

ORDER = 12
ENCODING_CAP = 200_000
STATE_BUDGET = 20_000
ORIGINAL_ROOT_POLICY = "MIN_ORIGINAL_VARIABLE_ID"


def canonical_clause(raw: Iterable[int]) -> Clause | None:
    s = set(int(x) for x in raw)
    if any(-lit in s for lit in s):
        return None
    return tuple(sorted(s, key=lambda lit: (abs(lit), lit < 0)))


def canonical_cnf(raw: Iterable[Iterable[int]]) -> CNF:
    out = set()
    for clause in raw:
        c = canonical_clause(clause)
        if c is not None:
            out.add(c)
    return tuple(sorted(out, key=lambda c: (len(c), c)))


def vars_of(cnf: CNF) -> list[int]:
    return sorted({abs(l) for c in cnf for l in c})


def encoding_units(cnf: CNF) -> int:
    return len(vars_of(cnf)) + len(cnf) + sum(len(c) for c in cnf)


def eval_cnf(cnf: CNF, a: dict[int, bool]) -> bool:
    return all(any(a[abs(l)] == (l > 0) for l in c) for c in cnf)


def brute_sat(cnf: CNF) -> bool:
    vs = vars_of(cnf)
    for bits in itertools.product((False, True), repeat=len(vs)):
        if eval_cnf(cnf, dict(zip(vs, bits))):
            return True
    return False


def neg_ref(r: Ref) -> Ref:
    if r == 'T':
        return 'F'
    if r == 'F':
        return 'T'
    assert isinstance(r, int)
    return -r


@dataclass
class Gate:
    e: int
    a: int
    b: int


class Builder:
    def __init__(self, start_var: int):
        self.next_var = start_var
        self.gates: list[Gate] = []
        self.clauses: list[Clause] = []

    def fresh(self) -> int:
        e = self.next_var
        self.next_var += 1
        return e

    def AND(self, a: Ref, b: Ref) -> Ref:
        if a == 'F' or b == 'F':
            return 'F'
        if a == 'T':
            return b
        if b == 'T':
            return a
        assert isinstance(a, int) and isinstance(b, int)
        if a == b:
            return a
        if a == -b:
            return 'F'
        e = self.fresh()
        # e <-> (a AND b), valid for signed literals a,b.
        defs = [(-e, a), (-e, b), (e, -a, -b)]
        self.clauses.extend(canonical_cnf(defs))
        self.gates.append(Gate(e, a, b))
        return e

    def conjunction(self, refs: list[Ref]) -> Ref:
        if not refs:
            return 'T'
        work = list(refs)
        while len(work) > 1:
            nxt: list[Ref] = []
            it = iter(work)
            for a in it:
                try:
                    b = next(it)
                except StopIteration:
                    nxt.append(a)
                    break
                nxt.append(self.AND(a, b))
            work = nxt
        return work[0]

    def clause_ref(self, clause: Clause) -> Ref:
        # OR(l_1,...,l_k) = NOT(AND(NOT l_1,...,NOT l_k)).
        if not clause:
            return 'F'
        if len(clause) == 1:
            return clause[0]
        t = self.conjunction([-lit for lit in clause])
        return neg_ref(t)


@dataclass
class Step:
    pivot: int
    p_count: int
    n_count: int
    pair_attempts_avoided: int
    explicit_distinct_resolvents: int
    input_clauses: int
    input_literals: int
    input_units: int
    gates_added: int
    output_clauses: int
    output_literals: int
    output_units: int


def explicit_frontier(cnf: CNF, pivot: int) -> set[Clause]:
    pos = [tuple(l for l in c if l != pivot) for c in cnf if pivot in c]
    neg = [tuple(l for l in c if l != -pivot) for c in cnf if -pivot in c]
    out: set[Clause] = set()
    for a in pos:
        for b in neg:
            c = canonical_clause((*a, *b))
            if c is not None:
                out.add(c)
    return out


def rewrite_pf1(cnf: CNF, pivot: int) -> tuple[CNF, Step]:
    max_var = max(vars_of(cnf), default=0)
    builder = Builder(max_var + 1)

    pos: list[Clause] = []
    neg: list[Clause] = []
    rest: list[Clause] = []
    for c in cnf:
        if pivot in c:
            pos.append(tuple(l for l in c if l != pivot))
        elif -pivot in c:
            neg.append(tuple(l for l in c if l != -pivot))
        else:
            rest.append(c)

    if not pos and not neg:
        step = Step(
            pivot=pivot, p_count=0, n_count=0,
            pair_attempts_avoided=0, explicit_distinct_resolvents=0,
            input_clauses=len(cnf), input_literals=sum(map(len, cnf)), input_units=encoding_units(cnf),
            gates_added=0, output_clauses=len(cnf), output_literals=sum(map(len, cnf)), output_units=encoding_units(cnf),
        )
        return cnf, step

    p_refs = [builder.clause_ref(c) for c in pos]
    n_refs = [builder.clause_ref(c) for c in neg]
    p_all = builder.conjunction(p_refs)
    n_all = builder.conjunction(n_refs)

    final: list[Clause] = list(rest) + list(builder.clauses)
    if p_all == 'T' or n_all == 'T':
        pass
    elif p_all == 'F' and n_all == 'F':
        final.append(())
    elif p_all == 'F':
        assert isinstance(n_all, int)
        final.append((n_all,))
    elif n_all == 'F':
        assert isinstance(p_all, int)
        final.append((p_all,))
    else:
        assert isinstance(p_all, int) and isinstance(n_all, int)
        c = canonical_clause((p_all, n_all))
        if c is not None:
            final.append(c)

    out = canonical_cnf(final)
    frontier = explicit_frontier(cnf, pivot)
    step = Step(
        pivot=pivot,
        p_count=len(pos),
        n_count=len(neg),
        pair_attempts_avoided=len(pos) * len(neg),
        explicit_distinct_resolvents=len(frontier),
        input_clauses=len(cnf),
        input_literals=sum(map(len, cnf)),
        input_units=encoding_units(cnf),
        gates_added=len(builder.gates),
        output_clauses=len(out),
        output_literals=sum(map(len, out)),
        output_units=encoding_units(out),
    )
    assert pivot not in vars_of(out)
    return out, step


def selftest() -> None:
    fixtures = [
        canonical_cnf(((1,2),(-1,3),(2,-3))),
        canonical_cnf(((1,),(-1,2),(-1,-2))),
        canonical_cnf(((1,2),(1,-2),(-1,3),(-1,-3))),
    ]
    for f in fixtures:
        before = brute_sat(f)
        g, _ = rewrite_pf1(f, 1)
        after = brute_sat(g)
        assert before == after, (f, g, before, after)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--fundamentum-root', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()

    selftest()

    direct = args.fundamentum_root / 'experiments' / 'direct'
    sys.path.insert(0, str(direct))
    from janus_tear_policy0a_graph_tautology_probe import graph_tautology_cnf
    from janus_c025_core import compile_residual_automaton

    cnf, original_variable_count = graph_tautology_cnf(ORDER)
    cnf = canonical_cnf(cnf)
    original_input_units = encoding_units(cnf)
    original_roots = list(range(1, original_variable_count + 1))

    steps: list[Step] = []
    cumulative_gates = 0
    cumulative_pair_attempts_avoided = 0
    peak_units = original_input_units
    terminal = 'ROOT_ELIMINATION_COMPLETE'

    for pivot in original_roots:
        if pivot not in vars_of(cnf):
            continue
        cnf, step = rewrite_pf1(cnf, pivot)
        steps.append(step)
        cumulative_gates += step.gates_added
        cumulative_pair_attempts_avoided += step.pair_attempts_avoided
        peak_units = max(peak_units, step.output_units)
        if step.output_units > ENCODING_CAP:
            terminal = 'OPEN_ENCODING_CAP'
            break

    automaton = None
    if terminal == 'ROOT_ELIMINATION_COMPLETE':
        remaining = vars_of(cnf)
        # Exact fail-closed handoff to the historical residual automaton.
        result = compile_residual_automaton(cnf, remaining, state_budget=STATE_BUDGET)
        automaton = {
            'status': result.status,
            'sat': result.sat,
            'witness_valid': result.witness is not None and eval_cnf(cnf, result.witness) if result.witness is not None else False,
            'residual_states': result.stats.residual_states,
            'bdd_nodes': result.stats.bdd_nodes,
            'max_frontier_states': result.stats.max_frontier_states,
            'subsumption_steps': result.stats.subsumption_steps,
            'error': result.stats.error,
        }
        terminal = 'EXACT' if result.status == 'EXACT' else 'OPEN_RESIDUAL_AUTOMATON_CAP'

    result = {
        'artifact_id': 'PF5-PF1-GT12-FROZEN-HOLDOUT-2026-08-25-v1.0',
        'claim_ceiling': 'FINITE_CAPABILITY_ONLY__P_VS_NP_OPEN',
        'subject': {
            'family': 'GRAPH_TAUTOLOGY',
            'order': ORDER,
            'original_variables': original_variable_count,
            'original_clauses': 452,
            'original_input_units': original_input_units,
            'historical_state_cap': STATE_BUDGET,
        },
        'frozen_policy': {
            'root_order': ORIGINAL_ROOT_POLICY,
            'encoding_cap': ENCODING_CAP,
            'residual_automaton_state_budget': STATE_BUDGET,
            'posthoc_cap_raise_allowed': False,
            'pf1_gate_basis': 'B2_AND_SIGNED_LITERALS_ONLY',
        },
        'terminal': terminal,
        'roots_processed': len(steps),
        'remaining_variables': len(vars_of(cnf)),
        'final_clauses': len(cnf),
        'final_literals': sum(map(len, cnf)),
        'final_units': encoding_units(cnf),
        'peak_units': peak_units,
        'cumulative_b2_gates_added': cumulative_gates,
        'cumulative_pair_attempts_avoided_proxy': cumulative_pair_attempts_avoided,
        'automaton_handoff': automaton,
        'steps': [asdict(s) for s in steps],
        'scientific_boundary': [
            'PF1 exactness is analytic; this run is finite mechanics/capability only.',
            'Avoided pair attempts are a representation comparison, not saved universal runtime.',
            'A finite GT12 success would not prove P=NP.',
            'A finite cap failure would not prove P!=NP.'
        ],
        'p_vs_np': 'OPEN',
    }

    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
