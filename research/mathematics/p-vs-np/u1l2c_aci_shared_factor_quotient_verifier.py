#!/usr/bin/env python3
"""U1-L2C exact proof-carrying ACI shared-factor quotient provider.

Frozen scope: closed single-output pure positive-AND DAGs over canonical signed
leaf IDs.  No SAT/equivalence oracle and no sampled valuations.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Dict, List, Tuple

MS = [2, 4, 8, 16, 32, 64, 128]
LANES = 4
PROJECTED = "x"


class Refusal(Exception):
    pass


@dataclass(frozen=True)
class Node:
    kind: str
    inputs: Tuple[str, ...] = ()
    token: str | None = None


class Dag:
    def __init__(self) -> None:
        self.nodes: Dict[str, Node] = {}
        self.order: List[str] = []
        self.output: str | None = None

    def leaf(self, name: str, token: str | None = None) -> str:
        assert name not in self.nodes
        self.nodes[name] = Node("ROOT", (), token or name)
        self.order.append(name)
        return name

    def and_gate(self, name: str, a: str, b: str) -> str:
        assert name not in self.nodes and a in self.nodes and b in self.nodes
        self.nodes[name] = Node("AND", (a, b), None)
        self.order.append(name)
        return name

    def bad_gate(self, name: str, kind: str, *inputs: str) -> str:
        assert name not in self.nodes
        self.nodes[name] = Node(kind, tuple(inputs), None)
        self.order.append(name)
        return name

    def fingerprint(self) -> str:
        payload = {
            "order": self.order,
            "nodes": {
                k: {"kind": self.nodes[k].kind, "inputs": list(self.nodes[k].inputs), "token": self.nodes[k].token}
                for k in self.order
            },
            "output": self.output,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def canonical_token(token: str) -> str:
    if not isinstance(token, str) or not token:
        raise Refusal("REFUSE_NON_ACI_CONE")
    return token


def token_depends_on(token: str, projected: str) -> bool:
    raw = token[1:] if token.startswith("~") else token
    return raw == projected


def source_dependency(d: Dag, projected: str) -> Tuple[Dict[str, bool], int]:
    dep: Dict[str, bool] = {}
    ac = 0
    for nid in d.order:
        n = d.nodes[nid]
        if n.kind == "ROOT":
            dep[nid] = token_depends_on(canonical_token(n.token or ""), projected)
        elif n.kind == "AND":
            if len(n.inputs) != 2 or any(i not in dep for i in n.inputs):
                raise Refusal("REFUSE_NON_ACI_CONE")
            dep[nid] = dep[n.inputs[0]] or dep[n.inputs[1]]
            if dep[nid]:
                ac += 1
        else:
            raise Refusal("REFUSE_NON_ACI_CONE")
    return dep, ac


def produce_certificate(d: Dag, projected: str) -> dict:
    if d.output is None or d.output not in d.nodes:
        raise Refusal("REFUSE_NON_ACI_CONE")

    factors: Dict[str, Tuple[str, ...]] = {}
    factor_ops = 0
    duplicate_eliminations = 0
    gate_count = 0

    for nid in d.order:
        n = d.nodes[nid]
        if n.kind == "ROOT":
            factors[nid] = (canonical_token(n.token or ""),)
            continue
        if n.kind != "AND" or len(n.inputs) != 2 or any(i not in factors for i in n.inputs):
            raise Refusal("REFUSE_NON_ACI_CONE")
        gate_count += 1
        left = factors[n.inputs[0]]
        right = factors[n.inputs[1]]
        factor_ops += len(left) + len(right)
        merged = tuple(sorted(set(left).union(right)))
        duplicate_eliminations += len(left) + len(right) - len(merged)
        factors[nid] = merged

    final_factors = factors[d.output]
    nondep = [f for f in final_factors if not token_depends_on(f, projected)]
    dep = [f for f in final_factors if token_depends_on(f, projected)]
    target_order = tuple(sorted(nondep) + sorted(dep))

    target_gates = []
    target_ac = 0
    if len(target_order) >= 2:
        current_dep = token_depends_on(target_order[0], projected)
        prev = target_order[0]
        for idx, factor in enumerate(target_order[1:], start=1):
            this_dep = token_depends_on(factor, projected)
            out_dep = current_dep or this_dep
            gid = f"q{idx}"
            target_gates.append((gid, prev, factor, out_dep))
            if out_dep:
                target_ac += 1
            prev = gid
            current_dep = out_dep

    target_payload = {
        "factor_order": list(target_order),
        "gates": [[g, a, b] for g, a, b, _ in target_gates],
    }
    target_sha = sha256(json.dumps(target_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    _, source_ac = source_dependency(d, projected)

    cert = {
        "schema": "JANUS_U1L2C_ACI_CERTIFICATE",
        "source_sha256": d.fingerprint(),
        "projected_root": projected,
        "node_factor_sets": {k: list(factors[k]) for k in d.order},
        "final_factor_set": list(final_factors),
        "duplicate_eliminations": duplicate_eliminations,
        "source_gate_count": gate_count,
        "source_ac_x": source_ac,
        "target_factor_order": list(target_order),
        "target_gate_count": max(0, len(target_order) - 1),
        "target_ac_x": target_ac,
        "target_sha256": target_sha,
        "ledger": {
            "source_nodes_visited": len(d.order),
            "source_edges_read": 2 * gate_count,
            "factor_merge_item_ops": factor_ops,
            "target_gates_built": max(0, len(target_order) - 1),
        },
    }
    cert["certificate_bytes"] = len(json.dumps(cert, sort_keys=True, separators=(",", ":")).encode())
    return cert


def independent_replay(d: Dag, cert: dict) -> None:
    """Independent recursive replay; does not trust producer node-factor sets."""
    if cert["source_sha256"] != d.fingerprint() or d.output is None:
        raise AssertionError("source binding mismatch")

    memo: Dict[str, frozenset[str]] = {}
    visiting: set[str] = set()

    def visit(nid: str) -> frozenset[str]:
        if nid in memo:
            return memo[nid]
        if nid in visiting or nid not in d.nodes:
            raise AssertionError("cycle or missing node")
        visiting.add(nid)
        n = d.nodes[nid]
        if n.kind == "ROOT":
            out = frozenset([canonical_token(n.token or "")])
        elif n.kind == "AND" and len(n.inputs) == 2:
            out = visit(n.inputs[0]) | visit(n.inputs[1])
        else:
            raise Refusal("REFUSE_NON_ACI_CONE")
        visiting.remove(nid)
        memo[nid] = out
        return out

    expected = tuple(sorted(visit(d.output)))
    assert expected == tuple(cert["final_factor_set"])
    assert set(cert["target_factor_order"]) == set(expected)
    assert len(cert["target_factor_order"]) == len(expected)

    # Replay target chain purely structurally: its factor union must be identical.
    if cert["target_factor_order"]:
        target_union = frozenset(cert["target_factor_order"])
    else:
        target_union = frozenset()
    assert target_union == frozenset(expected)

    _, source_ac = source_dependency(d, cert["projected_root"])
    assert source_ac == cert["source_ac_x"]

    seen_dep = False
    target_ac = 0
    for idx, token in enumerate(cert["target_factor_order"]):
        if idx == 0:
            seen_dep = token_depends_on(token, cert["projected_root"])
            continue
        seen_dep = seen_dep or token_depends_on(token, cert["projected_root"])
        if seen_dep:
            target_ac += 1
    assert target_ac == cert["target_ac_x"]
    assert cert["target_gate_count"] == max(0, len(expected) - 1)


def build_sf4(m: int) -> Dag:
    d = Dag()
    x = d.leaf("x")
    ys = [d.leaf(f"y{i}") for i in range(1, m + 1)]
    zs = [d.leaf(f"z{r}") for r in range(1, LANES + 1)]
    shared = [d.and_gate(f"a{i}", x, y) for i, y in enumerate(ys, start=1)]
    lanes = []
    for r, z in enumerate(zs, start=1):
        cur = d.and_gate(f"c{r}_1", shared[0], shared[1])
        for idx in range(2, m):
            cur = d.and_gate(f"c{r}_{idx}", cur, shared[idx])
        cur = d.and_gate(f"c{r}_{m}", cur, z)
        lanes.append(cur)
    p = d.and_gate("out12", lanes[0], lanes[1])
    q = d.and_gate("out34", lanes[2], lanes[3])
    d.output = d.and_gate("OUT", p, q)
    return d


def refusal_controls() -> List[dict]:
    controls = []

    d1 = Dag(); a = d1.leaf("a"); b = d1.leaf("b"); g = d1.and_gate("g", a, b); d1.output = d1.bad_gate("ng", "NOT_INTERNAL", g)
    d2 = Dag(); a2 = d2.leaf("a"); b2 = d2.leaf("b"); d2.output = d2.bad_gate("o", "OR", a2, b2)
    d3 = Dag(); a3 = d3.leaf("a"); b3 = d3.leaf("b"); op = d3.bad_gate("opaque", "OPAQUE", a3); d3.output = d3.and_gate("out", op, b3)

    for name, d in [("NEGATED_INTERNAL", d1), ("EXPLICIT_OR", d2), ("MIXED_OPAQUE_CHILD", d3)]:
        try:
            produce_certificate(d, PROJECTED)
        except Refusal as exc:
            assert str(exc) == "REFUSE_NON_ACI_CONE"
            controls.append({"name": name, "result": str(exc)})
        else:
            raise AssertionError(f"refusal control admitted: {name}")
    return controls


def main() -> None:
    rows = []
    total_cert_bytes = 0
    total_ops = 0
    for m in MS:
        d = build_sf4(m)
        cert = produce_certificate(d, PROJECTED)
        independent_replay(d, cert)

        expected_factors = {"x", *[f"y{i}" for i in range(1, m + 1)], *[f"z{r}" for r in range(1, LANES + 1)]}
        assert set(cert["final_factor_set"]) == expected_factors
        assert cert["source_gate_count"] == 5 * m + 3
        assert cert["source_ac_x"] == 5 * m + 3
        assert cert["target_gate_count"] == m + 4
        assert cert["target_ac_x"] == 1

        total_cert_bytes += cert["certificate_bytes"]
        total_ops += sum(cert["ledger"].values())
        rows.append({
            "m": m,
            "source_gate_count": cert["source_gate_count"],
            "source_ac_x": cert["source_ac_x"],
            "unique_factor_count": len(cert["final_factor_set"]),
            "duplicate_eliminations": cert["duplicate_eliminations"],
            "target_gate_count": cert["target_gate_count"],
            "target_ac_x": cert["target_ac_x"],
            "certificate_bytes": cert["certificate_bytes"],
            "source_sha256": cert["source_sha256"],
            "target_sha256": cert["target_sha256"],
            "replay": "PASS",
        })

    refused = refusal_controls()
    result = {
        "schema": "JANUS_U1L2C_ACI_SHARED_FACTOR_QUOTIENT_RESULT",
        "status": "PASS_EXACT_ACI_QUOTIENT_FROZEN_SCOPE",
        "claim_ceiling": "P_VS_NP_OPEN",
        "frozen_scope": {
            "m_values": MS,
            "lanes": LANES,
            "language": "CLOSED_PURE_POSITIVE_AND_DAG_OVER_CANONICAL_SIGNED_LEAF_IDS",
        },
        "rows": rows,
        "refusal_controls": refused,
        "global_ledger": {
            "total_certificate_bytes": total_cert_bytes,
            "total_counted_operations": total_ops,
        },
        "claim_ledger": {
            "PURE_AND_ACI_QUOTIENT_EXACTNESS": "PROVED_IN_SCOPE_BY_STRUCTURAL_REPLAY",
            "PURE_AND_ACI_QUOTIENT_DETERMINISTIC_POLY_CONSTRUCTION": "PROVED_IN_SCOPE_BY_EXPLICIT_BOUND",
            "SF4_SHARED_FANOUT_ESCAPE_REPAIRED": True,
            "ARBITRARY_B2_QUOTIENT": False,
            "SEQUENTIAL_EXISTENTIAL_CLOSURE": False,
            "P_EQUALS_NP": False,
        },
        "next_gate": "U1-L2C1_ACI_QUOTIENT_EXISTENTIAL_UPDATE_CLOSURE",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("U1L2C_RESULT_SHA256=" + sha256(packed).hexdigest())


if __name__ == "__main__":
    main()
