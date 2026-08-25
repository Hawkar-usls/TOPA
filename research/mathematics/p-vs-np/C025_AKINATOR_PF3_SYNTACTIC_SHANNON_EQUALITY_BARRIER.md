# C025 — Akinator PF3-S1: syntactic Shannon residual-novelty barrier

Status: **EXACT ROUTE-CLOSURE FOR FROZEN SYNTACTIC PROJECTOR**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Target lane

After PF1/PF2 a natural exact fallback is to keep one canonical Boolean DAG and existentially eliminate a root variable `x` by Shannon projection

`EXISTS_x(C) := OR(C[x=0], C[x=1])`.

Freeze a purely structural canonicalizer:

- exact hash-consing by explicit node tuples;
- commutative child ordering for AND/OR;
- constant propagation;
- idempotence `A op A = A`;
- direct-complement rules `A AND NOT A=0`, `A OR NOT A=1`;
- double-negation removal;
- no distributive factoring;
- no SAT/equivalence oracle;
- no search for algebraically equivalent circuits.

Call this lane `SYNTACTIC-SHANNON`.

It is exact and every local operation is polynomial in the explicit DAG size. This note proves that its **total DAG construction** can nevertheless be exponential in the original input.

---

## 1. Equality family

Let

`EQ_n(X,Y) := AND_{i=1}^n (x_i <-> y_i)`.

Use the standard 2-CNF encoding

`(NOT x_i OR y_i) AND (x_i OR NOT y_i)`

for every pair.

The explicit input has `O(n)` clauses, variables and literal occurrences.

Freeze IDs/order

`x_1,...,x_n,y_1,...,y_n`

and eliminate roots in increasing ID order.

---

## 2. Exact semantic fact after eliminating X

For every assignment `b in {0,1}^n` to Y there is exactly one X assignment satisfying equality, namely `X=b`.

Therefore

`exists X . EQ_n(X,Y) = TRUE`

for every Y.

So a constant-size exact final representation exists after the X block is projected.

This fact alone says nothing about the cost of discovering that representation.

---

## 3. Theorem S1 — frozen structural Shannon projection materializes 2^n distinct Y branches

After eliminating `x_1,...,x_k` by the frozen `SYNTACTIC-SHANNON` operator, before any semantic/distributive factoring, the resulting DAG contains a disjunctive branch for every bit string

`a in {0,1}^k`

whose Y-side condition fixes

`y_i=a_i` for `i<=k`,

conjoined with the still-unprojected equality constraints for `i>k`.

Distinct strings `a != a'` induce distinct literal-conjunction syntax because they differ in at least one sign of some `y_i`. Exact structural hash-consing therefore cannot identify these branch conditions.

Consequently at stage `k=n` there are at least

`2^n`

distinct branch/minterm structures represented in the constructed DAG history.

Hence

`D_total >= 2^n`

for this frozen projector/order, while the encoded input size is `O(n)`.

### Proof sketch by induction

Base `k=0` is the single unprojected equality conjunction.

For the induction step, every existing prefix branch contains the next equality pair. Restricting `x_{k+1}=0` and `x_{k+1}=1` yields respectively the two opposite literals on `y_{k+1}` under the same prefix branch and same untouched suffix. The Shannon OR retains both children. Neither child is the direct complement of the other as a whole because both include the same suffix and prefix context; none of the frozen local simplifications performs the distributive factoring needed to extract that common context. Thus every prior branch splits into two structurally distinct children and the branch count doubles.

QED for the frozen lane.

---

## 4. Stronger total-work observation

If the projector continues and eliminates the Y roots as well, the final semantic result is the constant `TRUE`, and the structural simplifier eventually reduces the live root to that terminal.

But previously created canonical nodes remain charged in `D_total`.

Therefore this family is an exact witness to

`FINAL_CONSTANT_RESULT != POLYNOMIAL_TOTAL_CONSTRUCTION`.

The theorem is about **cumulative created state**, not final live bytes.

---

## 5. Why this does not prove an intrinsic lower bound

The same equality family has easy stronger quotients.

### PF1 prebirth factorization

