# C025-E2R-L1G-F3-D — Semantic Restriction Survival Barrier

**Frozen:** 2026-08-24  
**Status:** `F3D_D0_BD_AND_RESTRICTION_SIZE_ALONE_REFUTED`  
**Scope:** frozen B2 `AND`-extension DAGs under an abstract NW-locality hypergraph.  
**Global ceiling:** unrestricted ER3/ER/EF and `P vs NP` remain open.

## 1. Why F3-D exists

F3 proved, in the stated restricted NW transfer, a pre-restriction structural tradeoff using:

```text
b = negative-frontier width
d = inversion depth
```

with analytical simulation ceiling

```text
S_local <= S^(7*(b+2)^(d+1)).
```

The next heavy-width step uses root restrictions. A syntactically crossing extension can become:

```text
CONSTANT
ALIAS
NW-LOCAL FUNCTION
```

after restriction. Therefore original `(b,d)` cannot be inserted into a post-restriction argument without a survival theorem.

Sokolov's functional encoding makes this semantic issue explicit: a local extension variable `y_g` corresponds under a partial `x`-assignment `rho` to the residual Boolean function `g|rho`, and a self-reduction produces a residual PRG formula on the restricted base functions. Thus the relevant object after restriction is the **residual function**, not merely the original syntactic support.

Primary source boundary:

- Dmitry Sokolov, *Pseudorandom Generators, Resolution and Heavy Width*, CCC 2022, DOI `10.4230/LIPIcs.CCC.2022.15`.
- Functional encoding: Section 3.1.
- Normal partial assignments / residual local functions: Section 3.1.1, Lemma 12.
- Self-reductions: Definition 20, Remark 21, Algorithm 1.

No theorem below is claimed to be Sokolov's theorem. The source is used only to freeze the semantic target that F3-D must match.

---

## 2. Abstract locality model

Let root variables be covered by a family of locality neighborhoods

```text
V_1, ..., V_m.
```

A Boolean function is **local** if it depends only on variables contained in one `V_i`; otherwise it is **crossing**.

Frozen B2 extensions have the form

```text
e := a AND b
```

where `a,b` are signed literals over root variables or earlier extensions.

For the pre-restriction DAG use the already frozen metrics:

- a **negative crossing edge** is a crossing child used negatively by a crossing parent;
- `d` is maximum negative-edge depth;
- `frontier_-(u)` follows positive crossing dependencies and stops at negative crossing edges;
- `b` is the maximum exposed negative-frontier cardinality.

After a root restriction `rho`, define each extension by its exact residual Boolean function over unassigned root variables. A semantically surviving crossing macro must be nonconstant and nonlocal after this residualization.

---

## 3. D0 counterfamily — one root bit can kill arbitrary width and depth

### Theorem F3D.D0

For every integers `B >= 2` and `D >= 1`, there exists an `O(BD)`-gate frozen-B2 extension DAG over a locality hypergraph such that:

```text
pre-restriction negative-frontier width b >= B,
pre-restriction inversion depth d >= D,
```

but there is a one-variable root restriction `rho` with

```text
|rho| = 1
```

under which **every crossing macro in the construction becomes a constant**.

Consequently any semantic surviving crossing skeleton is empty and

```text
b_rho = 0,
d_rho = 0.
```

### Construction

Choose one root variable `z` and roots `y_j` such that no locality neighborhood contains `{z,y_j}` for `j=1,...,B`.

For each branch `j`, create a negative chain:

```text
g[j,1] := z AND y_j
g[j,t] := z AND NOT g[j,t-1]       for t=2,...,D.
```

Each `g[j,t]` is crossing. The chain contributes `D-1` negative crossing edges.

Let `top_j := g[j,D]`. Aggregate the branch tops with positive reuse of the previous aggregate and a new negative branch input:

```text
A_2 := (NOT top_1) AND (NOT top_2)
A_k := A_(k-1) AND (NOT top_k)     for k=3,...,B.
```

Following the positive aggregate chain exposes the `B` negative top edges, so the final cone has negative-frontier width at least `B`. A path through a depth-`D` branch and its negative edge into the aggregate has inversion depth at least `D`.

The gate count is

```text
B*D + (B-1) = O(BD).
```

Now apply

```text
rho(z) = 0.
```

Inductively:

```text
g[j,1]|rho = 0,
g[j,t]|rho = 0 AND (...) = 0.
```

Hence every `top_j|rho = 0` and therefore

```text
A_2|rho = 1,
A_k|rho = 1.
```

All crossing macros collapse to constants. QED.

---

## 4. What this refutes

The construction refutes every proposed universal F3-D statement of the form

```text
large original b,d
+ small |rho|
=> nontrivially large surviving b_rho,d_rho
```

