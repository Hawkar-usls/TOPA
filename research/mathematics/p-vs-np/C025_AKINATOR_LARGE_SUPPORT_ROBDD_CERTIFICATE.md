# C025 — Akinator: large-support proof-carrying ROBDD certificate lane

Status: **POSITIVE LOCAL CERTIFICATE THEOREM + EXACT ORDER-FRONTIER BARRIER**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Goal

The bounded-support elimination theorem forces any hypothetical polynomial-size ER3 escape on the frozen hard family to contain a macro with transitive syntactic root support `Omega(N^eta)`.

Large support alone, however, does not imply that the macro requires an exponentially large exact semantic representation. Parity is the canonical example: it has large support but admits a linear-state recurrence.

This note freezes a non-heuristic large-support certificate language based on a **reduced ordered binary decision diagram** (ROBDD) under an explicit root-variable order.

The result has two parts:

1. a positive theorem: if the ROBDD certificates remain polynomial in original input length, exact macro construction, restriction, survival verification, and witness discovery are deterministic polynomial-time operations with no semantic oracle and no backtracking;
2. an exact barrier: a small B2 DAG can have exponentially large ROBDD under a bad fixed order, and the exponential is exactly witnessed by the number of distinct residual functions across an order cut.

No claim is made that a polynomial ROBDD order exists for every useful macro.

---

## 1. Frozen certificate object

Fix an explicit order of original root variables

`x_1 < x_2 < ... < x_n`.

An ROBDD certificate for a Boolean macro `g` contains:

- two terminals `0,1`;
- a root node ID;
- for each nonterminal node: `(var_index, low_child, high_child)`;
- child order strictly later than parent variable order;
- reduction conditions:
  - `low_child != high_child`;
  - no two nonterminal nodes share the same triple `(var_index, low_child, high_child)`;
- provenance binding the root to the represented B2 macro.

The order is part of the frozen selector protocol. No heuristic order search is silently permitted.

---

## 2. Deterministic verification

A verifier checks in polynomial time in certificate bytes:

1. graph acyclicity and root reachability;
2. ordered-variable condition on every edge;
3. both reduction conditions;
4. canonical node IDs/hash after sorting triples;
5. provenance against the parent certificates and B2 operation.

For a root literal, the canonical ROBDD is immediate.

For `e := NOT a`, the verifier deterministically complements terminal values and reduces/canonicalizes the resulting DAG.

For `e := a AND b`, the verifier recomputes the standard memoized pair construction:

`APPLY_AND(u,v)`

on node pairs `(u,v)`, splits on the earlier current variable, recursively computes low/high pairs, and interns the resulting triple in a deterministic unique table.

At most `|D_a|*|D_b|` node pairs are visited before reduction. Deterministic sorting/deduplication keeps the bit complexity polynomial in the explicit input and output diagram sizes.

Therefore:

`ROBDD_GATE_CERTIFICATE_VERIFICATION = POLYNOMIAL_IN_EXPLICIT_PARENT_AND_CHILD_DIAGRAM_BYTES`.

This is an exact structural verification claim, not a semantic sampling claim.

---

## 3. Deterministic discovery for accepted B2 gates

The same algorithms construct the child certificate rather than merely verify it.

For maximum current certificate size `B`:

- `NOT`: `poly(B)`;
- `AND`: `poly(B^2)` worst-case pair exploration plus deterministic reduction.

If a selector state has `V` represented literals/macros, all ordered AND pairs are enumerable in `O(V^2)`.

Thus if

`V(N) <= N^a` and `B(N) <= N^b`

for fixed universal constants `a,b`, one complete deterministic scan of all one-step B2 candidates and their ROBDD construction is polynomial in original encoded `N`.

No SAT solver, model counter, heuristic score, or backtracking is needed to construct these certificates.

Important law:

`POLYNOMIAL_IN_BDD_BYTES != POLYNOMIAL_IN_ORIGINAL_N`

unless a polynomial input-relative bound on the BDD bytes is proved.

---

## 4. Exact residual survival

