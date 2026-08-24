# C025-E2R-L1F — Crossing-extension elimination tradeoff

**Status:** `PROVED_IN_RESTRICTED_SCOPE__PROVIDER_PASS`.

**Scope firewall:** this is a tradeoff for the direct NW-parity family and its local-functional encoding. It does **not** prove a superpolynomial lower bound for unrestricted ER3 extension count and it does not resolve Issue #217.

## 1. Setup

A frozen B2 extension is

```text
e <-> (a AND b)
```

with clauses

```text
(~e OR a)
(~e OR b)
(e OR ~a OR ~b).
```

Call `e` **crossing** when its transitive root support is not contained in any single NW neighborhood. Local extensions are treated as free source variables in the functional encoding.

A local extension cannot depend on a crossing ancestor: support is the union of ancestor supports, so once neighborhood cover exceeds one it can never return to one along an extension-dependency edge.

Hence crossing variables may be eliminated in reverse introduction order without destroying the already-local extension definitions that remain.

Throughout this note `S` means **total proof-line volume including all used input/extension axioms** after reachability pruning. If a presentation stores definitions separately, add their explicit three-clause volume before applying the bound.

## 2. Clause expansion for one eliminated extension

For a clause `C` not containing both `e` and `~e`, define `EXP_e(C)` after replacing `e` by `(a AND b)`:

- if `e` does not occur, `EXP_e(C)={C}`;
- if `C = A OR e`,

```text
EXP_e(C) = {A OR a, A OR b};
```

- if `C = A OR ~e`,

```text
EXP_e(C) = {A OR ~a OR ~b}.
```

Duplicates are canonicalized and tautological clauses may be deleted.

Thus every old proof line produces at most two non-tautological clauses. The three defining axioms of `e` expand to tautologies and disappear.

## 3. Resolution-step simulation

### Pivot different from `e`

Suppose

```text
P = A OR y
Q = B OR ~y
R = A OR B
```

with `y != e`.

For each non-tautological clause in `EXP_e(R)`, resolve the corresponding clauses in `EXP_e(P)` and `EXP_e(Q)` on `y`.

There are only three occurrence states of `e` in each context: absent, positive, negative.

- absent/absent: one ordinary Resolution step;
- positive/absent or absent/positive: resolve the `a` copies and the `b` copies, at most two steps;
- negative/absent or absent/negative: one step;
- positive/positive: two matched steps (`a` with `a`, `b` with `b`);
- negative/negative: one step;
- positive/negative or negative/positive: the old resolvent contains both `e` and `~e` and is tautological, so no target line is required.

### Pivot equal to `e`

From

```text
A OR e
B OR ~e
```

the expansion contains

```text
A OR a
A OR b
B OR ~a OR ~b.
```

Resolve first on `a`:

```text
A OR B OR ~b,
```

then on `b` with `A OR b`:

```text
A OR B.
```

Thus an `e`-pivot inference is simulated by at most two ordinary Resolution steps.

## 4. One-gate elimination lemma

Let `pi` be a Resolution derivation over a CNF containing a topologically last crossing definition `e <-> (a AND b)`, with no later surviving definition depending on `e`.

Then `e` and its three defining clauses can be eliminated, producing a Resolution derivation over the remaining variables with

```text
|pi_without_e| <= 2 |pi|
```

up to tautology/duplicate deletion and ordinary identifier encoding overhead.

The argument is constructive: process the old derivation in order and emit at most two expanded clauses for every old line using the simulations above.

## 5. t-gate elimination theorem

Let `t` be the number of crossing extension variables in a B2/ER3 refutation and `S` its total proof-line volume.

Eliminate crossing variables in reverse introduction order. Local descendants of a crossing variable cannot exist, and later crossing variables have already been eliminated. Repeating the one-gate lemma gives a local-only Resolution proof of size

```text
S_local <= S * 2^t.
```

After identifying duplicate local-function variables by literal substitution, every remaining root/local axiom is contained in the NW functional encoding used by the heavy-width lower bound. Therefore, if every Resolution refutation of that functional encoding has size at least `L`, then

```text
S * 2^t >= L.
```

Equivalently,

```text
t >= log2(L/S).
```

This is the first proof-sensitive crossing-budget tradeoff. It does not use raw neighborhood cover.

## 6. Polynomial-input parameter regime

Use the formal source heavy-width theorem together with its random boundary-expander lemma, rather than only the maximal-degree corollary.

Fix `0 < delta < 1` and put

```text
m = n^(2-delta).
```

Choose a sufficiently large fixed constant `C` and

```text
Delta = C ln n.
```

Choose a sufficiently small fixed `xi>0` and a fixed `chi>1` with

