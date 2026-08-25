# C025 — Akinator PF2: function-to-relation boundary after existential projection

Status: **INTERNAL EXACT BARRIER + LIVE-WIDTH BRIDGE**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Why PF1 is not automatically iterable as a B2 functional DAG

PF1 proves that one CNF pivot can be existentially eliminated before pairwise resolvents are materialized by replacing the pivot block with a compact B2 factor circuit.

A dangerous shortcut is then:

> keep all previously created B2 extension nodes as ordinary Boolean functions of the remaining roots and repeat forever.

This is false in general. Existential projection of a root can turn the graph of a deterministic extension function into a **relation** on the surviving extension variables and remaining roots.

This note isolates that exact obstruction and connects it to the already-proved deterministic live-width DP certificate lane.

---

## 1. One-gate counterexample

Let

`e <-> (x AND y)`.

Consider the relation after eliminating root `x`:

`R(e,y) := exists x . [e <-> (x AND y)]`.

Evaluate it exactly.

### y=0

For both values of `x`, `x AND 0 = 0`, so only

`e=0`

is allowed.

### y=1

If `x=0`, then `e=0`; if `x=1`, then `e=1`.

Thus both

`e=0` and `e=1`

are allowed.

Therefore the projected relation is

`R = {(e=0,y=0), (e=0,y=1), (e=1,y=1)}`.

There is no Boolean function `h(y)` whose graph equals this relation, because at `y=1` both output values of `e` are admitted.

Hence:

`EXISTENTIAL_PROJECTION_OF_A_B2_FUNCTION_GRAPH_NEED_NOT_BE_A_FUNCTION_GRAPH = PROVED`.

---

## 2. Consequence for B2 provenance

Before projection, the B2 record

`e := x AND y`

means that `e` is uniquely determined by its parents.

After `x` has been existentially removed from the state, retaining the same live variable `e` while deleting `x` no longer permits the interpretation

`e = h(y)`

for any total Boolean function `h`.

Therefore a repeated elimination engine must do at least one of:

1. eliminate `e` in the same certified projection cone;
2. replace the projected relation by a new exact relational/factor representation;
3. introduce a different functional summary together with enough extra state to preserve all correlations;
4. prove that this particular gate/state is in a special class where functional determinism survives.

It may not silently reuse the old B2 function semantics.

New law:

`B2_FUNCTION_PROVENANCE_BEFORE_PROJECTION != FUNCTION_PROVENANCE_AFTER_PROJECTION`.

---

## 3. Joint-correlation counterexample

Per-macro marginal survival is even weaker than the full projected relation.

Let a root `t` be fixed true and define two B2 outputs

`e_1 := x AND t`

`e_2 := (NOT x) AND t`.

Under `t=1`, before projection these are exactly

`e_1=x`, `e_2=NOT x`.

After existentially eliminating `x`, the exact allowed boundary pairs are

`(e_1,e_2) in {(0,1),(1,0)}`.

Individually, however, each marginal variable can take both values:

`e_1 in {0,1}` and `e_2 in {0,1}`.

If a selector stores only independent per-macro survival certificates, the Cartesian product of the marginals also admits

`(0,0)` and `(1,1)`,

which are spurious.

Therefore:

`PER_MACRO_SURVIVAL_CERTIFICATES != EXACT_JOINT_BOUNDARY_RELATION`.

This is an exact two-bit counterexample, not an asymptotic claim.

---

## 4. The correct projected object

Let `X_elim` be the variables eliminated so far, `Y` the remaining roots, and `B` a set of live boundary extension variables referenced by retained constraints.

The exact state crossing the cut is the relation

`Rel_B(Y,B) := exists X_elim, internal_extensions . Constraints`.

This relation can contain correlations that are invisible in:

- individual extension supports;
- individual nonconstancy/survival bits;
- independent marginal value sets;
- pre-projection B2 gate identities.

Thus the next state resource is not a list of surviving macros. It is a **joint boundary relation** or an exact quotient/certificate representing that relation.

---

## 5. Exact bridge to deterministic live-width DP

The existing TOPA live-width theorem already supplies a safe representation lane for this relational object.

Given a serialized B2 gate-constraint DAG and a deterministic topological trace, define live bags from first/last occurrence intervals. With live width `lambda`, exact dynamic programming retains the set of boundary assignments consistent with all processed constraints.

The number of explicit boundary assignments is at most

`2^(lambda+1)`.

The existing theorem gives exact feasibility/survival in

`poly(T, certificate_bytes) * 2^O(lambda)`.

Therefore the PF2 relation barrier does not require a new semantic oracle: it reduces to an already-accounted boundary-state resource.

If

`lambda <= c*log N`

for one universal fixed `c` and all trace/state bytes are polynomial, the relational projection is polynomial in original `N`.

If `lambda/log N` is unbounded, the explicit boundary-state exponent is not uniformly fixed.

