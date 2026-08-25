#!/usr/bin/env python3
"""PF5 non-affine connected-boundary gate v4.

Finite exact mechanics only.

Left private wing: proof-carrying AFFINE_GF2 even parity.
Right private wing: deterministic interleaved OBDD for equality glue plus
non-affine OR / EXACTLY_ONE boundary predicate.
Heterogeneous JOIN: compile affine residual into a common boundary OBDD, copy
right residual into that manager, APPLY_AND, then repeatedly existentially
project shared roots. Strict witnesses are reconstructed only from actual
projection/pivot proofs.

This does not prove P=NP or P!=NP.
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
import pf5_connected_boundary_adhesion_v3_1 as v31
import pf5_connected_boundary_adhesion_v3_2 as v32


WIDTHS = (3, 4, 6, 8, 10, 12, 14)


@dataclass(frozen=True)
class V4Control:
    name: str
    k: int
    right_kind: str  # OR or EXACTLY_ONE
    expected_sat: bool

    @property
    def boundary(self) -> Tuple[int, ...]:
        return tuple(range(1, self.k + 1))

    @property
    def left_private(self) -> Tuple[int, ...]:
        return tuple(range(self.k + 1, 2 * self.k + 1))

    @property
    def right_private(self) -> Tuple[int, ...]:
        return tuple(range(2 * self.k + 1, 3 * self.k + 1))

    @property
    def input_bytes(self) -> int:
        return base.json_bytes({
            'name': self.name,
            'k': self.k,
            'right_kind': self.right_kind,
            'expected_sat': self.expected_sat,
            'boundary': self.boundary,
            'left_private': self.left_private,
            'right_private': self.right_private,
            'left_language': 'AFFINE_GF2',
            'right_language': 'INTERLEAVED_OBDD',
        })


def controls() -> List[V4Control]:
    out: List[V4Control] = []
    for k in WIDTHS:
        out.append(V4Control(f'NA_PAR_OR_K{k}_SAT', k, 'OR', True))
        out.append(V4Control(f'NA_PAR_EX1_K{k}_UNSAT', k, 'EXACTLY_ONE', False))
    return out


def canon_hash(obj) -> str:
    return sha256(base.canon_json(obj).encode()).hexdigest()


def manager_payload(b: base.BDD):
    return {
        'order': b.order,
        'nodes': sorted((u, *node) for u, node in b.nodes.items()),
    }


def manager_bytes(b: base.BDD) -> int:
    return base.json_bytes(manager_payload(b))


def bdd_support(b: base.BDD, root: int) -> Tuple[Set[int], int]:
    support: Set[int] = set()
    ops = 0
    for u in b.reachable(root):
        ops += 1
        v, _, _ = b.nodes[u]
        support.add(v)
    return support, ops


def right_accept(kind: str, state: int) -> bool:
    if kind == 'OR':
        return state == 1
    if kind == 'EXACTLY_ONE':
        return state == 1
    raise AssertionError(kind)


def right_update(kind: str, state: int, bit_value: int) -> int:
    if kind == 'OR':
        return int(bool(state or bit_value))
    if kind == 'EXACTLY_ONE':
        return min(2, state + int(bit_value))
    raise AssertionError(kind)


def build_right_wing_bdd(c: V4Control, b: base.BDD) -> Tuple[int, Dict, int]:
    """Exact finite-state constructor for G(B) AND all_i(C_i == B_i)."""
    B, C = c.boundary, c.right_private
    memo_pair: Dict[Tuple[int, int], int] = {}
    memo_b: Dict[Tuple[int, int, int], int] = {}
    calls = 0
    transitions = 0

    def pair(i: int, state: int) -> int:
        nonlocal calls
        calls += 1
        key = (i, state)
        if key in memo_pair:
            return memo_pair[key]
        if i == c.k:
            out = 1 if right_accept(c.right_kind, state) else 0
            memo_pair[key] = out
            return out
        lo = bstage(i, state, 0)
        hi = bstage(i, state, 1)
        out = b.mk(C[i], lo, hi)
        memo_pair[key] = out
        return out

    def bstage(i: int, state: int, pending_c: int) -> int:
        nonlocal calls, transitions
        calls += 1
        key = (i, state, pending_c)
        if key in memo_b:
            return memo_b[key]
        next_state = right_update(c.right_kind, state, pending_c)
        good = pair(i + 1, next_state)
        transitions += 1
        if pending_c == 0:
            out = b.mk(B[i], good, 0)
        else:
            out = b.mk(B[i], 0, good)
        memo_b[key] = out
        return out

    root = pair(0, 0)
    proof = {
        'constructor': 'PAIR_EQUALITY_PLUS_FINITE_STATE_PREDICATE',
        'kind': c.right_kind,
        'order': list(b.order),
        'pair_states': len(memo_pair),
        'pending_states': len(memo_b),
        'calls': calls,
        'transitions': transitions,
        'root': root,
        'manager_sha256': canon_hash(manager_payload(b)),
    }
    return root, proof, calls + transitions


def project_private_obdd(
    b: base.BDD,
    root: int,
    private_order: Sequence[int],
    prior_ops: int,
    prior_proof_bytes: int = 0,
) -> Dict:
    proof: List[Dict] = []
    peak = manager_bytes(b)
    cumulative = peak
    update_ops = 0

    for x in private_order:
        before = b.ops
        pre = root
        c0 = b.restrict(pre, x, False)
        c1 = b.restrict(pre, x, True)
        root = b.apply_or(c0, c1)
        update_ops += b.ops - before
        proof.append({'x': x, 'pre': pre, 'c0': c0, 'c1': c1, 'post': root})
        sb = manager_bytes(b)
        peak = max(peak, sb)
        cumulative += sb
        base.check_common_caps(
            peak,
            prior_proof_bytes + base.json_bytes(proof),
            cumulative,
            prior_ops + update_ops,
        )

    return {
        'root': root,
        'proof': proof,
        'representation_bytes_peak': peak,
        'cumulative_state_bytes': cumulative,
        'proof_bytes': base.json_bytes(proof),
        'projection_ops': update_ops,
    }


def expected_right(kind: str, bits: Sequence[int]) -> bool:
    if kind == 'OR':
        return any(bits)
    if kind == 'EXACTLY_ONE':
        return sum(bits) == 1
    raise AssertionError(kind)


def expected_left(bits: Sequence[int]) -> bool:
    return (sum(bits) & 1) == 0


def gf2_rank(vectors: Iterable[int], k: int) -> Tuple[int, int]:
    basis = [0] * k
    rank = 0
    ops = 0
    for original in vectors:
        x = int(original)
        for p in range(k - 1, -1, -1):
            ops += 1
            if not (x & (1 << p)):
                continue
            if basis[p]:
                x ^= basis[p]
                ops += 1
            else:
                basis[p] = x
                rank += 1
                break
    return rank, ops


def affine_truth_set_test(models: Set[int], k: int) -> Tuple[bool, int]:
    # Empty set is representable by contradiction; a nonempty affine relation
    # is a coset a+V. Translate by one anchor and test |D| == 2^rank(D).
    if not models:
        return True, 1
    anchor = min(models)
    diffs = {m ^ anchor for m in models}
    rank, ops = gf2_rank(diffs, k)
    return len(diffs) == (1 << rank), ops + len(models)


def verify_right_residual(c: V4Control, b: base.BDD, root: int) -> Dict:
    support, support_ops = bdd_support(b, root)
    truth: Set[int] = set()
    eval_ops = 0
    exact = support <= set(c.boundary)
    for n, bits in enumerate(product((0, 1), repeat=c.k)):
        env = {v: bool(z) for v, z in zip(c.boundary, bits)}
        got, zops = v3.eval_bdd_count(b, root, env)
        eval_ops += zops + c.k
        want = expected_right(c.right_kind, bits)
        if got:
            truth.add(n)
        if got != want:
            exact = False
    is_affine, affine_ops = affine_truth_set_test(truth, c.k)
    return {
        'exact': exact,
        'support': sorted(support),
        'models': len(truth),
        'truth': truth,
        'non_affine': not is_affine,
        'ops': support_ops + eval_ops + affine_ops,
    }


def affine_restrict(
    rows: Sequence[v31.Eq],
    x: int,
    value: bool,
    remaining_order: Sequence[int],
) -> Tuple[List[v31.Eq], Dict, int]:
    xb = v31.bit(x)
    raw: List[v31.Eq] = []
    ops = 0
    for r in rows:
        ops += 1
        if r.mask & xb:
            raw.append(v31.Eq(r.mask ^ xb, r.rhs ^ int(value)))
        else:
            raw.append(r)
    out, transcript, rops = v32.rref(raw, remaining_order)
    ops += rops
    return out, {
        'x': x,
        'value': int(value),
        'pre_sha256': v31.system_hash(rows),
        'post_sha256': v31.system_hash(out),
        'rref': transcript,
    }, ops


def compile_affine_to_common(
    rows: Sequence[v31.Eq],
    boundary: Sequence[int],
    dst: base.BDD,
) -> Dict:
    memo: Dict[Tuple[int, Tuple[Tuple[int, int], ...]], int] = {}
    transcript: List[Dict] = []
    calls = 0
    internal_ops = 0
    residual_cumulative = 0
    residual_peak = 0
    before_bdd_ops = dst.ops

    def key_rows(rs: Sequence[v31.Eq]) -> Tuple[Tuple[int, int], ...]:
        return tuple((int(r.mask), int(r.rhs)) for r in rs)

    def rec(i: int, rs: Sequence[v31.Eq]) -> int:
        nonlocal calls, internal_ops, residual_cumulative, residual_peak
        calls += 1
        payload_bytes = v31.system_bytes(rs)
        residual_cumulative += payload_bytes
        residual_peak = max(residual_peak, payload_bytes)
        if v32.is_contradiction(rs):
            return 0
        if not rs:
            return 1
        if i == len(boundary):
            raise AssertionError('affine residual nonterminal after full boundary restriction')
        key = (i, key_rows(rs))
        internal_ops += 1
        if key in memo:
            return memo[key]
        x = boundary[i]
        lo_rows, lo_proof, lo_ops = affine_restrict(rs, x, False, boundary[i+1:])
        hi_rows, hi_proof, hi_ops = affine_restrict(rs, x, True, boundary[i+1:])
        internal_ops += lo_ops + hi_ops
        lo = rec(i + 1, lo_rows)
        hi = rec(i + 1, hi_rows)
        out = dst.mk(x, lo, hi)
        memo[key] = out
        transcript.append({
            'i': i,
            'x': x,
            'state_sha256': v31.system_hash(rs),
            'lo': lo_proof,
            'hi': hi_proof,
            'node': out,
        })
        return out

    root = rec(0, list(rows))
    bdd_ops = dst.ops - before_bdd_ops
    proof = {
        'source_sha256': v31.system_hash(rows),
        'boundary_order': list(boundary),
        'root': root,
        'unique_residual_states': len(memo),
        'recursive_calls': calls,
        'transcript': transcript,
    }
    return {
        'root': root,
        'proof': proof,
        'proof_bytes': base.json_bytes(proof),
        'ops': internal_ops + calls + bdd_ops,
        'residual_cumulative_state_bytes': residual_cumulative,
        'residual_peak_state_bytes': residual_peak,
    }


def copy_residual_to_common(src: base.BDD, root: int, dst: base.BDD, boundary: Sequence[int]) -> Dict:
    allowed = set(boundary)
    memo: Dict[int, int] = {}
    transcript: List[Tuple[int, int]] = []
    visits = 0
    before = dst.ops

    def rec(u: int) -> int:
        nonlocal visits
        visits += 1
        if u in (0, 1):
            return u
        if u in memo:
            return memo[u]
        v, lo, hi = src.nodes[u]
        if v not in allowed:
            raise AssertionError(f'right residual still contains private variable {v}')
        out = dst.mk(v, rec(lo), rec(hi))
        memo[u] = out
        transcript.append((u, out))
        return out

    out_root = rec(root)
    proof = {
        'source_root': root,
        'destination_root': out_root,
        'source_manager_sha256': canon_hash(manager_payload(src)),
        'mapping': transcript,
    }
    return {
        'root': out_root,
        'proof': proof,
        'proof_bytes': base.json_bytes(proof),
        'ops': visits + (dst.ops - before),
    }


def apply_and(b: base.BDD, a: int, c: int) -> int:
    memo: Dict[Tuple[int, int], int] = {}

    def rec(u: int, v: int) -> int:
        b.ops += 1
        if u == 0 or v == 0:
            return 0
        if u == 1:
            return v
        if v == 1:
            return u
        if u == v:
            return u
        key = (u, v) if u <= v else (v, u)
        if key in memo:
            return memo[key]
        uv, ul, uh = b.nodes[u]
        vv, vl, vh = b.nodes[v]
        if b.rank[uv] == b.rank[vv]:
            out = b.mk(uv, rec(ul, vl), rec(uh, vh))
        elif b.rank[uv] < b.rank[vv]:
            out = b.mk(uv, rec(ul, v), rec(uh, v))
        else:
            out = b.mk(vv, rec(u, vl), rec(u, vh))
        memo[key] = out
        return out

    return rec(a, c)


def project_common_boundary(
    b: base.BDD,
    root: int,
    boundary: Sequence[int],
    prior_ops: int,
    prior_proof_bytes: int,
    prior_cumulative: int,
    prior_peak: int,
) -> Dict:
    proof: List[Dict] = []
    ops = 0
    peak = max(prior_peak, manager_bytes(b))
    cumulative = prior_cumulative + manager_bytes(b)

    for x in boundary:
        before = b.ops
        pre = root
        c0 = b.restrict(pre, x, False)
        c1 = b.restrict(pre, x, True)
        root = b.apply_or(c0, c1)
        ops += b.ops - before
        proof.append({'x': x, 'pre': pre, 'c0': c0, 'c1': c1, 'post': root})
        sb = manager_bytes(b)
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
        'proof': proof,
        'ops': ops,
        'proof_bytes': base.json_bytes(proof),
        'representation_bytes_peak': peak,
        'cumulative_state_bytes': cumulative,
    }


def lift_bdd_projection_witness(
    b: base.BDD,
    proof: Sequence[Dict],
    seed: Dict[int, bool],
) -> Tuple[Dict[int, bool], int]:
    env = dict(seed)
    ops = 0
    for rec in reversed(proof):
        x = int(rec['x'])
        z0, o0 = v3.eval_bdd_count(b, int(rec['c0']), env)
        ops += o0
        if z0:
            env[x] = False
            continue
        z1, o1 = v3.eval_bdd_count(b, int(rec['c1']), env)
        ops += o1
        if not z1:
            raise AssertionError(f'BDD witness lift failed at {x}')
        env[x] = True
    return env, ops


def verify_common_semantics(
    c: V4Control,
    left_affine: Sequence[v31.Eq],
    right_src_bdd: base.BDD,
    right_src_root: int,
    common: base.BDD,
    common_left_root: int,
    common_right_root: int,
    join_root: int,
) -> Dict:
    left_models = right_models = join_models = 0
    right_truth: Set[int] = set()
    join_truth: Set[int] = set()
    exact_left = exact_right_copy = exact_join = True
    ops = 0

    for n, bits in enumerate(product((0, 1), repeat=c.k)):
        env = {v: bool(z) for v, z in zip(c.boundary, bits)}
        la, lao = v31.eval_system(left_affine, env)
        rr, rro = v3.eval_bdd_count(right_src_bdd, right_src_root, env)
        cl, clo = v3.eval_bdd_count(common, common_left_root, env)
        cr, cro = v3.eval_bdd_count(common, common_right_root, env)
        jj, jjo = v3.eval_bdd_count(common, join_root, env)
        ops += lao + rro + clo + cro + jjo + c.k

        wl = expected_left(bits)
        wr = expected_right(c.right_kind, bits)
        wj = wl and wr
        if la:
            left_models += 1
        if rr:
            right_models += 1
            right_truth.add(n)
        if jj:
            join_models += 1
            join_truth.add(n)

        if not (la == wl and cl == la):
            exact_left = False
        if not (rr == wr and cr == rr):
            exact_right_copy = False
        if jj != wj:
            exact_join = False

    right_affine, rops = affine_truth_set_test(right_truth, c.k)
    join_affine, jops = affine_truth_set_test(join_truth, c.k)
    ops += rops + jops
    return {
        'affine_conversion_exact': exact_left,
        'right_copy_exact': exact_right_copy,
        'join_exact': exact_join,
        'left_models': left_models,
        'right_models': right_models,
        'join_models': join_models,
        'right_non_affine': not right_affine,
        'join_non_affine': not join_affine,
        'ops': ops,
    }


def eval_right_source(c: V4Control, env: Dict[int, bool]) -> Tuple[bool, int]:
    ops = 0
    for bvar, cvar in zip(c.boundary, c.right_private):
        ops += 1
        if bool(env[bvar]) != bool(env[cvar]):
            return False, ops
    bits = [int(bool(env[v])) for v in c.boundary]
    ops += c.k
    return expected_right(c.right_kind, bits), ops


def connectivity_check(c: V4Control) -> Tuple[bool, int]:
    vertices = set(c.boundary) | set(c.left_private) | set(c.right_private)
    graph: Dict[int, Set[int]] = {v: set() for v in vertices}
    ops = 0

    def edge(a: int, b: int) -> None:
        nonlocal ops
        graph[a].add(b)
        graph[b].add(a)
        ops += 1

    # Left parity-chain primal interactions.
    edge(c.left_private[0], c.boundary[0])
    for i in range(1, c.k):
        a0, a1, bv = c.left_private[i-1], c.left_private[i], c.boundary[i]
        edge(a0, a1)
        edge(a0, bv)
        edge(a1, bv)
    # Right equality glue attaches every private root to the shared boundary.
    for bv, cv in zip(c.boundary, c.right_private):
        edge(bv, cv)

    seen: Set[int] = set()
    stack = [c.boundary[0]]
    while stack:
        v = stack.pop()
        ops += 1
        if v in seen:
            continue
        seen.add(v)
        stack.extend(graph[v] - seen)
    return seen == vertices, ops


def run_control(c: V4Control) -> Dict:
    B, A, C = c.boundary, c.left_private, c.right_private
    connected, connectivity_ops = connectivity_check(c)
    assert connected

    phase = 'LEFT_AFFINE_PRIVATE'
    right_bdd: Optional[base.BDD] = None
    common: Optional[base.BDD] = None
    partial: Dict[str, object] = {}
    failed_discovery_ops = 0

    try:
        # Left proof-carrying affine wing.
        left0, left_build_ops = v31.build_affine_wing(B, A, False)
        left = v31.project_private(left0, A, left_build_ops + connectivity_ops)
        left_replay, left_replay_ops = v31.verify_projection_replay(
            left0, A, left['proof'], left['rows']
        )
        if not left_replay:
            raise AssertionError('left affine projection replay failed')

        # Right proof-carrying OBDD wing under a frozen interleaved order.
        phase = 'RIGHT_OBDD_CONSTRUCT'
        interleaved: List[int] = []
        for cv, bv in zip(C, B):
            interleaved.extend((cv, bv))
        right_bdd = base.BDD(tuple(interleaved))
        before_right_ops = right_bdd.ops
        right_root, right_constructor_proof, right_constructor_internal = build_right_wing_bdd(c, right_bdd)
        right_constructor_ops = (right_bdd.ops - before_right_ops) + right_constructor_internal
        right_constructor_proof_bytes = base.json_bytes(right_constructor_proof)
        base.check_common_caps(
            manager_bytes(right_bdd),
            right_constructor_proof_bytes,
            manager_bytes(right_bdd),
            left_build_ops + connectivity_ops + right_constructor_ops,
        )

        phase = 'RIGHT_OBDD_PRIVATE_PROJECT'
        prior_ops = (
            left_build_ops + connectivity_ops + int(left['projection_ops'])
            + left_replay_ops + right_constructor_ops
        )
        right = project_private_obdd(
            right_bdd,
            right_root,
            C,
            prior_ops,
            right_constructor_proof_bytes,
        )
        right_check = verify_right_residual(c, right_bdd, int(right['root']))
        if not right_check['exact']:
            raise AssertionError('right post-private residual is not the frozen predicate')
        if not right_check['non_affine']:
            raise AssertionError('right boundary control unexpectedly affine')

        # Common boundary OBDD manager.
        phase = 'AFFINE_TO_COMMON_OBDD'
        common = base.BDD(B)
        conversion = compile_affine_to_common(left['rows'], B, common)
        conversion_manager_bytes = manager_bytes(common)
        conversion_cumulative = (
            int(left['cumulative_state_bytes'])
            + int(right['cumulative_state_bytes'])
            + int(conversion['residual_cumulative_state_bytes'])
            + conversion_manager_bytes
        )
        conversion_peak = max(
            int(left['representation_bytes_peak']),
            int(right['representation_bytes_peak']),
            int(conversion['residual_peak_state_bytes']),
            conversion_manager_bytes,
        )
        proof_bytes_so_far = (
            int(left['proof_bytes']) + right_constructor_proof_bytes
            + int(right['proof_bytes']) + int(conversion['proof_bytes'])
        )
        ops_so_far = (
            left_build_ops + connectivity_ops + int(left['projection_ops']) + left_replay_ops
            + right_constructor_ops + int(right['projection_ops']) + int(right_check['ops'])
            + int(conversion['ops'])
        )
        base.check_common_caps(
            conversion_peak, proof_bytes_so_far, conversion_cumulative, ops_so_far
        )

        phase = 'COPY_RIGHT_TO_COMMON_OBDD'
        copied = copy_residual_to_common(right_bdd, int(right['root']), common, B)
        copy_state_bytes = manager_bytes(common)
        cumulative = conversion_cumulative + copy_state_bytes
        peak = max(conversion_peak, copy_state_bytes)
        proof_bytes_so_far += int(copied['proof_bytes'])
        ops_so_far += int(copied['ops'])
        base.check_common_caps(peak, proof_bytes_so_far, cumulative, ops_so_far)

        phase = 'HETEROGENEOUS_JOIN'
        before_join = common.ops
        join_root = apply_and(common, int(conversion['root']), int(copied['root']))
        join_ops = common.ops - before_join
        join_state_bytes = manager_bytes(common)
        cumulative += join_state_bytes
        peak = max(peak, join_state_bytes)
        join_proof = {
            'operator': 'COMMON_OBDD_APPLY_AND',
            'left_root': int(conversion['root']),
            'right_root': int(copied['root']),
            'join_root': join_root,
            'manager_sha256': canon_hash(manager_payload(common)),
        }
        proof_bytes_so_far += base.json_bytes(join_proof)
        ops_so_far += join_ops
        base.check_common_caps(peak, proof_bytes_so_far, cumulative, ops_so_far)

        phase = 'HETEROGENEOUS_SEMANTIC_VERIFY'
        semantic = verify_common_semantics(
            c,
            left['rows'],
            right_bdd,
            int(right['root']),
            common,
            int(conversion['root']),
            int(copied['root']),
            join_root,
        )
        if not semantic['affine_conversion_exact']:
            raise AssertionError('affine-to-OBDD conversion semantic mismatch')
        if not semantic['right_copy_exact']:
            raise AssertionError('right residual copy semantic mismatch')
        if not semantic['join_exact']:
            raise AssertionError('heterogeneous JOIN semantic mismatch')
        if c.expected_sat and not semantic['join_non_affine']:
            raise AssertionError('SAT joined relation was expected to remain non-affine')
        ops_so_far += int(semantic['ops'])
        base.check_common_caps(peak, proof_bytes_so_far, cumulative, ops_so_far)

        phase = 'SHARED_BOUNDARY_PROJECT'
        shared = project_common_boundary(
            common,
            join_root,
            B,
            ops_so_far,
            proof_bytes_so_far,
            cumulative,
            peak,
        )
        final_root = int(shared['root'])
        if final_root not in (0, 1):
            raise AssertionError('all shared roots projected but common OBDD is nonterminal')
        final_scalar = bool(final_root)
        if final_scalar != c.expected_sat:
            raise AssertionError('shared projection scalar disagrees with frozen control')

        proof_bytes = proof_bytes_so_far + int(shared['proof_bytes'])
        peak = int(shared['representation_bytes_peak'])
        cumulative = int(shared['cumulative_state_bytes'])
        shared_projection_ops = int(shared['ops'])

        witness: Optional[Dict[int, bool]] = None
        witness_valid: Optional[bool] = None
        witness_ops = 0
        verification_ops = 0
        witness_source = 'NO_WITNESS_COMMON_OBDD_FALSE'

        if final_scalar:
            boundary_env, bo = lift_bdd_projection_witness(common, shared['proof'], {})
            witness_ops += bo
            if set(boundary_env) != set(B):
                raise AssertionError('shared witness is incomplete')
            join_ok, jo = v3.eval_bdd_count(common, join_root, boundary_env)
            verification_ops += jo
            if not join_ok:
                raise AssertionError('reconstructed shared witness does not satisfy JOIN')

            right_env, ro = lift_bdd_projection_witness(right_bdd, right['proof'], boundary_env)
            witness_ops += ro
            left_env, lo = v31.lift_private(left['proof'], boundary_env)
            witness_ops += lo

            witness = dict(boundary_env)
            for v in A:
                if v not in left_env:
                    raise AssertionError(f'left private witness missing {v}')
                witness[v] = left_env[v]
            for v in C:
                if v not in right_env:
                    raise AssertionError(f'right private witness missing {v}')
                if v in witness:
                    raise AssertionError(f'witness overlap at {v}')
                witness[v] = right_env[v]
            if set(witness) != set(range(1, 3 * c.k + 1)):
                raise AssertionError('complete heterogeneous witness union failed')

            lv, lvo = v31.eval_system(left0, witness)
            rv, rvo = eval_right_source(c, witness)
            verification_ops += lvo + rvo
            witness_valid = lv and rv
            witness_source = 'COMMON_J_OBDD_PROOF_PLUS_RIGHT_OBDD_PROOF_PLUS_LEFT_AFFINE_PIVOTS'
            if not witness_valid:
                raise AssertionError('strict heterogeneous witness source verification failed')

        total_ops = ops_so_far + shared_projection_ops + witness_ops + verification_ops
        witness_bytes = base.json_bytes(witness or {})
        base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

        expected_left_models = 1 << (c.k - 1)
        expected_right_models = (1 << c.k) - 1 if c.right_kind == 'OR' else c.k
        expected_join_models = (1 << (c.k - 1)) - 1 if c.expected_sat else 0

        cert = {
            'control': c.name,
            'left_affine_sha256': v31.system_hash(left['rows']),
            'right_residual_root': int(right['root']),
            'right_constructor': right_constructor_proof,
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
            'right_language': 'INTERLEAVED_OBDD',
            'join_language': 'COMMON_FROZEN_ORDER_OBDD',
            'boundary_language_discovery': 'SUPPLIED_FROZEN_TYPES_ONLY',
            'input_bytes': c.input_bytes,
            'left_affine_private_project_exact': left_replay,
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
            'right_manager_nodes_total': len(right_bdd.nodes),
            'common_manager_nodes_total': len(common.nodes),
            'representation_bytes_peak': peak,
            'cumulative_state_bytes': cumulative,
            'proof_bytes': proof_bytes,
            'build_ops': left_build_ops + connectivity_ops + right_constructor_ops,
            'failed_discovery_ops': failed_discovery_ops,
            'left_private_projection_ops': int(left['projection_ops']),
            'right_private_projection_ops': int(right['projection_ops']),
            'affine_to_obdd_ops': int(conversion['ops']),
            'right_copy_ops': int(copied['ops']),
            'join_ops': join_ops,
            'shared_projection_ops': shared_projection_ops,
            'semantic_verification_ops': int(right_check['ops']) + int(semantic['ops']) + left_replay_ops,
            'witness_ops': witness_ops,
            'final_verification_ops': verification_ops,
            'total_charged_ops': total_ops,
            'certificate_sha256': canon_hash(cert),
            'witness': witness,
        }

    except base.CapHit as e:
        partial.update({
            'right_manager_nodes_total': 0 if right_bdd is None else len(right_bdd.nodes),
            'right_manager_ops': 0 if right_bdd is None else right_bdd.ops,
            'right_manager_bytes': 0 if right_bdd is None else manager_bytes(right_bdd),
            'common_manager_nodes_total': 0 if common is None else len(common.nodes),
            'common_manager_ops': 0 if common is None else common.ops,
            'common_manager_bytes': 0 if common is None else manager_bytes(common),
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
            'right_language': 'INTERLEAVED_OBDD',
            'join_language': 'COMMON_FROZEN_ORDER_OBDD',
            'boundary_language_discovery': 'SUPPLIED_FROZEN_TYPES_ONLY',
            'partial': partial,
            'claim': 'FINITE_HETEROGENEOUS_REPRESENTATION_ESCAPE_ONLY',
        }


def main(argv: Sequence[str]) -> int:
    rows = [run_control(c) for c in controls()]
    passed = [r for r in rows if r['status'] == 'PASS_EXACT_CLOSED']
    first_cap = next((r for r in rows if r['status'] == 'CAP_HIT'), None)

    result = {
        'artifact_id': 'PF5-NON-AFFINE-CONNECTED-BOUNDARY-V4',
        'protocol': 'PF5_NON_AFFINE_CONNECTED_BOUNDARY_GATE_V4.md',
        'claim_ceiling': 'P_VS_NP = OPEN',
        'widths_frozen_before_provider_run': list(WIDTHS),
        'caps': base.CAPS,
        'new_tuned_caps_added': False,
        'left_language': 'AFFINE_GF2',
        'right_languages': ['OR_INTERLEAVED_OBDD', 'EXACTLY_ONE_INTERLEAVED_OBDD'],
        'join_language': 'COMMON_FROZEN_ORDER_OBDD',
        'controls': rows,
        'all_passed_controls_exact': all(
            r['left_affine_private_project_exact']
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

    print('PF5_NON_AFFINE_CONNECTED_BOUNDARY_V4 = FROZEN')
    for r in rows:
        if r['status'] == 'PASS_EXACT_CLOSED':
            print(
                r['control'],
                'status=PASS_EXACT_CLOSED',
                'k=', r['k'],
                'right=', r['right_kind'],
                'models=', (r['left_models'], r['right_models'], r['join_models']),
                'right_nodes=', r['right_manager_nodes_total'],
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
    print('ALL_PASSED_CONTROLS_EXACT =', result['all_passed_controls_exact'])
    print('ALL_SAT_JOINED_BOUNDARIES_NON_AFFINE =', result['all_sat_joined_boundaries_non_affine'])
    print('FIRST_BASE_CAP_HIT =', result['first_base_cap_hit'])
    print('BOUNDARY_LANGUAGE_DISCOVERY = SUPPLIED_FROZEN_TYPES_ONLY')
    print('UNIVERSAL_CHEAP_LANGUAGE_SELECTION = OPEN')
    print('UNIVERSAL_CHEAP_CROSS_LANGUAGE_CONVERSION = OPEN')
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
