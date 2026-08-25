#!/usr/bin/env python3
"""PF5 v13.1 witness-adapter repair.

The v13 theorem gate, reducer, frozen seeds, exact judges and claim ceiling are
unchanged.  TRP-001 is repaired only by assigning deterministic default values
to source variables that disappear incidentally when later exact projections
remove their last clauses.
"""
from __future__ import annotations

import pf5_tautological_resolvent_projection_v13 as v13


def repaired_lift_witness(original, final_residual, transcript, final_assignment):
    ledger = {
        "projection_steps_reversed": 0,
        "removed_clause_checks": 0,
        "literal_checks": 0,
        "assignments_restored": 0,
        "default_free_assignments": 0,
    }

    # Every source variable receives a deterministic value.  Values supplied by
    # the residual witness override the defaults.  Explicit reverse projection
    # steps then overwrite their own projected variables in certificate order.
    assignment = {}
    for variable in v13.variables_of(original):
        assignment[variable] = False
        ledger["default_free_assignments"] += 1
    for variable, value in final_assignment.items():
        assignment[variable] = bool(value)

    if not v13.formula_true(final_residual, assignment, ledger):
        raise AssertionError("supplied residual witness does not satisfy residual")

    for entry in reversed(transcript):
        ledger["projection_steps_reversed"] += 1
        certificate = entry["certificate"]
        variable = certificate["variable"]
        if entry["kind"] == "PURE_LITERAL":
            assignment[variable] = bool(certificate["witness_value"])
            ledger["assignments_restored"] += 1
            continue

        positive_requires_true = False
        negative_requires_false = False
        for clause_as_list in certificate["removed_clauses"]:
            clause = tuple(clause_as_list)
            ledger["removed_clause_checks"] += 1
            if variable in clause:
                if v13.body_false(clause, variable, assignment, ledger):
                    positive_requires_true = True
            elif -variable in clause:
                if v13.body_false(clause, -variable, assignment, ledger):
                    negative_requires_false = True
            else:
                raise AssertionError("removed clause lacks projected variable")
        if positive_requires_true and negative_requires_false:
            raise AssertionError("tautological-resolvent proof failed witness lift")
        assignment[variable] = True if positive_requires_true else False
        ledger["assignments_restored"] += 1

    if not v13.formula_true(original, assignment, ledger):
        raise AssertionError("lifted witness does not satisfy source")
    return assignment, ledger


v13.lift_witness = repaired_lift_witness

if __name__ == "__main__":
    print("PF5_TRP_001_WITNESS_ADAPTER_REPAIR = ACTIVE")
    v13.main()
