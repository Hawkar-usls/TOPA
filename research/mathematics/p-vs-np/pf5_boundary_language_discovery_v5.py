#!/usr/bin/env python3
"""PF5 boundary language discovery gate v5.

The discovery function receives only an exact neutral OBDD plus ordered roots.
It receives no fixture/family/language label. Fixed recognizer order:
AFFINE semantic -> SYMMETRIC_WEIGHT semantic -> exact OBDD fallback.
Every failed recognizer is charged. Successful structured representations are
independently compiled back to OBDD and checked for exact equivalence before
repeated existential projection.

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
import pf5_connected_boundary_adhesion_v3_1 as v31
import pf5_connected_boundary_adhesion_v3_2 as v32
import pf5_non_affine_connected_boundary_v4 as v4


WIDTHS = (3, 4, 6, 8, 10, 12, 14)
RECOGNIZER_ORDER = (
    'AFFINE_SEMANTIC',
    'SYMMETRIC_WEIGHT_SEMANTIC',
    'GENERIC_OBDD_FALLBACK',
)


@dataclass(frozen=True)
class Fixture:
    name: str
    k: int
    kind: str
    expected_lane: str

    @property
    def boundary(self) -> Tuple[int, ...]:
        return tuple(range(1, self.k + 1))


def fixtures() -> List[Fixture]:
    out: List[Fixture] = []
    for k in WIDTHS:
        out.extend([
            Fixture(f'BLIND_PARITY_K{k}', k, 'PARITY_EVEN', 'AFFINE_GF2'),
            Fixture(f'BLIND_OR_K{k}', k, 'OR', 'SYMMETRIC_WEIGHT_SET'),
            Fixture(f'BLIND_EX1_K{k}', k, 'EXACTLY_ONE', 'SYMMETRIC_WEIGHT_SET'),
            Fixture(f'BLIND_IMPL_K{k}', k, 'IMPLIES_1_2', 'GENERIC_OBDD_FALLBACK'),
        ])
    return out


def canon_hash(obj) -> str:
    return sha256(base.canon_json(obj).encode()).hexdigest()


def build_neutral_fixture(f: Fixture) -> Tuple[base.BDD, int, Dict, int]:
    b = base.BDD(f.boundary)
    calls = 0
    transitions = 0

    if f.kind == 'IMPLIES_1_2':
        before = b.ops
        b2 = b.mk(f.boundary[1], 0, 1)
        root = b.mk(f.boundary[0], 1, b2)
        proof = {
            'neutral_constructor': 'FIXTURE_BOOLEAN_DAG',
            'root': root,
            'order': list(f.boundary),
            'manager_sha256': canon_hash(v4.manager_payload(b)),
        }
        return b, root, proof, (b.ops - before) + 2

    memo: Dict[Tuple[int, int], int] = {}

    def update(state: int, bit: int) -> int:
        if f.kind == 'PARITY_EVEN':
            return state ^ bit
        if f.kind == 'OR':
            return int(bool(state or bit))
        if f.kind == 'EXACTLY_ONE':
            return min(2, state + bit)
        raise AssertionError(f.kind)

    def accept(state: int) -> bool:
        if f.kind == 'PARITY_EVEN':
            return state == 0
        if f.kind in ('OR', 'EXACTLY_ONE'):
            return state == 1
        raise AssertionError(f.kind)

    def rec(i: int, state: int) -> int:
        nonlocal calls, transitions
        calls += 1
        key = (i, state)
        if key in memo:
            return memo[key]
        if i == f.k:
            out = 1 if accept(state) else 0
            memo[key] = out
            return out
        lo = rec(i + 1, update(state, 0))
        hi = rec(i + 1, update(state, 1))
        transitions += 2
        out = b.mk(f.boundary[i], lo, hi)
        memo[key] = out
        return out

    before = b.ops
    root = rec(0, 0)
    proof = {
        'neutral_constructor': 'FIXTURE_FINITE_STATE_OBDD',
        'root': root,
        'order': list(f.boundary),
        'states': len(memo),
        'calls': calls,
        'transitions': transitions,
        'manager_sha256': canon_hash(v4.manager_payload(b)),
    }
    return b, root, proof, calls + transitions + (b.ops - before)


# ---------------------------------------------------------------------------
# Affine semantic recognition from OBDD Shannon structure
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AffineDesc:
    empty: bool
    anchor: int
    basis: Tuple[int, ...]


def canonical_basis(vectors: Iterable[int], k: int) -> Tuple[Tuple[int, ...], int]:
    slots = [0] * k
    ops = 0
    for original in vectors:
        x = int(original)
        if x == 0:
            ops += 1
            continue
        for p in range(k - 1, -1, -1):
            ops += 1
            if not (x & (1 << p)):
                continue
            if slots[p]:
                x ^= slots[p]
                ops += 1
            else:
                slots[p] = x
                # Gauss-Jordan: clear the new pivot from every other row.
                for q in range(k):
                    if q != p and slots[q] and (slots[q] & (1 << p)):
                        slots[q] ^= x
                        ops += 1
                break
    out = tuple(slots[p] for p in range(k - 1, -1, -1) if slots[p])
    return out, ops + len(out)


def add_free_directions(desc: AffineDesc, positions: Sequence[int], k: int) -> Tuple[AffineDesc, int]:
    if desc.empty:
        return desc, 1
    basis, ops = canonical_basis(list(desc.basis) + [1 << p for p in positions], k)
    return AffineDesc(False, desc.anchor, basis), ops + len(positions)


def affine_recognize(b: base.BDD, root: int, boundary: Sequence[int]) -> Dict:
    k = len(boundary)
    memo: Dict[Tuple[int, int], Optional[AffineDesc]] = {}
    transcript: List[Dict] = []
    ops = 0
    failure: Optional[Dict] = None

    def rec(u: int, level: int) -> Optional[AffineDesc]:
        nonlocal ops, failure
        key = (u, level)
        ops += 1
        if key in memo:
            return memo[key]
        if u == 0:
            out = AffineDesc(True, 0, tuple())
            memo[key] = out
            return out
        if u == 1:
            basis, z = canonical_basis((1 << p for p in range(level, k)), k)
            ops += z
            out = AffineDesc(False, 0, basis)
            memo[key] = out
            return out

        var, lo_id, hi_id = b.nodes[u]
        rank = b.rank[var]
        if rank < level:
            raise AssertionError('OBDD rank regression')
        if rank > level:
            inner = rec(u, rank)
            if inner is None:
                memo[key] = None
                return None
            out, z = add_free_directions(inner, tuple(range(level, rank)), k)
            ops += z
            transcript.append({
                'u': u, 'level': level, 'kind': 'SKIPPED_FREE',
                'to_rank': rank, 'basis_dim': len(out.basis),
            })
            memo[key] = out
            return out

        lo = rec(lo_id, level + 1)
        hi = rec(hi_id, level + 1)
        if lo is None or hi is None:
            memo[key] = None
            return None

        if lo.empty and hi.empty:
            out = AffineDesc(True, 0, tuple())
            kind = 'BOTH_EMPTY'
        elif lo.empty:
            out = AffineDesc(False, hi.anchor | (1 << level), hi.basis)
            kind = 'LOW_EMPTY_FIXED_ONE'
        elif hi.empty:
            out = AffineDesc(False, lo.anchor, lo.basis)
            kind = 'HIGH_EMPTY_FIXED_ZERO'
        else:
            ops += 1
            if lo.basis != hi.basis:
                failure = {
                    'u': u,
                    'level': level,
                    'reason': 'COFACTOR_DIRECTION_SPACES_DIFFER',
                    'low_basis_sha256': canon_hash(lo.basis),
                    'high_basis_sha256': canon_hash(hi.basis),
                }
                transcript.append(dict(failure))
                memo[key] = None
                return None
            bridge = (1 << level) | (lo.anchor ^ hi.anchor)
            basis, z = canonical_basis(list(lo.basis) + [bridge], k)
            ops += z
            out = AffineDesc(False, lo.anchor, basis)
            kind = 'PARALLEL_COSETS_JOINED'

        transcript.append({
            'u': u,
            'level': level,
            'kind': kind,
            'empty': out.empty,
            'anchor': out.anchor,
            'basis_sha256': canon_hash(out.basis),
            'basis_dim': len(out.basis),
        })
        memo[key] = out
        return out

    desc = rec(root, 0)
    proof = {
        'recognizer': 'AFFINE_SEMANTIC',
        'source_root': root,
        'source_manager_sha256': canon_hash(v4.manager_payload(b)),
        'memo_states': len(memo),
        'transcript': transcript,
        'failure': failure,
        'result': None if desc is None else {
            'empty': desc.empty,
            'anchor': desc.anchor,
            'basis': list(desc.basis),
        },
    }
    return {
        'accepted': desc is not None,
        'desc': desc,
        'ops': ops,
        'proof': proof,
        'proof_bytes': base.json_bytes(proof),
    }


def matrix_rref_local(rows: Sequence[int], k: int) -> Tuple[List[int], List[int], int]:
    work = [int(x) for x in rows if x]
    r = 0
    pivots: List[int] = []
    ops = len(work)
    for col in range(k):
        idx = None
        for i in range(r, len(work)):
            ops += 1
            if work[i] & (1 << col):
                idx = i
                break
        if idx is None:
            continue
        if idx != r:
            work[r], work[idx] = work[idx], work[r]
            ops += 1
        for i in range(len(work)):
            if i != r and (work[i] & (1 << col)):
                work[i] ^= work[r]
                ops += 1
        pivots.append(col)
        r += 1
        if r == len(work):
            break
    return work[:r], pivots, ops


def affine_desc_to_equations(desc: AffineDesc, boundary: Sequence[int]) -> Tuple[List[v31.Eq], Dict, int]:
    k = len(boundary)
    if desc.empty:
        rows = [v31.Eq(0, 1)]
        proof = {'kind': 'EMPTY_TO_CONTRADICTION', 'rows': [r.payload() for r in rows]}
        return rows, proof, 1

    rref_rows, pivots, ops = matrix_rref_local(desc.basis, k)
    free = [c for c in range(k) if c not in set(pivots)]
    orth: List[int] = []
    for f in free:
        h = 1 << f
        for row, p in zip(rref_rows, pivots):
            ops += 1
            if (row & h).bit_count() & 1:
                h |= 1 << p
        orth.append(h)

    eqs: List[v31.Eq] = []
    for h in orth:
        mask = 0
        for j, var in enumerate(boundary):
            ops += 1
            if h & (1 << j):
                mask ^= v31.bit(var)
        rhs = (h & desc.anchor).bit_count() & 1
        eqs.append(v31.Eq(mask, rhs))
    eqs = v31.canon_system(eqs)
    proof = {
        'kind': 'COSET_DIRECTION_ORTHOGONAL_COMPLEMENT',
        'anchor': desc.anchor,
        'basis': list(desc.basis),
        'orthogonal_basis': orth,
        'equations': [r.payload() for r in eqs],
    }
    return eqs, proof, ops + len(eqs)


# ---------------------------------------------------------------------------
# Symmetric Hamming-weight semantic recognition
# ---------------------------------------------------------------------------


def symmetric_recognize(b: base.BDD, root: int, boundary: Sequence[int]) -> Dict:
    k = len(boundary)
    memo: Dict[Tuple[int, int], Optional[Tuple[int, ...]]] = {}
    transcript: List[Dict] = []
    ops = 0
    failure: Optional[Dict] = None

    def rec(u: int, level: int) -> Optional[Tuple[int, ...]]:
        nonlocal ops, failure
        key = (u, level)
        ops += 1
        if key in memo:
            return memo[key]
        n = k - level
        if u == 0:
            out: Tuple[int, ...] = tuple()
            memo[key] = out
            return out
        if u == 1:
            out = tuple(range(0, n + 1))
            memo[key] = out
            return out
        if level >= k:
            failure = {'u': u, 'level': level, 'reason': 'NONTERMINAL_PAST_LAST_LEVEL'}
            memo[key] = None
            return None

        var, lo_id, hi_id = b.nodes[u]
        rank = b.rank[var]
        if rank < level:
            raise AssertionError('OBDD rank regression')
        if rank == level:
            low = rec(lo_id, level + 1)
            high = rec(hi_id, level + 1)
            source_kind = 'EXPLICIT_SHANNON'
        else:
            # The current variable is skipped: low and high are the same
            # residual. Treat it exactly as a Shannon node with equal children.
            low = rec(u, level + 1)
            high = low
            source_kind = 'SKIPPED_EQUAL_CHILDREN'

        if low is None or high is None:
            memo[key] = None
            return None
        W0, W1 = set(low), set(high)
        tail_n = n - 1
        for t in range(1, tail_n + 1):
            ops += 1
            if ((t in W0) != ((t - 1) in W1)):
                failure = {
                    'u': u,
                    'level': level,
                    'reason': 'HAMMING_WEIGHT_COMPATIBILITY_FAIL',
                    'total_weight': t,
                    'low_contains': t in W0,
                    'high_tail_contains': (t - 1) in W1,
                }
                transcript.append(dict(failure))
                memo[key] = None
                return None
        out_set = W0 | {w + 1 for w in W1}
        out = tuple(sorted(out_set))
        transcript.append({
            'u': u,
            'level': level,
            'kind': source_kind,
            'low_weights': list(low),
            'high_tail_weights': list(high),
            'weights': list(out),
        })
        memo[key] = out
        return out

    weights = rec(root, 0)
    proof = {
        'recognizer': 'SYMMETRIC_WEIGHT_SEMANTIC',
        'source_root': root,
        'source_manager_sha256': canon_hash(v4.manager_payload(b)),
        'memo_states': len(memo),
        'transcript': transcript,
        'failure': failure,
        'result_weights': None if weights is None else list(weights),
    }
    return {
        'accepted': weights is not None,
        'weights': weights,
        'ops': ops,
        'proof': proof,
        'proof_bytes': base.json_bytes(proof),
    }


def build_weight_bdd(weights: Sequence[int], boundary: Sequence[int]) -> Tuple[base.BDD, int, Dict, int]:
    b = base.BDD(boundary)
    W = set(int(w) for w in weights)
    memo: Dict[Tuple[int, int], int] = {}
    calls = 0

    def rec(i: int, count: int) -> int:
        nonlocal calls
        calls += 1
        key = (i, count)
        if key in memo:
            return memo[key]
        if i == len(boundary):
            out = 1 if count in W else 0
            memo[key] = out
            return out
        lo = rec(i + 1, count)
        hi = rec(i + 1, count + 1)
        out = b.mk(boundary[i], lo, hi)
        memo[key] = out
        return out

    before = b.ops
    root = rec(0, 0)
    proof = {
        'constructor': 'SYMMETRIC_WEIGHT_SET_TO_OBDD',
        'weights': sorted(W),
        'root': root,
        'states': len(memo),
        'calls': calls,
    }
    return b, root, proof, calls + (b.ops - before)


def bdd_equivalent(
    a: base.BDD, ar: int, b: base.BDD, br: int
) -> Tuple[bool, int, int]:
    memo: Dict[Tuple[int, int], bool] = {}
    ops = 0

    def top_rank(m: base.BDD, u: int) -> int:
        if u in (0, 1):
            return 10**9
        return m.rank[m.nodes[u][0]]

    def branches(m: base.BDD, u: int, rank: int) -> Tuple[int, int]:
        if u in (0, 1) or top_rank(m, u) > rank:
            return u, u
        v, lo, hi = m.nodes[u]
        if m.rank[v] != rank:
            raise AssertionError('unexpected BDD rank')
        return lo, hi

    def rec(u: int, v: int) -> bool:
        nonlocal ops
        ops += 1
        key = (u, v)
        if key in memo:
            return memo[key]
        if u in (0, 1) and v in (0, 1):
            out = u == v
            memo[key] = out
            return out
        r = min(top_rank(a, u), top_rank(b, v))
        ul, uh = branches(a, u, r)
        vl, vh = branches(b, v, r)
        out = rec(ul, vl) and rec(uh, vh)
        memo[key] = out
        return out

    ok = rec(ar, br)
    return ok, ops, len(memo)


def verify_affine_conversion(
    source: base.BDD,
    source_root: int,
    desc: AffineDesc,
    boundary: Sequence[int],
) -> Dict:
    eqs, eq_proof, eq_ops = affine_desc_to_equations(desc, boundary)
    dst = base.BDD(boundary)
    compiled = v4.compile_affine_to_common(eqs, boundary, dst)
    ok, eqv_ops, pair_states = bdd_equivalent(source, source_root, dst, int(compiled['root']))
    proof = {
        'equation_derivation': eq_proof,
        'compile_proof': compiled['proof'],
        'equivalence_pair_states': pair_states,
        'equivalent': ok,
    }
    return {
        'equivalent': ok,
        'equations': eqs,
        'ops': eq_ops + int(compiled['ops']) + eqv_ops,
        'proof': proof,
        'proof_bytes': base.json_bytes(proof),
        'representation_bytes': v31.system_bytes(eqs),
    }


def verify_symmetric_conversion(
    source: base.BDD,
    source_root: int,
    weights: Sequence[int],
    boundary: Sequence[int],
) -> Dict:
    dst, root, constructor_proof, build_ops = build_weight_bdd(weights, boundary)
    ok, eqv_ops, pair_states = bdd_equivalent(source, source_root, dst, root)
    proof = {
        'constructor': constructor_proof,
        'destination_manager_sha256': canon_hash(v4.manager_payload(dst)),
        'equivalence_pair_states': pair_states,
        'equivalent': ok,
    }
    return {
        'equivalent': ok,
        'weights': tuple(int(w) for w in weights),
        'ops': build_ops + eqv_ops,
        'proof': proof,
        'proof_bytes': base.json_bytes(proof),
        'representation_bytes': base.json_bytes({'n': len(boundary), 'weights': list(weights)}),
    }


# ---------------------------------------------------------------------------
# Blind discovery. IMPORTANT: no fixture kind/name argument exists here.
# ---------------------------------------------------------------------------


def discover_language(source: base.BDD, root: int, boundary: Sequence[int]) -> Dict:
    attempts: List[Dict] = []
    failed_ops = 0
    failed_proof_bytes = 0
    total_ops = 0
    total_proof_bytes = 0

    affine = affine_recognize(source, root, boundary)
    total_ops += int(affine['ops'])
    total_proof_bytes += int(affine['proof_bytes'])
    if affine['accepted']:
        conv = verify_affine_conversion(source, root, affine['desc'], boundary)
        total_ops += int(conv['ops'])
        total_proof_bytes += int(conv['proof_bytes'])
        if not conv['equivalent']:
            raise AssertionError('accepted affine recognizer failed equivalence certificate')
        attempts.append({
            'recognizer': 'AFFINE_SEMANTIC',
            'status': 'ACCEPT_EQUIVALENT',
            'ops': int(affine['ops']) + int(conv['ops']),
            'proof_bytes': int(affine['proof_bytes']) + int(conv['proof_bytes']),
        })
        return {
            'lane': 'AFFINE_GF2',
            'payload': conv['equations'],
            'attempts': attempts,
            'failed_recognizer_ops': failed_ops,
            'failed_recognizer_proof_bytes': failed_proof_bytes,
            'discovery_ops': total_ops,
            'discovery_proof_bytes': total_proof_bytes,
            'selected_representation_bytes': int(conv['representation_bytes']),
            'equivalent': True,
        }

    attempts.append({
        'recognizer': 'AFFINE_SEMANTIC',
        'status': 'REJECT',
        'ops': int(affine['ops']),
        'proof_bytes': int(affine['proof_bytes']),
        'failure': affine['proof']['failure'],
    })
    failed_ops += int(affine['ops'])
    failed_proof_bytes += int(affine['proof_bytes'])

    sym = symmetric_recognize(source, root, boundary)
    total_ops += int(sym['ops'])
    total_proof_bytes += int(sym['proof_bytes'])
    if sym['accepted']:
        conv = verify_symmetric_conversion(source, root, sym['weights'], boundary)
        total_ops += int(conv['ops'])
        total_proof_bytes += int(conv['proof_bytes'])
        if not conv['equivalent']:
            raise AssertionError('accepted symmetric recognizer failed equivalence certificate')
        attempts.append({
            'recognizer': 'SYMMETRIC_WEIGHT_SEMANTIC',
            'status': 'ACCEPT_EQUIVALENT',
            'ops': int(sym['ops']) + int(conv['ops']),
            'proof_bytes': int(sym['proof_bytes']) + int(conv['proof_bytes']),
        })
        return {
            'lane': 'SYMMETRIC_WEIGHT_SET',
            'payload': conv['weights'],
            'attempts': attempts,
            'failed_recognizer_ops': failed_ops,
            'failed_recognizer_proof_bytes': failed_proof_bytes,
            'discovery_ops': total_ops,
            'discovery_proof_bytes': total_proof_bytes,
            'selected_representation_bytes': int(conv['representation_bytes']),
            'equivalent': True,
        }

    attempts.append({
        'recognizer': 'SYMMETRIC_WEIGHT_SEMANTIC',
        'status': 'REJECT',
        'ops': int(sym['ops']),
        'proof_bytes': int(sym['proof_bytes']),
        'failure': sym['proof']['failure'],
    })
    failed_ops += int(sym['ops'])
    failed_proof_bytes += int(sym['proof_bytes'])

    fallback_proof = {
        'recognizer': 'GENERIC_OBDD_FALLBACK',
        'source_root': root,
        'source_manager_sha256': canon_hash(v4.manager_payload(source)),
        'equivalence': 'IDENTITY',
    }
    fallback_ops = 1
    fallback_proof_bytes = base.json_bytes(fallback_proof)
    attempts.append({
        'recognizer': 'GENERIC_OBDD_FALLBACK',
        'status': 'ACCEPT_IDENTITY',
        'ops': fallback_ops,
        'proof_bytes': fallback_proof_bytes,
    })
    total_ops += fallback_ops
    total_proof_bytes += fallback_proof_bytes
    return {
        'lane': 'GENERIC_OBDD_FALLBACK',
        'payload': {'source': source, 'root': root},
        'attempts': attempts,
        'failed_recognizer_ops': failed_ops,
        'failed_recognizer_proof_bytes': failed_proof_bytes,
        'discovery_ops': total_ops,
        'discovery_proof_bytes': total_proof_bytes,
        'selected_representation_bytes': v4.manager_bytes(source),
        'equivalent': True,
    }


# ---------------------------------------------------------------------------
# Projection in discovered languages
# ---------------------------------------------------------------------------


def project_affine_all(
    equations: Sequence[v31.Eq], boundary: Sequence[int], prior_ops: int, prior_proof_bytes: int
) -> Dict:
    current = list(equations)
    proof: List[Dict] = []
    ops = 0
    peak = v31.system_bytes(current)
    cumulative = peak
    for x in boundary:
        current, rec, z = v31.project_var(current, x)
        ops += z
        proof.append(rec)
        sb = v31.system_bytes(current)
        peak = max(peak, sb)
        cumulative += sb
        base.check_common_caps(
            peak, prior_proof_bytes + base.json_bytes(proof), cumulative, prior_ops + ops
        )
    final_scalar = not v32.is_contradiction(current)
    if final_scalar and current:
        raise AssertionError('affine full projection remained constrained')
    return {
        'final_scalar': final_scalar,
        'proof': proof,
        'ops': ops,
        'proof_bytes': base.json_bytes(proof),
        'peak': peak,
        'cumulative': cumulative,
        'terminal': [r.payload() for r in current],
    }


def project_symmetric_all(
    weights: Sequence[int], boundary: Sequence[int], prior_ops: int, prior_proof_bytes: int
) -> Dict:
    W = set(int(w) for w in weights)
    n = len(boundary)
    proof: List[Dict] = []
    ops = 0
    peak = base.json_bytes({'n': n, 'weights': sorted(W)})
    cumulative = peak
    for x in boundary:
        before = set(W)
        after: Set[int] = set()
        for w in range(0, n):
            ops += 1
            if w in before or (w + 1) in before:
                after.add(w)
        rec = {
            'x': int(x),
            'n_before': n,
            'weights_before': sorted(before),
            'weights_after': sorted(after),
        }
        proof.append(rec)
        W = after
        n -= 1
        sb = base.json_bytes({'n': n, 'weights': sorted(W)})
        peak = max(peak, sb)
        cumulative += sb
        base.check_common_caps(
            peak, prior_proof_bytes + base.json_bytes(proof), cumulative, prior_ops + ops
        )
    if n != 0:
        raise AssertionError('symmetric projection did not consume all roots')
    return {
        'final_scalar': 0 in W,
        'proof': proof,
        'ops': ops,
        'proof_bytes': base.json_bytes(proof),
        'peak': peak,
        'cumulative': cumulative,
        'terminal_weights': sorted(W),
    }


def lift_symmetric_witness(proof: Sequence[Dict]) -> Tuple[Dict[int, bool], int]:
    env: Dict[int, bool] = {}
    ops = 0
    for rec in reversed(proof):
        before = set(int(w) for w in rec['weights_before'])
        tail_weight = sum(int(v) for v in env.values())
        ops += len(env) + 1
        x = int(rec['x'])
        if tail_weight in before:
            env[x] = False
        elif (tail_weight + 1) in before:
            env[x] = True
        else:
            raise AssertionError(f'symmetric witness lift failed at {x}')
    return env, ops


def run_fixture(f: Fixture) -> Dict:
    source, root, constructor_proof, build_ops = build_neutral_fixture(f)
    source_bytes = v4.manager_bytes(source)
    constructor_proof_bytes = base.json_bytes(constructor_proof)
    input_sha = canon_hash({
        'root': root,
        'order': list(f.boundary),
        'manager': v4.manager_payload(source),
    })
    base.check_common_caps(source_bytes, constructor_proof_bytes, source_bytes, build_ops)

    # Blind call: no fixture kind/name/expected lane enters this function.
    discovered = discover_language(source, root, f.boundary)
    if not discovered['equivalent']:
        raise AssertionError('selected representation lacks equivalence proof')

    prior_ops = build_ops + int(discovered['discovery_ops'])
    prior_proof_bytes = constructor_proof_bytes + int(discovered['discovery_proof_bytes'])

    lane = discovered['lane']
    if lane == 'AFFINE_GF2':
        projected = project_affine_all(
            discovered['payload'], f.boundary, prior_ops, prior_proof_bytes
        )
        final_scalar = bool(projected['final_scalar'])
        witness: Optional[Dict[int, bool]] = None
        witness_ops = 0
        if final_scalar:
            witness, witness_ops = v31.lift_private(projected['proof'], {})
        projection_peak = int(projected['peak'])
        projection_cumulative = int(projected['cumulative'])
        projection_proof_bytes = int(projected['proof_bytes'])
        projection_ops = int(projected['ops'])
        witness_source = 'DISCOVERED_AFFINE_PIVOT_PROOF'
    elif lane == 'SYMMETRIC_WEIGHT_SET':
        projected = project_symmetric_all(
            discovered['payload'], f.boundary, prior_ops, prior_proof_bytes
        )
        final_scalar = bool(projected['final_scalar'])
        witness = None
        witness_ops = 0
        if final_scalar:
            witness, witness_ops = lift_symmetric_witness(projected['proof'])
        projection_peak = int(projected['peak'])
        projection_cumulative = int(projected['cumulative'])
        projection_proof_bytes = int(projected['proof_bytes'])
        projection_ops = int(projected['ops'])
        witness_source = 'DISCOVERED_SYMMETRIC_WEIGHT_PROOF'
    elif lane == 'GENERIC_OBDD_FALLBACK':
        projected = v4.project_common_boundary(
            source,
            root,
            f.boundary,
            prior_ops,
            prior_proof_bytes,
            source_bytes,
            source_bytes,
        )
        final_root = int(projected['root'])
        if final_root not in (0, 1):
            raise AssertionError('fallback full projection nonterminal')
        final_scalar = bool(final_root)
        witness = None
        witness_ops = 0
        if final_scalar:
            witness, witness_ops = v4.lift_bdd_projection_witness(source, projected['proof'], {})
        projection_peak = int(projected['representation_bytes_peak'])
        projection_cumulative = int(projected['cumulative_state_bytes'])
        projection_proof_bytes = int(projected['proof_bytes'])
        projection_ops = int(projected['ops'])
        witness_source = 'DISCOVERED_GENERIC_OBDD_PROJECTION_PROOF'
    else:
        raise AssertionError(lane)

    if not final_scalar:
        raise AssertionError('all frozen v5 neutral fixtures are satisfiable')
    if witness is None or set(witness) != set(f.boundary):
        raise AssertionError('discovered-language witness incomplete')
    witness_ok, verify_ops = v3.eval_bdd_count(source, root, witness)
    if not witness_ok:
        raise AssertionError('discovered-language witness fails neutral source')

    total_ops = prior_ops + projection_ops + witness_ops + verify_ops
    proof_bytes = prior_proof_bytes + projection_proof_bytes
    peak = max(source_bytes, int(discovered['selected_representation_bytes']), projection_peak)
    cumulative = source_bytes + int(discovered['selected_representation_bytes']) + projection_cumulative
    witness_bytes = base.json_bytes(witness)
    base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

    attempts = discovered['attempts']
    failed_attempts = [a for a in attempts if a['status'] == 'REJECT']
    failed_work_charged = (
        int(discovered['failed_recognizer_ops']) == sum(int(a['ops']) for a in failed_attempts)
        and int(discovered['failed_recognizer_proof_bytes']) == sum(int(a['proof_bytes']) for a in failed_attempts)
    )

    cert = {
        'discovery_input_sha256': input_sha,
        'recognizer_order': list(RECOGNIZER_ORDER),
        'attempts': attempts,
        'selected_lane': lane,
        'projection_proof_sha256': canon_hash(projected['proof']),
        'witness_sha256': canon_hash(witness),
    }

    return {
        'fixture': f.name,
        'k': f.k,
        'external_kind_for_test_only': f.kind,
        'expected_lane_external_test_only': f.expected_lane,
        'status': 'PASS_EXACT_CLOSED',
        'discovery_input_unlabeled': True,
        'discovery_input_sha256': input_sha,
        'fixed_recognizer_order_used': [a['recognizer'] for a in attempts] == list(RECOGNIZER_ORDER[:len(attempts)]),
        'recognizer_attempts': attempts,
        'selected_lane': lane,
        'lane_matches_frozen_expectation': lane == f.expected_lane,
        'all_failed_recognizer_work_charged': failed_work_charged,
        'failed_recognizer_ops': int(discovered['failed_recognizer_ops']),
        'failed_recognizer_proof_bytes': int(discovered['failed_recognizer_proof_bytes']),
        'selected_representation_equivalent': True,
        'selected_representation_project_closed': True,
        'final_scalar': final_scalar,
        'strict_discovered_language_witness': witness_ok,
        'witness_source': witness_source,
        'witness_bytes': witness_bytes,
        'source_obdd_nodes': len(source.nodes),
        'representation_bytes_peak': peak,
        'cumulative_state_bytes': cumulative,
        'proof_bytes': proof_bytes,
        'build_ops': build_ops,
        'discovery_ops': int(discovered['discovery_ops']),
        'projection_ops': projection_ops,
        'witness_ops': witness_ops,
        'verification_ops': verify_ops,
        'total_charged_ops': total_ops,
        'certificate_sha256': canon_hash(cert),
        'witness': witness,
    }


def main(argv: Sequence[str]) -> int:
    rows: List[Dict] = []
    first_cap: Optional[Dict] = None
    for f in fixtures():
        try:
            rows.append(run_fixture(f))
        except base.CapHit as e:
            rec = {
                'fixture': f.name,
                'k': f.k,
                'external_kind_for_test_only': f.kind,
                'expected_lane_external_test_only': f.expected_lane,
                'status': 'CAP_HIT',
                'cap_reason': str(e),
                'claim': 'FINITE_DISCOVERY_PORTFOLIO_ESCAPE_ONLY',
            }
            rows.append(rec)
            if first_cap is None:
                first_cap = rec

    passed = [r for r in rows if r['status'] == 'PASS_EXACT_CLOSED']
    result = {
        'artifact_id': 'PF5-BOUNDARY-LANGUAGE-DISCOVERY-V5',
        'protocol': 'PF5_BOUNDARY_LANGUAGE_DISCOVERY_GATE_V5.md',
        'claim_ceiling': 'P_VS_NP = OPEN',
        'widths_frozen_before_provider_run': list(WIDTHS),
        'recognizer_order_frozen_before_provider_run': list(RECOGNIZER_ORDER),
        'caps': base.CAPS,
        'new_tuned_caps_added': False,
        'controls': rows,
        'passed_controls': len(passed),
        'all_passed_discovery_inputs_unlabeled': all(r['discovery_input_unlabeled'] for r in passed) if passed else False,
        'all_passed_fixed_recognizer_order': all(r['fixed_recognizer_order_used'] for r in passed) if passed else False,
        'all_passed_failed_work_charged': all(r['all_failed_recognizer_work_charged'] for r in passed) if passed else False,
        'all_passed_selected_equivalent': all(r['selected_representation_equivalent'] for r in passed) if passed else False,
        'all_passed_project_closed': all(r['selected_representation_project_closed'] for r in passed) if passed else False,
        'all_passed_strict_witness': all(r['strict_discovered_language_witness'] for r in passed) if passed else False,
        'blind_lane_selection_matches_frozen_expectation': all(r['lane_matches_frozen_expectation'] for r in passed) if passed else False,
        'first_base_cap_hit': first_cap,
        'universal_recognizer_portfolio_complete': 'OPEN',
        'universal_polynomial_discovery': 'OPEN',
        'universal_polynomial_coverage': 'OPEN',
        'global_progress_amortization': 'OPEN',
        'representation_lower_bound': 'NOT_ESTABLISHED',
        'p_vs_np': 'OPEN',
    }
    result['result_sha256'] = canon_hash(result)

    print('PF5_BOUNDARY_LANGUAGE_DISCOVERY_V5 = FROZEN')
    for r in rows:
        if r['status'] == 'PASS_EXACT_CLOSED':
            print(
                r['fixture'],
                'status=PASS_EXACT_CLOSED',
                'k=', r['k'],
                'selected=', r['selected_lane'],
                'attempts=', [(a['recognizer'], a['status']) for a in r['recognizer_attempts']],
                'failed_ops=', r['failed_recognizer_ops'],
                'peak=', r['representation_bytes_peak'],
                'ops=', r['total_charged_ops'],
                'witness=', r['witness_source'],
            )
        else:
            print(r['fixture'], 'status=CAP_HIT', 'k=', r['k'], 'cap=', r['cap_reason'])
    print('BLIND_LANE_SELECTION_MATCHES_FROZEN_EXPECTATION =', result['blind_lane_selection_matches_frozen_expectation'])
    print('ALL_FAILED_RECOGNIZER_WORK_CHARGED =', result['all_passed_failed_work_charged'])
    print('FIRST_BASE_CAP_HIT =', result['first_base_cap_hit'])
    print('UNIVERSAL_RECOGNIZER_PORTFOLIO_COMPLETE = OPEN')
    print('UNIVERSAL_POLYNOMIAL_DISCOVERY = OPEN')
    print('P_VS_NP = OPEN')
    print('RESULT_SHA256 =', result['result_sha256'])

    if '--json-out' in argv:
        i = list(argv).index('--json-out')
        with open(argv[i + 1], 'w', encoding='utf-8') as fh:
            json.dump(result, fh, indent=2, sort_keys=True)
            fh.write('\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