Given a partial root restriction `rho`, restrict the ROBDD by:

- following the selected edge at every node whose variable is assigned by `rho`;
- retaining unassigned nodes;
- reducing/canonicalizing the residual DAG.

This is polynomial in the current diagram bytes and the restriction bytes.

For a reduced diagram:

- root `0` means residual constant false;
- root `1` means residual constant true;
- any nonterminal root means the residual function is nonconstant.

If nonconstant, both terminals are reachable from the root. A deterministic DFS choosing low before high produces one root-to-0 path and one root-to-1 path; skipped/unmentioned roots are filled by a frozen canonical value. These yield explicit 0/1 witness assignments.

Therefore:

`ROBDD_RESIDUAL_SURVIVAL_DISCOVERY = POLYNOMIAL_IN_EXPLICIT_DIAGRAM_BYTES`.

This bypasses the general SAT-hard survival search only on the restricted representation lane where the ROBDD is already polynomially available.

---

## 5. Large support is compatible with a small certificate

Parity on `n` roots has support size `n`, yet under the natural root order the residual state after every prefix is determined by only the accumulated parity bit.

Thus a leveled ordered decision DAG needs at most two nonterminal semantic states per level: even and odd prefix parity.

After reduction, the ROBDD has `O(n)` nodes.

Hence:

`LARGE_ROOT_SUPPORT != LARGE_ROBDD_CERTIFICATE`.

This is why the previous support lower bound does not by itself kill the polynomial-Akinator route.

---

## 6. Exact residual-frontier parameter

For a Boolean function `f` and frozen order `x_1,...,x_n`, define

`R_i(f)`

as the number of distinct residual Boolean functions obtained by assigning arbitrary values to the first `i` ordered roots and leaving the remaining roots free.

Define the frozen-order residual frontier width

`R_max(f) := max_i R_i(f)`.

### Theorem E — residual-frontier lower bound for ordered diagrams

After consuming the first `i` variables, two prefix assignments may reach the same reduced subgraph only if they induce exactly the same residual Boolean function.

Therefore every ordered decision DAG representing `f` must expose at least `R_i(f)` distinct semantic states/subgraphs across that cut, counting terminals. In particular:

`ROBDD_size(f) + 2 >= R_max(f)`

up to the convention of whether terminals are included in the size.

Thus an exponential residual frontier forces an exponential ROBDD certificate for that frozen order.

This is an exact combinatorial lower bound, not a heuristic score.

---

## 7. Counterfamily — tiny B2 DAG, exponential frozen-order ROBDD

Define

`EQ_n(X,Y) := AND_{j=1}^n (x_j <-> y_j)`.

There is an `O(n)` B2 AND/NOT extension DAG for `EQ_n`:

- each equivalence can be built with constant many AND-over-literal gates plus De Morgan negation;
- combine the equivalence literals in a linear AND chain.

Now freeze the order

`x_1, x_2, ..., x_n, y_1, y_2, ..., y_n`.

After assigning all `x` variables, each `n`-bit string `a` leaves the residual function

`AND_j (y_j = a_j)`.

Distinct strings `a != a'` produce distinct residual functions because they accept different unique `Y` assignments.

Hence

`R_n(EQ_n) = 2^n`.

By Theorem E, every ROBDD in this frozen order has exponential size.

Yet under the interleaved order

`x_1,y_1,x_2,y_2,...,x_n,y_n`,

only a constant-width state is needed: either all compared pairs agree so far, or failure is already permanent.

Therefore:

`SMALL_B2_DAG != SMALL_ROBDD_UNDER_AN_ARBITRARY_FIXED_ORDER`

and

`VARIABLE_ORDER_IS_A_COMPUTATIONAL_RESOURCE`.

---

## 8. Why this is the next hidden exponent

The ROBDD lane removes semantic-oracle search only if the residual frontier under the deterministically chosen order remains polynomial.

The exact local cost can be charged by

- total ROBDD bytes `B(N)`;
- maximum cut residual count `R_max`;
- candidate pair-product cost.

