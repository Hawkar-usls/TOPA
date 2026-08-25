#!/usr/bin/env python3
"""PF5 GT12 successor: exact canonical clause-trace boundary DP.

Not an independent holdout. Frozen after exact component decomposition found one
giant component. No order search: use the existing canonical CNF clause order.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

STATE_CAP = 20_000
TRANSITION_WORK_CAP = 1_000_000


def build_post_congruence_state(topa_root: Path, fundamentum_root: Path):
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
    return pf1, cnf, original_variable_count, merges


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--topa-root', type=Path, required=True)
    ap.add_argument('--fundamentum-root', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()

    pf1, cnf, original_variable_count, merges = build_post_congruence_state(
        args.topa_root, args.fundamentum_root
    )

    if () in cnf:
        result = {
            'artifact_id': 'PF5-GT12-CLAUSE-TRACE-DP-2026-08-25-v1.0',
            'terminal': 'EXACT_UNSAT_EMPTY_CLAUSE',
            'p_vs_np': 'OPEN',
        }
        text = json.dumps(result, indent=2, sort_keys=True) + '\n'
        if args.output:
            args.output.write_text(text, encoding='utf-8')
        print(text, end='')
        return

    first = {}
    last = {}
    for t, clause in enumerate(cnf):
        for lit in clause:
            v = abs(lit)
            first.setdefault(v, t)
            last[v] = t

    introduced_at = defaultdict(list)
    forgotten_at = defaultdict(list)
    for v in first:
        introduced_at[first[v]].append(v)
        forgotten_at[last[v]].append(v)
    for xs in introduced_at.values():
        xs.sort()
    for xs in forgotten_at.values():
        xs.sort()

    # Exact width of this frozen interval decomposition.
    delta = [0] * (len(cnf) + 1)
    for v in first:
        delta[first[v]] += 1
        if last[v] + 1 < len(delta):
            delta[last[v] + 1] -= 1
    live = 0
    max_live = 0
    max_live_clause = None
    for t in range(len(cnf)):
        live += delta[t]
        if live > max_live:
            max_live = live
            max_live_clause = t
    lambda_clause = max_live - 1 if max_live else 0

    # State is a tuple of bits in sorted boundary_vars order after each clause.
    boundary_vars: tuple[int, ...] = ()
    states = {()}
    transition_work = 0
    max_states = 1
    max_states_clause = None
    steps = []
    terminal = 'EXACT_COMPLETE'
    trigger = None

    for t, clause in enumerate(cnf):
        new_vars = tuple(v for v in introduced_at.get(t, []) if v not in boundary_vars)
        full_vars = tuple(sorted((*boundary_vars, *new_vars)))
        pos = {v: i for i, v in enumerate(full_vars)}
        prev_pos = {v: i for i, v in enumerate(boundary_vars)}

        after_clause = set()
        for old in states:
            for new_bits in itertools.product((0, 1), repeat=len(new_vars)):
                transition_work += 1
                if transition_work > TRANSITION_WORK_CAP:
                    terminal = 'OPEN_TRANSITION_WORK_CAP'
                    trigger = {
                        'clause_index': t,
                        'new_vars': len(new_vars),
                        'live_vars': len(full_vars),
                        'states_before': len(states),
                        'transition_work': transition_work,
                    }
                    break
                values = [0] * len(full_vars)
                for v in boundary_vars:
                    values[pos[v]] = old[prev_pos[v]]
                for v, bit in zip(new_vars, new_bits):
                    values[pos[v]] = bit
                sat = False
                for lit in clause:
                    bit = values[pos[abs(lit)]]
                    if bit == (1 if lit > 0 else 0):
                        sat = True
                        break
                if sat:
                    after_clause.add(tuple(values))
            if terminal != 'EXACT_COMPLETE':
                break
        if terminal != 'EXACT_COMPLETE':
            break

        forget = set(forgotten_at.get(t, []))
        next_vars = tuple(v for v in full_vars if v not in forget)
        next_idx = [pos[v] for v in next_vars]
        projected = {tuple(s[i] for i in next_idx) for s in after_clause}

        if len(projected) > STATE_CAP:
            terminal = 'OPEN_BOUNDARY_STATE_CAP'
            trigger = {
                'clause_index': t,
                'clause_width': len(clause),
                'new_vars': len(new_vars),
                'forgotten_vars': len(forget),
                'live_vars_before_forget': len(full_vars),
                'boundary_vars_after_forget': len(next_vars),
                'states_before': len(states),
                'states_after_clause_before_forget': len(after_clause),
                'states_after_projection': len(projected),
                'transition_work': transition_work,
            }
            break

        states = projected
        boundary_vars = next_vars
        if len(states) > max_states:
            max_states = len(states)
            max_states_clause = t
        if t < 10 or t == max_live_clause or len(states) > STATE_CAP // 2:
            steps.append({
                'clause_index': t,
                'clause_width': len(clause),
                'new_vars': len(new_vars),
                'forgotten_vars': len(forget),
                'boundary_vars': len(boundary_vars),
                'states': len(states),
                'transition_work': transition_work,
            })

        if not states:
            terminal = 'EXACT_UNSAT_PREFIX'
            trigger = {'clause_index': t, 'transition_work': transition_work}
            break

    if terminal == 'EXACT_COMPLETE':
        assert boundary_vars == ()
        exact_sat = bool(states)
        terminal = 'EXACT_SAT_CURRENT_STATE' if exact_sat else 'EXACT_UNSAT_CURRENT_STATE'
    else:
        exact_sat = None

    result = {
        'artifact_id': 'PF5-GT12-CLAUSE-TRACE-DP-2026-08-25-v1.0',
        'experiment_class': 'MECHANISTIC_SUCCESSOR_NOT_INDEPENDENT_HOLDOUT',
        'claim_ceiling': 'FINITE_CURRENT_STATE_DP_ONLY__PF1_END_TO_END_WITNESS_PROVENANCE_OPEN__P_VS_NP_OPEN',
        'subject': {
            'family': 'GRAPH_TAUTOLOGY',
            'order': pf1.ORDER,
            'original_variables': original_variable_count,
        },
        'frozen_policy': {
            'clause_order': 'CURRENT_CANONICAL_CNF_SERIALIZATION_NO_SEARCH',
            'boundary_state_cap': STATE_CAP,
            'transition_work_cap': TRANSITION_WORK_CAP,
            'posthoc_order_change_allowed': False,
            'posthoc_cap_raise_allowed': False,
        },
        'input_state': {
            'units': pf1.encoding_units(cnf),
            'clauses': len(cnf),
            'variables': len(pf1.vars_of(cnf)),
            'congruence_merges': merges,
        },
        'width': {
            'max_live_variables': max_live,
            'lambda_clause': lambda_clause,
            'max_live_clause_index': max_live_clause,
        },
        'dp': {
            'terminal': terminal,
            'exact_sat_current_state': exact_sat,
            'transition_work': transition_work,
            'max_retained_states': max_states,
            'max_retained_states_clause_index': max_states_clause,
            'trigger': trigger,
            'selected_step_receipts': steps[:100],
        },
        'scientific_boundary': [
            'The width is exact only for the frozen canonical clause trace, not minimum pathwidth.',
            'The DP is exact until a frozen state/work cap is hit.',
            'A cap hit closes only this explicit clause-trace DP lane on this finite state.',
            'A finite exact decision of the transformed state would not discharge the separate PF1 original-root witness/provenance implementation obligation.',
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