For one pair

`(NOT x OR y) AND (x OR NOT y)`,

with pivot `x`, the PF1 residual sides are

`P = NOT y`, `N = y`.

Thus

`P OR N = TRUE`

immediately, before two child states are born. Repeating pairwise leaves only the untouched equality suffix and uses polynomial total work.

### Exact orbit quotient

The historical JANUS Tranception equality-family experiment constructs a polynomial-size prebirth orbit automaton and exact witness-return path.

Hence the S1 result proves only:

`PURE_STRUCTURAL_HASH_CONSING_PLUS_SHANNON_PROJECTION_IS_NOT_A_UNIVERSAL_POLYNOMIAL_QUOTIENT`.

It does **not** prove equality is hard, and it does **not** lower-bound arbitrary B2/ER representations.

---

## 6. What resource rescued equality?

The missing operation is not more hashing. It is a certified relation between two newly born branches:

`(y AND R) OR ((NOT y) AND R) = R`.

PF1 recognizes the equivalent distributive/quantifier identity **before** branch duplication.

Thus:

`SYNTACTIC_SHARING != ALGEBRAIC_QUOTIENT_DISCOVERY`.

The next universal route must admit proof-carrying local/global rewrite or orbit certificates, but must pay for discovering them and for all failed attempts.

---

## 7. PF3 trilemma after S1

The residual-novelty problem now has three increasingly strong lanes:

1. **Syntactic** — cheap exact equality, refuted as universal by S1 for the frozen Shannon lane.
2. **Restricted canonical** — ROBDD/ZDD/live-width representations; exact but may incur representation/order/boundary blow-up.
3. **Proof-carrying algebraic/orbit quotient** — can collapse S1 equality branches, but universal deterministic discovery and total certificate volume remain open.

There is no free semantic fourth lane.

---

## 8. Next gate — PF3-Q

Freeze a polynomially enumerable rewrite/quotient certificate language containing at least:

- PF1 pivot-factor identities;
- direct Boolean identities with local proof witnesses;
- exact signed/orbit generator certificates when structurally discoverable;
- low-live-width exact relation certificates;
- frozen-order canonical decision diagrams where within cap.

At each projection step require a deterministic first-fit certificate whose:

- discovery including failed candidates is polynomial in original `N`;
- verification is polynomial;
- output/current/cumulative bytes are under one fixed polynomial cap;
- exact witness provenance is preserved;
- an original-root elimination/global rank decrease occurs.

Universal availability is the open theorem.

---

## 9. Claim ledger

`SYNTACTIC_SHANNON_EXACTNESS = PROVED_BY_BOOLEAN_COFATOR_IDENTITY`

`SYNTACTIC_SHANNON_EQUALITY_X_FIRST_D_TOTAL_GE_2_POW_N = PROVED_FOR_FROZEN_LANE`

`SMALL_FINAL_DAG_IMPLIES_SMALL_TOTAL_WORK = REFUTED`

`PF1_COLLAPSES_EQUALITY_PAIR_PREBIRTH = PROVED`

`SYNTACTIC_HASH_CONSING_UNIVERSAL_POLY_QUOTIENT = REFUTED_FOR_FROZEN_PROJECTOR_POLICY`

`ALGEBRAIC_ORBIT_QUOTIENT_UNIVERSAL_DISCOVERY = OPEN`

`PF3_UNIVERSAL_RESIDUAL_NOVELTY_BOUND = OPEN`

`P_VS_NP = OPEN`

---

## 10. Laws

- `HASH_CONSING_CHILDREN_AFTER_BIRTH != PREBIRTH_FACTORING`
- `FINAL_TRUE != CHEAP_DISCOVERY_OF_TRUE`
- `STRUCTURALLY_DISTINCT_EQUIVALENT_BRANCHES_REQUIRE_A_PAID_QUOTIENT`
- `D_TOTAL_MATTERS_EVEN_WHEN_D_FINAL_IS_ONE`
- `EXPLICIT_EQUALITY_NEGATIVE_CONTROL_CAN_BE_EASY_FOR_A_STRONGER_EXACT_OPERATOR`