when the right-hand lower bound depends only on `(b,d,|rho|)`.

In particular:

```text
ORIGINAL_BD != RESTRICTION_ROBUST_BD
SMALL_RESTRICTION_SIZE != SMALL_SEMANTIC_DAMAGE
LARGE_INVERSION_STRUCTURE != DISTRIBUTED_INVERSION_STRUCTURE
```

This does **not** refute survival under the exact Sokolov self-reduction distribution on the frozen hard NW family. The counterfamily is an abstract locality-hypergraph barrier that identifies a missing parameter.

---

## 5. The hidden resource: restriction resilience

A scientifically admissible replacement must be defined from exact semantics, not a heuristic score.

### 5.1 Semantic collapse set

For a proof/macro DAG `P`, root set `R` and threshold pair `(B0,D0)`, define a restriction `rho` to be a **collapse restriction** if the exact residualized DAG/function system has

```text
b_sem(P|rho) < B0
OR
d_sem(P|rho) < D0.
```

The first crude parameter is the semantic kill number

```text
kappa_sem(P;B0,D0)
  := min |supp(rho)|
     over collapse restrictions rho.
```

F3D.D0 shows that arbitrarily large original `(b,d)` may coexist with

```text
kappa_sem = 1.
```

Therefore `kappa_sem` contains information absent from `(b,d)`.

### 5.2 Distributional survival functional

For an **explicitly specified** restriction distribution `D`, define

```text
SURV_P(B0,D0; D)
  := Pr_{rho <- D}[
       b_sem(P|rho) >= B0
       AND
       d_sem(P|rho) >= D0
     ].
```

This is not a confidence score. It is a mathematical probability under a named distribution over restrictions.

For the intended theorem-transfer target, `D` must be tied exactly to Sokolov's self-reduction construction (Definition 20 / Algorithm 1), including the treatment of every choice that the source algorithm leaves nonunique.

If a deterministic selector is introduced for an otherwise arbitrary source step, its preservation of the source hypotheses must be proved and its computation cost charged separately.

---

## 6. Why a single scalar kill number is still insufficient

`kappa_sem` is existential: one rare adversarial restriction may collapse the proof even if almost every self-reduction preserves it. Conversely a large minimum kill set does not by itself quantify survival probability under a structured distribution.

The next scientific object should therefore be a **survival curve** or a theorem directly bounding `SURV_P` under the exact self-reduction distribution.

Candidate exact questions:

```text
Q1. For a polynomial-size B2/ER3 proof P on the frozen NW family,
    how large can Pr[b_sem(P|rho) and d_sem(P|rho) collapse] be
    under the source self-reduction?

Q2. Can a polynomial-size proof concentrate almost all of its F3 inversion
    complexity behind a polynomial-size or constant-size set of kill variables?

Q3. Does NW expansion force any sufficiently large inversion structure to be
    distributed across many independently surviving neighborhoods?

Q4. Can one construct an explicit unrestricted B2 escape whose pre-restriction
    F3 complexity is large but whose semantic crossing skeleton systematically
    collapses under the heavy-width self-reductions?
```

Q3 is the hoped-for positive route; Q4 is the adversarial route. Neither is assumed.

---

## 7. Exact next gate

```text
F3D_D0_BD_PLUS_RESTRICTION_SIZE_ROUTE = REFUTED
F3D_D1_SEMANTIC_RESIDUAL_CLASSIFIER   = NEXT
F3D_D2_SOURCE_SELF_REDUCTION_MODEL    = NEXT
F3D_D3_RESTRICTION_RESILIENCE_THEOREM = OPEN
F3D_D4_EXPLICIT_COLLAPSE_ESCAPE       = OPEN
ISSUE_217_FULL_ER3                    = OPEN
P_VS_NP                               = OPEN
```

### D1 implementation requirement

For finite fixtures, implement exact truth-table residual semantics for small macro DAGs and classify each residual function as:

```text
CONSTANT
LOCAL_TO_V_i
CROSSING
```

The finite implementation is only a mechanics checker. The asymptotic F3-D result still requires a proof or counterfamily.

---

## 8. Claim firewall

```text
ONE_VARIABLE_COLLAPSE_COUNTERFAMILY
!=
SOKOLOV_SELF_REDUCTION_COLLAPSES_REAL_HARD_FAMILY

ABSTRACT_LOCALITY_HYPERGRAPH_BARRIER
!=
UNRESTRICTED_ER3_LOWER_BOUND

SURVIVAL_PROBABILITY_UNDER_DEFINED_DISTRIBUTION
!=
HEURISTIC_CONFIDENCE

F3D_RESTRICTION_RESILIENCE
!=
P_VS_NP_RESOLUTION
```
