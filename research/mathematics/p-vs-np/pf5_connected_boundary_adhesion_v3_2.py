#!/usr/bin/env python3
"""PF5 connected-boundary adhesion v3.2.

Repairs ADH-002 by keeping the shared boundary itself as an exact affine GF(2)
state. JOIN is conjunction + deterministic RREF; shared existential projection
is pivot/XOR/remove + RREF. Widths, controls, private representation and caps
remain unchanged.
"""

from __future__ import annotations

from hashlib import sha256
from itertools import product
import json
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pf5_boundary_coverage_matrix_v0 as base
import pf5_connected_boundary_adhesion_v3 as v3
import pf5_connected_boundary_adhesion_v3_1 as v31


Eq = v31.Eq
WIDTHS = v3.WIDTHS


def lowest_var(mask: int) -> int:
    if mask == 0:
        return 10**9
    return (mask & -mask).bit_length()


def rref(rows: Sequence[Eq], vars_order: Sequence[int]) -> Tuple[List[Eq], List[Dict], int]:
    # Deterministic Gauss-Jordan elimination over GF(2).
    work = [Eq(r.mask, r.rhs) for r in rows]
    work.sort(key=lambda r: (r.mask, r.rhs))
    transcript: List[Dict] = []
    ops = len(work)
    pivot_row = 0

    for x in vars_order:
        xb = v31.bit(x)
        idx = None
        for i in range(pivot_row, len(work)):
            ops += 1
            if work[i].mask & xb:
                idx = i
                break
        if idx is None:
            continue
        if idx != pivot_row:
            work[pivot_row], work[idx] = work[idx], work[pivot_row]
            ops += 1

        pivot_before = work[pivot_row]
        eliminated = 0
        for i in range(len(work)):
            if i == pivot_row:
                continue
            ops += 1
            if work[i].mask & xb:
                work[i] = Eq(
                    work[i].mask ^ work[pivot_row].mask,
                    work[i].rhs ^ work[pivot_row].rhs,
                )
                eliminated += 1
                ops += 1
        transcript.append({
            'pivot_var': x,
            'pivot_before': pivot_before.payload(),
            'eliminated_rows': eliminated,
        })
        pivot_row += 1

    # Canonical cleanup. Any 0=1 row makes the whole affine state FALSE.
    for r in work:
        ops += 1
        if r.mask == 0 and r.rhs == 1:
            return [Eq(0, 1)], transcript, ops
    clean = [r for r in work if r.mask != 0]
    uniq = {(r.mask, r.rhs) for r in clean}
    out = [Eq(m, rhs) for m, rhs in sorted(uniq, key=lambda z: (lowest_var(z[0]), z[0], z[1]))]
    return out, transcript, ops + len(out)


def join_affine(left: Sequence[Eq], right: Sequence[Eq], boundary: Sequence[int]) -> Tuple[List[Eq], Dict, int]:
    concatenated = list(left) + list(right)
    out, transcript, ops = rref(concatenated, boundary)
    proof = {
        'operator': 'J_B',
        'left_sha256': v31.system_hash(left),
        'right_sha256': v31.system_hash(right),
        'concat_sha256': v31.system_hash(v31.canon_system(concatenated)),
        'rref_transcript': transcript,
        'post_sha256': v31.system_hash(out),
        'post_rows': len(out),
    }
    return out, proof, ops + len(concatenated)


def project_boundary_var(rows: Sequence[Eq], x: int, remaining_order: Sequence[int]) -> Tuple[List[Eq], Dict, int]:
    xb = v31.bit(x)
    containing: List[Eq] = []
    keep: List[Eq] = []
    ops = 0
    for r in rows:
        ops += 1
        (containing if r.mask & xb else keep).append(r)

    pivot: Optional[Eq] = None
    xor_count = 0
    raw = list(keep)
    if containing:
        pivot = min(containing, key=lambda r: (r.mask.bit_count(), r.mask, r.rhs))
        skipped = False
        for r in containing:
            if not skipped and r == pivot:
                skipped = True
                continue
            raw.append(Eq(r.mask ^ pivot.mask, r.rhs ^ pivot.rhs))
            xor_count += 1
            ops += 1

    post, rref_transcript, rref_ops = rref(raw, remaining_order)
    ops += rref_ops
    proof = {
        'x': x,
        'pivot': None if pivot is None else pivot.payload(),
        'before_sha256': v31.system_hash(rows),
        'after_sha256': v31.system_hash(post),
        'xor_count': xor_count,
        'rref_transcript': rref_transcript,
        'before_rows': len(rows),
        'after_rows': len(post),
    }
    return post, proof, ops


