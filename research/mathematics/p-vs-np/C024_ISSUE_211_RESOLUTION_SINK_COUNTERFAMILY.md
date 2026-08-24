# C024 / Issue #211 — Resolution-Sink Padding Counterfamily

**Status:** strong formal refutation candidate for `UNIVERSAL_POLYNOMIAL_RESIDUAL_COUNT`; pending independent replay and exact implementation parity check before closing the parent issue.

**Claim ceiling:** this attacks the current deterministic `Policy-0A / JANUS-FC_local` residual-count lemma. It does **not** prove `P != NP` and does not rule out a different SAT calculus.

## 1. Target

Issue #211 asks whether there are fixed constants `c,N0` such that for every CNF `F` of canonical encoded bit length `N >= N0`, the uncapped deterministic Policy-0A execution creates at most

```text
S(F) <= N^c
```

unique pre-resolution exact cache keys.

To refute this universal statement it is sufficient to construct one explicit polynomial-size infinite family whose Policy-0A execution inherits a superpolynomial residual lower bound.

## 2. External theorem used

Beame, Impagliazzo, Pitassi and Segerlind, *Formula Caching in DPLL* (ACM TOCT 2010), Definition 4.24 and Theorem 4.28:

- `GT_n` is the directed graph-tautology / graph-ordering formula on `n(n-1)` directed variables, with the ordering clauses plus totality;
- every `FCWS` refutation of `GT_n` requires at least `2^(n-2)` nodes;
- the proof identifies at least `2^(n-2)` distinct residual formulas at novelty level `n-2`.

`FCWS` is stronger than exact basic Formula Caching, so the same lower bound is available against any projected exact-FC execution on the same `GT_n` object.

Primary source:

- https://www.cs.toronto.edu/~toni/Papers/memoization.pdf

## 3. Why the direct transfer previously failed

Policy-0A has an extra deterministic local Resolution pass at every exact residual. Therefore the historical Formula-Caching lower bound cannot be applied directly: a derived clause can change future residuals before branching.

The construction below does not try to prove that the local Resolution rule is harmless. Instead it forces that rule to spend its complete frozen attempt budget on an independent satisfiable gadget whose resolvents are tautologies.

## 4. Construction

For every `n >= 3`, let `GT_n` be the theorem-matched directed source formula. Let

```text
V = n(n-1)
B = 256 n^2
p = 64 n^2
```

Use pairwise fresh variables for all padding.

### 4.1 Uniform branch-frequency boosters

For every directed GT variable `x` add `B` private clauses

```text
(x OR b[x,r])       for r = 1..B
```

where every `b[x,r]` occurs nowhere else.

Properties:

1. If `x` is unassigned, all `B` clauses survive and add exactly `B` occurrences to `x`.
2. If `x = 1`, all of its booster clauses disappear as satisfied.
3. If `x = 0`, the clauses become private units `b[x,r]`, which unit propagation sets to `1`; they do not constrain another GT variable.
4. Therefore the boosters do not generate core implications and add the same frequency offset to every still-unassigned GT variable.

### 4.2 Resolution sink

Give the sink pivot `d` the smallest variable id. Introduce fresh `a`, `u_1..u_p`, `v_1..v_p` and clauses

```text
(d  OR  a  OR u_r)       for r = 1..p
(~d OR ~a  OR v_s)       for s = 1..p
```

For pivot `d`, every positive-parent / negative-parent pair has resolvent

```text
(a OR u_r OR ~a OR v_s)
```

which is tautological. Hence all `p^2` complementary-pair attempts are charged but **zero** resolvents are added.

The sink is satisfiable and shares no variables with the GT core or the booster leaves.

## 5. Frozen Policy-0A accounting

Policy-0A uses

```text
attempt_budget = max(64, 4 * literal_occurrences(current_key))
addition_budget = max(8, clause_count(current_key)//4)
```

and visits pivots in increasing variable-id order.

The source `GT_n` has

```text
V_GT = n(n-1)
L_GT = 3n(n-1)^2 <= 3n^3
```

literal occurrences.

The boosters contribute at most

```text
L_boost = 2 * V * B <= 512 n^4
```

and the sink contributes

```text
L_sink = 6p = 384 n^2.
```

Therefore at the root

```text
L0 <= 512 n^4 + 3 n^3 + 384 n^2
4L0 <= 2048 n^4 + 12 n^3 + 1536 n^2.
```

But

```text
p^2 = 4096 n^4.
```

