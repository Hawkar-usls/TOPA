# C025 — Akinator: deterministic live-width path-DP certificate lane

Status: **POSITIVE LARGE-SUPPORT CERTIFICATE THEOREM / LIVE-WIDTH FRONTIER OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Motivation

The ROBDD lane proves that large root support need not imply a large exact certificate, but adaptive variable-order discovery has a general hardness barrier.

This note removes variable-order search entirely for a second restricted lane.

A serialized B2 macro is already an acyclic sequence of local gate constraints. We derive a path decomposition **deterministically from the gate trace itself** and run exact dynamic programming over its live boundary.

No semantic oracle, heuristic ordering, model counting oracle, or backtracking is used to discover the decomposition.

---

## 1. B2 gate-constraint graph

For every extension definition

`e := a AND b`

with literals `a,b`, create the exact local Boolean relation

`e = value(a) AND value(b)`.

The relation touches at most the three underlying Boolean variables

`{e, var(a), var(b)}`.

For a selected output macro `g`, retain only the transitive dependency cone of `g` and its gate constraints.

Let the frozen topological gate order be

`G_1, G_2, ..., G_T`.

The order is part of the serialized B2 certificate and is not optimized after the fact.

---

## 2. Deterministic live intervals

For every variable `v` occurring in the dependency cone, define

- `first(v)` = first gate index whose constraint contains `v`;
- `last(v)` = last gate index whose constraint contains `v`.

Define the live bag at gate `t`:

`L_t := {v : first(v) <= t <= last(v)}`.

Every gate's variables are in its own bag.

For each variable, the set of bag indices containing it is exactly the interval

`[first(v), last(v)]`.

Hence `(L_1,...,L_T)` is a valid path decomposition of the gate-constraint primal graph:

1. every vertex occurs;
2. every edge created by a gate relation is covered by the gate's bag;
3. bags containing each vertex are contiguous.

No decomposition search is required.

Define the deterministic live width

`lambda(D) := max_t |L_t| - 1`.

The bags, first/last table, and `lambda` are computable exactly in polynomial time from the serialized gate trace.

---

## 3. Exact residual-survival DP

Let `rho` be a supplied partial assignment to root variables in the cone. To test whether output `g` can equal a bit `b`, add the unary conditions from `rho` plus `g=b`.

Run a standard exact path-DP:

- at bag `L_t`, retain the assignments to live variables that can be extended to satisfy all gate constraints processed through `t`;
- reject an assignment immediately if it violates `G_t` or a relevant unary condition;
- project forgotten variables when passing to the next bag;
- introduce newly live variables by both Boolean values;
- canonicalize equal boundary assignments.

There are at most

`2^(lambda+1)`

assignments per bag.

Transition and gate checks use only polynomial bit work per state.

Therefore feasibility of `g=b` is decidable in

`poly(T, certificate_bytes) * 2^O(lambda)`.

Run once for `b=0` and once for `b=1`.

The residual macro is nonconstant iff both runs are feasible.

By storing one predecessor pointer per retained state, explicit root witnesses for both output values are reconstructed with only polynomial overhead in the DP table size.

Thus:

`LIVE_WIDTH_EXACT_SURVIVAL = poly(T) * 2^O(lambda)`.

---

## 4. Input-relative polynomial gate

A claim of polynomial time in original encoded input length `N` requires fixed universal constants such that

- dependency-cone bytes `T_bytes <= N^c1`;
- `lambda <= c2*log_2 N`.

Then

`2^O(lambda) = N^O(1)`

with a universal fixed exponent, and exact survival/witness discovery is polynomial in original `N`.

If `lambda/log N` is unbounded, the exponent is not universally fixed.

New hidden-exponent law:

`2^O(LIVE_WIDTH) IS POLYNOMIAL_IN_N ONLY UNDER A_UNIVERSAL_O(LOG_N)_LIVE_WIDTH_BOUND`.

---

## 5. Large support with constant live width — parity chain

Use the frozen linear B2 implementation of running parity/XOR.

At stage `i`, the local gate block needs only:

- the previous parity state;
- the new root `x_i`;
- a constant number of temporary B2 extension variables;
- the new parity state passed to the next stage.

Every old root disappears after its local stage and every temporary disappears after the XOR block.

Therefore the live width is bounded by a universal constant under the natural serialized gate order, while the final macro has root support `n`.

Hence:

`LARGE_ROOT_SUPPORT != LARGE_LIVE_WIDTH`.

This lane can therefore handle exactly the kind of polynomially large support forced by the bounded-support ER3 elimination theorem when the macro has streaming/finite-state structure.

---

## 6. Polynomial candidate scan in the low-live-width lane

Suppose a proof state contains `V(N)<=N^a` explicit macros/literals and each candidate dependency cone is polynomially serialized.

Enumerate all B2 one-step candidates:

- `NOT a`: `O(V)`;
- `a AND b`: `O(V^2)`.

For each candidate:

1. form/reuse its dependency cone;
2. recompute exact first/last live intervals from the deterministic gate trace;
3. compute `lambda` without semantic search;
4. if `lambda > c*log N`, reject from the low-width lane without running exponential DP;
5. otherwise run exact DP and export the first canonical 0/1 witness pair if nonconstant.

For a frozen universal constant `c`, this is a deterministic polynomial scan in original `N`, assuming the explicit candidate cone/state bytes are polynomial in `N`.

