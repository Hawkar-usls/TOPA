# PF5 — Boundary Language Discovery Gate v5

Status: **FROZEN BLIND REPRESENTATION-SELECTION GATE**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

v4.1 established finite exact heterogeneous JOIN/projection when the boundary languages were supplied as control metadata.

v5 removes that hint.

The discovery routine receives only:

- a neutral exact OBDD state;
- its frozen variable order;
- the ordered boundary-root list.

It receives **no family name and no representation-language tag**.

A fixed recognizer portfolio must either discover and certify a more structured exact language or fall back to the source OBDD. Every rejected recognizer is charged.

---

## 1. Frozen controls

Widths are frozen before provider execution:

`K = [3,4,6,8,10,12,14]`.

Four unlabeled relation families are used at every width:

1. even parity — expected discovery lane `AFFINE_GF2`;
2. OR — expected discovery lane `SYMMETRIC_WEIGHT_SET`;
3. EXACTLY_ONE — expected discovery lane `SYMMETRIC_WEIGHT_SET`;
4. implication `b_1 -> b_2` — expected discovery lane `GENERIC_OBDD_FALLBACK`.

The expected labels are available only to the external test harness, never to the discovery function.

---

## 2. Fixed recognizer order

The portfolio order is frozen:

`AFFINE_SEMANTIC -> SYMMETRIC_WEIGHT_SEMANTIC -> OBDD_FALLBACK`.

No post-result reordering is permitted.

### 2.1 Affine semantic recognizer

For each OBDD node, recursively interpret its satisfying set as an affine coset over the remaining boundary coordinates.

A relation is represented internally as either EMPTY or

`a + V`,

where `a` is an anchor bit-vector and `V` has a canonical GF(2) basis.

At a Shannon node for variable `x`:

- if one cofactor is empty, `x` is fixed and the other affine set is lifted;
- if both are nonempty, the union is affine iff their direction spaces are equal;
- when equal, the extra direction `(x=1, delta=a_0 XOR a_1)` joins the basis.

Skipped OBDD variables are added as free basis directions.

This is exact semantic recognition from the OBDD graph; it does not inspect a family tag.

A successful coset is converted to a canonical affine equation system by taking the GF(2) orthogonal complement of its direction space. The resulting equations are independently compiled back to an OBDD and checked for exact equivalence with the source.

### 2.2 Symmetric-weight semantic recognizer

For a relation over `n` remaining roots, store an allowed Hamming-weight set `W subseteq {0,...,n}`.

At a Shannon node with low weight set `W0` and high tail-weight set `W1`, exact symmetry requires

`t in W0 iff (t-1) in W1`

for every shared total weight `1<=t<=n-1`.

If compatible,

`W = W0 UNION {w+1 : w in W1}`.

Skipped variables are handled as repeated equal low/high Shannon levels, so a nonconstant function that ignores one coordinate is correctly rejected as nonsymmetric.

A successful weight set is independently compiled back to an OBDD and checked for exact equivalence with the source.

### 2.3 Generic OBDD fallback

If both semantic recognizers reject, keep the exact source OBDD unchanged.

Fallback is not a failed experiment; it is the explicit final lane of the frozen portfolio.

---

## 3. Projection closure after discovery

The selected language must itself carry the repeated existential projection:

- `AFFINE_GF2`: pivot/XOR/remove equation projection with reverse-pivot witness reconstruction;
- `SYMMETRIC_WEIGHT_SET`: for one projected root,
  `W' = {w : w in W OR w+1 in W}`;
- `GENERIC_OBDD_FALLBACK`: restrict-0 / restrict-1 / APPLY_OR.

All roots are projected in the frozen left-to-right order until the state is a Boolean scalar.

---

## 4. Strict witness rule

For SAT controls, the final full boundary witness must come only from the selected language's actual projection proof:

- affine pivots;
- symmetric weight-transition proof;
- or OBDD branch proof.

The reconstructed assignment is checked against the original neutral source OBDD.

No family-level witness is allowed.

---

## 5. Accounting

All v0.1 caps remain unchanged. No v5-specific cap is introduced.

Charge:

- neutral OBDD fixture construction;
- every recognizer recursion/memo lookup/GF(2) basis operation;
- rejected recognizer work and failure certificate bytes;
- successful representation construction;
- independent compile-back equivalence proof;
- all repeated projection updates;
- all intermediate representation bytes;
- proof bytes;
- witness reconstruction and source verification.

The control-family name used by the external verifier is not charged to or visible from discovery.

---

## 6. Required verdicts

Per passing control:

- `DISCOVERY_INPUT_UNLABELED = TRUE`
- `FIXED_RECOGNIZER_ORDER_USED = TRUE`
- `ALL_FAILED_RECOGNIZER_WORK_CHARGED = TRUE`
- `SELECTED_REPRESENTATION_EQUIVALENT = TRUE`
- `SELECTED_REPRESENTATION_PROJECT_CLOSED = TRUE`
- `STRICT_DISCOVERED_LANGUAGE_WITNESS = TRUE`

Global:

- `BLIND_LANE_SELECTION_MATCHES_FROZEN_EXPECTATION`
- `FIRST_BASE_CAP_HIT`, if any
- `UNIVERSAL_RECOGNIZER_PORTFOLIO_COMPLETE = OPEN`
- `UNIVERSAL_POLYNOMIAL_DISCOVERY = OPEN`
- `UNIVERSAL_POLYNOMIAL_COVERAGE = OPEN`
- `GLOBAL_PROGRESS_AMORTIZATION = OPEN`
- `P_VS_NP = OPEN`

---

## 7. Interpretation

A full finite PASS demonstrates that some useful boundary-language structure can be discovered semantically rather than supplied by name, and that the selected representation remains proof-carrying under repeated `exists`.

It does **not** prove that the recognizer portfolio covers arbitrary SAT boundaries, nor that every useful compact representation has a polynomial recognizer/converter.

A finite escape therefore identifies one of two next fronts:

1. add a new representation language only if the escape provides an exact structural reason; or
2. attack recognizer completeness/selection cost directly.

---

## 8. Laws

- `SUPPLIED_TYPE != DISCOVERED_TYPE`
- `DISCOVERY_COST_IS_PART_OF_SOLVER_COST`
- `FAILED_RECOGNIZERS_ARE_NOT_FREE`
- `SELECTED_LANGUAGE_MUST_REMAIN_PROJECT_CLOSED`
- `EQUIVALENCE_CERTIFICATE_REQUIRED_BEFORE_SWITCH`
- `FINITE_DISCOVERY_PORTFOLIO != UNIVERSAL_DISCOVERY_THEOREM`
- `P_VS_NP = OPEN`
