#!/usr/bin/env python3
"""PF5 certified swap-orbit discovery v16.3.

Restricted constructive discovery from raw CNF only.

Variable groups are discovered by exact signed clause-incidence signatures.
Equal signatures certify transpositions that fix every clause individually.
Clause groups are exact duplicate canonical clauses. For the recognized raw
family where all clauses are identical positive full-support OR clauses, these
certificates recover the v16.2 (i,j) whole-order quotient without a family tag.

Outside the admitted cost language this module returns OPEN; it never calls a
general SAT, exact PS-width, Bellman, or automorphism oracle.
"""
from __future__ import annotations

from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path

import pf5_symbolic_count_quotient_v16_2 as v16_2

CAPABILITY_EXPONENT_Q = 2


def canonical_clause(clause):
    literals = tuple(sorted(set(int(x) for x in clause), key=lambda x: (abs(x), x < 0)))
    if any(lit == 0 for lit in literals):
        raise ValueError("literal 0")
    if any(-lit in literals for lit in literals):
        raise ValueError("tautological clause not admitted")
    return literals


def canonical_cnf(clauses):
    return tuple(canonical_clause(clause) for clause in clauses)


def variables_of(cnf):
    return sorted({abs(lit) for clause in cnf for lit in clause})


def signed_incidence_groups(cnf):
    variables = variables_of(cnf)
    signatures = {v: [] for v in variables}
    literal_scans = 0
    for clause_index, clause in enumerate(cnf):
        for lit in clause:
            literal_scans += 1
            signatures[abs(lit)].append((clause_index, 1 if lit > 0 else -1))
    by_signature = defaultdict(list)
    for variable in variables:
        by_signature[tuple(signatures[variable])].append(variable)
    groups = [
        {
            "signature": [list(row) for row in signature],
            "variables": members,
            "size": len(members),
        }
        for signature, members in sorted(
            by_signature.items(), key=lambda item: (item[0], item[1])
        )
    ]
    return groups, literal_scans


def duplicate_clause_groups(cnf):
    by_clause = defaultdict(list)
    for index, clause in enumerate(cnf):
        by_clause[clause].append(index)
    groups = [
        {
            "clause": list(clause),
            "indices": indices,
            "size": len(indices),
        }
        for clause, indices in sorted(by_clause.items())
    ]
    return groups


def verify_variable_group_transpositions_fix_clauses(cnf, variable_groups):
    """Replay the signature theorem directly on every group/member pair."""
    checks = 0
    for group in variable_groups:
        members = group["variables"]
        if not members:
            continue
        representative = members[0]
        for other in members[1:]:
            for clause in cnf:
                checks += 1
                rep_pos = representative in clause
                rep_neg = -representative in clause
                oth_pos = other in clause
                oth_neg = -other in clause
                if rep_pos != oth_pos or rep_neg != oth_neg:
                    return False, checks
    return True, checks


def orbit_state_product(variable_groups, clause_groups):
    product = 1
    for group in variable_groups:
        product *= group["size"] + 1
    for group in clause_groups:
        product *= group["size"] + 1
    return product


def source_size_L(cnf):
    return 1 + len(variables_of(cnf)) + len(cnf) + sum(len(c) for c in cnf)


def recognize_duplicate_full_support_positive_or(cnf, variable_groups, clause_groups):
    variables = variables_of(cnf)
    if not cnf or not variables:
        return False, "EMPTY_SOURCE"
    if len(clause_groups) != 1:
        return False, "CLAUSES_NOT_ALL_IDENTICAL"
    clause = cnf[0]
    if any(lit < 0 for lit in clause):
        return False, "NEGATIVE_LITERAL_PRESENT"
    if sorted(clause) != variables:
        return False, "CLAUSE_NOT_FULL_VARIABLE_SUPPORT"
    if any(other != clause for other in cnf):
        return False, "CLAUSE_COPY_MISMATCH"
    if len(variable_groups) != 1:
        return False, "VARIABLE_SWAP_GROUP_NOT_SINGLE_ORBIT"
    if sorted(variable_groups[0]["variables"]) != variables:
        return False, "VARIABLE_GROUP_COVERAGE_MISMATCH"
    return True, "DUPLICATE_FULL_SUPPORT_POSITIVE_OR"


