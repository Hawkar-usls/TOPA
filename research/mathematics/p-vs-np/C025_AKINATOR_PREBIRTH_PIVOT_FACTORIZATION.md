# C025 — Akinator: exact prebirth pivot factorization

Status: **POSITIVE EXACT ONE-PIVOT COMPRESSION THEOREM / ITERATED TOTAL-SIZE GATE OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Motivation

The add-only `MACRO-RESTORE-CAP` barrier proves that merely appending extension definitions cannot remove an already-existing Davis–Putnam resolvent frontier. A useful extension must replace/quotient the pivot block **before** all pairwise resolvents are born.

There is an exact Boolean identity that does precisely this for one CNF pivot.

It is a genuine constructive operator, not a heuristic score.

---

## 1. Pivot notation

Let `F` be a CNF and `x` a current variable.

Write every positive pivot clause as

`x OR A_i`, for `i=1,...,p`,

and every negative pivot clause as

`NOT x OR B_j`, for `j=1,...,q`,

where each `A_i` and `B_j` is the residual clause after deleting the pivot literal.

Let `R` be the conjunction of all clauses not containing `x`.

Thus

`F = R AND (AND_i (x OR A_i)) AND (AND_j (NOT x OR B_j))`.

Empty `A_i` or `B_j` are allowed and mean Boolean false.

---

## 2. Theorem PF1 — exact existential pivot factorization

Define

`P := AND_i A_i`

and

`N := AND_j B_j`.

Then as a Boolean relation on all variables except `x`,

`exists x . F  ==  R AND (P OR N)`.

### Proof

Fix an assignment `alpha` to every variable other than `x`.

- If `P(alpha)=1`, then all `A_i` are true. Choosing `x=0` satisfies every positive pivot clause via `A_i`, and every negative pivot clause via `NOT x`.
- If `N(alpha)=1`, then all `B_j` are true. Choosing `x=1` satisfies every positive pivot clause via `x`, and every negative pivot clause via `B_j`.

Therefore `P OR N` implies that some value of `x` satisfies the complete pivot block.

Conversely, if neither `P` nor `N` is true, choose `i` with `A_i(alpha)=0` and `j` with `B_j(alpha)=0`. Then the positive clause `(x OR A_i)` requires `x=1`, while the negative clause `(NOT x OR B_j)` requires `x=0`. No value of `x` satisfies both. Thus existential satisfiability of the pivot block implies `P OR N`.

The nonpivot conjunction `R` is independent of `x` and carries through unchanged. QED.

---

## 3. Equivalence to the complete resolvent frontier

Complete Davis–Putnam elimination adds all non-tautological clauses

`A_i OR B_j`.

Ignoring tautological pairs (which are Boolean true), the conjunction of the full pair family satisfies the distributive identity

`AND_{i,j} (A_i OR B_j) == (AND_i A_i) OR (AND_j B_j)`.

This is another direct proof of PF1.

The key complexity distinction is representation:

- explicit DP frontier: potentially `p*q` clauses before dedup;
- factored form: one occurrence of each `A_i`, one occurrence of each `B_j`, two conjunction aggregations and one disjunction.

Thus the pair **relation** can have a compact exact circuit representation even when its explicit CNF expansion is large.

---

## 4. Edge cases

If `p=0`, define `P=TRUE`. Then `P OR N=TRUE`, reflecting that choosing `x=0` satisfies every negative pivot clause regardless of the `B_j` values.

If `q=0`, define `N=TRUE`. Then choosing `x=1` satisfies every positive pivot clause.

If some `A_i=FALSE`, then `P=FALSE`; the factorized condition correctly requires `N=TRUE`, i.e. `x=1` plus every negative residual satisfied.

The analogous statement holds for an empty `B_j`.

---

## 5. B2 proof-carrying representation

The factored formula can be represented with the frozen B2 `AND/NOT` language.

### Clause node

For a residual clause

`A = l_1 OR ... OR l_k`,

construct

`a_false := (NOT l_1) AND ... AND (NOT l_k)`

with a binary AND chain, and use the signed literal `NOT a_false` as the value of `A`.

This needs `O(k)` B2 gates.

### Aggregate nodes

Build binary AND trees for all `A_i` values and all `B_j` values, producing `p_all` and `n_all`.

Encode

`p_all OR n_all = NOT((NOT p_all) AND (NOT n_all))`

with one additional AND gate plus a signed output literal.

Force the output true in the transformed state.

The complete B2 gate count is linear in the total literal volume of the pivot block, up to fixed binary-tree and serialization constants.

No `p*q` resolvent materialization is required.

---

## 6. Exact witness lift

Given a satisfying assignment of the transformed state on remaining roots and B2 gate values:

- if `P=1`, set eliminated pivot `x:=0`;
- else `N=1` must hold, set `x:=1`.

If both hold, use the frozen canonical rule `x:=0`.

By PF1 this reconstructed value satisfies every original pivot clause.

Therefore one elimination step has a deterministic exact witness-return map.

`PREBIRTH_FACTOR_WITNESS_LIFT = POLYNOMIAL_IN_EXPLICIT_FACTOR_CERTIFICATE_BYTES`.

