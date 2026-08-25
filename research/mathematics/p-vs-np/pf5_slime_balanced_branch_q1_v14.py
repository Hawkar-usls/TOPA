#!/usr/bin/env python3
"""PF5 Slime balanced binary branch decomposition q=1 experiment v14.

The only scientific change from v13 is tree topology.  The pinned producer
returns the same 16 v3 incidence leaf orders wrapped in balanced full binary
trees.  The bounded STV recurrence is generalized to arbitrary rooted binary
topology; q remains exactly 1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pf5_slime_capped_pswidth_compiler_v12 as v12

FROZEN_Q = 1
FROZEN_ROWS = [
    (10, 42, 910010), (10, 42, 910011),
    (12, 50, 910012), (12, 50, 910013),
    (14, 59, 910014), (14, 59, 910015),
    (16, 67, 910016), (16, 67, 910017),
    (18, 76, 910018), (18, 76, 910019),
    (20, 84, 910020), (20, 84, 910021),
]


def digest_json(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def import_v4(path: Path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "janus_slime_balanced_branch_tree_v4_pin", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Slime v4")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def annotate_tree(tree):
    """Return deterministic path-addressed nodes plus post/preorder traversals."""
    nodes = {}
    postorder = []
    preorder = []

    def walk(raw, node_id, depth):
        preorder.append(node_id)
        if "leaf" in raw:
            node = {
                "node_id": node_id,
                "kind": "LEAF",
                "leaf": raw["leaf"],
                "left": None,
                "right": None,
                "depth": depth,
                "leaves": frozenset([raw["leaf"]]),
            }
            nodes[node_id] = node
            postorder.append(node_id)
            return node["leaves"]
        left_id = node_id + "0"
        right_id = node_id + "1"
        left_leaves = walk(raw["left"], left_id, depth + 1)
        right_leaves = walk(raw["right"], right_id, depth + 1)
        node = {
            "node_id": node_id,
            "kind": "INTERNAL",
            "leaf": None,
            "left": left_id,
            "right": right_id,
            "depth": depth,
            "leaves": left_leaves | right_leaves,
        }
        nodes[node_id] = node
        postorder.append(node_id)
        return node["leaves"]

    all_leaves = walk(tree, "R", 0)
    return nodes, postorder, preorder, all_leaves


def validate_tree(formula, tree):
    nodes, postorder, preorder, leaves = annotate_tree(tree)
    expected = set(v12.all_incidence_leaves(formula))
    if leaves != expected:
        raise ValueError("balanced tree leaves do not match source incidence leaves")
    leaf_nodes = [node for node in nodes.values() if node["kind"] == "LEAF"]
    if len(leaf_nodes) != len(expected):
        raise ValueError("duplicate incidence leaf in tree")
    return nodes, postorder, preorder


def state_payload(node, forward, complement):
    fs = v12.canonical_signatures(forward)
    cs = v12.canonical_signatures(complement)
    return {
        "node_id": node["node_id"],
        "kind": node["kind"],
        "depth": node["depth"],
        "leaf": node["leaf"],
        "left": node["left"],
        "right": node["right"],
        "leaves": sorted(node["leaves"]),
        "clause_ids": sorted(v12.clause_ids_of_leaves(node["leaves"])),
        "forward_signatures": [list(x) for x in fs],
        "forward_digest": digest_json(fs),
        "forward_count": len(fs),
        "complement_signatures": [list(x) for x in cs],
        "complement_digest": digest_json(cs),
        "complement_count": len(cs),
    }


def compile_balanced_tree(formula, tree, q=FROZEN_Q):
    formula = v12.canonical_formula(formula)
    nodes, postorder, preorder = validate_tree(formula, tree)
    r = len(v12.all_incidence_leaves(formula))
    cap = max(2, r ** q)
    ledger = v12.WorkLedger()
    forward = {}
    complement = {}

    try:
        for node_id in postorder:
            node = nodes[node_id]
            if node["kind"] == "LEAF":
                leaf = node["leaf"]
                if leaf.startswith("v:"):
                    variable = int(leaf.split(":", 1)[1])
                    forward[node_id] = v12.variable_leaf_state(
                        formula, variable, cap, ledger, node_id
                    )
                else:
                    out = set()
                    v12.insert_capped(
                        out, frozenset(), cap, ledger, "FORWARD", node_id
                    )
                    forward[node_id] = out
            else:
                inside = v12.clause_ids_of_leaves(node["leaves"])
                forward[node_id] = v12.forward_join(
                    forward[node["left"]],
                    forward[node["right"]],
                    inside,
                    cap,
                    ledger,
                    node_id,
                )

        root_comp = set()
        v12.insert_capped(root_comp, frozenset(), cap, ledger, "COMPLEMENT", "R")
        complement["R"] = root_comp

        for node_id in preorder:
            node = nodes[node_id]
            if node["kind"] != "INTERNAL":
                continue
            left = node["left"]
            right = node["right"]
            complement[left] = v12.complement_join(
                forward[right],
                complement[node_id],
                v12.clause_ids_of_leaves(nodes[left]["leaves"]),
                cap,
                ledger,
                left,
            )
            complement[right] = v12.complement_join(
                forward[left],
                complement[node_id],
                v12.clause_ids_of_leaves(nodes[right]["leaves"]),
                cap,
                ledger,
                right,
            )

    except v12.StateCapExceeded as exc:
        states = exc.states
        return {
            "terminal": "OPEN_BALANCED_STATE_CAP",
            "q": q,
            "cap": cap,
            "tree_digest": digest_json(tree),
            "failure": {
                "phase": exc.phase,
                "node_id": exc.node_id,
                "depth": nodes[exc.node_id]["depth"],
                "cap": exc.cap,
                "distinct_states_at_refusal": len(states),
                "first_cap_plus_one_signatures": [list(x) for x in states],
                "partial_state_digest": digest_json(states),
                "ledger": exc.ledger,
            },
            "claim": "BALANCED_TREE_Q1_CAP_SCOPED_OPEN_NOT_HARDNESS",
        }

    state_rows = []
    peak = 0
    total = 0
    for node_id in preorder:
        payload = state_payload(nodes[node_id], forward[node_id], complement[node_id])
        state_rows.append(payload)
        peak = max(peak, payload["forward_count"], payload["complement_count"])
        total += payload["forward_count"] + payload["complement_count"]
    ledger.certificate_state_entries = total
    ledger_payload = ledger.to_dict()
    core = {
        "formula_digest": digest_json(formula),
        "tree": tree,
        "tree_digest": digest_json(tree),
        "q": q,
        "cap": cap,
        "nodes": state_rows,
        "peak_ps_state": peak,
        "total_ps_states": total,
        "ledger": ledger_payload,
    }
    cert_digest = digest_json(core)
    certificate = dict(core)
    certificate["certificate_digest"] = cert_digest
    certificate_bytes = len(
        json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()
    )
    return {
        "terminal": "CLOSED_BALANCED_PSWIDTH_CAP",
        "q": q,
        "cap": cap,
        "tree_digest": digest_json(tree),
        "peak_ps_state": peak,
        "total_ps_states": total,
        "pair_attempts": ledger.pair_attempts,
        "total_work_units": ledger_payload["total_work_units"],
        "certificate_bytes": certificate_bytes,
        "certificate": certificate,
    }


def _states(rows):
    return {frozenset(map(int, row)) for row in rows}


def replay_balanced_certificate(formula, result):
    if result.get("terminal") != "CLOSED_BALANCED_PSWIDTH_CAP":
        return False
    cert = result["certificate"]
    formula = v12.canonical_formula(formula)
    tree = cert["tree"]
    nodes, postorder, preorder = validate_tree(formula, tree)
    if cert["formula_digest"] != digest_json(formula):
        return False
    if cert["tree_digest"] != digest_json(tree):
        return False
    core = dict(cert)
    observed = core.pop("certificate_digest")
    if digest_json(core) != observed:
        return False
    stored = {row["node_id"]: row for row in cert["nodes"]}
    forward = {}
    complement = {}

    for node_id in postorder:
        node = nodes[node_id]
        if node["kind"] == "LEAF":
            leaf = node["leaf"]
            if leaf.startswith("v:"):
                x = int(leaf.split(":", 1)[1])
                expected = {
                    frozenset(ci for ci, clause in enumerate(formula) if x in clause),
                    frozenset(ci for ci, clause in enumerate(formula) if -x in clause),
                }
            else:
                expected = {frozenset()}
        else:
            inside = v12.clause_ids_of_leaves(node["leaves"])
            expected = {
                frozenset((a | b) - inside)
                for a in forward[node["left"]]
                for b in forward[node["right"]]
            }
        got = _states(stored[node_id]["forward_signatures"])
        if got != expected:
            return False
        forward[node_id] = got

    complement["R"] = {frozenset()}
    if _states(stored["R"]["complement_signatures"]) != complement["R"]:
        return False
    for node_id in preorder:
        node = nodes[node_id]
        if node["kind"] != "INTERNAL":
            continue
        for child, sibling in ((node["left"], node["right"]), (node["right"], node["left"])):
            child_clauses = v12.clause_ids_of_leaves(nodes[child]["leaves"])
            expected = {
                frozenset((a | b) & child_clauses)
                for a in forward[sibling]
                for b in complement[node_id]
            }
            got = _states(stored[child]["complement_signatures"])
            if got != expected:
                return False
            complement[child] = got

    peak = max(max(len(forward[n]), len(complement[n])) for n in nodes)
    total = sum(len(forward[n]) + len(complement[n]) for n in nodes)
    return peak == cert["peak_ps_state"] and total == cert["total_ps_states"]


def selection_key(result):
    return (
        result["peak_ps_state"],
        result["total_ps_states"],
        result["pair_attempts"],
        result["certificate_bytes"],
        result["tree_digest"],
    )


def compile_portfolio(formula, manifest):
    attempts = []
    closed_rows = []
    compiler_work = 0
    for candidate in manifest.candidates:
        result = compile_balanced_tree(formula, candidate.tree, q=FROZEN_Q)
        if result["terminal"] == "CLOSED_BALANCED_PSWIDTH_CAP":
            assert replay_balanced_certificate(formula, result)
            compiler_work += result["total_work_units"]
            row = {
                "candidate": candidate.name,
                "tree_digest": candidate.tree_digest,
                "leaf_order_digest": candidate.leaf_order_digest,
                "terminal": result["terminal"],
                "peak_ps_state": result["peak_ps_state"],
                "total_ps_states": result["total_ps_states"],
                "pair_attempts": result["pair_attempts"],
                "certificate_bytes": result["certificate_bytes"],
                "certificate_digest": result["certificate"]["certificate_digest"],
                "certificate_replayed_before_discard": True,
                "_full": result,
            }
            closed_rows.append(row)
        else:
            assert result["failure"]["distinct_states_at_refusal"] == result["cap"] + 1
            compiler_work += result["failure"]["ledger"]["total_work_units"]
            row = {
                "candidate": candidate.name,
                "tree_digest": candidate.tree_digest,
                "leaf_order_digest": candidate.leaf_order_digest,
                "terminal": result["terminal"],
                "failure": result["failure"],
                "claim": result["claim"],
            }
        attempts.append(row)

    cap = max(2, len(v12.all_incidence_leaves(formula)))
    if not closed_rows:
        for row in attempts:
            row.pop("_full", None)
        return {
            "terminal": "OPEN_BALANCED_PORTFOLIO_Q1_EXHAUSTED",
            "cap": cap,
            "closed_candidates": 0,
            "open_candidates": 16,
            "compiler_work_units": compiler_work,
            "attempts": attempts,
            "claim": "SIMPLE_BALANCED_TRANSFORM_Q1_PORTFOLIO_EXHAUSTED_NOT_HARDNESS",
        }

    selected = min(closed_rows, key=lambda row: selection_key(row["_full"]))
    selected_full = selected["_full"]
    assert replay_balanced_certificate(formula, selected_full)
    selected_name = selected["candidate"]
    for row in attempts:
        row.pop("_full", None)
    return {
        "terminal": "CLOSED_BALANCED_PORTFOLIO_Q1",
        "cap": cap,
        "closed_candidates": len(closed_rows),
        "open_candidates": 16 - len(closed_rows),
        "compiler_work_units": compiler_work,
        "selected_candidate": selected_name,
        "selected_key": list(selection_key(selected_full)),
        "selected_certificate": selected_full["certificate"],
        "selected_certificate_replay": True,
        "attempts": attempts,
    }


def run(producer_class, producer_identity):
    producer = producer_class()
    frozen = []
    for n, m, seed in FROZEN_ROWS:
        formula = v12.random_connected_3cnf(seed, n, m)
        manifest = producer.generate_manifest(formula)
        frozen.append((n, m, seed, formula, manifest))

    batch_sha = digest_json([
        (n, m, seed, digest_json(formula), manifest.manifest_sha256)
        for n, m, seed, formula, manifest in frozen
    ])

    results = []
    total_closed = 0
    total_open = 0
    recovered_sources = 0
    total_generation = 0
    total_compiler = 0
    for n, m, seed, formula, manifest in frozen:
        p = compile_portfolio(formula, manifest)
        total_closed += p["closed_candidates"]
        total_open += p["open_candidates"]
        recovered_sources += int(p["terminal"] == "CLOSED_BALANCED_PORTFOLIO_Q1")
        total_generation += manifest.total_generation_ops
        total_compiler += p["compiler_work_units"]
        results.append({
            "n": n,
            "m": m,
            "density": m / n,
            "seed": seed,
            "formula_sha256": digest_json(formula),
            "manifest_sha256": manifest.manifest_sha256,
            "source_v3_manifest_sha256": manifest.source_v3_manifest_sha256,
            "incidence_leaves": len(v12.all_incidence_leaves(formula)),
            "portfolio": p,
        })

    if recovered_sources:
        interpretation = "BALANCED_TOPOLOGY_RECOVERS_Q1_ON_FINITE_DENSE_CONTROL"
    else:
        interpretation = "SIMPLE_BALANCED_TRANSFORM_Q1_REFUTED_ON_FRESH_DENSE_LADDER"

    out = {
        "artifact_id": "PF5-SLIME-BALANCED-BRANCH-Q1-V14",
        "status": "FINITE_TOPOLOGY_ISOLATION_PROBE_COMPLETE",
        "producer": producer_identity,
        "q": FROZEN_Q,
        "frozen_rows": [list(x) for x in FROZEN_ROWS],
        "all_formulas_and_tree_manifests_frozen_before_compilation": True,
        "frozen_batch_sha256": batch_sha,
        "runtime_assignment_enumeration": False,
        "runtime_exact_width_oracle": False,
        "runtime_sat_oracle": False,
        "results": results,
        "recovered_sources": recovered_sources,
        "exhausted_sources": len(results) - recovered_sources,
        "closed_candidates": total_closed,
        "open_candidates": total_open,
        "global_ledger": {
            "topology_plus_slime_generation_ops": total_generation,
            "compiler_work_units": total_compiler,
            "candidate_attempts": len(results) * 16,
        },
        "terminal_interpretation": interpretation,
        "arbitrary_binary_tree_q1_completeness": "OPEN",
        "some_fixed_q_completeness": "OPEN",
        "p_vs_np": "OPEN",
    }
    out["result_sha256"] = digest_json(out)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-path", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    raw = args.producer_path.read_bytes()
    module = import_v4(args.producer_path)
    result = run(
        module.SlimeBalancedBranchTreeV4,
        {
            "commit": "9983b0173da9d5de1bfb5e9922fa78762160e94f",
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "PINNED_TOPOLOGY_ONLY_CANDIDATE_PRODUCER",
        },
    )
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_SLIME_BALANCED_BRANCH_Q1_V14 =", result["status"])
    print("FROZEN_BATCH_SHA256 =", result["frozen_batch_sha256"])
    print("RECOVERED_SOURCES =", result["recovered_sources"])
    print("EXHAUSTED_SOURCES =", result["exhausted_sources"])
    print("CLOSED_CANDIDATES =", result["closed_candidates"])
    print("OPEN_CANDIDATES =", result["open_candidates"])
    for row in result["results"]:
        p = row["portfolio"]
        print(
            "N", row["n"], "M", row["m"], "SEED", row["seed"],
            p["terminal"], "CAP", p["cap"],
            "CLOSED", p["closed_candidates"], "OPEN", p["open_candidates"],
            "SELECTED", p.get("selected_candidate"),
            "SELECTED_PEAK", p.get("selected_key", [None])[0],
        )
    print("TERMINAL_INTERPRETATION =", result["terminal_interpretation"])
    print("GLOBAL_LEDGER =", result["global_ledger"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
