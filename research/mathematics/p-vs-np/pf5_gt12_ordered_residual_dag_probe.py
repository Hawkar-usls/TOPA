#!/usr/bin/env python3
"""PF5 GT12 successor: frozen-order exact residual-CNF DAG.

This is an exact ordered residual quotient using only cofactoring and canonical
CNF byte equality. It is intentionally weaker than semantic ROBDD reduction:
no subsumption, SAT equivalence, model counting, or order search is used.

Not an independent holdout. Frozen after the canonical clause-trace DP lane hit
its state cap.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

STATE_CAP = 20_000
LITERAL_WORK_CAP = 1_000_000


def build_state(topa_root: Path, fundamentum_root: Path):
    pnp = topa_root / 'research' / 'mathematics' / 'p-vs-np'
    direct = fundamentum_root / 'experiments' / 'direct'
    sys.path.insert(0, str(pnp))
    sys.path.insert(0, str(direct))

    import pf5_pf1_gt12_holdout_probe as pf1
    import pf5_gt12_intact_gate_congruence_probe as cg
    from janus_tear_policy0a_graph_tautology_probe import graph_tautology_cnf

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
    merges = 0
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
        merges += len(batch)

    assert merges == 175
    assert pf1.encoding_units(cnf) == 37821
    assert len(pf1.vars_of(cnf)) == 4193
    return pf1, cnf, original_variable_count


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--topa-root', type=Path, required=True)
    ap.add_argument('--fundamentum-root', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()

    pf1, root, original_variable_count = build_state(args.topa_root, args.fundamentum_root)
    order = pf1.vars_of(root)

    literal_work = 0
    cumulative_unique_states = 1
    max_frontier = 1
    max_frontier_level = 0
    frontier = {root}
    terminal = 'EXACT_COMPLETE'
    trigger = None
    levels = []

    def cofactor(cnf, var: int, value: bool):
        nonlocal literal_work, terminal, trigger
        out = []
        sat_lit = var if value else -var
        false_lit = -sat_lit
        for clause in cnf:
            literal_work += len(clause)
            if literal_work > LITERAL_WORK_CAP:
                return None
            if sat_lit in clause:
                continue
            if false_lit in clause:
                nc = tuple(l for l in clause if l != false_lit)
                if not nc:
                    return ((),)
                out.append(nc)
            else:
                out.append(clause)
        return pf1.canonical_cnf(out)

    for level, var in enumerate(order, start=1):
        next_frontier = set()
        processed = 0
        for cnf in frontier:
            # If this variable is absent in this residual, no binary birth occurs.
            present = any(var in c or -var in c for c in cnf)
            if not present:
                next_frontier.add(cnf)
                continue
            for value in (False, True):
                child = cofactor(cnf, var, value)
                processed += 1
                if child is None:
                    terminal = 'OPEN_LITERAL_WORK_CAP'
                    trigger = {
                        'level': level,
                        'var': var,
                        'frontier_before': len(frontier),
                        'children_processed_this_level': processed,
                        'literal_work': literal_work,
                    }
                    break
                if child == ((),):
                    # UNSAT child; it does not need to remain as a live continuation.
                    continue
                if child == ():
                    terminal = 'EXACT_SAT_CURRENT_STATE'
                    trigger = {
                        'level': level,
                        'var': var,
                        'frontier_before': len(frontier),
                        'literal_work': literal_work,
                    }
                    next_frontier = {()}
                    break
                next_frontier.add(child)
            if terminal != 'EXACT_COMPLETE':
                break
        if terminal != 'EXACT_COMPLETE':
            break

        cumulative_unique_states += len(next_frontier)
        if len(next_frontier) > STATE_CAP or cumulative_unique_states > STATE_CAP:
            terminal = 'OPEN_RESIDUAL_STATE_CAP'
            trigger = {
                'level': level,
                'var': var,
                'frontier_before': len(frontier),
                'frontier_after': len(next_frontier),
                'cumulative_state_insertions_proxy': cumulative_unique_states,
                'literal_work': literal_work,
            }
            break

        frontier = next_frontier
        if len(frontier) > max_frontier:
            max_frontier = len(frontier)
            max_frontier_level = level
        if level <= 16 or len(frontier) >= STATE_CAP // 4:
            levels.append({
                'level': level,
                'var': var,
                'frontier': len(frontier),
                'cumulative_state_insertions_proxy': cumulative_unique_states,
                'literal_work': literal_work,
            })
        if not frontier:
            terminal = 'EXACT_UNSAT_CURRENT_STATE'
            trigger = {'level': level, 'var': var, 'literal_work': literal_work}
            break

    if terminal == 'EXACT_COMPLETE':
        terminal = 'EXACT_SAT_CURRENT_STATE' if frontier else 'EXACT_UNSAT_CURRENT_STATE'

    result = {
        'artifact_id': 'PF5-GT12-FROZEN-ORDER-RESIDUAL-DAG-2026-08-25-v1.0',
        'experiment_class': 'MECHANISTIC_SUCCESSOR_NOT_INDEPENDENT_HOLDOUT',
        'claim_ceiling': 'FINITE_CURRENT_STATE_QUOTIENT_ONLY__PF1_END_TO_END_WITNESS_PROVENANCE_OPEN__P_VS_NP_OPEN',
        'subject': {'family': 'GRAPH_TAUTOLOGY', 'order': pf1.ORDER, 'original_variables': original_variable_count},
        'frozen_policy': {
            'variable_order': 'ASCENDING_CURRENT_VARIABLE_ID_NO_SEARCH',
            'residual_equality': 'EXACT_CANONICAL_CNF_BYTES_ONLY',
            'subsumption': False,
            'semantic_equivalence': False,
            'state_cap': STATE_CAP,
            'literal_work_cap': LITERAL_WORK_CAP,
            'posthoc_order_change_allowed': False,
            'posthoc_cap_raise_allowed': False,
        },
        'input_state': {
            'units': pf1.encoding_units(root),
            'clauses': len(root),
            'variables': len(order),
        },
        'run': {
            'terminal': terminal,
            'literal_work': literal_work,
            'max_frontier': max_frontier,
            'max_frontier_level': max_frontier_level,
            'cumulative_state_insertions_proxy': cumulative_unique_states,
            'trigger': trigger,
            'selected_levels': levels[:100],
        },
        'scientific_boundary': [
            'Canonical residual CNF byte equality is a sufficient exact merge, not complete semantic ROBDD reduction.',
            'The variable order is frozen and not optimized.',
            'A cap hit closes only this exact frozen-order residual-DAG lane on this finite state.',
            'A finite exact SAT/UNSAT current-state result would not discharge full PF1 original-root witness provenance.',
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
