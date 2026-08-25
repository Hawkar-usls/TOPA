#!/usr/bin/env python3
"""PF5 connected-boundary adhesion gate v3.

Finite exact mechanics only. Two proof-carrying BDD wing states share a
nonempty boundary B. Private roots are projected inside their owner state,
then an exact explicit boundary JOIN is materialized before any shared root is
projected. All construction/update/table/witness work is charged.

This does not prove P=NP or P!=NP.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import product
import json
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import pf5_boundary_coverage_matrix_v0 as base


WIDTHS = (2, 4, 6, 8, 10, 12, 14)


@dataclass(frozen=True)
class AdhesionControl:
    name: str
    k: int
    right_target: bool

    @property
    def expected_sat(self) -> bool:
        return self.right_target is False

    @property
    def boundary(self) -> Tuple[int, ...]:
        return tuple(range(1, self.k + 1))

    @property
    def left_private(self) -> Tuple[int, ...]:
        return tuple(range(self.k + 1, 2 * self.k + 1))

    @property
    def right_private(self) -> Tuple[int, ...]:
        return tuple(range(2 * self.k + 1, 3 * self.k + 1))

    @property
    def input_bytes(self) -> int:
        return base.json_bytes({
            "name": self.name,
            "k": self.k,
            "right_target": self.right_target,
            "boundary": self.boundary,
            "left_private": self.left_private,
            "right_private": self.right_private,
            "wing": "PRIVATE_PARITY_CHAIN_PIN",
        })


def controls() -> List[AdhesionControl]:
    out: List[AdhesionControl] = []
    for k in WIDTHS:
        out.append(AdhesionControl(f"ADH_PARITY_K{k}_SAT", k, False))
        out.append(AdhesionControl(f"ADH_PARITY_K{k}_UNSAT", k, True))
    return out


def canon_hash(obj) -> str:
    return sha256(base.canon_json(obj).encode()).hexdigest()


def build_wing(
    boundary: Sequence[int], private: Sequence[int], target: bool
) -> Tuple[base.Dag, int]:
    if len(boundary) != len(private) or not boundary:
        raise ValueError("wing requires equal nonempty boundary/private chains")
    d = base.Dag()
    b = {v: d.var(v) for v in boundary}
    a = {v: d.var(v) for v in private}

    parts: List[int] = [d.eq(a[private[0]], b[boundary[0]])]
    for i in range(1, len(boundary)):
        parity_step = d.xor(a[private[i - 1]], b[boundary[i]])
        parts.append(d.eq(a[private[i]], parity_step))
    parts.append(a[private[-1]] if target else d.neg(a[private[-1]]))

    root = 1
    for z in parts:
        root = d.land(root, z)
    return d, root


def compile_bdd(
    d: base.Dag, raw_root: int, order: Sequence[int]
) -> Tuple[base.BDD, int, int]:
    b = base.BDD(order)
    memo: Dict[Tuple[int, int], int] = {}
    rec_calls = 0

    def rec(r: int, i: int) -> int:
        nonlocal rec_calls
        rec_calls += 1
        key = (r, i)
        if key in memo:
            return memo[key]
        if r in (0, 1):
            memo[key] = r
            return r
        if i == len(order):
            raise AssertionError("raw wing remained nonconstant after full order")
        x = order[i]
        lo = rec(d.restrict(r, x, False), i + 1)
        hi = rec(d.restrict(r, x, True), i + 1)
        out = b.mk(x, lo, hi)
        memo[key] = out
        return out

    root = rec(raw_root, 0)
    return b, root, rec_calls


def eval_bdd_count(b: base.BDD, root: int, assignment: Dict[int, bool]) -> Tuple[bool, int]:
    u = root
    ops = 0
    while u not in (0, 1):
        ops += 1
        v, lo, hi = b.nodes[u]
        if v not in assignment:
            raise AssertionError(f"BDD evaluation missing variable {v}")
        u = hi if assignment[v] else lo
    return bool(u), ops + 1


def eval_dag_count(d: base.Dag, root: int, assignment: Dict[int, bool]) -> Tuple[bool, int]:
    memo: Dict[int, bool] = {}
    ops = 0

    def rec(u: int) -> bool:
        nonlocal ops
        if u in memo:
            ops += 1
            return memo[u]
        ops += 1
        k = d.nodes[u]
        if k[0] == "C":
            z = bool(k[1])
        elif k[0] == "V":
            z = bool(assignment[int(k[1])])
        elif k[0] == "N":
            z = not rec(int(k[1]))
        elif k[0] == "A":
            z = rec(int(k[1])) and rec(int(k[2]))
        else:
            raise AssertionError(k)
        memo[u] = z
        return z

    return rec(root), ops


def project_private_bdd(
    b: base.BDD,
    root: int,
    private_order: Sequence[int],
    build_ops: int,
) -> Dict:
    proof: List[Dict] = []
    max_state = b.state_bytes(root)
    cumulative = max_state
    update_ops = 0

    for x in private_order:
        before = b.ops
        pre = root
        c0 = b.restrict(pre, x, False)
        c1 = b.restrict(pre, x, True)
        root = b.apply_or(c0, c1)
        update_ops += b.ops - before
        proof.append({"x": x, "pre": pre, "c0": c0, "c1": c1, "post": root})
        sb = b.state_bytes(root)
        max_state = max(max_state, sb)
        cumulative += sb
        base.check_common_caps(
            max_state,
            base.json_bytes(proof),
            cumulative,
            build_ops + update_ops,
        )

    return {
        "root": root,
        "proof": proof,
        "representation_bytes_peak": max_state,
        "cumulative_state_bytes": cumulative,
        "proof_bytes": base.json_bytes(proof),
        "projection_ops": update_ops,
    }


def rows_payload(rows: Iterable[str]) -> List[str]:
    return sorted(rows)


def table_state_bytes(left: Set[str], right: Set[str], joined: Set[str]) -> int:
    return base.json_bytes({
        "Lambda": rows_payload(left),
        "Rho": rows_payload(right),
        "J": rows_payload(joined),
    })


def materialize_boundary_relations(
    boundary: Sequence[int],
    left_bdd: base.BDD,
    left_root: int,
    right_bdd: base.BDD,
    right_root: int,
) -> Tuple[Set[str], Set[str], Set[str], Dict[str, int]]:
    left: Set[str] = set()
    right: Set[str] = set()
    enum_ops = 0
    eval_ops = 0

    for bits in product((0, 1), repeat=len(boundary)):
        enum_ops += 1
        env = {v: bool(bit) for v, bit in zip(boundary, bits)}
        lv, lo = eval_bdd_count(left_bdd, left_root, env)
        rv, ro = eval_bdd_count(right_bdd, right_root, env)
        eval_ops += lo + ro
        s = "".join(str(bit) for bit in bits)
        if lv:
            left.add(s)
        if rv:
            right.add(s)

    if len(left) <= len(right):
        joined = {row for row in left if row in right}
        join_ops = len(left)
    else:
        joined = {row for row in right if row in left}
        join_ops = len(right)

    return left, right, joined, {
        "boundary_enumeration_ops": enum_ops,
        "boundary_residual_eval_ops": eval_ops,
        "join_ops": join_ops,
    }


def project_join_rows(joined: Set[str], boundary: Sequence[int]) -> Tuple[Set[str], List[Dict], int, int, int]:
    current = set(joined)
    proof: List[Dict] = []
    ops = 0
    cumulative = base.json_bytes(rows_payload(current))
    peak = cumulative

    # Frozen left-to-right boundary order. At each step the projected bit is
    # position zero in the current canonical row encoding.
    for var in boundary:
        pre = set(current)
        post: Set[str] = set()
        for row in pre:
            ops += 1
            if not row:
                raise AssertionError("cannot project beyond empty boundary")
            post.add(row[1:])
            ops += 1
        proof.append({
            "x": var,
            "pre_sha256": canon_hash(rows_payload(pre)),
            "post_sha256": canon_hash(rows_payload(post)),
            "pre_rows": len(pre),
            "post_rows": len(post),
        })
        current = post
        sb = base.json_bytes(rows_payload(current))
        cumulative += sb
        peak = max(peak, sb)
    return current, proof, ops, peak, cumulative


def lift_private_witness(
    b: base.BDD,
    proof: Sequence[Dict],
    boundary_assignment: Dict[int, bool],
) -> Tuple[Dict[int, bool], int]:
    env: Dict[int, bool] = dict(boundary_assignment)
    witness_ops = 0
    for rec in reversed(proof):
        c0 = int(rec["c0"])
        c1 = int(rec["c1"])
        z0, o0 = eval_bdd_count(b, c0, env)
        witness_ops += o0
        x = int(rec["x"])
        if z0:
            env[x] = False
            continue
        z1, o1 = eval_bdd_count(b, c1, env)
        witness_ops += o1
        if not z1:
            raise AssertionError(f"private witness lift failed at {x}")
        env[x] = True
    return env, witness_ops


def connectivity_check(c: AdhesionControl) -> Tuple[bool, int]:
    # Variable interaction graph induced by parity-chain equations. Every
    # boundary variable occurs in both left and right wings.
    graph: Dict[int, Set[int]] = {v: set() for v in range(1, 3 * c.k + 1)}
    ops = 0

    def clique(xs: Sequence[int]) -> None:
        nonlocal ops
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                a, b = xs[i], xs[j]
                graph[a].add(b)
                graph[b].add(a)
                ops += 1

    B, A, C = c.boundary, c.left_private, c.right_private
    clique((A[0], B[0]))
    clique((C[0], B[0]))
    for i in range(1, c.k):
        clique((A[i], A[i - 1], B[i]))
        clique((C[i], C[i - 1], B[i]))

    seen: Set[int] = set()
    stack = [B[0]]
    while stack:
        v = stack.pop()
        ops += 1
        if v in seen:
            continue
        seen.add(v)
        stack.extend(graph[v] - seen)
    return seen == set(graph), ops


def expected_relation(k: int, target: bool) -> Set[str]:
    out: Set[str] = set()
    want = int(target)
    for bits in product((0, 1), repeat=k):
        if (sum(bits) & 1) == want:
            out.add("".join(str(x) for x in bits))
    return out


def run_control(c: AdhesionControl) -> Dict:
    B, A, C = c.boundary, c.left_private, c.right_private
    connected, connectivity_ops = connectivity_check(c)
    assert connected

    left_d, left_raw = build_wing(B, A, False)
    right_d, right_raw = build_wing(B, C, c.right_target)
    left_formula_build_ops = left_d.ops
    right_formula_build_ops = right_d.ops

    left_bdd: Optional[base.BDD] = None
    right_bdd: Optional[base.BDD] = None
    phase = "COMPILE"
    partial: Dict[str, object] = {}

    try:
        left_before = left_d.ops
        left_bdd, left_root, left_rec = compile_bdd(left_d, left_raw, tuple(A) + tuple(B))
        left_compile_ops = (left_d.ops - left_before) + left_bdd.ops + left_rec

        right_before = right_d.ops
        right_bdd, right_root, right_rec = compile_bdd(right_d, right_raw, tuple(C) + tuple(B))
        right_compile_ops = (right_d.ops - right_before) + right_bdd.ops + right_rec

        build_ops = (
            left_formula_build_ops + right_formula_build_ops
            + left_compile_ops + right_compile_ops + connectivity_ops
        )

        phase = "PRIVATE_PROJECTION"
        left_private = project_private_bdd(left_bdd, left_root, A, build_ops)
        right_private = project_private_bdd(right_bdd, right_root, C, build_ops + int(left_private["projection_ops"]))

        private_proof_bytes = int(left_private["proof_bytes"]) + int(right_private["proof_bytes"])
        private_cumulative = int(left_private["cumulative_state_bytes"]) + int(right_private["cumulative_state_bytes"])
        private_peak = int(left_private["representation_bytes_peak"]) + int(right_private["representation_bytes_peak"])
        private_project_ops = int(left_private["projection_ops"]) + int(right_private["projection_ops"])

        phase = "ADHESION_BUILD"
        left_rows, right_rows, joined_rows, table_ops = materialize_boundary_relations(
            B,
            left_bdd,
            int(left_private["root"]),
            right_bdd,
            int(right_private["root"]),
        )
        table_bytes = table_state_bytes(left_rows, right_rows, joined_rows)
        cumulative = private_cumulative + table_bytes
        peak = max(private_peak, table_bytes)
        total_ops = build_ops + private_project_ops + sum(table_ops.values())
        base.check_common_caps(peak, private_proof_bytes, cumulative, total_ops)

        partial.update({
            "left_boundary_rows": len(left_rows),
            "right_boundary_rows": len(right_rows),
            "join_rows": len(joined_rows),
            "adhesion_table_bytes": table_bytes,
        })

        phase = "BOUNDARY_PROJECTION"
        final_rows, boundary_proof, boundary_project_ops, boundary_peak, boundary_cumulative = project_join_rows(joined_rows, B)
        cumulative += boundary_cumulative
        peak = max(peak, boundary_peak)
        proof_bytes = private_proof_bytes + base.json_bytes(boundary_proof)
        total_ops += boundary_project_ops
        base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

        final_scalar = bool(final_rows)
        if final_rows not in (set(), {""}):
            raise AssertionError(f"unexpected terminal boundary relation {final_rows}")

        # Independent family oracle is used only as a validator, never to
        # construct Lambda/Rho/J or the witness.
        ref_left = expected_relation(c.k, False)
        ref_right = expected_relation(c.k, c.right_target)
        reference_ops = 2 * (1 << c.k)
        boundary_relations_exact = left_rows == ref_left and right_rows == ref_right
        join_exact = joined_rows == (ref_left & ref_right)
        expected_count = 1 << (c.k - 1)
        exponential_rows_observed = len(left_rows) == expected_count and len(right_rows) == expected_count

        witness: Optional[Dict[int, bool]] = None
        witness_ops = 0
        verification_ops = 0
        witness_valid: Optional[bool] = None
        witness_source: Optional[str] = None

        if final_scalar:
            chosen = min(joined_rows)
            boundary_assignment = {v: bit == "1" for v, bit in zip(B, chosen)}
            left_env, lo = lift_private_witness(left_bdd, left_private["proof"], boundary_assignment)
            right_env, ro = lift_private_witness(right_bdd, right_private["proof"], boundary_assignment)
            witness_ops += lo + ro

            witness = dict(boundary_assignment)
            for v in A:
                if v not in left_env:
                    raise AssertionError(f"left witness missing {v}")
                witness[v] = left_env[v]
            for v in C:
                if v not in right_env:
                    raise AssertionError(f"right witness missing {v}")
                if v in witness:
                    raise AssertionError(f"private witness overlap {v}")
                witness[v] = right_env[v]

            expected_vars = set(range(1, 3 * c.k + 1))
            if set(witness) != expected_vars:
                raise AssertionError("strict witness union incomplete")
            lv, lvo = eval_dag_count(left_d, left_raw, witness)
            rv, rvo = eval_dag_count(right_d, right_raw, witness)
            verification_ops += lvo + rvo
            witness_valid = lv and rv
            witness_source = "JOIN_ROW_PLUS_ACTUAL_WING_PROJECTION_PROOFS"
            if not witness_valid:
                raise AssertionError("strict adhesion witness verification failed")
        else:
            witness_valid = None
            witness_source = "NO_WITNESS_UNSAT_JOIN_EMPTY"

        verification_ops += reference_ops
        total_ops += witness_ops + verification_ops
        witness_bytes = base.json_bytes(witness or {})
        base.check_common_caps(peak, proof_bytes, cumulative, total_ops)

        cert = {
            "control": c.name,
            "k": c.k,
            "left_residual_sha256": canon_hash(left_bdd.state_bytes(int(left_private["root"]))),
            "right_residual_sha256": canon_hash(right_bdd.state_bytes(int(right_private["root"]))),
            "Lambda_sha256": canon_hash(rows_payload(left_rows)),
            "Rho_sha256": canon_hash(rows_payload(right_rows)),
            "J_sha256": canon_hash(rows_payload(joined_rows)),
            "boundary_projection": boundary_proof,
            "witness_sha256": canon_hash(witness or {}),
        }

        return {
            "control": c.name,
            "k": c.k,
            "expected_sat": c.expected_sat,
            "status": "PASS_EXACT_CLOSED",
            "cap_phase": None,
            "cap_reason": None,
            "connected": connected,
            "input_bytes": c.input_bytes,
            "left_boundary_rows": len(left_rows),
            "right_boundary_rows": len(right_rows),
            "expected_each_wing_rows": expected_count,
            "join_rows": len(joined_rows),
            "final_scalar": final_scalar,
            "private_projection_exact": True,
            "boundary_relations_exact": boundary_relations_exact,
            "adhesion_join_exact": join_exact,
            "repeated_boundary_project_exact": final_scalar == c.expected_sat,
            "strict_witness_glue_exact": (witness_valid is True) if final_scalar else True,
            "witness_valid": witness_valid,
            "witness_source": witness_source,
            "witness_bytes": witness_bytes,
            "representation_bytes_peak": peak,
            "cumulative_state_bytes": cumulative,
            "private_proof_bytes": private_proof_bytes,
            "boundary_proof_bytes": base.json_bytes(boundary_proof),
            "proof_bytes": proof_bytes,
            "build_ops": build_ops,
            "private_projection_ops": private_project_ops,
            "boundary_enumeration_ops": table_ops["boundary_enumeration_ops"],
            "boundary_residual_eval_ops": table_ops["boundary_residual_eval_ops"],
            "join_ops": table_ops["join_ops"],
            "boundary_projection_ops": boundary_project_ops,
            "witness_ops": witness_ops,
            "verification_ops": verification_ops,
            "total_charged_ops": total_ops,
            "adhesion_table_bytes": table_bytes,
            "explicit_table_exponential_footprint_observed": exponential_rows_observed,
            "certificate_sha256": canon_hash(cert),
            "witness": witness,
        }

    except base.CapHit as e:
        # Preserve all partial costs that are available at the point of failure.
        left_nodes = len(left_bdd.nodes) if left_bdd is not None else 0
        right_nodes = len(right_bdd.nodes) if right_bdd is not None else 0
        return {
            "control": c.name,
            "k": c.k,
            "expected_sat": c.expected_sat,
            "status": "CAP_HIT",
            "cap_phase": phase,
            "cap_reason": str(e),
            "connected": connected,
            "input_bytes": c.input_bytes,
            "left_bdd_nodes_partial": left_nodes,
            "right_bdd_nodes_partial": right_nodes,
            "partial": partial,
            "claim": "FINITE_EXPLICIT_BOUNDARY_REPRESENTATION_CAP_ONLY",
        }


def main(argv: Sequence[str]) -> int:
    rows = [run_control(c) for c in controls()]
    first_cap = next((r for r in rows if r["status"] == "CAP_HIT"), None)
    passed = [r for r in rows if r["status"] == "PASS_EXACT_CLOSED"]

    result = {
        "artifact_id": "PF5-CONNECTED-BOUNDARY-ADHESION-V3",
        "protocol": "PF5_CONNECTED_BOUNDARY_ADHESION_GATE_V3.md",
        "claim_ceiling": "P_VS_NP = OPEN",
        "widths_frozen_before_provider_run": list(WIDTHS),
        "caps": base.CAPS,
        "new_tuned_caps_added": False,
        "boundary_language": "EXPLICIT_CANONICAL_BITVECTOR_RELATION",
        "join_operator": "J_B(Lambda,Rho)=Lambda_INTERSECT_Rho",
        "controls": rows,
        "all_passed_controls_exact": all(
            r["boundary_relations_exact"]
            and r["adhesion_join_exact"]
            and r["repeated_boundary_project_exact"]
            and r["strict_witness_glue_exact"]
            for r in passed
        ),
        "explicit_table_exponential_footprint_observed": all(
            r["explicit_table_exponential_footprint_observed"] for r in passed
        ) if passed else False,
        "first_base_cap_hit": None if first_cap is None else {
            "control": first_cap["control"],
            "k": first_cap["k"],
            "phase": first_cap["cap_phase"],
            "reason": first_cap["cap_reason"],
        },
        "conditional_width_theorem": "POLY_WINGS + UNIVERSAL_O(LOG_N)_ADHESION => POLY_EXPLICIT_BOUNDARY_JOIN_PROJECT",
        "universal_o_log_n_adhesion_bound": "OPEN",
        "cheap_adhesion_discovery": "OPEN",
        "compressed_boundary_rewrite_discovery": "OPEN",
        "global_progress_amortization": "OPEN",
        "representation_lower_bound": "NOT_ESTABLISHED",
        "p_vs_np": "OPEN",
    }
    result["result_sha256"] = canon_hash(result)

    print("PF5_CONNECTED_BOUNDARY_ADHESION_PROTOCOL = FROZEN")
    for r in rows:
        if r["status"] == "PASS_EXACT_CLOSED":
            print(
                r["control"],
                "status=PASS_EXACT_CLOSED",
                "k=", r["k"],
                "rows=", r["left_boundary_rows"],
                "join=", r["join_rows"],
                "peak_bytes=", r["representation_bytes_peak"],
                "cum_bytes=", r["cumulative_state_bytes"],
                "ops=", r["total_charged_ops"],
                "witness=", r["witness_source"],
            )
        else:
            print(
                r["control"],
                "status=CAP_HIT",
                "k=", r["k"],
                "phase=", r["cap_phase"],
                "cap=", r["cap_reason"],
            )
    print("ADHESION_JOIN_EXACT_ON_PASSED_CONTROLS =", result["all_passed_controls_exact"])
    print("EXPLICIT_TABLE_EXPONENTIAL_FOOTPRINT_OBSERVED =", result["explicit_table_exponential_footprint_observed"])
    print("FIRST_BASE_CAP_HIT =", result["first_base_cap_hit"])
    print("UNIVERSAL_O_LOG_N_ADHESION_BOUND = OPEN")
    print("CHEAP_ADHESION_DISCOVERY = OPEN")
    print("COMPRESSED_BOUNDARY_REWRITE_DISCOVERY = OPEN")
    print("GLOBAL_PROGRESS_AMORTIZATION = OPEN")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])

    if "--json-out" in argv:
        i = list(argv).index("--json-out")
        with open(argv[i + 1], "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
