# C025-E2R-L1G-F3 — Negative-frontier width × inversion depth

**Status:** `F3_B1_DEPTH_ONLY_REFUTED_ANALYTICALLY`; `F3_B2_PAIRED_REPRESENTATION_BOUND_PROVED_ANALYTICALLY`; provider replay pending.

**Scope firewall:** this note refines the polarity-inversion structure of frozen B2 crossing macros. It is a representation theorem and adversarial barrier. Proof-level cut elimination in `(b,d)` and NW restriction survival remain separate gates.

## 1. Metrics

All root and already NW-neighborhood-local literals are treated as local atoms.

For a crossing extension DAG, a dependency edge is **negative** when a crossing child is used negated as an operand of a crossing parent.

### Inversion depth

For a crossing macro `e`, define

```text
d(e) = max number of negative crossing edges on any dependency path ending at e.
```

Positive crossing edges do not increase depth.

### Negative frontier of a positive closure

Starting at a crossing macro `u`, recursively follow every **positive** crossing dependency edge. Stop whenever a negative crossing edge is met.

Let

```text
frontier_-(u)
```

be the set of distinct negative crossing edges encountered on this boundary.

For a target macro `e`, define

```text
b(e) = max_{u in cone(e)} |frontier_-(u)|.
```

This is **negative-frontier width**.

Both are analytical measures, not assumed solver primitives.

## 2. Barrier F3.B1 — depth alone is insufficient

Take pairwise-disjoint local atoms `x_j,y_j` and define crossing-monotone macros

```text
G_j = x_j AND y_j.
```

Now build a binary aggregate

```text
H_2 = (~G_1) AND (~G_2)
H_3 = H_2 AND (~G_3)
...
F_k = H_(k-1) AND (~G_k).
```

Every dependency path to `F_k` contains at most one negative crossing edge: after entering the aggregate chain, all later aggregate edges are positive. Hence

```text
d(F_k)=1.
```

The explicit gate DAG has size `O(k)`.

But

```text
F_k = AND_j (~G_j),
~F_k = OR_j G_j.
```

Each positive `G_j` has structural CNF `{{x_j},{y_j}}`. Since the leaf pairs are disjoint, the exact structural CNF for the OR has the full Cartesian product

```text
|CNFEXP(~F_k)| = 2^k.
```

Therefore

```text
BOUNDED_INVERSION_DEPTH != POLYNOMIAL_MACRO_EXPANSION.
```

The failure is caused by an unbounded **parallel negative frontier**: `b(F_k)=k`.

## 3. Paired structural theorem

Let explicit macro-DAG volume be `S>=2`. Assume for every macro in the cone:

```text
negative-frontier width <= b,
inversion depth <= d.
```

Write `P_d` and `N_d` for worst-case structural CNF clause counts of a macro and its negation at inversion depth at most `d`.

### Base `d=0`

There is no negative crossing edge. Positive closure is a conjunction of at most `S` signed local literals, so

```text
P_0 <= S,
N_0 <= 1.
```

### Step

Flatten the positive closure of a macro `F`. It has the form

```text
F = L AND (~F_1) AND ... AND (~F_k),
k <= b,
```

where every frontier child has inversion depth at most `d-1`.

Therefore

```text
P_d <= S + b*N_(d-1),
N_d <= product_{j=1..k} P_(d-1,j) <= (P_(d-1))^b.
```

No disjointness of child cones is assumed.

Define the deliberately loose exponent

```text
E_d = (b+2)^(d+1).
```

Inductively, if both child polarities are at most `S^E_(d-1)`, then using `b<=S`:

```text
P_d <= S + b*S^E_(d-1) <= S^(E_(d-1)+2) <= S^E_d,
N_d <= S^(b*E_(d-1)) <= S^E_d.
```

Thus:

### Theorem F3.B2

```text
|CNFEXP(±e)| <= S^((b(e)+2)^(d(e)+1)).
```

This is structural representation only.

## 4. Immediate regimes

- fixed `b,d` => polynomial macro CNF representation;
- fixed `b` and `d=O(log log N)` with `S=poly(N)` can already be quasipolynomial/superpolynomial depending on constants;
- depth one with `b=Theta(N)` may have exponential expansion, as the barrier family shows.

Hence neither `b` nor `d` should be silently treated as constant.

## 5. Relation to F2

F2 used total negative-edge count `q` and proved a proof-level simulation

```text
S_local <= S^((q+5)!).
```

F3 seeks a potentially sharper structural decomposition because

```text
q counts all negative edges,
(b,d) records parallel width versus serial inversion depth.
```

The paired representation theorem does **not** automatically improve F2 proof simulation. A separate macro-cut theorem in `(b,d)` is required.

## 6. NW restriction target

Under a root restriction, transitive root support can shrink and a formerly crossing macro may become NW-local. Consequently negative crossing edges can disappear from the **surviving crossing skeleton**.

The next NW-specific resource is therefore not original `(b,d)` alone, but

```text
b_rho(e), d_rho(e)
```

computed after restriction and canonical reclassification of macros as local/crossing.

We need to quantify whether strategically global inversion frontiers survive the random/source restrictions used in the heavy-width argument.

## 7. Gates

```text
F3_A_METRICS                              = FROZEN
F3_B1_DEPTH_ONLY_POLY_ROUTE              = REFUTED
F3_B2_BD_REPRESENTATION_BOUND            = PROVED_ANALYTICALLY
F3_B2_PROVIDER_REPLAY                    = PENDING
F3_C_BD_MACRO_CUT_ELIMINATION            = OPEN / NEXT
F3_D_NW_RESTRICTION_SURVIVAL             = OPEN
F3_E_HEAVY_WIDTH_TRADEOFF                = OPEN
ISSUE_217_FULL_ER3                       = OPEN
P_VS_NP                                  = OPEN
```

## 8. Hard laws

```text
DEPTH_ONE_CAN_HAVE_EXPONENTIAL_EXPANSION
DEPTH_ALONE != POLARITY_COMPLEXITY
FRONTIER_WIDTH_ALONE != RESTRICTION_SURVIVAL
SMALL_BD_REPRESENTATION != SMALL_PROOF_WITHOUT_A_CUT_THEOREM
ORIGINAL_Q != SURVIVING_Q_AFTER_RESTRICTION
RESTRICTED_F3_RESULT != FULL_ER3_LOWER_BOUND
P_VS_NP = OPEN
```
