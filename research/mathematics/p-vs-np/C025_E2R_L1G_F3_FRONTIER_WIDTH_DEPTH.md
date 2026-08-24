# C025-E2R-L1G-F3 — Negative-frontier width × inversion depth

**Status:** `F3_B1_DEPTH_ONLY_REFUTED_ANALYTICALLY`; `F3_B2_PAIRED_REPRESENTATION_BOUND_PROVED_ANALYTICALLY`; `F3_C_PAIRED_CUT_ELIMINATION_PROVED_ANALYTICALLY_PENDING_PROVIDER_REPLAY`.

**Scope firewall:** this note refines the polarity-inversion structure of frozen B2 crossing macros on the stated NW hard-family transfer. Global ER3/ER/EF p-boundedness and P vs NP remain open.

## 1. Metrics

A crossing dependency edge is **negative** when a crossing child is used negated as an operand of a crossing parent.

For a crossing macro `e`, define inversion depth

```text
d(e) = max number of negative crossing edges on a dependency path ending at e.
```

Starting at `u`, follow all positive crossing edges and stop at negative crossing edges. The exposed set is `frontier_-(u)`. Define negative-frontier width

```text
b(e) = max_{u in cone(e)} |frontier_-(u)|.
```

These are analytical measures, not free solver primitives.

## 2. Barrier F3.B1 — depth alone is insufficient

For pairwise-disjoint local atoms define `G_j=x_j AND y_j`, then build a binary aggregate

```text
H_2 = (~G_1) AND (~G_2)
H_3 = H_2 AND (~G_3)
...
F_k = H_(k-1) AND (~G_k).
```

All aggregate-reuse edges are positive, hence every path has at most one negative crossing edge:

```text
d(F_k)=1.
```

The gate DAG is `O(k)`, but `~F_k=OR_j G_j`. Each `P(G_j)` has two disjoint unit clauses, so exact structural distribution gives

```text
|CNFEXP(~F_k)| = 2^k.
```

Thus

```text
BOUNDED_INVERSION_DEPTH != POLYNOMIAL_MACRO_EXPANSION.
```

Here `b(F_k)=k`; the missing resource is parallel negative-frontier width.

## 3. F3.B2 — paired representation theorem

Let explicit macro-DAG volume be `S>=2`, and assume every macro in the cone has frontier width at most `b` and inversion depth at most `d`.

Set

```text
E_d = (b+2)^(d+1).
```

For depth zero, positive closure is a conjunction of at most `S` local literals, so `P_0<=S`, `N_0<=1`.

At depth `d>0`, positive closure has form

```text
F = L AND (~F_1) AND ... AND (~F_k),
k<=b,
```

with child depth at most `d-1`. Hence

```text
P_d <= S + b*N_(d-1),
N_d <= (P_(d-1))^b.
```

If both child polarities are at most `S^E_(d-1)`, then using `b<=S`, both recurrences are bounded by `S^E_d`. Therefore

```text
|CNFEXP(±e)| <= S^((b+2)^(d+1)).
```

No disjointness of child cones is assumed.

## 4. F3.C — proof-level paired cut elimination

Use the pure-Resolution `restrict -> refute -> lift` context lemma established in F2.

Let `R_d` be a safe upper bound for a pure Resolution refutation of `P(F) union N(F)` when `(b,d)` bounds the macro cone.

Base `d=0`: complement of a conjunction is refuted against its local units in at most `S` steps.

For `d>0`, resolve local complement literals away, then eliminate the at most `b` frontier children one at a time by context-lifting the inductive complement refutation. The structural representation bound gives the deliberately loose recurrence

```text
R_d <= S^(E_d+1) + b*S^E_d*R_(d-1).
```

Claim inductively

```text
R_d <= S^(3 E_d).
```

Indeed `R_(d-1)<=S^(3E_(d-1))`, `b<=S`, and `E_d=(b+2)E_(d-1)`, so the recurrence exponent is at most

```text
E_d + 3E_(d-1) + 2 <= 3E_d
```

for the nontrivial `b>=1` case; `b=0` is the monotone base case.

### ER3 macro-pivot simulation

A width-3 source line expands into at most

```text
S^(3E_d)
```

local clauses. For each target expansion clause, F2 pure context lifting of the complement refutation costs at most `S^(3E_d)`. Thus one macro-pivot is safely simulated within `S^(6E_d)`, and multiplying by at most `S` source proof nodes gives

### Theorem F3.C1

```text
S_local <= S^(7 (b+2)^(d+1)).
```

The constant 7 is intentionally loose. The structural dependence on `(b,d)` is the point.

## 5. Hard-family width-depth tradeoff

For the polynomial-input existential NW-parity family, local-functional Resolution requires

```text
L(N) >= exp(N^eta)
```

for some fixed `eta>0` on sufficiently large family members.

Assume a polynomial-size B2/ER3 escape `S<=N^c`. The F3.C1 simulation forces

```text
N^(O((b+2)^(d+1))) >= exp(N^eta).
```

Taking logarithms,

```text
(b+2)^(d+1) * O(log N) >= N^eta.
```

Hence

```text
(d+1) * log(b+2) = Omega(log N).
```

### Structural consequence

A polynomial-size escape cannot simultaneously have narrow negative frontiers and shallow inversion depth.

Examples:
- constant `b` forces `d=Omega(log N)`;
- constant `d` forces `b=N^Omega(1)`;
- more generally the product in logarithmic coordinates must cross the stated threshold.

This does not imply superpolynomial total extension count.

## 6. Restriction survival is now the exact next resource

Under a root restriction, macro support can shrink and crossing nodes/negative edges may become local, aliases or constants. Define the **surviving crossing skeleton** after simplification and recompute

```text
b_rho(e), d_rho(e).
```

Pure deletion/simplification cannot create new original negative crossing edges, so these measures are candidates for monotone shrinkage. But the hard question is quantitative:

> how likely can a polynomial-size proof arrange its large `(b,d)` inversion structure so that enough of it survives the NW restrictions used by the heavy-width argument?

That is F3.D.

## 7. Gates

```text
F3_A_METRICS                              = FROZEN
F3_B1_DEPTH_ONLY_POLY_ROUTE              = REFUTED_ANALYTICALLY
F3_B2_BD_REPRESENTATION_BOUND            = PROVED_ANALYTICALLY
F3_C_BD_COMPLEMENT_REFUTATION            = PROVED_ANALYTICALLY
F3_C_BD_MACRO_CUT_ELIMINATION            = PROVED_ANALYTICALLY
F3_C_WIDTH_DEPTH_TRADEOFF                 = DERIVED_FROM_SOURCE_LOWER_BOUND
F3_PROVIDER_REPLAY                       = PENDING
F3_D_NW_RESTRICTION_SURVIVAL             = OPEN / NEXT
F3_E_HEAVY_WIDTH_TRADEOFF                = OPEN
ISSUE_217_FULL_ER3                       = OPEN
P_VS_NP                                  = OPEN
```

## 8. Hard laws

```text
DEPTH_ONE_CAN_HAVE_EXPONENTIAL_EXPANSION
DEPTH_ALONE != POLARITY_COMPLEXITY
WIDTH_DEPTH_TRADEOFF != SUPERPOLYNOMIAL_EXTENSION_COUNT
SMALL_BD_REPRESENTATION_REQUIRES_PROOF_LEVEL_CUT_THEOREM_BEFORE_USE
ORIGINAL_BD != SURVIVING_BD_AFTER_RESTRICTION
RESTRICTED_F3_RESULT != FULL_ER3_LOWER_BOUND
P_VS_NP = OPEN
```
