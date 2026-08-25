# PF5 Non-Affine Connected Boundary v4.1 — `NAB-001` COPY_GLUE repair

Status: **FROZEN REPAIR / SAME v4 CONTROLS / SAME CAPS**  
Claim ceiling: **P_VS_NP = OPEN**

## Preserved v4 receipt

The first v4 provider replay established exact heterogeneous JOIN/projection/witness mechanics on every control that reached the common boundary manager, including non-affine SAT joins `EVEN_PARITY AND OR`.

The first escape was earlier:

`NA_PAR_EX1_K10_UNSAT`

hit

`OBDD_MAX_NONTERMINAL_NODES = 192`

in phase

`RIGHT_OBDD_PRIVATE_PROJECT`.

Larger OR/EXACTLY_ONE controls hit the same phase. The right boundary predicates themselves are compact; the growth came from retaining OBDD history for the private equality wrapper

`c_i = b_i`.

This is preserved as:

`NAB-001-PRIVATE-COPY-GLUE-OBDD-ACCUMULATION`.

It is not a boundary lower bound and not a heterogeneous-JOIN lower bound.

---

## Exact COPY_GLUE representation

For any exact boundary state `G(B)`, define

`COPY_GLUE(G; C -> B) := G(B) AND AND_i (c_i = b_i)`.

The representation stores:

1. the proof-carrying boundary state `G(B)`;
2. an immutable one-to-one copy map `c_i -> b_i`.

For private `c_i`:

`exists c_i [G(B) AND (c_i=b_i) AND REST]`

is exactly

`G(B) AND REST`,

because for every value of `b_i` there is exactly one satisfying choice `c_i=b_i`.

Therefore `PROJECT(c_i)`:

- verifies the copy-map entry;
- removes that entry;
- leaves `G(B)` unchanged;
- records the removed pair and before/after map hashes.

No truth-table search and no SAT oracle are used.

Witness reversal is equally exact: restore

`c_i := b_i`

from the recorded pair. This is witness reconstruction from the actual projection proof, not a family-level injected witness.

---

## Boundary OBDD

`G(B)` itself is still represented by a frozen-order OBDD over

`b_1,...,b_k`.

The OBDD is built by the same deterministic finite-state predicate automaton as v4, but without first embedding the private copy roots into the OBDD:

- OR state: `seen_one`;
- EXACTLY_ONE state: saturated count `0,1,2+`.

The post-COPY_GLUE residual is independently checked on all `2^k` boundary assignments; verification work is charged.

---

## Frozen repair contract

Unchanged from v4:

- widths `[3,4,6,8,10,12,14]`;
- OR SAT controls;
- EXACTLY_ONE UNSAT controls;
- left affine parity wing;
- common frozen-order OBDD language;
- affine-to-OBDD conversion;
- APPLY_AND heterogeneous JOIN;
- repeated shared projection;
- all v0.1 caps;
- strict source-witness verification.

Changed only:

`RIGHT_PRIVATE_WRAPPER: OBDD_EMBEDDED_COPY -> PROOF_CARRYING_COPY_GLUE`.

No cap is raised and no width is removed.

---

## Required verdict

`NAB_001_REPAIRED` iff the first cap, if any, moves past `RIGHT_COPY_GLUE_PRIVATE_PROJECT` and v4.1 reaches strictly more frozen controls than v4.

A full pass moves the front to:

`BOUNDARY_LANGUAGE_DISCOVERY_GATE`.

That gate must distinguish `SUPPLIED_TYPE` from `DISCOVERED_TYPE`; v4.1 still receives the boundary languages as frozen control metadata.

---

## Claim ledger

`NAB_001_PRIVATE_COPY_GLUE_OBDD_ACCUMULATION = PRESERVED`

`COPY_GLUE_PROJECT_EXACT = TO_BE_PROVIDER_VERIFIED`

`COPY_GLUE_WITNESS_REVERSE_EXACT = TO_BE_PROVIDER_VERIFIED`

`WIDTHS_CHANGED = FALSE`

`CAPS_CHANGED = FALSE`

`COMMON_JOIN_LANGUAGE_CHANGED = FALSE`

`SUPPLIED_TYPE != DISCOVERED_TYPE`

`UNIVERSAL_CHEAP_LANGUAGE_SELECTION = OPEN`

`UNIVERSAL_POLYNOMIAL_COVERAGE = OPEN`

`P_VS_NP = OPEN`
