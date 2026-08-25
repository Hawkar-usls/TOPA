#!/usr/bin/env python3
"""PF5 continuation refinement certificate v16.1 finite audit.

Exponential audit only on already-open seed 911000.

Start from the weak exact partition (depth, current exact PS cut). Repeatedly
split blocks synchronously by the multiset of successor block IDs. Every split
emits a compact representative witness showing a successor-block count
discrepancy. The process must stabilize at the same partition as v16's bottom-up
future-bisimulation, reproduce Bellman optimum 4, and lift a concrete width-4
order.

The raw 4096-state lattice and exact PS table are explicit audit oracles. Nothing
here claims polynomial symbolic discovery.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_slime_exact_optimality_gap_v11 as v11
import pf5_whole_order_prefix_state_quotient_v16 as v16

SEED = 911000
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7
V5 = "SLIME_LOG_FEEDBACK_RELATION_PRESSURE"


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location("janus_slime_v5_1_pin_v16_1", path)
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


def canonical_partition_ids(keys):
    """Assign deterministic integer IDs to arbitrary comparable JSON-ish keys."""
    unique = sorted(set(keys), key=repr)
    mapping = {key: i for i, key in enumerate(unique)}
    return [mapping[key] for key in keys]


def successor_multiset(mask, class_ids, leaf_count):
    return tuple(
        sorted(
            class_ids[mask | (1 << bit_index)]
            for bit_index in range(leaf_count)
            if not (mask & (1 << bit_index))
        )
    )


def discrepancy_witness(multiset_a, multiset_b):
    ca = Counter(multiset_a)
    cb = Counter(multiset_b)
    for block_id in sorted(set(ca) | set(cb)):
        if ca[block_id] != cb[block_id]:
            return {
                "successor_block_id": block_id,
                "count_a": ca[block_id],
                "count_b": cb[block_id],
            }
    raise AssertionError("different multisets without count discrepancy")


def concrete_lift_to_block(mask, target_block, class_ids, leaves):
    lifts = []
    for bit_index, leaf in enumerate(leaves):
        bit = 1 << bit_index
        if mask & bit:
            continue
        nxt = mask | bit
        if class_ids[nxt] == target_block:
            lifts.append({"leaf": leaf, "next_mask": nxt})
    return lifts


def partition_blocks(class_ids):
    blocks = defaultdict(list)
    for mask, cid in enumerate(class_ids):
        blocks[cid].append(mask)
    return blocks


def partition_digest(class_ids):
    blocks = [tuple(masks) for _, masks in sorted(partition_blocks(class_ids).items())]
    payload = json.dumps(blocks, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def same_partition(class_ids_a, class_ids_b):
    def normalized(class_ids):
        return {
            frozenset(masks)
            for masks in partition_blocks(class_ids).values()
        }
    return normalized(class_ids_a) == normalized(class_ids_b)


def initial_cost_partition(leaves, cut_values):
    full = (1 << len(leaves)) - 1
    keys = [
        (
            mask.bit_count(),
            v16.state_cost(mask, full, cut_values),
        )
        for mask in range(1 << len(leaves))
    ]
    return canonical_partition_ids(keys)


def refinement_round(class_ids, leaves, round_index):
    n = len(leaves)
    old_blocks = partition_blocks(class_ids)
    old_digest = partition_digest(class_ids)
    signatures = []
    successor_profiles = []
    transition_refs = 0

    for mask in range(1 << n):
        profile = successor_multiset(mask, class_ids, n)
        transition_refs += len(profile)
        successor_profiles.append(profile)
        # old class ID is included so refinement is monotone and never merges.
        signatures.append((class_ids[mask], profile))

    next_ids = canonical_partition_ids(signatures)
    next_digest = partition_digest(next_ids)
    next_blocks = partition_blocks(next_ids)

    split_certificates = []
    split_state_count = 0
    for old_id, masks in sorted(old_blocks.items()):
        child_groups = defaultdict(list)
        for mask in masks:
            child_groups[next_ids[mask]].append(mask)
        if len(child_groups) <= 1:
            continue
        split_state_count += len(masks)
        new_ids = sorted(child_groups)
        a = child_groups[new_ids[0]][0]
        b = child_groups[new_ids[1]][0]
        pa = successor_profiles[a]
        pb = successor_profiles[b]
        diff = discrepancy_witness(pa, pb)
        target = diff["successor_block_id"]
        cert = {
            "round": round_index,
            "old_block_id": old_id,
            "old_block_size": len(masks),
            "old_partition_digest": old_digest,
            "new_partition_digest": next_digest,
            "representative_a_mask": a,
            "representative_b_mask": b,
            "representative_a_prefix": v16.mask_to_leaves(a, leaves),
            "representative_b_prefix": v16.mask_to_leaves(b, leaves),
            "successor_multiset_a": list(pa),
            "successor_multiset_b": list(pb),
            "discrepancy": diff,
            "concrete_lifts_a_to_discrepant_block": concrete_lift_to_block(
                a, target, class_ids, leaves
            ),
            "concrete_lifts_b_to_discrepant_block": concrete_lift_to_block(
                b, target, class_ids, leaves
            ),
            "resulting_new_block_ids": new_ids,
        }
        # Independent local replay of the split witness.
        assert class_ids[a] == class_ids[b] == old_id
        assert pa != pb
        assert Counter(pa)[target] != Counter(pb)[target]
        assert next_ids[a] != next_ids[b]
        split_certificates.append(cert)

    # Monotonicity: every next block must be contained in exactly one old block.
    monotonic = True
    for masks in next_blocks.values():
        parents = {class_ids[mask] for mask in masks}
        if len(parents) != 1:
            monotonic = False
            break
    if not monotonic:
        raise AssertionError("refinement merged previously separated states")

    return next_ids, {
        "round": round_index,
        "old_class_count": len(old_blocks),
        "new_class_count": len(next_blocks),
        "split_block_count": len(split_certificates),
        "split_state_count": split_state_count,
        "transition_refs": transition_refs,
        "old_partition_digest": old_digest,
        "new_partition_digest": next_digest,
        "monotone_refinement": True,
        "split_certificates": split_certificates,
    }


def refine_to_fixed_point(initial_ids, leaves):
    current = list(initial_ids)
    rounds = []
    all_certs = []
    round_index = 1
    while True:
        nxt, receipt = refinement_round(current, leaves, round_index)
        rounds.append({k: v for k, v in receipt.items() if k != "split_certificates"})
        all_certs.extend(receipt["split_certificates"])
        if same_partition(current, nxt):
            current = nxt
            break
        current = nxt
        round_index += 1
        if round_index > len(leaves) + 2:
            raise AssertionError("unexpectedly many refinement rounds for ranked DAG")
    return current, rounds, all_certs


def quotient_bellman_and_lift(class_ids, leaves, cut_values):
    n = len(leaves)
    full = (1 << n) - 1
    blocks = partition_blocks(class_ids)

    class_depth = {}
    class_cost = {}
    class_children = {}
    for cid, masks in blocks.items():
        representative = masks[0]
        depths = {mask.bit_count() for mask in masks}
        costs = {v16.state_cost(mask, full, cut_values) for mask in masks}
        profiles = {successor_multiset(mask, class_ids, n) for mask in masks}
        if len(depths) != 1 or len(costs) != 1 or len(profiles) != 1:
            raise AssertionError("fixed point is not a replayable future congruence")
        class_depth[cid] = next(iter(depths))
        class_cost[cid] = next(iter(costs))
        class_children[cid] = next(iter(profiles))

    by_depth = defaultdict(list)
    for cid, depth in class_depth.items():
        by_depth[depth].append(cid)

    future = {}
    for depth in range(n, -1, -1):
        for cid in sorted(by_depth[depth]):
            children = class_children[cid]
            if not children:
                future[cid] = 0
            else:
                future[cid] = min(
                    max(class_cost[child], future[child])
                    for child in children
                )

    mask = 0
    order = []
    lift_checks = 0
    while mask != full:
        cid = class_ids[mask]
        target = future[cid]
        candidates = []
        for bit_index, leaf in enumerate(leaves):
            bit = 1 << bit_index
            if mask & bit:
                continue
            nxt = mask | bit
            child = class_ids[nxt]
            value = max(class_cost[child], future[child])
            lift_checks += 1
            if value == target:
                candidates.append((leaf, bit_index, child))
        if not candidates:
            raise AssertionError("quotient action has no concrete lift")
        leaf, bit_index, _ = min(candidates)
        order.append(leaf)
        mask |= 1 << bit_index

    singleton_max = max(cut_values[1 << i] for i in range(n))
    quotient_value = max(singleton_max, future[class_ids[0]])
    return quotient_value, order, lift_checks


def run(producer, producer_identity):
    formula = v9.random_connected_3cnf(SEED, VARIABLE_COUNT, CLAUSE_COUNT)
    router = producer.SlimeLogFeedbackCandidateRouter()
    manifest = router.generate_manifest(formula)
    v5_order = next(
        c.linear_leaf_order for c in manifest.candidates if c.name == V5
    )
    leaves = sorted(v5_order)
    leaf_index = {leaf: i for i, leaf in enumerate(leaves)}
    assert len(leaves) == 12

    cut_values, cut_ledger = v11.exact_cut_cache(formula, leaves)
    raw_future, _, raw_bellman_checks = v16.exact_future_bellman(leaves, cut_values)
    exact_bisim = v16.exact_future_bisimulation(leaves, cut_values, raw_future)

    initial_ids = initial_cost_partition(leaves, cut_values)
    final_ids, rounds, certificates = refine_to_fixed_point(initial_ids, leaves)

    matches_v16 = same_partition(final_ids, exact_bisim["class_id"])
    if not matches_v16:
        raise AssertionError("continuation refinement did not reach v16 bisimulation")

    quotient_value, lifted_order, lift_checks = quotient_bellman_and_lift(
        final_ids, leaves, cut_values
    )
    lifted_width = v11.order_width_from_cache(lifted_order, leaf_index, cut_values)
    if quotient_value != 4 or lifted_width != 4:
        raise AssertionError("refined quotient failed exact bottleneck replay")

    cert_payload = json.dumps(
        certificates, sort_keys=True, separators=(",", ":")
    ).encode()
    round_transition_refs = sum(row["transition_refs"] for row in rounds)

    result = {
        "artifact_id": "PF5-CONTINUATION-REFINEMENT-CERTIFICATE-V16.1",
        "status": "FINITE_CONTINUATION_REFINEMENT_AUDIT_COMPLETE",
        "seed": SEED,
        "posthoc_not_holdout": True,
        "producer": producer_identity,
        "raw_subset_state_count": 1 << len(leaves),
        "initial_partition": {
            "definition": "(depth,current_exact_ps_cut)",
            "class_count": len(partition_blocks(initial_ids)),
            "partition_digest": partition_digest(initial_ids),
        },
        "refinement_rounds": rounds,
        "stabilized_after_rounds": len(rounds),
        "final_partition": {
            "class_count": len(partition_blocks(final_ids)),
            "partition_digest": partition_digest(final_ids),
            "matches_v16_future_bisimulation": matches_v16,
            "v16_bisimulation_class_count": exact_bisim["summary"][
                "future_bisimulation_class_count"
            ],
        },
        "split_certificate_count": len(certificates),
        "split_certificates_sha256": hashlib.sha256(cert_payload).hexdigest(),
        "split_certificate_bytes": len(cert_payload),
        "split_certificate_examples": certificates[:5],
        "quotient_bellman_value": quotient_value,
        "quotient_lifted_order": lifted_order,
        "quotient_lifted_width": lifted_width,
        "conditional_theorem": {
            "explicit_refinement_is_sound_on_finite_prefix_DAG": True,
            "fixed_point_is_future_congruence": True,
            "quotient_bellman_and_concrete_lift_are_exact": True,
            "polynomial_if_symbolic_blocks_splits_transitions_and_certificates_are_polynomially_bounded": True,
            "universal_polynomial_symbolic_refinement_exists": "OPEN",
        },
        "global_cost_ledger": {
            "slime_manifest_generation_ops": manifest.total_generation_ops,
            "exact_ps_cut_evaluations": cut_ledger["cuts"],
            "exact_ps_assignment_rows": cut_ledger["assignment_rows"],
            "exact_ps_literal_checks": cut_ledger["literal_checks"],
            "raw_bellman_transition_checks": raw_bellman_checks,
            "refinement_transition_refs": round_transition_refs,
            "split_certificate_bytes": len(cert_payload),
            "quotient_concrete_lift_checks": lift_checks,
        },
        "epistemic_firewall": {
            "raw_prefix_enumeration_is_exponential_audit_only": True,
            "exact_ps_table_is_exponential_audit_only": True,
            "exact_v16_bisimulation_is_used_only_as_independent_final_partition_oracle": True,
            "split_witnesses_use_only_prior_partition_successor_blocks": True,
            "no_merge_is_authorized_by_similarity": True,
            "no_claim_of_polynomial_split_discovery": True,
        },
        "next_gate": "SYMBOLIC_CONTINUATION_REFINEMENT_WITH_POLYNOMIAL_BLOCK_AND_SPLIT_BOUNDS",
        "universal_polynomial_prefix_quotient": "OPEN",
        "p_vs_np": "OPEN",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--producer-path", type=Path, required=True)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    raw = args.producer_path.read_bytes()
    producer = import_producer(args.producer_path)
    result = run(
        producer,
        {
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "PINNED_V5_1_PRODUCER_NOT_REFINEMENT_ORACLE",
        },
    )
    if args.json_out:
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
        )

    print("PF5_CONTINUATION_REFINEMENT_V16_1 =", result["status"])
    print("INITIAL_CLASSES =", result["initial_partition"]["class_count"])
    print("ROUND_COUNTS =", [
        (r["round"], r["old_class_count"], r["new_class_count"], r["split_block_count"])
        for r in result["refinement_rounds"]
    ])
    print("FINAL_CLASSES =", result["final_partition"]["class_count"])
    print("MATCHES_V16_BISIMULATION =", result["final_partition"]["matches_v16_future_bisimulation"])
    print("SPLIT_CERTIFICATES =", result["split_certificate_count"])
    print("SPLIT_CERT_BYTES =", result["split_certificate_bytes"])
    print("QUOTIENT_VALUE / WIDTH =", result["quotient_bellman_value"], result["quotient_lifted_width"])
    print("GLOBAL_COST_LEDGER =", result["global_cost_ledger"])
    print("UNIVERSAL_POLYNOMIAL_PREFIX_QUOTIENT = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