If `R_max(f_N)=2^{Omega(h(N))}`, the certificate route necessarily incurs that many semantic states for the frozen order.

The selector is not allowed to hide this by saying “choose a better order” unless the better order itself is found by a proved deterministic polynomial procedure.

New law:

`GOOD_ORDER_EXISTS != CHEAP_GOOD_ORDER_DISCOVERY`.

---

## 9. Proof-carrying order versus heuristic order

There are two scientifically admissible lanes:

### ORDER-FROZEN

A deterministic input-derived order is frozen before proof search. All cost and failures are charged to that order.

### ORDER-CERTIFIED

A certificate may advertise an order together with the ROBDD, but a polynomial Akinator claim additionally requires a deterministic polynomial algorithm that discovers the order/certificate. Cheap verification of an advertised good order is not enough.

Forbidden:

- genetic/order heuristics promoted to proof;
- “try many orders until one works” without charging the search;
- model ranking of orders as scientific authority;
- hiding an exponential number of attempted orders outside the proof trace.

---

## 10. What this solves and what remains open

Solved in this restricted lane:

- succinct exact representation can coexist with `Omega(N^eta)` root support;
- B2 NOT/AND certificate construction and verification are deterministic polynomial in explicit diagram sizes;
- exact residual survival and explicit 0/1 witness extraction are deterministic polynomial in diagram size;
- no semantic oracle is required once polynomial ROBDD certificates exist.

Still open:

1. polynomial ROBDD size for every useful selector macro;
2. deterministic polynomial discovery of a sufficiently good variable order if the frozen order fails;
3. universal next-step availability;
4. source-matched Sokolov restriction survival for the selected macro semantics;
5. a globally sound polynomially bounded progress potential;
6. total state/trace/certificate bytes polynomial in original `N`.

---

## 11. Next gate — residual-frontier/order selector

Freeze a deterministic order-generation rule and try to prove one of two outcomes:

### PASS route

Every nonterminal target state has a useful macro whose ROBDD under the frozen/generated order has polynomial residual frontier and whose accepted certificate decreases a global potential.

### FAIL route

Construct a source-matched family/state forcing superpolynomial `R_max` for every order reachable by the frozen deterministic order rule, or show that discovering a polynomial-frontier order itself reintroduces a hard search problem.

Do not claim order-independent OBDD hardness until proved.

---

## 12. Claim ledger

`LARGE_SUPPORT_ROBDD_CERTIFICATE_CONSTRUCTION = POLYNOMIAL_IN_EXPLICIT_DIAGRAM_BYTES`

`ROBDD_EXACT_RESIDUAL_SURVIVAL = POLYNOMIAL_IN_EXPLICIT_DIAGRAM_BYTES`

`PARITY_LARGE_SUPPORT_SMALL_ROBDD = PROVED_BY_TWO_STATE_RECURRENCE`

`RESIDUAL_FRONTIER_LOWER_BOUNDS_FROZEN_ORDER_ROBDD_SIZE = PROVED_IN_SCOPE`

`EQ_N_LINEAR_B2_DAG_EXPONENTIAL_X_THEN_Y_ROBDD = PROVED_IN_SCOPE`

`GOOD_VARIABLE_ORDER_DISCOVERY = OPEN`

`ORDER_INDEPENDENT_ROBDD_LOWER_BOUND_FOR_TARGET_NW_MACROS = NOT_PROVED`

`GLOBAL_PROGRESS = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 13. New laws

- `LARGE_SUPPORT != LARGE_STATE_SPACE`
- `DISTINCT_RESIDUAL_FUNCTIONS_ARE_THE_EXACT_ORDERED_STATE_RESOURCE`
- `SMALL_B2_DAG != SMALL_FROZEN_ORDER_ROBDD`
- `GOOD_ORDER_EXISTS != CHEAP_GOOD_ORDER_DISCOVERY`
- `PROOF_CARRYING_REPRESENTATION_SIZE_MUST_BE_CHARGED_IN_ORIGINAL_N`
- `EXACT_SURVIVAL != GLOBAL_PROGRESS`
