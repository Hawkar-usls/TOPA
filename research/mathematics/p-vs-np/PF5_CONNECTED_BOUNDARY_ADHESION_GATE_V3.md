# PF5 — Connected Boundary Adhesion Gate v3

Status: **FROZEN FINITE MECHANICS / CONDITIONAL WIDTH THEOREM**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Question

The v2.2 `COMPONENT_PRODUCT` constructor closes the separator-width-zero case: independent components may carry different exact representations and their SAT witnesses can be remapped and unioned.

The next exact question is the first nonzero-separator case.

Let

`F(A,B,C) = L(A,B) AND R(C,B)`

with pairwise-disjoint private sets `A,C`, nonempty shared boundary `B`, and no other overlap.

The representation problem is not "find another solver". It is:

> Can a proof-carrying state remain exact and directly closed under the next existential projection when two previously separate states share a live boundary, with separator discovery, JOIN, projection, witness glue, intermediate bytes and failed work all charged?

---

## 1. Exact adhesion law

Define the exact wing boundary relations

`Lambda(B) := exists A L(A,B)`

`Rho(B) := exists C R(C,B)`.

Then

`exists A exists C F = Lambda(B) AND Rho(B)`.

Define the adhesion JOIN operator

`J_B(Lambda,Rho) := Lambda INTERSECT Rho`.

For a boundary variable `b in B`,

`exists b exists A exists C F = exists b J_B(Lambda,Rho)`.

This is the first mathematically legitimate `J` in the representation algebra: it is an exact JOIN, not a heuristic controller choice.

Private projection and boundary projection are different phases:

1. **PRIVATE phase**: eliminate only variables in `A` or `C` inside their owning proof-carrying wing state.
2. **ADHESION phase**: before eliminating the first shared `b`, materialize or otherwise construct an exact representation of `J_B`.
3. **BOUNDARY phase**: project shared variables directly from the joined boundary representation.

The invalid shortcut

`(exists b Lambda) AND (exists b Rho)`

is forbidden because independent existential choices for `b` can destroy correlation.

---

## 2. Frozen explicit-table lane

v3 deliberately uses the simplest auditable boundary language first: an explicit canonical set of satisfying bit-vectors over `B`.

For width `k=|B|`:

- enumerate all `2^k` boundary assignments in lexicographic order;
- evaluate the exact post-private left residual and right residual;
- store `Lambda_rows` and `Rho_rows` canonically;
- compute `J_rows = Lambda_rows INTERSECT Rho_rows`;
- project boundary variables by canonical tuple projection/deduplication;
- preserve hashes/counts of every boundary state;
- reconstruct a boundary witness only from `J_rows`;
- lift private witnesses through the actual private-projection proof on each wing;
- verify the union against the original unprojected left and right formulas.

No SAT oracle, family-specific witness, or post-hoc variable order is permitted.

---

## 3. Frozen connected control family

Widths are frozen **before provider execution**:

`K = [2,4,6,8,10,12,14]`.

For each `k`, create two controls sharing boundary roots

`B = (b_1,...,b_k)`.

Each wing contains a private parity chain:

`a_1 = b_1`

`a_i = a_(i-1) XOR b_i` for `2<=i<=k`

plus a final pin `a_k = t`.

The left target is always `t_L=0`.

Two right targets are frozen:

- `SAT`: `t_R=0`, so both wing boundary relations are the same even-parity relation;
- `UNSAT`: `t_R=1`, so the two exact boundary relations are disjoint.

Thus every control is connected through the shared `B`, and each individual wing boundary relation contains exactly `2^(k-1)` rows.

This family is chosen to force a nontrivial exact boundary language while keeping each wing construction/projection simple and independently checkable.

---

## 4. Accounting contract

The existing v0.1 global caps remain unchanged:

