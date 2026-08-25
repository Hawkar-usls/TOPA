#!/usr/bin/env python3
"""PF5 giant connected 3-CNF source-to-boundary gate v7.

Starts from neutral connected 3-CNF. Frozen source pipeline:
SIGNED_PARITY_GRAPH_CNF -> ARTICULATION_BOUNDARY_3CNF -> GENERIC_OBDD.

For a discovered articulation variable b, clauses are partitioned exactly into
private child CNFs sharing only b. Each child is built as an exact local OBDD,
private roots are existentially projected, child relations over b are joined,
and SAT witnesses are reconstructed from the actual child projection proofs.

Finite mechanics only. P vs NP remains open.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pf5_boundary_coverage_matrix_v0 as base
import pf5_connected_boundary_adhesion_v3 as v3
import pf5_non_affine_connected_boundary_v4 as v4
import pf5_source_representation_bootstrap_v6 as v6


STAR_M = (2, 4, 8, 12, 16, 20)
RING_N = (6, 8, 10, 12, 14)
PIPELINE_ORDER = (
    'SIGNED_PARITY_GRAPH_CNF',
    'ARTICULATION_BOUNDARY_3CNF',
    'GENERIC_FROZEN_ORDER_OBDD',
)

Clause = v6.Clause
CNF = v6.CNF


@dataclass(frozen=True)
class Fixture:
    name: str
    size: int
    kind: str
    expected_path: str
    expected_sat: bool
    variables: Tuple[int, ...]
    order: Tuple[int, ...]
    clauses: CNF


def pin_gadget(b: int, a: int, c: int, target: int) -> List[Clause]:
    blit = b if target else -b
    return [
        v6.canon_clause((blit, a, c)),
        v6.canon_clause((blit, a, -c)),
        v6.canon_clause((blit, -a, c)),
        v6.canon_clause((blit, -a, -c)),
    ]


def make_fixtures() -> List[Fixture]:
    out: List[Fixture] = []
    for m in STAR_M:
        b = 1
        variables = tuple(range(1, 2 * m + 2))
        order = variables

        sat_clauses: List[Clause] = []
        unsat_clauses: List[Clause] = []
        for i in range(m):
            a = 2 + 2 * i
            c = 3 + 2 * i
            sat_clauses.extend(pin_gadget(b, a, c, 1))
            target = 0 if i == m - 1 else 1
            unsat_clauses.extend(pin_gadget(b, a, c, target))

        out.append(Fixture(
            f'3CNF_ART_STAR_M{m}_SAT', m, 'ARTICULATION_STAR_SAT',
            'ARTICULATION_BOUNDARY_3CNF', True,
            variables, order,
            v6.shuffled_cnf(sat_clauses, f'PF5-V7-STAR-SAT-{m}'),
        ))
        out.append(Fixture(
            f'3CNF_ART_STAR_M{m}_UNSAT', m, 'ARTICULATION_STAR_UNSAT',
            'ARTICULATION_BOUNDARY_3CNF', False,
            variables, order,
            v6.shuffled_cnf(unsat_clauses, f'PF5-V7-STAR-UNSAT-{m}'),
        ))

    for n in RING_N:
        variables = tuple(range(1, n + 1))
        clauses: List[Clause] = []
        for i in range(n):
            tri = (1 + i, 1 + ((i + 1) % n), 1 + ((i + 2) % n))
            clauses.append(v6.canon_clause(tri))
        out.append(Fixture(
            f'3CNF_2CONNECTED_RING_N{n}', n, 'TWO_CONNECTED_RING',
            'GENERIC_FROZEN_ORDER_OBDD', True,
            variables, variables,
            v6.shuffled_cnf(clauses, f'PF5-V7-RING-{n}'),
        ))
    return out


def hash_obj(obj) -> str:
    return sha256(base.canon_json(obj).encode()).hexdigest()


# ---------------------------------------------------------------------------
# Primal graph + articulation discovery
# ---------------------------------------------------------------------------


def build_primal_graph(clauses: Sequence[Clause], variables: Sequence[int]) -> Tuple[Dict[int, Set[int]], int]:
    graph: Dict[int, Set[int]] = {int(v): set() for v in variables}
    varset = set(graph)
    ops = 0
    for clause in clauses:
        vars_c = [abs(lit) for lit in clause]
        ops += len(clause)
        if any(v not in varset for v in vars_c):
            raise AssertionError('source clause references undeclared variable')
        for i in range(len(vars_c)):
            for j in range(i + 1, len(vars_c)):
                u, v = vars_c[i], vars_c[j]
                if u != v:
                    graph[u].add(v)
                    graph[v].add(u)
                    ops += 1
    return graph, ops


def graph_connected(graph: Dict[int, Set[int]]) -> Tuple[bool, int]:
    if not graph:
        return True, 0
    start = min(graph)
    seen: Set[int] = set()
    stack = [start]
    ops = 0
    while stack:
        u = stack.pop()
        ops += 1
        if u in seen:
            continue
        seen.add(u)
        stack.extend(sorted(graph[u] - seen, reverse=True))
    return seen == set(graph), ops


def tarjan_articulations(graph: Dict[int, Set[int]]) -> Tuple[List[int], List[Dict], int]:
    disc: Dict[int, int] = {}
    low: Dict[int, int] = {}
    parent: Dict[int, Optional[int]] = {}
    aps: Set[int] = set()
    transcript: List[Dict] = []
    time = 0
    ops = 0

    def dfs(u: int) -> None:
        nonlocal time, ops
        time += 1
        disc[u] = low[u] = time
        children = 0
        transcript.append({'enter': u, 'disc': time})
        for v in sorted(graph[u]):
            ops += 1
            if v not in disc:
                parent[v] = u
                children += 1
                dfs(v)
                low[u] = min(low[u], low[v])
                transcript.append({'tree_edge': [u, v], 'low_u': low[u], 'low_v': low[v]})
                if parent.get(u) is None and children > 1:
                    aps.add(u)
                if parent.get(u) is not None and low[v] >= disc[u]:
                    aps.add(u)
            elif v != parent.get(u):
                low[u] = min(low[u], disc[v])
                transcript.append({'back_edge': [u, v], 'low_u': low[u]})

    for root in sorted(graph):
        if root not in disc:
            parent[root] = None
            dfs(root)
    return sorted(aps), transcript, ops + len(disc)


def components_without(graph: Dict[int, Set[int]], removed: int) -> Tuple[List[Tuple[int, ...]], int]:
    remaining = set(graph) - {removed}
    seen: Set[int] = set()
    comps: List[Tuple[int, ...]] = []
    ops = 0
    for start in sorted(remaining):
        if start in seen:
            continue
        comp: Set[int] = set()
        stack = [start]
        while stack:
            u = stack.pop()
            ops += 1
            if u in seen or u == removed:
                continue
            seen.add(u)
            comp.add(u)
            stack.extend(sorted((graph[u] - {removed}) - seen, reverse=True))
        comps.append(tuple(sorted(comp)))
    return comps, ops


def discover_articulation_boundary(
    clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int]
) -> Dict:
    graph, graph_ops = build_primal_graph(clauses, variables)
    connected, conn_ops = graph_connected(graph)
    aps, tarjan_proof, tarjan_ops = tarjan_articulations(graph)
    ops = graph_ops + conn_ops + tarjan_ops
    proof: Dict = {
        'recognizer': 'ARTICULATION_BOUNDARY_3CNF',
        'source_sha256': v6.cnf_hash(clauses, variables, order),
        'source_connected': connected,
        'articulation_candidates': aps,
        'tarjan_transcript': tarjan_proof,
        'candidate_checks': [],
        'reject': None,
    }
    if not connected:
        proof['reject'] = {'reason': 'SOURCE_PRIMAL_GRAPH_NOT_CONNECTED'}
        return {'accepted': False, 'ops': ops, 'proof': proof, 'proof_bytes': base.json_bytes(proof)}

    for sep in aps:
        comps, cops = components_without(graph, sep)
        ops += cops
        if len(comps) < 2:
            proof['candidate_checks'].append({'separator': sep, 'status': 'REJECT_LT2_COMPONENTS'})
            continue
        comp_id: Dict[int, int] = {}
        for i, comp in enumerate(comps):
            for v in comp:
                comp_id[v] = i
        child_clauses: List[List[Clause]] = [[] for _ in comps]
        valid = True
        reason = None
        for clause in clauses:
            nonsep = {abs(l) for l in clause if abs(l) != sep}
            ids = {comp_id[v] for v in nonsep}
            ops += len(clause)
            if len(ids) != 1:
                valid = False
                reason = {'reason': 'CLAUSE_CROSSES_REMOVED_COMPONENTS', 'clause': list(clause)}
                break
            child_clauses[next(iter(ids))].append(tuple(clause))
        if not valid:
            proof['candidate_checks'].append({'separator': sep, 'status': 'REJECT', 'detail': reason})
            continue

        flattened = [c for group in child_clauses for c in group]
        roundtrip = sorted(flattened) == sorted(clauses) and len(flattened) == len(clauses)
        ops += len(flattened)
        if not roundtrip:
            proof['candidate_checks'].append({'separator': sep, 'status': 'REJECT_ROUNDTRIP'})
            continue

        children = []
        for comp, group in zip(comps, child_clauses):
            children.append({
                'private_vars': tuple(comp),
                'clauses': tuple(sorted(group)),
            })
        children.sort(key=lambda x: x['private_vars'])
        proof['candidate_checks'].append({
            'separator': sep,
            'status': 'ACCEPT',
            'component_sizes': [len(c['private_vars']) for c in children],
            'clause_counts': [len(c['clauses']) for c in children],
            'roundtrip_exact': True,
        })
        proof['selected_separator'] = sep
        proof['partition_sha256'] = hash_obj([
            {'private_vars': list(c['private_vars']), 'clauses': [list(q) for q in c['clauses']]}
            for c in children
        ])
        return {
            'accepted': True,
            'separator': sep,
            'children': children,
            'source_connected': connected,
            'roundtrip_exact': True,
            'ops': ops,
            'proof': proof,
            'proof_bytes': base.json_bytes(proof),
        }

    proof['reject'] = {'reason': 'NO_VALID_ARTICULATION_SEPARATOR'}
    return {
        'accepted': False,
        'source_connected': connected,
        'ops': ops,
        'proof': proof,
        'proof_bytes': base.json_bytes(proof),
    }


# ---------------------------------------------------------------------------
# Exact articulation solver
# ---------------------------------------------------------------------------


def solve_articulation(
    clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int],
    discovery: Dict, prior_ops: int, prior_proof_bytes: int
) -> Dict:
    sep = int(discovery['separator'])
    source_bytes = v6.cnf_bytes(clauses, variables, order)
    global_ops = prior_ops + int(discovery['ops'])
    global_proof_bytes = prior_proof_bytes + int(discovery['proof_bytes'])
    global_cumulative = source_bytes
    global_peak = source_bytes
    retained_state_bytes = 0
    child_records: List[Dict] = []
    child_runtime: List[Tuple[base.BDD, Dict, Tuple[int, ...]]] = []

    current_join: Set[int] = {0, 1}
    join_proof: List[Dict] = []
    join_ops = 0

    for idx, child in enumerate(discovery['children']):
        priv = tuple(int(v) for v in child['private_vars'])
        child_clauses = tuple(tuple(int(l) for l in c) for c in child['clauses'])
        local_vars = tuple(sorted(set(priv) | {sep}))
        local_order = tuple(sorted(priv)) + (sep,)
        local_source_bytes = v6.cnf_bytes(child_clauses, local_vars, local_order)

        built = v6.build_generic_obdd(
            child_clauses, local_vars, local_order,
            global_ops, global_proof_bytes, local_source_bytes,
        )
        if built['status'] == 'CAP_HIT':
            return {
                'status': 'CAP_HIT', 'cap_phase': 'CHILD_OBDD_BUILD',
                'cap_reason': built['cap_reason'], 'child_index': idx,
                'partial_nodes': built['partial_nodes'],
                'partial_manager_bytes': built['partial_manager_bytes'],
            }
        b = built['bdd']
        root = int(built['root'])
        global_ops += int(built['build_ops'])
        global_proof_bytes += int(built['proof_bytes'])
        global_cumulative += int(built['cumulative'])
        global_peak = max(global_peak, int(built['peak']))

        projected = v4.project_private_obdd(
            b, root, priv,
            global_ops, global_proof_bytes,
        )
        global_ops += int(projected['projection_ops'])
        global_proof_bytes += int(projected['proof_bytes'])
        global_cumulative += int(projected['cumulative_state_bytes'])
        global_peak = max(global_peak, int(projected['representation_bytes_peak']))

        residual_root = int(projected['root'])
        support, support_ops = v4.bdd_support(b, residual_root)
        global_ops += support_ops
        if not support <= {sep}:
            raise AssertionError(f'child residual retains non-boundary support {support}')

        allowed: Set[int] = set()
        eval_ops = 0
        for bit in (0, 1):
            ok, z = v3.eval_bdd_count(b, residual_root, {sep: bool(bit)})
            eval_ops += z
            if ok:
                allowed.add(bit)
        global_ops += eval_ops

        pre_join = set(current_join)
        current_join &= allowed
        join_ops += len(pre_join)
        join_proof.append({
            'child_index': idx,
            'child_relation': sorted(allowed),
            'join_before': sorted(pre_join),
            'join_after': sorted(current_join),
        })

        relation_bytes = base.json_bytes({'separator': sep, 'allowed': sorted(allowed)})
        manager_bytes = v4.manager_bytes(b)
        retained_state_bytes += manager_bytes + relation_bytes
        product_bytes = retained_state_bytes + base.json_bytes({
            'separator': sep, 'join': sorted(current_join), 'children_seen': idx + 1,
        })
        global_peak = max(global_peak, product_bytes)
        global_cumulative += relation_bytes + product_bytes

        record = {
            'child_index': idx,
            'private_vars': list(priv),
            'clause_count': len(child_clauses),
            'local_source_bytes': local_source_bytes,
            'boundary_relation': sorted(allowed),
            'manager_nodes_total': len(b.nodes),
            'manager_bytes': manager_bytes,
            'build_ops': int(built['build_ops']),
            'private_projection_ops': int(projected['projection_ops']),
            'boundary_eval_ops': eval_ops,
            'private_proof_bytes': int(projected['proof_bytes']),
            'residual_root': residual_root,
        }
        child_records.append(record)
        child_runtime.append((b, projected, priv))
        base.check_common_caps(global_peak, global_proof_bytes, global_cumulative, global_ops + join_ops)

    global_ops += join_ops
    join_proof_bytes = base.json_bytes(join_proof)
    global_proof_bytes += join_proof_bytes
    join_state_bytes = base.json_bytes({'separator': sep, 'allowed': sorted(current_join)})
    global_peak = max(global_peak, retained_state_bytes + join_state_bytes)
    global_cumulative += join_state_bytes
    base.check_common_caps(global_peak, global_proof_bytes, global_cumulative, global_ops)

    final_scalar = bool(current_join)
    boundary_project_proof = {
        'separator': sep,
        'pre_relation': sorted(current_join),
        'post_scalar': final_scalar,
        'rule': 'EXISTS_BOUNDARY_NONEMPTY_RELATION',
    }
    global_proof_bytes += base.json_bytes(boundary_project_proof)
    global_ops += 1

    witness: Optional[Dict[int, bool]] = None
    witness_ops = 0
    verification_ops = 0
    witness_source = 'NO_WITNESS_EMPTY_BOUNDARY_JOIN'
    witness_valid: Optional[bool] = None

    if final_scalar:
        bval = min(current_join)
        witness = {sep: bool(bval)}
        for (b, projected, priv), rec in zip(child_runtime, child_records):
            env, z = v4.lift_bdd_projection_witness(b, projected['proof'], {sep: bool(bval)})
            witness_ops += z
            for v in priv:
                if v not in env:
                    raise AssertionError(f'child witness missing {v}')
                if v in witness:
                    raise AssertionError(f'private overlap at {v}')
                witness[v] = env[v]
        if set(witness) != set(variables):
            raise AssertionError('articulation witness does not cover all source variables')
        witness_valid, verification_ops = v6.eval_cnf(clauses, witness)
        if not witness_valid:
            raise AssertionError('articulation witness fails original source CNF')
        witness_source = 'DISCOVERED_BOUNDARY_JOIN_PLUS_ACTUAL_CHILD_OBDD_PROOFS'

    global_ops += witness_ops + verification_ops
    witness_bytes = base.json_bytes(witness or {})
    base.check_common_caps(global_peak, global_proof_bytes, global_cumulative, global_ops)

    cert = {
        'source_sha256': v6.cnf_hash(clauses, variables, order),
        'separator': sep,
        'partition_sha256': discovery['proof']['partition_sha256'],
        'children': child_records,
        'join_proof': join_proof,
        'boundary_project': boundary_project_proof,
        'witness_sha256': hash_obj(witness or {}),
    }
    return {
        'status': 'PASS_EXACT_CLOSED',
        'selected_path': 'ARTICULATION_BOUNDARY_3CNF',
        'source_connected': bool(discovery['source_connected']),
        'separator': sep,
        'child_count': len(child_records),
        'source_partition_roundtrip_exact': bool(discovery['roundtrip_exact']),
        'children': child_records,
        'boundary_join_relation': sorted(current_join),
        'boundary_join_exact': True,
        'final_scalar': final_scalar,
        'strict_child_witness_glue': (witness_valid is True) if final_scalar else True,
        'witness_valid': witness_valid,
        'witness_source': witness_source,
        'witness_bytes': witness_bytes,
        'representation_bytes_peak': global_peak,
        'cumulative_state_bytes': global_cumulative,
        'proof_bytes': global_proof_bytes,
        'total_charged_ops': global_ops,
        'witness_ops': witness_ops,
        'verification_ops': verification_ops,
        'certificate_sha256': hash_obj(cert),
        'witness': witness,
    }


# ---------------------------------------------------------------------------
# Unlabeled connected-source pipeline
# ---------------------------------------------------------------------------


def solve_source(
    clauses: Sequence[Clause], variables: Sequence[int], frozen_order: Sequence[int]
) -> Dict:
    source_bytes = v6.cnf_bytes(clauses, variables, frozen_order)
    attempts: List[Dict] = []
    failed_ops = 0
    failed_proof_bytes = 0

    parity = v6.recognize_signed_parity_graph(clauses, variables, frozen_order)
    if parity['accepted']:
        # The v7 frozen controls are 3-CNF and should never enter this lane, but
        # keep the source pipeline exact if a future source does.
        attempts.append({
            'stage': 'SIGNED_PARITY_GRAPH_CNF', 'status': 'ACCEPT',
            'ops': int(parity['ops']), 'proof_bytes': int(parity['proof_bytes']),
        })
        return {
            'status': 'UNEXPECTED_EARLY_STRUCTURAL_ACCEPT',
            'attempts': attempts,
            'source_bytes': source_bytes,
        }
    attempts.append({
        'stage': 'SIGNED_PARITY_GRAPH_CNF', 'status': 'REJECT',
        'ops': int(parity['ops']), 'proof_bytes': int(parity['proof_bytes']),
        'failure': parity['proof']['reject'],
    })
    failed_ops += int(parity['ops'])
    failed_proof_bytes += int(parity['proof_bytes'])

    articulation = discover_articulation_boundary(clauses, variables, frozen_order)
    if articulation['accepted']:
        attempts.append({
            'stage': 'ARTICULATION_BOUNDARY_3CNF', 'status': 'ACCEPT',
            'ops': int(articulation['ops']), 'proof_bytes': int(articulation['proof_bytes']),
            'separator': int(articulation['separator']),
        })
        solved = solve_articulation(
            clauses, variables, frozen_order,
            articulation,
            failed_ops, failed_proof_bytes,
        )
        solved['pipeline_attempts'] = attempts
        solved['failed_pipeline_ops'] = failed_ops
        solved['failed_pipeline_proof_bytes'] = failed_proof_bytes
        solved['articulation_discovery_ops'] = int(articulation['ops'])
        solved['articulation_discovery_proof_bytes'] = int(articulation['proof_bytes'])
        solved['source_bytes'] = source_bytes
        return solved

    attempts.append({
        'stage': 'ARTICULATION_BOUNDARY_3CNF', 'status': 'REJECT',
        'ops': int(articulation['ops']), 'proof_bytes': int(articulation['proof_bytes']),
        'failure': articulation['proof']['reject'],
    })
    failed_ops += int(articulation['ops'])
    failed_proof_bytes += int(articulation['proof_bytes'])

    generic = v6.build_generic_obdd(
        clauses, variables, frozen_order,
        failed_ops, failed_proof_bytes, source_bytes,
    )
    if generic['status'] == 'CAP_HIT':
        attempts.append({
            'stage': 'GENERIC_FROZEN_ORDER_OBDD', 'status': 'CAP_HIT',
            'ops': int(generic['build_ops']), 'proof_bytes': int(generic['proof_bytes']),
            'cap_reason': generic['cap_reason'],
        })
        return {
            'status': 'CAP_HIT', 'cap_phase': 'GENERIC_SOURCE_OBDD_BUILD',
            'cap_reason': generic['cap_reason'],
            'pipeline_attempts': attempts,
            'failed_pipeline_ops': failed_ops + int(generic['build_ops']),
            'failed_pipeline_proof_bytes': failed_proof_bytes + int(generic['proof_bytes']),
            'source_bytes': source_bytes,
            'partial_nodes': generic['partial_nodes'],
            'partial_manager_bytes': generic['partial_manager_bytes'],
        }

    attempts.append({
        'stage': 'GENERIC_FROZEN_ORDER_OBDD', 'status': 'ACCEPT',
        'ops': int(generic['build_ops']), 'proof_bytes': int(generic['proof_bytes']),
    })
    b = generic['bdd']
    root = int(generic['root'])
    prior_ops = failed_ops + int(generic['build_ops'])
    prior_proof = failed_proof_bytes + int(generic['proof_bytes'])
    projected = v4.project_common_boundary(
        b, root, frozen_order,
        prior_ops, prior_proof,
        int(generic['cumulative']), int(generic['peak']),
    )
    final_root = int(projected['root'])
    if final_root not in (0, 1):
        raise AssertionError('generic ring projection remained nonterminal')
    final_scalar = bool(final_root)
    witness: Optional[Dict[int, bool]] = None
    witness_ops = 0
    verification_ops = 0
    witness_valid: Optional[bool] = None
    witness_source = 'NO_WITNESS_GENERIC_FALSE'
    if final_scalar:
        witness, witness_ops = v4.lift_bdd_projection_witness(b, projected['proof'], {})
        if set(witness) != set(variables):
            raise AssertionError('generic ring witness incomplete')
        witness_valid, verification_ops = v6.eval_cnf(clauses, witness)
        if not witness_valid:
            raise AssertionError('generic ring witness fails source CNF')
        witness_source = 'GENERIC_SOURCE_OBDD_PROJECTION_PROOF'

    total_ops = prior_ops + int(projected['ops']) + witness_ops + verification_ops
    proof_bytes = prior_proof + int(projected['proof_bytes'])
    peak = int(projected['representation_bytes_peak'])
    cumulative = int(projected['cumulative_state_bytes'])
    base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

    return {
        'status': 'PASS_EXACT_CLOSED',
        'selected_path': 'GENERIC_FROZEN_ORDER_OBDD',
        'pipeline_attempts': attempts,
        'failed_pipeline_ops': failed_ops,
        'failed_pipeline_proof_bytes': failed_proof_bytes,
        'source_bytes': source_bytes,
        'source_connected': bool(articulation['source_connected']),
        'articulation_rejected': True,
        'final_scalar': final_scalar,
        'strict_source_witness': (witness_valid is True) if final_scalar else True,
        'witness_valid': witness_valid,
        'witness_source': witness_source,
        'witness_bytes': base.json_bytes(witness or {}),
        'representation_bytes_peak': peak,
        'cumulative_state_bytes': cumulative,
        'proof_bytes': proof_bytes,
        'total_charged_ops': total_ops,
        'manager_nodes_total': len(b.nodes),
        'certificate_sha256': hash_obj({
            'source': v6.cnf_hash(clauses, variables, frozen_order),
            'attempts': attempts,
            'projection': projected['proof'],
            'witness': witness or {},
        }),
        'witness': witness,
    }


def run_fixture(f: Fixture) -> Dict:
    solved = solve_source(f.clauses, f.variables, f.order)
    if solved['status'] == 'CAP_HIT':
        return {
            'fixture': f.name, 'size': f.size,
            'external_kind_for_test_only': f.kind,
            'expected_path_external_test_only': f.expected_path,
            'expected_sat': f.expected_sat,
            **solved,
            'claim': 'FINITE_CONNECTED_3CNF_REPRESENTATION_ESCAPE_ONLY',
        }
    if solved['status'] != 'PASS_EXACT_CLOSED':
        raise AssertionError(f'unexpected source-pipeline status {solved["status"]}')
    if bool(solved['final_scalar']) != f.expected_sat:
        raise AssertionError(f'final scalar mismatch for {f.name}')

    attempts = solved['pipeline_attempts']
    failed_attempts = [a for a in attempts if a['status'] == 'REJECT']
    failed_charged = (
        int(solved['failed_pipeline_ops']) == sum(int(a['ops']) for a in failed_attempts)
        and int(solved['failed_pipeline_proof_bytes']) == sum(int(a['proof_bytes']) for a in failed_attempts)
    )
    return {
        'fixture': f.name, 'size': f.size,
        'external_kind_for_test_only': f.kind,
        'expected_path_external_test_only': f.expected_path,
        'expected_sat': f.expected_sat,
        **solved,
        'source_is_single_connected_3cnf': bool(solved['source_connected']) and all(len(c)==3 for c in f.clauses),
        'pipeline_api_unlabeled': True,
        'fixed_pipeline_order_used': [a['stage'] for a in attempts] == list(PIPELINE_ORDER[:len(attempts)]),
        'failed_pipeline_work_charged': failed_charged,
        'path_matches_frozen_expectation': solved['selected_path'] == f.expected_path,
    }


def main(argv: Sequence[str]) -> int:
    rows = [run_fixture(f) for f in make_fixtures()]
    passed = [r for r in rows if r['status']=='PASS_EXACT_CLOSED']
    first_cap = next((r for r in rows if r['status']=='CAP_HIT'), None)

    star_pass = [r for r in passed if r['external_kind_for_test_only'].startswith('ARTICULATION_STAR')]
    ring_rows = [r for r in rows if r['external_kind_for_test_only']=='TWO_CONNECTED_RING']

    result = {
        'artifact_id': 'PF5-GIANT-CONNECTED-3CNF-SOURCE-BOUNDARY-V7',
        'protocol': 'PF5_GIANT_CONNECTED_3CNF_SOURCE_BOUNDARY_GATE_V7.md',
        'claim_ceiling': 'P_VS_NP = OPEN',
        'star_sizes_frozen_before_provider_run': list(STAR_M),
        'ring_sizes_frozen_before_provider_run': list(RING_N),
        'pipeline_order_frozen_before_provider_run': list(PIPELINE_ORDER),
        'caps': base.CAPS,
        'new_tuned_caps_added': False,
        'controls': rows,
        'passed_controls': len(passed),
        'all_passed_connected_3cnf': all(r['source_is_single_connected_3cnf'] for r in passed) if passed else False,
        'all_passed_pipeline_unlabeled': all(r['pipeline_api_unlabeled'] for r in passed) if passed else False,
        'all_passed_fixed_pipeline_order': all(r['fixed_pipeline_order_used'] for r in passed) if passed else False,
        'all_passed_failed_work_charged': all(r['failed_pipeline_work_charged'] for r in passed) if passed else False,
        'all_passed_path_matches_expectation': all(r['path_matches_frozen_expectation'] for r in passed) if passed else False,
        'articulation_star_sat_and_unsat_closed': all(
            r['selected_path']=='ARTICULATION_BOUNDARY_3CNF'
            and r['source_partition_roundtrip_exact']
            and r['boundary_join_exact']
            and r['strict_child_witness_glue']
            for r in star_pass
        ) and len(star_pass)==2*len(STAR_M),
        'two_connected_ring_reaches_fallback': all(
            any(a['stage']=='ARTICULATION_BOUNDARY_3CNF' and a['status']=='REJECT' for a in r['pipeline_attempts'])
            and any(a['stage']=='GENERIC_FROZEN_ORDER_OBDD' for a in r['pipeline_attempts'])
            for r in ring_rows
        ),
        'first_base_cap_hit': None if first_cap is None else {
            'fixture': first_cap['fixture'], 'size': first_cap['size'],
            'phase': first_cap.get('cap_phase'), 'reason': first_cap['cap_reason'],
            'partial_nodes': first_cap.get('partial_nodes', 0),
            'partial_manager_bytes': first_cap.get('partial_manager_bytes', 0),
        },
        'width_one_separator_discovery_poly_in_explicit_source': 'PROVED_BY_TARJAN_PLUS_LINEAR_PARTITION_CHECK',
        'universal_small_separator_existence': 'OPEN',
        'universal_small_separator_discovery': 'OPEN',
        'two_connected_core_representation_discovery': 'OPEN',
        'universal_polynomial_coverage': 'OPEN',
        'global_progress_amortization': 'OPEN',
        'representation_lower_bound': 'NOT_ESTABLISHED',
        'next_front': 'TWO_CONNECTED_3CNF_CORE_GATE',
        'p_vs_np': 'OPEN',
    }
    result['result_sha256'] = hash_obj(result)

    print('PF5_GIANT_CONNECTED_3CNF_SOURCE_BOUNDARY_V7 = FROZEN')
    for r in rows:
        if r['status']=='PASS_EXACT_CLOSED':
            print(
                r['fixture'], 'status=PASS_EXACT_CLOSED', 'size=', r['size'],
                'path=', r['selected_path'],
                'attempts=', [(a['stage'],a['status']) for a in r['pipeline_attempts']],
                'peak=', r['representation_bytes_peak'],
                'ops=', r['total_charged_ops'],
                'scalar=', r['final_scalar'],
                'witness=', r['witness_source'],
            )
        else:
            print(
                r['fixture'], 'status=CAP_HIT', 'size=', r['size'],
                'phase=', r.get('cap_phase'), 'cap=', r['cap_reason'],
            )
    print('ARTICULATION_STAR_SAT_AND_UNSAT_CLOSED =', result['articulation_star_sat_and_unsat_closed'])
    print('TWO_CONNECTED_RING_REACHES_FALLBACK =', result['two_connected_ring_reaches_fallback'])
    print('FIRST_BASE_CAP_HIT =', result['first_base_cap_hit'])
    print('TWO_CONNECTED_CORE_REPRESENTATION_DISCOVERY = OPEN')
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =', result['result_sha256'])

    if '--json-out' in argv:
        i=list(argv).index('--json-out')
        with open(argv[i+1], 'w', encoding='utf-8') as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
            fh.write('\n')
    return 0


if __name__=='__main__':
    raise SystemExit(main(sys.argv[1:]))
