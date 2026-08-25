#!/usr/bin/env python3
"""PF5 GT12 successor: exact incidence-component decomposition.

Not an independent holdout. Frozen after the exact dead-intact-gate GC found
zero removable outputs on the post-congruence PF1 residue.

No semantic reasoning is used: components are ordinary variable-clause
incidence components. A single global residual-state budget is shared across
all component handoffs.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

HANDOFF_ENCODING_CAP = 20_000
GLOBAL_STATE_BUDGET = 20_000
COMPONENT_DISCOVERY_WORK_CAP = 500_000


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

    # Exact PF1 residue + already-frozen congruence fixpoint.
    raw, original_variable_count = graph_tautology_cnf(pf1.ORDER)
    cnf = pf1.canonical_cnf(raw)
    history = {}
    for pivot in range(1, original_variable_count + 1):
        if pivot not in pf1.vars_of(cnf):
            continue
        cnf, gates = cg.rewrite_with_gate_history(pf1, cnf, pivot)
        for g in gates:
            history[g.e] = g

    rep = {}
    congruence_merges = 0
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
        rep.update(batch)
        rewritten = []
        for c in cnf:
            nc = []
            for lit in c:
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

    if () in cnf:
        result = {
            'artifact_id': 'PF5-GT12-COMPONENT-DECOMPOSITION-2026-08-25-v1.0',
            'terminal': 'EXACT_UNSAT_EMPTY_CLAUSE',
            'p_vs_np': 'OPEN',
        }
        text = json.dumps(result, indent=2, sort_keys=True) + '\n'
        if args.output:
            args.output.write_text(text, encoding='utf-8')
        print(text, end='')
        return

    # Build exact incidence adjacency.
    var_to_clauses = defaultdict(list)
    discovery_work = 0
    for ci, clause in enumerate(cnf):
        for lit in clause:
            discovery_work += 1
            if discovery_work > COMPONENT_DISCOVERY_WORK_CAP:
                raise RuntimeError('COMPONENT_DISCOVERY_WORK_CAP')
            var_to_clauses[abs(lit)].append(ci)

    unseen_clauses = set(range(len(cnf)))
    components = []
    traversal_visits = 0

    while unseen_clauses:
        seed = min(unseen_clauses)
        q_clauses = deque([seed])
        comp_clause_ids = set()
        comp_vars = set()
        while q_clauses:
            ci = q_clauses.popleft()
            if ci in comp_clause_ids:
                continue
            comp_clause_ids.add(ci)
            unseen_clauses.discard(ci)
            traversal_visits += 1
            for lit in cnf[ci]:
                v = abs(lit)
                if v in comp_vars:
                    continue
                comp_vars.add(v)
                traversal_visits += 1
                for cj in var_to_clauses[v]:
                    discovery_work += 1
                    if discovery_work + traversal_visits > COMPONENT_DISCOVERY_WORK_CAP:
                        raise RuntimeError('COMPONENT_DISCOVERY_WORK_CAP')
                    if cj not in comp_clause_ids:
                        q_clauses.append(cj)
        sub = pf1.canonical_cnf(cnf[i] for i in comp_clause_ids)
        components.append({
            'cnf': sub,
            'clauses': len(sub),
            'literals': sum(map(len, sub)),
            'variables': len(pf1.vars_of(sub)),
            'units': pf1.encoding_units(sub),
            'min_clause_id': min(comp_clause_ids),
        })

    # Sort deterministically largest first, then canonical minimum clause id.
    components.sort(key=lambda x: (-x['units'], x['min_clause_id']))
    total_component_units = sum(c['units'] for c in components)
    max_units = max((c['units'] for c in components), default=0)
    largest_fraction = max_units / pf1.encoding_units(cnf) if cnf else 0.0

    terminal = 'COMPONENTS_WITHIN_INPUT_CAP'
    handoffs = []
    global_states_used = 0
    if max_units > HANDOFF_ENCODING_CAP:
        terminal = 'OPEN_GIANT_COMPONENT_INPUT_CAP'
    else:
        for idx, comp in enumerate(components):
            remaining_budget = GLOBAL_STATE_BUDGET - global_states_used
            if remaining_budget <= 0:
                terminal = 'OPEN_GLOBAL_COMPONENT_STATE_BUDGET'
                break
            ar = compile_residual_automaton(comp['cnf'], pf1.vars_of(comp['cnf']), state_budget=remaining_budget)
            states = ar.stats.residual_states
            global_states_used += states
            handoffs.append({
                'component': idx,
                'status': ar.status,
                'sat': ar.sat,
                'input_units': comp['units'],
                'residual_states': states,
                'bdd_nodes': ar.stats.bdd_nodes,
                'max_frontier_states': ar.stats.max_frontier_states,
                'error': ar.stats.error,
            })
            if ar.status != 'EXACT':
                terminal = 'OPEN_COMPONENT_RESIDUAL_AUTOMATON_CAP'
                break
        else:
            terminal = 'EXACT_COMPONENT_STATE_ONLY'

    result = {
        'artifact_id': 'PF5-GT12-COMPONENT-DECOMPOSITION-2026-08-25-v1.0',
        'experiment_class': 'MECHANISTIC_SUCCESSOR_NOT_INDEPENDENT_HOLDOUT',
        'claim_ceiling': 'FINITE_COMPONENT_STATE_ONLY__FULL_PF1_WITNESS_PROVENANCE_OPEN__P_VS_NP_OPEN',
        'subject': {'family': 'GRAPH_TAUTOLOGY', 'order': pf1.ORDER, 'original_variables': original_variable_count},
        'frozen_caps': {
            'handoff_encoding_cap': HANDOFF_ENCODING_CAP,
            'global_component_state_budget': GLOBAL_STATE_BUDGET,
            'component_discovery_work_cap': COMPONENT_DISCOVERY_WORK_CAP,
            'per_component_fresh_budget_forbidden': True,
            'posthoc_cap_raise_allowed': False,
        },
        'input_state': {
            'units': pf1.encoding_units(cnf),
            'clauses': len(cnf),
            'variables': len(pf1.vars_of(cnf)),
            'congruence_merges': congruence_merges,
        },
        'decomposition': {
            'component_count': len(components),
            'component_discovery_literal_and_adjacency_work': discovery_work,
            'traversal_visits': traversal_visits,
            'total_discovery_work': discovery_work + traversal_visits,
            'total_component_units_sum': total_component_units,
            'largest_component_units': max_units,
            'largest_component_fraction_of_global_units': largest_fraction,
            'components': [
                {k: v for k, v in c.items() if k != 'cnf'}
                for c in components[:50]
            ],
            'component_list_truncated_after': 50 if len(components) > 50 else None,
        },
        'handoffs': handoffs,
        'global_states_used': global_states_used,
        'terminal': terminal,
        'scientific_boundary': [
            'Incidence components are exact variable-disjoint conjunction factors.',
            'All components share one global residual-state budget; the cap is not multiplied by component count.',
            'This is not an independent holdout.',
            'EXACT_COMPONENT_STATE_ONLY would still not close the PF1 end-to-end original-root witness/provenance obligation.',
            'Finite GT12 component structure is not an asymptotic theorem.'
        ],
        'p_vs_np': 'OPEN',
    }

    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
