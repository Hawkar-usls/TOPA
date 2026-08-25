# PF5 — Two-Connected 3-CNF Core Gate v8

Status: **FROZEN WIDTH-TWO SEPARATOR DISCOVERY GATE**  
Claim ceiling: **P_VS_NP = OPEN**

## 0. Purpose

v7 proves the finite width-one articulation case. v8 removes articulation points from the positive structural controls and asks for the next exact constructor:

> discover a hidden **two-variable separator** directly from one connected 3-CNF source, build exact four-valued child boundary relations, JOIN/project them, reconstruct a source witness, and charge pair-search plus all downstream representation work.

---

## 1. Frozen width-two source family

Freeze child counts:

`M = [2,4,8,12,16]`.

Shared boundary roots are unknown to discovery and are generated as two variables `b_1,b_2`. Every child has one private pair `(a_i,c_i)` and contains two 3-CNF pin gadgets using the same private pair:

- one four-clause gadget pins `b_1` to a target bit;
- one four-clause gadget pins `b_2` to a target bit.

Thus every child is attached to **both** boundary roots.

Consequences for `m>=2`:

- the primal graph is connected;
- removing `b_1` alone leaves `b_2` connecting all children;
- removing `b_2` alone leaves `b_1` connecting all children;
- no private root is an articulation point;
- removing `{b_1,b_2}` separates the private pairs into `m` components.

Two controls per `m`:

- SAT: every child requires `(b_1,b_2)=(1,1)`;
- UNSAT: all but the last child require `(1,1)`, final child requires `(1,0)`.

All source clauses are exactly three literals. Clause order is deterministically hash-shuffled.

---

## 2. Frozen negative/fallback controls

Reuse 2-connected positive-triple rings for sizes

`R=[6,8,10,12,14]`.

Their primal graphs have neither a valid articulation separator nor a valid two-variable separator under the exact clause-locality rule used here. They must reach generic source-to-OBDD fallback only after all earlier failures are charged.

---

## 3. Frozen pipeline

`SIGNED_PARITY_GRAPH_CNF`

`-> ARTICULATION_BOUNDARY_3CNF`

`-> PAIR_SEPARATOR_BOUNDARY_3CNF`

`-> GENERIC_FROZEN_ORDER_OBDD`.

The source API receives only `(clauses, variables, frozen_order)`. It receives no family name and no separator hint.

---

## 4. Exact pair-separator discovery

After articulation discovery rejects, enumerate unordered root pairs `{u,v}` lexicographically.

For each pair:

1. remove both variables from the primal graph;
2. compute connected components of remaining roots;
3. require at least two nonempty components;
4. every source clause must have all non-separator roots in exactly one component;
5. assign the clause to that child component;
6. require exact source-clause roundtrip;
7. accept the first pair satisfying all checks.

For fixed separator width two this discovery is polynomial in explicit source size: at most `O(n^2)` candidate pairs, each checked by polynomial graph traversal and clause scan.

This does not prove that arbitrary useful separator width is bounded by two.

---

## 5. Child boundary representation

For discovered `B=(b_1,b_2)` and each child `C_i`, build exact child CNF `F_i(C_i,B)` in a local OBDD ordered

`sorted(C_i), b_1, b_2`.

Project every private root with actual OBDD proof records. Evaluate the residual on all four boundary assignments:

`00,01,10,11`.

Store exact child relation `R_i subseteq {00,01,10,11}`.

Global boundary state:

`J_B = INTERSECT_i R_i`.

All child managers and relation states share one global ledger.

`exists b_1 exists b_2 J_B` is TRUE iff `J_B` is nonempty.

---

## 6. Strict witness glue

For SAT:

1. choose canonical lexicographically smallest boundary row from `J_B`;
2. seed that assignment into every child's actual private OBDD projection proof;
3. reverse every private proof;
4. union all disjoint private roots plus both boundary roots;
5. verify the complete assignment against the original unsplit 3-CNF.

UNSAT exports no witness.

---

## 7. Accounting

All v0.1 caps remain unchanged. Charge:

- source bytes;
- signed-parity reject;
- Tarjan articulation reject;
- every candidate pair tested;
- every component traversal and clause-locality check;
- source partition roundtrip;
- all child OBDD builds/projections;
- four boundary evaluations per child;
- JOIN updates;
- retained product state bytes;
- witness reconstruction and final source verification;
- all fallback work on negative controls.

No fresh global budget per child is allowed.

---

## 8. Required verdicts

- `POSITIVE_SOURCES_HAVE_NO_ARTICULATION = TRUE`
- `PAIR_SEPARATOR_DISCOVERED_UNLABELED = TRUE`
- `WIDTH_TWO_PARTITION_ROUNDTRIP_EXACT = TRUE`
- `FOUR_VALUED_CHILD_RELATIONS_EXACT = TRUE`
- `WIDTH_TWO_JOIN_EXACT = TRUE`
- `STRICT_WIDTH_TWO_WITNESS_GLUE = TRUE`
- `RING_REJECTS_WIDTH_ONE_AND_WIDTH_TWO = TRUE`
- `WIDTH_TWO_SEPARATOR_DISCOVERY_POLY_IN_EXPLICIT_SOURCE = PROVED_BY_FIXED_WIDTH_ENUMERATION`
- `UNIVERSAL_BOUNDED_SEPARATOR_WIDTH = OPEN`
- `THREE_CONNECTED_CORE_REPRESENTATION_DISCOVERY = OPEN`
- `UNIVERSAL_POLYNOMIAL_COVERAGE = OPEN`
- `P_VS_NP = OPEN`.

---

## 9. Laws

- `NO_ARTICULATION != NO_SMALL_SEPARATOR`
- `SEPARATOR_WIDTH_TWO_IS_STILL_POLYNOMIALLY_ENUMERABLE`
- `FOUR_VALUED_BOUNDARY_RELATION_IS_EXACT_FINITE_ADHESION`
- `FIXED_SMALL_SEPARATOR_WIDTH != UNIVERSAL_SMALL_SEPARATOR_BOUND`
- `PAIR_SEPARATOR_FAILURE != HARDNESS`
- `P_VS_NP = OPEN`
