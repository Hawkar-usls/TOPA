# C025 — Akinator: OBDD order-discovery barrier

Status: **SOURCE-BOUND COMPLEXITY BARRIER + INTERNAL TRANSFER TO SELECTOR REQUIREMENTS**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

The large-support ROBDD certificate lane gives deterministic polynomial construction, verification, restriction, and exact survival **provided the relevant diagrams stay polynomially small under the chosen variable order**.

A tempting shortcut is:

> if the frozen order is bad, search for a better order.

That search must be charged.

---

## 1. External source result

Primary bibliographic result:

Beate Bollig and Ingo Wegener, **“Improving the Variable Ordering of OBDDs Is NP-Complete,”** IEEE Transactions on Computers 45(9), 993–1002, 1996. DOI: `10.1109/12.537122`.

Public bibliographic records identify the paper and its NP-completeness result. A contemporaneous paper by Bollig, Löbbing, and Wegener states in its abstract that computing an optimal variable ordering or improving a given OBDD ordering is NP-hard.

The source result concerns the general OBDD variable-ordering problem. It does **not** automatically prove hardness for the frozen NW-parity macro class or for a specially restricted deterministic order generator.

Source identity must be preserved:

`GENERAL_OBDD_ORDERING_HARDNESS != TARGET_NW_ORDERING_HARDNESS`.

---

## 2. Akinator consequence

The ROBDD lane has three logically distinct tasks:

1. verify a supplied ROBDD/order;
2. construct/restrict/combine ROBDDs once an order is fixed;
3. discover an order that keeps the required diagrams polynomially small.

Tasks 1–2 can be polynomial in explicit diagram bytes.

The external NP-hardness/NP-completeness result blocks the generic inference

`GOOD_ORDER_EXISTS => GOOD_ORDER_IS_CHEAPLY_DISCOVERABLE`.

Therefore any polynomial-Akinator theorem using adaptive ROBDD ordering must provide its **own target-specific deterministic polynomial order constructor** or prove that a frozen canonical order suffices.

A heuristic reordering engine, local search, simulated annealing, model ranking, or uncharged enumeration of orders cannot carry scientific authority in TOPA.

---

## 3. Exact relation to the internal EQ_n barrier

The internal family

`EQ_n(X,Y) = AND_j (x_j <-> y_j)`

has an `O(n)` B2 DAG.

Under order

`x_1,...,x_n,y_1,...,y_n`

the residual frontier after the X cut is `2^n`, forcing exponential ROBDD size.

Under interleaved order

`x_1,y_1,...,x_n,y_n`

the ROBDD is linear-size.

This finite/analytic counterfamily proves **order sensitivity** without using the external complexity theorem.

The Bollig–Wegener result adds a separate point: in the general OBDD representation, algorithmically finding/improving a good order is itself a hard optimization/decision task.

Do not conflate these:

- `EQ_n` = our explicit order-sensitivity theorem;
- Bollig–Wegener = external general order-discovery complexity theorem.

---

## 4. New exact selector gate

### ORDER-D1 — frozen-order lane

Provide a deterministic order derived directly from the input encoding and prove all useful selector macros have polynomial residual frontier under it.

### ORDER-D2 — target-specific adaptive lane

Provide a deterministic polynomial algorithm which, from the current proof state, constructs an order with polynomial ROBDD size for at least one certified-progress macro whenever such a step is required.

### ORDER-D3 — proof-carrying order is insufficient by itself

An advertised order plus a small ROBDD is cheaply verifiable, but that does not prove cheap discovery.

`SHORT_ORDER_CERTIFICATE != POLYNOMIAL_ORDER_SEARCH`.

### ORDER-D4 — total search accounting

Charge every attempted order and every temporary ROBDD created during reordering in original input length `N`.

---

## 5. Current front

The next route should avoid generic order optimization and instead search for a **compositional order/decomposition certificate** generated alongside the B2 macro itself.

Candidate structural resource:

`BOUNDARY_WIDTH`

across a decomposition/order cut, because the number of distinct residual functions is the actual ROBDD state count.

A promising proof-carrying object is therefore not merely `(macro, order)` but

`(macro, decomposition, boundary-state certificate)`

where:

- the decomposition is generated deterministically from parent certificates;
- boundary width is explicitly charged;
- exact residual states are deduplicated canonically;
- no search over exponentially many decompositions is hidden outside the trace.

No theorem that such a universally sufficient decomposition exists is claimed.

---

## 6. Claim ledger

`GENERAL_OBDD_VARIABLE_ORDER_IMPROVEMENT_NP_COMPLETE = SOURCE_BOUND_RESULT_BOLLIG_WEGENER_1996`

`GENERAL_OPTIMAL_OR_IMPROVED_ORDER_SEARCH_IS_NOT_A_FREE_SELECTOR_STEP = ESTABLISHED_BARRIER`

`TARGET_NW_MACRO_ORDER_DISCOVERY_NP_HARD = NOT_PROVED`

`FROZEN_ORDER_RESIDUAL_FRONTIER_BARRIER = PROVED_IN_INTERNAL_ROBDD_NOTE`

`COMPOSITIONAL_LOW_BOUNDARY_DECOMPOSITION = NEXT`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 7. Laws

- `GOOD_ORDER_EXISTS != CHEAP_GOOD_ORDER_DISCOVERY`
- `CHEAP_ORDER_VERIFICATION != CHEAP_ORDER_CONSTRUCTION`
- `GENERAL_OBDD_ORDERING_HARDNESS != SOURCE_MATCHED_NW_ORDERING_HARDNESS`
- `HEURISTIC_REORDERING_HAS_ZERO_THEOREM_AUTHORITY`
- `TEMPORARY_REORDERING_STATE_MUST_BE_CHARGED_IN_ORIGINAL_N`
