#!/usr/bin/env python3
"""JANUS RCTQ-4: typed signed normalization + balanced-polarity audit.

This verifier is outcome-neutral about whether B_37 escapes the frozen 16 exact
operators. It proves the balanced construction and exact witnesses, evaluates
all frozen domains, and reports either an escape or the exact older operator(s)
that close it. The swap-orbit domain is audited symbolically: discover exact
swap classes and compare P=product(|C_j|+1) to the frozen N^4 cap, without
materializing the admitted quotient table. No heuristic, randomization, SAT
oracle, truth-table oracle, or optimum oracle is used.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROTOCOL_COMMIT = "8d4699c79b87e3c149996b653ba5649c94a0565d"
LADDER = (37, 41, 43, 47)
ORBIT_K = 4


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


r3 = load_module("rctq4_rctq3", HERE / "rctq3_polarity_gauged_escape_verifier.py")
rf = load_module("rctq4_rctq3_rf", HERE / "rctq3_reverse_forward_gauge_normalization_verifier.py")


def frozen16():
    catalog = tuple(r3.frozen15()) + (rf.NORMALIZE,)
    summary = r3.km.base.validate_catalog(catalog)
    assert summary["active_exact_operator_count"] == 16
    return catalog


def complement_clause(c):
    return tuple(-l for l in c)


def balanced_cnf(n: int):
    _, G = r3.gauged_escape_cnf(n)
    rows = []
    for c in G:
        rows.append(tuple(c))
        rows.append(complement_clause(c))
    rows.append((1, 2, 3))
    rows.append((-1, -2, -3))
    B = r3.r2.canonical_cnf(tuple(rows))
    return G, B


def truth_profile(clause, assignment):
    vals = []
    for l in clause:
        bit = assignment[abs(l)]
        vals.append(bit if l > 0 else not bit)
    return tuple(vals)


def verify_balanced_witness_derivation(n: int, G, B):
    w1, w0 = r3.inherited_witnesses(G)
    for c in G:
        t1 = truth_profile(c, w1)
        t0 = truth_profile(c, w0)
        assert any(t1) and not all(t1)
        assert any(t0) and not all(t0)
        cc = complement_clause(c)
        assert any(truth_profile(cc, w1))
        assert any(truth_profile(cc, w0))
    assert (w1[1], w1[2], w1[3]) == (True, True, False)
    assert (w0[1], w0[2], w0[3]) == (False, False, True)
    assert r3.r2.eval_cnf(B, w1)
    assert r3.r2.eval_cnf(B, w0)
    return w1, w0


def polarity_balance(F):
    counts = r3.r2.polarity_counts(F)
    rows = {v: {"positive": p, "negative": m, "delta": p - m} for v, (p, m) in sorted(counts.items())}
    exact = all(x["delta"] == 0 for x in rows.values())
    return exact, rows


def symbolic_orbit_domain(F):
    blocks, _pair_rows, comparisons = r3.r2.swap.discover_swap_classes(F)
    sizes = tuple(len(b) for b in blocks)
    P = 1
    for m in sizes:
        P *= m + 1
    N = r3.r2.swap.encoded_size(F)
    cap = N ** ORBIT_K
    admitted = P <= cap
    return {
        "status": "ADMIT_ORBIT_STATE_PRODUCT_LE_N^4" if admitted else "REFUSE_ORBIT_STATE_PRODUCT_EXCEEDS_N^4",
        "admitted": admitted,
        "N": N,
        "K": ORBIT_K,
        "N_pow_4": cap,
        "P": P,
        "pair_comparisons": comparisons,
        "block_count": len(blocks),
        "block_sizes": list(sizes),
        "all_singletons": all(m == 1 for m in sizes),
        "audit_materialization_skipped": True,
        "would_materialize_orbit_weight_states": P,
    }


def domain_audit(n: int, include_table: bool):
    G, F = balanced_cnf(n)
    w1, w0 = verify_balanced_witness_derivation(n, G, F)
    vs = r3.r2.variables(F)
    counts = r3.r2.polarity_counts(F)
    profiles = {v: r3.r2.pivot_resolvent_profile(F, v) for v in vs}
    pure = [v for v, (p, m) in counts.items() if p == 0 or m == 0]
    zero = [v for v, x in profiles.items() if x["distinct_ntr"] == 0]
    single = [v for v, x in profiles.items() if x["distinct_ntr"] == 1]
    twin, twin_cert = r3.r2.has_complementary_twin(F)
    subs, subs_cert = r3.r2.has_strict_subsumption(F)
    ssr, ssr_cert = r3.r2.has_ssr(F)
    comps = r3.r2.incidence_component_count(F)
    pol = r3.polarity_terminal_certificate(F)
    balanced, balance_rows = polarity_balance(F)
    normalize_vars = [v for v, (p, m) in counts.items() if m > p]
    orbit = symbolic_orbit_domain(F)

    assert balanced is True
    assert normalize_vars == []
    assert pol["all_positive_clause_count"] >= 1
    assert pol["all_negative_clause_count"] >= 1
    assert pol["all_clauses_have_positive_literal"] is False
    assert pol["all_clauses_have_negative_literal"] is False

    admitted = []
    table = []
    for op in frozen16():
        oid = op.operator_id
        if op.source_language != "CNF":
            applies, reason = False, "REFUSE_SOURCE_LANGUAGE_MISMATCH"
        elif oid == "PURE_LITERAL_EXISTS":
            applies, reason = bool(pure), "HAS_PURE_LITERAL" if pure else "NO_PURE_LITERAL"
        elif oid == "TAUTOLOGICAL_RESOLVENT_EXISTS":
            applies, reason = bool(zero), "HAS_ZERO_NTR_PIVOT" if zero else "NO_PIVOT_WITH_ZERO_NTR"
        elif oid == "SINGLE_NTR_EXISTS":
            applies, reason = bool(single), "HAS_SINGLE_NTR_PIVOT" if single else "NO_PIVOT_WITH_EXACTLY_ONE_NTR"
        elif oid == "COMPLEMENTARY_TWIN":
            applies, reason = twin, "HAS_COMPLEMENTARY_TWIN" if twin else "NO_COMPLEMENTARY_TWIN"
        elif oid == "CLAUSE_SUBSUMPTION":
            applies, reason = subs, "HAS_STRICT_SUBSUMPTION" if subs else "NO_STRICT_SUBSUMPTION"
        elif oid == "SELF_SUBSUMING_RESOLUTION":
            applies, reason = ssr, "HAS_SSR_PAIR" if ssr else "NO_SSR_PAIR"
        elif oid == "COMPONENT_PRODUCT":
            applies, reason = comps > 1, "INCIDENCE_DISCONNECTED" if comps > 1 else "INCIDENCE_CONNECTED"
        elif oid == "SWAP_ORBIT_WEIGHT_EXISTS":
            applies, reason = orbit["admitted"], orbit["status"]
        elif oid == "UNIFORM_POLARITY_CLAUSE_WITNESS":
            applies = pol["all_clauses_have_positive_literal"] or pol["all_clauses_have_negative_literal"]
            reason = "UNIFORM_POLARITY_DOMAIN" if applies else "HAS_ALL_POSITIVE_AND_ALL_NEGATIVE_CLAUSE_BLOCKERS"
        elif oid == "SIGNED_POLARITY_COUNT_NORMALIZE":
            applies = bool(normalize_vars)
            reason = "HAS_NEG_GT_POS_VARIABLE" if applies else "ALL_VARIABLES_POS_EQ_NEG"
        else:
            raise AssertionError("unhandled CNF operator: " + oid)
        if applies:
            admitted.append(oid)
        if include_table:
            table.append({"operator_id": oid, "admitted": applies, "reason": reason})

    row = {
        "n": n,
        "variables": len(vs),
        "clauses": len(F),
        "literal_occurrences": sum(len(c) for c in F),
        "explicit_witness_1": "PASS" if r3.r2.eval_cnf(F, w1) else "FAIL",
        "explicit_witness_0": "PASS" if r3.r2.eval_cnf(F, w0) else "FAIL",
        "exact_pos_neg_balance": balanced,
        "normalizer_domain_variables": normalize_vars,
        "pure_literal_variables": pure,
        "zero_ntr_pivots": zero,
        "single_ntr_pivots": single,
        "complementary_twin": twin,
        "complementary_twin_certificate": twin_cert,
        "strict_subsumption": subs,
        "strict_subsumption_certificate": subs_cert,
        "self_subsuming_resolution": ssr,
        "ssr_certificate": ssr_cert,
        "incidence_component_count": comps,
        "polarity_terminal": pol,
        "swap_orbit": orbit,
        "admitted_frozen16_operator_ids": admitted,
        "escaped_all_frozen16": len(admitted) == 0,
    }
    if include_table:
        row["operator_domain_table"] = table
        row["balance_rows"] = balance_rows
    return row


def main():
    catalog = frozen16()
    primary = domain_audit(37, True)
    ladder = [domain_audit(n, False) for n in LADDER]

    escaped = primary["escaped_all_frozen16"]
    ladder_escape_ns = [row["n"] for row in ladder if row["escaped_all_frozen16"]]
    status = (
        "PASS_EXPLICIT_FROZEN_16_BALANCED_ESCAPE"
        if escaped
        else "PASS_BALANCED_FAMILY_CLOSED_BY_EXISTING_EXACT_OPERATOR"
    )
    next_gate = (
        "RCTQ5_REVERSE_BALANCED_ESCAPE_FOR_NEW_EXACT_INVARIANT"
        if escaped
        else (
            "RCTQ5_USE_FIRST_CONFIRMED_BALANCED_LADDER_ESCAPE_AND_REVERSE"
            if ladder_escape_ns
            else "RCTQ5_ANALYZE_EXISTING_EXACT_OPERATOR_THAT_CLOSES_BALANCED_FAMILY"
        )
    )
    result = {
        "schema": "JANUS_RCTQ4_SIGNED_NORMALIZATION_BALANCED_FAMILY_RESULT",
        "status": status,
        "claim_ceiling": "P_VS_NP_OPEN",
        "global_rule": "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT",
        "protocol_commit": PROTOCOL_COMMIT,
        "audit_repair": {
            "rctq4_001_preserved": True,
            "domain_semantics_changed": False,
            "orbit_domain_checked_without_materialization": True,
        },
        "catalog_extension": {
            "old_operator_count": 15,
            "new_operator_count": len(catalog),
            "new_operator_id": rf.NORMALIZE.operator_id,
            "exact": True,
            "is_state_count_compression": False,
            "is_universal_sat_progress": False,
        },
        "primary_balanced_family": primary,
        "ladder": ladder,
        "ladder_escape_ns": ladder_escape_ns,
        "theorem_ledger": {
            "BALANCED_CONSTRUCTION_POS_EQ_NEG_FOR_EVERY_VARIABLE": primary["exact_pos_neg_balance"],
            "SIGNED_POLARITY_COUNT_NORMALIZE_APPLIES_TO_B37": "SIGNED_POLARITY_COUNT_NORMALIZE" in primary["admitted_frozen16_operator_ids"],
            "B37_HAS_EXPLICIT_SAT_WITNESS": primary["explicit_witness_1"] == "PASS",
            "B37_ESCAPES_EVERY_FROZEN_16_OPERATOR_DOMAIN": escaped,
            "CATALOG_ESCAPE_IMPLIES_SAT_HARDNESS": False,
            "FINITE_CI_PRACTICALITY_EQUALS_ASYMPTOTIC_POLYNOMIALITY": False,
            "P_EQUALS_NP": False,
        },
        "next_gate": next_gate,
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("JANUS_RCTQ4_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
