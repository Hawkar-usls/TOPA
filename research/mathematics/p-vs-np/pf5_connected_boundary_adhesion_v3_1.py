#!/usr/bin/env python3
"""PF5 connected-boundary adhesion v3.1.

Repairs ADH-001 by replacing only the inner parity-wing OBDD with an exact
proof-carrying affine GF(2) representation. Frozen widths, explicit boundary
language and all v0.1 caps remain unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import product
import json
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pf5_boundary_coverage_matrix_v0 as base
import pf5_connected_boundary_adhesion_v3 as v3


WIDTHS = v3.WIDTHS


@dataclass(frozen=True)
class Eq:
    mask: int
    rhs: int

    def payload(self) -> Tuple[str, int]:
        return (hex(self.mask), int(self.rhs))


def canon_system(rows: Iterable[Eq]) -> List[Eq]:
    uniq = {(int(r.mask), int(r.rhs)) for r in rows}
    if (0, 1) in uniq:
        return [Eq(0, 1)]
    uniq.discard((0, 0))
    return [Eq(m, r) for m, r in sorted(uniq)]


def system_payload(rows: Sequence[Eq]):
    return [r.payload() for r in rows]


def system_bytes(rows: Sequence[Eq]) -> int:
    return base.json_bytes(system_payload(rows))


def system_hash(rows: Sequence[Eq]) -> str:
    return sha256(base.canon_json(system_payload(rows)).encode()).hexdigest()


def bit(v: int) -> int:
    return 1 << (v - 1)


def make_eq(vars_: Sequence[int], rhs: bool) -> Eq:
    m = 0
    for v in vars_:
        m ^= bit(v)
    return Eq(m, int(rhs))


def build_affine_wing(boundary: Sequence[int], private: Sequence[int], target: bool) -> Tuple[List[Eq], int]:
    if len(boundary) != len(private) or not boundary:
        raise ValueError('equal nonempty boundary/private chains required')
    rows: List[Eq] = []
    ops = 0

    rows.append(make_eq((private[0], boundary[0]), False))
    ops += 2
    for i in range(1, len(boundary)):
        rows.append(make_eq((private[i], private[i-1], boundary[i]), False))
        ops += 3
    rows.append(make_eq((private[-1],), target))
    ops += 1
    return canon_system(rows), ops + len(rows)


def project_var(rows: Sequence[Eq], x: int) -> Tuple[List[Eq], Dict, int]:
    xb = bit(x)
    containing: List[Eq] = []
    keep: List[Eq] = []
    ops = 0
    for r in rows:
        ops += 1
        (containing if (r.mask & xb) else keep).append(r)

    before_hash = system_hash(rows)
    if not containing:
        out = canon_system(rows)
        proof = {
            'x': x,
            'pivot': None,
            'before_sha256': before_hash,
            'after_sha256': system_hash(out),
            'xor_count': 0,
            'before_rows': len(rows),
            'after_rows': len(out),
        }
        return out, proof, ops

    pivot = min(containing, key=lambda r: (r.mask.bit_count(), r.mask, r.rhs))
    out_rows = list(keep)
    xor_count = 0
    skipped_pivot = False
    for r in containing:
        if not skipped_pivot and r == pivot:
            skipped_pivot = True
            continue
        out_rows.append(Eq(r.mask ^ pivot.mask, r.rhs ^ pivot.rhs))
        xor_count += 1
        ops += 1

    out = canon_system(out_rows)
    proof = {
        'x': x,
        'pivot': pivot.payload(),
        'before_sha256': before_hash,
        'after_sha256': system_hash(out),
        'xor_count': xor_count,
        'before_rows': len(rows),
        'after_rows': len(out),
    }
    return out, proof, ops


def project_private(rows: Sequence[Eq], private: Sequence[int], build_ops: int) -> Dict:
    current = list(rows)
    proof: List[Dict] = []
    peak = system_bytes(current)
    cumulative = peak
    ops = 0

    for x in private:
        current, rec, z = project_var(current, x)
        ops += z
        proof.append(rec)
        sb = system_bytes(current)
        peak = max(peak, sb)
        cumulative += sb
        base.check_common_caps(peak, base.json_bytes(proof), cumulative, build_ops + ops)

    return {
        'rows': current,
        'proof': proof,
        'representation_bytes_peak': peak,
        'cumulative_state_bytes': cumulative,
        'proof_bytes': base.json_bytes(proof),
        'projection_ops': ops,
    }


def assignment_mask(env: Dict[int, bool]) -> int:
    m = 0
    for v, val in env.items():
        if val:
            m |= bit(v)
    return m


def eval_system(rows: Sequence[Eq], env: Dict[int, bool]) -> Tuple[bool, int]:
    am = assignment_mask(env)
    ops = len(env)
    for r in rows:
        if r.mask == 0 and r.rhs == 1:
            return False, ops + 1
        parity = (r.mask & am).bit_count() & 1
        ops += r.mask.bit_count() + 1
        if parity != r.rhs:
            return False, ops
    return True, ops


def materialize(boundary: Sequence[int], left: Sequence[Eq], right: Sequence[Eq]) -> Tuple[Set[str], Set[str], Set[str], Dict[str, int]]:
    L: Set[str] = set()
    R: Set[str] = set()
    enum_ops = 0
    eval_ops = 0
    for bits in product((0, 1), repeat=len(boundary)):
        enum_ops += 1
        env = {v: bool(z) for v, z in zip(boundary, bits)}
        lv, lo = eval_system(left, env)
        rv, ro = eval_system(right, env)
        eval_ops += lo + ro
        row = ''.join(str(z) for z in bits)
        if lv:
            L.add(row)
        if rv:
            R.add(row)

    small, large = (L, R) if len(L) <= len(R) else (R, L)
    J = set()
    join_ops = 0
    for row in small:
        join_ops += 1
        if row in large:
            J.add(row)
    return L, R, J, {
        'boundary_enumeration_ops': enum_ops,
        'boundary_residual_eval_ops': eval_ops,
        'join_ops': join_ops,
    }


def solve_pivot(eq_payload: Tuple[str, int], x: int, env: Dict[int, bool]) -> Tuple[bool, int]:
    mask = int(eq_payload[0], 16)
    rhs = int(eq_payload[1])
    xb = bit(x)
    if not (mask & xb):
        raise AssertionError('pivot does not contain projected variable')
    other = mask ^ xb
    parity = 0
    ops = 0
    v = 1
    m = other
    while m:
        if m & 1:
            ops += 1
            if v not in env:
                raise AssertionError(f'witness lift missing remaining variable {v}')
            parity ^= int(env[v])
        v += 1
        m >>= 1
    return bool(rhs ^ parity), ops + 1


def lift_private(proof: Sequence[Dict], boundary_env: Dict[int, bool]) -> Tuple[Dict[int, bool], int]:
    env = dict(boundary_env)
    ops = 0
    for rec in reversed(proof):
        x = int(rec['x'])
        pivot = rec['pivot']
        if pivot is None:
            # Free existential root: choose canonical False.
            env[x] = False
            ops += 1
        else:
            val, z = solve_pivot(tuple(pivot), x, env)
            env[x] = val
            ops += z
    return env, ops


def verify_projection_replay(original: Sequence[Eq], private: Sequence[int], proof: Sequence[Dict], final_rows: Sequence[Eq]) -> Tuple[bool, int]:
    current = list(original)
    ops = 0
    for x, rec in zip(private, proof):
        if system_hash(current) != rec['before_sha256']:
            return False, ops
        out, replay, z = project_var(current, x)
        ops += z
        if replay != rec:
            return False, ops
        current = out
    return current == list(final_rows), ops


def run_control(c: v3.AdhesionControl) -> Dict:
    B, A, C = c.boundary, c.left_private, c.right_private
    connected, connectivity_ops = v3.connectivity_check(c)
    assert connected

    left0, left_build = build_affine_wing(B, A, False)
    right0, right_build = build_affine_wing(B, C, c.right_target)
    build_ops = left_build + right_build + connectivity_ops
    phase = 'PRIVATE_PROJECTION'
    partial: Dict[str, object] = {}

    try:
        left = project_private(left0, A, build_ops)
        right = project_private(right0, C, build_ops + int(left['projection_ops']))

        replay_left, rl_ops = verify_projection_replay(left0, A, left['proof'], left['rows'])
        replay_right, rr_ops = verify_projection_replay(right0, C, right['proof'], right['rows'])
        if not replay_left or not replay_right:
            raise AssertionError('affine projection proof replay failed')

        private_peak = int(left['representation_bytes_peak']) + int(right['representation_bytes_peak'])
        private_cum = int(left['cumulative_state_bytes']) + int(right['cumulative_state_bytes'])
        private_proof_bytes = int(left['proof_bytes']) + int(right['proof_bytes'])
        private_ops = int(left['projection_ops']) + int(right['projection_ops'])
        verification_ops = rl_ops + rr_ops

        phase = 'ADHESION_BUILD'
        L, R, J, table_ops = materialize(B, left['rows'], right['rows'])
        tables_payload = {'Lambda': sorted(L), 'Rho': sorted(R), 'J': sorted(J)}
        table_bytes = base.json_bytes(tables_payload)
        compact_residual_bytes = system_bytes(left['rows']) + system_bytes(right['rows'])
        adhesion_state_bytes = table_bytes + compact_residual_bytes
        peak = max(private_peak, adhesion_state_bytes)
        cumulative = private_cum + adhesion_state_bytes
        total_ops = build_ops + private_ops + verification_ops + sum(table_ops.values())
        partial.update({
            'left_boundary_rows': len(L),
            'right_boundary_rows': len(R),
            'join_rows': len(J),
            'adhesion_table_bytes': table_bytes,
            'compact_residual_bytes': compact_residual_bytes,
            'charged_ops_before_cap_check': total_ops,
        })
        base.check_common_caps(peak, private_proof_bytes, cumulative, total_ops)

        phase = 'BOUNDARY_PROJECTION'
        final_rows, boundary_proof, boundary_project_ops, boundary_peak, boundary_cum = v3.project_join_rows(J, B)
        peak = max(peak, boundary_peak)
        cumulative += boundary_cum
        proof_bytes = private_proof_bytes + base.json_bytes(boundary_proof)
        total_ops += boundary_project_ops
        base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

        final_scalar = bool(final_rows)
        if final_rows not in (set(), {''}):
            raise AssertionError('boundary projection did not terminate to scalar relation')

        ref_left = v3.expected_relation(c.k, False)
        ref_right = v3.expected_relation(c.k, c.right_target)
        reference_ops = 2 * (1 << c.k)
        boundary_exact = L == ref_left and R == ref_right
        join_exact = J == (ref_left & ref_right)
        expected_count = 1 << (c.k - 1)
        exponential_observed = len(L) == expected_count and len(R) == expected_count

        witness: Optional[Dict[int, bool]] = None
        witness_valid: Optional[bool] = None
        witness_ops = 0
        witness_source = 'NO_WITNESS_UNSAT_JOIN_EMPTY'

        if final_scalar:
            chosen = min(J)
            boundary_env = {v: bit_ == '1' for v, bit_ in zip(B, chosen)}
            left_env, lo = lift_private(left['proof'], boundary_env)
            right_env, ro = lift_private(right['proof'], boundary_env)
            witness_ops += lo + ro

            witness = dict(boundary_env)
            for v in A:
                witness[v] = left_env[v]
            for v in C:
                if v in witness:
                    raise AssertionError('private witness overlap')
                witness[v] = right_env[v]
            expected_vars = set(range(1, 3*c.k + 1))
            if set(witness) != expected_vars:
                raise AssertionError('strict affine witness union incomplete')

            lv, lvo = eval_system(left0, witness)
            rv, rvo = eval_system(right0, witness)
            verification_ops += lvo + rvo
            witness_valid = lv and rv
            witness_source = 'JOIN_ROW_PLUS_ACTUAL_AFFINE_PIVOT_PROOFS'
            if not witness_valid:
                raise AssertionError('affine witness verification failed')

        verification_ops += reference_ops
        total_ops += witness_ops + reference_ops
        witness_bytes = base.json_bytes(witness or {})
        base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

        cert = {
            'control': c.name,
            'left_projected_system_sha256': system_hash(left['rows']),
            'right_projected_system_sha256': system_hash(right['rows']),
            'Lambda_sha256': v3.canon_hash(sorted(L)),
            'Rho_sha256': v3.canon_hash(sorted(R)),
            'J_sha256': v3.canon_hash(sorted(J)),
            'boundary_projection': boundary_proof,
            'witness_sha256': v3.canon_hash(witness or {}),
        }

        return {
            'control': c.name,
            'k': c.k,
            'expected_sat': c.expected_sat,
            'status': 'PASS_EXACT_CLOSED',
            'cap_phase': None,
            'cap_reason': None,
            'connected': connected,
            'inner_representation': 'AFFINE_GF2',
            'input_bytes': c.input_bytes,
            'left_boundary_rows': len(L),
            'right_boundary_rows': len(R),
            'expected_each_wing_rows': expected_count,
            'join_rows': len(J),
            'final_scalar': final_scalar,
            'private_projection_exact': replay_left and replay_right,
            'boundary_relations_exact': boundary_exact,
            'adhesion_join_exact': join_exact,
            'repeated_boundary_project_exact': final_scalar == c.expected_sat,
            'strict_witness_glue_exact': (witness_valid is True) if final_scalar else True,
            'witness_valid': witness_valid,
            'witness_source': witness_source,
            'witness_bytes': witness_bytes,
            'representation_bytes_peak': peak,
            'cumulative_state_bytes': cumulative,
            'private_proof_bytes': private_proof_bytes,
            'boundary_proof_bytes': base.json_bytes(boundary_proof),
            'proof_bytes': proof_bytes,
            'build_ops': build_ops,
            'private_projection_ops': private_ops,
            'boundary_enumeration_ops': table_ops['boundary_enumeration_ops'],
            'boundary_residual_eval_ops': table_ops['boundary_residual_eval_ops'],
            'join_ops': table_ops['join_ops'],
            'boundary_projection_ops': boundary_project_ops,
            'witness_ops': witness_ops,
            'verification_ops': verification_ops,
            'total_charged_ops': total_ops,
            'adhesion_table_bytes': table_bytes,
            'compact_residual_bytes': compact_residual_bytes,
            'explicit_table_exponential_footprint_observed': exponential_observed,
            'certificate_sha256': v3.canon_hash(cert),
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
            'input_bytes': c.input_bytes,
            'partial': partial,
            'claim': 'FINITE_EXPLICIT_BOUNDARY_REPRESENTATION_CAP_ONLY' if phase != 'PRIVATE_PROJECTION' else 'FINITE_INNER_REPRESENTATION_CAP_ONLY',
        }


def main(argv: Sequence[str]) -> int:
    rows = [run_control(c) for c in v3.controls()]
    passed = [r for r in rows if r['status'] == 'PASS_EXACT_CLOSED']
    first_cap = next((r for r in rows if r['status'] == 'CAP_HIT'), None)

    result = {
        'artifact_id': 'PF5-CONNECTED-BOUNDARY-ADHESION-V3.1-AFFINE-WING',
        'repair_of': 'ADH-001-OBDD-WING-BOTTLENECK',
        'claim_ceiling': 'P_VS_NP = OPEN',
        'widths_frozen_before_v3_provider_run': list(WIDTHS),
        'widths_changed_from_v3': False,
        'caps': base.CAPS,
        'caps_changed_from_v3': False,
        'boundary_language_changed_from_v3': False,
        'inner_representation': 'AFFINE_GF2',
        'join_operator': 'J_B(Lambda,Rho)=Lambda_INTERSECT_Rho',
        'controls': rows,
        'all_passed_controls_exact': all(
            r['private_projection_exact']
            and r['boundary_relations_exact']
            and r['adhesion_join_exact']
            and r['repeated_boundary_project_exact']
            and r['strict_witness_glue_exact']
            for r in passed
        ),
        'explicit_table_exponential_footprint_observed': all(
            r['explicit_table_exponential_footprint_observed'] for r in passed
        ) if passed else False,
        'first_base_cap_hit': None if first_cap is None else {
            'control': first_cap['control'],
            'k': first_cap['k'],
            'phase': first_cap['cap_phase'],
            'reason': first_cap['cap_reason'],
            'partial': first_cap.get('partial', {}),
        },
        'adh001_repaired_if_first_cap_moves_past_private_projection': first_cap is None or first_cap['cap_phase'] != 'PRIVATE_PROJECTION',
        'conditional_width_theorem': 'POLY_WINGS + UNIVERSAL_O(LOG_N)_ADHESION => POLY_EXPLICIT_BOUNDARY_JOIN_PROJECT',
        'universal_o_log_n_adhesion_bound': 'OPEN',
        'cheap_compact_boundary_discovery': 'OPEN',
        'compressed_boundary_rewrite_discovery': 'OPEN',
        'global_progress_amortization': 'OPEN',
        'representation_lower_bound': 'NOT_ESTABLISHED',
        'p_vs_np': 'OPEN',
    }
    result['result_sha256'] = v3.canon_hash(result)

    print('PF5_CONNECTED_BOUNDARY_ADHESION_V3_1 = FROZEN')
    for r in rows:
        if r['status'] == 'PASS_EXACT_CLOSED':
            print(
                r['control'],
                'status=PASS_EXACT_CLOSED',
                'k=', r['k'],
                'rows=', r['left_boundary_rows'],
                'join=', r['join_rows'],
                'peak_bytes=', r['representation_bytes_peak'],
                'table_bytes=', r['adhesion_table_bytes'],
                'ops=', r['total_charged_ops'],
                'witness=', r['witness_source'],
            )
        else:
            print(
                r['control'],
                'status=CAP_HIT',
                'k=', r['k'],
                'phase=', r['cap_phase'],
                'cap=', r['cap_reason'],
                'partial=', r.get('partial', {}),
            )
    print('ADH_001_REPAIRED =', result['adh001_repaired_if_first_cap_moves_past_private_projection'])
    print('FIRST_BASE_CAP_HIT =', result['first_base_cap_hit'])
    print('EXPLICIT_TABLE_EXPONENTIAL_FOOTPRINT_OBSERVED =', result['explicit_table_exponential_footprint_observed'])
    print('UNIVERSAL_O_LOG_N_ADHESION_BOUND = OPEN')
    print('CHEAP_COMPACT_BOUNDARY_DISCOVERY = OPEN')
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =', result['result_sha256'])

    if '--json-out' in argv:
        i = list(argv).index('--json-out')
        with open(argv[i+1], 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
