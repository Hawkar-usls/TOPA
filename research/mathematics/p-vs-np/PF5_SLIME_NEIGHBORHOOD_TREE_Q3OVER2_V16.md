# PF5 Slime Neighborhood Tree q=3/2 v16

Status: **FROZEN BEFORE PROVIDER RUN**  
Claim ceiling: **P_VS_NP = OPEN**

## Purpose

Open a new fixed polynomial-cap hypothesis only after the q=1 program was separately falsified on PF5 v13-v15.

v16 keeps the exact same five source-driven neighborhood-tree heuristics from v15 and changes only the **predeclared fixed cap exponent**:

`q = 3/2`.

No q=1 receipt is reclassified or repaired.

## Pinned candidate producer

`Hawkar-usls/Janus-Demiurge@5a2ce5175049b59869c95d801b394f36ffdd3a4e`

Module:
`models/slime/slime_neighborhood_cluster_tree_v5.py`

Candidate set remains exactly:

- `NCT_COMMON_NEIGHBORS`
- `NCT_JACCARD_NEIGHBORS`
- `NCT_SYMDIFF_NEIGHBORS`
- `NCT_SIGNED_JACCARD`
- `NCT_HYBRID_SIGNED_ADJACENCY`

## Exact frozen cap

Let `r = #variables + #clauses`.

The new cap is exactly

`K(r) = ceil(r^(3/2)) = ceil(sqrt(r^3))`.

Implementation must compute this with integer arithmetic; floating-point exponentiation is forbidden in the cap calculation.

For a successful operand each PS-state family has size at most K, so every binary recurrence node attempts at most `K^2` state pairs. Because q=3/2 and the candidate count is fixed at five, every candidate attempt and the complete portfolio remain polynomially bounded.

## Fresh source domain

Frozen after q=1 v15 was sealed and before any q=3/2 provider execution:

| n | m | seeds |
|---:|---:|---|
| 10 | 42 | `912010, 912011` |
| 12 | 50 | `912012, 912013` |
| 14 | 59 | `912014, 912015` |

The source generator is unchanged: connected signed random 3-CNF with chain backbone and total density near 4.2.

All six formulas and all five-tree manifests per source must be frozen and hashed before the first capped compiler attempt.

## Runtime contract

Reuse the generalized arbitrary-binary STV recurrence from v14/v15, but supply the exact integer cap K above.

Every candidate returns:

- `CLOSED_Q3OVER2_PSWIDTH_CAP`, or
- `OPEN_Q3OVER2_STATE_CAP` at exactly K+1 distinct states.

Every CLOSED certificate is independently replayed before selection/discard.

The portfolio returns:

- `CLOSED_Q3OVER2_PORTFOLIO`, or
- `OPEN_Q3OVER2_PORTFOLIO_EXHAUSTED`.

No exact width oracle, assignment enumeration, SAT oracle, general SAT fallback, or adaptive cap escalation is allowed.

## Outcome-neutral questions

1. Does q=3/2 recover any source that the q=1 dense program would be expected to stress?
2. How many of the five frozen neighborhood trees close per source?
3. What peak PS-state size is selected relative to K?
4. How much bounded compiler work is required as K increases from O(r) to O(r^(3/2))?
5. Does any source exhaust all five candidates even under q=3/2?

## Interpretation

If a source closes:

`Q3OVER2_FINITE_RECOVERY_OBSERVED`.

This shows only that the linear cap was too restrictive for that finite source/candidate family. It is not a universal fixed-q theorem.

If a source exhausts all five candidates:

`CURRENT_NEIGHBORHOOD_PORTFOLIO_Q3OVER2_EXHAUSTED_ON_FINITE_SOURCE`.

This refutes only q=3/2 completeness for the current five-tree portfolio on that source. It does not refute other polynomial candidate constructions or any larger independently preregistered fixed exponent.

## Prohibitions

- no q changes after provider results;
- no cap formula changes;
- no new tree heuristic after results;
- no source replacement;
- no exact runtime scorer;
- no SAT oracle;
- no OPEN-to-hardness promotion;
- no CLOSED-to-P=NP promotion.

## Universal theorem gate

The target remains:

`EXISTS_FIXED_q_AND_POLY_CANDIDATE_CONSTRUCTION_SUCH_THAT_EVERY_CNF_HAS_A_CANDIDATE_OF_PSWIDTH_AT_MOST_N^q`.

`P_VS_NP = OPEN`
