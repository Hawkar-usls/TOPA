#!/usr/bin/env python3
"""PF5 non-affine connected-boundary v4.1.

Repairs NAB-001 by representing private equality roots as an exact COPY_GLUE
wrapper around the compact non-affine boundary OBDD. v4 widths, predicates,
common JOIN language and all caps remain unchanged.
"""

from __future__ import annotations

from hashlib import sha256
import json
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import pf5_boundary_coverage_matrix_v0 as base
import pf5_connected_boundary_adhesion_v3 as v3
import pf5_connected_boundary_adhesion_v3_1 as v31
import pf5_non_affine_connected_boundary_v4 as v4


WIDTHS = v4.WIDTHS


def canon_hash(obj) -> str:
    return sha256(base.canon_json(obj).encode()).hexdigest()


def build_boundary_predicate_bdd(c: v4.V4Control, b: base.BDD) -> Tuple[int, Dict, int]:
    memo: Dict[Tuple[int, int], int] = {}
    calls = 0
    transitions = 0

    def rec(i: int, state: int) -> int:
        nonlocal calls, transitions
        calls += 1
        key = (i, state)
        if key in memo:
            return memo[key]
        if i == c.k:
            out = 1 if v4.right_accept(c.right_kind, state) else 0
            memo[key] = out
            return out
        lo_state = v4.right_update(c.right_kind, state, 0)
        hi_state = v4.right_update(c.right_kind, state, 1)
        lo = rec(i + 1, lo_state)
        hi = rec(i + 1, hi_state)
        transitions += 2
        out = b.mk(c.boundary[i], lo, hi)
        memo[key] = out
        return out

    root = rec(0, 0)
    proof = {
        'constructor': 'FROZEN_BOUNDARY_PREDICATE_AUTOMATON',
        'kind': c.right_kind,
        'order': list(c.boundary),
        'states': len(memo),
        'calls': calls,
        'transitions': transitions,
        'root': root,
        'manager_sha256': canon_hash(v4.manager_payload(b)),
    }
    return root, proof, calls + transitions


def pairs_payload(pairs: Sequence[Tuple[int, int]]) -> List[List[int]]:
    return [[int(a), int(b)] for a, b in sorted(pairs)]


def copy_glue_state_bytes(b: base.BDD, pairs: Sequence[Tuple[int, int]]) -> int:
    return base.json_bytes({
        'boundary_manager': v4.manager_payload(b),
        'copy_pairs': pairs_payload(pairs),
    })


def project_copy_glue(
    b: base.BDD,
    root: int,
    pairs: Sequence[Tuple[int, int]],
    private_order: Sequence[int],
    prior_ops: int,
    prior_proof_bytes: int,
) -> Dict:
    current = list(sorted(pairs))
    proof: List[Dict] = []
    ops = 0
    peak = copy_glue_state_bytes(b, current)
    cumulative = peak

    for x in private_order:
        before = list(current)
        found = None
        for i, pair in enumerate(current):
            ops += 1
            if pair[0] == x:
                found = (i, pair)
                break
        if found is None:
            raise AssertionError(f'COPY_GLUE missing private root {x}')
        i, pair = found
        del current[i]
        rec = {
            'x': int(x),
            'mapped_boundary': int(pair[1]),
            'before_sha256': canon_hash(pairs_payload(before)),
            'after_sha256': canon_hash(pairs_payload(current)),
            'before_count': len(before),
            'after_count': len(current),
            'boundary_root_unchanged': int(root),
        }
        proof.append(rec)
        ops += 1
        sb = copy_glue_state_bytes(b, current)
        peak = max(peak, sb)
        cumulative += sb
        base.check_common_caps(
            peak,
            prior_proof_bytes + base.json_bytes(proof),
            cumulative,
            prior_ops + ops,
        )

    return {
        'root': root,
        'remaining_pairs': current,
        'proof': proof,
        'ops': ops,
        'proof_bytes': base.json_bytes(proof),
        'representation_bytes_peak': peak,
        'cumulative_state_bytes': cumulative,
        'exact': len(current) == 0 and len(proof) == len(private_order),
    }


def lift_copy_glue(proof: Sequence[Dict], boundary_env: Dict[int, bool]) -> Tuple[Dict[int, bool], int]:
    env = dict(boundary_env)
    ops = 0
    for rec in reversed(proof):
        x = int(rec['x'])
        bvar = int(rec['mapped_boundary'])
        ops += 1
        if bvar not in env:
            raise AssertionError(f'COPY_GLUE witness missing boundary root {bvar}')
        env[x] = bool(env[bvar])
    return env, ops