def project_boundary(rows: Sequence[Eq], boundary: Sequence[int], already_charged_ops: int, already_proof_bytes: int, already_cumulative: int, already_peak: int) -> Dict:
    current = list(rows)
    proof: List[Dict] = []
    ops = 0
    cumulative = already_cumulative + v31.system_bytes(current)
    peak = max(already_peak, v31.system_bytes(current))

    for i, x in enumerate(boundary):
        current, rec, z = project_boundary_var(current, x, boundary[i+1:])
        ops += z
        proof.append(rec)
        sb = v31.system_bytes(current)
        cumulative += sb
        peak = max(peak, sb)
        base.check_common_caps(
            peak,
            already_proof_bytes + base.json_bytes(proof),
            cumulative,
            already_charged_ops + ops,
        )

    return {
        'rows': current,
        'proof': proof,
        'projection_ops': ops,
        'representation_bytes_peak': peak,
        'cumulative_state_bytes': cumulative,
        'proof_bytes': base.json_bytes(proof),
    }


def is_contradiction(rows: Sequence[Eq]) -> bool:
    return len(rows) == 1 and rows[0].mask == 0 and rows[0].rhs == 1


def lift_boundary(proof: Sequence[Dict]) -> Tuple[Dict[int, bool], int]:
    env: Dict[int, bool] = {}
    ops = 0
    for rec in reversed(proof):
        x = int(rec['x'])
        pivot = rec['pivot']
        if pivot is None:
            env[x] = False
            ops += 1
        else:
            val, z = v31.solve_pivot(tuple(pivot), x, env)
            env[x] = val
            ops += z
    return env, ops


def verify_join_semantics(c: v3.AdhesionControl, left: Sequence[Eq], right: Sequence[Eq], joined: Sequence[Eq]) -> Tuple[bool, int, int, int, int]:
    left_count = right_count = join_count = 0
    ops = 0
    ok = True
    for bits in product((0, 1), repeat=c.k):
        env = {v: bool(z) for v, z in zip(c.boundary, bits)}
        lv, lo = v31.eval_system(left, env)
        rv, ro = v31.eval_system(right, env)
        jv, jo = v31.eval_system(joined, env)
        ops += lo + ro + jo + c.k
        parity = sum(bits) & 1
        exp_l = parity == 0
        exp_r = parity == int(c.right_target)
        exp_j = exp_l and exp_r
        if lv:
            left_count += 1
        if rv:
            right_count += 1
        if jv:
            join_count += 1
        if (lv, rv, jv) != (exp_l, exp_r, exp_j):
            ok = False
    return ok, ops, left_count, right_count, join_count


