# PF5 Pure-Literal Exact Projection v12

## Why this exists

The first exact v11 Slime optimality gap, seed `907000`, has a source-level property that does not require any heuristic, SAT oracle, PS-width probe, or assignment search: variable `x5` is pure negative. Recursive pure-literal projection then empties the formula.

This motivates one and only one new feature:

`PURE_LITERAL_EXISTENTIAL_PROJECTION`

It is not a candidate-scoring heuristic. It is an exact source rewrite with a replayable witness certificate.

## Exact theorem

Let

`F = R ∧ ∧_i (x ∨ A_i)`

and suppose `¬x` does not occur anywhere in `F`. Then

`∃x F ≡ R`.

A satisfying assignment of `R` lifts by setting `x = true`.

Symmetrically, if only `¬x` occurs, then

`∃x F ≡ R`

and a satisfying assignment of `R` lifts by setting `x = false`.

Therefore pure-literal elimination is an exact existential projection rule for SAT, not merely an equisatisfiability heuristic.

## Deterministic algorithm

Repeatedly:

1. scan all residual clauses and count positive/negative occurrences for each variable;
2. choose the smallest-index variable for which exactly one polarity occurs;
3. record a certificate containing the polarity counts, chosen witness value, exact removed-clause hashes, and residual hash;
4. remove every clause satisfied by the chosen pure literal;
5. continue until no pure literal remains.

No branch score, Slime trace, PS-width, SAT call, truth table, or post-hoc parameter selection is permitted.

## Cost ledger

Every scan, literal occurrence check, clause removal, certificate byte, residual byte, and witness-lift operation is charged. The implementation is polynomial in the explicit residual size per round and performs at most one round per variable.

## Frozen blind holdout

The first blind provider corpus is frozen before execution:

- seeds `908000..908031`;
- connected 3-CNF generator inherited unchanged from v9/v11;
- 5 variables, 7 clauses;
- no conditioning on whether a pure literal exists;
- no adaptive seed extension after results are observed.

The exact judge records only finite facts:

- whether the exact reducer fired;
- number of certified projection steps;
- residual variables/clauses;
- whether the residual is empty;
- exact source-vs-residual optimum caterpillar PS-width for bounded auditing when residual is non-empty.

The subset-DP scorer remains an exponential audit oracle and is not part of the runtime algorithm.

## Provider execution freeze

Branch: `pf5-pure-literal-exact-projection-v12`.

The feature, seeds, source generator, deterministic tie-break rule, certificate schema, and judge contract were fixed before this provider execution. Any failure is preserved; no parameter may be changed after observing the blind result.

## Claim ceiling

`PURE_LITERAL_EXISTENTIAL_PROJECTION = EXACT`

`UNIVERSAL_POLYNOMIAL_SEMANTIC_DECOMPOSITION_DISCOVERY = OPEN`

`P_VS_NP = OPEN`
