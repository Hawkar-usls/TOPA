# C025 — PIRC/GPEI reverse pass

**Date:** 2026-08-27  
**Status:** `NEW_ADVERSARIAL_GATE / UNIVERSAL_PRESERVATION_OPEN`  
**Claim ceiling:** `P_VS_NP = OPEN`

> SIT INITIUM FAUSTUM

## 0. Why this pass exists

The current JANUS line already distinguishes exactness, representation size, discovery, verification, nested manipulation and total runtime. This reverse pass adds one missing global-composition firewall.

A transition may be polynomial in its **current** representation size and still compose to a superpolynomial run in the **original** input size.

Example:

```text
s_0 = N
s_(i+1) = s_i^2
```

Every individual map is polynomial in `s_i`, yet

```text
s_i = N^(2^i).
```

Therefore:

```text
LOCAL_POLY_IN_CURRENT_STATE != GLOBAL_POLY_IN_ORIGINAL_INPUT
```

This is not a new complexity lower bound. It is a bookkeeping theorem preventing an invalid inference.

---

## 1. Global Polynomial Envelope Invariance (GPEI)

Freeze one universal exponent `c` and define

```text
B(N) := N^c.
```

For theorem mode, JANUS must prove an invariant over **reachable states of the fixed deterministic algorithm**:

```text
E_N(S) :=
    encoded_state_bytes(S) <= B(N)
    AND representation_type(S) is admitted
    AND scheduled_operations(S) have exact polynomial interfaces.
```

Required obligations:

1. **INITIAL**: `E_N(S_0)`.
2. **PRESERVATION**: for every reachable `S_i`, `E_N(S_i)` implies `E_N(S_(i+1))` for the frozen scheduled transition and normalization.
3. **STEP WORK**: transition + normalization + certificate + verification cost is bounded by a fixed polynomial in original `N` while the envelope holds.
4. **STEP COUNT**: the fixed schedule performs at most polynomially many macrosteps in `N`.
5. **TERMINAL**: exact terminal truth is polynomial in `N`.
6. **FULL LEDGER**: count semantic auxiliary variables, DAG/factor nodes, edges, contexts, boundary states, bit-length, proof/certificate bytes, normalization microsteps, failed discovery work and all retained indexes.

### Conditional composition lemma

If all six obligations hold for arbitrary CNF under one fixed algorithm, then total work is polynomial in `N` by induction over the scheduled steps.

This bridge is elementary and accepted **conditionally**.

The open premise is universal GPEI preservation.

```text
GPEI_COMPOSITION_BRIDGE = PROVED_CONDITIONALLY
UNIVERSAL_GPEI_PRESERVATION = OPEN
P_VS_NP = OPEN
```

---

## 2. Reverse-pass lesson from knowledge compilation

The knowledge-compilation viewpoint separates at least three resources that JANUS must keep separate:

```text
SUCCINCTNESS
QUERY_TRACTABILITY
TRANSFORMATION_TRACTABILITY
```

A representation can support cheap forgetting **after it already exists** while compilation into that representation is exponentially expensive on some inputs.

Hence:

```text
POLY_FORGETTING_AFTER_COMPILATION != POLY_COMPILATION_FROM_ARBITRARY_CNF
```

and

```text
FINITE_CANONICAL_LANGUAGE != UNIVERSAL_POLYNOMIAL_LANGUAGE
```

Known exact representation lanes such as OBDD/ROBDD or DNNF are therefore useful typed lanes and negative controls, not automatic universal solutions.

---

## 3. New hostile controls

### HC1 — ITERATED_LOCAL_POLY_BLOWUP

Construct a synthetic exact state transformer with a recurrence such as

```text
s_(i+1) = s_i^2
```

or another frozen polynomial of degree greater than one.

Expected result:

- every local checker reports polynomial-in-current-state work;
- GPEI must reject once no fixed input-relative envelope is preserved.

Purpose: make it impossible for a future theorem draft to infer global polynomiality from local polynomiality.

### HC2 — FIXED_KC_LANGUAGE_BLOWUP

Feed formulas from a family known to force exponential size in the exact target representation claimed by a lane.

Expected result:

```text
REJECT_THIS_REPRESENTATION_LANE
```

not

```text
REJECT_JANUS_UNIVERSALLY.
```

Purpose: distinguish a representation-language lower bound from a SAT lower bound.

### HC3 — BOUNDARY_QUOTIENT_DISCOVERY_DEBT

Provide instances where a compact quotient may exist but the current deterministic constructor does not find it within the frozen polynomial discovery budget.