def run_control(c: v3.AdhesionControl) -> Dict:
    B, A, C = c.boundary, c.left_private, c.right_private
    connected, connectivity_ops = v3.connectivity_check(c)
    assert connected

    left0, left_build = v31.build_affine_wing(B, A, False)
    right0, right_build = v31.build_affine_wing(B, C, c.right_target)
    build_ops = left_build + right_build + connectivity_ops
    phase = 'PRIVATE_PROJECTION'

    try:
        left = v31.project_private(left0, A, build_ops)
        right = v31.project_private(right0, C, build_ops + int(left['projection_ops']))
        replay_l, replay_l_ops = v31.verify_projection_replay(left0, A, left['proof'], left['rows'])
        replay_r, replay_r_ops = v31.verify_projection_replay(right0, C, right['proof'], right['rows'])
        if not replay_l or not replay_r:
            raise AssertionError('private affine proof replay failed')

        private_ops = int(left['projection_ops']) + int(right['projection_ops'])
        private_proof_bytes = int(left['proof_bytes']) + int(right['proof_bytes'])
        private_cumulative = int(left['cumulative_state_bytes']) + int(right['cumulative_state_bytes'])
        private_peak = int(left['representation_bytes_peak']) + int(right['representation_bytes_peak'])
        verification_ops = replay_l_ops + replay_r_ops

        phase = 'COMPRESSED_ADHESION_JOIN'
        joined, join_proof, join_ops = join_affine(left['rows'], right['rows'], B)
        join_state_bytes = v31.system_bytes(joined) + v31.system_bytes(left['rows']) + v31.system_bytes(right['rows'])
        peak = max(private_peak, join_state_bytes)
        cumulative = private_cumulative + join_state_bytes
        proof_bytes_before_boundary = private_proof_bytes + base.json_bytes(join_proof)
        total_ops_before_boundary = build_ops + private_ops + verification_ops + join_ops
        base.check_common_caps(peak, proof_bytes_before_boundary, cumulative, total_ops_before_boundary)

        semantic_ok, semantic_ops, left_count, right_count, join_count = verify_join_semantics(c, left['rows'], right['rows'], joined)
        verification_ops += semantic_ops
        if not semantic_ok:
            raise AssertionError('compressed affine join semantic verification failed')

        phase = 'COMPRESSED_BOUNDARY_PROJECTION'
        bp = project_boundary(
            joined,
            B,
            total_ops_before_boundary + semantic_ops,
            proof_bytes_before_boundary,
            cumulative,
            peak,
        )
        final = bp['rows']
        final_scalar = not is_contradiction(final)
        if final_scalar and final:
            raise AssertionError('all boundary variables projected but affine state remained constrained')
        if not final_scalar and not is_contradiction(final):
            raise AssertionError('UNSAT terminal is not canonical contradiction')

        proof_bytes = proof_bytes_before_boundary + int(bp['proof_bytes'])
        peak = int(bp['representation_bytes_peak'])
        cumulative = int(bp['cumulative_state_bytes'])
        boundary_projection_ops = int(bp['projection_ops'])

        witness: Optional[Dict[int, bool]] = None
        witness_valid: Optional[bool] = None
        witness_ops = 0
        witness_source = 'NO_WITNESS_AFFINE_CONTRADICTION'

        if final_scalar:
            boundary_env, bo = lift_boundary(bp['proof'])
            witness_ops += bo
            j_ok, j_ops = v31.eval_system(joined, boundary_env)
            verification_ops += j_ops
            if not j_ok:
                raise AssertionError('reconstructed boundary witness does not satisfy compressed join')

            left_env, lo = v31.lift_private(left['proof'], boundary_env)
            right_env, ro = v31.lift_private(right['proof'], boundary_env)
            witness_ops += lo + ro
            witness = dict(boundary_env)
            for v in A:
                witness[v] = left_env[v]
            for v in C:
                if v in witness:
                    raise AssertionError('private overlap')
                witness[v] = right_env[v]
            if set(witness) != set(range(1, 3*c.k + 1)):
                raise AssertionError('strict compressed witness union incomplete')
            lv, lvo = v31.eval_system(left0, witness)
            rv, rvo = v31.eval_system(right0, witness)
            verification_ops += lvo + rvo
            witness_valid = lv and rv
            witness_source = 'COMPRESSED_J_PIVOTS_PLUS_PRIVATE_AFFINE_PIVOTS'
            if not witness_valid:
                raise AssertionError('strict compressed witness verification failed')

        total_ops = build_ops + private_ops + join_ops + boundary_projection_ops + verification_ops + witness_ops
        witness_bytes = base.json_bytes(witness or {})
        base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

        expected_each = 1 << (c.k - 1)
        return {
            'control': c.name,
            'k': c.k,
            'expected_sat': c.expected_sat,
            'status': 'PASS_EXACT_CLOSED',
            'cap_phase': None,
            'cap_reason': None,
            'connected': connected,
            'inner_representation': 'AFFINE_GF2',
            'boundary_representation': 'AFFINE_GF2_RREF',
            'left_boundary_models_reference': left_count,
            'right_boundary_models_reference': right_count,
            'expected_each_wing_models': expected_each,
            'join_models_reference': join_count,
            'compressed_left_rows': len(left['rows']),
            'compressed_right_rows': len(right['rows']),
            'compressed_join_rows': len(joined),
            'compressed_join_bytes': v31.system_bytes(joined),
            'final_scalar': final_scalar,
            'private_projection_exact': replay_l and replay_r,
            'compressed_join_exact': semantic_ok,
            'compressed_boundary_projection_exact': final_scalar == c.expected_sat,
            'strict_witness_glue_exact': (witness_valid is True) if final_scalar else True,
            'witness_valid': witness_valid,
            'witness_source': witness_source,
            'witness_bytes': witness_bytes,
            'representation_bytes_peak': peak,
            'cumulative_state_bytes': cumulative,
            'proof_bytes': proof_bytes,
            'build_ops': build_ops,
            'private_projection_ops': private_ops,
            'join_ops': join_ops,
            'boundary_projection_ops': boundary_projection_ops,
            'verification_ops': verification_ops,
            'witness_ops': witness_ops,
            'total_charged_ops': total_ops,
            'join_proof_sha256': v3.canon_hash(join_proof),
            'certificate_sha256': v3.canon_hash({
                'control': c.name,
                'left': v31.system_hash(left['rows']),
                'right': v31.system_hash(right['rows']),
                'join': v31.system_hash(joined),
                'join_proof': join_proof,
                'boundary_proof': bp['proof'],
                'witness': witness or {},
            }),
            'witness': witness,
        }

    except base.CapHit as e:
        return {
            'control': c.name,
            'k': c.k,
            'expected_sat': c.expected_sat,
            'status': 'CAP_HIT',
            'cap_phase': phase,
            'cap_reason': str(e),
            'connected': connected,
            'inner_representation': 'AFFINE_GF2',
            'boundary_representation': 'AFFINE_GF2_RREF',
            'claim': 'FINITE_COMPRESSED_AFFINE_REPRESENTATION_CAP_ONLY',
        }


