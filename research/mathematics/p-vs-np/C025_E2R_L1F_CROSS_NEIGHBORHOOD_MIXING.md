# C025-E2R-L1F — Cross-neighborhood mixing escape measure

**Status:** `MIXING_MEASURE_FROZEN`; `RAW_COVER_COUNT_REFUTED_AS_SUPERPOLY_ROUTE`; heavy-width contamination tradeoff `OPEN`.

**Scope firewall:** this note studies the exact escape from the proved NW-neighborhood-local ER3 lower bound. It does not establish a lower bound for unrestricted ER3.

## 1. Neighborhood-cover number

Let the fixed NW graph have output neighborhoods

```text
Vars_1,...,Vars_m.
```

For a nonempty root-support set `S`, define the analytical measure

```text
cover_G(S) = min |I|
             such that S subseteq union_{i in I} Vars_i.
```

For a proof literal/extension `z`, write

```text
cover_G(z)=cover_G(support(z)).
```

A variable is NW-neighborhood-local exactly when `cover_G(z)=1`.

### Complexity firewall

Exact set cover is an optimization problem and is not assumed to be cheaply computable by Policy-0B. `cover_G` is an **analysis/lower-bound measure**, not a solver primitive.

```text
ANALYTIC_MEASURE != FREE_RUNTIME_OPERATION
```

## 2. Restriction monotonicity

If a root restriction `rho` is applied, previous work gives

```text
S_rho(z) subseteq S(z) minus dom(rho) subseteq S(z).
```

Set-cover number is monotone under subset inclusion, so

```text
cover_G(S_rho(z)) <= cover_G(S(z)).
```

Thus root restrictions cannot increase neighborhood cover.

## 3. Conjunction subadditivity

For a B2 extension

```text
e <-> (a AND b)
```

we have

```text
S(e)=S(a) union S(b).
```

Take minimum covers `I_a,I_b` for the two supports. Their union covers `S(e)`, hence

```text
cover_G(e) <= cover_G(a)+cover_G(b).
```

This is an exact structural inequality; it does not say the minimum cover is additive.

## 4. Crossing gates

Call an extension gate **crossing** if

```text
cover_G(e) > 1.
```

For a target extension `e`, let `T(e)` be the set of crossing extension nodes in its transitive dependency cone and put

```text
t(e)=|T(e)|.
```

Assume every relevant root variable belongs to at least one NW neighborhood; isolated irrelevant roots can be deleted from the direct formula.

### Lemma L1F.1 — crossing skeleton bound

```text
cover_G(e) <= t(e)+1.
```

**Proof sketch.** Contract every maximal connected dependency sub-DAG containing no crossing gate into a local source component. Such a component is supported inside one neighborhood: if its output is local, all ancestor supports are subsets of that local output support because frozen transitive support is defined by union and never shrinks during extension composition. The remaining connected dependency DAG has `t` binary crossing nodes and `l` local source components. A connected DAG with one sink, `t` internal nodes of indegree at most two and `l` sources has at least `t+l-1` edges and at most `2t` incoming edges, so `l<=t+1`. Choosing one neighborhood for each local source component covers the target support. Therefore `cover_G(e)<=l<=t+1`. □

Consequently

```text
t(e) >= cover_G(e)-1.
```

## 5. Why raw cover/crossing cardinality is still insufficient

The NW graph has only `m` output neighborhoods, so trivially

```text
cover_G(e) <= m.
```

In the heavy-width family

```text
m=n^(2-delta),
N_n=exp(O(log^(2-delta)n)).
```

Thus `m` is far below the superpolynomial-in-`N_n` extension count needed to attack global Issue #217. A lower bound obtained only from

```text
K >= t >= cover_G(e)-1
```

can therefore never yield the required conclusion for this family.

### Barrier L1F.2

Neighborhood-cover cardinality and the bare number of regions mixed by a single extension are not sufficient superpolynomial extension-count invariants.

This is analogous to the earlier semantic-class-count barrier: the number of available regions is itself too small.

## 6. What remains potentially powerful

The source heavy-width proof is not merely counting neighborhoods. It measures how Resolution clauses interact with a combinatorial graph structure under restrictions.

The surviving target is therefore a **contamination tradeoff**:

> quantify how much one crossing extension gate can reduce/destroy the heavy-width obstruction.

Desired form:

```text
HW_after >= HW_before - damage(e)
```

with a cumulative bound over `t` crossing gates strong enough to imply

```text
small t => still-large Resolution proof.
```

The measure must charge recursive reuse: one crossing extension may later feed many gates.

## 7. New exact gates

```text
L1F-A cover monotonicity/subadditivity        = PROVED
L1F-B crossing-skeleton cover bound           = PROVED
L1F-B2 raw cover-count superpoly route         = REFUTED
L1F-C heavy-width contamination per crossing  = NEXT / OPEN
L1F-D proof-size vs crossing-budget tradeoff  = OPEN
L1F-E global consequence                      = NOT ESTABLISHED
```

## 8. Hard laws

```text
ANALYTIC_COVER_NUMBER != CHEAP_SOLVER_PRIMITIVE
LARGE_NEIGHBORHOOD_COVER != SUPERPOLYNOMIAL_EXTENSION_COUNT
CROSSING_GATE_COUNT != HEAVY_WIDTH_DAMAGE_WITHOUT_A_THEOREM
NW_LOCAL_LOWER_BOUND != FULL_ER3_LOWER_BOUND
P_VS_NP = OPEN
```
