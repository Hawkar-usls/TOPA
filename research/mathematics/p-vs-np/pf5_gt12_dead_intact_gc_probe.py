#!/usr/bin/env python3
"""PF5 GT12 mechanistic successor: congruence -> dead intact B2 gate GC.

Not an independent holdout. Frozen after the gate-congruence receipt showed the
PF1 residue still exceeded the unchanged 20,000-unit handoff cap.

Logical authority:
- duplicate intact gate merge: exact structural congruence only;
- dead gate deletion: output occurs only in its complete current definition;
- no semantic equivalence or SAT oracle.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

GC_WORK_CAP = 1_000_000
HANDOFF_ENCODING_CAP = 20_000
STATE_BUDGET = 20_000


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
    import pf5_gt12_intact_gate_congruence_probe as cg
    from janus_tear_policy0a_graph_tautology_probe import graph_tautology_cnf
    from janus_c025_core import compile_residual_automaton

    raw, original_variable_count = graph_tautology_cnf(pf1.ORDER)
    cnf = pf1.canonical_cnf(raw)
    history = {}

    # Rebuild exact PF1 residue and historical gate recipes.
    for pivot in range(1, original_variable_count + 1):
        if pivot not in pf1.vars_of(cnf):
            continue
        cnf, gates = cg.rewrite_with_gate_history(pf1, cnf, pivot)
        for g in gates:
            history[g.e] = g
        assert pf1.encoding_units(cnf) <= pf1.ENCODING_CAP

    assert pf1.encoding_units(cnf) == 39746
    assert len(pf1.vars_of(cnf)) == 4368

    # Exact intact-gate congruence to the already-observed fixpoint.
    rep = {}
    congruence_merges = 0
    congruence_literal_visits = 0
    while True:
        clause_set = set(cnf)
        groups = defaultdict(list)
        for e, g in sorted(history.items()):
            if e in rep:
                continue
            a = cg.map_lit(g.a, rep)
            b = cg.map_lit(g.b, rep)
            defs = cg.expected_def_clauses(pf1, e, a, b)
            if all(dc in clause_set for dc in defs):
                groups[cg.canon_key(a, b)].append(e)
        batch = {}
        for outs in groups.values():
            if len(outs) > 1:
                r = min(outs)
                for d in outs:
                    if d != r:
                        batch[d] = r
        if not batch:
            break
        for d, r in batch.items():
            rep[d] = r
        rewritten = []
        for c in cnf:
            nc = []
            for lit in c:
                congruence_literal_visits += 1
                sign = 1 if lit > 0 else -1
                v = abs(lit)
                while v in batch:
                    v = batch[v]
                nc.append(sign * v)
            rewritten.append(nc)
        cnf = pf1.canonical_cnf(rewritten)
        congruence_merges += len(batch)

    assert congruence_merges == 175
    assert pf1.encoding_units(cnf) == 37821
    assert len(pf1.vars_of(cnf)) == 4193

    gc_start = {
        'units': pf1.encoding_units(cnf),
        'clauses': len(cnf),
        'variables': len(pf1.vars_of(cnf)),
    }

    pruned = set()
    provenance = []
    passes = []
    work = {
        'occurrence_literal_visits': 0,
        'definition_membership_checks': 0,
        'deleted_clause_records': 0,
        'passes': 0,
    }
    terminal = 'GC_FIXPOINT'

    while True:
        work['passes'] += 1
        clause_set = set(cnf)
        occ = defaultdict(set)
        for c in cnf:
            for lit in c:
                work['occurrence_literal_visits'] += 1
                occ[abs(lit)].add(c)
        total_work = sum(v for k, v in work.items() if k != 'passes')
        if total_work > GC_WORK_CAP:
            terminal = 'OPEN_DEAD_GC_WORK_CAP'
            break

        intact = {}
        for e, g in sorted(history.items()):
            if e in rep or e in pruned:
                continue
            a = cg.map_lit(g.a, rep)
            b = cg.map_lit(g.b, rep)
            defs = cg.expected_def_clauses(pf1, e, a, b)
            ok = True
            for dc in defs:
                work['definition_membership_checks'] += 1
                if dc not in clause_set:
                    ok = False
                    break
            if ok:
                intact[e] = (a, b, defs)

        dead = []
        for e, (a, b, defs) in intact.items():
            if occ.get(e, set()) == defs:
                dead.append((e, a, b, defs))

        passes.append({
            'pass': work['passes'],
            'units_before': pf1.encoding_units(cnf),
            'intact_definitions': len(intact),
            'dead_outputs_found': len(dead),
        })

        total_work = sum(v for k, v in work.items() if k != 'passes')
        if total_work > GC_WORK_CAP:
            terminal = 'OPEN_DEAD_GC_WORK_CAP'
            break
        if not dead:
            break

        delete_clauses = set()
        for e, a, b, defs in dead:
            delete_clauses.update(defs)
            provenance.append((e, a, b))
            pruned.add(e)
        work['deleted_clause_records'] += len(delete_clauses)
        cnf = pf1.canonical_cnf(c for c in cnf if c not in delete_clauses)
        passes[-1]['units_after'] = pf1.encoding_units(cnf)

    total_work = sum(v for k, v in work.items() if k != 'passes')
    after_units = pf1.encoding_units(cnf)
    after_vars_list = pf1.vars_of(cnf)
    extension_vars = [v for v in after_vars_list if v > original_variable_count]

    # Classify current intact vs non-intact extension outputs at fixpoint.
    clause_set = set(cnf)
    surviving_intact = 0
    for e, g in history.items():
        if e in rep or e in pruned or e not in extension_vars:
            continue
        a = cg.map_lit(g.a, rep)
        b = cg.map_lit(g.b, rep)
        defs = cg.expected_def_clauses(pf1, e, a, b)
        if all(dc in clause_set for dc in defs):
            surviving_intact += 1
    nonintact_or_other = len(extension_vars) - surviving_intact

    automaton = None
    if terminal == 'GC_FIXPOINT':
        if after_units > HANDOFF_ENCODING_CAP:
            terminal = 'OPEN_HANDOFF_INPUT_CAP_AFTER_DEAD_GC'
        else:
            ar = compile_residual_automaton(cnf, after_vars_list, state_budget=STATE_BUDGET)
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
        'artifact_id': 'PF5-GT12-DEAD-INTACT-GATE-GC-2026-08-25-v1.0',
        'experiment_class': 'MECHANISTIC_SUCCESSOR_NOT_INDEPENDENT_HOLDOUT',
        'claim_ceiling': 'FINITE_STATE_COMPRESSION_ONLY__Q_WITNESS_PROVENANCE_SEPARATELY_CHARGED__P_VS_NP_OPEN',
        'subject': {'family': 'GRAPH_TAUTOLOGY', 'order': pf1.ORDER, 'original_variables': original_variable_count},
        'frozen_caps': {
            'gc_work_cap': GC_WORK_CAP,
            'handoff_encoding_cap': HANDOFF_ENCODING_CAP,
            'residual_automaton_state_budget': STATE_BUDGET,
            'posthoc_cap_raise_allowed': False,
        },
        'congruence_prefix': {
            'merges': congruence_merges,
            'literal_substitution_visits': congruence_literal_visits,
            'start_units': 39746,
            'fixpoint_units': gc_start['units'],
        },
        'gc': {
            'start': gc_start,
            'passes': passes,
            'pruned_outputs': len(pruned),
            'provenance_records': len(provenance),
            'provenance_integer_fields': 3 * len(provenance),
            'work': work,
            'work_total': total_work,
        },
        'after': {
            'units': after_units,
            'clauses': len(cnf),
            'variables': len(after_vars_list),
            'extension_variables': len(extension_vars),
            'surviving_intact_definitions': surviving_intact,
            'nonintact_or_other_extension_variables': nonintact_or_other,
        },
        'automaton_handoff': automaton,
        'terminal': terminal,
        'scientific_boundary': [
            'Deadness is established only from current exact clause occurrences and intact definition triples.',
            'Deleted gate recipes are charged as Q_witness provenance, but end-to-end PF1 original-root witness reconstruction is not yet replayed.',
            'This successor is not an independent holdout.',
            'Finite GT12 compression is not an asymptotic theorem.'
        ],
        'p_vs_np': 'OPEN',
    }

    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