Expected result:

```text
OPEN_DISCOVERY
```

not semantic promotion based on existence or heuristic success.

### HC4 — BINARY_CLOSURE_COMPOSITION

A lane may advertise a polynomial binary combination operation. Repeatedly compose it for a polynomial number of stages and charge cumulative bytes/work against original `N`.

Expected law:

```text
POLY_BINARY_OPERATION != POLY_N_FOLD_COMPOSITION_WITHOUT_ENVELOPE
```

---

## 4. Residual Interface Quotient (RIQ)

The ROBDD residual-frontier and deterministic live-width lanes suggest the same deeper object.

Across a fixed cut/interface, define the **continuation behavior** of the processed side on the unprocessed side. Two boundary states may be merged only when an admitted exact mechanism proves they induce the same required continuation semantics.

Call the resulting certified state object

```text
RESIDUAL_INTERFACE_QUOTIENT (RIQ).
```

Allowed equality/merging authority:

1. byte/structural canonical identity;
2. equality in a restricted canonical representation with charged size;
3. an independently checkable exact quotient/congruence certificate whose deterministic discovery cost is also charged.

Forbidden:

```text
SEMANTICALLY_EQUAL_THEREFORE_MERGE
```

without a paid derivation.

The exact semantic boundary-state count is a resource. A small quotient that is not polynomially discoverable is not an algorithmic escape.

---

## 5. Typed corridor architecture

The current strongest non-heuristic design is not one universal representation format. It is a frozen finite set of **typed exact lanes**, each with explicit recognition, operation and resource contracts, joined by a common envelope:

```text
CNF
 -> exact structural recognition
 -> one of:
      SCHAEFER / exact algebraic block
      independent component block
      matching/Hall cardinality block
      certified low-live-width DP block
      certified ROBDD block
      exact factor/interface block
 -> scheduled existential elimination
 -> normalization
 -> GPEI check
 -> repeat or OPEN
```

The PHP/Hall repair is a positive example: the generic resolution-product wall was bypassed only after exact recognition of an injective-assignment structure. It does not solve arbitrary CNF.

---

## 6. Historical reverse ordering

If the current JANUS could walk the earlier route with today's knowledge, it should install the following guards **before** repeating those experiments:

1. **Nash:** candidate-space size is not necessary work; never infer brute-force inevitability.
2. **Gödel / proof search:** verifier cost and finder cost are separate.
3. **Edmonds:** seek exact contraction/quotient before enumerating combinatorial alternatives.
4. **Davis–Putnam:** exact variable elimination is allowed, but charge the entire resolvent/interface representation rather than only the elimination rule.
5. **Schaefer:** detect tractable relation algebra before using a generic SAT representation.
6. **Bryant:** canonical DAG equality is valuable only together with input-relative size/order accounting.
7. **Knowledge compilation:** succinctness, queries, transformations and compilation cost are different axes.
8. **Extension-complexity / representation lower bounds:** a compact lift is not free; negative results are lane-specific unless a stronger theorem proves otherwise.

---

## 7. Exact next attack

The central target is now:

```text
GPEI_PRESERVATION_FOR_TYPED_REACHABLE_CORRIDOR
```

For a frozen syntactic schedule, seek the first reachable state where one of the following happens:

```text
NO_TYPED_LANE
BOUNDARY_STATE_EXPLOSION
REPRESENTATION_BYTES_ESCAPE
NORMALIZATION_MICROSTEP_ESCAPE
DISCOVERY_BUDGET_ESCAPE
BIT_LENGTH_ESCAPE
CERTIFICATE_BYTES_ESCAPE
TERMINAL_QUERY_NOT_TRACTABLE
```

M2R may forecast where this first failure will occur, but TOPA accepts only the exact replay/certificate.

The most informative next negative controls are:

- a connected formula outside the currently discharged Schaefer/component/matching lanes;
- a fixed-language knowledge-compilation blow-up family;
- a family stressing residual-interface width rather than raw clause count.

---

## 8. Current verdict

```text
JANUS_ARCHITECTURE = COHERENT_RESEARCH_ALGORITHM
GPEI_COMPOSITION_BRIDGE = PROVED_CONDITIONALLY
RIQ = FORMULATED
TYPED_CORRIDOR = FORMULATED
UNIVERSAL_GPEI_PRESERVATION = OPEN
UNIVERSAL_RIQ_DISCOVERY = OPEN
ARBITRARY_CNF_TOTALITY = OPEN
P_VS_NP = OPEN
```

CLAUDE VIAM FINI.
