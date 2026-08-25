# PF5 — Non-Affine Connected Boundary Gate v4

Status: **FROZEN HETEROGENEOUS-REPRESENTATION GATE**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Why this gate exists

v3.2 closed the finite affine connected-boundary subalgebra:

`AFFINE_WING -> AFFINE_BOUNDARY -> J_B -> EXISTS -> AFFINE_BOUNDARY`.

That does not address arbitrary Boolean boundaries. The next control must therefore force the exact JOIN to cross representation languages.

v4 freezes a connected shared separator `B` with:

- a left proof-carrying **affine parity** wing;
- a right proof-carrying **non-affine** wing represented as an OBDD;
- an exact conversion of the affine residual into a common OBDD manager;
- exact heterogeneous `J = AND` in that manager;
- repeated shared existential projection directly on `J`;
- strict witness reconstruction through the common boundary proof and both original private-wing proofs.

No universal language selector is assumed.

---

## 1. Frozen widths and controls

Widths are frozen before provider execution:

`K = [3,4,6,8,10,12,14]`.

`k=3` is the smallest rung so that every intended right relation is genuinely non-affine.

For each `k`, shared roots are

`B=(b_1,...,b_k)`.

The left wing is exactly the v3.1 private parity chain pinned to even parity:

`Lambda(B) = PARITY(B)=0`.

The right wing has private roots `C=(c_1,...,c_k)` with exact equality glue

`c_i = b_i`

and one frozen boundary predicate `G(B)`.

Two controls are used per width.

### SAT control

`G(B) = OR(B)`.

After private projection:

`Rho_OR(B) = OR(B)`.

The joined relation is

`J_SAT(B) = EVEN_PARITY(B) AND OR(B)`.

Its model count is

`2^(k-1)-1`,

so for every frozen `k>=3` it is non-affine.

### UNSAT control

`G(B) = EXACTLY_ONE(B)`.

After private projection:

`Rho_EX1(B) = EXACTLY_ONE(B)`.

Every weight-one assignment has odd parity, hence

`J_UNSAT(B) = EVEN_PARITY(B) AND EXACTLY_ONE(B) = FALSE`.

For `k>=3`, `EXACTLY_ONE(B)` itself is non-affine because its model count `k` is not, in general, the size of an affine Boolean subspace/coset and the frozen finite verifier also checks the exact truth set.

---

## 2. Right proof-carrying OBDD wing

The right wing is constructed directly by a deterministic finite-state BDD constructor under the frozen interleaved order

`c_1,b_1,c_2,b_2,...,c_k,b_k`.

State carried by the constructor:

- pending value of the current private `c_i` until `b_i` is read;
- for `OR`: one bit `seen_one`;
- for `EXACTLY_ONE`: saturated count `0,1,2+`.

The `b_i` branch inconsistent with `c_i=b_i` is sent to FALSE. At the terminal layer the automaton accepts exactly when the frozen predicate is satisfied.

This is an exact constructor, not an adaptive variable-order search.

Private roots `c_i` are then existentially projected with the ordinary OBDD restrict/OR rule, storing actual `c0/c1/post` proof records for witness reversal.

The post-private residual is independently checked against the exact `OR` or `EXACTLY_ONE` truth function on all `2^k` boundary assignments. Those checks are charged as finite verification work and are not used to build the working state.

---

## 3. Affine-to-OBDD proof-carrying conversion

The left affine residual is converted into the same common OBDD language over frozen boundary order

`b_1,...,b_k`.

The compiler recursively restricts the canonical affine system by `b_i=0/1`, deterministically RREF-reduces each residual, memoizes by the exact canonical residual state, and creates the corresponding reduced BDD node.

Every:

- restriction;
- RREF row operation;
- memo lookup;
- BDD node construction;
- intermediate canonical affine state

is charged.

The conversion transcript includes source-system hash, destination-root hash/ID, recursion/state counts and work ledger.

This is a supplied conversion for the affine lane only. It is **not** a theorem that arbitrary boundary representations can be cheaply translated to OBDD.

---

## 4. Exact heterogeneous JOIN

After both residuals are in one common frozen-order OBDD manager:

`J_B(Lambda,Rho) := APPLY_AND(OBDD(Lambda), OBDD(Rho))`.

`APPLY_AND` is the canonical memoized Shannon apply over the common variable order.

