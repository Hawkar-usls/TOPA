#!/usr/bin/env python3
"""PF5 proof-carrying boundary coverage matrix v0.

Finite mechanics only.  The script compares exact state representations under
repeated existential projection and charges typed construction/update/witness
costs.  It does not prove any asymptotic P-vs-NP statement.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
from itertools import product
import json
import math
import random
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


CAPS = {
    "RAW_MAX_INTERNED_NODES": 5000,
    "OBDD_MAX_NONTERMINAL_NODES": 192,
    "FACTOR_MAX_BUCKET_SCOPE": 16,
    "MAX_PRIMARY_STATE_BYTES": 250_000,
    "MAX_PROOF_BYTES": 750_000,
    "MAX_CUMULATIVE_STATE_BYTES": 3_000_000,
    "MAX_OPERATION_COUNT": 3_000_000,
}

PRIMARY_LANES = [
    "RAW_B2_SHANNON",
    "FROZEN_ORDER_OBDD",
    "LIVE_WIDTH_FACTOR_DP",
    "TRANCEPTION_ORBIT_TEMPLATE",
]


class CapHit(RuntimeError):
    pass


def canon_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def json_bytes(obj) -> int:
    return len(canon_json(obj).encode("utf-8"))


def check_common_caps(state_bytes: int, proof_bytes: int, cumulative_bytes: int, ops: int) -> None:
    if state_bytes > CAPS["MAX_PRIMARY_STATE_BYTES"]:
        raise CapHit("MAX_PRIMARY_STATE_BYTES")
    if proof_bytes > CAPS["MAX_PROOF_BYTES"]:
        raise CapHit("MAX_PROOF_BYTES")
    if cumulative_bytes > CAPS["MAX_CUMULATIVE_STATE_BYTES"]:
        raise CapHit("MAX_CUMULATIVE_STATE_BYTES")
    if ops > CAPS["MAX_OPERATION_COUNT"]:
        raise CapHit("MAX_OPERATION_COUNT")


# ---------------------------------------------------------------------------
# Canonical AND/NOT DAG
# ---------------------------------------------------------------------------


class Dag:
    def __init__(self) -> None:
        self.nodes: List[Tuple] = [("C", 0), ("C", 1)]
        self.unique: Dict[Tuple, int] = {self.nodes[0]: 0, self.nodes[1]: 1}
        self.ops = 0
        self._restrict_cache: Dict[Tuple[int, int, bool], int] = {}

    def _intern(self, key: Tuple) -> int:
        self.ops += 1
        if key in self.unique:
            return self.unique[key]
        i = len(self.nodes)
        self.nodes.append(key)
        self.unique[key] = i
        return i

    def var(self, v: int) -> int:
        return self._intern(("V", int(v)))

    def neg(self, a: int) -> int:
        self.ops += 1
        if a == 0:
            return 1
        if a == 1:
            return 0
        k = self.nodes[a]
        if k[0] == "N":
            return int(k[1])
        return self._intern(("N", int(a)))

    def land(self, a: int, b: int) -> int:
        self.ops += 1
        if a == 0 or b == 0:
            return 0
        if a == 1:
            return b
        if b == 1:
            return a
        if a == b:
            return a
        if self.nodes[a] == ("N", b) or self.nodes[b] == ("N", a):
            return 0
        if a > b:
            a, b = b, a
        return self._intern(("A", int(a), int(b)))

    def lor(self, a: int, b: int) -> int:
        return self.neg(self.land(self.neg(a), self.neg(b)))

    def xor(self, a: int, b: int) -> int:
        return self.land(self.lor(a, b), self.neg(self.land(a, b)))

    def eq(self, a: int, b: int) -> int:
        return self.neg(self.xor(a, b))

    def eval(self, root: int, assignment: Dict[int, bool]) -> bool:
        memo: Dict[int, bool] = {}

        def rec(u: int) -> bool:
            if u in memo:
                return memo[u]
            k = self.nodes[u]
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

        return rec(root)

    def restrict(self, root: int, var: int, value: bool) -> int:
        key = (root, var, bool(value))
        if key in self._restrict_cache:
            self.ops += 1
            return self._restrict_cache[key]
        self.ops += 1
        k = self.nodes[root]
        if k[0] == "C":
            out = root
        elif k[0] == "V":
            out = int(bool(value)) if int(k[1]) == var else root
        elif k[0] == "N":
            out = self.neg(self.restrict(int(k[1]), var, value))
        elif k[0] == "A":
            out = self.land(
                self.restrict(int(k[1]), var, value),
                self.restrict(int(k[2]), var, value),
            )
        else:
            raise AssertionError(k)
        self._restrict_cache[key] = out
        return out

    def reachable(self, root: int) -> List[int]:
        seen: Set[int] = set()
        stack = [root]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            k = self.nodes[u]
            if k[0] == "N":
                stack.append(int(k[1]))
            elif k[0] == "A":
                stack.extend([int(k[1]), int(k[2])])
        return sorted(seen)

    def state_payload(self, root: int):
        ids = self.reachable(root)
        return {"root": root, "nodes": [[i, *self.nodes[i]] for i in ids]}

    def state_bytes(self, root: int) -> int:
        return json_bytes(self.state_payload(root))


@dataclass(frozen=True)
class Control:
    name: str
    kind: str
    param: int
    root_vars: Tuple[int, ...]
    projection_order: Tuple[int, ...]
    obdd_order: Tuple[int, ...]
    spec: Tuple

    @property
    def input_bytes(self) -> int:
        return json_bytes({
            "name": self.name,
            "kind": self.kind,
            "param": self.param,
            "root_vars": self.root_vars,
            "projection_order": self.projection_order,
            "obdd_order": self.obdd_order,
            "spec": self.spec,
        })


def canonical_clause(lits: Iterable[int]) -> Tuple[int, ...]:
    return tuple(sorted(set(int(x) for x in lits), key=lambda z: (abs(z), z < 0)))


def make_random3sat(n: int, m: int, tag: str) -> Tuple[Tuple[int, ...], ...]:
    seed = int.from_bytes(sha256(tag.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(seed)
    out: Set[Tuple[int, ...]] = set()
    while len(out) < m:
        vs = rng.sample(range(1, n + 1), 3)
        lits = [v if rng.getrandbits(1) else -v for v in vs]
        out.add(canonical_clause(lits))
    return tuple(sorted(out))


def make_controls() -> List[Control]:
    parity_n = 12
    eq_n = 8
    fan_n = 6
    rnd_n = 12
    rnd_m = math.floor(4.30 * rnd_n)
    rnd_clauses = make_random3sat(
        rnd_n, rnd_m, f"PF5-MATRIX-RANDOM3SAT-CAL-V0|n={rnd_n}"
    )

    eq_roots = tuple(range(1, 2 * eq_n + 1))
    eq_interleaved: List[int] = []
    for i in range(1, eq_n + 1):
        eq_interleaved.extend([i, eq_n + i])

    return [
        Control(
            "PARITY_CHAIN_12",
            "PARITY",
            parity_n,
            tuple(range(1, parity_n + 1)),
            tuple(range(1, parity_n + 1)),
            tuple(range(1, parity_n + 1)),
            ("PARITY_EQ_1", parity_n),
        ),
        Control(
            "EQ_PAIRS_INTERLEAVED_8",
            "EQUALITY",
            eq_n,
            eq_roots,
            eq_roots,
            tuple(eq_interleaved),
            ("EQ_PAIRS", eq_n),
        ),
        Control(
            "EQ_PAIRS_BLOCKED_8",
            "EQUALITY",
            eq_n,
            eq_roots,
            eq_roots,
            eq_roots,
            ("EQ_PAIRS", eq_n),
        ),
        Control(
            "FANOUT_PAIR_ARCH_6",
            "FANOUT",
            fan_n,
            tuple(range(1, 2 * fan_n + 1)),
            tuple(range(1, 2 * fan_n + 1)),
            tuple(range(1, 2 * fan_n + 1)),
            ("PAIR_FANOUT", fan_n),
        ),
        Control(
            "RANDOM3SAT_CAL_12",
            "CNF",
            rnd_n,
            tuple(range(1, rnd_n + 1)),
            tuple(range(1, rnd_n + 1)),
            tuple(range(1, rnd_n + 1)),
            ("CNF", rnd_clauses),
        ),
    ]


def build_control(c: Control) -> Tuple[Dag, int]:
    d = Dag()
    vs = {v: d.var(v) for v in c.root_vars}

    if c.kind == "PARITY":
        root = vs[c.root_vars[0]]
        for v in c.root_vars[1:]:
            root = d.xor(root, vs[v])
        return d, root

    if c.kind == "EQUALITY":
        n = c.param
        parts = [d.eq(vs[i], vs[n + i]) for i in range(1, n + 1)]
        root = 1
        for z in parts:
            root = d.land(root, z)
        return d, root

    if c.kind == "FANOUT":
        n = c.param
        e = [d.land(vs[i], vs[n + i]) for i in range(1, n + 1)]
        pair_nodes: List[int] = []
        for i in range(n):
            for j in range(i + 1, n):
                pair_nodes.append(d.land(e[i], e[j]))
        root = 1
        for z in pair_nodes:
            root = d.land(root, z)
        return d, root

    if c.kind == "CNF":
        clauses = c.spec[1]
        root = 1
        for clause in clauses:
            cr = 0
            for lit in clause:
                lv = vs[abs(lit)] if lit > 0 else d.neg(vs[abs(lit)])
                cr = d.lor(cr, lv)
            root = d.land(root, cr)
        return d, root

    raise AssertionError(c.kind)


def brute_sat(c: Control) -> Tuple[bool, Optional[Dict[int, bool]], int]:
    d, root = build_control(c)
    ops = 0
    for bits in product((False, True), repeat=len(c.root_vars)):
        ops += 1
        a = dict(zip(c.root_vars, bits))
        if d.eval(root, a):
            return True, a, ops
    return False, None, ops


# ---------------------------------------------------------------------------
# RAW B2 Shannon projection
# ---------------------------------------------------------------------------


def run_raw(c: Control) -> Dict:
    d, root = build_control(c)
    build_ops = d.ops
    proof: List[Dict] = []
    max_state = d.state_bytes(root)
    cumulative = max_state
    update_ops = 0
    cap_reason = None
    final_scalar: Optional[bool] = None
    witness: Optional[Dict[int, bool]] = None

    try:
        for x in c.projection_order:
            before_ops = d.ops
            pre = root
            c0 = d.restrict(pre, x, False)
            c1 = d.restrict(pre, x, True)
            root = d.lor(c0, c1)
            update_ops += d.ops - before_ops
            proof.append({"x": x, "pre": pre, "c0": c0, "c1": c1, "post": root})
            state_b = d.state_bytes(root)
            max_state = max(max_state, state_b)
            cumulative += state_b
            proof_b = json_bytes(proof)
            if len(d.nodes) > CAPS["RAW_MAX_INTERNED_NODES"]:
                raise CapHit("RAW_MAX_INTERNED_NODES")
            check_common_caps(max_state, proof_b, cumulative, build_ops + update_ops)

        if root not in (0, 1):
            raise AssertionError("all roots projected but RAW state is nonterminal")
        final_scalar = bool(root)

        witness_ops = 0
        if final_scalar:
            witness = {}
            for rec in reversed(proof):
                witness_ops += 1
                if d.eval(int(rec["c0"]), witness):
                    witness[int(rec["x"])] = False
                elif d.eval(int(rec["c1"]), witness):
                    witness[int(rec["x"])] = True
                else:
                    raise AssertionError("RAW witness lift failed")
        proof_b = json_bytes(proof)
        witness_b = json_bytes(witness or {})
        cert_payload = {"nodes": d.nodes, "root": root, "proof": proof}
        digest = sha256(canon_json(cert_payload).encode()).hexdigest()
        return {
            "lane": "RAW_B2_SHANNON",
            "status": "PASS_EXACT_CLOSED",
            "cap_reason": None,
            "final_scalar": final_scalar,
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": proof_b,
            "witness_bytes": witness_b,
            "build_ops": build_ops,
            "failed_discovery_ops": 0,
            "root_projection_ops": update_ops,
            "terminal_finalize_ops": 0,
            "verification_ops": 0,
            "witness_ops": witness_ops,
            "interned_nodes_total": len(d.nodes),
            "certificate_sha256": digest,
            "witness": witness,
        }
    except CapHit as e:
        cap_reason = str(e)
        return {
            "lane": "RAW_B2_SHANNON",
            "status": "CAP_HIT",
            "cap_reason": cap_reason,
            "final_scalar": None,
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": json_bytes(proof),
            "witness_bytes": 0,
            "build_ops": build_ops,
            "failed_discovery_ops": 0,
            "root_projection_ops": update_ops,
            "terminal_finalize_ops": 0,
            "verification_ops": 0,
            "witness_ops": 0,
            "interned_nodes_total": len(d.nodes),
            "certificate_sha256": None,
            "witness": None,
        }


# ---------------------------------------------------------------------------
# Frozen-order OBDD
# ---------------------------------------------------------------------------


class BDD:
    def __init__(self, order: Sequence[int]) -> None:
        self.order = tuple(order)
        self.rank = {v: i for i, v in enumerate(self.order)}
        self.nodes: Dict[int, Tuple[int, int, int]] = {}
        self.unique: Dict[Tuple[int, int, int], int] = {}
        self.next_id = 2
        self.ops = 0

    def mk(self, var: int, low: int, high: int) -> int:
        self.ops += 1
        if low == high:
            return low
        key = (var, low, high)
        if key in self.unique:
            return self.unique[key]
        if len(self.nodes) >= CAPS["OBDD_MAX_NONTERMINAL_NODES"]:
            raise CapHit("OBDD_MAX_NONTERMINAL_NODES")
        u = self.next_id
        self.next_id += 1
        self.nodes[u] = key
        self.unique[key] = u
        return u

    def eval(self, root: int, assignment: Dict[int, bool]) -> bool:
        u = root
        while u not in (0, 1):
            v, lo, hi = self.nodes[u]
            u = hi if assignment[v] else lo
        return bool(u)

    def restrict(self, root: int, var: int, value: bool) -> int:
        memo: Dict[int, int] = {}

        def rec(u: int) -> int:
            self.ops += 1
            if u in (0, 1):
                return u
            if u in memo:
                return memo[u]
            v, lo, hi = self.nodes[u]
            if v == var:
                out = rec(hi if value else lo)
            else:
                out = self.mk(v, rec(lo), rec(hi))
            memo[u] = out
            return out

        return rec(root)

    def apply_or(self, a: int, b: int) -> int:
        memo: Dict[Tuple[int, int], int] = {}

        def rec(u: int, v: int) -> int:
            self.ops += 1
            if u == 1 or v == 1:
                return 1
            if u == 0:
                return v
            if v == 0:
                return u
            if u == v:
                return u
            key = (u, v) if u <= v else (v, u)
            if key in memo:
                return memo[key]
            uv, ul, uh = self.nodes[u]
            vv, vl, vh = self.nodes[v]
            if self.rank[uv] == self.rank[vv]:
                out = self.mk(uv, rec(ul, vl), rec(uh, vh))
            elif self.rank[uv] < self.rank[vv]:
                out = self.mk(uv, rec(ul, v), rec(uh, v))
            else:
                out = self.mk(vv, rec(u, vl), rec(u, vh))
            memo[key] = out
            return out

        return rec(a, b)

    def reachable(self, root: int) -> List[int]:
        seen: Set[int] = set()
        stack = [root]
        while stack:
            u = stack.pop()
            if u in (0, 1) or u in seen:
                continue
            seen.add(u)
            _, lo, hi = self.nodes[u]
            stack.extend([lo, hi])
        return sorted(seen)

    def state_bytes(self, root: int) -> int:
        ids = self.reachable(root)
        return json_bytes({
            "order": self.order,
            "root": root,
            "nodes": [[u, *self.nodes[u]] for u in ids],
        })


def build_bdd_from_raw(c: Control) -> Tuple[BDD, int, Dag, int]:
    d, raw_root = build_control(c)
    b = BDD(c.obdd_order)
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
        if i == len(c.obdd_order):
            raise AssertionError("raw root nonconstant after full OBDD order")
        x = c.obdd_order[i]
        lo = rec(d.restrict(r, x, False), i + 1)
        hi = rec(d.restrict(r, x, True), i + 1)
        out = b.mk(x, lo, hi)
        memo[key] = out
        return out

    root = rec(raw_root, 0)
    return b, root, d, rec_calls


def run_obdd(c: Control) -> Dict:
    proof: List[Dict] = []
    max_state = 0
    cumulative = 0
    try:
        b, root, raw_dag, rec_calls = build_bdd_from_raw(c)
        build_ops = b.ops + raw_dag.ops + rec_calls
        max_state = b.state_bytes(root)
        cumulative = max_state
        update_ops = 0
        for x in c.projection_order:
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
            check_common_caps(
                max_state,
                json_bytes(proof),
                cumulative,
                build_ops + update_ops,
            )

        if root not in (0, 1):
            raise AssertionError("all roots projected but OBDD state is nonterminal")
        final_scalar = bool(root)
        witness: Optional[Dict[int, bool]] = None
        witness_ops = 0
        if final_scalar:
            witness = {}
            for rec in reversed(proof):
                witness_ops += 1
                if b.eval(int(rec["c0"]), witness):
                    witness[int(rec["x"])] = False
                elif b.eval(int(rec["c1"]), witness):
                    witness[int(rec["x"])] = True
                else:
                    raise AssertionError("OBDD witness lift failed")
        cert = {
            "order": b.order,
            "nodes": sorted((u, *k) for u, k in b.nodes.items()),
            "root": root,
            "proof": proof,
        }
        return {
            "lane": "FROZEN_ORDER_OBDD",
            "status": "PASS_EXACT_CLOSED",
            "cap_reason": None,
            "final_scalar": final_scalar,
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": json_bytes(proof),
            "witness_bytes": json_bytes(witness or {}),
            "build_ops": build_ops,
            "failed_discovery_ops": 0,
            "root_projection_ops": update_ops,
            "terminal_finalize_ops": 0,
            "verification_ops": 0,
            "witness_ops": witness_ops,
            "nonterminal_nodes_total": len(b.nodes),
            "certificate_sha256": sha256(canon_json(cert).encode()).hexdigest(),
            "witness": witness,
        }
    except CapHit as e:
        return {
            "lane": "FROZEN_ORDER_OBDD",
            "status": "CAP_HIT",
            "cap_reason": str(e),
            "final_scalar": None,
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": json_bytes(proof),
            "witness_bytes": 0,
            "build_ops": locals().get("build_ops", 0),
            "failed_discovery_ops": 0,
            "root_projection_ops": locals().get("update_ops", 0),
            "terminal_finalize_ops": 0,
            "verification_ops": 0,
            "witness_ops": 0,
            "nonterminal_nodes_total": len(locals().get("b", BDD(c.obdd_order)).nodes),
            "certificate_sha256": None,
            "witness": None,
        }


# ---------------------------------------------------------------------------
# Exact factor/boundary variable elimination
# ---------------------------------------------------------------------------


@dataclass
class Factor:
    scope: Tuple[str, ...]
    rows: Set[Tuple[int, ...]]
    provenance: str

    def payload(self):
        return {
            "scope": self.scope,
            "rows": sorted(self.rows),
            "provenance": self.provenance,
        }


def raw_ref(d: Dag, u: int) -> Tuple[str, object]:
    k = d.nodes[u]
    if k[0] == "C":
        return ("CONST", bool(k[1]))
    if k[0] == "V":
        return ("VAR", f"r{int(k[1])}")
    return ("VAR", f"g{u}")


def ref_value(ref: Tuple[str, object], env: Dict[str, int]) -> bool:
    return bool(ref[1]) if ref[0] == "CONST" else bool(env[str(ref[1])])


def factors_from_dag(d: Dag, root: int) -> Tuple[List[Factor], List[str], int]:
    factors: List[Factor] = []
    ops = 0
    reachable = d.reachable(root)
    gate_vars: List[str] = []
    for u in reachable:
        k = d.nodes[u]
        if k[0] not in ("N", "A"):
            continue
        out = f"g{u}"
        gate_vars.append(out)
        refs = [raw_ref(d, int(k[1]))]
        if k[0] == "A":
            refs.append(raw_ref(d, int(k[2])))
        scope = [out]
        for r in refs:
            if r[0] == "VAR" and str(r[1]) not in scope:
                scope.append(str(r[1]))
        scope_t = tuple(scope)
        rows: Set[Tuple[int, ...]] = set()
        for bits in product((0, 1), repeat=len(scope_t)):
            ops += 1
            env = dict(zip(scope_t, bits))
            lhs = bool(env[out])
            if k[0] == "N":
                rhs = not ref_value(refs[0], env)
            else:
                rhs = ref_value(refs[0], env) and ref_value(refs[1], env)
            if lhs == rhs:
                rows.add(tuple(bits))
        factors.append(Factor(scope_t, rows, f"gate:{u}:{k[0]}"))

    rr = raw_ref(d, root)
    if rr[0] == "CONST":
        rows = {()} if bool(rr[1]) else set()
        factors.append(Factor((), rows, "assert-output-const"))
    else:
        factors.append(Factor((str(rr[1]),), {(1,)}, "assert-output-true"))

    return factors, gate_vars, ops


def factors_bytes(factors: Sequence[Factor]) -> int:
    return json_bytes([f.payload() for f in factors])


def eliminate_factor_var(
    factors: List[Factor], var: str
) -> Tuple[List[Factor], Dict, int, int]:
    bucket = [f for f in factors if var in f.scope]
    if not bucket:
        return list(factors), {"var": var, "kind": "FREE", "scope": (), "choice": {}}, 0, 0

    union: List[str] = []
    for f in bucket:
        for z in f.scope:
            if z not in union:
                union.append(z)
    if len(union) > CAPS["FACTOR_MAX_BUCKET_SCOPE"]:
        raise CapHit("FACTOR_MAX_BUCKET_SCOPE")

    pos = {z: i for i, z in enumerate(union)}
    out_scope = tuple(z for z in union if z != var)
    out_rows: Set[Tuple[int, ...]] = set()
    choice: Dict[str, int] = {}
    ops = 0

    for bits in product((0, 1), repeat=len(union)):
        valid = True
        for f in bucket:
            ops += 1
            row = tuple(bits[pos[z]] for z in f.scope)
            if row not in f.rows:
                valid = False
                break
        if not valid:
            continue
        out_row = tuple(bits[pos[z]] for z in out_scope)
        out_rows.add(out_row)
        key = ",".join(str(x) for x in out_row)
        choice.setdefault(key, int(bits[pos[var]]))

    kept = [f for f in factors if var not in f.scope]
    kept.append(Factor(out_scope, out_rows, f"exists:{var}"))
    rec = {"var": var, "kind": "ELIM", "scope": out_scope, "choice": choice}
    return kept, rec, ops, len(union) - 1


def factor_scalar(factors: Sequence[Factor]) -> Optional[bool]:
    if any(f.scope for f in factors):
        return None
    return all(() in f.rows for f in factors)


def run_factor(c: Control) -> Dict:
    d, root = build_control(c)
    factors, gate_vars, build_ops = factors_from_dag(d, root)
    proof: List[Dict] = []
    max_state = factors_bytes(factors)
    cumulative = max_state
    max_boundary_width = 0
    root_ops = 0
    final_ops = 0
    try:
        for x in c.projection_order:
            factors, rec, ops, width = eliminate_factor_var(factors, f"r{x}")
            root_ops += ops
            max_boundary_width = max(max_boundary_width, width)
            proof.append(rec)
            sb = factors_bytes(factors)
            max_state = max(max_state, sb)
            cumulative += sb
            check_common_caps(
                max_state,
                json_bytes(proof),
                cumulative,
                build_ops + root_ops + final_ops,
            )

        def gate_id(z: str) -> int:
            return int(z[1:])

        for gv in sorted(set(gate_vars), key=gate_id, reverse=True):
            factors, rec, ops, width = eliminate_factor_var(factors, gv)
            final_ops += ops
            max_boundary_width = max(max_boundary_width, width)
            proof.append(rec)
            sb = factors_bytes(factors)
            max_state = max(max_state, sb)
            cumulative += sb
            check_common_caps(
                max_state,
                json_bytes(proof),
                cumulative,
                build_ops + root_ops + final_ops,
            )

        scalar = factor_scalar(factors)
        if scalar is None:
            raise AssertionError("factor finalization left live variables")

        witness: Optional[Dict[int, bool]] = None
        witness_ops = 0
        all_assignment: Dict[str, int] = {}
        if scalar:
            for rec in reversed(proof):
                witness_ops += 1
                var = str(rec["var"])
                if rec["kind"] == "FREE":
                    all_assignment[var] = 0
                    continue
                scope = tuple(rec["scope"])
                row = tuple(all_assignment[z] for z in scope)
                key = ",".join(str(x) for x in row)
                if key not in rec["choice"]:
                    raise AssertionError(f"missing factor witness row for {var}")
                all_assignment[var] = int(rec["choice"][key])
            witness = {v: bool(all_assignment.get(f"r{v}", 0)) for v in c.root_vars}

        cert = {
            "final_factors": [f.payload() for f in factors],
            "proof": proof,
        }
        return {
            "lane": "LIVE_WIDTH_FACTOR_DP",
            "status": "PASS_EXACT_CLOSED",
            "cap_reason": None,
            "final_scalar": bool(scalar),
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": json_bytes(proof),
            "witness_bytes": json_bytes(witness or {}),
            "build_ops": build_ops,
            "failed_discovery_ops": 0,
            "root_projection_ops": root_ops,
            "terminal_finalize_ops": final_ops,
            "verification_ops": 0,
            "witness_ops": witness_ops,
            "max_boundary_width": max_boundary_width,
            "certificate_sha256": sha256(canon_json(cert).encode()).hexdigest(),
            "witness": witness,
        }
    except CapHit as e:
        return {
            "lane": "LIVE_WIDTH_FACTOR_DP",
            "status": "CAP_HIT",
            "cap_reason": str(e),
            "final_scalar": None,
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": json_bytes(proof),
            "witness_bytes": 0,
            "build_ops": build_ops,
            "failed_discovery_ops": 0,
            "root_projection_ops": root_ops,
            "terminal_finalize_ops": final_ops,
            "verification_ops": 0,
            "witness_ops": 0,
            "max_boundary_width": max_boundary_width,
            "certificate_sha256": None,
            "witness": None,
        }


# ---------------------------------------------------------------------------
# Restricted Tranception/orbit template lane
# ---------------------------------------------------------------------------


def run_orbit(c: Control) -> Dict:
    proof: List[Dict] = []
    discovery_ops = 0
    max_state = 0
    cumulative = 0

    if c.kind == "PARITY":
        discovery_ops = 1
        state = {"kind": "PARITY_EQ_1", "vars": list(c.root_vars)}
        max_state = json_bytes(state)
        cumulative = max_state
        active = True
        for x in c.projection_order:
            if active and x in state["vars"]:
                others = [v for v in state["vars"] if v != x]
                proof.append({"kind": "PARITY_LIFT", "x": x, "others": others})
                state = {"kind": "TRUE", "vars": others}
                active = False
            else:
                proof.append({"kind": "FREE", "x": x})
                if "vars" in state and x in state["vars"]:
                    state["vars"].remove(x)
            sb = json_bytes(state)
            max_state = max(max_state, sb)
            cumulative += sb
        final_scalar = True
        witness: Dict[int, bool] = {}
        witness_ops = 0
        for rec in reversed(proof):
            witness_ops += 1
            x = int(rec["x"])
            if rec["kind"] == "FREE":
                witness[x] = False
            else:
                p = 0
                for v in rec["others"]:
                    p ^= int(bool(witness[int(v)]))
                witness[x] = bool(1 ^ p)
        cert = {"state": state, "proof": proof}
        return {
            "lane": "TRANCEPTION_ORBIT_TEMPLATE",
            "status": "PASS_EXACT_CLOSED",
            "cap_reason": None,
            "final_scalar": final_scalar,
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": json_bytes(proof),
            "witness_bytes": json_bytes(witness),
            "build_ops": discovery_ops,
            "failed_discovery_ops": 0,
            "root_projection_ops": len(proof),
            "terminal_finalize_ops": 0,
            "verification_ops": 0,
            "witness_ops": witness_ops,
            "template": "PARITY_EQ_1",
            "certificate_sha256": sha256(canon_json(cert).encode()).hexdigest(),
            "witness": witness,
        }

    if c.kind == "EQUALITY":
        discovery_ops = 2
        n = c.param
        pairs: Set[Tuple[int, int]] = {(i, n + i) for i in range(1, n + 1)}
        state = {"kind": "EQ_PAIRS", "pairs": sorted(pairs)}
        max_state = json_bytes(state)
        cumulative = max_state
        for x in c.projection_order:
            hit = None
            for p in sorted(pairs):
                if x in p:
                    hit = p
                    break
            if hit is None:
                proof.append({"kind": "FREE", "x": x})
            else:
                other = hit[1] if hit[0] == x else hit[0]
                proof.append({"kind": "EQ_LIFT", "x": x, "other": other})
                pairs.remove(hit)
            state = {"kind": "EQ_PAIRS", "pairs": sorted(pairs)}
            sb = json_bytes(state)
            max_state = max(max_state, sb)
            cumulative += sb
        final_scalar = True
        witness: Dict[int, bool] = {}
        witness_ops = 0
        for rec in reversed(proof):
            witness_ops += 1
            x = int(rec["x"])
            if rec["kind"] == "FREE":
                witness[x] = False
            else:
                witness[x] = bool(witness[int(rec["other"])])
        cert = {"state": state, "proof": proof}
        return {
            "lane": "TRANCEPTION_ORBIT_TEMPLATE",
            "status": "PASS_EXACT_CLOSED",
            "cap_reason": None,
            "final_scalar": final_scalar,
            "representation_bytes_peak": max_state,
            "cumulative_state_bytes": cumulative,
            "proof_bytes": json_bytes(proof),
            "witness_bytes": json_bytes(witness),
            "build_ops": discovery_ops,
            "failed_discovery_ops": 0,
            "root_projection_ops": len(proof),
            "terminal_finalize_ops": 0,
            "verification_ops": 0,
            "witness_ops": witness_ops,
            "template": "EQ_PAIRS",
            "certificate_sha256": sha256(canon_json(cert).encode()).hexdigest(),
            "witness": witness,
        }

    return {
        "lane": "TRANCEPTION_ORBIT_TEMPLATE",
        "status": "UNSUPPORTED",
        "cap_reason": None,
        "final_scalar": None,
        "representation_bytes_peak": 0,
        "cumulative_state_bytes": 0,
        "proof_bytes": 0,
        "witness_bytes": 0,
        "build_ops": 2,
        "failed_discovery_ops": 2,
        "root_projection_ops": 0,
        "terminal_finalize_ops": 0,
        "verification_ops": 0,
        "witness_ops": 0,
        "template": None,
        "certificate_sha256": None,
        "witness": None,
    }


# ---------------------------------------------------------------------------
# C2G laminar sidecar contract
# ---------------------------------------------------------------------------


def clauses_laminar(clauses: Sequence[Tuple[int, ...]]) -> bool:
    sets = [set(c) for c in clauses]
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            a, b = sets[i], sets[j]
            disjoint_cubes = any(-x in b for x in a)
            a_subset_b_cube = b < a  # Q(a) proper subset Q(b) iff b subset a
            b_subset_a_cube = a < b
            if sum(bool(z) for z in (disjoint_cubes, a_subset_b_cube, b_subset_a_cube)) != 1:
                return False
    return True


def run_c2g(c: Control) -> Dict:
    # Finite sanity fixture for the sidecar geometry itself.
    assert clauses_laminar([(1,), (1, 2), (-1, 3)])
    return {
        "lane": "C2G_LAMINAR",
        "status": "SIDECAR_ONLY",
        "role": "PROGRESS_SIDECAR",
        "primary_boundary_representation": False,
        "project_supported_as_primary": False,
        "composition": "COMPOSABLE_IF_SHORT_PROOF_CARRYING_REASON_IS_SUPPLIED",
        "universal_short_reason_discovery": "OPEN",
        "representation_bytes_peak": 0,
        "cumulative_state_bytes": 0,
        "proof_bytes": 0,
        "witness_bytes": 0,
        "build_ops": 1,
        "failed_discovery_ops": 0,
        "root_projection_ops": 0,
        "terminal_finalize_ops": 0,
        "verification_ops": 1,
        "witness_ops": 0,
        "final_scalar": None,
        "certificate_sha256": None,
        "witness": None,
    }


# ---------------------------------------------------------------------------
# Verification + matrix
# ---------------------------------------------------------------------------


def verify_completed_lane(c: Control, lane: Dict, reference_sat: bool) -> int:
    if lane["status"] != "PASS_EXACT_CLOSED":
        return 0
    ops = 1
    assert bool(lane["final_scalar"]) == bool(reference_sat), (c.name, lane["lane"])
    if reference_sat:
        w = lane.get("witness")
        assert w is not None
        d, root = build_control(c)
        ops += 1
        assert d.eval(root, {int(k): bool(v) for k, v in w.items()}), (c.name, lane["lane"], w)
    return ops


def matrix_run() -> Dict:
    controls = make_controls()
    out_controls: List[Dict] = []

    for c in controls:
        sat, ref_witness, ref_ops = brute_sat(c)
        lane_results = [run_raw(c), run_obdd(c), run_factor(c), run_orbit(c), run_c2g(c)]
        for lane in lane_results:
            lane["verification_ops"] = lane.get("verification_ops", 0) + verify_completed_lane(c, lane, sat)
            # Do not serialize witness twice in the public compact result.
            lane.pop("witness", None)
        covered = [
            lane["lane"]
            for lane in lane_results
            if lane["lane"] in PRIMARY_LANES and lane["status"] == "PASS_EXACT_CLOSED"
        ]
        out_controls.append({
            "name": c.name,
            "kind": c.kind,
            "input_bytes": c.input_bytes,
            "root_count": len(c.root_vars),
            "reference_sat": sat,
            "reference_classification_ops": ref_ops,
            "primary_coverage": covered,
            "representation_coverage_hole_under_v0_caps": not bool(covered),
            "lanes": lane_results,
        })

    result = {
        "artifact_id": "PF5-BOUNDARY-COVERAGE-MATRIX-V0",
        "protocol": "PF5_BOUNDARY_COVERAGE_MATRIX_V0.md",
        "claim_ceiling": "P_VS_NP = OPEN",
        "question": "proof-carrying representation compactness + direct closure under repeated existential projection with charged cost",
        "caps": CAPS,
        "primary_lanes": PRIMARY_LANES,
        "sidecar_lanes": ["C2G_LAMINAR"],
        "controls": out_controls,
        "portfolio": {
            "all_frozen_controls_have_primary_representation_coverage": all(
                not c["representation_coverage_hole_under_v0_caps"] for c in out_controls
            ),
            "universal_polynomial_coverage": "OPEN",
            "global_progress_amortization": "OPEN",
            "controller_switching_cost": "OPEN",
            "p_vs_np": "OPEN",
        },
    }
    result["result_sha256"] = sha256(canon_json(result).encode()).hexdigest()
    return result


def print_summary(result: Dict) -> None:
    print("PF5_BOUNDARY_COVERAGE_MATRIX_PROTOCOL = FROZEN")
    for c in result["controls"]:
        print(f"CONTROL {c['name']} reference_sat={c['reference_sat']} input_bytes={c['input_bytes']}")
        for lane in c["lanes"]:
            print(
                "  "
                + lane["lane"]
                + f" status={lane['status']}"
                + f" peak_bytes={lane.get('representation_bytes_peak', 0)}"
                + f" cumulative_bytes={lane.get('cumulative_state_bytes', 0)}"
                + f" build_ops={lane.get('build_ops', 0)}"
                + f" failed_discovery_ops={lane.get('failed_discovery_ops', 0)}"
                + f" project_ops={lane.get('root_projection_ops', 0)}"
                + f" finalize_ops={lane.get('terminal_finalize_ops', 0)}"
                + f" proof_bytes={lane.get('proof_bytes', 0)}"
                + f" witness_bytes={lane.get('witness_bytes', 0)}"
                + (f" cap={lane.get('cap_reason')}" if lane.get("cap_reason") else "")
            )
        print("  PRIMARY_COVERAGE=" + ",".join(c["primary_coverage"]))
        print("  COVERAGE_HOLE=" + str(c["representation_coverage_hole_under_v0_caps"]))
    print(
        "ALL_FROZEN_CONTROLS_PRIMARY_COVERED = "
        + str(result["portfolio"]["all_frozen_controls_have_primary_representation_coverage"])
    )
    print("UNIVERSAL_POLYNOMIAL_COVERAGE = OPEN")
    print("GLOBAL_PROGRESS_AMORTIZATION = OPEN")
    print("C2G_LAMINAR_PRIMARY_BOUNDARY_LANGUAGE = FALSE")
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 = " + result["result_sha256"])


def main(argv: Sequence[str]) -> int:
    result = matrix_run()
    print_summary(result)
    if "--json-out" in argv:
        i = list(argv).index("--json-out")
        path = argv[i + 1]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