```text
xi ln chi >= 2,
2 Delta >= 4 ln m,
```

and set the source expansion-loss parameter `epsilon=2xi`. The random-graph lemma then gives, with high probability,

```text
r = n/(Delta chi) = Theta(n/log n)
```

and boundary expansion `(1-epsilon)Delta` after matching notation.

Choose `xi` small enough that

```text
2^(6 epsilon Delta) <= n^(delta/2).
```

Parity on `Delta` variables is `(1/4,3 epsilon Delta)`-balanced whenever `3 epsilon < 1`, because after fixing fewer than all inputs the remaining parity is exactly balanced.

The formal heavy-width theorem therefore gives

```text
log L
  >= Omega(epsilon^5 * r^2 /(2^(6 epsilon Delta) * m))
  >= Omega(n^(delta/2)/polylog(n)).
```

The direct truth-table CNF has explicit encoded length

```text
N = O(m * 2^Delta * Delta * log n) = n^D polylog(n)
```

for a fixed constant `D = 2-delta + C ln 2` under ordinary binary literal identifiers. Hence there is a fixed `alpha>0` such that, for all sufficiently large members of the existential hard family,

```text
log L >= N^alpha.
```

For every fixed polynomial bound `S <= N^q`, the term `log S=O(log N)` is negligible, so

```text
t >= log2(L/S) >= Omega(N^alpha).
```

Thus a polynomial-size B2/ER3 refutation of this family cannot escape the NW-local lower bound using `o(N^alpha)` crossing extensions.

This is a **polynomial crossing-count lower bound**, not a superpolynomial one.

## 7. Provider replay

Authoritative finite-mechanics replay:

```text
repo       = Hawkar-usls/Janus-Fundamentum
branch     = c025-policy0b-fair-reason
workflow   = Validate C025 Fair Scheduler and Reasons
run        = 32746842601
job        = 97494297207
conclusion = SUCCESS
```

PASS gates:

```text
C025_E2R_L1F_NON_E_PIVOT_ALL_POLARITY_CASES
C025_E2R_L1F_E_PIVOT_TWO_STEP_SIMULATION
C025_E2R_L1F_EXTENSION_DEFINITION_EVAPORATION
C025_E2R_L1F_ONE_GATE_LINE_MULTIPLIER_LE_2
C025_E2R_L1F_LOCAL_DESCENDANT_OF_CROSSING_REJECTED_BY_SUPPORT
```

CI validates finite translation mechanics only. The asymptotic lower bound uses the external heavy-width theorem plus the parameter map above.

## 8. Why this still does not close #217

The tradeoff permits polynomially many crossings:

```text
t = N^alpha, N^(alpha+1), ...
```

Therefore it does not rule out a polynomial-size unrestricted ER3/B2 refutation.

It does remove a large class of possible escapes:

```text
O(log N) crossings        -> insufficient
polylog(N) crossings      -> insufficient
N^beta crossings          -> insufficient for every beta<alpha
```

for the frozen hard-family parameters.

The next gate is to ask whether the generic `2^t` elimination loss can be improved for a structurally restricted crossing circuit, or whether an explicit B2 construction forces exponential CNF expansion and proves that the generic factor is qualitatively unavoidable.

## 9. Exact status

```text
L1F_C_ONE_GATE_CNF_EXPANSION          = PROVED
L1F_C_RESOLUTION_STEP_SIMULATION      = PROVED__PROVIDER_PASS
L1F_C_T_GATE_ELIMINATION              = PROVED
L1F_D_SIZE_CROSSING_TRADEOFF          = PROVED_FROM_SOURCE_LOWER_BOUND
L1F_D_POLYNOMIAL_CROSSING_LOWER_BOUND = PROVED_IN_RESTRICTED_SCOPE
L1F_E_SUPERPOLY_CROSSING_LOWER_BOUND  = OPEN
ISSUE_217_FULL_ER3_EXTENSION_COUNT     = OPEN
P_VS_NP                                = OPEN
```

## 10. Hard laws

```text
ONE_CROSSING_EXTENSION_COSTS_AT_MOST_FACTOR_2_UNDER_EXACT_ELIMINATION
POLYNOMIAL_CROSSING_LOWER_BOUND != SUPERPOLYNOMIAL_EXTENSION_LOWER_BOUND
LOCAL_FUNCTIONS_FREE_IN_SOURCE_ENCODING != CROSSING_FUNCTIONS_FREE
FINITE_CI_REPLAY != ASYMPTOTIC_SOURCE_THEOREM
CROSSING_EXISTENCE != DETERMINISTIC_CROSSING_DISCOVERY
P_VS_NP = OPEN
```
