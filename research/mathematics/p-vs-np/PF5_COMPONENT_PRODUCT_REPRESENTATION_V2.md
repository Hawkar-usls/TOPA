# PF5 — Proof-Carrying Component-Product Representation v2

**Status:** `EXACT_COMPOSITION_THEOREM__FINITE_REPAIR_PROTOCOL_FROZEN`  
**Claim ceiling:** `P_VS_NP = OPEN`

## 1. Why v2 exists

`PF5_REPRESENTATION_ESCAPE_LADDER_V1` deliberately combined two already-revealed weaknesses:

- blocked equality, which defeats the frozen-order OBDD cap;
- a disjoint fan-out component, which defeats the explicit factor/boundary cap.

At `HYBRID_EQ10_FAN6` and `HYBRID_EQ12_FAN6`, the frozen primary matrix had no passing monolithic representation lane under the existing caps.

However, the hybrid was defined as a conjunction of **variable-disjoint components**. TOPA already has an exact incidence-component theorem and polynomial explicit-state component discovery for CNF.

Therefore the correct response is not a new solver and not a larger cap. It is to add a missing representation constructor:

```text
COMPONENT_PRODUCT(S_1, ..., S_k)
```

where each `S_i` may use a different already-admitted proof-carrying representation language.

---

## 2. Exact algebra theorem CP1

Let

```text
F = AND_i F_i
```

where `Var(F_i)` are pairwise disjoint.

For a variable `x in Var(F_j)`,

```text
exists x . F
=
(exists x . F_j) AND AND_{i != j} F_i.
```

### Proof

All factors `F_i`, `i != j`, are independent of `x`, so existential quantification distributes over their conjunction with `F_j`:

```text
exists x . (F_j AND G)
=
(exists x . F_j) AND G
```

for `x notin Var(G)`. Apply with `G=AND_{i!=j}F_i`. QED.

Thus a component-product representation is closed under the next existential projection whenever the selected representation for the affected component is itself closed under that projection.

No other component must be rebuilt.

---

## 3. Exact witness composition CP2

For SAT, each component representation returns a witness on its own disjoint original-root set.

Their disjoint union is a witness of the whole conjunction.

For UNSAT, one component ending in false makes the whole product false.

Witness bytes and reverse-provenance bytes remain charged componentwise and globally.

---

## 4. Representation manifest

The product certificate contains an immutable manifest entry for each component:

```text
component_id
original_root_set
component_input_hash
representation_type
representation_certificate_hash
representation_status
component_result
component_cost_ledger
```

The outer product record contains:

```text
ordered_component_manifest_hashes
global_variable_partition_hash
global_result
global_cost_ledger
```

The verifier checks pairwise disjoint root sets, component coverage of all current clauses/factors supplied by the decomposition certificate, each inner certificate under its own verifier, and the global Boolean composition rule.

---

## 5. Frozen heterogeneous selection policy for v2

v2 does not optimize among representations after seeing their costs.

For every discovered component, try in this fixed order:

```text
1. TRANCEPTION_ORBIT_TEMPLATE
2. FROZEN_ORDER_OBDD
3. LIVE_WIDTH_FACTOR_DP
4. RAW_B2_SHANNON
```

The first `PASS_EXACT_CLOSED` representation is selected.

Every failed/unsupported earlier attempt is retained in the component discovery ledger and charged.

This is a finite policy control, not a claim that this order is universally optimal.

---

## 6. One global budget

Componentization is forbidden from multiplying caps by the number of components.

For the whole product, sum:

```text
proof_bytes
witness_bytes
cumulative_state_bytes
build_ops
failed_discovery_ops
root_projection_ops
terminal_finalize_ops
verification_ops
witness_ops
```

and charge the serialized product manifest itself.

Peak current state is the sum of simultaneously retained component states plus the manifest, not the maximum of one component in isolation.

The same v0.1 caps remain in force.

---

## 7. v2 finite repair replay

Replay the exact frozen v1 ladder:

```text
HYBRID_EQ8_FAN6
HYBRID_EQ10_FAN6
HYBRID_EQ12_FAN6
```

with no changes to family parameters or caps.

The decomposition is the already-declared variable-disjoint split:

```text
EQ_m | FAN_6.
```

For the finite fixture, the split is verified from the public generator manifest. In the general CNF lane, discovery authority belongs to the existing deterministic incidence-component algorithm, not to a family label.

Expected behavior is **not frozen as PASS**. The test will report whichever inner representations actually pass under the unchanged caps and whether their global aggregate stays under the one shared budget.

---

## 8. Scope ceiling

If v2 repairs the v1 finite escape, the result means only:

```text
THE_V1_ESCAPE_WAS_A_MISSING_DISJOINT-COMPOSITION_REPRESENTATION_CASE
```

It does not establish universal polynomial coverage.

The next honest adversarial target must then be a **single connected component** in which independent-product factorization is unavailable.

Conversely, if the product still escapes, that is a finite failure of the current heterogeneous composition policy under unchanged caps, not a representation lower bound.

---

## 9. Next frontier if v2 passes

The natural successor is

```text
CONNECTED_BOUNDARY_ADHESION_GATE
```

Ask whether a connected state can be decomposed into proof-carrying pieces joined across a small explicit separator `B`, with exact relational boundary state on `B` and direct existential updates.

Disjoint components are separator size `|B|=0`. Thus component product is the width-zero base case of a possible broader separator/junction-tree representation algebra.

Any move to nonzero separators must charge:

- separator discovery;
- exact joint boundary relation;
- separator state bytes;
- update/recompression work;
- witness glue;
- cumulative bytes across all bags.

---

## 10. Laws

- `ONE_UNIVERSAL_FORMAT_IS_NOT_REQUIRED_IF_EXACT_COMPONENT_COMPOSITION_IS_PROVED`
- `EXISTS_X_DISTRIBUTES_OVER_VARIABLE_DISJOINT_CONJUNCTION`
- `HETEROGENEOUS_COMPONENT_REPRESENTATIONS_MAY_COEXIST`
- `FAILED_INNER_LANES_REMAIN_CHARGED`
- `COMPONENT_COUNT_MUST_NOT_MULTIPLY_THE_GLOBAL_BUDGET`
- `DISJOINT_COMPONENT_PRODUCT_IS_SEPARATOR_WIDTH_ZERO`
- `V1_FINITE_ESCAPE != REPRESENTATION_LOWER_BOUND`
- `P_VS_NP = OPEN`
