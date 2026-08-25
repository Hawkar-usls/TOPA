#!/usr/bin/env python3
"""JANUS RCTQ-3: typed polarity terminal + deterministic signed-gauge escape.

No heuristic, score, randomization, SAT oracle, truth-table oracle, or optimum
oracle is used.  The escape tests only transition completeness of a frozen
finite exact catalog and does not establish SAT hardness or resolve P vs NP.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROTOCOL_COMMIT = "51b0b44e9808ae69c1aab1c0e6eebcc8106ad82e"
GAUGE_PATTERN = (0, 0, 1, 1, 0)
LADDER = (37, 41, 43, 47)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


km = load_module(
    "rctq3_keymaster14",
    HERE / "u1l2c2k1_keymaster_catalog_extension_verifier.py",
)
r2 = load_module(
    "rctq3_rctq2_helpers",
    HERE / "rctq2_frozen_catalog_escape_verifier.py",
)

POLARITY = km.base.Operator(
    "UNIFORM_POLARITY_CLAUSE_WITNESS",
    "CNF",
    "TERMINAL",
    "ALL_CLAUSES_HAVE_POSITIVE_LITERAL_OR_ALL_CLAUSES_HAVE_NEGATIVE_LITERAL",
    "UNIFORM_POLARITY_CLAUSE_WITNESS_DIRECT_BOOLEAN_SEMANTICS",
    "ONE_REQUIRED_POLARITY_LITERAL_PER_CLAUSE",
    "O_TOTAL_LITERAL_OCCURRENCES_PLUS_VARIABLES",
    "DIRECT_ALL_ONES_OR_ALL_ZERO_WITNESS",
)

EXPECTED15 = tuple(op.operator_id for op in (tuple(km.base.ACTIVE_CATALOG) + (km.NEW, km.SELF, POLARITY)))
assert len(EXPECTED15) == 15


def frozen15():
    catalog = tuple(km.base.ACTIVE_CATALOG) + (km.NEW, km.SELF, POLARITY)
    summary = km.base.validate_catalog(catalog)
    assert summary["active_exact_operator_count"] == 15
    assert tuple(summary["active_operator_ids"]) == EXPECTED15
    return catalog


def gauge_bit(v: int) -> int:
    return GAUGE_PATTERN[(v - 1) % len(GAUGE_PATTERN)]


def gauge_lit(l: int) -> int:
    return -l if gauge_bit(abs(l)) else l


def apply_gauge(F):
    return r2.canonical_cnf(tuple(tuple(gauge_lit(l) for l in c) for c in F))


def gauged_escape_cnf(n: int):
    base = r2.escape_cnf(n)
    G = apply_gauge(base)
    # The gauge is an involution.
    assert apply_gauge(G) == base
    return base, G


def inherited_witnesses(G):
    vs = r2.variables(G)
    w_from_one = {v: not bool(gauge_bit(v)) for v in vs}
    w_from_zero = {v: bool(gauge_bit(v)) for v in vs}
    assert r2.eval_cnf(G, w_from_one)
    assert r2.eval_cnf(G, w_from_zero)
    assert any(w_from_one[v] != w_from_one[vs[0]] for v in vs[1:])
    assert any(w_from_zero[v] != w_from_zero[vs[0]] for v in vs[1:])
    return w_from_one, w_from_zero


def polarity_terminal_certificate(F):
    positive_rows = []
    negative_rows = []
    all_pos = True
    all_neg = True
    for idx, c in enumerate(F):
        pos = next((l for l in c if l > 0), None)
        neg = next((l for l in c if l < 0), None)
        if pos is None:
            all_pos = False
        else:
            positive_rows.append((idx, pos))
        if neg is None:
            all_neg = False
        else:
            negative_rows.append((idx, neg))
    return {
        "all_clauses_have_positive_literal": all_pos,
        "all_clauses_have_negative_literal": all_neg,
        "positive_certificate_rows": len(positive_rows),
        "negative_certificate_rows": len(negative_rows),
        "all_positive_clause_count": sum(all(l > 0 for l in c) for c in F),
        "all_negative_clause_count": sum(all(l < 0 for l in c) for c in F),
    }


def audit_gauged(n: int, full_table: bool):
    base, F = gauged_escape_cnf(n)
    vs = r2.variables(F)
    w1, w0 = inherited_witnesses(F)

    pol = r2.polarity_counts(F)
    profiles = {v: r2.pivot_resolvent_profile(F, v) for v in vs}
    pure = [v for v, (p, m) in pol.items() if p == 0 or m == 0]
    zero = [v for v, row in profiles.items() if row["distinct_ntr"] == 0]
    single = [v for v, row in profiles.items() if row["distinct_ntr"] == 1]
    twin, _ = r2.has_complementary_twin(F)
    subs, _ = r2.has_strict_subsumption(F)
    ssr, _ = r2.has_ssr(F)
    components = r2.incidence_component_count(F)
    polarity = polarity_terminal_certificate(F)

    orbit_state, orbit_cert = r2.swap.build_quotient(F)

    assert pure == []
    assert zero == []
    assert single == []
    assert twin is False
    assert subs is False
    assert ssr is False
    assert components == 1
    assert polarity["all_positive_clause_count"] > 0
    assert polarity["all_negative_clause_count"] > 0
    assert polarity["all_clauses_have_positive_literal"] is False
    assert polarity["all_clauses_have_negative_literal"] is False
    assert orbit_state is None
    assert orbit_cert["status"] == "REFUSE_ORBIT_STATE_PRODUCT_EXCEEDS_N^4"

    row = {
        "n": n,
        "variables": len(vs),
        "clauses": len(F),
        "literal_occurrences": sum(len(c) for c in F),
        "gauge_pattern": list(GAUGE_PATTERN),
        "gauge_involution_replay": apply_gauge(F) == base,
        "mixed_witness_from_original_all_ones": "PASS" if r2.eval_cnf(F, w1) else "FAIL",
        "mixed_witness_from_original_all_zero": "PASS" if r2.eval_cnf(F, w0) else "FAIL",
        "pure_literal_variables": pure,
        "zero_ntr_pivots": zero,
        "single_ntr_pivots": single,
        "complementary_twin": twin,
        "strict_subsumption": subs,
        "self_subsuming_resolution": ssr,
        "incidence_component_count": components,
        "polarity_terminal": polarity,
        "swap_orbit": {
            "status": orbit_cert["status"],
            "N": orbit_cert["N"],
            "P": orbit_cert["P"],
            "pair_comparisons": orbit_cert["pair_comparisons"],
            "block_count": len(orbit_cert["blocks"]),
            "all_singletons": all(len(b) == 1 for b in orbit_cert["blocks"]),
        },
    }

    if full_table:
        table = []
        for op in frozen15():
            if op.source_language != "CNF":
                table.append({"operator_id": op.operator_id, "admitted": False, "reason": "REFUSE_SOURCE_LANGUAGE_MISMATCH"})
                continue
            oid = op.operator_id
            if oid == "PURE_LITERAL_EXISTS":
                applies, reason = bool(pure), "NO_PURE_LITERAL"
            elif oid == "TAUTOLOGICAL_RESOLVENT_EXISTS":
                applies, reason = bool(zero), "NO_PIVOT_WITH_ZERO_NTR"
            elif oid == "SINGLE_NTR_EXISTS":
                applies, reason = bool(single), "NO_PIVOT_WITH_EXACTLY_ONE_NTR"
            elif oid == "COMPLEMENTARY_TWIN":
                applies, reason = twin, "NO_COMPLEMENTARY_TWIN"
            elif oid == "CLAUSE_SUBSUMPTION":
                applies, reason = subs, "NO_STRICT_SUBSUMPTION"
            elif oid == "SELF_SUBSUMING_RESOLUTION":
                applies, reason = ssr, "NO_SSR_PAIR"
            elif oid == "COMPONENT_PRODUCT":
                applies, reason = components > 1, "INCIDENCE_CONNECTED"
            elif oid == "SWAP_ORBIT_WEIGHT_EXISTS":
                applies, reason = orbit_state is not None, orbit_cert["status"]
            elif oid == "UNIFORM_POLARITY_CLAUSE_WITNESS":
                applies = polarity["all_clauses_have_positive_literal"] or polarity["all_clauses_have_negative_literal"]
                reason = "HAS_ALL_NEGATIVE_AND_ALL_POSITIVE_CLAUSES"
            else:
                raise AssertionError("unhandled CNF operator: " + oid)
            assert applies is False, (oid, reason)
            table.append({"operator_id": oid, "admitted": False, "reason": reason})
        assert len(table) == 15
        assert all(not r["admitted"] for r in table)
        row["operator_domain_table"] = table
    return row


def main():
    # The extension itself is exact and fail-closed against heuristic authority.
    catalog = frozen15()
    bad = km.base.Operator(
        "BAD_RCTQ3_SCORE", "CNF", "TERMINAL", "SCORE_HIGH", "NONE", "NONE", "NONE", "NONE",
        authority="HEURISTIC_ROUTER", forbidden_dependencies=("SCORE", "TOP_K")
    )
    ok, reason = bad.admitted()
    assert not ok and reason == "REFUSE_NONEXACT_SELECTION_AUTHORITY"

    primary = audit_gauged(37, True)
    ladder = [audit_gauged(n, False) for n in LADDER]
    assert primary["swap_orbit"]["P"] > primary["swap_orbit"]["N"] ** 4

    result = {
        "schema": "JANUS_RCTQ3_POLARITY_TERMINAL_GAUGED_ESCAPE_RESULT",
        "status": "PASS_TYPED_POLARITY_TERMINAL_AND_EXPLICIT_FROZEN_15_GAUGED_ESCAPE",
        "claim_ceiling": "P_VS_NP_OPEN",
        "global_rule": "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT",
        "protocol_commit": PROTOCOL_COMMIT,
        "catalog_extension": {
            "old_operator_count": 14,
            "new_operator_count": len(catalog),
            "new_operator_id": POLARITY.operator_id,
            "domain_predicate": POLARITY.domain_predicate,
            "theorem_id": POLARITY.theorem_id,
            "certificate_schema": POLARITY.certificate_schema,
            "complexity_bound": POLARITY.complexity_bound,
            "heuristic_injection_admitted": ok,
            "heuristic_injection_reason": reason,
        },
        "primary_gauged_escape": primary,
        "ladder": ladder,
        "theorem_ledger": {
            "UNIFORM_POLARITY_CLAUSE_WITNESS_EXACT_ON_CERTIFIED_DOMAIN": True,
            "SIGNED_GAUGE_IS_SAT_EQUIVALENCE_BIJECTION": True,
            "G37_HAS_TWO_EXPLICIT_MIXED_WITNESSES": True,
            "G37_ESCAPES_EVERY_FROZEN_15_OPERATOR_DOMAIN": True,
            "FROZEN_15_CATALOG_UNIVERSAL_NEXT_TRANSITION_AVAILABILITY": False,
            "GAUGE_RELABELING_IS_STATE_COUNT_COMPRESSION": False,
            "CATALOG_ESCAPE_IMPLIES_SAT_HARDNESS": False,
            "P_EQUALS_NP": False,
        },
        "reverse_obligation": "INSPECT_EXACT_SIGNED_GAUGE_NORMALIZATION_AS_REPRESENTATION_CHANGE_NOT_COMPRESSION",
        "next_gate": "RCTQ4_SIGNED_GAUGE_NORMALIZATION_OR_STRONGER_BALANCED_ESCAPE",
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("JANUS_RCTQ3_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
