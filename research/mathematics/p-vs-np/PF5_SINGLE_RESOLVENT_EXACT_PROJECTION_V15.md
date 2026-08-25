# PF5 Single-Resolvent Exact Projection v15

## Spiral parent

Parent checkpoint: `data/PF5-PNP-SPIRAL-JOURNAL-V14.json`.

Hephaestus Crystal is used only to freeze state identity and representation bytes. It never chooses a variable.

## Exact theorem

Write

`F = R ∧ ∧_i (x ∨ A_i) ∧ ∧_j (¬x ∨ B_j)`.

Davis–Putnam elimination gives

`∃x F ≡ R ∧ ∧_{i,j}(A_i ∨ B_j)`, with tautological resolvents omitted.

If, after tautological pairs are omitted, every remaining pair yields the **same single unique non-tautological resolvent** `C`, then duplicate copies collapse idempotently and

`∃x F ≡ R ∧ C`.

This is exact existential projection, not a heuristic simplification.

## Discovery

At a fixed point of already-admitted v12+v13 closure:

1. scan variables in increasing index;
2. require both polarities;
3. enumerate every positive×negative parent pair;
4. certify each tautological pair with a concrete complementary-literal witness;
5. canonicalize every non-tautological resolvent;
6. accept the first variable iff the set of unique non-tautological resolvents has cardinality exactly `1`;
7. remove all parents containing `x/¬x` and emit that one resolvent;
8. return to v12+v13 closure.

The acceptance predicate is the theorem premise itself. No score, entropy, crystal byte count, Slime trace, SAT result, PS-width result, or learned order is visible to discovery.

## Witness lift

Given a satisfying assignment of `R ∧ C`:

- if some positive parent body `A_i` is false, set `x=true`;
- if some negative parent body `B_j` is false, set `x=false`;
- otherwise use deterministic `false`.

Both requirements cannot hold simultaneously because then the corresponding non-tautological resolvent would be false, contradicting satisfaction of `C`; tautological pairs cannot conflict either.

## Diagnostic

The first v14 surviving crystal is seed `907004`, SHA-256 `c4966d4fc14f224c3380eafb8bced50d6363975f0dd967e5d803bfcc53955132`.

At its v12+v13 fixed point, `x1` has two positive parents and one negative parent. Exactly one cross pair is tautological; the other emits the single resolvent `(-3 ∨ 2 ∨ 5)`. v15 must prove this from the source residual itself.

## Frozen blind holdout

Before provider execution freeze seeds `910000..910031`, 5 variables, 7 clauses, from the unchanged connected-3CNF generator. The corpus is not conditioned on whether v15 fires. Baseline v12+v13 residuals and v15 residuals are both frozen before bounded exhaustive semantic audits.

## Claim ceiling

`SINGLE_NONTAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION = EXACT`

`HEPHAESTUS_CRYSTAL = ACCOUNTING_AND_RECURRENCE_ONLY`

`UNIVERSAL_POLYNOMIAL_SEMANTIC_DECOMPOSITION_DISCOVERY = OPEN`

`P_VS_NP = OPEN`
