# C025 — Akinator PF5-R4: canonical clause-trace boundary DP

Status: **EXACT REPRESENTATION-SPECIFIC DP THEOREM / UNIVERSAL WIDTH BOUND OPEN**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

The post-PF1 GT12 residue remains one connected incidence component after exact subsumption, intact-gate congruence and dead-intact-gate GC.

The next exact lane measures and consumes the **joint correlation across a frozen clause cut** rather than trying another semantic merge.

No order search is allowed. The current canonical clause serialization is the path order.

---

## 1. Frozen clause trace

Let the current canonical CNF be the ordered clause sequence

`C_1,...,C_m`.

For each current variable `v`, define

- `first(v)` = least clause index containing `v` or `NOT v`;
- `last(v)` = greatest such index.

Define

`L_t := {v : first(v) <= t <= last(v)}`.

Every variable of clause `C_t` belongs to `L_t`. For each variable, the indices of bags containing it form one interval. Therefore `(L_t)` is a valid path decomposition of the CNF primal graph under the frozen serialization.

Define

`lambda_clause := max_t |L_t| - 1`.

This width is exact for the frozen trace, not minimum pathwidth.

---

## 2. Exact dynamic program

Process clauses in order while maintaining the set of assignments to the currently live variables that extend to assignments satisfying every processed clause.

At step `t`:

1. introduce every variable with `first(v)=t` by both Boolean values;
2. reject assignments falsifying `C_t`;
3. forget variables with `last(v)=t`;
4. canonicalize identical assignments to the remaining live variables.

### Invariant

After step `t`, the table contains exactly the assignments to variables crossing the cut after `t` that extend to a satisfying assignment of `C_1 AND ... AND C_t`.

### Proof

Induct on `t`.

Introduction enumerates every possible value of variables first needed by the current clause. Clause filtering removes exactly assignments that cannot satisfy the newly added constraint. Forgetting existentially quantifies variables that occur in no future clause; two histories agreeing on the remaining boundary have identical future obligations and may be merged. Thus the invariant is preserved exactly. QED.

At the final step the boundary is empty. The CNF is satisfiable iff the empty assignment remains in the table.

---

## 3. Complexity

At every cut there are at most

`2^|L_t| <= 2^(lambda_clause+1)`

boundary assignments.

Thus the unrestricted explicit algorithm has time/space

`poly(m, literal_volume) * 2^O(lambda_clause)`.

For a frozen finite experiment, fail closed under explicit state and transition-work caps rather than allocating the full theoretical table.

A high frozen-trace width is not a lower bound against:

- a different clause order;
- another exact decomposition;
- a semantic/orbit quotient;
- an unrestricted circuit representation.

It closes only the selected deterministic explicit-DP lane when its cap is exceeded.

---

## 4. GT12 frozen successor

Use the exact post-congruence/post-GC giant component and freeze:

- clause order = existing canonical CNF serialization;
- boundary-state cap = `20000`;
- transition-work cap = `1000000`;
- no variable/clause order optimization;
- no post-hoc cap raise.

Record:

- `lambda_clause`;
- maximum live variables;
- maximum retained boundary states;
- cumulative transition attempts;
- first cap-trigger clause, if any;
- live/new/forgotten counts at the trigger.

If exact completion occurs, report only an exact decision for the transformed state. The existing PF1 reverse-provenance obligation remains separately charged under `Q_witness`.

---

## 5. Claim ledger

`CANONICAL_CLAUSE_LIVE_BAGS_FORM_VALID_PATH_DECOMPOSITION = PROVED`

`CLAUSE_TRACE_DP_INVARIANT_AND_EXACTNESS = PROVED`

`CLAUSE_TRACE_EXPLICIT_DP_COST = poly(state_bytes)*2^O(lambda_clause)`

`GT12_CANONICAL_TRACE_RESULT = NOT_YET_MEASURED`

`MINIMUM_PATHWIDTH_OR_OPTIMAL_ORDER = NOT_CLAIMED`

`UNIVERSAL_O_LOG_N_BOUNDARY_WIDTH = OPEN`

`UNIVERSAL_POLY_BOUNDARY_QUOTIENT = OPEN`

`P_VS_NP = OPEN`

---

## 6. Laws

- `CONNECTED != HIGH_PATHWIDTH`
- `FROZEN_TRACE_WIDTH != MINIMUM_PATHWIDTH`
- `EXACT_BOUNDARY_DP_MAY_FAIL_CLOSED_WITHOUT_A_SEMANTIC_ORACLE`
- `2^O(lambda) IS_POLYNOMIAL_ONLY_UNDER_A_UNIVERSAL_O(log N)_BOUND`
- `A_DP_CAP_FAILURE_CLOSES_THE_FROZEN_LANE_NOT_ALL_QUOTIENTS`