---

## 7. One-step complexity theorem

Let `L_x` be the explicit literal volume of all pivot clauses before elimination.

The factored B2 representation can be constructed and verified in

`O(poly(L_x))`

time and `O(L_x)` gate/record volume under fixed-width gate serialization.

Thus:

`ONE_PIVOT_PAIR_CROSS_PRODUCT_CAN_BE_REPLACED_BY_LINEAR_SIZE_B2_FACTOR_DAG = PROVED_IN_SCOPE`.

This is stronger than merely adding an extension after the DP frontier exists: the cross-product is never materialized.

---

## 8. Why this does not yet prove P=NP

After the first factorization, the state is no longer a plain root CNF unless the B2 DAG is Tseitin-encoded back into CNF or the solver changes representation.

Either route creates a new total-complexity obligation.

### Circuit route

Exact existential elimination of the next variable from a general circuit can always be written as

`C[x=0] OR C[x=1]`,

but repeated restriction/copying may produce exponentially many distinct residual subcircuits.

This is the same residual-frontier resource exposed by the ROBDD lane.

### Tseitin-CNF route

Returning the factor DAG to CNF introduces fresh extension variables and definition clauses. The next pivot can again be factorized exactly, but the total state/gate volume across many eliminations has not been proved to remain bounded by `N^K` for one universal fixed `K`.

A recurrence of the form

`S_{t+1} <= c*S_t`

with fixed `c>1` is not enough: after `Theta(N)` stages the crude bound is exponential.

Therefore:

`LINEAR_ONE_STEP_COMPRESSION != UNIFORM_POLYNOMIAL_FULL_RUN`.

---

## 9. Exact next resource — NOVEL RESIDUAL DAG MASS

The one-step theorem removes the explicit `|P_x||N_x|` pair explosion. What can still grow is the number of **distinct subfunctions/subcircuits that must remain alive across successive eliminations**.

Define for a deterministic elimination/factorization run:

`D_t := number of canonical distinct factor-DAG nodes retained after stage t`.

and

`D_total := number of canonical distinct nodes ever created, including discarded temporary nodes`.

A true polynomial Akinator theorem requires

`D_t <= N^K` and `D_total <= N^K`

for one universal fixed `K`, together with polynomial bit-cost canonicalization and witness provenance.

A small final DAG is insufficient if exponentially many failed/temporary nodes were created first.

---

## 10. Organism synthesis

The exact theorem matches, but is not proved by, patterns independently preserved across the JANUS ecosystem:

- historical JANUS Tranception diagnosis: quotient equivalent children before birth;
- Quantum/Physarum fail-closed line: generator proposes, exact verifier decides;
- OdontoForge: preserve branch lineage/EXIT and recovery cost;
- P-N distributed field: latency does not erase total work.

The mathematical content is PF1 and the explicit B2 construction above. The cross-repository pattern tells us **where to look**, not what is true.

---

## 11. Successor gates

### PF2 — deterministic canonical sharing

Build a frozen hash-consed factor-DAG representation and prove exact equality of nodes is purely syntactic/canonical, never collision-semantic.

### PF3 — residual novelty bound

Attempt to prove or refute a universal fixed-polynomial bound on `D_total` under a deterministic pivot rule and canonical factorization.

### PF4 — structural quotient certificates

If syntactic DAG novelty is superpolynomial on an explicit family, allow only proof-carrying equivalence/orbit quotients with polynomial discovery and witness lift; charge every failed quotient attempt.

### PF5 — total closure

If a universal fixed `K` bounds total DAG/proof/witness bytes and all `n` original roots are eliminated exactly, the final input-free DAG is evaluated directly, yielding a deterministic polynomial SAT decider and hence `P=NP`.

---

## 12. Claim ledger

`PREBIRTH_PIVOT_FACTORIZATION_IDENTITY = PROVED`

`PREBIRTH_PIVOT_FACTORIZATION_B2_SIZE = LINEAR_IN_EXPLICIT_PIVOT_LITERAL_VOLUME_UP_TO_FIXED_FACTORS`

`PREBIRTH_FACTOR_WITNESS_LIFT = PROVED`

`EXPLICIT_DP_PAIR_CROSS_PRODUCT_IS_NOT_INTRINSICALLY_REQUIRED_FOR_ONE_PIVOT = PROVED`

`ITERATED_FACTOR_DAG_TOTAL_SIZE_POLYNOMIAL = OPEN`

`UNIVERSAL_RESIDUAL_NOVELTY_BOUND = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 13. Laws

- `PAIRWISE_RESOLVENT_EXPANSION != MINIMUM_EXACT_REPRESENTATION`
- `AND_IJ_A_I_OR_B_J == AND_I_A_I OR AND_J_B_J`
- `COMPRESS_BEFORE_RESOLVENT_BIRTH`
- `ONE_STEP_LINEAR_FACTORING != POLYNOMIAL_TOTAL_RUN`
- `FINAL_SMALL_DAG != POLYNOMIAL_TOTAL_DAG_CONSTRUCTION`
- `RESIDUAL_NOVELTY_AND_INTERMEDIATE_BYTES_MUST_BE_CHARGED`
