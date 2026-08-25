# PF5 Tautological-Resolvent Exact Projection v13

## Purpose

v11 seed `907003` is the first exact Slime optimality-gap source that survives the already admitted v12 `PURE_LITERAL_EXISTENTIAL_PROJECTION` closure unchanged.

v13 admits exactly one new source operator:

`TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION`

It is not a heuristic, candidate score, search ranking, or decomposition guess. It is a special case of exact Davis–Putnam existential elimination with **zero emitted non-tautological resolvents**.

## Exact theorem

Write a CNF as

`F = R ∧ ∧_i (x ∨ A_i) ∧ ∧_j (¬x ∨ B_j)`.

General Davis–Putnam elimination gives

`∃x F ≡ R ∧ ∧_{i,j} (A_i ∨ B_j)`,

with tautological resolvents omitted because they are identically true.

Therefore, if every positive×negative resolvent `A_i ∨ B_j` is tautological, then

`∃x F ≡ R`.

So every clause containing `x` or `¬x` can be removed exactly and no replacement clause is emitted.

A resolvent is certified tautological by a concrete complementary-literal witness: a literal `l ∈ A_i` such that `¬l ∈ B_j` (or the symmetric orientation).

## Witness lift

Given an assignment to the surviving variables that satisfies `R`:

- if some positive parent body `A_i` is false, set `x=true`;
- if some negative parent body `B_j` is false, set `x=false`;
- if neither side requires a value, use a deterministic default.

Both requirements cannot occur simultaneously: if `A_i` and `B_j` were both false, the certified complementary literals in their tautological resolvent would have to be false simultaneously, which is impossible.

Thus the projection has a deterministic replayable witness lift.

## Deterministic discovery

At a residual fixed point of v12 pure-literal closure:

1. enumerate variables by increasing index;
2. require at least one positive and one negative occurrence;
3. enumerate every positive×negative parent-clause pair;
4. for each pair, search deterministically for the first complementary-literal witness;
5. accept the first variable only if **every** pair has such a witness;
6. remove all clauses containing either polarity of that variable;
7. return to exact pure-literal closure and repeat.

There is no score and no preference learned from PS-width or SAT outcomes. The acceptance predicate is the theorem premise itself.

## Cost

For each tested variable, all positive×negative clause pairs and literal comparisons are charged. Every removed clause, certificate byte, residual byte, verification operation and witness-lift operation is charged. There are at most as many successful projection rounds as source variables. Discovery is polynomial in the explicit residual size.

## Diagnostic obstruction

For seed `907003`, v12 pure-literal closure is an exact no-op. Variable `x1` has two positive and two negative parent clauses, and all four cross-resolvents are tautological. v13 therefore projects `x1` exactly without adding clauses. The composed exact closure is then allowed to continue using the same theorem gate plus already-admitted v12 pure projection.

The diagnostic is used only to select this theorem-backed operator. No exact optimal order, PS-width value, SAT result or truth table enters the runtime rule.

## Frozen blind holdout

Before provider execution, freeze:

- seeds `909000..909031`;
- connected 3-CNF generator inherited unchanged from v9/v11;
- 5 variables, 7 clauses;
- no conditioning on whether the new operator fires;
- no adaptive seed extension after results.

For every source, first freeze the v12 pure-only residual. Then freeze the v13 composed exact residual **before** any exact PS-width audit.

The bounded exponential judge may compare pure-only and v13 residual optimum caterpillar PS-width after all reductions are frozen. It remains an audit oracle only and is not part of the runtime algorithm.

## Claim ceiling

`PURE_LITERAL_EXISTENTIAL_PROJECTION = EXACT`

`TAUTOLOGICAL_RESOLVENT_EXISTENTIAL_PROJECTION = EXACT`

`UNIVERSAL_POLYNOMIAL_SEMANTIC_DECOMPOSITION_DISCOVERY = OPEN`

`P_VS_NP = OPEN`
