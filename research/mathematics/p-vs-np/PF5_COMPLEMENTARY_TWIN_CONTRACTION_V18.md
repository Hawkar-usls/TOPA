# PF5 Complementary-Twin Clause Contraction v18

## Parent obstruction

Parent spiral checkpoint: `data/PF5-PNP-SPIRAL-JOURNAL-V17.json`.

The first fresh residual surviving v12+v13+v15 is `(n=6,m=24,seed=911600)`, Hephaestus crystal SHA-256 `06cfc87bfe5963cb2ff913ce58aa1915236ad28b74d8c734d054862bb0cb4522`.

v18 adds exactly one theorem-backed operator.

## Exact identity

For any clause body `A` not containing `x` or `¬x`:

`(A ∨ x) ∧ (A ∨ ¬x) ≡ A`.

Proof is Boolean distributivity / consensus:

`(A ∨ x) ∧ (A ∨ ¬x) = A ∨ (x ∧ ¬x) = A`.

Therefore the two complementary twin clauses may be replaced by their common body with full logical equivalence, not merely equisatisfiability.

## Deterministic discovery

At a fixed point of v12+v13+v15:

1. scan variables in increasing index;
2. scan positive and negative parent clauses in source order;
3. remove the selected polarity literal from each parent;
4. accept the first pair iff the remaining canonical bodies are exactly identical;
5. replace the two parents by the common body (deduplicating an already-present identical clause is allowed by idempotence);
6. return to v12+v13+v15 exact closure and repeat.

There is no score, size threshold, entropy preference, Slime trace, SAT call, PS-width value, or truth-table query in runtime discovery.

## Certificate

Each contraction records:

- variable;
- both parent clauses and their original indices;
- common body;
- exact canonical body hashes;
- before/after residual SHA-256;
- whether the body was newly emitted or already present.

Replay recomputes the theorem premise and the exact output.

## Witness

Because this step is logical equivalence, surviving assignments are unchanged. If the contracted variable disappears entirely from the later residual, witness reconstruction may assign it a deterministic default; the equality above guarantees either value is valid whenever the common body is true.

## Diagnostic

On the frozen `911600` residual, clauses `(-3,-4,5)` and `(-3,4,5)` are complementary twins on `x4`, so they contract exactly to `(-3,5)`.

## Fresh holdout

Freeze before provider execution:

- `(n=6,m=24)` seeds `913600..913615`;
- `(n=7,m=28)` seeds `913700..913715`.

All 32 sources are generated and hashed before reduction. They are not conditioned on twin presence. All composed reductions are frozen before bounded semantic audits.

## Claim ceiling

`COMPLEMENTARY_TWIN_CLAUSE_CONTRACTION = EXACT_EQUIVALENCE`

`HEPHAESTUS_CRYSTAL = ACCOUNTING_RECURRENCE_ONLY`

`UNIVERSAL_EXACT_CLOSURE = OPEN`

`P_VS_NP = OPEN`