No truth-table materialization is used to construct `J`.

The joined OBDD must then support the entire frozen sequence

`exists b_1 -> exists b_2 -> ... -> exists b_k`

by direct

`restrict(0), restrict(1), APPLY_OR`.

Every intermediate joined/projection state is serialized and charged.

---

## 5. Strict witness path

For SAT controls, no family witness is allowed.

The final witness must be reconstructed only by:

1. reversing the actual common-OBDD shared-boundary projection proof to obtain all `b_i`;
2. reversing the actual right-wing OBDD private-projection proof to obtain all `c_i`;
3. reversing the actual left affine pivot proof to obtain all left-private roots;
4. checking the complete union against both original unprojected wing semantics.

UNSAT controls must terminate at canonical OBDD FALSE and export no witness.

---

## 6. Frozen accounting

All v0.1 caps remain unchanged:

- `RAW_MAX_INTERNED_NODES = 5000`
- `OBDD_MAX_NONTERMINAL_NODES = 192`
- `FACTOR_MAX_BUCKET_SCOPE = 16`
- `MAX_PRIMARY_STATE_BYTES = 250000`
- `MAX_PROOF_BYTES = 750000`
- `MAX_CUMULATIVE_STATE_BYTES = 3000000`
- `MAX_OPERATION_COUNT = 3000000`

No v4-specific tuned cap is added.

Charge at minimum:

- left affine wing build/private projection/proof replay;
- right OBDD constructor and private projection;
- failed/partial construction work on any cap hit;
- affine-to-OBDD conversion;
- right residual copy into the common manager;
- heterogeneous APPLY_AND JOIN;
- every shared existential projection;
- all intermediate state bytes and proof bytes;
- boundary/reference semantic verification;
- both private witness lifts and final source-formula verification.

---

## 7. Required provider verdicts

For every passing control:

- `LEFT_AFFINE_PRIVATE_PROJECT_EXACT`
- `RIGHT_NONAFFINE_PRIVATE_PROJECT_EXACT`
- `AFFINE_TO_OBDD_CONVERSION_EXACT`
- `RIGHT_OBDD_COPY_EXACT`
- `HETEROGENEOUS_JOIN_EXACT`
- `REPEATED_SHARED_PROJECT_EXACT`
- `STRICT_HETEROGENEOUS_WITNESS_GLUE_EXACT`

Global ledger:

- `FIRST_BASE_CAP_HIT`, if any;
- `BOUNDARY_LANGUAGE_DISCOVERY = SUPPLIED_FROZEN_TYPES_ONLY`;
- `UNIVERSAL_CHEAP_LANGUAGE_SELECTION = OPEN`;
- `UNIVERSAL_CHEAP_CROSS_LANGUAGE_CONVERSION = OPEN`;
- `UNIVERSAL_POLYNOMIAL_COVERAGE = OPEN`;
- `GLOBAL_PROGRESS_AMORTIZATION = OPEN`;
- `P_VS_NP = OPEN`.

---

## 8. Interpretation

A PASS proves only that the finite heterogeneous pair

`AFFINE_GF2 x {OR_OBDD, EXACTLY_ONE_OBDD}`

can be joined and repeatedly projected through a common proof-carrying OBDD under the frozen controls/caps.

A cap hit identifies the phase where this particular representation algebra escapes. It is not an intrinsic lower bound.

If v4 passes, the next adversary must remove the supplied representation labels and force a **language-discovery/selection gate**, or use a non-affine boundary family known to be bad for the frozen common OBDD order while another compact language exists.

---

## 9. Laws

- `AFFINE_CLOSED != BOOLEAN_UNIVERSAL`
- `HETEROGENEOUS_JOIN_REQUIRES_A_COMMON_EXACT_LANGUAGE_OR_EXACT_CROSS_LANGUAGE_OPERATOR`
- `COMPACT_IN_TWO_LANGUAGES != CHEAP_COMMON_LANGUAGE_DISCOVERY`
- `SUPPLIED_TYPE != DISCOVERED_TYPE`
- `JOIN_THEN_PROJECT_PRESERVES_SHARED_CORRELATION`
- `FINITE_HETEROGENEOUS_PASS != UNIVERSAL_POLYNOMIAL_COVERAGE`
- `P_VS_NP = OPEN`
