#!/usr/bin/env python3
"""PF5 whole-order prefix-state quotient v16 finite audit.

This script is deliberately exponential and is used only on the already-open
seed 911000. It does four things:

1. rebuilds the frozen Slime v5 order from the pinned external producer;
2. computes the exact PS cut value for every subset of the 12 incidence leaves;
3. computes the exact Bellman future bottleneck on the full subset lattice and
   locates the first state where a locally exact-minimum Slime action is not a
   globally Bellman-optimal action;
4. constructs an audit-only bottom-up future-bisimulation partition from exact
   cut costs and successor-class multisets, then verifies that Bellman DP on the
   finite quotient reproduces the raw optimum and lifts to a concrete order.

The construction of the cut table, Bellman table, and audit bisimulation all
enumerate exponentially many raw subsets. They are *not* a polynomial SAT or
layout algorithm. The universal target is to discover an equivalent compact
proof-carrying quotient directly from the source in polynomial total work.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pf5_slime_pswidth_blind_probe_v9 as v9
import pf5_slime_exact_optimality_gap_v11 as v11

SEED = 911000
VARIABLE_COUNT = 5
CLAUSE_COUNT = 7
V5 = "SLIME_LOG_FEEDBACK_RELATION_PRESSURE"


def import_producer(path: Path):
    spec = importlib.util.spec_from_file_location("janus_slime_v5_1_pin_v16", path)
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


def state_cost(mask: int, full: int, cut_values) -> int:
    if mask == 0 or mask == full:
        return 0
    return int(cut_values[mask])


def exact_future_bellman(leaves, cut_values):
    """Raw-subset Bellman table for min_order max_future_prefix_cut."""
    n = len(leaves)
    total_states = 1 << n
    full = total_states - 1
    inf = 10**18
    future = [inf] * total_states
    best_bit = [-1] * total_states
    transition_checks = 0
    future[full] = 0

    # Every successor has depth +1, so descending popcount is a topological DP.
    masks_by_depth = [[] for _ in range(n + 1)]
    for mask in range(total_states):
        masks_by_depth[mask.bit_count()].append(mask)

    for depth in range(n - 1, -1, -1):
        for mask in masks_by_depth[depth]:
            best_value = inf
            best_action = -1
            for bit_index in range(n):
                bit = 1 << bit_index
                if mask & bit:
                    continue
                nxt = mask | bit
                immediate = state_cost(nxt, full, cut_values)
                value = max(immediate, future[nxt])
                transition_checks += 1
                if value < best_value or (
                    value == best_value and leaves[bit_index] < leaves[best_action]
                ):
                    best_value = value
                    best_action = bit_index
            future[mask] = best_value
            best_bit[mask] = best_action

    return future, best_bit, transition_checks


def reconstruct_bellman_order(leaves, best_bit):
    full = (1 << len(leaves)) - 1
    mask = 0
    order = []
    while mask != full:
        bit_index = best_bit[mask]
        if bit_index < 0:
            raise AssertionError("missing Bellman action")
        bit = 1 << bit_index
        if mask & bit:
            raise AssertionError("Bellman action already selected")
        order.append(leaves[bit_index])
        mask |= bit
    return order


def order_width(order, leaf_index, cut_values):
    return v11.order_width_from_cache(order, leaf_index, cut_values)


def mask_to_leaves(mask, leaves):
    return [leaves[i] for i in range(len(leaves)) if mask & (1 << i)]


def v5_path_diagnostics(v5_order, leaves, leaf_index, cut_values, future):
    full = (1 << len(leaves)) - 1
    mask = 0
    rows = []
    local_exact_failures = 0
    bellman_failures = 0

    for step, chosen_leaf in enumerate(v5_order):
        chosen_index = leaf_index[chosen_leaf]
        candidates = []
        for bit_index, leaf in enumerate(leaves):
            bit = 1 << bit_index
            if mask & bit:
                continue
            nxt = mask | bit
            immediate = state_cost(nxt, full, cut_values)
            continuation = future[nxt]
            total = max(immediate, continuation)
            candidates.append(
                {
                    "leaf": leaf,
                    "next_mask": nxt,
                    "immediate_exact_ps": immediate,
                    "future_opt_after_action": continuation,
                    "action_bottleneck_value": total,
                }
            )

        chosen = next(row for row in candidates if row["leaf"] == chosen_leaf)
        best_immediate = min(row["immediate_exact_ps"] for row in candidates)
        best_bellman = min(row["action_bottleneck_value"] for row in candidates)
        immediate_best = [
            row for row in candidates if row["immediate_exact_ps"] == best_immediate
        ]
        bellman_best = [
            row for row in candidates if row["action_bottleneck_value"] == best_bellman
        ]
        same_immediate_better_future = [
            row
            for row in candidates
            if row["immediate_exact_ps"] == chosen["immediate_exact_ps"]
            and row["action_bottleneck_value"] < chosen["action_bottleneck_value"]
        ]
        if chosen["immediate_exact_ps"] != best_immediate:
            local_exact_failures += 1
        if chosen["action_bottleneck_value"] != best_bellman:
            bellman_failures += 1

        rows.append(
            {
                "step": step,
                "prefix_before": mask_to_leaves(mask, leaves),
                "mask_before": mask,
                "state_future_optimum": future[mask],
                "chosen": chosen,
                "best_immediate_exact_ps": best_immediate,
                "immediate_exact_min_candidates": immediate_best,
                "best_bellman_action_value": best_bellman,
                "bellman_optimal_candidates": bellman_best,
                "chosen_is_immediate_exact_minimum": (
                    chosen["immediate_exact_ps"] == best_immediate
                ),
                "chosen_is_bellman_optimal": (
                    chosen["action_bottleneck_value"] == best_bellman
                ),
                "same_immediate_better_future_candidates": same_immediate_better_future,
            }
        )
        mask |= 1 << chosen_index

    return rows, local_exact_failures, bellman_failures


def weak_label_audit(leaves, cut_values, future):
    n = len(leaves)
    full = (1 << n) - 1
    weak_cost = defaultdict(list)
    weak_value = defaultdict(list)

    def transition_profile(mask):
        rows = []
        for bit_index in range(n):
            bit = 1 << bit_index
            if mask & bit:
                continue
            nxt = mask | bit
            rows.append(
                (
                    state_cost(nxt, full, cut_values),
                    int(future[nxt]),
                )
            )
        return tuple(sorted(rows))

    profiles = {}
    for mask in range(1 << n):
        depth = mask.bit_count()
        cost = state_cost(mask, full, cut_values)
        value = int(future[mask])
        profile = transition_profile(mask)
        profiles[mask] = profile
        weak_cost[(depth, cost)].append(mask)
        weak_value[(depth, cost, value)].append(mask)

    def summarize(groups):
        unsafe = []
        merged_state_count = 0
        for label, masks in groups.items():
            if len(masks) <= 1:
                continue
            merged_state_count += len(masks)
            unique_profiles = {profiles[m] for m in masks}
            if len(unique_profiles) > 1:
                unsafe.append((label, masks, unique_profiles))
        example = None
        if unsafe:
            label, masks, unique_profiles = unsafe[0]
            m0 = masks[0]
            m1 = next(m for m in masks[1:] if profiles[m] != profiles[m0])
            example = {
                "label": list(label),
                "mask_a": m0,
                "state_a": mask_to_leaves(m0, leaves),
                "profile_a": [list(x) for x in profiles[m0]],
                "mask_b": m1,
                "state_b": mask_to_leaves(m1, leaves),
                "profile_b": [list(x) for x in profiles[m1]],
            }
        return {
            "class_count": len(groups),
            "states_inside_nontrivial_classes": merged_state_count,
            "unsafe_transition_collision_class_count": len(unsafe),
            "first_unsafe_collision": example,
        }

    return {
        "depth_plus_current_cut": summarize(weak_cost),
        "depth_plus_current_cut_plus_exact_future_value": summarize(weak_value),
    }


def exact_future_bisimulation(leaves, cut_values, future):
    """Audit-only unlabeled successor bisimulation on the full subset DAG.

    Class signature at a state is:
      (depth, exact current cut, sorted multiset of successor class ids).
    Action identities are abstracted, but each concrete representative retains
    a local leaf->successor-class lift table for replay.
    """
    n = len(leaves)
    full = (1 << n) - 1
    class_id = [-1] * (1 << n)
    class_signature_to_id = {}
    class_cost = {}
    class_children = {}
    class_future = {}
    class_members = defaultdict(list)
    next_class_id = 0
    signature_build_transition_refs = 0

    masks_by_depth = [[] for _ in range(n + 1)]
    for mask in range(1 << n):
        masks_by_depth[mask.bit_count()].append(mask)

    # Terminal.
    terminal_signature = (n, 0, ())
    class_signature_to_id[terminal_signature] = next_class_id
    class_id[full] = next_class_id
    class_cost[next_class_id] = 0
    class_children[next_class_id] = ()
    class_future[next_class_id] = 0
    class_members[next_class_id].append(full)
    next_class_id += 1

    for depth in range(n - 1, -1, -1):
        for mask in masks_by_depth[depth]:
            children = []
            for bit_index in range(n):
                bit = 1 << bit_index
                if mask & bit:
                    continue
                nxt = mask | bit
                cid = class_id[nxt]
                if cid < 0:
                    raise AssertionError("successor class not yet assigned")
                children.append(cid)
                signature_build_transition_refs += 1
            children_tuple = tuple(sorted(children))
            cost = state_cost(mask, full, cut_values)
            signature = (depth, cost, children_tuple)
            cid = class_signature_to_id.get(signature)
            if cid is None:
                cid = next_class_id
                next_class_id += 1
                class_signature_to_id[signature] = cid
                class_cost[cid] = cost
                class_children[cid] = children_tuple
                if not children_tuple:
                    class_future[cid] = 0
                else:
                    class_future[cid] = min(
                        max(class_cost[child], class_future[child])
                        for child in children_tuple
                    )
            class_id[mask] = cid
            class_members[cid].append(mask)

    # Verify every concrete raw state's Bellman value agrees with its class.
    mismatches = []
    for mask, cid in enumerate(class_id):
        if int(future[mask]) != int(class_future[cid]):
            mismatches.append((mask, cid, int(future[mask]), int(class_future[cid])))
    if mismatches:
        raise AssertionError(f"future-bisimulation mismatch: {mismatches[:3]}")

    # Verify same-class concrete states really have the same successor-class multiset.
    replay_failures = 0
    for cid, masks in class_members.items():
        expected = class_children[cid]
        for mask in masks:
            if mask == full:
                observed = ()
            else:
                observed = tuple(
                    sorted(
                        class_id[mask | (1 << bit_index)]
                        for bit_index in range(n)
                        if not (mask & (1 << bit_index))
                    )
                )
            if observed != expected:
                replay_failures += 1
    if replay_failures:
        raise AssertionError("successor-class replay failure")

    raw_by_depth = {depth: len(masks_by_depth[depth]) for depth in range(n + 1)}
    classes_by_depth = {}
    for depth in range(n + 1):
        classes_by_depth[depth] = len(
            {
                class_id[mask]
                for mask in masks_by_depth[depth]
            }
        )

    nontrivial_classes = sum(1 for masks in class_members.values() if len(masks) > 1)
    largest_class = max(len(masks) for masks in class_members.values())

    return {
        "class_id": class_id,
        "class_cost": class_cost,
        "class_children": class_children,
        "class_future": class_future,
        "class_members": class_members,
        "summary": {
            "raw_subset_state_count": 1 << n,
            "future_bisimulation_class_count": next_class_id,
            "nontrivial_class_count": nontrivial_classes,
            "largest_class_size": largest_class,
            "raw_states_by_depth": raw_by_depth,
            "classes_by_depth": classes_by_depth,
            "signature_build_transition_refs": signature_build_transition_refs,
            "replay_failures": replay_failures,
            "construction_is_exponential_audit_only": True,
        },
    }


def quotient_lift_order(leaves, cut_values, bisimulation):
    n = len(leaves)
    full = (1 << n) - 1
    class_id = bisimulation["class_id"]
    class_cost = bisimulation["class_cost"]
    class_future = bisimulation["class_future"]

    mask = 0
    order = []
    lift_checks = 0
    while mask != full:
        cid = class_id[mask]
        target_value = class_future[cid]
        candidates = []
        for bit_index, leaf in enumerate(leaves):
            bit = 1 << bit_index
            if mask & bit:
                continue
            nxt = mask | bit
            child = class_id[nxt]
            value = max(class_cost[child], class_future[child])
            lift_checks += 1
            if value == target_value:
                candidates.append((leaf, bit_index, child))
        if not candidates:
            raise AssertionError("quotient action has no concrete lift")
        leaf, bit_index, _ = min(candidates)
        order.append(leaf)
        mask |= 1 << bit_index
    return order, lift_checks


def run(producer, producer_identity):
    formula = v9.random_connected_3cnf(SEED, VARIABLE_COUNT, CLAUSE_COUNT)
    router = producer.SlimeLogFeedbackCandidateRouter()
    manifest = router.generate_manifest(formula)
    v5_order = next(
        c.linear_leaf_order
        for c in manifest.candidates
        if c.name == V5
    )
    leaves = sorted(v5_order)
    leaf_index = {leaf: i for i, leaf in enumerate(leaves)}
    n = len(leaves)
    assert n == 12

    cut_values, cut_ledger = v11.exact_cut_cache(formula, leaves)
    future, best_bit, bellman_checks = exact_future_bellman(leaves, cut_values)
    singleton_max = max(cut_values[1 << i] for i in range(n))
    raw_bellman_optimum = max(singleton_max, future[0])
    raw_bellman_order = reconstruct_bellman_order(leaves, best_bit)
    raw_bellman_order_width = order_width(raw_bellman_order, leaf_index, cut_values)
    v5_width = order_width(v5_order, leaf_index, cut_values)

    assert v5_width == 5
    assert raw_bellman_optimum == 4
    assert raw_bellman_order_width == raw_bellman_optimum

    path_rows, local_exact_failures, bellman_failures = v5_path_diagnostics(
        v5_order,
        leaves,
        leaf_index,
        cut_values,
        future,
    )
    assert local_exact_failures == 0
    assert bellman_failures > 0
    first_future_obstruction = next(
        row for row in path_rows if not row["chosen_is_bellman_optimal"]
    )

    weak = weak_label_audit(leaves, cut_values, future)
    bisimulation = exact_future_bisimulation(leaves, cut_values, future)
    quotient_order, lift_checks = quotient_lift_order(
        leaves,
        cut_values,
        bisimulation,
    )
    quotient_width = order_width(quotient_order, leaf_index, cut_values)
    quotient_start_class = bisimulation["class_id"][0]
    quotient_bellman_value = max(
        singleton_max,
        bisimulation["class_future"][quotient_start_class],
    )
    assert quotient_bellman_value == raw_bellman_optimum
    assert quotient_width == raw_bellman_optimum

    # Compact the first obstruction for the result payload.
    obstruction = {
        "step": first_future_obstruction["step"],
        "prefix_before": first_future_obstruction["prefix_before"],
        "mask_before": first_future_obstruction["mask_before"],
        "state_future_optimum": first_future_obstruction["state_future_optimum"],
        "chosen": first_future_obstruction["chosen"],
        "best_immediate_exact_ps": first_future_obstruction["best_immediate_exact_ps"],
        "best_bellman_action_value": first_future_obstruction["best_bellman_action_value"],
        "bellman_optimal_candidates": first_future_obstruction["bellman_optimal_candidates"],
        "same_immediate_better_future_candidates": first_future_obstruction[
            "same_immediate_better_future_candidates"
        ],
        "chosen_is_immediate_exact_minimum": first_future_obstruction[
            "chosen_is_immediate_exact_minimum"
        ],
        "chosen_is_bellman_optimal": first_future_obstruction[
            "chosen_is_bellman_optimal"
        ],
    }

    result = {
        "artifact_id": "PF5-WHOLE-ORDER-PREFIX-STATE-QUOTIENT-V16",
        "status": "FINITE_WHOLE_ORDER_AUDIT_COMPLETE",
        "seed": SEED,
        "posthoc_not_holdout": True,
        "producer": producer_identity,
        "formula": [list(c) for c in formula],
        "leaf_count": n,
        "raw_subset_state_count": 1 << n,
        "v5_order": v5_order,
        "v5_width": v5_width,
        "raw_bellman_optimal_order": raw_bellman_order,
        "raw_bellman_optimum": raw_bellman_optimum,
        "singleton_leaf_edge_max": singleton_max,
        "v5_local_exact_failure_count": local_exact_failures,
        "v5_bellman_future_failure_count": bellman_failures,
        "first_pure_future_obstruction": obstruction,
        "weak_scalar_label_audit": weak,
        "audit_future_bisimulation": bisimulation["summary"],
        "audit_quotient_start_class": quotient_start_class,
        "audit_quotient_bellman_value": quotient_bellman_value,
        "audit_quotient_lifted_order": quotient_order,
        "audit_quotient_lifted_width": quotient_width,
        "conditional_theorem_contract": {
            "Q1_rank_terminal_preservation": True,
            "Q2_exact_cost_preservation_required": True,
            "Q3_abstract_action_coverage_required": True,
            "Q4_transition_closure_required": True,
            "Q5_future_congruence_bisimulation_required": True,
            "Q6_concrete_order_lift_required": True,
            "Q7_polynomial_discovery_state_transition_and_certificate_bound_required": True,
            "if_Q1_Q7_and_polynomial_state_count_then_exact_bottleneck_DP_is_polynomial": True,
        },
        "global_cost_ledger": {
            "slime_v5_manifest_generation_ops": manifest.total_generation_ops,
            "exact_ps_cut_evaluations": cut_ledger["cuts"],
            "exact_ps_assignment_rows": cut_ledger["assignment_rows"],
            "exact_ps_literal_checks": cut_ledger["literal_checks"],
            "raw_bellman_transition_checks": bellman_checks,
            "audit_bisimulation_transition_refs": bisimulation["summary"][
                "signature_build_transition_refs"
            ],
            "audit_quotient_concrete_lift_checks": lift_checks,
        },
        "epistemic_firewall": {
            "exact_cut_table_is_exponential_audit_oracle": True,
            "raw_bellman_is_exponential_audit_oracle": True,
            "future_bisimulation_partition_is_exponential_audit_oracle": True,
            "weak_scalar_labels_are_not_admitted_congruences": True,
            "audit_bisimulation_is_not_claimed_polynomially_discoverable": True,
        },
        "next_gate": "POLYNOMIAL_PROOF_CARRYING_PREFIX_BISIMULATION_DISCOVERY_OR_STRONGER_SYMBOLIC_WHOLE_ORDER_STATE_LANGUAGE",
        "universal_polynomial_prefix_quotient": "OPEN",
        "universal_candidate_completeness": "OPEN",
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
            "role": "PINNED_V5_1_CANDIDATE_PRODUCER_NOT_BELLMAN_ORACLE",
        },
    )
    if args.json_out:
        args.json_out.write_text(
            json.dumps(result, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    print("PF5_WHOLE_ORDER_PREFIX_STATE_QUOTIENT_V16 =", result["status"])
    print("RAW_STATES =", result["raw_subset_state_count"])
    print("V5_WIDTH / OPT =", result["v5_width"], result["raw_bellman_optimum"])
    print("FIRST_PURE_FUTURE_OBSTRUCTION =", result["first_pure_future_obstruction"])
    print("WEAK_LABEL_AUDIT =", result["weak_scalar_label_audit"])
    print("AUDIT_BISIMULATION =", result["audit_future_bisimulation"])
    print("AUDIT_QUOTIENT_WIDTH =", result["audit_quotient_lifted_width"])
    print("GLOBAL_COST_LEDGER =", result["global_cost_ledger"])
    print("UNIVERSAL_POLYNOMIAL_PREFIX_QUOTIENT = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