This is a theorem about the explicit DP lane, not a lower bound against every possible compressed relation representation.

---

## 6. Why PF1 moved rather than removed the exponential

PF1 removes the immediate explicit pair frontier

`|P_x| * |N_x|`

for one root pivot.

PF2 shows the price can reappear as the amount of **joint correlation that must survive across the projection boundary**.

Thus the exact migration is:

`PAIRWISE_RESOLVENT_FRONTIER`

`-> PREBIRTH_FACTOR_DAG`

`-> JOINT_PROJECTED_BOUNDARY_RELATION`

`-> EXPLICIT_COST 2^O(lambda) IN THE LIVE-WIDTH LANE`.

The exponential has not been proved intrinsic to all representations. We have identified its next exact location in the currently constructive representation.

---

## 7. Mandatory atomic-cone rule

A safe functional-DAG implementation may impose the following fail-closed rule:

> An eliminated root may not leave behind a live extension variable whose defining dependency cone still contains that root, unless the survivor is accompanied by a new exact relational/rewrite certificate.

Call the set of live extension variables cut by this operation the **orphan boundary**

`O_x`.

A pure functional rewrite must eliminate/rebuild enough of the forward dependency cone that no stale function provenance crosses the cut.

A relational rewrite may retain `O_x`, but must carry their exact joint relation.

Hence a new structural resource is

`omega_x := |O_x|`

or, more accurately, the width/state complexity of the exact relation induced on `O_x`.

`SMALL_ORPHAN_COUNT` is a sufficient route to cheap explicit relation tracking; large orphan count is not by itself an unconditional lower bound because correlations may have a succinct circuit/BDD representation.

---

## 8. Organism-level interpretation

Several JANUS organs independently enforce parts of this rule:

- historical Tranception P-vs-NP diagnostics: quotient before child birth;
- OdontoForge: lineage must survive regeneration/EXIT;
- AIFC: a compact witness without its conditioning/provenance context cannot be promoted;
- P-N distributed field: intermediate/parallel work is charged rather than hidden;
- Fundamentum/TOPA: exact verifier and claim ceiling remain authoritative.

These are architecture donors. PF2 itself is the exact Boolean/projection argument above.

---

## 9. Next gate — BOUNDARY QUOTIENT

The current constructive question is now:

> Can every elimination step expose a deterministically discoverable proof-carrying quotient of its joint projected boundary relation whose total bytes, construction work, verification work, and accumulated novelty remain bounded by one fixed polynomial in original input length `N`?

Admissible certificate families include, if generated without hidden search:

- live-width DP tables for `lambda=O(log N)`;
- ROBDDs under a deterministic certified order;
- exact symmetry/orbit quotients with witness lift;
- another canonical relational DAG with an explicit polynomial state bound.

Forbidden shortcuts:

- independent per-macro survival marginals treated as a joint relation;
- stale B2 function definitions after eliminating their root dependencies;
- semantic equivalence oracle;
- heuristic compression score;
- exponentially many attempted decompositions/orders/quotients hidden outside the trace.

---

## 10. Claim ledger

`EXISTENTIAL_PROJECTION_CAN_DESTROY_EXTENSION_FUNCTIONALITY = PROVED`

`PER_MACRO_MARGINAL_SURVIVAL_CAN_LOSE_JOINT_CORRELATION = PROVED`

`FUNCTION_TO_RELATION_BOUNDARY = REQUIRED_FOR_GENERAL_ITERATED_PF1`

`LIVE_WIDTH_DP_IS_AN_EXACT_RELATIONAL_PROJECTION_LANE = IMPORTED_FROM_INTERNAL_PROVED_THEOREM`

`LAMBDA_O_LOG_N_GIVES_POLY_EXPLICIT_BOUNDARY_DP = PROVED_IN_EXISTING_SCOPE`

`UNIVERSAL_POLY_BOUNDARY_QUOTIENT = OPEN`

`ITERATED_FACTOR_DAG_TOTAL_POLY_BOUND = OPEN`

`POLYNOMIAL_AKINATOR = OPEN`

`P_VS_NP = OPEN`

---

## 11. Laws

- `EXISTENTIAL_PROJECTION_OF_A_FUNCTION_GRAPH_CAN_BE_A_RELATION`
- `STALE_FUNCTION_PROVENANCE_AFTER_PARENT_ELIMINATION_IS_UNSOUND`
- `PER_MACRO_SURVIVAL != JOINT_BOUNDARY_RELATION`
- `PAIR_FRONTIER_CAN_MIGRATE_INTO_BOUNDARY_CORRELATION_WIDTH`
- `EXPLICIT_BOUNDARY_DP_COSTS_2^O(LIVE_WIDTH)`
- `SMALL_ORPHAN_COUNT != NECESSARY_SMALL_RELATION_REPRESENTATION`
- `BOUNDARY_QUOTIENT_DISCOVERY_AND_TOTAL_BYTES_MUST_BE_CHARGED`