def discover(clauses):
    cnf = canonical_cnf(clauses)
    variables = variables_of(cnf)
    variable_groups, incidence_scans = signed_incidence_groups(cnf)
    clause_groups = duplicate_clause_groups(cnf)
    swap_ok, swap_replay_checks = verify_variable_group_transpositions_fix_clauses(
        cnf, variable_groups
    )
    if not swap_ok:
        raise AssertionError("signature group failed direct transposition replay")

    orbit_product = orbit_state_product(variable_groups, clause_groups)
    L = source_size_L(cnf)
    orbit_budget = L ** CAPABILITY_EXPONENT_Q
    family_ok, family_status = recognize_duplicate_full_support_positive_or(
        cnf, variable_groups, clause_groups
    )

    discovery_ops = (
        incidence_scans
        + len(cnf)
        + len(variables)
        + swap_replay_checks
        + len(variable_groups)
        + len(clause_groups)
    )
    certificate = {
        "canonical_cnf_sha256": hashlib.sha256(
            json.dumps(cnf, separators=(",", ":")).encode()
        ).hexdigest(),
        "variable_groups": variable_groups,
        "clause_groups": clause_groups,
        "variable_swap_transpositions_fix_each_clause": True,
        "clause_copy_permutations_fix_variable_leaves": True,
        "independent_product_action": True,
        "orbit_state_product": orbit_product,
        "source_size_L": L,
        "fixed_capability_exponent_q": CAPABILITY_EXPONENT_Q,
        "orbit_budget_L_pow_q": orbit_budget,
        "orbit_product_within_budget": orbit_product <= orbit_budget,
        "recognized_cost_language": family_status if family_ok else None,
        "discovery_ops": discovery_ops,
    }
    return cnf, certificate, family_ok, family_status


def solve_if_admitted(clauses):
    cnf, certificate, family_ok, family_status = discover(clauses)
    if not certificate["orbit_product_within_budget"]:
        return {
            "status": "OPEN_ORBIT_PRODUCT_BUDGET",
            "certificate": certificate,
            "reason": "certified orbit-count state product exceeds fixed L^2 budget",
        }
    if not family_ok:
        return {
            "status": "OPEN_COST_LANGUAGE",
            "certificate": certificate,
            "reason": family_status,
        }

    n = len(variables_of(cnf))
    m = len(cnf)
    symbolic = v16_2.symbolic_bellman(n, m)
    order, lift_checks = v16_2.lift_symbolic_order(n, m, symbolic["best_action"])
    return {
        "status": "CLOSED_POLY_DISCOVERED_COUNT_QUOTIENT",
        "certificate": certificate,
        "n": n,
        "m": m,
        "quotient_state_count": symbolic["state_count"],
        "quotient_transition_checks": symbolic["transition_checks"],
        "optimum": symbolic["optimum"],
        "concrete_order": order,
        "concrete_order_sha256": hashlib.sha256(
            json.dumps(order, separators=(",", ":")).encode()
        ).hexdigest(),
        "lift_checks": lift_checks,
    }


def perturbed_control(n=6, m=6):
    base = list(v16_2.duplicate_clause_family(n, m))
    last = list(base[-1])
    last[-1] = -last[-1]
    base[-1] = tuple(last)
    return tuple(base)


