#!/usr/bin/env python3
"""JANUS RCTQ-2: exact frozen-catalog coverage falsifier.

This verifier checks whether the currently frozen 14-operator Keymaster catalog
has any admitted next transition on one explicit nonterminal CNF state E_37.
No heuristic, score, randomization, SAT oracle, truth-table oracle, or optimum
oracle is used.  A catalog escape refutes only universal coverage of this
frozen finite catalog; it does not establish SAT hardness or resolve P vs NP.
"""
from __future__ import annotations

from collections import defaultdict, deque
from hashlib import sha256
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROTOCOL_COMMIT = "ecfc196751bb4f818535109454c83a2831a7c58c"

EXPECTED_CATALOG = (
    "PURE_LITERAL_EXISTS",
    "TAUTOLOGICAL_RESOLVENT_EXISTS",
    "SINGLE_NTR_EXISTS",
    "COMPLEMENTARY_TWIN",
    "CLAUSE_SUBSUMPTION",
    "SELF_SUBSUMING_RESOLUTION",
    "COMPONENT_PRODUCT",
    "TWO_SAT_SCC",
    "AFFINE_GF2_JOIN",
    "ACI_SHARED_FACTOR",
    "LITERAL_ACI_EXISTS",
    "SYMMETRIC_WEIGHT_EXISTS",
    "SWAP_ORBIT_WEIGHT_EXISTS",
    "SWAP_ORBIT_WEIGHT_EXISTS_CLOSED",
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ext = load_module(
    "rctq2_keymaster_extension",
    HERE / "u1l2c2k1_keymaster_catalog_extension_verifier.py",
)
swap = load_module(
    "rctq2_swap_orbit",
    HERE / "u1l2c2c1_swap_orbit_weight_quotient_verifier.py",
)


def lit_key(l: int):
    return (abs(l), 0 if l < 0 else 1)


def canonical_clause(clause):
    return tuple(sorted(set(int(x) for x in clause), key=lit_key))


def canonical_cnf(clauses):
    norm = [canonical_clause(c) for c in clauses]
    return tuple(sorted(norm, key=lambda c: (len(c), tuple(lit_key(x) for x in c))))


def variables(F):
    return tuple(sorted({abs(l) for c in F for l in c}))


def escape_cnf(n: int):
    assert n >= 11
    clauses = []
    for i0 in range(n):
        x = i0 + 1
        def v(offset: int) -> int:
            return ((i0 + offset) % n) + 1
        clauses.append((x, v(1), -v(2)))
        clauses.append((-x, v(3), v(5)))
    F = canonical_cnf(clauses)
    assert len(F) == 2 * n
    assert all(len(c) == 3 for c in F)
    return F


def eval_cnf(F, assignment):
    return all(any(assignment[abs(l)] if l > 0 else not assignment[abs(l)] for l in c) for c in F)


def polarity_counts(F):
    out = {v: [0, 0] for v in variables(F)}
    for c in F:
        for l in c:
            out[abs(l)][0 if l > 0 else 1] += 1
    return {v: tuple(x) for v, x in sorted(out.items())}


def pivot_resolvent_profile(F, x: int):
    pos = [c for c in F if x in c]
    neg = [c for c in F if -x in c]
    ntr = set()
    tautological = 0
    pairs = 0
    for p in pos:
        A = set(p); A.remove(x)
        for q in neg:
            pairs += 1
            B = set(q); B.remove(-x)
            r = A | B
            if any(-l in r for l in r):
                tautological += 1
            else:
                ntr.add(canonical_clause(r))
    return {
        "positive_parents": len(pos),
        "negative_parents": len(neg),
        "parent_pairs": pairs,
        "tautological_pairs": tautological,
        "distinct_ntr": len(ntr),
    }


def has_complementary_twin(F):
    clause_set = set(F)
    for c in F:
        for l in c:
            rest = [x for x in c if x != l]
            twin = canonical_clause([-l] + rest)
            if twin in clause_set:
                return True, {"clause": list(c), "twin": list(twin), "pivot": l}
    return False, None


def has_strict_subsumption(F):
    sets = [set(c) for c in F]
    for i, A in enumerate(sets):
        for j, B in enumerate(sets):
            if i != j and A < B:
                return True, {"small": list(F[i]), "large": list(F[j])}
    return False, None


def has_ssr(F):
    sets = [set(c) for c in F]
    for i, C in enumerate(F):
        for j, D in enumerate(F):
            if i == j:
                continue
            SD = sets[j]
            SC = sets[i]
            for l in C:
                if -l in SD:
                    A = SC - {l}
                    B = SD - {-l}
                    if A <= B:
                        return True, {"left": list(C), "right": list(D), "pivot": l}
    return False, None


def incidence_component_count(F):
    # Variable projection of the bipartite incidence graph: each clause joins
    # all variables it contains.  For nonempty clauses this has the same number
    # of nonempty incidence components.
    vs = variables(F)
    adj = {v: set() for v in vs}
    for c in F:
        cv = [abs(l) for l in c]
        for u, v in combinations(cv, 2):
            adj[u].add(v); adj[v].add(u)
    seen = set()
    count = 0
    for root in vs:
        if root in seen:
            continue
        count += 1
        seen.add(root)
        q = deque([root])
        while q:
            u = q.popleft()
            for v in sorted(adj[u]):
                if v not in seen:
                    seen.add(v); q.append(v)
    return count


def frozen_catalog():
    catalog = tuple(ext.base.ACTIVE_CATALOG) + (ext.NEW, ext.SELF)
    ids = tuple(op.operator_id for op in catalog)
    assert ids == EXPECTED_CATALOG, ids
    summary = ext.base.validate_catalog(catalog)
    assert summary["active_exact_operator_count"] == 14
    return catalog


def audit_instance(n: int, full_operator_table: bool):
    F = escape_cnf(n)
    vs = variables(F)
    all_ones = {v: True for v in vs}
    assert eval_cnf(F, all_ones)

    pol = polarity_counts(F)
    profiles = {v: pivot_resolvent_profile(F, v) for v in vs}
    pure = [v for v, (p, m) in pol.items() if p == 0 or m == 0]
    taut_pivots = [v for v, r in profiles.items() if r["distinct_ntr"] == 0]
    single_pivots = [v for v, r in profiles.items() if r["distinct_ntr"] == 1]
    twin, twin_cert = has_complementary_twin(F)
    subs, subs_cert = has_strict_subsumption(F)
    ssr, ssr_cert = has_ssr(F)
    components = incidence_component_count(F)

    orbit_state, orbit_cert = swap.build_quotient(F)
    assert orbit_state is None
    assert orbit_cert["status"] == "REFUSE_ORBIT_STATE_PRODUCT_EXCEEDS_N^4"

    row = {
        "n": n,
        "variable_count": len(vs),
        "clause_count": len(F),
        "literal_occurrences": sum(len(c) for c in F),
        "all_ones_witness_replay": "PASS_SAT_WITNESS",
        "polarity_profile_set": sorted({tuple(x) for x in pol.values()}),
        "resolvent_profile_set": sorted({
            (r["positive_parents"], r["negative_parents"], r["parent_pairs"], r["tautological_pairs"], r["distinct_ntr"])
            for r in profiles.values()
        }),
        "pure_literal_variables": pure,
        "zero_ntr_pivots": taut_pivots,
        "single_ntr_pivots": single_pivots,
        "complementary_twin": twin,
        "strict_subsumption": subs,
        "self_subsuming_resolution": ssr,
        "incidence_component_count": components,
        "swap_orbit": orbit_cert,
    }

    assert pure == []
    assert taut_pivots == []
    assert single_pivots == []
    assert twin is False and twin_cert is None
    assert subs is False and subs_cert is None
    assert ssr is False and ssr_cert is None
    assert components == 1

    if full_operator_table:
        operator_rows = []
        for op in frozen_catalog():
            if op.source_language != "CNF":
                operator_rows.append({
                    "operator_id": op.operator_id,
                    "admitted_on_E37": False,
                    "reason": "REFUSE_SOURCE_LANGUAGE_MISMATCH",
                    "source_language": op.source_language,
                })
                continue
            if op.operator_id == "PURE_LITERAL_EXISTS":
                applies, reason = bool(pure), "NO_PURE_LITERAL"
            elif op.operator_id == "TAUTOLOGICAL_RESOLVENT_EXISTS":
                applies, reason = bool(taut_pivots), "NO_PIVOT_WITH_ZERO_NTR"
            elif op.operator_id == "SINGLE_NTR_EXISTS":
                applies, reason = bool(single_pivots), "NO_PIVOT_WITH_EXACTLY_ONE_NTR"
            elif op.operator_id == "COMPLEMENTARY_TWIN":
                applies, reason = twin, "NO_COMPLEMENTARY_TWIN"
            elif op.operator_id == "CLAUSE_SUBSUMPTION":
                applies, reason = subs, "NO_STRICT_SUBSUMPTION"
            elif op.operator_id == "SELF_SUBSUMING_RESOLUTION":
                applies, reason = ssr, "NO_SSR_PAIR"
            elif op.operator_id == "COMPONENT_PRODUCT":
                applies, reason = components > 1, "INCIDENCE_CONNECTED"
            elif op.operator_id == "SWAP_ORBIT_WEIGHT_EXISTS":
                applies, reason = orbit_state is not None, orbit_cert["status"]
            else:
                raise AssertionError("unhandled CNF operator: " + op.operator_id)
            assert applies is False
            operator_rows.append({
                "operator_id": op.operator_id,
                "admitted_on_E37": False,
                "reason": reason,
                "source_language": op.source_language,
            })
        assert len(operator_rows) == 14
        assert all(r["admitted_on_E37"] is False for r in operator_rows)
        row["operator_domain_table"] = operator_rows
    return row


def main():
    primary = audit_instance(37, True)
    ladder = [audit_instance(n, False) for n in (37, 41, 43, 47)]

    orbit = primary["swap_orbit"]
    assert orbit["N"] == 334
    assert orbit["P"] == 2 ** 37
    assert orbit["P"] > orbit["N"] ** 4
    assert all(len(block) == 1 for block in orbit["blocks"])

    result = {
        "schema": "JANUS_RCTQ2_FROZEN_CATALOG_ESCAPE_RESULT",
        "status": "PASS_EXPLICIT_FROZEN_14_CATALOG_ESCAPE",
        "claim_ceiling": "P_VS_NP_OPEN",
        "global_rule": "NO_HEURISTICS_ANYWHERE_IN_PNP_PROJECT",
        "protocol_commit": PROTOCOL_COMMIT,
        "frozen_catalog_operator_count": 14,
        "frozen_catalog_operator_ids": list(EXPECTED_CATALOG),
        "primary_escape_state": primary,
        "secondary_escape_ladder": ladder,
        "theorem_ledger": {
            "FROZEN_14_CATALOG_UNIVERSAL_NEXT_TRANSITION_AVAILABILITY": False,
            "E37_IS_EXPLICIT_NONTERMINAL_SAT_STATE": True,
            "E37_ESCAPES_EVERY_FROZEN_OPERATOR_DOMAIN": True,
            "CATALOG_COVERAGE_FAILURE_IMPLIES_SAT_HARDNESS": False,
            "CATALOG_COVERAGE_FAILURE_IMPLIES_P_NOT_EQUAL_NP": False,
            "RESTRICT_ALONE_IS_EXISTENTIAL_SAT_EQUIVALENT_TRANSITION": False,
            "P_EQUALS_NP": False,
        },
        "meaning": "The currently frozen 14-operator exact Keymaster catalog is not universally transition-complete.  E_37 is an explicit satisfiable nonterminal CNF outside every frozen operator domain.  This localizes a missing exact transition schema; it is not a hardness theorem.",
        "next_gate": "RCTQ3_EXACT_BRANCH_COMPOSITION_OR_NEW_EQUIVALENCE_PRESERVING_CNF_TRANSITION",
        "universal_polynomial_sat_algorithm": "NOT_ESTABLISHED",
        "P_VS_NP": "OPEN",
    }
    packed = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    print(json.dumps(result, indent=2, sort_keys=True))
    print("JANUS_RCTQ2_RESULT_SHA256=" + sha256(packed).hexdigest())
    print("P_VS_NP=OPEN")


if __name__ == "__main__":
    main()
