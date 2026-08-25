# JANUS P=NP Proof Obligation Graph — v1

Status: **ACTIVE / UNIVERSAL_THEOREM_FRONT**  
Primary goal: **RESOLVE_P_VS_NP**  
Current claim ceiling: **P_VS_NP = OPEN**  
Base commit: `f3cc7ce8d217437d7f30976133d8d2675df9a82f`

## 0. Why this graph exists

Finite SAT controls, holdouts, exact reductions, decomposition experiments, Slime proposals, Hephaestus crystals, and proof-carrying action graphs are useful only insofar as they close a universal proof obligation.

This graph prevents the project from turning into an endless sequence of solver versions. Every future experiment must attach to one node below and must change that node's status by a replayable proof/certificate, a valid counterexample, or a precisely charged negative receipt.

The positive target is a uniform polynomial-time exact elimination/representation theorem. If that target is completed for arbitrary SAT instances with all costs charged, then SAT is in P and therefore P=NP.

The negative target is a valid universal lower-bound route strong enough to rule out polynomial algorithms; no such lower bound is currently proved here.

---

## 1. Terminal theorem target

Let `F` be an arbitrary CNF instance of original explicit size `N`.

We seek one deterministic algorithm that constructs a sequence

`R_0 -> R_1 -> ... -> R_t`, with `t <= poly(N)`,

where `R_0` represents `F`, and every transition is an exact proof-carrying operation such as existential projection, certified rewriting, representation creation, exact join, or exact tractable elimination.

For one fixed polynomial `p`, globally over the complete run, require:

1. `|R_i| <= p(N)` for every intermediate state;
2. total construction/discovery work `<= p(N)`;
3. total projection/rewrite/join work `<= p(N)`;
4. total failed-search work `<= p(N)`;
5. total serialized proof/certificate bytes `<= p(N)`;
6. total certificate verification work `<= p(N)`;
7. total witness recovery / terminal decision work `<= p(N)`;
8. no SAT/#SAT/equivalence oracle, nonuniform advice, hidden truth table, or exponentially large candidate portfolio;
9. exact semantic preservation at every stage;
10. closure: the representation emitted by one stage is admissible input for the next stage.

If all ten obligations are proved universally, repeated exact elimination decides SAT in deterministic polynomial time:

`UNIVERSAL_UNIFORM_EXACT_PROJECTION/REPRESENTATION_COMPILER => SAT in P => P = NP`.

---

## 2. Proof-obligation DAG

### P0 — SOURCE CONTRACT
**Status: CLOSED AS CONTRACT**

Input size `N` is measured from the explicit SAT/CNF source. All later costs are charged back to this original `N`, not merely to the current residual size.

### P1 — EXACTNESS
**Status: LOCALLY CLOSED / UNIVERSAL COMPOSITION OPEN**

Every admitted operator must prove either

`F <=> F'`

or

`exists x F <=> F'`,

with replayable proof data and witness/decision preservation where required.

Many local exact operators are already implemented. The remaining issue is universal composition without state explosion.

### P2 — REPRESENTATION SIZE
**Status: OPEN / MAJOR COMPLEXITY FRONT**

For arbitrary existential projections, polynomial-size circuit existence is already at the `NP subseteq P/poly` frontier in the broad circuit setting. Therefore universal succinctness cannot be treated as a routine compression lemma.

Required positive theorem: every state produced by the uniform compiler remains polynomial in original `N`.

### P3 — UNIFORM DISCOVERY / CONSTRUCTION
**Status: OPEN / CORE POSITIVE BARRIER**

A small representation existing somewhere is insufficient. JANUS must deterministically construct the next exact representation in polynomial total time.

This node explicitly charges unsuccessful candidate search.

### P4 — CERTIFICATION
**Status: PARTIAL / GLOBAL FORM OPEN**

Local proof objects exist for many reductions. Required universal theorem: all transformation correctness is checkable with globally polynomial proof bytes and verification work, without a semantic oracle.

### P5 — SEQUENTIAL CLOSURE
**Status: OPEN / CORE COMPOSITION BARRIER**

After projecting/reducing one variable or block, the emitted representation must remain inside the same admissible proof-carrying algebra so the next existential projection can be executed with the same polynomial guarantees.

This is stronger than proving one projection is cheap.

### P6 — GLOBAL COST INVARIANT
**Status: OPEN**

One polynomial budget must cover the entire run:

`Q_total = Q_state + Q_proof + Q_discovery + Q_failed_search + Q_build + Q_projection + Q_join + Q_verify + Q_witness`.

No per-component or per-stage resetting of the budget is allowed.

### P7 — TERMINAL SAT/UNSAT DECISION
**Status: LOCALLY CLOSED / DEPENDS ON P1-P6**

If all SAT variables are eliminated while P1-P6 hold, the zero-variable state is exact and decides SAT. SAT witness recovery must also remain polynomial for SAT instances.

### P8 — P=NP BRIDGE
**Status: CONDITIONAL THEOREM CLOSED**

If P1-P7 are universally closed with one polynomial bound, then SAT is in P. Because SAT is NP-complete, `P=NP` follows.

No finite experiment can independently close P8.

---

## 3. Active structural front: U1-L2 CREATE

The current strongest positive-control grammar is exact elimination under logarithmic induced width:

`w <= O(log N) => 2^O(w) = N^O(1)`.

With a valid ordering/certificate, exact bucket elimination is polynomial.

But original-graph-only low-width discovery is not universal: expander-like source graphs can have linear treewidth. Therefore the active structural question is not merely DISCOVER a separator in the original graph.

It is:

> **CREATE:** Given a high-width certified state, deterministically construct in polynomial time a polynomial-size proof-carrying extension/representation that exposes either a low-width exact projection interface or another exact rank that guarantees polynomial progress.

