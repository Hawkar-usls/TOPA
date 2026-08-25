#!/usr/bin/env python3
"""U1-L2C2K KEYMASTER exact method algebra.

This provider validates an exact dispatcher/pruner for already-certified proof
operators.  It does NOT prove a polynomial global frontier bound and does NOT
solve P vs NP.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

PROTOCOL_COMMIT = "ef7a4469261f63ed2ff861142fb6791ac47d32dc"

COST_FIELDS = (
    "state", "proof", "discovery", "failed_search", "build",
    "projection", "join", "verify", "witness",
)

FORBIDDEN_AUTHORITIES = {
    "RANDOM", "SCORE", "EMA", "TRACE", "SHORTLIST", "TOP_K",
    "ENTROPY_THRESHOLD", "RESONANCE_THRESHOLD", "LLM_JUDGEMENT",
    "NEURAL_CONFIDENCE", "FINITE_SUCCESS_SELECTION",
}


@dataclass(frozen=True)
class Cost:
    values: tuple[int, ...]

    def __post_init__(self):
        if len(self.values) != len(COST_FIELDS):
            raise ValueError("bad cost dimension")
        if any(v < 0 for v in self.values):
            raise ValueError("negative cost")

    def add(self, other: "Cost") -> "Cost":
        return Cost(tuple(a + b for a, b in zip(self.values, other.values)))

    def dominates(self, other: "Cost") -> bool:
        le = all(a <= b for a, b in zip(self.values, other.values))
        strict = any(a < b for a, b in zip(self.values, other.values))
        return le and strict

    def as_dict(self) -> dict:
        return dict(zip(COST_FIELDS, self.values))


ZERO = Cost((0,) * len(COST_FIELDS))


@dataclass(frozen=True)
class State:
    language: str
    payload: tuple
    obligations: tuple[str, ...]

    def canonical_payload(self) -> dict:
        return {
            "language": self.language,
            "payload": self.payload,
            "obligations": tuple(sorted(self.obligations)),
        }

    def fingerprint(self) -> str:
        packed = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":")
        ).encode()
        return sha256(packed).hexdigest()


@dataclass(frozen=True)
class Operator:
    operator_id: str
    source_language: str
    codomain_language: str
    domain_predicate: str
    theorem_id: str
    certificate_schema: str
    complexity_bound: str
    witness_lift: str
    authority: str = "EXACT_PREDICATE_ONLY"
    forbidden_dependencies: tuple[str, ...] = ()

    def schema_complete(self) -> bool:
        required = (
            self.operator_id,
            self.source_language,
            self.codomain_language,
            self.domain_predicate,
            self.theorem_id,
            self.certificate_schema,
            self.complexity_bound,
            self.witness_lift,
        )
        return all(bool(x) for x in required)

    def admitted(self) -> tuple[bool, str]:
        if not self.schema_complete():
            return False, "REFUSE_INCOMPLETE_OPERATOR_SCHEMA"
        if self.authority != "EXACT_PREDICATE_ONLY":
            return False, "REFUSE_NONEXACT_SELECTION_AUTHORITY"
        bad = sorted(set(self.forbidden_dependencies) & FORBIDDEN_AUTHORITIES)
        if bad:
            return False, "REFUSE_FORBIDDEN_DEPENDENCY:" + ",".join(bad)
        return True, "ADMIT_EXACT_OPERATOR"


@dataclass(frozen=True)
class Path:
    state: State
    cost: Cost
    proof_chain: tuple[str, ...]

    def chain_digest(self) -> str:
        return sha256("|".join(self.proof_chain).encode()).hexdigest()


ACTIVE_CATALOG = (
    Operator("PURE_LITERAL_EXISTS", "CNF", "CNF", "HAS_PURE_LITERAL", "PURE_LITERAL_EXISTENTIAL_PROJECTION", "PURE_LITERAL_CERT", "POLY_EXPLICIT_CNF_SCAN", "PURE_LITERAL_WITNESS"),
    Operator("TAUTOLOGICAL_RESOLVENT_EXISTS", "CNF", "CNF", "ALL_CROSS_RESOLVENTS_TAUTOLOGICAL", "TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION", "TR_PAIR_WITNESS_CERT", "POLY_EXPLICIT_PARENT_PAIR_SCAN", "TR_WITNESS"),
    Operator("SINGLE_NTR_EXISTS", "CNF", "CNF", "ONE_UNIQUE_NONTAUTOLOGICAL_RESOLVENT", "SINGLE_NONTAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION", "SINGLE_RESOLVENT_CERT", "POLY_EXPLICIT_PARENT_PAIR_SCAN", "DP_WITNESS"),
    Operator("COMPLEMENTARY_TWIN", "CNF", "CNF", "HAS_COMPLEMENTARY_TWIN", "COMPLEMENTARY_TWIN_CONTRACTION", "TWIN_CERT", "POLY_CLAUSE_SCAN", "IDENTITY_WITNESS"),
    Operator("CLAUSE_SUBSUMPTION", "CNF", "CNF", "HAS_STRICT_SUBSUMPTION", "CLAUSE_SUBSUMPTION", "SUBSUMPTION_CERT", "POLY_CLAUSE_PAIR_SCAN", "IDENTITY_WITNESS"),
    Operator("SELF_SUBSUMING_RESOLUTION", "CNF", "CNF", "HAS_SSR_PAIR", "SELF_SUBSUMING_RESOLUTION", "SSR_CERT", "POLY_CLAUSE_PAIR_SCAN", "IDENTITY_WITNESS"),
    Operator("COMPONENT_PRODUCT", "CNF", "COMPONENT_PRODUCT", "INCIDENCE_DISCONNECTED", "COMPONENT_PRODUCT", "COMPONENT_CERT", "POLY_INCIDENCE_TRAVERSAL", "COMPONENT_WITNESS_UNION"),
    Operator("TWO_SAT_SCC", "TWO_SAT", "TERMINAL", "MAX_CLAUSE_WIDTH_LE_2", "TWO_SAT_SCC_CERTIFICATE", "SCC_PATH_OR_MODEL_CERT", "POLY_IMPLICATION_GRAPH", "TWO_SAT_WITNESS"),
    Operator("AFFINE_GF2_JOIN", "AFFINE_BOUNDARY", "AFFINE_BOUNDARY", "AFFINE_RREF_DOMAIN", "AFFINE_GF2_BOUNDARY_JOIN", "RREF_CERT", "POLY_GF2_ELIMINATION", "AFFINE_WITNESS"),
    Operator("ACI_SHARED_FACTOR", "PURE_AND_DAG", "LITERAL_ACI", "PURE_AND_CONE", "PROOF_CARRYING_ACI_SHARED_FACTOR_QUOTIENT_PURE_AND", "ACI_FACTOR_CERT", "POLY_DAG_TRAVERSAL", "IDENTITY_WITNESS"),
    Operator("LITERAL_ACI_EXISTS", "LITERAL_ACI", "LITERAL_ACI", "PIVOT_IS_LITERAL_FACTOR", "LITERAL_ACI_QUOTIENT_DIRECT_EXISTENTIAL_UPDATE", "LITERAL_FACTOR_CERT", "POLY_FACTOR_SCAN", "LITERAL_FACTOR_WITNESS"),
    Operator("SYMMETRIC_WEIGHT_EXISTS", "SYMMETRIC_WEIGHT", "SYMMETRIC_WEIGHT", "FACTOR_DEPENDS_ONLY_ON_HAMMING_WEIGHT", "SYMMETRIC_WEIGHT_EXISTS_UPDATE_EXACT", "WEIGHT_SET_CERT", "O_M_PER_PROJECTION_O_M2_TOTAL", "HAMMING_WEIGHT_WITNESS"),
)

HISTORICAL_TRIAGE = {
    "SLIME_SEMANTIC_PRESSURE": "PRUNED_FROM_PROOF_PATH",
    "SLIME_EXACT_INCIDENCE_FINGERPRINT_FEATURES": "DONOR_ONLY",
    "WALKSAT": "PRUNED_FROM_PROOF_PATH",
    "PSO_SWARM": "PRUNED_FROM_PROOF_PATH",
    "PHYSARUM_RANDOM_WALK_THRESHOLD": "PRUNED_FROM_PROOF_PATH",
    "PHYSARUM_EXACT_FLOW_EQUATIONS": "DONOR_ONLY_PENDING_SAT_MORPHISM",
    "HIVE_LLM_SCORE_SYNTHESIS": "PRUNED_FROM_PROOF_PATH",
    "LEGACY_KEYMASTER_THRESHOLD_CONTROL": "PRUNED_FROM_PROOF_PATH",
    "ODONTO_M2R_EMA_CHAMPION_MUTATION": "PRUNED_FROM_PROOF_PATH",
    "RAMANUJAN_THETA_DIRECTOR_STEERING": "PRUNED_FROM_PROOF_PATH",
    "RAMANUJAN_THETA_EXACT_SUM_PRODUCT_RECURRENCE": "DONOR_ONLY",
    "MOD_THETA_PRIME": "PRUNED_FROM_PROOF_PATH",
    "HEPHAESTUS_ENTROPY_PURITY_SELECTION": "PRUNED_FROM_PROOF_PATH",
    "HEPHAESTUS_SYNTACTIC_HASH_REVISIT": "ALGEBRAIZED_ACTIVE",
    "KEYMASTER_STATE_GUARD_TRANSITION_MEMORY_ARCHITECTURE": "ALGEBRAIZED_ACTIVE",
    "AXIOM_BRIDGE": "GOVERNANCE_ONLY",
}


def validate_catalog(catalog: Iterable[Operator]) -> dict:
    admitted = []
    for op in catalog:
        ok, reason = op.admitted()
        assert ok, (op.operator_id, reason)
        admitted.append(op.operator_id)
    assert len(admitted) == len(set(admitted))
    return {"active_exact_operator_count": len(admitted), "active_operator_ids": admitted}


def typecheck_compose(left: Operator, right: Operator) -> dict:
    # right o left
    if left.codomain_language != right.source_language:
        return {"admitted": False, "reason": "REFUSE_LANGUAGE_MISMATCH"}
    ok_l, _ = left.admitted()
    ok_r, _ = right.admitted()
    if not (ok_l and ok_r):
        return {"admitted": False, "reason": "REFUSE_NONEXACT_COMPONENT"}
    return {
        "admitted": True,
        "source_language": left.source_language,
        "codomain_language": right.codomain_language,
        "certificate_rule": "CONCATENATE_CERTIFICATES",
        "cost_rule": "COMPONENTWISE_ADD",
        "witness_rule": "REVERSE_COMPOSE_WITNESS_LIFTS",
    }


def same_state(a: Path, b: Path) -> bool:
    return a.state.fingerprint() == b.state.fingerprint()


def exact_frontier_reduce(paths: Iterable[Path]) -> tuple[list[Path], list[dict]]:
    """Only identical canonical states may be cost-pruned in this provider."""
    groups: dict[str, list[Path]] = {}
    for p in paths:
        groups.setdefault(p.state.fingerprint(), []).append(p)

    kept: list[Path] = []
    receipts: list[dict] = []
    for fp in sorted(groups):
        group = sorted(groups[fp], key=lambda p: (p.cost.values, p.chain_digest()))
        local: list[Path] = []
        for candidate in group:
            dominated_by = next((k for k in local if k.cost.dominates(candidate.cost)), None)
            equal = next((k for k in local if k.cost.values == candidate.cost.values), None)
            if dominated_by is not None:
                receipts.append({
                    "state_sha256": fp,
                    "pruned_chain": candidate.chain_digest(),
                    "kept_chain": dominated_by.chain_digest(),
                    "reason": "IDENTICAL_STATE_COMPONENTWISE_COST_DOMINANCE",
                })
                continue
            if equal is not None:
                # Exact duplicate cost/state: deterministic one-representative serialization.
                receipts.append({
                    "state_sha256": fp,
                    "pruned_chain": candidate.chain_digest(),
                    "kept_chain": equal.chain_digest(),
                    "reason": "IDENTICAL_STATE_IDENTICAL_COST_DEDUP",
                })
                continue
            # Candidate may dominate earlier local members; remove only same-state members.
            survivors = []
            for old in local:
                if candidate.cost.dominates(old.cost):
                    receipts.append({
                        "state_sha256": fp,
                        "pruned_chain": old.chain_digest(),
                        "kept_chain": candidate.chain_digest(),
                        "reason": "IDENTICAL_STATE_COMPONENTWISE_COST_DOMINANCE",
                    })
                else:
                    survivors.append(old)
            survivors.append(candidate)
            local = survivors
        kept.extend(local)

    kept.sort(key=lambda p: (p.state.fingerprint(), p.cost.values, p.chain_digest()))
    return kept, receipts


def tests() -> dict:
    catalog = validate_catalog(ACTIVE_CATALOG)

    # Inject forbidden authority: must fail closed.
    injected = Operator(
        "BAD_TRACE_ROUTER", "CNF", "CNF", "ANY", "NONE", "NONE", "NONE", "NONE",
        authority="HEURISTIC_ROUTER", forbidden_dependencies=("TRACE", "TOP_K")
    )
    ok, injected_reason = injected.admitted()
    assert not ok and injected_reason == "REFUSE_NONEXACT_SELECTION_AUTHORITY"

    by_id = {op.operator_id: op for op in ACTIVE_CATALOG}
    c1 = typecheck_compose(by_id["ACI_SHARED_FACTOR"], by_id["LITERAL_ACI_EXISTS"])
    assert c1["admitted"] is True
    c2 = typecheck_compose(by_id["SYMMETRIC_WEIGHT_EXISTS"], by_id["SYMMETRIC_WEIGHT_EXISTS"])
    assert c2["admitted"] is True
    bad_comp = typecheck_compose(by_id["ACI_SHARED_FACTOR"], by_id["TWO_SAT_SCC"])
    assert bad_comp == {"admitted": False, "reason": "REFUSE_LANGUAGE_MISMATCH"}

    s = State("CNF", ("residual-A",), ("P5", "P6"))
    cheap = Path(s, Cost((10, 4, 3, 0, 2, 1, 0, 2, 1)), ("A", "B"))
    expensive = Path(s, Cost((12, 5, 3, 0, 2, 1, 0, 2, 1)), ("A", "C"))
    incomparable = Path(s, Cost((9, 7, 3, 0, 2, 1, 0, 2, 1)), ("A", "D"))
    exact_dup = Path(s, cheap.cost, ("X", "Y"))
    kept, receipts = exact_frontier_reduce([expensive, incomparable, cheap, exact_dup])
    assert len(kept) == 2
    assert sorted(p.cost.values for p in kept) == sorted([cheap.cost.values, incomparable.cost.values])
    assert any(r["reason"] == "IDENTICAL_STATE_COMPONENTWISE_COST_DOMINANCE" for r in receipts)
    assert any(r["reason"] == "IDENTICAL_STATE_IDENTICAL_COST_DEDUP" for r in receipts)

    # Different exact state may never be pruned merely because its cost is larger.
    s2 = State("CNF", ("residual-B",), ("P5", "P6"))
    p2 = Path(s2, Cost((999, 999, 999, 0, 0, 0, 0, 0, 0)), ("OTHER",))
    kept2, _ = exact_frontier_reduce([cheap, p2])
    assert len(kept2) == 2

    # Frontier explosion control: report count; never truncate.
    explosion_inputs = [
        Path(State("CNF", (f"unique-{i}",), ("P5",)), ZERO, (f"P{i}",))
        for i in range(64)
    ]
    explosion_kept, _ = exact_frontier_reduce(explosion_inputs)
    assert len(explosion_kept) == 64

    active_bad_dependencies = {
        op.operator_id: sorted(set(op.forbidden_dependencies) & FORBIDDEN_AUTHORITIES)
        for op in ACTIVE_CATALOG
        if set(op.forbidden_dependencies) & FORBIDDEN_AUTHORITIES
    }
    assert active_bad_dependencies == {}

    return {
        "catalog": catalog,
        "heuristic_injection_control": {
            "admitted": ok,
            "reason": injected_reason,
        },
        "composition_controls": {
            "ACI_TO_LITERAL_EXISTS": c1,
            "SYMMETRIC_SELF_COMPOSITION": c2,
            "LANGUAGE_MISMATCH": bad_comp,
        },
        "frontier_controls": {
            "same_state_input_paths": 4,
            "same_state_kept_non_dominated": len(kept),
            "prune_receipts": receipts,
            "different_state_paths_preserved": len(kept2),
            "frontier_explosion_input": 64,
            "frontier_explosion_preserved": len(explosion_kept),
            "silent_top_k_truncation": False,
        },
        "historical_triage": HISTORICAL_TRIAGE,
        "theorem_ledger": {
            "EXACT_OPERATOR_SCHEMA_FAIL_CLOSED": True,
            "EXACT_TYPE_CHECKED_COMPOSITION": True,
            "WITNESS_LIFTS_REVERSE_COMPOSE_BY_CONTRACT": True,
            "COSTS_COMPONENTWISE_ADD_BY_CONTRACT": True,
            "IDENTICAL_STATE_DOMINANCE_PRUNING_SAFE": True,
            "INCOMPARABLE_EXACT_PATHS_PRESERVED": True,
            "HEURISTIC_AUTHORITY_IN_ACTIVE_PROOF_PATH": False,
            "KEYMASTER_FRONTIER_POLY_BOUND": "OPEN_NOT_CLAIMED",
            "ARBITRARY_FACTOR_POLY_TRANSITION_QUOTIENT": "OPEN_NOT_CLAIMED",
            "P_EQUALS_NP": False,
        },
        "next_gates": [
            "U1-L2C2C_DISCOVER_PROOF_CARRYING_SYMMETRY_OR_OTHER_POLY_TRANSITION_QUOTIENT_FROM_ARBITRARY_FACTOR",
            "KEYMASTER_FRONTIER_POLY_BOUND",
        ],
    }


def main() -> None:
    payload = {
        "schema": "JANUS_U1L2C2K_KEYMASTER_EXACT_ALGEBRA_RESULT",
        "status": "PASS_EXACT_METHOD_ALGEBRA" ,
        "frozen_protocol_commit": PROTOCOL_COMMIT,
        "claim_ceiling": "P_VS_NP_OPEN",
        **tests(),
    }
    packed = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("U1L2C2K_RESULT_SHA256=" + sha256(packed).hexdigest())


if __name__ == "__main__":
    main()
