#!/usr/bin/env python3
"""PF5 projection-chain signature-cap diagnostic v12.2.

Post-hoc probe on already-observed seed 908001 only.  It tests a stronger
assignment-independent upper bound on precisely-satisfiable signature count.

For distinct nonempty projected clauses ordered by literal-set inclusion, any
chain A1 subseteq A2 subseteq ... subseteq At has at most t+1 satisfaction-bit
patterns because SAT(A_i) implies SAT(A_{i+1}).  Therefore for any partition of
the distinct projected clauses into chains of lengths t_j,

  |PS(projected)| <= product_j (t_j + 1).

Together with the assignment bound this gives

  |PS(projected)| <= min(2^r, product_j(t_j+1)),

where r is the number of visible variables.  Duplicate projected clauses are
collapsed because their satisfaction bits are identical.  A deterministic
minimum-cardinality chain cover is obtained from maximum bipartite matching in
the inclusion poset.  The exact PS scorer is used only afterwards to diagnose
whether this source-only theorem breaks the v12 cap tie.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_slime_exact_optimality_gap_v11 as v11

SEED = 908001
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location("slime_v2_chain_probe_pin", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load producer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def projected_distinct_clauses(formula, clause_indices, visible_variables):
    distinct = set()
    for index in sorted(clause_indices):
        projected = frozenset(
            lit for lit in formula[index] if abs(lit) in visible_variables
        )
        if projected:
            distinct.add(projected)
    return sorted(distinct, key=lambda c: (len(c), tuple(sorted(c))))


def minimum_chain_cover(clauses):
    """Deterministic min-cardinality chain cover of a finite inclusion poset."""
    n = len(clauses)
    if n == 0:
        return []
    # Edge i->j means clause i is a strict subset of clause j.
    edges = {
        i: [
            j for j in range(n)
            if i != j and clauses[i] < clauses[j]
        ]
        for i in range(n)
    }
    for i in edges:
        edges[i].sort(key=lambda j: (len(clauses[j]), tuple(sorted(clauses[j]))))

    match_right = {}

    def augment(left, seen):
        for right in edges[left]:
            if right in seen:
                continue
            seen.add(right)
            if right not in match_right or augment(match_right[right], seen):
                match_right[right] = left
                return True
        return False

    for left in range(n):
        augment(left, set())

    successor = {left: right for right, left in match_right.items()}
    predecessor = {right: left for right, left in match_right.items()}
    starts = [i for i in range(n) if i not in predecessor]
    chains = []
    covered = set()
    for start in starts:
        chain = []
        cur = start
        while True:
            if cur in covered:
                raise AssertionError("chain cover cycle")
            covered.add(cur)
            chain.append(cur)
            if cur not in successor:
                break
            cur = successor[cur]
        chains.append(chain)
    if covered != set(range(n)):
        raise AssertionError("incomplete chain cover")
    return chains


def chain_signature_cap(formula, selected_leaves):
    all_clause_indices = set(range(len(formula)))
    all_variables = {abs(lit) for clause in formula for lit in clause}
    selected_variables = {
        int(leaf.split(":", 1)[1])
        for leaf in selected_leaves if leaf.startswith("v:")
    }
    selected_clauses = {
        int(leaf.split(":", 1)[1])
        for leaf in selected_leaves if leaf.startswith("c:")
    }
    right_variables = all_variables - selected_variables

    left_distinct = projected_distinct_clauses(
        formula, all_clause_indices - selected_clauses, selected_variables
    )
    right_distinct = projected_distinct_clauses(
        formula, selected_clauses, right_variables
    )
    left_chains = minimum_chain_cover(left_distinct)
    right_chains = minimum_chain_cover(right_distinct)

    def side(visible_count, distinct, chains):
        product_bound = 1
        lengths = []
        for chain in chains:
            length = len(chain)
            lengths.append(length)
            product_bound *= length + 1
        assignment_bound = 1 << visible_count
        return {
            "visible_variables": visible_count,
            "distinct_projected_clauses": len(distinct),
            "chain_lengths": lengths,
            "chain_product_bound": product_bound,
            "assignment_bound": assignment_bound,
            "certified_signature_cap": min(assignment_bound, product_bound),
        }

    left = side(len(selected_variables), left_distinct, left_chains)
    right = side(len(right_variables), right_distinct, right_chains)
    combined = max(left["certified_signature_cap"], right["certified_signature_cap"])
    return {
        "left": left,
        "right": right,
        "combined_cap": combined,
        "combined_cap_log2_ceiling": 0 if combined <= 1 else math.ceil(math.log2(combined)),
    }


def run(producer, producer_identity):
    formula = v9.random_connected_3cnf(SEED, VARIABLE_COUNT, CLAUSE_COUNT)
    router = producer.SlimeSignatureCapCandidateRouter()
    manifest = router.generate_manifest(formula)
    new_order = next(
        c.linear_leaf_order for c in manifest.candidates
        if c.name == "SLIME_SIGNATURE_CAP_PRESSURE"
    )
    leaves = sorted(new_order)
    leaf_index = {leaf: i for i, leaf in enumerate(leaves)}
    cut_values, ledger = v11.exact_cut_cache(formula, leaves)

    # v12.1 found the first v2 local gap after prefix c:0,v:2,c:1.
    prefix = set(new_order[:3])
    remaining = sorted(set(leaves) - prefix)
    candidates = []
    for leaf in remaining:
        trial = prefix | {leaf}
        mask = 0
        for x in trial:
            mask |= 1 << leaf_index[x]
        old_cap = producer.signature_cap_exponent(
            producer.v1.canonical_cnf(formula), trial
        )
        chain_cap = chain_signature_cap(formula, trial)
        candidates.append(
            {
                "leaf": leaf,
                "v2_cap_log2": old_cap["cap_log2"],
                "chain_cap": chain_cap,
                "exact_next_ps": cut_values[mask],
            }
        )

    chosen = next(row for row in candidates if row["leaf"] == new_order[3])
    exact_best = min(row["exact_next_ps"] for row in candidates)
    chain_best = min(row["chain_cap"]["combined_cap"] for row in candidates)
    exact_best_rows = [row for row in candidates if row["exact_next_ps"] == exact_best]
    chain_best_rows = [row for row in candidates if row["chain_cap"]["combined_cap"] == chain_best]
    distinguishes = (
        chosen["chain_cap"]["combined_cap"] > chain_best
        and any(row["exact_next_ps"] < chosen["exact_next_ps"] for row in chain_best_rows)
    ) or (
        any(
            row["chain_cap"]["combined_cap"] < chosen["chain_cap"]["combined_cap"]
            and row["exact_next_ps"] < chosen["exact_next_ps"]
            for row in candidates
        )
    )

    result = {
        "artifact_id": "PF5-PROJECTION-CHAIN-CAP-PROBE-V12.2",
        "status": "POSTHOC_THEOREM_FEATURE_PROBE_COMPLETE",
        "seed": SEED,
        "posthoc_not_holdout": True,
        "producer": producer_identity,
        "formula": [list(c) for c in formula],
        "prefix_before_first_v2_local_gap": new_order[:3],
        "v2_chosen_next": new_order[3],
        "candidate_rows": candidates,
        "chosen_row": chosen,
        "exact_best_next_ps": exact_best,
        "exact_best_rows": exact_best_rows,
        "chain_cap_best": chain_best,
        "chain_cap_best_rows": chain_best_rows,
        "chain_cap_breaks_observed_v2_tie_in_helpful_direction": distinguishes,
        "theorem": {
            "chain_monotonicity": "A subseteq B implies SAT(A) => SAT(B)",
            "chain_patterns": "a chain of t distinct projected clauses has at most t+1 satisfaction patterns",
            "cover_bound": "PS <= product_j(chain_length_j+1)",
            "assignment_bound": "PS <= 2^visible_variables",
            "combined": "PS <= min(2^r, product_j(chain_length_j+1))",
            "duplicate_projected_clauses_collapsed": True,
            "source_only": True,
            "polynomial_feature_construction": True,
        },
        "exact_verifier_ledger": ledger,
        "p_vs_np": "OPEN",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-path", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    raw = args.producer_path.read_bytes()
    producer = import_producer(args.producer_path)
    result = run(
        producer,
        {
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "PINNED_V2_POSTHOC_FEATURE_PROBE",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_PROJECTION_CHAIN_CAP_PROBE_V12_2 =", result["status"])
    print("PREFIX =", result["prefix_before_first_v2_local_gap"])
    print("V2_CHOSEN =", result["v2_chosen_next"])
    for row in result["candidate_rows"]:
        print(row["leaf"], "V2LOG=", row["v2_cap_log2"], "CHAIN=", row["chain_cap"]["combined_cap"], "EXACT=", row["exact_next_ps"])
    print("CHAIN_CAP_BREAKS_TIE_HELPFULLY =", result["chain_cap_breaks_observed_v2_tie_in_helpful_direction"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