This is node **P3 + P5 + P6 simultaneously**.

### U1-L2 exact obligation

For every nonterminal admissible state `R` of source size `N`, construct in deterministic polynomial time a proof-carrying block `C(R)` such that at least one holds:

1. `C(R)` has certified effective induced width `O(log N)` and can enter exact bucket elimination; or
2. `C(R)` exposes another exact polynomially bounded elimination rank with a proven decrease;

and additionally:

- `|C(R)| <= poly(N)`;
- the constructor and all failed search cost `poly(N)`;
- proof bytes and verifier work `poly(N)`;
- the next emitted state satisfies the same input contract;
- the global rank cannot decrease more than `poly(N)` times.

A proof of this statement would close the main positive bridge.

---

## 4. Closed or blocked routes — do not walk in circles

These are preserved as negative receipts, not erased:

- `ORIGINAL_GRAPH_SMALL_SEPARATOR_UNIVERSALITY`: **REFUTED AS UNIVERSAL ROUTE** by high-treewidth/expander scope.
- `MONOLITHIC_FROZEN_ORDER_OBDD`: **FINITE ESCAPE OBSERVED**; order-sensitive and not a universal compact language.
- `EXPLICIT_BOUNDARY_TABLE`: **FINITE ESCAPE OBSERVED**; exponential boundary rows.
- `SEMANTIC_TARGET_RECOGNITION`: **BARRIER**; exact semantic recognition can encode coNP-hard equivalence-style work.
- `BRUTE_FORCE_MACRO/BLOCK_SEARCH`: **BARRIER**; candidate-space enumeration can itself be exponential.
- `COMPLETE_COFACTOR_ENUMERATION`: **BARRIER**; can enumerate exponential boundary information even when a compact answer exists.
- `FINITE_HOLDOUT_SUCCESS`: **NOT A THEOREM**.
- `HEURISTIC_GENERATOR_SUCCESS`: **NOT A PROOF**.
- `SMALL_REPRESENTATION_EXISTS`: **NONUNIFORM ONLY** unless uniform construction is proved.

Future work must cite which barrier it bypasses rather than silently reintroducing it.

---

## 5. Exact-positive library already available

The current algebra contains useful but non-universal exact pieces, including:

- pure-literal existential projection;
- tautological-resolvent projection;
- single-nontautological-resolvent projection;
- complementary-twin contraction;
- clause subsumption;
- self-subsuming resolution;
- component product for disjoint incidence components;
- exact 2-SAT SCC certificates;
- small strong-backdoor-to-2SAT proof trees;
- affine GF(2) boundary representation and exact JOIN;
- OBDD/common-language JOIN on restricted controls;
- bounded/live-width dynamic programming;
- logarithmic-induced-width bucket elimination with ordering certificate.

Their role in the proof is to define an exact instruction set from which a universal CREATE/EXPLOIT grammar might be built.

They are not individually evidence that P=NP.

---

## 6. JANUS machine-search rule

JANUS may search patterns humans would miss, but a discovered pattern becomes an admitted proof step only after conversion into all of:

`DETERMINISTIC_SOURCE_PREDICATE`
`+ EXACT_IDENTITY_OR_PROJECTION_THEOREM`
`+ POLY_DISCOVERY_BOUND`
`+ REPLAYABLE_CERTIFICATE`
`+ POLY_WITNESS_LIFT`
`+ GLOBAL_COST_CHARGE`.

Scores, traces, neural similarity, Slime flow, entropy, crystal compactness, or empirical success may propose a candidate but may not justify it.

---

## 7. Falsification branch

The program must also actively look for a family that kills the positive theorem.

A valid negative result must quantify over the relevant admissible representation/compiler class. Examples of useful obstructions include:

- every admissible exact representation after a specified projection requires superpolynomial size;
- every valid CREATE block preserving the frozen proof system requires superpolynomial total construction/search;
- sequential closure forces superpolynomial cumulative intermediate/proof bytes;
- a proposed universal rank fails to decrease or requires exponentially many stages.

Careful claim ceiling: for broad general circuit representation, a universal superpolynomial projection-size lower bound reaches major circuit lower-bound territory; failure of one representation family is not `P != NP`.

---

## 8. Spiral protocol

Every new research turn appends exactly one checkpoint object with:

- `spiral_index`;
- `parent_state_hash`;
- `current_state_hash`;
- `proof_obligation_node`;
- `hypothesis`;
- `source_predicate`;
- `exact_theorem`;
- `discovery_cost_bound`;
- `proof_cost_bound`;
- `witness_cost_bound`;
- `finite_controls`;
- `result = PASS | FAIL | CAP_HIT | COUNTEREXAMPLE | OPEN`;
- `what_changed`;
- `what_was_ruled_out`;
- `unpaid_debt`;
- `next_narrowest_gate`.

If `current_state_hash` equals a previous state with no strengthened theorem/certificate, mark `REVISIT` and do not repeat the same path.

Hephaestus crystal hashes are recurrence guards/accounting receipts only; they are never a proof of semantic equivalence unless the canonical representation contract itself proves that equivalence.

---

## 9. Current checkpoint

`ACTIVE_NODE = U1-L2 / P3+P5+P6`

`KNOWN_POLY_EXPLOIT = LOG_INDUCED_WIDTH_EXACT_ELIMINATION`

`KNOWN_UNIVERSAL_FAILURE = ORIGINAL_GRAPH_SEPARATOR_SEARCH`

`NEXT_REQUIRED_THEOREM = CERTIFIED_STRUCTURE_CREATION_WITH_GLOBAL_POLY_RANK`

`P_VS_NP = OPEN`

The next experiment is permitted only if it attacks that CREATE theorem or produces a falsifying family for it.