# C025 — Akinator PF5: exact polynomial Resolution schema for frozen graph tautologies

Status: **INTERNAL CONSTRUCTIVE RESOLUTION THEOREM + EXTERNAL ALIGNMENT**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Why this matters

The historical GT12 instance is valuable for exposing bad generic search/quotient policies, but it must not be mistaken for a hard family for general Resolution if a short family-specific proof schema exists.

External alignment: Buss and Johannsen, *On Linear Resolution* (2016), Theorem 14, give `O(n^3)` linear Resolution refutations for the ordering principles / graph tautologies. Earlier graph-tautology work also gives polynomial regular Resolution refutations.

This note gives an explicit construction directly for the exact `graph_tautology_cnf(n)` encoding frozen in JANUS Fundamentum, so the project does not rely on name similarity alone.

---

## 1. Exact JANUS encoding

For vertices `0,...,n-1`, there is one variable for each unordered pair.

`less(i,j)` is a signed literal representing the strict orientation `i<j`, with

`less(j,i) = NOT less(i,j)`.

The root CNF contains:

### Non-minimality

For each vertex `i`,

`M_i^n := OR_{j!=i} less(j,i)`.

So every vertex has a predecessor.

### Transitivity / no directed 3-cycle

For every distinct triple `(a,b,c)`, the canonical CNF contains

`less(a,b) OR less(b,c) OR less(c,a)`.

This is exactly the encoding implemented by `graph_tautology_cnf` in the pinned Fundamentum source.

---

## 2. One-vertex reduction lemma

Fix `m>=3` and suppose all clauses `M_i^m` for vertices `0,...,m-1` are available together with the original transitivity axioms.

Let

`z := m-1`.

For each `i<z`, define

`p := less(z,i)`

and

`M_i^{m-1} := OR_{k<z, k!=i} less(k,i)`.

Then

`M_i^m = p OR M_i^{m-1}`.

We derive `M_i^{m-1}` as follows.

### Step A — derive `NOT p OR M_i^{m-1}` from `M_z^m`

`M_z^m` contains all literals `less(k,z)` for `k<z`. In particular the term for `k=i` is

`less(i,z) = NOT less(z,i) = NOT p`.

For every `k<z`, `k!=i`, use the transitivity clause

`NOT less(k,z) OR NOT less(z,i) OR less(k,i)`.

This clause is one of the frozen graph-tautology cycle clauses.

Resolve the current clause on `less(k,z)`. The pivot literal is replaced by `NOT p OR less(k,i)`. Since `NOT p` is already present from the `k=i` term, after all `z-1=m-2` such resolutions the resulting clause is exactly

`NOT p OR M_i^{m-1}`.

### Step B — eliminate `p`

Resolve this clause with

`M_i^m = p OR M_i^{m-1}`

on `p`.

The resolvent is exactly

`M_i^{m-1}`.

Thus each `i<z` costs

`(m-2)+1 = m-1`

Resolution inferences.

There are `m-1` values of `i`, so reducing `GT_m` to all non-minimality clauses of `GT_{m-1}` costs exactly

`(m-1)^2`

inferences.

All transitivity clauses for the smaller vertex set were already root axioms of the original `GT_n` and need not be re-derived.

---

## 3. Base case

For `m=2`, the two non-minimality clauses are

`M_0^2 = less(1,0)`

and

`M_1^2 = less(0,1) = NOT less(1,0)`.

One final Resolution inference derives the empty clause.

---

## 4. Exact proof-size theorem

Starting from `GT_n`, apply the reduction for

`m=n,n-1,...,3`

and then the one base-case inference.

Total Resolution inferences:

`1 + SUM_{m=3}^n (m-1)^2`

`= SUM_{r=1}^{n-1} r^2`

`= (n-1)n(2n-1)/6`.

Therefore the exact JANUS graph-tautology encoding has a deterministic family-specific Resolution refutation generator of cubic inference count.

For `n=12`:

`(11*12*23)/6 = 506`.

This is dramatically smaller than the generic search work observed in the historical GT12 C025/BH-Q2 runs, proving that those runs localized **policy/search inefficiency**, not intrinsic Resolution proof-size hardness of GT.

---

## 5. Deterministic generator complexity

Given a recognized `GT_n` encoding:

- root clause lookup is polynomial via canonical clause keys;
- every required transitivity axiom is addressed by its explicit vertex triple;
- the sequence of pivots `(m,i,k)` is completely deterministic;
- there is no candidate search or backtracking;
- each produced clause has width at most `m-1` during the non-minimality derivations;
- total inference count is `Theta(n^3)`.

The direct encoded input already has polynomial size in `n`, so this generator is polynomial in actual input length as well.

Recognition of the exact JANUS family can be implemented by reconstructing the pair-variable map and checking equality with `graph_tautology_cnf(n)`; this is a family-specific recognizer, not a universal SAT classifier.

---

## 6. PF5 implication

Add a family-specific exact operator:

`GT_LINEAR_RESOLUTION_SCHEMA`.

If the current/root input is byte-identical to a recognized JANUS `GT_n` instance (up to an explicitly verified permitted renaming/sign isomorphism), emit the deterministic cubic Resolution proof rather than running generic residual search.

This makes GT a **positive schema-control** for proof discovery:

`SHORT_PROOF + CHEAP_SCHEMA_RECOGNITION + CHEAP_DETERMINISTIC_GENERATION`.

It does not make GT evidence for universal P=NP.

---

## 7. Benchmark repair

GT12 remains useful for testing whether generic algorithms can rediscover structure, but it is no longer admissible as a candidate hard family against unrestricted Resolution/ER.

New law:

`GENERIC_SEARCH_EXPLOSION_ON_A_FAMILY_WITH_A_KNOWN_SHORT_SCHEMA != PROOF_COMPLEXITY_LOWER_BOUND`.

For universal PF5 coverage, the next red benchmark should be a family/state for which no already-known same-system polynomial schema is being silently ignored.

---

## 8. Claim ledger

`JANUS_GT_N_HAS_EXPLICIT_CUBIC_RESOLUTION_GENERATOR = PROVED_BY_CONSTRUCTION`

`JANUS_GT_N_RESOLUTION_INFERENCE_COUNT = (n-1)n(2n-1)/6`

`JANUS_GT12_GENERATOR_INFERENCE_COUNT = 506`

`GT12_GENERIC_C025_CAP_HIT_IMPLIES_GT_RESOLUTION_HARDNESS = REFUTED`

`GT_LINEAR_RESOLUTION_SCHEMA_IS_FAMILY_SPECIFIC = TRUE`

`PF5_UNIVERSAL_SCHEMA_SELECTOR = OPEN`

`P_VS_NP = OPEN`

---

## 9. Laws

- `KNOWN_SHORT_FAMILY_SCHEMA_BEATS_GENERIC_STATE_EXPLORATION`
- `GENERIC_SEARCH_COST != MINIMUM_PROOF_SIZE`
- `FAMILY_RECOGNITION != UNIVERSAL_SAT_RECOGNITION`
- `A_HARD_BENCHMARK_MUST_BE_AUDITED_FOR_KNOWN_UPPER_BOUNDS`
- `PF5_MUST_INCLUDE_CHEAP_EXACT_SCHEMAS_WHEN_THEIR_DOMAIN_IS_SYNTACTICALLY_CERTIFIED`
