# PF5 Slime Balanced Binary Branch q=1 v14

Status: **FROZEN BEFORE PROVIDER RUN**  
Claim ceiling: **P_VS_NP = OPEN**

## Purpose

Isolate the cause of PF5 v13.

v13 refuted q=1 completeness for the frozen 16-candidate Slime-v3 **right-linear/caterpillar** incidence-decomposition portfolio on dense connected 3-CNF. That does not show that q=1 fails for the same leaf orders under a richer binary branch topology.

v14 changes exactly one scientific axis:

`RIGHT_LINEAR_CATERPILLAR -> BALANCED_FULL_BINARY_TREE`

The source-only Slime leaf orders, candidate names, source features, candidate count and state-cap exponent remain unchanged.

## Pinned topology producer

Repository: `Hawkar-usls/Janus-Demiurge`  
Commit: `9983b0173da9d5de1bfb5e9922fa78762160e94f`  
Module: `models/slime/slime_balanced_branch_tree_v4.py`

The producer first obtains the exact v3 16-order manifest, then recursively bisects each frozen order into a balanced full binary tree. The left-to-right leaves of every v4 tree are exactly the corresponding v3 order.

No SAT, truth table, PS-width, cap or probe feedback enters generation.

## Runtime compiler

Generalize the v12 bounded STV recurrence from a right-linear tree to an arbitrary rooted full binary incidence tree.

For internal node `v` with children `a,b`:

`PS(F_v) = { (A union B) \ C_v : A in PS(F_a), B in PS(F_b) }`,

where `C_v` is the set of source clause leaves below `v`.

For child `a`, sibling `b`, parent `v`:

`PS(F_bar_a) = { (A union B) intersect C_a : A in PS(F_b), B in PS(F_bar_v) }`.

Variable/clause leaf bases and certificate replay remain identical to v12.

## Cap remains frozen

`q = 1`

`K(F) = max(2, #variables + #clauses)`.

No escalation is permitted after results.

Every individual candidate remains fail-closed polynomially bounded: operands are at most `K` until refusal, so every internal recurrence tries at most `K^2` pairs; the tree has `O(r)` nodes and the candidate count is fixed at 16.

## Fresh dense source ladder

All rows are frozen now, after the v4 producer passed its topology-only CI:

| n | m | seeds |
|---:|---:|---|
| 10 | 42 | `910010, 910011` |
| 12 | 50 | `910012, 910013` |
| 14 | 59 | `910014, 910015` |
| 16 | 67 | `910016, 910017` |
| 18 | 76 | `910018, 910019` |
| 20 | 84 | `910020, 910021` |

Generation is the unchanged connected signed 3-CNF construction used by v13, at density approximately 4.2.

All raw formulas and all 16-tree manifests for all 12 rows must be frozen and hashed before the first bounded compiler attempt.

## Outcome-neutral terminals

For each candidate:

- `CLOSED_BALANCED_PSWIDTH_CAP`
- `OPEN_BALANCED_STATE_CAP`

For each source:

- `CLOSED_BALANCED_PORTFOLIO_Q1`
- `OPEN_BALANCED_PORTFOLIO_Q1_EXHAUSTED`

CI does not assume which terminal occurs.

## Independent validation

The runtime compiler may not enumerate assignments.

After runtime execution, CI performs a small validation-only cross-check on a bounded source by computing the C032 precisely-satisfiable cut signatures directly for selected arbitrary-tree edge cuts and comparing them with the stored forward/complement states. This exponential checker never participates in runtime selection.

## Frozen questions

1. Does balanced topology recover any q=1 CLOSED candidate on fresh dense sources where the right-linear v13 distribution exhausted?
2. How many of the 16 balanced candidates close per source?
3. Which internal-tree depth first reaches `K+1` when a candidate fails?
4. Does the selected balanced certificate replay independently from source + tree only?
5. If all candidates remain OPEN, can we conclude only that **this deterministic balanced transform** fails under q=1, not that arbitrary binary branch decompositions fail?

## Interpretation

If any fresh source closes:

`BALANCED_TOPOLOGY_RECOVERS_Q1_ON_FINITE_DENSE_CONTROL`.

This localizes at least part of v13 to decomposition topology, but does not prove universal q=1 completeness.

If all 12 sources exhaust all 16 candidates:

`SIMPLE_BALANCED_TRANSFORM_Q1_REFUTED_ON_FRESH_DENSE_LADDER`.

This still does not refute more adaptive binary tree construction or a larger predeclared fixed q.

## Prohibitions

- no q escalation;
- no v4 producer changes after holdout;
- no source replacement;
- no exact runtime scorer;
- no SAT oracle;
- no general fallback;
- no post-result tree rotations;
- no OPEN-to-hardness promotion;
- no CLOSED-to-P=NP promotion.

`P_VS_NP = OPEN`
