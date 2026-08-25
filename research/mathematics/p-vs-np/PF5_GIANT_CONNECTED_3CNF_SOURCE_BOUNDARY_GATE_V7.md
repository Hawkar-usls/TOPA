# PF5 — Giant Connected 3-CNF Source-to-Boundary Gate v7

Status: **FROZEN CONNECTED-SOURCE SEPARATOR DISCOVERY GATE**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Why v7 exists

v6 starts directly from CNF and can discover exact signed-parity structure before constructing a bad generic representation. But its structural lane still recognizes a globally decomposable binary relation.

v7 moves to a **single connected 3-CNF source component**. No binary parity representation is available at the source level.

The new question is:

> Can the source itself reveal a small exact boundary, and can the solver construct proof-carrying child boundary relations, JOIN them, project the boundary, reconstruct a source witness, and charge every discovery/build/update byte and operation?

The first frozen separator language is intentionally narrow and auditable: a single articulation variable of the CNF primal graph.

---

## 1. Frozen source families

### 1.1 Articulation-star 3-CNF family

Freeze gadget counts:

`M = [2,4,8,12,16,20]`.

Each source has one boundary root `b` and `m` private pairs `(a_i,c_i)`.

Every gadget contains four **3-literal** clauses. For target bit `t`:

If `t=1`, use all four sign combinations

`( b OR  a_i OR  c_i)`

`( b OR  a_i OR NOT c_i)`

`( b OR NOT a_i OR  c_i)`

`( b OR NOT a_i OR NOT c_i)`.

If `t=0`, replace `b` by `NOT b` in all four clauses.

For any fixed private assignment exactly one of the four private sign combinations is false, so the conjunction forces the boundary literal to the frozen target bit. Conversely, when the boundary target is satisfied, all four clauses are true.

Thus each gadget is an exact 3-CNF boundary pin without unit or binary clauses.

Two controls per `m`:

- SAT: every gadget requires `b=1`;
- UNSAT: all but the final gadget require `b=1`, while the final gadget requires `b=0`.

Before separator removal the primal graph is connected: every private pair forms a triangle with `b`. Removing `b` produces `m` disjoint private edges. The boundary label is not supplied to discovery.

Clause order is deterministically hash-shuffled before the pipeline sees the source.

### 1.2 2-connected 3-CNF ring fallback

Freeze ring sizes:

`R = [6,8,10,12,14]`.

Variables `v_1,...,v_n`; clauses are the cyclic positive triples

`(v_i OR v_(i+1) OR v_(i+2))`

with indices modulo `n`.

The primal graph is connected and has no articulation vertex for the frozen sizes. The formula is satisfiable (all-TRUE witness).

This family exists to force:

1. signed-parity source recognition reject;
2. articulation-boundary discovery reject;
3. exact generic CNF→OBDD fallback only after both failed attempts are charged.

---

## 2. Frozen source pipeline

Order is frozen before provider execution:

`SIGNED_PARITY_GRAPH_CNF`

`-> ARTICULATION_BOUNDARY_3CNF`

`-> GENERIC_FROZEN_ORDER_OBDD`.

No family name, target bit, separator variable, or representation tag is an input to the pipeline API.

---

## 3. Exact articulation discovery

From the neutral CNF, build the variable primal graph:

- one vertex per declared root;
- edge `{u,v}` when `u` and `v` occur together in a clause.

Charge every literal inspection and adjacency insertion.

Run deterministic Tarjan articulation-point discovery.

Candidate order is ascending variable id. For each candidate `b`:

1. remove `b` from the primal graph;
2. compute connected components of the remaining roots;
3. require at least two nonempty components;
4. for every source clause, all non-`b` variables must belong to exactly one such component;
5. assign the clause to that component;
6. require the union of assigned child clause lists to reproduce the source CNF exactly.

The first candidate satisfying all checks is the canonical separator.

Discovery is exact for the width-one articulation class only. Failure does not imply that the source has no larger useful separator.

---

## 4. Child proof-carrying boundary relations

For every discovered child component `C_i`, let `F_i(C_i,b)` be its exact assigned sub-CNF.

Build `F_i` directly in a local OBDD manager under frozen local order

`sorted(C_i), b`.

Then existentially project every private root in `C_i`, preserving the actual OBDD `c0/c1/post` proof records.

The resulting exact residual depends only on `b`.

Evaluate that residual at `b=0,1` to obtain the child relation

`R_i subseteq {0,1}`.

The source boundary relation is the exact JOIN

`J_b = INTERSECT_i R_i`.

All local managers, private-projection proof bytes, allowed-bit extraction work, child relation bytes, and failed construction work share one global ledger. There is no fresh independent global cap per child.

---

## 5. Shared-boundary projection and witness glue

