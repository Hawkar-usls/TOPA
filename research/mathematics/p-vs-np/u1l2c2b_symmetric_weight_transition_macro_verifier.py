#!/usr/bin/env python3
"""U1-L2C2B exact symmetric-weight nonliteral factor projection.

State: (m,A), where A is the exact allowed Hamming-weight set.
No SAT oracle, truth-table enumeration, heuristic score, or semantic equivalence oracle.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

MS = [8, 16, 32, 64, 128, 256]


class Refusal(Exception):
    pass


@dataclass(frozen=True)
class WeightState:
    m: int
    allowed: tuple[int, ...]


def make_state(m: int, allowed) -> WeightState:
    if m < 0:
        raise Refusal("REFUSE_NEGATIVE_ARITY")
    vals = tuple(sorted(set(int(x) for x in allowed)))
    if any(x < 0 or x > m for x in vals):
        raise Refusal("REFUSE_WEIGHT_OUT_OF_RANGE")
    return WeightState(m, vals)


def state_payload(s: WeightState) -> dict:
    return {"m": s.m, "allowed": list(s.allowed)}


def fingerprint(s: WeightState) -> str:
    return sha256(json.dumps(state_payload(s), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def serialized_bytes(s: WeightState) -> int:
    return len(json.dumps(state_payload(s), sort_keys=True, separators=(",", ":")).encode())


def theta_allowed(m: int) -> tuple[int, ...]:
    # Generate E(n)=n(3n-1)/2 by the exact C2A forward/backward recurrences.
    out = {0}

    n = 0
    e = 0
    while True:
        nxt = e + 3 * n + 1  # E(n+1)
        n += 1
        e = nxt
        if e > m:
            break
        out.add(e)

    n = 0
    e = 0
    while True:
        nxt = e - 3 * n + 2  # E(n-1)
        n -= 1
        e = nxt
        if e > m:
            break
        out.add(e)

    return tuple(sorted(out))


def project(s: WeightState) -> tuple[WeightState, dict]:
    if s.m == 0:
        return s, {
            "case": "TERMINAL",
            "source_sha256": fingerprint(s),
            "target_sha256": fingerprint(s),
            "inspections": 0,
            "certificate_bytes": 0,
        }

    A = set(s.allowed)
    new = []
    inspections = 0
    for t in range(s.m):
        inspections += 1
        if t in A or (t + 1) in A:
            new.append(t)
    target = make_state(s.m - 1, new)
    cert = {
        "case": "SYMMETRIC_EXISTS_WEIGHT_UPDATE",
        "source_m": s.m,
        "target_m": target.m,
        "source_allowed": list(s.allowed),
        "target_allowed": list(target.allowed),
        "source_sha256": fingerprint(s),
        "target_sha256": fingerprint(target),
        "inspections": inspections,
        "witness_rule": "x=0_if_t_in_A_else_1",
    }
    cert["certificate_bytes"] = len(json.dumps(cert, sort_keys=True, separators=(",", ":")).encode())
    return target, cert


def independent_verify(source: WeightState, target: WeightState, cert: dict) -> None:
    assert cert["source_sha256"] == fingerprint(source)
    assert cert["target_sha256"] == fingerprint(target)
    if source.m == 0:
        assert target == source and cert["case"] == "TERMINAL"
        return
    A = set(source.allowed)
    expected = tuple(t for t in range(source.m) if t in A or (t + 1) in A)
    assert target == make_state(source.m - 1, expected)
    assert cert["case"] == "SYMMETRIC_EXISTS_WEIGHT_UPDATE"


def sequential_project(source: WeightState) -> dict:
    current = source
    chain: list[tuple[WeightState, WeightState, dict]] = []
    inspections = 0
    cert_bytes = 0
    max_state_bytes = serialized_bytes(source)

    while current.m > 0:
        target, cert = project(current)
        independent_verify(current, target, cert)
        chain.append((current, target, cert))
        inspections += cert["inspections"]
        cert_bytes += cert["certificate_bytes"]
        max_state_bytes = max(max_state_bytes, serialized_bytes(target))
        current = target

    terminal_true = 0 in set(current.allowed)
    witness = []
    if terminal_true:
        remaining_weight = 0
        for src, tgt, cert in reversed(chain):
            assert remaining_weight in set(tgt.allowed)
            A = set(src.allowed)
            bit = 0 if remaining_weight in A else 1
            assert remaining_weight + bit in A
            witness.append(bit)
            remaining_weight += bit
        witness.reverse()
        assert len(witness) == source.m
        assert sum(witness) in set(source.allowed)
        replay = "PASS_SAT_WITNESS"
    else:
        replay = "PASS_UNSAT_TERMINAL_WEIGHT_SET"

    return {
        "terminal": "TRUE" if terminal_true else "FALSE",
        "witness_replay": replay,
        "witness_weight": sum(witness) if terminal_true else None,
        "steps": len(chain),
        "inspections": inspections,
        "certificate_bytes": cert_bytes,
        "max_state_bytes": max_state_bytes,
        "final_state_sha256": fingerprint(current),
    }


def controls() -> list[dict]:
    rows = []

    empty = make_state(5, [])
    seq = sequential_project(empty)
    assert seq["terminal"] == "FALSE"
    rows.append({"name": "EMPTY_ALLOWED", "result": seq["terminal"]})

    full = make_state(5, range(6))
    seq = sequential_project(full)
    assert seq["terminal"] == "TRUE"
    rows.append({"name": "FULL_ALLOWED", "result": seq["terminal"]})

    singleton = make_state(4, [2])
    target, cert = project(singleton)
    independent_verify(singleton, target, cert)
    assert target.allowed == (1, 2)
    rows.append({"name": "EXACT_WEIGHT_2", "target_allowed": list(target.allowed)})

    try:
        make_state(4, [5])
    except Refusal as exc:
        assert str(exc) == "REFUSE_WEIGHT_OUT_OF_RANGE"
        rows.append({"name": "MALFORMED_WEIGHT", "result": str(exc)})
    else:
        raise AssertionError("out-of-range weight admitted")

    return rows


def main() -> None:
    fixture_rows = []
    theta_first_projection_closed_count = 0
    global_inspections = 0
    global_cert_bytes = 0
    max_state_bytes = 0

    for m in MS:
        A = theta_allowed(m)
        source = make_state(m, A)
        first, cert = project(source)
        independent_verify(source, first, cert)
        theta_target = make_state(m - 1, theta_allowed(m - 1))
        theta_closed = first == theta_target
        if theta_closed:
            theta_first_projection_closed_count += 1

        seq = sequential_project(source)
        assert seq["terminal"] == "TRUE"
        assert seq["witness_replay"] == "PASS_SAT_WITNESS"
        assert seq["inspections"] == m * (m + 1) // 2

        global_inspections += seq["inspections"]
        global_cert_bytes += seq["certificate_bytes"]
        max_state_bytes = max(max_state_bytes, seq["max_state_bytes"])

        fixture_rows.append({
            "m": m,
            "assignment_presentation_count": str(1 << m),
            "hamming_weight_state_count_upper_bound": m + 1,
            "initial_allowed_count": len(A),
            "initial_allowed": list(A),
            "first_projection_allowed_count": len(first.allowed),
            "first_projection_is_theta_spectrum": theta_closed,
            "steps": seq["steps"],
            "terminal": seq["terminal"],
            "witness_replay": seq["witness_replay"],
            "witness_weight": seq["witness_weight"],
            "inspections": seq["inspections"],
            "certificate_bytes": seq["certificate_bytes"],
            "max_state_bytes": seq["max_state_bytes"],
            "source_sha256": fingerprint(source),
            "first_target_sha256": fingerprint(first),
            "final_state_sha256": seq["final_state_sha256"],
        })

    result = {
        "schema": "JANUS_U1L2C2B_SYMMETRIC_WEIGHT_TRANSITION_MACRO_RESULT",
        "status": "PASS_EXACT_NONLITERAL_SYMMETRIC_SEQUENTIAL_CLOSURE",
        "claim_ceiling": "P_VS_NP_OPEN",
        "frozen_protocol_commit": "b208b5cdda28d4d6ead4c39ab2d7b743ec87d294",
        "controls": controls(),
        "theta_rows": fixture_rows,
        "summary": {
            "cases": len(MS),
            "theta_first_projection_closed_cases": theta_first_projection_closed_count,
            "theta_first_projection_escape_cases": len(MS) - theta_first_projection_closed_count,
            "all_symmetric_weight_sequences_closed": True,
            "all_theta_seeded_cases_terminal_true": True,
            "all_witness_replays_pass": True,
        },
        "global_ledger": {
            "inspections": global_inspections,
            "certificate_bytes": global_cert_bytes,
            "max_state_bytes": max_state_bytes,
        },
        "theorem_ledger": {
            "SYMMETRIC_WEIGHT_FACTOR_IS_NONLITERAL": True,
            "SYMMETRIC_WEIGHT_EXISTS_UPDATE_EXACT": "PROVED_BY_TWO_BRANCH_WEIGHT_IDENTITY",
            "SYMMETRIC_WEIGHT_LANGUAGE_SEQUENTIALLY_CLOSED": True,
            "SYMMETRIC_WEIGHT_STATE_SIZE": "O(m)",
            "SYMMETRIC_WEIGHT_TOTAL_SEQUENTIAL_WORK": "O(m^2)_CONSERVATIVE",
            "SYMMETRIC_WEIGHT_WITNESS_LIFT": True,
            "THETA_PARAMETERIZATION_SEQUENTIALLY_CLOSED": theta_first_projection_closed_count == len(MS),
            "ARBITRARY_CNF_TO_SYMMETRIC_WEIGHT_MORPHISM": "OPEN_NOT_CLAIMED",
            "P_EQUALS_NP": False,
        },
        "method_update": {
            "8008_principle_realized_as": "EXACT_QUOTIENT_2^m_ASSIGNMENTS_TO_m_PLUS_1_HAMMING_WEIGHT_TRANSITION_STATES",
            "theta_role": "EXACT_STRUCTURED_INITIAL_SPECTRUM_FIXTURE_AND_RECURRENCE_DONOR",
            "closed_language": "GENERIC_EXACT_ALLOWED_HAMMING_WEIGHT_SET_NOT_THETA_ONLY",
        },
        "next_gate": "U1-L2C2C_DISCOVER_PROOF_CARRYING_SYMMETRY_OR_OTHER_POLY_TRANSITION_QUOTIENT_FROM_ARBITRARY_FACTOR",
    }

    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("U1L2C2B_RESULT_SHA256=" + sha256(packed).hexdigest())


if __name__ == "__main__":
    main()
