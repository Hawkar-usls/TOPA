# C025-C — Deterministic Reason Discovery and Proof-Search Cost

**Status:** problem split and cache-query lemma derived; global proof-search and input-relative cache-size bounds remain open.

**Claim ceiling:** this document does not establish polynomial-time SAT or `P=NP`.

## 1. Why C025-B does not close C025-C

C025-B gives a portable certificate that is cheap to validate **once supplied**. A solver still needs to answer two different questions:

```text
CACHE QUERY:
  does an already-stored certified reason apply to the current context?

PROOF SEARCH:
  if no stored reason applies, how does the deterministic policy discover a useful new reason/conflict?
```

They are not the same complexity problem.

## 2. Applicability is a subset query

For partial assignment `rho`, define its false-literal set

```text
FALSE(rho) = {
  v   if rho(v)=0,
  ~v  if rho(v)=1
}.
```

A certified clause reason `C` applies exactly when

```text
C subseteq FALSE(rho).
```

Thus reason-cache lookup is a dynamic subset-containment query over a family of stored clauses.

## 3. Incremental exact index

For every stored reason clause `C_i`, maintain

```text
false_count[i] = number of literals of C_i currently false.
```

For each literal `l`, maintain an occurrence list

```text
occ[l] = { i : l in C_i }.
```

When assignment of variable `v` makes literal `l` false, increment `false_count[i]` for each `i in occ[l]`. A reason becomes applicable exactly when

```text
false_count[i] == |C_i|.
```

Record changed counters on the ordinary DPLL trail so rollback performs the inverse updates exactly.

### Lemma C1 — query soundness and completeness

The counter index reports `C_i` applicable iff the current assignment falsifies every literal of `C_i`.

**Proof.** Each assigned variable contributes exactly its unique false polarity to `FALSE(rho)`. The counter is incremented exactly for stored clauses containing that false literal. Therefore `false_count[i]` equals `|C_i ∩ FALSE(rho)|`; equality with `|C_i|` is equivalent to `C_i subseteq FALSE(rho)`. □

### Lemma C2 — monotone-path update cost

Let

```text
M = sum_i |C_i|
```

be total literal volume of the current reason cache. Along a monotone sequence that assigns each variable at most once, the total number of counter increments is at most `M`.

**Proof.** A stored literal occurrence is touched only if its variable is assigned to the value making that literal false, and then it is touched once. Sum over all stored literal occurrences. □

Rollback costs exactly the number of reverted updates, so a descent plus rollback is `O(M)` counter operations, excluding integer/index representation factors.

## 4. The conditional discovery theorem

If at every point in a Policy-0B execution the total encoded reason-index representation satisfies

```text
M <= N^a
```

for a fixed constant `a`, then exact cached-reason applicability can be maintained in deterministic polynomial time per polynomial-length assignment/rollback trace.

This removes **cache-query mechanics** as an independent obstacle **conditional on C025-E/#212**.

It does not prove the premise `M <= N^a`.

## 5. Three remaining costs that must not be conflated

```text
C025-C1  EXISTING-REASON QUERY
          = polynomial in explicit cache volume M

C025-C2  NEW-REASON GENERATION
          = OPEN in original input length N

C025-E   TOTAL CACHE / PROOF-DAG REPRESENTATION
          = OPEN in original input length N
```

A large cache can make a perfectly efficient index globally expensive. A small cache can still fail if the deterministic solver needs superpolynomial search to generate the useful clauses.

Therefore:

```text
FAST_INDEX != SMALL_CACHE
SMALL_CACHE != FAST_PROOF_SEARCH
SHORT_PROOF_EXISTS != DETERMINISTIC_POLICY_FINDS_IT
```

## 6. Proof-search barrier

The Formula-Caching-with-reasons literature can show that a proof system has short proofs or p-simulates another proof system when supplied an appropriate proof structure. That is a statement about proof **existence/translation**.

For the P-vs-NP bridge we need an algorithmic theorem:

> Given arbitrary CNF `F`, the frozen deterministic Policy-0B discovers the required sequence of branches/reasons in time `poly(|F|)`.

No such theorem is currently established here.

The proof-search gate must explicitly charge:

- fair-layer inference work;
- conflict discovery;
- antecedent tracking;
- reason construction;
- reason-cache insertion/index maintenance;
- reason lookup;
- rollback;
- certificate materialization/verifier work;
- all states that do not yield a reusable reason.

## 7. Exact next targets

### C025-C1 — cache-query implementation

Implement occurrence lists + falsification counters + rollback and replay:

- overlapping reasons;
- clauses of different widths;
- opposite literal polarities;
- branch/backtrack cycles;
- duplicate reason rejection/canonicalization;
- empty-clause reason;
- contexts with unassigned reason variables.

### C025-C2 — deterministic generation theorem or counterfamily

Either prove a polynomial input-relative bound for the frozen generation policy, or construct an explicit infinite family where it requires superpolynomial work despite sound reasons and fair scheduling.

### C025-E — representation bound

Prove or refute a universal polynomial bound on the active reason/cache/proof-DAG representation. This is coupled to Issue #212.

## 8. Current frontier

```text
C025_B_PORTABLE_REASON_SOUNDNESS          = PROVED_ON_PAPER / REPLAY ACTIVE
C025_C_CACHE_QUERY_CORRECTNESS            = PROVED
C025_C_CACHE_QUERY_COST_IN_CACHE_VOLUME   = PROVED
C025_C_CACHE_QUERY_COST_IN_INPUT_N        = CONDITIONAL_ON_C025_E
C025_C_NEW_REASON_GENERATION              = OPEN
C025_C_DETERMINISTIC_GLOBAL_PROOF_SEARCH  = OPEN
C025_E_TOTAL_REASON_CACHE_SIZE            = OPEN
P_VS_NP                                   = OPEN
```
