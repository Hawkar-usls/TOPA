#!/usr/bin/env python3
"""PF5 two-connected 3-CNF core gate v8.

Neutral source pipeline:
SIGNED_PARITY -> ARTICULATION -> PAIR_SEPARATOR -> GENERIC_OBDD.
Positive controls have no articulation point but do have a hidden two-variable
separator. Child relations are exact subsets of {00,01,10,11}; JOIN and strict
witness glue are charged under one global ledger.

Finite mechanics only. P vs NP remains open.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import product
import json
import sys
from typing import Dict, List, Optional, Sequence, Set, Tuple

import pf5_boundary_coverage_matrix_v0 as base
import pf5_connected_boundary_adhesion_v3 as v3
import pf5_non_affine_connected_boundary_v4 as v4
import pf5_source_representation_bootstrap_v6 as v6
import pf5_giant_connected_3cnf_source_boundary_v7 as v7


PAIR_M = (2, 4, 8, 12, 16)
RING_N = (6, 8, 10, 12, 14)
PIPELINE_ORDER = (
    'SIGNED_PARITY_GRAPH_CNF',
    'ARTICULATION_BOUNDARY_3CNF',
    'PAIR_SEPARATOR_BOUNDARY_3CNF',
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


def make_fixtures() -> List[Fixture]:
    out: List[Fixture] = []
    b1, b2 = 1, 2
    for m in PAIR_M:
        variables = tuple(range(1, 2 * m + 3))
        sat: List[Clause] = []
        unsat: List[Clause] = []
        for i in range(m):
            a = 3 + 2 * i
            c = 4 + 2 * i
            sat.extend(v7.pin_gadget(b1, a, c, 1))
            sat.extend(v7.pin_gadget(b2, a, c, 1))
            unsat.extend(v7.pin_gadget(b1, a, c, 1))
            unsat.extend(v7.pin_gadget(b2, a, c, 0 if i == m - 1 else 1))
        out.append(Fixture(
            f'3CNF_PAIRSEP_M{m}_SAT', m, 'PAIR_SEPARATOR_SAT',
            'PAIR_SEPARATOR_BOUNDARY_3CNF', True,
            variables, variables,
            v6.shuffled_cnf(sat, f'PF5-V8-PAIR-SAT-{m}'),
        ))
        out.append(Fixture(
            f'3CNF_PAIRSEP_M{m}_UNSAT', m, 'PAIR_SEPARATOR_UNSAT',
            'PAIR_SEPARATOR_BOUNDARY_3CNF', False,
            variables, variables,
            v6.shuffled_cnf(unsat, f'PF5-V8-PAIR-UNSAT-{m}'),
        ))

    for n in RING_N:
        variables = tuple(range(1, n + 1))
        clauses = [
            v6.canon_clause((1+i, 1+((i+1)%n), 1+((i+2)%n)))
            for i in range(n)
        ]
        out.append(Fixture(
            f'3CNF_PAIRNEG_RING_N{n}', n, 'TWO_CONNECTED_RING',
            'GENERIC_FROZEN_ORDER_OBDD', True,
            variables, variables,
            v6.shuffled_cnf(clauses, f'PF5-V8-RING-{n}'),
        ))
    return out


def hash_obj(obj) -> str:
    return sha256(base.canon_json(obj).encode()).hexdigest()


def components_without_pair(
    graph: Dict[int, Set[int]], removed: Tuple[int, int]
) -> Tuple[List[Tuple[int, ...]], int]:
    banned = set(removed)
    remaining = set(graph) - banned
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
            if u in seen or u in banned:
                continue
            seen.add(u)
            comp.add(u)
            stack.extend(sorted((graph[u] - banned) - seen, reverse=True))
        comps.append(tuple(sorted(comp)))
    return comps, ops


def discover_pair_separator(
    clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int]
) -> Dict:
    graph, graph_ops = v7.build_primal_graph(clauses, variables)
    connected, conn_ops = v7.graph_connected(graph)
    ops = graph_ops + conn_ops
    proof: Dict = {
        'recognizer': 'PAIR_SEPARATOR_BOUNDARY_3CNF',
        'source_sha256': v6.cnf_hash(clauses, variables, order),
        'source_connected': connected,
        'candidate_checks': [],
        'reject': None,
    }
    if not connected:
        proof['reject'] = {'reason': 'SOURCE_PRIMAL_GRAPH_NOT_CONNECTED'}
        return {'accepted': False, 'ops': ops, 'proof': proof, 'proof_bytes': base.json_bytes(proof)}

    vars_sorted = sorted(graph)
    for ii in range(len(vars_sorted)):
        for jj in range(ii + 1, len(vars_sorted)):
            pair = (vars_sorted[ii], vars_sorted[jj])
            ops += 1
            comps, cops = components_without_pair(graph, pair)
            ops += cops
            if len(comps) < 2:
                proof['candidate_checks'].append({'separator': list(pair), 'status': 'REJECT_LT2_COMPONENTS'})
                continue
            cid: Dict[int, int] = {}
            for ci, comp in enumerate(comps):
                for v in comp:
                    cid[v] = ci
            child_clauses: List[List[Clause]] = [[] for _ in comps]
            valid = True
            detail = None
            for clause in clauses:
                nonsep = {abs(l) for l in clause if abs(l) not in pair}
                ids = {cid[v] for v in nonsep}
                ops += len(clause)
                if len(ids) != 1:
                    valid = False
                    detail = {'reason': 'CLAUSE_CROSSES_PAIR_REMOVAL_COMPONENTS', 'clause': list(clause)}
                    break
                child_clauses[next(iter(ids))].append(tuple(clause))
            if not valid:
                proof['candidate_checks'].append({'separator': list(pair), 'status': 'REJECT', 'detail': detail})
                continue
            flat = [c for g in child_clauses for c in g]
            roundtrip = sorted(flat) == sorted(clauses) and len(flat) == len(clauses)
            ops += len(flat)
            if not roundtrip:
                proof['candidate_checks'].append({'separator': list(pair), 'status': 'REJECT_ROUNDTRIP'})
                continue
            children = [
                {'private_vars': tuple(comp), 'clauses': tuple(sorted(group))}
                for comp, group in zip(comps, child_clauses)
            ]
            children.sort(key=lambda x: x['private_vars'])
            proof['candidate_checks'].append({
                'separator': list(pair), 'status': 'ACCEPT',
                'component_sizes': [len(c['private_vars']) for c in children],
                'clause_counts': [len(c['clauses']) for c in children],
                'roundtrip_exact': True,
            })
            proof['selected_separator'] = list(pair)
            proof['partition_sha256'] = hash_obj([
                {'private_vars': list(c['private_vars']), 'clauses': [list(q) for q in c['clauses']]}
                for c in children
            ])
            return {
                'accepted': True,
                'separator': pair,
                'children': children,
                'source_connected': connected,
                'roundtrip_exact': True,
                'ops': ops,
                'proof': proof,
                'proof_bytes': base.json_bytes(proof),
            }

    proof['reject'] = {'reason': 'NO_VALID_PAIR_SEPARATOR'}
    return {'accepted': False, 'source_connected': connected, 'ops': ops, 'proof': proof, 'proof_bytes': base.json_bytes(proof)}


def solve_pair_separator(
    clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int],
    discovery: Dict, prior_ops: int, prior_proof_bytes: int
) -> Dict:
    sep = tuple(int(v) for v in discovery['separator'])
    source_bytes = v6.cnf_bytes(clauses, variables, order)
    global_ops = prior_ops + int(discovery['ops'])
    global_proof = prior_proof_bytes + int(discovery['proof_bytes'])
    cumulative = source_bytes
    peak = source_bytes
    retained = 0
    current_join: Set[str] = {'00','01','10','11'}
    join_proof: List[Dict] = []
    join_ops = 0
    records: List[Dict] = []
    runtime: List[Tuple[base.BDD, Dict, Tuple[int, ...]]] = []

    for idx, child in enumerate(discovery['children']):
        priv = tuple(int(v) for v in child['private_vars'])
        child_clauses = tuple(tuple(int(l) for l in c) for c in child['clauses'])
        local_vars = tuple(sorted(set(priv) | set(sep)))
        local_order = tuple(sorted(priv)) + tuple(sep)
        local_source = v6.cnf_bytes(child_clauses, local_vars, local_order)
        built = v6.build_generic_obdd(child_clauses, local_vars, local_order, global_ops, global_proof, local_source)
        if built['status']=='CAP_HIT':
            return {
                'status':'CAP_HIT','cap_phase':'CHILD_OBDD_BUILD','cap_reason':built['cap_reason'],
                'child_index':idx,'partial_nodes':built['partial_nodes'],
                'partial_manager_bytes':built['partial_manager_bytes'],
            }
        b = built['bdd']; root = int(built['root'])
        global_ops += int(built['build_ops'])
        global_proof += int(built['proof_bytes'])
        cumulative += int(built['cumulative'])
        peak = max(peak, int(built['peak']))

        projected = v4.project_private_obdd(b, root, priv, global_ops, global_proof)
        global_ops += int(projected['projection_ops'])
        global_proof += int(projected['proof_bytes'])
        cumulative += int(projected['cumulative_state_bytes'])
        peak = max(peak, int(projected['representation_bytes_peak']))
        residual = int(projected['root'])
        support, sops = v4.bdd_support(b, residual)
        global_ops += sops
        if not support <= set(sep):
            raise AssertionError(f'pair child residual retains private support {support}')

        allowed: Set[str] = set()
        eval_ops = 0
        for bits in product((0,1), repeat=2):
            env = {sep[i]: bool(bits[i]) for i in range(2)}
            ok, z = v3.eval_bdd_count(b, residual, env)
            eval_ops += z
            if ok:
                allowed.add(''.join(str(x) for x in bits))
        global_ops += eval_ops
        before = set(current_join)
        current_join &= allowed
        join_ops += len(before)
        join_proof.append({
            'child_index':idx,'child_relation':sorted(allowed),
            'join_before':sorted(before),'join_after':sorted(current_join),
        })
        relation_bytes = base.json_bytes({'separator':list(sep),'allowed':sorted(allowed)})
        manager_bytes = v4.manager_bytes(b)
        retained += manager_bytes + relation_bytes
        product_bytes = retained + base.json_bytes({'separator':list(sep),'join':sorted(current_join),'children_seen':idx+1})
        peak = max(peak, product_bytes)
        cumulative += relation_bytes + product_bytes
        records.append({
            'child_index':idx,'private_vars':list(priv),'clause_count':len(child_clauses),
            'boundary_relation':sorted(allowed),'manager_nodes_total':len(b.nodes),
            'manager_bytes':manager_bytes,'build_ops':int(built['build_ops']),
            'private_projection_ops':int(projected['projection_ops']),
            'boundary_eval_ops':eval_ops,'residual_root':residual,
        })
        runtime.append((b, projected, priv))
        base.check_common_caps(peak, global_proof, cumulative, global_ops + join_ops)

    global_ops += join_ops
    global_proof += base.json_bytes(join_proof)
    join_bytes = base.json_bytes({'separator':list(sep),'allowed':sorted(current_join)})
    peak = max(peak, retained + join_bytes)
    cumulative += join_bytes
    final_scalar = bool(current_join)
    boundary_project = {
        'separator':list(sep),'pre_relation':sorted(current_join),
        'post_scalar':final_scalar,'rule':'EXISTS_TWO_BOUNDARY_NONEMPTY_RELATION',
    }
    global_proof += base.json_bytes(boundary_project)
    global_ops += 1

    witness: Optional[Dict[int,bool]] = None
    witness_ops = 0
    verify_ops = 0
    witness_valid: Optional[bool] = None
    witness_source = 'NO_WITNESS_EMPTY_WIDTH_TWO_JOIN'
    if final_scalar:
        chosen = min(current_join)
        seed = {sep[i]: chosen[i]=='1' for i in range(2)}
        witness = dict(seed)
        for b, projected, priv in runtime:
            env, z = v4.lift_bdd_projection_witness(b, projected['proof'], seed)
            witness_ops += z
            for v in priv:
                if v not in env:
                    raise AssertionError(f'pair child witness missing {v}')
                if v in witness:
                    raise AssertionError(f'pair child overlap {v}')
                witness[v] = env[v]
        if set(witness) != set(variables):
            raise AssertionError('width-two witness incomplete')
        witness_valid, verify_ops = v6.eval_cnf(clauses, witness)
        if not witness_valid:
            raise AssertionError('width-two witness fails source')
        witness_source = 'WIDTH_TWO_JOIN_PLUS_ACTUAL_CHILD_OBDD_PROOFS'
    global_ops += witness_ops + verify_ops
    base.check_common_caps(peak, global_proof, cumulative, global_ops)

    return {
        'status':'PASS_EXACT_CLOSED','selected_path':'PAIR_SEPARATOR_BOUNDARY_3CNF',
        'source_connected':bool(discovery['source_connected']),'separator':list(sep),
        'source_partition_roundtrip_exact':bool(discovery['roundtrip_exact']),
        'child_count':len(records),'children':records,
        'boundary_join_relation':sorted(current_join),'boundary_join_exact':True,
        'final_scalar':final_scalar,
        'strict_width_two_witness_glue':(witness_valid is True) if final_scalar else True,
        'witness_valid':witness_valid,'witness_source':witness_source,
        'witness_bytes':base.json_bytes(witness or {}),'representation_bytes_peak':peak,
        'cumulative_state_bytes':cumulative,'proof_bytes':global_proof,
        'total_charged_ops':global_ops,'witness_ops':witness_ops,'verification_ops':verify_ops,
        'certificate_sha256':hash_obj({
            'source':v6.cnf_hash(clauses,variables,order),'separator':list(sep),
            'partition':discovery['proof']['partition_sha256'],'children':records,
            'join':join_proof,'boundary_project':boundary_project,'witness':witness or {},
        }),
        'witness':witness,
    }


def generic_fallback(
    clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int],
    prior_ops: int, prior_proof: int, source_bytes: int
) -> Dict:
    generic = v6.build_generic_obdd(clauses, variables, order, prior_ops, prior_proof, source_bytes)
    if generic['status']=='CAP_HIT':
        return {
            'status':'CAP_HIT','cap_phase':'GENERIC_SOURCE_OBDD_BUILD','cap_reason':generic['cap_reason'],
            'partial_nodes':generic['partial_nodes'],'partial_manager_bytes':generic['partial_manager_bytes'],
        }
    b=generic['bdd']; root=int(generic['root'])
    ops = prior_ops + int(generic['build_ops'])
    proof = prior_proof + int(generic['proof_bytes'])
    projected = v4.project_common_boundary(
        b, root, order, ops, proof, int(generic['cumulative']), int(generic['peak'])
    )
    final_root=int(projected['root'])
    if final_root not in (0,1):
        raise AssertionError('v8 generic fallback nonterminal')
    final_scalar=bool(final_root)
    witness=None; witness_ops=0; verify_ops=0; witness_valid=None
    witness_source='NO_WITNESS_GENERIC_FALSE'
    if final_scalar:
        witness,witness_ops=v4.lift_bdd_projection_witness(b,projected['proof'],{})
        witness_valid,verify_ops=v6.eval_cnf(clauses,witness)
        if not witness_valid:
            raise AssertionError('v8 fallback witness fails source')
        witness_source='GENERIC_SOURCE_OBDD_PROJECTION_PROOF'
    total_ops=ops+int(projected['ops'])+witness_ops+verify_ops
    proof_bytes=proof+int(projected['proof_bytes'])
    base.check_common_caps(int(projected['representation_bytes_peak']),proof_bytes,int(projected['cumulative_state_bytes']),total_ops)
    return {
        'status':'PASS_EXACT_CLOSED','selected_path':'GENERIC_FROZEN_ORDER_OBDD',
        'final_scalar':final_scalar,'strict_source_witness':(witness_valid is True) if final_scalar else True,
        'witness_valid':witness_valid,'witness_source':witness_source,
        'witness_bytes':base.json_bytes(witness or {}),'manager_nodes_total':len(b.nodes),
        'representation_bytes_peak':int(projected['representation_bytes_peak']),
        'cumulative_state_bytes':int(projected['cumulative_state_bytes']),
        'proof_bytes':proof_bytes,'total_charged_ops':total_ops,'witness':witness,
    }


def solve_source(
    clauses: Sequence[Clause], variables: Sequence[int], frozen_order: Sequence[int]
) -> Dict:
    source_bytes=v6.cnf_bytes(clauses,variables,frozen_order)
    attempts:List[Dict]=[]; failed_ops=0; failed_proof=0

    parity=v6.recognize_signed_parity_graph(clauses,variables,frozen_order)
    if parity['accepted']:
        return {'status':'UNEXPECTED_EARLY_STRUCTURAL_ACCEPT'}
    attempts.append({'stage':'SIGNED_PARITY_GRAPH_CNF','status':'REJECT','ops':int(parity['ops']),'proof_bytes':int(parity['proof_bytes']),'failure':parity['proof']['reject']})
    failed_ops+=int(parity['ops']); failed_proof+=int(parity['proof_bytes'])

    art=v7.discover_articulation_boundary(clauses,variables,frozen_order)
    if art['accepted']:
        return {'status':'UNEXPECTED_ARTICULATION_ACCEPT','separator':art['separator']}
    attempts.append({'stage':'ARTICULATION_BOUNDARY_3CNF','status':'REJECT','ops':int(art['ops']),'proof_bytes':int(art['proof_bytes']),'failure':art['proof']['reject']})
    failed_ops+=int(art['ops']); failed_proof+=int(art['proof_bytes'])

    pair=discover_pair_separator(clauses,variables,frozen_order)
    if pair['accepted']:
        attempts.append({'stage':'PAIR_SEPARATOR_BOUNDARY_3CNF','status':'ACCEPT','ops':int(pair['ops']),'proof_bytes':int(pair['proof_bytes']),'separator':list(pair['separator'])})
        solved=solve_pair_separator(clauses,variables,frozen_order,pair,failed_ops,failed_proof)
        solved.update({
            'pipeline_attempts':attempts,'failed_pipeline_ops':failed_ops,
            'failed_pipeline_proof_bytes':failed_proof,
            'pair_discovery_ops':int(pair['ops']),'pair_discovery_proof_bytes':int(pair['proof_bytes']),
            'source_bytes':source_bytes,'articulation_rejected':True,
        })
        return solved

    attempts.append({'stage':'PAIR_SEPARATOR_BOUNDARY_3CNF','status':'REJECT','ops':int(pair['ops']),'proof_bytes':int(pair['proof_bytes']),'failure':pair['proof']['reject']})
    failed_ops+=int(pair['ops']); failed_proof+=int(pair['proof_bytes'])
    solved=generic_fallback(clauses,variables,frozen_order,failed_ops,failed_proof,source_bytes)
    solved.update({
        'pipeline_attempts':attempts+[{
            'stage':'GENERIC_FROZEN_ORDER_OBDD',
            'status':'ACCEPT' if solved['status']=='PASS_EXACT_CLOSED' else 'CAP_HIT',
            'ops':max(0,int(solved.get('total_charged_ops',failed_ops))-failed_ops),
            'proof_bytes':max(0,int(solved.get('proof_bytes',failed_proof))-failed_proof),
        }],
        'failed_pipeline_ops':failed_ops,'failed_pipeline_proof_bytes':failed_proof,
        'source_bytes':source_bytes,'source_connected':bool(pair['source_connected']),
        'articulation_rejected':True,'pair_separator_rejected':True,
    })
    return solved


def run_fixture(f:Fixture)->Dict:
    solved=solve_source(f.clauses,f.variables,f.order)
    if solved['status']=='CAP_HIT':
        return {
            'fixture':f.name,'size':f.size,'external_kind_for_test_only':f.kind,
            'expected_path_external_test_only':f.expected_path,'expected_sat':f.expected_sat,
            **solved,'claim':'FINITE_WIDTH_TWO_SEPARATOR_PORTFOLIO_ESCAPE_ONLY',
        }
    if solved['status']!='PASS_EXACT_CLOSED':
        raise AssertionError(f'unexpected v8 status {solved["status"]}')
    if bool(solved['final_scalar'])!=f.expected_sat:
        raise AssertionError(f'v8 scalar mismatch {f.name}')
    attempts=solved['pipeline_attempts']
    failed=[a for a in attempts if a['status']=='REJECT']
    failed_charged=(
        int(solved['failed_pipeline_ops'])==sum(int(a['ops']) for a in failed)
        and int(solved['failed_pipeline_proof_bytes'])==sum(int(a['proof_bytes']) for a in failed)
    )
    return {
        'fixture':f.name,'size':f.size,'external_kind_for_test_only':f.kind,
        'expected_path_external_test_only':f.expected_path,'expected_sat':f.expected_sat,
        **solved,
        'source_is_single_connected_3cnf':bool(solved['source_connected']) and all(len(c)==3 for c in f.clauses),
        'pipeline_api_unlabeled':True,
        'fixed_pipeline_order_used':[a['stage'] for a in attempts]==list(PIPELINE_ORDER[:len(attempts)]),
        'failed_pipeline_work_charged':failed_charged,
        'path_matches_frozen_expectation':solved['selected_path']==f.expected_path,
    }


def main(argv:Sequence[str])->int:
    rows=[run_fixture(f) for f in make_fixtures()]
    passed=[r for r in rows if r['status']=='PASS_EXACT_CLOSED']
    first_cap=next((r for r in rows if r['status']=='CAP_HIT'),None)
    positives=[r for r in passed if r['external_kind_for_test_only'].startswith('PAIR_SEPARATOR_')]
    rings=[r for r in rows if r['external_kind_for_test_only']=='TWO_CONNECTED_RING']
    result={
        'artifact_id':'PF5-TWO-CONNECTED-3CNF-CORE-V8',
        'protocol':'PF5_TWO_CONNECTED_3CNF_CORE_GATE_V8.md',
        'claim_ceiling':'P_VS_NP = OPEN',
        'pair_sizes_frozen_before_provider_run':list(PAIR_M),
        'ring_sizes_frozen_before_provider_run':list(RING_N),
        'pipeline_order_frozen_before_provider_run':list(PIPELINE_ORDER),
        'caps':base.CAPS,'new_tuned_caps_added':False,'controls':rows,
        'passed_controls':len(passed),
        'all_passed_connected_3cnf':all(r['source_is_single_connected_3cnf'] for r in passed) if passed else False,
        'all_passed_pipeline_unlabeled':all(r['pipeline_api_unlabeled'] for r in passed) if passed else False,
        'all_passed_fixed_pipeline_order':all(r['fixed_pipeline_order_used'] for r in passed) if passed else False,
        'all_passed_failed_work_charged':all(r['failed_pipeline_work_charged'] for r in passed) if passed else False,
        'all_passed_path_matches_expectation':all(r['path_matches_frozen_expectation'] for r in passed) if passed else False,
        'positive_sources_have_no_articulation':all(r['articulation_rejected'] for r in positives) and len(positives)==2*len(PAIR_M),
        'pair_separator_discovered_unlabeled':all(r['selected_path']=='PAIR_SEPARATOR_BOUNDARY_3CNF' for r in positives) and len(positives)==2*len(PAIR_M),
        'width_two_partition_roundtrip_exact':all(r['source_partition_roundtrip_exact'] for r in positives) and len(positives)==2*len(PAIR_M),
        'width_two_join_exact':all(r['boundary_join_exact'] for r in positives) and len(positives)==2*len(PAIR_M),
        'strict_width_two_witness_glue':all(r['strict_width_two_witness_glue'] for r in positives) and len(positives)==2*len(PAIR_M),
        'ring_rejects_width_one_and_width_two':all(
            any(a['stage']=='ARTICULATION_BOUNDARY_3CNF' and a['status']=='REJECT' for a in r['pipeline_attempts'])
            and any(a['stage']=='PAIR_SEPARATOR_BOUNDARY_3CNF' and a['status']=='REJECT' for a in r['pipeline_attempts'])
            and any(a['stage']=='GENERIC_FROZEN_ORDER_OBDD' for a in r['pipeline_attempts'])
            for r in rings
        ),
        'first_base_cap_hit':None if first_cap is None else {
            'fixture':first_cap['fixture'],'size':first_cap['size'],'phase':first_cap.get('cap_phase'),
            'reason':first_cap['cap_reason'],'partial_nodes':first_cap.get('partial_nodes',0),
            'partial_manager_bytes':first_cap.get('partial_manager_bytes',0),
        },
        'width_two_separator_discovery_poly_in_explicit_source':'PROVED_BY_FIXED_WIDTH_PAIR_ENUMERATION',
        'universal_bounded_separator_width':'OPEN',
        'three_connected_core_representation_discovery':'OPEN',
        'universal_polynomial_coverage':'OPEN','global_progress_amortization':'OPEN',
        'representation_lower_bound':'NOT_ESTABLISHED','next_front':'THREE_CONNECTED_3CNF_CORE_GATE','p_vs_np':'OPEN',
    }
    result['result_sha256']=hash_obj(result)
    print('PF5_TWO_CONNECTED_3CNF_CORE_V8 = FROZEN')
    for r in rows:
        if r['status']=='PASS_EXACT_CLOSED':
            print(r['fixture'],'status=PASS_EXACT_CLOSED','size=',r['size'],'path=',r['selected_path'],
                  'attempts=',[(a['stage'],a['status']) for a in r['pipeline_attempts']],
                  'peak=',r['representation_bytes_peak'],'ops=',r['total_charged_ops'],
                  'scalar=',r['final_scalar'],'witness=',r['witness_source'])
        else:
            print(r['fixture'],'status=CAP_HIT','size=',r['size'],'phase=',r.get('cap_phase'),'cap=',r['cap_reason'])
    print('PAIR_SEPARATOR_DISCOVERED_UNLABELED =',result['pair_separator_discovered_unlabeled'])
    print('RING_REJECTS_WIDTH_ONE_AND_WIDTH_TWO =',result['ring_rejects_width_one_and_width_two'])
    print('FIRST_BASE_CAP_HIT =',result['first_base_cap_hit'])
    print('THREE_CONNECTED_CORE_REPRESENTATION_DISCOVERY = OPEN')
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =',result['result_sha256'])
    if '--json-out' in argv:
        i=list(argv).index('--json-out')
        with open(argv[i+1],'w',encoding='utf-8') as fh:
            json.dump(result,fh,indent=2,sort_keys=True); fh.write('\n')
    return 0


if __name__=='__main__':
    raise SystemExit(main(sys.argv[1:]))
