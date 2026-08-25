#!/usr/bin/env python3
"""PF5 Slime capped PS-width compiler v12.

Runtime lane:
  raw CNF -> pinned Slime v3 incidence orders -> bounded exact STV PS-state
  recurrence -> CLOSED_PSWIDTH_CAP / OPEN_STATE_CAP -> deterministic selector.

No assignment enumeration, exact-width oracle, v9 audit scorer, or general SAT
fallback is used by this runtime compiler.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence

FROZEN_Q = 1
FRESH_N7_SEEDS = list(range(908000, 908016))
FRESH_N9_SEEDS = list(range(908100, 908108))


def canonical_formula(clauses: Iterable[Sequence[int]]):
    out = []
    for clause in clauses:
        lits = tuple(sorted(set(map(int, clause)), key=lambda x: (abs(x), x < 0)))
        if any(x == 0 for x in lits):
            raise ValueError("literal 0")
        if any(-x in lits for x in lits):
            raise ValueError("tautological clause")
        out.append(lits)
    return tuple(out)


def variables_of(formula):
    return sorted({abs(lit) for clause in formula for lit in clause})


def all_incidence_leaves(formula):
    return [f"v:{v}" for v in variables_of(formula)] + [
        f"c:{i}" for i in range(len(formula))
    ]


def random_connected_3cnf(seed: int, variable_count: int, clause_count: int):
    rng = random.Random(seed)
    clauses = []
    for start in range(1, variable_count - 1):
        variables = [start, start + 1, start + 2]
        clauses.append(tuple(v if rng.getrandbits(1) else -v for v in variables))
    seen = {
        tuple(sorted(clause, key=lambda x: (abs(x), x < 0)))
        for clause in clauses
    }
    while len(clauses) < clause_count:
        variables = rng.sample(range(1, variable_count + 1), 3)
        clause = tuple(v if rng.getrandbits(1) else -v for v in variables)
        key = tuple(sorted(clause, key=lambda x: (abs(x), x < 0)))
        if key in seen:
            continue
        seen.add(key)
        clauses.append(clause)
    return canonical_formula(clauses)


def duplicate_family(n=6, m=6):
    return canonical_formula([tuple(range(1, n + 1)) for _ in range(m)])


def unit_family(n):
    return canonical_formula([(v,) for v in range(1, n + 1)])


def canonical_signatures(states):
    return tuple(sorted(tuple(sorted(state)) for state in states))


def digest_json(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def validate_order(formula, order):
    expected = sorted(all_incidence_leaves(formula))
    if len(order) != len(expected) or sorted(order) != expected:
        raise ValueError("candidate order is not an exact incidence-leaf permutation")


def clause_ids_of_leaves(leaves):
    return frozenset(
        int(leaf.split(":", 1)[1])
        for leaf in leaves
        if leaf.startswith("c:")
    )


@dataclass
class WorkLedger:
    base_literal_checks: int = 0
    pair_attempts: int = 0
    signature_clause_ops: int = 0
    state_insert_attempts: int = 0
    recurrence_nodes: int = 0
    certificate_state_entries: int = 0

    def to_dict(self):
        return {
            "base_literal_checks": self.base_literal_checks,
            "pair_attempts": self.pair_attempts,
            "signature_clause_ops": self.signature_clause_ops,
            "state_insert_attempts": self.state_insert_attempts,
            "recurrence_nodes": self.recurrence_nodes,
            "certificate_state_entries": self.certificate_state_entries,
            "total_work_units": (
                self.base_literal_checks
                + self.pair_attempts
                + self.signature_clause_ops
                + self.state_insert_attempts
                + self.recurrence_nodes
                + self.certificate_state_entries
            ),
        }


class StateCapExceeded(Exception):
    def __init__(self, phase, node_id, cap, states, ledger):
        super().__init__(f"{phase}:{node_id}:state cap {cap} exceeded")
        self.phase = phase
        self.node_id = node_id
        self.cap = cap
        self.states = canonical_signatures(states)
        self.ledger = ledger.to_dict()


def insert_capped(out: set[frozenset[int]], state, cap, ledger, phase, node_id):
    ledger.state_insert_attempts += 1
    out.add(frozenset(state))
    if len(out) > cap:
        raise StateCapExceeded(phase, node_id, cap, out, ledger)


def variable_leaf_state(formula, variable: int, cap: int, ledger: WorkLedger, node_id: str):
    positive = set()
    negative = set()
    for clause_id, clause in enumerate(formula):
        for lit in clause:
            ledger.base_literal_checks += 1
            if abs(lit) == variable:
                if lit > 0:
                    positive.add(clause_id)
                else:
                    negative.add(clause_id)
    out: set[frozenset[int]] = set()
    insert_capped(out, positive, cap, ledger, "FORWARD", node_id)
    insert_capped(out, negative, cap, ledger, "FORWARD", node_id)
    return out


def forward_join(left, right, inside_clauses, cap, ledger, node_id):
    out: set[frozenset[int]] = set()
    ledger.recurrence_nodes += 1
    for a in left:
        for b in right:
            ledger.pair_attempts += 1
            ledger.signature_clause_ops += len(a) + len(b) + len(inside_clauses)
            merged = (a | b) - inside_clauses
            insert_capped(out, merged, cap, ledger, "FORWARD", node_id)
    return out


def complement_join(sibling_forward, parent_complement, child_clauses, cap, ledger, node_id):
    out: set[frozenset[int]] = set()
    ledger.recurrence_nodes += 1
    for a in sibling_forward:
        for b in parent_complement:
            ledger.pair_attempts += 1
            ledger.signature_clause_ops += len(a) + len(b) + len(child_clauses)
            merged = (a | b) & child_clauses
            insert_capped(out, merged, cap, ledger, "COMPLEMENT", node_id)
    return out


def make_tree(order):
    """Return node metadata for the left-associated/right-linear decomposition."""
    nodes: Dict[str, dict] = {}
    for i, leaf in enumerate(order):
        nodes[f"L{i}"] = {
            "node_id": f"L{i}",
            "kind": "LEAF",
            "leaf": leaf,
            "leaves": frozenset([leaf]),
            "left": None,
            "right": None,
        }
    if len(order) == 1:
        return nodes, "L0"
    for i in range(1, len(order)):
        left = "L0" if i == 1 else f"P{i-1}"
        right = f"L{i}"
        node_id = f"P{i}"
        nodes[node_id] = {
            "node_id": node_id,
            "kind": "INTERNAL",
            "leaf": None,
            "leaves": nodes[left]["leaves"] | nodes[right]["leaves"],
            "left": left,
            "right": right,
        }
    return nodes, f"P{len(order)-1}"


def state_payload(node, forward, complement):
    fs = canonical_signatures(forward)
    cs = canonical_signatures(complement)
    return {
        "node_id": node["node_id"],
        "kind": node["kind"],
        "leaves": sorted(node["leaves"]),
        "clause_ids": sorted(clause_ids_of_leaves(node["leaves"])),
        "forward_signatures": [list(x) for x in fs],
        "forward_digest": digest_json(fs),
        "forward_count": len(fs),
        "complement_signatures": [list(x) for x in cs],
        "complement_digest": digest_json(cs),
        "complement_count": len(cs),
    }


def compile_order(formula, order, q=FROZEN_Q):
    formula = canonical_formula(formula)
    order = list(order)
    validate_order(formula, order)
    r = len(order)
    cap = max(2, r ** q)
    ledger = WorkLedger()
    nodes, root = make_tree(order)
    forward: Dict[str, set[frozenset[int]]] = {}
    complement: Dict[str, set[frozenset[int]]] = {}

    try:
        # Forward leaf base states.
        for i, leaf in enumerate(order):
            node_id = f"L{i}"
            if leaf.startswith("v:"):
                variable = int(leaf.split(":", 1)[1])
                forward[node_id] = variable_leaf_state(
                    formula, variable, cap, ledger, node_id
                )
            elif leaf.startswith("c:"):
                out: set[frozenset[int]] = set()
                insert_capped(out, frozenset(), cap, ledger, "FORWARD", node_id)
                forward[node_id] = out
            else:
                raise ValueError(leaf)

        # Bottom-up forward PS sets.
        for i in range(1, r):
            node_id = f"P{i}"
            left = nodes[node_id]["left"]
            right = nodes[node_id]["right"]
            inside = clause_ids_of_leaves(nodes[node_id]["leaves"])
            forward[node_id] = forward_join(
                forward[left], forward[right], inside, cap, ledger, node_id
            )

        # Root complement base.
        root_comp: set[frozenset[int]] = set()
        insert_capped(root_comp, frozenset(), cap, ledger, "COMPLEMENT", root)
        complement[root] = root_comp

        # Top-down complement PS sets.
        if r > 1:
            for i in range(r - 1, 0, -1):
                parent = f"P{i}"
                left = nodes[parent]["left"]
                right = nodes[parent]["right"]
                left_clauses = clause_ids_of_leaves(nodes[left]["leaves"])
                right_clauses = clause_ids_of_leaves(nodes[right]["leaves"])
                complement[left] = complement_join(
                    forward[right], complement[parent], left_clauses,
                    cap, ledger, left
                )
                complement[right] = complement_join(
                    forward[left], complement[parent], right_clauses,
                    cap, ledger, right
                )
        else:
            # root is also leaf
            complement[root] = root_comp

    except StateCapExceeded as exc:
        partial = {
            "phase": exc.phase,
            "node_id": exc.node_id,
            "cap": exc.cap,
            "distinct_states_at_refusal": len(exc.states),
            "first_cap_plus_one_signatures": [list(x) for x in exc.states],
            "partial_state_digest": digest_json(exc.states),
            "ledger": exc.ledger,
        }
        return {
            "terminal": "OPEN_STATE_CAP",
            "q": q,
            "cap": cap,
            "order_digest": digest_json(order),
            "failure": partial,
            "claim": "CAP_SCOPED_OPEN_NOT_HARDNESS",
        }

    # Full certificate.
    node_order = [f"L{i}" for i in range(r)] + [f"P{i}" for i in range(1, r)]
    states = []
    peak = 0
    total = 0
    for node_id in node_order:
        payload = state_payload(nodes[node_id], forward[node_id], complement[node_id])
        states.append(payload)
        peak = max(peak, payload["forward_count"], payload["complement_count"])
        total += payload["forward_count"] + payload["complement_count"]
    ledger.certificate_state_entries = total
    ledger_payload = ledger.to_dict()
    certificate_core = {
        "formula_digest": digest_json(formula),
        "order": order,
        "order_digest": digest_json(order),
        "q": q,
        "cap": cap,
        "root": root,
        "nodes": states,
        "peak_ps_state": peak,
        "total_ps_states": total,
        "ledger": ledger_payload,
        "published_bridge": {
            "ps_preprocessing": "STV Theorem 1: O(k^2 log(k) m(m+n))",
            "solver": "STV Theorem 3: O(k^3 s(m+n)) for #SAT/weighted MaxSAT",
        },
    }
    certificate_digest = digest_json(certificate_core)
    certificate = dict(certificate_core)
    certificate["certificate_digest"] = certificate_digest
    certificate_bytes = len(
        json.dumps(certificate, sort_keys=True, separators=(",", ":")).encode()
    )
    return {
        "terminal": "CLOSED_PSWIDTH_CAP",
        "q": q,
        "cap": cap,
        "order_digest": digest_json(order),
        "peak_ps_state": peak,
        "total_ps_states": total,
        "pair_attempts": ledger.pair_attempts,
        "total_work_units": ledger_payload["total_work_units"],
        "certificate_bytes": certificate_bytes,
        "certificate": certificate,
    }


def _states_from_payload(rows):
    return {frozenset(map(int, row)) for row in rows}


def replay_closed_certificate(formula, result):
    """Independent recurrence replay from source + stored state certificate."""
    if result.get("terminal") != "CLOSED_PSWIDTH_CAP":
        return False
    cert = result["certificate"]
    formula = canonical_formula(formula)
    order = cert["order"]
    validate_order(formula, order)
    if cert["formula_digest"] != digest_json(formula):
        return False
    if cert["order_digest"] != digest_json(order):
        return False
    core = dict(cert)
    observed_digest = core.pop("certificate_digest")
    if digest_json(core) != observed_digest:
        return False

    nodes, root = make_tree(order)
    stored = {row["node_id"]: row for row in cert["nodes"]}
    forward = {}
    complement = {}

    # Replay forward leaves independently.
    for i, leaf in enumerate(order):
        node_id = f"L{i}"
        if leaf.startswith("v:"):
            x = int(leaf.split(":", 1)[1])
            pos = frozenset(
                ci for ci, clause in enumerate(formula) if x in clause
            )
            neg = frozenset(
                ci for ci, clause in enumerate(formula) if -x in clause
            )
            expected = {pos, neg}
        else:
            expected = {frozenset()}
        got = _states_from_payload(stored[node_id]["forward_signatures"])
        if got != expected:
            return False
        forward[node_id] = got

    # Replay forward internal recurrence.
    for i in range(1, len(order)):
        node_id = f"P{i}"
        left = nodes[node_id]["left"]
        right = nodes[node_id]["right"]
        inside = clause_ids_of_leaves(nodes[node_id]["leaves"])
        expected = {
            frozenset((a | b) - inside)
            for a in forward[left] for b in forward[right]
        }
        got = _states_from_payload(stored[node_id]["forward_signatures"])
        if got != expected:
            return False
        forward[node_id] = got

    # Replay complement recurrence.
    complement[root] = {frozenset()}
    if _states_from_payload(stored[root]["complement_signatures"]) != complement[root]:
        return False
    if len(order) > 1:
        for i in range(len(order) - 1, 0, -1):
            parent = f"P{i}"
            left = nodes[parent]["left"]
            right = nodes[parent]["right"]
            for child, sibling in ((left, right), (right, left)):
                child_clauses = clause_ids_of_leaves(nodes[child]["leaves"])
                expected = {
                    frozenset((a | b) & child_clauses)
                    for a in forward[sibling] for b in complement[parent]
                }
                got = _states_from_payload(stored[child]["complement_signatures"])
                if got != expected:
                    return False
                complement[child] = got

    peak = max(
        max(len(forward[node_id]), len(complement[node_id]))
        for node_id in stored
    )
    total = sum(
        len(forward[node_id]) + len(complement[node_id])
        for node_id in stored
    )
    return peak == cert["peak_ps_state"] and total == cert["total_ps_states"]


def import_slime_v3(path: Path):
    spec = importlib.util.spec_from_file_location(
        "janus_slime_candidate_swarm_v3_runtime_pin", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Slime v3")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def merge_ledgers(total, result):
    if result["terminal"] == "CLOSED_PSWIDTH_CAP":
        ledger = result["certificate"]["ledger"]
    else:
        ledger = result["failure"]["ledger"]
    for key, value in ledger.items():
        total[key] = total.get(key, 0) + value


def run_portfolio(formula, manifest, q=FROZEN_Q):
    formula = canonical_formula(formula)
    attempts = []
    global_ledger: dict[str, int] = {}
    successful = []
    for candidate in manifest.candidates:
        result = compile_order(formula, candidate.linear_leaf_order, q=q)
        merge_ledgers(global_ledger, result)
        row = {
            "candidate": candidate.name,
            "generation_ops": candidate.charged_ops,
            "result": result,
        }
        attempts.append(row)
        if result["terminal"] == "CLOSED_PSWIDTH_CAP":
            successful.append(row)

    global_ledger["slime_manifest_generation_ops"] = manifest.total_generation_ops
    global_ledger["candidate_attempts"] = len(attempts)
    global_ledger["closed_candidates"] = len(successful)
    global_ledger["open_candidates"] = len(attempts) - len(successful)

    if not successful:
        return {
            "terminal": "OPEN_PORTFOLIO_CAP_EXHAUSTED",
            "q": q,
            "cap": max(2, len(all_incidence_leaves(formula)) ** q),
            "attempts": attempts,
            "global_ledger": global_ledger,
            "claim": "PORTFOLIO_AND_CAP_SCOPED_OPEN_NOT_HARDNESS",
        }

    def selection_key(row):
        r = row["result"]
        return (
            r["peak_ps_state"],
            r["total_ps_states"],
            r["pair_attempts"],
            r["certificate_bytes"],
            r["order_digest"],
        )

    selected = min(successful, key=selection_key)
    assert replay_closed_certificate(formula, selected["result"])
    return {
        "terminal": "CLOSED_PORTFOLIO_PSWIDTH_CAP",
        "q": q,
        "cap": selected["result"]["cap"],
        "selected_candidate": selected["candidate"],
        "selected_key": list(selection_key(selected)),
        "selected_certificate_digest": selected["result"]["certificate"]["certificate_digest"],
        "selected_certificate_replay": True,
        "attempts": attempts,
        "global_ledger": global_ledger,
    }


def manual_lexical_canary(formula, q=FROZEN_Q):
    order = sorted(all_incidence_leaves(formula))
    return compile_order(formula, order, q=q)


def build_controls():
    controls = []
    for seed in FRESH_N7_SEEDS:
        controls.append((f"FRESH_N7_{seed}", random_connected_3cnf(seed, 7, 10)))
    for seed in FRESH_N9_SEEDS:
        controls.append((f"FRESH_N9_{seed}", random_connected_3cnf(seed, 9, 14)))
    controls.append(("DUPLICATE_K6_6", duplicate_family(6, 6)))
    return controls


def run(slime_v3_class, producer_identity):
    router = slime_v3_class()

    # Freeze all manifests before any bounded compiler attempt.
    frozen = []
    for fixture, formula in build_controls():
        manifest = router.generate_manifest(formula)
        frozen.append((fixture, formula, manifest))
    batch_hash = digest_json([
        (fixture, manifest.source_sha256, manifest.manifest_sha256)
        for fixture, _, manifest in frozen
    ])

    results = []
    closed_sources = 0
    total_closed_candidates = 0
    total_open_candidates = 0
    for fixture, formula, manifest in frozen:
        portfolio = run_portfolio(formula, manifest, q=FROZEN_Q)
        if portfolio["terminal"] == "CLOSED_PORTFOLIO_PSWIDTH_CAP":
            closed_sources += 1
        total_closed_candidates += portfolio["global_ledger"]["closed_candidates"]
        total_open_candidates += portfolio["global_ledger"]["open_candidates"]
        results.append({
            "fixture": fixture,
            "variables": len(variables_of(formula)),
            "clauses": len(formula),
            "incidence_leaves": len(all_incidence_leaves(formula)),
            "manifest_sha256": manifest.manifest_sha256,
            "portfolio": portfolio,
        })

    canaries = {}
    for n in (8, 10):
        formula = unit_family(n)
        result = manual_lexical_canary(formula)
        canaries[f"UNIT_N{n}_LEXICAL"] = result

    output = {
        "artifact_id": "PF5-SLIME-CAPPED-PSWIDTH-COMPILER-V12",
        "status": "FINITE_CAPPED_RUNTIME_PROBE_COMPLETE",
        "producer": producer_identity,
        "q_frozen_before_provider_run": FROZEN_Q,
        "state_cap_formula": "K=max(2,r^q), r=variables+clauses",
        "fresh_n7_seeds": FRESH_N7_SEEDS,
        "fresh_n9_seeds": FRESH_N9_SEEDS,
        "all_slime_manifests_frozen_before_compilation": True,
        "manifest_batch_sha256": batch_hash,
        "runtime_exact_width_oracle_used": False,
        "runtime_assignment_enumeration_used": False,
        "runtime_general_sat_fallback_used": False,
        "results": results,
        "closed_sources": closed_sources,
        "source_count": len(results),
        "total_closed_candidates": total_closed_candidates,
        "total_open_candidates": total_open_candidates,
        "manual_fail_fast_canaries": canaries,
        "universal_fixed_q_candidate_completeness": "OPEN",
        "remaining_gate": "EXISTS_FIXED_q_AND_POLY_SLIME_PORTFOLIO_SUCH_THAT_FOR_EVERY_CNF_SOME_CANDIDATE_HAS_PSWIDTH_AT_MOST_N^q",
        "p_vs_np": "OPEN",
    }
    output["result_sha256"] = digest_json(output)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--producer-path", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    raw = args.producer_path.read_bytes()
    module = import_slime_v3(args.producer_path)
    result = run(
        module.SlimeSemanticCandidateSwarmV3Amortized,
        {
            "commit": "421794b5c7e3b96f52550cf710fe2d8d2f3b59db",
            "path": str(args.producer_path),
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "role": "PINNED_POLYNOMIAL_CANDIDATE_PRODUCER_NOT_WIDTH_ORACLE",
        },
    )

    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print("PF5_SLIME_CAPPED_PSWIDTH_COMPILER_V12 =", result["status"])
    print("Q =", result["q_frozen_before_provider_run"])
    print("MANIFEST_BATCH_SHA256 =", result["manifest_batch_sha256"])
    print("CLOSED_SOURCES =", result["closed_sources"], "/", result["source_count"])
    print("CLOSED_CANDIDATES =", result["total_closed_candidates"])
    print("OPEN_CANDIDATES =", result["total_open_candidates"])
    for row in result["results"]:
        p = row["portfolio"]
        print(
            row["fixture"],
            p["terminal"],
            "cap=", p["cap"],
            "selected=", p.get("selected_candidate"),
            "closed=", p["global_ledger"]["closed_candidates"],
            "open=", p["global_ledger"]["open_candidates"],
        )
    for name, canary in result["manual_fail_fast_canaries"].items():
        print(
            name,
            canary["terminal"],
            "cap=", canary["cap"],
            "refusal_states=", canary.get("failure", {}).get("distinct_states_at_refusal"),
        )
    print("UNIVERSAL_FIXED_q_CANDIDATE_COMPLETENESS = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
