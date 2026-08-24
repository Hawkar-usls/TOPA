# C025-E2R-L1G-F1 — Polarity-inversion budget

**Status:** `FORMULA_EXPANSION_BOUND_PROVED`; proof-level cut-elimination transfer `OPEN`.

**Scope firewall:** this note bounds exact local-CNF **representation size** of crossing macros using the number of negative crossing dependency edges. It does not yet bound the size of a Resolution proof after all macros are eliminated.

## 1. Negative crossing-edge budget

In the crossing dependency DAG, an edge

```text
parent <- child
```

is **negative** when the parent definition uses `~child` as an operand and both variables are crossing extensions.

For a crossing variable `e`, let

```text
q(e)
```

be the number of distinct negative crossing edges in the transitive dependency sub-DAG of `e`.

Local/root literal negations are free and are not counted; they remain local atoms in the NW functional encoding.

Let `S>=2` be an upper bound on explicit variables/definition edges/local operand occurrences in the considered macro DAG.

## 2. Positive-closure normal form

Starting from a crossing variable `e`, follow all **positive** crossing edges and flatten their AND gates. Stop whenever a negative crossing edge is encountered.

After idempotent duplicate deletion, the represented function has the form

```text
F_e = (AND local literals) AND (AND_{j=1..k} ~F_j),
```

where

- each displayed `~F_j` corresponds to a distinct frontier negative crossing edge;
- `k <= q(e)`;
- every child sub-DAG `F_j` contains at most `q(e)-1` negative crossing edges;
- different child sub-DAGs may overlap, so the proof must not assume their edge budgets are disjoint.

This last point is why the bound below is deliberately loose.

## 3. Exact local-CNF expansion

Let `P(e)` be the canonical CNF clause set for `F_e` and `N(e)` the canonical CNF clause set for `~F_e`, both over local atoms only.

For `q=0`, positive closure contains only local literals:

```text
|P(e)| <= S,
|N(e)| <= 1.
```

For `q>0`, use the normal form above.

### Positive polarity

`P(e)` is the union of:

- at most `S` local unit clauses;
- the expansions `N(F_j)` of at most `q` frontier children.

### Negative polarity

By De Morgan,

```text
~F_e = (OR negated local literals) OR F_1 OR ... OR F_k.
```

The local part contributes one clause, while OR of CNFs distributes by Cartesian product. Therefore

```text
|N(e)| <= product_j |P(F_j)|.
```

No disjointness of child dependency cones is used.

## 4. Safe factorial exponent bound

Define

```text
H(q) = (q+2)!.
```

Induct on `q`.

Base `q=0` is immediate because `|P|<=S<=S^2` and `|N|<=1`.

For the inductive step, each frontier child has negative-edge budget at most `q-1`, hence by induction both polarities have size at most `S^H(q-1)`.

Positive expansion obeys

```text
|P(e)| <= S + q*S^H(q-1)
        <= S^(H(q-1)+2)
        <= S^H(q).
```

using `q<=S` and the deliberately generous factorial exponent.

Negative expansion obeys

```text
|N(e)| <= (S^H(q-1))^q
        = S^(q H(q-1))
        <= S^H(q).
```

Thus for either polarity

```text
|CNFEXP(±e)| <= S^((q(e)+2)!).
```

The theorem is representation-only; it does not assert that a Resolution inference on macro pivot `e` can always be simulated within the same bound.

## 5. Consequences that are already valid

- `q=0` recovers the crossing-monotone polynomial-expansion regime.
- every fixed constant `q` gives polynomial exact local-CNF representation size;
- if `q=o(log N/log log N)` and `S=poly(N)`, the factorial exponent is `N^o(1)`, so macro representations remain `exp(N^o(1))` in size.

The last statement still does **not** contradict the NW Resolution lower bound until a proof-level cut-elimination/simulation theorem is established.

## 6. Parity sanity check

The frozen parity circuit has `Theta(n)` negative crossing edges and `Theta(n)` gates while its root-CNF expansion has `2^(n-1)` clauses. This is consistent with the theorem and shows that `q` must be allowed to grow on genuinely high-expansion circuits.

## 7. Next gate

`L1G-F2` asks:

> Can every Resolution inference over macros whose total negative crossing-edge budget is `q` be translated into local Resolution with overhead bounded by `S^poly_or_factorial(q)`?

A positive result would turn the representation theorem into a proof-size tradeoff and force a growing polarity-inversion budget on any short ER3 escape. A counterexample would identify a new form of macro-cut compression not visible from CNF representation size alone.

## 8. Exact status

```text
L1G_F1_NEGATIVE_EDGE_METRIC                = FROZEN
L1G_F1_POSITIVE_CLOSURE_NORMAL_FORM        = PROVED
L1G_F1_CNF_EXPANSION_FACTORIAL_BOUND       = PROVED
L1G_F1_FIXED_Q_POLY_REPRESENTATION         = PROVED
L1G_F2_PROOF_LEVEL_MACRO_CUT_ELIMINATION   = OPEN / NEXT
ISSUE_217_FULL_ER3                          = OPEN
P_VS_NP                                     = OPEN
```

## 9. Hard laws

```text
SMALL_MACRO_CNF != SMALL_MACRO_CUT_ELIMINATION_WITHOUT_A_THEOREM
NEGATIVE_EDGE_COUNT != TOTAL_EXTENSION_COUNT
FIXED_Q_POLY_REPRESENTATION != FULL_ER3_LOWER_BOUND
PARITY_REMAINS_A_COMPRESSION_COUNTEREXAMPLE
P_VS_NP = OPEN
```