def run_control(c: v4.V4Control) -> Dict:
    B, A, C = c.boundary, c.left_private, c.right_private
    connected, connectivity_ops = v4.connectivity_check(c)
    assert connected

    phase = 'LEFT_AFFINE_PRIVATE'
    right_bdd: Optional[base.BDD] = None
    common: Optional[base.BDD] = None
    partial: Dict[str, object] = {}

    try:
        left0, left_build_ops = v31.build_affine_wing(B, A, False)
        left = v31.project_private(left0, A, left_build_ops + connectivity_ops)
        left_replay, left_replay_ops = v31.verify_projection_replay(
            left0, A, left['proof'], left['rows']
        )
        if not left_replay:
            raise AssertionError('left affine projection replay failed')

        phase = 'RIGHT_BOUNDARY_OBDD_CONSTRUCT'
        right_bdd = base.BDD(B)
        before = right_bdd.ops
        right_root, right_constructor_proof, right_constructor_internal = build_boundary_predicate_bdd(c, right_bdd)
        right_constructor_ops = (right_bdd.ops - before) + right_constructor_internal
        right_constructor_proof_bytes = base.json_bytes(right_constructor_proof)

        copy_pairs = list(zip(C, B))
        copy_map_build_ops = len(copy_pairs)
        initial_copy_bytes = copy_glue_state_bytes(right_bdd, copy_pairs)
        build_ops = left_build_ops + connectivity_ops + right_constructor_ops + copy_map_build_ops
        base.check_common_caps(
            max(int(left['representation_bytes_peak']), initial_copy_bytes),
            int(left['proof_bytes']) + right_constructor_proof_bytes,
            int(left['cumulative_state_bytes']) + initial_copy_bytes,
            build_ops + int(left['projection_ops']) + left_replay_ops,
        )

        phase = 'RIGHT_COPY_GLUE_PRIVATE_PROJECT'
        prior_ops = build_ops + int(left['projection_ops']) + left_replay_ops
        copy_project = project_copy_glue(
            right_bdd,
            right_root,
            copy_pairs,
            C,
            prior_ops,
            int(left['proof_bytes']) + right_constructor_proof_bytes,
        )
        if not copy_project['exact']:
            raise AssertionError('COPY_GLUE private projection did not discharge every pair')

        right_check = v4.verify_right_residual(c, right_bdd, int(copy_project['root']))
        if not right_check['exact']:
            raise AssertionError('right boundary OBDD is not exact frozen predicate')
        if not right_check['non_affine']:
            raise AssertionError('right boundary predicate unexpectedly affine')

        phase = 'AFFINE_TO_COMMON_OBDD'
        common = base.BDD(B)
        conversion = v4.compile_affine_to_common(left['rows'], B, common)
        common_after_conversion = v4.manager_bytes(common)
        cumulative = (
            int(left['cumulative_state_bytes'])
            + int(copy_project['cumulative_state_bytes'])
            + int(conversion['residual_cumulative_state_bytes'])
            + common_after_conversion
        )
        peak = max(
            int(left['representation_bytes_peak']),
            int(copy_project['representation_bytes_peak']),
            int(conversion['residual_peak_state_bytes']),
            common_after_conversion,
        )
        proof_bytes = (
            int(left['proof_bytes']) + right_constructor_proof_bytes
            + int(copy_project['proof_bytes']) + int(conversion['proof_bytes'])
        )
        ops_so_far = (
            build_ops + int(left['projection_ops']) + left_replay_ops
            + int(copy_project['ops']) + int(right_check['ops'])
            + int(conversion['ops'])
        )
        base.check_common_caps(peak, proof_bytes, cumulative, ops_so_far)

        phase = 'COPY_RIGHT_TO_COMMON_OBDD'
        copied = v4.copy_residual_to_common(
            right_bdd, int(copy_project['root']), common, B
        )
        sb = v4.manager_bytes(common)
        cumulative += sb
        peak = max(peak, sb)
        proof_bytes += int(copied['proof_bytes'])
        ops_so_far += int(copied['ops'])
        base.check_common_caps(peak, proof_bytes, cumulative, ops_so_far)

        phase = 'HETEROGENEOUS_JOIN'
        before_join = common.ops
        join_root = v4.apply_and(common, int(conversion['root']), int(copied['root']))
        join_ops = common.ops - before_join
        sb = v4.manager_bytes(common)
        cumulative += sb
        peak = max(peak, sb)
        join_proof = {
            'operator': 'COMMON_OBDD_APPLY_AND',
            'left_root': int(conversion['root']),
            'right_root': int(copied['root']),
            'join_root': int(join_root),
            'manager_sha256': canon_hash(v4.manager_payload(common)),
        }
        proof_bytes += base.json_bytes(join_proof)
        ops_so_far += join_ops
        base.check_common_caps(peak, proof_bytes, cumulative, ops_so_far)

        phase = 'HETEROGENEOUS_SEMANTIC_VERIFY'
        semantic = v4.verify_common_semantics(
            c,
            left['rows'],
            right_bdd,
            int(copy_project['root']),
            common,
            int(conversion['root']),
            int(copied['root']),
            int(join_root),
        )
        if not semantic['affine_conversion_exact']:
            raise AssertionError('affine conversion mismatch')
        if not semantic['right_copy_exact']:
            raise AssertionError('right common-copy mismatch')
        if not semantic['join_exact']:
            raise AssertionError('heterogeneous JOIN mismatch')
        if c.expected_sat and not semantic['join_non_affine']:
            raise AssertionError('SAT joined relation unexpectedly affine')
        ops_so_far += int(semantic['ops'])
        base.check_common_caps(peak, proof_bytes, cumulative, ops_so_far)

        phase = 'SHARED_BOUNDARY_PROJECT'
        shared = v4.project_common_boundary(
            common,
            int(join_root),
            B,
            ops_so_far,
            proof_bytes,
            cumulative,
            peak,
        )
        final_root = int(shared['root'])
        if final_root not in (0, 1):
            raise AssertionError('all shared roots projected but common OBDD nonterminal')
        final_scalar = bool(final_root)
        if final_scalar != c.expected_sat:
            raise AssertionError('terminal scalar disagrees with frozen control')

        proof_bytes += int(shared['proof_bytes'])
        peak = int(shared['representation_bytes_peak'])
        cumulative = int(shared['cumulative_state_bytes'])
        shared_projection_ops = int(shared['ops'])

        witness: Optional[Dict[int, bool]] = None
        witness_valid: Optional[bool] = None
        witness_ops = 0
        final_verification_ops = 0
        witness_source = 'NO_WITNESS_COMMON_OBDD_FALSE'

        if final_scalar:
            boundary_env, bo = v4.lift_bdd_projection_witness(common, shared['proof'], {})
            witness_ops += bo
            if set(boundary_env) != set(B):
                raise AssertionError('shared boundary witness incomplete')
            join_ok, jo = v3.eval_bdd_count(common, int(join_root), boundary_env)
            final_verification_ops += jo
            if not join_ok:
                raise AssertionError('reconstructed shared witness misses JOIN')

            right_env, ro = lift_copy_glue(copy_project['proof'], boundary_env)
            witness_ops += ro
            left_env, lo = v31.lift_private(left['proof'], boundary_env)
            witness_ops += lo

            witness = dict(boundary_env)
            for v in A:
                if v not in left_env:
                    raise AssertionError(f'left witness missing {v}')
                witness[v] = left_env[v]
            for v in C:
                if v not in right_env:
                    raise AssertionError(f'COPY_GLUE witness missing {v}')
                if v in witness:
                    raise AssertionError(f'witness overlap {v}')
                witness[v] = right_env[v]
            if set(witness) != set(range(1, 3 * c.k + 1)):
                raise AssertionError('complete v4.1 witness union failed')

            lv, lvo = v31.eval_system(left0, witness)
            rv, rvo = v4.eval_right_source(c, witness)
            final_verification_ops += lvo + rvo
            witness_valid = lv and rv
            witness_source = 'COMMON_J_OBDD_PROOF_PLUS_COPY_GLUE_PROOF_PLUS_LEFT_AFFINE_PIVOTS'
            if not witness_valid:
                raise AssertionError('strict v4.1 source witness verification failed')

        total_ops = ops_so_far + shared_projection_ops + witness_ops + final_verification_ops
        witness_bytes = base.json_bytes(witness or {})
        base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

        expected_left_models = 1 << (c.k - 1)
        expected_right_models = (1 << c.k) - 1 if c.right_kind == 'OR' else c.k
        expected_join_models = (1 << (c.k - 1)) - 1 if c.expected_sat else 0

        cert = {
            'control': c.name,
            'left_affine': v31.system_hash(left['rows']),
            'right_constructor': right_constructor_proof,
            'copy_glue': copy_project['proof'],
            'affine_conversion': conversion['proof'],
            'right_copy': copied['proof'],
            'join': join_proof,
            'shared_projection': shared['proof'],
            'witness_sha256': canon_hash(witness or {}),
        }

        return {
            'control': c.name,
            'k': c.k,
            'right_kind': c.right_kind,
            'expected_sat': c.expected_sat,
            'status': 'PASS_EXACT_CLOSED',
            'cap_phase': None,
            'cap_reason': None,
            'connected': connected,
            'left_language': 'AFFINE_GF2',
            'right_language': 'COPY_GLUE_OF_BOUNDARY_OBDD',
            'join_language': 'COMMON_FROZEN_ORDER_OBDD',
            'boundary_language_discovery': 'SUPPLIED_FROZEN_TYPES_ONLY',
            'copy_glue_project_exact': copy_project['exact'],
            'right_nonaffine_private_project_exact': right_check['exact'],
            'right_boundary_non_affine': right_check['non_affine'],
            'affine_to_obdd_conversion_exact': semantic['affine_conversion_exact'],
            'right_obdd_copy_exact': semantic['right_copy_exact'],
            'heterogeneous_join_exact': semantic['join_exact'],
            'joined_boundary_non_affine': semantic['join_non_affine'],
            'repeated_shared_project_exact': final_scalar == c.expected_sat,
            'strict_heterogeneous_witness_glue_exact': (witness_valid is True) if final_scalar else True,
            'final_scalar': final_scalar,
            'witness_valid': witness_valid,
            'witness_source': witness_source,
            'witness_bytes': witness_bytes,
            'left_models': int(semantic['left_models']),
            'right_models': int(semantic['right_models']),
            'join_models': int(semantic['join_models']),
            'expected_left_models': expected_left_models,
            'expected_right_models': expected_right_models,
            'expected_join_models': expected_join_models,
            'right_boundary_manager_nodes_total': len(right_bdd.nodes),
            'common_manager_nodes_total': len(common.nodes),
            'representation_bytes_peak': peak,
            'cumulative_state_bytes': cumulative,
            'proof_bytes': proof_bytes,
            'build_ops': build_ops,
            'copy_glue_projection_ops': int(copy_project['ops']),
            'left_private_projection_ops': int(left['projection_ops']),
            'affine_to_obdd_ops': int(conversion['ops']),
            'right_copy_ops': int(copied['ops']),
            'join_ops': join_ops,
            'shared_projection_ops': shared_projection_ops,
            'semantic_verification_ops': int(right_check['ops']) + int(semantic['ops']) + left_replay_ops,
            'witness_ops': witness_ops,
            'final_verification_ops': final_verification_ops,
            'total_charged_ops': total_ops,
            'certificate_sha256': canon_hash(cert),
            'witness': witness,
        }

    except base.CapHit as e:
        partial.update({
            'right_boundary_manager_nodes_total': 0 if right_bdd is None else len(right_bdd.nodes),
            'right_boundary_manager_ops': 0 if right_bdd is None else right_bdd.ops,
            'right_boundary_manager_bytes': 0 if right_bdd is None else v4.manager_bytes(right_bdd),
            'common_manager_nodes_total': 0 if common is None else len(common.nodes),
            'common_manager_ops': 0 if common is None else common.ops,
            'common_manager_bytes': 0 if common is None else v4.manager_bytes(common),
        })
        return {
            'control': c.name,
            'k': c.k,
            'right_kind': c.right_kind,
            'expected_sat': c.expected_sat,
            'status': 'CAP_HIT',
            'cap_phase': phase,
            'cap_reason': str(e),
            'connected': connected,
            'left_language': 'AFFINE_GF2',
            'right_language': 'COPY_GLUE_OF_BOUNDARY_OBDD',
            'join_language': 'COMMON_FROZEN_ORDER_OBDD',
            'boundary_language_discovery': 'SUPPLIED_FROZEN_TYPES_ONLY',
            'partial': partial,
            'claim': 'FINITE_HETEROGENEOUS_REPRESENTATION_ESCAPE_ONLY',
        }


