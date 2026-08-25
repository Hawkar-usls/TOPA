# PF5 Slime Neighborhood Tree q=1 v15

Status: **FROZEN BEFORE PROVIDER RUN**  
Claim ceiling: **P_VS_NP = OPEN**

## Purpose

Test source-driven, non-contiguous incidence branch partitions after both PF5 v13 (right-linear) and v14 (balanced contiguous) exhausted q=1 on dense connected 3-CNF.

v15 keeps the q=1 capped STV compiler unchanged and swaps only the candidate-tree producer.

## Pinned producer

`Hawkar-usls/Janus-Demiurge@5a2ce5175049b59869c95d801b394f36ffdd3a4e`

Module:
`models/slime/slime_neighborhood_cluster_tree_v5.py`

Five source-only candidates:

- `NCT_COMMON_NEIGHBORS`
- `NCT_JACCARD_NEIGHBORS`
- `NCT_SYMDIFF_NEIGHBORS`
- `NCT_SIGNED_JACCARD`
- `NCT_HYBRID_SIGNED_ADJACENCY`

Trees are produced by deterministic agglomerative average-linkage over incidence leaves. No SAT result, assignment enumeration, PS-width, cap outcome or probe feedback enters generation.

## Cap and compiler

Unchanged from v12-v14:

`q = 1`

`K(F) = max(2, #variables + #clauses)`.

The generalized arbitrary-binary STV recurrence from v14 is reused unchanged. Every candidate stops at the first K+1 distinct state family.

## Fresh dense source ladder

Frozen now after the producer CI passed:

| n | m | seeds |
|---:|---:|---|
| 10 | 42 | `911010, 911011` |
| 12 | 50 | `911012, 911013` |
| 14 | 59 | `911014, 911015` |
| 16 | 67 | `911016, 911017` |
| 18 | 76 | `911018, 911019` |
| 20 | 84 | `911020, 911021` |

All raw formulas and all five tree manifests for all 12 sources are frozen and hashed before bounded compilation begins.

## Outcome-neutral questions

1. Does any non-contiguous neighborhood tree recover q=1 closure on fresh dense sources?
2. Which neighborhood objective closes most often?
3. If all five fail, where do they first hit K+1 (forward/complement and tree depth)?
4. What is the charged source-tree discovery cost relative to bounded compilation?
5. Does any CLOSED certificate independently replay from source + tree only?

## Interpretation

Any recovery means only:
`SOURCE_DRIVEN_NONCONTIGUOUS_TREE_RECOVERS_Q1_ON_FINITE_CONTROL`.

No recovery means only:
`CURRENT_FIVE_NEIGHBORHOOD_TREE_HEURISTICS_Q1_EXHAUSTED_ON_FRESH_DENSE_LADDER`.

Neither terminal decides arbitrary branch-decomposition q=1 completeness, any larger fixed q, or P versus NP.

## Prohibitions

- no q escalation;
- no post-result tree rotations or new similarity metric;
- no source replacement;
- no exact runtime scorer;
- no SAT oracle;
- no general fallback;
- no OPEN-to-hardness promotion;
- no CLOSED-to-P=NP promotion.

`P_VS_NP = OPEN`
