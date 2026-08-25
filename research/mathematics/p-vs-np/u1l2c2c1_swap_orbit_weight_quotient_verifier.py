#!/usr/bin/env python3
"""U1-L2C2C1 exact swap-automorphism orbit-weight quotient.

No heuristics, randomization, SAT oracle, semantic equivalence oracle, or 2^n
assignment table.  Variable symmetries are admitted only when literal variable
transpositions preserve canonical CNF exactly.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import product
import json
from math import prod

K = 4
PROTOCOL_COMMIT = "eb894852020fe5e70b01959d454f9f11a3f42ba9"


def lit_key(l: int):
    return (abs(l), 0 if l < 0 else 1)


def canonical_cnf(clauses):
    norm = []
    for clause in clauses:
        lits = tuple(sorted(set(int(x) for x in clause), key=lit_key))
        norm.append(lits)
    return tuple(sorted(norm, key=lambda c: (len(c), tuple(lit_key(x) for x in c))))


def variables(F):
    return tuple(sorted({abs(l) for c in F for l in c}))


def encoded_size(F):
    vs = variables(F)
    return len(vs) + len(F) + sum(len(c) for c in F) + 1


def swap_lit(l, u, v):
    a = abs(l)
    s = -1 if l < 0 else 1
    if a == u:
        a = v
    elif a == v:
        a = u
    return s * a


def swap_cnf(F, u, v):
    return canonical_cnf(tuple(tuple(swap_lit(l, u, v) for l in c) for c in F))


def is_swap_automorphism(F, u, v):
    return canonical_cnf(F) == swap_cnf(F, u, v)


class DSU:
    def __init__(self, xs):
        self.p = {x: x for x in xs}
    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[max(a,b)] = min(a,b)


def discover_swap_classes(F):
    F = canonical_cnf(F)
    vs = variables(F)
    dsu = DSU(vs)
    pair_rows = []
    comparisons = 0
    for i, u in enumerate(vs):
        for v in vs[i+1:]:
            comparisons += 1
            ok = is_swap_automorphism(F, u, v)
            pair_rows.append((u, v, ok))
            if ok:
                dsu.union(u, v)
    groups = {}
    for v in vs:
        groups.setdefault(dsu.find(v), []).append(v)
    blocks = tuple(tuple(g) for _, g in sorted(groups.items()))

    # Independent closure replay: every pair inside a discovered class must
    # itself be an admitted transposition automorphism.
    for block in blocks:
        for i, u in enumerate(block):
            for v in block[i+1:]:
                assert is_swap_automorphism(F, u, v)
    return blocks, pair_rows, comparisons


def eval_cnf(F, assignment):
    for c in F:
        if not any((assignment[abs(l)] if l > 0 else not assignment[abs(l)]) for l in c):
            return False
    return True


def canonical_assignment(blocks, weights):
    a = {}
    for block, w in zip(blocks, weights):
        assert 0 <= w <= len(block)
        for i, v in enumerate(block):
            a[v] = i < w
    return a


@dataclass(frozen=True)
class OrbitState:
    blocks: tuple[tuple[int, ...], ...]
    sizes: tuple[int, ...]
    accepting: tuple[tuple[int, ...], ...]


def state_payload(s):
    return {
        "blocks": [list(b) for b in s.blocks],
        "sizes": list(s.sizes),
        "accepting": [list(w) for w in s.accepting],
    }


def fingerprint(s):
    return sha256(json.dumps(state_payload(s), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_quotient(F):
    F = canonical_cnf(F)
    blocks, pair_rows, comparisons = discover_swap_classes(F)
    sizes = tuple(len(b) for b in blocks)
    P = prod(m + 1 for m in sizes)
    N = encoded_size(F)
    if P > N ** K:
        return None, {
            "status": "REFUSE_ORBIT_STATE_PRODUCT_EXCEEDS_N^4",
            "N": N,
            "P": P,
            "pair_comparisons": comparisons,
            "blocks": [list(b) for b in blocks],
        }

    accepting = []
    evaluations = 0
    ranges = [range(m + 1) for m in sizes]
    for w in product(*ranges):
        evaluations += 1
        a = canonical_assignment(blocks, w)
        if eval_cnf(F, a):
            accepting.append(tuple(w))
    s = OrbitState(blocks, sizes, tuple(sorted(accepting)))
    cert = {
        "status": "PASS_SWAP_ORBIT_QUOTIENT",
        "N": N,
        "P": P,
        "K": K,
        "pair_comparisons": comparisons,
        "quotient_evaluations": evaluations,
        "blocks": [list(b) for b in blocks],
        "sizes": list(sizes),
        "accepting_count": len(accepting),
        "state_sha256": fingerprint(s),
        "all_within_block_transpositions_replayed": True,
    }
    return s, cert


def project_block_coordinate(s: OrbitState, j: int):
    assert s.sizes[j] > 0
    A = set(s.accepting)
    target_sizes = list(s.sizes)
    target_sizes[j] -= 1
    target_acc = []
    inspected = 0
    ranges = [range(m + 1) for m in target_sizes]
    for w in product(*ranges):
        inspected += 1
        w0 = tuple(w)
        w1 = list(w)
        w1[j] += 1
        if w0 in A or tuple(w1) in A:
            target_acc.append(w0)
    target = OrbitState(s.blocks, tuple(target_sizes), tuple(sorted(target_acc)))
    cert = {
        "case": "EXACT_ORBIT_WEIGHT_EXISTS",
        "block_index": j,
        "source_sha256": fingerprint(s),
        "target_sha256": fingerprint(target),
        "inspected_target_weight_states": inspected,
    }
    return target, cert


def independent_verify_projection(source, target, cert):
    j = cert["block_index"]
    assert cert["source_sha256"] == fingerprint(source)
    assert cert["target_sha256"] == fingerprint(target)
    assert source.sizes[j] == target.sizes[j] + 1
    for i in range(len(source.sizes)):
        if i != j:
            assert source.sizes[i] == target.sizes[i]
    A = set(source.accepting)
    expected = []
    ranges = [range(m + 1) for m in target.sizes]
    for w in product(*ranges):
        w0 = tuple(w)
        w1 = list(w); w1[j] += 1
        if w0 in A or tuple(w1) in A:
            expected.append(w0)
    assert tuple(sorted(expected)) == target.accepting


def sequential_project(F, source):
    current = source
    # Deterministic pivot order: increasing original variable id. Map each
    # variable to its discovered block; each projection reduces that size.
    block_of = {}
    for j, block in enumerate(source.blocks):
        for v in block:
            block_of[v] = j
    order = sorted(block_of)
    chain = []
    operations = 0
    for v in order:
        j = block_of[v]
        target, cert = project_block_coordinate(current, j)
        independent_verify_projection(current, target, cert)
        chain.append((v, current, target, cert))
        operations += cert["inspected_target_weight_states"]
        current = target
    assert all(m == 0 for m in current.sizes)
    terminal_true = tuple(0 for _ in current.sizes) in set(current.accepting)

    witness = {}
    replay = "PASS_UNSAT_TERMINAL_ORBIT_STATE"
    if terminal_true:
        w = [0] * len(current.sizes)
        for v, src, tgt, cert in reversed(chain):
            j = cert["block_index"]
            assert tuple(w) in set(tgt.accepting)
            if tuple(w) in set(src.accepting):
                bit = 0
            else:
                w1 = list(w); w1[j] += 1
                assert tuple(w1) in set(src.accepting)
                bit = 1
                w = w1
            witness[v] = bool(bit)
        assert eval_cnf(canonical_cnf(F), witness)
        replay = "PASS_SAT_WITNESS"

    return {
        "terminal": "TRUE" if terminal_true else "FALSE",
        "witness_replay": replay,
        "steps": len(chain),
        "projection_weight_state_inspections": operations,
        "final_sha256": fingerprint(current),
    }


def symmetric_sat_fixture(n=12):
    return canonical_cnf((tuple(range(1,n+1)), tuple(-i for i in range(1,n+1))))


def symmetric_unsat_fixture(n=10):
    clauses = [(i,) for i in range(1,n+1)]
    clauses.append(tuple(-i for i in range(1,n+1)))
    return canonical_cnf(clauses)


def two_block_fixture():
    A = tuple(range(1,8))
    B = tuple(range(8,12))
    return canonical_cnf((A, tuple(-x for x in A), tuple(-x for x in B)))


def asymmetric_fixture(n=40):
    clauses = [(1,)]
    clauses.extend((i, i+1) for i in range(1,n))
    return canonical_cnf(clauses)


def controls():
    rows = []
    # False-positive pair control.
    F = canonical_cnf(((1,2),(-1,3)))
    assert not is_swap_automorphism(F, 2, 3)
    rows.append({"name":"PAIR_SWAP_FALSE_POSITIVE", "result":"PASS_REJECT"})

    for name, F, expected_terminal in [
        ("ONE_BLOCK_SYMMETRIC_SAT", symmetric_sat_fixture(), "TRUE"),
        ("ONE_BLOCK_SYMMETRIC_UNSAT", symmetric_unsat_fixture(), "FALSE"),
        ("TWO_BLOCK_SYMMETRIC", two_block_fixture(), "TRUE"),
    ]:
        s, cert = build_quotient(F)
        assert s is not None and cert["status"] == "PASS_SWAP_ORBIT_QUOTIENT"
        seq = sequential_project(F, s)
        assert seq["terminal"] == expected_terminal
        if expected_terminal == "TRUE":
            assert seq["witness_replay"] == "PASS_SAT_WITNESS"
        rows.append({
            "name": name,
            "N": cert["N"],
            "P": cert["P"],
            "blocks": cert["blocks"],
            "terminal": seq["terminal"],
            "witness_replay": seq["witness_replay"],
            "projection_inspections": seq["projection_weight_state_inspections"],
        })

    F = asymmetric_fixture()
    s, cert = build_quotient(F)
    assert s is None
    assert cert["status"] == "REFUSE_ORBIT_STATE_PRODUCT_EXCEEDS_N^4"
    rows.append({
        "name": "ASYMMETRIC_ORBIT_EXPLOSION",
        "result": cert["status"],
        "N": cert["N"],
        "P": str(cert["P"]),
        "block_count": len(cert["blocks"]),
    })
    return rows


def main():
    rows = controls()
    result = {
        "schema": "JANUS_U1L2C2C1_SWAP_ORBIT_WEIGHT_QUOTIENT_RESULT",
        "status": "PASS_RESTRICTED_AUTOMATIC_EXACT_C2C_QUOTIENT",
        "claim_ceiling": "P_VS_NP_OPEN",
        "frozen_protocol_commit": PROTOCOL_COMMIT,
        "fixed_polynomial_exponent_K": K,
        "controls": rows,
        "theorem_ledger": {
            "PAIR_SWAP_DISCOVERY_POLYNOMIAL": True,
            "WITHIN_CLASS_TRANSPOSITIONS_CERTIFIED": True,
            "WEIGHT_VECTOR_IS_EXACT_ORBIT_QUOTIENT": True,
            "QUOTIENT_BUILD_POLYNOMIAL_WHEN_P_LE_N_POW_K": True,
            "EXISTENTIAL_UPDATE_EXACT_AND_CLOSED": True,
            "WITNESS_LIFT_REPLAY": True,
            "ARBITRARY_CNF_HAS_POLY_SWAP_ORBIT_PRODUCT": "OPEN_NOT_CLAIMED",
            "P_EQUALS_NP": False,
        },
        "next_gate": "C2C2_EXTEND_EXACT_TRANSITION_EQUIVALENCE_BEYOND_LITERAL_VARIABLE_SWAP_ORBITS_OR_PROVE_GLOBAL_CANONICAL_STATE_BOUND",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("U1L2C2C1_RESULT_SHA256=" + sha256(packed).hexdigest())

if __name__ == "__main__":
    main()
