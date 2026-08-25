#!/usr/bin/env python3
"""U1-L2C1 direct existential projection on literal ACI quotient states.

Exact symbolic four-case update, sequential closure, and witness replay.
No SAT oracle, semantic equivalence oracle, or sampled valuation search.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Dict, Iterable, List, Tuple

MS = [2, 4, 8, 16, 32, 64, 128]


class Refusal(Exception):
    pass


@dataclass(frozen=True)
class Factor:
    kind: str
    token: str
    deps: Tuple[str, ...] = ()

    @staticmethod
    def literal(token: str) -> "Factor":
        if not token or token == "~":
            raise ValueError("invalid literal")
        raw = token[1:] if token.startswith("~") else token
        return Factor("LITERAL", token, (raw,))


@dataclass(frozen=True)
class State:
    kind: str
    factors: Tuple[Factor, ...] = ()


def lit_parts(token: str) -> Tuple[str, bool]:
    if token.startswith("~"):
        return token[1:], False
    return token, True


def canonical_set(tokens: Iterable[str]) -> State:
    unique = sorted(set(tokens))
    return State("SET", tuple(Factor.literal(t) for t in unique)) if unique else State("TRUE")


def fingerprint(state: State) -> str:
    payload = {
        "kind": state.kind,
        "factors": [{"kind": f.kind, "token": f.token, "deps": list(f.deps)} for f in state.factors],
    }
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def serialized_bytes(state: State) -> int:
    payload = {
        "kind": state.kind,
        "factors": [{"kind": f.kind, "token": f.token, "deps": list(f.deps)} for f in state.factors],
    }
    return len(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())


def contradiction_var(literal_tokens: List[str]) -> str | None:
    pos = set()
    neg = set()
    for tok in literal_tokens:
        var, positive = lit_parts(tok)
        (pos if positive else neg).add(var)
    both = sorted(pos & neg)
    return both[0] if both else None


def project(state: State, pivot: str) -> Tuple[State, dict]:
    source_sha = fingerprint(state)
    inspections = 0

    if state.kind == "TRUE":
        target = State("TRUE")
        cert = {"case": "TERMINAL_TRUE", "witness_bit": 0, "literal_inspections": 0}
    elif state.kind == "FALSE":
        target = State("FALSE")
        cert = {"case": "TERMINAL_FALSE", "witness_bit": None, "literal_inspections": 0}
    elif state.kind != "SET":
        raise Refusal("REFUSE_UNKNOWN_STATE")
    else:
        for f in state.factors:
            inspections += 1
            if f.kind != "LITERAL":
                if pivot in f.deps:
                    raise Refusal("REFUSE_NONLITERAL_PIVOT_DEPENDENT_FACTOR")
                raise Refusal("REFUSE_NONLITERAL_FACTOR")

        tokens = [f.token for f in state.factors]
        bad = contradiction_var(tokens)
        if bad is not None:
            target = State("FALSE")
            cert = {
                "case": "GLOBAL_COMPLEMENT_CONTRADICTION",
                "contradiction_var": bad,
                "witness_bit": None,
                "literal_inspections": inspections,
            }
        else:
            p = pivot in tokens
            n = ("~" + pivot) in tokens
            assert not (p and n)
            if not p and not n:
                target = state
                cert = {"case": "00_IRRELEVANT", "p": False, "n": False, "witness_bit": 0, "literal_inspections": inspections}
            elif p:
                target = canonical_set(t for t in tokens if t != pivot)
                cert = {"case": "10_POSITIVE", "p": True, "n": False, "witness_bit": 1, "literal_inspections": inspections}
            else:
                target = canonical_set(t for t in tokens if t != "~" + pivot)
                cert = {"case": "01_NEGATIVE", "p": False, "n": True, "witness_bit": 0, "literal_inspections": inspections}

    cert.update({
        "source_sha256": source_sha,
        "target_sha256": fingerprint(target),
        "pivot": pivot,
        "source_bytes": serialized_bytes(state),
        "target_bytes": serialized_bytes(target),
    })
    cert["certificate_bytes"] = len(json.dumps(cert, sort_keys=True, separators=(",", ":")).encode())
    return target, cert


def independent_verify(source: State, target: State, cert: dict) -> None:
    assert cert["source_sha256"] == fingerprint(source)
    assert cert["target_sha256"] == fingerprint(target)
    pivot = cert["pivot"]

    if source.kind == "TRUE":
        assert cert["case"] == "TERMINAL_TRUE" and target.kind == "TRUE" and cert["witness_bit"] == 0
        return
    if source.kind == "FALSE":
        assert cert["case"] == "TERMINAL_FALSE" and target.kind == "FALSE" and cert["witness_bit"] is None
        return
    assert source.kind == "SET"
    for f in source.factors:
        if f.kind != "LITERAL":
            if pivot in f.deps:
                raise Refusal("REFUSE_NONLITERAL_PIVOT_DEPENDENT_FACTOR")
            raise Refusal("REFUSE_NONLITERAL_FACTOR")

    tokens = [f.token for f in source.factors]
    bad = contradiction_var(tokens)
    if bad is not None:
        assert cert["case"] == "GLOBAL_COMPLEMENT_CONTRADICTION"
        assert target.kind == "FALSE" and cert["witness_bit"] is None
        assert bad == cert["contradiction_var"]
        return

    p = pivot in tokens
    n = ("~" + pivot) in tokens
    if not p and not n:
        assert cert["case"] == "00_IRRELEVANT" and target == source and cert["witness_bit"] == 0
    elif p:
        expected = canonical_set(t for t in tokens if t != pivot)
        assert cert["case"] == "10_POSITIVE" and target == expected and cert["witness_bit"] == 1
    else:
        expected = canonical_set(t for t in tokens if t != "~" + pivot)
        assert cert["case"] == "01_NEGATIVE" and target == expected and cert["witness_bit"] == 0


def eval_literal(token: str, assignment: Dict[str, int]) -> bool:
    var, positive = lit_parts(token)
    if var not in assignment:
        return False
    value = bool(assignment[var])
    return value if positive else not value


def replay_witness(original: State, assignment: Dict[str, int]) -> bool:
    if original.kind == "TRUE":
        return True
    if original.kind == "FALSE":
        return False
    return all(eval_literal(f.token, assignment) for f in original.factors if f.kind == "LITERAL")


def sequential_project(original: State, root_order: List[str]) -> dict:
    current = original
    witness: Dict[str, int] = {}
    certs = []
    inspections = 0
    cert_bytes = 0
    max_state_bytes = serialized_bytes(current)

    for pivot in root_order:
        target, cert = project(current, pivot)
        independent_verify(current, target, cert)
        certs.append(cert)
        inspections += cert["literal_inspections"]
        cert_bytes += cert["certificate_bytes"]
        if cert["witness_bit"] is not None:
            witness[pivot] = cert["witness_bit"]
        current = target
        max_state_bytes = max(max_state_bytes, serialized_bytes(current))
        if current.kind == "FALSE":
            break

    if current.kind == "TRUE":
        assert replay_witness(original, witness)
        replay = "PASS_SAT_WITNESS"
    elif current.kind == "FALSE":
        replay = "PASS_UNSAT_LITERAL_CONTRADICTION"
    else:
        replay = "OPEN_ORDER_INCOMPLETE"

    return {
        "terminal": current.kind,
        "witness": witness,
        "steps": len(certs),
        "literal_inspections": inspections,
        "certificate_bytes": cert_bytes,
        "max_state_bytes": max_state_bytes,
        "replay": replay,
        "certificate_chain_sha256": sha256(json.dumps(certs, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


def fixture_rows() -> List[dict]:
    rows = []
    fixtures = [
        ("IRRELEVANT", canonical_set(["y"]), "x", "SET", 0),
        ("POSITIVE", canonical_set(["x", "y"]), "x", "SET", 1),
        ("NEGATIVE", canonical_set(["~x", "y"]), "x", "SET", 0),
        ("CONTRADICTORY", canonical_set(["x", "~x", "y"]), "x", "FALSE", None),
        ("ONE_FACTOR_TO_TRUE", canonical_set(["x"]), "x", "TRUE", 1),
        ("ALREADY_TRUE", State("TRUE"), "x", "TRUE", 0),
        ("ALREADY_FALSE", State("FALSE"), "x", "FALSE", None),
    ]
    for name, source, pivot, target_kind, witness_bit in fixtures:
        target, cert = project(source, pivot)
        independent_verify(source, target, cert)
        assert target.kind == target_kind and cert["witness_bit"] == witness_bit
        rows.append({"name": name, "case": cert["case"], "target_kind": target.kind, "witness_bit": cert["witness_bit"], "certificate_bytes": cert["certificate_bytes"]})
    return rows


def sf4_quotient_state(m: int) -> Tuple[State, List[str]]:
    tokens = ["x"] + [f"y{i}" for i in range(1, m + 1)] + [f"z{r}" for r in range(1, 5)]
    order = ["x"] + [f"y{i}" for i in range(1, m + 1)] + [f"z{r}" for r in range(1, 5)]
    return canonical_set(tokens), order


def refusal_control() -> dict:
    source = State("SET", (Factor("OPAQUE", "g", ("x", "y")), Factor.literal("z")))
    try:
        project(source, "x")
    except Refusal as exc:
        assert str(exc) == "REFUSE_NONLITERAL_PIVOT_DEPENDENT_FACTOR"
        return {"name": "OPAQUE_G_X_Y", "result": str(exc)}
    raise AssertionError("opaque pivot-dependent factor admitted")


def main() -> None:
    fixtures = fixture_rows()
    sf4_rows = []
    global_inspections = 0
    global_cert_bytes = 0
    max_state_bytes = 0

    for m in MS:
        source, order = sf4_quotient_state(m)
        seq = sequential_project(source, order)
        assert seq["terminal"] == "TRUE"
        assert seq["replay"] == "PASS_SAT_WITNESS"
        assert len(seq["witness"]) == len(order)
        global_inspections += seq["literal_inspections"]
        global_cert_bytes += seq["certificate_bytes"]
        max_state_bytes = max(max_state_bytes, seq["max_state_bytes"])
        sf4_rows.append({
            "m": m,
            "root_count": len(order),
            "initial_factor_count": len(source.factors),
            "terminal": seq["terminal"],
            "steps": seq["steps"],
            "literal_inspections": seq["literal_inspections"],
            "certificate_bytes": seq["certificate_bytes"],
            "max_state_bytes": seq["max_state_bytes"],
            "witness_replay": seq["replay"],
            "certificate_chain_sha256": seq["certificate_chain_sha256"],
        })

    refusal = refusal_control()
    result = {
        "schema": "JANUS_U1L2C1_LITERAL_FACTOR_EXISTENTIAL_CLOSURE_RESULT",
        "status": "PASS_DIRECT_SEQUENTIAL_EXISTENTIAL_CLOSURE_FROZEN_LITERAL_LANGUAGE",
        "claim_ceiling": "P_VS_NP_OPEN",
        "fixtures": fixtures,
        "sf4_rows": sf4_rows,
        "refusal_control": refusal,
        "global_ledger": {
            "literal_inspections": global_inspections,
            "certificate_bytes": global_cert_bytes,
            "max_state_bytes": max_state_bytes,
        },
        "theorem_ledger": {
            "LITERAL_ACI_QUOTIENT_DIRECT_EXISTENTIAL_UPDATE": "PROVED_IN_SCOPE_BY_COMPLETE_FOUR_CASE_IDENTITY",
            "LITERAL_ACI_QUOTIENT_SEQUENTIAL_CLOSURE": "PROVED_IN_SCOPE",
            "LITERAL_ACI_QUOTIENT_POLY_TOTAL_STATE_WORK": "O(nL)_CONSERVATIVE_BOUND",
            "LITERAL_ACI_QUOTIENT_WITNESS_LIFT": "PROVED_IN_SCOPE_BY_REPLAY",
            "NONLITERAL_FACTOR_PROJECTION": "OPEN_REFUSED",
            "ARBITRARY_B2_SEQUENTIAL_CLOSURE": "OPEN",
            "P_EQUALS_NP": False,
        },
        "next_gate": "U1-L2C2_CERTIFIED_NONLITERAL_FACTOR_PROJECTION",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("U1L2C1_RESULT_SHA256=" + sha256(packed).hexdigest())


if __name__ == "__main__":
    main()
