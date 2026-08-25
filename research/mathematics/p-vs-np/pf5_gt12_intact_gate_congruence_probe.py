#!/usr/bin/env python3
"""PF5 GT12 mechanistic successor: exact intact B2 gate congruence reuse.

This experiment is not an independent holdout. It follows the observed fact
that certified syntactic subsumption leaves the PF1 GT12 residue unchanged.

Only historical PF1 gates whose complete current B2 definition triple is still
present are eligible. Duplicate intact definitions with identical signed inputs
are merged by exact syntactic substitution. Stale/projection-damaged gate
provenance has zero authority.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Union

Ref = Union[int, str]

WORK_CAP = 1_000_000
HANDOFF_ENCODING_CAP = 20_000
STATE_BUDGET = 20_000


def map_lit(lit: int, rep: dict[int, int]) -> int:
    sign = 1 if lit > 0 else -1
    v = abs(lit)
    while v in rep and rep[v] != v:
        v = rep[v]
    return sign * v


def canon_key(a: int, b: int) -> tuple[int, int]:
    return tuple(sorted((a, b), key=lambda z: (abs(z), z < 0)))


@dataclass
class GateRec:
    e: int
    a: int
    b: int


def rewrite_with_gate_history(pf1, cnf, pivot: int):
    """Byte-identical PF1 rewrite plus emitted historical gate records."""
    max_var = max(pf1.vars_of(cnf), default=0)
    builder = pf1.Builder(max_var + 1)
    pos = []
    neg = []
    rest = []
    for c in cnf:
        if pivot in c:
            pos.append(tuple(l for l in c if l != pivot))
        elif -pivot in c:
            neg.append(tuple(l for l in c if l != -pivot))
        else:
            rest.append(c)

    if not pos and not neg:
        return cnf, []

    p_refs = [builder.clause_ref(c) for c in pos]
    n_refs = [builder.clause_ref(c) for c in neg]
    p_all = builder.conjunction(p_refs)
    n_all = builder.conjunction(n_refs)

    final = list(rest) + list(builder.clauses)
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
        c = pf1.canonical_clause((p_all, n_all))
        if c is not None:
            final.append(c)

    out = pf1.canonical_cnf(final)
    gates = [GateRec(g.e, g.a, g.b) for g in builder.gates]

    # Guard against implementation drift: compare with the already-frozen PF1.
    frozen_out, _ = pf1.rewrite_pf1(cnf, pivot)
    assert out == frozen_out
    return out, gates


def expected_def_clauses(pf1, e: int, a: int, b: int):
    return set(pf1.canonical_cnf(((-e, a), (-e, b), (e, -a, -b))))


def apply_batch_substitution(pf1, cnf, merges: dict[int, int], work: dict[str, int]):
    def resolve(v: int) -> int:
        while v in merges:
            nv = merges[v]
            if nv == v:
                break
            v = nv
        return v

    rewritten = []
    for c in cnf:
        nc = []
        for lit in c:
            work['literal_substitution_visits'] += 1
            if work['total'] + work['literal_substitution_visits'] > WORK_CAP:
                raise RuntimeError('WORK_CAP')
            sign = 1 if lit > 0 else -1
            v = resolve(abs(lit))
            nc.append(sign * v)
        rewritten.append(nc)
    return pf1.canonical_cnf(rewritten)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--topa-root', type=Path, required=True)
    ap.add_argument('--fundamentum-root', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()

    pnp = args.topa_root / 'research' / 'mathematics' / 'p-vs-np'
    direct = args.fundamentum_root / 'experiments' / 'direct'
    sys.path.insert(0, str(pnp))
    sys.path.insert(0, str(direct))

    import pf5_pf1_gt12_holdout_probe as pf1
    from janus_tear_policy0a_graph_tautology_probe import graph_tautology_cnf
    from janus_c025_core import compile_residual_automaton

    raw, original_variable_count = graph_tautology_cnf(pf1.ORDER)
    cnf = pf1.canonical_cnf(raw)
    gate_history: dict[int, GateRec] = {}

    for pivot in range(1, original_variable_count + 1):
        if pivot not in pf1.vars_of(cnf):
            continue
        cnf, gates = rewrite_with_gate_history(pf1, cnf, pivot)
        for g in gates:
            assert g.e not in gate_history
            gate_history[g.e] = g
        assert pf1.encoding_units(cnf) <= pf1.ENCODING_CAP

    before_units = pf1.encoding_units(cnf)
    before_clauses = len(cnf)
    before_vars = len(pf1.vars_of(cnf))
    assert before_units == 39746
    assert before_vars == 4368

    rep: dict[int, int] = {}
    work = {
        'definition_clause_membership_checks': 0,
        'key_insertions': 0,
        'literal_substitution_visits': 0,
        'passes': 0,
        'total': 0,
    }
    total_merges = 0
    pass_receipts = []
    terminal = 'CONGRUENCE_FIXPOINT'

    while True:
        work['passes'] += 1
        clause_set = set(cnf)
        groups = defaultdict(list)
        intact = 0

        for e, g in sorted(gate_history.items()):
            if e in rep:
                continue
            a = map_lit(g.a, rep)
            b = map_lit(g.b, rep)
            defs = expected_def_clauses(pf1, e, a, b)
            ok = True
            for dc in defs:
                work['definition_clause_membership_checks'] += 1
                if dc not in clause_set:
                    ok = False
                    break
            if not ok:
                continue
            intact += 1
            key = canon_key(a, b)
            groups[key].append(e)
            work['key_insertions'] += 1

        total_now = (
            work['definition_clause_membership_checks']
            + work['key_insertions']
            + work['literal_substitution_visits']
        )
        work['total'] = total_now
        if total_now > WORK_CAP:
            terminal = 'OPEN_GATE_REUSE_WORK_CAP'
            break

        batch: dict[int, int] = {}
        duplicate_groups = 0
        for key, outs in groups.items():
            if len(outs) <= 1:
                continue
            duplicate_groups += 1
            r = min(outs)
            for d in outs:
                if d != r:
                    batch[d] = r

        pass_receipts.append({
            'pass': work['passes'],
            'intact_definitions': intact,
            'unique_structural_keys': len(groups),
            'duplicate_groups': duplicate_groups,
            'merges_proposed': len(batch),
            'units_before': pf1.encoding_units(cnf),
        })

        if not batch:
            break

        # Merge maps are acyclic because duplicate outputs share earlier inputs.
        for d, r in batch.items():
            rep[d] = r
        try:
            cnf = apply_batch_substitution(pf1, cnf, batch, work)
        except RuntimeError:
            terminal = 'OPEN_GATE_REUSE_WORK_CAP'
            break
        total_merges += len(batch)
        pass_receipts[-1]['units_after'] = pf1.encoding_units(cnf)

    after_units = pf1.encoding_units(cnf)
    after_clauses = len(cnf)
    after_vars = len(pf1.vars_of(cnf))
    work['total'] = (
        work['definition_clause_membership_checks']
        + work['key_insertions']
        + work['literal_substitution_visits']
    )

    automaton = None
    if terminal == 'CONGRUENCE_FIXPOINT':
        if after_units > HANDOFF_ENCODING_CAP:
            terminal = 'OPEN_HANDOFF_INPUT_CAP_AFTER_GATE_CONGRUENCE'
        else:
            remaining = pf1.vars_of(cnf)
            ar = compile_residual_automaton(cnf, remaining, state_budget=STATE_BUDGET)
            automaton = {
                'status': ar.status,
                'sat': ar.sat,
                'residual_states': ar.stats.residual_states,
                'bdd_nodes': ar.stats.bdd_nodes,
                'max_frontier_states': ar.stats.max_frontier_states,
                'error': ar.stats.error,
            }
            terminal = 'EXACT_STATE_ONLY' if ar.status == 'EXACT' else 'OPEN_RESIDUAL_AUTOMATON_CAP'

    result = {
        'artifact_id': 'PF5-GT12-INTACT-GATE-CONGRUENCE-2026-08-25-v1.0',
        'experiment_class': 'MECHANISTIC_SUCCESSOR_NOT_INDEPENDENT_HOLDOUT',
        'claim_ceiling': 'FINITE_STATE_COMPRESSION_ONLY__FULL_WITNESS_PROVENANCE_NOT_YET_REPLAYED__P_VS_NP_OPEN',
        'subject': {'family': 'GRAPH_TAUTOLOGY', 'order': pf1.ORDER, 'original_variables': original_variable_count},
        'frozen_caps': {
            'gate_reuse_work_cap': WORK_CAP,
            'handoff_encoding_cap': HANDOFF_ENCODING_CAP,
            'residual_automaton_state_budget': STATE_BUDGET,
            'posthoc_cap_raise_allowed': False,
        },
        'before': {'units': before_units, 'clauses': before_clauses, 'variables': before_vars, 'historical_gates': len(gate_history)},
        'after': {'units': after_units, 'clauses': after_clauses, 'variables': after_vars},
        'congruence': {
            'successful_merges': total_merges,
            'work': work,
            'passes': pass_receipts,
        },
        'automaton_handoff': automaton,
        'terminal': terminal,
        'scientific_boundary': [
            'Only currently intact historical B2 definition triples authorize reuse.',
            'No semantic equivalence is queried.',
            'This is a mechanistic successor, not an independent holdout.',
            'An EXACT_STATE_ONLY handoff would still not be a full SAT-solver receipt until PF1 reverse witness/proof provenance is replayed end to end.',
            'Finite GT12 behavior is not an asymptotic theorem.'
        ],
        'p_vs_np': 'OPEN',
    }

    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