For every `n >= 1`,

```text
p^2 > 4L0.
```

The local pass adds zero clauses, and all later branching/restriction/unit-propagation steps only delete clauses or literals. Thus for every later nonterminal key `K_t`,

```text
4 * literal_occurrences(K_t) <= 4L0 < p^2.
```

So the pass always exhausts its complete attempt budget inside pivot `d` and returns before reaching any later pivot. No core Resolution inference is ever performed.

## 6. Why Policy-0A never branches into the sink

Every still-unassigned GT variable retains all `B` booster occurrences, hence has frequency at least

```text
B = 256 n^2.
```

The largest sink frequencies are

```text
freq(d) = freq(a) = 2p = 128 n^2.
```

All other padding variables have frequency `1` after exhaustive unit propagation.

Therefore, while any core variable remains,

```text
max_core_frequency >= B > 2p >= max_padding_frequency.
```

Policy-0A's most-frequent-variable branch rule must choose a GT-core variable. Adding the same `B` offset to every unassigned core variable also preserves the relative ordering/tie-breaking among the core frequencies.

If no core variable remains, the unsatisfiable GT core has already produced contradiction, so the search never needs to branch on the padding variables.

## 7. Projection lemma

Define `P(K)` to delete every clause containing a padding variable from an augmented pre-resolution key `K`.

Because:

- the sink is variable-disjoint from the core;
- a booster leaf occurs only in `(x OR b[x,r])`;
- booster propagation never forces a GT variable;
- the local Resolution pass never gets past sink pivot `d`;

we have for every nonterminal Policy-0A state reached under cumulative core restriction `rho`:

```text
P(K) = unitprop(GT_n | rho).
```

Thus the augmented execution projects to a valid exact Formula-Caching / DPLL-with-caching refutation of the theorem-matched `GT_n` core.

An augmented exact-cache collision can never identify two different projected core residuals, because equality of augmented keys implies equality after applying the deterministic projection `P`.

Hence

```text
number_of_unique_augmented_keys
    >= number_of_distinct_projected_GT_residuals.
```

## 8. Residual lower bound

Theorem 4.28 gives at least

```text
2^(n-2)
```

distinct GT residuals in every `FCWS` refutation. Exact Formula Caching is not stronger than `FCWS`, so the projected execution cannot use fewer.

Therefore the padded family `H_n` satisfies

```text
S(H_n) >= 2^(n-2).
```

## 9. Parameter transfer to actual input length

The construction contains:

- `O(n^2)` core variables;
- `V*B = O(n^4)` booster leaves/clauses;
- `O(n^2)` sink variables/clauses;
- `O(n^4)` total literal occurrences.

With ordinary deterministic integer-literal encoding, the largest variable id needs `O(log n)` bits. Thus

```text
N_n = bit_length(H_n) = O(n^4 log n).
```

For any fixed constant `c`,

```text
N_n^c = n^O(c) * (log n)^O(c) = 2^O(log n),
```

while

```text
S(H_n) >= 2^(n-2).
```

Therefore `S(H_n)` is superpolynomial in `N_n`.

## 10. Consequence if independent replay confirms parity

The construction would refute Issue #211:

```text
UNIVERSAL_POLYNOMIAL_RESIDUAL_COUNT = FALSE_FOR_CURRENT_POLICY0A
```

and therefore the current positive `POLYNOMIAL_RESIDUAL_CACHE_BRIDGE_FOR_CNF_SAT` cannot be completed for **this exact Policy-0A**, irrespective of Issue #212.

This is **not** evidence that `P != NP`. It only kills this exact algorithmic route. The counterfamily then becomes a design constraint for the next calculus: any replacement local inference budget must not be adversarially starvable by irrelevant early pivots.

## 11. Remaining replay gates

Before promoting the parent issue from `OPEN` to `REFUTED`, require all of:

1. exact line-by-line parity with the registered Policy-0A `limited_resolution`, unit propagation and branch rule;
2. machine check that sink pivot `d` exhausts the attempt budget with zero additions on frozen small `n` fixtures;
3. machine check that every chosen branch variable is in the GT core on those fixtures;
4. independent review of the projection lemma;
5. independent review of the `GT_n` source encoding and Theorem 4.28 scope;
6. explicit final parameter conversion from family parameter `n` to canonical input bit length.

Until those replay gates complete, classification is:

```text
ISSUE_211 = STRONG_FORMAL_REFUTATION_CANDIDATE
P_VS_NP = OPEN
```
