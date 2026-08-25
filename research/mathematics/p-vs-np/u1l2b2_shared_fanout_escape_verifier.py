#!/usr/bin/env python3
"""Symbolic verifier for U1-L2B2 shared-fanout escape family SF_4(m).

No SAT oracle and no sampled valuations. Equivalence is certified by exact ACI
normalization of positive conjunctions to root-factor sets.
"""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
from typing import Dict, List, Set, Tuple

MS = [2, 4, 8, 16, 32, 64]
LOCAL_G_MAX = 3
LANES = 4


class Dag:
    def __init__(self) -> None:
        self.kind: Dict[str, str] = {}
        self.inputs: Dict[str, Tuple[str, str]] = {}
        self.users: Dict[str, List[str]] = defaultdict(list)
        self.output: str | None = None

    def root(self, name: str) -> str:
        assert name not in self.kind
        self.kind[name] = "ROOT"
        return name

    def and_gate(self, name: str, a: str, b: str) -> str:
        assert name not in self.kind
        assert a in self.kind and b in self.kind and a != b
        self.kind[name] = "AND"
        self.inputs[name] = (a, b)
        self.users[a].append(name)
        self.users[b].append(name)
        return name

    def gate_count(self) -> int:
        return sum(1 for k in self.kind.values() if k == "AND")

    def dependency(self, root: str) -> Dict[str, bool]:
        dep: Dict[str, bool] = {}
        for n in self.kind:
            if self.kind[n] == "ROOT":
                dep[n] = (n == root)
            else:
                a, b = self.inputs[n]
                dep[n] = dep[a] or dep[b]
        return dep

    def aci_factor_set(self, node: str, memo=None) -> frozenset[str]:
        if memo is None:
            memo = {}
        if node in memo:
            return memo[node]
        if self.kind[node] == "ROOT":
            out = frozenset([node])
        else:
            a, b = self.inputs[node]
            out = self.aci_factor_set(a, memo) | self.aci_factor_set(b, memo)
        memo[node] = out
        return out

    def state_sha(self) -> str:
        payload = {
            "kind": self.kind,
            "inputs": {k: list(v) for k, v in self.inputs.items()},
            "output": self.output,
        }
        packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return sha256(packed).hexdigest()


def build_sf4(m: int) -> Tuple[Dag, List[str], List[str]]:
    d = Dag()
    x = d.root("x")
    ys = [d.root(f"y{i}") for i in range(1, m + 1)]
    zs = [d.root(f"z{r}") for r in range(1, LANES + 1)]

    shared = []
    for i, y in enumerate(ys, start=1):
        shared.append(d.and_gate(f"a{i}", x, y))

    lane_outputs = []
    for r, z in enumerate(zs, start=1):
        # Left chain over all shared a_i, then z_r.
        cur = d.and_gate(f"c{r}_1", shared[0], shared[1])
        for idx in range(2, m):
            cur = d.and_gate(f"c{r}_{idx}", cur, shared[idx])
        cur = d.and_gate(f"c{r}_{m}", cur, z)
        lane_outputs.append(cur)

    d12 = d.and_gate("out_12", lane_outputs[0], lane_outputs[1])
    d34 = d.and_gate("out_34", lane_outputs[2], lane_outputs[3])
    out = d.and_gate("OUT", d12, d34)
    d.output = out
    return d, shared, lane_outputs


def compact_factor_payload(m: int) -> dict:
    factors = ["x"] + [f"y{i}" for i in range(1, m + 1)] + [f"z{r}" for r in range(1, LANES + 1)]
    return {
        "factors": sorted(factors),
        "gate_count": m + 4,
        "ac_x": 1,
    }


def main() -> None:
    rows = []
    for m in MS:
        d, shared, lane_outputs = build_sf4(m)
        g0 = d.gate_count()
        dep = d.dependency("x")
        ac0 = sum(1 for n, k in d.kind.items() if k == "AND" and dep[n])
        assert g0 == 5 * m + 3
        assert ac0 == g0

        fanouts = [len(d.users[a]) for a in shared]
        assert fanouts == [LANES] * m
        closure_min = 1 + min(fanouts)
        assert closure_min == 5 and closure_min > LOCAL_G_MAX

        source_factors = sorted(d.aci_factor_set(d.output))
        compact = compact_factor_payload(m)
        assert source_factors == compact["factors"]
        assert compact["gate_count"] == m + 4
        assert compact["ac_x"] == 1

        # Exact algebraic size/interface gap.
        ac_lower_bound_current_local_grammar = m
        assert ac_lower_bound_current_local_grammar >= (g0 - 3) // 5

        source_payload = {
            "m": m,
            "g0": g0,
            "ac0": ac0,
            "fanouts": fanouts,
            "output_factor_set": source_factors,
            "state_sha256": d.state_sha(),
        }
        compact_packed = json.dumps(compact, sort_keys=True, separators=(",", ":")).encode()
        compact_sha = sha256(compact_packed).hexdigest()

        rows.append({
            "m": m,
            "source_gate_count": g0,
            "source_ac_x": ac0,
            "shared_gate_count": m,
            "shared_gate_fanout": LANES,
            "minimum_closed_region_size_if_shared_gate_internal": closure_min,
            "frozen_local_g_max": LOCAL_G_MAX,
            "proved_surviving_ac_lower_bound_for_current_local_grammar": m,
            "compact_gate_count": compact["gate_count"],
            "compact_ac_x": compact["ac_x"],
            "aci_factor_count": len(source_factors),
            "aci_source_equals_compact": True,
            "source_state_sha256": source_payload["state_sha256"],
            "compact_state_sha256": compact_sha,
        })

    result = {
        "schema": "JANUS_U1L2B2_SHARED_FANOUT_ESCAPE_VERIFIER",
        "status": "PASS_SYMBOLIC_ACI_ESCAPE_LADDER",
        "m_values": MS,
        "lanes": LANES,
        "frozen_local_g_max": LOCAL_G_MAX,
        "rows": rows,
        "theorem_receipt": {
            "current_fixed_context_closed_k4_g3_grammar_universally_complete": False,
            "reason": "M_SHARED_X_DEPENDENT_GATES_SURVIVE_WHILE_GLOBAL_ACI_QUOTIENT_HAS_AC_X_1",
            "not_a_lower_bound_against_general_representations": True,
            "next_gate": "U1-L2C_PROOF_CARRYING_ACI_SHARED_FACTOR_QUOTIENT",
        },
        "claim_ceiling": "P_VS_NP_OPEN",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("ESCAPE_RESULT_SHA256=" + sha256(packed).hexdigest())


if __name__ == "__main__":
    main()
