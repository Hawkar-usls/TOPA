# PF5 Certified Swap-Orbit Discovery v16.3

Status: **RESTRICTED CONSTRUCTIVE DISCOVERY THEOREM**  
Claim ceiling: **`P_VS_NP = OPEN`**

## Goal

v16.2 supplied the symmetry of the duplicate-clause family by hand. v16.3
removes that hint. The input is raw CNF only.

We seek proof-carrying leaf orbit classes that can support a polynomial
whole-order quotient without using SAT, exact PS-width, Bellman values, or graph
automorphism as a free oracle.

## Safe variable swap certificate

For every variable `x`, build its exact signed clause-incidence signature

```text
Sig(x) = sorted((clause_index, sign) for every occurrence of x).
```

If `Sig(x)=Sig(y)`, then swapping `x` and `y` fixes every clause individually:
whenever one occurs in a clause, the other occurs there with the same sign, and
when one is absent the other is absent. Thus the transposition `(x y)` is an
explicit source automorphism with all clause leaves fixed.

Variables with identical signatures form a certified swap group. The
transpositions inside one group generate its full symmetric group, so any two
selected-variable subsets having the same count in each group are equivalent
under a source automorphism.

This is intentionally stronger than general CNF automorphism discovery, but it
is deterministic and polynomial.

## Clause-copy swap certificate

Clause leaves with exactly identical canonical literal tuples are freely
permutable while every variable leaf is fixed. They form exact duplicate-clause
groups.

Because the admitted variable swaps fix every clause individually, variable and
clause-copy swap groups compose independently.

## Orbit-count state bound

For discovered variable groups `G_i` and clause groups `H_j`, the exact orbit
count of raw prefix subsets under this certified product action is bounded by

```text
Q_orbit = product_i (|G_i|+1) * product_j (|H_j|+1).
```

The orbit-count vector is closed under adding one leaf: one coordinate is
incremented. A concrete action lift chooses the least-index remaining leaf in
the selected group.

A fixed capability gate may refuse when this product is not polynomially bounded
under the chosen universal exponent. Refusal is `OPEN`, not hardness.

## Exact cost language

Orbit discovery alone does not make exact PS-cut cost easy for arbitrary CNF.
v16.3 therefore closes only a recognized cost-language family:

```text
DUPLICATE_FULL_SUPPORT_POSITIVE_OR
```

Acceptance requires, from raw CNF only:

1. all clauses are identical;
2. every clause contains every source variable exactly once;
3. every literal is positive;
4. the source is nonempty.

For this family, discovery must recover exactly one variable swap group and one
clause-copy group, so the state is the v16.2 `(i,j)` count quotient and the
exact two-signature cut decoder applies.

No family label is supplied to the API.

## Conditional generalization

For any future admitted message language `M`, certified swap-orbit counts may be
combined with `M` only if:

- exact cut cost is replayably decoded from the combined state;
- transitions are closed;
- future congruence is certified;
- total orbit/message product states and proofs are polynomially bounded.

Symmetry is a compression donor, not a substitute for semantic cost messages.

## Acceptance gate

The executable audit must:

- discover the duplicate OR family from raw CNF with no family tag;
- replay signed-incidence and duplicate-clause certificates;
- match v16.2 exact cut/Bellman results on small controls;
- run large symbolic controls with no raw subset enumeration;
- reject perturbed/nonmatching controls without general SAT fallback;
- charge discovery, quotient DP, and lift work separately.

## Surviving gate

```text
ORBIT_COUNTS_X_PROOF_CARRYING_SEMANTIC_MESSAGE_LANGUAGE
```

with polynomial discovery and state-product bounds on arbitrary admitted CNF
families.

```text
P_VS_NP = OPEN
```