`exists b J_b` is TRUE iff `J_b` is nonempty.

For SAT:

1. choose the canonical smallest allowed boundary bit from `J_b`;
2. for each child, reverse its actual private OBDD projection proof with the chosen boundary value fixed;
3. union all disjoint child private assignments plus `b`;
4. require full declared-variable coverage;
5. evaluate the original unsplit source CNF directly.

No gadget target or family witness is injected.

For UNSAT, `J_b` must be empty and no witness is exported.

---

## 6. 2-connected fallback

If articulation discovery rejects, construct the full source CNF directly in the frozen-order OBDD fallback and run repeated existential projection exactly as in v6.

Both preceding failed recognizers remain charged.

A generic OBDD cap hit is a finite representation/bootstrap escape only.

---

## 7. Accounting

All v0.1 caps remain unchanged. No v7 size cap is added.

Charge:

- source CNF bytes;
- signed-parity recognizer reject work/proof;
- primal graph construction;
- Tarjan DFS operations;
- candidate-removal component traversals;
- clause-to-child partition checks;
- source round-trip partition certificate;
- every child CNF→OBDD build;
- every child private existential projection;
- child manager/intermediate state bytes;
- child boundary evaluations;
- JOIN/intersection operations and bytes;
- shared-boundary witness choice;
- every child witness reverse operation;
- final direct source-CNF verification;
- or, for fallback, complete generic OBDD build/projection work after all prior rejects.

---

## 8. Required provider verdicts

Per passing articulation control:

- `SOURCE_IS_SINGLE_CONNECTED_3CNF = TRUE`
- `SIGNED_PARITY_SOURCE_REJECT_CHARGED = TRUE`
- `ARTICULATION_DISCOVERED_WITHOUT_LABEL = TRUE`
- `SOURCE_PARTITION_ROUNDTRIP_EXACT = TRUE`
- `ALL_CHILD_BOUNDARY_RELATIONS_EXACT = TRUE`
- `BOUNDARY_JOIN_EXACT = TRUE`
- `STRICT_CHILD_WITNESS_GLUE = TRUE`

Per passing ring control:

- `SOURCE_IS_SINGLE_CONNECTED_3CNF = TRUE`
- `SIGNED_PARITY_SOURCE_REJECT_CHARGED = TRUE`
- `ARTICULATION_REJECT_CHARGED = TRUE`
- `GENERIC_SOURCE_BOOTSTRAP_SELECTED = TRUE`
- `STRICT_SOURCE_WITNESS = TRUE`

Global:

- `ARTICULATION_STAR_SAT_AND_UNSAT_CLOSED`
- `TWO_CONNECTED_RING_REACHES_FALLBACK`
- `FIRST_BASE_CAP_HIT`, if any;
- `WIDTH_ONE_SEPARATOR_DISCOVERY_POLY_IN_EXPLICIT_SOURCE = PROVED_BY_ALGORITHM`
- `UNIVERSAL_SMALL_SEPARATOR_EXISTENCE = OPEN`
- `UNIVERSAL_SMALL_SEPARATOR_DISCOVERY = OPEN`
- `TWO_CONNECTED_CORE_REPRESENTATION_DISCOVERY = OPEN`
- `UNIVERSAL_POLYNOMIAL_COVERAGE = OPEN`
- `GLOBAL_PROGRESS_AMORTIZATION = OPEN`
- `P_VS_NP = OPEN`.

---

## 9. Interpretation

A full articulation-star PASS shows that a source can remain one connected 3-CNF component while still admitting a cheaply discoverable exact boundary decomposition and proof-carrying JOIN/project/witness algebra.

The 2-connected ring prevents interpreting that result as a generic connected-3CNF theorem. Once articulation is absent, v7 has no structural separator lane and must fall back.

The next exact front after v7 is therefore the **2-CONNECTED 3-CNF CORE GATE**: discover and certify separator width greater than one, or find a compact source-to-boundary representation that does not rely on articulation points.

---

## 10. Laws

- `CONNECTED_SOURCE != INDECOMPOSABLE_SOURCE`
- `ARTICULATION_IS_SEPARATOR_WIDTH_ONE`
- `SEPARATOR_DISCOVERY_COST_IS_SOLVER_COST`
- `CHILD_BOUNDARY_RELATIONS_SHARE_ONE_GLOBAL_LEDGER`
- `SOURCE_PARTITION_MUST_ROUNDTRIP_EXACTLY`
- `2_CONNECTED != NO_USEFUL_SEPARATOR`
- `ARTICULATION_FAILURE != HARDNESS`
- `FINITE_WIDTH_ONE_SEPARATOR_PASS != UNIVERSAL_SEPARATOR_THEOREM`
- `P_VS_NP = OPEN`