def main(argv: Sequence[str]) -> int:
    rows = [run_control(c) for c in v4.controls()]
    passed = [r for r in rows if r['status'] == 'PASS_EXACT_CLOSED']
    first_cap = next((r for r in rows if r['status'] == 'CAP_HIT'), None)
    initial_v4_passed_controls = 9

    result = {
        'artifact_id': 'PF5-NON-AFFINE-CONNECTED-BOUNDARY-V4.1-COPY-GLUE',
        'repair_of': 'NAB-001-PRIVATE-COPY-GLUE-OBDD-ACCUMULATION',
        'claim_ceiling': 'P_VS_NP = OPEN',
        'widths_frozen_before_v4_provider_run': list(WIDTHS),
        'widths_changed_from_v4': False,
        'caps': base.CAPS,
        'caps_changed_from_v4': False,
        'common_join_language_changed_from_v4': False,
        'right_private_wrapper': 'PROOF_CARRYING_COPY_GLUE',
        'controls': rows,
        'passed_controls': len(passed),
        'initial_v4_passed_controls': initial_v4_passed_controls,
        'all_passed_controls_exact': all(
            r['copy_glue_project_exact']
            and r['right_nonaffine_private_project_exact']
            and r['right_boundary_non_affine']
            and r['affine_to_obdd_conversion_exact']
            and r['right_obdd_copy_exact']
            and r['heterogeneous_join_exact']
            and r['repeated_shared_project_exact']
            and r['strict_heterogeneous_witness_glue_exact']
            for r in passed
        ) if passed else False,
        'all_sat_joined_boundaries_non_affine': all(
            r['joined_boundary_non_affine'] for r in passed if r['expected_sat']
        ) if any(r['expected_sat'] for r in passed) else False,
        'first_base_cap_hit': None if first_cap is None else {
            'control': first_cap['control'],
            'k': first_cap['k'],
            'kind': first_cap['right_kind'],
            'phase': first_cap['cap_phase'],
            'reason': first_cap['cap_reason'],
            'partial': first_cap.get('partial', {}),
        },
        'nab001_repaired': (
            len(passed) > initial_v4_passed_controls
            and (first_cap is None or first_cap['cap_phase'] != 'RIGHT_COPY_GLUE_PRIVATE_PROJECT')
        ),
        'boundary_language_discovery': 'SUPPLIED_FROZEN_TYPES_ONLY',
        'universal_cheap_language_selection': 'OPEN',
        'universal_cheap_cross_language_conversion': 'OPEN',
        'universal_polynomial_coverage': 'OPEN',
        'global_progress_amortization': 'OPEN',
        'representation_lower_bound': 'NOT_ESTABLISHED',
        'next_front_if_full_pass': 'BOUNDARY_LANGUAGE_DISCOVERY_GATE',
        'p_vs_np': 'OPEN',
    }
    result['result_sha256'] = canon_hash(result)

    print('PF5_NON_AFFINE_CONNECTED_BOUNDARY_V4_1 = FROZEN')
    for r in rows:
        if r['status'] == 'PASS_EXACT_CLOSED':
            print(
                r['control'],
                'status=PASS_EXACT_CLOSED',
                'k=', r['k'],
                'right=', r['right_kind'],
                'models=', (r['left_models'], r['right_models'], r['join_models']),
                'right_nodes=', r['right_boundary_manager_nodes_total'],
                'common_nodes=', r['common_manager_nodes_total'],
                'peak=', r['representation_bytes_peak'],
                'ops=', r['total_charged_ops'],
                'witness=', r['witness_source'],
            )
        else:
            print(
                r['control'],
                'status=CAP_HIT',
                'k=', r['k'],
                'right=', r['right_kind'],
                'phase=', r['cap_phase'],
                'cap=', r['cap_reason'],
                'partial=', r.get('partial', {}),
            )
    print('NAB_001_REPAIRED =', result['nab001_repaired'])
    print('PASSED_CONTROLS =', result['passed_controls'])
    print('FIRST_BASE_CAP_HIT =', result['first_base_cap_hit'])
    print('BOUNDARY_LANGUAGE_DISCOVERY = SUPPLIED_FROZEN_TYPES_ONLY')
    print('UNIVERSAL_CHEAP_LANGUAGE_SELECTION = OPEN')
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =', result['result_sha256'])

    if '--json-out' in argv:
        i = list(argv).index('--json-out')
        with open(argv[i + 1], 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
