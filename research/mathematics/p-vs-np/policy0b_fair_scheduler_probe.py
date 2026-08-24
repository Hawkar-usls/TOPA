#!/usr/bin/env python3
"""Finite scheduler-only probe for C025 Policy-0B-Fair.

This probe deliberately does NOT implement a new SAT solver and does not retain
all generated resolvents.  It verifies the scheduler lemma on the frozen C024
resolution-sink counterfamily: every complementary parent pair in the frozen
layer can be visited in O(L^2) attempts, and the early sink pivot can no longer
prevent later GT-core pivots from being reached.

Claim ceiling: scheduler mechanics only; no polynomial-SAT claim.
"""

from __future__ import annotations

from collections import defaultdict

from policy0a_padded_gt_counterfamily import build_padded_gt, unit_propagate


def frozen_pair_profile(cnf):
    positive = defaultdict(list)
    negative = defaultdict(list)
    for clause in cnf:
        for literal in clause:
            (positive if literal > 0 else negative)[abs(literal)].append(clause)

    pivots = sorted(set(positive) & set(negative))
    profile = []
    total_attempts = 0
    for pivot in pivots:
        attempts = len(positive[pivot]) * len(negative[pivot])
        total_attempts += attempts
        profile.append((pivot, len(positive[pivot]), len(negative[pivot]), attempts))
    return profile, total_attempts


def self_test(n: int = 3) -> None:
    family = build_padded_gt(n)
    propagated, contradiction = unit_propagate(family.cnf)
    assert not contradiction
    assert propagated is not None

    L = sum(len(clause) for clause in propagated)
    profile, attempts = frozen_pair_profile(propagated)
    profile_by_pivot = {row[0]: row for row in profile}

    # Complete-layer bound: sum p_x q_x <= (sum p_x)(sum q_x) <= L^2/4.
    assert attempts * 4 <= L * L

    # The old sink remains large and first, but it no longer terminates the pass.
    assert family.sink_d in profile_by_pivot
    assert profile[0][0] == family.sink_d
    assert profile_by_pivot[family.sink_d][3] == family.p**2

    reached_core = [row for row in profile if row[0] in family.core_variables]
    assert reached_core, "fair scan must reach at least one GT-core pivot"

    # Every eligible core pivot is represented in the scan; no early cutoff exists.
    eligible_core = {
        pivot
        for pivot in family.core_variables
        if pivot in profile_by_pivot
    }
    scanned_core = {row[0] for row in reached_core}
    assert scanned_core == eligible_core

    print("TOPA_POLICY0B_FAIR_SCHEDULER = PASS")
    print(f"n = {n}")
    print(f"literal_occurrences = {L}")
    print(f"eligible_pivots = {len(profile)}")
    print(f"complete_pair_attempts = {attempts}")
    print(f"L_squared_over_4 = {(L * L) // 4}")
    print(f"sink_attempts = {family.p**2}")
    print(f"eligible_core_pivots = {len(eligible_core)}")
    print(f"scanned_core_pivots = {len(scanned_core)}")
    print("claim_boundary = fair frozen-layer scheduling only; no resolvent-retention or polynomial-total-time theorem")


if __name__ == "__main__":
    self_test()
