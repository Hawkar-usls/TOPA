# C025-E2R-L1F — Crossing-extension elimination tradeoff

**Status:** `ONE_GATE_ELIMINATION_PROVED`; asymptotic crossing-budget consequence pending provider replay.

**Scope firewall:** this is a tradeoff for the direct NW-parity family and its local-functional encoding. It does **not** prove a lower bound for unrestricted ER3 with polynomially many crossing extensions, and it does not resolve Issue #217.

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

Thus every old proof line produces at most two non-tautological clauses.

The three defining axioms of `e` expand to tautologies and disappear.

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

up to deletion of tautological/duplicate lines and ordinary representation overhead.

The argument is constructive: process the old derivation in order and emit at most two expanded clauses for every old line using the simulations above.

## 5. t-gate elimination theorem

Let `t` be the number of crossing extension variables in a B2/ER3 refutation and `S` its proof-line count.

Eliminate crossing variables in reverse introduction order. Local descendants of a crossing variable cannot exist, and later crossing variables have already been eliminated. Repeating the one-gate lemma gives a local-only Resolution proof of size

```text
S_local <= S * 2^t.
```

After identifying duplicate local-function variables by literal substitution, every remaining root/local axiom is an axiom of the NW functional encoding used by the heavy-width lower bound. Therefore, if every Resolution refutation of that functional encoding has size at least `L`, then

```text
S * 2^t >= L.
```

Equivalently,

```text
t >= log2(L/S).
```

This is the first proof-sensitive crossing-budget tradeoff. It does not use raw neighborhood cover.

## 6. Polynomial-input parameter regime

The source heavy-width theorem is more general than the maximal-degree corollary. Combine its formal expander theorem with the random-graph existence lemma using

```text
m = n^(2-delta),
Delta = C log n
```

for a sufficiently large fixed `C`, and choose a sufficiently small fixed expansion-loss parameter `epsilon>0` so that the factor `2^(O(epsilon Delta))` is `n^q` with `q<delta`.

For parity base functions, the balancedness condition survives every restriction fixing fewer than all `Delta` inputs.

The direct truth-table CNF has

```text
N = O(m * 2^Delta * Delta * log n) = n^O(1).
```

The heavy-width theorem then yields an existential random-graph family with local-functional Resolution lower bound

```text
L = exp(n^Omega(delta) / polylog(n)).
```

(after shrinking constants in the exponent as needed).

Hence, for every polynomial-size B2/ER3 proof `S=N^O(1)`,

```text
t >= Omega(log L) = n^Omega(delta) = N^alpha
```

for some fixed `alpha>0` depending on the frozen constants.

So a polynomial-size refutation of this family cannot escape the NW-local lower bound using only `o(N^alpha)` crossing extensions.

This is a **polynomial crossing-count lower bound**, not a superpolynomial one.

## 7. Why this still does not close #217

The tradeoff permits

```text
t = N^alpha, N^(alpha+1), ...
```

which is still polynomial in the input length. Therefore it does not rule out a polynomial-size unrestricted ER3/B2 refutation.

It does, however, remove a large class of possible escapes:

```text
O(log N) crossings        -> insufficient
polylog(N) crossings      -> insufficient
N^beta crossings          -> insufficient for every beta<alpha
```

for the frozen hard-family parameters.

The next gate is to improve the elimination cost per crossing from exponential in `t` to a subexponential/polynomial function for a structurally restricted crossing skeleton, or to exhibit an explicit crossing construction showing that such an improvement is impossible.

## 8. Exact status

```text
L1F_C_ONE_GATE_CNF_EXPANSION          = PROVED
L1F_C_RESOLUTION_STEP_SIMULATION      = PROVED
L1F_C_T_GATE_ELIMINATION              = PROVED
L1F_D_SIZE_CROSSING_TRADEOFF          = PROVED_FROM_SOURCE_LOWER_BOUND
L1F_D_POLYNOMIAL_CROSSING_LOWER_BOUND = CLAIM_PENDING_PROVIDER_REPLAY
L1F_E_SUPERPOLY_CROSSING_LOWER_BOUND  = OPEN
ISSUE_217_FULL_ER3_EXTENSION_COUNT     = OPEN
P_VS_NP                                = OPEN
```

## 9. Hard laws

```text
ONE_CROSSING_EXTENSION_CAN_BUY_AT_MOST_FACTOR_2_UNDER_EXACT_ELIMINATION
POLYNOMIAL_CROSSING_LOWER_BOUND != SUPERPOLYNOMIAL_EXTENSION_LOWER_BOUND
LOCAL_FUNCTIONS_FREE_IN_SOURCE_ENCODING != CROSSING_FUNCTIONS_FREE
CROSSING_EXISTENCE != DETERMINISTIC_CROSSING_DISCOVERY
P_VS_NP = OPEN
```
