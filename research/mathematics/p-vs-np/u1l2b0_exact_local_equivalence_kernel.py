#!/usr/bin/env python3
"""U1-L2B0 exact local equivalence kernel.

Frozen scope:
  k=4 formal boundary variables
  g<=3 topologically ordered B2 AND gates with signed inputs

This is exhaustive finite algebra synthesis, not heuristic search.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from itertools import combinations, product
from typing import Dict, Iterable, List, Sequence, Tuple

K = 4
G_MAX = 3
ROWS = 1 << K
FULL_MASK = (1 << ROWS) - 1

Literal = int  # +/- (signal_id + 1)
Gate = Tuple[Literal, Literal]
Circuit = Tuple[Gate, ...]


@dataclass(frozen=True)
class Rep:
    gates: Circuit
    output_sign: int
    truth: int
    dep_count: int
    gate_count: int
    encoding: str


def sid(lit: Literal) -> int:
    return abs(lit) - 1


def boundary_masks() -> List[int]:
    out: List[int] = []
    for var in range(K):
        mask = 0
        for row in range(ROWS):
            if (row >> var) & 1:
                mask |= 1 << row
        out.append(mask)
    return out


BOUNDARY_MASKS = boundary_masks()


def lit_mask(lit: Literal, signals: Sequence[int]) -> int:
    m = signals[sid(lit)]
    return m if lit > 0 else (FULL_MASK ^ m)


def lit_dep(lit: Literal, deps: Sequence[bool]) -> bool:
    return deps[sid(lit)]


def evaluate_circuit_mask(gates: Circuit, output_sign: int) -> Tuple[int, List[int], List[bool]]:
    signals = list(BOUNDARY_MASKS)
    # dependency on each p is recomputed separately outside; placeholder here
    for a, b in gates:
        assert sid(a) < len(signals) and sid(b) < len(signals)
        assert sid(a) != sid(b)
        signals.append(lit_mask(a, signals) & lit_mask(b, signals))
    if gates:
        out_lit = output_sign * (K + len(gates))
    else:
        raise ValueError("zero-gate output requires a boundary signal")
    truth = lit_mask(out_lit, signals)
    return truth, signals, []


def output_truth(gates: Circuit, output_sign: int, boundary_output: int | None = None) -> int:
    if not gates:
        assert boundary_output is not None
        lit = output_sign * (boundary_output + 1)
        return lit_mask(lit, BOUNDARY_MASKS)
    return evaluate_circuit_mask(gates, output_sign)[0]


def dependency_count(gates: Circuit, projected_var: int) -> int:
    deps: List[bool] = [i == projected_var for i in range(K)]
    count = 0
    for a, b in gates:
        d = lit_dep(a, deps) or lit_dep(b, deps)
        deps.append(d)
        count += int(d)
    return count


def reachable_internal_gate_ids(gates: Circuit) -> set[int]:
    if not gates:
        return set()
    needed = {K + len(gates) - 1}
    stack = [K + len(gates) - 1]
    while stack:
        gate_sid = stack.pop()
        gi = gate_sid - K
        a, b = gates[gi]
        for lit in (a, b):
            child = sid(lit)
            if child >= K and child not in needed:
                needed.add(child)
                stack.append(child)
    return needed


def all_gates_reachable(gates: Circuit) -> bool:
    if not gates:
        return True
    return reachable_internal_gate_ids(gates) == set(range(K, K + len(gates)))


def gate_choices(available_signal_count: int) -> Iterable[Gate]:
    # Distinct signal IDs, AND commutativity canonicalized by a<b signal id.
    for a_sid, b_sid in combinations(range(available_signal_count), 2):
        for sa, sb in product((1, -1), repeat=2):
            yield (sa * (a_sid + 1), sb * (b_sid + 1))


def encoding(gates: Circuit, output_sign: int, boundary_output: int | None = None) -> str:
    if not gates:
        assert boundary_output is not None
        return f"OUT={'+' if output_sign > 0 else '-'}b{boundary_output}"
    parts = []
    for i, (a, b) in enumerate(gates):
        def fmt(lit: int) -> str:
            s = '+' if lit > 0 else '-'
            x = sid(lit)
            return f"{s}{'b' + str(x) if x < K else 'g' + str(x-K)}"
        parts.append(f"g{i}=({fmt(a)}&{fmt(b)})")
    parts.append(f"OUT={'+' if output_sign > 0 else '-'}g{len(gates)-1}")
    return ';'.join(parts)


def enumerate_circuits() -> List[Tuple[Circuit, int, int | None, int, str]]:
    """Return every admitted circuit as (gates,out_sign,boundary_output,truth,encoding)."""
    admitted: List[Tuple[Circuit, int, int | None, int, str]] = []

    # Zero-gate signed boundary outputs.
    for b in range(K):
        for out_sign in (1, -1):
            enc = encoding(tuple(), out_sign, b)
            admitted.append((tuple(), out_sign, b, output_truth(tuple(), out_sign, b), enc))

    def rec(prefix: Tuple[Gate, ...], target_len: int) -> None:
        if len(prefix) == target_len:
            if not all_gates_reachable(prefix):
                return
            for out_sign in (1, -1):
                enc = encoding(prefix, out_sign)
                admitted.append((prefix, out_sign, None, output_truth(prefix, out_sign), enc))
            return
        for gate in gate_choices(K + len(prefix)):
            rec(prefix + (gate,), target_len)

    for m in range(1, G_MAX + 1):
        rec(tuple(), m)

    # Encoding uniqueness is an internal enumeration sanity check.
    encs = [row[4] for row in admitted]
    assert len(encs) == len(set(encs)), "duplicate canonical circuit encoding"
    return admitted


def eval_row(gates: Circuit, output_sign: int, row: int, boundary_output: int | None = None) -> bool:
    vals: List[bool] = [bool((row >> i) & 1) for i in range(K)]

    def lv(lit: int) -> bool:
        v = vals[sid(lit)]
        return v if lit > 0 else (not v)

    for a, b in gates:
        assert sid(a) != sid(b)
        vals.append(lv(a) and lv(b))

    if gates:
        v = vals[K + len(gates) - 1]
    else:
        assert boundary_output is not None
        v = vals[boundary_output]
    return v if output_sign > 0 else (not v)


def row_truth_mask(gates: Circuit, output_sign: int, boundary_output: int | None = None) -> int:
    mask = 0
    for row in range(ROWS):
        if eval_row(gates, output_sign, row, boundary_output):
            mask |= 1 << row
    return mask


def main() -> None:
    circuits = enumerate_circuits()

    # Independent row evaluator must agree for every admitted circuit, not just samples.
    for gates, out_sign, b_out, truth, enc in circuits:
        replay = row_truth_mask(gates, out_sign, b_out)
        assert replay == truth, f"truth evaluator disagreement: {enc}"

    best: Dict[Tuple[int, int], Rep] = {}
    rep_by_encoding: Dict[str, Tuple[Circuit, int, int | None, int]] = {}
    distinct_functions = set()

    for gates, out_sign, b_out, truth, enc in circuits:
        distinct_functions.add(truth)
        rep_by_encoding[enc] = (gates, out_sign, b_out, truth)
        for p in range(K):
            dep = dependency_count(gates, p)
            rep = Rep(gates, out_sign, truth, dep, len(gates), enc)
            key = (truth, p)
            old = best.get(key)
            if old is None or (rep.dep_count, rep.gate_count, rep.encoding) < (
                old.dep_count,
                old.gate_count,
                old.encoding,
            ):
                best[key] = rep

    strict_replacements = []
    source_circuits_with_replacement = set()
    strict_by_projected_var = [0] * K

    for gates, out_sign, b_out, truth, enc in circuits:
        source_g = len(gates)
        for p in range(K):
            source_dep = dependency_count(gates, p)
            target = best[(truth, p)]
            admissible = (
                target.gate_count <= source_g
                and (target.dep_count < source_dep or target.gate_count < source_g)
            )
            if not admissible:
                continue
            # The equivalence condition is the catalog key; replay it independently.
            tgates, tout, tbout, ttruth = rep_by_encoding[target.encoding]
            assert ttruth == truth
            assert row_truth_mask(tgates, tout, tbout) == row_truth_mask(gates, out_sign, b_out)
            strict_replacements.append(
                {
                    "projected_var": p,
                    "truth_hex": f"{truth:04x}",
                    "source": enc,
                    "target": target.encoding,
                    "source_cost": [source_dep, source_g],
                    "target_cost": [target.dep_count, target.gate_count],
                }
            )
            source_circuits_with_replacement.add(enc)
            strict_by_projected_var[p] += 1

    strict_replacements.sort(
        key=lambda r: (
            r["source"],
            r["projected_var"],
            r["target"],
            r["truth_hex"],
        )
    )

    catalog_rows = []
    for (truth, p), rep in sorted(best.items()):
        catalog_rows.append(
            {
                "truth_hex": f"{truth:04x}",
                "projected_var": p,
                "dep_count": rep.dep_count,
                "gate_count": rep.gate_count,
                "encoding": rep.encoding,
            }
        )

    catalog_payload = {
        "schema": "JANUS_U1L2B0_LOCAL_EQUIVALENCE_CATALOG",
        "k": K,
        "g_max": G_MAX,
        "basis": "SIGNED_AND_DISTINCT_SIGNAL_IDS",
        "canonical_rows": catalog_rows,
    }
    catalog_bytes = json.dumps(catalog_payload, sort_keys=True, separators=(",", ":")).encode()
    catalog_sha = sha256(catalog_bytes).hexdigest()

    # Lexical, not cherry-picked, replay certificates.
    replay_receipts = strict_replacements[:16]

    # A machine-readable result summary; no assertion that improvements must exist.
    result = {
        "schema": "JANUS_U1L2B0_PROVIDER_RESULT",
        "status": "PASS_EXHAUSTIVE_FROZEN_LOCAL_SCOPE",
        "k": K,
        "g_max": G_MAX,
        "rows_per_truth_table": ROWS,
        "admitted_circuits": len(circuits),
        "distinct_functions_reached": len(distinct_functions),
        "canonical_function_projection_classes": len(best),
        "strict_replacement_pairs": len(strict_replacements),
        "source_circuits_with_at_least_one_strict_replacement": len(source_circuits_with_replacement),
        "strict_replacements_by_projected_var": strict_by_projected_var,
        "catalog_bytes": len(catalog_bytes),
        "catalog_sha256": catalog_sha,
        "lexical_replay_receipts": replay_receipts,
        "claim_ceiling": "P_VS_NP_OPEN",
        "next_gate_if_nontrivial": "U1-L2B1_EXACT_LOCAL_SATURATION_ON_PREBIRTH_PROJECTION_DAGS",
    }

    # Provider invariants.
    assert len(best) == len(distinct_functions) * K
    assert all(r["target_cost"] <= r["source_cost"] or r["target_cost"][0] < r["source_cost"][0]
               for r in strict_replacements)

    print(json.dumps(result, indent=2, sort_keys=True))
    print("RESULT_SHA256=" + sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest())


if __name__ == "__main__":
    main()