- `RAW_MAX_INTERNED_NODES = 5000`
- `OBDD_MAX_NONTERMINAL_NODES = 192`
- `FACTOR_MAX_BUCKET_SCOPE = 16`
- `MAX_PRIMARY_STATE_BYTES = 250000`
- `MAX_PROOF_BYTES = 750000`
- `MAX_CUMULATIVE_STATE_BYTES = 3000000`
- `MAX_OPERATION_COUNT = 3000000`

v3 adds **no new tuned size cap**.

Charge at minimum:

- left/right formula build operations;
- every private `restrict`/OR projection operation;
- private proof bytes;
- every enumerated boundary assignment;
- left/right residual evaluation work;
- serialization bytes of `Lambda`, `Rho`, `J` and every projected boundary state;
- JOIN membership/intersection work;
- boundary projection/deduplication work;
- private witness lift and shared-boundary witness work;
- final verification against the original wing formulas.

A cap hit is a finite representation result only. It is not a lower bound against compressed boundary languages.

---

## 5. Conditional width theorem

For the frozen explicit boundary table language, the number of possible boundary rows is at most `2^k`.

If an enclosing proof system supplies universal constants `c,d` such that for every relevant state:

- the wing representations and their private projection/provenance have total size/work at most `N^d`, and
- `k <= c log_2 N`,

then

`2^k <= N^c`

and exact JOIN plus repeated boundary projection is polynomial in original input length `N` with a fixed universal exponent.

Therefore:

`POLY_WINGS + UNIVERSAL_O(LOG N)_ADHESION => POLY_EXPLICIT_BOUNDARY_JOIN_PROJECT`.

What is **not** proved is that every SAT proof state admits such a separator, or that discovering/re-writing to one is polynomial.

---

## 6. Required v3 verdicts

The provider replay must report independently:

- `PRIVATE_PROJECTION_EXACT`
- `BOUNDARY_RELATIONS_EXACT`
- `ADHESION_JOIN_EXACT`
- `REPEATED_BOUNDARY_PROJECT_EXACT`
- `STRICT_WITNESS_GLUE_EXACT`
- `FIRST_BASE_CAP_HIT`, if any
- `EXPLICIT_TABLE_EXPONENTIAL_FOOTPRINT_OBSERVED`
- `UNIVERSAL_O_LOG_N_ADHESION_BOUND = OPEN`
- `CHEAP_ADHESION_DISCOVERY = OPEN`
- `COMPRESSED_BOUNDARY_REWRITE_DISCOVERY = OPEN`
- `GLOBAL_PROGRESS_AMORTIZATION = OPEN`
- `P_VS_NP = OPEN`

---

## 7. Interpretation

If all frozen widths pass, the finite lane validates the JOIN/projection/witness mechanics but says nothing universal.

If the unchanged base state/operation cap is hit as `k` grows, that is expected evidence about the **explicit table representation**. The correct successor is a compressed proof-carrying boundary language (for example OBDD/orbit/automaton where admitted), not a claim of intrinsic hardness.

If a compressed language repairs the finite table escape, the next front becomes discovery: can an appropriate compact boundary representation be found and certified without exponential search?

---

## 8. Laws

- `SEPARATOR_WIDTH_ZERO = COMPONENT_PRODUCT`
- `NONZERO_SEPARATOR_REQUIRES_CORRELATION_PRESERVING_JOIN`
- `EXISTS_DOES_NOT_DISTRIBUTE_OVER_SHARED_BOUNDARY_CONJUNCTION`
- `J_B = EXACT_BOUNDARY_JOIN`
- `EXPLICIT_BOUNDARY_STATE_COST = 2^O(|B|)`
- `O(LOG N)_ADHESION_MAKES_EXPLICIT_JOIN_POLYNOMIAL_CONDITIONALLY`
- `FINITE_TABLE_CAP_HIT != REPRESENTATION_LOWER_BOUND`
- `COMPACT_BOUNDARY_EXISTS != CHEAP_COMPACT_BOUNDARY_DISCOVERY`
- `P_VS_NP = OPEN`