def run():
    small = []
    for n in range(1, 5):
        for m in range(1, 5):
            formula = v16_2.duplicate_clause_family(n, m)
            result = solve_if_admitted(formula)
            if result["status"] != "CLOSED_POLY_DISCOVERED_COUNT_QUOTIENT":
                raise AssertionError((n, m, result))
            raw = v16_2.verify_small(n, m)
            if result["optimum"] != raw["raw_optimum"]:
                raise AssertionError("discovered quotient optimum mismatch")
            if result["quotient_state_count"] != (n + 1) * (m + 1):
                raise AssertionError("wrong discovered state count")
            small.append(
                {
                    "n": n,
                    "m": m,
                    "status": result["status"],
                    "variable_group_count": len(result["certificate"]["variable_groups"]),
                    "clause_group_count": len(result["certificate"]["clause_groups"]),
                    "orbit_state_product": result["certificate"]["orbit_state_product"],
                    "quotient_state_count": result["quotient_state_count"],
                    "optimum": result["optimum"],
                    "raw_optimum": raw["raw_optimum"],
                    "discovery_ops": result["certificate"]["discovery_ops"],
                }
            )

    large = []
    for n, m in [(16, 16), (64, 64), (256, 256), (512, 512)]:
        formula = v16_2.duplicate_clause_family(n, m)
        result = solve_if_admitted(formula)
        if result["status"] != "CLOSED_POLY_DISCOVERED_COUNT_QUOTIENT":
            raise AssertionError((n, m, result["status"]))
        large.append(
            {
                "n": n,
                "m": m,
                "status": result["status"],
                "quotient_state_count": result["quotient_state_count"],
                "orbit_state_product": result["certificate"]["orbit_state_product"],
                "orbit_budget_L_pow_q": result["certificate"]["orbit_budget_L_pow_q"],
                "quotient_transition_checks": result["quotient_transition_checks"],
                "discovery_ops": result["certificate"]["discovery_ops"],
                "lift_checks": result["lift_checks"],
                "optimum": result["optimum"],
                "raw_subset_enumeration_used": False,
                "concrete_order_sha256": result["concrete_order_sha256"],
            }
        )

    negatives = []
    negative_formulas = {
        "PERTURBED_DUPLICATE_OR": perturbed_control(),
        "MIXED_SMALL_CNF": ((1, 2, 3), (-1, 2, 4), (1, -3, 4)),
    }
    for name, formula in negative_formulas.items():
        result = solve_if_admitted(formula)
        if result["status"] == "CLOSED_POLY_DISCOVERED_COUNT_QUOTIENT":
            raise AssertionError(f"negative control unexpectedly admitted: {name}")
        negatives.append(
            {
                "name": name,
                "status": result["status"],
                "reason": result["reason"],
                "variable_group_count": len(result["certificate"]["variable_groups"]),
                "clause_group_count": len(result["certificate"]["clause_groups"]),
                "orbit_state_product": result["certificate"]["orbit_state_product"],
                "orbit_product_within_budget": result["certificate"]["orbit_product_within_budget"],
            }
        )

    result = {
        "artifact_id": "PF5-CERTIFIED-SWAP-ORBIT-DISCOVERY-V16.3",
        "status": "RESTRICTED_CONSTRUCTIVE_DISCOVERY_PASS",
        "api_input": "RAW_CNF_ONLY_NO_FAMILY_TAG",
        "fixed_capability_exponent_q": CAPABILITY_EXPONENT_Q,
        "variable_orbit_certificate": "EQUAL_SIGNED_CLAUSE_INCIDENCE_SIGNATURES",
        "clause_orbit_certificate": "EXACT_DUPLICATE_CANONICAL_CLAUSES",
        "admitted_cost_language": "DUPLICATE_FULL_SUPPORT_POSITIVE_OR",
        "small_exhaustive_controls": small,
        "large_symbolic_only_controls": large,
        "negative_controls": negatives,
        "theorem": {
            "equal_signed_incidence_certifies_clause_pointwise_variable_transpositions": True,
            "connected_transpositions_generate_full_symmetric_group_per_variable_class": True,
            "duplicate_clause_copies_are_freely_permutable": True,
            "variable_and_clause_copy_actions_compose_independently": True,
            "orbit_count_vector_is_transition_closed": True,
            "orbit_state_product_formula": "product_group(size+1)",
            "fixed_orbit_product_gate": "Q_orbit <= L^2",
            "recognized_duplicate_OR_cost_decoder_is_exact": True,
            "whole_order_Bellman_and_concrete_lift_are_polynomial_on_admitted_family": True,
        },
        "epistemic_firewall": {
            "no_family_tag_in_api": True,
            "no_general_graph_automorphism_oracle": True,
            "no_sat_oracle": True,
            "no_exact_pswidth_or_bellman_oracle_in_discovery": True,
            "orbit_discovery_without_cost_language_does_not_close_instance": True,
            "negative_controls_return_open": True,
            "universal_orbit_message_product_bound_not_proved": True,
        },
        "next_gate": "ORBIT_COUNTS_X_PROOF_CARRYING_SEMANTIC_MESSAGE_LANGUAGE",
        "universal_polynomial_prefix_quotient": "OPEN",
        "p_vs_np": "OPEN",
    }
    payload = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    result["result_sha256"] = hashlib.sha256(payload).hexdigest()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()
    result = run()
    if args.json_out:
        args.json_out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print("PF5_CERTIFIED_SWAP_ORBIT_DISCOVERY_V16_3 =", result["status"])
    print("SMALL =", len(result["small_exhaustive_controls"]))
    print("LARGE =", [(r["n"], r["quotient_state_count"], r["discovery_ops"], r["optimum"]) for r in result["large_symbolic_only_controls"]])
    print("NEGATIVE =", [(r["name"], r["status"], r["reason"]) for r in result["negative_controls"]])
    print("NEXT_GATE =", result["next_gate"])
    print("P_VS_NP = OPEN")
    print("RESULT_SHA256 =", result["result_sha256"])


if __name__ == "__main__":
    main()
