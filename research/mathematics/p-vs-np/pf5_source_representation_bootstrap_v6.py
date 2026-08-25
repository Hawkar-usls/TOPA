#!/usr/bin/env python3
"""PF5 source representation bootstrap gate v6.

Discovery starts from neutral CNF bytes, declared variables and one frozen
order. No prebuilt OBDD and no family/language tag enters the bootstrap API.
Frozen portfolio:
  SIGNED_PARITY_GRAPH_CNF -> GENERIC_FROZEN_ORDER_OBDD

The signed-parity lane recognizes paired binary CNF encodings of u XOR v = p,
compresses them into canonical signed components, supports exact existential
projection by deletion/rerooting, and reconstructs witnesses from projection
proofs. Generic OBDD construction is paid only when the structural recognizer
rejects.

Finite mechanics only. P vs NP remains open.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pf5_boundary_coverage_matrix_v0 as base
import pf5_non_affine_connected_boundary_v4 as v4


WIDTHS = (4, 6, 8, 10, 12, 14)
BOOTSTRAP_ORDER = ('SIGNED_PARITY_GRAPH_CNF', 'GENERIC_FROZEN_ORDER_OBDD')

Clause = Tuple[int, ...]
CNF = Tuple[Clause, ...]


@dataclass(frozen=True)
class SourceFixture:
    name: str
    n: int
    kind: str
    expected_lane: str
    expected_sat: bool
    variables: Tuple[int, ...]
    order: Tuple[int, ...]
    clauses: CNF


def canon_clause(lits: Iterable[int]) -> Clause:
    vals = tuple(sorted((int(x) for x in lits), key=lambda z: (abs(z), z < 0)))
    if len({abs(x) for x in vals}) != len(vals):
        raise ValueError(f'repeated variable in clause {vals}')
    return vals


def canon_cnf(clauses: Iterable[Iterable[int]]) -> CNF:
    rows = [canon_clause(c) for c in clauses]
    if len(set(rows)) != len(rows):
        raise ValueError('duplicate source clause')
    return tuple(sorted(rows))


def shuffled_cnf(clauses: Iterable[Iterable[int]], tag: str) -> CNF:
    rows = [canon_clause(c) for c in clauses]
    if len(set(rows)) != len(rows):
        raise ValueError('duplicate source clause')
    return tuple(sorted(rows, key=lambda c: sha256((tag + '|' + repr(c)).encode()).hexdigest()))


def parity_edge_clauses(u: int, v: int, p: int) -> Tuple[Clause, Clause]:
    if u == v:
        raise ValueError('self parity edge')
    if p == 0:
        return canon_clause((-u, v)), canon_clause((u, -v))
    if p == 1:
        return canon_clause((u, v)), canon_clause((-u, -v))
    raise ValueError(p)


def make_fixtures() -> List[SourceFixture]:
    out: List[SourceFixture] = []
    for n in WIDTHS:
        # Signed blocked-pair SAT canary. Variable order is X block then Y block.
        pair_clauses: List[Clause] = []
        for i in range(1, n + 1):
            p = i & 1
            pair_clauses.extend(parity_edge_clauses(i, n + i, p))
        pair_vars = tuple(range(1, 2 * n + 1))
        out.append(SourceFixture(
            f'CNF_SIGNED_BLOCKED_PAIRS_N{n}', n, 'SIGNED_BLOCKED_PAIRS',
            'SIGNED_PARITY_COMPONENTS', True,
            pair_vars, pair_vars,
            shuffled_cnf(pair_clauses, f'PF5-V6-PAIRS-{n}'),
        ))

        # Contradictory signed cycle; remaining roots are attached consistently.
        cycle_edges: List[Tuple[int, int, int]] = [(1, 2, 0), (2, 3, 0), (1, 3, 1)]
        for i in range(3, n):
            cycle_edges.append((i, i + 1, (i + n) & 1))
        cycle_clauses: List[Clause] = []
        for u, v, p in cycle_edges:
            cycle_clauses.extend(parity_edge_clauses(u, v, p))
        vars_n = tuple(range(1, n + 1))
        out.append(SourceFixture(
            f'CNF_SIGNED_CYCLE_UNSAT_N{n}', n, 'SIGNED_CYCLE_UNSAT',
            'SIGNED_PARITY_COMPONENTS', False,
            vars_n, vars_n,
            shuffled_cnf(cycle_clauses, f'PF5-V6-CYCLE-{n}'),
        ))

        # Wide OR must reject parity graph and use generic source-to-OBDD bootstrap.
        out.append(SourceFixture(
            f'CNF_WIDE_OR_N{n}', n, 'WIDE_OR',
            'GENERIC_FROZEN_ORDER_OBDD', True,
            vars_n, vars_n,
            canon_cnf([vars_n]),
        ))
    return out


def cnf_payload(clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int]) -> Dict:
    return {
        'variables': list(variables),
        'order': list(order),
        'clauses': [list(c) for c in clauses],
    }


def cnf_bytes(clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int]) -> int:
    return base.json_bytes(cnf_payload(clauses, variables, order))


def cnf_hash(clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int]) -> str:
    return sha256(base.canon_json(cnf_payload(clauses, variables, order)).encode()).hexdigest()


def eval_cnf(clauses: Sequence[Clause], env: Dict[int, bool]) -> Tuple[bool, int]:
    ops = 0
    for clause in clauses:
        sat = False
        for lit in clause:
            ops += 1
            val = bool(env[abs(lit)])
            if val == (lit > 0):
                sat = True
                break
        if not sat:
            return False, ops
    return True, ops


# ---------------------------------------------------------------------------
# Signed parity source recognizer
# ---------------------------------------------------------------------------


def sign_pattern(clause: Clause, u: int, v: int) -> Tuple[int, int]:
    d = {abs(l): 1 if l > 0 else -1 for l in clause}
    return d[u], d[v]


def edge_clauses_canonical(u: int, v: int, p: int) -> Set[Clause]:
    return set(parity_edge_clauses(u, v, p))


def component_state_payload(state: Dict) -> Dict:
    return {
        'false': bool(state['false']),
        'components': [
            {
                'root': int(c['root']),
                'members': [[int(v), int(p)] for v, p in c['members']],
            }
            for c in state['components']
        ],
    }


def component_state_bytes(state: Dict) -> int:
    return base.json_bytes(component_state_payload(state))


def component_state_hash(state: Dict) -> str:
    return sha256(base.canon_json(component_state_payload(state)).encode()).hexdigest()


def recognize_signed_parity_graph(
    clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int]
) -> Dict:
    ops = 0
    proof: Dict = {
        'recognizer': 'SIGNED_PARITY_GRAPH_CNF',
        'source_sha256': cnf_hash(clauses, variables, order),
        'groups': [],
        'reject': None,
    }

    varset = set(int(v) for v in variables)
    if set(order) != varset or len(order) != len(varset):
        proof['reject'] = {'reason': 'ORDER_VARIABLE_SET_MISMATCH'}
        return {'accepted': False, 'ops': 1, 'proof': proof, 'proof_bytes': base.json_bytes(proof)}

    groups: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {}
    clause_by_group: Dict[Tuple[int, int], Set[Clause]] = {}
    for idx, clause in enumerate(clauses):
        ops += 1
        if len(clause) != 2:
            proof['reject'] = {'reason': 'NON_BINARY_CLAUSE', 'index': idx, 'clause': list(clause)}
            return {'accepted': False, 'ops': ops, 'proof': proof, 'proof_bytes': base.json_bytes(proof)}
        u, v = sorted((abs(clause[0]), abs(clause[1])))
        if u == v or u not in varset or v not in varset:
            proof['reject'] = {'reason': 'INVALID_BINARY_PAIR', 'index': idx, 'clause': list(clause)}
            return {'accepted': False, 'ops': ops, 'proof': proof, 'proof_bytes': base.json_bytes(proof)}
        pat = sign_pattern(clause, u, v)
        groups.setdefault((u, v), set()).add(pat)
        clause_by_group.setdefault((u, v), set()).add(tuple(clause))
        ops += 2

    edges: List[Tuple[int, int, int]] = []
    consumed: Set[Clause] = set()
    eq0 = {(-1, 1), (1, -1)}
    eq1 = {(1, 1), (-1, -1)}
    for pair in sorted(groups):
        pats = groups[pair]
        ops += 1
        if pats == eq0 and len(clause_by_group[pair]) == 2:
            p = 0
        elif pats == eq1 and len(clause_by_group[pair]) == 2:
            p = 1
        else:
            proof['groups'].append({
                'pair': list(pair), 'patterns': sorted([list(x) for x in pats]),
                'status': 'REJECT_INCOMPLETE_OR_CONFLICTING_PARITY_ENCODING',
            })
            proof['reject'] = {'reason': 'PAIR_NOT_EXACT_PARITY_ENCODING', 'pair': list(pair)}
            return {'accepted': False, 'ops': ops, 'proof': proof, 'proof_bytes': base.json_bytes(proof)}
        u, v = pair
        edges.append((u, v, p))
        consumed |= clause_by_group[pair]
        proof['groups'].append({'pair': [u, v], 'parity': p, 'status': 'ACCEPT_EDGE'})
        ops += 2

    if set(clauses) != consumed:
        proof['reject'] = {'reason': 'UNCONSUMED_SOURCE_CLAUSE'}
        return {'accepted': False, 'ops': ops + len(clauses), 'proof': proof, 'proof_bytes': base.json_bytes(proof)}

    # Exact source round-trip from recognized signed edges.
    rebuilt: Set[Clause] = set()
    for u, v, p in edges:
        rebuilt |= edge_clauses_canonical(u, v, p)
        ops += 2
    roundtrip_exact = rebuilt == set(clauses)
    if not roundtrip_exact:
        proof['reject'] = {'reason': 'SOURCE_ROUNDTRIP_MISMATCH'}
        return {'accepted': False, 'ops': ops, 'proof': proof, 'proof_bytes': base.json_bytes(proof)}

    # Deterministic signed-component traversal.
    adj: Dict[int, List[Tuple[int, int]]] = {int(v): [] for v in variables}
    for u, v, p in edges:
        adj[u].append((v, p))
        adj[v].append((u, p))
        ops += 2
    for v in adj:
        adj[v].sort()

    seen: Set[int] = set()
    components: List[Dict] = []
    contradiction: Optional[Dict] = None
    traversal: List[Dict] = []
    for root in sorted(varset):
        if root in seen:
            continue
        offsets: Dict[int, int] = {root: 0}
        queue = [root]
        seen.add(root)
        while queue:
            u = queue.pop(0)
            ops += 1
            for v, p in adj[u]:
                want = offsets[u] ^ p
                ops += 1
                if v not in offsets:
                    offsets[v] = want
                    seen.add(v)
                    queue.append(v)
                    traversal.append({'from': u, 'to': v, 'edge_parity': p, 'assigned_offset': want})
                elif offsets[v] != want:
                    contradiction = {
                        'u': u, 'v': v, 'edge_parity': p,
                        'offset_u': offsets[u], 'offset_v': offsets[v],
                        'required_offset_v': want,
                    }
                    traversal.append({'conflict': dict(contradiction)})
                    break
            if contradiction is not None:
                break
        members = tuple(sorted((int(v), int(p)) for v, p in offsets.items()))
        components.append({'root': root, 'members': members})
        if contradiction is not None:
            break

    # If contradiction happened early, component coverage is irrelevant because
    # the exact conjunction is already FALSE.
    if contradiction is not None:
        state = {'false': True, 'components': []}
    else:
        # Include any isolated declared variable as singleton component; traversal already did.
        state = {'false': False, 'components': sorted(components, key=lambda c: c['root'])}
        if {v for c in state['components'] for v, _ in c['members']} != varset:
            raise AssertionError('component traversal failed variable coverage')
        # Verify every recognized edge against canonical offsets.
        lookup: Dict[int, Tuple[int, int]] = {}
        for c in state['components']:
            for v, p in c['members']:
                lookup[v] = (c['root'], p)
        for u, v, p in edges:
            ops += 1
            if lookup[u][0] != lookup[v][0] or (lookup[u][1] ^ lookup[v][1]) != p:
                raise AssertionError('consistent edge not represented by component offsets')

    proof.update({
        'signed_edges': [[u, v, p] for u, v, p in edges],
        'roundtrip_exact': roundtrip_exact,
        'roundtrip_sha256': sha256(base.canon_json(sorted([list(c) for c in rebuilt])).encode()).hexdigest(),
        'traversal': traversal,
        'contradiction': contradiction,
        'state_sha256': component_state_hash(state),
    })
    return {
        'accepted': True,
        'ops': ops,
        'proof': proof,
        'proof_bytes': base.json_bytes(proof),
        'state': state,
        'source_equivalence_exact': roundtrip_exact,
    }


# ---------------------------------------------------------------------------
# Signed component projection + witness
# ---------------------------------------------------------------------------


def project_component_var(state: Dict, x: int) -> Tuple[Dict, Dict, int]:
    before_hash = component_state_hash(state)
    if state['false']:
        out = {'false': True, 'components': []}
        proof = {
            'x': int(x), 'mode': 'FALSE_STICKY',
            'before_sha256': before_hash, 'after_sha256': component_state_hash(out),
            'lift_to_var': None, 'lift_parity': None,
        }
        return out, proof, 1

    comps = [
        {'root': int(c['root']), 'members': tuple((int(v), int(p)) for v, p in c['members'])}
        for c in state['components']
    ]
    ops = 0
    idx = None
    for i, c in enumerate(comps):
        ops += 1
        if any(v == x for v, _ in c['members']):
            idx = i
            break
    if idx is None:
        raise AssertionError(f'project root {x} absent from component state')

    c = comps[idx]
    offsets = dict(c['members'])
    px = offsets[x]
    del offsets[x]
    lift_to: Optional[int]
    lift_parity: Optional[int]

    if not offsets:
        mode = 'DELETE_SINGLETON'
        lift_to = None
        lift_parity = None
        del comps[idx]
        ops += 1
    elif x != c['root']:
        mode = 'DELETE_NONROOT'
        lift_to = c['root']
        lift_parity = px
        comps[idx] = {'root': c['root'], 'members': tuple(sorted(offsets.items()))}
        ops += len(offsets)
    else:
        mode = 'REROOT_AFTER_ROOT_DELETE'
        new_root = min(offsets)
        q = offsets[new_root]
        new_offsets = {v: p ^ q for v, p in offsets.items()}
        lift_to = new_root
        lift_parity = q
        comps[idx] = {'root': new_root, 'members': tuple(sorted(new_offsets.items()))}
        ops += len(new_offsets)

    comps.sort(key=lambda z: z['root'])
    out = {'false': False, 'components': comps}
    proof = {
        'x': int(x), 'mode': mode,
        'before_sha256': before_hash,
        'after_sha256': component_state_hash(out),
        'lift_to_var': lift_to,
        'lift_parity': lift_parity,
    }
    return out, proof, ops + 1


def project_components_all(
    state: Dict, order: Sequence[int], prior_ops: int, prior_proof_bytes: int, source_bytes: int
) -> Dict:
    current = state
    proof: List[Dict] = []
    ops = 0
    peak = max(source_bytes, component_state_bytes(current))
    cumulative = source_bytes + component_state_bytes(current)
    for x in order:
        current, rec, z = project_component_var(current, x)
        ops += z
        proof.append(rec)
        sb = component_state_bytes(current)
        peak = max(peak, sb)
        cumulative += sb
        base.check_common_caps(
            peak, prior_proof_bytes + base.json_bytes(proof), cumulative, prior_ops + ops
        )
    if current['false']:
        final_scalar = False
    else:
        if current['components']:
            raise AssertionError('all declared variables projected but signed components remain')
        final_scalar = True
    return {
        'final_scalar': final_scalar,
        'proof': proof,
        'ops': ops,
        'proof_bytes': base.json_bytes(proof),
        'peak': peak,
        'cumulative': cumulative,
        'terminal_state': component_state_payload(current),
    }


def lift_component_witness(proof: Sequence[Dict]) -> Tuple[Dict[int, bool], int]:
    env: Dict[int, bool] = {}
    ops = 0
    for rec in reversed(proof):
        mode = rec['mode']
        x = int(rec['x'])
        if mode == 'FALSE_STICKY':
            raise AssertionError('cannot reconstruct SAT witness from FALSE proof')
        if mode == 'DELETE_SINGLETON':
            env[x] = False
            ops += 1
        else:
            target = int(rec['lift_to_var'])
            parity = int(rec['lift_parity'])
            ops += 1
            if target not in env:
                raise AssertionError(f'component witness lift missing target {target}')
            env[x] = bool(int(env[target]) ^ parity)
    return env, ops


# ---------------------------------------------------------------------------
# Generic source-to-OBDD fallback
# ---------------------------------------------------------------------------


def build_generic_obdd(
    clauses: Sequence[Clause], variables: Sequence[int], order: Sequence[int],
    prior_ops: int, prior_proof_bytes: int, source_bytes: int
) -> Dict:
    b = base.BDD(order)
    proof: List[Dict] = []
    root = 1
    build_ops = 0
    cumulative = source_bytes
    peak = source_bytes
    try:
        for ci, clause in enumerate(clauses):
            clause_root = 0
            literal_roots: List[int] = []
            before = b.ops
            for lit in clause:
                v = abs(lit)
                node = b.mk(v, 0, 1) if lit > 0 else b.mk(v, 1, 0)
                literal_roots.append(node)
                clause_root = b.apply_or(clause_root, node)
            root = v4.apply_and(b, root, clause_root)
            build_ops += b.ops - before
            proof.append({
                'clause_index': ci,
                'clause': list(clause),
                'literal_roots': literal_roots,
                'clause_root': clause_root,
                'formula_root_after': root,
            })
            sb = v4.manager_bytes(b)
            peak = max(peak, sb)
            cumulative += sb
            base.check_common_caps(
                peak, prior_proof_bytes + base.json_bytes(proof), cumulative,
                prior_ops + build_ops,
            )
        return {
            'status': 'PASS', 'bdd': b, 'root': root,
            'build_ops': build_ops, 'proof': proof,
            'proof_bytes': base.json_bytes(proof),
            'peak': peak, 'cumulative': cumulative,
        }
    except base.CapHit as e:
        return {
            'status': 'CAP_HIT', 'cap_reason': str(e),
            'build_ops': build_ops + b.ops,
            'proof': proof, 'proof_bytes': base.json_bytes(proof),
            'partial_nodes': len(b.nodes), 'partial_manager_bytes': v4.manager_bytes(b),
            'peak': max(peak, v4.manager_bytes(b)), 'cumulative': cumulative,
        }


# ---------------------------------------------------------------------------
# Unlabeled source bootstrap API
# ---------------------------------------------------------------------------


def bootstrap_representation(
    clauses: Sequence[Clause], variables: Sequence[int], frozen_order: Sequence[int]
) -> Dict:
    source_bytes = cnf_bytes(clauses, variables, frozen_order)
    attempts: List[Dict] = []
    failed_ops = 0
    failed_proof_bytes = 0

    parity = recognize_signed_parity_graph(clauses, variables, frozen_order)
    if parity['accepted']:
        attempts.append({
            'bootstrap': 'SIGNED_PARITY_GRAPH_CNF', 'status': 'ACCEPT_EQUIVALENT',
            'ops': int(parity['ops']), 'proof_bytes': int(parity['proof_bytes']),
        })
        return {
            'status': 'PASS',
            'lane': 'SIGNED_PARITY_COMPONENTS',
            'payload': parity['state'],
            'attempts': attempts,
            'failed_bootstrap_ops': 0,
            'failed_bootstrap_proof_bytes': 0,
            'bootstrap_ops': int(parity['ops']),
            'bootstrap_proof_bytes': int(parity['proof_bytes']),
            'source_equivalence_exact': bool(parity['source_equivalence_exact']),
            'selected_representation_bytes': component_state_bytes(parity['state']),
            'source_bytes': source_bytes,
        }

    attempts.append({
        'bootstrap': 'SIGNED_PARITY_GRAPH_CNF', 'status': 'REJECT',
        'ops': int(parity['ops']), 'proof_bytes': int(parity['proof_bytes']),
        'failure': parity['proof']['reject'],
    })
    failed_ops += int(parity['ops'])
    failed_proof_bytes += int(parity['proof_bytes'])

    generic = build_generic_obdd(
        clauses, variables, frozen_order,
        failed_ops, failed_proof_bytes, source_bytes,
    )
    if generic['status'] == 'CAP_HIT':
        attempts.append({
            'bootstrap': 'GENERIC_FROZEN_ORDER_OBDD', 'status': 'CAP_HIT',
            'ops': int(generic['build_ops']), 'proof_bytes': int(generic['proof_bytes']),
            'cap_reason': generic['cap_reason'],
        })
        return {
            'status': 'CAP_HIT', 'cap_reason': generic['cap_reason'],
            'attempts': attempts,
            'failed_bootstrap_ops': failed_ops + int(generic['build_ops']),
            'failed_bootstrap_proof_bytes': failed_proof_bytes + int(generic['proof_bytes']),
            'source_bytes': source_bytes,
            'partial_nodes': generic['partial_nodes'],
            'partial_manager_bytes': generic['partial_manager_bytes'],
        }

    attempts.append({
        'bootstrap': 'GENERIC_FROZEN_ORDER_OBDD', 'status': 'ACCEPT_SYNTAX_PRESERVING',
        'ops': int(generic['build_ops']), 'proof_bytes': int(generic['proof_bytes']),
    })
    return {
        'status': 'PASS',
        'lane': 'GENERIC_FROZEN_ORDER_OBDD',
        'payload': {'bdd': generic['bdd'], 'root': generic['root']},
        'attempts': attempts,
        'failed_bootstrap_ops': failed_ops,
        'failed_bootstrap_proof_bytes': failed_proof_bytes,
        'bootstrap_ops': failed_ops + int(generic['build_ops']),
        'bootstrap_proof_bytes': failed_proof_bytes + int(generic['proof_bytes']),
        'source_equivalence_exact': True,
        'selected_representation_bytes': v4.manager_bytes(generic['bdd']),
        'source_bytes': source_bytes,
        'generic_build_peak': generic['peak'],
        'generic_build_cumulative': generic['cumulative'],
    }


def run_fixture(f: SourceFixture) -> Dict:
    source_bytes = cnf_bytes(f.clauses, f.variables, f.order)
    source_sha = cnf_hash(f.clauses, f.variables, f.order)

    # Blind call: fixture name/kind/expected lane is not an argument.
    selected = bootstrap_representation(f.clauses, f.variables, f.order)
    if selected['status'] == 'CAP_HIT':
        return {
            'fixture': f.name, 'n': f.n,
            'external_kind_for_test_only': f.kind,
            'expected_lane_external_test_only': f.expected_lane,
            'expected_sat': f.expected_sat,
            'status': 'CAP_HIT', 'cap_reason': selected['cap_reason'],
            'bootstrap_attempts': selected['attempts'],
            'failed_bootstrap_ops': selected['failed_bootstrap_ops'],
            'failed_bootstrap_proof_bytes': selected['failed_bootstrap_proof_bytes'],
            'partial_nodes': selected.get('partial_nodes', 0),
            'partial_manager_bytes': selected.get('partial_manager_bytes', 0),
            'claim': 'FINITE_SOURCE_BOOTSTRAP_PORTFOLIO_ESCAPE_ONLY',
        }

    lane = selected['lane']
    prior_ops = int(selected['bootstrap_ops'])
    prior_proof_bytes = int(selected['bootstrap_proof_bytes'])

    if lane == 'SIGNED_PARITY_COMPONENTS':
        projected = project_components_all(
            selected['payload'], f.order,
            prior_ops, prior_proof_bytes, source_bytes,
        )
        final_scalar = bool(projected['final_scalar'])
        witness: Optional[Dict[int, bool]] = None
        witness_ops = 0
        witness_source = 'NO_WITNESS_SIGNED_COMPONENT_CONTRADICTION'
        if final_scalar:
            witness, witness_ops = lift_component_witness(projected['proof'])
            witness_source = 'SIGNED_COMPONENT_REROOT_PROJECTION_PROOF'
        projection_ops = int(projected['ops'])
        projection_proof_bytes = int(projected['proof_bytes'])
        peak = int(projected['peak'])
        cumulative = int(projected['cumulative']) + int(selected['selected_representation_bytes'])
    elif lane == 'GENERIC_FROZEN_ORDER_OBDD':
        b = selected['payload']['bdd']
        root = int(selected['payload']['root'])
        build_cumulative = int(selected.get('generic_build_cumulative', source_bytes))
        build_peak = int(selected.get('generic_build_peak', v4.manager_bytes(b)))
        projected = v4.project_common_boundary(
            b, root, f.order,
            prior_ops, prior_proof_bytes,
            build_cumulative, build_peak,
        )
        final_root = int(projected['root'])
        if final_root not in (0, 1):
            raise AssertionError('generic bootstrap full projection nonterminal')
        final_scalar = bool(final_root)
        witness = None
        witness_ops = 0
        witness_source = 'NO_WITNESS_GENERIC_OBDD_FALSE'
        if final_scalar:
            witness, witness_ops = v4.lift_bdd_projection_witness(b, projected['proof'], {})
            witness_source = 'GENERIC_SOURCE_OBDD_PROJECTION_PROOF'
        projection_ops = int(projected['ops'])
        projection_proof_bytes = int(projected['proof_bytes'])
        peak = int(projected['representation_bytes_peak'])
        cumulative = int(projected['cumulative_state_bytes'])
    else:
        raise AssertionError(lane)

    if final_scalar != f.expected_sat:
        raise AssertionError(f'bootstrap scalar mismatch for {f.name}')

    witness_valid: Optional[bool] = None
    verification_ops = 0
    if final_scalar:
        if witness is None or set(witness) != set(f.variables):
            raise AssertionError('source witness incomplete')
        witness_valid, verification_ops = eval_cnf(f.clauses, witness)
        if not witness_valid:
            raise AssertionError('source witness fails original CNF')
    else:
        witness_valid = None

    total_ops = prior_ops + projection_ops + witness_ops + verification_ops
    proof_bytes = prior_proof_bytes + projection_proof_bytes
    witness_bytes = base.json_bytes(witness or {})
    base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

    failed_attempts = [a for a in selected['attempts'] if a['status'] in ('REJECT', 'CAP_HIT')]
    failed_work_charged = (
        int(selected['failed_bootstrap_ops']) == sum(int(a['ops']) for a in failed_attempts)
        and int(selected['failed_bootstrap_proof_bytes']) == sum(int(a['proof_bytes']) for a in failed_attempts)
    )

    cert = {
        'source_sha256': source_sha,
        'bootstrap_order': list(BOOTSTRAP_ORDER),
        'attempts': selected['attempts'],
        'selected_lane': lane,
        'projection_proof_sha256': sha256(base.canon_json(projected['proof']).encode()).hexdigest(),
        'witness_sha256': sha256(base.canon_json(witness or {}).encode()).hexdigest(),
    }

    return {
        'fixture': f.name,
        'n': f.n,
        'external_kind_for_test_only': f.kind,
        'expected_lane_external_test_only': f.expected_lane,
        'expected_sat': f.expected_sat,
        'status': 'PASS_EXACT_CLOSED',
        'source_input_is_cnf_only': True,
        'bootstrap_input_has_no_prebuilt_obdd': True,
        'bootstrap_api_unlabeled': True,
        'source_sha256': source_sha,
        'source_bytes': source_bytes,
        'fixed_bootstrap_order_used': [a['bootstrap'] for a in selected['attempts']] == list(BOOTSTRAP_ORDER[:len(selected['attempts'])]),
        'bootstrap_attempts': selected['attempts'],
        'selected_lane': lane,
        'lane_matches_frozen_expectation': lane == f.expected_lane,
        'failed_bootstrap_work_charged': failed_work_charged,
        'failed_bootstrap_ops': int(selected['failed_bootstrap_ops']),
        'failed_bootstrap_proof_bytes': int(selected['failed_bootstrap_proof_bytes']),
        'source_equivalence_certificate_exact': bool(selected['source_equivalence_exact']),
        'selected_representation_project_closed': True,
        'final_scalar': final_scalar,
        'strict_source_witness': (witness_valid is True) if final_scalar else True,
        'witness_valid': witness_valid,
        'witness_source': witness_source,
        'witness_bytes': witness_bytes,
        'representation_bytes_peak': peak,
        'cumulative_state_bytes': cumulative,
        'proof_bytes': proof_bytes,
        'bootstrap_ops': prior_ops,
        'projection_ops': projection_ops,
        'witness_ops': witness_ops,
        'verification_ops': verification_ops,
        'total_charged_ops': total_ops,
        'certificate_sha256': sha256(base.canon_json(cert).encode()).hexdigest(),
        'witness': witness,
    }


def main(argv: Sequence[str]) -> int:
    rows = [run_fixture(f) for f in make_fixtures()]
    passed = [r for r in rows if r['status'] == 'PASS_EXACT_CLOSED']
    first_cap = next((r for r in rows if r['status'] == 'CAP_HIT'), None)

    result = {
        'artifact_id': 'PF5-SOURCE-REPRESENTATION-BOOTSTRAP-V6',
        'protocol': 'PF5_SOURCE_REPRESENTATION_BOOTSTRAP_GATE_V6.md',
        'claim_ceiling': 'P_VS_NP = OPEN',
        'widths_frozen_before_provider_run': list(WIDTHS),
        'bootstrap_order_frozen_before_provider_run': list(BOOTSTRAP_ORDER),
        'caps': base.CAPS,
        'new_tuned_caps_added': False,
        'controls': rows,
        'passed_controls': len(passed),
        'all_passed_source_cnf_only': all(r['source_input_is_cnf_only'] for r in passed) if passed else False,
        'all_passed_no_prebuilt_obdd': all(r['bootstrap_input_has_no_prebuilt_obdd'] for r in passed) if passed else False,
        'all_passed_bootstrap_unlabeled': all(r['bootstrap_api_unlabeled'] for r in passed) if passed else False,
        'all_passed_fixed_bootstrap_order': all(r['fixed_bootstrap_order_used'] for r in passed) if passed else False,
        'all_passed_failed_work_charged': all(r['failed_bootstrap_work_charged'] for r in passed) if passed else False,
        'all_passed_source_equivalence_exact': all(r['source_equivalence_certificate_exact'] for r in passed) if passed else False,
        'all_passed_project_closed': all(r['selected_representation_project_closed'] for r in passed) if passed else False,
        'all_passed_strict_source_witness': all(r['strict_source_witness'] for r in passed) if passed else False,
        'blind_lane_selection_matches_frozen_expectation': all(r['lane_matches_frozen_expectation'] for r in passed) if passed else False,
        'signed_blocked_pair_discovered_before_obdd': all(
            r['selected_lane']=='SIGNED_PARITY_COMPONENTS' and len(r['bootstrap_attempts'])==1
            for r in passed if r['external_kind_for_test_only']=='SIGNED_BLOCKED_PAIRS'
        ),
        'parity_cycle_contradiction_discovered': all(
            r['selected_lane']=='SIGNED_PARITY_COMPONENTS' and r['final_scalar'] is False
            for r in passed if r['external_kind_for_test_only']=='SIGNED_CYCLE_UNSAT'
        ),
        'wide_or_uses_generic_bootstrap': all(
            r['selected_lane']=='GENERIC_FROZEN_ORDER_OBDD'
            for r in passed if r['external_kind_for_test_only']=='WIDE_OR'
        ),
        'first_base_cap_hit': None if first_cap is None else {
            'fixture': first_cap['fixture'], 'n': first_cap['n'],
            'reason': first_cap['cap_reason'],
            'partial_nodes': first_cap.get('partial_nodes', 0),
            'partial_manager_bytes': first_cap.get('partial_manager_bytes', 0),
        },
        'generic_obdd_bad_order_receipt': 'PRESERVED_FROM_PF5_V0_BLOCKED_EQUALITY',
        'universal_source_representation_discovery': 'OPEN',
        'universal_polynomial_bootstrap': 'OPEN',
        'universal_polynomial_coverage': 'OPEN',
        'global_progress_amortization': 'OPEN',
        'representation_lower_bound': 'NOT_ESTABLISHED',
        'next_front_if_full_pass': 'GIANT_CONNECTED_3CNF_SOURCE_TO_BOUNDARY_GATE',
        'p_vs_np': 'OPEN',
    }
    result['result_sha256'] = sha256(base.canon_json(result).encode()).hexdigest()

    print('PF5_SOURCE_REPRESENTATION_BOOTSTRAP_V6 = FROZEN')
    for r in rows:
        if r['status']=='PASS_EXACT_CLOSED':
            print(
                r['fixture'], 'status=PASS_EXACT_CLOSED', 'n=', r['n'],
                'selected=', r['selected_lane'],
                'attempts=', [(a['bootstrap'],a['status']) for a in r['bootstrap_attempts']],
                'source_bytes=', r['source_bytes'],
                'peak=', r['representation_bytes_peak'],
                'ops=', r['total_charged_ops'],
                'scalar=', r['final_scalar'],
                'witness=', r['witness_source'],
            )
        else:
            print(r['fixture'], 'status=CAP_HIT', 'n=', r['n'], 'cap=', r['cap_reason'])
    print('SIGNED_BLOCKED_PAIR_DISCOVERED_BEFORE_OBDD =', result['signed_blocked_pair_discovered_before_obdd'])
    print('PARITY_CYCLE_CONTRADICTION_DISCOVERED =', result['parity_cycle_contradiction_discovered'])
    print('WIDE_OR_USES_GENERIC_BOOTSTRAP =', result['wide_or_uses_generic_bootstrap'])
    print('FIRST_BASE_CAP_HIT =', result['first_base_cap_hit'])
    print('UNIVERSAL_SOURCE_REPRESENTATION_DISCOVERY = OPEN')
    print('UNIVERSAL_POLYNOMIAL_BOOTSTRAP = OPEN')
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