No heuristic candidate score is used.

This proves local **survival-certificate discovery**, not global proof progress.

---

## 7. Forced-live-width counterfamily for a given B2 dependency architecture

Large live width can be forced by fan-out dependencies even when every gate has fan-in two.

Construct roots `(x_i,y_i)` and first-layer extensions

`e_i := x_i AND y_i`, for `i=1,...,n`.

For every pair `i<j`, create

`g_{i,j} := e_i AND e_j`.

Finally combine all `g_{i,j}` by a B2 AND aggregation tree so every pair gate lies in the final output's dependency cone.

The total DAG size is `O(n^2)`.

Consider **any topological gate order of this fixed dependency DAG**. Let `e_j` be the last first-layer `e`-gate to be created. Immediately when `e_j` becomes available, every earlier `e_i` must still be live because the child gate `g_{i,j}` could not have been executed before `e_j` existed and is still in the dependency cone.

Thus at least `n` first-layer extension values are simultaneously live at that point, up to the precise before/after-gate bag convention.

Therefore

`lambda = Omega(n) = Omega(sqrt(T))`

for every topological serialization of this fixed architecture.

### Critical ceiling

The final Boolean function of this particular redundant architecture is semantically much simpler than its DAG suggests; an alternative B2 representation may avoid the large live width.

So this proves

`SMALL_OR_SIMPLE_SEMANTIC_FUNCTION != SMALL_LIVE_WIDTH_FOR_EVERY_GIVEN_DAG`

only as a **representation-architecture barrier**.

It does not prove that the function intrinsically requires large live width across all equivalent B2 circuits.

---

## 8. Representation rewrite is a new discovery resource

The counterfamily exposes another possible escape:

> rewrite the macro into an equivalent low-live-width B2 DAG before running the DP.

That rewrite cannot be assumed free.

To use it in a polynomial Akinator theorem, the selector must provide:

1. a deterministic polynomial rewrite constructor;
2. a polynomially checkable equivalence/provenance certificate;
3. polynomial total intermediate bytes;
4. a universal bound on resulting live width;
5. no backtracking through exponentially many rewrite choices.

Hence:

`LOW_WIDTH_EQUIVALENT_REPRESENTATION_EXISTS != CHEAP_LOW_WIDTH_REWRITE_DISCOVERY`.

---

## 9. Relation to ROBDD residual frontier

ROBDD residual frontier and live-width DP are two views of the same general resource: **how much boundary information must survive a cut**.

- ROBDD: boundary state is the exact residual Boolean function under a root-prefix cut.
- LIVE-DP: boundary state is an assignment to simultaneously live circuit variables under a gate-trace cut.

Both have exact exponential dependence on a boundary parameter.

The live-width lane avoids variable-order optimization but may pay for syntactic circuit liveness; the ROBDD lane can quotient more semantic states but may pay for root-order discovery.

Neither dominates the other universally.

---

## 10. Current exact next gate

The next proof-carrying selector layer should combine these without heuristic choice:

`BOUNDARY_CERTIFICATE := (representation_type, deterministic_decomposition, width_bound, exact_state_table_provenance)`.

Required theorem:

> At every nonterminal target state, a polynomially enumerable candidate has a deterministically constructible boundary certificate of width `O(log N)` **and** a globally sound proof-progress certificate.

The survival half is now solved in the low-width lane.

The **global progress half remains open**.

---

## 11. Claim ledger

`GATE_TRACE_LIVE_BAGS_FORM_A_VALID_PATH_DECOMPOSITION = PROVED_IN_SCOPE`

`LIVE_WIDTH_EXACT_SURVIVAL_TIME = poly(T)*2^O(lambda)`

`LAMBDA_O_LOG_N_WITH_POLY_TRACE_IMPLIES_POLY_SURVIVAL_DISCOVERY = PROVED_IN_SCOPE`

`PARITY_CHAIN_LARGE_SUPPORT_CONSTANT_LIVE_WIDTH = PROVED_IN_SCOPE`

`PAIR_FANOUT_ARCHITECTURE_FORCES_LAMBDA_OMEGA_SQRT_T = PROVED_FOR_FIXED_DAG_ARCHITECTURE`

`EQUIVALENT_LOW_WIDTH_REWRITE_DISCOVERY = OPEN`

`UNIVERSAL_O_LOG_N_BOUNDARY_CERTIFICATE = OPEN`

`GLOBAL_PROGRESS_CERTIFICATE = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 12. Laws

- `ROOT_SUPPORT_WIDTH != LIVE_BOUNDARY_WIDTH`
- `DETERMINISTIC_GATE_TRACE_CAN_GENERATE_A_PATH_DECOMPOSITION_WITHOUT_SEARCH`
- `LOW_LIVE_WIDTH_GIVES_EXACT_POLYNOMIAL_SURVIVAL_FOR_LAMBDA_O_LOG_N`
- `SIMPLE_SEMANTICS != LOW_WIDTH_FOR_A_GIVEN_REDUNDANT_DAG`
- `LOW_WIDTH_EQUIVALENT_REPRESENTATION_EXISTS != CHEAP_REWRITE_DISCOVERY`
- `SURVIVAL_CERTIFICATE != GLOBAL_PROGRESS_CERTIFICATE`
