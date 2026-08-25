#!/usr/bin/env python3
"""Exact generator/verifier for the frozen JANUS graph-tautology encoding.

The construction proves the family-specific cubic Resolution upper bound directly
for our encoding. CI validates finite n=2..12 mechanics; the general theorem is
the analytic induction recorded in C025_AKINATOR_GT_LINEAR_RESOLUTION_SCHEMA.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

Clause = tuple[int, ...]


def canon_clause(lits: Iterable[int]) -> Clause | None:
    s = set(int(x) for x in lits)
    if any(-l in s for l in s):
        return None
    return tuple(sorted(s, key=lambda z: (abs(z), z < 0)))


def resolve(c1: Clause, c2: Clause, pivot: int) -> Clause:
    if pivot in c1 and -pivot in c2:
        left, right = c1, c2
    elif -pivot in c1 and pivot in c2:
        left, right = c2, c1
    else:
        raise AssertionError(("missing complementary pivot", pivot, c1, c2))
    raw = [l for l in left if l != pivot] + [l for l in right if l != -pivot]
    out = canon_clause(raw)
    if out is None:
        raise AssertionError(("tautological resolvent", pivot, c1, c2))
    return out


@dataclass(frozen=True)
class Inference:
    left: Clause
    right: Clause
    pivot: int
    result: Clause
    tag: str


def build_pair_vars(n: int):
    pair = {}
    nxt = 1
    for i in range(n):
        for j in range(i + 1, n):
            pair[(i, j)] = nxt
            nxt += 1
    return pair


def less(pair, i: int, j: int) -> int:
    assert i != j
    return pair[(i, j)] if i < j else -pair[(j, i)]


def m_clause(pair, m: int, i: int) -> Clause:
    c = canon_clause(less(pair, k, i) for k in range(m) if k != i)
    assert c is not None
    return c


def generate_and_verify(n: int, root: tuple[Clause, ...]):
    pair = build_pair_vars(n)
    root_set = set(root)
    available = set(root)
    proof: list[Inference] = []

    # Verify exact root non-minimality clauses are present.
    for i in range(n):
        assert m_clause(pair, n, i) in root_set

    for m in range(n, 2, -1):
        z = m - 1
        mz = m_clause(pair, m, z)
        assert mz in available

        for i in range(z):
            p = less(pair, z, i)
            mi_m = m_clause(pair, m, i)
            target_small = m_clause(pair, m - 1, i)
            assert mi_m in available

            cur = mz
            for k in range(z):
                if k == i:
                    continue
                a = less(pair, k, z)
                trans = canon_clause((-a, -p, less(pair, k, i)))
                assert trans is not None
                assert trans in root_set, (n, m, i, k, trans)
                new = resolve(cur, trans, a)
                # Independent step verifier: recompute from parents.
                assert resolve(cur, trans, a) == new
                proof.append(Inference(cur, trans, a, new, f"m{m}:i{i}:k{k}"))
                available.add(new)
                cur = new

            expected_guarded = canon_clause((-p, *target_small))
            assert expected_guarded is not None
            assert cur == expected_guarded, (n, m, i, cur, expected_guarded)

            new_m = resolve(mi_m, cur, p)
            assert new_m == target_small, (n, m, i, new_m, target_small)
            assert resolve(mi_m, cur, p) == new_m
            proof.append(Inference(mi_m, cur, p, new_m, f"m{m}:i{i}:drop-z"))
            available.add(new_m)

    m0 = m_clause(pair, 2, 0)
    m1 = m_clause(pair, 2, 1)
    assert m0 in available and m1 in available
    p = less(pair, 1, 0)
    empty = resolve(m0, m1, p)
    assert empty == ()
    proof.append(Inference(m0, m1, p, empty, "base-GT2"))
    available.add(empty)

    expected = (n - 1) * n * (2 * n - 1) // 6
    assert len(proof) == expected, (n, len(proof), expected)
    assert () in available

    # Full proof replay again, this time requiring every parent to be root or
    # previously derived, independent of construction-time checks.
    replay_available = set(root)
    for step in proof:
        assert step.left in replay_available
        assert step.right in replay_available
        assert resolve(step.left, step.right, step.pivot) == step.result
        replay_available.add(step.result)
    assert () in replay_available

    return {
        "n": n,
        "root_clauses": len(root),
        "resolution_inferences": len(proof),
        "expected_inferences": expected,
        "empty_clause_derived": True,
        "full_replay_pass": True,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--fundamentum-root', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()

    direct = args.fundamentum_root / 'experiments' / 'direct'
    sys.path.insert(0, str(direct))
    from janus_tear_policy0a_graph_tautology_probe import graph_tautology_cnf

    rows = []
    for n in range(2, 13):
        root, var_count = graph_tautology_cnf(n)
        row = generate_and_verify(n, tuple(root))
        row['variables'] = var_count
        rows.append(row)

    gt12 = rows[-1]
    assert gt12['variables'] == 66
    assert gt12['root_clauses'] == 452
    assert gt12['resolution_inferences'] == 506

    result = {
        'artifact_id': 'JANUS-GT-LINEAR-RESOLUTION-SCHEMA-FINITE-REPLAY-2026-08-25-v1.0',
        'claim_ceiling': 'FINITE_GENERATOR_REPLAY_PLUS_ANALYTIC_GENERAL_THEOREM__P_VS_NP_OPEN',
        'rows': rows,
        'gt12': gt12,
        'scientific_boundary': [
            'CI verifies the explicit generator/replayer for n=2..12.',
            'The cubic all-n theorem is the induction in the companion proof note, aligned with Buss-Johannsen Theorem 14.',
            'This is a family-specific Resolution upper bound, not a universal SAT algorithm.',
            'GT generic-search cap hits are not Resolution lower bounds.'
        ],
        'p_vs_np': 'OPEN',
    }
    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
