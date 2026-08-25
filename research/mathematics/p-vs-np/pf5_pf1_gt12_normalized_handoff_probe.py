#!/usr/bin/env python3
"""PF5 GT12 mechanistic successor: PF1 -> certified subsumption -> exact handoff.

This is NOT an independent holdout. It was frozen only after the prior GT12 PF1
run ended at OPEN_HANDOFF_INPUT_CAP. No cap from the prior run is raised.

The normalizer is exact and proof-carrying. Discovery work is counted as subset
membership probes and is fail-closed under a frozen cap.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

NORMALIZATION_SUBSET_PROBE_CAP = 500_000
HANDOFF_ENCODING_CAP = 20_000
STATE_BUDGET = 20_000


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--topa-root', type=Path, required=True)
    ap.add_argument('--fundamentum-root', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()

    pnp_dir = args.topa_root / 'research' / 'mathematics' / 'p-vs-np'
    direct = args.fundamentum_root / 'experiments' / 'direct'
    sys.path.insert(0, str(pnp_dir))
    sys.path.insert(0, str(direct))

    import pf5_pf1_gt12_holdout_probe as pf1
    from janus_tear_policy0a_graph_tautology_probe import graph_tautology_cnf
    from janus_c025_core import (
        SubsumptionStep,
        NormalizationCertificate,
        cnf_hash,
        verify_normalization,
        compile_residual_automaton,
    )

    # Rebuild the exact prior PF1 residue under the same frozen root policy.
    cnf_raw, original_variable_count = graph_tautology_cnf(pf1.ORDER)
    cnf = pf1.canonical_cnf(cnf_raw)
    pf1_steps = []
    for pivot in range(1, original_variable_count + 1):
        if pivot not in pf1.vars_of(cnf):
            continue
        cnf, step = pf1.rewrite_pf1(cnf, pivot)
        pf1_steps.append(step)
        if step.output_units > pf1.ENCODING_CAP:
            result = {
                'artifact_id': 'PF5-PF1-GT12-NORM-HANDOFF-2026-08-25-v1.0',
                'terminal': 'OPEN_PF1_ENCODING_CAP',
                'claim_ceiling': 'FINITE_MECHANICS_ONLY__P_VS_NP_OPEN',
                'p_vs_np': 'OPEN',
            }
            text = json.dumps(result, indent=2, sort_keys=True) + '\n'
            if args.output:
                args.output.write_text(text, encoding='utf-8')
            print(text, end='')
            return

    before = cnf
    before_units = pf1.encoding_units(before)
    before_clauses = len(before)
    before_literals = sum(map(len, before))
    max_clause_width = max((len(c) for c in before), default=0)

    # Exact indexed subsumption. Clauses are processed shortest first. For each
    # clause we enumerate its literal subsets and test whether a retained clause
    # is exactly one of those subsets. Every membership test is charged.
    retained = []
    retained_set = set()
    steps = []
    subset_probes = 0
    terminal = 'NORMALIZATION_COMPLETE'

    for clause in sorted(before, key=lambda c: (len(c), c)):
        found = None
        # Proper subsets are sufficient because canonical_cnf has deduplicated
        # equal clauses. Empty clause is included naturally when present.
        for r in range(0, len(clause)):
            for idxs in itertools.combinations(range(len(clause)), r):
                subset_probes += 1
                if subset_probes > NORMALIZATION_SUBSET_PROBE_CAP:
                    terminal = 'OPEN_NORMALIZATION_DISCOVERY_CAP'
                    break
                cand = tuple(clause[i] for i in idxs)
                # canonical order is inherited by subsequences of canonical clause.
                if cand in retained_set:
                    found = cand
                    break
            if terminal != 'NORMALIZATION_COMPLETE' or found is not None:
                break
        if terminal != 'NORMALIZATION_COMPLETE':
            break
        if found is not None:
            steps.append(SubsumptionStep(clause, found))
        else:
            retained.append(clause)
            retained_set.add(clause)

    automaton = None
    normalized = None
    certificate_ok = False
    if terminal == 'NORMALIZATION_COMPLETE':
        normalized = pf1.canonical_cnf(retained)
        cert = NormalizationCertificate(cnf_hash(before), cnf_hash(normalized), tuple(steps))
        certificate_ok = verify_normalization(before, normalized, cert)
        assert certificate_ok
        normalized_units = pf1.encoding_units(normalized)
        if normalized_units > HANDOFF_ENCODING_CAP:
            terminal = 'OPEN_HANDOFF_INPUT_CAP_AFTER_CERTIFIED_NORMALIZATION'
        else:
            remaining = pf1.vars_of(normalized)
            ar = compile_residual_automaton(normalized, remaining, state_budget=STATE_BUDGET)
            automaton = {
                'status': ar.status,
                'sat': ar.sat,
                'witness_valid': ar.witness is not None and pf1.eval_cnf(normalized, ar.witness) if ar.witness is not None else False,
                'residual_states': ar.stats.residual_states,
                'bdd_nodes': ar.stats.bdd_nodes,
                'max_frontier_states': ar.stats.max_frontier_states,
                'subsumption_steps': ar.stats.subsumption_steps,
                'normalization_certificates': ar.stats.normalization_certificates,
                'error': ar.stats.error,
            }
            terminal = 'EXACT' if ar.status == 'EXACT' else 'OPEN_RESIDUAL_AUTOMATON_CAP'
    else:
        normalized_units = None

    result = {
        'artifact_id': 'PF5-PF1-GT12-NORM-HANDOFF-2026-08-25-v1.0',
        'experiment_class': 'MECHANISTIC_SUCCESSOR_NOT_INDEPENDENT_HOLDOUT',
        'claim_ceiling': 'FINITE_MECHANICS_ONLY__P_VS_NP_OPEN',
        'subject': {
            'family': 'GRAPH_TAUTOLOGY',
            'order': pf1.ORDER,
            'original_variables': original_variable_count,
        },
        'frozen_caps': {
            'pf1_encoding_cap': pf1.ENCODING_CAP,
            'normalization_subset_probe_cap': NORMALIZATION_SUBSET_PROBE_CAP,
            'handoff_encoding_cap': HANDOFF_ENCODING_CAP,
            'residual_automaton_state_budget': STATE_BUDGET,
            'posthoc_cap_raise_allowed': False,
        },
        'pf1_residue': {
            'roots_processed': len(pf1_steps),
            'units': before_units,
            'clauses': before_clauses,
            'literals': before_literals,
            'variables': len(pf1.vars_of(before)),
            'max_clause_width': max_clause_width,
        },
        'certified_normalization': {
            'terminal': 'COMPLETE' if normalized is not None else terminal,
            'subset_probes': subset_probes,
            'certificate_steps': len(steps),
            'certificate_verified': certificate_ok,
            'normalized_units': normalized_units,
            'normalized_clauses': len(normalized) if normalized is not None else None,
            'normalized_literals': sum(map(len, normalized)) if normalized is not None else None,
            'normalized_variables': len(pf1.vars_of(normalized)) if normalized is not None else None,
        },
        'automaton_handoff': automaton,
        'terminal': terminal,
        'scientific_boundary': [
            'This run follows the prior GT12 handoff-cap result and is not an independent holdout.',
            'Only syntactic subsumption has logical authority in the normalization step.',
            'Every subset membership probe is charged; no semantic minimization is used.',
            'A finite success does not imply a universal polynomial bound.',
            'A finite cap failure does not imply P!=NP.'
        ],
        'p_vs_np': 'OPEN',
    }

    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