def main(argv: Sequence[str]) -> int:
    rows = [run_control(c) for c in v3.controls()]
    result = {
        'artifact_id': 'PF5-CONNECTED-BOUNDARY-ADHESION-V3.2-COMPRESSED-AFFINE-JOIN',
        'repair_of': 'ADH-002-EXPLICIT-BOUNDARY-TABLE-ESCAPE',
        'claim_ceiling': 'P_VS_NP = OPEN',
        'widths': list(WIDTHS),
        'widths_changed_from_v3': False,
        'caps': base.CAPS,
        'caps_changed_from_v3': False,
        'inner_representation_changed_from_v3_1': False,
        'boundary_representation': 'AFFINE_GF2_RREF',
        'join_operator': 'J_B=RREF_GF2(Lambda_UNION_Rho)',
        'controls': rows,
        'all_frozen_controls_pass': all(r['status']=='PASS_EXACT_CLOSED' for r in rows),
        'all_frozen_controls_exact': all(
            r.get('private_projection_exact') is True
            and r.get('compressed_join_exact') is True
            and r.get('compressed_boundary_projection_exact') is True
            and r.get('strict_witness_glue_exact') is True
            for r in rows if r['status']=='PASS_EXACT_CLOSED'
        ),
        'adh002_repaired': all(r['status']=='PASS_EXACT_CLOSED' for r in rows if r['k']==14),
        'arbitrary_boundary_is_affine': 'NOT_CLAIMED',
        'next_front': 'NON_AFFINE_CONNECTED_BOUNDARY_GATE',
        'cheap_boundary_language_discovery': 'OPEN',
        'universal_polynomial_coverage': 'OPEN',
        'global_progress_amortization': 'OPEN',
        'p_vs_np': 'OPEN',
    }
    result['result_sha256'] = v3.canon_hash(result)

    print('PF5_CONNECTED_BOUNDARY_ADHESION_V3_2 = FROZEN')
    for r in rows:
        if r['status']=='PASS_EXACT_CLOSED':
            print(
                r['control'],
                'status=PASS_EXACT_CLOSED',
                'k=', r['k'],
                'Lrows=', r['compressed_left_rows'],
                'Rrows=', r['compressed_right_rows'],
                'Jrows=', r['compressed_join_rows'],
                'Jbytes=', r['compressed_join_bytes'],
                'peak=', r['representation_bytes_peak'],
                'ops=', r['total_charged_ops'],
                'witness=', r['witness_source'],
            )
        else:
            print(r['control'], 'status=CAP_HIT', 'phase=', r['cap_phase'], 'cap=', r['cap_reason'])
    print('ADH_002_REPAIRED =', result['adh002_repaired'])
    print('ALL_FROZEN_CONTROLS_PASS =', result['all_frozen_controls_pass'])
    print('NEXT_FRONT = NON_AFFINE_CONNECTED_BOUNDARY_GATE')
    print('CHEAP_BOUNDARY_LANGUAGE_DISCOVERY = OPEN')
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =', result['result_sha256'])

    if '--json-out' in argv:
        i=list(argv).index('--json-out')
        with open(argv[i+1], 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
